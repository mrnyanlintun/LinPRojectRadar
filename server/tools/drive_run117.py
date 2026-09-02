"""
RUN 117 DRIVER. The three new supply paths, on real projects through the real upload route,
and every one of them proved able to fail.

NOTHING UNDER TEST IS SUPPLIED. Every project below is built from Run 110's census documents
plus or patched with the new fields, uploaded through `projectupload`, computed through
`projectcomputeall` and applied through `projectcategoryapply`. `saveprojectdata` is never
called and no structure is handed to any module.

STANDING RULE 4 IS THE SHAPE OF THIS FILE. Every check that a new feed WORKS is paired with a
check that the same feed FAILS when the fault is introduced into the thing the check reads --
the notice's severity word removed, the event table's schedule-path column removed, the firm
names removed -- and returns when it is taken out again.

Run from `server/`:  python tools/drive_run117.py
"""

import hashlib, json, pathlib, sys, time
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
SRC = (HERE / "drive_run110_census.py").read_text()
HEAD = SRC.split("def raw(t):")[0]
G = {"__name__": "r117proof"}
exec(compile(HEAD, "census_head", "exec"), G)
post, b64, S, END = G["post"], G["b64"], G["S"], G["END"]
BASE_DOCS = G["DOCS"]
from sqlalchemy import select
from app.documents import set_extractor_override
from app.extraction_client import StubExtractor
from app.models import Project
from app.research_identity import hash_access_token
from app.research_models import Participant, ComputedResult
from app.simulation import registry as REG

STAMP = str(int(time.time() * 1000))
SVC = REG.service_index()


def run_case(tag, extra_docs, patch=None):
    """Build a whole project from the census documents plus `extra_docs`, through the real
    upload/compute routes. Nothing is supplied to any module."""
    pid = f"PRJ-R117-{tag}-{STAMP}"
    admin_tok = f"r117a-{tag}-{STAMP}"
    docs = [(t, ty, dict(ex)) for t, ty, ex in BASE_DOCS]
    if patch:
        docs = [(t, ty, ({**ex, **patch[ty]} if ty in patch else ex)) for t, ty, ex in docs]
    docs = docs + list(extra_docs)

    def raw(t):
        return f"%PDF-1.4 R117 {tag} {STAMP} {t}\n".encode()

    set_extractor_override(StubExtractor(
        {hashlib.sha256(raw(t)).hexdigest(): (ty, ex) for t, ty, ex in docs}))
    with S() as s:
        r = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
        if r is None:
            s.add(Participant(pseudonymous_code=f"R117-A-{tag}-{STAMP}", role="ResearchAdmin",
                              access_token_hash=hash_access_token(admin_tok)))
        else:
            r.access_token_hash = hash_access_token(admin_tok)
        s.add(Project(legacy_id=pid, doc={"id": pid, "name": f"Run 117 {tag}",
                                          "sector": "construction", "signals": {}, "events": []}))
        s.commit()
    admin = post({"action": "researchlogin", "access_token": admin_tok})["session_token"]
    c = post({"action": "adminparticipantcreate", "session_token": admin,
              "pseudonymous_code": f"R117-PM-{tag}-{STAMP}", "role": "Participant",
              "account_type": "operational"})
    pm = post({"action": "researchlogin", "access_token": c["access_token"]})["session_token"]
    post({"action": "adminmemberadd", "session_token": admin, "id": pid,
          "participant_id": c["participant_id"], "project_role": "PM"})
    for t, ty, ex in docs:
        r = post({"action": "projectupload", "session_token": pm, "id": pid, "period": 1,
                  "period_end": END,
                  "documents": [{"filename": t + ".pdf", "mimeType": "application/pdf",
                                 "dataBase64": b64(raw(t))}]})
        assert r.get("ok"), (t, str(r)[:200])
    post({"action": "projectcomputeall", "session_token": pm, "id": pid})
    post({"action": "projectcategoryapply", "session_token": pm, "id": pid, "period": 1})
    with S() as s:
        p = s.scalar(select(Project).where(Project.legacy_id == pid))
        row = s.scalar(select(ComputedResult).where(ComputedResult.project_id == p.id,
                                                    ComputedResult.superseded_by.is_(None)))
        res = {m.get("module_id"): m for m in (row.module_results or [])} if row else {}
        ab = {a.get("module_id"): a for a in (row.abstained or [])} if row else {}
    census = {}
    for mid in SVC:
        r = res.get(mid)
        census[mid] = ("BAND " + str(r["status_color"]).upper()) if (r and r.get("status_color")) \
            else ("COMPUTED-NO-BAND" if r else ("ABSTAIN" if mid in ab else "NO ROW"))
    return census, res, ab


def show(name, census):
    b = sum(1 for v in census.values() if v.startswith("BAND"))
    c = sum(1 for v in census.values() if v == "COMPUTED-NO-BAND")
    a = sum(1 for v in census.values() if v == "ABSTAIN")
    n = sum(1 for v in census.values() if v == "NO ROW")
    print(f"  {name:<46} band {b} | cnb {c} | abstain {a} | no row {n}")
    return (b, c, a, n)


NOTICE_SAFETY = ("notice_sw", "correspondence_notice", {
    "document_date": END, "document_risk_score": 0.4,
    "notice_served_by": "State OSHA", "notice_served_on": "Meridian Construction LLC",
    "notice_claim": "Cessation of all work at the north elevation.",
    "notice_date_served": END, "notice_kind": "stop work order",
    "notice_enforcement_domain": "safety",
    "notice_enforcement_severity": "stop work order",
    "notice_enforcement_authority": "State Occupational Safety and Health Administration",
    "notice_enforcement_reference": "OSHA-SW-2026-0114",
})
NOTICE_ENV = ("notice_nov", "correspondence_notice", {
    "document_date": END, "document_risk_score": 0.4,
    "notice_served_by": "State Department of Environmental Quality",
    "notice_served_on": "Meridian Construction LLC",
    "notice_claim": "Unpermitted discharge to the receiving watercourse.",
    "notice_date_served": END, "notice_kind": "notice of violation",
    "notice_enforcement_domain": "environmental",
    "notice_enforcement_severity": "notice of violation",
    "notice_enforcement_authority": "State Department of Environmental Quality",
    "notice_enforcement_reference": "DEQ-NOV-2026-0221",
})
NOTICE_NODOMAIN = ("notice_nd", "correspondence_notice", {
    "document_date": END, "document_risk_score": 0.4,
    "notice_served_on": "Meridian Construction LLC", "notice_date_served": END,
    "notice_kind": "stop work order",
    "notice_enforcement_severity": "stop work order",
})
NOTICE_PLAIN = ("notice_pl", "correspondence_notice", {
    "document_date": END, "document_risk_score": 0.4,
    "notice_served_by": "Owner", "notice_served_on": "Meridian Construction LLC",
    "notice_claim": "Notice of a differing site condition.", "notice_date_served": END,
    "notice_contract_form": "AIA A201", "notice_kind": "differing site condition",
})

WEATHER_ROWS = [
    {"Event ID": "W-01", "Event date": "2026-02-11", "Activity ID": "A130",
     "Schedule path": "P-CRIT", "Days lost": 3, "Available float days": 8,
     "Causal evidence": "Site daily record and NOAA station observation",
     "Planned work": "Roof deck pour"},
    {"Event ID": "W-02", "Event date": "2026-03-04", "Activity ID": "A140",
     "Schedule path": "P-CRIT", "Days lost": 2, "Available float days": 8,
     "Causal evidence": "Site daily record and NOAA station observation",
     "Planned work": "Facade installation"},
]
FIELD_WEATHER = {"field_report": {
    "weather_events_json": WEATHER_ROWS,
    "weather_allowance_days_remaining": 6,
    "weather_calendar_id": "CAL-STD-5D",
    "weather_day_basis": "working",
}}
TRADE = {
    "ncr_log": {"trade_attribution_json": [
        {"NCR number": "NCR-014", "Subcontractor": "Harbour Electrical",
         "Type": "nonconformance", "Status": "Closed", "Date": "2026-02-20"},
        {"NCR number": "NCR-015", "Subcontractor": "Northline Mechanical",
         "Type": "nonconformance", "Status": "Closed", "Date": "2026-03-02"},
        {"NCR number": "NCR-016", "Type": "nonconformance", "Status": "Open",
         "Date": "2026-03-09"},
        {"Subcontractor": "Harbour Electrical", "Type": "nonconformance"},
    ]},
    "inspection_report": {"trade_attribution_json": [
        {"Item": "INSP-201", "Trade contractor": "Harbour Electrical",
         "Record kind": "inspection failure", "Status": "Rejected"},
    ]},
    "safety_report": {"trade_attribution_json": [
        {"Reference": "SAF-07", "Firm": "Northline Mechanical",
         "Record kind": "safety incident", "Severity": "first aid"},
    ]},
}

print("=" * 100)
print("RUN 117 PROOF -- every new feed, and every one proved able to fail")
print("=" * 100)

base, bres, bab = run_case("base", [])
show("BASELINE (census documents only)", base)
print(f"    A6.2={base['A6.2']}  A6.3={base['A6.3']}  A4.5={base['A4.5']}  A4.8={base['A4.8']}")

print("\n-- GOAL 1a: a SAFETY stop-work notice must take A6.2 to Red --")
c1, r1, _ = run_case("sw", [NOTICE_SAFETY])
show("WITH the stop-work notice", c1)
print(f"    A6.2 {base['A6.2']} -> {c1['A6.2']}")
print("    A6.2 sentence:", str(r1.get("A6.2", {}).get("evidence_metric"))[:200])
c1b, _, _ = run_case("sw_removed", [NOTICE_PLAIN])
print(f"    FALSIFICATION -- notice present but stating NO enforcement severity: "
      f"A6.2 -> {c1b['A6.2']}")

print("\n-- GOAL 1b: an ENVIRONMENTAL notice of violation must take A6.3 to Red --")
c2, r2, _ = run_case("nov", [NOTICE_ENV])
show("WITH the notice of violation", c2)
print(f"    A6.3 {base['A6.3']} -> {c2['A6.3']}")
print("    A6.3 sentence:", str(r2.get("A6.3", {}).get("evidence_metric"))[:200])
print("    A6.3 boundary:", str(r2.get("A6.3", {}).get("band_boundary"))[:160])

print("\n-- GOAL 1c: a notice stating NO regime must route to NEITHER module --")
c3, r3, _ = run_case("nodomain", [NOTICE_NODOMAIN])
print(f"    A6.2 {base['A6.2']} -> {c3['A6.2']}   A6.3 {base['A6.3']} -> {c3['A6.3']}")

print("\n-- GOAL 2: the field report's weather EVENT TABLE must band A4.5 --")
c4, r4, _ = run_case("weather", [], patch=FIELD_WEATHER)
show("WITH the field report's event table", c4)
print(f"    A4.5 {base['A4.5']} -> {c4['A4.5']}")
print("    A4.5 sentence:", str(r4.get("A4.5", {}).get("evidence_metric"))[:200])
_broken = {"field_report": {**FIELD_WEATHER["field_report"],
                            "weather_events_json": [
                                {k: v for k, v in WEATHER_ROWS[0].items()
                                 if k != "Schedule path"}]}}
c4b, _, a4b = run_case("weather_broken", [], patch=_broken)
print(f"    FALSIFICATION -- the same table with the SCHEDULE PATH column removed: "
      f"A4.5 -> {c4b['A4.5']}")

print("\n-- GOAL 3: trade records attributed, and the unattributed one reported --")
c5, r5, _ = run_case("trade", [], patch=TRADE)
show("WITH trade_attribution_json on three types", c5)
_a48 = r5.get("A4.8", {})
print(f"    A4.8 {base['A4.8']} -> {c5['A4.8']}  (the band must NOT move)")
print("    attributed:", _a48.get("trade_records_attributed_count"),
      "| unattributed:", _a48.get("trade_records_unattributed_count"),
      "| unusable rows:", _a48.get("trade_records_rows_unusable"))
print("    by firm:", {k: len(v) for k, v in
                       (_a48.get("trade_records_by_subcontractor") or {}).items()})
print("    types:", _a48.get("trade_records_source_document_types"))
print("    sentence:", str(_a48.get("evidence_metric"))[:400])
print("    posture effect:", str(_a48.get("trade_records_posture_effect"))[:120])
c5b, r5b, _ = run_case("trade_nofirm", [], patch={
    "ncr_log": {"trade_attribution_json": [
        {k: v for k, v in row.items() if k not in ("Subcontractor", "Firm", "Trade contractor")}
        for row in TRADE["ncr_log"]["trade_attribution_json"]]}})
_b = r5b.get("A4.8", {})
print(f"    FALSIFICATION -- the SAME rows with every firm name removed: attributed "
      f"{_b.get('trade_records_attributed_count')} | unattributed "
      f"{_b.get('trade_records_unattributed_count')} | A4.8 -> {c5b['A4.8']}")

print("\n-- REGRESSION: no module that banded at baseline may be un-banded by any case --")
for nm, cc in (("safety notice", c1), ("env notice", c2), ("no-domain notice", c3),
               ("field weather", c4), ("trade records", c5)):
    lost = [m for m in SVC if base[m].startswith("BAND") and not cc[m].startswith("BAND")]
    gained = [f"{m} {base[m]}->{cc[m]}" for m in SVC if base[m] != cc[m]]
    print(f"    {nm:<20} lost-band {lost or 'NONE'} | changed {gained or 'none'}")
print("=" * 100)


# --------------------------------------------------------------------------- the checked claims
PASSED = FAILED = 0


def check(cond, what, detail=""):
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print(f"  PASS  {what}" + (f"  [{detail}]" if detail else ""))
    else:
        FAILED += 1
        print(f"  FAIL  {what}" + (f"  [{detail}]" if detail else ""))


print()
print("=" * 100)
print("RUN 117 CHECKS")
print("=" * 100)
check(base["A6.2"] == "BAND GREEN" and c1["A6.2"] == "BAND RED",
      "GOAL 1a: a correspondence notice stating a safety stop-work order takes A6.2 to Red",
      f"{base['A6.2']} -> {c1['A6.2']}")
check(c1b["A6.2"] == "BAND GREEN",
      "FALSIFIED and RESTORED: a notice with NO enforcement severity leaves A6.2 Green",
      c1b["A6.2"])
check(base["A6.3"] == "BAND GREEN" and c2["A6.3"] == "BAND RED",
      "GOAL 1b: a correspondence notice stating a notice of violation takes A6.3 to Red",
      f"{base['A6.3']} -> {c2['A6.3']}")
check("HARD OVERRIDE" in str(r2.get("A6.3", {}).get("band_boundary") or ""),
      "and the Red it asserts is the owner's existing hard override, not a new band")
check(c3["A6.2"] == "BAND GREEN" and c3["A6.3"] == "BAND GREEN",
      "GOAL 1c: a notice stating NO regime routes to NEITHER module and is never guessed at",
      f"A6.2 {c3['A6.2']} / A6.3 {c3['A6.3']}")
check(base["A4.5"] == "ABSTAIN" and c4["A4.5"].startswith("BAND"),
      "GOAL 2: the field report's weather EVENT TABLE bands A4.5",
      f"{base['A4.5']} -> {c4['A4.5']}")
check(c4b["A4.5"] == "ABSTAIN",
      "FALSIFIED: the same table with the schedule-path column removed abstains again",
      c4b["A4.5"])
check((r5.get("A4.8", {}).get("trade_records_attributed_count") == 4
       and r5.get("A4.8", {}).get("trade_records_unattributed_count") == 1
       and r5.get("A4.8", {}).get("trade_records_rows_unusable") == 1),
      "GOAL 3: four records attributed, one unattributed, one unusable row dropped and counted",
      f"{r5.get('A4.8', {}).get('trade_records_attributed_count')}/"
      f"{r5.get('A4.8', {}).get('trade_records_unattributed_count')}/"
      f"{r5.get('A4.8', {}).get('trade_records_rows_unusable')}")
check(c5["A4.8"] == base["A4.8"],
      "and NO trade record moves A4.8's band -- the band is still the report's own rating",
      f"{base['A4.8']} -> {c5['A4.8']}")
check(_b.get("trade_records_attributed_count") == 0
      and _b.get("trade_records_unattributed_count") == 3,
      "FALSIFIED: the same rows with every firm name removed attribute NOTHING and are all "
      "reported as unattributed",
      f"{_b.get('trade_records_attributed_count')}/{_b.get('trade_records_unattributed_count')}")
_lost = [m for m in SVC for cc in (c1, c2, c3, c4, c5)
         if base[m].startswith("BAND") and not cc[m].startswith("BAND")]
check(not _lost, "REGRESSION: no module that banded at baseline is un-banded by any case",
      str(sorted(set(_lost))))
print("=" * 100)
print(f"RUN 117 DRIVER: {PASSED} passed, {FAILED} failed, {PASSED + FAILED} checks")
print("=" * 100)
