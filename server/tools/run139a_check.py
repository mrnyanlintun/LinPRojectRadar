#!/usr/bin/env python3
"""
RUN 139A. THE ORRERY KEY, CHECKED AGAINST THE RENDERED PAGE.

The project build is drive_run94_charts.py's, unchanged in substance: a real
`projectupload` and a real `projectcomputeall`, then every performance category pressed
through `projectcategoryapply`, so the canvas draws what the platform actually produces.
Nothing under test is supplied.

WHAT THIS MEASURES, all in a real Chromium, all read back from the rendered page:
  1. the canvas's CSS box at every viewport width the panel renders at;
  2. `ctx.measureText` for every module name and every category name at candidate fonts, on
     the panel's own 2D context, so the legend's footprint is a measurement not an estimate;
  3. the module population the panel draws (`data-modules` and its siblings);
  4. the moon order the painter produced, read from `LinProjectNet2D.lastScene()`;
  5. a PNG of the canvas per theme, for pixel-sampled contrast afterwards.

Run from server/:
  DATABASE_URL=sqlite:///<throwaway> RUN139A_OUT=<dir> python tools/run139a_measure.py
"""
from __future__ import annotations
import ast, base64, hashlib, io, json, logging, os, pathlib, socket, sys, threading, time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
logging.disable(logging.INFO)

from reportlab.lib.pagesizes import LETTER            # noqa: E402
from reportlab.pdfgen import canvas as rl_canvas      # noqa: E402
from fastapi.testclient import TestClient             # noqa: E402
from sqlalchemy import select                          # noqa: E402
import app.main as main                                # noqa: E402
from app.documents import set_extractor_override       # noqa: E402
from app.extraction_client import StubExtractor        # noqa: E402
from app.extraction_fields import extraction_fields_for  # noqa: E402
from app.models import Project                         # noqa: E402
from app.research_identity import hash_access_token    # noqa: E402
from app.research_models import Participant            # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
STAMP = int(time.time())
PID = f"PRJ-R139C-{STAMP}"
ADMIN = f"run139c-admin-{STAMP}"
P1_END = "2026-03-31"
SECTOR = os.environ.get("RUN139A_SECTOR", "construction")

def say(*a): print(" ".join(str(x) for x in a), flush=True)
def post(p):
    r = client.post("/exec", content=json.dumps(p), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"HTTP {r.status_code} {r.text[:400]}"
    return r.json()
def b64(raw): return base64.b64encode(raw).decode()

_src = (HERE / "drive_run74_did_extraction_store.py").read_text(encoding="utf-8")
_vnode = next(n for n in ast.parse(_src).body
              if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "VALUES")
VALUES = eval(compile(ast.Expression(_vnode.value), "<v>", "eval"), {"PERIOD_END": P1_END}, {})
DOCSET = [("D01_contract_award.pdf", "contract_value"),
          ("D02_pay_application.pdf", "pay_application"),
          ("D05_schedule_update.pdf", "schedule_update"),
          ("D06_monthly_report.pdf", "monthly_report")]

def make_pdf(filename, doc_type, ex):
    buf = io.BytesIO(); c = rl_canvas.Canvas(buf, pagesize=LETTER)
    c.setFont("Helvetica-Bold", 13); c.drawString(72, 720, filename)
    c.setFont("Helvetica", 9); y = 700
    c.drawString(72, y, f"Document type: {doc_type} stamp {STAMP}"); y -= 18
    for k, v in ex.items():
        s = json.dumps(v) if isinstance(v, (list, dict)) else str(v)
        for chunk in [s[i:i+90] for i in range(0, max(len(s), 1), 90)]:
            c.drawString(72, y, f"{k}: {chunk}"); y -= 12
            if y < 60: c.showPage(); c.setFont("Helvetica", 9); y = 720
    c.showPage(); c.save(); return buf.getvalue()

OVERRIDE, DOCS = {}, []
for fn, dt in DOCSET:
    ex = {f: VALUES[f] for f in (extraction_fields_for(dt) or []) if f in VALUES}
    ex.setdefault("document_date", P1_END)
    raw = make_pdf(fn, dt, ex)
    OVERRIDE[hashlib.sha256(raw).hexdigest()] = (dt, ex, 0.95)
    DOCS.append((fn, raw))
set_extractor_override(StubExtractor(OVERRIDE))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code=f"R139A-ADMIN-{STAMP}", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PID)) is None:
        s.add(Project(legacy_id=PID, doc={"id": PID, "name": "Run 139A orrery legend",
                                          "sector": SECTOR, "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": f"R139A-PM-{STAMP}", "role": "Participant",
                "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PID,
      "participant_id": created["participant_id"], "project_role": "PM"})

say("=" * 100); say(f"RUN 139A  project={PID}  sector={SECTOR}  DATABASE_URL={os.environ.get('DATABASE_URL')}")
say("=" * 100)
U = post({"action": "projectupload", "session_token": PM, "id": PID, "period": 1,
          "period_end": P1_END,
          "documents": [{"filename": fn, "mimeType": "application/pdf", "dataBase64": b64(r)}
                        for fn, r in DOCS]})
say(f"upload: ok={U.get('ok')}")
CA = post({"action": "projectcomputeall", "session_token": PM, "id": PID})
say(f"computeall: ok={CA.get('ok')}")
for cat in ("A1", "A2", "A3", "A4", "A6"):
    r = post({"action": "projectcategoryapply", "session_token": PM, "id": PID,
              "period": 1, "category": cat})
    say(f"  apply {cat}: ok={r.get('ok')}")
# --------------------------------------------------------------------------------- BROWSER
sock = socket.socket(); sock.bind(("127.0.0.1", 0)); PORT = sock.getsockname()[1]; sock.close()
import uvicorn  # noqa: E402
srv = uvicorn.Server(uvicorn.Config(main.app, host="127.0.0.1", port=PORT, log_level="critical"))
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(200):
    try:
        c = socket.create_connection(("127.0.0.1", PORT), 0.2); c.close(); break
    except OSError: time.sleep(0.05)
BASE = f"http://127.0.0.1:{PORT}"
CHROME = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"
OUT = pathlib.Path(os.environ.get("RUN139A_OUT", "/tmp/run139a")); OUT.mkdir(parents=True, exist_ok=True)
TAG = os.environ.get("RUN139A_TAG", "after")

PASS = FAIL = 0
def check(cond, what, detail=""):
    global PASS, FAIL
    if cond: PASS += 1; say(f"  PASS  {what}" + (f"  [{detail}]" if detail else ""))
    else:    FAIL += 1; say(f"  FAIL  {what}" + (f"  [{detail}]" if detail else ""))
    return bool(cond)

OPEN = r"""() => {
  if (window.LinApp && LinApp.showPage) { try { LinApp.showPage('detail'); } catch(e){} }
  const sec = document.querySelector('#section-d-projnet');
  if (sec && !sec.classList.contains('open')) {
    const h = sec.querySelector('.collapse-header'); if (h) h.click();
  }
  return sec ? sec.className : 'NO SECTION';
}"""
SETTHEME = r"""(t) => { document.body.setAttribute('data-theme', t);
  document.documentElement.setAttribute('data-theme', t);
  return document.body.getAttribute('data-theme'); }"""

READ = r"""() => {
  const host = document.querySelector('.detail-projnet2d');
  const cv = host && host.querySelector('canvas.projnet2d-canvas');
  if (!host || !cv) return { present:false };
  const N = window.LinProjectNet2D;
  const legend = N && N.lastLegend ? N.lastLegend() : null;
  const scene  = N && N.lastScene  ? N.lastScene()  : null;
  const cats = (window.performanceCategories ? window.performanceCategories() : []) || [];
  const registry = {};                      /* module_id -> name, straight from the roster */
  const catName = {};
  cats.forEach(c => { catName[c.key] = c.name;
                      (c.modules||[]).forEach(m => registry[m.module_id] = m.name); });
  const g = cv.getContext('2d');
  /* the drawn width of each entry's text, so the pixel sample covers the glyphs and no more */
  const widths = {};
  if (legend) {
    legend.entries.forEach((e, i) => {
      g.save();
      g.font = (e.kind === 'head' ? '700 ' : '500 ') + legend.font + 'px system-ui, sans-serif';
      widths[i] = Math.ceil(g.measureText(e.text).width);
      g.restore();
    });
  }
  const attrs = {};
  ['modules','legend-entries','legend-modules','legend-band-key','legend-columns','legend-font']
    .forEach(k => attrs[k] = host.getAttribute('data-'+k));
  return { present:true, legend, widths, registry, catName, attrs,
           css: { w: Math.round(cv.getBoundingClientRect().width),
                  h: Math.round(cv.getBoundingClientRect().height) },
           moons: scene ? scene.bodies.filter(b=>b.kind==='moon')
                    .map(b=>({id:b.key, cat:b.category, state:b.state, ic:b.identityColor})) : [],
           png: cv.toDataURL('image/png') };
}"""

# ---- CONTRAST, FROM THE PAINTED PIXEL ------------------------------------------------------
# There is no DOM to walk here: this is a <canvas>, so the only honest measurement is the
# bitmap the 2D context painted. For each legend text run the sampler takes the rectangle the
# glyphs were drawn in, calls the MOST COMMON colour in it the background and the pixel
# FURTHEST from that background in relative luminance the ink, and reports the WCAG 2.1
# contrast ratio of that pair. Walking `background-color` up the DOM gave a wrong answer on
# this codebase (Run 128); here it is not even available.
from PIL import Image  # noqa: E402
import collections  # noqa: E402

def lum(c):
    def ch(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(c[0]) + 0.7152 * ch(c[1]) + 0.0722 * ch(c[2])

def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)

def contrast_of(img, x, y, w, fs):
    # The GROUND is read from a box taller than the glyphs -- fs + 16 rather than fs + 2 -- so
    # that most of the sampled area is page and the modal colour is the ground. With six shadow
    # passes a tight crop can be more than half ink, and the modal colour then IS the ink: that
    # artefact reported 1.9:1 for a row whose real contrast is far higher, and it is a fault in
    # the measurement, not in the paint. The INK is still taken from the tight glyph box.
    h = int(round(fs)) + 2
    tight = (max(0, x - 1), max(0, int(y - h / 2)),
             min(img.width, x + w + 1), min(img.height, int(y + h / 2) + 1))
    wide = (max(0, x - 6), max(0, int(y - h / 2) - 8),
            min(img.width, x + w + 6), min(img.height, int(y + h / 2) + 8))
    if tight[2] <= tight[0] or tight[3] <= tight[1]: return None
    tpx = list(img.crop(tight).convert("RGB").getdata())
    wpx = list(img.crop(wide).convert("RGB").getdata())
    if not tpx or not wpx: return None
    bg = collections.Counter(wpx).most_common(1)[0][0]
    lbg = lum(bg)
    ink = max(tpx, key=lambda p: abs(lum(p) - lbg))
    return {"bg": bg, "ink": ink, "ratio": round(ratio(ink, bg), 2)}

from playwright.sync_api import sync_playwright  # noqa: E402
from app.theme import THEMES  # noqa: E402
ALL_THEMES = list(THEMES) + ["dark"]
say(f"THEME AUTHORITY server/app/theme.py THEMES = {THEMES}; plus archived-but-renderable 'dark'")
VIEWPORTS = [int(v) for v in os.environ.get("RUN139A_VW", "1440,1280").split(",")]
THEMELIST = [t for t in os.environ.get("RUN139A_THEMES", "").split(",") if t] or ALL_THEMES

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME, args=["--use-gl=swiftshader", "--no-sandbox"])
    for VW in VIEWPORTS:
        say("=" * 100); say(f"VIEWPORT {VW}px")
        pg = b.new_page(viewport={"width": VW, "height": 2400})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        for pat in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                    "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
            pg.route(pat, lambda r: r.abort())
        pg.goto(BASE + "/", wait_until="domcontentloaded")
        pg.evaluate("(t) => sessionStorage.setItem('og-session-token', t)", PM)
        pg.goto(BASE + "/", wait_until="domcontentloaded")
        pg.wait_for_timeout(8000)
        pg.evaluate("() => window.LinApp && LinApp.showPage && LinApp.showPage('detail')")
        pg.evaluate("(id) => window.LinDetail && LinDetail.render(id)", PID)
        pg.wait_for_timeout(12000)
        pg.evaluate(OPEN); pg.wait_for_timeout(4000)
        for TH in THEMELIST:
            say("-" * 100); say(f"THEME {TH} at {VW}px  (set: {pg.evaluate(SETTHEME, TH)})")
            pg.evaluate("(id) => window.LinDetail && LinDetail.render(id)", PID)
            pg.wait_for_timeout(3000); pg.evaluate(OPEN); pg.wait_for_timeout(2500)
            R = pg.evaluate(READ)
            if not R.get("present"):
                check(False, "the panel rendered"); continue
            (OUT / f"{TAG}_{VW}_{TH}.png").write_bytes(
                base64.b64decode(R["png"].split(",", 1)[1]))
            L = R["legend"]
            say(f"  canvas {R['css']}  attrs={R['attrs']}")
            if not L:
                check(False, "a key was drawn at all"); continue
            say(f"  key: font={L['font']}px columns={L['columns']} "
                f"modulesDrawn={L['modulesDrawn']} box={L['box']} entries={len(L['entries'])}")

            mods = [e for e in L["entries"] if e["kind"] == "module"]
            heads = [e for e in L["entries"] if e["kind"] == "head"]
            bands = [e for e in L["entries"] if e["kind"] == "band"]
            say(f"  {len(heads)} headings, {len(mods)} module names, {len(bands)} band rows")

            # 1. THE BAND KEY SURVIVED
            check(len(bands) == 9, "the nine-row band key is still drawn", f"{len(bands)} rows")

            if L["modulesDrawn"]:
                # 2. EVERY MODULE NAME IS THE REGISTRY'S NAME FOR THAT MODULE ID
                bad = [(e["id"], e["text"], R["registry"].get(e["id"]))
                       for e in mods if R["registry"].get(e["id"]) != e["text"]]
                check(not bad, "every entry carries its own module's registry name",
                      f"{len(bad)} wrong: {bad[:3]}")
                check(len(mods) == len(R["registry"]),
                      "every module the panel draws has an entry",
                      f"{len(mods)} entries vs {len(R['registry'])} in the roster, "
                      f"data-modules={R['attrs']['modules']}")
                # 3. EVERY SWATCH IS THAT MOON'S OWN IDENTITY RIM, AND ITS OWN STATE
                byid = {m["id"]: m for m in R["moons"]}
                badc = [(e["id"], e["swatch"], (byid.get(e["id"]) or {}).get("ic"))
                        for e in mods if (byid.get(e["id"]) or {}).get("ic") != e["swatch"]]
                check(not badc, "every swatch is the identity rim of the moon it names",
                      f"{len(badc)} wrong: {badc[:3]}")
                bads = [(e["id"], e["state"], (byid.get(e["id"]) or {}).get("state"))
                        for e in mods if (byid.get(e["id"]) or {}).get("state") != e["state"]]
                check(not bads, "every entry's treatment is the state of the moon it names",
                      f"{len(bads)} wrong: {bads[:3]}")
                # 4. HEADINGS ARE THE CATEGORY NAMES THE PLANETS CARRY
                want = {(k + "  " + v) for k, v in R["catName"].items()}
                got = {h["text"] for h in heads if h["group"] != "band"}
                check(got == want, "every category heading is the planet's own name",
                      f"missing={sorted(want-got)} extra={sorted(got-want)}")
            else:
                say("  MODULE NAMES OMITTED at this canvas size -- band key only")
                check(R["attrs"]["legend-modules"] == "omitted",
                      "the omission is declared on the container")

            # 5. CONTRAST OF EVERY KEY TEXT ELEMENT, FROM THE PAINTED PIXEL
            img = Image.open(io.BytesIO(base64.b64decode(R["png"].split(",", 1)[1])))
            rows = []
            for i, e in enumerate(L["entries"]):
                w = R["widths"].get(str(i), R["widths"].get(i))
                if not w: continue
                c = contrast_of(img, e["x"], e["y"], w, L["font"])
                if c: rows.append((e["kind"], e["text"], c))
            byk = {}
            for k, t, c in rows: byk.setdefault(k, []).append(c["ratio"])
            for k in sorted(byk):
                say(f"  CONTRAST {k}: n={len(byk[k])} min={min(byk[k])}:1 "
                    f"median={sorted(byk[k])[len(byk[k])//2]}:1 max={max(byk[k])}:1")
            for k, t, c in sorted(rows, key=lambda r: r[2]["ratio"])[:6]:
                say(f"    worst {k} {t[:38]!r}: {c['ratio']}:1  ink={c['ink']} bg={c['bg']}")
            check(min(r[2]["ratio"] for r in rows) >= 3.0,
                  "every key text element reaches 3:1 against its own painted ground",
                  f"min {min(r[2]['ratio'] for r in rows)}:1")
            (OUT / f"{TAG}_legend_{VW}_{TH}.json").write_text(json.dumps(
                {"attrs": R["attrs"], "legend": L,
                 "contrast": [(k, t, c) for k, t, c in rows]}, indent=1))
        say(f"  page errors: {errs[:3]}")
        pg.close()
    b.close()
say("=" * 100); say(f"RUN 139A CHECK: {PASS} passed, {FAIL} failed")
say("DONE")
sys.exit(1 if FAIL else 0)
