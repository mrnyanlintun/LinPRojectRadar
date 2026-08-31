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

from typing import Any, Callable

from . import canonical_v6 as V6
from .abm import ABMStructureError
from .canonical import StructureAbsent
from .canonical_v6 import V6_STRUCTURE_KEYS, V6_STRUCTURE_WORDS, v6_structure
from .lineage import evidence_body_of, independence_established, lineage_status
from .models import ABSTAIN_STRUCTURE_ABSENT
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
        r = result.get("incidence_rate")
        return (f"recordable incidence rate {r} per 200,000 employee hours"
                if r is not None else str(result.get("lagging_reason", "")))
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
