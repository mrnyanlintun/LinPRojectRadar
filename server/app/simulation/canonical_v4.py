"""
THE v4 CANONICAL METHOD LAYER FOR CATEGORIES 4 AND 5.

WHY THIS FILE EXISTS. The supervisory method contract supplied for Run 29 states, for each of the
ten Category-4 targets and the eight Category-5 targets, the canonical method that module is
named for, the evidence or model structure the method is defined on, and a hand-checkable known
answer. Run 27 established that most of those eighteen modules were computing a transparent proxy
because the defining structure was not in the platform at all: dispute escalation was a weighted
sum of a request count, a change count and a document risk score; specification conflict density
was a document risk score multiplied by the square root of a request count; discrete event
simulation was the reciprocal of an interruption term built from two indices. This file supplies
the structures and the canonical arithmetic, and the module runners in models.py and models_doc.py
call into it.

THE RULES THIS FILE ENFORCES are the v3 rules, unchanged, because the failure they prevent is the
same one.

1. A canonical method computes ONLY from its defining structure. When the structure is absent the
   caller ABSTAINS -- Not Estimable -- and reports no substitute figure. There is no proxy
   fallback anywhere below. In particular nothing here reads `docRiskScore`, `rfiCount`,
   `changeOrderCount`, `cpi` or `spi`: a dispute is not proved by a request count, a queue rate is
   not inferred from an activity count, and a DES event list is not inferred from progress.
2. NO BAND IS INVENTED. Every function here returns numbers and nothing else. The caller emits the
   number with calibration pending and asserts no colour wherever the v2 band was drawn over a
   different quantity. Run 33 owns calibration.
3. NOTHING HERE READS A FILE, A CLOCK OR A DATABASE. Every structure arrives on the caller's
   signal inputs, exactly as every scalar does, so no operational path can reach a fixture.
4. NOTHING HERE IS DERIVED FROM THE v2 IMPLEMENTATION. Each function was written from the supplied
   contract; the oracles in server/tools/test_run29_canonical_oracles.py carry the contract's own
   numbers, not numbers read back out of this file.
5. PROVENANCE TRAVELS. Every structure carries the source of its own figures and every result
   carries it back out, because Run 31 implements the Category-9 qualification gate over these
   same rows and cannot qualify what has no lineage. Run 29 does not close a LINEAGE finding.

THE 5.2 / 5.3 LINEAGE RULE, which is the one parsimony decision in Run 29's scope. Tornado Risk
Ranking does not create a second evidence body. `tornado_ranking` takes the OUTPUT DICTIONARY of
`sensitivity_analysis` and nothing else -- it has no access to the structure, to the response
model or to the signal inputs -- so it is structurally incapable of computing an independent
result. Its lineage names the sensitivity model it was derived from.
"""

from __future__ import annotations

import math
from datetime import date
from typing import Any, Sequence

from .canonical import StructureAbsent
from .canonical_v3 import _f, _provenance, _rows
from .rng import num

# =================================================================================================
# THE GOVERNED v4 STRUCTURES.
#
# One structure per shared need. `sensitivityModel` serves BOTH A5.2 and A5.3, which is the
# parsimony decision the contract makes: the tornado ranks what the sensitivity computed.
# =================================================================================================

#: Module id -> the signal-inputs key carrying its defining v4 structure.
V4_STRUCTURE_KEYS: dict[str, str] = {
    "A4.1": "documentRiskEvidence",
    "A4.2": "rfiEventLog",
    "A4.3": "submittalDecisionRegister",
    "A4.4": "ncrExposureRecord",
    "A4.5": "weatherImpactEvents",
    "A4.6": "changeEventRegister",
    "A4.7": "claimDisputeRegister",
    "A4.8": "subcontractorAssessments",
    "A4.9": "procurementItems",
    "A4.10": "specificationConflictRegister",
    "A5.1": "dsmDependencyModel",
    "A5.2": "sensitivityModel",
    "A5.3": "sensitivityModel",
    "A5.4": "scenarioSet",
    "A5.5": "systemDynamicsModel",
    "A5.6": "queueModel",
    "A5.7": "agentSupplyChainModel",
    "A5.8": "desProcessModel",
}

#: The plain words for what each structure IS. These reach a reader in the abstention sentence,
#: so they carry no module id, no key name and no reason code, per the naming rules.
V4_STRUCTURE_WORDS: dict[str, str] = {
    "A4.1": "a document risk evidence record: the passages read, what each was classified as, "
            "how severe and how confident that finding is, and which document it came from",
    "A4.2": "a register of requests for information as events, each with its own identity and "
            "the dates it was raised and answered, and the span of time the register covers",
    "A4.3": "a submittal decision register: each submittal, each revision of it, and the "
            "decision recorded against it on the project's own disposition list",
    "A4.4": "a nonconformance record with the exposure it is measured against: the "
            "nonconformances raised, and the inspections, hours or value they arose from",
    "A4.5": "a weather impact record: the weather events, the activities they stopped, the time "
            "actually lost, the allowance in the contract calendar, and the float on the path",
    "A4.6": "a change event register with the exposure it is measured over: each change, its "
            "type, cause and value, and the span of time or contract value it arose against",
    "A4.7": "a claim and dispute register: the project's own governed escalation process and the "
            "stage each issue has reached on it, with the dates it reached them",
    "A4.8": "a subcontractor performance assessment: each firm, the criteria it was rated "
            "against, the rating on each, who assessed it and the weights that were applied",
    "A4.9": "an item level procurement register: for each item, the date it is required on site, "
            "the date it is forecast to arrive, and the activity it feeds",
    "A4.10": "a specification conflict register: each identified conflict, the two places in the "
             "specification that disagree, whether it has been confirmed, and the exposure the "
             "conflicts are counted over",
    "A5.1": "a dependency matrix for the design: the parts of the design, which of them depend "
            "on which others and how strongly, and the rework the propagation starts from",
    "A5.2": "a sensitivity model: a named response function, the state it is evaluated at, and "
            "the inputs to be moved with the range each is moved across",
    "A5.3": "a sensitivity model: a named response function, the state it is evaluated at, and "
            "the inputs to be moved with the range each is moved across",
    "A5.4": "a scenario set: named scenarios, each stating every input it changes together, the "
            "reasoning behind it, and the response model they are all evaluated through",
    "A5.5": "a system dynamics rework model: the stock of work in the backlog, the work arriving "
            "and completed each step, and the share of completed work that returns as rework",
    "A5.6": "a queue model: the rate work arrives at, the rate it is served at, how many servers "
            "there are and the order they take work in",
    "A5.7": "an agent based supply chain model: the agents, the state each starts in, the rule "
            "each follows, who they are connected to, and the steps the model runs over",
    "A5.8": "a discrete event model: the entities and when they arrive, the resources that serve "
            "them, how long service takes, and the order simultaneous events are taken in",
}


def require_v4_structure(si: dict, module_id: str) -> dict:
    """The v4 structure, or StructureAbsent carrying the sentence the ledger will show."""
    key = V4_STRUCTURE_KEYS[module_id]
    words = V4_STRUCTURE_WORDS[module_id]
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


# ------------------------------------------------------------------------------ shared helpers


def _int(container: Any, field: str, words: str) -> int:
    v = _f(container, field, words)
    if v != int(v):
        raise StructureAbsent(
            f"The {words} provided for this project carries a count that is not a whole number, "
            f"so no reading is taken from it.")
    return int(v)


def _text(container: Any, field: str, words: str) -> str:
    value = str((container or {}).get(field) or "").strip()
    if not value:
        raise StructureAbsent(
            f"The {words} provided for this project is missing a description this method needs "
            f"to read it, so no reading is taken from it.")
    return value


def _day(container: Any, day_field: str, date_field: str, words: str) -> float:
    """
    A point in time as a day number.

    Two forms are accepted because two are genuinely in use: a whole day index counted from the
    project's own origin, which is how a schedule tool exports it, and a calendar date, which is
    how a register written by a person carries it. Nothing is inferred when neither is present.
    """
    raw = (container or {}).get(day_field)
    if raw is not None:
        v = num(raw, None)
        if v is None or not math.isfinite(v):
            raise StructureAbsent(
                f"The {words} provided for this project carries a day that is not a number, so "
                f"no reading is taken from it.")
        return float(v)
    iso = str((container or {}).get(date_field) or "").strip()
    if not iso:
        raise StructureAbsent(
            f"The {words} provided for this project does not carry the dates this method is "
            f"defined on, so no reading is taken from it.")
    try:
        parsed = date.fromisoformat(iso)
    except ValueError:
        raise StructureAbsent(
            f"A date in the {words} provided for this project is not a calendar date, so no "
            f"reading is taken from it.") from None
    return float(parsed.toordinal())


def _unique_ids(rows: Sequence[dict], field: str, words: str) -> list[str]:
    """
    Every entry has an identity and no two share one.

    BOTH HALVES MATTER. A blank identity means the entries cannot be told apart. A REPEATED
    identity means the same thing has been declared twice, and in a register that is counted --
    nonconformances, changes, conflicts, procurement items, queues, scenarios, entities -- the
    same event or item would then be counted twice. That is the double-counting fault the
    supplied contract names for procurement and for the request register, and it is refused here
    for every register rather than guarded in one place.
    """
    out = []
    seen: set[str] = set()
    for r in rows:
        ident = str(r.get(field) or "").strip()
        if not ident:
            raise StructureAbsent(
                f"An entry in the {words} provided for this project carries no identity, so the "
                f"entries cannot be told apart and no reading is taken from them.")
        if ident in seen:
            raise StructureAbsent(
                f"The {words} provided for this project declares the same entry twice, so it "
                f"would be counted twice, and no reading is taken from it.")
        seen.add(ident)
        out.append(ident)
    return out


# =================================================================================================
# 4.1 DOCUMENT RISK SCORE
#
# The contract is explicit that there is no universal scalar document risk score, and that three
# things must be kept apart: the accuracy of the extraction, the arithmetic of the aggregation,
# and the operational banding. This function does exactly ONE of those three -- the aggregation --
# and it refuses to do it at all unless every finding carries the traceability the other two
# depend on: the document it came from, the passage that was read, the class it was put in, a
# severity, a confidence and the version of the rule or model that put it there.
#
# A mathematically correct score does not prove that the extraction is accurate. Nothing here
# claims it does, and the result carries the coverage and the classifier version so the reader can
# see what the score rests on. Empirical precision and recall are Run 33's work; see section 9 of
# the supplied contract and the report.
# =================================================================================================

#: Aggregation rules this layer will perform. Named on the structure, never assumed, because two
#: different rules over the same findings give two different scores and a reader must know which.
_DOC_RISK_RULES = ("SEVERITY_CONFIDENCE_WEIGHTED_MEAN", "MAX_SEVERITY", "COVERAGE_WEIGHTED_MEAN")


def document_risk_evidence(structure: dict) -> dict[str, Any]:
    """
    The aggregated document risk score, and every finding it was formed from.

    ORACLE (contract 4.1 has no scalar oracle of its own; this is the arithmetic it names).
    Two findings under SEVERITY_CONFIDENCE_WEIGHTED_MEAN with severity 0.8 at confidence 1.0 and
    severity 0.4 at confidence 0.5 score (0.8*1.0 + 0.4*0.5) / (1.0 + 0.5) = 1.0/1.5 = 0.6667.
    """
    words = V4_STRUCTURE_WORDS["A4.1"]
    prov = _provenance(structure, words, "classifier_version", "taxonomy_id", "source")
    rule = _text(structure, "aggregation_rule", words).upper()
    if rule not in _DOC_RISK_RULES:
        raise StructureAbsent(
            "The document risk evidence provided for this project names a way of combining its "
            "findings that this platform does not perform, so no score is formed from it.")
    coverage = _f(structure, "coverage", words)
    if not 0 < coverage <= 1:
        raise StructureAbsent(
            "The document risk evidence provided for this project does not say what share of the "
            "documents was read, or says it read none of them, so no score is formed from it.")
    findings = _rows(structure, "findings", words)
    prepared = []
    for f in findings:
        prepared.append({
            "finding_id": _text(f, "finding_id", words),
            "document_id": _text(f, "document_id", words),
            "document_type": _text(f, "document_type", words),
            "evidence_span": _text(f, "evidence_span", words),
            "risk_class": _text(f, "risk_class", words),
            "candidate": _text(f, "extracted_candidate", words),
            "severity": _f(f, "severity", words),
            "confidence": _f(f, "confidence", words),
            "effective_date": str(f.get("effective_date") or ""),
        })
    for p in prepared:
        if not 0 <= p["severity"] <= 1 or not 0 <= p["confidence"] <= 1:
            raise StructureAbsent(
                "A finding in the document risk evidence provided for this project reports a "
                "severity or a confidence outside the range a share can occupy, so no score is "
                "formed from it.")
    if rule == "MAX_SEVERITY":
        score = max(p["severity"] for p in prepared)
    elif rule == "COVERAGE_WEIGHTED_MEAN":
        score = (sum(p["severity"] for p in prepared) / len(prepared)) * coverage
    else:
        weight = sum(p["confidence"] for p in prepared)
        if weight <= 0:
            raise StructureAbsent(
                "Every finding in the document risk evidence provided for this project is held "
                "with no confidence at all, so there is nothing to weight a score by.")
        score = sum(p["severity"] * p["confidence"] for p in prepared) / weight
    classes: dict[str, int] = {}
    for p in prepared:
        classes[p["risk_class"]] = classes.get(p["risk_class"], 0) + 1
    return {
        "risk_score": score,
        "aggregation_rule": rule,
        "coverage": coverage,
        "findings": prepared,
        "finding_count": len(prepared),
        "documents_cited": sorted({p["document_id"] for p in prepared}),
        "risk_classes": dict(sorted(classes.items())),
        "classifier_version": prov["classifier_version"],
        "taxonomy_id": prov["taxonomy_id"],
        "source": prov["source"],
        "empirical_validation": "PENDING_RUN_33",
    }


# =================================================================================================
# 4.2 RFI VELOCITY
# =================================================================================================


def rfi_velocity(structure: dict) -> dict[str, Any]:
    """
    Requests for information per unit of exposure time, from the events themselves.

    ORACLE (contract 4.2): twelve requests over thirty days is 0.4 per day, or twelve per
    standardised thirty day period.

    THE DOUBLE-COUNTING RULE the contract states in its own words: "Do not count revisions of the
    same cumulative register as new RFI events." A register uploaded monthly is CUMULATIVE -- the
    second upload repeats every row of the first -- so an event is identified by its own request
    identity and a repeated identity is one event, not two. Where two rows share an identity and
    disagree about their dates the register is refused rather than silently deduplicated to one of
    them, because which one is right is not this layer's decision to guess.
    """
    words = V4_STRUCTURE_WORDS["A4.2"]
    prov = _provenance(structure, words, "source", "register_id")
    exposure = _f(structure, "exposure_days", words)
    if exposure <= 0:
        raise StructureAbsent(
            "The request register provided for this project covers no span of time, so there is "
            "no exposure for a rate of requests to be measured over.")
    events = _rows(structure, "events", words)
    seen: dict[str, dict] = {}
    for e in events:
        ident = _text(e, "rfi_id", words)
        created = _day(e, "created_day", "created_date", words)
        record = {
            "rfi_id": ident,
            "created": created,
            "status": _text(e, "status", words).upper(),
            "topic": str(e.get("topic") or ""),
            "responsible_party": str(e.get("responsible_party") or ""),
            "reporting_period": e.get("reporting_period"),
            "response": (_day(e, "response_day", "response_date", words)
                         if (e.get("response_day") is not None or e.get("response_date"))
                         else None),
            "closed": (_day(e, "close_day", "close_date", words)
                       if (e.get("close_day") is not None or e.get("close_date"))
                       else None),
            "due": (_day(e, "due_day", "due_date", words)
                    if (e.get("due_day") is not None or e.get("due_date")) else None),
        }
        if ident in seen:
            prior = seen[ident]
            if (prior["created"], prior["response"], prior["closed"]) != (
                    record["created"], record["response"], record["closed"]):
                raise StructureAbsent(
                    "The request register provided for this project carries the same request "
                    "twice with different dates against it, so how many requests were raised "
                    "cannot be established and no rate is formed from it.")
            continue
        seen[ident] = record
    unique = sorted(seen.values(), key=lambda r: (r["created"], r["rfi_id"]))
    count = len(unique)
    open_states = {"OPEN", "PENDING", "AWAITING_RESPONSE"}
    relevant_open = [r for r in unique if r["status"] in open_states]
    as_of = _f(structure, "as_of_day", words) if structure.get("as_of_day") is not None else None
    overdue = None
    overdue_ratio = None
    if as_of is not None and all(r["due"] is not None for r in relevant_open):
        overdue = sum(1 for r in relevant_open if r["due"] < as_of)
        overdue_ratio = (overdue / len(relevant_open)) if relevant_open else None
    return {
        "events_counted": count,
        "rows_supplied": len(events),
        "duplicate_rows_collapsed": len(events) - count,
        "exposure_days": exposure,
        "rate_per_day": count / exposure,
        "rate_per_30_days": (count / exposure) * 30.0,
        "open_relevant": len(relevant_open),
        "overdue": overdue,
        "overdue_ratio": overdue_ratio,
        "source": prov["source"],
        "register_id": prov["register_id"],
    }


# =================================================================================================
# 4.3 SUBMITTAL REJECTION RATE
# =================================================================================================

#: The governed disposition list. A project states which of its own statuses maps to which of
#: these, on the structure, so nothing here silently merges "approved as noted" into "approved" or
#: "revise and resubmit" into "rejected". A status the project has not mapped is refused.
_SUBMITTAL_DISPOSITIONS = ("APPROVED", "APPROVED_AS_NOTED", "REVISE_AND_RESUBMIT", "REJECTED",
                           "FOR_RECORD", "WITHDRAWN")

#: Which of the governed dispositions count in the numerator, and which in the assessed
#: population. Withdrawn and for-record submittals were never assessed, so they are in neither.
_REJECTED_DISPOSITIONS = ("REJECTED",)
_ASSESSED_DISPOSITIONS = ("APPROVED", "APPROVED_AS_NOTED", "REVISE_AND_RESUBMIT", "REJECTED")


def submittal_rejection(structure: dict) -> dict[str, Any]:
    """
    Rejected decisions as a share of the assessed population.

    ORACLE (contract 4.3): three rejected of twenty assessed is 0.15.

    A DENOMINATOR MIXING THIS PERIOD'S DECISIONS WITH A CUMULATIVE BACKLOG IS INVALID, which the
    contract states outright, so every decision carries the period it was made in and the register
    declares the period the rate is being formed for. Decisions from other periods are excluded
    from both numerator and denominator rather than counted into one of them.
    """
    words = V4_STRUCTURE_WORDS["A4.3"]
    prov = _provenance(structure, words, "source", "taxonomy_version")
    period = structure.get("reporting_period")
    decisions = _rows(structure, "decisions", words)
    mapping_raw = structure.get("disposition_mapping")
    mapping = {}
    if isinstance(mapping_raw, dict):
        for k, v in mapping_raw.items():
            mapping[str(k).strip().upper()] = str(v or "").strip().upper()
    prepared = []
    for d in decisions:
        raw_status = _text(d, "disposition", words).upper()
        governed = mapping.get(raw_status, raw_status)
        if governed not in _SUBMITTAL_DISPOSITIONS:
            raise StructureAbsent(
                "The submittal register provided for this project records a decision this "
                "platform has no governed meaning for, and guessing which of approval, "
                "resubmission or rejection was meant would change the rate, so none is formed.")
        prepared.append({
            "submittal_id": _text(d, "submittal_id", words),
            "revision_id": _text(d, "revision_id", words),
            "disposition": governed,
            "reported_disposition": raw_status,
            "decision_day": _day(d, "decision_day", "decision_date", words),
            "reviewer": _text(d, "reviewer", words),
            "reporting_period": d.get("reporting_period"),
        })
    # A DECISION IS IDENTIFIED BY THE SUBMITTAL AND THE REVISION TOGETHER, because one submittal
    # legitimately carries several revisions and each is its own decision. The same submittal at
    # the same revision declared twice is one decision reported twice, and counting it twice
    # would move both sides of the share, so it is refused.
    _unique_ids([{"id": f'{p["submittal_id"]}|{p["revision_id"]}'} for p in prepared],
                "id", words)
    if period is not None:
        in_window = [p for p in prepared if p["reporting_period"] == period]
    else:
        in_window = prepared
    assessed = [p for p in in_window if p["disposition"] in _ASSESSED_DISPOSITIONS]
    rejected = [p for p in assessed if p["disposition"] in _REJECTED_DISPOSITIONS]
    if not assessed:
        raise StructureAbsent(
            "No submittal in the register provided for this project was assessed in the period "
            "being reported, so there is no population for a rejection share to be taken of.")
    if not 0 <= len(rejected) <= len(assessed):
        raise StructureAbsent(
            "More submittals are recorded rejected than were assessed, so the register does not "
            "describe one population and no rejection share is formed from it.")
    counts: dict[str, int] = {}
    for p in in_window:
        counts[p["disposition"]] = counts.get(p["disposition"], 0) + 1
    unique_submittals = {p["submittal_id"] for p in assessed}
    # RUN 106, GOAL THREE. THE FIRST-REVIEW POPULATION, WHICH IS A DIFFERENT POPULATION.
    #
    # The owner's Run 106 measure is FIRST-REVIEW rejection: submittals rejected or returned for
    # revision ON FIRST REVIEW, divided by submittals RECEIVING a first review. He states in
    # terms that later resubmittal outcomes are not in the denominator, because the measure is
    # first-pass document quality and not eventual cycles.
    #
    # `rejection_rate` above is the CONTRACT 4.3 quantity -- rejections over the whole assessed
    # decision population -- and it is not touched, not renamed and not rebanded. The first-review
    # share is computed BESIDE it, from the same rows, so the two quantities stay distinguishable
    # and nothing that reads the contract figure changes.
    #
    # THE FIRST REVIEW IS THE EARLIEST DECISION FOR A SUBMITTAL, by decision day and then by
    # revision identifier where a day is shared. Nothing is invented: a submittal with one
    # decision is its own first review, and the ordering is read off fields the register states.
    first: dict[str, dict[str, Any]] = {}
    for p in assessed:
        sid = p["submittal_id"]
        key = (p["decision_day"], str(p["revision_id"]))
        held = first.get(sid)
        if held is None or key < (held["decision_day"], str(held["revision_id"])):
            first[sid] = p
    first_rows = list(first.values())
    first_rejected = [p for p in first_rows if p["disposition"] in _REJECTED_DISPOSITIONS]
    return {
        "rejection_rate": len(rejected) / len(assessed),
        "first_review_rate": (len(first_rejected) / len(first_rows)) if first_rows else None,
        "first_review_rejected": len(first_rejected),
        "first_review_assessed": len(first_rows),
        "rejected": len(rejected),
        "assessed": len(assessed),
        "decisions_supplied": len(prepared),
        "unique_submittals": len(unique_submittals),
        "resubmission_cycles": len(assessed) - len(unique_submittals),
        "disposition_counts": dict(sorted(counts.items())),
        "reporting_period": period,
        "taxonomy_version": prov["taxonomy_version"],
        "source": prov["source"],
    }


# =================================================================================================
# 4.4 NCR RATE
# =================================================================================================


def ncr_rate(structure: dict) -> dict[str, Any]:
    """
    Nonconformances per unit of governed exposure.

    ORACLE (contract 4.4): four nonconformances over one hundred inspections is 0.04.

    NO EXPOSURE, NO NORMALISED RATE. The contract's words are "do not fabricate a normalized NCR
    rate", so an exposure unit and an exposure quantity are both required and neither is defaulted.
    Open count, age of open, severity and closure are tracked SEPARATELY and are not divided by
    each other, which is the defect the previous implementation was corrected for in an earlier
    run and which is not reintroduced here in a new shape.

    TWO NUMERATOR FORMS, AND WHY THE SECOND EXISTS. Run 29's closure decomposed the claim that no
    real corpus populates this structure, and found it false for this one measure: the
    nonconformance log already yields a COUNT of nonconformances raised in the period, and the
    inspection report already yields the number of items inspected, which is a governed exposure
    in the contract's own words. Both are extracted today and both reach the signal inputs. So a
    record may carry either

        `ncrs`      -- a list of nonconformance EVENTS, each with an identity, dates and a
                       severity, from which the count, the open backlog, the ages, the severity
                       mix and the closure rate are all derived; or
        `ncr_count` -- a COUNT that was extracted as a count, with no per-event detail.

    THE COUNT FORM FABRICATES NOTHING. It does not invent identities or dates to make a list out
    of a number: the quantities that need events are reported as ABSENT, `event_detail_available`
    is False, and the reader is told which. It is the same canonical quantity -- events over
    governed exposure -- from a thinner record, which is exactly the position Run 27 recorded for
    A4.2 and A4.3 and the position section 3 of the closure contract requires be taken wherever
    the corpus really holds the defining figures.
    """
    words = V4_STRUCTURE_WORDS["A4.4"]
    prov = _provenance(structure, words, "source")
    unit = _text(structure, "exposure_unit", words)
    quantity = _f(structure, "exposure_quantity", words)
    if quantity <= 0:
        raise StructureAbsent(
            "The nonconformance record provided for this project reports no exposure to measure "
            "its nonconformances against, so no rate is formed from it.")
    as_of = _f(structure, "as_of_day", words) if structure.get("as_of_day") is not None else None

    if structure.get("ncrs") is None and structure.get("ncr_count") is not None:
        # ---- THE COUNT FORM.
        count = _f(structure, "ncr_count", words)
        if count < 0 or count != int(count):
            raise StructureAbsent(
                "The nonconformance record provided for this project reports a count of "
                "nonconformances that is not a whole number at or above nought, so no rate is "
                "formed from it.")
        basis = _text(structure, "ncr_count_basis", words)
        open_ = num(structure.get("open_count"), None)
        closed = num(structure.get("closed_count"), None)
        if open_ is not None and open_ < 0:
            raise StructureAbsent(
                "A negative count of open nonconformances is not a measurable backlog, so no "
                "reading is taken from the record provided for this project.")
        return {
            "ncr_rate": int(count) / quantity,
            "ncr_count": int(count),
            "ncr_count_basis": basis,
            "event_detail_available": False,
            "exposure_unit": unit,
            "exposure_quantity": quantity,
            "open_count": int(open_) if open_ is not None else None,
            "closed_count": int(closed) if closed is not None else None,
            "reopened_count": None,
            "closure_rate": None,
            "mean_open_age_days": None,
            "max_open_age_days": None,
            "severity_counts": {},
            "source": prov["source"],
        }

    events = _rows(structure, "ncrs", words)
    prepared = []
    for e in events:
        issued = _day(e, "issue_day", "issue_date", words)
        closed_day = (_day(e, "close_day", "close_date", words)
                      if (e.get("close_day") is not None or e.get("close_date")) else None)
        if closed_day is not None and closed_day < issued:
            raise StructureAbsent(
                "A nonconformance in the record provided for this project is closed before it "
                "was raised, so the record does not describe one history and no rate is formed.")
        prepared.append({
            "ncr_id": _text(e, "ncr_id", words),
            "issue_day": issued,
            "close_day": closed_day,
            "reopened": bool(e.get("reopened")),
            "severity": _text(e, "severity", words).upper(),
            "reporting_period": e.get("reporting_period"),
        })
    _unique_ids(prepared, "ncr_id", words)
    open_ = [p for p in prepared if p["close_day"] is None]
    closed_ = [p for p in prepared if p["close_day"] is not None]
    severities: dict[str, int] = {}
    for p in prepared:
        severities[p["severity"]] = severities.get(p["severity"], 0) + 1
    ages = ([as_of - p["issue_day"] for p in open_] if as_of is not None else [])
    return {
        "ncr_rate": len(prepared) / quantity,
        "ncr_count": len(prepared),
        "ncr_count_basis": "nonconformance events carried on the record",
        "event_detail_available": True,
        "exposure_unit": unit,
        "exposure_quantity": quantity,
        "open_count": len(open_),
        "closed_count": len(closed_),
        "reopened_count": sum(1 for p in prepared if p["reopened"]),
        "closure_rate": (len(closed_) / len(prepared)) if prepared else None,
        "mean_open_age_days": (sum(ages) / len(ages)) if ages else None,
        "max_open_age_days": max(ages) if ages else None,
        "severity_counts": dict(sorted(severities.items())),
        "source": prov["source"],
    }


# =================================================================================================
# 4.5 WEATHER DAY IMPACT
# =================================================================================================


def weather_day_impact(structure: dict) -> dict[str, Any]:
    """
    The modelled schedule consequence of verified weather events, before recovery.

    ORACLE (contract 4.5): a verified weather event causing two lost days on a zero-float critical
    activity with no mitigation has a direct modelled path effect, before recovery logic, of two
    days.

    THE ARITHMETIC, stated so it is checkable. For each event the days actually lost are first
    absorbed by the weather allowance the contract calendar grants and still has remaining, then
    by the float available on the activity's path. What survives both is the direct effect on that
    path. Recovery and mitigation are reported separately and are NOT netted off the direct
    effect, because the contract asks for the effect "before recovery logic".

    WEATHER OCCURRENCE IS NOT SCHEDULE IMPACT, which is why an event with no activity, no path and
    no float figure is refused rather than counted: a raw count of weather days is not this method.
    """
    words = V4_STRUCTURE_WORDS["A4.5"]
    prov = _provenance(structure, words, "source", "weather_calendar_id")
    allowance_remaining = _f(structure, "allowance_days_remaining", words)
    if allowance_remaining < 0:
        raise StructureAbsent(
            "The weather record provided for this project reports a negative remaining weather "
            "allowance, so no impact is modelled from it.")
    events = _rows(structure, "events", words)
    per_path: dict[str, float] = {}
    prepared = []
    remaining = allowance_remaining
    for e in events:
        lost = _f(e, "actual_lost_days", words)
        if lost < 0:
            raise StructureAbsent(
                "A weather event in the record provided for this project reports a negative "
                "amount of lost time, so no impact is modelled from it.")
        path = _text(e, "schedule_path_id", words)
        row = {
            "event_id": _text(e, "event_id", words),
            "event_day": _day(e, "event_day", "event_date", words),
            "activity_id": _text(e, "activity_id", words),
            "schedule_path_id": path,
            "planned_work": str(e.get("planned_work") or ""),
            "actual_lost_days": lost,
            "available_float_days": _f(e, "available_float_days", words),
            "causal_evidence": _text(e, "causal_evidence", words),
            "mitigation_days": num(e.get("mitigation_days"), 0.0) or 0.0,
        }
        if row["available_float_days"] < 0:
            raise StructureAbsent(
                "A weather event in the record provided for this project is linked to an "
                "activity with negative float, so no impact is modelled from it.")
        absorbed_by_allowance = min(remaining, lost)
        remaining -= absorbed_by_allowance
        unabsorbed = lost - absorbed_by_allowance
        row["allowance_absorbed_days"] = absorbed_by_allowance
        prepared.append(row)
        per_path[path] = per_path.get(path, 0.0) + unabsorbed
    path_effect = {}
    floats = {}
    for row in prepared:
        floats.setdefault(row["schedule_path_id"], row["available_float_days"])
    for path, unabsorbed in per_path.items():
        path_effect[path] = max(0.0, unabsorbed - floats[path])
    for row in prepared:
        row["path_effect_days"] = path_effect[row["schedule_path_id"]]
    direct = max(path_effect.values()) if path_effect else 0.0
    return {
        "direct_path_effect_days": direct,
        "path_effect_days": dict(sorted(path_effect.items())),
        "events": prepared,
        "event_count": len(prepared),
        "total_lost_days": sum(r["actual_lost_days"] for r in prepared),
        "allowance_days_remaining_after": remaining,
        "mitigation_days_reported": sum(r["mitigation_days"] for r in prepared),
        "weather_calendar_id": prov["weather_calendar_id"],
        "source": prov["source"],
    }


# =================================================================================================
# 4.6 CHANGE ORDER FREQUENCY
# =================================================================================================


def change_frequency(structure: dict) -> dict[str, Any]:
    """
    Governed change events per unit of exposure, with magnitude reported separately.

    ORACLE (contract 4.6): six changes over one hundred and eighty days is 6/180 = 0.033333...
    changes per day, or one change per standardised thirty day period.

    FREQUENCY AND MAGNITUDE ARE NOT COMBINED. The contract forbids "one unnamed composite", which
    is exactly what the previous implementation formed by banding a raw count jointly with the
    percentage growth of the contract sum. Magnitude is the sum of the change values over the
    baseline contract value and is reported under its own name.
    """
    words = V4_STRUCTURE_WORDS["A4.6"]
    prov = _provenance(structure, words, "source")
    exposure = _f(structure, "exposure_days", words)
    if exposure <= 0:
        raise StructureAbsent(
            "The change register provided for this project covers no span of time, so there is "
            "no exposure for a frequency of changes to be measured over.")
    baseline = _f(structure, "baseline_contract_value", words)
    if baseline <= 0:
        raise StructureAbsent(
            "The change register provided for this project reports no baseline contract value, "
            "so the magnitude of its changes cannot be measured against anything.")
    events = _rows(structure, "changes", words)
    prepared = []
    for e in events:
        direction = _text(e, "direction", words).upper()
        if direction not in ("ADDITIVE", "DEDUCTIVE"):
            raise StructureAbsent(
                "A change in the register provided for this project does not say whether it adds "
                "to or takes away from the contract, so its value cannot be signed and no "
                "magnitude is formed from it.")
        value = _f(e, "value", words)
        if value < 0:
            raise StructureAbsent(
                "A change in the register provided for this project carries a negative value "
                "alongside the direction it is already signed by, so no magnitude is formed.")
        prepared.append({
            "change_id": _text(e, "change_id", words),
            "issue_day": _day(e, "issue_day", "issue_date", words),
            "change_type": _text(e, "change_type", words),
            "cause": _text(e, "cause", words),
            "value": value,
            "direction": direction,
            "signed_value": value if direction == "ADDITIVE" else -value,
            "reporting_period": e.get("reporting_period"),
        })
    _unique_ids(prepared, "change_id", words)
    net = sum(p["signed_value"] for p in prepared)
    gross = sum(p["value"] for p in prepared)
    types: dict[str, int] = {}
    causes: dict[str, int] = {}
    for p in prepared:
        types[p["change_type"]] = types.get(p["change_type"], 0) + 1
        causes[p["cause"]] = causes.get(p["cause"], 0) + 1
    return {
        "change_frequency_per_day": len(prepared) / exposure,
        "change_frequency_per_30_days": (len(prepared) / exposure) * 30.0,
        "change_count": len(prepared),
        "exposure_days": exposure,
        "change_magnitude_net": net / baseline,
        "change_magnitude_gross": gross / baseline,
        # RUN 101. ADDITIONS AND OMISSIONS STATED SEPARATELY, which the owner's order requires
        # and which a net figure hides: a project with a five per cent addition and a five per
        # cent omission is not the same project as one with neither. AN OMISSION IS NEVER
        # ADVERSE (section 12.1b), so it is reported as the reduction it is and is never added
        # to the exposure the additions represent.
        "additions_value": sum(p["value"] for p in prepared if p["direction"] == "ADDITIVE"),
        "omissions_value": sum(p["value"] for p in prepared if p["direction"] == "DEDUCTIVE"),
        "additions_fraction": sum(p["value"] for p in prepared
                                  if p["direction"] == "ADDITIVE") / baseline,
        "omissions_fraction": sum(p["value"] for p in prepared
                                  if p["direction"] == "DEDUCTIVE") / baseline,
        "baseline_contract_value": baseline,
        "revised_contract_value": baseline + net,
        "additive_count": sum(1 for p in prepared if p["direction"] == "ADDITIVE"),
        "deductive_count": sum(1 for p in prepared if p["direction"] == "DEDUCTIVE"),
        "type_counts": dict(sorted(types.items())),
        "cause_counts": dict(sorted(causes.items())),
        "source": prov["source"],
    }


# =================================================================================================
# 4.7 DISPUTE ESCALATION INDEX
# =================================================================================================


def dispute_escalation(structure: dict) -> dict[str, Any]:
    """
    The state of the project's claims on the project's OWN governed escalation process.

    THE LADDER IS NOT UNIVERSAL AND IS NOT DEFINED HERE. The contract is explicit that a ladder
    such as S0 noticed, S1 claim submitted, S2 determination, S3 negotiation, S4 mediation,
    S5 litigation is "a TEST FIXTURE, not a universal production taxonomy". So the process, its
    stages and their order arrive ON THE STRUCTURE, are versioned, and this function reads the
    stage each issue has reached against the order the project declared.

    THE THREE PROPERTIES THE CONTRACT NAMES, each enforced rather than asserted:
      - a later governed escalation state cannot look less escalated: the reading is the rank of
        the highest stage reached, which is monotone in the declared order by construction;
      - missing dispute evidence cannot improve the condition: no register, NO READING. There is
        no zero, no default stage and no "quiet" state;
      - a request count, a change count and a document risk score do not prove a dispute: none of
        the three is read anywhere in this function.
    """
    words = V4_STRUCTURE_WORDS["A4.7"]
    prov = _provenance(structure, words, "source", "process_id", "process_version")
    stages = _rows(structure, "process_stages", words)
    order: dict[str, int] = {}
    for s in stages:
        stage_id = _text(s, "stage_id", words)
        rank = _int(s, "rank", words)
        if stage_id in order:
            raise StructureAbsent(
                "The dispute process provided for this project names the same stage twice, so "
                "the order of its stages is not established and no reading is taken from it.")
        order[stage_id] = rank
    if len(set(order.values())) != len(order):
        raise StructureAbsent(
            "The dispute process provided for this project gives two of its stages the same "
            "place in the order, so which is the more escalated is not established.")
    issues = _rows(structure, "issues", words)
    prepared = []
    as_of = _f(structure, "as_of_day", words) if structure.get("as_of_day") is not None else None
    for i in issues:
        stage_id = _text(i, "current_stage_id", words)
        if stage_id not in order:
            raise StructureAbsent(
                "An issue in the dispute register provided for this project sits at a stage the "
                "declared process does not contain, so no place on the ladder is read for it.")
        history = i.get("stage_history")
        prepared.append({
            "issue_id": _text(i, "issue_id", words),
            "current_stage_id": stage_id,
            "rank": order[stage_id],
            "stage_day": _day(i, "stage_day", "stage_date", words),
            "notice_given": bool(i.get("notice_given")),
            "claim_value": num(i.get("claim_value"), None),
            "evidence_source": _text(i, "evidence_source", words),
            "stage_history": history if isinstance(history, list) else [],
            "unresolved_age_days": (as_of - _day(i, "raised_day", "raised_date", words)
                                    if as_of is not None else None),
        })
    _unique_ids(prepared, "issue_id", words)
    max_rank = max(order.values())
    min_rank = min(order.values())
    highest = max(prepared, key=lambda p: (p["rank"], p["issue_id"]))
    span = (max_rank - min_rank) or 1
    ages = [p["unresolved_age_days"] for p in prepared if p["unresolved_age_days"] is not None]
    return {
        "highest_stage_id": highest["current_stage_id"],
        "highest_stage_rank": highest["rank"],
        "escalation_position": (highest["rank"] - min_rank) / span,
        "process_id": prov["process_id"],
        "process_version": prov["process_version"],
        "stage_count": len(order),
        "issue_count": len(prepared),
        "issues_at_highest": sum(1 for p in prepared if p["rank"] == highest["rank"]),
        "issues": prepared,
        "total_claim_value": sum(p["claim_value"] for p in prepared
                                 if p["claim_value"] is not None),
        "max_unresolved_age_days": max(ages) if ages else None,
        "source": prov["source"],
    }


# =================================================================================================
# 4.8 SUBCONTRACTOR PERFORMANCE
# =================================================================================================


def subcontractor_performance(structure: dict) -> dict[str, Any]:
    """
    A traceable multi-criteria assessment, weighted by declared and versioned weights.

    ORACLE (contract 4.8): ratings 0.80, 0.90 and 0.70 under equal weights score 0.80.

    THE OPAQUE SCORE IS REFUSED, which is the whole point of the correction. The previous
    implementation consumed a single precomputed `subcontractorComplianceScore` with no component
    evidence and no provenance; the contract's words are "Do not validate this module by consuming
    an opaque precomputed compliance score with no component evidence". Component ratings, the
    evaluator, the assessment period and the weight version are all required, and the weights must
    sum to one because a weighted mean whose weights do not is not a weighted mean.
    """
    words = V4_STRUCTURE_WORDS["A4.8"]
    prov = _provenance(structure, words, "source", "weights_version")
    weights_raw = structure.get("weights")
    if not isinstance(weights_raw, dict) or not weights_raw:
        raise StructureAbsent(
            "The subcontractor assessment provided for this project does not say how much weight "
            "each criterion carries, so no overall score is formed from it.")
    weights = {}
    for k, v in weights_raw.items():
        w = num(v, None)
        if w is None or not math.isfinite(w) or w < 0:
            raise StructureAbsent(
                "The subcontractor assessment provided for this project carries a weight that is "
                "not a number at or above nought, so no overall score is formed from it.")
        weights[str(k).strip()] = float(w)
    total_weight = sum(weights.values())
    if abs(total_weight - 1.0) > 1e-9:
        raise StructureAbsent(
            "The weights in the subcontractor assessment provided for this project do not add up "
            "to one, so a weighted score formed from them would not be on the scale its parts "
            "are on, and none is formed.")
    assessments = _rows(structure, "assessments", words)
    results = []
    for a in assessments:
        ratings_raw = a.get("ratings")
        if not isinstance(ratings_raw, dict) or not ratings_raw:
            raise StructureAbsent(
                "A subcontractor in the assessment provided for this project carries no ratings "
                "against the declared criteria, so no score is formed for it.")
        ratings = {}
        for k, v in ratings_raw.items():
            r = num(v, None)
            if r is None or not math.isfinite(r):
                raise StructureAbsent(
                    "A rating in the subcontractor assessment provided for this project is not a "
                    "number, so no score is formed from it.")
            ratings[str(k).strip()] = float(r)
        if set(ratings) != set(weights):
            raise StructureAbsent(
                "A subcontractor in the assessment provided for this project was not rated "
                "against exactly the criteria the weights are declared over, so the weights "
                "would not add up over the ratings present and no score is formed.")
        score = sum(weights[k] * ratings[k] for k in weights)
        results.append({
            "subcontractor_id": _text(a, "subcontractor_id", words),
            "period": _text(a, "period", words),
            "evaluator": _text(a, "evaluator", words),
            "ratings": dict(sorted(ratings.items())),
            "score": score,
            "critical_violation": bool(a.get("critical_violation")),
            "rating_provenance": _text(a, "rating_provenance", words),
        })
    _unique_ids(results, "subcontractor_id", words)
    lowest = min(results, key=lambda r: (r["score"], r["subcontractor_id"]))
    return {
        "assessments": results,
        "subcontractor_count": len(results),
        "mean_score": sum(r["score"] for r in results) / len(results),
        "lowest_score": lowest["score"],
        "lowest_subcontractor": lowest["subcontractor_id"],
        "critical_violations": [r["subcontractor_id"] for r in results
                                if r["critical_violation"]],
        "criteria": sorted(weights),
        "weights": dict(sorted(weights.items())),
        "weights_version": prov["weights_version"],
        "source": prov["source"],
    }


# =================================================================================================
# 4.9 PROCUREMENT LEAD TIME MONITOR
# =================================================================================================


def procurement_slack(structure: dict) -> dict[str, Any]:
    """
    Item level procurement slack: required on site less forecast delivery.

    ORACLE (contract 4.9): required day one hundred against a forecast delivery of day one hundred
    and ten is a slack of minus ten days.

    NO DOUBLE COUNTING. The contract's words are "Do not double-count delayed items when delayed
    is already a subset of at-risk". Here an item is in exactly one state, decided by its own
    slack against its own float, and the states partition the register: LATE (slack below nought),
    AT_RISK (slack at or above nought but inside the float that protects it), and ON_TIME. A count
    ratio alone is not the canonical monitor, so the per-item slacks are the result and the counts
    are reported beside them.
    """
    words = V4_STRUCTURE_WORDS["A4.9"]
    prov = _provenance(structure, words, "source")
    items = _rows(structure, "items", words)
    results = []
    for it in items:
        required = _day(it, "required_on_site_day", "required_on_site_date", words)
        forecast = _day(it, "forecast_delivery_day", "forecast_delivery_date", words)
        slack = required - forecast
        flt = _f(it, "available_float_days", words)
        if flt < 0:
            raise StructureAbsent(
                "An item in the procurement register provided for this project sits on an "
                "activity with negative float, so no procurement slack is read from it.")
        if slack < 0:
            state = "LATE"
        elif slack < flt:
            state = "AT_RISK"
        else:
            state = "ON_TIME"
        results.append({
            "item_id": _text(it, "item_id", words),
            "required_on_site_day": required,
            "forecast_delivery_day": forecast,
            "slack_days": slack,
            "available_float_days": flt,
            "criticality": _text(it, "criticality", words),
            "status": _text(it, "procurement_status", words),
            "schedule_activity_id": _text(it, "schedule_activity_id", words),
            "forecast_uncertainty_days": num(it.get("forecast_uncertainty_days"), None),
            "state": state,
        })
    _unique_ids(results, "item_id", words)
    worst = min(results, key=lambda r: (r["slack_days"], r["item_id"]))
    states: dict[str, int] = {"LATE": 0, "AT_RISK": 0, "ON_TIME": 0}
    for r in results:
        states[r["state"]] += 1
    return {
        "items": results,
        "item_count": len(results),
        "minimum_slack_days": worst["slack_days"],
        "worst_item_id": worst["item_id"],
        "mean_slack_days": sum(r["slack_days"] for r in results) / len(results),
        "state_counts": states,
        "source": prov["source"],
    }


# =================================================================================================
# 4.10 SPECIFICATION CONFLICT DENSITY
# =================================================================================================


def specification_conflict_density(structure: dict) -> dict[str, Any]:
    """
    Verified conflicts per unit of declared specification exposure.

    ORACLE (contract 4.10): five verified conflicts over two hundred and fifty requirements is a
    density of 0.02 conflicts per requirement, or twenty per thousand requirements.

    THE PROXY IS NOT KEPT. `docRiskScore * sqrt(rfiCount)` is not conflict density, and the
    contract says so in those words; nothing in this function reads either field. Each conflict
    retains the two evidence locations that disagree, because a conflict with one location is an
    observation about a single clause and not a conflict at all.
    """
    words = V4_STRUCTURE_WORDS["A4.10"]
    prov = _provenance(structure, words, "source", "specification_document_id",
                       "specification_revision")
    unit = _text(structure, "exposure_unit", words)
    quantity = _f(structure, "exposure_quantity", words)
    if quantity <= 0:
        raise StructureAbsent(
            "The specification conflict register provided for this project does not say how much "
            "specification the conflicts were found in, so there is no exposure for a density to "
            "be measured over and none is formed.")
    conflicts = _rows(structure, "conflicts", words)
    prepared = []
    for c in conflicts:
        state = _text(c, "state", words).upper()
        if state not in ("CONFIRMED", "CANDIDATE"):
            raise StructureAbsent(
                "A conflict in the register provided for this project is neither confirmed nor "
                "recorded as a candidate, so which of the two the density counts is not "
                "established and none is formed.")
        prepared.append({
            "conflict_id": _text(c, "conflict_id", words),
            "location_a": _text(c, "evidence_location_a", words),
            "location_b": _text(c, "evidence_location_b", words),
            "state": state,
            "reviewer": _text(c, "reviewer", words) if state == "CONFIRMED" else
                        str(c.get("reviewer") or ""),
            "discipline": _text(c, "discipline", words),
            "cross_reference_id": str(c.get("cross_reference_id") or ""),
        })
    _unique_ids(prepared, "conflict_id", words)
    for p in prepared:
        if p["location_a"] == p["location_b"]:
            raise StructureAbsent(
                "A conflict in the register provided for this project cites the same place in "
                "the specification twice, so it records no disagreement between two places and "
                "no density is formed from it.")
    verified = [p for p in prepared if p["state"] == "CONFIRMED"]
    return {
        "conflict_density": len(verified) / quantity,
        "conflicts_per_thousand": (len(verified) / quantity) * 1000.0,
        "verified_conflicts": len(verified),
        "candidate_conflicts": len(prepared) - len(verified),
        "exposure_unit": unit,
        "exposure_quantity": quantity,
        "conflicts": prepared,
        "specification_document_id": prov["specification_document_id"],
        "specification_revision": prov["specification_revision"],
        "source": prov["source"],
        "detection_precision_recall": "PENDING_RUN_33",
    }


# =================================================================================================
# 5.1 DSM REWORK PROPAGATION
# =================================================================================================

#: The two orientations a dependency matrix is written in. Neither is assumed: a matrix read in
#: the wrong orientation propagates rework backwards along every edge, and the result still looks
#: like a number, so the structure must say which one it is.
_DSM_ORIENTATIONS = ("ROW_RECEIVES_FROM_COLUMN", "ROW_FEEDS_COLUMN")


def dsm_rework_propagation(structure: dict) -> dict[str, Any]:
    """
    Rework propagated over a declared dependency matrix.

    ORACLE (contract 5.1): with D = [[0, 0.5], [0, 0]] and R0 = [0, 1] under R_next = D * R,
    R1 = [0.5, 0] and R2 = [0, 0].

    The propagation is the matrix-vector product under the DECLARED orientation, iterated under
    the DECLARED stopping rule. Nothing here reads a performance index: dependency topology is not
    recoverable from CPI or SPI and the contract forbids substituting one for the other.
    """
    words = V4_STRUCTURE_WORDS["A5.1"]
    prov = _provenance(structure, words, "source", "model_version")
    orientation = _text(structure, "matrix_orientation", words).upper()
    if orientation not in _DSM_ORIENTATIONS:
        raise StructureAbsent(
            "The dependency matrix provided for this project does not say which way round it is "
            "written, so which part depends on which is not established and no rework is traced.")
    nodes = _rows(structure, "nodes", words)
    node_ids = _unique_ids(nodes, "node_id", words)
    if len(set(node_ids)) != len(node_ids):
        raise StructureAbsent(
            "The dependency matrix provided for this project names the same part of the design "
            "twice, so its parts cannot be told apart and no rework is traced through them.")
    index = {n: i for i, n in enumerate(node_ids)}
    size = len(node_ids)
    matrix = [[0.0] * size for _ in range(size)]
    edges = structure.get("edges")
    if not isinstance(edges, list):
        raise StructureAbsent(
            "The dependency matrix provided for this project carries no list of dependencies "
            "between its parts, so no rework is traced through them.")
    prepared_edges = []
    for e in edges:
        if not isinstance(e, dict):
            raise StructureAbsent(
                "A dependency in the matrix provided for this project is not in a form this "
                "method can read, so no rework is traced through it.")
        source = _text(e, "source", words)
        target = _text(e, "target", words)
        if source not in index or target not in index:
            raise StructureAbsent(
                "A dependency in the matrix provided for this project joins a part of the design "
                "that the matrix does not declare, so the topology is incomplete and no rework "
                "is traced through it.")
        strength = _f(e, "strength", words)
        if not 0 <= strength <= 1:
            raise StructureAbsent(
                "A dependency in the matrix provided for this project carries a strength outside "
                "the range a probability can occupy, so no rework is traced through it.")
        if orientation == "ROW_RECEIVES_FROM_COLUMN":
            matrix[index[target]][index[source]] = strength
        else:
            matrix[index[source]][index[target]] = strength
        prepared_edges.append({"source": source, "target": target, "strength": strength})
    seed_raw = structure.get("seed_rework_vector")
    if not isinstance(seed_raw, dict) or not seed_raw:
        raise StructureAbsent(
            "The dependency matrix provided for this project carries no rework to start the "
            "propagation from, so there is nothing to trace through it.")
    seed = [0.0] * size
    for k, v in seed_raw.items():
        name = str(k).strip()
        if name not in index:
            raise StructureAbsent(
                "The rework the propagation starts from names a part of the design the matrix "
                "does not declare, so no rework is traced through it.")
        value = num(v, None)
        if value is None or not math.isfinite(value) or value < 0:
            raise StructureAbsent(
                "The rework the propagation starts from carries an amount that is not a number "
                "at or above nought, so no rework is traced through it.")
        seed[index[name]] = float(value)
    stopping = structure.get("stopping_rule")
    if not isinstance(stopping, dict):
        raise StructureAbsent(
            "The dependency matrix provided for this project does not say when the propagation "
            "stops, and a matrix with a cycle in it propagates forever, so none is run.")
    max_iterations = _int(stopping, "max_iterations", words)
    epsilon = _f(stopping, "epsilon", words)
    if max_iterations < 1 or epsilon < 0:
        raise StructureAbsent(
            "The stopping rule provided with the dependency matrix does not permit even one step "
            "of propagation, or sets a tolerance below nought, so none is run.")
    waves = [list(seed)]
    current = list(seed)
    stopped = "MAX_ITERATIONS"
    for _ in range(max_iterations):
        nxt = [sum(matrix[i][j] * current[j] for j in range(size)) for i in range(size)]
        waves.append(nxt)
        current = nxt
        if sum(abs(v) for v in current) <= epsilon:
            stopped = "CONVERGED"
            break
    totals = [sum(w[i] for w in waves[1:]) for i in range(size)]
    return {
        "nodes": node_ids,
        "matrix_orientation": orientation,
        "matrix": matrix,
        "edges": prepared_edges,
        "seed_rework_vector": dict(zip(node_ids, seed)),
        "waves": [dict(zip(node_ids, w)) for w in waves],
        "wave_count": len(waves) - 1,
        "propagated_rework": dict(zip(node_ids, totals)),
        "total_propagated_rework": sum(totals),
        "stopped_because": stopped,
        "model_version": prov["model_version"],
        "source": prov["source"],
    }


# =================================================================================================
# THE GOVERNED RESPONSE MODEL, shared by 5.2, 5.3 and 5.4.
#
# A sensitivity, a tornado and a scenario are all "recompute the SAME response with the inputs
# moved", so they read the SAME declared response function. It is a polynomial response surface --
# a list of terms, each a coefficient and a power for each variable -- which is general enough to
# carry both of the contract's engine oracles (Y = x1^2 + x2 and Y = 2*x1 + x2) and general enough
# for a project to declare its own. It is DATA, not code: a project names its own response model
# and this layer evaluates it, so no laboratory function is hard-coded into production.
# =================================================================================================


def parse_response_model(structure: dict, words: str) -> dict[str, Any]:
    model = structure.get("response_model")
    if not isinstance(model, dict):
        raise StructureAbsent(
            "No response model has been declared for this project, so there is nothing for the "
            "inputs to be moved through and no reading is taken.")
    model_id = _text(model, "model_id", words)
    version = _text(model, "version", words)
    terms_raw = model.get("terms")
    if not isinstance(terms_raw, list) or not terms_raw:
        raise StructureAbsent(
            "The response model declared for this project carries no terms, so it computes "
            "nothing and no reading is taken from it.")
    terms = []
    variables: set[str] = set()
    for t in terms_raw:
        if not isinstance(t, dict):
            raise StructureAbsent(
                "The response model declared for this project is not in a form this method can "
                "read, so no reading is taken from it.")
        coefficient = _f(t, "coefficient", words)
        powers_raw = t.get("powers")
        if not isinstance(powers_raw, dict):
            raise StructureAbsent(
                "A term of the response model declared for this project does not say which "
                "inputs it is formed from, so no reading is taken from it.")
        powers = {}
        for k, v in powers_raw.items():
            p = num(v, None)
            if p is None or not math.isfinite(p):
                raise StructureAbsent(
                    "A term of the response model declared for this project raises an input to a "
                    "power that is not a number, so no reading is taken from it.")
            powers[str(k).strip()] = float(p)
            variables.add(str(k).strip())
        terms.append({"coefficient": coefficient, "powers": powers})
    return {"model_id": model_id, "version": version, "terms": terms,
            "variables": sorted(variables)}


def evaluate_response(model: dict, state: dict[str, float], words: str) -> float:
    total = 0.0
    for term in model["terms"]:
        value = term["coefficient"]
        for var, power in term["powers"].items():
            if var not in state:
                raise StructureAbsent(
                    "The response model declared for this project reads an input the state it is "
                    "being evaluated at does not carry, so no reading is taken from it.")
            base = state[var]
            if base < 0 and power != int(power):
                raise StructureAbsent(
                    "The response model declared for this project raises a negative input to a "
                    "fractional power, which has no real value, so no reading is taken from it.")
            value *= base ** power
        total += value
    if not math.isfinite(total):
        raise StructureAbsent(
            "The response model declared for this project does not produce a finite value at the "
            "state it is being evaluated at, so no reading is taken from it.")
    return total


def _base_state(structure: dict, words: str) -> dict[str, float]:
    raw = structure.get("base_state")
    if not isinstance(raw, dict) or not raw:
        raise StructureAbsent(
            "No base state has been declared for this project, so there is no point for the "
            "response to be evaluated at and no reading is taken.")
    state = {}
    for k, v in raw.items():
        value = num(v, None)
        if value is None or not math.isfinite(value):
            raise StructureAbsent(
                "The base state declared for this project carries a value that is not a number, "
                "so no reading is taken from it.")
        state[str(k).strip()] = float(value)
    return state


# =================================================================================================
# 5.2 SENSITIVITY ANALYSIS
# =================================================================================================


def sensitivity_analysis(structure: dict) -> dict[str, Any]:
    """
    A one-at-a-time local sensitivity: the response RECOMPUTED with each input moved.

    ORACLE (contract 5.2): with Y = x1^2 + x2 at x1 = 2, x2 = 1, Y = 5. Raising x1 by ten per cent
    to 2.2 gives Y = 5.84, so dY = 0.84 and the normalised sensitivity is
    (0.84/5) / (0.2/2) = 1.68.

    IT IS DECLARED AS LOCAL, NOT GLOBAL. The contract permits a one-at-a-time local method "if
    declared as such" and forbids calling it global; `method` on the result says which it is.
    Ranking currently bad variables is not sensitivity: every figure below comes from an actual
    recomputation of the response at a moved input.
    """
    words = V4_STRUCTURE_WORDS["A5.2"]
    prov = _provenance(structure, words, "source")
    model = parse_response_model(structure, words)
    base_state = _base_state(structure, words)
    method = _text(structure, "method", words).upper()
    if method != "LOCAL_ONE_AT_A_TIME":
        raise StructureAbsent(
            "The sensitivity model provided for this project asks for a method this platform "
            "does not perform, so no sensitivity is computed from it.")
    base_response = evaluate_response(model, base_state, words)
    inputs = _rows(structure, "inputs", words)
    results = []
    for inp in inputs:
        input_id = _text(inp, "input_id", words)
        if input_id not in base_state:
            raise StructureAbsent(
                "An input the sensitivity model asks to move is not part of the base state it is "
                "moved from, so there is nothing to move and no sensitivity is computed.")
        low = _f(inp, "low", words)
        high = _f(inp, "high", words)
        if high < low:
            raise StructureAbsent(
                "An input the sensitivity model asks to move has a high end below its low end, "
                "so the range it is moved across is not a range and no sensitivity is computed.")
        fraction = _f(inp, "perturbation_fraction", words)
        if fraction == 0:
            raise StructureAbsent(
                "An input the sensitivity model asks to move is to be moved by nothing at all, "
                "so the response cannot respond to it and no sensitivity is computed.")
        base_value = base_state[input_id]
        moved_value = base_value * (1.0 + fraction)
        delta_x = moved_value - base_value
        if delta_x == 0 or base_value == 0 or base_response == 0:
            raise StructureAbsent(
                "An input the sensitivity model asks to move, or the response at the base state, "
                "is nought, so a normalised sensitivity is a division by nought and none is "
                "computed.")
        moved_state = dict(base_state)
        moved_state[input_id] = moved_value
        moved_response = evaluate_response(model, moved_state, words)
        delta_y = moved_response - base_response
        low_state = dict(base_state)
        low_state[input_id] = low
        high_state = dict(base_state)
        high_state[input_id] = high
        results.append({
            "input_id": input_id,
            "units": str(inp.get("units") or ""),
            "base_value": base_value,
            "moved_value": moved_value,
            "perturbation_fraction": fraction,
            "base_response": base_response,
            "moved_response": moved_response,
            "delta_response": delta_y,
            "normalised_sensitivity": (delta_y / base_response) / (delta_x / base_value),
            "low": low,
            "high": high,
            "response_at_low": evaluate_response(model, low_state, words),
            "response_at_high": evaluate_response(model, high_state, words),
        })
    _unique_ids(results, "input_id", words)
    return {
        "method": "LOCAL_ONE_AT_A_TIME",
        "method_scope": "LOCAL",
        "response_model_id": model["model_id"],
        "response_model_version": model["version"],
        "base_state": dict(sorted(base_state.items())),
        "base_response": base_response,
        "inputs": results,
        "input_count": len(results),
        "source": prov["source"],
    }


# =================================================================================================
# 5.3 TORNADO RISK RANKING
#
# THE PARSIMONY DECISION, and the only one in Run 29's scope. 5.2 computes; 5.3 ranks what 5.2
# computed. The signature below is the proof: this function takes the RESULT DICTIONARY of
# `sensitivity_analysis` and nothing else. It cannot read the structure, the response model, the
# signal inputs or any project field, so it CANNOT form an independent evidence body even by
# accident. Its lineage names the sensitivity model it was derived from.
# =================================================================================================


def tornado_ranking(sensitivity: dict) -> dict[str, Any]:
    """
    The swing in the response when each input is moved across its declared range, ranked.

    ORACLE (contract 5.3): impacts of A = 120 - 90 = 30, B = 105 - 98 = 7 and C = 110 - 80 = 30
    rank A and C tied above B.

    THE TIE POLICY IS EXPLICIT, as the contract requires: equal absolute impacts share a rank, and
    among them the order shown is by input identity ascending, so the presentation is stable and
    two equal swings are never presented as though one beat the other.
    """
    if not isinstance(sensitivity, dict) or "inputs" not in sensitivity:
        raise StructureAbsent(
            "No sensitivity result has been produced for this project, and this ranking presents "
            "a sensitivity rather than computing one, so there is nothing to rank.")
    bars = []
    for row in sensitivity["inputs"]:
        impact = row["response_at_high"] - row["response_at_low"]
        bars.append({
            "input_id": row["input_id"],
            "response_at_low": row["response_at_low"],
            "response_at_high": row["response_at_high"],
            "impact": impact,
            "absolute_impact": abs(impact),
        })
    bars.sort(key=lambda b: (-b["absolute_impact"], b["input_id"]))
    rank = 0
    previous = None
    for bar in bars:
        if previous is None or bar["absolute_impact"] != previous:
            rank += 1
            previous = bar["absolute_impact"]
        bar["rank"] = rank
    tied = sorted({b["absolute_impact"] for b in bars
                   if sum(1 for o in bars if o["absolute_impact"] == b["absolute_impact"]) > 1})
    return {
        "bars": bars,
        "ranked_inputs": [b["input_id"] for b in bars],
        "top_input": bars[0]["input_id"] if bars else None,
        "top_impact": bars[0]["impact"] if bars else None,
        "distinct_ranks": rank,
        "tie_policy": "EQUAL_ABSOLUTE_IMPACT_SHARES_A_RANK_ORDERED_BY_INPUT_ID",
        "tied_impacts": tied,
        "derived_from": "A5.2",
        "derived_from_response_model_id": sensitivity.get("response_model_id"),
        "derived_from_response_model_version": sensitivity.get("response_model_version"),
        "derived_from_base_response": sensitivity.get("base_response"),
        "independent_evidence": False,
    }


# =================================================================================================
# 5.4 SCENARIO MODELING
# =================================================================================================


def scenario_modeling(structure: dict) -> dict[str, Any]:
    """
    Named, coherent, multi-variable states evaluated through one governed response model.

    ORACLE (contract 5.4): with Y = 2*x1 + x2, BASE (2, 1) gives 5, ADVERSE (3, 2) gives 8 and
    RECOVERY (1.5, 1) gives 4.

    A SCENARIO IS A COHERENT STATE, so every scenario must set every variable the response model
    reads -- a scenario that changes one variable and leaves another to be inherited from
    somewhere is not a declared state -- and every scenario must satisfy the consistency
    constraints the set declares. An inconsistent state is refused, not evaluated.

    This is not Category 10. Nothing here chooses between the scenarios or recommends one: the
    question answered is "what happens under this condition", and which intervention to choose is
    a later category's question.
    """
    words = V4_STRUCTURE_WORDS["A5.4"]
    prov = _provenance(structure, words, "source", "scenario_set_version")
    model = parse_response_model(structure, words)
    constraints_raw = structure.get("consistency_constraints")
    constraints = []
    if constraints_raw is not None:
        if not isinstance(constraints_raw, list):
            raise StructureAbsent(
                "The consistency constraints declared for this project's scenarios are not in a "
                "form this method can read, so no scenario is evaluated.")
        for c in constraints_raw:
            if not isinstance(c, dict):
                raise StructureAbsent(
                    "A consistency constraint declared for this project's scenarios is not in a "
                    "form this method can read, so no scenario is evaluated.")
            constraints.append({
                "constraint_id": _text(c, "constraint_id", words),
                "variable": _text(c, "variable", words),
                "minimum": num(c.get("minimum"), None),
                "maximum": num(c.get("maximum"), None),
            })
    scenarios = _rows(structure, "scenarios", words)
    results = []
    for s in scenarios:
        variables_raw = s.get("variables")
        if not isinstance(variables_raw, dict) or not variables_raw:
            raise StructureAbsent(
                "A scenario declared for this project changes no inputs, so it is not a state "
                "the response can be evaluated at and none is evaluated.")
        state = {}
        for k, v in variables_raw.items():
            value = num(v, None)
            if value is None or not math.isfinite(value):
                raise StructureAbsent(
                    "A scenario declared for this project carries a value that is not a number, "
                    "so no response is evaluated at it.")
            state[str(k).strip()] = float(value)
        if set(model["variables"]) - set(state):
            raise StructureAbsent(
                "A scenario declared for this project does not state a value for every input the "
                "response model reads, so it is not a coherent state and none is evaluated.")
        for c in constraints:
            if c["variable"] not in state:
                continue
            v = state[c["variable"]]
            if (c["minimum"] is not None and v < c["minimum"]) or \
               (c["maximum"] is not None and v > c["maximum"]):
                raise StructureAbsent(
                    "A scenario declared for this project sets an input outside the range the "
                    "scenario set itself declares to be consistent, so the state is not coherent "
                    "and no response is evaluated at it.")
        results.append({
            "scenario_id": _text(s, "scenario_id", words),
            "name": _text(s, "name", words),
            "version": _text(s, "version", words),
            "rationale": _text(s, "rationale", words),
            "variables": dict(sorted(state.items())),
            "response": evaluate_response(model, state, words),
        })
    _unique_ids(results, "scenario_id", words)
    return {
        "scenarios": results,
        "scenario_count": len(results),
        "response_model_id": model["model_id"],
        "response_model_version": model["version"],
        "constraints": constraints,
        "responses": {r["scenario_id"]: r["response"] for r in results},
        "minimum_response": min(r["response"] for r in results),
        "maximum_response": max(r["response"] for r in results),
        "scenario_set_version": prov["scenario_set_version"],
        "source": prov["source"],
    }


# =================================================================================================
# 5.5 REWORK FEEDBACK LOOP
# =================================================================================================


def rework_feedback_loop(structure: dict) -> dict[str, Any]:
    """
    A stock and flow rework model stepped through time.

    THE ACCOUNTING, exactly as the contract states it:
        Backlog(t+1) = Backlog(t) + NewWork(t) + ReworkGenerated(t) - WorkCompleted(t)
        ReworkGenerated(t) = ErrorRate(t) * WorkCompleted(t)

    ORACLE (contract 5.5): Backlog0 = 10, NewWork = 5, WorkCompleted = 8, ErrorRate = 0.25 gives
    ReworkGenerated = 2 and Backlog1 = 9.

    A weighted composite of a cost index, a request count and a change count is not a feedback
    loop, and nothing here reads any of the three.
    """
    words = V4_STRUCTURE_WORDS["A5.5"]
    prov = _provenance(structure, words, "source", "model_version")
    time_step = _f(structure, "time_step", words)
    if time_step <= 0:
        raise StructureAbsent(
            "The rework model provided for this project has a time step of nought or less, so it "
            "does not advance through time and no reading is taken from it.")
    backlog = _f(structure, "initial_backlog", words)
    if backlog < 0:
        raise StructureAbsent(
            "The rework model provided for this project starts with a negative backlog, which is "
            "not a stock of work, so no reading is taken from it.")
    steps = _rows(structure, "steps", words)
    trace = []
    total_new = 0.0
    total_completed = 0.0
    total_rework = 0.0
    for s in steps:
        new_work = _f(s, "new_work", words)
        completed = _f(s, "work_completed", words)
        error_rate = _f(s, "error_rate", words)
        if new_work < 0 or completed < 0:
            raise StructureAbsent(
                "A step of the rework model provided for this project reports a negative amount "
                "of work arriving or completed, so no reading is taken from it.")
        if not 0 <= error_rate <= 1:
            raise StructureAbsent(
                "A step of the rework model provided for this project reports an error rate "
                "outside the range a share can occupy, so no reading is taken from it.")
        available = backlog + new_work
        if completed > available + 1e-9:
            raise StructureAbsent(
                "A step of the rework model provided for this project completes more work than "
                "was in the backlog to complete, so the accounting does not balance and no "
                "reading is taken from it.")
        rework = error_rate * completed
        opening = backlog
        backlog = opening + new_work + rework - completed
        total_new += new_work
        total_completed += completed
        total_rework += rework
        trace.append({
            "step": _int(s, "step", words),
            "opening_backlog": opening,
            "new_work": new_work,
            "work_completed": completed,
            "error_rate": error_rate,
            "rework_generated": rework,
            "closing_backlog": backlog,
        })
    conservation = abs((trace[0]["opening_backlog"] + total_new + total_rework - total_completed)
                       - backlog)
    if conservation > 1e-6:
        raise StructureAbsent(
            "The rework model provided for this project does not conserve its own stock across "
            "the steps it was run over, so no reading is taken from it.")
    return {
        "time_step": time_step,
        "initial_backlog": trace[0]["opening_backlog"],
        "final_backlog": backlog,
        "steps_run": len(trace),
        "trace": trace,
        "total_new_work": total_new,
        "total_work_completed": total_completed,
        "total_rework_generated": total_rework,
        "rework_share_of_completed": (total_rework / total_completed) if total_completed else None,
        "accounting_residual": conservation,
        "model_version": prov["model_version"],
        "source": prov["source"],
    }


# =================================================================================================
# 5.6 QUEUEING THEORY BOTTLENECK
# =================================================================================================


def queue_model(structure: dict) -> dict[str, Any]:
    """
    An M/M/c queue per declared queue, and the stability condition enforced.

    ORACLE (contract 5.6): lambda = 2, mu = 3, one server gives rho = 2/3, L = 2, W = 1,
    Lq = 4/3 and Wq = 2/3, and Little's Law holds: L = lambda*W = 2 and Lq = lambda*Wq = 4/3.

    AN UNSTABLE QUEUE IS NOT GIVEN A REASSURING STEADY STATE. Where lambda is at or above c*mu the
    queue has no steady state at all, and the contract's instruction is to return unstable rather
    than a finite waiting time. This raises, so the caller abstains and says which queue it was:
    there is no finite L, W, Lq or Wq to report and reporting one would be a fabrication.

    A share of constrained activities in a look-ahead window is not queueing theory, and nothing
    here reads an activity count.
    """
    words = V4_STRUCTURE_WORDS["A5.6"]
    prov = _provenance(structure, words, "source", "model_version")
    queues = _rows(structure, "queues", words)
    readings = []
    for q in queues:
        queue_id = _text(q, "queue_id", words)
        lam = _f(q, "arrival_rate", words)
        mu = _f(q, "service_rate", words)
        servers = _int(q, "servers", words)
        discipline = _text(q, "discipline", words).upper()
        if discipline not in ("FIFO", "LIFO", "PRIORITY"):
            raise StructureAbsent(
                "A queue provided for this project takes its work in an order this platform has "
                "no model for, so no waiting time is computed from it.")
        if lam <= 0 or mu <= 0 or servers < 1:
            raise StructureAbsent(
                "A queue provided for this project reports no arrivals, no service or no "
                "servers, so no waiting time is computed from it.")
        rho = lam / (servers * mu)
        if rho >= 1.0:
            raise StructureAbsent(
                f"Work arrives at the queue called {queue_id} at least as fast as its servers "
                f"can deal with it, so the waiting time grows without limit and there is no "
                f"steady state for this method to report. No finite waiting time is offered in "
                f"its place.")
        a = lam / mu
        terms = sum((a ** n) / math.factorial(n) for n in range(servers))
        last = (a ** servers) / (math.factorial(servers) * (1 - rho))
        p0 = 1.0 / (terms + last)
        lq = p0 * (a ** servers) * rho / (math.factorial(servers) * (1 - rho) ** 2)
        wq = lq / lam
        w = wq + 1.0 / mu
        ell = lam * w
        readings.append({
            "queue_id": queue_id,
            "arrival_rate": lam,
            "service_rate": mu,
            "servers": servers,
            "discipline": discipline,
            "utilisation": rho,
            "L": ell,
            "W": w,
            "Lq": lq,
            "Wq": wq,
            "p0": p0,
            "littles_law_L": lam * w,
            "littles_law_Lq": lam * wq,
        })
    _unique_ids(readings, "queue_id", words)
    bottleneck = max(readings, key=lambda r: (r["utilisation"], r["queue_id"]))
    return {
        "queues": readings,
        "queue_count": len(readings),
        "bottleneck": bottleneck,
        "stability": "STABLE",
        "model": "M/M/c",
        "model_version": prov["model_version"],
        "source": prov["source"],
    }


# =================================================================================================
# 5.7 AGENT-BASED SUPPLY CHAIN
# =================================================================================================

#: The deterministic step order, stated once here so a reader can hand-check any trace. Within one
#: time step: demand is posted, deliveries land, the carrier collects, the supplier ships.
_ABM_STEP_ORDER = ("POST_DEMAND", "DELIVER", "COLLECT", "SHIP")

_ABM_RULES = {
    "SUPPLIER_SHIP_ONE_IF_STOCK_AND_REQUEST",
    "CARRIER_COLLECT_ONE_AND_DELIVER_AFTER_DELAY",
    "PROJECT_POST_DEMAND_AND_COUNT_RECEIPTS",
}


class _Lcg:
    """A small, self-contained, seeded generator so a stochastic run is reproducible from its
    seed alone and cannot be shifted by an unrelated call elsewhere in the process."""

    def __init__(self, seed: int) -> None:
        self.state = (int(seed) & 0xFFFFFFFF) or 1

    def next(self) -> float:
        self.state = (1664525 * self.state + 1013904223) & 0xFFFFFFFF
        return self.state / 4294967296.0


def agent_supply_chain(structure: dict) -> dict[str, Any]:
    """
    Agents, states, behaviour rules, interactions, environment and time, actually stepped.

    THE STEP ORDER, which makes every trace hand-checkable, is POST_DEMAND, DELIVER, COLLECT,
    SHIP within each time step.

    ORACLE (contract 5.7, one supplier, one carrier, one project, deterministic): supplier stock
    two, travel delay one, project demand two posted at step nought. Step 0 ships one unit to the
    dock. Step 1 the carrier collects it, due at step 2, and the supplier ships the second unit.
    Step 2 the first unit is received, the carrier collects the second, due at step 3. Step 3 the
    second unit is received. Received two, backordered nought, supplier stock nought.

    A long-lead at-risk ratio is not an agent-based model, and nothing here reads a procurement
    count. Where the model declares a disruption probability the run is stochastic and the seed
    and replication count are carried out with the result, per the contract's stochastic rules.
    """
    words = V4_STRUCTURE_WORDS["A5.7"]
    prov = _provenance(structure, words, "source", "model_version")
    environment = _text(structure, "environment", words)
    time_steps = _int(structure, "time_steps", words)
    if time_steps < 2:
        raise StructureAbsent(
            "The agent model provided for this project runs over a single point in time, so "
            "there is no run over time for a supply chain to be simulated across.")
    travel_delay = _int(structure, "travel_delay_steps", words)
    if travel_delay < 0:
        raise StructureAbsent(
            "The agent model provided for this project gives the carrier a negative travel time, "
            "so no run is made from it.")
    agents = _rows(structure, "agents", words)
    by_type: dict[str, list[dict]] = {}
    prepared = []
    for a in agents:
        agent_type = _text(a, "agent_type", words).upper()
        rule = _text(a, "behaviour_rule", words).upper()
        if rule not in _ABM_RULES:
            raise StructureAbsent(
                "An agent in the model provided for this project follows a rule this platform "
                "has no behaviour for, so no run is made from it.")
        links = a.get("interaction_links")
        if not isinstance(links, list) or not links:
            raise StructureAbsent(
                "An agent in the model provided for this project is connected to nobody, so the "
                "agents provided do not interact and no run is made from them.")
        row = {
            "agent_id": _text(a, "agent_id", words),
            "agent_type": agent_type,
            "behaviour_rule": rule,
            "interaction_links": [str(x) for x in links],
            "inventory": num(a.get("inventory"), 0.0) or 0.0,
            "demand": num(a.get("demand"), 0.0) or 0.0,
            "state": _text(a, "state", words).upper(),
        }
        prepared.append(row)
        by_type.setdefault(agent_type, []).append(row)
    _unique_ids(prepared, "agent_id", words)
    known = {p["agent_id"] for p in prepared}
    for p in prepared:
        for link in p["interaction_links"]:
            if link not in known:
                raise StructureAbsent(
                    "An agent in the model provided for this project is connected to somebody "
                    "the model does not contain, so no run is made from it.")
    for required_type in ("SUPPLIER", "CARRIER", "PROJECT"):
        if len(by_type.get(required_type, [])) != 1:
            raise StructureAbsent(
                "The agent model provided for this project does not carry exactly one supplier, "
                "one carrier and one project, which is the structure this platform simulates, so "
                "no run is made from it.")
    supplier = by_type["SUPPLIER"][0]
    carrier = by_type["CARRIER"][0]
    project = by_type["PROJECT"][0]

    disruption = num(structure.get("disruption_probability"), 0.0) or 0.0
    if not 0 <= disruption <= 1:
        raise StructureAbsent(
            "The agent model provided for this project reports a chance of disruption outside "
            "the range a probability can occupy, so no run is made from it.")
    stochastic = disruption > 0
    seed = None
    replications = 1
    if stochastic:
        seed = _int(structure, "seed", words)
        replications = _int(structure, "replications", words)
        if replications < 1:
            raise StructureAbsent(
                "The agent model provided for this project asks for fewer than one run, so no "
                "run is made from it.")

    runs = []
    for replication in range(replications):
        rng = _Lcg((seed or 0) + replication) if stochastic else None
        inventory = supplier["inventory"]
        outstanding = project["demand"]
        requests = 0.0
        dock = 0
        in_transit: list[int] = []
        carrier_busy = False
        received = 0
        trace = []
        disrupted_steps = 0
        for t in range(time_steps):
            disrupted = bool(rng is not None and rng.next() < disruption)
            if disrupted:
                disrupted_steps += 1
            # POST_DEMAND
            if outstanding > 0:
                requests += outstanding
                outstanding = 0.0
            # DELIVER
            landed = [d for d in in_transit if d == t]
            for _ in landed:
                received += 1
                in_transit.remove(t)
                carrier_busy = False
            # COLLECT
            if not disrupted and not carrier_busy and dock > 0:
                dock -= 1
                in_transit.append(t + travel_delay)
                carrier_busy = True
            # SHIP
            if not disrupted and inventory > 0 and requests > 0:
                inventory -= 1
                requests -= 1
                dock += 1
            trace.append({
                "step": t, "disrupted": disrupted, "supplier_inventory": inventory,
                "open_requests": requests, "dock": dock, "in_transit": len(in_transit),
                "received": received,
            })
        runs.append({
            "replication": replication,
            "received": received,
            "backordered": project["demand"] - received,
            "supplier_inventory_final": inventory,
            "disrupted_steps": disrupted_steps,
            "trace": trace,
        })
    received_values = [r["received"] for r in runs]
    return {
        "agents": [{k: v for k, v in p.items()} for p in prepared],
        "agent_count": len(prepared),
        "agent_types": sorted(by_type),
        "rules": sorted({p["behaviour_rule"] for p in prepared}),
        "environment": environment,
        "time_steps": time_steps,
        "travel_delay_steps": travel_delay,
        "step_order": list(_ABM_STEP_ORDER),
        "stochastic": stochastic,
        "seed": seed,
        "replications": replications,
        "runs": runs,
        "received": received_values[0] if not stochastic else
                    sum(received_values) / len(received_values),
        "backordered": runs[0]["backordered"] if not stochastic else
                       project["demand"] - (sum(received_values) / len(received_values)),
        "demand": project["demand"],
        "supplier_id": supplier["agent_id"],
        "carrier_id": carrier["agent_id"],
        "project_agent_id": project["agent_id"],
        "model_version": prov["model_version"],
        "source": prov["source"],
        "empirical_calibration": "PENDING_RUN_33",
    }


# =================================================================================================
# 5.8 DISCRETE EVENT SIMULATION
# =================================================================================================

#: The simultaneous-event policy, declared rather than emergent: at equal event times a departure
#: is processed before an arrival, so a resource is released before the next entity asks for it,
#: and among equal events of the same kind the order is by entity identity ascending.
_DES_EVENT_ORDER = {"DEPARTURE": 0, "ARRIVAL": 1}


def des_process_model(structure: dict) -> dict[str, Any]:
    """
    A real event-driven simulation: an event list, a clock, resources, a queue and routing.

    ORACLE (contract 5.8): one server; job A arrives at 0 with service 2, job B arrives at 1 with
    service 2. A starts at 0, ends at 2, waits 0. B starts at 2, ends at 4, waits 1. Mean wait is
    0.5.

    A progress or schedule index is not a discrete event simulation, and nothing here reads one.
    Where service times are declared as a distribution the run is stochastic, and the seed and the
    replication count are carried out with the result.
    """
    words = V4_STRUCTURE_WORDS["A5.8"]
    prov = _provenance(structure, words, "source", "model_version")
    discipline = _text(structure, "queue_discipline", words).upper()
    if discipline not in ("FIFO", "PRIORITY"):
        raise StructureAbsent(
            "The discrete event model provided for this project takes its work in an order this "
            "platform has no model for, so no run is made from it.")
    resources = _rows(structure, "resources", words)
    if len(resources) != 1:
        raise StructureAbsent(
            "The discrete event model provided for this project does not carry exactly one "
            "resource, which is the routing this platform simulates, so no run is made from it.")
    resource_id = _text(resources[0], "resource_id", words)
    capacity = _int(resources[0], "capacity", words)
    if capacity < 1:
        raise StructureAbsent(
            "The resource in the discrete event model provided for this project has no capacity, "
            "so nothing can ever be served and no run is made from it.")
    termination = _text(structure, "termination_condition", words).upper()
    if termination != "ALL_ENTITIES_DEPARTED":
        raise StructureAbsent(
            "The discrete event model provided for this project asks to stop on a condition this "
            "platform does not implement, so no run is made from it.")
    entities = _rows(structure, "entities", words)
    prepared = []
    stochastic = False
    for e in entities:
        service_raw = e.get("service_time")
        distribution = e.get("service_distribution")
        if service_raw is None and not isinstance(distribution, dict):
            raise StructureAbsent(
                "An entity in the discrete event model provided for this project carries neither "
                "a service time nor a distribution to draw one from, so no run is made from it.")
        if isinstance(distribution, dict):
            stochastic = True
            family = _text(distribution, "family", words).upper()
            if family != "EXPONENTIAL":
                raise StructureAbsent(
                    "An entity in the discrete event model provided for this project draws its "
                    "service from a distribution this platform does not sample, so no run is "
                    "made from it.")
            mean = _f(distribution, "mean", words)
            if mean <= 0:
                raise StructureAbsent(
                    "An entity in the discrete event model provided for this project draws its "
                    "service from a distribution with a mean of nought or less, so no run is "
                    "made from it.")
        prepared.append({
            "entity_id": _text(e, "entity_id", words),
            "entity_type": _text(e, "entity_type", words),
            "arrival_time": _f(e, "arrival_time", words),
            "service_time": (float(num(service_raw, 0.0) or 0.0)
                             if service_raw is not None else None),
            "service_distribution": distribution if isinstance(distribution, dict) else None,
            "priority": int(num(e.get("priority"), 0) or 0),
        })
    _unique_ids(prepared, "entity_id", words)
    for p in prepared:
        if p["arrival_time"] < 0:
            raise StructureAbsent(
                "An entity in the discrete event model provided for this project arrives before "
                "the clock starts, so no run is made from it.")
        if p["service_time"] is not None and p["service_time"] < 0:
            raise StructureAbsent(
                "An entity in the discrete event model provided for this project is served for a "
                "negative length of time, so no run is made from it.")
    seed = None
    replications = 1
    if stochastic:
        seed = _int(structure, "seed", words)
        replications = _int(structure, "replications", words)
        if replications < 1:
            raise StructureAbsent(
                "The discrete event model provided for this project asks for fewer than one run, "
                "so no run is made from it.")

    runs = []
    for replication in range(replications):
        rng = _Lcg((seed or 0) + replication) if stochastic else None
        runs.append(_des_run(prepared, capacity, discipline, rng))
    mean_waits = [r["mean_wait"] for r in runs]
    return {
        "resource_id": resource_id,
        "capacity": capacity,
        "queue_discipline": discipline,
        "event_order_policy": "DEPARTURE_BEFORE_ARRIVAL_THEN_ENTITY_ID",
        "termination_condition": termination,
        "entity_count": len(prepared),
        "stochastic": stochastic,
        "seed": seed,
        "replications": replications,
        "runs": runs,
        "mean_wait": sum(mean_waits) / len(mean_waits),
        "entities": runs[0]["entities"],
        "events": runs[0]["events"],
        "clock_end": runs[0]["clock_end"],
        "model_version": prov["model_version"],
        "source": prov["source"],
    }


def _des_run(entities: list[dict], capacity: int, discipline: str, rng) -> dict[str, Any]:
    """One replication: a true event list with a clock, a queue and a released resource."""
    service_times = {}
    for e in entities:
        if e["service_time"] is not None:
            service_times[e["entity_id"]] = e["service_time"]
        else:
            mean = float(e["service_distribution"]["mean"])
            u = rng.next()
            u = min(max(u, 1e-12), 1 - 1e-12)
            service_times[e["entity_id"]] = -mean * math.log(1.0 - u)
    events = [{"time": e["arrival_time"], "type": "ARRIVAL", "entity_id": e["entity_id"]}
              for e in entities]
    by_id = {e["entity_id"]: e for e in entities}
    queue: list[str] = []
    busy = 0
    clock = 0.0
    results: dict[str, dict] = {}
    log = []
    while events:
        events.sort(key=lambda ev: (ev["time"], _DES_EVENT_ORDER[ev["type"]], ev["entity_id"]))
        event = events.pop(0)
        clock = event["time"]
        log.append(dict(event))
        if event["type"] == "DEPARTURE":
            busy -= 1
        else:
            queue.append(event["entity_id"])
        while busy < capacity and queue:
            if discipline == "PRIORITY":
                queue.sort(key=lambda eid: (-by_id[eid]["priority"],
                                            by_id[eid]["arrival_time"], eid))
            chosen = queue.pop(0)
            start = clock
            end = start + service_times[chosen]
            busy += 1
            results[chosen] = {
                "entity_id": chosen,
                "entity_type": by_id[chosen]["entity_type"],
                "arrival": by_id[chosen]["arrival_time"],
                "service_time": service_times[chosen],
                "start": start,
                "end": end,
                "wait": start - by_id[chosen]["arrival_time"],
            }
            events.append({"time": end, "type": "DEPARTURE", "entity_id": chosen})
    ordered = [results[e["entity_id"]] for e in entities]
    waits = [r["wait"] for r in ordered]
    return {
        "entities": ordered,
        "events": log,
        "event_count": len(log),
        "clock_end": clock,
        "mean_wait": sum(waits) / len(waits),
        "max_wait": max(waits),
        "makespan": max(r["end"] for r in ordered),
    }
