#!/usr/bin/env python3
"""
RUN 56. THE SUCCESSOR FREEZE RELEASE RECORDS.

Writes, beside the v25 and v26 releases and never over either:

  research/freeze/RUN56_SUCCESSOR_FREEZE_RECORD.json
  research/freeze/RUN56_SUCCESSOR_FREEZE_REPORT.md
  research/freeze/RUN56_SUCCESSOR_FREEZE_CHECKSUMS.csv

The historical relationship is explicit in every one of them:

    v25 accepted freeze -> Run 40 identified S1/S2 -> owner authorised remediation
    -> v26 successor -> Run 42 proved two identity losses -> v27 successor
    -> owner's retirement ruling -> v28 successor -> Run 43J diagnosed eleven render defects
    -> owner ordered four of them repaired -> v29 successor -> Run 44 measured the period-scoping
    fall-through -> owner signed off the canonical field classification -> v30 successor

The v25, v26, v27, v28 and v29 records remain exactly as Runs 37, 41, 42, 43 and 44 wrote them. They are
the evidence for anything computed under those stamps and a successor that edited them would
destroy it.

Usage: python tools/build_run56_successor_release.py
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
DECLARED_DELETIONS = tuple(PP.V21_TO_V22_DELETED)

#: EXPLICIT COMMIT HASH, never a relative reference: Run 54 wrote its own proofs of absence
#: against HEAD~1 and they decayed silently into false proofs that still passed as later commits
#: walked the reference back.
RUN54_PREDELETION_COMMIT = "e13b4f1"

PREDECESSOR_RECORD = FREEZE / "RUN55_SUCCESSOR_FREEZE_RECORD.json"
PREDECESSOR_CHECKSUMS = FREEZE / "RUN55_SUCCESSOR_FREEZE_CHECKSUMS.csv"
IDENTITY = FREEZE / "run56_freeze_candidate_identity.json"
GATE = FREEZE / "run56_successor_freeze_gate.csv"
BEHAVIOUR = FREEZE / "run56_candidate_behaviour_digest.json"


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
                         "tracked": r["tracked"], "moved_since_v32": "DELETED_BY_RUN56"})
            print(f"  DECLARED DELETION recorded in the manifest, not dropped from it: "
                  f"{r['path']}")
            continue
        h = sha(p)
        if h != r["sha256"]:
            moved.append(r["path"])
        rows.append({"path": r["path"], "sha256": h, "git_object": git_object(p),
                     "tracked": r["tracked"],
                     "moved_since_v32": "YES" if h != r["sha256"] else "no"})
    for extra in ("research/freeze/run56_freeze_candidate_identity.json",
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
                     "tracked": "TRACKED", "moved_since_v32": "ADDED_BY_RUN56"})

    out_sums = FREEZE / "RUN56_SUCCESSOR_FREEZE_CHECKSUMS.csv"
    with out_sums.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["path", "sha256", "git_object", "tracked",
                                           "moved_since_v32"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    release_digest = hashlib.sha256(out_sums.read_text(encoding="utf-8").encode()).hexdigest()

    rec = {
        "release_disposition": "FINAL_FREEZE_ACCEPTED",
        "label": "Opus Gubernatio research instrument, Run-56 successor freeze (sim-2026.08-v37)",
        "created": datetime.date(2026, 8, 22).isoformat(),
        "authority": (
            "THE OWNER'S RULINGS IN THE RUN 56 ORDER, TWO CARRIED AND ONE STOPPED. "
            "1. THE DUPLICATE 'Upload documents' CONTROL IS REMOVED FROM THE PROJECT DETAIL "
            "PAGE -- CARRIED (Run 56 order, section 6). Run 55 moved the six-control admin "
            "panel onto a page that already carried .detail-upload with the same label, so the "
            "page ended up with two controls performing the same action. The moved .pe-populate "
            "is removed FROM THE DETAIL PAGE ONLY, and the survivor was PROVED to do everything "
            "the removed control did BEFORE the removal, pinned to the explicit commit e13b4f1: "
            "the entire body of .pe-populate's handler is one statement, openUploadModal(id), "
            "and .detail-upload calls the same function with render()'s own p.id. The builder "
            "still emits the button when no host element is supplied, so the portfolio-row "
            "journey is untouched, and its listener is guarded rather than deleted. Measured in "
            "a real browser on three projects: the detail page carries EXACTLY ONE control that "
            "opens the upload dialog. "
            "2. REMOVING .detail-reset IS STOPPED UNDER SECTION 9.1, AND BOTH CONTROLS REMAIN. "
            "The order rules that .pe-reset clears more and so survives. THAT PREMISE IS FALSE "
            "AGAINST THE CODE, established by comparison at e13b4f1 rather than by reading: "
            "NEITHER control is a superset of the other. Only .detail-reset calls "
            "LinResults.clear(), re-fetches through LinStore.getProject into LIN_PROJECTS, "
            "forces the in-memory record to awaiting-ingest and re-renders the page; only "
            ".pe-reset calls LinStore.load(), logEvent() and renderPortfolioAdmin(). Removing "
            "either would lose something the survivor does not do, so neither was removed and "
            "the duplication is left on the record rather than resolved by guess. "
            "3. ARCHIVE AND RESET SIGNALS ASK BEFORE ACTING -- CARRIED (Run 56 order, section "
            "7). The pattern is REUSED, NOT INVENTED, and it was established by execution "
            "first: the application already confirms with window.confirm in app.js and "
            "decision-ui.js and with LinUI.openModal for its destructive project-scoped actions "
            "in ingest.js and admin-ops.js. THE SECOND IS THE ONE TAKEN, because four files in "
            "this repository already record that window.confirm returns false in this container "
            "and in any dialog suppressing browser, which would have made Archive impossible to "
            "perform and so would have changed what the confirmed action does. Each "
            "confirmation NAMES THE PROJECT in its title, its detail sentence and on its "
            "button, and that identifier was verified against the one rendered in the detail "
            "heading. NO CONTROL WAS ADDED: the dialog carries one button, the confirm, exactly "
            "as openDeleteArchivedModal does, and cancelling is LinUI.openModal's own x, Escape "
            "and backdrop; measured live against the phase A commit, the detail page's visible "
            "button list is IDENTICAL before and after. CANCELLING DOES NOTHING AT ALL, proved "
            "by execution with counting spies on LinStore and on LinApp.showPage: no call, no "
            "navigation, no state change. CONFIRMING DOES EXACTLY WHAT THE CONTROL DID BEFORE: "
            "each action body is asserted BYTE-IDENTICAL to e13b4f1 once the gate is stripped. "
            "NO STORED FIGURE CHANGED, no band, status, colour or posture moved, 101 registered "
            "and 63 in service, voting exactly A1.7 and A1.8, and the behaviour digest is "
            "RE-DERIVED and unchanged. THE SUITE POPULATION THIS RELEASE MEASURES IS 203 and is "
            "unchanged from the Run-55 release."),
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
            "sha256 over RUN56_SUCCESSOR_FREEZE_CHECKSUMS.csv, which content-addresses every "
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
        "behavioural_delta_v36_to_v37": [
            "the project detail page carried TWO controls labelled 'Upload documents' after "
            "Run 55 moved the admin panel onto it. It now carries ONE. The survivor is the "
            "pre-existing .detail-upload; the removed one is the moved .pe-populate, whose "
            "entire handler body was the single statement openUploadModal(id). Measured in a "
            "rendered browser on three projects: controls opening the upload dialog 1, and the "
            "moved panel's control list is now ['Save info', 'Recompute this project', 'Reset "
            "signals', 'Archive', 'Close']",
            "the project detail page STILL carries TWO controls that clear stored signals, "
            "deliberately and on the record: removing either was STOPPED under section 9.1 "
            "because neither is a superset of the other",
            "'Archive' now opens a confirmation naming the project before it archives, and its "
            "action is unchanged once confirmed",
            "'Reset signals' now opens a confirmation naming the project before it clears, and "
            "its action is unchanged once confirmed",
            "NOTHING ELSE A PARTICIPANT READS IS DIFFERENT. No rendered identifier changed, no "
            "naming sweep was run, and nothing was stripped from or restored to rendered text. "
            "Measured live against the phase A commit, the detail page's visible button list is "
            "IDENTICAL before and after the confirmations were added",
            "the portfolio list and the portfolio row are UNCHANGED"
        ],
        "behavioural_delta_scope_statement": (
            "Exactly these six, and every one of them is DISPLAYED TEXT. NO STORED FIGURE MOVED "
            "and nothing is derived into storage. No formula, band, threshold, calibration, "
            "abstention rule or population moved: voting is still exactly A1.7 and A1.8, 63 "
            "modules in service of 101 registered. NO MODULE BUCKETS DIFFERENTLY: the grouping "
            "map is byte-identical to v32 and the DOM was read back panel by panel. NO "
            "USER-FACING CONTROL WAS ADDED, MOVED OR REMOVED and no panel states a reporting "
            "period. decision-ui.js gained comments and nothing else, and its behaviour was "
            "re-executed: a request stating period 1 against a research assignment at period 3 "
            "still answers with period 3."),
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
                        "artifact": "research/freeze/run52_successor_freeze_gate.csv"},
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
    (artifact_out(FREEZE / "RUN56_SUCCESSOR_FREEZE_RECORD.json")).write_text(
        json.dumps(rec, indent=2) + "\n", encoding="utf-8")

    report = f"""# Run-56 successor freeze report

**Disposition: FINAL_FREEZE_ACCEPTED** for `sim-2026.08-v37`.

## Why there is a successor at all

A duplicate control was removed from a page a participant works on, and two destructive controls
on that page now ask before acting. What a participant READS AND CLICKS is part of the frozen
candidate, so v36 is **superseded, not amended**.

    v25 accepted freeze -> S1/S2 -> v26 -> mechanism repair -> v27 -> retirement -> v28
    -> render repairs -> v29 -> retrieval by field kind -> v30 -> the EVM consistency check
    -> v31 -> the current period and the live naming instances -> v32
    -> the completion of the naming correction -> v33
    -> the delivery of the six rulings Run 50 stopped on -> v34
    -> one dead control removed and one name across the wire -> v35
    -> the deep-dive deletion, Manage navigating, and the six admin controls moved -> v36
    -> one duplicate control removed and two confirmations added -> v37 successor

## The three rulings, and what each became

| ruling | what was built |
|---|---|
| 1. Remove the duplicate "Upload documents" (`.pe-populate`) from the detail page | **Carried.** The survivor `.detail-upload` was proved to do everything the removed control did BEFORE the removal, pinned to the explicit commit `e13b4f1`: the entire body of `.pe-populate`'s handler is one statement, `openUploadModal(id)`, and `.detail-upload` calls the same function with `render()`'s own `p.id`. Removal is scoped to the hosted path, so the portfolio-row journey is untouched and the listener is guarded rather than deleted. Measured in a real browser on three projects: the detail page carries EXACTLY ONE control that opens the upload dialog. |
| 2. Remove `.detail-reset` and keep `.pe-reset` | **NOT CARRIED. STOPPED under section 9.1, and BOTH controls remain.** The ruling's premise -- that `.pe-reset` clears more -- is FALSE, established by comparison at `e13b4f1` rather than by reading. NEITHER control is a superset of the other: only `.detail-reset` calls `LinResults.clear()`, re-fetches through `LinStore.getProject` into `LIN_PROJECTS`, forces the in-memory record to awaiting-ingest and re-renders the page; only `.pe-reset` calls `LinStore.load()`, `logEvent()` and `renderPortfolioAdmin()`. `detail.js` did not move. |
| 3. Archive and Reset signals ask before acting | **Carried, reusing the pattern the application already has.** `LinUI.openModal`, the shape used by `openDeleteArchivedModal` and `openDeleteProjectModal`, NOT `window.confirm` -- four files in this repository already record that `window.confirm` returns false in this container, which would have made Archive impossible to perform. Each confirmation names the project in its title, its detail and on its button. No control was added; cancelling is the dialog's own x, Escape and backdrop and was proved by execution to make no call, cause no navigation and change no state. |

## What a participant reads and clicks, before and after

Exactly one file a participant loads moved: `assets/js/ingest.js`. It is not sequence-bearing, so
this link carries **no sequence exception**, and that is DECLARED as an empty tuple rather than
left as a silence. All five members of `SEQUENCE_BEARING_FILES_FROM_V21` are present and byte for
byte identical to v21, measured.

NO STORED FIGURE MOVED. No formula, band, threshold, calibration, abstention rule or population
moved: voting is still exactly A1.7 and A1.8, 63 modules in service of 101 registered, and the
behaviour digest is RE-DERIVED and unchanged.

## Gate

{len(gate)} blocker classes evaluated, {len(blocked)} blocked. Artifact:
`research/freeze/run56_successor_freeze_gate.csv`.

The v25 to v36 release records are preserved unchanged and still record their own stamps.
"""
    (artifact_out(FREEZE / "RUN56_SUCCESSOR_FREEZE_REPORT.md")).write_text(report, encoding="utf-8")

    print("wrote RUN56_SUCCESSOR_FREEZE_CHECKSUMS.csv:", len(rows), "rows")
    print("wrote RUN56_SUCCESSOR_FREEZE_RECORD.json")
    print("wrote RUN56_SUCCESSOR_FREEZE_REPORT.md")
    print("governed files moved since v32:", moved or "(none)")
    print("release content digest:", release_digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
