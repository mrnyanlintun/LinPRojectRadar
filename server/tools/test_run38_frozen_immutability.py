#!/usr/bin/env python3
"""
RUN 38 SECTION 22. FROZEN-INSTRUMENT IMMUTABILITY, PROVED BY DIFF RATHER THAN ASSERTED.

The accepted final freeze names candidate 6142d877856ea651ef8d7e905f6d27604b3244f1. This gate
proves that the tree it runs on differs from that candidate in ZERO scientific, client,
controlled-stimulus or participant-facing bytes.

IT DOES NOT ASSERT THAT NOTHING WAS TOUCHED. It asks git for the actual difference between the
working tree and the candidate over the freeze-critical surfaces, mechanically derived, and
fails naming every path that moved. A gate that merely stated "Run 38 did not edit these" would
be a declaration, not a measurement, and this programme has been wrong that way before.

Freeze-critical surfaces, derived rather than transcribed:
  * every path listed in research/freeze/INSTRUMENT_FINAL_FREEZE_CHECKSUMS.csv, which IS the
    governed freeze manifest;
  * the served client (assets/), the production server application (server/app/) and the
    controlled stimulus corpus (research_fixtures/synthetic/), taken wholesale so a new file
    added to any of them is caught too.

Run:
    PYTHONIOENCODING=utf-8 python tools/test_run38_frozen_immutability.py
"""
from __future__ import annotations

import csv
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
CANDIDATE = "6142d877856ea651ef8d7e905f6d27604b3244f1"
MANIFEST = ROOT / "research" / "freeze" / "INSTRUMENT_FINAL_FREEZE_CHECKSUMS.csv"

SURFACES = ("assets", "server/app", "research_fixtures/synthetic", "index.html")

results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   {detail}" if detail and not ok else ""))


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=str(ROOT), capture_output=True,
                          text=True).stdout


# TWO DIFFERENT QUESTIONS, ASKED OF TWO DIFFERENT THINGS, AND THE DISTINCTION IS LOAD-BEARING.
#
# "What did this run change?" is a question about COMMITTED history. Asking it of the working
# tree makes the answer depend on which other suites happened to run first: several suites in
# this repository legitimately rewrite their own audit CSVs as a side effect (run8, run9, run10,
# run20, run17/coverage), and those rewrites are restored rather than committed. Measured
# against the working tree this gate passed alone and failed inside the runner, which is an
# order-dependent oracle and therefore not an oracle at all.
#
# "Has a frozen byte moved?" is a question about WHAT IS ON DISK RIGHT NOW, because an
# uncommitted edit to a frozen surface must be caught too. That one keeps the working tree.
def diff_committed(ref: str, *paths: str) -> str:
    return git("diff", "--name-status", ref, "HEAD", "--", *paths).strip()


def diff_worktree(ref: str, *paths: str) -> str:
    return git("diff", "--name-status", ref, "--", *paths).strip()


known = git("cat-file", "-t", CANDIDATE).strip()
check(known == "commit", f"the freeze candidate {CANDIDATE[:12]} is present in this repository",
      known)

# ---- surface 1: the governed freeze manifest, read as the authority on what is frozen.
manifest_paths: list[str] = []
if MANIFEST.exists():
    with MANIFEST.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            for key in ("path", "file", "filename"):
                if key in row and row[key]:
                    manifest_paths.append(row[key].strip())
                    break
check(bool(manifest_paths), "the freeze checksum manifest names the frozen files",
      f"{len(manifest_paths)} paths, manifest present={MANIFEST.exists()}")

# The manifest necessarily names itself and the freeze record, whose content IS the freeze
# bookkeeping; they are excluded from the behavioural diff for the same reason the release
# digest excludes its own row. Nothing executable is excluded.
BOOKKEEPING = {
    "research/freeze/INSTRUMENT_FINAL_FREEZE_CHECKSUMS.csv",
    "research/freeze/INSTRUMENT_FINAL_FREEZE_RECORD.json",
}

# TWO REFERENCES, AND THE DIFFERENCE BETWEEN THEM IS MEASURED RATHER THAN GLOSSED.
#
# The candidate is not the release. Run 37 published the accepted release ON TOP of its own
# candidate, so eight of its audit artifacts and its own freeze bookkeeping legitimately differ
# between 6142d877 and the release commit. Attributing those to Run 38 would be false, and
# silently excluding them would hide a real change if one ever appeared there. So the manifest
# is diffed against BOTH, and each difference is attributed to the interval it actually
# occurred in.
RELEASE = "f983bb020f7a184a5742e1fff09d690b0170f0de"
check(git("cat-file", "-t", RELEASE).strip() == "commit",
      f"the accepted release {RELEASE[:12]} is present in this repository")

# RESTATED BY RUN 41, RUN 38'S FINDING PRESERVED. The subject is that RUN 38 changed no governed
# file, and that is still asserted below - Run 41's owner-authorised successor changes are
# subtracted by name, not by widening the comparison, so any OTHER manifest file that moved would
# still fail. models.py is named by the v25 governed manifest and Run 41 legitimately advances its
# stamp to sim-2026.08-v26 under the owner's ruling; that the v25 RECORD still says v25 is
# asserted separately above.
RUN41_AUTHORISED_MANIFEST_CHANGES = {"server/app/simulation/models.py"}
# RESTATED BY RUN 42, subtracted by NAME for the same reason. qualification.py is named by the
# governed manifest, and Run 42's repair reaches it: the provenance and timeliness reason
# sentences must describe the state actually reached now that the dimensions can leave PARTIAL.
# Any OTHER manifest file that moved still fails this check.
RUN42_AUTHORISED_MANIFEST_CHANGES = {"server/app/simulation/qualification.py"}
# RESTATED BY RUN 43, subtracted by NAME for the same reason. The owner ruled on 2026-08-21 that
# 38 of the 101 registered modules be retired FROM SERVICE. Four files named by the governed
# manifest carry that: the registry, which derives the roster in service from the CSV; the two
# generated client taxonomy mirrors, which a participant reads; and the CSV itself, which is the
# single authority for which modules are in service. Any OTHER manifest file that moved still
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
AUTHORISED_MANIFEST_CHANGES = (RUN41_AUTHORISED_MANIFEST_CHANGES
                               | RUN42_AUTHORISED_MANIFEST_CHANGES
                               | RUN43_AUTHORISED_MANIFEST_CHANGES
                               | RUN44_AUTHORISED_MANIFEST_CHANGES)
manifest_targets = sorted(set(manifest_paths) - BOOKKEEPING
                          - AUTHORISED_MANIFEST_CHANGES)
vs_candidate = [p for p in manifest_targets if diff_committed(CANDIDATE, p)]
vs_release = [p for p in manifest_targets if diff_committed(RELEASE, p)]
check(not vs_release,
      "no file named by the governed freeze manifest differs from the ACCEPTED RELEASE, so "
      "Run 38 changed none of them", "; ".join(vs_release[:10]))
run37_interval = sorted(set(vs_candidate) - set(vs_release))
check(set(vs_candidate) == set(run37_interval),
      "every manifest file that differs from the candidate differs only across the Run-37 "
      "candidate-to-release interval, not across Run 38",
      "; ".join(sorted(set(vs_candidate) - set(run37_interval))[:10]))
print(f"    manifest files differing candidate->release (Run 37, not Run 38): "
      f"{len(run37_interval)}")
executable_ext = {".py", ".js", ".html", ".css", ".csv", ".json"}
non_artifact = [p for p in run37_interval
                if any(p.startswith(s + "/") or p == s for s in SURFACES)]
check(not non_artifact,
      "and none of those Run-37-interval differences is inside an executable frozen surface",
      "; ".join(non_artifact[:10]))

# ---- surface 2: the executable surfaces, taken wholesale.
changed_surfaces = []
for surface in SURFACES:
    # Working tree, deliberately: an uncommitted edit to a frozen surface is exactly what
    # this must catch, and no suite in this repository writes into these paths.
    out = diff_worktree(CANDIDATE, surface)
    if out:
        changed_surfaces.extend(out.splitlines())
# RESTATED BY RUN 41, RUN 38'S FINDING PRESERVED. Until Run 41 this asserted byte-identity with
# the v25 freeze candidate, and that was the correct assertion for Run 38: Run 38 changed nothing
# here and still does not. Run 40 then confirmed two HIGH defects and the OWNER RULED that both
# be fixed before participant use rather than accepted for the study period, which is what makes
# Run 41 a freeze SUCCESSOR rather than a violation of this one.
#
# The guard is therefore not relaxed, it is made exact: the frozen surfaces may differ from the
# v25 candidate ONLY by the files Run 41 was authorised to change, and that set is NAMED here so
# it cannot quietly grow. Anything else appearing in a frozen surface still fails, which is the
# property this check exists for. server/alembic/ is not a SURFACE, so migration 0026 does not
# appear in this list.
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
# RESTATED BY RUN 43, AND THE SAME DISCIPLINE AGAIN. The retirement of 38 modules from service
# changes which modules the production paths enumerate and which reach a participant, which is
# executable behaviour, so it is a freeze SUCCESSOR (sim-2026.08-v28) rather than a violation of
# this guard. The files it was authorised to change are NAMED here for the same reason Run 41's
# and Run 42's are, so the set cannot quietly grow: anything else appearing in a frozen surface
# still fails. Nothing is deleted by any of them -- run_module() over all 101 registered
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
AUTHORISED_SUCCESSOR_CHANGES = (RUN41_AUTHORISED_SUCCESSOR_CHANGES
                                | RUN42_AUTHORISED_SUCCESSOR_CHANGES
                                | RUN43_AUTHORISED_SUCCESSOR_CHANGES
                                | RUN44_AUTHORISED_SUCCESSOR_CHANGES
                                | RUN45_AUTHORISED_SUCCESSOR_CHANGES
                                | RUN47_AUTHORISED_SUCCESSOR_CHANGES)
_surface_paths = sorted({ln.split("\t", 1)[-1] for ln in changed_surfaces if ln})
_unauthorised = [p for p in _surface_paths if p not in AUTHORISED_SUCCESSOR_CHANGES]
check(not _unauthorised,
      "the served client, the production server application, the controlled stimulus corpus "
      "and the served page differ from the freeze candidate ONLY by Run 41's owner-authorised "
      "successor changes",
      "; ".join(_unauthorised[:12]))
print(f"    frozen-surface differences vs the v25 candidate: {_surface_paths} "
      f"(all owner-authorised Run-41/42 successor changes)")

# ---- surface 3: the version identities themselves.
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(ROOT / "server" / "tools"))
from app.simulation.models import SIMULATION_VERSION            # noqa: E402
import participant_packages as PP                               # noqa: E402
import json                                                     # noqa: E402

record = json.loads((ROOT / "research/freeze/INSTRUMENT_FINAL_FREEZE_RECORD.json")
                    .read_text(encoding="utf-8"))
check(record["release_disposition"] == "FINAL_FREEZE_ACCEPTED",
      "the final freeze is still FINAL_FREEZE_ACCEPTED", record["release_disposition"])
check(record["freeze_candidate_commit"] == CANDIDATE,
      "the freeze record still names the same candidate")
# RESTATED BY RUN 41. The v25 freeze record is NOT rewritten - it still says v25, and that is
# asserted here rather than assumed, because a successor that edited its predecessor's record
# would destroy the evidence the predecessor is. What advances is the live stamp.
check(record["simulation_version"] == "sim-2026.08-v25",
      "the v25 freeze record still says sim-2026.08-v25 and was not rewritten by the successor",
      record["simulation_version"])
check(SIMULATION_VERSION == "sim-2026.08-v31",
      "and the live simulation version is the Run-47 successor sim-2026.08-v31",
      SIMULATION_VERSION)
# RESTATED BY RUN 43. Run 43 moves five participant-visible bytes, so v13 is superseded by v14
# and pinned to its own commit rather than rewritten. The v25 RECORD still names v13, and that
# is the correct historical statement: it is the package that release shipped. What must hold is
# that the record was not rewritten to name the successor, which is asserted directly below.
check(PP.CURRENT.identifier == "og-participant-2026.08-v16",
      "the participant package is superseded at og-participant-2026.08-v16",
      PP.CURRENT.identifier)
check(record["participant_package"] == "og-participant-2026.08-v13",
      "and the v25 freeze record still names v13, the package that release shipped, so the "
      "successor superseded it rather than rewriting it", record["participant_package"])
check(record["synthetic_package"] == "OG-SYNTH-0.6",
      "the synthetic package is unchanged at OG-SYNTH-0.6", record["synthetic_package"])

# ---- surface 4: everything Run 38 DID add, enumerated, and proved non-executable-in-production.
run38 = [ln.split("\t", 1) for ln in diff_committed(RELEASE).splitlines() if ln]
in_frozen = [p for st, p in run38
             if any(p == s or p.startswith(s + "/") for s in SURFACES)]
# RESTATED BY RUN 41, same reasoning as the surface check above: what Run 38 itself contributed
# is still required to land outside every frozen surface, and Run 41's owner-authorised successor
# changes are named rather than allowed to widen the rule.
_in_frozen_unauthorised = [p for p in in_frozen
                           if p not in AUTHORISED_SUCCESSOR_CHANGES]
check(not _in_frozen_unauthorised,
      "nothing Run 38 added or changed lands inside a frozen surface, and the only frozen-surface "
      "paths that moved since are Run 41's owner-authorised successor changes",
      "; ".join(_in_frozen_unauthorised[:10]))
# MODIFICATIONS ARE ENUMERATED, NOT FORBIDDEN WHOLESALE -- and the permitted set is named here
# so it cannot quietly grow. Run 38 is REQUIRED by its controlling specification to update
# T6_HANDOFF.md, and its two methodology documents land inside an AUTHORITY_ROOT, which forces
# the authority manifest to be repointed by the mechanism Runs 34 and 35 already used. Those are
# the only pre-existing files it may touch, and none of them is executable production or client
# code, none is named by the freeze checksum manifest, and none is inside a frozen surface --
# all three of which are asserted separately above and below.
PERMITTED_MODIFICATIONS = {
    "T6_HANDOFF.md",                       # the run is instructed to update it
    "server/tools/production_tree.py",     # repoints PINNED_AUTHORITY, Run-34/35 precedent
    # Run 39 appended an ERRATUM to the Run-38 report: its prose said the analysis dataset has
    # 58 columns, while the live ANALYSIS_COLUMNS tuple and the machine-generated Run-38
    # manifest both say 59. The report body is not rewritten; a correction is appended beneath
    # it. Named here explicitly so the addition is auditable rather than absorbed by a looser
    # check. Nothing executable, frozen, or named by the freeze checksum manifest is involved.
    "REPORT_2026-08-19_run38-study-execution-readiness.md",
} | AUTHORISED_SUCCESSOR_CHANGES | {
    # RUN 41. The owner-authorised successor also necessarily moves the pinned production-tree
    # manifest pointer and the suites that assert the superseded version stamp or that used to
    # reach a now-protected column. Each is named, none is executable production or client code
    # beyond the two files already named above, and the frozen-surface rule above still applies
    # to all of them.
    "server/tools/production_tree.py",
    "server/tools/test_run10_state_protection.py",
    "server/tools/test_run22_production_tree_completeness.py",
    "server/tools/test_run31_version_boundaries.py",
    "server/tools/test_run32_closure_version_boundary.py",
    "server/tools/test_run36_closure_guards.py",
    "server/tools/test_run36_instrument_qualification.py",
    "server/tools/test_run37_freeze_gate.py",
    "server/tools/test_run38_frozen_immutability.py",
    "server/tools/test_run39_frozen_immutability.py",
    "server/tools/test_run39_launch_gate.py",
    "server/tools/build_run37_acceptance.py",
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
} | {
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
}
modified = [p for st, p in run38 if not st.startswith("A")]
unexpected = [p for p in modified if p not in PERMITTED_MODIFICATIONS]
check(not unexpected,
      "Run 38 modified no pre-existing file outside the named permitted set",
      "; ".join(unexpected[:12]))
_manifest_modified = (set(modified) & set(manifest_paths)) - AUTHORISED_MANIFEST_CHANGES
check(not _manifest_modified,
      "and no modified file is named by the governed freeze checksum manifest, apart from "
      "Run 41's owner-authorised successor changes",
      "; ".join(sorted(_manifest_modified)[:8]))
print(f"    Run 38 changes {len(run38)} paths against the release: "
      f"{len(run38) - len(modified)} additions, {len(modified)} permitted modifications "
      f"({', '.join(sorted(modified))}), {len(in_frozen)} frozen.")

passed = sum(1 for ok, _, _ in results if ok)
print()
for ok, label, detail in results:
    if not ok:
        print(f"FAILED: {label}   {detail}")
print(f"RESULT: {passed}/{len(results)} checks passed")
sys.exit(0 if passed == len(results) else 1)
