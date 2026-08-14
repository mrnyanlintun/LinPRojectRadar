"""
RUN 21. THE DECLARED PRODUCTION CHANGES OF THIS RUN.

WHY A SECOND MANIFEST RATHER THAN AN EDIT TO THE FIRST. `run20_production_changes.py` is Run
20's record of what Run 20 changed, checked against `code_audit/run20_production_freeze.sha256`,
production as it stood at the Run-20 STARTING commit. That freeze is deliberately immovable: a
baseline regenerated whenever production changes agrees with production by construction and can
never catch an undeclared edit. Adding Run-21 files to the Run-20 manifest would make Run 20
appear to have made changes it did not make, which is a falsified record, and the honest
alternative is a separate declaration that the same guard reads alongside it.

THE GUARD'S PROPERTY IS UNCHANGED AND IS NOT WEAKENED BY THIS FILE. The set of production files
whose bytes differ from the Run-20 freeze must still equal EXACTLY the union of what the two
manifests declare. An undeclared production edit is still red. A declared file that was never
touched is still red. Neither side is derived from the other: one is a hash of bytes on disk,
the other is hand-written here.

Each entry is (queue item or reason, path, why).
"""

from __future__ import annotations

#: Production files Run 21 changed, with the Run-20 queue item that authorised each.
RUN21_PRODUCTION_CHANGES: dict[str, tuple[str, str, str]] = {
    "QUEUE.3 simulations": (
        "Run-20 Run-21 queue item 3",
        "assets/js/simulations.js",
        "The browser instrument went on publishing the four regulatory claims Run 20 cycle 2 "
        "WITHDREW from the server, to a researcher on research/deepdive.html, for the whole of "
        "Run 20. Withdrawn here to match the server exactly: the FAR part number attached to an "
        "uncited 25% overrun level and the sentence REPORTING REQUIRED; the OMB circular reduced "
        "to three thresholds and then said to make reporting MANDATORY; the EVM compliance said "
        "to be BREACHED when no reporting cadence, due date or received date is held anywhere in "
        "this repository; and the constraint rule NAMED after a regulation that states no such "
        "threshold. NO BAND, BOUNDARY, THRESHOLD OR ARITHMETIC RESULT CHANGED and no substitute "
        "threshold was introduced -- only the false attribution and the withdrawn conclusion. "
        "The result keys were renamed to the server's and the server's threshold_provenance and "
        "regulatory_determination disclosures added, so the two now agree key for key. Proved by "
        "executing the shipped JavaScript in node against the shipped server on the same inputs "
        "in server/tools/test_run21_governance_instrument_parity.py, and each guard proved RED "
        "by a real violation there."),
}
