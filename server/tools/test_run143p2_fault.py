"""
RUN 143 PART 2 -- PROOF 13: prove it can fail.

A check that cannot fail proves nothing. This file BREAKS the carried marking three ways, one
at a time, observes the defect the owner named -- a carried reading indistinguishable from a
current one -- and restores. It asserts the failure, so a run in which the injection did NOT
produce the defect fails too: that would mean the marking is not what makes the difference.

    PYTHONPATH=. python tools/test_run143p2_fault.py

Clears __pycache__ under app/simulation/ on the way out.
"""
from __future__ import annotations

import datetime
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CUTOFF = datetime.date(2026, 6, 30)
FAILS: list[str] = []
TARGET = "A2.1"
HISTORY = [{"period": "P1",
            "modules": [{"module_id": TARGET, "category": "A2", "status_color": "Amber",
                         "evidence_metric": "P1's own sentence."}]}]


def check(name, ok, detail=""):
    print(("PASS  " if ok else "FAIL  ") + name + (("  -- " + detail) if detail else ""))
    if not ok:
        FAILS.append(name)


def clear_cache():
    for d in ROOT.rglob("__pycache__"):
        shutil.rmtree(d, ignore_errors=True)


def carried_row():
    """Compute the row in a FRESH interpreter state, so an injection is actually picked up."""
    for name in [m for m in sys.modules if m.startswith("app.")]:
        del sys.modules[name]
    from app.simulation.compute import compute_project
    res = compute_project({}, "fault", "P3", CUTOFF, project_id="PRJ-F",
                          prior_readings=HISTORY)
    return next((m for m in res["modules"] if m["module_id"] == TARGET), None)


def with_injection(path: pathlib.Path, old: str, new: str, label: str, observe):
    original = path.read_text()
    assert original.count(old) == 1, f"{label}: injection anchor is not unique"
    print(f"\n--- INJECTION: {label}")
    try:
        path.write_text(original.replace(old, new))
        clear_cache()
        observe(carried_row())
    finally:
        path.write_text(original)
        clear_cache()
    # And the restore must put it back, or every check after this one is meaningless.
    row = carried_row()
    check(f"RESTORED after {label}",
          row is not None and row.get("carried") is True
          and row.get("carried_from_period") == "P1")


# --------------------------------------------------------------- the baseline, before breaking
base = carried_row()
check("baseline: the carried reading is marked", base is not None and base.get("carried") is True)
check("baseline: it names its source period", base and base.get("carried_from_period") == "P1")
check("baseline: its sentence says it is carried",
      base and "Carried from P1" in (base.get("evidence_metric") or ""))

CF = ROOT / "app" / "simulation" / "carry_forward.py"


# 1. Break the marker itself. This is the exact defect: the band is published and NOTHING says
#    it is not this period's. `getModuleStatus` returns the band; `getModuleCarried` tests
#    `carried === true` and would return null; the row renders as current on every surface.
def observe_marker(row):
    check("13a: the reading is still published (the band still votes)",
          row is not None and row.get("status_color") == "Amber")
    check("13a: DEFECT OBSERVED -- the carried marker is gone, so the client's "
          "getModuleCarried test (carried === true) fails and it renders as CURRENT",
          row is not None and row.get("carried") is not True,
          f"carried={row.get('carried')!r}")


with_injection(CF, '            new["carried"] = True\n',
               '            new["carried"] = False  # RUN 143 FAULT INJECTION\n',
               "the carried marker is falsified", observe_marker)


# 2. Break the sentence. The band and the flag survive, but `evidence_metric` -- the field the
#    export's flat column and every tooltip read -- becomes the earlier period's sentence with
#    nothing marking it, so a surface reading only that field shows a stale finding as current.
def observe_sentence(row):
    check("13b: DEFECT OBSERVED -- the published sentence no longer says it is carried",
          row is not None and "Carried from" not in (row.get("evidence_metric") or ""),
          repr((row.get("evidence_metric") or "")[:60]))
    check("13b: and it is the earlier period's sentence presented as this period's",
          row is not None and row.get("evidence_metric") == "P1's own sentence.")


with_injection(CF,
               '''            new["evidence_metric"] = carried_sentence(str(period),
                                                      prior.get("evidence_metric"))''',
               '''            new["evidence_metric"] = prior.get("evidence_metric")  # RUN 143 FAULT''',
               "the carried sentence is replaced by the bare original", observe_sentence)


# 3. Break the period name. The order forbids "the previous period" precisely because a removed
#    period makes it false; this injection shows what a label that does not name its source
#    looks like, and that nothing downstream can recover the period once it is gone.
def observe_period(row):
    check("13c: DEFECT OBSERVED -- the row no longer names the period it came from",
          row is not None and row.get("carried_from_period") != "P1",
          f"carried_from_period={row.get('carried_from_period')!r}")
    check("13c: the export's flat column would therefore be empty for a carried reading",
          row is not None and not row.get("carried_from_period"))


with_injection(CF, '            new["carried_from_period"] = period\n',
               '            new["carried_from_period"] = None  # RUN 143 FAULT INJECTION\n',
               "the source period is dropped", observe_period)

# ---------------------------------------------------- the exclusion, broken and observed too
def observe_exclusion(row):
    from app.simulation.compute import compute_project
    hist = [{"period": "P1", "modules": [{"module_id": "C1.5", "category": "C1",
                                          "status_color": "Green",
                                          "evidence_metric": "an earlier Green"}]}]
    res = compute_project({}, "fault", "P3", CUTOFF, project_id="PRJ-F", prior_readings=hist)
    got = [m for m in res["modules"] if m["module_id"] == "C1.5"]
    check("13d: DEFECT OBSERVED -- with the exemption list emptied, C1.5 (which can never "
          "band at all) publishes a carried Green", bool(got), f"{len(got)} row(s)")


with_injection(CF, 'NEVER_CARRY_MODULES: frozenset[str] = frozenset({"C1.5", "B1.1", "B1.2"})',
               'NEVER_CARRY_MODULES: frozenset[str] = frozenset()  # RUN 143 FAULT INJECTION',
               "the by-id exemption list is emptied", observe_exclusion)

# and prove the exemption is back
from app.simulation.carry_forward import NEVER_CARRY_MODULES        # noqa: E402
check("RESTORED: the exemption list holds its three modules",
      NEVER_CARRY_MODULES == frozenset({"C1.5", "B1.1", "B1.2"}), str(sorted(NEVER_CARRY_MODULES)))

clear_cache()
print("\n" + ("EVERY INJECTION PRODUCED THE DEFECT AND EVERY RESTORE HELD"
              if not FAILS else f"{len(FAILS)} FAILED: {FAILS}"))
sys.exit(1 if FAILS else 0)
