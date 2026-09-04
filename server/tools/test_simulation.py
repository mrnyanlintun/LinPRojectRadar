#!/usr/bin/env python3
"""B7 verification: the seven guarantees for the server-side analytical layer."""

from __future__ import annotations

import csv
import json
import pathlib
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from app.simulation import (  # noqa: E402
    SIMULATION_VERSION, MissingModuleError, available_modules,
    compute_project, contributes_to_project_status, dst_fuse, unported_modules,
)
from app.simulation.models import VALIDATED, insufficient  # noqa: E402

# RUN 135C, H9. `PortfolioModuleError` and `app.simulation.portfolio` were removed by 88e6ca0 at
# Run 97, together with the twenty Group D / B2 / B3 / B4 modules and the D1 Portfolio Health
# category. This file has not executed a single one of its checks since. The import is repaired by
# dropping the two removed names, and the checks that were ABOUT the removed feature are restated
# as checks that it is GONE, taking their expectation from tools/run96_removed.py -- the record of
# what was removed -- and not from the registry those checks audit. That independence is the whole
# point of run96_removed.py and it is what makes putting a retired row back a failure here.
import importlib.util as _il  # noqa: E402
_spec = _il.spec_from_file_location(
    "run96_removed", pathlib.Path(__file__).resolve().parent / "run96_removed.py")
run96_removed = _il.module_from_spec(_spec)
_spec.loader.exec_module(run96_removed)  # noqa: E402
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
# RUN 43, THE RETIREMENT. available_modules() is now the INTERSECTION of the implemented set with
# the modules in service, so it is no longer the whole of VALIDATED. The oracle here is NOT
# service_index() -- that would be asserting the function under test against its own expression.
# The retired set is re-derived HERE, by reading the retirement notes out of the registry CSV
# directly, so this check fails if available_modules() and the CSV ever disagree.
_CSV = pathlib.Path(__file__).resolve().parents[2] / "p0-baseline" / "module_renumbering_map.csv"
with _CSV.open(encoding="utf-8-sig", newline="") as _fh:
    _ROWS = list(csv.DictReader(_fh))
# RUN 135C. This read looked for RETIRED in the `notes` column and found nothing, so the retired
# set was silently empty and the two checks below compared available_modules() against the whole
# of VALIDATED -- weaker than intended, and unnoticed because the file has not run since Run 97.
# The CSV marks a retirement by writing RETIRED in `new_id`, not in `notes`. Both conventions are
# read here so the check survives either, and the count is REPORTED rather than required to be
# positive: a registry with nothing retired is a legitimate state and must not read as a defect.
_RETIRED_FROM_CSV = {str(r["new_id"]).strip() for r in _ROWS
                     if str(r.get("notes") or "").strip().upper().startswith("RETIRED")
                     or str(r["new_id"]).strip().upper() == "RETIRED"} - {"RETIRED", ""}
_RETIRED_ROWS = [r for r in _ROWS if str(r["new_id"]).strip().upper() == "RETIRED"]
print(f"  NOTE  registry CSV carries {len(_ROWS)} rows, {len(_RETIRED_ROWS)} marked RETIRED, "
      f"{len(_RETIRED_FROM_CSV)} retired ids still carrying a module id")
# The intent of the deleted `> 0` check was that the retired set be DERIVED from the CSV rather
# than imported from the code it audits. That intent is kept, and made non-vacuous, by requiring
# the CSV-derived set and the registry's own answer to agree in both directions.
from app.simulation import registry as _registry  # noqa: E402
check(set(_registry.retired_modules()) == _RETIRED_FROM_CSV,
      "the registry's retired set and the CSV-derived retired set agree",
      f"registry={sorted(_registry.retired_modules())} csv={sorted(_RETIRED_FROM_CSV)}")
check(set(available_modules()) == set(VALIDATED) - _RETIRED_FROM_CSV,
      f"available == validated minus the retired, derived from the CSV "
      f"({len(set(VALIDATED) - _RETIRED_FROM_CSV)} modules)",
      str(sorted(set(available_modules()) ^ (set(VALIDATED) - _RETIRED_FROM_CSV))))
check(not (set(available_modules()) & _RETIRED_FROM_CSV),
      "and not one retired module is available to compute",
      str(sorted(set(available_modules()) & _RETIRED_FROM_CSV)))
# THE CHECK THAT USED TO BE HERE COULD NOT FAIL.
#
# It asserted `len(unported_modules()) == 101 - len(VALIDATED)`. unported_modules() was
# `sorted(set(registry_index()) - set(VALIDATED))`, and registry_index() is exactly the 101 live
# CSV rows, so the left side IS 101 - len(VALIDATED) by construction. It was true whatever the
# code did, and it did not notice that Document Risk Score is declared and never implemented.
#
# Its replacement then had to compute the unported set here, by hand, because unported_modules()
# counted the five Group D modules as unported although portfolio.py implements them: it answered
# six where exactly one is. That workaround is gone. unported_modules() now subtracts
# PORTFOLIO_VALIDATED and is asked directly, which is the only way this check can notice the
# function regressing.
# RUN 135C. Was `unported_modules() == ["A4.1"]`. A4.1 is one of the seventy-one modules removed
# at Runs 96 and 97, so it is no longer declared and cannot be unported. The expectation comes
# from run96_removed.py, not from unported_modules().
assert "A4.1" in run96_removed.REMOVED
check(unported_modules() == [],
      "no declared computation is unported (A4.1, the last one, was removed at Run 96/97)",
      str(unported_modules()))
# RUN 135C. Was `len(VALIDATED) + len(PORTFOLIO_VALIDATED) == 100`. PORTFOLIO_VALIDATED is gone,
# and so is the hardcoded 101: the CSV now carries 33 declared rows, not 101, because Runs 96 and
# 97 removed their rows outright rather than marking them retired. The population is therefore
# re-derived from the CSV -- the declared set -- and cross-checked against run96_removed.py, which
# is independent of the registry. A removed id reappearing in the CSV fails the second check.
_DECLARED_FROM_CSV = {str(r["new_id"]).strip() for r in _ROWS
                      if str(r["new_id"]).strip()} - {"RETIRED"}
check(len(VALIDATED) == len(_DECLARED_FROM_CSV),
      f"the server registers every declared computation "
      f"({len(_DECLARED_FROM_CSV)} rows in module_renumbering_map.csv)",
      str(sorted(_DECLARED_FROM_CSV ^ set(VALIDATED))))
_readmitted = sorted(_DECLARED_FROM_CSV & set(run96_removed.REMOVED))
check(_readmitted == [],
      "not one of the 71 modules removed at Runs 96 and 97 is declared in the registry CSV",
      str(_readmitted))
# The registry and the two implementation sets must partition the CSV with nothing left over and
# nothing counted twice. This is what catches a Group D id being dropped from PORTFOLIO_VALIDATED,
# which the equality above would report only as a longer unported list.
check(set(registry_index()) == set(VALIDATED) | set(unported_modules()),
      "registered plus unported accounts for every declared computation, exactly once",
      str(sorted(set(registry_index()) ^ (set(VALIDATED) | set(unported_modules())))))
# Taken from unported_modules() directly now that it is correct. It cannot yield a Group D id:
# those are subtracted, so run_module cannot raise PortfolioModuleError here, which the except
# clause below does not catch.
#
# THE GUARD IS NOT DECORATION. Indexing [0] unguarded is how a suite dies with an IndexError
# instead of failing, and a crashed suite prints no RESULT line and reads exactly like a clean
# run. Fault injection produced precisely that: over-subtracting in unported_modules() emptied the
# list and killed this file silently. An empty list is now a red check, not a traceback.
# RUN 135C. The refusal guarantee is kept but its SUBJECT is changed, because the old subject no
# longer exists. Every declared module is implemented today, so unported_modules() is empty and
# the block below could only ever record a red check about its own missing fixture -- a check
# whose subject is gone is a retired check, not a failing one. The guarantee that matters is
# unchanged: an id the registry does not serve must be REFUSED, not approximated. The subject is
# now a retired id taken from run96_removed.py, which is what a caller would actually send.
_unported = unported_modules()
check(_unported == [],
      "every declared computation is implemented (nothing unported to refuse)", str(_unported))
_refusal_subject = run96_removed.REMOVED[0]
try:
    run_module(_refusal_subject, HEALTHY, make_rng(1), CUTOFF)
    check(False, f"retired {_refusal_subject} raises rather than approximating", "no raise")
except MissingModuleError as exc:
    check(True, f"retired {_refusal_subject} raises MissingModuleError", str(exc)[:70])

print()
print("=" * 78)
print("GUARANTEE 3: PERT seeding is per (scenario_id, period)")
print("=" * 78)
# The DISTRESSED project is used for the seeding guarantee, because the forecast module's
# spread is driven by the two indices: a project at or above plan on both has an optimistic and
# a pessimistic bound that coincide, so its forecast collapses deterministically to the mode and
# carries no sampling variation for two seeds to differ over. That collapse is the module's
# documented behaviour, not a defect, and it is asserted separately below.
p1a = compute_project(DISTRESSED, "sc-1", "P1", CUTOFF)
p1b = compute_project(DISTRESSED, "sc-1", "P1", CUTOFF)
p2 = compute_project(DISTRESSED, "sc-1", "P2", CUTOFF)
other = compute_project(DISTRESSED, "sc-2", "P1", CUTOFF)


# RUN 10. This guarantee used to be read off the criticality module. That module now abstains
# on the absent activity network, so it publishes no sampled figure to compare. The guarantee is
# unchanged and is read off the forecast module instead, which is seeded from the same
# (scenario_id, period) pair through the same holder and is the other stochastic module in the
# registry. Nothing about the seeding rule is relaxed here; only which module demonstrates it.
# RUN 36 CLOSURE, THE OWNER'S A1.1 RULING. A1.1 no longer publishes a stored row at all: its
# canonical input contract is not governed, so it is operationally disabled for insufficient input
# and the retained budget-and-index approximation is not reached from production. THE SEEDING
# GUARANTEE IS UNCHANGED AND IS STILL PROVED HERE -- it is read off the RETAINED ADAPTATION driven
# directly with the seeds compute_project derives, which is where that arithmetic still lives.
# This is a test calling preserved historical code on purpose; the assertion three lines below is
# what proves production cannot do the same.
from app.simulation.models_sim import run_monte_carlo as _retained_mc  # noqa: E402

_MC_SI = {"bac": 1_000_000.0, "cpi": 0.9, "spi": 0.95, "docRiskScore": 0.3}


def mc(run, si=None):
    """The retained adaptation, driven with the seed THIS run derived. Never a production route."""
    return _retained_mc(dict(si or _MC_SI), lambda: 0.5, run["seed"])


check(mc(p1a)["p80_eac"] == mc(p1b)["p80_eac"],
      "same scenario+period -> same P80", str(mc(p1a)["p80_eac"]))
check(mc(p1a)["p80_eac"] != mc(p2)["p80_eac"],
      "different period -> different P80",
      f"P1={mc(p1a)['p80_eac']} P2={mc(p2)['p80_eac']}")
check(mc(p1a)["p80_eac"] != mc(other)["p80_eac"],
      "different scenario -> different P80")
check(all(m["module_id"] != "A1.1" for m in p1a["modules"]),
      "and A1.1 publishes NO stored row, because its canonical input contract is not governed",
      str([m["module_id"] for m in p1a["modules"] if m["module_id"] == "A1.1"]))
check(seed_from("sc-1", "P1") == p1a["seed"], "seed derives from (scenario_id, period) only")
check(all(m["module_id"] != "A2.1" for m in p1a["modules"]),
      "the criticality module publishes no stored row without an activity network")
_h = compute_project(HEALTHY, "sc-1", "P1", CUTOFF)
_h2 = compute_project(HEALTHY, "sc-1", "P2", CUTOFF)
# THE DETERMINISTIC COLLAPSE is a property of the HEALTHY project's own indices -- at or above
# plan on both, the spread driver is nought and the Beta-PERT degenerates -- so the retained
# adaptation is driven with THOSE inputs rather than the generic ones above. Two different seeds
# must still give one answer, which is what "deterministic" means here.
check(mc(_h, HEALTHY)["p80_eac"] == mc(_h2, HEALTHY)["p80_eac"],
      "a project at or above plan on both indices collapses to one deterministic forecast",
      str(mc(_h, HEALTHY)["p80_eac"]))

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
# RUN 135C, H9. THIS GUARANTEE IS RESTATED, NOT DELETED. Group D and the D1 Portfolio Health
# category were removed by 88e6ca0 at Run 97 along with PortfolioModuleError, so "Group D is
# unreachable from a single-project path" is now the stronger fact that Group D is not reachable
# from ANY path because it is not in the registry at all. The five ids and the category name come
# from run96_removed.py, which is the record of the removal and does not change when the registry
# changes -- so a Group D row written back into the CSV fails here rather than being adopted.
_d_ids = [k for k, v in registry_index().items() if v["group"] == "D"]
check(_d_ids == [], "the registry has no Group D module (all five removed at Run 97)",
      str(_d_ids))
check("D1" in run96_removed.REMOVED_CATEGORIES_AT_RUN97,
      "run96_removed.py still records D1 Portfolio Health as removed at Run 97")
_d_back = sorted(m for m in run96_removed.REMOVED_AT_RUN97 if m in registry_index())
check(_d_back == [], "not one module removed at Run 97 is back in the registry", str(_d_back))
for _mid in run96_removed.REMOVED_AT_RUN97:
    try:
        run_module(_mid, HEALTHY, make_rng(1), CUTOFF)
        check(False, f"{_mid} is refused on the single-project path", "no raise")
    except MissingModuleError:
        pass
    except Exception as exc:  # noqa: BLE001
        check(False, f"{_mid} is refused with MissingModuleError",
              f"{type(exc).__name__}: {exc}"[:70])
# RUN 135C. Was `m["group"]`; the module rows a run publishes carry no "group" key, so this line
# died with a KeyError the moment the file was made to execute again. The group is a property of
# the REGISTRY row, not of the published module row, so it is looked up there.
_idx = registry_index()
check(all(_idx.get(m.get("module_id"), {}).get("group") != "D" for m in run["modules"]),
      "no Group D module appears in a run",
      str(sorted({m.get("module_id") for m in run["modules"]
                  if _idx.get(m.get("module_id"), {}).get("group") == "D"})))

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
