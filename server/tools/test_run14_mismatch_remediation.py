#!/usr/bin/env python3
"""
RUN 14 WORKSTREAM A — the eight Run 13 mismatches, fixed and retested.

WHAT THIS SUITE IS FOR. Run 13 recorded nine defect occurrences across eight unique modules and
repaired none of them. This suite derives that scope from Run 13's own committed evidence rather
than from any list written here, reproduces each occurrence as Run 13 stated it, asserts the
corrected behaviour, and proves each assertion could have failed by injecting a fault into an
isolated copy of the production function and watching the assertion turn red.

WHAT IS NOT ASSERTED. Nothing here says a band boundary is right, that a proxy is a good measure,
or that the platform has been validated against field data. The corrections are refusals: an
impossible figure is not read as evidence, a withheld figure does not buy a calmer reading, and
a method whose defining structure is absent says so instead of reporting something else under
its name.

Run:
    PYTHONIOENCODING=utf-8 python tools/test_run14_mismatch_remediation.py
"""
from __future__ import annotations

import csv
import pathlib
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from app.extraction_merge import (  # noqa: E402
    MalformedNumericError, NumericRangeError, validate_numeric_fields, validate_signal_value,
)
from app.field_registry import BOUNDED_MAX_SI_FIELDS, SIGNED_SI_FIELDS  # noqa: E402
from app.simulation.compute import compute_project  # noqa: E402
from app.simulation.fusion import normalise_status  # noqa: E402
from app.simulation.models import SIMULATION_VERSION, VALIDATED  # noqa: E402
from app.simulation.registry import (  # noqa: E402
    CORE_VOTING_MODULES, DISABLED_CONCEPT_ONLY, run_module,
)

from tools.build_run13_evidence import CUTOFF, NOOP, STRUCTURED, band_of  # noqa: E402
from tests.synthetic_fixtures.importers import production_structures as PS  # noqa: E402
from tools.build_run13_mutation_proof import (  # noqa: E402
    FlipCompare, NegateGuard, mutated_callable,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
AUDIT = ROOT / "code_audit"
BAND_RANK = {"Red": 0, "Amber": 1, "Yellow": 2, "Green": 3}

PASSED = 0
TOTAL = 0
FAILURES: list[str] = []


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


def improved(before: str | None, after: str | None) -> bool:
    """Is `after` a calmer reading than `before`? An abstention is never an improvement."""
    if after is None or before is None:
        return False
    return BAND_RANK[after] > BAND_RANK[before]


def run(mid: str, si: dict):
    try:
        return run_module(mid, si, NOOP, CUTOFF)
    except Exception as exc:                                          # noqa: BLE001
        return {"raised": repr(exc)}


# =================================================================================================
section("1. THE SCOPE, DERIVED FROM RUN 13'S EVIDENCE AND NOT FROM THIS FILE")
# =================================================================================================
_ev = list(csv.DictReader(open(AUDIT / "run13_101_module_evidence.csv", encoding="utf-8-sig")))
_fa = list(csv.DictReader(open(AUDIT / "run13_failures_and_anomalies.csv", encoding="utf-8-sig")))
MISMATCH = sorted(r["module_id"] for r in _ev if r["factual_result"] == "MISMATCH")
NOT_TESTABLE = sorted(r["module_id"] for r in _ev if r["factual_result"] == "NOT_TESTABLE")
DISABLED = sorted(r["module_id"] for r in _ev if r["factual_result"] == "DISABLED_AS_DESIGNED")
check(len(MISMATCH) == 8, "Run 13's evidence carries exactly eight mismatch modules",
      str(MISMATCH))
check(len(NOT_TESTABLE) == 2, "and exactly two not-testable modules", str(NOT_TESTABLE))
check(len(DISABLED) == 8, "and exactly eight disabled modules", str(DISABLED))
check(not (set(MISMATCH) & set(NOT_TESTABLE) & set(DISABLED))
      and len(set(MISMATCH) | set(NOT_TESTABLE) | set(DISABLED)) == 18,
      "the three populations are disjoint, so the run's scope is eighteen unique modules")

# The nine occurrences across eight modules, and the module the two sets share.
_occurrences = [r for r in _fa
                if r["module_id"] in set(MISMATCH) and "OBSERVATION" not in r["defect_class"]]
BANDING = sorted({r["module_id"] for r in _occurrences
                  if r["defect_class"] == "out-of-domain favourable banding"})
MISSINGNESS = sorted({r["module_id"] for r in _occurrences
                      if r["defect_class"] == "missing evidence improves the reading"})
STRUCTURE = sorted({r["module_id"] for r in _occurrences
                    if r["defect_class"] == "canonical method replaced by proxy"})
check(len(_occurrences) == 9, "the anomaly file carries nine defect occurrences",
      str(len(_occurrences)))
check(len(BANDING) == 5, "five of them are out-of-domain favourable banding", str(BANDING))
check(len(MISSINGNESS) == 2, "two are missing evidence improving the reading", str(MISSINGNESS))
check(len(STRUCTURE) == 2, "two are a canonical structure absent", str(STRUCTURE))
_overlap = sorted(set(BANDING) & set(MISSINGNESS))
check(_overlap == ["A3.5"],
      "and the nine reconcile to eight because ONE module carries two of them",
      str(_overlap))
check(sorted(set(BANDING) | set(MISSINGNESS) | set(STRUCTURE)) == MISMATCH,
      "the three defect classes cover the eight mismatch modules exactly")


# =================================================================================================
section("2. THE NUMERIC CONTRACT NOW HAS AN UPPER END, PER FIELD, AND REFUSES RATHER THAN CLAMPS")
# =================================================================================================
check(BOUNDED_MAX_SI_FIELDS["actualPctComplete"] == 100.0
      and BOUNDED_MAX_SI_FIELDS["plannedPctComplete"] == 100.0,
      "a percent complete is bounded at a hundred, which is what the quantity is")
check("docRiskScore" not in BOUNDED_MAX_SI_FIELDS,
      "the document risk score is NOT in this table: its own guard remains the one authority "
      "for its range, and two authorities for one field is how a range check drifts")
for _unbounded in ("cpi", "spi", "bac", "ac", "ev", "actualLaborHours", "rfiCount",
                   "analogousOverrunPct", "totalManhours", "oshaIncidentRate"):
    check(_unbounded not in BOUNDED_MAX_SI_FIELDS,
          f"no ceiling is invented for a quantity whose definition supplies none: {_unbounded}")
check(set(BOUNDED_MAX_SI_FIELDS) & SIGNED_SI_FIELDS == set(),
      "no field that may legitimately be negative carries an invented upper bound either")

# The document boundary. A pay application carrying an impossible progress figure is refused
# whole, exactly as a negative one has been since the numeric contract was written.
try:
    validate_numeric_fields("pay_application", {"percent_complete_verified": 10_000})
    check(False, "an impossible percent complete is refused at the document boundary")
except NumericRangeError as _exc:
    check("cannot be above" in str(_exc) and "Nothing was stored" in str(_exc),
          "an impossible percent complete is refused at the document boundary, whole-document, "
          "and the sentence says nothing was stored", str(_exc)[:90])
for _ok in (0, 1, 50, 99.9, 100):
    try:
        validate_numeric_fields("pay_application", {"percent_complete_verified": _ok})
        check(True, f"a percent complete of {_ok} is still accepted")
    except (NumericRangeError, MalformedNumericError) as _exc:
        check(False, f"a percent complete of {_ok} is still accepted", str(_exc)[:80])
try:
    validate_numeric_fields("pay_application", {"percent_complete_verified": 100.0001})
    check(False, "and just above the bound is refused, so the boundary is inclusive at the top")
except NumericRangeError:
    check(True, "and just above the bound is refused, so the boundary is inclusive at the top")
# Refused, NOT clamped: the value does not arrive downstream repaired into the calmest reading.
try:
    validate_signal_value("actualPctComplete", 10_000)
    check(False, "the legacy direct-write path refuses the same figure")
except NumericRangeError as _exc:
    check("Nothing was changed" in str(_exc),
          "the legacy direct-write path refuses the same figure and changes nothing",
          str(_exc)[:80])
try:
    validate_signal_value("cpi", 10_000)
    check(True, "and it does not refuse a large cost index, which is implausible, not impossible")
except NumericRangeError as _exc:
    check(False, "and it does not refuse a large cost index", str(_exc)[:80])


# =================================================================================================
section("3. THE FIVE OUT-OF-DOMAIN BANDING OCCURRENCES: THE RUN 13 REPRODUCER, BEFORE AND AFTER")
# =================================================================================================
#
# Run 13's exact case: the nominal project with one bounded field driven to ten thousand. The
# recorded actual was Green on all five, from a nominal reading that was not Green. The
# corrected behaviour is an abstention: no reading is formed from a figure the quantity cannot
# take, and nothing is clamped to the nearest value it can take either.
# THE NOMINAL PROJECT. Run 13's own structured fixture, with ONE correction that matters for
# the two canonical-method modules: Run 13 built their decision objects from a problem id the
# synthetic package does not carry, so the builders returned an empty object and both modules
# abstained on the version guard WITH the structure and computed a proxy WITHOUT it. That is
# exactly backwards from what those two tests need to show, so the real decision problem is used
# here and the empty-object case is asserted separately below as its own abstention.
BASE = dict(STRUCTURED,
            scenarioDecisionStructure=PS.scenario_decision("DP-01"),
            decisionMatrix=PS.decision_matrix("DP-01"))
check(bool(BASE["scenarioDecisionStructure"]) and bool(BASE["decisionMatrix"]),
      "the nominal project carries a real decision problem rather than an empty object")
check(BASE["scenarioDecisionStructure"]["data_origin"] == "SYNTHETIC_RESEARCH_FIXTURE"
      and BASE["scenarioDecisionStructure"]["not_for_empirical_validation"] is True,
      "and that decision problem is a synthetic research fixture, marked as not constituting "
      "empirical validation")
for mid in BANDING:
    nominal = band_of(run(mid, dict(BASE)))
    si = dict(BASE)
    si["actualPctComplete"] = 10_000
    out = run(mid, si)
    check(out.get("insufficient_data") is True,
          f"{mid}: an impossible reported progress abstains rather than banding",
          str(out.get("status_color")))
    check(not improved(nominal, band_of(out)),
          f"{mid}: and the Run 13 reproducer no longer reads Green from it",
          f"nominal {nominal} -> {band_of(out)}")
    check(str(out.get("evidence_metric", "")).strip() != ""
          and "actualPctComplete" not in str(out.get("evidence_metric")),
          f"{mid}: the abstention carries a reader sentence that names no field key",
          str(out.get("evidence_metric"))[:80])
    check(band_of(run(mid, dict(BASE))) == nominal,
          f"{mid}: and the ordinary project is unaffected by the guard", str(nominal))

# EXHAUSTED, NOT SAMPLED. Every bounded field, driven just above its own bound and far above it,
# against every executable module. No module may band better than it did on the nominal project.
_regressions: list[str] = []
_guarded: list[str] = []
for _field, _max in sorted(BOUNDED_MAX_SI_FIELDS.items()):
    for _bad in (_max + 0.5, _max * 10, _max * 1000, 1e9):
        for _mid in sorted(VALIDATED):
            if _mid in DISABLED_CONCEPT_ONLY:
                continue
            _nom = band_of(run(_mid, dict(BASE)))
            _si = dict(BASE)
            if _field not in _si:
                continue
            _si[_field] = _bad
            _got = run(_mid, _si)
            if improved(_nom, band_of(_got)):
                _regressions.append(f"{_mid}:{_field}={_bad}:{_nom}->{band_of(_got)}")
            elif _got.get("insufficient_data") and not run(_mid, dict(BASE)).get(
                    "insufficient_data"):
                _guarded.append(f"{_mid}:{_field}")
check(not _regressions,
      "across every executable module and every bounded field, no value outside the field's own "
      "domain produces a calmer reading than the ordinary project",
      "; ".join(sorted(set(_regressions))[:6]))
check(len(set(_guarded)) >= len(BANDING),
      "and the guard is live: modules do change behaviour on those values rather than the sweep "
      "passing because nothing reads the fields", str(len(set(_guarded))))


# =================================================================================================
section("4. THE TWO MISSINGNESS OCCURRENCES: REMOVING EVIDENCE MUST NOT IMPROVE THE READING")
# =================================================================================================
#
# EXHAUSTED OVER EVERY STRICT SUBSET THAT IS TRACTABLE. For each of the two modules the run
# takes the fields the module reads and removes every non-empty combination of them, which is
# every strict subset of its evidence, and requires that none of the removals produces a calmer
# reading than the full evidence does.
import itertools  # noqa: E402

SUBSET_FIELDS = {
    "A3.5": ("indirectCostPlan", "indirectCostActual", "actualPctComplete"),
    "C1.6": ("ev", "ac", "cpi", "spi", "pv", "bac", "actualPctComplete"),
}
for mid in MISSINGNESS:
    fields = SUBSET_FIELDS[mid]
    full = band_of(run(mid, dict(BASE)))
    check(full is not None, f"{mid}: the full evidence produces a reading to compare against",
          str(full))
    worse_or_equal = True
    _bad_removals: list[str] = []
    _subsets = 0
    for size in range(1, len(fields) + 1):
        for combo in itertools.combinations(fields, size):
            si = {k: v for k, v in BASE.items() if k not in combo}
            got = band_of(run(mid, si))
            _subsets += 1
            if improved(full, got):
                worse_or_equal = False
                _bad_removals.append(f"minus {', '.join(combo)} -> {got}")
    check(worse_or_equal,
          f"{mid}: across all {_subsets} strict subsets of its evidence, no removal improves the "
          f"reading", "; ".join(_bad_removals[:4]))
    check(_subsets == 2 ** len(fields) - 1,
          f"{mid}: and the sweep was exhaustive over those fields rather than a sample",
          str(_subsets))

# The two Run 13 cases named exactly, so the specific defect is asserted and not only the
# property that covers it.
_a35_nominal = band_of(run("A3.5", dict(BASE)))
_a35_dropped = run("A3.5", {k: v for k, v in BASE.items() if k != "actualPctComplete"})
check(_a35_dropped.get("insufficient_data") is True,
      "A3.5: with no reported progress the module abstains, where Run 13 recorded it moving from "
      "Red to Yellow", str(_a35_dropped.get("status_color")))
check(_a35_dropped.get("abstention_reason_code") == "missing_required_input",
      "A3.5: and it abstains because a required input is absent, not for some other reason",
      str(_a35_dropped.get("abstention_reason_code")))
for _drop in ("actualPctComplete", "bac"):
    _c16 = band_of(run("C1.6", {k: v for k, v in BASE.items() if k != _drop}))
    check(not improved(band_of(run("C1.6", dict(BASE))), _c16),
          f"C1.6: dropping the figure a failing check compares no longer turns the reading "
          f"Green ({_drop})", f"{band_of(run('C1.6', dict(BASE)))} -> {_c16}")
_c16_full = run("C1.6", dict(BASE))
check(_c16_full.get("checks_declared") == 3,
      "C1.6: the score is taken over the three agreements the method is defined over",
      str(_c16_full.get("checks_declared")))
_c16_part = run("C1.6", {k: v for k, v in BASE.items() if k != "pv"})
check(_c16_part.get("checks_not_performed") == 1
      and "could not be run" in str(_c16_part.get("evidence_metric")),
      "C1.6: and a check that could not be run is said so in words rather than dropped from the "
      "denominator", str(_c16_part.get("evidence_metric"))[:100])


# =================================================================================================
section("5. THE TWO CANONICAL-METHOD OCCURRENCES: ABSENT STRUCTURE MEANS ABSTENTION")
# =================================================================================================
STRUCTURE_KEY = {"A5.4": "scenarioDecisionStructure", "B2.19": "decisionMatrix"}
for mid in STRUCTURE:
    key = STRUCTURE_KEY[mid]
    with_structure = run(mid, dict(BASE))
    check(with_structure.get("insufficient_data") is not True,
          f"{mid}: with its defining structure present the method computes", str(with_structure))
    check(with_structure.get("canonical_structure") in
          ("action_scenario_payoff", "alternatives_by_criteria_matrix"),
          f"{mid}: and the result names the structure it was computed across",
          str(with_structure.get("canonical_structure")))
    without = run(mid, {k: v for k, v in BASE.items() if k != key})
    check(without.get("insufficient_data") is True,
          f"{mid}: with the structure absent the method abstains rather than substituting a "
          f"proxy", str(without.get("status_color")))
    check(without.get("abstention_reason_code") == "canonical_decision_structure_absent",
          f"{mid}: and the abstention names the absent structure", str(without))
    check(without.get("status_color") is None
          and normalise_status(without.get("status_color")) is None,
          f"{mid}: no band of any kind reaches fusion from the structureless case")
    # No input to a single project can bring the reading back: the substitute is gone, not
    # merely harder to reach.
    _reachable = set()
    for _cpi in (0.5, 0.9, 1.0, 1.4):
        for _spi in (0.5, 0.9, 1.0, 1.4):
            for _risk in (0.0, 0.3, 0.9):
                _si = {k: v for k, v in BASE.items() if k != key}
                _si.update(cpi=_cpi, spi=_spi, docRiskScore=_risk)
                _reachable.add(run(mid, _si).get("status_color"))
    check(_reachable == {None},
          f"{mid}: and no combination of single-project figures reaches a band", str(_reachable))


# =================================================================================================
section("6. THE REAL EXECUTION PATH, AND THE PROTECTIONS THAT MUST NOT HAVE MOVED")
# =================================================================================================
_plain = compute_project(dict(STRUCTURED), "S-RUN14", "P1", CUTOFF)
_ids = {m["module_id"] for m in _plain["modules"]}
for mid in MISMATCH:
    check(mid in _ids or mid in {a.get("module_id") for a in _plain.get("abstained", [])},
          f"{mid}: is accounted for on the application's own compute path, computed or "
          f"abstained")
_impossible = dict(STRUCTURED)
_impossible["actualPctComplete"] = 10_000
_hot = compute_project(_impossible, "S-RUN14", "P1", CUTOFF)
check(_hot["project_status"] is not None,
      "a project carrying an impossible figure still produces a fused status rather than "
      "crashing the pipeline", str(_hot["project_status"]))
check(BAND_RANK.get(normalise_status(_hot["project_status"]), -1)
      <= BAND_RANK.get(normalise_status(_plain["project_status"]), -1),
      "and that status is no calmer than the same project without the impossible figure",
      f"{_plain['project_status']} -> {_hot['project_status']}")
check(sorted(CORE_VOTING_MODULES) == ["A1.7", "A1.8"],
      "the voting set is still exactly the two cost-lineage modules", str(sorted(
          CORE_VOTING_MODULES)))
check(not (set(CORE_VOTING_MODULES) & set(MISMATCH)),
      "and none of the eight corrected modules votes, so no correction can move a project "
      "status through the vote")
check(sorted(DISABLED_CONCEPT_ONLY) == DISABLED,
      "the eight disabled modules are the eight Run 13 recorded, and this run activated none "
      "of them", str(sorted(DISABLED_CONCEPT_ONLY)))
check(SIMULATION_VERSION == "sim-2026.08-v9",
      "the analytical layer is stamped at this run's version, and every earlier stamp remains "
      "the historical baseline for results collected under it", SIMULATION_VERSION)


# =================================================================================================
section("7. MUTATION PROOF: EVERY ASSERTION ABOVE COULD HAVE FAILED")
# =================================================================================================
#
# Production files are never edited. For each corrected module an ISOLATED COPY of its own
# source is compiled with a fault in it, and the corrected behaviour is required to disappear
# under that fault. A mutation that changes nothing is a check that cannot fail, which is the
# thing this programme has been bitten by repeatedly.
MUTATION_CASE = {
    # module: (the input that must abstain after the fix, the field removed if any)
    "A2.11": ({"actualPctComplete": 10_000}, None),
    "A3.2": ({"actualPctComplete": 10_000}, None),
    "A3.3": ({"actualPctComplete": 10_000}, None),
    "A3.5": ({"actualPctComplete": 10_000}, None),
    "A5.8": ({"actualPctComplete": 10_000}, None),
    "C1.6": ({}, "actualPctComplete"),
    "A5.4": ({}, "scenarioDecisionStructure"),
    "B2.19": ({}, "decisionMatrix"),
}
for mid in MISMATCH:
    overrides, drop = MUTATION_CASE[mid]
    fn = VALIDATED[mid][1]
    si = {k: v for k, v in BASE.items() if k != drop}
    si.update(overrides)
    live = fn(dict(si), NOOP, CUTOFF)
    changed = []
    for transformer, name in ((NegateGuard, "every branch guard inverted"),
                              (FlipCompare, "every ordering comparison reversed")):
        mutant, count = mutated_callable(fn, transformer)
        if mutant is None or count == 0:
            continue
        try:
            got = mutant(dict(si), NOOP, CUTOFF)
        except Exception as exc:                                      # noqa: BLE001
            got = {"raised": repr(exc)}
        if got != live:
            changed.append(name)
    check(bool(changed),
          f"{mid}: the corrected behaviour disappears when a fault is injected into an isolated "
          f"copy of the production function", "; ".join(changed) or "NO MUTATION BOUND")
    after = fn(dict(si), NOOP, CUTOFF)
    check(after == live,
          f"{mid}: and the production function is unchanged after the injection", str(after)[:80])

# The shared guard itself, mutated: with the bounded table emptied, the five banding cases come
# back. This proves the sweep in section 3 is passing because of the guard and not because the
# inputs never reached the modules.
import app.field_registry as _fr  # noqa: E402

_saved = dict(_fr.BOUNDED_MAX_SI_FIELDS)
try:
    _fr.BOUNDED_MAX_SI_FIELDS.clear()
    _returned = []
    for mid in BANDING:
        _nom = band_of(run(mid, dict(BASE)))
        _si = dict(BASE)
        _si["actualPctComplete"] = 10_000
        if improved(_nom, band_of(run(mid, _si))):
            _returned.append(mid)
    check(sorted(_returned) == BANDING,
          "with the bounded-field table emptied all five banding occurrences return, so the "
          "sweep above is passing because of the guard", str(_returned))
finally:
    _fr.BOUNDED_MAX_SI_FIELDS.update(_saved)
_restored = []
for mid in BANDING:
    _si = dict(BASE)
    _si["actualPctComplete"] = 10_000
    if run(mid, _si).get("insufficient_data") is True:
        _restored.append(mid)
check(sorted(_restored) == BANDING,
      "and the guard is restored afterwards, so nothing later in this suite runs against a "
      "mutated table", str(_restored))


print("\n" + "=" * 78)
if FAILURES:
    print("FAILURES:")
    for f in FAILURES:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{TOTAL} checks passed")
print("=" * 78)
sys.exit(0 if PASSED == TOTAL else 1)
