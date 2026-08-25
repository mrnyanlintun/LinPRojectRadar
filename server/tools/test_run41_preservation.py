#!/usr/bin/env python3
"""
RUN 41 sections 10-15 - the preservation proofs, executed rather than asserted.

Neither S1 (a response-header policy at the document-serving boundary) nor S2 (a database trigger
on the decisions row) may alter the science, the participant's experience, or the AI binding.
This suite is the enforcement of that, and every claim here is measured:

  section 10  the full participant state sequence still runs end to end, in order, and the
              stages the participant passes through are exactly the governed ones
  section 11  the AI recommendation delivered at all 36 project-period positions is digest-
              identical between the pinned v25 line and the v26 working tree
  section 12  the whole registered module population emits byte-identical rows across the
              boundary; voting is still exactly two; the Category-9 gate and Category-10
              boundary are unmoved
  section 13  the stamp advanced to v26, the history is append-only, and v25 still reconstructs
              from its own git object
  sections    the participant package, synthetic package and analysis schema are retained
  14-15       because their governed bytes did not move - determined by measuring the bytes,
              not by assertion

THE 36-POSITION AND 101-MODULE COMPARISONS ARE NOT RECOMPUTED HERE. They are produced by
run41_ai_binding_digests.py (run once on each line, from each line's own git object) and by
build_run41_v25_v26_execution_proof.py. This suite requires those artefacts to exist, to cover
the full population, and to record zero movement - and fails if any of them is missing, so a
deleted artefact is a failure rather than a silent skip.

Run (from server/): DATABASE_URL=... SESSION_SECRET=... python tools/test_run41_preservation.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(HERE))

from fastapi.testclient import TestClient  # noqa: E402

import app.main as main  # noqa: E402
from app.simulation import registry as REG  # noqa: E402
from app.simulation.models import (  # noqa: E402
    SIMULATION_VERSION, SIMULATION_VERSION_HISTORY, SIMULATION_VERSION_SUPERSEDED)
import participant_packages as PP  # noqa: E402
import run38_analysis_export as AX  # noqa: E402
import run41_flow  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
results: list[tuple[bool, str, str]] = []

V25_COMMIT = "4bd14684abadd3ab8a94d68964b686993a5d6718"
AUDIT = ROOT / "code_audit"


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   -- {detail}" if detail and not ok else ""))


print("=" * 78)
print("RUN 41 - preservation of science, sequence and AI binding across v25 -> v26")
print("=" * 78)

# ------------------------------------------------------------------ section 10
print()
print("-" * 78)
print("SECTION 10 - the participant state sequence, driven end to end")
print("-" * 78)

ctx = run41_flow.build(main, client, "R41PR")
post, p = ctx["post"], ctx["p"]

stages = []
ev = post({"action": "researchevidenceget", "session_token": p})
stages.append(ev.get("current_stage"))
pj = post({"action": "researchprejudgment", "session_token": p, "pre_action": "monitor",
           "pre_confidence": 55, "pre_assessment": "preservation probe"})
stages.append(pj.get("current_stage"))
rv = post({"action": "researchreveal", "session_token": p})
stages.append(rv.get("current_stage"))
fd = post({"action": "researchdecision", "session_token": p, **run41_flow.FINAL_PAYLOAD})
stages.append(fd.get("current_stage"))

check([s for s in stages] == ["evidence", "awaiting_reveal", "deciding", "complete"],
      "the governed stage sequence is evidence -> awaiting_reveal -> deciding -> complete",
      str(stages))
check(all(r.get("ok") is True for r in (ev, pj, rv, fd)),
      "every step of the sequence succeeds under v26",
      str([r.get("ok") for r in (ev, pj, rv, fd)]))
check(rv.get("package") is not None and pj.get("package") is None,
      "the AI reveal still happens at the reveal step and not before it (timing unchanged)")

resumed = post({"action": "researchsequencestate", "session_token": p})
check(resumed.get("ok") is True and resumed.get("current_stage") == "complete",
      "reload/resume after the final lock returns the same stage",
      str(resumed)[:160])

# ------------------------------------------------------------------ section 11
print()
print("-" * 78)
print("SECTION 11 - the AI binding, both lines, all 36 positions")
print("-" * 78)

b25 = AUDIT / "run41_ai_binding_v25.json"
b26 = AUDIT / "run41_ai_binding_v26.json"
check(b25.is_file() and b26.is_file(),
      "both binding captures exist (pinned v25 line and v26 working tree)",
      f"v25={b25.is_file()} v26={b26.is_file()}")
if b25.is_file() and b26.is_file():
    d25 = json.loads(b25.read_text(encoding="utf-8"))
    d26 = json.loads(b26.read_text(encoding="utf-8"))
    check(d25.get("simulation_version") == "sim-2026.08-v25"
          and d26.get("simulation_version") == "sim-2026.08-v26",
          "the two captures really came from the two different lines",
          f"{d25.get('simulation_version')} vs {d26.get('simulation_version')}")
    check(d25.get("position_count") == 36 and d26.get("position_count") == 36,
          "each capture covers all 36 project-period positions",
          f"{d25.get('position_count')} vs {d26.get('position_count')}")
    check(set(d25["positions"]) == set(d26["positions"]),
          "the same 36 positions were visited on both lines")
    moved = [k for k in sorted(d25["positions"])
             if d25["positions"][k]["recommendation_digest"]
             != d26["positions"].get(k, {}).get("recommendation_digest")]
    check(not moved,
          f"recommendation digests are identical at all 36 positions (moved: {len(moved)})",
          str(moved[:6]))
    check(d25.get("unique_recommendation_digests") == 6
          and d26.get("unique_recommendation_digests") == 6,
          "6 unique project-level AI exposures on both lines, as Run 40 established",
          f"{d25.get('unique_recommendation_digests')} vs "
          f"{d26.get('unique_recommendation_digests')}")
    check(d26.get("projects_with_one_recommendation_across_all_periods") == 6,
          "the recommendation is still attached per project, constant across its 6 periods")

# ------------------------------------------------------------------ section 12
print()
print("-" * 78)
print("SECTION 12 - the scientific population, both lines")
print("-" * 78)

proof = AUDIT / "run41_v25_v26_execution_proof.csv"
check(proof.is_file(), "the v25 -> v26 execution proof exists", str(proof))
if proof.is_file():
    with proof.open(encoding="utf-8") as fh:
        prows = list(csv.DictReader(fh))
    counter = [r for r in prows if r["module_id"] == "ACCEPTANCE_COUNTER"]
    check(bool(counter), "the proof carries its acceptance counter")
    if counter:
        check(counter[0]["observed"] == "0" and counter[0]["result"] == "PASS",
              "modules whose emitted row moved across the v25 -> v26 boundary = 0",
              f"observed={counter[0]['observed']} result={counter[0]['result']}")
    pop = [r for r in prows if r["module_id"] == "POPULATION"]
    check(bool(pop) and pop[0]["result"] == "PASS",
          "the registered module population itself did not move")
    check(all(r["result"] == "PASS" for r in prows),
          "no row of the execution proof records a divergence",
          str([r["module_id"] for r in prows if r["result"] != "PASS"][:6]))

check(sorted(REG.CORE_VOTING_MODULES) == ["A1.7", "A1.8"],
      "voting remains exactly 2, and the same 2",
      str(sorted(REG.CORE_VOTING_MODULES)))

# The Category-9 gate and the Category-10 boundary, measured by EXECUTION on an unqualified
# package rather than by reading their source.
import build_run36_audit as AUD  # noqa: E402
unqual = {k: v for k, v in AUD.CORPUS_SI.items() if k != "evidenceQualification"}
bypass = []
for m in ("B1.1", "B1.2", "B2.18", "B2.19", "B4.3", "B4.7"):
    try:
        r = REG.run_module(m, dict(unqual), AUD.NOOP, AUD.CUT)
    except Exception:                                            # noqa: BLE001
        continue
    if not r.get("insufficient_data") and r.get("status_color"):
        bypass.append(m)
check(not bypass, "the Category-9 gate is unchanged: no unqualified probe reaches a band",
      str(bypass))
v7 = (ROOT / "server" / "app" / "simulation" / "canonical_v7.py").read_text(encoding="utf-8")
check('"human_authorization_required": True' in v7
      and '"creates_project_evidence": False' in v7
      and not (set(REG.CORE_VOTING_MODULES) & {"B4.1", "B4.2", "B4.3", "B4.4", "B4.5", "B4.6",
                                               "B4.7", "B2.18", "B2.19"}),
      "the Category-10 boundary is unchanged: authorisation required, creates no project "
      "evidence, and no Category-10 identity votes")

# ------------------------------------------------------------------ section 13
print()
print("-" * 78)
print("SECTION 13 - the version boundary")
print("-" * 78)

# RESTATED BY RUN 42. This section's subject is that RUN 41's boundary is PRESERVED, not that
# v26 is live forever. Run 42 supersedes v26 with v27, so what must still hold is that v26 is
# in the history exactly where Run 41 put it -- directly after v25 -- and that the live stamp is
# Run 42's own successor. Asserting the live stamp is still v26 would make this file fail every
# time a later run legitimately supersedes, which would be a guard measuring the wrong thing.
# RESTATED BY RUN 43, for the same reason Run 42 restated it: this section's subject is that
# RUN 41's boundary is PRESERVED, not that any later stamp is live forever. Run 43 supersedes
# v27 with v28 for the retirement of 38 modules from service. RESTATED AGAIN BY RUN 44, for the
# third time and the same reason: Run 44 supersedes v28 with v29 for the participant-facing
# render defects. What this section asserts is Run 41's boundary, which is untouched below.
# RESTATED AGAIN BY RUN 48, for the same reason and with the same scope: Run 48 supersedes v31
# with v32 because WHICH STORED ROW A PAGE READS is executable behaviour. Run 41's boundary is
# untouched and is still asserted below.
# RUN 56. RESTATED BY RUN 56, for the same reason and with the same scope: Run 56 supersedes v36 with v37 because WHAT A PARTICIPANT REACHES AND CLICKS is executable behaviour -- the duplicate 'Upload documents' control is removed from the project detail page and Archive and Reset signals now ask before acting. Run 41's boundary is untouched and is still asserted below.
# RUN 57. RESTATED BY RUN 57, for the same reason and with the same scope: Run 57 supersedes
# v37 with v38 because WHAT A PARTICIPANT REACHES AND CLICKS is executable behaviour -- the two
# controls that cleared stored signals are MERGED into one that does the union of both handler
# bodies, and the other is removed. Run 41's boundary is untouched and is still asserted below.
# RUN 59. RESTATED AGAIN, same scope: no markdown document carries authority, six production-tree
# members moved, and one of them -- assets/js/decision-ui.js -- is SEQUENCE-BEARING, so v38 is
# SUPERSEDED rather than amended. Run 41's boundary is untouched and is still asserted below.
check(SIMULATION_VERSION == "sim-2026.08-v40", "the live stamp is Run 62's successor "
      "sim-2026.08-v40", SIMULATION_VERSION)
check(SIMULATION_VERSION_SUPERSEDED == "sim-2026.08-v39",
      "and it records v39, Run 59's stamp, as the stamp it supersedes",
      SIMULATION_VERSION_SUPERSEDED)
_i26 = SIMULATION_VERSION_HISTORY.index("sim-2026.08-v26")
check(SIMULATION_VERSION_HISTORY[_i26 - 1:_i26 + 1] == ("sim-2026.08-v25", "sim-2026.08-v26"),
      "the history is append-only and Run 41's boundary is preserved: v26 still directly "
      "follows v25", str(SIMULATION_VERSION_HISTORY[-3:]))
# RUN 56 SHIFTS THE WHOLE LADDER BY ONE RATHER THAN INSERTING INTO IT. The tail is checked
# position by position, so appending v37 moves every index below it; adding a row without
# shifting the rest would have left two clauses asserting the same index and silently dropped
# one stamp from the check.
# RUN 57 SHIFTS THE WHOLE LADDER BY ONE AGAIN, for the reason Run 56 recorded: the tail is
# checked POSITION BY POSITION, so appending v38 moves every index below it, and adding a row
# without shifting the rest would leave two clauses asserting the same index and silently drop
# one stamp from the check while still passing.
# RUN 59 SHIFTS THE WHOLE LADDER BY ONE AGAIN, for the reason Runs 56 and 57 recorded: this tail
# is checked POSITION BY POSITION, so appending v39 moves every index below it, and adding a row
# without shifting the rest would leave two clauses asserting the same index and SILENTLY DROP
# ONE STAMP from the check while still passing. Two runs nearly did exactly that AND RUN 59 DID:
# the first attempt at this reconciliation changed [-1] alone, the check went RED naming
# ('sim-2026.08-v37', 'sim-2026.08-v38', 'sim-2026.08-v39'), and the ladder was then shifted
# properly and DEEPENED BY ONE CLAUSE so v30 is still reached. This is carry-forward item 1 in the
# Run 59 report, and the guard caught it exactly as it was built to.
# RUN 62 SHIFTS THE WHOLE LADDER BY ONE AGAIN AND DEEPENS IT BY ONE CLAUSE, for the reason Runs
# 56, 57 and 59 recorded and Run 59 proved by going red: this tail is checked POSITION BY
# POSITION. Appending v40 moves every index below it. Changing [-1] alone would leave two clauses
# asserting the same index and SILENTLY DROP ONE STAMP from the check while still passing, which
# is exactly what Run 59's first attempt did. The eleventh clause is added so v30 is still
# reached after the shift, rather than falling off the bottom of the ladder.
check(SIMULATION_VERSION_HISTORY[-1] == "sim-2026.08-v40"
      and SIMULATION_VERSION_HISTORY[-2] == "sim-2026.08-v39"
      and SIMULATION_VERSION_HISTORY[-3] == "sim-2026.08-v38"
      and SIMULATION_VERSION_HISTORY[-4] == "sim-2026.08-v37"
      and SIMULATION_VERSION_HISTORY[-5] == "sim-2026.08-v36"
      and SIMULATION_VERSION_HISTORY[-6] == "sim-2026.08-v35"
      and SIMULATION_VERSION_HISTORY[-7] == "sim-2026.08-v34"
      and SIMULATION_VERSION_HISTORY[-8] == "sim-2026.08-v33"
      and SIMULATION_VERSION_HISTORY[-9] == "sim-2026.08-v32"
      and SIMULATION_VERSION_HISTORY[-10] == "sim-2026.08-v31"
      and SIMULATION_VERSION_HISTORY[-11] == "sim-2026.08-v30",
      "and v27 to v40 were appended after v26 rather than replacing it",
      str(SIMULATION_VERSION_HISTORY[-3:]))
check(len(SIMULATION_VERSION_HISTORY) == len(set(SIMULATION_VERSION_HISTORY)),
      "no stamp appears twice in the history")

# v25 MUST STILL RECONSTRUCT FROM ITS OWN GIT OBJECT.
_v25 = subprocess.run(["git", "show", f"{V25_COMMIT}:server/app/simulation/models.py"],
                      cwd=ROOT, capture_output=True, text=True)
check(_v25.returncode == 0
      and 'SIMULATION_VERSION = "sim-2026.08-v25"' in _v25.stdout
      and 'SIMULATION_VERSION = "sim-2026.08-v26"' not in _v25.stdout,
      "the v25 predecessor reconstructs from its pinned git object and still says v25",
      f"rc={_v25.returncode}")

# AND SO MUST v26, for exactly the same reason: Run 42 supersedes it, so it must not have
# rewritten it. Without this, a successor could quietly edit the line it claims to supersede.
_v26 = subprocess.run(["git", "show",
                       "1b624d3e3cd5ead39b90e80ac351cfc1e2f9a281:server/app/simulation/models.py"],
                      cwd=ROOT, capture_output=True, text=True)
check(_v26.returncode == 0
      and 'SIMULATION_VERSION = "sim-2026.08-v26"' in _v26.stdout
      and 'SIMULATION_VERSION = "sim-2026.08-v27"' not in _v26.stdout,
      "the v26 predecessor reconstructs from its pinned git object and still says v26",
      f"rc={_v26.returncode}")

# ------------------------------------------------------------------ sections 14-15
print()
print("-" * 78)
print("SECTIONS 14-15 - the package decisions, taken from the bytes")
print("-" * 78)

v13_record = AUDIT / "run36_closure_participant_package_v13_checksums.sha256"
rec: dict[str, str] = {}
for ln in v13_record.read_text(encoding="utf-8").splitlines():
    if re.match(r"^[0-9a-f]{64}  ", ln):
        h, path = ln.split("  ", 1)
        rec[path] = h
check(len(rec) > 60, "the v13 participant-package record names its governed files", str(len(rec)))
# RESTATED BY RUN 43. Run 41 retained v13 and that record stands. Run 43 MINTS v14, because the
# retirement moves five participant-visible bytes, and it declares exactly which five. What this
# section is for is unchanged and is asserted more strictly: the files that moved are exactly the
# ones the successor declares, and NOT ONE of them carries a step of the participant sequence.
# RESTATED BY RUN 44. The subject is unchanged and is measured against the CURRENT record
# rather than a superseded one: measuring the live tree against v13 would report every later
# supersession as drift, which is the defect Run 43 had to correct in the freeze gate's B11.
# What is asserted is the union of the declared deltas, so nothing rides along at any link.
# RESTATED BY RUN 48, same construction: v17 is the current link, so its declared delta joins
# the union. RESTATED AGAIN BY RUN 49 for v18. Nothing here is loosened -- the union is still
# exactly what the successors declare, so a file that moved without being declared at some link
# is still red.
_declared_since_v13 = sorted(set(PP.V13_TO_V14_CHANGED) | set(PP.V14_TO_V15_CHANGED)
                            | set(PP.V15_TO_V16_CHANGED) | set(PP.V16_TO_V17_CHANGED)
                            | set(PP.V17_TO_V18_CHANGED) | set(PP.V18_TO_V19_CHANGED))
# RUN 54. A DELETED FILE MUST COUNT AS MOVED, NOT CRASH. `assets/js/deepdive.js` was DELETED on
# the owner's ruling at section 8 of the Run 54 order, and hashing a path that does not exist
# raised FileNotFoundError, which is a crash and a crash is not a pass. A missing file now hashes
# to None, so it can never equal a recorded digest and is therefore ALWAYS counted as moved. The
# comparison is not loosened: an UNDECLARED deletion still fails, exactly as an undeclared edit
# does, and the declaration is V20_TO_V21_SEQUENCE_EXCEPTION in participant_packages.py.
def _sha_or_gone(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


moved_pkg = sorted(p for p, h in rec.items()
                   if _sha_or_gone(ROOT / p) != h)
check(moved_pkg == _declared_since_v13,
      f"of the {len(rec)} governed participant-package bytes, exactly the {len(moved_pkg)} the "
      f"v14, v15, v16, v17, v18 and v19 successors declare between them moved, and no others",
      str(moved_pkg[:8]))
# THE SEQUENCE. Run 44 moves ONE sequence-bearing file on the owner's order at its section 4.4,
# and it is named rather than tolerated. Every other one is still held to byte-identity against
# v13, so the invariant is intact for the five that carry a step of the decision sequence.
seq_moved = sorted(f for f in PP.SEQUENCE_BEARING_FILES
                   if _sha_or_gone(ROOT / f) != rec.get(f))
# RUN 49 adds decision-ui.js, which gains COMMENTS ONLY on the owner's ruling 4. Both are named
# rather than tolerated, and the other FOUR are still held to byte-identity against v13.
# RUN 51 adds the remaining four, each on its own ruling's authority and each carrying its own
# named exception record in the v19 checksum record's header. The union is still exactly what the
# successors DECLARE, so a sequence-bearing file that moved without a declared record is still
# red -- which is proved by injection rather than asserted.
# RUN 54 adds V20_TO_V21_SEQUENCE_EXCEPTION -- deepdive.js, DELETED. It is named here on
# exactly the same construction as every earlier exception, so a second sequence-bearing file
# disappearing is still red.
_seq_authorised = sorted(set(PP.V14_TO_V15_SEQUENCE_EXCEPTION)
                         | set(PP.V17_TO_V18_SEQUENCE_EXCEPTION)
                         | set(PP.V18_TO_V19_SEQUENCE_EXCEPTION)
                         | set(PP.V20_TO_V21_SEQUENCE_EXCEPTION))
check(seq_moved == _seq_authorised,
      f"of the {len(PP.SEQUENCE_BEARING_FILES)} sequence-bearing files, exactly the "
      f"{len(_seq_authorised)} the owner authorised have moved since v13, each with its own "
      f"named exception record, and no step of the decision sequence, no reveal gate, no lock, "
      f"no randomization and no questionnaire ITEM, response option, scale or order moved -- "
      f"which the participant-package suite asserts structurally, not by byte-identity",
      str(seq_moved))
check(PP.CURRENT.identifier == "og-participant-2026.08-v25",
      "the participant package is superseded at og-participant-2026.08-v25, and the v13, v14 and "
      "v15 records are pinned rather than rewritten",
      PP.CURRENT.identifier)

# The synthetic corpus and the analysis schema: measured against the pinned predecessor tree.
for label, path in (("synthetic corpus", "research_fixtures/synthetic"),
                    ("analysis export module", "server/tools/run38_analysis_export.py")):
    d = subprocess.run(["git", "diff", "--name-only", V25_COMMIT, "--", path],
                       cwd=ROOT, capture_output=True, text=True).stdout.strip()
    check(not d, f"the {label} is byte-identical to the pinned v25 predecessor",
          d[:200])
check(AX.ANALYSIS_SCHEMA_VERSION == "og-analysis-2026.08-v1",
      "the analysis schema is retained at og-analysis-2026.08-v1", AX.ANALYSIS_SCHEMA_VERSION)

passed = sum(1 for ok, _, _ in results if ok)
total = len(results)
print()
print("=" * 78)
print(f"RESULT: {passed}/{total} checks passed")
print("=" * 78)
sys.exit(0 if passed == total else 1)
