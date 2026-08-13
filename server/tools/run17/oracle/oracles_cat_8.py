"""
Run 19 independent oracles for Category 8, governance and compliance.

Written from supervisory specification section 17 and from the dated regulatory snapshot it
carries, REGULATORY_SNAPSHOT_2026-08-12, and from nothing else.

THE GOVERNING RULE OF THIS WHOLE CATEGORY, stated by the specification and enforced here:
A RULE CHECK IS NOT A LEGAL DETERMINATION. No function in this file returns "compliant". The
permitted result vocabulary is fixed below, and the prohibited claims are listed so a test can
assert their absence from what production says to a reader.

No web retrieval was performed for this run. Every authority below is cited to the committed
snapshot and is labelled REGULATORY_SNAPSHOT_2026-08-12, never "current law".
"""

from __future__ import annotations

SNAPSHOT = "REGULATORY_SNAPSHOT_2026-08-12"

#: The authorities the specification's snapshot names, with what each does and does NOT establish.
AUTHORITIES = {
    "FAR_FAC": {"cite": "FAR FAC 2026-01, effective 2026-03-13", "snapshot": SNAPSHOT},
    "FAR_34.201": {
        "cite": "FAR 34.201, earned value management system policy",
        "establishes": ("EVMS applies to major acquisitions for development in accordance with "
                        "OMB Circular A-11, and agencies may require EVMS for other acquisitions "
                        "under agency procedures. As a minimum, contractors submit monthly "
                        "reports for contracts to which EVMS applies."),
        "does_not_establish": ("any numeric cost-overrun threshold, and any inference of "
                               "applicability from the budget at completion alone"),
        "snapshot": SNAPSHOT},
    "FAR_52.234-4": {
        "cite": "FAR 52.234-4, earned value management system contract clause",
        "establishes": ("an applicable contractor system must comply with EIA-748 current at "
                        "time of award and submit reports as required by the contract"),
        "does_not_establish": "any cost or schedule performance band",
        "snapshot": SNAPSHOT},
    "FAR_43.102": {
        "cite": "FAR 43.102, contracting officer authority for modifications",
        "establishes": "that only a contracting officer acting within delegated authority may "
                       "execute a contract modification, by written instrument",
        "does_not_establish": "any threshold count of modifications",
        "snapshot": SNAPSHOT},
    "FAR_46.2": {
        "cite": "FAR Subpart 46.2, contract quality requirements",
        "establishes": "acquisition-specific quality requirements",
        "does_not_establish": "any universal quality score band",
        "snapshot": SNAPSHOT},
    "FAR_42.15": {
        "cite": "FAR Subpart 42.15, contractor performance information",
        "establishes": "CPARS as the official source for federal past-performance information",
        "does_not_establish": "any unofficial substitute assembled from project documents",
        "snapshot": SNAPSHOT},
    "OMB_A11": {
        "cite": "OMB Circular A-11, edition dated 2025-08-29",
        "establishes": "capital programming requirements expressed as configured requirements "
                       "with sections, applicability and required evidence",
        "does_not_establish": "any reduction of the circular to a budget and cost-index "
                              "threshold pair",
        "snapshot": SNAPSHOT},
    "OSHA": {
        "cite": "OSHA incidence-rate formula and OSHA leading-indicator guidance",
        "establishes": "IncidenceRate = RecordableCases * 200000 / EmployeeHoursWorked, and "
                       "that leading preventive indicators are a distinct and supported class",
        "does_not_establish": "any substitution of incidents mentioned in meeting minutes for "
                              "recordable cases, and no exposure denominator other than hours",
        "snapshot": SNAPSHOT},
    "EPA_NPDES": {
        "cite": "EPA NPDES construction stormwater, the applicable construction general permit "
                "and the governing jurisdictional permit",
        "establishes": "project, jurisdiction and permit specific obligations",
        "does_not_establish": "a compliance percentage from environmental topics mentioned in "
                              "documents",
        "snapshot": SNAPSHOT},
}

#: The only results a rule check may return. Specification 17.
RULE_RESULTS = ("Satisfied", "Not Satisfied", "Not Applicable", "Insufficient Evidence")

#: The four applicability states specification 8.2 requires be testable.
APPLICABILITY_STATES = ("Applicable", "Not Applicable", "Review Required",
                        "Insufficient Evidence")

#: Claims no module may make. Specification 17, general.
PROHIBITED_CLAIMS = ("far compliant", "far-compliant", "omb compliant", "osha compliant",
                     "epa compliant", "legally compliant", "in compliance with the law",
                     "certified compliant", "fully compliant")

PERMITTED_FORM = ("Available evidence satisfies, does not satisfy, or is insufficient for the "
                  "configured rule check, subject to responsible-authority review.")


def evms_applicability(*, acquisition_designation=None, agency=None, agency_procedure=None,
                       contract_clauses=None, award_date=None, rule_version=None) -> str:
    """
    Specification 8.2. Applicability of earned value management, from the evidence that decides
    it, never from the budget at completion.

    The four states the specification requires. Insufficient Evidence is returned when the
    deciding facts are absent, which is the case that matters: a project about which none of
    these is known is not thereby Not Applicable.
    """
    if rule_version is None:
        return "Insufficient Evidence"
    if acquisition_designation is None and agency_procedure is None:
        return "Insufficient Evidence"
    if acquisition_designation == "major_development":
        return "Applicable" if contract_clauses else "Review Required"
    if agency_procedure == "requires_evms":
        return "Applicable" if contract_clauses else "Review Required"
    if acquisition_designation == "not_major" and agency_procedure == "does_not_require":
        return "Not Applicable"
    return "Review Required"


def rule_result(*, applicable: bool | None, required_evidence_present: bool,
                evidence_satisfies: bool | None) -> str:
    """Specification 8.3. One configured requirement's result, with no fifth possibility."""
    if applicable is False:
        return "Not Applicable"
    if applicable is None or not required_evidence_present or evidence_satisfies is None:
        return "Insufficient Evidence"
    return "Satisfied" if evidence_satisfies else "Not Satisfied"


def reporting_compliance(*, applicable: bool, clause_present: bool, required_cadence_days=None,
                         due_day=None, received_day=None) -> str:
    """
    Specification 8.4. Reporting compliance is about a report being due and arriving, never
    about cost or schedule performance.
    """
    if not applicable:
        return "Not Applicable"
    if not clause_present or required_cadence_days is None or due_day is None:
        return "Insufficient Evidence"
    if received_day is None:
        return "Not Satisfied"
    return "Satisfied" if received_day <= due_day else "Not Satisfied"


def modification_governance(*, contracting_officer_id=None, modification_type=None,
                            written_instrument=False, effective_date=None,
                            approvals_present=False) -> str:
    """
    Specification 8.5 with FAR 43.102. What governs a modification is AUTHORITY and INSTRUMENT,
    not how many modifications there have been.
    """
    if contracting_officer_id is None:
        return "Not Satisfied"
    if not written_instrument or effective_date is None or modification_type is None:
        return "Insufficient Evidence"
    return "Satisfied" if approvals_present else "Not Satisfied"


def compliance_rate(satisfied: int, applicable_assessed: int) -> float:
    """
    Specification 8.6. ComplianceRate = SatisfiedApplicableAssessed / ApplicableAssessed.

    The specification's worked case is 92 of 100 assessed applicable requirements, giving .92.
    Unassessed requirements are NOT in either the numerator or the denominator, so they cannot
    silently count as satisfied.
    """
    if applicable_assessed <= 0:
        raise ValueError("no applicable assessed requirements, so no rate is defined")
    if satisfied > applicable_assessed or satisfied < 0:
        raise ValueError("more satisfied than assessed is not a rate")
    return satisfied / applicable_assessed


def critical_exception_visible(rate: float, critical_exceptions: int) -> dict:
    """
    Specification 8.6. A critical exception must remain SEPARATELY visible and is
    noncompensatory by policy: a high aggregate rate does not absorb it.
    """
    return {"rate": rate, "critical_exceptions": critical_exceptions,
            "aggregate_may_stand_alone": critical_exceptions == 0}


def osha_incidence_rate(recordable_cases: float, employee_hours_worked: float) -> float:
    """
    Specification 8.7. IncidenceRate = RecordableCases * 200000 / EmployeeHoursWorked.

    The specification's worked case: 3 cases over 200,000 hours is a rate of 3.0. Zero hours
    worked has no rate, and the specification requires abstention rather than a number.
    """
    if employee_hours_worked <= 0:
        raise ValueError("no hours worked, so no exposure and no incidence rate")
    if recordable_cases < 0:
        raise ValueError("a negative count of recordable cases is not a measurement")
    return recordable_cases * 200000.0 / employee_hours_worked


def safety_package(lagging: dict | None, leading: dict | None) -> dict:
    """
    Specification 8.7. Lagging outcomes and leading preventive evidence are DISTINCT and must be
    reported separately. Zero recorded injuries alone must not produce a strong-safety-system
    conclusion, so this returns the two halves and never one combined verdict.
    """
    return {
        "lagging": lagging,
        "leading": leading,
        "may_conclude_strong_system": bool(leading) and bool(lagging),
    }


def permit_conformance(*, permit_authority=None, permit_version=None,
                       requirements: list[dict] | None = None) -> dict:
    """
    Specification 8.8. Environmental conformance is project, jurisdiction and permit specific,
    so the authority and the permit version are part of the question, not context.
    """
    if permit_authority is None or permit_version is None:
        return {"result": "Insufficient Evidence", "rate": None, "critical_violations": None}
    reqs = requirements or []
    assessed = [r for r in reqs if r.get("applicable") and r.get("result") is not None]
    if not assessed:
        return {"result": "Insufficient Evidence", "rate": None, "critical_violations": None}
    satisfied = sum(1 for r in assessed if r["result"] == "Satisfied")
    critical = sum(1 for r in assessed
                   if r["result"] == "Not Satisfied" and r.get("critical"))
    return {"result": "Satisfied" if satisfied == len(assessed) else "Not Satisfied",
            "rate": satisfied / len(assessed), "critical_violations": critical}


def worst_dimension(ratings: dict[str, float]) -> tuple[str, float]:
    """
    Specification 8.9. The worst or critical dimension is preserved SEPARATELY rather than
    averaged away without policy authority.
    """
    name = min(ratings, key=lambda k: (ratings[k], k))
    return name, ratings[name]


def says_prohibited(text: str) -> list[str]:
    """Any prohibited legal-certification claim present in a sentence shown to a reader."""
    low = (text or "").lower()
    return [c for c in PROHIBITED_CLAIMS if c in low]


def self_test() -> list[str]:
    fails: list[str] = []

    def eq(label, got, want, tol=1e-9):
        if got is None or abs(float(got) - float(want)) > tol:
            fails.append(f"{label}: got {got!r}, specification says {want!r}")

    # 8.2 -- all four applicability states are reachable, and none from the budget.
    got = {
        evms_applicability(rule_version="FAC 2026-01", acquisition_designation="major_development",
                           contract_clauses=["52.234-4"]),
        evms_applicability(rule_version="FAC 2026-01", acquisition_designation="not_major",
                           agency_procedure="does_not_require"),
        evms_applicability(rule_version="FAC 2026-01", acquisition_designation="major_development"),
        evms_applicability(),
    }
    if got != {"Applicable", "Not Applicable", "Review Required", "Insufficient Evidence"}:
        fails.append(f"8.2 all four applicability states must be reachable, got {sorted(got)}")
    if evms_applicability(rule_version="FAC 2026-01") != "Insufficient Evidence":
        fails.append("8.2 a rule version alone does not decide applicability")

    # 8.3 -- the four rule results, and no fifth.
    if rule_result(applicable=False, required_evidence_present=True,
                   evidence_satisfies=True) != "Not Applicable":
        fails.append("8.3 an inapplicable requirement is Not Applicable")
    if rule_result(applicable=True, required_evidence_present=False,
                   evidence_satisfies=None) != "Insufficient Evidence":
        fails.append("8.3 absent required evidence is Insufficient Evidence, never Satisfied")
    if rule_result(applicable=True, required_evidence_present=True,
                   evidence_satisfies=True) != "Satisfied":
        fails.append("8.3 satisfied evidence is Satisfied")
    if rule_result(applicable=True, required_evidence_present=True,
                   evidence_satisfies=False) != "Not Satisfied":
        fails.append("8.3 unsatisfied evidence is Not Satisfied")

    # 8.4 -- a report received after its due date is not satisfied, whatever performance says.
    if reporting_compliance(applicable=True, clause_present=True, required_cadence_days=30,
                            due_day=30, received_day=28) != "Satisfied":
        fails.append("8.4 a report received before its due date satisfies the check")
    if reporting_compliance(applicable=True, clause_present=True, required_cadence_days=30,
                            due_day=30, received_day=45) != "Not Satisfied":
        fails.append("8.4 a late report does not satisfy the check")
    if reporting_compliance(applicable=True, clause_present=False,
                            required_cadence_days=30) != "Insufficient Evidence":
        fails.append("8.4 no clause means insufficient evidence")

    # 8.5 -- authority governs, not count.
    if modification_governance() != "Not Satisfied":
        fails.append("8.5 a modification with no contracting officer does not satisfy")
    if modification_governance(contracting_officer_id="CO-1", modification_type="bilateral",
                               written_instrument=True, effective_date="2026-05-01",
                               approvals_present=True) != "Satisfied":
        fails.append("8.5 an authorised written bilateral modification satisfies")

    # 8.6 -- 92 of 100 is .92, and unassessed cannot become satisfied.
    eq("8.6 compliance rate", compliance_rate(92, 100), 0.92)
    try:
        compliance_rate(120, 100)
        fails.append("8.6 more satisfied than assessed must be refused")
    except ValueError:
        pass
    try:
        compliance_rate(0, 0)
        fails.append("8.6 no assessed applicable requirements has no rate")
    except ValueError:
        pass
    if critical_exception_visible(0.99, 1)["aggregate_may_stand_alone"]:
        fails.append("8.6 one critical exception must remain separately visible and must not be "
                     "absorbed by a high aggregate rate")

    # 8.7 -- 3 cases over 200,000 hours is 3.0; zero hours abstains.
    eq("8.7 OSHA incidence rate", osha_incidence_rate(3, 200000), 3.0)
    eq("8.7 the rate scales with exposure", osha_incidence_rate(3, 400000), 1.5)
    try:
        osha_incidence_rate(3, 0)
        fails.append("8.7 zero hours worked has no exposure and no rate")
    except ValueError:
        pass
    if safety_package({"rate": 0.0}, None)["may_conclude_strong_system"]:
        fails.append("8.7 zero recorded injuries alone must not conclude a strong safety system")
    if not safety_package({"rate": 0.0}, {"inspections": 12})["may_conclude_strong_system"]:
        fails.append("8.7 lagging and leading evidence together may support the conclusion")

    # 8.8 -- no permit authority or version means insufficient evidence, not a percentage.
    if permit_conformance()["result"] != "Insufficient Evidence":
        fails.append("8.8 no permit authority or version is insufficient evidence")
    pc = permit_conformance(permit_authority="EPA CGP", permit_version="2022 CGP",
                            requirements=[{"applicable": True, "result": "Satisfied"},
                                          {"applicable": True, "result": "Not Satisfied",
                                           "critical": True}])
    eq("8.8 conformance rate", pc["rate"], 0.5)
    if pc["critical_violations"] != 1:
        fails.append("8.8 a critical permit violation must remain separately counted")

    # 8.9 -- the worst dimension survives.
    name, val = worst_dimension({"overall": 4.5, "schedule": 4.0, "cost": 4.2, "quality": 2.0})
    if name != "quality" or val != 2.0:
        fails.append(f"8.9 the worst dimension is quality at 2.0, got {name} at {val}")

    # The prohibited-claim detector must actually detect.
    if not says_prohibited("This project is FAR compliant"):
        fails.append("the prohibited-claim detector must detect a compliance certification")
    if says_prohibited("Available evidence satisfies the configured rule check"):
        fails.append("the permitted form must not be flagged as a prohibited claim")

    return fails


_FAILS = self_test()
assert not _FAILS, "Category 8 oracle does not reproduce the specification: " + "; ".join(_FAILS)
