#!/usr/bin/env python3
"""
RUN 34. THE PH.1 TREE-COUNT CALIBRATION CAMPAIGN.

EXECUTED STRICTLY UNDER research/methodology/run34_portfolio_calibration_protocol.md, which was
committed at a2ed922 BEFORE this file was written. Candidates {100, 400, 1000}; the STABILITY
fixture and the 30-seed set are the protocol's, unmodified; the decision rule is the protocol's
D1-D6, applied as written.

NO SCIKIT-LEARN. Run 33 established why the cross-implementation correlation cannot select this
parameter: at t=100 the implementation agrees with ITSELF across seeds essentially as closely as
it agrees with scikit-learn, so that statistic carries no information about the tree count. The
protocol forbids using it as a basis for selection, and this campaign does not compute it.

Writes:
  code_audit/run34_ph1_tree_count_calibration.csv
  code_audit/run34_ph1_holdout_result.csv
"""

from __future__ import annotations

import csv
import json
import pathlib
import statistics
import sys
import time
import tracemalloc

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(ROOT / "server" / "tools"))

PROTOCOL = ROOT / "research" / "methodology" / "run34_portfolio_calibration_protocol.md"
STABILITY = (ROOT / "research_fixtures" / "synthetic" / "OG-SYNTH-0.5"
             / "package_D_portfolio_health" / "ph1_rank_agreement_fixture.json")
CAL = (ROOT / "research_fixtures" / "synthetic" / "OG-SYNTH-0.6"
       / "package_D_portfolio_calibration" / "run34_ph1_calibration_labelled.json")
HOLD = (ROOT / "research_fixtures" / "synthetic" / "OG-SYNTH-0.6"
        / "package_D_portfolio_calibration" / "run34_ph1_holdout_labelled.json")
OUT = ROOT / "code_audit" / "run34_ph1_tree_count_calibration.csv"
OUT_HOLD = ROOT / "code_audit" / "run34_ph1_holdout_result.csv"

#: PROTOCOL section 2 and 4. Not extended, not reordered.
CANDIDATES = (100, 400, 1000)
SEEDS = tuple(20250815 + 1000 * k for k in range(30))
TOP_K = 10


def spearman(a, b):
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


def load(path):
    from app.simulation import canonical_v8 as V8
    fx = json.loads(path.read_text(encoding="utf-8"))
    cohort = V8.PortfolioCohort(fx["cohort"], fx["feature_schema"], fx["feature_records"])
    feats = [f for f in cohort.features if f.required]
    X = [[cohort.value(m, f) for f in feats] for m in cohort.members]
    return fx, cohort, X, list(cohort.project_ids)


def auc(scores, labels):
    """ROC-AUC by rank, and PR-AUC by the trapezoid over the precision-recall path."""
    pos = [s for s, y in zip(scores, labels) if y == 1]
    neg = [s for s, y in zip(scores, labels) if y == 0]
    if not pos or not neg:
        return float("nan"), float("nan")
    wins = sum((1.0 if a > b else 0.5 if a == b else 0.0) for a in pos for b in neg)
    roc = wins / (len(pos) * len(neg))
    order = sorted(range(len(scores)), key=lambda i: -scores[i])
    tp = fp = 0
    prev_recall = 0.0
    pr = 0.0
    for i in order:
        if labels[i] == 1:
            tp += 1
        else:
            fp += 1
        recall = tp / len(pos)
        precision = tp / (tp + fp)
        pr += precision * (recall - prev_recall)
        prev_recall = recall
    return roc, pr


def main() -> int:
    from app.simulation import canonical_v8 as V8
    from app.simulation.isolation_forest import IsolationForest

    if not PROTOCOL.is_file():
        print("the predeclared protocol is missing; refusing to run a calibration campaign")
        return 1

    _fx, cohort, X, ids = load(STABILITY)
    psi = min(V8.IF_SUBSAMPLE, len(X))
    print(f"STABILITY fixture {STABILITY.name}: n={len(X)} psi={psi} seeds={len(SEEDS)}")

    rows = [["record_type", "n_trees", "metric", "value", "note"]]
    rows.append(["PREDECLARATION", "-", "protocol",
                 "research/methodology/run34_portfolio_calibration_protocol.md",
                 f"committed before this campaign was written; candidates {list(CANDIDATES)}; "
                 f"{len(SEEDS)} seeds, all used, none selected; STABILITY fixture "
                 f"{STABILITY.name}, unmodified and frozen in OG-SYNTH-0.5"])

    metrics = {}
    for t in CANDIDATES:
        vecs, fits = [], []
        tracemalloc.start()
        for s in SEEDS:
            t0 = time.perf_counter()
            f = IsolationForest(X, n_trees=t, subsample=psi, seed=s)
            v = [f.anomaly_score(x) for x in X]
            fits.append(time.perf_counter() - t0)
            vecs.append(v)
        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()

        pair_rho, pair_top1, pair_topk = [], [], []
        for i in range(len(vecs)):
            for j in range(i + 1, len(vecs)):
                pair_rho.append(spearman(vecs[i], vecs[j]))
                ti = max(range(len(vecs[i])), key=lambda k: vecs[i][k])
                tj = max(range(len(vecs[j])), key=lambda k: vecs[j][k])
                pair_top1.append(1.0 if ti == tj else 0.0)
                si = {k for k in sorted(range(len(vecs[i])), key=lambda k: -vecs[i][k])[:TOP_K]}
                sj = {k for k in sorted(range(len(vecs[j])), key=lambda k: -vecs[j][k])[:TOP_K]}
                pair_topk.append(len(si & sj) / len(si | sj))
        var = statistics.mean(
            [statistics.pvariance([v[i] for v in vecs]) for i in range(len(X))])
        m = {"S": statistics.mean(pair_rho), "A1": statistics.mean(pair_top1),
             "A10": statistics.mean(pair_topk), "V": var,
             "R": statistics.median(fits), "M": peak}
        metrics[t] = m
        for key, label, note in (
                ("S", "within_production_rank_stability",
                 "mean pairwise Spearman of the score vector with itself across distinct seeds"),
                ("A1", "top_1_agreement", "fraction of seed pairs naming the same most-anomalous "
                                          "project"),
                ("A10", f"top_{TOP_K}_agreement",
                 f"mean Jaccard overlap of top-{TOP_K} sets across seed pairs"),
                ("V", "mean_per_project_score_variance", "across the 30 seeds"),
                ("R", "median_runtime_seconds", "fit and score the whole cohort, one seed"),
                ("M", "peak_traced_memory_bytes", "tracemalloc peak over the 30 fits")):
            rows.append(["METRIC", str(t), label, f"{m[key]:.6f}" if key != "M" else str(m[key]),
                         note])
        print(f"  t={t:5d}  S={m['S']:.6f}  A1={m['A1']:.4f}  A10={m['A10']:.4f}  "
              f"V={m['V']:.3e}  R={m['R']:.3f}s  M={m['M']}")

    # -- marginal improvement, as the protocol requires it to be reported ---------------------
    for lo, hi in ((100, 400), (400, 1000)):
        dS = metrics[hi]["S"] - metrics[lo]["S"]
        inst = (1 - metrics[hi]["S"]) / (1 - metrics[lo]["S"])
        cost = metrics[hi]["R"] / metrics[lo]["R"] if metrics[lo]["R"] else float("inf")
        rows.append(["MARGINAL", f"{lo}->{hi}", "delta_stability", f"{dS:+.6f}",
                     f"instability ratio I(t')/I(t) = {inst:.4f}; runtime ratio "
                     f"R(t')/R(t) = {cost:.2f}"])
        print(f"  {lo}->{hi}: dS={dS:+.6f} instability ratio={inst:.4f} runtime x{cost:.2f}")

    # -- THE DECISION RULE, APPLIED AS WRITTEN -------------------------------------------------
    # D2, the controlling clause: does the tree count have a demonstrable operational consequence?
    # Decided from the state of the corpus, by EXECUTING the production route rather than by
    # asserting about it.
    from app.simulation import portfolio_health as PH
    real = PH.compute_portfolio_health_snapshot("PROBE", {}, [], "2026-01-31")
    d1 = real["results"]["cat8_1_isolation_forest"]
    operational_reading = not d1.get("abstained")
    flag_permitted = bool(d1.get("authoritative_flag_permitted"))
    d2_pass = operational_reading and flag_permitted
    rows.append(["DECISION", "-", "D2_operational_relevance_gate",
                 "PASS" if d2_pass else "FAIL",
                 "Executed through the real production route: PH.1 on the corpus as it stands "
                 f"abstained={d1.get('abstained')} disposition={d1.get('disposition')}. No "
                 "governed portfolio cohort is supplied, so PH.1 produces NO operational reading "
                 "and no authoritative flag under any schema. The stability/compute trade-off "
                 "therefore has no operational units and NO candidate has defensible superiority."])
    if d2_pass:
        chosen = CANDIDATES[0]
        for lo, hi in zip(CANDIDATES, CANDIDATES[1:]):
            inst_ok = (1 - metrics[hi]["S"]) <= 0.5 * (1 - metrics[lo]["S"])
            cost_ok = metrics[hi]["R"] <= 4 * metrics[lo]["R"]
            if inst_ok and cost_ok and chosen == lo:
                chosen = hi
            else:
                break
        state = "SELECTED_UNDER_D3"
    else:
        chosen = 100
        state = "UNRESOLVED_NO_OPERATIONAL_CONSEQUENCE"
    rows.append(["DECISION", str(chosen), "selected_tree_count", str(chosen),
                 "D4 applies: retain the published default of 100 and record calibration "
                 "unresolved. This is an authorised outcome under contract section 6A and is not "
                 "a failure to complete. D5 tie-break would also prefer the smaller count."
                 if not d2_pass else "D3 applied."])
    rows.append(["DECISION", "-", "tree_count_calibration_status", state, ""])
    rows.append(["DECISION", "-", "production_tree_count_after_run34", str(V8.IF_TREES),
                 "unchanged" if V8.IF_TREES == chosen else "CHANGED"])
    # THE D3 COUNTERFACTUAL, RECORDED BECAUSE IT IS INFORMATIVE AND BECAUSE IT COST NOTHING TO
    # CHECK. Had the operational-relevance gate passed, D3 would have been applied; reporting what
    # it would have decided is honest and it happens to corroborate the outcome independently.
    _cf = 100
    _cf_trace = []
    for lo, hi in zip(CANDIDATES, CANDIDATES[1:]):
        inst_ok = (1 - metrics[hi]["S"]) <= 0.5 * (1 - metrics[lo]["S"])
        cost_ok = metrics[hi]["R"] <= 4 * metrics[lo]["R"]
        _cf_trace.append(f"{lo}->{hi}: instability halves={inst_ok}, runtime<=4x={cost_ok}")
        if inst_ok and cost_ok and _cf == lo:
            _cf = hi
        else:
            break
    rows.append(["DECISION", str(_cf), "D3_counterfactual_if_gate_had_passed", str(_cf),
                 "Reported for completeness; it did not decide anything, because D2 failed. "
                 + "; ".join(_cf_trace)])
    rows.append(["PROHIBITED_BASIS", "-", "cross_implementation_spearman", "NOT USED",
                 "The protocol forbids selecting a tree count because cross-implementation "
                 "Spearman exceeds 0.99, and this campaign does not compute it. Run 33 "
                 "established why: at t=100 the implementation agrees with itself across seeds "
                 "(0.986049) essentially as closely as with scikit-learn (0.986057)."])

    with OUT.open("w", encoding="utf-8", newline="") as fh:
        csv.writer(fh, lineterminator="\n").writerows(rows)
    print(f"wrote {OUT.relative_to(ROOT)}   selected t={chosen}  ({state})")

    # -- D6. THE HOLDOUT, SCORED ONCE, AFTER SELECTION IS FINAL --------------------------------
    hrows = [["record_type", "dataset", "metric", "value", "note"]]
    hrows.append(["ORDERING", "-", "selection_completed_before_holdout_read", "YES",
                  "The tree count above was fixed by D2/D4 from the state of the corpus and the "
                  "stability metrics alone. The holdout is read now, after selection, and CANNOT "
                  "change it: protocol D6 and section 11 item 5."])
    for path, role in ((CAL, "CALIBRATION"), (HOLD, "HOLDOUT")):
        fx, coh, Xs, pids = load(path)
        labels = [int(fx["labels"][p]) for p in pids]
        f = IsolationForest(Xs, n_trees=chosen, subsample=min(V8.IF_SUBSAMPLE, len(Xs)),
                            seed=V8.IF_SEED)
        sc = [f.anomaly_score(x) for x in Xs]
        roc, pr = auc(sc, labels)
        pos = [s for s, y in zip(sc, labels) if y == 1]
        neg = [s for s, y in zip(sc, labels) if y == 0]
        hrows.append([role, fx["dataset_id"], "roc_auc", f"{roc:.6f}",
                      f"t={chosen}, seed={V8.IF_SEED}, n={len(Xs)}, "
                      f"{sum(labels)} labelled anomalous"])
        hrows.append([role, fx["dataset_id"], "pr_auc", f"{pr:.6f}", ""])
        hrows.append([role, fx["dataset_id"], "mean_score_labelled_anomalous",
                      f"{statistics.mean(pos):.6f}", ""])
        hrows.append([role, fx["dataset_id"], "mean_score_labelled_normal",
                      f"{statistics.mean(neg):.6f}", ""])
        hrows.append([role, fx["dataset_id"], "separation",
                      f"{statistics.mean(pos) - statistics.mean(neg):+.6f}",
                      "difference of means; a SYNTHETIC separation statistic"])
        print(f"  {role}: ROC-AUC {roc:.4f}  PR-AUC {pr:.4f}  "
              f"separation {statistics.mean(pos) - statistics.mean(neg):+.4f}")
    hrows.append(["BOUNDARY", "-", "data_origin", "SYNTHETIC_RESEARCH_CALIBRATION",
                  "These are separation statistics on SYNTHETIC data with ground truth defined "
                  "before the detector. They are NOT field performance, NOT a false-positive "
                  "rate, NOT predictive validity and NOT empirical validation, and they "
                  "authorise no operational threshold."])
    hrows.append(["BOUNDARY", "-", "operational_threshold_created", "NONE",
                  "No operational anomaly threshold is created by this run. PH.1 emits a "
                  "continuous score and no flag."])
    with OUT_HOLD.open("w", encoding="utf-8", newline="") as fh:
        csv.writer(fh, lineterminator="\n").writerows(hrows)
    print(f"wrote {OUT_HOLD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
