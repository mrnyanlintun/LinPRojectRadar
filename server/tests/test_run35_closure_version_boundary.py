#!/usr/bin/env python3
"""
RUN 35 FINAL CLOSURE: THE v22 -> v23 SIMULATION VERSION BOUNDARY, PROVED BY EXECUTION.

The v22 line is extracted FROM ITS GIT OBJECT into a throwaway package and EXECUTED beside the
current one on identical governed inputs. A source diff would prove only that the text changed,
and this programme has already had one agent claim a divergence that did not exist because the
predecessor abstained. Nothing here is inferred.

Required and asserted below:
  * A1.7 genuine divergence on the Run-35 reference fixture;
  * A1.7 genuine divergence on the band-boundary fixture -- a STATUS, not only a number;
  * A1.8 genuine divergence on the Run-35 reference fixture;
  * genuine NON-divergence for modules this closure did not touch, and for an A1.7 input on which
    the rounded and the full-precision value agree;
  * the predecessor still stamps itself v22, so no predecessor was regenerated to agree with the
    corrected behaviour.

Writes code_audit/run35_v22_v23_voter_execution_proof.csv.
"""

from __future__ import annotations

import csv
import pathlib
import subprocess
import sys
import tempfile
from fractions import Fraction as F

_HERE = pathlib.Path(__file__).resolve().parent
ROOT = _HERE.parents[1]
sys.path.insert(0, str(ROOT / "server"))

#: The exact commit that merged Run 35 to main. The v22 line is read from this git object, and it
#: is the commit the closure's owner prompt names as the expected starting state.
V22_COMMIT = "034cf03be257f4582bc1a856262c56ea11bb4558"
OUT = ROOT / "code_audit" / "run35_v22_v23_voter_execution_proof.csv"

PASSED = 0
FAILED = 0
FAILURES: list[str] = []
ROWS = [["record_type", "module", "input", "v22_behaviour", "v23_behaviour", "divergence",
         "observed_by", "result"]]


def check(ok, label, detail=""):
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}" + (f"  [{detail}]" if detail else ""))
    else:
        FAILED += 1
        FAILURES.append(label)
        print(f"  FAIL  {label}  [{detail}]")
    return bool(ok)


def head(t):
    print("\n" + "=" * 94 + f"\n{t}\n" + "=" * 94)


def git_show(path, rev=V22_COMMIT):
    return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout


# =================================================================================================
head("1. THE STAMP AND ITS HISTORY, APPEND-ONLY AND READ OUT OF GIT")
# =================================================================================================
from app.simulation.models import (                                    # noqa: E402
    SIMULATION_VERSION, SIMULATION_VERSION_HISTORY, SIMULATION_VERSION_SUPERSEDED,
)

# RUN 36 REPAIR, the same defect and the same repair as `test_run32_closure_version_boundary`.
# These are settled claims about what the RUN-35 CLOSURE did, and they were being taken from the
# LIVE TREE, so any legitimate later append falsified them -- which Run 36 did, adding v24 for
# the A1.1 band withdrawal. A boundary claim about a past run must be read from that run's own
# object. What stays a LIVE assertion is the only property that genuinely is one: that v23
# survives in the history exactly once, so a later run appended beside it rather than over it.
V23_COMMIT = "dafc35d35bafe5af76e1ce48ef7daceab9daed2c"
_v23_src = git_show("server/app/simulation/models.py", V23_COMMIT)
check('SIMULATION_VERSION = "sim-2026.08-v23"' in _v23_src,
      f"the stamp at the Run-35 closure head {V23_COMMIT[:7]} is sim-2026.08-v23, read out of "
      f"git rather than out of the working tree")
check('SIMULATION_VERSION_SUPERSEDED = "sim-2026.08-v22"' in _v23_src,
      "and the line it superseded is named there as v22")
check(SIMULATION_VERSION_HISTORY.count("sim-2026.08-v23") == 1,
      "and v23 survives exactly once in the live history, so a later run appended beside it "
      "rather than overwriting it", SIMULATION_VERSION)
check(SIMULATION_VERSION_HISTORY.index("sim-2026.08-v23")
      == SIMULATION_VERSION_HISTORY.index("sim-2026.08-v22") + 1,
      "it directly follows sim-2026.08-v22 in the history")
check(len(SIMULATION_VERSION_HISTORY) == len(set(SIMULATION_VERSION_HISTORY)),
      "EVERY SIMULATION IDENTIFIER IS UNIQUE", f"{len(SIMULATION_VERSION_HISTORY)} stamps")
_old_src = git_show("server/app/simulation/models.py")
_seg = _old_src.split("SIMULATION_VERSION_HISTORY: tuple[str, ...] = (")[1].split(")")[0]
_old = tuple(s.strip().strip('",') for s in _seg.replace("\n", " ").split()
             if s.strip().strip('",').startswith("sim-"))
check(SIMULATION_VERSION_HISTORY[:len(_old)] == _old,
      f"the history at {V22_COMMIT[:7]} is a strict PREFIX of the history now, read out of git",
      f"{len(_old)} -> {len(SIMULATION_VERSION_HISTORY)}")
_v23_seg = _v23_src.split("SIMULATION_VERSION_HISTORY: tuple[str, ...] = (")[1].split(")")[0]
_v23_hist = tuple(x.strip().strip('",') for x in _v23_seg.replace("\n", " ").split()
                  if x.strip().strip('",').startswith("sim-"))
check(_v23_hist[len(_old):] == ("sim-2026.08-v23",),
      "and AT THE CLOSURE HEAD it had grown by exactly the one stamp this closure was authorised "
      "to add", str(_v23_hist[len(_old):]))
check(SIMULATION_VERSION_HISTORY[:len(_v23_hist)] == _v23_hist,
      "and the closure head's history is still a strict PREFIX of the live history, so nothing "
      "this closure recorded has been rewritten since",
      f"{len(_v23_hist)} -> {len(SIMULATION_VERSION_HISTORY)}")
check('SIMULATION_VERSION = "sim-2026.08-v22"' in _old_src,
      "PREDECESSOR RECONSTRUCTION: the v22 line reconstructs from its own git object and still "
      "says v22, so no predecessor stamp was regenerated to describe v23 behaviour")
check("_round3(remaining_work / remaining_budget)" in git_show(
          "server/app/simulation/models_evm.py"),
      "and the v22 object still carries the DEFECTIVE line -- the rounded value fed to the band "
      "-- so the failing predecessor is preserved rather than quietly corrected")


# =================================================================================================
head("2. THE v22 LINE, EXTRACTED FROM ITS GIT OBJECT AND EXECUTED")
# =================================================================================================
_TMP = tempfile.mkdtemp(prefix="run35-v22-")
_FAKE = pathlib.Path(_TMP) / "repo"
_PKG = _FAKE / "server" / "app" / "oldsim35"
_PKG.mkdir(parents=True)
(_FAKE / "p0-baseline").mkdir(parents=True)
(_FAKE / "p0-baseline" / "module_renumbering_map.csv").write_text(
    git_show("p0-baseline/module_renumbering_map.csv"), encoding="utf-8")
_names = subprocess.run(["git", "ls-tree", "--name-only", V22_COMMIT,
                         "server/app/simulation/"], cwd=ROOT, capture_output=True, text=True,
                        check=True).stdout.split()
_py = [n for n in _names if n.endswith(".py")]
if len(_py) < 10:
    raise SystemExit("v22 extraction found no simulation sources; refusing to run half a proof")
for _n in _py:
    (_PKG / pathlib.Path(_n).name).write_text(git_show(_n), encoding="utf-8")
(_PKG / "__init__.py").write_text("", encoding="utf-8")
sys.path.insert(0, str(_PKG.parent))

import oldsim35.models as old_models                                   # noqa: E402
import oldsim35.models_evm as OLDEVM                                   # noqa: E402

from app.simulation import models_evm as NEWEVM                        # noqa: E402
from app.simulation import registry as REG                             # noqa: E402

check(old_models.SIMULATION_VERSION == "sim-2026.08-v22",
      f"the package extracted from {V22_COMMIT[:7]} is stamped v22", old_models.SIMULATION_VERSION)
check(OLDEVM.__name__.startswith("oldsim35") and NEWEVM is not OLDEVM,
      "and it carries its OWN earned-value layer, executed below rather than described")


# =================================================================================================
head("3. IDENTICAL GOVERNED INPUTS, BOTH LINES EXECUTED")
# =================================================================================================
NOOP = (lambda: 0.5)
CUT = "2026-06-30"

#: The Run-35 governed corpus scalars, the same evidence the partial reference standards scored.
CORPUS = {"bac": 1_000_000.0, "ev": 400_000.0, "ac": 440_000.0, "pv": 450_000.0,
          "cpi": 0.909, "spi": 0.889, "docRiskScore": 0.35,
          "actualPctComplete": 40.0, "plannedPctComplete": 45.0}
#: The band-boundary fixture the pre-change measurement found by SEARCH, not by assertion.
BOUNDARY = {"bac": 1_000_000.0, "ev": 989_999.0, "ac": 990_000.0}
#: An A1.7 input on which the rounded and the full-precision value are the same number, so the
#: two lines must agree. This is the legitimate non-divergence inside the changed module itself.
EXACT = {"bac": 1_000_000.0, "ev": 400_000.0, "ac": 500_000.0}     # 600000/500000 = 1.2 exactly


def both(fn_name, si):
    o = getattr(OLDEVM, fn_name)(dict(si), NOOP, CUT)
    n = getattr(NEWEVM, fn_name)(dict(si), NOOP, CUT)
    return o, n


def row(kind, module, label, o, n, diverges, observed):
    ROWS.append([kind, module, label, o, n, "YES" if diverges else "NO", observed,
                 "PASS"])


# ---- divergence 1: A1.7 on the Run-35 reference fixture
o, n = both("run_tcpi", CORPUS)
_ref_f = (CORPUS["bac"] - CORPUS["ev"]) / (CORPUS["bac"] - CORPUS["ac"])
d1 = check(o["tcpi"] != n["tcpi"],
           "DIVERGENCE 1: A1.7 emits a different analytical value on the Run-35 reference "
           "fixture", f"v22 {o['tcpi']} -> v23 {n['tcpi']}")
check(n["tcpi"] == _ref_f,
      "and the v23 value IS the published identity evaluated in the application's own arithmetic",
      f"{n['tcpi']} == {_ref_f}")
check(F(str(o["tcpi"])) - F(600000, 560000) == F(-3, 7000),
      "while the v22 value carries exactly the -3/7000 discrepancy Run 35 recorded",
      str(F(str(o["tcpi"])) - F(600000, 560000)))
row("DIVERGENCE", "A1.7", "Run-35 governed corpus", f"tcpi={o['tcpi']} ({o['status_color']})",
    f"tcpi={n['tcpi']} ({n['status_color']})", True, "executed both extracted packages")

# ---- divergence 2: A1.7 band boundary -- a STATUS moves
o, n = both("run_tcpi", BOUNDARY)
d2 = check(o["status_color"] != n["status_color"],
           "DIVERGENCE 2: A1.7 assigns a DIFFERENT BAND on the boundary fixture -- premature "
           "rounding decided a status", f"v22 {o['status_color']} -> v23 {n['status_color']}")
# RUN 135C, H8. Was `n["status_color"] == "Amber"`, the pre-Run-114 answer for an index just
# above 1.00. Run 114 (fc9d60c) inserted the owner-calibrated Yellow rung -- its report, section
# 6, states the A1.7 ladder as "Green | <= 1.00 / Yellow | > 1.00 to 1.05 / Amber | > 1.05 to
# 1.10 / Red | > 1.10" -- so an index of 1.0001 is Yellow. The expectation is taken from that
# order, not from the ladder under test. What this check is FOR is unchanged and is not weakened:
# v22 must answer Green where the full-precision index is above 1.00, and v23 must answer
# something adverse; the adverse band is now named as the Run 114 order names it.
check(o["status_color"] == "Green" and n["status_color"] == "Yellow",
      "and the direction is the one the pre-change measurement recorded: v22 answered Green "
      "where the full-precision index is above 1.00, and v23 answers the Run 114 Yellow rung "
      "(fc9d60c REPORT_2026-09-02_run114.md s6)",
      f"{o['status_color']} -> {n['status_color']}")
row("DIVERGENCE", "A1.7", "band-boundary fixture bac=1e6 ev=989999 ac=990000",
    f"tcpi={o['tcpi']} band={o['status_color']}", f"tcpi={n['tcpi']} band={n['status_color']}",
    True, "executed both extracted packages")

# ---- divergence 3: A1.8 on the Run-35 reference fixture
o, n = both("run_vac", CORPUS)
_vref_f = CORPUS["bac"] - CORPUS["bac"] / CORPUS["cpi"]
d3 = check(o["vac"] != n["vac"],
           "DIVERGENCE 3: A1.8 emits a different analytical value on the Run-35 reference "
           "fixture", f"v22 {o['vac']} -> v23 {n['vac']}")
check(n["vac"] == _vref_f,
      "and the v23 value IS BAC - BAC/CPI in the application's own arithmetic",
      f"{n['vac']} == {_vref_f}")
check(F(str(o["vac"])) - (F(1_000_000) - F(1_000_000) / F("0.909")) == F(10, 909),
      "while the v22 value carries exactly the +10/909 discrepancy Run 35 recorded",
      str(F(str(o["vac"])) - (F(1_000_000) - F(1_000_000) / F("0.909"))))
check(o["status_color"] == n["status_color"],
      "A1.8's BAND is unchanged, because it already read the full-precision percentage: no "
      "status defect is claimed for this module", f"{o['status_color']}")
row("DIVERGENCE", "A1.8", "Run-35 governed corpus", f"vac={o['vac']} ({o['status_color']})",
    f"vac={n['vac']} ({n['status_color']})", True, "executed both extracted packages")

# ---- non-divergence A: A1.7 where rounding is exact
o, n = both("run_tcpi", EXACT)
check(o["tcpi"] == n["tcpi"] and o["status_color"] == n["status_color"],
      "NON-DIVERGENCE A: on an input whose index is exactly representable at three decimals, "
      "A1.7 returns the identical value AND the identical band under both lines",
      f"{o['tcpi']} / {o['status_color']}")
row("NON_DIVERGENCE", "A1.7", "exact-at-three-decimals fixture (1.2)",
    f"tcpi={o['tcpi']} band={o['status_color']}", f"tcpi={n['tcpi']} band={n['status_color']}",
    False, "executed both extracted packages")

# ---- non-divergence B: the displayed sentence is unchanged on the corpus
o, n = both("run_tcpi", CORPUS)
check(o["evidence_metric"] == n["evidence_metric"],
      "NON-DIVERGENCE B: the PARTICIPANT-VISIBLE A1.7 sentence is byte-identical on the corpus, "
      "because rounding was always what the display wanted", n["evidence_metric"][:60])
row("NON_DIVERGENCE", "A1.7", "Run-35 corpus, displayed sentence",
    o["evidence_metric"][:70], n["evidence_metric"][:70], False, "string comparison of both runs")
o, n = both("run_vac", CORPUS)
check(o["evidence_metric"] == n["evidence_metric"],
      "NON-DIVERGENCE C: the PARTICIPANT-VISIBLE A1.8 sentence is byte-identical on the corpus",
      n["evidence_metric"][:60])
row("NON_DIVERGENCE", "A1.8", "Run-35 corpus, displayed sentence",
    o["evidence_metric"][:70], n["evidence_metric"][:70], False, "string comparison of both runs")

# ---- non-divergence D: modules this closure did not touch
_untouched = 0
for _fn, _mid in (("run_budget_execution", "A1.9"), ("run_cost_variance", "A1.5")):
    if not hasattr(OLDEVM, _fn) or not hasattr(NEWEVM, _fn):
        continue
    o, n = both(_fn, CORPUS)
    if check(o == n, f"NON-DIVERGENCE D: {_mid} is byte-identical under both lines",
             str(o.get("evidence_metric", ""))[:50]):
        _untouched += 1
    row("NON_DIVERGENCE", _mid, "Run-35 governed corpus", str(o)[:70], str(n)[:70], False,
        "executed both extracted packages")
check(_untouched >= 1, "at least one untouched module was genuinely executed on both lines",
      f"{_untouched} untouched modules compared")

check(d1 and d2 and d3, "AT LEAST ONE GENUINE DIVERGENCE EXISTS, and it was executed rather "
                        "than inferred from a source diff")


# =================================================================================================
head("4. THE VOTING SET IS UNCHANGED BY THE CORRECTION")
# =================================================================================================
check(set(REG.CORE_VOTING_MODULES) == {"A1.7", "A1.8"},
      "voting remains exactly A1.7 and A1.8", str(sorted(REG.CORE_VOTING_MODULES)))
check(len(REG.CORE_VOTING_MODULES) == 2, "voting count = 2")


# =================================================================================================
with OUT.open("w", encoding="utf-8", newline="") as fh:
    csv.writer(fh, lineterminator="\n").writerows(ROWS)
print(f"\nwrote {OUT.relative_to(ROOT)}  ({len(ROWS) - 1} rows)")
for f in FAILURES:
    print(f"  FAILED: {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(0 if FAILED == 0 else 1)
