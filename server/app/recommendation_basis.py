"""
WHY THE RECOMMENDED COURSE IS THE ONE RECOMMENDED.

THE DEFECT THIS EXISTS TO CLOSE. The Governance Decision card laid out three scored courses,
said a lower score means a smaller worst case, recommended the course scoring 8 over the one
scoring 5, and then said it could not say why: "the stored result records the recommendation and
the scores. It does not record the rule that set the recommendation against the score." A
recommendation that contradicts its own scoring and cannot explain itself is worse than no
recommendation, because a project manager can neither act on it nor argue with it.

THE RULE IS NOT ABSENT. It is in `simulation/models_gov.py`'s regret module and it is short:

    1. score the three courses from a fixed payoff matrix over fixed future probabilities;
    2. take the lowest-scoring course;
    3. THEN OVERRIDE IT ON THE PERIOD'S OWN COST AND SCHEDULE PERFORMANCE:
         either figure below 0.88  -> escalate
         else either below 0.95    -> investigate

TWO THINGS THAT FOLLOW, AND BOTH BELONG ON THE CARD.

First, step 3 is what decides. The scores rank the courses; they do not choose between them.

Second, and this is the part the card was most wrong about: THE SCORES ARE THE SAME FOR EVERY
PROJECT AND EVERY PERIOD. The matrix and the probabilities are literals with no input
dependence, so `expected_regret` is `{monitor: 11, investigate: 5, escalate: 8}` on every result
this platform has ever stored or ever will. Presenting them as "the courses of action the
analysis scored for this period" told a reader that something about their period produced those
numbers. Nothing did. They are a property of the method, not a finding about the project.

WHY THE THRESHOLDS ARE RESTATED HERE RATHER THAN IMPORTED. They are inline literals inside the
module's function body, not module-level constants, so there is nothing to import.
`server/app/simulation/` is out of scope for modification, so they are mirrored here with the
one safeguard that makes a mirror honest: `test_six_fixes.py` section 3 drives the REAL module
across each threshold and asserts the branch this file predicts is the branch that actually
fires. If the module's rule changes, that check goes red rather than this file quietly lying.

NOTHING HERE COMPUTES A RECOMMENDATION. It explains one that is already stored.
"""
from __future__ import annotations

from typing import Any

# Mirrored from `simulation/models_gov.py` `run_regret_minimization`, and pinned against the
# real module by a check. See the note above on why these are copied rather than imported.
ESCALATE_BELOW = 0.88
INVESTIGATE_BELOW = 0.95

# The course each override branch selects, and the course the ranking alone would select.
_ESCALATE = "escalate"
_INVESTIGATE = "investigate"

# The names the card uses. No module id, no number: NAMING_AUTHORITY.
_COURSE_TITLE = {
    "monitor": "keep the project under routine monitoring",
    "investigate": "investigate before taking a formal step",
    "escalate": "escalate to management review",
}


def _fmt(v: float) -> str:
    """A stored figure as the card prints it, unaltered in value."""
    return f"{float(v):.2f}".rstrip("0").rstrip(".")


def recommendation_basis(signal_inputs: dict | None,
                         regret_module: dict | None) -> dict[str, Any] | None:
    """
    Why the stored recommendation is what it is, or None when there is nothing to explain.

    Returns `{rule, sentence, scores_are_fixed, recommended, lowest}` where `rule` is one of
    "performance_override" (a threshold on the period's own figures decided it) or "ranking"
    (nothing overrode the ranking, so the lowest-scoring course stands).

    Every figure quoted in `sentence` is read from the stored result. The thresholds are the
    module's own and are pinned by a check.
    """
    si = signal_inputs or {}
    mod = regret_module or {}
    scores = mod.get("expected_regret")
    recommended = mod.get("recommended_action")
    if not isinstance(scores, dict) or not recommended:
        return None

    numeric = {k: v for k, v in scores.items() if isinstance(v, (int, float))}
    if not numeric:
        return None
    lowest_score = min(numeric.values())
    lowest = [k for k, v in numeric.items() if v == lowest_score]

    cpi = si.get("cpi")
    spi = si.get("spi")
    have = isinstance(cpi, (int, float)) and isinstance(spi, (int, float))

    # Which branch of the module's rule fired, decided from the same figures it read.
    if have and (cpi < ESCALATE_BELOW or spi < ESCALATE_BELOW):
        breached = []
        if cpi < ESCALATE_BELOW:
            breached.append(f"cost performance at {_fmt(cpi)}")
        if spi < ESCALATE_BELOW:
            breached.append(f"schedule performance at {_fmt(spi)}")
        sentence = (
            "The recommendation is not taken from the scores. This period's "
            + " and ".join(breached)
            + (" are" if len(breached) > 1 else " is")
            + f" below {_fmt(ESCALATE_BELOW)}, and the analysis escalates whenever either "
              f"figure falls below {_fmt(ESCALATE_BELOW)}, whatever the ranking says."
        )
        rule = "performance_override"
    elif have and (cpi < INVESTIGATE_BELOW or spi < INVESTIGATE_BELOW):
        breached = []
        if cpi < INVESTIGATE_BELOW:
            breached.append(f"cost performance at {_fmt(cpi)}")
        if spi < INVESTIGATE_BELOW:
            breached.append(f"schedule performance at {_fmt(spi)}")
        sentence = (
            "The recommendation is not taken from the scores. This period's "
            + " and ".join(breached)
            + (" are" if len(breached) > 1 else " is")
            + f" below {_fmt(INVESTIGATE_BELOW)}, and the analysis calls for investigation "
              f"whenever either figure falls below {_fmt(INVESTIGATE_BELOW)} without reaching "
              f"the {_fmt(ESCALATE_BELOW)} escalation point."
        )
        rule = "performance_override"
    elif have:
        sentence = (
            f"Cost performance at {_fmt(cpi)} and schedule performance at {_fmt(spi)} are both "
            f"at or above {_fmt(INVESTIGATE_BELOW)}, so no performance rule applies and the "
            "lowest scoring course stands."
        )
        rule = "ranking"
    else:
        # Without the figures the rule reads, the branch cannot be established. Say that
        # rather than guess which one fired.
        return {
            "rule": "unknown",
            "sentence": ("The analysis records the recommendation and the scores. This period's "
                         "cost and schedule performance are not both on the stored result, so "
                         "which rule set the recommendation cannot be established here."),
            "scores_are_fixed": True,
            "recommended": recommended,
            "lowest": lowest,
        }

    return {
        "rule": rule,
        "sentence": sentence,
        # Stated so the card can stop calling a constant a finding about this period.
        "scores_are_fixed": True,
        "recommended": recommended,
        "lowest": lowest,
    }
