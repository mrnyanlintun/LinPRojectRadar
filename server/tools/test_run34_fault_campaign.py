"""
RUN 34 -- THE 20-FAULT CALIBRATION CAMPAIGN, WIRED INTO THE ACCEPTANCE RUNNER.

`server/run_all_suites.sh` globs `tools/test_*.py`, so the campaign body under `server/tests/` is
executed here rather than copied. One campaign, one place its faults are stated.
"""

from __future__ import annotations

import os
import pathlib
import runpy
import sys

_HERE = pathlib.Path(__file__).resolve().parent
_BODY = _HERE.parent / "tests" / "test_run34_fault_campaign.py"

if not _BODY.is_file():
    print("RESULT: 0/1 checks passed")
    print(f"the Run-34 fault campaign is missing at {_BODY}")
    sys.exit(1)

os.chdir(_HERE.parent)
runpy.run_path(str(_BODY), run_name="__main__")
