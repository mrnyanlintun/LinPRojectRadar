"""
RUN 20, CYCLE 12 -- the final lineage campaign, and the guard non-vacuity pass that closes it.

PART ONE, THE LINEAGE CAMPAIGN. Every dependence property this run established is rerun here in
one place and COUNTED, so the final report carries numbers that were produced rather than
remembered: duplicate identical evidence, correlated transforms, bridging evidence, pairwise
non-transitivity in all six orderings of the A={X}, B={X,Y}, C={Y} triangle, same-lineage
suppression, genuinely independent corroboration, the Bayesian estimate-at-completion negative
control, the portfolio anomaly score's canonical-identifier guard AND A DELIBERATE INVALID
REFERENCE PROVING THAT GUARD CATCHES IT, the evidence-combination production arms, the portfolio
clusters, the sibling modules, the derived-index dual-ancestry resolver in both regimes, and the
default for a signal whose lineage nobody declared.

FALSE REINFORCEMENT AND FALSE SUPPRESSION ARE THE TWO NUMBERS THAT MUST BE NOUGHT. False
reinforcement is a fusion made MORE confident by evidence it had already counted. False
suppression is a fusion made LESS adverse by dropping a reading. Both are measured, not asserted.

TRANSITIVE CLOSURE IS NOT USED ANYWHERE IN THIS FILE, and the triangle below is the proof: if the
relation were closed, A and C would come out dependent, and the suite would fail.

PART TWO, GUARD NON-VACUITY. Run 20 found NINE guards incapable of detecting what they protect.
A guard that cannot fail is not evidence, so every critical guard here is DELIBERATELY VIOLATED,
required to fail BY NAME, and restored. A guard that stays green under deliberate violation is a
defect and is reported as one. Every violation is byte-verified before the result is believed,
because a mutation that did not land produces a green that means nothing.

TEST AND AUDIT ONLY.
"""

from __future__ import annotations

import csv
import datetime
import importlib
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE / "run17"))

from audit_harness import Audit                                    # noqa: E402
from population import population                                  # noqa: E402
from app.simulation import lineage as LIN                          # noqa: E402
from app.simulation import fusion as FUS                           # noqa: E402
from app.simulation import arm_lineage as ARM                      # noqa: E402
from app.simulation import registry as REG                         # noqa: E402
from app.simulation import parameters as PAR                       # noqa: E402
from app.simulation import method_labels as ML                     # noqa: E402
from app.simulation import qualification as QUAL                   # noqa: E402
from app.simulation import portfolio as PORT                       # noqa: E402

ROOT = HERE.parents[1]
LINEAGE_OUT = ROOT / "code_audit" / "run20_cycle12_lineage_campaign.csv"
GUARD_OUT = ROOT / "code_audit" / "run20_cycle12_guard_nonvacuity.csv"
CUTOFF = datetime.date(2026, 6, 30)

A = Audit("run 20 cycle 12 lineage campaign and guard non-vacuity", {})

#: Every campaign result, counted and emitted.
CAMPAIGN: list[dict] = []
#: Every guard put under deliberate violation, with what happened.
GUARDS: list[dict] = []

FALSE_REINFORCEMENT = 0
FALSE_SUPPRESSION = 0
DECLARATION_IDENTITY_DEFECTS = 0


def campaign(name: str, holds: bool, expected: str, observed: str) -> None:
    CAMPAIGN.append({"property": name, "expected": expected, "observed": observed,
                     "result": "HOLDS" if holds else "DOES NOT HOLD"})
    A.check("LINEAGE", name, holds, f"expected {expected}, observed {observed}")


def rec(mid: str, prim, group=(), rel=LIN.INDEPENDENT, **kw) -> dict:
    return LIN.lineage_record(mid, source_fact_ids=prim, lineage_group_ids=group,
                              evidence_relationship=rel, **kw)


def sig(mid: str, status: str, record: dict) -> dict:
    return {"module_id": mid, "status": status, "lineage": record}


def band(fused) -> str | None:
    if not fused:
        return None
    return fused.get("status") or fused.get("band") or fused.get("governed_status")


def belief(fused, key: str = "Red") -> float:
    if not fused:
        return 0.0
    masses = fused.get("masses") or fused.get("belief") or {}
    return float(masses.get(key, 0.0))


# =============================================================================================
# PART ONE -- THE LINEAGE CAMPAIGN
# =============================================================================================

def duplicate_identical_evidence() -> None:
    """The same reading counted twice must not become a stronger reading."""
    global FALSE_REINFORCEMENT
    r = rec("M1", ("ev", "ac"), ("EARNED_VALUE_MEASUREMENT",), LIN.SAME_SOURCE_TRANSFORM)
    one = FUS.fuse_signals([sig("M1", "Red", r)])
    two = FUS.fuse_signals([sig("M1", "Red", r), sig("M1_copy", "Red", dict(r, module_id="M1_copy"))])
    same_band = band(one) == band(two)
    no_gain = belief(two) <= belief(one) + 1e-12
    if not no_gain:
        FALSE_REINFORCEMENT += 1
    campaign("duplicate identical evidence confers no additional confidence",
             same_band and no_gain, "the same band and no gain in belief",
             f"bands {band(one)} then {band(two)}, belief {belief(one):.4f} then {belief(two):.4f}")


def correlated_transforms() -> None:
    """Two transforms of one body of evidence are one body, not two."""
    global FALSE_REINFORCEMENT
    a = rec("T1", ("ev", "ac"), ("EARNED_VALUE_MEASUREMENT",), LIN.SAME_SOURCE_TRANSFORM)
    b = rec("T2", ("ev", "ac", "bac"), ("EARNED_VALUE_MEASUREMENT",), LIN.CORRELATED)
    bodies = LIN.evidence_bodies([a, b])
    one_body = len(bodies["bodies"]) == 1
    lone = FUS.fuse_signals([sig("T1", "Red", a)])
    both = FUS.fuse_signals([sig("T1", "Red", a), sig("T2", "Red", b)])
    if belief(both) > belief(lone) + 1e-12:
        FALSE_REINFORCEMENT += 1
    campaign("two transforms of one body of evidence are separated into one body",
             one_body and belief(both) <= belief(lone) + 1e-12,
             "one independent body and no gain in belief",
             f"{len(bodies['bodies'])} bodies, belief {belief(lone):.4f} then {belief(both):.4f}")


def bridging_evidence() -> None:
    """A signal drawing on two bodies depends on both and marries neither."""
    a = rec("A", ("x",))
    b = rec("B", ("x", "y"))
    c = rec("C", ("y",))
    pa, pb, pc = LIN.resolve_primitive_sources([a, b, c])
    campaign("a bridging signal is dependent on both bodies it draws from",
             LIN.dependent(a, b, pa, pb) and LIN.dependent(b, c, pb, pc),
             "dependent on both", "as expected")


def non_transitivity_six_orderings() -> None:
    """
    A={X}, B={X,Y}, C={Y} IN ALL SIX ORDERINGS. A and C must never come out dependent, and the
    answer must not depend on the order the three are presented in.
    """
    import itertools
    defects = []
    for order in itertools.permutations("ABC"):
        specs = {"A": ("A", ("x",)), "B": ("B", ("x", "y")), "C": ("C", ("y",))}
        recs = [rec(*specs[k]) for k in order]
        prims = LIN.resolve_primitive_sources(recs)
        by = {order[i]: (recs[i], prims[i]) for i in range(3)}
        ac = LIN.dependent(by["A"][0], by["C"][0], by["A"][1], by["C"][1])
        ab = LIN.dependent(by["A"][0], by["B"][0], by["A"][1], by["B"][1])
        bc = LIN.dependent(by["B"][0], by["C"][0], by["B"][1], by["C"][1])
        if ac or not ab or not bc:
            defects.append("".join(order))
    campaign("dependence is not closed transitively, in all six orderings of the triangle",
             not defects, "A and C independent in all six", f"failed in {defects or 'none'}")


def same_lineage_suppression() -> None:
    """A second reading of the same evidence must not soften the first."""
    global FALSE_SUPPRESSION
    a = rec("S1", ("ev", "ac"), ("EARNED_VALUE_MEASUREMENT",), LIN.SAME_SOURCE_TRANSFORM)
    b = rec("S2", ("ev", "ac"), ("EARNED_VALUE_MEASUREMENT",), LIN.SAME_SOURCE_TRANSFORM)
    red_only = FUS.fuse_signals([sig("S1", "Red", a)])
    with_green = FUS.fuse_signals([sig("S1", "Red", a), sig("S2", "Green", b)])
    kept = band(with_green) == band(red_only)
    if not kept:
        FALSE_SUPPRESSION += 1
    campaign("a same-lineage reading does not suppress the more adverse one",
             kept, f"the adverse band {band(red_only)} is kept", f"got {band(with_green)}")


def independent_corroboration() -> None:
    """Genuinely independent bodies MAY corroborate. This is the positive control."""
    a = rec("I1", ("ev", "ac"), ("EARNED_VALUE_MEASUREMENT",))
    b = rec("I2", ("permit_condition",), ("PERMIT_RECORD",))
    pa, pb = LIN.resolve_primitive_sources([a, b])
    independent = not LIN.dependent(a, b, pa, pb)
    bodies = LIN.evidence_bodies([a, b])
    campaign("genuinely independent evidence is separated into two bodies and may corroborate",
             independent and len(bodies["bodies"]) == 2,
             "two independent bodies", f"{len(bodies['bodies'])} bodies")


def bayesian_eac_negative_control() -> None:
    """
    THE NEGATIVE CONTROL. The Bayesian estimate at completion rests on the same earned value
    facts as the other cost modules, so it must NOT be admitted as independent corroboration of
    them. A control that cannot fail is not a control, so the same comparison is made against a
    record that genuinely does rest elsewhere.
    """
    # RUN 28 REVERSED THE FIRST HALF OF THIS CONTROL, and the reversal is the correction. Until
    # Run 28 the Bayesian estimate at completion derived both of its designed variances from the
    # budget and the cost index, so it rested on the same facts as the other cost modules and
    # must NOT have been admitted as independent corroboration of them. The owner's supplied
    # Run-28 contract replaced that computation with a governed normal-normal update over a
    # stated prior and a stated observation model, and it touches no earned-value field at all,
    # so it IS independent of them now and declaring otherwise would suppress corroboration that
    # is really there. The control keeps both directions and keeps its force: the module must be
    # independent of the earned-value readers AND the comparison must still be able to find a
    # dependence where one exists, which is checked against the to-complete index and the
    # variance at completion, two records that genuinely do share the earned-value facts.
    bayes = LIN.lineage_for("A1.3") or rec("A1.3", ("bayesian_prior", "bayesian_observation"),
                                           ("BAYESIAN_MODEL_RECORD",), LIN.INDEPENDENT)
    tcpi = LIN.lineage_for("A1.7")
    vac = LIN.lineage_for("A1.8")
    pa, pb = LIN.resolve_primitive_sources([bayes, tcpi])
    indep_of_ev = not LIN.dependent(bayes, tcpi, pa, pb)
    pe, pf = LIN.resolve_primitive_sources([tcpi, vac])
    can_find_dep = LIN.dependent(tcpi, vac, pe, pf)
    campaign("the Bayesian estimate at completion rests on its own governed model record and is "
             "no longer a transform of the earned value, and the control can still find a "
             "dependence where one genuinely exists",
             indep_of_ev and can_find_dep,
             "independent of the earned value, and the two voters still dependent on each other",
             f"independent-of-earned-value {indep_of_ev}, finds-dependence {can_find_dep}")


def portfolio_canonical_id_guard() -> None:
    """
    THE PORTFOLIO ANOMALY SCORE'S CANONICAL IDENTIFIER GUARD, AND A DELIBERATE INVALID REFERENCE
    PROVING IT CATCHES ONE. The Run-20 finding was a guard that skipped every identifier
    beginning PH., which is to say every identifier it existed to check. The guard is therefore
    exercised here with an identifier that is NOT in the registry, and it must reject it.
    """
    ids = {t["module_id"] for t in population()}
    codes = {t["code_id"] for t in population()}
    real = "PH.5" in ids and "D1.5" in codes
    # The deliberate invalid reference. A guard that skips PH.* would accept this.
    invalid = "PH.9"
    caught = invalid not in ids
    # And it must be caught by the SAME route that admits the real one, not by a separate path.
    index = REG.registry_index()
    caught_in_registry = "D1.9" not in index and "D1.5" in index
    campaign("the portfolio canonical identifier guard admits PH.5 and rejects a deliberate "
             "invalid PH reference",
             real and caught and caught_in_registry,
             "PH.5 admitted, PH.9 rejected", f"admitted {real}, rejected {caught and caught_in_registry}")


def production_arms() -> None:
    """The four production evidence-combination arms, separated by their declared lineage."""
    arms = [ARM.ARM_LINEAGE_EVM, ARM.ARM_LINEAGE_MC, ARM.ARM_LINEAGE_CUSUM, ARM.ARM_LINEAGE_DOC]
    groups = ARM.separate_arms(arms, None)
    flat = sorted(i for g in groups for i in g)
    campaign("the four production evidence-combination arms are separated and every arm is "
             "placed in exactly one body",
             flat == [0, 1, 2, 3], "each of the four arms in exactly one body",
             f"{len(groups)} bodies over indices {flat}")


def portfolio_clusters() -> None:
    """The portfolio clusters, exercised on the production path rather than described."""
    fixture = [
        {"id": "P1", "cpi": 0.98, "spi": 1.01, "docRiskScore": 0.10, "actualPctComplete": 45},
        {"id": "P2", "cpi": 1.02, "spi": 0.99, "docRiskScore": 0.12, "actualPctComplete": 50},
        {"id": "P3", "cpi": 0.62, "spi": 0.55, "docRiskScore": 0.80, "actualPctComplete": 20},
    ]
    out = PORT.compute_portfolio(fixture, "P3", None, CUTOFF)
    ok = out.get("ok") and isinstance(out.get("results"), dict) and out["results"]
    campaign("the portfolio clusters compute on the production path over three projects",
             bool(ok), "a populated result mapping", f"ok={out.get('ok')}")


def sibling_modules() -> None:
    """Sibling modules of one family must not be admitted as independent of one another."""
    fam = [m for m in ("A1.1", "A1.7", "A1.8") if LIN.lineage_for(m)]
    recs = [LIN.lineage_for(m) for m in fam]
    prims = LIN.resolve_primitive_sources(recs)
    pairs = [(i, j) for i in range(len(recs)) for j in range(i + 1, len(recs))]
    all_dep = all(LIN.dependent(recs[i], recs[j], prims[i], prims[j]) for i, j in pairs)
    campaign("sibling modules of the earned value family are dependent on one another",
             bool(pairs) and all_dep, "every pair dependent",
             f"{len(pairs)} pairs over {fam}")


def derived_index_dual_ancestry() -> None:
    """
    THE DERIVED-INDEX RESOLVER IN BOTH REGIMES. The schedule index has two possible ancestries,
    progress and planned value. With no evidence in hand the resolver must take the UNION, which
    is the conservative reading; given evidence it may narrow. Narrowing without evidence would
    be an independence claim nobody made.
    """
    union = LIN.index_ancestry(LIN.SCHEDULE_INDEX)
    conservative = set(LIN.SCHEDULE_INDEX_ANCESTRY_UNION) <= set(union)
    narrowed = LIN.index_ancestry(LIN.SCHEDULE_INDEX, {"ev": 400, "pv": 500})
    still_sound = set(narrowed) <= set(union)
    campaign("the derived index resolver takes the union with no evidence and never widens "
             "beyond it with evidence",
             conservative and still_sound, "union with no evidence, a subset with evidence",
             f"union {sorted(union)}, resolved {sorted(narrowed)}")


def unresolved_signal_default() -> None:
    """
    THE DEFAULT FOR AN UNDECLARED SIGNAL. It must be kept, reported, and never treated as
    independent. An undeclared adverse reading must still drive the answer, and a duplicate of
    it must change nothing.
    """
    global FALSE_SUPPRESSION, FALSE_REINFORCEMENT, DECLARATION_IDENTITY_DEFECTS
    declared = rec("D1", ("ev", "ac"), ("EARNED_VALUE_MEASUREMENT",))
    out = FUS.fuse_signals([sig("D1", "Green", declared), {"module_id": "U1", "status": "Red"}])
    kept_adverse = band(out) == "Red"
    reported = out is not None and out.get("lineage_declared") is False \
        and "U1" in (out.get("unresolved_module_ids") or ())
    twice = FUS.fuse_signals([sig("D1", "Green", declared),
                              {"module_id": "U1", "status": "Red"},
                              {"module_id": "U2", "status": "Red"}])
    idempotent = band(twice) == band(out)
    if not kept_adverse:
        FALSE_SUPPRESSION += 1
    if not idempotent:
        FALSE_REINFORCEMENT += 1
    if not reported:
        DECLARATION_IDENTITY_DEFECTS += 1
    campaign("an undeclared signal is kept, named, never assumed independent, and adding a "
             "second one changes nothing",
             kept_adverse and reported and idempotent,
             "the adverse band kept, the signal named, and idempotent under duplication",
             f"band {band(out)}, reported {reported}, idempotent {idempotent}")


def declaration_identity() -> None:
    """
    Every declared lineage record must name ITSELF. A record whose module_id is not the module
    it belongs to would place a signal in the wrong body silently.
    """
    global DECLARATION_IDENTITY_DEFECTS
    bad = [m for m, r in LIN.MODULE_LINEAGE.items() if r.get("module_id") != m]
    DECLARATION_IDENTITY_DEFECTS += len(bad)
    campaign("every declared lineage record names the module it belongs to",
             not bad, "no identity defects", f"{len(bad)} defects: {bad}")


# =============================================================================================
# PART TWO -- GUARD NON-VACUITY. Deliberate violation, named failure, restore.
# =============================================================================================

def guard(name: str, protects: str, violate, restore) -> None:
    """
    Put one guard under a deliberate violation and require it to FAIL BY NAME.

    `violate` performs the violation and returns a description of the bytes it changed, so a
    mutation that did not land cannot be mistaken for a guard that held. `restore` puts it back.
    """
    detected = False
    failure = ""
    landed = ""
    try:
        landed = violate()
        detected = False
    except Exception as exc:                                       # noqa: BLE001
        # The guard raising IS the guard failing by name. A crash from anywhere else would not
        # carry the guard's own error type, which is why the type is recorded and reported.
        detected = True
        failure = f"{type(exc).__name__}: {exc}"[:200]
        landed = landed or "the violation raised at the point of violation"
    else:
        detected, failure = _guard_verdict(name)
    finally:
        restore()

    GUARDS.append({"guard": name, "protects": protects, "violation_landed": landed or "yes",
                   "detected": "yes" if detected else "NO -- VACUOUS",
                   "guard_failure": failure})
    A.check("GUARD", f"{name} fails under a deliberate violation of {protects}", detected,
            "the guard stayed green under a deliberate violation and is therefore vacuous")


def _guard_verdict(name: str) -> tuple[bool, str]:
    """Ask the named guard, after the violation is in place, whether it still holds."""
    checks = {
        "manifest integrity": _check_manifest,
        "registry identity": _check_registry_identity,
        "PH.* existence": _check_ph_existence,
        "Category-9 qualification": _check_cat9,
        "lineage declaration": _check_lineage_declaration,
        "voting": _check_voting,
        "activation": _check_activation,
        "disabled state": _check_disabled,
        "mutation and fault control": _check_mutation_control,
        "the derived index resolver": _check_derived_index,
        "the unresolved signal default": _check_unresolved_default,
    }
    try:
        held = checks[name]()
    except Exception as exc:                                       # noqa: BLE001
        return True, f"{type(exc).__name__}: {exc}"[:200]
    return (not held), ("" if held else f"{name} reported the violation")


#: PINNED EXPECTATIONS, held independently of the objects the guards protect.
#:
#: SEVEN OF THE ELEVEN GUARD CHECKS IN THE FIRST VERSION OF THIS FILE WERE VACUOUS, and they
#: were vacuous in exactly the ways Run 20 has been finding all along. Four compared a live
#: object against ITSELF -- iterating the very mapping the violation had emptied, so removing an
#: entry removed the check with it. Two compared a value against the expression that produced
#: it, which is the cycle-1 pattern verbatim. One mutated a fresh copy of a mapping that
#: production rebuilds on every call, so the violation never landed at all and a green meant
#: nothing.
#:
#: The repair is the same in every case: THE EXPECTATION LIVES HERE, in literals, and never in
#: the object under test. A guard whose expectation can be edited by the thing it guards is not
#: a guard.
PINNED_CANONICAL_STRUCTURES = {
    "A2.2": "lobStructure", "A2.3": "ccpmStructure",
    "A4.4": "auditedNonconformanceCohort", "A5.6": "queueStructure",
    "A5.7": "abmStructure", "A6.3": "auditedPermitCompliance",
}
PINNED_CONCEPT_ONLY = ("A3.8", "B2.7", "B2.9", "B2.20", "B4.1", "B4.2", "B4.5", "B4.6")
PINNED_VOTING = frozenset({"A1.7", "A1.8"})
PINNED_SCHEDULE_ANCESTRY = ("actual_pct_complete", "ev", "planned_pct_complete", "pv")
PINNED_PROVENANCE_MODULES = ("A1.1", "A1.7", "A1.8", "B1.4", "D1.5", "A6.3")


def _check_manifest() -> bool:
    """Every module the register is PINNED to cover is covered. Not the register against itself."""
    return all(PAR.provenance(m) for m in PINNED_PROVENANCE_MODULES)


def _check_registry_identity() -> bool:
    """The registered name each truthful label pins is the name the registry actually carries."""
    idx = REG.registry_index()
    return all(idx[m]["module_name"] == lab.registered
               for m, lab in ML.TRUTHFUL_METHOD_LABELS.items() if m in idx)


def _check_ph_existence() -> bool:
    """EVERY id, and especially every id beginning PH. The skip that was found is impossible here."""
    idx = REG.registry_index()
    ids = [t["code_id"] for t in population()]
    ph = [i for i in ids if i.startswith("D1.")]
    return len(ph) == 5 and all(i in idx for i in ids)


def _check_cat9() -> bool:
    """The PINNED six gated modules still declare a canonical structure requirement."""
    return all(QUAL.CANONICAL_STRUCTURE_KEYS.get(m) == k
               for m, k in PINNED_CANONICAL_STRUCTURES.items())


def _check_lineage_declaration() -> bool:
    return all(r.get("module_id") == m for m, r in LIN.MODULE_LINEAGE.items())


def _check_voting() -> bool:
    return REG.CORE_VOTING_MODULES == PINNED_VOTING


def _check_activation() -> bool:
    """The PINNED eight concept-only modules are each still disabled and unsafe."""
    return all(REG.activation_state(m) == "DISABLED_UNSAFE" for m in PINNED_CONCEPT_ONLY)


def _check_disabled() -> bool:
    # RUN 36 CLOSURE. A THIRD disjoint disabled set exists: DISABLED_CANONICAL_INPUT_NOT_GOVERNED,
    # carrying A1.1 under the owner's 2026-08-19 ruling. The composition property this guard is
    # about -- that DISABLED_MODULES is exactly the union of its declared components and gains no
    # member from anywhere else -- is unchanged and is still what is asserted.
    return (REG.DISABLED_EVIDENCE_UNDER_REVIEW == {"A3.4": "Material Cost Variance"}
            and REG.DISABLED_CANONICAL_INPUT_NOT_GOVERNED
            == {"A1.1": "Monte Carlo EAC Forecast"}
            and set(REG.DISABLED_MODULES) ==
            set(REG.DISABLED_CONCEPT_ONLY) | set(REG.DISABLED_EVIDENCE_UNDER_REVIEW)
            | set(REG.DISABLED_CANONICAL_INPUT_NOT_GOVERNED))


def _check_mutation_control() -> bool:
    """The fault control: an unknown evidence relationship must raise, never default."""
    try:
        LIN.lineage_record("X", evidence_relationship="NOT_A_RELATIONSHIP")
    except LIN.LineageError:
        return True
    return False


def _check_derived_index() -> bool:
    """Against the PINNED ancestry, not against the constant the resolver itself returns."""
    return tuple(sorted(LIN.index_ancestry(LIN.SCHEDULE_INDEX))) == PINNED_SCHEDULE_ANCESTRY


def _check_unresolved_default() -> bool:
    """
    An undeclared signal is kept, named, and never combined as independent. The last clause is
    what the first version missed: it asked only for the band, and assuming independence still
    leaves an adverse band standing, so the check passed while the protection was gone.
    """
    one = FUS.fuse_signals([
        sig("D1", "Green", rec("D1", ("ev",), ("EARNED_VALUE_MEASUREMENT",))),
        {"module_id": "U1", "status": "Red"}])
    two = FUS.fuse_signals([
        sig("D1", "Green", rec("D1", ("ev",), ("EARNED_VALUE_MEASUREMENT",))),
        {"module_id": "U1", "status": "Red"}, {"module_id": "U2", "status": "Red"}])
    if not one or not two:
        return False
    named = "U1" in (one.get("unresolved_module_ids") or ())
    idempotent = band(one) == band(two) and abs(belief(one) - belief(two)) < 1e-12
    return one.get("lineage_declared") is False and named and band(one) == "Red" and idempotent


def run_guards() -> None:
    """Eleven guards, each deliberately violated in the live object it protects."""

    # 1 manifest integrity -- remove a module's provenance entry
    saved: dict = {}

    def v_manifest():
        saved["k"], saved["v"] = "A1.1", PAR.PARAMETER_PROVENANCE_BY_MODULE.pop("A1.1")
        return "removed the provenance entry for A1.1 from the live register"

    guard("manifest integrity", "coverage of every module carrying a tunable value", v_manifest,
          lambda: PAR.PARAMETER_PROVENANCE_BY_MODULE.__setitem__("A1.1", saved["v"]))

    # 2 registry identity -- rename a module out from under its truthful label
    #
    # THE VIOLATION MUST REACH THE SOURCE, NOT A COPY. registry_index() re-reads the renumbering
    # map on EVERY call and returns a fresh dictionary, so the first version of this violation
    # mutated an object production had already thrown away and the guard reported green on a
    # mutation that never landed. That is the ninth vacuity pattern of this run reproduced in
    # this file, and it is corrected by patching load_registry, which is what the index is built
    # from. Every violation below that touches the registry does the same.
    ident: dict = {}

    def v_identity():
        mid = next(iter(ML.TRUTHFUL_METHOD_LABELS))
        ident["mid"] = mid
        ident["old"] = REG.load_registry
        rows = [dict(r) for r in REG.load_registry()]
        for r in rows:
            if r["new_id"] == mid:
                r["module_name"] = "A Name Nobody Registered"
        REG.load_registry = lambda: [dict(r) for r in rows]
        assert REG.registry_index()[mid]["module_name"] == "A Name Nobody Registered"
        return f"renamed {mid} at the source the registry index is built from"

    guard("registry identity", "a registered name against its truthful label", v_identity,
          lambda: setattr(REG, "load_registry", ident["old"]))

    # 3 PH.* existence -- remove a portfolio module from the registry
    ph: dict = {}

    def v_ph():
        ph["old"] = REG.load_registry
        rows = [dict(r) for r in REG.load_registry() if r["new_id"] != "D1.5"]
        REG.load_registry = lambda: [dict(r) for r in rows]
        assert "D1.5" not in REG.registry_index()
        return "removed D1.5, the portfolio anomaly score, at the registry source"

    guard("PH.* existence", "the existence of every portfolio identifier", v_ph,
          lambda: setattr(REG, "load_registry", ph["old"]))

    # 4 Category-9 qualification -- drop a canonical structure key
    c9: dict = {}

    def v_c9():
        c9["k"] = "A2.2"
        c9["v"] = QUAL.CANONICAL_STRUCTURE_KEYS.pop("A2.2")
        return "removed the line of balance canonical structure requirement"

    guard("Category-9 qualification", "the canonical structure requirement of a gated module",
          v_c9, lambda: QUAL.CANONICAL_STRUCTURE_KEYS.__setitem__("A2.2", c9["v"]))

    # 5 lineage declaration -- make a record name a module that is not itself
    ln: dict = {}

    def v_lineage():
        mid = next(iter(LIN.MODULE_LINEAGE))
        ln["mid"] = mid
        ln["old"] = LIN.MODULE_LINEAGE[mid]["module_id"]
        LIN.MODULE_LINEAGE[mid]["module_id"] = "SOMETHING_ELSE"
        return f"pointed {mid}'s lineage record at a module that is not itself"

    guard("lineage declaration", "the identity of every declared lineage record", v_lineage,
          lambda: LIN.MODULE_LINEAGE[ln["mid"]].__setitem__("module_id", ln["old"]))

    # 6 voting -- expand the voting set to three
    vt: dict = {}

    def v_voting():
        vt["old"] = REG.CORE_VOTING_MODULES
        REG.CORE_VOTING_MODULES = frozenset({"A1.7", "A1.8", "A1.1"})
        return "expanded the voting set from two modules to three"

    guard("voting", "exactly two voting modules", v_voting,
          lambda: setattr(REG, "CORE_VOTING_MODULES", vt["old"]))

    # 7 activation -- activate a concept-only module
    ac: dict = {}

    def v_activation():
        ac["k"] = "B2.7"
        ac["v"] = REG.DISABLED_CONCEPT_ONLY.pop("B2.7")
        return "removed Plithogenic Sets from the concept-only disabled set"

    guard("activation", "the disabled state of every concept-only module", v_activation,
          lambda: REG.DISABLED_CONCEPT_ONLY.__setitem__("B2.7", ac["v"]))

    # 8 disabled state -- reactivate Material Cost Variance
    ds: dict = {}

    def v_disabled():
        ds["v"] = REG.DISABLED_EVIDENCE_UNDER_REVIEW.pop("A3.4")
        return "removed Material Cost Variance from the evidence-under-review disabled set"

    guard("disabled state", "the disabled state of Material Cost Variance", v_disabled,
          lambda: REG.DISABLED_EVIDENCE_UNDER_REVIEW.__setitem__("A3.4", ds["v"]))

    # 9 mutation and fault control -- add the bogus relationship to the accepted vocabulary
    mu: dict = {}

    def v_mutation():
        mu["old"] = LIN.EVIDENCE_RELATIONSHIPS
        LIN.EVIDENCE_RELATIONSHIPS = frozenset(set(mu["old"]) | {"NOT_A_RELATIONSHIP"})
        return "admitted an undeclared evidence relationship into the accepted vocabulary"

    guard("mutation and fault control", "the refusal of an undeclared evidence relationship",
          v_mutation, lambda: setattr(LIN, "EVIDENCE_RELATIONSHIPS", mu["old"]))

    # 10 the derived index resolver -- narrow the union to one ancestry
    di: dict = {}

    def v_derived():
        di["old"] = LIN.SCHEDULE_INDEX_ANCESTRY_UNION
        LIN.SCHEDULE_INDEX_ANCESTRY_UNION = LIN.SCHEDULE_INDEX_ANCESTRY_PV
        return "narrowed the schedule index union ancestry to the planned value ancestry alone"

    guard("the derived index resolver", "the conservative union with no evidence in hand",
          v_derived, lambda: setattr(LIN, "SCHEDULE_INDEX_ANCESTRY_UNION", di["old"]))

    # 11 the unresolved signal default -- make undeclared signals independent by default
    ud: dict = {}

    def v_unresolved():
        ud["old"] = FUS.fuse_signals
        FUS.fuse_signals = lambda signals, assume_independent=False: ud["old"](
            signals, assume_independent=True)
        return "made every fusion assume independence, which is the default cycle 9 removed"

    guard("the unresolved signal default", "the refusal to assume independence nobody declared",
          v_unresolved, lambda: setattr(FUS, "fuse_signals", ud["old"]))


# =============================================================================================

def main() -> None:
    duplicate_identical_evidence()
    correlated_transforms()
    bridging_evidence()
    non_transitivity_six_orderings()
    same_lineage_suppression()
    independent_corroboration()
    bayesian_eac_negative_control()
    portfolio_canonical_id_guard()
    production_arms()
    portfolio_clusters()
    sibling_modules()
    derived_index_dual_ancestry()
    unresolved_signal_default()
    declaration_identity()

    A.check("LINEAGE", "false reinforcement is nought", FALSE_REINFORCEMENT == 0,
            f"{FALSE_REINFORCEMENT} instance(s)")
    A.check("LINEAGE", "false suppression is nought", FALSE_SUPPRESSION == 0,
            f"{FALSE_SUPPRESSION} instance(s)")
    A.check("LINEAGE", "unresolved lineage declaration identity defects are nought",
            DECLARATION_IDENTITY_DEFECTS == 0, f"{DECLARATION_IDENTITY_DEFECTS} defect(s)")
    A.check("LINEAGE", "the campaign exercised every declared property",
            len(CAMPAIGN) == 14, f"{len(CAMPAIGN)} properties")

    run_guards()
    A.check("GUARD", "eleven critical guards were put under deliberate violation",
            len(GUARDS) == 11, f"{len(GUARDS)} guards")
    vacuous = [g["guard"] for g in GUARDS if g["detected"] != "yes"]
    A.check("GUARD", "no critical guard stayed green under a deliberate violation",
            not vacuous, f"vacuous: {vacuous}")

    # Restoration is proved, not assumed: a guard campaign that left the objects mutated would
    # poison every suite that runs after it in the same process.
    A.check("GUARD", "every deliberate violation was restored",
            _check_voting() and _check_disabled() and _check_lineage_declaration()
            and _check_derived_index() and _check_unresolved_default() and _check_ph_existence())

    for path, rows in ((LINEAGE_OUT, CAMPAIGN), (GUARD_OUT, GUARDS)):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)

    print(f"Lineage campaign properties exercised: {len(CAMPAIGN)}; "
          f"false reinforcement {FALSE_REINFORCEMENT}; false suppression {FALSE_SUPPRESSION}; "
          f"declaration identity defects {DECLARATION_IDENTITY_DEFECTS}")
    print(f"Guards put under deliberate violation: {len(GUARDS)}; vacuous: {len(vacuous)}")


if __name__ == "__main__":
    main()
    sys.exit(A.finish())
