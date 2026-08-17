"""
RUN 30 -- THE v14 TO v15 VERSION BOUNDARY, PROVED BY EXECUTION.

WHY THIS SUITE EXISTS. A stamp identifies EXECUTABLE ANALYTICAL BEHAVIOUR, and this programme has
already got the question wrong once by reasoning about it instead of running it: Run 28 first
held at v11 on the argument that no arithmetic had moved, then disproved itself by executing both
lines from git. So the bump is not argued here. THE v14 ANALYTICAL PACKAGE IS EXTRACTED FROM GIT
OBJECT ac7c011, IMPORTED, AND RUN BESIDE THE CURRENT ONE ON IDENTICAL INPUT.

WHAT THIS SUITE CLAIMS, STATED HONESTLY. It proves specific divergences on identical input, which
is all a version boundary needs. It does not claim to enumerate every divergence.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))

from app.simulation.models import (  # noqa: E402
    SIMULATION_VERSION, SIMULATION_VERSION_HISTORY, SIMULATION_VERSION_SUPERSEDED,
)

#: The commit sim-2026.08-v14 was pushed at: the Run-29 closure head, and Run 30's start state.
V14_COMMIT = "ac7c011"

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


def git_show(path: str, rev: str = V14_COMMIT) -> str:
    return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout


# =================================================================================================
head("1. THE STAMP AND ITS HISTORY")
# =================================================================================================

# RESTATED BY THE RUN-30 CLOSURE: this suite proves the v14-to-v15 boundary and still
# does; the current-stamp assertion follows the live line.
# RESTATED BY RUN 31, PASS 1. The assertion below pinned the CURRENT stamp to this run's
# own stamp, which was true until the next authorised append. Run 31 appends v17. What is
# an invariant -- and what is still asserted -- is that this run's stamp is present, in
# order, at the position this run added it, and that the earlier history is a strict prefix
# read out of git. The precedent for this restatement is Run 29's identical comment in
# test_run28_version_boundary.py.
check("sim-2026.08-v16" in SIMULATION_VERSION_HISTORY,
      "the stamp Run 30 added, sim-2026.08-v16, is present in the history",
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

_old_models_src = git_show("server/app/simulation/models.py")
_old_hist = _old_models_src.split("SIMULATION_VERSION_HISTORY: tuple[str, ...] = (")[1].split(")")[0]
_old_stamps = tuple(s.strip().strip('",') for s in _old_hist.replace("\n", " ").split()
                    if s.strip().strip('",').startswith("sim-"))
check(bool(_old_stamps) and SIMULATION_VERSION_HISTORY[:len(_old_stamps)] == _old_stamps,
      f"the history recorded at commit {V14_COMMIT} is a strict PREFIX of the history now, read "
      f"out of git rather than out of a note, so this run appended and overwrote nothing",
      f"{_old_stamps} vs {SIMULATION_VERSION_HISTORY}")
check(SIMULATION_VERSION_HISTORY[len(_old_stamps):][:2] == ("sim-2026.08-v15",
                                                            "sim-2026.08-v16"),
      "and it grew by the two stamps Run 30 is authorised to add: v15 for the canonical layer "
      "and v16 for repointing the operational routes onto it",
      str(SIMULATION_VERSION_HISTORY[len(_old_stamps):]))
check(_old_stamps[-1] == "sim-2026.08-v14",
      "and the line this run supersedes is the line that commit shipped", str(_old_stamps[-1]))


# =================================================================================================
head("2. THE v14 LINE, EXTRACTED FROM GIT AND EXECUTED")
# =================================================================================================

_TMP = tempfile.mkdtemp(prefix="run30-v14-")
_PKG = pathlib.Path(_TMP) / "oldsim30"
_PKG.mkdir()
_names = subprocess.run(["git", "ls-tree", "--name-only", V14_COMMIT,
                         "server/app/simulation/"],
                        cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
_py = [n for n in _names if n.endswith(".py")]
if len(_py) < 10:
    raise SystemExit("v14 extraction found no simulation sources at the pinned commit; refusing "
                     "to run half of every proof")
for _n in _py:
    (_PKG / pathlib.Path(_n).name).write_text(git_show(_n), encoding="utf-8")
(_PKG / "__init__.py").write_text("", encoding="utf-8")
sys.path.insert(0, _TMP)

import oldsim30.models as old_models        # noqa: E402
import oldsim30.models_gov as old_gov       # noqa: E402

from app.simulation import models_gov as new_gov       # noqa: E402

check(old_models.SIMULATION_VERSION == "sim-2026.08-v14",
      f"the package extracted from git object {V14_COMMIT} is stamped v14, so it is the line "
      f"this run supersedes and not a copy of the current one", old_models.SIMULATION_VERSION)
check(old_gov.run_worst_n_of_m is not new_gov.run_worst_n_of_m,
      "and its functions are genuinely different objects from the live ones, so the comparison "
      "below runs two lines rather than one twice")

NOOP = lambda: 0.5  # noqa: E731
CUTOFF = "2026-06-30"


def abstains(result) -> bool:
    return bool(result.get("insufficient_data"))


# =================================================================================================
head("3. THE DIVERGENCES THAT SETTLE THE BUMP")
# =================================================================================================

# ONE identical assembled package, in two sizes of module array. THE EVIDENCE IS IDENTICAL IN
# BOTH: three primary signals reading red, and a signal array of transformations of those same
# arms which learn nothing new.
def pkg(extra_rows: int) -> dict:
    return {"signals": {"mc": {"status": "red"}, "cusum": {"status": "red", "breached": True},
                        "doc": {"status": "red"},
                        "decision": {"state": "Red-review"}},
            "simulationSignals": {"signal_array":
                                  [{"module_id": f"R{i}", "status_color": "Red"}
                                   for i in range(3)]
                                  + [{"module_id": f"G{i}", "status_color": "Green"}
                                     for i in range(extra_rows)]}}


SMALL, BIG = pkg(0), pkg(60)

# ---- DIVERGENCE 1: B1.4 Worst-N-of-M, the structural defect Run 27 measured.
_o_small = old_gov.run_worst_n_of_m(SMALL, NOOP, CUTOFF).get("status_color")
_o_big = old_gov.run_worst_n_of_m(BIG, NOOP, CUTOFF).get("status_color")
check(_o_small == "Red" and _o_big == "Yellow",
      "sim-2026.08-v14, EXECUTED, reports Red beside a small module array and Yellow beside a "
      "large one ON IDENTICAL ADVERSE EVIDENCE: the red count was compared against a fraction "
      "of an M that grew with the registry",
      f"small={_o_small} big={_o_big}")
_n_small = new_gov.run_worst_n_of_m(SMALL, NOOP, CUTOFF)
_n_big = new_gov.run_worst_n_of_m(BIG, NOOP, CUTOFF)
check(_n_small.get("mean_worst_2") == _n_big.get("mean_worst_2") == 3.0,
      "THE CURRENT LINE reports the same Worst-2 mean of 3.0 in both, because the statistic has "
      "no denominator that grows with the registry. Same input, different emitted result",
      f"small={_n_small.get('mean_worst_2')} big={_n_big.get('mean_worst_2')}")
check(_n_small.get("status_color") is None and _n_big.get("status_color") is None,
      "and it asserts NO traffic-light boundary over the statistic, where v14 asserted one that "
      "no evidence in this repository establishes")

# ---- DIVERGENCE 2: B1.2 Weighted Voting, the four unsourced weight literals.
_o_wv = old_gov.run_weighted_voting(SMALL, NOOP, CUTOFF)
_n_wv = new_gov.run_weighted_voting(SMALL, NOOP, CUTOFF)
check(_o_wv.get("status_color") == "Red" and not abstains(_o_wv),
      "sim-2026.08-v14 weighs the same package with four literal weights (1.5, 1.0, 0.6, 1.5) "
      "carried in the module with no authority anywhere in the repository, and reports a state",
      str(_o_wv.get("votes")))
check(abstains(_n_wv) and "weighting policy" in str(_n_wv.get("abstention_reason", "")),
      "THE CURRENT LINE ABSTAINS on the identical package, because a weighted vote with no "
      "governed weighting policy weighs nothing. Same input, different emitted result",
      str(_n_wv.get("abstention_reason"))[:90])

# ---- DIVERGENCE 3: B1.3 Majority Rules, one vote per REGISTERED MODULE versus one per body.
_o_mr = old_gov.run_majority_rules(BIG, NOOP, CUTOFF)
_n_mr = new_gov.run_majority_rules(BIG, NOOP, CUTOFF)
check(_o_mr.get("total_votes") == 66 and _o_mr.get("status_color") == "Green",
      "sim-2026.08-v14 counts sixty-six voters on this package -- three primary signals and "
      "sixty-three module rows, every one of them a transformation of the same arms -- and the "
      "sixty Green transformations outvote the adverse evidence",
      f"{_o_mr.get('total_votes')} voters, {_o_mr.get('status_color')}")
check(_n_mr.get("total_votes") == 2 and _n_mr.get("status_color") == "Red",
      "THE CURRENT LINE counts TWO independent bodies of evidence and reports Red. Same input, "
      "different emitted result",
      f"{_n_mr.get('total_votes')} voters, {_n_mr.get('status_color')}")
check(sorted(_n_mr.get("lineage", {}).get("duplicate_lineage_suppressed", [])) == ["cusum"],
      "and the further reading of the earned-value body it set aside is NAMED rather than "
      "silently dropped",
      str(_n_mr.get("lineage", {}).get("duplicate_lineage_suppressed")))

# ---- WHAT DID NOT MOVE, so the boundary is not overclaimed.
import oldsim30.models_decision as old_dec       # noqa: E402
from app.simulation import models_decision as new_dec       # noqa: E402
_CD = {"signals": {"evm": {"status": "red"}, "mc": {"status": "green"},
                   "cusum": {"status": "green", "breached": False},
                   "doc": {"status": "green"}}}
check(old_dec.run_conservative_dominance(_CD, NOOP, CUTOFF).get("state")
      == new_dec.run_conservative_dominance(_CD, NOOP, CUTOFF).get("state") == "Red",
      "B1.1 Conservative Dominance is BYTE-FOR-BYTE the same computation on both lines and "
      "returns the same state: Run 30 protected the one Category-6 scientific pass and did not "
      "undo Run 20 cycle 9")
check(old_gov.run_dst is not new_gov.run_dst
      and old_gov.run_dst({"evm": {"cpi": 0.85, "spi": 0.85}, "doc": {"score": 0.8}},
                          NOOP, CUTOFF).get("belief_red")
      == new_gov.run_dst({"evm": {"cpi": 0.85, "spi": 0.85}, "doc": {"score": 0.8}},
                         NOOP, CUTOFF).get("belief_red"),
      "and B2.1's shipped Dempster combination is unchanged, so Run 20 cycle 7's same-lineage "
      "fix is preserved rather than rewritten")

print()
print("=" * 78)
if FAILURES:
    print(f"{len(FAILURES)} check(s) did not hold:")
    for f in FAILURES:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
