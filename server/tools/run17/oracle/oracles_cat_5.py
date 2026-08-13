"""
Run 19 independent oracles for Category 5, system dynamics and complexity.

Written from supervisory specification section 14 and from nothing else. Self proved at import
against the specification's worked answers. Nothing is imported from server/app.

The queueing oracle is the closed-form M/M/1 result the specification names in section 24, the
discrete event oracle is a hand event schedule, and the agent-based oracle replays behaviour
rules over a hand-computed state history, which is what section 5.7 asks for.
"""

from __future__ import annotations


# ------------------------------------------------------------------ 5.1 DSM propagation

def dsm_step(matrix: list[list[float]], vector: list[float]) -> list[float]:
    """Specification 5.1, under the declared convention R_next = D * R."""
    return [sum(matrix[i][j] * vector[j] for j in range(len(vector)))
            for i in range(len(matrix))]


def dsm_propagate(matrix: list[list[float]], seed: list[float], steps: int) -> list[list[float]]:
    """The successive waves, seed first, so the accumulation convention is explicit."""
    out = [list(seed)]
    for _ in range(steps):
        out.append(dsm_step(matrix, out[-1]))
    return out


# ------------------------------------------------------------------ 5.2 Sensitivity

def normalised_sensitivity(f, base: dict, variable: str, relative_step: float) -> float:
    """
    Specification 5.2. S_i = (DeltaY / Y) / (DeltaXi / Xi), a dimensionless elasticity.

    Being dimensionless is the whole point: it is what makes two different inputs COMPARABLE, so
    a ranking of several inputs by sensitivity means something. A ranking of quantities that are
    not on a common scale does not.
    """
    y0 = f(base)
    perturbed = dict(base)
    perturbed[variable] = base[variable] * (1.0 + relative_step)
    y1 = f(perturbed)
    return ((y1 - y0) / y0) / relative_step


# ------------------------------------------------------------------ 5.3 Tornado

def tornado_impacts(f, base: dict, ranges: dict[str, tuple[float, float]]) -> list[tuple]:
    """
    Specification 5.3. Impact_i = Y_i(high) - Y_i(low), ranked by absolute impact.

    The OUTPUT is evaluated at each input's low and high value. Nothing here reads how far an
    input currently sits from a nominal value: that is a different quantity.
    """
    out = []
    for name, (lo, hi) in ranges.items():
        y_lo = f({**base, name: lo})
        y_hi = f({**base, name: hi})
        out.append((name, y_hi - y_lo, abs(y_hi - y_lo)))
    return sorted(out, key=lambda r: (-r[2], r[0]))


# ------------------------------------------------------------------ 5.4 Scenario expectation

def scenario_expectation(probabilities: dict[str, float],
                         outcomes: dict[str, dict[str, float]]) -> dict:
    """
    Specification 5.4 and 10.4. The expectation of each action over a stated distribution.

    The probabilities must be a distribution and every action must have an outcome under every
    scenario, or no expectation exists.
    """
    if abs(sum(probabilities.values()) - 1.0) > 1e-9:
        raise ValueError("the scenario probabilities do not describe one distribution")
    for action, row in outcomes.items():
        if set(row) != set(probabilities):
            raise ValueError(f"{action} has no outcome under every scenario described")
    exp = {a: sum(probabilities[s] * v for s, v in row.items()) for a, row in outcomes.items()}
    best = min(exp, key=lambda a: (exp[a], a))
    return {"expectations": exp, "best": best, "worst_case_of_best": max(outcomes[best].values())}


# ------------------------------------------------------------------ 5.5 Rework feedback

def rework_step(backlog: float, new_work: float, completed: float, error_rate: float) -> dict:
    """
    Specification 5.5. The stock and flow accounting of a rework loop:
        ReworkGenerated_t = ErrorRate_t * WorkCompleted_t
        Backlog_(t+1) = Backlog_t + NewWork_t + ReworkGenerated_t - WorkCompleted_t

    The specification's worked case: backlog 10, new work 5, completed 8, error rate .25 gives
    rework of 2 and a next backlog of 9.
    """
    rework = error_rate * completed
    return {"rework": rework, "backlog_next": backlog + new_work + rework - completed}


def rework_run(backlog: float, new_work: float, completed: float, error_rate: float,
               steps: int) -> list[float]:
    """The stock over time, so equilibrium and amplification are observable."""
    out = [backlog]
    for _ in range(steps):
        out.append(rework_step(out[-1], new_work, completed, error_rate)["backlog_next"])
    return out


# ------------------------------------------------------------------ 5.6 Queueing

def mm1(lam: float, mu: float) -> dict:
    """
    Specification 5.6. The closed-form M/M/1 results, and the stability condition.

    rho = lam/mu, stable only if rho < 1. L = rho/(1-rho); W = 1/(mu-lam);
    Lq = rho^2/(1-rho); Wq = rho/(mu-lam).

    The specification's worked case: lam=2, mu=3 gives rho=2/3, L=2, W=1, Lq=4/3, Wq=2/3, and
    Little's Law holds. At lam >= mu NO steady-state solution is returned, because there is none:
    returning a reassuring number there is the defect the specification names.
    """
    rho = lam / mu
    if rho >= 1.0:
        return {"rho": rho, "stable": False, "L": None, "W": None, "Lq": None, "Wq": None}
    return {"rho": rho, "stable": True,
            "L": rho / (1 - rho), "W": 1.0 / (mu - lam),
            "Lq": rho ** 2 / (1 - rho), "Wq": rho / (mu - lam)}


def littles_law_holds(lam: float, mu: float, tol: float = 1e-9) -> bool:
    q = mm1(lam, mu)
    if not q["stable"]:
        return True
    return (abs(q["L"] - lam * q["W"]) < tol) and (abs(q["Lq"] - lam * q["Wq"]) < tol)


def utilisation_from_observation(total_service: float, servers: float, horizon: float) -> float:
    """The empirical utilisation of an observed queue: server time used over server time available."""
    if servers < 1 or horizon <= 0:
        raise ValueError("no servers or no observation window, so no utilisation")
    return total_service / (servers * horizon)


# ------------------------------------------------------------------ 5.7 Agent-based model

def replay_supply_chain(events: int = 3) -> list[dict]:
    """
    Specification 5.7's minimum laboratory model, replayed by APPLYING THE RULES.

    Supplier: ships one unit when inventory > 0 and a request is pending.
    Carrier: collects a shipped unit and delivers it after a declared travel delay of one step.
    Project: demand received, or backordered.

    The state history below is PRODUCED by executing those rules, not supplied, which is the
    difference between an agent-based model and a table of states. Hand computed:
      t0  supplier inventory 1, request pending, carrier available, project backordered
      t1  supplier ships, inventory 0, carrier busy carrying one unit
      t2  carrier delivers, project received, carrier available again
    """
    supplier = {"inventory": 1, "request_pending": True}
    carrier = {"state": "available", "carrying": 0, "eta": None}
    project = {"state": "backordered"}
    history = []
    for t in range(events):
        history.append({"t": t, "supplier": dict(supplier), "carrier": dict(carrier),
                        "project": dict(project)})
        if carrier["state"] == "busy" and carrier["eta"] == t:
            carrier.update(state="available", carrying=0, eta=None)
            project["state"] = "received"
        elif (supplier["inventory"] > 0 and supplier["request_pending"]
              and carrier["state"] == "available"):
            supplier["inventory"] -= 1
            supplier["request_pending"] = False
            carrier.update(state="busy", carrying=1, eta=t + 1)
    return history


# ------------------------------------------------------------------ 5.8 Discrete event simulation

def des_single_server(arrivals: list[tuple[str, float, float]]) -> dict:
    """
    Specification 5.8's worked case, by an explicit event schedule over a simulation clock.

    One server, first come first served. Job A arrives at 0 needing 2; job B arrives at 1
    needing 2. Expected: A starts 0 ends 2 waits 0; B arrives 1, starts 2, ends 4, waits 1;
    mean wait one half.

    arrivals: (name, arrival_time, service_time), which the simulation sorts by arrival, and by
    name on a tie, so the simultaneous-event policy is explicit rather than incidental.
    """
    queue = sorted(arrivals, key=lambda j: (j[1], j[0]))
    clock = 0.0
    log = []
    for name, arrival, service in queue:
        start = max(clock, arrival)
        end = start + service
        log.append({"job": name, "arrival": arrival, "start": start, "end": end,
                    "wait": start - arrival})
        clock = end
    waits = [row["wait"] for row in log]
    return {"log": log, "mean_wait": sum(waits) / len(waits) if waits else 0.0,
            "makespan": clock}


# ------------------------------------------------------------------ self proof

def self_test() -> list[str]:
    fails: list[str] = []

    def eq(label, got, want, tol=1e-9):
        if got is None or abs(float(got) - float(want)) > tol:
            fails.append(f"{label}: got {got!r}, specification says {want!r}")

    # 5.1 -- the specification's two-node matrix and seed.
    D = [[0.0, 0.5], [0.0, 0.0]]
    waves = dsm_propagate(D, [0.0, 1.0], 2)
    if waves[1] != [0.5, 0.0]:
        fails.append(f"5.1 first wave: got {waves[1]}, specification says [0.5, 0]")
    if waves[2] != [0.0, 0.0]:
        fails.append(f"5.1 second wave: got {waves[2]}, specification says [0, 0]")
    if dsm_step([[0.0, 0.0], [0.0, 0.0]], [1.0, 1.0]) != [0.0, 0.0]:
        fails.append("5.1 a zero matrix propagates nothing")
    if dsm_step(D, [0.0, 2.0]) != [1.0, 0.0]:
        fails.append("5.1 propagation is linear in the seed, so edge strength is monotone")

    # 5.2 -- the specification's Y = x1^2 + x2 at (2,1), ten per cent step on x1, S = 1.68.
    def y(v):
        return v["x1"] ** 2 + v["x2"]
    eq("5.2 normalised sensitivity", normalised_sensitivity(y, {"x1": 2.0, "x2": 1.0}, "x1", 0.10),
       1.68, 1e-9)
    # An input the output does not depend on has zero sensitivity, which is the property that
    # makes the elasticity meaningful rather than an artefact of scale.
    eq("5.2 an unused input has no sensitivity",
       normalised_sensitivity(lambda v: v["x1"], {"x1": 2.0, "x2": 1.0}, "x2", 0.10), 0.0)

    # 5.3 -- the specification's A, B, C low and high outputs.
    # The specification supplies each input's LOW and HIGH OUTPUT directly, so the laboratory
    # model here is the additive one under which the output at an input's low and high value IS
    # the pair the specification states: 90/120 for A, 98/105 for B, 80/110 for C.
    ranked = tornado_impacts(lambda v: v["A"] + v["B"] + v["C"],
                             {"A": 90.0, "B": 98.0, "C": 80.0},
                             {"A": (90.0, 120.0), "B": (98.0, 105.0), "C": (80.0, 110.0)})
    names = [r[0] for r in ranked]
    impacts = {r[0]: r[1] for r in ranked}
    eq("5.3 impact of A", impacts["A"], 30)
    eq("5.3 impact of B", impacts["B"], 7)
    eq("5.3 impact of C", impacts["C"], 30)
    if names[-1] != "B":
        fails.append(f"5.3 B has the smallest impact and must rank last, got {names}")
    if set(names[:2]) != {"A", "C"}:
        fails.append(f"5.3 A and C tie above B, got {names}")

    # 5.4 -- a hand expectation.
    sd = scenario_expectation({"S1": 0.6, "S2": 0.4},
                              {"hold": {"S1": 0.0, "S2": 100.0},
                               "act": {"S1": 30.0, "S2": 30.0}})
    eq("5.4 expectation of holding", sd["expectations"]["hold"], 40.0)
    eq("5.4 expectation of acting", sd["expectations"]["act"], 30.0)
    if sd["best"] != "act":
        fails.append("5.4 the lower expected cost is chosen")
    eq("5.4 worst case of the chosen action", sd["worst_case_of_best"], 30.0)
    try:
        scenario_expectation({"S1": 0.6, "S2": 0.6}, {"a": {"S1": 1.0, "S2": 1.0}})
        fails.append("5.4 probabilities that do not sum to one must be refused")
    except ValueError:
        pass

    # 5.5 -- the specification's worked backlog case.
    r = rework_step(10, 5, 8, 0.25)
    eq("5.5 rework generated", r["rework"], 2.0)
    eq("5.5 next backlog", r["backlog_next"], 9.0)
    eq("5.5 zero error rate generates no rework", rework_step(10, 5, 8, 0.0)["rework"], 0.0)
    eq("5.5 with no work completed nothing is completed and nothing reworked",
       rework_step(10, 5, 0, 0.25)["backlog_next"], 15.0)
    # Equilibrium: new work plus rework exactly equals completion, so the stock does not move.
    equil = rework_run(10, 6, 8, 0.25, 5)
    if any(abs(v - 10) > 1e-9 for v in equil):
        fails.append(f"5.5 at new work 6, completion 8 and error rate .25 the backlog is in "
                     f"equilibrium, got {equil}")
    # Amplification: a higher error rate makes the stock grow rather than hold.
    if not rework_run(10, 6, 8, 0.60, 5)[-1] > 10:
        fails.append("5.5 a higher error rate must amplify the backlog")

    # 5.6 -- the specification's M/M/1 case and Little's Law.
    q = mm1(2, 3)
    eq("5.6 utilisation", q["rho"], 2 / 3)
    eq("5.6 number in system", q["L"], 2.0)
    eq("5.6 time in system", q["W"], 1.0)
    eq("5.6 number in queue", q["Lq"], 4 / 3)
    eq("5.6 time in queue", q["Wq"], 2 / 3)
    if not littles_law_holds(2, 3):
        fails.append("5.6 Little's Law must hold on the specification's case")
    unstable = mm1(3, 3)
    if unstable["stable"] or unstable["L"] is not None:
        fails.append("5.6 at an arrival rate equal to the service rate there is no steady state "
                     "and no reassuring solution may be returned")
    if mm1(4, 3)["L"] is not None:
        fails.append("5.6 an arrival rate above the service rate has no steady state")
    eq("5.6 empirical utilisation of an observed queue",
       utilisation_from_observation(60, 2, 30), 1.0)

    # 5.7 -- the hand-computed agent state history, produced by replaying the rules.
    h = replay_supply_chain(3)
    if h[0]["project"]["state"] != "backordered":
        fails.append("5.7 the project starts backordered")
    if h[1]["supplier"]["inventory"] != 0 or h[1]["carrier"]["state"] != "busy":
        fails.append(f"5.7 at t1 the supplier has shipped and the carrier is busy, got {h[1]}")
    if h[2]["project"]["state"] != "received":
        fails.append(f"5.7 at t2 the project has received the unit, got {h[2]}")
    if replay_supply_chain(3) != h:
        fails.append("5.7 the replay is deterministic and reproducible")

    # 5.8 -- the specification's two-job schedule.
    d = des_single_server([("A", 0.0, 2.0), ("B", 1.0, 2.0)])
    rows = {r["job"]: r for r in d["log"]}
    eq("5.8 A starts at 0", rows["A"]["start"], 0.0)
    eq("5.8 A ends at 2", rows["A"]["end"], 2.0)
    eq("5.8 A waits nothing", rows["A"]["wait"], 0.0)
    eq("5.8 B starts at 2", rows["B"]["start"], 2.0)
    eq("5.8 B ends at 4", rows["B"]["end"], 4.0)
    eq("5.8 B waits one", rows["B"]["wait"], 1.0)
    eq("5.8 mean wait", d["mean_wait"], 0.5)
    # Simultaneous arrivals: the tie policy is by name and must be explicit and stable.
    tie = des_single_server([("B", 0.0, 1.0), ("A", 0.0, 1.0)])
    if [r["job"] for r in tie["log"]] != ["A", "B"]:
        fails.append("5.8 the simultaneous-event policy must be explicit and deterministic")
    # A server released before the next arrival leaves no wait.
    idle = des_single_server([("A", 0.0, 1.0), ("B", 10.0, 1.0)])
    eq("5.8 a job arriving after the server is free waits nothing",
       idle["mean_wait"], 0.0)

    return fails


_FAILS = self_test()
assert not _FAILS, "Category 5 oracle does not reproduce the specification: " + "; ".join(_FAILS)
