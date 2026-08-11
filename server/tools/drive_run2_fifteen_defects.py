#!/usr/bin/env python3
"""
Browser drive for the fifteen defects: the real pages, a real Chromium, a real server, both
themes.

WHY THIS EXISTS SEPARATELY FROM THE SUITE. `test_run2_fifteen_defects.py` proves the arithmetic
on the real computation path and reads it back through the API. It cannot tell you what a person
looking at the Signal Ledger sees. Several of the fifteen changed from a number to an abstention,
one changed from Green to Red and one changed the number it renders, and every one of those
changes lands on a row a project manager reads. This drives that page.

THE DRIVE IS PROVED ABLE TO FAIL END TO END. Two projects are seeded on the SAME server from
identical documents. The first computes on this branch's modules. The second computes with
the pinned baseline commit's own module functions swapped into the live server for the duration of its
computation, which is the shipped behaviour rather than an approximation of it. Then the same
page is driven for both and the rows are compared. If the page showed the same thing either way,
this run changed nothing that anybody can see, and the drive says so.

Container facts this script encodes so no session loses time on them again:
  - Chromium is at /opt/pw-browsers and the installed Playwright expects a different build, so
    the executable path is passed explicitly, and it is the headless SHELL because the full
    binary has had old headless mode removed.
  - The parser-blocking Google sign-in script is blackholed by the proxy; it and the map tile
    host, which is refused at CONNECT, are aborted here.
  - CSS transitions are suppressed before any computed style is read, or a frozen timeline
    returns the previous theme's values.

Run:
    DATABASE_URL=sqlite:///... SESSION_SECRET=... PYTHONIOENCODING=utf-8 \
        python tools/drive_run2_fifteen_defects.py
"""

from __future__ import annotations

import base64
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

ROOT = pathlib.Path(__file__).resolve().parents[2]
SHELL = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"

#: THE BASELINE COMMIT, PINNED BY SHA AND NOT BY BRANCH NAME.
#:
#: This must not be `origin/main`. The moment this run merges, `origin/main` becomes the FIXED
#: code, every "fails on the old code" half of every proof below would be comparing the fix with
#: itself, and the suite would go green while proving nothing. That is precisely the vacuous-check
#: failure this project keeps finding, and it would have been introduced by the suite written to
#: prevent it. The sha is the commit this branch was cut from: the last one carrying the fifteen
#: defects.
BASELINE_REV = "c2c609e"
PORT = 8123
BASE = f"http://127.0.0.1:{PORT}"
ADMIN = "r2-browser-admin"
FIXED_PRJ = "PRJ-R2-FIXED"
LEGACY_PRJ = "PRJ-R2-ASBEFORE"

PASSED = 0
FAILED = 0


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


MONTHS = {
    1: ("2026-03-31", 3_000_000, 3_050_000, 3_050_000, 25.0, 25.0),
    2: ("2026-04-30", 4_000_000, 4_250_000, 4_150_000, 33.0, 34.0),
    3: ("2026-05-31", 5_000_000, 5_500_000, 5_300_000, 42.0, 44.0),
    4: ("2026-06-30", 6_000_000, 6_900_000, 6_500_000, 50.0, 54.0),
}
EXTRAS = ("PROC", "PERF", "FIELD", "NCR", "OAC", "INSP")


def doc_bytes(prj: str, tag: str) -> bytes:
    return f"%PDF-1.4 RUN2 BROWSER {prj} {tag}\n".encode()


def records_for(prj: str) -> dict:
    d4 = "2026-06-30"
    rec = {}
    for p, m in MONTHS.items():
        rec[hashlib.sha256(doc_bytes(prj, f"M{p}")).hexdigest()] = ("monthly_report", {
            "earned_value": m[1], "actual_cost": m[2], "planned_value": m[3],
            "budget_at_completion": 12_000_000, "actual_percent_complete": m[4],
            "planned_percent_complete": m[5], "report_date": m[0], "document_date": m[0],
            "document_risk_score": 0.45})
    # The condition documents go into EVERY period, not only the last: the Signal Ledger draws
    # the project's current snapshot, and a row that has no document in that period reads "No
    # data" for reasons that have nothing to do with this run.
    for p, m in MONTHS.items():
        d = m[0]
        rec[hashlib.sha256(doc_bytes(prj, f"PROC{p}")).hexdigest()] = ("procurement_log", {
            "long_lead_items_total": 10, "at_risk": 8, "delayed": 5, "report_date": d})
        rec[hashlib.sha256(doc_bytes(prj, f"PERF{p}")).hexdigest()] = (
            "past_performance_report", {
                "overall_rating": 4.5, "schedule_rating": 4.2, "cost_rating": 4.4,
                "quality_rating": 2.0, "source": "Owner evaluation"})
        rec[hashlib.sha256(doc_bytes(prj, f"FIELD{p}")).hexdigest()] = ("field_report", {
            "weather_days_lost": 3, "quality_deficiencies_noted": 2, "document_date": d})
        rec[hashlib.sha256(doc_bytes(prj, f"NCR{p}")).hexdigest()] = ("ncr_log", {
            "ncr_issued": 2, "ncr_closed": 1, "ncr_open": 12, "report_period": d})
        rec[hashlib.sha256(doc_bytes(prj, f"OAC{p}")).hexdigest()] = ("oac_minutes", {
            "environmental_issues_discussed": 2, "safety_incidents_discussed": 0,
            "document_date": d})
        rec[hashlib.sha256(doc_bytes(prj, f"INSP{p}")).hexdigest()] = ("inspection_report", {
            "items_inspected": 40, "items_failed": 2, "deficiency_count": 2,
            "document_date": d})
    return rec


def post(payload: dict) -> dict:
    req = urllib.request.Request(BASE + "/exec", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "text/plain"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode())


# ---------------------------------------------------------------------------------------------
# the pinned baseline commit's own module functions, loaded for real (same mechanism the suite uses).
# ---------------------------------------------------------------------------------------------

def load_legacy():
    tmp = tempfile.mkdtemp(prefix="fifteen-defects-browser-baseline-")
    pkg = pathlib.Path(tmp) / "oldsim"
    pkg.mkdir()
    names = subprocess.run(
        ["git", "ls-tree", "--name-only", BASELINE_REV, "server/app/simulation/"],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    py = [n for n in names if n.endswith(".py")]
    if len(py) < 10:
        raise SystemExit("baseline extraction found nothing; refusing to drive only one half")
    for n in py:
        body = subprocess.run(["git", "show", f"{BASELINE_REV}:{n}"],
                              cwd=ROOT, capture_output=True, text=True, check=True).stdout
        (pkg / pathlib.Path(n).name).write_text(body, encoding="utf-8")
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    sys.path.insert(0, tmp)
    import oldsim.models  # noqa: F401  (root first: it registers the extension tables)
    import oldsim.fusion as of
    import oldsim.models_decision as od
    import oldsim.models_doc as odoc
    import oldsim.models_ext as oext
    import oldsim.models_gov as ogov
    import oldsim.models_sim as osim
    return of, od, odoc, oext, ogov, osim


#: (live module, attribute, legacy source module, legacy attribute). Every function this run
#: changed, so "as before" really is as before rather than as before in the parts that were
#: convenient.
def swap_table(of, od, odoc, oext, ogov, osim):
    import app.simulation.fusion as f
    import app.simulation.models_decision as d
    import app.simulation.models_doc as doc
    import app.simulation.models_ext as ext
    import app.simulation.models_gov as gov
    import app.simulation.models_sim as sim
    import app.simulation.portfolio as pf
    import oldsim.portfolio as opf
    return [
        (f, "dst_combine", of, "dst_combine"),
        (d, "run_conservative_dominance", od, "run_conservative_dominance"),
        (d, "run_abm_governance", od, "run_abm_governance"),
        (gov, "run_weighted_voting", ogov, "run_weighted_voting"),
        (gov, "run_majority_rules", ogov, "run_majority_rules"),
        (gov, "run_worst_n_of_m", ogov, "run_worst_n_of_m"),
        (gov, "run_whatif_matrix", ogov, "run_whatif_matrix"),
        (doc, "run_quality_compliance", odoc, "run_quality_compliance"),
        (doc, "run_procurement_lead_time", odoc, "run_procurement_lead_time"),
        (doc, "run_ncr_rate", odoc, "run_ncr_rate"),
        (doc, "run_weather_impact", odoc, "run_weather_impact"),
        (doc, "run_scenario_modeling", odoc, "run_scenario_modeling"),
        (doc, "run_contractor_performance", odoc, "run_contractor_performance"),
        (doc, "run_environmental_compliance", odoc, "run_environmental_compliance"),
        (ext, "run_cost_risk", oext, "run_cost_risk"),
        (ext, "run_float_consumption", oext, "run_float_consumption"),
        (sim, "run_monte_carlo", osim, "run_monte_carlo"),
        (pf, "compute_portfolio", opf, "compute_portfolio"),
    ]


def rebind_registry():
    """
    The registry captured every formula function by VALUE at import time, so swapping a module
    attribute is not enough on its own. This rebuilds the registry's table from the modules'
    CURRENT attributes, which is what makes the swap reach the real computation path rather than
    changing a name nothing reads. Failing to do this would have produced a drive that compared
    a project with itself and reported everything identical, which is the exact false-clean this
    project keeps finding.
    """
    from app.simulation.models import VALIDATED
    import app.simulation.models_decision as d
    import app.simulation.models_doc as doc
    import app.simulation.models_ext as ext
    import app.simulation.models_gov as gov
    import app.simulation.models_sim as sim
    live = {}
    for mod in (d, doc, ext, gov, sim):
        for name in dir(mod):
            if name.startswith("run_"):
                live[name] = getattr(mod, name)
    for mid, (cls, fn) in list(VALIDATED.items()):
        nm = getattr(fn, "__name__", "")
        if nm in live:
            VALIDATED[mid] = (cls, live[nm])
        elif nm in ("run_monte_carlo_module",):
            pass  # wrapper: it looks up models_sim.run_monte_carlo at call time already
    return VALIDATED


def seed(prj: str, name: str, pm_token: str | None = None) -> str:
    from sqlalchemy import select
    import app.main as main
    from app.models import Project
    from app.research_identity import hash_access_token
    from app.research_models import Participant
    with main.SessionFactory() as s:
        row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
        if row is None:
            s.add(Participant(pseudonymous_code="R2-BROWSER-ADMIN", role="ResearchAdmin",
                              access_token_hash=hash_access_token(ADMIN)))
        else:
            row.access_token_hash = hash_access_token(ADMIN)
        if s.scalar(select(Project).where(Project.legacy_id == prj)) is None:
            s.add(Project(legacy_id=prj,
                          doc={"id": prj, "name": name, "signals": {}, "events": []}))
        s.commit()
    admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
    if pm_token is None:
        created = post({"action": "adminparticipantcreate", "session_token": admin,
                        "pseudonymous_code": "R2-BROWSER-PM", "role": "Participant",
                        "account_type": "operational"})
        pm_token = post({"action": "researchlogin",
                         "access_token": created["access_token"]})["session_token"]
        globals()["_PM_ID"] = created["participant_id"]
    post({"action": "adminmemberadd", "session_token": admin, "id": prj,
          "participant_id": globals()["_PM_ID"], "project_role": "PM"})
    for p in (1, 2, 3, 4):
        docs = [{"filename": f"M{p}.pdf", "mimeType": "application/pdf",
                 "dataBase64": base64.b64encode(doc_bytes(prj, f"M{p}")).decode()}]
        docs += [{"filename": f"{t}{p}.pdf", "mimeType": "application/pdf",
                  "dataBase64": base64.b64encode(doc_bytes(prj, f"{t}{p}")).decode()}
                 for t in EXTRAS]
        post({"action": "projectupload", "session_token": pm_token, "id": prj,
              "period": p, "period_end": MONTHS[p][0], "documents": docs})
    post({"action": "projectcomputeall", "session_token": pm_token, "id": prj})
    return pm_token


def ledger_text(page) -> str:
    """The Signal Ledger's own body, not the whole page: `#body-d-ledger` is what
    collapsibleSection('d-ledger', 'Signal Inputs', ...) builds."""
    return page.evaluate("""() => {
        const el = document.querySelector('#body-d-ledger');
        return el ? (el.innerText || '') : '';
    }""")


def main_drive() -> None:
    import uvicorn
    from playwright.sync_api import sync_playwright

    import app.main as main
    from app.documents import set_extractor_override
    from app.extraction_client import StubExtractor

    legacy = load_legacy()
    all_records = {}
    all_records.update(records_for(FIXED_PRJ))
    all_records.update(records_for(LEGACY_PRJ))
    set_extractor_override(StubExtractor(all_records))

    config = uvicorn.Config(main.app, host="127.0.0.1", port=PORT, log_level="critical")
    server = uvicorn.Server(config)
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(120):
        try:
            urllib.request.urlopen(BASE + "/readyz", timeout=2).read()
            break
        except Exception:
            time.sleep(0.5)

    print("=" * 78)
    print("A. Two projects, identical documents, one computed on each version of the modules")
    print("=" * 78)

    pm = seed(FIXED_PRJ, "Richmond VA construction", None)
    print("  seeded and computed on this branch")

    table = swap_table(*legacy)
    saved = [(owner, attr, getattr(owner, attr)) for owner, attr, _, _ in table]
    for owner, attr, src, name in table:
        setattr(owner, attr, getattr(src, name))
    rebind_registry()
    try:
        seed(LEGACY_PRJ, "Richmond VA construction as before", pm)
    finally:
        for owner, attr, fn in saved:
            setattr(owner, attr, fn)
        rebind_registry()
    print("  seeded and computed with the pinned baseline commit's own module functions, then restored")

    # THE SWAP MUST BE PROVED TO HAVE TAKEN. If the two stored rows are identical, the rest of
    # this drive would compare a project with itself and report a clean pass.
    fixed_row = post({"action": "projectresults", "session_token": pm,
                      "id": FIXED_PRJ, "period": 4})["result"]
    legacy_row = post({"action": "projectresults", "session_token": pm,
                       "id": LEGACY_PRJ, "period": 4})["result"]
    fixed_mods = {m["module_id"]: m for m in (fixed_row.get("module_results") or [])}
    legacy_mods = {m["module_id"]: m for m in (legacy_row.get("module_results") or [])}
    check(fixed_mods.get("A4.9", {}).get("risk_ratio") == 0.65
          and legacy_mods.get("A4.9", {}).get("risk_ratio") == 1.8,
          "the swap took: the same procurement document stores 0.65 on this branch and 1.8 as "
          "before", f"{fixed_mods.get('A4.9', {}).get('risk_ratio')} vs "
                    f"{legacy_mods.get('A4.9', {}).get('risk_ratio')}")
    check("A6.3" in legacy_mods and "A6.3" not in fixed_mods,
          "and the synthetic environmental score is stored as before and absent on this branch")
    check(fixed_mods.get("A6.4", {}).get("status_color") == "Red"
          and legacy_mods.get("A6.4", {}).get("status_color") == "Green",
          "and the contractor evaluation is Red on this branch and Green as before",
          f"{fixed_mods.get('A6.4', {}).get('status_color')} vs "
          f"{legacy_mods.get('A6.4', {}).get('status_color')}")

    print()
    print("=" * 78)
    print("B. The Signal Ledger in a real browser, both themes")
    print("=" * 78)

    seen: dict[str, dict[str, str]] = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=SHELL,
            args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist",
                  "--no-sandbox"])
        for theme in ("plain", "newyork"):
            page = browser.new_page(viewport={"width": 1680, "height": 1400})
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            for pattern in ("**accounts.google.com**", "**apis.google.com**",
                            "**gstatic.com**", "**tiles.openfreemap.org**",
                            "**maps.googleapis.com**"):
                page.route(pattern, lambda r: r.abort())
            page.goto(BASE + "/", wait_until="domcontentloaded")
            page.evaluate(
                "([tok, th]) => { sessionStorage.setItem('og-session-token', tok);"
                " localStorage.setItem('lin-theme', th); }", [pm, theme])
            page.goto(BASE + "/", wait_until="domcontentloaded")
            page.add_style_tag(content="*,*::before,*::after{transition:none!important;"
                                       "animation:none!important}")
            page.wait_for_timeout(7000)

            applied = page.evaluate("document.body.dataset.theme")
            if applied != theme:
                # The account's stored theme wins over localStorage on boot, so switch through
                # the application's own theme flyout rather than forcing the attribute.
                LABELS = {"plain": "Fairbanks", "light": "Miami", "newyork": "NYC",
                          "maria": "Maria"}
                page.click(".dock-menu")
                page.wait_for_timeout(600)
                page.click(f".dock-flyout .flyout-pill:has-text('{LABELS[theme]}')")
                page.wait_for_timeout(1800)
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
                applied = page.evaluate("document.body.dataset.theme")
            check(applied == theme, f"[{theme}] the application is in this theme", str(applied))
            bg = page.evaluate("getComputedStyle(document.body).backgroundColor")
            seen.setdefault("_bg", {})[theme] = bg
            print(f"    [{theme}] body background {bg}")

            for prj, label in ((FIXED_PRJ, "this branch"), (LEGACY_PRJ, "as before")):
                page.evaluate("id => window.LinApp.openDetail(id)", prj)
                page.wait_for_timeout(6000)
                # The Signal Ledger is inside a collapsible section that starts closed. Open
                # every section through the application's own toggle rather than by setting
                # display, so what is read back is what the application actually drew.
                page.evaluate("""() => {
                    document.querySelectorAll('.collapse-section').forEach(sec => {
                        if (!sec.classList.contains('open')) {
                            const h = sec.querySelector('.collapse-header');
                            if (h) h.click();
                        }
                    });
                    // Each category is a native <details>; the module rows are inside it.
                    document.querySelectorAll('details.cat-row').forEach(d => { d.open = true; });
                }""")
                page.wait_for_timeout(4000)
                txt = ledger_text(page)
                seen.setdefault(theme, {})[prj] = txt
                check(len(txt) > 500,
                      f"[{theme}] the Signal Ledger rendered for the project computed on "
                      f"{label}", str(len(txt)))
                check(not errors, f"[{theme}] no uncaught page error on {label}",
                      str(errors[:2]))
                check("—" not in txt,
                      f"[{theme}] no em dash on the ledger for {label}")

            fixed_txt = seen[theme][FIXED_PRJ]
            legacy_txt = seen[theme][LEGACY_PRJ]
            check(fixed_txt != legacy_txt,
                  f"[{theme}] THE PAGE ITSELF DIFFERS between the two, so this run changed "
                  "something a person can see")
            # Asserted on the ROW'S OWN SENTENCE rather than on the bare number: "1.8" also
            # occurs elsewhere on this page, and a substring check against it would have been
            # satisfied by a different module's figure.
            FIXED_ROW = "weighted disruption 0.65"
            OLD_ROW = "weighted disruption 1.8"
            check(FIXED_ROW in fixed_txt and OLD_ROW not in fixed_txt
                  and OLD_ROW in legacy_txt and FIXED_ROW not in legacy_txt,
                  f"[{theme}] the procurement row reads a weighted disruption of 0.65 on this "
                  "branch and 1.8 as before",
                  f"fixed: {FIXED_ROW in fixed_txt}/{OLD_ROW in fixed_txt}; "
                  f"before: {OLD_ROW in legacy_txt}/{FIXED_ROW in legacy_txt}")
            check("quality 2" in fixed_txt and "quality 2" not in legacy_txt,
                  f"[{theme}] the contractor row names the quality rating on this branch and "
                  "did not before")
            check("12 open of 2 NCRs issued" in legacy_txt
                  and "12 open of 2 NCRs issued" not in fixed_txt,
                  f"[{theme}] the nonconformance row reported a backlog of twelve against an "
                  "intake of two as a ratio of six, and no longer does")
            check("3 weather days lost" in legacy_txt
                  and "3 weather days lost" not in fixed_txt,
                  f"[{theme}] the weather row asserted a worst case with no float figure, and "
                  "no longer does")
            check("Environmental compliance: 90" in legacy_txt
                  and "Environmental compliance: 90" not in fixed_txt,
                  f"[{theme}] the synthetic environmental score of 90 per cent is on the page "
                  "as before and is gone on this branch",
                  f"before: {'Environmental compliance: 90' in legacy_txt}")
            for word in ("proxy:", "Advisory, non-voting", "newly wired", "unqualified",
                         "remediation"):
                check(word.lower() not in fixed_txt.lower(),
                      f"[{theme}] no qualifier text reached the ledger: '{word}'")
            page.close()
        browser.close()

    check(seen["_bg"]["plain"] != seen["_bg"]["newyork"],
          "the two themes really do render differently, read off computed style",
          str(seen["_bg"]))
    server.should_exit = True


if __name__ == "__main__":
    try:
        main_drive()
    finally:
        print()
        print("=" * 78)
        print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
        print("=" * 78)
    sys.exit(1 if FAILED else 0)
