#!/usr/bin/env python3
"""
Run 87, goal one: A COMPARISON-ONLY MODULE CANNOT REACH THE PROJECT STATUS.

What is proved, by measurement on a specification reading of the shape the platform stores:

  (1) a COMPUTED B1.2 reading carrying an adverse band does NOT change the project status;
  (2) the check CAN FAIL -- the same injection is measured with the admission filter
      NEUTRALISED, and the project status then flips, which is the red state the fix removes;
  (3) the category arithmetic for VOTING modules is unchanged by the fix, measured on the
      same rows before and after neutralisation;
  (4) B1.1 Conservative Dominance, which its specification says "does emit a band" and which
      is NOT a comparison ensemble, is still admitted.

Nothing in `server/app/simulation/` is touched by this run or by this test. The decision rule
is still `fusion.worst_band`; only ADMISSION to the rollup changed.

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
    return sp.project_status(sp.category_statuses(readings))


def main() -> int:
    print("Run 87 goal one -- comparison-only modules and the category rollup")

    print("\n1. THE SET ESTABLISHED FROM THE TREE")
    check("comparison-only set", sorted(sp.COMPARISON_ONLY_MODULES), ["B1.2", "B1.3", "B1.4"])
    check("B1.1 is admitted", sp.admitted_to_category_rollup("B1.1"), True)
    check("A1.7 is admitted", sp.admitted_to_category_rollup("A1.7"), True)
    check("B1.2 is not admitted", sp.admitted_to_category_rollup("B1.2"), False)

    print("\n2. BASELINE, no B1 reading at all")
    base = _base()
    check("project status", _project(base), "Green")
    check("A1 category status", sp.category_statuses(base)["A1"]["status"], "Green")
    check("A1 status_set_by", sp.category_statuses(base)["A1"]["status_set_by"],
          ["A1.7", "A1.8"])

    print("\n3. THE INJECTION -- a COMPUTED B1.2 carrying an adverse band")
    inj = _base()
    inj["B1"] = _reading("B1", [{"module_id": "B1.2", "state": "computed", "band": "Red"}])
    cats = sp.category_statuses(inj)
    check("project status UNCHANGED", _project(inj), "Green")
    check("B1 category carries no band", cats["B1"]["status"], None)
    check("B1 set_by is empty", cats["B1"]["status_set_by"], [])
    check("B1.2 is still VISIBLE in the reading (ledger untouched)",
          cats["B1"]["module_count"], 1)
    check("group B still contributes (the group predicate is untouched)",
          cats["B1"]["contributes_to_project_status"], True)
    check("A1 arithmetic unchanged by the injection", cats["A1"]["status"], "Green")

    print("\n4. THE SAME TEST GOES RED WITH THE FIX NEUTRALISED")
    saved = sp.COMPARISON_ONLY_MODULES
    try:
        sp.COMPARISON_ONLY_MODULES = frozenset()          # neutralise
        red_cats = sp.category_statuses(inj)
        check("NEUTRALISED: B1 now carries the adverse band", red_cats["B1"]["status"], "Red")
        check("NEUTRALISED: project status flips -- this is the defect",
              _project(inj), "Red")
        check("NEUTRALISED: voting arithmetic for A1 is STILL unchanged",
              red_cats["A1"]["status"], "Green")
        check("NEUTRALISED: A1 status_set_by STILL unchanged",
              red_cats["A1"]["status_set_by"], ["A1.7", "A1.8"])
    finally:
        sp.COMPARISON_ONLY_MODULES = saved                 # restore

    print("\n5. RESTORED")
    check("project status back to unchanged", _project(inj), "Green")
    check("set restored", sorted(sp.COMPARISON_ONLY_MODULES), ["B1.2", "B1.3", "B1.4"])

    print("\n6. B1.1 IS NOT EXCLUDED -- its band still sets its category")
    b11 = _base()
    b11["B1"] = _reading("B1", [
        {"module_id": "B1.1", "state": "computed", "band": "Amber"},
        {"module_id": "B1.2", "state": "computed", "band": "Red"},
    ])
    c = sp.category_statuses(b11)
    check("B1 status is B1.1's band, not B1.2's", c["B1"]["status"], "Amber")
    check("B1 set_by is B1.1 alone", c["B1"]["status_set_by"], ["B1.1"])
    check("project status is the worst ADMITTED band", _project(b11), "Amber")

    print(f"\n{'ALL PASS' if not FAILURES else 'FAILURES: ' + ', '.join(FAILURES)}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
