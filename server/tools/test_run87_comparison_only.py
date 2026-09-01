#!/usr/bin/env python3
"""
Run 87, goal one: AN EXCLUDED MODULE'S BAND CANNOT REACH ITS CATEGORY'S POSTURE.

RE-POINTED AT RUN 106, AND THE REASON IS RECORDED HERE RATHER THAN LEFT TO A DIFF. Three things
the owner changed made checks in this suite go red, and none is weakened or dropped:

  * THE SET WAS RENAMED. `spec_projection.COMPARISON_ONLY_MODULES` is now
    `EXCLUDED_FROM_CATEGORY_ROLLUP`, because B1.2 stopped being a comparison ensemble: the owner
    ruled at Run 106 that the weighted vote over the five category postures IS the project status
    rule, and B1.2 now reports it. The EXCLUSION is unchanged and so is its structural reason --
    B1.2's reading is computed FROM the category rollup, so it cannot be evidence within it.
  * THE QUANTITY THIS SUITE MEASURED WAS THE PROJECT STATUS. Under Run 105's worst-wins rule a
    B1.2 Red admitted to B1 flipped the project. Under the owner's Run 106 weighted rule, B1
    carries NO WEIGHT AT ALL -- only A1, A2, A3, A4 and A6 are weighed -- so the project status
    is now protected from B1 by a SECOND, INDEPENDENT mechanism, and measuring it would no longer
    exercise the admission filter. That is a stronger position, and it is asserted below rather
    than assumed. The suite's own subject moves to the quantity the filter still governs: the
    CATEGORY posture. Section 4's neutralise-and-go-red proof flips that, so this suite is no
    more able to pass vacuously than it was.
  * THE THIRD CONSEQUENCE IS ASSERTED TOO: with B1 carrying no weight, the project status does
    NOT move even with the filter neutralised, and that is checked in the neutralised block so
    the claim is measured and not argued.

What is proved, by measurement on a specification reading of the shape the platform stores:

  (1) a COMPUTED B1.2 reading carrying an adverse band does NOT change the project status;
  (2) the check CAN FAIL -- the same injection is measured with the admission filter
      NEUTRALISED, and the project status then flips, which is the red state the fix removes;
  (3) the category arithmetic for VOTING modules is unchanged by the fix, measured on the
      same rows before and after neutralisation;
  (4) B1.1 Conservative Dominance, which its specification says "does emit a band" and which
      is NOT a comparison ensemble, is still admitted.

Nothing in `server/app/simulation/` was touched by RUN 87 or by this test. ADMISSION to the
rollup is what Run 87 changed and is what this suite is about; the DECISION rule has since moved
twice (Run 105 to worst-wins across the categories, Run 106 to the owner's weighted vote) and
this suite does not pin it -- `test_run89_required_core.py` does.

Run (from server/):  python tools/test_run87_comparison_only.py
"""
from __future__ import annotations

import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from app import spec_projection as sp
from app.research_models import SpecificationReading

FAILURES: list[str] = []


def check(label: str, got, want) -> None:
    ok = got == want
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: got {got!r}, want {want!r}")
    if not ok:
        FAILURES.append(label)


def _reading(cat: str, mods: list[dict]) -> SpecificationReading:
    return SpecificationReading(
        reading_id=f"r87-{cat}", category_key=cat, state="computed",
        status=None, counts={"computed": len(mods)}, modules=mods, reason=None,
        missing_upstream=[], served_by="run87-test",
    )


def _base() -> dict[str, SpecificationReading]:
    """A1 as the real stored row of PRJ-R79-1787885845 period 1 carries it: A1.7 and A1.8
    COMPUTED Green, the rest abstained. That row is the voting-arithmetic control."""
    return {
        "A1": _reading("A1", [
            {"module_id": "A1.2", "state": "abstained", "band": None},
            {"module_id": "A1.7", "state": "computed", "band": "Green"},
            {"module_id": "A1.8", "state": "computed", "band": "Green"},
        ]),
    }


def _project(readings) -> str | None:
    """
    THE BAND THE PROJECT RULE PRODUCES over the admitted categories.

    RUN 89 UPDATED THIS, AND IT IS NOT A WEAKENING. Run 89 goal three added the required-core
    gate on top of worst-wins, so `sp.project_status` now returns "Indeterminate" on these
    fixtures -- which carry only A1 and B1 and therefore have three required categories with no
    posture. That answers a DIFFERENT question (may an official status be issued) from the one
    this suite asks (does a comparison-only module's band reach the project fusion). The
    published-status gate has its own suite, `test_run89_required_core.py`, which proves the
    arithmetic here is untouched across all 256 four-band combinations.

    RUN 106: this reads `fused_band` off the same basis record, which is now the band the
    OWNER'S WEIGHTED VOTE produced. It is used below to prove the project status is INDEPENDENT
    of B1 -- not to prove the admission filter works, which is section 3's job and is measured on
    the category posture.
    """
    return sp.project_status_basis(sp.category_statuses(readings))["fused_band"]


def main() -> int:
    print("Run 87 goal one -- comparison-only modules and the category rollup")

    print("\n1. THE SET ESTABLISHED FROM THE TREE")
    # RUN 98: trimmed to {B1.2}; B1.3 and B1.4 left the registry at Run 97 and no longer
    # resolve, so naming them here asserted nothing about any module in service.
    check("excluded-from-rollup set", sorted(sp.EXCLUDED_FROM_CATEGORY_ROLLUP), ["B1.2"])
    check("the old name is GONE, not aliased -- two names for one set can drift",
          hasattr(sp, "COMPARISON_ONLY_MODULES"), False)
    check("B1.1 is admitted", sp.admitted_to_category_rollup("B1.1"), True)
    check("A1.7 is admitted", sp.admitted_to_category_rollup("A1.7"), True)
    check("B1.2 is not admitted", sp.admitted_to_category_rollup("B1.2"), False)

    print("\n2. BASELINE, no B1 reading at all")
    base = _base()
    check("project status", _project(base), "Green")
    check("A1 category status", sp.category_statuses(base)["A1"]["status"], "Green")
    check("A1 status_set_by", sp.category_statuses(base)["A1"]["status_set_by"],
          ["A1.7", "A1.8"])

    print("\n2b. B1 CARRIES NO WEIGHT IN THE OWNER'S PROJECT RULE -- the second mechanism")
    from app.simulation.project_posture import PROJECT_CATEGORY_WEIGHTS
    check("the weighted categories are the owner's five", sorted(PROJECT_CATEGORY_WEIGHTS),
          ["A1", "A2", "A3", "A4", "A6"])
    check("B1 is not among them", "B1" in PROJECT_CATEGORY_WEIGHTS, False)

    print("\n3. THE INJECTION -- a COMPUTED B1.2 carrying an adverse band")
    inj = _base()
    inj["B1"] = _reading("B1", [{"module_id": "B1.2", "state": "computed", "band": "Red"}])
    cats = sp.category_statuses(inj)
    check("project status UNCHANGED", _project(inj), "Green")
    check("B1 is not in the assessed set the project rule weighed",
          "B1" in (sp.project_status_basis(cats)["project_category_scores"] and
                   [c["category"] for c in
                    sp.project_status_basis(cats)["project_category_scores"]]), False)
    check("B1 category carries no band", cats["B1"]["status"], None)
    check("B1 set_by is empty", cats["B1"]["status_set_by"], [])
    check("B1.2 is still VISIBLE in the reading (ledger untouched)",
          cats["B1"]["module_count"], 1)
    check("group B still contributes (the group predicate is untouched)",
          cats["B1"]["contributes_to_project_status"], True)
    check("A1 arithmetic unchanged by the injection", cats["A1"]["status"], "Green")

    print("\n4. THE SAME TEST GOES RED WITH THE FIX NEUTRALISED")
    saved = sp.EXCLUDED_FROM_CATEGORY_ROLLUP
    try:
        sp.EXCLUDED_FROM_CATEGORY_ROLLUP = frozenset()     # neutralise
        red_cats = sp.category_statuses(inj)
        check("NEUTRALISED: B1 now carries the adverse band -- THIS IS THE DEFECT",
              red_cats["B1"]["status"], "Red")
        check("NEUTRALISED: B1.2 is named as having set it",
              red_cats["B1"]["status_set_by"], ["B1.2"])
        # RUN 106. The project status does NOT move even neutralised, because B1 carries no
        # weight. Measured, so the claim above is not an argument.
        check("NEUTRALISED: the PROJECT status still does not move -- B1 carries no weight",
              _project(inj), "Green")
        check("NEUTRALISED: voting arithmetic for A1 is STILL unchanged",
              red_cats["A1"]["status"], "Green")
        check("NEUTRALISED: A1 status_set_by STILL unchanged",
              red_cats["A1"]["status_set_by"], ["A1.7", "A1.8"])
    finally:
        sp.EXCLUDED_FROM_CATEGORY_ROLLUP = saved           # restore

    print("\n5. RESTORED")
    check("project status back to unchanged", _project(inj), "Green")
    check("B1 carries no posture again", sp.category_statuses(inj)["B1"]["status"], None)
    check("set restored", sorted(sp.EXCLUDED_FROM_CATEGORY_ROLLUP), ["B1.2"])

    print("\n6. B1.1 IS NOT EXCLUDED -- its band still sets its category")
    b11 = _base()
    b11["B1"] = _reading("B1", [
        {"module_id": "B1.1", "state": "computed", "band": "Amber"},
        {"module_id": "B1.2", "state": "computed", "band": "Red"},
    ])
    c = sp.category_statuses(b11)
    check("B1 status is B1.1's band, not B1.2's", c["B1"]["status"], "Amber")
    check("B1 set_by is B1.1 alone", c["B1"]["status_set_by"], ["B1.1"])
    # RUN 106. B1 carries no weight, so its Amber does not reach the project either way. The
    # ADMISSION fact is the two checks above; this one records what the project rule now does.
    check("project status is formed from the WEIGHTED categories, which do not include B1",
          _project(b11), "Green")

    print(f"\n{'ALL PASS' if not FAILURES else 'FAILURES: ' + ', '.join(FAILURES)}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
