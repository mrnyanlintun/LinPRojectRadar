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

from .lineage import (
    INDEPENDENT,
    NON_PROJECT_EVIDENCE,
    group_labels,
    lineage_record,
    evidence_bodies,
)

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


#: Severity order over the four bands, worst last. There is nothing to calibrate here: it is the
#: order the platform already displays them in, written down so the conservative comparison below
#: does not have to be reinvented by each reader.
BAND_SEVERITY: dict[str, int] = {"Green": 0, "Yellow": 1, "Amber": 2, "Red": 3}


def worst_band(bands) -> str | None:
    """The most adverse of a set of bands, or None when the set is empty."""
    present = [b for b in bands if b in BAND_SEVERITY]
    return max(present, key=lambda b: BAND_SEVERITY[b]) if present else None


def fuse_signals(signals) -> dict[str, Any] | None:
    """
    Fuse LINEAGE-BEARING signals into one belief distribution.

    This is the lineage-aware combination, and `dst_fuse` below is now a thin caller of it. Each
    signal is a mapping carrying at least `status`, optionally `module_id` and optionally
    `lineage`, a record built by `lineage.lineage_record`.

    THE THREE STEPS, AND THE REASON FOR EACH.

    STEP ONE, ADMISSION. A signal whose evidence relationship is QUALITY_METADATA,
    GOVERNANCE_OUTPUT or DECISION_OUTPUT is not project-condition evidence and is DROPPED, not
    grouped. Grouping would still let it vote inside whichever body it landed in. Specification
    18 states the Category 9 half of this directly: a data-quality result is a statement about
    the evidence and never another independent risk vote. The other two are computed from signals
    that have already been counted, so admitting them would count that evidence twice through a
    longer path. Every drop is reported in `excluded_non_evidential`, because an exclusion that
    nobody can see is indistinguishable from a signal that was never produced.

    STEP TWO, SEPARATION INTO INDEPENDENT BODIES. What remains is separated by
    `lineage.evidence_bodies`, which selects a maximum set of PAIRWISE-INDEPENDENT signals and
    absorbs every other signal into exactly one body it depends on. Two transforms of one body of
    earned-value evidence land in ONE body. A signal that bridges two disjoint bodies is absorbed
    into one of them: it neither becomes a third body nor merges the two it bridges. That last
    clause is the correction to the connected-component treatment this step used to apply, which
    made dependence transitive and let a bridge destroy real corroboration.

    STEP THREE, TWO DIFFERENT OPERATORS FOR TWO DIFFERENT QUESTIONS.

      WITHIN a body of evidence the question is not "do these agree" -- one body cannot agree
      with itself, and Dempster's rule applied here is what manufactured 0.9273 out of a single
      0.7000 source. The question is what this one body of evidence says when it is read in more
      than one way, and the answer taken is the most adverse of those readings. That operator is
      IDEMPOTENT, which is precisely the property the supervisory clarification requires: adding
      a copy, an algebraic transform or a derived metric of a signal already present changes
      nothing at all. It is also, deliberately, a governance choice and not a scientific constant
      -- an OWNER_POLICY provenance, carrying no weight, no correlation estimate and no tuned
      parameter, because there is no defensible empirical basis in this repository for any of
      those and inventing one would be worse than being conservative. Disagreement between two
      readings of one body is RECORDED (`disagreement`) rather than scored.

      ACROSS bodies of evidence the independence Dempster's rule assumes is now true by
      construction, so the existing rule applies unchanged, including the Red emphasis, which is
      applied once per BODY rather than once per signal so that duplicating a Red signal cannot
      apply it twice.

    THE CONFLICT COEFFICIENT. K is only computed across bodies. With one body there is nothing
    for it to measure and it is not manufactured: `conflict` stays 0.0 for the callers that have
    always read it, and `conflict_estimable` says whether that zero means anything.
    """
    admitted_bands: list[str] = []
    admitted_recs: list[dict] = []
    excluded: list[dict] = []
    undeclared = 0

    for i, sig in enumerate(signals or []):
        rec = sig.get("lineage")
        mid = sig.get("module_id") or (rec or {}).get("module_id") or f"__unnamed_{i}"
        rel = rec["evidence_relationship"] if rec else INDEPENDENT
        band = normalise_status(sig.get("status"))
        if rel in NON_PROJECT_EVIDENCE:
            excluded.append({"module_id": mid, "evidence_relationship": rel, "band": band})
            continue
        if band is None:
            # An abstention contributes no mass at all. It is not a neutral value, and it is
            # visible to the caller through the run's own abstention list.
            continue
        if rec is None:
            undeclared += 1
            rec = lineage_record(mid)
        admitted_bands.append(band)
        admitted_recs.append(rec)

    if not admitted_bands:
        return None

    separation = evidence_bodies(admitted_recs)
    groups = separation["bodies"]
    labels = group_labels(admitted_recs, groups)
    bodies = []
    for g, label in zip(groups, labels):
        bands_in = [admitted_bands[i] for i in g]
        rep = worst_band(bands_in)
        bodies.append({
            "lineage_group": label,
            "band": rep,
            # The selected pairwise-independent signal is first; the rest were absorbed into it.
            "representative_module_id": admitted_recs[g[0]]["module_id"],
            "member_module_ids": [admitted_recs[i]["module_id"] for i in g],
            "member_bands": bands_in,
            "primitive_source_ids": sorted(separation["primitive_sources"][g[0]]),
            "disagreement": len(set(bands_in)) > 1,
        })

    result = None
    last_k = 0.0
    for body in bodies:
        mass = STATUS_MASS[body["band"]]
        if result:
            c = dst_combine(result, mass)
            last_k = c.get("conflict", 0.0)
            result = c
        else:
            result = {s: mass[s] for s in STATES}
            result["conflict"] = 0.0
        if body["band"] == "Red":
            result = dst_combine(result, dst_discount(mass, 0.5))

    status = BANDS[0]
    for b in BANDS[1:]:
        if result[b] > result[status]:
            status = b
    return {
        "mass": {s: result[s] for s in STATES},
        "status": status,
        "conflict": last_k,
        "lineage_groups": len(bodies),
        "lineage_bodies": bodies,
        "conflict_estimable": len(bodies) >= 2,
        "excluded_non_evidential": excluded,
        "lineage_declared": undeclared == 0,
        "body_selection_exact": separation["selection_exact"],
        "signals_admitted": len(admitted_bands),
    }


def dst_fuse(statuses) -> dict[str, Any] | None:
    """
    Fuse bare status strings into one belief distribution.

    KEPT, AND KEPT WITH ITS ORIGINAL ARITHMETIC, for every caller that genuinely has independent
    sources and nothing else to say about them. Each status is given its own body of evidence,
    which is what this function has always assumed; the difference is that the assumption is now
    STATED in the returned object (`lineage_declared` is False) instead of being invisible. A
    consumer that must not fuse on an undeclared lineage -- the voting path is one -- can now
    detect that it was handed one, which it previously could not.

    A Red-dominant source is applied at 1.5x (full once, then a half-strength discounted
    re-combination) so a single Red cannot silently sink a set of greens while genuine Red
    evidence still dominates. The conflict K recorded is the last genuine combine, not the Red
    re-combine, which is a weighting artefact and would inflate it.
    """
    return fuse_signals([{"status": st} for st in (statuses or [])])


# ---------------------------------------------------------------------------- RUN 11, GATES 5, 6
#
# WHY THIS LIVES HERE. fusion.py is the one place the status vocabulary is recognised, and both
# of these are statements ABOUT a fusion: what the fused rollup may be called, and whether its
# conflict coefficient means anything. Putting them anywhere else would create a second place
# that has an opinion about what a fused status is.
#
# WHY IT IS A PURE FUNCTION OVER THE STORED CATEGORY STATUSES. Migrations 0020 through 0025 are
# unapplied in production, so nothing here may add a column. Both statements are DERIVED at read
# time from `category_statuses`, which every stored result already carries, so a row computed
# before this run gets the same answer as one computed after it without being rewritten.

#: The registry categories whose lineage is cost. A1 is Cost and EVM Performance, which is where
#: both voting modules live.
COST_LINEAGE_CATEGORIES = frozenset({"A1"})

NOT_ESTIMABLE_SINGLE_LINEAGE = "NOT_ESTIMABLE_SINGLE_LINEAGE"
CONFLICT_ESTIMATED = "ESTIMATED"
SINGLE_LINEAGE_SENTENCE = "Conflict: not estimable from one voting lineage"


def governed_status_semantics(category_statuses, raw_conflict=0.0) -> dict:
    """
    What the governed rollup may be called, and whether its conflict number means anything.

    BOTH ANSWERS ARE DERIVED FROM THE VOTING SET AS IT STANDS. If a second lineage ever votes,
    the label widens and the conflict coefficient becomes reportable, by themselves, with no
    wording to remember and no constant to change.

    CONFLICT. Dempster's K measures how far two INDEPENDENT bodies of evidence disagree. With one
    lineage the combine loop never performs a genuine combination and K comes back as 0.0 — which
    is also the value it takes when independent sources agree completely. A reader cannot tell
    those apart, and the second reading is the strongest claim the measure can make. So with one
    lineage the number is withheld and the state is named. No score is manufactured.

    LABEL. Two modules vote and both are cost lineage, so the rollup says whether the remaining
    budget can still carry the remaining work. It does not speak for schedule, evidence quality,
    procurement, safety or governance. Calling it overall project health would claim a breadth of
    evidence that has not voted. This is a DISPLAY string: no code constant is renamed by it, and
    it says nothing about Group A, which is a group of 53 modules and not this rollup.
    """
    cats = category_statuses or {}
    lineages = sorted(
        cat for cat, c in cats.items()
        if isinstance(c, dict) and c.get("status") and c.get("contributes_to_project_status")
    )
    if len(lineages) >= 2:
        conflict_state = CONFLICT_ESTIMATED
        conflict_value = raw_conflict
        conflict_sentence = None
        label = "Governed Project Status"
        scope = "Fused from the categories that vote: " + ", ".join(lineages) + "."
    else:
        conflict_state = NOT_ESTIMABLE_SINGLE_LINEAGE
        conflict_value = None
        conflict_sentence = SINGLE_LINEAGE_SENTENCE
        if len(lineages) == 1 and set(lineages) <= COST_LINEAGE_CATEGORIES:
            label = "Cost Recovery Status"
            scope = ("Fused from the cost lineage only: the to-complete cost efficiency and the "
                     "variance at completion. No schedule, evidence-quality, procurement or "
                     "governance measure votes on it.")
        elif len(lineages) == 1:
            label = "Governed Project Status"
            scope = "Fused from one voting lineage: " + lineages[0] + "."
        else:
            label = "Governed Project Status"
            scope = "No category voted, so no governed status was fused."
    return {
        "project_status_label": label,
        "project_status_scope": scope,
        "project_conflict": conflict_value,
        "project_conflict_state": conflict_state,
        "project_conflict_sentence": conflict_sentence,
        "voting_lineages": lineages,
    }
