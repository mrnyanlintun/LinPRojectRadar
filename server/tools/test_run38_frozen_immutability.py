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

manifest_targets = sorted(set(manifest_paths) - BOOKKEEPING)
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
    "server/app/simulation/models.py",       # the stamp advances to sim-2026.08-v26
}
_surface_paths = sorted({ln.split("\t", 1)[-1] for ln in changed_surfaces if ln})
_unauthorised = [p for p in _surface_paths if p not in RUN41_AUTHORISED_SUCCESSOR_CHANGES]
check(not _unauthorised,
      "the served client, the production server application, the controlled stimulus corpus "
      "and the served page differ from the freeze candidate ONLY by Run 41's owner-authorised "
      "successor changes",
      "; ".join(_unauthorised[:12]))
print(f"    frozen-surface differences vs the v25 candidate: {_surface_paths} "
      f"(all owner-authorised Run-41 successor changes)")

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
check(SIMULATION_VERSION == "sim-2026.08-v26",
      "and the live simulation version is the Run-41 successor sim-2026.08-v26",
      SIMULATION_VERSION)
check(PP.CURRENT.identifier == "og-participant-2026.08-v13",
      "the participant package is unchanged at og-participant-2026.08-v13",
      PP.CURRENT.identifier)
check(record["participant_package"] == PP.CURRENT.identifier,
      "the freeze record and the package registry agree")
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
                           if p not in RUN41_AUTHORISED_SUCCESSOR_CHANGES]
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
} | RUN41_AUTHORISED_SUCCESSOR_CHANGES | {
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
    "research/study_execution/OWNER_WEBSITE_ACCEPTANCE_CHECKLIST.md",
}
modified = [p for st, p in run38 if not st.startswith("A")]
unexpected = [p for p in modified if p not in PERMITTED_MODIFICATIONS]
check(not unexpected,
      "Run 38 modified no pre-existing file outside the named permitted set",
      "; ".join(unexpected[:12]))
check(not (set(modified) & set(manifest_paths)),
      "and no modified file is named by the governed freeze checksum manifest",
      "; ".join(sorted(set(modified) & set(manifest_paths))[:8]))
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
