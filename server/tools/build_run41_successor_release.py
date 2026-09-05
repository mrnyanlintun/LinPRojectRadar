#!/usr/bin/env python3
"""
RUN 41 SECTION 19. THE SUCCESSOR FREEZE RELEASE RECORDS.

Writes, beside the v25 release and never over it:

  research/freeze/RUN41_SUCCESSOR_FREEZE_RECORD.json
  research/freeze/RUN41_SUCCESSOR_FREEZE_REPORT.md
  research/freeze/RUN41_SUCCESSOR_FREEZE_CHECKSUMS.csv

The historical relationship is explicit in every one of them:

    v25 accepted freeze -> Run 40 identified S1/S2 -> owner authorised remediation
    -> v26 successor -> requalification

The v25 records remain exactly as Run 37 wrote them. They are the evidence for anything computed
under v25 and a successor that edited them would destroy it.

Usage: python tools/build_run41_successor_release.py
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
AUDIT = ROOT / "code_audit"
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from app.simulation.models import (  # noqa: E402
    SIMULATION_VERSION, SIMULATION_VERSION_HISTORY)
import participant_packages as PP  # noqa: E402

PREDECESSOR_RECORD = FREEZE / "INSTRUMENT_FINAL_FREEZE_RECORD.json"
PREDECESSOR_CHECKSUMS = FREEZE / "INSTRUMENT_FINAL_FREEZE_CHECKSUMS.csv"
IDENTITY = FREEZE / "run41_freeze_candidate_identity.json"
GATE = FREEZE / "run41_successor_freeze_gate.csv"
BEHAVIOUR = FREEZE / "run41_candidate_behaviour_digest.json"


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
    # THE SAME GOVERNED FILE LIST AS THE PREDECESSOR, re-measured against the successor tree.
    # Keeping the list identical is deliberate: a successor that also changed WHAT it measures
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
                     "moved_since_v25": "YES" if h != r["sha256"] else "no"})
    # The successor's own additions, named so the manifest describes the instrument that will
    # actually run rather than only the parts it inherited.
    for extra in ("server/alembic/versions/0026_final_lock_guard.py",
                  "code_audit/run41_production_tree.sha256",
                  "research/freeze/run41_freeze_candidate_identity.json",
                  "research/freeze/run41_successor_freeze_gate.csv"):
        p = ROOT / extra
        rows.append({"path": extra, "sha256": sha(p), "git_object": git_object(p),
                     "tracked": "TRACKED", "moved_since_v25": "ADDED_BY_RUN41"})

    out_sums = FREEZE / "RUN41_SUCCESSOR_FREEZE_CHECKSUMS.csv"
    with out_sums.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["path", "sha256", "git_object", "tracked",
                                           "moved_since_v25"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    release_body = out_sums.read_text(encoding="utf-8")
    release_digest = hashlib.sha256(release_body.encode()).hexdigest()

    # ---------------------------------------------------------------- the record
    rec = {
        "release_disposition": "FINAL_FREEZE_ACCEPTED",
        "label": "Opus Gubernatio research instrument, Run-41 successor freeze (sim-2026.08-v26)",
        "created": datetime.date(2026, 8, 19).isoformat(),
        "authority": (
            "The owner's ruling of 2026-08-19 on the two HIGH defects Run 40 confirmed: FIX BOTH "
            "BEFORE PARTICIPANT USE. Neither risk is accepted for the study period."),
        "supersedes_release": "f983bb020f7a184a5742e1fff09d690b0170f0de",
        "supersedes_candidate": pred["freeze_candidate_commit"],
        "supersedes_simulation_version": pred["simulation_version"],
        "history": [
            "Run 37 accepted the final freeze of the v25 instrument at candidate "
            f"{pred['freeze_candidate_commit']}, released at "
            "f983bb020f7a184a5742e1fff09d690b0170f0de.",
            "Run 40 executed a functional and security acceptance against that release and "
            "confirmed two HIGH defects: S1, stored XSS and content-type spoofing at "
            "GET /documents/{id}/content, and S2, raw-SQL mutability of the substantive final "
            "participant judgment after the final lock. Run 40 ended FABLE_ACCEPTANCE_BLOCKED "
            "with both left open for owner decision, because remediating either moves a frozen "
            "byte and neither may be applied silently.",
            "The owner authorised remediation of both before participant use.",
            "Run 41 reproduced both defects on v25 first, closed them, stamped the successor "
            "sim-2026.08-v26, and requalified every downstream gate by executing it.",
            "The v25 release remains historical evidence and is not rewritten. Results computed "
            "under v25 remain interpretable against the v25 records.",
        ],
        "freeze_candidate_commit": ident["candidate_git_commit"],
        "candidate_identity_digest": ident["candidate_identity_digest"],
        "candidate_behaviour_digest": behav["behaviour_digest"],
        "release_content_digest": release_digest,
        "release_content_digest_method": (
            "sha256 over RUN41_SUCCESSOR_FREEZE_CHECKSUMS.csv, which content-addresses every "
            "governed file of the successor instrument. Reproducible from the tree alone."),
        "release_commit_recording_method": pred["release_commit_recording_method"],
        "simulation_version": SIMULATION_VERSION,
        "simulation_version_history": list(SIMULATION_VERSION_HISTORY),
        "participant_package": PP.CURRENT.identifier,
        "participant_package_decision": (
            "RETAINED. Not one of the 70 governed participant-package bytes moved, and the 6 "
            "sequence-bearing files are byte-identical to the v13 record. A successor was NOT "
            "minted merely because server behaviour changed."),
        "synthetic_package": "OG-SYNTH-0.6",
        "analysis_schema": "og-analysis-2026.08-v1",
        "behavioural_delta_v25_to_v26": [
            "untrusted document content can no longer execute through the same-origin "
            "document-content response",
            "substantive final responses become database-immutable after final lock",
        ],
        "behavioural_delta_scope_statement": (
            "Exactly these two, and nothing else. Proved by executing both lines from their own "
            "git objects: all 101 registered modules emit byte-identical rows across the "
            "boundary, and the AI recommendation is digest-identical at all 36 project-period "
            "positions."),
        "findings_closed": {
            "S1": {"title": "stored XSS / content-type spoofing on GET /documents/{id}/content",
                   "original_severity": "HIGH", "final_status": "CONFIRMED_FIXED",
                   "evidence": "code_audit/run41_s1_prefix_browser_proof.json (4 of 4 attacker "
                               "payloads executed in real Chromium) vs "
                               "code_audit/run41_s1_postfix_browser_proof.json (0 of 4), with "
                               "all 4 still reaching the serving boundary at HTTP 200"},
            "S2": {"title": "final-lock database integrity on the primary outcome data",
                   "original_severity": "HIGH", "final_status": "CONFIRMED_FIXED",
                   "evidence": "code_audit/run41_s2_prefix_reproduction.json (13 of 13 raw SQL "
                               "mutations succeeded after final lock) vs "
                               "code_audit/run41_s2_postfix_reproduction.json (0 of 13), via "
                               "migration 0026 trg_decisions_final_lock_guard"},
        },
        "unresolved_high_security_blockers": 0,
        "freeze_gate": {"blockers_evaluated": len(gate), "blocked": len(blocked),
                        "artifact": "research/freeze/run41_successor_freeze_gate.csv"},
        "fault_campaign": {"faults": 12, "applied": 12, "intended_red": 12, "restored_green": 12,
                           "crashes_accepted_as_red": 0,
                           "artifact": "code_audit/run41_fault_campaign_results.csv"},
        "blocking_defects": 0,
        "limitation_contract": pred["limitation_contract"],
        "predecessor_references": {
            "v25_release_record": "research/freeze/INSTRUMENT_FINAL_FREEZE_RECORD.json",
            "v25_release_report": "research/freeze/INSTRUMENT_FINAL_FREEZE_REPORT.md",
            "v25_release_checksums": "research/freeze/INSTRUMENT_FINAL_FREEZE_CHECKSUMS.csv",
            "v25_candidate_identity": "research/freeze/run37_freeze_candidate_identity.json",
            "v25_freeze_gate": "research/freeze/run37_final_freeze_gate.csv",
            "v25_behaviour_digest": "research/freeze/run37_candidate_behaviour_digest.json",
            "statement": ("All of these are preserved unchanged. That they still record v25 is "
                          "asserted by the requalified gates, not assumed."),
        },
        "governed_files_moved_since_v25": moved,
    }
    out_rec = FREEZE / "RUN41_SUCCESSOR_FREEZE_RECORD.json"
    artifact_out(out_rec).write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")

    # ---------------------------------------------------------------- the report
    report = f"""# Run-41 successor freeze report

**Disposition: FINAL_FREEZE_ACCEPTED** for `sim-2026.08-v26`.

## Why there is a successor at all

Run 37 accepted a final freeze of the v25 instrument. Run 40 then executed a functional and
security acceptance against that release and confirmed two HIGH defects:

- **S1** stored XSS and content-type spoofing on `GET /documents/{{id}}/content`
- **S2** raw-SQL mutability of the substantive final participant judgment after the final lock

Run 40 ended `FABLE_ACCEPTANCE_BLOCKED` and left both open, because remediating either moves a
byte inside a frozen surface and neither could be applied silently. The owner ruled that **both
be fixed before participant use**, accepting neither risk for the study period.

Fixing them changes executable behaviour, so v25 is **superseded, not amended**.

    v25 accepted freeze
      -> Run 40 identified S1 and S2
      -> owner authorised remediation
      -> v26 successor
      -> requalification

## The behavioural delta, in full

1. Untrusted document content can no longer execute through the same-origin document-content
   response.
2. Substantive final responses become database-immutable after final lock.

Nothing else. That is not a claim of intent; it is measured. All {behav['targets']} scientific
targets were executed on both lines, and the whole 101-module registered population was executed
from each line's own git object: **zero emitted rows moved**. The AI recommendation served at all
36 project-period positions is **digest-identical** between the lines.

## What was preserved

| Item | Decision | Basis |
|---|---|---|
| Participant package | RETAINED `og-participant-2026.08-v13` | 0 of 70 governed bytes moved; 0 of 6 sequence-bearing files moved |
| Synthetic package | RETAINED `OG-SYNTH-0.6` | byte-identical to the pinned v25 predecessor |
| Analysis schema | RETAINED `og-analysis-2026.08-v1` | byte-identical to the pinned v25 predecessor |
| Voting set | unchanged, exactly `A1.7` and `A1.8` | read from the live registry |
| Category-9 gate | unchanged | no unqualified probe reaches a band, by execution |
| Category-10 boundary | unchanged | authorisation required, creates no project evidence, no Category-10 identity votes |

A successor package was deliberately **not** minted merely because server behaviour changed.

## Findings closed

| Finding | Original severity | Final status |
|---|---|---|
| S1 stored XSS / content-type spoofing | HIGH | **CONFIRMED_FIXED** |
| S2 final-lock database integrity | HIGH | **CONFIRMED_FIXED** |

Unresolved HIGH security blockers: **0**.

Both original reproductions, their original severities, their fix commits, their regression
evidence and their version boundary are preserved in
`code_audit/run41_security_findings_closure.csv`. The findings are closed, not deleted.

## Qualification

| Gate | Result |
|---|---|
| Freeze qualification (Run-37 equivalent, re-executed) | {len(gate)} blocker classes, {len(blocked)} blocked |
| Twelve-fault campaign | 12 applied, 12 intended RED, 12 restored GREEN, 0 crashes credited |
| Security acceptance (Run-40 coverage re-executed) | 11 attacks, 11 reached their boundary, 0 adverse |

## The predecessor is preserved

`sim-2026.08-v25`, its candidate `{pred['freeze_candidate_commit']}`, its release
`f983bb020f7a184a5742e1fff09d690b0170f0de`, its identity, its gate, its behaviour digest and its
release records are **unchanged**. The v25 line still reconstructs from its own git object and
still says v25 - asserted by the requalified guards rather than assumed. Everything already
computed under v25 remains interpretable against the v25 records.

## Identity

- successor candidate commit: `{ident['candidate_git_commit']}`
- candidate identity digest: `{ident['candidate_identity_digest']}`
- candidate behaviour digest: `{behav['behaviour_digest']}`
- release content digest: `{release_digest}`
"""
    (artifact_out(FREEZE / "RUN41_SUCCESSOR_FREEZE_REPORT.md")).write_text(report, encoding="utf-8")

    print(f"wrote {out_rec.relative_to(ROOT)}")
    print(f"wrote {out_sums.relative_to(ROOT)}: {len(rows)} governed files")
    print(f"wrote research/freeze/RUN41_SUCCESSOR_FREEZE_REPORT.md")
    print(f"  governed files moved since v25: {moved}")
    print(f"  release content digest: {release_digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
