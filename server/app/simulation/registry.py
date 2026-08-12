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

#: Every module this server refuses to execute, whatever the reason. This is the set the
#: enforcement points read, so a new disablement reason cannot be added without every gate
#: picking it up. The two component sets stay separate above because they mean different things
#: and because the eight remain, individually, part of the scientific review population.
DISABLED_MODULES: dict[str, str] = {**DISABLED_CONCEPT_ONLY, **DISABLED_EVIDENCE_UNDER_REVIEW}

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
PROXY_QUALIFIERS: dict[str, str] = {
    "A1.2": "hard-coded transformations of two-sided CUSUM on real SPI history; k, H, sigma "
            "floor and Amber band uncalibrated",
    "A1.3": "Normal-normal updating with designed constant variances, not a governed Bayesian "
            "model",
    "A1.4": "Scalar Kalman recursion with fixed Q and R, short history, no calibrated filtering "
            "claim",
    "A1.9": "an expenditure-versus-progress control ratio, not a standardised statistical test",
    "A1.10": "fixed 50 per cent shrinkage toward historical mean; coefficient not estimated",
    "A2.4": "a custom compression ratio; no network-based crashing model or calibrated bands",
    "A2.6": "a single planned versus actual snapshot, not a longitudinal S-curve analysis",
    "A2.7": "a simplified shift summary on real milestone history, bands uncalibrated",
    "A3.3": "a labour-hours ratio, not an earned-output productivity model",
    "A3.5": "a transparent ratio; validity depends on whether the indirect plan is total or "
            "period-to-date",
    "A3.7": "an analogous-cost ratio; project selection, normalisation and adaptation "
            "ungoverned",
    "A3.9": "a material-escalation ratio with no external price index, time base or geography",
    # REVISED BY THE FIFTEEN-DEFECTS RUN, and revised deliberately rather than left standing.
    # The previous run's label named "fallback behaviour" as part of what this computation does.
    # Defect 12 removed the fallbacks, so the label had stopped describing the module: it now
    # requires verified lost days and a positive float figure and refuses without either, and a
    # label that still advertised a fabrication would be inaccurate in the opposite direction
    # from the one the labelling exercise was correcting. What remains uncalibrated is the band
    # ladder, and that is what the qualifier now says.
    "A4.5": "a lost-days over available-float ratio with ungoverned bands, computed only from "
            "verified lost days and a reported float figure",
    "A4.6": "contract growth plus a raw count; no time or exposure denominator",
    "A4.7": "an ad hoc 0.3 / 0.3 / 0.4 weighted sum; weights and dependence uncalibrated",
    "A4.8": "a precomputed compliance score; provenance and construction unvalidated",
    "A5.2": "local CPI perturbation plus deviations, not calibrated multivariate sensitivity",
    "A5.3": "a ranking of four present-state deviations; no outcome-response ranges estimated",
    "B2.10": "hard-coded transformations of raw CPI, SPI and document risk",
    "B2.11": "hard-coded memberships consuming raw metrics; no calibration evidenced",
    "B2.12": "designed perturbations, not elicited or observed hesitant assessments",
    "B2.13": "membership intervals that are designed constants",
    "B2.14": "entropy over designed state probabilities; measures the lookup, not the project",
    "B2.15": "fixed mappings from raw metrics; no governed possibility distribution",
    "B2.16": "algebraically bounded but fixed memberships on raw unqualified inputs",
    "B2.17": "formula-shaped with designed memberships, no empirical or elicitation basis",
    "B3.5": "a raw modification count; not a frequency without a denominator",
    "B4.3": "an explainable four-rule checklist, not a constraint-satisfaction solver",
    "B4.4": "four deterministic EAC variants; not an action-by-scenario matrix or optimiser",
    "D1.2": "an empirical CPI and SPI percentile rank; small-n behaviour and bands unvalidated",
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
    if new_id in CORE_VOTING_MODULES:
        return "ENABLED_QUALIFIED"
    return "ADVISORY_ONLY"


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
    """New ids this server can compute today."""
    return sorted(VALIDATED)


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
        if out.get("insufficient_data") or out.get("status_color") is None:
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
