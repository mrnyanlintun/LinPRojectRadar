"""
THE FIFTY-ONE MODULES RUN 96 REMOVED, STATED BY NAME.

WHY THIS LIST IS WRITTEN OUT WHEN EVERY OTHER POPULATION IN THIS INSTRUMENT IS DERIVED.

Every count of modules IN SERVICE is derived from `p0-baseline/module_renumbering_map.csv`,
because a stated live population drifts from the computed one and this programme has made that
mistake nine times. This list is the opposite case and the reasoning inverts.

A check that asks the registry which modules are absent, and then asserts that those modules are
absent, cannot fail. Run 96 measured exactly that: with `A1.1` written back into the CSV, both
`test_run6_known_answer` and `test_run17_scientific_methods` went GREEN, because each had derived
its expectation of absence from the very file the restoration changed. The suites adapted to the
regression instead of reporting it.

So the ORACLE for a removal must be independent of the thing it audits, and for a removal the only
independent oracle is the record of what was removed. This file is that record. It is a historical
fact about one run, it does not change when the registry changes, and it is what makes putting a
retired row back a FAILURE rather than a silent widening.

It states nothing about which modules are in service. Nothing derives a live count from it.
"""
from __future__ import annotations

#: The identifiers whose registry rows, dispatch entries and specifications Run 96 deleted.
#: Established at run time from `registry.retired_modules()` at commit e852c46, less Group D.
REMOVED_AT_RUN96: tuple[str, ...] = (
    "A1.1", "A1.3", "A1.4", "A1.10",
    "A2.2", "A2.3", "A2.4", "A2.5", "A2.6", "A2.10", "A2.11",
    "A3.1", "A3.4", "A3.7", "A3.8", "A3.9",
    "A4.1", "A4.10",
    "A5.1", "A5.2", "A5.3", "A5.4", "A5.5", "A5.6", "A5.7", "A5.8",
    "B2.1", "B2.2", "B2.3", "B2.4", "B2.5", "B2.6", "B2.7", "B2.8", "B2.9",
    "B2.10", "B2.11", "B2.12", "B2.13", "B2.14", "B2.15", "B2.16", "B2.17",
    "B2.19", "B2.20",
    "B4.1", "B4.2", "B4.4", "B4.5", "B4.6", "B4.7",
)

#: The five Group D rows Run 96 STOPPED on and deliberately left in service-marking. They are
#: still retired, they still resolve, and the Run 96 report states why. Named here so that a
#: reader of this file is not left thinking the retirement roster is empty.
STOPPED_AT_RUN96: tuple[str, ...] = ("D1.1", "D1.2", "D1.3", "D1.4", "D1.5")


def assert_removed(check, registry) -> None:
    """
    Assert the removal against the stated roster. `check(name, condition, detail)`.

    This is the check that goes red if a removed row is ever written back.
    """
    idx = registry.registry_index()
    back = sorted(m for m in REMOVED_AT_RUN96 if m in idx)
    check("every module Run 96 removed is still absent from the registry", not back,
          f"BACK IN THE REGISTRY: {back}" if back else "")
    check("the Run 96 removal roster is the fifty-one it records -- not silently shortened",
          len(REMOVED_AT_RUN96) == 51 and len(set(REMOVED_AT_RUN96)) == 51,
          str(len(REMOVED_AT_RUN96)))
    still = sorted(m for m in STOPPED_AT_RUN96 if m not in idx)
    check("and the five Group D rows Run 96 stopped on are still there, still resolving",
          not still, f"MISSING: {still}" if still else "")
    refused = []
    for mid in REMOVED_AT_RUN96:
        try:
            registry.run_module(mid, {}, lambda: 0.5, "2025-06-30")
        except registry.MissingModuleError:
            refused.append(mid)
        except Exception:                                              # noqa: BLE001
            pass
    check("and the dispatcher refuses every one of them by name",
          len(refused) == len(REMOVED_AT_RUN96),
          f"did not refuse: {sorted(set(REMOVED_AT_RUN96) - set(refused))}")
