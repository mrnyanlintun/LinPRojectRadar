#!/usr/bin/env python3
"""
Browser drive for the freeze point: the Signal Ledger and the Governance Decision card, a real
Chromium, a real server, both themes.

WHAT IT PROVES THAT THE SUITE CANNOT. The suite proves the bands and the guards on the real
computation path and reads them back through the API. It cannot say what a project manager
looking at the page sees. Two of the seven were re-banded and all seven gained guards, and every
one of those changes lands on a row somebody reads.

THE DRIVE IS PROVED ABLE TO FAIL END TO END. Three projects are seeded on the SAME server:
  - one computed on this branch;
  - one computed with the pinned baseline commit's own seven formula functions swapped into the
    live registry, which is the shipped behaviour rather than an approximation of it;
  - one whose actual cost has reached its budget, which is the case the run names: the ratio
    whose denominator is zero. On this branch that row abstains; as before it manufactured a Red.
The registry captures formula functions BY VALUE at import, so the swap rebinds the registry
table as well. Without that the drive would compare a project with itself and report clean.

Container facts this script encodes so no session loses time on them again:
  - Chromium is at /opt/pw-browsers and the installed Playwright expects a different build, so
    the executable path is passed explicitly, and it is the headless SHELL because the full
    binary has had old headless mode removed.
  - The parser-blocking Google sign-in script is blackholed by the proxy; it and the map tile
    host, which is refused at CONNECT, are aborted here.
  - CSS transitions are suppressed before any computed style is read.

Run:
    DATABASE_URL=sqlite:///... SESSION_SECRET=... PYTHONIOENCODING=utf-8 \
        python tools/drive_run4_validate_seven.py
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

#: PINNED BY SHA, NOT BY BRANCH NAME: once this run merges, origin/main becomes this code and
#: every "as before" half would be comparing the fix with itself.
BASELINE_REV = "640c355"
PORT = 8127
BASE = f"http://127.0.0.1:{PORT}"
ADMIN = "r4-browser-admin"
NOW_PRJ = "PRJ-R4-NOW"
BEFORE_PRJ = "PRJ-R4-ASBEFORE"
DONE_PRJ = "PRJ-R4-ATCOMPLETION"

SEVEN = ("A1.7", "A1.8", "A2.8", "A3.2", "A3.4", "A4.2", "A4.3")

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
#: The project at completion: actual cost has reached the budget at completion exactly, which is
#: the zero denominator the run names.
#: Every period, not only the last: the detail page renders one period's snapshot and which one
#: it lands on is not this drive's business to assume. With the budget reached in all four, any
#: period the page chooses shows the case the run names.
DONE_MONTHS = {
    1: ("2026-03-31", 3_000_000, 12_000_000, 3_000_000, 25.0, 25.0),
    2: ("2026-04-30", 6_000_000, 12_000_000, 6_000_000, 50.0, 50.0),
    3: ("2026-05-31", 9_000_000, 12_000_000, 9_000_000, 75.0, 75.0),
    4: ("2026-06-30", 11_500_000, 12_000_000, 11_500_000, 96.0, 96.0),
}
TAGS = ("LOOK", "PAY", "COST", "RFI", "SUB")


def doc_bytes(prj: str, tag: str) -> bytes:
    return f"%PDF-1.4 RUN4 BROWSER {prj} {tag}\n".encode()


def records_for(prj: str, months: dict) -> dict:
    rec = {}
    for p, m in months.items():
        rec[hashlib.sha256(doc_bytes(prj, f"M{p}")).hexdigest()] = ("monthly_report", {
            "earned_value": m[1], "actual_cost": m[2], "planned_value": m[3],
            "budget_at_completion": 12_000_000, "actual_percent_complete": m[4],
            "planned_percent_complete": m[5], "report_date": m[0], "document_date": m[0],
            "document_risk_score": 0.45})
        d = m[0]
        rec[hashlib.sha256(doc_bytes(prj, f"LOOK{p}")).hexdigest()] = ("lookahead_schedule", {
            "activities_planned": 60, "activities_constrained": 4 + 3 * p,
            "lookahead_weeks": 3, "report_date": d})
        rec[hashlib.sha256(doc_bytes(prj, f"PAY{p}")).hexdigest()] = ("pay_application", {
            "amount_paid_to_date": m[2], "percent_complete_verified": m[4],
            "completed_to_date": m[1], "original_contingency": 600_000,
            "remaining_contingency": 600_000 - 90_000 * p, "application_date": d})
        rec[hashlib.sha256(doc_bytes(prj, f"COST{p}")).hexdigest()] = ("cost_report", {
            "material_cost_baseline": 4_000_000,
            "material_cost_current": 4_000_000 + 90_000 * p,
            "indirect_cost_plan": 900_000, "indirect_cost_actual": 880_000, "report_date": d})
        rec[hashlib.sha256(doc_bytes(prj, f"RFI{p}")).hexdigest()] = ("rfi_log", {
            "rfi_total": 20 + 7 * p, "rfi_open": 4 + 3 * p, "rfi_overdue": p,
            "avg_response_days": 8.0 + p, "rfi_period_days": 30,
            "oldest_open_days": 20 + 9 * p, "log_date": d})
        rec[hashlib.sha256(doc_bytes(prj, f"SUB{p}")).hexdigest()] = ("submittal_register", {
            "submittals_total": 40 + 16 * p, "submittals_rejected": 3 + 3 * p,
            "document_date": d})
    return rec


def post(payload: dict) -> dict:
    req = urllib.request.Request(BASE + "/exec", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "text/plain"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode())


def load_baseline():
    tmp = tempfile.mkdtemp(prefix="run4-browser-baseline-")
    pkg = pathlib.Path(tmp) / "oldsim4b"
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
    import oldsim4b.models  # noqa: F401
    import oldsim4b.models_doc as odoc
    import oldsim4b.models_evm as oevm
    import oldsim4b.models_ext as oext
    return {
        "A1.7": oevm.run_tcpi, "A1.8": oevm.run_vac,
        "A2.8": oext.run_lookahead_health, "A3.2": oext.run_contingency_burn,
        "A3.4": oext.run_material_cost_variance,
        "A4.2": odoc.run_rfi_velocity, "A4.3": odoc.run_submittal_rejection,
    }


def seed(prj: str, name: str, months: dict, pm_token: str | None = None) -> str:
    from sqlalchemy import select
    import app.main as main
    from app.models import Project
    from app.research_identity import hash_access_token
    from app.research_models import Participant
    with main.SessionFactory() as s:
        row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
        if row is None:
            s.add(Participant(pseudonymous_code="R4-BROWSER-ADMIN", role="ResearchAdmin",
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
                        "pseudonymous_code": "R4-BROWSER-PM", "role": "Participant",
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
                 for t in TAGS]
        post({"action": "projectupload", "session_token": pm_token, "id": prj,
              "period": p, "period_end": months[p][0], "documents": docs})
    post({"action": "projectcomputeall", "session_token": pm_token, "id": prj})
    return pm_token


def ledger_text(page) -> str:
    return page.evaluate("""() => {
        const el = document.querySelector('#body-d-ledger');
        return el ? (el.innerText || '') : '';
    }""")


def card_text(page) -> str:
    return page.evaluate("""() => {
        const el = document.querySelector('#body-d-decision') ||
                   document.querySelector('#d-decision');
        return el ? (el.innerText || '') : '';
    }""")


def main_drive() -> None:
    import uvicorn
    from playwright.sync_api import sync_playwright

    import app.main as main
    from app.documents import set_extractor_override
    from app.extraction_client import StubExtractor
    from app.simulation.models import VALIDATED

    old_fn = load_baseline()
    records = {}
    records.update(records_for(NOW_PRJ, MONTHS))
    records.update(records_for(BEFORE_PRJ, MONTHS))
    records.update(records_for(DONE_PRJ, DONE_MONTHS))
    set_extractor_override(StubExtractor(records))

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
    print("A. Three projects on one server, computed on each version of the seven")
    print("=" * 78)

    pm = seed(NOW_PRJ, "Richmond VA construction", MONTHS, None)
    seed(DONE_PRJ, "Richmond VA construction at completion", DONE_MONTHS, pm)
    print("  seeded and computed on this branch")

    saved = {mid: VALIDATED[mid] for mid in SEVEN}
    for mid in SEVEN:
        VALIDATED[mid] = (saved[mid][0], old_fn[mid])
    try:
        seed(BEFORE_PRJ, "Richmond VA construction as before", MONTHS, pm)
    finally:
        for mid in SEVEN:
            VALIDATED[mid] = saved[mid]
    print("  seeded and computed with the pinned baseline's own seven, then restored")

    now_row = post({"action": "projectresults", "session_token": pm,
                    "id": NOW_PRJ, "period": 4})["result"]
    before_row = post({"action": "projectresults", "session_token": pm,
                       "id": BEFORE_PRJ, "period": 4})["result"]
    done_row = post({"action": "projectresults", "session_token": pm,
                     "id": DONE_PRJ, "period": 4})["result"]
    now_m = {m["module_id"]: m for m in (now_row.get("module_results") or [])}
    before_m = {m["module_id"]: m for m in (before_row.get("module_results") or [])}
    done_m = {m["module_id"]: m for m in (done_row.get("module_results") or [])}
    done_ab = {a["module_id"]: a for a in (done_row.get("abstained") or [])}

    check(now_m.get("A1.7", {}).get("status_color") != before_m.get("A1.7", {}).get("status_color"),
          "THE SWAP TOOK: the same documents band the required cost efficiency differently on "
          "this branch and as before",
          f"{now_m.get('A1.7', {}).get('status_color')} vs "
          f"{before_m.get('A1.7', {}).get('status_color')}")
    check(now_m.get("A1.7", {}).get("tcpi") == before_m.get("A1.7", {}).get("tcpi"),
          "and the NUMBER is identical either way, so the formula was not touched",
          f"{now_m.get('A1.7', {}).get('tcpi')} vs {before_m.get('A1.7', {}).get('tcpi')}")
    check("A1.7" in done_ab and "A1.7" not in done_m,
          "and at completion, where the remaining budget is zero, it abstains on this branch",
          str(done_ab.get("A1.7", {}).get("reason"))[:90])

    print()
    print("=" * 78)
    print("B. The Signal Ledger and the Governance Decision card, both themes")
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
                LABELS = {"plain": "Fairbanks", "light": "Miami", "newyork": "NYC"}
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

            for prj, label in ((NOW_PRJ, "this branch"), (BEFORE_PRJ, "as before"),
                               (DONE_PRJ, "at completion")):
                page.evaluate("id => window.LinApp.openDetail(id)", prj)
                page.wait_for_timeout(6000)
                page.evaluate("""() => {
                    document.querySelectorAll('.collapse-section').forEach(sec => {
                        if (!sec.classList.contains('open')) {
                            const h = sec.querySelector('.collapse-header');
                            if (h) h.click();
                        }
                    });
                    document.querySelectorAll('details.cat-row').forEach(d => { d.open = true; });
                }""")
                page.wait_for_timeout(4000)
                txt = ledger_text(page)
                seen.setdefault(theme, {})[prj] = txt
                seen.setdefault(theme + "-card", {})[prj] = card_text(page)
                check(len(txt) > 500,
                      f"[{theme}] the Signal Ledger rendered for the project computed on "
                      f"{label}", str(len(txt)))
                check(not errors, f"[{theme}] no uncaught page error on {label}",
                      str(errors[:2]))
                check("—" not in txt, f"[{theme}] no em dash on the ledger for {label}")

            now_txt = seen[theme][NOW_PRJ]
            before_txt = seen[theme][BEFORE_PRJ]
            done_txt = seen[theme][DONE_PRJ]
            check("Awaiting" in now_txt or "Insufficient data" in now_txt,
                  f"[{theme}] an abstaining row on an ordinary project states its own reason "
                  "under the silent row, which is what the graft in this run made visible")
            check(now_txt != before_txt,
                  f"[{theme}] THE PAGE ITSELF DIFFERS between the two, so this run changed "
                  "something a person can see")
            # The row's own sentence, not a bare number that occurs elsewhere on the page.
            check("the cost efficiency the remaining work must achieve" in now_txt
                  and "the cost efficiency the remaining work must achieve" not in before_txt,
                  f"[{theme}] the required-efficiency row states what the figure means on this "
                  "branch and did not before")
            check("to finish within budget" in before_txt,
                  f"[{theme}] and the row was on the page before too, so the comparison is "
                  "between two renderings of the same row")
            check("Budget exhausted: no remaining funds" not in done_txt,
                  f"[{theme}] the project at completion no longer reads a manufactured Red on "
                  "the required-efficiency row")
            import re as _re
            _lines = done_txt.splitlines()
            _i = [k for k, ln in enumerate(_lines) if "TCPI" in ln]
            _tcpi_line = _lines[max(0, _i[0] - 2):_i[0] + 6] if _i else []
            print(f"    [{theme}] at-completion rows mentioning the measure: {_tcpi_line[:6]}")
            _proxy_line = [ln for ln in now_txt.splitlines() if "proxy" in ln.lower()]
            print(f"    [{theme}] rows mentioning proxy: {_proxy_line[:6]}")
            check("no remaining funding" in done_txt or "Awaiting a remaining budget" in done_txt,
                  f"[{theme}] it states in words what it is waiting for instead",
                  str(_tcpi_line[:3]))
            # A NEW WAY FOR TEXT TO REACH THIS PAGE OPENED IN THIS RUN, so the scan is widened
            # to match. Abstention reasons now render under a silent row, and the disabled
            # modules carry a reason of their own that says they are concept-only and excluded
            # from fusion. That sentence must not appear here: a disabled module renders the
            # platform's not-relevant state, not an abstention, and the words are checked
            # rather than the mechanism trusted.
            for word in ("(proxy:", "Advisory, non-voting", "newly wired", "unqualified",
                         "remediation", "validated", "Christensen", "PMBOK", "citation",
                         "concept-only", "non-voting", "excluded from every fusion"):
                check(word.lower() not in now_txt.lower(),
                      f"[{theme}] nothing qualifier-like reached the ledger: '{word}'")
                check(word.lower() not in seen[theme + "-card"][NOW_PRJ].lower(),
                      f"[{theme}] nor the decision card: '{word}'")
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
