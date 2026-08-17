#!/usr/bin/env python3
"""
RUN 31, PASS 1: restate the version-boundary suites that pinned the then-current stamp.

WHY THIS IS A RESTATEMENT AND NOT A RELAXATION. Each of these suites proves ONE run's version
boundary. Its scientific claim is "my run appended stamp X onto the line that commit shipped, and
overwrote nothing". That claim is proved against a GIT OBJECT and is untouched here.

What breaks on an authorised append is the SECOND kind of assertion these suites also carry:
`SIMULATION_VERSION == "sim-2026.08-v16"`, and `HISTORY[len(old):] == (exact tuple)`. Those say
"and my stamp is still the current one", which was true only until the next authorised run. That
is a pin on a moving value, not an invariant.

THE PRECEDENT IS ALREADY IN THIS REPOSITORY. `test_run28_version_boundary.py` carries a comment
written by Run 29 making exactly this restatement, for exactly this reason, and naming it
MONOTONE GROWTH BY AT LEAST ONE. This script applies that same restatement to the remaining
suites rather than inventing a new convention.

WHAT REMAINS ASSERTED, and it is every invariant that is actually an invariant:
  * the history is a strict PREFIX of the current history, read from the run's own git object;
  * every stamp is unique;
  * the history ends at the current stamp;
  * the stamps THIS run added appear, contiguously, in order, at the position it added them;
  * the line it superseded is the line its predecessor commit shipped.

Nothing here asserts that any past run's stamp is still the current one, because that is false by
design the moment a later authorised run appends.
"""

import pathlib
import re
import sys

TOOLS = pathlib.Path(__file__).resolve().parent

RESTATEMENT = (
    "# RESTATED BY RUN 31, PASS 1. The assertion below pinned the CURRENT stamp to this run's\n"
    "# own stamp, which was true until the next authorised append. Run 31 appends v17. What is\n"
    "# an invariant -- and what is still asserted -- is that this run's stamp is present, in\n"
    "# order, at the position this run added it, and that the earlier history is a strict prefix\n"
    "# read out of git. The precedent for this restatement is Run 29's identical comment in\n"
    "# test_run28_version_boundary.py.\n")

# (file, [(old_fragment, new_fragment)])
EDITS: list[tuple[str, list[tuple[str, str]]]] = [
    ("test_run30_version_boundary.py", [
        ('check(SIMULATION_VERSION == "sim-2026.08-v16",\n'
         '      "the analytical layer is stamped sim-2026.08-v16", SIMULATION_VERSION)\n'
         'check(SIMULATION_VERSION_SUPERSEDED == "sim-2026.08-v15",\n'
         '      "and names sim-2026.08-v15 as the line it supersedes", SIMULATION_VERSION_SUPERSEDED)',
         RESTATEMENT +
         'check("sim-2026.08-v16" in SIMULATION_VERSION_HISTORY,\n'
         '      "the stamp Run 30 added, sim-2026.08-v16, is present in the history",\n'
         '      str(SIMULATION_VERSION_HISTORY))\n'
         'check(SIMULATION_VERSION_HISTORY.index("sim-2026.08-v16")\n'
         '      == SIMULATION_VERSION_HISTORY.index("sim-2026.08-v15") + 1,\n'
         '      "and it directly follows sim-2026.08-v15, the line it superseded",\n'
         '      str(SIMULATION_VERSION_HISTORY))'),
        ('check(SIMULATION_VERSION_HISTORY[len(_old_stamps):] == ("sim-2026.08-v15",\n'
         '                                                        "sim-2026.08-v16"),',
         'check(SIMULATION_VERSION_HISTORY[len(_old_stamps):][:2] == ("sim-2026.08-v15",\n'
         '                                                            "sim-2026.08-v16"),'),
    ]),
    ("test_run30_closure_version_boundary.py", [
        ('check(SIMULATION_VERSION == "sim-2026.08-v16",\n'
         '      "the analytical layer is stamped sim-2026.08-v16", SIMULATION_VERSION)\n'
         'check(SIMULATION_VERSION_SUPERSEDED == "sim-2026.08-v15",\n'
         '      "and names sim-2026.08-v15 as the line it supersedes", SIMULATION_VERSION_SUPERSEDED)',
         RESTATEMENT +
         'check("sim-2026.08-v16" in SIMULATION_VERSION_HISTORY,\n'
         '      "the stamp this closure added, sim-2026.08-v16, is present in the history",\n'
         '      str(SIMULATION_VERSION_HISTORY))\n'
         'check(SIMULATION_VERSION_HISTORY.index("sim-2026.08-v16")\n'
         '      == SIMULATION_VERSION_HISTORY.index("sim-2026.08-v15") + 1,\n'
         '      "and it directly follows sim-2026.08-v15, the line it superseded",\n'
         '      str(SIMULATION_VERSION_HISTORY))'),
        ('check(SIMULATION_VERSION_HISTORY[len(_old_stamps):] == ("sim-2026.08-v16",),',
         'check(SIMULATION_VERSION_HISTORY[len(_old_stamps):][:1] == ("sim-2026.08-v16",),'),
    ]),
    ("test_run29_version_boundary.py", [
        ('check(SIMULATION_VERSION == "sim-2026.08-v16",\n'
         '      "the analytical layer is stamped sim-2026.08-v16", SIMULATION_VERSION)\n'
         'check(SIMULATION_VERSION_SUPERSEDED == "sim-2026.08-v15",\n'
         '      "and names sim-2026.08-v15 as the line it supersedes", SIMULATION_VERSION_SUPERSEDED)',
         RESTATEMENT +
         'check("sim-2026.08-v13" in SIMULATION_VERSION_HISTORY,\n'
         '      "the stamp Run 29 added, sim-2026.08-v13, is present in the history",\n'
         '      str(SIMULATION_VERSION_HISTORY))\n'
         'check(SIMULATION_VERSION_HISTORY.index("sim-2026.08-v13")\n'
         '      == SIMULATION_VERSION_HISTORY.index("sim-2026.08-v12") + 1,\n'
         '      "and it directly follows sim-2026.08-v12, the line it superseded",\n'
         '      str(SIMULATION_VERSION_HISTORY))'),
        ('check(SIMULATION_VERSION_HISTORY[len(_old_stamps):] == ("sim-2026.08-v13", "sim-2026.08-v14",',
         'check(SIMULATION_VERSION_HISTORY[len(_old_stamps):][:4] == ("sim-2026.08-v13", "sim-2026.08-v14",'),
    ]),
    ("test_run29_closure_version_boundary.py", [
        ('check(SIMULATION_VERSION == "sim-2026.08-v16",\n'
         '      "the analytical layer is stamped sim-2026.08-v16", SIMULATION_VERSION)\n'
         'check(SIMULATION_VERSION_SUPERSEDED == "sim-2026.08-v15",\n'
         '      "and names sim-2026.08-v15 as the line it supersedes", SIMULATION_VERSION_SUPERSEDED)',
         RESTATEMENT +
         'check("sim-2026.08-v14" in SIMULATION_VERSION_HISTORY,\n'
         '      "the stamp this closure added, sim-2026.08-v14, is present in the history",\n'
         '      str(SIMULATION_VERSION_HISTORY))\n'
         'check(SIMULATION_VERSION_HISTORY.index("sim-2026.08-v14")\n'
         '      == SIMULATION_VERSION_HISTORY.index("sim-2026.08-v13") + 1,\n'
         '      "and it directly follows sim-2026.08-v13, the line it superseded",\n'
         '      str(SIMULATION_VERSION_HISTORY))'),
        ('check(SIMULATION_VERSION_HISTORY[len(_old_stamps):] == ("sim-2026.08-v14", "sim-2026.08-v15",',
         'check(SIMULATION_VERSION_HISTORY[len(_old_stamps):][:3] == ("sim-2026.08-v14", "sim-2026.08-v15",'),
    ]),
    ("test_run28_version_boundary.py", [
        ('check(SIMULATION_VERSION == "sim-2026.08-v16",\n'
         '      "the analytical layer is stamped sim-2026.08-v16", SIMULATION_VERSION)',
         RESTATEMENT +
         'check("sim-2026.08-v12" in SIMULATION_VERSION_HISTORY,\n'
         '      "the stamp Run 28 added, sim-2026.08-v12, is present in the history",\n'
         '      str(SIMULATION_VERSION_HISTORY))'),
        ('check(SIMULATION_VERSION_SUPERSEDED == "sim-2026.08-v15",',
         'check(SIMULATION_VERSION_HISTORY.index("sim-2026.08-v12")\n'
         '      == SIMULATION_VERSION_HISTORY.index("sim-2026.08-v11") + 1,'),
        ('check(SIMULATION_VERSION_HISTORY == (\n'
         '      "sim-2026.07-v1", "sim-2026.08-v2", "sim-2026.08-v3", "sim-2026.08-v4", "sim-2026.08-v5",\n'
         '      "sim-2026.08-v6", "sim-2026.08-v7", "sim-2026.08-v8", "sim-2026.08-v9", "sim-2026.08-v10",\n'
         '      "sim-2026.08-v11", "sim-2026.08-v12", "sim-2026.08-v13", "sim-2026.08-v14",\n'
         '      "sim-2026.08-v15", "sim-2026.08-v16"),',
         'check(SIMULATION_VERSION_HISTORY[:16] == (\n'
         '      "sim-2026.07-v1", "sim-2026.08-v2", "sim-2026.08-v3", "sim-2026.08-v4", "sim-2026.08-v5",\n'
         '      "sim-2026.08-v6", "sim-2026.08-v7", "sim-2026.08-v8", "sim-2026.08-v9", "sim-2026.08-v10",\n'
         '      "sim-2026.08-v11", "sim-2026.08-v12", "sim-2026.08-v13", "sim-2026.08-v14",\n'
         '      "sim-2026.08-v15", "sim-2026.08-v16"),'),
        ('check(SIMULATION_VERSION_HISTORY[len(_old_stamps):] == ("sim-2026.08-v12", "sim-2026.08-v13",',
         'check(SIMULATION_VERSION_HISTORY[len(_old_stamps):][:5] == ("sim-2026.08-v12", "sim-2026.08-v13",'),
    ]),
    ("test_run10_state_protection.py", [
        ('      SIMULATION_VERSION == "sim-2026.08-v16")',
         '      SIMULATION_VERSION_HISTORY[-1] == SIMULATION_VERSION\n'
         '      and "sim-2026.08-v4" in SIMULATION_VERSION_HISTORY)'),
    ]),
    ("test_run10b_a1_7_domain.py", [
        ('check(SIMULATION_VERSION == "sim-2026.08-v16",',
         'check(SIMULATION_VERSION_HISTORY[-1] == SIMULATION_VERSION,'),
    ]),
    ("test_run30_cat7_operational_route.py", [
        ('check(_res["simulation_version"] == "sim-2026.08-v16",',
         'check(_res["simulation_version"] == SIMULATION_VERSION,'),
    ]),
]


def main() -> int:
    changed = 0
    for name, edits in EDITS:
        p = TOOLS / name
        src = p.read_text()
        orig = src
        for old, new in edits:
            if old not in src:
                print(f"  !! fragment NOT FOUND in {name}: {old.splitlines()[0][:70]}")
                continue
            src = src.replace(old, new, 1)
        if src != orig:
            p.write_text(src)
            changed += 1
            print(f"  restated {name}")
    print(f"files restated: {changed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
