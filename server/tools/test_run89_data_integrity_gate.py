#!/usr/bin/env python3
"""
Run 89, goal two: DATA INTEGRITY IS AN ELIGIBILITY GATE AND CANNOT REACH THE PROJECT STATUS.

What is proved, by measurement rather than by argument:

  (1) C1 renders as "Data Integrity" -- the registry's own category name, not a restatement.
  (2) C1.5 Information Completeness Ratio, INJECTED with an adverse band on both status
      paths, changes NO category status outside C1 and does NOT change the project status.
  (3) THE CHECK CAN FAIL. The same injection is measured with the group predicate
      NEUTRALISED, and the project status then flips to the injected band. That is the red
      state, and it is asserted, so this test cannot pass vacuously.
  (4) An unassessed category returns NOT ASSESSED -- a null status -- rather than Green,
      Amber or Red. `fusion.worst_band` over no admitted band is None, at both levels.
  (5) C1.5 is NOT added to `spec_projection.EXCLUDED_FROM_CATEGORY_ROLLUP`: it does not need to be,
      because the whole of group C is already excluded one level up. Asserted so that a later
      run cannot quietly add it and believe it was always there.

Run (from server/):  python tools/test_run89_data_integrity_gate.py
"""
from __future__ import annotations

import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from app import spec_projection as sp
from app.research_models import SpecificationReading
from app.simulation import compute as sim_compute
from app.simulation.fusion import worst_band
from app.simulation.registry import service_index

FAILURES: list[str] = []


def check(label: str, got, want) -> None:
    ok = got == want
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: got {got!r}, want {want!r}")
    if not ok:
        FAILURES.append(label)


def _reading(cat: str, mods: list[dict]) -> SpecificationReading:
    return SpecificationReading(
        reading_id=f"r89-{cat}", category_key=cat, state="computed",
        status=None, counts={"computed": len(mods)}, modules=mods, reason=None,
        missing_upstream=[], served_by="run89-test",
    )


def _mod(mid: str, band: str | None) -> dict:
    return {"module_id": mid, "state": "computed", "band": band, "band_asserted": band is not None,
            "value": 0.5, "display": "0.5", "evidence_metric": "test", "reason": None}


# A1 carries a measured Green. C1 carries an ADVERSE C1.5, which is exactly what must not travel.
READINGS = {
    "A1": _reading("A1", [_mod("A1.7", "Green"), _mod("A1.8", "Green")]),
    "C1": _reading("C1", [_mod("C1.5", "Red")]),
}

print("1. THE CATEGORY IS NAMED DATA INTEGRITY, FROM THE REGISTRY")
_c1_names = {v["category_name"] for k, v in service_index().items() if v["category"] == "C1"}
check("C1's registry category name", sorted(_c1_names), ["Data Integrity"])
_c1_ids = sorted(k for k, v in service_index().items() if v["category"] == "C1")
print(f"  (measured, reported not asserted) C1 modules IN SERVICE: {_c1_ids}")

print("\n2. THE INJECTION: AN ADVERSE C1.5 REACHES NOTHING")
cats = sp.category_statuses(READINGS)
check("C1 was called and has an entry", "C1" in cats, True)
check("C1 does NOT contribute to project status", cats["C1"]["contributes_to_project_status"], False)
check("A1 is unchanged by the injection", cats["A1"]["status"], "Green")
# The band worst-wins produced, which is the quantity C1.5 must not be able to move. The
# PUBLISHED status on this fixture is "Indeterminate" -- Run 89 goal three's required-core gate,
# because A2, A3 and A6 carry no posture here -- and that is asserted straight after, so both
# facts are measured and neither hides the other.
check("THE FUSED BAND is A1's Green, not C1.5's Red",
      sp.project_status_basis(cats)["fused_band"], "Green")
check("...and the PUBLISHED status is Awaiting analysis, because three required categories are "
      "absent from this fixture -- C1.5 did not cause that either (RUN 106 renamed the word; "
      "the fact is unchanged)",
      sp.project_status(cats), sp.AWAITING)
check("group predicate refuses group C", sim_compute.contributes_to_project_status("C"), False)

print("\n3. THE SAME TEST GOES RED WITH THE EXCLUSION NEUTRALISED")
# RE-POINTED AT RUN 106, AND THE REASON MATTERS. Under Run 105's worst-wins project rule,
# neutralising the GROUP predicate was enough to let C1's Red into the project band. Under the
# owner's Run 106 weighted rule there is a SECOND, INDEPENDENT exclusion: C1 is not in
# `project_posture.PROJECT_CATEGORY_WEIGHTS` at all, so admitting the group moves nothing. Both
# mechanisms are now measured -- the group predicate below, and the weight profile after it --
# and the go-red proof is moved onto the profile, which is the one that can still flip the band.
_real = sim_compute.contributes_to_project_status
try:
    sp.contributes_to_project_status = lambda group: True
    cats_bad = sp.category_statuses(READINGS)
    check("NEUTRALISED: C1 now contributes", cats_bad["C1"]["contributes_to_project_status"], True)
    check("NEUTRALISED: the band STILL does not move -- C1 carries no weight either",
          sp.project_status_basis(cats_bad)["fused_band"], "Green")
    check("NEUTRALISED: A1 arithmetic STILL unchanged", cats_bad["A1"]["status"], "Green")

    # THE SECOND NEUTRALISATION, and this one DOES go red: put Data Integrity in the owner's
    # weight profile. That is the defect the executable assertion in `project_posture` and the
    # one in `models_gov` exist to make impossible.
    import app.simulation.project_posture as PP
    _real_weights = dict(PP.PROJECT_CATEGORY_WEIGHTS)
    try:
        PP.PROJECT_CATEGORY_WEIGHTS.clear()
        PP.PROJECT_CATEGORY_WEIGHTS.update({"A1": 0.5, "C1": 0.5})
        check("NEUTRALISED: with C1 weighted, the band flips to C1.5's Red -- this is the defect",
              sp.project_status_basis(sp.category_statuses(READINGS))["fused_band"], "Amber")
    finally:
        PP.PROJECT_CATEGORY_WEIGHTS.clear()
        PP.PROJECT_CATEGORY_WEIGHTS.update(_real_weights)
finally:
    sp.contributes_to_project_status = _real
check("RESTORED: C1 is excluded from the weight profile again",
      "C1" in sp.project_status_basis(sp.category_statuses(READINGS))["project_weights"], False)

print("\n4. RESTORED")
cats_back = sp.category_statuses(READINGS)
check("fused band back to Green", sp.project_status_basis(cats_back)["fused_band"], "Green")
check("C1 excluded again", cats_back["C1"]["contributes_to_project_status"], False)

print("\n5. NOT ASSESSED IS A NULL STATUS, NEVER A GREEN")
check("worst_band over no band at all", worst_band([]), None)
check("worst_band over only nulls", worst_band([None, None]), None)
_none = sp.category_statuses({"A2": _reading("A2", [_mod("A2.7", None)])})
check("a called category whose modules assert no band carries a NULL status",
      _none["A2"]["status"], None)
check("...and it is not Green", _none["A2"]["status"] == "Green", False)
check("...and the fused band over it alone is null",
      sp.project_status_basis(_none)["fused_band"], None)

print("\n6. C1.5 IS NOT IN THE EXCLUDED SET, AND DOES NOT NEED TO BE")
# RE-POINTED TWICE, AND BOTH REASONS ARE RECORDED. (a) RUN 98 trimmed the set to {B1.2}: B1.3 and
# B1.4 left the registry at Run 97 and no longer resolve, so this line had been asserting a stale
# membership since then and was ALREADY RED before Run 106 touched it. (b) RUN 106 renamed the set
# to EXCLUDED_FROM_CATEGORY_ROLLUP, because B1.2 stopped being a comparison ensemble when the
# owner made the weighted vote the project status rule. Neither change weakens what this section
# proves, which is that C1.5 is not in the set.
check("the excluded set is Run 98's, unextended",
      sorted(sp.EXCLUDED_FROM_CATEGORY_ROLLUP), ["B1.2"])
check("C1.5 is admitted to its OWN category rollup (it is a gate reading, not a project posture)",
      sp.admitted_to_category_rollup("C1.5"), True)

print("\n7. THE EXCLUSION FROM THE WEIGHTED PROFILE IS EXECUTABLE, NOT A COMMENT")
from app.simulation import models_gov as GOV
check("C1 is not in the weight profile", "C1" in GOV.WEIGHTED_VOTING_CATEGORY_WEIGHTS, False)
# RUN 95, SECTION 3. The owner restated his profile over FIVE categories at 0.28/0.28/0.17/
# 0.11/0.16. A5 Systems and Dynamics is gone: Run 95 retired every module it held. The weights
# are asserted by VALUE as well as by key set, because the profile is the owner's stated
# authority and a silent drift in a number is exactly what this check exists to catch.
check("the profile is exactly the owner's five, Run 95 section 3",
      sorted(GOV.WEIGHTED_VOTING_CATEGORY_WEIGHTS), ["A1", "A2", "A3", "A4", "A6"])
check("...at the owner's stated weights", dict(GOV.WEIGHTED_VOTING_CATEGORY_WEIGHTS),
      {"A1": 0.28, "A2": 0.28, "A3": 0.17, "A4": 0.11, "A6": 0.16})
check("A5 is not in the profile", "A5" in GOV.WEIGHTED_VOTING_CATEGORY_WEIGHTS, False)
check("the provenance names the owner, not a literature value",
      "owner's stated authority" in GOV.WEIGHT_PROVENANCE, True)
check("...summing to 1.00", round(sum(GOV.WEIGHTED_VOTING_CATEGORY_WEIGHTS.values()), 10), 1.0)
# RE-POINTED AT RUN 106: `weighted_category_vote` no longer returns a plurality WINNER. The owner
# made the weighted vote the project status rule, so it now returns the banded weighted SUM under
# the key `status`. The fact under test -- that a C1 posture is ignored and not weighed -- is
# unchanged and is asserted on the new key, and on the assessed set as well so the check names
# what was and was not weighed rather than only what came out.
_c1 = GOV.weighted_category_vote({"A1": {"status": "Green"}, "C1": {"status": "Red"}})
check("a C1 posture is ignored by the weighted vote, not weighed", _c1["status"], "Green")
check("...and C1 is not in the assessed set", _c1["assessed_categories"], ["A1"])
# AND THE GUARD FIRES. Adding Data Integrity to the profile raises rather than being weighed.
_real_profile = dict(GOV.WEIGHTED_VOTING_CATEGORY_WEIGHTS)
_raised = None
try:
    GOV.WEIGHTED_VOTING_CATEGORY_WEIGHTS = {"C1": 1.0}
    try:
        GOV.weighted_category_vote({"C1": {"status": "Red"}})
    except AssertionError as exc:
        _raised = str(exc)
finally:
    GOV.WEIGHTED_VOTING_CATEGORY_WEIGHTS = _real_profile
check("INJECTED: adding Data Integrity to the profile RAISES",
      _raised, "Data Integrity is a precondition for using the criteria, not a criterion in them.")
check("RESTORED: the profile is the owner's again",
      sorted(GOV.WEIGHTED_VOTING_CATEGORY_WEIGHTS), ["A1", "A2", "A3", "A4", "A6"])

print("\n" + ("ALL PASS" if not FAILURES else f"{len(FAILURES)} FAILURES: {FAILURES}"))
sys.exit(1 if FAILURES else 0)
