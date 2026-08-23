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

# --- CAMPAIGN SAFETY (Run 54, phase A) -----------------------------------------------------
# THE START-AND-END DIRTY-TREE GUARD. A campaign must not BEGIN on a dirty tree: Run 53
# established that a leaked fault is snapshotted from disk by the next campaign, faithfully
# restored by its `finally`, and thereby CERTIFIED by its own passing assertion. An end-only
# check cannot see that, because the leak began in an earlier process. See
# server/tools/campaign_safety.py for the full mechanism and the proof.
import sys as _cs_sys, pathlib as _cs_pl                                       # noqa: E402
_cs_sys.path.insert(0, str(_cs_pl.Path(_cs_pl.Path(__file__).resolve().parents[2]) / "server" / "tools"))
from campaign_safety import (arm as _cs_arm, restore_guard, head_text,          # noqa: E402,F401
                             snapshot_text, CampaignTreeDirty)
_cs_arm(_cs_pl.Path(_cs_pl.Path(__file__).resolve().parents[2]), "test_run33_ph1_fault_campaign.py",
        allow=[])
# -------------------------------------------------------------------------------------------

_HERE = pathlib.Path(__file__).resolve().parent
_CAMPAIGN = _HERE.parent / "tests" / "test_run33_ph1_fault_campaign.py"

if not _CAMPAIGN.is_file():
    print("RESULT: 0/1 checks passed")
    print(f"the PH.1 fault campaign is missing at {_CAMPAIGN}")
    sys.exit(1)

os.chdir(_HERE.parent)
runpy.run_path(str(_CAMPAIGN), run_name="__main__")
