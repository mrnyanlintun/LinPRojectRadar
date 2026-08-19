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
vs_candidate = [p for p in manifest_targets
                if git("diff", "--name-only", CANDIDATE, "--", p).strip()]
vs_release = [p for p in manifest_targets
              if git("diff", "--name-only", RELEASE, "--", p).strip()]
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
    out = git("diff", "--name-status", CANDIDATE, "--", surface).strip()
    if out:
        changed_surfaces.extend(out.splitlines())
check(not changed_surfaces,
      "the served client, the production server application, the controlled stimulus corpus "
      "and the served page are byte-identical to the freeze candidate",
      "; ".join(changed_surfaces[:12]))

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
check(SIMULATION_VERSION == "sim-2026.08-v25",
      "the simulation version is unchanged at sim-2026.08-v25", SIMULATION_VERSION)
check(record["simulation_version"] == SIMULATION_VERSION,
      "the freeze record and the code agree on the simulation version")
check(PP.CURRENT.identifier == "og-participant-2026.08-v13",
      "the participant package is unchanged at og-participant-2026.08-v13",
      PP.CURRENT.identifier)
check(record["participant_package"] == PP.CURRENT.identifier,
      "the freeze record and the package registry agree")
check(record["synthetic_package"] == "OG-SYNTH-0.6",
      "the synthetic package is unchanged at OG-SYNTH-0.6", record["synthetic_package"])

# ---- surface 4: everything Run 38 DID add, enumerated, and proved non-executable-in-production.
run38 = [ln.split("\t", 1) for ln in
         git("diff", "--name-status", RELEASE).strip().splitlines() if ln]
in_frozen = [p for st, p in run38
             if any(p == s or p.startswith(s + "/") for s in SURFACES)]
check(not in_frozen, "nothing Run 38 added or changed lands inside a frozen surface",
      "; ".join(in_frozen[:10]))
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
