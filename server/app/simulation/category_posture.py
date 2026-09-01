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

THE PROJECT STATUS IS NOT FORMED HERE. Since RUN 106 it is the owner's WEIGHTED VOTE over the
five category postures, computed by `project_posture.project_posture` on BOTH paths -- the
Python rollup and the specification projection -- subject to the required-core gate, which
publishes "Awaiting analysis" with a sentence when it withholds. Worst-wins, which Run 105 had
installed at project level, is gone from there and survives here as the rule for A6. This module
forms a CATEGORY posture and nothing else.

THE SCALE AND THE CUTS BELOW ARE NOW SHARED. `BAND_SCORE` and `AVERAGE_CUTS` are imported by
`project_posture` rather than copied into it, so the category arithmetic and the project
arithmetic cannot drift apart.

RUN 105, GOAL THREE. AN AVERAGE OVER ONE MODULE IS THAT MODULE, AND THE CARD MUST SAY SO.

On the owner's corpus A4 Document-Derived Signals published Green from ONE banded module
(A4.2 RFI Velocity) out of eight in service. The arithmetic string was already honest -- it
said "1 banded module" -- but a reader who sees Green over a category name reasonably assumes
several modules agreed, and that posture feeds the project status.

WHAT WAS CONSIDERED, AND WHY A MINIMUM COUNT WAS REJECTED.

  A MINIMUM BANDED COUNT below which the category carries no posture was measured against the
  corpus before being rejected, not rejected by taste. Banded counts there are A1 2 of 7,
  A2 4 of 5, A3 3 of 4, A4 1 of 8, A6 4 of 4. A floor of 2 strips A4's posture; a floor of 3
  strips A4's and A1's. A4 and A1 are both in the REQUIRED CORE, so either floor forces the
  corpus project to Awaiting analysis -- the platform would answer "we cannot say" about a project
  whose modules did in fact read, which is a worse failure than a thin Green. It is also a
  NUMBER WITH NO RECORDED BASIS: nothing in the owner's calibration says two readings are
  enough and one is not, and rule 1 of this run's order forbids inventing one.

  DISCLOSURE was chosen. The posture is carried, and the record now states -- in a field of its
  own AND inside the arithmetic string every surface already renders -- that it rests on a
  single reading, naming the module and how many modules in the category produced none. The
  count is not a threshold: 1 is the point at which the word "average" stops describing what
  happened, which is arithmetic and not calibration.

  IT IS SCOPED TO AVERAGING. Worst-wins over one banded module is exactly what worst-wins
  means -- the worst of one reading is that reading, and nothing was averaged away -- so no
  thinness is claimed for A6 or for any category on the default rule.
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

#: RUN 105, GOAL THREE. The point at which an average stops averaging. Not a calibrated
#: threshold and not a floor on publication: at one banded module the mean IS that module's
#: score, so the record says so. See the module docstring for why no minimum count was imposed.
SINGLE_READING_COUNT = 1

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


def thinness_words(module_id: Any, considered: int | None) -> str:
    """
    What the card says about an average formed from ONE reading. Read off the reading itself --
    the module that banded and how many modules in the category were considered -- so no
    surface has to compose it and none can overstate it.
    """
    silent = None
    if isinstance(considered, int) and considered > SINGLE_READING_COUNT:
        silent = considered - SINGLE_READING_COUNT
    return ("THIS POSTURE RESTS ON ONE READING. Only " + str(module_id) + " asserted a band in "
            "this category"
            + (f", and {silent} other module" + ("" if silent == 1 else "s")
               + " considered here produced none" if silent else "")
            + ", so the average is that single module's score and nothing was averaged against "
              "it. It is not the agreement of several modules, and it should be read as one "
              "measurement rather than a settled category position.")


def category_posture(category_key: str | None,
                     module_bands: Iterable[tuple[Any, Any]],
                     modules_in_category: int | None = None) -> dict[str, Any]:
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
    pairs = list(module_bands)
    # HOW MANY MODULES WERE ON THE TABLE. Callers that hand this function only the banded
    # modules pass the total explicitly; callers that hand it every admitted module do not
    # need to, and the length of what they handed over is the count. Never inflated.
    considered = modules_in_category if isinstance(modules_in_category, int) else len(pairs)
    contributors: list[dict[str, Any]] = []
    for module_id, band in pairs:
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
        # RUN 105, GOAL THREE. Whether this posture is an average over a SINGLE reading, and
        # the sentence that says so. False/None on every other posture, including a worst-wins
        # category with one banded module -- the worst of one reading is that reading and
        # nothing was averaged away.
        "posture_single_reading": False,
        "posture_thinness_words": None,
        "posture_modules_considered": considered,
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
        if len(contributors) == SINGLE_READING_COUNT:
            record["posture_single_reading"] = True
            record["posture_thinness_words"] = thinness_words(
                contributors[0]["module_id"], considered)
            # APPENDED TO THE ARITHMETIC ITSELF, so every surface that already renders the
            # working shows the thinness without a renderer being changed to look for a new
            # field. The field exists as well, for a surface that wants to mark it.
            record["posture_arithmetic"] += " " + record["posture_thinness_words"]
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
