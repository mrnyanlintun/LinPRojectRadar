#!/usr/bin/env python3
"""
RUN 34 FINAL CLOSURE. THE FIVE-FAULT NON-VACUITY CAMPAIGN FOR THE PARAMETER-COUNT GUARD.

A count guard that cannot fail proves nothing, so each of the five defects the contract names is
injected into the real artifact (or the real report) and the guard is required to go RED for the
intended reason, then restored.

WHAT IS MUTATED. Faults 1 to 4 mutate the PROVENANCE ARTIFACT -- the file the guard reads and the
generator writes. Fault 5 mutates the REPORT. In every case the mutation changes what the named
guard actually reads, so a red result is the guard working rather than something else breaking.

A CRASH IS NOT A RED. The guard is executed as a subprocess and its exit status is read; an
exception is reported as a CRASH and scored zero.

NOTE ON FAULTS 1 AND 2. The provenance artifact is GENERATED, and the guard's first section
regenerates it and byte-compares. That check would go red for ANY mutation, which would make
every fault red for the same uninformative reason. So the campaign asserts on the SPECIFIC named
check for each fault, read from the guard's own output, and not merely on the exit status.

Writes code_audit/run34_count_fault_injection_results.csv.
"""

from __future__ import annotations

import csv
import pathlib
import re
import subprocess
import sys

_HERE = pathlib.Path(__file__).resolve().parent
ROOT = _HERE.parents[1]

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
_cs_arm(_cs_pl.Path(ROOT), "test_run34_count_fault_campaign.py",
        allow=["code_audit/run34_count_fault_injection_results.csv", "code_audit/run34_portfolio_parameter_provenance.csv"])
# -------------------------------------------------------------------------------------------
GUARD = ROOT / "server" / "tests" / "test_run34_parameter_count_closure.py"
PROV = ROOT / "code_audit" / "run34_portfolio_parameter_provenance.csv"
REPORT = ROOT / "REPORT_2026-08-18_run34-portfolio-health-calibration.md"
OUT = ROOT / "code_audit" / "run34_count_fault_injection_results.csv"

REQUIRED = 4   # RUN 59: was 5. Fault 5 retired; see the block below.
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
    """Execute the guard and return (ok, failing check names, crashed)."""
    r = subprocess.run([sys.executable, str(GUARD)], cwd=str(ROOT / "server"),
                       capture_output=True, text=True,
                       env={"PYTHONIOENCODING": "utf-8", "PATH": "/usr/bin:/bin",
                            "PYTHONDONTWRITEBYTECODE": "1"})
    if not re.search(r"^RESULT: \d+/\d+ checks passed$", r.stdout, re.M):
        return False, [], True                      # no canonical result line == a crash
    fails = re.findall(r"^  FAIL  (.+?)(?:  \[|$)", r.stdout, re.M)
    return r.returncode == 0, fails, False


def fault(n, target, path, old, new, mutation, guard_name, expect_fail_substr):
    """One fault. `expect_fail_substr` names the check that must be among the guard's failures."""
    global APPLIED, REDS, RESTORED, CRASHES
    f = ROOT / path
    original = f.read_text(encoding="utf-8")
    ok, _, crashed = run_guard()
    green = check(ok and not crashed, f"F{n} GREEN BEFORE: {guard_name}")
    applied = confirmed = red = crash = False
    try:
        if original.count(old) != 1:
            check(False, f"F{n} NOT APPLIED: the mutation anchor is not unique in {path}",
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
                hit = [x for x in fails if expect_fail_substr.lower() in x.lower()]
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


# The exact text of one parameter row, used as the anchor for faults 1 and 2.
_ROW = ("PARAMETER,D1.4,tie_rule,ALL_TIED_NEIGHBOURS_IN_ASCENDING_PROJECT_ID_ORDER,"
        "\"A declared deterministic tie rule, so that ordering cannot depend on input order.\","
        "OWNER_POLICY")


# =================================================================================================
head("FAULT 1: A PARAMETER ROW IS REMOVED")
# =================================================================================================
_line = [ln for ln in PROV.read_text(encoding="utf-8").splitlines()
         if ln.startswith("PARAMETER,D1.4,tie_rule,")][0]
fault(1, "the provenance artifact", "code_audit/run34_portfolio_parameter_provenance.csv",
      _line + "\n", "",
      "the D1.4 tie_rule parameter row is deleted, so a governed parameter the live registry "
      "declares has no provenance record",
      "MISSING GOVERNED PARAMETER RECORDS = 0, derived from the live registry",
      "MISSING GOVERNED PARAMETER RECORDS")


# =================================================================================================
head("FAULT 2: A PARAMETER ROW IS DUPLICATED")
# =================================================================================================
fault(2, "the provenance artifact", "code_audit/run34_portfolio_parameter_provenance.csv",
      _line + "\n", _line + "\n" + _line + "\n",
      "the D1.4 tie_rule row appears twice, so one parameter is counted as two",
      "DUPLICATE PARAMETER ROWS = 0",
      "DUPLICATE PARAMETER ROWS")


# =================================================================================================
head("FAULT 3: A CLASSIFICATION IS BLANKED")
# =================================================================================================
fault(3, "the provenance artifact", "code_audit/run34_portfolio_parameter_provenance.csv",
      _ROW, _ROW.replace(",OWNER_POLICY", ","),
      "the D1.4 tie_rule row's parameter_class is blanked, so a parameter carries no provenance "
      "class at all",
      "BLANK CLASSIFICATIONS = 0",
      "BLANK CLASSIFICATIONS")


# =================================================================================================
head("FAULT 4: AN ILLEGAL CLASSIFICATION IS INTRODUCED")
# =================================================================================================
fault(4, "the provenance artifact", "code_audit/run34_portfolio_parameter_provenance.csv",
      _ROW, _ROW.replace(",OWNER_POLICY", ",PROBABLY_FINE"),
      "the D1.4 tie_rule row is given a class that is not one of the seven permitted values",
      "ILLEGAL CLASSIFICATION VALUES = 0",
      "ILLEGAL CLASSIFICATION VALUES")


# =================================================================================================
head("FAULT 5: THE REPORT DISTRIBUTION DISAGREES WITH THE CSV")
# =================================================================================================
# THE DEFECT THIS CLOSURE EXISTS TO GUARD AGAINST. The report is padded so its class counts sum to
# 21 instead of the true 19 -- exactly the shape of the error the contract supposed had occurred.
# RUN 59, PHASE B. RETIRED, NOT DELETED.
#
# Owner's ruling, 2026-08-25: no markdown document carries authority, and this fault's TARGET is
# REPORT_2026-08-18_run34-portfolio-health-calibration.md -- sealed evidence. The guard it
# existed to prove red has itself been retired for exactly that reason, so this injection now
# proves nothing: mutating a document nothing asserts cannot turn anything red, and reporting it
# as a passing fault would be a vacuous check dressed as a guarantee.
#
# REQUIRED falls from 5 to 4 with it. That is a deliberate, recorded reduction and not a silent
# one: the constant is changed HERE, beside the reason, and the four surviving faults all inject
# into CSV artifacts or production and are unaffected. Clear the flag and restore REQUIRED to 5
# to run it again. THE BODY IS NOT DELETED.
RETIRED_RUN59_REPORT_FAULT = True

if not RETIRED_RUN59_REPORT_FAULT:
    fault(5, "the Run-34 report", "REPORT_2026-08-18_run34-portfolio-health-calibration.md",
          "| `UNSUPPORTED` | 7 | operational anomaly threshold",
          "| `UNSUPPORTED` | 9 | operational anomaly threshold",
          "the report's published UNSUPPORTED count is padded from 7 to 9 so the seven classes sum to "
          "21 rather than to the true 19 -- the precise defect this closure guards against",
          "the report's distribution equals the artifact's, class for class, and sums to the true "
          "parameter total",
          "REPORT'S DISTRIBUTION EQUALS THE ARTIFACT'S")
else:
    print("  RETIRED (Run 59)  FAULT 5, which mutated a sealed evidence document to prove a guard that is itself now retired")


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
