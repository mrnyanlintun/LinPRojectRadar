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
from .models import (
    ABSTAIN_STRUCTURE_ABSENT, PROVENANCE_WORDS,
    THRESHOLD_SOURCES, THRESHOLD_SOURCE_EXTERNAL, THRESHOLD_SOURCE_OWNER,
    THRESHOLD_SOURCE_PROJECT,
    THRESHOLD_SOURCE_WORDS,
)
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
    # RUN 113, ORDER SECTION 3. C1.5's USE, WHICH THIS FILE ALREADY DECLARED AND NOTHING CLAIMED.
    #
    # Run 109 measured `_route` raising `KeyError: 'C1.5'` here the moment a governed
    # `informationPackageRecord` was supplied. Run 111 proposed stopping the lookup on the
    # ground that an ungated route never uses the result. THAT READING IS HALF RIGHT AND THE
    # HALF IT MISSES IS THE DECIDING ONE. `use` is consumed TWICE, not once:
    #
    #   * `_qualification_block(ev, use)` -- which becomes `row["qualification"]`, so `use` is
    #     STORED on the ledger row as `requested_use` and `eligible_for_use`; and
    #   * `if gated and not ev.eligible_for(use)` -- the gate, which C1.5 is routed past.
    #
    # And `_qualify` (line 137) performs the SAME lookup independently, before the gate is ever
    # reached, so removing the line at the route would not stop the KeyError at all. Dropping
    # the use would mean inventing a null `requested_use` for a row that the four Category-8
    # rows all fill -- inventing an input, which section 1 forbids.
    #
    # `USE_REQUIREMENTS` below already carries "quality_assessment", with a comment naming
    # Category 9 and section 22's circularity, and NO MODULE NAMED IT. The vocabulary was
    # written for this module and left unclaimed. C1.5 claims it. It requires NOTHING of its
    # evidence -- an empty requirement set, not a relaxed one -- and the route stays
    # `gated=False`, so eligibility still blocks nothing; what changes is that the stored row
    # now names the use it was assessed for instead of the module crashing.
    "C1.5": "quality_assessment",
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
        # RUN 117, SECTION 4.1. THE ENFORCEMENT NOTICES THIS PERIOD SERVED.
        #
        # `_severe_safety_events` has read `structure["severe_events"]` since Run 102 and NOTHING
        # IN THE TREE EVER WROTE THAT KEY -- measured at this run's start head, not cited. The
        # owner's map says a stop-work order arrives on a correspondence notice, so
        # `documents._run69_structures` now reads one onto `safetySevereEvents` and this is where
        # it joins the record. The words are the notice's own: nothing here maps a severity word
        # onto the override vocabulary, and a word outside it matches nothing and is carried
        # unranked, which is the behaviour `_severe_safety_events` already had.
        #
        # A NOTICE ALONE IS ENOUGH TO BUILD THE RECORD. A project served a stop-work order and
        # holding no safety report still reaches the override; the frequency leg then has no
        # figures and bands nothing, which is correct and is not a reason to withhold the Red.
        severe = si.get("safetySevereEvents")
        severe = list(severe) if isinstance(severe, list) else []
        if cases is None and hours is None and stated is None and not severe:
            return None
        rec: dict[str, Any] = {
            "evidence_id": "A6.2-corpus",
            "reporting_period": si.get("reportPeriod"),
            "provenance": "assembled from the project's Safety Report extraction",
            "document_stated_incident_rate": stated,
            "leading_indicators": [],
            "severe_events": severe,
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
    #
    # RUN 102, SECTION 6. THE SIXTH ENTRY IS THE `threshold_source` -- which rung of the owner's
    # precedence order actually supplied the figure. It is REQUIRED whenever a colour is
    # returned; `_route` raises rather than store a band without it, which is section 12.5.
    out = out + (None,) * (6 - len(out))
    return out


def _band_quality_compliance(result: dict[str, Any], structure: Mapping[str, Any]) -> tuple:
    """
    A6.1. RUN 102, SECTION 4.1. THE MEASURE IS FIRST-PASS INSPECTION ACCEPTANCE.

        FirstPassAcceptance = items passing on FIRST inspection / items inspected

    WHAT CHANGED AND WHY. Run 101 measured that this module computed a REQUIREMENT CONFORMANCE
    RATE -- satisfied applicable assessed requirements over assessed applicable requirements --
    and banded on that. The owner's Run 102 table defines the measure as first-pass inspection
    acceptance, which is a different population with a different denominator. Section 12.3 fails
    the run for attaching a band to a quantity the module does not compute, so the module now
    COMPUTES the first-pass rate (`canonical_v6._first_pass_acceptance`) and the band is drawn
    over that. The conformance rate is still reported and is explicitly not what bands.

    THE REWORK-COST BENCHMARKS ARE NOT THE SOURCE FOR THESE BANDS AND ARE NOT CITED AS ONE. The
    owner states it in terms: the published research supports rework COST as a proportion of
    contract value, which is a different quantity with a different denominator and a different
    direction. Section 12.3 fails the run for citing them here. They are not applied.

    THE PRECEDENCE ORDER IS EXERCISED, NOT LABELLED. Where the project's own quality plan or
    inspection and test plan states an acceptance target for THIS quantity, that figure is the
    threshold and the threshold source is `project_specific` -- rung 1, and it overrides the
    owner's default because it is stricter authority, not because it is stricter arithmetic.
    Where it does not, the owner's configured 95/90/80 ladder applies at rung 3.

    THE CRITICAL OVERRIDE IS NONCOMPENSATORY AND OUTRANKS BOTH. A failed critical inspection,
    hold-point inspection, life-safety requirement, commissioning acceptance test or other
    explicitly designated critical quality item is Red however high the rate.
    """
    rate = result.get("first_pass_acceptance_rate")
    if rate is None:
        _conf = result.get("quality_compliance_rate")
        return (None, None,
                ("no first-pass inspection acceptance rate is measurable from the evidence "
                 "supplied. This module's measure is items passing on FIRST inspection divided "
                 "by items inspected, and an inspection record must state both figures for it. "
                 + ("A requirement conformance rate of "
                    f"{_conf} is reported and is NOT what this band is drawn over: it is a "
                    "different population with a different denominator. " if _conf is not None
                    else "")
                 + "The published rework-cost benchmarks measure rework cost as a proportion of "
                   "contract value, a different quantity again, and are not applied here"),
                None, None, None)
    # THE HARD OVERRIDE FIRST, because a critical failure cannot be averaged away by a rate.
    critical = result.get("critical_quality_failures") or []
    cuts = _BR.entry("quality_first_pass_acceptance_bands")
    target = structure.get("acceptance_target")
    source = structure.get("acceptance_target_source")
    quantity = str(structure.get("acceptance_target_quantity") or "").strip()
    project_target = (isinstance(target, (int, float)) and 0 < target <= 1 and bool(source)
                      and quantity in ("", "first_pass_acceptance",
                                       "first_pass_inspection_acceptance"))
    _override = (
        "HARD OVERRIDE, and it outranks every percentage band: Red if a critical inspection, "
        "hold-point inspection, life-safety requirement, commissioning acceptance test, or "
        "other explicitly designated critical quality item fails. A critical failure does not "
        "average away inside a high pass rate.")
    if project_target:
        boundary = (f"a first-pass acceptance rate at or above the project's own stated "
                    f"acceptance target of {target} is Green; below it is Red. The document "
                    f"states one figure, so two bands are what it supports and no intermediate "
                    f"ladder is drawn between them. {_override}")
        basis = (f"the project's own uploaded document: {source}. Rung 1 of the owner's "
                 f"precedence order -- a project-specific threshold overrides the owner's "
                 f"configured default")
        colour = "Red" if critical else ("Green" if rate >= target else "Red")
        return (colour, boundary, basis, "CODIFIED", None, THRESHOLD_SOURCE_PROJECT)
    if not cuts.get("configured"):
        return (None, None,
                "no acceptance threshold for first-pass inspection acceptance is configured and "
                "no project document states one, so the rate is displayed and no band is "
                "asserted", None, None, None)
    g, y, a = (cuts["green_at_or_above"], cuts["yellow_at_or_above"], cuts["amber_at_or_above"])
    colour = ("Red" if critical
              else "Green" if rate >= g else "Yellow" if rate >= y
              else "Amber" if rate >= a else "Red")
    boundary = (
        f"on first-pass inspection acceptance -- items passing on FIRST inspection divided by "
        f"items inspected: at or above {g} is Green; at or above {y} and below {g} is Yellow; "
        f"at or above {a} and below {y} is Amber; below {a} is Red. Each boundary is INCLUSIVE "
        f"ON ITS LOWER SIDE. {_override}")
    basis = (
        "the owner's Run 102 order, section 4.1, and the threshold table attached to it. "
        "OWNER-CONFIGURED: the owner states in terms that the collected research supports "
        "REWORK COST BENCHMARKS, not a universal first-pass inspection-rate threshold, and that "
        "rework ratios must NOT be cited as the source for these pass-rate bands. They are not "
        "cited here and are not applied. A project quality plan or inspection and test plan "
        "with a stricter requirement overrides these bands, and none is stated by any document "
        "this project has uploaded")
    return (colour, boundary, basis, "OWNER-CALIBRATED", None, THRESHOLD_SOURCE_OWNER)


def _band_safety(result: dict[str, Any], structure: Mapping[str, Any]) -> tuple:
    """
    A6.2. RUN 102, SECTION 4.2. FREQUENCY BANDS ON THE BENCHMARK RATIO.

        BenchmarkRatio = project TRIR / the applicable BLS construction TRIR

    WHAT CHANGED, AND WHAT DID NOT. Run 101's THREE MEASURES STAY -- frequency, severity and
    near-miss -- and they are still reported separately and are STILL NEVER COMPOSITED (section
    12.7). This changes only HOW FREQUENCY BANDS: Run 101 compared the rate to three absolute
    cutoffs derived from the benchmark; the owner now bands the RATIO of the rate to the
    benchmark, at 0.75, 1.00 and 1.50. The two forms are close but not identical -- the ratio
    form makes the benchmark ENTER THE ARITHMETIC rather than only the comparison -- and that is
    the owner's stated intent.

    THE BENCHMARK IS CONFIGURED DATA AND IS NEVER A LITERAL HERE (section 12.6). It is read from
    `band_reference_data.json` with its year, its unit and its source, and it is stored
    UNVERIFIED. Where it is not configured NOTHING BANDS: no default is supplied, because a
    default benchmark is an invented threshold.

    THE FORMULA AND THE BENCHMARK ARE CODIFIED; THE THREE MULTIPLIERS ARE OWNER-CONFIGURED, so
    the basis class and the boundary class differ and the reading carries both.

    TOTAL HOURS WORKED IS ALWAYS DISPLAYED BESIDE THE RATE -- the owner's reason is that small
    projects have volatile rates after a single recordable event -- and that is why the exposure
    floor stays: BENEATH THE FLOOR NOTHING BANDS (section 12.6).

    THE HARD OVERRIDE OUTRANKS THE RATIO. A fatality, a serious life-threatening event, a
    stop-work order or an unresolved high-severity safety violation is Red however low the rate.
    """
    floor = _BR.configured_value("safety_exposure_floor_hours")
    hours = result.get("employee_hours_worked")
    near = structure.get("near_miss_reported")
    active = bool(isinstance(hours, (int, float)) and hours > 0)
    _severe = _severe_safety_events(structure, result)
    _override = (
        "HARD OVERRIDE, and it outranks the ratio: Red for a fatality, a serious "
        "life-threatening event, a stop-work order, or an unresolved high-severity safety "
        "violation, however low the recordable rate.")
    if _severe:
        return ("Red",
                _override + " This project's safety record states " + _severe["what"] + ".",
                ("the owner's Run 102 order, section 4.2. The override is a consequence "
                 "condition, not a rate: no exposure-normalised frequency can make it not have "
                 "happened, so it is applied before the exposure floor and before the ratio"),
                "OWNER-CALIBRATED", None, THRESHOLD_SOURCE_OWNER)
    if isinstance(hours, (int, float)) and floor and hours < floor:
        return (None, None,
                f"exposure for this period is {hours} employee hours, beneath the configured "
                f"floor of {floor}. Beneath it a rate turns entirely on whether a single event "
                f"happened, so no rate is banded and none is published as though it were "
                f"stable. Total hours worked is displayed beside the rate for exactly this "
                f"reason", None, None, None)
    # ------------------------------------------- THE FREQUENCY LEG BANDS ON THE BENCHMARK RATIO
    _anchor = _BR.configured_value("construction_industry_recordable_rate")
    _cuts = _BR.entry("safety_benchmark_ratio_bands")
    _rate = (result.get("frequency") or {}).get("recordable_rate_osha_200k")
    if _anchor and _cuts.get("configured") and isinstance(_rate, (int, float)) and _anchor > 0:
        _ratio = _rate / float(_anchor)
        _g, _y, _a = (_cuts["green_at_or_below"], _cuts["yellow_at_or_below"],
                      _cuts["amber_at_or_below"])
        colour = ("Green" if _ratio <= _g else "Yellow" if _ratio <= _y
                  else "Amber" if _ratio <= _a else "Red")
        return (colour,
                f"on the BENCHMARK RATIO -- this project's recordable case rate per 200,000 "
                f"employee hours ({_rate}) divided by the applicable published construction "
                f"benchmark ({_anchor}), giving {round(_ratio, 4)}: at or below {_g} is Green; "
                f"above {_g} and at or below {_y} is Yellow; above {_y} and at or below {_a} is "
                f"Amber; above {_a} is Red. THE FORMULA AND THE BENCHMARK ARE CODIFIED; THESE "
                f"THREE MULTIPLIERS ARE THE OWNER'S. Total hours worked ({hours}) is displayed "
                f"beside the rate, and nothing bands beneath the configured exposure floor. "
                f"Zero is a value and is not treated as missing, but a zero recordable count "
                f"never produces a favourable system claim: severity and near-miss are reported "
                f"separately and are never combined with this measure. {_override}",
                f"THE FORMULA is the OSHA incidence-rate identity and the BENCHMARK is "
                f"{_BR.source_of('construction_industry_recordable_rate')}. IT IS STORED "
                f"UNVERIFIED -- both research reports flag the value [Confirm] and state that "
                f"primary-source verification against the BLS publication and the current year "
                f"was not completed. THE THREE MULTIPLIERS 0.75, 1.00 and 1.50 are the owner's "
                f"configured tolerance, stated in his Run 102 order section 4.2, and have no "
                f"published basis",
                "CODIFIED",
                "OWNER-CALIBRATED",
                THRESHOLD_SOURCE_OWNER)
    if isinstance(near, (int, float)) and active:
        if near <= 0:
            return ("Amber",
                    "zero near-misses reported on a project with recorded exposure hours above "
                    "the floor is Amber. A HIGH reporting rate is the healthy state: it "
                    "indicates a working reporting culture, and a low or zero rate on an active "
                    "project indicates under-reporting rather than safety. Zero is a value here "
                    "and is not treated as missing",
                    "the owner's Run 101 order, section 3.6, unchanged by Run 102. No published "
                    "expected near-miss rate exists for construction, so no ladder is drawn "
                    "over the count and only the near-zero condition the order states in terms "
                    "is banded",
                    "OWNER-CALIBRATED", None, THRESHOLD_SOURCE_OWNER)
        return (None, None,
                f"{near} near-misses were reported on an active project, which is the healthy "
                f"direction. No published expected near-miss rate exists for construction, so "
                f"reporting activity above zero is displayed and no ladder is drawn over the "
                f"count", None, None, None)
    unconfigured = _BR.entry("construction_industry_recordable_rate")
    return (None, None,
            "the frequency rate is reported on both the OSHA 200,000-hour and the ILO "
            "1,000,000-hour bases and is not banded, because the benchmark the ratio is formed "
            "against is not available: " + str(unconfigured.get("why_absent")) +
            " No threshold for a severity rate was supplied, so none is applied, and no "
            "published expected near-miss rate exists for construction. The three measures are "
            "reported separately and are never combined into one index",
            None, None, None)


#: The words a safety record may use for the four conditions the owner's hard override names.
#: A record that states one of them is Red however low its rate. The words are the order's own;
#: a severity word that is none of these matches nothing and is reported unranked rather than
#: dropped to the nearest one.
_SAFETY_OVERRIDE_WORDS: frozenset = frozenset({
    "fatality", "fatal", "death", "permanent_total_disability",
    "serious_life_threatening_event", "life_threatening", "serious_injury",
    "stop_work", "stop_work_order", "cease_and_desist",
    "unresolved_high_severity_violation", "high_severity_violation",
})


def _severe_safety_events(structure: Mapping[str, Any], result: dict[str, Any]) -> dict | None:
    """
    The owner's hard-override condition, read from what the record states. Never inferred.

    TWO ROUTES, both the document's own statement: a `severe_events` list whose rows name one of
    the override conditions, and the fatality count the severity leg already reads. Nothing here
    derives a fatality from a rate or from days lost.
    """
    hits: list[str] = []
    for row in (structure.get("severe_events") or []):
        if isinstance(row, dict):
            word = str(row.get("event_type") or row.get("severity") or "").strip().lower()
        else:
            word = str(row or "").strip().lower()
        word = word.replace(" ", "_").replace("-", "_")
        if word in _SAFETY_OVERRIDE_WORDS:
            hits.append(word)
    n_fatal = (result.get("severity") or {}).get("fatalities_or_ptd")
    if isinstance(n_fatal, (int, float)) and n_fatal > 0:
        hits.append(f"{int(n_fatal)} fatality or permanent total disability")
    if not hits:
        return None
    return {"what": ", ".join(sorted(set(hits))), "events": sorted(set(hits))}


def _band_environmental(result: dict[str, Any], structure: Mapping[str, Any]) -> tuple:
    """
    A6.3. RUN 102, SECTION 4.3. TIMELY CLOSURE, AND THE MANDATORY-DEADLINE OVERRIDE.

        TimelyClosureRate = corrective actions closed by their required deadline
                            / corrective actions requiring closure

    THIS REPLACES RUN 101'S CONSEQUENCE LADDER, ON THE OWNER'S EXPLICIT REVERSAL (section 0.2).
    Run 101 built a four-rung severity ladder over `environmental_findings` and took any
    confirmed violation to Red. The owner has ruled that the measure is a closure RATE with a
    critical-violation override, and that is what this now is. The severity words the ladder
    ranked are retained below and are still read -- they are now the OVERRIDE's vocabulary
    rather than the band's, which is where the owner has put them.

    THE DEADLINE IS CODIFIED AND IS THE PROJECT'S OWN -- its permit, its environmental
    management plan, or its contract. NOTHING HERE SUPPLIES A DEADLINE OR DEFAULTS ONE, and the
    EPA Construction General Permit's seven-day figure is NOT applied as a substitute: it is a
    fact about one permit regime, not about this project's commitments, and applicability is
    never assumed. An action stating no deadline is in neither the numerator nor the denominator
    and is counted separately.

    THE PERCENTAGE BANDS ARE OWNER-CONFIGURED. The owner records that no published universal
    aggregate closure-rate threshold exists; the correct basis is the project's own instrument,
    and the percentages over it are his.

    A MANDATORY DEADLINE ALWAYS OVERRIDES THE PERCENTAGE (section 4.3, in terms). Any overdue
    critical permit violation, enforcement notice, stop-work condition, or corrective action
    unclosed past a mandatory regulatory or permit deadline is Red at any rate, including 100
    per cent.
    """
    _override = (
        "HARD OVERRIDE, and it outranks every percentage band: Red for any overdue critical "
        "permit violation, enforcement notice, stop-work condition, or corrective action left "
        "unclosed past a mandatory regulatory or permit deadline. A mandatory deadline always "
        "overrides the percentage.")
    overdue = list(result.get("overdue_mandatory_actions") or [])
    enforcement = _environmental_override_findings(structure)
    rate = result.get("timely_closure_rate")
    cuts = _BR.entry("environmental_timely_closure_bands")
    if overdue or enforcement:
        what = []
        if overdue:
            what.append(f"{len(overdue)} corrective action"
                        f"{'' if len(overdue) == 1 else 's'} unclosed past a mandatory or "
                        f"critical deadline")
        if enforcement:
            what.append("an enforcement condition of the kind the override names: "
                        + ", ".join(enforcement))
        return ("Red",
                _override + " This project's environmental record states " + "; ".join(what)
                + ".",
                ("the owner's Run 102 order, section 4.3. The DEADLINE is CODIFIED -- the "
                 "project's own permit, environmental management plan or contract states it, "
                 "and nothing here supplies or defaults one. The override is a consequence "
                 "condition, not a percentage, and no closure rate can make it not have "
                 "happened"),
                "CODIFIED", None, THRESHOLD_SOURCE_PROJECT)
    if rate is None:
        return (None, None,
                (str(result.get("timely_closure_reason"))
                 if result.get("timely_closure_reason") else
                 "no corrective-action register with required deadlines is recorded for this "
                 "project, so no timely-closure rate is measurable. This module's measure is "
                 "corrective actions closed by their required deadline divided by corrective "
                 "actions requiring closure; the deadline must be the project's own permit, "
                 "environmental management plan or contract, and none is stated. No closure "
                 "rate is estimated from a violations count or a document-stated compliance "
                 "percentage, which are different quantities"),
                None, None, None)
    if not cuts.get("configured"):
        return (None, None,
                "no closure-rate band is configured, so the timely-closure rate is displayed "
                "and no band is asserted", None, None, None)
    g, y, a = (cuts["green_at"], cuts["yellow_at_or_above"], cuts["amber_at_or_above"])
    colour = ("Green" if rate >= g else "Yellow" if rate >= y
              else "Amber" if rate >= a else "Red")
    boundary = (
        f"on the timely closure rate -- corrective actions closed BY their required deadline "
        f"divided by corrective actions requiring closure: {g} exactly, every action closed on "
        f"time, is Green; at or above {y} and below {g} is Yellow; at or above {a} and below "
        f"{y} is Amber; below {a} is Red. Green requires ALL of them, not almost all. "
        f"{_override}")
    basis = (
        "the owner's Run 102 order, section 4.3. THE DEADLINE IS CODIFIED and is the project's "
        "own -- its permit, its environmental management plan, or its contract -- and nothing "
        "here supplies one, defaults one, or substitutes the EPA Construction General Permit's "
        "seven-day figure for it. THE PERCENTAGE BANDS ARE OWNER-CONFIGURED: the owner records "
        "that no published universal aggregate closure-rate threshold exists, so these three "
        "percentages are his tolerance and are not presented as a published standard")
    return (colour, boundary, basis, "CODIFIED", "OWNER-CALIBRATED", THRESHOLD_SOURCE_OWNER)


def _environmental_override_findings(structure: Mapping[str, Any]) -> list[str]:
    """
    The enforcement conditions the owner's override names, as the record states them.

    READ FROM THE SAME SEVERITY WORDS RUN 101'S LADDER RANKED. Those words are not deleted: the
    owner has moved them from deciding the band to deciding the override, and a record that
    already states them is still understood. A severity word that is none of them matches
    nothing and is reported unranked rather than dropped to the nearest one.
    """
    hits: list[str] = []
    for f in (structure.get("environmental_findings") or []):
        if not isinstance(f, dict):
            continue
        sev = str(f.get("severity") or "").strip().lower()
        if sev in _ENV_OVERRIDE:
            hits.append(sev)
    return sorted(set(hits))


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

#: RUN 102. THE OVERRIDE'S VOCABULARY: the conditions the owner's section 4.3 names in terms --
#: an overdue critical permit violation, an enforcement notice, a stop-work condition. It is the
#: Run 101 Red rung MINUS `missed_corrective_action_deadline`, which is no longer read from a
#: severity word at all: a missed deadline is now MEASURED from the corrective-action register's
#: own dates in `canonical_v6._timely_closure`, where it is a fact rather than a label.
_ENV_OVERRIDE: frozenset = frozenset(_ENV_RED - {"missed_corrective_action_deadline"}) | frozenset({
    "notice_of_violation", "enforcement_notice", "administrative_order",
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
                "project, so there is no rating to map", None, None, None)
    # THE RATING MAY ARRIVE AS THE DOCUMENT'S WORD OR AS ITS NUMBER ON THE SHIPPED FIVE-POINT
    # SCALE, and both resolve to the SAME word through `extraction_merge.CPARS_RATING_SCALE` --
    # the one authority for that scale, inverted here rather than transcribed. A rating that is
    # neither one of the five words nor one of the five numbers resolves to nothing and falls
    # into no band, which section 3 boundary rule 2 requires.
    seen = [_cpars_word(r.get("rating")) for r in rows if isinstance(r, dict)]
    mapped = [(_CPARS_BANDS[s], s) for s in seen if s in _CPARS_BANDS]
    unmapped = sorted({s for s in seen if s and s not in _CPARS_BANDS})
    if not mapped:
        # ================ RUN 102, SECTION 4.4. THE NUMERIC FALLBACK, AND WHERE IT YIELDS.
        # USED ONLY WHERE NO OWNER SCALE IS PROVIDED. A rating that resolves to one of the five
        # CPARS words has already banded above and never reaches here, so this cannot displace
        # the CPARS mapping. It also yields to the contract's own scorecard method: where the
        # assessment record states a `rating_scale_source` -- the contract's own scorecard --
        # this generic 0-to-100 ladder is NOT applied, because a contract scorecard is rung 1 of
        # the precedence order and this is rung 3, and rung 3 may not overwrite rung 1 with a
        # scale that means something else on that contract's own paper.
        _numeric = _numeric_scores(rows)
        _cuts = _BR.entry("contractor_numeric_fallback_bands")
        _scale_source = result.get("rating_scale_source") or result.get(
            "factor_definitions_version")
        if _numeric and _cuts.get("configured") and not result.get("rating_scale_source"):
            _g, _y, _a = (_cuts["green_at_or_above"], _cuts["yellow_at_or_above"],
                          _cuts["amber_at_or_above"])
            _worst_value, _worst_factor = min(_numeric)
            colour = ("Green" if _worst_value >= _g else "Yellow" if _worst_value >= _y
                      else "Amber" if _worst_value >= _a else "Red")
            return (colour,
                    f"on a numeric contractor performance score out of 100, WORST FACTOR "
                    f"banding as above: at or above {_g} is Green; at or above {_y} and below "
                    f"{_g} is Yellow; at or above {_a} and below {_y} is Amber; below {_a} is "
                    f"Red. Each boundary is INCLUSIVE ON ITS LOWER SIDE. The worst rated factor "
                    f"was {_worst_factor} at {_worst_value}, and a marginal factor is not "
                    f"cancelled by a strong one",
                    "the owner's Run 102 order, section 4.4. OWNER-CONFIGURED, and a FALLBACK "
                    "only: it is used where no owner scale is provided and it YIELDS to the "
                    "contract's own scorecard or rating method, which is rung 1 of the "
                    "precedence order. The five CPARS ratings, where they are present, band "
                    "through the CPARS mapping and never reach this ladder",
                    "OWNER-CALIBRATED", None, THRESHOLD_SOURCE_OWNER)
        _why_not = ""
        if _numeric and result.get("rating_scale_source"):
            _why_not = (f" A numeric score is recorded, and the owner's numeric fallback is NOT "
                        f"applied to it: this contract states its own scorecard method "
                        f"({_scale_source!r}), which outranks a generic 0-to-100 ladder, and "
                        f"this platform holds no reading of that scorecard's own bands.")
        return (None, None,
                f"none of the ratings recorded for this project is one of the five CPARS "
                f"ratings the mapping is defined over (recorded: {unmapped}), so no band is "
                f"asserted and none falls to a nearest rating.{_why_not}", None, None, None)
    worst = max(mapped, key=lambda p: _CPARS_SEVERITY[p[0]])
    return (worst[0],
            "Exceptional and Very Good map to Green; Satisfactory to Yellow; Marginal to Amber; "
            "Unsatisfactory to Red. Where several factors are rated the WORST rating bands, "
            "because a marginal factor is not cancelled by an exceptional one and no governed "
            "policy for averaging factor ratings is supplied. Collapsing five ordinal levels "
            "into four bands is a DESIGN CHOICE, not a published mapping: Exceptional and Very "
            "Good are joined because both stand above the Satisfactory level the guidance "
            "defines as meeting contract requirements",
            "the owner's Run 101 order, section 3.8, unchanged by Run 102: the five ratings are "
            "defined in the CPARS guidance and referenced by FAR Subpart 42.15",
            "CODIFIED", None,
            # RUNG 2. The CPARS/FAR rating scale is a formal external instrument, not this
            # owner's configured tolerance and not a figure from this project's own contract.
            THRESHOLD_SOURCE_EXTERNAL)


def _numeric_scores(rows: list[dict[str, Any]]) -> list[tuple[float, Any]]:
    """
    RUN 102. The factor ratings that are plain numbers on a 0-to-100 scale, with their factors.

    A RATING THAT IS ONE OF THE FIVE CPARS NUMBERS IS NOT ONE OF THESE. `_cpars_word` already
    resolves 1 through 5 to the five CPARS words, and anything it resolves has banded through
    the CPARS mapping and never reaches this function. A value outside 0 to 100 is not on the
    scale this ladder is defined over and is left out rather than clamped.
    """
    out: list[tuple[float, Any]] = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        value = r.get("rating")
        try:
            number = float(str(value).strip())
        except (TypeError, ValueError):
            continue
        if 0 <= number <= 100:
            out.append((number, r.get("factor")))
    return out


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
        _colour, _boundary, _basis, _prov, _bprov, _tsrc = _a6_band(
            module_id, result, structure)
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
            # RUN 102, SECTION 12.5. A BAND STORED WITHOUT ITS THRESHOLD SOURCE FAILS THE RUN,
            # so this raises rather than defaulting -- the same construction `models.banded`
            # uses, for the same reason: a default is a place where forgetting is possible.
            if _tsrc not in THRESHOLD_SOURCES:
                raise ValueError(f"{module_id}: {_tsrc!r} is not one of the three threshold "
                                 f"sources; a band may not be stored without one")
            row["threshold_source"] = _tsrc
            row["threshold_source_words"] = THRESHOLD_SOURCE_WORDS[_tsrc]
            row["threshold_precedence_order"] = (
                "project-specific document, then formal external basis, then the owner's "
                "configured default. Where none of the three supplies a threshold the figure is "
                "displayed, no band is asserted, no vote is cast and the reason is stated")
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
        # RUN 102. THE FIRST-PASS FIGURE LEADS, because it is what this module now bands on. The
        # requirement conformance rate follows where it was also measurable, named as the second
        # figure it is; neither stands in for the other.
        parts = []
        if result.get("first_pass_acceptance_rate") is not None:
            parts.append(
                f"{result.get('items_passing_first_inspection')} of "
                f"{result.get('items_inspected')} items inspected were accepted on FIRST "
                f"inspection, a first-pass acceptance rate of "
                f"{round(result['first_pass_acceptance_rate'], 4)}"
                + (f"; {len(result.get('critical_quality_failures') or [])} designated critical "
                   f"or hold-point item(s) failed"
                   if result.get("critical_quality_failures") else
                   "; no designated critical or hold-point item failed"))
        elif result.get("first_pass_reason"):
            parts.append(str(result["first_pass_reason"]))
        if result.get("quality_compliance_rate") is not None:
            parts.append(
                f"separately, {result.get('satisfied')} of {result.get('applicable_assessed')} "
                f"assessed applicable quality requirements are satisfied, which is a different "
                f"population and is not what the band is drawn over")
        return ". ".join(parts) if parts else str(result.get("reason", ""))
    if m == "environmental_compliance":
        # RUN 102. THE TIMELY-CLOSURE FIGURE LEADS, for the same reason.
        parts = []
        if result.get("timely_closure_rate") is not None:
            parts.append(
                f"{result.get('corrective_actions_closed_by_deadline')} of "
                f"{result.get('corrective_actions_requiring_closure')} corrective actions "
                f"requiring closure were closed by their required deadline, a timely closure "
                f"rate of {round(result['timely_closure_rate'], 4)}"
                + (f"; {len(result.get('corrective_actions_without_a_stated_deadline') or [])} "
                   f"further action(s) state no deadline and are in neither the numerator nor "
                   f"the denominator"
                   if result.get("corrective_actions_without_a_stated_deadline") else ""))
        elif result.get("timely_closure_reason"):
            parts.append(str(result["timely_closure_reason"]))
        if result.get("environmental_compliance_rate") is not None:
            parts.append(
                f"separately, {result.get('satisfied')} of {result.get('applicable_assessed')} "
                f"assessed applicable environmental requirements are satisfied, which is a "
                f"different population and is not what the band is drawn over")
        return ". ".join(parts) if parts else str(result.get("reason", ""))
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
