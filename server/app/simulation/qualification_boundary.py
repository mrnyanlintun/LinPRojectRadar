"""
THE SYSTEM-WIDE OPERATIONAL QUALIFICATION BOUNDARY (Run 31, Pass 2), v18.

WHAT THIS CLOSES, and it is the defect this programme has now failed at twice. Run 30 built
`canonical_v5` correct and oracled and PRODUCTION NEVER CALLED IT -- reached on zero of twenty --
while every direct-call proof stayed green for the entire life of the defect. Run 31's own first
pass then built `QualifiedEvidence` and left it decorative: the class existed, and the operational
dispatchers still accepted raw values. Specification section 22 says in terms that creating the
class while the dispatchers accept raw CPI/SPI/document-risk is NOT the gate.

So this file is not a helper. It is installed INTO the dispatch table, last, by `models.py`, and
`registry.run_module` cannot reach a gated module without passing through it. The proof suite
profiles the interpreter through the real production entry point rather than calling anything
here.

WHICH MODULES ARE GATED, AND IT IS DERIVED, NOT LISTED. `gated_module_ids()` reads the shipped
registry and selects the four consumer categories the architecture names -- Signal Synthesis,
Evidence Combination, Regulatory & Authority Thresholds / Delivery Quality Performance, and
Decision Optimization. A hand-written list here would be the duplicate-of-the-dispatcher that
section 13 forbids, and it would silently miss a module the registry gained.

WHAT THE GATE ASSESSES, AND WHAT IT HONESTLY DOES NOT. Run 20 cycle 3 settled this position for
the voting path and it is kept exactly: WHAT IS NOT DECLARED IS NOT ASSESSED, AND IS CERTAINLY
NOT ASSUMED CLEAN. A project package that declares no qualification record is not silently
treated as qualified -- but neither is a fabricated assessment invented for it. What the gate
refuses is evidence whose DECLARED qualification state makes it ineligible for the requested use:
UNASSESSED, INSUFFICIENT_EVIDENCE, REVIEW_REQUIRED, a missing critical input, an unresolved
material conflict, staleness against that use's own freshness rule, or -- for a use requiring
independently combinable evidence -- unresolved lineage.

THE TWO DIMENSIONS STAY SEPARATE (section 12), in BOTH directions:
  * a record may be QUALIFIED and its lineage UNRESOLVED -- it is still not independently
    combinable, because qualification is not independence;
  * a record may have ESTABLISHED_INDEPENDENT lineage and be STALE or UNASSESSED for the
    requested use -- it is still not eligible, because independence is not freshness.
Each dimension is tested against its own rule and neither is inferred from the other.

CATEGORY 9 IS NOT GATED BY ITSELF. The C1.x modules ARE the assessment; requiring them to consume
qualified evidence would be the circular architecture section 22 forbids. They are excluded here
by construction, not by exception.
"""

from __future__ import annotations

import functools
import pathlib
from typing import Any, Callable

from .models import insufficient
from .qualified_evidence import (
    ELIGIBLE_STATES, INSUFFICIENT_EVIDENCE, QualifiedEvidence, REVIEW_REQUIRED, STALE, UNASSESSED,
    assess,
)

#: Stamped on every row this boundary refuses, so a reader of the ledger can tell a refusal by
#: the gate from a module's own abstention.
RESULT_SOURCE = "QUALIFICATION_BOUNDARY_V18"

#: The reason code a gated refusal carries.
ABSTAIN_UNQUALIFIED = "evidence_not_qualified_for_use"

#: The governed structure key a project supplies its Category-9 assessment under. Absent means
#: undeclared, which is assessed as such rather than assumed clean.
QUALIFICATION_KEY = "evidenceQualification"

#: The registry category names whose consumers require qualified governed evidence. Derived
#: against the shipped registry, never a module list.
GATED_CATEGORY_NAMES = frozenset({
    "Signal Synthesis",                  # Category 6
    "Evidence Combination",              # Category 7
    "Regulatory & Authority Thresholds",  # Category 8 (B3)
    "Delivery Quality Performance",      # Category 8 (A6)
    "Decision Optimization",             # Category 10
})

#: Category 9 itself. Excluded by construction: it performs the assessment.
ASSESSING_CATEGORY_NAMES = frozenset({"Data Integrity"})

#: What each gated category's use requires. Section 21 forbids one global rule, so these are
#: per-use and a use that does not state a requirement does not acquire one.
# INDEPENDENCE IS NOT A CONDITION OF RUNNING, IT IS A CONDITION OF COMBINING, and putting it
# here was a real design error caught by the v17->v18 boundary proof. Section 12 says a QUALIFIED
# record whose lineage is UNRESOLVED is not INDEPENDENTLY COMBINABLE -- it does not say the
# consumer may not execute. Requiring independence at the module gate made every Signal Synthesis
# and Evidence Combination module ineligible on lineage alone, which is a DISABLED CONSUMER
# wearing a gate's clothes: the qualified version of the evidence was refused too, so eligibility
# had not changed at all.
#
# Independence is enforced where evidence is actually combined, which is where it belongs and
# where this repository already enforces it: `fuse_qualified`, the lineage declaration table and
# `eligible_signals`/`independent_signals` in the canonical layer. Those are untouched, so
# UNRESOLVED lineage is still never treated as independent -- Run 30's protection is intact and
# is asserted separately.
CATEGORY_USE: dict[str, tuple[str, dict[str, Any]]] = {
    "Signal Synthesis": ("signal_synthesis", {}),
    "Evidence Combination": ("evidence_combination", {}),
    "Regulatory & Authority Thresholds": ("governance_rule_check", {}),
    "Delivery Quality Performance": ("requirement_conformance", {}),
    "Decision Optimization": ("decision_optimization", {}),
}


def gated_module_ids() -> dict[str, str]:
    """
    {module_id: category_name} for every module the architecture requires qualified evidence for.

    READ FROM THE SHIPPED REGISTRY. A module the registry gains in a gated category is gated the
    moment it exists, with nothing here to remember to update.
    """
    # RUN 31 PASS-2 CLOSURE. The gated population now comes from the GOVERNED CONSUMER CONTRACT
    # in `qualification_contract`, not from a category-name set kept here. The contract is the
    # authority and this module is its reader; a route it declares REQUIRED is gated, and a route
    # in a consumer category that it does not declare at all is ALSO gated, because
    # CONFIGURATION_MISSING must block rather than pass.
    from .qualification_contract import (
        CONFIGURATION_MISSING, REQUIRED, expected_qualification_required, requirement_for,
    )
    cats = _registry_categories()
    gated: dict[str, str] = {}
    for mid, cat in cats.items():
        req = requirement_for(mid)
        if req == REQUIRED or (req == CONFIGURATION_MISSING
                               and mid in expected_qualification_required()):
            gated[mid] = cat
    # A route the contract cannot classify at all is gated too: deny is the default branch.
    for mid, cat in cats.items():
        if requirement_for(mid) == CONFIGURATION_MISSING and mid not in gated:
            gated[mid] = cat
    return gated


def _registry_categories() -> dict[str, str]:
    """
    {module_id: category_name} read from THE SAME CSV `registry.registry_index()` reads.

    Read directly rather than through the registry because this module is installed from inside
    `models.py` at import time and `registry` imports `models` -- going through the registry here
    is a circular import. The SOURCE is identical, which is the property that matters: the gated
    set is derived from the shipped registry data and not from a list maintained here.
    """
    import csv
    path = (pathlib.Path(__file__).resolve().parents[3] / "p0-baseline"
            / "module_renumbering_map.csv")
    with path.open(encoding="utf-8-sig", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if r.get("new_id")]
    # Retired aliases are not routes; see qualification_contract._registry_rows for why.
    return {r["new_id"]: r["category_name"] for r in rows
            if r["new_id"] != "RETIRED" and r.get("group") != "-"}


def declared_evidence(si: dict, module_id: str, category_name: str) -> QualifiedEvidence | None:
    """
    The project's DECLARED Category-9 assessment for this use, or None when none is declared.

    None is not "clean". The caller treats an undeclared package under the Run-20 cycle-3
    position: the conditions that can be assessed are assessed, and the ones the package does not
    declare are reported as unassessed rather than assumed satisfied.
    """
    decl = si.get(QUALIFICATION_KEY)
    if not isinstance(decl, dict):
        return None
    use, reqs = CATEGORY_USE.get(category_name, ("analytical_use", {}))
    per_module = decl.get(module_id) if isinstance(decl.get(module_id), dict) else decl
    ev = QualifiedEvidence(
        evidence_id=str(per_module.get("evidence_id") or f"{module_id}-declared"),
        source_id=per_module.get("source"),
        source_type=per_module.get("source_type"),
        period=per_module.get("period"),
        effective_date=per_module.get("effective_date"),
        _raw_value=si,
        required_inputs=tuple(per_module.get("required_inputs", ()) or ()),
        missing_fields=tuple(per_module.get("missing_fields", ()) or ()),
        invalid_fields=tuple(per_module.get("invalid_fields", ()) or ()),
        critical_missing=tuple(per_module.get("critical_missing", ()) or ()),
        timeliness_status=per_module.get("timeliness_status", UNASSESSED),
        verification_status=per_module.get("verification_status"),
        source_authority=per_module.get("source_authority"),
        reliability_rubric_version=per_module.get("reliability_rubric_version"),
        reliability_weight=per_module.get("reliability_weight"),
        missing_audit_elements=tuple(per_module.get("missing_audit_elements", ()) or ()),
        critical_audit_missing=tuple(per_module.get("critical_audit_missing", ()) or ()),
        package_missing_domains=tuple(per_module.get("package_missing_domains", ()) or ()),
        material_conflicts=tuple(per_module.get("material_conflicts", ()) or ()),
    )
    # LINEAGE IS READ FROM THE SHIPPED DECLARATION TABLE, NEVER FROM THE PACKAGE. A project may
    # not declare its own evidence independent: that is exactly the manufactured independence
    # the lineage table exists to prevent.
    from .lineage import evidence_body_of, independence_established, lineage_status
    status = lineage_status(module_id, applicable=True)
    ev.lineage_status = status
    ev.independence_established = independence_established(status)
    ev.evidence_body = evidence_body_of(module_id, status)
    # An explicitly declared state is honoured only when it is NOT more favourable than what the
    # evidence supports: a package may declare itself unassessed, and may not declare itself
    # qualified. `assess` recomputes the verdict from the evidence characteristics.
    declared_state = per_module.get("qualification_state")
    assess(ev, uses=(use,), use_requirements={use: reqs})
    if declared_state == UNASSESSED:
        ev.qualification_state = UNASSESSED
        ev.use_eligibility = {use: False}
        ev.qualification_reasons = tuple(list(ev.qualification_reasons)
                                         + ["the package declares this evidence UNASSESSED"])
    return ev


def _refuse(module_id: str, method_class: str, ev: QualifiedEvidence | None, use: str,
            sentence: str) -> dict[str, Any]:
    out = insufficient(method_class, sentence, ABSTAIN_UNQUALIFIED)
    out["result_source"] = RESULT_SOURCE
    out["qualification"] = {
        "requested_use": use,
        "qualification_state": ev.qualification_state if ev else UNASSESSED,
        "eligible_for_use": False,
        "qualification_reasons": list(ev.qualification_reasons) if ev else
            ["no Category-9 assessment is declared for this evidence, so it is unassessed"],
        "lineage_status": ev.lineage_status if ev else None,
        "independence_established": ev.independence_established if ev else False,
        "material_conflicts": [dict(c) for c in ev.material_conflicts] if ev else [],
        "timeliness_status": ev.timeliness_status if ev else UNASSESSED,
    }
    return out


def _refuse_missing(module_id: str, method_class: str, use: str, reason_code: str,
                    sentence: str) -> dict[str, Any]:
    """
    The governed abstention for a route blocked before any evidence could be assessed.

    THE ROW IS NOT BLANK AND IS NOT HIDDEN (section 5). It carries the module, the requested use,
    the qualification state UNASSESSED, the reason, the lineage state SEPARATELY, the simulation
    version and an explicit `consumer_executed = False`. It never says QUALIFIED.
    """
    from .lineage import evidence_body_of, independence_established, lineage_status
    from .models import SIMULATION_VERSION, insufficient

    status = lineage_status(module_id, applicable=True)
    out = insufficient(method_class, sentence, reason_code)
    out["result_source"] = RESULT_SOURCE
    out["consumer_executed"] = False
    out["simulation_version"] = SIMULATION_VERSION
    out["qualification"] = {
        "module_id": module_id,
        "requested_use": use,
        "qualification_state": UNASSESSED,
        "eligible_for_use": False,
        "qualification_reason": reason_code,
        "qualification_reasons": [sentence],
        "evidence_id": None,
        "simulation_version": SIMULATION_VERSION,
        "consumer_executed": False,
    }
    # LINEAGE IS REPORTED SEPARATELY AND IS NOT INFERRED FROM THE MISSING QUALIFICATION. The two
    # dimensions are different defects and each keeps its own answer.
    out["lineage"] = {
        "lineage_status": status,
        "independence_established": independence_established(status),
        "evidence_body": evidence_body_of(module_id, status),
    }
    return out


def install(validated: dict[str, tuple[str, Callable]]) -> dict[str, list[str]]:
    """
    Wrap every gated runner IN THE DISPATCH TABLE. Returns what was wrapped, for the artifact.

    THIS IS THE WHOLE ENFORCEMENT. After this call there is no entry in `VALIDATED` for a gated
    module that reaches its runner without the boundary first. `registry.run_module` looks the
    runner up here, so a consumer cannot route around it by hand-building a signal package.
    """
    gated = gated_module_ids()
    wrapped: dict[str, list[str]] = {"gated": [], "assessing_excluded": []}
    for mid, cat in sorted(gated.items()):
        entry = validated.get(mid)
        if entry is None:
            continue
        method_class, inner = entry
        use, _reqs = CATEGORY_USE.get(cat, ("analytical_use", {}))

        def make(mid=mid, cat=cat, method_class=method_class, inner=inner, use=use):
            def run(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
                from .qualification_contract import (
                    ASSESSMENT_MISSING, CONFIGURATION_MISSING, CONTRACT_MISSING, requirement_for,
                )
                # THE CONTRACT IS CONSULTED FIRST, AND AN ABSENT CONTRACT BLOCKS. Section 2: a
                # target route with no governed qualification-requirement declaration is a
                # configuration failure. The default branch is deny.
                if requirement_for(mid) == CONFIGURATION_MISSING:
                    return _refuse_missing(
                        mid, method_class, use, CONTRACT_MISSING,
                        "No governed qualification requirement is declared for this route, so it "
                        "is not executed. An undeclared route is a configuration failure and is "
                        "blocked rather than allowed through.")
                ev = declared_evidence(si, mid, cat)
                # OWNER DECISION, PASS-2 CLOSURE: ABSENCE FAILS CLOSED. A package carrying no
                # Category-9 assessment is UNASSESSED, and UNASSESSED is ineligible. Nothing is
                # inferred, nothing is imputed, and the consumer does not execute first and get
                # stamped afterwards.
                if ev is None:
                    return _refuse_missing(
                        mid, method_class, use, ASSESSMENT_MISSING,
                        "The evidence offered to this measure carries no Category-9 assessment, "
                        "so it is unassessed and not eligible for this use. No reading is "
                        "produced and no figure is used in its place. This measure is one of "
                        "the exceptions to carry-forward: an earlier reading is not shown here "
                        "either, because the refusal is about whether this evidence may be used "
                        "at all, and republishing a reading the gate has just declared "
                        "ineligible would defeat the gate.")
                if not ev.eligible_for(use):
                    return _refuse(
                        mid, method_class, ev, use,
                        "The evidence supplied for this measure has not been qualified for this "
                        "use, so it is not read and no figure is produced in its place. No "
                        "earlier reading is carried forward in its place either: the refusal is "
                        "about whether this evidence may be used at all, not about a missing "
                        "input. "
                        + ("; ".join(ev.qualification_reasons) if ev.qualification_reasons
                           else ""))
                result = inner(si, rand, period_cutoff)
                if ev is not None and isinstance(result, dict):
                    result.setdefault("qualification", {})
                    if isinstance(result["qualification"], dict):
                        result["qualification"].update({
                            "requested_use": use,
                            "qualification_state": ev.qualification_state,
                            "eligible_for_use": True,
                            "lineage_status": ev.lineage_status,
                            "independence_established": ev.independence_established,
                        })
                return result
            # TRANSPARENT TO INTROSPECTION, OPAQUE TO BYPASS. `functools.wraps` copies the
            # inner runner's __name__, __module__, __doc__ and sets __wrapped__, so every
            # existing proof that asks WHICH IMPLEMENTATION a module resolves to -- Run 30's
            # Category-7 route inventory, Run 27's parsimony source reads, Run 14's
            # disabled-method lookups -- keeps reading the real runner rather than this wrapper.
            # That is the honest answer to those questions: the canonical route is still what
            # executes, with the boundary in front of it.
            #
            # The gate is NOT hidden. `__gated__`, `__gated_use__` and `__wrapped_runner__` are
            # set explicitly and `gate_installed_for()` reports them, so a proof that asks
            # WHETHER THE BOUNDARY IS PRESENT gets a straight answer too. The two questions are
            # different and both are answerable.
            functools.wraps(inner)(run)
            run.__gated__ = True
            run.__wrapped_runner__ = inner
            run.__gated_use__ = use
            return run

        validated[mid] = (method_class, make())
        wrapped["gated"].append(mid)
    wrapped["assessing_excluded"] = sorted(
        mid for mid, cat in _registry_categories().items()
        if cat in ASSESSING_CATEGORY_NAMES)
    return wrapped


def gate_installed_for(fn: Callable) -> dict[str, Any] | None:
    """Whether the qualification boundary wraps this dispatch entry, and for which use."""
    if not getattr(fn, "__gated__", False):
        return None
    return {"gated": True, "use": getattr(fn, "__gated_use__", None),
            "wraps": getattr(fn, "__wrapped_runner__", None),
            "result_source": RESULT_SOURCE}
