#!/usr/bin/env python3
"""B7 verification: the seven guarantees for the server-side analytical layer."""

from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from app.simulation import (  # noqa: E402
    SIMULATION_VERSION, MissingModuleError, PortfolioModuleError, available_modules,
    compute_project, contributes_to_project_status, dst_fuse, unported_modules,
)
from app.simulation.models import VALIDATED, insufficient  # noqa: E402
from app.simulation.portfolio import PORTFOLIO_VALIDATED  # noqa: E402
from app.simulation.registry import registry_index, run_module  # noqa: E402
from app.simulation.rng import make_rng, seed_from  # noqa: E402

results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((ok, label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   {detail}" if detail and not ok else ""))


# The reporting period's data cutoff. Required everywhere: no module reads the system clock.
CUTOFF = "2026-07-31"

HEALTHY = {"spi": 1.05, "cpi": 1.02, "bac": 8000000, "actualPctComplete": 62}
DISTRESSED = {"spi": 0.70, "cpi": 0.80, "bac": 12500000, "actualPctComplete": 15}

print("=" * 78)
print("GUARANTEE 1: identical inputs produce byte-identical output")
print("=" * 78)
a = compute_project(HEALTHY, "sc-1", "P1", CUTOFF)
b = compute_project(HEALTHY, "sc-1", "P1", CUTOFF)
check(json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True),
      "compute_project is byte-identical across two runs")
check(a["seed"] == b["seed"], "seed identical across runs")

print()
print("=" * 78)
print("GUARANTEE 2: every available module is a validated module")
print("=" * 78)
check(set(available_modules()) == set(VALIDATED),
      f"available == validated ({len(VALIDATED)} modules)", str(available_modules()))
# THE CHECK THAT USED TO BE HERE COULD NOT FAIL.
#
# It asserted `len(unported_modules()) == 101 - len(VALIDATED)`. unported_modules() is
# `sorted(set(registry_index()) - set(VALIDATED))`, and registry_index() is exactly the 101 live
# CSV rows, so the left side IS 101 - len(VALIDATED) by construction. It was true whatever the
# code did, and it did not notice that Document Risk Score is declared and never implemented.
#
# It is replaced by a check against the genuinely unported set, computed here rather than taken
# from unported_modules(), because that function counts the five Group D modules as unported
# although portfolio.py implements them: it reports six where exactly one is. The over-report is
# asserted below rather than silently worked around, so that if the function is ever corrected
# this check fails loudly and is updated deliberately.
#
# Correcting unported_modules() itself means editing server/app/simulation/, which the work that
# wrote this check was not permitted to touch.
GENUINELY_UNPORTED = sorted(set(registry_index()) - set(VALIDATED) - set(PORTFOLIO_VALIDATED))
check(GENUINELY_UNPORTED == ["A4.1"],
      "exactly one declared computation is unported, and it is A4.1",
      str(GENUINELY_UNPORTED))
check(len(VALIDATED) + len(PORTFOLIO_VALIDATED) == 100,
      "the server registers 100 computations",
      str(len(VALIDATED) + len(PORTFOLIO_VALIDATED)))
check(sorted(set(unported_modules()) - set(GENUINELY_UNPORTED)) == sorted(PORTFOLIO_VALIDATED),
      "unported_modules() over-reports by exactly the Group D set (known defect, not yet fixed)",
      str(sorted(set(unported_modules()) - set(GENUINELY_UNPORTED))))
# Taken from the genuinely unported set, not unported_modules()[0]. That index happened to be
# A4.1 only because A sorts before D; had Document Risk Score been ported, [0] would have become
# a Group D id and run_module would have raised PortfolioModuleError, which the except clause
# below does not catch.
still_unported = GENUINELY_UNPORTED[0]
try:
    run_module(still_unported, HEALTHY, make_rng(1), CUTOFF)
    check(False, "an unported module raises rather than approximating", "no raise")
except MissingModuleError as exc:
    check("refuses to compute" in str(exc), f"unported {still_unported} raises MissingModuleError",
          str(exc)[:70])

print()
print("=" * 78)
print("GUARANTEE 3: PERT seeding is per (scenario_id, period)")
print("=" * 78)
p1a = compute_project(HEALTHY, "sc-1", "P1", CUTOFF)
p1b = compute_project(HEALTHY, "sc-1", "P1", CUTOFF)
p2 = compute_project(HEALTHY, "sc-1", "P2", CUTOFF)
other = compute_project(HEALTHY, "sc-2", "P1", CUTOFF)


def pert(run):
    return next(m for m in run["modules"] if m["module_id"] == "A2.1")


check(pert(p1a)["p80_duration_days"] == pert(p1b)["p80_duration_days"],
      "same scenario+period -> same P80", str(pert(p1a)["p80_duration_days"]))
check(pert(p1a)["p80_duration_days"] != pert(p2)["p80_duration_days"],
      "different period -> different P80",
      f"P1={pert(p1a)['p80_duration_days']} P2={pert(p2)['p80_duration_days']}")
check(pert(p1a)["p80_duration_days"] != pert(other)["p80_duration_days"],
      "different scenario -> different P80")
check(pert(p1a)["seed"] == p1a["seed"], "seed recorded on the stochastic module result")
check(seed_from("sc-1", "P1") == p1a["seed"], "seed derives from (scenario_id, period) only")

print()
print("=" * 78)
print("GUARANTEE 4: a Group C Red does not change project status")
print("=" * 78)
# Fuse directly: healthy condition categories plus a Red evidence-quality category.
condition = ["Green"]
with_c = dst_fuse(condition + ["Red"])
without_c = dst_fuse(condition)
check(with_c["status"] == "Red", "before: a Red evidence category would have sunk one Green",
      str(with_c["status"]))
check(without_c["status"] == "Green", "after: excluding Group C leaves it healthy",
      str(without_c["status"]))
check(contributes_to_project_status("C") is False, "Group C does not contribute")
check(contributes_to_project_status("A") is True and contributes_to_project_status("B") is True,
      "Groups A and B do contribute")
run = compute_project(HEALTHY, "sc-1", "P1", CUTOFF)
check(all(not c["contributes_to_project_status"]
          for k, c in run["category_statuses"].items() if c["group"] == "C"),
      "no Group C category is marked as contributing")

print()
print("=" * 78)
print("GUARANTEE 5: Group D is unreachable from a single-project path")
print("=" * 78)
d_ids = [k for k, v in registry_index().items() if v["group"] == "D"]
check(len(d_ids) == 5, f"registry has 5 Group D modules", str(len(d_ids)))
try:
    run_module(d_ids[0], HEALTHY, make_rng(1), CUTOFF)
    check(False, "Group D raises on a single-project path", "no raise")
except PortfolioModuleError as exc:
    check("3 or more projects" in str(exc), "Group D raises PortfolioModuleError",
          str(exc)[:70])
check(all(m["group"] != "D" for m in run["modules"]), "no Group D module appears in a run")

print()
print("=" * 78)
print("GUARANTEE 6: a module with missing inputs abstains")
print("=" * 78)
empty = compute_project({}, "sc-1", "P1", CUTOFF)
abst = insufficient("Test_Module")
check(abst["status_color"] is None and abst["insufficient_data"] is True,
      "the abstention contract is status_color None + insufficient_data")
check(dst_fuse([None]) is None, "an abstaining status contributes no mass")
check(dst_fuse(["Green", None]) is not None and dst_fuse(["Green", None])["status"] == "Green",
      "an abstention does not shift the fused band")
check("abstained" in empty, "run reports which modules abstained",
      str(empty.get("abstained")))

print()
print("=" * 78)
print("GUARANTEE 7: SIMULATION_VERSION on every result set")
print("=" * 78)
check(run["simulation_version"] == SIMULATION_VERSION,
      f"version stamped: {SIMULATION_VERSION}")
check(empty["simulation_version"] == SIMULATION_VERSION,
      "version stamped even when everything abstains")

print()
print("=" * 78)
print("PERIOD CUTOFF: required, recorded, and the only notion of \"now\"")
print("=" * 78)
check(run["period_cutoff"] == CUTOFF, "cutoff recorded on the result set", str(run.get("period_cutoff")))
try:
    compute_project(HEALTHY, "sc-1", "P1")          # type: ignore[call-arg]
    check(False, "period_cutoff is required, not optional", "call succeeded without it")
except TypeError:
    check(True, "period_cutoff is required, not optional")
src_dir = pathlib.Path(__file__).resolve().parents[1] / "app" / "simulation"
clock_reads = []
for f in sorted(src_dir.glob("*.py")):
    body = f.read_text(encoding="utf-8")
    for pat in ("datetime.now(", "time.time(", "date.today(", "datetime.utcnow("):
        if pat in body:
            clock_reads.append(f"{f.name}: {pat}")
check(not clock_reads, "no module in the analytical layer reads the system clock", str(clock_reads))

print()
print("=" * 78)
print("SAMPLE OUTPUT (distressed project)")
print("=" * 78)
d = compute_project(DISTRESSED, "sc-9", "P1", CUTOFF)
for m in d["modules"]:
    print("  %-6s %-30s %-6s %s" % (m["module_id"], m["method_class"], m["status_color"],
                                    m["evidence_metric"][:56]))
print("  category statuses:", {k: v["status"] for k, v in d["category_statuses"].items()})
print("  project status   :", d["project_status"], "| categories voting:", d["categories_voting"])

print()
print("=" * 78)
failed = [r for r in results if not r[0]]
print(f"RESULT: {len(results) - len(failed)}/{len(results)} checks passed")
for _, label, detail in failed:
    print(f"  FAILED: {label}  {detail}")
print("=" * 78)
sys.exit(1 if failed else 0)
