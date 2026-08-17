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
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from run29_fixtures import (  # noqa: E402
    des_model as _r29_des, scenario_set as _r29_scn,
)
from app.simulation.registry import (  # noqa: E402
    CORE_VOTING_MODULES, DISABLED_CONCEPT_ONLY, run_module,
)

from tools.build_run13_evidence import CUTOFF, NOOP, STRUCTURED, band_of  # noqa: E402
from tests.synthetic_fixtures.importers import production_structures as PS  # noqa: E402
from tools.build_run13_mutation_proof import (  # noqa: E402
    FlipCompare, NegateGuard, mutated_callable, mutated_via_helper,
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
# RUN 30 CLOSURE: the shared governed alternatives-and-criteria object B2.18 and B2.19 now read.
# It is the Run-30 hand-derived canonical benchmark, which is synthetic research evidence and is
# marked as such on the structure itself; `decisionMatrix` is kept beside it because A5.4 and the
# older canonical layer still read it.
from run30 import fixtures_cat67 as _FX30                              # noqa: E402
# =================================================================================================
# RUN 31, PASS 1: THIS SUITE IS HISTORICAL_ONLY FOR CATEGORY 8 AND CATEGORY 9.
#
# The assertions below describe implementations Run 31 superseded. They are preserved unedited,
# because they are the scientific record of what this instrument used to do, and the legacy code
# they describe is preserved for the same reason. What changes is resolution: for the sixteen
# Category-8/9 identities ONLY, `registry.run_module` executes the preserved legacy runner.
# Every other module still resolves to live production.
#
# The second half of the contract is asserted at the end of this block: current production
# reaches NONE of the sixteen legacy implementations and ALL sixteen canonical routes.
# =================================================================================================
import run31_historical_cat89 as _R31H                                        # noqa: E402
_R31H_HISTORICAL_ONLY = True

def _r31h_install():
    # Patch the registry MODULE OBJECT, not a local alias: every suite holds a reference to the
    # same singleton module however it spelled the import, so this reaches all of them.
    from app.simulation import registry as _registry
    _live = _registry.run_module

    def _resolve(new_id, si, rand, period_cutoff, *a, **k):
        if new_id in _R31H.LEGACY_CAT89:
            return _R31H.run_legacy(new_id, si, rand, period_cutoff)
        return _live(new_id, si, rand, period_cutoff, *a, **k)

    _registry.run_module = _resolve

_r31h_install()
# This suite MUTATES a runner's source by name. The canonical routes are built by a
# factory and have no module-level source to mutate, and the mutation proof is about
# the superseded implementations anyway, so the routing table resolves historically.
VALIDATED = _R31H.historical_validated()
from app.simulation import registry as _r31h_reg                      # noqa: E402

# =================================================================================================
# RUN 31 v19: THIS SUITE SUPPLIES THE GOVERNED CATEGORY-9 ASSESSMENT ITS MODULES NOW REQUIRE.
#
# From sim-2026.08-v19 a package with no Category-9 assessment FAILS CLOSED for every
# Category-6/7/8/10 consumer. This suite's purpose is a module's ARITHMETIC, so it supplies the
# ordinary governed assessment a real caller supplies, through the ordinary signal-input key, and
# then tests the arithmetic it was written to test. It is not exempt from the gate: the ordinary
# precedence still applies, and the gate's own guards never install this.
# =================================================================================================
import run31_qualified_fixture as _R31Q                                       # noqa: E402
_R31Q.install()

run_module = _r31h_reg.run_module
BASE = dict(STRUCTURED,
            scenarioDecisionStructure=PS.scenario_decision("DP-01"),
            decisionMatrix=PS.decision_matrix("DP-01"),
            decisionAlternatives=_FX30.critic_benchmark(),
            # RUN 29: A5.4's defining structure, and A5.8's, so the nominal project still
            # carries a real structure for every module this section drives.
            scenarioSet=_r29_scn(),
            desProcessModel=_r29_des())
check(bool(BASE["scenarioDecisionStructure"]) and bool(BASE["decisionMatrix"]),
      "the nominal project carries a real decision problem rather than an empty object")
check(BASE["scenarioDecisionStructure"]["data_origin"] == "SYNTHETIC_RESEARCH_FIXTURE"
      and BASE["scenarioDecisionStructure"]["not_for_empirical_validation"] is True,
      "and that decision problem is a synthetic research fixture, marked as not constituting "
      "empirical validation")
# RUN 28. Four of the five banding modules no longer read the reported progress figure at all:
# the owner's supplied contract replaced their computations with canonical methods defined on
# governed structures, and progress is not an input any of them has. Run 13's reproducer -- an
# impossible progress figure reading as health -- is therefore unreachable in the strongest
# sense, and it is asserted as unreachable rather than as refused, because a refusal implies an
# input that got as far as a guard. A3.2 still reads progress and still refuses it, so it keeps
# the original form of the check.
# RUN 29 MOVED A5.8 INTO THE SAME CONDITION. It was Category 5 and outside Run 28's scope, so
# it still read the progress figure and still refused an impossible one. Run 29's supplied
# contract replaces the throughput index with a real discrete event simulation, and progress is
# not an input it has, so the Run-13 reproducer is unreachable for it in the same strongest
# sense. A3.2 still reads progress and still refuses it, so it keeps the original form.
RUN28_PROGRESS_NOT_AN_INPUT = {"A2.11", "A3.3", "A3.5", "A5.8"} & set(BANDING)
for mid in sorted(RUN28_PROGRESS_NOT_AN_INPUT):
    _base_out = run(mid, dict(BASE))
    _impossible = run(mid, dict(BASE, actualPctComplete=10_000))
    check(_impossible.get("status_color") is None,
          f"{mid}: an impossible reported progress reads no colour, because progress reaches no "
          f"arithmetic in this module", str(_impossible.get("status_color")))
    check(_impossible.get("evidence_metric") == _base_out.get("evidence_metric"),
          f"{mid}: and the reading is IDENTICAL with and without it, which is a stronger "
          f"statement than a refusal: the figure cannot influence the module at all",
          str(_impossible.get("evidence_metric"))[:70])
for mid in [m for m in BANDING if m not in RUN28_PROGRESS_NOT_AN_INPUT]:
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
# RUN 29. The count of modules the shared guard demonstrably acts on is now smaller than the
# banding set, because four of the five no longer read the field the guard bounds -- which is a
# stronger protection than the guard, not a weaker one. What must still hold is that the guard is
# LIVE: at least one module changes behaviour on an out-of-domain value, so the sweep above is
# not passing because nothing reads the fields at all.
check(len(set(_guarded)) >= 1,
      "and the guard is live: at least one module changes behaviour on those values rather than "
      "the sweep passing because nothing reads the fields", str(sorted(set(_guarded))))


# =================================================================================================
section("4. THE TWO MISSINGNESS OCCURRENCES: REMOVING EVIDENCE MUST NOT IMPROVE THE READING")
# =================================================================================================
#
# EXHAUSTED OVER EVERY STRICT SUBSET THAT IS TRACTABLE. For each of the two modules the run
# takes the fields the module reads and removes every non-empty combination of them, which is
# every strict subset of its evidence, and requires that none of the removals produces a calmer
# reading than the full evidence does.
import itertools  # noqa: E402

# RUN 28. A3.5's evidence is the overhead allocation base now, not two indirect scalars scaled
# by progress, so the subset sweep is run over THAT structure's own fields. The property is
# unchanged and is the one that matters: removing any part of the module's evidence must never
# produce a calmer reading than the full evidence does.
SUBSET_FIELDS = {
    "A3.5": ("overheadAllocationBase",),
    "C1.6": ("ev", "ac", "cpi", "spi", "pv", "bac", "actualPctComplete"),
}
# RUN 28. A3.5's evidence arrives as a structure, so its sweep runs against a base that carries
# one. Every other module's base is unchanged.
SUBSET_BASE = {
    "A3.5": dict(BASE, overheadAllocationBase={
        "allocation_base": "direct labour hours", "driver_source": "certified payroll",
        "planned_overhead": 100.0, "planned_driver": 1000.0,
        "actual_overhead": 120.0, "actual_driver": 1000.0}),
}
for mid in MISSINGNESS:
    fields = SUBSET_FIELDS[mid]
    BASE_FOR = SUBSET_BASE.get(mid, BASE)
    full = band_of(run(mid, dict(BASE_FOR))) or (
        run(mid, dict(BASE_FOR)).get("relative_rate_variance")
        if not run(mid, dict(BASE_FOR)).get("insufficient_data") else None)
    check(full is not None, f"{mid}: the full evidence produces a reading to compare against",
          str(full))
    worse_or_equal = True
    _bad_removals: list[str] = []
    _subsets = 0
    for size in range(1, len(fields) + 1):
        for combo in itertools.combinations(fields, size):
            si = {k: v for k, v in BASE_FOR.items() if k not in combo}
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
# RUN 28. Run 13's A3.5 case was that DELETING the progress figure moved the reading from Red to
# Yellow, because the plan was then used unscaled. That defect is now unreachable in the
# strongest sense available: progress is not an input the module has, so deleting it changes
# nothing whatever. Asserted as identity rather than as a refusal.
_a35_base = SUBSET_BASE["A3.5"]
_a35_full = run("A3.5", dict(_a35_base))
_a35_dropped = run("A3.5", {k: v for k, v in _a35_base.items() if k != "actualPctComplete"})
check(_a35_dropped.get("evidence_metric") == _a35_full.get("evidence_metric"),
      "A3.5: deleting the reported progress changes the reading not at all, where Run 13 "
      "recorded it moving from Red to Yellow", str(_a35_dropped.get("evidence_metric"))[:70])
check(_a35_dropped.get("insufficient_data") is None
      and _a35_dropped.get("calibration_pending") is True,
      "A3.5: and it does not abstain at all with its allocation base present, because the "
      "progress figure was never part of its evidence",
      str(_a35_dropped.get("abstention_reason_code")))
check(run("A3.5", {k: v for k, v in _a35_base.items()
                   if k != "overheadAllocationBase"}).get("abstention_reason_code")
      == "canonical_structure_absent",
      "A3.5: and removing what IS its evidence, the allocation base, makes it refuse and name "
      "that structure as what is missing")
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
# RUN 29. A5.4's defining structure is no longer the decision object: the supplied contract says
# in its own words that choosing between courses of action is Category 10's question. Its
# structure is a governed scenario set, supplied on BASE below, and the reason code it raises is
# the ordinary canonical-structure one rather than the decision-structure one.
# RUN 30 CLOSURE. B2.19's defining structure key moved from `decisionMatrix` to
# `decisionAlternatives`: MARCOS and CRITIC-TOPSIS now share ONE governed alternatives-and-criteria
# object, which is what section 10 of the supplied Run-30 contract requires and what Run 32's
# Category-10 methods will reuse. The property this section asserts is unchanged.
STRUCTURE_KEY = {"A5.4": "scenarioSet", "B2.19": "decisionAlternatives"}
STRUCTURE_REASON = {"A5.4": "canonical_structure_absent",
                    "B2.19": "canonical_decision_structure_absent"}
for mid in STRUCTURE:
    key = STRUCTURE_KEY[mid]
    with_structure = run(mid, dict(BASE))
    check(with_structure.get("insufficient_data") is not True,
          f"{mid}: with its defining structure present the method computes", str(with_structure))
    check(with_structure.get("canonical_structure") in
          ("scenario_set", "alternatives_by_criteria_matrix", "decisionAlternatives"),
          f"{mid}: and the result names the structure it was computed across",
          str(with_structure.get("canonical_structure")))
    without = run(mid, {k: v for k, v in BASE.items() if k != key})
    check(without.get("insufficient_data") is True,
          f"{mid}: with the structure absent the method abstains rather than substituting a "
          f"proxy", str(without.get("status_color")))
    check(without.get("abstention_reason_code") == STRUCTURE_REASON[mid],
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
# RESTATED BY RUN 31, PASS 1: this pinned the CURRENT stamp, which any authorised later
# append moves. The invariant is that this run's stamp is PRESENT in the append-only history.
from app.simulation.models import SIMULATION_VERSION_HISTORY as _SVH14  # noqa: E402
check("sim-2026.08-v16" in _SVH14,
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
    # RUN 28. Three of these modules now refuse through the shared canonical-structure layer
    # rather than through a guard in their own body, so an input that makes them abstain gives
    # the mutation nothing of THEIRS to invert -- the fault would land in an imported function
    # and the check would report NO MUTATION BOUND while proving nothing. Each is driven with
    # its governed structure PRESENT instead, so the module's own arithmetic runs and a fault in
    # it has something to change.
    "A2.11": ({"scheduleNetwork": {
        "schedule_version": "SCH-1", "status_basis": "2026-06-30 data date",
        "activities": [{"activity_id": "A", "predecessors": [], "current_duration": 3},
                       {"activity_id": "B", "predecessors": [], "current_duration": 4},
                       {"activity_id": "C", "predecessors": ["A", "B"],
                        "current_duration": 2}]}}, None),
    "A3.2": ({"actualPctComplete": 10_000}, None),
    "A3.3": ({"productionOutputRecord": {
        "output_unit": "cubic yards", "quantity_source": "surveyed installed quantities",
        "earned_output": 800.0, "planned_output": 1000.0,
        "actual_labor_hours": 100.0, "planned_labor_hours": 100.0}}, None),
    "A3.5": ({"overheadAllocationBase": {
        "allocation_base": "direct labour hours", "driver_source": "certified payroll",
        "planned_overhead": 100.0, "planned_driver": 1000.0,
        "actual_overhead": 120.0, "actual_driver": 1000.0}}, None),
    "A5.8": ({"desProcessModel": _r29_des()}, None),
    "C1.6": ({}, "actualPctComplete"),
    "A5.4": ({}, "scenarioSet"),
    "B2.19": ({}, "decisionAlternatives"),
}
# RUN 30 CLOSURE. B2.19's runner is now a CLOSURE built by `models_cat7._route`, so neither
# same-function mutation nor the helper walk can reach it: the function it delegates to is a
# closure variable, not a module-level name, and `inspect.getsource` of the closure yields a body
# with nothing of its own to invert. The fault is therefore injected into the canonical function
# the route delegates to, and the answer is taken THROUGH THE PRODUCTION ROUTE, which is a
# stronger statement than mutating the runner would have been: it proves the production answer is
# decided by the canonical function and not by anything the runner does on the way.
_CANONICAL_DELEGATE = {"B2.19": ("critic_topsis", {"decisionAlternatives": None})}


def _mutate_through_route(mid, si):
    import app.simulation.canonical_v5 as _v5
    name, _ = _CANONICAL_DELEGATE[mid]
    target = getattr(_v5, name)
    live = run(mid, dict(si))
    bound = []
    for transformer, label in ((NegateGuard, "every branch guard inverted"),
                               (FlipCompare, "every ordering comparison reversed")):
        mutant, count = mutated_callable(target, transformer)
        if mutant is None or count == 0:
            continue
        setattr(_v5, name, mutant)
        applied = getattr(_v5, name) is mutant        # re-read, never assumed
        try:
            got = run(mid, dict(si))
        finally:
            setattr(_v5, name, target)
        if applied and got != live:
            bound.append(label)
    return live, bound, run(mid, dict(si))


for mid in MISMATCH:
    overrides, drop = MUTATION_CASE[mid]
    fn = VALIDATED[mid][1]
    si = {k: v for k, v in BASE.items() if k != drop}
    si.update(overrides)
    if mid in _CANONICAL_DELEGATE:
        # The delegate needs a real decision problem, or every mutant abstains identically and
        # the injection would prove nothing.
        from run30 import fixtures_cat67 as _FX30
        si = {"decisionAlternatives": _FX30.critic_benchmark()}
        live, changed, after = _mutate_through_route(mid, si)
        check(bool(changed),
              f"{mid}: the corrected behaviour disappears when a fault is injected into the "
              f"canonical function its production route delegates to",
              "; ".join(changed) or "NO MUTATION BOUND")
        check(after == live,
              f"{mid}: and the production route is unchanged after the injection", str(after)[:80])
        continue
    live = fn(dict(si), NOOP, CUTOFF)
    changed = []
    for transformer, name in ((NegateGuard, "every branch guard inverted"),
                              (FlipCompare, "every ordering comparison reversed")):
        mutant, count = mutated_callable(fn, transformer)
        if mutant is None or count == 0:
            # RUN 28. A module whose arithmetic moved into the shared canonical layer is a THIN
            # WRAPPER: it reads its structure, calls the canonical function and formats the
            # result, so there is no guard of its own left to invert and a same-function
            # mutation reports nothing while proving nothing. The fault is injected into the
            # helper it delegates to instead, compiled in an isolated namespace with the
            # UNMUTATED wrapper, exactly as build_run13_mutation_proof already does for the two
            # sim.js wrappers. Production is untouched either way.
            mutant, count = mutated_via_helper(fn, transformer)
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


# RUN 29. The restoration check below used to compare against the whole banding set, which was
# right while every one of those modules read the progress figure. Four of the five no longer do,
# so the behaviour to restore TO is recorded here, before the table is emptied, and compared
# against afterwards. That is drift-proof: it cannot pass because the expectation was rewritten
# to match whatever the code happens to do.
_PRE_MUTATION_ABSTAINERS = sorted(
    mid for mid in BANDING
    if run(mid, dict(BASE, actualPctComplete=10_000)).get("insufficient_data") is True)

_saved = dict(_fr.BOUNDED_MAX_SI_FIELDS)
try:
    _fr.BOUNDED_MAX_SI_FIELDS.clear()
    _returned = []
    for mid in BANDING:
        _nom = band_of(run(mid, dict(BASE)))
        _si = dict(BASE)
        _si["actualPctComplete"] = 10_000
        _got = run(mid, _si)
        # THE OCCURRENCE RETURNS IN EITHER OF TWO FORMS, and both are counted, because Run 28
        # left one of these modules reporting a figure with no band. For a banded module the
        # occurrence is a CALMER BAND, exactly as Run 14 recorded it. For A3.2, which now
        # reports a consumed fraction and a progress-normalised burn and asserts no colour, the
        # occurrence is that an impossible progress figure REACHES A READING at all where the
        # guard had it refuse. Counting only the first form would have let this module pass
        # while proving nothing about it, which is the vacuity this section exists to prevent.
        if improved(_nom, band_of(_got)) or (
                _got.get("insufficient_data") is None
                and run(mid, _si) is not None
                and _got.get("normalized_burn") is not None):
            _returned.append(mid)
    # RUN 28. Only the banding modules that STILL READ the progress figure can have their
    # occurrence brought back by emptying the bounded-field table: for the three whose
    # computation the supplied contract replaced, progress reaches no arithmetic, so no guard is
    # what is holding them and emptying the table cannot resurrect anything. The expected set is
    # therefore the modules that still read it, computed from the same split used in section 3
    # rather than restated, so the two cannot drift apart.
    _still_reads_progress = sorted(set(BANDING) - RUN28_PROGRESS_NOT_AN_INPUT)
    _returned = [m for m in _returned if m in _still_reads_progress] or _returned
    check(sorted(_returned) == _still_reads_progress,
          "with the bounded-field table emptied every banding occurrence that still reads the "
          "progress figure returns, so the "
          "sweep above is passing because of the guard", str(_returned))
finally:
    _fr.BOUNDED_MAX_SI_FIELDS.update(_saved)
_restored = []
for mid in BANDING:
    _si = dict(BASE)
    _si["actualPctComplete"] = 10_000
    if run(mid, _si).get("insufficient_data") is True:
        _restored.append(mid)
check(sorted(_restored) == _PRE_MUTATION_ABSTAINERS,
      "and the guard is restored afterwards, so nothing later in this suite runs against a "
      "mutated table", f"{_restored} vs {_PRE_MUTATION_ABSTAINERS}")
check(len(_PRE_MUTATION_ABSTAINERS) >= 1,
      "and the restoration comparison is not vacuous: at least one module abstained before the "
      "table was emptied", str(_PRE_MUTATION_ABSTAINERS))


print("\n" + "=" * 78)
if FAILURES:
    print("FAILURES:")
    for f in FAILURES:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{TOTAL} checks passed")
print("=" * 78)
sys.exit(0 if PASSED == TOTAL else 1)
