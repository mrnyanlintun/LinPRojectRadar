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
check(not changed_surfaces,
      "the production server application, the participant/client assets, the served page, the "
      "controlled stimuli, the frozen methodology specification and the participant sequence "
      "authority are all byte-identical to the freeze candidate",
      "; ".join(changed_surfaces[:12]))

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
targets = sorted(set(manifest_paths) - BOOKKEEPING)
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
check(SIMULATION_VERSION == "sim-2026.08-v25",
      "the simulation is unchanged at sim-2026.08-v25", SIMULATION_VERSION)
check(PP.CURRENT.identifier == "og-participant-2026.08-v13",
      "the participant package is unchanged at og-participant-2026.08-v13",
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
    "T6_HANDOFF.md",
    "REPORT_2026-08-19_run38-study-execution-readiness.md",
    "server/tools/test_run38_frozen_immutability.py",
    # Repoints PINNED_AUTHORITY to code_audit/run39_authority_tree.sha256, because Run 39's
    # dataset-classification contract lands inside an AUTHORITY_ROOT. Run-34, 35 and 38
    # precedent; prior manifests stay addressable.
    "server/tools/production_tree.py",
}
run39 = [ln.split("\t", 1) for ln in diff_committed(RUN38_READY).splitlines() if ln]
in_frozen = [p for st, p in run39
             if any(p == s or p.startswith(s + "/") for s in SURFACES)]
check(not in_frozen, "nothing Run 39 added or changed lands inside a frozen surface",
      "; ".join(in_frozen[:10]))

modified = [p for st, p in run39 if not st.startswith("A")]
unexpected = [p for p in modified if p not in PERMITTED_MODIFICATIONS]
check(not unexpected, "Run 39 modified no pre-existing file outside the named permitted set",
      "; ".join(unexpected[:12]))
check(not (set(modified) & set(manifest_paths)),
      "and no modified file is named by the governed freeze checksum manifest",
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
