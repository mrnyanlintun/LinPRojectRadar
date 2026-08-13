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
    "8.2": ("2 P0C", "server/app/simulation/models_gov.py",
            "the twenty-five per cent review level no longer carries the name and part number "
            "of a regulation that states no such threshold, and no reporting obligation is "
            "asserted from a cost ratio"),
    "8.3": ("2 P0C", "server/app/simulation/models_gov.py",
            "MANDATORY REPORTING TRIGGERED is removed: the two conditions remain as internal "
            "observations and no obligation under the circular is concluded from them"),
    "8.4": ("2 P0C", "server/app/simulation/models_gov.py",
            "performance indices below an internal review level are no longer reported as "
            "reporting-threshold breaches, and the result states that reporting compliance is "
            "not assessed"),
    "10.3": ("2 P0C", "server/app/simulation/models_gov.py",
             "the rule named FAR threshold is renamed for the forecast-overrun comparison it "
             "actually is, since no provision states it"),
}


#: THE ARCHITECTURAL CHANGES, DECLARED SEPARATELY AND FOR A REASON. The manifest above is keyed
#: by scientific module id, and the guard that reads it requires every key to be one of the
#: hundred targets. Cycle 3 changes the COMBINATION RULE, which is not a module and has no module
#: id, so declaring it above would have meant either inventing a module id for it or widening the
#: guard's module check until it no longer checked anything. It is declared here instead, under
#: the register's own architectural row ids, and the byte comparison covers both dictionaries.
#:
#: architectural id -> (cycle, production file, one line on what changed)
#: The key is the register row id followed by the file's own short name, because one
#: architectural row can reach more than one production file and a dictionary cannot hold the
#: same key twice. The guard splits on the space and checks the row id against the register.
RUN20_ARCHITECTURAL_CHANGES: dict[str, tuple[str, str, str]] = {
    "ARCH.2 compute": ("3 P0D", "server/app/simulation/compute.py",
                       "the live voting path supplies each vote's declared lineage to the "
                       "combination, and each category's fused status inherits the bodies of "
                       "evidence behind it so two categories resting on one body cannot "
                       "corroborate each other either"),
    "ARCH.2 fusion": ("3 P0D", "server/app/simulation/fusion.py",
               "the combination rule partitions its signals into bodies of evidence before "
               "combining them, so two transforms of one body no longer corroborate each other, "
               "and a quality, governance or decision output is refused as project evidence"),
}

#: PRODUCTION FILES CREATED BY RUN 20. A new file cannot differ from a freeze taken before it
#: existed, so the byte comparison can never see one. Declaring them here is what stops a whole
#: new production module being added without any declaration at all.
#:
#: RUN 20 CYCLE 4 WIDENED THIS ENTRY FROM ONE CYCLE TO THE TUPLE OF CYCLES THAT HAVE TOUCHED THE
#: FILE, and the reason is a gap cycle 4's own sweep found in cycle 3's guard. Cycle 4 changes
#: only lineage.py, which is a NEW production file and therefore has no baseline row to differ
#: from. The manifest's cycle-set check reads the cycles off the baseline-file declarations, so
#: a cycle that touches nothing but a new file declared itself NOWHERE and the check that exists
#: to catch exactly that would have stayed green. The cycles are read off this list too now.
#:
#: relative path -> (the cycles that have changed it, in order, what the file is)
RUN20_NEW_PRODUCTION_FILES: dict[str, tuple[tuple[str, ...], str]] = {
    "server/app/simulation/qualification_gate.py": (
        ("3 P0D",), "the Category-9 operational qualification gate: the preflight over a project "
                    "evidence package, the qualified signal whose band and value cannot be read "
                    "around its verdict, and the converter that refuses a raw bypass"),
    "server/app/simulation/lineage.py": (
        ("3 P0D", "4 P0D"),
        "the framework-level evidence lineage vocabulary, records and partition, read by the "
        "combination rule and by the qualification gate. Cycle 4 added the declared lineages of "
        "the two advisory duplicate pairs, Change Order Frequency with Contract Modification "
        "Frequency and Sensitivity Analysis with Tornado Risk Ranking, and the contract change "
        "record as a body of evidence in its own right. DECLARATION ONLY: no band, boundary, "
        "threshold or arithmetic result of any module changed"),
}


def changed(module_id: str) -> bool:
    return module_id in RUN20_PRODUCTION_CHANGES


def expected_flag(module_id: str) -> str:
    return "yes" if changed(module_id) else "no"
