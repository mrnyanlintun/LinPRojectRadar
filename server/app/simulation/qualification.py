"""
The evidence qualification object (the category nine question), and nothing more than the
evidence in this repository can actually answer.

WHAT THIS FILE IS. Run 11 audited what a qualification of the evidence behind one project period
could honestly say and found three answerable questions and three that are not answerable here:

  ANSWERABLE   are the inputs a module declares as required actually present
  ANSWERABLE   is a canonical method's defining structure actually present
  ANSWERABLE   does this reporting period apply to this project at all
  PARTLY       provenance: a document TYPE is recorded per field, never a document identity or
               version, so a field cannot be traced to the artefact that produced it
  PARTLY       timeliness: the period cutoff bounds every computation, but there is no per-field
               as-of date, so a stale field inside a current period is undetectable
  NOT AT ALL   revision resolution: nothing joins a document revision to the field a module reads

THE RULE. Each of those is a SEPARATE, NAMED dimension carrying its own state. There is no
composite number anywhere in this file, and there must never be one: a single score would let a
known gap and a measured strength cancel, and a reader could not tell which they were looking at.
For the same reason nothing here converts an unknown into a favourable state; the states for the
three unanswerable dimensions are the honest PARTIAL and NOT_ESTIMABLE, not a penalty and not a
pass.

WHAT MAY HARD GATE, AND WHAT MAY NOT. Only the three answerable dimensions can affect execution,
and they do it through the abstention behaviour that ALREADY exists rather than a new one: a
module missing a required input, or missing its canonical structure, already abstains through
`models.eligible` and `canonical`, and this file only reports that it did. Provenance, timeliness
and revision resolution are METADATA. They never gate, they never subtract, and they never become
a number. A project cannot be made to look better by anything in this file, because nothing here
feeds fusion, voting, a band boundary or a status.
"""

from __future__ import annotations

from typing import Any

from .canonical import CANONICAL_STRUCTURE_KEYS
from .registry import DISABLED_CONCEPT_ONLY, registry_index

#: Bumped when the SHAPE or the MEANING of a dimension changes, never for a wording change.
QUALIFICATION_VERSION = "cat9-qual-v1"

# Controlled states. PASS/PARTIAL/FAIL/NOT_APPLICABLE/NOT_ESTIMABLE, matching the vocabulary the
# repository already uses for a coefficient that cannot be estimated (fusion.NOT_ESTIMABLE_*).
PASS = "PASS"
PARTIAL = "PARTIAL"
FAIL = "FAIL"
NOT_APPLICABLE = "NOT_APPLICABLE"
NOT_ESTIMABLE = "NOT_ESTIMABLE"

QUALIFICATION_STATES = (PASS, PARTIAL, FAIL, NOT_APPLICABLE, NOT_ESTIMABLE)

#: The reasons carried on the two dimensions this repository cannot answer. Stated once, so a
#: reader of the object and a reader of this file cannot be told two different things.
REVISION_RESOLUTION_REASON = (
    "No revision lineage is joined to the field a module reads. Document versioning exists at "
    "the document level and is not resolved to a field, and upload order is not evidence of "
    "which revision is current, so the revision state is not estimable rather than assumed."
)
PROVENANCE_PARTIAL_REASON = (
    "A document type is recorded for each sourced field. No document identity and no document "
    "version is recorded, so a field cannot be traced to the artefact that produced it."
)
TIMELINESS_PARTIAL_REASON = (
    "The reporting period cutoff bounds every computation. No per-field as-of date is recorded, "
    "so a field that is stale inside an applicable period cannot be detected."
)


def _module_ids_for(compute_result: dict[str, Any]) -> tuple[set[str], dict[str, str]]:
    computed = {r["module_id"] for r in compute_result.get("modules", [])}
    abstained = {r["module_id"]: (r.get("abstention_reason_code") or "")
                 for r in compute_result.get("abstained", [])}
    return computed, abstained


def _required_inputs_dimension(abstained: dict[str, str]) -> tuple[str, list[str]]:
    """
    Did any module that was actually allowed to run abstain for want of what it requires? The
    answer is read off the abstentions the run already produced, not recomputed here: one place
    decides what a module requires, and it is the module.

    EVERY non-disabled abstention counts, not only the ones carrying a machine reason code. The
    code is present on the modules the later runs corrected and absent on the rest, so counting
    only coded abstentions would report a clean required-input state on a run where a dozen
    modules went silent for want of their inputs. That would be the exact failure this object
    exists to prevent: making incomplete evidence look healthier than it is. A module whose
    defining structure is absent is reported on the canonical dimension instead, so no module is
    counted twice.
    """
    missing = sorted(mid for mid in abstained
                     if mid not in DISABLED_CONCEPT_ONLY
                     and mid not in CANONICAL_STRUCTURE_KEYS)
    return (PASS if not missing else PARTIAL), missing


def _canonical_dimension(si: dict, abstained: dict[str, str]) -> tuple[str, list[str]]:
    missing = sorted(mid for mid, key in CANONICAL_STRUCTURE_KEYS.items()
                     if not si.get(key))
    return (PASS if not missing else PARTIAL), missing


def _period_applicability(period: str | None, period_cutoff: Any) -> str:
    if not period or period_cutoff is None:
        return NOT_APPLICABLE
    return PASS


def _provenance(si: dict) -> tuple[str, dict[str, Any]]:
    sources = si.get("sources") or {}
    typed = 0
    identified = 0
    for key in sources:
        src = sources[key]
        entry = src[-1] if isinstance(src, list) else src
        if not isinstance(entry, dict):
            continue
        if entry.get("docType"):
            typed += 1
        # Recorded only if the repository ever gains a per-field document identity. It does not
        # have one today, so this stays zero and the dimension stays PARTIAL rather than PASS.
        if entry.get("documentId") and entry.get("documentVersion"):
            identified += 1
    evidence = {
        "fields_with_source_type": typed,
        "fields_with_document_identity_and_version": identified,
        "reason": PROVENANCE_PARTIAL_REASON,
    }
    if not sources:
        return NOT_ESTIMABLE, {**evidence, "reason":
                               "No source record accompanies this period's fields."}
    if identified and identified == typed:
        return PASS, evidence
    return PARTIAL, evidence


def _timeliness(si: dict, period_cutoff: Any) -> tuple[str, dict[str, Any]]:
    if period_cutoff is None:
        return NOT_ESTIMABLE, {"reason": "No reporting period cutoff was supplied."}
    sources = si.get("sources") or {}
    dated = 0
    for key in sources:
        src = sources[key]
        entry = src[-1] if isinstance(src, list) else src
        if isinstance(entry, dict) and entry.get("asOf"):
            dated += 1
    basis = {
        "period_cutoff": str(period_cutoff),
        "fields_with_as_of_date": dated,
        "reason": TIMELINESS_PARTIAL_REASON,
    }
    if sources and dated == len(sources):
        return PASS, basis
    return PARTIAL, basis


def _overall(required_status: str, canonical_status: str, period_status: str,
             provenance_status: str, timeliness_status: str,
             revision_status: str) -> str:
    """
    The overall state is the WEAKEST of the dimensions, chosen by rank, never averaged and never
    scored. It exists so a caller that reads one field cannot read a healthier picture than the
    dimensions hold; it can never be better than any dimension.
    """
    if period_status == NOT_APPLICABLE:
        return NOT_APPLICABLE
    states = (required_status, canonical_status, period_status,
              provenance_status, timeliness_status, revision_status)
    for worst in (FAIL, NOT_ESTIMABLE, PARTIAL):
        if worst in states:
            return worst
    return PASS


def build_qualification(si: dict, compute_result: dict[str, Any], *,
                        project_id: str | None,
                        reporting_period: str | None,
                        period_cutoff: Any,
                        generated_at: str | None = None) -> dict[str, Any]:
    """
    The qualification object for one project and one reporting period.

    `generated_at` is passed in rather than read from the clock, so the same evidence produces
    the same object on any day it is built, exactly as every module in this layer does.
    """
    if not isinstance(si, dict) or not isinstance(compute_result, dict):
        # A malformed input is refused as NOT_ESTIMABLE rather than defaulted to anything
        # favourable, and it carries no dimension at all.
        return {
            "project_id": project_id,
            "reporting_period": reporting_period,
            "qualification_version": QUALIFICATION_VERSION,
            "overall_qualification_state": NOT_ESTIMABLE,
            "malformed_input": True,
            "generated_at": generated_at,
        }

    _computed, abstained = _module_ids_for(compute_result)
    required_status, missing_required = _required_inputs_dimension(abstained)
    canonical_status, missing_canonical = _canonical_dimension(si, abstained)
    period_status = _period_applicability(reporting_period, period_cutoff)
    provenance_status, provenance_evidence = _provenance(si)
    timeliness_status, timeliness_basis = _timeliness(si, period_cutoff)
    revision_status = NOT_ESTIMABLE

    return {
        "project_id": project_id,
        "reporting_period": reporting_period,
        "evidence_package": compute_result.get("scenario_id"),
        "qualification_version": QUALIFICATION_VERSION,
        "required_inputs_status": required_status,
        "missing_required_inputs": missing_required,
        "canonical_structure_status": canonical_status,
        "missing_canonical_structures": missing_canonical,
        "period_applicability_status": period_status,
        "provenance_status": provenance_status,
        "provenance_evidence": provenance_evidence,
        "timeliness_status": timeliness_status,
        "timeliness_basis": timeliness_basis,
        "revision_resolution_status": revision_status,
        "revision_resolution_reason": REVISION_RESOLUTION_REASON,
        "overall_qualification_state": _overall(
            required_status, canonical_status, period_status,
            provenance_status, timeliness_status, revision_status),
        "generated_at": generated_at,
    }


def qualification_for_stored_result(*, signal_inputs, module_results, abstained,
                                    project_id, period, period_cutoff,
                                    evidence_package=None) -> dict[str, Any]:
    """
    The same object, derived at READ time from a stored result row.

    Derived rather than stored so no column and no migration is added, and so a row written
    before this run answers exactly as one written after it. The one function above does all the
    deciding; this only reshapes a row into what it reads.
    """
    return build_qualification(
        signal_inputs if isinstance(signal_inputs, dict) else None,
        {"modules": module_results or [], "abstained": abstained or [],
         "scenario_id": evidence_package},
        project_id=project_id,
        reporting_period=period,
        period_cutoff=period_cutoff,
        generated_at=None,
    )


def module_qualification(si: dict, module_id: str) -> dict[str, Any]:
    """
    The per-module face of the same object: what a single named method can inspect before it
    computes. It reports; it does not decide. The decision stays where it already is.
    """
    index = registry_index()
    key = CANONICAL_STRUCTURE_KEYS.get(module_id)
    return {
        "module_id": module_id,
        "qualification_version": QUALIFICATION_VERSION,
        "canonical_structure_required": key is not None,
        "canonical_structure_status": (
            NOT_APPLICABLE if key is None else (PASS if si.get(key) else FAIL)),
        "registered": module_id in index,
    }
