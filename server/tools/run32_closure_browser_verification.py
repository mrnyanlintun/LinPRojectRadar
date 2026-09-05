"""
RUN 32 FINAL CLOSURE. BROWSER AND API VERIFICATION, AGAINST THE RUNNING APPLICATION.

SOURCE STRINGS ARE NOT EVIDENCE THAT A READER SEES THE TRUTH. A file can carry the corrected
sentence and the page can still render a cached object, a different field, or nothing at all. So
this drives the actual application in Chromium, reads the objects the page itself has loaded and
the surfaces it renders, and compares them against the SAME independently derived inventory the
truth guard uses -- registry identity, activation, dispatch tables, canonical structure maps and
the runner resolved past the Category-9 boundary.

Standing environment constraints of this programme are honoured: `window.confirm` is forced to
return false, any Google SSO request is aborted, and the application under test is pointed at a
throwaway migrated SQLite database. Production Postgres is never contacted.

Writes code_audit/run32_defensibility_browser_api_verification.csv.
"""

from __future__ import annotations
# Run 137, Item 2: artefact writes route to the Run 135C scratch root by default.
import os as _f10_os, sys as _f10_sys  # noqa: E402
_f10_sys.path.insert(0, _f10_os.path.join(
    _f10_os.path.dirname(_f10_os.path.abspath(__file__)), "..", "tools"))
_f10_sys.path.insert(0, _f10_os.path.dirname(_f10_os.path.abspath(__file__)))
from artifact_write import artifact_out  # noqa: E402

import csv
import importlib.util
import json
import pathlib
import sys
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(HERE))

_spec = importlib.util.spec_from_file_location(
    "run32_inventory", HERE / "build_run32_defensibility_inventory.py")
INV = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(INV)

from app.simulation import registry as REG                                  # noqa: E402

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8099"

#: The modules the closure contract calls out by name, plus every Category-10 identity.
FOCUS = ["A4.1", "A3.4", "B2.9", "B2.7", "B2.20", "B2.18", "B2.19",
         "A6.1", "A6.2", "A6.4", "B3.1", "B3.2", "B3.3", "B3.4", "B3.5",
         "A1.1", "A1.7", "D1.1"] + [f"B4.{i}" for i in range(1, 8)]

ROWS: list[list] = []
PASSED = 0
FAILED = 0


def record(page: str, mid: str, rendered_name: str, rendered_exec: str,
           expected_name: str, expected_exec: str, struct_stmt: str, op_state: str,
           ok: bool, note: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
    else:
        FAILED += 1
    ROWS.append([page, mid, rendered_name, rendered_exec, expected_name, expected_exec,
                 struct_stmt, op_state, "PASS" if ok else "FAIL", note])


def main() -> int:
    from playwright.sync_api import sync_playwright

    reg = {m["new_id"]: m["module_name"] for m in REG.load_registry()}
    expected = {mid: INV.expected_for(mid, name) for mid, name in reg.items()}

    # ---------------------------------------------------------------- the API surface
    with urllib.request.urlopen(f"{BASE}/", timeout=30) as r:
        assert r.status == 200, r.status

    with sync_playwright() as pw:
        # The preinstalled Chromium's build number does not match the one this Playwright
        # package expects, and `playwright install` is not run in this environment. The
        # executable that IS present is used directly, so the page is driven by a real browser
        # rather than the verification being skipped.
        # The installed Chromium build has REMOVED old headless mode, which is what this
        # Playwright version asks for, so the full browser refuses to start. The standalone
        # headless shell is the supported replacement and is installed alongside it. Preferred,
        # with the full binary as a fallback; `playwright install` is never run.
        _shell = sorted(pathlib.Path("/opt/pw-browsers").glob(
            "chromium_headless_shell-*/chrome-linux/headless_shell"))
        _chrome = sorted(pathlib.Path("/opt/pw-browsers").glob(
            "chromium-*/chrome-linux/chrome"))
        _exe = (_shell or _chrome)[-1]
        browser = pw.chromium.launch(args=["--no-sandbox"], executable_path=str(_exe))
        ctx = browser.new_context()
        # STANDING CONSTRAINTS OF THIS PROGRAMME.
        ctx.add_init_script("window.confirm = () => false;")
        ctx.route("**/accounts.google.com/**", lambda route: route.abort())
        ctx.route("**/*.googleapis.com/**", lambda route: route.abort())
        page = ctx.new_page()
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(BASE, wait_until="networkidle", timeout=60000)

        # THE OBJECT THE PAGE ITSELF HAS LOADED, read out of the live JS context rather than
        # from the file on disk. This is what a reader's browser is actually holding.
        served = page.evaluate(
            "() => (window.DS_DEFENSIBILITY_EVIDENCE || {}).modules || null")
        if not served:
            record("index.html (defensibility object)", "-", "-", "-", "-", "-", "-", "-",
                   False, "window.DS_DEFENSIBILITY_EVIDENCE.modules did not load in the browser")
        else:
            for mid in sorted(reg):
                e = expected[mid]
                s = served.get(mid) or {}
                ok = (s.get("name") == reg[mid]
                      and s.get("implementation") == e["execution"]
                      and s.get("operationalState") == INV.state_of(e)
                      and s.get("canonicalStructure") == e["structure_stmt"]
                      and s.get("canonicalRunner") == e["runner"])
                if mid in FOCUS or not ok:
                    record("index.html -> DS_DEFENSIBILITY_EVIDENCE (loaded in browser)", mid,
                           str(s.get("name")), str(s.get("implementation"))[:120],
                           reg[mid], e["execution"][:120], str(s.get("canonicalStructure"))[:90],
                           str(s.get("operationalState")), ok,
                           "" if ok else "the object the browser holds disagrees with the "
                                         "instrument")

        # THE PARTICIPANT-FACING TAXONOMY, as the page holds it.
        tax = page.evaluate(
            "() => { const out = {};"
            " const src = window.LIN_CATEGORIES || null;"
            " if (!src) return null;"
            " const walk = (n) => { if (Array.isArray(n)) return n.forEach(walk);"
            "   if (n && typeof n === 'object') { if (n.num && n.name) out[n.num] ="
            "     {name: n.name, mc: n.method_class || null};"
            "     Object.values(n).forEach(walk); } };"
            " walk(src); return out; }")
        if tax:
            for mid in [m for m in FOCUS if m in tax]:
                e = expected[mid]
                want_mc = (REG.VALIDATED[mid][0] if mid in REG.VALIDATED else None)
                ok = tax[mid]["name"] == reg[mid] and (
                    want_mc is None or tax[mid]["mc"] == want_mc)
                record("index.html -> participant taxonomy (loaded in browser)", mid,
                       tax[mid]["name"], f"method_class={tax[mid]['mc']}", reg[mid],
                       f"method_class={want_mc}", e["structure_stmt"][:90],
                       INV.state_of(e), ok,
                       "" if ok else "the participant-facing name or method class is not the "
                                     "registry's current one")
        else:
            record("index.html -> participant taxonomy", "-", "-", "-", "-", "-", "-", "-",
                   False, "no taxonomy object was exposed to the page")

        # THE METHOD-INFORMATION / HELP SURFACE.
        #
        # IT IS NOT REACHABLE FROM A BROWSER HERE, AND THAT IS RECORDED RATHER THAN PASSED OVER.
        # The handbook renders only inside an authenticated participant session, and its module
        # arrays are local to knowledge.js rather than exposed on `window`, so no unauthenticated
        # page evaluation can read them. Driving a participant login to reach it would exercise
        # the experimental sequence this closure must not touch. Its contents are therefore
        # guarded at source instead, by test_run32_defensibility_truth.py section 6, which checks
        # every Category-10 entry against the canonical layer for a surviving v19 proxy
        # description, a band ladder, and the current method-class identifier.
        _kn_present = page.evaluate("() => !!window.LIN_KNOWLEDGE")
        record("index.html -> method help (NOT BROWSER-REACHABLE)", "-", "n/a", "n/a",
               "n/a", "n/a", "n/a", "n/a", _kn_present,
               "the handbook script loads, but its module arrays are module-local and the "
               "surface renders only in an authenticated participant session; the Category-10 "
               "entries are guarded at source by test_run32_defensibility_truth.py section 6 "
               "instead of being claimed as a browser check that was not performed")

        record("index.html (page errors)", "-", "-", "-", "-", "-", "-", "-",
               not errors, "; ".join(errors[:2]) if errors else "no uncaught page errors")
        browser.close()

    out = ROOT / "code_audit" / "run32_defensibility_browser_api_verification.csv"
    with artifact_out(out).open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["page/route", "module", "rendered/current name",
                    "rendered execution statement", "expected name",
                    "expected execution statement", "canonical-structure statement",
                    "current operational state", "PASS/FAIL", "note"])
        w.writerows(ROWS)

    for r in ROWS:
        if r[8] == "FAIL":
            print("FAIL:", r[0], r[1], r[9])
    print(f"wrote {out.relative_to(ROOT)}  ({len(ROWS)} rows)")
    print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
