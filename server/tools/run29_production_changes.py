"""
RUN 29. THE DECLARED PRODUCTION CHANGES OF THE CATEGORY 4 AND 5 CANONICAL REMEDIATION.

WHY A SEVENTH MANIFEST. `run20_production_changes.py` through `run28_production_changes.py` each
record what THEIR OWN run changed against the immovable Run-20 freeze in
`code_audit/run20_production_freeze.sha256`. Folding this run's files into any of them would
falsify that run's record. The guard's property is unchanged and is not loosened by a word: the
set of production files whose bytes differ from the Run-20 freeze must equal EXACTLY the union of
what the manifests declare, so an undeclared production edit is still red and a declared file
that was never touched is still red. NO PATH MAY APPEAR IN TWO MANIFESTS, which is why the
changed-file list below is EMPTY: every baseline file Run 29 edited was already declared by an
earlier run, and declaring one twice would let one change be counted as two.

THIS RUN IS OWNER-DIRECTED, on the same footing as Run 28. The owner's supplied Run-29
supervisory contract authorises modifying current analytical production code, modifying data
contracts, and adding structured project-data, event, DSM, system-dynamics, queue, agent and DES
structures, for the Category 4 and Category 5 scope and no wider. The guard was turned RED first
and observed -- it reported exactly

    undeclared: ['server/app/documents.py',
                 'server/app/project_data.py',
                 'server/app/simulation/lineage.py',
                 'server/app/simulation/method_labels.py',
                 'server/app/simulation/models.py',
                 'server/app/simulation/models_doc.py',
                 'server/app/simulation/parameters.py',
                 'server/app/simulation/registry.py']
    and no OTHER file has appeared in the simulation package undeclared:
                ['server/app/simulation/canonical_v4.py']

-- and only then were these declarations written.

FOUR PATHS ARE DELIBERATELY NOT REPEATED HERE, because an earlier manifest already declares them
and one change is never counted twice: `server/app/simulation/models_doc.py` and
`server/app/simulation/registry.py` (Run 20), and `server/app/simulation/models.py` and
`server/app/documents.py` (Run 28). Three further files Run 29 changed -- `project_data.py`,
`lineage.py`, `parameters.py` and `method_labels.py` -- were created AFTER the Run-20 freeze was
taken, so the byte comparison has no baseline row for them and they are declared in their own
list below rather than fed to a comparison that would reject them. What Run 29 changed in each is
recorded in the files themselves, in
REPORT_2026-08-16_run29-cat4-5-canonical-remediation-v13.md, and in the superseding freeze record
research/freeze/RUN29_CANONICAL_CAT4_5_FREEZE_2026-08-16.json.

Each entry is (authority, path, why).
"""

from __future__ import annotations

_OWNER = ("owner supervisory method contract of 2026-08-16 for Run 29: implement the supplied "
          "Category 4 and Category 5 canonical contracts in the new analytical line, supply the "
          "evidence and model structures those methods are defined on, and abstain where a "
          "project does not possess them")

#: EMPTY, AND THAT IS THE GUARD WORKING RATHER THAN A GAP. Every file Run 29 changed that the
#: Run-20 freeze covers is ALREADY declared by an earlier manifest, and no path may appear in
#: two: `models_doc.py` and `registry.py` by Run 20, `models.py` and `documents.py` by Run 28.
#: Declaring any of them again would let one change be counted as two declarations and would
#: make the union equality the guard rests on satisfiable by a file nobody touched twice. What
#: Run 29 changed in each is recorded in the files themselves and in the run report.
RUN29_PRODUCTION_CHANGES: dict[str, tuple[str, str, str]] = {}

#: Files Run 29 changed that the Run-20 freeze CANNOT cover, because they did not exist when it
#: was taken. The byte comparison has no baseline row for them, so they are declared here for the
#: record and are NOT fed to the union equality, which would reject a path absent from the
#: baseline. They are covered instead by the production-tree freeze this run supersedes,
#: research/freeze/RUN29_CANONICAL_CAT4_5_FREEZE_2026-08-16.json, which hashes the whole tracked
#: production surface rather than only the files the Run-20 freeze happened to contain.
RUN29_CHANGES_TO_POST_BASELINE_FILES: dict[str, tuple[str, str, str]] = {
    "R29.2 the governed intake vocabulary": (
        _OWNER,
        "server/app/project_data.py",
        "THE INTAKE READS THE v4 MAP AS WELL. `governed_structure_keys()` is the union of the "
        "canonical, v3 and v4 structure maps rather than the first two. Without this line the "
        "seventeen Category 4 and 5 structures would have been describable in a test and "
        "writable by nothing, which is the exact defect Run 28's closure found and section 15 of "
        "the Run-29 contract forbids repeating. No rule of the store changed: it is still "
        "append-only, still period-effective, still validates nothing for plausibility, and a "
        "document-derived structure still wins over a typed-in one.",
    ),
    "R29.3 the two lineage declarations the rewrites falsified": (
        _OWNER,
        "server/app/simulation/lineage.py",
        "TWO RECORDS REWRITTEN, BECAUSE THE FACTS THEY NAMED ARE NO LONGER THE FACTS THOSE "
        "MODULES READ. A4.6 Change Order Frequency declared the two extracted contract sums and "
        "a change count on the contract-change body, as a same-source transform paired with "
        "B3.5; it now computes from a governed change event register and reads none of the "
        "three, so it declares its own body and B3.5 is alone in the old one. Leaving the pair "
        "would assert a corroboration that has stopped existing, which is the error Run 20 cycle "
        "5 recorded in its other direction. A5.3 Tornado Risk Ranking declared CORRELATED with "
        "A5.2 because each recomputed over the same evidence; it now takes A5.2's RESULT as its "
        "only argument and is declared DERIVED with A5.2 as its dependency, which is what the "
        "supplied contract requires its lineage to show.",
    ),
    "R29.4 the parameter provenance entry the new computation needs": (
        _OWNER,
        "server/app/simulation/parameters.py",
        "A5.1 JOINS THE SWEEP. It abstained unconditionally from Run 7 until Run 29 gave it the "
        "dependency matrix it was waiting for, so it carried no tunable value and needed no "
        "entry. It carries one now, and the cycle-11 sweep subtracts nothing.",
    ),
    "R29.5 the six truthful method labels the rewrites falsified": (
        _OWNER,
        "server/app/simulation/method_labels.py",
        "SIX LABELS REMOVED: A4.6, A4.7, A4.10, A5.3, A5.5 and A5.8. A truthful method label is "
        "a statement about what the code DOES, and each of those six now does what its "
        "registered name says. Leaving them would be the same untruth this table exists to "
        "prevent, told in the other direction.",
    ),
}

#: Production files Run 29 CREATED. The byte comparison structurally cannot reach these: a file
#: that did not exist when the Run-20 freeze was taken has no baseline row to differ from, so
#: without this declaration a new production file could appear in the simulation package with
#: nothing anywhere recording it. The guard reads this list alongside Run 20's and Run 28's.
RUN29_NEW_PRODUCTION_FILES: dict[str, str] = {
    "server/app/simulation/canonical_v4.py":
        "The v4 canonical method layer for Categories 4 and 5. It defines the seventeen governed "
        "structures the eighteen targets are computed on, and the arithmetic of each supplied "
        "contract: the document risk evidence aggregation with its provenance requirements, the "
        "de-duplicating RFI event count over exposure, the governed submittal disposition "
        "taxonomy, the nonconformance rate over declared exposure, the weather path effect after "
        "allowance and float, the change frequency reported separately from magnitude, the "
        "project's own dispute escalation ladder, the versioned weighted subcontractor "
        "assessment, item-level procurement slack, verified conflict density over declared "
        "exposure, DSM rework propagation under a declared orientation and stopping rule, the "
        "polynomial response surface that serves the sensitivity, tornado and scenario methods, "
        "the stock-and-flow rework model, the M/M/c queue with its stability condition enforced, "
        "the stepped agent-based supply chain, and the event-driven discrete event simulation. "
        "It reads no file, no clock and no database: every structure arrives on the caller's "
        "signal inputs. `tornado_ranking` takes the sensitivity RESULT as its only argument, "
        "which is what makes it structurally incapable of forming an independent evidence body.",
}
