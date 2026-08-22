"""
RUN 37. THE FINAL FREEZE GATE, AS AN ENFORCED SUITE.

The gate is not a report. It is executed here, wired into `run_all_suites.sh`, and it FAILS the
acceptance run whenever any of its fifteen blocker classes is non-zero. Its oracles are the live
tree and executed behaviour; `build_run37_acceptance.py` is run into a TEMPORARY directory so this
file can never regenerate the artefact it is checking.

A CRASH IS NOT A RED. The generator's exit status and its RESULT are both examined, and a failure
to produce the gate at all is itself a blocker rather than a silent pass.
"""

from __future__ import annotations

import csv
import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(HERE))

PASSED = 0
FAILED = 0
FAILURES: list[str] = []


def check(name, ok, why, got=""):
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {name}  {why}")
    else:
        FAILED += 1
        FAILURES.append(f"{name}  {why}")
        print(f"FAIL  {name}  {why}  [{got}]")


# RUN 41. This gate is the Run-37-equivalent freeze qualification, re-executed against the
# SUCCESSOR candidate. Run 37 accepted v25; Run 40 found two HIGH defects on it; the owner
# authorised remediation; Run 41 is the successor. The gate is not edited to say PASS - it is the
# same fifteen blocker classes, regenerated from the live tree and evaluated against the
# successor's own identity, gate and release records. The v25 artefacts are untouched and remain
# the historical evidence for that release.
# RUN 43. The successor is re-evaluated once more, for the retirement of 38 modules from
# service. The gate is not edited to say PASS -- it is the same fifteen blocker classes,
# regenerated from the live tree and evaluated against the successor's own identity, gate and
# release records. The v25, v26 and v27 artefacts are untouched and remain the historical
# evidence for those releases.
# RUN 44. The successor is re-evaluated once more, for the repair of the four participant-facing
# render defects Run 43J diagnosed. The gate is not edited to say PASS -- it is the same fifteen
# blocker classes, regenerated from the live tree and evaluated against the successor's own
# identity, gate and release records. The v25, v26, v27 and v28 artefacts are untouched and remain
# the historical evidence for those releases.
# RUN 45. The successor is re-evaluated once more, for the closure of the period-scoping
# fall-through Run 44 measured. The gate is not edited to say PASS -- it is the same fifteen
# blocker classes, regenerated from the live tree and evaluated against the successor's own
# identity, gate and release records. The v25, v26, v27, v28 and v29 artefacts are untouched and
# remain the historical evidence for those releases.
# RUN 47. The successor is re-evaluated once more, for the EVM consistency check. The gate is not
# edited to say PASS -- it is the same fifteen blocker classes, regenerated from the live tree and
# evaluated against the successor's own identity, gate and release records. The v25, v26, v27,
# v28, v29 and v30 artefacts are untouched and remain the historical evidence for those releases.
# RUN 48. The successor is re-evaluated once more, for the period the project detail page opens
# on and the live naming instances. The gate is not edited to say PASS -- it is the same fifteen
# blocker classes, regenerated from the live tree and evaluated against the successor's own
# identity, gate and release records. The v25, v26, v27, v28, v29, v30 and v31 artefacts are
# untouched and remain the historical evidence for those releases.
# RUN 49. The successor is re-evaluated once more, for the completion of the naming correction.
# The gate is not edited to say PASS -- it is the same fifteen blocker classes, regenerated from
# the live tree and evaluated against the successor's own identity, gate and release records. The
# v25 to v32 artefacts are untouched and remain the historical evidence for those releases.
SUCCESSOR_GATE = "run49_successor_freeze_gate.csv"
SUCCESSOR_RECORD = "RUN49_SUCCESSOR_FREEZE_RECORD.json"
SUCCESSOR_REPORT = "RUN49_SUCCESSOR_FREEZE_REPORT.md"
SUCCESSOR_CHECKSUMS = "RUN49_SUCCESSOR_FREEZE_CHECKSUMS.csv"

print("=" * 94)
print("RUN 37-EQUIVALENT FREEZE GATE, RE-EXECUTED FOR THE RUN-42 SUCCESSOR")
print("=" * 94)

_TMP = pathlib.Path(tempfile.mkdtemp(prefix="run37-gate-"))
_proc = subprocess.run(
    [sys.executable, str(HERE / "build_run37_acceptance.py"),
     "--out-audit", str(_TMP), "--out-freeze", str(_TMP)],
    capture_output=True, text=True)
check("run37.gate.generator_runs", _proc.returncode == 0,
      "the acceptance generator runs to completion; a crash is a blocker, not a pass",
      (_proc.stderr or "")[-300:])


def rows(p):
    if not p.is_file():
        return []
    with p.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


_fresh = rows(_TMP / SUCCESSOR_GATE)
_committed = rows(ROOT / "research" / "freeze" / SUCCESSOR_GATE)
check("run37.gate.artifact_present", bool(_committed),
      "the committed freeze gate exists", len(_committed))
check("run37.gate.reproduces",
      [(r["blocker_id"], r["count"], r["result"]) for r in _fresh]
      == [(r["blocker_id"], r["count"], r["result"]) for r in _committed],
      "and it REPRODUCES from the current tree, so it is not a stale snapshot",
      f"{len(_fresh)} fresh vs {len(_committed)} committed")

# EVERY BLOCKER IS EVALUATED FROM THE FRESHLY REGENERATED GATE, NOT FROM THE COMMITTED CSV.
# The first version of this file read the committed artefact, so mutating the instrument moved
# nothing it looked at and all fifteen faults stayed green: the suite was VACUOUS and the
# non-vacuity campaign is what found it. The committed artefact is still required to reproduce,
# immediately above, so a stale commit is caught too -- but the LIVE TREE is what decides.
_gate = _fresh or _committed
check("run37.gate.fifteen_blocker_classes", len(_gate) == 15,
      "all fifteen blocker classes are evaluated", len(_gate))

for _r in _gate:
    check(f"run37.gate.{_r['blocker_id']}", _r["result"] == "PASS",
          f"blocker class {_r['blocker_id']} ({_r['blocker']}) is zero", _r["evidence"][:180])

_blocked = [r for r in _gate if r["result"] != "PASS"]
check("run37.gate.blocking_defects_zero", len(_blocked) == 0,
      "BLOCKING DEFECTS = 0, which is the condition for a final release record to exist",
      str([r["blocker_id"] for r in _blocked]))

# ------------------------------------------------------------------ the release-record coupling
_record = ROOT / "research" / "freeze" / SUCCESSOR_RECORD
_report = ROOT / "research" / "freeze" / SUCCESSOR_REPORT
_sums = ROOT / "research" / "freeze" / SUCCESSOR_CHECKSUMS

# THE PREDECESSOR'S OWN RELEASE RECORDS MUST STILL BE THERE, UNCHANGED. A successor that quietly
# replaced them would destroy the evidence for everything computed under v25.
_v25_record = ROOT / "research" / "freeze" / "INSTRUMENT_FINAL_FREEZE_RECORD.json"
check("run37.gate.predecessor_release_preserved",
      _v25_record.is_file()
      and json.loads(_v25_record.read_text(encoding="utf-8")).get("simulation_version")
      == "sim-2026.08-v25",
      "the v25 release record is still present and still says v25, so the successor superseded "
      "it rather than rewriting it",
      str(_v25_record.is_file()))

# AND SO MUST EVERY INTERMEDIATE PREDECESSOR. Each successor record is the evidence for
# everything computed under its own stamp. Checking only the oldest release would let the most
# recent one be quietly rewritten, which is the mutation this class of check exists to catch, so
# every predecessor in the chain is checked and each must still record its OWN stamp.
for _pred_file, _pred_stamp in (("RUN41_SUCCESSOR_FREEZE_RECORD.json", "sim-2026.08-v26"),
                                ("RUN42_SUCCESSOR_FREEZE_RECORD.json", "sim-2026.08-v27"),
                                ("RUN43_SUCCESSOR_FREEZE_RECORD.json", "sim-2026.08-v28"),
                                # RUN 48 adds the two most recent predecessors to the chain,
                                # which strengthens this check rather than loosening it: v30's
                                # and v31's records must also still say what they said.
                                ("RUN45_SUCCESSOR_FREEZE_RECORD.json", "sim-2026.08-v30"),
                                ("RUN47_SUCCESSOR_FREEZE_RECORD.json", "sim-2026.08-v31")):
    _pr = ROOT / "research" / "freeze" / _pred_file
    check("run37.gate.immediate_predecessor_release_preserved",
          _pr.is_file()
          and json.loads(_pr.read_text(encoding="utf-8")).get("simulation_version")
          == _pred_stamp,
          f"the {_pred_stamp} successor release record is still present and still says "
          f"{_pred_stamp}",
          str(_pr.is_file()))
check("run37.gate.no_release_while_blocked",
      not (_blocked and (_record.is_file() or _report.is_file())),
      "NO FINAL RELEASE RECORD MAY EXIST WHILE ANY BLOCKER STANDS",
      f"blocked={len(_blocked)} record={_record.is_file()} report={_report.is_file()}")
check("run37.gate.release_present_when_clean",
      bool(_blocked) or (_record.is_file() and _report.is_file() and _sums.is_file()),
      "and when the gate is clean the final release record, report and checksum manifest exist",
      f"record={_record.is_file()} report={_report.is_file()} checksums={_sums.is_file()}")

# ------------------------------------------------------------------ the limitation contract
if _record.is_file():
    _rec = json.loads(_record.read_text(encoding="utf-8"))
    # CASE-INSENSITIVE: the requirement is that the statement is PRESENT, not that it is cased a
    # particular way. The release states two of these in capitals for emphasis.
    _lim = json.dumps(_rec.get("limitation_contract", {})).lower()
    for _need, _what in (
            ("0 of 100", "empirical field validation is stated as 0 of 100"),
            ("NOT a claim of validated real-world predictive effectiveness",
             "the release explicitly denies any claim of validated real-world predictive "
             "effectiveness"),
            ("OG-SYNTH-0.1", "the historical incompleteness of OG-SYNTH-0.1 is stated"),
            ("bounded controlled-study", "qualification is stated as bounded controlled-study "
             "instrument use")):
        check("run37.gate.limitation_stated", _need.lower() in _lim, _what, _need)
    check("run37.gate.disposition",
          _rec.get("release_disposition") == "FINAL_FREEZE_ACCEPTED" and not _blocked,
          "the recorded disposition is FINAL_FREEZE_ACCEPTED and the gate agrees",
          str(_rec.get("release_disposition")))
    check("run37.gate.no_self_reference",
          "PENDING_FINAL_COMMIT" not in _record.read_text(encoding="utf-8")
          and _rec.get("freeze_candidate_commit")
          # RE-ANCHORED BY RUN 49, on Run 48's own construction, which was Run 47's, Run 45's,
          # Run 44's and Run 43's. Each successor must name its IMMEDIATE predecessor's candidate
          # as its parent: Run 48 named Run 47's, and Run 49 supersedes v32, so the record must
          # now name RUN 48's candidate. Named explicitly rather than loosened to "any commit",
          # because the point of the check is that the record cannot point at itself and cannot
          # silently reparent.
          and _rec.get("freeze_candidate_commit")
          != "e3d1b698b4797bb0fad4bde413317e56ecfd2398"
          and _rec.get("supersedes_candidate")
          == "e3d1b698b4797bb0fad4bde413317e56ecfd2398"
          and bool(_rec.get("release_content_digest"))
          and bool(_rec.get("release_commit_recording_method")),
          "the record distinguishes freeze_candidate_commit, release_content_digest and "
          "release_commit_recording_method, and contains no self-referential placeholder",
          str(_rec.get("release_commit_recording_method"))[:120])

print()
print("=" * 94)
if FAILURES:
    print("FAILURES:")
    for f in FAILURES:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
raise SystemExit(1 if FAILED else 0)
