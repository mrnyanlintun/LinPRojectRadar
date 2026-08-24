#!/usr/bin/env python3
"""
RUN 57, PHASE B. THE DERIVED PINS AND THE TWO FIXED POINTS, PROVED BY INJECTION.

A derivation that is never made to fail is a derivation nobody has tested. Every claim here is
established by injecting a fault, READING THE BYTES BACK FROM DISK to confirm the injection
landed, observing the intended red, restoring inside a `finally` that cannot be skipped, and
re-checking the baseline afterwards.

THE SNAPSHOT IS TAKEN FROM THE COMMITTED REFERENCE, never from disk. Run 53 traced a five-run
fault leak to exactly that: a per-fault snapshot taken from disk restored the corruption
faithfully and certified it. `campaign_safety` provides the start-AND-end tree check that is the
actual fix.

Run from a CLEAN directory, never the scratchpad root.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "server"))

from campaign_safety import require_clean_tree, head_text, porcelain  # noqa: E402

PASSED = 0
FAILED = 0
_fail: list[str] = []


def check(ok, label, detail=""):
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        _fail.append(label)
        print(f"  ****  {label}" + (f"   [{detail}]" if detail else ""))
    return bool(ok)


GATE = ROOT / "server" / "tools" / "test_run37_freeze_gate.py"
ACC = ROOT / "server" / "tools" / "build_run37_acceptance.py"
PKG = ROOT / "server" / "tools" / "participant_packages.py"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")

print(f"cwd: {os.getcwd()}")
print(f"repository root: {ROOT}")
require_clean_tree(ROOT, "start", "run57 derived-pin campaign")
print(f"tree at start: {porcelain(ROOT) or 'CLEAN'}")


def run_gate():
    return subprocess.run([sys.executable, "-u", str(GATE)], cwd=str(ROOT), env=ENV,
                          capture_output=True, text=True)


def run_acc(extra=()):
    return subprocess.run([sys.executable, "-u", str(ACC), "--out-audit", str(OUT),
                           "--out-freeze", str(OUT), *extra], cwd=str(ROOT), env=ENV,
                          capture_output=True, text=True)


OUT = pathlib.Path(os.environ.get("RUN57_OUT", "/tmp/run57-derived-pins"))
OUT.mkdir(parents=True, exist_ok=True)

# =================================================================================================
print()
print("=" * 94)
print("1. NO TYPED RELEASE CONSTANT SURVIVES IN THE GATE SUITE  (guarantee 8)")
print("=" * 94)
G = GATE.read_text(encoding="utf-8")
CODE = re.sub(r"/\*.*?\*/", "", "\n".join(l.split("#")[0] for l in G.splitlines()), flags=re.S)
typed_names = re.findall(r'"(?:RUN\d+_SUCCESSOR[A-Z_]*\.\w+|run\d+_successor[a-z_]*\.\w+)"', CODE)
typed_hashes = re.findall(r'"[0-9a-f]{40}"', CODE)
print(f"    typed release filenames in gate-suite CODE: {typed_names}")
print(f"    typed 40-character commit hashes in gate-suite CODE: {typed_hashes}")
check(not typed_names,
      "GUARANTEE 8: the gate suite contains NO typed release filename -- all four names are "
      "derived", str(typed_names))
check(not typed_hashes,
      "GUARANTEE 8: and NO typed 40-character commit hash -- the no_self_reference anchor is "
      "derived too", str(typed_hashes))
# NON-VACUITY, pinned to an EXPLICIT commit, never to a relative reference.
BASE = "50dfb40fd83850a5342ab9106c063cbe87f367e9"
GB = subprocess.run(["git", "-C", str(ROOT), "show", f"{BASE}:server/tools/test_run37_freeze_gate.py"],
                    capture_output=True, text=True).stdout
CODE_B = re.sub(r"/\*.*?\*/", "", "\n".join(l.split("#")[0] for l in GB.splitlines()), flags=re.S)
was_names = re.findall(r'"(?:RUN\d+_SUCCESSOR[A-Z_]*\.\w+|run\d+_successor[a-z_]*\.\w+)"', CODE_B)
was_hashes = re.findall(r'"[0-9a-f]{40}"', CODE_B)
print(f"    at {BASE[:7]} the same sweep found: {was_names} and {was_hashes}")
check(len(was_names) == 4 and len(was_hashes) == 2,
      f"and the check is NOT VACUOUS: at {BASE[:7]} the same uncapped sweep found FOUR typed "
      f"release filenames and TWO typed commit hashes",
      f"{was_names} {was_hashes}")

print()
print("=" * 94)
print("2. THE DERIVED VALUES, AND THE ANCHOR IS A SPECIFIC NAMED COMMIT  (guarantee 10)")
print("=" * 94)
r = run_gate()
derived = {}
for line in r.stdout.splitlines():
    m = re.match(r"\s+(SUCCESSOR_\w+)\s+=\s+(\S+)", line)
    if m:
        derived[m.group(1)] = m.group(2)
    m2 = re.search(r"no_self_reference anchor = ([0-9a-f]{40})", line)
    if m2:
        derived["ANCHOR"] = m2.group(1)
for k, v in derived.items():
    print(f"    {k:22} = {v}")
check(len(derived) == 5, "all four release names and the anchor are DERIVED and printed by the "
                         "suite itself", str(derived))
sys.path.insert(0, str(HERE))
import participant_packages as PP  # noqa: E402
run_now = re.search(r"run(\d+)_participant_package", PP.CURRENT.record).group(1)
check(derived.get("SUCCESSOR_GATE") == f"run{run_now}_successor_freeze_gate.csv"
      and derived.get("SUCCESSOR_RECORD") == f"RUN{run_now}_SUCCESSOR_FREEZE_RECORD.json"
      and derived.get("SUCCESSOR_REPORT") == f"RUN{run_now}_SUCCESSOR_FREEZE_REPORT.md"
      and derived.get("SUCCESSOR_CHECKSUMS") == f"RUN{run_now}_SUCCESSOR_FREEZE_CHECKSUMS.csv",
      f"and all four name the release of participant_packages.CURRENT ({PP.CURRENT.identifier}, "
      f"run {run_now}) -- one fact, four names", str(derived))
anchor = derived.get("ANCHOR", "")
check(re.fullmatch(r"[0-9a-f]{40}", anchor or "") is not None,
      "GUARANTEE 10: the anchor is a full 40-character commit id, not a pattern", anchor)
_cat = subprocess.run(["git", "-C", str(ROOT), "cat-file", "-t", anchor],
                      capture_output=True, text=True)
print(f"    git cat-file -t {anchor} -> {_cat.stdout.strip() or _cat.stderr.strip()}")
check(_cat.stdout.strip() == "commit",
      "GUARANTEE 10: and it RESOLVES to a specific named commit in this repository at evaluation "
      "time -- the rule accepts that commit and no other", _cat.stdout.strip())
pred = PP.PARTICIPANT_PACKAGES[-2]
pred_run = re.search(r"run(\d+)_participant_package", pred.record).group(1)
pred_rec = json.loads((ROOT / "research" / "freeze"
                       / f"RUN{pred_run}_SUCCESSOR_FREEZE_RECORD.json").read_text(encoding="utf-8"))
check(anchor == pred_rec["freeze_candidate_commit"],
      f"and it is exactly what the IMMEDIATE PREDECESSOR release (run {pred_run}, "
      f"{pred.identifier}) declares as its own freeze candidate -- read from that record, not "
      f"from the record under test, so the check is not circular", anchor)

print()
print("=" * 94)
print("3. INJECTION: POINT THE CHAIN AT THE PREDECESSOR  (guarantee 9)")
print("=" * 94)
PKG_SNAP = head_text(ROOT, PKG)          # THE COMMITTED REFERENCE, never disk
check(PKG_SNAP == PKG.read_text(encoding="utf-8"),
      "the snapshot is taken from the COMMITTED bytes at HEAD and they match disk before the "
      "injection")
INJ = PKG_SNAP + (
    "\n\n# RUN 57 FAULT INJECTION -- REMOVED BY THE CAMPAIGN'S finally. Points the chain one link\n"
    "# back so the derivation must resolve to the PREDECESSOR release.\n"
    "PARTICIPANT_PACKAGES = PARTICIPANT_PACKAGES[:-1]\n"
    "CURRENT = PARTICIPANT_PACKAGES[-1]\n")
try:
    PKG.write_text(INJ, encoding="utf-8")
    back = PKG.read_text(encoding="utf-8")
    check(back == INJ and back.rstrip().endswith("CURRENT = PARTICIPANT_PACKAGES[-1]"),
          "INJECTION LANDED: the bytes are read back from disk and carry the fault")
    ri = run_gate()
    inj_names = dict(re.findall(r"\s+(SUCCESSOR_\w+)\s+=\s+(\S+)", ri.stdout))
    inj_anchor = re.search(r"no_self_reference anchor = ([0-9a-f]{40})", ri.stdout)
    for k, v in inj_names.items():
        print(f"    UNDER FAULT {k:22} = {v}")
    print(f"    UNDER FAULT ANCHOR             = {inj_anchor and inj_anchor.group(1)}")
    _res = [l for l in ri.stdout.splitlines() if l.startswith("RESULT:")]
    _fails = [l.strip() for l in ri.stdout.splitlines() if l.strip().startswith("- run37.gate")]
    print(f"    {_res}")
    for l in _fails:
        print("      " + l)
    check(bool(_res), "the gate suite RAN under the fault (a suite printing no result line has "
                      "not run)", ri.stdout[-300:])
    check(all(f"run{pred_run}" in v.lower() for v in inj_names.values()),
          f"ALL FOUR names moved TOGETHER to the predecessor release (run {pred_run}) -- they "
          f"cannot disagree with one another, which is exactly the Run-55 state (one advanced, "
          f"three left behind) MADE INEXPRESSIBLE", str(inj_names))
    check(inj_anchor is not None and inj_anchor.group(1) != anchor,
          "and the anchor moved with them, to the predecessor-of-the-predecessor's candidate",
          str(inj_anchor and inj_anchor.group(1)))
    check(any("reproduces" in f for f in _fails),
          "GUARANTEE 9: the derived pins GO RED for the intended reason -- run37.gate.reproduces "
          "fails, because the gate artefact now being named is the predecessor's, which the live "
          "tree does not reproduce", str(_fails))
    check(any("no_self_reference" in f for f in _fails) or any("B15" in f for f in _fails)
          or any("disposition" in f for f in _fails),
          "and at least one further release-pinned row falls with it", str(_fails))
    check("RESULT: 34/34" not in ri.stdout,
          "and the suite does NOT report 34/34 under the fault -- the derivation is not vacuous",
          str(_res))
finally:
    PKG.write_text(PKG_SNAP, encoding="utf-8")
check(PKG.read_text(encoding="utf-8") == PKG_SNAP,
      "RESTORED: participant_packages.py is byte-identical to its committed bytes")
print(f"    tree after the injection: {porcelain(ROOT) or 'CLEAN'}")
check(not porcelain(ROOT), "and the working tree is CLEAN again -- the baseline is re-checked, "
                           "not assumed", str(porcelain(ROOT)))
rb = run_gate()
check(any(l.startswith("RESULT:") for l in rb.stdout.splitlines()),
      "and the baseline gate suite RUNS again after the restore",
      rb.stdout[-200:])
print(f"    baseline after restore: "
      f"{[l for l in rb.stdout.splitlines() if l.startswith('RESULT:')]}")

print()
print("=" * 94)
print("4. INJECTION: A DELIBERATELY WRONG CANDIDATE  (guarantee 11)")
print("=" * 94)
ACC_SNAP = head_text(ROOT, ACC)
check(ACC_SNAP == ACC.read_text(encoding="utf-8"),
      "the snapshot is taken from the COMMITTED bytes at HEAD and they match disk")
r0 = run_acc()
m0 = re.search(r"CANDIDATE as set in this file : (\S+)\n\s+CANDIDATE as computed\s+: (\S+)",
               r0.stdout)
print(f"    baseline: set={m0 and m0.group(1)}  computed={m0 and m0.group(2)}  rc={r0.returncode}")
check(m0 is not None,
      "the generator REPORTS both values plainly on every run, matching or not", r0.stdout[:300])
WRONG = "0" * 40
cur = re.search(r'^CANDIDATE = "([0-9a-f]{40})"$', ACC_SNAP, re.M).group(1)
INJ2 = ACC_SNAP.replace(f'CANDIDATE = "{cur}"', f'CANDIDATE = "{WRONG}"')
try:
    ACC.write_text(INJ2, encoding="utf-8")
    back2 = ACC.read_text(encoding="utf-8")
    check(f'CANDIDATE = "{WRONG}"' in back2,
          "INJECTION LANDED: the bytes are read back from disk and carry the wrong constant")
    r1 = run_acc()
    print(f"    under the wrong constant, rc={r1.returncode}")
    for l in r1.stdout.splitlines():
        if "CANDIDATE" in l or "REFUS" in l or "should read" in l:
            print("      " + l)
    determinable = "NOT DETERMINABLE" not in r1.stdout.split("gate")[0]
    if determinable:
        check(r1.returncode == 3,
              "GUARANTEE 11: the mint REFUSES TO PROCEED while CANDIDATE does not match -- it "
              "exits non-zero rather than warning and continuing", str(r1.returncode))
        check(f"CANDIDATE = {WRONG}" in r1.stdout and "it should read" in r1.stdout,
              "and it NAMES BOTH VALUES: the one that is set and the one it should read",
              r1.stdout[-400:])
        check(ACC.read_text(encoding="utf-8") == INJ2,
              "and it DOES NOT EDIT THE CONSTANT: the file is byte-identical after the refusal")
        check("gate clean" not in r1.stdout and "FREEZE GATE:" not in r1.stdout,
              "and it produced NO gate at all -- the refusal is a stop, not a warning")
    else:
        check(False,
              "GUARANTEE 11 NOT PROVED ON THIS TREE: the expected candidate is NOT DETERMINABLE "
              "here, so the refusal could not fire. Re-run on a clean tree whose candidate "
              "identity the tree reproduces.", r1.stdout[:400])
finally:
    ACC.write_text(ACC_SNAP, encoding="utf-8")
check(ACC.read_text(encoding="utf-8") == ACC_SNAP,
      "RESTORED: build_run37_acceptance.py is byte-identical to its committed bytes")

require_clean_tree(ROOT, "end", "run57 derived-pin campaign")
print(f"    tree at end: {porcelain(ROOT) or 'CLEAN'}")
check(not porcelain(ROOT), "and the tree is CLEAN at the END as well as at the START -- the "
                           "start-AND-end check is the actual fix, not the finally")

print()
print("=" * 94)
print(f"RESULT  passed={PASSED}  failed={FAILED}")
for f in _fail:
    print("  FAILED: " + f)
print("=" * 94)
sys.exit(1 if FAILED else 0)
