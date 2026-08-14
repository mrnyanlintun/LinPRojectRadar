#!/usr/bin/env python3
"""
POST-RUN-22. WHY A POPULATED PROJECT READ DIFFERENTLY AFTER A PROJECT SWITCH.

The first pass of the Run-23 driver recorded, on the SAME populated project, two module dots
moving amber -> red and the governed rollup moving Amber -> Red after a populated -> empty ->
populated round trip, while the SERVER's own row for that project stayed Amber throughout. That
is either cross-project state leaking into the diagram (which the acceptance forbids outright)
or the driver reading a frame the page had not finished assembling. This probe answers which,
by reading the project object the renderer itself reads, not the pixels.
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
import urllib.request

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

import tools.drive_run16_final_flow as r16  # noqa: E402

r16.PORT = 8232
r16.BASE = f"http://127.0.0.1:{r16.PORT}"
r16.ADMIN = "r23-probe-admin"
r16.EMPTY = "PRJ-R23P-EMPTY"
r16.FULL = "PRJ-R23P-FULL"
r16.ONEDOC = "PRJ-R23P-ONEDOC"

READ_STATE = r"""
() => {
  const all = (window.LIN_PROJECTS || []).concat(window.LIN_ARCHIVED || []);
  const proj = all.find(x => x && x.id === window.__pid) || null;
  if (!proj) return { found: false };
  const sig = proj.signals || {};
  const sim = (proj.simulationSignals && proj.simulationSignals.signal_array) || [];
  return {
    found: true, id: proj.id,
    decision: sig.decision ? JSON.stringify(sig.decision).slice(0, 300) : null,
    mc: sig.mc ? sig.mc.status : null,
    cusum: sig.cusum ? sig.cusum.status : null,
    doc: sig.doc ? sig.doc.status : null,
    simCount: sim.length,
    reds: sim.filter(r => String(r.status_color || '').toLowerCase() === 'red')
             .map(r => r.method_class),
    ambers: sim.filter(r => String(r.status_color || '').toLowerCase() === 'amber')
             .map(r => r.method_class),
    fusion: window.getProjectFusion ? JSON.stringify(window.getProjectFusion(proj)).slice(0, 200) : null,
  };
}
"""


def main() -> None:
    import uvicorn
    from playwright.sync_api import sync_playwright
    import app.main as main_app
    from app.documents import set_extractor_override
    from app.extraction_client import StubExtractor

    set_extractor_override(StubExtractor(r16.records()))
    cfg = uvicorn.Config(main_app.app, host="127.0.0.1", port=r16.PORT, log_level="critical")
    threading.Thread(target=uvicorn.Server(cfg).run, daemon=True).start()
    for _ in range(120):
        try:
            urllib.request.urlopen(r16.BASE + "/readyz", timeout=2).read()
            break
        except Exception:
            time.sleep(0.5)
    pm = r16.seed()
    print("server row:", json.dumps(r16.server_state(pm, r16.FULL, 1)))

    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=r16.SHELL,
                               args=["--use-gl=swiftshader", "--enable-webgl",
                                     "--ignore-gpu-blocklist", "--no-sandbox"])
        page = b.new_page(viewport={"width": 1680, "height": 1400})
        page.set_default_timeout(45000)
        for pat in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                    "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
            page.route(pat, lambda r: r.abort())
        page.goto(r16.BASE + "/", wait_until="domcontentloaded")
        page.evaluate("tok => sessionStorage.setItem('og-session-token', tok)", pm)
        page.goto(r16.BASE + "/", wait_until="domcontentloaded")
        page.wait_for_timeout(8000)

        def snap(tag: str, pid: str) -> None:
            page.evaluate("id => { window.__pid = id; }", pid)
            st = page.evaluate(READ_STATE)
            print(f"\n--- {tag} ({pid})")
            print(json.dumps(st, indent=1)[:1400])

        r16.open_detail(page, r16.FULL)
        snap("first visit", r16.FULL)
        page.wait_for_timeout(6000)
        snap("first visit, +6s", r16.FULL)
        r16.open_detail(page, r16.EMPTY)
        snap("empty", r16.EMPTY)
        r16.open_detail(page, r16.FULL)
        snap("back to populated", r16.FULL)
        page.wait_for_timeout(6000)
        snap("back to populated, +6s", r16.FULL)
        b.close()


if __name__ == "__main__":
    main()
