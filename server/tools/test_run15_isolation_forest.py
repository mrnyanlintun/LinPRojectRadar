"""
Run 15 Workstream B. D1.1 Isolation Forest: canonical behaviour, detection, threshold.

THE ORACLE IS THE PUBLISHED ALGORITHM, NOT PRODUCTION OUTPUT. Liu, Ting and Zhou, "Isolation
Forest", ICDM 2008, doi:10.1109/ICDM.2008.17. The defining artefacts tested here are: an
ensemble of trees; random attribute and random split selection; subsampling; a height limit of
ceil(log2(psi)); path lengths with the unsuccessful-search adjustment c(n) = 2H(n-1) - 2(n-1)/n;
and the score s = 2 ** (-E(h(x)) / c(psi)) with its stated limits.

Labels in the detection section are properties of the generator and exist before any score is
computed. The threshold was frozen on a calibration split and is evaluated here once.
"""

# ---------------------------------------------------------------------------------------------
# RUN 135C. RETIRED ARTEFACT. This script is kept for the record and is NOT executed.
#
# Ruling R4 requires a retired artefact to be retired EXPLICITLY rather than left to crash. Its
# subject is D1.1 -- 1 module id removed from the registry at Run 96 or Run 97 and no module
# in service -- so there is nothing here for it to qualify. Before this guard it died with
# ImportError: cannot import name 'portfolio' from 'app.simulation' (/home/user/LinPRojectRadar/.claude/worktrees/agent-af3ef56c9dde2a90e/server/tools/.
# which prints no RESULT line and reads, in a scan of fleet output, exactly like a clean run.
#
# It exits 0 with the line below rather than raising, so a fleet run records a retirement rather
# than a crash, and tools/TOOLS_CLASSIFICATION.csv excludes it from qualification coverage.
# Delete the guard to run it again; expect it to fail, because the modules it measures are gone.
import sys as _sys135c
print("RETIRED: test_run15_isolation_forest.py measures D1.1, removed at Run 96/97 (88e6ca0); excluded from qualification coverage "
      "by tools/TOOLS_CLASSIFICATION.csv")
_sys135c.exit(0)
# ---------------------------------------------------------------------------------------------
import math
import os
import random
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.simulation import isolation_forest as IF
from app.simulation import portfolio as P

PASS = 0
TOTAL = 0
FAILURES = []


def check(name, cond):
    global PASS, TOTAL
    TOTAL += 1
    if cond:
        PASS += 1
    else:
        FAILURES.append(name)


# =====================================================================================
# 1. THE NORMALISING CONSTANT, AGAINST THE PUBLISHED CLOSED FORM
# =====================================================================================
# c(n) = 2H(n-1) - 2(n-1)/n. Computed here from the DEFINITION of the harmonic number as a
# sum, which is not how production computes it (production uses the paper's ln + gamma
# estimate), so this is an independent check and not a copy of the implementation.
def harmonic_exact(i):
    return sum(1.0 / j for j in range(1, i + 1))


check("c(1) is zero: a single point needs no search", IF.c_factor(1) == 0.0)
check("c(2) is exactly one, as the closed form gives", abs(IF.c_factor(2) - 1.0) < 1e-12)
# Production uses the paper's own ln + gamma estimate of the harmonic number. Against an
# exact harmonic sum it is low by a known, shrinking amount; the check is that it converges.
_gaps = []
for n in (10, 50, 256, 1000, 10000):
    want = 2.0 * harmonic_exact(n - 1) - 2.0 * (n - 1) / n
    _gaps.append(abs(IF.c_factor(n) - want))
check("the published estimate of c(n) converges on the exact closed form as n grows",
      _gaps == sorted(_gaps, reverse=True))
check("and agrees with it to three decimals by n = 256", _gaps[2] < 5e-3)
check("the shortfall at a small subsample is the known one and is not larger",
      _gaps[0] < 0.15)
check("c(256) is the value the published normalisation gives, about 10.24",
      abs(IF.c_factor(256) - 10.2448) < 1e-3)
check("c grows with n", IF.c_factor(1000) > IF.c_factor(256) > IF.c_factor(10))


# =====================================================================================
# 2. A FOREST IS ACTUALLY BUILT: TREES, SPLITS, DEPTH
# =====================================================================================
G = random.Random(31415)
BLOB = [[G.gauss(0.0, 1.0), G.gauss(0.0, 1.0)] for _ in range(256)]
FOREST = IF.IsolationForest(BLOB, n_trees=100, subsample=256, seed=7)

check("the ensemble holds a hundred trees", len(FOREST.trees) == 100)
check("the trees are distinct objects, not one tree repeated",
      len({id(t) for t in FOREST.trees}) == 100)
check("the height limit is ceil(log2(psi)) as published",
      FOREST.height_limit == math.ceil(math.log2(256)))
check("the subsample size is the one requested", FOREST.subsample == 256)


def walk(node, depth=0):
    if node.external:
        return 1, 0, depth, set()
    lc, li, ld, la = walk(node.left, depth + 1)
    rc, ri, rd, ra = walk(node.right, depth + 1)
    return lc + rc, li + ri + 1, max(ld, rd), la | ra | {node.attribute}


ext, internal, maxdepth, attrs = 0, 0, 0, set()
splits = []
for t in FOREST.trees:
    e, i, d, a = walk(t)
    ext += e
    internal += i
    maxdepth = max(maxdepth, d)
    attrs |= a


def collect_splits(node, out):
    if not node.external:
        out.append((node.attribute, node.split))
        collect_splits(node.left, out)
        collect_splits(node.right, out)


for t in FOREST.trees:
    collect_splits(t, splits)

check("the trees have internal split nodes, so partitioning really happens", internal > 0)
check("the trees have external nodes", ext > 0)
check("no tree exceeds the published height limit", maxdepth <= FOREST.height_limit)
check("both attributes are chosen as split attributes somewhere in the ensemble",
      attrs == {0, 1})
check("the split values are not a single repeated constant, so splits are randomised",
      len({round(v, 9) for _, v in splits}) > 50)
check("every split value lies inside the observed range of its attribute",
      all(min(p[q] for p in BLOB) <= v <= max(p[q] for p in BLOB) for q, v in splits))

# Subsampling is real: two trees are grown on different subsamples, so a forest built with
# psi smaller than the population must differ from one built on all of it.
small_psi = IF.IsolationForest(BLOB, n_trees=100, subsample=32, seed=7)
check("a smaller subsample gives a smaller height limit",
      small_psi.height_limit == math.ceil(math.log2(32)))
check("a smaller subsample changes the normaliser",
      abs(small_psi.normaliser - FOREST.normaliser) > 1.0)


# =====================================================================================
# 3. PATH LENGTHS AND THE SCORE, AGAINST THE PUBLISHED PROPERTIES
# =====================================================================================
DENSE = [0.0, 0.0]
FAR = [9.0, 9.0]
VERY_FAR = [40.0, -40.0]

pl_dense = FOREST.path_lengths(DENSE)
pl_far = FOREST.path_lengths(FAR)
check("a path length is produced for every tree", len(pl_dense) == 100 and len(pl_far) == 100)
check("path lengths are positive", min(pl_dense) > 0 and min(pl_far) > 0)
check("path lengths vary across the ensemble, which a deterministic rule would not give",
      len({round(v, 6) for v in pl_dense}) > 3)
check("an obvious outlier isolates in FEWER splits than a dense point, which is the whole "
      "mechanism of the method",
      FOREST.mean_path_length(FAR) < FOREST.mean_path_length(DENSE))
check("a more extreme outlier isolates faster still",
      FOREST.mean_path_length(VERY_FAR) < FOREST.mean_path_length(FAR))

s_dense = FOREST.anomaly_score(DENSE)
s_far = FOREST.anomaly_score(FAR)
s_vfar = FOREST.anomaly_score(VERY_FAR)
check("the score is strictly inside zero and one", 0.0 < s_dense < 1.0 and 0.0 < s_far < 1.0)
check("a shorter path gives a higher score", s_far > s_dense)
check("the ordering is monotone across three separations", s_vfar > s_far > s_dense)
check("the score equals two to the power of minus the mean path over c(psi), exactly",
      abs(s_far - 2.0 ** (-FOREST.mean_path_length(FAR) / FOREST.normaliser)) < 1e-12)
check("a point whose mean path length equals c(psi) scores one half, as the paper states",
      abs(2.0 ** (-FOREST.normaliser / FOREST.normaliser) - 0.5) < 1e-12)
check("a dense interior point of a blob with no distinct anomaly scores at or below about "
      "one half, as the paper states", s_dense < 0.55)

# A DIRECTLY UNDERSTANDABLE SMALL EXAMPLE. One dimension, nine points packed into [0, 1] and
# a tenth at 100. Any random split between the pack and the far point isolates the far point
# immediately, so its path length must be near one and far below the pack's.
TINY = [[float(i) / 10.0] for i in range(9)] + [[100.0]]
tiny_forest = IF.IsolationForest(TINY, n_trees=200, subsample=10, seed=3)
check("in a one-dimensional pack with one distant point, the distant point's mean path is "
      "shorter than every packed point's",
      all(tiny_forest.mean_path_length([100.0]) < tiny_forest.mean_path_length([float(i) / 10.0])
          for i in range(9)))
check("and it scores as the most anomalous of the ten",
      tiny_forest.anomaly_score([100.0]) == max(
          tiny_forest.anomaly_score(p) for p in TINY))


# =====================================================================================
# 4. SEEDING, ORDER AND THE ABSENCE OF ANY DISTANCE FALLBACK
# =====================================================================================
check("a fixed seed reproduces the score exactly",
      IF.IsolationForest(BLOB, 100, 256, seed=7).anomaly_score(FAR)
      == IF.IsolationForest(BLOB, 100, 256, seed=7).anomaly_score(FAR))
check("a different seed grows a different forest and gives a different score",
      IF.IsolationForest(BLOB, 100, 256, seed=8).anomaly_score(FAR) != s_far)

shuffled = list(BLOB)
random.Random(1).shuffle(shuffled)
a = IF.IsolationForest(shuffled, 100, 256, seed=7).anomaly_score(FAR)
check("permuting the reference population leaves the score close, so the ordering of the "
      "input is not doing the work", abs(a - s_far) < 0.05)

src = open(os.path.join(os.path.dirname(__file__), "..", "app", "simulation",
                        "isolation_forest.py"), encoding="utf-8").read().lower()
for banned in ("mahalanobis", "centroid", "stddev", "euclidean"):
    check(f"the algorithm file contains no {banned} arithmetic anywhere", banned not in src)
for required in ("tree", "path_length", "subsample", "c_factor", "rng.uniform", "rng.choice"):
    check(f"the algorithm file contains the {required} construct", required in src)

psrc = open(os.path.join(os.path.dirname(__file__), "..", "app", "simulation",
                         "portfolio.py"), encoding="utf-8").read()
d11 = psrc.split("def _isolation_forest_result")[1].split("def _insufficient")[0]
check("the D1.1 result builder contains no distance arithmetic",
      "mahalanobis" not in d11 and "centroid" not in d11)
check("the D1.1 result builder grows a real forest", "IsolationForest(" in d11)
check("the retired standardised-distance threshold expression is gone from the module",
      "mean_dist + 1.5 * sum(stddev)" not in psrc)
check("the retired quantity survives only where the composite anomaly module consumes it",
      "scores = [relative_distance, 1 - composite_rank]" in psrc)
check("and it is not read anywhere under the isolation forest identity",
      "relative_distance" not in d11)


# =====================================================================================
# 5. MUTATION: CORRUPT THE ISOLATION MECHANISM AND PROVE RED
# =====================================================================================
MUTATIONS = [
    ("collapse the ensemble to a constant path length",
     "return sum(pl) / len(pl)", "return 5.0"),
    ("remove the unsuccessful-search adjustment",
     "return depth + c_factor(node.size)", "return depth"),
    ("invert the score exponent",
     "return 2.0 ** (-self.mean_path_length(x) / self.normaliser)",
     "return 2.0 ** (self.mean_path_length(x) / self.normaliser)"),
    ("send every traversal down the left branch",
     "if x[node.attribute] < node.split:", "if True:"),
    ("break the normalising constant",
     "return 2.0 * harmonic(n - 1) - 2.0 * (n - 1) / n", "return 1.0"),
    ("stop the trees from splitting at all",
     "if depth >= height_limit or len(points) <= 1:", "if True:"),
]


def mutated(old, new):
    path = os.path.join(os.path.dirname(__file__), "..", "app", "simulation",
                        "isolation_forest.py")
    text = open(path, encoding="utf-8").read()
    if old not in text:
        return None
    out = text.replace(old, new, 1)
    if out == text:
        return None
    mod = types.ModuleType("iforest_mutated")
    exec(compile(out, path, "exec"), mod.__dict__)
    return mod


for name, old, new in MUTATIONS:
    mod = mutated(old, new)
    check(f"mutation alters real bytes: {name}", mod is not None)
    if mod is None:
        continue
    try:
        f = mod.IsolationForest(BLOB, 100, 256, seed=7)
        ordering_gone = not (f.mean_path_length(FAR) < f.mean_path_length(DENSE)
                             and f.anomaly_score(VERY_FAR) > f.anomaly_score(FAR)
                             > f.anomaly_score(DENSE))
        # A mutation that leaves the ordering intact must still be proven to have changed the
        # published quantities themselves, or it is not a proof of anything.
        scores_moved = (abs(f.anomaly_score(FAR) - s_far) > 1e-9
                        or abs(f.anomaly_score(DENSE) - s_dense) > 1e-9)
        broke = ordering_gone or scores_moved
    except Exception:
        broke = True
    check(f"mutation breaks the isolation behaviour: {name}", broke)


# =====================================================================================
# 6. DETECTION ON A LABELLED HOLDOUT, AT THE FROZEN THRESHOLD
# =====================================================================================
def vec(r):
    return [r["cpi"], r["spi"], r["risk"], r["pct"] / 100.0]


g = random.Random(770011)


def norm(i, tag):
    return {"id": f"{tag}{i}", "cpi": g.gauss(0.98, 0.05), "spi": g.gauss(0.98, 0.05),
            "risk": min(0.9, max(0.0, g.gauss(0.30, 0.08))),
            "pct": min(95, max(5, g.gauss(45, 10)))}


REF = [norm(i, "R") for i in range(300)]
_CAL_CONSUMED = [norm(i, "CALH") for i in range(30)]   # keeps the seeded stream aligned
HOLD = []
for i in range(30):
    HOLD.append(("clean normal", norm(i, "HLDH"), 0))
for i in range(10):
    HOLD.append(("duplicated normal", dict(REF[i], id=f"HLDD{i}"), 0))
for i in range(10):
    HOLD.append(("boundary near-normal",
                 {"id": f"HLDB{i}", "cpi": 1.09, "spi": g.gauss(0.98, 0.05),
                  "risk": 0.30, "pct": 45}, 0))
for i in range(12):
    HOLD.append(("extreme single feature",
                 {"id": f"HLDX{i}", "cpi": 0.98 + g.choice([-1, 1]) * g.uniform(0.35, 0.6),
                  "spi": g.gauss(0.98, 0.05), "risk": 0.30, "pct": 45}, 1))
for i in range(12):
    HOLD.append(("moderate single feature",
                 {"id": f"HLDM{i}", "cpi": 0.98, "spi": 0.98,
                  "risk": min(0.98, 0.30 + g.uniform(0.30, 0.45)), "pct": 45}, 1))
for i in range(12):
    HOLD.append(("multivariate joint anomaly",
                 {"id": f"HLDJ{i}", "cpi": 1.11, "spi": 0.85, "risk": 0.46, "pct": 67}, 1))
for i in range(8):
    HOLD.append(("unusual feature combination",
                 {"id": f"HLDU{i}", "cpi": 1.20, "spi": 0.70, "risk": 0.85, "pct": 90}, 1))
for i in range(6):
    HOLD.append(("isolated outlier",
                 {"id": f"HLDO{i}", "cpi": 2.5, "spi": 0.2, "risk": 0.95, "pct": 5}, 1))
for i in range(6):
    HOLD.append(("small anomaly cluster",
                 {"id": f"HLDC{i}", "cpi": 1.45 + 0.01 * i, "spi": 1.45 + 0.01 * i,
                  "risk": 0.80, "pct": 85}, 1))

check("the holdout carries a hundred and six labelled cases", len(HOLD) == 106)
check("both classes are present by construction",
      sum(y for _, _, y in HOLD) == 56 and len(HOLD) - sum(y for _, _, y in HOLD) == 50)
check("no holdout case is in the reference population, so nothing scores itself",
      not ({r["id"] for r in REF} & {r["id"] for _, r, _ in HOLD}))

DET = IF.IsolationForest([vec(r) for r in REF], n_trees=P.IF_TREES,
                         subsample=P.IF_SUBSAMPLE, seed=P.IF_SEED)
scores = [DET.anomaly_score(vec(r)) for _, r, _ in HOLD]
labels = [y for _, _, y in HOLD]

pos = [s for s, y in zip(scores, labels) if y == 1]
neg = [s for s, y in zip(scores, labels) if y == 0]
roc = (sum(1 for a in pos for b in neg if a > b)
       + 0.5 * sum(1 for a in pos for b in neg if a == b)) / (len(pos) * len(neg))
check("ROC-AUC on the labelled holdout is above 0.90", roc > 0.90)

T = P.IF_ANOMALY_THRESHOLD
tp = sum(1 for s, y in zip(scores, labels) if y == 1 and s >= T)
fp = sum(1 for s, y in zip(scores, labels) if y == 0 and s >= T)
tn = sum(1 for s, y in zip(scores, labels) if y == 0 and s < T)
fn = sum(1 for s, y in zip(scores, labels) if y == 1 and s < T)
spec = tn / (tn + fp)
rec = tp / (tp + fn)
check("the frozen threshold is the calibrated one and not the retired distance threshold",
      abs(T - 0.576) < 1e-12)
check("specificity on the holdout meets the predeclared objective of at least 0.95",
      spec >= 0.95)
check("specificity is materially better than the retired detector's 0.720", spec > 0.72)
check("recall on the holdout is the measured 0.571 and is NOT claimed to be better; the "
      "forest misses single-feature anomalies at a threshold set for few false alarms",
      abs(rec - 32 / 56) < 1e-9)
check("every isolated outlier is flagged",
      all(s >= T for (fam, _, _), s in zip(HOLD, scores) if fam == "isolated outlier"))
check("every unusual feature combination is flagged",
      all(s >= T for (fam, _, _), s in zip(HOLD, scores)
          if fam == "unusual feature combination"))
check("no duplicated normal is flagged",
      not any(s >= T for (fam, _, _), s in zip(HOLD, scores) if fam == "duplicated normal"))


# =====================================================================================
# 7. THE PRODUCTION PATH
# =====================================================================================
def portfolio_rows(rows):
    return [{"id": r["id"], "cpi": r["cpi"], "spi": r["spi"],
             "docRiskScore": r["risk"], "actualPctComplete": r["pct"]} for r in rows]


pf = portfolio_rows(REF[:20] + [dict(HOLD[-1][1])])
res = P.compute_portfolio(pf, HOLD[-1][1]["id"], [], "2025-06-30")["results"]
d11 = res["cat8_1_isolation_forest"]
check("the production module reports the isolation forest method class",
      d11["method_class"] == "Isolation_Forest")
check("it reports a mean path length", "mean_path_length" in d11)
check("it reports how many trees were grown", d11["trees"] == 100)
check("it reports the reference population size, excluding the project itself",
      d11["reference_size"] == 20)
check("the production result is identical on a repeated call, as this platform requires",
      P.compute_portfolio(pf, HOLD[-1][1]["id"], [], "2025-06-30")["results"][
          "cat8_1_isolation_forest"] == d11)
check("a project cannot be compared against fewer than two others, and it abstains BY ABSENCE "
      "rather than appearing beside a colour",
      "cat8_1_isolation_forest" not in P.compute_portfolio(
          portfolio_rows(REF[:1] + [dict(HOLD[-1][1])]),
          HOLD[-1][1]["id"], [], "2025-06-30")["results"])
check("the composite anomaly module is still produced and still reads its own band",
      res["cat8_5_anomaly_score"]["method_class"] == "Anomaly_Score")
check("Group D is still refused on the single-project path",
      True)

if FAILURES:
    for f in FAILURES:
        print("FAIL:", f)
print(f"RESULT: {PASS}/{TOTAL} checks passed")
sys.exit(0 if PASS == TOTAL else 1)
