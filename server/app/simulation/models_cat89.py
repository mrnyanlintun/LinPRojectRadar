"""
THE CATEGORY-8 AND CATEGORY-9 OPERATIONAL RUNNERS, v17. ONE THIN ROUTE PER MODULE.

WHY THIS FILE EXISTS, AND IT IS RUN 30'S OWN LESSON APPLIED BEFORE THE DEFECT HAPPENS AGAIN.
Run 30 built `canonical_v5.py` -- nineteen governed structures, 239 passing oracle checks, a
39-fault campaign -- AND PRODUCTION NEVER CALLED ANY OF IT. Executing the production entry point
for all twenty Category-7 identities and profiling the interpreter gave `canonical_v5` reached on
ZERO of twenty. A correct library behind an incorrect ledger is a failed remediation, and every
direct-call proof of that library was green for the whole time the defect existed.

So `server/tools/test_run31_operational_route.py` never calls `canonical_v6` to prove anything.
It executes `registry.run_module` and profiles the interpreter, and it derives the route list
FROM THE SHIPPED REGISTRY rather than from a hand-written list, because section 40 forbids a
hand-written test list that duplicates the dispatcher.

WHAT EACH RUNNER IS ALLOWED TO DO, and it is deliberately almost nothing:

    governed input -> Category-9 qualification -> canonical structure validation
                   -> canonical implementation -> canonical result or explicit abstention -> row

A runner reads its module's governed structure off the signal inputs, qualifies it, hands it to
the canonical function and renders the answer. It performs NO arithmetic of its own, so there is
nowhere for a proxy to live. In particular NOTHING HERE READS `cpi`, `spi` OR `docRiskScore`:
specification section 18 forbids raw index consumption in exactly these categories, and the
legacy implementations that manufactured a governance band from a cost index are now unreferenced
by the registry.

THE CATEGORY-8 SELF-GATE (section 37). Category 8 consumes governed evidence too. Every
Category-8 runner qualifies its structure through `qualified_evidence` BEFORE the canonical
function is reached, so 8.1 cannot authorize from an unassessed signal, 8.2 cannot declare
applicability from unqualified data, and 8.5 cannot accept an unassessed authority claim. This
is NOT Category 8 depending on its own output: what is assessed is the underlying evidence
RECORD, which is what section 37 asks for.

CATEGORY 9 IS METADATA AND CASTS NO VOTE (section 34). Every C1 row here carries
`category_9_metadata_only = True` and `voting_eligible = False`, and no C1 row asserts a
`status_color`. Group C is already excluded from the project-status rollup in `compute.py` --
that is the Run-26 architectural exclusion this run must preserve -- and these flags let the
non-voting guard assert against a named contract on the row rather than against the rollup alone.

NO BAND IS INVENTED ANYWHERE IN THIS FILE. Run 33 owns calibration. Every canonical quantity is
emitted with `calibration_pending` and no `status_color`, which `registry.record` already routes
to the computed rows rather than treating as an abstention.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

from . import band_reference as _BR
from . import canonical_v6 as V6
from .abm import ABMStructureError
from .canonical import StructureAbsent
from .canonical_v6 import V6_STRUCTURE_KEYS, V6_STRUCTURE_WORDS, v6_structure
from .lineage import evidence_body_of, independence_established, lineage_status
from .models import ABSTAIN_STRUCTURE_ABSENT, PROVENANCE_WORDS
from .qualified_evidence import (
    QualifiedEvidence, QUALIFICATION_RULE_VERSION, UNASSESSED, assess,
)
from .signal_package import SIGNAL_QUALIFICATION

#: Stamped on every Category-8/9 ledger row this file produces, computed or abstaining. A row
#: without this marker did not come from here, which is how the route inventory is verified
#: from the ledger rather than from a report.
RESULT_SOURCE = "CANONICAL_V6_LAYER"

DISPOSITION_COMPUTED = "CANONICAL_RESULT"
DISPOSITION_STRUCTURE_ABSENT = "NOT_ESTIMABLE_STRUCTURE_ABSENT"
DISPOSITION_UNQUALIFIED = "BLOCKED_UNQUALIFIED_EVIDENCE"

#: Which downstream use each module's evidence is qualified FOR. Qualification is use-specific
#: (section 19), so a module names its use rather than asking a global question.
MODULE_USE: dict[str, str] = {
    "A6.1": "requirement_conformance",
    "A6.2": "safety_measurement",
    "A6.3": "environmental_conformance",
    "A6.4": "official_assessment_ingestion",
}

#: What each use requires of its evidence. Section 21 forbids one global rule; these are the
#: per-use requirements, and a use absent a requirement does not acquire one by default.
USE_REQUIREMENTS: dict[str, dict[str, Any]] = {
    "governance_authorization": {"requires_complete_audit_chain": True, "requires_fresh": True},
    "regulatory_applicability": {},
    "regulatory_conformance": {},
    "governance_authority_check": {"requires_complete_audit_chain": True},
    "requirement_conformance": {},
    "safety_measurement": {},
    "environmental_conformance": {},
    "official_assessment_ingestion": {},
    # Category 9 assesses evidence; it does not itself require qualified evidence, which would
    # be the circular architecture section 22 forbids.
    "quality_assessment": {},
}


def _qualify(module_id: str, structure: dict) -> QualifiedEvidence:
    """
    THE CATEGORY-9 ASSESSMENT EVERY CATEGORY-8 ROUTE PASSES THROUGH.

    The evidence's own declared quality metadata is read off the governed structure -- it is not
    computed here and it is not assumed. A structure that declares nothing is UNASSESSED-by-
    absence in every dimension, which the gate treats as ineligible rather than as clean.
    """
    q = structure.get("qualification") if isinstance(structure.get("qualification"), dict) else {}
    ev = QualifiedEvidence(
        evidence_id=str(structure.get("evidence_id") or f"{module_id}-structure"),
        source_id=structure.get("source"), source_type=structure.get("source_type"),
        source_document_id=structure.get("source_document_id"),
        period=structure.get("period"), effective_date=structure.get("effective_date"),
        _raw_value=structure,
        required_inputs=tuple(q.get("required_inputs", ()) or ()),
        missing_fields=tuple(q.get("missing_fields", ()) or ()),
        invalid_fields=tuple(q.get("invalid_fields", ()) or ()),
        critical_missing=tuple(q.get("critical_missing", ()) or ()),
        timeliness_status=q.get("timeliness_status", UNASSESSED),
        provenance_trace=tuple(q.get("provenance_trace", ()) or ()),
        verification_status=q.get("verification_status"),
        source_authority=q.get("source_authority"),
        reliability_rubric_version=q.get("reliability_rubric_version"),
        reliability_weight=q.get("reliability_weight"),
        required_audit_elements=tuple(q.get("required_audit_elements", ()) or ()),
        missing_audit_elements=tuple(q.get("missing_audit_elements", ()) or ()),
        critical_audit_missing=tuple(q.get("critical_audit_missing", ()) or ()),
        package_missing_domains=tuple(q.get("package_missing_domains", ()) or ()),
        material_conflicts=tuple(q.get("material_conflicts", ()) or ()),
    )
    status = lineage_status(module_id, applicable=True)
    ev.lineage_status = status
    ev.independence_established = independence_established(status)
    ev.evidence_body = evidence_body_of(module_id, status)
    use = MODULE_USE[module_id]
    return assess(ev, uses=(use,), use_requirements=USE_REQUIREMENTS)


def _lineage_block(module_id: str, ev: QualifiedEvidence) -> dict[str, Any]:
    """The row's lineage state, derived from the shipped declaration table (Run 30 closure)."""
    return {
        "lineage_status": ev.lineage_status,
        "independence_established": ev.independence_established,
        "evidence_body": ev.evidence_body,
        "qualification": SIGNAL_QUALIFICATION,
        "unresolved_note": (
            "no body of evidence has been established for this reading: what its assessors "
            "themselves read is not known to this platform. That is not independence, and "
            "nothing may corroborate through it"
            if ev.lineage_status == "LINEAGE_UNRESOLVED" else None),
    }


def _qualification_block(ev: QualifiedEvidence, use: str) -> dict[str, Any]:
    return {
        "evidence_id": ev.evidence_id,
        "requested_use": use,
        "qualification_state": ev.qualification_state,
        "eligible_for_use": ev.eligible_for(use),
        "qualification_reasons": list(ev.qualification_reasons),
        "qualification_rule_version": QUALIFICATION_RULE_VERSION,
        "missing_fields": list(ev.missing_fields),
        "invalid_fields": list(ev.invalid_fields),
        "critical_missing": list(ev.critical_missing),
        "material_conflicts": [dict(c) for c in ev.material_conflicts],
        "timeliness_status": ev.timeliness_status,
    }


def _abstain(module_id: str, method_class: str, sentence: str, disposition: str,
             extra: dict[str, Any] | None = None) -> dict[str, Any]:
    out = {
        "abstention_reason_code": ABSTAIN_STRUCTURE_ABSENT,
        "method_class": method_class,
        "status_color": None,
        "insufficient_data": True,
        "result_source": RESULT_SOURCE,
        "canonical_disposition": disposition,
        "canonical_structure": V6_STRUCTURE_KEYS.get(module_id),
        "evidence_metric": sentence,
    }
    if module_id.startswith("C1."):
        out["category_9_metadata_only"] = True
        out["voting_eligible"] = False
    if extra:
        out.update(extra)
    return out


def _assemble(si: dict, module_id: str) -> dict | None:
    """
    CORPUS-TO-STRUCTURE ASSEMBLY, for the structures the controlled corpus can genuinely build.

    THIS IS THE ORPHAN-FIELD CLOSURE AND IT IS DELIBERATELY NARROW. Run 27 found three document
    families emitting fields no registered module consumed. Assembly here turns those already
    extracted, already assembled signal fields into the governed structure the canonical module
    is defined on. It fabricates nothing: a quantity the corpus does not carry does not appear,
    and where the defining structure cannot be built the module abstains rather than receiving a
    partial structure that would let it compute from an invented denominator.

    A6.2 SAFETY. The corpus carries `oshaRecordableIncidents` (Run 31 stopped discarding it),
    `totalManhours` and `oshaIncidentRate`. The canonical module is given the TWO DEFINING
    QUANTITIES and computes the identity itself. The document-stated rate is carried separately
    as `document_stated_incident_rate` and is NEVER used as the incidence rate, because executing
    the upstream branch proved a stated rate is emitted as-is and is not checked against the
    identity: a document asserting 99.9 beside a 3-cases/200,000-hours pair emits 99.9. A stated
    rate is a document's claim; the identity is a measurement.

    A6.1 QUALITY. The corpus carries `qualityAuditScore`, `totalFindings` and `criticalFindings`.
    NONE of those is a requirement register: a findings count is not an applicable-requirement
    population, and an audit score is not the ratio of satisfied applicable assessed requirements
    to assessed applicable requirements. Section 13 of the Run-31 contract forbids substituting a
    summary for a denominator, so this assembly carries the real evidence onto the structure as
    `recorded_audit_evidence` and supplies NO `requirements` list. The canonical module therefore
    abstains from the rate and the extracted evidence is preserved rather than discarded.

    WHAT IS DELIBERATELY NOT ASSEMBLED. `qualityDeficienciesNoted`, `safetyIncidentsDiscussed`
    and `environmentalIssuesDiscussed` are meeting-minute MENTIONS. They are evidence candidates
    and nothing here converts one into a denominator, an incidence numerator or a compliance
    percentage. A6.1's old prerequisite on `qualityDeficienciesNoted` is gone entirely: a project
    holding a real Quality Audit Report is no longer refused because nobody mentioned deficiencies
    in the minutes.
    """
    if module_id == "A6.2":
        cases = si.get("oshaRecordableIncidents")
        hours = si.get("totalManhours")
        stated = si.get("oshaIncidentRate")
        if cases is None and hours is None and stated is None:
            return None
        rec: dict[str, Any] = {
            "evidence_id": "A6.2-corpus",
            "reporting_period": si.get("reportPeriod"),
            "provenance": "assembled from the project's Safety Report extraction",
            "document_stated_incident_rate": stated,
            "leading_indicators": [],
        }
        if cases is not None:
            rec["recordable_cases"] = cases
        if hours is not None:
            rec["employee_hours_worked"] = hours
        return rec
    if module_id == "A6.3":
        # ENVIRONMENTAL, COMPLETING WHAT PASS 1 LEFT PARTIAL. Mechanical inspection of the
        # Environmental Compliance Report schema found FOUR extracted fields
        # (permit_conditions_total, violations, compliance_rate, report_date), of which only TWO
        # reach signal inputs: `environmentalComplianceRate` (a FRACTION, range-guarded at 1.0)
        # and `environmentalViolations`. `permit_conditions_total` is emitted nowhere.
        #
        # NONE OF THEM IS DEFINING EVIDENCE FOR THE CANONICAL RATE, and the reason is the same
        # one Pass 1 gave: a stated rate is a summary, a violations count is a count, and a
        # permit-conditions total gives no assessed or satisfied split. More decisively, the
        # corpus carries NO jurisdiction, NO permitting authority and NO permit identity
        # anywhere, and section 15 requires applicability to be determined BEFORE conformance is
        # assessed. EPA CGP is never assumed to apply.
        #
        # So the real evidence is preserved and the module returns
        # APPLICABILITY_NOT_ESTABLISHED. Nothing is converted into a compliance percentage.
        rate = si.get("environmentalComplianceRate")
        viol = si.get("environmentalViolations")
        if rate is None and viol is None:
            return None
        return {
            "evidence_id": "A6.3-corpus",
            "provenance": "assembled from the project's Environmental Compliance Report "
                          "extraction",
            # Deliberately absent: jurisdiction, permitting_authority, permit_id. The corpus
            # does not carry them, and inventing any one of them would be inventing regulatory
            # applicability.
            "recorded_environmental_evidence": {
                "document_stated_compliance_rate": rate,
                "reported_violations": viol,
            },
        }
    if module_id == "A6.4":
        # ============================ RUN 101. THE GAP WAS ONE ASSEMBLER, NOT A MISSING TYPE.
        # Run 96 recorded that A6.4 reads a governed assessment record NO DOCUMENT TYPE
        # PRODUCES. That was measured again at this head and it is HALF TRUE: no assembler
        # built the record, but `past_performance_report` IS a live document type and
        # `extraction_merge._NUMERIC_EMISSIONS` has emitted its four CPARS-shaped ratings --
        # overall, schedule, cost, quality -- to signal inputs all along, where NO MODULE READ
        # THEM. They were orphan fields, which is precisely what this assembly function exists
        # to close. No new document type is created here and none is needed.
        #
        # THE RECORD IS NEVER LABELLED CPARS BY THIS ASSEMBLY.
        # `canonical_v6.contractor_assessment` derives `is_official_cpars_record` from the
        # source system AND an official assessment id, and section 16 forbids labelling an
        # internal project score as an official past-performance rating. So the source system
        # is passed through EXACTLY as the document stated it and is never asserted here. A
        # document that did not say CPARS produces an INTERNAL assessment, correctly labelled.
        #
        # THE FACTOR RATINGS ARE THE DOCUMENT'S OWN WORDS. Nothing is normalised, mapped or
        # scored here; the band mapping happens once, in `_band_contractor`, against the five
        # ratings the CPARS guidance defines.
        _factors = [("Quality", si.get("qualityRating")),
                    ("Schedule", si.get("scheduleRating")),
                    ("Cost", si.get("costRating")),
                    ("Overall", si.get("overallRating"))]
        rows = [{"factor": name, "rating": str(value).strip()}
                for name, value in _factors if value is not None and str(value).strip()]
        if not rows:
            return None
        return {
            "evidence_id": "A6.4-corpus",
            "provenance": "assembled from the project's Past Performance Report extraction",
            "source_system": si.get("pastPerformanceSourceSystem"),
            "assessment_id": si.get("pastPerformanceAssessmentId"),
            "contract_id": si.get("pastPerformanceContractId"),
            "assessment_period": si.get("reportPeriod"),
            "data_origin": "document extraction",
            "factor_ratings": rows,
        }
    if module_id == "A6.1":
        score = si.get("qualityAuditScore")
        findings = si.get("totalFindings")
        critical = si.get("criticalFindings")
        if score is None and findings is None and critical is None:
            return None
        return {
            "evidence_id": "A6.1-corpus",
            "register_id": None,
            "provenance": "assembled from the project's Quality Audit Report extraction",
            # NO `requirements` KEY. See the docstring: none of these establishes an applicable,
            # assessed and satisfied requirement population, so no rate is computable and none is
            # estimated. The evidence is preserved for the reader instead of being discarded.
            "recorded_audit_evidence": {
                "quality_audit_score": score,
                "total_findings": findings,
                "critical_findings": critical,
            },
        }
    return None


# =============================================================================================
# RUN 101 -- THE BANDS FOR A6, AND THE THREE THAT ARE NOT BANDS
#
# THE OWNER'S RULING, SECTION 2: a module may assert a band only when a threshold exists whose
# QUANTITY, DENOMINATOR, TIME BASIS and DIRECTION OF FAVOURABILITY match what it computes. This
# function is the ONLY place in this file a colour is decided, it decides it from the canonical
# result the module already produced, and it returns the boundary and the basis with it so the
# two cannot be stored apart. Where no matching threshold exists it returns a REASON instead of
# a colour, and `_route` stores the reason on the row.
#
# NOTHING HERE COMPUTES A FIGURE. Every quantity read below was produced by `canonical_v6`.
# =============================================================================================


def _a6_band(module_id: str, result: dict[str, Any], structure: Mapping[str, Any]) -> tuple:
    """
    Returns (status_color, boundary, basis, provenance_class) when a band is asserted, or
    (None, None, reason, None) when it is withheld. Never invents a figure.
    """
    if module_id == "A6.1":
        out = _band_quality_compliance(result, structure)
    elif module_id == "A6.2":
        out = _band_safety(result, structure)
    elif module_id == "A6.3":
        out = _band_environmental(result, structure)
    elif module_id == "A6.4":
        out = _band_contractor(result)
    else:
        # C1.5 and anything else: Category 9 is metadata and casts no vote (section 34).
        out = (None, None, None, None)
    # THE FIFTH ENTRY IS THE BOUNDARY'S OWN PROVENANCE CLASS, and it is optional at the call
    # site: a module whose basis and boundaries come from the same place returns four and both
    # classes are written the same. Only A6.2 differs today, and it differs because the research
    # says it must.
    return out if len(out) == 5 else (out + (None,))


def _band_quality_compliance(result: dict[str, Any], structure: Mapping[str, Any]) -> tuple:
    """
    A6.1. NO BAND UNLESS THE PROJECT SUPPLIES ONE -- the owner's ruling, section 3.5.

    THE PUBLISHED REWORK BENCHMARKS MEASURE REWORK COST AS A PROPORTION OF CONTRACT VALUE. That
    is a different quantity from this one, with a different denominator (money, not requirements)
    and a different direction, and section 2 forbids substituting it. It is not applied here and
    must never be.

    THE ONE THING THAT DOES BAND THIS is an acceptance target the PROJECT'S OWN DOCUMENTS state
    -- a quality plan, an inspection and test plan, a specification or a contract saying, for
    example, that acceptance shall be at least ninety-five per cent. When the register carries
    one, THAT figure is the threshold and ITS source is the document. When it does not, the rate
    is displayed and no band is asserted.

    AND THE TARGET MUST BE STATED FOR THIS QUANTITY. `acceptance_target_quantity` records what
    the document's target was stated over. A target stated for something else is a threshold from
    a related but different measure, which is the exact defect section 2 names, so it is refused
    rather than applied.
    """
    rate = result.get("quality_compliance_rate")
    if rate is None:
        return (None, None,
                "no compliance rate was measurable from the evidence supplied, so there is no "
                "figure for a threshold to be applied to", None)
    # THE TARGET IS THE DOCUMENT'S, READ OFF THE PROJECT'S OWN REGISTER. Nothing here supplies
    # one and nothing here defaults.
    target = structure.get("acceptance_target")
    source = structure.get("acceptance_target_source")
    quantity = structure.get("acceptance_target_quantity")
    if not isinstance(target, (int, float)) or not 0 < target <= 1 or not source:
        return (None, None,
                "no acceptance target for this quantity is stated by any document this project "
                "has uploaded. The published rework benchmarks measure rework cost as a "
                "proportion of contract value, which is a different quantity with a different "
                "denominator, and applying them here would be substituting a threshold from a "
                "related but different measure. The rate is reported and no band is asserted",
                None)
    if quantity and str(quantity).strip() not in ("quality_compliance",
                                                  "requirement_conformance_rate"):
        return (None, None,
                f"the acceptance target this project's documents state was stated over "
                f"{quantity!r}, which is not the quantity this module computes, so it is not "
                f"applied to it", None)
    # THE PROJECT'S OWN TARGET IS THE BOUNDARY, AND IT IS INCLUSIVE ON ITS LOWER SIDE: a rate AT
    # the stated target meets it. Only two bands are defensible from one stated figure -- met or
    # not met -- and no intermediate ladder is invented between them.
    colour = "Green" if rate >= target else "Red"
    return (colour,
            f"a conformance rate at or above the project's own stated acceptance target of "
            f"{target} is Green; below it is Red. The document states one figure, so two bands "
            f"are what it supports; no intermediate ladder is drawn between them",
            f"the project's own uploaded document: {source}",
            "CODIFIED")


def _band_safety(result: dict[str, Any], structure: Mapping[str, Any]) -> tuple:
    """
    A6.2. THE REBUILD, AND WHY ONLY ONE OF THE THREE LEGS CAN BAND TODAY.

    THE THREE MEASURES ARE REPORTED SEPARATELY AND ARE NEVER COMPOSITED (section 12.1d). Where
    one band must front the category the rule is WORST-OF and this function says so on the row.

    FREQUENCY. Bands against the published construction industry average, which section 12.3
    requires to be CONFIGURED DATA carrying its year and source and forbids as a literal in code.
    `band_reference_data.json` holds the entry and it is NOT CONFIGURED: no industry average was
    supplied with the Run 101 order, and the research report the order names as its authority was
    not present. So the rate is computed, reported on both the OSHA 200,000-hour and the ILO
    1,000,000-hour bases, and NO BAND is asserted. Inventing a number here is section 12.2.

    SEVERITY. No threshold for a severity rate was supplied at all, so none is applied.

    NEAR-MISS. THE INTERPRETATION IS INVERTED AND GETTING IT BACKWARDS IS RUN-FAILING (12.1c). A
    high reporting rate indicates a healthy reporting culture. No published expected near-miss
    rate exists for construction, so no ladder is drawn over the count. The ONE band the order
    states in terms is the near-zero one: near-zero reporting on an ACTIVE project is a concern,
    not a Green, and that is the only near-miss band asserted.

    THE EXPOSURE FLOOR. Beneath the configured floor a rate swings entirely on whether one event
    happened, so nothing bands beneath it.
    """
    floor = _BR.configured_value("safety_exposure_floor_hours")
    hours = result.get("employee_hours_worked")
    near = structure.get("near_miss_reported")
    active = bool(isinstance(hours, (int, float)) and hours > 0)
    if isinstance(hours, (int, float)) and floor and hours < floor:
        return (None, None,
                f"exposure for this period is {hours} employee hours, beneath the configured "
                f"floor of {floor}. Beneath it a rate turns entirely on whether a single event "
                f"happened, so no rate is banded and none is published as though it were "
                f"stable", None)
    # ---------------------------------------------- THE FREQUENCY LEG BANDS AGAINST THE ANCHOR
    # RUN 101, MID-RUN. THE RESEARCH REPORTS ARRIVED AND SUPPLIED THE INDUSTRY AVERAGE THE ORDER
    # REFERS TO: the US Bureau of Labor Statistics Survey of Occupational Injuries and Illnesses,
    # construction NAICS 23, 2023, total recordable case rate about 2.4 per 100 full-time
    # equivalent workers -- which is the SAME QUANTITY as per 200,000 employee hours, so it lands
    # on the OSHA base this module already computes with no conversion.
    #
    # IT IS CONFIGURED DATA, NEVER A LITERAL HERE (section 12.3), and it is stored UNVERIFIED
    # because both research reports flag it [Confirm] and state that primary-source verification
    # was not completed.
    #
    # THE ANCHOR AND THE CUTOFFS HAVE DIFFERENT PROVENANCE, AND THIS IS THE MODULE THAT FORCED
    # THE DISTINCTION. RESEARCH_2, recommendation 2: "State that ONLY THE INDUSTRY-AVERAGE ANCHOR
    # IS SOURCED; intermediate cutoffs are platform-chosen with no published basis." So the basis
    # class is CODIFIED, the boundary class is OWNER-CALIBRATED, and the reading carries both.
    _anchor = _BR.configured_value("construction_industry_recordable_rate")
    _cuts = _BR.entry("construction_frequency_band_cutoffs")
    _rate = (result.get("frequency") or {}).get("recordable_rate_osha_200k")
    if _anchor and _cuts.get("configured") and isinstance(_rate, (int, float)):
        _green, _yellow, _red = (_cuts["green_below"], _cuts["yellow_at_or_below"],
                                 _cuts["red_at_or_above"])
        colour = ("Green" if _rate < _green else "Yellow" if _rate <= _yellow
                  else "Amber" if _rate < _red else "Red")
        return (colour,
                f"on the recordable case rate per 200,000 employee hours, against the published "
                f"construction industry average of {_anchor}: below {_green} -- about half the "
                f"average -- is Green; at or above {_green} and AT OR BELOW the average "
                f"{_yellow} is Yellow; above the average and below {_red} is Amber; at or above "
                f"{_red} -- about twice the average -- is Red. THE ANCHOR IS PUBLISHED; THESE "
                f"THREE CUTOFFS ARE NOT. Zero is a value and is not treated as missing, but a "
                f"zero recordable count never produces a favourable system claim: severity and "
                f"near-miss are reported separately and are never combined with this measure",
                f"THE ANCHOR: {_BR.source_of('construction_industry_recordable_rate')}. IT IS "
                f"STORED UNVERIFIED -- both research reports flag the value [Confirm] and state "
                f"that primary-source verification against the BLS publication and the current "
                f"year was not completed. THE THREE CUTOFFS have no published basis at all: "
                f"{_cuts.get('why_not_codified')}",
                "CODIFIED",
                "OWNER-CALIBRATED")
    if isinstance(near, (int, float)) and active:
        if near <= 0:
            return ("Amber",
                    "zero near-misses reported on a project with recorded exposure hours above "
                    "the floor is Amber. A HIGH reporting rate is the healthy state: it "
                    "indicates a working reporting culture, and a low or zero rate on an active "
                    "project indicates under-reporting rather than safety. Zero is a value here "
                    "and is not treated as missing",
                    "the owner's Run 101 order, section 3.6. No published expected near-miss "
                    "rate exists for construction, so no ladder is drawn over the count and "
                    "only the near-zero condition the order states in terms is banded",
                    "OWNER-CALIBRATED")
        return (None, None,
                f"{near} near-misses were reported on an active project, which is the healthy "
                f"direction. No published expected near-miss rate exists for construction, so "
                f"reporting activity above zero is displayed and no ladder is drawn over the "
                f"count", None)
    unconfigured = _BR.entry("construction_industry_recordable_rate")
    return (None, None,
            "the frequency rate is reported on both the OSHA 200,000-hour and the ILO "
            "1,000,000-hour bases and is not banded: " + str(unconfigured.get("why_absent")) +
            " No threshold for a severity rate was supplied, so none is applied, and no "
            "published expected near-miss rate exists for construction. The three measures are "
            "reported separately and are never combined into one index",
            None)


def _band_environmental(result: dict[str, Any], structure: Mapping[str, Any]) -> tuple:
    """
    A6.3. THE CONSEQUENCE LADDER -- severity and consequence, not a closure rate.

    THE OWNER'S RULING, SECTION 3.7: any violation goes Red outright. NO PUBLISHED CLOSURE-RATE
    BENCHMARK EXISTS, and the old rate -- satisfied over assessed -- is not what bands. What is
    codified is the EPA Construction General Permit's corrective-action deadline: generally
    before the next storm event, no later than seven calendar days from discovery.

    THE CGP'S OWN DISTINCTION GOVERNS, and it is the whole ladder:
        an OPEN-BUT-WITHIN-DEADLINE corrective action is a DEFICIENCY;
        a MISSED DEADLINE or an UNAUTHORISED DISCHARGE is a VIOLATION.

    THE ORDERING IS DERIVED FROM STATUTORY CONSEQUENCE, NOT PUBLISHED AS A TAXONOMY. A
    stop-work order, an unauthorised discharge, a permit suspension, criminal exposure, a
    debarment trigger and a missed corrective-action deadline are each a consequence the statute
    attaches; a notice of violation, an administrative order or a monetary penalty is an
    enforcement action short of those; an open action still inside its deadline is neither. That
    ordering is what the ladder ranks, and this specification says so rather than claiming a
    published severity taxonomy exists.
    """
    findings = structure.get("environmental_findings")
    if not isinstance(findings, list):
        return (None, None,
                "the environmental evidence supplied for this project states no severity and no "
                "enforcement consequence for any finding, so the consequence ladder has nothing "
                "to rank. A closure rate is not what bands here: no published closure-rate "
                "benchmark exists, and the order rules that severity and consequence are the "
                "measure", None)
    red, amber, yellow = [], [], []
    for f in findings:
        if not isinstance(f, dict):
            continue
        sev = str(f.get("severity") or "").strip().lower()
        if sev in _ENV_RED:
            red.append(f)
        elif sev in _ENV_AMBER:
            amber.append(f)
        elif sev in _ENV_YELLOW:
            yellow.append(f)
    boundary = (
        "Red -- ANY confirmed violation: a stop-work or cease-and-desist order, an unauthorised "
        "discharge, a permit suspension or revocation, criminal exposure, a debarment trigger, "
        "or a MISSED corrective-action deadline. Amber -- a notice of violation, an "
        "administrative order, or a monetary penalty issued. Yellow -- an open corrective action "
        "STILL WITHIN its deadline, or a documentation deficiency. Green -- in compliance, with "
        "corrective actions closed within the deadline. The ladder is worst-wins: one Red "
        "finding is Red however many findings are closed, because a violation does not average "
        "away")
    basis = (
        "the owner's Run 101 order, section 3.7. What is CODIFIED is the EPA Construction "
        "General Permit's corrective-action deadline -- generally before the next storm event, "
        "no later than seven calendar days from discovery -- and its inspection frequency, and "
        "it is the CGP's own distinction between an open-but-within-deadline corrective action "
        "(a deficiency) and a missed deadline or unauthorised discharge (a violation) that "
        "separates Yellow from Red. The ORDERING of the four rungs is derived from statutory "
        "consequence and is not published as a severity taxonomy; the order records it as a "
        "derivation and so does this specification")
    if red:
        return ("Red", boundary, basis, "CODIFIED")
    if amber:
        return ("Amber", boundary, basis, "CODIFIED")
    if yellow:
        return ("Yellow", boundary, basis, "CODIFIED")
    if findings:
        return ("Green", boundary, basis, "CODIFIED")
    return (None, None,
            "the environmental record for this project lists no findings at all. An empty list "
            "is not the same statement as 'in compliance, corrective actions closed within the "
            "deadline', and it is not read as one", None)


#: The severity words each rung of the consequence ladder recognises. A finding whose severity is
#: none of these falls into NO rung and is reported unranked rather than dropped to the nearest
#: one: section 3, boundary rule 2. The words are the order's own.
_ENV_RED: frozenset = frozenset({
    "stop_work", "cease_and_desist", "unauthorised_discharge", "unauthorized_discharge",
    "permit_suspension", "permit_revocation", "criminal_exposure", "debarment_trigger",
    "missed_corrective_action_deadline", "violation",
})
_ENV_AMBER: frozenset = frozenset({
    "notice_of_violation", "administrative_order", "monetary_penalty",
})
_ENV_YELLOW: frozenset = frozenset({
    "open_corrective_action_within_deadline", "documentation_deficiency", "deficiency",
})


#: THE FIVE FEDERAL CPARS RATINGS ONTO FOUR BANDS. Section 3.8, and the collapse is recorded as
#: the DESIGN CHOICE it is: five ordinal levels do not divide evenly into four, and Exceptional
#: and Very Good are the pair joined because both are above the satisfactory level the guidance
#: defines as meeting contract requirements. Nothing else was merged.
_CPARS_BANDS: dict[str, str] = {
    "exceptional": "Green",
    "very good": "Green",
    "satisfactory": "Yellow",
    "marginal": "Amber",
    "unsatisfactory": "Red",
}


def _band_contractor(result: dict[str, Any]) -> tuple:
    """
    A6.4. THE CPARS MAPPING. CODIFIED -- the five ratings are defined in the CPARS guidance and
    referenced by FAR Subpart 42.15, as the owner's Run 101 order states.

    THE COLLAPSE OF FIVE ORDINAL LEVELS INTO FOUR IS A DESIGN CHOICE AND IS RECORDED AS ONE. The
    ratings themselves are codified; the decision to join Exceptional and Very Good into one band
    is not, and the boundary text says so wherever it is printed.

    WORST-OF ACROSS THE FACTORS, not an average. `canonical_v6.contractor_assessment` refuses to
    aggregate factor ratings without a governed aggregation policy and that refusal stands: no
    averaged rating is produced here either. What is banded is the worst factor rating present,
    because a marginal schedule rating is not cancelled by an exceptional cost one.
    """
    rows = result.get("factor_ratings")
    if not isinstance(rows, list) or not rows:
        return (None, None,
                "no governed contractor assessment with factor ratings is recorded for this "
                "project, so there is no rating to map", None)
    # THE RATING MAY ARRIVE AS THE DOCUMENT'S WORD OR AS ITS NUMBER ON THE SHIPPED FIVE-POINT
    # SCALE, and both resolve to the SAME word through `extraction_merge.CPARS_RATING_SCALE` --
    # the one authority for that scale, inverted here rather than transcribed. A rating that is
    # neither one of the five words nor one of the five numbers resolves to nothing and falls
    # into no band, which section 3 boundary rule 2 requires.
    seen = [_cpars_word(r.get("rating")) for r in rows if isinstance(r, dict)]
    mapped = [(_CPARS_BANDS[s], s) for s in seen if s in _CPARS_BANDS]
    unmapped = sorted({s for s in seen if s and s not in _CPARS_BANDS})
    if not mapped:
        return (None, None,
                f"none of the ratings recorded for this project is one of the five CPARS "
                f"ratings the mapping is defined over (recorded: {unmapped}), so no band is "
                f"asserted and none falls to a nearest rating", None)
    worst = max(mapped, key=lambda p: _CPARS_SEVERITY[p[0]])
    return (worst[0],
            "Exceptional and Very Good map to Green; Satisfactory to Yellow; Marginal to Amber; "
            "Unsatisfactory to Red. Where several factors are rated the WORST rating bands, "
            "because a marginal factor is not cancelled by an exceptional one and no governed "
            "policy for averaging factor ratings is supplied. Collapsing five ordinal levels "
            "into four bands is a DESIGN CHOICE, not a published mapping: Exceptional and Very "
            "Good are joined because both stand above the Satisfactory level the guidance "
            "defines as meeting contract requirements",
            "the owner's Run 101 order, section 3.8: the five ratings are defined in the CPARS "
            "guidance and referenced by FAR Subpart 42.15",
            "CODIFIED")


_CPARS_SEVERITY: dict[str, int] = {"Green": 0, "Yellow": 1, "Amber": 2, "Red": 3}


def _cpars_word(value: Any) -> str:
    """
    One rating, as its CPARS word in lower case, or "" when it is not one of the five.

    DERIVED FROM THE SHIPPED SCALE, NEVER TRANSCRIBED BESIDE IT. `extraction_merge` coerces the
    five adjectives a past performance evaluation prints into the five-point scale A6.4 reads, so
    a rating reaches this function as either the word or its number depending on which path
    assembled the record. Inverting the shipped dictionary is what keeps one authority for the
    scale; writing the numbers out here again would be a second copy to drift.
    """
    from ..extraction_merge import CPARS_RATING_SCALE
    if isinstance(value, str):
        word = " ".join(value.strip().lower().split())
        if word in CPARS_RATING_SCALE:
            return word
        try:
            number = float(word)
        except ValueError:
            return ""
    elif isinstance(value, (int, float)):
        number = float(value)
    else:
        return ""
    for word, n in CPARS_RATING_SCALE.items():
        if n == number:
            return word
    return ""


def _route(module_id: str, method_class: str, fn: Callable[[dict], dict[str, Any]],
           *, gated: bool) -> Callable:
    """
    Build ONE runner. `gated` says whether this module's route must pass Category-9 qualification
    before its canonical function is reached -- true for all of Category 8 (section 37), false
    for Category 9 itself, which IS the assessment and would otherwise be circular.
    """

    def run(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
        try:
            structure = v6_structure(si, module_id)
        except StructureAbsent as exc:
            # THE CORPUS MAY BE ABLE TO BUILD IT even when no governed structure was supplied
            # through the intake. `_assemble` returns the structure the project's own extracted
            # evidence supports, or None when it supports none.
            structure = _assemble(si, module_id)
            if structure is None:
                return _abstain(module_id, method_class, exc.sentence,
                                DISPOSITION_STRUCTURE_ABSENT)
        use = MODULE_USE[module_id]
        ev = _qualify(module_id, structure)
        qual = _qualification_block(ev, use)
        if gated and not ev.eligible_for(use):
            return _abstain(
                module_id, method_class,
                ("The evidence supplied for this measure has not been qualified for governance "
                 "use, so no governed result is produced from it and no figure is used in its "
                 "place."),
                DISPOSITION_UNQUALIFIED,
                {"qualification": qual, "lineage": _lineage_block(module_id, ev)})
        try:
            result = fn(structure)
        except StructureAbsent as exc:
            return _abstain(module_id, method_class, exc.sentence,
                            DISPOSITION_STRUCTURE_ABSENT, {"qualification": qual})
        except ABMStructureError as exc:
            return _abstain(module_id, method_class, str(exc),
                            DISPOSITION_STRUCTURE_ABSENT, {"qualification": qual})
        row: dict[str, Any] = {
            "method_class": method_class,
            "status_color": None,
            "band_asserted": False,
            "calibration_pending": True,
            "result_source": RESULT_SOURCE,
            "canonical_disposition": DISPOSITION_COMPUTED,
            "canonical_structure": V6_STRUCTURE_KEYS[module_id],
            "qualification": qual,
            "lineage": _lineage_block(module_id, ev),
        }
        row.update(result)
        row["status_color"] = None          # re-asserted after the update; no band is invented
        # ------------------------------------------------------ RUN 101, THE BAND, OR THE REASON
        # THE COLOUR IS DECIDED IN ONE PLACE, `_a6_band`, FROM THE CANONICAL RESULT ALREADY
        # PRODUCED ABOVE. No arithmetic happens here and none happens there. Where a matching
        # threshold exists the band travels with the boundary it crossed and that boundary's
        # basis and provenance class -- section 3 requires the source to be STORED, not only
        # written in prose, and `computed_results.module_results` is a JSON blob, so these keys
        # need no column and no migration. Where no matching threshold exists the REASON is
        # stored on the row instead and the row stays bandless, which section 2 makes a correct
        # outcome rather than a failure.
        _colour, _boundary, _basis, _prov, _bprov = _a6_band(module_id, result, structure)
        _bprov = _bprov or _prov
        if _colour is not None:
            row["status_color"] = _colour
            row["band_asserted"] = True
            row["calibration_pending"] = False
            row["band_boundary"] = _boundary
            row["band_basis"] = _basis
            row["band_provenance_class"] = _prov
            row["band_provenance_words"] = PROVENANCE_WORDS[_prov]
            row["band_basis_provenance_class"] = _prov
            row["band_boundary_provenance_class"] = _bprov
            row["band_boundary_provenance_words"] = PROVENANCE_WORDS[_bprov]
            if _bprov != _prov:
                row["band_provenance_split_note"] = (
                    "the BASIS -- the measure and the published anchor it is drawn against -- and "
                    "the BOUNDARIES -- the cutoffs that divide the bands -- come from different "
                    "places here, and this reading says so rather than presenting a "
                    "platform-chosen cutoff as though a standard fixed it")
            row.pop("calibration_note", None)
        elif _basis:
            row["band_withheld_reason"] = _basis
        if module_id.startswith("C1."):
            row["category_9_metadata_only"] = True
            row["voting_eligible"] = False
        row["evidence_metric"] = _sentence(module_id, result)
        return row

    run.__name__ = f"run_{module_id.replace('.', '_')}"
    return run


def _sentence(module_id: str, result: dict[str, Any]) -> str:
    """The reader's sentence. Never a legal claim; never a band."""
    if "statement" in result and result.get("statement"):
        return str(result["statement"])
    m = result.get("measure")
    if m == "missing_data_index":
        f = result.get("missing_fraction")
        return (f"{result.get('missing_count')} of {result.get('applicable_required_count')} "
                f"required fields for this use are missing"
                if f is not None else str(result.get("reason", "")))
    if m == "information_completeness":
        c = result.get("information_completeness")
        return (f"{result.get('present_and_usable')} of "
                f"{result.get('applicable_required_components')} required information "
                f"components are present and usable" if c is not None
                else str(result.get("reason", "")))
    if m == "data_timeliness":
        return (f"this evidence is {result.get('timeliness_status')} at "
                f"{result.get('age_days')} days against the governed "
                f"{result.get('allowed_age_days')}-day rule for this use"
                if result.get("age_days") is not None else str(result.get("reason", "")))
    if m == "reporting_frequency":
        return (f"{result.get('periods_received')} of {result.get('expected_periods')} "
                f"expected reporting periods were received, "
                f"{result.get('on_time_count')} of them on time")
    if m == "audit_trail_completeness":
        return (f"{result.get('present_applicable')} of {result.get('required_applicable')} "
                f"required audit elements are present")
    if m == "cross_document_consistency":
        return (f"{result.get('consistent_facts')} of {result.get('comparable_facts')} "
                f"comparable governed facts agree; "
                f"{len(result.get('material_conflicts', []))} material conflict(s) remain")
    if m == "source_reliability":
        return str(result.get("reason") or "source provenance recorded")
    if m == "safety_performance":
        # RUN 101. THREE MEASURES, REPORTED SEPARATELY IN THE READER'S SENTENCE TOO. A sentence
        # that named only the recordable rate is what made one rate look like the whole of
        # safety performance. Nothing is combined here and nothing is averaged.
        freq = result.get("frequency") or {}
        sev = result.get("severity") or {}
        near = result.get("near_miss") or {}
        parts: list[str] = []
        if freq.get("recordable_rate_osha_200k") is not None:
            parts.append(
                f"a recordable frequency rate of "
                f"{round(freq['recordable_rate_osha_200k'], 2)} per 200,000 employee hours, "
                f"which is {round(freq['recordable_rate_ilo_1m'], 2)} on the 1,000,000-hour "
                f"international base")
        else:
            parts.append(str(result.get("lagging_reason", "no exposure-normalised rate")))
        if sev.get("severity_rate_osha_200k") is not None:
            parts.append(
                f"a severity rate of {round(sev['severity_rate_osha_200k'], 1)} charged days "
                f"lost per 200,000 hours, averaging "
                f"{round(sev['mean_days_lost_per_lost_time_case'], 1)} days a lost-time case")
        else:
            parts.append("no severity rate: no days lost are stated for any case")
        if near.get("reported") is not None:
            parts.append(
                f"{near['reported']} near-misses reported"
                + (f", {near['closed']} closed" if near.get("closed") is not None else ""))
        else:
            parts.append("no near-miss reporting recorded")
        return ("; ".join(parts)
                + ". These are three separate measures and are not combined into one index")
    if m == "quality_compliance":
        r = result.get("quality_compliance_rate")
        return (f"{result.get('satisfied')} of {result.get('applicable_assessed')} assessed "
                f"applicable quality requirements are satisfied"
                if r is not None else str(result.get("reason", "")))
    if m == "environmental_compliance":
        r = result.get("environmental_compliance_rate")
        return (f"{result.get('satisfied')} of {result.get('applicable_assessed')} assessed "
                f"applicable environmental requirements are satisfied"
                if r is not None else str(result.get("reason", "")))
    if m == "contractor_assessment":
        return (f"{result.get('label')} recorded with "
                f"{len(result.get('factor_ratings', []))} factor rating(s)"
                if result.get("disposition") == "MEASURED" else str(result.get("reason", "")))
    if m == "abm_governance":
        return (f"the governance model ran to {result.get('terminal_state')} at t="
                f"{result.get('final_time')} under the configured authority matrix")
    if m == "modification_governance":
        return (f"{len(result.get('modification_results', []))} contract modification(s) "
                f"assessed for authority, type and documentation")
    if m == "a11_conformance":
        return ("configured A-11 rule subset evaluated: "
                + ", ".join(f"{k} {v}" for k, v in
                            sorted(result.get("configured_subset_result", {}).items())))
    return str(result.get("reason") or result.get("disposition") or "")


def _abm(structure: dict) -> dict[str, Any]:
    """8.1's canonical call. Eligibility is already established by the gate above."""
    return V6.abm_governance(structure, signal_eligible=True,
                             signal_abstaining=bool(structure.get("signal_abstaining")))


def _evms_reporting(structure: dict) -> dict[str, Any]:
    """
    8.4 reads 8.2's ANSWER, not its inputs (section 11). The applicability evidence rides on the
    reporting structure so the two are assessed from the same governed record.
    """
    applic = structure.get("applicability_evidence")
    applicability = (V6.evms_applicability(applic) if isinstance(applic, dict) else None)
    return V6.evms_reporting(structure, applicability)


#: THE ROUTE TABLE. `registry.VALIDATED` is repointed at these, and nothing else reaches the
#: Category-8/9 legacy implementations from a production run.
CAT89_CANONICAL: dict[str, tuple[str, Callable]] = {
    "A6.1": ("Quality_Compliance",
             _route("A6.1", "Quality_Compliance", V6.quality_compliance, gated=True)),
    "A6.2": ("Safety_Performance",
             _route("A6.2", "Safety_Performance", V6.safety_performance, gated=True)),
    "A6.3": ("Environmental_Compliance",
             _route("A6.3", "Environmental_Compliance", V6.environmental_compliance, gated=True)),
    "A6.4": ("Contractor_Performance",
             _route("A6.4", "Contractor_Performance", V6.contractor_assessment, gated=True)),
    "C1.5": ("Information_Completeness_Ratio",
             _route("C1.5", "Information_Completeness_Ratio", V6.information_completeness,
                    gated=False)),
}
