"""
RUN 22 ITEM 7. WHAT THE ~195-SECOND RELOAD ACTUALLY IS.

WHAT RUN 21 ESTABLISHED AND WHERE IT STOPPED. The reload really happens: a sentinel written onto
`window` before the reload is gone afterwards, which only a destroyed document can produce. The
application really comes back and really reconstructs the same state from the server. Playwright's
`page.reload(wait_until="commit")` nevertheless times out at 45 s, and the driver's own polling
loop saw the application ready at about 195 s. Run 21 said plainly that it had not determined
whether that number is a container artefact or a cost a participant would meet, and left it as a
release blocker for this run.

WHY ELAPSED WALL TIME CANNOT ANSWER IT, AND WHY THIS PROBE IS BUILT THE WAY IT IS. The 195 s in
Run 21's evidence is the elapsed time of a POLLING LOOP that calls `page.evaluate` every two
seconds, and its own note records the shape of the problem: "1 successful reads, 1 evaluate errors
while the document was navigating". Two data points in 212 seconds. `page.evaluate` blocks while
the execution context is being replaced, so that loop measures the moment Playwright was willing
to answer, which is an upper bound on the page's readiness and not a measurement of it. Widening
the timeout would have hidden the question; the owner's rule forbids it and it would have been
the wrong instrument anyway.

So this probe never asks Playwright when the page was ready. It subscribes to browser EVENTS --
`domcontentloaded`, `load`, and every `request`/`response`/`requestfailed` -- which are delivered
over CDP as they happen and do not depend on an execution context existing, and it then reads the
new document's own `performance` timeline, which is the browser's record of its own navigation
and is immune to anything the harness does. Where those two disagree, the browser is right.

THE VARIANTS, AND WHAT EACH ISOLATES.
    A  reload, populated project, third parties aborted exactly as the Run-21 driver does
    B  reload, populated project, NOTHING aborted -- isolates whether the abort routing is
       itself the cost, which would make the harness the cause
    C  goto the same URL instead of reload, populated project -- isolates the reload PRIMITIVE
       from the page's own cost, because both fetch and rebuild the same document
    D  reload, empty project -- isolates the cost of rebuilding project state from the cost of
       loading the document
    E  reload in a fresh context with no project open -- the participant's first-load path

Nothing here changes production. This file is a measuring instrument.
"""

from __future__ import annotations

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

r16.PORT = 8223
r16.BASE = f"http://127.0.0.1:{r16.PORT}"
r16.ADMIN = "r22-reload-admin"
r16.EMPTY = "PRJ-R22-EMPTY"
r16.FULL = "PRJ-R22-FULL"
r16.ONEDOC = "PRJ-R22-ONEDOC"
r16.LABEL = "run22_reload"

BASE = r16.BASE
THIRD_PARTY = ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
               "**tiles.openfreemap.org**", "**maps.googleapis.com**")

ROWS: list[dict] = []


def classify(url: str) -> str:
    """The owner's classification, applied to a URL. Local paths are resolved by their role."""
    if "accounts.google.com" in url or "apis.google.com" in url:
        return "AUTH"
    if "tiles.openfreemap.org" in url or "maps.googleapis.com" in url:
        return "TILE/MAP"
    if "gstatic.com" in url or "googletagmanager" in url:
        return "EXTERNAL_OPTIONAL"
    if not url.startswith(BASE):
        return "EXTERNAL_OPTIONAL"
    tail = url[len(BASE):]
    if tail.startswith("/exec") or tail.startswith("/api"):
        return "REQUIRED_API"
    if tail.startswith("/assets/vendor/"):
        return "CORE_APPLICATION"
    if tail.startswith("/assets/") or tail in ("/", "/index.html", "/logo.png"):
        return "CORE_APPLICATION"
    return "OTHER"


def instrument(page) -> dict:
    """
    Subscribes to the events that do not need an execution context.

    Returns a mutable record. `t0` is set by the caller immediately before the navigation is
    triggered, so every timestamp below is an offset from the instant the participant asked for
    the reload -- which is the only zero that means anything to a participant.
    """
    rec: dict = {"t0": None, "dcl": None, "load": None, "requests": [], "first_response": None}

    def on_response(resp):
        if rec["t0"] is None:
            return
        dt = time.time() - rec["t0"]
        if rec["first_response"] is None and resp.url.rstrip("/") == BASE:
            rec["first_response"] = dt
        rec["requests"].append((resp.url, classify(resp.url), dt, resp.status))

    def on_failed(req):
        if rec["t0"] is None:
            return
        rec["requests"].append((req.url, classify(req.url), time.time() - rec["t0"], "FAILED"))

    page.on("domcontentloaded",
            lambda _p: rec.__setitem__("dcl", time.time() - rec["t0"]) if rec["t0"] else None)
    page.on("load",
            lambda _p: rec.__setitem__("load", time.time() - rec["t0"]) if rec["t0"] else None)
    page.on("response", on_response)
    page.on("requestfailed", on_failed)
    return rec


def poll_usable(page, rec: dict, budget: float) -> dict:
    """
    When the instrument becomes USABLE, which is the participant-facing metric.

    Deliberately separated from the browser lifecycle: `load` waits for every subresource
    including ones no participant needs, and readiness for a participant is that the application
    object exists and the controls are in the DOM. Both are polled; both are reported; neither is
    allowed to stand in for the other.
    """
    out = {"app_object": None, "controls": None, "ready_state_at_app": None, "evaluate_errors": 0,
           "evaluate_reads": 0}
    deadline = time.time() + budget
    while time.time() < deadline:
        try:
            st = page.evaluate("""() => ({
                app: !!(window.LinApp && window.LinApp.openDetail),
                controls: !!document.querySelector('#projects, #project-list, .project-card, '
                          + '#detail-root, #section-d-neural'),
                ready: document.readyState
            })""")
            out["evaluate_reads"] += 1
            dt = time.time() - rec["t0"]
            if st["app"] and out["app_object"] is None:
                out["app_object"] = dt
                out["ready_state_at_app"] = st["ready"]
            if st["controls"] and out["controls"] is None:
                out["controls"] = dt
            if out["app_object"] is not None and out["controls"] is not None:
                break
        except Exception:
            out["evaluate_errors"] += 1
        time.sleep(0.25)
    return out


def perf_timeline(page) -> dict:
    """
    The BROWSER'S OWN record of the navigation it just performed.

    This is the authority. It is produced inside the document by the user agent, so no harness
    wait semantics, route handler or CDP round trip can inflate it. Where this and the harness
    disagree about how long the page took, this is the measurement and the harness is the artefact.
    """
    try:
        return page.evaluate("""() => {
            const n = performance.getEntriesByType('navigation')[0];
            const rs = performance.getEntriesByType('resource')
                .map(r => ({name: r.name, start: r.startTime, dur: r.duration}))
                .sort((a, b) => b.dur - a.dur).slice(0, 15);
            return n ? {
                requestStart: n.requestStart, responseStart: n.responseStart,
                responseEnd: n.responseEnd, domInteractive: n.domInteractive,
                domContentLoaded: n.domContentLoadedEventEnd, domComplete: n.domComplete,
                loadEvent: n.loadEventEnd, duration: n.duration, slowest: rs
            } : {error: 'no navigation entry', slowest: rs};
        }""")
    except Exception as exc:
        return {"error": str(exc)[:200]}


def row(variant: str, name: str, value, note: str = "") -> None:
    ROWS.append({"variant": variant, "measurement": name, "value": str(value), "note": note})
    print(f"  {variant:26} {name:34} {value}")


def run_variant(pw, variant: str, *, abort_third_party: bool, populated: bool,
                use_goto: bool, open_project: bool, token: str) -> None:
    print(f"\n--- {variant}")
    b = pw.chromium.launch(executable_path=SHELL,
                           args=["--use-gl=swiftshader", "--enable-webgl",
                                 "--ignore-gpu-blocklist", "--no-sandbox"])
    try:
        p = b.new_page(viewport={"width": 1680, "height": 1400})
        p.set_default_timeout(45000)
        p.set_default_navigation_timeout(45000)
        if abort_third_party:
            for pattern in THIRD_PARTY:
                p.route(pattern, lambda r: r.abort())
        p.goto(BASE + "/", wait_until="domcontentloaded")
        p.evaluate("tok => sessionStorage.setItem('og-session-token', tok)", token)
        p.goto(BASE + "/", wait_until="domcontentloaded")
        p.wait_for_timeout(6000)
        if open_project:
            r16.open_detail(p, r16.FULL if populated else r16.EMPTY)

        rec = instrument(p)
        p.evaluate("() => { window.__r22_sentinel = 'before'; }")
        rec["t0"] = time.time()
        primitive_err = ""
        t_prim = None
        try:
            if use_goto:
                p.goto(BASE + "/", wait_until="commit", timeout=45000)
            else:
                p.reload(wait_until="commit", timeout=45000)
            t_prim = time.time() - rec["t0"]
        except Exception as exc:
            primitive_err = str(exc).splitlines()[0][:120]
            t_prim = time.time() - rec["t0"]

        usable = poll_usable(p, rec, budget=600)
        sentinel = None
        try:
            sentinel = p.evaluate("() => window.__r22_sentinel || null")
        except Exception:
            sentinel = "unreadable"

        row(variant, "primitive", "returned" if not primitive_err else "timed_out",
            primitive_err)
        row(variant, "primitive_seconds", f"{t_prim:.2f}")
        row(variant, "document_destroyed", "yes" if sentinel is None else f"no ({sentinel})",
            "the sentinel proves a real document reload")
        row(variant, "first_response_seconds",
            "n/a" if rec["first_response"] is None else f"{rec['first_response']:.2f}",
            "time to the server's HTML response")
        row(variant, "domcontentloaded_seconds",
            "n/a" if rec["dcl"] is None else f"{rec['dcl']:.2f}")
        row(variant, "app_object_seconds",
            "n/a" if usable["app_object"] is None else f"{usable['app_object']:.2f}",
            "core application initialised")
        row(variant, "controls_usable_seconds",
            "n/a" if usable["controls"] is None else f"{usable['controls']:.2f}",
            "PARTICIPANT-FACING METRIC")
        row(variant, "load_event_seconds",
            "never" if rec["load"] is None else f"{rec['load']:.2f}",
            "includes nonessential subresources")
        row(variant, "readyState_when_app_ready", usable["ready_state_at_app"])
        row(variant, "evaluate_reads", usable["evaluate_reads"])
        row(variant, "evaluate_errors", usable["evaluate_errors"])

        by_class: dict[str, list[float]] = {}
        for url, kind, dt, status in rec["requests"]:
            by_class.setdefault(kind, []).append(dt)
        for kind in sorted(by_class):
            row(variant, f"last_{kind}_seconds", f"{max(by_class[kind]):.2f}",
                f"{len(by_class[kind])} requests")
        slow = sorted(rec["requests"], key=lambda r: -r[2])[:5]
        for url, kind, dt, status in slow:
            row(variant, "slowest_request", f"{dt:.2f}s {kind} {status}", url[:140])

        perf = perf_timeline(p)
        for k in ("responseStart", "responseEnd", "domInteractive", "domContentLoaded",
                  "domComplete", "loadEvent", "duration"):
            if k in perf:
                row(variant, f"browser_perf_{k}_ms", f"{perf[k]:.0f}",
                    "the browser's own navigation timeline")
        for entry in (perf.get("slowest") or [])[:5]:
            row(variant, "browser_slowest_resource",
                f"{entry['dur']:.0f}ms", entry["name"][:140])
        if "error" in perf:
            row(variant, "browser_perf_error", perf["error"])
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
        run_variant(pw, "A_reload_populated_3p_aborted", abort_third_party=True,
                    populated=True, use_goto=False, open_project=True, token=token)
        run_variant(pw, "B_reload_populated_3p_allowed", abort_third_party=False,
                    populated=True, use_goto=False, open_project=True, token=token)
        run_variant(pw, "C_goto_populated_3p_aborted", abort_third_party=True,
                    populated=True, use_goto=True, open_project=True, token=token)
        run_variant(pw, "D_reload_empty_3p_aborted", abort_third_party=True,
                    populated=False, use_goto=False, open_project=True, token=token)
        run_variant(pw, "E_reload_no_project_3p_aborted", abort_third_party=True,
                    populated=False, use_goto=False, open_project=False, token=token)

    out = ROOT / "code_audit" / "run22_reload_diagnostics.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["variant", "measurement", "value", "note"])
        w.writeheader()
        w.writerows(ROWS)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
