"""
RUN 30 -- INDEPENDENT REFERENCE IMPLEMENTATIONS OF MARCOS AND CRITIC-TOPSIS.

THE INDEPENDENCE PROOF, stated plainly so a reader can check it rather than take it on trust:

  * This module imports NOTHING from `app`. It cannot reach `app.simulation.canonical_v5`, so no
    production expression can be evaluated through it.
  * It works on plain lists of numbers assembled by its own reader, not on the production
    structure objects, and it carries its own orientation handling.
  * It was written from the published method steps -- Stevic et al. (2020) for MARCOS,
    Diakoulaki et al. (1995) for CRITIC, Hwang & Yoon for TOPSIS -- as those steps are set out in
    the Run-30 supervisory contract, and NOT by reading the production implementation.
  * The frozen dictionaries at the foot of this file are the expected intermediates and rankings.
    They are literals. The oracle suite compares production against BOTH this reference and those
    literals, so an error common to reference and production would still have to also match the
    frozen numbers.

BENCHMARK PROVENANCE: both benchmarks are HAND_DERIVED_CANONICAL_FIXTURE. Neither is taken from a
published worked example and neither is presented as one. Every intermediate is shown in
`code_audit/run30_decision_ranking_oracles.csv` and in the Run-30 report.
"""

from __future__ import annotations

import math


def _read(problem: dict) -> tuple[list[str], list[str], list[str], dict, dict]:
    """(alternative ids, criterion ids, orientations, values[alt][crit], weights[crit])."""
    crit_ids = [c["criterion_id"] for c in problem["criteria"]]
    orient = {c["criterion_id"]: c["orientation"] for c in problem["criteria"]}
    weights = {c["criterion_id"]: c.get("weight") for c in problem["criteria"]}
    alt_ids = [a["alternative_id"] for a in problem["alternatives"]]
    values = {a["alternative_id"]: dict(a["values"]) for a in problem["alternatives"]}
    return alt_ids, crit_ids, orient, values, weights


def marcos(problem: dict) -> dict:
    alt_ids, crit_ids, orient, values, raw_w = _read(problem)
    total = sum(raw_w[c] for c in crit_ids)
    w = {c: raw_w[c] / total for c in crit_ids}
    ai, aai = {}, {}
    for c in crit_ids:
        column = [values[a][c] for a in alt_ids]
        if orient[c] == "benefit":
            ai[c] = max(column)
            aai[c] = min(column)
        else:
            ai[c] = min(column)
            aai[c] = max(column)

    def norm_row(row):
        return {c: (row[c] / ai[c] if orient[c] == "benefit" else ai[c] / row[c])
                for c in crit_ids}

    s = {a: sum(w[c] * norm_row(values[a])[c] for c in crit_ids) for a in alt_ids}
    s_ai = sum(w[c] * norm_row(ai)[c] for c in crit_ids)
    s_aai = sum(w[c] * norm_row(aai)[c] for c in crit_ids)
    out = {}
    for a in alt_ids:
        km = s[a] / s_aai
        kp = s[a] / s_ai
        tot = kp + km
        f_km = kp / tot
        f_kp = km / tot
        out[a] = tot / (1.0 + (1.0 - f_kp) / f_kp + (1.0 - f_km) / f_km)
    order = sorted(alt_ids, key=lambda a: (-out[a], a))
    return {"weights": w, "ideal": ai, "anti_ideal": aai, "s": s, "s_ideal": s_ai,
            "s_anti_ideal": s_aai, "utility": out, "ranking": order}


def critic_topsis(problem: dict) -> dict:
    alt_ids, crit_ids, orient, values, _ = _read(problem)
    m = len(alt_ids)
    # CRITIC: min-max normalisation with orientation, sample standard deviation, Pearson
    # correlation, C_j = sigma_j * sum_k (1 - r_jk), weights normalised.
    z = {}
    for c in crit_ids:
        column = [values[a][c] for a in alt_ids]
        lo, hi = min(column), max(column)
        span = hi - lo
        z[c] = [((v - lo) / span) if orient[c] == "benefit" else ((hi - v) / span)
                for v in column]
    mean = {c: sum(z[c]) / m for c in crit_ids}
    sigma = {c: math.sqrt(sum((v - mean[c]) ** 2 for v in z[c]) / (m - 1)) for c in crit_ids}
    r = {}
    for j in crit_ids:
        r[j] = {}
        for k in crit_ids:
            cov = sum((z[j][i] - mean[j]) * (z[k][i] - mean[k]) for i in range(m))
            dj = math.sqrt(sum((z[j][i] - mean[j]) ** 2 for i in range(m)))
            dk = math.sqrt(sum((z[k][i] - mean[k]) ** 2 for i in range(m)))
            r[j][k] = cov / (dj * dk)
    info = {j: sigma[j] * sum(1.0 - r[j][k] for k in crit_ids) for j in crit_ids}
    tot = sum(info.values())
    weights = {j: info[j] / tot for j in crit_ids}
    # TOPSIS: vector normalisation, weights, ideals by orientation, Euclidean distances.
    nrm = {}
    for c in crit_ids:
        column = [values[a][c] for a in alt_ids]
        d = math.sqrt(sum(v * v for v in column))
        nrm[c] = [v / d for v in column]
    wtd = {c: [weights[c] * v for v in nrm[c]] for c in crit_ids}
    a_plus, a_minus = {}, {}
    for c in crit_ids:
        if orient[c] == "benefit":
            a_plus[c], a_minus[c] = max(wtd[c]), min(wtd[c])
        else:
            a_plus[c], a_minus[c] = min(wtd[c]), max(wtd[c])
    rows = []
    for i, a in enumerate(alt_ids):
        dp = math.sqrt(sum((wtd[c][i] - a_plus[c]) ** 2 for c in crit_ids))
        dm = math.sqrt(sum((wtd[c][i] - a_minus[c]) ** 2 for c in crit_ids))
        rows.append({"alternative_id": a, "d_plus": dp, "d_minus": dm,
                     "closeness": dm / (dp + dm) if (dp + dm) else 0.0})
    order = sorted(rows, key=lambda x: (-x["closeness"], x["alternative_id"]))
    return {"sigma": sigma, "correlation": r, "information": info, "weights": weights,
            "positive_ideal": a_plus, "negative_ideal": a_minus, "rows": rows,
            "ranking": [x["alternative_id"] for x in order]}


# =================================================================================================
# THE FROZEN EXPECTED INTERMEDIATES. Literals, filled in once from the hand derivation recorded in
# code_audit/run30_decision_ranking_oracles.csv, never regenerated from production.
# =================================================================================================

#: MARCOS benchmark: A1(4,3,2) A2(2,5,4) A3(3,1,1) on C1 benefit .5, C2 benefit .3, C3 cost .2.
#: Ideal AI = (4, 5, 1); anti-ideal AAI = (2, 1, 4).
#: Normalised against AI: A1 (1, .6, .5) -> S = .5(1)+.3(.6)+.2(.5) = .78
#:                        A2 (.5, 1, .25) -> S = .25+.30+.05 = .60
#:                        A3 (.75, .2, 1) -> S = .375+.06+.20 = .635
#:                        AAI (.5, .2, .25) -> S_AAI = .25+.06+.05 = .36 ; AI -> S_AI = 1.0
MARCOS_FROZEN = {
    "ideal": {"C1": 4.0, "C2": 5.0, "C3": 1.0},
    "anti_ideal": {"C1": 2.0, "C2": 1.0, "C3": 4.0},
    "s": {"A1": 0.78, "A2": 0.60, "A3": 0.635},
    "s_ideal": 1.0,
    "s_anti_ideal": 0.36,
#: K- = S/S_AAI ; K+ = S/S_AI. f(K-) = K+/(K++K-) ; f(K+) = K-/(K++K-).
#: f(K) = (K+ + K-) / (1 + (1-f(K+))/f(K+) + (1-f(K-))/f(K-)).
#: A1: K- = .78/.36 = 2.1666666667, K+ = .78, sum = 2.9466666667,
#:     f(K-) = .78/2.9466666667 = 9/34, f(K+) = 2.1666666667/2.9466666667 = 25/34,
#:     (1-f(K+))/f(K+) = 9/25 = .36, (1-f(K-))/f(K-) = 25/9 = 2.7777777778,
#:     f(K) = 2.9466666667 / 4.1377777778 = 0.7121374866.
    "k_minus": {"A1": 2.1666666666666665, "A2": 1.6666666666666667, "A3": 1.7638888888888888},
    "k_plus": {"A1": 0.78, "A2": 0.60, "A3": 0.635},
    "utility": {"A1": 0.7121374865735767, "A2": 0.5477980665950591,
                "A3": 0.5797529538131042},
    "ranking": ["A1", "A3", "A2"],
}

#: CRITIC-TOPSIS benchmark: four alternatives, three criteria, C3 a cost criterion.
#: A1(8,5,3) A2(6,7,5) A3(9,4,6) A4(5,8,2).
#: Min-max normalised with orientation, every column becomes a permutation of {0,.25,.75,1}:
#:   C1 (8,6,9,5) -> (.75,.25,1,0) ; C2 (5,7,4,8) -> (.25,.75,0,1) ;
#:   C3 cost (3,5,6,2) -> (.75,.25,0,1).
#: Each column has mean .5 and sample variance .625/3, so sigma = sqrt(.2083333) = .4564354646.
#: r(C1,C2) = -1 exactly (C2 = 1 - C1). r(C1,C3) = -.375/.625 = -.6. r(C2,C3) = +.6.
#:   C_C1 = .4564354646 * (0 + 2 + 1.6) = 1.6431676725
#:   C_C2 = .4564354646 * (2 + 0 + 0.4) = 1.0954451150
#:   C_C3 = .4564354646 * (1.6 + 0.4 + 0) = 0.9128709292
#:   sum = 3.6514837167 -> w = (.45, .30, .25) exactly.
CRITIC_FROZEN = {
    "sigma": {"C1": 0.45643546458763845, "C2": 0.45643546458763845,
              "C3": 0.45643546458763845},
    "information": {"C1": 1.6431676725154982, "C2": 1.0954451150103324,
                    "C3": 0.9128709291752769},
    "weights": {"C1": 0.44999999999999996, "C2": 0.30000000000000004, "C3": 0.25},
    "closeness": {"A1": 0.6078816912578591, "A2": 0.39211830874214104,
                  "A3": 0.45337109921054747, "A4": 0.5466289007894526},
    "ranking": ["A1", "A4", "A3", "A2"],
}
