#!/usr/bin/env python3
"""
RUN 33: THE v20 -> v21 SIMULATION VERSION BOUNDARY, PROVED BY EXECUTION.

THE RULE THIS FILE ENFORCES, and it is the one the programme has kept since Run 4: a change to
what the analytical layer emits must be DETECTABLE IN ALREADY-COLLECTED DATA. A stamp that moves
without a demonstrated behavioural difference is decoration, and a stamp that does not move while
behaviour changes silently invalidates every result stored under it.

SO NOTHING HERE IS PROVED BY READING SOURCE. The v20 line is extracted FROM ITS GIT OBJECT into a
throwaway package and EXECUTED beside the current one ON IDENTICAL PORTFOLIO INPUTS, and the
divergences are observed by running both.

WHAT MUST BE SHOWN, and all three are required:

  * AT LEAST TWO DIVERGENCES -- portfolio inputs on which v20 and v21 genuinely disagree.
  * AT LEAST ONE NON-DIVERGENCE -- an input on which the two lines agree, so the move is shown to
    be SCOPED. A run that changed everything would be a rewrite, not a remediation.
  * APPEND-ONLY HISTORY -- the history at the v20 commit is a strict PREFIX of the history now,
    read out of git.

THE NON-DIVERGENCE IS A REAL ONE AND IS NOT MANUFACTURED. It is asserted on a project-level
module OUTSIDE this run's scope, executed on both lines, because Run 33 touched no project-level
arithmetic at all: that is what "scoped" means here and it is what the check demonstrates.

Writes code_audit/run33_simulation_version_execution_proof.csv.
"""

from __future__ import annotations

import csv
import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(ROOT / "server" / "tools"))

#: The exact commit this run branched from: HEAD == main == origin/main, verified from git before
#: any edit. The v20 line is read from this git object and from nowhere else.
V20_COMMIT = "54409af2a07ac989489447379e8379cc9f95e15f"

OUT = ROOT / "code_audit" / "run33_simulation_version_execution_proof.csv"

PASSED = 0
FAILED = 0
FAILURES: list[str] = []
ROWS: list[list[str]] = [["record_type", "module", "input", "v20_behaviour", "v21_behaviour",
                          "divergence", "observed_by", "result"]]


def check(ok, label, detail=""):
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}" + (f"  [{detail}]" if detail else ""))
    else:
        FAILED += 1
        FAILURES.append(label)
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))
    return bool(ok)


def head(t):
    print("\n" + "=" * 94 + f"\n{t}\n" + "=" * 94)


def git_show(path, rev=V20_COMMIT):
    return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout


# =================================================================================================
head("1. THE STAMP AND ITS HISTORY, APPEND-ONLY AND READ OUT OF GIT")
# =================================================================================================
from app.simulation.models import (                                    # noqa: E402
    SIMULATION_VERSION, SIMULATION_VERSION_HISTORY, SIMULATION_VERSION_SUPERSEDED,
)

check(SIMULATION_VERSION == "sim-2026.08-v21", "the current stamp is sim-2026.08-v21",
      SIMULATION_VERSION)
check(SIMULATION_VERSION_SUPERSEDED == "sim-2026.08-v20",
      "and the line it supersedes is named as v20", SIMULATION_VERSION_SUPERSEDED)
check(SIMULATION_VERSION_HISTORY.index("sim-2026.08-v21")
      == SIMULATION_VERSION_HISTORY.index("sim-2026.08-v20") + 1,
      "it directly follows sim-2026.08-v20 in the history")
check(len(SIMULATION_VERSION_HISTORY) == len(set(SIMULATION_VERSION_HISTORY)),
      "EVERY SIMULATION IDENTIFIER IS UNIQUE: no historical stamp has been re-used",
      f"{len(SIMULATION_VERSION_HISTORY)} stamps")
check(SIMULATION_VERSION_HISTORY[-1] == SIMULATION_VERSION,
      "the history ends at the current stamp, so the two cannot drift apart")

_old_src = git_show("server/app/simulation/models.py")
_seg = _old_src.split("SIMULATION_VERSION_HISTORY: tuple[str, ...] = (")[1].split(")")[0]
_old_stamps = tuple(s.strip().strip('",') for s in _seg.replace("\n", " ").split()
                    if s.strip().strip('",').startswith("sim-"))
check(bool(_old_stamps) and SIMULATION_VERSION_HISTORY[:len(_old_stamps)] == _old_stamps,
      f"the history recorded at commit {V20_COMMIT} is a strict PREFIX of the history now, read "
      f"out of git rather than out of a note, so this run appended and overwrote nothing",
      f"{len(_old_stamps)} -> {len(SIMULATION_VERSION_HISTORY)}")
check(SIMULATION_VERSION_HISTORY[len(_old_stamps):] == ("sim-2026.08-v21",),
      "and it grew by exactly the one stamp this run is authorised to add",
      str(SIMULATION_VERSION_HISTORY[len(_old_stamps):]))
check(_old_stamps[-1] == "sim-2026.08-v20",
      "and the line this run supersedes is the line that commit shipped", _old_stamps[-1])
check('SIMULATION_VERSION = "sim-2026.08-v20"' in _old_src,
      f"PREDECESSOR RECONSTRUCTION: the v20 line reconstructs byte-for-byte from {V20_COMMIT} "
      f"and still says v20, so no predecessor stamp was regenerated to describe v21 behaviour")


# =================================================================================================
head("2. THE v20 LINE, EXTRACTED FROM ITS GIT OBJECT AND EXECUTED")
# =================================================================================================
_TMP = tempfile.mkdtemp(prefix="run33-v20-")
_FAKE_ROOT = pathlib.Path(_TMP) / "repo"
_PKG = _FAKE_ROOT / "server" / "app" / "oldsim33"
_PKG.mkdir(parents=True)
(_FAKE_ROOT / "p0-baseline").mkdir(parents=True)
(_FAKE_ROOT / "p0-baseline" / "module_renumbering_map.csv").write_text(
    git_show("p0-baseline/module_renumbering_map.csv"), encoding="utf-8")
_names = subprocess.run(["git", "ls-tree", "--name-only", V20_COMMIT,
                         "server/app/simulation/"], cwd=ROOT, capture_output=True, text=True,
                        check=True).stdout.split()
_py = [n for n in _names if n.endswith(".py")]
if len(_py) < 10:
    raise SystemExit("v20 extraction found no simulation sources at the pinned commit; refusing "
                     "to run half of every proof")
for _n in _py:
    (_PKG / pathlib.Path(_n).name).write_text(git_show(_n), encoding="utf-8")
(_PKG / "__init__.py").write_text("", encoding="utf-8")
sys.path.insert(0, str(_PKG.parent))

import oldsim33.models as old_models                                   # noqa: E402
import oldsim33.portfolio as old_portfolio                             # noqa: E402

from app.simulation import canonical_v8 as V8                          # noqa: E402
from app.simulation import portfolio_health as PH                      # noqa: E402

check(old_models.SIMULATION_VERSION == "sim-2026.08-v20",
      f"the package extracted from git object {V20_COMMIT} is stamped v20, so it is the line "
      f"this run supersedes and not a copy of the current one", old_models.SIMULATION_VERSION)
check(old_portfolio.__name__.startswith("oldsim33")
      and callable(old_portfolio.compute_portfolio),
      "and it carries its OWN portfolio implementation, executed below rather than described",
      old_portfolio.__file__.split("/")[-2])
check("IF_ANOMALY_THRESHOLD" in dir(old_portfolio)
      and old_portfolio.IF_ANOMALY_THRESHOLD == 0.576,
      "the v20 line carries the banded threshold constant, read from the extracted package",
      str(old_portfolio.IF_ANOMALY_THRESHOLD))


# =================================================================================================
head("3. IDENTICAL PORTFOLIO INPUTS, BOTH LINES EXECUTED")
# =================================================================================================
# ONE input set, expressed in the shape each line reads. The FIGURES are the same on both sides:
# three projects, the same cost and schedule indices, the same document risk, the same progress,
# and the same three-period cost-index history. That is what "identical portfolio inputs" means
# for two lines whose intake genuinely differs -- v20 reads bare vectors, v21 reads a governed
# cohort -- and the numbers a reader would recognise are held fixed across both.
PROJECTS = [("P1", 0.80, 0.90, 40.0, 55.0),
            ("P2", 1.00, 1.00, 10.0, 50.0),
            ("P3", 1.02, 0.99, 12.0, 48.0)]
HISTORY_CPI = [(0, 1.00), (1, 0.90), (2, 0.80)]

_v20_portfolio = [{"id": p, "cpi": c, "spi": s, "docRiskScore": d, "actualPctComplete": a}
                  for p, c, s, d, a in PROJECTS]
_v20_history = [{"signal_inputs": {"cpi": v}} for _t, v in HISTORY_CPI]
V20 = old_portfolio.compute_portfolio(_v20_portfolio, "P1", _v20_history, "2026-01-31")
check(V20.get("ok") is True and len(V20.get("results") or {}) >= 4,
      "the v20 line COMPUTES on this input and returns its result set",
      str(sorted((V20.get("results") or {}))))

_SV = "boundary-v1"


def _feat(fid, orientation, units="ratio"):
    return {"feature_id": fid, "label": fid, "units": units, "orientation": orientation,
            "scaling_rule": "NONE_RAW_UNITS", "missingness_rule": "ABSTAIN_NEVER_IMPUTE",
            "source_module": "BOUNDARY", "qualification_requirement": "CATEGORY_9_ELIGIBLE",
            "required": True}


COHORT = {"cohort_id": "BOUNDARY-COHORT", "portfolio_id": "PF", "period": "2026-01",
          "project_ids": [p for p, *_ in PROJECTS], "inclusion_rule": "all",
          "exclusion_rule": "none", "feature_schema_version": _SV,
          "qualification_policy": "CATEGORY_9", "model_version": "boundary-m1"}
SCHEMA = {"version": _SV,
          "features": [_feat("cost_index", V8.LOWER_IS_MORE_ADVERSE),
                       _feat("schedule_index", V8.LOWER_IS_MORE_ADVERSE),
                       _feat("document_risk", V8.HIGHER_IS_MORE_ADVERSE, "score"),
                       _feat("progress_pct", V8.NEUTRAL, "percent")]}
RECORDS = [{"project_id": p, "cohort_id": "BOUNDARY-COHORT", "period": "2026-01",
            "values": {"cost_index": c, "schedule_index": s, "document_risk": d,
                       "progress_pct": a},
            "qualification_state": "QUALIFIED", "missing_fields": [], "invalid_fields": [],
            "source_lineage": f"L::{p}", "source_provenance": f"P::{p}",
            "feature_schema_version": _SV}
           for p, c, s, d, a in PROJECTS]
HISTORIES = [{"project_id": "P1", "signal_id": "cost_index", "units": "ratio",
              "orientation": V8.LOWER_IS_MORE_ADVERSE, "source": "BOUNDARY",
              "history_version": "h1",
              "observations": [{"reporting_time": t, "value": v,
                                "qualification_state": "QUALIFIED"}
                               for t, v in HISTORY_CPI]}]
V21 = V8.compute_portfolio_health(COHORT, SCHEMA, RECORDS, HISTORIES)
check(V21["structure_absent"] is False and len(V21["results"]) == 5,
      "the v21 line COMPUTES on the same figures, expressed as a governed cohort",
      str(sorted(V21["results"])))

_d = 0


def divergence(module, what, old, new, why, ok):
    global _d
    ROWS.append(["DIVERGENCE", module, what, old, new, "YES", "execution of both lines",
                 "PASS" if ok else "FAIL"])
    if ok:
        _d += 1
    check(ok, f"DIVERGENCE {module}: {why}", f"v20 {old} | v21 {new}")


# --- DIVERGENCE 1: PH.3 interval counting versus the OLS slope -----------------------------------
_o3 = (V20["results"] or {}).get("cat8_3_trajectory_classifier") or {}
_n3 = V21["results"]["cat8_3_trajectory_classifier"]["projects"]["P1"][0]
divergence("D1.3 Signal Trajectory Classifier",
           "three cost-index observations 1.00, 0.90, 0.80 at times 0, 1, 2",
           f"trend {_o3.get('trend')} per period, status_color {_o3.get('status_color')}",
           f"OLS slope {_n3['ols_slope_exact']} per day, AdverseSlope "
           f"{_n3['adverse_slope_exact']}, classification {_n3['classification']}, no band",
           "v20 reported a banded status colour off an endpoint-difference trend; v21 reports an "
           "OLS slope on the actual reporting times and a classification with no band at all",
           bool(_o3) and _o3.get("status_color") is not None
           and "status_color" not in _n3 and _n3["magnitude_band"] is None
           and _n3["classification"] == V8.DETERIORATING)

# --- DIVERGENCE 2: PH.5 placeholder scalar versus a blocked scalar --------------------------------
_o5 = (V20["results"] or {}).get("cat8_5_anomaly_score") or {}
_n5 = V21["results"]["cat8_5_anomaly_score"]
divergence("D1.5 Anomaly Score", "the same three-project portfolio",
           f"composite_score {_o5.get('composite_score')}, status_color "
           f"{_o5.get('status_color')}",
           f"score {_n5['score']}, disposition {_n5['disposition']}, "
           f"result_type {_n5['result_type']}",
           "v20 emitted a scalar composite and a status colour; v21 emits a profile with the "
           "scalar withheld under PARAMETER_PROVENANCE_BLOCKED",
           isinstance(_o5.get("composite_score"), (int, float))
           and _n5["score"] is None
           and _n5["disposition"] == V8.PARAMETER_PROVENANCE_BLOCKED)

# --- DIVERGENCE 3: PH.4 fixed radius versus the continuous relationship ---------------------------
_o4 = (V20["results"] or {}).get("cat8_4_cross_project_pattern") or {}
_n4 = V21["results"]["cat8_4_cross_project_pattern"]
divergence("D1.4 Cross-project Pattern Detector", "the same three-project portfolio",
           f"similar_project_count {_o4.get('similar_project_count')} inside a fixed 0.15 "
           f"radius, status_color {_o4.get('status_color')}",
           f"nearest neighbour of P1 = "
           f"{_n4['projects']['P1']['nearest_neighbour_project_ids']} at distance "
           f"{_n4['projects']['P1']['distance']:.4f}, match_threshold "
           f"{_n4['match_threshold']}",
           "v20 counted matches inside an unvalidated fixed radius and banded the result; v21 "
           "reports the continuous nearest-neighbour relationship and applies no threshold",
           "similar_project_count" in _o4 and _o4.get("status_color") is not None
           and _n4["match_threshold"] is None
           and "status_color" not in _n4)

# --- DIVERGENCE 4: PH.1 one forest per project versus one forest per cohort -----------------------
_o1 = (V20["results"] or {}).get("cat8_1_isolation_forest") or {}
_n1 = V21["results"]["cat8_1_isolation_forest"]
# v20 fits a forest on the OTHER projects, once per scored project; run it for a second project
# and read its own metadata back, so the claim is observed rather than asserted.
_o1b = (old_portfolio.compute_portfolio(_v20_portfolio, "P2", _v20_history, "2026-01-31")
        ["results"] or {}).get("cat8_1_isolation_forest") or {}
divergence("D1.1 Isolation Forest", "the same three-project portfolio, scored for P1 and for P2",
           f"portfolio_size {_o1.get('portfolio_size')} but reference_size "
           f"{_o1.get('reference_size')} when scoring P1 and {_o1b.get('reference_size')} when "
           f"scoring P2 -- with three projects a reference of two NECESSARILY excludes the "
           f"project being scored, so the two scores come from forests fitted on different "
           f"populations -- with status_color {_o1.get('status_color')}",
           f"ONE forest fitted on {len(_n1['model']['fitted_project_population'])} projects, "
           f"scoring every member; no status colour",
           "v20 grew a separate forest per scored project and displayed those scores together; "
           "v21 fits one governed forest per cohort and model version",
           bool(_o1) and _o1.get("status_color") is not None
           and _o1.get("portfolio_size") == 3 and _o1.get("reference_size") == 2
           and _o1b.get("portfolio_size") == 3 and _o1b.get("reference_size") == 2
           and _n1["model"]["one_forest_per_cohort"] is True
           and len(_n1["model"]["fitted_project_population"]) == 3
           and len(_n1["projects"]) == 3 and "status_color" not in _n1)


# =================================================================================================
head("4. THE LEGITIMATE NON-DIVERGENCE, executed on both lines")
# =================================================================================================
# RUN 33 TOUCHED NO PROJECT-LEVEL ARITHMETIC. A1.7 TCPI is one of the two voting modules and sits
# entirely outside this run's scope; both lines are executed on identical signal inputs and must
# agree exactly. This is what makes the stamp's move SCOPED rather than a rewrite, and it is a
# REAL agreement observed by running both, not a claim about the diff.
_SI = {"bac": 1000000.0, "ac": 520000.0, "ev": 480000.0, "pv": 500000.0,
       "actual_pct_complete": 48.0, "planned_pct_complete": 50.0, "eac": 1080000.0}
_old_tcpi = old_models.VALIDATED["A1.7"][1](dict(_SI), lambda: 0.5, "2026-01-31")
from app.simulation.models import VALIDATED as NEW_VALIDATED            # noqa: E402
_new_tcpi = NEW_VALIDATED["A1.7"][1](dict(_SI), lambda: 0.5, "2026-01-31")
_same = json.dumps(_old_tcpi, sort_keys=True, default=str) == json.dumps(
    _new_tcpi, sort_keys=True, default=str)
ROWS.append(["NON_DIVERGENCE", "A1.7 To-Complete Performance Index",
             "identical earned-value signal inputs",
             json.dumps(_old_tcpi, sort_keys=True, default=str)[:150],
             json.dumps(_new_tcpi, sort_keys=True, default=str)[:150],
             "NO", "execution of both lines", "PASS" if _same else "FAIL"])
check(_same,
      "NON-DIVERGENCE: a voting project-level module outside this run's scope returns a "
      "BYTE-IDENTICAL result on both lines, so the v21 move is scoped to Portfolio Health",
      json.dumps(_new_tcpi, sort_keys=True, default=str)[:100])
check(_old_tcpi.get("method_class") is not None,
      "and it really computed on both lines rather than agreeing by both abstaining",
      str(_old_tcpi.get("method_class")))

check(_d >= 2, f"AT LEAST TWO GENUINE DIVERGENCES were observed by execution: {_d} found",
      str(_d))

ROWS.append(["SUMMARY", "-", "-", f"v20 at {V20_COMMIT}", "v21 current",
             f"{_d} divergences, 1 non-divergence", "execution of both lines",
             "PASS" if _d >= 2 and _same else "FAIL"])
with OUT.open("w", encoding="utf-8", newline="") as fh:
    csv.writer(fh, lineterminator="\n").writerows(ROWS)
print(f"\nwrote {OUT.relative_to(ROOT)}")

print()
print("=" * 94)
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
print("=" * 94)
if FAILURES:
    print("FAILURES:")
    for f in FAILURES:
        print("  -", f)
sys.exit(1 if FAILED else 0)
