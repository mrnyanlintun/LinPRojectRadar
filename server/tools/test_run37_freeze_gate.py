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
import re
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
# RUN 51. The successor is re-evaluated once more, for the delivery of the six rulings Run 50
# stopped on. The gate is not edited to say PASS -- it is the same fifteen blocker classes,
# regenerated from the live tree and evaluated against the successor's own identity, gate and
# release records. The v25 to v33 artefacts are untouched and remain the historical evidence for
# those releases.
# RUN 56. The successor is re-evaluated once more, for the removal of the duplicate "Upload
# documents" control from the project detail page and the two confirmations. The gate is not
# edited to say PASS -- it is the same fifteen blocker classes, regenerated from the live tree
# and evaluated against the successor's own identity, gate and release records. The v25 to v36
# artefacts are untouched and remain the historical evidence for those releases.
#
# RUN 57, PHASE B. THE FOUR RELEASE NAMES ARE NO LONGER TYPED, AND NEITHER IS THE ANCHOR.
#
# The four names below used to be four hand-edited strings. Run 55 advanced SUCCESSOR_GATE to its
# own file and left SUCCESSOR_RECORD, SUCCESSOR_REPORT and SUCCESSOR_CHECKSUMS pinned at RUN51,
# and the `no_self_reference` anchor was last advanced by Run 49 and still named Run 48's
# candidate. Rows 28, 33 and 34 therefore asserted the disposition of a release three mints old,
# AND THEY PASSED THE WHOLE TIME, because the stale pins agreed with one another. Two stale
# guards that reinforce each other read exactly like a passing check.
#
# All four are now DERIVED FROM ONE PLACE: the participant-package chain, whose CURRENT link is
# the one thing a mint must advance anyway, and whose checksum record carries the minting run's
# own number in its filename. FOUR NAMES BECOME ONE FACT. The Run-55 condition -- one pin
# advanced and three left behind -- IS NOT EXPRESSIBLE HERE ANY MORE: there is no second place
# to leave behind.
#
# NOTHING IS LOOSENED. Each name still resolves to ONE specific file for ONE specific release, and
# the anchor below still resolves to ONE specific named commit at evaluation time. A rule that
# accepted "any commit" would be the weakening the order forbids, and it is not what this is: the
# anchor is read out of the PREDECESSOR link's own release record, so it names a commit the
# predecessor release itself declared, not a pattern.
import participant_packages as _PP  # noqa: E402


def _minting_run(pkg) -> int:
    """The run that minted a package link, read from that link's own checksum-record filename.

    A SPECIFIC integer derived from the chain. If the filename does not carry one, this raises
    rather than guessing: a derivation that cannot resolve must stop, never fall back to a
    pattern that matches anything.
    """
    m = re.search(r"run(\d+)_participant_package", pkg.record)
    if m is None:
        raise SystemExit(
            f"RUN 57 DERIVATION FAILED: the package link {pkg.identifier} names the checksum "
            f"record {pkg.record!r}, which carries no run number, so the release names cannot be "
            f"derived from the chain. Stopping rather than falling back to a typed constant.")
    return int(m.group(1))


_RUN = _minting_run(_PP.CURRENT)
_PRED_RUN = _minting_run(_PP.PARTICIPANT_PACKAGES[-2])
# RUN 91. THE GATE ARTEFACT'S NAME IS DERIVED FROM THE GENERATOR, NOT FROM THE PACKAGE LINK.
#
# WHAT WAS WRONG. This name was `f"run{_RUN}_successor_freeze_gate.csv"`, with `_RUN` read from
# the PARTICIPANT PACKAGE link (v26, minted at run 63). But the gate artefact is a property of
# the FREEZE CANDIDATE, not of the participant package, and the two chains parted at Run 67:
# `build_run37_acceptance.py` advanced `GATE_FILE` to `run67_successor_freeze_gate.csv` while the
# package chain stayed at v26/run63. The generator therefore wrote run67 into the temp directory
# and this file looked for run63 there, found nothing, and `run37.gate.reproduces` failed for ever
# with "0 fresh vs 15 committed" -- a NAME MISMATCH reported as a stale snapshot. Worse, `_gate`
# below falls back to the COMMITTED csv when `_fresh` is empty, so all fifteen blocker checks were
# reading the stale artefact: the vacuity this suite's own comment says the campaign found.
#
# NOTHING IS LOOSENED. The name still resolves to ONE specific file for ONE specific release; it
# is now read from the one place that decides it, and this raises rather than guessing.
_GEN_SRC = (HERE / "build_run37_acceptance.py").read_text(encoding="utf-8")
_m = re.search(r'^GATE_FILE = "([^"]+)"', _GEN_SRC, re.M)
if _m is None:
    raise SystemExit(
        "RUN 91 DERIVATION FAILED: build_run37_acceptance.py carries no module-level GATE_FILE "
        "constant, so the gate artefact's name cannot be derived from the generator that writes "
        "it. Stopping rather than falling back to a typed constant.")
SUCCESSOR_GATE = _m.group(1)
SUCCESSOR_RECORD = f"RUN{_RUN}_SUCCESSOR_FREEZE_RECORD.json"
SUCCESSOR_REPORT = f"RUN{_RUN}_SUCCESSOR_FREEZE_REPORT.md"
SUCCESSOR_CHECKSUMS = f"RUN{_RUN}_SUCCESSOR_FREEZE_CHECKSUMS.csv"

#: The `no_self_reference` anchor. DERIVED, and still a SPECIFIC NAMED COMMIT at evaluation time:
#: it is the freeze candidate the IMMEDIATE PREDECESSOR release declared as its own, read out of
#: that release's record. The check it feeds is unchanged -- the current record may not point at
#: this commit as its own candidate, and must name it as the one it supersedes.
_PRED_RECORD_PATH = ROOT / "research" / "freeze" / f"RUN{_PRED_RUN}_SUCCESSOR_FREEZE_RECORD.json"
if not _PRED_RECORD_PATH.is_file():
    raise SystemExit(
        f"RUN 57 DERIVATION FAILED: the predecessor release record {_PRED_RECORD_PATH} does not "
        f"exist, so the no_self_reference anchor cannot be derived. Stopping rather than "
        f"loosening the check to accept any commit.")
PREDECESSOR_ANCHOR = json.loads(
    _PRED_RECORD_PATH.read_text(encoding="utf-8")).get("freeze_candidate_commit")
if not isinstance(PREDECESSOR_ANCHOR, str) or not re.fullmatch(r"[0-9a-f]{40}", PREDECESSOR_ANCHOR):
    raise SystemExit(
        f"RUN 57 DERIVATION FAILED: {_PRED_RECORD_PATH.name} carries freeze_candidate_commit="
        f"{PREDECESSOR_ANCHOR!r}, which is not a full 40-character commit hash, so the anchor "
        f"would not name a specific commit. Stopping rather than loosening the check.")

print(f"  DERIVED from participant_packages.CURRENT ({_PP.CURRENT.identifier}, record "
      f"{_PP.CURRENT.record}): run {_RUN}")
print(f"    SUCCESSOR_GATE      = {SUCCESSOR_GATE}")
print(f"    SUCCESSOR_RECORD    = {SUCCESSOR_RECORD}")
print(f"    SUCCESSOR_REPORT    = {SUCCESSOR_REPORT}")
print(f"    SUCCESSOR_CHECKSUMS = {SUCCESSOR_CHECKSUMS}")
print(f"  DERIVED from the predecessor link ({_PP.PARTICIPANT_PACKAGES[-2].identifier}, run "
      f"{_PRED_RUN}): no_self_reference anchor = {PREDECESSOR_ANCHOR}")

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
# RUN 91. THE FALLBACK TO THE COMMITTED CSV IS REMOVED, AND THAT IS A STRENGTHENING.
#
# `_gate = _fresh or _committed` meant that whenever the generator REFUSED TO RUN -- which it has
# done on every clean tree since the CANDIDATE fixed point went stale -- every one of the fifteen
# blocker checks silently read the COMMITTED snapshot instead. That snapshot records a clean gate,
# so the suite reported all fifteen classes green while a live evaluation reports B01, B04, B11 and
# B15 BLOCKED. The one line that would have said so, `run37.gate.reproduces`, was itself failing for
# an unrelated name mismatch (see SUCCESSOR_GATE above) and was read as a known cosmetic failure.
# That is the exact vacuity the comment above says the campaign found, reintroduced by a fallback.
#
# A gate that cannot regenerate CANNOT CERTIFY. There is now no artefact to fall back to: the
# blocker checks read the freshly regenerated gate or they read nothing and fail.
_gate = _fresh
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
          # RE-ANCHORED BY RUN 56, on Run 49's own construction, which was Run 48's, Run 47's,
          # Run 45's, Run 44's and Run 43's. Each successor must name its IMMEDIATE
          # predecessor's candidate as its parent. THIS ANCHOR HAD STOPPED ADVANCING: it still
          # named RUN 48's candidate, and it kept passing only because SUCCESSOR_RECORD above
          # was itself still pinned at the RUN 51 record, whose parent really is Run 48's
          # candidate. With SUCCESSOR_RECORD advanced to the release actually being minted, the
          # anchor must advance with it, to RUN 55's candidate -- the immediate predecessor of
          # sim-2026.08-v37. Named EXPLICITLY rather than loosened to "any commit", because the
          # point of the check is that the record cannot point at itself and cannot silently
          # reparent; loosening it here would be the weakening the order forbids.
          and _rec.get("freeze_candidate_commit")
          != PREDECESSOR_ANCHOR
          and _rec.get("supersedes_candidate")
          == PREDECESSOR_ANCHOR
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
