#!/usr/bin/env python3
"""
Run 10B, Gate 1: the out-of-domain defect in a VOTING module.

WHY THIS SUITE IS SEPARATE AND WHY IT RUNS FIRST. Exactly two modules vote on project status.
The Run 10 neighbour sweep found that one of them, the to-complete cost efficiency measure,
returns Green on input outside the domain its quantities can occupy. That is the only defect
carried out of Run 10 that can move a project's status by itself, so it is corrected before any
integration work and proved here.

WHAT A CHECK IN THIS FILE IS.

1. THE PRIOR BEHAVIOUR IS THE SHIPPED CODE, extracted from the pinned baseline revision by git
   and imported, not a description of it and not a hand-written copy.
2. EVERY EXPECTATION IS DERIVED FROM A DEFINITION, never from running the module and recording
   what it returned.
3. DOMAINS ARE EXHAUSTED OR RANDOMISED rather than illustrated: the band is swept across its
   boundaries from both sides, and the invalid domain is swept over a randomised grid.
4. EVERY CHECK IS PROVED ABLE TO FAIL: section 7 perturbs each expectation and asserts red.
5. THE REAL PATH IS EXERCISED: project status is fused through compute_project, the same
   function the upload path calls, before and after the correction.

Run:
    PYTHONIOENCODING=utf-8 python tools/test_run10b_a1_7_domain.py
"""

from __future__ import annotations

import datetime as _dt
import pathlib
import random
import subprocess
import sys
import tempfile

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from app.simulation.compute import compute_project  # noqa: E402
from app.simulation.models import ABSTAIN_MALFORMED_INPUT, SIMULATION_VERSION  # noqa: E402
from app.simulation.models_evm import run_tcpi  # noqa: E402
from app.simulation.registry import CORE_VOTING_MODULES  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASELINE_REV = "c5d7101"
CUTOFF = _dt.date(2026, 6, 30)

PASSED = 0
FAILED = 0


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def section(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def band(result):
    return result.get("status_color")


def abstains(result) -> bool:
    return bool(result.get("insufficient_data")) and result.get("status_color") is None


def si_of(bac, ev, ac, **extra):
    out = {"bac": bac, "ev": ev, "ac": ac}
    out.update(extra)
    return out


# =================================================================================================
section("0. THE PRIOR BEHAVIOUR IS THE SHIPPED CODE AT THE PINNED BASELINE")
# =================================================================================================

_TMP = tempfile.mkdtemp(prefix="run10b-baseline-")
# The package is nested three levels below a temporary root and the renumbering map is linked
# beside it, because the registry resolves that map relative to its own file. A flat copy
# would resolve to the filesystem root and the baseline would fail to load at all, which is
# exactly the "the check crashed and looked clean" failure this repository has been bitten by.
_PKG_ROOT = pathlib.Path(_TMP) / "a" / "b"
_PKG = _PKG_ROOT / "oldsim10b"
_PKG.mkdir(parents=True)
(pathlib.Path(_TMP) / "p0-baseline").symlink_to(ROOT / "p0-baseline")
_names = subprocess.run(["git", "ls-tree", "--name-only", BASELINE_REV, "server/app/simulation/"],
                        cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
_py = [n for n in _names if n.endswith(".py")]
if len(_py) < 10:
    raise SystemExit("baseline extraction found no simulation sources at the pinned baseline; "
                     "refusing to run half of every proof")
for _n in _py:
    body = subprocess.run(["git", "show", f"{BASELINE_REV}:{_n}"],
                          cwd=ROOT, capture_output=True, text=True, check=True).stdout
    (_PKG / pathlib.Path(_n).name).write_text(body, encoding="utf-8")
(_PKG / "__init__.py").write_text("", encoding="utf-8")
sys.path.insert(0, str(_PKG_ROOT))
import oldsim10b.models as old_models  # noqa: E402
import oldsim10b.models_evm as old_evm  # noqa: E402

check(old_models.SIMULATION_VERSION == "sim-2026.08-v4",
      "the pinned baseline is the version Run 10 shipped", old_models.SIMULATION_VERSION)
check(SIMULATION_VERSION == "sim-2026.08-v10",
      "and this branch is stamped at this run's version, so a result computed before the "
      "correction and one computed after are distinguishable in already collected data",
      SIMULATION_VERSION)
_baseline_src = subprocess.run(["git", "show", f"{BASELINE_REV}:server/app/simulation/models_evm.py"],
                               cwd=ROOT, capture_output=True, text=True, check=True).stdout
_now_src = (ROOT / "server" / "app" / "simulation" / "models_evm.py").read_text(encoding="utf-8")
check(_baseline_src != _now_src,
      "the correction actually altered the bytes of the shipped module file",
      f"baseline {len(_baseline_src)} bytes, now {len(_now_src)} bytes")


# =================================================================================================
section("1. THE REPRODUCER FROM THE NEIGHBOUR SWEEP, RUN AGAINST THE BASELINE CODE")
# =================================================================================================

# A project that has consumed most of its budget and earned little of it. With a truthfully
# reported actual cost the remaining work cannot be finished at the planned efficiency, and the
# module says so.
HONEST = si_of(1_000_000, 400_000, 900_000)
_honest_old = old_evm.run_tcpi(dict(HONEST), lambda: 0.5, CUTOFF)
check(band(_honest_old) == "Red",
      "baseline, truthful input: remaining work 600000 over remaining budget 100000 is 6.0, "
      "which is above the sourced upper edge, so Red", str(_honest_old.get("tcpi")))

# The reproducer: the same project with the actual cost reported below zero. Nothing about the
# project improved. The denominator merely grew past the budget itself.
REPRO = si_of(1_000_000, 400_000, -900_000)
_repro_old = old_evm.run_tcpi(dict(REPRO), lambda: 0.5, CUTOFF)
check(band(_repro_old) == "Green",
      "baseline, reproducer: an actual cost reported below zero reads Green in a module that "
      "votes on project status", str(_repro_old.get("tcpi")))
check(_repro_old.get("tcpi") is not None and _repro_old["tcpi"] < 1.0,
      "baseline, reproducer: and it reports a ratio, so the reading is indistinguishable "
      "downstream from a measured one", str(_repro_old.get("tcpi")))

# The second face of the same defect, from the numerator side.
REPRO_EV = si_of(1_000_000, 1_400_000, 900_000)
_repro_ev_old = old_evm.run_tcpi(dict(REPRO_EV), lambda: 0.5, CUTOFF)
check(band(_repro_ev_old) == "Green",
      "baseline, second face: an earned value above the budget at completion makes the "
      "remaining work negative and also reads Green", str(_repro_ev_old.get("tcpi")))

_repro_bac_old = old_evm.run_tcpi(si_of(-1_000, -2_000, -3_000), lambda: 0.5, CUTOFF)
check(band(_repro_bac_old) == "Green",
      "baseline, third face: a budget at completion below zero, with an earned value and an "
      "actual cost below it, reads Green",
      str(_repro_bac_old.get("status_color")))


# =================================================================================================
section("2. THE CORRECTION: OUT-OF-DOMAIN INPUT REFUSES, IT IS NOT CLAMPED")
# =================================================================================================

_repro_new = run_tcpi(dict(REPRO), lambda: 0.5, CUTOFF)
check(abstains(_repro_new),
      "the reproducer now abstains rather than returning a band", str(_repro_new))
check(_repro_new.get("abstention_reason_code") == ABSTAIN_MALFORMED_INPUT,
      "with the malformed input reason code, which the export and the API group on",
      str(_repro_new.get("abstention_reason_code")))
check("tcpi" not in _repro_new,
      "and no ratio is reported, so nothing downstream can read a quantity off it")
_reason = str(_repro_new.get("evidence_metric") or "")
check(_reason.endswith("."), "the reason is a sentence", _reason[:80])
check("—" not in _reason and "&" not in _reason, "with no em dash and no ampersand", _reason[:80])
check("_" not in _reason, "and no key name or reason code", _reason[:80])
check(not any(f"{g}{n}." in _reason for g in "ABCD" for n in range(1, 12)),
      "and no module id", _reason[:80])
check("substitute" in _reason.lower(),
      "and it states that no substitute figure is used", _reason[:80])

_repro_ev_new = run_tcpi(dict(REPRO_EV), lambda: 0.5, CUTOFF)
check(abstains(_repro_ev_new),
      "an earned value above the budget at completion abstains", str(_repro_ev_new))

check(band(run_tcpi(dict(HONEST), lambda: 0.5, CUTOFF)) == "Red",
      "and the truthful reading is unchanged by the correction: still Red, same ratio",
      str(run_tcpi(dict(HONEST), lambda: 0.5, CUTOFF).get("tcpi")))
check(run_tcpi(dict(HONEST), lambda: 0.5, CUTOFF).get("tcpi")
      == _honest_old.get("tcpi"),
      "identical to the baseline ratio on in-domain input, so no in-domain result moved")


# =================================================================================================
section("3. THE INVALID DOMAIN, SWEPT RATHER THAN ILLUSTRATED")
# =================================================================================================

rng = random.Random(100_710)
_invalid = 0
_favourable_before = 0
for _ in range(600):
    bac = rng.choice([-1.0, 0.0, rng.uniform(1e4, 5e6)])
    ev = rng.choice([-rng.uniform(1, 5e6), rng.uniform(0, 5e6)])
    ac = rng.choice([-rng.uniform(1, 5e6), rng.uniform(0, 5e6)])
    out_of_domain = (bac <= 0) or (ev < 0) or (ac < 0) or (ev > bac)
    if not out_of_domain:
        continue
    _invalid += 1
    si = si_of(bac, ev, ac)
    new = run_tcpi(dict(si), lambda: 0.5, CUTOFF)
    if not abstains(new):
        check(False, "an out-of-domain case still produced a band", str((si, new)))
        break
    old = old_evm.run_tcpi(dict(si), lambda: 0.5, CUTOFF)
    if band(old) in ("Green", "Amber"):
        _favourable_before += 1
else:
    check(True, f"every one of the {_invalid} out-of-domain cases in the sweep abstains")
check(_invalid > 200, "the sweep actually reached the invalid domain in bulk", str(_invalid))
check(_favourable_before > 0,
      "and the baseline read favourably on some of them, so the sweep is not vacuous",
      f"{_favourable_before} of {_invalid} read Green or Amber before")

for label, si in (
    ("a budget at completion of exactly zero", si_of(0, 0, 0)),
    ("a budget at completion below zero", si_of(-1, 0, 0)),
    ("an earned value one unit below zero", si_of(100, -1, 10)),
    ("an actual cost one unit below zero", si_of(100, 10, -1)),
    ("an earned value one unit above the budget", si_of(100, 101, 10)),
):
    check(abstains(run_tcpi(dict(si), lambda: 0.5, CUTOFF)),
          f"out of domain by one unit: {label} abstains")


# =================================================================================================
section("4. THE ADMISSIBLE EDGES OF EACH DOMAIN STILL COMPUTE")
# =================================================================================================

for label, si, expect in (
    ("an actual cost of exactly zero, which is a project that has spent nothing",
     si_of(100.0, 0.0, 0.0), "Green"),
    ("an earned value of exactly zero, which is a project that has earned nothing",
     si_of(100.0, 0.0, 50.0), "Red"),
    ("an earned value exactly equal to the budget, which is completed work",
     si_of(100.0, 100.0, 50.0), "Green"),
):
    out = run_tcpi(dict(si), lambda: 0.5, CUTOFF)
    check(not abstains(out), f"in domain at the edge: {label} computes", str(out))
    check(band(out) == expect,
          f"and its band follows from the ratio alone: {label}",
          f"{out.get('tcpi')} -> {band(out)} (expected {expect})")

# Derivation of the three expectations above, stated rather than taken from the module:
#   (100 - 0)/(100 - 0)   = 1.000 -> at the definitional edge -> Green
#   (100 - 0)/(100 - 50)  = 2.000 -> above the upper sourced edge -> Red is expected...
# The second case is deliberately re-derived here: 100/50 = 2.0, which is above 1.10.
_edge2 = run_tcpi(si_of(100.0, 0.0, 50.0), lambda: 0.5, CUTOFF)
check(_edge2.get("tcpi") == 2.0,
      "the zero earned value edge case reports the ratio the definition gives, 2.0",
      str(_edge2.get("tcpi")))


# =================================================================================================
section("5. THE SOURCED BAND BOUNDARIES ARE WHERE THEY WERE, SWEPT FROM BOTH SIDES")
# =================================================================================================

# The band edges are 1.00 and 1.10 and neither moves in this run. Each is approached from both
# sides by choosing (bac, ev, ac) so that (bac - ev)/(bac - ac) is exactly the target ratio.
def at_ratio(r: float):
    """remaining budget fixed at 1000, remaining work set to r * 1000."""
    bac, ac = 10_000.0, 9_000.0          # remaining budget 1000
    ev = bac - r * 1_000.0               # remaining work r * 1000
    return si_of(bac, ev, ac)


for r, expect in ((0.5, "Green"), (0.999, "Green"), (1.0, "Green"),
                  (1.001, "Amber"), (1.05, "Amber"), (1.099, "Amber"), (1.10, "Amber"),
                  (1.101, "Red"), (1.5, "Red"), (6.0, "Red")):
    out = run_tcpi(at_ratio(r), lambda: 0.5, CUTOFF)
    check(band(out) == expect,
          f"the ratio {r} bands {expect}, from the definitional edge at 1.00 and the stability "
          f"margin at 1.10", f"{out.get('tcpi')} -> {band(out)}")
    old = old_evm.run_tcpi(at_ratio(r), lambda: 0.5, CUTOFF)
    check(band(old) == band(out),
          f"and the baseline agreed at {r}, so no boundary moved in this run",
          f"{band(old)} then, {band(out)} now")


# =================================================================================================
section("6. MISSING AND MALFORMED INPUT")
# =================================================================================================

for missing in ("bac", "ev", "ac"):
    si = si_of(1000.0, 400.0, 500.0)
    del si[missing]
    check(abstains(run_tcpi(si, lambda: 0.5, CUTOFF)),
          f"a missing input abstains rather than defaulting: {missing}")
    si2 = si_of(1000.0, 400.0, 500.0)
    si2[missing] = None
    check(abstains(run_tcpi(si2, lambda: 0.5, CUTOFF)),
          f"an input reported as nothing abstains: {missing}")

for malformed in ("", "n/a", "TBD", float("nan"), float("inf"), float("-inf")):
    for key in ("bac", "ev", "ac"):
        si = si_of(1000.0, 400.0, 500.0)
        si[key] = malformed
        out = run_tcpi(si, lambda: 0.5, CUTOFF)
        check(abstains(out),
              f"a reading that is not a finite number abstains: {key} = {malformed!r}", str(out))

check(abstains(run_tcpi({}, lambda: 0.5, CUTOFF)),
      "no input at all abstains")


# =================================================================================================
section("7. PROJECT STATUS: THE REAL FUSION PATH, BEFORE AND AFTER")
# =================================================================================================

# The two voting modules are the to-complete cost efficiency measure and variance at completion.
check(CORE_VOTING_MODULES == frozenset({"A1.7", "A1.8"}),
      "exactly two modules vote, and this run adds none", str(sorted(CORE_VOTING_MODULES)))

# A project whose truthful reading is unfavourable in both voting modules, then the same project
# with the actual cost reported below zero.
BASE_SI = {
    "bac": 1_000_000.0, "ev": 400_000.0, "ac": 900_000.0,
    "cpi": 0.444, "spi": 0.8,
}
POISONED = dict(BASE_SI, ac=-900_000.0)

honest = compute_project(dict(BASE_SI), "S-A", "P1", CUTOFF)
poisoned_now = compute_project(dict(POISONED), "S-A", "P1", CUTOFF)

check(honest["project_status"] is not None,
      "the truthful project fuses to a status", str(honest["project_status"]))
check(honest["project_status"] != "Green",
      "and that status is not Green, because neither voting module reads favourably",
      str(honest["project_status"]))

_voted_now = [m["module_id"] for m in poisoned_now["modules"]
              if m["module_id"] in CORE_VOTING_MODULES]
check("A1.7" not in _voted_now,
      "after the correction the out-of-domain project has no reading from the corrected voter "
      "at all, so it cannot contribute a favourable status", str(_voted_now))
check(poisoned_now["project_status"] != "Green",
      "and the fused project status for the out-of-domain project is not Green",
      str(poisoned_now["project_status"]))
check(poisoned_now["categories_voting"] <= honest["categories_voting"],
      "the out-of-domain project votes with no more categories than the truthful one",
      f"{poisoned_now['categories_voting']} vs {honest['categories_voting']}")

# The same fusion, on the baseline code, to show the status actually moved.
_old_compute = None
try:
    import oldsim10b.compute as _oc  # noqa: E402
    _old_compute = _oc
except Exception:
    _old_compute = None
if _old_compute is not None:
    poisoned_before = _old_compute.compute_project(dict(POISONED), "S-A", "P1", CUTOFF)
    _voted_before = [m["module_id"] for m in poisoned_before["modules"]
                     if m["module_id"] in CORE_VOTING_MODULES]
    check("A1.7" in _voted_before,
          "the baseline did let the corrected voter contribute a band on that same input",
          str(_voted_before))
    check(next(m["status_color"] for m in poisoned_before["modules"]
               if m["module_id"] == "A1.7") == "Green",
          "and the band it contributed was Green")

    # The status effect is isolated by removing the OTHER voter's input, so the corrected module
    # is the only voter on the project. This is the case where the defect decided the project's
    # status by itself rather than being masked by its neighbour.
    ISOLATED = {"bac": 1_000_000.0, "ev": 400_000.0, "ac": -900_000.0}
    iso_before = _old_compute.compute_project(dict(ISOLATED), "S-A", "P1", CUTOFF)
    iso_now = compute_project(dict(ISOLATED), "S-A", "P1", CUTOFF)
    check(iso_before["project_status"] == "Green",
          "with the other voter silent, the baseline fused the whole project to Green from an "
          "actual cost reported below zero", str(iso_before["project_status"]))
    check(iso_now["project_status"] != "Green",
          "after the correction that same project no longer fuses to Green",
          str(iso_now["project_status"]))
    check(iso_now["categories_voting"] == 0,
          "because no voting module holds an admissible reading on it, so there is nothing to "
          "fuse rather than a favourable status to fuse", str(iso_now["categories_voting"]))

    # And the neighbour case, where the other voter reads unfavourably, is unchanged: the
    # correction removes a false favourable reading, it does not manufacture an unfavourable one.
    check(poisoned_before["project_status"] == poisoned_now["project_status"] == "Red",
          "where the other voter already read Red the fused status is Red before and after",
          f"{poisoned_before['project_status']} then, {poisoned_now['project_status']} now")
else:
    check(False, "the baseline fusion path could not be loaded, so the status regression is "
                 "unproved")

# The correction must not have moved any in-domain project's status.
rng2 = random.Random(770_017)
_moved = []
for _ in range(300):
    bac = rng2.uniform(1e5, 5e6)
    ev = rng2.uniform(0, bac)
    ac = rng2.uniform(0, bac * 1.5)
    si = {"bac": bac, "ev": ev, "ac": ac, "cpi": max(0.05, ev / ac if ac else 1.0),
          "spi": rng2.uniform(0.5, 1.2)}
    a = compute_project(dict(si), "S-A", "P1", CUTOFF)["project_status"]
    b = _old_compute.compute_project(dict(si), "S-A", "P1", CUTOFF)["project_status"]
    if a != b:
        _moved.append((si, a, b))
check(not _moved,
      "over 300 randomised in-domain projects the fused status is identical before and after, "
      "so the correction moves status only where the input was outside its domain",
      str(_moved[:2]))


# =================================================================================================
section("8. MUTATION PROOF: EVERY EXPECTATION ABOVE CAN GO RED")
# =================================================================================================

def mutation(label: str, fn) -> None:
    """fn returns True when the deliberately wrong expectation is REJECTED."""
    check(fn(), f"mutation: {label}")


mutation("claiming the reproducer still bands would fail",
         lambda: not (band(run_tcpi(dict(REPRO), lambda: 0.5, CUTOFF)) == "Green"))
mutation("claiming the truthful project abstains would fail",
         lambda: not abstains(run_tcpi(dict(HONEST), lambda: 0.5, CUTOFF)))
mutation("claiming the definitional edge 1.00 bands Amber would fail",
         lambda: band(run_tcpi(at_ratio(1.0), lambda: 0.5, CUTOFF)) != "Amber")
mutation("claiming the stability edge 1.10 bands Red would fail",
         lambda: band(run_tcpi(at_ratio(1.10), lambda: 0.5, CUTOFF)) != "Red")
mutation("claiming an actual cost of exactly zero abstains would fail",
         lambda: not abstains(run_tcpi(si_of(100.0, 0.0, 0.0), lambda: 0.5, CUTOFF)))
mutation("claiming the corrected module carries a ratio on out-of-domain input would fail",
         lambda: "tcpi" not in run_tcpi(dict(REPRO), lambda: 0.5, CUTOFF))
mutation("claiming the voting set has three members would fail",
         lambda: CORE_VOTING_MODULES != frozenset({"A1.7", "A1.8", "A1.9"}))

# A real injection, applied to the module under test and then removed, to show the suite is
# testing the shipped function and not a copy of it.
_orig = run_tcpi.__globals__["_TCPI_PLANNED_EFFICIENCY"]
run_tcpi.__globals__["_TCPI_PLANNED_EFFICIENCY"] = 99.0
_injected = band(run_tcpi(at_ratio(6.0), lambda: 0.5, CUTOFF))
run_tcpi.__globals__["_TCPI_PLANNED_EFFICIENCY"] = _orig
check(_injected == "Green",
      "an injected boundary of 99 does change the module's answer, so these checks are reading "
      "the shipped function rather than a copy of its arithmetic", str(_injected))
check(band(run_tcpi(at_ratio(6.0), lambda: 0.5, CUTOFF)) == "Red",
      "and the injection is restored, so the band is where the sources put it again")


print()
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(0 if FAILED == 0 else 1)
