#!/usr/bin/env python3
"""
RUN 42. THE SUCCESSOR FREEZE RELEASE RECORDS.

Writes, beside the v25 and v26 releases and never over either:

  research/freeze/RUN42_SUCCESSOR_FREEZE_RECORD.json
  research/freeze/RUN42_SUCCESSOR_FREEZE_REPORT.md
  research/freeze/RUN42_SUCCESSOR_FREEZE_CHECKSUMS.csv

The historical relationship is explicit in every one of them:

    v25 accepted freeze -> Run 40 identified S1/S2 -> owner authorised remediation
    -> v26 successor -> Run 42 proved two identity losses in the period-binding and
    evidence-lineage mechanism -> v27 successor -> requalification

The v25 and v26 records remain exactly as Runs 37 and 41 wrote them. They are the evidence for
anything computed under those stamps and a successor that edited them would destroy it.

Usage: python tools/build_run42_successor_release.py
"""
from __future__ import annotations
# Run 137, Item 2: artefact writes route to the Run 135C scratch root by default.
import os as _f10_os, sys as _f10_sys  # noqa: E402
_f10_sys.path.insert(0, _f10_os.path.join(
    _f10_os.path.dirname(_f10_os.path.abspath(__file__)), "..", "tools"))
_f10_sys.path.insert(0, _f10_os.path.dirname(_f10_os.path.abspath(__file__)))
from artifact_write import artifact_out  # noqa: E402

import csv
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
FREEZE = ROOT / "research" / "freeze"
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from app.simulation.models import (  # noqa: E402
    SIMULATION_VERSION, SIMULATION_VERSION_HISTORY)
import participant_packages as PP  # noqa: E402

PREDECESSOR_RECORD = FREEZE / "RUN41_SUCCESSOR_FREEZE_RECORD.json"
PREDECESSOR_CHECKSUMS = FREEZE / "RUN41_SUCCESSOR_FREEZE_CHECKSUMS.csv"
IDENTITY = FREEZE / "run42_freeze_candidate_identity.json"
GATE = FREEZE / "run42_successor_freeze_gate.csv"
BEHAVIOUR = FREEZE / "run42_candidate_behaviour_digest.json"


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git_object(p: pathlib.Path) -> str:
    return subprocess.run(["git", "hash-object", str(p)], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout.strip()


def main() -> int:
    pred = json.loads(PREDECESSOR_RECORD.read_text(encoding="utf-8"))
    ident = json.loads(IDENTITY.read_text(encoding="utf-8"))
    behav = json.loads(BEHAVIOUR.read_text(encoding="utf-8"))
    with GATE.open(encoding="utf-8", newline="") as fh:
        gate = list(csv.DictReader(fh))
    blocked = [r for r in gate if r["result"] != "PASS"]
    if blocked:
        raise SystemExit(f"the successor gate reports {len(blocked)} blockers; refusing to write "
                         f"a release record while any blocker stands: "
                         f"{[r['blocker_id'] for r in blocked]}")

    # ---------------------------------------------------------------- checksum manifest
    # THE SAME GOVERNED FILE LIST AS THE PREDECESSOR, re-measured against the successor tree,
    # for the same reason Run 41 kept Run 37's: a successor that also changed WHAT it measures
    # could not be compared with the release it supersedes.
    with PREDECESSOR_CHECKSUMS.open(encoding="utf-8", newline="") as fh:
        pred_rows = list(csv.DictReader(fh))
    rows, moved = [], []
    for r in pred_rows:
        p = ROOT / r["path"]
        if not p.is_file():
            raise SystemExit(f"a governed file named by the predecessor manifest is missing: "
                             f"{r['path']}")
        h = sha(p)
        if h != r["sha256"]:
            moved.append(r["path"])
        rows.append({"path": r["path"], "sha256": h, "git_object": git_object(p),
                     "tracked": r["tracked"],
                     "moved_since_v26": "YES" if h != r["sha256"] else "no"})
    for extra in ("code_audit/run42_production_tree.sha256",
                  "research/freeze/run42_freeze_candidate_identity.json",
                  "research/freeze/run42_successor_freeze_gate.csv",
                  "code_audit/run42_v26_v27_execution_proof.csv",
                  "server/tools/test_run42_period_binding_mechanism.py"):
        p = ROOT / extra
        rows.append({"path": extra, "sha256": sha(p), "git_object": git_object(p),
                     "tracked": "TRACKED", "moved_since_v26": "ADDED_BY_RUN42"})

    out_sums = FREEZE / "RUN42_SUCCESSOR_FREEZE_CHECKSUMS.csv"
    with out_sums.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["path", "sha256", "git_object", "tracked",
                                           "moved_since_v26"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    release_digest = hashlib.sha256(out_sums.read_text(encoding="utf-8").encode()).hexdigest()

    rec = {
        "release_disposition": "FINAL_FREEZE_ACCEPTED",
        "label": "Opus Gubernatio research instrument, Run-42 successor freeze (sim-2026.08-v27)",
        "created": datetime.date(2026, 8, 21).isoformat(),
        "authority": (
            "The owner's instruction of 2026-08-21: fix the background data-processing and "
            "calculation mechanism, and specifically the missing document-to-fact-to-module "
            "lineage and the loss of project/period identity."),
        "supersedes_candidate": pred["freeze_candidate_commit"],
        "supersedes_simulation_version": pred["simulation_version"],
        "history": [
            "Run 37 accepted the final freeze of the v25 instrument.",
            "Run 40 confirmed two HIGH defects; the owner authorised remediation; Run 41 closed "
            "them and stamped the successor sim-2026.08-v26 at candidate "
            f"{pred['freeze_candidate_commit']}.",
            "Run 42 traced the background data-processing mechanism end to end -- upload, "
            "selected-period persistence, extraction, stored facts, module input retrieval, "
            "C1/Category-9 qualification, category calculation, project status, brief and "
            "decision, longitudinal ordering and lineage -- and proved TWO identity losses in "
            "it. Both were losses in the PATH, not absences in the data.",
            "Run 42 repaired both, stamped the successor sim-2026.08-v27, and requalified every "
            "downstream gate by executing it.",
            "The v25 and v26 releases remain historical evidence and are not rewritten. Results "
            "computed under either remain interpretable against their own records.",
        ],
        "freeze_candidate_commit": ident["candidate_git_commit"],
        "candidate_identity_digest": ident["candidate_identity_digest"],
        "candidate_behaviour_digest": behav["behaviour_digest"],
        "release_content_digest": release_digest,
        "release_content_digest_method": (
            "sha256 over RUN42_SUCCESSOR_FREEZE_CHECKSUMS.csv, which content-addresses every "
            "governed file of the successor instrument. Reproducible from the tree alone."),
        "release_commit_recording_method": pred["release_commit_recording_method"],
        "simulation_version": SIMULATION_VERSION,
        "simulation_version_history": list(SIMULATION_VERSION_HISTORY),
        "participant_package": PP.CURRENT.identifier,
        "participant_package_decision": (
            "RETAINED. Determined mechanically, not assumed: not one of the 70 governed "
            "participant-package bytes moved, the 6 sequence-bearing files are byte-identical to "
            "the v13 record, and none of the five production files Run 42 changed is named by "
            "that record. A successor was NOT minted merely because server behaviour changed."),
        "synthetic_package": "OG-SYNTH-0.6",
        "analysis_schema": "og-analysis-2026.08-v1",
        "behavioural_delta_v26_to_v27": [
            "the per-field source record carries the identity of the artefact each field was "
            "read from: documentId, documentVersion, asOf and revisionOf",
            "the qualification record names the project it is about, on the compute path and "
            "the read path alike",
        ],
        "behavioural_delta_scope_statement": (
            "Exactly these two, and nothing else. Proved by EXECUTING both lines from their own "
            "git objects rather than by reading a diff: all 101 registered modules emit "
            "byte-identical rows across the boundary, every signal input except the sources "
            "record is byte-identical, and the revision and overall qualification dimensions do "
            "not move. See code_audit/run42_v26_v27_execution_proof.csv."),
        "defects_closed": {
            "D1": {"title": "the per-field source record dropped the document identity",
                   "final_status": "CONFIRMED_FIXED",
                   "evidence": "code_audit/run42_baseline_state_chrono.json recorded 0 of 7 "
                               "fields carrying a document identity; after the repair 7 of 7 "
                               "do, and the provenance and timeliness dimensions reach PASS. "
                               "Fault F1 and F4 in code_audit/run42_fault_campaign.csv both "
                               "turn the regression suite red when reintroduced."},
            "D2": {"title": "the qualification record named a null project",
                   "final_status": "CONFIRMED_FIXED",
                   "evidence": "evidence_qualification.project_id was null for every period in "
                               "the baseline and names the project after the repair. Faults F2 "
                               "and F3 both turn the regression suite red; F2 is caught only by "
                               "the direct compute-path section, which is why that section "
                               "exists."},
        },
        "scientific_state_unchanged": (
            "NO input was invented, NO fact fabricated, NO qualification rule relaxed and NO "
            "scientific method changed. revision_resolution_status remains NOT_ESTIMABLE and "
            "overall_qualification_state therefore remains NOT_ESTIMABLE, which is a deliberate "
            "fail-closed decision Run 42 did not overturn and reports to the owner instead. The "
            "modules that abstain for want of their governed structure still abstain."),
        "unresolved_high_security_blockers": 0,
        "freeze_gate": {"blockers_evaluated": len(gate), "blocked": len(blocked),
                        "artifact": "research/freeze/run42_successor_freeze_gate.csv"},
        "fault_campaign": {"faults": 6, "intended_red": 5, "caught": 5,
                           "inert_control_correctly_green": 1,
                           "artifact": "code_audit/run42_fault_campaign.csv"},
        "blocking_defects": 0,
        "limitation_contract": pred["limitation_contract"],
        "predecessor_references": {
            "v25_release_record": "research/freeze/INSTRUMENT_FINAL_FREEZE_RECORD.json",
            "v26_release_record": "research/freeze/RUN41_SUCCESSOR_FREEZE_RECORD.json",
            "v26_candidate_identity": "research/freeze/run41_freeze_candidate_identity.json",
            "v26_freeze_gate": "research/freeze/run41_successor_freeze_gate.csv",
            "statement": ("All of these are preserved unchanged. That they still record v25 and "
                          "v26 is asserted by the requalified gates, not assumed."),
        },
        "governed_files_moved_since_v26": moved,
    }
    (artifact_out(FREEZE / "RUN42_SUCCESSOR_FREEZE_RECORD.json")).write_text(
        json.dumps(rec, indent=2) + "\n", encoding="utf-8")

    report = f"""# Run-42 successor freeze report

**Disposition: FINAL_FREEZE_ACCEPTED** for `sim-2026.08-v27`.

## Why there is a successor at all

Run 41 accepted a successor freeze of the v26 instrument. Run 42 was then instructed to fix the
background data-processing and calculation mechanism, on the rule that the reporting period a
person SELECTS at upload is authoritative and that nothing else -- upload order, document date,
filename, database insertion order, extraction completion order -- may decide it.

The mechanism was traced end to end and **most of it was already correct**. The selected period
binds correctly; extraction cannot reach the period because the period is bound before extraction
runs; there is no cross-period or cross-project retrieval; and the longitudinal series are ordered
by reporting-period identity, never by upload or computation time. Uploading four periods out of
order produces a byte-identical analytical state.

Two defects were proved, and both were losses in the PATH rather than absences in the data:

1. **The per-field source record dropped the document identity.** Every observation has always
   carried `document_id`, `sha256`, `revision_of` and `as_of`, and the stored result has always
   listed the same identity per document. The per-field record kept only the document TYPE. The
   qualification layer counts a field as traced only when it carries both an identity and a
   version, so it counted **zero on every project ever computed**, and the provenance and
   timeliness dimensions were structurally pinned to PARTIAL.

2. **The qualification record named a null project.** The compute path read the identity from a
   signal-inputs key that does not exist, and the read path hard-coded `None`, while both callers
   held the project the whole time.

Repairing either moves bytes inside a frozen surface, so v26 is **superseded, not amended**.

    v25 accepted freeze -> S1/S2 -> v26 successor -> Run 42 mechanism repair -> v27 successor

## What did NOT change, proved by execution

| Subject | Result |
|---|---|
| Registered module population | 101, identical |
| Module emitted rows across the boundary | **0 of 101 moved** |
| Signal inputs other than the source record | byte-identical |
| `revision_resolution_status` | NOT_ESTIMABLE, unchanged |
| `overall_qualification_state` | NOT_ESTIMABLE, unchanged |
| Participant package | RETAINED `og-participant-2026.08-v13`, 70 of 70 bytes identical |
| Synthetic package | RETAINED `OG-SYNTH-0.6` |
| Analysis schema | RETAINED `og-analysis-2026.08-v1` |

This is not inferred from a source diff. Both lines were extracted from their own pinned git
objects and executed on identical inputs: `code_audit/run42_v26_v27_execution_proof.csv`.

## The scientific position

No input was invented, no fact fabricated, no qualification rule relaxed and no scientific method
changed. The instrument still abstains wherever the governed structure is absent, and that is the
correct answer rather than a failure. The revision dimension remains NOT_ESTIMABLE by deliberate
decision, so the overall qualification state remains NOT_ESTIMABLE; that is reported to the owner
as a decision to take, not quietly relaxed to make categories light up.

## Gate

{len(gate)} blocker classes evaluated, {len(blocked)} blocked. Artifact:
`research/freeze/run42_successor_freeze_gate.csv`.

The v25 and v26 release records are preserved unchanged and still record their own stamps.
"""
    (artifact_out(FREEZE / "RUN42_SUCCESSOR_FREEZE_REPORT.md")).write_text(report, encoding="utf-8")

    print("wrote RUN42_SUCCESSOR_FREEZE_CHECKSUMS.csv:", len(rows), "rows")
    print("wrote RUN42_SUCCESSOR_FREEZE_RECORD.json")
    print("wrote RUN42_SUCCESSOR_FREEZE_REPORT.md")
    print("governed files moved since v26:", moved or "(none)")
    print("release content digest:", release_digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
