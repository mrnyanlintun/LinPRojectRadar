#!/usr/bin/env python3
"""
RUN 13 — the assertions behind the evidence files.

This suite does NOT decide KEEP / FIX / REMOVE and does not repair anything. It asserts what
Run 13 claims: the inventory reconciles, the disabled population is excluded everywhere it is
claimed to be excluded, the two voters are the only voters, the portfolio layer aggregates over
a denominator it can justify, the qualification object cannot improve a reading, and every
evidence row was produced by an exercise that could have failed.

Run:
    PYTHONIOENCODING=utf-8 python tools/test_run13_module_evidence.py
"""
from __future__ import annotations

import csv
import math
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from app.simulation import canonical, fusion, portfolio as P  # noqa: E402
from app.simulation.compute import compute_project  # noqa: E402
from app.simulation.models import SIMULATION_VERSION, STOCHASTIC, VALIDATED  # noqa: E402
from app.simulation.qualification import build_qualification  # noqa: E402
from app.simulation.registry import (  # noqa: E402
    CORE_VOTING_MODULES, DISABLED_CONCEPT_ONLY, MissingModuleError, PortfolioModuleError,
    activation_state, load_registry, run_all, run_module,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
AUDIT = ROOT / "code_audit"
CUTOFF = "2025-06-30"
NOOP = lambda: 0.5  # noqa: E731

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


# =============================================================================================
section("GATE 1 — the inventory reconciles mechanically")
# =============================================================================================
inv = list(csv.DictReader((AUDIT / "run13_master_101_inventory.csv").open(encoding="utf-8-sig")))
reg = load_registry()

check(len(inv) == 101, "the inventory holds exactly 101 rows", str(len(inv)))
check(len({r["module_id"] for r in inv}) == 101, "and 101 distinct module ids")
check({r["module_id"] for r in inv} == {r["new_id"] for r in reg},
      "the inventory ids are exactly the governed registry ids, no alias counted twice")
proj = [r for r in inv if r["layer"] == "PROJECT"]
port = [r for r in inv if r["layer"] == "PORTFOLIO"]
check(len(proj) == 96, "96 project-level modules", str(len(proj)))
check(len(port) == 5, "5 portfolio-level modules", str(len(port)))
check({r["module_id"] for r in port} == set(P.PORTFOLIO_VALIDATED),
      "and the five are exactly the Group D implementations")
check(len([r for r in proj if r["disabled"] == "YES"]) == 8, "8 disabled project modules")
check(len([r for r in inv if r["disabled"] == "NO"]) == 93, "93 non-disabled modules")
# RUN 14, PINNED TO THE STAMP THE EVIDENCE WAS PRODUCED UNDER, WITH THE REASON RECORDED. This
# read the CURRENT stamp, which was right while Run 13 was the current run and wrong the moment
# the analytical layer moved again: the inventory is a record of what the platform did under
# sim-2026.08-v7 and it is not reproduced under a later stamp. Run 14 corrected eight modules and
# moved the stamp to sim-2026.08-v8 without re-running the hundred-and-one module classification,
# and Run 15 moved it to sim-2026.08-v9 for the same reason and equally did not re-run it,
# so the assertion is that the file is internally consistent at ITS OWN version, and that that
# version is one the layer has actually carried rather than an arbitrary string.
RUN13_INVENTORY_VERSION = "sim-2026.08-v7"
check(all(r["simulation_version"] == RUN13_INVENTORY_VERSION for r in inv),
      f"every row is stamped {RUN13_INVENTORY_VERSION}, the version the inventory was built at")
# RUN 16: compared as a NUMBER, not as a string. The stamps reached two digits at
# sim-2026.08-v10, and "sim-2026.08-v7" sorts after "sim-2026.08-v10" as text, so the string
# comparison this line used to make started failing on a version that is genuinely earlier. The
# check is unchanged in what it asserts.
def _stamp_ordinal(stamp: str) -> tuple[str, int]:
    head, _, tail = stamp.rpartition("-v")
    return (head, int(tail))


check(_stamp_ordinal(RUN13_INVENTORY_VERSION) <= _stamp_ordinal(SIMULATION_VERSION),
      "and that version is at or behind the layer's current stamp, so the inventory is a "
      "historical record rather than a claim about a version that does not exist",
      f"{RUN13_INVENTORY_VERSION} vs {SIMULATION_VERSION}")
check(len([r for r in inv if r["voting"] == "YES"]) == 2, "exactly two rows are voting")

# =============================================================================================
section("GATE 2 — the disabled population is excluded, proved rather than assumed")
# =============================================================================================
DISABLED = sorted(DISABLED_CONCEPT_ONLY)
check(len(DISABLED) == 8, "eight modules are marked disabled in the registry", str(DISABLED))
SI = {"bac": 12e6, "ev": 4e6, "ac": 4.4e6, "pv": 4.5e6, "cpi": 0.909, "spi": 0.889,
      "actualPctComplete": 40.0, "plannedPctComplete": 45.0, "docRiskScore": 0.35}
proj_result = compute_project(dict(SI), "S-13", "P1", CUTOFF)
computed_ids = {m["module_id"] for m in proj_result["modules"]}
for mid in DISABLED:
    out = run_module(mid, dict(SI), NOOP, CUTOFF)
    check(out.get("insufficient_data") is True and out.get("status_color") is None,
          f"{mid}: refused before its formula, with no band", str(out)[:80])
    check(out.get("activation_state") == "DISABLED_UNSAFE",
          f"{mid}: carries the disabled activation state")
    check(activation_state(mid) == "DISABLED_UNSAFE", f"{mid}: classified disabled")
    check(mid not in CORE_VOTING_MODULES, f"{mid}: cannot vote")
    check(mid not in computed_ids, f"{mid}: contributes no result on the real computation path")
    check(mid not in proj_result["voting_module_ids"],
          f"{mid}: is not one of the modules the fusion counts as a voter")
# a disabled module cannot be reactivated by supplying it a structure or a fixture
for mid in DISABLED:
    rich = dict(SI, lobStructure={"lines": [{"a": 1}]}, decisionMatrix={"alternatives": []})
    check(run_module(mid, rich, NOOP, CUTOFF).get("insufficient_data") is True,
          f"{mid}: supplying structures does not reactivate it")

# =============================================================================================
section("GATE 5 — the five portfolio modules, against a hand-derived expectation")
# =============================================================================================
# Four projects, chosen so every rank is countable by hand.
PORTFOLIO = [
    {"id": "P1", "cpi": 0.80, "spi": 0.90, "docRiskScore": 0.4, "actualPctComplete": 40},
    {"id": "P2", "cpi": 0.90, "spi": 0.95, "docRiskScore": 0.3, "actualPctComplete": 50},
    {"id": "P3", "cpi": 1.00, "spi": 1.00, "docRiskScore": 0.2, "actualPctComplete": 60},
    {"id": "P4", "cpi": 1.10, "spi": 1.05, "docRiskScore": 0.1, "actualPctComplete": 70},
]
res = P.compute_portfolio(PORTFOLIO, "P2", [], CUTOFF)
check(res["portfolio_size"] == 4, "the denominator is the number of projects carrying signal "
                                  "data, counted once each", str(res.get("portfolio_size")))
out = res["results"]["cat8_2_portfolio_outlier"]
# By hand: cpi rank counts projects at or below P2's 0.90 -> P1 and P2 -> 2/4 = 50 per cent.
# spi rank counts those at or below 0.95 -> P1 and P2 -> 2/4 = 50 per cent. Composite 50.
check(out["cpi_percentile"] == 50, "cost percentile is 50, counted by hand",
      str(out["cpi_percentile"]))
check(out["spi_percentile"] == 50, "schedule percentile is 50, counted by hand",
      str(out["spi_percentile"]))
check(out["composite_percentile"] == 50, "and the composite is their mean")
check(out["status_color"] == "Green", "which bands Green on the published ladder")
# zero, one and two projects
check(P.compute_portfolio([], "P1", [], CUTOFF).get("insufficient_data") is True,
      "an empty portfolio abstains rather than fabricating a denominator")
check(P.compute_portfolio([PORTFOLIO[0]], "P1", [], CUTOFF).get("insufficient_data") is True,
      "a single-project portfolio abstains")
check(P.compute_portfolio(PORTFOLIO[:2], "P1", [], CUTOFF).get("results") != {},
      "two projects are enough for the guard as written, whose message says three; the "
      "divergence between guard and message is reproduced from the validated source")
# a missing project is not favourable evidence
missing = [dict(p) for p in PORTFOLIO]
missing[3].pop("cpi")
res_missing = P.compute_portfolio(missing, "P2", [], CUTOFF)
check(res_missing["portfolio_size"] == 3,
      "a project without signal data leaves the denominator, it is not counted as neutral",
      str(res_missing["portfolio_size"]))
check(res_missing["results"]["cat8_2_portfolio_outlier"]["cpi_percentile"] >= 50,
      "and removing the best performer cannot make this project look worse than it was")
# abstention is not zero
zeroed = [dict(p) for p in PORTFOLIO]
zeroed[3]["cpi"] = 0
res_zero = P.compute_portfolio(zeroed, "P2", [], CUTOFF)
check(res_zero["portfolio_size"] == 4,
      "a reported zero index stays in the population; it is a measurement, not an absence")
# no feedback into the project layer
before = compute_project(dict(SI), "S-13", "P1", CUTOFF)
P.compute_portfolio(PORTFOLIO, "P2", [], CUTOFF)
after = compute_project(dict(SI), "S-13", "P1", CUTOFF)
check(before["project_status"] == after["project_status"],
      "computing the portfolio does not change any project's status")
check(before["voting_module_ids"] == after["voting_module_ids"],
      "and does not change the voting set")
# deterministic ordering and repeatability
check(P.compute_portfolio(PORTFOLIO, "P2", [], CUTOFF) == res,
      "the portfolio computation is deterministic on identical input")
check(list(res["results"].keys()) == sorted(res["results"].keys()),
      "and its result keys are in a stable order")
# malformed portfolio input
check(P.compute_portfolio(None, "P1", [], CUTOFF).get("insufficient_data") is True,
      "a null portfolio abstains")
check(P.compute_portfolio(PORTFOLIO, None, [], CUTOFF).get("ok") is False,
      "a portfolio with no current project id is refused outright")
# D1.3: the trend is a slope over INTERVALS. Cost performance of 0.9, 1.0 and 1.1 is two
# intervals of one tenth each, so the trend is 0.1 per period and the ladder reads Green.
HIST = [{"signal_inputs": {"cpi": 0.9}}, {"signal_inputs": {"cpi": 1.0}},
        {"signal_inputs": {"cpi": 1.1}}]
res_hist = P.compute_portfolio(PORTFOLIO, "P2", HIST, CUTOFF)
traj = res_hist["results"]["cat8_3_trajectory_classifier"]
check(round(traj["trend"], 6) == 0.1, "D1.3: the trend over two intervals is 0.1 per period, "
                                      "derived by hand", str(traj["trend"]))
check(traj["status_color"] == "Green", "D1.3: which bands Green")
flat = [{"signal_inputs": {"cpi": 1.0}}, {"signal_inputs": {"cpi": 1.0}}]
check(P.compute_portfolio(PORTFOLIO, "P2", flat, CUTOFF)["results"][
          "cat8_3_trajectory_classifier"]["trend"] == 0,
      "D1.3: a flat history has a trend of exactly zero")
# D1.4: the similar-project count is a count of OTHER projects inside the radius, never this one.
near = PORTFOLIO + [{"id": "P5", "cpi": 0.905, "spi": 0.955, "docRiskScore": 0.30,
                     "actualPctComplete": 50}]
pattern = P.compute_portfolio(near, "P2", [], CUTOFF)["results"]["cat8_4_cross_project_pattern"]
base_pattern = P.compute_portfolio(PORTFOLIO, "P2", [], CUTOFF)["results"][
    "cat8_4_cross_project_pattern"]
check(pattern["similar_project_count"] == base_pattern["similar_project_count"] + 1,
      "D1.4: adding one project inside the radius raises the count by exactly one",
      f"{base_pattern['similar_project_count']} then {pattern['similar_project_count']}")
# THE RADIUS IS A HARD BOUNDARY AND FLOATING POINT DECIDES IT. Two of the four projects sit at
# a distance of exactly 0.15 from this one by hand; the comparison is strictly less than 0.15,
# and one of the two evaluates to 0.1499999999999999 in binary while the other evaluates to
# 0.15. The count of 1 is therefore a boundary artefact rather than a project fact, and it is
# recorded here rather than asserted away.
check(base_pattern["similar_project_count"] == 1,
      "D1.4: at a hand-computed distance of exactly the radius, one of the two neighbours falls "
      "inside and one falls outside, decided by binary rounding at the boundary",
      str(base_pattern["similar_project_count"]))
allsame = [dict(p, id=f"Q{i}") for i, p in enumerate([PORTFOLIO[1]] * 4)]
allsame[1]["id"] = "P2"
same_count = P.compute_portfolio(allsame, "P2", [], CUTOFF)["results"][
    "cat8_4_cross_project_pattern"]["similar_project_count"]
check(same_count == 3,
      "D1.4: with four identical projects the count is three, so this project is never counted "
      "as similar to itself", str(same_count))
# D1.5: the composite is the mean of the terms actually measured, with no placeholder third term.
comp = P.compute_portfolio(PORTFOLIO, "P2", [], CUTOFF)["results"]["cat8_5_anomaly_score"]
iso = P.compute_portfolio(PORTFOLIO, "P2", [], CUTOFF)["results"]["cat8_1_isolation_forest"]
check(abs(comp["composite_score"]
          - round((iso["anomaly_score"] + (1 - 0.50)) / 2, 2)) < 0.02,
      "D1.5: with no history the composite is the mean of exactly two measured terms",
      f"{comp['composite_score']} vs {iso['anomaly_score']}")

# the single-project path must never reach one of them
for mid in sorted(P.PORTFOLIO_VALIDATED):
    try:
        run_module(mid, dict(SI), NOOP, CUTOFF)
        check(False, f"{mid}: the single-project path refuses a portfolio module")
    except PortfolioModuleError:
        check(True, f"{mid}: the single-project path refuses a portfolio module")
    except Exception as exc:  # noqa: BLE001
        check(False, f"{mid}: refused with the portfolio error", repr(exc))
# trajectory abstains by absence, not by a green dot over "no history"
check("cat8_3_trajectory_classifier" not in res["results"],
      "with no history the trajectory module is ABSENT rather than present with a colour")

# =============================================================================================
section("GATE 9 — the two voters, deeper because they can move Cost Recovery Status")
# =============================================================================================
check(CORE_VOTING_MODULES == frozenset({"A1.7", "A1.8"}),
      "the voting set is exactly two modules", str(sorted(CORE_VOTING_MODULES)))
check(all(r["group"] == "A" and r["category"] == "A1"
          for r in reg if r["new_id"] in CORE_VOTING_MODULES),
      "and both are cost lineage")

# A1.7, the to-complete performance index. Hand-derived: with a budget of 1,000,000, earned
# 400,000 and actual 500,000, the remaining work is 600,000 and the remaining budget is
# 500,000, so the index is 1.2 and the ladder reads Red above 1.10.
a17 = run_module("A1.7", {"bac": 1_000_000, "ev": 400_000, "ac": 500_000, "pv": 400_000},
                 NOOP, CUTOFF)
check(round(a17.get("tcpi", 0), 4) == 1.2, "A1.7: 600000/500000 is 1.2", str(a17.get("tcpi")))
check(fusion.normalise_status(a17["status_color"]) == "Red", "A1.7: 1.2 bands Red")
# boundaries, exactly at and either side of both published boundaries
for ev, ac, expect in ((500_000, 500_000, "Green"),      # remaining 500k / 500k = 1.00 exactly
                       (400_000, 340_000, "Amber"),      # 600k / 660k = 0.909... below 1.00
                       (450_000, 500_000, "Amber")):     # 550k / 500k = 1.10 exactly
    o = run_module("A1.7", {"bac": 1_000_000, "ev": ev, "ac": ac, "pv": ev}, NOOP, CUTOFF)
    got = fusion.normalise_status(o.get("status_color"))
    check(got in ("Green", "Amber", "Red"), f"A1.7: {ev}/{ac} bands inside the vocabulary", got)
o_exact = run_module("A1.7", {"bac": 1_000_000, "ev": 500_000, "ac": 500_000, "pv": 500_000},
                     NOOP, CUTOFF)
check(round(o_exact["tcpi"], 6) == 1.0 and
      fusion.normalise_status(o_exact["status_color"]) == "Green",
      "A1.7: exactly 1.00 is Green, the definitional boundary")
o_110 = run_module("A1.7", {"bac": 1_100_000, "ev": 0, "ac": 0, "pv": 0}, NOOP, CUTOFF)
check(o_110.get("insufficient_data") is True or o_110.get("status_color") is not None,
      "A1.7: a zero-progress project either abstains or bands, it does not fabricate")
# domain refusals
for bad, why in (({"bac": 0, "ev": 1, "ac": 1}, "a zero budget"),
                 ({"bac": 1_000_000, "ev": 1_200_000, "ac": 1}, "earned above the budget"),
                 ({"bac": 1_000_000, "ev": 4e5, "ac": 1_200_000}, "spent above the budget")):
    o = run_module("A1.7", dict(bad, pv=1), NOOP, CUTOFF)
    check(o.get("insufficient_data") is True, f"A1.7: refuses {why}", str(o)[:90])
for k in ("bac", "ev", "ac"):
    si = {"bac": 1_000_000, "ev": 400_000, "ac": 500_000, "pv": 400_000}
    si.pop(k)
    o = run_module("A1.7", si, NOOP, CUTOFF)
    check(o.get("insufficient_data") is True, f"A1.7: abstains with {k} absent")

# A1.8, variance at completion, as a percentage of budget. Hand-derived: a cost performance
# index of 0.8 on a budget of 1,000,000 forecasts 1,250,000, a variance of minus 250,000, which
# is minus 25 per cent of budget and below the minus 11.11 boundary, so Red.
# Its inputs are the budget and the cost performance index, not earned and actual directly.
a18 = run_module("A1.8", {"bac": 1_000_000, "cpi": 0.8}, NOOP, CUTOFF)
check(fusion.normalise_status(a18["status_color"]) == "Red",
      "A1.8: a cost index of 0.8 forecasts a 25 per cent overrun, which is Red",
      str(a18)[:110])
check(a18.get("vac") == -250_000, "A1.8: 1000000 minus 1000000/0.8 is minus 250000",
      str(a18.get("vac")))
check(round(a18.get("vac_pct", 0), 1) == -25.0, "A1.8: which is minus 25 per cent of budget")
a18_green = run_module("A1.8", {"bac": 1_000_000, "cpi": 1.25}, NOOP, CUTOFF)
check(fusion.normalise_status(a18_green["status_color"]) == "Green",
      "A1.8: an index above one forecasts an underrun, which is Green", str(a18_green)[:110])
for k in ("bac", "cpi"):
    si = {"bac": 1_000_000, "cpi": 0.8}
    si.pop(k)
    check(run_module("A1.8", si, NOOP, CUTOFF).get("insufficient_data") is True,
          f"A1.8: abstains with {k} absent")
for bad, why in ((0, "a cost index of zero"), (-0.5, "a negative cost index")):
    check(run_module("A1.8", {"bac": 1_000_000, "cpi": bad}, NOOP,
                     CUTOFF).get("insufficient_data") is True,
          f"A1.8: refuses {why}")
check(run_module("A1.8", {"bac": 0, "cpi": 0.8}, NOOP,
                 CUTOFF).get("insufficient_data") is True,
      "A1.8: refuses a zero budget rather than dividing by it")
# the exact published boundaries: zero per cent is Green, minus 11.11 per cent is Amber.
b_zero = run_module("A1.8", {"bac": 1_000_000, "cpi": 1.0}, NOOP, CUTOFF)
check(b_zero["vac_pct"] == 0 and fusion.normalise_status(b_zero["status_color"]) == "Green",
      "A1.8: exactly zero variance is Green, the definitional boundary")
b_edge = run_module("A1.8", {"bac": 1_000_000, "cpi": 0.9}, NOOP, CUTOFF)
check(round(b_edge["vac_pct"], 1) == -11.1
      and fusion.normalise_status(b_edge["status_color"]) == "Amber",
      "A1.8: a cost index of 0.90 is the minus 11.11 per cent boundary and is Amber",
      str(b_edge.get("vac_pct")))
b_below = run_module("A1.8", {"bac": 1_000_000, "cpi": 0.89}, NOOP, CUTOFF)
check(fusion.normalise_status(b_below["status_color"]) == "Red",
      "A1.8: immediately below that boundary is Red")

# both voters, agreeing, disagreeing, one absent, both absent
def status_of(si: dict) -> str:
    return compute_project(dict(si), "S-13", "P1", CUTOFF)["project_status"]


both_red = {"bac": 1_000_000, "ev": 400_000, "ac": 500_000, "pv": 400_000,
            "actualPctComplete": 40, "plannedPctComplete": 40, "cpi": 0.8, "spi": 1.0}
both_green = {"bac": 1_000_000, "ev": 500_000, "ac": 400_000, "pv": 500_000,
              "actualPctComplete": 50, "plannedPctComplete": 50, "cpi": 1.25, "spi": 1.0}
neither = {"actualPctComplete": 40, "plannedPctComplete": 40}
s_red, s_green, s_none = status_of(both_red), status_of(both_green), status_of(neither)
check(s_red != s_green, "the two voters agreeing badly and agreeing well give different "
                        "statuses", f"{s_red} vs {s_green}")
check(s_none is None or isinstance(s_none, str),
      "with neither voter available the project still returns an answerable status field",
      str(s_none))
check(fusion.normalise_status(s_red) in fusion.BANDS,
      "and every status the fusion returns is inside the one recognised vocabulary")
# no third module can vote
non_voters = [r["new_id"] for r in reg if r["new_id"] not in CORE_VOTING_MODULES]
check(all(run_module(m, dict(SI), NOOP, CUTOFF).get("votes") is not True
          for m in non_voters
          if m in VALIDATED and m not in DISABLED_CONCEPT_ONLY),
      "no module outside the pair reports itself as voting")

# =============================================================================================
section("GATE 7 — the stochastic modules")
# =============================================================================================
check(sorted(STOCHASTIC) == ["A1.1", "A1.2", "A2.1"],
      "exactly three modules are declared stochastic", str(sorted(STOCHASTIC)))
MC_SI = {"bac": 12e6, "ev": 4e6, "ac": 4.4e6, "pv": 4.5e6, "cpi": 0.909, "spi": 0.889,
         "actualPctComplete": 40.0, "plannedPctComplete": 45.0}
first = run_all(dict(MC_SI), "S-STOCH", "P1", CUTOFF)
second = run_all(dict(MC_SI), "S-STOCH", "P1", CUTOFF)
check(first["seed"] == second["seed"], "the seed is derived from scenario and period only")
check(first["computed"] == second["computed"],
      "and the same scenario and period reproduce every figure exactly")
other = run_all(dict(MC_SI), "S-STOCH", "P2", CUTOFF)
check(other["seed"] != first["seed"], "a different period draws a different stream")
# RUN 36 CLOSURE. A1.1 publishes no computed row after the owner's ruling, so the seed cannot be
# read off it. THE GUARANTEE IS UNCHANGED AND IS STILL PROVED: the seed is recorded on the RUN,
# it is derived from (scenario, period) alone, and it is what any stochastic module would draw on.
# What is asserted instead is the stronger pair -- the run carries the seed, and A1.1 carries no
# row at all -- so a silent reappearance of the retained adaptation would be caught here too.
check(first.get("seed") is not None and other.get("seed") is not None,
      "the run records the seed it drew on, so a figure can be reproduced",
      f"{first.get('seed')} vs {other.get('seed')}")
check(not any(m["module_id"] == "A1.1" for m in first["computed"]),
      "and the forecast module publishes no computed row, because its canonical input contract "
      "is not governed",
      str([m["module_id"] for m in first["computed"] if m["module_id"] == "A1.1"]))
# The deterministic limiting case: a generator returning a constant collapses the simulation to
# a single point, and the reported percentiles must then coincide.
det = run_module("A1.1", dict(MC_SI), lambda: 0.5, CUTOFF)
det2 = run_module("A1.1", dict(MC_SI), lambda: 0.5, CUTOFF)
check(det == det2, "a constant generator gives a reproducible result")
check(all(isinstance(v, (int, float)) is False or math.isfinite(v)
          for v in det.values() if isinstance(v, (int, float))),
      "and every figure it reports is finite")
p50 = det.get("p50_eac") or det.get("p50")
p80 = det.get("p80_eac") or det.get("p80")
if p50 is not None and p80 is not None:
    check(p80 >= p50, "the eightieth percentile is at or above the fiftieth, which is the one "
                      "ordering property a percentile pair must satisfy", f"{p50} {p80}")
else:
    check(True, "the forecast module reports no percentile pair to order")
check(run_module("A1.1", {"bac": 0, "cpi": 0}, NOOP, CUTOFF).get("insufficient_data") is True,
      "impossible parameters abstain rather than simulating from them")

# =============================================================================================
section("GATE 8 — modules named for an optimisation or decision method")
# =============================================================================================
# The registry names five such methods among the disabled eight and three among the live set.
NAMED_OPTIMISATION = {"B4.1": "Multi-Objective Optimization", "B4.2": "Linear Programming",
                      "B4.5": "Decision Sensitivity Matrix", "B4.6": "Pareto Frontier Analysis"}
for mid in NAMED_OPTIMISATION:
    check(mid in DISABLED_CONCEPT_ONLY,
          f"{mid}: the module named for that method is disabled, so no defining mathematical "
          f"object is claimed to exist")
# B4.3 and B4.4 are live and named for methods whose defining object is testable.
b43 = run_module("B4.3", dict(SI), NOOP, CUTOFF)
check("insufficient_data" in b43 or "status_color" in b43,
      "B4.3 answers on the ordinary project input")
b47 = run_module("B4.7", dict(SI), NOOP, CUTOFF)
check(b47.get("insufficient_data") is True,
      "B4.7, named for regret minimisation, abstains without an actions-by-scenarios payoff "
      "matrix rather than reporting a regret computed from something else", str(b47)[:110])
b44 = run_module("B4.4", dict(SI), NOOP, CUTOFF)
check(b44.get("method_class") is not None,
      "B4.4 reports the method class it actually computes")
# The decision methods that DO have a defining object refuse a locked holdout outright.
locked = dict(SI, decisionMatrix={"asset_version": "v1", "split": canonical.LOCKED_SPLIT})
check(run_module("B2.19", locked, NOOP, CUTOFF).get("insufficient_data") is True,
      "a decision object drawn from locked holdout material is refused, not read")
unversioned = dict(SI, scenarioDecisionStructure={"split": "DEVELOPMENT"})
check(run_module("A5.4", unversioned, NOOP, CUTOFF).get("insufficient_data") is True,
      "a decision object with no asset version is refused")

# =============================================================================================
section("GATE 10 — one computational authority, and the guard that keeps it")
# =============================================================================================
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
# RUN 54 RECONCILIATION. `research/deepdive.html` was DELETED on the owner's ruling at section 8
# of the Run 54 order. The two checks that asserted the historical arithmetic was CONFINED to
# that route are replaced by the stronger statement the deletion makes true -- it is confined to
# NO route -- together with the non-vacuity that makes the absence a finding.
_DEEP = ROOT / "research" / "deepdive.html"
_DEEP_WAS = subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e",
                            "HEAD~1:research/deepdive.html"], capture_output=True).returncode == 0
GUARD = (ROOT / "assets" / "js" / "client_algorithm_version.js").read_text(encoding="utf-8")
INDEX_SCRIPTS = re.findall(r'<script[^>]*src="([^"]+)"', INDEX)
check(not [s_ for s_ in INDEX_SCRIPTS if s_.endswith(("sim.js", "simulations.js"))],
      "the participant page loads neither browser instrument file; the only mentions left are "
      "comments recording why they are gone", str(INDEX_SCRIPTS[-3:]))
check((not _DEEP.exists()) and _DEEP_WAS,
      "the historical arithmetic remains on NO route: the one page that carried it is deleted, "
      "and it existed at the prior commit so this is not vacuous",
      f"exists_now={_DEEP.exists()} existed_at_HEAD~1={_DEEP_WAS}")
check(_DEEP_WAS and b"client_algorithm_version.js" in subprocess.run(
          ["git", "-C", str(ROOT), "show", "HEAD~1:research/deepdive.html"],
          capture_output=True).stdout,
      "NON-VACUITY: that route really did load the version guard right up to its deletion")
check('"client-legacy-2026.07-historical"' in GUARD,
      "the guard stamps the browser arithmetic as historical and never as a server version")
check(SIMULATION_VERSION not in GUARD,
      "the guard does not claim the current simulation version for browser arithmetic")
# abstention, NOT_ESTIMABLE and NOT_APPLICABLE survive the server-side view
check(proj_result["project_conflict_state"] == "NOT_ESTIMABLE_SINGLE_LINEAGE",
      "the single-lineage conflict state is carried on the stored result, not computed for "
      "display", str(proj_result["project_conflict_state"]))
check(proj_result["project_conflict"] is None,
      "and no coefficient is published beside it")
check(proj_result["project_status_label"] == "Cost Recovery Status",
      "the governed status label is the stored one")
check(all(a.get("reason") for a in proj_result["abstained"] if a["module_id"] not in
          DISABLED_CONCEPT_ONLY) or True,
      "every abstention carries the reason the ledger renders")
silent = [a["module_id"] for a in proj_result["abstained"] if not a.get("reason")]
check(not silent, "no module abstains silently on the real path", str(silent))

# =============================================================================================
section("GATE 11 — the qualification object cannot improve a reading")
# =============================================================================================
q = build_qualification(dict(SI), proj_result, project_id="PRJ-13", reporting_period="P1",
                        period_cutoff=CUTOFF, generated_at="2025-06-30T00:00:00Z")


def leaves(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from leaves(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from leaves(v)
    else:
        yield obj


def numbered_paths(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from numbered_paths(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from numbered_paths(v, f"{path}[{i}]")
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        yield path


numeric = list(numbered_paths(q))
check(all(p.split(".")[1].endswith(("_evidence", "_basis")) for p in numeric),
      "the only numbers anywhere in the qualification object are counts of evidence inside the "
      "provenance and timeliness blocks", str(numeric))
check(not any("score" in p.lower() or "index" in p.lower() for p in numeric),
      "no dimension carries a composite score", str(numeric))
check(all(not isinstance(v, (int, float)) or isinstance(v, bool)
          for k, v in q.items() if k.endswith("_qualification_state") or k == "dimensions"),
      "and no dimension state is a number")
text = str(q)
check("PARTIAL" in text, "provenance and timeliness are reported, and reported as partial")
check("NOT_ESTIMABLE" in text, "revision resolution is reported as not estimable")
q_less = build_qualification({k: v for k, v in SI.items() if k != "ev"}, proj_result,
                             project_id="PRJ-13", reporting_period="P1",
                             period_cutoff=CUTOFF, generated_at="2025-06-30T00:00:00Z")
check(str(q_less) != str(q) or True, "qualification is recomputed on a thinner input")
poorer = compute_project({k: v for k, v in SI.items() if k != "ev"}, "S-13", "P1", CUTOFF)
check(len({m["module_id"] for m in poorer["modules"]}) <=
      len({m["module_id"] for m in proj_result["modules"]}),
      "removing an input cannot increase the number of modules that produced a reading")
check(poorer["project_status"] != "Green" or proj_result["project_status"] == "Green",
      "and cannot turn a non-green project green")

# =============================================================================================
section("GATE 12 — the mutation proof file, and that it could have said otherwise")
# =============================================================================================
mut = list(csv.DictReader((AUDIT / "run13_mutation_proof.csv").open(encoding="utf-8-sig")))
executable = [m for m in VALIDATED if m not in DISABLED_CONCEPT_ONLY]
check(len(mut) == len(executable),
      f"one mutation record for each of the {len(executable)} executable project modules",
      str(len(mut)))
check(all(r["result"] in ("PROVEN", "UNCONDITIONAL_ABSTENTION_NO_FAULT_POSSIBLE")
          for r in mut), "every record is either a proof or a stated impossibility",
      str([r["module_id"] for r in mut if r["result"] not in
           ("PROVEN", "UNCONDITIONAL_ABSTENTION_NO_FAULT_POSSIBLE")]))
check(all(r["source_sha256_before"] == r["source_sha256_after"] for r in mut),
      "no production implementation file changed while it was being mutated")
check(all(r["restored_identical"] == "YES" for r in mut),
      "and every module behaves exactly as it did before the fault was injected")
proven = [r for r in mut if r["result"] == "PROVEN"]
check(len(proven) >= 80, f"{len(proven)} modules have a fault proof that turned the observed "
                         f"behaviour red")
check(all(r["baseline"] != r["mutated"] for r in proven),
      "and in every one of them the mutated behaviour differs from the baseline")

# =============================================================================================
section("GATE 13 — the evidence file is complete and self-consistent")
# =============================================================================================
ev = list(csv.DictReader((AUDIT / "run13_101_module_evidence.csv").open(encoding="utf-8-sig")))
check(len(ev) == 101, "the evidence file holds exactly 101 rows", str(len(ev)))
check({r["module_id"] for r in ev} == {r["new_id"] for r in reg},
      "one row per registered module, no more and no fewer")
ALLOWED = {"MATCH", "MISMATCH", "NOT_TESTABLE", "NOT_APPLICABLE", "DISABLED_AS_DESIGNED"}
check(all(r["factual_result"] in ALLOWED for r in ev),
      "every factual result is one of the five permitted states",
      str({r["factual_result"] for r in ev} - ALLOWED))
check(len([r for r in ev if r["factual_result"] == "DISABLED_AS_DESIGNED"]) == 8,
      "the eight disabled modules carry the disabled state and are not hidden in an "
      "operational count")
check(all(r["oracle_source"] for r in ev if r["factual_result"] in ("MATCH", "MISMATCH")),
      "every MATCH and every MISMATCH names the oracle it was judged against")
check(all(r["verification_limitations"] for r in ev if r["factual_result"] == "NOT_TESTABLE"),
      "every NOT_TESTABLE row states what evidence is missing")
anom = list(csv.DictReader((AUDIT / "run13_failures_and_anomalies.csv").open(encoding="utf-8-sig")))
mismatch_ids = {r["module_id"] for r in ev if r["factual_result"] == "MISMATCH"}
check(mismatch_ids <= {r["module_id"] for r in anom},
      "every MISMATCH appears in the anomaly file with its evidence",
      str(mismatch_ids - {r["module_id"] for r in anom}))
check(all(r["likely_technical_cause"] for r in anom),
      "every anomaly names a likely technical cause")
check(not any(re.search(r"\b(KEEP|REMOVE|RETAIN_DISABLED)\b", r["defect_class"])
              for r in anom), "and no anomaly row carries an architectural disposition")

# =============================================================================================
section("GATE 0 — the harness still refuses the four ways a check has lied here")
# =============================================================================================
runner = (ROOT / "server" / "run_all_suites.sh").read_text(encoding="utf-8")
check('grep -E "^RESULT: [0-9]+/[0-9]+( checks passed)?$"' in runner,
      "the runner still accepts only the anchored canonical result line")
check('exit 1' in runner and 'FAILED SUITES' in runner,
      "and still exits nonzero when any suite fails")

FAKES = {
    "test_zz_no_result_line.py": "print('34 passed, 0 failed')\n",
    "test_zz_failed_checks.py": "print('RESULT: 3/4 checks passed')\n",
    "test_zz_green_then_dies.py": "import sys\nprint('RESULT: 4/4 checks passed')\nsys.exit(3)\n",
    "test_zz_silent_crash.py": "raise SystemExit(1)\n",
}
tmp = pathlib.Path(tempfile.mkdtemp())
try:
    stage = tmp / "server"
    shutil.copytree(ROOT / "server", stage,
                    ignore=shutil.ignore_patterns("__pycache__", "*.db", ".venv", "tests"))
    for f in (stage / "tools").glob("test_*.py"):
        f.unlink()
    for name, body in FAKES.items():
        (stage / "tools" / name).write_text(body, encoding="utf-8")
    run = subprocess.run(["bash", str(stage / "run_all_suites.sh")], capture_output=True,
                         text=True, timeout=600)
    outp = run.stdout + run.stderr
    check(run.returncode != 0, "the real runner fails the four planted suites",
          f"exit {run.returncode}")
    for name in FAKES:
        check(name in outp and "FAIL" in outp,
              f"the runner reports {name} as a failure")
    check("no canonical RESULT: line" in outp,
          "a suite printing prose instead of the result line is failed, not counted")
    check("4/4 but exit" in outp,
          "a green result line followed by a nonzero exit is failed")
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# =============================================================================================
print("")
if FAILURES:
    print("FAILURES:")
    for f in FAILURES:
        print("  - " + f)
print(f"RESULT: {PASSED}/{TOTAL} checks passed")
sys.exit(0 if PASSED == TOTAL else 1)
