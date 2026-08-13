"""
Run 19, Gate 0. Re-prove that the strict suite runner can FAIL.

A suite counts as a pass only when the process exits zero, the anchored canonical RESULT line is
present, the numerator equals the denominator, and no contradictory failure marker exists. That
is worth re-proving every run, because the whole audit rests on it: a runner that accepts a
crash, or accepts prose, would make every green in this programme meaningless.

Four failure modes are exercised, each by planting a throwaway suite in a scratch copy of the
runner's directory and confirming the runner rejects it:

  1. false prose, "all tests passed", with no canonical RESULT line
  2. a reported failed count, RESULT: 3/5
  3. a green RESULT line followed by a nonzero exit
  4. a silent crash before any RESULT line is printed

Writes code_audit/run19_harness_integrity.csv.
"""

from __future__ import annotations

import csv
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SERVER = HERE.parent
ROOT = SERVER.parent

CASES = {
    "false prose with no canonical RESULT line": (
        'print("All 12 tests passed successfully.")\n'
        'print("0 failed")\n'),
    "a reported failed count": (
        'print("RESULT: 3/5 checks passed")\n'),
    "a green RESULT line followed by a nonzero exit": (
        'import sys\n'
        'print("RESULT: 5/5 checks passed")\n'
        'sys.exit(3)\n'),
    "a silent crash before any RESULT line": (
        'raise SystemError("the interpreter died before reporting")\n'),
    # The control: a genuinely green suite must be ACCEPTED, or the runner is simply broken and
    # rejecting everything, which would prove nothing.
    "CONTROL, a genuinely green suite": (
        'print("RESULT: 5/5 checks passed")\n'),
}


def main() -> int:
    rows = []
    ok = True
    for label, body in CASES.items():
        with tempfile.TemporaryDirectory() as tmp:
            scratch = pathlib.Path(tmp) / "repo"
            shutil.copytree(ROOT, scratch,
                            ignore=shutil.ignore_patterns("__pycache__", ".venv", "*.pyc",
                                                          "*.db", ".git", "node_modules"))
            tools = scratch / "server" / "tools"
            # Remove the real suites so only the planted one runs, which keeps this fast and
            # makes the runner's verdict unambiguous.
            for f in tools.glob("test_*.py"):
                f.unlink()
            (tools / "test_zz_harness_probe.py").write_text(body, encoding="utf-8")
            env = dict(os.environ)
            env["PYTHONIOENCODING"] = "utf-8"
            proc = subprocess.run(["bash", "run_all_suites.sh"],
                                  cwd=str(scratch / "server"), env=env,
                                  capture_output=True, text=True, timeout=600)
            out = proc.stdout + proc.stderr
            rejected = proc.returncode != 0 or "FAILED SUITES" in out
            expected_rejected = not label.startswith("CONTROL")
            correct = rejected == expected_rejected
            ok = ok and correct
            rows.append({
                "failure_mode": label,
                "runner_exit_code": proc.returncode,
                "runner_rejected_it": "yes" if rejected else "no",
                "expected": "reject" if expected_rejected else "accept",
                "harness_behaved_correctly": "yes" if correct else "NO",
                "runner_verdict_line": next(
                    (ln.strip() for ln in out.splitlines()
                     if ln.startswith("FAIL") or ln.strip() == "ALL SUITES GREEN"), ""),
            })
            print(f"{'ok  ' if correct else 'FAIL'}  {label}: exit {proc.returncode}, "
                  f"{'rejected' if rejected else 'accepted'}")

    target = ROOT / "code_audit" / "run19_harness_integrity.csv"
    with target.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"\nwritten: {target}")
    print("HARNESS INTEGRITY: " + ("PROVED" if ok else "NOT PROVED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
