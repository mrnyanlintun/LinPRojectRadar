#!/usr/bin/env python3
"""
Run 39: the main-study data freeze procedure, as executable code.

The freeze procedure is written down in
`research/study_execution/MAIN_STUDY_DATA_FREEZE_PROCEDURE.md`. This module IS that procedure,
so the document describes something that runs rather than something someone intends to do. A
written procedure nobody can execute is not a control.

IT PRODUCES NO STUDY DATASET IN RUN 39. There are no MAIN_STUDY registrations, so
`freeze_dataset` refuses with `EmptyDatasetError` when asked for the main study. That refusal is
the correct behaviour and the launch gate asserts it: freezing an empty set would create an
artifact that looks like a study dataset and contains nothing.

The same machinery is rehearsed against the PILOT class, which is how determinism and checksum
reproduction are proved without fabricating study observations.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from sqlalchemy.orm import Session                                    # noqa: E402

import run38_analysis_export as AX                                    # noqa: E402
import run39_dataset_class as DC                                      # noqa: E402
import run39_launch_gate as LG                                        # noqa: E402

REPO = pathlib.Path(__file__).resolve().parents[2]


class EmptyDatasetError(RuntimeError):
    """Asked to freeze a class with no observations. Never silently produces an empty artifact."""


class InvariantError(RuntimeError):
    """A pre-freeze invariant failed. The freeze is refused rather than recorded with a caveat."""


#: The invariants every frozen artifact must satisfy, checked BEFORE the checksum is taken.
#: Ordered, and each returns the count of violations, which must be zero.
def check_invariants(rows: list[dict]) -> list[tuple[str, int]]:
    keys = [(r["study_participant_id"], r["scenario_id"], r["period"]) for r in rows]
    return [
        ("duplicate participant/project/period rows", len(keys) - len(set(keys))),
        ("rows missing a project", sum(1 for r in rows if not r["evidence_project_id"])),
        ("rows missing a period", sum(1 for r in rows if not r["period"])),
        ("final response without preliminary lock",
         sum(1 for r in rows if r["final_submitted_at"] and not r["pre_locked_at"])),
        ("final response without AI reveal",
         sum(1 for r in rows if r["final_submitted_at"] and not r["reveal_at"])),
        ("AI reveal before preliminary lock",
         sum(1 for r in rows if r["reveal_at"] and r["pre_locked_at"]
             and r["reveal_at"] < r["pre_locked_at"])),
        ("impossible timestamp ordering",
         sum(1 for r in rows if r["final_submitted_at"] and r["reveal_at"]
             and r["final_submitted_at"] < r["reveal_at"])),
        ("rows missing frozen-instrument version identity",
         sum(1 for r in rows if not (r["simulation_version"] and r["participant_package"]
                                     and r["synthetic_package"] and r["schema_version"]
                                     and r["freeze_candidate_commit"]))),
        ("direct identifier columns",
         sum(1 for c in AX.DIRECT_IDENTIFIER_TOKENS if c in AX.ANALYSIS_COLUMNS)),
        ("participant-authored free-text columns",
         len(set(AX.FREE_TEXT_COLUMNS_EXCLUDED) & set(AX.ANALYSIS_COLUMNS))),
    ]


def checksum(payload: bytes) -> str:
    """sha256 over the exact bytes. The single freeze checksum procedure."""
    return hashlib.sha256(payload).hexdigest()


def freeze_dataset(session: Session, out_dir: pathlib.Path, stem: str,
                   dataset_class: str = DC.MAIN_STUDY,
                   registry: dict[str, str] | None = None) -> dict:
    """
    Steps 4 to 10 of the written procedure, executed.

    Returns the freeze record. Raises rather than degrading: an empty dataset, a failed
    invariant, or a checksum that does not reproduce from the written file all stop the freeze.
    """
    reg = DC.load_registry() if registry is None else registry
    rows, payload, sidecar = LG.build_class_export(session, dataset_class, reg)

    if not rows:
        raise EmptyDatasetError(
            f"no observations are classified {dataset_class}; refusing to write an artifact that "
            f"would look like a dataset and contain nothing")

    violations = [(name, n) for name, n in check_invariants(rows) if n]
    if violations:
        raise InvariantError(f"pre-freeze invariants failed: {violations}")

    digest = checksum(payload)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_p = out_dir / f"{stem}.csv"
    csv_p.write_bytes(payload)

    # STEP 10 IN PRACTICE: re-read from disk and re-derive. Trusting the in-memory bytes would
    # not detect a truncated or partially written file, which is the failure this step exists for.
    written = csv_p.read_bytes()
    if checksum(written) != digest:
        csv_p.unlink(missing_ok=True)
        raise InvariantError("the written file does not reproduce the checksum; freeze aborted")

    manifest = AX.freeze_manifest(payload, rows)
    record = {
        "frozen_artifact": csv_p.name,
        "dataset_class": dataset_class,
        "sha256": digest,
        "checksum_procedure": "sha256 over the exact UTF-8 bytes of the CSV, no BOM, LF endings",
        "row_count": len(rows),
        "column_count": manifest["column_count"],
        "schema_version": manifest["schema_version"],
        "row_grain": AX.ROW_GRAIN,
        "simulation_version": manifest["simulation_version"],
        "participant_package": manifest["participant_package"],
        "synthetic_package": manifest["synthetic_package"],
        "freeze_candidate_commit": manifest["freeze_candidate_commit"],
        "classification_registry_sha256": sidecar["classification_registry_sha256"],
        "participants": sidecar["participants"],
        "invariants_checked": [name for name, _ in check_invariants(rows)],
        "invariant_violations": 0,
        "frozen_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "immutability": ("This file is never edited. A correction is a NEW artifact with a new "
                         "checksum, never an in-place change."),
        "analysis_rule": ("Statistical analysis runs against this frozen artifact only, never "
                          "against the live operational database."),
    }
    (out_dir / f"{stem}.manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / f"{stem}.class.json").write_text(
        json.dumps(sidecar, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / f"{stem}.freeze.json").write_text(
        json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    return record


def verify_frozen(csv_path: pathlib.Path, freeze_record_path: pathlib.Path) -> list[str]:
    """Re-verify a frozen artifact from disk alone. Returns the list of problems; empty is good."""
    problems: list[str] = []
    record = json.loads(freeze_record_path.read_text(encoding="utf-8"))
    actual = checksum(csv_path.read_bytes())
    if actual != record["sha256"]:
        problems.append(f"checksum mismatch: recorded {record['sha256']} actual {actual}")
    header = csv_path.read_text(encoding="utf-8").split("\n")[0].split(",")
    if header != list(AX.ANALYSIS_COLUMNS):
        problems.append("column header does not match the frozen column list")
    if record["schema_version"] != AX.ANALYSIS_SCHEMA_VERSION:
        problems.append(f"schema version drift: {record['schema_version']}")
    if record.get("invariant_violations", 1) != 0:
        problems.append("the freeze record admits invariant violations")
    for field in ("simulation_version", "participant_package", "synthetic_package",
                  "freeze_candidate_commit"):
        if not record.get(field):
            problems.append(f"provenance field {field} is missing from the freeze record")
    return problems
