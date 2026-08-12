"""
Run 17 artifact builder.

Writes the three Run-17 evidence artifacts with one row per Run-17 target, every time:

  server/tools/run17/method_cards.json      one method card per target
  server/tools/run17/scientific_results.csv the results matrix, exactly 100 rows
  server/tools/run17/source_ledger.csv      the literature/authority ledger

Findings live in findings.py, keyed by Module_ID_Text_Key. A target with no entry there is
written with disposition NOT_REACHED_IN_THIS_RUN rather than a guess. That is the whole point of
the split: the artifact is always complete and always honest about which rows carry real work.

This builder writes AUDIT ARTIFACTS ONLY. It imports nothing from server/app except through
population.py's read of the registry CSV, and it changes no production file.
"""

from __future__ import annotations

import csv
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from population import population, reconciliation  # noqa: E402
from findings import FINDINGS, SOURCE_LEDGER, METHOD_CARD_DEFAULTS  # noqa: E402

#: Exactly the columns the owner specification section 26 requires, in that order.
RESULT_COLUMNS = [
    "module_id", "module_name", "category", "basis_class", "operational_activation",
    "voting_status", "primary_method_source", "canonical_structure_required",
    "canonical_structure_present", "implementation_verified", "known_answer_pass",
    "boundary_pass", "missingness_pass", "invariant_pass", "stochastic_diagnostics_pass",
    "reproducibility_pass", "parameter_provenance_status", "calibration_status",
    "threshold_status", "empirical_validation_status", "regulatory_snapshot",
    "cat9_qualification_status", "lineage_status", "scientific_disposition",
    "production_change_made", "finding_summary", "required_next_action", "test_names",
    "evidence_paths",
]

#: The value written into every unreached row. Not a disposition that implies any assurance.
NOT_REACHED = "NOT_REACHED_IN_THIS_RUN"

#: Fields that carry an assurance claim. An unreached row gets NOT_ASSESSED in each, never a
#: blank and never a favourable default, so no reader can mistake silence for a pass.
ASSURANCE_FIELDS = [
    "canonical_structure_present", "implementation_verified", "known_answer_pass",
    "boundary_pass", "missingness_pass", "invariant_pass", "stochastic_diagnostics_pass",
    "reproducibility_pass", "parameter_provenance_status", "calibration_status",
    "threshold_status", "empirical_validation_status", "cat9_qualification_status",
    "lineage_status",
]


def build_rows() -> list[dict[str, str]]:
    rows = []
    for target in population():
        key = target["module_id"]
        found = FINDINGS.get(key)
        row = {c: "" for c in RESULT_COLUMNS}
        row["module_id"] = key
        row["module_name"] = target["module_name"]
        row["category"] = target["category"]
        row["production_change_made"] = "no"
        row["regulatory_snapshot"] = "n/a"
        if found is None:
            for field in ASSURANCE_FIELDS:
                row[field] = "NOT_ASSESSED"
            row["basis_class"] = "NOT_ASSESSED"
            row["canonical_structure_required"] = "NOT_ASSESSED"
            row["primary_method_source"] = "NOT_ASSESSED"
            row["scientific_disposition"] = NOT_REACHED
            row["finding_summary"] = (
                "Not reached in Run 17. No scientific determination of any kind is made for "
                "this module by this run, and no prior run's determination is carried forward "
                "into this row as though Run 17 had confirmed it."
            )
            row["required_next_action"] = (
                "Execute the Run-17 protocol for this module in the follow-up run.")
            row["test_names"] = "none"
            row["evidence_paths"] = "none"
        else:
            row.update({k: v for k, v in found.items() if k in RESULT_COLUMNS})
        rows.append(row)
    return rows


def write_results(rows: list[dict[str, str]]) -> None:
    path = HERE / "scientific_results.csv"
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=RESULT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def write_method_cards() -> None:
    cards = {}
    for target in population():
        key = target["module_id"]
        card = dict(METHOD_CARD_DEFAULTS)
        card.update({
            "module_id": key,
            "module_name": target["module_name"],
            "category": target["category"],
            "code_id": target["code_id"],
            "operationally_disabled_concept_only": target["concept_only"] == "yes",
        })
        found = FINDINGS.get(key)
        if found is None:
            card["scientific_disposition"] = NOT_REACHED
            card["evidence"] = "Not reached in Run 17."
        else:
            card.update(found.get("method_card", {}))
            card["scientific_disposition"] = found["scientific_disposition"]
            card["basis_class"] = found["basis_class"]
            card["current_code_location"] = found.get("code_location", "")
            card["current_implementation_summary"] = found.get("finding_summary", "")
            card["primary_source"] = found.get("primary_method_source", "")
            card["evidence"] = found.get("evidence_paths", "")
        cards[key] = card
    (HERE / "method_cards.json").write_text(
        json.dumps(cards, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_source_ledger() -> None:
    path = HERE / "source_ledger.csv"
    cols = ["source_id", "citation", "doi_or_identifier", "source_tier", "retrieved",
            "provenance_note", "used_for_modules"]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=cols)
        writer.writeheader()
        for entry in SOURCE_LEDGER:
            writer.writerow({c: entry.get(c, "") for c in cols})


def main() -> int:
    rec = reconciliation()
    if rec["mapping_problems"]:
        print("POPULATION MAPPING PROBLEMS:")
        for p in rec["mapping_problems"]:
            print("  " + p)
        return 1
    if rec["total_targets"] != 100 or rec["unique_module_ids"] != 100:
        print(f"POPULATION IS NOT 100: {rec['total_targets']} targets, "
              f"{rec['unique_module_ids']} unique")
        return 1
    rows = build_rows()
    assert len(rows) == 100
    assert len({r["module_id"] for r in rows}) == 100
    write_results(rows)
    write_method_cards()
    write_source_ledger()

    reached = [r for r in rows if r["scientific_disposition"] != NOT_REACHED]
    print(f"scientific_results.csv: {len(rows)} rows, {len(rows[0])} columns")
    print(f"method_cards.json: 100 cards")
    print(f"source_ledger.csv: {len(SOURCE_LEDGER)} sources")
    print(f"reached: {len(reached)}/100   not reached: {100 - len(reached)}")
    from collections import Counter
    for disp, n in sorted(Counter(r["scientific_disposition"] for r in rows).items(),
                          key=lambda kv: -kv[1]):
        print(f"  {n:3d}  {disp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
