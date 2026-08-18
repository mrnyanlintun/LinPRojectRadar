"""
RUN 32 FINAL CLOSURE. AUTHENTICATED BROWSER VERIFICATION OF THE QUALIFIER AND AUTHORITY CLOSURE.

THE PER-MODULE HANDBOOK SURFACE EXISTS AND IS REACHED HERE. Two earlier closures recorded it
NOT_VERIFIED because the navigation was wrong, not because the surface was absent: it lives behind
Handbook -> the "Methods and Framework" tab -> a per-category "module reference" topic, and it
renders every module's documentation including the "Status. Proxy: ..." line that
RUN1_PROXY_QUALIFIER drives. Classification: CURRENT_REQUIRED_SURFACE.

A throwaway migrated SQLite database is used and the session is established through the normal
research login route. window.confirm returns false and Google SSO is aborted. Production Postgres
is never contacted.

Writes code_audit/run32_proxy_qualifier_browser_verification.csv.
"""
from __future__ import annotations

import csv, json, os, pathlib, re, sys, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "server"))

BASE = os.environ.get("RUN32_BASE", "http://127.0.0.1:8097")
TOKEN = os.environ.get("RUN32_TOKEN", "run32-qual-token")

ROWS: list[list] = []
PASSED = FAILED = 0


def record(page, module, consumer, mc, requested, resolved, rendered, expected,
           empty, historical, ok, note=""):
    global PASSED, FAILED
    if ok:
        PASSED += 1
    else:
        FAILED += 1
    ROWS.append([page, module, consumer, mc, requested, resolved, rendered, expected,
                 "YES" if empty else "NO", "YES" if historical else "NO",
                 "PASS" if ok else "FAIL", note])


def post(payload):
    req = urllib.request.Request(BASE + "/exec", method="POST",
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "text/plain"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def main() -> int:
    from app.simulation import registry as REG
    from app.simulation.portfolio import PORTFOLIO_VALIDATED as PV
    from playwright.sync_api import sync_playwright

    reg = {m["new_id"]: m["module_name"] for m in REG.load_registry()}
    qual_by_mc = {(REG.VALIDATED[k][0] if k in REG.VALIDATED else PV.get(k, k)): (k, v)
                  for k, v in REG.PROXY_QUALIFIERS.items()}
    token = post({"action": "researchlogin", "access_token": TOKEN})["session_token"]

    shell = sorted(pathlib.Path("/opt/pw-browsers").glob(
        "chromium_headless_shell-*/chrome-linux/headless_shell"))
    full = sorted(pathlib.Path("/opt/pw-browsers").glob("chromium-*/chrome-linux/chrome"))
    exe = (shell or full)[-1]

    with sync_playwright() as pw:
        b = pw.chromium.launch(args=["--no-sandbox"], executable_path=str(exe))
        ctx = b.new_context()
        ctx.add_init_script("window.confirm = () => false;")
        ctx.add_init_script("try { sessionStorage.setItem('og-session-token', %s); } catch (e) {}"
                            % json.dumps(token))
        ctx.route("**/accounts.google.com/**", lambda r: r.abort())
        ctx.route("**/*.googleapis.com/**", lambda r: r.abort())
        page = ctx.new_page()
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(BASE, wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(1200)

        # ---------------------------------------------------------- the runtime taxonomy
        live = page.evaluate(
            "() => { const out = {}; (window.LIN_CATEGORIES||[]).forEach(c => "
            "(c.modules||[]).forEach(m => out[m.num] = "
            "{name: m.name, mc: m.method_class, disabled: !!m.disabled})); return out; }")
        for mid in sorted(reg):
            g = live.get(mid) or {}
            want_mc = (REG.VALIDATED[mid][0] if mid in REG.VALIDATED
                       else PV.get(mid, g.get("mc")))
            ok = (g.get("name") == reg[mid] and g.get("mc") == want_mc
                  and g.get("disabled") == (mid in REG.DISABLED_MODULES))
            if not ok or mid in qual_by_mc or mid.startswith(("B3.", "B4.")):
                record("index.html -> LIN_CATEGORIES (authenticated runtime)", mid,
                       "taxonomy.js generated artifact", str(g.get("mc")), "n/a", "n/a",
                       f"{g.get('name')} / disabled={g.get('disabled')}",
                       f"{reg[mid]} / disabled={mid in REG.DISABLED_MODULES}",
                       False, False, ok,
                       "" if ok else "runtime taxonomy disagrees with the registry authority")

        # ---------------------------------------------------------- the handbook surface
        page.evaluate("() => { const b = document.querySelector('[data-nav=\"handbook\"]');"
                      " if (b) b.click(); }")
        page.wait_for_timeout(1800)
        page.evaluate("() => { const t = [...document.querySelectorAll('[id^=hb-tab-]')]"
                      ".find(e => /method/i.test(e.innerText || '')); if (t) t.click(); }")
        page.wait_for_timeout(2200)
        topics = page.evaluate(
            "() => [...document.querySelectorAll('[data-topic]')]"
            ".map(e => e.getAttribute('data-topic')).filter(t => /modules$/.test(t))")
        record("handbook -> Methods and Framework", "-", "MODREF topic navigation", "n/a",
               "n/a", "n/a", f"{len(topics)} module-reference topics",
               "the per-module handbook surface is reachable", False, False,
               len(topics) >= 8,
               "" if len(topics) >= 8 else "the per-module reference topics were not found")

        seen: dict[str, dict] = {}
        for t in topics:
            page.evaluate("(t) => { const b = document.querySelector(`[data-topic=\"${t}\"]`);"
                          " if (b) b.click(); }", t)
            page.wait_for_timeout(900)
            found = page.evaluate(
                # collapsibleSection() emits id="section-modref-<mc>" with the content in a
                # SIBLING "body-modref-<mc>" that is display:none until expanded. innerText is
                # empty for a hidden element, so textContent is what must be read -- otherwise
                # every section reads as blank and the check would pass or fail for the wrong
                # reason.
                "() => { const out = {};"
                " document.querySelectorAll('[id^=body-modref-]').forEach(sec => {"
                "   const key = sec.id.replace('body-modref-','');"
                "   const txt = sec.textContent || '';"
                "   const m = txt.match(/Status\\.\\s*Proxy:\\s*([^\\n]*?)\\.\\s*Advisory/);"
                "   out[key] = { title: (sec.innerText||'').split('\\n')[0].trim(),"
                "                proxy: m ? m[1] : null,"
                "                disabledLine: /Status\\.\\s*Disabled\\./.test(txt) };"
                " }); return out; }")
            seen.update(found)

        record("handbook -> module reference", "-", "modDoc() rendered sections", "n/a", "n/a",
               "n/a", f"{len(seen)} module sections rendered",
               "every documented module renders", False, False, len(seen) >= 90,
               "" if len(seen) >= 90 else "too few module sections rendered to verify")

        # Every rendered section is keyed by method_class. Check the qualifier it shows.
        for mc, sec in sorted(seen.items()):
            expected = qual_by_mc.get(mc)
            shown = sec.get("proxy")
            if expected:
                ok = shown is not None and shown.strip() == expected[1].strip()
                record("handbook -> module reference", expected[0],
                       "modDoc() RUN1_PROXY_QUALIFIER", mc, mc, mc if shown else "(no match)",
                       (shown or "no Proxy line")[:110], expected[1][:110],
                       shown is None, False, ok,
                       "" if ok else "a qualifier the server still holds did not render")
            elif shown is not None:
                mid = next((k for k, v in live.items() if v.get("mc") == mc), mc)
                record("handbook -> module reference", mid,
                       "modDoc() RUN1_PROXY_QUALIFIER", mc, mc, mc, shown[:110],
                       "no qualifier: the server holds none for this module",
                       False, True, False,
                       "a proxy qualifier is presented as current for a module the server no "
                       "longer qualifies")

        record("index.html (page errors)", "-", "console", "n/a", "n/a", "n/a",
               "; ".join(errors[:2]) or "none", "none", False, False, not errors)
        b.close()

    out = ROOT / "code_audit" / "run32_proxy_qualifier_browser_verification.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["page/route", "module", "consumer", "current method class",
                    "qualifier key requested", "qualifier key resolved", "rendered qualifier",
                    "expected qualifier", "lookup empty?", "historical content shown?",
                    "PASS/FAIL", "note"])
        w.writerows(ROWS)
    for r in ROWS:
        if r[10] == "FAIL":
            print("FAIL:", r[0], r[1], r[11])
    print(f"wrote {out.relative_to(ROOT)}  ({len(ROWS)} rows)")
    print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
