#!/usr/bin/env python3
"""
RUN 34: THE v21 -> v22 SIMULATION VERSION BOUNDARY, PROVED BY EXECUTION.

A change to what the analytical layer emits must be DETECTABLE IN ALREADY-COLLECTED DATA. The v21
line is extracted FROM ITS GIT OBJECT into a throwaway package and EXECUTED beside the current one
on identical portfolio inputs. A source diff would prove only that the text changed.

Required: at least two genuine divergences, at least one legitimate non-divergence, and an
append-only history read out of git.

Writes code_audit/run34_simulation_version_execution_proof.csv.
"""

from __future__ import annotations

import csv
import json
import pathlib
import subprocess
import sys
import tempfile

_HERE = pathlib.Path(__file__).resolve().parent
ROOT = _HERE.parents[1]
sys.path.insert(0, str(ROOT / "server"))

#: The exact commit Run 33's closure merged to main. The v21 line is read from this git object.
V21_COMMIT = "f5c52d3fd97498e031bad7e93ceb5cdc7ee65151"
OUT = ROOT / "code_audit" / "run34_simulation_version_execution_proof.csv"

PASSED = 0
FAILED = 0
FAILURES: list[str] = []
ROWS = [["record_type", "module", "input", "v21_behaviour", "v22_behaviour", "divergence",
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


def git_show(path, rev=V21_COMMIT):
    return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout


# =================================================================================================
head("1. THE STAMP AND ITS HISTORY, APPEND-ONLY AND READ OUT OF GIT")
# =================================================================================================
from app.simulation.models import (                                    # noqa: E402
    SIMULATION_VERSION, SIMULATION_VERSION_HISTORY, SIMULATION_VERSION_SUPERSEDED,
)

check(SIMULATION_VERSION == "sim-2026.08-v22", "the current stamp is sim-2026.08-v22",
      SIMULATION_VERSION)
check(SIMULATION_VERSION_SUPERSEDED == "sim-2026.08-v21",
      "and the line it supersedes is named as v21", SIMULATION_VERSION_SUPERSEDED)
check(SIMULATION_VERSION_HISTORY.index("sim-2026.08-v22")
      == SIMULATION_VERSION_HISTORY.index("sim-2026.08-v21") + 1,
      "it directly follows sim-2026.08-v21 in the history")
check(len(SIMULATION_VERSION_HISTORY) == len(set(SIMULATION_VERSION_HISTORY)),
      "EVERY SIMULATION IDENTIFIER IS UNIQUE", f"{len(SIMULATION_VERSION_HISTORY)} stamps")
_old_src = git_show("server/app/simulation/models.py")
_seg = _old_src.split("SIMULATION_VERSION_HISTORY: tuple[str, ...] = (")[1].split(")")[0]
_old = tuple(s.strip().strip('",') for s in _seg.replace("\n", " ").split()
             if s.strip().strip('",').startswith("sim-"))
check(SIMULATION_VERSION_HISTORY[:len(_old)] == _old,
      f"the history at {V21_COMMIT[:7]} is a strict PREFIX of the history now, read out of git",
      f"{len(_old)} -> {len(SIMULATION_VERSION_HISTORY)}")
check(SIMULATION_VERSION_HISTORY[len(_old):] == ("sim-2026.08-v22",),
      "and it grew by exactly the one stamp this run is authorised to add")
check('SIMULATION_VERSION = "sim-2026.08-v21"' in _old_src,
      "PREDECESSOR RECONSTRUCTION: the v21 line reconstructs from its own git object and still "
      "says v21, so no predecessor stamp was regenerated to describe v22 behaviour")


# =================================================================================================
head("2. THE v21 LINE, EXTRACTED FROM ITS GIT OBJECT AND EXECUTED")
# =================================================================================================
_TMP = tempfile.mkdtemp(prefix="run34-v21-")
_FAKE = pathlib.Path(_TMP) / "repo"
_PKG = _FAKE / "server" / "app" / "oldsim34"
_PKG.mkdir(parents=True)
(_FAKE / "p0-baseline").mkdir(parents=True)
(_FAKE / "p0-baseline" / "module_renumbering_map.csv").write_text(
    git_show("p0-baseline/module_renumbering_map.csv"), encoding="utf-8")
_names = subprocess.run(["git", "ls-tree", "--name-only", V21_COMMIT,
                         "server/app/simulation/"], cwd=ROOT, capture_output=True, text=True,
                        check=True).stdout.split()
_py = [n for n in _names if n.endswith(".py")]
if len(_py) < 10:
    raise SystemExit("v21 extraction found no simulation sources; refusing to run half a proof")
for _n in _py:
    (_PKG / pathlib.Path(_n).name).write_text(git_show(_n), encoding="utf-8")
(_PKG / "__init__.py").write_text("", encoding="utf-8")
sys.path.insert(0, str(_PKG.parent))

import oldsim34.models as old_models                                   # noqa: E402
import oldsim34.canonical_v8 as OLD                                    # noqa: E402

from app.simulation import canonical_v8 as NEW                         # noqa: E402

check(old_models.SIMULATION_VERSION == "sim-2026.08-v21",
      f"the package extracted from {V21_COMMIT[:7]} is stamped v21", old_models.SIMULATION_VERSION)
check(OLD.__name__.startswith("oldsim34") and NEW is not OLD,
      "and it carries its OWN Portfolio Health layer, executed below rather than described")


# =================================================================================================
head("3. IDENTICAL PORTFOLIO INPUTS, BOTH LINES EXECUTED")
# =================================================================================================
SV = "boundary34-v1"
COHORT = {"cohort_id": "B34", "portfolio_id": "PF", "period": "2026-01",
          "project_ids": ["A", "B", "C", "D"], "inclusion_rule": "all", "exclusion_rule": "none",
          "feature_schema_version": SV, "qualification_policy": "CATEGORY_9",
          "model_version": "b34-m1"}


def feat(fid, orientation):
    return {"feature_id": fid, "label": fid, "units": "index", "orientation": orientation,
            "scaling_rule": "NONE_RAW_UNITS", "missingness_rule": "ABSTAIN_NEVER_IMPUTE",
            "source_module": "BOUNDARY", "qualification_requirement": "CATEGORY_9_ELIGIBLE",
            "required": True}


SCHEMA = {"version": SV, "features": [feat("f_a", "HIGHER_IS_MORE_ADVERSE"),
                                      feat("f_b", "LOWER_IS_MORE_ADVERSE")]}
VALUES = {"A": (1.0, 1.00), "B": (2.0, 0.95), "C": (3.0, 0.90), "D": (10.0, 0.60)}
RECORDS = [{"project_id": p, "cohort_id": "B34", "period": "2026-01",
            "values": {"f_a": v[0], "f_b": v[1]}, "qualification_state": "QUALIFIED",
            "missing_fields": [], "invalid_fields": [], "source_lineage": f"L::{p}",
            "source_provenance": f"P::{p}", "feature_schema_version": SV}
           for p, v in sorted(VALUES.items())]
HIST = [{"project_id": "A", "signal_id": "cost_index", "units": "ratio",
         "orientation": "LOWER_IS_MORE_ADVERSE", "source": "B34", "history_version": "h1",
         "observations": [{"reporting_time": t, "value": v, "qualification_state": "QUALIFIED"}
                          for t, v in ((0, 1.0), (1, 1.0), (2, 1.0))]}]

V21 = OLD.compute_portfolio_health(COHORT, SCHEMA, RECORDS, HIST)
V22 = NEW.compute_portfolio_health(COHORT, SCHEMA, RECORDS, HIST)
check(V21["structure_absent"] is False and V22["structure_absent"] is False,
      "both lines compute on the identical governed cohort")

_d = 0


def divergence(module, what, old, new, why, ok):
    global _d
    ROWS.append(["DIVERGENCE", module, what, old, new, "YES", "execution of both lines",
                 "PASS" if ok else "FAIL"])
    if ok:
        _d += 1
    check(ok, f"DIVERGENCE {module}: {why}", f"v21 {old} | v22 {new}")


# --- DIVERGENCE 1: PH.2 emitted an equal-weighted composite; v22 withholds it -------------------
_o2 = V21["results"]["cat8_2_portfolio_outlier"]
_n2 = V22["results"]["cat8_2_portfolio_outlier"]
divergence("D1.2 Portfolio Outlier Detection", "the same four-project cohort, two features",
           f"composite {_o2['projects']['D']['portfolio_outlier_percentile']} under equal "
           f"weighting, provenance {_o2.get('composite_weighting_provenance')}",
           f"composite {_n2['projects']['D']['portfolio_outlier_percentile']}, disposition "
           f"{_n2['disposition']}, result_type {_n2['result_type']}",
           "v21 emitted an equal-weighted composite labelled OWNER_POLICY; v22 withholds it "
           "absent governed weights and returns the per-feature percentile profile",
           isinstance(_o2["projects"]["D"]["portfolio_outlier_percentile"], float)
           and _n2["projects"]["D"]["portfolio_outlier_percentile"] is None
           and _n2["disposition"] == "PARAMETER_PROVENANCE_BLOCKED")
# and the underlying midranks are UNCHANGED, so the withdrawal removed a weighting, not a number.
check(_o2["projects"]["D"]["feature_percentiles_exact"]
      == _n2["projects"]["D"]["feature_percentiles_exact"],
      "and the per-feature midranks are IDENTICAL across the two lines, so what v22 withdrew is "
      "the weighting and not the measurement",
      str(_n2["projects"]["D"]["feature_percentiles_exact"]))

# --- DIVERGENCE 2: PH.1 on a two-project cohort -------------------------------------------------
_two_c = dict(COHORT, project_ids=["A", "B"])
_two_r = [r for r in RECORDS if r["project_id"] in ("A", "B")]
_o1 = OLD.compute_portfolio_health(_two_c, SCHEMA, _two_r, [])["results"][
    "cat8_1_isolation_forest"]
_n1 = NEW.compute_portfolio_health(_two_c, SCHEMA, _two_r, [])["results"][
    "cat8_1_isolation_forest"]
divergence("D1.1 Isolation Forest", "a governed cohort of exactly two eligible projects",
           f"computed: abstained={_o1.get('abstained')}, "
           f"{len(_o1.get('projects') or {})} project score(s)",
           f"abstained={_n1.get('abstained')}, disposition={_n1.get('disposition')}",
           "v21 grew a forest on two projects, where each is the other's entire reference "
           "population; v22 is NOT_ESTIMABLE below three",
           _o1.get("abstained") is False and _n1.get("abstained") is True
           and _n1.get("disposition") == "NOT_ESTIMABLE")

# --- DIVERGENCE 3: PH.3 zero-slope vocabulary ---------------------------------------------------
_o3 = V21["results"]["cat8_3_trajectory_classifier"]["projects"]["A"][0]
_n3 = V22["results"]["cat8_3_trajectory_classifier"]["projects"]["A"][0]
divergence("D1.3 Signal Trajectory Classifier", "a constant cost-index history 1.0, 1.0, 1.0",
           f"classification {_o3['classification']}, equal-spacing reported: "
           f"{'equally_spaced' in _o3}",
           f"classification {_n3['classification']}, equally_spaced={_n3.get('equally_spaced')}",
           "v21 called a zero slope FLAT and reported nothing about the time basis; v22 uses the "
           "contract's STABLE and reports whether the series was equally spaced rather than "
           "leaving it assumed",
           _o3["classification"] == "FLAT" and _n3["classification"] == "STABLE"
           and "equally_spaced" not in _o3 and _n3.get("equally_spaced") is True)


# =================================================================================================
head("4. THE LEGITIMATE NON-DIVERGENCE, executed on both lines")
# =================================================================================================
# Run 34 changed what is REPORTED where a reading is possible. It changed nothing about WHEN a
# reading is possible at all, and nothing outside Portfolio Health. Both are checked by execution.
_o_abs = OLD.compute_portfolio_health(None, None, [], [])
_n_abs = NEW.compute_portfolio_health(None, None, [], [])
_same_abs = (sorted(_o_abs["results"]) == sorted(_n_abs["results"])
             and all(_o_abs["results"][k]["abstained"] == _n_abs["results"][k]["abstained"]
                     for k in _o_abs["results"])
             and all(_o_abs["results"][k]["abstention_reason"]
                     == _n_abs["results"][k]["abstention_reason"] for k in _o_abs["results"]))
ROWS.append(["NON_DIVERGENCE", "all five Portfolio Health modules",
             "no governed cohort supplied at all",
             "all five abstain, same five reasons", "all five abstain, same five reasons",
             "NO", "execution of both lines", "PASS" if _same_abs else "FAIL"])
check(_same_abs,
      "NON-DIVERGENCE: with NO governed cohort, both lines abstain identically -- same five "
      "identities, same five reasons, byte for byte. Run 34 changed what is reported where a "
      "reading is possible, not when a reading is possible")

_SI = {"bac": 1000000.0, "ac": 520000.0, "ev": 480000.0, "pv": 500000.0,
       "actual_pct_complete": 48.0, "planned_pct_complete": 50.0, "eac": 1080000.0}
_o_t = old_models.VALIDATED["A1.7"][1](dict(_SI), lambda: 0.5, "2026-01-31")
from app.simulation.models import VALIDATED as NEWV                    # noqa: E402
_n_t = NEWV["A1.7"][1](dict(_SI), lambda: 0.5, "2026-01-31")
_same_t = json.dumps(_o_t, sort_keys=True, default=str) == json.dumps(_n_t, sort_keys=True,
                                                                     default=str)
ROWS.append(["NON_DIVERGENCE", "A1.7 To-Complete Performance Index",
             "identical earned-value signal inputs",
             json.dumps(_o_t, sort_keys=True, default=str)[:120],
             json.dumps(_n_t, sort_keys=True, default=str)[:120],
             "NO", "execution of both lines", "PASS" if _same_t else "FAIL"])
check(_same_t,
      "NON-DIVERGENCE: a voting project-level module outside this run's scope is BYTE-IDENTICAL "
      "on both lines, so the v22 move is scoped to Portfolio Health")
check(_o_t.get("method_class") is not None,
      "and it really computed on both lines rather than agreeing by both abstaining")

check(_d >= 2, f"AT LEAST TWO GENUINE DIVERGENCES observed by execution: {_d} found", str(_d))
ROWS.append(["SUMMARY", "-", "-", f"v21 at {V21_COMMIT}", "v22 current",
             f"{_d} divergences, 2 non-divergences", "execution of both lines",
             "PASS" if _d >= 2 and _same_abs and _same_t else "FAIL"])
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
