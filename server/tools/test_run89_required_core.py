#!/usr/bin/env python3
"""
Run 89, goal three: THE REQUIRED CORE, AND INDETERMINATE.

What is proved, by measurement:

  (1) WORST-WINS IS UNCHANGED where all four required categories are assessed. The published
      status is measured against `fusion.worst_band` computed independently over the same
      contributing categories -- the arithmetic, not a restatement of it -- and they are equal
      for every band and for a Red/Amber/Green mix.
  (2) INDETERMINATE is issued, on both status paths, exactly when a required category carries
      no posture, and the fused band is still recorded beside it rather than discarded.
  (3) A SUPPORTING CATEGORY NEVER BLOCKS AND NEVER CREATES A GREEN. A4 and A5 absent leaves an
      official status; A4 and A5 absent never turns a missing required category into a Green.
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


print("1. WORST-WINS IS UNCHANGED WHEN ALL FOUR REQUIRED CATEGORIES ARE ASSESSED")
_n = 0
for combo in itertools.product(["Green", "Yellow", "Amber", "Red"], repeat=4):
    cats = _cats(A1=combo[0], A2=combo[1], A3=combo[2], A6=combo[3])
    # The arithmetic, computed here independently of the gate, exactly as it was before Run 89.
    independent = worst_band([c["status"] for c in cats.values()
                              if c["status"] and c["contributes_to_project_status"]])
    if sp.project_status(cats) != independent:
        FAILURES.append(f"arithmetic moved for {combo}")
        print(f"  [FAIL] {combo}: gate {sp.project_status(cats)!r} != worst_band {independent!r}")
    _n += 1
print(f"  [{'PASS' if not FAILURES else 'FAIL'}] all {_n} four-band combinations publish exactly "
      f"worst_band, unchanged")

print("\n  ...and with the two SUPPORTING categories also assessed, and adverse:")
cats = _cats(A1="Green", A2="Green", A3="Green", A6="Green", A4="Red", A5="Red")
check("supporting categories still enter worst-wins (they always did)",
      sp.project_status(cats), "Red")
check("...and the status is OFFICIAL", sp.project_status_basis(cats)["official"], True)

print("\n2. INDETERMINATE WHEN A REQUIRED CATEGORY CARRIES NO POSTURE")
cats = _cats(A1="Red", A2="Green", A3="Green")          # A6 never called
b = sp.project_status_basis(cats)
check("status", sp.project_status(cats), "Indeterminate")
check("official", b["official"], False)
check("which required category is missing", b["required_missing"], ["A6"])
check("its state is never_called (no reading stored at all)",
      b["required_missing_detail"][0]["state"], "never_called")
check("THE FUSED BAND IS STILL RECORDED, not discarded", b["fused_band"], "Red")
check("every assessed category is still visible with its posture",
      sorted((k, v["status"]) for k, v in cats.items() if v["status"]),
      [("A1", "Red"), ("A2", "Green"), ("A3", "Green")])

print("\n  ...and a required category CALLED but carrying no band is equally missing:")
cats2 = sp.category_statuses({
    "A1": _reading("A1", [_mod("A1.7", "Green")]), "A2": _reading("A2", [_mod("A2.7", "Green")]),
    "A3": _reading("A3", [_mod("A3.2", "Green")]), "A6": _reading("A6", [_mod("A6.1", None)])})
b2 = sp.project_status_basis(cats2)
check("status", sp.project_status(cats2), "Indeterminate")
check("A6 is missing", b2["required_missing"], ["A6"])
check("its state is the reading's own state, NOT never_called",
      b2["required_missing_detail"][0]["state"], "computed")
check("A6 is NOT Green", cats2["A6"]["status"], None)

print("\n3. A SUPPORTING CATEGORY NEVER BLOCKS, AND NEVER CREATES A GREEN")
cats = _cats(A1="Green", A2="Green", A3="Green", A6="Green")   # A4 and A5 never called
b = sp.project_status_basis(cats)
check("A4 and A5 absent does NOT block the official status", b["official"], True)
check("status is the fused Green", sp.project_status(cats), "Green")
check("A4 and A5 are reported as not assessed", b["supporting_not_assessed"], ["A4", "A5"])
cats = _cats(A1="Green", A2="Green", A3="Green")               # A6 missing, A4/A5 missing too
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
