"""
The truthful method label layer.

WHY THIS FILE EXISTS. Run 19 found twenty-three registered modules whose NAME claims an
analytical method the code does not perform, and eight more whose name or reported claim rests
on a canonical data structure that is not present anywhere in this repository. A name is a
scientific claim. "Discrete Event Simulation" asserts an event schedule, entities, resources and
a clock; "Schedule Risk Analysis P80" asserts a schedule network sampled to a distribution;
"Rough Sets" asserts an information table of objects and attributes. None of those structures is
in the corpus, and Run 20 is forbidden to invent any of them.

THE TWO PERMITTED RESOLUTIONS, and only two: implement the canonical method, or say plainly what
the computation is. Where the defining structure genuinely exists on the signal inputs, the
canonical route is taken and the module lives in canonical.py, which already gates six modules
and abstains when their structure is absent. Where it does not exist, and cannot be supplied
without fabricating project evidence, this file supplies the truthful name.

WHAT THIS FILE DOES NOT DO.

* It changes no arithmetic. Not one band, boundary, weight or constant is touched from here.
* It does not rename the participant instrument. The served participant surface is FROZEN and
  checksummed (code_audit/run12_participant_package_checksums.sha256, package version
  og-participant-2026.08-v1), the study is mid-sequence, and renaming what a participant reads
  would change the treatment. That is outside this run's authority. Every entry below therefore
  carries PARTICIPANT_SURFACE_OWNER_DECISION and the register records it as an owner decision:
  the truthful name reaches the API response, the export and the methods documentation, by
  exactly the mechanism Run 1 used for the thirty proxy qualifiers, and reaches no participant
  screen.
* It does not make anything voting, and it does not activate anything. Four entries below are
  modules that are disabled, and they stay disabled: a truthful name is not a rehabilitation.
* It asserts no empirical validity. A correctly named proxy is still a proxy.

THE FIELDS. `registered` is the name the registry carries and is checked against
p0-baseline/module_renumbering_map.csv, so a registry edit that renames a module cannot leave a
stale claim standing here. `truthful` is what the computation is. `performs` is the one sentence
a reader gets. `absent` names the structure that is NOT present, in plain words, so the gap is a
record rather than an omission. `disposition` is the final scientific state.
"""

from __future__ import annotations

#: The dispositions this file may carry. A truthful label does not upgrade anything.
LABEL_DISPOSITIONS: frozenset[str] = frozenset({
    "CORRECT_PROXY_ONLY",
    "CORRECT_ABSTENTION",
    "FUTURE_RESEARCH_ONLY",
    "OWNER_DECISION_REQUIRED",
    "REGULATORY_VERSION_BLOCKED",
    "EMPIRICAL_VALIDATION_BLOCKED",
})

#: The one sentence about the participant surface, carried once so it cannot drift.
PARTICIPANT_SURFACE_OWNER_DECISION: str = (
    "The served participant surface is frozen and checksummed and the study is mid-sequence, so "
    "the name a participant reads is not changed by this run. Renaming it is an owner decision "
    "about the instrument, not a remediation. The truthful name is published on the interface "
    "response, the export and the methods documentation only."
)


class MethodLabel:
    """One module's registered claim, what it actually computes, and what is absent."""

    __slots__ = ("registered", "truthful", "performs", "absent", "disposition")

    def __init__(self, registered: str, truthful: str, performs: str, absent: str,
                 disposition: str) -> None:
        if disposition not in LABEL_DISPOSITIONS:
            raise ValueError(f"unknown label disposition: {disposition}")
        if truthful.strip().lower() == registered.strip().lower():
            raise ValueError(
                f"the truthful name for {registered} repeats the registered name, which would "
                f"leave the claim exactly where Run 19 found it")
        self.registered = registered
        self.truthful = truthful
        self.performs = performs
        self.absent = absent
        self.disposition = disposition

    def as_dict(self) -> dict[str, str]:
        return {
            "registered_name": self.registered,
            "truthful_method_name": self.truthful,
            "performs": self.performs,
            "absent_canonical_structure": self.absent,
            "label_disposition": self.disposition,
            "participant_surface": PARTICIPANT_SURFACE_OWNER_DECISION,
        }


# ---------------------------------------------------------------------------------------------
# THE TWENTY-THREE METHOD LABEL MISMATCHES, resolved by truthful naming because in every one of
# them the canonical structure is absent from the corpus and inventing it is prohibited.
# ---------------------------------------------------------------------------------------------

# RUN 28. NINE ENTRIES ARE GONE FROM THIS DICTIONARY, and they are gone for the reason this file
# says a label may go: the canonical method was implemented. A1.5, A1.6, A1.10, A1.11, A2.7,
# A2.10, A2.11, A3.6 and A3.9 now carry out the method their registered name claims, from a
# governed structure that arrives on the signal inputs, and they ABSTAIN when that structure is
# absent. Each of the nine entries said, truthfully at the time, that the code did something
# weaker than its name; leaving them would now be a false claim in the opposite direction. Two of
# the nine were renamed in the same run on the owner's authority -- A1.10 to CPI Shrinkage
# Forecast and A1.11 to Independent EAC Reconciliation Index -- and the registry map carries the
# new names. A3.8's entry STAYS: that module remains disabled and non-voting, its canonical
# structure exists only as a laboratory implementation, and a truthful label on a disabled module
# is exactly where a stale claim would otherwise survive.
TRUTHFUL_METHOD_LABELS: dict[str, MethodLabel] = {

    # ---------------------------------------------------------------- category 1, cost and EVM

    # ---------------------------------------------------------------------- category 2, schedule

    # -------------------------------------------------------------------------- category 3, cost
    "A3.8": MethodLabel(
        registered="Parametric Cost Index",
        truthful="Disabled: no parametric estimating relationship is implemented",
        performs="nothing. The module is disabled and its formula function is never called",
        absent="measurable cost drivers, an estimating relationship fitted to them and "
               "calibrated coefficients with their standard errors. A parametric estimate is the "
               "relationship; without it there is no method to name",
        disposition="FUTURE_RESEARCH_ONLY",
    ),

    # ------------------------------------------- categories 4 and 5, change, claims, simulation
    # RUN 29 REMOVED SIX ENTRIES FROM HERE: A4.6 Change Order Frequency, A4.7 Dispute Escalation
    # Index, A4.10 Specification Conflict Density, A5.3 Tornado Risk Ranking, A5.5 Rework
    # Feedback Loop and A5.8 Discrete Event Simulation.
    #
    # A truthful method label is a statement about what the code DOES. Each of those six now does
    # what its registered name says, from a governed structure supplied by the owner's Run-29
    # contract, and abstains when that structure is absent. Leaving the labels would be the same
    # untruth this table exists to prevent, told in the other direction: a reader would be shown
    # "Throughput index from the schedule index and progress ratio" beside a module that runs an
    # event list with a clock, a resource and a queue, and "Ranked present-state deviations"
    # beside a module that ranks the swings a sensitivity analysis computed.
    #
    # The register `test_run20_cycle10_truthful_labels.py` maintains is what forces this file to
    # be corrected rather than left: it asserts that every labelled module still lacks the
    # structure the label says is absent, so a label whose structure has arrived turns it red.

    # ------------------------------------------------------------------- category 6, ensembles
    "B1.2": MethodLabel(
        registered="Weighted Voting",
        truthful="Fixed-weight signal band tally",
        performs="tallies the bands of the assembled signals under four fixed weights and "
                 "reports the heaviest band and its share",
        absent="provenance for the four weights, which are design constants with no source, and "
               "the qualified-evidence boundary: the tally reads assembled primary signals "
               "directly rather than already qualified signal states",
        disposition="CORRECT_PROXY_ONLY",
    ),

    # ---------------------------------------------------------------- category 7, soft computing
    "B2.2": MethodLabel(
        registered="Rough Sets",
        truthful="Supermajority band classification over bodies of evidence",
        performs="assigns each body of evidence a band, and calls a band definite when it holds "
                 "more than three quarters of the bodies, borderline otherwise",
        absent="an information table: real objects described by real attributes, from which "
               "indiscernibility classes and then the lower and upper approximations are "
               "derived. There are no objects here, only this project's own signals",
        disposition="CORRECT_PROXY_ONLY",
    ),
    "B2.14": MethodLabel(
        registered="Maximum Entropy",
        truthful="Entropy of a designed band lookup",
        performs="reads a fixed four-way probability vector from the worse of the two "
                 "performance indices, adjusts two of its entries by the document risk score, "
                 "renormalises and reports the normalised Shannon entropy",
        absent="moment constraints and a maximisation subject to them. Nothing is maximised: "
               "the distribution is looked up, so the entropy measures the lookup table",
        disposition="CORRECT_PROXY_ONLY",
    ),
    "B2.18": MethodLabel(
        registered="MARCOS Ranking",
        truthful="Single-project criterion scoring against designed reference points",
        performs="scores this one project against designed ideal and anti-ideal reference points",
        absent="a real set of alternatives to rank. A ranking method over one alternative "
               "returns that alternative, and the reference points are designed rather than "
               "derived from the alternative set as the method requires",
        disposition="OWNER_DECISION_REQUIRED",
    ),

    # ------------------------------------------------------------------- category 8, governance
    "B3.1": MethodLabel(
        registered="ABM Governance Layer",
        truthful="Action boundary and authority matrix",
        performs="maps the decision layer state to the action to take and the authority that "
                 "may take it",
        absent="agents with decision rules, an interaction structure and time steps. The mapping "
               "itself is sound and is not changed; what is absent is everything that would make "
               "it agent based",
        disposition="CORRECT_PROXY_ONLY",
    ),
    "A6.4": MethodLabel(
        registered="Contractor Performance Score",
        truthful="Project-document contractor estimate",
        performs="scores contractor performance from figures carried on this project's own "
                 "documents",
        absent="official past performance information: a source system identifier, the "
               "assessment period, the record status and its review state. Nothing here is past "
               "performance information and it must not be read as such",
        disposition="CORRECT_PROXY_ONLY",
    ),

    # ------------------------------------------------------------------ category 9, data quality
    "C1.6": MethodLabel(
        registered="Cross-document Consistency Score",
        truthful="Reported index self-consistency check",
        performs="recomputes the two performance indices and the reported progress from the "
                 "earned value figures in one reported set and counts the disagreements against "
                 "the three checks the method is defined over",
        absent="per-field source records. Every figure compared comes from the same assembled "
               "set, so no fact is compared across two documents and no document is identified "
               "as the source of any disagreement",
        disposition="CORRECT_PROXY_ONLY",
    ),
    "C1.4": MethodLabel(
        registered="Audit Trail Completeness",
        truthful="Declared audit field presence check",
        performs="counts the presence of the declared audit fields",
        absent="assessment of the real signal, judgment and audit objects, event chronology and "
               "linkage between them, and a noncompensatory treatment of the critical fields",
        disposition="OWNER_DECISION_REQUIRED",
    ),

    # ----------------------------------------------------------------- category 10, optimisation
    "B4.1": MethodLabel(
        registered="Multi-Objective Optimization",
        truthful="Disabled: no objectives, decision variables or feasible set are implemented",
        performs="nothing. The module is disabled and its formula function is never called",
        absent="declared objectives, decision variables, constraints and a feasible set. A real "
               "implementation is a new build and not a rename",
        disposition="FUTURE_RESEARCH_ONLY",
    ),
    "B4.2": MethodLabel(
        registered="Linear Programming",
        truthful="Disabled: no decision variables, objective or constraints are implemented",
        performs="nothing. The module is disabled and its formula function is never called",
        absent="decision variables, a linear objective and a constraint system. None exists "
               "anywhere in the corpus",
        disposition="FUTURE_RESEARCH_ONLY",
    ),
    "B4.4": MethodLabel(
        registered="What-If Scenario Matrix",
        truthful="Earned value completion forecast range",
        performs="computes four completion forecasts by perturbing the cost index and reports "
                 "the spread between the widest two as a share of budget",
        absent="candidate actions with identity as the rows and scenarios as the columns. There "
               "is one dimension here, not a matrix, and no action is carried",
        disposition="CORRECT_PROXY_ONLY",
    ),
    "B4.5": MethodLabel(
        registered="Decision Sensitivity Matrix",
        truthful="Disabled: no decisions and no sensitivities are implemented",
        performs="nothing. The module is disabled and its formula function is never called",
        absent="a decision set, declared input ranges and a response evaluated over them",
        disposition="FUTURE_RESEARCH_ONLY",
    ),
    "B4.6": MethodLabel(
        registered="Pareto Frontier Analysis",
        truthful="Disabled: no alternative set and no dominance relation are implemented",
        performs="nothing. The module is disabled and its formula function is never called",
        absent="a set of alternatives evaluated on two or more objectives, over which dominance "
               "can be assessed. A frontier over a single project is not defined",
        disposition="FUTURE_RESEARCH_ONLY",
    ),
}


# ---------------------------------------------------------------------------------------------
# THE STRUCTURAL AND CLAIM GAPS THAT ARE NOT NAMING FAULTS. These modules are named for what
# they do; what is missing is evidence behind the claim, not a different method. They are
# recorded here so the P2 population is complete in one place and so nothing is disposed of by
# being left out.
# ---------------------------------------------------------------------------------------------

#: module id -> (disposition, the sentence stating what is not established)
STRUCTURAL_CLAIM_LIMITS: dict[str, tuple[str, str]] = {
    "A4.1": ("EMPIRICAL_VALIDATION_BLOCKED",
             "No labelled reference corpus of documents exists in this repository, so the "
             "precision and recall of this score are unmeasured and no accuracy claim about it "
             "is supportable on any surface."),
    "A6.3": ("REGULATORY_VERSION_BLOCKED",
             "The permit authority, the jurisdiction and the version of the conditions being "
             "assessed are not carried, and no committed authority in this repository supplies "
             "them. The reading is a count of reported conditions met and is not a compliance "
             "determination under any named instrument."),
}


def method_label(module_id: str) -> MethodLabel | None:
    return TRUTHFUL_METHOD_LABELS.get(module_id)


def claim_limit(module_id: str) -> tuple[str, str] | None:
    return STRUCTURAL_CLAIM_LIMITS.get(module_id)


def labelled_modules() -> list[str]:
    return sorted(TRUTHFUL_METHOD_LABELS)
