#!/usr/bin/env python3
"""
`PORTFOLIO_VALIDATED` after Run 97 removed Group D -- derived, never asserted.

WHAT THIS REPLACES. Until Run 97 the set of validated Portfolio Health identifiers lived in
`app.simulation.portfolio.PORTFOLIO_VALIDATED`. Run 97 goal one (88e6ca0, "D1 Portfolio Health
removed entirely") deleted `simulation/portfolio.py` and `simulation/portfolio_health.py`, struck
the five D1 rows from the registry and the taxonomy authority, and removed the Group D branch
from `run_module`. Six tool scripts still imported that name at module level and had therefore
crashed on import ever since -- three of them generators (`build_run13_evidence.py`,
`build_run32_defensibility_inventory.py`, `build_run36_audit.py`) that other suites import in
turn, so the crash reached further than the six.

WHY A DERIVATION AND NOT A LITERAL EMPTY SET. Writing `PORTFOLIO_VALIDATED = frozenset()` would
bake today's answer into the tooling and go on being "right" if Group D were ever restored, which
is precisely the failure mode Run 97 warned about when it repointed the retired-module oracles at
an explicit roster. This reads the live registry instead: the set is empty because the registry
holds no Group D row, and it repopulates by itself if one is ever written back. Callers that
count on it -- `test_run36_instrument_qualification.py:250`, `test_run36_fault_guards.py:312` --
then get the true answer either way rather than a frozen one.

The removal itself is asserted, with its roster, in `tools/run96_removed.py`
(`REMOVED_AT_RUN97`) and in `tools/test_run17_scientific_methods.py`'s `portfolio_health()`.
Nothing here asserts anything; it only reports what the registry currently holds.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.simulation import registry as _REG  # noqa: E402


def portfolio_validated() -> frozenset[str]:
    """The validated Portfolio Health identifiers the registry holds right now.

    Empty since Run 97. Not a constant: it is recomputed on each call so a restored Group D row
    is visible to every caller without any of them being edited.
    """
    idx = _REG.registry_index()
    return frozenset(m for m in idx if _REG.group_of(m) == "D")


#: Module-level alias, so the six scripts that did `from app.simulation.portfolio import
#: PORTFOLIO_VALIDATED` keep the exact shape they used (a set of ids, tested with `in` and
#: `sorted()`), with only the source of the name changed.
PORTFOLIO_VALIDATED = portfolio_validated()


# -------------------------------------------------------------------------------------------------
# RUN 137. `PortfolioModuleError`, AFTER THE BRANCH THAT RAISED IT WAS REMOVED.
#
# Until Run 97 `registry.run_module` carried a Group D branch that refused a portfolio-level
# identifier on a single-project call with `PortfolioModuleError`. Run 97 deleted the branch AND
# the five D1 rows, so such an identifier is now refused one step earlier and by a different name:
# it is not in the registry at all, and `MissingModuleError` is raised.
#
# The REFUSAL still happens, and every caller that names this class is asserting that it happens --
# `test_run13_module_evidence.py:251` wraps the dispatch in `except PortfolioModuleError` to prove
# the runner will not compute a portfolio module on a single project. That assertion is still true
# and is now true more strongly. The alias keeps it evaluable instead of dying at import.
#
# THIS IS AN ALIAS, NOT A NEW EXCEPTION. Defining a fresh class would silently stop those handlers
# catching anything: the refusal would go uncaught and the check would die rather than pass, or --
# worse -- a bare `except` upstream would swallow it and the check would pass having proved
# nothing. The alias is the removed name pointing at the refusal that replaced it.
# -------------------------------------------------------------------------------------------------

PortfolioModuleError = _REG.MissingModuleError

__all__ = [n for n in dir() if not n.startswith("_")]
