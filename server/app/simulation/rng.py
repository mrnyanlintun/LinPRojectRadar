"""
Deterministic PRNG and JavaScript-compatible numeric helpers.

Two participants uploading identical documents must receive identical module results, so no model
may draw from an unseeded generator. Python's `random` module is deliberately not used: it is
process-global, so an unrelated call elsewhere would shift the stream and silently change a
participant's figures.

The generator is mulberry32, bit-for-bit as the JavaScript runs it. Unsigned 32-bit arithmetic
reproduces JavaScript's Math.imul and >>> exactly: the bit patterns are identical whether the
intermediate is read as signed or unsigned.
"""

from __future__ import annotations

import hashlib
import math

_M = 0xFFFFFFFF


def seed_from(*parts: str) -> int:
    """
    Derive a 32-bit seed from the identifying parts of a period.

    Callers pass (scenario_id, period) and nothing else. participant_id is deliberately excluded:
    every participant must receive the identical P80 for the same scenario and period, and a seed
    varying by participant would reintroduce exactly the variance this design removes.
    """
    material = "|".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(material).digest()[:4], "big") & _M


def make_rng(seed: int):
    """Return a callable producing floats in [0,1), matching mulberry32 exactly."""
    state = {"s": seed & _M}

    def rand() -> float:
        state["s"] = (state["s"] + 0x6D2B79F5) & _M
        s = state["s"]
        t = ((s ^ (s >> 15)) * ((1 | s) & _M)) & _M
        t = (((t + (((t ^ (t >> 7)) * ((61 | t) & _M)) & _M)) & _M) ^ t) & _M
        return ((t ^ (t >> 14)) & _M) / 4294967296.0

    return rand


def js_round(value: float) -> float:
    """
    JavaScript Math.round: ties go toward positive infinity.

    Python's round() is banker's rounding, so round(2.5) is 2 there and 3 in JavaScript. Using the
    built-in would differ from the instrument's own history at exactly the values most likely to
    sit on a threshold.
    """
    if math.isnan(value) or math.isinf(value):
        return value
    return math.floor(value + 0.5)


def round1(v: float) -> float:
    return js_round(v * 10) / 10


def round2(v: float) -> float:
    return js_round(v * 100) / 100


def pctile(sorted_asc, q: float) -> float:
    """
    Index-based percentile, matching the JavaScript helper.

    Deliberately not interpolated and deliberately not numpy.percentile, which interpolates and
    returns a different P80 for the same sample. The discarded backend spike used a third rule
    again, int(n*q), which is why its RCF debiasing factor was 1.45 where the instrument shows 1.38.
    """
    if not sorted_asc:
        return float("nan")
    i = max(0, min(math.floor(q * (len(sorted_asc) - 1)), len(sorted_asc) - 1))
    return sorted_asc[i]


def num(value, default):
    try:
        n = float(value)
    except (TypeError, ValueError):
        return default
    return n if math.isfinite(n) else default


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def as_percent(value, default):
    if value is None:
        return default
    try:
        n = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(n):
        return default
    return n * 100 if n <= 1 else n
