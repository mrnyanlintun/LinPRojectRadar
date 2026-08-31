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
    # ================================================================= GOAL THREE
    # THE TWO BRANCH LAYERS, MEASURED FROM THE RENDERED SVG ATTRIBUTES.
    #
    # The Run 94 driver's own project has NO module with a current result, so every
    # module -> category line there renders in its unestimable STATE (0.14) and there is no live
    # one to compare against. That measurement is reported as it stands; this one supplies a row
    # whose modules DO carry results, which is the only way to see the LIVE tier of both layers.
    # The production file is loaded and its own `render` is called; nothing is reimplemented.
    FLOWPAGE = """<!doctype html><meta charset="utf-8"><style>__CSS__</style>
    <body><div id="flowhost" style="width:1240px"></div></body>"""
    for VW in (1280, 1024):
        say("=" * 96)
        say(f"GOAL THREE -- SIGNAL FLOW BRANCH ATTRIBUTES AT {VW}px")
        pg = b.new_page(viewport={"width": VW, "height": 2400})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.set_content(FLOWPAGE.replace("__CSS__", CSS))
        for f in ("assets/js/config.js", "assets/js/taxonomy.js", "assets/js/categories.js"):
            pg.add_script_tag(content=(ROOT / f).read_text(encoding="utf-8"))
        prow = json.loads((SCRATCH / "row_posture.json").read_text())
        pg.evaluate("""(r)=>{
          window.LinResults = { rowFor: () => r, all: () => [r] };
          window.LinDocs = window.LinDocs || { statusFor: () => ({}) };
          /* `isUploaded` is filled from the DOCUMENTS PANEL'S OWN event walk -- the chart calls
             `LinDetail.uploadedDocEvents(project)` rather than reading a field -- so a document
             type is marked uploaded here by supplying that event log, which is the same shape
             the panel renders. Without it every doc -> module line renders in its not-uploaded
             STATE and there is no live tier to compare. */
          const types = Object.keys((r.signal_inputs && r.signal_inputs.sources) || {});
          window.LinDetail = window.LinDetail || {};
          window.LinDetail.uploadedDocEvents = () =>
            types.map(t => ({ type:'signals_extracted', docType:t }));
        }""", prow)
        pg.add_script_tag(content=FLOW)
        ok = pg.evaluate("""(r)=>{
          try {
            window.LinNeuralFlow.render(
              /* The shape the chart actually reads: `simulationSignals.signal_array` is what
                 builds its method-class lookup, and `documents` is what marks a type uploaded.
                 Measured, not guessed: with only `module_results` supplied every line rendered
                 in its unestimable STATE and there was no live tier to compare. */
              { id:'run96', project_id:'run96', name:'Run 96', sector:'construction',
                project_status:r.project_status, category_statuses:r.category_statuses,
                module_results:r.module_results, signal_inputs:r.signal_inputs,
                simulationSignals:{ signal_array:r.module_results },
                documents:(r.signal_inputs && r.signal_inputs.sources)
                            ? Object.keys(r.signal_inputs.sources).map(
                                function(k){ return { doc_type:k, uploaded:true }; })
                            : [] },
              document.getElementById('flowhost'));
            return 'rendered';
          } catch (e) { return 'ERROR ' + e.message; }
        }""", prow)
        say(f"  render: {ok}")
        m = pg.evaluate("""() => {
          const rows = (t) => Array.from(document.querySelectorAll(
              '[data-edge-type="' + t + '"]')).map(e => (e.getAttribute('opacity')||'?') +
              ' @ ' + (e.getAttribute('stroke-width')||'?') + 'px');
          const tally = (a) => a.reduce((m,k)=>(m[k]=(m[k]||0)+1,m),{});
          const term = Array.from(document.querySelectorAll('[data-edge-terminates]')).map(e=>
            [e.getAttribute('data-edge-terminates'), e.getAttribute('opacity'),
             !!e.getAttribute('stroke-dasharray'), !!e.getAttribute('marker-end')].join('|'));
          return { dm: tally(rows('DOCUMENT -> MODULE')), mc: tally(rows('MODULE -> CATEGORY')),
                   term: tally(term) };
        }""")
        say(f"    DOCUMENT -> MODULE   {m['dm']}")
        say(f"    MODULE   -> CATEGORY {m['mc']}")
        LIVE_DM = {k for k in m["dm"] if not k.startswith("0.12")}
        LIVE_MC = {k for k in m["mc"] if not k.startswith("0.14")}
        say(f"    LIVE TIER doc->mod {sorted(LIVE_DM)}")
        say(f"    LIVE TIER mod->cat {sorted(LIVE_MC)}")
        say(f"    GOAL THREE MET -- the two layers render at the SAME opacity and stroke "
            f"treatment: {LIVE_DM == LIVE_MC and len(LIVE_MC) > 0}")
        say(f"    STATE OPACITIES UNTOUCHED -- 0.14 on an unestimable mod->cat: "
            f"{any(k.startswith('0.14') for k in m['mc'])}; 0.12 on a not-uploaded doc->mod: "
            f"{any(k.startswith('0.12') for k in m['dm'])}")
        say(f"    CATEGORY -> STATUS terminations (must be unchanged): {m['term']}")
        say(f"  PAGE ERRORS: {errs[:2]}")
        pg.close()
    b.close()
say("RUN 96 CARD DRIVE COMPLETE")
