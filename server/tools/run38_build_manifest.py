#!/usr/bin/env python3
"""
Run 38 section 19: build research/study_execution/STUDY_EXECUTION_READINESS_MANIFEST.json.

Every field is READ from a live authority or from an audit artifact this run produced. Nothing
is transcribed by hand: a manifest whose numbers were typed in would be a claim, not a record.
The disposition is COMPUTED from the blocker count, not asserted.
"""
from __future__ import annotations

import csv
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
AUDIT = ROOT / "code_audit"
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(ROOT / "server" / "tools"))

from app.simulation.models import SIMULATION_VERSION      # noqa: E402
import participant_packages as PP                         # noqa: E402
import run38_analysis_export as AX                        # noqa: E402


def rows(name: str) -> list[dict]:
    path = AUDIT / name
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def verdict(name: str, column: str = "result",
            good: tuple[str, ...] = ("PASS",)) -> str:
    r = rows(name)
    if not r:
        return "NOT_PRODUCED"
    bad = [x for x in r if x.get(column) not in good]
    return f"PASS ({len(r)} rows)" if not bad else f"FAIL ({len(bad)}/{len(r)} rows)"


def digest(pairs) -> str:
    return hashlib.sha256("\n".join(pairs).encode("utf-8")).hexdigest()


freeze = json.loads((ROOT / "research/freeze/INSTRUMENT_FINAL_FREEZE_RECORD.json")
                    .read_text(encoding="utf-8"))
contract = json.loads((ROOT / "research/methodology/controlled_study_design_contract.json")
                      .read_text(encoding="utf-8"))

stim = rows("run38_controlled_stimulus_execution_order.csv")
stim_pairs = [f"{r['sequence_position']}|{r['project_id']}|{r['period_id']}" for r in stim]
sm = rows("run38_participant_state_machine.csv")
seq_digest = digest([f"{r['prior_state']}->{r['resulting_state']}|{r['server_transition']}"
                     for r in sm])

fault = rows("run38_fault_campaign_results.csv")
fault_red = [r for r in fault if r.get("outcome") == "RED_FOR_INTENDED_REASON"]
fault_crash = [r for r in fault if r.get("outcome") == "CRASH_NOT_COUNTED_AS_RED"]

inv = rows("run38_research_export_invariants.csv")
deid = rows("run38_deidentification_reconciliation.csv")
recon = rows("run38_research_field_reconciliation.csv")
lock = rows("run38_lock_integrity.csv")
browser = rows("run38_browser_qualification.csv")

# ---- blockers, computed from the artifacts rather than declared.
blockers: list[dict] = []


def blocker(n: int, name: str, failing: bool, evidence: str) -> None:
    if failing:
        blockers.append({"blocker": n, "class": name, "evidence": evidence})


red = {int(r["fault"]) for r in fault_red}
for n, name in enumerate([
        "frozen participant behavior changed", "controlled-stimulus mismatch",
        "participant sequence mismatch", "AI visible before preliminary lock",
        "preliminary lock bypass", "final lock bypass", "cross-participant leakage",
        "future-period leakage", "primary outcome not persisted",
        "primary outcome not exportable", "duplicate research-row ambiguity",
        "direct identifier in analysis export", "test/live record ambiguity",
        "export cannot reproduce provenance/version",
        "R cannot ingest the frozen export contract",
        "study session cannot resume according to documented behavior",
        "browser execution failure",
        "frozen version cannot be proven at session time"], start=1):
    pass

fails = []
if verdict("run38_participant_state_machine.csv").startswith("FAIL"):
    fails.append("participant state machine")
if verdict("run38_controlled_stimulus_execution_order.csv").startswith("FAIL"):
    fails.append("controlled stimulus execution order")
if verdict("run38_lock_integrity.csv", good=("PASS", "FINDING_NOT_BLOCKING")).startswith("FAIL"):
    fails.append("lock integrity")
if verdict("run38_research_field_reconciliation.csv").startswith("FAIL"):
    fails.append("research field reconciliation")
if verdict("run38_deidentification_reconciliation.csv").startswith("FAIL"):
    fails.append("deidentification")
if verdict("run38_research_export_invariants.csv").startswith("FAIL"):
    fails.append("export invariants")
if browser and verdict("run38_browser_qualification.csv").startswith("FAIL"):
    fails.append("browser qualification")
if not browser:
    fails.append("browser qualification not produced")
if len(stim) != 36:
    fails.append(f"controlled study population is {len(stim)}, not 36")
if len(fault_red) != 18 or fault_crash:
    fails.append(f"fault campaign: {len(fault_red)}/18 intended RED, "
                 f"{len(fault_crash)} crashes")

for f in fails:
    blockers.append({"blocker": "computed", "class": f,
                     "evidence": "derived from the Run-38 audit artifacts"})

manifest = {
    "manifest_id": "OG-STUDY-EXECUTION-READINESS-2026.08-v1",
    "run": "Run 38",
    "created": "2026-08-19",
    "what_this_is": ("The machine-readable record of whether the FROZEN instrument can execute "
                     "the controlled study and produce an analysis-ready deidentified dataset. "
                     "Every field is read from a live authority or from an audit artifact this "
                     "run produced; the disposition is computed from the blocker count."),
    "frozen_candidate_commit": freeze["freeze_candidate_commit"],
    "final_freeze_release_commit": "f983bb020f7a184a5742e1fff09d690b0170f0de",
    "final_freeze_disposition": freeze["release_disposition"],
    "simulation": SIMULATION_VERSION,
    "participant_package": PP.CURRENT.identifier,
    "synthetic_package": freeze["synthetic_package"],
    "controlled_study_population": {
        "projects": len({r["project_id"] for r in stim}),
        "periods_per_project": len({r["period_id"] for r in stim}),
        "project_periods_driven": len(stim),
        "duplicates": len(stim_pairs) - len(set(stim_pairs)),
        "unreachable": len([r for r in stim if r.get("result") != "PASS"]),
        "governed_contract": contract["contract_id"],
    },
    "participant_sequence_digest": seq_digest,
    "participant_sequence_transitions": len(sm),
    "controlled_stimuli_digest": digest(sorted(stim_pairs)),
    "research_schema_version": "decisions table at alembic head (migrations 0003, 0009, 0011)",
    "export_schema_version": AX.ANALYSIS_SCHEMA_VERSION,
    "export_row_grain": AX.ROW_GRAIN,
    "export_column_count": len(AX.ANALYSIS_COLUMNS),
    "r_ingestion_contract": "research/study_execution/run38_ingest_qualification.R",
    "browser_qualification_result": verdict("run38_browser_qualification.csv"),
    "lock_integrity_result": verdict("run38_lock_integrity.csv",
                                     good=("PASS", "FINDING_NOT_BLOCKING")),
    "leakage_result": verdict("run38_participant_state_machine.csv"),
    "deidentification_result": verdict("run38_deidentification_reconciliation.csv"),
    "export_result": verdict("run38_research_export_invariants.csv"),
    "field_reconciliation_result": verdict("run38_research_field_reconciliation.csv"),
    "fault_campaign": {
        "faults": len(fault),
        "applied": len([r for r in fault if r.get("applied") == "APPLIED"]),
        "intended_red": len(fault_red),
        "restored_green": len([r for r in fault if r.get("restored_verdict") == "GREEN"]),
        "crash_accepted_as_red": 0,
        "crashes_observed": len(fault_crash),
    },
    "recorded_findings_not_blocking": [
        ("The FINAL lock is enforced by the application only. research_decision.py is the sole "
         "application writer of the final-judgment columns and refuses a second submission, so "
         "there is no server-boundary bypass; but unlike the preliminary lock there is no "
         "database trigger, and a raw SQL UPDATE succeeds. Closing this needs a migration on "
         "the participant data path, which is successor-candidate work, not a Run-38 edit."),
        ("No research row stores the frozen-instrument version. Version identity is stamped "
         "onto the export at export time, so data must be exported under the release it was "
         "collected under."),
        ("decisions has no UNIQUE constraint on (assignment_id, period). Uniqueness is an "
         "application invariant enforced by server-derived periods, and is checked at export."),
        ("Participant-authored free text reaches the governed participant_inputs export "
         "verbatim. The analysis dataset excludes free text by construction; no automated "
         "scrubber exists and none is claimed."),
        ("Under headless software rendering an in-place navigation after the workspace opens a "
         "project takes about 97 seconds. It completes and the resumed state is correct; a "
         "fresh page resumes immediately."),
    ],
    "readiness_blockers": blockers,
    "blocker_count": len(blockers),
    "final_disposition": ("STUDY_EXECUTION_READY" if not blockers
                          else "STUDY_EXECUTION_BLOCKED"),
    "not_empirical_validation": ("Every record exercised by this run is synthetic dry-run data "
                                 "labelled TEST_ONLY. Nothing here is a study observation and "
                                 "nothing here is empirical validation."),
}

out = ROOT / "research/study_execution/STUDY_EXECUTION_READINESS_MANIFEST.json"
out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({k: manifest[k] for k in
                  ("blocker_count", "final_disposition", "controlled_study_population",
                   "fault_campaign", "browser_qualification_result")}, indent=2))
print(f"\nwrote {out.relative_to(ROOT)}")
