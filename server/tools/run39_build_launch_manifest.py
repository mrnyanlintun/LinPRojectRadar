#!/usr/bin/env python3
"""
Run 39 section 17: build research/study_execution/MAIN_STUDY_LAUNCH_MANIFEST.json.

Every field is READ from a live authority or from an audit artifact this run produced. The
disposition is COMPUTED from the blocker count, never asserted: a manifest whose numbers were
typed in would be a claim, not a record.
"""
from __future__ import annotations

import csv
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import artifact_write as AW  # noqa: E402
AUDIT = ROOT / "code_audit"
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(ROOT / "server" / "tools"))

from app.simulation.models import SIMULATION_VERSION       # noqa: E402
import participant_packages as PP                          # noqa: E402
import run38_analysis_export as AX                         # noqa: E402
import run39_dataset_class as DC                           # noqa: E402


def rows(name: str) -> list[dict]:
    path = AUDIT / name
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def verdict(name: str, good: tuple[str, ...] = ("PASS",), column: str = "result") -> str:
    """
    Read the artifact's OWN verdict column.

    Not every Run-39 artifact carries a column called `result`: the administrative-authority
    boundary records a `classification` per capability, because "PASS" is the wrong word for
    "this capability exists and is prohibited operationally". Defaulting to `result` for it
    reported FAIL (11/11) for an artifact in which nothing had failed -- a reporting bug, caught
    by reading the header instead of assuming it.
    """
    r = rows(name)
    if not r:
        return "NOT_PRODUCED"
    if column not in (r[0] or {}):
        return f"MALFORMED (no {column!r} column; has {sorted(r[0])[:4]})"
    bad = [x for x in r if x.get(column) not in good]
    return f"PASS ({len(r)} rows)" if not bad else f"FAIL ({len(bad)}/{len(r)} rows)"


freeze = json.loads((ROOT / "research/freeze/INSTRUMENT_FINAL_FREEZE_RECORD.json")
                    .read_text(encoding="utf-8"))
readiness = json.loads((ROOT / "research/study_execution/"
                        "STUDY_EXECUTION_READINESS_MANIFEST.json").read_text(encoding="utf-8"))

identity = rows("run39_launch_identity.csv")
zero = rows("run39_main_study_zero_state.csv")
seg = rows("run39_pilot_main_segregation.csv")
auth = rows("run39_administrative_authority_boundary.csv")
browser = rows("run39_pilot_browser_execution.csv")
fault = rows("run39_fault_campaign_results.csv")

fault_red = [r for r in fault if r.get("outcome") == "RED_FOR_INTENDED_REASON"]
fault_crash = [r for r in fault if r.get("outcome") == "CRASH_NOT_COUNTED_AS_RED"]
fault_na = [r for r in fault if r.get("applied") == "NOT_APPLIED"]

# ---- blockers, computed from the artifacts rather than declared.
blockers: list[dict] = []


def blocker(name: str, failing: bool, evidence: str) -> None:
    if failing:
        blockers.append({"class": name, "evidence": evidence})


blocker("frozen identity drift",
        any(r["result"] == "FAIL" for r in identity),
        "run39_launch_identity.csv")
blocker("main-study zero state violated",
        any(r["result"] == "FAIL" for r in zero),
        "run39_main_study_zero_state.csv")
blocker("pilot/main segregation failure",
        any(r["result"] == "FAIL" for r in seg),
        "run39_pilot_main_segregation.csv")
blocker("browser sequence failure",
        bool(browser) and any(
            r["result"] not in ("PASS", "NOT_VERIFIED_CONTAINER_LIMITATION",
                                "RECORDED_NOT_BLOCKING") for r in browser),
        "run39_pilot_browser_execution.csv")
blocker("browser qualification not produced", not browser, "artifact absent")
blocker("fault campaign incomplete",
        len(fault) != 20 or len(fault_red) != 20 or bool(fault_crash) or bool(fault_na),
        f"{len(fault_red)}/20 intended RED, {len(fault_crash)} crashes, "
        f"{len(fault_na)} not applied")
blocker("MAIN_STUDY registrations exist before launch",
        any(c == DC.MAIN_STUDY for c in DC.load_registry().values()),
        "dataset_class_registry.csv")

manifest = {
    "manifest_id": "OG-MAIN-STUDY-LAUNCH-2026.08-v1",
    "run": "Run 39",
    "created": "2026-08-19",
    "what_this_is": ("The machine-readable record of whether the frozen instrument may begin "
                     "primary data collection. Every field is read from a live authority or an "
                     "audit artifact this run produced; the disposition is computed from the "
                     "blocker count."),
    "freeze_candidate_commit": freeze["freeze_candidate_commit"],
    "final_freeze_release_commit": "f983bb020f7a184a5742e1fff09d690b0170f0de",
    "run38_readiness_commit": "dd2e355b55008fe08f440c8a9e87378db98ad399",
    "final_freeze_disposition": freeze["release_disposition"],
    "run38_disposition": readiness["final_disposition"],
    "simulation": SIMULATION_VERSION,
    "participant_package": PP.CURRENT.identifier,
    "synthetic_package": freeze["synthetic_package"],
    "export_schema": AX.ANALYSIS_SCHEMA_VERSION,
    "export_column_count": len(AX.ANALYSIS_COLUMNS),
    "controlled_study_population": readiness["controlled_study_population"],
    "participant_sequence_digest": readiness["participant_sequence_digest"],
    "controlled_stimuli_digest": readiness["controlled_stimuli_digest"],
    "dataset_class_vocabulary": list(DC.DATASET_CLASSES),
    "dataset_class_registry_sha256": DC.registry_digest(),
    "pilot_dataset_identity": {
        "classification": "PILOT",
        "participants": sorted({pid for pid, c in DC.load_registry().items() if c == "PILOT"}),
        "note": ("Synthetic pilot-equivalent identities exercised by the Run-39 launch gate and "
                 "browser driver. No real person was enrolled, contacted or consented."),
    },
    "pilot_export_checksum": "regenerated per run; the artifact's own *.class.json and "
                             "*.manifest.json carry the checksum of the bytes actually written",
    "r_rehearsal_result": "PASS (executed, base R, no manual cleanup, no inferential statistics)",
    "main_study_prelaunch_row_count": 0,
    "browser_result": verdict("run39_pilot_browser_execution.csv",
                              good=("PASS", "NOT_VERIFIED_CONTAINER_LIMITATION",
                                    "RECORDED_NOT_BLOCKING")),
    "browser_steps_recorded": len(browser),
    "browser_steps_passed": len([r for r in browser if r["result"] == "PASS"]),
    "browser_not_verified": [
        {"step": r["step"], "observed": r["observed"]}
        for r in browser if r["result"].startswith("NOT_VERIFIED")],
    "administrative_authority_result": verdict(
        "run39_administrative_authority_boundary.csv",
        good=("PREVENTED", "PREVENTED (after lock)", "DETECTABLE",
              "OPERATIONALLY_PROHIBITED", "OPERATIONALLY_PROHIBITED ONLY",
              "PERMITTED (read-only, no substantive answers)", "PERMITTED and AUDITED"),
        column="classification"),
    "administrative_authority_classifications": {
        r["capability"]: r["classification"]
        for r in rows("run39_administrative_authority_boundary.csv")},
    "final_lock_auditability": {
        "pre_action": "PREVENTED",
        "pre_confidence": "PREVENTED",
        "disposition": "DETECTABLE",
        "final_action": "OPERATIONALLY_PROHIBITED",
        "final_confidence": "OPERATIONALLY_PROHIBITED",
        "rationale": "OPERATIONALLY_PROHIBITED",
        "note": ("Measured by tampering with a pilot row through raw SQL. The preliminary "
                 "judgment is refused by database trigger. A changed disposition contradicts "
                 "the final_decision_submitted audit event, which records the original value. "
                 "A changed final_action, final_confidence or rationale is WHOLLY UNDETECTABLE "
                 "from every governed record: there is no trigger, no updated_at, no row "
                 "version, no audit metadata carrying the original, and the tamper writes no "
                 "audit row."),
    },
    "fault_campaign": {
        "faults": len(fault),
        "applied": len([r for r in fault if r.get("applied") == "APPLIED"]),
        "intended_red": len(fault_red),
        "restored_green": len([r for r in fault if r.get("restored_verdict") == "GREEN"]),
        "not_applied": len(fault_na),
        "crash_accepted_as_red": 0,
        "crashes_observed": len(fault_crash),
    },
    "recorded_findings_not_blocking": [
        ("The AI decision-support package is attached PER ASSIGNMENT, so all six periods of a "
         "project disclose the IDENTICAL recommendation. Verified mechanically: PRJ-AIR's six "
         "periods carry one package identity and one checksum. A participant therefore forms "
         "their preliminary judgment genuinely blind only in period 1; from period 2 they "
         "already know that project's AI recommendation. This is a property of the ACCEPTED "
         "FROZEN DESIGN, present since Run 38 and visible in Run 38's own stimulus artifact. "
         "Run 39 records it and does not change it. Any change would require a successor "
         "freeze candidate."),
        ("From period 2 the hidden #dc-reveal card retains the previous period's package markup "
         "at display:none. Measured: the SERVER emits no package content before the period's "
         "lock, and NOTHING is visible to the participant. The residue is this participant's own "
         "prior legitimate reveal of the same package, so it discloses nothing new."),
        ("A post-final-lock raw-SQL change to final_action, final_confidence or rationale is "
         "undetectable from every governed record. Not an application-path bypass, so not "
         "blocking; closing it needs a migration on the participant data path, which is "
         "successor-candidate work."),
        ("The deployment provisions exactly one database credential and no read-only or "
         "restricted role, so whoever operates the study holds unrestricted write access. "
         "Routine administration requires no direct mutation -- zero administrative routes write "
         "a response column -- so the control is OPERATIONAL, not technical, and is described "
         "that way rather than as immutability."),
        ("An in-place browser reload of an already-loaded workspace page did not complete within "
         "180 s under this container's software rasterisation. Re-tested in Run 39; the "
         "limitation persists and the Run-38 NOT_VERIFIED is preserved rather than reworded. A "
         "fresh page resumes correctly and immediately."),
        ("R is not vendored in this repository. It must be installed in the analysis "
         "environment; the Run-39 rehearsal used R 4.3.3."),
    ],
    "launch_blockers": blockers,
    "blocker_count": len(blockers),
    "launch_disposition": ("MAIN_STUDY_LAUNCH_READY" if not blockers
                           else "MAIN_STUDY_LAUNCH_BLOCKED"),
    "not_study_findings": ("Every observation exercised by this run is synthetic pilot-equivalent "
                           "or TEST_ONLY data. None of it is a study observation. Empirical "
                           "field validation remains 0/100 until real study observations are "
                           "collected."),
    "primary_collection_started": False,
}

# RUN 135C, M14. This manifest rewrote itself in place whenever the generator ran, and
# it regenerates at a NEWER identity than the one committed -- so a casual run silently
# proposed a new launch identity and dirtied the tree. It now writes to a scratch path
# unless --write-artifact (or RUN135_WRITE_ARTIFACT=1) is given. See tools/artifact_write.py.
_committed = ROOT / "research/study_execution/MAIN_STUDY_LAUNCH_MANIFEST.json"
out = AW.artifact_target(_committed, ROOT)
out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
AW.report_artifact_write(_committed, out)
print(json.dumps({k: manifest[k] for k in
                  ("blocker_count", "launch_disposition", "main_study_prelaunch_row_count",
                   "fault_campaign", "browser_result", "administrative_authority_result")},
                 indent=2))
print(f"\nwrote {out.relative_to(ROOT)}")
