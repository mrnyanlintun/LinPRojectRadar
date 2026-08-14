"""
RUN 26. THE DECLARED PRODUCTION CHANGES OF THE COUNTS, WIRING AND EMPTY-PROJECT RUN.

WHY A FIFTH MANIFEST. `run20_production_changes.py`, `run21_production_changes.py`,
`run23_production_changes.py` and `run25_production_changes.py` each record what their own run
changed against the immovable Run-20 freeze in `code_audit/run20_production_freeze.sha256`.
Folding this run's file into any of them would falsify that run's record. The guard's property
is unchanged: the set of production files whose bytes differ from the Run-20 freeze must equal
EXACTLY the union of what the manifests declare.

`assets/js/neural_flow.js` and `index.html` are NOT repeated here. Run 21 already declares the
first and Run 25 the second; both already differ from the Run-20 freeze, and declaring either
twice would let one change be counted as two. Run 26 changed both again -- the wiring, the
empty-project colour rule and the count wording -- and what those changes were is recorded in
the files themselves, in REPORT_2026-08-14_sitewide-counts-wiring-and-empty.md, and in the
superseding freeze record research/freeze/RUN26_COUNTS_WIRING_EMPTY_FREEZE_2026-08-14.json.

Each entry is (authority, path, why).
"""

from __future__ import annotations

RUN26_PRODUCTION_CHANGES: dict[str, tuple[str, str, str]] = {
    "COUNTS.1 knowledge": (
        "owner instruction of 2026-08-14: reconcile module and scientific-target counts "
        "across the whole site, using the correct number for the correct scope",
        "assets/js/knowledge.js",
        "THE KNOWLEDGE LIBRARY NOW STATES SCOPE RATHER THAN ONE UNQUALIFIED NUMBER. Four "
        "user-visible passages said 100 without saying which population of 100 they meant, "
        "and two of them implied the whole registry. Established at runtime from the "
        "registry: 101 registered modules, 96 at project level and 5 Portfolio Health, of "
        "which the analytical server computes 100; the one it does not is the document risk "
        "score, a value the extraction model supplies. The passages now carry the registry "
        "total and both of its scopes, name the one module that makes the computed figure "
        "differ, and separate registration from activation so a registered advisory or "
        "disabled module is not read as an inflated capability claim. One overclaim was "
        "removed with them: 'the analytical layer runs 100 registered computations' became "
        "the project's 96 registered modules, because the five Portfolio Level modules do "
        "not run on a single project. Display and text only: no count, no threshold, no "
        "status rule, no algorithm and nothing under server/app/simulation/ changed. No "
        "figure in these passages is a literal any more in the sense that matters: each is "
        "checked against the number the registry itself yields, by "
        "server/tools/test_run26_counts_and_wiring.py.",
    ),
}
