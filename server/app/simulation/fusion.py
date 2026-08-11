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


#: The four condition bands, and the ONE place the platform's status vocabulary is recognised.
BANDS = ("Green", "Yellow", "Amber", "Red")


def normalise_status(status) -> str | None:
    """
    Map any status string this platform emits onto one of the four bands. Returns None for a
    value outside the vocabulary, which is an ABSTENTION and never a band.

    THE FIFTEEN DEFECTS, defect 1, and the reason it is shared rather than local. The analytical
    layer emits capitalised bands ("Red"); the instrument's own signal assembler and the two
    governance projections emit lowercase ones ("red"); the conservative health state emits
    "Red-review". Four separate computations each carried their own comparison against ONE of
    those casings, so a status in the other casing missed every arm and fell through to whatever
    the final `else` happened to be. In three voting ensembles and in Conservative Dominance that
    final else was Green, so a Red signal, a light-amber signal and an unrecognised string alike
    became reassuring evidence. Matching is therefore case-insensitive here, and an unrecognised
    value returns None so that a caller must decide what to do with it rather than being handed a
    silent Green.

    The Yellow test runs before Amber deliberately: "light-amber" contains the substring "amber",
    so testing Amber first would misclassify it.
    """
    s = "" if status is None else str(status).strip().lower()
    if not s:
        return None
    if "red" in s:
        return "Red"
    if "yellow" in s or "light-amber" in s:
        return "Yellow"
    if "amber" in s or "orange" in s:
        return "Amber"
    if "green" in s:
        return "Green"
    # Complete is not a fused band; a completed source contributes best-case evidence.
    if "complete" in s or "blue" in s:
        return "Green"
    return None


def status_to_mass(status) -> dict[str, float] | None:
    """Map a status string to a belief mass. Returns None to abstain."""
    band = normalise_status(status)
    return STATUS_MASS[band] if band else None


#: "Unknown" is not a fifth condition a project can be in. It is Θ, the whole frame of
#: discernment: the mass a source declines to commit, which is compatible with EVERY state.
#: Dempster's rule intersects focal elements, and {Green,Yellow,Amber,Red} ∩ {Green} is {Green},
#: not the empty set. Treating Θ as a disjoint singleton made ignorance into conflict, which is
#: the second of the fifteen defects (audit P0 finding 4).
IGNORANCE = "Unknown"


def dst_combine(m1: dict[str, float], m2: dict[str, float]) -> dict[str, float]:
    """
    Dempster's rule over the four condition states plus Θ. Returns the normalised combination
    plus the conflict coefficient K.

    THE FIFTEEN DEFECTS, defect 2. Θ (`Unknown`) is the whole frame, so it intersects every
    state rather than conflicting with it: Θ ∩ {s} = {s}, and Θ ∩ Θ = Θ. Only two DISTINCT
    condition states are genuinely disjoint, and only those contribute to K.

    Worked proof, the audit's own: two sources each Green 0.8, Θ 0.2. The products are
    Green·Green 0.64 -> Green, Green·Θ 0.16 -> Green, Θ·Green 0.16 -> Green, Θ·Θ 0.04 -> Θ.
    K is 0, Green is 0.96 and Θ is 0.04. Before this fix K was 0.32 and Green 0.941176, because
    the two cross terms were counted as disagreement between a belief and an abstention.
    """
    combined = {s: 0.0 for s in STATES}
    k = 0.0
    for s1 in STATES:
        for s2 in STATES:
            mass = m1.get(s1, 0.0) * m2.get(s2, 0.0)
            if s1 == s2:
                combined[s1] += mass
            elif s1 == IGNORANCE:
                combined[s2] += mass
            elif s2 == IGNORANCE:
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
