"""Builds code_audit/run20_master_remediation_register.csv mechanically from the Run-19
committed artifacts. Nothing here is hand-entered per module: every field is derived from
server/tools/run17/scientific_results.csv and code_audit/run19_next_remediation_queue.csv,
so the register cannot drift from the audit it claims to summarise.

Run twice, it produces the same bytes. It is the single source of the Run-20 headline counts.
"""
from __future__ import annotations
# Run 137, Item 2: artefact writes route to the Run 135C scratch root by default.
import os as _f10_os, sys as _f10_sys  # noqa: E402
_f10_sys.path.insert(0, _f10_os.path.join(
    _f10_os.path.dirname(_f10_os.path.abspath(__file__)), "..", "tools"))
_f10_sys.path.insert(0, _f10_os.path.dirname(_f10_os.path.abspath(__file__)))
from artifact_write import artifact_out  # noqa: E402

import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
RESULTS = os.path.join(ROOT, "server", "tools", "run17", "scientific_results.csv")
QUEUE = os.path.join(ROOT, "code_audit", "run19_next_remediation_queue.csv")
TRANSITIONS = os.path.join(ROOT, "code_audit", "run20_disposition_transitions.csv")
#: The Run-19 dispositions, frozen from the results table as it stood at commit 772ad8f before
#: Run 20 changed anything. The register reports where each module STARTED, and the live results
#: table reports where it stands now, so a fix can never quietly rewrite its own baseline.
BASELINE = os.path.join(ROOT, "code_audit", "run20_run19_baseline_dispositions.csv")
CYCLES = os.path.join(ROOT, "code_audit", "run20_defect_class_cycles.csv")
OUT = os.path.join(ROOT, "code_audit", "run20_master_remediation_register.csv")

COLUMNS = [
    "module_id", "module_name", "category", "Run19_disposition", "Run19_root_cause",
    "scientific_authority", "required_structure", "current_structure",
    "implementation_defect", "parameter_gap", "threshold_gap", "calibration_gap",
    "Category9_gap", "lineage_gap", "regulatory_gap", "label_gap",
    "empirical_validation_gap", "owner_decision_needed", "remediation_authorized",
    "priority", "cycle_number", "status", "fix_commit", "post_fix_disposition",
    "tests", "mutation_proof", "neighbour_sweep", "notes",
]

# Disposition -> the root-cause vocabulary of the owner prompt section 10. One disposition can
# imply more than one root cause; the queue's own priority letter disambiguates the rest.
ROOT_CAUSE = {
    "IMPLEMENTATION_DEFECT": "METHOD_IMPLEMENTATION_DEFECT",
    "METHOD_LABEL_MISMATCH": "METHOD_LABEL_MISMATCH",
    "MISSING_CANONICAL_DATA_STRUCTURE": "CANONICAL_STRUCTURE_MISSING",
    "PARAMETER_PROVENANCE_BLOCKED": "PARAMETER_PROVENANCE_GAP",
    "THRESHOLD_CALIBRATION_BLOCKED": "THRESHOLD_CALIBRATION_GAP",
    "METHOD_PASS_CALIBRATION_PENDING": "THRESHOLD_CALIBRATION_GAP",
    "REGULATORY_VERSION_BLOCKED": "REGULATORY_VERSION_GAP",
    "OWNER_DECISION_REQUIRED": "OWNER_POLICY_GAP",
    "FUTURE_RESEARCH_ONLY": "FUTURE_RESEARCH_ONLY",
    "CORRECT_PROXY_ONLY": "METHOD_LABEL_MISMATCH",
    "CORRECT_ABSTENTION": "",
    "SCIENTIFIC_PASS": "",
}

# A remediation is authorized when the correction is available inside the repository from the
# committed specification alone. It is BLOCKED when it needs something the run cannot lawfully
# obtain: owner judgement, real field outcomes, or an external authority.
BLOCKED_BY = {
    "OWNER_DECISION_REQUIRED": "BLOCKED_OWNER_DECISION",
    "PARAMETER_PROVENANCE_BLOCKED": "BLOCKED_NO_DEFENSIBLE_PROVENANCE",
    "THRESHOLD_CALIBRATION_BLOCKED": "BLOCKED_NO_CALIBRATION_DATA",
    "METHOD_PASS_CALIBRATION_PENDING": "BLOCKED_NO_EMPIRICAL_DATA",
    "FUTURE_RESEARCH_ONLY": "BLOCKED_APPLICABILITY_NOT_ESTABLISHED",
}


def yn(flag: bool) -> str:
    return "yes" if flag else "no"


def load_progress() -> dict[str, dict]:
    """
    Run-20 progress, read from the transition log rather than typed into the register. A module
    is CLOSED_RUN20 only if a transition was actually applied to the results table, so the
    register cannot claim a fix that did not happen.
    """
    if not os.path.exists(TRANSITIONS):
        return {}
    return {r["module_id"]: r for r in csv.DictReader(open(TRANSITIONS, encoding="utf-8"))}


def main() -> None:
    results = list(csv.DictReader(open(RESULTS, encoding="utf-8")))
    queue = {r["module_id"]: r for r in csv.DictReader(open(QUEUE, encoding="utf-8"))}
    progress = load_progress()
    baseline = {r["module_id"]: r["run19_disposition"]
                for r in csv.DictReader(open(BASELINE, encoding="utf-8"))}
    assert len(results) == 100, f"expected 100 scientific rows, found {len(results)}"
    assert len({r["module_id"] for r in results}) == 100, "module ids are not unique"

    rows = []
    for r in results:
        mid = r["module_id"]
        q = queue.get(mid)
        disp = baseline.get(mid, r["scientific_disposition"])
        now = r["scientific_disposition"]
        done = progress.get(mid)
        priority = q["priority"] if q else "NONE"
        # Architectural targets ARCH.1/ARCH.2 live only in the queue, never in the 100 rows.
        blocked = BLOCKED_BY.get(disp, "")
        authorized = "no" if blocked else "yes"
        rows.append({
            "module_id": mid,
            "module_name": r["module_name"],
            "category": r["category"],
            "Run19_disposition": disp,
            "Run19_root_cause": ROOT_CAUSE.get(disp, ""),
            "scientific_authority": r["primary_method_source"],
            "required_structure": r["canonical_structure_required"],
            "current_structure": r["canonical_structure_present"],
            "implementation_defect": yn(r["implementation_verified"] == "no"),
            "parameter_gap": yn(r["parameter_provenance_status"] not in ("SOURCED", "n/a", "")),
            "threshold_gap": yn(r["threshold_status"] in
                                ("HEURISTIC_UNCALIBRATED", "UNSUPPORTED")),
            "calibration_gap": yn(r["calibration_status"] not in ("CALIBRATED", "n/a", "")),
            "Category9_gap": yn(r["cat9_qualification_status"] != "QUALIFIED"),
            "lineage_gap": yn(r["lineage_status"] not in ("TRACEABLE", "n/a", "")),
            "regulatory_gap": yn(disp == "REGULATORY_VERSION_BLOCKED"),
            "label_gap": yn(disp in ("METHOD_LABEL_MISMATCH", "CORRECT_PROXY_ONLY")),
            "empirical_validation_gap": yn(r["empirical_validation_status"] != "DONE"),
            "owner_decision_needed": yn(disp == "OWNER_DECISION_REQUIRED"),
            "remediation_authorized": authorized,
            "priority": priority,
            "cycle_number": done["cycle"] if done else "",
            "status": ("CLOSED_RUN20" if done else "OPEN" if q else "CLOSED_RUN19"),
            "fix_commit": "see code_audit/run20_defect_class_cycles.csv" if done else "",
            "post_fix_disposition": now if (done or not q) else "",
            "tests": r["test_names"],
            "mutation_proof": "",
            "neighbour_sweep": "",
            "notes": blocked or (q["required_action"] if q else "No Run-19 finding open."),
        })

    # The two architectural targets carry no scientific_results row of their own; they are the
    # Category-9 gate and the lineage control, and the register must not lose them.
    for mid in ("ARCH.1", "ARCH.2"):
        q = queue[mid]
        rows.append({c: "" for c in COLUMNS} | {
            "module_id": mid,
            "module_name": q["module_name"],
            "category": "ARCH",
            "Run19_disposition": q["scientific_disposition"],
            "Run19_root_cause": ("CATEGORY9_QUALIFICATION_GAP" if mid == "ARCH.1"
                                 else "LINEAGE_DEPENDENCE_GAP"),
            "scientific_authority": "Specification 22",
            "required_structure": "yes",
            "current_structure": "no",
            "Category9_gap": yn(mid == "ARCH.1"),
            "lineage_gap": yn(mid == "ARCH.2"),
            "remediation_authorized": "yes",
            "priority": q["priority"],
            "status": "OPEN",
            "notes": q["required_action"],
        })

    rows.sort(key=lambda r: (r["priority"], r["module_id"]))
    with open(artifact_out(OUT), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    print(f"RESULT: {len(rows)}/{len(rows)} register rows written")


if __name__ == "__main__":
    main()
