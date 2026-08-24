#!/usr/bin/env python3
"""
RUN 41 - the section-17 fault campaign, enforced by the acceptance runner.

run41_fault_campaign.py is the executable evidence: it injects twelve faults into real files,
confirms each landed, requires the named guard to go red FOR ITS OWN REASON, restores, and
requires green again. This suite is what makes that campaign enforced rather than merely
available, because a campaign the runner never invokes is a campaign nobody has to keep passing.

It does three things, and the third is the one that matters:

  1. reads the committed results artefact and requires 12 applied, 12 red for the intended
     reason, 12 restored green, and zero crashes credited as red;
  2. derives the twelve fault classes from the campaign script's own FAULTS list rather than
     from a list written here, so a fault that is quietly deleted from the campaign fails this
     suite instead of silently reducing coverage;
  3. RE-EXECUTES ONE FAULT LIVE, end to end, against the real files. Checks 1 and 2 read
     records, and a record can be stale or hand-edited. Re-running one fault proves the harness
     still injects, still detects, and still restores at the moment this suite runs. Fault 4 -
     removing the final-lock trigger from the migration - is the one chosen, because it is the
     whole of S2: if that injection does not turn the S2 guard red, nothing else in this
     campaign can be trusted either.

Set RUN41_FULL_CAMPAIGN=1 to re-execute all twelve here instead of one (slow).

Run (from server/): python tools/test_run41_fault_campaign.py
"""
from __future__ import annotations

import ast
import csv
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]

# --- CAMPAIGN SAFETY (Run 54, phase A) -----------------------------------------------------
# THE START-AND-END DIRTY-TREE GUARD. A campaign must not BEGIN on a dirty tree: Run 53
# established that a leaked fault is snapshotted from disk by the next campaign, faithfully
# restored by its `finally`, and thereby CERTIFIED by its own passing assertion. An end-only
# check cannot see that, because the leak began in an earlier process. See
# server/tools/campaign_safety.py for the full mechanism and the proof.
import sys as _cs_sys, pathlib as _cs_pl                                       # noqa: E402
_cs_sys.path.insert(0, str(_cs_pl.Path(ROOT) / "server" / "tools"))
from campaign_safety import (arm as _cs_arm, restore_guard, head_text,          # noqa: E402,F401
                             snapshot_text, CampaignTreeDirty)
_cs_arm(_cs_pl.Path(ROOT), "test_run41_fault_campaign.py",
        # RUN 55, PHASE B, section 8 item 1: THE ALLOW LIST IS TIGHTENED TO DECLARED
        # OUTPUTS. Run 54 derived this list by taking every `code_audit/` literal in the
        # file, which swept in READ-ONLY inputs and fault TARGETS as well as outputs. An
        # allow entry is a promise that the campaign is designed to write that path;
        # naming a file it only reads widens the guard for nothing. Established by
        # execution: this file contains no write to code_audit at all.
        # (that artifact is written by run41_fault_campaign.py, a DIFFERENT file.)
        allow=[])
# -------------------------------------------------------------------------------------------
CAMPAIGN = HERE / "run41_fault_campaign.py"
RESULTS = ROOT / "code_audit" / "run41_fault_campaign_results.csv"

EXPECTED_FAULTS = 12
results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   -- {detail}" if detail and not ok else ""))


print("=" * 78)
print("RUN 41 - section 17 fault campaign, enforced")
print("=" * 78)

# ------------------------------------------------------------------ 1. the artefact
check(RESULTS.is_file(), "the fault-campaign results artefact exists", str(RESULTS))
rows = []
if RESULTS.is_file():
    with RESULTS.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))

check(len(rows) == EXPECTED_FAULTS,
      f"the campaign recorded exactly {EXPECTED_FAULTS} faults", str(len(rows)))
applied = [r for r in rows if r["applied"] == "APPLIED"]
red = [r for r in rows if r["outcome"] == "RED_FOR_INTENDED_REASON"]
restored = [r for r in rows if r["restored_verdict"] == "GREEN"]
crashed = [r for r in rows if r["outcome"] == "CRASH_NOT_COUNTED_AS_RED"]
unrelated = [r for r in rows if r["outcome"] == "RED_BUT_UNRELATED_NOT_COUNTED"]
undetected = [r for r in rows if r["outcome"] == "STILL_GREEN_FAULT_UNDETECTED"]

check(len(applied) == EXPECTED_FAULTS, f"12/12 applied ({len(applied)})",
      str([r["fault"] for r in rows if r not in applied]))
check(len(red) == EXPECTED_FAULTS, f"12/12 turned the intended guard RED ({len(red)})",
      str([(r["fault"], r["outcome"]) for r in rows if r["outcome"]
           != "RED_FOR_INTENDED_REASON"]))
check(len(restored) == EXPECTED_FAULTS, f"12/12 restored GREEN ({len(restored)})",
      str([r["fault"] for r in rows if r["restored_verdict"] != "GREEN"]))
check(not crashed, "0 crashes accepted as RED", str([r["fault"] for r in crashed]))
check(not unrelated, "0 unrelated refusals counted as evidence",
      str([r["fault"] for r in unrelated]))
check(not undetected, "0 faults left undetected", str([r["fault"] for r in undetected]))

# Every recorded RED must actually quote its intended-reason fragment in the guard's own failing
# line. Without this the "intended reason" column would be a label rather than a measurement.
mislabelled = [r["fault"] for r in red
               if r["intended_reason_fragment"] not in (r.get("matched_failing_line") or "")]
check(not mislabelled,
      "every RED quotes its intended-reason fragment inside the guard's own failing line",
      str(mislabelled))

# ------------------------------------------------------------------ 2. coverage is derived
tree = ast.parse(CAMPAIGN.read_text(encoding="utf-8"))
faults_node = None
for node in ast.walk(tree):
    if isinstance(node, ast.Assign) and len(node.targets) == 1 \
            and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "FAULTS":
        faults_node = node.value
if faults_node is None or not isinstance(faults_node, ast.List):
    check(False, "the campaign's FAULTS list can be read from its source", "not found")
    declared = []
else:
    declared = [el.elts[0].value for el in faults_node.elts if isinstance(el, ast.Tuple)]
    check(len(declared) == EXPECTED_FAULTS,
          f"the campaign script still declares {EXPECTED_FAULTS} faults", str(len(declared)))
    check(sorted(declared) == list(range(1, EXPECTED_FAULTS + 1)),
          "and they are numbered 1..12 with none missing", str(sorted(declared)))
    check(sorted(int(r["fault"]) for r in rows) == sorted(declared),
          "the recorded faults are exactly the declared faults, so the artefact is not stale "
          "against a changed campaign",
          f"recorded={sorted(int(r['fault']) for r in rows)} declared={sorted(declared)}")

# ------------------------------------------------------------------ 3. re-execute live
print()
print("-" * 78)
print("LIVE RE-EXECUTION - the harness is exercised now, not merely reported on")
print("-" * 78)

MIGRATION = ROOT / "server" / "alembic" / "versions" / "0026_final_lock_guard.py"
S2_GUARD = HERE / "test_run41_final_lock_guard.py"
ANCHOR = "    elif dialect == \"sqlite\":\n        op.execute(SQLITE_TRIGGER)"
MUTANT = "    elif dialect == \"sqlite\":\n        pass"
FRAGMENT = "migration 0026 created trg_decisions_final_lock_guard"


def run_guard() -> tuple[str, str]:
    for d in ROOT.rglob("__pycache__"):
        shutil.rmtree(d, ignore_errors=True)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="run41-live-"))
    db = tmp / "live.db"
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "SESSION_SECRET": "run41-live",
           "DATABASE_URL": f"sqlite:///{db}"}
    rc = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"],
                        cwd=str(ROOT / "server"), capture_output=True, text=True, env=env)
    if rc.returncode != 0:
        shutil.rmtree(tmp, ignore_errors=True)
        return "CRASH", "alembic could not build a database"
    p = subprocess.run([sys.executable, str(S2_GUARD)], cwd=str(HERE),
                       capture_output=True, text=True, env=env)
    shutil.rmtree(tmp, ignore_errors=True)
    out = p.stdout + p.stderr
    res = [ln for ln in out.splitlines() if ln.startswith("RESULT: ")]
    if not res:
        return "CRASH", (out.strip().splitlines() or ["no output"])[-1][:160]
    failing = " | ".join(ln.strip() for ln in out.splitlines()
                         if ln.strip().startswith("FAIL  "))
    a, b = res[-1].removeprefix("RESULT: ").split(" ")[0].split("/")
    return ("GREEN" if (a == b and not failing) else "RED"), failing


before = MIGRATION.read_bytes()
v0, _ = run_guard()
check(v0 == "GREEN", "baseline: the S2 guard is GREEN before injection", v0)

src = MIGRATION.read_text(encoding="utf-8")
check(ANCHOR in src, "the injection anchor is present in the live migration")
# RUN 55, PHASE B. THE RESTORE IS IN A `finally`. It was a bare statement after run_guard(), so
# a raise there left a MUTATED ALEMBIC MIGRATION on disk -- the file the freeze gate's S2 guard
# reads. Run 53 established that the next campaign then snapshots the corruption and cements it
# with its own correct restore. The arm() guard is the fix; this is the hygiene, and a
# known-incomplete repair is not left half-done.
try:
    MIGRATION.write_text(src.replace(ANCHOR, MUTANT, 1), encoding="utf-8")
    check(MIGRATION.read_bytes() != before,
          "the injection changed bytes on disk (it was APPLIED)")

    v1, failing = run_guard()
    check(v1 == "RED", "with the trigger removed the S2 guard goes RED (a crash would not count)",
          f"{v1}: {failing[:160]}")
    check(v1 == "RED" and FRAGMENT in failing,
          "and it is RED for the INTENDED reason, quoted from the guard's own failing line",
          failing[:200])
finally:
    MIGRATION.write_bytes(before)
check(MIGRATION.read_bytes() == before, "the migration is restored byte for byte")
v2, _ = run_guard()
check(v2 == "GREEN", "and the S2 guard is GREEN again after restoration", v2)

if os.environ.get("RUN41_FULL_CAMPAIGN") == "1":
    p = subprocess.run([sys.executable, str(CAMPAIGN)], cwd=str(HERE),
                       capture_output=True, text=True,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    check(p.returncode == 0, "the full twelve-fault campaign re-runs clean",
          (p.stdout + p.stderr)[-300:])

passed = sum(1 for ok, _, _ in results if ok)
total = len(results)
print()
print("=" * 78)
print(f"RESULT: {passed}/{total} checks passed")
print("=" * 78)
sys.exit(0 if passed == total else 1)
