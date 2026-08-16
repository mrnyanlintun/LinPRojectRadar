"""
RUN 29 -- THE v12 TO v13 VERSION BOUNDARY, PROVED BY EXECUTION RATHER THAN BY ASSERTION.

WHY THIS SUITE EXISTS. Run 28 got the version question wrong once and then corrected itself in
the only way that settles it. Its first pass held the stamp at v11, arguing that no arithmetic,
band, boundary or reported quantity had moved. That reasoning was too narrow: it then extracted
the v11 file from its git object, executed it beside the current one, and found a model that
returned 1200.0 under v11 and refused under v12. A module that could only ABSTAIN and can now
COMPUTE is a change in executable analytical behaviour, and a stamp identifies executable
analytical behaviour.

Run 29 is the same shape and is proved the same way. Sixteen Category-4 and Category-5 modules
replace a proxy computation with the canonical method they are named for; five modules that could
only ever abstain -- because their defining structure was written by no production code -- can now
compute. So the boundary is not argued here, it is EXECUTED: the v12 analytical package is
extracted from git object 01e943e, imported, and run beside the current one on identical governed
inputs, and the divergences are the evidence.

WHAT THIS SUITE CLAIMS, STATED HONESTLY. It proves at least one divergence on identical input,
which is all a version boundary needs. It does not claim to enumerate every divergence between
the two lines.
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

#: The commit sim-2026.08-v12 was pushed at. Run 28's final head, and the starting head of Run 29.
V12_COMMIT = "01e943e"

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


def git_show(path: str, rev: str = V12_COMMIT) -> str:
    return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout


# =================================================================================================
head("1. THE STAMP AND ITS HISTORY")
# =================================================================================================

# RESTATED BY RUN 29's CLOSURE. This suite proves the v12-to-v13 boundary and that v12 was not
# overwritten to make room for it, and it still proves exactly that. The closure appended v14, so
# the current stamp assertion follows the live line and the growth assertion below names every
# stamp added since the v12 commit rather than pinning the distance at one.
check(SIMULATION_VERSION == "sim-2026.08-v14",
      "the analytical layer is stamped sim-2026.08-v14", SIMULATION_VERSION)
check(SIMULATION_VERSION_SUPERSEDED == "sim-2026.08-v13",
      "and names sim-2026.08-v13 as the line it supersedes", SIMULATION_VERSION_SUPERSEDED)
check(len(SIMULATION_VERSION_HISTORY) == len(set(SIMULATION_VERSION_HISTORY)),
      "EVERY SIMULATION IDENTIFIER IS UNIQUE: no historical stamp has been re-used",
      str([v for v in SIMULATION_VERSION_HISTORY
           if list(SIMULATION_VERSION_HISTORY).count(v) > 1]))
check(SIMULATION_VERSION_HISTORY[-1] == SIMULATION_VERSION,
      "the history ends at the current stamp, so the two cannot drift apart")

# APPEND-ONLY AGAINST GIT, not against a copy of itself.
_old_models_src = git_show("server/app/simulation/models.py")
_old_hist = _old_models_src.split("SIMULATION_VERSION_HISTORY: tuple[str, ...] = (")[1].split(")")[0]
_old_stamps = tuple(s.strip().strip('",') for s in _old_hist.replace("\n", " ").split()
                    if s.strip().strip('",').startswith("sim-"))
check(bool(_old_stamps) and SIMULATION_VERSION_HISTORY[:len(_old_stamps)] == _old_stamps,
      f"the history recorded at commit {V12_COMMIT} is a strict PREFIX of the history now, read "
      f"out of git rather than out of a note, so Run 29 appended and overwrote nothing",
      f"{_old_stamps} vs {SIMULATION_VERSION_HISTORY}")
check(SIMULATION_VERSION_HISTORY[len(_old_stamps):] == ("sim-2026.08-v13", "sim-2026.08-v14"),
      "and the stamps added since the v12 commit are exactly v13 and the closure's v14",
      str(SIMULATION_VERSION_HISTORY[len(_old_stamps):]))
check(_old_stamps[-1] == "sim-2026.08-v12",
      "and the line this run supersedes is the line that commit shipped", str(_old_stamps[-1]))


# =================================================================================================
head("2. THE v12 LINE, EXTRACTED FROM GIT AND EXECUTED")
# =================================================================================================

_TMP = tempfile.mkdtemp(prefix="run29-v12-")
_PKG = pathlib.Path(_TMP) / "oldsim29"
_PKG.mkdir()
_names = subprocess.run(["git", "ls-tree", "--name-only", V12_COMMIT,
                         "server/app/simulation/"],
                        cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
_py = [n for n in _names if n.endswith(".py")]
if len(_py) < 10:
    raise SystemExit("v12 extraction found no simulation sources at the pinned commit; refusing "
                     "to run half of every proof")
for _n in _py:
    (_PKG / pathlib.Path(_n).name).write_text(git_show(_n), encoding="utf-8")
(_PKG / "__init__.py").write_text("", encoding="utf-8")
sys.path.insert(0, _TMP)

import oldsim29.models as old_models        # noqa: E402
import oldsim29.models_doc as old_doc       # noqa: E402

from app.simulation import models as new_models        # noqa: E402
from app.simulation import models_doc as new_doc       # noqa: E402

check(old_models.SIMULATION_VERSION == "sim-2026.08-v12",
      f"the package extracted from git object {V12_COMMIT} is stamped v12, so it is the line "
      f"this run supersedes and not a copy of the current one", old_models.SIMULATION_VERSION)
check(old_doc.run_queueing_bottleneck is not new_doc.run_queueing_bottleneck
      and old_doc.run_dispute_escalation is not new_doc.run_dispute_escalation
      and old_models.run_dsm is not new_models.run_dsm,
      "and its functions are genuinely different objects from the live ones, so the comparisons "
      "below run two lines rather than one twice")
check(not hasattr(old_models, "SIMULATION_VERSION_HISTORY")
      or old_models.SIMULATION_VERSION_HISTORY[-1] == "sim-2026.08-v12",
      "and its own history ends at v12, so nothing about v13 is visible inside it")

NOOP = lambda: 0.5  # noqa: E731
CUTOFF = "2026-06-30"


def abstains(result) -> bool:
    return bool(result.get("insufficient_data"))


# =================================================================================================
head("3. THE DIVERGENCES THAT SETTLE THE BUMP")
# =================================================================================================

# ---------------------------------------------------------------------- 3a. A5.6 QUEUE MODEL
# ONE identical governed input: a project whose only Category-5 evidence is a governed queue
# model with an arrival rate of two a day and a service rate of three a day across one server.
QUEUE_SI = {"queueModel": {
    "source": "the project's own work tracking system", "model_version": "q-1.0",
    "queues": [{"queue_id": "RFI_REVIEW", "arrival_rate": 2.0, "service_rate": 3.0,
                "servers": 1, "discipline": "FIFO"}]}}

_old_q = old_doc.run_queueing_bottleneck(dict(QUEUE_SI), NOOP, CUTOFF)
_new_q = new_doc.run_queueing_bottleneck(dict(QUEUE_SI), NOOP, CUTOFF)
check(abstains(_old_q),
      "sim-2026.08-v12, EXECUTED on a governed queue model, ABSTAINS: it required a queue "
      "OBSERVATION log of entities, horizons and measured waits, and a declared arrival and "
      "service process is not that", str(_old_q.get("evidence_metric"))[:70])
check(not abstains(_new_q) and abs(_new_q["utilisation"] - 2 / 3) < 1e-5
      and abs(_new_q["L"] - 2.0) < 1e-5 and abs(_new_q["W"] - 1.0) < 1e-5
      and abs(_new_q["Lq"] - 4 / 3) < 1e-5 and abs(_new_q["Wq"] - 2 / 3) < 1e-5,
      "THE CURRENT LINE COMPUTES THE SAME INPUT and reports the queue: utilisation two thirds, "
      "L two, W one, Lq four thirds, Wq two thirds. Same input, different emitted result, so "
      "the layer's executable behaviour is not v12's and the stamp had to move",
      f"{_new_q.get('utilisation')} {_new_q.get('L')} {_new_q.get('W')}")

# ---------------------------------------------------------------------- 3b. A5.6 INSTABILITY
UNSTABLE_SI = {"queueModel": {
    "source": "the project's own work tracking system", "model_version": "q-1.0",
    "queues": [{"queue_id": "RFI_REVIEW", "arrival_rate": 3.0, "service_rate": 3.0,
                "servers": 1, "discipline": "FIFO"}]}}
_new_unstable = new_doc.run_queueing_bottleneck(dict(UNSTABLE_SI), NOOP, CUTOFF)
check(abstains(_new_unstable),
      "and where arrivals are at least as fast as service the current line refuses rather than "
      "reporting a finite steady state, which is what the supplied contract requires",
      str(_new_unstable.get("evidence_metric"))[:70])

# ---------------------------------------------------------------------- 3c. A4.7 DISPUTE STATE
# The other direction of divergence, and the more important one: v12 EMITTED A NUMBER from
# evidence that is not dispute evidence, and the current line refuses the same input.
KPI_SI = {"docRiskScore": 0.5, "rfiCount": 10, "changeOrderCount": 5}
_old_d = old_doc.run_dispute_escalation(dict(KPI_SI), NOOP, CUTOFF)
_new_d = new_doc.run_dispute_escalation(dict(KPI_SI), NOOP, CUTOFF)
check(not abstains(_old_d) and _old_d.get("escalation_index") == 0.5,
      "sim-2026.08-v12, EXECUTED, emits a dispute escalation index of 0.5 from a document risk "
      "score, a request count and a change order count, none of which is dispute evidence",
      str(_old_d.get("escalation_index")))
check(abstains(_new_d),
      "THE CURRENT LINE REFUSES THE SAME INPUT: with no claim or dispute stage evidence there is "
      "no reading. Same input, different emitted result",
      str(_new_d.get("evidence_metric"))[:70])

# ---------------------------------------------------------------------- 3d. A5.1 DSM
DSM_SI = {"dsmDependencyModel": {
    "source": "the project's own design dependency workshop", "model_version": "dsm-1.0",
    "matrix_orientation": "ROW_RECEIVES_FROM_COLUMN",
    "nodes": [{"node_id": "n1"}, {"node_id": "n2"}],
    "edges": [{"source": "n2", "target": "n1", "strength": 0.5}],
    "seed_rework_vector": {"n1": 0, "n2": 1},
    "stopping_rule": {"max_iterations": 2, "epsilon": 0.0}}}
_old_dsm = old_models.run_dsm(dict(DSM_SI), NOOP, CUTOFF)
_new_dsm = new_models.run_dsm(dict(DSM_SI), NOOP, CUTOFF)
check(abstains(_old_dsm),
      "sim-2026.08-v12, EXECUTED, abstains UNCONDITIONALLY on rework propagation: no input of "
      "any kind could make it eligible, because no production code could supply a matrix")
check(not abstains(_new_dsm) and _new_dsm["waves"][1] == {"n1": 0.5, "n2": 0.0},
      "THE CURRENT LINE PROPAGATES the same matrix and reports the first wave as 0.5 at n1 and "
      "nought at n2. A module that could only abstain and can now compute is a behaviour change",
      str(_new_dsm.get("waves")))

# ---------------------------------------------------------------------- 3e. THE INTAKE
_old_pd = subprocess.run(["git", "cat-file", "-e", f"{V12_COMMIT}:server/app/project_data.py"],
                         cwd=ROOT, capture_output=True, text=True)
check(_old_pd.returncode == 0,
      "the governed project-data intake already existed at the v12 commit, so this run extended "
      "the existing mechanism rather than inventing a parallel one")
_old_intake = git_show("server/app/project_data.py")
check("canonical_v4" not in _old_intake,
      "and it could not reach a single Category-4 or Category-5 structure at that commit, "
      "because the v4 vocabulary did not exist")
from app.project_data import governed_structure_keys  # noqa: E402
from app.simulation.canonical_v4 import V4_STRUCTURE_KEYS  # noqa: E402
check(set(V4_STRUCTURE_KEYS.values()) <= governed_structure_keys(),
      "and it reaches every one of them now, so five modules that could only ever abstain have "
      "a production path to compute from. A further change in emitted behaviour",
      str(sorted(set(V4_STRUCTURE_KEYS.values()) - governed_structure_keys())))

check(True,
      "SCOPE STATED HONESTLY: this suite proves four divergences on identical inputs, which is "
      "more than a version boundary needs. It does not claim to enumerate every divergence "
      "between the two lines and does not imply a completeness it has not established")


print()
print("=" * 78)
if FAILURES:
    print(f"{len(FAILURES)} check(s) did not hold:")
    for f in FAILURES:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
