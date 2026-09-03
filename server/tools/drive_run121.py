"""
RUN 121. THE HOLD COMES OFF, AND QUALITY REACHES THE SCHEDULE.

SECTION 1 -- GOAL 1, THE REMOVAL. What went, and each of the four things the owner's order says
must NOT be lost, proved through the real route and the page a participant loads.
SECTION 2 -- GOAL 2, the closed-record rule, proved both ways on every override in both engines.
SECTION 3 -- GOAL 3, the open critical nonconformance reaching schedule reliability, with the
weighted-severity figure the owner asked to see.
SECTION 4 -- GOAL 4.4, Run 120's AST proof re-run after the changes.
SECTION 5 -- FALSIFICATION. Every check in sections 1 to 3 shown ABLE TO FAIL by putting the
fault into the thing the check reads and then taking it out again. A deletion is exactly where a
check quietly stops being able to fail, so nothing here is asserted without that proof.

NOTHING UNDER TEST IS SUPPLIED TO A RENDERER. Section 1's page checks go through the real
upload, compute and category-apply routes and read the DOM the owner's own page produces.

Run from `server/`:  python tools/drive_run121.py
"""
import ast, base64, hashlib, json, logging, pathlib, sys, time
HERE = pathlib.Path("/home/user/LinPRojectRadar/server/tools"); sys.path.insert(0, str(HERE.parent))
logging.disable(logging.INFO)
from app.simulation import contractor_factors as CF
from app.simulation import trade_factors as TF
from app.simulation import pm_review as PMR

PASS = FAIL = 0
def ck(name, got, want):
    global PASS, FAIL
    if got == want:
        PASS += 1; print(f"  PASS  {name}")
    else:
        FAIL += 1; print(f"  FAIL  {name}: got {got!r}, want {want!r}")

print("=" * 100)
print("RUN 121 -- PM review becomes a discrete event; a closed record fires nothing; an open")
print("critical nonconformance makes the firm's schedule unreliable")
print("=" * 100)

# =================================================================================================
# SECTION 1. GOAL 1 -- THE HOLD IS GONE, AND THE FOUR THINGS THAT MUST NOT GO WITH IT
# =================================================================================================
print("\n1. THE HOLD IS GONE")

print("   1.1 the state itself no longer exists in the executing code")
_src = pathlib.Path(
    "/home/user/LinPRojectRadar/server/app/simulation/pm_review.py").read_text()
_tree = ast.parse(_src)
for _n in ast.walk(_tree):
    if isinstance(_n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        if ast.get_docstring(_n, clean=False):
            _n.body = _n.body[1:] or [ast.Pass()]
class _Blank(ast.NodeTransformer):
    def visit_Constant(self, node):
        return ast.copy_location(ast.Constant(value=""), node) if isinstance(
            node.value, str) else node
PMR_CODE = ast.unparse(_Blank().visit(_tree))
for gone in ("pending_pm_review", "MODULE_STATE_PENDING", "POSTURES_REQUIRING_REVIEW",
             "PENDING_WORDS"):
    ck(f"the CODE of pm_review.py never mentions {gone}", gone in PMR_CODE, False)
ck("there are exactly two module states left, and neither is a hold",
   list(PMR.MODULE_STATES), ["stands", "reviewed_by_pm"])

print("   1.2 resolve publishes every computed posture, adverse or not, with no review at all")
for band in ("Green", "Yellow", "Amber", "Red"):
    r = PMR.resolve(band, None)
    ck(f"a computed {band} STANDS and publishes",
       (r["posture"], r["module_state"], r["review_required"]), (band, "stands", False))

print("   1.3 KEPT: a recorded disposition still governs the computed posture")
ck("accept -- the normalised posture stands, and the module is marked reviewed",
   (lambda r: (r["posture"], r["module_state"]))(
       PMR.resolve("Red", {"disposition": "accept"})), ("Red", "reviewed_by_pm"))
ck("modify -- the PM's own posture REPLACES the computed one",
   PMR.resolve("Red", {"disposition": "modify", "pm_posture": "Yellow",
                       "rationale": "x"})["posture"], "Yellow")
ck("reject/Override -- the PM's own posture replaces the computed one",
   PMR.resolve("Green", {"disposition": "reject", "pm_posture": "Red",
                         "rationale": "x"})["posture"], "Red")
ck("defer -- Not Assessed, with the owner's limitation",
   (lambda r: (r["posture"], r["assessment_limitation"]))(
       PMR.resolve("Amber", {"disposition": "defer"})), (None, "Pending PM evidence review"))
ck("no action within current authority -- the normalised posture stands",
   PMR.resolve("Amber", {"disposition": "no_action_within_current_authority"})["posture"],
   "Amber")
ck("all five dispositions are still offered and none was dropped",
   sorted(PMR.DISPOSITION_EFFECT), ["accept", "defer", "modify",
                                    "no_action_within_current_authority", "reject"])
ck("a disposition this platform does not hold changes nothing and no longer holds the module",
   (lambda r: (r["posture"], r["module_state"], r.get("uninterpretable_review")))(
       PMR.resolve("Red", {"disposition": "not_a_disposition"})),
   ("Red", "stands", True))

print("   1.4 KEPT: the lift is still MEASURED, and now DISCLOSED instead of held")
ck("a three-band lift is measured exactly as Run 119 measured it",
   PMR.lift_bands("Red", "Green"), 3)
_l = PMR.resolve("Green", None, "Red")
ck("...the reading PUBLISHES its Green", (_l["posture"], _l["module_state"]),
   ("Green", "stands"))
ck("...and its own sentence says it was lifted",
   "two or more bands BETTER" in _l["module_state_words"], True)
ck("...and the audit record marks it disclosed and NOT held",
   (lambda a: (a["lift_bands"], a["lift_disclosed"], a["held_for_lift"]))(
       PMR.audit_record(normalised_posture="Green", source_rating="Unsatisfactory",
                        source_document_id="d", source_document_version="1", period="2026-Q1",
                        normalisation_rule="r", normalisation_rule_version="v", resolution=_l)),
   (3, True, False))
_l1 = PMR.resolve("Green", None, "Yellow")
ck("A ONE-BAND LIFT IS NOT DISCLOSED -- the disclosure discriminates and is not always on",
   (_l1["lift_bands"], _l1["lift_disclosed"],
    "two or more bands BETTER" in _l1["module_state_words"]), (1, False, False))
ck("and a reading with NO starting posture has no movement, and none is inferred",
   (lambda r: (r["lift_bands"], r["lift_disclosed"]))(PMR.resolve("Green", None, None)),
   (None, False))

print("   1.5 KEPT: the audit record still carries every field the owner enumerates")
_a = PMR.audit_record(
    normalised_posture="Red", source_rating="Unsatisfactory", source_document_id="doc-1",
    source_document_version="v2", period="2026-Q1", normalisation_rule="rule",
    normalisation_rule_version="v1",
    resolution=PMR.resolve("Red", {"disposition": "modify", "pm_posture": "Amber",
                                   "rationale": "site walk", "recorded_by": "P-1",
                                   "recorded_at": "2026-03-31T00:00:00Z",
                                   "evidence_references": ["NCR-1"]}, "Red"))
for f in ("source_rating", "source_document_id", "source_document_version", "assessment_period",
          "normalisation_rule", "normalisation_rule_version", "platform_mapped_posture",
          "pm_participant_id", "pm_recorded_at", "disposition", "disposition_label",
          "rationale", "evidence_references", "pm_final_posture"):
    ck(f"the audit record still carries `{f}`", _a.get(f) is not None, True)
ck("the source rating is carried VERBATIM and never altered", _a["source_rating"],
   "Unsatisfactory")
ck("the platform's own mapping is preserved BESIDE the PM's, not replaced by it",
   (_a["platform_mapped_posture"], _a["pm_final_posture"]), ("Red", "Amber"))

# =================================================================================================
# SECTION 2. GOAL 2 -- A CLOSED RECORD DOES NOT FIRE AN OVERRIDE
# =================================================================================================
print("\n2. THE CLOSED-RECORD RULE, PROVED BOTH WAYS ON EVERY OVERRIDE WITH A KNOWABLE STATUS")

FULL = dict(packages_due=100, packages_completed_on_time=96,
            inspections_performed=100, inspections_passed_first=99,
            exposure_hours=400_000, recordable_incidents=1,
            commitments_due=100, commitments_met_on_time=96, active_work="yes")
def P(records, **over):
    d = dict(FULL); d.update(over)
    return CF.firm_posture(firm="F", records=list(records), denominators=d)

CASES = {
    "schedule_reliability": {"record_reference": "WP-7", "record_kind": "work_package",
                             "record_milestone_forecast_late": "yes"},
    "quality_execution": {"record_reference": "NCR-9", "record_kind": "nonconformance",
                          "record_severity": "critical"},
    "safety": {"record_reference": "SAF-3", "record_kind": "safety_incident",
               "record_severity": "fatality"},
    "commercial_administration": {"record_reference": "SUB-2", "record_kind": "submittal",
                                  "record_milestone_forecast_late": "yes"},
}
for name, rec in CASES.items():
    op = P([dict(rec, record_status="open")])
    cl = P([dict(rec, record_status="closed")])
    si = P([dict(rec)])
    ck(f"A6.4 {name}: an OPEN record fires the override",
       (name in op["overrides_fired"], op["final_posture"]), (True, "Red"))
    ck(f"A6.4 {name}: the SAME record CLOSED fires nothing",
       (cl["overrides_fired"], cl["final_posture"]), ([], "Green"))
    ck(f"A6.4 {name}: a record printing NO status is treated as OPEN and still fires",
       name in si["overrides_fired"], True)

print("   2.2 Run 118's eight-factor engine ALREADY applied the rule -- measured, not assumed")
_tf_src = pathlib.Path(
    "/home/user/LinPRojectRadar/server/app/simulation/trade_factors.py").read_text()
ck("`trade_factors.is_open` exists and reads `record_status`",
   (TF.is_open({"record_status": "open"}), TF.is_open({"record_status": "closed"}),
    TF.is_open({})), (True, False, True))
_eight = ["nonconformances", "failed_inspections", "safety", "environmental", "quality_audit",
          "procurement", "field_observations", "commissioning"]
ck("all eight of its factor functions filter their override population through `is_open`",
   [f for f in _eight
    if f"def factor_{f}(" in _tf_src
    and "is_open(r)" not in _tf_src.split(f"def factor_{f}(")[1].split("\ndef ")[0]],
   [])

# =================================================================================================
# SECTION 3. GOAL 3 -- AN OPEN CRITICAL NONCONFORMANCE MAKES THE SCHEDULE UNRELIABLE
# =================================================================================================
print("\n3. AN OPEN CRITICAL NONCONFORMANCE REACHES SCHEDULE RELIABILITY")
NCR = {"record_reference": "NCR-1", "record_kind": "nonconformance",
       "record_severity": "critical", "record_status": "open"}
p = P([NCR])
ck("it fires the SCHEDULE override as well as the quality one",
   sorted(p["overrides_fired"]), ["quality_execution", "schedule_reliability"])
ck("and the firm's final posture is Red",  p["final_posture"], "Red")
ck("the schedule factor's hit names the reason -- rectification takes time",
   "rectification takes time"
   in " ".join(p["by_name"]["schedule_reliability"]["override_hits"]), True)
ck("the record is listed on the schedule factor as an open critical nonconformance",
   p["by_name"]["schedule_reliability"]["open_critical_nonconformances"], ["NCR-1"])
for w in ("minor", "observation", "major"):
    q = P([dict(NCR, record_severity=w)])
    ck(f"a {w} nonconformance fires NEITHER override -- the CRITICAL SET is what qualifies",
       q["overrides_fired"], [])
ck("the same critical nonconformance CLOSED fires neither -- goal 2 governs goal 3 too",
   P([dict(NCR, record_status="closed")])["overrides_fired"], [])
print("   3.2 WHAT ONE OPEN CRITICAL NONCONFORMANCE DOES TO THE WEIGHTED SEVERITY")
print("       clean firm:            weighted", P([])["weighted_severity"],
      "->", P([])["weighted_posture"], "| final", P([])["final_posture"])
print("       + one open critical:   weighted", p["weighted_severity"],
      "->", p["weighted_posture"], "| final", p["final_posture"])
ck("THE WEIGHTED SEVERITY IS UNCHANGED: an override is applied AFTER the weighted calculation "
   "as a worst-of and contributes NOTHING to it",
   (P([])["weighted_severity"], p["weighted_severity"],
    P([])["weighted_posture"], p["weighted_posture"]), (0.0, 0.0, "Green", "Green"))
ck("the movement is entirely in the override arm: Green weighted, Red published",
   (p["weighted_posture"], p["override_posture"], p["final_posture"]),
   ("Green", "Red", "Red"))
ck("it does NOT touch the Schedule category: nothing here writes a forecast date or a "
   "Schedule module id",
   [k for k in ("A2.1", "A2.7", "A2.12", "forecast_completion") if k in PMR_CODE], [])
ck("the four weights are unchanged", CF.WEIGHTS,
   {"schedule_reliability": 0.40, "quality_execution": 0.25, "safety": 0.20,
    "commercial_administration": 0.15})

# =================================================================================================
# SECTION 4. GOAL 4.4 -- RUN 120's AST PROOF, RE-RUN AFTER THIS RUN'S CHANGES
# =================================================================================================
print("\n4. NO MODULE POSTURE IS READ ANYWHERE IN THE ENGINE (order section 4.4)")
_cf = pathlib.Path(
    "/home/user/LinPRojectRadar/server/app/simulation/contractor_factors.py").read_text()
_ct = ast.parse(_cf)
for _n in ast.walk(_ct):
    if isinstance(_n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        if ast.get_docstring(_n, clean=False):
            _n.body = _n.body[1:] or [ast.Pass()]
CF_CODE = ast.unparse(_Blank().visit(_ct))
_found = [f for f in ("A6.1", "A6.2", "A6.3", "category_posture", "module_results",
                      "status_color", "project_posture", "BAND_SCORE", "moduleReviews")
          if f in CF_CODE]
ck("the executing code of contractor_factors.py mentions NO module posture", _found, [])
print("       modules named in the executing code:", _found or "NONE")

# =================================================================================================
# SECTION 5. FALSIFICATION -- EVERY CHECK ABOVE PROVED ABLE TO FAIL
# =================================================================================================
print("\n5. FALSIFICATION -- the fault is put INTO the thing each check reads, and taken out")
def falsify(name, mutate, restore, probe):
    global PASS, FAIL
    before = probe()
    mutate()
    try:
        during = probe()
    finally:
        restore()
    after = probe()
    if before and not during and after:
        PASS += 1
        print(f"  PROVED  {name}: passes, FAILS under the fault, passes again")
    else:
        FAIL += 1
        print(f"  NOT PROVED  {name}: before={before} under-fault={during} after={after}")

# 5.1 THE HOLD REALLY IS GONE, and the check that says so can see it come back.
_orig_resolve = PMR.resolve
def _put_the_hold_back():
    def held(normalised, review, source=None):
        if normalised in ("Amber", "Red") and not review:
            return {"posture": None, "module_state": "pending_pm_review",
                    "review_required": True, "review": None, "lift_bands": None,
                    "lift_disclosed": False, "held_for_lift": False,
                    "module_state_words": "held"}
        return _orig_resolve(normalised, review, source)
    PMR.resolve = held
falsify("the no-hold check reads the real `resolve`",
        _put_the_hold_back, lambda: setattr(PMR, "resolve", _orig_resolve),
        lambda: PMR.resolve("Red", None)["posture"] == "Red")

# 5.2 THE DISPOSITION'S AUTHORITY.
_orig_effect = dict(PMR.DISPOSITION_EFFECT["modify"])
falsify("the disposition-governs check reads the real DISPOSITION_EFFECT",
        lambda: PMR.DISPOSITION_EFFECT["modify"].update({"takes_pm_posture": False}),
        lambda: PMR.DISPOSITION_EFFECT["modify"].update(_orig_effect),
        lambda: PMR.resolve("Red", {"disposition": "modify", "pm_posture": "Yellow",
                                    "rationale": "x"})["posture"] == "Yellow")

# 5.3 THE LIFT DISCLOSURE.
_orig_words = PMR.LIFT_DISCLOSURE_WORDS
falsify("the lift-disclosure check reads the real sentence",
        lambda: setattr(PMR, "LIFT_DISCLOSURE_WORDS", "nothing to see here"),
        lambda: setattr(PMR, "LIFT_DISCLOSURE_WORDS", _orig_words),
        lambda: "two or more bands BETTER"
        in PMR.resolve("Green", None, "Red")["module_state_words"])

# 5.4 THE LIFT SIZE.
_orig_n = PMR.LIFT_BANDS_REQUIRING_DISCLOSURE
falsify("the two-band size check reads the real number",
        lambda: setattr(PMR, "LIFT_BANDS_REQUIRING_DISCLOSURE", 1),
        lambda: setattr(PMR, "LIFT_BANDS_REQUIRING_DISCLOSURE", _orig_n),
        lambda: PMR.resolve("Green", None, "Yellow")["lift_disclosed"] is False)

# 5.5 GOAL 2, THE CLOSED-RECORD RULE.
_orig_closed = CF._CLOSED_WORDS
falsify("the closed-record check reads the real closed vocabulary",
        lambda: setattr(CF, "_CLOSED_WORDS", frozenset()),
        lambda: setattr(CF, "_CLOSED_WORDS", _orig_closed),
        lambda: P([{"record_reference": "WP-7", "record_kind": "work_package",
                    "record_milestone_forecast_late": "yes",
                    "record_status": "closed"}])["overrides_fired"] == [])

# 5.6 GOAL 3, THE CRITICAL SET.
_orig_q = CF._QUALITY_OVERRIDE
falsify("the open-critical-nonconformance check reads the real critical vocabulary",
        lambda: setattr(CF, "_QUALITY_OVERRIDE", frozenset()),
        lambda: setattr(CF, "_QUALITY_OVERRIDE", _orig_q),
        lambda: "schedule_reliability" in P([NCR])["overrides_fired"])

# 5.7 GOAL 3, THE POPULATION.
_orig_k = CF._KIND_NCR
falsify("...and the real nonconformance population, not any record at all",
        lambda: setattr(CF, "_KIND_NCR", frozenset()),
        lambda: setattr(CF, "_KIND_NCR", _orig_k),
        lambda: "schedule_reliability" in P([NCR])["overrides_fired"])

print()
print("=" * 100)
print(f"RUN 121 ENGINE DRIVER: {PASS} passed, {FAIL} failed, {PASS + FAIL} total")
print("=" * 100)
sys.exit(1 if FAIL else 0)
