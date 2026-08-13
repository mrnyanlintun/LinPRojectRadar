"""
Run 19 independent oracles for Category 7, evidence combination and epistemic uncertainty.

Written from supervisory specification section 16 and from nothing else. Self proved at import.
Imports nothing from server/app.

THE GENERAL CATEGORY-7 RULE the specification states, and which governs every disposition drawn
from this file: these methods represent uncertainty in different mathematical forms, and passing
their ALGEBRA does not establish that the memberships, masses, linguistic probabilities or
reliability values fed into them are empirically calibrated. Everything here tests algebra and
admissibility. None of it tests provenance, which is a separate column.
"""

from __future__ import annotations

import itertools
import math


# ------------------------------------------------------------------ 7.1 Dempster-Shafer

def dempster(m1: dict[frozenset, float], m2: dict[frozenset, float]) -> dict:
    """
    Specification 7.1. K is the mass on empty intersections; the combined mass on a nonempty A is
    the sum of products intersecting to A, over (1 - K).

    Total conflict, K = 1, has NO combined mass: the specification requires an explicit
    total-conflict state rather than a division by zero or a fabricated verdict.
    """
    k = 0.0
    raw: dict[frozenset, float] = {}
    for a, va in m1.items():
        for b, vb in m2.items():
            inter = a & b
            if not inter:
                k += va * vb
            else:
                raw[inter] = raw.get(inter, 0.0) + va * vb
    if abs(k - 1.0) < 1e-12:
        return {"conflict": 1.0, "total_conflict": True, "mass": None}
    return {"conflict": k, "total_conflict": False,
            "mass": {a: v / (1.0 - k) for a, v in raw.items()}}


def belief(mass: dict[frozenset, float], a: frozenset) -> float:
    """Specification 7.1. Bel(A) = sum of m(B) for B a subset of A."""
    return sum(v for b, v in mass.items() if b <= a)


def plausibility(mass: dict[frozenset, float], a: frozenset) -> float:
    """Specification 7.1. Pl(A) = sum of m(B) for B intersecting A."""
    return sum(v for b, v in mass.items() if b & a)


def discount(mass: dict[frozenset, float], alpha: float, theta: frozenset) -> dict:
    """Specification 7.1. m'(A) = alpha*m(A) for A != Theta; m'(Theta) = 1-alpha+alpha*m(Theta)."""
    out = {a: alpha * v for a, v in mass.items() if a != theta}
    out[theta] = 1.0 - alpha + alpha * mass.get(theta, 0.0)
    return out


# ------------------------------------------------------------------ 7.2 Rough sets

def approximations(classes: list[set], x: set) -> dict:
    """
    Specification 7.2. The lower approximation is the union of equivalence classes fully inside
    X; the upper is the union of those intersecting X; the boundary is upper less lower.

    The specification's worked case: U = {1,2,3,4} partitioned as {1,2} and {3,4}, with
    X = {1,3,4}, gives a lower approximation of {3,4}, an upper of {1,2,3,4} and a boundary of
    {1,2}.
    """
    lower: set = set()
    upper: set = set()
    for cls in classes:
        if cls <= x:
            lower |= cls
        if cls & x:
            upper |= cls
    return {"lower": lower, "upper": upper, "boundary": upper - lower}


# ------------------------------------------------------------------ 7.3 Neutrosophic

def neutrosophic_admissible(t: float, i: float, f: float) -> bool:
    """
    Specification 7.3. Each of T, I and F lies in [0,1], and UNLIKE ordinary probabilities they
    need NOT sum to one. That is the defining difference and it is what is tested.
    """
    return all(0.0 <= v <= 1.0 for v in (t, i, f))


# ------------------------------------------------------------------ 7.4 Interval fuzzy

def interval_admissible(lo: float, hi: float) -> bool:
    """Specification 7.4. 0 <= mu_L <= mu_U <= 1."""
    return 0.0 <= lo <= hi <= 1.0


def interval_intersection(a: tuple, b: tuple) -> tuple:
    """Specification 7.4, standard min/max operators: [min(l1,l2), min(u1,u2)]."""
    return (min(a[0], b[0]), min(a[1], b[1]))


def interval_union(a: tuple, b: tuple) -> tuple:
    """Specification 7.4: [max(l1,l2), max(u1,u2)]."""
    return (max(a[0], b[0]), max(a[1], b[1]))


# ------------------------------------------------------------------ 7.5 Z-numbers

def z_number(a_value: float, b_reliability: float) -> dict:
    """
    Specification 7.5. Z = (A, B): a restriction and the reliability of that restriction.

    Both components must survive the input contract. A missing reliability may NOT silently
    become one, so it is returned as None and the caller must handle it.
    """
    if b_reliability is None:
        return {"A": a_value, "B": None, "qualified": None}
    return {"A": a_value, "B": b_reliability, "qualified": a_value * b_reliability}


# ------------------------------------------------------------------ 7.6 PLTS

def plts_admissible(terms: dict[str, float]) -> bool:
    """Specification 7.6. Probabilities are non-negative and, when complete, sum to at most one."""
    return all(p >= 0 for p in terms.values()) and sum(terms.values()) <= 1.0 + 1e-9


def plts_score(terms: dict[str, float], order: list[str]) -> float:
    """The expected index over the ORDERED linguistic term set, which is the declared operator."""
    idx = {s: i for i, s in enumerate(order)}
    total = sum(terms.values())
    if total <= 0:
        raise ValueError("a probabilistic linguistic term set with no probability has no score")
    return sum(idx[s] * p for s, p in terms.items()) / total


# ------------------------------------------------------------------ 7.7 Plithogenic

def plithogenic_aggregate(d1: float, d2: float, contradiction: float) -> float:
    """
    Specification 7.7. A published plithogenic aggregation whose LIMITING CASES at the
    contradiction-degree endpoints are what the specification asks be tested.

    At c = 0 the two appurtenance degrees are fully compatible and the operator is the t-norm
    (product). At c = 1 they are fully contradictory and it is the t-conorm (probabilistic sum).
    In between it interpolates. The endpoints are the testable content.
    """
    if not 0.0 <= contradiction <= 1.0:
        raise ValueError("a contradiction degree lies in nought to one")
    t_norm = d1 * d2
    t_conorm = d1 + d2 - d1 * d2
    return (1 - contradiction) * t_norm + contradiction * t_conorm


# ------------------------------------------------------------------ 7.8 Belief rule base

def brb_aggregate(rules: list[dict]) -> dict:
    """
    Specification 7.8. A rule is IF antecedents THEN a belief distribution over consequents, with
    beta_j >= 0 and their sum at most one.

    With ONE fully activated rule and no others, the output must equal that rule's consequent
    distribution EXACTLY, which is the specification's worked oracle. The aggregation implemented
    here is activation-weighted, which is the declared form being checked against.
    """
    active = [r for r in rules if r["activation"] > 0]
    if not active:
        return {"activated": 0, "belief": None}
    total = sum(r["activation"] * r.get("weight", 1.0) for r in active)
    consequents: set = set()
    for r in active:
        consequents |= set(r["belief"])
    out = {c: sum(r["activation"] * r.get("weight", 1.0) * r["belief"].get(c, 0.0)
                  for r in active) / total for c in consequents}
    return {"activated": len(active), "belief": out}


def belief_distribution_admissible(belief_map: dict[str, float]) -> bool:
    """Specification 7.8. beta_j >= 0 and sum beta_j <= 1."""
    return all(v >= 0 for v in belief_map.values()) and sum(belief_map.values()) <= 1.0 + 1e-9


# ------------------------------------------------------------------ 7.9 Quantum probability

def born_rule(amplitudes: list[complex], projector_index: int) -> float:
    """
    Specification 7.9. P(A) = <psi|P_A|psi>, which for a projector onto one basis state is the
    squared modulus of that amplitude.

    The specification's worked case: |psi> = (1/sqrt2)(|0> + |1>) has P(0) = .5.
    """
    norm = sum(abs(a) ** 2 for a in amplitudes)
    if abs(norm - 1.0) > 1e-9:
        raise ValueError("the state is not normalised, so it is not a state")
    return abs(amplitudes[projector_index]) ** 2


def sequential_measurement(amplitudes: list[complex], first: list[list[complex]],
                           second: list[list[complex]]) -> float:
    """
    Specification 7.9. Order effects require NONCOMMUTING projectors, so this applies two
    projectors in sequence and returns the resulting probability. Applying them in the other
    order gives a different answer exactly when they do not commute, which is the whole point.
    """
    def apply(matrix, vec):
        return [sum(matrix[i][j] * vec[j] for j in range(len(vec))) for i in range(len(matrix))]
    v = apply(first, amplitudes)
    v = apply(second, v)
    return sum(abs(x) ** 2 for x in v)


# ------------------------------------------------------------------ 7.10 to 7.17 admissibility

def pythagorean_admissible(mu: float, nu: float) -> bool:
    """Specification 7.10. mu^2 + nu^2 <= 1."""
    return 0 <= mu <= 1 and 0 <= nu <= 1 and mu * mu + nu * nu <= 1.0 + 1e-12


def pythagorean_hesitancy(mu: float, nu: float) -> float:
    """Specification 7.10. pi = sqrt(1 - mu^2 - nu^2)."""
    return math.sqrt(max(0.0, 1.0 - mu * mu - nu * nu))


def picture_admissible(mu: float, eta: float, nu: float) -> bool:
    """Specification 7.11. mu, eta, nu >= 0 and mu + eta + nu <= 1."""
    return all(v >= 0 for v in (mu, eta, nu)) and mu + eta + nu <= 1.0 + 1e-12


def picture_refusal(mu: float, eta: float, nu: float) -> float:
    """Specification 7.11. r = 1 - mu - eta - nu."""
    return 1.0 - mu - eta - nu


def hesitant_score_mean(h: list[float]) -> float:
    """
    Specification 7.12. If the chosen score is the arithmetic mean it is this, but the
    specification is explicit that the scoring function must be DECLARED and that the mean is
    not the only canonical choice.
    """
    if not h:
        raise ValueError("an empty hesitant fuzzy element has no score")
    return sum(h) / len(h)


def type2_footprint_admissible(lower: float, upper: float) -> bool:
    """Specification 7.13. 0 <= lower(x) <= upper(x) <= 1."""
    return 0.0 <= lower <= upper <= 1.0


def max_entropy_distribution(n: int) -> list[float]:
    """
    Specification 7.14. Maximising H(p) = -sum p ln p subject only to normalisation gives the
    UNIFORM distribution. For two outcomes that is (.5, .5) with H = ln 2.
    """
    return [1.0 / n] * n


def shannon_entropy_nats(p: list[float]) -> float:
    return -sum(x * math.log(x) for x in p if x > 0)


def possibility_of(pi: dict[str, float], a: set) -> float:
    """Specification 7.15. Pi(A) = sup over A of pi(x)."""
    vals = [v for k, v in pi.items() if k in a]
    return max(vals) if vals else 0.0


def necessity_of(pi: dict[str, float], a: set) -> float:
    """Specification 7.15. N(A) = 1 - Pi(complement of A)."""
    return 1.0 - possibility_of(pi, set(pi) - a)


def spherical_admissible(mu: float, nu: float, pi_: float) -> bool:
    """Specification 7.16. mu^2 + nu^2 + pi^2 <= 1."""
    return mu * mu + nu * nu + pi_ * pi_ <= 1.0 + 1e-12


def fermatean_admissible(mu: float, nu: float) -> bool:
    """Specification 7.17. mu^3 + nu^3 <= 1."""
    return mu ** 3 + nu ** 3 <= 1.0 + 1e-12


# ------------------------------------------------------------------ 7.18 MARCOS

def marcos(matrix: dict[str, dict[str, float]], weights: dict[str, float],
           benefit: dict[str, bool]) -> dict:
    """
    The published MARCOS steps, implemented separately from production as specification 7.18
    requires, over a real decision matrix with at least two alternatives.

    An ideal and an anti-ideal alternative are formed from the matrix; each is normalised
    according to whether the criterion is a benefit or a cost; the weighted sums give the two
    utility degrees, and the final utility function gives the ranking.
    """
    crits = list(weights)
    if len(matrix) < 2:
        raise ValueError("MARCOS ranks alternatives and one alternative is not a ranking")
    ideal = {c: (max(matrix[a][c] for a in matrix) if benefit[c]
                 else min(matrix[a][c] for a in matrix)) for c in crits}
    anti = {c: (min(matrix[a][c] for a in matrix) if benefit[c]
                else max(matrix[a][c] for a in matrix)) for c in crits}
    rows = dict(matrix)
    rows["__IDEAL__"] = ideal
    rows["__ANTI__"] = anti

    def norm(a, c):
        return (rows[a][c] / ideal[c]) if benefit[c] else (ideal[c] / rows[a][c])

    s = {a: sum(weights[c] * norm(a, c) for c in crits) for a in rows}
    s_ai, s_id = s["__ANTI__"], s["__IDEAL__"]
    out = {}
    for a in matrix:
        k_neg = s[a] / s_ai
        k_pos = s[a] / s_id
        f_kn = k_pos / (k_pos + k_neg)
        f_kp = k_neg / (k_pos + k_neg)
        out[a] = (k_pos + k_neg) / (1 + (1 - f_kp) / f_kp + (1 - f_kn) / f_kn)
    return {"utility": out, "ranking": sorted(out, key=lambda a: -out[a])}


# ------------------------------------------------------------------ 7.19 CRITIC-TOPSIS

def _std(xs: list[float]) -> float:
    n = len(xs)
    m = sum(xs) / n
    return math.sqrt(sum((x - m) ** 2 for x in xs) / n)


def _corr(a: list[float], b: list[float]) -> float:
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((y - mb) ** 2 for y in b))
    return num / (da * db) if da and db else 0.0


def critic_weights(matrix: dict[str, dict[str, float]]) -> dict[str, float]:
    """
    Specification 7.19. C_j = sigma_j * sum_k (1 - r_jk); w_j = C_j / sum C.

    Computed on the NORMALISED matrix, and it requires several alternatives: with one row every
    standard deviation is zero and no weight is defined, which is the degeneracy the
    specification warns about.
    """
    crits = list(next(iter(matrix.values())))
    if len(matrix) < 2:
        raise ValueError("CRITIC derives contrast across alternatives and one row has none")
    cols = {c: [matrix[a][c] for a in matrix] for c in crits}
    normed = {}
    for c in crits:
        lo, hi = min(cols[c]), max(cols[c])
        normed[c] = [((v - lo) / (hi - lo)) if hi > lo else 0.0 for v in cols[c]]
    info = {c: _std(normed[c]) * sum(1 - _corr(normed[c], normed[k]) for k in crits)
            for c in crits}
    total = sum(info.values())
    if total <= 0:
        raise ValueError("no criterion carries contrast, so no weights are defined")
    return {c: info[c] / total for c in crits}


def topsis(matrix: dict[str, dict[str, float]], weights: dict[str, float],
           benefit: dict[str, bool]) -> dict:
    """Specification 7.19. Vector normalise, weight, find the ideals, distances and closeness."""
    crits = list(weights)
    denom = {c: math.sqrt(sum(matrix[a][c] ** 2 for a in matrix)) for c in crits}
    v = {a: {c: weights[c] * (matrix[a][c] / denom[c]) for c in crits} for a in matrix}
    best = {c: (max(v[a][c] for a in v) if benefit[c] else min(v[a][c] for a in v))
            for c in crits}
    worst = {c: (min(v[a][c] for a in v) if benefit[c] else max(v[a][c] for a in v))
             for c in crits}
    cc = {}
    for a in v:
        dp = math.sqrt(sum((v[a][c] - best[c]) ** 2 for c in crits))
        dn = math.sqrt(sum((v[a][c] - worst[c]) ** 2 for c in crits))
        cc[a] = dn / (dp + dn) if (dp + dn) else 0.0
    return {"closeness": cc, "ranking": sorted(cc, key=lambda a: -cc[a])}


# ------------------------------------------------------------------ 7.20 Hypersoft

def hypersoft_tuples(attribute_values: dict[str, list[str]]) -> list[tuple]:
    """
    Specification 7.20. The Cartesian product of the disjoint attribute-value subspaces. EVERY
    required tuple must be explicit.
    """
    keys = list(attribute_values)
    return [tuple(zip(keys, combo))
            for combo in itertools.product(*(attribute_values[k] for k in keys))]


def hypersoft_complete(mapping: dict, attribute_values: dict[str, list[str]]) -> dict:
    """
    Specification 7.20's critical test: a missing tuple may NOT silently receive a favourable or
    default value. It must be reported as incomplete and the method must abstain.
    """
    required = hypersoft_tuples(attribute_values)
    missing = [t for t in required if t not in mapping]
    return {"required": len(required), "missing": missing, "complete": not missing}


# ------------------------------------------------------------------ self proof

def self_test() -> list[str]:
    fails: list[str] = []

    def eq(label, got, want, tol=1e-9):
        if got is None or abs(float(got) - float(want)) > tol:
            fails.append(f"{label}: got {got!r}, specification says {want!r}")

    G, R = "G", "R"
    THETA = frozenset({G, R})

    # 7.1 -- the specification's worked combination.
    m1 = {frozenset({G}): 0.6, THETA: 0.4}
    m2 = {frozenset({G}): 0.5, THETA: 0.5}
    c = dempster(m1, m2)
    eq("7.1 conflict on the worked case", c["conflict"], 0.0)
    eq("7.1 combined mass on Green", c["mass"][frozenset({G})], 0.8)
    eq("7.1 combined mass on the frame", c["mass"][THETA], 0.2)
    tc = dempster({frozenset({G}): 1.0}, {frozenset({R}): 1.0})
    if not tc["total_conflict"] or tc["mass"] is not None:
        fails.append("7.1 total conflict must return an explicit state, never a verdict")
    eq("7.1 total conflict K", tc["conflict"], 1.0)
    eq("7.1 belief in Green", belief(c["mass"], frozenset({G})), 0.8)
    eq("7.1 plausibility of Green", plausibility(c["mass"], frozenset({G})), 1.0)
    if not belief(c["mass"], frozenset({G})) <= plausibility(c["mass"], frozenset({G})):
        fails.append("7.1 belief may never exceed plausibility")
    d = discount({frozenset({G}): 0.6, THETA: 0.4}, 0.5, THETA)
    eq("7.1 discounted mass on Green", d[frozenset({G})], 0.3)
    eq("7.1 discounted mass on the frame", d[THETA], 0.7)
    eq("7.1 a discounted mass still sums to one", sum(d.values()), 1.0)

    # 7.2 -- the specification's worked approximations.
    a = approximations([{1, 2}, {3, 4}], {1, 3, 4})
    if a["lower"] != {3, 4}:
        fails.append(f"7.2 lower approximation: got {a['lower']}, specification says {{3,4}}")
    if a["upper"] != {1, 2, 3, 4}:
        fails.append(f"7.2 upper approximation: got {a['upper']}")
    if a["boundary"] != {1, 2}:
        fails.append(f"7.2 boundary region: got {a['boundary']}, specification says {{1,2}}")
    exact = approximations([{1, 2}, {3, 4}], {3, 4})
    if exact["boundary"]:
        fails.append("7.2 a set that is a union of classes has an empty boundary")

    # 7.3 -- T, I, F need not sum to one, which is the defining difference.
    if not neutrosophic_admissible(0.9, 0.9, 0.9):
        fails.append("7.3 T, I and F need not sum to one")
    if neutrosophic_admissible(1.5, 0.1, 0.1):
        fails.append("7.3 a component outside nought to one is inadmissible")

    # 7.4 -- the specification's worked interval operators.
    A, B = (0.4, 0.7), (0.5, 0.8)
    if interval_intersection(A, B) != (0.4, 0.7):
        fails.append(f"7.4 intersection: got {interval_intersection(A, B)}")
    if interval_union(A, B) != (0.5, 0.8):
        fails.append(f"7.4 union: got {interval_union(A, B)}")
    if not interval_admissible(*A) or interval_admissible(0.8, 0.4):
        fails.append("7.4 admissibility requires the lower bound not exceed the upper")

    # 7.5 -- reliability must survive, and a missing one may not become one.
    if z_number(0.8, None)["qualified"] is not None:
        fails.append("7.5 a missing reliability may not silently become one")
    eq("7.5 maximum reliability approaches the value-only limit",
       z_number(0.8, 1.0)["qualified"], 0.8)
    if not z_number(0.8, 0.5)["qualified"] < z_number(0.8, 0.9)["qualified"]:
        fails.append("7.5 lowering reliability with the value fixed must move the qualified "
                     "result in the declared direction")

    # 7.6 -- PLTS admissibility and the ordered score.
    order = ["Red", "Amber", "Green"]
    if not plts_admissible({"Green": 0.6, "Amber": 0.3}):
        fails.append("7.6 a set summing below one is admissible")
    if plts_admissible({"Green": 0.9, "Amber": 0.5}):
        fails.append("7.6 probabilities summing above one are inadmissible")
    if plts_admissible({"Green": -0.1}):
        fails.append("7.6 a negative probability is inadmissible")
    eq("7.6 a degenerate one-term set scores that term's index",
       plts_score({"Green": 1.0}, order), 2.0)
    eq("7.6 permutation of the representation does not change the score",
       plts_score({"Amber": 0.5, "Green": 0.5}, order),
       plts_score({"Green": 0.5, "Amber": 0.5}, order))

    # 7.7 -- the contradiction-degree endpoints.
    eq("7.7 at zero contradiction the operator is the t-norm",
       plithogenic_aggregate(0.6, 0.5, 0.0), 0.30)
    eq("7.7 at full contradiction it is the t-conorm",
       plithogenic_aggregate(0.6, 0.5, 1.0), 0.80)
    if not (plithogenic_aggregate(0.6, 0.5, 0.0)
            < plithogenic_aggregate(0.6, 0.5, 0.5)
            < plithogenic_aggregate(0.6, 0.5, 1.0)):
        fails.append("7.7 the operator must interpolate monotonically between its endpoints")

    # 7.8 -- one fully activated rule reproduces its consequent exactly.
    one = brb_aggregate([{"activation": 1.0, "weight": 1.0,
                          "belief": {"Green": 0.7, "Amber": 0.2, "Red": 0.1}}])
    eq("7.8 one activated rule reproduces its Green belief", one["belief"]["Green"], 0.7)
    eq("7.8 and its Amber belief", one["belief"]["Amber"], 0.2)
    eq("7.8 and its Red belief", one["belief"]["Red"], 0.1)
    if brb_aggregate([{"activation": 0.0, "weight": 1.0, "belief": {"Green": 1.0}}])["belief"]:
        fails.append("7.8 a rule base with no activated rule has concluded nothing")
    if not belief_distribution_admissible({"Green": 0.7, "Amber": 0.2, "Red": 0.1}):
        fails.append("7.8 a distribution summing to one is admissible")
    if belief_distribution_admissible({"Green": 0.7, "Amber": 0.7}):
        fails.append("7.8 belief degrees summing above one are inadmissible")

    # 7.9 -- the Born rule on the specification's superposition.
    inv = 1.0 / math.sqrt(2)
    eq("7.9 P(0) on the equal superposition", born_rule([inv, inv], 0), 0.5)
    eq("7.9 P(1) on the same state", born_rule([inv, inv], 1), 0.5)
    try:
        born_rule([1.0, 1.0], 0)
        fails.append("7.9 an unnormalised state is not a state and must be refused")
    except ValueError:
        pass
    # Noncommuting projectors give order-dependent results, which is what an order effect IS.
    p0 = [[1.0, 0.0], [0.0, 0.0]]
    half = [[0.5, 0.5], [0.5, 0.5]]
    ab = sequential_measurement([inv, inv], p0, half)
    ba = sequential_measurement([inv, inv], half, p0)
    if abs(ab - ba) < 1e-12:
        fails.append("7.9 noncommuting projectors must give an order-dependent probability")

    # 7.10 -- the specification's worked boundary and its inadmissible pair.
    if not pythagorean_admissible(0.6, 0.8):
        fails.append("7.10 (.6,.8) lies exactly on the boundary and is admissible")
    eq("7.10 hesitancy on the boundary", pythagorean_hesitancy(0.6, 0.8), 0.0)
    if pythagorean_admissible(0.8, 0.8):
        fails.append("7.10 (.8,.8) sums to 1.28 and is inadmissible")

    # 7.11 -- the specification's worked refusal degree.
    if not picture_admissible(0.4, 0.2, 0.3):
        fails.append("7.11 (.4,.2,.3) is admissible")
    eq("7.11 refusal degree", picture_refusal(0.4, 0.2, 0.3), 0.1)
    if picture_admissible(0.5, 0.4, 0.4):
        fails.append("7.11 a sum above one is inadmissible")

    # 7.12 -- the specification's hesitant element under the mean score.
    eq("7.12 mean score of {.2,.5,.7}", hesitant_score_mean([0.2, 0.5, 0.7]), 1.4 / 3)
    eq("7.12 a single value scores itself", hesitant_score_mean([0.5]), 0.5)
    eq("7.12 the mean is permutation invariant",
       hesitant_score_mean([0.7, 0.2, 0.5]), hesitant_score_mean([0.2, 0.5, 0.7]))
    try:
        hesitant_score_mean([])
        fails.append("7.12 an empty hesitant element has no score")
    except ValueError:
        pass

    # 7.13 -- the footprint of uncertainty.
    if not type2_footprint_admissible(0.3, 0.7) or type2_footprint_admissible(0.7, 0.3):
        fails.append("7.13 the lower membership function may not exceed the upper")

    # 7.14 -- maximum entropy under normalisation alone.
    p = max_entropy_distribution(2)
    if p != [0.5, 0.5]:
        fails.append(f"7.14 the maximum entropy distribution over two outcomes: got {p}")
    eq("7.14 its entropy is the natural log of two", shannon_entropy_nats(p), math.log(2))
    if not shannon_entropy_nats([0.5, 0.5]) > shannon_entropy_nats([0.9, 0.1]):
        fails.append("7.14 the uniform distribution must have the greatest entropy")

    # 7.15 -- the specification's worked possibility and necessity.
    pi = {"a": 1.0, "b": 0.4}
    eq("7.15 possibility of {b}", possibility_of(pi, {"b"}), 0.4)
    eq("7.15 necessity of {a}", necessity_of(pi, {"a"}), 0.6)
    eq("7.15 maxitivity",
       possibility_of(pi, {"a", "b"}), max(possibility_of(pi, {"a"}), possibility_of(pi, {"b"})))
    if abs(max(pi.values()) - 1.0) > 1e-12:
        fails.append("7.15 a normalised possibility distribution has a supremum of one")

    # 7.16 and 7.17 -- the specification's worked admissible and inadmissible triples.
    if not spherical_admissible(0.6, 0.6, 0.5):
        fails.append("7.16 (.6,.6,.5) sums to .97 and is admissible")
    if spherical_admissible(0.8, 0.8, 0.1):
        fails.append("7.16 (.8,.8,.1) sums to 1.29 and is inadmissible")
    if not fermatean_admissible(0.8, 0.7):
        fails.append("7.17 (.8,.7) cubes to .855 and is admissible")
    if fermatean_admissible(0.9, 0.9):
        fails.append("7.17 (.9,.9) cubes to 1.458 and is inadmissible")

    # 7.18 -- MARCOS over a real matrix, with a dominated alternative ranking last.
    mat = {"A": {"c1": 0.9, "c2": 0.9}, "B": {"c1": 0.6, "c2": 0.6},
           "C": {"c1": 0.3, "c2": 0.3}}
    w = {"c1": 0.5, "c2": 0.5}
    ben = {"c1": True, "c2": True}
    m = marcos(mat, w, ben)
    if m["ranking"] != ["A", "B", "C"]:
        fails.append(f"7.18 a dominating alternative must rank first: got {m['ranking']}")
    if m["utility"]["A"] <= m["utility"]["C"]:
        fails.append("7.18 the dominated alternative must score lowest")
    ident = marcos({"A": {"c1": 0.5}, "B": {"c1": 0.5}}, {"c1": 1.0}, {"c1": True})
    if abs(ident["utility"]["A"] - ident["utility"]["B"]) > 1e-9:
        fails.append("7.18 identical alternatives must score identically")
    try:
        marcos({"A": {"c1": 1.0}}, {"c1": 1.0}, {"c1": True})
        fails.append("7.18 one alternative is not a ranking and must be refused")
    except ValueError:
        pass
    # Benefit and cost reversal must reverse the ranking on a single-criterion matrix.
    rev = marcos(mat, w, {"c1": False, "c2": False})
    if rev["ranking"][0] != "C":
        fails.append(f"7.18 reversing benefit to cost must reverse the ranking: {rev['ranking']}")

    # 7.19 -- CRITIC weights and TOPSIS closeness over the same matrix.
    cw = critic_weights(mat)
    eq("7.19 the CRITIC weights sum to one", sum(cw.values()), 1.0)
    try:
        critic_weights({"A": {"c1": 1.0, "c2": 1.0}})
        fails.append("7.19 CRITIC derives contrast across alternatives and one row has none")
    except ValueError:
        pass
    t = topsis(mat, w, ben)
    if t["ranking"] != ["A", "B", "C"]:
        fails.append(f"7.19 TOPSIS ranking: got {t['ranking']}")
    if not 0.0 <= t["closeness"]["B"] <= 1.0:
        fails.append("7.19 closeness lies in nought to one")
    if abs(t["closeness"]["A"] - 1.0) > 1e-9:
        fails.append("7.19 the alternative that IS the ideal has closeness one")

    # 7.20 -- the Cartesian product must be explicit and a missing tuple must abstain.
    av = {"cost": ["good", "poor"], "schedule": ["good", "poor"]}
    tuples = hypersoft_tuples(av)
    if len(tuples) != 4:
        fails.append(f"7.20 a two by two product has four tuples, got {len(tuples)}")
    full = {t: 0.5 for t in tuples}
    if not hypersoft_complete(full, av)["complete"]:
        fails.append("7.20 a complete mapping is complete")
    partial = dict(full)
    del partial[tuples[0]]
    inc = hypersoft_complete(partial, av)
    if inc["complete"] or len(inc["missing"]) != 1:
        fails.append("7.20 deleting one tuple must be reported as explicit incompleteness")

    return fails


_FAILS = self_test()
assert not _FAILS, "Category 7 oracle does not reproduce the specification: " + "; ".join(_FAILS)
