#!/usr/bin/env python3
"""
RUN 45. THE SUCCESSOR FREEZE RELEASE RECORDS.

Writes, beside the v25 and v26 releases and never over either:

  research/freeze/RUN45_SUCCESSOR_FREEZE_RECORD.json
  research/freeze/RUN45_SUCCESSOR_FREEZE_REPORT.md
  research/freeze/RUN45_SUCCESSOR_FREEZE_CHECKSUMS.csv

The historical relationship is explicit in every one of them:

    v25 accepted freeze -> Run 40 identified S1/S2 -> owner authorised remediation
    -> v26 successor -> Run 42 proved two identity losses -> v27 successor
    -> owner's retirement ruling -> v28 successor -> Run 43J diagnosed eleven render defects
    -> owner ordered four of them repaired -> v29 successor -> Run 44 measured the period-scoping
    fall-through -> owner signed off the canonical field classification -> v30 successor

The v25, v26, v27, v28 and v29 records remain exactly as Runs 37, 41, 42, 43 and 44 wrote them. They are
the evidence for anything computed under those stamps and a successor that edited them would
destroy it.

Usage: python tools/build_run45_successor_release.py
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

PREDECESSOR_RECORD = FREEZE / "RUN44_SUCCESSOR_FREEZE_RECORD.json"
PREDECESSOR_CHECKSUMS = FREEZE / "RUN44_SUCCESSOR_FREEZE_CHECKSUMS.csv"
IDENTITY = FREEZE / "run45_freeze_candidate_identity.json"
GATE = FREEZE / "run45_successor_freeze_gate.csv"
BEHAVIOUR = FREEZE / "run45_candidate_behaviour_digest.json"


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
                     "moved_since_v29": "YES" if h != r["sha256"] else "no"})
    for extra in ("code_audit/run45_production_tree.sha256",
                  "code_audit/run45_field_classification_proposal.md",
                  "code_audit/run45_census_before.csv",
                  "code_audit/run45_census_after.csv",
                  "research/freeze/run45_freeze_candidate_identity.json",
                  "research/freeze/run45_successor_freeze_gate.csv",
                  "server/tools/build_run45_census.py",
                  "server/tools/test_run45_period_scoping.py"):
        p = ROOT / extra
        rows.append({"path": extra, "sha256": sha(p), "git_object": git_object(p),
                     "tracked": "TRACKED", "moved_since_v29": "ADDED_BY_RUN45"})

    out_sums = FREEZE / "RUN45_SUCCESSOR_FREEZE_CHECKSUMS.csv"
    with out_sums.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["path", "sha256", "git_object", "tracked",
                                           "moved_since_v29"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    release_digest = hashlib.sha256(out_sums.read_text(encoding="utf-8").encode()).hexdigest()

    rec = {
        "release_disposition": "FINAL_FREEZE_ACCEPTED",
        "label": "Opus Gubernatio research instrument, Run-45 successor freeze (sim-2026.08-v30)",
        "created": datetime.date(2026, 8, 22).isoformat(),
        "authority": (
            "The owner's ruling of 2026-08-22 on the Run 45 section 5.1 classification proposal. "
            "The classification is canonical, decided once and signed off before any code "
            "changed: 13 IDENTITY fields, 62 PERIOD fields, 2 UNDETERMINED. The owner further "
            "ruled the contingency pair SPLIT -- originalContingency identity, "
            "remainingContingency period -- changeOrderCount PERIOD as today with the event-"
            "accumulation gap recorded as a known limitation, and the float pair UNDETERMINED "
            "with its contradiction recorded rather than resolved."),
        "supersedes_candidate": pred["freeze_candidate_commit"],
        "supersedes_simulation_version": pred["simulation_version"],
        "history": [
            "Run 37 accepted the final freeze of the v25 instrument.",
            "Run 40 confirmed two HIGH defects; the owner authorised remediation; Run 41 closed "
            "them and stamped the successor sim-2026.08-v26.",
            "Run 42 traced the background data-processing mechanism end to end, proved two "
            "identity losses in it, repaired both, and PROVED PERIOD BINDING CORRECT: values "
            "bind to their own period and upload order does not matter. That proof is preserved "
            "and re-run under the new retrieval by Run 45.",
            "Run 43 retired 38 of the 101 registered modules FROM SERVICE on the owner's ruling "
            "of 2026-08-21, and stamped the successor sim-2026.08-v28.",
            "Run 44 repaired four participant-facing render defects and stamped sim-2026.08-v29; "
            "it also MEASURED, and reported without acting, that retrieval scoped every field to "
            "the period its document was uploaded into, that bac fell through to 4,463,290 where "
            "the contract said 5,874,620, and that baselineContractSum inverted its own declared "
            "precedence.",
            "Run 45 proposed the canonical classification and STOPPED for sign-off; on the "
            "owner's ruling it implemented retrieval by kind and stamped sim-2026.08-v30.",
            "The v25, v26, v27, v28 and v29 releases remain historical evidence and are not "
            "rewritten. Results computed under any of them remain interpretable against their "
            "own records.",
        ],
        "freeze_candidate_commit": ident["candidate_git_commit"],
        "candidate_identity_digest": ident["candidate_identity_digest"],
        "candidate_behaviour_digest": behav["behaviour_digest"],
        "release_content_digest": release_digest,
        "release_content_digest_method": (
            "sha256 over RUN45_SUCCESSOR_FREEZE_CHECKSUMS.csv, which content-addresses every "
            "governed file of the successor instrument. Reproducible from the tree alone."),
        "release_commit_recording_method": pred["release_commit_recording_method"],
        "simulation_version": SIMULATION_VERSION,
        "simulation_version_history": list(SIMULATION_VERSION_HISTORY),
        "participant_package": PP.CURRENT.identifier,
        "participant_package_decision": (
            "RETAINED at og-participant-2026.08-v15. Determined mechanically, not assumed: NONE "
            "of the 70 governed participant-package bytes moved, and none of the six sequence-"
            "bearing files moved. Run 45 changes what the server RETRIEVES, not what the client "
            "renders: no step of the decision sequence, no reveal gate, no lock, no "
            "randomization and NO USER-FACING CONTROL was added, moved or removed."),
        "synthetic_package": "OG-SYNTH-0.6",
        "analysis_schema": "og-analysis-2026.08-v1",
        "canonical_field_classification": {
            "identity": 13, "period": 62, "undetermined": 2, "total_emittable": 77,
            "authority": "code_audit/run45_field_classification_proposal.md, and the owner's "
                         "ruling recorded in REPORT_2026-08-22_run45_period_scoping_fix.md",
            "declared_in": "server/app/field_registry.py IDENTITY_FIELDS / PERIOD_FIELDS / "
                           "UNDETERMINED_FIELDS, asserted at import to partition FIELD_KINDS",
        },
        "behavioural_delta_v29_to_v30": [
            "an IDENTITY field uploaded at period 1 is retrieved at periods 2, 3 and 4; it was "
            "invisible outside its own period before",
            "declared document-type precedence holds ACROSS periods, so the contract at period 1 "
            "beats a change order at period 2 for baselineContractSum: Run 44's measured 6,100,000 "
            "inversion now returns the contract's own 5,874,620",
            "a PERIOD field still never carries forward: absent in its period is absent, even "
            "where an earlier period reported one",
            "A3.2 Contingency Burn Rate computes in periods that restate only the remaining "
            "contingency, because the original is now carried; it still abstains where the "
            "PERIOD half is absent",
        ],
        "behavioural_delta_scope_statement": (
            "Exactly these four, and every one of them is in RETRIEVAL. No formula, band, "
            "threshold, calibration, abstention rule or population moved: voting is still "
            "exactly A1.7 and A1.8, 63 modules in service of 101 registered, Group C still does "
            "not contribute to project status, Portfolio Health is still in service nowhere. "
            "The census over the repository fixtures moves exactly three modules, all "
            "attributable to an identity field newly visible in a period -- A1.7 and A1.8 to "
            "bac, A3.2 to originalContingency -- and the two control corpora, one single-period "
            "and one four-monthly-report, are byte-identical before and after, which is the "
            "control on the claim that period-field retrieval did not change. Run 42's "
            "upload-order equivalence was re-run under the new retrieval and holds for both "
            "kinds."),
        "defects_closed": {
            "period_scoping_fall_through": (
                "An identity field was retrieved only in the period its document was uploaded "
                "into, so bac fell through to a pay application's weaker restatement from "
                "period 2 onward. Closed."),
            "baseline_contract_sum_precedence_inversion": (
                "field_registry.py:185 declares the contract's own figure beats a change "
                "order's account of it; with the contract invisible the change order won by "
                "default. Closed: precedence now holds across the carry-forward."),
        },
        "known_limitation_event_accumulation": (
            "changeOrderCount is declared EVENT, and an event population ACCUMULATES: nothing "
            "supersedes it, and earlier periods' executed change orders have not stopped "
            "existing, so it is strictly neither identity nor period. The correct retrieval "
            "would be a third rule -- a union at or before the period with latest-per-entity -- "
            "and the owner ruled at 1.3 that the rule is NOT to be defined and section 4 is NOT "
            "to be widened. It stays PERIOD, as today. Recorded so a later session finds it "
            "rather than rediscovering it."),
        "recorded_contradiction_float_pair": (
            "totalFloat and consumedFloat stay UNDETERMINED by the owner's ruling 1.4. "
            "field_registry.py:56 groups both as progress snapshots, while :202 says "
            "schedule_update REVISES WHAT time_phased_schedule ESTABLISHED, which is the same "
            "grammar baselineEnd was classified identity on. No module in service consumes "
            "either value, so the ambiguity costs nothing today. They are retrieved as period "
            "fields, which is the unchanged behaviour."),
        "scientific_state_unchanged": (
            "NO input was invented, NO fact fabricated, NO qualification rule relaxed and NO "
            "scientific method changed. A module that abstains for want of its governed "
            "structure still abstains, with the same reason and the same code. What changed is "
            "WHICH PERIODS' observations are eligible for a field, decided from the field's own "
            "declared meaning and signed off by the owner before any code was written -- never "
            "from what would make a module compute. The one module that newly computes, A3.2, "
            "computes because the original contingency it always required is now retrievable, "
            "and its figures were hand-computed from the stated formula and checked against it "
            "rather than read back from it."),
        "unresolved_high_security_blockers": 0,
        "freeze_gate": {"blockers_evaluated": len(gate), "blocked": len(blocked),
                        "artifact": "research/freeze/run45_successor_freeze_gate.csv"},
        "blocking_defects": 0,
        "limitation_contract": pred["limitation_contract"],
        "predecessor_references": {
            "v25_release_record": "research/freeze/INSTRUMENT_FINAL_FREEZE_RECORD.json",
            "v26_release_record": "research/freeze/RUN41_SUCCESSOR_FREEZE_RECORD.json",
            "v27_release_record": "research/freeze/RUN42_SUCCESSOR_FREEZE_RECORD.json",
            "v28_release_record": "research/freeze/RUN43_SUCCESSOR_FREEZE_RECORD.json",
            "v29_release_record": "research/freeze/RUN44_SUCCESSOR_FREEZE_RECORD.json",
            "v29_candidate_identity": "research/freeze/run44_freeze_candidate_identity.json",
            "v29_freeze_gate": "research/freeze/run44_successor_freeze_gate.csv",
            "statement": ("All of these are preserved unchanged. That they still record v25, "
                          "v26, v27, v28 and v29 is asserted by the requalified gates, not "
                          "assumed."),
        },
        "governed_files_moved_since_v29": moved,
    }
    (FREEZE / "RUN45_SUCCESSOR_FREEZE_RECORD.json").write_text(
        json.dumps(rec, indent=2) + "\n", encoding="utf-8")

    report = f"""# Run-45 successor freeze report

**Disposition: FINAL_FREEZE_ACCEPTED** for `sim-2026.08-v30`.

## Why there is a successor at all

Run 44 accepted a successor freeze of the v29 instrument and, separately and without acting,
MEASURED a defect in retrieval: every observation was scoped to the period its document was
uploaded into. A contract uploaded at period 1 was invisible from period 2 on, `bac` fell through
to a pay application's weaker restatement -- **4,463,290 where the contract said 5,874,620** --
and `baselineContractSum` **inverted its own declared precedence**, a change order's account of
the original beating the contract that established it.

What a module is GIVEN is executable behaviour, so v29 is **superseded, not amended**.

    v25 accepted freeze -> S1/S2 -> v26 successor -> Run 42 mechanism repair -> v27 successor
    -> owner's retirement ruling -> v28 successor -> Run 43J render diagnosis
    -> owner's repair order -> v29 successor -> Run 44's period-scoping measurement
    -> owner's classification ruling -> v30 successor

## The classification is canonical and was signed off BEFORE any code changed

Run 45 stopped at its section 5.1, proposed the classification with the declaration each kind was
read off quoted per field, and reported five fields as UNDETERMINED rather than resolving them.
The owner ruled. Only then did retrieval change.

| kind | count | retrieval |
|---|---|---|
| IDENTITY | 13 | the latest value **at or before** the period being computed, declared document-type precedence holding **across** the carry-forward |
| PERIOD | 62 | the period's own documents and nothing else - **byte-identical to v29** |
| UNDETERMINED | 2 | retrieved as period fields, which is the unchanged behaviour; the contradiction is recorded, not resolved |
| **total emittable** | **77** | every field in `FIELD_KINDS`, asserted at import to partition exactly |

## What changed, and what did not

| Subject | Result |
|---|---|
| An identity field uploaded at period 1, read at periods 2-4 | now **retrieved**; previously absent |
| `baselineContractSum` with a contract at period 1 and a change order at period 2 | **5,874,620**, the contract's own figure; the 6,100,000 inversion is dead |
| A period field absent in its period | still **absent**; no carry-forward |
| Upload order, chronological vs reversed, both kinds | **identical** derived state - Run 42's proof re-run under the new retrieval |
| Cross-project leakage | none |
| Registered / in service / computed / voting | 101 / 63 / 62 / exactly A1.7 and A1.8, all identical |
| Modules moving on the fixtures | exactly **three**: A1.7, A1.8 (`bac` newly visible) and A3.2 (`originalContingency` newly visible) |
| The two control corpora | **byte-identical before and after** |
| Sequence-bearing participant files | **none moved** |
| User-facing controls | **none added, moved or removed** |
| Synthetic package | RETAINED `OG-SYNTH-0.6` |
| Analysis schema | RETAINED `og-analysis-2026.08-v1` |

The census is not inferred from a diff: it drives the real routes -- upload, extract, compute,
read back -- on this tree and on the predecessor, and compares the two CSVs row by row.

## Two things recorded so a later session does not rediscover them

1. **`changeOrderCount` is strictly neither kind.** It is declared EVENT, and an event population
   accumulates: nothing supersedes it, and earlier periods' executed change orders have not
   stopped existing. The correct retrieval would be a third rule, a union at or before the period
   with latest-per-entity. The owner ruled at 1.3 that the rule is not to be defined and section 4
   is not to be widened. It stays PERIOD, as today.
2. **`totalFloat` and `consumedFloat` remain UNDETERMINED.** `field_registry.py:56` calls both a
   progress snapshot; `:202` says `schedule_update` revises what `time_phased_schedule`
   ESTABLISHED, which is the grammar `baselineEnd` was classified identity on. No module in
   service consumes either value, so the ambiguity costs nothing today.

## The scientific position

No input was invented, no fact fabricated, no qualification rule relaxed and no scientific method
changed. A module that abstains for want of its governed structure still abstains, with the same
reason and the same code. Every kind was read off a DECLARATION quoted with file and line, never
off what the implementation happened to do and never off what would make a module compute.

## Gate

{len(gate)} blocker classes evaluated, {len(blocked)} blocked. Artifact:
`research/freeze/run45_successor_freeze_gate.csv`.

The v25, v26, v27, v28 and v29 release records are preserved unchanged and still record their own
stamps.
"""
    (FREEZE / "RUN45_SUCCESSOR_FREEZE_REPORT.md").write_text(report, encoding="utf-8")

    print("wrote RUN45_SUCCESSOR_FREEZE_CHECKSUMS.csv:", len(rows), "rows")
    print("wrote RUN45_SUCCESSOR_FREEZE_RECORD.json")
    print("wrote RUN45_SUCCESSOR_FREEZE_REPORT.md")
    print("governed files moved since v29:", moved or "(none)")
    print("release content digest:", release_digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
