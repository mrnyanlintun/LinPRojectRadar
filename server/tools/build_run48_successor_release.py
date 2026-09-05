#!/usr/bin/env python3
"""
RUN 48. THE SUCCESSOR FREEZE RELEASE RECORDS.

Writes, beside the v25 and v26 releases and never over either:

  research/freeze/RUN48_SUCCESSOR_FREEZE_RECORD.json
  research/freeze/RUN48_SUCCESSOR_FREEZE_REPORT.md
  research/freeze/RUN48_SUCCESSOR_FREEZE_CHECKSUMS.csv

The historical relationship is explicit in every one of them:

    v25 accepted freeze -> Run 40 identified S1/S2 -> owner authorised remediation
    -> v26 successor -> Run 42 proved two identity losses -> v27 successor
    -> owner's retirement ruling -> v28 successor -> Run 43J diagnosed eleven render defects
    -> owner ordered four of them repaired -> v29 successor -> Run 44 measured the period-scoping
    fall-through -> owner signed off the canonical field classification -> v30 successor

The v25, v26, v27, v28 and v29 records remain exactly as Runs 37, 41, 42, 43 and 44 wrote them. They are
the evidence for anything computed under those stamps and a successor that edited them would
destroy it.

Usage: python tools/build_run48_successor_release.py
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

PREDECESSOR_RECORD = FREEZE / "RUN47_SUCCESSOR_FREEZE_RECORD.json"
PREDECESSOR_CHECKSUMS = FREEZE / "RUN47_SUCCESSOR_FREEZE_CHECKSUMS.csv"
IDENTITY = FREEZE / "run48_freeze_candidate_identity.json"
GATE = FREEZE / "run48_successor_freeze_gate.csv"
BEHAVIOUR = FREEZE / "run48_candidate_behaviour_digest.json"


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
                     "moved_since_v31": "YES" if h != r["sha256"] else "no"})
    for extra in ("research/freeze/run48_freeze_candidate_identity.json",
                  "research/freeze/run48_successor_freeze_gate.csv",
                  "server/tools/test_run48_current_period.py",
                  "server/tools/drive_run48_browser.py"):
        p = ROOT / extra
        rows.append({"path": extra, "sha256": sha(p), "git_object": git_object(p),
                     "tracked": "TRACKED", "moved_since_v31": "ADDED_BY_RUN48"})

    out_sums = FREEZE / "RUN48_SUCCESSOR_FREEZE_CHECKSUMS.csv"
    with out_sums.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["path", "sha256", "git_object", "tracked",
                                           "moved_since_v31"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    release_digest = hashlib.sha256(out_sums.read_text(encoding="utf-8").encode()).hexdigest()

    rec = {
        "release_disposition": "FINAL_FREEZE_ACCEPTED",
        "label": "Opus Gubernatio research instrument, Run-48 successor freeze (sim-2026.08-v32)",
        "created": datetime.date(2026, 8, 22).isoformat(),
        "authority": (
            "The owner's three rulings of 2026-08-22 in the Run 48 order, section 2. 1. THE "
            "DETAIL PAGE SHOWS THE LATEST PERIOD THAT HAS DOCUMENTS AND HAS BEEN COMPUTED FROM "
            "THEM: not period 1, and not the latest period with documents alone. The upload "
            "design is unchanged and this concerns the READ side only. 2. THE LIVE NAMING "
            "INSTANCES ARE CORRECTED, because modules have been retired and the labels carried a "
            "retired numbering scheme; a sequence-bearing file is edited whenever an ordered fix "
            "requires it, each edit carrying its own named exception record. 3. THE BRIEF'S DEAD "
            "CATEGORY LABEL MAP IS DELETED rather than kept corrected. No control is added, "
            "moved or removed, and no stored figure changes."),
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
            "Run 48 made the project detail page read the CURRENT period rather than the "
            "hard-coded period 1, and corrected the live instances of the retired naming "
            "scheme; sim-2026.08-v32.",
            "The v25, v26, v27, v28, v29, v30 and v31 releases remain historical evidence and are "
            "not rewritten. Results computed under any of them remain interpretable against "
            "their own records.",
        ],
        "freeze_candidate_commit": ident["candidate_git_commit"],
        "candidate_identity_digest": ident["candidate_identity_digest"],
        "candidate_behaviour_digest": behav["behaviour_digest"],
        "release_content_digest": release_digest,
        "release_content_digest_method": (
            "sha256 over RUN48_SUCCESSOR_FREEZE_CHECKSUMS.csv, which content-addresses every "
            "governed file of the successor instrument. Reproducible from the tree alone."),
        "release_commit_recording_method": pred["release_commit_recording_method"],
        "simulation_version": SIMULATION_VERSION,
        "simulation_version_history": list(SIMULATION_VERSION_HISTORY),
        "participant_package": PP.CURRENT.identifier,
        "participant_package_decision": (
            "SUPERSEDED to og-participant-2026.08-v17. Determined mechanically, not assumed: "
            "THREE of the seventy governed files moved -- assets/js/detail.js, "
            "assets/js/deepdive.js and assets/js/charts3d.js -- and ONE OF THE THREE IS "
            "SEQUENCE-BEARING. deepdive.js moved on the owner's ruling 2, which authorises a "
            "sequence-bearing file to be edited whenever an ordered fix requires it; the "
            "exception is DECLARED BY NAME in participant_packages.py as "
            "V16_TO_V17_SEQUENCE_EXCEPTION rather than admitted by widening the invariant, and "
            "the other five sequence-bearing files are byte for byte identical to v16. What "
            "moved inside deepdive.js is the panel label map, its fallback, and the separation "
            "of the grouping number from the displayed label; the grouping numbers are exactly "
            "the ones the retired labels parsed to, measured panel by panel in the rendered "
            "DOM. No step of the decision sequence, no reveal gate, no lock, no randomization "
            "and NO USER-FACING CONTROL was added, moved or removed."),
        "synthetic_package": "OG-SYNTH-0.6",
        "analysis_schema": "og-analysis-2026.08-v1",
        "canonical_field_classification": {
            "identity": 13, "period": 62, "undetermined": 2, "total_emittable": 77,
            "authority": "code_audit/run45_field_classification_proposal.md, and the owner's "
                         "ruling recorded in REPORT_2026-08-22_run45_period_scoping_fix.md",
            "declared_in": "server/app/field_registry.py IDENTITY_FIELDS / PERIOD_FIELDS / "
                           "UNDETERMINED_FIELDS, asserted at import to partition FIELD_KINDS",
        },
        "behavioural_delta_v31_to_v32": [
            "the project detail page opens on the LATEST PERIOD THAT HAS BEEN COMPUTED rather "
            "than on period 1, so every panel that holds the stored row -- the key drivers, the "
            "abstention reasons, `recommendation_basis` and the Run 47 disagreement findings -- "
            "reads that period's row",
            "`projectperiods` carries two derived read-only fields, `computed_periods` and "
            "`latest_computed_period`, read from the live computed results themselves",
            "the deep-dive panel labels, the synthesis chart node label and the text sent to the "
            "executive brief's model carry no module identifier and no number",
            "the dead category label map in detail.js is deleted",
        ],
        "behavioural_delta_scope_statement": (
            "Exactly these four, and every one of them is on the READ path. NO STORED FIGURE "
            "MOVED and nothing is derived into storage: `_computed_periods` and "
            "`_latest_computed_period` only read the result table, and the detail page only "
            "chooses which stored row to ask for. No formula, band, threshold, calibration, "
            "abstention rule or population moved: voting is still exactly A1.7 and A1.8, 63 "
            "modules in service of 101 registered. THE DETERMINATION IS DERIVED AND ASSUMES "
            "NOTHING: it does not assume the highest period number has results, it does not "
            "assume periods are contiguous, and it assumes no maximum period count; each of the "
            "three is refuted by its own fixture in test_run48_current_period.py. A project with "
            "no computed result in any period keeps the empty state the page already renders. NO "
            "USER-FACING CONTROL WAS ADDED, MOVED OR REMOVED and the detail page holds no period "
            "selector, measured in the real browser DOM."),
        "defects_closed": {
            "detail_page_pinned_to_period_one": (
                "`primeAndRefresh` in assets/js/detail.js read the stored result back with a "
                "hard-coded `period: 1`. Every panel on the project detail page then held that "
                "row, so on a project whose current period was not 1 the whole page showed "
                "period 1 and said nothing about it. It is also why Run 47's browser fixture had "
                "to be single-period. The page now reads the latest period for which computed "
                "results exist, and the Run 48 browser fixture is multi-period."),
            "live_retired_naming_instances": (
                "Three rendered or model-bound sites carried the retired 'Cat N' scheme against "
                "NAMING_AUTHORITY.md:96: deepdive.js's CAT_FROM_MODULE with nineteen entries and "
                "a concatenating fallback, charts3d.js's synthesis node label, and the category "
                "identifier detail.js sent into the executive brief's model prompt. All three "
                "are groups and purposes only. The comment markers that record why a thing moved "
                "are deliberately untouched."),
            "dead_category_label_map": (
                "detail.js carried a category label map that no code read, rediscovered by four "
                "runs. Deleted on the owner's ruling 3."),
        },
        "known_limitation_surviving_retired_scheme_instances": (
            "The section 5.2 re-sweep found further LIVE instances of the retired scheme that "
            "this run was NOT ordered to correct and did NOT correct: the collapsible group "
            "headers deepdive.js builds print 'Cat 1' through 'Cat 10' beside each group name, "
            "and the same file's banner and several of its prose sentences name 'Cat 6.1', 'Cat "
            "7.1-7.9' and 'Cat 8.1'. They are reported rather than corrected, and are enumerated "
            "in the Run 48 report. The three decision-ui.js `period: 1` literals are reported "
            "there too: they were established BY EXECUTION to be inert, because that surface "
            "only ever addresses a research project and the route derives the period from the "
            "assignment and ignores the payload entirely."),
        "scientific_state_unchanged": (
            "NO input was invented, NO fact fabricated, NO qualification rule relaxed and NO "
            "scientific method changed. A module that abstains still abstains, with the same "
            "reason and the same code. Nothing was corrected, substituted, clamped or bounded. "
            "Every expected figure in the Run 47 suite was hand-computed from the stated "
            "formula and written as a literal; the order's own arithmetic was re-derived rather "
            "than copied, and one slip in it was found and reported rather than echoed."),
        "unresolved_high_security_blockers": 0,
        "freeze_gate": {"blockers_evaluated": len(gate), "blocked": len(blocked),
                        "artifact": "research/freeze/run48_successor_freeze_gate.csv"},
        "blocking_defects": 0,
        "limitation_contract": pred["limitation_contract"],
        "predecessor_references": {
            "v25_release_record": "research/freeze/INSTRUMENT_FINAL_FREEZE_RECORD.json",
            "v26_release_record": "research/freeze/RUN41_SUCCESSOR_FREEZE_RECORD.json",
            "v27_release_record": "research/freeze/RUN42_SUCCESSOR_FREEZE_RECORD.json",
            "v28_release_record": "research/freeze/RUN43_SUCCESSOR_FREEZE_RECORD.json",
            "v29_release_record": "research/freeze/RUN44_SUCCESSOR_FREEZE_RECORD.json",
            "v30_release_record": "research/freeze/RUN45_SUCCESSOR_FREEZE_RECORD.json",
            "v31_release_record": "research/freeze/RUN47_SUCCESSOR_FREEZE_RECORD.json",
            "v31_candidate_identity": "research/freeze/run47_freeze_candidate_identity.json",
            "v31_freeze_gate": "research/freeze/run47_successor_freeze_gate.csv",
            "statement": ("All of these are preserved unchanged. That they still record v25, "
                          "v26, v27, v28, v29, v30 and v31 is asserted by the requalified "
                          "gates, not assumed."),
        },
        "governed_files_moved_since_v31": moved,
    }
    (artifact_out(FREEZE / "RUN48_SUCCESSOR_FREEZE_RECORD.json")).write_text(
        json.dumps(rec, indent=2) + "\n", encoding="utf-8")

    report = f"""# Run-48 successor freeze report

**Disposition: FINAL_FREEZE_ACCEPTED** for `sim-2026.08-v32`.

## Why there is a successor at all

The project detail page read the stored result back with a hard-coded `period: 1`. Every panel on
that page holds whatever that one call returns, so on a project whose current period was not 1
the key drivers, the abstention reasons, the served basis for the recommendation and the Run 47
disagreement findings all described period 1. WHICH STORED ROW A PAGE READS is executable
behaviour, so v31 is **superseded, not amended**.

    v25 accepted freeze -> S1/S2 -> v26 -> mechanism repair -> v27 -> retirement -> v28
    -> render repairs -> v29 -> retrieval by field kind -> v30 -> the EVM consistency check
    -> v31 -> the current period and the live naming instances -> v32 successor

## The three rulings, and what each became

| ruling | what was built |
|---|---|
| The page shows the latest period that has been computed | `_computed_periods` and `_latest_computed_period` in `server/app/documents.py`, read from the live computed results; `projectperiods` serves them; `primeAndRefresh` reads that period's row |
| The live naming instances are corrected | `deepdive.js` panel labels and fallback, `charts3d.js` node label, the brief prompt in `detail.js`: groups and purposes only |
| The dead category label map is deleted | Removed from `detail.js` outright |

## What changed, and what did not

| Subject | Result |
|---|---|
| Stored figures of any kind | **unchanged**; every addition is on the read path |
| Project status, category statuses, bands, colours, postures | **unchanged** |
| Registered / in service / voting | 101 / 63 / exactly A1.7 and A1.8, all identical |
| Sequence-bearing participant files | **one moved**, `assets/js/deepdive.js`, on ruling 2, with its own named exception record; the other five are byte-identical |
| User-facing controls | **none added, moved or removed**; the detail page still has no period selector |
| Participant package | SUPERSEDED to `og-participant-2026.08-v17` |
| Synthetic package | RETAINED `OG-SYNTH-0.6` |
| Analysis schema | RETAINED `og-analysis-2026.08-v1` |

## Gate

{len(gate)} blocker classes evaluated, {len(blocked)} blocked. Artifact:
`research/freeze/run48_successor_freeze_gate.csv`.

The v25, v26, v27, v28, v29, v30 and v31 release records are preserved unchanged and still record
their own stamps.
"""
    (artifact_out(FREEZE / "RUN48_SUCCESSOR_FREEZE_REPORT.md")).write_text(report, encoding="utf-8")

    print("wrote RUN48_SUCCESSOR_FREEZE_CHECKSUMS.csv:", len(rows), "rows")
    print("wrote RUN48_SUCCESSOR_FREEZE_RECORD.json")
    print("wrote RUN48_SUCCESSOR_FREEZE_REPORT.md")
    print("governed files moved since v31:", moved or "(none)")
    print("release content digest:", release_digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
