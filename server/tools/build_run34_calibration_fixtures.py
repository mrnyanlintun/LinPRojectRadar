#!/usr/bin/env python3
"""
RUN 34. THE LABELLED PORTFOLIO HEALTH CALIBRATION AND HOLDOUT FIXTURES.

GROUND TRUTH IS DEFINED BEFORE THE DETECTOR, AND BEFORE THE DATA. The anomalous project
identifiers are chosen FIRST, by a rule stated here and fixed by the predeclared protocol; the
generative mechanism for an anomalous point is then applied BECAUSE the project carries that
label. No detector is run at any point in this file, and no detector output settles any label.
The label causes the point; the point never causes the label.

THE HOLDOUT IS AN INDEPENDENT DRAW under the SAME generative specification with a DIFFERENT
generator seed. That is what makes it a holdout: not different rules, the same rules re-run.

SYNTHETIC. Every fixture states data_origin = SYNTHETIC_RESEARCH_CALIBRATION,
not_for_empirical_validation = true and ground_truth_defined_before_detector = true. These
fixtures establish numerical behaviour, stability, sensitivity and known anomaly separation. They
establish NOTHING about real construction-project anomaly prevalence, field false-positive rates,
practitioner usefulness, operational business thresholds or predictive validity.
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import random

ROOT = pathlib.Path(__file__).resolve().parents[2]
PKG = ROOT / "research_fixtures" / "synthetic" / "OG-SYNTH-0.6"
DIR = PKG / "package_D_portfolio_calibration"

#: Predeclared in research/methodology/run34_portfolio_calibration_protocol.md section 4.
CALIBRATION_SEED = 340001
HOLDOUT_SEED = 340002
N_PROJECTS = 200

#: THE LABEL RULE, FIXED BEFORE ANY VALUE IS DRAWN. Project index i is anomalous iff i % 20 == 7.
#: It is an arithmetic property of the identifier, so it cannot be influenced by any measurement.
def is_anomalous(i: int) -> bool:
    return i % 20 == 7


#: The generative specification. Normals are standard normal in three dimensions; an anomalous
#: project is displaced onto a shell at DISPLACEMENT standard deviations in a uniformly random
#: direction. Declared here so the holdout can be an independent draw under the same rules.
DIMENSIONS = 3
DISPLACEMENT = 5.0

FEATURES = ("g1", "g2", "g3")


def feature(fid: str) -> dict:
    return {"feature_id": fid, "label": fid, "units": "index",
            "orientation": "HIGHER_IS_MORE_ADVERSE", "scaling_rule": "NONE_RAW_UNITS",
            "missingness_rule": "ABSTAIN_NEVER_IMPUTE",
            "source_module": "SYNTHETIC_CALIBRATION_FIXTURE",
            "qualification_requirement": "CATEGORY_9_ELIGIBLE", "required": True}


def build(dataset_id: str, seed: int, prefix: str, role: str) -> dict:
    rng = random.Random(seed)
    schema_version = f"synth-run34-cal-v1"
    records, labels, ids = [], {}, []
    for i in range(N_PROJECTS):
        pid = f"{prefix}-{i:03d}"
        ids.append(pid)
        # THE LABEL IS DECIDED FIRST, from the identifier alone.
        anomalous = is_anomalous(i)
        labels[pid] = 1 if anomalous else 0
        # AND THE POINT IS THEN GENERATED BECAUSE OF THE LABEL.
        base = [rng.gauss(0.0, 1.0) for _ in range(DIMENSIONS)]
        if anomalous:
            direction = [rng.gauss(0.0, 1.0) for _ in range(DIMENSIONS)]
            norm = math.sqrt(sum(d * d for d in direction)) or 1.0
            base = [DISPLACEMENT * d / norm + 0.25 * b
                    for d, b in zip(direction, base)]
        records.append({
            "project_id": pid, "cohort_id": dataset_id, "period": "2026-01",
            "values": {f: round(v, 6) for f, v in zip(FEATURES, base)},
            "qualification_state": "QUALIFIED", "missing_fields": [], "invalid_fields": [],
            "source_lineage": f"SYNTHETIC_CALIBRATION::{pid}",
            "source_provenance": f"SYNTHETIC_CALIBRATION::{dataset_id}",
            "feature_schema_version": schema_version,
        })
    return {
        "data_origin": "SYNTHETIC_RESEARCH_CALIBRATION",
        "not_for_empirical_validation": True,
        "ground_truth_defined_before_detector": True,
        "dataset_id": dataset_id,
        "role": role,
        "generator_seed": seed,
        "label_rule": "project index i is anomalous iff i % 20 == 7; decided from the identifier "
                      "alone, before any feature value is drawn, and never from any detector "
                      "output",
        "generative_specification": {
            "dimensions": DIMENSIONS,
            "normal": "each coordinate drawn standard normal",
            "anomalous": f"displaced onto a shell at {DISPLACEMENT} standard deviations in a "
                         f"uniformly random direction, plus a quarter-weight normal jitter",
            "n_projects": N_PROJECTS,
            "n_anomalous": sum(1 for i in range(N_PROJECTS) if is_anomalous(i)),
        },
        "what_this_establishes": [
            "numerical behaviour", "stability", "sensitivity", "known anomaly separation",
            "known cohort effects", "parameter trade-offs",
        ],
        "what_this_does_not_establish": [
            "real construction-project anomaly prevalence", "field false-positive rate",
            "practitioner usefulness", "operational business threshold", "predictive validity",
        ],
        "labels": labels,
        "cohort": {
            "cohort_id": dataset_id, "portfolio_id": "SYNTH-CALIBRATION-PORTFOLIO",
            "project_ids": ids, "period": "2026-01",
            "inclusion_rule": "every declared synthetic calibration project",
            "exclusion_rule": "none", "feature_schema_version": schema_version,
            "qualification_policy": "CATEGORY_9_ELIGIBLE_STATES_ONLY",
            "model_version": "ph-v22-synthetic-calibration-m1",
        },
        "feature_schema": {"version": schema_version,
                           "features": [feature(f) for f in FEATURES]},
        "feature_records": records,
    }


def main() -> int:
    DIR.mkdir(parents=True, exist_ok=True)
    for name, dsid, seed, prefix, role in (
            ("run34_ph1_calibration_labelled.json", "RUN34-CAL", CALIBRATION_SEED, "CAL",
             "CALIBRATION"),
            ("run34_ph1_holdout_labelled.json", "RUN34-HOLDOUT", HOLDOUT_SEED, "HOLD",
             "HOLDOUT")):
        payload = build(dsid, seed, prefix, role)
        (DIR / name).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {(DIR / name).relative_to(ROOT)}: {N_PROJECTS} projects, "
              f"{sum(payload['labels'].values())} labelled anomalous")

    lines = ["# OPUS GUBERNATIO SYNTHETIC PACKAGE OG-SYNTH-0.6",
             "# Successor to OG-SYNTH-0.5, whose own CHECKSUMS.sha256 is preserved unchanged.",
             "# Every path below is relative to the repository root.", "#"]
    for f in sorted(p for p in PKG.rglob("*") if p.is_file()
                    and p.name != "CHECKSUMS.sha256"):
        lines.append(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  "
                     f"{f.relative_to(ROOT).as_posix()}")
    (PKG / "CHECKSUMS.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {(PKG / 'CHECKSUMS.sha256').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
