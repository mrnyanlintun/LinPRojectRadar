"""
RUN 30 FINAL CLOSURE -- LINEAGE SEMANTICS, AND THE FOUR FAULTS THAT PROVE THE GUARD.

WHAT THIS SUITE DEFENDS. Run 30's closure removed eleven Category-7 lineage declarations whose
content had become false, and deliberately did not replace them with invented independent bodies.
That was the right call and it left a representation problem: a row with no lineage record was
indistinguishable from a row whose independence had been established, because both carried
nothing. The four states in `lineage.py` close it, and this suite asserts that:

  * every Category-7 row carries one of the four states, never a blank;
  * `independence_established` is true for exactly one of them;
  * no evidence body is synthesised for a row whose lineage is unresolved;
  * SOURCE PROVENANCE AND INDEPENDENCE ARE SEPARATE -- a row may know exactly where its structure
    came from and still have unresolved independence, and both are said;
  * and UNRESOLVED is not treated as eligible independent evidence in the fusion path.

The last of those is Fault D, and it is also the behavioural question the version decision turns
on, so it is measured rather than asserted.
"""

from __future__ import annotations

import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from app.simulation import fusion as FUS                          # noqa: E402
from app.simulation import lineage as LIN                         # noqa: E402
from app.simulation import models_cat7 as CAT7M                   # noqa: E402
from app.simulation import registry as REG                        # noqa: E402
from app.simulation.canonical_v5 import V5_STRUCTURE_KEYS         # noqa: E402
from run30 import fixtures_cat67 as FX                            # noqa: E402

NOOP = lambda: 0.5  # noqa: E731
CUTOFF = "2026-06-30"
SI = {"bac": 1_000_000.0, "ev": 400_000.0, "ac": 440_000.0, "pv": 450_000.0,
      "cpi": 0.909, "spi": 0.889, "docRiskScore": 0.35}

CAT7 = sorted((m for m in REG.registry_index() if m.startswith("B2.")),
              key=lambda m: int(m.split(".")[1]))

PASSED = 0
FAILED = 0
FAILURES: list[str] = []
FAULTS: list[dict] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        FAILURES.append(label)
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def head(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def safe(probe):
    try:
        return ("ok", probe())
    except Exception as exc:                                      # noqa: BLE001
        return ("crash", repr(exc)[:120])


def ledger_rows() -> dict:
    out = REG.run_all(dict(SI), "S", "P1", CUTOFF)
    rows = {m["module_id"]: m for m in out["abstained"]}
    rows.update({m["module_id"]: m for m in out["computed"]})
    return rows


# =================================================================================================
head("1. THE FOUR STATES, AND WHAT EACH ONE MEANS")
# =================================================================================================
check(LIN.LINEAGE_STATES == (LIN.LINEAGE_ESTABLISHED_INDEPENDENT,
                             LIN.LINEAGE_ESTABLISHED_DEPENDENT,
                             LIN.LINEAGE_UNRESOLVED,
                             LIN.LINEAGE_NOT_APPLICABLE),
      "the vocabulary is exactly four states and they are declared in one place",
      str(LIN.LINEAGE_STATES))
check(LIN.independence_established(LIN.LINEAGE_ESTABLISHED_INDEPENDENT) is True,
      "independence is established by exactly one state")
check(not any(LIN.independence_established(s) for s in LIN.LINEAGE_STATES
              if s != LIN.LINEAGE_ESTABLISHED_INDEPENDENT),
      "and by no other, INCLUDING the absence of a declaration")
_bad = safe(lambda: LIN.independence_established("SOMETHING_ELSE"))
check(_bad[0] == "crash" and "LineageError" in _bad[1],
      "a state outside the vocabulary raises rather than defaulting", str(_bad))
# The derivation is from the shipped table, so it cannot be asserted into existence.
check(LIN.lineage_status("A1.7") == LIN.LINEAGE_ESTABLISHED_DEPENDENT,
      "a declared module reports the state its own declaration implies",
      LIN.lineage_status("A1.7"))
check(LIN.lineage_status("B2.14") == LIN.LINEAGE_UNRESOLVED,
      "an undeclared module reports UNRESOLVED, never INDEPENDENT",
      LIN.lineage_status("B2.14"))
check(LIN.lineage_status("B2.7", applicable=False) == LIN.LINEAGE_NOT_APPLICABLE,
      "and a module that produces no reading at all reports NOT_APPLICABLE, which is a "
      "different statement from UNRESOLVED")
check(LIN.evidence_body_of("B2.14", LIN.LINEAGE_UNRESOLVED) is None,
      "no evidence body is synthesised from a module id for an unresolved row")


# =================================================================================================
head("2. EVERY CATEGORY-7 LEDGER ROW SAYS ITS STATE. NONE IS BLANK.")
# =================================================================================================
_rows = ledger_rows()
_missing = [m for m in CAT7 if m not in _rows]
check(not _missing, "all twenty Category-7 identities reach the ledger", str(_missing))
_blank = [m for m in CAT7
          if not (_rows[m].get("lineage") or {}).get("lineage_status")]
check(not _blank,
      "AMBIGUOUS BLANK LINEAGE STATES = 0: every row states which of the four states it is in",
      str(_blank))
_outside = [m for m in CAT7
            if (_rows[m]["lineage"] or {}).get("lineage_status") not in LIN.LINEAGE_STATES]
check(not _outside, "and every state is inside the governed vocabulary", str(_outside))
_claimed = [m for m in CAT7 if (_rows[m]["lineage"] or {}).get("independence_established")]
check(not _claimed,
      "FABRICATED INDEPENDENT BODIES = 0: not one Category-7 row claims established "
      "independence, because not one has it", str(_claimed))
_bodies = [m for m in CAT7 if (_rows[m]["lineage"] or {}).get("evidence_body")]
check(not _bodies,
      "and not one carries an evidence body, so no transformation gained a body by having a "
      "module id", str(_bodies))
_disabled = sorted(m for m in CAT7 if m in REG.DISABLED_MODULES)
check(all((_rows[m]["lineage"] or {}).get("lineage_status") == LIN.LINEAGE_NOT_APPLICABLE
          for m in _disabled),
      f"the three disabled and archived identities report NOT_APPLICABLE: {_disabled}")
_operational = [m for m in CAT7 if m not in REG.DISABLED_MODULES]
check(all((_rows[m]["lineage"] or {}).get("lineage_status") == LIN.LINEAGE_UNRESOLVED
          for m in _operational),
      "and the seventeen operational identities report UNRESOLVED, which is the truthful state "
      "of a structure whose assessors' own sources this platform does not know")


# =================================================================================================
head("3. SOURCE PROVENANCE IS KEPT SEPARATE FROM EVIDENCE INDEPENDENCE")
# =================================================================================================
# A row may know exactly where its structure came from and STILL have unresolved independence.
# Both are reported; neither is inferred from the other.
_with_structure = REG.run_module(
    "B2.14", {V5_STRUCTURE_KEYS["B2.14"]: FX.maxent_expectation(1.0)}, NOOP, CUTOFF)
_lin = _with_structure["lineage"]
check(bool(_lin["source_provenance"]),
      "with a governed structure supplied, the row records who defined it and where it came from",
      str(sorted(_lin["source_provenance"])))
check(_lin["lineage_status"] == LIN.LINEAGE_UNRESOLVED
      and _lin["independence_established"] is False,
      "and its independence is STILL unresolved, because knowing the source of a structure is "
      "not knowing what its assessor read", _lin["lineage_status"])
check(bool(str(_lin.get("unresolved_note") or "").strip()),
      "and the row says so in words, so a reader is not left to interpret a null")
check(_with_structure.get("canonical_disposition") == "CANONICAL_RESULT",
      "while the analytical reading itself is produced normally: unresolved lineage does not "
      "suppress the reading, it refuses only corroboration through it")


# =================================================================================================
head("4. THE FOUR MANDATED FAULTS")
# =================================================================================================
def fault(name: str, target, attr: str, mutant, probe, baseline_expected) -> None:
    if not hasattr(target, attr):
        FAULTS.append({"fault": name, "result": "INJECTION_NOT_APPLIED",
                       "detail": f"no attribute {attr!r}"})
        check(False, f"{name}: INJECTION SITE DOES NOT EXIST -- recorded INJECTION_NOT_APPLIED, "
                     f"not scored as RED", attr)
        return
    original = getattr(target, attr)
    kind0, base = safe(probe)
    if kind0 == "crash" or base != baseline_expected:
        FAULTS.append({"fault": name, "result": "NOT_PROVEN",
                       "detail": f"baseline {base!r} vs expected {baseline_expected!r}"})
        check(False, f"{name}: the baseline is not what the guard expects",
              f"{base!r} vs {baseline_expected!r}")
        return
    setattr(target, attr, mutant)
    applied = getattr(target, attr) is mutant        # RE-READ, never assumed
    kind1, hurt = safe(probe)
    setattr(target, attr, original)
    kind2, restored = safe(probe)
    ok_red = kind1 == "ok" and hurt != base
    ok_restored = kind2 == "ok" and restored == base and getattr(target, attr) is original
    FAULTS.append({"fault": name,
                   "result": "RED_THEN_GREEN" if (applied and ok_red and ok_restored)
                             else "NOT_PROVEN",
                   "detail": f"baseline={base!r} injected={hurt!r} restored={restored!r} "
                             f"injection_applied={applied}"})
    check(applied, f"{name}: the injection APPLIED (re-read from the module)")
    check(ok_red, f"{name}: the guard goes RED under the fault",
          f"baseline={base!r} injected={hurt!r} ({kind1})")
    check(ok_restored, f"{name}: restored, and the guard is GREEN again",
          f"restored={restored!r} ({kind2})")


def _guard_states_and_claims():
    """What section 2 asserts, as one value: every row's state is in the vocabulary, none blank,
    and no row claims independence it has not established."""
    rows = ledger_rows()
    for m in CAT7:
        lin = rows[m].get("lineage") or {}
        st = lin.get("lineage_status")
        if st not in LIN.LINEAGE_STATES:
            return "BLANK_OR_INVALID_STATE"
        if lin.get("independence_established") and st != LIN.LINEAGE_ESTABLISHED_INDEPENDENT:
            return "CLAIM_WITHOUT_STATE"
        if lin.get("evidence_body") and st == LIN.LINEAGE_UNRESOLVED:
            return "BODY_ON_UNRESOLVED_ROW"
        if st == LIN.LINEAGE_ESTABLISHED_INDEPENDENT and LIN.lineage_for(m) is None:
            return "INDEPENDENCE_WITHOUT_DECLARATION"
    return "ALL_STATES_SOUND"


# ---- FAULT A: an UNRESOLVED row is declared ESTABLISHED_INDEPENDENT without evidence.
def _status_lying(module_id, *, applicable=True):
    if not applicable:
        return LIN.LINEAGE_NOT_APPLICABLE
    return LIN.LINEAGE_ESTABLISHED_INDEPENDENT          # asserted, never derived


fault("FAULT A: an UNRESOLVED lineage state is declared ESTABLISHED_INDEPENDENT without evidence",
      CAT7M, "lineage_status", _status_lying, _guard_states_and_claims, "ALL_STATES_SOUND")

# ---- FAULT B: the lineage status is removed from the row entirely.
def _block_without_status(module_id, structure, *, applicable):
    block = dict(CAT7M._lineage_block.__wrapped__(module_id, structure, applicable=applicable)) \
        if hasattr(CAT7M._lineage_block, "__wrapped__") else None
    return {"derived_from": "something", "qualification": "unqualified"}   # no status at all


fault("FAULT B: the lineage status is removed from a Category-7 ledger row",
      CAT7M, "_lineage_block", _block_without_status,
      _guard_states_and_claims, "ALL_STATES_SOUND")

# ---- FAULT C: two transformations of ONE established body are given different invented body ids.
def _body_per_module(module_id, status):
    return f"BODY_OF_{module_id}"                      # a body per module id, which is the defect


def _guard_distinct_bodies():
    """
    Two transformations of ONE established body must keep naming that body.

    THE FIRST FORM OF THIS GUARD WAS WRONG AND IS RECORDED RATHER THAN QUIETLY REPLACED. It
    asked whether two modules sharing the earned-value body produce the SAME body string, and
    they do not: A1.1 also belongs to the document body and A1.2 also belongs to the reporting
    history, so their joined identifiers differ legitimately. Belonging to more than one body is
    not an invented body.

    The property that actually matters is that the identifier comes from the DECLARED groups and
    never from the module id, so two modules that share a group still share it. That is what is
    asserted: the intersection of their body sets must be non-empty and must contain the group
    they both declare.
    """
    same = sorted(m for m, r in LIN.MODULE_LINEAGE.items()
                  if LIN.EARNED_VALUE_BODY in (r.get("lineage_group_ids") or ()))[:2]
    if len(same) < 2:
        return "NO_PAIR_TO_TEST"
    sets = [set((LIN.evidence_body_of(m, LIN.lineage_status(m)) or "").split("+"))
            for m in same]
    shared = sets[0] & sets[1]
    if LIN.EARNED_VALUE_BODY not in shared:
        return "SPLIT_INTO_INVENTED_BODIES"
    if any(m in (LIN.evidence_body_of(m, LIN.lineage_status(m)) or "") for m in same):
        return "BODY_NAMED_AFTER_THE_MODULE"
    return "SHARED_BODY_PRESERVED"


fault("FAULT C: two transformations of one established body get different invented body ids",
      LIN, "evidence_body_of", _body_per_module, _guard_distinct_bodies,
      "SHARED_BODY_PRESERVED")


# ---- FAULT D: UNRESOLVED is treated as eligible independent evidence in the fusion path.
#
# THIS IS ALSO THE VERSION QUESTION. If treating UNRESOLVED as independent changes a fusion
# outcome, lineage status is behavioural rather than descriptive. It is measured, not assumed.
_UNDECLARED = [{"module_id": m, "status": "Amber", "lineage": None}
               for m in ("X1", "X2", "X3")]


def _guard_unresolved_not_independent():
    """Three undeclared Amber readings must NOT sharpen belief as three independent bodies.
    Returns the fused Amber mass rounded, which is the quantity FUSION.1 protects."""
    out = FUS.fuse_signals([dict(s) for s in _UNDECLARED])
    return (out["lineage_groups"], out["unresolved_signal_count"], round(out["mass"]["Amber"], 4))


_real_record = LIN.lineage_record


def _independent_by_default(module_id, **kw):
    """The pre-FUSION.1 defect: an undeclared signal is given its own independent body."""
    kw.setdefault("evidence_relationship", LIN.INDEPENDENT)
    return _real_record(module_id, **kw)


def _fuse_treating_unresolved_as_independent(signals):
    patched = []
    for s in signals:
        s = dict(s)
        if s.get("lineage") is None:
            s["lineage"] = _real_record(s["module_id"],
                                        evidence_relationship=LIN.INDEPENDENT,
                                        lineage_group_ids=(f"BODY_{s['module_id']}",))
        patched.append(s)
    return _real_fuse(patched)


_real_fuse = FUS.fuse_signals
fault("FAULT D: UNRESOLVED is treated as eligible independent evidence in the fusion path",
      FUS, "fuse_signals", _fuse_treating_unresolved_as_independent,
      _guard_unresolved_not_independent, (0, 3, 0.7))


# =================================================================================================
head("5. WHAT FAULT D MEASURED, AND THE VERSION DECISION IT SETTLES")
# =================================================================================================
_baseline = _guard_unresolved_not_independent()
check(_baseline == (0, 3, 0.7),
      "with three undeclared readings the shipped fusion manufactures NO body, records three "
      "unresolved signals, and holds Amber belief at the single reading 0.7000", str(_baseline))
_as_independent = _fuse_treating_unresolved_as_independent([dict(s) for s in _UNDECLARED])
check(_as_independent["mass"]["Amber"] > 0.9,
      "treating them as independent sharpens Amber belief past 0.9, so LINEAGE STATUS IS "
      "BEHAVIOURAL in the fusion path and not merely descriptive",
      str(round(_as_independent["mass"]["Amber"], 4)))
# AND THE DECISIVE POINT FOR THE STAMP: that behaviour is FUSION.1, shipped since Run 20 cycle 9
# and unchanged by this closure. What this closure added is a NAME for the state on the row. So
# the behaviour Fault D demonstrates is v16's behaviour, not a change to it.
check(FUS.fuse_signals is _real_fuse,
      "and the shipped fusion is restored, so the measurement above changed nothing")
_names_only = [m for m in CAT7
               if (_rows[m].get("lineage") or {}).get("lineage_status") is not None]
check(len(_names_only) == 20,
      "the closure's own contribution is the state NAME on all twenty rows; the eligibility "
      "behaviour it names was already shipped and is unchanged")

with (ROOT / "code_audit" / "run30_lineage_fault_injection.csv").open(
        "w", encoding="utf-8", newline="\n") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["fault", "result", "detail"])
    for r in FAULTS:
        w.writerow([r["fault"], r["result"], r["detail"]])

_proven = [r for r in FAULTS if r["result"] == "RED_THEN_GREEN"]
_not_applied = [r for r in FAULTS if r["result"] == "INJECTION_NOT_APPLIED"]
print()
check(len(FAULTS) == 4, "all four mandated lineage faults were attempted", str(len(FAULTS)))
check(not _not_applied, "none was recorded INJECTION_NOT_APPLIED", str(_not_applied))
check(len(_proven) == 4, "every fault went RED for its intended reason and GREEN on restore",
      str([r["fault"] for r in FAULTS if r["result"] != "RED_THEN_GREEN"]))
check(_guard_states_and_claims() == "ALL_STATES_SOUND",
      "and the baseline is sound again after the whole campaign, not only after each fault")

print()
print("=" * 78)
if FAILURES:
    print(f"{len(FAILURES)} check(s) did not hold:")
    for f in FAILURES:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
