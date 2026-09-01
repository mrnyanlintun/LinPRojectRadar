#!/usr/bin/env python3
"""
Run 89, goal three: THE REQUIRED CORE, AND THE WORD PUBLISHED WHEN IT IS INCOMPLETE.

RE-POINTED AT RUN 106, AND THE REASON IS RECORDED HERE RATHER THAN LEFT TO A DIFF. Two checks
below went red because THE OWNER DELIBERATELY CHANGED THE BEHAVIOUR THEY PINNED, and neither is
weakened, dropped or made unable to fail:

  * SECTION 1 pinned the project rule to `fusion.worst_band` over the contributing categories
    (Run 105's rule) across all 1024 band combinations. Run 106 section 1 replaces that rule with
    the owner's WEIGHTED VOTE. The sweep is unchanged in shape and is still exhaustive over the
    same 1024 combinations; the independent arithmetic it is measured against is now the weighted
    sum, COMPUTED IN THIS FILE from the owner's published weights and the Run 104 scale rather
    than by calling the function under test, so it remains an independent check and not a
    restatement. A case where the two rules DIFFER is asserted explicitly, so the sweep cannot
    pass by accident if the platform quietly reverted to worst-wins.
  * THE WORD in sections 2, 3 and 5 was "Indeterminate". Run 106 section 2 removes it: there are
    six statuses and that is not one of them. The word asserted is now "Awaiting analysis", read
    from `sp.AWAITING` rather than typed, so this suite cannot drift from the architecture; and
    the SENTENCE that must accompany it is asserted too, because a bare label is the defect the
    owner's ruling is about.

What is proved, by measurement:

  (1) THE PUBLISHED STATUS IS THE OWNER'S WEIGHTED VOTE where all five required categories are
      assessed. It is measured against the weighted sum computed independently here over the
      same contributing categories -- the arithmetic, not a restatement of it -- for all 1024
      band combinations.
  (2) "Awaiting analysis" is issued, on both status paths, exactly when a required category
      carries no posture; the band is still recorded beside it rather than discarded; and the
      reason sentence names the missing category.
  (3) THERE IS NO SUPPORTING TIER ANY MORE, and its absence is asserted rather than assumed.
      RUN 95 SECTION 3.2 SUPERSEDED RUN 89 HERE: the required core is all five weighted
      performance categories, A4 Document Signals moved from supporting to required, and A5
      Systems and Dynamics holds no module in service and is not a category of this platform.
      What Run 89 checked -- that A4 and A5 absent still leaves an official status -- is now
      FALSE BY THE OWNER'S RULING, so it is not asserted; the check is REPLACED by the fact
      that took its place, which is that A4 absent BLOCKS, and by the check that a missing
      category still never becomes a Green. That last half is the part that mattered and it
      is kept intact.
  (4) THE WITHHELD-STATUS WORD IS NOT A BAND. It is not in `BAND_SEVERITY` and `worst_band`
      never returns it and never ranks it.
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
from app.simulation.category_posture import AVERAGE_CUTS, BAND_SCORE
from app.simulation.project_posture import PROJECT_CATEGORY_WEIGHTS

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


def independent_weighted(cats: dict) -> str | None:
    """
    THE OWNER'S RUN 106 PROJECT RULE, WRITTEN OUT HERE AND NOT IMPORTED FROM THE THING UNDER
    TEST. It uses the published weight profile and the published Run 104 scale and cuts -- which
    is what a reader would use to check by hand -- and performs the sum itself, so a defect in
    `project_posture` cannot make this agree with it.
    """
    present = {k: c["status"] for k, c in cats.items()
               if k in PROJECT_CATEGORY_WEIGHTS and c.get("status")
               and c.get("contributes_to_project_status")}
    if not present:
        return None
    total = sum(PROJECT_CATEGORY_WEIGHTS[k] for k in present)
    s = sum((PROJECT_CATEGORY_WEIGHTS[k] / total) * BAND_SCORE[b] for k, b in present.items())
    for cut, band in AVERAGE_CUTS:
        if round(s, 10) >= cut:
            return band
    return "Red"


print("1. THE PUBLISHED STATUS IS THE OWNER'S WEIGHTED VOTE, ALL FIVE CATEGORIES ASSESSED")
# THE POPULATION IS THE REQUIRED SET ITSELF, NOT A TYPED LIST OF NAMES. Run 89 wrote four names
# and `repeat=4`; Run 95 made the core five. Reading `sp.REQUIRED_CATEGORIES` here means the
# exhaustive sweep follows the architecture instead of restating it, and the count it prints is
# measured (4 bands ** 5 categories == 1024) rather than written down.
_REQ = list(sp.REQUIRED_CATEGORIES)
_n = 0
for combo in itertools.product(["Green", "Yellow", "Amber", "Red"], repeat=len(_REQ)):
    cats = _cats(**dict(zip(_REQ, combo)))
    # The arithmetic, computed here independently of the gate, exactly as it was before Run 89.
    independent = independent_weighted(cats)
    if sp.project_status(cats) != independent:
        FAILURES.append(f"arithmetic moved for {combo}")
        print(f"  [FAIL] {combo}: gate {sp.project_status(cats)!r} != weighted {independent!r}")
    _n += 1
print(f"  [{'PASS' if not FAILURES else 'FAIL'}] all {_n} band combinations over the "
      f"{len(_REQ)} required categories publish exactly the owner's weighted vote")
check("the sweep was exhaustive over the required core, not a sample",
      _n, 4 ** len(sp.REQUIRED_CATEGORIES))
check("the required core is the owner's five, Run 95 section 3.2",
      list(sp.REQUIRED_CATEGORIES), ["A1", "A2", "A3", "A4", "A6"])

print("\n  ...and the sweep is not passing because the two rules agree:")
# THE CASE WHERE WORST-WINS AND THE WEIGHTED VOTE DIFFER, ASSERTED EXPLICITLY. Without this the
# 1024-combination sweep would still pass if the platform silently reverted to Run 105's rule on
# some subset, because on many combinations the two rules coincide. Four Greens and one Amber in
# Delivery Quality: worst-wins says Amber, the owner's weights say 0.28(2)+0.28(2)+0.17(2)
# +0.11(2)+0.16(-1) = +1.52, which is at or above 1.5 and therefore Green. This IS the owner's
# corpus project, and it is the change Run 106 was ordered to make.
cats = _cats(A1="Green", A2="Green", A3="Green", A4="Green", A6="Amber")
check("worst-wins over these five categories would say", worst_band(
    [c["status"] for c in cats.values() if c["status"]]), "Amber")
check("the owner's weighted vote says", sp.project_status(cats), "Green")
check("...and the arithmetic is published on the basis, to four places",
      sp.project_status_basis(cats)["project_weighted_sum"], 1.52)
check("...and the status is OFFICIAL", sp.project_status_basis(cats)["official"], True)

print("\n  ...and an adverse required category moves the sum by its weight and no more:")
cats = _cats(A1="Green", A2="Green", A3="Green", A6="Green", A4="Red")
# 0.28(2)+0.28(2)+0.17(2)+0.16(2) + 0.11(-2) = 1.78 - 0.22 = +1.56, at or above 1.5.
check("A4 Red does NOT drag the project to Red -- there is no override",
      sp.project_status(cats), "Green")
check("...and the weighted sum shows exactly how far it moved it",
      sp.project_status_basis(cats)["project_weighted_sum"], 1.56)
check("...and the status is OFFICIAL", sp.project_status_basis(cats)["official"], True)

print("\n2. \"AWAITING ANALYSIS\" WHEN A REQUIRED CATEGORY CARRIES NO POSTURE")
check("the word is the architecture's own, not typed here", sp.AWAITING, "Awaiting analysis")
# A4 IS SUPPLIED HERE BECAUSE RUN 95 MADE IT REQUIRED. The fact under test is what happens when
# ONE required category is missing, so every other required category must carry a posture or the
# check would be measuring two absences at once.
cats = _cats(A1="Red", A2="Green", A3="Green", A4="Green")   # A6 never called
b = sp.project_status_basis(cats)
check("status", sp.project_status(cats), sp.AWAITING)
check("official", b["official"], False)
# RUN 106, GOAL TWO. A BARE LABEL IS NOT ENOUGH. The sentence must name the missing category.
check("the reason sentence names the missing category",
      "A6" in (b["status_reason"] or ""), True)
check("...and says no posture is issued",
      "no project posture is issued" in (b["status_reason"] or "").lower(), True)
check("which required category is missing", b["required_missing"], ["A6"])
check("its state is never_called (no reading stored at all)",
      b["required_missing_detail"][0]["state"], "never_called")
# A1 Red, A2/A3/A4 Green, A6 unassessed. The weights renormalise over the four that reported:
# (0.28(-2) + 0.28(2) + 0.17(2) + 0.11(2)) / 0.84 = 0.56/0.84 = +0.6667 -> Yellow.
check("THE BAND IS STILL RECORDED, not discarded", b["fused_band"], "Yellow")
check("...and it was formed by RENORMALISING over the categories that reported, never by "
      "scoring the absent one as zero", b["project_renormalised"], True)
check("...and the renormalisation is stated in the arithmetic",
      "REMOVED FROM THE DENOMINATOR" in (b["project_arithmetic"] or ""), True)
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
check("status", sp.project_status(cats2), sp.AWAITING)
check("A6 is missing", b2["required_missing"], ["A6"])
check("its state is the reading's own state, NOT never_called",
      b2["required_missing_detail"][0]["state"], "computed")
check("A6 is NOT Green", cats2["A6"]["status"], None)

print("\n3. THERE IS NO SUPPORTING TIER, AND A MISSING CATEGORY NEVER BECOMES A GREEN")
cats = _cats(A1="Green", A2="Green", A3="Green", A6="Green")   # A4 never called
b = sp.project_status_basis(cats)
check("A4 absent DOES block the official status now -- Run 95 made it required",
      b["official"], False)
check("...and the status is Awaiting analysis, not the weighted Green",
      sp.project_status(cats), sp.AWAITING)
check("...while the fused Green is still recorded beside it", b["fused_band"], "Green")
check("the supporting tier is empty", list(sp.SUPPORTING_CATEGORIES), [])
check("so supporting_assessed publishes [] rather than vanishing",
      b["supporting_assessed"], [])
check("and supporting_not_assessed publishes [] too", b["supporting_not_assessed"], [])
check("A5 is in neither tier -- it is not a category of this platform",
      "A5" in sp.REQUIRED_CATEGORIES or "A5" in sp.SUPPORTING_CATEGORIES, False)
cats = _cats(A1="Green", A2="Green", A3="Green")               # A6 and A4 missing
check("no documents supplied does NOT produce a Green for a missing required category",
      sp.project_status(cats), sp.AWAITING)

print("\n4. THE WITHHELD-STATUS WORD IS NOT A BAND")
check("not in BAND_SEVERITY", sp.AWAITING in BAND_SEVERITY, False)
check("worst_band cannot return it", worst_band([sp.AWAITING]), None)
check("worst_band ranks it nowhere against a real band",
      worst_band([sp.AWAITING, "Green"]), "Green")
# RUN 106, GOAL TWO. THE REMOVED WORD IS GONE FROM THE VOCABULARY AND FROM BOTH STATUS PATHS.
check("the removed word is not in BAND_SEVERITY either", "Indeterminate" in BAND_SEVERITY, False)
check("and the specification path never publishes it",
      "Indeterminate" in {sp.project_status(_cats(A1="Green")),
                          sp.project_status(_cats(A1="Green", A2="Green", A3="Green",
                                                  A4="Green", A6="Green"))}, False)

print("\n5. THE CHECK CAN FAIL -- THE REQUIRED SET NEUTRALISED")
_real = sp.REQUIRED_CATEGORIES
try:
    sp.REQUIRED_CATEGORIES = ()
    cats = _cats(A1="Red", A2="Green", A3="Green")     # A4 and A6 still missing
    # (0.28(-2) + 0.28(2) + 0.17(2)) / 0.73 = 0.34/0.73 = +0.4658 -> Amber.
    check("NEUTRALISED: the gate no longer fires", sp.project_status(cats), "Amber")
    check("NEUTRALISED: the row is declared official -- this is the defect",
          sp.project_status_basis(cats)["official"], True)
finally:
    sp.REQUIRED_CATEGORIES = _real
cats = _cats(A1="Red", A2="Green", A3="Green")
check("RESTORED: Awaiting analysis again", sp.project_status(cats), sp.AWAITING)

print("\n" + ("ALL PASS" if not FAILURES else f"{len(FAILURES)} FAILURES: {FAILURES}"))
sys.exit(1 if FAILURES else 0)
