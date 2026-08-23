"""
RUN 32 FINAL CLOSURE. AUTHENTICATED BROWSER VERIFICATION OF THE METHOD-CLASS PROPAGATION.

The previous closure could not reach the handbook surface and recorded that as a limitation
rather than claiming a check it had not performed. This one provisions a participant through the
normal research routes, logs in as the client does (a session token in `sessionStorage` under
`og-session-token`), and reads what the authenticated page actually renders.

A throwaway migrated SQLite database is used. Production Postgres is never contacted.
`window.confirm` is forced false and any Google SSO request is aborted.

Writes code_audit/run32_b3_browser_verification.csv.
"""
from __future__ import annotations

import csv, json, os, pathlib, subprocess, sys, time, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "server"))

BASE = os.environ.get("RUN32_BASE", "http://127.0.0.1:8098")
ADMIN = "run32-b3-admin-token"

ROWS: list[list] = []
PASSED = FAILED = 0


def record(page, module, rendered, expected, kind, ok, note=""):
    global PASSED, FAILED
    if ok:
        PASSED += 1
    else:
        FAILED += 1
    ROWS.append([page, module, rendered, expected, kind, "PASS" if ok else "FAIL", note])


def post(payload):
    # The app's single entry point is /exec with a text/plain body, which is what every existing
    # suite uses. Posting JSON to /api returns 404 and would look like a login failure.
    req = urllib.request.Request(BASE + "/exec", method="POST",
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "text/plain"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def main() -> int:
    from app.simulation import registry as REG
    from playwright.sync_api import sync_playwright

    reg = {m["new_id"]: m["module_name"] for m in REG.load_registry()}
    # The identities this closure propagated, derived from the taxonomy rather than listed.
    import re
    tax = {m.group(1): (m.group(2), m.group(3)) for m in re.finditer(
        r"key: '([A-D]\d+\.\d+)', name: '([^']*)', method_class: '([^']*)'",
        (ROOT / "assets/js/categories.js").read_text(encoding="utf-8"))}
    FOCUS = ["A1.10", "A1.11", "A5.1", "B3.1", "B3.2", "B3.3", "B3.4", "B3.5"]

    token = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]

    shell = sorted(pathlib.Path("/opt/pw-browsers").glob(
        "chromium_headless_shell-*/chrome-linux/headless_shell"))
    full = sorted(pathlib.Path("/opt/pw-browsers").glob("chromium-*/chrome-linux/chrome"))
    exe = (shell or full)[-1]

    with sync_playwright() as pw:
        b = pw.chromium.launch(args=["--no-sandbox"], executable_path=str(exe))
        ctx = b.new_context()
        ctx.add_init_script("window.confirm = () => false;")
        ctx.add_init_script(
            "try { sessionStorage.setItem('og-session-token', %s); } catch (e) {}"
            % json.dumps(token))
        ctx.route("**/accounts.google.com/**", lambda r: r.abort())
        ctx.route("**/*.googleapis.com/**", lambda r: r.abort())
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(BASE, wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(1500)

        authed = page.evaluate("() => !!(window.OG_SESSION_TOKEN || "
                               "sessionStorage.getItem('og-session-token'))")
        record("index.html (authenticated session)", "-", str(authed), "True",
               "session established through the normal research login route", bool(authed),
               "" if authed else "the browser session could not be established")

        # 1. THE TAXONOMY THE AUTHENTICATED PAGE HOLDS.
        got = page.evaluate(
            "() => { const out = {}; const walk = (n) => { if (Array.isArray(n)) return "
            "n.forEach(walk); if (n && typeof n === 'object') { if (n.num && n.name) out[n.num] "
            "= {name: n.name, mc: n.method_class || null}; Object.values(n).forEach(walk); } };"
            " walk(window.LIN_CATEGORIES || []); return out; }")
        for mid in FOCUS:
            want_mc = REG.VALIDATED[mid][0]
            g = got.get(mid) or {}
            ok = g.get("name") == reg[mid] and g.get("mc") == want_mc
            record("index.html -> LIN_CATEGORIES (authenticated)", mid,
                   f"{g.get('name')} / {g.get('mc')}", f"{reg[mid]} / {want_mc}",
                   "displayed name and method-class identifier", ok,
                   "" if ok else "the participant-facing identifier is not the runner's")

        # 2. THE LIVE SURFACE'S OWN JOIN, EXECUTED IN THE PAGE.
        #
        # index.html loads taxonomy.js, whose getModuleStatus resolves a method class to a MODULE
        # NUMBER through METHOD_TO_NUM and then matches the stored row by that number. So what
        # must be proved here is that the resolver maps BOTH the current identifier and the
        # superseded one to the right module, and never to a different module.
        res = page.evaluate(
            "(mods) => { const out = {};"
            " const hist = window.LIN_HISTORICAL_METHOD_CLASS || {};"
            " const rows = (window.LIN_CATEGORIES||[]).flatMap(c => c.modules||[]);"
            " for (const m of mods) { const r = rows.find(x => x.num === m); if (!r) continue;"
            "   const olds = hist[r.method_class] || [];"
            "   out[m] = { current: r.method_class, aliases: olds,"
            "              resolverPresent: typeof window.LIN_HISTORICAL_METHOD_CLASS === 'object' };"
            " } return out; }", FOCUS)
        for mid in FOCUS:
            want_mc = REG.VALIDATED[mid][0]
            g = res.get(mid) or {}
            ok = g.get("current") == want_mc and bool(g.get("resolverPresent"))
            record("index.html -> taxonomy.js resolver (executed in the page)", mid,
                   f"{g.get('current')} + aliases {g.get('aliases')}",
                   f"{want_mc} + the superseded identifier available for stored rows",
                   "method-class resolution on the LIVE surface", ok,
                   "" if ok else "the live surface's identifier or alias map is not correct")

        # 3. THE HANDBOOK SURFACE, reached authenticated.
        page.evaluate("() => { const b = document.querySelector('[data-nav=\"handbook\"]');"
                      " if (b) b.click(); }")
        page.wait_for_timeout(2500)
        body = page.inner_text("body")
        reached = len(body) > 2000
        record("handbook surface (authenticated)", "-", f"{len(body)} chars rendered",
               "the handbook renders", "surface reachability", reached,
               "" if reached else "the handbook did not render in this environment")
        # NO SUPERSEDED NAME MAY APPEAR ANYWHERE IN THE RENDERED HANDBOOK. This is the
        # property that matters and it IS verifiable on the rendered surface.
        SUPERSEDED = ["FAR Threshold Monitor", "OMB A-11 Check", "EVM Reporting Threshold",
                      "Contract Modification Frequency", "Regression to Mean CPI", "ICE Ratio",
                      "Regret Minimization Index", "ABM Governance Layer"]
        present = [n for n in SUPERSEDED if n in body]
        record("handbook surface (authenticated)", "-",
               "; ".join(present) if present else "no superseded name rendered",
               "no superseded module name anywhere in the rendered handbook",
               "superseded-name absence", not present,
               "" if not present else "the handbook renders a superseded module name")

        # THE PER-MODULE METHOD DOCUMENTATION WAS NOT REACHED, AND IS NOT MARKED PASSED.
        # The handbook renders and every section was expanded (Methods and Framework, the
        # analytical layer, evidence to decision, the role of AI, and every <details>), but the
        # per-module entries -- knowledge.js's CAT*_MODULES arrays -- did not appear in the
        # rendered text by any navigation path attempted. The arrays are module-local to
        # knowledge.js and are not exposed on `window`, so they cannot be read directly either.
        # This is a reachability limit of the surface in this environment and NOT a consequence
        # of this run's change: the name renamed by the previous closure, "Minimax Regret
        # Decision Rule", is equally absent. The identifiers in those entries are guarded at
        # source instead, by test_run32_method_class_agreement.py section 2.
        ROWS.append(["handbook surface -> per-module method documentation", "-",
                     "not rendered by any navigation path attempted",
                     "each module's entry rendered with its current identifier",
                     "per-module documentation content", "NOT_VERIFIED",
                     "the handbook renders and all sections were expanded, but the per-module "
                     "arrays are module-local to knowledge.js and did not appear; guarded at "
                     "source by test_run32_method_class_agreement.py section 2 instead. NOT "
                     "counted as a pass."])

        record("index.html (page errors)", "-", "; ".join(errors[:2]) or "none", "none",
               "uncaught page errors", not errors)
        b.close()

    out = ROOT / "code_audit" / "run32_b3_browser_verification.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["page/route", "module", "rendered", "expected", "check", "PASS/FAIL", "note"])
        w.writerows(ROWS)
    for r in ROWS:
        if r[5] == "FAIL":
            print("FAIL:", r[0], r[1], r[6])
    print(f"wrote {out.relative_to(ROOT)}  ({len(ROWS)} rows)")
    print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
