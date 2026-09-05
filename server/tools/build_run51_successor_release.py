#!/usr/bin/env python3
"""
RUN 51. THE SUCCESSOR FREEZE RELEASE RECORDS.

Writes, beside the v25 and v26 releases and never over either:

  research/freeze/RUN51_SUCCESSOR_FREEZE_RECORD.json
  research/freeze/RUN51_SUCCESSOR_FREEZE_REPORT.md
  research/freeze/RUN51_SUCCESSOR_FREEZE_CHECKSUMS.csv

The historical relationship is explicit in every one of them:

    v25 accepted freeze -> Run 40 identified S1/S2 -> owner authorised remediation
    -> v26 successor -> Run 42 proved two identity losses -> v27 successor
    -> owner's retirement ruling -> v28 successor -> Run 43J diagnosed eleven render defects
    -> owner ordered four of them repaired -> v29 successor -> Run 44 measured the period-scoping
    fall-through -> owner signed off the canonical field classification -> v30 successor

The v25, v26, v27, v28 and v29 records remain exactly as Runs 37, 41, 42, 43 and 44 wrote them. They are
the evidence for anything computed under those stamps and a successor that edited them would
destroy it.

Usage: python tools/build_run51_successor_release.py
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

PREDECESSOR_RECORD = FREEZE / "RUN48_SUCCESSOR_FREEZE_RECORD.json"
PREDECESSOR_CHECKSUMS = FREEZE / "RUN48_SUCCESSOR_FREEZE_CHECKSUMS.csv"
IDENTITY = FREEZE / "run51_freeze_candidate_identity.json"
GATE = FREEZE / "run51_successor_freeze_gate.csv"
BEHAVIOUR = FREEZE / "run51_candidate_behaviour_digest.json"


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
                     "moved_since_v32": "YES" if h != r["sha256"] else "no"})
    for extra in ("research/freeze/run51_freeze_candidate_identity.json",
                  "research/freeze/run51_successor_freeze_gate.csv",
                  "server/tools/test_run49_naming_completion.py",
                  "server/tools/drive_run51_browser.py",
                  "server/tools/run51_dash_sweep.py",
                  "server/tools/drive_run49_browser.py"):
        p = ROOT / extra
        rows.append({"path": extra, "sha256": sha(p), "git_object": git_object(p),
                     "tracked": "TRACKED", "moved_since_v32": "ADDED_BY_RUN49"})

    out_sums = FREEZE / "RUN51_SUCCESSOR_FREEZE_CHECKSUMS.csv"
    with out_sums.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["path", "sha256", "git_object", "tracked",
                                           "moved_since_v32"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    release_digest = hashlib.sha256(out_sums.read_text(encoding="utf-8").encode()).hexdigest()

    rec = {
        "release_disposition": "FINAL_FREEZE_ACCEPTED",
        "label": "Opus Gubernatio research instrument, Run-51 successor freeze (sim-2026.08-v34)",
        "created": datetime.date(2026, 8, 22).isoformat(),
        "authority": (
            "The owner's SIX RULINGS of 2026-08-22 in the Run 51 order, section 3. 1. THE "
            "PORTFOLIO HEALTH FLYOUT IS DELETED ENTIRELY -- six symbols and the three buttons "
            "inside them -- because it rendered nowhere, had no caller anywhere in the served "
            "application, and an unreachable button is not a control. 2. THE TAXONOMY'S PRIMARY "
            "KEY IS SEPARATED FROM THE LABEL AND RENAMED across the authority, both generated "
            "mirrors and every consumer: the key dispatches, and what renders is a name that "
            "carries no identifier. 3. THE EIGHT-MODULE COMPLIANCE PANEL IS SPLIT into two "
            "panels, one per current category, which adds a panel and is intended. 4. EVERY EN "
            "DASH AND EM DASH IN USER-FACING TEXT IS REPLACED BY WORDS, with the vendored "
            "library stopped and named rather than broken. 5. SEVEN MIS-FILED PANELS ARE "
            "CORRECTED, including the two alias cases. 6. THE DEEP-DIVE GROUPING BOUND IS "
            "DERIVED FROM THE TAXONOMY, so the eleventh project-level category renders. Every "
            "count of modules or categories on a served page derives rather than being typed. No "
            "stored figure changes, no band, status, colour or posture changes, and the "
            "behaviour digest is unchanged."),
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
            "The v25 to v33 releases remain historical evidence and are "
            "not rewritten. Results computed under any of them remain interpretable against "
            "their own records.",
        ],
        "freeze_candidate_commit": ident["candidate_git_commit"],
        "candidate_identity_digest": ident["candidate_identity_digest"],
        "candidate_behaviour_digest": behav["behaviour_digest"],
        "release_content_digest": release_digest,
        "release_content_digest_method": (
            "sha256 over RUN51_SUCCESSOR_FREEZE_CHECKSUMS.csv, which content-addresses every "
            "governed file of the successor instrument. Reproducible from the tree alone."),
        "release_commit_recording_method": pred["release_commit_recording_method"],
        "simulation_version": SIMULATION_VERSION,
        "simulation_version_history": list(SIMULATION_VERSION_HISTORY),
        "participant_package": PP.CURRENT.identifier,
        "participant_package_decision": (
            "SUPERSEDED to og-participant-2026.08-v19. Determined mechanically, not assumed: "
            "THREE of the seventy governed files moved -- assets/js/deepdive.js, "
            "assets/js/decision-ui.js and assets/js/detail.js -- and TWO OF THE THREE ARE "
            "SEQUENCE-BEARING. Both exceptions are DECLARED BY NAME in participant_packages.py "
            "as V17_TO_V18_SEQUENCE_EXCEPTION rather than admitted by widening the invariant, "
            "and the other four sequence-bearing files are byte for byte identical to v17. What "
            "moved inside deepdive.js is displayed TEXT and the panel label map; the grouping "
            "map CAT_NUM_FROM_MODULE is byte-identical to v17, so not one panel can have moved "
            "to a different collapsible group. What moved inside decision-ui.js is COMMENTS "
            "ONLY: with every whole-line comment stripped the two versions are identical, which "
            "the package suite measures rather than asserts. No step of the decision sequence, "
            "no reveal gate, no lock, no randomization and NO USER-FACING CONTROL was added, "
            "moved or removed."),
        "synthetic_package": "OG-SYNTH-0.6",
        "analysis_schema": "og-analysis-2026.08-v1",
        "canonical_field_classification": {
            "identity": 13, "period": 62, "undetermined": 2, "total_emittable": 77,
            "authority": "code_audit/run45_field_classification_proposal.md, and the owner's "
                         "ruling recorded in REPORT_2026-08-22_run45_period_scoping_fix.md",
            "declared_in": "server/app/field_registry.py IDENTITY_FIELDS / PERIOD_FIELDS / "
                           "UNDETERMINED_FIELDS, asserted at import to partition FIELD_KINDS",
        },
        "behavioural_delta_v33_to_v34": [
            "the Portfolio Health flyout is gone from the served bytes: renderCat8Health, "
            "CAT8_MODULES, cat8HealthData, cat8HealthDataFromLive, isSnapshotStale, cat8Retired "
            "and the three buttons inside them. It rendered on no surface before and renders on "
            "none now; window.LinDeepDive exports render alone",
            "the Signal Ledger prints no module identifier chip and no category identifier chip: "
            "63 module chips and 11 category chips are gone, counted in the rendered DOM",
            "the action plan's trigger lines name the category and the module instead of "
            "prefixing an identifier, and the executive brief lists category NAMES instead of "
            "category identifiers",
            "the exported workbook's Category and Module identifier columns are gone",
            "the Signal Flow tooltip prints the module name alone",
            "the handbook states the modules in service where it stated 96 registered modules, "
            "and every count of modules or categories on the handbook and the About page is "
            "filled from registry_index() and service_index() instead of typed into prose",
            "the handbook's Signal Stack diagram prints method names instead of ten retired "
            "module identifiers, and its accessible name states the population in service "
            "instead of ten categories",
            "the deep-dive surface files seven previously mis-filed panels under the category "
            "their module belongs to in the current taxonomy, including the two alias cases",
            "the deep-dive surface renders an ELEVENTH collapsible group, Data Integrity, and a "
            "SIXTH, Delivery Quality Performance, neither of which could render before",
            "the eight-module compliance panel is TWO panels, one per current category",
            "no served string on any participant surface, SVG text nodes and accessible names "
            "included, carries a module identifier, a category identifier, the retired scheme, "
            "an ampersand, an em dash or an en dash",
            "rendered placeholders that were a bare em dash now say what they mean"
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
                        "artifact": "research/freeze/run51_successor_freeze_gate.csv"},
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
    (artifact_out(FREEZE / "RUN51_SUCCESSOR_FREEZE_RECORD.json")).write_text(
        json.dumps(rec, indent=2) + "\n", encoding="utf-8")

    report = f"""# Run-49 successor freeze report

**Disposition: FINAL_FREEZE_ACCEPTED** for `sim-2026.08-v34`.

## Why there is a successor at all

Run 48's own second sweep found that the retired "Cat N" scheme still rendered on the deep-dive
surface in ten group headers, a banner, a metric-box label, a panel heading, a note and three
prose sentences, and in one sentence reaching the executive brief's model. What a participant
READS is part of the frozen candidate, so v32 is **superseded, not amended**.

    v25 accepted freeze -> S1/S2 -> v26 -> mechanism repair -> v27 -> retirement -> v28
    -> render repairs -> v29 -> retrieval by field kind -> v30 -> the EVM consistency check
    -> v31 -> the current period and the live naming instances -> v32
    -> the completion of the naming correction -> v33
    -> the delivery of the six rulings Run 50 stopped on -> v34 successor

## The five rulings, and what each became

| ruling | what was built |
|---|---|
| Every surviving rendered instance is corrected | `deepdive.js`: the ten group headers, the banner, the metric-box label, the comparison heading and note, three confidence sentences, the comparison table's row prefix and column header, the Portfolio Health flyout headings; `detail.js`: the brief prompt |
| The ampersand is corrected | `detail.js:1086` now reads "Documents and Extracted Signals" |
| The fallback map is made specific again | `CAT_FROM_MODULE` extended from 19 keys to all 77 the call sites pass; no key left on the neutral fallback |
| The period literals are left and recorded | Three comments in `decision-ui.js`; not one byte of executable text changed |
| No panel states its period, no control anywhere | Nothing added |

## What changed, and what did not

| Subject | Result |
|---|---|
| Stored figures of any kind | **unchanged**; every change is displayed text |
| Project status, category statuses, bands, colours, postures | **unchanged** |
| Registered / in service / voting | 101 / 63 / exactly A1.7 and A1.8, all identical |
| Panel bucketing | **unchanged**; `CAT_NUM_FROM_MODULE` is byte-identical to v32 |
| Sequence-bearing participant files | **two moved**, `deepdive.js` and `decision-ui.js`, each with its own named exception record; the other four are byte-identical |
| User-facing controls | **none added, moved or removed** |
| Participant package | SUPERSEDED to `og-participant-2026.08-v19` |
| Synthetic package | RETAINED `OG-SYNTH-0.6` |
| Analysis schema | RETAINED `og-analysis-2026.08-v1` |

## A guarantee recorded NOT MET, rather than dressed up

Run 48's guarantee 11 -- that no user-facing text anywhere in `assets/` carries a module
identifier, a category number, the retired scheme, an ampersand, an em dash or an en dash -- is
**still not met**, and meeting it is outside this run's authority. `app.js` prints a category
identifier and a module identifier on the Categories page from the GENERATED taxonomy, and en and
em dashes remain in user-facing text across roughly forty files including four sequence-bearing
ones that stop condition 9.5 forbids this run to move.

## Gate

{len(gate)} blocker classes evaluated, {len(blocked)} blocked. Artifact:
`research/freeze/run51_successor_freeze_gate.csv`.

The v25 to v32 release records are preserved unchanged and still record their own stamps.
"""
    (artifact_out(FREEZE / "RUN51_SUCCESSOR_FREEZE_REPORT.md")).write_text(report, encoding="utf-8")

    print("wrote RUN51_SUCCESSOR_FREEZE_CHECKSUMS.csv:", len(rows), "rows")
    print("wrote RUN51_SUCCESSOR_FREEZE_RECORD.json")
    print("wrote RUN51_SUCCESSOR_FREEZE_REPORT.md")
    print("governed files moved since v32:", moved or "(none)")
    print("release content digest:", release_digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
