#!/usr/bin/env python3
"""
Run 38: the qualified analysis-dataset export.

WHAT THIS IS AND IS NOT
-----------------------
This is an EXPORT-VALIDATION / ANALYSIS-HANDOFF tool built by Run 38 under the run's explicit
permission to "build export-validation tools" and to "build or verify one controlled export
path from research database state to analysis dataset". It MODIFIES NOTHING FROZEN. It does
not touch app/research_export.py; it CONSUMES that module's governed builders
(`build_rows`, `build_stimulus_rows`) and composes their output into one flat, deidentified,
checksummed CSV with explicit provenance.

WHY A SEPARATE PATH RATHER THAN AN EDIT TO research_export.py
-------------------------------------------------------------
Three measured facts required it, and none of them may be repaired in place:

  1. `EXPORT_COLUMNS` (the governed flat CSV) carries NO AI recommendation. The recommendation
     actually disclosed lives on the Stimulus sheet of the xlsx workbook. Revision direction
     relative to the AI therefore cannot be derived from the governed flat CSV alone. It IS
     derivable by joining Stimulus to Decisions on instance_id, which is what this module does.

  2. `EXPORT_COLUMNS` carries NO frozen-instrument version identity (no simulation version, no
     participant package, no schema version), so a governed CSV cannot prove which instrument
     produced it.

  3. `EXPORT_COLUMNS` includes three participant-authored free-text columns
     (`pre_assessment`, `rationale`, `residual_risk`). Measured behaviour: text typed into
     `rationale` reaches the CSV verbatim, including an email address. There is no automated
     removal and no governed manual-review procedure in the repository, so that CSV cannot be
     asserted free of direct identifiers.

FREE TEXT IS EXCLUDED BY CONSTRUCTION, NOT SCRUBBED.
This follows the precedent already in the repository: the workbook's `analysis_long` sheet
"carries NONE of it, by construction: it is built from a fixed column list that contains no
free-text field". Run 38 does not invent an automated scrubber, because the efficacy of a
scrubber cannot be proved and asserting it would be exactly the kind of unearned claim this
programme forbids. Instead the analysis dataset carries only NON-IDENTIFYING DERIVATIONS of the
free-text fields (presence flag and character count), and the raw text stays in the governed
`participant_inputs` export, which is review-required and is NOT the analysis dataset.
There is consequently NO governed rationale coding protocol in this repository, so no rationale
content variable is claimed here.

NO CORRECTNESS LABEL IS INTRODUCED. `revision_direction` is stated relative to the AI
recommendation, which is what the study measures; it is not agreement-as-correctness and no
reference standard is asserted.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import pathlib
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from sqlalchemy.orm import Session  # noqa: E402

from app.research_export import (  # noqa: E402
    build_analysis_long_rows, build_rows, build_stimulus_rows,
)
from app.simulation.models import SIMULATION_VERSION  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import participant_packages as PP  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parents[2]

#: Bumped only by a deliberate contract change. Recorded in every row.
ANALYSIS_SCHEMA_VERSION = "og-analysis-2026.08-v1"

#: The two permitted values of record_class. CLOSED VOCABULARY.
RECORD_CLASSES = ("TEST_ONLY", "STUDY")

#: How a row is classified. A pseudonymous code carrying this prefix is a dry-run record.
#: This is an operational labelling convention Run 38 establishes and the runbook binds; it is
#: applied mechanically to the only participant identifier that reaches an export.
TEST_ONLY_CODE_PREFIX = "R38-TESTONLY-"

#: One row per participant x project(scenario) x period.
ROW_GRAIN = "participant x project(scenario) x period"

ANALYSIS_COLUMNS: tuple[str, ...] = (
    # ---- provenance (section 19 / blocker 14 / blocker 18)
    "schema_version",
    "simulation_version",
    "participant_package",
    "synthetic_package",
    "freeze_candidate_commit",
    "record_class",
    "exported_at",
    # ---- keys
    "study_participant_id",
    "instance_id",
    "scenario_id",
    "scenario_version",
    "evidence_project_id",
    "sequence_number",
    "period",
    # ---- design
    "order_group",
    "config_code",
    # ---- preliminary judgment
    "pre_action",
    "pre_confidence",
    "pre_submitted_at",
    "pre_locked_at",
    "pre_assessment_present",
    "pre_assessment_chars",
    # ---- disclosed AI treatment (joined from the governed Stimulus builder)
    "reveal_at",
    "package_id",
    "package_version",
    "package_hash",
    "ai_recommended_action",
    "ai_detected_condition",
    "ai_output_type",
    "ai_model_version",
    # ---- final judgment
    "final_action",
    "disposition",
    "final_confidence",
    "final_submitted_at",
    "reason_code",
    "evidence_items_count",
    "rationale_present",
    "rationale_chars",
    "residual_risk_present",
    "escalation_level",
    "owner_role",
    "authority_role",
    "resource_constraint",
    "deadline_present",
    # ---- derived dependent variables (section 7 / section 16)
    "action_revised",
    "revision_direction",
    "pre_matches_ai",
    "final_matches_ai",
    "confidence_change",
    "confidence_direction",
    # ---- timing (section 8)
    "deliberation_seconds",
    "pre_assessment_seconds",
    "time_on_instance_seconds",
    "pre_committed_before_disclosure",
    "completion_state",
    "session_break",
    # ---- transition
    "branch_id",
    "next_state_id",
    "transition_displayed_at",
)

#: Columns whose value must come from a closed set. Enforced by the R ingestion contract.
CATEGORICAL_LEVELS: dict[str, tuple[str, ...]] = {
    "record_class": RECORD_CLASSES,
    "revision_direction": ("none", "toward_ai", "away_from_ai", "lateral"),
    "confidence_direction": ("increase", "decrease", "unchanged"),
    "completion_state": ("complete", "pre_only", "revealed_not_decided", "not_started"),
}

#: Nothing participant-authored appears in the dataset. Asserted by the readiness suite.
FREE_TEXT_COLUMNS_EXCLUDED: tuple[str, ...] = ("pre_assessment", "rationale", "residual_risk")

#: Names that must never appear anywhere in the serialised bytes.
DIRECT_IDENTIFIER_TOKENS: tuple[str, ...] = (
    "email", "google_email", "display_name", "access_token", "access_token_hash",
    "session_token", "session_ref", "ip_address", "ip_hash", "participant_id",
    "employee_id", "consent_id",
)


def _synthetic_package() -> str:
    rec = json.loads((REPO / "research/freeze/INSTRUMENT_FINAL_FREEZE_RECORD.json")
                     .read_text(encoding="utf-8"))
    return rec["synthetic_package"]


def _freeze_candidate() -> str:
    rec = json.loads((REPO / "research/freeze/INSTRUMENT_FINAL_FREEZE_RECORD.json")
                     .read_text(encoding="utf-8"))
    return rec["freeze_candidate_commit"]


def _chars(value) -> int | None:
    return None if value is None else len(str(value))


def _present(value) -> bool:
    return value is not None and str(value).strip() != ""


def _classify(code: str | None) -> str:
    return "TEST_ONLY" if (code or "").startswith(TEST_ONLY_CODE_PREFIX) else "STUDY"


def _completion_state(dec: dict) -> str:
    if dec.get("final_submitted_at"):
        return "complete"
    if dec.get("reveal_at"):
        return "revealed_not_decided"
    if dec.get("pre_locked_at"):
        return "pre_only"
    return "not_started"


def _revision(pre, final, ai) -> tuple[int | None, str | None, bool | None, bool | None]:
    if pre is None or final is None:
        return None, None, (None if ai is None or pre is None else pre == ai), None
    revised = int(pre != final)
    pre_ai = None if ai is None else (pre == ai)
    fin_ai = None if ai is None else (final == ai)
    if ai is None:
        direction = None
    elif not revised:
        direction = "none"
    elif final == ai:
        direction = "toward_ai"
    elif pre == ai:
        direction = "away_from_ai"
    else:
        direction = "lateral"
    return revised, direction, pre_ai, fin_ai


def build_analysis_rows(session: Session, start=None, end=None) -> list[dict]:
    """Compose the governed Decisions and Stimulus builders into the analysis grain."""
    decisions = build_rows(session, start, end)
    stimulus = {r["instance_id"]: r for r in build_stimulus_rows(session, start, end)}
    # `project` (the evidence project the instance belongs to) is carried by the
    # governed analysis_long builder, not by the Stimulus sheet. Read from there
    # rather than recomputed, so the two can never disagree.
    projects = {r["instance_id"]: r["project"]
                for r in build_analysis_long_rows(session, start, end)}
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    sim, pkg, syn, cand = (SIMULATION_VERSION, PP.CURRENT.identifier,
                           _synthetic_package(), _freeze_candidate())

    out: list[dict] = []
    for d in decisions:
        st = stimulus.get(d["instance_id"], {})
        ai = st.get("recommended_action")
        revised, direction, pre_ai, fin_ai = _revision(d["pre_action"], d["final_action"], ai)
        cshift = d.get("confidence_shift")
        cdir = (None if cshift is None else
                "increase" if cshift > 0 else "decrease" if cshift < 0 else "unchanged")
        items = d.get("evidence_items")
        row = {
            "schema_version": ANALYSIS_SCHEMA_VERSION,
            "simulation_version": sim,
            "participant_package": pkg,
            "synthetic_package": syn,
            "freeze_candidate_commit": cand,
            "record_class": _classify(d["pseudonymous_code"]),
            "exported_at": now,
            "study_participant_id": d["pseudonymous_code"],
            "instance_id": d["instance_id"],
            "scenario_id": d["scenario_id"],
            "scenario_version": d["scenario_version"],
            "evidence_project_id": projects.get(d["instance_id"]),
            "sequence_number": d["sequence_number"],
            "period": d["period"],
            "order_group": d["order_group"],
            "config_code": d["config_code"],
            "pre_action": d["pre_action"],
            "pre_confidence": d["pre_confidence"],
            "pre_submitted_at": d["pre_submitted_at"],
            "pre_locked_at": d["pre_locked_at"],
            "pre_assessment_present": _present(d["pre_assessment"]),
            "pre_assessment_chars": _chars(d["pre_assessment"]),
            "reveal_at": d["reveal_at"],
            "package_id": d["package_id"],
            "package_version": d["package_version"],
            "package_hash": d["package_hash"],
            "ai_recommended_action": ai,
            "ai_detected_condition": st.get("detected_condition"),
            "ai_output_type": st.get("output_type"),
            "ai_model_version": st.get("model_version"),
            "final_action": d["final_action"],
            "disposition": d["disposition"],
            "final_confidence": d["final_confidence"],
            "final_submitted_at": d["final_submitted_at"],
            "reason_code": d["reason_code"],
            "evidence_items_count": (len(items) if isinstance(items, list) else None),
            "rationale_present": _present(d["rationale"]),
            "rationale_chars": _chars(d["rationale"]),
            "residual_risk_present": _present(d["residual_risk"]),
            "escalation_level": d["escalation_level"],
            "owner_role": d["owner_role"],
            "authority_role": d["authority_role"],
            "resource_constraint": d["resource_constraint"],
            "deadline_present": _present(d["deadline"]),
            "action_revised": revised,
            "revision_direction": direction,
            "pre_matches_ai": pre_ai,
            "final_matches_ai": fin_ai,
            "confidence_change": cshift,
            "confidence_direction": cdir,
            "deliberation_seconds": d["deliberation_seconds"],
            "pre_assessment_seconds": d["pre_assessment_seconds"],
            "time_on_instance_seconds": d["time_on_instance_seconds"],
            "pre_committed_before_disclosure": d["pre_committed_before_disclosure"],
            "completion_state": _completion_state(d),
            "session_break": d["session_break"],
            "branch_id": d["branch_id"],
            "next_state_id": d["next_state_id"],
            "transition_displayed_at": d["transition_displayed_at"],
        }
        missing = set(ANALYSIS_COLUMNS) - set(row)
        extra = set(row) - set(ANALYSIS_COLUMNS)
        if missing or extra:
            raise RuntimeError(f"analysis row shape drift: missing={sorted(missing)} "
                               f"extra={sorted(extra)}")
        out.append({k: row[k] for k in ANALYSIS_COLUMNS})

    # DETERMINISTIC ORDERING. Named explicitly so two exports of the same data are byte-equal
    # apart from exported_at, which is why the checksum procedure holds exported_at fixed.
    out.sort(key=lambda r: (str(r["study_participant_id"]), int(r["sequence_number"] or 0),
                            str(r["period"])))
    return out


def _cell(value) -> str:
    """DETERMINISTIC NULL AND BOOLEAN REPRESENTATION. NA for null, TRUE/FALSE for booleans."""
    if value is None:
        return "NA"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    return str(value)


def serialise_csv(rows: list[dict]) -> bytes:
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=list(ANALYSIS_COLUMNS), lineterminator="\n",
                       extrasaction="raise")
    w.writeheader()
    for r in rows:
        w.writerow({k: _cell(r[k]) for k in ANALYSIS_COLUMNS})
    return buf.getvalue().encode("utf-8")


def checksum(payload: bytes) -> str:
    """FREEZE PROCEDURE: sha256 over the exact UTF-8 bytes of the CSV, no BOM, LF endings."""
    return hashlib.sha256(payload).hexdigest()


def freeze_manifest(payload: bytes, rows: list[dict]) -> dict:
    return {
        "artifact": "run38 frozen analysis dataset (dry run)",
        "schema_version": ANALYSIS_SCHEMA_VERSION,
        "row_grain": ROW_GRAIN,
        "row_count": len(rows),
        "column_count": len(ANALYSIS_COLUMNS),
        "columns": list(ANALYSIS_COLUMNS),
        "sha256": checksum(payload),
        "encoding": "utf-8",
        "line_terminator": "LF",
        "null_representation": "NA",
        "boolean_representation": "TRUE/FALSE",
        "record_classes_present": sorted({r["record_class"] for r in rows}),
        "categorical_levels": {k: list(v) for k, v in CATEGORICAL_LEVELS.items()},
        "simulation_version": SIMULATION_VERSION,
        "participant_package": PP.CURRENT.identifier,
        "synthetic_package": _synthetic_package(),
        "freeze_candidate_commit": _freeze_candidate(),
        "free_text_excluded_by_construction": list(FREE_TEXT_COLUMNS_EXCLUDED),
        "not_study_evidence": ("Every row whose record_class is TEST_ONLY is synthetic dry-run "
                               "data and is not a study observation."),
    }
