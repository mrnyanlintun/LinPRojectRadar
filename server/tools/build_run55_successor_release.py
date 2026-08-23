#!/usr/bin/env python3
"""
RUN 55. THE SUCCESSOR FREEZE RELEASE RECORDS.

Writes, beside the v25 and v26 releases and never over either:

  research/freeze/RUN55_SUCCESSOR_FREEZE_RECORD.json
  research/freeze/RUN55_SUCCESSOR_FREEZE_REPORT.md
  research/freeze/RUN55_SUCCESSOR_FREEZE_CHECKSUMS.csv

The historical relationship is explicit in every one of them:

    v25 accepted freeze -> Run 40 identified S1/S2 -> owner authorised remediation
    -> v26 successor -> Run 42 proved two identity losses -> v27 successor
    -> owner's retirement ruling -> v28 successor -> Run 43J diagnosed eleven render defects
    -> owner ordered four of them repaired -> v29 successor -> Run 44 measured the period-scoping
    fall-through -> owner signed off the canonical field classification -> v30 successor

The v25, v26, v27, v28 and v29 records remain exactly as Runs 37, 41, 42, 43 and 44 wrote them. They are
the evidence for anything computed under those stamps and a successor that edited them would
destroy it.

Usage: python tools/build_run55_successor_release.py
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
DECLARED_DELETIONS = tuple(PP.V20_TO_V21_DELETED)

#: EXPLICIT COMMIT HASH, never a relative reference: Run 54 wrote its own proofs of absence
#: against HEAD~1 and they decayed silently into false proofs that still passed as later commits
#: walked the reference back.
RUN54_PREDELETION_COMMIT = "bf36ef6"

PREDECESSOR_RECORD = FREEZE / "RUN52_SUCCESSOR_FREEZE_RECORD.json"
PREDECESSOR_CHECKSUMS = FREEZE / "RUN52_SUCCESSOR_FREEZE_CHECKSUMS.csv"
IDENTITY = FREEZE / "run55_freeze_candidate_identity.json"
GATE = FREEZE / "run55_successor_freeze_gate.csv"
BEHAVIOUR = FREEZE / "run55_candidate_behaviour_digest.json"


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
                         "tracked": r["tracked"], "moved_since_v32": "DELETED_BY_RUN54"})
            print(f"  DECLARED DELETION recorded in the manifest, not dropped from it: "
                  f"{r['path']}")
            continue
        h = sha(p)
        if h != r["sha256"]:
            moved.append(r["path"])
        rows.append({"path": r["path"], "sha256": h, "git_object": git_object(p),
                     "tracked": r["tracked"],
                     "moved_since_v32": "YES" if h != r["sha256"] else "no"})
    for extra in ("research/freeze/run55_freeze_candidate_identity.json",
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
                     "tracked": "TRACKED", "moved_since_v32": "ADDED_BY_RUN55"})

    out_sums = FREEZE / "RUN55_SUCCESSOR_FREEZE_CHECKSUMS.csv"
    with out_sums.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["path", "sha256", "git_object", "tracked",
                                           "moved_since_v32"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    release_digest = hashlib.sha256(out_sums.read_text(encoding="utf-8").encode()).hexdigest()

    rec = {
        "release_disposition": "FINAL_FREEZE_ACCEPTED",
        "label": "Opus Gubernatio research instrument, Run-55 successor freeze (sim-2026.08-v36)",
        "created": datetime.date(2026, 8, 22).isoformat(),
        "authority": (
            "THE OWNER'S RULINGS CARRIED BY RUN 54 AND COMPLETED BY RUN 55. Run 54 completed "
            "four phases and could mint none of them: the acceptance generator hashed a pinned "
            "candidate identity that still named a file Run 54 had deleted, so gate rows 2 and "
            "3 failed and, correctly, nothing was merged. Run 55 completes the same body of "
            "work and mints it. "
            "1. THE CAMPAIGN LEAK IS GUARDED (Run 54 order, section 6). Run 52 found three "
            "guards in canonical_v8.py replaced by `if False:`, left by a campaign that died "
            "between injecting and restoring, and FIVE consecutive runs certified rather than "
            "caught it, because each next campaign snapshotted the corruption FROM DISK and "
            "its own correct restore cemented it. server/tools/campaign_safety.py adds a "
            "start-AND-end dirty-tree check and pristine-HEAD snapshots; all 39 campaigns are "
            "armed; the suite runner fails a suite that leaves production or client source "
            "dirty. Run 55 completes the `finally` hygiene on the remaining fifteen campaigns "
            "and brings server/tests/ inside the runner, so the campaign most implicated in "
            "the leak now runs inside the pass meant to catch it. "
            "2. THE CLIENT-SIDE DEEP-DIVE SURFACE IS DELETED -- CARRIED. Reached by no route "
            "the service serves; every one of its 78 panels gated on the legacy client-side "
            "blob. assets/js/deepdive.js, research/deepdive.html and the route in "
            "server/app/main.py that served it are gone. The guarantee that no served route "
            "loads a client-side model is now UNCONDITIONAL rather than confined to one route. "
            "3. MANAGE NAVIGATES, OPEN IS REMOVED -- CARRIED, AND THIS REVERSES RUN 52'S STOP "
            "UNDER ITS SECTION 8.1. The order of work was not negotiable and was not "
            "negotiated: Manage was re-bound and MEASURED IN A REAL BROWSER reaching the detail "
            "page of its OWN row's project, per row and per surface, BEFORE Open was removed, "
            "and reachability was re-measured after. No project's detail page was unreachable "
            "at any point. Both guards that enforced the old stop are REVISED, not deleted, "
            "and a third found by sweep with them. "
            "4. THE SIX ADMIN CONTROLS MOVE ONTO THE PROJECT DETAIL PAGE -- CARRIED (Run 55 "
            "order, section 6). Save info, Upload documents, Recompute this project, Reset "
            "signals, Archive and Close were left unreachable when Manage stopped opening the "
            "inline accordion. They are MOVED, not rewritten: the same builder, the same "
            "markup, the same six handlers, a different parent element. Measured in a real "
            "browser on three projects: each renders exactly once on the detail page and acts "
            "on that project and no other. Archive and Reset signals are destructive; both "
            "carried NO confirmation before the move and carry none after it, and their "
            "handler bodies are byte-identical to their pre-move bytes. The four dead "
            "`.li-open` rules in radar.css go with the control they styled. "
            "5. DISPLAYED IDENTIFIERS ARE ACCEPTABLE -- the Run 54 phase D authority revision, "
            "obeyed as the reversal it is. NO NAMING SWEEP WAS RUN; nothing was stripped from "
            "rendered text and nothing was restored. "
            "NO STORED FIGURE CHANGED, no band, status, colour or posture moved, 101 "
            "registered and 63 in service, voting exactly A1.7 and A1.8, and the behaviour "
            "digest is RE-DERIVED and unchanged. THE SUITE POPULATION THIS RELEASE MEASURES "
            "GREW FROM 193 TO 203 because the runner now runs server/tests/ as well as "
            "server/tools/, and every record carrying that figure is reconciled to it."),
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
            "The v25 to v34 releases remain historical evidence and are "
            "not rewritten. Results computed under any of them remain interpretable against "
            "their own records.",
        ],
        "freeze_candidate_commit": ident["candidate_git_commit"],
        "candidate_identity_digest": ident["candidate_identity_digest"],
        "candidate_behaviour_digest": behav["behaviour_digest"],
        "release_content_digest": release_digest,
        "release_content_digest_method": (
            "sha256 over RUN55_SUCCESSOR_FREEZE_CHECKSUMS.csv, which content-addresses every "
            "governed file of the successor instrument. Reproducible from the tree alone."),
        "release_commit_recording_method": pred["release_commit_recording_method"],
        "simulation_version": SIMULATION_VERSION,
        "simulation_version_history": list(SIMULATION_VERSION_HISTORY),
        "participant_package": PP.CURRENT.identifier,
        "participant_package_decision": (
            "SUPERSEDED to og-participant-2026.08-v20. Determined mechanically, not assumed: "
            "SEVEN of the seventy governed files moved -- assets/js/categories.js, "
            "assets/js/deepdive.js, assets/js/detail.js, assets/js/neural_flow.js, "
            "assets/js/projectnet2d.js, assets/js/signals.js and assets/js/taxonomy.js -- and "
            "EXACTLY ONE OF THE SEVEN IS SEQUENCE-BEARING. That exception is DECLARED BY NAME "
            "in participant_packages.py as V19_TO_V20_SEQUENCE_EXCEPTION rather than admitted "
            "by widening the invariant, and the other five sequence-bearing files are byte for "
            "byte identical to v19. What moved inside deepdive.js is the removal of one DEAD "
            "button whose handler called a symbol that does not exist, plus a parameter and a "
            "reader-less DOM attribute renamed to the single module-identifier name; NO "
            "RENDERED TEXT CHANGED. The other six carry ruling 3 and nothing else. "
            "assets/js/app.js is byte for byte identical to v19 because ruling 1 was stopped "
            "under section 8.1. No step of the decision sequence, no reveal gate, no lock, no "
            "randomization and NO REACHABLE USER-FACING CONTROL other than the dead one ruling "
            "2 names was added, moved or removed."),
        "synthetic_package": "OG-SYNTH-0.6",
        "analysis_schema": "og-analysis-2026.08-v1",
        "canonical_field_classification": {
            "identity": 13, "period": 62, "undetermined": 2, "total_emittable": 77,
            "authority": "code_audit/run45_field_classification_proposal.md, and the owner's "
                         "ruling recorded in REPORT_2026-08-22_run45_period_scoping_fix.md",
            "declared_in": "server/app/field_registry.py IDENTITY_FIELDS / PERIOD_FIELDS / "
                           "UNDETERMINED_FIELDS, asserted at import to partition FIELD_KINDS",
        },
        "behavioural_delta_v34_to_v35": [
            "the dead 'see Health' button is gone from the research deep-dive surface. Its "
            "handler called window.LinIngest.openHealthModal(), which exists nowhere in this "
            "repository, so clicking it did nothing; it was a control in appearance only. "
            "Measured in a rendered browser: [data-goto-health] nodes 0, occurrences of the "
            "string 'see Health' 0, deep-dive panels still rendered 64",
            "the anomaly sentence the button sat beside is UNCHANGED and still renders: "
            "'Portfolio Health: no anomaly flagged.'",
            "NOTHING ELSE A PARTICIPANT READS IS DIFFERENT. The module identifier moved to one "
            "name, module_id, on both sides of the wire, but that field is a dispatch key: it "
            "is never rendered. No rendered identifier changed, no naming sweep was run, and "
            "nothing was stripped from or restored to rendered text",
            "the project list is UNCHANGED, deliberately: ruling 1 was stopped under section "
            "8.1 after a browser established that Manage opens an inline accordion under its "
            "own row and that Open is the only route from the list to the project detail page"
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
    (FREEZE / "RUN55_SUCCESSOR_FREEZE_RECORD.json").write_text(
        json.dumps(rec, indent=2) + "\n", encoding="utf-8")

    report = f"""# Run-52 successor freeze report

**Disposition: FINAL_FREEZE_ACCEPTED** for `sim-2026.08-v35`.

## Why there is a successor at all

A dead control was removed from a surface a participant reads, and the module identifier moved
to a single name on both sides of the wire. What a participant READS is part of the frozen
candidate, so v34 is **superseded, not amended**.

    v25 accepted freeze -> S1/S2 -> v26 -> mechanism repair -> v27 -> retirement -> v28
    -> render repairs -> v29 -> retrieval by field kind -> v30 -> the EVM consistency check
    -> v31 -> the current period and the live naming instances -> v32
    -> the completion of the naming correction -> v33
    -> the delivery of the six rulings Run 50 stopped on -> v34
    -> one dead control removed and one name across the wire -> v35 successor

## The four rulings, and what each became

| ruling | what was built |
|---|---|
| 1. Remove the Open button from the project list | **NOT CARRIED. Surface STOPPED under section 8.1.** The ruling's premise -- that Manage and Open lead to the same page -- is FALSE, established by execution in a real browser: Manage opens an inline admin accordion under its own row and never leaves the portfolio page, while Open is the ONLY route from the project list to the project detail page. `app.js` did not move. |
| 2. Remove the dead "see Health" button | Carried. `deepdive.js`: the button and its `[data-goto-health]` handler are gone; the anomaly sentence it sat beside is unchanged and still renders. |
| 3. One name for the module identifier: `module_id` | Carried. `taxonomy_authority.json` (101 module rows), `build_client_taxonomy.py`, both regenerated mirrors (63 rows each), and every client consumer. Two sites STOPPED under 8.2 and named. |
| 4. Identifiers on screen are not touched | Obeyed as the reversal it is. **No naming sweep was run.** Nothing stripped, nothing restored. |

## What changed, and what did not

| Subject | Result |
|---|---|
| Stored figures of any kind | **unchanged** |
| Project status, category statuses, bands, colours, postures | **unchanged** |
| Behaviour digest | **unchanged**, `8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1` |
| Registered / in service / voting | 101 / 63 / exactly A1.7 and A1.8, all identical |
| Rendered identifiers | **unchanged**; no sweep was run |
| Sequence-bearing participant files | **one moved**, `deepdive.js`, with its own named exception record; the other five are byte-identical to v19 |
| User-facing controls | **one removed, and it was dead**: the see-Health button. Nothing else added, moved or removed. |
| Participant package | SUPERSEDED to `og-participant-2026.08-v20` |
| Synthetic package | RETAINED `OG-SYNTH-0.6` |
| Analysis schema | RETAINED `og-analysis-2026.08-v1` |

## Two rename sites recorded STOPPED, rather than forced

`p0-baseline/module_renumbering_map.csv`'s `new_id`/`old_id` column pair is not renamed. It is a
PAIR -- the current identity and the pre-renumbering identity -- not one name for one thing, its
name originates in the header row of a frozen baseline artifact the freeze gate pins, and it has
309 occurrences across more than thirty files. Where the identifier actually crosses the wire --
the stored row, the API response, the export -- it is already `module_id`.

`deepdive.js`'s methods-comparison `num` field is not renamed. It is the ordinal of a METHOD in
that table (09 = the conservative-dominance baseline, 10 = Dempster-Shafer), not a registry
module identifier; calling it `module_id` would assert an identity it does not have.

## Gate

{len(gate)} blocker classes evaluated, {len(blocked)} blocked. Artifact:
`research/freeze/run52_successor_freeze_gate.csv`.

The v25 to v34 release records are preserved unchanged and still record their own stamps.
"""
    (FREEZE / "RUN55_SUCCESSOR_FREEZE_REPORT.md").write_text(report, encoding="utf-8")

    print("wrote RUN55_SUCCESSOR_FREEZE_CHECKSUMS.csv:", len(rows), "rows")
    print("wrote RUN55_SUCCESSOR_FREEZE_RECORD.json")
    print("wrote RUN55_SUCCESSOR_FREEZE_REPORT.md")
    print("governed files moved since v32:", moved or "(none)")
    print("release content digest:", release_digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
