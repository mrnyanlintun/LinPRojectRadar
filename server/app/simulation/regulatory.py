"""
THE GOVERNED, VERSIONED REGULATORY RULE LAYER (Run 31).

WHY THIS FILE EXISTS. Before Run 31 the Category-8 regulatory identities carried their authority
inline: a FAR applicability decision was a comparison against a budget-at-completion literal
inside `models_gov.py`, an A-11 conformance result was a ratio of a cost index, and the citation
that would have told a reader WHICH RULE was being applied did not exist anywhere in the
executable path. A regulatory result with no rule identity, no edition and no effective date is
not a conformance check; it is a colour with a legal-sounding name on it.

So every rule this instrument applies is an object here, and every Category-8 result names the
object it applied. Section 32 of the Run-31 contract asks for exactly one governed versioned rule
structure rather than literals scattered across module functions, and section 33 says a rule with
a missing version, a superseded version, unknown or conflicting applicability, or missing required
evidence MUST NOT silently produce a positive conformance result. Both are enforced here, in the
constructor and in `evaluate`, so a module cannot route around them.

WHAT THIS LAYER IS NOT, and section 6 is explicit. This is a rule / authority / conformance /
governed-performance layer. IT ISSUES NO LEGAL DETERMINATION. There is no state in this file
meaning "FAR compliant", "OSHA compliant", "EPA compliant" or "legally compliant", and
`PROHIBITED_CLAIM_PATTERNS` below exists so a guard can prove no current production string says
one. The single permitted form of words is `CONFORMANCE_SENTENCE`.

THE SNAPSHOT IS FROZEN AND SUPPLIED. `REGULATORY_SNAPSHOT` is the Run-31 supervisory authority
snapshot, checked by supervisory review and reproduced verbatim. Nothing in this repository
fetches a "latest" edition from anywhere: section 33 forbids inventing currency by scraping, and
an instrument whose regulatory answers change because a website changed is not reproducible.
A rule whose edition is not the snapshot edition is SUPERSEDED and evaluates to REVIEW_REQUIRED.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

#: The Run-31 frozen supervisory authority snapshot identity. Stamped on every rule result.
REGULATORY_SNAPSHOT = "REGULATORY_SNAPSHOT_2026-08-16"

# ---------------------------------------------------------------------------------------------
# DISPOSITIONS.
#
# These are the ONLY values a rule evaluation may end in. Note what is absent: there is no
# COMPLIANT, no PASS and no CERTIFIED. SATISFIED means the configured evidence satisfies the
# configured check under the stated rule version, which is a statement about evidence and a
# configured rule, not about the law.
# ---------------------------------------------------------------------------------------------

SATISFIED = "SATISFIED"
NOT_SATISFIED = "NOT_SATISFIED"
NOT_APPLICABLE = "NOT_APPLICABLE"
INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
REVIEW_REQUIRED = "REVIEW_REQUIRED"

RULE_DISPOSITIONS = (SATISFIED, NOT_SATISFIED, NOT_APPLICABLE, INSUFFICIENT_EVIDENCE,
                     REVIEW_REQUIRED)

#: The applicability vocabulary 8.2 answers in (section 9). APPLICABLE/NOT_APPLICABLE are shared
#: with the rule dispositions above by name only; they are answers to a different question.
APPLICABLE = "APPLICABLE"
APPLICABILITY_STATES = (APPLICABLE, NOT_APPLICABLE, REVIEW_REQUIRED, INSUFFICIENT_EVIDENCE)

#: Dispositions that are NOT a positive conformance result. Section 33's requirement is that a
#: defective rule cannot land in the positive set; the guard asserts against this tuple rather
#: than against a repetition of the sentence, so the guard cannot pass by agreeing with itself.
NON_POSITIVE = (NOT_SATISFIED, NOT_APPLICABLE, INSUFFICIENT_EVIDENCE, REVIEW_REQUIRED)

#: The one permitted form of words for a conformance statement (section 6). Every Category-8
#: regulatory result renders through this and nothing else.
CONFORMANCE_SENTENCE = (
    "Available governed evidence {verb} the configured rule check under {citation} "
    "({edition}, effective {effective_date}), subject to responsible-authority review."
)

_VERBS = {
    SATISFIED: "satisfies",
    NOT_SATISFIED: "does not satisfy",
    INSUFFICIENT_EVIDENCE: "is insufficient for",
    REVIEW_REQUIRED: "requires responsible-authority review for",
    NOT_APPLICABLE: "is not within the applicability of",
}

#: Lower-cased substrings a current production Category-8 string may NEVER contain (section 42).
#: Historical reports and packages are out of scope by design: section 42 says guard current
#: production output only, and rewriting history to match today's vocabulary would destroy the
#: audit record of what the instrument used to claim.
PROHIBITED_CLAIM_PATTERNS: tuple[str, ...] = (
    "far compliant", "far-compliant", "omb compliant", "osha compliant", "epa compliant",
    "legally compliant", "legally noncompliant", "legally non-compliant", "certified compliant",
    "is compliant with far", "in compliance with far", "legal determination",
    "fully compliant", "compliance certified",
)


class RuleVersionError(ValueError):
    """A rule object was constructed without the identity a governed rule must carry."""


@dataclass(frozen=True)
class RegulatoryRule:
    """
    ONE governed, versioned regulatory or governance rule.

    Every field here is required by section 32 and none of them has a default that could stand
    in for missing governance: a rule with no edition or no effective date raises rather than
    evaluating, because the alternative is a conformance answer nobody can date.
    """

    rule_id: str
    authority_family: str          # FAR | OMB | OSHA | EPA | STATE | TRIBAL | LOCAL | CONTRACT
    citation: str                  # e.g. "FAR 34.201"
    edition: str                   # e.g. "FAC 2026-01"
    effective_date: str            # ISO date
    summary: str
    applicability_conditions: tuple[str, ...]
    required_evidence: tuple[str, ...]
    reviewer_role: str
    superseded: bool = False
    source_record: str = REGULATORY_SNAPSHOT
    section: str | None = None

    def __post_init__(self) -> None:
        for name in ("rule_id", "authority_family", "citation", "edition", "effective_date",
                     "reviewer_role"):
            if not getattr(self, name):
                raise RuleVersionError(
                    f"a governed regulatory rule cannot be constructed without {name}; "
                    f"a conformance result carrying no {name} is not datable or reviewable")
        if not self.required_evidence:
            raise RuleVersionError(
                f"rule {self.rule_id} declares no required evidence, so any evidence at all "
                f"would satisfy it; that is not a check")

    def identity(self) -> dict[str, Any]:
        """The provenance block every result carries. Section 6's required fields."""
        return {
            "rule_id": self.rule_id,
            "authority_family": self.authority_family,
            "rule_source": self.citation,
            "rule_section": self.section,
            "rule_version": self.edition,
            "effective_date": self.effective_date,
            "superseded": self.superseded,
            "reviewer_role": self.reviewer_role,
            "source_record": self.source_record,
            "regulatory_snapshot": REGULATORY_SNAPSHOT,
        }


def sentence(rule: RegulatoryRule, disposition: str) -> str:
    """The one permitted conformance form of words, filled for this rule and disposition."""
    return CONFORMANCE_SENTENCE.format(
        verb=_VERBS[disposition], citation=rule.citation,
        edition=rule.edition, effective_date=rule.effective_date)


def evaluate(rule: RegulatoryRule, evidence: Mapping[str, Any],
             *, applicable: bool | None, satisfied_when: Any = None,
             reviewer: str | None = None) -> dict[str, Any]:
    """
    Evaluate ONE governed rule against ONE evidence mapping, and refuse in every defective case.

    THE PRECEDENCE IS THE WHOLE POINT and it runs defect-first, because every ordering that puts
    the positive test earlier admits a positive answer from a rule nobody can date:

      1. superseded edition            -> REVIEW_REQUIRED  (section 33)
      2. applicability unknown         -> INSUFFICIENT_EVIDENCE
      3. not applicable                -> NOT_APPLICABLE   (and NOT_APPLICABLE != satisfied)
      4. required evidence missing     -> INSUFFICIENT_EVIDENCE, listing what is missing
      5. reviewer required and absent  -> REVIEW_REQUIRED
      6. only now, the configured test -> SATISFIED / NOT_SATISFIED

    `satisfied_when` is the module's configured logic and is a callable taking the evidence. It
    is reached ONLY at step 6, so a module cannot supply a predicate that returns True and thereby
    obtain a positive result from a superseded rule or from absent evidence.
    """
    result: dict[str, Any] = dict(rule.identity())
    result["evidence_keys_supplied"] = sorted(k for k, v in evidence.items() if v is not None)
    result["required_evidence"] = list(rule.required_evidence)
    result["reviewer"] = reviewer
    result["missing_evidence"] = []
    result["conflicting_evidence"] = []

    def done(disposition: str, reason: str) -> dict[str, Any]:
        result["result"] = disposition
        result["reason"] = reason
        result["statement"] = sentence(rule, disposition)
        return result

    if rule.superseded or rule.edition != _current_edition(rule.authority_family, rule.edition):
        return done(REVIEW_REQUIRED,
                    f"the configured edition {rule.edition} is not the edition carried by "
                    f"{REGULATORY_SNAPSHOT} for this authority, so the check is not evaluated")
    if applicable is None:
        return done(INSUFFICIENT_EVIDENCE,
                    "applicability could not be established from the governed evidence supplied")
    if applicable is False:
        return done(NOT_APPLICABLE,
                    "the governed evidence establishes this rule does not apply in this context")

    missing = [k for k in rule.required_evidence if evidence.get(k) is None]
    if missing:
        result["missing_evidence"] = missing
        return done(INSUFFICIENT_EVIDENCE,
                    "required evidence is absent: " + ", ".join(missing))
    if rule.reviewer_role and reviewer is None:
        return done(REVIEW_REQUIRED,
                    f"this rule records {rule.reviewer_role} as the responsible authority and no "
                    f"reviewer is recorded against the evidence")
    if satisfied_when is None:
        return done(REVIEW_REQUIRED, "no configured result logic was supplied for this rule")
    verdict = satisfied_when(evidence)
    if verdict is None:
        return done(INSUFFICIENT_EVIDENCE,
                    "the configured check could not be resolved on the evidence supplied")
    return done(SATISFIED if verdict else NOT_SATISFIED,
                "the configured check was evaluated on the governed evidence listed")


# ---------------------------------------------------------------------------------------------
# THE FROZEN SUPPLIED SNAPSHOT (section 7). Verbatim from supervisory review; nothing is derived.
# ---------------------------------------------------------------------------------------------

#: Current edition per authority family under this snapshot. `evaluate` compares against this,
#: so a rule constructed with any other edition is REVIEW_REQUIRED without the module having to
#: remember to check.
CURRENT_EDITIONS: dict[str, str] = {
    "FAR": "FAC 2026-01",
    "OMB": "A-11 2025-08-29",
    "OSHA": "OSHA recordkeeping/incidence guidance (snapshot 2026-08-16)",
    "EPA": "EPA Construction General Permit, 2022 as modified",
}


def _current_edition(family: str, supplied: str) -> str:
    """The snapshot edition for a family; a family with no snapshot entry is CONTRACT-governed."""
    return CURRENT_EDITIONS.get(family, supplied)


FAR_34_201 = RegulatoryRule(
    rule_id="FAR-34.201",
    authority_family="FAR", citation="FAR 34.201", section="34.201",
    edition="FAC 2026-01", effective_date="2026-03-13",
    summary=("EVMS is required for major acquisitions for development in accordance with OMB "
             "Circular A-11; the Government may also require EVMS for other acquisitions under "
             "agency procedures; where EVMS applies, contracting officers require EVMS monthly "
             "reports at minimum."),
    applicability_conditions=("federal_context", "acquisition_designation",
                              "major_acquisition_status", "agency_procedure"),
    required_evidence=("acquisition_id", "federal_context", "acquisition_designation", "agency"),
    reviewer_role="contracting officer",
)

FAR_52_234_4 = RegulatoryRule(
    rule_id="FAR-52.234-4",
    authority_family="FAR", citation="FAR 52.234-4", section="52.234-4",
    edition="FAC 2026-01", effective_date="2026-03-13",
    summary=("Where the clause applies, the contractor uses an EVMS determined by the Cognizant "
             "Federal Agency to comply with EIA-748 in the version current at time of award "
             "under the clause, and reports are submitted according to the contract."),
    applicability_conditions=("clause_incorporated",),
    required_evidence=("clause_id", "award_date", "eia748_version"),
    reviewer_role="contracting officer",
)

FAR_43_102 = RegulatoryRule(
    rule_id="FAR-43.102",
    authority_family="FAR", citation="FAR 43.102", section="43.102",
    edition="FAC 2026-01", effective_date="2026-03-13",
    summary=("Only contracting officers acting within the scope of their authority may execute "
             "Government contract modifications."),
    applicability_conditions=("federal_context",),
    required_evidence=("modification_id", "executing_official", "authority_evidence"),
    reviewer_role="contracting officer",
)

FAR_43_103 = RegulatoryRule(
    rule_id="FAR-43.103",
    authority_family="FAR", citation="FAR 43.103", section="43.103",
    edition="FAC 2026-01", effective_date="2026-03-13",
    summary="Bilateral and unilateral contract modification types are distinct.",
    applicability_conditions=("federal_context",),
    required_evidence=("modification_id", "modification_type", "signed_parties"),
    reviewer_role="contracting officer",
)

FAR_43_301 = RegulatoryRule(
    rule_id="FAR-43.301",
    authority_family="FAR", citation="FAR 43.301", section="43.301",
    edition="FAC 2026-01", effective_date="2026-03-13",
    summary=("SF 30 applicability follows the governing FAR/form rule; it is never inferred from "
             "a count of modifications."),
    applicability_conditions=("federal_context", "sf30_applicable"),
    # `written_instrument` is DELIBERATELY NOT required evidence here. It is the SUBJECT of this
    # rule's check, not a precondition for evaluating it: listing it would make an absent SF 30
    # return INSUFFICIENT_EVIDENCE, when section 12 says an applicable-but-missing form is a
    # documentation finding (NOT_SATISFIED / review). A rule may not require the very thing it
    # is testing for.
    required_evidence=("modification_id", "sf30_applicable"),
    reviewer_role="contracting officer",
)

FAR_46_2 = RegulatoryRule(
    rule_id="FAR-46.2",
    authority_family="FAR", citation="FAR Subpart 46.2", section="46.2",
    edition="FAC 2026-01", effective_date="2026-03-13",
    summary=("Contract quality requirements depend on the acquisition, including its technical "
             "description, complexity and criticality. There is no universal one-number FAR "
             "quality score."),
    applicability_conditions=("contract_quality_requirements_established",),
    required_evidence=("requirement_register", "requirement_source"),
    reviewer_role="quality assurance authority",
)

FAR_42_15 = RegulatoryRule(
    rule_id="FAR-42.15",
    authority_family="FAR", citation="FAR Subpart 42.15", section="42.15",
    edition="FAC 2026-01", effective_date="2026-03-13",
    summary=("Contractor performance information includes ratings and supporting narratives; "
             "CPARS is the official source for Federal past-performance information; evaluation "
             "factors, narratives, contractor comments/rebuttals and agency review state must "
             "remain traceable where applicable."),
    applicability_conditions=("federal_context", "official_assessment_exists"),
    required_evidence=("source_system", "assessment_id", "contract_id", "assessment_period",
                       "factor_ratings"),
    reviewer_role="assessing official",
)

OMB_A11 = RegulatoryRule(
    rule_id="OMB-A11-CAPITAL-PROGRAMMING",
    authority_family="OMB", citation="OMB Circular A-11", section="capital programming",
    edition="A-11 2025-08-29", effective_date="2025-08-29",
    summary=("Capital programming guidance. This instrument evaluates ONLY an explicitly "
             "configured requirement subset and never a global A-11 conformance state."),
    applicability_conditions=("federal_context", "capital_program"),
    required_evidence=("rule_register", "a11_edition"),
    reviewer_role="agency capital programming authority",
)

OSHA_INCIDENCE = RegulatoryRule(
    rule_id="OSHA-INCIDENCE-RATE",
    authority_family="OSHA", citation="OSHA recordable incidence rate identity",
    section="recordkeeping",
    edition="OSHA recordkeeping/incidence guidance (snapshot 2026-08-16)",
    effective_date="2026-08-16",
    summary=("IncidenceRate = RecordableCases * 200000 / EmployeeHoursWorked. Leading indicators "
             "are proactive/preventive; lagging indicators describe events that already "
             "occurred; a defensible safety system uses both classes and zero injuries alone is "
             "not proof of a strong safety programme."),
    applicability_conditions=("exposure_hours_recorded",),
    required_evidence=("recordable_cases", "employee_hours_worked"),
    reviewer_role="safety authority",
)

EPA_CGP_2022 = RegulatoryRule(
    rule_id="EPA-CGP-2022-MODIFIED",
    authority_family="EPA", citation="EPA Construction General Permit (2022, as modified)",
    section="construction stormwater",
    edition="EPA Construction General Permit, 2022 as modified",
    effective_date="2022-02-17",
    summary=("The modified 2022 EPA Construction General Permit is applicable ONLY where EPA is "
             "the permitting authority. Construction-stormwater authority may instead be state, "
             "tribal, local or another applicable jurisdictional authority, so applicability "
             "must be determined before conformance is assessed."),
    applicability_conditions=("permitting_authority_is_epa",),
    required_evidence=("jurisdiction", "permitting_authority", "permit_id"),
    reviewer_role="environmental permitting authority",
)

#: Every rule this instrument can apply, addressable by id. A module names a rule from here; it
#: does not construct one inline, which is what section 32 forbids.
RULE_REGISTER: dict[str, RegulatoryRule] = {
    r.rule_id: r for r in (
        FAR_34_201, FAR_52_234_4, FAR_43_102, FAR_43_103, FAR_43_301, FAR_46_2, FAR_42_15,
        OMB_A11, OSHA_INCIDENCE, EPA_CGP_2022,
    )
}

#: Which registered modules each rule serves. Used to generate the regulatory-currency artifact
#: mechanically rather than by transcription.
RULE_MODULES: dict[str, tuple[str, ...]] = {
    "FAR-34.201": ("B3.2", "B3.4"),
    "FAR-52.234-4": ("B3.2", "B3.4"),
    "FAR-43.102": ("B3.5",),
    "FAR-43.103": ("B3.5",),
    "FAR-43.301": ("B3.5",),
    "FAR-46.2": ("A6.1",),
    "FAR-42.15": ("A6.4",),
    "OMB-A11-CAPITAL-PROGRAMMING": ("B3.3",),
    "OSHA-INCIDENCE-RATE": ("A6.2",),
    "EPA-CGP-2022-MODIFIED": ("A6.3",),
}


def prohibited_claims_in(text: str) -> list[str]:
    """Every prohibited unqualified legal-compliance claim present in one production string."""
    low = (text or "").lower()
    return [p for p in PROHIBITED_CLAIM_PATTERNS if p in low]
