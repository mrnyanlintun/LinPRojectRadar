"""
The single declared list of modules Run 20 changed in production.

Run 19 was a no-production-change run, and its category suites and its consolidator each
enforced that by refusing any row recording a production change. Run 20 is authorized to change
production, so that guard is not removed: it is narrowed to this manifest. A row may record a
production change only if its module is named here, and a module named here that records no
change is equally a failure. The guard therefore still catches an accidental production edit,
and it also catches a fix that was made but not declared.

Every entry cites the cycle that changed it and the file that carries the change.
"""

#: module_id -> (cycle, production file, one line on what changed)
RUN20_PRODUCTION_CHANGES: dict[str, tuple[str, str, str]] = {
    "3.7": ("1 P0B", "server/app/simulation/models_ext.py",
            "the budget goes through the shared positive preflight, and an underrunning analog "
            "no longer reports a negative quantity of money at risk"),
    "8.7": ("1 P0B", "server/app/simulation/models_doc.py",
            "the uncited multiplication by ten that turned an incident count into an incidence "
            "rate is removed, so only a reported rate produces a rate"),
    "9.2": ("1 P0B", "server/app/simulation/models_dq.py",
            "a document dated after the period cutoff abstains as malformed instead of banding "
            "as the freshest reading the module has"),
    "9.7": ("1 P0B", "server/app/simulation/models_dq.py",
            "the gap from the last report to the period cutoff is measured on the module's own "
            "existing ladder, so cessation is visible"),
}


def changed(module_id: str) -> bool:
    return module_id in RUN20_PRODUCTION_CHANGES


def expected_flag(module_id: str) -> str:
    return "yes" if changed(module_id) else "no"
