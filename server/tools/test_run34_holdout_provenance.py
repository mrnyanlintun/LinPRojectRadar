"""
RUN 34 FINAL METADATA CLOSURE -- THE HOLDOUT/SELECTION ORDER GUARD, WIRED INTO THE RUNNER.

`server/run_all_suites.sh` globs `tools/test_*.py`. The guard body under `server/tests/` is
executed here rather than copied, so there is one oracle and one place its expectations are set.
"""

from __future__ import annotations

import os
import pathlib
import runpy
import sys

_HERE = pathlib.Path(__file__).resolve().parent
_BODY = _HERE.parent / "tests" / "test_run34_holdout_provenance.py"

if not _BODY.is_file():
    print("RESULT: 0/1 checks passed")
    print(f"the Run-34 holdout provenance guard is missing at {_BODY}")
    sys.exit(1)

os.chdir(_HERE.parent)
runpy.run_path(str(_BODY), run_name="__main__")
