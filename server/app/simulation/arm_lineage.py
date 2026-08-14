"""
RUN 20 CYCLE 9, ARCH.5. THE FOUR ASSEMBLED ARMS, DECLARED ONCE FOR EVERY MODULE THAT READS THEM.

WHY THIS FILE EXISTS. Cycle 7 established, by execution rather than by field name, what the four
assembled signal arms actually rest on. Cycle 7 fixed B2.1, the one Dempster combination that
read them. The cycle 7 neighbour sweep then found SEVEN MORE registered modules reading the SAME
FOUR ARMS -- B2.2, B2.3, B2.4, B2.5, B2.6, B2.7, B2.8 and B2.9 -- and aggregating them with
EQUAL WEIGHT PER ARM. That is ARCH.5.

THE WARNING ARCH.5 CARRIES, AND IT IS THE REASON THIS IS NOT A COPY OF B2.1'S FIX. None of these
modules is a Dempster combination, so B2.1's precondition does not transfer to them unaltered.
What DOES transfer is the fact underneath it, which is a property of ANCESTRY and not of
aggregation syntax: three of the four arms are readings of ONE earned-value measurement.

  index arm      the lesser of the cost and schedule indices          EARNED VALUE
  forecast arm   the eightieth-percentile overrun, a Beta-PERT
                 forecast scaled by those same two indices and
                 spread by the document risk score                    EARNED VALUE + DOCUMENT
                                                                      (this arm is the BRIDGE)
  trend arm      a cumulative sum over the schedule index history     EARNED VALUE + HISTORY
  document arm   the document risk score                              DOCUMENT

SO AN EQUAL-WEIGHT-PER-ARM AGGREGATION GIVES THE EARNED-VALUE MEASUREMENT THREE QUARTERS OF THE
VOTE AND THE DOCUMENT EVIDENCE ONE QUARTER, on evidence that is one measurement and one document
score. Measured on B2.2 Rough Sets, whose classification is a ratio of arm counts against the arm
total: three Red earned-value readings give exactly 0.75, which is the boundary its
lower-approximation test sits on. The duplication is not a rounding effect; it decides the band.

WHAT IS DONE ABOUT IT, AND WHAT IS DELIBERATELY NOT DONE.

  NOT DONE: no weight is introduced. No arm is given a correlation coefficient, a reliability
  discount or a tuned multiplier. There is no defensible empirical basis in this repository for
  any such number and inventing one would be worse than the duplication.

  DONE: the arms are separated into INDEPENDENT BODIES by the existing lineage contract -- the
  same `evidence_bodies` every other consumer uses, with no transitive closure -- and each body
  contributes ONE reading, the most adverse of its members. That operator is IDEMPOTENT, which is
  exactly the property required: a second and a third reading of one body change nothing. It is
  an OWNER_POLICY governance choice, it carries no parameter, and it is the same operator
  `fusion.fuse_signals` and B2.1 already apply for the same reason.

  Ties within a body keep the EARLIEST arm in the module's own evaluation order: declared,
  deterministic, and deliberately not a choice made by which reading gives the more convenient
  answer.

THE SCHEDULE INDEX HAS TWO ANCESTRIES AND THAT IS HANDLED BY THE CYCLE 8 RESOLVER, NOT ASSUMED.
`extraction_merge` derives the schedule index from the earned value over the planned value, and
falls back to actual over planned progress when no planned value exists. A record keyed only by
module id is wrong in one regime whichever ancestry it names. `separate_arms` therefore resolves
the declarations against the project's own evidence before separating, and the resolution can
only ever narrow. Both regimes are measured in the cycle 9 suite rather than reasoned about: in
BOTH, the three earned-value arms remain one body and the document arm remains a second, because
in the fallback regime the index arm and the trend arm intersect on the progress figures instead
of on the earned value.
"""

from __future__ import annotations

from typing import Any

from .fusion import BAND_SEVERITY
from .lineage import (
    CORRELATED, DOCUMENT_BODY, EARNED_VALUE_BODY, INDEPENDENT, REPORTING_HISTORY_BODY,
    SAME_SOURCE_TRANSFORM, evidence_bodies, lineage_record, resolve_records_for_evidence,
)

#: The arms' declared lineage. Each names the PRIMITIVE facts the arm's reading ultimately rests
#: on, not the immediate argument it is handed: the cost index is not a fact, it is a step.
ARM_LINEAGE_EVM = lineage_record(
    "B2.1.evm", source_fact_ids=("ac", "ev", "pv"),
    lineage_group_ids=(EARNED_VALUE_BODY,),
    evidence_relationship=SAME_SOURCE_TRANSFORM,
    derivation_chain=("ev,ac,pv", "cost performance index = ev / ac",
                      "schedule performance index = ev / pv", "the lesser of the two indices"))
# THE BUDGET IS DELIBERATELY ABSENT HERE, AND CYCLE 7'S OWN FIRST DRAFT DECLARED IT. A1.1 reads
# the budget and its absolute forecast figures rest on it, so A1.1's own record names it
# correctly. THIS ARM READS ONLY THE EIGHTIETH-PERCENTILE OVERRUN AS A PERCENTAGE OF THE BUDGET,
# and that ratio is scale-invariant in the budget: doubling the budget does not move it by a
# rounding step. A fact that cannot move an arm's reading is not that arm's evidence, whatever
# the producing module rests on, and the material-influence probe is what caught the
# over-declaration rather than any amount of reading the producer's declaration.
ARM_LINEAGE_MC = lineage_record(
    "B2.1.mc", source_fact_ids=("ac", "doc_risk_score", "ev", "pv"),
    lineage_group_ids=(EARNED_VALUE_BODY, DOCUMENT_BODY),
    evidence_relationship=CORRELATED,
    derivation_chain=("A1.1", "cost performance index = ev / ac",
                      "schedule performance index = ev / pv",
                      "estimate at completion scaled by the two indices",
                      "stochastic sampling spread by the document risk score",
                      "eightieth-percentile overrun against the budget"))
ARM_LINEAGE_CUSUM = lineage_record(
    "B2.1.cusum", source_fact_ids=("ev", "pv", "reporting_history"),
    lineage_group_ids=(EARNED_VALUE_BODY, REPORTING_HISTORY_BODY),
    evidence_relationship=CORRELATED,
    derivation_chain=("A1.2", "schedule index history ending with this period",
                      "two-sided cumulative sum of the index deviations",
                      "whether the decision interval was breached"))
ARM_LINEAGE_DOC = lineage_record(
    "B2.1.doc", source_fact_ids=("doc_risk_score",),
    lineage_group_ids=(DOCUMENT_BODY,),
    evidence_relationship=INDEPENDENT,
    derivation_chain=("the document risk score",))

#: The arm each assembled signal key supplies, so that a module which reads the keys can name the
#: lineage without restating it. `evm` supplies ONE arm even though it carries two indices: the
#: cost index and the schedule index are two readings of one earned-value measurement and were
#: never two arms.
ARM_LINEAGE_BY_KEY: dict[str, dict] = {
    "evm": ARM_LINEAGE_EVM,
    "mc": ARM_LINEAGE_MC,
    "cusum": ARM_LINEAGE_CUSUM,
    "doc": ARM_LINEAGE_DOC,
}


def separate_arms(arm_records: list[dict], si: dict | None = None) -> list[list[int]]:
    """
    Separate the PRESENT arms into independent bodies of evidence, in the module's own order.

    Returns a list of bodies, each a sorted list of indices into `arm_records`. The declarations
    are resolved against the project's evidence first, so the schedule index's ancestry is the
    one the project's own facts select rather than the one a module id would guess.
    """
    resolved = resolve_records_for_evidence(arm_records, si) if si is not None else arm_records
    groups = evidence_bodies(resolved)["bodies"]
    return [sorted(g) for g in groups]


def one_reading_per_body(arm_records: list[dict], arm_bands: list[str],
                         si: dict | None = None) -> dict[str, Any]:
    """
    THE ARCH.5 DEDUPLICATION, WEIGHT-FREE.

    Given the present arms and the band each of them reads, return the indices of the arms that
    survive: one per independent body, the most adverse reading in that body, ties going to the
    earliest arm in the module's own evaluation order.

    `kept` is what a caller aggregates over. `bodies` is the audit trail, so a reader of a stored
    result can see that three arms were one body rather than having to infer it from a count that
    says nothing about dependence.
    """
    bodies = separate_arms(arm_records, si)
    kept: list[int] = []
    summary: list[dict[str, Any]] = []
    for members in bodies:
        worst = max(BAND_SEVERITY.get(arm_bands[i], -1) for i in members)
        pick = next(i for i in members if BAND_SEVERITY.get(arm_bands[i], -1) == worst)
        kept.append(pick)
        summary.append({
            "representative_arm_id": arm_records[pick]["module_id"],
            "member_arm_ids": [arm_records[i]["module_id"] for i in members],
            "member_bands": [arm_bands[i] for i in members],
            "disagreement": len({arm_bands[i] for i in members}) > 1,
        })
    order = sorted(range(len(kept)), key=lambda j: kept[j])
    return {
        "kept": [kept[j] for j in order],
        "bodies": [summary[j] for j in order],
        "arms_present": len(arm_records),
        "bodies_of_evidence": len(bodies),
        "arms_suppressed_as_duplicate": len(arm_records) - len(bodies),
    }
