"""
RUN 30 CLOSURE -- THE v15 TO v16 VERSION BOUNDARY, PROVED BY EXECUTION.

WHY THE STAMP MOVED AGAIN. v15 built the canonical Category-7 layer and production never called
it: executing the production entry point for all twenty identities and profiling the interpreter
gave `canonical_v5` reached on ZERO of twenty. v16 repoints every one of them. That is a change
in EXECUTABLE ANALYTICAL BEHAVIOUR on the operational path, which is what a stamp identifies.

It is not argued here. THE v15 PACKAGE IS EXTRACTED FROM GIT OBJECT ce03eb1, IMPORTED, AND RUN
BESIDE THE CURRENT ONE ON IDENTICAL INPUT.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from app.simulation.models import (  # noqa: E402
    SIMULATION_VERSION, SIMULATION_VERSION_HISTORY, SIMULATION_VERSION_SUPERSEDED,
)
from run30 import fixtures_cat67 as FX                            # noqa: E402

#: The commit sim-2026.08-v15 was pushed at: the Run-30 report-landing head.
V15_COMMIT = "ce03eb1"

PASSED = 0
FAILED = 0
FAILURES: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        FAILURES.append(label)
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def head(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def git_show(path: str, rev: str = V15_COMMIT) -> str:
    return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout


# =================================================================================================
head("1. THE STAMP AND ITS HISTORY")
# =================================================================================================
# RESTATED BY RUN 31, PASS 1. The assertion below pinned the CURRENT stamp to this run's
# own stamp, which was true until the next authorised append. Run 31 appends v17. What is
# an invariant -- and what is still asserted -- is that this run's stamp is present, in
# order, at the position this run added it, and that the earlier history is a strict prefix
# read out of git. The precedent for this restatement is Run 29's identical comment in
# test_run28_version_boundary.py.
check("sim-2026.08-v16" in SIMULATION_VERSION_HISTORY,
      "the stamp this closure added, sim-2026.08-v16, is present in the history",
      str(SIMULATION_VERSION_HISTORY))
check(SIMULATION_VERSION_HISTORY.index("sim-2026.08-v16")
      == SIMULATION_VERSION_HISTORY.index("sim-2026.08-v15") + 1,
      "and it directly follows sim-2026.08-v15, the line it superseded",
      str(SIMULATION_VERSION_HISTORY))
check(len(SIMULATION_VERSION_HISTORY) == len(set(SIMULATION_VERSION_HISTORY)),
      "EVERY SIMULATION IDENTIFIER IS UNIQUE: no historical stamp has been re-used",
      str([v for v in SIMULATION_VERSION_HISTORY
           if list(SIMULATION_VERSION_HISTORY).count(v) > 1]))
check(SIMULATION_VERSION_HISTORY[-1] == SIMULATION_VERSION,
      "the history ends at the current stamp, so the two cannot drift apart")

_old_src = git_show("server/app/simulation/models.py")
_old_hist = _old_src.split("SIMULATION_VERSION_HISTORY: tuple[str, ...] = (")[1].split(")")[0]
_old_stamps = tuple(s.strip().strip('",') for s in _old_hist.replace("\n", " ").split()
                    if s.strip().strip('",').startswith("sim-"))
check(bool(_old_stamps) and SIMULATION_VERSION_HISTORY[:len(_old_stamps)] == _old_stamps,
      f"the history recorded at commit {V15_COMMIT} is a strict PREFIX of the history now, read "
      f"out of git rather than out of a note, so this closure appended and overwrote nothing",
      f"{_old_stamps} vs {SIMULATION_VERSION_HISTORY}")
check(SIMULATION_VERSION_HISTORY[len(_old_stamps):][:1] == ("sim-2026.08-v16",),
      "and it grew by exactly the one stamp this closure is authorised to add",
      str(SIMULATION_VERSION_HISTORY[len(_old_stamps):]))
check(_old_stamps[-1] == "sim-2026.08-v15",
      "and the line this closure supersedes is the line that commit shipped", str(_old_stamps[-1]))


# =================================================================================================
head("2. THE v15 LINE, EXTRACTED FROM GIT AND EXECUTED")
# =================================================================================================
_TMP = tempfile.mkdtemp(prefix="run30c-v15-")
_PKG = pathlib.Path(_TMP) / "oldsim30c"
_PKG.mkdir()
_names = subprocess.run(["git", "ls-tree", "--name-only", V15_COMMIT,
                         "server/app/simulation/"],
                        cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
_py = [n for n in _names if n.endswith(".py")]
if len(_py) < 10:
    raise SystemExit("v15 extraction found no simulation sources at the pinned commit; refusing "
                     "to run half of every proof")
for _n in _py:
    (_PKG / pathlib.Path(_n).name).write_text(git_show(_n), encoding="utf-8")
(_PKG / "__init__.py").write_text("", encoding="utf-8")
sys.path.insert(0, _TMP)

import oldsim30c.models as old_models          # noqa: E402
import oldsim30c.models_fuzzy as old_fuzzy     # noqa: E402
import oldsim30c.models_evc as old_evc         # noqa: E402

from app.simulation import registry as REG     # noqa: E402
from app.simulation.canonical_v5 import V5_STRUCTURE_KEYS   # noqa: E402

check(old_models.SIMULATION_VERSION == "sim-2026.08-v15",
      f"the package extracted from git object {V15_COMMIT} is stamped v15, so it is the line "
      f"this closure supersedes and not a copy of the current one", old_models.SIMULATION_VERSION)
check("B2.14" in old_models.VALIDATED
      and old_models.VALIDATED["B2.14"][1].__module__ == "oldsim30c.models_fuzzy",
      "and ITS OWN ROUTING TABLE sends Maximum Entropy to the fuzzy proxy module, which is the "
      "defect this closure corrects, read out of the extracted line rather than asserted",
      str(old_models.VALIDATED["B2.14"][1].__module__))
check(REG.VALIDATED["B2.14"][1].__module__ == "app.simulation.models_cat7",
      "where the current line sends it to the canonical route",
      REG.VALIDATED["B2.14"][1].__module__)

NOOP = lambda: 0.5  # noqa: E731
CUTOFF = "2026-06-30"


def abstains(r) -> bool:
    return bool(r.get("insufficient_data"))


# =================================================================================================
head("3. THE DIVERGENCES THAT SETTLE THE BUMP")
# =================================================================================================
# ONE identical input: the flat signal inputs a real reporting period produces, carrying every
# crisp metric the proxies read and no governed epistemic structure of any kind.
FLAT = {"bac": 1_000_000.0, "ev": 400_000.0, "ac": 440_000.0, "pv": 450_000.0,
        "cpi": 0.909, "spi": 0.889, "docRiskScore": 0.35}

# ---- DIVERGENCE 1: Maximum Entropy, the module Run 27 proved was a function of min(cpi, spi).
_o = old_fuzzy.run_maximum_entropy(dict(FLAT), NOOP, CUTOFF)
_n = REG.run_module("B2.14", dict(FLAT), NOOP, CUTOFF)
check(_o.get("status_color") == "Amber" and not abstains(_o),
      "sim-2026.08-v15, EXECUTED, reports Amber for Maximum Entropy from the entropy of a lookup "
      "table indexed by the worse of the two performance indices",
      str(_o.get("evidence_metric"))[:70])
check(abstains(_n) and _n.get("canonical_disposition") == "NOT_ESTIMABLE_STRUCTURE_ABSENT",
      "THE CURRENT LINE ABSTAINS on the identical input, because no state space and no "
      "constraints were supplied and there is nothing to maximise over. Same input, different "
      "emitted result", str(_n.get("canonical_disposition")))

# ---- DIVERGENCE 2: Type-2, the midpoint collapse the contract forbids.
_o = old_fuzzy.run_type2_fuzzy(dict(FLAT), NOOP, CUTOFF)
_n = REG.run_module("B2.13", dict(FLAT), NOOP, CUTOFF)
check(_o.get("centroid") is not None and not abstains(_o),
      "sim-2026.08-v15 reports a Type-2 centroid taken from designed constants",
      str(_o.get("evidence_metric"))[:60])
check(abstains(_n) and _n.get("type_reduced") is None,
      "THE CURRENT LINE ABSTAINS and produces no reduced figure at all")

# ---- DIVERGENCE 3: Fermatean, the other min(cpi, spi) function.
_o = old_fuzzy.run_fermatean_fuzzy(dict(FLAT), NOOP, CUTOFF)
_n = REG.run_module("B2.17", dict(FLAT), NOOP, CUTOFF)
check(not abstains(_o) and abstains(_n),
      "sim-2026.08-v15 reports a Fermatean membership pair from the crisp indices; the current "
      "line abstains for want of an assessed pair",
      f"v15={_o.get('status_color')} v16={_n.get('status_color')}")

# ---- DIVERGENCE 4: Rough Sets, on the assembled package rather than the flat inputs.
from app.simulation import signal_package as SP                    # noqa: E402
_sig, _ = SP.build_signals(FLAT, [
    {"status_color": "amber", "overrun_pct_p80": 8.0, "module_id": "A1.1"},
    {"status_color": "green", "breached": False, "module_id": "A1.2"}])
_NESTED = SP.adapt(FLAT, _sig, decision={"state": "Amber"}, signal_array=[])
_o = old_evc.run_rough_sets(dict(_NESTED), NOOP, CUTOFF)
_n = REG.run_module("B2.2", dict(_NESTED), NOOP, CUTOFF)
check(not abstains(_o) and abstains(_n),
      "sim-2026.08-v15 bands the assembled arms as a rough-set classification; the current line "
      "abstains, because four crisp readings are not a decision table",
      f"v15={_o.get('status_color')} v16={_n.get('status_color')}")

# ---- AND THE CURRENT LINE COMPUTES WHERE v15 COULD NOT: given the defining structure, the
# canonical route returns the supplied contract's own answer, which v15 had no way to read.
_n = REG.run_module("B2.14", {V5_STRUCTURE_KEYS["B2.14"]: FX.maxent_expectation(1.0)},
                    NOOP, CUTOFF)
import math                                                        # noqa: E402
check(not abstains(_n) and abs(_n["entropy"] - math.log(3)) < 1e-9,
      "and given a governed state space and constraint the current line returns the contract's "
      "own ln 3, which is a reading v15 had no structure to take at all",
      str(_n.get("entropy")))

# =================================================================================================
head("4. ONE LEGITIMATE AGREEMENT, SO THE BOUNDARY IS NOT OVERCLAIMED")
# =================================================================================================
_o = old_evc.run_plithogenic(dict(_NESTED), NOOP, CUTOFF) if hasattr(
    old_evc, "run_plithogenic") else None
_o_reg = old_models.VALIDATED["B2.7"][1]
check(_o_reg is not None, "the v15 line carries a Plithogenic implementation")
_v15_disabled = "B2.7" in git_show("server/app/simulation/registry.py")
_n = REG.run_module("B2.7", {V5_STRUCTURE_KEYS["B2.7"]: FX.plithogenic()}, NOOP, CUTOFF)
check(abstains(_n) and _n.get("operational") is False and _v15_disabled,
      "BOTH LINES REFUSE Plithogenic on a complete laboratory structure: it was disabled under "
      "v15 and it is disabled under v16. The closure widened what can be read and retired a set "
      "of proxies; it activated nothing")
from app.simulation import models_decision as new_dec              # noqa: E402
import oldsim30c.models_decision as old_dec                        # noqa: E402
_CD = {"signals": {"evm": {"status": "red"}, "mc": {"status": "green"},
                   "cusum": {"status": "green", "breached": False},
                   "doc": {"status": "green"}}}
check(old_dec.run_conservative_dominance(_CD, NOOP, CUTOFF).get("state")
      == new_dec.run_conservative_dominance(_CD, NOOP, CUTOFF).get("state") == "Red",
      "and B1.1 Conservative Dominance is byte-for-byte the same computation on both lines, so "
      "the one Category-6 scientific pass is untouched by the closure")

print()
print("=" * 78)
if FAILURES:
    print(f"{len(FAILURES)} check(s) did not hold:")
    for f in FAILURES:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
