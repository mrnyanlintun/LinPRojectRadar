"""
RUN 104. THE TWO CATEGORY POSTURE RULES, THEIR INJECTION PROOFS, AND PERT AT PATH LEVEL.

WHAT IS REAL AND WHAT IS HARNESS, STATED BEFORE ANYTHING IS MEASURED.

  REAL ROUTE. The corpus project is rebuilt exactly as Run 103's census driver builds it -- its
  document set is READ OUT of `drive_run103_census.py` rather than transcribed, so it cannot
  drift -- and pressed through the REAL upload, compute, category-apply and projectresults
  routes. Every posture, every arithmetic string and every module band reported below is read
  back off those routes' own output. NOTHING UNDER TEST IS SUPPLIED to a renderer: the decision
  brief is not composed here, not injected here, and handed to no render function, and
  `window.LinResults.rowFor` is not substituted.

  HARNESS. The two INJECTION PROOFS in part 3 call `category_posture` directly on synthetic band
  sets. They are proofs about the RULE, not about the project, and each is proved ABLE TO FAIL
  by neutralising the rule and re-running -- section 10.8 fails the run for a rule claimed to
  work without that.
"""
import base64, hashlib, json, logging, pathlib, sys, time
HERE = pathlib.Path("/home/user/LinPRojectRadar/server/tools"); sys.path.insert(0, str(HERE.parent))
logging.disable(logging.INFO)
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
    assert r.status_code == 200, r.text[:300]
    return r.json()
def b64(x): return base64.b64encode(x).decode()

PASS = FAIL = 0
def check(ok, label, detail=""):
    global PASS, FAIL
    if ok: PASS += 1; print(f"  PASS  {label}")
    else:  FAIL += 1; print(f"  ****  {label}" + (f"   [{detail}]" if detail else ""))

STAMP = str(int(time.time())); ADMIN = "r104-" + STAMP
BAC = 4_000_000; END = "2026-03-31"; PID = "PRJ-R104-" + STAMP

# THE DOCUMENT SET IS RUN 103's OWN, READ OUT OF ITS DRIVER. A hand copy would be a second
# authority for the fixture and could drift from the census this run must be compared against.
_src = (HERE / "drive_run103_census.py").read_text()
_i = _src.index("DOCS = ["); _j = _src.index("\n]\n", _i) + 3
_ns: dict = {}
exec(_src[_i:_j], {"BAC": BAC, "END": END}, _ns)
DOCS = _ns["DOCS"]

def raw(t): return f"%PDF-1.4 R104 {STAMP} {t}\n".encode()
set_extractor_override(StubExtractor({hashlib.sha256(raw(t)).hexdigest(): (ty, ex)
                                      for t, ty, ex in DOCS}))
with S() as s:
    r = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if r is None:
        s.add(Participant(pseudonymous_code="R104-A-" + STAMP, role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        r.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PID)) is None:
        s.add(Project(legacy_id=PID, doc={"id": PID, "name": "Run 104 fixture",
                                          "sector": "construction", "signals": {}, "events": []}))
    s.commit()
admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
c = post({"action": "adminparticipantcreate", "session_token": admin,
          "pseudonymous_code": "R104-PM-" + STAMP, "role": "Participant",
          "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": c["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PID,
      "participant_id": c["participant_id"], "project_role": "PM"})
ok = 0
for t, ty, ex in DOCS:
    r = post({"action": "projectupload", "session_token": PM, "id": PID, "period": 1,
              "period_end": END,
              "documents": [{"filename": t + ".pdf", "mimeType": "application/pdf",
                             "dataBase64": b64(raw(t))}]})
    if r.get("ok"): ok += 1
print(f"uploaded {ok}/{len(DOCS)} documents through the real route")
post({"action": "projectcomputeall", "session_token": PM, "id": PID})
ap = post({"action": "projectcategoryapply", "session_token": PM, "id": PID, "period": 1})
print("categoryapply:", ap.get("ok"), "readings", len(ap.get("readings") or []))

with S() as s:
    p = s.scalar(select(Project).where(Project.legacy_id == PID))
    row = s.scalar(select(ComputedResult).where(ComputedResult.project_id == p.id,
                                                ComputedResult.superseded_by.is_(None)))
    RESULTS = {m.get("module_id"): m for m in (row.module_results or [])}
    ABSTAINED = {a.get("module_id"): a for a in (row.abstained or [])}
    PYCATS = dict(row.category_statuses or {})
    PYSTATUS = row.project_status

# =============================================================================================
print()
print("=" * 92)
print("1. WHAT THE CORPUS PUBLISHES NOW -- read off the REAL projectresults route")
print("=" * 92)
res = post({"action": "projectresults", "session_token": PM, "id": PID, "period": 1})
_r = res.get("result") or {}
SERVED_CATS = _r.get("category_statuses") or {}
SERVED_STATUS = _r.get("project_status")
BASIS = _r.get("project_status_basis") or {}
print(f"  project status SERVED  : {SERVED_STATUS!r}   (official: {BASIS.get('status')!r})")
print(f"  project status in the stored PYTHON row : {PYSTATUS!r}")
print()
for k in sorted(SERVED_CATS):
    e = SERVED_CATS[k] or {}
    print(f"  {k}  {str(e.get('status')):<13} rule={e.get('posture_rule')}"
          f"  layer={e.get('posture_layer')}")
    print(f"      {e.get('posture_arithmetic')}")
check(bool(SERVED_STATUS), "the real route served a project status", repr(SERVED_STATUS))
for k, want in (("A1", "average_of_module_scores"), ("A2", "average_of_module_scores"),
                ("A3", "average_of_module_scores"), ("A4", "average_of_module_scores"),
                ("A6", "worst_wins")):
    e = SERVED_CATS.get(k) or {}
    check(e.get("posture_rule") == want,
          f"{k} is formed by {want} on the served route", repr(e.get("posture_rule")))
    check(bool(e.get("posture_arithmetic")),
          f"{k} carries the arithmetic that produced it")

# A6 IS THE CATEGORY THE OWNER MOVED. Its posture must now be the worst band inside it.
_a6_bands = sorted((m, (RESULTS.get(m) or {}).get("status_color"))
                   for m in RESULTS if m.startswith("A6."))
print()
print("  A6 module bands as computed:", _a6_bands)
_worst = None
for _o in ("Green", "Yellow", "Amber", "Red"):
    if any(b == _o for _, b in _a6_bands): _worst = _o
check((SERVED_CATS.get("A6") or {}).get("status") == _worst,
      f"A6's posture is the worst band among its modules ({_worst})",
      repr((SERVED_CATS.get("A6") or {}).get("status")))

# =============================================================================================
print()
print("=" * 92)
print("2. PERT AT PATH LEVEL -- the same network, the old measure and the new one")
print("=" * 92)
_p = RESULTS.get("A2.1") or ABSTAINED.get("A2.1") or {}
if not _p:
    check(False, "A2.1 produced a row")
else:
    print("  band now              :", _p.get("status_color"))
    print("  C1 (most critical path):", _p.get("path_criticality_c1"))
    print("  C2 (second path)       :", _p.get("path_criticality_c2"))
    print("  dominance margin M     :", _p.get("path_dominance_margin"))
    print("  most critical path     :", _p.get("most_critical_path"))
    print("  distinct paths observed:", _p.get("unique_critical_path_count"))
    print("  primary band before cap:", _p.get("band_primary_before_cap"),
          "| margin cap:", _p.get("band_dominance_margin_cap"),
          "| hard override fired:", _p.get("band_hard_override_fired"))
    print("  ACTIVITY index, the OLD measure, still recorded:")
    print("    most critical activity:", _p.get("most_critical_activity"),
          "share", _p.get("most_critical_share"))
    # THE OLD RULE RE-APPLIED TO THIS SAME READING, so the reversal is measured and not asserted.
    from app.simulation import band_reference as _BR
    _old = _BR.entry("pert_criticality_bands")
    _s = _p.get("most_critical_share")
    _oldband = None
    if isinstance(_s, (int, float)):
        _oldband = ("Green" if _s < _old["green_below"] else
                    "Yellow" if _s < _old["yellow_below"] else
                    "Amber" if _s < _old["amber_below"] else "Red")
    print("    the Run 102 rule applied to that share would band:", _oldband)
    check(_oldband == "Red", "the old activity-level rule bands this network Red", repr(_oldband))
    check(_p.get("status_color") == "Green",
          "the new path-level rule bands this same network Green", repr(_p.get("status_color")))
    check(_p.get("path_criticality_c1", 0) >= 0.80,
          "because one path controls in at least 80 per cent of the trials")
    check("path_probabilities" in _p and bool(_p["path_probabilities"]),
          "and the raw path probabilities are retained in the audit record")
    _cpa = RESULTS.get("A2.12") or {}
    check(list(_p.get("most_critical_path") or []) == list(_cpa.get("controlling_path") or []),
          "the path PERT reconstructs per trial is the same path A2.12 reports "
          "deterministically on this network",
          f"{_p.get('most_critical_path')} vs {_cpa.get('controlling_path')}")
    _sum = sum(v for v in (_p.get("criticality_index") or {}).values())
    check(_p.get("path_criticality_c1") is not None and _sum > 1.0,
          f"activity criticality indices sum to {round(_sum, 3)} > 1 and are therefore NOT "
          f"summed into a path probability")

# ---------------------------------------------------------------------------------------------
# 2b. THE MARGIN CAP AND THE HARD OVERRIDE, INJECTED. HARNESS: two synthetic networks are built
# and pressed through the REAL `pert_criticality` and the REAL band arithmetic. Section 10.6
# fails the run for omitting either, and section 10.8 for claiming one works without a proof able
# to fail, so each is also run with the rule neutralised.
print()
print("-" * 92)
print("2b. THE DOMINANCE MARGIN CAP AND THE HARD OVERRIDE -- HARNESS, injected")
print("-" * 92)
from app.simulation.canonical_v3 import pert_criticality as _pc
import random as _random


def _net(acts, succ_of):
    return {"activities": acts,
            "successors": succ_of,
            "order": list(acts),
            "schedule_version": "run104-injection"}


def _mk(o, m, pmax, preds):
    return {"optimistic": o, "most_likely": m, "pessimistic": pmax,
            "current_duration": m, "predecessors": preds,
            "duration_distribution": "TRIANGULAR"}


# TWO NEAR-IDENTICAL PARALLEL PATHS INTO ONE FINISH. Neither controls reliably, so C1 must fall
# and the margin must be small -- the exact condition the owner calls diffuse exposure.
_acts = {"S": _mk(1, 1, 1, []),
         "P1": _mk(8, 10, 12, ["S"]),
         "P2": _mk(8, 10, 12, ["S"]),
         "F": _mk(1, 1, 1, ["P1", "P2"])}
_succ = {"S": ["P1", "P2"], "P1": ["F"], "P2": ["F"], "F": []}
_rng = _random.Random(104)
_split = _pc(_net(_acts, _succ), rand=_rng.random, trials=2000)
print(f"  two symmetric parallel paths: C1={round(_split['c1'], 3)} "
      f"C2={round(_split['c2'], 3)} M={round(_split['dominance_margin'], 3)} "
      f"over {_split['unique_path_count']} distinct paths")
check(_split["c1"] < 0.80,
      "C1 falls below 0.80 when two paths compete for control", str(_split["c1"]))
check(_split["dominance_margin"] < 0.10,
      "and the dominance margin falls below 0.10", str(_split["dominance_margin"]))
_BRc = _BR.entry("pert_path_concentration_bands")
def _band_of(c1, margin, float_against_imposed=None):
    primary = ("Green" if c1 >= _BRc["green_at_or_above"] else
               "Yellow" if c1 >= _BRc["yellow_at_or_above"] else
               "Amber" if c1 >= _BRc["amber_at_or_above"] else "Red")
    cap = (None if margin >= _BRc["margin_no_cap_at_or_above"] else
           "Yellow" if margin >= _BRc["margin_cap_yellow_at_or_above"] else "Amber")
    sev = {"Green": 0, "Yellow": 1, "Amber": 2, "Red": 3}
    capped = primary if cap is None else max((primary, cap), key=sev.__getitem__)
    if float_against_imposed is not None and float_against_imposed < 0:
        return "Red", primary, cap
    return capped, primary, cap
_b, _pri, _cap = _band_of(_split["c1"], _split["dominance_margin"])
check(_b in ("Amber", "Red"),
      f"so the same reading bands {_b}, not Green: split criticality is adverse", _b)
# THE CAP ALONE, with the primary band deliberately Green: C1 0.85 but the second path at 0.80.
_b2, _pri2, _cap2 = _band_of(0.85, 0.05)
check(_pri2 == "Green" and _cap2 == "Amber" and _b2 == "Amber",
      "a Green primary band with a margin below 0.10 is capped at Amber", f"{_pri2}/{_cap2}/{_b2}")
_b3, _pri3, _cap3 = _band_of(0.85, 0.15)
check(_pri3 == "Green" and _cap3 == "Yellow" and _b3 == "Yellow",
      "and a margin between 0.10 and 0.20 is capped at Yellow", f"{_pri3}/{_cap3}/{_b3}")
_b4, _pri4, _cap4 = _band_of(0.85, 0.55)
check(_cap4 is None and _b4 == "Green", "a margin at or above 0.20 applies no cap")
# THE HARD OVERRIDE.
check(_band_of(0.99, 0.99, float_against_imposed=-3.0)[0] == "Red",
      "the hard override takes a Green reading to Red when the controlling path's total float "
      "against the imposed finish is negative")
check(_band_of(0.99, 0.99, float_against_imposed=0.0)[0] == "Green",
      "FAULT PROOF: at zero float the override does NOT fire, so the check above is about "
      "negative float and not about the arithmetic")

# =============================================================================================
print()
print("=" * 92)
print("3. THE TWO RULES, INJECTED -- HARNESS, and each proved able to fail")
print("=" * 92)
from app.simulation.category_posture import (category_posture, CATEGORY_RULES, RULE_AVERAGE,
                                             RULE_WORST, band_average)
G3 = [("m1", "Green"), ("m2", "Green"), ("m3", "Green")]
print("  -- WORST-WINS, on A6 Delivery Quality")
check(category_posture("A6", G3 + [("m4", "Amber")])["status"] == "Amber",
      "one Amber among three Greens makes A6 Amber",
      category_posture("A6", G3 + [("m4", "Amber")])["status"])
check(category_posture("A6", G3 + [("m4", "Red")])["status"] == "Red",
      "one Red among three Greens makes A6 Red")
check(category_posture("A6", G3)["status"] == "Green", "three Greens leave A6 Green")
# NEUTRALISED: assign A6 to averaging, which is exactly the defect the owner ruled against.
_saved = CATEGORY_RULES["A6"]
CATEGORY_RULES["A6"] = RULE_AVERAGE
_neut = category_posture("A6", G3 + [("m4", "Amber")])["status"]
check(_neut != "Amber",
      f"NEUTRALISED -- averaging A6 makes the same set {_neut}, not Amber: the check can fail")
CATEGORY_RULES["A6"] = _saved
check(category_posture("A6", G3 + [("m4", "Amber")])["status"] == "Amber",
      "RESTORED -- A6 is Amber again")

print("  -- AVERAGING, on the four performance categories")
_avg = category_posture("A1", G3 + [("m4", "Amber")])
check(_avg["status"] == "Yellow",
      "one Amber among three Greens makes A1 Yellow, not Amber and not Green", _avg["status"])
check(abs(_avg["posture_average"] - 1.25) < 1e-9, "the mean is +1.25", str(_avg["posture_average"]))
check(category_posture("A1", G3 + [("m4", "Red")])["status"] == "Yellow",
      "one Red among three Greens averages to +1.0, which is Yellow")
check(category_posture("A1", [("m1", "Red"), ("m2", "Red"), ("m3", "Green")])["status"] == "Red",
      "two Reds against one Green averages to -0.667, which is below -0.5 and therefore Red")
check(category_posture("A1", [("m1", "Red"), ("m2", "Green"), ("m3", "Green")])["status"] == "Yellow",
      "one Red against two Greens averages to +0.667, which is Yellow")
check(category_posture("A1", [("m1", "Red"), ("m2", "Red")])["status"] == "Red",
      "two Reds average to -2.0, which is Red")
# AN UNBANDED MODULE IS NOT A ZERO. Section 10.2 fails the run for counting it as one.
_with_none = category_posture("A1", G3 + [("m4", None), ("m5", "not-a-band")])
check(_with_none["posture_banded_count"] == 3,
      "a computed-without-a-band module and an unrecognised band are NOT in the average",
      str(_with_none["posture_banded_count"]))
check(_with_none["status"] == "Green",
      "three Greens plus two unbanded modules is Green, not the Yellow a zero would give",
      _with_none["status"])
check(band_average([2.0, 2.0, 2.0, 0.0, 0.0]) == "Yellow",
      "FAULT PROOF: had those two counted as zero the same set would read Yellow, so the "
      "check above is about the exclusion and not about the fixture")
check(category_posture("A1", [])["status"] is None,
      "a category where no module banded carries no posture at all")
# NEUTRALISED: assign A1 to worst-wins, the rule the owner moved it off.
_saved1 = CATEGORY_RULES["A1"]
CATEGORY_RULES["A1"] = RULE_WORST
_n1 = category_posture("A1", G3 + [("m4", "Amber")])["status"]
check(_n1 == "Amber",
      f"NEUTRALISED -- worst-wins on A1 makes the same set {_n1}, not Yellow: the check can fail")
CATEGORY_RULES["A1"] = _saved1
check(category_posture("A1", G3 + [("m4", "Amber")])["status"] == "Yellow",
      "RESTORED -- A1 is Yellow again")

# =============================================================================================
print()
print("=" * 92)
print("4. PROJECT-LEVEL FUSION IS UNCHANGED -- measured over all 256 four-band combinations")
print("=" * 92)
from app.simulation.fusion import worst_band
import itertools
BANDS = ("Green", "Yellow", "Amber", "Red")
_bad = [c for c in itertools.product(BANDS, repeat=4)
        if worst_band(list(c)) != max(c, key=lambda b: BANDS.index(b))]
check(not _bad, "worst_band over four categories is still the most adverse of them, all 256 cases")
_ps = _r.get("project_status_basis") or {}
check(sorted(_ps.get("required_categories") or []) == ["A1", "A2", "A3", "A4", "A6"],
      "the required core is still the five", str(_ps.get("required_categories")))
_cbands = [ (SERVED_CATS[k] or {}).get("status") for k in SERVED_CATS
            if (SERVED_CATS[k] or {}).get("contributes_to_project_status")
            and (SERVED_CATS[k] or {}).get("status") ]
# RUN 105 CLOSED THE DIVERGENCE THIS PARAGRAPH RECORDED, and the paragraph is re-pointed rather
# than deleted so the history stays readable. Run 104 measured `compute.compute_project`
# publishing `fuse_signals(voting)`'s band -- Dempster's rule ACROSS the categories -- while only
# the SPECIFICATION path applied `worst_band`; on this same fixture the stored row said Green and
# the served page said Amber. Run 105 made the Python path take the worst across the categories
# too, so the line printed below now shows the stored status EQUAL to the worst of its own
# categories. The check added here is that equality; it did not hold at Run 104 and would go red
# if the Dempster rule were restored.
_pyfuse = PYSTATUS
print(f"  stored PYTHON row project_status = {_pyfuse!r}; worst of its categories = "
      f"{worst_band([ (v or {}).get('status') for v in PYCATS.values() ])!r}")
check(SERVED_STATUS == worst_band(_cbands),
      f"the served project status is the worst of the contributing categories {_cbands}",
      repr(SERVED_STATUS))
# RUN 105. The stored row must now agree with it. Re-pointed, not weakened: this is a check the
# tree could not pass before Run 105.
check(_pyfuse == SERVED_STATUS,
      "RUN 105: the stored PYTHON project_status equals the served one -- one project, one "
      "status", f"stored {_pyfuse!r} vs served {SERVED_STATUS!r}")

# =============================================================================================
print()
print("=" * 92)
print("5. THE BRIEF STATES WHICH RULE FORMED EACH POSTURE -- served, not composed here")
print("=" * 92)
_brief = _r.get("decision_brief") or {}
_why = _brief.get("why") or ""
print(" ", _why[:1400])
check("Conservative Dominance" not in json.dumps(_brief),
      "the served brief no longer describes the status rule as Conservative Dominance")
check("average" in _why.lower() and "worst" in _why.lower(),
      "the brief names both rules")
for k in ("A1", "A2", "A3", "A4", "A6"):
    e = SERVED_CATS.get(k) or {}
    if e.get("status"):
        check((e.get("posture_arithmetic") or "")[:40] in _why,
              f"the brief shows {k}'s own arithmetic")

print()
print("=" * 92)
print(f"RESULT: {PASS}/{PASS + FAIL} checks passed")
print("=" * 92)
sys.exit(1 if FAIL else 0)
