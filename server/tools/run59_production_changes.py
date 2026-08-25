"""
RUN 59. THE PRODUCTION FILES THIS RUN CHANGED, DECLARED.

WHY THIS FILE EXISTS, and it is the Run-28/29/30/31/32/33/36/41/42/43/44/51 precedent unchanged.
The Run-20 baseline freeze compares production bytes against a pinned baseline, and the
declared-changes guard requires the differing set and the declared set to be EXACTLY equal -- so
an undeclared production edit is red, and a declared file that was never touched is red too.

IT IS DECLARED HERE AND NOT FOLDED INTO AN EARLIER RUN'S LIST. A run's manifest is the record of
what THAT run did, and merging them would falsify both.

RUN 59 IS THE OWNER'S RULING THAT NO MARKDOWN DOCUMENT IN THIS REPOSITORY CARRIES AUTHORITY. It
declares only the production paths no earlier manifest already names. `assets/js/decision-ui.js`,
`server/app/research_export.py`, `server/app/evm_consistency.py`,
`server/app/simulation/portfolio_health.py` and `server/app/simulation/models.py` are NOT declared
here, because earlier manifests already declare each of them and no path may appear in two -- one
change may never be counted as two.

WHAT THIS RUN CHANGED IN THOSE ALREADY-DECLARED FILES, recorded here so the reader of this
manifest is not left to infer it from a checksum. IN EVERY ONE OF THEM WHAT MOVED IS A COMMENT
AND NOTHING ELSE:

  * `assets/js/decision-ui.js` -- SEQUENCE-BEARING, and its move carries a NAMED EXCEPTION OF
    RECORD in participant_packages.V23_TO_V24_SEQUENCE_EXCEPTION. The block comment heading the
    module and category NAME tables gave as its reason that the analytical layer's ids "must
    never appear in participant-facing text". That prohibition was SUPERSEDED by the owner on
    2026-08-23. The comment now records that displayed identifiers are acceptable and that the
    table holds NAMES because a name is what a participant can read. NOT ONE entry of GROUP_NAMES
    or MODULE_NAMES changed, and the file is byte-identical to v23 once block comments are
    stripped, which test_run28_participant_packages.py asserts.
  * `server/app/research_export.py` -- the comment cited "NAMING_AUTHORITY.md rule 6" BY NUMBER,
    and rule 6 is the line phase A removed. Citation dropped, reason stated directly.
  * `server/app/evm_consistency.py` -- the same superseded rule, cited unnumbered. Citation
    dropped. The em-dash half of what it cited is KEPT, because that half stands.
  * `server/app/simulation/portfolio_health.py` -- cited "NAMING_AUTHORITY section 4", which is
    the section that RECORDED THE REVERSAL, so the code cited the reversal as the source of the
    rule. Citation dropped.
  * `server/app/simulation/models.py` -- the stamp advances to sim-2026.08-v39 and its boundary
    note is written.

Each entry is (authority, path, why).
"""

from __future__ import annotations

_OWNER = ("owner's order of 2026-08-25, Run 59 sections 2, 6.3 and 6.5: no markdown document in "
          "this repository carries authority; correct or drop the code citations of the "
          "superseded module-identifier rule; and let the module count float, marked as the "
          "figure at a date rather than stated as a settled fact")

#: Production files Run 59 CREATED.
RUN59_NEW_PRODUCTION_FILES: dict[str, str] = {}

#: Production files Run 59 CHANGED.
RUN59_PRODUCTION_CHANGES: dict[str, tuple[str, str, str]] = {
    "R1": (_OWNER, "server/app/document_evidence.py",
           "SECTION 6.3, D2. The comment above `_FINDINGS` cited NAMING_AUTHORITY for a "
           "prohibition on module ids, numbers and 'Cat N' in the `bearing` string. The owner "
           "SUPERSEDED that prohibition on 2026-08-23 and no markdown document carries "
           "authority, so the citation is DROPPED and the reason stated directly: the string is "
           "read by someone deciding what to do about a document, and a key tells them nothing. "
           "Displayed identifiers are permitted and are simply not useful here. WHAT MOVED IS A "
           "COMMENT AND NOTHING ELSE. Not one executable byte moved, no `_FINDINGS` row moved, "
           "no field, threshold, wording or rendered string moved, and the behaviour digest is "
           "RE-DERIVED and unchanged."),
    "R2": (_OWNER, "p0-baseline/MODULE_TAXONOMY.md",
           "SECTION 6.5, D7. THE COUNT FLOATS. The title stated '101 distinct computations' as "
           "a settled fact. It now states, as the figure at 2026-08-25 and not as a settled "
           "fact, that 101 are registered and 63 are in service, and records that the module set "
           "is not settled and that this document carries no authority. NO NEW NUMBER IS "
           "INVENTED: 101 and 63 are the executed figures from registry_index() and "
           "service_index(). The two strings test_run28_closure.py:132 required -- 'single "
           "source of truth' and 'module_renumbering_map.csv' -- are preserved unmoved on line "
           "3. This file is a PRODUCTION-TREE MEMBER, which is why correcting it is a mint and "
           "why it is declared here."),
}
