"""
The module registry: which of the 101 computations this server can actually perform.

The registry reads p0-baseline/module_renumbering_map.csv, the same source of truth the frontend
registry is generated from, so the two cannot drift.

It refuses loudly. A module that has not been ported and numerically validated against the
JavaScript is NOT computed and NOT silently omitted: asking for it raises. An unvalidated module
producing a confident wrong number is the failure this design cannot tolerate, and a shorter
signal array that nobody notices is the same failure wearing a quieter coat.
"""

from __future__ import annotations

import csv
import pathlib
from typing import Any, Callable

from .parameters import (  # noqa: F401
    NO_CALIBRATION_SET, PARAMETER_PROVENANCE_BY_MODULE, provenance as parameter_provenance,
)
from .method_labels import (  # noqa: F401
    PARTICIPANT_SURFACE_OWNER_DECISION, STRUCTURAL_CLAIM_LIMITS, TRUTHFUL_METHOD_LABELS,
    claim_limit, method_label,
)
from .models import SIMULATION_VERSION, STOCHASTIC, VALIDATED  # noqa: F401
from .portfolio import PORTFOLIO_VALIDATED
from .rng import make_rng, seed_from
from .signal_package import (
    ADAPTER_TIERS, CATEGORY_9_DEVIATION, NESTED_INPUT_MODULES, SIGNAL_QUALIFICATION,
    WIRING_NOTE, adapt, array_entry, build_signals, decision_snapshot, supplied_and_absent,
)

CSV_PATH = pathlib.Path(__file__).resolve().parents[3] / "p0-baseline" / "module_renumbering_map.csv"


class MissingModuleError(RuntimeError):
    """Raised when a caller asks for a module this server cannot compute."""


class PortfolioModuleError(RuntimeError):
    """Raised when a single-project computation reaches a Group D module."""


# ---------------------------------------------------------------------------------------------
# Remediation Run 1 (see remediation_programme.md and remediation_decisions_answered.md at the
# repository root). Label strings, the activation-state field, and the fusion-exclusion list
# ONLY -- no arithmetic in this file or anywhere under simulation/ is touched by this run.
# ---------------------------------------------------------------------------------------------

#: The eight concept-only modules the external arithmetic audit found undefensible: none
#: implements the analytical structure its name claims. Non-executable in production, non-voting,
#: excluded from every fusion input and every rollup. run_module() below refuses to call their
#: formula function at all -- see the short-circuit there. Code ids per
#: remediation_decisions_answered.md 1.3.
DISABLED_CONCEPT_ONLY: dict[str, str] = {
    "A3.8": "Parametric Cost Index",
    "B2.7": "Plithogenic Sets",
    "B2.9": "Quantum Probability",
    "B2.20": "Hypersoft Sets",
    "B4.1": "Multi-Objective Optimization",
    "B4.2": "Linear Programming",
    "B4.5": "Decision Sensitivity Matrix",
    "B4.6": "Pareto Frontier Analysis",
}

#: RUN 16, WORKSTREAM C. TEMPORARILY DISABLED PENDING AN EVIDENCE-DESIGN DECISION, WHICH IS A
#: DIFFERENT THING FROM THE EIGHT ABOVE AND IS KEPT IN ITS OWN SET SO THE TWO CANNOT BE CONFUSED.
#:
#: Material Cost Variance is NOT classified as algorithmically invalid and no claim is made here
#: about its arithmetic. The reason is application validity: a construction project can contain
#: thousands of distinct materials, and interpreting a material variance requires evidence this
#: platform does not collect -- a contractual material baseline, the schedule of values or
#: approved contract rates, material specifications, planned quantities, approved and current
#: procurement data, procurement timing, sourcing location, supplier conditions, regional
#: availability, freight and logistics, currency, tariff and duty, approved substitutions,
#: escalation provisions, and trade disruption where it applies. Those conditions differ by
#: region and by date: a material readily available in one market can be scarce or
#: import-dependent in another. The current implementation cannot infer that context from
#: generic project inputs, so it cannot be treated as a universally interpretable automatic
#: material-market detector.
#:
#: THE MODULE REMAINS REGISTERED. It keeps its registry entry, its identity and its audit
#: lineage; only its execution is withdrawn. It was already non-voting (see
#: HELD_NON_VOTING_UNSOURCED_BANDS below, whose entry stays, because the band it lacks is still
#: the band it lacks), so nothing about the voting set changes.
#:
#: The owner has NOT decided whether the module is ultimately retained behind a purpose-built
#: contract material baseline and current procurement report evidence design, or removed because
#: the external market-research burden outweighs its value. That decision is deferred.
DISABLED_EVIDENCE_UNDER_REVIEW: dict[str, str] = {
    "A3.4": "Material Cost Variance",
}

#: The one reason string for the set above, in the repository's own governed vocabulary. It is
#: deliberately NOT the concept-only wording: nothing here says the module's structure is absent
#: or its arithmetic wrong.
EVIDENCE_UNDER_REVIEW_REASON = (
    "Material Cost Variance is disabled pending an evidence and context requirement under "
    "review. Interpreting a material variance needs a contractual material baseline, approved "
    "contract rates and quantities, and current procurement and market context, which this "
    "platform does not collect and cannot infer from generic project inputs. Not executed, not "
    "voting, excluded from every fusion input and rollup. Its registry entry and audit lineage "
    "are retained."
)

#: RUN 36 CLOSURE, THE OWNER'S A1.1 RULING OF 2026-08-19. A THIRD, DISJOINT REASON.
#:
#: The owner resolved the specification ambiguity Run 36 identified: the `Required:` input list in
#: supervisory specification s1.1 GOVERNS what qualifies as canonical A1.1 Monte Carlo EAC
#: Forecast. The permission to "retain" the scalar BAC/CPI/SPI/document-risk adaptation permits it
#: to be PRESERVED as scientific and historical code. It does NOT waive the canonical input
#: contract and does NOT authorize the adaptation to stand in for canonical Monte Carlo execution.
#:
#: Canonical A1.1 requires TWO governed elements: the declared `costDriverDistributions` structure,
#: and an authoritative deterministic mapping from the sampled cost drivers to EAC. The
#: specification requires that mapping and DOES NOT DEFINE IT. Inventing one would be inventing
#: the canonical method, which this programme refuses. Until both exist, A1.1 does not execute
#: operationally as the canonical method.
#:
#: THIS IS NOT A SOFTWARE FAILURE AND THE SENTENCE BELOW DOES NOT SAY IT IS. Nothing is broken:
#: the arithmetic is intact, the structure reader is intact, and the module is not called unsafe.
#: What is absent is a governed scientific input contract, which is why the reason code is
#: CANONICAL_DRIVER_DISTRIBUTION_MAPPING_NOT_GOVERNED and not a missing-value code.
DISABLED_CANONICAL_INPUT_NOT_GOVERNED: dict[str, str] = {
    "A1.1": "Monte Carlo EAC Forecast",
}

#: The machine-readable reason code, kept distinct from every ordinary missing-input code so that
#: an absent scientific CONTRACT is never read as an absent VALUE.
CANONICAL_INPUT_NOT_GOVERNED_CODE = "CANONICAL_DRIVER_DISTRIBUTION_MAPPING_NOT_GOVERNED"

CANONICAL_INPUT_NOT_GOVERNED_REASON = (
    "The cost forecast is not produced. The method this module is named for draws from a declared "
    "set of uncertain cost drivers, and two things it needs are not established: the declared set "
    "of drivers itself, and the rule that turns drawn driver figures into a forecast of the final "
    "cost. The second of those has never been written down anywhere this platform can read, so "
    "there is no defensible way to produce the forecast and none is produced. This is a limit of "
    "the evidence and the method definition, not a fault in the computation. The earlier "
    "budget-and-index approximation is kept in the record for traceability and is not used here."
)

#: Every module this server refuses to execute, whatever the reason. This is the set the
#: enforcement points read, so a new disablement reason cannot be added without every gate
#: picking it up. The two component sets stay separate above because they mean different things
#: and because the eight remain, individually, part of the scientific review population.
DISABLED_MODULES: dict[str, str] = {**DISABLED_CONCEPT_ONLY, **DISABLED_EVIDENCE_UNDER_REVIEW,
                                    **DISABLED_CANONICAL_INPUT_NOT_GOVERNED}

#: The seven CORE modules the audit approves to vote on project status, on an interim basis,
#: until Run 4 validates them and Run 4's acceptance criterion restores voting on a durable
#: footing (remediation_decisions_answered.md 1.1, Option C; 4.3). Every other live module keeps
#: computing and keeps showing in the ledger -- it simply does not feed category rollup, project
#: status fusion, generated recommendation text, courses of action, or the decision card. See
#: compute.py, which is the only place this set is read for fusion purposes.
#
# RUN 4 (VALIDATE THE SEVEN) NARROWED THIS SET, AND THAT IS THE RUN'S RESULT RATHER THAN A
# FAILURE OF IT. A module votes only when all three of the run's bars are cleared: its band
# boundaries are sourced, its abstention guards exist, and its boundary tests pass. Guards were
# built and boundary tests written for all seven. Two have band boundaries a source actually
# specifies; five do not, and no source was stretched to cover them. See BAND_SOURCES below,
# the comment beside each band in the module's own file, and
# REPORT_2026-08-11_run4-validate-seven.md.
CORE_VOTING_MODULES: frozenset[str] = frozenset({
    "A1.7",   # TCPI
    "A1.8",   # Variance at Completion
})

#: The five that stay non-voting after Run 4, each with the reason, so the set is a record and
#: not an absence. They compute, they show their finding on the ledger exactly as before, and
#: they are excluded from category rollup, project status fusion, generated recommendation text,
#: courses of action and the decision card, on the same footing as every other advisory module.
HELD_NON_VOTING_UNSOURCED_BANDS: dict[str, str] = {
    "A2.8": "Look-Ahead Schedule Health: no source specifies a constraint-rate threshold; the "
            "published plan-reliability benchmarks measure a different quantity",
    "A3.2": "Contingency Burn Rate: no source specifies a burn-against-progress threshold, and "
            "the proportional-drawdown premise the band rests on is not what the contingency "
            "literature describes",
    "A3.4": "Material Cost Variance: no source specifies a control limit for a mid-execution "
            "variance against a progress-adjusted baseline; the published accuracy ranges "
            "describe estimate accuracy at preparation",
    "A4.2": "RFI Velocity: no source specifies a per-week request rate or an overdue-share "
            "threshold",
    "A4.3": "Submittal Rejection Rate: no source specifies a rejection-share threshold",
}

#: The citation for every band boundary a voting module carries, recorded here as well as beside
#: the band in the module's own file, so the export and the API can carry it without the
#: frontend or the exporter reaching into a formula file. This is the freeze record's own copy.
BAND_SOURCES: dict[str, str] = {
    "A1.7": (
        "Green at or below 1.00, Amber at or below 1.10, Red above. 1.00 is definitional: "
        "Project Management Institute, A Guide to the Project Management Body of Knowledge, "
        "6th edition, 2017, section 7.4.2.2, and PMI Practice Standard for Earned Value "
        "Management, 2nd edition, 2011, define this index as the cost efficiency the remaining "
        "work must achieve, so at or below 1.00 the remaining budget suffices at the efficiency "
        "already planned. 1.10 applies a sourced number by stated inference: Christensen and "
        "Heise, Cost Performance Index Stability, National Contract Management Journal 25(1), "
        "1993, pages 7 to 15, found the cumulative cost performance index does not move by more "
        "than 0.10 after the twenty per cent completion point, so a demand for more than that "
        "improvement is beyond what the remaining work is observed to deliver."
    ),
    "A1.8": (
        "Green at or above zero per cent, Amber at or above minus 11.11 per cent, Red below. "
        "Zero is definitional: the Project Management Institute (A Guide to the Project Management "
        "Body of Knowledge, 6th edition, 2017, section 7.4.2.2; Practice Standard for Earned "
        "Value Management, 2nd edition, 2011) defines variance at completion as budget minus "
        "forecast, so a negative variance is a forecast overrun. Minus 11.11 per cent is the "
        "exact restatement of a cost performance index of 0.90, because this forecast is the "
        "index-based one, and 0.90 applies the 0.10 stability finding of Christensen and Heise "
        "(National Contract Management Journal 25(1), 1993, pages 7 to 15) by stated inference. The stated limit of that citation: the stability finding is "
        "conditional on the project being past twenty per cent complete and this measure does "
        "not read percent complete, so the condition is not enforced."
    ),
}

#: WHAT THESE CITATIONS DO NOT ESTABLISH, carried in the code because the same sentence has to
#: appear in the export, the methods documentation and the report without being reinvented.
#: They establish that the boundaries come from a published source rather than from nobody. They
#: do not establish how often the measure is right. The auditor's production re-entry gate
#: requires false-positive and false-negative performance measured on labelled holdout cases;
#: no labelled corpus and no expert reference standard exist for this platform, so that
#: performance is unmeasured and no surface may describe these modules as validated without
#: this qualification.
BAND_SOURCE_LIMIT: str = (
    "Band boundaries are sourced to published literature. False-positive and false-negative "
    "performance is not measured: no labelled holdout corpus and no expert reference standard "
    "exist for this platform, so how often a band is right is unknown."
)

#: The thirty proxy modules and the qualifier appended to their canonical name wherever the
#: qualifier is shown. Per remediation_decisions_answered.md 1.4 and Part 4 of the Run 1 prompt,
#: that is the export, the API response (a new field alongside the unchanged module_id and
#: evidence_metric -- see run_module()'s "proxy_qualifier" key below), and the methods
#: documentation. It is NEVER shown on the participant ledger or decision-card surface, which
#: read a module's canonical name from the frontend taxonomy and its finding from
#: evidence_metric, neither of which this run touches.
# RUN 28. ELEVEN ENTRIES ARE GONE FROM THIS DICTIONARY, and they are gone because the proxy is
# gone. A1.3, A1.4, A1.9, A1.10, A2.4, A2.6, A2.7, A3.3, A3.5, A3.7 and A3.9 now carry out the
# canonical method their registered name claims, from a governed structure, and abstain when that
# structure is absent. A qualifier saying "not a governed Bayesian model" or "a labour-hours
# ratio, not an earned-output productivity model" would now be false in the opposite direction:
# it would advertise a weakness the code no longer has. A1.2 keeps its entry, because the CUSUM
# design is frozen and the supplied contract forbids retuning it in Run 28, so what that
# qualifier says about the calibration of k, H and the sigma floor remains true.
PROXY_QUALIFIERS: dict[str, str] = {
    "A1.2": "hard-coded transformations of two-sided CUSUM on real SPI history; k, H, sigma "
            "floor and Amber band uncalibrated",
    # RUN 29. SIX FURTHER ENTRIES ARE GONE, and they are gone for the same reason Run 28's
    # eleven went: the proxy is gone. A4.5, A4.6, A4.7, A4.8, A5.2 and A5.3 now carry out the
    # canonical method their registered name claims, from a governed structure, and abstain when
    # that structure is absent. A qualifier saying "a lost-days over available-float ratio", "an
    # ad hoc 0.3 / 0.3 / 0.4 weighted sum" or "a ranking of four present-state deviations" would
    # now be false in the opposite direction: it would advertise a weakness the code no longer
    # has, which is the error this dictionary exists to prevent in its own direction.
    # RUN 30 CLOSURE. EIGHT FURTHER ENTRIES ARE GONE -- B2.10 to B2.17 -- and for exactly the
    # reason Run 28's eleven and Run 29's six went: the proxy is gone. Every one of the twenty
    # Category-7 production identities now routes through models_cat7.py into the canonical v5
    # layer and abstains when its defining structure is absent, so a qualifier reading
    # "hard-coded transformations of raw CPI, SPI and document risk" or "entropy over designed
    # state probabilities; measures the lookup, not the project" would now be FALSE IN THE
    # OPPOSITE DIRECTION: it would advertise a weakness the code no longer has, which is the
    # error this dictionary exists to prevent in its own direction. The legacy functions those
    # sentences described still sit in models_fuzzy.py as the historical record of the v14/v15
    # line, and no production route reaches them.
    # RUN 32 FINAL CLOSURE. THREE FURTHER ENTRIES ARE GONE -- B3.5, B4.3 and B4.4 -- and for
    # exactly the reason Run 28's eleven, Run 29's six and Run 30's eight went: the proxy is gone.
    # THE RULE WAS STATED HERE AND THEN NOT APPLIED TWICE. Run 31 repointed B3.5 onto
    # models_cat89 and the canonical v6 layer, where it reads a governed contract-modification
    # register; Run 32 repointed B4.3 and B4.4 onto models_cat10 and the canonical v7 layer,
    # where B4.3 solves a real variable/domain/constraint network and B4.4 compares a complete
    # action-by-scenario matrix. Neither run withdrew the qualifier the remediation had made
    # false. So the dictionary went on saying that B4.3 was "an explainable four-rule checklist,
    # not a constraint-satisfaction solver" about a module that IS a constraint-satisfaction
    # solver, and that B4.4 was "four deterministic EAC variants" about a module that refuses to
    # run without a governed matrix. That is the error this dictionary exists to prevent, in the
    # direction it warns about above: advertising a weakness the code no longer has.
    #
    # The sentences are preserved as history in code_audit/run32_proxy_qualifier_reconciliation
    # .csv, one row per withdrawn entry with the run that withdrew it, and the legacy functions
    # they described still sit in models_gov.py and models_fuzzy.py as the historical record with
    # no production route reaching them.
    # RUN 33. THE LAST PORTFOLIO ENTRY IS GONE -- D1.2 -- and for exactly the reason the earlier
    # twenty-eight went: the proxy is gone. The sentence described "an empirical CPI and SPI
    # percentile rank; small-n behaviour and bands unvalidated", and every clause of it is now
    # false of the module it names. D1.2 at v21 ranks the COMPLETE governed required
    # risk-oriented feature set of a declared cohort, not cpi and spi; it uses a MIDRANK
    # percentile with the governed orientation applied before ranking, not a "less than or equal"
    # count; it carries NO bands at all, so no band can be unvalidated; and small-n is not left
    # to a qualifier -- the cohort refuses to rank below three eligible projects and carries an
    # explicit small-sample limitation below ten. Leaving the sentence in place would advertise
    # a weakness the code no longer has, which is the error this dictionary exists to prevent in
    # the direction the note above warns about.
    #
    # The sentence is preserved as history in code_audit/run33_proxy_qualifier_withdrawal.csv,
    # and the legacy implementation it described still sits in portfolio.py as the historical
    # record with no production route reaching it.
}


def activation_state(new_id: str) -> str:
    """
    One of the auditor's required activation states (see remediation_programme.md, "Activation
    states the auditor requires"), for this run's purposes only. Read-only classification -- it
    changes no arithmetic and is not itself consulted by run_module()'s abstention contract
    except for the disabled set, which is short-circuited explicitly below.
    """
    if new_id in DISABLED_CONCEPT_ONLY:
        return "DISABLED_UNSAFE"
    # RUN 16. Its own state, not DISABLED_UNSAFE: this module is not being called unsafe.
    if new_id in DISABLED_EVIDENCE_UNDER_REVIEW:
        return "DISABLED_EVIDENCE_UNDER_REVIEW"
    # RUN 36 CLOSURE. Its own state again, and again not DISABLED_UNSAFE: the module is not being
    # called unsafe. Its canonical input contract is not governed.
    if new_id in DISABLED_CANONICAL_INPUT_NOT_GOVERNED:
        return "DISABLED_INSUFFICIENT_INPUT"
    if new_id in CORE_VOTING_MODULES:
        return "ENABLED_QUALIFIED"
    return "ADVISORY_ONLY"


def _attach_method_label(entry: dict, new_id: str) -> None:
    """
    RUN 20 CYCLE 10. Attach the truthful method label and the claim limit, if this module has
    one. Mutates in place and returns nothing, because it is called from two places that build
    two different shapes of record and both must carry the same claim.

    NOTHING IS INVENTED HERE. Every sentence comes from method_labels.py, and the registered
    name in that file is checked against the registry CSV by the cycle 10 suite, so a rename in
    the registry cannot leave a stale claim standing.
    """
    label = method_label(new_id)
    if label is not None:
        entry.update(label.as_dict())
    limit = claim_limit(new_id)
    if limit is not None:
        entry["claim_limit_disposition"] = limit[0]
        entry["claim_limit"] = limit[1]
    # RUN 20 CYCLE 11. The provenance of every tunable value the module reads, and the sentence
    # stating why no calibration was performed. A module can carry values of more than one
    # class, so this is a LIST: collapsing it to one class would have hidden the isolation
    # forest, whose published defaults sit underneath an invented band ladder.
    params = parameter_provenance(new_id)
    if params:
        entry["parameter_provenance"] = [p.as_dict() for p in params]


def proxy_label(new_id: str, canonical_name: str) -> str | None:
    """
    The canonical name plus its proxy qualifier, in the one fixed form used on every surface the
    qualifier is allowed to appear on (export, API, methods documentation). Returns None for a
    module that is not one of the thirty relabeled proxies.
    """
    qualifier = PROXY_QUALIFIERS.get(new_id)
    if qualifier is None:
        return None
    return f"{canonical_name} (proxy: {qualifier}. Advisory, non-voting.)"


def load_registry() -> list[dict[str, str]]:
    """Every live module from the CSV, in file order."""
    with CSV_PATH.open(encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    return [r for r in rows if r["new_id"].strip().upper() != "RETIRED"]


def registry_index() -> dict[str, dict[str, str]]:
    return {r["new_id"]: r for r in load_registry()}


def available_modules() -> list[str]:
    """
    New ids this server can compute today.

    RUN 43, THE RETIREMENT. This is the INTERSECTION of the implemented set with the registry,
    not `sorted(VALIDATED)`. The registry CSV is the single authority for which modules exist,
    and Run 43 retired thirty-eight of them there by the existing `RETIRED` convention in the
    `new_id` column. `load_registry()` already drops those rows, so intersecting here is what
    makes the retirement take effect on every path that enumerates modules, without a second
    registry file and without deleting the formula functions from the dozen `models_*` files
    that build `VALIDATED`.

    The formulas are deliberately KEPT. Retiring a module is a statement about the taxonomy and
    the explanation burden, not a claim that its arithmetic is wrong, and the audit lineage for
    every retired module has to remain readable. A retired id is unreachable because it is not
    in the registry, which `run_module()` checks first and refuses on; keeping its function
    reachable-by-name would require someone to call it deliberately, bypassing the registry.

    Deriving the live set rather than restating it is also why this run does not repeat the
    failure the programme has now made nine times: a stated set that drifted from the computed
    one. There is no list here to fall out of date.
    """
    return sorted(set(VALIDATED) & set(registry_index()))


def unported_modules() -> list[str]:
    """
    Everything declared in the registry but implemented nowhere.

    The Group D subtraction is the point. This used to be `registry_index() - VALIDATED`, and
    VALIDATED holds only the single-project modules, so all five Group D modules were reported as
    unported even though portfolio.py implements them. It answered 6 where exactly 1 is genuine,
    and two checks in the suite had to compute the unported set themselves to work around it.

    No import cycle: portfolio.py imports only from rng.
    """
    return sorted(set(registry_index()) - set(VALIDATED) - set(PORTFOLIO_VALIDATED))


def group_of(new_id: str) -> str:
    row = registry_index().get(new_id)
    return row["group"] if row else ""


def run_module(new_id: str, si: dict, rand: Callable[[], float],
               period_cutoff) -> dict[str, Any]:
    """
    Compute one module. Raises rather than approximating.

    Group D is a hard error here rather than an abstention: those modules need three or more
    projects, so a single-project path reaching one is a routing mistake, not missing data, and
    reporting it as "insufficient data" would hide the mistake.

    A module in DISABLED_MODULES is short-circuited HERE, before its formula function is ever
    called: it is genuinely non-executable in production, not merely non-voting. No arithmetic in
    the module itself is touched or reached. Two disjoint reasons feed that set and each keeps
    its own activation state and its own sentence -- concept-only (Run 1) and evidence and
    context requirement under review (Run 16) -- because they are not the same finding.
    """
    index = registry_index()
    if new_id not in index:
        raise MissingModuleError(f"{new_id} is not in the module registry")
    if index[new_id]["group"] == "D":
        raise PortfolioModuleError(
            f"{new_id} is a Group D portfolio-level module and requires 3 or more projects; "
            f"it cannot be computed on a single project"
        )
    if new_id in DISABLED_CONCEPT_ONLY:
        # RUN 30 CLOSURE. THE SHARED SENTENCE BECAME FALSE FOR THREE OF THE EIGHT. It says the
        # module has "no production implementation of the analytical structure its name claims",
        # and for B2.7 Plithogenic, B2.9 Quantum and B2.20 Hypersoft that is no longer true: each
        # now has a canonical laboratory structure in canonical_v5.py. What is true of all three
        # is that they are NOT OPERATIONAL, which is a different statement and the one that has
        # to be made. Those three therefore answer with their own runner's refusal, which says
        # so truthfully and carries the canonical result source onto the ledger row.
        #
        # THE GATE IS UNCHANGED IN SUBSTANCE. The refusal is still returned HERE, before the
        # module's mathematics is reached, and those runners read no input at all, so a complete
        # laboratory structure cannot make one of them compute. Completeness is not activation.
        from .models_cat7 import CAT7_CANONICAL
        if new_id in CAT7_CANONICAL:
            return CAT7_CANONICAL[new_id][1](si, rand, period_cutoff)
        return {
            "status_color": None,
            "insufficient_data": True,
            "activation_state": "DISABLED_UNSAFE",
            "evidence_metric": (
                f"{DISABLED_CONCEPT_ONLY[new_id]} is disabled: it is a concept-only module with "
                "no production implementation of the analytical structure its name claims. Not "
                "executed, not voting, excluded from every fusion input and rollup."
            ),
        }
    # RUN 16, WORKSTREAM C. Short-circuited on the same footing and in the same place, before
    # its formula function is reached, so it cannot execute in a production analytical run. Its
    # arithmetic is untouched and unreached.
    if new_id in DISABLED_EVIDENCE_UNDER_REVIEW:
        return {
            "status_color": None,
            "insufficient_data": True,
            "activation_state": "DISABLED_EVIDENCE_UNDER_REVIEW",
            "evidence_metric": EVIDENCE_UNDER_REVIEW_REASON,
        }
    # RUN 36 CLOSURE, THE OWNER'S A1.1 RULING. Short-circuited in the SAME PLACE and on the same
    # footing as the other two disjoint reasons: before the module's formula function is reached.
    # That is what makes the retained scalar adaptation production-unreachable rather than merely
    # deprecated -- it cannot be entered at all, so it cannot become a fallback when the canonical
    # inputs are absent, and it cannot supply a project status. `models_sim.run_monte_carlo` and
    # `monte_carlo_eac` are untouched and remain reconstructable as scientific history.
    if new_id in DISABLED_CANONICAL_INPUT_NOT_GOVERNED:
        return {
            # THE MODULE'S IDENTITY SURVIVES ITS DISABLEMENT, and it is read from the dispatch
            # table rather than restated here, so the identity cannot drift from the function the
            # registry points at. A1.1 is still Monte Carlo EAC Forecast; it is not executing.
            "method_class": VALIDATED[new_id][0] if new_id in VALIDATED else None,
            "status_color": None,
            "band_asserted": False,
            "insufficient_data": True,
            "activation_state": "DISABLED_INSUFFICIENT_INPUT",
            "abstention_reason_code": CANONICAL_INPUT_NOT_GOVERNED_CODE,
            "canonical_disposition": "CANONICAL_INPUT_CONTRACT_NOT_SATISFIED",
            "retained_adaptation": "preserved in app.simulation.models_sim.run_monte_carlo as "
                                   "historical research implementation; not reached from here",
            "evidence_metric": CANONICAL_INPUT_NOT_GOVERNED_REASON,
        }
    if new_id not in VALIDATED:
        raise MissingModuleError(
            f"{new_id} ({index[new_id]['module_name']}) has not been ported and validated "
            f"against the JavaScript implementation; this server refuses to compute it"
        )
    _, fn = VALIDATED[new_id]
    return fn(si, rand, period_cutoff)


def run_all(si: dict, scenario_id: str, period: str, period_cutoff,
            only: list[str] | None = None) -> dict[str, Any]:
    """
    Run every module this server can compute, on one project's signalInputs.

    The generator is seeded once from (scenario_id, period) and shared, so the sequence a
    stochastic model draws depends only on the scenario and period, never on the participant or on
    how many modules ran before it.

    period_cutoff is required, not optional. A module needing a reference date receives it; no
    module reads the system clock. Making it optional would let a caller omit it and let a
    future module quietly fall back to the wall clock.
    """
    seed = seed_from(scenario_id, period)
    rand = make_rng(seed)
    # The sim.js pair derive their own streams from the seed rather than sharing this generator,
    # so they need the seed value itself. Published here so every module keeps one call signature.
    from .models import SEED_HOLDER
    SEED_HOLDER["seed"] = seed

    index = registry_index()
    ids = only if only is not None else available_modules()

    results = []
    abstained = []

    def record(new_id: str, out: dict, adapted: str | None = None) -> None:
        """
        One module's outcome, stored the same way whichever pass produced it.

        `adapted` is the assembly note for one of the fourteen nested-input modules: what the
        adapter could supply it and what it could not. It is appended to the abstention reason
        so a module of the fourteen that still abstains says WHY, rather than being silent and
        indistinguishable from the wiring failure this adapter fixed.
        """
        # RUN 28. A calibration-pending row is a COMPUTED row with no band asserted, not an
        # abstention: the canonical method ran and produced a figure, and only the colour is
        # withheld because no boundary for the quantity has been established from evidence. It
        # is routed to `computed` so the figure reaches the ledger, the interface and the
        # export, and it cannot reach status fusion because fusion reads only the two voting
        # modules. Without this arm the old `status_color is None` test would file every
        # canonical Category 1 to 3 result as though the module had nothing to say, which is
        # the opposite of what happened. `insufficient_data` still wins: a module that abstains
        # AND sets this flag is an abstention, so the flag cannot be used to smuggle a row past
        # a genuine refusal.
        _pending = bool(out.get("calibration_pending")) and not out.get("insufficient_data")
        if not _pending and (out.get("insufficient_data") or out.get("status_color") is None):
            # Retain the module's own abstention message (evidence_metric), when it gave one, so
            # the ledger can say why a module is silent instead of showing only its bare id. A
            # module that produced no message is recorded with reason=None; nothing is invented.
            reason = out.get("evidence_metric")
            # A module disabled as concept-only already states why it is silent, and the
            # adapter is not part of that answer: it is refused before its input is consulted.
            if new_id in DISABLED_MODULES:
                adapted = None
            if adapted is not None:
                reason = f"{reason} {adapted}" if reason else adapted
            entry = {
                "module_id": new_id,
                "reason": reason,
                "activation_state": out.get("activation_state") or activation_state(new_id),
            }
            # RUN 20 CYCLE 10. The truthful method label travels with an abstaining or disabled
            # module too. Four of the entries below are disabled modules whose registered name
            # claims a method that is not implemented at all, and a disabled module is exactly
            # where a stale prestigious claim survives unexamined.
            _attach_method_label(entry, new_id)
            # RUN 7. The stable machine code for WHY, beside the sentence that says why in
            # words. The sentence is what the ledger renders and it carries no code, no key name
            # and no module id; the code is what the API, the export and the analysis group on,
            # and it never reaches a participant surface. Present only on modules corrected by
            # Run 7 and any module that adopts the shared layer later, so a row computed before
            # Run 7 and one computed after are distinguishable rather than both carrying an
            # empty field.
            if out.get("abstention_reason_code"):
                entry["abstention_reason_code"] = out["abstention_reason_code"]
            if new_id in NESTED_INPUT_MODULES:
                entry["newly_wired_unvalidated"] = True
                entry["wiring_note"] = WIRING_NOTE
                entry["signal_qualification"] = SIGNAL_QUALIFICATION
            # RUN 30 CLOSURE. AN ABSTENTION IS A LEDGER ROW AND MUST SAY WHICH LINE PRODUCED IT.
            # Run 30's first pass built a canonical layer production never called, and the only
            # surface on which that was visible was the ledger. A row that merely goes quiet is
            # indistinguishable from a proxy that happened to have nothing to say, so the
            # canonical source, the structure it was waiting for, the provenance of whatever was
            # supplied, the disposition and the lineage travel onto the abstaining row too.
            # These are new keys only: the participant ledger's status accessors read module_id,
            # status_color and evidence_metric, none of which is touched.
            for _k in ("result_source", "canonical_disposition", "canonical_structure",
                       "structure_provenance", "abstention_reason", "lineage",
                       "canonical_state", "operational"):
                if out.get(_k) is not None:
                    entry[_k] = out[_k]
            abstained.append(entry)
            return
        out = dict(out)
        out["module_id"] = new_id
        out["group"] = index[new_id]["group"]
        out["category"] = index[new_id]["category"]
        if new_id in STOCHASTIC:
            out["seed"] = seed
        # Run 1 remediation: activation state and, for the thirty relabeled proxies, the
        # canonical-name-plus-qualifier label. New keys on the result dict only -- module_id,
        # status_color and evidence_metric (what the participant ledger renders) are untouched.
        # This is what makes the qualifier reach the API response without reaching the ledger:
        # taxonomy.js's getModuleStatus/getModuleResult never read these two keys.
        out["activation_state"] = activation_state(new_id)
        # RUN 20 CYCLE 10. See method_labels.py. Where the registered name claims a method the
        # code does not perform, the result carries the truthful name of the computation, the
        # canonical structure that is absent, and the disposition. New keys only: the
        # participant ledger's status accessors read module_id, status_color and
        # evidence_metric, none of which is touched, and the served participant package is
        # frozen and is not renamed by this run.
        _attach_method_label(out, new_id)
        label = proxy_label(new_id, index[new_id]["module_name"])
        if label is not None:
            out["proxy_qualifier"] = PROXY_QUALIFIERS[new_id]
            out["proxy_label"] = label
        out["votes"] = new_id in CORE_VOTING_MODULES
        # Remediation Run 4 (validate the seven). A voting module carries the citation for its
        # own band boundaries and the sentence stating what that citation does not establish;
        # one held non-voting for want of a source carries the reason. New keys on the result
        # dict only, read by the export and the API, never by the participant ledger's status
        # accessors -- the same mechanism Run 1 and Run 3 used.
        if new_id in BAND_SOURCES:
            out["band_source"] = BAND_SOURCES[new_id]
            out["band_source_limit"] = BAND_SOURCE_LIMIT
        elif new_id in HELD_NON_VOTING_UNSOURCED_BANDS:
            out["band_source"] = None
            out["held_non_voting_reason"] = HELD_NON_VOTING_UNSOURCED_BANDS[new_id]
        # Remediation Run 3 (the adapter). The fourteen nested-input modules are reachable,
        # shown, and explicitly marked as newly wired and unvalidated -- in the API response,
        # the export and the methods documentation, never on the participant surface, exactly
        # like Run 1's proxy qualifier and by the same mechanism (new keys the frontend's
        # status accessors do not read). `signal_qualification` records the Category 9
        # deviation on the data itself: these fourteen consume raw, unqualified signals.
        if new_id in NESTED_INPUT_MODULES:
            out["newly_wired_unvalidated"] = True
            out["wiring_note"] = WIRING_NOTE
            out["signal_qualification"] = SIGNAL_QUALIFICATION
            out["category_9_deviation"] = CATEGORY_9_DEVIATION
        results.append(out)

    # ------------------------------------------------------------------ pass 1: flat inputs
    # Every module whose input contract is the flat signalInputs dictionary, in exactly the
    # order, and against exactly the shared generator, it always ran in. The fourteen
    # nested-input modules never draw from `rand` (verified: no rand() call in models_gov.py,
    # models_evc.py or models_decision.py), so deferring them to the passes below cannot move
    # any other module's position in the random stream. That is what makes the other modules'
    # results provably byte-identical to a run without this adapter.
    flat_ids = [i for i in ids if i not in NESTED_INPUT_MODULES]
    for new_id in flat_ids:
        record(new_id, run_module(new_id, si, rand, period_cutoff))

    # ------------------------------------------------- passes 2 to 4: the assembled package
    # ONE adapter, three tiers, because each tier's input is the tier before it: the signal
    # package, then the decision snapshot B1.1 produces, then the array of everything computed
    # so far. This is the browser's own assembly order (signals.js), and it is the only place
    # in the server where the nested package exists.
    nested_ids = [i for i in ids if i in NESTED_INPUT_MODULES]
    if nested_ids:
        signals, absence = build_signals(si, results)
        note = supplied_and_absent(signals, absence)
        decision = None
        for tier in ADAPTER_TIERS:
            tier_ids = [i for i in tier if i in nested_ids]
            if not tier_ids:
                continue
            adapted_si = adapt(si, signals, decision=decision,
                               signal_array=[array_entry(r) for r in results])
            for new_id in tier_ids:
                record(new_id, run_module(new_id, adapted_si, rand, period_cutoff), adapted=note)
            if decision is None:
                decision = decision_snapshot(
                    next((r for r in results if r.get("module_id") == "B1.1"), None))

    # Stable order, independent of which pass produced a row: string-sorted by module id, which
    # is the order `available_modules()` already yielded, so every row a run without the adapter
    # produced keeps its position.
    results.sort(key=lambda r: r["module_id"])
    abstained.sort(key=lambda r: r["module_id"])

    return {
        "simulation_version": SIMULATION_VERSION,
        "seed": seed,
        "scenario_id": scenario_id,
        "period": period,
        "period_cutoff": str(period_cutoff),
        "computed": results,
        "abstained": abstained,
        "unported": unported_modules(),
    }
