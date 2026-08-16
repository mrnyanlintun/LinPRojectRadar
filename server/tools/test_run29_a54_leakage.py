"""
RUN 29 CLOSURE -- THE A5.4 CATEGORY-10 LEAKAGE GUARD.

WHY THIS SUITE EXISTS. Run 29 found A5.4 Scenario Modeling returning a RECOMMENDED ACTION and its
expected cost from an actions-by-scenarios payoff matrix, and removed it, because the supplied
contract separates the two questions in its own words:

    Category 5 asks:  "What happens to the system under this condition?"
    Category 10 asks: "Which management intervention should be chosen?"

Removing the path also removed one of the two modules that exercised the reference-object leakage
controls, which Run 29 recorded as a coverage reduction rather than glossing it. This suite is the
sharper, contract-specific replacement the closure contract asks for: instead of testing the
decision object's split and version guards through a module that should not read a decision object
at all, it tests THE THING THAT ACTUALLY MATTERS -- that A5.4 cannot emit a Category-10 output by
any route.

WHAT A LEAK WOULD LOOK LIKE, enumerated rather than gestured at. A recommended action, a preferred
option, a decision ranking, an optimisation result, a participant recommendation object, or any
other key by which a reader could take a management decision out of a module whose question is
what happens under a condition.

THE GUARD IS PROVED ABLE TO FAIL. A recommendation object is deliberately reintroduced into an
isolated copy of the production function, the injection is confirmed by reading the mutated
module's output back, the named guard is observed RED for the intended reason, the fault is
restored and the guard observed GREEN again. Production is never mutated.
"""

from __future__ import annotations

import ast
import datetime
import pathlib
import sys
import textwrap
import types

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from app.simulation import models_doc as MD                     # noqa: E402
from app.simulation import registry as REG                      # noqa: E402
import run29_fixtures as FX                                     # noqa: E402

CUTOFF = datetime.date(2026, 6, 30)
RAND = lambda: 0.5  # noqa: E731

PASSED = 0
FAILED = 0
FAILURES: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> bool:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        FAILURES.append(label)
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))
    return ok


def head(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


# -------------------------------------------------------------------------------------------
# THE GUARD ITSELF, defined once so the suite and the fault injection read the same rule.
# -------------------------------------------------------------------------------------------

#: Result keys by which a Category-10 decision output could leave a Category-5 module. Names are
#: matched case-insensitively on the KEY, and the value-bearing check below also refuses a nested
#: object carrying any of them, so wrapping the recommendation one level down does not evade it.
DECISION_OUTPUT_KEYS = (
    "recommended_action", "recommendation", "preferred_option", "preferred_action",
    "decision_ranking", "ranked_actions", "best_action", "chosen_action", "optimal_action",
    "optimisation_result", "optimization_result", "expected_cost_delta", "worst_case_cost_delta",
    "actions_considered", "action_scenario_payoff", "decision_layer_state", "courses_of_action",
    "participant_recommendation", "advice", "should_do",
)

#: The reference-object keys whose presence would mean the module had read a decision problem.
DECISION_STRUCTURE_KEYS = ("reference_object", "reference_asset_version", "reference_split",
                           "scenarioDecisionStructure", "decisionMatrix")


def decision_leak(result: dict) -> list[str]:
    """
    Every route by which a Category-10 decision output could be leaving this result.

    Returns the offending keys. An empty list is the guard holding. Nested objects are walked, so
    a recommendation hidden one level down inside a scenario row is still found.
    """
    found: list[str] = []

    def walk(node, path: str) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                lowered = str(k).lower()
                if lowered in {n.lower() for n in DECISION_OUTPUT_KEYS} and v is not None:
                    found.append(f"{path}{k}")
                if lowered in {n.lower() for n in DECISION_STRUCTURE_KEYS} and v is not None:
                    found.append(f"{path}{k}")
                walk(v, f"{path}{k}.")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}{i}.")

    walk(result, "")
    return sorted(set(found))


def run_a54(si: dict, fn=None) -> dict:
    if fn is None:
        return REG.run_module("A5.4", si, RAND, CUTOFF)
    return fn(dict(si), RAND, CUTOFF)


# =================================================================================================
head("1. THE MODULE ANSWERS ITS OWN QUESTION AND COMPUTES")
# =================================================================================================

_ok = run_a54({"scenarioSet": FX.scenario_set()})
check(_ok.get("responses") == {"BASE": 5.0, "ADVERSE": 8.0, "RECOVERY": 4.0},
      "A5.4 evaluates the three coherent states through the governed response model and reports "
      "what happens under each", str(_ok.get("responses")))
check(not _ok.get("insufficient_data"),
      "so the guard below is read against a module that really produced a result, not against an "
      "abstention that would satisfy any leakage test trivially")


# =================================================================================================
head("2. NO CATEGORY-10 DECISION OUTPUT LEAVES IT, BY ANY ROUTE")
# =================================================================================================

_leaks = decision_leak(_ok)
check(not _leaks,
      "THE NAMED GUARD: no recommended action, preferred option, decision ranking, optimisation "
      "result, participant recommendation object or reference decision object appears anywhere "
      "in the result, at any depth", str(_leaks))
check(len(DECISION_OUTPUT_KEYS) >= 19 and len(DECISION_STRUCTURE_KEYS) >= 5,
      "and the guard enumerates the routes rather than testing one name",
      f"{len(DECISION_OUTPUT_KEYS)} output keys, {len(DECISION_STRUCTURE_KEYS)} structure keys")

# The retired path itself: a decision object must produce NO reading at all, so the module cannot
# be brought back to Category 10's question by supplying Category 10's structure.
_with_decision = run_a54({
    "bac": 1_000_000.0,
    "scenarioDecisionStructure": {
        "asset_version": "v", "split": "DEVELOPMENT", "decision_object_id": "D1",
        "evaluated_project_id": "P1", "reference_member_project_ids": ["P2"],
        "scenarios": [{"scenario_id": "S1", "probability": 0.6},
                      {"scenario_id": "S2", "probability": 0.4}],
        "outcomes": [{"action_id": "hold", "scenario_id": "S1", "cost_delta_usd": 0.0},
                     {"action_id": "hold", "scenario_id": "S2", "cost_delta_usd": 100.0},
                     {"action_id": "act", "scenario_id": "S1", "cost_delta_usd": 30.0},
                     {"action_id": "act", "scenario_id": "S2", "cost_delta_usd": 30.0}]}})
check(bool(_with_decision.get("insufficient_data")),
      "supplying a complete, well-formed decision problem produces NO reading, so the retired "
      "path cannot be reached by handing the module the structure it used to read",
      str(_with_decision.get("evidence_metric"))[:80])
check(not decision_leak(_with_decision),
      "and nothing leaks out of the abstention either", str(decision_leak(_with_decision)))

# Both together, which is the case a partial restoration would produce.
_both = run_a54({"scenarioSet": FX.scenario_set(), "bac": 1_000_000.0,
                 "scenarioDecisionStructure": {
                     "asset_version": "v", "split": "DEVELOPMENT", "decision_object_id": "D1",
                     "scenarios": [{"scenario_id": "S1", "probability": 1.0}],
                     "outcomes": [{"action_id": "a", "scenario_id": "S1",
                                   "cost_delta_usd": 1.0}]}})
check(_both.get("responses") == _ok.get("responses") and not decision_leak(_both),
      "and with BOTH structures present the module reads only the scenario set: the decision "
      "object changes nothing and leaks nothing", str(decision_leak(_both)))

# The source itself: the module must not even import the decision reader.
_src = textwrap.dedent(
    (ROOT / "server" / "app" / "simulation" / "models_doc.py").read_text(encoding="utf-8"))
_fn_src = "def run_scenario_modeling" + _src.split(
    "def run_scenario_modeling")[1].split("\ndef ")[0]
check("scenario_decision" not in _fn_src and "require_reference_object" not in _fn_src
      and "recommended_action" not in _fn_src,
      "and the production function's own source calls no decision reader and names no "
      "recommended action, so the absence is structural rather than incidental")
check("scenario_decision" not in _src,
      "nor does anything else in the module file import the decision reader any more")

# THE PARTICIPANT SURFACE. A Category-10 output reaching a participant is the harm this guards
# against, so the rendered sentence is checked too.
_sentence = str(_ok.get("evidence_metric") or "")
check("No state is recommended over any other" in _sentence,
      "and the sentence a reader sees says explicitly that no state is recommended over any "
      "other, so the boundary is stated to the reader rather than left to be inferred",
      _sentence[-90:])
for _word in ("should", "best option", "choose", "preferred", "optimal", "we advise"):
    check(_word not in _sentence.lower(),
          f"and it carries no {_word!r}, so no decision is implied in prose either",
          _sentence[:90])
# The disclaimer must not be the ONLY thing carrying the word, which would make the check above
# satisfiable by a sentence that also recommended something.
check(_sentence.lower().count("recommend") == 1,
      "and the word appears exactly once, in that disclaimer, so the sentence cannot be both "
      "disclaiming and recommending", str(_sentence.lower().count("recommend")))


# =================================================================================================
head("3. FAULT 6: THE GUARD IS PROVED ABLE TO FAIL")
# =================================================================================================

# THE INJECTION. The production function is compiled into an ISOLATED namespace with one added
# statement: a recommendation object put back onto the result, which is exactly the Category-10
# output Run 29 removed. Production is untouched; the mutant is a separate function object.
print()
print("--- FAULT 6: a recommendation object reintroduced into A5.4")

_green_before = check(not decision_leak(run_a54({"scenarioSet": FX.scenario_set()})),
                      "F6 GREEN BEFORE: the live module leaks nothing")

_tree = ast.parse(_fn_src)
_func = _tree.body[0]


class _InjectRecommendation(ast.NodeTransformer):
    """Put a Category-10 recommendation back onto the returned object."""

    def __init__(self) -> None:
        self.count = 0

    def visit_Return(self, node):  # noqa: N802
        if isinstance(node.value, ast.Call):
            for kw in list(node.value.keywords):
                if kw.arg == "scenarios":
                    self.count += 1
                    node.value.keywords.append(
                        ast.keyword(arg="recommended_action",
                                    value=ast.Constant(value="ADVERSE")))
                    node.value.keywords.append(
                        ast.keyword(arg="decision_ranking",
                                    value=ast.Constant(value="ADVERSE,BASE,RECOVERY")))
                    break
        return node


_tr = _InjectRecommendation()
_mutant_tree = ast.fix_missing_locations(_tr.visit(_tree))
check(_tr.count == 1,
      "F6 INJECTION APPLIED: the recommendation keywords were added to the one return the "
      "function makes when it computes", f"{_tr.count} site(s)")

_ns = dict(vars(MD))
exec(compile(_mutant_tree, "<mutated run_scenario_modeling>", "exec"), _ns)  # noqa: S102
_mutant = _ns["run_scenario_modeling"]
check(_mutant is not MD.run_scenario_modeling,
      "and the mutant is a genuinely different function object from the production one")

_mutant_out = run_a54({"scenarioSet": FX.scenario_set()}, _mutant)
check(_mutant_out.get("recommended_action") == "ADVERSE"
      and _mutant_out.get("decision_ranking") == "ADVERSE,BASE,RECOVERY",
      "F6 INJECTION CONFIRMED: the mutated module really does emit a recommended action and a "
      "decision ranking, read back off its own output rather than assumed",
      str(_mutant_out.get("recommended_action")))
check(_mutant_out.get("responses") == _ok.get("responses"),
      "and it is otherwise the same module: the scenario responses are unchanged, so what the "
      "guard catches below is the leak and not an unrelated failure")

_mutant_leaks = decision_leak(_mutant_out)
_red = check(_mutant_leaks == ["decision_ranking", "recommended_action"],
             "F6 RED FOR THE INTENDED REASON: the named guard reports exactly the two "
             "Category-10 keys that were reintroduced, and no others", str(_mutant_leaks))

# A nested leak, because a real regression would more likely hide one level down.
_nested = dict(_ok)
_nested["scenarios"] = [dict(s) for s in _ok["scenarios"]]
_nested["scenarios"][0]["recommendation"] = "take the recovery plan"
check(decision_leak(_nested) == ["scenarios.0.recommendation"],
      "F6 RED ON A NESTED LEAK TOO: a recommendation hidden inside a scenario row is found, so "
      "wrapping it one level down does not evade the guard", str(decision_leak(_nested)))

# RESTORE and re-observe. Nothing was ever written to production, and that is asserted rather
# than assumed by re-reading the file and re-running the live function.
_after = run_a54({"scenarioSet": FX.scenario_set()})
_green_after = check(not decision_leak(_after) and _after == _ok,
                     "F6 RESTORED: the live module leaks nothing and returns exactly what it "
                     "returned before the injection")
_src_after = (ROOT / "server" / "app" / "simulation" / "models_doc.py").read_text(encoding="utf-8")
check(_src_after == _src and "recommended_action" not in _src_after,
      "and the production file on disk is byte-identical to what it was before the injection, "
      "read back from disk rather than assumed")


print()
print("=" * 78)
if FAILURES:
    print(f"{len(FAILURES)} check(s) did not hold:")
    for f in FAILURES:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
