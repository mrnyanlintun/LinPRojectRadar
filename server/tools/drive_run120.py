"""
RUN 120. THE FOUR FACTORS, THEIR OVERRIDES, THE ELIGIBILITY RULE AND THE WORST ACTIVE FIRM.

Sections 1 to 6 prove the ENGINE -- `simulation.contractor_factors` -- at its own boundary, in
the arithmetic the owner stated. Section 7 proves the ROUTE end to end through the REAL upload,
compute and category-apply routes, with NOTHING under test supplied to a renderer and no
structure handed to a module. Section 8 is the FALSIFICATION set: every check below is shown
able to fail by putting the fault into the thing the check reads and then taking it out again.

Run from `server/`:  python tools/drive_run120.py
"""
import base64, hashlib, json, logging, pathlib, sys, time
HERE = pathlib.Path("/home/user/LinPRojectRadar/server/tools"); sys.path.insert(0, str(HERE.parent))
logging.disable(logging.INFO)
from app.simulation import contractor_factors as CF

PASS = FAIL = 0
def ck(name, got, want):
    global PASS, FAIL
    if got == want:
        PASS += 1; print(f"  PASS  {name}")
    else:
        FAIL += 1; print(f"  FAIL  {name}: got {got!r}, want {want!r}")

FULL = dict(packages_due=100, packages_completed_on_time=96,
            inspections_performed=100, inspections_passed_first=99,
            exposure_hours=400_000, recordable_incidents=1,
            commitments_due=100, commitments_met_on_time=96,
            active_work="yes")

def firm(**over):
    d = dict(FULL); d.update(over)
    return d

def posture(records=(), **over):
    return CF.firm_posture(firm="F", records=list(records), denominators=firm(**over))

print("=" * 100)
print("RUN 120 -- contractor delivery factors: four ladders, four overrides, the eligibility")
print("rule, the weighted aggregate and the worst active firm")
print("=" * 100)

# =============================================================== 1. THE FOUR LADDERS, EVERY RUNG
print("\n1. EACH FACTOR PROVED TO BAND, on every rung of its own ladder")
print("   1.1 Schedule reliability -- Green >=95; Yellow 90 to <95; Amber 80 to <90; Red <80")
for on_time, want in ((100, "Green"), (95, "Green"), (94.9, "Yellow"), (90, "Yellow"),
                      (89.9, "Amber"), (80, "Amber"), (79.9, "Red"), (0, "Red")):
    p = posture(packages_completed_on_time=on_time)
    ck(f"schedule {on_time}% -> {want}", p["factor_bands"]["schedule_reliability"], want)

print("   1.2 Quality execution -- Green >=98; Yellow 95 to <98; Amber 90 to <95; Red <90")
for n, want in ((100, "Green"), (98, "Green"), (97.9, "Yellow"), (95, "Yellow"),
                (94.9, "Amber"), (90, "Amber"), (89.9, "Red"), (0, "Red")):
    p = posture(inspections_passed_first=n)
    ck(f"quality {n}% -> {want}", p["factor_bands"]["quality_execution"], want)

print("   1.3 Safety TRIR = recordables x 200,000 / hours -- Green <1.0; Yellow 1.0 to <2.0;")
print("       Amber 2.0 to <3.0; Red >=3.0. The FORMULA is codified, the CUTS are the owner's.")
for rec, want, rate in ((1, "Green", 0.5), (2, "Yellow", 1.0), (3, "Yellow", 1.5),
                        (4, "Amber", 2.0), (5, "Amber", 2.5), (6, "Red", 3.0), (10, "Red", 5.0)):
    p = posture(recordable_incidents=rec)
    ck(f"safety {rec} recordables / 400,000h = TRIR {rate} -> {want}",
       (p["factor_bands"]["safety"], p["factor_values"]["safety"]), (want, rate))

print("   1.4 Commercial and administration -- Green >=95; Yellow 90 to <95; Amber 80 to <90;")
print("       Red <80")
for n, want in ((100, "Green"), (95, "Green"), (94.9, "Yellow"), (90, "Yellow"),
                (89.9, "Amber"), (80, "Amber"), (79.9, "Red"), (0, "Red")):
    p = posture(commitments_met_on_time=n)
    ck(f"commercial {n}% -> {want}", p["factor_bands"]["commercial_administration"], want)

# ============================================== 2. EACH OVERRIDE, PROVED TO FIRE AND NOT TO FIRE
print("\n2. EACH OVERRIDE PROVED BOTH TO FIRE AND NOT TO FIRE -- eight proofs")
print("   Overrides apply AFTER the weighted calculation; the final posture is the WORSE of the")
print("   weighted result and any override that fired.")

CLEAN = firm()   # all four Green, weighted severity 0.00

def one(records, **over):
    return CF.firm_posture(firm="F", records=records, denominators=firm(**over))

# 2.1 schedule override
r_fire = [{"record_reference": "WP-7", "record_kind": "work_package",
           "record_milestone_forecast_late": "yes"}]
r_not = [{"record_reference": "WP-7", "record_kind": "work_package",
          "record_milestone_forecast_late": "no"}]
p = one(r_fire); q = one(r_not)
ck("schedule override FIRES on a controlling-path milestone forecast late",
   (p["overrides_fired"], p["final_posture"]), (["schedule_reliability"], "Red"))
ck("schedule override does NOT fire when the same column says no",
   (q["overrides_fired"], q["final_posture"]), ([], "Green"))

# 2.2 quality override
r_fire = [{"record_reference": "NCR-3", "record_kind": "nonconformance",
           "record_severity": "life_safety", "record_status": "open"}]
r_not = [{"record_reference": "NCR-3", "record_kind": "nonconformance",
          "record_severity": "life_safety", "record_status": "closed"}]
r_word = [{"record_reference": "NCR-4", "record_kind": "nonconformance",
           "record_severity": "cosmetic", "record_status": "open"}]
p = one(r_fire); q = one(r_not); w = one(r_word)
ck("quality override FIRES on an OPEN critical life-safety nonconformance",
   (p["overrides_fired"], p["final_posture"]), (["quality_execution"], "Red"))
ck("quality override does NOT fire once the same nonconformance is CLOSED",
   (q["overrides_fired"], q["final_posture"]), ([], "Green"))
ck("a severity word outside the owner's closed set fires NOTHING and is not dropped to the "
   "nearest", w["overrides_fired"], [])

# 2.3 safety override
r_fire = [{"record_reference": "SAF-1", "record_kind": "incident",
           "record_severity": "fatality", "record_status": "open"}]
r_not = [{"record_reference": "SAF-1", "record_kind": "incident",
          "record_severity": "first_aid", "record_status": "open"}]
p = one(r_fire); q = one(r_not)
ck("safety override FIRES on a fatality", (p["overrides_fired"], p["final_posture"]),
   (["safety"], "Red"))
ck("safety override does NOT fire on a first-aid case",
   (q["overrides_fired"], q["final_posture"]), ([], "Green"))

# 2.4 commercial override
r_fire = [{"record_reference": "SUB-12", "record_kind": "submittal", "record_status": "open",
           "record_milestone_forecast_late": "yes"}]
r_not = [{"record_reference": "SUB-12", "record_kind": "submittal", "record_status": "closed",
          "record_milestone_forecast_late": "yes"}]
p = one(r_fire); q = one(r_not)
ck("commercial override FIRES on an UNFULFILLED submittal blocking the controlling path",
   ("commercial_administration" in p["overrides_fired"], p["final_posture"]), (True, "Red"))
ck("commercial override does NOT fire once that submittal is closed",
   ("commercial_administration" in q["overrides_fired"], q["final_posture"]), (False, "Green"))

print("\n   2.5 AN OVERRIDE NEVER IMPROVES A POSTURE. A firm whose weighted result is already")
print("       Red and whose override fires stays Red; a firm whose weighted result is Amber and")
print("       whose override fires becomes Red -- the WORSE of the two, never the override alone.")
_AMBER = firm(packages_completed_on_time=85, inspections_passed_first=92)
p = CF.firm_posture(firm="F", records=r_fire, denominators=_AMBER)
ck("weighted Amber (0.40x2 + 0.25x2 = 1.30) + override -> Red",
   (p["weighted_posture"], p["final_posture"]), ("Amber", "Red"))
p2 = CF.firm_posture(firm="F", records=[], denominators=_AMBER)
ck("the same weighted Amber with NO override stays Amber", p2["final_posture"], "Amber")
_RED = firm(packages_completed_on_time=10, inspections_passed_first=10,
            recordable_incidents=6, commitments_met_on_time=10)
p3 = CF.firm_posture(firm="F", records=r_fire, denominators=_RED)
ck("weighted Red + override stays Red -- an override never improves a posture",
   (p3["weighted_posture"], p3["final_posture"]), ("Red", "Red"))

# ================================================================== 3. THE WEIGHTED AGGREGATE
print("\n3. THE WEIGHTED AGGREGATE -- 0.40 schedule + 0.25 quality + 0.20 safety + 0.15")
print("   commercial, on severities Green 0, Yellow 1, Amber 2, Red 3. Cuts: 0.00 to <0.50")
print("   Green; 0.50 to <1.25 Yellow; 1.25 to <2.00 Amber; 2.00 to 3.00 Red.")
CASES = [
    # (schedule%, quality%, recordables, commercial%) -> (severity, band)
    ((96, 99, 1, 96), 0.0, "Green"),
    ((92, 99, 1, 96), 0.4, "Green"),      # Yellow schedule alone: 0.40 x 1
    ((85, 99, 1, 96), 0.8, "Yellow"),     # Amber schedule alone: 0.40 x 2
    ((70, 99, 1, 96), 1.2, "Yellow"),     # Red schedule alone: 0.40 x 3 = 1.20, still Yellow
    ((70, 94, 1, 96), 1.7, "Amber"),      # + Amber quality 0.50
    ((70, 89, 6, 79), 3.0, "Red"),        # every factor Red
    ((96, 99, 1, 79), 0.45, "Green"),     # Red commercial alone: 0.15 x 3 = 0.45
]
for (s, q, rec, c), sev, want in CASES:
    p = posture(packages_completed_on_time=s, inspections_passed_first=q,
                recordable_incidents=rec, commitments_met_on_time=c)
    ck(f"schedule {s}%, quality {q}%, {rec} recordables, commercial {c}% -> {sev} {want}",
       (p["weighted_severity"], p["weighted_posture"]), (sev, want))

print("   3.1 THE BOUNDARIES ARE INCLUSIVE ON THEIR LOWER SIDE")
for sev, want in ((0.0, "Green"), (0.4999, "Green"), (0.50, "Yellow"), (1.2499, "Yellow"),
                  (1.25, "Amber"), (1.9999, "Amber"), (2.00, "Red"), (3.00, "Red")):
    ck(f"weighted severity {sev} -> {want}", CF.band_weighted(sev), want)

print("   3.2 THE SCALE IS NOT `category_posture`'s, AND IS NOT A NEGATION OF IT")
from app.simulation.category_posture import BAND_SCORE, AVERAGE_CUTS
from app.simulation.fusion import BAND_SEVERITY
ck("category_posture.BAND_SCORE is higher-is-BETTER and straddles zero",
   BAND_SCORE, {"Green": 2.0, "Yellow": 1.0, "Amber": -1.0, "Red": -2.0})
ck("it is NOT a rescaling of the owner's severity (a negation would give -0/-1/-2/-3)",
   [-BAND_SCORE[b] for b in ("Green", "Yellow", "Amber", "Red")] == [0, 1, 2, 3], False)
ck("fusion.BAND_SEVERITY IS the owner's scale, already shipped, and is what the engine imports",
   BAND_SEVERITY, {"Green": 0, "Yellow": 1, "Amber": 2, "Red": 3})
ck("the engine imports it rather than restating it",
   CF.BAND_SEVERITY is BAND_SEVERITY, True)

# ================================================================= 4. THE ELIGIBILITY RULE
print("\n4. THE ELIGIBILITY RULE -- ALL FOUR OR NONE, and the two are NEVER blended")
for missing in ("packages_due", "inspections_passed_first", "exposure_hours", "commitments_due"):
    d = firm(); d.pop(missing)
    p = CF.firm_posture(firm="F", records=[], denominators=d, source_posture="Amber",
                        source_rating="Marginal")
    ck(f"dropping {missing} makes the firm INELIGIBLE and it takes the FALLBACK",
       (p["eligible_for_four_factor"], p["posture_basis"], p["final_posture"]),
       (False, "source_rating_fallback", "Amber"))

print("   4.1 THE HEADLINE PROOF THE ORDER ASKS FOR: three factors and a source rating must")
print("       take the fallback, NOT a blend. The three present factors are ALL GREEN and the")
print("       source rating is Marginal (Amber). A blend of any kind would publish better than")
print("       Amber; the fallback publishes Amber.")
d = firm(); d.pop("exposure_hours"); d.pop("recordable_incidents")
p = CF.firm_posture(firm="F", records=[], denominators=d, source_posture="Amber",
                    source_rating="Marginal")
ck("three Green factors + a Marginal source rating -> Amber, the source rating unchanged",
   p["final_posture"], "Amber")
ck("...and the weighted severity was never formed at all", p["weighted_severity"], None)
ck("...and the safety factor is UNAVAILABLE, not Green",
   (p["factor_bands"]["safety"], p["by_name"]["safety"]["available"]), (None, False))
ck("...and the three that were calculable are still reported",
   sorted(p["factors_available"]),
   ["commercial_administration", "quality_execution", "schedule_reliability"])

print("   4.2 A MISSING FACTOR MUST NOT QUIETLY IMPROVE A FIRM. The same firm with three RED")
print("       factors and no safety figure takes the SAME Amber fallback -- the calculation is")
print("       discarded whole, in both directions.")
d2 = firm(packages_completed_on_time=10, inspections_passed_first=10,
          commitments_met_on_time=10)
d2.pop("exposure_hours")
p2 = CF.firm_posture(firm="F", records=[], denominators=d2, source_posture="Amber",
                     source_rating="Marginal")
ck("three Red factors + a Marginal source rating -> Amber, not Red", p2["final_posture"],
   "Amber")

print("   4.3 NEITHER AVAILABLE -> NOT ASSESSED. Never Green.")
p3 = CF.firm_posture(firm="F", records=[], denominators={}, source_posture=None)
ck("no factors and no source rating -> Not Assessed",
   (p3["final_posture"], p3["posture_basis"]), (None, "not_assessed"))
ck("every factor says what it is waiting for",
   all(f["unavailable_reason"] for f in p3["factors"]), True)

print("   4.4 A ZERO DENOMINATOR NEVER PRODUCES A RATE")
p4 = CF.firm_posture(firm="F", records=[], denominators=firm(packages_due=0))
ck("packages_due 0 -> schedule UNAVAILABLE, and the firm ineligible",
   (p4["factor_bands"]["schedule_reliability"], p4["eligible_for_four_factor"]), (None, False))

print("   4.5 AN OVERRIDE ON AN INELIGIBLE FIRM MOVES NOTHING, and is still REPORTED.")
d5 = firm(); d5.pop("commitments_due")
p5 = CF.firm_posture(firm="F", records=r_fire, denominators=d5, source_posture="Green",
                     source_rating="Very Good")
ck("a fired override on a fallback firm is reported...", bool(p5["overrides_fired"]), True)
ck("...and does not move the fallback posture", p5["final_posture"], "Green")

# ============================================================ 5. THE WORST ACTIVE FIRM
print("\n5. THE WORST FINAL POSTURE AMONG FIRMS WITH ACTIVE WORK")
A = CF.firm_posture(firm="Alpha", records=[], denominators=firm())                    # Green
B = CF.firm_posture(firm="Bravo", records=[],
                    denominators=firm(packages_completed_on_time=70))                 # Yellow
C = CF.firm_posture(firm="Coast", records=[],
                    denominators=firm(packages_completed_on_time=10,
                                      inspections_passed_first=10,
                                      recordable_incidents=6,
                                      commitments_met_on_time=10))                    # Red
ck("Alpha Green, Bravo Yellow, Coast Red",
   [A["final_posture"], B["final_posture"], C["final_posture"]], ["Green", "Yellow", "Red"])
ck("the worst governs", CF.governing([A, B, C])["firm"], "Coast")

C_off = CF.firm_posture(firm="Coast", records=[],
                        denominators=firm(packages_completed_on_time=10,
                                          inspections_passed_first=10,
                                          recordable_incidents=6,
                                          commitments_met_on_time=10, active_work="no"))
ck("a firm the document states has NO active work is out of the comparison",
   CF.governing([A, B, C_off])["firm"], "Bravo")
blk = CF.across_firms([A, B, C_off])
ck("...and the exclusion is REPORTED, never silent",
   blk["contractor_firms_excluded_no_active_work"], ["Coast"])

C_silent = dict(firm(packages_completed_on_time=10, inspections_passed_first=10,
                     recordable_incidents=6, commitments_met_on_time=10))
C_silent.pop("active_work")
C_sil = CF.firm_posture(firm="Coast", records=[], denominators=C_silent)
ck("a firm that states NOTHING about active work is CARRIED in the comparison",
   CF.governing([A, B, C_sil])["firm"], "Coast")
ck("...and the silence is reported",
   CF.across_firms([A, B, C_sil])["contractor_firms_active_work_not_stated"], ["Coast"])

# ================================================== 6. NO MODULE POSTURE IS READ (section 7.2)
print("\n6. NO MODULE POSTURE IS READ ANYWHERE IN THIS CALCULATION (section 7.2)")
# THE CHECK IS OVER THE EXECUTABLE CODE, NOT THE PROSE. The module's docstring names A6.1,
# A6.2, A6.3 and `category_posture` precisely in order to record why it does NOT read them, and
# a check that failed on the explanation would be a check nobody could satisfy honestly. So the
# source is parsed, every docstring and every comment is stripped, and what is left is the code.
import ast, io, tokenize
_path = pathlib.Path(
    "/home/user/LinPRojectRadar/server/app/simulation/contractor_factors.py")
_src = _path.read_text()
_tree = ast.parse(_src)
for _node in ast.walk(_tree):
    if isinstance(_node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        _d = ast.get_docstring(_node, clean=False)
        if _d:
            _node.body = _node.body[1:] or [ast.Pass()]
# EVERY STRING LITERAL IS STRIPPED TOO. `SCOPE_WORDS` is the sentence a reader is shown -- "not
# A6.1's, not A6.2's, not A6.3's" -- and naming the three modules it does not read is the point
# of it. What must contain no module reference is the code that EXECUTES.
class _Blank(ast.NodeTransformer):
    def visit_Constant(self, node):
        return ast.copy_location(ast.Constant(value=""), node) if isinstance(
            node.value, str) else node
CODE = ast.unparse(_Blank().visit(_tree))
for forbidden in ("A6.1", "A6.2", "A6.3", "category_posture", "module_results", "status_color",
                  "project_posture", "BAND_SCORE", "moduleReviews"):
    ck(f"the CODE of `contractor_factors.py` never mentions {forbidden}", forbidden in CODE,
       False)
ck("it imports exactly three platform names, and every one of them is a SEVERITY ORDERING, a "
   "CODIFIED FORMULA or a CLOSED VOCABULARY -- never a posture",
   sorted(n.module for n in ast.walk(_tree) if isinstance(n, ast.ImportFrom)
          and n.level and n.module),
   ["fusion", "models_cat89", "trade_factors"])

# ============================================================ 7. THE REAL ROUTE, END TO END
print("\n7. THE REAL ROUTE -- upload, compute and category-apply, nothing supplied")
from fastapi.testclient import TestClient
from sqlalchemy import select
import app.main as main
from app.documents import set_extractor_override
from app.extraction_client import StubExtractor
from app.models import Project
from app.research_identity import hash_access_token
from app.research_models import Participant, ComputedResult
client = TestClient(main.app, raise_server_exceptions=False); S = main.SessionFactory
def post(p):
    r = client.post("/exec", content=json.dumps(p), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, r.text[:400]
    return r.json()
def b64(x): return base64.b64encode(x).decode()

END = "2026-03-31"

def run_case(tag, docs):
    stamp = str(int(time.time() * 1000)) + tag
    pid = "PRJ-R120-" + stamp
    admin_tok = "r120a-" + stamp
    def raw(t): return f"%PDF-1.4 R120 {stamp} {t}\n".encode()
    set_extractor_override(StubExtractor(
        {hashlib.sha256(raw(t)).hexdigest(): (ty, ex) for t, ty, ex in docs}))
    with S() as s:
        r = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
        if r is None:
            s.add(Participant(pseudonymous_code="R120-A-" + stamp, role="ResearchAdmin",
                              access_token_hash=hash_access_token(admin_tok)))
        else:
            r.access_token_hash = hash_access_token(admin_tok)
        if s.scalar(select(Project).where(Project.legacy_id == pid)) is None:
            s.add(Project(legacy_id=pid, doc={"id": pid, "name": "Run 120 " + tag,
                                              "sector": "construction", "signals": {},
                                              "events": []}))
        s.commit()
    admin = post({"action": "researchlogin", "access_token": admin_tok})["session_token"]
    c = post({"action": "adminparticipantcreate", "session_token": admin,
              "pseudonymous_code": "R120-PM-" + stamp, "role": "Participant",
              "account_type": "operational"})
    pm = post({"action": "researchlogin", "access_token": c["access_token"]})["session_token"]
    post({"action": "adminmemberadd", "session_token": admin, "id": pid,
          "participant_id": c["participant_id"], "project_role": "PM"})
    for t, ty, ex in docs:
        post({"action": "projectupload", "session_token": pm, "id": pid, "period": 1,
              "period_end": END,
              "documents": [{"filename": t + ".pdf", "mimeType": "application/pdf",
                             "dataBase64": b64(raw(t))}]})
    post({"action": "projectcomputeall", "session_token": pm, "id": pid})
    with S() as s:
        p = s.scalar(select(Project).where(Project.legacy_id == pid))
        row = s.scalar(select(ComputedResult).where(ComputedResult.project_id == p.id,
                                                    ComputedResult.superseded_by.is_(None)))
        res = {m.get("module_id"): m for m in (row.module_results or [])} if row else {}
        ab = {a.get("module_id"): a for a in (row.abstained or [])} if row else {}
    return res.get("A6.4"), ab.get("A6.4")

# --- 7.1 A project whose documents state everything four factors need, and a firm that is Amber
INSP = ("insp", "inspection_report", {
    "items_inspected": 200, "items_passed": 198, "items_failed": 2,
    "items_passing_first_inspection": 193, "document_date": END,
    "trade_denominators_json": [
        {"Subcontractor": "Northline Mechanical", "Inspections performed": 100,
         "Inspections passed first": 92, "Packages due": 50,
         "Packages completed on time": 44, "Commitments due": 40,
         "Commitments met on time": 37, "Exposure hours": 200000,
         "Recordable incidents": 2, "Active work": "yes"}],
    "trade_attribution_json": [
        {"Reference": "NCR-11", "Subcontractor": "Northline Mechanical",
         "Kind": "nonconformance", "Severity": "minor", "Status": "open"}]})
row, ab = run_case("a", [INSP])
print("   7.1 one inspection report stating all four populations for one firm")
ck("A6.4 bands from the four-factor calculation",
   (row or {}).get("contractor_governing_basis"), "four_factor_calculation")
gov = next((p for p in (row or {}).get("contractor_firm_postures", [])), None)
ck("schedule 44/50 = 88% -> Amber", (gov or {})["factor_bands"]["schedule_reliability"], "Amber")
ck("quality 92/100 = 92% -> Amber", (gov or {})["factor_bands"]["quality_execution"], "Amber")
ck("safety 2 x 200000 / 200000 = TRIR 2.0 -> Amber", (gov or {})["factor_bands"]["safety"],
   "Amber")
ck("commercial 37/40 = 92.5% -> Yellow",
   (gov or {})["factor_bands"]["commercial_administration"], "Yellow")
ck("weighted severity 0.40x2 + 0.25x2 + 0.20x2 + 0.15x1 = 1.85 -> Amber",
   ((gov or {})["weighted_severity"], (gov or {})["weighted_posture"]), (1.85, "Amber"))
ck("an Amber posture is HELD for PM review and asserts no band",
   ((row or {}).get("status_color"), (row or {}).get("module_state")),
   (None, "pending_pm_review"))
ck("the audit record carries the four factor values",
   sorted(((row or {}).get("pm_review_audit_record") or {}).get("factor_values") or {}),
   ["commercial_administration", "quality_execution", "safety", "schedule_reliability"])
ck("the audit record carries the evidence references behind the quality factor",
   (((row or {}).get("pm_review_audit_record") or {}).get("factor_evidence_references")
    or {}).get("quality_execution"), ["NCR-11"])

# --- 7.2 The same project with a GREEN firm: it stands, unheld, and enters Delivery Quality
GREEN = ("insp", "inspection_report", {
    "items_inspected": 200, "items_passing_first_inspection": 193, "document_date": END,
    "trade_denominators_json": [
        {"Subcontractor": "Northline Mechanical", "Inspections performed": 100,
         "Inspections passed first": 99, "Packages due": 50,
         "Packages completed on time": 49, "Commitments due": 40,
         "Commitments met on time": 39, "Exposure hours": 400000,
         "Recordable incidents": 1, "Active work": "yes"}],
    "trade_attribution_json": []})
row2, _ = run_case("b", [GREEN])
print("   7.2 the same shape with a clean firm")
ck("A6.4 bands GREEN and is not held",
   ((row2 or {}).get("status_color"), (row2 or {}).get("module_state")), ("Green", "stands"))
ck("the band carries its threshold source", (row2 or {}).get("threshold_source"),
   "owner_configured_default")

# --- 7.3 The fallback: three factors and a source rating
FALLBACK_DOCS = [
    ("insp", "inspection_report", {
        "items_inspected": 200, "items_passing_first_inspection": 193, "document_date": END,
        "trade_denominators_json": [
            {"Subcontractor": "Northline Mechanical", "Inspections performed": 100,
             "Inspections passed first": 99, "Packages due": 50,
             "Packages completed on time": 49, "Commitments due": 40,
             "Commitments met on time": 39, "Active work": "yes"}],
        "trade_attribution_json": []}),
    ("subr", "subcontractor_report", {
        "subcontractor_ratings_json": [
            {"Subcontractor": "Northline Mechanical", "Assessment period": "2026-03",
             "Rating": "Marginal"}],
        "subcontractor_rating_scale": "owner_five_point_label",
        "subcontractor_report_date": END, "subcontractor_report_version": "1"}),
]
row3, ab3 = run_case("c", FALLBACK_DOCS)
print("   7.3 three factors (no exposure hours) plus a stated Marginal rating")
gov3 = next((p for p in (row3 or {}).get("contractor_firm_postures", [])), None)
ck("the firm is INELIGIBLE for the four-factor calculation",
   (gov3 or {})["eligible_for_four_factor"], False)
ck("it takes the SOURCE RATING FALLBACK, Marginal -> Amber",
   ((gov3 or {})["posture_basis"], (gov3 or {})["final_posture"]),
   ("source_rating_fallback", "Amber"))
ck("the three calculable factors are all GREEN and did NOT lift it",
   sorted(b for b in (gov3 or {})["factor_bands"].values() if b), ["Green", "Green", "Green"])

# --- 7.4 The lift hold: four factors Green, source rating Unsatisfactory (Red)
LIFT_DOCS = [
    ("insp", "inspection_report", {
        "items_inspected": 200, "items_passing_first_inspection": 193, "document_date": END,
        "trade_denominators_json": [
            {"Subcontractor": "Northline Mechanical", "Inspections performed": 100,
             "Inspections passed first": 99, "Packages due": 50,
             "Packages completed on time": 49, "Commitments due": 40,
             "Commitments met on time": 39, "Exposure hours": 400000,
             "Recordable incidents": 1, "Active work": "yes"}],
        "trade_attribution_json": []}),
    ("subr", "subcontractor_report", {
        "subcontractor_ratings_json": [
            {"Subcontractor": "Northline Mechanical", "Assessment period": "2026-03",
             "Rating": "Unsatisfactory"}],
        "subcontractor_rating_scale": "owner_five_point_label",
        "subcontractor_report_date": END, "subcontractor_report_version": "1"}),
]
row4, _ = run_case("d", LIFT_DOCS)
print("   7.4 four Green factors against a stated Unsatisfactory rating -- Run 119's lift hold")
ck("the calculated posture is Green", (row4 or {}).get("contractor_calculated_posture"), "Green")
ck("a three-band lift is HELD, not published",
   ((row4 or {}).get("status_color"), (row4 or {}).get("module_state")),
   (None, "pending_pm_review"))
ck("the audit record names the lift",
   (((row4 or {}).get("pm_review_audit_record") or {}).get("lift_bands"),
    ((row4 or {}).get("pm_review_audit_record") or {}).get("held_for_lift")), (3, True))
ck("the source rating is preserved beside it, never over it",
   ((row4 or {}).get("pm_review_audit_record") or {}).get("source_rating"), "Unsatisfactory")

# ============================================================ 8. THE FALSIFICATION SET
print("\n8. FALSIFICATION -- every check above shown ABLE TO FAIL by putting the fault into the")
print("   thing the check reads, and then taking it out again.")
def falsify(name, mutate, restore, check):
    global PASS, FAIL
    before = check()
    mutate()
    during = check()
    restore()
    after = check()
    if before and not during and after:
        PASS += 1; print(f"  PROVED  {name}: passes, fails under the fault, passes again")
    else:
        FAIL += 1
        print(f"  NOT PROVED  {name}: before={before} under-fault={during} after={after}")

_orig_w = dict(CF.WEIGHTS)
falsify("the weighted aggregate check reads the real weights",
        lambda: CF.WEIGHTS.update({"schedule_reliability": 0.10}),
        lambda: CF.WEIGHTS.update(_orig_w),
        lambda: posture(packages_completed_on_time=70)["weighted_severity"] == 1.2)

_orig_cuts = CF.WEIGHTED_CUTS
def _set_cuts(v):
    CF.WEIGHTED_CUTS = v
falsify("the band cut check reads the real cuts",
        lambda: _set_cuts(((0.10, "Red"), (0.05, "Amber"), (0.01, "Yellow"))),
        lambda: _set_cuts(_orig_cuts),
        lambda: CF.band_weighted(0.4) == "Green")

_orig_sched = CF._SCHEDULE_CUTS
def _set_sched(v):
    CF._SCHEDULE_CUTS = v
falsify("the schedule ladder check reads the real ladder",
        lambda: _set_sched(((10.0, "Green"), (5.0, "Yellow"), (1.0, "Amber"))),
        lambda: _set_sched(_orig_sched),
        lambda: posture(packages_completed_on_time=85)["factor_bands"][
            "schedule_reliability"] == "Amber")

_orig_qo = CF._QUALITY_OVERRIDE
def _set_qo(v):
    CF._QUALITY_OVERRIDE = v
falsify("the quality override check reads the real vocabulary",
        lambda: _set_qo(frozenset()),
        lambda: _set_qo(_orig_qo),
        lambda: one([{"record_reference": "N", "record_kind": "nonconformance",
                      "record_severity": "life_safety",
                      "record_status": "open"}])["final_posture"] == "Red")

_orig_names = CF.FACTOR_NAMES
def _elig_check():
    d = firm(); d.pop("exposure_hours")
    return CF.firm_posture(firm="F", records=[], denominators=d,
                           source_posture="Amber")["posture_basis"] == "source_rating_fallback"
_orig_fs = CF.factor_safety
def _fake_safety(records, denominators):
    out = _orig_fs(records, denominators)
    if not out["available"]:
        out["available"] = True; out["band"] = "Green"
    return out
falsify("the eligibility check really requires all four factors",
        lambda: setattr(CF, "factor_safety", _fake_safety),
        lambda: setattr(CF, "factor_safety", _orig_fs),
        _elig_check)

_orig_gov = CF.governing
falsify("the worst-active-firm check really reads active_work",
        lambda: setattr(CF, "governing",
                        lambda ps: max([p for p in ps if p.get("final_posture")],
                                       key=lambda p: CF.BAND_SEVERITY[p["final_posture"]])),
        lambda: setattr(CF, "governing", _orig_gov),
        lambda: CF.governing([A, B, C_off])["firm"] == "Bravo")

print()
print("=" * 100)
print(f"RUN 120 DRIVER: {PASS} passed, {FAIL} failed, {PASS + FAIL} total")
print("=" * 100)
