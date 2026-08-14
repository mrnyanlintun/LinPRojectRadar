"""
RUN 28. THE DECLARED PRODUCTION CHANGES OF THE CATEGORY 1 TO 3 CANONICAL REMEDIATION.

WHY A SIXTH MANIFEST. `run20_production_changes.py`, `run21_production_changes.py`,
`run23_production_changes.py`, `run25_production_changes.py` and `run26_production_changes.py`
each record what THEIR OWN run changed against the immovable Run-20 freeze in
`code_audit/run20_production_freeze.sha256`. Folding this run's files into any of them would
falsify that run's record. The guard's property is unchanged and is not loosened by a word: the
set of production files whose bytes differ from the Run-20 freeze must equal EXACTLY the union of
what the manifests declare, so an undeclared production edit is still red and a declared file
that was never touched is still red.

THIS IS THE RUN THAT CHANGES ANALYTICAL PRODUCTION CODE, AND IT IS OWNER-DIRECTED. Every run
since Run 20 has left `server/app/simulation/` byte-identical, and the declared-changes guard has
enforced that. Run 28 is explicitly authorised by the owner's supplied supervisory contract to
modify v3 analytical production code, data contracts and schemas for the Category 1 to 3 scope.
The guard was turned RED first and observed -- it reported exactly

    undeclared: ['assets/js/ds_defensibility_evidence.js',
                 'p0-baseline/module_renumbering_map.csv',
                 'server/app/documents.py',
                 'server/app/simulation/models.py',
                 'server/app/simulation/models_evm.py']
    and no OTHER file has appeared in the simulation package undeclared:
                ['server/app/simulation/canonical_v3.py']

-- and only then were these declarations written. The change of contract is recorded as an
owner-directed change in `code_audit/run20_anti_fossilization_register.csv`, exactly as Run 25
recorded the rail removal and Run 26 the not-relevant colour reversal.

FIVE PATHS ARE DELIBERATELY NOT REPEATED HERE. `server/app/simulation/models_ext.py`,
`registry.py` and `method_labels.py` are already declared by `run20_production_changes.py`, and
they already differ from the Run-20 freeze; declaring any of them twice would let one change be
counted as two and would turn the no-duplicate check red. Run 28 changed all three again, and
what those changes were is recorded in the files themselves, in
REPORT_2026-08-14_run28-cat1-3-canonical-remediation-v3.md, and in the superseding freeze record
research/freeze/RUN28_CANONICAL_CAT1_3_FREEZE_2026-08-14.json.

Each entry is (authority, path, why).
"""

from __future__ import annotations

_OWNER = ("owner supervisory method contract of 2026-08-14 for Run 28: implement the supplied "
          "Category 1 to 3 canonical contracts in the new analytical line, supply the data "
          "structures those methods are defined on, and abstain where a project does not "
          "possess them")

RUN28_PRODUCTION_CHANGES: dict[str, tuple[str, str, str]] = {
    "R28.1 version boundary and the calibration-pending contract": (
        _OWNER,
        "server/app/simulation/models.py",
        "THE NEW ANALYTICAL LINE, AND THE CONTRACT THAT LETS A METHOD REPORT A FIGURE WITHOUT "
        "ASSERTING A COLOUR. SIMULATION_VERSION moves to sim-2026.08-v11, the next unused "
        "identifier in the sequence Runs 7 through 16 built, and SIMULATION_VERSION_HISTORY "
        "records every stamp this layer has ever carried so a run that overwrote one instead of "
        "appending is detectable. `calibration_pending()` is added: a result carrying a real "
        "canonical figure, `status_color` None, `band_asserted` False and `calibration_pending` "
        "True, which is NOT an abstention and which the registry routes to the computed rows. It "
        "exists because twenty-one modules now report a quantity that is not the quantity their "
        "old, already-uncited, band ladder was drawn over, and the supplied contract forbids "
        "inventing a threshold for an uncalibrated measure. A2.1 PERT Network Criticality and "
        "A3.1 Reference Class Forecasting, which abstained unconditionally since Run 7 and Run "
        "10B because no production path supplied their structure, gain that supply path and now "
        "compute when a project carries one. A2.2 Line of Balance gains the planned production "
        "rate beside the actual one and A2.3 CCPM Buffer Health gains the contract's buffer "
        "consumed and buffer consumption ratio, with the fever-chart lines reported as the "
        "policy lines they are rather than as an asserted status.",
    ),
    "R28.2 the v3 canonical method layer": (
        _OWNER,
        "server/app/simulation/canonical_v3.py",
        "A NEW PRODUCTION FILE: the governed v3 structures for Categories 1 to 3 and the "
        "canonical arithmetic defined on them. Twenty-three structure keys, each with the plain "
        "words a reader sees when it is absent, and pure functions for every supplied contract: "
        "the Beta-PERT moments, the normal-normal posterior, the scalar Kalman recursion, an "
        "identified ARIMA workflow with AICc selection and residual diagnostics, earned schedule "
        "by interpolation on the cumulative planned value curve, the execution ratio against an "
        "approved expenditure baseline, partial pooling toward a reference class, the "
        "independent EAC reconciliation with its independence CHECKED rather than asserted, a "
        "schedule network with forward and backward passes serving five Category-2 methods, "
        "stochastic criticality and schedule risk that recompute the network on every trial, "
        "line of balance production rates, the CCPM buffer consumption pair, the remaining "
        "duration demand ratio, network-derived float consumption, the S-curve point deviation "
        "and trend, milestone variance against the original commitment, the look-ahead ready "
        "fraction, time-phased resource load ratios, reference class forecasting, contingency "
        "burn, output per labour hour, overhead absorption over an explicit allocation base, a "
        "simulated cost-risk distribution, analogous adaptation, the laboratory parametric cost "
        "model, and escalation from a named external index. ONE quantile convention is frozen "
        "for the whole line in `empirical_quantile` and every percentile this platform reports "
        "goes through it. Nothing here reads a file, a clock or a database, and no band, "
        "boundary or threshold appears anywhere in it.",
    ),
    "R28.3 the Category 1 module runners": (
        _OWNER,
        "server/app/simulation/models_evm.py",
        "SEVEN CATEGORY-1 MODULES NOW CARRY OUT THE METHOD THEY ARE NAMED FOR, OR ABSTAIN. "
        "A1.3 Bayesian EAC required a governed model record with a prior, its source, an "
        "observation model and the basis its variance was estimated from, in place of two "
        "designed constants; A1.4 Kalman a state-space record whose process and measurement "
        "variances state where they came from, in place of the literals 0.01 and 0.1; A1.5 an "
        "identified ARIMA workflow in place of an AR(1) on first differences; A1.6 Earned "
        "Schedule interpolation on a cumulative planned value curve in place of actual percent "
        "over planned percent; A1.9 Budget Execution Rate an approved time-phased expenditure "
        "baseline in place of budget times percent complete; A1.10, RENAMED CPI Shrinkage "
        "Forecast on the owner's authority, partial pooling toward a governed reference "
        "population in place of a fixed one-half shrinkage toward the project's own history; "
        "and A1.11, RENAMED Independent EAC Reconciliation Index on the owner's authority, two "
        "provenance-distinct forecasts in place of two transformations of one reported vector. "
        "A1.7 TCPI and A1.8 Variance at Completion are the two scientific passes and are NOT "
        "touched: their arithmetic, their bands, their citations and their votes are "
        "byte-identical, which the suites assert by name.",
    ),
    "R28.4 the corpus supply paths": (
        _OWNER,
        "server/app/documents.py",
        "TWO STRUCTURES ARE NOW ASSEMBLED FROM EVIDENCE THIS PLATFORM ALREADY HOLDS, which is "
        "the supply-path half of the run rather than the method half. `milestoneForecastHistory` "
        "gives Milestone Trend Analysis the committed baseline date it needs to measure a "
        "variance against: each activity's baseline finish was already extracted and stored per "
        "period and was reaching no module, so this is a wiring gap closed rather than a fact "
        "invented, and an activity with no parseable baseline finish is left out rather than "
        "given a substitute. `costRiskModel` gives Cost Risk Analysis P80 the risk events it "
        "needs: the comment this file has carried since the risk-register run said the register "
        "was being served to a module with no slot for it and that the change to reach for it "
        "was left to be authorised, and the owner's Run-28 contract authorises it. Each usable "
        "register row becomes one event carrying the register's OWN probability and cost impact "
        "and nothing else; a row the register could not give both figures for is already "
        "refused upstream and never reaches the model. No impact distribution is invented: a "
        "register states one figure, so the declared family is POINT.",
    ),
    "R28.5 the registry identity": (
        _OWNER,
        "p0-baseline/module_renumbering_map.csv",
        "THE TWO APPROVED CATEGORY 1 TO 3 RENAMES, AND NO OTHERS. A1.10 Regression to Mean CPI "
        "becomes CPI Shrinkage Forecast and A1.11 ICE Ratio becomes Independent EAC "
        "Reconciliation Index, both on the owner's explicit authority in the supplied contract. "
        "This file is the single source of truth the server registry and the frontend registry "
        "are both generated from, so the rename reaches both without either being edited by "
        "hand. `assets/js/taxonomy.js` is NOT changed: it is the participant ledger's own name "
        "source, it is inside the frozen and checksummed participant package, and the study is "
        "mid-sequence, so renaming what a participant reads would change the treatment. That is "
        "the same boundary method_labels.py has drawn since Run 20 and it is not crossed here. "
        "RUN 28 CLOSURE ADDENDUM, recorded rather than rewritten: the owner\'s closure "
        "instruction REVERSES the taxonomy.js decision above. It requires the current v11 "
        "surface to be consistent, explicitly permits a successor package and freeze record if "
        "the checksum changes, and requires the predecessor to be preserved. taxonomy.js is "
        "therefore renamed in R28.7 below, the predecessor package checksums are untouched, and "
        "the successor freeze record names the predecessor as its parent. The experimental "
        "sequence and every band, boundary and arithmetic result are unchanged: only display "
        "strings moved.",
    ),
    "R28.6 the published defensibility evidence": (
        _OWNER,
        "assets/js/ds_defensibility_evidence.js",
        "REGENERATED FROM THE REGISTRY, NOT EDITED. This file is generated by "
        "server/tools/build_run11_defensibility_evidence.py and two suites assert it is "
        "byte-identical to what that generator produces, so it necessarily moves when the "
        "registry does. The only change is the two approved names. It is a methods-documentation "
        "surface, which is one of the three places Run 20 established a truthful or corrected "
        "name may reach -- the interface response, the export and the methods documentation -- "
        "and it is not a participant ledger surface.",
    ),
    # ---------------------------------------------------------------- RUN 28 CLOSURE
    #
    # The owner's closure instruction requires Run 28's own defects closed before Run 29. Three
    # of them change production: the approved renames were declared in the registry and never
    # propagated to the surfaces a reader actually sees; the A1.1 naming drift was recorded and
    # left open; and the twenty abstentions had no intake path behind them. Each file below is
    # named individually with what changed in it and why, on the same footing as every entry
    # above and no wider.
    "R28.7 the approved renames on every current surface": (
        _OWNER,
        "assets/js/taxonomy.js",
        "THE MIXED STATE CLOSED. Run 28 renamed A1.10 and A1.11 in the registry and deliberately "
        "did not touch this file, leaving the instrument saying two different things about the "
        "same module at the same time: the registry and the generated defensibility evidence "
        "carried the approved names while the taxonomy a reader is shown carried the old ones. "
        "The owner's closure instruction requires the current v11 surface to be consistent and "
        "explicitly permits a successor package, version and freeze record where the checksum "
        "changes, with the predecessor preserved. This file also carries the A1.1 drift, which "
        "is closed IN THE OTHER DIRECTION: the surface is aligned to `Monte Carlo EAC`, the name "
        "p0-baseline/module_renumbering_map.csv records, and the authority itself is NOT edited. "
        "DISPLAY STRINGS ONLY. Every `method_class` constant, every `required` key list, every "
        "id and every number in the file is byte-identical, so no module's inputs, routing or "
        "arithmetic changed and no step of the participant decision sequence moved.",
    ),
    "R28.7a the registry the taxonomy is generated from": (
        _OWNER, "assets/js/categories.js",
        "The same three display names, in the file MODULE_TAXONOMY.md states is generated from "
        "the renumbering map. It disagreed with its own source on all three. Names only.",
    ),
    "R28.7c the researcher deep dive": (
        _OWNER, "assets/js/deepdive.js",
        "Panel headings and one metric label. Names only.",
    ),
    "R28.7d the module charts": (
        _OWNER, "assets/js/charts3d.js",
        "Two chart section headings and one drawn caption. Names only; no scale, series or "
        "value changed.",
    ),
    "R28.7e the decision card labels": (
        _OWNER, "assets/js/decision-ui.js",
        "The module id to display name table a decision card reads. Names only.",
    ),
    "R28.7f the workspace labels": (
        _OWNER, "assets/js/workspace.js",
        "The same table on the workspace surface. Names only.",
    ),
    "R28.7g the defensibility data": (
        _OWNER, "assets/js/ds_defensibility_data.js",
        "The module names and the permitted-claim sentences that quote them, so a claim limit "
        "cannot name a module that no longer exists under that name. Names only.",
    ),
    "R28.8 the supply path the abstentions rest on": (
        _OWNER,
        "server/app/writes.py",
        "THE `saveprojectdata` ACTION. Run 28 made twenty of the twenty-eight Category 1 to 3 "
        "modules abstain because the structure their canonical method is defined on is absent "
        "from the corpus, which is only defensible if the platform can RECEIVE that structure. "
        "It could not: twenty-one of the twenty-three v3 structure keys were written by no "
        "production code and appeared only in test fixtures. This is the intake, on the ordinary "
        "/exec write path with the ordinary session authorisation, verified-write and "
        "append-only rules. It SUPPLIES NOTHING: a record that does not satisfy the canonical "
        "contract still makes the module abstain, because canonical_v3 decides that. No existing "
        "handler, no existing action and no existing response shape changed.",
    ),
    # NOT DECLARED HERE, AND THAT IS THE GUARD WORKING RATHER THAN A GAP. Three files this
    # closure changed are already declared by an EARLIER manifest and no path may appear in two:
    # `assets/js/knowledge.js` and `assets/js/neural_flow.js` (Run 21 and the post-Run-22 UI
    # correction) carry the same two node and title renames, and
    # `server/app/simulation/models_ext.py` (Run 20) carries A3.6's declared dependence policy on
    # the result. One change is never counted twice.
}

#: Production files Run 28 CREATED. The byte comparison structurally cannot reach these: a file
#: that did not exist when the Run-20 freeze was taken has no baseline row to differ from, so
#: without this declaration a new production file could appear in the simulation package with
#: nothing anywhere recording it. The guard reads this list alongside Run 20's own.
RUN28_NEW_PRODUCTION_FILES: dict[str, str] = {
    "server/app/simulation/canonical_v3.py":
        "The v3 canonical method layer for Categories 1 to 3. See R28.2 above.",
    "server/app/project_data.py":
        "RUN 28 CLOSURE, R28.8. The governed project data object: the INTAKE PATH for the "
        "canonical v3 structures. Run 28 left twenty of the twenty-eight Category 1 to 3 modules "
        "abstaining because their defining structure is absent from the corpus, and the closure "
        "audit found that twenty-one of the twenty-three structure keys were written by NO "
        "production code at all -- they existed in test fixtures and nowhere else. An abstention "
        "whose supply path only a test can exercise is a description of a supply path, not one. "
        "This module is the store: append-only, period-effective so an earlier period recomputes "
        "byte-identically, vocabulary read from canonical_v3 rather than restated, and it "
        "validates nothing for plausibility because canonical_v3\'s own guards decide whether a "
        "structure satisfies its contract. Reached from the API by `saveprojectdata`.",
}
