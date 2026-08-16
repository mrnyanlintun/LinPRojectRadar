"""
The parameter provenance register.

WHY THIS FILE EXISTS. Every band boundary, cap, weight, membership and multiplier in this
platform is a number somebody chose. Run 4 established the discipline for the two voting modules
and cited their boundaries to published literature. Nothing had ever done the same for the rest,
so a boundary with a citation and a boundary invented in an afternoon were indistinguishable
from the outside, and a reader could not tell which was which.

WHAT THIS FILE ASSERTS, AND ONLY THIS. For every module that carries a tunable value, the class
of that value and the provenance of the class. It introduces no number that any computation
reads, changes no boundary, and calibrates nothing. A module classified UNSUPPORTED keeps the
number it has: reclassifying it is the honest act, and replacing it with a different invented
number would not be.

WHY NOTHING IS CALIBRATED HERE. Calibration needs an objective, a metric, an error-performance
target, a calibration set, a holdout and a sensitivity analysis. The calibration set does not
exist: there is no labelled corpus of project outcomes in this repository and no expert
reference standard, and synthetic laboratory data is not empirical field validation. Inventing
one to improve a count is the single thing this programme most firmly refuses.

THE ENUMERATION IS MECHANICAL, NOT TRANSCRIBED. The cycle 11 suite walks the syntax tree of
every module function, collects every numeric literal and every module-level named numeric
constant those functions read, subtracts the definitional values below, and requires what
remains to be covered by an entry here. A value added to a module tomorrow and not classified
fails that suite. This is what stops the register from being a snapshot that quietly goes stale.
"""

from __future__ import annotations

#: The classification vocabulary the cycle instruction fixes. DEFINITIONAL is added for the
#: values that are not choices at all: nought, one, one hundred as the base of a percentage, the
#: milliseconds in a day. Calling those heuristics would drown the real findings in noise.
PARAMETER_CLASSES: frozenset[str] = frozenset({
    "THEORETICAL_CONSTANT",
    "PUBLISHED_METHOD_PARAMETER",
    "REGULATORY_VALUE",
    "CONTRACT_VALUE",
    "OWNER_POLICY",
    "CALIBRATED_PARAMETER",
    "HEURISTIC",
    "UNSUPPORTED",
    "DEFINITIONAL",
})

#: The classes that may NOT be claimed without a citation naming a source outside this
#: repository. The suite enforces it: a claim of published provenance must carry the publication.
CLASSES_REQUIRING_CITATION: frozenset[str] = frozenset({
    "THEORETICAL_CONSTANT", "PUBLISHED_METHOD_PARAMETER", "REGULATORY_VALUE",
    "CONTRACT_VALUE", "CALIBRATED_PARAMETER",
})

#: Values that are not, in themselves, choices: bases, counts and unit conversions. THIS LIST IS
#: DOCUMENTATION AND IS NOT USED TO EXCLUDE ANYTHING FROM COVERAGE, and that is a correction made
#: inside this cycle rather than a design. The first version of this register did subtract these
#: values from the enumeration, and the subtraction was silently swallowing real boundaries: the
#: line of balance module bands at three days of crew separation, the change order module bands
#: at three orders and five per cent of growth, and every one of those numbers is in this list.
#: A guard that removes a value because the same number is elsewhere a unit conversion is the
#: vacuous-guard pattern this programme keeps finding. Coverage is therefore required for EVERY
#: module carrying any numeric value at all, and the list below only records why certain values
#: are not themselves the interesting part of an entry.
DEFINITIONAL_VALUES: dict[float, str] = {
    0: "the origin of every quantity here",
    1: "unity, the value of a ratio at parity and the total of a normalised distribution",
    2: "the divisor of a mean of two, and the count of the pair being averaged",
    3: "a minimum count of periods or checks, stated by the method it belongs to",
    4: "the count of the four bands, and of the four arms a module reads",
    5: "a minimum count of observations",
    7: "the days in a week",
    10: "the base of the percentage and per-mille conversions",
    12: "the months in a year",
    24: "the hours in a day",
    60: "the minutes in an hour and the seconds in a minute",
    100: "the base of a percentage",
    365: "the days in a year",
    1000: "the thousands separator in a money figure",
    86400000: "the milliseconds in a day",
    -1: "the additive inverse of unity",
    0.5: "one half, the divisor of a mean of two",
    0.0: "the origin, written as a float",
    1.0: "unity, written as a float",
}

#: The one sentence about calibration, carried once.
NO_CALIBRATION_SET: str = (
    "No calibration is performed for this value and none is claimed. Calibration requires an "
    "objective, a metric, an error-performance target, a calibration set, a frozen selection, a "
    "holdout evaluation and a sensitivity analysis. This repository holds no labelled corpus of "
    "project outcomes and no expert reference standard, so the calibration set does not exist, "
    "and synthetic laboratory data would not be empirical field validation of it."
)


class Provenance:
    """One module's tunable values, their class, and where the class comes from."""

    __slots__ = ("module_id", "kind", "parameter_class", "provenance")

    def __init__(self, module_id: str, kind: str, parameter_class: str,
                 provenance: str) -> None:
        if parameter_class not in PARAMETER_CLASSES:
            raise ValueError(f"unknown parameter class: {parameter_class}")
        if parameter_class in CLASSES_REQUIRING_CITATION and ", " not in provenance:
            raise ValueError(
                f"{module_id} claims {parameter_class} without naming a source; a claim of "
                f"published provenance must carry the publication")
        self.module_id = module_id
        self.kind = kind
        self.parameter_class = parameter_class
        self.provenance = provenance

    def as_dict(self) -> dict[str, str]:
        return {
            "parameter_kind": self.kind,
            "parameter_class": self.parameter_class,
            "parameter_provenance": self.provenance,
            "calibration": NO_CALIBRATION_SET,
        }


# The shared reasons. Each is written once and applied by name, so two modules with the same
# situation cannot end up with two different accounts of it.
_LADDER = ("a four band ladder over the quantity the module reports")
_UNSOURCED_LADDER = (
    "The boundaries are design choices. No source in this repository, in the supervisory "
    "specification, or in any publication cited by this platform specifies a boundary for this "
    "quantity, so they are recorded as chosen rather than derived. They are not moved by this "
    "run: replacing an invented number with a different invented number is not a repair."
)
_DESIGNED_MEMBERSHIP = (
    "The memberships, masses and hesitancies are designed constants. The theory this module "
    "belongs to specifies the algebra these numbers must satisfy and says nothing about what "
    "the numbers should be for a construction project; supplying them requires elicitation from "
    "experts or estimation from labelled outcomes, and neither exists here. The algebra is "
    "enforced and the numbers are recorded as designed."
)
_AD_HOC_WEIGHTS = (
    "The weights are an ad hoc split with no source. No publication, specification or owner "
    "policy in this repository fixes them, and no data exists from which they could be "
    "estimated."
)
_CAP = (
    "The cap is a chosen saturation point with no source. It decides at what count a term stops "
    "growing, which is a judgement about exposure that no publication cited here makes."
)


def _u(mid: str, kind: str = _LADDER) -> Provenance:
    return Provenance(mid, kind, "UNSUPPORTED", _UNSOURCED_LADDER)


def _m(mid: str) -> Provenance:
    return Provenance(mid, "designed memberships, masses or hesitancies with a band ladder",
                      "UNSUPPORTED", _DESIGNED_MEMBERSHIP)


PARAMETER_PROVENANCE: dict[str, Provenance] = {}


# ---------------------------------------------------------------------------------------------
# THE TWO VOTING MODULES, AND THEY ARE THE ONLY TWO WITH PUBLISHED PROVENANCE IN THE WHOLE
# REGISTRY. That is the finding of this cycle stated in one place: of the eighty-one modules
# carrying a tunable value, two carry a citation and seventy-nine do not.
# ---------------------------------------------------------------------------------------------
PARAMETER_PROVENANCE.update({
    "A1.7": Provenance(
        "A1.7", "two band boundaries on the to-complete cost efficiency index",
        "PUBLISHED_METHOD_PARAMETER",
        "One boundary is definitional and one is applied by stated inference. Project Management "
        "Institute, A Guide to the Project Management Body of Knowledge, 6th edition, 2017, "
        "section 7.4.2.2, and PMI Practice Standard for Earned Value Management, 2nd edition, "
        "2011, define this index as the cost efficiency the remaining work must achieve. "
        "Christensen and Heise, Cost Performance Index Stability, National Contract Management "
        "Journal 25(1), 1993, pages 7 to 15, supply the observed stability of one tenth. The "
        "stated limit is that a sourced boundary is not a measured false-positive rate."),
    "A1.8": Provenance(
        "A1.8", "two band boundaries on the variance at completion, as a percentage",
        "PUBLISHED_METHOD_PARAMETER",
        "Zero is definitional under Project Management Institute, A Guide to the Project "
        "Management Body of Knowledge, 6th edition, 2017, section 7.4.2.2. Minus 11.11 per cent "
        "is the exact restatement of a cost performance index of 0.90, which applies the one "
        "tenth stability finding of Christensen and Heise, National Contract Management Journal "
        "25(1), 1993, pages 7 to 15, by stated inference. The stated limit is that the stability "
        "finding is conditional on twenty per cent completion and this measure does not read "
        "percent complete, so the condition is not enforced."),
})

# ---------------------------------------------------------------------------------------------
# THE UPLIFT MULTIPLIER THAT CARRIED A PERCENTILE'S NAME. Recorded separately because the
# finding is specific and would be lost inside a shared reason.
# ---------------------------------------------------------------------------------------------
_UPLIFT_128 = (
    "The multiplier 1.28 is close to the standard normal deviate at the NINETIETH percentile, "
    "1.2816, and not at the eightieth, which is 0.8416. Under the name this module used to "
    "carry the number was therefore wrong as well as unsourced. Cycle 10 removed the percentile "
    "claim from the name, because nothing here is sampled and no distribution is formed, so the "
    "multiplier is no longer asserting a percentile of anything. As a multiplier it has no "
    "source at all, and neither does the half applied to the index shortfall beside it, or the "
    "floor under that shortfall. They are recorded as chosen."
)
for _mid in ("A2.10", "A3.6"):
    PARAMETER_PROVENANCE[_mid] = Provenance(
        _mid, "an uplift multiplier, a floor under the index shortfall, and a band ladder",
        "UNSUPPORTED", _UPLIFT_128)

# ---------------------------------------------------------------------------------------------
# AD HOC WEIGHTED SUMS. Named individually because a weight decides how much one piece of
# evidence outranks another, which is a stronger claim than a boundary makes.
# ---------------------------------------------------------------------------------------------
for _mid, _kind in (
    ("A4.7", "three weights on a capped request count, a capped change order count and the "
             "document risk score, plus two caps and a band ladder"),
    ("A5.5", "three weights on the same two capped counts and the cost index shortfall, plus "
             "two caps and a band ladder"),
    ("B1.2", "four weights on the assembled signal bands"),
    ("A4.8", "a weight on a precomputed score, with a band ladder"),
    ("C1.3", "reliability weights applied to sources"),
):
    PARAMETER_PROVENANCE[_mid] = Provenance(_mid, _kind, "UNSUPPORTED", _AD_HOC_WEIGHTS)

# ---------------------------------------------------------------------------------------------
# THE SOFT COMPUTING FAMILY. Every one of them: the algebra is the method and is enforced; the
# numbers the algebra operates on are designed.
# ---------------------------------------------------------------------------------------------
for _mid in ("B2.1", "B2.2", "B2.3", "B2.4", "B2.5", "B2.6", "B2.7", "B2.8", "B2.9", "B2.10",
             "B2.11", "B2.12", "B2.13", "B2.14", "B2.15", "B2.16", "B2.17", "B2.18", "B2.19",
             "B2.20"):
    PARAMETER_PROVENANCE[_mid] = _m(_mid)

# ---------------------------------------------------------------------------------------------
# THE STATISTICAL FAMILY: the designed variances, gains and control limits that make a method
# look estimated when it is set.
# ---------------------------------------------------------------------------------------------
PARAMETER_PROVENANCE.update({
    "A1.2": Provenance(
        "A1.2", "the reference shift, the decision interval and the floor under the standard "
                "deviation of a two-sided cumulative sum",
        "UNSUPPORTED",
        "The cumulative sum chart is a real method and the arithmetic here performs it. Its "
        "reference shift and decision interval are chosen to meet a target run length under an "
        "assumed shift size, and neither the target nor the shift size is stated anywhere in "
        "this repository, so these are set rather than designed to a criterion. The floor under "
        "the standard deviation is a numerical guard with no statistical basis at all."),
    "A1.3": Provenance(
        "A1.3", "the prior and observation variances of a normal-normal update",
        "UNSUPPORTED",
        "The updating rule is correct and the variances are constants written into the file. A "
        "Bayesian model's variances encode how much the prior and the observation are each to be "
        "believed; fixed ones assert a belief that was never elicited or estimated. The "
        "posterior is arithmetic about those constants."),
    "A1.4": Provenance(
        "A1.4", "the process and observation noise of a scalar Kalman recursion, and a band "
                "ladder",
        "UNSUPPORTED",
        "The recursion is correct. Its two noise terms determine the gain and therefore the "
        "entire filtering behaviour, and both are fixed constants rather than estimated from the "
        "series. No filtering performance is claimed and none is measurable from a history this "
        "short."),
    "A1.5": Provenance(
        "A1.5", "the clamp on the autoregressive coefficient, and a band ladder",
        "UNSUPPORTED",
        "The coefficient is estimated from the series, which is the one estimated quantity in "
        "the module, but the clamp that bounds it and the ladder that bands the projection are "
        "chosen. No order was identified and no interval is reported, which is why the name no "
        "longer claims one."),
})

# ---------------------------------------------------------------------------------------------
# THE REGULATORY AND CONTRACTUAL SURFACES. Cycle 2 already removed the false authority claims;
# this records what the remaining numbers are, which is not regulatory values.
# ---------------------------------------------------------------------------------------------
_NO_AUTHORITY = (
    "These are internal review levels and are NOT regulatory values. Cycle 2 removed the "
    "assertions that a named instrument sets them, because no provision cited anywhere in this "
    "repository does. Under the frozen regulatory snapshot no authority for any of them was "
    "found, and the egress restrictions on the official sources are recorded rather than worked "
    "around. They are recorded as chosen internal levels and no obligation is concluded from any "
    "of them."
)
for _mid in ("B3.2", "B3.3", "B3.4", "B4.3"):
    PARAMETER_PROVENANCE[_mid] = Provenance(
        _mid, "internal review levels and a band ladder", "UNSUPPORTED", _NO_AUTHORITY)
PARAMETER_PROVENANCE["A6.3"] = Provenance(
    "A6.3", "a three level ladder over a share of reported permit conditions met",
    "UNSUPPORTED",
    "No permit authority, jurisdiction or version is carried with the conditions being assessed, "
    "and no committed authority in this repository supplies a compliance level. The reading is a "
    "count of reported conditions met and is not a compliance determination under any named "
    "instrument. This value is blocked on regulatory version rather than merely unsourced, and "
    "the block is recorded rather than resolved by assertion.")

# ---------------------------------------------------------------------------------------------
# THE TWO ROWS CARRIED FORWARD FROM CYCLE 9 BECAUSE CLOSING THEM MEANT INVENTING A CONSTANT.
# Cycle 11 revisited both for genuine provenance and found none, so both are RECLASSIFIED
# honestly rather than closed. This is the exit target that is not met, stated here in the code
# as well as in the report.
# ---------------------------------------------------------------------------------------------
PARAMETER_PROVENANCE["B1.4"] = Provenance(
    "B1.4", "the FRACTION of the total signal count that sets the trigger of a worst N of M rule",
    "UNSUPPORTED",
    "The rule is defined by a FIXED N out of M. This implementation triggers on a fraction of "
    "the total instead, so every benign signal that arrives raises the count needed and can "
    "switch an existing adverse set off. Repairing it means choosing a fixed N, and cycle 11 "
    "searched the supervisory specification, this repository and every source it cites and found "
    "no N in any of them. The row is therefore reclassified PARAMETER_PROVENANCE_BLOCKED rather "
    "than closed with a fabricated constant, and the module stays advisory and non-voting.")
PARAMETER_PROVENANCE["D1.5"] = Provenance(
    "D1.5", "the weights over the anomaly components, which move with data availability",
    "UNSUPPORTED",
    "The weights are renormalised over whichever components happen to be present, so the same "
    "project scores differently according to DATA AVAILABILITY, which is to say according to how much evidence it supplied. Governing them means "
    "fixing them, and fixing them means choosing values that no calibration evidence in this "
    "repository can choose. The row is reclassified THRESHOLD_CALIBRATION_BLOCKED rather than "
    "closed, and the module stays advisory and non-voting.")

# ---------------------------------------------------------------------------------------------
# EVERYTHING ELSE: an unsourced band ladder, and in several cases a cap beside it. Applied by
# name rather than left implicit, so a module cannot be omitted by being forgotten.
# ---------------------------------------------------------------------------------------------
_LADDER_ONLY = (
    "A1.6", "A1.9", "A1.10", "A1.11", "A2.2", "A2.4", "A2.5", "A2.7", "A2.8", "A2.9", "A2.11",
    "A3.2", "A3.3", "A3.4", "A3.5", "A3.8", "A3.9", "A4.3", "A4.4", "A4.9", "A4.10", "A5.2",
    "A5.4", "A5.7", "A5.8", "A6.1", "A6.4", "B4.1", "B4.2", "B4.4", "B4.5", "B4.6",
    "A1.1", "A2.3", "A2.6", "A3.7", "A5.6", "A6.2", "B1.3",
    # RUN 28. A2.1 and A3.1 abstained unconditionally from Run 7 and Run 10B until Run 28 gave
    # them the structures they were waiting for, so neither carried a tunable value and neither
    # needed an entry. Both now do: the criticality index and the reference class forecast each
    # carry a simulation trial count and a governed percentile, and neither number is calibrated
    # against anything in this repository. They join the sweep rather than being excused from it.
    "A2.1", "A3.1",
    # RUN 29. A5.1 abstained unconditionally from Run 7 until Run 29 gave it the dependency
    # matrix it was waiting for, so it carried no tunable value and needed no entry. It does
    # now: the propagation rounds the rework it reports to a fixed number of places, and the
    # stopping rule's tolerance is read from the model rather than fixed here but the rounding
    # is not. Neither is calibrated against anything in this repository, so it joins the sweep
    # rather than being excused from it. No band ladder is attached to it: A5.1 asserts no
    # colour, so what is unsourced is the presentation constant and not a boundary.
    "A5.1",
    "C1.1", "C1.2", "C1.4", "C1.5", "C1.6", "C1.7",
    "D1.1", "D1.2", "D1.3", "D1.4",
)
for _mid in _LADDER_ONLY:
    PARAMETER_PROVENANCE.setdefault(_mid, _u(_mid))

_LADDER_AND_CAP = {
    "A4.2": "a per week request rate, an overdue share ladder and two count caps",
    "A4.5": "a lost days over available float ladder",
    "A4.6": "a joint ladder over a raw count and a contract growth percentage",
    "A5.3": "the scale applied to the document risk score before the deviations are ranked",
    "B3.5": "a joint ladder over a raw modification count and a growth percentage",
}
for _mid, _kind in _LADDER_AND_CAP.items():
    PARAMETER_PROVENANCE[_mid] = Provenance(_mid, _kind, "UNSUPPORTED",
                                            _UNSOURCED_LADDER + " " + _CAP)


# ---------------------------------------------------------------------------------------------
# THE ONE PLACE WHERE REAL PUBLISHED PROVENANCE WAS FOUND OUTSIDE THE VOTING PAIR, and it is
# recorded because cycle 11 went looking rather than assuming the answer. A module can carry
# values of more than one class, so the register holds a LIST per module: collapsing a module to
# a single class would have hidden exactly this case, where a published algorithm's own defaults
# sit underneath an invented band ladder.
# ---------------------------------------------------------------------------------------------
_EXTRA: dict[str, list[Provenance]] = {
    "D1.1": [
        Provenance(
            "D1.1", "the tree count, the subsample size and the average path length normaliser "
                    "of an isolation forest",
            "PUBLISHED_METHOD_PARAMETER",
            "One hundred trees and a subsample of 256 are the defaults of the algorithm as "
            "published: Liu, Ting and Zhou, Isolation Forest, Eighth IEEE International "
            "Conference on Data Mining, 2008, doi 10.1109/ICDM.2008.17, which reports that the "
            "path length converges well before that tree count and that the subsample bounds the "
            "swamping and masking effects. The height limit is the base two logarithm of the "
            "subsample, stated in the same paper."),
        Provenance(
            "D1.1", "the Euler-Mascheroni constant inside the harmonic approximation",
            "THEORETICAL_CONSTANT",
            "The limit of the harmonic series less the natural logarithm, a mathematical "
            "constant and not a choice. It appears in the average unsuccessful search path "
            "length of a binary search tree, which is the normaliser the same paper defines: "
            "Liu, Ting and Zhou, 2008, equation 1."),
    ],
}

#: module id -> every distinct provenance the module carries, in declaration order.
PARAMETER_PROVENANCE_BY_MODULE: dict[str, list[Provenance]] = {}
for _k, _v in PARAMETER_PROVENANCE.items():
    PARAMETER_PROVENANCE_BY_MODULE[_k] = [_v]
for _k, _vs in _EXTRA.items():
    PARAMETER_PROVENANCE_BY_MODULE.setdefault(_k, []).extend(_vs)


#: THE TWO ROWS THAT COULD ONLY HAVE BEEN CLOSED BY INVENTING A CONSTANT, named here rather than
#: left to be inferred from the prose above. Cycle 12 recomputes every disposition from
#: production, and a determination that lives only inside a paragraph cannot be recomputed: it
#: can only be transcribed, which is the thing this cycle exists to stop. Neither entry changes
#: any arithmetic, activates anything, or makes anything voting; both modules stay advisory and
#: non-voting. This is the Run-20 exit target IMPLEMENTATION_DEFECT equal to zero recorded, in
#: code, as NOT MET, together with the reason it is not met.
BLOCKED_DISPOSITIONS: dict[str, str] = {
    "B1.4": "PARAMETER_PROVENANCE_BLOCKED",
    "D1.5": "THRESHOLD_CALIBRATION_BLOCKED",
}


def blocked_disposition(module_id: str) -> str | None:
    """The blocked scientific disposition of a module, or None when it carries none."""
    return BLOCKED_DISPOSITIONS.get(module_id)


def provenance(module_id: str) -> list[Provenance]:
    return PARAMETER_PROVENANCE_BY_MODULE.get(module_id, [])


def classified_modules() -> list[str]:
    return sorted(PARAMETER_PROVENANCE_BY_MODULE)


def class_counts() -> dict[str, int]:
    out: dict[str, int] = {}
    for entries in PARAMETER_PROVENANCE_BY_MODULE.values():
        for p in entries:
            out[p.parameter_class] = out.get(p.parameter_class, 0) + 1
    return out
