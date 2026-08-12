"""
The canonical-structure layer: what each named method needs before it may compute at all.

WHY THIS FILE EXISTS. Run 8 classified twenty-seven modules and found a class of them whose
arithmetic was faithful and hand-checkable but whose METHOD was not present. A line-of-balance
measure whose unit count, production rates and buffer are literals in a source file is arithmetic
about that file, not about the project. A critical-chain fever chart whose buffer is derived from
the schedule performance index is not reading a sized buffer. A queueing measure with no arrival
process, no service process and no capacity is not a queueing model. An agent-based measure with
no agents, no rules and no time steps is not an agent-based model.

THE RULE THIS FILE ENFORCES, and it is the whole of it: a canonical method may compute only when
its defining structure is present. When the structure is absent the module ABSTAINS. It does not
degrade into a proxy in order to keep a number flowing onto the ledger, because a proxy reading
and a measured reading are indistinguishable once they reach a category rollup or a reader.

WHAT THIS FILE DOES NOT DO.

* It does not move a band boundary. Each module keeps the band it already carried, applied to a
  quantity of the same kind now taken from the real structure instead of from a literal or an
  index. Where a canonical quantity has only one defensible boundary, only one boundary is used
  and the module says so, rather than inventing a ladder to fill the space.
* It does not read a file. Every structure arrives on the signal inputs the caller assembled,
  exactly as every scalar does. Nothing here opens a path, so no operational execution can fall
  back to a research fixture through this layer.
* It does not make anything voting. Every module reached from here is non-voting and stays so.
* Computing here establishes no empirical or field validity of any kind, and a structure that
  arrives from a synthetic research fixture carries its own origin markings with it.

THE STRUCTURE CONTRACT is a plain dictionary on the signal inputs under the key named below, so
the production input contract is the same shape as every other input and an absent structure is
the ordinary absent-input case rather than a special one.
"""

from __future__ import annotations

import math
from typing import Any

from .rng import num

#: Module id to the signal-inputs key carrying its defining structure. Read by the modules
#: themselves, by the export and by the tests, so the contract is stated once.
CANONICAL_STRUCTURE_KEYS: dict[str, str] = {
    "A2.2": "lobStructure",
    "A2.3": "ccpmStructure",
    "A4.4": "auditedNonconformanceCohort",
    "A5.6": "queueStructure",
    "A5.7": "abmStructure",
    "A6.3": "auditedPermitCompliance",
}

#: The plain words for what each structure IS, used in the abstention sentence a reader sees.
#: No module id, no key name and no reason code ever appears in one of these.
CANONICAL_STRUCTURE_WORDS: dict[str, str] = {
    "A2.2": "a line of balance: locations in sequence, the crews working them, and a production "
            "rate and start for each line of work",
    "A2.3": "a critical chain with its activities and a sized project buffer",
    "A4.4": "an audited nonconformance cohort",
    "A5.6": "a queue: the entities that arrived, the service they received, the servers "
            "available to them and the window they were observed over",
    "A5.7": "a set of supply chain agents with decision rules, an interaction group and a state "
            "history across time steps",
    "A6.3": "audited permit condition compliance",
}


class StructureAbsent(Exception):
    """Raised with the reader's sentence when the required structure is not usable."""

    def __init__(self, sentence: str) -> None:
        super().__init__(sentence)
        self.sentence = sentence


def _rows(structure: Any, key: str, words: str) -> list[dict]:
    rows = structure.get(key)
    if not isinstance(rows, list) or not rows:
        raise StructureAbsent(
            f"No {words} has been provided for this project, so the method this measure is "
            f"named for cannot be carried out. No substitute reading is reported in its place.")
    for r in rows:
        if not isinstance(r, dict):
            raise StructureAbsent(
                f"The {words} provided for this project is not in a form this measure can read, "
                f"so no reading is taken from it.")
    return rows


def require_structure(si: dict, module_id: str) -> dict:
    """The structure, or StructureAbsent carrying the sentence the ledger will show."""
    key = CANONICAL_STRUCTURE_KEYS[module_id]
    words = CANONICAL_STRUCTURE_WORDS[module_id]
    structure = si.get(key)
    if structure is None:
        raise StructureAbsent(
            f"Awaiting {words}. This measure is named for a method that cannot be carried out "
            f"without it, so no reading is reported and no other figure is used in its place.")
    if not isinstance(structure, dict):
        raise StructureAbsent(
            f"The {words} provided for this project is not in a form this measure can read, so "
            f"no reading is taken from it.")
    return structure


def _finite(row: dict, field: str, words: str) -> float:
    v = num(row.get(field), None)
    if v is None or not math.isfinite(v):
        raise StructureAbsent(
            f"The {words} provided for this project is incomplete or carries a figure that is "
            f"not a number, so no reading is taken from it.")
    return v


# ------------------------------------------------------------------ A2.2 Line of Balance

def line_of_balance(structure: dict) -> dict[str, Any]:
    """
    The minimum time separation between a leading and a following line of work.

    THE QUANTITY IS THE ONE THE BAND ALREADY READS, so no boundary moves: the smallest buffer in
    days between the two crews anywhere across the locations. What changes is where it comes
    from. Each line of work advances at its own production rate in locations per day from its own
    start day, so the leading crew reaches location u on day s_lead + u / rate_lead and the
    following crew on day s_follow + u / rate_follow. The separation at location u is the
    difference, and the reading is its minimum over the locations that exist. Where the following
    crew is slower the separation grows and the minimum is at the first location; where it is
    faster the separation closes and the minimum is at the last, which is the interference case
    the method exists to find.
    """
    words = CANONICAL_STRUCTURE_WORDS["A2.2"]
    packages = _rows(structure, "work_packages", words)
    leading = str(structure.get("leading_work_type") or "")
    following = str(structure.get("following_work_type") or "")
    if not leading or not following or leading == following:
        raise StructureAbsent(
            "The line of balance provided does not name a leading and a following line of work "
            "to measure the separation between, so no separation is reported.")
    lead = [p for p in packages if str(p.get("work_type_id")) == leading]
    follow = [p for p in packages if str(p.get("work_type_id")) == following]
    if not lead or not follow:
        raise StructureAbsent(
            "The line of balance provided carries no work packages for one of the two lines of "
            "work named, so there is no second line to measure a separation against.")
    rate_lead = _finite(lead[0], "production_rate_locations_per_day", words)
    rate_follow = _finite(follow[0], "production_rate_locations_per_day", words)
    if rate_lead <= 0 or rate_follow <= 0:
        raise StructureAbsent(
            "A production rate in the line of balance provided is zero or below, and a line of "
            "work cannot advance at that rate, so no separation is measurable from it.")
    start_lead = min(_finite(p, "start_day", words) for p in lead)
    start_follow = min(_finite(p, "start_day", words) for p in follow)
    locations = sorted({int(_finite(p, "location_sequence", words)) for p in packages})
    if not locations:
        raise StructureAbsent(
            "The line of balance provided carries no locations in sequence, so there is nowhere "
            "for a separation to be measured at.")
    separations = [((start_follow + u / rate_follow) - (start_lead + u / rate_lead), u)
                   for u in locations]
    minimum, at_location = min(separations, key=lambda pair: pair[0])
    return {
        "minimum_separation_days": minimum,
        # The separation at the first location, which is where the two lines start apart. The
        # deep-dive chart draws the following line from it, so it is reported for the same
        # reason it always was, now measured rather than declared.
        "first_separation_days": separations[0][0],
        "critical_location_sequence": at_location,
        "leading_rate": rate_lead,
        "following_rate": rate_follow,
        "locations": len(locations),
    }


# --------------------------------------------------------------- A2.3 CCPM Buffer Health

def ccpm_buffer_health(structure: dict) -> dict[str, Any]:
    """
    The fever chart point, read off a sized buffer rather than off the schedule index.

    Buffer consumption is the share of the project buffer that has been used, which is the sized
    buffer less what remains, over the sized buffer. Chain completion is the share of the
    critical chain that is done. Both are quantities of the buffer and the chain, which is what
    the method is defined on; the fever-chart zones the module already carried are unchanged and
    are applied to them.
    """
    words = CANONICAL_STRUCTURE_WORDS["A2.3"]
    chains = _rows(structure, "chains", words)
    buffers = _rows(structure, "buffers", words)
    project_chains = [c for c in chains if str(c.get("chain_type") or "").upper() == "PROJECT"]
    if not project_chains:
        raise StructureAbsent(
            "The critical chain provided carries no project chain, so there is no chain for a "
            "project buffer to protect and no fever chart to place a reading on.")
    chain = project_chains[0]
    chain_id = str(chain.get("chain_id") or "")
    protecting = [b for b in buffers
                  if str(b.get("chain_id") or "") == chain_id
                  and str(b.get("buffer_type") or "").upper() == "PROJECT"]
    if not protecting:
        raise StructureAbsent(
            "The critical chain provided has no sized project buffer, and a buffer derived from "
            "a performance index is not a sized buffer, so no buffer consumption is reported.")
    buf = protecting[0]
    original = _finite(buf, "original_buffer_days", words)
    remaining = _finite(buf, "remaining_buffer_days", words)
    progress = _finite(buf, "chain_progress_fraction", words)
    if original <= 0:
        raise StructureAbsent(
            "The project buffer provided is sized at zero days or below, so there is no buffer "
            "for a consumption to be a share of.")
    if remaining > original or remaining < 0:
        raise StructureAbsent(
            "The project buffer provided has more days remaining than it was sized for, or "
            "fewer than none, so the pair does not describe one buffer.")
    if progress < 0 or progress > 1:
        raise StructureAbsent(
            "The critical chain provided reports a completion outside the range a share of the "
            "chain can take, so no fever chart reading is placed from it.")
    return {
        "pct_buffer_consumed": (original - remaining) / original * 100.0,
        "pct_chain_complete": progress * 100.0,
        "project_buffer_days": original,
        "feeding_buffer_count": sum(
            1 for b in buffers if str(b.get("buffer_type") or "").upper() == "FEEDING"),
        "chain_activity_count": int(num(chain.get("activity_count"), 0) or 0),
    }


# -------------------------------------------------------- A5.6 Queueing Theory Bottleneck

def queue_bottleneck(structure: dict) -> dict[str, Any]:
    """
    Server utilisation of the busiest queue, and the one boundary that is definitional.

    For a queue with c servers observed over a window, utilisation is the server time occupied by
    service divided by the server time available, which is c times the window. The single
    boundary applied to it is the stability condition of queueing theory itself: at a utilisation
    of one or more the arrival process is at least as fast as the service the servers can give,
    the queue has no steady state and waiting grows without bound. That boundary is definitional
    in the same sense the to-complete index's boundary of one is.

    ONE BOUNDARY IS ALL THAT IS USED. No source was found that specifies a utilisation at which a
    project's queue becomes a warning rather than a fact, and none is invented here, so this
    reports two levels and not four. The measured mean and ninetieth percentile waits are carried
    on the finding so a reader sees the queue rather than only a colour.
    """
    words = CANONICAL_STRUCTURE_WORDS["A5.6"]
    queues = _rows(structure, "queues", words)
    readings = []
    for q in queues:
        servers = _finite(q, "servers", words)
        horizon = _finite(q, "horizon_days", words)
        service = _finite(q, "total_service_days", words)
        entities = _finite(q, "entities", words)
        if servers < 1 or horizon <= 0 or service < 0 or entities < 0:
            raise StructureAbsent(
                "A queue provided for this project reports no servers, no window to observe "
                "them over, or a negative amount of service or arrivals, so no utilisation is "
                "measurable from it.")
        waits = q.get("wait_times_days")
        if not isinstance(waits, list) or len(waits) != int(entities):
            raise StructureAbsent(
                "A queue provided for this project does not carry a waiting time for each "
                "entity that arrived, so the queue it describes is incomplete.")
        wait_values = sorted(float(num(w, 0.0) or 0.0) for w in waits)
        readings.append({
            "queue_id": str(q.get("queue_id") or ""),
            "utilisation": service / (servers * horizon),
            "arrival_rate_per_day": entities / horizon,
            "mean_wait_days": (sum(wait_values) / len(wait_values)) if wait_values else 0.0,
            "p90_wait_days": _p90(wait_values),
            "entities": int(entities),
            "servers": int(servers),
        })
    bottleneck = max(readings, key=lambda r: r["utilisation"])
    return {"bottleneck": bottleneck, "queues": readings}


def _p90(values: list[float]) -> float:
    """Linear interpolated ninetieth percentile, the same definition the fixtures record."""
    if not values:
        return 0.0
    n = len(values)
    k = 0.9 * (n - 1)
    lo = int(math.floor(k))
    return values[lo] + (k - lo) * (values[min(lo + 1, n - 1)] - values[lo])


# -------------------------------------------------------- A5.7 Agent-Based Supply Chain

def agent_supply_chain(structure: dict) -> dict[str, Any]:
    """
    The share of supply chain agents in a disrupted state at the last time step observed.

    THE QUANTITY IS THE ONE THE BAND ALREADY READS, a share of a supply chain that is at risk, so
    no boundary moves. What changes is that it is now a share of AGENTS whose states came out of
    a rule replay across time steps, rather than a share of rows in a procurement log. The
    structure must carry agents, a decision rule for each, an interaction group, and a state
    history over more than one time step, because a model with one step is not a model over time.
    """
    words = CANONICAL_STRUCTURE_WORDS["A5.7"]
    agents = _rows(structure, "agents", words)
    states = _rows(structure, "states", words)
    for a in agents:
        if not str(a.get("agent_id") or "") or not str(a.get("decision_rule_id") or ""):
            raise StructureAbsent(
                "An agent provided for this project has no decision rule, and agents without "
                "rules do not make a model of behaviour, so no reading is taken.")
        if not str(a.get("network_group") or ""):
            raise StructureAbsent(
                "An agent provided for this project belongs to no interaction group, so the "
                "agents provided do not interact and no reading is taken.")
    steps = sorted({int(_finite(s, "time_step", words)) for s in states})
    if len(steps) < 2:
        raise StructureAbsent(
            "The agent state history provided covers a single point in time, so there is no "
            "run over time for a supply chain to be simulated across.")
    known = {str(a.get("agent_id")) for a in agents}
    last = steps[-1]
    final = [s for s in states if int(num(s.get("time_step"), 0) or 0) == last]
    if {str(s.get("agent_id")) for s in final} != known:
        raise StructureAbsent(
            "The agent state history provided does not cover every agent at the last time step, "
            "so the share of the supply chain at risk cannot be formed from it.")
    disrupted = sum(1 for s in final if str(s.get("state") or "").upper() != "NORMAL")
    return {
        "at_risk_ratio": disrupted / len(final),
        "agents": len(known),
        "time_steps": len(steps),
        "disrupted_agents": disrupted,
        "rules": len({str(a.get("decision_rule_id")) for a in agents}),
    }


# =================================================================================================
# THE REFERENCE AND DECISION OBJECT LAYER (the two modules whose defining structure is not a
# property of the project being assessed but an object outside it).
#
# A reference or decision object is not an input the project reports. It is a population, a
# training set or a decision problem that exists independently of the project and is READ, never
# written and never learned from at run time. Three rules are enforced here and each exists to
# stop a specific way this kind of module goes wrong.
#
# 1. VERSION AND PROVENANCE. The object states which package version produced it. A result that
#    cannot say which reference object produced it is not interpretable later, so an object with
#    no version is refused rather than used.
# 2. SPLIT DISCIPLINE, AND THE HOLDOUT IS LOCKED. Only a development or validation split may be
#    read. A locked holdout is refused outright, because the whole purpose of locking it is that
#    nothing may consult it, and a module that quietly reads it has leaked the outcome it is
#    supposed to be measured against.
# 3. NO SELF-TRAINING. The project being assessed may not appear in the reference population it
#    is being assessed against. If it does, the module is comparing the project with itself and
#    the comparison means nothing.
#
# Nothing here writes. The structures are copied out of the caller's dictionary and the caller's
# rows are never mutated, so a reference population cannot be edited through this layer.
# =================================================================================================

#: The splits a module may read at run time.
READABLE_SPLITS: frozenset[str] = frozenset({"DEVELOPMENT", "VALIDATION"})
#: The split that is locked, named so the refusal can be specific about what was attempted.
LOCKED_SPLIT = "LOCKED_HOLDOUT"

REFERENCE_OBJECT_KEYS: dict[str, str] = {
    "A5.4": "scenarioDecisionStructure",
    "B2.19": "decisionMatrix",
}

REFERENCE_OBJECT_WORDS: dict[str, str] = {
    "A5.4": "a decision problem: the actions open to the project, the scenarios they play out "
            "under, and the probability of each scenario",
    "B2.19": "a decision matrix: more than one alternative, scored against criteria that each "
             "state the direction that counts as better",
}


def require_reference_object(si: dict, module_id: str) -> dict:
    """The decision or reference object, with the three guards above applied before it is used."""
    key = REFERENCE_OBJECT_KEYS[module_id]
    words = REFERENCE_OBJECT_WORDS[module_id]
    obj = si.get(key)
    if obj is None:
        raise StructureAbsent(
            f"Awaiting {words}. This measure is named for a method that compares options that "
            f"have been set out, and none has been provided, so no reading is reported and no "
            f"other figure is used in its place.")
    if not isinstance(obj, dict):
        raise StructureAbsent(
            f"The decision information provided for this project is not in a form this measure "
            f"can read, so no reading is taken from it.")
    if not str(obj.get("asset_version") or ""):
        raise StructureAbsent(
            "The decision information provided does not say which version of the reference "
            "material it came from, so a reading taken from it could not be interpreted later "
            "and none is taken.")
    split = str(obj.get("split") or "").upper()
    if split == LOCKED_SPLIT:
        raise StructureAbsent(
            "The decision information provided comes from material that is held back and "
            "locked. It is locked precisely so that no measure consults it, so no reading is "
            "taken from it.")
    if split not in READABLE_SPLITS:
        raise StructureAbsent(
            "The decision information provided does not say which part of the reference "
            "material it belongs to, so it cannot be shown to be material this measure is "
            "allowed to read, and no reading is taken.")
    evaluated = str(obj.get("evaluated_project_id") or "")
    members = obj.get("reference_member_project_ids") or ()
    if evaluated and evaluated in set(str(m) for m in members):
        raise StructureAbsent(
            "The project being assessed is itself part of the reference material it would be "
            "compared against, so the comparison would be of the project with itself and no "
            "reading is taken from it.")
    return obj


def scenario_decision(obj: dict) -> dict[str, Any]:
    """
    Probability weighted expected outcome per action, and the worst scenario for the best action.

    The expectation of an action is the sum over scenarios of the scenario's probability times
    that action's outcome under it, which is the definition of an expectation over a stated
    distribution and nothing more. The recommended action is the one whose expectation is
    smallest, because the outcome carried here is a cost. The scenario range the band reads is
    that action's worst outcome across the scenarios, which is the quantity the module's existing
    ladder has always been placed on, so no boundary moves.
    """
    words = REFERENCE_OBJECT_WORDS["A5.4"]
    scenarios = _rows(obj, "scenarios", words)
    outcomes = _rows(obj, "outcomes", words)
    probability = {}
    for sc in scenarios:
        sid = str(sc.get("scenario_id") or "")
        p = _finite(sc, "probability", words)
        if not sid or p < 0 or p > 1:
            raise StructureAbsent(
                "A scenario in the decision information provided carries no name, or a "
                "probability outside the range a probability can take, so no expectation is "
                "formed from it.")
        probability[sid] = p
    total = sum(probability.values())
    if abs(total - 1.0) > 1e-6:
        raise StructureAbsent(
            "The scenario probabilities in the decision information provided do not sum to one, "
            "so they do not describe one distribution and no expectation is formed from them.")
    by_action: dict[str, list[tuple[str, float]]] = {}
    for row in outcomes:
        aid = str(row.get("action_id") or "")
        sid = str(row.get("scenario_id") or "")
        if not aid or sid not in probability:
            raise StructureAbsent(
                "An outcome in the decision information provided belongs to no action, or to a "
                "scenario that was not described, so the outcomes and the scenarios do not "
                "describe one decision.")
        by_action.setdefault(aid, []).append((sid, _finite(row, "cost_delta_usd", words)))
    if not by_action:
        raise StructureAbsent(
            "The decision information provided sets out no action with an outcome, so there is "
            "nothing to choose between.")
    for aid, rows in by_action.items():
        if {sid for sid, _v in rows} != set(probability):
            raise StructureAbsent(
                "An action in the decision information provided has no outcome under every "
                "scenario described, so its expectation cannot be formed.")
    expectations = {aid: sum(probability[sid] * v for sid, v in rows)
                    for aid, rows in by_action.items()}
    best = min(expectations, key=lambda a: expectations[a])
    worst_case = max(v for _sid, v in by_action[best])
    return {
        "recommended_action": best,
        "expected_cost_delta": expectations[best],
        "worst_case_cost_delta": worst_case,
        "actions": len(expectations),
        "scenarios": len(probability),
    }


def critic_topsis(obj: dict) -> dict[str, Any]:
    """
    CRITIC weights across the alternatives, then the TOPSIS closeness of each.

    THE DEGENERACY THIS REPLACES IS THE POINT. With one alternative there is no spread across
    alternatives, so the weighting was taken from the spread of a single project's own three
    criteria and a criterion equal to their mean carried a weight of exactly zero, dropping out
    of its own decision. CRITIC is defined across alternatives, so more than one is required
    here and the weights are computed the way the method defines them: each criterion's standard
    deviation over its normalised column, times the sum over criteria of one minus the
    correlation between the two normalised columns, normalised to sum to one.

    The closeness coefficient is then the distance to the anti-ideal over the sum of both
    distances, taken on the vector normalised matrix weighted by those weights, with each
    criterion's ideal at its own better end. The band the module already carried is applied to
    that coefficient unchanged.
    """
    words = REFERENCE_OBJECT_WORDS["B2.19"]
    criteria = _rows(obj, "criteria", words)
    alternatives = _rows(obj, "alternatives", words)
    if len(alternatives) < 2:
        raise StructureAbsent(
            "The decision matrix provided sets out a single alternative, and a weighting that "
            "is defined by how much the alternatives differ cannot be formed from one of them, "
            "so no ranking is reported.")
    names = []
    directions = {}
    for c in criteria:
        cid = str(c.get("criterion_id") or "")
        direction = str(c.get("direction") or "").upper()
        if not cid or direction not in ("MIN", "MAX"):
            raise StructureAbsent(
                "A criterion in the decision matrix provided does not say which direction "
                "counts as better, so no ideal can be placed on it and no ranking is reported.")
        names.append(cid)
        directions[cid] = direction
    if len(set(names)) != len(names) or not names:
        raise StructureAbsent(
            "The decision matrix provided names a criterion more than once, or names none, so "
            "no ranking is reported from it.")
    columns: dict[str, list[float]] = {c: [] for c in names}
    ids = []
    for alt in alternatives:
        aid = str(alt.get("alternative_id") or "")
        values = alt.get("values")
        if not aid or not isinstance(values, dict) or set(values) != set(names):
            raise StructureAbsent(
                "An alternative in the decision matrix provided is not scored against every "
                "criterion, so the alternatives cannot be compared and no ranking is reported.")
        ids.append(aid)
        for c in names:
            v = num(values.get(c), None)
            if v is None or not math.isfinite(v):
                raise StructureAbsent(
                    "A score in the decision matrix provided is not a number, so no ranking is "
                    "reported from it.")
            columns[c].append(v)

    def _sd(vals: list[float]) -> float:
        mu = sum(vals) / len(vals)
        return math.sqrt(sum((v - mu) ** 2 for v in vals) / (len(vals) - 1))

    def _corr(a: list[float], b: list[float]) -> float:
        ma, mb = sum(a) / len(a), sum(b) / len(b)
        top = sum((x - ma) * (y - mb) for x, y in zip(a, b))
        bottom = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
        return top / bottom if bottom else 0.0

    normalised = {}
    for c in names:
        col = columns[c]
        lo, hi = min(col), max(col)
        span = hi - lo
        if span == 0:
            normalised[c] = [0.0] * len(col)
        elif directions[c] == "MAX":
            normalised[c] = [(v - lo) / span for v in col]
        else:
            normalised[c] = [(hi - v) / span for v in col]
    raw = {}
    for c in names:
        raw[c] = _sd(normalised[c]) * sum(1.0 - _corr(normalised[c], normalised[d])
                                          for d in names)
    total = sum(raw.values())
    if total <= 0:
        raise StructureAbsent(
            "Every alternative in the decision matrix provided scores identically on every "
            "criterion, so there is nothing for a weighting to be formed from and no ranking is "
            "reported.")
    weights = {c: raw[c] / total for c in names}

    lengths = {c: math.sqrt(sum(v * v for v in columns[c])) for c in names}
    weighted = {}
    for c in names:
        L = lengths[c]
        weighted[c] = [(v / L if L else 0.0) * weights[c] for v in columns[c]]
    ideal, anti = {}, {}
    for c in names:
        col = weighted[c]
        if directions[c] == "MAX":
            ideal[c], anti[c] = max(col), min(col)
        else:
            ideal[c], anti[c] = min(col), max(col)
    closeness = []
    for i, aid in enumerate(ids):
        d_ideal = math.sqrt(sum((weighted[c][i] - ideal[c]) ** 2 for c in names))
        d_anti = math.sqrt(sum((weighted[c][i] - anti[c]) ** 2 for c in names))
        total_d = d_ideal + d_anti
        closeness.append((aid, (d_anti / total_d) if total_d else 0.0, d_ideal, d_anti))
    closeness.sort(key=lambda row: -row[1])
    top = closeness[0]
    return {
        "top_alternative": top[0],
        "closeness": top[1],
        "distance_ideal": top[2],
        "distance_anti": top[3],
        "weights": weights,
        "alternatives": len(ids),
        "ranking": [row[0] for row in closeness],
    }
