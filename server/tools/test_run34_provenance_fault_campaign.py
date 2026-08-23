"""
RUN 34 FINAL METADATA CLOSURE -- THE FIVE-FAULT PROVENANCE CAMPAIGN, WIRED INTO THE RUNNER.

`server/run_all_suites.sh` globs `tools/test_*.py`. The campaign body under `server/tests/` is
executed here rather than copied.
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
_cs_arm(_cs_pl.Path(_cs_pl.Path(__file__).resolve().parents[2]), "test_run34_provenance_fault_campaign.py",
        allow=[])
# -------------------------------------------------------------------------------------------

_HERE = pathlib.Path(__file__).resolve().parent
_BODY = _HERE.parent / "tests" / "test_run34_provenance_fault_campaign.py"

if not _BODY.is_file():
    print("RESULT: 0/1 checks passed")
    print(f"the Run-34 provenance fault campaign is missing at {_BODY}")
    sys.exit(1)

os.chdir(_HERE.parent)
runpy.run_path(str(_BODY), run_name="__main__")
