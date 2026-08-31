#!/usr/bin/env python3
"""
Run 89, goal three: THE REQUIRED CORE, AND INDETERMINATE.

What is proved, by measurement:

  (1) WORST-WINS IS UNCHANGED where all five required categories are assessed. The published
      status is measured against `fusion.worst_band` computed independently over the same
      contributing categories -- the arithmetic, not a restatement of it -- and they are equal
      for every band and for a Red/Amber/Green mix.
  (2) INDETERMINATE is issued, on both status paths, exactly when a required category carries
      no posture, and the fused band is still recorded beside it rather than discarded.
  (3) THERE IS NO SUPPORTING TIER ANY MORE, and its absence is asserted rather than assumed.
      RUN 95 SECTION 3.2 SUPERSEDED RUN 89 HERE: the required core is all five weighted
      performance categories, A4 Document Signals moved from supporting to required, and A5
      Systems and Dynamics holds no module in service and is not a category of this platform.
      What Run 89 checked -- that A4 and A5 absent still leaves an official status -- is now
      FALSE BY THE OWNER'S RULING, so it is not asserted; the check is REPLACED by the fact
      that took its place, which is that A4 absent BLOCKS, and by the check that a missing
      category still never becomes a Green. That last half is the part that mattered and it
      is kept intact.
  (4) INDETERMINATE IS NOT A BAND. It is not in `BAND_SEVERITY` and `worst_band` never returns
      it and never ranks it.
  (5) THE CHECK CAN FAIL. The required set is neutralised to empty and the same row then
      publishes the fused band as official -- the state the gate exists to prevent.

Run (from server/):  python tools/test_run89_required_core.py
"""
from __future__ import annotations

import itertools
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from app import spec_projection as sp
from app.research_models import SpecificationReading
from app.simulation.fusion import BAND_SEVERITY, worst_band

FAILURES: list[str] = []


def check(label: str, got, want) -> None:
    ok = got == want
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: got {got!r}, want {want!r}")
    if not ok:
        FAILURES.append(label)


def _mod(mid: str, band: str | None) -> dict:
    return {"module_id": mid, "state": "computed", "band": band, "band_asserted": band is not None,
            "value": 1.0, "display": "1.0", "evidence_metric": "test", "reason": None}


def _reading(cat: str, mods: list[dict]) -> SpecificationReading:
    return SpecificationReading(
        reading_id=f"r89rc-{cat}", category_key=cat, state="computed", status=None,
        counts={"computed": len(mods)}, modules=mods, reason=None, missing_upstream=[],
        served_by="run89-test")


def _cats(**bands) -> dict:
    return sp.category_statuses({k: _reading(k, [_mod(f"{k}.1", v)]) for k, v in bands.items()})


print("1. WORST-WINS IS UNCHANGED WHEN ALL FIVE REQUIRED CATEGORIES ARE ASSESSED")
# THE POPULATION IS THE REQUIRED SET ITSELF, NOT A TYPED LIST OF NAMES. Run 89 wrote four names
# and `repeat=4`; Run 95 made the core five. Reading `sp.REQUIRED_CATEGORIES` here means the
# exhaustive sweep follows the architecture instead of restating it, and the count it prints is
# measured (4 bands ** 5 categories == 1024) rather than written down.
_REQ = list(sp.REQUIRED_CATEGORIES)
_n = 0
for combo in itertools.product(["Green", "Yellow", "Amber", "Red"], repeat=len(_REQ)):
    cats = _cats(**dict(zip(_REQ, combo)))
    # The arithmetic, computed here independently of the gate, exactly as it was before Run 89.
    independent = worst_band([c["status"] for c in cats.values()
                              if c["status"] and c["contributes_to_project_status"]])
    if sp.project_status(cats) != independent:
        FAILURES.append(f"arithmetic moved for {combo}")
        print(f"  [FAIL] {combo}: gate {sp.project_status(cats)!r} != worst_band {independent!r}")
    _n += 1
print(f"  [{'PASS' if not FAILURES else 'FAIL'}] all {_n} band combinations over the "
      f"{len(_REQ)} required categories publish exactly worst_band, unchanged")
check("the sweep was exhaustive over the required core, not a sample",
      _n, 4 ** len(sp.REQUIRED_CATEGORIES))
check("the required core is the owner's five, Run 95 section 3.2",
      list(sp.REQUIRED_CATEGORIES), ["A1", "A2", "A3", "A4", "A6"])

print("\n  ...and an adverse required category still wins:")
cats = _cats(A1="Green", A2="Green", A3="Green", A6="Green", A4="Red")
check("A4 is required now and its Red still enters worst-wins",
      sp.project_status(cats), "Red")
check("...and the status is OFFICIAL", sp.project_status_basis(cats)["official"], True)

print("\n2. INDETERMINATE WHEN A REQUIRED CATEGORY CARRIES NO POSTURE")
# A4 IS SUPPLIED HERE BECAUSE RUN 95 MADE IT REQUIRED. The fact under test is what happens when
# ONE required category is missing, so every other required category must carry a posture or the
# check would be measuring two absences at once.
cats = _cats(A1="Red", A2="Green", A3="Green", A4="Green")   # A6 never called
b = sp.project_status_basis(cats)
check("status", sp.project_status(cats), "Indeterminate")
check("official", b["official"], False)
check("which required category is missing", b["required_missing"], ["A6"])
check("its state is never_called (no reading stored at all)",
      b["required_missing_detail"][0]["state"], "never_called")
check("THE FUSED BAND IS STILL RECORDED, not discarded", b["fused_band"], "Red")
check("every assessed category is still visible with its posture",
      sorted((k, v["status"]) for k, v in cats.items() if v["status"]),
      [("A1", "Red"), ("A2", "Green"), ("A3", "Green"), ("A4", "Green")])

print("\n  ...and a required category CALLED but carrying no band is equally missing:")
cats2 = sp.category_statuses({
    "A1": _reading("A1", [_mod("A1.7", "Green")]), "A2": _reading("A2", [_mod("A2.7", "Green")]),
    "A3": _reading("A3", [_mod("A3.2", "Green")]),
    "A4": _reading("A4", [_mod("A4.2", "Green")]),   # required since Run 95; supplied so that
    "A6": _reading("A6", [_mod("A6.1", None)])})     # A6 is the only category missing a posture
b2 = sp.project_status_basis(cats2)
check("status", sp.project_status(cats2), "Indeterminate")
check("A6 is missing", b2["required_missing"], ["A6"])
check("its state is the reading's own state, NOT never_called",
      b2["required_missing_detail"][0]["state"], "computed")
check("A6 is NOT Green", cats2["A6"]["status"], None)

print("\n3. THERE IS NO SUPPORTING TIER, AND A MISSING CATEGORY NEVER BECOMES A GREEN")
cats = _cats(A1="Green", A2="Green", A3="Green", A6="Green")   # A4 never called
b = sp.project_status_basis(cats)
check("A4 absent DOES block the official status now -- Run 95 made it required",
      b["official"], False)
check("...and the status is Indeterminate, not the fused Green",
      sp.project_status(cats), "Indeterminate")
check("...while the fused Green is still recorded beside it", b["fused_band"], "Green")
check("the supporting tier is empty", list(sp.SUPPORTING_CATEGORIES), [])
check("so supporting_assessed publishes [] rather than vanishing",
      b["supporting_assessed"], [])
check("and supporting_not_assessed publishes [] too", b["supporting_not_assessed"], [])
check("A5 is in neither tier -- it is not a category of this platform",
      "A5" in sp.REQUIRED_CATEGORIES or "A5" in sp.SUPPORTING_CATEGORIES, False)
cats = _cats(A1="Green", A2="Green", A3="Green")               # A6 and A4 missing
check("no documents supplied does NOT produce a Green for a missing required category",
      sp.project_status(cats), "Indeterminate")

print("\n4. INDETERMINATE IS NOT A BAND")
check("not in BAND_SEVERITY", "Indeterminate" in BAND_SEVERITY, False)
check("worst_band cannot return it", worst_band(["Indeterminate"]), None)
check("worst_band ranks it nowhere against a real band",
      worst_band(["Indeterminate", "Green"]), "Green")

print("\n5. THE CHECK CAN FAIL -- THE REQUIRED SET NEUTRALISED")
_real = sp.REQUIRED_CATEGORIES
try:
    sp.REQUIRED_CATEGORIES = ()
    cats = _cats(A1="Red", A2="Green", A3="Green")     # A6 still missing
    check("NEUTRALISED: the gate no longer fires", sp.project_status(cats), "Red")
    check("NEUTRALISED: the row is declared official -- this is the defect",
          sp.project_status_basis(cats)["official"], True)
finally:
    sp.REQUIRED_CATEGORIES = _real
cats = _cats(A1="Red", A2="Green", A3="Green")
check("RESTORED: Indeterminate again", sp.project_status(cats), "Indeterminate")

print("\n" + ("ALL PASS" if not FAILURES else f"{len(FAILURES)} FAILURES: {FAILURES}"))
sys.exit(1 if FAILURES else 0)
