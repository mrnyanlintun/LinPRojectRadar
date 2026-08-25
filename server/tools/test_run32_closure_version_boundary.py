"""
RUN 32 CLOSURE: THE v19 -> v20 SIMULATION VERSION BOUNDARY, PROVED BY EXECUTION.

THE RULE THIS FILE ENFORCES, and it is the one the programme has kept since Run 4: a change to
what the analytical layer emits must be DETECTABLE IN ALREADY-COLLECTED DATA. A stamp that moves
without a demonstrated behavioural difference is decoration, and a stamp that does not move while
behaviour changes silently invalidates every result stored under it.

SO NOTHING HERE IS PROVED BY READING SOURCE. The v19 line is extracted FROM ITS GIT OBJECT into a
throwaway package and EXECUTED beside the current one, and the divergences are observed by running
both. A source diff would prove only that the text changed, which is not the claim.

WHAT MUST BE SHOWN, and all three are required:

  * AT LEAST TWO DIVERGENCES -- inputs on which v19 and v20 genuinely disagree, so the stamp
    earns its move.
  * AT LEAST ONE NON-DIVERGENCE -- an input on which the two lines agree exactly, so the move is
    shown to be SCOPED. A run that changed everything would be a rewrite, not a remediation, and
    the non-divergence is what distinguishes them.
  * APPEND-ONLY HISTORY -- the history at the v19 commit is a strict PREFIX of the history now,
    read out of git, so this run appended and overwrote nothing.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

#: The exact commit Run 31 merged to main. The v19 line is read from this git object.
V19_COMMIT = "73297a63949004472889f0dac5510292d219ce29"

#: RUN 36 REPAIR. The exact commit Run 32 merged to main, where the stamp reads sim-2026.08-v20.
#: THE DEFECT THIS CLOSES. Section 3 below is a claim about what RUN 32 changed, and it was
#: taking its "new" line from the LIVE TREE. That made a historical, settled claim depend on
#: every future run: the moment a later run legitimately changed a module outside Category 10 --
#: which Run 36 did, withdrawing A1.1's unsupported band -- the non-divergence assertion went red
#: for a reason that has nothing to do with Run 32. A scope claim about a past run must be
#: EXECUTED ON THAT RUN'S OWN OBJECTS. Both lines are now extracted from git, so the assertion is
#: fixed forever and still fails if either pinned object is rewritten, which is the thing it is
#: really guarding.
V20_COMMIT = "93f08bc"

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


def git_show(path: str, rev: str = V19_COMMIT) -> str:
    return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout


from app.simulation.models import (  # noqa: E402
    SIMULATION_VERSION, SIMULATION_VERSION_HISTORY, SIMULATION_VERSION_SUPERSEDED,
)

# =================================================================================================
head("1. THE STAMP AND ITS HISTORY, APPEND-ONLY AND READ OUT OF GIT")
# =================================================================================================
# RESTATED BY RUN 33. Run 32's stamp expectations were true until the next authorised append.
# What this suite is FOR -- that v20 was really added, at the right position, after v19, and that
# the v19 package still reconstructs from its own git object and still behaves as v19 -- is
# unchanged and is asserted below on v20's HISTORICAL position rather than on the live stamp.
# RESTATED BY THE RUN-35 FINAL CLOSURE. The assertion below pinned the CURRENT stamp to the
# stamp its own run appended, which was true until the next authorised append. The closure
# appends v23, because A1.7 and A1.8 now compute their canonical value at the application's
# own precision and A1.7 bands from it. What is an INVARIANT -- and what is still asserted --
# is that this run's stamp is present, in order, at the position this run added it, and that
# the earlier history is a strict prefix read out of git. The precedent is Run 29's identical
# restatement in test_run28_version_boundary.py and Run 31's in run31_restate_version_suites.
check("sim-2026.08-v22" in SIMULATION_VERSION_HISTORY,
      "the stamp this boundary concerns, sim-2026.08-v22, is present in the history",
      SIMULATION_VERSION)
# RESTATED BY THE RUN-35 FINAL CLOSURE, same reason as the stamp pin above: the SUPERSEDED
# field names the line the CURRENT stamp replaced, so it moves whenever a later authorised
# run appends. What is an invariant is the ORDER of the two stamps this run's boundary is
# about, which is asserted from the history instead.
check(SIMULATION_VERSION_HISTORY.index("sim-2026.08-v22")
      == SIMULATION_VERSION_HISTORY.index("sim-2026.08-v21") + 1,
      "and v22 directly follows the v21 line it superseded",
      SIMULATION_VERSION_SUPERSEDED)
check("sim-2026.08-v20" in SIMULATION_VERSION_HISTORY,
      "the stamp Run 32 added is still present in the history")
check(SIMULATION_VERSION_HISTORY.index("sim-2026.08-v20")
      == SIMULATION_VERSION_HISTORY.index("sim-2026.08-v19") + 1,
      "and it directly follows sim-2026.08-v19, the line it superseded")
check(len(SIMULATION_VERSION_HISTORY) == len(set(SIMULATION_VERSION_HISTORY)),
      "EVERY SIMULATION IDENTIFIER IS UNIQUE: no historical stamp has been re-used")
check(SIMULATION_VERSION_HISTORY[-1] == SIMULATION_VERSION,
      "the history ends at the current stamp, so the two cannot drift apart")

_old_src = git_show("server/app/simulation/models.py")
_old_hist = _old_src.split("SIMULATION_VERSION_HISTORY: tuple[str, ...] = (")[1].split(")")[0]
_old_stamps = tuple(s.strip().strip('",') for s in _old_hist.replace("\n", " ").split()
                    if s.strip().strip('",').startswith("sim-"))
check(bool(_old_stamps) and SIMULATION_VERSION_HISTORY[:len(_old_stamps)] == _old_stamps,
      f"the history recorded at commit {V19_COMMIT} is a strict PREFIX of the history now, read "
      f"out of git rather than out of a note, so this run appended and overwrote nothing",
      f"{_old_stamps} vs {SIMULATION_VERSION_HISTORY}")
# RESTATED BY RUN 41, same discipline: the earlier stamps are still exactly the prefix they were,
# and v26 is Run 41's own single authorised append for the S1/S2 successor.
# RESTATED BY RUN 42: v27 is Run 42's own single authorised append for the evidence-provenance
# successor.
# RESTATED BY RUN 43: v28 is Run 43's own single authorised append for the retirement of 38
# modules from service.
# RESTATED BY RUN 44: v29 is Run 44's own single authorised append for the repair of the four
# participant-facing render defects Run 43J diagnosed.
check(SIMULATION_VERSION_HISTORY[len(_old_stamps):] == ("sim-2026.08-v20", "sim-2026.08-v21",
                                                       "sim-2026.08-v22", "sim-2026.08-v23",
                                                       "sim-2026.08-v24", "sim-2026.08-v25",
                                                       "sim-2026.08-v26",
                                                       "sim-2026.08-v27",
                                                       "sim-2026.08-v28",
                                                       "sim-2026.08-v29",
                                                       "sim-2026.08-v30",
                                                       "sim-2026.08-v31",
                                                       "sim-2026.08-v32",
                                                       "sim-2026.08-v33", "sim-2026.08-v34",
                                                       "sim-2026.08-v35",
                                                       # RUN 55: the single authorised append for
                                                       # the mint of Runs 54 and 55. The list is
                                                       # EXTENDED, never edited: every stamp
                                                       # before it keeps its position, which is
                                                       # what makes this an append check rather
                                                       # than a restatement.
                                                       "sim-2026.08-v36",
                                                       # RUN 56's own single authorised append.
                                                       # NOTHING IS REMOVED FROM THIS TUPLE.
                                                       "sim-2026.08-v37",
                                                       # RUN 57's own single authorised
                                                       # append. NOTHING IS REMOVED FROM
                                                       # THIS TUPLE.
                                                       "sim-2026.08-v38",
                                                       # RUN 59's own single authorised
                                                       # append. NOTHING IS REMOVED FROM
                                                       # THIS TUPLE.
                                                       "sim-2026.08-v39",
                                                       # RUN 62's own single authorised
                                                       # append, an EXTENSION and not an
                                                       # edit: v39 keeps its position.
                                                       # NOTHING IS REMOVED FROM THIS
                                                       # TUPLE.
                                                       "sim-2026.08-v40",
                                                       # RUN 63's own single authorised
                                                       # append, an EXTENSION and not an
                                                       # edit: v40 keeps its position.
                                                       # NOTHING IS REMOVED FROM THIS
                                                       # TUPLE.
                                                       "sim-2026.08-v41"),
      "and it grew by exactly the stamps Runs 32, 33, 34, 35, 36, 41, 42, 43, 44, 45, 47, 48, 49, 55, "
      "56, 57, 59, 62 and 63 "
      "were "
      "each authorised "
      "to add",
      str(SIMULATION_VERSION_HISTORY[len(_old_stamps):]))
check(_old_stamps[-1] == "sim-2026.08-v19",
      "and the line this run supersedes is the line that commit shipped", str(_old_stamps[-1]))


# =================================================================================================
head("2. THE v19 LINE, EXTRACTED FROM ITS GIT OBJECT AND EXECUTED")
# =================================================================================================
# THE EXTRACTED PACKAGE IS PLACED AT THE DEPTH THE v19 CODE EXPECTS. `qualification_boundary`
# and `qualification_contract` resolve the shipped registry CSV as `parents[3]/p0-baseline/...`,
# counted from `server/app/simulation/`. Dropping the sources into a flat temp directory would
# make that path resolve to the filesystem root and the import would die -- so the layout is
# reconstructed, and the CSV is taken FROM THE SAME COMMIT, so the v19 line reads the registry as
# it stood rather than as it stands now.
_TMP = tempfile.mkdtemp(prefix="run32-v19-")
_FAKE_ROOT = pathlib.Path(_TMP) / "repo"
_PKG = _FAKE_ROOT / "server" / "app" / "oldsim32"
_PKG.mkdir(parents=True)
(_FAKE_ROOT / "p0-baseline").mkdir(parents=True)
(_FAKE_ROOT / "p0-baseline" / "module_renumbering_map.csv").write_text(
    git_show("p0-baseline/module_renumbering_map.csv"), encoding="utf-8")
_names = subprocess.run(["git", "ls-tree", "--name-only", V19_COMMIT,
                         "server/app/simulation/"],
                        cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
_py = [n for n in _names if n.endswith(".py")]
if len(_py) < 10:
    raise SystemExit("v19 extraction found no simulation sources at the pinned commit; refusing "
                     "to run half of every proof")
for _n in _py:
    (_PKG / pathlib.Path(_n).name).write_text(git_show(_n), encoding="utf-8")
(_PKG / "__init__.py").write_text("", encoding="utf-8")
sys.path.insert(0, str(_PKG.parent))

import oldsim32.models as old_models            # noqa: E402

# THE v20 LINE, EXTRACTED FROM ITS OWN GIT OBJECT rather than read out of the working tree. See
# the V20_COMMIT note above for why.
_TMP20 = tempfile.mkdtemp(prefix="run32-v20-")
_FAKE_ROOT20 = pathlib.Path(_TMP20) / "repo"
_PKG20 = _FAKE_ROOT20 / "server" / "app" / "newsim32"
_PKG20.mkdir(parents=True)
(_FAKE_ROOT20 / "p0-baseline").mkdir(parents=True)
(_FAKE_ROOT20 / "p0-baseline" / "module_renumbering_map.csv").write_text(
    git_show("p0-baseline/module_renumbering_map.csv", V20_COMMIT), encoding="utf-8")
_names20 = subprocess.run(["git", "ls-tree", "--name-only", V20_COMMIT,
                           "server/app/simulation/"],
                          cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
_py20 = [n for n in _names20 if n.endswith(".py")]
if len(_py20) < 10:
    raise SystemExit("v20 extraction found no simulation sources at the pinned commit; refusing "
                     "to run half of every proof")
for _n in _py20:
    (_PKG20 / pathlib.Path(_n).name).write_text(git_show(_n, V20_COMMIT), encoding="utf-8")
(_PKG20 / "__init__.py").write_text("", encoding="utf-8")
sys.path.insert(0, str(_PKG20.parent))

import newsim32.models as new_models            # noqa: E402

check(new_models.SIMULATION_VERSION == "sim-2026.08-v20",
      f"the package extracted from git object {V20_COMMIT} is stamped v20, so it is the line "
      f"this run produced and not the working tree", new_models.SIMULATION_VERSION)

check(old_models.SIMULATION_VERSION == "sim-2026.08-v19",
      f"the package extracted from git object {V19_COMMIT} is stamped v19, so it is the line "
      f"this run supersedes and not a copy of the current one", old_models.SIMULATION_VERSION)

# ITS OWN ROUTING TABLE, read from the extracted line rather than asserted about it.
_old_b41 = old_models.VALIDATED["B4.1"][1]
check(_old_b41.__module__.startswith("oldsim32"),
      "and ITS OWN ROUTING TABLE sends Multi-Objective Optimization into the v19 decision "
      "module, which is the defect this run corrects", _old_b41.__module__)
_new_b41 = new_models.VALIDATED["B4.1"][1]
_new_inner = getattr(_new_b41, "__wrapped__", _new_b41)
check(_new_inner.__module__.endswith("models_cat10"),
      "while the current line routes it to the canonical Category-10 layer",
      _new_inner.__module__)


# =================================================================================================
head("3. THE DIVERGENCES, OBSERVED BY RUNNING BOTH LINES ON THE SAME INPUT")
# =================================================================================================
# A PROJECT CARRYING NO GOVERNED DECISION STRUCTURE, but carrying exactly the three index fields
# the v19 Category-10 implementations blended into a recommendation. This is the ordinary case:
# the controlled corpus holds no decision problem, so it is what a real project looked like.
# THE PACKAGE MUST PASS CATEGORY-9 QUALIFICATION, AND THIS IS THE CORRECTION OF A FALSE CLAIM
# THIS FILE ORIGINALLY MADE. The first version of this probe supplied no qualification record.
# BOTH lines then refused with CATEGORY9_ASSESSMENT_MISSING -- the v18 boundary is present in v19
# too -- so the "divergence" it reported was not one, and the run would have claimed credit for a
# difference that does not exist. That is the Run-31 lesson (a divergence example must be
# EXECUTED on both lines before it is written down) and it is why this probe declares a QUALIFIED
# assessment: only past the gate is the Category-10 implementation itself reached, which is where
# v19 and v20 actually differ.
QUAL = {"qualification_state": "QUALIFIED", "timeliness_status": "TIMELY",
        "verification_status": "verified", "source_authority": "system_of_record"}

SI_NO_STRUCTURE = {
    "cpi": 0.92, "spi": 0.88, "docRiskScore": 0.41,
    "bac": 1000000.0, "ac": 480000.0, "ev": 440000.0, "pv": 500000.0,
    "actualPctComplete": 44.0, "plannedPctComplete": 50.0,
    "percentComplete": 44.0, "durationMonths": 24, "monthsElapsed": 11,
    "evidenceQualification": QUAL,
}


def rand():
    return 0.5


def run_old(mid, si):
    try:
        return old_models.VALIDATED[mid][1](dict(si), rand, None)
    except Exception as exc:                                    # noqa: BLE001
        return {"__error__": f"{type(exc).__name__}: {exc}"}


def run_new(mid, si):
    try:
        return new_models.VALIDATED[mid][1](dict(si), rand, None)
    except Exception as exc:                                    # noqa: BLE001
        return {"__error__": f"{type(exc).__name__}: {exc}"}


def produced_a_reading(row: dict) -> bool:
    """Whether a row reports a figure, as opposed to abstaining or refusing."""
    if not isinstance(row, dict) or "__error__" in row:
        return False
    if row.get("insufficient_data") or row.get("abstention_reason_code"):
        return False
    return any(isinstance(v, (int, float)) and not isinstance(v, bool)
               for k, v in row.items() if k not in ("period",))


DIVERGENCES = 0

# ---- DIVERGENCE 1: B4.1 Multi-Objective Optimization -------------------------------------------
_o41 = run_old("B4.1", SI_NO_STRUCTURE)
_n41 = run_new("B4.1", SI_NO_STRUCTURE)
_d1 = produced_a_reading(_o41) and not produced_a_reading(_n41)
if _d1:
    DIVERGENCES += 1
check(_d1,
      "DIVERGENCE 1: on a project with no governed decision problem, v19 reported a "
      "multi-objective optimization figure and v20 reports none",
      f"v19={ {k: v for k, v in _o41.items() if k != 'period'} } v20_abstains="
      f"{not produced_a_reading(_n41)}")

# ---- DIVERGENCE 2: B4.2 Linear Programming -----------------------------------------------------
# CHOSEN BY EXECUTION, NOT BY GUESS. This slot originally claimed B4.7 diverged here. It does
# not: v19's B4.7 ALREADY abstained on a project with no payoff matrix, because Run 7 corrected
# exactly that module. Running all seven identities on this input is what established which ones
# genuinely differ -- B4.1, B4.2, B4.3, B4.4, B4.5 and B4.6 do; B4.7 does not -- and the claim
# was replaced with one of the six rather than kept because it read well.
_o42 = run_old("B4.2", SI_NO_STRUCTURE)
_n42 = run_new("B4.2", SI_NO_STRUCTURE)
_d2 = produced_a_reading(_o42) and not produced_a_reading(_n42)
if _d2:
    DIVERGENCES += 1
check(_d2,
      "DIVERGENCE 2: v19 reported a linear-programming score for a model with no decision "
      "variables and no constraint matrix; v20 reports no reading until a governed linear "
      "program is supplied",
      f"v19_keys={[k for k in _o42 if 'score' in k]} v20_reading={produced_a_reading(_n42)}")

# ---- THE HONEST NON-DIVERGENCE INSIDE THE SCOPE ------------------------------------------------
# B4.7 abstained on BOTH lines for this input. Recording it as a divergence would have been a
# false claim of credit, so it is recorded as what it is.
_o47 = run_old("B4.7", SI_NO_STRUCTURE)
_n47 = run_new("B4.7", SI_NO_STRUCTURE)
check(not produced_a_reading(_o47) and not produced_a_reading(_n47),
      "IN-SCOPE NON-DIVERGENCE: B4.7 produced no reading on EITHER line for a project with no "
      "payoff matrix, because v19 already refused there. Its v20 change is the rename and the "
      "fact that it now computes when a matrix IS supplied, not a new abstention",
      f"v19_reading={produced_a_reading(_o47)} v20_reading={produced_a_reading(_n47)}")

# ---- DIVERGENCE 3: the method name itself, which is section 3's rename -------------------------
_d3 = (old_models.VALIDATED["B4.7"][0] != new_models.VALIDATED["B4.7"][0]
       and new_models.VALIDATED["B4.7"][0] == "Minimax_Regret_Decision_Rule")
if _d3:
    DIVERGENCES += 1
check(_d3,
      "DIVERGENCE 3: the emitted method class for B4.7 changed from the v19 name to "
      "Minimax_Regret_Decision_Rule, so the rename is visible in a stored row",
      f"v19={old_models.VALIDATED['B4.7'][0]} v20={new_models.VALIDATED['B4.7'][0]}")

check(DIVERGENCES >= 2,
      f"AT LEAST TWO DIVERGENCES were observed by execution ({DIVERGENCES} found), so the stamp "
      f"move is earned rather than declared")


# =================================================================================================
head("4. THE NON-DIVERGENCE, WHICH IS WHAT MAKES THE CHANGE SCOPED")
# =================================================================================================
# A1.1 Cost Performance Index is outside Run 32's scope entirely. Both lines must produce the
# SAME row on the same input. If this diverged, the run would have changed something it was not
# authorised to change, and that is precisely what this check is for.
_oa = run_old("A1.1", SI_NO_STRUCTURE)
_na = run_new("A1.1", SI_NO_STRUCTURE)


def comparable(row: dict) -> dict:
    return {k: v for k, v in row.items()
            if k not in ("evidence_qualification", "qualification", "lineage")}


check(comparable(_oa) == comparable(_na),
      "NON-DIVERGENCE: A1.1 Cost Performance Index, outside this run's scope, produces an "
      "IDENTICAL row on both lines, so the v20 change is scoped to Category 10",
      f"v19={comparable(_oa)} v20={comparable(_na)}")

# A second one, on the other side of the instrument, for the same reason.
_ob = run_old("A1.2", SI_NO_STRUCTURE)
_nb = run_new("A1.2", SI_NO_STRUCTURE)
check(comparable(_ob) == comparable(_nb),
      "NON-DIVERGENCE: A1.2 is likewise identical on both lines",
      f"v19={comparable(_ob)} v20={comparable(_nb)}")


# =================================================================================================
head("5. THE v20 LINE REPORTS A RESULT WHERE A GOVERNED DECISION PROBLEM EXISTS")
# =================================================================================================
# ABSTENTION EVERYWHERE WOULD NOT BE A REMEDIATION. The canonical line must produce the method it
# is named for when the structure it needs is actually supplied.
MATRIX = {
    "context_id": "RUN32-BOUNDARY", "source": "run32 version boundary proof",
    "orientation": "benefit", "units": "score",
    "actions": [{"action_id": "A"}, {"action_id": "B"}, {"action_id": "C"}],
    "scenarios": [{"scenario_id": "S1"}, {"scenario_id": "S2"}],
    "cells": {"A": {"S1": 20, "S2": 12}, "B": {"S1": 16, "S2": 16},
              "C": {"S1": 12, "S2": 20}},
}
_si_with = dict(SI_NO_STRUCTURE, actionScenarioMatrix=MATRIX)
_row = run_new("B4.7", _si_with)
check(_row.get("minimax_regret_alternative") == "B",
      "with a governed action-by-scenario matrix supplied, v20 B4.7 identifies B as the "
      "minimax-regret alternative, so the canonical route computes rather than only abstaining",
      str(_row.get("minimax_regret_alternative") or _row.get("evidence_metric")))
# THE TWO SCIENTIFICALLY LOAD-BEARING PROPERTIES ARE ASSERTED SEPARATELY, and the Run-32 fault
# campaign is why. They used to be one conjunction, which meant a single check caught BOTH fault
# 18 (an algorithm exercising human approval authority) and fault 24 (a decision output re-entering
# as project-condition evidence). A conjunction that catches two different defects cannot tell you
# WHICH defect it caught, so neither fault could be proved independently non-vacuous. They are four
# checks now, and each fault turns its own one red.
check(_row.get("result_class") == "ANALYTICAL_RESULT",
      "the row it emits is stamped ANALYTICAL_RESULT and never HUMAN_DECISION",
      str(_row.get("result_class")))
check(_row.get("human_authorization_required") is True,
      "and it requires human authorisation, so no algorithm here exercises approval authority",
      str(_row.get("human_authorization_required")))
check(_row.get("creates_project_evidence") is False,
      "and it creates no project evidence, so a decision output cannot re-enter as a "
      "project-condition observation",
      str(_row.get("creates_project_evidence")))
check(_row.get("status_color") is None,
      "and it carries no status colour, so it cannot reach status fusion",
      str(_row.get("status_color")))

_old_with = run_old("B4.7", _si_with)
check(_old_with.get("minimax_regret_alternative") is None,
      "DIVERGENCE ON THE SAME SUPPLIED STRUCTURE: the v19 line does not read the matrix at all, "
      "so it names no minimax-regret alternative from it")


print()
if FAILURES:
    print("FAILURES:")
    for f in FAILURES:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(0 if FAILED == 0 else 1)
