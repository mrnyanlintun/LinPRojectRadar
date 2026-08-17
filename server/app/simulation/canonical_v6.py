"""
THE CANONICAL CATEGORY-8 AND CATEGORY-9 LAYER, v17 (Run 31).

WHAT THIS REPLACES, and every one of these was real production behaviour at v16:

  B3.1  ABM Governance Layer            a threshold comparison on cpi/spi/docRiskScore, with no
                                        agent, no state, no message, no clock and no authority.
  B3.2  FAR Threshold Monitor           EVMS applicability inferred from BAC and cpi.
  B3.3  OMB A-11 Check                  a global "A-11" band from a cost index.
  B3.4  EVM Reporting Threshold         reporting conformance from cpi/spi.
  B3.5  Contract Modification Frequency a raw modification count -- and Category 4.6's job.
  A6.1  Quality Compliance Index        gated on a meeting-minute deficiency mention.
  A6.2  Safety Performance Index        a band from meeting-minute incident mentions.
  A6.3  Environmental Compliance Rate   a band from meeting-minute issue mentions.
  A6.4  Contractor Performance Score    an internal score with no official-assessment structure.
  C1.1  Missing Data Index              missingness over an ELEVEN-FIELD HARD-CODED LIST that is
                                        not any module's actual required-input contract.
  C1.2  Data Timeliness Score           one universal age against one universal window.
  C1.3  Source Reliability Weighting    a weight derived in part from BAC.
  C1.4  Audit Trail Completeness        an event count, not an audit-element assessment.
  C1.5  Information Completeness Ratio  field missingness again -- i.e. 9.1 under another name.
  C1.6  Cross-document Consistency      no governed fact comparison at all.
  C1.7  Reporting Frequency Index       an interval between two extraction events.

EVERY FUNCTION HERE IS PURE AND TAKES ITS GOVERNED STRUCTURE. There is no `si` in this file, no
`rand`, no wall clock and no band ladder: Run 33 owns calibration, so a canonical quantity is
returned with `calibration_pending` and NO `status_color`. Section 53's list of parameters this
run may not invent -- reliability weights, freshness windows, quality and environmental bands,
safety combination weights, contractor aggregation weights, ABM latency distributions, Category-9
thresholds, consistency tolerances and reporting grace windows -- is enforced by the simple fact
that every one of them must arrive IN the structure or the function abstains.

THE 9.1 / 9.5 AND 9.2 / 9.7 DISTINCTIONS ARE STRUCTURAL, NOT DOCUMENTARY (sections 27 and 29).
9.1 reads `required_fields` for ONE module/use and answers field-level missingness. 9.5 reads
`components` -- whole information domains -- and answers package coverage. They cannot return the
same answer because they do not read the same key, and `nonredundancy` below constructs the
witness: a package whose every present record has complete fields while an entire required
domain is absent. 9.2 reads ONE record's age against ONE use's freshness rule; 9.7 reads a
SCHEDULE and a HISTORY. Neither can be computed from the other's input.
"""

from __future__ import annotations

import datetime as _dt
from typing import Any, Iterable, Mapping, Sequence

from . import regulatory as REG
from .abm import ABMStructureError, model_from
from .canonical import StructureAbsent
from .qualified_evidence import (
    CONSISTENT, FUTURE_DATED, MATERIAL_CONFLICT, NOT_COMPARABLE, STALE, TIMELINESS_UNKNOWN, TIMELY,
)

#: The governed structure key each Run-31 module reads off the signal inputs, and the reader's
#: words for it. `project_data.governed_structure_keys()` unions this with the earlier four maps,
#: so an intake path exists for every one of them rather than only for a test.
V6_STRUCTURE_KEYS: dict[str, str] = {
    "B3.1": "abmGovernanceModel",
    "B3.2": "evmsApplicabilityEvidence",
    "B3.3": "a11RuleRegister",
    "B3.4": "evmsReportingRecord",
    "B3.5": "contractModificationRegister",
    "A6.1": "qualityRequirementRegister",
    "A6.2": "safetyPerformanceRecord",
    "A6.3": "environmentalRequirementRegister",
    "A6.4": "contractorAssessmentRecord",
    "C1.1": "requiredInputContract",
    "C1.2": "evidenceTimelinessRecord",
    "C1.3": "sourceProvenanceRecord",
    "C1.4": "auditChainRecord",
    "C1.5": "informationPackageRecord",
    "C1.6": "crossDocumentFactSet",
    "C1.7": "reportingCadenceRecord",
}

V6_STRUCTURE_WORDS: dict[str, str] = {
    "B3.1": "a governed agent, authority-matrix and interaction structure",
    "B3.2": "governed acquisition, agency and clause applicability evidence",
    "B3.3": "a configured A-11 rule register",
    "B3.4": "a governed EVMS reporting record",
    "B3.5": "a governed contract modification register",
    "A6.1": "a governed quality requirement register",
    "A6.2": "a governed safety exposure and leading-indicator record",
    "A6.3": "a governed environmental permit and requirement register",
    "A6.4": "a governed contractor assessment record",
    "C1.1": "the required-input contract for the module or use being assessed",
    "C1.2": "a governed evidence date and freshness rule",
    "C1.3": "a governed source provenance record",
    "C1.4": "a governed audit chain record",
    "C1.5": "a governed information package definition",
    "C1.6": "a governed cross-document fact set",
    "C1.7": "a governed reporting cadence record and report history",
}


def v6_structure(si: dict, module_id: str) -> dict:
    """The module's defining structure off the signal inputs, or StructureAbsent."""
    key = V6_STRUCTURE_KEYS[module_id]
    words = V6_STRUCTURE_WORDS[module_id]
    structure = si.get(key)
    if structure is None:
        raise StructureAbsent(
            f"Awaiting {words}. This measure is named for a method that cannot be carried out "
            f"without it, so no reading is reported and no other figure is used in its place.")
    if not isinstance(structure, dict):
        raise StructureAbsent(
            f"The information provided for this project in place of {words} is not in a form "
            f"this measure can read, so no reading is taken from it.")
    return structure


def _rows(structure: Mapping[str, Any], key: str, words: str) -> list[dict]:
    rows = structure.get(key)
    if not isinstance(rows, list) or not rows:
        raise StructureAbsent(
            f"Awaiting {words}. No entries are recorded, so there is nothing to assess and no "
            f"figure is produced in place of one.")
    for r in rows:
        if not isinstance(r, dict):
            raise StructureAbsent(
                f"An entry supplied as {words} is not in a form this measure can read.")
    return rows


def _date(value: Any) -> _dt.date | None:
    if not isinstance(value, str):
        return None
    try:
        return _dt.date.fromisoformat(value[:10])
    except ValueError:
        return None


# =============================================================================================
# CATEGORY 9 -- EVIDENCE QUALIFICATION MEASURES. METADATA ONLY. NO BAND. NO VOTE.
# =============================================================================================

def missing_data_index(structure: Mapping[str, Any]) -> dict[str, Any]:
    """
    9.1 MISSING DATA INDEX. Field-level mandatory missingness FOR ONE MODULE OR USE.

        MissingFraction_m = RequiredApplicableMissing_m / RequiredApplicableCount_m

    The denominator is the ACTIVE GOVERNED CONTRACT's required fields, supplied in the structure
    -- not this file's opinion about which eleven fields matter, which is what v16 did.

    THE FOUR RULES SECTION 23 SUPPLIES, and each is a branch below rather than a comment:
    zero IS a value and is never missing; null is missing; absent is missing; optional and
    not-applicable fields never enter the denominator. Invalid/malformed mandatory fields are
    identified SEPARATELY and may make the evidence ineligible; they are not folded into the
    missing count, because "present but unreadable" and "absent" are different findings.

    A tiny missing fraction cannot compensate for a missing critical field: `critical_missing`
    is returned alongside and the gate treats it noncompensatorily.
    """
    required = structure.get("required_fields")
    if not isinstance(required, list) or not required:
        raise StructureAbsent(
            "Awaiting the required-input contract for the module or use being assessed. Without "
            "it there is no denominator, and a completeness figure with an invented denominator "
            "is not a measurement.")
    values = structure.get("values")
    if not isinstance(values, dict):
        values = {}
    not_applicable = set(structure.get("not_applicable_fields", ()) or ())
    invalid_declared = set(structure.get("invalid_fields", ()) or ())
    critical = set(structure.get("critical_fields", ()) or ())

    applicable = [f for f in required if f not in not_applicable]
    if not applicable:
        return {
            "measure": "missing_data_index",
            "applicable_required_count": 0,
            "missing_fraction": None,
            "disposition": "NO_APPLICABLE_REQUIREMENT",
            "reason": ("every field in this use's required-input contract is recorded as not "
                       "applicable, so there is no completeness question to answer"),
            "missing_fields": [], "invalid_fields": [], "critical_missing": [],
            "denominator_source": structure.get("contract_id"),
            "calibration_pending": True,
        }
    missing = [f for f in applicable if f not in values or values.get(f) is None]
    invalid = [f for f in applicable if f in invalid_declared and f not in missing]
    critical_missing = sorted(set(missing) & critical)
    return {
        "measure": "missing_data_index",
        "applicable_required_count": len(applicable),
        "missing_count": len(missing),
        "missing_fraction": len(missing) / len(applicable),
        "missing_fields": sorted(missing),
        "invalid_fields": sorted(invalid),
        "critical_missing": critical_missing,
        "denominator_source": structure.get("contract_id"),
        "contract_version": structure.get("contract_version"),
        "disposition": "MEASURED",
        "calibration_pending": True,
    }


def data_timeliness(structure: Mapping[str, Any]) -> dict[str, Any]:
    """
    9.2 DATA TIMELINESS. Age of ONE record against the freshness rule for ONE source class/use.

        Age = EvaluationDate - EffectiveOrSourceDate

    The date FIELD used is explicit (`date_field`), because "the date" on a construction document
    is ambiguous and choosing silently is how a stale record passes. The allowed age and the
    inclusive/exclusive boundary rule both arrive in the structure: section 24 says the boundary
    must be declared in the supplied freshness configuration and section 53 forbids inventing a
    window, so an absent rule abstains rather than defaulting.
    """
    eval_d = _date(structure.get("evaluation_date"))
    src_d = _date(structure.get("effective_date") or structure.get("source_date"))
    rule = structure.get("freshness_rule")
    if not isinstance(rule, dict):
        raise StructureAbsent(
            "Awaiting the governed freshness rule for this source class and use. No universal "
            "allowed age is supplied or invented, so no timeliness reading is taken.")
    allowed = rule.get("allowed_age_days")
    if not isinstance(allowed, (int, float)):
        raise StructureAbsent(
            "The governed freshness rule records no allowed age, so there is nothing to compare "
            "this record's age against.")
    inclusive = rule.get("boundary")
    if inclusive not in ("inclusive", "exclusive"):
        raise StructureAbsent(
            "The governed freshness rule does not declare whether an age exactly equal to the "
            "allowed age is still timely, and that boundary is not chosen here.")
    base = {
        "measure": "data_timeliness",
        "date_field": structure.get("date_field"),
        "source_class": structure.get("source_class"),
        "use": structure.get("use"),
        "allowed_age_days": allowed,
        "boundary": inclusive,
        "freshness_rule_version": rule.get("version"),
        "calibration_pending": True,
    }
    if eval_d is None or src_d is None:
        base.update({"age_days": None, "timeliness_status": TIMELINESS_UNKNOWN,
                     "reason": "a required date is absent or unreadable, so no age is computed"})
        return base
    age = (eval_d - src_d).days
    base["age_days"] = age
    if age < 0:
        base["timeliness_status"] = FUTURE_DATED
        base["reason"] = "the source date is later than the evaluation date"
        return base
    fresh = age <= allowed if inclusive == "inclusive" else age < allowed
    base["timeliness_status"] = TIMELY if fresh else STALE
    return base


def source_reliability(structure: Mapping[str, Any]) -> dict[str, Any]:
    """
    9.3 SOURCE RELIABILITY. A TRANSPARENT PROVENANCE ASSESSMENT, and a number ONLY if a governed
    rubric supplies one.

    BAC HAS NO PLACE HERE and the v16 weighting that used it is gone. What is assessed is the
    evidence's own characteristics: authority, verification state, provenance completeness,
    traceability, freshness, corroboration and genuinely measured extraction confidence.

    Section 25 and section 53: no pseudo-precise numeric weight is invented. With no governed
    rubric the weight is NONE -- not 1, not 0.5 -- and the component evidence is still reported,
    which is the point: a structural assessment remains useful without a fabricated scalar.

    Where a rubric IS supplied it must carry a version and a basis, and the rubric's own scores
    are applied; this function chooses none of them. Monotonicity in verification (section 25) is
    therefore a property of the SUPPLIED rubric, and the oracle tests the supplied one.
    """
    rubric = structure.get("rubric")
    components = {
        "source_authority": structure.get("source_authority"),
        "verification_status": structure.get("verification_status"),
        "provenance_complete": structure.get("provenance_complete"),
        "traceability": structure.get("traceability"),
        "corroboration": list(structure.get("corroboration", ()) or ()),
        "extraction_confidence": structure.get("extraction_confidence"),
        "superseded": structure.get("superseded"),
        "conflicting_records": list(structure.get("conflicting_records", ()) or ()),
    }
    out: dict[str, Any] = {
        "measure": "source_reliability",
        "components": components,
        "calibration_pending": True,
    }
    if not isinstance(rubric, dict):
        out.update({
            "reliability_weight": None,
            "rubric_version": None,
            "disposition": "NO_GOVERNED_MAPPING",
            "reason": ("no governed reliability rubric is established for this source, so no "
                       "numeric reliability weight is asserted; the component evidence above is "
                       "reported instead"),
        })
        return out
    scores = rubric.get("scores")
    if not isinstance(scores, dict) or not rubric.get("version") or not rubric.get("basis"):
        raise StructureAbsent(
            "A reliability rubric was supplied without a score mapping, a version or a basis, so "
            "any weight computed from it would be undatable and unattributable.")
    total = 0.0
    used: dict[str, Any] = {}
    for attr, table in scores.items():
        val = components.get(attr)
        key = str(val)
        if isinstance(table, dict) and key in table:
            total += float(table[key])
            used[attr] = table[key]
    out.update({
        "reliability_weight": total,
        "rubric_version": rubric.get("version"),
        "rubric_basis": rubric.get("basis"),
        "rubric_calibration_source": rubric.get("calibration_source"),
        "rubric_effective_date": rubric.get("effective_date"),
        "not_for_operational_weighting": bool(rubric.get("not_for_operational_weighting")),
        "attribute_scores": used,
        "disposition": "GOVERNED_RUBRIC_APPLIED",
    })
    return out


def audit_trail_completeness(structure: Mapping[str, Any]) -> dict[str, Any]:
    """
    9.4 AUDIT TRAIL COMPLETENESS. NONCOMPENSATORY.

        ATC_d = RequiredApplicableAuditElementsPresent / RequiredApplicableAuditElements

    AuditComplete only when ATC = 1 AND every critical element is present AND the required
    linkages and chronology are valid. Adding a hundred optional fields cannot compensate,
    because optional elements never enter either side of the ratio -- which is a structural fact
    about this function, not a promise in a docstring.

    The elements assessed are the real research/governance objects: signal package, judgment
    ledger, authority, response, override/defer/escalation, method version, evidence and
    event/timestamp linkage. BAC is not assessed and is not assessable here.
    """
    schema = structure.get("audit_schema")
    if not isinstance(schema, dict):
        raise StructureAbsent(
            "Awaiting the versioned audit schema that says which elements are mandatory, which "
            "are critical and which are optional. Without it, completeness has no definition.")
    critical = list(schema.get("mandatory_critical", ()) or ())
    noncritical = list(schema.get("mandatory_noncritical", ()) or ())
    required = critical + noncritical
    if not required:
        raise StructureAbsent(
            "The audit schema declares no mandatory elements, so every chain would be complete.")
    not_applicable = set(structure.get("not_applicable_elements", ()) or ())
    present = structure.get("present_elements")
    if not isinstance(present, (list, tuple)):
        present = ()
    present_set = set(present)

    applicable = [e for e in required if e not in not_applicable]
    applicable_critical = [e for e in critical if e not in not_applicable]
    have = [e for e in applicable if e in present_set]
    missing = [e for e in applicable if e not in present_set]
    critical_missing = [e for e in applicable_critical if e not in present_set]

    links = structure.get("links", {}) or {}
    broken_links = sorted(k for k, v in links.items() if not v)
    chronology_ok = bool(structure.get("chronology_valid", True))

    atc = len(have) / len(applicable) if applicable else None
    complete = (atc == 1.0 and not critical_missing and not broken_links and chronology_ok)
    return {
        "measure": "audit_trail_completeness",
        "atc": atc,
        "required_applicable": len(applicable),
        "present_applicable": len(have),
        "missing_elements": missing,
        "critical_missing": critical_missing,
        "broken_links": broken_links,
        "chronology_valid": chronology_ok,
        "audit_complete": complete,
        "audit_schema_version": schema.get("version"),
        "optional_elements_present": sorted(present_set - set(required)),
        "calibration_pending": True,
    }


def information_completeness(structure: Mapping[str, Any]) -> dict[str, Any]:
    """
    9.5 INFORMATION COMPLETENESS RATIO. PACKAGE-LEVEL COVERAGE, and it reads a different key
    from 9.1 so the two cannot silently become the same measure.

        InformationCompleteness = PresentAndUsableApplicableRequired / ApplicableRequired

    "Usable" is the load-bearing word. A component whose mandatory internal fields are ALL
    missing is not usable merely because a filename exists, so `usable` is computed from the
    component's own field state and a component may be present-but-unusable. Not-applicable
    components are excluded from the denominator; optional components never enter it.

    Critical package absence stays separately visible in `missing_critical_domains`.
    """
    components = _rows(structure, "components", "the applicable required information package")
    applicable, present_usable = [], []
    missing_domains, unusable, missing_critical = [], [], []
    for c in components:
        name = c.get("component_id") or c.get("domain") or "?"
        if c.get("applicable") is False or c.get("required") is False:
            continue
        applicable.append(name)
        if not c.get("present"):
            missing_domains.append(name)
            if c.get("critical"):
                missing_critical.append(name)
            continue
        mandatory = list(c.get("mandatory_fields", ()) or ())
        values = c.get("values") if isinstance(c.get("values"), dict) else {}
        if mandatory and all(values.get(f) is None for f in mandatory):
            unusable.append(name)
            if c.get("critical"):
                missing_critical.append(name)
            continue
        present_usable.append(name)
    if not applicable:
        return {
            "measure": "information_completeness",
            "applicable_required_components": 0, "information_completeness": None,
            "disposition": "NO_APPLICABLE_COMPONENT",
            "missing_domains": [], "unusable_components": [], "missing_critical_domains": [],
            "package_id": structure.get("package_id"), "calibration_pending": True,
        }
    return {
        "measure": "information_completeness",
        "applicable_required_components": len(applicable),
        "present_and_usable": len(present_usable),
        "information_completeness": len(present_usable) / len(applicable),
        "missing_domains": missing_domains,
        "unusable_components": unusable,
        "missing_critical_domains": missing_critical,
        "package_id": structure.get("package_id"),
        "package_version": structure.get("package_version"),
        "disposition": "MEASURED",
        "calibration_pending": True,
    }


def cross_document_consistency(structure: Mapping[str, Any]) -> dict[str, Any]:
    """
    9.6 CROSS-DOCUMENT CONSISTENCY. The SAME governed fact across actual source records.

    THE CONFLICT IS NEVER AVERAGED AWAY. A material conflict is returned as a row naming both
    sources and both values; there is no reconciliation step, no mean and no "resolved" value.
    Section 28 says never average 100 and 110 to 105 and declare the conflict gone, and there is
    no arithmetic in this function that could.

    Comparability is checked BEFORE agreement: different reporting periods, different units or
    different revision contexts are NOT_COMPARABLE, not inconsistent. Numeric tolerance arrives
    in the fact's own `tolerance` rule -- no universal tolerance is supplied and none is invented
    -- and is relative to the GOVERNED REFERENCE source's value.
    """
    facts = _rows(structure, "facts", "a governed cross-document fact set")
    comparisons, conflicts = [], []
    comparable = consistent = 0
    for f in facts:
        fact_id = f.get("fact_id")
        observations = f.get("observations")
        ref_source = f.get("reference_source")
        if not isinstance(observations, list) or len(observations) < 2:
            comparisons.append({"fact_id": fact_id, "result": NOT_COMPARABLE,
                                "reason": "fewer than two source records report this fact"})
            continue
        ref = next((o for o in observations if o.get("source_id") == ref_source), None)
        if ref is None:
            comparisons.append({"fact_id": fact_id, "result": NOT_COMPARABLE,
                                "reason": "no governed reference source is configured"})
            continue
        for o in observations:
            if o is ref:
                continue
            row = {
                "fact_id": fact_id, "reference_source": ref_source,
                "source_id": o.get("source_id"),
                "reference_value": ref.get("value"), "value": o.get("value"),
                "units": o.get("units"), "reference_units": ref.get("units"),
                "period": o.get("period"), "reference_period": ref.get("period"),
                "effective_date": o.get("effective_date"),
                "revision": o.get("revision"), "reference_revision": ref.get("revision"),
                "source_authority": o.get("source_authority"),
                "normalization": f.get("normalization"),
                "tolerance_rule": f.get("tolerance"),
                "tolerance_rule_version": f.get("tolerance_version"),
            }
            if o.get("period") != ref.get("period") or o.get("units") != ref.get("units"):
                row["result"] = NOT_COMPARABLE
                row["reason"] = ("these records describe different reporting periods or units, "
                                 "so they do not contradict one another")
                comparisons.append(row)
                continue
            comparable += 1
            a, b = ref.get("value"), o.get("value")
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                tol = f.get("tolerance")
                if not isinstance(tol, dict):
                    row["result"] = NOT_COMPARABLE
                    row["reason"] = ("no governed numeric tolerance rule is configured for this "
                                     "fact, and none is invented here")
                    comparable -= 1
                    comparisons.append(row)
                    continue
                rel = tol.get("relative")
                absol = tol.get("absolute")
                diff = abs(b - a)
                row["difference"] = diff
                if rel is not None and a != 0:
                    row["relative_difference"] = diff / abs(a)
                    ok = (diff / abs(a)) <= rel
                elif absol is not None:
                    ok = diff <= absol
                else:
                    row["result"] = NOT_COMPARABLE
                    row["reason"] = "the configured tolerance rule states neither bound"
                    comparable -= 1
                    comparisons.append(row)
                    continue
            else:
                norm = f.get("normalization")
                ok = (str(a) == str(b)) if norm != "casefold" else (
                    str(a).casefold() == str(b).casefold())
            row["result"] = CONSISTENT if ok else MATERIAL_CONFLICT
            if ok:
                consistent += 1
            else:
                conflicts.append(dict(row))
            comparisons.append(row)
    return {
        "measure": "cross_document_consistency",
        "comparisons": comparisons,
        "material_conflicts": conflicts,
        "comparable_facts": comparable,
        "consistent_facts": consistent,
        "consistency_fraction": (consistent / comparable) if comparable else None,
        "disposition": "MEASURED" if comparisons else "NO_COMPARABLE_FACT",
        "calibration_pending": True,
    }


def reporting_frequency(structure: Mapping[str, Any]) -> dict[str, Any]:
    """
    9.7 REPORTING FREQUENCY. RECURRING CADENCE, which is a different question from 9.2's freshness
    of one record now, and reads a schedule and a history rather than one date.

        ReportingCoverage    = UniqueValidExpectedPeriodsReceived / ExpectedPeriods
        OnTimeReportingRate  = ExpectedReportsReceivedWithinGovernedWindow / ExpectedReports

    DUPLICATES CANNOT INFLATE THE NUMERATOR: coverage counts UNIQUE expected periods matched, so
    a second report for period 1 matches a period already matched and changes nothing.

    An APPROVED EXTENSION moves the governed due date for that period and the report is evaluated
    against the revised date. No grace window is invented (section 53): a report is late if it
    arrives after its governed due date, extension included.
    """
    periods = _rows(structure, "expected_periods", "the governed reporting schedule")
    history = structure.get("report_history")
    if not isinstance(history, list):
        history = []
    extensions = structure.get("approved_extensions", {}) or {}

    matched: dict[str, dict[str, Any]] = {}
    duplicates = []
    for rec in history:
        if not isinstance(rec, dict):
            continue
        pid = rec.get("period_id")
        if pid in matched:
            duplicates.append(rec)
            continue
        matched[pid] = rec

    rows, on_time = [], 0
    for p in periods:
        pid = p.get("period_id")
        due = _date(extensions.get(pid) or p.get("due_date"))
        revised = pid in extensions
        rec = matched.get(pid)
        received = _date(rec.get("received_date")) if rec else None
        row = {"period_id": pid, "due_date": (due.isoformat() if due else None),
               "due_date_revised_by_approved_extension": revised,
               "received_date": (received.isoformat() if received else None)}
        if rec is None:
            row["status"] = "MISSING"
        elif received is None or due is None:
            row["status"] = "INSUFFICIENT_EVIDENCE"
        elif received <= due:
            row["status"] = "ON_TIME"
            on_time += 1
        else:
            row["status"] = "LATE"
            row["days_late"] = (received - due).days
        rows.append(row)

    expected = len(periods)
    covered = sum(1 for r in rows if r["status"] in ("ON_TIME", "LATE"))
    return {
        "measure": "reporting_frequency",
        "report_class": structure.get("report_class"),
        "observation_window": structure.get("observation_window"),
        "expected_periods": expected,
        "periods_received": covered,
        "reporting_coverage": (covered / expected) if expected else None,
        "on_time_count": on_time,
        "on_time_reporting_rate": (on_time / expected) if expected else None,
        "duplicate_reports_ignored": len(duplicates),
        "approved_extensions": dict(extensions),
        "cadence_version": structure.get("cadence_version"),
        "cessation_status": structure.get("cessation_status"),
        "periods": rows,
        "disposition": "MEASURED",
        "calibration_pending": True,
    }


def nonredundancy(package_structure: Mapping[str, Any],
                  field_structure: Mapping[str, Any]) -> dict[str, Any]:
    """
    THE 9.1 vs 9.5 WITNESS (section 27). Construct nothing; MEASURE both on the same package and
    report whether production can distinguish the two states. If it cannot, Run 31 is not closed.
    """
    fields = missing_data_index(field_structure)
    package = information_completeness(package_structure)
    return {
        "field_level_missing_fraction": fields.get("missing_fraction"),
        "field_level_complete": fields.get("missing_fraction") == 0,
        "package_coverage": package.get("information_completeness"),
        "package_complete": package.get("information_completeness") == 1,
        "missing_domains": package.get("missing_domains"),
        "distinguishable": (fields.get("missing_fraction") == 0
                            and package.get("information_completeness") != 1),
    }


# =============================================================================================
# CATEGORY 8 -- GOVERNANCE, AUTHORITY, CONFORMANCE. NO LEGAL DETERMINATION IS ISSUED.
# =============================================================================================

def evms_applicability(structure: Mapping[str, Any]) -> dict[str, Any]:
    """
    8.2 FAR/AGENCY EVMS APPLICABILITY MONITOR.

    NOTHING HERE READS BAC, CPI, SPI, EV OR AC, and section 9 forbids inferring applicability
    from any of them. Applicability is a question about the acquisition, the agency, the agency
    procedure and the contract clause, and it is answered from that evidence or not at all.

    Precedence: conflicting evidence -> REVIEW_REQUIRED; incomplete designation/agency/clause
    evidence -> INSUFFICIENT_EVIDENCE; explicit non-applicability established -> NOT_APPLICABLE;
    major-for-development OR an explicit agency-procedure/contract requirement -> APPLICABLE.
    """
    federal = structure.get("federal_context")
    designation = structure.get("acquisition_designation")
    major = structure.get("major_acquisition")
    agency = structure.get("agency")
    procedure = structure.get("agency_procedure_requires_evms")
    clause = structure.get("clause_id")
    conflicts = list(structure.get("conflicting_evidence", ()) or ())
    rule = REG.FAR_34_201
    out: dict[str, Any] = dict(rule.identity())
    out.update({
        "measure": "evms_applicability",
        "acquisition_id": structure.get("acquisition_id"),
        "federal_context": federal, "agency": agency,
        "acquisition_designation": designation, "major_acquisition": major,
        "agency_procedure_requires_evms": procedure, "clause_id": clause,
        "award_date": structure.get("award_date"),
        "evidence_source": structure.get("evidence_source"),
        "conflicting_evidence": conflicts,
        "calibration_pending": True,
    })

    def done(state: str, reason: str) -> dict[str, Any]:
        out["applicability"] = state
        out["reason"] = reason
        out["statement"] = REG.sentence(
            rule, REG.SATISFIED if state == REG.APPLICABLE else
            REG.NOT_APPLICABLE if state == REG.NOT_APPLICABLE else
            REG.REVIEW_REQUIRED if state == REG.REVIEW_REQUIRED else REG.INSUFFICIENT_EVIDENCE)
        return out

    if conflicts:
        return done(REG.REVIEW_REQUIRED,
                    "the governed applicability evidence conflicts: " + "; ".join(conflicts))
    if federal is None:
        return done(REG.INSUFFICIENT_EVIDENCE,
                    "whether this is a Federal acquisition is not established by the evidence")
    if federal is False:
        if procedure is True:
            return done(REG.APPLICABLE,
                        "a non-Federal contract requirement establishes that EVMS applies")
        return done(REG.NOT_APPLICABLE,
                    "this is not a Federal acquisition and no contract requirement establishing "
                    "EVMS applicability is recorded")
    if structure.get("evms_not_applicable_established") is True:
        return done(REG.NOT_APPLICABLE,
                    "the governed evidence establishes EVMS is not applicable in this "
                    "acquisition, agency and contract context")
    if designation is None or agency is None:
        return done(REG.INSUFFICIENT_EVIDENCE,
                    "the acquisition designation or agency is not established, and neither is "
                    "inferred from cost or schedule performance")
    if major is True and designation == "development":
        return done(REG.APPLICABLE,
                    "this is a major acquisition for development under the configured rule")
    if procedure is True or clause:
        return done(REG.APPLICABLE,
                    "an explicit agency procedure or contract clause requires EVMS for this "
                    "acquisition")
    if major is None or procedure is None:
        return done(REG.INSUFFICIENT_EVIDENCE,
                    "major-acquisition status or the applicable agency procedure is not "
                    "established, so applicability is not determined")
    return done(REG.NOT_APPLICABLE,
                "this acquisition is not major for development and no agency procedure or "
                "clause requiring EVMS is recorded")


def a11_conformance(structure: Mapping[str, Any]) -> dict[str, Any]:
    """
    8.3 VERSIONED A-11 CAPITAL PROGRAMMING CONFORMANCE CHECK.

    A CONFIGURED SUBSET ONLY. The project-level line summarises the rules actually configured and
    NEVER claims global A-11 conformance -- `subset_only` is True on every result and the summary
    field is named `configured_subset_result` so no caller can mistake it for a certification.

    Every rule in the register is evaluated through `regulatory.evaluate`, so a superseded or
    wrong-edition rule cannot reach a positive answer regardless of what this function does.
    """
    edition = structure.get("a11_edition")
    rules = _rows(structure, "rules", "a configured A-11 rule register")
    results = []
    for r in rules:
        section = r.get("section")
        try:
            rule = REG.RegulatoryRule(
                rule_id=r.get("rule_id") or "", authority_family="OMB",
                citation="OMB Circular A-11", section=section,
                edition=edition or "", effective_date=r.get("effective_date") or "",
                summary=r.get("summary") or "",
                applicability_conditions=tuple(r.get("applicability_conditions", ()) or ()),
                required_evidence=tuple(r.get("required_evidence", ()) or ("evidence",)),
                reviewer_role=r.get("reviewer_role") or "agency capital programming authority",
                superseded=bool(r.get("superseded")))
        except REG.RuleVersionError as exc:
            results.append({"rule_id": r.get("rule_id"), "section": section,
                            "result": REG.REVIEW_REQUIRED, "reason": str(exc)})
            continue
        applicable = r.get("applicable")
        evidence = r.get("evidence") if isinstance(r.get("evidence"), dict) else {}
        res = REG.evaluate(rule, evidence, applicable=applicable,
                           satisfied_when=(lambda e, rr=r: rr.get("satisfied")),
                           reviewer=r.get("reviewer"))
        res["section"] = section
        results.append(res)
    counts: dict[str, int] = {}
    for res in results:
        counts[res["result"]] = counts.get(res["result"], 0) + 1
    return {
        "measure": "a11_conformance",
        "a11_edition": edition,
        "subset_only": True,
        "rule_results": results,
        "configured_subset_result": counts,
        "global_a11_claim": None,
        "note": ("this result covers only the rules configured in the supplied register and is "
                 "not a statement about Circular A-11 as a whole"),
        "calibration_pending": True,
    }


def evms_reporting(structure: Mapping[str, Any], applicability: Mapping[str, Any] | None
                   ) -> dict[str, Any]:
    """
    8.4 EVMS REPORTING COMPLIANCE MONITOR. APPLICABILITY COMES FIRST.

        ReportingDelayDays  = ReceivedDate - DueDate           (where both exist)
        CompletenessFraction = ArtifactsReceived / ArtifactsExpected

    If 8.2 says NOT_APPLICABLE this module returns NOT_APPLICABLE and CANNOT issue a reporting
    violation. If applicability is unresolved it returns INSUFFICIENT_EVIDENCE and CANNOT
    manufacture compliance. CPI and SPI are not read here and cannot establish anything.
    No traffic-light threshold is invented; the delay and the fraction are reported.
    """
    state = (applicability or {}).get("applicability")
    out: dict[str, Any] = dict(REG.FAR_34_201.identity())
    out.update({"measure": "evms_reporting", "evms_applicability": state,
                "calibration_pending": True})
    if state == REG.NOT_APPLICABLE:
        out.update({"result": REG.NOT_APPLICABLE,
                    "reason": ("EVMS is not applicable to this acquisition, so no reporting "
                               "conformance question arises and no violation is issued"),
                    "statement": REG.sentence(REG.FAR_34_201, REG.NOT_APPLICABLE)})
        return out
    if state != REG.APPLICABLE:
        out.update({"result": REG.INSUFFICIENT_EVIDENCE,
                    "reason": ("EVMS applicability is not established, so reporting conformance "
                               "is not assessed and no compliance is recorded"),
                    "statement": REG.sentence(REG.FAR_34_201, REG.INSUFFICIENT_EVIDENCE)})
        return out

    clause = structure.get("clause_id")
    cadence = structure.get("required_cadence")
    if not clause or not cadence:
        out.update({"result": REG.INSUFFICIENT_EVIDENCE,
                    "reason": ("the governing clause or the required reporting cadence is not "
                               "recorded, so conformance is not assessed"),
                    "statement": REG.sentence(REG.FAR_34_201, REG.INSUFFICIENT_EVIDENCE)})
        return out
    expected = structure.get("required_artifacts_expected")
    received = structure.get("required_artifacts_received")
    due = _date(structure.get("due_date"))
    got = _date(structure.get("received_date"))
    out.update({
        "clause_id": clause, "required_cadence": cadence,
        "minimum_federal_cadence": "monthly",
        "reporting_period": structure.get("reporting_period"),
        "due_date": structure.get("due_date"), "received_date": structure.get("received_date"),
        "required_artifacts_expected": expected, "required_artifacts_received": received,
        "exception": structure.get("exception"),
        "contract_version": structure.get("contract_version"),
        "provenance": structure.get("provenance"),
    })
    out["reporting_delay_days"] = (got - due).days if (due and got) else None
    if isinstance(expected, (int, float)) and expected > 0 and isinstance(received, (int, float)):
        out["completeness_fraction"] = received / expected
    else:
        out["completeness_fraction"] = None
    missing_report = got is None
    complete = (out["completeness_fraction"] == 1.0 and not missing_report
                and out["reporting_delay_days"] is not None and out["reporting_delay_days"] <= 0)
    if missing_report:
        out["result"] = REG.NOT_SATISFIED
        out["reason"] = "no report is recorded as received for this reporting period"
    elif complete:
        out["result"] = REG.SATISFIED
        out["reason"] = "the configured reporting cadence and artifact set were met"
    else:
        out["result"] = REG.NOT_SATISFIED
        out["reason"] = "the configured reporting cadence or artifact set was not met"
    out["statement"] = REG.sentence(REG.FAR_34_201, out["result"])
    return out


def modification_governance(structure: Mapping[str, Any]) -> dict[str, Any]:
    """
    8.5 CONTRACT MODIFICATION GOVERNANCE CHECK. AUTHORITY, PROCESS AND DOCUMENTATION.

    THIS IS NOT CATEGORY 4.6. There is NO COUNT in this result: 4.6 owns change frequency and
    magnitude exposure, and section 12 forbids using a change count as this module's result. What
    is assessed, per modification, is whether an authorized contracting officer executed it,
    whether the unilateral/bilateral distinction is honoured, and whether the governing written
    instrument and form rule are satisfied.

    SIGNATURE EXISTENCE IS NEVER AUTHORITY. `authority_evidence` is a separate required field
    from `signed_parties`, and a modification with signatures but no authority evidence is
    INSUFFICIENT_EVIDENCE, not satisfied.
    """
    mods = _rows(structure, "modifications", "a governed contract modification register")
    results = []
    for m in mods:
        federal = m.get("federal_context", structure.get("federal_context"))
        ev = {
            "modification_id": m.get("modification_id"),
            "executing_official": m.get("executing_official"),
            "authority_evidence": m.get("authority_evidence"),
            "modification_type": m.get("modification_type"),
            "signed_parties": m.get("signed_parties"),
            "sf30_applicable": m.get("sf30_applicable"),
            "written_instrument": m.get("written_instrument"),
        }
        authority = REG.evaluate(
            REG.FAR_43_102, ev, applicable=(True if federal else False),
            satisfied_when=lambda e: bool(e.get("authority_evidence")
                                          and e.get("executing_official")
                                          and e.get("authority_evidence") != "NONE"),
            reviewer=m.get("reviewer"))
        # A person with no contracting-officer authority fails the authority rule even when the
        # instrument is signed: the predicate above reads authority_evidence, never signatures.
        if authority["result"] == REG.SATISFIED and not m.get("officer_authority_current", True):
            authority["result"] = REG.NOT_SATISFIED
            authority["reason"] = ("the executing official is not recorded as a contracting "
                                   "officer acting within the scope of their authority")
            authority["statement"] = REG.sentence(REG.FAR_43_102, REG.NOT_SATISFIED)

        mtype = m.get("modification_type")
        type_rule = REG.evaluate(
            REG.FAR_43_103, ev, applicable=(True if federal else False),
            satisfied_when=lambda e: (
                None if e.get("modification_type") not in ("unilateral", "bilateral") else
                (bool(e.get("signed_parties")) and len(e.get("signed_parties") or []) >= 2)
                if e.get("modification_type") == "bilateral" else True),
            reviewer=m.get("reviewer"))

        sf30_applicable = m.get("sf30_applicable")
        form_rule = REG.evaluate(
            REG.FAR_43_301, ev,
            applicable=(None if sf30_applicable is None
                        else (True if (federal and sf30_applicable) else False)),
            satisfied_when=lambda e: bool(e.get("written_instrument")),
            reviewer=m.get("reviewer"))

        results.append({
            "modification_id": m.get("modification_id"),
            "contract_id": m.get("contract_id", structure.get("contract_id")),
            "regime": "FEDERAL" if federal else "NON_FEDERAL",
            "modification_type": mtype,
            "issue_date": m.get("issue_date"), "effective_date": m.get("effective_date"),
            "funding_evidence": m.get("funding_evidence"),
            "price_ceiling_status": m.get("price_ceiling_status"),
            "required_approvals": m.get("required_approvals"),
            "exceptions": m.get("exceptions"),
            "provenance": m.get("provenance"),
            "authority_check": authority,
            "type_check": type_rule,
            "form_check": form_rule,
        })
    return {
        "measure": "modification_governance",
        "modification_results": results,
        "contract_id": structure.get("contract_id"),
        "note": ("this module assesses modification authority, process and documentation; "
                 "change frequency and magnitude exposure are a different measure"),
        "calibration_pending": True,
    }


def quality_compliance(structure: Mapping[str, Any]) -> dict[str, Any]:
    """
    8.6 QUALITY COMPLIANCE INDEX. REQUIREMENT-BASED.

        QualityComplianceRate = SatisfiedApplicableAssessed / ApplicableAssessed   (denom > 0)

    UNASSESSED REQUIREMENTS DO NOT COUNT AS SATISFIED and do not enter the denominator either:
    they are reported separately, because a register with ninety unassessed requirements and ten
    satisfied ones is not ninety-percent compliant and is not ten-percent compliant; it is
    ten-of-ten with ninety outstanding, and the reader needs both numbers.

    CRITICAL EXCEPTIONS ARE NONCOMPENSATORY: one critical exception is returned in its own list
    and cannot disappear inside a 99% aggregate. No status threshold is invented (section 53).
    """
    # RUN 31, DEFECT 2A. A PROJECT MAY HOLD REAL QUALITY AUDIT EVIDENCE AND NO REQUIREMENT
    # REGISTER, and that combination must neither compute nor discard what it has. The old
    # implementation refused this project for the wrong reason entirely -- it required a
    # MEETING-MINUTE deficiency mention before it would look at the audit at all -- so a project
    # with a genuine Quality Audit Report abstained because nobody discussed deficiencies.
    #
    # An audit score, a findings count and a critical-findings count are SUMMARIES. None of them
    # establishes the applicable, assessed and satisfied requirement populations this rate is
    # defined over, and section 13 forbids substituting a summary for a denominator. So the rate
    # is NOT estimated and the evidence is REPORTED, which is the honest partial disposition.
    if "requirements" not in structure and structure.get("recorded_audit_evidence"):
        return {
            "measure": "quality_compliance",
            "quality_compliance_rate": None,
            "disposition": "NOT_ESTIMABLE",
            "reason": ("the project's Quality Audit evidence is recorded below, but it "
                       "establishes no applicable, assessed and satisfied requirement "
                       "population, so no compliance rate is measurable and none is estimated"),
            "recorded_audit_evidence": dict(structure["recorded_audit_evidence"]),
            "applicable_assessed": 0, "satisfied": 0,
            "unassessed_applicable": [], "critical_exceptions": [],
            "register_id": structure.get("register_id"),
            "rule": REG.FAR_46_2.identity(),
            "calibration_pending": True,
        }
    reqs = _rows(structure, "requirements", "a governed quality requirement register")
    applicable_assessed, satisfied, unassessed, critical_exceptions = [], [], [], []
    for r in reqs:
        rid = r.get("requirement_id")
        if r.get("applicable") is False:
            continue
        if not r.get("assessed"):
            unassessed.append(rid)
            continue
        applicable_assessed.append(rid)
        if r.get("satisfied"):
            satisfied.append(rid)
        else:
            if r.get("criticality") in ("critical", "high"):
                critical_exceptions.append({
                    "requirement_id": rid, "criticality": r.get("criticality"),
                    "source": r.get("source"), "status": r.get("status"),
                    "corrective_action": r.get("corrective_action"),
                    "period": r.get("period"), "provenance": r.get("provenance"),
                })
    out = {
        "measure": "quality_compliance",
        "applicable_assessed": len(applicable_assessed),
        "satisfied": len(satisfied),
        "unassessed_applicable": unassessed,
        "critical_exceptions": critical_exceptions,
        "register_id": structure.get("register_id"),
        "register_version": structure.get("register_version"),
        "rule": REG.FAR_46_2.identity(),
        "calibration_pending": True,
    }
    if not applicable_assessed:
        out.update({"quality_compliance_rate": None, "disposition": "NOT_ESTIMABLE",
                    "reason": ("no applicable quality requirement has been assessed, so no "
                               "compliance rate is measurable and none is estimated")})
        return out
    out["quality_compliance_rate"] = len(satisfied) / len(applicable_assessed)
    out["disposition"] = "MEASURED"
    return out


def safety_performance(structure: Mapping[str, Any]) -> dict[str, Any]:
    """
    8.7 SAFETY PERFORMANCE INDEX. TWO DISTINCT FAMILIES, NEVER AVERAGED.

    LAGGING, the OSHA identity exactly as supplied:

        IncidenceRate = RecordableCases * 200000 / EmployeeHoursWorked

    Zero employee hours ABSTAINS with INVALID_DENOMINATOR; hours are never fabricated, and a
    meeting-minute incident MENTION is never an incidence-rate numerator (section 14). Where
    hours are absent the lagging branch abstains and the leading evidence still reports.

    LEADING: governed proactive measures, reported as they are recorded. There is NO COMBINED
    SCORE: section 14 forbids averaging the two families without a governed combination policy,
    and none is supplied, so none is computed.

    ZERO RECORDABLES ALONE NEVER PRODUCES A FAVOURABLE SYSTEM CLAIM. `system_claim` is always
    None here; the rate is a rate.
    """
    cases = structure.get("recordable_cases")
    hours = structure.get("employee_hours_worked")
    out: dict[str, Any] = {
        "measure": "safety_performance",
        "rule": REG.OSHA_INCIDENCE.identity(),
        "reporting_period": structure.get("reporting_period"),
        "provenance": structure.get("provenance"),
        "system_claim": None,
        "calibration_pending": True,
    }
    if not isinstance(cases, (int, float)) or not isinstance(hours, (int, float)):
        out.update({"incidence_rate": None, "lagging_disposition": "ABSTAIN_NO_EXPOSURE_DATA",
                    "lagging_reason": ("recordable cases and employee hours worked are not both "
                                       "recorded, so no exposure-normalised rate is computed and "
                                       "no substitute is used")})
    elif hours <= 0:
        out.update({"incidence_rate": None, "lagging_disposition": "INVALID_DENOMINATOR",
                    "lagging_reason": ("no employee hours worked are recorded for this period, "
                                       "so an exposure-normalised rate has no denominator")})
    else:
        out.update({"recordable_cases": cases, "employee_hours_worked": hours,
                    "incidence_rate": cases * 200000 / hours,
                    "lagging_disposition": "MEASURED"})
    leading = structure.get("leading_indicators")
    if isinstance(leading, list) and leading:
        out["leading_indicators"] = [
            {"indicator": l.get("indicator"), "value": l.get("value"),
             "period": l.get("period"), "provenance": l.get("provenance")}
            for l in leading if isinstance(l, dict)]
        out["leading_disposition"] = "RECORDED"
    else:
        out["leading_indicators"] = []
        out["leading_disposition"] = "ABSTAIN_NO_LEADING_EVIDENCE"
    severe = structure.get("severe_events")
    out["severe_events"] = list(severe) if isinstance(severe, list) else []
    # THE DOCUMENT-STATED RATE IS CARRIED, LABELLED, AND NEVER USED AS THE MEASUREMENT.
    # Executing `extraction_merge.emit_observations` proved a rate asserted by a document is
    # emitted unchecked -- 99.9 survived beside a recorded 3-cases/200,000-hours pair -- so it
    # cannot stand as an exposure-normalised measurement. It is still EVIDENCE, and dropping it
    # would hide a disagreement between what a document claims and what its own figures imply,
    # so it travels out under a name that says exactly what it is.
    stated = structure.get("document_stated_incident_rate")
    out["document_stated_incident_rate"] = stated
    out["document_stated_rate_note"] = (
        "a rate asserted by the source document; it is recorded as a claim and is not used as "
        "the exposure-normalised incidence rate, which is computed from the recordable cases "
        "and employee hours worked" if stated is not None else None)
    if stated is not None and out.get("incidence_rate") is not None:
        out["document_stated_rate_agrees"] = abs(float(stated) - out["incidence_rate"]) < 1e-9
    else:
        out["document_stated_rate_agrees"] = None
    out["combined_index"] = None
    out["combined_index_reason"] = (
        "no governed policy for combining leading and lagging safety evidence is supplied, so "
        "no combined safety score is produced")
    return out


def environmental_compliance(structure: Mapping[str, Any]) -> dict[str, Any]:
    """
    8.8 ENVIRONMENTAL COMPLIANCE RATE. APPLICABILITY COMES FIRST.

        EnvironmentalComplianceRate = SatisfiedApplicableAssessed / ApplicableAssessed

    EPA CGP IS NOT ASSUMED TO APPLY. The permitting authority is read from the evidence and may
    be EPA, state, tribal, local or another authority; where it is not established, conformance
    is NOT assessed. Section 15 forbids hard-coding EPA applicability and this function has no
    branch that could.

    Unassessed applicable requirements never count as satisfied, and a critical permit violation
    is returned separately and noncompensatorily.
    """
    jurisdiction = structure.get("jurisdiction")
    authority = structure.get("permitting_authority")
    out: dict[str, Any] = {
        "measure": "environmental_compliance",
        "site_id": structure.get("site_id"), "jurisdiction": jurisdiction,
        "permitting_authority": authority,
        "permit_id": structure.get("permit_id"),
        "permit_version": structure.get("permit_version"),
        "operator_status": structure.get("operator_status"),
        "provenance": structure.get("provenance"),
        "calibration_pending": True,
    }
    if authority == "EPA":
        out["rule"] = REG.EPA_CGP_2022.identity()
    else:
        out["rule"] = None
        out["rule_note"] = ("the permitting authority for this site is not EPA, so the EPA "
                            "Construction General Permit is not the governing instrument here")
    # RUN 31 PASS 2. THE REAL EXTRACTED EVIDENCE TRAVELS OUT WITH THE REFUSAL. A document-stated
    # compliance rate and a reported violations count are EVIDENCE; they are simply not a
    # requirement register, and neither establishes the jurisdiction and permitting authority
    # that must be settled before conformance is assessed. Dropping them would discard what the
    # project actually holds; using them as a rate would invent regulatory applicability. Both
    # are refused, so they are carried under names that say exactly what they are.
    recorded = structure.get("recorded_environmental_evidence")
    if recorded:
        out["recorded_environmental_evidence"] = dict(recorded)
        out["recorded_evidence_note"] = (
            "a rate asserted by the source document and a reported violations count; neither is "
            "an applicable/assessed/satisfied requirement population, so neither is used as the "
            "environmental compliance rate")
    if not authority or not jurisdiction:
        out.update({"environmental_compliance_rate": None,
                    "disposition": "APPLICABILITY_NOT_ESTABLISHED",
                    "reason": ("the jurisdiction and permitting authority for this site are not "
                               "established, so environmental conformance is not assessed"),
                    "critical_violations": []})
        return out
    reqs = structure.get("requirements")
    if not isinstance(reqs, list) or not reqs:
        out.update({"environmental_compliance_rate": None, "disposition": "NOT_ESTIMABLE",
                    "reason": "no applicable environmental requirement register is recorded",
                    "critical_violations": []})
        return out
    applicable_assessed, satisfied, unassessed, critical = [], [], [], []
    for r in reqs:
        if not isinstance(r, dict) or r.get("applicable") is False:
            continue
        rid = r.get("requirement_id")
        if not r.get("assessed"):
            unassessed.append(rid)
            continue
        applicable_assessed.append(rid)
        if r.get("satisfied"):
            satisfied.append(rid)
        elif r.get("criticality") in ("critical", "high"):
            critical.append({"requirement_id": rid, "criticality": r.get("criticality"),
                             "source": r.get("source"),
                             "corrective_action": r.get("corrective_action")})
    out.update({"applicable_assessed": len(applicable_assessed), "satisfied": len(satisfied),
                "unassessed_applicable": unassessed, "critical_violations": critical})
    if not applicable_assessed:
        out.update({"environmental_compliance_rate": None, "disposition": "NOT_ESTIMABLE",
                    "reason": ("no applicable environmental requirement has been assessed, so "
                               "no compliance rate is measurable")})
        return out
    out["environmental_compliance_rate"] = len(satisfied) / len(applicable_assessed)
    out["disposition"] = "MEASURED"
    return out


def contractor_assessment(structure: Mapping[str, Any]) -> dict[str, Any]:
    """
    8.9 CONTRACTOR PERFORMANCE ASSESSMENT SIGNAL. GOVERNED OFFICIAL-ASSESSMENT INGESTION.

    An INTERNAL assessment is labelled internal and can NEVER carry the CPARS label: `is_cpars`
    is True only when the source system is CPARS AND the record carries an official assessment
    id, and `label` is derived from that rather than supplied. Section 16 forbids labelling an
    internal project score as CPARS or as an official past-performance rating.

    FACTOR-LEVEL EVIDENCE IS PRESERVED and the worst/critical factor is returned separately. No
    aggregation happens unless a governed aggregation policy is supplied, because section 53
    forbids inventing contractor-assessment weights.
    """
    source = structure.get("source_system")
    assessment_id = structure.get("assessment_id")
    factors = structure.get("factor_ratings")
    out: dict[str, Any] = {
        "measure": "contractor_assessment",
        "rule": REG.FAR_42_15.identity(),
        "source_system": source, "assessment_id": assessment_id,
        "contract_id": structure.get("contract_id"),
        "assessment_period": structure.get("assessment_period"),
        "status": structure.get("status"),
        "factor_definitions_version": structure.get("factor_definitions_version"),
        "narratives": structure.get("narratives"),
        "contractor_comments_state": structure.get("contractor_comments_state"),
        "agency_review_state": structure.get("agency_review_state"),
        "reviewer": structure.get("reviewer"),
        "data_origin": structure.get("data_origin"),
        "provenance": structure.get("provenance"),
        "calibration_pending": True,
    }
    is_cpars = bool(source == "CPARS" and assessment_id)
    out["is_official_cpars_record"] = is_cpars
    out["label"] = ("CPARS past-performance record" if is_cpars
                    else "internal Contractor Performance Assessment Signal")
    if not isinstance(factors, list) or not factors:
        out.update({"disposition": "ABSTAIN_NO_GOVERNED_ASSESSMENT",
                    "reason": ("no governed official or internal contractor assessment with "
                               "factor ratings is recorded, so no signal is produced"),
                    "factor_ratings": [], "worst_factor": None, "aggregate": None})
        return out
    rows = [{"factor": f.get("factor"), "rating": f.get("rating"),
             "narrative": f.get("narrative"), "critical": bool(f.get("critical"))}
            for f in factors if isinstance(f, dict)]
    order = structure.get("rating_order")
    worst = None
    if isinstance(order, list) and order:
        ranked = [r for r in rows if r["rating"] in order]
        if ranked:
            worst = min(ranked, key=lambda r: order.index(r["rating"]))
    critical_rows = [r for r in rows if r["critical"]]
    out.update({
        "factor_ratings": rows,
        "worst_factor": worst,
        "critical_factors": critical_rows,
        "rating_order": order,
        "aggregate": None,
        "aggregate_reason": ("no governed aggregation policy for contractor assessment factors "
                             "is supplied, so no averaged rating is produced and the factor "
                             "level evidence stands"),
        "disposition": "MEASURED",
    })
    return out


def abm_governance(structure: Mapping[str, Any], *, signal_eligible: bool,
                   signal_abstaining: bool) -> dict[str, Any]:
    """
    8.1 AGENT-BASED GOVERNANCE MODEL. Builds the model from the governed structure and RUNS it.

    Everything real happens in `abm.py`: agents, states, messages, a clock, deterministic event
    ordering and the authority matrix. This function exists so the production runner has one
    canonical entry and so the ABM's structural refusal surfaces as an abstention rather than as
    a traceback.
    """
    model = model_from(structure, signal_eligible=signal_eligible,
                       signal_abstaining=signal_abstaining)
    terminal = model.run()
    return {
        "measure": "abm_governance",
        "action_class": model.env.action_class,
        "terminal_state": terminal,
        "final_time": model.env.clock,
        "agents": [{"agent_id": a.agent_id, "role": a.role, "state": a.state,
                    "response_latency": a.response_latency,
                    "messages_sent": len(a.outbox), "messages_received": len(a.inbox)}
                   for a in model.agents.values()],
        "authority_matrix": [
            {"action_class": r.action_class, "permitted_recommender": r.permitted_recommender,
             "required_approver": r.required_approver,
             "contractor_response_required": r.contractor_response_required,
             "procedural_requirement": r.procedural_requirement,
             "evidence_requirement": r.evidence_requirement}
            for r in model.env.matrix.rules.values()],
        "state_history": model.history,
        "deterministic": True,
        "stochastic_latency": False,
        "calibration_pending": True,
    }
