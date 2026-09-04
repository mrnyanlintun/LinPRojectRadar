"""
The value shapes a real risk register carries, and the ones this parser refuses.

WHY REFUSAL IS THE POINT OF THIS FILE. The three forecasting modules downstream of the register
were producing an eightieth-percentile estimate at completion of 10,555,811 dollars on a project
whose authored estimate was 4,835,600, because they had no calibration data and generated from
literals instead. The cure is not a better guess. It is that a module with no real input
abstains, and that depends entirely on this file never manufacturing an input that the document
did not state.

So the rule here is the one `schedule_dates.py` already keeps, applied to a different kind of
value: a cell that cannot be read REFUSES, by name, with a reason. It never falls back.

WHAT IS A PROBABILITY AND WHAT ONLY LOOKS LIKE ONE. This is the load-bearing judgement in this
module, so it is stated plainly.

  READ AS A PROBABILITY:
    a percentage       "30%", "30 %", "30 per cent"      -> 0.30
    a decimal fraction "0.3", ".3"                        -> 0.30
    a whole percent    "30" where a percent sign or a %-headed column says so -> 0.30

  RECORDED AS A BAND, AND REFUSED AS A PROBABILITY:
    a word             "High", "Very Likely", "Remote"
    an ordinal         "4", "4 of 5", "3/5"
    a banded range     "Medium (30-50%)" is read as the band "Medium"; see below

  A WORD IS NOT A NUMBER, AND TURNING ONE INTO THE OTHER IS THE DEFECT THIS TASK EXISTS TO FIX.
  "High" has no numeric value the document states. Every scheme that maps it to 0.7, or to 0.8,
  or to the midpoint of a band, is importing a number from outside the document and presenting
  it as read. A register that scores its risks 1 to 5 is telling us an ORDER, not a likelihood:
  the interval between 4 and 5 is not stated to be the interval between 1 and 2, and treating
  the scale as linear in probability is an assumption the register does not make.

  The band is not thrown away. `RiskProbability.band` carries the word or ordinal verbatim, so
  the recommendation can say a risk is scored High by the register and name it, which is
  quoting. What the band cannot do is enter a cost distribution, and it does not.

  A BANDED RANGE IS DELIBERATELY NOT AVERAGED. "Medium (30-50%)" states a range, and its
  midpoint, 40%, appears nowhere in the document. Taking a midpoint is the same import as
  mapping a word. The band is recorded and the probability refuses.

MONEY. "$120,000", "120,000", "120000", "(45,000)" as a negative, and a bare "1.2M"/"1.2m" or
"450k" multiplier, are read. A currency this platform cannot identify refuses rather than being
treated as dollars, because a register denominated in another currency summing into a dollar
exposure is a wrong number that looks right.

DURATION. "10 days", "10d", "2 weeks", "1 month" are read into days, with the month taken as 30
days ONLY where the document wrote "month"; a bare number refuses, because a duration column
headed neither days nor weeks states no unit.

OPEN OR CLOSED. A small closed vocabulary, and anything outside it refuses. "Mitigated" is NOT
silently read as closed: a mitigated risk that is still being carried is open, and which one the
register means is a judgement the register has to state.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

# ------------------------------------------------------------------ refusal, shared shape


@dataclass(frozen=True)
class ValueRefusal:
    """A cell that held something this parser will not turn into the value asked for."""

    raw: str
    reason: str

    def as_dict(self) -> dict:
        return {"raw": self.raw, "reason": self.reason}


def _clean(value: Any) -> str:
    return " ".join(str(value if value is not None else "").split()).strip()


# Cells that are present and plainly say "nothing here". These are EMPTY, not refusals: a blank
# is the register declining to state a value, which is different from stating one this parser
# cannot read.
_BLANK = {"", "-", "--", "n/a", "na", "none", "nil", "tbd", "tba", "?", "."}


def is_blank(value: Any) -> bool:
    return _clean(value).lower() in _BLANK


# ------------------------------------------------------------------ probability

# Words a register uses for likelihood. Recorded as bands. Deliberately NOT mapped to numbers.
_BAND_WORDS = (
    "very high", "very likely", "almost certain", "certain", "frequent",
    "high", "likely", "probable", "major",
    "medium", "moderate", "possible", "occasional",
    "low", "unlikely", "improbable", "seldom", "minor",
    "very low", "very unlikely", "rare", "remote", "negligible",
)

_PERCENT = re.compile(r"^(\d+(?:\.\d+)?)\s*(?:%|per\s*cent|percent|pct)$", re.IGNORECASE)
# RUN 135, M5. A FRACTION HAS A DECIMAL POINT. THE BARE INTEGERS 1 AND 0 ARE NOT FRACTIONS.
#
# This pattern was `^(0?\.\d+|0|1(?:\.0+)?)$` and it matched a bare "1" and a bare "0", which
# reached `RiskProbability(value=1.0)` and `value=0.0` before the bare-number refusal below
# could see them. Every other bare integer -- 2, 3, 4, 5 -- refuses, and refuses for a reason
# that applies word for word to 1 and 0: the cell states no unit and an ordinal scale is the
# commonest register convention. ON A 1-TO-5 LIKELIHOOD REGISTER THE LOWEST-LIKELIHOOD ROWS
# THEREFORE READ AS CERTAIN, which is the reassuring direction and the one nothing downstream
# catches. The register reader supplies no scale hint -- `risk_register.py` passes
# `column_is_percent` and nothing else -- so there is no basis on which 1 could be told from a
# 1 of 5, and refusing is the only honest answer.
#
# A SECOND READING WAS WRONG IN THE SAME PLACE. This branch is tested BEFORE the percent-column
# branch, so on a column headed "Probability (%)" a stated "1" -- one per cent -- was read as
# 1.0, CERTAINTY, rather than 0.01. With the bare integers gone it now falls through to that
# branch and reads 0.01, as the heading says.
#
# A DECIMAL POINT IS THE UNIT STATEMENT. "0.4", ".4", "1.0" and "0.0" are written the way a
# fraction is written and are all still accepted; "1" and "0" are written the way an ordinal is
# written and now refuse with the same reason 2 through 5 refuse with.
_FRACTION = re.compile(r"^(0?\.\d+|1\.0+)$")
_ORDINAL_OF = re.compile(r"^(\d+)\s*(?:/|of|out of)\s*(\d+)$", re.IGNORECASE)


@dataclass(frozen=True)
class RiskProbability:
    """
    A likelihood the register stated.

    Exactly one of `value` and `band` is set. `value` is a real probability in 0..1 that the
    document stated numerically and that a cost distribution may use. `band` is a label the
    document stated, which may be quoted and may NOT be turned into a number.
    """

    value: float | None
    band: str | None
    raw: str

    @property
    def is_numeric(self) -> bool:
        return self.value is not None

    def as_dict(self) -> dict:
        return {"value": self.value, "band": self.band, "raw": self.raw}


def parse_probability(cell: Any, *, column_is_percent: bool = False
                      ) -> RiskProbability | ValueRefusal | None:
    """
    A likelihood, a band, a refusal, or None for a blank cell.

    `column_is_percent` is set by the caller when the COLUMN HEADING says percent (for example
    "Probability (%)"). Only then is a bare "30" read as 30 per cent, because only then has the
    document stated the unit. Without it a bare number in 2..100 refuses: it could be a percent,
    a 1-to-5 ordinal, or a score, and nothing in the cell distinguishes them.
    """
    raw = _clean(cell)
    if is_blank(raw):
        return None

    m = _PERCENT.match(raw)
    if m:
        pct = float(m.group(1))
        if not 0.0 <= pct <= 100.0:
            return ValueRefusal(raw, "a percentage outside 0 to 100 is not a probability")
        return RiskProbability(value=pct / 100.0, band=None, raw=raw)

    if _FRACTION.match(raw):
        return RiskProbability(value=float(raw), band=None, raw=raw)

    lowered = raw.lower()
    # Longest first, so "very high" is not matched as "high".
    for word in sorted(_BAND_WORDS, key=len, reverse=True):
        if lowered == word or lowered.startswith(word + " ") or lowered.startswith(word + "("):
            return RiskProbability(value=None, band=raw, raw=raw)

    m = _ORDINAL_OF.match(raw)
    if m:
        return RiskProbability(value=None, band=raw, raw=raw)

    if re.fullmatch(r"\d+(?:\.\d+)?", raw):
        number = float(raw)
        if column_is_percent:
            if not 0.0 <= number <= 100.0:
                return ValueRefusal(raw, "a percentage outside 0 to 100 is not a probability")
            return RiskProbability(value=number / 100.0, band=None, raw=raw)
        # A bare number with no unit anywhere. An ordinal scale is the commonest register
        # convention and a percent is the next, and this cell cannot tell them apart.
        return ValueRefusal(
            raw,
            "a bare number with no percent sign and no percent in the column heading states no "
            "unit: it may be a percentage or a position on an ordinal scale, and the two mean "
            "different things")

    return ValueRefusal(raw, "not a percentage, a fraction, or a likelihood band this "
                             "platform recognises")


# ------------------------------------------------------------------ money

_CURRENCY_OK = ("$", "usd", "us$")
# Symbols that are definitely money and definitely NOT the currency this platform sums in.
_CURRENCY_OTHER = ("£", "€", "¥", "gbp", "eur", "jpy", "cad", "aud", "chf", "inr")
_MULTIPLIER = {"k": 1_000.0, "m": 1_000_000.0, "bn": 1_000_000_000.0, "b": 1_000_000_000.0}
_MONEY = re.compile(
    r"^(?P<neg>\()?\s*(?P<cur>[$£€¥]|usd|us\$|gbp|eur)?\s*"
    r"(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)\s*"
    r"(?P<mult>k|m|bn|b)?\s*(?P<cur2>usd|dollars?)?\s*\)?$",
    re.IGNORECASE)


def parse_money(cell: Any) -> float | ValueRefusal | None:
    """
    A cost impact in dollars, a refusal, or None for a blank cell.

    A NEGATIVE IS PRESERVED. A register that carries an opportunity alongside its threats states
    a negative cost impact, and flipping its sign to make it a threat would be inventing one.
    """
    raw = _clean(cell)
    if is_blank(raw):
        return None

    lowered = raw.lower()
    for token in _CURRENCY_OTHER:
        if token in lowered and not any(ok in lowered for ok in ("usd", "us$")):
            return ValueRefusal(
                raw, f"stated in a currency this platform does not convert ({token}); a figure "
                     f"in another currency summed as dollars is a wrong number that looks right")

    m = _MONEY.match(raw)
    if not m:
        return ValueRefusal(raw, "not a money amount this platform reads")
    number = float(m.group("num").replace(",", ""))
    mult = (m.group("mult") or "").lower()
    if mult:
        number *= _MULTIPLIER[mult]
    if m.group("neg"):
        number = -number
    return number


# ------------------------------------------------------------------ duration

_DURATION = re.compile(
    r"^(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>d|day|days|w|wk|wks|week|weeks|mo|month|months)$",
    re.IGNORECASE)
_UNIT_DAYS = {"d": 1.0, "day": 1.0, "days": 1.0,
              "w": 7.0, "wk": 7.0, "wks": 7.0, "week": 7.0, "weeks": 7.0,
              "mo": 30.0, "month": 30.0, "months": 30.0}


def parse_duration_days(cell: Any, *, column_unit: str | None = None
                        ) -> float | ValueRefusal | None:
    """
    A time impact in days, a refusal, or None for a blank cell.

    `column_unit` is the unit the COLUMN HEADING stated ("days", "weeks"), which is how a bare
    number becomes readable. Without a unit in the cell or the heading, a bare number refuses.
    """
    raw = _clean(cell)
    if is_blank(raw):
        return None
    m = _DURATION.match(raw)
    if m:
        return float(m.group("num")) * _UNIT_DAYS[m.group("unit").lower()]
    if re.fullmatch(r"\d+(?:\.\d+)?", raw):
        if column_unit and column_unit.lower() in _UNIT_DAYS:
            return float(raw) * _UNIT_DAYS[column_unit.lower()]
        return ValueRefusal(raw, "a bare number with no unit in the cell or the column heading "
                                 "states no duration")
    return ValueRefusal(raw, "not a duration this platform reads")


# ------------------------------------------------------------------ open or closed

_OPEN_WORDS = {"open", "active", "live", "current", "ongoing", "monitoring", "in progress"}
_CLOSED_WORDS = {"closed", "retired", "expired", "realised", "realized", "resolved"}
# Words that state a MITIGATION state and not an OPEN/CLOSED state. A mitigated risk that is
# still carried is open; a mitigated risk that has been retired is closed. The register has to
# say which, and where it says only this, the status refuses rather than being assumed.
_AMBIGUOUS_STATUS = {"mitigated", "managed", "treated", "controlled", "accepted", "transferred"}


def parse_open_closed(cell: Any) -> bool | ValueRefusal | None:
    """True for open, False for closed, a refusal, or None for a blank cell."""
    raw = _clean(cell)
    if is_blank(raw):
        return None
    lowered = raw.lower()
    if lowered in _OPEN_WORDS:
        return True
    if lowered in _CLOSED_WORDS:
        return False
    if lowered in _AMBIGUOUS_STATUS:
        return ValueRefusal(
            raw, f"'{raw}' states how the risk is being treated, not whether it is still "
                 f"carried; a treated risk may be open or closed and the register has to say "
                 f"which")
    return ValueRefusal(raw, "not an open or closed status this platform recognises")


# ------------------------------------------------------------------ score

def parse_score(cell: Any) -> float | ValueRefusal | None:
    """
    A resulting risk score, a refusal, or None for a blank cell.

    Stored as the number the register printed, with NO normalisation: a 1-to-25 matrix score and
    a 1-to-5 score are different scales, the register does not always say which, and rescaling
    one to the other would be inventing the scale. Comparison across registers is therefore not
    offered, which is honest; comparison WITHIN one register is what a reader actually does.
    """
    raw = _clean(cell)
    if is_blank(raw):
        return None
    if re.fullmatch(r"\d+(?:\.\d+)?", raw):
        return float(raw)
    m = _ORDINAL_OF.match(raw)
    if m:
        return float(m.group(1))
    return ValueRefusal(raw, "not a numeric risk score")
