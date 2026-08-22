#!/usr/bin/env python3
"""
RUN 44. THE SUCCESSOR FREEZE RELEASE RECORDS.

Writes, beside the v25 and v26 releases and never over either:

  research/freeze/RUN44_SUCCESSOR_FREEZE_RECORD.json
  research/freeze/RUN44_SUCCESSOR_FREEZE_REPORT.md
  research/freeze/RUN44_SUCCESSOR_FREEZE_CHECKSUMS.csv

The historical relationship is explicit in every one of them:

    v25 accepted freeze -> Run 40 identified S1/S2 -> owner authorised remediation
    -> v26 successor -> Run 42 proved two identity losses -> v27 successor
    -> owner's retirement ruling -> v28 successor -> Run 43J diagnosed eleven render defects
    -> owner ordered four of them repaired -> v29 successor -> requalification

The v25, v26, v27 and v28 records remain exactly as Runs 37, 41, 42 and 43 wrote them. They are
the evidence for anything computed under those stamps and a successor that edited them would
destroy it.

Usage: python tools/build_run44_successor_release.py
"""
from __future__ import annotations

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

PREDECESSOR_RECORD = FREEZE / "RUN43_SUCCESSOR_FREEZE_RECORD.json"
PREDECESSOR_CHECKSUMS = FREEZE / "RUN43_SUCCESSOR_FREEZE_CHECKSUMS.csv"
IDENTITY = FREEZE / "run44_freeze_candidate_identity.json"
GATE = FREEZE / "run44_successor_freeze_gate.csv"
BEHAVIOUR = FREEZE / "run44_candidate_behaviour_digest.json"


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
                     "moved_since_v28": "YES" if h != r["sha256"] else "no"})
    for extra in ("code_audit/run44_participant_package_v15_checksums.sha256",
                  "code_audit/run44_v28_v29_execution_proof.csv",
                  "research/freeze/run44_freeze_candidate_identity.json",
                  "research/freeze/run44_successor_freeze_gate.csv",
                  "server/tools/run44_production_changes.py"):
        p = ROOT / extra
        rows.append({"path": extra, "sha256": sha(p), "git_object": git_object(p),
                     "tracked": "TRACKED", "moved_since_v28": "ADDED_BY_RUN44"})

    out_sums = FREEZE / "RUN44_SUCCESSOR_FREEZE_CHECKSUMS.csv"
    with out_sums.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["path", "sha256", "git_object", "tracked",
                                           "moved_since_v28"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    release_digest = hashlib.sha256(out_sums.read_text(encoding="utf-8").encode()).hexdigest()

    rec = {
        "release_disposition": "FINAL_FREEZE_ACCEPTED",
        "label": "Opus Gubernatio research instrument, Run-44 successor freeze (sim-2026.08-v29)",
        "created": datetime.date(2026, 8, 22).isoformat(),
        "authority": (
            "The owner's order of 2026-08-22, Run 44: the four participant-facing render defects "
            "Run 43J classified F are repaired at the render, where they are. Storage was correct "
            "in every one of them and is untouched. Section 4.4 of that order additionally "
            "authorises ONE sequence-bearing participant file to move, deepdive.js, for the "
            "Portfolio Health flyout's reason sentence."),
        "supersedes_candidate": pred["freeze_candidate_commit"],
        "supersedes_simulation_version": pred["simulation_version"],
        "history": [
            "Run 37 accepted the final freeze of the v25 instrument.",
            "Run 40 confirmed two HIGH defects; the owner authorised remediation; Run 41 closed "
            "them and stamped the successor sim-2026.08-v26.",
            "Run 42 traced the background data-processing mechanism end to end, proved two "
            "identity losses in it, repaired both and stamped the successor sim-2026.08-v27 at "
            f"candidate {pred['freeze_candidate_commit']}.",
            "Run 43 retired 38 of the 101 registered modules FROM SERVICE on the owner's ruling "
            "of 2026-08-21, and stamped the successor sim-2026.08-v28.",
            "Run 43J diagnosed eleven render defects on a participant render and classified "
            "seven F, one C and three G; it changed nothing.",
            "Run 44 repaired the four the owner ordered repaired and stamped the successor "
            "sim-2026.08-v29. All four are at the render: no server computation moved, and "
            "run_module() on all 101 identifiers is byte-identical to v28 on both a full and a "
            "starved evidence package, proved by executing both lines.",
            "The v25, v26, v27 and v28 releases remain historical evidence and are not "
            "rewritten. Results computed under any of them remain interpretable against their "
            "own records.",
        ],
        "freeze_candidate_commit": ident["candidate_git_commit"],
        "candidate_identity_digest": ident["candidate_identity_digest"],
        "candidate_behaviour_digest": behav["behaviour_digest"],
        "release_content_digest": release_digest,
        "release_content_digest_method": (
            "sha256 over RUN44_SUCCESSOR_FREEZE_CHECKSUMS.csv, which content-addresses every "
            "governed file of the successor instrument. Reproducible from the tree alone."),
        "release_commit_recording_method": pred["release_commit_recording_method"],
        "simulation_version": SIMULATION_VERSION,
        "simulation_version_history": list(SIMULATION_VERSION_HISTORY),
        "participant_package": PP.CURRENT.identifier,
        "participant_package_decision": (
            "SUPERSEDED at og-participant-2026.08-v15. Determined mechanically, not assumed: "
            "four of the 70 governed participant-package bytes moved -- detail.js, signals.js, "
            "deepdive.js and radar.css -- and ONE OF THE FOUR IS SEQUENCE-BEARING. That is "
            "stated rather than absorbed: deepdive.js carries the Portfolio Health flyout, whose "
            "reason sentence was false on every render after the Run-43 offload, and the owner "
            "ordered it corrected at Run 44 section 4.4. The other five sequence-bearing files "
            "are byte-identical to the v14 record, and no step of the decision sequence, no "
            "reveal gate, no lock, no randomization and no user-facing control moved. The v14 "
            "record is pinned to the commit whose blobs it describes and is NOT regenerated."),
        "synthetic_package": "OG-SYNTH-0.6",
        "analysis_schema": "og-analysis-2026.08-v1",
        "behavioural_delta_v28_to_v29": [
            "status comparison on the project detail page is case-insensitive at every site that "
            "orders or selects a severity, through one shared rank: a module storing lowercase "
            "'green' no longer ranks as more adverse than one storing 'Green'",
            "no surface names a module as the driver of a severity better than its own; where "
            "no module in a category is as adverse as the category, the panel says so instead",
            "an absent document-risk score renders as absent on every surface including the "
            "Executive Brief's key drivers, and a genuine stored zero still renders as zero",
            "CPI and SPI are labelled computed rather than extracted, on the signals panel and "
            "in the upload result line",
            "the Portfolio Health flyout states that the analysis is no longer in service, "
            "derived from the loaded taxonomy, instead of asking for at least three projects",
        ],
        "behavioural_delta_scope_statement": (
            "Exactly these five, and nothing else, and every one of them is at the render. "
            "Proved by EXECUTING rather than by reading a diff: the v28 line is extracted from "
            "its own pinned git object and imported as its own package, and run_module() over "
            "all 101 registered identifiers on BOTH lines against a full and a starved evidence "
            "package produces zero rows that differ, with the stamp normalised out and asserted "
            "separately so a run that minted no stamp could not pass. The comparison was proved "
            "failable by perturbing one module's own input and observing that module diverge. "
            "The merged signal inputs and their per-field source record are identical, the "
            "docRiskScore shape is still present-and-null, and the fusion returns the same band "
            "for every voting pair tried. No module in service changed its computed result. "
            "Voting is still exactly A1.7 and A1.8, Group C still does not contribute to project "
            "status, and Portfolio Health is still in service nowhere."),
        "defects_closed": {},
        "scientific_state_unchanged": (
            "NO input was invented, NO fact fabricated, NO qualification rule relaxed and NO "
            "scientific method changed. Nothing on the analytical side was touched at all: the "
            "repairs are at the render, because that is where Run 43J's evidence put them. "
            "Storage was already correct in every case and stays correct -- the document-risk "
            "score is stored present-and-null by design so a genuine zero stays distinguishable "
            "from an absence, CPI and SPI are derived values in a derived-values slot with no "
            "source record, and the category status is the server's own fusion, read verbatim by "
            "the client. The modules in service that abstain for want of their governed "
            "structure still abstain, with the same reasons and the same codes. Three of Run "
            "43J's eleven defects remain classified G and are UNRESOLVED: they need read access "
            "to stored rows this run did not have and did not take."),
        "unresolved_high_security_blockers": 0,
        "freeze_gate": {"blockers_evaluated": len(gate), "blocked": len(blocked),
                        "artifact": "research/freeze/run44_successor_freeze_gate.csv"},
        "blocking_defects": 0,
        "limitation_contract": pred["limitation_contract"],
        "predecessor_references": {
            "v25_release_record": "research/freeze/INSTRUMENT_FINAL_FREEZE_RECORD.json",
            "v26_release_record": "research/freeze/RUN41_SUCCESSOR_FREEZE_RECORD.json",
            "v27_release_record": "research/freeze/RUN42_SUCCESSOR_FREEZE_RECORD.json",
            "v28_release_record": "research/freeze/RUN43_SUCCESSOR_FREEZE_RECORD.json",
            "v28_candidate_identity": "research/freeze/run43_freeze_candidate_identity.json",
            "v28_freeze_gate": "research/freeze/run43_successor_freeze_gate.csv",
            "statement": ("All of these are preserved unchanged. That they still record v25, "
                          "v26, v27 and v28 is asserted by the requalified gates, not assumed."),
        },
        "governed_files_moved_since_v28": moved,
    }
    (FREEZE / "RUN44_SUCCESSOR_FREEZE_RECORD.json").write_text(
        json.dumps(rec, indent=2) + "\n", encoding="utf-8")

    report = f"""# Run-44 successor freeze report

**Disposition: FINAL_FREEZE_ACCEPTED** for `sim-2026.08-v29`.

## Why there is a successor at all

Run 43 accepted a successor freeze of the v28 instrument. Run 43J then diagnosed eleven defects
on a participant render, classified seven of them F (render or presentation defect, storage
correct), one C and three G, and **changed nothing**. The owner ordered four of the F defects
repaired on 2026-08-22.

Every repair is at the render. **Storage was correct in every one of them**, and the record of
what a participant was SHOWN is what the freeze governs, so v28 is **superseded, not amended**.

    v25 accepted freeze -> S1/S2 -> v26 successor -> Run 42 mechanism repair -> v27 successor
    -> owner's retirement ruling -> v28 successor -> Run 43J render diagnosis
    -> owner's repair order -> v29 successor

## The four defects, and what each one showed a participant

| Defect | What it showed | What it shows now |
|---|---|---|
| Severity ranked on capitalisation | a module storing lowercase `green` was selected as its category's "worst" ahead of two properly-cased Green ones, because a key miss fell through to the unknown rank | one shared, case-insensitive rank at every site on the page that orders a status |
| Driver attribution unchecked | an Amber category offered a Green module as the driver of its Amber | a module better than the severity it would drive is not named as driving it, and the panel says why |
| Absent document risk rendered as a value | an absent score is stored present-and-null, and `Number(null)` is 0 and finite, so it rendered `0.00` Green and was carried into the Executive Brief as a key driver | absent renders as absent; a genuine stored zero still renders as zero |
| Computed figures labelled extracted | CPI and SPI carried the extracted mark with no source to show | both are labelled computed, on the panel and in the upload result line |

The fifth change is the Portfolio Health flyout, which told a participant the panel needed at
least three projects when after the Run-43 offload no number of projects makes it compute. It now
states the current state, from a predicate **derived from the taxonomy the page loaded**.

## What did NOT change, proved by execution

| Subject | Result |
|---|---|
| Registered module population | 101, identical |
| `run_module()` over all 101 identifiers, full package | **0 rows differ** against the v28 line |
| `run_module()` over all 101 identifiers, starved package | **0 rows differ** against the v28 line |
| Modules in service, available, retired, voting | identical |
| Merged signal inputs and per-field source record | identical |
| `docRiskScore` on an absent observation | still PRESENT AND NULL |
| Fused category status over the voting pair | identical for every band pair tried |
| Synthetic package | RETAINED `OG-SYNTH-0.6` |
| Analysis schema | RETAINED `og-analysis-2026.08-v1` |

This is not inferred from a source diff. The v28 line is extracted from its own pinned git object
and imported as its own package, both lines are executed on identical inputs, and the comparison
was **proved failable** by perturbing one module's own input and observing that module, and only
that module, diverge. The stamp is normalised out of the row comparison and asserted separately,
so a run that minted no stamp could not pass.

## The one invariant this release deliberately breaks

`assets/js/deepdive.js` is one of the six `SEQUENCE_BEARING_FILES`, and every participant-package
record since v10 asserts those six are byte-identical across a successor. **This release cannot
say that, and says so instead.** The change is the Portfolio Health flyout's reason sentence and
nothing else: no step of the decision sequence, no reveal gate, no lock, no randomization, no
server contract, no append-only record and no user-facing control moved. Its authority is the
owner's order at Run 44 section 4.4. The gate's B04 blocker and the package checks were
reconciled to the true bytes and to a NAMED exception; neither was disabled, weakened or widened,
and a second sequence-bearing file moving is still a failure.

## The scientific position

No input was invented, no fact fabricated, no qualification rule relaxed and no scientific method
changed. Nothing on the analytical side was touched. **Three of Run 43J's eleven defects remain
classified G and are unresolved**, together with three further G questions: every one of them
needs read access to stored rows that this run did not have and did not take.

## Gate

{len(gate)} blocker classes evaluated, {len(blocked)} blocked. Artifact:
`research/freeze/run44_successor_freeze_gate.csv`.

The v25, v26, v27 and v28 release records are preserved unchanged and still record their own
stamps.
"""
    (FREEZE / "RUN44_SUCCESSOR_FREEZE_REPORT.md").write_text(report, encoding="utf-8")

    print("wrote RUN44_SUCCESSOR_FREEZE_CHECKSUMS.csv:", len(rows), "rows")
    print("wrote RUN44_SUCCESSOR_FREEZE_RECORD.json")
    print("wrote RUN44_SUCCESSOR_FREEZE_REPORT.md")
    print("governed files moved since v28:", moved or "(none)")
    print("release content digest:", release_digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
