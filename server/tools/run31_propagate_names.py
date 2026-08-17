#!/usr/bin/env python3
"""
RUN 31, PASS 2: propagate the approved current Category-8 names to every CURRENT surface.

WHY A SCRIPT RATHER THAN HAND EDITS. Run 28's closure found the failure this prevents: the
registry saying one thing and the page a reader is shown saying another, at the same moment,
about the same module. The surfaces below are exactly the ones `test_run28_closure.py` already
treats as current, plus the two production registries, so a name cannot land in one and miss
another.

WHAT IS DELIBERATELY NOT TOUCHED. Historical artefacts -- old reports, freezes, the Run-17 audit
population and its category results, captured contract baselines, VALIDATION.md's record of the
JavaScript port -- keep their historical wording. Rewriting them to erase an old name would
destroy the evidence that the name was ever different, which is the same principle that kept the
legacy runners in the tree. The Run-31 source comments that NAME the superseded implementations
(canonical_v6's replacement table, abm.py's owner-override note, lineage.py's removal notes) are
also historical references and stay.

THE 8.1 OVERRIDE IS ENFORCED HERE. 8.1 becomes `Agent-Based Governance Model` and NOT
`Action Boundary & Authority Matrix`; the matrix stays policy/configuration consumed by the ABM.
No Bayesian terminology is introduced.
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]

#: OLD -> NEW. The only renames authorised in this pass.
RENAMES: dict[str, tuple[str, str]] = {
    "B3.1": ("ABM Governance Layer", "Agent-Based Governance Model"),
    "B3.2": ("FAR Threshold Monitor", "FAR/Agency EVMS Applicability Monitor"),
    "B3.3": ("OMB A-11 Check", "Versioned A-11 Capital Programming Conformance Check"),
    "B3.4": ("EVM Reporting Threshold", "EVMS Reporting Compliance Monitor"),
    "B3.5": ("Contract Modification Frequency", "Contract Modification Governance Check"),
    "A6.4": ("Contractor Performance Score", "Contractor Performance Assessment Signal"),
}
#: Unchanged by owner decision, listed so the check below can assert they are already correct.
UNCHANGED = {"A6.1": "Quality Compliance Index", "A6.2": "Safety Performance Index",
             "A6.3": "Environmental Compliance Rate"}

#: Current surfaces. Same list `test_run28_closure.py` uses, plus the registry CSV.
CURRENT_SURFACES = (
    "p0-baseline/module_renumbering_map.csv",
    "assets/js/categories.js",
    "assets/js/taxonomy.js",
    "assets/js/knowledge.js",
    "assets/js/deepdive.js",
    "assets/js/charts3d.js",
    "assets/js/decision-ui.js",
    "assets/js/workspace.js",
    "assets/js/neural_flow.js",
    "assets/js/ds_defensibility_data.js",
    "assets/js/ds_defensibility_evidence.js",
)


def main() -> int:
    changed: dict[str, int] = {}
    for rel in CURRENT_SURFACES:
        p = ROOT / rel
        if not p.is_file():
            print(f"  !! missing surface {rel}")
            continue
        src = p.read_text(encoding="utf-8")
        orig = src
        n = 0
        for _mid, (old, new) in RENAMES.items():
            if old in src:
                n += src.count(old)
                src = src.replace(old, new)
        if src != orig:
            p.write_text(src, encoding="utf-8")
            changed[rel] = n
            print(f"  {rel}: {n} occurrence(s) renamed")
    print(f"surfaces changed: {len(changed)}")

    # Verify no current surface still speaks a retired name.
    offenders = []
    for rel in CURRENT_SURFACES:
        p = ROOT / rel
        if not p.is_file():
            continue
        txt = p.read_text(encoding="utf-8")
        for mid, (old, _new) in RENAMES.items():
            if old in txt:
                offenders.append(f"{rel}:{mid}:{old}")
    print("current surfaces still speaking a retired name:", offenders or "NONE")
    return 1 if offenders else 0


if __name__ == "__main__":
    sys.exit(main())
