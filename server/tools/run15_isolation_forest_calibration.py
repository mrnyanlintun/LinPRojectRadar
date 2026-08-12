"""
Run 15 Workstream B. Threshold calibration for the real Isolation Forest at D1.1.

NOT field validation. Everything here is a seeded synthetic population whose labels exist
before any score is computed. Nothing touches operational storage.

PREDECLARED THRESHOLD OBJECTIVE, fixed before any threshold was scored:
    choose the SMALLEST anomaly score threshold whose specificity on the CALIBRATION split is
    at least 0.95, that is a false-positive rate of at most one project in twenty. A portfolio
    anomaly flag sends a project to human review, and one review in twenty is a load a
    portfolio manager can carry. The shipped standardised-distance threshold reached
    specificity 0.720; that number was NOT used to set this objective and the old threshold is
    not carried over in any form.
Then FREEZE the threshold and evaluate ONCE on the HOLDOUT split.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.simulation.isolation_forest import IsolationForest

FEATURES = ("cpi", "spi", "risk", "pct")
TREES = 100
SUBSAMPLE = 256
SEED = 20250815


def vec(r):
    return [r["cpi"], r["spi"], r["risk"], r["pct"] / 100.0]


def normal(g, i, tag):
    return {"id": f"{tag}{i}", "cpi": g.gauss(0.98, 0.05), "spi": g.gauss(0.98, 0.05),
            "risk": min(0.9, max(0.0, g.gauss(0.30, 0.08))),
            "pct": min(95, max(5, g.gauss(45, 10)))}


def labelled_split(g, tag, reference):
    """The nine families of Run 14, so the two detectors are compared on like fixtures."""
    out = []
    for i in range(30):
        out.append(("clean normal", normal(g, i, tag + "H"), 0))
    for i in range(10):
        out.append(("duplicated normal", dict(reference[i], id=f"{tag}D{i}"), 0))
    for i in range(10):
        out.append(("boundary near-normal",
                    {"id": f"{tag}B{i}", "cpi": 0.98 + 0.11, "spi": g.gauss(0.98, 0.05),
                     "risk": 0.30, "pct": 45}, 0))
    for i in range(12):
        out.append(("extreme single feature",
                    {"id": f"{tag}X{i}",
                     "cpi": 0.98 + g.choice([-1, 1]) * g.uniform(0.35, 0.6),
                     "spi": g.gauss(0.98, 0.05), "risk": 0.30, "pct": 45}, 1))
    for i in range(12):
        out.append(("moderate single feature",
                    {"id": f"{tag}M{i}", "cpi": 0.98, "spi": 0.98,
                     "risk": min(0.98, 0.30 + g.uniform(0.30, 0.45)), "pct": 45}, 1))
    for i in range(12):
        out.append(("multivariate joint anomaly",
                    {"id": f"{tag}J{i}", "cpi": 0.98 + 0.13, "spi": 0.98 - 0.13,
                     "risk": 0.30 + 0.16, "pct": 45 + 22}, 1))
    for i in range(8):
        out.append(("unusual feature combination",
                    {"id": f"{tag}U{i}", "cpi": 1.20, "spi": 0.70,
                     "risk": 0.85, "pct": 90}, 1))
    for i in range(6):
        out.append(("isolated outlier",
                    {"id": f"{tag}O{i}", "cpi": 2.5, "spi": 0.2,
                     "risk": 0.95, "pct": 5}, 1))
    for i in range(6):
        out.append(("small anomaly cluster",
                    {"id": f"{tag}C{i}", "cpi": 1.45 + 0.01 * i, "spi": 1.45 + 0.01 * i,
                     "risk": 0.80, "pct": 85}, 1))
    return out


def build():
    g = random.Random(770011)
    reference = [normal(g, i, "R") for i in range(300)]
    cal = labelled_split(g, "CAL", reference)
    hold = labelled_split(g, "HLD", reference)
    return reference, cal, hold


def auc_roc(pairs):
    pos = [s for s, y in pairs if y == 1]
    neg = [s for s, y in pairs if y == 0]
    wins = sum(1 for a in pos for b in neg if a > b) + 0.5 * sum(
        1 for a in pos for b in neg if a == b)
    return wins / (len(pos) * len(neg))


def auc_pr(pairs):
    ordered = sorted(pairs, key=lambda p: -p[0])
    total = sum(y for _, y in ordered)
    tp = 0
    area = 0.0
    prev_recall = 0.0
    for i, (_, y) in enumerate(ordered, start=1):
        tp += y
        recall = tp / total
        precision = tp / i
        area += precision * (recall - prev_recall)
        prev_recall = recall
    return area


def confusion(scores, labels, t):
    tp = sum(1 for s, y in zip(scores, labels) if y == 1 and s >= t)
    fn = sum(1 for s, y in zip(scores, labels) if y == 1 and s < t)
    fp = sum(1 for s, y in zip(scores, labels) if y == 0 and s >= t)
    tn = sum(1 for s, y in zip(scores, labels) if y == 0 and s < t)
    return tp, fp, tn, fn


def metrics(tp, fp, tn, fn):
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "precision": tp / (tp + fp) if tp + fp else 0.0,
            "recall": tp / (tp + fn) if tp + fn else 0.0,
            "specificity": tn / (tn + fp) if tn + fp else 0.0,
            "false_positive_rate": fp / (tn + fp) if tn + fp else 0.0}


def main():
    reference, cal, hold = build()
    forest = IsolationForest([vec(r) for r in reference], n_trees=TREES,
                             subsample=SUBSAMPLE, seed=SEED)
    ref_ids = {r["id"] for r in reference}
    assert not (ref_ids & {r["id"] for _, r, _ in cal if not r["id"].startswith("CALD")})

    cal_scores = [forest.anomaly_score(vec(r)) for _, r, _ in cal]
    cal_labels = [y for _, _, y in cal]

    # CALIBRATION: smallest threshold reaching specificity 0.95. Grid over the score range.
    chosen = None
    for step in range(1, 1001):
        t = step / 1000.0
        m = metrics(*confusion(cal_scores, cal_labels, t))
        if m["specificity"] >= 0.95:
            chosen = (t, m)
            break
    t, cal_m = chosen
    print("CALIBRATION threshold:", t)
    print("  calibration:", {k: round(v, 4) if isinstance(v, float) else v
                             for k, v in cal_m.items()})
    print("  calibration ROC-AUC", round(auc_roc(list(zip(cal_scores, cal_labels))), 4),
          "PR-AUC", round(auc_pr(list(zip(cal_scores, cal_labels))), 4))

    # FROZEN. One evaluation on the holdout.
    h_scores = [forest.anomaly_score(vec(r)) for _, r, _ in hold]
    h_labels = [y for _, _, y in hold]
    h_m = metrics(*confusion(h_scores, h_labels, t))
    print("HOLDOUT at the frozen threshold:",
          {k: round(v, 4) if isinstance(v, float) else v for k, v in h_m.items()})
    print("  holdout ROC-AUC", round(auc_roc(list(zip(h_scores, h_labels))), 4),
          "PR-AUC", round(auc_pr(list(zip(h_scores, h_labels))), 4))
    fams = {}
    for (fam, _, y), s in zip(hold, h_scores):
        fams.setdefault(fam, []).append((s, y))
    print("  per family (mean score, flagged fraction):")
    for fam, vals in fams.items():
        print(f"    {fam:28s} mean={sum(s for s, _ in vals)/len(vals):.3f} "
              f"flagged={sum(1 for s, _ in vals if s >= t)/len(vals):.3f} label={vals[0][1]}")
    return t, cal_m, h_m, cal_scores, cal_labels, h_scores, h_labels


if __name__ == "__main__":
    main()
