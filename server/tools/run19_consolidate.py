"""
Run 19, Gate 9. Consolidate the hundred scientific-result rows and build the audit artefacts.

INPUTS
  server/tools/run17/scientific_results.csv        the prior table, 21 assessed + 79 not reached
  server/tools/run17/categories/category_*.csv     this run's eight category result files

VALIDATION BEFORE CONSOLIDATION, which the owner's Gate 5 requires of the integrating agent:
  every category file has exactly the 29-column contract;
  every disposition is in the allowed vocabulary;
  a row records a production change only if its module is in the declared Run-20
    manifest, and every module in that manifest records one;
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
sys.path.insert(0, str(HERE.parent))          # server/, for the registry
sys.path.insert(0, str(HERE / "run17"))

from run20_production_changes import expected_flag  # noqa: E402
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
    print(f"prior table: {len(prior)} rows")

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
            # RUN 20. Run 19 changed no production file and this refused any row claiming
            # otherwise. Run 20 is authorized to change production, so the guard is narrowed to
            # the declared manifest rather than removed: an undeclared production change and an
            # undelivered declared fix both still fail here.
            if r["production_change_made"] != expected_flag(mid):
                fail(f"{path.name} row {mid} records production_change_made="
                     f"{r['production_change_made']!r} but the declared Run-20 manifest expects "
                     f"{expected_flag(mid)!r}")
            if not r["finding_summary"].strip():
                fail(f"{path.name} row {mid} has an empty finding summary")
            if mid in newly:
                fail(f"{mid} appears in two category files, the second being {path.name}")
            newly[mid] = r
        per_file[path.name] = [r["module_id"] for r in rows]
        print(f"  validated {path.name}: {len(rows)} rows")

    # ---------------------------------------------------------------- activation, from the code
    #
    # The activation column is a FACT ABOUT THE REGISTRY and must not be typed by hand into a
    # category file. An earlier version of this run did type it by hand and recorded four
    # concept-only modules as advisory when the registry has them disabled, in the very table
    # whose purpose includes proving that concept-only activation is zero. It is now checked
    # against the registry and consolidation refuses on any disagreement.
    from app.simulation import registry as REG  # noqa: E402
    code_id = {t["module_id"]: t["code_id"] for t in population()}
    mismatched = []
    for mid, r in newly.items():
        actual = REG.activation_state(code_id[mid])
        stated = r["operational_activation"]
        if actual == "DISABLED_UNSAFE" and stated != "DISABLED_UNSAFE":
            mismatched.append(f"{mid}: the registry has it {actual} and the row says {stated}")
        if actual != "DISABLED_UNSAFE" and stated == "DISABLED_UNSAFE":
            mismatched.append(f"{mid}: the row says DISABLED_UNSAFE and the registry has it "
                              f"{actual}")
    if mismatched:
        fail("a result row's activation state disagrees with the registry:\n  "
             + "\n  ".join(mismatched))
    print(f"  activation column agrees with the registry on all {len(newly)} new rows")

    # ---------------------------------------------------------------- reconcile the population
    rec = reconciliation()
    if rec["total_targets"] != 100 or rec["unique_module_ids"] != 100:
        fail(f"the population does not reconcile to 100: {rec}")
    targets = [t["module_id"] for t in population()]
    target_set = set(targets)

    # The prior-assessed set is whatever the category files do NOT cover. Deriving it this way
    # rather than from the not-reached marker makes a re-run idempotent: consolidating twice
    # gives the same table instead of refusing because the marker is already gone.
    prior_assessed = {r["module_id"]: r for r in prior if r["module_id"] not in newly}
    if len(prior_assessed) != 21:
        fail(f"{len(prior_assessed)} prior-assessed rows, expected 21")
    still_unreached = [r["module_id"] for r in prior_assessed.values()
                       if r["scientific_disposition"] in (NOT_REACHED, "NOT_ASSESSED", "")]
    if still_unreached:
        fail(f"these prior rows are still unassessed and no category file covers them: "
             f"{sorted(still_unreached)}")
    if set(prior_assessed) | set(newly) != target_set:
        missing = sorted(target_set - (set(prior_assessed) | set(newly)))
        extra = sorted((set(prior_assessed) | set(newly)) - target_set)
        fail(f"the union of prior and new does not equal the hundred targets. "
             f"Missing: {missing}. Unexpected: {extra}")
    print(f"  {len(prior_assessed)} prior-assessed rows carried forward, "
          f"{len(newly)} newly assessed")

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
