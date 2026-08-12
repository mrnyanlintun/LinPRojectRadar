#!/usr/bin/env python3
"""
RUN 16. THE SERVED PROJECT DETAIL PAGE, DRIVEN IN A REAL BROWSER.

WHY THIS EXISTS. tests_render.html never loads index.html, and Runs 11, 12 and 15 each found a
participant-visible defect that only the served page revealed. Workstreams A and B of Run 16 are
entirely about what the served Project Detail page says, so the evidence has to come from the
served page.

WHAT IT DRIVES, in the four states the owner named:

  STATE A  a brand-new project: no documents, no signals, no computation
  STATE B  a populated project: four periods of recognised evidence, computed
  STATE C  the populated project after clear-all, read same-session AND after a reload
  STATE D  a switch between populated, empty and populated again
  ONEDOC   a project holding exactly one recognised document, computed

For every state it reads, from the SERVED DOM: the Signal Flow column headers, the module dot
colours, the document node colours, the project status node, the animated-flow path count, the
presence of the Signal navigation rail, and the presence of any collapse/hide control. It reads
the SERVER's own answer for the same project through the participant's own session, so the two
can be compared rather than assumed.

It prints a canonical RESULT line so it can be read the same way a suite is, but it lives
outside the test_*.py glob deliberately: it needs Chromium, and run_all_suites.sh must not
depend on a browser being installed.

CONTAINER FACTS (carried forward, do not rediscover): Chromium is the headless SHELL at an
explicit path; the parser-blocking Google sign-in script and the map tile host must be aborted;
CSS transitions must be suppressed before reading computed styles; window.confirm returns false
here, so no step may be confirm-gated (the clear-all button deliberately is not).

Run:
    DATABASE_URL=sqlite:///... SESSION_SECRET=... PYTHONIOENCODING=utf-8 \
        python tools/drive_run16_final_flow.py
"""
from __future__ import annotations

import base64
import hashlib
import os
import json
import pathlib
import sys
import threading
import time
import urllib.request

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

ROOT = pathlib.Path(__file__).resolve().parents[2]
SHELL = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"
PORT = 8161
BASE = f"http://127.0.0.1:{PORT}"
ADMIN = "r16-browser-admin"
EMPTY = "PRJ-R16-EMPTY"
FULL = "PRJ-R16-FULL"
ONEDOC = "PRJ-R16-ONEDOC"

LABEL = os.environ.get("RUN16_LABEL", "browser_facts")
PASSED = 0
FAILED = 0
FACTS: list[list[str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def fact(state: str, name: str, value: str) -> None:
    FACTS.append([state, name, str(value)])
    print(f"        . {state} / {name} = {value}")


MONTHS = {
    1: ("2026-03-31", 3_000_000, 3_050_000, 3_050_000, 25.0, 25.0),
    2: ("2026-04-30", 4_000_000, 4_250_000, 4_150_000, 33.0, 34.0),
    3: ("2026-05-31", 5_000_000, 5_500_000, 5_300_000, 42.0, 44.0),
    4: ("2026-06-30", 6_000_000, 6_900_000, 6_500_000, 50.0, 54.0),
}
TAGS = ("LOOK", "PAY", "COST", "RFI", "SUB")


def doc_bytes(project: str, tag: str) -> bytes:
    return f"%PDF-1.4 RUN16 {project} {tag}\n".encode()


def _monthly(m, d):
    return {"earned_value": m[1], "actual_cost": m[2], "planned_value": m[3],
            "budget_at_completion": 12_000_000, "actual_percent_complete": m[4],
            "planned_percent_complete": m[5], "report_date": d, "document_date": d,
            "document_risk_score": 0.45}


def records() -> dict:
    rec = {}
    for p, m in MONTHS.items():
        d = m[0]
        rec[hashlib.sha256(doc_bytes(FULL, f"M{p}")).hexdigest()] = ("monthly_report", _monthly(m, d))
        rec[hashlib.sha256(doc_bytes(FULL, f"LOOK{p}")).hexdigest()] = ("lookahead_schedule", {
            "activities_planned": 60, "activities_constrained": 4 + 3 * p,
            "lookahead_weeks": 3, "report_date": d})
        rec[hashlib.sha256(doc_bytes(FULL, f"PAY{p}")).hexdigest()] = ("pay_application", {
            "amount_paid_to_date": m[2], "percent_complete_verified": m[4],
            "completed_to_date": m[1], "original_contingency": 600_000,
            "remaining_contingency": 600_000 - 90_000 * p, "application_date": d})
        rec[hashlib.sha256(doc_bytes(FULL, f"COST{p}")).hexdigest()] = ("cost_report", {
            "material_cost_baseline": 4_000_000,
            "material_cost_current": 4_000_000 + 90_000 * p,
            "indirect_cost_plan": 900_000, "indirect_cost_actual": 880_000, "report_date": d})
        rec[hashlib.sha256(doc_bytes(FULL, f"RFI{p}")).hexdigest()] = ("rfi_log", {
            "rfi_total": 20 + 7 * p, "rfi_open": 4 + 3 * p, "rfi_overdue": p,
            "avg_response_days": 8.0 + p, "rfi_period_days": 30,
            "oldest_open_days": 20 + 9 * p, "log_date": d})
        rec[hashlib.sha256(doc_bytes(FULL, f"SUB{p}")).hexdigest()] = ("submittal_register", {
            "submittals_total": 40 + 16 * p, "submittals_rejected": 3 + 3 * p,
            "document_date": d})
    # The one-document control: exactly one recognised monthly report, period 1.
    rec[hashlib.sha256(doc_bytes(ONEDOC, "M1")).hexdigest()] = (
        "monthly_report", _monthly(MONTHS[1], MONTHS[1][0]))
    return rec


def post(payload: dict) -> dict:
    req = urllib.request.Request(BASE + "/exec", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "text/plain"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode())


def seed() -> str:
    from sqlalchemy import select
    import app.main as main
    from app.models import Project
    from app.research_identity import hash_access_token
    from app.research_models import Participant
    with main.SessionFactory() as s:
        row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
        if row is None:
            s.add(Participant(pseudonymous_code="R16-BROWSER-ADMIN", role="ResearchAdmin",
                              access_token_hash=hash_access_token(ADMIN)))
        else:
            row.access_token_hash = hash_access_token(ADMIN)
        for pid, name in ((EMPTY, "Run 16 empty project"),
                          (FULL, "Run 16 populated project"),
                          (ONEDOC, "Run 16 one-document project")):
            if s.scalar(select(Project).where(Project.legacy_id == pid)) is None:
                s.add(Project(legacy_id=pid,
                              doc={"id": pid, "name": name, "signals": {}, "events": []}))
        s.commit()
    admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
    created = post({"action": "adminparticipantcreate", "session_token": admin,
                    "pseudonymous_code": "R16-BROWSER-PM", "role": "Participant",
                    "account_type": "operational"})
    pm = post({"action": "researchlogin",
               "access_token": created["access_token"]})["session_token"]
    for pid in (EMPTY, FULL, ONEDOC):
        post({"action": "adminmemberadd", "session_token": admin, "id": pid,
              "participant_id": created["participant_id"], "project_role": "PM"})
    for p in (1, 2, 3, 4):
        docs = [{"filename": f"M{p}.pdf", "mimeType": "application/pdf",
                 "dataBase64": base64.b64encode(doc_bytes(FULL, f"M{p}")).decode()}]
        docs += [{"filename": f"{t}{p}.pdf", "mimeType": "application/pdf",
                  "dataBase64": base64.b64encode(doc_bytes(FULL, f"{t}{p}")).decode()}
                 for t in TAGS]
        post({"action": "projectupload", "session_token": pm, "id": FULL,
              "period": p, "period_end": MONTHS[p][0], "documents": docs})
    post({"action": "projectcomputeall", "session_token": pm, "id": FULL})
    post({"action": "projectupload", "session_token": pm, "id": ONEDOC, "period": 1,
          "period_end": MONTHS[1][0],
          "documents": [{"filename": "M1.pdf", "mimeType": "application/pdf",
                         "dataBase64": base64.b64encode(doc_bytes(ONEDOC, "M1")).decode()}]})
    post({"action": "projectcomputeall", "session_token": pm, "id": ONEDOC})
    # The empty project is left exactly as created: no upload, no compute, no synthetic data.
    return pm


# ---------------------------------------------------------------- DOM readers

READ_FLOW = r"""
() => {
  const c = document.querySelector('.detail-neural-flow');
  if (!c) return { present: false };
  const svg = c.querySelector('svg');
  if (!svg) return { present: false };
  const headers = Array.from(svg.querySelectorAll('text'))
    .filter(t => parseFloat(t.getAttribute('y')) < 34 && t.getAttribute('font-weight') === '700')
    .map(t => t.textContent.trim());
  const nodes = svg.querySelector('#lnf-nodes');
  const counts = {};
  let coloured = 0;
  nodes.querySelectorAll('circle,rect,polygon').forEach(el => {
    const f = (el.getAttribute('fill') || '').toLowerCase();
    if (!f || f === 'none') return;
    counts[f] = (counts[f] || 0) + 1;
  });
  const prj = svg.querySelector('#lnf-prj');
  const prjTexts = prj ? Array.from(prj.querySelectorAll('text')).map(t => t.textContent.trim()) : [];
  const animated = svg.querySelectorAll(
    '.lnf-flow-a,.lnf-flow-b,.lnf-flow-c,.lnf-flow-fb').length;
  const activeCls = svg.querySelectorAll('.lnf-active').length;
  const summary = c.querySelector('.lnf-summary');
  return {
    present: true, headers, counts, prjTexts, animated, activeCls,
    summary: summary ? summary.innerText.replace(/\s+/g, ' ').trim() : null,
    paths: svg.querySelectorAll('path').length
  };
}
"""

READ_RAIL = r"""
() => {
  const nav = document.getElementById('detail-secnav');
  const visible = !!nav && !nav.hasAttribute('hidden') &&
    getComputedStyle(nav).display !== 'none';
  const btns = nav ? Array.from(nav.querySelectorAll('.detail-secnav-btn')) : [];
  // Any control whose job is to collapse/hide, anywhere on the page, by any of the
  // shapes this repository could have used for one.
  const arrows = /[◀▶◂▸‹›❮❯«»]/;
  const suspects = Array.from(document.querySelectorAll('button,[role="button"],a'))
    .filter(el => {
      const t = (el.textContent || '').trim();
      const a = ((el.getAttribute('aria-label') || '') + ' ' +
                 (el.getAttribute('title') || '')).toLowerCase();
      const cls = (el.className && el.className.baseVal !== undefined
                   ? el.className.baseVal : String(el.className || '')).toLowerCase();
      const hit = arrows.test(t) || /\bcollapse\b|\bhide (the )?(rail|nav|navigator)\b/.test(a) ||
                  /secnav-(toggle|collapse|hide)/.test(cls);
      if (!hit) return false;
      const r = el.getBoundingClientRect();
      return r.width > 0 && r.height > 0;
    })
    .map(el => ({ text: (el.textContent || '').trim().slice(0, 24),
                  cls: String(el.className.baseVal !== undefined ? el.className.baseVal : el.className),
                  x: Math.round(el.getBoundingClientRect().x),
                  y: Math.round(el.getBoundingClientRect().y) }));
  return { present: !!nav, visible, buttons: btns.length,
           labels: btns.map(b => b.textContent.trim()), suspects };
}
"""


def open_detail(page, pid: str) -> None:
    if page is None:
        return
    page.evaluate("id => LinApp.openDetail(id)", pid)
    page.wait_for_timeout(2500)
    # Open the Signal Flow section (heavy visuals render on FIRST expand).
    page.evaluate("""() => {
      const h = document.querySelector('#section-d-neural .collapse-header');
      const body = document.getElementById('body-d-neural');
      if (h && body && body.style.display === 'none') h.click();
    }""")
    page.wait_for_timeout(2500)


def server_state(pm: str, pid: str, period: int = 1) -> dict:
    r = post({"action": "projectresults", "session_token": pm, "id": pid, "period": period})
    if not r.get("ok", True) or "result" not in r:
        return {"live_row": False, "error": r.get("error")}
    row = r["result"]
    return {
        "live_row": True,
        "modules": len(row.get("module_results") or []),
        "abstained": len(row.get("abstained") or []),
        "categories": len(row.get("category_statuses") or {}),
        "project_status": row.get("project_status"),
        "status_label": row.get("project_status_label"),
    }


def write_facts() -> None:
    import csv
    out = ROOT / "code_audit" / f"run16_final_flow_{LABEL}.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["state", "observation", "value"])
        w.writerows(FACTS)
    print(f"\nwrote {out}")


def main_drive() -> None:
    import uvicorn
    from playwright.sync_api import sync_playwright

    import app.main as main
    from app.documents import set_extractor_override
    from app.extraction_client import StubExtractor

    set_extractor_override(StubExtractor(records()))
    config = uvicorn.Config(main.app, host="127.0.0.1", port=PORT, log_level="critical")
    server = uvicorn.Server(config)
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(120):
        try:
            urllib.request.urlopen(BASE + "/readyz", timeout=2).read()
            break
        except Exception:
            time.sleep(0.5)

    pm = seed()

    print("=" * 78)
    print("SERVER STATE, read through the participant's own session, before the browser")
    print("=" * 78)
    for pid in (EMPTY, FULL, ONEDOC):
        st = server_state(pm, pid, 1)
        fact("server:" + pid, "live_row", str(st.get("live_row")))
        for k in ("modules", "abstained", "categories", "project_status"):
            if k in st:
                fact("server:" + pid, k, str(st[k]))

    with sync_playwright() as pw:
        errors: list[str] = []

        def browser_for_page():
            b = pw.chromium.launch(
                executable_path=SHELL,
                args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist",
                      "--no-sandbox"])
            p = b.new_page(viewport={"width": 1680, "height": 1400})
            p.set_default_timeout(45000)
            p.set_default_navigation_timeout(45000)
            p.on("pageerror", lambda e: errors.append(str(e)))
            for pattern in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                            "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
                p.route(pattern, lambda r: r.abort())
            p.goto(BASE + "/", wait_until="domcontentloaded")
            p.evaluate("tok => sessionStorage.setItem('og-session-token', tok)", pm)
            p.goto(BASE + "/", wait_until="domcontentloaded")
            p.add_style_tag(content="*,*::before,*::after{transition:none!important;"
                                    "animation:none!important}")
            p.wait_for_timeout(8000)
            return (b, p)

        browsers: list = []

        def reload_state(state: str, pid: str) -> None:
            """
            WHAT A RELOAD CAN SHOW, AND WHERE IT IS ACTUALLY DECIDED.

            CONTAINER FACT, recorded so no session spends another hour on it: there is no way to
            reload the served page inside this container that returns in reasonable time.
            page.reload(), a repeat goto(), a scheduled location.reload(), a second page in the
            same browser and a second browser in the same Playwright context all stall for
            minutes, because the served page holds requests open (the parser-blocking sign-in
            script is aborted and the map tile host is refused at CONNECT) and every Playwright
            navigation primitive waits on them.

            That is a harness limitation and it is reported as one rather than skipped. What a
            reload could tell us is decided upstream anyway: a reloaded page reads the server,
            and the server's answer for this project is recorded here directly, through the
            participant's own session. The Run 16 defect was a SERVER fact, the cleared project
            going on serving a live derived row, so this is the layer the evidence belongs at.
            The pre-fix run in code_audit/run16_final_flow_before.csv did capture the reloaded
            DOM, and it is the record of what the defect looked like.
            """
            st = server_state(pm, pid, 1)
            fact(state, "browser_reload_captured",
                 "no: no reload primitive returns in this container")
            for k in ("live_row", "modules", "categories", "project_status"):
                if k in st:
                    fact(state, "server_" + k, str(st[k]))

        browsers.append(browser_for_page())
        page = browsers[-1][1]

        def report(state: str) -> dict:
            if page is None:
                fact(state, "not_captured", "the reload did not complete in this container")
                return {"flow": {}, "rail": {"visible": None, "suspects": None}}
            flow = page.evaluate(READ_FLOW)
            rail = page.evaluate(READ_RAIL)
            fact(state, "flow_present", str(flow.get("present")))
            if flow.get("present"):
                fact(state, "headers", " | ".join(flow["headers"]))
                fact(state, "node_fill_counts", json.dumps(flow["counts"], sort_keys=True))
                fact(state, "project_status_node", " ".join(flow["prjTexts"]))
                fact(state, "animated_paths", str(flow["animated"]))
                fact(state, "active_marked_paths", str(flow["activeCls"]))
                fact(state, "summary_strip", str(flow["summary"]))
            fact(state, "rail_visible", str(rail["visible"]))
            fact(state, "rail_buttons", str(rail["buttons"]))
            fact(state, "collapse_suspects", json.dumps(rail["suspects"]))
            page.screenshot(path=str(ROOT / "code_audit" /
                                     f"run16_shot_{LABEL}_{state}.png"), full_page=False)
            return {"flow": flow, "rail": rail}

        print()
        print("=" * 78)
        print("STATE A — brand-new empty project (no documents, no signals, no computation)")
        print("=" * 78)
        open_detail(page, EMPTY)
        a = report("A-empty")
        check(a["rail"]["visible"], "STATE A: the Signal navigation rail is visible")
        check(a["rail"]["suspects"] == [],
              "STATE A: no collapse/hide control is present", json.dumps(a["rail"]["suspects"]))
        reload_state("A-empty-reload", EMPTY)

        print()
        print("=" * 78)
        print("STATE B — populated project")
        print("=" * 78)
        open_detail(page, FULL)
        report("B-populated")

        print()
        print("=" * 78)
        print("ONE-DOCUMENT CONTROL — exactly one recognised document")
        print("=" * 78)
        open_detail(page, ONEDOC)
        report("onedoc")

        print()
        print("=" * 78)
        print("STATE D — project switch: populated, empty, populated")
        print("=" * 78)
        open_detail(page, FULL)
        d1 = report("D-switch-1-populated")
        open_detail(page, EMPTY)
        d2 = report("D-switch-2-empty")
        open_detail(page, FULL)
        d3 = report("D-switch-3-populated")
        check(json.dumps(d1["flow"].get("counts")) == json.dumps(d3["flow"].get("counts")),
              "STATE D: the populated project reads the same before and after the switch")
        check(json.dumps(d2["flow"].get("counts")) != json.dumps(d1["flow"].get("counts")),
              "STATE D: the empty project does not read as the populated one")

        print()
        print("=" * 78)
        print("STATE C — clear-all on the populated project, same session then reloaded")
        print("=" * 78)
        open_detail(page, FULL)
        page.evaluate("""() => {
          const b = document.querySelector('.detail-reset');
          if (b) b.click();
        }""")
        page.wait_for_timeout(6000)
        page.evaluate("""() => {
          const h = document.querySelector('#section-d-neural .collapse-header');
          const body = document.getElementById('body-d-neural');
          if (h && body && body.style.display === 'none') h.click();
        }""")
        page.wait_for_timeout(2500)
        c = report("C-cleared-same-session")
        # GATE 4, STATE C. The active paths must disappear in the SAME session, not only after a
        # reload, and the header must stop claiming results the server no longer holds.
        check(c["flow"].get("animated") == 0,
              "STATE C: no path is animated once the evidence is cleared",
              str(c["flow"].get("animated")))
        check("0 WITH A CURRENT RESULT" in " | ".join(c["flow"].get("headers") or []),
              "STATE C: the header reports no module with a current result",
              " | ".join(c["flow"].get("headers") or []))
        check("NOT ESTIMABLE" in " | ".join(c["flow"].get("headers") or []),
              "STATE C: and the governed rollup is not estimable",
              " | ".join(c["flow"].get("headers") or []))
        check(c["rail"]["visible"] and c["rail"]["suspects"] == [],
              "STATE C: the Signal rail is present and no collapse control appeared")
        st = server_state(pm, FULL, 1)
        fact("C-cleared-server", "live_row", str(st.get("live_row")))
        for k in ("modules", "categories", "project_status"):
            if k in st:
                fact("C-cleared-server", k, str(st[k]))
        reload_state("C-cleared-reloaded", FULL)

        fact("browser", "page_errors", json.dumps(errors[:5]))
        fact("browser", "browsers_launched", str(len(browsers)))

    write_facts()
    print(f"\nRESULT: {PASSED}/{PASSED + FAILED} checks passed")


if __name__ == "__main__":
    try:
        main_drive()
    except Exception:
        # The evidence gathered before the failure is still evidence, and losing it to a
        # container flake in the last state has cost this programme time before.
        write_facts()
        raise
