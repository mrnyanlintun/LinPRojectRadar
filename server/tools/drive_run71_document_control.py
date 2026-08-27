#!/usr/bin/env python3
"""
RUN 71. DOCUMENT CONTROL: withdraw a document from a period, recalculate, and prove all seven.

Every proof at section 8 of the Run 71 order is executed here against the real routes
(`projectupload` -> `projectcomputeall` -> `projectdocumentarchive` -> `projectcomputeall`),
and the seventh is executed in a real Chromium against the page served by this process.

THE VERIFICATION RULE (Run 61) IS FOLLOWED: loaded from the server, nothing pre-primed -- this
file never calls LinResults.prime -- and the current period is not 1.

argv[1] = label   argv[2] = path to write the captured JSON to
"""
from __future__ import annotations
import base64, hashlib, json, logging, os, pathlib, socket, sys, threading, time

LABEL = sys.argv[1] if len(sys.argv) > 1 else "run71"
OUT = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path("run71_capture.json")
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
logging.disable(logging.INFO)
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402
import app.main as main  # noqa: E402
from app.documents import set_extractor_override  # noqa: E402
from app.extraction_client import StubExtractor  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import Participant  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
FAIL: list[str] = []


def post(p):
    r = client.post("/exec", content=json.dumps(p), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"HTTP {r.status_code} {r.text[:300]}"
    return r.json()


def b64(raw):
    return base64.b64encode(raw).decode()


def check(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    if not ok:
        FAIL.append(name)
    return ok


D = "PRJ-R71"
ADMIN = "run71-admin-token"
BAC = 4_000_000
END = {1: "2026-03-31", 2: "2026-04-30"}
LAST = 2

CURVE = {0: (0, 0), 1: (1_020_000, 1_000_000), 2: (1_500_000, 1_460_000)}
EVAC = {1: (1_000_000, 1_050_000), 2: (2_000_000, 2_100_000)}
BASELINE_ROWS = [
    {"Period": p, "Period ending": (END[p] if p else "2025-12-31"),
     "Planned value this period (USD)": CURVE[p][0] - CURVE[p - 1][0] if p else 0,
     "Cumulative planned value (USD)": CURVE[p][0],
     "Cumulative planned spend (USD)": CURVE[p][1]}
    for p in range(0, LAST + 1)
]

# THE PERIOD-2 DOCUMENTS ARE DELIBERATELY SINGLE-SOURCE. Each of the four below is the ONLY
# document in this project stating its fields, so archiving one is a clean withdrawal and the
# other three are the control group for "no other document's fields are touched".
DOCS = [
    ("contract", 1, "contract_value",
     {"original_contract_sum": BAC, "project_start_date": "2026-01-01",
      "project_end_date": "2027-06-30"}),
    ("tps1", 1, "time_phased_schedule",
     {"planned_value_to_date": CURVE[1][0], "data_date": END[1], "document_date": END[1],
      "baseline_curve_json": BASELINE_ROWS}),
    ("pay1", 1, "pay_application",
     {"amount_paid_to_date": EVAC[1][1], "completed_to_date": EVAC[1][0],
      "application_date": END[1], "document_date": END[1]}),
    ("tps2", 2, "time_phased_schedule",
     {"planned_value_to_date": CURVE[2][0], "data_date": END[2], "document_date": END[2],
      "baseline_curve_json": BASELINE_ROWS}),
    ("pay2", 2, "pay_application",
     {"amount_paid_to_date": EVAC[2][1], "completed_to_date": EVAC[2][0],
      "application_date": END[2], "document_date": END[2]}),
    # ---- the four single-source period-2 documents ----
    ("safe2", 2, "safety_report",
     {"osha_recordable_incidents": 2, "total_manhours": 180_000, "incident_rate": 2.2,
      "report_period": END[2], "document_date": END[2]}),
    ("rfi2", 2, "rfi_log",
     {"rfi_total": 120, "rfi_open": 30, "rfi_answered": 90, "rfi_overdue": 8,
      "avg_response_days": 11, "rfi_period_days": 30, "oldest_open_days": 44,
      "log_date": END[2], "document_date": END[2]}),
    ("sub2", 2, "submittal_register",
     {"submittals_total": 200, "submittals_rejected": 24, "document_date": END[2]}),
    ("env2", 2, "environmental_report",
     {"permit_conditions_total": 40, "violations": 2, "compliance_rate": 0.95,
      "report_date": END[2], "document_date": END[2]}),
]
#: the document this run archives. Chosen because nothing else in the fixture states its fields.
TARGET = "safe2"


def doc_bytes(tag):
    return f"%PDF-1.4 RUN71 {tag}\n".encode()


set_extractor_override(StubExtractor({
    hashlib.sha256(doc_bytes(t)).hexdigest(): (ty, ex) for t, _p, ty, ex in DOCS}))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="R71-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == D)) is None:
        s.add(Project(legacy_id=D, doc={"id": D, "name": "Run 71 document control fixture",
                                        "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": f"R71-PM-{int(time.time())}", "role": "Participant",
                "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": D,
      "participant_id": created["participant_id"], "project_role": "PM"})

for tag, per, _ty, _ex in DOCS:
    r = post({"action": "projectupload", "session_token": PM, "id": D, "period": per,
              "period_end": END[per],
              "documents": [{"filename": f"{tag}.pdf", "mimeType": "application/pdf",
                             "dataBase64": b64(doc_bytes(tag))}]})
    assert r.get("ok") is True, str(r)[:400]

assert post({"action": "projectcomputeall", "session_token": PM, "id": D}).get("ok") is True

CAP: dict = {"label": LABEL}


def read_row(period):
    res = post({"action": "projectresults", "session_token": PM, "id": D, "period": period})
    return res.get("result") or {}


def modules(row):
    return {m.get("module_id"): m for m in (row.get("module_results") or [])}


def abstentions(row):
    return {a.get("module_id"): a.get("reason") for a in (row.get("abstained") or [])}


BEFORE = read_row(LAST)
MODS_BEFORE = modules(BEFORE)
ABS_BEFORE = abstentions(BEFORE)
SI_BEFORE = BEFORE.get("signal_inputs") or {}
CATS_BEFORE = {k: (v or {}).get("status") for k, v in (BEFORE.get("category_statuses") or {}).items()}

dc = post({"action": "projectdocumentcontrol", "session_token": PM, "id": D})
assert dc.get("ok") is True, str(dc)[:300]
PERIODS = {int(p["period"]): p for p in dc["periods"]}
target_doc = [d for d in PERIODS[LAST]["documents"] if d["filename"] == f"{TARGET}.pdf"][0]
TARGET_ID = target_doc["document_id"]
TARGET_FIELDS = target_doc["fields"]

print("=" * 96)
print(f"LABEL: {LABEL}   repository root: {ROOT}   DATABASE_URL: {os.environ.get('DATABASE_URL')}")
print(f"project {D}: periods held {sorted(PERIODS)}  current (latest) period {LAST}")
print(f"period {LAST} live documents: "
      f"{[d['filename'] for d in PERIODS[LAST]['documents']]}")
print(f"target document: {TARGET}.pdf  id={TARGET_ID}  fields={TARGET_FIELDS}")
print(f"modules holding a result BEFORE: {len(MODS_BEFORE)}")
print("=" * 96)

# ------------------------------------------------------------------ PROOF 4, FIRST HALF
# `projectcompute` on an UNCHANGED period declines. This is the Run 68 note, executed, so the
# "did not skip" half below is measured against a demonstrated skip and not against a claim.
SKIP = post({"action": "projectcompute", "session_token": PM, "id": D, "period": LAST})
check("4a. projectcompute SKIPS while the documents are unchanged",
      SKIP.get("ok") is True and SKIP.get("recomputed") is False,
      f"recomputed={SKIP.get('recomputed')} note={SKIP.get('note')!r}")

# ------------------------------------------------------------------ PROOF 1, FIRST HALF
# The module(s) that compute FROM the target document, established by what the document
# supplies and what moves when it is withdrawn. Recorded here; asserted after the recompute.
CAP["target_fields"] = TARGET_FIELDS
CAP["si_before_target_fields"] = {f: SI_BEFORE.get(f) for f in TARGET_FIELDS}
# THE FIELDS THAT ACTUALLY REACH THE LIVE FIGURES. `emit_observations` emits a field; whether
# selection carries it into `signal_inputs` is a separate question, and this fixture found one
# that does not (`oshaRecordableIncidents` is emitted and is in `field_registry.FIELD_KINDS`
# but is absent from `extraction_merge._KEY_ORDER`, so `select_signal_inputs` never writes it).
# That is a pre-existing gap this run RECORDS and does not fix: repairing it would change what
# A6.2 computes and cross a version boundary. The withdrawal proof is stated over the fields
# that were genuinely in the live figures, and the others are named rather than hidden.
LIVE_TARGET_FIELDS = [f for f in TARGET_FIELDS if SI_BEFORE.get(f) is not None]
NOT_SELECTED = [f for f in TARGET_FIELDS if f not in LIVE_TARGET_FIELDS]
CAP["target_fields_reaching_signal_inputs"] = LIVE_TARGET_FIELDS
CAP["target_fields_emitted_but_never_selected"] = NOT_SELECTED
check("1a. the target document's fields are present in the live signal inputs before archiving",
      bool(LIVE_TARGET_FIELDS)
      and all(SI_BEFORE.get(f) is not None for f in LIVE_TARGET_FIELDS),
      f"in the live figures: {[(f, SI_BEFORE.get(f)) for f in LIVE_TARGET_FIELDS]}; "
      f"emitted but never selected into signal_inputs by the platform (pre-existing, "
      f"unchanged by this run): {NOT_SELECTED}")

# ------------------------------------------------------------------ PROOF 5. CANCEL
# The server-side half: the confirmation is a REQUIRED, RECORDED string, so a request that
# carries none is refused and nothing is archived. The browser half (dismissing the dialog) is
# executed in the Chromium section below.
NOCONF = post({"action": "projectdocumentarchive", "session_token": PM, "id": D,
               "period": LAST, "document_ids": [TARGET_ID]})
dc_after_noconf = post({"action": "projectdocumentcontrol", "session_token": PM, "id": D})
still_live = [d["document_id"] for d in
              [p for p in dc_after_noconf["periods"] if int(p["period"]) == LAST][0]["documents"]]
check("5a. an archive request with no recorded confirmation is refused and archives nothing",
      NOCONF.get("ok") is not True and TARGET_ID in still_live,
      f"error={NOCONF.get('error')!r}; target still live={TARGET_ID in still_live}")

# ------------------------------------------------------------------ THE ARCHIVE
CONFIRMATION = (f"Archive 1 document from reporting period {LAST} of {D}. The document and its "
                f"bytes are kept and stay readable. The extracted fields are withdrawn from "
                f"this project's live document set. The stored figures do not change until you "
                f"generate signals for every period. No other document is touched.")
ARCH = post({"action": "projectdocumentarchive", "session_token": PM, "id": D,
             "period": LAST, "document_ids": [TARGET_ID], "confirmation": CONFIRMATION})
assert ARCH.get("ok") is True, str(ARCH)[:400]
CAP["archive_response"] = ARCH
print("-" * 96)
print("ARCHIVE RESPONSE:")
print(json.dumps(ARCH, indent=2)[:1400])
print("-" * 96)

# ------------------------------------------------------------------ RULING 3 / §4.6
AFTER_ARCHIVE_NO_RECOMPUTE = read_row(LAST)
check("4b. the live figures do NOT move on archiving alone (archiving stages, recalculate applies)",
      AFTER_ARCHIVE_NO_RECOMPUTE.get("result_id") == BEFORE.get("result_id")
      and len(modules(AFTER_ARCHIVE_NO_RECOMPUTE)) == len(MODS_BEFORE),
      f"result_id unchanged={AFTER_ARCHIVE_NO_RECOMPUTE.get('result_id') == BEFORE.get('result_id')}, "
      f"modules {len(MODS_BEFORE)} -> {len(modules(AFTER_ARCHIVE_NO_RECOMPUTE))}")

# ------------------------------------------------------------------ PROOF 3. THE BYTES
content = client.get(f"/documents/{TARGET_ID}/content",
                     params={"project_id": D, "session_token": PM})
got = content.content
CAP["bytes_readback"] = {"status": content.status_code, "len": len(got),
                         "sha256": hashlib.sha256(got).hexdigest(),
                         "expected_sha256": hashlib.sha256(doc_bytes(TARGET)).hexdigest()}
check("3. the archived document's bytes read back intact from the archive",
      content.status_code == 200 and got == doc_bytes(TARGET),
      f"HTTP {content.status_code}, {len(got)} bytes, sha256 "
      f"{hashlib.sha256(got).hexdigest()[:16]}… == uploaded "
      f"{hashlib.sha256(doc_bytes(TARGET)).hexdigest()[:16]}…")

# ------------------------------------------------------------------ PROOF 4, SECOND HALF
RECALC = post({"action": "projectcomputeall", "session_token": PM, "id": D})
assert RECALC.get("ok") is True, str(RECALC)[:300]
CAP["recalc"] = RECALC
per_last = [r for r in RECALC["results"] if int(r.get("period", 0)) == LAST]
check("4c. recalculate after an archive RECOMPUTED period %d and did not skip it" % LAST,
      bool(per_last) and per_last[0].get("recomputed") is True
      and not per_last[0].get("skipped"),
      json.dumps(per_last[0] if per_last else {}))
DIRECT = post({"action": "projectcompute", "session_token": PM, "id": D, "period": LAST})
check("4d. a second projectcompute now skips again (the change was consumed, not repeated)",
      DIRECT.get("recomputed") is False, f"recomputed={DIRECT.get('recomputed')}")

AFTER = read_row(LAST)
MODS_AFTER = modules(AFTER)
ABS_AFTER = abstentions(AFTER)
SI_AFTER = AFTER.get("signal_inputs") or {}
CATS_AFTER = {k: (v or {}).get("status") for k, v in (AFTER.get("category_statuses") or {}).items()}

FELL_SILENT = sorted(set(MODS_BEFORE) - set(MODS_AFTER))
MOVED = sorted(m for m in set(MODS_BEFORE) & set(MODS_AFTER)
               if json.dumps(MODS_BEFORE[m], sort_keys=True, default=str)
               != json.dumps(MODS_AFTER[m], sort_keys=True, default=str))
CATS_CHANGED = sorted(k for k in set(CATS_BEFORE) | set(CATS_AFTER)
                      if CATS_BEFORE.get(k) != CATS_AFTER.get(k))
CAP["fell_silent"] = FELL_SILENT
CAP["moved"] = MOVED
CAP["categories_changed"] = {k: [CATS_BEFORE.get(k), CATS_AFTER.get(k)] for k in CATS_CHANGED}
CAP["new_abstention_reasons"] = {m: ABS_AFTER.get(m) for m in FELL_SILENT}

print("-" * 96)
print(f"WHAT CHANGED  modules before {len(MODS_BEFORE)} -> after {len(MODS_AFTER)}")
print(f"  fell silent : {FELL_SILENT}")
for m in FELL_SILENT:
    print(f"      {m}: {ABS_AFTER.get(m)!r}")
print(f"  moved       : {MOVED}")
print(f"  categories  : {CAP['categories_changed']}")
print("-" * 96)

# ------------------------------------------------------------------ PROOF 1, SECOND HALF
check("1b. every field the archived document supplied has left the live signal inputs",
      all(SI_AFTER.get(f) is None for f in TARGET_FIELDS),
      str({f: SI_AFTER.get(f) for f in TARGET_FIELDS}))
check("1c. at least one module that computed from it now DECLINES and states what it wants",
      bool(FELL_SILENT) and all(ABS_AFTER.get(m) for m in FELL_SILENT),
      f"{FELL_SILENT} -> " + "; ".join(f"{m}: {ABS_AFTER.get(m)}" for m in FELL_SILENT))
# No module may hold a value that came ONLY from the archived document.
# The strongest form available: the VALUES the archived document supplied appear nowhere in any
# surviving module's stored result. Searched over the serialised result of every module that
# still holds one, so a stale figure carried under a name nobody enumerated is still caught.
TARGET_VALUES = [SI_BEFORE[f] for f in LIVE_TARGET_FIELDS]


def numeric_leaves(node, out=None):
    """Every NUMBER anywhere in a stored module result. Numbers only, and never a substring of
    prose: the first form of this check matched "2.2" inside a PMBOK section citation, which is
    exactly the vacuity trap — a match on a name rather than on the site."""
    out = [] if out is None else out
    if isinstance(node, bool):
        return out
    if isinstance(node, (int, float)):
        out.append(float(node))
    elif isinstance(node, dict):
        for v in node.values():
            numeric_leaves(v, out)
    elif isinstance(node, list):
        for v in node:
            numeric_leaves(v, out)
    return out


survivors_holding = sorted(
    m for m, r in MODS_AFTER.items()
    if any(float(v) in numeric_leaves(r) for v in TARGET_VALUES))
CAP["survivors_holding_a_withdrawn_value"] = survivors_holding
check("7.1 no module still holds a value that came only from the archived document",
      not survivors_holding and all(SI_AFTER.get(f) is None for f in LIVE_TARGET_FIELDS),
      f"withdrawn values {TARGET_VALUES} appear as a number in {len(survivors_holding)} of "
      f"{len(MODS_AFTER)} surviving module results; signal_inputs now "
      f"{[(f, SI_AFTER.get(f)) for f in LIVE_TARGET_FIELDS]}")

# ------------------------------------------------------------------ PROOF 2. THE OTHERS
# EVERY OTHER LIVE DOCUMENT'S FIELDS, taken from the read the dialog itself uses — the field
# names selection actually produced, not the extraction's snake_case keys — so the comparison
# covers the real figures and cannot be vacuously empty.
OTHERS = [d for d in PERIODS[LAST]["documents"] if d["document_id"] != TARGET_ID]
OTHER_FIELDS = sorted({f for d in OTHERS for f in d["fields"]})
kept = {f: [SI_BEFORE.get(f), SI_AFTER.get(f)] for f in OTHER_FIELDS}
unchanged = {f: v for f, v in kept.items() if v[0] == v[1]}
changed = {f: v for f, v in kept.items() if v[0] != v[1]}
CAP["other_document_fields"] = {"unchanged": unchanged, "changed": changed}
check("2. archiving one document of several left every other document's figures unchanged",
      bool(kept) and not changed,
      f"{len(unchanged)} field(s) from the {len(OTHERS)} other period-{LAST} documents "
      f"identical before and after; {len(changed)} changed: {changed}")
dc2 = post({"action": "projectdocumentcontrol", "session_token": PM, "id": D})
live_after = {d["document_id"] for d in
              [p for p in dc2["periods"] if int(p["period"]) == LAST][0]["documents"]}
arch_after = {d["document_id"] for d in
              [p for p in dc2["periods"] if int(p["period"]) == LAST][0]["archived"]}
check("7.2 only the ticked document was withdrawn from the live set",
      arch_after == {TARGET_ID} and TARGET_ID not in live_after
      and len(live_after) == len(PERIODS[LAST]["documents"]) - 1,
      f"live {len(PERIODS[LAST]['documents'])} -> {len(live_after)}, archived {sorted(arch_after)}")

# ------------------------------------------------------------------ PROOF 6. THE RECORD
REC = dc2["record"]
CAP["record"] = REC
entry = REC[0] if REC else {}
print("-" * 96)
print("AUDIT RECORD, READ BACK:")
print(json.dumps(entry, indent=2))
print("-" * 96)
check("6. the archive record names the document, the period, the time and the fields withdrawn",
      bool(entry)
      and entry.get("period") == LAST
      and bool(entry.get("archived_at"))
      and bool(entry.get("archived_by"))
      and entry.get("confirmation") == CONFIRMATION
      and sorted(entry.get("fields_withdrawn") or []) == sorted(TARGET_FIELDS)
      and any(d.get("document_id") == TARGET_ID and d.get("filename") == f"{TARGET}.pdf"
              for d in (entry.get("documents") or [])),
      f"period={entry.get('period')} at={entry.get('archived_at')} by={entry.get('archived_by')} "
      f"fields={entry.get('fields_withdrawn')} confirmation recorded verbatim="
      f"{entry.get('confirmation') == CONFIRMATION}")

# The record is an APPEND-ONLY audit_events row, not derived state.
from app.research_models import AuditEvent  # noqa: E402
with Session() as s:
    rows = s.scalars(select(AuditEvent).where(
        AuditEvent.event_type == "documents_archived")).all()
    raw = [r for r in rows if (r.event_metadata or {}).get("project_id") == D]
    CAP["audit_rows_in_table"] = len(raw)
    check("6b. it is written to audit_events, the append-only table, one row per archive action",
          len(raw) == 1 and raw[0].event_type == "documents_archived",
          f"{len(raw)} row(s) of event_type=documents_archived for {D}, "
          f"event_id={raw[0].event_id if raw else None}")

# 7.4 nothing destroyed: the Document row and its bytes survive the recompute too.
from app.research_models import Document  # noqa: E402
with Session() as s:
    d = s.scalar(select(Document).where(Document.document_id == TARGET_ID))
    check("7.4 nothing is destroyed: the document row and its bytes survive the recalculate",
          d is not None and d.content == doc_bytes(TARGET) and d.extraction,
          f"content {len(d.content) if d and d.content else 0} bytes, extraction keys "
          f"{sorted((d.extraction or {}).keys()) if d else []}")

if os.environ.get("RUN71_NO_BROWSER"):
    CAP["failures"] = FAIL
    OUT.write_text(json.dumps(CAP, indent=2), encoding="utf-8")
    print("=" * 96)
    print(f"RESULT: {12 - len(FAIL)}/12 checks passed" if False else
          f"SERVER-SIDE RESULT: {len(FAIL)} failure(s): {FAIL}")
    raise SystemExit(1 if FAIL else 0)

# ==================================================================== PROOF 7. THE BROWSER
sock = socket.socket(); sock.bind(("127.0.0.1", 0)); PORT = sock.getsockname()[1]; sock.close()
import uvicorn  # noqa: E402
cfg = uvicorn.Config(main.app, host="127.0.0.1", port=PORT, log_level="critical")
server = uvicorn.Server(cfg)
threading.Thread(target=server.run, daemon=True).start()
for _ in range(200):
    try:
        c = socket.create_connection(("127.0.0.1", PORT), 0.2); c.close(); break
    except OSError:
        time.sleep(0.05)
BASE = f"http://127.0.0.1:{PORT}"

from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=CHROME,
                                 args=["--use-gl=swiftshader", "--no-sandbox", "--headless=new"])
    page = browser.new_page(viewport={"width": 1680, "height": 2400})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    for pat in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
        page.route(pat, lambda r: r.abort())
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.evaluate("(t) => sessionStorage.setItem('og-session-token', t)", PM)
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.add_style_tag(content="*,*::before,*::after{transition:none!important;animation:none!important}")
    page.wait_for_timeout(9000)
    page.evaluate("() => window.LinApp && LinApp.showPage && LinApp.showPage('portfolio')")
    page.wait_for_timeout(2000)
    try:
        page.evaluate("() => window.LinApp && LinApp.buildFallbackList && LinApp.buildFallbackList()")
    except Exception:
        pass
    page.wait_for_timeout(1500)
    # NOTHING IS PRIMED. render() is called and then read, in that order (Run 60's defect was
    # the reverse), and LinResults.prime is not called anywhere in this file.
    page.evaluate("(id) => window.LinDetail && LinDetail.render(id)", D)
    page.wait_for_timeout(10000)

    # 7a. THE CONTROL, AND ITS PLACE IN THE PANEL, read off the rendered DOM.
    CAP["head_actions"] = page.evaluate("""() => {
      const h = document.querySelector('.detail-head-actions');
      if (!h) return null;
      return Array.from(h.children).map(el => ({tag: el.tagName, cls: el.className,
                                                text: (el.textContent||'').trim()}));
    }""")
    print("=" * 96)
    print("BROWSER — .detail-head-actions, in document order:")
    for i, el in enumerate(CAP["head_actions"] or [], 1):
        print(f"  {i}. <{el['tag']} class=\"{el['cls']}\"> {el['text']!r}")
    check("7a. exactly one 'Document control' button exists on the detail page",
          len(page.query_selector_all("[data-doc-control]")) == 1,
          f"{len(page.query_selector_all('[data-doc-control]'))} found")
    # NO SECOND RECOMPUTE CONTROL: count every control on this page that recomputes.
    CAP["recompute_controls"] = page.evaluate("""() => {
      const root = document.getElementById('detail-root') || document.body;
      return Array.from(root.querySelectorAll('button')).map(b => (b.textContent||'').trim())
        .filter(t => /recomput|recalcul|generate signals/i.test(t));
    }""")
    check("7b. no second control duplicating the existing recompute",
          len(CAP["recompute_controls"]) == len(set(CAP["recompute_controls"]))
          and sum(1 for t in CAP["recompute_controls"] if "Generate signals" in t) == 1,
          str(CAP["recompute_controls"]))

    # CLICKED THROUGH THE DOM, not through Playwright's visibility gate: this harness renders
    # the detail page with LinDetail.render() while the portfolio page is the shown one (the
    # shape every browser driver here has used since Run 44), so the button is in the document
    # and wired but its ancestor page section is display:none. The listener under test is the
    # same listener either way; nothing about the control is bypassed.
    page.evaluate("() => document.querySelector('[data-doc-control]').click()")
    page.wait_for_timeout(2500)
    CAP["dialog_periods"] = page.evaluate("""() => {
      const s = document.querySelector('.dc-dc-period');
      return s ? Array.from(s.options).map(o => ({value: o.value, label: o.textContent})) : null;
    }""")
    print(f"  period dropdown options: {CAP['dialog_periods']}")
    check("7c. the period dropdown lists the periods that hold documents",
          [o["value"] for o in (CAP["dialog_periods"] or [])] == [str(p) for p in sorted(PERIODS)],
          str([o["value"] for o in (CAP["dialog_periods"] or [])]))

    def dialog_docs():
        return page.evaluate("""() => Array.from(document.querySelectorAll('.dc-dc-tick'))
            .map(c => ({id: c.dataset.docId,
                        label: (c.closest('label').textContent||'').trim()}))""")

    page.evaluate("""(v) => { const s = document.querySelector('.dc-dc-period');
        s.value = v; s.dispatchEvent(new Event('change', {bubbles:true})); }""", "1")
    page.wait_for_timeout(700)
    CAP["dialog_period_1"] = dialog_docs()
    page.evaluate("""(v) => { const s = document.querySelector('.dc-dc-period');
        s.value = v; s.dispatchEvent(new Event('change', {bubbles:true})); }""", str(LAST))
    page.wait_for_timeout(700)
    CAP["dialog_period_2"] = dialog_docs()
    print(f"  period 1 lists: {[d['label'] for d in CAP['dialog_period_1']]}")
    print(f"  period {LAST} lists: {[d['label'] for d in CAP['dialog_period_2']]}")
    check("7d. selecting a period lists THAT period's live documents with checkboxes",
          len(CAP["dialog_period_1"]) == len([1 for _t, p, _y, _e in DOCS if p == 1])
          and len(CAP["dialog_period_2"]) == len(live_after)
          and all(d["id"] != TARGET_ID for d in CAP["dialog_period_2"]),
          f"period 1: {len(CAP['dialog_period_1'])} boxes, period {LAST}: "
          f"{len(CAP['dialog_period_2'])} boxes, archived one absent from the live list")
    CAP["dialog_archived_shown"] = page.evaluate(
        """() => Array.from(document.querySelectorAll('.dc-dc-archived li'))
                      .map(li => (li.textContent||'').trim())""")
    CAP["dialog_record_shown"] = page.evaluate(
        """() => Array.from(document.querySelectorAll('.dc-dc-record-list li'))
                      .map(li => (li.textContent||'').trim())""")
    print(f"  archived shown in dialog: {CAP['dialog_archived_shown']}")
    print(f"  record shown in dialog:   {CAP['dialog_record_shown']}")

    # 7e. THE ARCHIVE CONTROL ACTS ON THE TICKED SET ONLY. Tick exactly one of the remaining
    # period-2 documents and read the sentence the confirmation shows.
    SECOND = CAP["dialog_period_2"][0]
    page.evaluate("""(id) => { const c = document.querySelector('.dc-dc-tick[data-doc-id="'+id+'"]');
        c.checked = true; c.dispatchEvent(new Event('change', {bubbles:true})); }""", SECOND["id"])
    page.wait_for_timeout(400)
    CAP["archive_button_label"] = page.evaluate(
        "() => document.querySelector('.dc-dc-archive').textContent.trim()")
    check("7e. the archive control names the ticked count only",
          CAP["archive_button_label"] == "Archive 1 document", CAP["archive_button_label"])

    # 7f. THE CANCEL PATH. Open the confirmation, read its sentence, then DISMISS it with
    # Escape and prove nothing was archived and no field was withdrawn.
    page.evaluate("() => document.querySelector('.dc-dc-archive').click()")
    page.wait_for_timeout(900)
    CAP["confirmation_sentence"] = page.evaluate(
        """() => { const p = document.querySelectorAll('.app-modal-backdrop');
                   const last = p[p.length-1];
                   const e = last && last.querySelector('.login-error');
                   return e ? e.textContent.trim() : null; }""")
    print(f"  confirmation sentence shown: {CAP['confirmation_sentence']!r}")
    check("7f. the confirmation names how many documents and which period",
          bool(CAP["confirmation_sentence"])
          and "Archive 1 document from reporting period 2" in CAP["confirmation_sentence"])
    page.keyboard.press("Escape")
    page.wait_for_timeout(1200)
    dc3 = post({"action": "projectdocumentcontrol", "session_token": PM, "id": D})
    arch_now = {d["document_id"] for d in
                [p for p in dc3["periods"] if int(p["period"]) == LAST][0]["archived"]}
    AFTER_CANCEL = read_row(LAST)
    CAP["after_cancel"] = {"archived": sorted(arch_now),
                           "result_id": AFTER_CANCEL.get("result_id"),
                           "modules": len(modules(AFTER_CANCEL))}
    check("5b. cancelling the confirmation archived nothing and withdrew no field",
          arch_now == {TARGET_ID}
          and AFTER_CANCEL.get("result_id") == AFTER.get("result_id")
          and modules(AFTER_CANCEL).keys() == MODS_AFTER.keys()
          and len(dc3["record"]) == 1,
          f"archived set still {sorted(arch_now)}, result_id unchanged, "
          f"{len(modules(AFTER_CANCEL))} modules, {len(dc3['record'])} audit entr(y/ies)")
    CAP["page_errors"] = errors
    browser.close()

server.should_exit = True
CAP["failures"] = FAIL
OUT.write_text(json.dumps(CAP, indent=2), encoding="utf-8")
print("=" * 96)
print(f"page errors: {CAP.get('page_errors')}")
TOTAL = 17
print(f"RESULT: {TOTAL - len(FAIL)}/{TOTAL} checks passed")
if FAIL:
    print("FAILURES: " + "; ".join(FAIL))
raise SystemExit(1 if FAIL else 0)
