"""
RUN 27. THE FAULT CAMPAIGN: prove the matrix guard can fail, one named fault at a time.

This programme has found sixteen-plus vacuous guards, and the owner's five failure modes are
history rather than theory: a check crashed instead of failing and printed no RESULT line; an
injection silently failed to apply; a fixture built state by a route the application never takes;
a check asserted against a copy of the logic; a check asserted the defect's own sentence verbatim.

So each fault below does four things in order and records all four:

  1. APPLY the mutation to code_audit/run27_98_module_remediation_matrix.csv
  2. CONFIRM THE MUTATION ACTUALLY LANDED, by re-reading the file from disk and asserting the
     specific structural change (a row count, a duplicate id, an emptied cell). An injection that
     silently failed to apply would stop the campaign here rather than produce a green "restored".
  3. RUN THE GUARD as a separate process and require it to exit NON-ZERO, to print a canonical
     RESULT line, and for the NAMED check to be among the failures. A crash is not red: a run
     with no RESULT line is recorded as CRASH_NOT_RED and fails the campaign.
  4. RESTORE from the byte-exact backup and re-run the guard to full green.

The baseline is re-checked after every single fault, not once at the end.
"""

from __future__ import annotations

import csv
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]

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
_cs_arm(_cs_pl.Path(ROOT), "run27_fault_campaign.py",
        allow=["code_audit/run27_98_module_remediation_matrix.csv", "code_audit/run27_guard_nonvacuity.csv"])
# -------------------------------------------------------------------------------------------
MATRIX = ROOT / "code_audit" / "run27_98_module_remediation_matrix.csv"
GUARD = ROOT / "server" / "tools" / "test_run27_remediation_matrix.py"
OUT = ROOT / "code_audit" / "run27_guard_nonvacuity.csv"

RESULT_RE = re.compile(r"^RESULT: (\d+)/(\d+)( checks passed)?$", re.M)


def read_rows() -> tuple[list[str], list[dict[str, str]]]:
    with MATRIX.open(encoding="utf-8-sig") as fh:
        r = csv.DictReader(fh)
        return list(r.fieldnames or []), list(r)


def write_rows(cols: list[str], rows: list[dict[str, str]]) -> None:
    with MATRIX.open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow(row)


def run_guard() -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, GUARD.name],
        cwd=str(GUARD.parent), capture_output=True, text=True,
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
    )
    return proc.returncode, proc.stdout + proc.stderr


def verdict(rc: int, out: str, expected_label: str) -> tuple[str, str]:
    m = RESULT_RE.search(out)
    if not m:
        return "CRASH_NOT_RED", "the guard printed no canonical RESULT line"
    passed, total = int(m.group(1)), int(m.group(2))
    if rc == 0 and passed == total:
        return "GREEN", f"{passed}/{total}"
    hit = [ln.strip(" -") for ln in out.splitlines()
           if ln.strip().startswith("- ") and expected_label in ln]
    if not hit:
        return "RED_WRONG_REASON", f"{passed}/{total}; the named check was not among the failures"
    return "RED_FOR_THE_INTENDED_REASON", f"{passed}/{total}; {hit[0][:150]}"


# --------------------------------------------------------------------------------------------
# The six mandated faults. Each returns a callable that mutates the parsed rows, plus a
# confirmation predicate run against the file AFTER it is rewritten.
# --------------------------------------------------------------------------------------------

def _omit(rows):
    return [r for r in rows if r["canonical_id"] != "A5.6"]


def _confirm_omit(rows):
    return "A5.6" not in {r["canonical_id"] for r in rows}


def _duplicate(rows):
    dup = next(dict(r) for r in rows if r["canonical_id"] == "A1.2")
    return rows + [dup]


def _confirm_duplicate(rows):
    ids = [r["canonical_id"] for r in rows]
    return ids.count("A1.2") == 2


def _include_pass(rows):
    smuggled = dict(rows[0])
    smuggled["canonical_id"] = "A1.7"
    smuggled["current_registered_name"] = "TCPI"
    return rows + [smuggled]


def _confirm_include_pass(rows):
    return "A1.7" in {r["canonical_id"] for r in rows}


def _strip_data(rows):
    out = []
    for r in rows:
        r = dict(r)
        if r["canonical_id"] == "A2.10":
            r["exact_missing_evidence"] = ""
        out.append(r)
    return out


def _confirm_strip_data(rows):
    row = next(r for r in rows if r["canonical_id"] == "A2.10")
    return row["exact_missing_evidence"] == "" and "DATA" in (
        row["primary_remediation_type"] + " " + row["secondary_remediation_types"])


def _strip_supply(rows):
    out = []
    for r in rows:
        r = dict(r)
        if r["canonical_id"] == "A2.10":
            r["supply_mechanism"] = ""
        out.append(r)
    return out


def _confirm_strip_supply(rows):
    row = next(r for r in rows if r["canonical_id"] == "A2.10")
    return row["supply_mechanism"] == ""


def _strip_run(rows):
    out = []
    for r in rows:
        r = dict(r)
        if r["canonical_id"] == "C1.7":
            r["recommended_future_run"] = ""
        out.append(r)
    return out


def _confirm_strip_run(rows):
    return next(r for r in rows if r["canonical_id"] == "C1.7")["recommended_future_run"] == ""


FAULTS = [
    ("F1 omit one of the non-pass targets (A5.6 Queueing Theory Bottleneck)",
     _omit, _confirm_omit, "missing non-pass targets = 0"),
    ("F2 duplicate one module (A1.2 CUSUM Anomaly Monitor appears twice)",
     _duplicate, _confirm_duplicate, "duplicate rows = 0"),
    ("F3 include a SCIENTIFIC_PASS module (A1.7 TCPI smuggled into the matrix)",
     _include_pass, _confirm_include_pass,
     "SCIENTIFIC_PASS targets accidentally included = 0"),
    ("F4 remove the DATA requirement from a DATA row (A2.10 missing evidence emptied)",
     _strip_data, _confirm_strip_data, "DATA rows without a stated missing input = 0"),
    ("F5 remove the supply mechanism from that same DATA row (A2.10)",
     _strip_supply, _confirm_strip_supply,
     "DATA rows without a proposed supply mechanism = 0"),
    ("F6 leave one row without a future run (C1.7 Reporting Frequency Index)",
     _strip_run, _confirm_strip_run, "orphan future-run assignments = 0"),
]


def main() -> int:
    backup = pathlib.Path(tempfile.mkdtemp()) / "matrix_backup.csv"
    shutil.copy2(MATRIX, backup)

    records = []
    rc, out = run_guard()
    base_status, base_detail = verdict(rc, out, "")
    print(f"BASELINE  {base_status}  {base_detail}")
    if base_status != "GREEN":
        print("baseline is not green; refusing to run the campaign against a red baseline")
        return 1
    records.append(dict(fault="BASELINE (before any injection)", injection_confirmed="n/a",
                        guard_exit=str(rc), verdict=base_status, detail=base_detail,
                        expected_check=""))

    ok = True
    # RUN 55, PHASE B. THE RESTORE IS IN A `finally`. It was a bare statement at the end of the
    # loop body, so a raise between the mutation and it left the mutated bytes on disk, where
    # Run 53 established the next campaign snapshots them and cements them with its own correct
    # restore. The guard from campaign_safety.arm() is the fix; this is the hygiene, and a
    # known-incomplete repair is not left half-done.
    for label, mutate, confirm, expected in FAULTS:
        applied = False
        try:
            cols, rows = read_rows()
            write_rows(cols, mutate(rows))
            _, reread = read_rows()
            applied = confirm(reread)
            if not applied:
                print(f"{label}: INJECTION DID NOT APPLY -- campaign halted for this fault")
                records.append(dict(fault=label, injection_confirmed="NO",
                                    guard_exit="", verdict="INJECTION_FAILED",
                                    detail="the mutation was not present when the file "
                                           "was re-read",
                                    expected_check=expected))
                ok = False
            else:
                rc, out = run_guard()
                status, detail = verdict(rc, out, expected)
                print(f"{label}\n    injection confirmed on re-read: YES\n    "
                      f"{status}  {detail}")
                records.append(dict(fault=label, injection_confirmed="YES", guard_exit=str(rc),
                                    verdict=status, detail=detail, expected_check=expected))
                if status != "RED_FOR_THE_INTENDED_REASON":
                    ok = False
        finally:
            shutil.copy2(backup, MATRIX)
        if not applied:
            continue
        rc, out = run_guard()
        rstatus, rdetail = verdict(rc, out, "")
        print(f"    restored -> {rstatus} {rdetail}")
        records.append(dict(fault=f"{label} :: RESTORED AND BASELINE RE-CHECKED",
                            injection_confirmed="n/a", guard_exit=str(rc), verdict=rstatus,
                            detail=rdetail, expected_check=""))
        if rstatus != "GREEN":
            ok = False

    with OUT.open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.DictWriter(fh, fieldnames=["fault", "injection_confirmed", "guard_exit",
                                           "verdict", "detail", "expected_check"],
                           lineterminator="\n")
        w.writeheader()
        for r in records:
            w.writerow(r)
    print(f"\nwrote {OUT.relative_to(ROOT)}")
    print("CAMPAIGN " + ("PASSED" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
