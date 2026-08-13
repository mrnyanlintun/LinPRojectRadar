"""
Run 19, Gate 9. Consolidate the hundred scientific-result rows and build the audit artefacts.

INPUTS
  server/tools/run17/scientific_results.csv        the prior table, 21 assessed + 79 not reached
  server/tools/run17/categories/category_*.csv     this run's eight category result files

VALIDATION BEFORE CONSOLIDATION, which the owner's Gate 5 requires of the integrating agent:
  every category file has exactly the 29-column contract;
  every disposition is in the allowed vocabulary;
  no row records a production change;
  no module id appears in two category files;
  the union of prior-assessed and newly-assessed ids is exactly the hundred targets;
  no id is lost or gained, and no id collides under float coercion.

OUTPUTS
  server/tools/run17/scientific_results.csv        rebuilt, 100 complete rows
  code_audit/run19_final_100_reconciliation.csv
  code_audit/run19_remaining_79_results.csv
  code_audit/run19_fault_injection_results.csv
  code_audit/run19_next_remediation_queue.csv
"""

from __future__ import annotations

import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE / "run17"))

from audit_harness import ALLOWED_DISPOSITIONS, RESULT_HEADER  # noqa: E402
from population import population, reconciliation              # noqa: E402

RESULTS = HERE / "run17" / "scientific_results.csv"
CATEGORIES = HERE / "run17" / "categories"
AUDIT = ROOT / "code_audit"
NOT_REACHED = "NOT_REACHED_IN_THIS_RUN"


def fail(msg: str) -> None:
    print(f"CONSOLIDATION REFUSED: {msg}")
    sys.exit(1)


def read(path: pathlib.Path) -> list[dict]:
    return list(csv.DictReader(path.open(encoding="utf-8-sig")))


def main() -> int:
    prior = read(RESULTS)
    prior_assessed = {r["module_id"]: r for r in prior
                      if r["scientific_disposition"] != NOT_REACHED}
    prior_unreached = {r["module_id"] for r in prior
                       if r["scientific_disposition"] == NOT_REACHED}
    print(f"prior table: {len(prior)} rows, {len(prior_assessed)} assessed, "
          f"{len(prior_unreached)} not reached")

    # ---------------------------------------------------------------- validate each category
    newly: dict[str, dict] = {}
    per_file: dict[str, list[str]] = {}
    for path in sorted(CATEGORIES.glob("category_*_results.csv")):
        rows = read(path)
        if not rows:
            fail(f"{path.name} is empty")
        for r in rows:
            if list(r) != RESULT_HEADER:
                fail(f"{path.name} row {r.get('module_id')} does not have the 29-column "
                     f"contract; got {len(r)} columns")
            mid = r["module_id"]
            if r["scientific_disposition"] not in ALLOWED_DISPOSITIONS:
                fail(f"{path.name} row {mid} carries disposition "
                     f"{r['scientific_disposition']!r}, which is not in the allowed vocabulary")
            if r["production_change_made"] != "no":
                fail(f"{path.name} row {mid} records a production change")
            if not r["finding_summary"].strip():
                fail(f"{path.name} row {mid} has an empty finding summary")
            if mid in newly:
                fail(f"{mid} appears in two category files, the second being {path.name}")
            newly[mid] = r
        per_file[path.name] = [r["module_id"] for r in rows]
        print(f"  validated {path.name}: {len(rows)} rows")

    # ---------------------------------------------------------------- reconcile the population
    rec = reconciliation()
    if rec["total_targets"] != 100 or rec["unique_module_ids"] != 100:
        fail(f"the population does not reconcile to 100: {rec}")
    targets = [t["module_id"] for t in population()]
    target_set = set(targets)

    if set(newly) != prior_unreached:
        missing = sorted(prior_unreached - set(newly))
        extra = sorted(set(newly) - prior_unreached)
        fail(f"the newly assessed set is not exactly the previously unreached set. "
             f"Still unassessed: {missing}. Assessed but not previously unreached: {extra}")
    if not set(prior_assessed) | set(newly) == target_set:
        fail("the union of prior and new does not equal the hundred targets")

    # ---------------------------------------------------------------- build the hundred rows
    final: list[dict] = []
    for t in population():
        mid = t["module_id"]
        row = dict(prior_assessed.get(mid) or newly[mid])
        row["module_id"] = mid
        row["module_name"] = t["module_name"]
        final.append({c: row.get(c, "") for c in RESULT_HEADER})

    if len(final) != 100:
        fail(f"{len(final)} rows built, not 100")
    ids = [r["module_id"] for r in final]
    if len(set(ids)) != 100:
        fail("the hundred rows do not carry a hundred unique ids")
    if any(r["scientific_disposition"] in (NOT_REACHED, "NOT_ASSESSED", "") for r in final):
        fail("a row still carries a not-reached, not-assessed or blank disposition")
    if "3.4" in set(ids):
        fail("Material Cost Variance appears as a scientific-result row and must not")
    # Float coercion would merge these pairs, so prove the text keys survived.
    for a, b in (("1.1", "1.10"), ("2.1", "2.10"), ("4.1", "4.10"), ("7.1", "7.10"),
                 ("7.2", "7.20")):
        if not (a in set(ids) and b in set(ids)):
            fail(f"{a} and {b} did not both survive as distinct text keys")

    with RESULTS.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=RESULT_HEADER)
        w.writeheader()
        for r in final:
            w.writerow(r)
    print(f"\nwrote {RESULTS} with {len(final)} rows")

    # ---------------------------------------------------------------- audit artefacts
    AUDIT.mkdir(exist_ok=True)

    with (AUDIT / "run19_final_100_reconciliation.csv").open(
            "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["module_id", "module_name", "category", "assessed_in",
                    "scientific_disposition", "operational_activation", "voting_status"])
        for r in final:
            w.writerow([r["module_id"], r["module_name"], r["category"],
                        "Run 17" if r["module_id"] in prior_assessed else "Run 19",
                        r["scientific_disposition"], r["operational_activation"],
                        r["voting_status"]])

    with (AUDIT / "run19_remaining_79_results.csv").open(
            "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=RESULT_HEADER)
        w.writeheader()
        for r in final:
            if r["module_id"] in newly:
                w.writerow(r)

    faults: list[dict] = []
    cols = ["module_id", "fault", "file_mutated", "bytes_changed", "test_turned_red",
            "red_test_name", "restored", "notes"]
    for path in sorted(CATEGORIES.glob("category_*_faults.csv")):
        for r in read(path):
            r["category_file"] = path.name
            faults.append(r)
    with (AUDIT / "run19_fault_injection_results.csv").open(
            "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols + ["category_file"])
        w.writeheader()
        for r in faults:
            w.writerow({c: r.get(c, "") for c in cols + ["category_file"]})

    # ---------------------------------------------------------------- counts
    from collections import Counter
    counts = Counter(r["scientific_disposition"] for r in final)
    print("\nscientific disposition counts over the final hundred rows:")
    for d, n in counts.most_common():
        print(f"  {n:>3}  {d}")
    print(f"\nNOT_REACHED remaining: "
          f"{sum(1 for r in final if r['scientific_disposition'] == NOT_REACHED)}")
    print(f"NOT_ASSESSED remaining: "
          f"{sum(1 for r in final if r['scientific_disposition'] == 'NOT_ASSESSED')}")
    print(f"blank dispositions: "
          f"{sum(1 for r in final if not r['scientific_disposition'].strip())}")
    print(f"rows recording a production change: "
          f"{sum(1 for r in final if r['production_change_made'] != 'no')}")
    reds = sum(1 for f in faults if f.get("test_turned_red") == "YES")
    print(f"\nfault injections recorded: {len(faults)}, producing a named red: {reds}")
    print(f"fault injections that crashed instead of failing and were replaced: "
          f"{sum(1 for f in faults if f.get('test_turned_red') == 'NO_CRASHED_INSTEAD')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
