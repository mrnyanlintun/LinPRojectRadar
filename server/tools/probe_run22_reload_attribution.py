"""
RUN 22 ITEM 7, SECOND STAGE. WHAT THE ~54 SECONDS IS SPENT ON.

WHAT THE FIRST PROBE SETTLED. `probe_run22_reload_latency.py` measured the reload with browser
events and the document's own performance timeline instead of with harness wait semantics, and
three of the possible explanations died there.

    the server            responseStart 12 ms, responseEnd 21 ms. Not the server.
    third-party resources aborted 54.1 s vs allowed 59.1 s. About five seconds of fifty-four.
                          Not the third parties, so this is NOT the "blocked external resource"
                          outcome the owner's option A describes.
    the reload primitive  goto 58.5 s vs reload 54.1 s. The same cost either way, so it is not
                          `page.reload()` and not a reload-specific path.

What is left is a single interval: responseEnd at 21 ms to domInteractive at about 54 000 ms.
Every subresource in the browser's own resource timeline completes in under 53 ms. So the time is
not spent fetching anything. It is spent EXECUTING, on the renderer main thread, while the parser
is blocked -- which is also why `page.evaluate` could not answer and why Run 21's two-second
polling loop reported a number (195 s) that was an upper bound on readiness rather than a
measurement of it.

THE QUESTION THIS PROBE ANSWERS, AND WHY IT DECIDES THE RELEASE. Execution time on the main
thread splits into two kinds with opposite release consequences:

    SOFTWARE-RASTERISED GRAPHICS. The Run-21 driver launches the browser with
    `--use-gl=swiftshader --enable-webgl --ignore-gpu-blocklist`. swiftshader is a CPU
    implementation of the GL pipeline, chosen so a headless container with no GPU can render the
    3D charts at all. A participant's browser does not use it. If the interval is swiftshader,
    it is a HARNESS ARTEFACT: the qualification environment is paying a cost the study
    environment does not, and the owner's option C applies.

    APPLICATION JAVASCRIPT. Parsing and executing the shipped scripts, building state, laying
    out. A participant pays this on their own CPU. If the interval is application JavaScript then
    it is the owner's option B, a real instrument-performance defect, and no amount of
    reclassification makes a three-minute -- or even a fifty-four-second -- reload acceptable.

HOW IT IS SEPARATED, WITHOUT GUESSING. The same populated project is reloaded under three GL
configurations that differ in nothing else: swiftshader as Run 21 launches it, the browser's own
default (SwiftShader not forced), and WebGL disabled outright. If the interval collapses when the
software GL pipeline is taken away, the interval was the software GL pipeline. A CPU profile is
captured through the DevTools protocol in the swiftshader configuration as well, so the answer
does not rest on the three-way comparison alone: the profile names the functions.

Nothing here changes production.
"""

from __future__ import annotations

import collections
import csv
import pathlib
import sys
import threading
import time
import urllib.request

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

import tools.drive_run16_final_flow as r16  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
SHELL = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"

r16.PORT = 8224
r16.BASE = f"http://127.0.0.1:{r16.PORT}"
r16.ADMIN = "r22-attrib-admin"
r16.EMPTY = "PRJ-R22A-EMPTY"
r16.FULL = "PRJ-R22A-FULL"
r16.ONEDOC = "PRJ-R22A-ONEDOC"
r16.LABEL = "run22_attrib"

BASE = r16.BASE
THIRD_PARTY = ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
               "**tiles.openfreemap.org**", "**maps.googleapis.com**")

#: The three GL configurations. Only the GL flags differ.
CONFIGS: tuple[tuple[str, list[str], str], ...] = (
    ("swiftshader_as_run21",
     ["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist", "--no-sandbox"],
     "exactly the flags drive_run21_instrument.py launches with"),
    ("browser_default_gl", ["--no-sandbox"],
     "no GL flags forced; the browser decides, as a participant's browser does"),
    ("webgl_disabled", ["--disable-webgl", "--disable-gpu", "--no-sandbox"],
     "WebGL removed outright, so any 3D surface cannot render at all"),
)

ROWS: list[dict] = []


def row(config: str, name: str, value, note: str = "") -> None:
    ROWS.append({"config": config, "measurement": name, "value": str(value), "note": note})
    print(f"  {config:22} {name:32} {value}   {note}")


def measure(pw, config: str, args: list[str], why: str, token: str, profile: bool) -> None:
    print(f"\n--- {config}: {why}")
    b = pw.chromium.launch(executable_path=SHELL, args=args)
    try:
        p = b.new_page(viewport={"width": 1680, "height": 1400})
        p.set_default_timeout(45000)
        p.set_default_navigation_timeout(45000)
        for pattern in THIRD_PARTY:
            p.route(pattern, lambda r: r.abort())
        p.goto(BASE + "/", wait_until="domcontentloaded")
        p.evaluate("tok => sessionStorage.setItem('og-session-token', tok)", token)
        p.goto(BASE + "/", wait_until="domcontentloaded")
        p.wait_for_timeout(6000)
        r16.open_detail(p, r16.FULL)

        dcl: list[float] = []
        t0 = time.time()
        p.on("domcontentloaded", lambda _p: dcl.append(time.time() - t0))

        cdp = None
        if profile:
            cdp = p.context.new_cdp_session(p)
            cdp.send("Profiler.enable")
            cdp.send("Profiler.setSamplingInterval", {"interval": 1000})
            cdp.send("Profiler.start")

        t0 = time.time()
        try:
            p.reload(wait_until="commit", timeout=45000)
        except Exception:
            pass

        usable = None
        deadline = time.time() + 400
        while time.time() < deadline:
            try:
                if p.evaluate("() => !!(window.LinApp && window.LinApp.openDetail)"):
                    usable = time.time() - t0
                    break
            except Exception:
                pass
            time.sleep(0.25)

        row(config, "gl_flags", " ".join(a for a in args if a != "--no-sandbox") or "(none)", why)
        row(config, "app_usable_seconds", "never" if usable is None else f"{usable:.2f}",
            "core application initialised after the reload")
        row(config, "domcontentloaded_seconds", f"{dcl[-1]:.2f}" if dcl else "n/a")
        try:
            perf = p.evaluate("""() => {
                const n = performance.getEntriesByType('navigation')[0];
                return n ? {ri: n.responseEnd, di: n.domInteractive, dc: n.domContentLoadedEventEnd}
                         : null;
            }""")
            if perf:
                row(config, "browser_responseEnd_ms", f"{perf['ri']:.0f}",
                    "the server's part, from the browser's own timeline")
                row(config, "browser_domInteractive_ms", f"{perf['di']:.0f}",
                    "parser finished and blocking scripts executed")
                row(config, "browser_main_thread_ms", f"{perf['di'] - perf['ri']:.0f}",
                    "THE INTERVAL IN QUESTION: responseEnd to domInteractive")
        except Exception as exc:
            row(config, "browser_perf_error", str(exc)[:120])

        if cdp is not None:
            try:
                prof = cdp.send("Profiler.stop")["profile"]
                nodes = {n["id"]: n for n in prof["nodes"]}
                hits: collections.Counter = collections.Counter()
                for nid in prof.get("samples", []):
                    n = nodes.get(nid)
                    if not n:
                        continue
                    cf = n["callFrame"]
                    url = cf.get("url") or "(no url)"
                    short = url.rsplit("/", 1)[-1] or url
                    hits[f"{short}:{cf.get('functionName') or '(anonymous)'}"] += 1
                total = sum(hits.values()) or 1
                interval_ms = 1.0  # 1000 microseconds
                row(config, "cpu_profile_samples", total,
                    "sampled at 1 ms through the DevTools Profiler")
                for label, n in hits.most_common(12):
                    row(config, "cpu_profile_top", f"{n * interval_ms:.0f}ms "
                                                   f"({100 * n / total:.1f}%)", label)
            except Exception as exc:
                row(config, "cpu_profile_error", str(exc)[:160])
    finally:
        b.close()


def main() -> None:
    import uvicorn
    from playwright.sync_api import sync_playwright

    import app.main as main_app
    from app.documents import set_extractor_override
    from app.extraction_client import StubExtractor

    set_extractor_override(StubExtractor(r16.records()))
    config = uvicorn.Config(main_app.app, host="127.0.0.1", port=r16.PORT, log_level="critical")
    server = uvicorn.Server(config)
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(120):
        try:
            urllib.request.urlopen(BASE + "/readyz", timeout=2).read()
            break
        except Exception:
            time.sleep(0.5)

    token = r16.seed()
    with sync_playwright() as pw:
        for name, args, why in CONFIGS:
            measure(pw, name, args, why, token, profile=(name == "swiftshader_as_run21"))

    out = ROOT / "code_audit" / "run22_reload_attribution.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["config", "measurement", "value", "note"])
        w.writeheader()
        w.writerows(ROWS)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
