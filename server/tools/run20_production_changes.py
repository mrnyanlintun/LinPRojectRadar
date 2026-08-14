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
    "5.2": ("9 P1", "server/app/simulation/models_doc.py",
            "Sensitivity Analysis ranked three quantities of which only ONE was a sensitivity. "
            "The cost-index driver perturbs the index and recomputes the estimate at completion; "
            "the other two were the schedule index's distance from one, halved, and the raw "
            "document risk score, and the estimate at completion is not a function of either. It "
            "now reports the one driver it perturbs, and reports the other two under their own "
            "names as levels that are not ranked and cannot set the band"),
    "6.1": ("9 P1", "server/app/simulation/models_decision.py",
            "Conservative Dominance applied a COUNTING rule, not a dominance rule: a lone Red "
            "signal read Amber and selected routine early warning. It now reports the most "
            "adverse band any present signal reads, which introduces no threshold, weight or "
            "constant. Absent or unrecognised evidence still cannot reach the calmest band, "
            "which is the pre-existing requirement kept unchanged. The governance projection's "
            "decision-layer state is untouched and is reported beside the dominance state"),
    "7.10": ("9 P1", "server/app/simulation/models_fuzzy.py",
             "Pythagorean Fuzzy Sets took the hesitancy from the RAW membership pair and then "
             "adjusted the pair, so the three numbers a reader is shown did not satisfy the "
             "identity that defines the set. The constraint is now enforced on the adjusted pair "
             "and the hesitancy taken from it, which is what the spherical module in the same "
             "file already did"),
    "7.15": ("9 P1", "server/app/simulation/models_fuzzy.py",
             "Possibility Theory did not normalise its possibility distribution, so on some "
             "projects nothing was fully possible, and its necessity was the possibility less an "
             "invented 0.30. The distribution is normalised by its own supremum, a monotone "
             "rescaling that cannot move the dominant band, and the necessity is the dual, one "
             "less the possibility of the complement"),
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
    "FUSION.1 fusion": ("9 P1", "server/app/simulation/fusion.py",
               "an undeclared signal is no longer treated as INDEPENDENT by default. Silence "
               "produced an empty primitive set, which intersects nothing, so an undeclared "
               "signal was selected as its own body of evidence and corroborated everything. It "
               "is now an EXPLICIT UNRESOLVED reading: kept, folded in with the idempotent "
               "worst-band operator so it can never add certainty, never combined by Dempster's "
               "rule, and reported by name. Independence must now be ASSERTED by the caller, "
               "which dst_fuse does and only dst_fuse does"),
    "ARCH.5 evc": ("9 P1", "server/app/simulation/models_evc.py",
               "the six advisory evidence-combination siblings aggregated the same four "
               "assembled arms with equal weight per arm, and three of those four arms are "
               "readings of ONE earned-value measurement, so that measurement held three "
               "quarters of every vote. The arms are now separated into independent bodies by "
               "the existing lineage contract and each body contributes one reading, the most "
               "adverse of its members. NO WEIGHT, correlation coefficient or reliability "
               "discount is introduced. Neutrosophic Logic's absolute count threshold is "
               "expressed as the share it always was, one half, because left absolute it would "
               "have demanded unanimity over two bodies and suppressed a Red earned-value "
               "reading. Interval Fuzzy Sets keeps the more adverse of the two index readings, "
               "which are one body. The Belief Rule Base stops conditioning on the trend breach "
               "as a separate antecedent from the index state"),
    "PARAM.1 registry": ("11 P3", "server/app/simulation/registry.py",
               "every module's published record now carries the provenance of every tunable "
               "value it reads, as a LIST because a module can carry values of more than one "
               "class, together with the sentence stating why nothing here is calibrated. NEW "
               "KEYS ONLY: no arithmetic, band, boundary or constant is touched"),
    "LABEL.1 registry": ("10 P2", "server/app/simulation/registry.py",
               "every module whose registered NAME claims a method the code does not perform, "
               "and every module whose reported claim rests on a canonical structure this "
               "repository does not hold, now carries on its published record the truthful name "
               "of the computation it performs, the structure that is absent, and its "
               "disposition. NEW KEYS ONLY: no arithmetic, band, boundary or constant is "
               "touched, the registry CSV keeps its registered names, and the participant "
               "ledger's three accessors are untouched, so the frozen instrument is not renamed "
               "mid-study. That rename is recorded as an owner decision instead"),
}

#: PRODUCTION FILES CREATED BY RUN 20. A new file cannot differ from a freeze taken before it
#: existed, so the byte comparison can never see one. Declaring them here is what stops a whole
#: new production module being added without any declaration at all.
#:
#: relative path -> (the cycles that have changed it, in order, what the file is)
RUN20_NEW_PRODUCTION_FILES: dict[str, tuple[tuple[str, ...], str]] = {
    "server/app/simulation/qualification_gate.py": (
        ("3 P0D",), "the Category-9 operational qualification gate: the preflight over a project "
                    "evidence package, the qualified signal whose band and value cannot be read "
                    "around its verdict, and the converter that refuses a raw bypass"),
    "server/app/simulation/lineage.py": (
        ("3 P0D", "4 P0D", "5 P0D"),
        "the framework-level evidence lineage vocabulary, records and partition, read by the "
        "combination rule and by the qualification gate. Cycle 4 added the declared lineages of "
        "the two advisory duplicate pairs, Change Order Frequency with Contract Modification "
        "Frequency and Sensitivity Analysis with Tornado Risk Ranking, and the contract change "
        "record as a body of evidence in its own right. DECLARATION ONLY: no band, boundary, "
        "threshold or arithmetic result of any module changed. Cycle 5 corrected three declarations "
        "that named the wrong module: A1.1 was declared the cost performance index and is Monte "
        "Carlo EAC, A3.5 was declared a sensitivity sweep inside the earned-value body and is "
        "Overhead Absorption Rate resting on the indirect cost ledger, and the A2.1 entry was "
        "removed because that module abstains on an absent canonical structure on every project "
        "and so emits no signal whose evidence there is anything to declare"),
    "server/app/simulation/arm_lineage.py": (
        ("9 P1",),
        "ARCH.5. The four assembled signal arms declared ONCE for every module that reads them, "
        "and the weight-free deduplication that gives each independent body of evidence exactly "
        "one reading, the most adverse of its members. The declarations are the ones cycle 7 "
        "established by execution and are moved here byte for byte; the separation resolves them "
        "against the project's own evidence first, using cycle 8's derived-index resolver, so "
        "the schedule index's two ancestries are the project's property and not the module's"),
    "server/app/simulation/parameters.py": (
        ("11 P3",),
        "PARAM.1. The parameter provenance register: for every module carrying a tunable value, "
        "the class of that value and the provenance of the class, plus the one sentence stating "
        "why no calibration was performed and what a calibration would have required. It "
        "introduces no number that any computation reads and moves no boundary. It refuses at "
        "construction both a class outside the permitted vocabulary and a claim of published, "
        "theoretical, regulatory, contractual or calibrated provenance with no source named"),
    "server/app/simulation/method_labels.py": (
        ("10 P2",),
        "LABEL.1. The truthful method label table: for each module whose registered name claims "
        "a method the code does not perform, the name of the computation actually performed, "
        "the canonical structure that is absent stated in plain words, and the disposition. It "
        "carries no arithmetic and no constant that any computation reads, and it refuses at "
        "construction both a truthful name that merely repeats the registered claim and a "
        "disposition outside the permitted vocabulary"),
}


def changed(module_id: str) -> bool:
    return module_id in RUN20_PRODUCTION_CHANGES


def expected_flag(module_id: str) -> str:
    return "yes" if changed(module_id) else "no"
