#!/usr/bin/env python3
"""
RUN 47. THE SUCCESSOR FREEZE RELEASE RECORDS.

Writes, beside the v25 and v26 releases and never over either:

  research/freeze/RUN47_SUCCESSOR_FREEZE_RECORD.json
  research/freeze/RUN47_SUCCESSOR_FREEZE_REPORT.md
  research/freeze/RUN47_SUCCESSOR_FREEZE_CHECKSUMS.csv

The historical relationship is explicit in every one of them:

    v25 accepted freeze -> Run 40 identified S1/S2 -> owner authorised remediation
    -> v26 successor -> Run 42 proved two identity losses -> v27 successor
    -> owner's retirement ruling -> v28 successor -> Run 43J diagnosed eleven render defects
    -> owner ordered four of them repaired -> v29 successor -> Run 44 measured the period-scoping
    fall-through -> owner signed off the canonical field classification -> v30 successor

The v25, v26, v27, v28 and v29 records remain exactly as Runs 37, 41, 42, 43 and 44 wrote them. They are
the evidence for anything computed under those stamps and a successor that edited them would
destroy it.

Usage: python tools/build_run47_successor_release.py
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

PREDECESSOR_RECORD = FREEZE / "RUN45_SUCCESSOR_FREEZE_RECORD.json"
PREDECESSOR_CHECKSUMS = FREEZE / "RUN45_SUCCESSOR_FREEZE_CHECKSUMS.csv"
IDENTITY = FREEZE / "run47_freeze_candidate_identity.json"
GATE = FREEZE / "run47_successor_freeze_gate.csv"
BEHAVIOUR = FREEZE / "run47_candidate_behaviour_digest.json"


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
                     "moved_since_v30": "YES" if h != r["sha256"] else "no"})
    for extra in ("research/freeze/run47_freeze_candidate_identity.json",
                  "research/freeze/run47_successor_freeze_gate.csv",
                  "server/app/evm_consistency.py",
                  "server/tools/test_run47_evm_consistency.py",
                  "server/tools/drive_run47_browser.py"):
        p = ROOT / extra
        rows.append({"path": extra, "sha256": sha(p), "git_object": git_object(p),
                     "tracked": "TRACKED", "moved_since_v30": "ADDED_BY_RUN47"})

    out_sums = FREEZE / "RUN47_SUCCESSOR_FREEZE_CHECKSUMS.csv"
    with out_sums.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["path", "sha256", "git_object", "tracked",
                                           "moved_since_v30"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    release_digest = hashlib.sha256(out_sums.read_text(encoding="utf-8").encode()).hexdigest()

    rec = {
        "release_disposition": "FINAL_FREEZE_ACCEPTED",
        "label": "Opus Gubernatio research instrument, Run-47 successor freeze (sim-2026.08-v31)",
        "created": datetime.date(2026, 8, 22).isoformat(),
        "authority": (
            "The owner's four rulings of 2026-08-22 in the Run 47 order, section 2. 1. THE "
            "DOCUMENT TAKES PRECEDENCE: the value a document states is stored as given, nothing "
            "is derived from a percentage and nothing is overridden. 2. THE PLATFORM COMPUTES "
            "THE IMPLIED VALUE AND COMPARES. 3. TOLERANCE IS 2 PER CENT: above it is a "
            "disagreement, at or below it is not reported. 4. A DISAGREEMENT IS CARRIED INTO "
            "THE EXECUTIVE BRIEF AND THE RECOMMENDATION AS TEXT and does not change the "
            "recommendation's posture. There is no adjudication, no stored decision, no "
            "suppression, no user-facing control and no per-document dismissal."),
        "supersedes_candidate": pred["freeze_candidate_commit"],
        "supersedes_simulation_version": pred["simulation_version"],
        "history": [
            "Run 37 accepted the final freeze of the v25 instrument.",
            "Run 41 closed the two HIGH defects Run 40 confirmed and stamped sim-2026.08-v26.",
            "Run 42 repaired two identity losses in the data-processing mechanism and proved "
            "period binding correct; sim-2026.08-v27.",
            "Run 43 retired 38 of the 101 registered modules from service; sim-2026.08-v28.",
            "Run 44 repaired four participant-facing render defects; sim-2026.08-v29.",
            "Run 45 implemented retrieval by canonical field kind on the owner's signed-off "
            "classification; sim-2026.08-v30.",
            "Run 46 traced the CPI defect from code and minted nothing: it established that "
            "CPI 1.22 still reproduces exactly, that pv = 824,370 and SPI 1.27 do not reproduce "
            "from a period-consistent document set, and that pv is a PERIOD field that cannot "
            "carry forward. THIS RUN DOES NOT ATTEMPT TO EXPLAIN THE RENDER.",
            "Run 47 built the check that would have caught it: where one document states both a "
            "value and the percentage that determines it against a known budget at completion, "
            "the two are compared and a difference above 2 per cent is reported as text on "
            "surfaces that already exist; sim-2026.08-v31.",
            "The v25, v26, v27, v28, v29 and v30 releases remain historical evidence and are "
            "not rewritten. Results computed under any of them remain interpretable against "
            "their own records.",
        ],
        "freeze_candidate_commit": ident["candidate_git_commit"],
        "candidate_identity_digest": ident["candidate_identity_digest"],
        "candidate_behaviour_digest": behav["behaviour_digest"],
        "release_content_digest": release_digest,
        "release_content_digest_method": (
            "sha256 over RUN47_SUCCESSOR_FREEZE_CHECKSUMS.csv, which content-addresses every "
            "governed file of the successor instrument. Reproducible from the tree alone."),
        "release_commit_recording_method": pred["release_commit_recording_method"],
        "simulation_version": SIMULATION_VERSION,
        "simulation_version_history": list(SIMULATION_VERSION_HISTORY),
        "participant_package": PP.CURRENT.identifier,
        "participant_package_decision": (
            "RETAINED at og-participant-2026.08-v15. Determined mechanically, not assumed: NONE "
            "of the six sequence-bearing files moved. Run 47 adds TEXT to two surfaces that "
            "already exist, the Executive Brief and the courses-of-action card. No step of the "
            "decision sequence, no reveal gate, no lock, no randomization and NO USER-FACING "
            "CONTROL was added, moved or removed; the disagreement blocks were measured in the "
            "rendered DOM to contain zero controls of any kind."),
        "synthetic_package": "OG-SYNTH-0.6",
        "analysis_schema": "og-analysis-2026.08-v1",
        "canonical_field_classification": {
            "identity": 13, "period": 62, "undetermined": 2, "total_emittable": 77,
            "authority": "code_audit/run45_field_classification_proposal.md, and the owner's "
                         "ruling recorded in REPORT_2026-08-22_run45_period_scoping_fix.md",
            "declared_in": "server/app/field_registry.py IDENTITY_FIELDS / PERIOD_FIELDS / "
                           "UNDETERMINED_FIELDS, asserted at import to partition FIELD_KINDS",
        },
        "behavioural_delta_v30_to_v31": [
            "a served result now carries `consistency_findings`: every relation where ONE "
            "document stated both a value and the percentage that determines it against a known "
            "budget at completion, and the two differ by more than 2 per cent of the implied "
            "value",
            "the Executive Brief renders that text, deterministically, from the stored row and "
            "not from the generated brief",
            "the courses-of-action card renders it beside the recommendation, on both the "
            "available and the unavailable branch",
            "the retired 'Cat N' labels in BRIEF_CAT_LABEL are groups and purposes only",
        ],
        "behavioural_delta_scope_statement": (
            "Exactly these four. NOTHING IS DERIVED INTO STORAGE and NO STORED FIGURE MOVED: "
            "the check is a pure function called on the READ path from the stored row, so it "
            "cannot write. No formula, band, threshold, calibration, abstention rule or "
            "population moved: voting is still exactly A1.7 and A1.8, 63 modules in service of "
            "101 registered. The full served census -- every module result, every category "
            "status, every band, every colour, every posture and every abstention -- is "
            "IDENTICAL with and without a disagreement present, asserted against a fixture that "
            "genuinely holds one and against the same serve with the finding suppressed. `pv` "
            "is absent from BOUNDED_MAX_SI_FIELDS and stays absent: the remedy is a comparison, "
            "not a clamp."),
        "defects_closed": {
            "unchecked_value_percentage_relation": (
                "A document stating both a value and the percentage that determines it against "
                "a known budget at completion could disagree with itself without the platform "
                "noticing. On the render that prompted this run a planned value of 824,370 sat "
                "against an implied 1,085,042, a difference of 24.02 per cent of the implied "
                "value, and schedule performance read 1.27 where the same document's "
                "percentages imply 0.964. The disagreement is now computed and reported. It is "
                "NOT corrected: the document's figure stands."),
            "retired_cat_n_labels": (
                "BRIEF_CAT_LABEL carried ten entries in the retired 'Cat N' scheme against "
                "NAMING_AUTHORITY.md:96, found by Run 44 and carried unacted by Runs 45 and 46. "
                "Corrected to groups and purposes."),
        },
        "known_limitation_relations_not_implemented": (
            "The section 5 sweep found ONE further pair with a value-and-percentage shape that "
            "was NOT implemented: historical_data states analogous_overrun_pct together with "
            "similar_project_bac and similar_project_final_cost. Those three determine each "
            "other against the REFERENCE project's budget at completion, not this project's, "
            "and section 5's first condition is written about the project's own known budget at "
            "completion. It is recorded rather than implemented, and no stored value would need "
            "deriving or overriding to implement it later."),
        "recorded_split_document_case": (
            "Where a value and its percentage come from DIFFERENT documents the check does not "
            "run and reports nothing, by section 5's second condition. The case is reachable "
            "and was constructed: a Time-phased Schedule stating only the planned value and a "
            "Monthly Progress Report stating only the planned percent complete produce two "
            "different documentIds in signal_inputs.sources and no finding."),
        "scientific_state_unchanged": (
            "NO input was invented, NO fact fabricated, NO qualification rule relaxed and NO "
            "scientific method changed. A module that abstains still abstains, with the same "
            "reason and the same code. Nothing was corrected, substituted, clamped or bounded. "
            "Every expected figure in the Run 47 suite was hand-computed from the stated "
            "formula and written as a literal; the order's own arithmetic was re-derived rather "
            "than copied, and one slip in it was found and reported rather than echoed."),
        "unresolved_high_security_blockers": 0,
        "freeze_gate": {"blockers_evaluated": len(gate), "blocked": len(blocked),
                        "artifact": "research/freeze/run47_successor_freeze_gate.csv"},
        "blocking_defects": 0,
        "limitation_contract": pred["limitation_contract"],
        "predecessor_references": {
            "v25_release_record": "research/freeze/INSTRUMENT_FINAL_FREEZE_RECORD.json",
            "v26_release_record": "research/freeze/RUN41_SUCCESSOR_FREEZE_RECORD.json",
            "v27_release_record": "research/freeze/RUN42_SUCCESSOR_FREEZE_RECORD.json",
            "v28_release_record": "research/freeze/RUN43_SUCCESSOR_FREEZE_RECORD.json",
            "v29_release_record": "research/freeze/RUN44_SUCCESSOR_FREEZE_RECORD.json",
            "v30_release_record": "research/freeze/RUN45_SUCCESSOR_FREEZE_RECORD.json",
            "v30_candidate_identity": "research/freeze/run45_freeze_candidate_identity.json",
            "v30_freeze_gate": "research/freeze/run45_successor_freeze_gate.csv",
            "statement": ("All of these are preserved unchanged. That they still record v25, "
                          "v26, v27, v28, v29 and v30 is asserted by the requalified gates, not "
                          "assumed."),
        },
        "governed_files_moved_since_v30": moved,
    }
    (artifact_out(FREEZE / "RUN47_SUCCESSOR_FREEZE_RECORD.json")).write_text(
        json.dumps(rec, indent=2) + "\n", encoding="utf-8")

    report = f"""# Run-47 successor freeze report

**Disposition: FINAL_FREEZE_ACCEPTED** for `sim-2026.08-v31`.

## Why there is a successor at all

A Time-phased Schedule states a planned value to date and a planned percent complete in the same
document. Against a known budget at completion the two determine each other, and on the render
that prompted this run they did not agree: a stated 824,370 against a budget at completion of
5,874,620 and a planned percent complete of 18.47, which implies 1,085,042. The platform
extracted both figures, stored both, and never compared them. Schedule performance is earned
value over planned value, so a planned value that low reads a project as ahead of schedule when
the document's own percentages say it is behind.

What a served result CARRIES is executable behaviour, so v30 is **superseded, not amended**.

    v25 accepted freeze -> S1/S2 -> v26 -> mechanism repair -> v27 -> retirement -> v28
    -> render repairs -> v29 -> retrieval by field kind -> v30 -> Run 46's CPI trace
    -> owner's four rulings -> v31 successor

## The four rulings, and what each became

| ruling | what was built |
|---|---|
| The document takes precedence | `pv` and `ev` are stored exactly as stated. Nothing is derived into storage, nothing is clamped, and `pv` is still absent from `BOUNDED_MAX_SI_FIELDS` |
| The platform computes the implied value and compares | `server/app/evm_consistency.py`, a pure function called on the READ path from the stored row |
| Tolerance is 2 per cent | `TOLERANCE = 0.02`, measured against the **implied** value; both sides of the boundary are exercised |
| A disagreement is text, not a posture change | Rendered on the Executive Brief and beside the recommendation. The full census with and without it is identical |

## What changed, and what did not

| Subject | Result |
|---|---|
| Stored `pv`, `ev`, `bac`, percentages | **unchanged**, byte-identical across a full recompute |
| Project status, category statuses, bands, colours, postures | **identical** with and without a disagreement |
| Abstentions | **identical**; no module abstains that would otherwise compute |
| Registered / in service / voting | 101 / 63 / exactly A1.7 and A1.8, all identical |
| Sequence-bearing participant files | **none moved** |
| User-facing controls | **none added, moved or removed**; the rendered blocks hold zero controls |
| Participant package | RETAINED `og-participant-2026.08-v15` |
| Synthetic package | RETAINED `OG-SYNTH-0.6` |
| Analysis schema | RETAINED `og-analysis-2026.08-v1` |

## Gate

{len(gate)} blocker classes evaluated, {len(blocked)} blocked. Artifact:
`research/freeze/run47_successor_freeze_gate.csv`.

The v25, v26, v27, v28, v29 and v30 release records are preserved unchanged and still record
their own stamps.
"""
    (artifact_out(FREEZE / "RUN47_SUCCESSOR_FREEZE_REPORT.md")).write_text(report, encoding="utf-8")

    print("wrote RUN47_SUCCESSOR_FREEZE_CHECKSUMS.csv:", len(rows), "rows")
    print("wrote RUN47_SUCCESSOR_FREEZE_RECORD.json")
    print("wrote RUN47_SUCCESSOR_FREEZE_REPORT.md")
    print("governed files moved since v30:", moved or "(none)")
    print("release content digest:", release_digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
