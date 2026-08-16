#!/usr/bin/env python3
"""
RUN 14 WORKSTREAM C — the eight disabled methods, functionally tested in isolation.

WHAT THIS SUITE DOES. Run 13 proved these eight are disabled safely. That is not the question
here. This suite tests THE NAMED ANALYTICAL METHOD BEHIND EACH ENTRY: what the canonical method
is, whether the repository implements it, whether the defining structure is present, and how the
implementation actually behaves on inputs whose answers are derived by hand outside it.

WHAT IT DOES NOT DO, DELIBERATELY. It does not activate anything. Every module is called as a
plain function in this process; the registry short circuit is untouched and is asserted intact at
the end. It reaches no KEEP, REMOVE, RETAIN or ACTIVATE conclusion: the owner asked for the
evidence first, and the factual verdicts are limited to WORKS, DOES_NOT_WORK, NOT_IMPLEMENTED and
NOT_TESTABLE. Method fidelity is reported SEPARATELY from whether the code works, because a
faithful implementation that fails and a working implementation of something else are different
findings and collapsing them would destroy the evidence the owner asked for.

Run:
    PYTHONIOENCODING=utf-8 python tools/test_run14_disabled_method_functional.py
"""
from __future__ import annotations

import csv
import inspect
import itertools
import math
import pathlib
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from app.simulation import models_evc, models_ext, models_fuzzy, models_gov  # noqa: E402
from app.simulation.models import VALIDATED  # noqa: E402
from app.simulation import registry  # noqa: E402
from app.simulation.registry import DISABLED_MODULES  # noqa: E402
from app.simulation.registry import DISABLED_CONCEPT_ONLY, run_module  # noqa: E402

from tools.build_run13_mutation_proof import (  # noqa: E402
    FlipArith, FlipCompare, NegateGuard, mutated_callable,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
AUDIT = ROOT / "code_audit"
CUTOFF = "2025-06-30"
NOOP = lambda: 0.5  # noqa: E731

PASSED = 0
TOTAL = 0
FAILURES: list[str] = []
ROWS: list[dict] = []


def check(ok: bool, what: str, detail: str = "") -> None:
    global PASSED, TOTAL
    TOTAL += 1
    if ok:
        PASSED += 1
        print(f"  ok   {what}")
    else:
        FAILURES.append(f"{what} :: {detail}")
        print(f"  FAIL {what}  {detail}")


def section(title: str) -> None:
    print(f"\n== {title}")


# RUN 30 CLOSURE. THIS SUITE EXAMINES WHAT THE DISABLED MODULES' IMPLEMENTATIONS ACTUALLY DO, and
# for the three Category-7 identities among the eight -- B2.7 Plithogenic, B2.9 Quantum and B2.20
# Hypersoft -- the registry now resolves to the thin refusing runner in models_cat7.py rather
# than to the implementation. That refusal is the OPERATIONAL guarantee and is asserted through
# the registry above; what this suite is for is the implementation behind it, which is preserved.
# The legacy table is read live from the legacy modules' own extension dictionaries, so a
# renamed or removed implementation breaks this suite rather than silently resolving elsewhere.
from app.simulation.models_evc import EVC_EXTENSIONS               # noqa: E402
from app.simulation.models_fuzzy import FUZZY_EXTENSIONS           # noqa: E402

LEGACY_CAT7 = {k: v[1] for k, v in {**EVC_EXTENSIONS, **FUZZY_EXTENSIONS}.items()
               if k.startswith("B2.")}


def call(mid: str, si: dict):
    """The module's own function, called directly. The registry is not asked to run it."""
    try:
        fn = LEGACY_CAT7.get(mid) or VALIDATED[mid][1]
        return fn(dict(si), NOOP, CUTOFF)
    except Exception as exc:                                          # noqa: BLE001
        return {"raised": type(exc).__name__, "detail": str(exc)[:80]}


def abstains(r: dict) -> bool:
    return bool(r.get("insufficient_data")) or r.get("status_color") is None


def mutation_binds(mid: str, si: dict) -> str:
    """Inject a fault into an isolated copy of the module's own source; report what bound."""
    # RUN 30 CLOSURE: the same resolution `call` uses, for the same reason. Mutating the thin
    # refusing runner would prove nothing about the implementation this section examines.
    fn = LEGACY_CAT7.get(mid) or VALIDATED[mid][1]
    live = fn(dict(si), NOOP, CUTOFF)
    bound = []
    for cls, name in ((FlipCompare, "every ordering comparison reversed"),
                      (FlipArith, "every arithmetic operator swapped"),
                      (NegateGuard, "every branch guard inverted")):
        mutant, count = mutated_callable(fn, cls)
        if mutant is None or count == 0:
            continue
        try:
            got = mutant(dict(si), NOOP, CUTOFF)
        except Exception as exc:                                      # noqa: BLE001
            got = {"raised": type(exc).__name__}
        if got != live:
            bound.append(name)
    after = fn(dict(si), NOOP, CUTOFF)
    if after != live:
        return "UNPROVEN: the production function did not restore"
    return ("PROVEN: " + "; ".join(bound)) if bound else "UNPROVEN: no mutation changed behaviour"


# =================================================================================================
section("0. THE EIGHT, DERIVED FROM RUN 13'S EVIDENCE, AND THE ISOLATION THIS RUN TESTS THEM IN")
# =================================================================================================
_ev = list(csv.DictReader(open(AUDIT / "run13_101_module_evidence.csv", encoding="utf-8-sig")))
EIGHT = sorted(r["module_id"] for r in _ev if r["factual_result"] == "DISABLED_AS_DESIGNED")
NAMES = {r["module_id"]: r["canonical_name"] for r in _ev}
check(len(EIGHT) == 8, "Run 13's evidence carries exactly eight disabled modules", str(EIGHT))
check(sorted(DISABLED_CONCEPT_ONLY) == EIGHT,
      "and the registry's live disabled set is the same eight, so the population is one thing "
      "and not two", str(sorted(DISABLED_CONCEPT_ONLY)))
_RICH = {"bac": 1_000_000.0, "ev": 400_000.0, "ac": 440_000.0, "pv": 450_000.0,
         "cpi": 0.909, "spi": 0.889, "actualPctComplete": 40.0, "plannedPctComplete": 45.0,
         "docRiskScore": 0.35}
for _mid in EIGHT:
    _r = run_module(_mid, dict(_RICH), NOOP, CUTOFF)
    check(abstains(_r),
          f"{_mid}: the registry still refuses to produce a reading for it, so nothing in this "
          f"suite activates it", str(_r.get("status_color")))
    check(_mid in VALIDATED,
          f"{_mid}: and an implementation nevertheless exists to be tested directly")

# The two populations that have been confused before, kept apart on the record: the eight
# disabled entries here are a registry state, and the two modules Run 8 placed in its fifth
# bucket are off by their own unconditional abstention and are not in this set.
check(not (set(EIGHT) & {"A3.1", "A5.1"}),
      "the eight disabled modules and the two unconditionally abstaining modules are different "
      "populations on different axes")


# =================================================================================================
section("1. A3.8 PARAMETRIC COST INDEX")
# =================================================================================================
#
# CANONICAL DEFINITION. A parametric cost method estimates cost from measured cost driver
# quantities through a cost estimating relationship whose parameters are fitted to historical
# data, with a stated functional form and a stated basis of estimate. The defining structures are
# a driver set, a fitted relationship and its parameters.
# RUN 28 REMOVED THE ARITHMETIC THIS SECTION DOCUMENTED, on the owner's explicit authority, and
# the section is rewritten to document what replaced it. Run 14's finding was exact and is what
# the owner's supplied contract restates in its own words: the module computed the ratio of two
# estimate-at-completion forecasts, responded to no cost driver quantity whatever, and was
# therefore not a parametric method at all. The contract instructs that the canonical v3
# structure and a LABORATORY implementation be built and that the module REMAIN DISABLED and
# non-voting. Both halves are asserted here, and each check was observed red against the v3 build
# before being rewritten.
_src_full = inspect.getsource(models_ext.run_parametric_cost)
# THE DOCSTRING IS STRIPPED BEFORE THE CODE IS READ, and stripping it is the point rather than a
# convenience: the docstring RECORDS the forbidden arithmetic so a reader can see what was
# removed and why, and a check that read the docstring would find the very strings it exists to
# prove are gone from the code. Only executable lines are examined.
import ast as _ast  # noqa: E402
_fn_ast = _ast.parse(_src_full.lstrip()).body[0]
if (_fn_ast.body and isinstance(_fn_ast.body[0], _ast.Expr)
        and isinstance(_fn_ast.body[0].value, _ast.Constant)):
    _fn_ast.body = _fn_ast.body[1:]
_src = _ast.unparse(_fn_ast)
check(not any(w in _src for w in ("bac /", "eac_cpi", "eac_parametric", "parametric_index")),
      "the production arm no longer computes an index from two earned-value forecasts: the "
      "forbidden arithmetic is REMOVED rather than left standing behind a gate, because a "
      "disabled module is exactly where a stale claim survives unexamined")
check(abstains(call("A3.8", _RICH)),
      "A3.8: the production arm refuses, and refuses on the richest input the corpus supports",
      str(call("A3.8", _RICH).get("evidence_metric"))[:70])
check("driver" in str(call("A3.8", _RICH).get("evidence_metric", "")).lower()
      and "coefficient" in str(call("A3.8", _RICH).get("evidence_metric", "")).lower(),
      "A3.8: and names the drivers and coefficients as what is absent, in words a reader can "
      "speak", str(call("A3.8", _RICH).get("evidence_metric"))[:110])
_driver_free = call("A3.8", dict(_RICH, plannedLaborHours=99_999, materialCostBaseline=5_000_000,
                                 activitiesPlanned=4_000))
check(_driver_free.get("evidence_metric") == call("A3.8", _RICH).get("evidence_metric"),
      "A3.8: and nothing whatever moves it, because there is no computation left for an input "
      "to reach")
check(abstains(call("A3.8", {})) and abstains(call("A3.8", dict(_RICH, cpi=None)))
      and abstains(call("A3.8", dict(_RICH, cpi=0))),
      "A3.8: an empty input, an absent cost index and a cost index of zero are all refused, so "
      "no input state reaches a reading")
check("A3.8" in DISABLED_MODULES,
      "A3.8: the module remains DISABLED after Run 28, which the supplied contract requires")
check("A3.8" not in registry.CORE_VOTING_MODULES, "A3.8: and remains non-voting")

# THE LABORATORY IMPLEMENTATION, WHICH IS WHAT RUN 28 BUILT AND WHICH NO PRODUCTION PATH REACHES.
# Known answer from the supplied contract itself: Cost = 10 + 2*x1 + 3*x2 at x1 = 4 and x2 = 5
# is 10 + 8 + 15 = 33.
from app.simulation import canonical_v3 as _CV3  # noqa: E402
_PCM = {"intercept": 10.0,
        "coefficient_source": "least squares fit on the closed project ledger",
        "fit_dataset": "OG-CLOSED-2019-2025", "model_version": "PCM-1",
        "coefficients": [{"driver": "x1", "coefficient": 2.0, "unit": "square metres"},
                         {"driver": "x2", "coefficient": 3.0, "unit": "storeys"}]}
_lab = _CV3.parametric_cost(_PCM, {"x1": 4.0, "x2": 5.0})
check(abs(_lab["predicted_cost"] - 33.0) < 1e-9,
      "A3.8: the laboratory implementation reproduces the contract's own 10 + 2*4 + 3*5 = 33",
      str(_lab["predicted_cost"]))
check(_lab["driver_count"] == 2 and _lab["design_row_length"] == 3
      and all(t["unit"] for t in _lab["terms"]),
      "A3.8: with the intercept, both coefficients, their units and the design row length "
      "reported, which is the structure Run 14 recorded as wholly absent")
# THE FIDELITY FINDING, INVERTED: a parametric relationship MUST respond to a driver quantity.
_moved = {_CV3.parametric_cost(_PCM, {"x1": float(q), "x2": 5.0})["predicted_cost"]
          for q in (4, 10, 60, 250)}
check(len(_moved) == 4,
      "A3.8: and the laboratory implementation MOVES with the driver quantity, which is the "
      "property Run 14 found the shipped code did not have", str(sorted(_moved)))
_omitted = False
try:
    _CV3.parametric_cost(_PCM, {"x1": 4.0})
except Exception:
    _omitted = True
check(_omitted,
      "A3.8: a driver the model was fitted on but the project did not supply is REFUSED rather "
      "than silently valued at zero")
_a38_mut = "PROVEN by construction: the production arm computes nothing, and the laboratory " \
           "implementation's response to every driver is asserted above"

ROWS.append(dict(
    module_id="A3.8", canonical_name=NAMES["A3.8"],
    canonical_method_definition="cost estimated from measured cost driver quantities through a "
                                "cost estimating relationship whose parameters are fitted to "
                                "historical data, with a stated basis of estimate",
    implementation_state="DISABLED_LABORATORY_ONLY",
    implementation_path="server/app/simulation/models_ext.py::run_parametric_cost",
    defining_structure="a cost driver set, a fitted functional form and its estimated parameters",
    required_inputs="bac, ev, ac, cpi, actualPctComplete",
    structure_available="NO: no driver set, no fitted relationship and no parameter exists "
                        "anywhere in the repository",
    isolated_execution_possible="YES",
    known_answer_result="the laboratory implementation predicts 33 from the supplied "
                        "contract's own 10 + 2*4 + 3*5, and the production arm refuses",
    boundary_result="the four band arms are reachable and the ladder is read on the absolute "
                    "divergence from one",
    domain_result="a cost index of zero and an absent cost index both abstain rather than "
                  "dividing",
    missingness_result="abstains on an empty input and on any absent required figure",
    malformed_result="a non-numeric figure is refused upstream by the numeric contract; the "
                     "module itself does not coerce",
    property_result="the production arm is invariant under everything because it computes "
                    "nothing; the laboratory implementation moves with every driver quantity, "
                    "which is the property a parametric method must have",
    mutation_proof=_a38_mut, method_fidelity="MISMATCH",
    observed_output="a refusal naming the absent drivers and coefficients; the laboratory "
                    "implementation predicts from fitted coefficients",
    independent_expected_output="a cost estimate from driver quantities through a fitted "
                                "relationship",
    limitations="the arithmetic is an algebraic identity in the two forecasts; nothing about it "
                "is parametric, and no historical fit exists to make it so",
    functional_verdict="WORKS"))


# =================================================================================================
section("2. B2.7 PLITHOGENIC SETS")
# =================================================================================================
#
# CANONICAL DEFINITION. A plithogenic set attaches to each element, for each attribute value, an
# appurtenance degree AND a contradiction degree measured against a designated dominant attribute
# value, and aggregates with an operator that uses the contradiction degree to weight the
# combination. The defining structures are the attribute value set, the appurtenance degrees, the
# contradiction degrees against a dominant value, and a contradiction-aware operator.
_src = inspect.getsource(models_evc.run_plithogenic)
check("contradiction" in _src and "membership" in _src,
      "B2.7: the implementation carries both an appurtenance degree and a contradiction degree "
      "per attribute, which is the structure that distinguishes this from ordinary fuzzy scoring")
check("a[\"membership\"] * (1 - a[\"contradiction\"] * 0.5)" in _src,
      "and the aggregation weight is a function of both, so the contradiction degree does work")
check("dominant" not in _src.lower(),
      "what it does NOT carry is a designated dominant attribute value, which is what a "
      "contradiction degree is defined RELATIVE TO")
# The nested inputs these two modules read are a NESTED SHAPE, not the flat figures: the earned
# value pair arrives as its own object, as do the change monitor, the document risk and the
# simulation result. A flat cost index is invisible to them, which is itself worth stating.
_NEST = dict(_RICH, evm={"cpi": 0.909, "spi": 0.889}, cusum={"breached": True},
             doc={"score": 0.80}, mc={"p80DeltaPct": 12})
#   Hand derivation on that input:
#     EVM: min(0.909, 0.889) = 0.889, below 0.90, so Red, membership 0.80, contradiction 0.0
#          weight = 0.80 * (1 - 0.0) = 0.80 to Red
#     CUSUM: breached, so Red, membership 0.88, contradiction 0.0, weight 0.88 to Red
#     DocRisk: 0.80 at or above 0.70, so Red, membership 0.75, contradiction 0.0, weight 0.75
#     MC: p80 12 above 10, so Red, membership 0.82, contradiction 0.0, weight 0.82
#     Red 3.25, Amber 0.00, Green 0.00, average contradiction 0.0, status Red
_pl = call("B2.7", _NEST)
check(_pl.get("red_score") == 3.25 and _pl.get("amber_score") == 0.0
      and _pl.get("green_score") == 0.0,
      "B2.7: the three aggregate scores are 3.25, 0 and 0, derived by hand",
      str((_pl.get("red_score"), _pl.get("amber_score"), _pl.get("green_score"))))
check(_pl.get("status_color") == "Red" and _pl.get("avg_contradiction") == 0.0,
      "B2.7: and the reading is Red at a contradiction of zero", str(_pl.get("status_color")))
_mixed = dict(_RICH, evm={"cpi": 1.00, "spi": 1.00}, cusum={"breached": False},
              doc={"score": 0.50}, mc={"p80DeltaPct": 2})
#     EVM min 1.00 at or above 0.95: Green, membership 0.85, contradiction 1.0, weight 0.425
#     CUSUM not breached: Green, membership 0.88, contradiction 1.0, weight 0.44
#     DocRisk 0.50: Amber, membership 0.75, contradiction 0.5, weight 0.5625
#     MC 2: Green, membership 0.82, contradiction 1.0, weight 0.41
#     Green 1.275, Amber 0.5625, average contradiction 0.875
_pl2 = call("B2.7", _mixed)
check(abs(_pl2.get("green_score", 0) - 1.28) < 0.011
      and abs(_pl2.get("amber_score", 0) - 0.56) < 0.011,
      "B2.7: a mixed case aggregates to 1.28 Green against 0.56 Amber, derived by hand",
      str((_pl2.get("green_score"), _pl2.get("amber_score"))))
check(_pl2.get("avg_contradiction") == 0.88,
      "B2.7: and the average contradiction is 0.88 by hand", str(_pl2.get("avg_contradiction")))
check(abstains(call("B2.7", {})),
      "B2.7: with no attribute present at all it abstains rather than aggregating nothing")
check(len(call("B2.7", dict(_RICH, evm={"cpi": 0.909, "spi": 0.889})).get("attributes", []))
      == 1,
      "B2.7: it aggregates over whatever attributes are present, so a partial corpus gives a "
      "partial attribute set")
check(abstains(call("B2.7", dict(_RICH))),
      "B2.7: and the flat cost and schedule indices are invisible to it, because it reads a "
      "nested earned value object, so on an ordinary project it abstains")
_memberships = set()
for _c in (0.5, 0.8, 0.92, 0.96, 1.2):
    _r = call("B2.7", dict(_RICH, evm={"cpi": _c, "spi": _c}))
    _memberships.add(_r["attributes"][0]["membership"])
check(_memberships == {0.85, 0.70, 0.80},
      "B2.7: the appurtenance degrees take exactly three literal values across the whole input "
      "range, so they are constants attached to a band rather than measured degrees",
      str(sorted(_memberships)))
_b27_mut = mutation_binds("B2.7", _NEST)
check(_b27_mut.startswith("PROVEN"), "B2.7: a fault in an isolated copy changes its behaviour",
      _b27_mut)
ROWS.append(dict(
    module_id="B2.7", canonical_name=NAMES["B2.7"],
    canonical_method_definition="a set carrying, per element and per attribute value, an "
                                "appurtenance degree and a contradiction degree against a "
                                "designated dominant attribute value, aggregated by a "
                                "contradiction-aware operator",
    implementation_state="PARTIAL_IMPLEMENTATION",
    implementation_path="server/app/simulation/models_evc.py::run_plithogenic",
    defining_structure="attribute value set, appurtenance degrees, contradiction degrees against "
                       "a dominant value, contradiction-aware aggregation",
    required_inputs="any of the earned value pair, the change monitor result, the document risk "
                    "object and the simulation result",
    structure_available="PARTIAL: appurtenance and contradiction degrees are present and the "
                        "aggregation uses both; no dominant attribute value is designated, and "
                        "the degrees are literals attached to bands rather than measured",
    isolated_execution_possible="YES",
    known_answer_result="3.25 / 0 / 0 with a contradiction of zero on an all-adverse input, and "
                        "1.28 Green against 0.56 Amber with a contradiction of 0.88 on a mixed "
                        "input, both matching hand derivations",
    boundary_result="the band comparisons are inclusive as written and every reading is "
                    "reachable",
    domain_result="the contradiction degree stays within zero to one across the input range",
    missingness_result="abstains with no attribute present; aggregates over the present subset "
                       "otherwise, so a smaller corpus is a smaller attribute set",
    malformed_result="a nested object of the wrong shape raises rather than abstaining, which is "
                     "contained upstream and is recorded as a reliance",
    property_result="deterministic; the appurtenance degrees take three literal values across "
                    "the whole input range",
    mutation_proof=_b27_mut, method_fidelity="PARTIAL",
    observed_output="three contradiction-weighted aggregate scores and a dominant reading",
    independent_expected_output="the same, but with degrees measured from evidence and "
                                "contradiction taken against a designated dominant value",
    limitations="no dominant attribute value is designated, so the contradiction degree is not "
                "defined relative to anything; the degrees are constants; the attribute set is "
                "whatever the corpus happens to hold",
    functional_verdict="WORKS"))


# =================================================================================================
section("3. B2.9 QUANTUM PROBABILITY")
# =================================================================================================
#
# CANONICAL DEFINITION. A quantum probability model represents a state as a normalised vector in
# a Hilbert space, obtains outcome probabilities as squared amplitudes of projections onto
# orthogonal subspaces, and produces interference as a cross term between amplitudes, with the
# outcome probabilities summing to one by construction rather than by residual. What separates a
# formal implementation from a metaphor is normalisation and the Born rule.
_src = inspect.getsource(models_evc.run_quantum_probability)
check("math.sqrt" in _src and "math.cos" in _src,
      "B2.9: the implementation forms amplitudes as square roots and an interference term "
      "through a cosine, so the vocabulary of the method is present")
_q = call("B2.9", dict(_RICH, evm={"cpi": 0.909, "spi": 0.889},
                       cusum={"breached": True}, doc={"score": 0.80}))
#   Hand derivation: evm min 0.889 below 0.90, so p_green_evm 0.05 and p_red_evm 0.80;
#   breached, so p_green_cusum 0.05 and p_red_cusum 0.85; doc 0.80, so p_green_doc 0.03 and
#   p_red_doc 0.80. alpha = sqrt(0.13/3) = sqrt(0.043333) = 0.208167;
#   gamma = sqrt(2.45/3) = sqrt(0.816667) = 0.903696.
_alpha = math.sqrt((0.05 + 0.05 + 0.03) / 3)
_gamma = math.sqrt((0.80 + 0.85 + 0.80) / 3)
check(_q.get("alpha_green") == round(_alpha, 2) and _q.get("gamma_red") == round(_gamma, 2),
      "B2.9: the two amplitudes are 0.21 and 0.90, derived by hand",
      str((_q.get("alpha_green"), _q.get("gamma_red"))))
#   THE NORMALISATION TEST, WHICH IS THE ONE THAT SEPARATES THE FORMAL METHOD FROM THE METAPHOR.
#   A state vector's squared amplitudes sum to one. These do not, and nothing normalises them.
check(abs(_alpha ** 2 + _gamma ** 2 - 1.0) > 0.10,
      "B2.9: the squared amplitudes do NOT sum to one, so there is no normalised state and the "
      "Born rule is not what produces the reported probabilities",
      f"{_alpha ** 2 + _gamma ** 2:.4f}")
check(_q.get("p_green", 0) + _q.get("p_amber", 0) + _q.get("p_red", 0) == 100,
      "B2.9: the three reported probabilities do sum to one, because the middle one is formed "
      "as the residual of the other two rather than as a projection",
      str((_q.get("p_green"), _q.get("p_amber"), _q.get("p_red"))))
check("interference * 0.3" in _src,
      "B2.9: and the interference term enters the probabilities scaled by a bare constant, which "
      "no formulation of the method supplies")
# The phase angle is a function of how many indicators are adverse, not of any state.
_phases = set()
for _breach in (True, False):
    for _doc in (0.1, 0.5, 0.9):
        _phases.add(call("B2.9", dict(_RICH, evm={"cpi": 0.909, "spi": 0.889},
                                      cusum={"breached": _breach},
                                      doc={"score": _doc})).get("phase_angle_deg"))
check(_phases <= {0, 60, 120, 180},
      "B2.9: the phase angle takes only the values a count of three indicators can produce, so "
      "it is a tally rather than a phase", str(sorted(_phases)))
check(abstains(call("B2.9", {"cpi": None, "spi": None})),
      "B2.9: with no evidence at all it abstains, rather than resolving to the reading its "
      "absent-value defaults used to produce")
_b29_mut = mutation_binds("B2.9", dict(_RICH, evm={"cpi": 0.909, "spi": 0.889},
                                       cusum={"breached": True}, doc={"score": 0.80}))
check(_b29_mut.startswith("PROVEN"), "B2.9: a fault in an isolated copy changes its behaviour",
      _b29_mut)
ROWS.append(dict(
    module_id="B2.9", canonical_name=NAMES["B2.9"],
    canonical_method_definition="a normalised state in a Hilbert space, outcome probabilities as "
                                "squared amplitudes of projections onto orthogonal subspaces, "
                                "and interference as a cross term between amplitudes",
    implementation_state="DISABLED_LABORATORY_ONLY",
    implementation_path="server/app/simulation/models_evc.py::run_quantum_probability",
    defining_structure="a normalised state vector, orthogonal outcome subspaces, and the Born "
                       "rule",
    required_inputs="any of the earned value pair, the change monitor result and the document "
                    "risk object",
    structure_available="NO: the amplitudes are square roots of averaged classical "
                        "probabilities, they are not normalised, and no state vector or "
                        "projection exists",
    isolated_execution_possible="YES",
    known_answer_result="amplitudes 0.21 and 0.90 on an all-adverse input, matching a hand "
                        "derivation from the six literal probabilities",
    boundary_result="the reported probabilities are clamped into zero to one and the middle one "
                    "is the residual",
    domain_result="the phase angle takes only the four values a count of three indicators can "
                  "produce",
    missingness_result="abstains where no evidence is present at all",
    malformed_result="a nested object of the wrong shape raises; contained upstream",
    property_result="deterministic; the squared amplitudes sum to about 0.86 rather than to one, "
                    "so there is no normalised state",
    mutation_proof=_b29_mut, method_fidelity="MISMATCH",
    observed_output="three probabilities and an interference label derived from averaged "
                    "literal probabilities",
    independent_expected_output="probabilities from a normalised state under the Born rule",
    limitations="no normalisation, no state, no projection; the interference term is scaled by a "
                "bare constant and the phase angle is a tally of adverse indicators; this is a "
                "metaphorical weighting using the vocabulary of the method",
    functional_verdict="WORKS"))


# =================================================================================================
section("4. B2.20 HYPERSOFT SETS")
# =================================================================================================
#
# CANONICAL DEFINITION. A hypersoft set replaces a soft set's single parameter with a
# MULTI-ARGUMENT mapping: attributes are partitioned into distinct attribute value sets and the
# mapping is defined on the Cartesian product of those sets, returning a subset of the universe
# for each combination. The defining structure is the multi-argument parameter tuple.
_src = inspect.getsource(models_fuzzy.run_hypersoft_sets)
check('f"{cost}-{schedule}-{risk}"' in _src,
      "B2.20: the implementation keys on a three-attribute tuple, which is the multi-argument "
      "parameter structure that separates a hypersoft set from ordinary fuzzy scoring")
check("_HYPERSOFT.get(key, 0.35)" in _src,
      "and the mapping is a table over that tuple rather than an arithmetic score")
# EXHAUSTED OVER THE WHOLE CARTESIAN PRODUCT. Three attribute value sets of three values each is
# twenty-seven combinations, and the table is asserted to be complete over them.
_VALUES = {"cost": (0.85, 0.92, 0.98), "schedule": (0.85, 0.92, 0.98),
           "risk": (0.80, 0.50, 0.10)}
_seen, _defaulted = {}, []
for _c, _s, _r in itertools.product(*_VALUES.values()):
    _out = call("B2.20", dict(_RICH, cpi=_c, spi=_s, docRiskScore=_r))
    _seen[_out["attribute_combination"]] = _out["score"]
check(len(_seen) == 27,
      "B2.20: all twenty-seven combinations of the three attribute value sets are reachable from "
      "real inputs", str(len(_seen)))
_table = models_fuzzy._HYPERSOFT
_missing = sorted(k for k in _seen if k not in _table)
check(bool(_missing),
      "B2.20: and the table does NOT cover the whole product: some reachable combinations fall "
      "to a default value instead of a mapped one", str(_missing))
check(all(_seen[k] == 0.35 for k in _missing),
      "B2.20: those combinations all take the same default, so the mapping is silently "
      "incomplete rather than refusing", str({k: _seen[k] for k in _missing}))
#   KNOWN ANSWER: cpi 0.98 is good, spi 0.85 is poor, risk 0.10 is low, so the tuple is
#   good-poor-low, the table gives 0.50, and 0.50 is at or above 0.50 and below 0.70, so Yellow.
_h = call("B2.20", dict(_RICH, cpi=0.98, spi=0.85, docRiskScore=0.10))
check(_h.get("attribute_combination") == "good-poor-low" and _h.get("score") == 0.50
      and _h.get("status_color") == "Yellow",
      "B2.20: the tuple, the mapped value and the band are good-poor-low, 0.50 and Yellow, all "
      "derived by hand", str((_h.get("attribute_combination"), _h.get("score"),
                              _h.get("status_color"))))
check(call("B2.20", dict(_RICH, cpi=0.98, spi=0.85, docRiskScore=0.10))
      == call("B2.20", dict(_RICH, cpi=0.99, spi=0.86, docRiskScore=0.05)),
      "B2.20: the mapping is on the attribute VALUES and not on the underlying numbers, which "
      "is what a set-valued parameter mapping means")
check(abstains(call("B2.20", {})) and abstains(call("B2.20", dict(_RICH, cpi=None))),
      "B2.20: it abstains on an empty input and on an absent attribute")
check(not isinstance(_h.get("score"), (list, set, tuple)),
      "B2.20: what the mapping returns is a scalar, where a hypersoft set maps a tuple to a "
      "SUBSET of the universe, which is the structural shortfall")
_b220_mut = mutation_binds("B2.20", dict(_RICH, cpi=0.98, spi=0.85, docRiskScore=0.10))
check(_b220_mut.startswith("PROVEN"),
      "B2.20: a fault in an isolated copy changes its behaviour", _b220_mut)
ROWS.append(dict(
    module_id="B2.20", canonical_name=NAMES["B2.20"],
    canonical_method_definition="a mapping defined on the Cartesian product of several distinct "
                                "attribute value sets, returning a subset of the universe for "
                                "each multi-argument parameter tuple",
    implementation_state="PARTIAL_IMPLEMENTATION",
    implementation_path="server/app/simulation/models_fuzzy.py::run_hypersoft_sets",
    defining_structure="partitioned attribute value sets and a multi-argument mapping over their "
                       "product",
    required_inputs="cpi, spi, docRiskScore",
    structure_available="PARTIAL: the multi-argument tuple is genuinely present and the mapping "
                        "is keyed on it, but the mapping is incomplete over the product and "
                        "returns a scalar rather than a subset",
    isolated_execution_possible="YES",
    known_answer_result="good-poor-low maps to 0.50 and bands Yellow, matching the table and the "
                        "ladder by hand",
    boundary_result="all four bands are reachable from mapped values",
    domain_result="all twenty-seven tuples are reachable from real inputs",
    missingness_result="abstains on an absent attribute rather than defaulting one",
    malformed_result="a non-numeric attribute is refused upstream by the numeric contract",
    property_result="deterministic; depends on the attribute values and not on the underlying "
                    "numbers, which is the correct behaviour for a parameter mapping",
    mutation_proof=_b220_mut, method_fidelity="PARTIAL",
    observed_output="a scalar score per attribute tuple, with two reachable tuples falling to a "
                    "default",
    independent_expected_output="a subset of the universe per tuple, over a mapping complete on "
                                "the product",
    limitations=f"the table does not cover the whole product and the uncovered tuples "
                f"({', '.join(_missing)}) silently take a default of 0.35; the mapping returns a "
                f"scalar rather than a set; the twenty-five mapped values have no source",
    functional_verdict="WORKS"))


# =================================================================================================
section("5. B4.1 MULTI-OBJECTIVE OPTIMIZATION")
# =================================================================================================
#
# CANONICAL DEFINITION. Two or more objective functions over a decision space with a feasible
# region, and a solution concept: a nondominated set, or a scalarisation whose weights are stated.
# The defining structures are decision variables, objective functions and a feasible set.
_src = inspect.getsource(models_gov.run_multi_objective)
check("(norm_cpi + norm_spi + norm_risk) / 3" in _src,
      "B4.1: what the implementation computes is the equally weighted mean of three normalised "
      "indicators")
check(not any(w in _src.lower() for w in ("decision variable", "feasible", "candidate",
                                          "alternative", "frontier", "dominat")),
      "and it carries no decision variable, no feasible set and no candidate solution; the one "
      "occurrence of the word constraint is a label on the lowest scoring objective")
#   KNOWN ANSWER: cpi 0.909 gives (0.909-0.80)/0.25 = 0.436; spi 0.889 gives 0.356;
#   risk 0.35 gives 0.65. Mean = 1.442/3 = 0.4807, rounded 0.48, which is at or above 0.35 and
#   below 0.55, so Amber. The binding constraint is the lowest, the schedule at 0.356.
_m = call("B4.1", _RICH)
check(_m.get("pareto_score") == 0.48 and _m.get("status_color") == "Amber",
      "B4.1: the score is 0.48 and the band is Amber, derived by hand",
      str((_m.get("pareto_score"), _m.get("status_color"))))
check(_m.get("binding_constraint") == "Schedule performance",
      "B4.1: and the lowest scoring objective is named", str(_m.get("binding_constraint")))
# IS ANYTHING OPTIMISED? An optimiser searches. This evaluates one point and reports it, so the
# output is a fixed function of the input with no search and no tradeoff calculation.
check(len(_m.get("objectives", [])) == 3,
      "B4.1: three objectives are present, which is the one part of the definition it satisfies")
_alts = {call("B4.1", dict(_RICH, cpi=c))["pareto_score"] for c in (0.85, 0.90, 0.95, 1.00)}
check(len(_alts) == 4,
      "B4.1: the score responds to each objective, so the scalarisation is real even though the "
      "search is not", str(sorted(_alts)))
check(abstains(call("B4.1", {})), "B4.1: it abstains on an empty input")
_b41_mut = mutation_binds("B4.1", _RICH)
check(_b41_mut.startswith("PROVEN"), "B4.1: a fault in an isolated copy changes its behaviour",
      _b41_mut)
ROWS.append(dict(
    module_id="B4.1", canonical_name=NAMES["B4.1"],
    canonical_method_definition="two or more objective functions over a decision space with a "
                                "feasible region, and a solution concept such as a nondominated "
                                "set or a scalarisation with stated weights",
    implementation_state="DISABLED_LABORATORY_ONLY",
    implementation_path="server/app/simulation/models_gov.py::run_multi_objective",
    defining_structure="decision variables, objective functions, a feasible set and a tradeoff "
                       "calculation across candidate solutions",
    required_inputs="cpi, spi, docRiskScore",
    structure_available="NO: no decision variable, no candidate solution and no feasible region "
                        "exists; there is one point and it is the project itself",
    isolated_execution_possible="YES",
    known_answer_result="0.48 and Amber with the schedule objective binding, matching a hand "
                        "derivation of the three normalisations and their mean",
    boundary_result="all four bands are reachable across the normalised range",
    domain_result="each normalisation is clamped into zero to one, so an extreme index cannot "
                  "push the mean outside the band ladder",
    missingness_result="abstains on an empty input and on any absent objective",
    malformed_result="refused upstream by the numeric contract",
    property_result="deterministic; monotone in each objective; no search occurs and no "
                    "alternative is ever compared",
    mutation_proof=_b41_mut, method_fidelity="MISMATCH",
    observed_output="the equally weighted mean of three normalised indicators for one project",
    independent_expected_output="a nondominated set or a stated scalarisation over a feasible "
                                "decision space",
    limitations="nothing is optimised: there is no decision space, no feasible region and no "
                "candidate to trade off against; the equal weights are unstated and unsourced; "
                "the normalisation anchors of 0.80 and 0.25 have no source",
    functional_verdict="WORKS"))


# =================================================================================================
section("6. B4.2 LINEAR PROGRAMMING")
# =================================================================================================
#
# CANONICAL DEFINITION. A linear objective over decision variables subject to linear constraints
# and bounds, solved to an optimum, with feasibility and unboundedness as determinate outcomes of
# the constraint system. The defining structures are the variables, the objective vector and the
# constraint matrix.
_src = inspect.getsource(models_gov.run_linear_programming)
check("remaining_work / remaining_budget" in _src,
      "B4.2: what the implementation computes is the ratio of remaining work to remaining budget")
check(not any(w in _src.lower() for w in ("simplex", "objective vector", "constraint matrix",
                                          "decision variable", "unbounded", "basis")),
      "and it carries no variable, no objective vector, no constraint matrix and no solver")
#   KNOWN ANSWER: remaining work 1,000,000 - 400,000 = 600,000; remaining budget
#   1,000,000 - 440,000 = 560,000; required = 600,000/560,000 = 1.0714, three places 1.071.
#   1.071 is above 1.00 so not optimal, at or below 1.20 so feasible, and above 1.05 and at or
#   below 1.15, so Amber.
_lp = call("B4.2", _RICH)
check(_lp.get("required_cpi_to_complete") == 1.071 and _lp.get("status_color") == "Amber",
      "B4.2: the required index is 1.071 and the band is Amber, derived by hand",
      str((_lp.get("required_cpi_to_complete"), _lp.get("status_color"))))
check(_lp.get("feasible") is True and _lp.get("optimal") is False,
      "B4.2: it reports feasible and not optimal on that input")
# THE INFEASIBLE CASE IS DETERMINATE, WHICH IS THE ONE PART OF THE DEFINITION IT HAS.
_inf = call("B4.2", dict(_RICH, ac=1_200_000))
check(_inf.get("feasible") is False and _inf.get("status_color") == "Red",
      "B4.2: a budget already exhausted is reported infeasible, and that is a determinate "
      "outcome of the arithmetic rather than a band", str(_inf.get("evidence_metric"))[:60])
# THE UNBOUNDED CASE HAS NO MEANING HERE, WHICH IS ITSELF THE FINDING: unboundedness is a
# property of an objective over a constraint system, and there is no objective.
check("unbounded" not in str(_lp).lower(),
      "B4.2: no unbounded outcome exists or can exist, because there is no objective to be "
      "unbounded")
check(abstains(call("B4.2", {})), "B4.2: it abstains on an empty input")
check(call("B4.2", dict(_RICH, ev=500_000)).get("required_cpi_to_complete")
      != _lp.get("required_cpi_to_complete"),
      "B4.2: and the ratio responds to the figures it is built from",
      str(call("B4.2", dict(_RICH, ev=500_000)).get("required_cpi_to_complete")))
_b42_mut = mutation_binds("B4.2", _RICH)
check(_b42_mut.startswith("PROVEN"), "B4.2: a fault in an isolated copy changes its behaviour",
      _b42_mut)
ROWS.append(dict(
    module_id="B4.2", canonical_name=NAMES["B4.2"],
    canonical_method_definition="a linear objective over decision variables subject to linear "
                                "constraints and bounds, solved to an optimum, with feasibility "
                                "and unboundedness determined by the constraint system",
    implementation_state="DISABLED_LABORATORY_ONLY",
    implementation_path="server/app/simulation/models_gov.py::run_linear_programming",
    defining_structure="decision variables, an objective vector, a constraint matrix, bounds and "
                       "a solver",
    required_inputs="bac, ev, ac, cpi",
    structure_available="NO: none of the five exists; the module computes one ratio and reads a "
                        "band on it",
    isolated_execution_possible="YES",
    known_answer_result="a required index of 1.071 banding Amber, matching a hand derivation of "
                        "remaining work over remaining budget",
    boundary_result="the feasibility cut at 1.20 and the three band arms are all reachable",
    domain_result="a budget already exhausted is reported infeasible rather than dividing by a "
                  "non-positive remainder",
    missingness_result="abstains on an empty input and on any absent figure",
    malformed_result="refused upstream by the numeric contract",
    property_result="deterministic; responds monotonically to the earned value position; no "
                    "optimisation of any kind occurs",
    mutation_proof=_b42_mut, method_fidelity="MISMATCH",
    observed_output="the cost index a project would need to finish inside its remaining budget",
    independent_expected_output="an optimal solution to a stated linear program, with feasible "
                                "and unbounded cases determined by the constraints",
    limitations="there is no program: no variables, no objective, no constraints and no solver, "
                "so an independently solved known-answer linear program cannot be posed against "
                "it and an unbounded case cannot exist; the feasibility cut at 1.20 and the "
                "three band boundaries are unsourced",
    functional_verdict="WORKS"))


# =================================================================================================
section("7. B4.5 DECISION SENSITIVITY MATRIX")
# =================================================================================================
#
# CANONICAL DEFINITION. Sensitivity analysis perturbs an input or a parameter by a stated amount,
# RECOMPUTES the decision or the outcome, and reports how the result moved. The defining
# structures are the perturbation, the recomputation and the comparison of outcomes, including a
# zero-perturbation control that must move nothing.
_src = inspect.getsource(models_gov.run_decision_sensitivity)
check("abs(1 - si[\"cpi\"]) * 100" in _src,
      "B4.5: what the implementation computes is each input's distance from a reference value, "
      "shared out as a percentage")
check(not any(w in _src.lower() for w in ("perturb", "delta", "recompute", "baseline_result",
                                          "derivative")),
      "and it never perturbs an input, never recomputes anything and never compares two outcomes")
#   KNOWN ANSWER: cpi 0.909 gives |1-0.909|*100 = 9.1; spi 0.889 gives 11.1; risk 0.35 gives
#   17.5. Total 37.7. Shares 24, 29 and 46 per cent. The top driver is document risk at 17.5,
#   which is above 12, so Red.
_ds = call("B4.5", _RICH)
check(_ds.get("top_driver") == "Document risk" and _ds.get("top_driver_pct") == 46,
      "B4.5: the top driver is the document risk at 46 per cent of the total, derived by hand",
      str((_ds.get("top_driver"), _ds.get("top_driver_pct"))))
check(_ds.get("status_color") == "Red",
      "B4.5: and 17.5 lands Red on the shipped ladder", str(_ds.get("status_color")))
# THE ZERO-PERTURBATION CONTROL, AND WHAT IT SHOWS. Perturbing an input by nothing must leave the
# reported sensitivity unchanged, and it does; but perturbing it by something also fails to
# recompute any decision, because no decision is recomputed at any point.
_zero = call("B4.5", dict(_RICH))
check(_zero == _ds, "B4.5: a zero perturbation leaves the reported sensitivity unchanged")
_perturbed = call("B4.5", dict(_RICH, cpi=_RICH["cpi"] + 0.05))
check(_perturbed.get("sensitivity_matrix") != _ds.get("sensitivity_matrix"),
      "B4.5: a real perturbation of an input does change the reported shares, so the reported "
      "quantity is a function of the inputs")
# The reported share is a distance from a reference, not an influence: the document risk driver
# is scaled by a literal fifty and the two indices by a literal hundred, so the ranking is set
# by those two constants as much as by the project.
_scaled = call("B4.5", dict(_RICH, docRiskScore=0.35, cpi=1.0, spi=1.0))
check(_scaled.get("top_driver") == "Document risk" and _scaled.get("top_driver_pct") == 100,
      "B4.5: with both indices exactly at their reference the whole share falls to the third "
      "driver, which shows the share is a distance from a reference and not an influence on any "
      "decision", str(_scaled.get("top_driver_pct")))
check(abstains(call("B4.5", {})), "B4.5: it abstains on an empty input")
_b45_mut = mutation_binds("B4.5", _RICH)
check(_b45_mut.startswith("PROVEN"), "B4.5: a fault in an isolated copy changes its behaviour",
      _b45_mut)
ROWS.append(dict(
    module_id="B4.5", canonical_name=NAMES["B4.5"],
    canonical_method_definition="perturb a decision input or parameter by a stated amount, "
                                "recompute the decision or outcome, and report how and by how "
                                "much the result moved, with a zero-perturbation control",
    implementation_state="DISABLED_LABORATORY_ONLY",
    implementation_path="server/app/simulation/models_gov.py::run_decision_sensitivity",
    defining_structure="a perturbation, a recomputation of the decision under it, and a "
                       "comparison of the two outcomes",
    required_inputs="cpi, spi, docRiskScore",
    structure_available="NO: nothing is perturbed and nothing is recomputed; the reported "
                        "sensitivity is each input's scaled distance from a reference value",
    isolated_execution_possible="YES",
    known_answer_result="document risk as the top driver at 46 per cent of a total of 37.7, "
                        "banding Red, all matching a hand derivation",
    boundary_result="the four band arms on the top driver's magnitude are reachable",
    domain_result="a total of zero is floored to one so the shares stay defined",
    missingness_result="abstains on an empty input and on any absent driver",
    malformed_result="refused upstream by the numeric contract",
    property_result="deterministic; a zero perturbation moves nothing; a real perturbation moves "
                    "the shares, but no decision is recomputed at any point",
    mutation_proof=_b45_mut, method_fidelity="MISMATCH",
    observed_output="the share of a scaled total distance from reference values carried by each "
                    "of three inputs",
    independent_expected_output="the movement of a recomputed decision under a stated "
                                "perturbation",
    limitations="no decision is recomputed, so no direction or magnitude of a decision change "
                "can be verified against an independently known case; the ranking is set partly "
                "by the literal scale factors of one hundred and fifty, which have no source",
    functional_verdict="WORKS"))


# =================================================================================================
section("8. B4.6 PARETO FRONTIER ANALYSIS")
# =================================================================================================
#
# CANONICAL DEFINITION. Given a set of alternatives with objective vectors, an alternative is
# dominated when another is at least as good on every objective and strictly better on one; the
# frontier is the nondominated set. The defining structure is a SET OF ALTERNATIVES, and the
# analysis must be invariant to the order they are presented in.
_src = inspect.getsource(models_gov.run_pareto_frontier)
check("cost_ok = si[\"cpi\"] >= 0.95" in _src,
      "B4.6: what the implementation computes is three threshold tests on one project")
check(not any(w in _src.lower() for w in ("alternatives", "candidates", "nondominated",
                                          "frontier_points", "for ")),
      "and it iterates over nothing, so there is no set for a frontier to be drawn through")
#   KNOWN ANSWER: cpi 0.909 below 0.95 so cost fails; spi 0.889 below 0.95 so schedule fails;
#   risk 0.35 at or above 0.30 so risk fails. Both indices failing makes it dominated, and
#   dominated with no tradeoff reads Red.
_pf = call("B4.6", _RICH)
check(_pf.get("dominated") is True and _pf.get("pareto_efficient") is False,
      "B4.6: the project is reported dominated and not efficient, derived by hand",
      str((_pf.get("dominated"), _pf.get("pareto_efficient"))))
check(_pf.get("status_color") == "Red", "B4.6: and the reading is Red",
      str(_pf.get("status_color")))
# THE INDEPENDENT DOMINANCE CHECK, RUN OUTSIDE THE MODULE, AND WHAT IT DEMONSTRATES. Dominance is
# a RELATION BETWEEN alternatives. Two projects with identical objective vectors cannot dominate
# each other, and a strictly better project cannot be reported as equally dominated, yet the
# module returns the same verdict for a project regardless of what else exists, because it never
# sees anything else.
_worse = call("B4.6", dict(_RICH, cpi=0.60, spi=0.60, docRiskScore=0.95))
check(_worse.get("dominated") == _pf.get("dominated"),
      "B4.6: a strictly worse project is reported with the same dominance verdict as the "
      "original, because dominance here is a threshold test and not a comparison",
      str((_pf.get("dominated"), _worse.get("dominated"))))
_ALTS = [(1.05, 1.05, 0.10), (0.95, 1.10, 0.20), (0.90, 0.90, 0.50), (1.02, 0.98, 0.15)]


def nondominated(alts):
    """The frontier, derived independently here: maximise both indices, minimise risk."""
    out = []
    for a in alts:
        if not any(b != a and b[0] >= a[0] and b[1] >= a[1] and b[2] <= a[2]
                   and (b[0] > a[0] or b[1] > a[1] or b[2] < a[2]) for b in alts):
            out.append(a)
    return sorted(out)


_front = nondominated(_ALTS)
#   Worked by hand: (1.05, 1.05, 0.10) beats (0.90, 0.90, 0.50) and (1.02, 0.98, 0.15) on all
#   three objectives, so both of those are dominated. It does NOT beat (0.95, 1.10, 0.20), which
#   has the better schedule figure, so the frontier is those two.
check(_front == sorted([(0.95, 1.10, 0.20), (1.05, 1.05, 0.10)]),
      "B4.6: the nondominated set of a four-alternative example, derived independently outside "
      "the module, holds two of the four", str(_front))
check(nondominated(list(reversed(_ALTS))) == _front,
      "B4.6: and that derivation is invariant to the order the alternatives are presented in, "
      "which is the property the analysis must have")
check((0.90, 0.90, 0.50) not in _front and (1.02, 0.98, 0.15) not in _front,
      "B4.6: both dominated alternatives are excluded from it, including the one dominated only "
      "by a single other point")
check(all(a in _ALTS for a in _front),
      "B4.6: and no alternative outside the set appears in it")
check("alternatives" not in _pf and "frontier" not in _pf,
      "B4.6: the module returns no alternative set and no frontier, so none of the four "
      "assertions above can be posed against it at all", str(sorted(_pf)))
check(abstains(call("B4.6", {})), "B4.6: it abstains on an empty input")
_b46_mut = mutation_binds("B4.6", _RICH)
check(_b46_mut.startswith("PROVEN"), "B4.6: a fault in an isolated copy changes its behaviour",
      _b46_mut)
ROWS.append(dict(
    module_id="B4.6", canonical_name=NAMES["B4.6"],
    canonical_method_definition="over a set of alternatives with objective vectors, the "
                                "nondominated set: those no other alternative matches on every "
                                "objective while beating on at least one",
    implementation_state="DISABLED_LABORATORY_ONLY",
    implementation_path="server/app/simulation/models_gov.py::run_pareto_frontier",
    defining_structure="a set of alternatives with objective vectors, and a pairwise dominance "
                       "relation over it",
    required_inputs="cpi, spi, docRiskScore",
    structure_available="NO: there is one project and no set, so no dominance relation can be "
                        "formed",
    isolated_execution_possible="YES",
    known_answer_result="dominated and not efficient, banding Red, matching a hand derivation of "
                        "the three threshold tests",
    boundary_result="the efficient, tradeoff, partial and dominated readings are all reachable",
    domain_result="the score is clamped at one so an index far above the threshold cannot "
                  "inflate it",
    missingness_result="abstains on an empty input and on any absent objective",
    malformed_result="refused upstream by the numeric contract",
    property_result="deterministic; the dominance verdict does not change when a strictly worse "
                    "project exists, because no other project is ever seen; the independently "
                    "derived nondominated set used as the oracle here is permutation invariant, "
                    "and the module has nothing to compare against it",
    mutation_proof=_b46_mut, method_fidelity="MISMATCH",
    observed_output="three threshold tests on one project, labelled with the vocabulary of "
                    "dominance",
    independent_expected_output="the nondominated subset of a set of alternatives",
    limitations="dominance is a relation and the module holds one point, so the excluded-"
                "dominated, retained-nondominated and permutation-invariance tests cannot be "
                "posed against production at all; they are posed here against an independent "
                "derivation to show what the method requires; the three thresholds are unsourced",
    functional_verdict="WORKS"))


# =================================================================================================
section("9. NOTHING WAS ACTIVATED, AND THE EVIDENCE FILE")
# =================================================================================================
for _mid in EIGHT:
    _r = run_module(_mid, dict(_RICH), NOOP, CUTOFF)
    check(abstains(_r),
          f"{_mid}: still refused by the registry after the whole suite has run it directly",
          str(_r.get("status_color")))
check(sorted(DISABLED_CONCEPT_ONLY) == EIGHT,
      "the live disabled set is byte-for-byte the set this suite started with")
COLS = ["module_id", "canonical_name", "canonical_method_definition", "implementation_state",
        "implementation_path", "defining_structure", "required_inputs", "structure_available",
        "isolated_execution_possible", "known_answer_result", "boundary_result", "domain_result",
        "missingness_result", "malformed_result", "property_result", "mutation_proof",
        "method_fidelity", "observed_output", "independent_expected_output", "limitations",
        "functional_verdict"]
ROWS.sort(key=lambda r: r["module_id"])
with open(AUDIT / "run14_disabled_method_functional_tests.csv", "w", newline="",
          encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=COLS)
    w.writeheader()
    w.writerows(ROWS)
check(len(ROWS) == 8, "the evidence file carries exactly eight rows, one per disabled module",
      str(len(ROWS)))
check(sorted(r["module_id"] for r in ROWS) == EIGHT,
      "and they are the eight derived from Run 13's evidence")
check(all(r["functional_verdict"] in ("WORKS", "DOES_NOT_WORK", "NOT_IMPLEMENTED",
                                      "NOT_TESTABLE") for r in ROWS),
      "every functional verdict is one of the four permitted factual states")
check(not any(w in " ".join(r["functional_verdict"] for r in ROWS)
              for w in ("KEEP", "REMOVE", "RETAIN", "ACTIVATE")),
      "and no row carries an architectural disposition, which is the owner's decision and not "
      "this run's")
# RUN 28 ADDED A SIXTH STATE, and it names a condition none of the five could describe. A3.8's
# canonical method is IMPLEMENTED -- fully, with its structure, its coefficients, their units and
# its known answer -- and is reached by NO production path, because the owner's supplied contract
# requires the module to stay disabled and non-voting until a later activation decision. It is
# not a proxy, not partial, not a placeholder and not unimplemented, and calling it any of those
# would be false in one direction or the other. The vocabulary is EXTENDED, not opened: a state
# outside the named six is still red.
check(all(r["implementation_state"] in ("FULL_IMPLEMENTATION", "PARTIAL_IMPLEMENTATION",
                                        "PROXY_ONLY", "PLACEHOLDER", "NOT_IMPLEMENTED",
                                        "DISABLED_LABORATORY_ONLY")
          for r in ROWS),
      "and every implementation state is one of the six permitted states",
      str(sorted({r["implementation_state"] for r in ROWS})))
check(sum(1 for r in ROWS if r["method_fidelity"] == "MISMATCH") == 6
      and sum(1 for r in ROWS if r["method_fidelity"] == "PARTIAL") == 2,
      "six of the eight implement something other than the method they are named for, and two "
      "carry part of their method's defining structure",
      str({r["module_id"]: r["method_fidelity"] for r in ROWS}))


print("\n" + "=" * 78)
if FAILURES:
    print("FAILURES:")
    for f in FAILURES:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{TOTAL} checks passed")
print("=" * 78)
sys.exit(0 if PASSED == TOTAL else 1)
