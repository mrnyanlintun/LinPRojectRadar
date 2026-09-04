"""
RUN 106, GOAL ONE. HOW THE PROJECT COMBINES ITS FIVE CATEGORY POSTURES, IN ONE PLACE.

THE OWNER'S RULING, RUN 106 SECTION 1, AND IT REPLACES THE PROJECT-LEVEL RULE.

  The project status is produced by WEIGHTED VOTING over the five category postures. Each
  posture scores on the scale the category rules already use -- Green +2, Yellow +1, Amber -1,
  Red -2 -- the scores are multiplied by the owner's weight profile, summed, and the sum is
  banded on the cuts the category rules already use: at or above 1.5 Green, at or above 0.5
  Yellow, at or above -0.5 Amber, below -0.5 Red.

  His recorded reason for replacing worst-wins: worst-wins at project level means a project is
  almost never Green, everyone lives in permanent alarm, and nobody trusts the dashboard.

NO OVERRIDE, AND THAT IS DELIBERATE. A Red in Delivery Quality moves the sum by 0.16 and no
more. No safety override, no environmental override, and worst-wins is not restored under
another name. THE CONSEQUENCE IS STATED RATHER THAN HIDDEN: a project can publish Green with an
adverse module inside it, so the decision card names every adverse module reading as a material
driver whatever the status above it says (`decision_brief._adverse_readings`, Run 106 goal five).

THE SCALE AND THE CUTS ARE NOT COPIED. `BAND_SCORE` and `AVERAGE_CUTS` are imported from
`category_posture`, which is where the owner's Run 104 scale is written. A second copy could
drift from the first, and two scales that disagree is precisely the defect Run 104 closed at
category level.

THE WEIGHTS ARE NOT COPIED EITHER. They live here now, and `models_gov` imports them under the
name it has always used. Before this run the same five numbers existed only as B1.2 Weighted
Voting's own profile; what changed at Run 106 is not the numbers but their AUTHORITY -- they
decide the project status.

A CATEGORY WITH NO POSTURE IS REMOVED FROM THE DENOMINATOR AND THE REST ARE RENORMALISED.
It is never scored as zero. Zero on this scale sits between Yellow (+1) and Amber (-1) and would
read as a neutral, middling assessment when the truth is that nothing was assessed at all --
a fabricated neutral is indistinguishable from a measured one once it reaches the arithmetic.
Renormalising is the rule `specifications/B1_signal_synthesis.md` shared rule 3 already states
("an abstaining signal casts no vote, CARRIES NO WEIGHT"), the rule `canonical_v5.weighted_voting`
already applies to its eligible signals, and the rule `models_gov.weighted_category_vote` has
applied to these same five categories since Run 89. No fourth rule is invented.

  WHAT RENORMALISATION DOES AND DOES NOT BUY. The REQUIRED-CORE GATE is unchanged by this run
  and sits on top of this rule: unless all five of A1, A2, A3, A4 and A6 carry a posture, no
  status is published at all. So on the published path renormalisation is never reached with a
  category missing -- the gate has already withheld the status. It matters for the band recorded
  BESIDE a withheld status (`fused_band`), which the card shows so that withholding a posture
  cannot conceal an adverse reading, and for B1.2's own reading. It is kept, and honest, rather
  than being replaced by a refusal that the gate already performs.

WITH NO CATEGORY ASSESSED AT ALL there is nothing to weigh and the status is None. Nothing is
returned in place of a reading.
"""

from __future__ import annotations

from typing import Any, Mapping

from .category_posture import AVERAGE_CUTS, BAND_SCORE
from .fusion import BAND_SEVERITY

#: The owner's weight profile, restated at Run 95 section 3 and given PROJECT-LEVEL AUTHORITY by
#: Run 106 section 1. HIS DECISION, NOT A DERIVED OR LITERATURE VALUE AND NOT CALIBRATED.
#: Keyed by registry category key; the comments are the owner's words for those categories.
PROJECT_CATEGORY_WEIGHTS: dict[str, float] = {
    "A1": 0.28,   # Cost and EVM Performance
    "A2": 0.28,   # Schedule
    "A3": 0.17,   # Cost Risk
    "A4": 0.11,   # Document Signals
    "A6": 0.16,   # Delivery Quality
}

#: Executable, so the profile cannot lose its normalisation to an edit that forgets to check.
#:
#: RUN 135. THESE TWO INVARIANTS WERE `assert` STATEMENTS AND ARE NOW EXPLICIT RAISES.
#:
#: The comments beside them said "executable, so the profile cannot ..." -- and under `python -O`
#: they are not executable at all: the interpreter discards an `assert` at compile time, both
#: checks vanish, and a weight profile that does not sum to one, or that has acquired Data
#: Integrity as a criterion, is loaded in silence. Neither of these is a debugging aid. The first
#: is what makes the project rule a WEIGHTED VOTE rather than an arbitrary scaling of one, and the
#: second is the standing ruling that Data Integrity is a PRECONDITION for using the criteria and
#: never a criterion in them. An invariant whose violation changes every published project status
#: is not something to check only when the interpreter feels like it.
#:
#: They raise at import, exactly as the asserts did, and the message each carried is preserved.
if abs(sum(PROJECT_CATEGORY_WEIGHTS.values()) - 1.0) >= 1e-9:
    raise ValueError(
        "the owner's weight profile must sum to one: "
        f"{' + '.join(f'{k} {w:g}' for k, w in PROJECT_CATEGORY_WEIGHTS.items())} = "
        f"{sum(PROJECT_CATEGORY_WEIGHTS.values()):.12g}. The project rule is a WEIGHTED VOTE "
        f"over the five category postures and a profile that does not sum to one makes it a "
        f"scaled one, so every published project status would move. Nothing was loaded.")

#: Data Integrity is a precondition for using the criteria, never a criterion in them. Executable,
#: so the profile cannot acquire it by an edit that forgets the rule. See the Run 135 note above
#: for why this is a raise and not an `assert`.
PROJECT_EXCLUDED_CATEGORIES: frozenset[str] = frozenset({"C1"})

if set(PROJECT_CATEGORY_WEIGHTS) & PROJECT_EXCLUDED_CATEGORIES:
    raise ValueError(
        "Data Integrity is a precondition for using the criteria, not a criterion in them. "
        f"The weight profile names {sorted(set(PROJECT_CATEGORY_WEIGHTS) & PROJECT_EXCLUDED_CATEGORIES)}, "
        f"which is excluded from the project vote. Nothing was loaded.")

WEIGHT_PROVENANCE = ("the owner's stated authority, Run 95 section 3 restated at Run 106 section "
                     "1: his decision, not a derived or literature value and not calibrated")

PROJECT_RULE = "weighted_vote_over_category_postures"

PROJECT_RULE_SHORT = "the weighted vote over its five category postures"

PROJECT_BOUNDARY_WORDS = (
    "on the weighted sum of the five category postures' scores -- Green +2, Yellow +1, Amber -1, "
    "Red -2 -- weighted "
    + ", ".join(f"{k} {w:g}" for k, w in PROJECT_CATEGORY_WEIGHTS.items())
    + ": at or above 1.5 is Green; at or above 0.5 and below 1.5 is Yellow; at or above -0.5 and "
      "below 0.5 is Amber; below -0.5 is Red. Each boundary is INCLUSIVE ON ITS LOWER SIDE. "
      "There is no override: an adverse category moves the sum by its own weight and no more.")

PROJECT_RULE_WORDS = (
    "the project weighs its five category postures by the owner's profile and bands the sum. "
    "Worst-wins was replaced at Run 106 because at project level it meant a project was almost "
    "never Green, which puts every reader in permanent alarm and destroys trust in the "
    "dashboard. An adverse category is not overridden away and is not allowed to dominate: it "
    "moves the sum by its weight, and the adverse module readings behind it are named on the "
    "card whatever band sits above them.")


def band_weighted(score: float) -> str:
    """Band a weighted sum on the owner's cuts. The Red arm is the open bottom."""
    for cut, band in AVERAGE_CUTS:
        if score >= cut:
            return band
    return "Red"


def project_posture(category_statuses: Mapping[str, Any] | None) -> dict[str, Any]:
    """
    The project's posture and the arithmetic that produced it.

    `category_statuses` is the rollup this platform already builds -- key -> entry with a
    `status` -- and only the five weighted categories are read from it. A category carrying no
    posture is listed as unassessed, is dropped from the denominator, and is NEVER scored.

    Returns `status` None when no weighted category carries a posture. The caller decides what
    to publish; the required-core gate lives with the caller, not here.
    """
    cats = category_statuses if isinstance(category_statuses, Mapping) else {}
    present: dict[str, str] = {}
    unassessed: list[str] = []
    for key in PROJECT_CATEGORY_WEIGHTS:
        entry = cats.get(key)
        band = (entry or {}).get("status") if isinstance(entry, Mapping) else None
        band = str(band).capitalize() if band else None
        if band in BAND_SEVERITY:
            present[key] = band
        else:
            unassessed.append(key)

    record: dict[str, Any] = {
        "status": None,
        "project_rule": PROJECT_RULE,
        "project_rule_short": PROJECT_RULE_SHORT,
        "project_rule_words": PROJECT_RULE_WORDS,
        "project_boundary": PROJECT_BOUNDARY_WORDS,
        "weights": dict(PROJECT_CATEGORY_WEIGHTS),
        "weight_provenance": WEIGHT_PROVENANCE,
        "assessed_categories": sorted(present),
        "unassessed_categories": unassessed,
        "renormalised": bool(unassessed) and bool(present),
        "normalised_weights": {},
        "category_scores": [],
        "weighted_sum": None,
        "project_arithmetic": None,
    }
    if not present:
        record["project_arithmetic"] = (
            "None of the five weighted categories carries a posture, so there is nothing to "
            "weigh and no project posture is formed. That is an absence of a reading, not a "
            "favourable one, and no category was scored as zero to fill the gap.")
        return record

    total = sum(PROJECT_CATEGORY_WEIGHTS[k] for k in present)
    weights = {k: PROJECT_CATEGORY_WEIGHTS[k] / total for k in present}
    record["normalised_weights"] = {k: round(v, 6) for k, v in weights.items()}
    contributions = []
    for key in sorted(present):
        band = present[key]
        score = BAND_SCORE[band]
        contributions.append({"category": key, "band": band, "score": score,
                              "weight": PROJECT_CATEGORY_WEIGHTS[key],
                              "normalised_weight": round(weights[key], 6),
                              "contribution": round(weights[key] * score, 6)})
    # Summed from the UNROUNDED normalised weights, then rounded to ten places so a repeated
    # binary fraction cannot put the sum a hair under a cut it is exactly on. The figure the
    # record publishes is rounded to four, which is what a hand check reads.
    weighted_sum = round(sum(weights[c["category"]] * c["score"] for c in contributions), 10)
    status = band_weighted(weighted_sum)
    record["category_scores"] = contributions
    record["weighted_sum"] = round(weighted_sum, 4)
    record["status"] = status
    record["project_arithmetic"] = (
        "; ".join(f"{c['category']} {c['band']} {c['score']:+.0f} x {c['normalised_weight']:.4g}"
                  for c in contributions)
        + f" -- weighted sum {weighted_sum:+.4g}, which crosses into {status}."
        + ((" " + str(len(unassessed)) + " of the five weighted categories carr"
            + ("ies" if len(unassessed) == 1 else "y") + " no posture ("
            + ", ".join(unassessed) + "), so it was REMOVED FROM THE DENOMINATOR and the "
            "remaining weights renormalised over " + ", ".join(sorted(present))
            + ". An unassessed category is never scored as zero, which would read as a neutral "
              "assessment when nothing was assessed at all.")
           if unassessed else
           " All five weighted categories carry a posture, so the owner's weights are used "
           "unaltered."))
    return record
