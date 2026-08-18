"""
RUN 33 FINAL CLOSURE -- THE PH.1 FIXED-FOREST ORACLE, WIRED INTO THE ACCEPTANCE RUNNER.

WHY THIS FILE EXISTS. `server/tests/test_run33_ph1_fixed_forest.py` holds the primary
method-fidelity proof for the Isolation Forest: c(n) from the definition, oracles A to D on
hand-built forests, fixed-forest scoring equivalence against an independent scorer, the real
production route, reproducibility hashes, and the structural proof that the oracle is independent.

IT WOULD NOT BE REACHED BY THE ACCEPTANCE GATE ON ITS OWN. `server/run_all_suites.sh` globs
`tools/test_*.py`, so a file under `server/tests/` is never executed by the gate. Run 32 found
exactly this and left the precedent this file follows: a correct oracle outside the runner is an
unenforced oracle, and the load-bearing deliverable of this closure must not be one.

IT IS WIRED IN RATHER THAN COPIED. Duplicating the oracles would create two bodies that drift,
and the one that drifted would still look green. This file EXECUTES the oracle module in-process,
so there is exactly one set of oracle values and one place they are stated. The executed module
prints its own canonical `RESULT:` line and sets its own exit status, which is what the runner
reads.
"""

from __future__ import annotations

import os
import pathlib
import runpy
import sys

_HERE = pathlib.Path(__file__).resolve().parent
_ORACLES = _HERE.parent / "tests" / "test_run33_ph1_fixed_forest.py"

if not _ORACLES.is_file():
    # A missing oracle file must FAIL the runner, not silently report nothing. The runner
    # accepts only an anchored RESULT line, so print one that cannot be read as a pass.
    print("RESULT: 0/1 checks passed")
    print(f"the PH.1 fixed-forest oracle module is missing at {_ORACLES}")
    sys.exit(1)

os.chdir(_HERE.parent)
runpy.run_path(str(_ORACLES), run_name="__main__")
