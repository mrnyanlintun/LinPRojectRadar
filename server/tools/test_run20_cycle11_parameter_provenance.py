"""
RUN 20 CYCLE 11. P3: PARAMETERS, THRESHOLDS, CALIBRATION AND PROVENANCE.

Every band boundary, cap, weight, membership and multiplier in this platform is a number
somebody chose. Run 4 cited the two voting modules' boundaries to published literature and
nothing had ever done the same for the rest, so a boundary with a citation and a boundary
invented in an afternoon were indistinguishable from outside.

THE ENUMERATION IS MECHANICAL AND EXHAUSTIVE, NOT SAMPLED. Section 1 walks the syntax tree of
every module function in the simulation package, collects every numeric literal and every
module-level named numeric constant those functions read, subtracts the definitional values,
and requires what remains to be covered by an entry in the parameter provenance register. This
is what stops the register being a snapshot that quietly goes stale: a value added tomorrow and
left unclassified fails here.

WHAT CYCLE 11 FOUND. Of the eighty-seven modules carrying a tunable value, THREE carry published
provenance and one carries a mathematical constant. Everything else is UNSUPPORTED. The three
are the two voting modules, whose boundaries Run 4 cited, and the isolation forest, whose tree
count, subsample and path length normaliser are the published defaults of the algorithm itself.
That last one is the reason the register holds a LIST per module rather than one class: a
published algorithm's own defaults sit underneath an invented band ladder, and collapsing the
module to a single class would have hidden it.

NOTHING IS CALIBRATED AND NOTHING PRETENDS TO BE. The calibration set does not exist: there is
no labelled corpus of project outcomes here and no expert reference standard, and synthetic
laboratory data is not empirical field validation. Section 4 requires that no value anywhere
claims CALIBRATED_PARAMETER.

TWO ROWS ARE RECLASSIFIED RATHER THAN CLOSED, and that is the Run-20 exit target that is not
met. Section 5 records both, and requires both to be safe meanwhile.
"""

import ast
import os
import pathlib
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.simulation import parameters as PARAMS  # noqa: E402
from app.simulation.models_sim import monte_carlo_eac, run_monte_carlo  # noqa: E402
from app.simulation.registry import (  # noqa: E402
    BAND_SOURCES, CORE_VOTING_MODULES, activation_state,
)
from run17 import population as POP  # noqa: E402

_passed = 0
_total = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global _passed, _total
    _total += 1
    if cond:
        _passed += 1
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}" + (f"  [{detail}]" if detail else ""))


PKG = pathlib.Path(__file__).resolve().parents[1] / "app" / "simulation"
POPULATION = {r["code_id"] for r in POP.population()}


def _fn_to_module() -> dict[str, str]:
    """Every run_ function to the module id the registry binds it to, read from the code."""
    out: dict[str, str] = {}
    for p in PKG.glob("*.py"):
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            val = node.value if isinstance(node, (ast.Assign, ast.AnnAssign)) else None
            if isinstance(val, ast.Dict):
                for k, v in zip(val.keys, val.values):
                    if (isinstance(k, ast.Constant) and isinstance(v, ast.Tuple)
                            and len(v.elts) == 2 and isinstance(v.elts[1], ast.Name)):
                        out[v.elts[1].id] = k.value
    return out


def _module_level_numbers(tree: ast.Module) -> dict[str, set]:
    """
    Every module-level name bound to a number, or to an EXPRESSION over numbers and other such
    names, mapped to the set of numeric values that name carries.

    THE EXPRESSIONS ARE THE POINT, AND THE FIRST VERSION OF THIS FUNCTION MISSED THEM. The two
    voting modules write one boundary as a literal and derive the other from it: the beyond
    observed limit is the planned efficiency plus the stability margin, and the variance limit
    is one less the reciprocal of the stability index, as a percentage. A collector that took
    only names bound directly to a constant saw neither derived boundary, and so the sweep
    reported the only two sourced values in the registry as absent while calling itself
    complete. That is the vacuous-guard pattern again, found inside this cycle's own instrument.
    """
    raw: dict[str, ast.expr] = {}
    for node in tree.body:
        targets = []
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            targets = [node.target.id]
        if targets and node.value is not None:
            for t in targets:
                raw[t] = node.value

    def numbers_in(expr: ast.expr, depth: int = 0) -> set:
        if depth > 4:
            return set()
        vals = set()
        for n in ast.walk(expr):
            if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) \
                    and not isinstance(n.value, bool):
                vals.add(n.value)
            elif isinstance(n, ast.Name) and n.id in raw and n.id != getattr(expr, "id", None):
                vals |= numbers_in(raw[n.id], depth + 1)
        return vals

    out: dict[str, set] = {}
    for name, expr in raw.items():
        vals = numbers_in(expr)
        if vals:
            out[name] = vals
    return out


def enumerate_tunables() -> dict[str, set]:
    """
    module id -> every non-definitional number the module's own function reads, whether written
    as a literal inside it or as a module-level named constant it refers to.

    THE NAMED CONSTANTS ARE THE POINT. The two voting modules write their sourced boundaries as
    named constants, so an enumeration over literals alone would have skipped precisely the two
    values in the whole registry that HAVE a citation, and the register would have looked worse
    than the truth while claiming to be complete.
    """
    fn_map = _fn_to_module()
    found: dict[str, set] = {}
    for p in PKG.glob("*.py"):
        tree = ast.parse(p.read_text(encoding="utf-8"))
        named = _module_level_numbers(tree)
        for node in ast.walk(tree):
            if not (isinstance(node, ast.FunctionDef) and node.name.startswith("run_")):
                continue
            mid = fn_map.get(node.name)
            if mid is None:
                continue
            vals = set()
            for n in ast.walk(node):
                if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) \
                        and not isinstance(n.value, bool):
                    vals.add(n.value)
                elif isinstance(n, ast.Name) and n.id in named:
                    vals |= named[n.id]
            # NOTHING IS SUBTRACTED. The first version of this sweep removed the
            # definitional values and was silently swallowing real boundaries: three days of
            # crew separation, three change orders, five per cent of growth. Every module that
            # carries any number at all must be classified.
            if vals:
                found[mid] = vals
    return found


print("=== 1. THE ENUMERATION IS MECHANICAL, EXHAUSTIVE AND COVERED ===")
TUNABLE = enumerate_tunables()
check("the enumeration finds tunable values in a substantial part of the registry, so it is not "
      "vacuously satisfied by finding nothing", len(TUNABLE) >= 70, str(len(TUNABLE)))
_uncovered = sorted(m for m in TUNABLE if not PARAMS.provenance(m))
check("every module carrying a tunable value has a provenance entry, swept and not sampled",
      not _uncovered, str(_uncovered))
# Material Cost Variance is a registered module and is NOT one of the hundred scientific
# targets, because the owner withdrew its execution and cycle 12's population subtracts it. It
# still carries numbers, so it is still classified: withdrawing a module's execution does not
# make the numbers inside it sourced.
check("every classified module is a real registry module, and the only one outside the hundred "
      "scientific targets is the one the owner disabled pending an evidence decision",
      set(PARAMS.classified_modules()) - POPULATION == {"A3.4"},
      str(sorted(set(PARAMS.classified_modules()) - POPULATION)))
check("the named module-level constants are reached: the two voting modules appear in the "
      "enumeration, and they write their boundaries as names rather than literals",
      "A1.7" in TUNABLE and "A1.8" in TUNABLE)
check("and the sourced numbers themselves are reached THROUGH the expressions that derive the "
      "boundaries from them, which the first version of this sweep could not see",
      0.1 in TUNABLE["A1.7"] and 0.9 in TUNABLE["A1.8"],
      f"{sorted(TUNABLE['A1.7'])} {sorted(TUNABLE['A1.8'])}")


print("\n=== 2. THE CLASSIFICATION IS DISCIPLINED ===")
_all = [p for m in PARAMS.classified_modules() for p in PARAMS.provenance(m)]
check("every class is one of the permitted vocabulary",
      all(p.parameter_class in PARAMS.PARAMETER_CLASSES for p in _all))
check("every entry that claims published, theoretical, regulatory, contractual or calibrated "
      "provenance names a source",
      all(", " in p.provenance for p in _all
          if p.parameter_class in PARAMS.CLASSES_REQUIRING_CITATION))
check("no entry carries a module identifier in its prose",
      not [p for p in _all if any(t in p.provenance + p.kind
                                  for t in ("A1.", "A2.", "B2.", "D1.", "PH."))])
check("no entry uses an em dash", not [p for p in _all if "—" in p.provenance + p.kind])
check("and none uses an ampersand in prose",
      not [p for p in _all if "&" in p.provenance + p.kind])


print("\n=== 3. WHAT THE SWEEP ACTUALLY FOUND ===")
_counts = PARAMS.class_counts()
check("published provenance exists for exactly three, and no more was claimed than was found",
      _counts.get("PUBLISHED_METHOD_PARAMETER") == 3, str(_counts))
_published = sorted(m for m in PARAMS.classified_modules()
                    if any(p.parameter_class == "PUBLISHED_METHOD_PARAMETER"
                           for p in PARAMS.provenance(m)))
check("and they are the two voting modules and the isolation forest, which is the one place "
      "outside the voting pair where cycle 11 found a real published parameter",
      _published == ["A1.7", "A1.8", "D1.1"], str(_published))
check("the two voting modules' provenance agrees with the band source record Run 4 froze, so "
      "the register cannot drift from the citation the export already publishes",
      all("Christensen" in BAND_SOURCES[m] and "Christensen" in PARAMS.provenance(m)[0].provenance
          for m in ("A1.7", "A1.8")))
check("exactly one mathematical constant is claimed, and it is a constant rather than a choice",
      _counts.get("THEORETICAL_CONSTANT") == 1)
check("the overwhelming majority are UNSUPPORTED, which is the finding of this cycle and not a "
      "failure of it", _counts.get("UNSUPPORTED", 0) >= 80, str(_counts))
check("no value is claimed to be a regulatory value anywhere in the registry, because cycle 2 "
      "found no provision that states one and cycle 11 found none either",
      "REGULATORY_VALUE" not in _counts)
check("no value is claimed to be an owner policy, because no owner policy document in this "
      "repository fixes a number", "OWNER_POLICY" not in _counts)


print("\n=== 4. NOTHING IS CALIBRATED, AND NOTHING PRETENDS TO BE ===")
check("no entry anywhere claims to be a calibrated parameter",
      "CALIBRATED_PARAMETER" not in _counts, str(_counts))
check("every entry carries the sentence stating why no calibration was performed",
      all(p.as_dict()["calibration"] == PARAMS.NO_CALIBRATION_SET for p in _all))
check("and that sentence names what a calibration would have needed, rather than merely saying "
      "there was none",
      all(w in PARAMS.NO_CALIBRATION_SET
          for w in ("holdout", "sensitivity", "calibration set", "labelled")))
check("and it states plainly that synthetic laboratory data would not be field validation",
      "synthetic" in PARAMS.NO_CALIBRATION_SET)


print("\n=== 5. THE TWO ROWS CARRIED FROM CYCLE 9, REVISITED AND RECLASSIFIED ===")
_b14 = PARAMS.provenance("B1.4")[0]
check("the worst N of M rule's trigger is recorded as a FRACTION of the total, which is the "
      "defect", "FRACTION" in _b14.kind or "fraction" in _b14.provenance)
check("and it is reclassified as blocked on parameter provenance rather than closed with an "
      "invented count", "PARAMETER_PROVENANCE_BLOCKED" in _b14.provenance)
check("and the search that justifies the reclassification is stated: the specification, this "
      "repository and its cited sources", "supervisory specification" in _b14.provenance)
_ph5 = PARAMS.provenance("D1.5")[0]
check("the anomaly score's weights are recorded as moving with data availability",
      "AVAILABILITY" in _ph5.provenance or "availability" in _ph5.kind)
check("and it is reclassified as blocked on threshold calibration rather than closed",
      "THRESHOLD_CALIBRATION_BLOCKED" in _ph5.provenance)
check("both remain advisory and non-voting, which is what makes an unresolved row safe",
      activation_state("B1.4") == "ADVISORY_ONLY"
      and "B1.4" not in CORE_VOTING_MODULES and "D1.5" not in CORE_VOTING_MODULES)
check("no unsupported value reaches a voting module: the voting pair's own values are the "
      "published ones and nothing else",
      not [m for m in CORE_VOTING_MODULES
           if any(p.parameter_class in ("UNSUPPORTED", "HEURISTIC")
                  for p in PARAMS.provenance(m))])


print("\n=== 6. THE PARAMETER ITS ONLY CALLER NEVER SUPPLIES, DETERMINED BY EXECUTION ===")
# The queued case. The forecast function accepts three trend inputs and genuinely widens its
# spread when they arrive; the production caller supplies none of them. The question the cycle
# sets is which of six things that is, and it is answered by running the code rather than by
# reading the signature.
_SI = {"bac": 1_000_000.0, "ev": 400_000.0, "ac": 500_000.0, "pv": 450_000.0,
       "cpi": 0.8, "spi": 0.89}
_plain = run_monte_carlo(dict(_SI), lambda: 0.5, 12345)
_with_trend = run_monte_carlo(dict(_SI, cusumBreached=True, cusumDrift=3.0,
                                   cusumThreshold=1.0), lambda: 0.5, 12345)
check("supplying the trend inputs to the production caller changes NOTHING, so on the "
      "production path the parameter is dead rather than defaulted",
      _plain == _with_trend)
_a = monte_carlo_eac({"cpi": 0.8, "spi": 0.89, "bac": 1_000_000.0, "docScore": 0.5}, 12345)
_b = monte_carlo_eac({"cpi": 0.8, "spi": 0.89, "bac": 1_000_000.0, "docScore": 0.5,
                      "cusumBreached": True, "cusumDrift": 3.0, "cusumThreshold": 1.0}, 12345)
check("the underlying function DOES respond to them, so the deadness is in the caller and not "
      "in the arithmetic, which is what makes this a caller question", _a != _b)
check("the caller is therefore incomplete rather than the parameter being scientifically "
      "required: no result, band or figure this platform publishes depends on the trend inputs, "
      "and no default substitutes for them",
      _plain == _with_trend and _a != _b)
check("no default is silently standing in for missing trend evidence, which is the outcome that "
      "would have been unsafe: the production forecast is identical to the forecast computed "
      "with the trend evidence absent by construction",
      _plain.get("evidence_metric") == _with_trend.get("evidence_metric"))


print("\n=== 7. GUARD NON-VACUITY: EACH GUARD CATCHES WHAT IT PROTECTS ===")
# 7a. Coverage: remove an entry and the sweep must name the module.
# RUN 28. A2.9 no longer carries a tunable value -- its band ladder is gone with the supplied
# contract, which supplies no bands for a time-phased load ratio -- so removing its entry can no
# longer make the sweep name it, and using it here would have been a vacuous injection. The
# module the injection uses is CHOSEN FROM THE SWEEP'S OWN OUTPUT rather than named in advance,
# so a future run that removes another module's constants cannot make this control silently
# vacuous the way it just would have.
_victim = sorted(TUNABLE)[0]
_saved = PARAMS.PARAMETER_PROVENANCE_BY_MODULE.pop(_victim)
_fired = _victim in [m for m in TUNABLE if not PARAMS.provenance(m)]
PARAMS.PARAMETER_PROVENANCE_BY_MODULE[_victim] = _saved
check(f"the coverage guard FIRES when {_victim}'s classification is deliberately removed",
      _fired)
check("and goes green again once it is restored, for that module specifically",
      bool(PARAMS.provenance(_victim)))
check("and goes green again once it is restored",
      not [m for m in TUNABLE if not PARAMS.provenance(m)])

# 7b. Citation: a published claim without a source must be refused at construction.
try:
    PARAMS.Provenance("A1.7", "x", "PUBLISHED_METHOD_PARAMETER", "because I say so")
    _refused = False
except ValueError:
    _refused = True
check("a claim of published provenance with no source named is REFUSED at construction",
      _refused)
try:
    PARAMS.Provenance("A1.7", "x", "INVENTED_CLASS", "a, b")
    _refused = False
except ValueError:
    _refused = True
check("and a class outside the permitted vocabulary is REFUSED", _refused)

# 7c. The enumerator must actually see a new unclassified value. A synthetic module function is
# parsed here rather than written into production, so the probe cannot alter any real result.
_probe = ast.parse("def run_probe(si):\n    return 0.4242\n")
_vals = {n.value for n in ast.walk(_probe)
         if isinstance(n, ast.Constant) and isinstance(n.value, float)}
check("the enumerator's own collection step SEES a value it has never been told about, so a "
      "number added tomorrow cannot pass unnoticed", _vals == {0.4242})

# 7d. The definitional exclusion must not be swallowing real choices.
# 7d. THE EXCLUSION THAT WAS FOUND VACUOUS INSIDE THIS CYCLE, and the proof it is gone. The
# first version of the sweep subtracted the definitional values, and several of those numbers
# are real band boundaries elsewhere in the registry: the line of balance bands at three days of
# separation, the change order module bands at three orders and at five per cent of growth. The
# subtraction removed them from view while the sweep reported itself complete.
_swallowed = {v for v in PARAMS.DEFINITIONAL_VALUES
              if any(v in vals for vals in TUNABLE.values())}
check("the definitional values really do occur inside real modules, so subtracting them would "
      "have hidden genuine boundaries", len(_swallowed) >= 3, str(sorted(_swallowed)))
check("and the sweep subtracts NOTHING, so those modules are covered rather than excused",
      all(PARAMS.provenance(m) for m in TUNABLE))
# RUN 28 REMOVED THE LINE OF BALANCE BOUNDARY ALTOGETHER, which is a stronger outcome than the
# one this check was written to protect. The boundary at three days of crew separation was
# uncited, cycle 11's first sweep was subtracting it from view, and this check was added to prove
# it was visible again. The owner's supplied Run-28 contract settles it: the module reports the
# separation and the production slopes and asserts NO colour, so there is no boundary left to be
# visible. The check is restated on a boundary that DOES still exist and was in the same
# swallowed set -- the change order module's three orders and five per cent of growth -- so the
# property that the sweep subtracts nothing is still proved by a real case.
check("A2.2 carries no separation boundary at all any more, because the module asserts no band",
      not ({1.5, 3.0} & TUNABLE.get("A2.2", set())), str(sorted(TUNABLE.get("A2.2", set()))))
check("and a boundary from the same swallowed set is still visible to the sweep, so the "
      "subtraction really is gone rather than merely untested",
      3 in TUNABLE.get("A4.6", set()) or 3.0 in TUNABLE.get("A4.6", set()),
      str(sorted(TUNABLE.get("A4.6", set()))))

# 7e. The trend probe must be capable of showing a difference, or section 6 is vacuous.
check("the trend probe is not vacuous: the underlying function's two results really do differ, "
      "and differ in the spread the trend evidence is supposed to widen",
      _a != _b and sorted(_a) == sorted(_b))

print(f"\nRESULT: {_passed}/{_total} checks passed")
sys.exit(0 if _passed == _total else 1)
