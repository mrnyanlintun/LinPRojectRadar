"""
RUN 104. HOW A CATEGORY FORMS ITS POSTURE, AND THE ONE PLACE THE TWO RULES ARE WRITTEN.

THE DEFECT THIS CLOSES. Run 103 measured a project publishing Green with A6.4 Contractor
Performance reading Amber inside it. The Python rollup formed a category posture through
`fusion.fuse_signals`, which treats modules that declare no lineage as independent bodies of
evidence, so three Greens outvoted one Amber and the category read greener than the evidence.
The safeguard inside `fuse_signals` -- whose own docstring warns that an undeclared signal
would make the fusion read greener than the evidence -- never fired, because
`qualification_gate.qualify()` manufactures an empty lineage record for a module that declares
none, so nothing was ever *undeclared* by the time the fusion saw it.

THE OWNER'S RULING, RUN 104 SECTION 2, AND IT IS NOT "RESTORE WORST-WINS EVERYWHERE".
Different categories deserve different treatment and the platform now says so plainly:

  AVERAGING -- A1 Cost and EVM Performance, A2 Schedule, A3 Cost Risk, A4 Document Signals.
    These are PERFORMANCE MEASURES. One weak module among several should move the posture
    without dominating it. Each banded module scores Green +2, Yellow +1, Amber -1, Red -2;
    the scores are averaged over ONLY the modules that asserted a band; the average is banded.

  WORST-WINS -- A6 Delivery Quality Performance. Quality, safety, environmental and contractor
    performance are CONFORMANCE AND COMPLIANCE MEASURES. An adverse reading in any of them is a
    finding in its own right and is not averaged against three good ones. The owner's recorded
    reasoning: contractor performance covers timely submittals, incorporation into the general
    contractor's management, timely execution and safety compliance -- it is a compliance
    measure, not a score to be averaged away. A single Amber makes the category Amber; a single
    Red makes it Red.

A MODULE THAT DID NOT BAND IS NOT IN THE AVERAGE AND IS NOT A ZERO. Computed-without-a-band,
abstained and failed alike contribute nothing: zero would be a fabricated middling reading, and
a fabricated neutral is indistinguishable from a measured one once it reaches the arithmetic.
A category where NO module banded carries NO posture, exactly as before this run.

CATEGORIES THE OWNER'S ORDER DOES NOT ASSIGN KEEP THE RULE THEY HAD. The order names five
categories. B1 Signal Synthesis and C1 Data Integrity are not among them, are not in the
required core, and are not performance measures; their rule is therefore UNCHANGED
(worst-wins), and that is recorded here as a default rather than left to silence. No vocabulary
is widened and no threshold is invented for them.

THE PROJECT STATUS IS NOT TOUCHED. It is still the worst band across the contributing
categories, subject to the required-core gate and Indeterminate. This module changes how a
CATEGORY forms its posture and nothing else.
"""

from __future__ import annotations

from typing import Any, Iterable

from .fusion import BAND_SEVERITY, worst_band

#: The two rules, by name.
RULE_AVERAGE = "average_of_module_scores"
RULE_WORST = "worst_wins"

#: Which rule forms which category's posture. The owner's Run 104 assignment, section 2.
CATEGORY_RULES: dict[str, str] = {
    "A1": RULE_AVERAGE,   # Cost and EVM Performance -- performance measure
    "A2": RULE_AVERAGE,   # Schedule Performance -- performance measure
    "A3": RULE_AVERAGE,   # Cost Risk -- performance measure
    "A4": RULE_AVERAGE,   # Document-Derived Signals -- performance measure
    "A6": RULE_WORST,     # Delivery Quality Performance -- conformance and compliance
}

#: A category the owner has not assigned keeps the rule the platform already applied.
DEFAULT_RULE = RULE_WORST

#: Band -> score. The owner's Run 104 scale, section 2.1. Adverse is negative, so a single Red
#: pulls the mean twice as hard as a Yellow lifts it.
BAND_SCORE: dict[str, float] = {"Green": 2.0, "Yellow": 1.0, "Amber": -1.0, "Red": -2.0}

#: The average's band boundaries, worst first, each read as "at or above this cut". The Red arm
#: is the open bottom and has no lower cut.
AVERAGE_CUTS: tuple[tuple[float, str], ...] = ((1.5, "Green"), (0.5, "Yellow"), (-0.5, "Amber"))

AVERAGE_BOUNDARY_WORDS = (
    "on the mean of the banded modules' scores -- Green +2, Yellow +1, Amber -1, Red -2, "
    "averaged over only the modules that asserted a band: at or above 1.5 is Green; at or above "
    "0.5 and below 1.5 is Yellow; at or above -0.5 and below 0.5 is Amber; below -0.5 is Red. "
    "Each boundary is INCLUSIVE ON ITS LOWER SIDE. A module that computed without a band, "
    "abstained or failed is not in the average and does not count as zero.")

WORST_BOUNDARY_WORDS = (
    "on the most adverse band any module in this category asserted. There is no averaging, no "
    "combination and no independence claim: a single Amber makes the category Amber and a "
    "single Red makes it Red, because these are conformance and compliance measures and an "
    "adverse reading in one of them is a finding in its own right.")

RULE_WORDS: dict[str, str] = {
    RULE_AVERAGE: ("this category averages its banded modules' scores, because its modules are "
                   "performance measures and one weak module among several should move the "
                   "posture without dominating it"),
    RULE_WORST: ("this category takes the worst band any of its modules asserted, because its "
                 "modules are conformance and compliance measures and an adverse reading in one "
                 "of them is a finding in its own right"),
}

RULE_SHORT: dict[str, str] = {
    RULE_AVERAGE: "the average of its banded modules' scores",
    RULE_WORST: "the worst band among its modules",
}


def rule_for(category_key: str | None) -> str:
    """Which rule forms this category's posture."""
    return CATEGORY_RULES.get(str(category_key or ""), DEFAULT_RULE)


def band_average(scores: Iterable[float]) -> str | None:
    """Band a mean of module scores. Returns None over an empty set: no modules, no posture."""
    vals = list(scores)
    if not vals:
        return None
    mean = sum(vals) / len(vals)
    for cut, band in AVERAGE_CUTS:
        if mean >= cut:
            return band
    return "Red"


def category_posture(category_key: str | None,
                     module_bands: Iterable[tuple[Any, Any]]) -> dict[str, Any]:
    """
    The posture of ONE category, and the arithmetic that produced it.

    `module_bands` is (module_id, band) for the modules ADMITTED to this category's rollup --
    admission is decided by the caller, which is where it has always been decided. A band the
    platform's vocabulary does not hold is not a band and is dropped here, exactly as
    `worst_band` drops it.

    The returned record is the category's WORKING, and it is returned rather than recomputed by
    every surface so that a reader who sees a Green over an Amber module can check the sum
    instead of guessing. Section 10.3 fails the run for a posture that cannot show it.
    """
    rule = rule_for(category_key)
    contributors: list[dict[str, Any]] = []
    for module_id, band in module_bands:
        b = str(band).capitalize() if band is not None else None
        if b not in BAND_SEVERITY:
            continue
        contributors.append({"module_id": module_id, "band": b,
                             "score": BAND_SCORE[b] if rule == RULE_AVERAGE else None})

    record: dict[str, Any] = {
        "status": None,
        "posture_rule": rule,
        "posture_rule_words": RULE_WORDS[rule],
        "posture_rule_short": RULE_SHORT[rule],
        "posture_boundary": AVERAGE_BOUNDARY_WORDS if rule == RULE_AVERAGE
        else WORST_BOUNDARY_WORDS,
        "posture_module_scores": contributors,
        "posture_banded_count": len(contributors),
        "posture_average": None,
        "posture_arithmetic": None,
        "status_set_by": [],
    }
    if not contributors:
        record["posture_arithmetic"] = (
            "No module in this category asserted a band, so the category carries no posture. "
            "That is an absence of a reading, not a favourable one.")
        return record

    if rule == RULE_AVERAGE:
        scores = [c["score"] for c in contributors]
        mean = sum(scores) / len(scores)
        status = band_average(scores)
        record["status"] = status
        record["posture_average"] = round(mean, 4)
        # EVERY BANDED MODULE SET THIS POSTURE. Under an average there is no single setter, and
        # naming the most adverse one would describe a rule this category does not apply.
        record["status_set_by"] = sorted(str(c["module_id"]) for c in contributors)
        record["posture_arithmetic"] = (
            "; ".join(f"{c['module_id']} {c['band']} {c['score']:+.0f}" for c in contributors)
            + f" -- {len(scores)} banded module"
            + ("" if len(scores) == 1 else "s")
            + f", total {sum(scores):+.0f}, mean {mean:+.4g}, which crosses into {status}.")
        return record

    status = worst_band([c["band"] for c in contributors])
    record["status"] = status
    record["status_set_by"] = sorted(str(c["module_id"]) for c in contributors
                                     if c["band"] == status)
    record["posture_arithmetic"] = (
        "; ".join(f"{c['module_id']} {c['band']}" for c in contributors)
        + f" -- the worst of {len(contributors)} banded module"
        + ("" if len(contributors) == 1 else "s")
        + f" is {status}, and it is the category's posture without averaging.")
    return record
