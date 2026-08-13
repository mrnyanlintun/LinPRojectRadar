"""
THE FRAMEWORK-LEVEL EVIDENCE LINEAGE MODEL.

WHY THIS FILE EXISTS AND WHY IT IS NOT PART OF THE COMBINATION RULE. Run 20 cycle 3 step one
measured, and pinned numerically, that one body of evidence counted twice sharpened belief from
0.7000 to 0.9273, and that the two modules which actually vote on project status are two
transforms of one body of earned-value evidence. The obvious repair is to patch the combination
rule so it notices the duplicate. That repair is refused here, because the combination rule is
not the only consumer that needs to know whether two signals are independent: a synthesis, a
governance projection, a decision card and an evidence qualification all have the same question
and would each have grown their own answer to it. So the lineage vocabulary lives HERE, in one
file that knows nothing about Dempster's rule, and every consumer reads the same partition.

WHAT A LINEAGE RECORD CARRIES. The supervisory clarification names the fields, and each is kept
for a reason that is not decorative:

  module_id             which analytical module emitted the signal
  source_fact_ids       the governed facts the signal ultimately rests on, NOT the immediate
                        arguments. A signal that reads a cost performance index rests on earned
                        value and actual cost, and it says so, because the index is not a fact.
  source_document_ids   the artefacts those facts were read from, where an identity exists
  dependency_ids        the other SIGNALS this one consumes
  lineage_group_ids     declared evidence bodies, for dependence a fact list cannot express
  evidence_relationship one of the nine classes below
  derivation_chain      the ordered transformations from the facts to the emitted value. For a
                        derived signal this is the whole point: recording only the final module
                        id loses exactly the information that proves two signals are one.

THE PARTITION RULE, WHICH IS THE ONLY THING A CONSUMER ACTUALLY NEEDS. Two signals belong to one
body of evidence when any of the following holds, and the relation is then closed transitively:

  1. they share a declared lineage group id;
  2. one names the other in its dependency ids or its derivation chain;
  3. their source fact ids intersect.

Rule 3 is structural and is deliberately NOT conditional on what the signals declare themselves
to be. A signal that claims INDEPENDENT while resting on the same governed facts as its
neighbour is not independent, and a claim is not evidence. Rules 1 and 2 exist because
dependence can be real without any shared fact id being recorded: a synthesis of two signals
shares no raw fact with either, and must still never corroborate them.

WHAT THIS FILE DOES NOT DO. It assigns no weights, estimates no correlation coefficient and
carries no calibrated constant. There is nothing here to calibrate: the partition is a set
operation on declared identifiers, and the treatment of a partition is the consumer's decision,
stated in the consumer.
"""

from __future__ import annotations

from typing import Any, Iterable

# ----------------------------------------------------------------- the nine evidence relationships
#
# Each is a statement about the signal's relation to the evidence body it belongs to, not about
# its quality. A DERIVED signal is not worse than an INDEPENDENT one; it simply may not
# corroborate the thing it was derived from.

#: Rests on its own body of evidence. The only class that may corroborate another signal.
INDEPENDENT = "INDEPENDENT"
#: Reads the same governed facts as another signal, without transforming them.
SAME_SOURCE = "SAME_SOURCE"
#: Computed from another SIGNAL rather than from facts.
DERIVED = "DERIVED"
#: A deterministic transformation of the same governed facts another signal reads. The two
#: voting modules are this, which is why the class is named rather than folded into SAME_SOURCE.
SAME_SOURCE_TRANSFORM = "SAME_SOURCE_TRANSFORM"
#: Shares part of its evidence body with another signal without being a transform of it.
CORRELATED = "CORRELATED"
#: Produced by combining other signals. Never independent of any of its constituents.
SYNTHESIZED = "SYNTHESIZED"
#: A statement about the EVIDENCE, not about the project. Category 9 lives here.
QUALITY_METADATA = "QUALITY_METADATA"
#: A governance projection over signals that have already been counted.
GOVERNANCE_OUTPUT = "GOVERNANCE_OUTPUT"
#: A recommendation or decision-support output.
DECISION_OUTPUT = "DECISION_OUTPUT"

EVIDENCE_RELATIONSHIPS: tuple[str, ...] = (
    INDEPENDENT, SAME_SOURCE, DERIVED, SAME_SOURCE_TRANSFORM, CORRELATED,
    SYNTHESIZED, QUALITY_METADATA, GOVERNANCE_OUTPUT, DECISION_OUTPUT,
)

#: THE ANTI-FEEDBACK SET. These three are not project-condition evidence at all, whatever module
#: id they carry. A data-quality result says the evidence is thin, which is not the same claim as
#: the project being in trouble; a governance projection and a decision output are computed FROM
#: signals that have already been counted, so admitting them counts that evidence a second time
#: through a longer path. Specification 18 states the rule for Category 9 directly: its output is
#: qualification metadata and not another independent risk vote. A consumer of project condition
#: must drop these rather than group them, because grouping would still let them vote inside
#: whichever body they landed in.
NON_PROJECT_EVIDENCE: frozenset[str] = frozenset({
    QUALITY_METADATA, GOVERNANCE_OUTPUT, DECISION_OUTPUT,
})

#: The classes that assert dependence outright. Membership here is sufficient to refuse
#: corroboration; it is not necessary, because rule 3 of the partition can find dependence a
#: declaration has failed to mention.
DEPENDENT_RELATIONSHIPS: frozenset[str] = frozenset({
    SAME_SOURCE, DERIVED, SAME_SOURCE_TRANSFORM, CORRELATED, SYNTHESIZED,
})


class LineageError(ValueError):
    """An evidence relationship outside the vocabulary, which is never a silent default."""


def lineage_record(module_id: str,
                   source_fact_ids: Iterable[str] = (),
                   source_document_ids: Iterable[str] = (),
                   dependency_ids: Iterable[str] = (),
                   lineage_group_ids: Iterable[str] = (),
                   evidence_relationship: str = INDEPENDENT,
                   derivation_chain: Iterable[str] = ()) -> dict[str, Any]:
    """
    Build one lineage record. Plain dicts rather than a class, because these are serialised into
    the stored compute result and read back by code that has no import of this module.

    An unrecognised relationship RAISES. There is no default: a signal whose relationship nobody
    declared would otherwise become INDEPENDENT by accident, which is the exact failure this
    file exists to prevent.
    """
    if evidence_relationship not in EVIDENCE_RELATIONSHIPS:
        raise LineageError(
            f"{module_id}: {evidence_relationship!r} is not one of the declared evidence "
            f"relationships {EVIDENCE_RELATIONSHIPS}")
    return {
        "module_id": module_id,
        "source_fact_ids": tuple(sorted(set(source_fact_ids))),
        "source_document_ids": tuple(sorted(set(source_document_ids))),
        "dependency_ids": tuple(sorted(set(dependency_ids))),
        "lineage_group_ids": tuple(sorted(set(lineage_group_ids))),
        "evidence_relationship": evidence_relationship,
        "derivation_chain": tuple(derivation_chain),
    }


def _linked(a: dict, b: dict) -> bool:
    """
    Are these two signals directly in one body of evidence? The three rules of the partition,
    each written once. Transitivity is applied by `partition`, not here.
    """
    if set(a["lineage_group_ids"]) & set(b["lineage_group_ids"]):
        return True
    if b["module_id"] in a["dependency_ids"] or a["module_id"] in b["dependency_ids"]:
        return True
    if b["module_id"] in a["derivation_chain"] or a["module_id"] in b["derivation_chain"]:
        return True
    if set(a["source_fact_ids"]) & set(b["source_fact_ids"]):
        return True
    return False


def partition(records: list[dict]) -> list[list[int]]:
    """
    Partition signal indices into bodies of evidence: the connected components of `_linked`.

    Returned as index lists, in first-appearance order, so a caller can keep whatever it has
    alongside the records without this function needing to know what that is.
    """
    n = len(records)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(n):
        for j in range(i + 1, n):
            if _linked(records[i], records[j]):
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[ri] = rj

    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return [g for _, g in sorted(groups.items(), key=lambda kv: min(kv[1]))]


def group_labels(records: list[dict], groups: list[list[int]]) -> list[str]:
    """A stable, readable name for each body of evidence, for the audit trail and the tests."""
    out = []
    for g in groups:
        declared = sorted({gid for i in g for gid in records[i]["lineage_group_ids"]})
        if declared:
            out.append("+".join(declared))
        else:
            facts = sorted({f for i in g for f in records[i]["source_fact_ids"]})
            out.append("facts:" + ",".join(facts) if facts
                       else "signals:" + ",".join(sorted(records[i]["module_id"] for i in g)))
    return out


# ------------------------------------------------------------------- the declared module lineages
#
# WHY THE DERIVATION CHAIN IS SPELLED OUT RATHER THAN SUMMARISED. The supervisory clarification
# asks that a derived signal retain the chain and not only the final module id. The chain below
# is what makes the dependence CHECKABLE by a reader: anyone can see that the variance at
# completion reaches the earned value through the cost performance index, and that the
# to-complete index reaches it directly, without having to trust the relationship label.
#
# The fact vocabulary is the governed input names the modules themselves declare: bac, ev, ac,
# pv and the reporting history. A ratio is never a fact here; it is a step in a chain.

EARNED_VALUE_BODY = "EARNED_VALUE_MEASUREMENT"
DOCUMENT_BODY = "DOCUMENT_EVIDENCE"
REPORTING_HISTORY_BODY = "REPORTING_HISTORY"
#: The change order log and the two contract sums read from it. Run 20 cycle 4. It is its own
#: body and shares nothing with the earned-value measurement, which is why the two advisory
#: duplicate pairs must NOT collapse into one body between them.
CONTRACT_CHANGE_BODY = "CONTRACT_CHANGE_RECORD"
#: The indirect cost ledger. Run 20 cycle 5. Its own body, sharing nothing with the earned-value
#: measurement, which is exactly what the entry corrected in that cycle had denied.
INDIRECT_COST_BODY = "INDIRECT_COST_LEDGER"

MODULE_LINEAGE: dict[str, dict[str, Any]] = {
    # ---- the two voting modules, which are the reason this file exists
    "A1.7": lineage_record(
        "A1.7", source_fact_ids=("ac", "bac", "ev"),
        lineage_group_ids=(EARNED_VALUE_BODY,),
        evidence_relationship=SAME_SOURCE_TRANSFORM,
        derivation_chain=("bac,ev,ac", "work remaining = bac - ev",
                          "funds remaining = bac - ac",
                          "to-complete performance index = (bac - ev) / (bac - ac)")),
    "A1.8": lineage_record(
        "A1.8", source_fact_ids=("ac", "bac", "ev"),
        lineage_group_ids=(EARNED_VALUE_BODY,),
        evidence_relationship=SAME_SOURCE_TRANSFORM,
        derivation_chain=("bac,ev,ac", "cost performance index = ev / ac",
                          "estimate at completion = bac / cost performance index",
                          "variance at completion = bac - estimate at completion")),
    # ---- the other lineages the supervisory clarification names by example
    # RUN 20 CYCLE 5. This entry declared A1.1 to be the cost performance index. A1.1 IS MONTE
    # CARLO EAC: it forecasts the estimate at completion by sampling, scaled by both indices and
    # spread by the document risk score, and it refuses a budget of zero and either index at or
    # below zero. It is CORRELATED and not a same-source transform, because the sampling is not a
    # deterministic transformation of the facts and because its body is not identical to the
    # voters' -- it reaches the document evidence as well.
    "A1.1": lineage_record(  # Monte Carlo estimate at completion
        "A1.1", source_fact_ids=("ac", "bac", "doc_risk_score", "ev", "pv"),
        lineage_group_ids=(EARNED_VALUE_BODY, DOCUMENT_BODY),
        evidence_relationship=CORRELATED,
        derivation_chain=("bac,ev,ac,pv and the document risk score",
                          "cost performance index = ev / ac",
                          "schedule performance index = ev / pv",
                          "estimate at completion scaled by the two indices",
                          "stochastic sampling of the estimate at completion, spread by the "
                          "document risk score",
                          "eightieth-percentile overrun against the budget")),
    "A1.2": lineage_record(  # two-sided CUSUM over reporting history
        "A1.2", source_fact_ids=("ev", "pv", "reporting_history"),
        lineage_group_ids=(EARNED_VALUE_BODY, REPORTING_HISTORY_BODY),
        evidence_relationship=CORRELATED,
        derivation_chain=("reporting history of ev and pv",
                          "schedule performance index per period",
                          "two-sided cumulative sum of the index deviations")),
    "A1.3": lineage_record(
        "A1.3", source_fact_ids=("ev", "pv", "reporting_history"),
        lineage_group_ids=(EARNED_VALUE_BODY, REPORTING_HISTORY_BODY),
        evidence_relationship=CORRELATED,
        derivation_chain=("reporting history", "normal-normal updating")),
    "A1.4": lineage_record(  # scalar Kalman recursion
        "A1.4", source_fact_ids=("ev", "pv", "reporting_history"),
        lineage_group_ids=(EARNED_VALUE_BODY, REPORTING_HISTORY_BODY),
        evidence_relationship=CORRELATED,
        derivation_chain=("reporting history", "scalar Kalman recursion")),
    "A1.5": lineage_record(  # ARIMA-style extrapolation of the reporting history
        "A1.5", source_fact_ids=("ev", "pv", "reporting_history"),
        lineage_group_ids=(EARNED_VALUE_BODY, REPORTING_HISTORY_BODY),
        evidence_relationship=CORRELATED,
        derivation_chain=("reporting history", "autoregressive extrapolation")),
    # RUN 20 CYCLE 5. THE A2.1 ENTRY IS REMOVED AND NOT CORRECTED. It declared A2.1 to be earned
    # schedule over the earned-value body. A2.1 IS PERT NETWORK CRITICALITY, and it abstains with
    # the reason code canonical_structure_absent on every project this platform holds, because
    # the corpus carries no activity network with logic and three-point durations. A lineage
    # record is a statement about a SIGNAL'S evidence. A module that emits no signal on any
    # project has no signal whose evidence there is anything to declare, and declaring one
    # asserts the existence of evidence that was never produced. If the corpus ever carries an
    # activity network, the record is written then, against the reading the module then makes.
    # RUN 20 CYCLE 5, AND THIS IS THE ONE THAT DID HARM. This entry declared A3.5 to be a
    # tornado sensitivity sweep resting on the earned-value body. A3.5 IS OVERHEAD ABSORPTION
    # RATE: actual indirect cost over an indirect plan scaled by progress. It shares NO fact with
    # the earned-value measurement, so an INDEPENDENT second body of evidence had been declared
    # inside the first and could no longer corroborate it. Measured before the correction, an
    # Amber to-complete index and an Amber overhead absorption fused to 0.7000 in ONE body; they
    # are two bodies and 0.9273. A wrong dependence declaration is not merely over-cautious: it
    # destroys corroboration that was really there, which is the failure mode the positive
    # control exists to catch and which a control built from a synthetic body cannot see.
    #
    # The progress figure is declared even though declaring it creates a dependence on the other
    # readers of progress. It scales the denominator, so the reading genuinely rests on it, and a
    # fact is not omitted because its consequences are inconvenient.
    "A3.5": lineage_record(  # Overhead Absorption Rate
        "A3.5",
        source_fact_ids=("actual_pct_complete", "indirect_cost_actual", "indirect_cost_plan"),
        lineage_group_ids=(INDIRECT_COST_BODY,),
        evidence_relationship=INDEPENDENT,
        derivation_chain=("the planned and actual indirect cost and the reported progress",
                          "indirect plan scaled by progress",
                          "absorption ratio = actual indirect cost / the scaled plan")),
    # ---- RUN 20 CYCLE 4. The two advisory duplicate pairs Run 19 recorded as lineage findings
    #      and cycle 3 left undeclared. DECLARATION ONLY: no band, boundary, threshold or
    #      arithmetic result of any of these four modules is changed by their appearing here.
    #
    #      The first pair. Change Order Frequency and Contract Modification Frequency read the
    #      SAME three governed fields, compute the SAME scope-growth expression from the same two
    #      contract sums, and report the same change count. They differ only in the thresholds
    #      they band it with, which is why on one and the same project they can and do return
    #      different colours: two readings of one body of evidence, not two bodies.
    "A4.6": lineage_record(  # Change Order Frequency
        "A4.6",
        source_fact_ids=("baseline_contract_sum", "change_order_count", "revised_contract_sum"),
        lineage_group_ids=(CONTRACT_CHANGE_BODY,),
        evidence_relationship=SAME_SOURCE_TRANSFORM,
        derivation_chain=("change order log", "count of change orders",
                          "scope growth = (revised contract sum - baseline contract sum) "
                          "/ baseline contract sum")),
    "B3.5": lineage_record(  # Contract Modification Frequency
        "B3.5",
        source_fact_ids=("baseline_contract_sum", "change_order_count", "revised_contract_sum"),
        lineage_group_ids=(CONTRACT_CHANGE_BODY,),
        evidence_relationship=SAME_SOURCE_TRANSFORM,
        derivation_chain=("change order log", "count of contract modifications",
                          "scope growth = (revised contract sum - baseline contract sum) "
                          "/ baseline contract sum")),
    #      The second pair. Sensitivity Analysis perturbs the cost index and ranks three drivers;
    #      Tornado Risk Ranking ranks four present-state deviations built from the same indices
    #      and the same document risk score, plus the two progress figures. The overlap is most
    #      of the body, so it is CORRELATED rather than a transform of the other's output: it is
    #      not computed FROM the sensitivity signal, it recomputes over the same evidence. The
    #      partition does not depend on that distinction -- the shared facts settle it -- and the
    #      label is recorded because a label is a claim, and a claim is not evidence.
    "A5.2": lineage_record(  # Sensitivity Analysis
        "A5.2", source_fact_ids=("ac", "bac", "doc_risk_score", "ev", "pv"),
        lineage_group_ids=(EARNED_VALUE_BODY, DOCUMENT_BODY),
        evidence_relationship=SAME_SOURCE_TRANSFORM,
        derivation_chain=("bac,ev,ac,pv and the document risk score",
                          "cost performance index = ev / ac",
                          "estimate at completion = bac / cost performance index",
                          "one-at-a-time perturbation of the cost index by plus and minus 0.05",
                          "ranked driver swings")),
    "A5.3": lineage_record(  # Tornado Risk Ranking
        "A5.3", source_fact_ids=("ac", "actual_pct_complete", "doc_risk_score", "ev",
                                 "planned_pct_complete", "pv"),
        lineage_group_ids=(EARNED_VALUE_BODY, DOCUMENT_BODY),
        evidence_relationship=CORRELATED,
        derivation_chain=("bac,ev,ac,pv, the document risk score and the two progress figures",
                          "cost performance index = ev / ac",
                          "schedule performance index = ev / pv",
                          "absolute deviation of each index from one",
                          "absolute progress shortfall",
                          "ranked present-state deviations")),
    # ---- the synthesis, which may never corroborate anything it was built from
    "PH.5": lineage_record(
        "PH.5", source_fact_ids=(),
        dependency_ids=("A1.7", "A1.8"),
        lineage_group_ids=("PORTFOLIO_HEALTH_SYNTHESIS",),
        evidence_relationship=SYNTHESIZED,
        derivation_chain=("A1.7", "A1.8", "portfolio health constituent roll-up")),
}


def lineage_for(module_id: str) -> dict[str, Any] | None:
    """The declared lineage of a module, or None when none is declared.

    None is NOT an independence claim. A consumer that needs a partition and receives None must
    say so; `fusion` records it as an undeclared lineage rather than assuming independence.
    """
    rec = MODULE_LINEAGE.get(module_id)
    return dict(rec) if rec else None
