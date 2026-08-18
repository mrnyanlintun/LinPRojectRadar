"""
RUN 33 FINAL CLOSURE -- THE PH.1 TEN-FAULT CAMPAIGN, WIRED INTO THE ACCEPTANCE RUNNER.

`server/tests/test_run33_ph1_fault_campaign.py` turns every guard the PH.1 closure rests on RED
by mutating real production source, and restores it. `server/run_all_suites.sh` globs
`tools/test_*.py`, so without this shim the campaign would sit outside the acceptance gate --
the same finding Run 32 recorded about the Category-10 oracles. It is EXECUTED here rather than
copied, so there is one campaign and one place its faults are stated.
"""

from __future__ import annotations

import os
import pathlib
import runpy
import sys

_HERE = pathlib.Path(__file__).resolve().parent
_CAMPAIGN = _HERE.parent / "tests" / "test_run33_ph1_fault_campaign.py"

if not _CAMPAIGN.is_file():
    print("RESULT: 0/1 checks passed")
    print(f"the PH.1 fault campaign is missing at {_CAMPAIGN}")
    sys.exit(1)

os.chdir(_HERE.parent)
runpy.run_path(str(_CAMPAIGN), run_name="__main__")
