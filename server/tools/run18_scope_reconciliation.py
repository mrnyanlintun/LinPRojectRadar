#!/usr/bin/env python3
"""
RUN 18, GATE 1. MECHANICAL SCOPE RECONCILIATION.

Proves, from the current authoritative registry and the committed Run-17 results matrix, that:

  * the 100 Run-18 scientific targets are exactly the Run-17 population (96 project-level
    registered modules, minus Material Cost Variance, plus 5 portfolio modules);
  * the assessed set and the not-reached set partition those 100 exactly;
  * |assessed| + |not reached| = 100 with an empty intersection and an empty symmetric
    difference against the registry-derived population;
  * Material Cost Variance is registered and is NOT one of the 100 rows.

IDENTITY RULES, carried forward and enforced here rather than trusted:
  * `old_id` in p0-baseline/module_renumbering_map.csv is NOT the canonical key. Run 17 proved
    two retired alias rows displace every later id by one, so `old_id` 3.4 is Labor Productivity
    Index while the v0.5 key 3.4 is Material Cost Variance. Driving the exclusion off `old_id`
    would exclude the wrong module and execute the disabled one. population.py derives identity
    from `new_id` with the group letter mapped to the category number, reconciled BY MODULE NAME
    against the 101-name specification, and raises if the two ever disagree.
  * Identifiers are strings everywhere. This script asserts that the float-collision guard still
    reports the five pairs it must (1.1/1.10, 2.1/2.10, 4.1/4.10, 7.1/7.10, 7.2/7.20), so a
    future refactor that silently starts parsing ids as floats fails here.

Emits code_audit/run18_scope_reconciliation.csv and a canonical RESULT line.
"""
from __future__ import annotations
# Run 137, Item 2: artefact writes route to the Run 135C scratch root by default.
import os as _f10_os, sys as _f10_sys  # noqa: E402
_f10_sys.path.insert(0, _f10_os.path.join(
    _f10_os.path.dirname(_f10_os.path.abspath(__file__)), "..", "tools"))
_f10_sys.path.insert(0, _f10_os.path.dirname(_f10_os.path.abspath(__file__)))
from artifact_write import artifact_out  # noqa: E402

import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tools.run17 import population  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
RESULTS = ROOT / "server" / "tools" / "run17" / "scientific_results.csv"
OUT = ROOT / "code_audit" / "run18_scope_reconciliation.csv"

NOT_REACHED = "NOT_REACHED_IN_THIS_RUN"

passed = total = 0
rows: list[list[str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    global passed, total
    total += 1
    if ok:
        passed += 1
        print(f"  PASS  {label}")
    else:
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))
    rows.append([label, "PASS" if ok else "FAIL", detail])


def main() -> int:
    rec = population.reconciliation()
    pop = population.population()
    pop_keys = [m["module_id"] for m in pop]

    # ---- the registry-derived population -----------------------------------
    check(rec["mapping_problems"] == [],
          "the registry-to-specification name mapping raises no problem",
          str(rec["mapping_problems"]))
    check(rec["project_level"] == 96, "the registry declares 96 project-level modules",
          str(rec["project_level"]))
    check(rec["portfolio_level"] == 5, "the registry declares 5 portfolio modules",
          str(rec["portfolio_level"]))
    check(rec["excluded_key"] == "3.4" and rec["excluded_name"] == "Material Cost Variance",
          "the excluded key 3.4 resolves to Material Cost Variance, not Labor Productivity Index",
          f"{rec['excluded_key']} -> {rec['excluded_name']}")
    check(rec["total_targets"] == 100, "96 minus 1 plus 5 gives 100 scientific targets",
          str(rec["total_targets"]))
    check(len(set(pop_keys)) == 100, "the 100 targets carry 100 unique canonical ids",
          str(len(set(pop_keys))))
    check("3.4" not in pop_keys, "Material Cost Variance is not one of the 100 target rows")

    # ---- the float guard, still active -------------------------------------
    expected_collisions = {"1.1 vs 1.10", "2.1 vs 2.10", "4.1 vs 4.10",
                           "7.1 vs 7.10", "7.2 vs 7.20"}
    check(set(rec["float_coercion_would_collide"]) == expected_collisions,
          "the five id pairs that float coercion would merge are still detected",
          str(rec["float_coercion_would_collide"]))

    # ---- the Run-17 committed matrix, partitioned --------------------------
    committed = list(csv.DictReader(RESULTS.open(encoding="utf-8")))
    committed_keys = [r["module_id"] for r in committed]
    assessed = [r["module_id"] for r in committed
                if r["scientific_disposition"] != NOT_REACHED]
    unreached = [r["module_id"] for r in committed
                 if r["scientific_disposition"] == NOT_REACHED]

    check(len(committed) == 100, "the committed Run-17 matrix carries 100 rows",
          str(len(committed)))
    check(len(set(committed_keys)) == 100, "with 100 unique ids", str(len(set(committed_keys))))
    check(set(committed_keys) == set(pop_keys),
          "the committed matrix covers exactly the registry-derived population",
          str(sorted(set(committed_keys) ^ set(pop_keys))))
    check(len(assessed) == 21, "exactly 21 rows carry a scientific disposition",
          str(len(assessed)))
    check(len(unreached) == 79, f"exactly 79 rows are {NOT_REACHED}", str(len(unreached)))
    check(set(assessed) & set(unreached) == set(),
          "the assessed and unreached sets are disjoint")
    check(set(assessed) | set(unreached) == set(pop_keys),
          "their union is exactly the 100-target population",
          str(sorted((set(assessed) | set(unreached)) ^ set(pop_keys))))
    check(len(assessed) + len(unreached) == 100, "21 + 79 = 100",
          f"{len(assessed)} + {len(unreached)}")
    check(all(r["scientific_disposition"].strip() for r in committed),
          "no committed row carries a blank disposition")

    for k in sorted(assessed):
        rows.append([f"assessed:{k}", "ASSESSED", ""])
    for k in sorted(unreached):
        rows.append([f"unreached:{k}", NOT_REACHED, ""])

    artifact_out(OUT.parent).mkdir(parents=True, exist_ok=True)
    with artifact_out(OUT).open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["item", "outcome", "detail"])
        w.writerows(rows)
    print(f"\nwrote {OUT}")
    print(f"\nRESULT: {passed}/{total} checks passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
