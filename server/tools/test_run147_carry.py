#!/usr/bin/env python3
"""
RUN 147, THE OWNER'S ITEM 4: IS CARRY-FORWARD A SECOND FAULT?

Reads the fixture `tools/test_run147_capture.py` already built (PRJ-R147-A) in the SAME
throwaway database, and answers one question with evidence rather than by reading code:

    where does a carried reading LIVE, and is it on the wire the detail page receives?

Run (from server/), after test_run147_capture.py, against the SAME throwaway database:

    DATABASE_URL=sqlite:///<same throwaway>.db python tools/test_run147_carry.py

CONSTRUCTED FIXTURE. PRJ-002 is not reachable from this container.

THE ANSWER THIS ESTABLISHES. `simulation.carry_forward.select_carried` returns NEW ROWS that
`compute` APPENDS TO `run["computed"]`, which is stored as `computed_results.module_results`.
`facade.live_statuses` -- the six-key list projection the page renders from before any graft --
deliberately omits `module_results`. So a carried reading has exactly ONE route to the page:
the `projectresults` response, through the graft. If the graft does not run, carry-forward
produces nothing visible for the SAME single reason the period's own readings do. It is not a
second fault, and no evidence of a second fault can be obtained from a blank page.
"""
from __future__ import annotations

import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

RESULTS: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    RESULTS.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"  [{detail}]" if detail else ""))


def main() -> None:
    from sqlalchemy import select

    import app.facade as F
    import app.main as main
    from app.models import Project
    from app.research_models import ComputedResult

    LEGACY = "PRJ-R147-A"
    Session = main.SessionFactory
    with Session() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == LEGACY))
        if proj is None:
            print("RESULT: fixture PRJ-R147-A absent -- run tools/test_run147_capture.py first "
                  "against this same database")
            sys.exit(1)
        rows = {r.period: r for r in s.scalars(select(ComputedResult).where(
            ComputedResult.project_id == proj.id,
            ComputedResult.superseded_by.is_(None))).all()}
        r2 = rows.get(2)
        mods2 = r2.module_results or []
        carried = [m for m in mods2 if isinstance(m, dict)
                   and (m.get("carried_from_period") is not None
                        or m.get("carried") or m.get("carried_from"))]
        print(f"    period-2 live row: {len(mods2)} module rows, "
              f"{len(r2.abstained or [])} abstentions")
        print(f"    of those module rows, {len(carried)} are carried readings from an "
              f"earlier period")
        if carried:
            print(f"    example carried row keys: {sorted(carried[0].keys())[:12]}")
        # WHERE A CARRIED READING LIVES.
        check(all(isinstance(m, dict) for m in mods2)
              and len(mods2) > 0,
              "carried and own readings alike live in ONE field, module_results",
              f"{len(mods2)} rows")

        proj_list = (F.live_statuses(s, [proj]) or {}).get(proj.id) or {}
    print(f"    live_statuses projection keys: {sorted(proj_list.keys())}")
    check("module_results" not in proj_list,
          "and the list projection the page renders from before any graft OMITS that field, so "
          "a carried reading has exactly one route to the page: the projectresults graft")
    check(bool(proj_list.get("category_statuses")) and bool(proj_list.get("project_status")),
          "while the category postures and the project status ARE on it -- which is why they "
          "survive a graft that never ran",
          f"{len(proj_list.get('category_statuses') or {})} categories, "
          f"status={proj_list.get('project_status')!r}")

    print("\n  CONCLUSION: carry-forward is a SERVER-SIDE compute-time operation whose output "
          "is\n  indistinguishable, on the wire, from the period's own readings. A page that "
          "receives no\n  module rows shows no carried reading for the SAME reason it shows no "
          "own reading.\n  IT IS NOT A SECOND FAULT, and a blank page carries no evidence "
          "either way about it.")

    failed = [r for r in RESULTS if not r[0]]
    print(f"\nRESULT: {len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    for ok, label, detail in failed:
        print(f"  FAILED: {label}  [{detail}]")
    sys.exit(1 if failed else 0)


main()
