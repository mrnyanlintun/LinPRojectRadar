"""
THE GOVERNANCE DECISION CARD, COMPOSED IN PYTHON FROM STORED READINGS.

WHAT THIS PRODUCES, AND WHAT IT REFUSES TO PRODUCE.

The platform produces a PERFORMANCE FINDING, a DECISION QUESTION and -- from RUN 140,
2026-09-05, BY THE OWNER'S DECISION, THIS RUN BEING THE ORIGIN OF THE CHANGE -- CANDIDATE
MITIGATIONS for every reading that is not Green, aimed exactly one band up: Red toward Amber,
Amber toward Yellow, Yellow toward Green.

WHAT IS STILL REFUSED, AND IT IS MOST OF IT. There is no deadline here, no approval authority,
no assigned owner and no corrective-action template. Every one of those requires an approved
knowledge base the platform does not have, and that reason is unchanged. A card that named who
must act, or by when, would be asserting an authority the instrument has never been given.

WHAT CHANGED IS THE REASON A MITIGATION CAN BE OFFERED AT ALL, and the distinction is the whole
defence. It is NOT that the platform acquired an approved knowledge base -- it did not. It is
that a candidate mitigation is a RECORDED, REPLAYABLE MODEL COMPOSITION: it is composed against
a context built in code from the deciding constant and the canonical quantity, validated before
storage, stored with its composition date, model and provider, and rendered verbatim from
storage. It can be replayed, attributed and refuted. A deadline or an authority cannot be, which
is why those stay refused. The mitigations are also reveal-gated, served only where the
recommendation package is visible, so a participant never meets one before their pre-judgment
is locked.

WHY IT IS PYTHON AND NOT A MODEL. This follows the owner's Run 76 ruling: fusion stays in code,
because identical evidence must yield the same posture. No model decides a status, chooses a
driver, creates a threshold, assigns an authority, or judges evidence adequate.

THE ONE CARVE-OUT, RUN 140. A model COMPOSES CANDIDATE MITIGATIONS, and only those. It is handed
a context built entirely in code -- the band the code decided, the boundary read from the same
constant the band decision reads, and the gap computed from the canonical quantity -- and it
writes prose against figures it did not choose and cannot change. It still decides no status,
no driver, no threshold and no authority. Every figure in a mitigation block is the code's; only
the sentence around it is composed, and that sentence is validated and stored before it is ever
rendered. Every sentence below is assembled from figures already stored by the compute path, and
every one of them names the figure it rests on.

THE FINDING IS DECLARATIVE AND THE MITIGATION IS UNADDRESSED. "The Schedule category shows a
material adverse condition against the approved baseline" is a finding, and every sentence in
the finding, the posture and the question reads like that one.

THE COUNTER-EXAMPLE HAD TO BE REPLACED AT RUN 140, because "Resequence work now" is no longer
far from something the card might carry -- "Resequence the affected work against the verified
critical path" IS a permissible candidate mitigation. The line is not imperative mood; it is
WHO AND WHEN. A candidate names no person, role, team or authority and no date: "the PM should
resequence work by Friday" is forbidden three times over, and "Resequence the affected work
against the verified critical path" is not, because it addresses nobody and dates nothing. A
candidate also invents no figure and reaches across no module the evidence does not join.

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

    `status` is what the instrument stands behind. `fused_band` is the band the WEIGHTED VOTE
    over the assessed categories produced (Run 106 goal one), and it is reported beside an
    "Awaiting analysis" status rather than instead of it, because withholding a posture must
    never conceal an adverse reading.

    RUN 106, GOAL TWO. Where the status is "Awaiting analysis" the SENTENCE saying why comes
    with it, read back off `status_reason` which the status architecture composed. A bare label
    is never rendered: the owner's words are that nobody will understand one word.
    """
    status = basis.get("status")
    official = bool(basis.get("official"))
    out: dict[str, Any] = {"status": status, "official": official}
    if basis.get("fused_band"):
        out["fused_band"] = basis["fused_band"]
    if basis.get("status_reason"):
        out["status_reason"] = basis["status_reason"]
    if basis.get("project_arithmetic"):
        out["project_arithmetic"] = basis["project_arithmetic"]
        out["project_rule_short"] = basis.get("project_rule_short")
        out["project_boundary"] = basis.get("project_boundary")
        out["project_weighted_sum"] = basis.get("project_weighted_sum")
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

    The Awaiting-analysis path is the common case and is built as carefully as the assessed one: it
    names how many required categories carry a posture, how many do not, and -- when an assessed
    category is adverse -- says so in the same sentence, so the withheld posture cannot bury it.
    """
    required = list(basis.get("required_categories") or _REQUIRED_CATEGORIES)
    assessed = list(basis.get("required_assessed") or [])
    missing = list(basis.get("required_missing") or [])
    adverse = [k for k in assessed if _band(cats.get(k, {}).get("status")) in _SEVERITY]
    by_id = {m.get("module_id"): m for m in modules if m.get("module_id")}

    if not basis.get("official"):
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
        # RUN 106, GOAL FIVE. THE ADVERSE MODULE READINGS ARE NAMED WHATEVER THE BAND ABOVE
        # THEM SAYS. Under the weighted rule a project can publish Green with a Red module
        # inside it -- the owner has ruled that and it is not to be softened -- so the finding
        # itself must not be able to close without naming it. The category-level sentence above
        # cannot do that job: an averaging category with a Red module in it can read Yellow or
        # even Green, and `_SEVERITY` does not rank Yellow, so the module vanished from the
        # sentence entirely. This names the MODULE.
        return (
            f"The project posture is {basis['status']}, formed from all "
            f"{len(assessed)} required categories.{adverse_txt}"
            + _adverse_module_sentence(cats, modules, basis))
    return None


#: Every band that is not Green is an adverse reading for the purpose of naming drivers. This is
#: DELIBERATELY WIDER than `_SEVERITY`, which ranks only Red and Amber for ordering: a Yellow
#: module inside a Green project is exactly the reading the owner's Run 106 ruling makes
#: invisible if nothing goes looking for it.
_ADVERSE_BANDS = frozenset({"yellow", "amber", "red"})


def _adverse_readings(cats: Mapping[str, Mapping[str, Any]],
                      modules: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """
    RUN 106, GOAL FIVE. EVERY MODULE READING THAT IS NOT GREEN, WHATEVER SITS ABOVE IT.

    A consequence of the owner's weighted project rule is that a Green project can hold a Red
    module: the module moves its category, the category moves the sum by its weight, and the sum
    can still band Green. The ruling stands. What must not stand is the Red disappearing.

    THE SELECTION IS NOT A JUDGEMENT AND HAS NO THRESHOLD. Every module row whose stored
    `status_color` is Yellow, Amber or Red is here, in severity order. Nothing is filtered by
    category, by whether the module set its category's posture, or by how the project banded.
    """
    by_severity = {"red": 0, "amber": 1, "yellow": 2}
    cat_of = {}
    for key, cat in (cats or {}).items():
        for mid in (cat.get("status_set_by") or []):
            cat_of[mid] = key
    rows: list[dict[str, Any]] = []
    for mod in modules or []:
        band = _band(mod.get("status_color"))
        if band not in _ADVERSE_BANDS:
            continue
        mid = mod.get("module_id")
        key = cat_of.get(mid) or mod.get("category")
        cat = (cats or {}).get(key) or {}
        rows.append({
            "module_id": mid,
            "band": band.title(),
            "category": key,
            "category_name": _cat_name(str(key)) if key else None,
            "category_band": (str(cat.get("status")).title() if cat.get("status") else None),
            "method_class": mod.get("method_class"),
            "reading": mod.get("evidence_metric"),
            "visible_above": ("this reading is more adverse than the band its category "
                              "publishes" if cat.get("status")
                              and by_severity.get(band, 9)
                              < by_severity.get(_band(cat.get("status")), 9) else None),
        })
    rows.sort(key=lambda r: (by_severity.get(_band(r["band"]), 9),
                             str(r.get("category") or ""), str(r.get("module_id") or "")))
    return rows


def _adverse_module_sentence(cats: Mapping[str, Mapping[str, Any]],
                             modules: Sequence[Mapping[str, Any]],
                             basis: Mapping[str, Any]) -> str:
    """The sentence the finding closes with, naming adverse modules under a better status."""
    rows = _adverse_readings(cats, modules)
    if not rows:
        return ""
    named = "; ".join(
        f"{r['module_id']} {r['band']}" + (f" ({r['reading']})" if r.get("reading") else "")
        + (f" in {r['category']} {r['category_name']}" if r.get("category") else "")
        for r in rows)
    return (" ADVERSE READINGS INSIDE THIS POSTURE, named regardless of the band above them: "
            + named + ". The project status is a weighted vote over the five category postures "
            "and an adverse category moves the sum by its weight and no more, so a favourable "
            "project band does not mean these readings were absent, outweighed on their own "
            "terms, or found not to hold. Each is a finding at its own level.")


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
    thin: list[str] = []
    for key in sorted(cats):
        entry = cats.get(key) or {}
        if not entry.get("status") or not entry.get("posture_arithmetic"):
            continue
        # RUN 105, GOAL THREE. A category whose average rests on ONE banded module is MARKED
        # here, not left for the reader to notice that the count in the arithmetic says 1. The
        # marker and the sentence are both READ BACK off the reading; neither is composed here.
        mark = ("ONE READING ONLY -- " if entry.get("posture_single_reading") else "")
        if entry.get("posture_single_reading"):
            thin.append(f"{key} {_cat_name(key)}")
        lines.append(
            f"{mark}{key} {_cat_name(key)} is {_band(entry['status'])}, formed from "
            f"{entry.get('posture_rule_short') or 'its modules'}: "
            f"{entry['posture_arithmetic']}")
    if not lines:
        return None
    if thin:
        lines.append(
            "READ " + (" and ".join(thin))
            + (" with care: it rests" if len(thin) == 1 else " with care: they rest")
            + " on a single banded module, so the average is that module's score and is not "
              "the agreement of several. The platform publishes the posture rather than "
              "withholding it, because a minimum banded count would leave a required category "
              "without a posture and force the whole project to Awaiting analysis; what it will "
              "not do is let the band read as a settled category position.")
    return ("How each category formed its posture. "
            "Four performance categories -- Cost and EVM, Schedule, Cost Risk and "
            "Document-Derived Signals -- average their banded modules' scores, so one weak "
            "module moves the posture without dominating it. Delivery Quality takes the worst "
            "band any of its modules asserted, because quality, safety, environmental and "
            "contractor performance are conformance and compliance measures and an adverse "
            "reading in one of them is a finding in its own right. The project then WEIGHS "
            "those five postures on the owner's profile and bands the sum; since Run 106 it does "
            "NOT take the worst. " + " ".join(lines))


def _why(basis: Mapping[str, Any]) -> str | None:
    """The rule that produced the finding, named. Not a justification -- a derivation."""
    required = list(basis.get("required_categories") or ())
    if not required:
        return None
    if not basis.get("official"):
        return (
            "An official posture is issued only when every required category carries one. "
            f"The required set is {', '.join(required)}. "
            f"{len(basis.get('required_missing') or [])} of them assert no band, so the "
            "posture is withheld rather than imputed. The band the weighted vote produced over "
            "the categories that were assessed is recorded beside it and is not used in its "
            "place.")
    return (
        "The project posture is the WEIGHTED VOTE over the five category postures, on the "
        "owner's weight profile: each posture scores Green +2, Yellow +1, Amber -1, Red -2, the "
        "scores are weighted and summed, and the sum is banded at or above 1.5 Green, 0.5 "
        f"Yellow, -0.5 Amber, below that Red. Every one of the required set "
        f"({', '.join(required)}) carries a band. THERE IS NO OVERRIDE: an adverse category "
        "moves the sum by its own weight and no more, which is why an adverse module reading is "
        "named on this card whatever band sits above it. "
        + str(basis.get("project_arithmetic") or "")
        + " How each CATEGORY formed the band it brings here is stated beside that category "
        "below, because the platform does not use one rule for all of them.")


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
    # RUN 107, SECTION 3. THE FALLBACK IS REMOVED, AND REMOVING IT IS THE POINT.
    #
    # What stood here read `registry.BAND_SOURCES` when a row stored no basis and STAMPED
    # "CODIFIED" onto it. It existed for exactly two modules, A1.7 and A1.8, whose bands were
    # stored without provenance. Both now return through `models.banded` and store their basis,
    # their two provenance classes and their threshold source in the row itself, so the fallback
    # has nothing left to serve -- and while it stood, ANY module that banded without recording
    # a provenance class would have been printed as though a standard fixed its boundary, which
    # is the concealment Run 106 found rather than a compatibility shim.
    #
    # WHAT THIS MEANS FOR A ROW STORED BEFORE THIS RUN, stated plainly rather than hidden: a
    # pre-Run-107 A1.7 or A1.8 row recorded no basis, and the card will now say so in as many
    # words instead of printing a citation the row never held. That is the true statement about
    # that row. Nothing rewrites a stored row, and `registry.BAND_SOURCES` is unchanged and is
    # still the single source of the citation -- `models_evm._evm_band_source` reads it.
    if not provenance:
        return {
            "boundary": None,
            "boundary_basis": None,
            "boundary_provenance": None,
            "boundary_note": ("this module asserted a band without recording the boundary it "
                              "crossed or that boundary's source"),
        }
    # RUN 101. THE BASIS AND THE BOUNDARY MAY HAVE DIFFERENT PROVENANCE, and where they do the
    # card must say so or it presents a platform-chosen cutoff as though a standard fixed it.
    # Only an ANCHOR such as a published industry average is sourced; the intermediate cutoffs
    # drawn around it are platform-chosen with no published basis. (RUN 108 restated this note:
    # it quoted a research report that is not in this repository and was never read.) Both
    # classes are read from stored fields; neither is decided here.
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
    # RUN 121. THE HELD-READING LIMITATION IS DELETED, NOT LEFT BEHIND AS A GUARD.
    #
    # Run 107 printed a separate limitation for a reading held pending a Project Manager's
    # review, because such a reading withheld its band for a reason that was NOT "no threshold
    # was established". The owner has ruled the hold off: Project Manager feedback is a discrete
    # event and no computed posture waits on one, so `pending_pm_review` is no longer a state
    # this platform can produce and `pm_review.MODULE_STATE_PENDING` no longer exists.
    #
    # A dead `if` that can never be true is a limitation nobody can ever see fail, so it is
    # removed rather than kept "just in case". A reading that DOES withhold its band now does so
    # for exactly the reasons the two blocks below state, and `band_withheld_reason` -- which a
    # PM's own Defer or Override still writes -- is printed verbatim by the third.
    pending = [m for m in modules if m.get("calibration_pending")]
    if pending:
        names = ", ".join(sorted({str(m.get("method_class")) for m in pending}))
        out.append(
            f"{len(pending)} readings report a figure without a status colour, because no "
            f"boundary for the quantity has been established from evidence: {names}.")
    # RUN 108. A MODULE THAT WITHHELD ITS BAND NOW SAYS WHAT IT NEEDS, HERE, ON THE CARD.
    #
    # THE DEFECT THIS CLOSES, measured on the page rather than argued: a module that abstained
    # STORED a full sentence naming exactly what was missing -- `band_withheld_reason` -- and
    # the card printed only its method class in a list. The owner's own rule is that a module
    # missing what it needs abstains AND SAYS WHAT IT NEEDS, and a sentence that reaches no
    # surface says nothing to the person reading the page.
    #
    # The reasons are printed VERBATIM from the stored row. Nothing is summarised, nothing is
    # composed here, and no model is asked what a module needed.
    _withheld = [m for m in modules
                 if m.get("status_color") is None and m.get("band_withheld_reason")]
    for m in _withheld[:6]:
        out.append(f"{m.get('method_class') or m.get('module_id')} asserted no band. "
                   f"{m['band_withheld_reason']}")
    if len(_withheld) > 6:
        out.append(f"{len(_withheld) - 6} further readings withheld a band and each states its "
                   f"own reason on its row.")
    if basis.get("required_missing"):
        out.append(
            "No value was imputed for any category that could not be assessed, and no "
            "substitute figure was used in place of one.")
    return out


# ------------------------------------------------------------------ 8. the decision question

def _question(basis: Mapping[str, Any], cats: Mapping[str, Mapping[str, Any]]) -> str | None:
    """
    THE QUESTION PUT TO THE REVIEWER. It is a question, not an instruction.

    It asks what the reviewer makes of the finding. THE QUESTION ITSELF IS UNCHANGED BY RUN 140
    and was deliberately left alone: the card now offers candidate mitigations, so "no remedy is
    offered" is no longer true, but the question still does not ask the reviewer to APPROVE one.
    It asks what they make of the finding, and the mitigations are material for that judgment,
    not a thing to sign. It names no authority, because the platform holds none -- that reason is
    untouched. The disposition set is out of scope for this run and the question at :484-494
    stays open.
    """
    missing = list(basis.get("required_missing") or [])
    assessed_adverse = [k for k in (basis.get("required_assessed") or [])
                        if _band(cats.get(k, {}).get("status")) in _SEVERITY]
    if not basis.get("official"):
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

    RUN 106, GOAL ONE. IT IS NO LONGER A DIAGNOSTIC BESIDE THE STATUS -- IT IS A RESTATEMENT OF
    THE STATUS RULE. The category posture rules still form the five postures (averaging in the
    four performance categories, worst-wins in Delivery Quality); the PROJECT then weighs those
    five on the owner's profile, and B1.2 reports that same weighted vote from the same function.
    It is labelled as a restatement so a reviewer does not read it as a second opinion, and it
    remains excluded from its own category's rollup because it is derived from that rollup.
    """
    b12 = next((m for m in modules if m.get("module_id") == "B1.2"), None)
    if not b12:
        return None
    out: dict[str, Any] = {
        "role": ("restates the project status rule -- the weighted vote over the five category "
                 "postures -- computed by the same function that sets the status, so it is not "
                 "a second opinion and cannot disagree with the band above"),
    }
    for key in ("status_color", "evidence_metric", "weighted_sum", "project_arithmetic",
                "class_votes", "insufficient_data", "abstention_reason_code"):
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
        "posture", "finding", "why", "forecast", "drivers", "adverse_readings", "evidence",
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

    # RUN 106, GOAL FIVE. A BLOCK OF ITS OWN, so an adverse module cannot be lost to the
    # four-row collapse in `drivers` or to a category posture that reads better than it does.
    # Every non-Green module reading is here, in severity order, whatever the project publishes.
    adverse = _adverse_readings(cats, modules)
    if adverse:
        card["adverse_readings"] = {
            "rows": adverse,
            "rule": ("every module reading that is not Green, named regardless of the category "
                     "posture or the project status above it. The project status is a weighted "
                     "vote and an adverse category moves the sum by its weight and no more, so "
                     "a favourable project band is not evidence that these readings were "
                     "absent or outweighed."),
        }

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
