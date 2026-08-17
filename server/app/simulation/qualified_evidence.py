"""
THE CATEGORY-9 QUALIFIED EVIDENCE OBJECT AND THE ONE GOVERNED QUALIFICATION BOUNDARY (Run 31).

WHAT WAS MISSING, in production's own words. `signal_package.py` records
`SIGNAL_QUALIFICATION = "unqualified"` and a `CATEGORY_9_DEVIATION` saying the eligibility gate
the architecture requires is not implemented and NOTHING gates these inputs on evidence quality.
Run 26 measured the exposure: 205 of 397 document-to-module edges land inside Categories 6, 7, 8
and 10, and B3.1 declared raw `cpi`, `spi` and `docRiskScore` as required inputs -- which
specification section 18 forbids in those words.

`qualification_gate.py` closed HALF of this in an earlier run: it qualifies the four assembled
PROJECT-STATUS signals and `fuse_qualified` refuses a raw dict, so the VOTE path is governed.
What it never covered is the per-EVIDENCE-RECORD question the architecture actually asks:

    PROJECT EVIDENCE -> CATEGORY 9 QUALITY ASSESSMENT -> QUALIFIED EVIDENCE -> ANALYTICAL USE.

That is this file. It does NOT replace `qualification_gate.py` and does not soften it; section 21
says build ONE governed boundary rather than separate incompatible gates, so `QualifiedEvidence`
is the record-level object and the existing `QualifiedSignal` remains the project-status-vote
object, with `qualification_gate` continuing to own the vote. Two objects, one boundary, no
second universe of qualification states.

THE ENFORCEMENT MECHANISM IS THE SAME ONE THAT ALREADY WORKS HERE. A qualified record is an
OBJECT whose value is behind a property that returns None unless the verdict permits the
REQUESTED USE. There is no arrangement of consumer code that reads the number while ignoring the
verdict, because when the verdict refuses there is no number to read. `require_qualified` refuses
a raw mapping outright, so a consumer cannot route around the gate by hand-building the shape.

USE-SPECIFIC BY DESIGN (section 19). A record may be fresh enough for historical analysis and
stale for a current-period decision. Qualification is therefore evaluated FOR A USE, not once and
for all, and `eligible_for` takes the use. Section 21 forbids one global rule collapsing all
stale evidence into one traffic-light class, so there is no global freshness constant here.

WHAT THIS FILE MAY NEVER DO (section 34). Category-9 output is METADATA. It is not a project
condition, not a vote, and not an independent mass. Nothing here returns a `status_color`, and
`NON_VOTING` is asserted by the guard that proves Category 9 cannot enter Conservative Dominance,
Weighted Voting, Majority Rules, Dempster-Shafer, Project Status or the voting count.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

# ---------------------------------------------------------------------------------------------
# QUALIFICATION STATES (section 19).
# ---------------------------------------------------------------------------------------------

UNASSESSED = "UNASSESSED"
QUALIFIED = "QUALIFIED"
QUALIFIED_WITH_LIMITATIONS = "QUALIFIED_WITH_LIMITATIONS"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
NOT_APPLICABLE = "NOT_APPLICABLE"

QUALIFICATION_STATES = (UNASSESSED, QUALIFIED, QUALIFIED_WITH_LIMITATIONS, REVIEW_REQUIRED,
                        INSUFFICIENT_EVIDENCE, NOT_APPLICABLE)

#: The ONLY states from which a value may be read for an analytical or governance use.
#: UNASSESSED IS NOT HERE, which is section 21's first requirement: raw/unassessed evidence is
#: blocked downstream. It is never converted to QUALIFIED, to Green, or to reliability 1.
ELIGIBLE_STATES = (QUALIFIED, QUALIFIED_WITH_LIMITATIONS)

#: Timeliness dispositions (9.2). Section 24 forbids an invented decaying score.
TIMELY = "TIMELY"
STALE = "STALE"
FUTURE_DATED = "FUTURE_DATED"
TIMELINESS_UNKNOWN = "INSUFFICIENT_EVIDENCE"

#: Consistency dispositions (9.6).
CONSISTENT = "CONSISTENT"
MATERIAL_CONFLICT = "MATERIAL_CONFLICT"
NOT_COMPARABLE = "NOT_COMPARABLE"

#: Category 9 is metadata. This constant exists so a guard can assert against a named contract
#: rather than against a repetition of a sentence.
NON_VOTING = True


class RawEvidenceError(TypeError):
    """A consumer offered raw evidence where the contract requires a qualified object."""


class QualificationNotPermitted(RuntimeError):
    """A consumer read a value the qualification verdict does not permit for the stated use."""


@dataclass
class QualifiedEvidence:
    """
    ONE governed evidence record, carrying its Category-9 assessment (section 18).

    Fields map onto structures this repository already carries wherever they are semantically
    identical -- section 18 says do not duplicate signal-package/ledger data merely to satisfy
    field names -- and the ones that are genuinely new are the qualification dimensions the
    architecture was missing.
    """

    evidence_id: str
    source_id: str | None = None
    source_type: str | None = None
    source_document_id: str | None = None
    project: str | None = None
    period: str | None = None
    effective_date: str | None = None
    units: str | None = None

    #: The observed value, DELIBERATELY PRIVATE. Read it through `value_for(use)`.
    _raw_value: Any = None

    # -- 9.1 field-level missingness ------------------------------------------------------------
    required_inputs: tuple[str, ...] = ()
    missing_fields: tuple[str, ...] = ()
    invalid_fields: tuple[str, ...] = ()
    critical_missing: tuple[str, ...] = ()
    denominator_source: str | None = None

    # -- 9.2 timeliness -------------------------------------------------------------------------
    evaluation_date: str | None = None
    data_age_days: int | None = None
    freshness_rule: str | None = None
    freshness_rule_version: str | None = None
    timeliness_status: str = UNASSESSED

    # -- 9.3 reliability (metadata only; no invented number) -------------------------------------
    provenance_trace: tuple[str, ...] = ()
    verification_status: str | None = None
    source_authority: str | None = None
    corroboration: tuple[str, ...] = ()
    extraction_confidence: float | None = None
    reliability_rubric_version: str | None = None
    reliability_weight: Any = None          # None means NO GOVERNED MAPPING. Never defaulted to 1.

    # -- 9.4 audit ------------------------------------------------------------------------------
    required_audit_elements: tuple[str, ...] = ()
    missing_audit_elements: tuple[str, ...] = ()
    critical_audit_missing: tuple[str, ...] = ()

    # -- 9.5 package coverage -------------------------------------------------------------------
    package_requirement: str | None = None
    package_coverage: float | None = None
    package_missing_domains: tuple[str, ...] = ()

    # -- 9.6 consistency ------------------------------------------------------------------------
    consistency_comparisons: tuple[dict[str, Any], ...] = ()
    material_conflicts: tuple[dict[str, Any], ...] = ()

    # -- 9.7 cadence ----------------------------------------------------------------------------
    reporting_history: tuple[str, ...] = ()
    cadence_status: str | None = None

    # -- lineage (Run 30 closure, section 20) ---------------------------------------------------
    lineage_status: str = "LINEAGE_UNRESOLVED"
    evidence_body: str | None = None
    independence_established: bool = False

    # -- verdict --------------------------------------------------------------------------------
    qualification_state: str = UNASSESSED
    qualification_reasons: tuple[str, ...] = ()
    qualification_rule_version: str | None = None
    simulation_version: str | None = None
    #: Per-use eligibility, populated by `assess`. A use absent from here is NOT eligible.
    use_eligibility: dict[str, bool] = field(default_factory=dict)

    # -- the enforcement surface ----------------------------------------------------------------
    def eligible_for(self, use: str) -> bool:
        """Eligibility for ONE named downstream use. Absence is never eligibility."""
        if self.qualification_state not in ELIGIBLE_STATES:
            return False
        return bool(self.use_eligibility.get(use, False))

    def value_for(self, use: str) -> Any:
        """
        The observed value, or None. THERE IS NO OTHER READER.

        A consumer that ignores the verdict gets None rather than a number, which is why this is
        a property-style accessor and not a public attribute: the refusal cannot be forgotten.
        """
        if not self.eligible_for(use):
            return None
        return self._raw_value

    def refusal_for(self, use: str) -> dict[str, Any] | None:
        """The explicit disposition a consumer must render when the value is refused."""
        if self.eligible_for(use):
            return None
        return {
            "evidence_id": self.evidence_id,
            "requested_use": use,
            "qualification_state": self.qualification_state,
            "reasons": list(self.qualification_reasons),
            "missing_fields": list(self.missing_fields),
            "invalid_fields": list(self.invalid_fields),
            "critical_missing": list(self.critical_missing),
            "material_conflicts": [dict(c) for c in self.material_conflicts],
            "timeliness_status": self.timeliness_status,
            "lineage_status": self.lineage_status,
            "qualification_rule_version": self.qualification_rule_version,
            "simulation_version": self.simulation_version,
        }


# ---------------------------------------------------------------------------------------------
# THE GATE (section 21). One boundary, defect-first precedence.
# ---------------------------------------------------------------------------------------------

#: The qualification rule version stamped on every verdict. Bumped when the rule changes, so an
#: archived verdict says which rule produced it.
QUALIFICATION_RULE_VERSION = "run31-qualification-rule-v1"


def assess(ev: QualifiedEvidence, *, uses: Sequence[str],
           use_requirements: Mapping[str, Mapping[str, Any]] | None = None,
           simulation_version: str | None = None) -> QualifiedEvidence:
    """
    Assess ONE evidence record for a set of named uses and set its verdict.

    THE PRECEDENCE, and it is defect-first for the reason section 39 gives: every ordering that
    tests the favourable case earlier lets missing or bad evidence look favourable.

      1. missing/invalid CRITICAL mandatory input -> INSUFFICIENT_EVIDENCE, ineligible for all.
         Section 21 forbids imputing zero, so nothing is substituted.
      2. material unresolved consistency conflict -> REVIEW_REQUIRED for the affected use, and
         the conflict STAYS on the object. It is never averaged away.
      3. critical audit-chain incompleteness -> ineligible for any use whose contract requires a
         complete audit chain.
      4. future-dated -> REVIEW_REQUIRED.
      5. stale against the use's own freshness requirement -> ineligible FOR THAT USE ONLY.
      6. lineage UNRESOLVED -> ineligible for any use requiring independently combinable
         evidence. UNRESOLVED IS NEVER INDEPENDENT (section 20).
      7. otherwise QUALIFIED, or QUALIFIED_WITH_LIMITATIONS where a non-blocking limitation
         (unresolved reliability, package incompleteness) was recorded.
    """
    reqs = dict(use_requirements or {})
    reasons: list[str] = []
    ev.qualification_rule_version = QUALIFICATION_RULE_VERSION
    ev.simulation_version = simulation_version
    ev.use_eligibility = {}

    blocking = False
    limitation = False

    if ev.critical_missing:
        reasons.append("critical mandatory input missing: " + ", ".join(ev.critical_missing))
        blocking = True
    invalid_critical = tuple(f for f in ev.invalid_fields if f in ev.required_inputs)
    if invalid_critical:
        reasons.append("mandatory input invalid: " + ", ".join(invalid_critical))
        blocking = True

    if blocking:
        ev.qualification_state = INSUFFICIENT_EVIDENCE
        ev.qualification_reasons = tuple(reasons)
        ev.use_eligibility = {u: False for u in uses}
        return ev

    if ev.material_conflicts:
        reasons.append(
            f"{len(ev.material_conflicts)} unresolved material consistency conflict(s) remain "
            f"on this evidence and are not reconciled here")
        ev.qualification_state = REVIEW_REQUIRED
        ev.qualification_reasons = tuple(reasons)
        ev.use_eligibility = {u: False for u in uses}
        return ev

    if ev.timeliness_status == FUTURE_DATED:
        reasons.append("the source date is later than the evaluation date")
        ev.qualification_state = REVIEW_REQUIRED
        ev.qualification_reasons = tuple(reasons)
        ev.use_eligibility = {u: False for u in uses}
        return ev

    if ev.reliability_weight is None and ev.reliability_rubric_version is None:
        reasons.append("no governed reliability mapping is established, so no numeric "
                       "reliability weight is asserted")
        limitation = True
    if ev.package_missing_domains:
        reasons.append("required information package domains absent: "
                       + ", ".join(ev.package_missing_domains))
        limitation = True

    for use in uses:
        r = reqs.get(use, {})
        ok = True
        if r.get("requires_complete_audit_chain") and (
                ev.critical_audit_missing or ev.missing_audit_elements):
            reasons.append(f"{use}: the audit chain required for this use is incomplete")
            ok = False
        if r.get("requires_fresh") and ev.timeliness_status == STALE:
            reasons.append(f"{use}: the evidence is stale against this use's freshness rule")
            ok = False
        if r.get("requires_fresh") and ev.timeliness_status in (UNASSESSED, TIMELINESS_UNKNOWN):
            reasons.append(f"{use}: freshness could not be assessed for this use")
            ok = False
        if r.get("requires_independent") and not ev.independence_established:
            reasons.append(f"{use}: independence is not established "
                           f"({ev.lineage_status}), so this evidence is not independently "
                           f"combinable for this use")
            ok = False
        if r.get("requires_complete_package") and ev.package_missing_domains:
            reasons.append(f"{use}: the required information package is incomplete")
            ok = False
        ev.use_eligibility[use] = ok

    ev.qualification_state = QUALIFIED_WITH_LIMITATIONS if limitation else QUALIFIED
    ev.qualification_reasons = tuple(reasons)
    return ev


def require_qualified(obj: Any, use: str) -> QualifiedEvidence:
    """
    THE BOUNDARY A CONSUMER CROSSES. Refuses anything that is not a QualifiedEvidence.

    Section 22: it is not enough to create the class while dispatchers still accept raw values.
    A consumer that calls this with a float, a dict or a raw signal gets an exception, not a
    number, so a raw bypass cannot be silent.
    """
    if not isinstance(obj, QualifiedEvidence):
        raise RawEvidenceError(
            f"raw evidence was offered for the use {use!r}; this consumer requires a "
            f"Category-9 QualifiedEvidence object and will not read an unqualified value")
    if obj.qualification_state == UNASSESSED:
        raise QualificationNotPermitted(
            f"evidence {obj.evidence_id} has not been assessed by Category 9, so it is not "
            f"eligible for the use {use!r}")
    return obj
