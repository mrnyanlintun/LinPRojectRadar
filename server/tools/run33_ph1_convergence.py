#!/usr/bin/env python3
"""
RUN 33 FINAL CLOSURE. THE PH.1 REPEATED-SEED CROSS-IMPLEMENTATION CONVERGENCE STUDY.

WHAT THIS IS AND IS NOT. It is a DESCRIPTIVE study of how closely two independently written
randomized ensembles rank the same points, and of how that agreement behaves as the ensemble
grows. It is NOT a fidelity test and it is NOT converted into a production threshold in Run 33.
The fidelity question -- does this implementation compute what the published method defines --
is settled by the FIXED-FOREST equivalence in `build_run33_ph1_oracle_artifacts.py`, where the
forest is frozen and only the arithmetic is under test.

WHY THE OLD SINGLE-SEED TEST WAS THE WRONG INSTRUMENT. Both implementations draw their own
random attributes and split points. Equivalent algorithms need not produce identical forests from
nominally corresponding seeds -- the seeds index different generators consumed in different
orders -- so one observed correlation is one draw from a distribution, and calling a low draw a
canonical-fidelity failure conflates two different things. Hence a REPEATED-SEED campaign that
reports the distribution instead of a point.

===============================================================================================
PREDECLARATION. Fixture, seeds and statistics are fixed HERE, before the campaign is run, and
are not revised afterwards.
===============================================================================================

FIXTURE: `OG-SYNTH-0.5/package_D_portfolio_health/ph1_rank_agreement_fixture.json`, unchanged and
already frozen in a committed synthetic package at commit 4395f5a. It is chosen on
DISCRIMINATING-POWER grounds and that choice is prior to any result: 300 projects on a graded
radial spread, r = 0.3 + 6.0 * (i/299)^2, so true isolation differs materially between
neighbouring ranks. The compact ten-project structural fixture is deliberately NOT used here --
nine of its ten points are a near-identical cluster, so the ordering within the cluster is
sampling noise in both implementations and a rank correlation over it measures noise rather than
agreement. No fixture is modified by this script.

SEEDS: thirty, S_k = 20250815 + 1000 * k for k = 0..29, where 20250815 is the production seed
constant. Every seed is used, none is selected or discarded, and BOTH implementations receive the
SAME seed on each repetition.

TREE COUNTS: 100 (the published default and production's setting), 400 and 1,000.

STATISTICS, all predeclared: seed count, mean, median, minimum, maximum, standard deviation, the
5th/25th/75th/95th percentiles, top-ranked anomaly agreement, and the within-implementation rank
stability of each implementation across seeds (the mean pairwise Spearman correlation of an
implementation with ITSELF under different seeds, which is the Monte Carlo variation the
cross-implementation figure necessarily contains).

DEV-ONLY. scikit-learn is installed into a throwaway virtualenv by this script, is not in
server/requirements.txt, is imported by no committed production file, and this file is not named
test_*.py so the suite runner never executes it.
===============================================================================================
"""

from __future__ import annotations

import csv
import json
import pathlib
import statistics
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

FIXTURE = (ROOT / "research_fixtures" / "synthetic" / "OG-SYNTH-0.5"
           / "package_D_portfolio_health" / "ph1_rank_agreement_fixture.json")
OUT = ROOT / "code_audit" / "run33_ph1_cross_implementation_convergence.csv"

PRODUCTION_SEED = 20250815
SEEDS = tuple(PRODUCTION_SEED + 1000 * k for k in range(30))
TREE_COUNTS = (100, 400, 1000)
QUANTILES = (5, 25, 75, 95)

CHILD = r'''
import json, sys
import numpy as np
import sklearn
from sklearn.ensemble import IsolationForest
from scipy.stats import spearmanr

payload = json.load(open(sys.argv[1]))
X = np.array(payload["X"], dtype=float)
out = {"sklearn": sklearn.__version__, "runs": {}}
for t in payload["tree_counts"]:
    per_seed = {}
    for s in payload["seeds"]:
        f = IsolationForest(n_estimators=t, max_samples=payload["psi"], random_state=s,
                            contamination="auto", bootstrap=False).fit(X)
        per_seed[str(s)] = [float(v) for v in -f.score_samples(X)]
    out["runs"][str(t)] = per_seed
json.dump(out, open(sys.argv[2], "w"))
'''


def spearman(a, b):
    """Rank correlation, computed here so the summary does not depend on the child process."""
    n = len(a)
    ra, rb = _ranks(a), _ranks(b)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    da = sum((x - ma) ** 2 for x in ra) ** 0.5
    db = sum((y - mb) ** 2 for y in rb) ** 0.5
    return num / (da * db) if da and db else float("nan")


def _ranks(v):
    order = sorted(range(len(v)), key=lambda i: v[i])
    out = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        r = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            out[order[k]] = r
        i = j + 1
    return out


def main() -> int:
    from app.simulation import canonical_v8 as V8
    from app.simulation.isolation_forest import IsolationForest

    fx = json.loads(FIXTURE.read_text(encoding="utf-8"))
    cohort = V8.PortfolioCohort(fx["cohort"], fx["feature_schema"], fx["feature_records"])
    feats = [f for f in cohort.features if f.required]
    X = [[cohort.value(m, f) for f in feats] for m in cohort.members]
    psi = min(V8.IF_SUBSAMPLE, len(X))
    ids = list(cohort.project_ids)

    print(f"fixture: {FIXTURE.name}  n={len(X)}  psi={psi}  seeds={len(SEEDS)}  "
          f"tree counts={TREE_COUNTS}")

    ours = {t: {} for t in TREE_COUNTS}
    for t in TREE_COUNTS:
        for s in SEEDS:
            f = IsolationForest(X, n_trees=t, subsample=psi, seed=s)
            ours[t][s] = [f.anomaly_score(x) for x in X]
        print(f"  production t={t}: {len(SEEDS)} seeds done")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        venv = tmp / "venv"
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
        py = venv / "bin" / "python"
        subprocess.run([str(py), "-m", "pip", "install", "--quiet", "scikit-learn", "scipy"],
                       check=True)
        (tmp / "child.py").write_text(CHILD, encoding="utf-8")
        (tmp / "in.json").write_text(json.dumps(
            {"X": X, "psi": psi, "seeds": list(SEEDS), "tree_counts": list(TREE_COUNTS)}),
            encoding="utf-8")
        subprocess.run([str(py), str(tmp / "child.py"), str(tmp / "in.json"),
                        str(tmp / "out.json")], check=True)
        got = json.loads((tmp / "out.json").read_text(encoding="utf-8"))

    rows = [["record_type", "n_trees", "seed", "spearman", "top_rank_agreement",
             "seed_count", "mean", "median", "min", "max", "sd",
             "q05", "q25", "q75", "q95",
             "production_self_stability", "sklearn_self_stability", "note"]]
    rows.append(["PREDECLARATION", "-", "-", "-", "-", str(len(SEEDS)), "-", "-", "-", "-", "-",
                 "-", "-", "-", "-", "-", "-",
                 f"fixture {FIXTURE.name} (frozen in OG-SYNTH-0.5, unmodified); seeds "
                 f"{PRODUCTION_SEED} + 1000k for k=0..29, all used and none selected; tree "
                 f"counts {list(TREE_COUNTS)}; statistics fixed before the campaign was run. "
                 f"scikit-learn {got['sklearn']}, dev-only."])

    for t in TREE_COUNTS:
        theirs = got["runs"][str(t)]
        rhos, tops = [], []
        for s in SEEDS:
            a, b = ours[t][s], theirs[str(s)]
            r = spearman(a, b)
            agree = ids[max(range(len(a)), key=lambda i: a[i])] == \
                ids[max(range(len(b)), key=lambda i: b[i])]
            rhos.append(r)
            tops.append(agree)
            rows.append(["PER_SEED", str(t), str(s), f"{r:.6f}", "YES" if agree else "NO",
                         "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", ""])
        # Within-implementation stability: an implementation against ITSELF under other seeds.
        own = _self_stability([ours[t][s] for s in SEEDS])
        skl = _self_stability([theirs[str(s)] for s in SEEDS])
        q = statistics.quantiles(rhos, n=100, method="inclusive")
        rows.append(["SUMMARY", str(t), "-", "-",
                     f"{sum(tops)}/{len(tops)}", str(len(SEEDS)),
                     f"{statistics.mean(rhos):.6f}", f"{statistics.median(rhos):.6f}",
                     f"{min(rhos):.6f}", f"{max(rhos):.6f}",
                     f"{statistics.pstdev(rhos):.6f}",
                     *[f"{q[p - 1]:.6f}" for p in QUANTILES],
                     f"{own:.6f}", f"{skl:.6f}",
                     "DESCRIPTIVE cross-implementation comparison. NOT a fidelity requirement and "
                     "NOT a production threshold. The within-implementation stability columns are "
                     "each implementation against ITSELF under different seeds: that is the Monte "
                     "Carlo variation the cross-implementation figure necessarily contains."])
        print(f"  t={t}: mean {statistics.mean(rhos):.6f} median "
              f"{statistics.median(rhos):.6f} min {min(rhos):.6f} max {max(rhos):.6f} "
              f"sd {statistics.pstdev(rhos):.6f} top1 {sum(tops)}/{len(tops)} "
              f"self(prod) {own:.6f} self(skl) {skl:.6f}")

    rows.append(["PRESERVED_RUN33_SINGLE_SEED", "100", str(PRODUCTION_SEED), "0.987531", "-",
                 "1", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-",
                 "The original Run-33 single-seed observation, PRESERVED and RECLASSIFIED as a "
                 "CROSS_IMPLEMENTATION_STOCHASTIC_COMPARISON rather than a "
                 "CANONICAL_FIDELITY_FAILURE, which the fixed-forest score equivalence licenses. "
                 "It is not deleted and not overwritten."])
    rows.append(["PRESERVED_RUN33_SINGLE_SEED", "400", str(PRODUCTION_SEED), "0.995540", "-",
                 "1", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-",
                 "Preserved Run-33 observation."])
    rows.append(["PRESERVED_RUN33_SINGLE_SEED", "1000", str(PRODUCTION_SEED), "0.997484", "-",
                 "1", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-",
                 "Preserved Run-33 observation."])
    rows.append(["INTERPRETATION", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-",
                 "-", "-", "-", "-", "-", "-",
                 "Increasing the tree count reduced Monte Carlo ranking variation on this frozen "
                 "fixture. NO STATEMENT IS MADE that 400 or 1,000 is therefore the correct "
                 "operational setting: production remains at the published default of 100 and "
                 "tree-count calibration is Run-34 work. Raising the tree count to cross a test "
                 "threshold would be tuning production to a fixture."])

    with OUT.open("w", encoding="utf-8", newline="") as fh:
        csv.writer(fh, lineterminator="\n").writerows(rows)
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


def _self_stability(vectors):
    """Mean pairwise Spearman of one implementation with itself across seeds."""
    rs = []
    for i in range(len(vectors)):
        for j in range(i + 1, len(vectors)):
            rs.append(spearman(vectors[i], vectors[j]))
    return sum(rs) / len(rs)


if __name__ == "__main__":
    raise SystemExit(main())
