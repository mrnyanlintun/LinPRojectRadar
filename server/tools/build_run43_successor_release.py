#!/usr/bin/env python3
"""
RUN 43. THE SUCCESSOR FREEZE RELEASE RECORDS.

Writes, beside the v25 and v26 releases and never over either:

  research/freeze/RUN43_SUCCESSOR_FREEZE_RECORD.json
  research/freeze/RUN43_SUCCESSOR_FREEZE_REPORT.md
  research/freeze/RUN43_SUCCESSOR_FREEZE_CHECKSUMS.csv

The historical relationship is explicit in every one of them:

    v25 accepted freeze -> Run 40 identified S1/S2 -> owner authorised remediation
    -> v26 successor -> Run 42 proved two identity losses in the period-binding and
    evidence-lineage mechanism -> v27 successor -> requalification

The v25 and v26 records remain exactly as Runs 37 and 41 wrote them. They are the evidence for
anything computed under those stamps and a successor that edited them would destroy it.

Usage: python tools/build_run43_successor_release.py
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

PREDECESSOR_RECORD = FREEZE / "RUN42_SUCCESSOR_FREEZE_RECORD.json"
PREDECESSOR_CHECKSUMS = FREEZE / "RUN42_SUCCESSOR_FREEZE_CHECKSUMS.csv"
IDENTITY = FREEZE / "run43_freeze_candidate_identity.json"
GATE = FREEZE / "run43_successor_freeze_gate.csv"
BEHAVIOUR = FREEZE / "run43_candidate_behaviour_digest.json"


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
                     "moved_since_v27": "YES" if h != r["sha256"] else "no"})
    for extra in ("code_audit/run43_production_tree.sha256",
                  "code_audit/run43_participant_package_v14_checksums.sha256",
                  "research/freeze/run43_freeze_candidate_identity.json",
                  "research/freeze/run43_successor_freeze_gate.csv",
                  "server/tools/run43_production_changes.py"):
        p = ROOT / extra
        rows.append({"path": extra, "sha256": sha(p), "git_object": git_object(p),
                     "tracked": "TRACKED", "moved_since_v27": "ADDED_BY_RUN43"})

    out_sums = FREEZE / "RUN43_SUCCESSOR_FREEZE_CHECKSUMS.csv"
    with out_sums.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["path", "sha256", "git_object", "tracked",
                                           "moved_since_v27"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    release_digest = hashlib.sha256(out_sums.read_text(encoding="utf-8").encode()).hexdigest()

    rec = {
        "release_disposition": "FINAL_FREEZE_ACCEPTED",
        "label": "Opus Gubernatio research instrument, Run-43 successor freeze (sim-2026.08-v28)",
        "created": datetime.date(2026, 8, 21).isoformat(),
        "authority": (
            "The owner's ruling of 2026-08-21, Run 43: 38 of the 101 registered modules are "
            "RETIRED FROM SERVICE. Retirement is a statement about the taxonomy and the "
            "explanation burden, not a claim that any arithmetic is wrong."),
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
            "of 2026-08-21, and stamped the successor sim-2026.08-v28. Retirement removes a "
            "module from service, not from the registry: every retired module keeps its registry "
            "entry, its formula function and its audit lineage, and run_module() on all 101 "
            "identifiers returns output byte-identical to v27.",
            "The v25, v26 and v27 releases remain historical evidence and are not rewritten. "
            "Results computed under any of them remain interpretable against their own records.",
        ],
        "freeze_candidate_commit": ident["candidate_git_commit"],
        "candidate_identity_digest": ident["candidate_identity_digest"],
        "candidate_behaviour_digest": behav["behaviour_digest"],
        "release_content_digest": release_digest,
        "release_content_digest_method": (
            "sha256 over RUN43_SUCCESSOR_FREEZE_CHECKSUMS.csv, which content-addresses every "
            "governed file of the successor instrument. Reproducible from the tree alone."),
        "release_commit_recording_method": pred["release_commit_recording_method"],
        "simulation_version": SIMULATION_VERSION,
        "simulation_version_history": list(SIMULATION_VERSION_HISTORY),
        "participant_package": PP.CURRENT.identifier,
        "participant_package_decision": (
            "SUPERSEDED at og-participant-2026.08-v14. Determined mechanically, not assumed: "
            "five of the 70 governed participant-package bytes moved -- the two generated client "
            "taxonomy mirrors, detail.js, knowledge.js and index.html -- and the 6 "
            "sequence-bearing files are byte-identical to the v13 record. The v13 record is "
            "pinned to the commit whose blobs it describes and is NOT regenerated."),
        "synthetic_package": "OG-SYNTH-0.6",
        "analysis_schema": "og-analysis-2026.08-v1",
        "behavioural_delta_v27_to_v28": [
            "38 of the 101 registered modules are retired from service, so no production path "
            "enumerates them: they reach no ledger row, no abstention list, no participant "
            "surface, no export row and no browser taxonomy entry",
            "Group D falls to zero in service, so live_portfolio_modules() returns () and the "
            "Portfolio Health dispatcher produces a retired snapshot instead of five readings",
            "the counts a participant reads now state three populations -- 101 registered, 63 in "
            "service, 62 computed -- where they stated two",
        ],
        "behavioural_delta_scope_statement": (
            "Exactly these, and nothing else. Proved by EXECUTING rather than by reading a diff: "
            "run_module() over all 101 registered identifiers against a worktree at the v27 "
            "commit produces 0 diff lines, and that comparison was proved failable by "
            "re-injecting a short-circuit at 1,530 diff lines and restoring to 0. No module in "
            "service changed its computed result. Voting is still exactly A1.7 and A1.8, Group C "
            "still does not contribute to project status, and Portfolio Health never did."),
        "defects_closed": {},
        "scientific_state_unchanged": (
            "NO input was invented, NO fact fabricated, NO qualification rule relaxed and NO "
            "scientific method changed. The formulas of the 38 retired modules are KEPT, because "
            "retiring a module is a statement about the taxonomy and not a claim that its "
            "arithmetic is wrong, and their audit lineage remains readable. canonical_v8, the "
            "Portfolio Health computation, is untouched and its supplied Run-33 oracles are "
            "still executed against it directly. The modules in service that abstain for want of "
            "their governed structure still abstain, with the same reasons and the same codes."),
        "unresolved_high_security_blockers": 0,
        "freeze_gate": {"blockers_evaluated": len(gate), "blocked": len(blocked),
                        "artifact": "research/freeze/run43_successor_freeze_gate.csv"},
        "blocking_defects": 0,
        "limitation_contract": pred["limitation_contract"],
        "predecessor_references": {
            "v25_release_record": "research/freeze/INSTRUMENT_FINAL_FREEZE_RECORD.json",
            "v26_release_record": "research/freeze/RUN41_SUCCESSOR_FREEZE_RECORD.json",
            "v27_release_record": "research/freeze/RUN42_SUCCESSOR_FREEZE_RECORD.json",
            "v27_candidate_identity": "research/freeze/run42_freeze_candidate_identity.json",
            "v27_freeze_gate": "research/freeze/run42_successor_freeze_gate.csv",
            "statement": ("All of these are preserved unchanged. That they still record v25, "
                          "v26 and v27 is asserted by the requalified gates, not assumed."),
        },
        "governed_files_moved_since_v27": moved,
    }
    (FREEZE / "RUN43_SUCCESSOR_FREEZE_RECORD.json").write_text(
        json.dumps(rec, indent=2) + "\n", encoding="utf-8")

    report = f"""# Run-43 successor freeze report

**Disposition: FINAL_FREEZE_ACCEPTED** for `sim-2026.08-v28`.

## Why there is a successor at all

Run 42 accepted a successor freeze of the v27 instrument. The owner then ruled, on 2026-08-21,
that **38 of the 101 registered modules are retired from service**.

Retirement is a statement about the taxonomy and the explanation burden. It is **not** a claim
that any module's arithmetic is wrong, and nothing is deleted: every retired module keeps its
registry entry, its formula function and its audit lineage, and asking `run_module()` for one by
name still resolves and still returns exactly what it returned under v27. What changes is which
modules the production paths **enumerate**, and therefore which reach a participant.

The single authority for which modules are in service is the `notes` column of
`p0-baseline/module_renumbering_map.csv`. **No list of retired identifiers is written anywhere
else in the tree**, so reinstating a module there restores it to service with no other edit.

Which modules a participant sees is executable behaviour, so v27 is **superseded, not amended**.

    v25 accepted freeze -> S1/S2 -> v26 successor -> Run 42 mechanism repair -> v27 successor
    -> owner's retirement ruling -> v28 successor

## The populations after the retirement

| Population | Count | Derived from |
|---|---|---|
| Registered in the registry | 101 | `registry.registry_index()` |
| Retired from service | 38 | the `notes` column of the registry map |
| In service | 63 | `registry.service_index()` |
| Computed by the analytical server | 62 | `registry.available_modules()` |
| Group D (Portfolio Health) in service | 0 | `portfolio_health.live_portfolio_modules()` |

## What did NOT change, proved by execution

| Subject | Result |
|---|---|
| Registered module population | 101, identical |
| `run_module()` over all 101 identifiers | **0 diff lines** against a worktree at v27 |
| Modules in service whose computed result moved | **0** |
| Voting set | `A1.7`, `A1.8`, unchanged |
| Group C contributes to project status | No, unchanged |
| Portfolio Health contributes to project status | No -- it never did |
| `canonical_v8`, the Portfolio Health computation | untouched, and its oracles still execute |
| Synthetic package | RETAINED `OG-SYNTH-0.6` |
| Analysis schema | RETAINED `og-analysis-2026.08-v1` |

This is not inferred from a source diff. The comparison was **proved failable**: re-injecting a
retirement short-circuit into `run_module()` produced 1,530 diff lines, and removing it returned
the diff to 0.

## The scientific position

No input was invented, no fact fabricated, no qualification rule relaxed and no scientific method
changed. The 38 retired formulas are kept as the research record. The modules in service that
abstain for want of their governed structure still abstain, with the same reasons and the same
stable codes. `revision_resolution_status` remains NOT_ESTIMABLE by the deliberate fail-closed
decision Run 42 reported, and Run 43 did not overturn it either.

## Gate

{len(gate)} blocker classes evaluated, {len(blocked)} blocked. Artifact:
`research/freeze/run43_successor_freeze_gate.csv`.

The v25, v26 and v27 release records are preserved unchanged and still record their own stamps.
"""
    (FREEZE / "RUN43_SUCCESSOR_FREEZE_REPORT.md").write_text(report, encoding="utf-8")

    print("wrote RUN43_SUCCESSOR_FREEZE_CHECKSUMS.csv:", len(rows), "rows")
    print("wrote RUN43_SUCCESSOR_FREEZE_RECORD.json")
    print("wrote RUN43_SUCCESSOR_FREEZE_REPORT.md")
    print("governed files moved since v26:", moved or "(none)")
    print("release content digest:", release_digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
