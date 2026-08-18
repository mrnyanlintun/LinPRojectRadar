"""
RUN 34 FINAL CLOSURE -- THE FIVE-FAULT COUNT CAMPAIGN, WIRED INTO THE ACCEPTANCE RUNNER.

`server/run_all_suites.sh` globs `tools/test_*.py`. The campaign body under `server/tests/` is
executed here rather than copied.
"""

from __future__ import annotations

import os
import pathlib
import runpy
import sys

_HERE = pathlib.Path(__file__).resolve().parent
_BODY = _HERE.parent / "tests" / "test_run34_count_fault_campaign.py"

if not _BODY.is_file():
    print("RESULT: 0/1 checks passed")
    print(f"the Run-34 count fault campaign is missing at {_BODY}")
    sys.exit(1)

os.chdir(_HERE.parent)
runpy.run_path(str(_BODY), run_name="__main__")
