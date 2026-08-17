"""
RUN 30 CLOSURE -- THE CATEGORY-7 OPERATIONAL ROUTE, PROVED THROUGH THE PRODUCTION ENTRY POINT.

THE DEFECT THIS SUITE EXISTS FOR. Run 30's first pass built `canonical_v5.py` -- nineteen governed
structures, the canonical mathematics of every supplied contract, 239 oracle checks against the
contract's own numbers, a 39-fault non-vacuity campaign -- AND PRODUCTION NEVER CALLED ANY OF IT.
Every one of those proofs called the canonical layer directly, and every one of them was green for
the whole time the defect existed.

SO NOTHING HERE CALLS `canonical_v5` TO PROVE ANYTHING. Every claim below is made by executing
`registry.run_module`, the same entry point that builds real module results and ledger rows, and
recording from the INTERPRETER which functions actually ran (`run30/route_trace.py` uses
`sys.setprofile`). A profiler sees what really executed, including through a path nobody thought
to enumerate; a wrapper or a decorator list would not.

AND THE ROUTING TABLE IS READ LIVE FROM `registry.VALIDATED`. It is never restated here. A
hand-written copy of the dispatcher stays green when the dispatcher changes underneath it, which
is the same failure mode as a chart suite asserting against a copied implementation.
"""

from __future__ import annotations

import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from app.simulation import registry as REG                       # noqa: E402
from app.simulation.models import SIMULATION_VERSION            # noqa: E402
from app.simulation import lineage as LIN                        # noqa: E402
from app.simulation.canonical_v5 import V5_STRUCTURE_KEYS        # noqa: E402
from app.simulation.compute import compute_project               # noqa: E402
from run30 import fixtures_cat67 as FX                           # noqa: E402
from run30.route_trace import (                                  # noqa: E402
    LEGACY_PROXY_MODULES, canonical_hits, legacy_hits, trace_calls,
)
from tests.synthetic_fixtures.importers import production_structures as PS  # noqa: E402

NOOP = lambda: 0.5  # noqa: E731
CUTOFF = "2026-06-30"

PASSED = 0
FAILED = 0
FAILURES: list[str] = []
ROWS: list[dict] = []


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


#: The twenty Category-7 identities, derived from the registry index rather than listed.
CAT7 = sorted((m for m in REG.registry_index() if m.startswith("B2.")),
              key=lambda m: int(m.split(".")[1]))

#: The canonical fixture each identity's structure is satisfied by. Research fixtures only; every
#: one carries data_origin = SYNTHETIC_RESEARCH_FIXTURE.
FIXTURES = {
    "B2.1": FX.dst_independent, "B2.2": FX.rough_table,
    "B2.3": lambda: FX.neutrosophic(0.7, 0.2, 0.1),
    "B2.4": lambda: FX.interval(0.4, 0.7),
    "B2.5": lambda: FX.z_number("cost overrun likely", "very likely"),
    "B2.6": lambda: FX.plts([("Green", 0.2), ("Amber", 0.5), ("Red", 0.3)]),
    "B2.7": FX.plithogenic, "B2.8": FX.brb_single_rule,
    "B2.10": lambda: FX.pyth(0.6, 0.8), "B2.11": lambda: FX.picture(0.4, 0.2, 0.3),
    "B2.12": lambda: FX.hesitant([0.2, 0.5, 0.7]),
    "B2.13": lambda: FX.type2([(0.0, 0.3, 0.7)]),
    "B2.14": lambda: FX.maxent_expectation(1.0),
    "B2.15": lambda: FX.possibility({"a": 1.0, "b": 0.4}),
    "B2.16": lambda: FX.spherical(0.6, 0.6, 0.5),
    "B2.17": lambda: FX.fermatean(0.8, 0.7),
    "B2.18": FX.marcos_benchmark, "B2.19": FX.critic_benchmark,
    "B2.20": FX.hypersoft_complete,
}

#: The three that must never compute, whatever they are given.
NON_OPERATIONAL = ("B2.7", "B2.9", "B2.20")


def route(mid: str, si: dict):
    """Execute the PRODUCTION entry point and record what really ran."""
    return trace_calls(lambda: REG.run_module(mid, si, NOOP, CUTOFF))


# =================================================================================================
head("1. THE ROUTING TABLE, READ LIVE, AND NOT ONE LEGACY RESOLUTION AMONG THE TWENTY")
# =================================================================================================
check(len(CAT7) == 20 and len(set(CAT7)) == 20,
      "the Category-7 population is twenty identities, derived from the registry index",
      str(len(CAT7)))
_resolved = {m: REG.VALIDATED[m][1].__module__ for m in CAT7}
_legacy_resolutions = sorted(m for m, mod in _resolved.items() if mod in LEGACY_PROXY_MODULES)
check(not _legacy_resolutions,
      "NO Category-7 production identity resolves to a legacy proxy implementation. The check "
      "enumerates the shipped routing table rather than a list written beside it",
      str(_legacy_resolutions))
check(all(mod == "app.simulation.models_cat7" for mod in _resolved.values()),
      "and all twenty resolve to the canonical Category-7 route",
      str(sorted(set(_resolved.values()))))
# The legacy implementations are PRESERVED. Retired is not deleted.
from app.simulation.models_evc import EVC_EXTENSIONS              # noqa: E402
from app.simulation.models_fuzzy import FUZZY_EXTENSIONS          # noqa: E402
_legacy = {k: v for k, v in {**EVC_EXTENSIONS, **FUZZY_EXTENSIONS}.items()
           if k.startswith("B2.")}
check(len(_legacy) >= 17,
      "and the legacy implementations are still in the tree as the historical record of the "
      "v14/v15 line, reachable from no production route", str(len(_legacy)))
check(all(REG.VALIDATED[m][1] is not fn for m, fn in _legacy.items()),
      "with every one of them a different object from what the registry now dispatches to")


# =================================================================================================
head("2. EXECUTED: WITH ITS STRUCTURE PRESENT, EACH ROUTE REACHES THE CANONICAL LAYER")
# =================================================================================================
for mid in CAT7:
    key = V5_STRUCTURE_KEYS.get(mid)
    si = {key: FIXTURES[mid]()} if mid in FIXTURES and key else {}
    out, seen, err = route(mid, si)
    canon = canonical_hits(seen)
    legacy = legacy_hits(seen)
    disabled = mid in NON_OPERATIONAL
    ROWS.append({
        "module": mid,
        "production_input_shape": key or "(no structure: disabled identity)",
        "defining_structure_present": "yes" if si else "no",
        "parameter_provenance_present": "yes (synthetic research fixture)" if si else "no",
        "production_runner_reached": REG.VALIDATED[mid][1].__module__,
        "canonical_function_reached": ";".join(sorted(
            s.split(":")[1].split(".")[0] for s in canon)) or
            ("the canonical operational gate refused before any mathematics" if disabled
             else "NONE"),
        "legacy_proxy_reached": "yes" if legacy else "no",
        "result": str(out.get("canonical_disposition") or out.get("evidence_metric"))[:80],
        "expected_result_or_disposition":
            "DISABLED or ARCHIVED, no reading" if disabled else "CANONICAL_RESULT",
        "pass_fail": "",
    })
    if disabled:
        ok = (not legacy and out.get("insufficient_data") is True
              and out.get("operational") is False
              and out.get("canonical_disposition") in ("DISABLED", "ARCHIVED")
              and out.get("result_source") == "CANONICAL_V5_LAYER")
        check(ok, f"{mid}: refused by the canonical operational gate BEFORE any mathematics, on a "
                  f"COMPLETE laboratory structure, with no legacy proxy reached",
              f"{out.get('canonical_disposition')} legacy={sorted(legacy)}")
    else:
        ok = (bool(canon) and not legacy
              and out.get("canonical_disposition") == "CANONICAL_RESULT")
        check(ok, f"{mid}: the production route REACHED the canonical layer and no legacy proxy "
                  f"ran", f"canonical={len(canon)} legacy={sorted(legacy)} err={err}")
    ROWS[-1]["pass_fail"] = "PASS" if ok else "FAIL"
check(all(r["legacy_proxy_reached"] == "no" for r in ROWS),
      "legacy proxy reached = 0 of 20, measured by executing every route and profiling the "
      "interpreter", str([r["module"] for r in ROWS if r["legacy_proxy_reached"] != "no"]))


# =================================================================================================
head("3. KNOWN ANSWERS THROUGH THE PRODUCTION DISPATCHER, NOT THROUGH A DIRECT CALL")
# =================================================================================================
# Every expected value is the supplied contract's own number, and it is compared against what the
# PRODUCTION DISPATCHER returned. `canonical_v5` is not called anywhere in this section.
def near(label, got, want, tol=1e-9):
    try:
        ok = abs(float(got) - float(want)) <= tol
    except Exception as exc:                                      # noqa: BLE001
        check(False, label, f"not a number: {exc!r}")
        return
    check(ok, label, f"got {got!r} want {want!r}")


def prod(mid, structure):
    return REG.run_module(mid, {V5_STRUCTURE_KEYS[mid]: structure}, NOOP, CUTOFF)

import math                                                       # noqa: E402

_o = prod("B2.1", FX.dst_independent())
near("7.1 DST through production: m({G}) = .8", _o["belief"]["G"], 0.8)
near("7.1 and the conflict coefficient is 0", _o["conflict"], 0.0)
_o = prod("B2.2", FX.rough_table())
check(_o["lower"] == ["3", "4"] and _o["upper"] == ["1", "2", "3", "4"]
      and _o["boundary"] == ["1", "2"],
      "7.2 Rough Sets through production: Lower {3,4}, Upper {1,2,3,4}, Boundary {1,2}", str(_o))
_o = prod("B2.3", FX.neutrosophic(0.7, 0.2, 0.1))
check((_o["truth"], _o["indeterminacy"], _o["falsity"]) == (0.7, 0.2, 0.1),
      "7.3 Neutrosophic through production: (.7,.2,.1) preserved exactly")
_o2 = prod("B2.3", FX.neutrosophic(0.7, 0.8, 0.1))
check(_o2["indeterminacy"] == 0.8,
      "7.3 and (.7,.8,.1) stays distinct, so indeterminacy is not 1-T-F")
_o = prod("B2.4", FX.interval(0.4, 0.7))
check((_o["membership_lower"], _o["membership_upper"]) == (0.4, 0.7),
      "7.4 Interval Fuzzy through production: [.4,.7] read as given")
_o = prod("B2.6", FX.plts([("Green", 0.2), ("Amber", 0.5), ("Red", 0.3)]))
near("7.6 PLTS through production: the probabilities sum to one",
     sum(t["probability"] for t in _o["terms"]), 1.0)
_o = prod("B2.8", FX.brb_single_rule())
check((_o["belief"]["Green"], _o["belief"]["Amber"], _o["belief"]["Red"]) == (0.7, 0.2, 0.1),
      "7.8 Belief Rule Base through production: one fully activated rule returns (.7,.2,.1)")
_o = prod("B2.10", FX.pyth(0.6, 0.8))
near("7.10 Pythagorean through production: hesitancy 0 for (.6,.8)", _o["hesitancy"], 0.0)
_o = prod("B2.11", FX.picture(0.4, 0.2, 0.3))
near("7.11 Picture through production: refusal .1", _o["refusal"], 0.1)
_o = prod("B2.12", FX.hesitant([0.2, 0.5, 0.7]))
near("7.12 Hesitant through production: score .4666666667", _o["score"], 1.4 / 3)
_o = prod("B2.13", FX.type2([(0.0, 0.3, 0.7)]))
near("7.13 Type-2 through production: footprint width .4", _o["max_fou_width"], 0.4)
check(_o["type_reduced"] is None,
      "7.13 and NO type-reduced figure is produced, so the route did not acquire a midpoint "
      "fallback on the way")
_o = prod("B2.14", FX.maxent_expectation(1.0))
near("7.14 Maximum Entropy through production: H = ln 3", _o["entropy"], math.log(3), 1e-9)
near("7.14 and the supplied expectation is met exactly",
     _o["constraint_expectations"]["mean"], 1.0, 1e-9)
_o = prod("B2.15", FX.possibility({"a": 1.0, "b": 0.4}))
near("7.15 Possibility through production: the degrees sum to 1.4 and that is admissible",
     sum(_o["distribution"].values()), 1.4)
_o = prod("B2.16", FX.spherical(0.6, 0.6, 0.5))
check((_o["membership"], _o["non_membership"], _o["hesitancy"]) == (0.6, 0.6, 0.5),
      "7.16 Spherical through production: the three components stay distinct")
_o = prod("B2.17", FX.fermatean(0.8, 0.7))
check((_o["membership"], _o["non_membership"]) == (0.8, 0.7),
      "7.17 Fermatean through production: (.8,.7) read as given, not shrunk")
_o = prod("B2.18", FX.marcos_benchmark())
check(_o["ranking"] == ["A1", "A3", "A2"],
      "7.18 MARCOS through production: the frozen ranking A1 > A3 > A2", str(_o["ranking"]))
_o = prod("B2.19", FX.critic_benchmark())
check(_o["ranking"] == ["A1", "A4", "A3", "A2"],
      "7.19 CRITIC-TOPSIS through production: the frozen ranking A1 > A4 > A3 > A2",
      str(_o["ranking"]))
near("7.19 and the CRITIC weights sum to one", sum(_o["criterion_weights"].values()), 1.0)

# The blocked operators, reached through production and returning the BLOCKED disposition rather
# than an approximation.
_o = REG.run_module("B2.5", {V5_STRUCTURE_KEYS["B2.5"]:
                             FX.z_number("cost overrun likely", "very likely")}, NOOP, CUTOFF)
check(_o["reduction"] is None and str(_o["reduction_blocked"]).strip(),
      "7.5 Z-numbers through production: the reduction is BLOCKED, not approximated")
_o = REG.run_module("B2.8", {V5_STRUCTURE_KEYS["B2.8"]: FX.brb_two_rules()}, NOOP, CUTOFF)
check(_o.get("canonical_state") == "AGGREGATION_BLOCKED"
      and _o.get("canonical_disposition") == "OPERATOR_BLOCKED",
      "7.8 two activated rules through production: AGGREGATION_BLOCKED, no ER variant chosen",
      str(_o.get("canonical_state")))
_o = REG.run_module("B2.20", {V5_STRUCTURE_KEYS["B2.20"]: FX.hypersoft_missing()},
                    NOOP, CUTOFF)
check(_o.get("operational") is False,
      "7.20 an incomplete Cartesian structure through production produces no operational reading")


# =================================================================================================
head("4. MISSING STRUCTURE NEVER FALLS BACK TO A PROXY")
# =================================================================================================
# GUARD_CAT7_NO_PROXY_FALLBACK_ON_MISSING_CANONICAL_STRUCTURE.
#
# Driven on a RICH flat signalInputs -- every crisp metric the legacy proxies read, and no
# governed structure at all. Under v15 seventeen of these produced a band from those metrics.
RICH = {"bac": 1_000_000.0, "ev": 400_000.0, "ac": 440_000.0, "pv": 450_000.0,
        "cpi": 0.909, "spi": 0.889, "docRiskScore": 0.35,
        "actualPctComplete": 40.0, "plannedPctComplete": 45.0}
_no_fallback = []
for mid in CAT7:
    out, seen, _err = route(mid, dict(RICH))
    if legacy_hits(seen) or out.get("status_color") is not None:
        _no_fallback.append(mid)
check(not _no_fallback,
      "GUARD_CAT7_NO_PROXY_FALLBACK_ON_MISSING_CANONICAL_STRUCTURE: with every crisp metric "
      "present and no governed structure, not one of the twenty reaches a legacy implementation "
      "or emits a band", str(_no_fallback))
_dispositions = {}
for mid in CAT7:
    out = REG.run_module(mid, dict(RICH), NOOP, CUTOFF)
    _dispositions[mid] = out.get("canonical_disposition")
check(all(d in ("NOT_ESTIMABLE_STRUCTURE_ABSENT", "DISABLED", "ARCHIVED")
          for d in _dispositions.values()),
      "and every one of the twenty names its disposition rather than going quiet",
      str(sorted({d for d in _dispositions.values()})))


# =================================================================================================
head("5. THE LEDGER IS THE OPERATIONAL TRUTH SURFACE")
# =================================================================================================
_res = compute_project(dict(RICH), "P-LEDGER", "P1", CUTOFF)
_computed = {m["module_id"]: m for m in _res["modules"]}
_abstained = {m["module_id"]: m for m in _res.get("abstained", [])}
_rows = {**_abstained, **_computed}
_missing = [m for m in CAT7 if m not in _rows]
check(not _missing, "every Category-7 identity appears on the ledger, computed or abstaining",
      str(_missing))
_bad_source = [m for m in CAT7 if _rows[m].get("result_source") != "CANONICAL_V5_LAYER"]
check(not _bad_source,
      "every Category-7 ledger row records the canonical v16 route as its result source",
      str(_bad_source))
_no_reason = [m for m in CAT7 if not str(_rows[m].get("abstention_reason") or "").strip()]
check(not _no_reason, "and every abstaining row carries its reason in words", str(_no_reason))
_no_lineage = [m for m in CAT7 if m not in NON_OPERATIONAL and not _rows[m].get("lineage")]
check(not _no_lineage, "and every non-disabled row carries its lineage", str(_no_lineage))
# B2.9 is the one identity with no structure to name, and that is the truth about it rather than
# an omission: it is ARCHIVED, and what it would need to be restored is a Hilbert-space state
# space and a measurement model that this platform does not hold and does not solicit. Its row
# says so in words instead.
_no_structure = [m for m in CAT7
                 if m != "B2.9" and not _rows[m].get("canonical_structure")]
check(not _no_structure, "and names the structure it is defined on", str(_no_structure))
check(_rows["B2.9"].get("canonical_disposition") == "ARCHIVED"
      and "research record" in str(_rows["B2.9"].get("abstention_reason", "")),
      "with the archived identity naming its archival instead, because there is no structure it "
      "is waiting for", str(_rows["B2.9"].get("canonical_disposition")))
_proxy_marked = [m for m in CAT7
                 if _rows[m].get("proxy_qualifier") or _rows[m].get("proxy_label")
                 or _rows[m].get("truthful_method_name")]
check(not _proxy_marked,
      "and NO Category-7 row carries a legacy-proxy marker or a truthful-method label, because "
      "neither statement is true of the code any more", str(_proxy_marked))
_live_disabled = [m for m in NON_OPERATIONAL if m in _computed]
check(not _live_disabled,
      "the disabled and archived identities do not appear as live analytical readings at all",
      str(_live_disabled))
check(_res["simulation_version"] == SIMULATION_VERSION,
      "and the ledger carries the current simulation version", str(_res["simulation_version"]))
check(sorted(REG.CORE_VOTING_MODULES) == ["A1.7", "A1.8"],
      "voting is still exactly the two", str(sorted(REG.CORE_VOTING_MODULES)))
check("A3.4" in REG.DISABLED_MODULES, "and Material Cost Variance is still disabled")


# =================================================================================================
head("6. THE SYNTHETIC PACKAGE'S OWN DECISION PROBLEM REACHES THE CANONICAL RUNNER")
# =================================================================================================
_pkg_alts = PS.decision_alternatives("DP-01")
_out, _seen, _err = route("B2.19", {"decisionAlternatives": _pkg_alts})
check(bool(canonical_hits(_seen)) and not legacy_hits(_seen)
      and _out.get("canonical_disposition") == "CANONICAL_RESULT",
      "the synthetic research package's decision problem reaches the canonical layer through the "
      "production dispatcher, rather than being a structurally canonical fixture nothing runs",
      f"canonical={len(canonical_hits(_seen))} err={_err}")
check(_pkg_alts.get("data_origin") == "SYNTHETIC_RESEARCH_FIXTURE"
      and _pkg_alts.get("not_for_empirical_validation") is True,
      "and it carries its research origin, so a canonical success proves implementation and not "
      "field validity")
_locked, _, _ = route("B2.19", {"decisionAlternatives":
                                PS.decision_alternatives("DP-01", split="LOCKED_HOLDOUT")})
check(_locked.get("insufficient_data") is True,
      "and locked holdout material is still refused after the repointing, so the leakage control "
      "survived the change of structure")


# =================================================================================================
head("7. NO CATEGORY-7 LINEAGE CLAIM SURVIVES THAT THE ROUTE NO LONGER SUPPORTS")
# =================================================================================================
_still_declared = sorted(m for m in CAT7 if LIN.lineage_for(m) is not None)
check(not _still_declared,
      "no Category-7 identity declares a lineage record naming the earned-value or document "
      "body: the canonical route reads neither, and a record saying otherwise would assert a "
      "dependence that has stopped existing", str(_still_declared))


with (ROOT / "code_audit" / "run30_cat7_operational_execution.csv").open(
        "w", encoding="utf-8", newline="\n") as fh:
    w = csv.DictWriter(fh, fieldnames=list(ROWS[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(ROWS)

print()
print("=" * 78)
if FAILURES:
    print(f"{len(FAILURES)} check(s) did not hold:")
    for f in FAILURES:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
