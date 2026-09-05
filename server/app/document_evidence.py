"""
WHAT THE PERIOD'S DOCUMENTS ESTABLISH, AND WHICH DOCUMENT ESTABLISHES IT.

THE DEFECT THIS EXISTS TO CLOSE. The recommendation was built from the computed signals alone,
and behind it sat a regret module whose payoff matrix and future probabilities are literals: the
three scores are `{monitor: 11, investigate: 5, escalate: 8}` on every project and every period
this platform has ever stored. Nothing about a project reaches them. The recommendation itself
then came from a threshold on cost and schedule performance, so the card could show a reader
three scored courses and not one of the numbers was about their project.

Meanwhile the documents that produced those signals were sitting in the period, holding exactly
what the signals reduce away. Cost performance of 0.84 does not say that eleven requests for
information are still open, that a submittal was rejected, or that a procurement item is late.
Those are in the documents, they are already extracted, and nothing was reading them back.

WHAT THIS MODULE DOES. Given the period's live documents, it returns the findings their stored
extractions support, each one carrying the document it came from BY NAME. Nothing here computes
a recommendation, ranks anything, or scores anything. It reports what was read.

THE RULE, AND IT IS THE CARD'S EXISTING RULE. Every statement is either a figure read back from
a stored extraction, or an explicit statement that the platform does not hold what would be
needed to say. There is no third kind of sentence here.

WHAT THE PLATFORM CANNOT SAY, AND WHY IT SAYS SO OUT LOUD. Extraction stores only the field list
each document type declares (`extraction_client` drops every other key the model returns, on
purpose). For the two most narrative types, `correspondence_notice` and `risk_register`, that
list is a risk score and a date and nothing else. So a notice in the period is a fact this
platform holds; what the notice SAYS is not. `not_established` below carries those documents by
name rather than letting their silence read as their absence, because a card that omits a served
notice entirely is worse than one that says a notice is here and its content was not read.

NO SCORE IS INVENTED HERE. `ranking` states whether a ranking of the courses can be produced
from this period's evidence and, when it cannot, why not, in the words the card prints. Building
some fresh weighting out of these counts would be the same defect as the literal payoff matrix
wearing different clothes: a number that looks like a finding and is really a choice nobody
made. The honest output is a refusal with its reason, and that is what this returns.
"""
from __future__ import annotations

from typing import Any

from .risk_exposure import register_exposure

# --------------------------------------------------------------------------- the findings table
#
# One row per (doc_type, field) that says something a reader would act on differently if they
# knew it. Every entry names a field that `extraction_fields._EXTRACTION_FIELDS` actually
# declares for that type -- `test_period_picker_and_evidence.py` asserts that, so a field renamed
# in the vocabulary turns this table red instead of silently reporting nothing forever.
#
# `bearing` is what the finding bears on, in the reader's language, not a module or category
# name. RUN 59: the citation of NAMING_AUTHORITY is DROPPED -- no markdown document carries
# authority, and the identifier prohibition it named was SUPERSEDED on 2026-08-23. The reason
# stands on its own: this string is read by someone deciding what to do about a document, and a
# key tells them nothing. Displayed identifiers are permitted; they are simply not useful here.
#
# `singular`/`plural` are formatted with the integer value. They are written to read as a
# statement of fact and never as advice: THIS MODULE reports, it does not recommend.
#
# RUN 140 SCOPES THAT SENTENCE AND DOES NOT DELETE IT. It is true of this module and stays true:
# nothing here composes a response to anything it counts, and these strings are read straight
# into a band decision, so advice in one of them would contaminate the evidence. It is NOT a
# platform-wide claim any more. From 2026-09-05 the Suggested Decision card carries candidate
# mitigations for every non-Green reading, composed elsewhere (`decision_brief.py`), gated
# elsewhere, and never from these sentences.

_FINDINGS: tuple[dict[str, Any], ...] = (
    # Unresolved scope questions.
    {"doc_type": "rfi_log", "field": "rfi_open", "bearing": "unresolved scope questions",
     "singular": "{n} request for information is still open",
     "plural": "{n} requests for information are still open"},
    {"doc_type": "rfi_log", "field": "rfi_overdue", "bearing": "unresolved scope questions",
     "singular": "{n} request for information is overdue",
     "plural": "{n} requests for information are overdue"},
    {"doc_type": "rfi_log", "field": "oldest_open_days", "bearing": "unresolved scope questions",
     "singular": "the oldest open request for information has been open {n} day",
     "plural": "the oldest open request for information has been open {n} days"},
    # Non-conformance.
    {"doc_type": "ncr_log", "field": "ncr_open", "bearing": "unresolved non-conformances",
     "singular": "{n} non-conformance is open",
     "plural": "{n} non-conformances are open"},
    {"doc_type": "ncr_log", "field": "ncr_overdue", "bearing": "unresolved non-conformances",
     "singular": "{n} non-conformance is overdue",
     "plural": "{n} non-conformances are overdue"},
    # Approvals.
    {"doc_type": "submittal_register", "field": "submittals_rejected",
     "bearing": "rejected approvals",
     "singular": "{n} submittal was rejected", "plural": "{n} submittals were rejected"},
    # Procurement position.
    {"doc_type": "procurement_log", "field": "delayed", "bearing": "the procurement position",
     "singular": "{n} procurement item is delayed",
     "plural": "{n} procurement items are delayed"},
    {"doc_type": "procurement_log", "field": "at_risk", "bearing": "the procurement position",
     "singular": "{n} procurement item is at risk",
     "plural": "{n} procurement items are at risk"},
    # Open disputes and unclosed actions, from the meeting record.
    {"doc_type": "oac_minutes", "field": "subcontractor_disputes", "bearing": "open disputes",
     "singular": "{n} subcontractor dispute was recorded in the meeting",
     "plural": "{n} subcontractor disputes were recorded in the meeting"},
    {"doc_type": "oac_minutes", "field": "outstanding_action_items",
     "bearing": "unclosed actions",
     "singular": "{n} action item from the meeting is outstanding",
     "plural": "{n} action items from the meeting are outstanding"},
    {"doc_type": "oac_minutes", "field": "safety_actions_open", "bearing": "unclosed actions",
     "singular": "{n} safety action is open", "plural": "{n} safety actions are open"},
    # Scope change volume.
    {"doc_type": "change_order", "field": "change_order_count", "bearing": "scope change",
     "singular": "{n} change order is recorded", "plural": "{n} change orders are recorded"},
    # Quality on the ground.
    {"doc_type": "inspection_report", "field": "items_failed", "bearing": "quality on site",
     "singular": "{n} inspected item failed", "plural": "{n} inspected items failed"},
    {"doc_type": "inspection_report", "field": "critical_deficiency_count",
     "bearing": "quality on site",
     "singular": "{n} critical deficiency was recorded",
     "plural": "{n} critical deficiencies were recorded"},
    {"doc_type": "field_report", "field": "quality_deficiencies_noted",
     "bearing": "quality on site",
     "singular": "{n} quality deficiency was noted in the field",
     "plural": "{n} quality deficiencies were noted in the field"},
)

# Document types whose stored extraction is a risk score and a date and nothing else, so their
# CONTENT is not available to quote. Named here so the card can say a document is present and
# unread rather than staying silent about it. Kept in step with the vocabulary by a check.
# BOTH ENTRIES ARE GONE, and that is the whole point of this change.
#
# This map used to carry `correspondence_notice` and `risk_register`, because the extraction for
# each was a risk score and a date and the card could only say a document was present and unread.
# Both are read now: a register's rows come from the document itself (`risk_register`), and a
# notice's who, what, when and which-clock come from its own prose plus a deadline derived in
# code from the form it named (`contract_notices`). Naming them here now would be the card
# claiming it had not read something it had.
#
# The map is kept, empty, rather than deleted: it is the right place for the next document type
# whose content genuinely is not stored, and a check asserts every key in it is a real type.
_CONTENT_NOT_STORED: dict[str, str] = {}

# The words the card prints when it declines to rank. Held here, next to the reason it is true,
# so the sentence and its justification cannot drift apart.
NO_RANKING_REASON: str = (
    "The stored courses carry the same three scores on every project and every reporting "
    "period, because the table they come from does not read any project input. They rank "
    "nothing about this project, so no ranking is shown."
)


def _as_int(value: Any) -> int | None:
    """A whole count, or None. A float that is not whole is not a count and is refused."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    return None


def register_findings(risks: list[dict] | None) -> list[dict[str, Any]]:
    """
    What the risk register establishes, each statement naming the risk it came from.

    A RISK IS NAMED, NOT COUNTED. "Four risks are open" tells a project manager nothing they can
    act on; "R-002, utility relocation delayed by a third party, is open, scored High, owned by
    M. Chen, response Transfer" is a sentence they can take to the person named in it. So this
    reports the risks that carry the most weight the register itself assigned, by key.

    NOTHING HERE RANKS OR SCORES. The ordering is the register's own score where it stated one,
    and the register's own order where it did not. No risk is promoted or demoted by anything
    this platform decided.

    A BAND IS QUOTED AS A BAND. Where the register said "High", the sentence says High. It is
    never turned into a number, here or anywhere else.
    """
    rows = [r for r in (risks or []) if isinstance(r, dict)]
    live = [r for r in rows if r.get("is_open") is not False]
    if not live:
        return []

    # The register's own score orders them where it stated one; everything unscored keeps the
    # register's order behind everything scored. Stable, and decided by the document.
    def sort_key(item):
        index, row = item
        score = row.get("score")
        return (0, -float(score), index) if isinstance(score, (int, float)) else (1, 0.0, index)

    ordered = [r for _, r in sorted(enumerate(live), key=sort_key)]

    out: list[dict[str, Any]] = []
    for r in ordered[:MAX_NAMED_RISKS]:
        key = str(r.get("risk_key") or "").strip()
        description = str(r.get("description") or "").strip()
        if not key and not description:
            continue
        # The weight the register assigned, quoted in the register's own terms.
        weight: list[str] = []
        if isinstance(r.get("score"), (int, float)):
            weight.append(f"scored {_plain(r['score'])} by the register")
        if r.get("probability_band"):
            weight.append(f"likelihood {r['probability_band']}")
        elif isinstance(r.get("probability"), (int, float)):
            weight.append(f"likelihood {round(float(r['probability']) * 100)} per cent")
        if isinstance(r.get("cost_impact"), (int, float)):
            weight.append(f"cost impact {_money(r['cost_impact'])}")
        if isinstance(r.get("time_impact_days"), (int, float)) and r["time_impact_days"]:
            weight.append(f"time impact {_plain(r['time_impact_days'])} days")

        held = []
        if r.get("owner"):
            held.append(f"owned by {r['owner']}")
        if r.get("response_strategy"):
            held.append(f"response {r['response_strategy']}")
        if r.get("residual_position"):
            held.append(f"residual position {r['residual_position']}")

        name = f"{key}, {description}" if key and description else (key or description)
        sentence = f"{name} is open"
        if weight:
            sentence += ": " + ", ".join(weight)
        if held:
            sentence += ". The register records it " + ", ".join(held)
        out.append({
            "sentence": sentence + ".",
            "risk_key": key or None,
            "owner": r.get("owner") or None,
            "response_strategy": r.get("response_strategy") or None,
            "unmitigated": not r.get("mitigation_status"),
        })
    return out


def notice_findings(notices: list[dict] | None) -> list[dict[str, Any]]:
    """
    What each notice in the period asserts, and what clock it started.

    A DEADLINE IS PRINTED ONLY WHERE ONE WAS DERIVED. Where the document named no contract form,
    the sentence says the deadline is not established and why, rather than leaving a reader to
    assume there is no clock. A LOOKBACK IS NEVER PRINTED AS A DEADLINE: the federal twenty-day
    figure bars no claim and saying it does would be worse than saying nothing.
    """
    out: list[dict[str, Any]] = []
    for n in (notices or []):
        if not isinstance(n, dict):
            continue
        parts: list[str] = []
        served_by, served_on = n.get("served_by"), n.get("served_on")
        if served_by and served_on:
            parts.append(f"{served_by} served notice on {served_on}")
        elif served_by:
            parts.append(f"{served_by} served notice")
        else:
            parts.append("A notice was served")
        if n.get("date_served"):
            parts.append(f"on {n['date_served']}")
        elif n.get("date_served_refusal"):
            parts.append("on a date this platform could not read")
        sentence = " ".join(parts)
        if n.get("claim"):
            sentence += f". It claims {n['claim']}"
        if n.get("references_text"):
            sentence += f". It references {n['references_text']}"

        if n.get("deadline_kind") == "lookback" and n.get("deadline_days"):
            clock = (f"{n['deadline_citation']} sets no notice deadline; costs incurred more "
                     f"than {n['deadline_days']} days before written notice are not "
                     f"recoverable. This bars no claim.")
        elif n.get("deadline_date"):
            clock = (f"The deadline it starts is {n['deadline_date']} "
                     f"({n.get('deadline_citation') or 'the named form'}).")
        else:
            clock = "Not established: " + (n.get("deadline_basis")
                                           or "no deadline could be derived") + "."
        out.append({
            "sentence": sentence.rstrip(".") + ".",
            "clock": clock,
            "filename": n.get("filename"),
            "second_step": (n.get("second_step") or {}).get("basis")
            if isinstance(n.get("second_step"), dict) else None,
        })
    return out


def _plain(value: Any) -> str:
    """A number as the card prints it, unaltered in value."""
    text = f"{float(value):.2f}".rstrip("0").rstrip(".")
    return text or "0"


def _money(value: Any) -> str:
    return f"{int(round(float(value))):,} dollars"


# How many risks the card names. The register is unbounded and the card is not: naming forty
# risks is a list nobody reads, and naming none is the state this change exists to end. The
# count is stated here rather than buried, and the block says how many were left unnamed.
MAX_NAMED_RISKS = 5


def document_evidence(documents: list[dict] | None,
                      risks: list[dict] | None = None,
                      notices: list[dict] | None = None) -> dict[str, Any]:
    """
    What this period's documents establish, each statement naming the document behind it.

    `documents` is `documents._period_documents`' shape: dicts carrying `doc_type`, `filename`
    and `extraction`. Superseded documents are already excluded by that reader, so a replaced
    revision never speaks here.

    Returns `{documents_read, findings, not_established, ranking}`:

      documents_read   every live document in the period, by name and type, so a reader can see
                       what was available to read and not only what it yielded.
      findings         one entry per (document, field) the table above covers and the document
                       actually carries a non-zero whole count for. Each has `sentence`,
                       `filename`, `doc_type`, `field`, `value` and `bearing`.
      not_established  documents present whose content this platform does not store.
      ranking          `{possible: False, reason: ...}` always, today. See the module docstring:
                       the only scores the platform holds are constants, and inventing a
                       replacement here would be the same defect in new clothes.

    A zero count is NOT a finding. "0 non-conformances are open" is a true sentence and a
    useless one on a card whose whole purpose is to surface what a reader would act on; the
    document is still listed in `documents_read`, so its silence is visible as silence.
    """
    docs = [d for d in (documents or []) if isinstance(d, dict)]

    documents_read = [
        {"filename": d.get("filename"), "doc_type": d.get("doc_type")}
        for d in docs
    ]

    by_type: dict[str, list[dict]] = {}
    for d in docs:
        by_type.setdefault(str(d.get("doc_type") or ""), []).append(d)

    findings: list[dict[str, Any]] = []
    for spec in _FINDINGS:
        for d in by_type.get(spec["doc_type"], []):
            extraction = d.get("extraction")
            if not isinstance(extraction, dict):
                continue
            n = _as_int(extraction.get(spec["field"]))
            if n is None or n <= 0:
                continue
            template = spec["singular"] if n == 1 else spec["plural"]
            findings.append({
                "sentence": template.format(n=n),
                "filename": d.get("filename"),
                "doc_type": spec["doc_type"],
                "field": spec["field"],
                "value": n,
                "bearing": spec["bearing"],
            })

    not_established: list[dict[str, Any]] = []
    for doc_type, description in _CONTENT_NOT_STORED.items():
        for d in by_type.get(doc_type, []):
            not_established.append({
                "filename": d.get("filename"),
                "doc_type": doc_type,
                "sentence": (f"This period contains {description}. Its content is not stored, "
                             f"so what it says is not established here."),
            })

    register = register_findings(risks)
    named = len(register)
    live_risks = [r for r in (risks or [])
                  if isinstance(r, dict) and r.get("is_open") is not False]
    return {
        "documents_read": documents_read,
        "findings": findings,
        "not_established": not_established,
        # What the register says, by named risk. `unnamed` is stated rather than left implicit:
        # a card showing five of forty open risks must say it is showing five of forty.
        "register": {
            "open_count": len(live_risks),
            "named": register,
            "unnamed": max(0, len(live_risks) - named),
            # The exposure the register itself supports: probability times cost impact over the
            # rows carrying both numbers, and nothing else. This is the ONLY completion-side
            # figure on this card that has an input behind it, which is why the card prints it
            # and refuses the modules' percentile. See `risk_exposure`.
            "exposure": register_exposure(live_risks),
        },
        # Each notice as the event it is, with the clock it started or the reason none is stated.
        "notices": notice_findings(notices),
        "ranking": {"possible": False, "reason": NO_RANKING_REASON},
    }
