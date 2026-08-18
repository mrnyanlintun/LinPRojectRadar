#!/usr/bin/env python3
"""
RUN 34 FINAL METADATA CLOSURE. THE FIVE-FAULT NON-VACUITY CAMPAIGN FOR THE HOLDOUT-ORDER GUARD.

Each of the five defects the closure contract names is injected into the real artifact or the
real report, and the guard must go RED FOR THE INTENDED REASON -- identified by the specific
check that fails, read from the guard's own output, not merely by a non-zero exit status.

A CRASH IS NOT A RED. The guard runs as a subprocess; a run that produces no canonical RESULT
line is recorded as a CRASH and scored zero.

THE GUARD DOES NOT REGENERATE ITS SUBJECT. That was the defect the previous Run-34 campaign
exposed, where regeneration wiped every injected fault before the later checks ran. This guard
regenerates into a temporary directory only, so an injected fault survives to be caught.

Writes code_audit/run34_provenance_fault_injection_results.csv.
"""

from __future__ import annotations

import csv
import pathlib
import re
import subprocess
import sys

_HERE = pathlib.Path(__file__).resolve().parent
ROOT = _HERE.parents[1]
GUARD = ROOT / "server" / "tests" / "test_run34_holdout_provenance.py"
HOLDOUT = "code_audit/run34_ph1_holdout_result.csv"
REPORT = "REPORT_2026-08-18_run34-portfolio-health-calibration.md"
OUT = ROOT / "code_audit" / "run34_provenance_fault_injection_results.csv"

REQUIRED = 5
PASSED = FAILED = 0
FAILURES: list[str] = []
ROWS = [["fault", "target", "mutation", "applied", "confirmed_applied", "guard", "intended_red",
         "crash_accepted_as_red", "restored_green", "result"]]
APPLIED = REDS = RESTORED = CRASHES = 0


def check(ok, label, detail=""):
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}" + (f"  [{detail}]" if detail else ""))
    else:
        FAILED += 1
        FAILURES.append(label)
        print(f"  FAIL  {label}  [{detail}]")
    return bool(ok)


def head(t):
    print("\n" + "=" * 94 + f"\n{t}\n" + "=" * 94)


def run_guard():
    r = subprocess.run([sys.executable, str(GUARD)], cwd=str(ROOT / "server"),
                       capture_output=True, text=True,
                       env={"PYTHONIOENCODING": "utf-8", "PATH": "/usr/bin:/bin",
                            "PYTHONDONTWRITEBYTECODE": "1"})
    if not re.search(r"^RESULT: \d+/\d+ checks passed$", r.stdout, re.M):
        return False, [], True
    return r.returncode == 0, re.findall(r"^  FAIL  (.+?)(?:  \[|$)", r.stdout, re.M), False


def fault(n, target, path, old, new, mutation, guard_name, expect):
    global APPLIED, REDS, RESTORED, CRASHES
    f = ROOT / path
    original = f.read_text(encoding="utf-8")
    ok, _, crashed = run_guard()
    green = check(ok and not crashed, f"F{n} GREEN BEFORE: {guard_name}")
    applied = confirmed = red = crash = False
    try:
        if original.count(old) != 1:
            check(False, f"F{n} NOT APPLIED: anchor not unique in {path}",
                  str(original.count(old)))
        else:
            f.write_text(original.replace(old, new, 1), encoding="utf-8")
            applied = True
            back = f.read_text(encoding="utf-8")
            confirmed = check(back != original and new in back,
                              f"F{n} INJECTION CONFIRMED: read back from disk, not assumed")
            ok2, fails, crash = run_guard()
            if crash:
                check(False, f"F{n} CRASHED rather than failing a guard -- NOT counted as RED")
            else:
                hit = [x for x in fails if expect.lower() in x.lower()]
                red = check((not ok2) and bool(hit),
                            f"F{n} RED for the intended reason: {guard_name}",
                            (hit[0][:90] if hit else f"failures were {fails[:2]}"))
    finally:
        f.write_text(original, encoding="utf-8")
    ok3, _, crashed3 = run_guard()
    restored = check(f.read_text(encoding="utf-8") == original and ok3 and not crashed3,
                     f"F{n} RESTORED GREEN: file byte-identical, guard green again")
    APPLIED += 1 if applied else 0
    REDS += 1 if red else 0
    RESTORED += 1 if restored else 0
    CRASHES += 1 if crash else 0
    ROWS.append([str(n), target, mutation, "YES" if applied else "NO",
                 "YES" if confirmed else "NO", guard_name, "YES" if red else "NO",
                 "YES" if crash else "NO", "YES" if restored else "NO",
                 "PASS" if (green and applied and confirmed and red and restored and not crash)
                 else "FAIL"])


_hold_text = (ROOT / HOLDOUT).read_text(encoding="utf-8")
_CHANGED_LINE = [ln for ln in _hold_text.splitlines()
                 if ln.startswith("PROVENANCE,-,holdout_changed_selection,")][0]
_SEL_COMMIT_LINE = [ln for ln in _hold_text.splitlines()
                    if ln.startswith("PROVENANCE,-,selection_commit,")][0]
_NONCONS_LINE = [ln for ln in _hold_text.splitlines()
                 if ln.startswith("PROVENANCE,-,selection_reads_holdout_dataset,")][0]


# =================================================================================================
head("FAULT 1: holdout_changed_selection IS DELETED")
# =================================================================================================
fault(1, "the holdout artifact", HOLDOUT, _CHANGED_LINE + "\n", "",
      "the holdout_changed_selection row is removed entirely, so the artifact no longer states "
      "whether the holdout influenced the selection",
      "the holdout artifact records holdout_changed_selection",
      "records holdout_changed_selection")


# =================================================================================================
head("FAULT 2: holdout_changed_selection IS CHANGED FROM NO TO YES")
# =================================================================================================
fault(2, "the holdout artifact", HOLDOUT,
      "PROVENANCE,-,holdout_changed_selection,NO,",
      "PROVENANCE,-,holdout_changed_selection,YES,",
      "the artifact asserts that the holdout DID change the selection, which would mean a "
      "parameter was chosen after inspecting holdout results",
      "holdout_changed_selection = NO",
      "holdout_changed_selection = NO")


# =================================================================================================
head("FAULT 3: THE HOLDOUT IS MADE TO APPEAR TO PRECEDE SELECTION")
# =================================================================================================
# The recorded selection commit is replaced by a LATER commit, so the artifact represents the
# selection as having happened after the holdout evaluation.
_later = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                        text=True).stdout.strip()
fault(3, "the holdout artifact", HOLDOUT,
      _SEL_COMMIT_LINE,
      _SEL_COMMIT_LINE.replace(_SEL_COMMIT_LINE.split(",")[3], _later, 1),
      "the recorded selection_commit is replaced with a LATER commit, so the artifact represents "
      "selection as having occurred after the holdout evaluation",
      "the artifact's recorded commits are the ones GIT gives",
      "recorded commits are the ones GIT gives")


# =================================================================================================
head("FAULT 4: THE SELECTION-BEFORE-HOLDOUT EVIDENCE IS REMOVED")
# =================================================================================================
# The non-consumption finding -- the only evidence that actually separates the two phases -- is
# flipped to UNPROVEN, which is what the artifact would say if the proof had not been run.
fault(4, "the holdout artifact", HOLDOUT,
      "PROVENANCE,-,selection_reads_holdout_dataset,NO,",
      "PROVENANCE,-,selection_reads_holdout_dataset,UNPROVEN,",
      "the non-consumption evidence is withdrawn, leaving the ordering claim resting on commit "
      "order alone -- which cannot support it, because the holdout fixture predates selection "
      "and both phases share a commit",
      "the artifact records the same non-consumption result this guard just derived",
      "same non-consumption result")


# =================================================================================================
head("FAULT 5: THE REPORT AND THE ARTIFACT DISAGREE")
# =================================================================================================
# THE SHAPE THAT WOULD HAVE CAUGHT THE EARLIER COUNT DISCREPANCY. The report's stated value is
# changed while the artifact keeps its own, so the two disagree -- and the guard compares the
# report's value against the ARTIFACT's, not against a second copy of itself.
fault(5, "the Run-34 report", REPORT,
      "| `holdout_changed_selection` | **NO** |",
      "| `holdout_changed_selection` | **YES** |",
      "the report states holdout_changed_selection = YES while the artifact states NO, so the "
      "published claim and the recorded fact disagree",
      "the report's stated holdout_changed_selection equals the artifact's",
      "stated holdout_changed_selection equals the artifact")


# =================================================================================================
head("CAMPAIGN TOTALS")
# =================================================================================================
_rows = ROWS[1:]
check(len(_rows) == REQUIRED, f"faults required = {REQUIRED}; recorded = {len(_rows)}")
check(APPLIED == REQUIRED, f"faults applied = {APPLIED}", f"NOT_APPLIED = {REQUIRED - APPLIED}")
check(REDS == REQUIRED, f"intended RED = {REDS}")
check(RESTORED == REQUIRED, f"restored GREEN = {RESTORED}")
check(CRASHES == 0, f"crashes accepted as RED = {CRASHES}")
check(all(r[-1] == "PASS" for r in _rows), "every fault row PASSES")
ROWS.append(["TOTALS", "-", "-", str(APPLIED), "-", "-", str(REDS), str(CRASHES), str(RESTORED),
             "PASS" if (APPLIED == REDS == RESTORED == REQUIRED and CRASHES == 0) else "FAIL"])
with OUT.open("w", encoding="utf-8", newline="") as fh:
    csv.writer(fh, lineterminator="\n").writerows(ROWS)
print(f"\nwrote {OUT.relative_to(ROOT)}")

print()
print("=" * 94)
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
print("=" * 94)
if FAILURES:
    print("FAILURES:")
    for f in FAILURES:
        print("  -", f)
sys.exit(1 if FAILED else 0)
