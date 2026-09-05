#!/usr/bin/env python3
"""
RUN 57. THE SUCCESSOR FREEZE RELEASE RECORDS.

Writes, beside the v25 and v26 releases and never over either:

  research/freeze/RUN57_SUCCESSOR_FREEZE_RECORD.json
  research/freeze/RUN57_SUCCESSOR_FREEZE_REPORT.md
  research/freeze/RUN57_SUCCESSOR_FREEZE_CHECKSUMS.csv

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
DECLARED_DELETIONS = tuple(PP.V22_TO_V23_DELETED)

#: EXPLICIT COMMIT HASH, never a relative reference: Run 54 wrote its own proofs of absence
#: against HEAD~1 and they decayed silently into false proofs that still passed as later commits
#: walked the reference back.
RUN54_PREDELETION_COMMIT = "e13b4f1"

PREDECESSOR_RECORD = FREEZE / "RUN56_SUCCESSOR_FREEZE_RECORD.json"
PREDECESSOR_CHECKSUMS = FREEZE / "RUN56_SUCCESSOR_FREEZE_CHECKSUMS.csv"
IDENTITY = FREEZE / "run57_freeze_candidate_identity.json"
GATE = FREEZE / "run57_successor_freeze_gate.csv"
BEHAVIOUR = FREEZE / "run57_candidate_behaviour_digest.json"


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
                         "tracked": r["tracked"], "moved_since_v32": "DELETED_BY_RUN57"})
            print(f"  DECLARED DELETION recorded in the manifest, not dropped from it: "
                  f"{r['path']}")
            continue
        h = sha(p)
        if h != r["sha256"]:
            moved.append(r["path"])
        rows.append({"path": r["path"], "sha256": h, "git_object": git_object(p),
                     "tracked": r["tracked"],
                     "moved_since_v32": "YES" if h != r["sha256"] else "no"})
    for extra in ("research/freeze/run57_freeze_candidate_identity.json",
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
                     "tracked": "TRACKED", "moved_since_v32": "ADDED_BY_RUN57"})

    out_sums = FREEZE / "RUN57_SUCCESSOR_FREEZE_CHECKSUMS.csv"
    with out_sums.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["path", "sha256", "git_object", "tracked",
                                           "moved_since_v32"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    release_digest = hashlib.sha256(out_sums.read_text(encoding="utf-8").encode()).hexdigest()

    rec = {
        "release_disposition": "FINAL_FREEZE_ACCEPTED",
        "label": "Opus Gubernatio research instrument, Run-57 successor freeze (sim-2026.08-v38)",
        "created": datetime.date(2026, 8, 24).isoformat(),
        "authority": (
            "THE OWNER'S RULING IN THE RUN 57 ORDER, SECTION 7, CARRIED IN FULL. THE TWO RESET CONTROLS "
            "MERGED INTO ONE, AND THE OTHER REMOVED. THREE participant-visible files moved -- "
            "assets/js/ingest.js, assets/js/detail.js and assets/css/radar.css -- and NOT ONE is "
            "sequence-bearing, so this link carries NO sequence exception and "
            "V22_TO_V23_SEQUENCE_EXCEPTION is an EMPTY tuple that is DECLARED rather than omitted. THE "
            "PROBLEM RUN 56 LEFT ON THE RECORD: the project detail page carried TWO controls that clear "
            "stored signals, .detail-reset and the .pe-reset Run 55 moved onto the page, and Run 56 "
            "measured that NEITHER handler was a superset of the other, so it stopped rather than remove "
            "either. THE OWNER'S RUN 57 RULING MERGES THEM: the survivor does the UNION of both bodies, "
            "and the other is removed -- the only removal that loses no behaviour. RE-MEASURED AT THE "
            "EXPLICIT COMMIT 50dfb40 rather than taken from Run 56's table: Run 56's eleven-behaviour "
            "comparison is reproduced exactly, and a twelfth probe finds a sixth .detail-reset-only "
            "behaviour, LinStore.getCached(, which this link acts on. .pe-reset SURVIVES because every "
            "behaviour unique to .detail-reset is reachable from ingest.js through interfaces that are "
            "ALREADY public -- window.LinResults, window.LIN_PROJECTS, LinStore.getProject and getCached, "
            "and detail.js's exported LinDetail.render -- whereas logEvent() and confirmDestructive(), "
            "unique to .pe-reset, are module-private to ingest.js and would have had to be newly EXPORTED "
            "to build the union in detail.js. Merging into the survivor adds nothing to any module's "
            "public surface and leaves Run 56's confirmation byte-identical and in place. THE MERGED "
            "HANDLER IS ORDERED BY DEPENDENCY, NOT CONCATENATED: server reset first; both caches dropped "
            "before any re-fetch or re-render; LinStore.load() before getProject(id); the awaiting-ingest "
            "mutation after the re-fetch; logEvent() once before the re-renders; and LinDetail.render(id) "
            "LAST because it rebuilds the host that contains the surviving button. THE UNION IS EXACT, "
            "asserted statement by statement against 50dfb40, with two declared adaptations. REMOVED WITH "
            "IT: .detail-reset's markup, its .detail-reset-msg aria-live span, wireReset(), its call "
            "site, and radar.css's now-dead .detail-reset-msg rule -- and that dead-CSS check is REAL "
            "rather than vacuous, because the rule existed at 50dfb40. MEASURED IN A REAL BROWSER ON "
            "THREE PROJECTS, 65/65: BEFORE, two controls that clear stored signals per page; AFTER, "
            "EXACTLY ONE. Exactly one button lost, NONE added or moved, panel order unchanged, the panel "
            "bound to the viewed project and no other. CONFIRMING really calls resetSignals, "
            "LinResults.clear(), LinStore.load(), getProject(), LinDetail.render() and logEvent(), proved "
            "with counting spies, and touches NO other project; CANCELLING makes no call and changes no "
            "state. No window.confirm was introduced. NOTHING IS COMPUTED DIFFERENTLY AND NO STORED "
            "FIGURE MOVED: no formula, band, threshold, calibration, abstention rule or population moved, "
            "voting is still exactly A1.7 and A1.8, 63 modules are in service of 101 registered, and the "
            "behaviour digest is RE-DERIVED and unchanged. THE SUITE POPULATION THIS RELEASE MEASURES IS "
            "203 and is unchanged. PHASE B OF THIS RUN CHANGED THE MINT MACHINERY, NOT THE INSTRUMENT: "
            "the freeze gate's four release pins and its no_self_reference anchor are now DERIVED from "
            "the participant-package chain instead of hand-typed, and build_run37_acceptance.py now "
            "computes what its CANDIDATE constant should read and REFUSES to proceed while it disagrees. "
            "The v22 candidate, its identity, its gate and its release records are preserved unchanged as "
            "the historical evidence for anything computed under v37."),
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
            "sha256 over RUN57_SUCCESSOR_FREEZE_CHECKSUMS.csv, which content-addresses every "
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
        "behavioural_delta_v37_to_v38": [
            "the project detail page carried TWO controls that clear stored signals: "
            ".detail-reset, labelled 'Clear stored signals for this project', and the .pe-reset "
            "labelled 'Reset signals' that Run 55 moved onto the page inside the admin panel. "
            "IT NOW CARRIES EXACTLY ONE. Measured in a rendered browser on three projects: "
            "controls that clear stored signals 2 before, 1 after, and the button lost is "
            "'Clear stored signals for this project' on every one of them",
            "the surviving control does the UNION of both handler bodies. It calls "
            "LinStore.resetSignals, LinSignals.clearCache and LinResults.clear, then "
            "LinStore.load and LinStore.getProject into LIN_PROJECTS, then forces the cached "
            "record to awaiting-ingest, then logEvent once, then LinApp.refresh, "
            "renderPortfolioAdmin and LinDetail.render. Every one of those was observed by a "
            "counting spy in a real browser, not read out of the source",
            "the surviving control still ASKS BEFORE CLEARING, with Run 56's confirmation "
            "unchanged and byte-identical, and cancelling still makes no call and changes no "
            "state",
            "NOTHING ELSE A PARTICIPANT READS IS DIFFERENT. No rendered identifier changed, no "
            "naming sweep was run, and NOT ONE control was added or moved: exactly one button "
            "was lost and the admin panel's control order is unchanged",
            "the portfolio list and the portfolio row are UNCHANGED"
        ],
        "behavioural_delta_scope_statement": (
            "Exactly these five, and every one of them is a CONTROL OR ITS DISPLAYED TEXT. NO STORED "
            "FIGURE MOVED and nothing is derived into storage. No formula, band, threshold, calibration, "
            "abstention rule or population moved: voting is still exactly A1.7 and A1.8, 63 modules in "
            "service of 101 registered, and the behaviour digest is RE-DERIVED and unchanged. EXACTLY ONE "
            "user-facing control was REMOVED and it is the one the owner's ruling names; none was added "
            "and none was moved, measured live in a browser on three projects before and after. The "
            "removal was made safe by MERGING FIRST: the survivor was given the union of both handler "
            "bodies and the union was asserted statement by statement against the explicit commit 50dfb40 "
            "before the other control was removed, so no behaviour was lost with it."),
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
    (artifact_out(FREEZE / "RUN57_SUCCESSOR_FREEZE_RECORD.json")).write_text(
        json.dumps(rec, indent=2) + "\n", encoding="utf-8")

    report = f"""# Run-57 successor freeze report

**Disposition: FINAL_FREEZE_ACCEPTED** for `sim-2026.08-v38`.

## Why there is a successor at all

A user-facing control was removed from a page a participant works on, and the control that
survives it now does the work of both. What a participant READS AND CLICKS is part of the frozen
candidate, so v37 is **superseded, not amended**.

    v25 accepted freeze -> S1/S2 -> v26 -> mechanism repair -> v27 -> retirement -> v28
    -> render repairs -> v29 -> retrieval by field kind -> v30 -> the EVM consistency check
    -> v31 -> the current period and the live naming instances -> v32
    -> the completion of the naming correction -> v33
    -> the delivery of the six rulings Run 50 stopped on -> v34
    -> one dead control removed and one name across the wire -> v35
    -> the deep-dive deletion, Manage navigating, and the six admin controls moved -> v36
    -> one duplicate control removed and two confirmations added -> v37
    -> the two reset controls MERGED into one -> v38 successor

## The ruling, and what it became

| ruling | what was built |
|---|---|
| Merge the two reset handler bodies into one control that does the union, then remove the other | **Carried in full.** Run 56 stopped this removal because NEITHER handler was a superset of the other, so removing either alone would have lost behaviour. Run 57 removes that objection rather than overruling it: the survivor is given the UNION first. Both bodies were RE-MEASURED at the explicit commit `50dfb40` rather than taken from Run 56's table -- Run 56's eleven-behaviour comparison reproduces exactly, and a twelfth probe finds a sixth `.detail-reset`-only behaviour, `LinStore.getCached(`, which this release acts on. |
| Which selector survives | **`.pe-reset`**, and the reason is stated rather than picked silently: every behaviour unique to `.detail-reset` is reachable from `ingest.js` through interfaces that are ALREADY public (`window.LinResults`, `window.LIN_PROJECTS`, `LinStore.getProject`/`getCached`, and `detail.js`'s exported `LinDetail.render`), whereas `logEvent()` and `confirmDestructive()` -- unique to `.pe-reset` -- are module-private to `ingest.js` and would have had to be newly EXPORTED to build the union inside `detail.js`. Merging into the survivor adds nothing to any module's public surface, and it leaves Run 56's confirmation byte-identical and in place. |
| The order of the merged handler | **By dependency, not by concatenation.** Server reset first; both caches dropped before any re-fetch or re-render; `LinStore.load()` before `getProject(id)` so the store-wide reload cannot overwrite the record just fetched; the awaiting-ingest mutation after the re-fetch; `logEvent()` once before the re-renders; `LinDetail.render(id)` LAST, because it rebuilds the host that contains the surviving button. |
| What went with the removal | `.detail-reset`'s markup, its `.detail-reset-msg` aria-live span, `wireReset()`, `wireReset`'s call site in `render()`, and `radar.css`'s now-dead `.detail-reset-msg` rule. **That dead-CSS check is a real one and not a vacuous one**, because the rule existed at `50dfb40`. |

## What a participant reads and clicks, before and after

Measured in real Chromium on three projects: **BEFORE, each detail page carried TWO controls that
clear stored signals; AFTER, exactly ONE.** Exactly one button was lost -- "Clear stored signals
for this project" -- and NONE was added or moved. The admin panel's control order is unchanged and
its panel is bound to the viewed project and no other. Confirming really calls `resetSignals`,
`LinResults.clear()`, `LinStore.load()`, `getProject()`, `LinDetail.render()` and `logEvent()`,
proved with counting spies rather than by reading, and touches no other project; cancelling makes
no call and changes no state.

Three files a participant loads moved: `assets/js/ingest.js`, `assets/js/detail.js` and
`assets/css/radar.css`. Not one is sequence-bearing, so this link carries **no sequence
exception**, and that is DECLARED as an empty tuple rather than left as a silence. All five
members of `SEQUENCE_BEARING_FILES_FROM_V21` are present and byte for byte identical to v22,
measured.

NO STORED FIGURE MOVED. No formula, band, threshold, calibration, abstention rule or population
moved: voting is still exactly A1.7 and A1.8, 63 modules in service of 101 registered, and the
behaviour digest is RE-DERIVED and unchanged.

## Gate

{len(gate)} blocker classes evaluated, {len(blocked)} blocked. Artifact:
`research/freeze/run57_successor_freeze_gate.csv`.

The v25 to v37 release records are preserved unchanged and still record their own stamps.
"""
    (artifact_out(FREEZE / "RUN57_SUCCESSOR_FREEZE_REPORT.md")).write_text(report, encoding="utf-8")

    print("wrote RUN57_SUCCESSOR_FREEZE_CHECKSUMS.csv:", len(rows), "rows")
    print("wrote RUN57_SUCCESSOR_FREEZE_RECORD.json")
    print("wrote RUN57_SUCCESSOR_FREEZE_REPORT.md")
    print("governed files moved since v32:", moved or "(none)")
    print("release content digest:", release_digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
