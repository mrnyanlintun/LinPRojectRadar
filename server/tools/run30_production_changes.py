"""
RUN 30. THE DECLARED PRODUCTION CHANGES OF THE CATEGORY 6 AND 7 CANONICAL REMEDIATION.

WHY AN EIGHTH MANIFEST. `run20_production_changes.py` through `run29_production_changes.py` each
record what THEIR OWN run changed against the immovable Run-20 freeze in
`code_audit/run20_production_freeze.sha256`. Folding this run's files into any of them would
falsify that run's record. The guard's property is unchanged and is not loosened by a word: the
set of production files whose bytes differ from the Run-20 freeze must equal EXACTLY the union of
what the manifests declare, so an undeclared production edit is still red and a declared file
that was never touched is still red. NO PATH MAY APPEAR IN TWO MANIFESTS, which is why the
changed-file list below is EMPTY: the one baseline file Run 30 edited, `models_gov.py`, is
already declared by Run 20, and declaring it twice would let one change be counted as two.

THIS RUN IS OWNER-DIRECTED, on the same footing as Runs 28 and 29. The owner's supplied Run-30
supervisory contract authorises modifying current Category-6/7 analytical code, modifying
evidence and data contracts, extending the existing governed project-data intake, and adding
decision-table, mass-function, fuzzy/linguistic, belief-rule, epistemic-parameter and
alternatives/criteria structures, for the Category 6 and Category 7 scope and no wider.

THE GUARD WAS TURNED RED FIRST AND OBSERVED, before any of these declarations was written. It
reported exactly

    and no OTHER file has appeared in the simulation package undeclared:
                ['server/app/simulation/canonical_v5.py']

and the production-tree freeze guard reported

    {'added': ['server/app/simulation/canonical_v5.py'], 'removed': [],
     'changed': ['server/app/simulation/models_gov.py'], 'renamed': []}

Each entry is (authority, path, why).
"""

from __future__ import annotations

_OWNER = ("owner supervisory method contract of 2026-08-16 for Run 30: implement the supplied "
          "Category 6 and Category 7 canonical contracts in the new analytical line, supply the "
          "epistemic and decision structures those methods are defined on, and abstain where a "
          "project does not possess them")

#: EMPTY, AND THAT IS THE GUARD WORKING RATHER THAN A GAP. The only file Run 30 changed that the
#: Run-20 freeze covers is `server/app/simulation/models_gov.py`, and Run 20 already declares it.
#: Declaring it again would let one change be counted as two declarations and would make the
#: union equality the guard rests on satisfiable by a file nobody touched twice. What Run 30
#: changed in it is recorded in the file itself and in the run report.
RUN30_PRODUCTION_CHANGES: dict[str, tuple[str, str, str]] = {}

#: Files Run 30 changed that the Run-20 freeze CANNOT cover, because they did not exist when it
#: was taken. The byte comparison has no baseline row for them, so they are declared here for the
#: record and are NOT fed to the union equality, which would reject a path absent from the
#: baseline. They are covered instead by the production-tree freeze this run supersedes.
RUN30_CHANGES_TO_POST_BASELINE_FILES: dict[str, tuple[str, str, str]] = {
    "R30.1 the governed intake vocabulary": (
        _OWNER,
        "server/app/project_data.py",
        "THE INTAKE READS THE v5 MAP AS WELL. `governed_structure_keys()` is the union of the "
        "canonical, v3, v4 and v5 structure maps rather than the first three. Without this line "
        "the nineteen Category 6 and 7 structures would have been describable in a test and "
        "writable by nothing, which is the exact defect Run 28's closure found, section 11 of "
        "the Run-30 contract forbids, and Run 29 had to fix in the same place for the v4 map. No "
        "rule of the store changed: it is still append-only, still period-effective, still "
        "validates nothing for plausibility, and a document-derived structure still wins over a "
        "typed-in one.",
    ),
}

#: Production files Run 30 CREATED. The byte comparison structurally cannot reach these: a file
#: that did not exist when the Run-20 freeze was taken has no baseline row to differ from, so
#: without this declaration a new production file could appear in the simulation package with
#: nothing anywhere recording it. The guard reads this list alongside the earlier runs'.
RUN30_NEW_PRODUCTION_FILES: dict[str, str] = {
    "server/app/simulation/canonical_v5.py":
        "The v5 canonical method layer for Categories 6 and 7. It defines the nineteen governed "
        "structures the twenty-four targets are computed on and the canonical mathematics of "
        "each supplied contract: the severity synthesis over governed signals with duplicate "
        "lineage collapsed (conservative dominance, class-weighted voting, majority with an "
        "explicit tie and quorum policy, and the frozen Worst-2 mean statistic); Dempster-Shafer "
        "over real mass functions with belief, plausibility, the conflict coefficient, Shafer "
        "discounting, an explicit total-conflict refusal and an independence assertion that has "
        "no default; rough-set lower and upper approximations over a decision table; the "
        "single-valued neutrosophic triple with an INDEPENDENT indeterminacy; interval fuzzy "
        "membership with the min/max operators; the Z-number representation with its reliability "
        "kept explicit; normalised probabilistic linguistic term sets; the plithogenic and "
        "hypersoft LABORATORY structures, both non-operational; the belief rule base with a "
        "single fully activated rule and multi-rule aggregation refused; the seven separately "
        "enforced fuzzy-family domains; a real maximum-entropy optimiser solved through the "
        "convex dual; possibility theory as a maxitive measure; and one shared alternatives and "
        "criteria object carrying MARCOS and CRITIC-TOPSIS. Nothing in the file reads cpi, spi "
        "or docRiskScore: every epistemic quantity arrives on a governed structure or the method "
        "abstains.",
}
