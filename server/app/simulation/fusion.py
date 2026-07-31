"""
Dempster-Shafer fusion, ported from assets/js/simulations.js.

Deliberately NOT ported from backend/governance.py. That router classifies into `Critical` and
`Red-Review`, which no module emits, and its FAIRNESS_SENSITIVE list names two modules that exist
nowhere in the codebase, so two of its three fairness triggers can never fire. Porting it would
have introduced a status vocabulary the analytical layer cannot produce.

The vocabulary here is exactly what the modules emit: Green, Yellow, Amber, Red. A module that
abstains contributes no mass at all rather than a neutral value, because a fabricated neutral is
indistinguishable from a measured one once it reaches the combination.
"""

from __future__ import annotations

from typing import Any

STATES = ("Green", "Yellow", "Amber", "Red", "Unknown")

STATUS_MASS: dict[str, dict[str, float]] = {
    "Green":  {"Green": 0.80, "Yellow": 0.08, "Amber": 0.06, "Red": 0.04, "Unknown": 0.02},
    "Yellow": {"Green": 0.10, "Yellow": 0.70, "Amber": 0.13, "Red": 0.05, "Unknown": 0.02},
    "Amber":  {"Green": 0.05, "Yellow": 0.12, "Amber": 0.70, "Red": 0.11, "Unknown": 0.02},
    "Red":    {"Green": 0.03, "Yellow": 0.05, "Amber": 0.14, "Red": 0.76, "Unknown": 0.02},
}


def status_to_mass(status) -> dict[str, float] | None:
    """
    Map a status string to a belief mass. Returns None to abstain.

    The Yellow test runs before Amber deliberately: "light-amber" contains the substring "amber",
    so testing Amber first would misclassify it.
    """
    s = "" if status is None else str(status).lower()
    if not s:
        return None
    if "red" in s:
        return STATUS_MASS["Red"]
    if "yellow" in s or "light-amber" in s:
        return STATUS_MASS["Yellow"]
    if "amber" in s or "orange" in s:
        return STATUS_MASS["Amber"]
    if "green" in s:
        return STATUS_MASS["Green"]
    # Complete is not a fused band; a completed source contributes best-case evidence.
    if "complete" in s or "blue" in s:
        return STATUS_MASS["Green"]
    return None


def dst_combine(m1: dict[str, float], m2: dict[str, float]) -> dict[str, float]:
    """Dempster's rule. Returns the normalised combination plus the conflict coefficient K."""
    combined = {s: 0.0 for s in STATES}
    k = 0.0
    for s1 in STATES:
        for s2 in STATES:
            mass = m1.get(s1, 0.0) * m2.get(s2, 0.0)
            if s1 == s2:
                combined[s1] += mass
            else:
                k += mass
    norm = 1 - k
    if norm <= 0:
        out = {s: 0.2 for s in STATES}
        out["conflict"] = 1.0
        return out
    for s in STATES:
        combined[s] = combined[s] / norm
    combined["conflict"] = k
    return combined


def dst_discount(m: dict[str, float], alpha: float) -> dict[str, float]:
    """Shafer discounting: scale a source by alpha; the freed belief flows to Unknown."""
    out = {s: alpha * m.get(s, 0.0) for s in STATES}
    out["Unknown"] += 1 - alpha
    return out


def dst_fuse(statuses) -> dict[str, Any] | None:
    """
    Fuse status strings into one belief distribution.

    A Red-dominant source is applied at 1.5x (full once, then a half-strength discounted
    re-combination) so a single Red cannot silently sink a set of greens while genuine Red evidence
    still dominates. The conflict K recorded is the last genuine combine, not the Red re-combine,
    which is a weighting artefact and would inflate it.
    """
    sources = []
    for st in statuses or []:
        m = status_to_mass(st)
        if m:
            sources.append({"mass": m, "red": m is STATUS_MASS["Red"]})
    if not sources:
        return None

    result = None
    last_k = 0.0
    for src in sources:
        if result:
            c = dst_combine(result, src["mass"])
            last_k = c.get("conflict", 0.0)
            result = c
        else:
            result = {s: src["mass"][s] for s in STATES}
            result["conflict"] = 0.0
        if src["red"]:
            result = dst_combine(result, dst_discount(src["mass"], 0.5))

    bands = ("Green", "Yellow", "Amber", "Red")
    status = bands[0]
    for b in bands[1:]:
        if result[b] > result[status]:
            status = b
    return {"mass": {s: result[s] for s in STATES}, "status": status, "conflict": last_k}
