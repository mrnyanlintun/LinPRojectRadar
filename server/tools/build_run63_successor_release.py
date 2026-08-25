#!/usr/bin/env python3
"""
RUN 63. THE SUCCESSOR FREEZE RELEASE RECORDS.

Writes, beside the v25 and v26 releases and never over either:

  research/freeze/RUN59_SUCCESSOR_FREEZE_RECORD.json
  research/freeze/RUN59_SUCCESSOR_FREEZE_REPORT.md
  research/freeze/RUN59_SUCCESSOR_FREEZE_CHECKSUMS.csv

The historical relationship is explicit in every one of them:

    v25 accepted freeze -> Run 40 identified S1/S2 -> owner authorised remediation
    -> v26 successor -> Run 42 proved two identity losses -> v27 successor
    -> owner's retirement ruling -> v28 successor -> Run 43J diagnosed eleven render defects
    -> owner ordered four of them repaired -> v29 successor -> Run 44 measured the period-scoping
    fall-through -> owner signed off the canonical field classification -> v30 successor

The v25, v26, v27, v28 and v29 records remain exactly as Runs 37, 41, 42, 43 and 44 wrote them. They are
the evidence for anything computed under those stamps and a successor that edited them would
destroy it.

Usage: python tools/build_run57_successor_release.py
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

#: THE ONLY DISAPPEARANCES THIS BUILDER WILL ACCEPT. Not written here by hand: read from the
#: package chain's own record. A file may only leave a governed manifest by being named there,
#: and it is RECORDED IN the manifest as DELETED rather than dropped out of it, so the release
#: still names every file the predecessor governed.
DECLARED_DELETIONS = tuple(PP.V25_TO_V26_DELETED)

#: EXPLICIT COMMIT HASH, never a relative reference: Run 54 wrote its own proofs of absence
#: against HEAD~1 and they decayed silently into false proofs that still passed as later commits
#: walked the reference back.
RUN54_PREDELETION_COMMIT = "e13b4f1"

PREDECESSOR_RECORD = FREEZE / "RUN62_SUCCESSOR_FREEZE_RECORD.json"
PREDECESSOR_CHECKSUMS = FREEZE / "RUN62_SUCCESSOR_FREEZE_CHECKSUMS.csv"
IDENTITY = FREEZE / "run63_freeze_candidate_identity.json"
GATE = FREEZE / "run63_successor_freeze_gate.csv"
BEHAVIOUR = FREEZE / "run63_candidate_behaviour_digest.json"


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
    rows, moved, deleted = [], [], []
    for r in pred_rows:
        p = ROOT / r["path"]
        if not p.is_file():
            # THE REFUSAL IS NARROWED BY DECLARATION, NOT WEAKENED. A governed file vanishing is
            # normally a release that has silently stopped measuring something, and that must
            # still raise. It is accepted here only when the file is named in
            # participant_packages.V20_TO_V21_DELETED -- the record the package chain already
            # carries -- AND it really is absent AND it really existed at the pinned predeletion
            # commit. An undeclared disappearance still raises.
            # RUN 56, A SECOND NARROWING AND NOT A WEAKENING. The predecessor manifest CARRIES
            # its deletions forward as rows rather than dropping them, with an empty sha256 and
            # a `moved_since_v32` of DELETED_BY_RUN54. Such a row is an ALREADY-RECORDED
            # deletion, not a new one, and requiring a fresh declaration for it every run would
            # mean re-declaring every historical deletion forever -- which would make the
            # declaration list a list of history rather than a list of THIS link's deletions,
            # and would hide a genuinely new disappearance among them.
            #
            # It is accepted here ONLY when the predecessor row itself already recorded the
            # deletion AND the sha256 it carries is empty AND the file really is still absent.
            # A file that vanished for the FIRST time in this link still requires a declaration
            # in participant_packages, still has to have existed at the pinned commit, and still
            # raises without one. A predecessor row that carried real bytes and whose file has
            # now vanished still raises.
            already_recorded = (r.get("moved_since_v32", "").startswith("DELETED_BY_")
                                and not r["sha256"])
            if already_recorded:
                deleted.append(r["path"])
                rows.append({"path": r["path"], "sha256": "", "git_object": "",
                             "tracked": r["tracked"],
                             "moved_since_v32": r["moved_since_v32"]})
                print(f"  deletion ALREADY RECORDED by the predecessor manifest, carried "
                      f"forward and still absent: {r['path']}")
                continue
            if r["path"] not in DECLARED_DELETIONS:
                raise SystemExit(f"a governed file named by the predecessor manifest is "
                                 f"missing and is NOT declared as deleted: {r['path']}")
            rc = subprocess.run(["git", "cat-file", "-e",
                                 f"{RUN54_PREDELETION_COMMIT}:{r['path']}"],
                                cwd=ROOT, capture_output=True).returncode
            if rc != 0:
                raise SystemExit(f"declared deletion {r['path']} did not exist at "
                                 f"{RUN54_PREDELETION_COMMIT}; the declaration is vacuous.")
            deleted.append(r["path"])
            rows.append({"path": r["path"], "sha256": "", "git_object": "",
                         "tracked": r["tracked"], "moved_since_v32": "DELETED_BY_RUN63"})
            print(f"  DECLARED DELETION recorded in the manifest, not dropped from it: "
                  f"{r['path']}")
            continue
        h = sha(p)
        if h != r["sha256"]:
            moved.append(r["path"])
        rows.append({"path": r["path"], "sha256": h, "git_object": git_object(p),
                     "tracked": r["tracked"],
                     "moved_since_v32": "YES" if h != r["sha256"] else "no"})
    for extra in ("research/freeze/run63_freeze_candidate_identity.json",
                  "research/freeze/run63_successor_freeze_gate.csv",
                  "code_audit/run63_participant_package_v26_checksums.sha256",
                  "code_audit/run63_production_tree.sha256",
                  "server/tools/build_run63_candidate_identity.py",
                  "server/tools/build_run63_successor_release.py",
                  "server/tools/drive_run63_four_charts.py",
                  "server/tools/test_run63_four_charts.py",
                  "research/freeze/run62_freeze_candidate_identity.json",
                  "research/freeze/run62_successor_freeze_gate.csv",
                  "code_audit/run62_participant_package_v25_checksums.sha256",
                  "code_audit/run62_production_tree.sha256",
                  "server/tools/build_run62_candidate_identity.py",
                  "server/tools/build_run62_successor_release.py",
                  "server/tools/drive_run61_caller_shapes.py",
                  "server/tools/test_run61_caller_states_its_question.py",
                  "research/freeze/run59_freeze_candidate_identity.json",
                  "research/freeze/run62_successor_freeze_gate.csv",
                  "code_audit/run59_participant_package_v24_checksums.sha256",
                  "code_audit/run59_production_tree.sha256",
                  "server/tools/build_run59_candidate_identity.py",
                  "server/tools/build_run59_successor_release.py",
                  "research/freeze/run57_freeze_candidate_identity.json",
                  "research/freeze/run57_successor_freeze_gate.csv",
                  "code_audit/run57_participant_package_v23_checksums.sha256",
                  "code_audit/run57_production_tree.sha256",
                  "server/tools/drive_run57_reset_merge.py",
                  "server/tools/drive_run57_derived_pins.py",
                  "research/freeze/run56_freeze_candidate_identity.json",
                  "research/freeze/run56_successor_freeze_gate.csv",
                  "code_audit/run56_participant_package_v22_checksums.sha256",
                  "code_audit/run56_production_tree.sha256",
                  "server/tools/drive_run56_duplicate_controls.py",
                  "research/freeze/run55_freeze_candidate_identity.json",
                  "research/freeze/run55_successor_freeze_gate.csv",
                  "code_audit/run55_participant_package_v21_checksums.sha256",
                  "code_audit/run55_production_tree.sha256",
                  "server/tools/campaign_safety.py",
                  "server/tools/drive_run54_navigation.py",
                  "server/tools/drive_run55_admin_controls.py",
                  "server/tools/test_run49_naming_completion.py",
                  "server/tools/drive_run52_browser.py",
                  "server/tools/drive_run51_browser.py",
                  "server/tools/run51_dash_sweep.py",
                  "server/tools/drive_run49_browser.py"):
        p = ROOT / extra
        rows.append({"path": extra, "sha256": sha(p), "git_object": git_object(p),
                     "tracked": "TRACKED", "moved_since_v32": "ADDED_BY_RUN63"})

    out_sums = FREEZE / "RUN63_SUCCESSOR_FREEZE_CHECKSUMS.csv"
    with out_sums.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["path", "sha256", "git_object", "tracked",
                                           "moved_since_v32"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    release_digest = hashlib.sha256(out_sums.read_text(encoding="utf-8").encode()).hexdigest()

    rec = {
        "release_disposition": "FINAL_FREEZE_ACCEPTED",
        "label": "Opus Gubernatio research instrument, Run-59 successor freeze (sim-2026.08-v39)",
        "created": datetime.date(2026, 8, 25).isoformat(),
        "authority": (
            "THE OWNER'S RUN 62 ORDER, SECTION 2: the fix exists and is not on the site. Two branches "
            "were finished, gated nowhere and stacked unmerged -- Run 60's diagnosis at 75ea02e and "
            "Run 61's fix at a8fa1bd -- and Run 61 correctly refused to merge production bytes whose "
            "gate status was unknown. THIS RELEASE RUNS THE GATE AND PUBLISHES THEM. THREE of the 242 "
            "production-tree members moved: assets/js/detail.js, assets/js/taxonomy.js and "
            "assets/js/workspace.js. TWO files were ADDED under server/tools -- "
            "drive_run61_caller_shapes.py and test_run61_caller_states_its_question.py -- so the suite "
            "population this release measures is 204, up from 203, and test_suite_identity is DERIVED "
            "from the filesystem rather than copied so the new suite cannot be silently unmeasured. "
            "WHAT WAS FIXED: the stored-signal row a project detail page reads was not necessarily the "
            "row of the period the page holds. taxonomy.js now keys its row cache by (project, period) "
            "and exposes rowForPeriod, latest and rowsForPeriods, with the period travelling with the "
            "row; workspace.js resolves projectperiods then latest_computed_period then projectresults, "
            "so the caller states its question before it asks; detail.js re-renders its provenance line "
            "from the row it actually received. assets/js/workspace.js IS SEQUENCE-BEARING and this "
            "link therefore carries a NAMED EXCEPTION OF RECORD in V24_TO_V25_SEQUENCE_EXCEPTION, "
            "declared rather than discovered by a checksum; what moved inside it is the ORDER OF THE "
            "SERVER CALLS and no step of the decision sequence, no reveal gate, no lock, no "
            "randomization and no questionnaire moved. assets/js/taxonomy.js is NOT sequence-bearing, "
            "MEASURED against SEQUENCE_BEARING_FILES_FROM_V21. NO CONTROL was added, moved or removed. "
            "NOTHING IS COMPUTED DIFFERENTLY AND NO STORED FIGURE MOVED: 101 registered, 63 in service, "
            "voting exactly A1.7 and A1.8, and the behaviour digest is RE-DERIVED and unchanged. THE "
            "AUTHORITY TREE DID NOT MOVE: its manifest sha256 b52c47a68a20ab1629681ea240abdea2167c67f2"
            "89d181f446a8170704dc1596 is unmoved for a SIXTH run. The v24 record is NOT regenerated: it "
            "describes the tree as v24 left it and is PINNED to 5f5cf60."),
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
            "Run 49 finished that naming correction across every surviving rendered instance the "
            "sweep enumerated, extended the deep-dive panel label map to every key the call "
            "sites pass, and recorded the server's period override at the three inert literals "
            "in decision-ui.js; sim-2026.08-v33.",
            "Run 50 measured every visual surface in a rendered browser and HALTED without "
            "merging on three stop conditions, establishing that the five visual surfaces "
            "already drew the population in service and that what the owner saw was a typed "
            "literal at knowledge.js:585.",
            "Run 51 delivered the six rulings Run 50 stopped on; sim-2026.08-v34.",
            "Run 52 removed the dead see-Health button and moved the module identifier to one "
            "name on both sides of the wire, module_id, and STOPPED ruling 1 under section 8.1 "
            "after establishing by execution that Manage does not reach the project detail "
            "page; sim-2026.08-v35.",
            "Runs 54 and 55, taken as one supersession, deleted the unreachable client-side "
            "deep-dive surface and its route, made the project list's Manage control navigate "
            "to the project detail page in place of a redundant Open control, moved the six "
            "operational admin controls onto that detail page, and brought server/tests/ inside "
            "the suite runner so the suite population became 203; sim-2026.08-v36.",
            "Runs 60 and 61, taken as one supersession and PUBLISHED by Run 62: Run 60 "
            "diagnosed in a rendered browser that the stored-signal row a project detail page "
            "reads was not necessarily the row of the period the page holds, and Run 61 fixed it "
            "by making the caller state its question -- the row cache keyed by (project, period), "
            "the period travelling with the row, and the workspace resolving the period before it "
            "asks for results; sim-2026.08-v40.",
            "The v25 to v34 releases remain historical evidence and are "
            "not rewritten. Results computed under any of them remain interpretable against "
            "their own records.",
        ],
        "freeze_candidate_commit": ident["candidate_git_commit"],
        "candidate_identity_digest": ident["candidate_identity_digest"],
        "candidate_behaviour_digest": behav["behaviour_digest"],
        "release_content_digest": release_digest,
        "release_content_digest_method": (
            "sha256 over RUN63_SUCCESSOR_FREEZE_CHECKSUMS.csv, which content-addresses every "
            "governed file of the successor instrument. Reproducible from the tree alone."),
        "release_commit_recording_method": pred["release_commit_recording_method"],
        "simulation_version": SIMULATION_VERSION,
        "simulation_version_history": list(SIMULATION_VERSION_HISTORY),
        "participant_package": PP.CURRENT.identifier,
        "participant_package_decision": (
            "SUPERSEDED to og-participant-2026.08-v25. Determined mechanically, not assumed: EXACTLY "
            "THREE of the sixty-nine governed files moved -- assets/js/detail.js, "
            "assets/js/taxonomy.js and assets/js/workspace.js -- and nothing was added and nothing "
            "deleted. ONE of the three IS SEQUENCE-BEARING, assets/js/workspace.js, so this link "
            "carries a NAMED EXCEPTION OF RECORD in V24_TO_V25_SEQUENCE_EXCEPTION with its own "
            "paragraph in the v25 checksum record. Whether taxonomy.js or workspace.js was "
            "sequence-bearing was ESTABLISHED BY MEASUREMENT against SEQUENCE_BEARING_FILES_FROM_V21 "
            "rather than assumed: taxonomy.js is not a member, workspace.js is. The other FOUR members "
            "of that set -- decision.js, decision-ui.js, intake.json and debrief.json -- are present "
            "and byte for byte identical to v24, measured. What moved inside workspace.js is the ORDER "
            "OF THE SERVER CALLS the client makes when loading a project's stored signals. NO step of "
            "the decision sequence, NO reveal gate, NO lock, NO randomization, NO questionnaire, NO "
            "append-only record and NO REACHABLE USER-FACING CONTROL was added, moved or removed."),
        "synthetic_package": "OG-SYNTH-0.6",
        "analysis_schema": "og-analysis-2026.08-v1",
        "canonical_field_classification": {
            "identity": 13, "period": 62, "undetermined": 2, "total_emittable": 77,
            "authority": "code_audit/run45_field_classification_proposal.md, and the owner's "
                         "ruling recorded in REPORT_2026-08-22_run45_period_scoping_fix.md",
            "declared_in": "server/app/field_registry.py IDENTITY_FIELDS / PERIOD_FIELDS / "
                           "UNDETERMINED_FIELDS, asserted at import to partition FIELD_KINDS",
        },
        "behavioural_delta_v39_to_v40": [
            "THE ONE OBSERVABLE CHANGE IS A CORRECTION, and it is named rather than denied: a project "
            "detail page now renders the stored-signal row of the period the page holds. Before this "
            "release a page holding period 4 could render period 1's figures, which the owner saw as "
            "CPI 1.22 on a period-4 page and which the owner's own production query has since closed "
            "as period-mixing rather than as a data defect",
            "NO formula, band, threshold, calibration, abstention rule or population moved. NO stored "
            "figure moved and nothing is derived into storage",
            "NO user-facing control was added, moved or removed",
            "assets/js/workspace.js is SEQUENCE-BEARING and its move is a NAMED EXCEPTION of record. "
            "What moved inside it is the ORDER OF THE SERVER CALLS, not a step of the sequence"
        ],
        "behavioural_delta_scope_statement": (
            "ONE BEHAVIOUR MOVES AND IT IS THE DEFECT BEING CORRECTED: which stored row a project "
            "detail page reads. NOTHING ELSE. NO STORED FIGURE MOVED and nothing is derived into "
            "storage. No formula, band, threshold, calibration, abstention rule or population moved: "
            "voting is still exactly A1.7 and A1.8, 63 modules in service of 101 registered, and the "
            "behaviour digest is RE-DERIVED and unchanged. NO user-facing control was added, moved or "
            "removed."),
        "defects_closed": {
            "surviving_rendered_retired_scheme_instances": (
                "Run 48's second sweep enumerated rendered instances of the retired 'Cat N' "
                "scheme it was not ordered to correct: the ten collapsible group headers, the "
                "Signal Stack banner, the Dempster-Shafer metric-box label, the synthesis "
                "comparison heading and note, three confidence sentences, and one sentence "
                "reaching the executive brief's model. All are corrected here, together with "
                "three further live instances this run's own sweep found that no order named: "
                "the 'Module NN:' prefix on every comparison-table row, the 'Agrees with M09' "
                "column header, and the 'D1.N' identifier on each Portfolio Health module "
                "heading."),
            "deep_dive_panel_label_collapse": (
                "Run 48's corrected fallback resolved every key the map did not cover onto the "
                "single phrase 'Signal Analysis', which was correct under the authority but "
                "collapsed roughly sixty panels onto one heading. The map now covers all "
                "seventy-seven keys the call sites pass, each resolving to the purpose of the "
                "MODULE ITSELF, taken from the module's own title at its call site and not from "
                "the collapsible group it is filed under."),
            "ampersand_in_a_section_title": (
                "assets/js/detail.js titled a section 'Documents & Extracted Signals'. The "
                "naming authority requires the word 'and' in user-facing text."),
            "undocumented_inert_period_literals": (
                "assets/js/decision-ui.js carries three `period: 1` literals that the server "
                "overrides. They are LEFT IN PLACE on ruling 4 because they change nothing, and "
                "each site now records that documents._resolve_period derives the period from "
                "the research assignment and ignores the value."),
        },
        "known_limitation_surviving_retired_scheme_instances": (
            "STATED PLAINLY RATHER THAN CLAIMED CLOSED. Run 49's own repository-wide sweep of "
            "assets/ found module identifiers still rendering OUTSIDE the surfaces this run was "
            "ordered to correct, and they are NOT corrected here: assets/js/app.js prints the "
            "category identifier at :1360 and the module identifier at :1346 on the Categories "
            "page, both read from the GENERATED taxonomy in assets/js/categories.js, so "
            "correcting them means changing server/tools/taxonomy_authority.json and "
            "regenerating. En dashes and em dashes also remain in user-facing text across "
            "roughly forty files in assets/, including four SEQUENCE-BEARING files -- "
            "decision.js, workspace.js, intake.json and debrief.json -- which this run has no "
            "authority to move and which stop condition 9.5 forbids it to move. Run 48's "
            "guarantee 11 is therefore recorded as NOT MET for a second time, with the reason "
            "named, rather than reported as met."),
        "scientific_state_unchanged": (
            "NO input was invented, NO fact fabricated, NO qualification rule relaxed and NO "
            "scientific method changed. A module that abstains still abstains, with the same "
            "reason and the same code. Nothing was corrected, substituted, clamped or bounded. "
            "Every expected figure in the Run 47 suite was hand-computed from the stated "
            "formula and written as a literal; the order's own arithmetic was re-derived rather "
            "than copied, and one slip in it was found and reported rather than echoed."),
        "unresolved_high_security_blockers": 0,
        "freeze_gate": {"blockers_evaluated": len(gate), "blocked": len(blocked),
                        "artifact": "research/freeze/run62_successor_freeze_gate.csv"},
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
            "v32_release_record": "research/freeze/RUN48_SUCCESSOR_FREEZE_RECORD.json",
            "v32_candidate_identity": "research/freeze/run48_freeze_candidate_identity.json",
            "v32_freeze_gate": "research/freeze/run48_successor_freeze_gate.csv",
            "statement": ("All of these are preserved unchanged. That they still record v25, "
                          "v26, v27, v28, v29, v30, v31 and v32 is asserted by the requalified "
                          "gates, not assumed."),
        },
        "governed_files_moved_since_v32": moved,
    }
    (FREEZE / "RUN62_SUCCESSOR_FREEZE_RECORD.json").write_text(
        json.dumps(rec, indent=2) + "\n", encoding="utf-8")

    report = f"""# Run-62 successor freeze report

**Disposition: FINAL_FREEZE_ACCEPTED** for `sim-2026.08-v40`.

## Why there is a successor at all

**The fix is published.** Two branches were finished, gated nowhere and stacked unmerged: Run
60's diagnosis and Run 61's fix. Three of the 242 governed production-tree members moved --
`assets/js/detail.js`, `assets/js/taxonomy.js`, `assets/js/workspace.js` -- and two files were
added under `server/tools`, which moves the suite population this freeze measures from 203 to
204.

    v25 accepted freeze -> ... -> v39 -> the caller states its question -> v40 successor

## The defect, and what closed it

A project detail page read a stored-signal row that was not necessarily the row of the period
the page holds. `taxonomy.js` now keys its row cache by `(project, period)` and exposes
`rowForPeriod` (that period or nothing), `latest` (the period travels with the row) and
`rowsForPeriods`. `workspace.js` resolves `projectperiods`, then `latest_computed_period`, then
`projectresults`, so the caller states its question before it asks. `detail.js` re-renders its
provenance line from the row it actually received.

## What a participant reads and clicks, before and after

One sequence-bearing file moved, `assets/js/workspace.js`, so this link carries a **named
exception of record** in `V24_TO_V25_SEQUENCE_EXCEPTION`. What moved inside it is the ORDER OF
THE SERVER CALLS. The other four members of `SEQUENCE_BEARING_FILES_FROM_V21` are present and
byte-identical, measured. `taxonomy.js` is **not** sequence-bearing, measured and not assumed.

NO STORED FIGURE MOVED. Voting is still exactly A1.7 and A1.8, 63 modules in service of 101
registered, and the behaviour digest is RE-DERIVED and unchanged. No control was added, moved or
removed.

## Gate

{len(gate)} blocker classes evaluated, {len(blocked)} blocked. Artifact:
`research/freeze/run62_successor_freeze_gate.csv`.

The v25 to v39 release records are preserved unchanged and still record their own stamps.
"""
    (FREEZE / "RUN62_SUCCESSOR_FREEZE_REPORT.md").write_text(report, encoding="utf-8")

    print("wrote RUN62_SUCCESSOR_FREEZE_CHECKSUMS.csv:", len(rows), "rows")
    print("wrote RUN62_SUCCESSOR_FREEZE_RECORD.json")
    print("wrote RUN62_SUCCESSOR_FREEZE_REPORT.md")
    print("governed files moved since v32:", moved or "(none)")
    print("release content digest:", release_digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
