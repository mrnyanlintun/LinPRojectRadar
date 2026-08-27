#!/usr/bin/env python3
"""
RUN 73. DO THE CHARTS READ THE PROJECT BEING VIEWED?

The owner reports PRJ-001 and TST-007 rendering the same picture. Neither project exists in
this repository's database (enumerated: no PRJ-001, no TST-007), so this harness builds TWO
projects through the REAL routes with GENUINELY DIFFERENT documents -- different contract sum,
different EV/AC figures, different period counts, different logs -- plus a THIRD with no
documents at all, and compares them chart by chart.

THE BINDING CONSTRAINT (order sec.6.3, sec.9): the two projects are navigated between WITHOUT A
PAGE RELOAD, via LinDetail.render(id), which is the application's own navigation. A hard reload
between projects would hide a cache fault, which is how this survived.

RUN 61's rule is honoured: this file NEVER calls LinResults.prime.

argv[1] = label   argv[2] = path to write the captured JSON to
"""
from __future__ import annotations
import base64, hashlib, json, logging, os, pathlib, socket, sys, threading, time

LABEL = sys.argv[1] if len(sys.argv) > 1 else "run73"
OUT = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path("run73_capture.json")
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
from app.simulation.registry import registry_index, service_index, CORE_VOTING_MODULES  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
STAMP = int(time.time())

def post(p):
    r = client.post("/exec", content=json.dumps(p), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"HTTP {r.status_code} {r.text[:300]}"
    return r.json()

def b64(raw): return base64.b64encode(raw).decode()

ADMIN = f"run73-admin-{STAMP}"

# ---------------------------------------------------------------------------- TWO SPECIFICATIONS
# Project A: 4,000,000 contract, 8 periods, cost-overrun performance (Run 70's evidence).
# Project B: 11,500,000 contract, 4 periods, DIFFERENT figures throughout -- ahead on cost,
#            different RFI/NCR/safety/quality logs, different milestone slips.
# Nothing here is a copy of the other. The two document sets state different facts.

SPECS = {
  "A": dict(
    bac=4_000_000, last=8,
    end={1:"2026-03-31",2:"2026-04-30",3:"2026-05-31",4:"2026-06-30",
         5:"2026-07-31",6:"2026-08-31",7:"2026-09-30",8:"2026-10-31"},
    curve={0:(0,0),1:(1_020_000,1_000_000),2:(1_500_000,1_460_000),3:(2_000_000,1_950_000),
           4:(2_500_000,2_440_000),5:(3_000_000,2_930_000),6:(3_400_000,3_330_000),
           7:(3_750_000,3_680_000),8:(4_000_000,3_930_000)},
    evac={1:(1_000_000,1_050_000),2:(2_000_000,2_100_000),3:(2_150_000,2_300_000),
          4:(2_400_000,2_620_000),5:(2_700_000,2_980_000),6:(2_950_000,3_300_000),
          7:(3_150_000,3_570_000),8:(3_300_000,3_800_000)},
    start="2026-01-01", finish="2027-06-30",
    agency="General Services Administration", acq="GS-P-26-0114",
    contingency=(200_000, 90_000),
    rfi={"rfi_total":120,"rfi_open":30,"rfi_answered":90,"rfi_overdue":8,
         "avg_response_days":11,"rfi_period_days":30,"oldest_open_days":44},
    sub={"submittals_total":200,"submittals_rejected":24},
    ncr={"ncr_issued":14,"ncr_closed":9,"ncr_open":5},
    insp={"items_inspected":300,"items_passed":280,"items_failed":20,
          "deficiency_count":20,"critical_deficiency_count":2},
    qa={"total_findings":18,"critical_findings":3,"deficiency_count":18,"audit_score":82},
    safe={"osha_recordable_incidents":2,"total_manhours":180_000,"incident_rate":2.2},
    env={"permit_conditions_total":40,"violations":2,"compliance_rate":0.95},
    res={"planned_labor_hours":120_000,"actual_labor_hours":131_000,
         "quantity_installed_to_date":8200,"quantity_planned_to_date":9000},
    cost={"indirect_cost_plan":480_000,"indirect_cost_actual":561_000,
          "planned_allocation_base_quantity":120_000,"actual_allocation_base_quantity":131_000},
    risk=0.4,
    ms=[("MS-01","Foundations complete","2026-06-30","2026-07-19"),
        ("MS-02","Structure topped out","2026-09-30","2026-11-06"),
        ("MS-03","Building watertight","2026-12-15","2026-12-09")],
  ),
  "B": dict(
    bac=11_500_000, last=4,
    end={1:"2026-02-28",2:"2026-03-31",3:"2026-04-30",4:"2026-05-31"},
    curve={0:(0,0),1:(2_300_000,2_250_000),2:(4_600_000,4_500_000),
           3:(7_500_000,7_400_000),4:(11_500_000,11_300_000)},
    evac={1:(2_500_000,2_300_000),2:(5_100_000,4_700_000),
          3:(8_000_000,7_450_000),4:(10_400_000,9_800_000)},
    start="2025-11-01", finish="2027-02-28",
    agency="Department of Veterans Affairs", acq="VA-C-25-8890",
    contingency=(750_000, 610_000),
    rfi={"rfi_total":38,"rfi_open":4,"rfi_answered":34,"rfi_overdue":1,
         "avg_response_days":5,"rfi_period_days":30,"oldest_open_days":9},
    sub={"submittals_total":640,"submittals_rejected":19},
    ncr={"ncr_issued":3,"ncr_closed":3,"ncr_open":0},
    insp={"items_inspected":1450,"items_passed":1441,"items_failed":9,
          "deficiency_count":9,"critical_deficiency_count":0},
    qa={"total_findings":4,"critical_findings":0,"deficiency_count":4,"audit_score":96},
    safe={"osha_recordable_incidents":0,"total_manhours":410_000,"incident_rate":0.0},
    env={"permit_conditions_total":72,"violations":0,"compliance_rate":1.0},
    res={"planned_labor_hours":305_000,"actual_labor_hours":291_000,
         "quantity_installed_to_date":24_600,"quantity_planned_to_date":23_800},
    cost={"indirect_cost_plan":1_380_000,"indirect_cost_actual":1_299_000,
          "planned_allocation_base_quantity":305_000,"actual_allocation_base_quantity":291_000},
    risk=0.12,
    ms=[("MS-01","Site enabling works","2026-01-31","2026-01-24"),
        ("MS-02","Core and shell","2026-08-31","2026-08-20"),
        ("MS-03","Systems energised","2027-01-15","2027-01-15")],
  ),
}

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

def docx_with_table(rows):
    import io, zipfile
    def cell(t):
        return f'<w:tc><w:p><w:r><w:t xml:space="preserve">{t}</w:t></w:r></w:p></w:tc>'
    trs = "".join("<w:tr>" + "".join(cell(c) for c in r) + "</w:tr>" for r in rows)
    doc = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           f'<w:document xmlns:w="{W}"><w:body><w:tbl>{trs}</w:tbl></w:body></w:document>')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '</Types>')
        z.writestr("_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            '</Relationships>')
        z.writestr("word/document.xml", doc)
    return buf.getvalue()

DOCX_MIME = ("application/vnd.openxmlformats-officedocument"
             ".wordprocessingml.document")

def build_docs(key):
    """The document set for one project, as (tag, period, doc_type, extraction)."""
    S = SPECS[key]
    END, BAC, LAST = S["end"], S["bac"], S["last"]
    CURVE, EVAC = S["curve"], S["evac"]
    per = {}
    for p in range(1, LAST + 1):
        ev, ac = EVAC[p]; pv = CURVE[p][0]
        per[p] = {"ev":ev,"ac":ac,"pv":pv,
                  "planned_pct":round(pv/BAC*100,2), "actual_pct":round(ev/BAC*100,2)}
    base_rows = [
        {"Period": p, "Period ending": (END[p] if p else "2025-09-30"),
         "Planned value this period (USD)": CURVE[p][0]-CURVE[p-1][0] if p else 0,
         "Cumulative planned value (USD)": CURVE[p][0],
         "Cumulative planned spend (USD)": CURVE[p][1]}
        for p in range(0, LAST+1)]
    prov = {"baseline_version": f"PMB Rev {2 if key=='A' else 5}, reissued "
                               f"{'2026-01-15' if key=='A' else '2025-10-20'}",
            "baseline_approval_source": "Approved by the Project Sponsor and the Contracting "
                                        "Officer, Baseline Change Board record "
                                        f"BCB-2026-{'004' if key=='A' else '017'}"}
    docs = [
      ("contract", 1, "contract_value",
       {"original_contract_sum": BAC, "project_start_date": S["start"],
        "project_end_date": S["finish"], "federal_acquisition": True,
        "contracting_agency": S["agency"], "acquisition_designation": "development",
        "major_acquisition": True, "agency_procedure_requires_evms": True,
        "evms_clause_id": "FAR 52.234-4", "award_date": S["start"],
        "acquisition_id": S["acq"]}),
    ]
    for p in range(1, LAST+1):
        docs.append((f"tps{p}", p, "time_phased_schedule",
          {"planned_value_to_date": per[p]["pv"],
           "planned_percent_complete": per[p]["planned_pct"],
           "data_date": END[p], "document_date": END[p],
           "baseline_curve_json": base_rows, **prov}))
        extra = {}
        if p == LAST:
            extra = {"original_contingency": S["contingency"][0],
                     "remaining_contingency": S["contingency"][1]}
        docs.append((f"pay{p}", p, "pay_application",
          {"amount_paid_to_date": per[p]["ac"], "completed_to_date": per[p]["ev"],
           "percent_complete_verified": per[p]["actual_pct"],
           "application_date": END[p], "document_date": END[p], **extra}))
    # schedule updates in periods 1, 2 and LAST so the milestone history has >= 2 snapshots
    def ms_rows(shift_days):
        out = []
        for code, desc, bfin, cfin in S["ms"]:
            out.append({"Milestone": code, "Description": desc,
                        "Baseline finish": bfin, "Current finish": cfin})
        return out
    for idx, p in enumerate(sorted({1, 2, LAST})):
        docs.append((f"sched{p}", p, "schedule_update",
          {"data_date": END[p], "document_date": END[p],
           "planned_percent_complete": per[p]["planned_pct"],
           "milestones_json": ms_rows(idx)}))
    L = LAST
    docs += [
      ("riskL", L, "risk_register", {"document_date": END[L], "document_risk_score": S["risk"]}),
      ("rfiL", L, "rfi_log", {**S["rfi"], "log_date": END[L], "document_date": END[L]}),
      ("subL", L, "submittal_register", {**S["sub"], "document_date": END[L]}),
      ("ncrL", L, "ncr_log", {**S["ncr"], "report_period": END[L], "document_date": END[L]}),
      ("inspL", L, "inspection_report", {**S["insp"], "document_date": END[L]}),
      ("qaL", L, "quality_audit_report",
       {**S["qa"], "audit_date": END[L], "document_date": END[L]}),
      ("safeL", L, "safety_report",
       {**S["safe"], "report_period": END[L], "document_date": END[L]}),
      ("envL", L, "environmental_report",
       {**S["env"], "report_date": END[L], "document_date": END[L]}),
      ("resL", L, "resource_report",
       {**S["res"], "document_date": END[L],
        "resource_plan_version": f"Resource Plan Rev {3 if key=='A' else 6}",
        "resource_profile_json": [
          {"Period":"2026-03","Trade":"Electrical",
           "Demand hours": 4000 if key=="A" else 9100,
           "Available hours": 3500 if key=="A" else 9400},
          {"Period":"2026-03","Trade":"Mechanical",
           "Demand hours": 2000 if key=="A" else 5200,
           "Available hours": 2500 if key=="A" else 5600},
          {"Period":"2026-04","Trade":"Electrical",
           "Demand hours": 5200 if key=="A" else 8800,
           "Available hours": 4000 if key=="A" else 9000},
          {"Period":"2026-04","Trade":"Mechanical",
           "Demand hours": 2400 if key=="A" else 4900,
           "Available hours": 3000 if key=="A" else 5300}],
        "quantity_unit": "linear metres of conduit",
        "quantity_source": "field quantity survey signed off by the superintendent"}),
      ("costL", L, "cost_report",
       {**S["cost"], "report_date": END[L], "document_date": END[L],
        "overhead_allocation_base": "direct labour hours",
        "overhead_driver_source": "the overhead schedule printed in this cost report"}),
      ("coL", L, "change_order",
       {"change_order_date": END[L], "document_date": END[L],
        "modifications_json": (
          [{"Modification No":"M-001","Date issued":"2026-02-10","Federal":"Yes",
            "Modification type":"Bilateral","Executed by":"J. Alvarez, Contracting Officer",
            "Authority reference":"Warrant CO-4471, unlimited",
            "Signatories":"J. Alvarez; Northgate Constructors",
            "SF30 applicable":"Yes","Written instrument":"SF 30 dated 2026-02-10"},
           {"Modification No":"M-003","Date issued":"2026-04-18","Federal":"Yes",
            "Modification type":"Bilateral","Executed by":"T. Okafor, Project Engineer",
            "Authority reference":"","Signatories":"T. Okafor; Northgate Constructors",
            "SF30 applicable":"Yes","Written instrument":""}]
          if key == "A" else
          [{"Modification No":"V-100","Date issued":"2026-01-12","Federal":"Yes",
            "Modification type":"Bilateral","Executed by":"P. Nakamura, Contracting Officer",
            "Authority reference":"Warrant VA-8801, unlimited",
            "Signatories":"P. Nakamura; Cascade Builders",
            "SF30 applicable":"Yes","Written instrument":"SF 30 dated 2026-01-12"}])}),
    ]
    return docs

_BYTES_CACHE = {}

def doc_bytes(key, tag):
    """Bytes are UNIQUE PER PROJECT AND PER RUN, so no cached extraction from another
       project is replayed into this one (Run 72's open finding)."""
    if (key, tag) in _BYTES_CACHE:
        return _BYTES_CACHE[(key, tag)]
    if tag == "riskL":
        S = SPECS[key]
        rows = [["Risk ID","Description","Probability","Impact","Score"]]
        if key == "A":
            rows += [["R-01","Electrical subcontractor capacity","0.4","0.6","0.24"],
                     ["R-02","Long-lead switchgear delivery","0.5","0.7","0.35"]]
        else:
            rows += [["V-01","Permit renewal timing","0.1","0.3","0.03"],
                     ["V-02","Commissioning window","0.2","0.2","0.04"]]
        rows += [["MARKER", f"{key}-{STAMP}", "0", "0", "0"]]
        # zipfile stamps the current time into each entry, so the bytes are not
        # reproducible across calls; cache them so the extractor override's hash
        # is the hash of the bytes actually uploaded.
        _BYTES_CACHE[(key, tag)] = docx_with_table(rows)
        return _BYTES_CACHE[(key, tag)]
    return f"%PDF-1.4 RUN73 project={key} tag={tag} stamp={STAMP}\n".encode()

PA = f"PRJ-R73-{STAMP}-A"
PB = f"PRJ-R73-{STAMP}-B"
PE = f"PRJ-R73-{STAMP}-EMPTY"

DOCSETS = {"A": build_docs("A"), "B": build_docs("B")}
OVERRIDE = {}
for k, ds in DOCSETS.items():
    for tag, _p, ty, ex in ds:
        OVERRIDE[hashlib.sha256(doc_bytes(k, tag)).hexdigest()] = (ty, ex)
set_extractor_override(StubExtractor(OVERRIDE))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code=f"R73-ADMIN-{STAMP}", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    for pid, nm in ((PA, "Run 73 project A"), (PB, "Run 73 project B"),
                    (PE, "Run 73 project with no documents")):
        if s.scalar(select(Project).where(Project.legacy_id == pid)) is None:
            s.add(Project(legacy_id=pid,
                          doc={"id": pid, "name": nm, "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": f"R73-PM-{STAMP}", "role": "Participant",
                "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
for pid in (PA, PB, PE):
    post({"action": "adminmemberadd", "session_token": admin, "id": pid,
          "participant_id": created["participant_id"], "project_role": "PM"})

FIX = {}
for key, pid in (("A", PA), ("B", PB)):
    S = SPECS[key]
    for tag, per_, _ty, _ex in DOCSETS[key]:
        fn = f"{tag}.docx" if tag == "riskL" else f"{tag}.pdf"
        mt = DOCX_MIME if tag == "riskL" else "application/pdf"
        r = post({"action": "projectupload", "session_token": PM, "id": pid, "period": per_,
                  "period_end": S["end"][per_],
                  "documents": [{"filename": fn, "mimeType": mt,
                                 "dataBase64": b64(doc_bytes(key, tag))}]})
        assert r.get("ok") is True, f"{key}/{tag}: {str(r)[:300]}"
    cr = post({"action": "projectcomputeall", "session_token": PM, "id": pid})
    assert cr.get("ok") is True, f"{key} compute: {str(cr)[:400]}"
    pr = post({"action": "projectperiods", "session_token": PM, "id": pid})
    lp = pr.get("latest_computed_period")
    res = post({"action": "projectresults", "session_token": PM, "id": pid, "period": lp})
    ROW = res.get("result") or {}
    mr = ROW.get("module_results") or []
    cs = ROW.get("category_statuses") or {}
    FIX[key] = {
      "legacy_id": pid, "uploads": len(DOCSETS[key]),
      "contract_sum": S["bac"], "periods_uploaded": S["last"],
      "latest_computed_period": lp, "row_period": ROW.get("period"),
      "MODULES_HOLDING_A_RESULT": len(mr),
      "module_ids": sorted(m.get("module_id") for m in mr),
      "category_statuses": {k: (v or {}).get("status") for k, v in cs.items()},
      "CATEGORIES_CARRYING_A_STATUS": len([k for k,v in cs.items() if (v or {}).get("status")]),
      "project_status": ROW.get("project_status"),
      "abstained_count": len(ROW.get("abstained") or []),
      "no_band": sorted(m.get("module_id") for m in mr if m.get("status_color") is None),
    }

print("=" * 96)
print(f"LABEL: {LABEL}")
print(f"repository root: {ROOT}   DATABASE_URL: {os.environ.get('DATABASE_URL')}")
print(f"registry: {len(registry_index())}  in service: {len(service_index())}")
print("-" * 96)
for k in ("A", "B"):
    print(f"--- PROJECT {k}: {FIX[k]['legacy_id']}")
    for kk, vv in FIX[k].items():
        print(f"    {kk:32} {vv}")
print("=" * 96)

if os.environ.get("RUN73_FIXTURE_ONLY"):
    OUT.write_text(json.dumps({"label": LABEL, "fixture": FIX,
                               "empty_project": PE}, indent=2), encoding="utf-8")
    print(f"fixture-only capture written to {OUT}")
    raise SystemExit(0)

# ------------------------------------------------------------------------------------ BROWSER
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

# WHAT EACH OF THE FIVE CHARTS RENDERS, read off the DOM the charts actually built.
CHARTS_JS = r"""(id) => {
  const q  = (s) => document.querySelector(s);
  const qa = (s) => Array.from(document.querySelectorAll(s));
  const txt = (e) => e ? (e.textContent || '').trim() : null;

  // --- Signal Flow (neural_flow.js): SVG groups .lnf-nd carry data-kind and data-active.
  const nd = qa('.detail-neural-flow .lnf-nd');
  const byKind = {};
  nd.forEach(g => {
    const k = g.getAttribute('data-kind') || '?';
    byKind[k] = byKind[k] || {nodes:0, lit:0};
    byKind[k].nodes++;
    if (g.getAttribute('data-active') === 'true') byKind[k].lit++;
  });
  const flowHdr = qa('.detail-neural-flow text').map(t => (t.textContent||'').trim())
                    .filter(t => /UPLOADED ON THIS PROJECT|RETAINED/i.test(t));
  const signal_flow = {
    nodes: nd.length,
    lit: nd.filter(g => g.getAttribute('data-active') === 'true').length,
    by_kind: byKind,
    doc_header: flowHdr,
    doc_nodes: (byKind.document||{}).nodes || 0,
    doc_lit: (byKind.document||{}).lit || 0,
  };

  // --- Project Signal Network (projectnet2d.js): canvas + a rendered tally line.
  const pn = q('.projnet2d-panel');
  const canvas = q('.projnet2d-canvas');
  let px = null;
  try {
    if (canvas && canvas.width) {
      const d = canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height).data;
      let h = 5381;
      for (let i = 0; i < d.length; i += 997) { h = ((h*33) ^ d[i]) >>> 0; }
      px = h.toString(16) + ':' + canvas.width + 'x' + canvas.height;
    }
  } catch(e) { px = 'ERR:' + e.message; }
  const foot = txt(q('.projnet2d-foot'));
  let pnLit = null;
  if (foot) {
    const m = foot.match(/(\d+) Red · (\d+) Amber · (\d+) Yellow · (\d+) Green · (\d+) No-data/);
    if (m) pnLit = Number(m[1])+Number(m[2])+Number(m[3])+Number(m[4]);
  }
  const project_signal_network = {
    eyebrow: txt(q('.projnet2d-head .eyebrow')),
    tally: foot,
    lit: pnLit,
    awaiting: !!q('.projnet2d-awaiting'),
    canvas_pixels: px,
  };

  const secText = (secId) => {
    const b = document.getElementById('body-' + secId);
    return b ? (b.textContent || '').replace(/\s+/g,' ').trim().slice(0, 700) : null;
  };
  const secNums = (secId) => {
    const b = document.getElementById('body-' + secId);
    if (!b) return null;
    return ((b.textContent || '').match(/-?\d[\d,\.]*/g) || []).slice(0, 60);
  };
  const badge = (secId) => {
    const h = document.getElementById('sec-' + secId) ||
              document.querySelector('[data-section="' + secId + '"]');
    return h ? (h.textContent||'').replace(/\s+/g,' ').trim().slice(0,160) : null;
  };

  // --- Signal Web, Ensemble Analysis, Signal Ledger (built in detail.js).
  const cell = (sel) => qa(sel).length;
  const signal_web = {
    nodes: cell('#body-d-web [data-module-id], #body-d-web .swb-cell, #body-d-web .sw-node'),
    lit_by_class: qa('#body-d-web [class*="status-"], #body-d-web [data-status]')
                    .filter(e => {
                      const s = e.getAttribute('data-status') || e.className || '';
                      return /green|yellow|amber|red|complete/i.test(String(s));
                    }).length,
    numbers: secNums('d-web'), text: secText('d-web'),
  };
  const ensemble_analysis = { numbers: secNums('d-ensemble'), text: secText('d-ensemble') };
  const signal_ledger = {
    rows: cell('.detail-ledger tr, .detail-ledger [data-module-id]'),
    numbers: secNums('d-ledger'), text: secText('d-ledger'),
  };

  // --- what the page believes it is showing, and what the stored row says.
  const p = (window.LIN_PROJECTS || []).filter(x => x.id === id)[0] || null;
  let row = null;
  try { row = (window.LinResults && LinResults.rowFor(p)) || null; } catch(e) {}
  const cs = (row && row.category_statuses) || {};
  return {
    asked_for: id,
    project_found_in_list: !!p,
    stored: {
      row_present: !!row,
      row_period: row ? row.period : null,
      module_results: row && row.module_results ? row.module_results.length : null,
      cats_with_status: Object.keys(cs).filter(k => cs[k] && cs[k].status).length,
      category_statuses: Object.keys(cs).reduce((a,k)=>{a[k]=(cs[k]||{}).status||null;return a;},{}),
      project_status: row ? (row.project_status || null) : null,
    },
    signal_flow, project_signal_network, signal_web, ensemble_analysis, signal_ledger,
    heading: (document.querySelector('#detail-root h1, #detail-root .detail-title') || {}).textContent || null,
  };
}"""

OPEN_ALL_JS = r"""() => {
  const opened = [];
  document.querySelectorAll('[id^="body-"]').forEach((b) => {
    const id = b.id.replace(/^body-/, '');
    if (b.style.display === 'none' && window.toggleSection) { toggleSection(id); opened.push(id); }
  });
  return opened;
}"""

CAP = {"label": LABEL, "fixture": FIX, "projects": {"A": PA, "B": PB, "EMPTY": PE}}

def visit(page, pid, tag):
    """Navigate via the application's OWN navigation. NO RELOAD."""
    page.evaluate("(id) => window.LinDetail && LinDetail.render(id)", pid)
    page.wait_for_timeout(12000)
    page.evaluate(OPEN_ALL_JS)
    page.wait_for_timeout(9000)
    cap = page.evaluate(CHARTS_JS, pid)
    cap["_visit"] = tag
    CAP[tag] = cap
    return cap

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=CHROME,
                                 args=["--use-gl=swiftshader", "--no-sandbox", "--headless=new"])
    page = browser.new_page(viewport={"width": 1680, "height": 3200})
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
    page.evaluate("() => window.LinApp && LinApp.showPage && LinApp.showPage('workspace')")
    page.wait_for_timeout(3000)
    page.evaluate("() => window.LinApp && LinApp.showPage && LinApp.showPage('portfolio')")
    page.wait_for_timeout(1500)
    try:
        page.evaluate("() => window.LinApp && LinApp.buildFallbackList && LinApp.buildFallbackList()")
    except Exception:
        pass
    page.wait_for_timeout(1500)
    CAP["loaded_project_ids"] = page.evaluate(
        "() => (window.LIN_PROJECTS||[]).map(p=>p.id)")

    # PROOF 1 + 3 + 4 + 5: A -> B -> A -> EMPTY, all in ONE page load, no reload anywhere.
    visit(page, PA, "visit_1_A")
    visit(page, PB, "visit_2_B")
    visit(page, PA, "visit_3_A_again")
    visit(page, PE, "visit_4_EMPTY")
    CAP["page_errors"] = errors
    browser.close()
server.should_exit = True

def brief(c):
    return {
      "signal_flow_nodes": c["signal_flow"]["nodes"],
      "signal_flow_lit": c["signal_flow"]["lit"],
      "signal_flow_docs": c["signal_flow"]["doc_lit"],
      "signal_flow_doc_header": c["signal_flow"]["doc_header"],
      "projnet_tally": c["project_signal_network"]["tally"],
      "projnet_lit": c["project_signal_network"]["lit"],
      "projnet_pixels": c["project_signal_network"]["canvas_pixels"],
      "web_numbers": (c["signal_web"]["numbers"] or [])[:12],
      "ensemble_numbers": (c["ensemble_analysis"]["numbers"] or [])[:12],
      "ledger_rows": c["signal_ledger"]["rows"],
      "ledger_numbers": (c["signal_ledger"]["numbers"] or [])[:12],
      "stored_module_results": c["stored"]["module_results"],
      "stored_cats_with_status": c["stored"]["cats_with_status"],
      "stored_project_status": c["stored"]["project_status"],
      "stored_period": c["stored"]["row_period"],
    }

print("=" * 96)
print("PER-VISIT CHART READINGS (one page load, navigation via LinDetail.render, NO RELOAD)")
for tag in ("visit_1_A", "visit_2_B", "visit_3_A_again", "visit_4_EMPTY"):
    c = CAP.get(tag)
    if not c: continue
    print("-" * 96)
    print(f"{tag}   asked_for={c['asked_for']}")
    for k, v in brief(c).items():
        print(f"    {k:28} {v}")
print("=" * 96)
a1, b2, a3 = CAP["visit_1_A"], CAP["visit_2_B"], CAP["visit_3_A_again"]
print(f"A vs B IDENTICAL (whole capture minus id): "
      f"{json.dumps(brief(a1), sort_keys=True) == json.dumps(brief(b2), sort_keys=True)}")
print(f"A returns to its own figures on revisit: "
      f"{json.dumps(brief(a1), sort_keys=True) == json.dumps(brief(a3), sort_keys=True)}")
print(f"page errors: {CAP['page_errors']}")
OUT.write_text(json.dumps(CAP, indent=2), encoding="utf-8")
print(f"capture written to {OUT}")
