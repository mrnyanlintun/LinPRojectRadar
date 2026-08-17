"""
THE CATEGORY-7 OPERATIONAL RUNNERS, v16. ONE THIN ROUTE PER MODULE INTO THE CANONICAL LAYER.

WHY THIS FILE EXISTS, AND IT IS RUN 30'S OWN DEFECT. Run 30's first pass built
`canonical_v5.py`: nineteen governed structures, the canonical mathematics of every supplied
Category-6 and Category-7 contract, two hundred and thirty-nine passing oracle checks against the
contract's own numbers, and a thirty-nine fault non-vacuity campaign. AND PRODUCTION NEVER CALLED
ANY OF IT. Executing the production entry point for all twenty Category-7 identities and
recording, from the interpreter, which functions actually ran, gave `canonical_v5` reached on
ZERO of twenty. Seventeen ran their v14 proxy arithmetic; three were short-circuited as disabled.

A correct library behind an incorrect ledger is a failed remediation, and every direct-call proof
of that library was green for the whole time the defect existed. That is why this file's own
guard, `server/tools/test_run30_cat7_operational_route.py`, never calls `canonical_v5` to prove
anything: it executes `registry.run_module` and profiles the interpreter.

WHAT EACH RUNNER IS ALLOWED TO DO, AND IT IS DELIBERATELY ALMOST NOTHING.

    governed input -> canonical structure validation -> canonical implementation
                   -> canonical result or explicit abstention -> ledger row

A runner reads its module's governed structure off the signal inputs, hands it to the canonical
function, and renders the answer. It performs NO arithmetic of its own, so there is nowhere for a
proxy to live. In particular NOTHING HERE READS `cpi`, `spi` OR `docRiskScore`: a crisp index is
not a mass function, not a membership, not a linguistic probability and not a possibility degree,
and the seventeen legacy implementations that manufactured one from another are now unreferenced
by the registry.

THE FOUR BLOCKED OPERATORS SURVIVE THE REPOINTING, which is the moment they were most at risk. A
route that must return something is exactly where a blocked operator gets quietly approximated.

  * B2.13 Type-2      -- type reduction is blocked. THERE IS NO MIDPOINT FALLBACK. The footprint
                         of uncertainty is reported and no single figure is produced.
  * B2.5  Z-numbers   -- no reduction operator is invented; representation only.
  * B2.8  Belief Rule Base -- a single fully activated rule returns its own consequent exactly;
                         two or more activated rules return AGGREGATION_BLOCKED. No ER variant is
                         chosen here.
  * B2.7  Plithogenic -- no operator is chosen, and the runner refuses regardless.

None of the four formulations is frozen in the supervisory artifacts. The specification cites
Karnik-Mendel by DOI at line 341 and asks only that a centroid reduction, "if" used, be verified
at line 2152; it cites RIMER by DOI at line 338 and asks for testing "for the selected ER
formulation" without selecting one. A citation is not a formulation.

THE THREE DISABLED AND ARCHIVED IDENTITIES REFUSE HERE TOO, not only at the registry gate. The
registry short-circuits B2.7, B2.9 and B2.20 before any runner is reached, and that is the
operational guarantee; the runners below refuse as well, so the guarantee does not rest on a
single gate and can be proved at the runner itself. A COMPLETE laboratory structure does not
change the answer: completeness is not activation.

NO BAND IS INVENTED ANYWHERE IN THIS FILE. Run 33 owns calibration. Every canonical quantity is
emitted with `calibration_pending` and no `status_color`, which `registry.record` already routes
to the computed rows rather than treating as an abstention.
"""

from __future__ import annotations

from typing import Any, Callable

from . import canonical_v5 as V5
from .canonical import StructureAbsent
from .canonical_v5 import V5_STRUCTURE_KEYS, V5_STRUCTURE_WORDS, v5_structure
from .lineage import (
    evidence_body_of, independence_established, lineage_status,
)
from .models import ABSTAIN_DECISION_STRUCTURE_ABSENT, ABSTAIN_STRUCTURE_ABSENT
from .signal_package import SIGNAL_QUALIFICATION

#: Stamped on every Category-7 ledger row this file produces, computed or abstaining. The ledger
#: is the operational truth surface, so a reader can tell from the row itself which line produced
#: it rather than having to trust a report. A row without this marker did not come from here.
RESULT_SOURCE = "CANONICAL_V5_LAYER"

#: The dispositions a Category-7 route may end in. There is no other exit.
DISPOSITION_COMPUTED = "CANONICAL_RESULT"
DISPOSITION_STRUCTURE_ABSENT = "NOT_ESTIMABLE_STRUCTURE_ABSENT"
DISPOSITION_OPERATOR_BLOCKED = "OPERATOR_BLOCKED"
DISPOSITION_DISABLED = "DISABLED"
DISPOSITION_ARCHIVED = "ARCHIVED"


def _lineage_block(module_id: str, structure: Any, *, applicable: bool) -> dict[str, Any]:
    """
    THE ROW'S LINEAGE STATE, SAID RATHER THAN LEFT BLANK.

    Run 30's closure removed eleven Category-7 lineage declarations whose content had become
    false, and deliberately did NOT replace them with invented independent bodies. That left the
    right facts and the wrong representation: a row with no lineage record was indistinguishable
    from a row whose independence had been established, because both carried nothing.

    Every row now carries the state explicitly, DERIVED from the shipped declaration table by
    `lineage.lineage_status`. There is no branch anywhere in this file that can put
    LINEAGE_ESTABLISHED_INDEPENDENT on a row whose declaration does not say so.

    SOURCE PROVENANCE AND EVIDENCE INDEPENDENCE ARE KEPT APART, which is the distinction the
    closure instruction turns on. A row may know exactly where its structure came from -- who
    assessed it, which document, which period -- and still have UNRESOLVED independence, because
    knowing the source of a structure is not knowing what the assessor themselves read. Both are
    reported, side by side, and neither is inferred from the other.
    """
    status = lineage_status(module_id, applicable=applicable)
    return {
        "lineage_status": status,
        "independence_established": independence_established(status),
        "evidence_body": evidence_body_of(module_id, status),
        "source_provenance": _provenance_of(structure),
        "derived_from": V5_STRUCTURE_WORDS.get(module_id),
        "qualification": SIGNAL_QUALIFICATION,
        "transformation_note":
            "this measure is a representation of evidence supplied for this project and is "
            "not a further independent reading of the project's condition",
        "unresolved_note":
            "no body of evidence has been established for this reading: what its assessors "
            "themselves read is not known to this platform. That is not independence, and "
            "nothing may corroborate through it"
        if status == "LINEAGE_UNRESOLVED" else None,
    }


def _provenance_of(structure: Any) -> dict[str, Any]:
    """The lineage fields the structure carried, echoed back onto the row.

    Run 31 builds the Category-9 qualification gate over these same rows and cannot qualify what
    has no lineage, so provenance travels out with the answer rather than being consumed.
    """
    if not isinstance(structure, dict):
        return {}
    keep = ("source", "assessed_by", "elicited_from", "defined_by", "research_origin",
            "context_id", "period", "data_origin", "not_for_empirical_validation")
    return {k: structure[k] for k in keep if k in structure}


#: The two modules whose defining structure is a decision problem rather than an evidence or
#: parameter object, so their abstention raises the decision-structure reason code the platform
#: already carries rather than the generic one.
_DECISION_STRUCTURE_MODULES = frozenset({"B2.18", "B2.19"})


def _abstain(method_class: str, module_id: str, sentence: str, disposition: str,
             structure: Any = None) -> dict[str, Any]:
    return {
        "abstention_reason_code":
            ABSTAIN_DECISION_STRUCTURE_ABSENT if module_id in _DECISION_STRUCTURE_MODULES
            else ABSTAIN_STRUCTURE_ABSENT,
        "method_class": method_class,
        "status_color": None,
        "insufficient_data": True,
        "result_source": RESULT_SOURCE,
        "canonical_disposition": disposition,
        "canonical_structure": V5_STRUCTURE_KEYS.get(module_id),
        "structure_provenance": _provenance_of(structure),
        "abstention_reason": sentence,
        "signal_qualification": SIGNAL_QUALIFICATION,
        "lineage": _lineage_block(module_id, structure, applicable=True),
        "evidence_metric": sentence,
    }


def _computed(method_class: str, module_id: str, structure: Any, sentence: str,
              payload: dict[str, Any]) -> dict[str, Any]:
    row = {
        "method_class": method_class,
        # NO BAND. Run 33 owns calibration and this file invents none.
        "status_color": None,
        "calibration_pending":
            "no boundary has been established for this platform that would turn this reading "
            "into a state, so none is asserted",
        "result_source": RESULT_SOURCE,
        "canonical_disposition": DISPOSITION_COMPUTED,
        "canonical_structure": V5_STRUCTURE_KEYS.get(module_id),
        "structure_provenance": _provenance_of(structure),
        "signal_qualification": SIGNAL_QUALIFICATION,
        "lineage": _lineage_block(module_id, structure, applicable=True),
        "evidence_metric": sentence,
    }
    row.update(payload)
    return row


def _route(module_id: str, method_class: str, canonical_name: str,
           render_name: str) -> Callable:
    """
    Build one runner. The SAME four steps for every module, so no module can acquire a private
    fallback: read the governed structure, call the canonical function, and render whatever it
    returned. A refusal from either step becomes an abstention carrying its own sentence.

    THE CANONICAL FUNCTION AND THE RENDERER ARE BOTH RESOLVED BY NAME AT CALL TIME, not captured
    at import. Two reasons,
    and the second is the one that matters. It keeps the routing table honest: `canonical_name`
    is looked up on the canonical module every call, so a function renamed or removed there
    breaks every route that named it instead of leaving a route silently bound to a stale object.
    And it makes the route FAULT-INJECTABLE: a mutant compiled over the canonical function and
    set on the canonical module really is what the production route then executes, so a guard can
    prove the production answer is decided by the canonical mathematics rather than by anything
    the runner does on the way. A late-bound delegate is the difference between a mutation proof
    and a mutation that quietly fails to apply.
    """

    def run(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
        structure = None
        canonical = getattr(V5, canonical_name)
        render = globals()[render_name]
        try:
            structure = v5_structure(si or {}, module_id)
            out = canonical(structure)
        except StructureAbsent as exc:
            return _abstain(method_class, module_id, exc.sentence,
                            DISPOSITION_STRUCTURE_ABSENT, structure)
        if not out.get("estimable", True):
            # The canonical layer decided it cannot answer. Its own words are carried through;
            # nothing is substituted and no earlier arithmetic is consulted.
            reason = out.get("reason") or (
                "this measure cannot be carried out on the information provided for this "
                "project, so no reading is reported")
            blocked = out.get("state") in ("AGGREGATION_BLOCKED", "TOTAL_CONFLICT",
                                           "DEPENDENCE_UNRESOLVED", "INFEASIBLE", "NOT_SOLVED")
            row = _abstain(method_class, module_id, reason,
                           DISPOSITION_OPERATOR_BLOCKED if blocked
                           else DISPOSITION_STRUCTURE_ABSENT, structure)
            if out.get("state"):
                row["canonical_state"] = out["state"]
            return row
        sentence, payload = render(out)
        return _computed(method_class, module_id, structure, sentence, payload)

    run.__name__ = f"run_{method_class.lower()}"
    run.__qualname__ = run.__name__
    return run


def _refuse(module_id: str, method_class: str, disposition: str,
            sentence: str) -> Callable:
    """
    A disabled or archived identity's operational runner.

    IT REFUSES BEFORE ANY STRUCTURE IS READ, so a complete laboratory structure cannot make it
    compute. Completeness is not activation, and the refusal does not depend on what was
    supplied.
    """

    def run(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
        return {
            "method_class": method_class,
            "status_color": None,
            "insufficient_data": True,
            "activation_state": "DISABLED_UNSAFE",
            "result_source": RESULT_SOURCE,
            "canonical_disposition": disposition,
            "canonical_structure": V5_STRUCTURE_KEYS.get(module_id),
            "operational": False,
            "abstention_reason": sentence,
            # A disabled or archived identity produces no analytical reading, so there is no
            # signal for a lineage statement to be about. NOT_APPLICABLE says that, and is
            # distinct from UNRESOLVED, which describes a reading that exists.
            "lineage": _lineage_block(module_id, None, applicable=False),
            "evidence_metric": sentence,
        }

    run.__name__ = f"run_{method_class.lower()}"
    run.__qualname__ = run.__name__
    # THE DISPOSITION IS READABLE WITHOUT RUNNING THE MODULE, and there is still exactly ONE
    # place it is stated -- the `_refuse` call that built this runner. The served defensibility
    # object has to say whether an identity is DISABLED or ARCHIVED, and those are different
    # claims: disabled means not operational, archived means kept as part of the research record
    # and not a runnable current capability. Deriving it by executing the runner would need a
    # database; copying it into a second table would let the two drift, which is exactly the
    # defect this closure exists to remove. Introspection reads the one source instead.
    run.canonical_disposition = disposition
    return run


# =================================================================================================
# THE RENDERERS. Each turns a canonical result into the sentence a reader sees and the fields the
# export carries. They contain no arithmetic that decides anything: every number below was
# computed by the canonical layer.
# =================================================================================================

def _r_dst(out: dict) -> tuple[str, dict]:
    bel = out.get("belief", {})
    parts = ", ".join(f"{k} {v:.2f}" for k, v in sorted(bel.items()))
    conflict = out.get("conflict")
    tail = (f"; disagreement between the bodies {conflict:.2f}"
            if out.get("conflict_estimable") and conflict is not None
            else "; disagreement cannot be measured from a single body of evidence")
    return (f"Belief from the evidence supplied: {parts}{tail}",
            {"bodies": out.get("bodies"), "belief": bel,
             "plausibility": out.get("plausibility"),
             "conflict": conflict, "conflict_estimable": out.get("conflict_estimable")})


def _r_rough(out: dict) -> tuple[str, dict]:
    return (f"Of the cases recorded, {len(out['lower'])} certainly belong to the decision being "
            f"approximated and {len(out['boundary'])} cannot be told either way",
            {"universe_size": len(out["universe"]), "lower": out["lower"],
             "upper": out["upper"], "boundary": out["boundary"],
             "accuracy": out.get("accuracy")})


def _r_neutrosophic(out: dict) -> tuple[str, dict]:
    return (f"Supported {out['truth']:.2f}, undetermined {out['indeterminacy']:.2f}, "
            f"contradicted {out['falsity']:.2f}",
            {"truth": out["truth"], "indeterminacy": out["indeterminacy"],
             "falsity": out["falsity"]})


def _r_interval(out: dict) -> tuple[str, dict]:
    lo, up = out["membership"]
    return (f"Membership assessed between {lo:.2f} and {up:.2f}",
            {"membership_lower": lo, "membership_upper": up})


def _r_z(out: dict) -> tuple[str, dict]:
    return (f"Assessed as {out['restriction']['term']}, with reliability stated as "
            f"{out['reliability']['term']}. No single combined figure is produced, because the "
            f"way to combine an assertion with its reliability has not been set for this "
            f"platform",
            {"restriction": out["restriction"], "reliability": out["reliability"],
             "reduction": None, "reduction_blocked": out["reduction_blocked"]})


def _r_plts(out: dict) -> tuple[str, dict]:
    parts = ", ".join(f"{t['term']} {t['probability']:.2f}" for t in out["terms"])
    return (f"Assessed as {parts}", {"terms": out["terms"]})


def _r_brb(out: dict) -> tuple[str, dict]:
    bel = out["belief"]
    parts = ", ".join(f"{k} {v:.2f}" for k, v in sorted(bel.items()))
    return (f"One rule speaks to this project, concluding {parts}",
            {"belief": bel, "incompleteness": out.get("incompleteness"),
             "activated_rules": out.get("activated"),
             "aggregation": out.get("aggregation")})


def _r_pythagorean(out: dict) -> tuple[str, dict]:
    return (f"Membership {out['membership']:.2f}, non membership "
            f"{out['non_membership']:.2f}, hesitancy {out['hesitancy']:.2f}",
            {"membership": out["membership"], "non_membership": out["non_membership"],
             "hesitancy": out["hesitancy"]})


def _r_picture(out: dict) -> tuple[str, dict]:
    return (f"Positive {out['positive']:.2f}, neutral {out['neutral']:.2f}, negative "
            f"{out['negative']:.2f}, with {out['refusal']:.2f} not assessed either way",
            {"positive": out["positive"], "neutral": out["neutral"],
             "negative": out["negative"], "refusal": out["refusal"]})


def _r_hesitant(out: dict) -> tuple[str, dict]:
    return (f"{out['count']} assessors gave degrees averaging {out['score']:.4f}",
            {"degrees": out["degrees"], "score": out["score"],
             "score_operator": out["score_operator"]})


def _r_type2(out: dict) -> tuple[str, dict]:
    return (f"Membership assessed as a range at {len(out['points'])} point(s), the widest "
            f"spread being {out['max_fou_width']:.2f}. No single figure is produced, because "
            f"the way to reduce a membership that is itself a range has not been set for this "
            f"platform",
            {"points": out["points"], "max_fou_width": out["max_fou_width"],
             "type_reduced": None,
             "type_reduction_blocked": out["type_reduction_blocked"]})


def _r_maxent(out: dict) -> tuple[str, dict]:
    return (f"The least committal distribution consistent with the evidence supplied has "
            f"entropy {out['entropy']:.4f} over {len(out['states'])} states",
            {"distribution": out["distribution"], "entropy": out["entropy"],
             "multipliers": out["multipliers"],
             "constraint_expectations": out["constraint_expectations"],
             "solver": out["solver"], "optimization_status": out["state"]})


def _r_possibility(out: dict) -> tuple[str, dict]:
    parts = ", ".join(f"{k} {v:.2f}" for k, v in sorted(out["distribution"].items()))
    return (f"Possibility assessed as {parts}", {"distribution": out["distribution"],
                                                 "universe": out["universe"]})


def _r_spherical(out: dict) -> tuple[str, dict]:
    return (f"Membership {out['membership']:.2f}, non membership "
            f"{out['non_membership']:.2f}, hesitancy {out['hesitancy']:.2f}",
            {"membership": out["membership"], "non_membership": out["non_membership"],
             "hesitancy": out["hesitancy"]})


def _r_fermatean(out: dict) -> tuple[str, dict]:
    return (f"Membership {out['membership']:.2f}, non membership {out['non_membership']:.2f}",
            {"membership": out["membership"], "non_membership": out["non_membership"]})


def _r_marcos(out: dict) -> tuple[str, dict]:
    order = " then ".join(out["ranking"])
    return (f"Of the options compared, the order is {order}",
            {"ranking": out["ranking"], "ranks": out["ranks"],
             "utility": {r["alternative_id"]: r["utility"] for r in out["rows"]},
             "ideal": out["ideal"], "anti_ideal": out["anti_ideal"],
             "decision_lineage": out["lineage"]})


def _r_critic(out: dict) -> tuple[str, dict]:
    order = " then ".join(out["ranking"])
    return (f"Of the options compared, the order is {order}",
            {"ranking": out["ranking"], "ranks": out["ranks"],
             "criterion_weights": out["weights"],
             "closeness": {r["alternative_id"]: r["closeness"] for r in out["rows"]},
             "weights_are_algorithmic": out["weights_are_algorithmic"],
             "decision_lineage": out["lineage"]})


# =================================================================================================
# THE ROUTING TABLE. Twenty identities, twenty routes, nothing else.
# =================================================================================================

CAT7_CANONICAL: dict[str, tuple[str, Callable]] = {
    "B2.1": ("DST_Evidence_Combination",
             _route("B2.1", "DST_Evidence_Combination", "dempster_shafer", "_r_dst")),
    "B2.2": ("Rough_Sets_Classification",
             _route("B2.2", "Rough_Sets_Classification", "rough_approximations", "_r_rough")),
    "B2.3": ("Neutrosophic_Logic",
             _route("B2.3", "Neutrosophic_Logic", "neutrosophic", "_r_neutrosophic")),
    "B2.4": ("Interval_Fuzzy_Sets",
             _route("B2.4", "Interval_Fuzzy_Sets", "interval_fuzzy", "_r_interval")),
    "B2.5": ("Z_Numbers", _route("B2.5", "Z_Numbers", "z_number", "_r_z")),
    "B2.6": ("PLTS", _route("B2.6", "PLTS", "plts", "_r_plts")),
    "B2.7": ("Plithogenic_Sets",
             _refuse("B2.7", "Plithogenic_Sets", DISPOSITION_DISABLED,
                     "Plithogenic Sets is disabled for operational use: it is held as research "
                     "only and produces no reading for any project. A complete set of assessed "
                     "degrees does not change that, because the way they would be combined has "
                     "not been settled.")),
    "B2.8": ("Belief_Rule_Base",
             _route("B2.8", "Belief_Rule_Base", "belief_rule_base", "_r_brb")),
    "B2.9": ("Quantum_Probability",
             _refuse("B2.9", "Quantum_Probability", DISPOSITION_ARCHIVED,
                     "Quantum Probability is archived and disabled for operational use: it is "
                     "kept as part of the research record and produces no reading for any "
                     "project. Restoring it would require evidence this platform does not "
                     "hold.")),
    "B2.10": ("Pythagorean_Fuzzy",
              _route("B2.10", "Pythagorean_Fuzzy", "pythagorean_fuzzy", "_r_pythagorean")),
    "B2.11": ("Picture_Fuzzy",
              _route("B2.11", "Picture_Fuzzy", "picture_fuzzy", "_r_picture")),
    "B2.12": ("Hesitant_Fuzzy",
              _route("B2.12", "Hesitant_Fuzzy", "hesitant_fuzzy", "_r_hesitant")),
    "B2.13": ("Type2_Fuzzy", _route("B2.13", "Type2_Fuzzy", "type2_fuzzy", "_r_type2")),
    "B2.14": ("Maximum_Entropy",
              _route("B2.14", "Maximum_Entropy", "maximum_entropy", "_r_maxent")),
    "B2.15": ("Possibility_Theory",
              _route("B2.15", "Possibility_Theory", "possibility", "_r_possibility")),
    "B2.16": ("Spherical_Fuzzy",
              _route("B2.16", "Spherical_Fuzzy", "spherical_fuzzy", "_r_spherical")),
    "B2.17": ("Fermatean_Fuzzy",
              _route("B2.17", "Fermatean_Fuzzy", "fermatean_fuzzy", "_r_fermatean")),
    "B2.18": ("MARCOS", _route("B2.18", "MARCOS", "marcos", "_r_marcos")),
    "B2.19": ("CRITIC_TOPSIS", _route("B2.19", "CRITIC_TOPSIS", "critic_topsis", "_r_critic")),
    "B2.20": ("Hypersoft_Sets",
              _refuse("B2.20", "Hypersoft_Sets", DISPOSITION_DISABLED,
                      "Hypersoft Sets is disabled for operational use: it is held as research "
                      "only and produces no reading for any project. A complete set of "
                      "attribute combinations does not change that.")),
}
