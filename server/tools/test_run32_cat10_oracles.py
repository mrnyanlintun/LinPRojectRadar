"""
RUN 32 -- THE CATEGORY-10 ORACLES, WIRED INTO THE ACCEPTANCE RUNNER.

WHY THIS FILE EXISTS. `server/tests/test_run32_cat10_oracles.py` holds the independent oracles for
the canonical Category-10 decision layer: the supplied Wyndor optimum, the nondominated set, the
feasible CSP assignments, the 4/7 sensitivity crossover, the minimax-regret alternative,
permutation invariance, orientation sensitivity and abstention. It passes 68/68.

IT WAS NOT REACHED BY THE ACCEPTANCE GATE. `server/run_all_suites.sh` is the suite runner and it
globs `tools/test_*.py`. A file under `server/tests/` is therefore never executed by the gate, so
those 68 checks were not in the acceptance total and a regression in `canonical_v7` would not
have turned the run red. That is the same class of finding as Run 30's: a correct library behind
an unchanged ledger is a failed remediation, and a correct oracle outside the runner is an
unenforced oracle.

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
_ORACLES = _HERE.parent / "tests" / "test_run32_cat10_oracles.py"

if not _ORACLES.is_file():
    # A missing oracle file must FAIL the runner, not silently report nothing. The runner
    # accepts only an anchored RESULT line, so print one that cannot be read as a pass.
    print(f"RESULT: 0/1 checks passed")
    print(f"the Category-10 oracle module is missing at {_ORACLES}")
    sys.exit(1)

# The oracle module inserts the server root on sys.path itself and calls sys.exit() with its own
# status. Running it as "__main__" reproduces exactly what a direct invocation does.
os.chdir(_HERE.parent)
runpy.run_path(str(_ORACLES), run_name="__main__")
