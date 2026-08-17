"""
THE GOVERNED QUALIFICATION-REQUIREMENT CONTRACT (Run 31, Pass-2 closure, v19).

WHY THIS FILE EXISTS AND WHY IT IS NOT A LIST IN THE DISPATCHER. The owner's closure decision is
that a package carrying NO Category-9 assessment must FAIL CLOSED for any consumer whose
architecture requires qualified evidence. The obvious way to implement that is to work out, at
the call site, what each module needs -- and that is exactly what section 2 forbids, because a
requirement computed inside the dispatcher is a copy of production logic checked against
production logic, which is the failure this programme has already found repeatedly.

So the requirement is DECLARED HERE, per registered route, and the dispatcher reads the
declaration. This file is the authority; `qualification_boundary` is only its reader.

THE THREE STATES, and the fourth thing that is not a state.

    REQUIRED        this route consumes governed evidence and may not execute without a
                    Category-9 assessment of it.
    NOT_REQUIRED    this route does not consume governed evidence in the sense the architecture
                    means -- it PRODUCES or TRANSFORMS project evidence. Categories 1 to 5.
    NOT_APPLICABLE  this route performs the assessment itself. Category 9. Gating it behind its
                    own output is the circular architecture the specification forbids.

    CONFIGURATION_MISSING is NOT a state a route may be declared in. It is what
    `requirement_for` RETURNS when a route in a consumer category has no declaration at all, and
    section 2 is explicit about what must then happen: treat it as configuration failure and
    BLOCK. THE DEFAULT BRANCH IS DENY. A route somebody forgot to declare fails; it does not sail
    through, and `test_run31_pass2_acceptance` injects exactly that to prove the default is deny
    rather than permissive.

HOW THE DECLARATIONS ARE BUILT, and why this is not a second hand-written route list. The
population comes from the SHIPPED REGISTRY CSV -- the same file `registry.registry_index()` reads
-- and each module's requirement follows from its registered CATEGORY ROLE, which is a property
the registry already records. Nothing here enumerates module ids. A module the registry gains in
a consumer category is REQUIRED the moment it exists; a module that moves category moves with it.
The guard then derives the expected population independently and compares, so a category
silently dropped from `CONSUMER_CATEGORY_ROLES` turns it red rather than shrinking the loop.
"""

from __future__ import annotations

import csv
import pathlib
from typing import Any

REQUIRED = "QUALIFICATION_REQUIRED"
NOT_REQUIRED = "QUALIFICATION_NOT_REQUIRED"
NOT_APPLICABLE = "QUALIFICATION_NOT_APPLICABLE"
CONFIGURATION_MISSING = "QUALIFICATION_CONTRACT_MISSING"

DECLARABLE_STATES = (REQUIRED, NOT_REQUIRED, NOT_APPLICABLE)

#: The reason a blocked route records when the evidence carries no Category-9 assessment at all.
#: Distinct from a DECLARED-but-ineligible assessment, which keeps its own reasons.
ASSESSMENT_MISSING = "CATEGORY9_ASSESSMENT_MISSING"

#: The reason a blocked route records when its own contract is absent.
CONTRACT_MISSING = "QUALIFICATION_CONTRACT_MISSING"

#: THE GOVERNED ROLE OF EACH REGISTERED CATEGORY, which is what decides the requirement. These
#: are the architecture's own words: Categories 1-5 generate or transform project evidence,
#: Category 9 qualifies it, and Categories 6, 7, 8 and 10 consume the qualified result.
CONSUMER_CATEGORY_ROLES: dict[str, str] = {
    # Category 6 -- signal synthesis over governed signals
    "Signal Synthesis": REQUIRED,
    # Category 7 -- evidence combination over governed epistemic structures
    "Evidence Combination": REQUIRED,
    # Category 8 -- governance, authority and conformance over governed evidence
    "Regulatory & Authority Thresholds": REQUIRED,
    "Delivery Quality Performance": REQUIRED,
    # Category 10 -- decision optimisation over governed project state
    "Decision Optimization": REQUIRED,
    # Category 9 -- performs the assessment; gating it behind itself is circular
    "Data Integrity": NOT_APPLICABLE,
}

#: Categories 1 to 5 and the portfolio layer PRODUCE or TRANSFORM project evidence. They are the
#: left-hand side of `PROJECT EVIDENCE -> CATEGORY 9 -> QUALIFIED EVIDENCE -> USE`, so requiring
#: them to consume qualified evidence would make them consumers of their own output, which
#: section 2 forbids in terms.
PRODUCER_CATEGORY_ROLES: dict[str, str] = {
    "Cost & EVM Performance": NOT_REQUIRED,
    "Schedule Performance": NOT_REQUIRED,
    "Cost Risk": NOT_REQUIRED,
    "Document-Derived Condition Signals": NOT_REQUIRED,
    "System Dynamics & Complexity": NOT_REQUIRED,
    "Portfolio Health": NOT_REQUIRED,
}

CATEGORY_ROLES: dict[str, str] = {**CONSUMER_CATEGORY_ROLES, **PRODUCER_CATEGORY_ROLES}

_CSV = pathlib.Path(__file__).resolve().parents[3] / "p0-baseline" / "module_renumbering_map.csv"


def _registry_rows() -> list[dict[str, str]]:
    """
    Read the SHIPPED REGISTRY CSV directly.

    Directly rather than through `registry.registry_index()` because this module is imported from
    `models.py` at import time and `registry` imports `models`; going through the registry here
    is a circular import. The SOURCE is identical, which is the property that matters.
    """
    with _CSV.open(encoding="utf-8-sig", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if r.get("new_id")]
    # RETIRED ALIASES ARE NOT ROUTES. Two rows carry new_id "RETIRED" and group "-": they are
    # consolidated aliases of A4.1 and A5.1, recorded so the renumbering stays reconstructable.
    # They dispatch to nothing and appear in no validation map, so they are neither consumers nor
    # producers and must not be declared either way -- gating an alias would inflate the expected
    # population against a route that cannot execute.
    return [r for r in rows if r["new_id"] != "RETIRED" and r.get("group") != "-"]


def qualification_contract() -> dict[str, str]:
    """
    {module_id: declared requirement} for every registered route.

    Derived from the registry's own category assignment. A category absent from `CATEGORY_ROLES`
    produces NO entry, which `requirement_for` then reports as CONFIGURATION_MISSING rather than
    silently defaulting to permissive.
    """
    out: dict[str, str] = {}
    for r in _registry_rows():
        role = CATEGORY_ROLES.get(r["category_name"])
        if role is not None:
            out[r["new_id"]] = role
    return out


def requirement_for(module_id: str) -> str:
    """
    The governed requirement for one route, or CONFIGURATION_MISSING.

    THE DEFAULT IS DENY. A module in a category this contract does not declare gets
    CONFIGURATION_MISSING, and the boundary blocks it. Section 2: a target downstream route with
    no governed qualification-requirement declaration is a configuration failure, not a licence.
    """
    return qualification_contract().get(module_id, CONFIGURATION_MISSING)


def expected_qualification_required() -> set[str]:
    """
    The routes that MUST be gated, derived independently from the registry and the category role.

    The guard compares this against what the dispatcher actually gated. Deriving it here rather
    than reading the boundary's own answer is the whole point: a category silently dropped from
    `CONSUMER_CATEGORY_ROLES` changes both sides of a self-referential check and neither side of
    this one.
    """
    consumer = {c for c, role in CONSUMER_CATEGORY_ROLES.items() if role == REQUIRED}
    return {r["new_id"] for r in _registry_rows() if r["category_name"] in consumer}


def expected_not_applicable() -> set[str]:
    """The routes that must NOT be gated because they perform the assessment."""
    na = {c for c, role in CONSUMER_CATEGORY_ROLES.items() if role == NOT_APPLICABLE}
    return {r["new_id"] for r in _registry_rows() if r["category_name"] in na}


def contract_report() -> dict[str, Any]:
    """The whole contract, for the artifact and for the guard."""
    c = qualification_contract()
    return {
        "declared_routes": len(c),
        "required": sorted(m for m, s in c.items() if s == REQUIRED),
        "not_required": sorted(m for m, s in c.items() if s == NOT_REQUIRED),
        "not_applicable": sorted(m for m, s in c.items() if s == NOT_APPLICABLE),
        "undeclared_categories": sorted({r["category_name"] for r in _registry_rows()
                                         if r["category_name"] not in CATEGORY_ROLES}),
    }
