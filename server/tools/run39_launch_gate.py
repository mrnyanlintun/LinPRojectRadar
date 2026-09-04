#!/usr/bin/env python3
"""
Run 39: pilot export and main-study launch machinery.

THIS MODULE ADDS AN OPERATIONAL LAYER AND CHANGES NO FROZEN BYTE.

It calls `run38_analysis_export` unchanged: same 58 columns, same schema version
`og-analysis-2026.08-v1`, same categorical levels, same derivations, same serialisation, same
checksum procedure. Everything Run 39 adds sits OUTSIDE that: which rows are selected, and a
sidecar provenance record naming the governed dataset class of the artifact as a whole.

WHY THE DATASET CLASS IS A SIDECAR AND NOT A COLUMN
---------------------------------------------------
The frozen contract's `record_class` column has a CLOSED vocabulary of ("TEST_ONLY", "STUDY")
and is derived from a pseudonymous-code prefix. Run 39 must distinguish three classes
(TEST_ONLY / PILOT / MAIN_STUDY) and must not derive class from a naming convention. Widening
that column's vocabulary would change the frozen export schema, which Run 39's hard boundary
forbids and which section 21 forbids resolving by minting a successor.

The specification permits the alternative it needs: the dataset class must be "retained OR
provenance-linkable". So the class is carried in the sidecar `*.class.json`, which names the
artifact's single governed class and pins the registry digest that produced it. A PILOT artifact
and a MAIN_STUDY artifact are therefore never confusable, because an export contains exactly one
class and says which, while the frozen CSV bytes stay exactly what the frozen contract specifies.
"""
from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from sqlalchemy import select                                        # noqa: E402
from sqlalchemy.orm import Session                                   # noqa: E402

import run38_analysis_export as AX                                   # noqa: E402
import run39_dataset_class as DC                                     # noqa: E402
from app.research_models import Assignment, Decision, Participant    # noqa: E402

REPO = pathlib.Path(__file__).resolve().parents[2]

#: The frozen contract this run consumes and does not alter.
EXPECTED_SCHEMA = "og-analysis-2026.08-v1"

#: DERIVED FROM THE LIVE AUTHORITY, NEVER TRANSCRIBED.
#: Run 39's controlling specification says "58 columns unless the frozen contract mechanically
#: specifies otherwise". It does specify otherwise: `run38_analysis_export.ANALYSIS_COLUMNS` is
#: the contract's implementation and it holds 59 columns, and the machine-generated Run-38
#: readiness manifest independently recorded export_column_count = 59. The "58" that appears in
#: the Run-38 report prose and handoff was hand-written and is wrong; it is corrected there by
#: errata rather than propagated here. This constant is computed so it cannot drift from the
#: thing it describes.
EXPECTED_COLUMN_COUNT = len(AX.ANALYSIS_COLUMNS)


def build_class_export(session: Session, dataset_class: str,
                       registry: dict[str, str] | None = None) -> tuple[list[dict], bytes, dict]:
    """
    One governed class, through the frozen export path.

    Returns (rows, csv_bytes, sidecar). The CSV bytes are produced by
    run38_analysis_export.serialise_csv with no interference of any kind.
    """
    reg = DC.load_registry() if registry is None else registry
    all_rows = AX.build_analysis_rows(session)
    rows = DC.select(all_rows, dataset_class, reg)
    payload = AX.serialise_csv(rows)
    manifest = AX.freeze_manifest(payload, rows)

    # DELIBERATELY NO RAISE HERE. Schema and column-count drift are JUDGED by
    # test_run39_launch_gate.py, which turns red and names the failure. Raising here killed the
    # gate mid-run instead, and a process that dies without printing its result is a crash, not
    # a detection -- the distinction this programme insists on. The values are surfaced in the
    # sidecar below so the caller can judge them.

    sidecar = {
        "artifact_dataset_class": dataset_class,
        "dataset_class_vocabulary": list(DC.DATASET_CLASSES),
        "classification_authority": str(DC.REGISTRY.relative_to(REPO)),
        "classification_registry_sha256": DC.registry_digest(),
        "classification_rule": ("The governed registry is the sole authority. A participant the "
                                "registry does not name is UNCLASSIFIED and can never be "
                                "exported as MAIN_STUDY. Dataset class is never inferred from a "
                                "participant's code, label or date."),
        "row_count": len(rows),
        "participants": sorted({r["study_participant_id"] for r in rows}),
        "dataset_sha256": manifest["sha256"],
        "schema_version": manifest["schema_version"],
        "column_count": manifest["column_count"],
        "built_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "not_study_findings": ("A PILOT or TEST_ONLY artifact is operational qualification "
                               "evidence. It is not a study observation and it is not empirical "
                               "validation."),
    }
    return rows, payload, sidecar


def main_study_row_count(session: Session,
                         registry: dict[str, str] | None = None) -> tuple[int, list[str]]:
    """
    THE ZERO-STATE MEASUREMENT, taken from the database rather than from the registry alone.

    Counts persisted `decisions` rows whose owning participant is registered MAIN_STUDY. Reading
    only the registry would prove that nobody is *registered*, which is a weaker claim than that
    no main-study observation *exists*.
    """
    reg = DC.load_registry() if registry is None else registry
    # RUN 135C, M12. `if not main_codes: return 0, []` stood here, before any query. The registry
    # holds zero MAIN_STUDY entries, so on the live path this function returned (0, []) WITHOUT
    # TOUCHING THE DATABASE -- proved with a session whose .execute raises: it returned (0, [])
    # rather than raising. The docstring's claim, that the measurement is "taken from the database
    # rather than from the registry alone", was therefore false exactly when it mattered: at the
    # zero state the gate exists to certify. A main-study observation persisted against a
    # participant the registry does not list would have been invisible.
    #
    # The query now runs first and unconditionally, over every participant carrying decisions, and
    # the MAIN_STUDY decision is taken per row by DC.classify -- the same classifier the rest of
    # the gate uses -- rather than by an in-list built from a registry that may be empty or stale.
    rows = session.execute(
        select(Participant.pseudonymous_code, Decision.decision_id)
        .join(Assignment, Assignment.participant_id == Participant.participant_id)
        .join(Decision, Decision.assignment_id == Assignment.assignment_id)
    ).all()
    main = [r for r in rows if DC.classify(r[0], reg) == DC.MAIN_STUDY]
    return len(main), sorted({r[0] for r in main})


def session_completeness(session: Session,
                         registry: dict[str, str] | None = None) -> list[dict]:
    """
    Per-participant completion audit, derived from persisted rows only.

    NOTHING IS MANUFACTURED. A participant with 17 decisions is reported as having 17. The
    classification of complete vs incomplete is a count, not a repair.
    """
    reg = DC.load_registry() if registry is None else registry
    out: list[dict] = []
    for p in session.scalars(select(Participant)).all():
        decisions = session.scalars(
            select(Decision).join(Assignment)
            .where(Assignment.participant_id == p.participant_id)).all()
        # RUN 135C, L6. `if not decisions: continue` stood here. A participant with zero decisions
        # was OMITTED from the completeness audit rather than reported as incomplete, so the set
        # this function returns was not the participant set -- it was the subset that happened to
        # have data, and "every participant in this list is complete" said nothing about the ones
        # silently dropped. A zero-decision participant is now reported with observations 0 and
        # complete_36 False, which is what an incomplete set looks like when it is reported rather
        # than trimmed.
        keys = {(d.assignment_id, d.period) for d in decisions}
        out.append({
            "study_participant_id": p.pseudonymous_code,
            "dataset_class": DC.classify(p.pseudonymous_code, reg),
            "observations": len(decisions),
            "unique_project_periods": len(keys),
            "duplicate_project_periods": len(decisions) - len(keys),
            "pre_locked": sum(1 for d in decisions if d.pre_locked_at is not None),
            "revealed": sum(1 for d in decisions if d.reveal_at is not None),
            "final_locked": sum(1 for d in decisions if d.final_submitted_at is not None),
            "reveal_after_pre_lock": sum(
                1 for d in decisions
                if d.reveal_at is not None and d.pre_locked_at is not None
                and d.reveal_at >= d.pre_locked_at),
            "complete_36": len(keys) == 36 and all(
                d.final_submitted_at is not None for d in decisions) and len(decisions) == 36,
        })
    return sorted(out, key=lambda r: str(r["study_participant_id"] or ""))


def write_export(out_dir: pathlib.Path, stem: str, payload: bytes,
                 rows: list[dict], sidecar: dict) -> dict[str, pathlib.Path]:
    """Write the CSV, the frozen manifest and the Run-39 class sidecar together."""
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_p = out_dir / f"{stem}.csv"
    man_p = out_dir / f"{stem}.manifest.json"
    cls_p = out_dir / f"{stem}.class.json"
    csv_p.write_bytes(payload)
    man_p.write_text(json.dumps(AX.freeze_manifest(payload, rows), indent=2, sort_keys=True),
                     encoding="utf-8")
    cls_p.write_text(json.dumps(sidecar, indent=2, sort_keys=True), encoding="utf-8")
    return {"csv": csv_p, "manifest": man_p, "class": cls_p}
