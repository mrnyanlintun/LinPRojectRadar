#!/usr/bin/env python3
"""
RUN 39 SECTION 20. FROZEN-INSTRUMENT IMMUTABILITY, PROVED BY DIFF RATHER THAN ASSERTED.

Run 39 is an operational gate. It may add launch controls, documentation, validators and audit
artifacts, and it may not move a single frozen byte. This gate asks git for the actual difference
between the tree and the accepted freeze, mechanically, and fails naming every path that moved.

TWO REFERENCES, TWO QUESTIONS -- the same distinction the Run-38 gate had to learn.

  "Has a frozen byte moved?" is asked of the WORKING TREE, because an uncommitted edit to a
  frozen surface must be caught too. This is what the fault campaign's faults 2 and 3 exercise.

  "What did this run change?" is asked of COMMITTED history, because several suites in this
  repository legitimately rewrite their own audit CSVs during a run and those rewrites are
  restored rather than committed. Measured against the working tree, the answer would depend on
  which other suites happened to run first, which is an order-dependent oracle and therefore not
  an oracle at all.

Run:
    PYTHONIOENCODING=utf-8 python tools/test_run39_frozen_immutability.py
"""
from __future__ import annotations

import csv
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
CANDIDATE = "6142d877856ea651ef8d7e905f6d27604b3244f1"
RELEASE = "f983bb020f7a184a5742e1fff09d690b0170f0de"
RUN38_READY = "dd2e355b55008fe08f440c8a9e87378db98ad399"
MANIFEST = ROOT / "research" / "freeze" / "INSTRUMENT_FINAL_FREEZE_CHECKSUMS.csv"

#: The freeze-critical surfaces section 20 names, taken wholesale so a NEW file added to any of
#: them is caught as well as an edit to an existing one.
SURFACES = (
    "server/app",                                    # the production server application
    "assets",                                        # the participant/client assets
    "index.html",                                    # the served page
    "research_fixtures/synthetic",                   # the controlled stimuli
    "research/methodology/PCEIF_100_MODULE_SUPERVISORY_METHOD_SPECIFICATION_v1.md",
    "research/methodology/controlled_study_design_contract.json",   # participant sequence authority
)

results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   {detail}" if detail and not ok else ""))


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=str(ROOT), capture_output=True,
                          text=True).stdout


def diff_committed(ref: str, *paths: str) -> str:
    return git("diff", "--name-status", ref, "HEAD", "--", *paths).strip()


def diff_worktree(ref: str, *paths: str) -> str:
    return git("diff", "--name-status", ref, "--", *paths).strip()


for ref, name in ((CANDIDATE, "freeze candidate"), (RELEASE, "accepted release"),
                  (RUN38_READY, "Run-38 readiness commit")):
    check(git("cat-file", "-t", ref).strip() == "commit",
          f"the {name} {ref[:12]} is present in this repository")

# ---- surface 1: the freeze-critical surfaces, WORKING TREE, against the candidate.
changed_surfaces: list[str] = []
for surface in SURFACES:
    out = diff_worktree(CANDIDATE, surface)
    if out:
        changed_surfaces.extend(out.splitlines())
# RESTATED BY RUN 41, RUN 39'S FINDING PRESERVED. This asserted byte-identity with the v25
# freeze candidate, which was correct for Run 39 and remains true of everything Run 39 did. Run 40
# then confirmed two HIGH defects and the OWNER RULED that both be fixed before participant use,
# making Run 41 an authorised freeze SUCCESSOR rather than a violation. The guard is made exact
# rather than relaxed: the frozen surfaces may differ from the v25 candidate ONLY by the files
# Run 41 was authorised to change, NAMED here so the set cannot quietly grow.
RUN41_AUTHORISED_SUCCESSOR_CHANGES = {
    "server/app/main.py",                    # finding S1: the document-serving boundary
    "server/app/simulation/models.py",       # the stamp advances to sim-2026.08-v26, then v27
}

# RESTATED BY RUN 42, AND THE SAME DISCIPLINE AGAIN. Run 42 traced the background
# data-processing mechanism end to end and proved two identity losses in it: the per-field
# source record dropped the document identity every observation already carried, and the
# qualification record named a null project. Repairing the path moves executable behaviour, so
# it is a freeze SUCCESSOR (sim-2026.08-v27) rather than a violation of this guard. The files it
# was authorised to change are NAMED here for the same reason Run 41's are, so the set cannot
# quietly grow: anything else appearing in a frozen surface still fails.
RUN42_AUTHORISED_SUCCESSOR_CHANGES = {
    "server/app/extraction_merge.py",           # the per-field provenance record itself
    "server/app/simulation/qualification.py",   # the dimension reasons that read it
    "server/app/simulation/compute.py",         # the project identity passed to the record
    "server/app/documents.py",                  # the same identity on the read path
}
# identifiers is byte-identical to v27.
RUN43_AUTHORISED_SUCCESSOR_CHANGES = {
    "server/app/simulation/registry.py",           # the derived roster and its populations
    "server/app/simulation/portfolio_health.py",   # the Portfolio Health offload
    "server/app/research_export.py",               # the populations the export enumerates
    "server/app/training.py",                      # the training abstention population
    "assets/js/taxonomy.js",                       # generated from the roster in service
    "assets/js/categories.js",                     # generated from the roster in service
    "assets/js/detail.js",                         # the registered Group A count in its comment
    "assets/js/knowledge.js",                      # the three populations a participant reads
    "index.html",                                  # the same three populations
    "p0-baseline/module_renumbering_map.csv",      # the single authority for service
}
# RESTATED BY RUN 44, AND THE SAME DISCIPLINE AGAIN. The repair of the four participant-facing
# render defects Run 43J diagnosed changes what a participant is SHOWN, which is executable
# behaviour, so it is a freeze SUCCESSOR (sim-2026.08-v29) rather than a violation of this guard.
# The files it was authorised to change are NAMED here, so the set cannot quietly grow: anything
# else appearing in a frozen surface still fails. Nothing on the analytical side moved --
# run_module() over all 101 registered identifiers is byte-identical to v28 on a full and a
# starved evidence package, proved by executing both lines.
#
# assets/js/deepdive.js IS NAMED HERE DELIBERATELY AND IS THE EXCEPTION OF RECORD. It is one of
# the six SEQUENCE_BEARING_FILES, and its authority is the owner's order at Run 44 section 4.4:
# the Portfolio Health flyout told a participant the panel needed at least three projects when
# after the Run-43 offload no number of projects makes it compute. The other five sequence-bearing
# files are still byte-identical, which the participant-package suite asserts separately.
RUN44_AUTHORISED_SUCCESSOR_CHANGES = {
    "assets/js/detail.js",       # one shared case-insensitive severity rank; the driver guard;
                                 # an absent document-risk score rendering as absent
    "assets/js/signals.js",      # CPI and SPI labelled computed rather than extracted
    "assets/js/deepdive.js",     # the Portfolio Health flyout's reason sentence (section 4.4)
    "assets/css/radar.css",      # one added rule for the computed mark
    "server/app/simulation/registry.py",   # a DOCSTRING only; the function body is untouched
}
# RESTATED BY RUN 45, AND THE SAME DISCIPLINE AGAIN. Run 45 closes the period-scoping
# fall-through Run 44 measured: identity fields now retrieve the latest value at or before the
# period being computed, with declared document-type precedence holding across the carry-forward,
# so a contract uploaded at period 1 is no longer invisible at period 2. WHAT A MODULE IS GIVEN
# is executable behaviour, so it is a freeze SUCCESSOR (sim-2026.08-v30) rather than a violation
# of this guard. ONE file needs naming here: `server/app/field_registry.py`, which carries the
# classification. `extraction_merge.py`, `documents.py` and `models.py` are already named by
# Run 41's or Run 42's set above, and no path is named twice. NO PARTICIPANT-FACING CONTROL
# MOVED and no sequence-bearing file moved. Period-field retrieval is unchanged, which the
# Run-45 census proves on two control corpora that are byte-identical before and after.
RUN45_AUTHORISED_SUCCESSOR_CHANGES = {
    "server/app/field_registry.py",   # the canonical IDENTITY/PERIOD classification itself
}
# RESTATED BY RUN 47, AND THE SAME DISCIPLINE AGAIN. Run 47 adds the EVM consistency check on
# the owner's four rulings: where ONE document states both a value and the percentage that
# determines it against a known budget at completion, the implied value is computed and the two
# are compared, and a difference above 2 per cent of the implied value is reported AS TEXT on
# surfaces that already exist. WHAT A SERVED RESULT CARRIES is executable behaviour, so it is a
# freeze SUCCESSOR (sim-2026.08-v31) rather than a violation of this guard. TWO files need naming
# here: `assets/js/recommendation_options.js`, which renders the text beside the recommendation,
# and `server/app/evm_consistency.py`, which is new. `detail.js`, `documents.py` and `models.py`
# are already named by an earlier set above, and no path is named twice. NOTHING IS DERIVED INTO
# STORAGE, NO STORED FIGURE MOVED, NO PARTICIPANT-FACING CONTROL MOVED and NO SEQUENCE-BEARING
# FILE MOVED: all six are byte-identical, which the participant-package suite asserts separately.
RUN47_AUTHORISED_SUCCESSOR_CHANGES = {
    "assets/js/recommendation_options.js",  # the disagreement text beside the recommendation
    "server/app/evm_consistency.py",        # NEW: the comparison itself, a pure read-path function
}
# RESTATED BY RUN 48, AND THE SAME DISCIPLINE AGAIN. Run 48 makes the project detail page read
# back the stored row for the LATEST PERIOD THAT HAS BEEN COMPUTED instead of for the literal
# period 1, and corrects the live instances of the retired "Cat N" naming scheme, on the owner's
# three rulings of 2026-08-22. WHICH STORED ROW A PAGE READS is executable behaviour, so it is a
# freeze SUCCESSOR (sim-2026.08-v32) rather than a violation of this guard. TWO files need naming
# here: `assets/js/deepdive.js`, whose panel labels become groups and purposes, and
# `assets/js/charts3d.js`, whose synthesis node label does the same. `detail.js`, `documents.py`
# and `models.py` are already named by an earlier set above, and no path is named twice. NO
# STORED FIGURE MOVED and nothing is derived into storage: every addition is on the READ path.
# NO USER-FACING CONTROL MOVED, and the detail page still holds no period selector. ONE
# SEQUENCE-BEARING FILE MOVED, deepdive.js, on the owner's ruling 2, and it carries its own named
# exception record in participant_packages.py, which the package suite asserts separately.
RUN48_AUTHORISED_SUCCESSOR_CHANGES = {
    "assets/js/deepdive.js",   # the deep-dive panel labels: groups and purposes, no identifier
    "assets/js/charts3d.js",   # one chart node label, same rule
}

# RUN 49. The owner's five rulings of 2026-08-22 finish the naming correction the Run 48 sweep
# left unfinished. TWO files move, both named here, and both sequence-bearing, each with its own
# named exception record in participant_packages.py: `assets/js/deepdive.js`, whose ten group
# headers, banner, metric-box label, comparison table and five prose sentences drop the retired
# "Cat N" scheme and whose panel label map is extended to every key the call sites pass; and
# `assets/js/decision-ui.js`, which gains COMMENTS ONLY at its three inert `period: 1` literals
# recording that the server derives the period from the research assignment and ignores the
# value. `assets/js/detail.js` is already named by an earlier set above and is not named twice.
# NO STORED FIGURE MOVED. NO BAND, STATUS, COLOUR OR POSTURE MOVED. NO USER-FACING CONTROL WAS
# ADDED, MOVED OR REMOVED. NO MODULE BUCKETS DIFFERENTLY: the grouping number is declared in
# CAT_NUM_FROM_MODULE and this run did not touch it.
RUN49_AUTHORISED_SUCCESSOR_CHANGES = {
    "assets/js/deepdive.js",     # the retired scheme, everywhere it still rendered, plus the map
    "assets/js/decision-ui.js",  # comments only at the three inert period literals
}
# RESTATED BY RUN 51, AND THE SAME DISCIPLINE AGAIN. Run 51 delivered the six rulings Run 50
# stopped on. What a participant is SHOWN changes -- a dead surface is deleted, a panel becomes
# two, seven panels move to the category their module belongs to, an eleventh group appears, and
# every count on a served page derives instead of being typed -- which is executable behaviour,
# so it is a freeze SUCCESSOR (sim-2026.08-v34) rather than a violation of this guard. Every file
# is NAMED here, so the set cannot quietly grow: anything else appearing in a frozen surface
# still fails. NOTHING ON THE ANALYTICAL SIDE MOVED: the behaviour digest is reproduced
# identically and no stored figure changed.
#
# ALL SIX SEQUENCE_BEARING_FILES ARE NAMED HERE DELIBERATELY and each is an exception OF RECORD,
# with what moved inside it written into the v19 checksum record's own header. Their authority is
# the owner's rulings 1 to 6 in the Run 51 order of 2026-08-22.
RUN51_AUTHORISED_SUCCESSOR_CHANGES = {
    "assets/js/deepdive.js",       # SEQUENCE-BEARING: the flyout deleted, the panel split, the
                                   # buckets corrected, the loop bound derived
    "assets/js/decision.js",       # SEQUENCE-BEARING: no identifier in the action plan
    "assets/js/decision-ui.js",    # SEQUENCE-BEARING: rendered placeholders say what they mean
    "assets/js/workspace.js",      # SEQUENCE-BEARING: the same, at six rendered fields
    "assets/questionnaires/intake.json",    # SEQUENCE-BEARING: wording inside existing labels
    "assets/questionnaires/debrief.json",   # SEQUENCE-BEARING: one placeholder notice
    "assets/js/app.js",            # the ledger identifier chips; the derived About counts
    "assets/js/knowledge.js",      # the handbook counts and the Signal Stack SVG labels
    "assets/js/detail.js",         # the key/label separation and the brief's category names
    "assets/js/signals.js",        # the key/label separation and the document group labels
    "assets/js/neural_flow.js",    # the population it draws is in service, not registered
    "assets/js/projectnet2d.js",   # the key/label separation
    "assets/js/export.js",         # the workbook's identifier columns
    "assets/js/taxonomy.js",       # GENERATED from the authority and the registry
    "assets/js/categories.js",     # GENERATED from the authority and the registry
    "assets/js/ds_defensibility_data.js",   # the registry sentence derives; ampersands to words
    "assets/js/charts3d.js",       # axis and pill labels
    "assets/js/auditor.js",        # rendered placeholders and one model prompt
    "assets/js/admin-ops.js",      # rendered placeholders
    "assets/js/ingest.js",         # one rendered placeholder
    "assets/js/store.js",          # one console separator
    "assets/visualizations/pceif_neural_signal_flow.html",   # the page title and heading
    "index.html",                  # three typed counts become derived spans
    "server/app/simulation/models.py",       # the stamp advances to sim-2026.08-v34
    "server/tools/taxonomy_authority.json",  # `num` becomes `key`: the primary key, named
    "server/tools/build_client_taxonomy.py", # emits `key` and the derived counts block
}
RUN59_AUTHORISED_SUCCESSOR_CHANGES = {
    # RUN 59. NO MARKDOWN DOCUMENT CARRIES AUTHORITY. Six production-tree members moved and EVERY
    # ONE OF THE SIX EDITS IS A COMMENT OR A DOCUMENT HEADING. Not one executable byte moved, no
    # rendered string moved, and no control was added, moved or removed.
    "assets/js/decision-ui.js",    # SEQUENCE-BEARING: the block comment heading the NAME tables
                                   # stated the SUPERSEDED identifier prohibition as its reason.
                                   # Named exception of record, V23_TO_V24_SEQUENCE_EXCEPTION.
                                   # Not one entry of GROUP_NAMES or MODULE_NAMES changed.
    "server/app/research_export.py",             # cited "NAMING_AUTHORITY.md rule 6" BY NUMBER
    "server/app/document_evidence.py",           # cited the same superseded rule
    "server/app/evm_consistency.py",             # cited the same superseded rule
    "server/app/simulation/portfolio_health.py", # cited "NAMING_AUTHORITY section 4", which is
                                   # the section that RECORDED THE REVERSAL: the code cited the
                                   # reversal as the source of the rule
    "server/app/simulation/models.py",           # the stamp advances to sim-2026.08-v39
    "p0-baseline/MODULE_TAXONOMY.md",            # the count is marked as the figure at a date
}

#: RUN 62. THE PUBLICATION OF RUNS 60 AND 61.
RUN62_AUTHORISED_SUCCESSOR_CHANGES = {
    # RUN 62. THE PUBLICATION OF RUNS 60 AND 61. Three production-tree members moved and the
    # change is the correction the owner has waited ten runs for: a project detail page now
    # renders the stored-signal row of the period the page holds. No control was added, moved or
    # removed and no stored figure changed.
    "assets/js/detail.js",         # re-renders its provenance line from the row it received
    "assets/js/taxonomy.js",       # the stored-row cache is keyed by (project, period)
    "assets/js/workspace.js",      # SEQUENCE-BEARING: the ORDER of the server calls, so the
                                   # period is resolved BEFORE results are requested. Named
                                   # exception of record, V24_TO_V25_SEQUENCE_EXCEPTION.
}
AUTHORISED_SUCCESSOR_CHANGES = (RUN41_AUTHORISED_SUCCESSOR_CHANGES
                                | RUN42_AUTHORISED_SUCCESSOR_CHANGES
                                | RUN43_AUTHORISED_SUCCESSOR_CHANGES
                                | RUN44_AUTHORISED_SUCCESSOR_CHANGES
                                | RUN45_AUTHORISED_SUCCESSOR_CHANGES
                                | RUN47_AUTHORISED_SUCCESSOR_CHANGES
                                | RUN48_AUTHORISED_SUCCESSOR_CHANGES
                                | RUN49_AUTHORISED_SUCCESSOR_CHANGES
                                | RUN51_AUTHORISED_SUCCESSOR_CHANGES
                                | RUN59_AUTHORISED_SUCCESSOR_CHANGES
                                | RUN62_AUTHORISED_SUCCESSOR_CHANGES)
_surface_paths = sorted({ln.split("\t", 1)[-1] for ln in changed_surfaces if ln})
_unauthorised = [p for p in _surface_paths if p not in AUTHORISED_SUCCESSOR_CHANGES]
check(not _unauthorised,
      "the production server application, the participant/client assets, the served page, the "
      "controlled stimuli, the frozen methodology specification and the participant sequence "
      "authority differ from the freeze candidate ONLY by Run 41's owner-authorised successor "
      "changes",
      "; ".join(_unauthorised[:12]))

# ---- surface 2: the governed freeze checksum manifest.
manifest_paths: list[str] = []
if MANIFEST.exists():
    with MANIFEST.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            for key in ("path", "file", "filename"):
                if key in r and r[key]:
                    manifest_paths.append(r[key].strip())
                    break
check(bool(manifest_paths), "the freeze checksum manifest names the frozen files",
      f"{len(manifest_paths)} paths")

BOOKKEEPING = {
    "research/freeze/INSTRUMENT_FINAL_FREEZE_CHECKSUMS.csv",
    "research/freeze/INSTRUMENT_FINAL_FREEZE_RECORD.json",
}
# RESTATED BY RUN 41, RUN 39'S FINDING PRESERVED. The subject is that RUN 39 changed no governed
# file, still asserted below. Run 41's owner-authorised successor changes are subtracted BY NAME,
# not by widening the comparison, so any other manifest file that moved would still fail.
RUN41_AUTHORISED_MANIFEST_CHANGES = {"server/app/simulation/models.py"}
# RESTATED BY RUN 42, subtracted by NAME for the same reason. qualification.py is named by the
# governed manifest, and Run 42's repair reaches it: the provenance and timeliness reason
# sentences must describe the state actually reached now that the dimensions can leave PARTIAL.
# Any OTHER manifest file that moved still fails this check.
RUN42_AUTHORISED_MANIFEST_CHANGES = {"server/app/simulation/qualification.py"}
# fails this check.
RUN43_AUTHORISED_MANIFEST_CHANGES = {
    "server/app/simulation/registry.py",
    "assets/js/taxonomy.js",
    "assets/js/categories.js",
    "p0-baseline/module_renumbering_map.csv",
    # The generator that emits both client taxonomy mirrors. Its population source moves from
    # the whole registry to registry.service_index(); the mirrors themselves are its output and
    # are named above.
    "server/tools/build_client_taxonomy.py",
}
# RUN 44. The manifest files this run was authorised to move, named for the same reason.
# registry.py moves for a DOCSTRING only; the JavaScript and the stylesheet are the render
# repairs themselves.
RUN44_AUTHORISED_MANIFEST_CHANGES = {
    "server/app/simulation/registry.py",
    "assets/js/detail.js",
    "assets/js/signals.js",
    "assets/js/deepdive.js",
    "assets/css/radar.css",
}
# RUN 49. The manifest files this run was authorised to move, named for the same reason.
# decision-ui.js moves for COMMENTS ONLY, on the owner's ruling 4; deepdive.js and detail.js
# carry the naming completion itself and are already named by the Run-44 set above.
RUN49_AUTHORISED_MANIFEST_CHANGES = {
    "assets/js/decision-ui.js",
}
# RUN 51. The manifest files this run was authorised to move, named for the same reason.
# taxonomy_authority.json is the taxonomy's own authority and its PRIMARY-KEY FIELD is renamed
# from `num` to `key` on the owner's ruling 2, so that a render site cannot mistake the key for a
# label; not one identifier, module or category changed. decision.js, workspace.js and both
# questionnaires are sequence-bearing and each carries its own named exception record in the v19
# checksum record. Any OTHER manifest file that moved still fails this check.
RUN51_AUTHORISED_MANIFEST_CHANGES = {
    "server/tools/taxonomy_authority.json",
    "assets/js/decision.js",
    "assets/js/workspace.js",
    "assets/questionnaires/intake.json",
    "assets/questionnaires/debrief.json",
    "assets/js/app.js",
    "assets/js/knowledge.js",
    "assets/js/detail.js",
    "assets/js/signals.js",
    "assets/js/deepdive.js",
    "assets/js/decision-ui.js",
    "assets/js/taxonomy.js",
    "assets/js/categories.js",
    "assets/js/neural_flow.js",
    "assets/js/charts3d.js",
    "assets/js/ds_defensibility_data.js",
    "index.html",
}
AUTHORISED_MANIFEST_CHANGES = (RUN41_AUTHORISED_MANIFEST_CHANGES
                               | RUN42_AUTHORISED_MANIFEST_CHANGES
                               | RUN43_AUTHORISED_MANIFEST_CHANGES
                               | RUN44_AUTHORISED_MANIFEST_CHANGES
                               | RUN49_AUTHORISED_MANIFEST_CHANGES
                               | RUN51_AUTHORISED_MANIFEST_CHANGES)
targets = sorted(set(manifest_paths) - BOOKKEEPING - AUTHORISED_MANIFEST_CHANGES)
vs_ready = [p for p in targets if diff_committed(RUN38_READY, p)]
check(not vs_ready,
      "no file named by the governed freeze checksum manifest differs from the Run-38 readiness "
      "commit, so Run 39 changed none of them", "; ".join(vs_ready[:10]))

# ---- surface 3: the version identities, from the live code and the governed records.
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(ROOT / "server" / "tools"))
from app.simulation.models import SIMULATION_VERSION                    # noqa: E402
import participant_packages as PP                                       # noqa: E402
import run38_analysis_export as AX                                      # noqa: E402

freeze = json.loads((ROOT / "research/freeze/INSTRUMENT_FINAL_FREEZE_RECORD.json")
                    .read_text(encoding="utf-8"))
readiness = json.loads((ROOT / "research/study_execution/"
                        "STUDY_EXECUTION_READINESS_MANIFEST.json").read_text(encoding="utf-8"))

check(freeze["release_disposition"] == "FINAL_FREEZE_ACCEPTED",
      "the final freeze is still FINAL_FREEZE_ACCEPTED")
check(freeze["freeze_candidate_commit"] == CANDIDATE,
      "the freeze record still names the same candidate")
check(readiness["final_disposition"] == "STUDY_EXECUTION_READY",
      "the Run-38 readiness disposition is unchanged")
# RESTATED BY RUN 41. The v25 freeze record is not rewritten - asserted, not assumed - and the
# live stamp advances to the authorised successor.
check(freeze["simulation_version"] == "sim-2026.08-v25",
      "the v25 freeze record still says sim-2026.08-v25 and was not rewritten by the successor",
      freeze["simulation_version"])
# RUN 56. RESTATED BY RUN 56, for the same reason and with the same scope: Run 56 supersedes v36 with v37 because WHAT A PARTICIPANT REACHES AND CLICKS is executable behaviour -- the duplicate 'Upload documents' control is removed from the project detail page and Archive and Reset signals now ask before acting.
check(SIMULATION_VERSION == "sim-2026.08-v40",
      "and the live simulation is the Run-62 successor sim-2026.08-v40", SIMULATION_VERSION)
# RESTATED BY RUN 43: v13 is superseded by v14 and pinned to its own commit rather than rewritten.
check(PP.CURRENT.identifier == "og-participant-2026.08-v25",
      "the participant package is superseded at og-participant-2026.08-v25",
      PP.CURRENT.identifier)
check(freeze["synthetic_package"] == "OG-SYNTH-0.6",
      "the synthetic package is unchanged at OG-SYNTH-0.6")
check(AX.ANALYSIS_SCHEMA_VERSION == "og-analysis-2026.08-v1",
      "the analysis export schema is unchanged at og-analysis-2026.08-v1",
      AX.ANALYSIS_SCHEMA_VERSION)

# NO SUCCESSOR WAS MINTED. Section 21 forbids minting one for launch documentation, pilot
# provenance, audit artifacts, validators or pilot data -- which is everything Run 39 produced.
check(readiness["export_schema_version"] == AX.ANALYSIS_SCHEMA_VERSION,
      "the Run-38 manifest and the live export module still agree on the schema version")
check(len(AX.ANALYSIS_COLUMNS) == readiness["export_column_count"],
      "and on the column count, derived on both sides rather than transcribed",
      f"{len(AX.ANALYSIS_COLUMNS)} vs {readiness['export_column_count']}")

# ---- surface 4: what Run 39 actually changed, enumerated against the Run-38 readiness commit.
#
# The permitted set is NAMED so it cannot quietly grow. Run 39 is required by its controlling
# specification to update T6_HANDOFF.md, and it appends an erratum to the Run-38 report because
# that report's prose carries a column count the live code contradicts. Neither is executable,
# neither is inside a frozen surface, and neither is named by the freeze checksum manifest --
# all three of which are asserted separately above and below.
PERMITTED_MODIFICATIONS = {
    # RUN 57. The reset control merged into one and the pinned guards that named it advanced.
    # `test_run21_reset_disclosure.py` read the reset control's promise off `.detail-reset`'s
    # title in detail.js; the control MOVED FILE when the two handlers were merged, so the guard
    # is re-pointed at ingest.js, where the surviving control makes the promise in the same
    # words, and a further check is ADDED requiring detail.js to carry no reset control at all.
    # NAMED HERE rather than admitted by widening the rule.
    "server/tools/test_run21_reset_disclosure.py",
    "T6_HANDOFF.md",
    "REPORT_2026-08-19_run38-study-execution-readiness.md",
    "server/tools/test_run38_frozen_immutability.py",
    # Repoints PINNED_AUTHORITY to code_audit/run39_authority_tree.sha256, because Run 39's
    # dataset-classification contract lands inside an AUTHORITY_ROOT. Run-34, 35 and 38
    # precedent; prior manifests stay addressable.
    "server/tools/production_tree.py",
} | AUTHORISED_SUCCESSOR_CHANGES | {
    # RUN 41's owner-authorised successor. Each pre-existing file it must touch is named: the
    # pinned production-tree pointer, the suites that asserted the superseded stamp or the old
    # freeze anchors, the three suites that used to reach a column the S2 trigger now protects,
    # and the owner checklist the specification requires be updated to v26.
    # RUN 51, THE DELIVERY OF WHAT RUN 50 STOPPED ON. The suites and tools whose pinned
    # expectation is a stamp, a package identity, a manifest pointer or a parsed field name the
    # successor legitimately moves. Each is NAMED rather than the rule being widened. Not one is
    # executable production or client code, not one is named by the freeze checksum manifest,
    # and not one is inside a frozen surface.
    "server/tools/build_run32_b3_reconciliation.py",
    "server/tools/run26_fault_campaign.py",
    "server/tools/run32_b3_browser_verification.py",
    "server/tools/run32_qualifier_fault_campaign.py",
    "server/tools/test_run10_synthetic_v03.py",
    "server/tools/test_run16_material_cost_variance_disabled.py",
    "server/tools/test_run16_final_flow_and_rail.py",
    "server/tools/test_run24_empty_project_diagram.py",
    "server/tools/test_run26_counts_and_wiring.py",
    "server/tools/test_run28_participant_packages.py",
    "server/tools/test_run32_client_authority.py",
    "server/tools/test_run32_defensibility_truth.py",
    "server/tools/test_run32_method_class_agreement.py",
    "server/tools/test_run35_closure_voter_identities.py",
    "server/tools/test_run36_fault_guards.py",
    "server/tools/test_run41_preservation.py",
    "server/tools/test_run44_participant_defect_fixes.py",
    "server/tools/test_run48_current_period.py",
    "server/tools/test_run49_naming_completion.py",
    "server/tools/test_run2_fifteen_defects.py",
    "server/tools/test_run20_declared_production_changes.py",
    "server/tools/test_run25_rail_removal.py",
    "server/tools/test_run6_known_answer.py",
    "server/tools/test_run8_retest_classify_27.py",
    "server/tools/participant_packages.py",
    "server/tools/test_run38_frozen_immutability.py",
    "server/tools/test_run10_state_protection.py",
    "server/tools/test_run22_production_tree_completeness.py",
    "server/tools/test_run31_version_boundaries.py",
    "server/tools/test_run32_closure_version_boundary.py",
    "server/tools/test_run36_closure_guards.py",
    "server/tools/test_run36_instrument_qualification.py",
    "server/tools/test_run37_freeze_gate.py",
    "server/tools/test_run39_frozen_immutability.py",
    "server/tools/test_run39_launch_gate.py",
    "server/tools/build_run37_acceptance.py",
    # RUN 55, THE MINT. NAMED, NOT WIDENED: `tests_render.html`'s row-actions group asserted the
    # pre-Run-54 project-list state -- exactly one Open control, labelled "Open ->", in a cluster
    # reading "Manage|Open ->". Run 54 phase C removed that control on the owner's ruling, so the
    # group was revised to assert the CURRENT state. This entry names that one file; it does not
    # loosen the rule that every other pre-existing file must be untouched.
    "tests_render.html",
    "server/tools/test_export.py",
    "server/tools/test_admin_ops_t7t8.py",
    "server/tools/test_decision_ui_t4.py",
    # RUN 41, second pass. Four further pinned guards had to be told which file the successor
    # was authorised to change: the two production-baseline comparisons, the declared-changes
    # manifest guard, and the pinned-manifest chain. Each names the file rather than widening its
    # rule, so all four keep their full force over everything else.
    "server/tools/test_run6_known_answer.py",
    "server/tools/test_run8_retest_classify_27.py",
    "server/tools/test_run20_declared_production_changes.py",
    "server/tools/test_run25_rail_removal.py",
    "research/study_execution/OWNER_WEBSITE_ACCEPTANCE_CHECKLIST.md",
    "server/tools/test_run39_frozen_immutability.py",
    "server/tools/test_run39_launch_gate.py",
    "server/tools/test_run37_freeze_gate.py",
    "server/tools/build_run37_acceptance.py",
    "server/tools/production_tree.py",
    "server/tools/test_run6_known_answer.py",
    "server/tools/test_run8_retest_classify_27.py",
    "server/tools/test_run10_state_protection.py",
    "server/tools/test_run20_declared_production_changes.py",
    "server/tools/test_run22_production_tree_completeness.py",
    "server/tools/test_run31_version_boundaries.py",
    "server/tools/test_run32_closure_version_boundary.py",
    "server/tools/test_run36_instrument_qualification.py",
    # RUN 43, THE RETIREMENT. The suites whose pinned expectation is a population, a stamp or a
    # manifest pointer the successor legitimately moves. Each names the file rather than widening
    # its rule, so all of them keep their full force over everything else. Not one is executable
    # production or client code, not one is named by the freeze checksum manifest, and not one is
    # inside a frozen surface -- all three asserted separately above and below.
    "NAMING_AUTHORITY.md",
    "server/tools/participant_packages.py",
    "server/tools/build_client_taxonomy.py",
    "server/tools/build_run34_artifacts.py",
    "server/tools/run34_ph1_tree_count_calibration.py",
    "server/tools/test_courses_of_action.py",
    "server/tools/test_documents_b7b.py",
    "server/tools/test_map_and_module_count.py",
    "server/tools/test_period_series.py",
    "server/tools/test_run10_synthetic_v03.py",
    "server/tools/test_run10b_canonical_integration.py",
    "server/tools/test_run14_mismatch_remediation.py",
    "server/tools/test_run16_material_cost_variance_disabled.py",
    "server/tools/test_run1_disable_and_relabel.py",
    "server/tools/test_run20_cycle10_truthful_labels.py",
    "server/tools/test_run20_cycle12_reaudit.py",
    "server/tools/test_run20_lineage_declaration_truth.py",
    "server/tools/test_run24_empty_project_diagram.py",
    "server/tools/test_run26_counts_and_wiring.py",
    "server/tools/test_run28_closure.py",
    "server/tools/test_run28_participant_packages.py",
    "server/tools/test_run2_fifteen_defects.py",
    "server/tools/test_run30_cat7_operational_route.py",
    "server/tools/test_run30_lineage_semantics.py",
    "server/tools/test_run32_client_authority.py",
    "server/tools/test_run32_defensibility_truth.py",
    "server/tools/test_run32_method_class_agreement.py",
    "server/tools/test_run33_portfolio_health.py",
    "server/tools/test_run3_adapter.py",
    "server/tools/test_run41_preservation.py",
    "server/tools/test_run4_validate_seven.py",
    "server/tools/test_run7_fix_now_defects.py",
    "server/tools/test_simulation.py",
    "server/tools/test_six_fixes.py",
    "server/tools/test_workspace_t3t5.py",
} | {
    # RUN 44, THE PARTICIPANT-FACING RENDER DEFECTS. One further suite whose pinned expectation
    # the successor legitimately moves: test_run36_fault_guards asserted that all six
    # sequence-bearing files are byte-identical to the frozen v11 package, and Run 44 was
    # authorised by the owner at its section 4.4 to move exactly one of them. Its check now names
    # that one exception rather than being widened, so it keeps its full force over the other
    # five. Not executable production or client code, and not named by the freeze checksum
    # manifest.
    "server/tools/test_run36_fault_guards.py",
} | {
    # RUN 54, PHASE A: THE CAMPAIGN-SAFETY GUARD. Every fault campaign in the repository -- 39 of
    # them, 35 in server/tools and 4 in server/tests -- is armed with the start-AND-end dirty-tree
    # guard, and the suite runner now fails when a suite leaves production or client source dirty.
    # The authority is the owner's section 7 of the Run 54 order. Each file is NAMED here rather
    # than admitted by widening the rule, on exactly the Run-41 / Run-43 / Run-44 construction
    # above, so the check keeps its full force over everything else. NOT ONE is executable
    # production or client code, not one is named by the freeze checksum manifest, and not one is
    # inside a frozen surface -- all three asserted separately above and below. server/tools/
    # campaign_safety.py itself is an ADDITION, not a modification, and needs no entry.
    "server/run_all_suites.sh",
    "server/tests/test_run33_ph1_fault_campaign.py",
    "server/tests/test_run34_count_fault_campaign.py",
    "server/tests/test_run34_fault_campaign.py",
    "server/tests/test_run34_provenance_fault_campaign.py",
    "server/tools/drive_run26_faults.py",
    "server/tools/run20_cycle12_cycle3_fault_battery.py",
    "server/tools/run22_guard_mutation_campaign.py",
    "server/tools/run26_fault_campaign.py",
    "server/tools/run27_fault_campaign.py",
    "server/tools/run28_closure_fault_campaign.py",
    "server/tools/run28_fault_campaign.py",
    "server/tools/run31_full_fault_campaign.py",
    "server/tools/run31_pass2_targeted_faults.py",
    "server/tools/run31_synthetic_scope_faults.py",
    "server/tools/run32_b3_fault_campaign.py",
    "server/tools/run32_closure_fault_campaign.py",
    "server/tools/run32_fault_campaign.py",
    "server/tools/run32_qualifier_count_fault_campaign.py",
    "server/tools/run32_qualifier_fault_campaign.py",
    "server/tools/run35_closure_fault_campaign.py",
    "server/tools/run35_fault_campaign.py",
    "server/tools/run36_closure_fault_campaign.py",
    "server/tools/run36_fault_campaign.py",
    "server/tools/run37_documentation_scope_campaign.py",
    "server/tools/run37_freeze_gate_campaign.py",
    "server/tools/run38_fault_campaign.py",
    "server/tools/run39_fault_campaign.py",
    "server/tools/run41_fault_campaign.py",
    "server/tools/run51_injection_campaign.py",
    "server/tools/run52_injection_campaign.py",
    "server/tools/test_run20_cycle12_fault_evidence.py",
    "server/tools/test_run29_fault_campaign.py",
    "server/tools/test_run33_ph1_fault_campaign.py",
    "server/tools/test_run33_portfolio_fault_injection.py",
    "server/tools/test_run34_count_fault_campaign.py",
    "server/tools/test_run34_fault_campaign.py",
    "server/tools/test_run34_provenance_fault_campaign.py",
    "server/tools/test_run36_fault_guards.py",
    "server/tools/test_run41_fault_campaign.py",
    # RUN 54, PHASES B, C AND D. The deep-dive surface is DELETED on the owner's ruling at
    # section 8, and the suites that asserted properties OF that surface are reconciled to assert
    # its absence instead. Each is NAMED here rather than admitted by widening the rule. The two
    # deleted paths and assets/js/app.js and index.html are named in the successor set below;
    # these four are the reconciled guards and the deleted page itself.
    "research/deepdive.html",
    "server/tools/test_run11_browser_server_authority.py",
    "server/tools/test_run12_final_verification.py",
    "server/tools/test_run13_module_evidence.py",
    "server/tools/test_run28_closure.py",
    "server/tools/test_run36_fault_guards.py",
    "server/tools/test_run41_preservation.py",
    "server/tools/test_run49_naming_completion.py",
    "server/tools/test_run6_known_answer.py",
    "server/tools/test_run48_current_period.py",
    "server/tools/test_run44_participant_defect_fixes.py",
    "server/tools/test_run38_frozen_immutability.py",
    "server/tools/test_run39_frozen_immutability.py",
    "server/tools/drive_run50_browser.py",
    "server/tools/run52_rendered_text_capture.py",
    "code_audit/run45_field_classification_proposal.md",
    # RUN 59. NO MARKDOWN DOCUMENT CARRIES AUTHORITY. Each file is NAMED here rather than the
    # rule widened, and NOT ONE is executable production or client code that a participant runs.
    # The documents corrected against production, all of them transport or history:
    "BACKEND_CHANGES_NEEDED.md",
    "COPY_GLOSSARY.md",
    "GROUP_ASSIGNMENT.md",
    "MODULE_RETIREMENT_DECISIONS.md",
    "README.md",
    "T6_HANDOFF.md",
    "remediation_programme.md",
    "training_pmp_upgrade_roadmap.md",
    "p0-baseline/MODULE_TAXONOMY.md",
    "server/tools/run17/categories/WORKER_BRIEF.md",
    # The four server comments that cited the SUPERSEDED module-identifier rule. COMMENTS ONLY:
    # not one executable byte moved in any of them, which the freeze checksum manifest records
    # as a digest change and the behaviour digest records as no change at all.
    "server/app/document_evidence.py",
    "server/app/evm_consistency.py",
    "server/app/research_export.py",
    "server/app/simulation/portfolio_health.py",
    # The mint machinery and the pinned guards this mint advanced:
    "server/tools/production_tree.py",
    "server/tools/build_run37_acceptance.py",
    "server/tools/test_run25_rail_removal.py",
    "server/tools/test_run31_version_boundaries.py",
    "server/tools/test_run32_closure_version_boundary.py",
    "server/tools/test_run36_instrument_qualification.py",
    "server/tools/test_run37_documentation_scope.py",
    "server/tools/test_run39_launch_gate.py",
    # PHASE B: the guards re-pointed off markdown, and the guards retired. Every retired body is
    # PRESENT; nothing was deleted.
    "server/tools/test_disclaimers.py",
    "server/tools/test_export_workbook.py",
    "server/tools/test_group_assignment.py",
    "server/tools/test_run32_qualifier_count_closure.py",
    "server/tests/test_run34_parameter_count_closure.py",
    "server/tests/test_run34_holdout_provenance.py",
    "server/tests/test_run34_count_fault_campaign.py",
    "server/tests/test_run34_provenance_fault_campaign.py",
}
run39 = [ln.split("\t", 1) for ln in diff_committed(RUN38_READY).splitlines() if ln]
in_frozen = [p for st, p in run39
             if any(p == s or p.startswith(s + "/") for s in SURFACES)]
_in_frozen_unauthorised = [p for p in in_frozen
                           if p not in AUTHORISED_SUCCESSOR_CHANGES]
check(not _in_frozen_unauthorised,
      "nothing Run 39 added or changed lands inside a frozen surface, and the only frozen-surface "
      "paths that moved since are Run 41's owner-authorised successor changes",
      "; ".join(_in_frozen_unauthorised[:10]))

modified = [p for st, p in run39 if not st.startswith("A")]
unexpected = [p for p in modified if p not in PERMITTED_MODIFICATIONS]
check(not unexpected, "Run 39 modified no pre-existing file outside the named permitted set",
      "; ".join(unexpected[:12]))
check(not ((set(modified) & set(manifest_paths)) - AUTHORISED_MANIFEST_CHANGES),
      "and no modified file is named by the governed freeze checksum manifest, apart from "
      "Run 41's owner-authorised successor changes",
      "; ".join(sorted(set(modified) & set(manifest_paths))[:8]))

print(f"    Run 39 changes {len(run39)} paths against the Run-38 readiness commit: "
      f"{len(run39) - len(modified)} additions, {len(modified)} permitted modifications"
      f"{' (' + ', '.join(sorted(modified)) + ')' if modified else ''}, "
      f"{len(in_frozen)} frozen.")

passed = sum(1 for ok, _, _ in results if ok)
print()
for ok, label, detail in results:
    if not ok:
        print(f"FAILED: {label}   {detail}")
print(f"RESULT: {passed}/{len(results)} checks passed")
sys.exit(0 if passed == len(results) else 1)
