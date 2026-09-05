#!/usr/bin/env python3
"""
RUN 59. THE SUCCESSOR FREEZE RELEASE RECORDS.

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

#: THE ONLY DISAPPEARANCES THIS BUILDER WILL ACCEPT. Not written here by hand: read from the
#: package chain's own record. A file may only leave a governed manifest by being named there,
#: and it is RECORDED IN the manifest as DELETED rather than dropped out of it, so the release
#: still names every file the predecessor governed.
DECLARED_DELETIONS = tuple(PP.V23_TO_V24_DELETED)

#: EXPLICIT COMMIT HASH, never a relative reference: Run 54 wrote its own proofs of absence
#: against HEAD~1 and they decayed silently into false proofs that still passed as later commits
#: walked the reference back.
RUN54_PREDELETION_COMMIT = "e13b4f1"

PREDECESSOR_RECORD = FREEZE / "RUN57_SUCCESSOR_FREEZE_RECORD.json"
PREDECESSOR_CHECKSUMS = FREEZE / "RUN57_SUCCESSOR_FREEZE_CHECKSUMS.csv"
IDENTITY = FREEZE / "run59_freeze_candidate_identity.json"
GATE = FREEZE / "run59_successor_freeze_gate.csv"
BEHAVIOUR = FREEZE / "run59_candidate_behaviour_digest.json"


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
                         "tracked": r["tracked"], "moved_since_v32": "DELETED_BY_RUN59"})
            print(f"  DECLARED DELETION recorded in the manifest, not dropped from it: "
                  f"{r['path']}")
            continue
        h = sha(p)
        if h != r["sha256"]:
            moved.append(r["path"])
        rows.append({"path": r["path"], "sha256": h, "git_object": git_object(p),
                     "tracked": r["tracked"],
                     "moved_since_v32": "YES" if h != r["sha256"] else "no"})
    for extra in ("research/freeze/run59_freeze_candidate_identity.json",
                  "research/freeze/run59_successor_freeze_gate.csv",
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
                     "tracked": "TRACKED", "moved_since_v32": "ADDED_BY_RUN59"})

    out_sums = FREEZE / "RUN59_SUCCESSOR_FREEZE_CHECKSUMS.csv"
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
            "THE OWNER'S RULING IN THE RUN 59 ORDER, SECTION 2, CARRIED IN FULL: NO MARKDOWN DOCUMENT "
            "IN THIS REPOSITORY CARRIES AUTHORITY. Production code is the truth; REPORT_*.md, "
            "code_audit/REPORT_*.md, research/freeze/*.md and the fixture records are SEALED EVIDENCE; "
            "everything else is transport or history and governs nothing. SIX of the 242 production-tree "
            "members moved and EVERY ONE OF THE SIX EDITS IS A COMMENT OR A DOCUMENT HEADING -- "
            "assets/js/decision-ui.js, p0-baseline/MODULE_TAXONOMY.md, server/app/research_export.py, "
            "server/app/document_evidence.py, server/app/evm_consistency.py and "
            "server/app/simulation/portfolio_health.py. NOT ONE EXECUTABLE BYTE MOVED, no rendered string "
            "moved and no control was added, moved or removed. Five of the six cited a module-identifier "
            "prohibition the owner SUPERSEDED on 2026-08-23; research_export.py cited it BY NUMBER as "
            "'NAMING_AUTHORITY.md rule 6', and portfolio_health.py cited 'NAMING_AUTHORITY section 4', "
            "which is the very section that RECORDED THE REVERSAL, so the code cited the reversal as the "
            "source of the rule. In all five the citation is DROPPED and the reason stated directly, "
            "established by execution rather than assumed: no test anywhere reads any of those comment "
            "strings. assets/js/decision-ui.js is SEQUENCE-BEARING, so this link carries a NAMED "
            "EXCEPTION OF RECORD in V23_TO_V24_SEQUENCE_EXCEPTION, and what moved inside it is proved to "
            "be a comment and nothing else: the file is byte-identical to v23 once block comments are "
            "stripped, and GROUP_NAMES and MODULE_NAMES are byte-identical across the link. PHASE A "
            "corrected EIGHT documents, not the five the order named -- an uncapped sweep added "
            "COPY_GLOSSARY.md, README.md and BACKEND_CHANGES_NEEDED.md to Run 58's inventory -- and "
            "corrected MODULE_RETIREMENT_DECISIONS.md, which said the REGISTERED count fell 101 to 63 "
            "when it is the IN-SERVICE count that fell. PHASE B REMOVED THE GUARDS THAT ASSERTED A "
            "MARKDOWN DOCUMENT'S CONTENT. FOUR were RE-POINTED at non-markdown production oracles and "
            "every one was proved still able to fail BY BREAKING PRODUCTION, not by breaking a document: "
            "test_group_assignment.py, which used to raise SystemExit and ABORT THE SUITE when a fenced "
            "block went missing, now reads p0-baseline/module_renumbering_map.csv; test_disclaimers.py's "
            "meta-description check now reads assets/js/knowledge.js; and both DISCLAIMERS_DRAFT.md "
            "comparisons now read assets/js/disclaimers.js. FIFTEEN further checks were RETIRED THE WAY "
            "MODULES WERE RETIRED -- they stop running, their bodies are NOT deleted, and the reason is "
            "recorded beside each. NO CHECK WAS DELETED. Run 58's finding of the first order is closed: "
            "REPORT_2026-08-18_run34-portfolio-health-calibration.md, an EVIDENCE document, was read as "
            "an AUTHORITY by four live suites, one of them out of a merged commit so that even a correct "
            "edit could not restore green. TWO guards were STOPPED rather than re-pointed, because "
            "re-pointing would have meant inventing an oracle. NOTHING IS COMPUTED DIFFERENTLY AND NO "
            "STORED FIGURE MOVED: 101 registered, 63 in service, voting exactly A1.7 and A1.8, and the "
            "behaviour digest is RE-DERIVED and unchanged. THE AUTHORITY TREE DID NOT MOVE: its manifest "
            "sha256 b52c47a68a20ab1629681ea240abdea2167c67f289d181f446a8170704dc1596 is unmoved for a "
            "FIFTH run, and the supervisory specification is NOT deleted, NOT renamed and NOT removed "
            "from it -- only its CONTROLLING designation is withdrawn. THE SUITE POPULATION THIS RELEASE "
            "MEASURES IS 203 and is unchanged. The v23 candidate, its identity, its gate and its release "
            "records are preserved unchanged as the historical evidence for anything computed under v38."),
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
            "The v25 to v34 releases remain historical evidence and are "
            "not rewritten. Results computed under any of them remain interpretable against "
            "their own records.",
        ],
        "freeze_candidate_commit": ident["candidate_git_commit"],
        "candidate_identity_digest": ident["candidate_identity_digest"],
        "candidate_behaviour_digest": behav["behaviour_digest"],
        "release_content_digest": release_digest,
        "release_content_digest_method": (
            "sha256 over RUN59_SUCCESSOR_FREEZE_CHECKSUMS.csv, which content-addresses every "
            "governed file of the successor instrument. Reproducible from the tree alone."),
        "release_commit_recording_method": pred["release_commit_recording_method"],
        "simulation_version": SIMULATION_VERSION,
        "simulation_version_history": list(SIMULATION_VERSION_HISTORY),
        "participant_package": PP.CURRENT.identifier,
        "participant_package_decision": (
            "SUPERSEDED to og-participant-2026.08-v22. Determined mechanically, not assumed: "
            "EXACTLY ONE of the sixty-nine governed files moved -- assets/js/ingest.js -- and "
            "NOTHING was added and nothing deleted. IT IS NOT SEQUENCE-BEARING, so this link "
            "carries NO sequence exception and V21_TO_V22_SEQUENCE_EXCEPTION is an EMPTY tuple "
            "that is DECLARED rather than omitted; all five members of "
            "SEQUENCE_BEARING_FILES_FROM_V21 are present and byte for byte identical to v21, "
            "measured and not assumed. What moved inside ingest.js is the removal of the "
            "DUPLICATE 'Upload documents' control from the detail page only, whose survivor was "
            "proved to do everything it did, and a confirmation in front of Archive and in "
            "front of Reset signals built on the LinUI.openModal shape the application already "
            "uses for its destructive project-scoped actions. NO RENDERED IDENTIFIER CHANGED. "
            "assets/js/detail.js is byte for byte identical to v21 because the second removal "
            "the order directed was STOPPED under section 9.1. No step of the decision "
            "sequence, no reveal gate, no lock, no randomization and NO REACHABLE USER-FACING "
            "CONTROL other than the one duplicate the order names was added, moved or "
            "removed."),
        "synthetic_package": "OG-SYNTH-0.6",
        "analysis_schema": "og-analysis-2026.08-v1",
        "canonical_field_classification": {
            "identity": 13, "period": 62, "undetermined": 2, "total_emittable": 77,
            "authority": "code_audit/run45_field_classification_proposal.md, and the owner's "
                         "ruling recorded in REPORT_2026-08-22_run45_period_scoping_fix.md",
            "declared_in": "server/app/field_registry.py IDENTITY_FIELDS / PERIOD_FIELDS / "
                           "UNDETERMINED_FIELDS, asserted at import to partition FIELD_KINDS",
        },
        "behavioural_delta_v38_to_v39": [
            "NONE. This release changes NO behaviour a participant can observe. Six production-tree "
            "members moved and every one of the six edits is a COMMENT or a DOCUMENT HEADING: not one "
            "executable byte, not one rendered string, not one control",
            "assets/js/decision-ui.js is SEQUENCE-BEARING and its move is a NAMED EXCEPTION of record. "
            "What moved inside it is PROVED to be a comment and nothing else: the file is byte-identical "
            "to v23 once block comments are stripped, and GROUP_NAMES and MODULE_NAMES are byte-identical "
            "across the link, asserted rather than asserted-about",
            "the stamp moves because the MANIFEST moves, which is the version-boundary rule working as "
            "intended, not because behaviour did"
        ],
        "behavioural_delta_scope_statement": (
            "EXACTLY NONE, and that is a measured statement rather than a hopeful one. NO STORED FIGURE "
            "MOVED and nothing is derived into storage. No formula, band, threshold, calibration, "
            "abstention rule or population moved: voting is still exactly A1.7 and A1.8, 63 modules in "
            "service of 101 registered, and the behaviour digest is RE-DERIVED and unchanged. NO "
            "user-facing control was added, moved or removed. NO rendered text changed. What this release "
            "contains is a correction to what the repository SAYS about itself and the removal of every "
            "check that let a document with no authority turn a guard red."),
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
                        "artifact": "research/freeze/run59_successor_freeze_gate.csv"},
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
    (artifact_out(FREEZE / "RUN59_SUCCESSOR_FREEZE_RECORD.json")).write_text(
        json.dumps(rec, indent=2) + "\n", encoding="utf-8")

    report = f"""# Run-59 successor freeze report

**Disposition: FINAL_FREEZE_ACCEPTED** for `sim-2026.08-v39`.

## Why there is a successor at all

**No behaviour moved.** Six of the 242 governed production-tree members moved and every one of
the six edits is a comment or a document heading. The stamp advances because the MANIFEST
advances, which is the version-boundary rule working as intended, and because one of the six is
`assets/js/decision-ui.js`, a **sequence-bearing** participant file. What a participant reads and
clicks is part of the frozen candidate, so v38 is **superseded, not amended** -- even though what
a participant reads and clicks is, in this release, byte for byte what it was.

    v25 accepted freeze -> ... -> v37 -> the two reset controls merged into one -> v38
    -> no markdown document carries authority -> v39 successor

## The ruling, and what it became

| ruling | what was built |
|---|---|
| No markdown document carries authority | Eight documents corrected against production, not five: an uncapped sweep added `COPY_GLOSSARY.md`, `README.md` and `BACKEND_CHANGES_NEEDED.md` to Run 58's inventory of five. |
| The five code citations of the superseded rule | **Dropped in all five**, the reason stated directly. `research_export.py` cited it by number as "rule 6"; `portfolio_health.py` cited "NAMING_AUTHORITY section 4", which is the section that RECORDED THE REVERSAL. Established by execution that no test reads any of those comment strings. |
| The registered count | `MODULE_RETIREMENT_DECISIONS.md` said the REGISTERED count fell 101 to 63. It is the IN-SERVICE count that fell. Corrected. |
| The count floats | `GROUP_ASSIGNMENT.md` and `p0-baseline/MODULE_TAXONOMY.md` now mark their figures as the figure at a date. **No new number was invented.** |
| The specification floats | Its CONTROLLING designation is withdrawn from `production_tree.py` and the read-first order from `WORKER_BRIEF.md`. It is NOT deleted, NOT renamed and NOT removed from the authority tree, whose manifest sha256 is unmoved for a fifth run. |
| No check may assert a markdown document's content | Four guards **re-pointed** at production oracles, each proved still able to fail BY BREAKING PRODUCTION. Fifteen checks **retired the way modules were retired**: they stop running, their bodies are not deleted, the reason is recorded. Two **stopped**, because re-pointing them would have meant inventing an oracle. **No check was deleted.** |

## What a participant reads and clicks, before and after

**Identical.** One file a participant loads moved, `assets/js/decision-ui.js`, and it is
sequence-bearing, so this link carries a **named exception of record** in
`V23_TO_V24_SEQUENCE_EXCEPTION` rather than a discovery by checksum. What moved inside it is
proved to be a comment and nothing else: the file is byte-identical to v23 once block comments
are stripped, and `GROUP_NAMES` and `MODULE_NAMES` are byte-identical across the link. The other
four members of `SEQUENCE_BEARING_FILES_FROM_V21` are present and byte-identical, measured.

NO STORED FIGURE MOVED. No formula, band, threshold, calibration, abstention rule or population
moved: voting is still exactly A1.7 and A1.8, 63 modules in service of 101 registered, and the
behaviour digest is RE-DERIVED and unchanged.

## Gate

{len(gate)} blocker classes evaluated, {len(blocked)} blocked. Artifact:
`research/freeze/run59_successor_freeze_gate.csv`.

The v25 to v38 release records are preserved unchanged and still record their own stamps.
"""
    (artifact_out(FREEZE / "RUN59_SUCCESSOR_FREEZE_REPORT.md")).write_text(report, encoding="utf-8")

    print("wrote RUN59_SUCCESSOR_FREEZE_CHECKSUMS.csv:", len(rows), "rows")
    print("wrote RUN59_SUCCESSOR_FREEZE_RECORD.json")
    print("wrote RUN59_SUCCESSOR_FREEZE_REPORT.md")
    print("governed files moved since v32:", moved or "(none)")
    print("release content digest:", release_digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
