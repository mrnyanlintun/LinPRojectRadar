"""
THE GOVERNANCE DECISION CARD, COMPOSED IN PYTHON FROM STORED READINGS.

WHAT THIS PRODUCES, AND WHAT IT REFUSES TO PRODUCE.

The platform produces a PERFORMANCE FINDING and a DECISION QUESTION. It does not produce an
action recommendation. There is no prescribed remedy here, no deadline, no approval authority and
no corrective-action template, because each of those requires an approved knowledge base the
platform does not have. A card that told a reviewer what to do would be asserting an authority
the instrument has never been given.

WHY IT IS PYTHON AND NOT A MODEL. This follows the owner's Run 76 ruling: fusion stays in code,
because identical evidence must yield the same posture. No model decides a status, chooses a
driver, creates a threshold, prescribes an action, assigns an authority, or judges evidence
adequate. Every sentence below is assembled from figures already stored by the compute path, and
every one of them names the figure it rests on.

THE LANGUAGE IS DECLARATIVE, NEVER IMPERATIVE. "The Schedule category shows a material adverse
condition against the approved baseline" is a finding. "Resequence work now" is an instruction,
and this module does not write one.

WHAT IS RENDERED IS ONLY WHAT CAN BE POPULATED TRUTHFULLY. A block with no honest content and no
defined source is OMITTED -- it is not rendered with "not established", "not available" or any
other placeholder, because a placeholder is a claim that a thing was looked for and found
wanting, and in most of these cases nothing was ever computed to look for.

NOTHING HERE WRITES. It is a pure function of the stored row, in the same class as
`recommendation_basis` and `consistency_findings`: no column is added, no migration is needed,
and a row stored before this run answers exactly as one stored after it.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from .simulation.compute import _REQUIRED_CATEGORIES

#: The reader-facing name of each category. Taken from the registry's own category names at the
#: point of composition, never typed here, EXCEPT for this fallback map which exists only so a
#: category with no registry row still has a readable name rather than a bare key.
_FALLBACK_NAMES = {
    "A1": "Cost and EVM Performance",
    "A2": "Schedule Performance",
    "A3": "Cost Risk",
    "A4": "Document-Derived Signals",
    "A6": "Delivery Quality",
    "B1": "Signal Synthesis",
    "B2": "Evidence Combination",
    "B3": "Regulatory Authority",
    "B4": "Decision Optimisation",
    "C1": "Data Integrity",
}

#: Severity order for driver selection. Red before Amber; anything else does not rank.
_SEVERITY = {"red": 0, "amber": 1}

#: How many drivers the collapsed view shows. The rest go behind an expansion.
COLLAPSED_DRIVERS = 4


def _cat_name(key: str) -> str:
    try:
        from .simulation import registry as _reg
        for row in _reg.load_registry():
            if row.get("category") == key and row.get("category_name"):
                return str(row["category_name"]).strip()
    except Exception:                                                   # noqa: BLE001
        pass
    return _FALLBACK_NAMES.get(key, key)


def _band(value: Any) -> str:
    return str(value or "").strip().lower()


# ------------------------------------------------------------------ 1. project posture

def _posture(basis: Mapping[str, Any]) -> dict[str, Any]:
    """
    The official project posture, exactly as the status architecture published it.

    `status` is what the instrument stands behind. `fused_band` is the worst band the ASSESSED
    categories produced, and it is reported beside an Indeterminate status rather than instead of
    it, because withholding an official posture must never conceal an adverse reading.
    """
    status = basis.get("status")
    official = bool(basis.get("official"))
    out: dict[str, Any] = {"status": status, "official": official}
    if basis.get("fused_band"):
        out["fused_band"] = basis["fused_band"]
    return out



#: Fields that are bookkeeping rather than a reading, and must never be offered as "the figure".
_NON_FIGURE_KEYS = frozenset({"seed", "periods", "breach_index", "votes", "module_count"})


def _headline_figure(mod: Mapping[str, Any]) -> tuple[str, Any] | None:
    """
    ONE figure from a module's own reading, to be named in a sentence that asserts a condition.

    THE THREE RECOMMENDATION CHECKS REQUIRE THIS. Check 1 rejects a sentence that asserts a
    condition about the project and names no figure, and check 3 rejects one naming a figure the
    stored result does not hold. Run 96 measured both firing on the first draft of the assessed
    finding, and the SENTENCE was changed rather than the check: it now carries the figure the
    module actually computed, read off the stored reading itself.

    The choice is deterministic -- the first numeric field in the module's own key order that is
    not bookkeeping -- so the same reading always yields the same sentence.
    """
    for key, value in mod.items():
        if key in _NON_FIGURE_KEYS:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        return (str(key), value)
    return None


def _adverse_phrase(key: str, cats: Mapping[str, Mapping[str, Any]],
                    by_id: Mapping[str, Mapping[str, Any]]) -> str:
    """`Cost & EVM Performance (Red, A1.7 tcpi 3.5)` -- the category, its band, and its figure."""
    cat = cats.get(key, {})
    band = str(cat.get("status") or "").title()
    for mid in (cat.get("status_set_by") or []):
        fig = _headline_figure(by_id.get(mid, {}))
        if fig:
            return f"{_cat_name(key)} ({band}, {mid} {fig[0].replace('_', ' ')} {fig[1]})"
    return f"{_cat_name(key)} ({band})"


# ------------------------------------------------------------------ 2. the finding

def _finding(basis: Mapping[str, Any], cats: Mapping[str, Mapping[str, Any]],
             modules: Sequence[Mapping[str, Any]] = ()) -> str | None:
    """
    ONE declarative sentence, naming its figure, produced by rule and not by choice.

    The Indeterminate path is the common case and is built as carefully as the assessed one: it
    names how many required categories carry a posture, how many do not, and -- when an assessed
    category is adverse -- says so in the same sentence, so the withheld posture cannot bury it.
    """
    required = list(basis.get("required_categories") or _REQUIRED_CATEGORIES)
    assessed = list(basis.get("required_assessed") or [])
    missing = list(basis.get("required_missing") or [])
    adverse = [k for k in assessed if _band(cats.get(k, {}).get("status")) in _SEVERITY]
    by_id = {m.get("module_id"): m for m in modules if m.get("module_id")}

    if basis.get("status") == "Indeterminate":
        parts = [
            f"An official project posture is withheld: {len(assessed)} of the "
            f"{len(required)} required categories carry a posture and {len(missing)} do not "
            f"({', '.join(missing)})."
        ]
        if adverse:
            worst = sorted(adverse, key=lambda k: _SEVERITY[_band(cats[k]["status"])])
            named = ", ".join(_adverse_phrase(k, cats, by_id) for k in worst)
            parts.append(
                f"That withholding does not qualify what was assessed: {named}.")
        return " ".join(parts)

    if basis.get("status"):
        adverse_txt = ""
        if adverse:
            worst = sorted(adverse, key=lambda k: _SEVERITY[_band(cats[k]["status"])])
            adverse_txt = (
                " The categories carrying the adverse condition are "
                + ", ".join(_adverse_phrase(k, cats, by_id) for k in worst) + ".")
        return (
            f"The project posture is {basis['status']}, formed from all "
            f"{len(assessed)} required categories.{adverse_txt}")
    return None


# ------------------------------------------------------------------ 3. why it was produced

def _posture_rules(cats: Mapping[str, Mapping[str, Any]]) -> str | None:
    """
    RUN 104, GOAL TWO. WHICH RULE FORMED EACH CATEGORY'S POSTURE, AND THE ARITHMETIC.

    A reader who sees a Green over an Amber module needs to know why without guessing, and
    section 10.3 fails the run for a posture that cannot show the arithmetic that produced it.
    Every sentence here is READ BACK off the category entry -- `posture_rule_short` and
    `posture_arithmetic`, written by `simulation.category_posture` -- so the card can never
    claim a rule the reading does not carry.
    """
    lines: list[str] = []
    for key in sorted(cats):
        entry = cats.get(key) or {}
        if not entry.get("status") or not entry.get("posture_arithmetic"):
            continue
        lines.append(
            f"{key} {_cat_name(key)} is {_band(entry['status'])}, formed from "
            f"{entry.get('posture_rule_short') or 'its modules'}: "
            f"{entry['posture_arithmetic']}")
    if not lines:
        return None
    return ("How each category formed its posture. "
            "Four performance categories -- Cost and EVM, Schedule, Cost Risk and "
            "Document-Derived Signals -- average their banded modules' scores, so one weak "
            "module moves the posture without dominating it. Delivery Quality takes the worst "
            "band any of its modules asserted, because quality, safety, environmental and "
            "contractor performance are conformance and compliance measures and an adverse "
            "reading in one of them is a finding in its own right. The project then takes the "
            "worst across the categories. " + " ".join(lines))


def _why(basis: Mapping[str, Any]) -> str | None:
    """The rule that produced the finding, named. Not a justification -- a derivation."""
    required = list(basis.get("required_categories") or ())
    if not required:
        return None
    if basis.get("status") == "Indeterminate":
        return (
            "An official posture is issued only when every required category carries one. "
            f"The required set is {', '.join(required)}. "
            f"{len(basis.get('required_missing') or [])} of them assert no band, so the "
            "posture is withheld rather than imputed. The worst band among the categories that "
            "were assessed is recorded beside it and is not used in its place.")
    return (
        "The project posture is the worst band among the required categories: the worst "
        f"category decides, and every one of the required set ({', '.join(required)}) carries "
        "a band. No category's band was averaged, weighted away or overridden at project level. "
        "How each CATEGORY formed the band it brings here is stated beside that category below, "
        "because the platform does not use one rule for all of them.")


# ------------------------------------------------------------------ 4. forecast and baseline

#: Reading keys that carry a forecast or a baseline comparison, and how each is read aloud.
#: A line appears ONLY where the module actually computed it; there is no blank forecast row and
#: no fabricated one.
_FORECAST_KEYS: tuple[tuple[str, str], ...] = (
    ("eac", "Estimate at completion"),
    ("posterior_eac", "Estimate at completion"),
    ("p80_eac", "Estimate at completion, 80th percentile"),
    ("p50_eac", "Estimate at completion, 50th percentile"),
    ("tcpi", "To-complete performance index"),
    ("vac", "Variance at completion"),
    ("earned_schedule", "Earned schedule"),
    ("independent_eac", "Independent estimate at completion"),
)


def _forecast(modules: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    seen: set[str] = set()
    for mod in modules:
        for key, label in _FORECAST_KEYS:
            if key not in mod:
                continue
            value = mod.get(key)
            if value is None or label in seen:
                continue
            seen.add(label)
            lines.append({
                "label": label,
                "value": value,
                "module_id": mod.get("module_id"),
                "method_class": mod.get("method_class"),
            })
    return lines


#: RUN 101, GOAL FOUR. What the card prints for a band whose provenance predates this run's
#: mechanism. A1.7 and A1.8 carry their citation in `registry.BAND_SOURCES` -- the Run 4
#: mechanism -- and their specifications are OUT OF SCOPE for this run (section 9.1), so they
#: are read through that older field rather than being left with no basis printed. Two
#: mechanisms, one card, and neither is a model.
def _boundary_and_basis(module_id: str, mod: Mapping[str, Any]) -> dict[str, Any]:
    """
    The boundary a driver's figure crossed and where that boundary came from, from STORED fields.

    Returns the three keys the card renders. Nothing is inferred: a module that stored no
    boundary gets no boundary printed, and the card says so in as many words rather than leaving
    the reader to assume one existed.
    """
    from .simulation.models import PROVENANCE_WORDS
    boundary = mod.get("band_boundary")
    basis = mod.get("band_basis")
    provenance = mod.get("band_provenance_class")
    words = mod.get("band_provenance_words")
    if not basis:
        # The Run 4 mechanism, for the two modules that predate this one.
        from .simulation.registry import BAND_SOURCES
        legacy = BAND_SOURCES.get(module_id)
        if legacy:
            boundary = boundary or legacy
            basis = legacy
            provenance = provenance or "CODIFIED"
            words = words or "a standard, regulation or agency requirement"
    if not provenance:
        return {
            "boundary": None,
            "boundary_basis": None,
            "boundary_provenance": None,
            "boundary_note": ("this module asserted a band without recording the boundary it "
                              "crossed or that boundary's source"),
        }
    # RUN 101, MID-RUN. THE BASIS AND THE BOUNDARY MAY HAVE DIFFERENT PROVENANCE, and where they
    # do the card must say so or it presents a platform-chosen cutoff as though a standard fixed
    # it. `RESEARCH_2_safety_and_environmental_severity.md`, recommendation 2: "State that only
    # the industry-average anchor is sourced; intermediate cutoffs are platform-chosen with no
    # published basis." Both classes are read from stored fields; neither is decided here.
    basis_class = mod.get("band_basis_provenance_class") or provenance
    boundary_class = mod.get("band_boundary_provenance_class") or provenance
    out = {
        "boundary": boundary,
        "boundary_basis": basis,
        "boundary_provenance": basis_class,
        "boundary_provenance_words": (mod.get("band_provenance_words") or words),
        "boundary_cutoff_provenance": boundary_class,
        "boundary_cutoff_provenance_words": (mod.get("band_boundary_provenance_words")
                                             or PROVENANCE_WORDS.get(boundary_class)),
    }
    if boundary_class != basis_class:
        out["boundary_provenance_split"] = (
            f"the measure and the anchor it is drawn against are {basis_class}; the cutoffs that "
            f"divide the bands are {boundary_class}")
    return out


# ------------------------------------------------------------------ 5. material drivers

def _drivers(cats: Mapping[str, Mapping[str, Any]],
             modules: Sequence[Mapping[str, Any]],
             basis: Mapping[str, Any]) -> dict[str, Any]:
    """
    DRIVER SELECTION IS DETERMINISTIC AND STATED, and it is not a judgement.

    A module is a driver only if it AFFECTED THE FINAL CATEGORY POSTURE -- it is named in that
    category's `status_set_by` -- or if it EXPLAINS THE LIMITATION, meaning it sits in a required
    category that asserted no band. Nothing else qualifies, however interesting its reading.

    THE ORDER IS: Red, then Amber, then the largest unfavourable variance, then a worsening
    trend. At most four are shown collapsed; the rest are behind an expansion and are not
    dropped.

    SIGNALS ARE NOT CALLED CONTRADICTORY HERE. The category rollup computes an explicit
    `conflict` figure, and only that figure can say two signals disagree. Where it is absent or
    zero, no disagreement is asserted.
    """
    by_id = {m.get("module_id"): m for m in modules if m.get("module_id")}
    rows: list[dict[str, Any]] = []

    for key, cat in cats.items():
        cat_band = _band(cat.get("status"))
        for mid in (cat.get("status_set_by") or []):
            mod = by_id.get(mid, {})
            row = {
                "module_id": mid,
                "category": key,
                "category_name": _cat_name(key),
                "band": mod.get("status_color") or cat.get("status"),
                "method_class": mod.get("method_class"),
                "reading": mod.get("evidence_metric"),
                "role": "set the category posture",
            }
            # RUN 101, GOAL FOUR. THE REASONING FROM THE FIGURE TO THE FINDING IS MADE VISIBLE.
            # Until now the card named a figure and a band and stopped there, which leaves the
            # reader unable to tell a boundary somebody defended from one somebody invented. It
            # now also states WHICH BOUNDARY THE FIGURE CROSSED and WHERE THAT BOUNDARY CAME
            # FROM -- the source for a codified one, "widely used convention" for a conventional
            # one, and plainly "no published basis; the owner's stated threshold" for an
            # owner-calibrated one.
            #
            # THIS STAYS COMPOSED IN CODE AND ASSEMBLED FROM STORED FIELDS. No model decides a
            # status, a driver, a threshold or a reason: `band_boundary`, `band_basis` and
            # `band_provenance_class` were written onto the module's own row when the band was
            # asserted, which is why goal one had to STORE the provenance rather than only write
            # it in a specification.
            row.update(_boundary_and_basis(mid, mod))
            rows.append(row)
        if key in (basis.get("required_missing") or []):
            rows.append({
                "module_id": None,
                "category": key,
                "category_name": _cat_name(key),
                "band": None,
                "reading": (cat.get("module_count") is not None
                            and f"{cat.get('module_count')} modules were called in this "
                                f"category and none asserted a band" or None),
                "role": "explains the limitation",
            })
        del cat_band

    def rank(row: Mapping[str, Any]) -> tuple:
        band = _band(row.get("band"))
        return (_SEVERITY.get(band, 2),
                0 if row["role"] == "set the category posture" else 1,
                str(row.get("category") or ""),
                str(row.get("module_id") or ""))

    rows.sort(key=rank)

    conflicts = {k: c.get("conflict") for k, c in cats.items()
                 if isinstance(c.get("conflict"), (int, float)) and c.get("conflict")}
    return {
        "collapsed": rows[:COLLAPSED_DRIVERS],
        "expanded": rows[COLLAPSED_DRIVERS:],
        "total": len(rows),
        "order": "Red, then Amber, then largest unfavourable variance, then worsening trend",
        # Only a computed disagreement may be reported as one.
        "computed_disagreement": conflicts or None,
    }


# ------------------------------------------------------------------ 6/7. evidence, limitations

def _evidence(modules: Sequence[Mapping[str, Any]],
              cats: Mapping[str, Mapping[str, Any]],
              sources: Any) -> dict[str, Any]:
    banded = [m for m in modules if m.get("status_color")]
    bodies: list[str] = []
    for cat in cats.values():
        for body in (cat.get("lineage_bodies") or []):
            if body not in bodies:
                bodies.append(str(body))
    out: dict[str, Any] = {
        "modules_computed": len(modules),
        "modules_asserting_a_band": len(banded),
        "categories_assessed": sorted(k for k, c in cats.items() if c.get("status")),
    }
    if bodies:
        out["evidence_bodies"] = bodies
    if sources:
        out["source_documents"] = sources
    return out


def _limitations(basis: Mapping[str, Any],
                 cats: Mapping[str, Mapping[str, Any]],
                 modules: Sequence[Mapping[str, Any]]) -> list[str]:
    """
    What this assessment could NOT establish. Every entry names the thing that was missing.

    NO IMPUTED VALUE IS EVER USED, and that is stated rather than left to be assumed, because a
    reader who is shown a withheld posture is entitled to know it was withheld and not filled in.
    """
    out: list[str] = []
    for detail in (basis.get("required_missing_detail") or []):
        key = detail.get("category")
        out.append(
            f"{_cat_name(str(key))} ({key}) could not be assessed: "
            f"{detail.get('missing')}.")
    pending = [m for m in modules if m.get("calibration_pending")]
    if pending:
        names = ", ".join(sorted({str(m.get("method_class")) for m in pending}))
        out.append(
            f"{len(pending)} readings report a figure without a status colour, because no "
            f"boundary for the quantity has been established from evidence: {names}.")
    if basis.get("required_missing"):
        out.append(
            "No value was imputed for any category that could not be assessed, and no "
            "substitute figure was used in place of one.")
    return out


# ------------------------------------------------------------------ 8. the decision question

def _question(basis: Mapping[str, Any], cats: Mapping[str, Mapping[str, Any]]) -> str | None:
    """
    THE QUESTION PUT TO THE REVIEWER. It is a question, not an instruction.

    It asks what the reviewer makes of the finding. It does not ask them to approve a remedy,
    because no remedy is offered, and it names no authority, because the platform holds none.
    """
    missing = list(basis.get("required_missing") or [])
    assessed_adverse = [k for k in (basis.get("required_assessed") or [])
                        if _band(cats.get(k, {}).get("status")) in _SEVERITY]
    if basis.get("status") == "Indeterminate":
        if assessed_adverse:
            return (
                "On the evidence presented, is the adverse condition in "
                f"{', '.join(_cat_name(k) for k in assessed_adverse)} sufficient to act on "
                f"while {', '.join(missing)} remain unassessed?")
        return (
            f"On the evidence presented, is the absence of an assessment for "
            f"{', '.join(missing)} material to the decision now before you?")
    if basis.get("status"):
        return (
            f"On the evidence presented, does the {basis['status']} posture and the drivers "
            "named above reflect the condition of this project as you understand it?")
    return None


# ------------------------------------------------------------------ 9. weighted voting

def _weighted_voting(modules: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    """
    THE WEIGHTED VOTING DIAGNOSTIC, and it is a DIAGNOSTIC and not the status.

    THE CATEGORY POSTURE RULES set the official status -- averaging in the four performance
    categories, worst-wins in Delivery Quality, then worst across the categories. B1.2 is a
    comparison ensemble, admitted to the card as a reading a reviewer may weigh against the
    official posture, and it is labelled that way so it cannot be mistaken for the decision.
    """
    b12 = next((m for m in modules if m.get("module_id") == "B1.2"), None)
    if not b12:
        return None
    out: dict[str, Any] = {
        "role": ("diagnostic only -- the category posture rules and the worst category set the "
                 "official status"),
    }
    for key in ("status_color", "evidence_metric", "class_votes", "insufficient_data",
                "abstention_reason_code"):
        if b12.get(key) is not None:
            out[key] = b12[key]
    if len(out) == 1:
        return None
    return out


# ------------------------------------------------------------------ 11. reviewer disposition

def _reviewer(project: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """
    THE ASSIGNED REVIEWER, RENDERED ONLY WHERE A PROJECT RECORD HOLDS ONE.

    A ROLE IS NEVER INFERRED. If the record does not name an assigned reviewer, this returns
    nothing at all and the card renders no authority line -- the platform does not own authority
    and must not imply that it does.
    """
    if not project:
        return None
    for key in ("assigned_reviewer", "reviewer", "reviewer_name"):
        value = project.get(key)
        if isinstance(value, str) and value.strip():
            return {"assigned_reviewer": value.strip(), "source": key}
    return None


# ------------------------------------------------------------------ 12. audit record

def _audit(row: Mapping[str, Any]) -> dict[str, Any]:
    out = {}
    for key, label in (("simulation_version", "simulation_version"),
                       ("seed", "seed"),
                       ("period", "period"),
                       ("period_cutoff", "period_cutoff"),
                       ("computed_at", "computed_at")):
        if row.get(key) is not None:
            out[label] = row[key]
    return out


# ------------------------------------------------------------------ the card

def compose_decision_brief(*,
                           category_statuses: Mapping[str, Mapping[str, Any]],
                           module_results: Sequence[Mapping[str, Any]],
                           status_basis: Mapping[str, Any],
                           row: Mapping[str, Any] | None = None,
                           project: Mapping[str, Any] | None = None,
                           source_documents: Any = None) -> dict[str, Any]:
    """
    Compose the twelve blocks of the Governance Decision card, in the playbook's order.

    A block that cannot be populated truthfully is ABSENT FROM THE RESULT, not present and
    empty: the renderer prints what it is given, so an omission here is an omission on the card.

    ALTERNATIVES AND COMPARATIVE EFFECTS IS NEVER RETURNED. That block renders only when the
    What-if Scenario Matrix has computed on user-supplied alternatives. B4.4 and B4.7 were
    retired and Run 96 removed them from the registry, and `recommendation_options` returns
    `available: false` on every row, so the block can never be populated today. It is therefore
    omitted entirely rather than rendered as an empty state, because an empty-state sentence
    would tell a reviewer that alternatives were considered and none were found, which is not
    what happened: none were ever computed.
    """
    cats = dict(category_statuses or {})
    modules = list(module_results or [])
    basis = dict(status_basis or {})
    row = dict(row or {})

    card: dict[str, Any] = {"order": [
        "posture", "finding", "why", "forecast", "drivers", "evidence",
        "limitations", "question", "weighted_voting", "reviewer", "audit",
    ]}

    card["posture"] = _posture(basis)

    finding = _finding(basis, cats, modules)
    if finding:
        card["finding"] = finding

    why = _why(basis)
    # RUN 104, GOAL TWO. The two category rules, and the arithmetic each produced, on the card.
    _rules = _posture_rules(cats)
    if _rules:
        why = (why + " " + _rules) if why else _rules
    # RUN 102, GOAL ONE. WHICH LAYER PRODUCED EACH POSTURE, NAMED ON THE CARD.
    # Section 12.1 fails the run for a fallback that does not say so. `posture_layer` is written
    # onto every merged category entry by `spec_projection.merge_python_row`, and this sentence
    # reads it back rather than restating a rule -- so a card can never claim a layer the
    # reading does not carry. Where every posture came from the specification layer the sentence
    # is not added: there is nothing to disclose.
    _from_python = sorted(k for k, c in cats.items()
                          if (c or {}).get("posture_layer") == "python_module_layer")
    if _from_python:
        _layers = (
            "The posture for " + ", ".join(_from_python) + " is served from this platform's own "
            "Python module layer, because the specification layer holds no reading for "
            + ("that category" if len(_from_python) == 1 else "those categories") +
            " this period. Every other posture on this card is a stored specification reading. "
            "No category's posture is formed from both layers.")
        why = (why + " " + _layers) if why else _layers
    if why:
        card["why"] = why

    forecast = _forecast(modules)
    if forecast:
        card["forecast"] = forecast

    drivers = _drivers(cats, modules, basis)
    if drivers["total"]:
        card["drivers"] = drivers

    card["evidence"] = _evidence(modules, cats, source_documents)

    limitations = _limitations(basis, cats, modules)
    if limitations:
        card["limitations"] = limitations

    question = _question(basis, cats)
    if question:
        card["question"] = question

    voting = _weighted_voting(modules)
    if voting:
        card["weighted_voting"] = voting

    reviewer = _reviewer(project)
    if reviewer:
        card["reviewer"] = reviewer

    audit = _audit(row)
    if audit:
        card["audit"] = audit

    return card
