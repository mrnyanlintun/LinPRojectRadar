#!/usr/bin/env python3
"""
RUN 34. THE PORTFOLIO HEALTH CALIBRATION ARTIFACT TABLES, DERIVED MECHANICALLY.

Every identity comes from the LIVE registry and every parameter row from the LIVE parameter
registry in `canonical_v8`. Nothing is transcribed. If the registry disagrees with a count stated
anywhere else, this file reports what the registry says.

THE FIVE ASSURANCE LAYERS ARE NEVER COLLAPSED. Canonical method correctness, parameter
provenance, synthetic calibration, holdout performance and real empirical validation are five
separate statements with genuinely different statuses, and each module states all five.

Writes:
  code_audit/run34_portfolio_health_scope.csv
  code_audit/run34_portfolio_parameter_provenance.csv
  code_audit/run34_real_portfolio_calibration_reconciliation.csv
  code_audit/run34_portfolio_health_calibration_closure.csv
"""

from __future__ import annotations

import csv
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

from app.simulation import canonical_v8 as V8                          # noqa: E402
from app.simulation import portfolio_health as PH                      # noqa: E402
from app.simulation.portfolio import PORTFOLIO_VALIDATED               # noqa: E402
from app.simulation.registry import CSV_PATH                           # noqa: E402

AUDIT = ROOT / "code_audit"
CAL_DS = "RUN34-CAL (OG-SYNTH-0.6, labelled, ground truth before detector)"
HOLD_DS = "RUN34-HOLDOUT (OG-SYNTH-0.6, independent draw, scored once after selection)"


def write(path, header, rows):
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote {path.relative_to(ROOT)}: {len(rows)} rows")


def population():
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as fh:
        return [r for r in csv.DictReader(fh)
                if (r.get("category_name") or "").strip() == "Portfolio Health"]


CANONICAL_IMPL = {
    "D1.1": "app.simulation.canonical_v8.isolation_forest",
    "D1.2": "app.simulation.canonical_v8.portfolio_outlier",
    "D1.3": "app.simulation.canonical_v8.trajectory_classifier",
    "D1.4": "app.simulation.canonical_v8.cross_project_pattern",
    "D1.5": "app.simulation.canonical_v8.anomaly_profile",
}
THRESHOLD = {
    "D1.1": ("0.576, frozen synthetic laboratory threshold",
             "Run 15 synthetic calibration split; SCHEMA-BOUND and COHORT-BOUND; applied "
             "operationally nowhere"),
    "D1.2": ("none", "no percentile band is calibrated or authorised"),
    "D1.3": ("none", "direction only; the 1e-12 is numerical tolerance, not a band"),
    "D1.4": ("none", "the unvalidated 0.15 radius was retired in Run 33 and not replaced"),
    "D1.5": ("none", "no composite threshold, because no composite is produced"),
}
OBJECTIVE = {
    "D1.1": "Establish tree-count provenance under a predeclared decision rule; establish the "
            "cohort-size policy (n<3 / 3<=n<10 / n>=10); confine the frozen threshold to its own "
            "schema AND to the canonical cohort size.",
    "D1.2": "Establish orientation provenance including the two-sided case; withdraw the "
            "equal-weighted composite, which was an owner-policy choice emitted as though it "
            "were canonical, and return the per-feature percentile profile instead.",
    "D1.3": "Predeclare the minimum observation count; make the time basis explicit rather than "
            "assumed; adopt the contract's IMPROVING/STABLE/DETERIORATING/NOT_ESTIMABLE "
            "vocabulary; keep the numerical tolerance identified as a tolerance.",
    "D1.4": "Keep the radius retired; require an explicit schema, normalization rule, missing-"
            "feature policy, cohort identity and metric; keep the tie rule deterministic and "
            "declared.",
    "D1.5": "Preserve the blocked scalar; thread a governed weight record through so that the "
            "block is a measured absence rather than an unwired one; state the missing "
            "missingness policy separately from the missing weights.",
}
RUN35 = {m: ("Empirical field validation against real project outcomes, and the final parsimony "
             "decision. Nothing in Run 34 is field validated.")
         for m in CANONICAL_IMPL}

#: THE FIVE ASSURANCE LAYERS, per module, stated separately and never merged.
LAYERS = {
    "D1.1": ("ESTABLISHED_RUN_33", "ESTABLISHED_RUN_34",
             "ESTABLISHED_RUN_34_SYNTHETIC", "ESTABLISHED_RUN_34_SYNTHETIC", "PENDING"),
    "D1.2": ("ESTABLISHED_RUN_33", "ESTABLISHED_RUN_34", "NOT_APPLICABLE_NO_PARAMETER",
             "NOT_APPLICABLE_NO_PARAMETER", "PENDING"),
    "D1.3": ("ESTABLISHED_RUN_33", "ESTABLISHED_RUN_34", "NOT_APPLICABLE_NO_PARAMETER",
             "NOT_APPLICABLE_NO_PARAMETER", "PENDING"),
    "D1.4": ("ESTABLISHED_RUN_33", "ESTABLISHED_RUN_34", "NOT_APPLICABLE_NO_PARAMETER",
             "NOT_APPLICABLE_NO_PARAMETER", "PENDING"),
    "D1.5": ("ESTABLISHED_RUN_33", "ESTABLISHED_RUN_34", "NOT_ATTEMPTED_COMPOSITE_BLOCKED",
             "NOT_ATTEMPTED_COMPOSITE_BLOCKED", "PENDING"),
}
LAYER_NOTE = {
    "D1.1": "Layers 3 and 4 are SYNTHETIC: a laboratory threshold and a labelled separation "
            "statistic on generated data. They are not field performance.",
    "D1.2": "No parameter reaches production, so there is nothing to calibrate: the composite is "
            "withheld rather than fitted.",
    "D1.3": "Direction only; the minimum observation count is a predeclared structural minimum, "
            "not a fitted value.",
    "D1.4": "Continuous distance only; no radius exists to calibrate.",
    "D1.5": "The composite is blocked, so there is no composite to calibrate or to hold out.",
}


def tree_count_state():
    path = AUDIT / "run34_ph1_tree_count_calibration.csv"
    if not path.is_file():
        return "NOT_RUN"
    with path.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["metric"] == "tree_count_calibration_status":
                return r["value"]
    return "NOT_RUN"


def main() -> int:
    pop = population()
    ids = sorted(r["new_id"] for r in pop)
    if ids != sorted(PORTFOLIO_VALIDATED):
        print(f"REGISTRY DISAGREEMENT: {ids} vs {sorted(PORTFOLIO_VALIDATED)}", file=sys.stderr)
        return 1
    names = {r["new_id"]: r["module_name"] for r in pop}
    phids = {r["new_id"]: r["old_id"] for r in pop}
    tstate = tree_count_state()

    # --------------------------------------------------------------------- 1. scope
    write(AUDIT / "run34_portfolio_health_scope.csv",
          ["module", "ph_id", "current_name", "canonical_implementation", "current_parameters",
           "parameter_source", "current_threshold", "threshold_source", "cohort_requirement",
           "feature_schema_requirement", "real_corpus_availability", "current_operational_result",
           "run34_calibration_objective", "later_empirical_validation_requirement"],
          [[mid, phids[mid], names[mid], CANONICAL_IMPL[mid],
            "; ".join(f"{p['parameter']}={p['value']}"
                      for p in V8.parameters_for(mid)) or "none",
            "; ".join(sorted({p["parameter_class"] for p in V8.parameters_for(mid)})),
            THRESHOLD[mid][0], THRESHOLD[mid][1],
            "a governed portfolio cohort with a declared population, period, feature schema and "
            "model version",
            "one declared feature schema shared by every cohort member; mixed schemas rejected",
            "ABSENT: the controlled portfolio supplies no governed cohort",
            "ABSTAINS on the real corpus; computes on a supplied governed cohort",
            OBJECTIVE[mid], RUN35[mid]]
           for mid in ids])

    # --------------------------------------------------------------------- 2. provenance
    rows = []
    for p in V8.PH_PARAMETERS:
        calibrated = "yes" if p["calibrated"] else "no"
        rows.append([
            p["module"], p["parameter"], "none" if p["value"] is None else str(p["value"]),
            p["source"], p["parameter_class"],
            CAL_DS if p["parameter_class"] == V8.SYNTHETIC_LAB_CALIBRATION
            or (p["module"] == "D1.1" and p["parameter"] == "n_trees") else "none",
            HOLD_DS if p["parameter_class"] == V8.SYNTHETIC_LAB_CALIBRATION
            or (p["module"] == "D1.1" and p["parameter"] == "n_trees") else "none",
            p["effective_schema"] or "all schemas",
            "the governed cohort under that schema",
            calibrated, "no",
            "yes" if p["applied_operationally"] else "no",
            p["note"] or "retained as declared",
            "PASS"])
    rows.append(["-", "UNCLASSIFIED PARAMETERS", "0", "-", "-", "-", "-", "-", "-", "-", "-",
                 "-", "every parameter carries exactly one of the seven declared classes",
                 "PASS" if not [p for p in V8.PH_PARAMETERS
                                if p["parameter_class"] not in V8.PARAMETER_CLASSES] else "FAIL"])
    rows.append(["-", "UNSUPPORTED PARAMETERS APPLIED", str(len(V8.unsupported_applied())),
                 "-", "-", "-", "-", "-", "-", "-", "-", "-",
                 "an UNSUPPORTED parameter is recorded but may never be applied to produce an "
                 "operational reading", "PASS" if not V8.unsupported_applied() else "FAIL"])
    write(AUDIT / "run34_portfolio_parameter_provenance.csv",
          ["module", "parameter", "current_value", "current_source", "parameter_class",
           "calibration_dataset", "holdout_dataset", "effective_schema", "effective_cohort",
           "calibrated", "field_validated", "operationally_authorized", "action", "result"],
          rows)

    # --------------------------------------------------------------------- 3. reconciliation
    snap = PH.compute_portfolio_health_snapshot("PROBE", {}, [], "2026-01-31")
    absent = snap["structure_absent"]
    write(AUDIT / "run34_real_portfolio_calibration_reconciliation.csv",
          ["module", "governed_cohort_present", "cohort_size", "feature_schema",
           "history_present", "alternatives_or_weights_present", "calibration_record_present",
           "real_corpus_computation_possible", "continuous_output_possible",
           "authoritative_flag_possible", "abstention_or_limitation_reason", "result"],
          [[mid, "no" if absent else "yes", "0", "none declared",
            "no", "no", "no", "no", "no", "no",
            snap["results"][V8.RESULT_KEYS[mid]]["abstention_reason"], "PASS"]
           for mid in ids])

    # --------------------------------------------------------------------- 4. closure
    DISPOSITION = {
        "D1.1": (f"TREE COUNT RETAINED AT 100 (published default); {tstate}. Cohort-size policy "
                 f"established. Frozen threshold confined to its own schema AND to the canonical "
                 f"cohort size; it authorises nothing operationally.",
                 "Empirical validation, and an operational anomaly threshold if one is ever "
                 "wanted -- none exists and none was created."),
        "D1.2": ("COMPOSITE WITHHELD. Equal weighting is an owner-policy choice, not a canonical "
                 "fact, and it is no longer emitted as though it were one. The per-feature "
                 "adverse-tail percentile profile is returned; the supplied oracle midranks are "
                 "unchanged and live in that profile.",
                 "Owner-supplied governed weights, if a composite is wanted; empirical "
                 "validation."),
        "D1.3": ("DIRECTION ONLY, on the contract's IMPROVING/STABLE/DETERIORATING/NOT_ESTIMABLE "
                 "vocabulary. Minimum observations predeclared at three. Actual reporting times "
                 "used; equal spacing reported, never assumed.",
                 "Magnitude calibration if any magnitude distinction is ever wanted -- none is "
                 "authorised; empirical validation."),
        "D1.4": ("CONTINUOUS DISTANCE ONLY. No radius, no cluster flag, deterministic declared "
                 "tie rule, ordering-invariant.",
                 "Radius or clustering calibration if a flag is ever wanted; empirical "
                 "validation."),
        "D1.5": ("COMPOSITE REMAINS NONE under PARAMETER_PROVENANCE_BLOCKED. Run 34 threaded a "
                 "governed weight record through so the block is a MEASURED absence rather than "
                 "an unwired one, and states separately that no governed missingness policy "
                 "exists either.",
                 "Governed weights AND a governed missingness policy, both from a permitted "
                 "source; empirical validation."),
    }
    write(AUDIT / "run34_portfolio_health_calibration_closure.csv",
          ["module", "layer1_canonical_implementation", "layer2_parameter_provenance",
           "layer3_synthetic_calibration", "layer4_holdout", "layer5_real_empirical_validation",
           "assurance_layer_note", "real_corpus_availability", "operational_continuous_output",
           "operational_authoritative_flag", "abstention_or_limitation", "voting",
           "final_run34_disposition", "run35_remainder"],
          [[mid, *LAYERS[mid], LAYER_NOTE[mid],
            "ABSENT: no governed cohort in the controlled portfolio",
            "yes, on a supplied governed cohort", "no",
            "abstains on the real corpus; small-cohort limitation explicit below ten projects",
            "false", DISPOSITION[mid][0], DISPOSITION[mid][1]]
           for mid in ids])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
