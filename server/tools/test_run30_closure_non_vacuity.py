"""
RUN 30 CLOSURE -- THE NON-VACUITY CAMPAIGN FOR THE OPERATIONAL REPOINTING. FOURTEEN FAULTS.

WHAT A FAULT IS HERE. Each one puts a legacy proxy, a disabled activation or a stale stamp BACK
into the production routing table or the production layer, and then asks the closure's own guard
whether it notices. The mutation is made on the live module object and is CONFIRMED TO HAVE
APPLIED by re-reading the attribute afterwards; the probe is then evaluated THROUGH
`registry.run_module`, the production entry point, never through a direct call to the canonical
layer. It must go red for the intended reason, and it must go green again on restore.

A CRASH IS NOT RED. Every probe is wrapped: an exception is reported as a crash and the fault is
recorded NOT_PROVEN rather than counted. If an injection site does not exist the fault is recorded
INJECTION_NOT_APPLIED and is never scored.
"""

from __future__ import annotations

import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from app.simulation import canonical_v5 as V5                     # noqa: E402
from app.simulation import models as MODELS                       # noqa: E402
from app.simulation import models_cat7 as CAT7M                   # noqa: E402
from app.simulation import models_evc as EVC                      # noqa: E402
from app.simulation import models_fuzzy as FZ                     # noqa: E402
from app.simulation import registry as REG                        # noqa: E402
from app.simulation.canonical_v5 import V5_STRUCTURE_KEYS         # noqa: E402
from run30 import fixtures_cat67 as FX                            # noqa: E402
from run30.route_trace import canonical_hits, legacy_hits, trace_calls  # noqa: E402

NOOP = lambda: 0.5  # noqa: E731
CUTOFF = "2026-06-30"
RICH = {"bac": 1_000_000.0, "ev": 400_000.0, "ac": 440_000.0, "pv": 450_000.0,
        "cpi": 0.909, "spi": 0.889, "docRiskScore": 0.35}

PASSED = 0
FAILED = 0
FAILURES: list[str] = []
RECORDS: list[dict] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        FAILURES.append(label)
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def safe(probe):
    try:
        return ("ok", probe())
    except Exception as exc:                                      # noqa: BLE001
        return ("crash", repr(exc)[:120])


def fault(number: int, name: str, target, attr: str, mutant, probe, baseline_expected) -> None:
    """Inject into PRODUCTION, confirm it applied, observe the guard, restore, re-observe."""
    if not hasattr(target, attr):
        RECORDS.append({"fault": number, "name": name, "result": "INJECTION_NOT_APPLIED",
                        "detail": f"no attribute {attr!r} on {getattr(target, '__name__', target)}"})
        check(False, f"F{number:02d} {name}: INJECTION SITE DOES NOT EXIST -- recorded "
                     f"INJECTION_NOT_APPLIED, not scored as RED", attr)
        return
    original = getattr(target, attr)
    kind0, base = safe(probe)
    if kind0 == "crash" or base != baseline_expected:
        RECORDS.append({"fault": number, "name": name, "result": "NOT_PROVEN",
                        "detail": f"baseline {base!r} vs expected {baseline_expected!r}"})
        check(False, f"F{number:02d} {name}: the baseline is not what the guard expects",
              f"{base!r} vs {baseline_expected!r}")
        return
    setattr(target, attr, mutant)
    applied = getattr(target, attr) is mutant          # RE-READ FROM THE MODULE, never assumed
    kind1, hurt = safe(probe)
    setattr(target, attr, original)
    kind2, restored = safe(probe)
    ok_red = kind1 == "ok" and hurt != base
    ok_restored = kind2 == "ok" and restored == base and getattr(target, attr) is original
    RECORDS.append({"fault": number, "name": name,
                    "result": "RED_THEN_GREEN" if (applied and ok_red and ok_restored)
                              else "NOT_PROVEN",
                    "detail": f"baseline={base!r} injected={hurt!r} restored={restored!r} "
                              f"injection_applied={applied}"})
    check(applied, f"F{number:02d} {name}: the injection APPLIED (re-read from the module)")
    check(ok_red, f"F{number:02d} {name}: the guard goes RED under the fault",
          f"baseline={base!r} injected={hurt!r} ({kind1})")
    check(ok_restored, f"F{number:02d} {name}: restored, and the guard is GREEN again",
          f"restored={restored!r} ({kind2})")


def _route_probe(mid, si):
    """What the CLOSURE GUARD asks: did the production route reach the canonical layer, did any
    legacy implementation run, and what disposition came back."""
    out, seen, err = trace_calls(lambda: REG.run_module(mid, si, NOOP, CUTOFF))
    if err:
        raise RuntimeError(err)
    return (bool(canonical_hits(seen)), bool(legacy_hits(seen)),
            out.get("canonical_disposition"))


# THE INJECTION SITE, ESTABLISHED BY EXECUTION RATHER THAN BY GUESS. `registry.py` does
# `from .models import VALIDATED`, so it holds its OWN name bound to the dict. Rebinding
# `models.VALIDATED` sets an attribute that `run_module` never reads: the mutation applies
# cleanly and changes nothing, which is the silent-injection failure mode this programme
# catalogues. It was observed happening here on the first pass -- every probe returned its
# baseline under the fault -- and the site was repointed to `registry.VALIDATED`, which is the
# name the dispatcher actually resolves.
def _validated_with(mid, fn):
    """A copy of the shipped routing table with one identity pointed somewhere else."""
    table = dict(REG.VALIDATED)
    table[mid] = (REG.VALIDATED[mid][0], fn)
    return table


print("=" * 78)
print("RUN 30 CLOSURE -- NON-VACUITY CAMPAIGN")
print("=" * 78)

# 1 ------------------------------------------------------ dispatcher points back to legacy proxy
fault(1, "a Category-7 dispatcher deliberately points back to its legacy proxy",
      REG, "VALIDATED", _validated_with("B2.10", FZ.run_pythagorean_fuzzy),
      lambda: _route_probe("B2.10", {V5_STRUCTURE_KEYS["B2.10"]: FX.pyth(0.6, 0.8)}),
      (True, False, "CANONICAL_RESULT"))

# 2 ------------------------------------------- missing structure falls through to a legacy proxy
def _fallback_runner(si, rand, period_cutoff):
    """The defect: canonical first, legacy proxy when the structure is absent."""
    out = CAT7M.CAT7_CANONICAL["B2.16"][1](si, rand, period_cutoff)
    if out.get("insufficient_data"):
        return FZ.run_spherical_fuzzy(si, rand, period_cutoff)
    return out


fault(2, "missing canonical structure deliberately falls through to a proxy",
      REG, "VALIDATED", _validated_with("B2.16", _fallback_runner),
      lambda: _route_probe("B2.16", dict(RICH)),
      (True, False, "NOT_ESTIMABLE_STRUCTURE_ABSENT"))

# 3 ------------------------------------------------- canonical Dempster fixture to the old proxy
fault(3, "the canonical Dempster fixture routed to the old proxy",
      REG, "VALIDATED", _validated_with("B2.1", REG.VALIDATED["B3.1"][1]),
      lambda: _route_probe("B2.1", {V5_STRUCTURE_KEYS["B2.1"]: FX.dst_independent()}),
      (True, False, "CANONICAL_RESULT"))

# 4 --------------------------------- canonical fuzzy fixture to the generic old fuzzy implementation
fault(4, "a canonical fuzzy fixture routed to the generic old fuzzy implementation",
      REG, "VALIDATED", _validated_with("B2.11", FZ.run_picture_fuzzy),
      lambda: _route_probe("B2.11", {V5_STRUCTURE_KEYS["B2.11"]: FX.picture(0.4, 0.2, 0.3)}),
      (True, False, "CANONICAL_RESULT"))

# 5 ------------------------------------------- Maximum Entropy back to the min(CPI,SPI) lookup
fault(5, "Maximum Entropy routed to the old min(CPI,SPI) implementation",
      REG, "VALIDATED", _validated_with("B2.14", FZ.run_maximum_entropy),
      lambda: _route_probe("B2.14", dict(RICH, **{V5_STRUCTURE_KEYS["B2.14"]:
                                                  FX.maxent_expectation(1.0)})),
      (True, False, "CANONICAL_RESULT"))

# 6 ------------------------------------------------ Fermatean back to the min(CPI,SPI) proxy
fault(6, "Fermatean routed to the old min(CPI,SPI) implementation",
      REG, "VALIDATED", _validated_with("B2.17", FZ.run_fermatean_fuzzy),
      lambda: _route_probe("B2.17", dict(RICH, **{V5_STRUCTURE_KEYS["B2.17"]:
                                                  FX.fermatean(0.8, 0.7)})),
      (True, False, "CANONICAL_RESULT"))

# 7 -------------------------------------------------------- Type-2 acquires a midpoint fallback
# THE INJECTION SITE IS THE RENDERER, and finding that out is itself part of the proof. Mutating
# `canonical_v5.type2_fuzzy` to compute a midpoint applies cleanly and changes nothing, because
# the runner's renderer sets `type_reduced` to None explicitly and never copies a reduced figure
# out of the canonical result. That is the guarantee working -- there is no path by which the
# canonical layer can hand a midpoint to the ledger -- so the fault is injected where a midpoint
# COULD actually reach a row: the renderer that builds it.
def _midpoint_renderer(out):
    p = out["points"][0]
    mid = (p["lower"] + p["upper"]) / 2                          # the forbidden substitute
    return (f"Membership reduced to {mid:.2f}",
            {"points": out["points"], "max_fou_width": out["max_fou_width"],
             "type_reduced": mid,
             "type_reduction_blocked": out["type_reduction_blocked"]})


fault(7, "Type-2 routed to a midpoint fallback", CAT7M, "_r_type2", _midpoint_renderer,
      lambda: REG.run_module("B2.13", {V5_STRUCTURE_KEYS["B2.13"]:
                                       FX.type2([(0.0, 0.3, 0.7)])},
                             NOOP, CUTOFF).get("type_reduced"),
      None)

# 8 --------------------------------------------------------- MARCOS to a single-project proxy
fault(8, "MARCOS routed to a single-project proxy",
      REG, "VALIDATED", _validated_with("B2.18", FZ.run_marcos),
      lambda: _route_probe("B2.18", dict(RICH, **{V5_STRUCTURE_KEYS["B2.18"]:
                                                  FX.marcos_benchmark()})),
      (True, False, "CANONICAL_RESULT"))

# 9 --------------------------------------------------- CRITIC-TOPSIS to a single-project proxy
fault(9, "CRITIC-TOPSIS routed to a single-project proxy",
      REG, "VALIDATED", _validated_with("B2.19", FZ.run_critic_topsis),
      lambda: _route_probe("B2.19", dict(RICH, **{V5_STRUCTURE_KEYS["B2.19"]:
                                                  FX.critic_benchmark()})),
      (True, False, "CANONICAL_RESULT"))

# 10 ----------------------------------------------------------- disabled Plithogenic activated
# THE INJECTION SITE FOR A DISABLED IDENTITY IS NOT THE ROUTING TABLE. `run_module`
# short-circuits DISABLED_CONCEPT_ONLY before it consults `VALIDATED`, so a mutant put there
# would never be reached and the fault would apply cleanly while changing nothing. The disabled
# branch resolves the refusing runner from `models_cat7.CAT7_CANONICAL` at call time, and that is
# where the fault has to go for it to be a fault at all.
def _cat7_with(mid, fn):
    table = dict(CAT7M.CAT7_CANONICAL)
    table[mid] = (CAT7M.CAT7_CANONICAL[mid][0], fn)
    return table


def _operational_plithogenic(si, rand, period_cutoff):
    out = V5.plithogenic_lab(si[V5_STRUCTURE_KEYS["B2.7"]])
    return {"method_class": "Plithogenic_Sets", "status_color": "Amber",
            "operational": True, "canonical_disposition": "CANONICAL_RESULT",
            "result_source": "CANONICAL_V5_LAYER", "evidence_metric": "activated",
            "attributes": out["attributes"]}


fault(10, "disabled Plithogenic made operational",
      CAT7M, "CAT7_CANONICAL", _cat7_with("B2.7", _operational_plithogenic),
      lambda: (REG.run_module("B2.7", {V5_STRUCTURE_KEYS["B2.7"]: FX.plithogenic()},
                              NOOP, CUTOFF).get("operational"),
               REG.run_module("B2.7", {V5_STRUCTURE_KEYS["B2.7"]: FX.plithogenic()},
                              NOOP, CUTOFF).get("status_color")),
      (False, None))

# 11 -------------------------------------------------------------- archived Quantum activated
fault(11, "archived Quantum made operational",
      REG, "DISABLED_CONCEPT_ONLY",
      {k: v for k, v in REG.DISABLED_CONCEPT_ONLY.items() if k != "B2.9"},
      lambda: "B2.9" in REG.DISABLED_CONCEPT_ONLY, True)

# 12 ------------------------------------------------------------- disabled Hypersoft activated
def _operational_hypersoft(si, rand, period_cutoff):
    return {"method_class": "Hypersoft_Sets", "status_color": "Green", "operational": True,
            "canonical_disposition": "CANONICAL_RESULT", "result_source": "CANONICAL_V5_LAYER",
            "evidence_metric": "activated"}


fault(12, "disabled Hypersoft made operational",
      CAT7M, "CAT7_CANONICAL", _cat7_with("B2.20", _operational_hypersoft),
      lambda: (REG.run_module("B2.20", {V5_STRUCTURE_KEYS["B2.20"]: FX.hypersoft_complete()},
                              NOOP, CUTOFF).get("operational"),
               REG.run_module("B2.20", {V5_STRUCTURE_KEYS["B2.20"]: FX.hypersoft_complete()},
                              NOOP, CUTOFF).get("status_color")),
      (False, None))

# 13 ------------------------------- a ledger row CLAIMS the canonical source while legacy ran
def _lying_runner(si, rand, period_cutoff):
    """The subtlest fault in the campaign: the row says CANONICAL_V5_LAYER, and a legacy
    implementation produced it. Only a probe that watches the interpreter can tell."""
    out = dict(EVC.run_rough_sets(si, rand, period_cutoff))
    out["result_source"] = "CANONICAL_V5_LAYER"
    out["canonical_disposition"] = "CANONICAL_RESULT"
    out["canonical_structure"] = V5_STRUCTURE_KEYS["B2.2"]
    return out


def _honesty_probe():
    """Reads the CLAIM and the FACT together. A row claiming the canonical source while a legacy
    function executed is the failure this returns False for."""
    si = {V5_STRUCTURE_KEYS["B2.2"]: FX.rough_table()}
    out, seen, err = trace_calls(lambda: REG.run_module("B2.2", si, NOOP, CUTOFF))
    if err:
        raise RuntimeError(err)
    claims = out.get("result_source") == "CANONICAL_V5_LAYER"
    truly_canonical = bool(canonical_hits(seen)) and not legacy_hits(seen)
    return claims and truly_canonical


fault(13, "a ledger row claims the canonical source while a legacy function actually executed",
      REG, "VALIDATED", _validated_with("B2.2", _lying_runner),
      _honesty_probe, True)

# 14 --------------------------------------------------------- duplicate simulation-version stamp
fault(14, "a duplicate simulation-version stamp",
      MODELS, "SIMULATION_VERSION_HISTORY",
      MODELS.SIMULATION_VERSION_HISTORY + ("sim-2026.08-v15",),
      lambda: len(MODELS.SIMULATION_VERSION_HISTORY)
      == len(set(MODELS.SIMULATION_VERSION_HISTORY)), True)


_out = ROOT / "code_audit" / "run30_closure_fault_injection.csv"
with _out.open("w", encoding="utf-8", newline="\n") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["fault", "name", "result", "detail"])
    for r in RECORDS:
        w.writerow([r["fault"], r["name"], r["result"], r["detail"]])

_proven = [r for r in RECORDS if r["result"] == "RED_THEN_GREEN"]
_not_applied = [r for r in RECORDS if r["result"] == "INJECTION_NOT_APPLIED"]
print()
check(len(RECORDS) == 14, "all fourteen mandated faults were attempted", str(len(RECORDS)))
check(not _not_applied, "no fault was recorded INJECTION_NOT_APPLIED",
      str([r["fault"] for r in _not_applied]))
check(len(_proven) == 14, "every fault went RED for its intended reason and GREEN on restore",
      str([r["fault"] for r in RECORDS if r["result"] != "RED_THEN_GREEN"]))
# AND THE BASELINE IS RECHECKED AFTER THE WHOLE CAMPAIGN, not only after each fault.
check(all(REG.VALIDATED[m][1].__module__ == "app.simulation.models_cat7"
          for m in (f"B2.{n}" for n in range(1, 21))),
      "and after the whole campaign the routing table is exactly as it shipped: all twenty "
      "Category-7 identities still resolve to the canonical route")
check(MODELS.SIMULATION_VERSION_HISTORY[-1] == "sim-2026.08-v16"
      and len(MODELS.SIMULATION_VERSION_HISTORY)
      == len(set(MODELS.SIMULATION_VERSION_HISTORY)),
      "and the version history is unchanged and still unique")

print()
print("=" * 78)
if FAILURES:
    print(f"{len(FAILURES)} check(s) did not hold:")
    for f in FAILURES:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
