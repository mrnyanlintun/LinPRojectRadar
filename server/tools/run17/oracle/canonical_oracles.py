"""
Run 17 independent oracles.

EVERY FUNCTION HERE IS WRITTEN FROM THE FORMAL EQUATIONS IN THE OWNER SPECIFICATION, not from
the production source. Owner specification section 24 is explicit that a second function copied
from the first is not independent, so the rule this file follows is: open the specification's
equation, implement it, and never open the production module while doing so. Where the
specification supplies a worked numeric answer, that answer is asserted here as a self-test so
the oracle itself is proved before it is used to judge anything.

TEST-ONLY. Nothing in server/app imports this file, and it imports nothing from server/app.
"""

from __future__ import annotations

import math

# ---------------------------------------------------------------- Category 1


def normal_normal_posterior(mu0: float, tau0_sq: float, y: float,
                            sigma_sq: float) -> tuple[float, float]:
    """
    Owner spec 1.3. tau1^2 = 1/(1/tau0^2 + 1/sigma^2);
                    mu1 = tau1^2 * (mu0/tau0^2 + y/sigma^2).
    Returns (posterior_mean, posterior_variance).
    """
    tau1_sq = 1.0 / (1.0 / tau0_sq + 1.0 / sigma_sq)
    mu1 = tau1_sq * (mu0 / tau0_sq + y / sigma_sq)
    return mu1, tau1_sq


def kalman_scalar_step(x_prev: float, p_prev: float, q: float, r: float,
                       z: float) -> tuple[float, float, float]:
    """
    Owner spec 1.4, scalar random-walk. x_pred = x_prev; P_pred = P_prev + Q;
    K = P_pred/(P_pred+R); x_post = x_pred + K(z - x_pred); P_post = (1-K)P_pred.
    Returns (x_post, p_post, k).
    """
    p_pred = p_prev + q
    k = p_pred / (p_pred + r)
    x_post = x_prev + k * (z - x_prev)
    return x_post, (1.0 - k) * p_pred, k


def kalman_scalar_filter(history: list[float], q: float, r: float,
                         p0: float = 1.0) -> float:
    """The recursion run over a series, initialised at the first observation."""
    x, p = history[0], p0
    for z in history[1:]:
        x, p, _ = kalman_scalar_step(x, p, q, r, z)
    return x


def earned_schedule(pv_cumulative: list[float], ev: float, at: float) -> dict[str, float]:
    """
    Owner spec 1.6. Find integer C with PV_C <= EV < PV_(C+1); ES = C + (EV-PV_C)/(PV_(C+1)-PV_C);
    SV(t) = ES - AT; SPI(t) = ES/AT.

    pv_cumulative is indexed by time period, pv_cumulative[t] being cumulative PV at time t.
    """
    c = None
    for t in range(len(pv_cumulative) - 1):
        if pv_cumulative[t] <= ev < pv_cumulative[t + 1]:
            c = t
            break
    if c is None:
        raise ValueError("earned value does not fall inside the supplied planned-value curve")
    span = pv_cumulative[c + 1] - pv_cumulative[c]
    es = c + (ev - pv_cumulative[c]) / span
    return {"C": float(c), "ES": es, "SV_t": es - at, "SPI_t": es / at}


def tcpi(bac: float, ev: float, ac: float, eac: float | None = None) -> float:
    """Owner spec 1.7. TCPI_BAC = (BAC-EV)/(BAC-AC); TCPI_EAC = (BAC-EV)/(EAC-AC)."""
    denominator = (bac - ac) if eac is None else (eac - ac)
    return (bac - ev) / denominator


def vac(bac: float, eac: float) -> float:
    """Owner spec 1.8. VAC = BAC - EAC."""
    return bac - eac


def cpi_shrinkage(cpi_project: float, mu_reference: float, w: float) -> float:
    """Owner spec 1.10. CPI_shrunk = w*CPI_project + (1-w)*mu_reference."""
    return w * cpi_project + (1.0 - w) * mu_reference


def beta_pert_mean(a: float, m: float, b: float, lam: float = 4.0) -> float:
    """Owner spec 1.1. Beta-PERT mean = (a + lam*m + b)/(lam + 2)."""
    return (a + lam * m + b) / (lam + 2.0)


def cusum_two_sided(xs: list[float], mu0: float, sigma: float,
                    k: float, h: float) -> dict[str, object]:
    """
    Owner spec 1.2, tabular standardised CUSUM.
    Cplus_t = max(0, Cplus_(t-1) + z_t - k); Cminus_t = max(0, Cminus_(t-1) - z_t - k);
    z_t = (x_t - mu0)/sigma. Returns the full trajectories plus the first index at which
    either statistic strictly exceeds h.
    """
    cp, cm = 0.0, 0.0
    cps, cms = [], []
    signal_at = None
    for i, x in enumerate(xs):
        z = (x - mu0) / sigma
        cp = max(0.0, cp + z - k)
        cm = max(0.0, cm - z - k)
        cps.append(cp)
        cms.append(cm)
        if signal_at is None and (cp > h or cm > h):
            signal_at = i
    return {"c_plus": cps, "c_minus": cms, "signal_index": signal_at}


# ---------------------------------------------------------------- Category 6


#: Owner spec 15: one ordered severity vocabulary, Green < Yellow < Amber < Red.
SEVERITY_ORDER = ("Green", "Yellow", "Amber", "Red")
SEVERITY_RANK = {s: i for i, s in enumerate(SEVERITY_ORDER)}


def conservative_dominance(states: list[str]) -> str:
    """Owner spec 6.1. Result = worst credible qualified signal."""
    qualified = [s for s in states if s in SEVERITY_RANK]
    if not qualified:
        raise ValueError("no qualified signal")
    return max(qualified, key=lambda s: SEVERITY_RANK[s])


def weighted_severity_score(states: list[str], weights: list[float]) -> float:
    """Owner spec 6.2. Score = sum(w_i * s_i) with s_i the ordinal severity score 0..3."""
    return sum(w * SEVERITY_RANK[s] for s, w in zip(states, weights))


def majority_state(states: list[str]) -> str:
    """
    Owner spec 6.3. Count qualified governed states; the most frequent wins. Tie policy made
    explicit here and it is the conservative one: the more severe state takes the tie.
    """
    qualified = [s for s in states if s in SEVERITY_RANK]
    if not qualified:
        raise ValueError("no qualified signal")
    best = None
    for s in SEVERITY_ORDER:
        n = qualified.count(s)
        if best is None or n > best[1] or (n == best[1] and SEVERITY_RANK[s] > SEVERITY_RANK[best[0]]):
            best = (s, n)
    return best[0]


def worst_n_of_m(states: list[str], n: int) -> str:
    """
    Owner spec 6.4, under the second-stage operation the specification names as the collapsing
    case: select the worst N of M, then take their maximum. Returned so the test can prove the
    collapse to conservative dominance rather than assert it.
    """
    qualified = sorted((s for s in states if s in SEVERITY_RANK),
                       key=lambda s: SEVERITY_RANK[s], reverse=True)
    if not qualified:
        raise ValueError("no qualified signal")
    return max(qualified[:n], key=lambda s: SEVERITY_RANK[s])


# ---------------------------------------------------------------- Category 7


def dempster_combine(m1: dict[frozenset, float],
                     m2: dict[frozenset, float]) -> tuple[dict[frozenset, float], float]:
    """
    Owner spec 7.1, over explicit focal SETS rather than labels, which is the point: Theta
    intersects every focal element instead of conflicting with it.

    K = sum over disjoint pairs; m12(A) = [sum_(B cap C = A) m1(B)m2(C)] / (1-K).
    Raises on total conflict rather than fabricating a distribution.
    """
    raw: dict[frozenset, float] = {}
    k = 0.0
    for b, mb in m1.items():
        for c, mc in m2.items():
            inter = b & c
            if not inter:
                k += mb * mc
            else:
                raw[inter] = raw.get(inter, 0.0) + mb * mc
    if k >= 1.0:
        raise ZeroDivisionError("total conflict: Dempster's rule is undefined")
    return {a: v / (1.0 - k) for a, v in raw.items()}, k


def belief(m: dict[frozenset, float], a: frozenset) -> float:
    """Bel(A) = sum over B subset of A."""
    return sum(v for b, v in m.items() if b <= a)


def plausibility(m: dict[frozenset, float], a: frozenset) -> float:
    """Pl(A) = sum over B intersecting A."""
    return sum(v for b, v in m.items() if b & a)


def shafer_discount(m: dict[frozenset, float], alpha: float,
                    theta: frozenset) -> dict[frozenset, float]:
    """Reliability discount: m'(A) = alpha*m(A) for A != Theta; m'(Theta) = 1-alpha+alpha*m(Theta)."""
    out = {a: alpha * v for a, v in m.items() if a != theta}
    out[theta] = 1.0 - alpha + alpha * m.get(theta, 0.0)
    return out


# ---------------------------------------------------------------- Portfolio Health


def harmonic_exact(i: int) -> float:
    """Exact harmonic number, as an independent check on the paper's ln+gamma estimate."""
    return sum(1.0 / j for j in range(1, i + 1))


def c_factor(n: int) -> float:
    """Owner spec PH.1. c(n) = 2*H_(n-1) - 2*(n-1)/n, using the EXACT harmonic number."""
    if n <= 1:
        return 0.0
    if n == 2:
        return 1.0
    return 2.0 * harmonic_exact(n - 1) - 2.0 * (n - 1) / n


def isolation_score(mean_path: float, psi: int) -> float:
    """Owner spec PH.1. s(x,n) = 2^(-E[h(x)]/c(psi))."""
    return 2.0 ** (-mean_path / c_factor(psi))


def ols_slope(ts: list[float], xs: list[float]) -> float:
    """Owner spec PH.3. Ordinary least squares slope of x on t."""
    n = len(ts)
    tbar = sum(ts) / n
    xbar = sum(xs) / n
    num = sum((t - tbar) * (x - xbar) for t, x in zip(ts, xs))
    den = sum((t - tbar) ** 2 for t in ts)
    return num / den


def euclidean(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


# ---------------------------------------------------------------- oracle self-tests


def self_test() -> list[str]:
    """
    Prove each oracle against the worked answer the owner specification supplies. Returns the
    list of failures; empty is the proof. Run before any oracle judges production.
    """
    fails = []

    def near(label, got, want, tol=1e-9):
        if abs(got - want) > tol:
            fails.append(f"{label}: got {got!r}, specification says {want!r}")

    # 1.3 spec oracle: mu0=100, tau0^2=100, y=120, sigma^2=100 -> mean 110, variance 50.
    m, v = normal_normal_posterior(100, 100, 120, 100)
    near("1.3 posterior mean", m, 110.0)
    near("1.3 posterior variance", v, 50.0)

    # 1.4 spec oracle: x0=1, P0=1, Q=0, R=1, z=2 -> K=.5, x=1.5, P=.5.
    x, p, k = kalman_scalar_step(1.0, 1.0, 0.0, 1.0, 2.0)
    near("1.4 K", k, 0.5)
    near("1.4 x_post", x, 1.5)
    near("1.4 P_post", p, 0.5)

    # 1.6 spec oracle: PV 0,20,40,60; EV=50; AT=3 -> C=2, ES=2.5, SV(t)=-0.5, SPI(t)=0.8333...
    es = earned_schedule([0, 20, 40, 60], 50, 3)
    near("1.6 C", es["C"], 2.0)
    near("1.6 ES", es["ES"], 2.5)
    near("1.6 SV(t)", es["SV_t"], -0.5)
    near("1.6 SPI(t)", es["SPI_t"], 5.0 / 6.0)

    # 1.7 spec oracle: BAC=100, EV=60, AC=70 -> 4/3; with EAC=120 -> 0.8.
    near("1.7 TCPI_BAC", tcpi(100, 60, 70), 4.0 / 3.0)
    near("1.7 TCPI_EAC", tcpi(100, 60, 70, eac=120), 0.8)

    # 1.8 spec oracle: BAC=100, EAC=120 -> -20.
    near("1.8 VAC", vac(100, 120), -20.0)

    # 1.10 spec oracle: .80, 1.00, w=.60 -> .88.
    near("1.10 shrinkage", cpi_shrinkage(0.80, 1.00, 0.60), 0.88)

    # 1.1 spec oracle: a=80, m=100, b=140, lambda=4 -> 103.333...
    near("1.1 Beta-PERT mean", beta_pert_mean(80, 100, 140), 620.0 / 6.0)

    # 1.2 spec oracle: mu0=0, sigma=1, x=1 repeatedly, k=.5 -> Cplus rises .5 each observation;
    # at 10 observations Cplus=5; at 11, 5.5.
    c = cusum_two_sided([1.0] * 11, 0.0, 1.0, 0.5, 5.0)
    near("1.2 Cplus at 10 observations", c["c_plus"][9], 5.0)
    near("1.2 Cplus at 11 observations", c["c_plus"][10], 5.5)
    if c["signal_index"] != 10:
        fails.append(f"1.2 strict-exceedance signal index: got {c['signal_index']}, expected 10")

    # 6.1 spec oracle: Green,Yellow,Amber -> Amber; Green,Red,Red -> Red.
    if conservative_dominance(["Green", "Yellow", "Amber"]) != "Amber":
        fails.append("6.1 conservative dominance oracle")
    if conservative_dominance(["Green", "Red", "Red"]) != "Red":
        fails.append("6.1 conservative dominance oracle (Red)")

    # 6.2 spec oracle: severities 0,1,2,3; weights .5,.3,.2; Green,Amber,Red -> 1.2.
    near("6.2 weighted score", weighted_severity_score(
        ["Green", "Amber", "Red"], [0.5, 0.3, 0.2]), 1.2, tol=1e-12)

    # 6.3 spec oracle: Green,Red,Red -> Red.
    if majority_state(["Green", "Red", "Red"]) != "Red":
        fails.append("6.3 majority oracle")

    # 7.1 spec oracle: Theta={G,R}; m1({G})=.6, m1(Theta)=.4; m2({G})=.5, m2(Theta)=.5;
    # K=0; combined m({G})=.8, m(Theta)=.2.
    G, R = "G", "R"
    theta = frozenset({G, R})
    m1 = {frozenset({G}): 0.6, theta: 0.4}
    m2 = {frozenset({G}): 0.5, theta: 0.5}
    comb, k_conf = dempster_combine(m1, m2)
    near("7.1 K", k_conf, 0.0)
    near("7.1 m({G})", comb[frozenset({G})], 0.8)
    near("7.1 m(Theta)", comb[theta], 0.2)
    # Total conflict must raise, not fabricate.
    try:
        dempster_combine({frozenset({G}): 1.0}, {frozenset({R}): 1.0})
        fails.append("7.1 total conflict did not raise")
    except ZeroDivisionError:
        pass

    # PH.1 spec: for n>2, c(n)=2H_(n-1) - 2(n-1)/n. c(2) = 1 by the paper.
    near("PH.1 c(2)", c_factor(2), 1.0)
    near("PH.1 c(3)", c_factor(3), 2.0 * 1.5 - 2.0 * 2.0 / 3.0)
    # s -> 0.5 when E[h] = c(psi).
    near("PH.1 score at E[h]=c(psi)", isolation_score(c_factor(10), 10), 0.5)

    # PH.3 spec oracle: t=[0,1,2], x=[1.0,.9,.8] -> slope -.1 per period.
    near("PH.3 OLS slope", ols_slope([0, 1, 2], [1.0, 0.9, 0.8]), -0.1, tol=1e-12)

    return fails


if __name__ == "__main__":
    problems = self_test()
    for p in problems:
        print("ORACLE SELF-TEST FAILURE: " + p)
    print(f"oracle self-test: {len(problems)} failures")
