#!/usr/bin/env python3
"""
RUN 33 FINAL CLOSURE. THE PH.1 FIXED-FOREST FIDELITY ORACLE.

THIS IS THE PRIMARY METHOD-FIDELITY PROOF FOR THE ISOLATION FOREST, and it replaces a test that
could never have been one. The withdrawn acceptance condition was a single-seed Spearman
correlation with scikit-learn of at least 0.99. Both implementations construct RANDOMIZED
ensembles, so one observed correlation between two independent draws mixes algorithm fidelity
with Monte Carlo ensemble variation and cannot separate them. The measurement that CAN separate
them is this one: FREEZE the forest, then require two independently written scorers to agree on
the same points over the same trees. Ensemble randomness is held constant and only the arithmetic
is under test.

THE BINDING CONSTRAINT, AND THE REASON FAULT 10 EXISTS. The expected scores here are NEVER
created by calling the production scorer. `server/tools/run33_frozen_forest.py` reimplements
c(n), the path-length traversal, the ensemble mean and the normalized score from the published
definition, and evaluates FROZEN TREE STRUCTURES recorded as plain data -- selected feature,
split value, left/right children, leaf sample size. Asserting against a copy of the logic is the
fourth of the five ways a check has lied in this repository, and section 9 below proves the
independence structurally rather than claiming it.

    c(n)      = 2 H(n-1) - 2 (n-1)/n,  c(0) = c(1) = 0,  c(2) = 1
    h_i(x)    = edges traversed, PLUS c(size) at the external node reached
    E[h(x)]   = (1/t) sum_i h_i(x)
    s(x, psi) = 2 ** (-E[h(x)] / c(psi))

Run (from server/):
    PYTHONIOENCODING=utf-8 python tests/test_run33_ph1_fixed_forest.py
"""

from __future__ import annotations

import csv
import hashlib
import inspect
import json
import os
import pathlib
import subprocess
import sys

_HERE = pathlib.Path(__file__).resolve().parent
ROOT = _HERE.parents[1]
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(ROOT / "server" / "tools"))

import run33_frozen_forest as O                                        # noqa: E402
from app.simulation import canonical_v8 as V8                          # noqa: E402
from app.simulation import isolation_forest as PROD                    # noqa: E402
from app.simulation import portfolio_health as PH                      # noqa: E402
from app.simulation.isolation_forest import IsolationForest            # noqa: E402

AUDIT = ROOT / "code_audit"
FIXTURES = (ROOT / "research_fixtures" / "synthetic" / "OG-SYNTH-0.5"
            / "package_D_portfolio_health")

PASS = 0
TOTAL = 0
FAILURES: list[str] = []


def check(cond, name, detail=""):
    global PASS, TOTAL
    TOTAL += 1
    if cond:
        PASS += 1
        print(f"  PASS  {name}" + (f"  [{detail}]" if detail else ""))
    else:
        FAILURES.append(name)
        print(f"  FAIL  {name}  [{detail}]")
    return bool(cond)


def head(t):
    print("\n" + "=" * 94 + f"\n{t}\n" + "=" * 94)


def fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


TOL = O.EQUIVALENCE_TOLERANCE


def _to_node(t):
    """
    Materialise one hand-built frozen tree into production's own node objects.

    STRUCTURE ONLY. Nothing here computes a path or a score; it exists so the PRODUCTION scorer
    can be run over a forest that neither implementation generated, which is the cleanest possible
    comparison: identical trees, two independent scorers.
    """
    if t["external"]:
        return PROD._Node(True, size=t["size"])
    return PROD._Node(False, attribute=t["feature"], split=t["split"],
                      left=_to_node(t["left"]), right=_to_node(t["right"]))


def _prod_path(t, x):
    return PROD._path_length(x, _to_node(t), 0)




# =================================================================================================
head("1. c(n) AND c(psi), REIMPLEMENTED FROM THE DEFINITION")
# =================================================================================================
check(O.oracle_c(0) == 0.0 and O.oracle_c(1) == 0.0, "c(0) = c(1) = 0")
check(O.oracle_c(2) == 1.0, "c(2) = 1 exactly")
# The oracle's c(n) must agree with production's, because both implement the SAME declared
# approximation. That is not circularity: the oracle wrote the formula out from the definition
# with its own Euler constant, and agreement is the claim under test.
_worst_c = max(abs(O.oracle_c(n) - PROD.c_factor(n)) for n in range(2, 400))
check(_worst_c <= TOL,
      "the independent c(n) agrees with production's over n = 2..399, so the two implement the "
      "same declared closed form", f"worst {_worst_c:.3e}")
# THE DECLARED DEVIATION IS PRESERVED AND MEASURED, not assumed. Production uses the paper's own
# ln + Euler estimate of the harmonic number; the exact sum is computed here independently.
_gaps = [abs(O.oracle_c(n) - O.oracle_c(n, exact=True)) for n in (10, 50, 256, 1000, 10000)]
check(_gaps == sorted(_gaps, reverse=True),
      "the declared ln + Euler approximation of H shrinks monotonically against the exact "
      "harmonic sum, which is the recorded Run-15 deviation measured rather than assumed",
      f"{_gaps[0]:.4f} -> {_gaps[-1]:.6f}")
check(_gaps[2] < 5e-3, "and agrees to three decimals by the published psi = 256")
check(abs(O.oracle_c(256) - 10.244771) < 1e-5,
      "c(256) is the published value, about 10.2448", f"{O.oracle_c(256):.6f}")


# =================================================================================================
head("2. ORACLE A -- SHALLOW ANOMALY OUTRANKS DEEP ISOLATION")
# =================================================================================================
_shallow = O.hand_forest([O.chain_tree(1)], 10)
_deep = O.hand_forest([O.chain_tree(6)], 10)
_ss, _sd = O.oracle_score(_shallow, [0.0]), O.oracle_score(_deep, [0.0])
check(abs(O.oracle_mean_path(_shallow, [0.0]) - 1.0) < 1e-12
      and abs(O.oracle_mean_path(_deep, [0.0]) - 6.0) < 1e-12,
      "the two hand-built forests isolate the point at exactly 1 and 6 edges",
      f"{O.oracle_mean_path(_shallow, [0.0])} vs {O.oracle_mean_path(_deep, [0.0])}")
check(_ss > _sd,
      "ORACLE A: a point isolated at a SHORTER path receives a HIGHER anomaly score",
      f"{_ss:.6f} > {_sd:.6f}")
# AND THE PRODUCTION SCORER, RUN OVER THE SAME HAND-BUILT TREES, SAYS THE SAME THING. The trees
# are materialised into production's own node objects here -- structure only, no scoring -- so
# the two implementations are compared on a forest neither of them generated.
check(abs(_prod_path(_shallow["trees"][0], [0.0]) - 1.0) <= TOL
      and abs(_prod_path(_deep["trees"][0], [0.0]) - 6.0) <= TOL,
      "and production's own path length over the same hand-built trees is 1 and 6",
      f"{_prod_path(_shallow['trees'][0], [0.0])} / {_prod_path(_deep['trees'][0], [0.0])}")


# =================================================================================================
head("3. ORACLE B -- IDENTICAL ADJUSTED PATH LENGTHS GIVE EQUAL SCORES")
# =================================================================================================
_fb = O.hand_forest([O.chain_tree(2), O.chain_tree(4), O.chain_tree(3)], 10)
_p1, _p2 = [0.10], [0.20]
check(O.oracle_path_lengths(_fb, _p1) == O.oracle_path_lengths(_fb, _p2),
      "two distinct points take the identical adjusted path length in EVERY frozen tree",
      str(O.oracle_path_lengths(_fb, _p1)))
check(O.oracle_score(_fb, _p1) == O.oracle_score(_fb, _p2),
      "ORACLE B: and therefore receive EQUAL scores",
      f"{O.oracle_score(_fb, _p1):.12f}")


# =================================================================================================
head("4. ORACLE C -- ENSEMBLE AVERAGING OVER HAND-SPECIFIED PATH LENGTHS")
# =================================================================================================
_A = O.hand_forest([O.chain_tree(1), O.chain_tree(2), O.chain_tree(2)], 10)
_B = O.hand_forest([O.chain_tree(3), O.chain_tree(3), O.chain_tree(3)], 10)
check(O.oracle_path_lengths(_A, [0.0]) == [1.0, 2.0, 2.0],
      "point A's per-tree path lengths are exactly [1, 2, 2]",
      str(O.oracle_path_lengths(_A, [0.0])))
check(O.oracle_path_lengths(_B, [0.0]) == [3.0, 3.0, 3.0],
      "point B's per-tree path lengths are exactly [3, 3, 3]",
      str(O.oracle_path_lengths(_B, [0.0])))
_mA, _mB = O.oracle_mean_path(_A, [0.0]), O.oracle_mean_path(_B, [0.0])
check(abs(_mA - 5 / 3) < 1e-12 and _mB == 3.0,
      "E[h(x)] = (1/t) sum h_i(x) gives A = 5/3 and B = 3, calculated independently",
      f"{_mA:.12f} and {_mB:.12f}")
# The expected scores, written out from the formula rather than taken from any implementation.
_expA = 2.0 ** (-(5 / 3) / O.oracle_c(10))
_expB = 2.0 ** (-3.0 / O.oracle_c(10))
check(abs(O.oracle_score(_A, [0.0]) - _expA) < 1e-12
      and abs(O.oracle_score(_B, [0.0]) - _expB) < 1e-12,
      "and s(x, psi) = 2 ** (-E[h(x)] / c(psi)) reproduces the hand-calculated scores",
      f"{_expA:.12f} and {_expB:.12f}")
check(O.oracle_score(_A, [0.0]) > O.oracle_score(_B, [0.0]),
      "ORACLE C: POINT A IS THE MORE ANOMALOUS, as the shorter mean path requires",
      f"{O.oracle_score(_A, [0.0]):.6f} > {O.oracle_score(_B, [0.0]):.6f}")


# =================================================================================================
head("5. ORACLE D -- THE TERMINAL-NODE c(n) ADJUSTMENT, NOT RAW DEPTH")
# =================================================================================================
_multi = O.hand_forest([O.chain_tree(2, leaf_size=7)], 10)
_single = O.hand_forest([O.chain_tree(2, leaf_size=1)], 10)
_hm = O.oracle_mean_path(_multi, [0.0])
_hs = O.oracle_mean_path(_single, [0.0])
check(_hs == 2.0,
      "a terminal node holding ONE sample adds c(1) = 0, so h(x) is the raw depth 2", f"{_hs}")
check(abs(_hm - (2.0 + O.oracle_c(7))) < 1e-12,
      "ORACLE D: a terminal node holding SEVEN samples adds c(7), so h(x) = depth + c(7)",
      f"{_hm:.12f} = 2 + {O.oracle_c(7):.12f}")
check(_hm != _hs and _hm > _hs,
      "so raw depth alone cannot reproduce both, which is what makes the adjustment observable")


# =================================================================================================
head("6. FIXED-FOREST SCORING EQUIVALENCE -- THE PRIMARY FIDELITY PROOF")
# =================================================================================================
_fx = fixture("ph1_isolation_forest_fixture.json")
_cohort = V8.PortfolioCohort(_fx["cohort"], _fx["feature_schema"], _fx["feature_records"])
_feats = [f for f in _cohort.features if f.required]
_X = [[_cohort.value(m, f) for f in _feats] for m in _cohort.members]
_ids = list(_cohort.project_ids)
_forest = IsolationForest(_X, n_trees=V8.IF_TREES,
                          subsample=min(V8.IF_SUBSAMPLE, len(_X)), seed=V8.IF_SEED)
_frozen = O.serialize_forest(_forest)

for _k in ("psi", "n_trees", "seed", "height_limit", "c_psi", "path_depth_convention",
           "external_node_adjustment", "trees"):
    check(_k in _frozen, f"the frozen forest records {_k}")
check(all(("feature" in t and "split" in t and "left" in t and "right" in t and "size" in t)
          for t in _frozen["trees"]),
      "and every tree records its selected feature, split value, children and leaf sample size")
check(abs(_frozen["c_psi"] - _forest.normaliser) <= TOL,
      "c(psi) recomputed by the oracle matches the constant production divides by",
      f"{_frozen['c_psi']:.15f}")

_worst_path = 0.0
for _pid, _x in zip(_ids, _X):
    _tp, _mp = _forest.path_lengths(_x), O.oracle_path_lengths(_frozen, _x)
    _worst_path = max(_worst_path, max(abs(a - b) for a, b in zip(_tp, _mp)))
check(_worst_path <= TOL,
      f"PER-TREE PATH LENGTHS AGREE across {len(_frozen['trees'])} trees x {len(_X)} points, so "
      f"the score agreement below is not two errors cancelling in the mean",
      f"worst {_worst_path:.3e}")

_worst = 0.0
for _pid, _x in zip(_ids, _X):
    _worst = max(_worst, abs(_forest.anomaly_score(_x) - O.oracle_score(_frozen, _x)))
check(_worst <= TOL,
      "FIXED-FOREST SCORE EQUIVALENCE: the production scorer and the independent frozen-forest "
      f"scorer agree on every point within the predeclared tolerance {TOL:.0e}, which is "
      f"justified by floating-point association alone",
      f"worst {_worst:.3e}")
check(abs(_forest.mean_path_length(_X[0]) - O.oracle_mean_path(_frozen, _X[0])) <= TOL,
      "and E[h(x)] agrees too")


# =================================================================================================
head("7. THE PRODUCTION ROUTE -- one governed cohort, ONE forest, comparable identities")
# =================================================================================================
# Entered through the real PH.1 route, not a helper: the canonical layer over a governed cohort.
_run = V8.compute_portfolio_health(_fx["cohort"], _fx["feature_schema"], _fx["feature_records"],
                                   [])
_d1 = _run["results"]["cat8_1_isolation_forest"]
check(_d1["abstained"] is False, "the real PH.1 route computes on the governed cohort")
_model = _d1["model"]
check(_model["one_forest_per_cohort"] is True
      and sorted(_model["fitted_project_population"]) == sorted(_d1["projects"]),
      "ONE forest is fitted per cohort/model version and every member is scored by it",
      f"{len(_model['fitted_project_population'])} projects")

# SEPARATE FOREST PER SCORED PROJECT = 0, proved by INDEPENDENT RECONSTRUCTION. A forest is
# rebuilt here from the model metadata the route reported, and the independent oracle scores every
# project from THAT ONE forest. If the route had fitted a forest per project, its scores would not
# be these scores.
_rebuilt = IsolationForest(_X, n_trees=_model["n_trees"],
                           subsample=_model["subsample_psi"], seed=_model["seed"])
_refrozen = O.serialize_forest(_rebuilt)
_route_gap = max(abs(_d1["projects"][p]["anomaly_score"] - O.oracle_score(_refrozen, x))
                 for p, x in zip(_ids, _X))
check(_route_gap <= TOL,
      "SEPARATE FOREST PER SCORED PROJECT = 0: every score the production route reported IS the "
      "score ONE forest produces, recomputed by the independent oracle from the reported model "
      "metadata", f"worst {_route_gap:.3e}")
_route_paths = max(abs(_d1["projects"][p]["mean_path_length"] - O.oracle_mean_path(_refrozen, x))
                   for p, x in zip(_ids, _X))
check(_route_paths <= TOL,
      "and the mean path lengths the route reported reach the canonical path-length "
      "implementation, independently recomputed", f"worst {_route_paths:.3e}")

for _k in ("cohort_id", "model_version", "seed", "feature_schema_version"):
    check(_model.get(_k) not in (None, ""),
          f"the result retains {_k}", str(_model.get(_k))[:48])
check(_d1["cohort"]["cohort_id"] == _fx["cohort"]["cohort_id"]
      and _d1["cohort"]["feature_schema_version"] == _fx["cohort"]["feature_schema_version"]
      and _d1["cohort"]["model_version"] == _fx["cohort"]["model_version"],
      "and the cohort identity travels with it")

# COMPARABILITY: scores are comparable only when cohort, schema and model version agree. A record
# on another schema is refused outright, so two scales can never be ranked together.
_mixed = [dict(_fx["feature_records"][0], feature_schema_version="OTHER")] \
    + _fx["feature_records"][1:]
_mr = V8.compute_portfolio_health(_fx["cohort"], _fx["feature_schema"], _mixed, [])
check(_mr["results"]["cat8_1_isolation_forest"]["abstained"] is True,
      "cross-project scores are comparable ONLY when cohort, schema and model identities agree: "
      "a member on another feature schema is refused rather than ranked alongside")

# The frozen synthetic threshold stays schema-bound.
check(V8.RUN15_FROZEN_THRESHOLD == 0.576, "the frozen synthetic threshold is unchanged at 0.576")
check(all(p["exploratory_flag"] is None for p in _d1["projects"].values()),
      "and yields NO flag under a schema that is not the one it was fitted on")


# =================================================================================================
head("8. REPRODUCIBILITY -- exact hashes, and a different seed is not a failure")
# =================================================================================================
_a = IsolationForest(_X, n_trees=V8.IF_TREES, subsample=min(V8.IF_SUBSAMPLE, len(_X)),
                     seed=V8.IF_SEED)
_b = IsolationForest(_X, n_trees=V8.IF_TREES, subsample=min(V8.IF_SUBSAMPLE, len(_X)),
                     seed=V8.IF_SEED)
_ha, _hb = O.forest_digest(O.serialize_forest(_a)), O.forest_digest(O.serialize_forest(_b))
check(_ha == _hb,
      "same cohort, feature schema, psi, tree count, seed and model version give an IDENTICAL "
      "tree structure, hashed over the frozen representation", _ha[:16])
_sa = [_a.anomaly_score(x) for x in _X]
_sb = [_b.anomaly_score(x) for x in _X]
check(_sa == _sb, "and identical scores for every project")
_c = IsolationForest(_X, n_trees=V8.IF_TREES, subsample=min(V8.IF_SUBSAMPLE, len(_X)),
                     seed=V8.IF_SEED + 1)
_hc = O.forest_digest(O.serialize_forest(_c))
check(_hc != _ha,
      "a DIFFERENT seed builds a different forest. THE METHOD IS RANDOMIZED: this is the method "
      "behaving, not a nondeterminism failure", _hc[:16])
check([_c.anomaly_score(x) for x in _X] != _sa,
      "and its scores may differ, which is permitted and is not a defect")
_gap_a = max(abs(_a.anomaly_score(x) - O.oracle_score(O.serialize_forest(_a), x)) for x in _X)
_gap_c = max(abs(_c.anomaly_score(x) - O.oracle_score(O.serialize_forest(_c), x)) for x in _X)
check(_gap_a <= TOL and _gap_c <= TOL,
      "the independent scorer agrees on BOTH forests, so the equivalence is a property of the "
      "arithmetic and not of one lucky draw", f"{_gap_a:.3e} / {_gap_c:.3e}")


# =================================================================================================
head("9. THE ORACLE IS GENUINELY INDEPENDENT")
# =================================================================================================
# INDEPENDENCE IS CHECKED ON THE PARSED SOURCE, not by searching for a substring: the module's
# own docstring names the production module it is checking, and a text search would either flag
# that prose or have to be weakened until it flagged nothing.
import ast                                                             # noqa: E402

_oracle_path = ROOT / "server" / "tools" / "run33_frozen_forest.py"
_src = _oracle_path.read_text(encoding="utf-8")
_tree = ast.parse(_src)
_imports = set()
for _node in ast.walk(_tree):
    if isinstance(_node, ast.Import):
        _imports.update(a.name for a in _node.names)
    elif isinstance(_node, ast.ImportFrom):
        _imports.add(_node.module or "")
check(not any(m.startswith("app") or "isolation_forest" in m or "canonical_v8" in m
              for m in _imports),
      "the oracle module imports NOTHING from production: its entire import set is the standard "
      "library", str(sorted(_imports)))
# And it references none of production's scoring names anywhere in its executable code.
_names = {n.id for n in ast.walk(_tree) if isinstance(n, ast.Name)} | \
         {n.attr for n in ast.walk(_tree) if isinstance(n, ast.Attribute)}
for _name in ("_path_length", "c_factor", "anomaly_score", "mean_path_length", "harmonic"):
    check(_name not in _names,
          f"and its executable code never references production's {_name}")
# The Euler constant is written out separately in the source text -- the two files share no
# literal -- while necessarily denoting the same double, as two statements of one constant must.
_prod_src = (ROOT / "server" / "app" / "simulation" / "isolation_forest.py").read_text(
    encoding="utf-8")
_o_lit = _src.split("EULER_GAMMA_ORACLE = ")[1].split("\n")[0].strip()
_p_lit = _prod_src.split("EULER_GAMMA = ")[1].split("\n")[0].strip()
check(_o_lit != _p_lit,
      "even the Euler constant is written out separately, so the two files share no literal text",
      f"{_o_lit} vs {_p_lit}")
check(O.EULER_GAMMA_ORACLE == PROD.EULER_GAMMA,
      "while denoting the same double, as two statements of one constant must")
# THE DECISIVE INDEPENDENCE PROOF: perturb production's path length IN PROCESS and require the
# oracle's answer to be UNMOVED. A delegating oracle would move with it.
_orig_pl = PROD._path_length
try:
    PROD._path_length = lambda x, node, depth: _orig_pl(x, node, depth) + 1.0
    _perturbed = _forest.anomaly_score(_X[0])
    _oracle_still = O.oracle_score(_frozen, _X[0])
finally:
    PROD._path_length = _orig_pl
_baseline = _forest.anomaly_score(_X[0])
check(abs(_perturbed - _baseline) > 1e-6,
      "with production's path length perturbed, the PRODUCTION score moves",
      f"{_baseline:.6f} -> {_perturbed:.6f}")
check(abs(_oracle_still - _baseline) <= TOL,
      "and the ORACLE's score does not, because it evaluates the frozen structures itself. An "
      "oracle that delegated to production would have moved with it",
      f"{_oracle_still:.6f}")


# =================================================================================================
head("10. THE ARTIFACTS ARE GENERATED, NOT HAND-AUTHORED, AND THE LAYERS STAY SEPARATE")
# =================================================================================================
_before = {n: (AUDIT / n).read_bytes() for n in (
    "run33_ph1_fixed_forest_oracle.csv", "run33_ph1_reproducibility.csv",
    "run33_ph1_oracle_closure.csv")}
_r = subprocess.run([sys.executable,
                     str(ROOT / "server" / "tools" / "build_run33_ph1_oracle_artifacts.py")],
                    cwd=str(ROOT), capture_output=True, text=True,
                    env={**os.environ, "PYTHONIOENCODING": "utf-8"})
check(_r.returncode == 0, "the PH.1 artifact generator runs cleanly", _r.stderr[-200:])
for _n, _bts in _before.items():
    check((AUDIT / _n).read_bytes() == _bts,
          f"{_n} is byte-identical to what the generator produces")


def _rows(name):
    with (AUDIT / name).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


_ff = _rows("run33_ph1_fixed_forest_oracle.csv")
check(all(r["result"] == "PASS" for r in _ff),
      f"every fixed-forest row passes ({len(_ff)} rows)")
for _t in ("ORACLE_A", "ORACLE_B", "ORACLE_C", "ORACLE_D", "FIXED_FOREST_SCORE",
           "FIXED_FOREST_PATHS", "FIXED_FOREST_C", "FIXED_FOREST_TOLERANCE"):
    check(any(r["record_type"] == _t for r in _ff),
          f"the fixed-forest artifact records {_t}")
_rp = _rows("run33_ph1_reproducibility.csv")
check(all(r["result"] == "PASS" for r in _rp), "every reproducibility row passes")
check(any(r["record_type"] == "DIFFERENT_SEED_STRUCTURE" and r["relation"] == "DIFFERENT"
          for r in _rp),
      "and a different seed is recorded as producing a different forest, not as a failure")

_cl = _rows("run33_ph1_oracle_closure.csv")
_layers = [r["assurance_layer"] for r in _cl]
check(_layers == ["CANONICAL_TREE_CONSTRUCTION", "FIXED_FOREST_SCORE_EQUIVALENCE",
                  "REPRODUCIBILITY", "CROSS_IMPLEMENTATION_STOCHASTIC_COMPARISON",
                  "TREE_COUNT_CALIBRATION", "THRESHOLD_CALIBRATION", "PH1_FINAL_DISPOSITION"],
      "THE SIX ASSURANCE LAYERS ARE STATED SEPARATELY, plus the final disposition",
      str(len(_layers)))
_status = {r["assurance_layer"]: r["status"] for r in _cl}
check(len(set(_status.values())) >= 4,
      "and they do NOT collapse into one PASS/FAIL: the statuses genuinely differ",
      str(sorted(set(_status.values()))))
check(_status["FIXED_FOREST_SCORE_EQUIVALENCE"] == "PASS",
      "fixed-forest score equivalence = PASS")
check(_status["REPRODUCIBILITY"] == "PASS", "reproducibility = PASS")
check(_status["TREE_COUNT_CALIBRATION"] == "PENDING_RUN_34",
      "tree-count calibration = PENDING_RUN_34")
check(_status["THRESHOLD_CALIBRATION"] == "PENDING_RUN_34",
      "threshold calibration = PENDING_RUN_34")
check(_status["CROSS_IMPLEMENTATION_STOCHASTIC_COMPARISON"]
      == "CROSS_IMPLEMENTATION_STOCHASTIC_COMPARISON",
      "and the correlation study is classified as a stochastic comparison, NOT as a fidelity "
      "verdict")


# =================================================================================================
head("11. THE CONVERGENCE STUDY, AND THE RECLASSIFICATION IT LICENSES")
# =================================================================================================
_conv = _rows("run33_ph1_cross_implementation_convergence.csv")
_pre = [r for r in _conv if r["record_type"] == "PREDECLARATION"]
check(len(_pre) == 1 and "frozen in OG-SYNTH-0.5" in _pre[0]["note"],
      "the campaign records its PREDECLARATION: fixture, seeds, tree counts and statistics")
_summ = {r["n_trees"]: r for r in _conv if r["record_type"] == "SUMMARY"}
check(sorted(_summ, key=int) == ["100", "400", "1000"],
      "summaries exist for t = 100, 400 and 1000", str(sorted(_summ, key=int)))
for _t, _r in _summ.items():
    check(int(_r["seed_count"]) >= 30, f"t={_t}: at least 30 independent seeds",
          _r["seed_count"])
    for _c in ("mean", "median", "min", "max", "sd", "q05", "q25", "q75", "q95",
               "top_rank_agreement", "production_self_stability", "sklearn_self_stability"):
        check(_r[_c] not in ("", "-"), f"t={_t}: {_c} reported", _r[_c])
_per = [r for r in _conv if r["record_type"] == "PER_SEED"]
check(len(_per) == 90,
      "every seed at every tree count is reported, so no favourable seed was selected",
      f"{len(_per)} per-seed rows")

# THE RECLASSIFICATION IS CONDITIONAL, AND THE CONDITION IS TESTED HERE, NOT ASSUMED.
check(_worst <= TOL and _worst_path <= TOL,
      "the fixed-forest equivalence condition that section 7's reclassification depends on is "
      "satisfied BY MEASUREMENT above, not by assertion")
_preserved = {r["n_trees"]: r["spearman"] for r in _conv
              if r["record_type"] == "PRESERVED_RUN33_SINGLE_SEED"}
check(_preserved == {"100": "0.987531", "400": "0.995540", "1000": "0.997484"},
      "and the original Run-33 single-seed observations are PRESERVED, not deleted or overwritten",
      str(_preserved))

# THE DECISIVE INTERPRETATION, asserted on the measured numbers rather than narrated: at t=100
# this implementation agrees with ITSELF across seeds about as closely as it agrees with
# scikit-learn, so the cross-implementation shortfall is ensemble variance and carries no
# information about fidelity.
_t100 = _summ["100"]
_cross, _self = float(_t100["mean"]), float(_t100["production_self_stability"])
check(abs(_cross - _self) < 0.01,
      "AT t=100 THE CROSS-IMPLEMENTATION AGREEMENT AND THE IMPLEMENTATION'S AGREEMENT WITH "
      "ITSELF ACROSS SEEDS ARE INDISTINGUISHABLE, so the shortfall is Monte Carlo ensemble "
      "variation and not an algorithm difference",
      f"cross {_cross:.6f} vs self {_self:.6f}")
check(float(_summ["1000"]["sd"]) < float(_summ["100"]["sd"]),
      "and increasing the tree count reduced Monte Carlo ranking variation on this frozen "
      "fixture", f"sd {_summ['100']['sd']} -> {_summ['1000']['sd']}")

# TREE COUNT STAYS AT THE PUBLISHED DEFAULT.
check(V8.IF_TREES == 100,
      "PRODUCTION TREE COUNT REMAINS 100, the published default. It was not raised to cross a "
      "test threshold, which would be tuning production to a fixture", str(V8.IF_TREES))
_interp = [r for r in _conv if r["record_type"] == "INTERPRETATION"]
check(len(_interp) == 1 and "NO STATEMENT IS MADE" in _interp[0]["note"],
      "and the artifact makes NO claim that 400 or 1,000 is therefore the correct operational "
      "setting")

# scikit-learn is not a production dependency.
_req = (ROOT / "server" / "requirements.txt").read_text(encoding="utf-8").lower()
check(not any(k in _req for k in ("scikit", "sklearn", "numpy", "scipy")),
      "scikit-learn remains dev-only and is not a production dependency")
_g = subprocess.run(["git", "grep", "-lE", "^import sklearn|^from sklearn", "--", "server/app"],
                    cwd=ROOT, capture_output=True, text=True)
check(not _g.stdout.strip(), "and no production file imports it", _g.stdout[:80])


# =================================================================================================
head("12. THE SIMULATION VERSION DID NOT MOVE")
# =================================================================================================
from app.simulation.models import SIMULATION_VERSION                   # noqa: E402

# RESTATED BY RUN 34. The Run-33 closure's finding was that fixed-forest equivalence passed, so
# THAT run required no analytical fix and did not move the stamp. That remains true and is
# asserted as a HISTORICAL position. Run 34 then changed Portfolio Health behaviour on its own
# account -- the PH.2 composite, the PH.1 cohort minimum, the PH.3 classification vocabulary --
# and moved the stamp to v22 for those reasons, which are nothing to do with this oracle.
from app.simulation.models import SIMULATION_VERSION_HISTORY as _H            # noqa: E402

check("sim-2026.08-v21" in _H,
      "the v21 stamp Run 33 closed under is still in the history, unmoved", str(_H[-3:]))
check(SIMULATION_VERSION == "sim-2026.08-v22",
      "and the live stamp is v22, moved by Run 34's calibration changes to PH.1, PH.2 and PH.3 "
      "and not by anything this fixed-forest oracle found", SIMULATION_VERSION)


print()
print("=" * 94)
print(f"RESULT: {PASS}/{TOTAL} checks passed")
print("=" * 94)
if FAILURES:
    print("FAILURES:")
    for f in FAILURES:
        print("  -", f)
sys.exit(1 if FAILURES else 0)
