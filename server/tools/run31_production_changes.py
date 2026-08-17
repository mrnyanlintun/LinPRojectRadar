"""
RUN 31. THE DECLARED PRODUCTION CHANGES OF THE CATEGORY 8 AND 9 CANONICAL REMEDIATION.

WHY A NINTH MANIFEST. `run20_production_changes.py` through `run30_production_changes.py` each
record what THEIR OWN run changed against the immovable Run-20 freeze in
`code_audit/run20_production_freeze.sha256`. Folding this run's files into any of them would
falsify that run's record. The guard's property is unchanged and is not loosened by a word: the
set of production files whose bytes differ from the Run-20 freeze must equal EXACTLY the union of
what the manifests declare, so an undeclared production edit is still red and a declared file
that was never touched is still red.

NO PATH MAY APPEAR IN TWO MANIFESTS, which is why the changed-file list below is EMPTY. The two
baseline-covered files Run 31 edited are:

    server/app/simulation/models.py   -- already declared by Run 28
    server/app/project_data.py        -- already declared by Run 30, in its
                                         RUN30_CHANGES_TO_POST_BASELINE_FILES list

Declaring either again would let one change be counted as two and would make the union equality
the guard rests on satisfiable by a file nobody touched twice. What Run 31 changed in each is
recorded in the file itself and in the run report.

THIS RUN IS OWNER-DIRECTED, on the same footing as Runs 28, 29 and 30. The owner's supplied
Run-31 supervisory contract authorises modifying current Category-8/9 analytical and governance
code, modifying evidence qualification and routing, extending the existing governed project-data
intake, and adding regulatory-rule objects, authority matrices, agent/state/message structures,
requirement registers, provenance structures, audit schemas, information-package schemas,
consistency-comparison structures and reporting-cadence structures, for the Category 8 and
Category 9 scope and no wider.

THE GUARD WAS TURNED RED FIRST AND OBSERVED, before any of these declarations was written. It
reported exactly

    and no OTHER file has appeared in the simulation package undeclared:
        ['server/app/simulation/abm.py', 'server/app/simulation/canonical_v6.py',
         'server/app/simulation/models_cat89.py', 'server/app/simulation/qualified_evidence.py',
         'server/app/simulation/regulatory.py']

and the production-tree freeze guard reported

    {'added': ['server/app/simulation/abm.py', 'server/app/simulation/canonical_v6.py',
               'server/app/simulation/models_cat89.py',
               'server/app/simulation/qualified_evidence.py',
               'server/app/simulation/regulatory.py'],
     'removed': [], 'changed': ['server/app/project_data.py',
                                'server/app/simulation/models.py'], 'renamed': []}

Each entry is (authority, path, why).
"""

from __future__ import annotations

_OWNER = ("owner supervisory method contract of 2026-08-17 for Run 31: implement the supplied "
          "Category 8 and Category 9 canonical contracts in the new analytical line, install the "
          "Category-9 evidence-qualification boundary the architecture requires, supply the "
          "governed regulatory, agent-based-governance and evidence-quality structures those "
          "methods are defined on, and abstain where a project does not possess them")

#: EMPTY, AND THAT IS THE GUARD WORKING RATHER THAN A GAP. See the module docstring: both
#: baseline-covered files Run 31 edited are already declared by an earlier run's manifest, and no
#: path may appear in two.
RUN31_PRODUCTION_CHANGES: dict[str, tuple[str, str, str]] = {
    "R31.1 the safety numerator stops being discarded": (
        _OWNER,
        "server/app/extraction_merge.py",
        "THE NUMERATOR OF THE OSHA IDENTITY NEVER REACHED SIGNAL INPUTS. The tier map sent "
        "`osha_recordable_incidents` to None, so the derived rate and the denominator were "
        "emitted and the recordable-case COUNT was dropped. EXECUTING this branch -- not reading "
        "it -- showed why that mattered: when the extractor supplies `incident_rate` directly it "
        "is emitted AS-IS and is never checked against the identity, so a document stating 99.9 "
        "beside a recorded 3-cases/200,000-hours pair emitted 99.9. A consumer reading "
        "`oshaIncidentRate` could not distinguish a rate this platform DERIVED from the identity "
        "from a rate a document ASSERTED. Emitting the count lets the canonical Safety "
        "Performance module compute RecordableCases * 200000 / EmployeeHoursWorked itself from "
        "the two defining quantities. No rate is changed and nothing is fabricated: one "
        "already-extracted field stops being thrown away.",
    ),
    "R31.2 the new safety field is registered": (
        _OWNER,
        "server/app/field_registry.py",
        "`oshaRecordableIncidents` is registered as a SNAPSHOT field, the same kind as "
        "`totalManhours` and `oshaIncidentRate` beside it, so the field the change above emits "
        "has a declared merge kind rather than an implicit one.",
    ),
}

#: Files Run 31 changed that the Run-20 freeze CANNOT cover, because they did not exist when it
#: was taken. EMPTY for the same reason as above: `project_data.py` is already declared in
#: Run 30's post-baseline list, and declaring it a second time would falsify that record.
RUN31_CHANGES_TO_POST_BASELINE_FILES: dict[str, tuple[str, str, str]] = {}

#: Production files Run 31 CREATED. The byte comparison structurally cannot reach these: a file
#: that did not exist when the Run-20 freeze was taken has no baseline row to differ from, so
#: without this declaration a new production file could appear in the simulation package with
#: nothing anywhere recording it. The guard reads this list alongside the earlier runs'.
RUN31_NEW_PRODUCTION_FILES: dict[str, str] = {
    "server/app/simulation/regulatory.py":
        "The governed, versioned regulatory rule layer. Before Run 31 the Category-8 regulatory "
        "identities carried their authority inline -- a FAR applicability decision was a "
        "comparison against a budget-at-completion literal, an A-11 conformance result was a "
        "ratio of a cost index -- and the citation that would tell a reader WHICH RULE was "
        "applied did not exist anywhere in the executable path. This file holds every rule as an "
        "object with a rule id, citation, edition, effective date, applicability conditions, "
        "required evidence and reviewer role, refuses construction without them, and evaluates "
        "defect-first so a superseded edition, unknown applicability, absent evidence or a "
        "missing reviewer cannot reach a positive conformance result. It also holds the frozen "
        "REGULATORY_SNAPSHOT_2026-08-16 supplied by supervisory review, and the prohibited "
        "legal-claim vocabulary the wording guard asserts against. It issues NO legal "
        "determination and contains no state meaning 'compliant'.",
    "server/app/simulation/abm.py":
        "The Agent-Based Governance Model for 8.1. The legacy runner read cpi, spi and "
        "docRiskScore off the flat signal inputs, compared them against literals and emitted a "
        "band: there were no agents, no state, no messages, no clock and no authority. This file "
        "supplies the structural contract the supplied theory requires -- agents with stable "
        "ids, roles, states, authority sets, inboxes and response latencies; an environment with "
        "a simulation clock, an event queue and the declared (delivery_time, sequence) ordering "
        "rule; an Action Boundary and Authority Matrix as POLICY consumed by the model rather "
        "than as a registered module; and deterministic transitions with no random draw and no "
        "invented latency distribution. Authority cannot be self-upgraded: every authorization "
        "passes one test against the matrix. No Bayesian layer exists here and none may be "
        "added.",
    "server/app/simulation/qualified_evidence.py":
        "The Category-9 QualifiedEvidence object and the one governed qualification boundary. "
        "Production's own signal_package.py recorded that the eligibility gate the architecture "
        "requires was not implemented and that nothing gated inputs on evidence quality. This "
        "file supplies the record-level object that closes it: the six qualification states, a "
        "value readable only through value_for(use) so a consumer that ignores the verdict gets "
        "None rather than a number, a use-specific eligibility map so a record may be fresh "
        "enough for historical analysis and stale for a current-period decision, and a "
        "defect-first assess() in which a missing critical input, an unresolved material "
        "conflict, a broken audit chain, a future date, staleness against the use's own rule and "
        "unresolved lineage each block rather than degrade. It complements rather than replaces "
        "qualification_gate.py, which continues to own the project-status vote.",
    "server/app/simulation/canonical_v6.py":
        "The v6 canonical method layer for Categories 8 and 9. It defines the sixteen governed "
        "structures the sixteen targets are computed on and the canonical mathematics or rule "
        "logic of each supplied contract: the OSHA incidence identity, the requirement-register "
        "conformance rates for quality and environment with critical exceptions kept "
        "noncompensatory, permit and jurisdiction applicability determined before conformance, "
        "governed official-assessment ingestion with the worst factor preserved and no invented "
        "aggregation, versioned EVMS applicability and reporting conformance that read no cost "
        "or schedule index, modification authority and documentation governance that never "
        "treats a signature as authority and carries no change count, and the seven "
        "evidence-quality measures. Every function is pure, takes its governed structure, and "
        "emits calibration_pending with NO status_color, because Run 33 owns calibration.",
    "server/app/simulation/models_cat89.py":
        "The sixteen thin operational runners. This is the file that decides which "
        "implementation production actually runs, and it exists because Run 30's own defect was "
        "a correct canonical layer that production never called: canonical_v5 was reached on "
        "ZERO of twenty Category-7 identities while every direct-call proof of it stayed green. "
        "Each runner reads its module's governed structure, qualifies it through Category 9 for "
        "the Category-8 routes, hands it to the canonical function and renders the answer, and "
        "performs no arithmetic of its own so there is nowhere for a proxy to live. Nothing here "
        "reads cpi, spi or docRiskScore. Every Category-9 row carries "
        "category_9_metadata_only and voting_eligible=False, and no row asserts a band.",
}
