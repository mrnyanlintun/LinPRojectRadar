# Group B: Recommendation and Governance -- module source export

Regenerated from the registry (Run 5, post-freeze; see code_audit/REPORT_2026-08-11_run5-export.md). Every section below carries its activation state. Headings are canonical module names; no module id appears as a heading, per NAMING_AUTHORITY.md.

**36 modules in this group.**

---

## Conservative Dominance

Purpose: Conservative Dominance, category "Signal Synthesis".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. NEWLY WIRED: Newly wired and unvalidated: this module could not execute on the normal computation path before the flat-to-nested signal adapter, so its output has never been validated against real project evidence. Advisory, non-voting.

Method class: `Conservative_Dominance`

```python
def run_conservative_dominance(si: dict, rand: Callable[[], float],
                               period_cutoff) -> dict[str, Any]:
    if not _guard(si):
        return insufficient("Conservative_Dominance")
    d = _derive_decision(si)
    return {
        "method_class": "Conservative_Dominance",
        "status_color": d["healthState"],
        "state": d["healthState"],
        "conflict": d["conflictType"],
        # NO EM DASH. This string is what the Signal Ledger renders as this module's finding,
        # and until the flat-to-nested adapter landed it reached no screen, because the module
        # could not execute on the normal path at all. The moment it became reachable it became
        # user-facing text, which NAMING_AUTHORITY.md's standing rule covers. The separator is
        # the only change: no arithmetic, no state name, no classification is touched.
        "evidence_metric": f"{d['healthState']}: {d['conflictType']}",
    }
```

---

## Weighted Voting

Purpose: Weighted Voting, category "Signal Synthesis".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. NEWLY WIRED: Newly wired and unvalidated: this module could not execute on the normal computation path before the flat-to-nested signal adapter, so its output has never been validated against real project evidence. Advisory, non-voting.

Method class: `Weighted_Voting`

```python
def run_weighted_voting(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    project = si or {}
    s = project.get("signals") or {}
    sim = (project.get("simulationSignals") or {}).get("signal_array") or []
    votes = {"Green": 0, "Yellow": 0, "Amber": 0, "Red": 0}
    weights = {"cat1": 1.5, "cat4": 1.0, "cat7": 0.6, "cat9": 1.5}

    def add_vote(status, w):
        b = _vote_bucket(status)
        if not b:
            return
        votes[b] += w

    if s.get("mc") is not None:
        add_vote(s["mc"].get("status"), weights["cat1"])
    if s.get("cusum") is not None:
        add_vote(s["cusum"].get("status"), weights["cat1"])
    if s.get("doc") is not None:
        add_vote(s["doc"].get("status"), weights["cat4"])
    for m in sim:
        add_vote(m.get("status_color"), weights["cat7"])
    if s.get("decision") is not None:
        add_vote(s["decision"].get("state"), weights["cat9"])

    total = sum(votes[k] for k in votes)  # insertion order; do not sort
    if total == 0:
        return insufficient("Weighted_Voting")
    dominant = "Green"
    for b in list(votes)[1:]:  # JS reduce with `>` keeps the LATER key on ties
        dominant = dominant if votes[dominant] > votes[b] else b
    pct = int(js_round((votes[dominant] / total) * 100))
    return {
        "method_class": "Weighted_Voting",
        "status_color": dominant,
        "votes": votes,
        "dominant_pct": pct,
        "evidence_metric": f"Weighted vote: {dominant} ({pct}% of weighted signals)",
    }
```

---

## Majority Rules

Purpose: Majority Rules, category "Signal Synthesis".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. NEWLY WIRED: Newly wired and unvalidated: this module could not execute on the normal computation path before the flat-to-nested signal adapter, so its output has never been validated against real project evidence. Advisory, non-voting.

Method class: `Majority_Rules`

```python
def run_majority_rules(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    project = si or {}
    s = project.get("signals") or {}
    sim = (project.get("simulationSignals") or {}).get("signal_array") or []
    counts = {"Green": 0, "Yellow": 0, "Amber": 0, "Red": 0}

    def count(status):
        b = _vote_bucket(status)
        if not b:
            return
        counts[b] += 1

    if s.get("mc") is not None:
        count(s["mc"].get("status"))
    if s.get("cusum") is not None:
        count(s["cusum"].get("status"))
    if s.get("doc") is not None:
        count(s["doc"].get("status"))
    for m in sim:
        count(m.get("status_color"))

    total = sum(counts[k] for k in counts)
    if total == 0:
        return insufficient("Majority_Rules")
    majority = "Green"
    for b in list(counts)[1:]:
        majority = majority if counts[majority] > counts[b] else b
    pct = int(js_round((counts[majority] / total) * 100))
    return {
        "method_class": "Majority_Rules",
        "status_color": majority,
        "counts": counts,
        "majority_pct": pct,
        "total_votes": total,
        "evidence_metric": (
            f"{majority} by majority ({counts[majority]} of {total} modules, {pct}%)"
        ),
    }
```

---

## Worst-N-of-M

Purpose: Worst-N-of-M, category "Signal Synthesis".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. NEWLY WIRED: Newly wired and unvalidated: this module could not execute on the normal computation path before the flat-to-nested signal adapter, so its output has never been validated against real project evidence. Advisory, non-voting.

Method class: `Worst_N_of_M`

```python
def run_worst_n_of_m(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    project = si or {}
    s = project.get("signals") or {}
    sim = (project.get("simulationSignals") or {}).get("signal_array") or []
    all_statuses: list = []
    if s.get("mc") is not None:
        all_statuses.append(s["mc"].get("status"))
    if s.get("cusum") is not None:
        all_statuses.append(s["cusum"].get("status"))
    if s.get("doc") is not None:
        all_statuses.append(s["doc"].get("status"))
    for m in sim:
        if m.get("status_color"):
            all_statuses.append(m["status_color"])
    # Defect 1 again, third of the three ensembles. `"Red" in st` and `st == "Amber"` are the
    # same capitalised comparisons _vote_bucket carried, applied directly here: the lowercase
    # primary signals counted as neither red nor amber and simply vanished from both tallies
    # while still inflating the denominator. Every status is banded first, and one outside the
    # vocabulary is dropped from the denominator too rather than diluting the red fraction.
    bands = [b for b in (normalise_status(st) for st in all_statuses) if b]
    if not bands:
        return insufficient("Worst_N_of_M")
    red_count = sum(1 for b in bands if b == "Red")
    amber_count = sum(1 for b in bands if b == "Amber")
    m_total = len(bands)
    if red_count >= math.ceil(m_total * 0.3):
        status = "Red"
    elif amber_count >= math.ceil(m_total * 0.4):
        status = "Amber"
    elif red_count >= 1:
        status = "Yellow"
    else:
        status = "Green"
    return {
        "method_class": "Worst_N_of_M",
        "status_color": status,
        "red_count": red_count,
        "amber_count": amber_count,
        "total_modules": m_total,
        "evidence_metric": f"{red_count} Red + {amber_count} Amber of {m_total} total modules",
    }
```

---

## Dempster-Shafer

Purpose: Dempster-Shafer, category "Evidence Combination".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. NEWLY WIRED: Newly wired and unvalidated: this module could not execute on the normal computation path before the flat-to-nested signal adapter, so its output has never been validated against real project evidence. Advisory, non-voting.

Method class: `DST_Evidence_Combination`

```python
def run_dst(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    ex = si
    sources: list[dict] = []

    # Presence checks are `is not None`, not Python truthiness: a JS empty object {} is truthy,
    # so an empty mc/cusum/doc still takes the signal-present branch there.
    evm = ex.get("evm")
    cpi = evm.get("cpi") if evm is not None else None
    spi = evm.get("spi") if evm is not None else None

    # D1. With none of the four signals present, the three vacuous {0.25 × 4} masses below
    # combined to nothing while the doc arm's `absent -> score 0 -> Green` branch supplied a
    # real Green mass, so the fusion returned Green on every project the server computed. This
    # is Dempster-Shafer: the honest representation of no evidence is no combination, not a
    # combination of ignorance with one asserted belief.
    if not (cpi and spi) and ex.get("mc") is None and ex.get("cusum") is None \
            and ex.get("doc") is None:
        return insufficient("DST_Evidence_Combination")

    if cpi and spi:
        evm_min = min(cpi, spi)
        if evm_min >= 0.95:
            sources.append({"Green": 0.80, "Amber": 0.10, "Red": 0.05, "Unknown": 0.05})
        elif evm_min >= 0.90:
            sources.append({"Green": 0.10, "Amber": 0.70, "Red": 0.15, "Unknown": 0.05})
        else:
            sources.append({"Green": 0.05, "Amber": 0.15, "Red": 0.75, "Unknown": 0.05})
    else:
        sources.append({"Green": 0.25, "Amber": 0.25, "Red": 0.25, "Unknown": 0.25})

    mc = ex.get("mc")
    if mc is not None:
        p80 = mc.get("p80DeltaPct") or 0
        if p80 <= 5:
            sources.append({"Green": 0.75, "Amber": 0.15, "Red": 0.05, "Unknown": 0.05})
        elif p80 <= 10:
            sources.append({"Green": 0.10, "Amber": 0.65, "Red": 0.20, "Unknown": 0.05})
        else:
            sources.append({"Green": 0.05, "Amber": 0.10, "Red": 0.80, "Unknown": 0.05})
    else:
        sources.append({"Green": 0.25, "Amber": 0.25, "Red": 0.25, "Unknown": 0.25})

    cusum = ex.get("cusum")
    if cusum is not None:
        if not cusum.get("breached"):
            sources.append({"Green": 0.75, "Amber": 0.15, "Red": 0.05, "Unknown": 0.05})
        else:
            sources.append({"Green": 0.05, "Amber": 0.15, "Red": 0.75, "Unknown": 0.05})
    else:
        sources.append({"Green": 0.25, "Amber": 0.25, "Red": 0.25, "Unknown": 0.25})

    doc = ex.get("doc")
    # JS: `doc ? doc.score : 0` — a present doc with an undefined score makes both comparisons
    # below false and lands in the Red branch. Absent doc -> 0 -> Green.
    doc_score = (doc.get("score") if doc is not None else 0)
    if doc_score is not None and doc_score < 0.30:
        sources.append({"Green": 0.75, "Amber": 0.15, "Red": 0.05, "Unknown": 0.05})
    elif doc_score is not None and doc_score < 0.70:
        sources.append({"Green": 0.10, "Amber": 0.70, "Red": 0.15, "Unknown": 0.05})
    else:
        sources.append({"Green": 0.05, "Amber": 0.15, "Red": 0.75, "Unknown": 0.05})

    result = dict(sources[0])
    for s in sources[1:]:
        result = dst_combine(result, s)

    # JS reduce with `>` keeps the LATER state on ties.
    max_state = "Green"
    for b in ("Amber", "Red"):
        max_state = max_state if result[max_state] > result[b] else b

    decision = ex.get("decision")
    conservative = decision.get("state") if decision is not None else None
    # JS `a && expr`: null when conservative is null/'' — not False.
    agrees = (max_state.lower() == conservative.lower()) if conservative else conservative
    conflict = result.get("conflict", 0.0)
    conflict_level = "High" if conflict > 0.3 else ("Moderate" if conflict > 0.1 else "Low")
    status = "Red" if max_state == "Red" else ("Amber" if max_state == "Amber" else "Green")

    return {
        "method_class": "DST_Evidence_Combination",
        "status_color": status,
        "belief_green": round2(result["Green"]),
        "belief_amber": round2(result["Amber"]),
        "belief_red": round2(result["Red"]),
        "belief_unknown": round2(result["Unknown"]),
        "conflict_mass": round2(conflict),
        "conflict_level": conflict_level,
        "agrees_with_conservative": agrees,
        "conservative_state": conservative,
        "evidence_metric": (
            f"Belief: Green {int(js_round(result['Green'] * 100))}% · "
            f"Amber {int(js_round(result['Amber'] * 100))}% · "
            f"Red {int(js_round(result['Red'] * 100))}% · "
            f"Conflict mass {int(js_round(conflict * 100))}%"
        ),
    }
```

---

## Pythagorean Fuzzy Sets

Purpose: Pythagorean Fuzzy Sets, category "Evidence Combination".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: hard-coded transformations of raw CPI, SPI and document risk

Method class: `Pythagorean_Fuzzy`

```python
def run_pythagorean_fuzzy(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "docRiskScore")):
        return insufficient("Pythagorean_Fuzzy")
    evm_min = min(si["cpi"], si["spi"])
    mu = _clamp01((evm_min - 0.85) / 0.15)
    nu = _clamp01((0.95 - evm_min) / 0.15)
    if mu * mu + nu * nu > 1:
        norm = math.sqrt(mu * mu + nu * nu)
        mu /= norm
        nu /= norm
    pi = math.sqrt(max(0, 1 - mu * mu - nu * nu))
    doc = si.get("docRiskScore") or 0
    adj_mu = mu * (1 - doc * 0.3)
    adj_nu = min(1, nu + doc * 0.3)
    score = adj_mu - adj_nu
    color = ("Green" if score >= 0.3 else "Yellow" if score >= 0.0
             else "Amber" if score >= -0.3 else "Red")
    return {
        "method_class": "Pythagorean_Fuzzy",
        "status_color": color,
        "membership": round2(adj_mu),
        "non_membership": round2(adj_nu),
        "hesitancy": round2(pi),
        "evidence_metric": (
            f"PFS: μ={_js_str(round2(adj_mu))} ν={_js_str(round2(adj_nu))} "
            f"π={_js_str(round2(pi))}"
        ),
    }
```

---

## Picture Fuzzy Sets

Purpose: Picture Fuzzy Sets, category "Evidence Combination".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: hard-coded memberships consuming raw metrics; no calibration evidenced

Method class: `Picture_Fuzzy`

```python
def run_picture_fuzzy(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "docRiskScore")):
        return insufficient("Picture_Fuzzy")
    evm_min = min(si["cpi"], si["spi"])
    positive = max(0, min(0.95, (evm_min - 0.85) / 0.15))
    negative = max(0, min(0.95, (0.95 - evm_min) / 0.15)) * (1 + si["docRiskScore"] * 0.5)
    negative = min(0.95, negative)
    neutral = max(0, 0.6 - positive - negative) * 0.3
    refusal = max(0, 1 - positive - neutral - negative)
    score = positive - negative
    color = ("Green" if score >= 0.30 else "Yellow" if score >= 0.00
             else "Amber" if score >= -0.30 else "Red")
    return {
        "method_class": "Picture_Fuzzy",
        "status_color": color,
        "positive": round2(positive),
        "neutral": round2(neutral),
        "negative": round2(negative),
        "refusal": round2(refusal),
        "evidence_metric": (
            f"PicFS: +{_js_str(round2(positive))} 0{_js_str(round2(neutral))} "
            f"-{_js_str(round2(negative))} r{_js_str(round2(refusal))}"
        ),
    }
```

---

## Hesitant Fuzzy Sets

Purpose: Hesitant Fuzzy Sets, category "Evidence Combination".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: designed perturbations, not elicited or observed hesitant assessments

Method class: `Hesitant_Fuzzy`

```python
def run_hesitant_fuzzy(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi")):
        return insufficient("Hesitant_Fuzzy")
    evm_min = min(si["cpi"], si["spi"])
    evm_max = max(si["cpi"], si["spi"])
    memberships = [
        _clamp01((evm_min - 0.85) / 0.15),
        _clamp01((evm_max - 0.85) / 0.15),
        _clamp01(((evm_min + evm_max) / 2 - 0.85) / 0.15),
    ]
    score = sum(memberships) / len(memberships)
    hesitancy = max(memberships) - min(memberships)
    color = ("Green" if score >= 0.7 else "Yellow" if score >= 0.5
             else "Amber" if score >= 0.3 else "Red")
    return {
        "method_class": "Hesitant_Fuzzy",
        "status_color": color,
        "memberships": [round2(m) for m in memberships],
        "average_membership": round2(score),
        "hesitancy_degree": round2(hesitancy),
        "evidence_metric": (
            f"HFS: avg membership {_js_str(round2(score))}, "
            f"hesitancy {_js_str(round2(hesitancy))}"
        ),
    }
```

---

## Type-2 Fuzzy Sets

Purpose: Type-2 Fuzzy Sets, category "Evidence Combination".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: membership intervals that are designed constants

Method class: `Type2_Fuzzy`

```python
def run_type2_fuzzy(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi")):
        return insufficient("Type2_Fuzzy")
    evm_min = min(si["cpi"], si["spi"])
    primary = _clamp01((evm_min - 0.85) / 0.15)
    uncertainty = abs(si["cpi"] - si["spi"]) * 2
    lower = max(0, primary - uncertainty * 0.5)
    upper = min(1, primary + uncertainty * 0.5)
    centroid = (lower + upper) / 2
    footprint = upper - lower
    color = ("Green" if centroid >= 0.7 and footprint <= 0.2
             else "Yellow" if centroid >= 0.5
             else "Amber" if centroid >= 0.3 else "Red")
    return {
        "method_class": "Type2_Fuzzy",
        "status_color": color,
        "lower_membership": round2(lower),
        "upper_membership": round2(upper),
        "centroid": round2(centroid),
        "footprint_of_uncertainty": round2(footprint),
        "evidence_metric": (
            f"T2FS: centroid {_js_str(round2(centroid))}, FOU {_js_str(round2(footprint))}"
        ),
    }
```

---

## Maximum Entropy

Purpose: Maximum Entropy, category "Evidence Combination".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: entropy over designed state probabilities; measures the lookup, not the project

Method class: `Maximum_Entropy`

```python
def run_maximum_entropy(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "docRiskScore")):
        return insufficient("Maximum_Entropy")
    evm_min = min(si["cpi"], si["spi"])
    raw = [
        max(0.01, 0.70 if evm_min >= 0.95 else 0.20 if evm_min >= 0.90 else 0.05),
        max(0.01, 0.20 if evm_min >= 0.95 else 0.50 if evm_min >= 0.90 else 0.20),
        max(0.01, 0.07 if evm_min >= 0.95 else 0.25 if evm_min >= 0.90 else 0.60),
        max(0.01, 0.02 if evm_min >= 0.95 else 0.05 if evm_min >= 0.90 else 0.15),
    ]
    total = sum(raw)
    probs = [p / total for p in raw]
    doc = si.get("docRiskScore") or 0
    probs[2] = min(0.95, probs[2] + doc * 0.2)
    probs[3] = min(0.95, probs[3] + doc * 0.1)
    total = sum(probs)
    probs = [p / total for p in probs]
    entropy = -sum(p * math.log2(p) for p in probs if p > 0)
    normalized = entropy / math.log2(4)
    labels = ["Green", "Yellow", "Amber", "Red"]
    dominant = labels[probs.index(max(probs))]
    return {
        "method_class": "Maximum_Entropy",
        "status_color": dominant,
        "probabilities": {
            "Green": int(js_round(probs[0] * 100)),
            "Yellow": int(js_round(probs[1] * 100)),
            "Amber": int(js_round(probs[2] * 100)),
            "Red": int(js_round(probs[3] * 100)),
        },
        "entropy": round2(normalized),
        "evidence_metric": f"MaxEnt: {dominant} (entropy {_js_str(round2(normalized))})",
    }
```

---

## Possibility Theory

Purpose: Possibility Theory, category "Evidence Combination".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: fixed mappings from raw metrics; no governed possibility distribution

Method class: `Possibility_Theory`

```python
def run_possibility_theory(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "docRiskScore")):
        return insufficient("Possibility_Theory")
    evm_min = min(si["cpi"], si["spi"])
    doc = si.get("docRiskScore") or 0
    possibility = {
        "Green": min(1, max(0, (evm_min - 0.85) / 0.10) * (1 - doc * 0.5)),
        "Amber": min(1, max(0, 1 - (evm_min - 0.88) / 0.10) * (1 + doc * 0.3)),
        "Red": min(1, max(0, (0.92 - evm_min) / 0.10) + doc * 0.4),
    }
    necessity = {k: max(0, v - 0.3) for k, v in possibility.items()}
    dominant = "Green"
    for b in list(possibility)[1:]:  # JS reduce with `>`: later key wins ties
        dominant = dominant if possibility[dominant] > possibility[b] else b
    return {
        "method_class": "Possibility_Theory",
        "status_color": dominant,
        "possibility": {k: round2(v) for k, v in possibility.items()},
        "necessity": {k: round2(v) for k, v in necessity.items()},
        "evidence_metric": (
            f"Possibility: {dominant} (Π={_js_str(round2(possibility[dominant]))}, "
            f"N={_js_str(round2(necessity[dominant]))})"
        ),
    }
```

---

## Spherical Fuzzy Sets

Purpose: Spherical Fuzzy Sets, category "Evidence Combination".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: algebraically bounded but fixed memberships on raw unqualified inputs

Method class: `Spherical_Fuzzy`

```python
def run_spherical_fuzzy(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "docRiskScore")):
        return insufficient("Spherical_Fuzzy")
    evm_min = min(si["cpi"], si["spi"])
    mu = max(0, min(0.95, (evm_min - 0.82) / 0.18))
    nu = max(0, min(0.95, (0.98 - evm_min) / 0.18)) * (1 + (si.get("docRiskScore") or 0) * 0.5)
    nu = min(0.95, nu)
    constraint = mu * mu + nu * nu
    if constraint > 1:
        sc = math.sqrt(constraint)
        mu /= sc
        nu /= sc
    pi = math.sqrt(max(0, 1 - mu * mu - nu * nu))
    score = mu - nu
    color = ("Green" if score >= 0.4 else "Yellow" if score >= 0.1
             else "Amber" if score >= -0.2 else "Red")
    return {
        "method_class": "Spherical_Fuzzy",
        "status_color": color,
        "mu": round2(mu),
        "nu": round2(nu),
        "pi": round2(pi),
        "score": round2(score),
        "evidence_metric": (
            f"SFS: μ={_js_str(round2(mu))} ν={_js_str(round2(nu))} π={_js_str(round2(pi))}"
        ),
    }
```

---

## Fermatean Fuzzy Sets

Purpose: Fermatean Fuzzy Sets, category "Evidence Combination".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: formula-shaped with designed memberships, no empirical or elicitation basis

Method class: `Fermatean_Fuzzy`

```python
def run_fermatean_fuzzy(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi")):
        return insufficient("Fermatean_Fuzzy")
    evm_min = min(si["cpi"], si["spi"])
    mu = max(0, min(0.99, (evm_min - 0.80) / 0.20))
    nu = max(0, min(0.99, (1.00 - evm_min) / 0.20))
    while mu ** 3 + nu ** 3 > 1:
        mu *= 0.95
        nu *= 0.95
    pi = (max(0, 1 - mu ** 3 - nu ** 3)) ** (1 / 3)
    score = mu - nu
    color = ("Green" if score >= 0.35 else "Yellow" if score >= 0.05
             else "Amber" if score >= -0.25 else "Red")
    return {
        "method_class": "Fermatean_Fuzzy",
        "status_color": color,
        "mu": round2(mu),
        "nu": round2(nu),
        "pi": round2(pi),
        "evidence_metric": (
            f"FFS: μ={_js_str(round2(mu))} ν={_js_str(round2(nu))} π={_js_str(round2(pi))}"
        ),
    }
```

---

## MARCOS Ranking

Purpose: MARCOS Ranking, category "Evidence Combination".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `MARCOS`

```python
def run_marcos(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "docRiskScore")):
        return insufficient("MARCOS")
    criteria = [
        {"value": si["cpi"], "ideal": 1.05, "anti": 0.80, "weight": 0.40},
        {"value": si["spi"], "ideal": 1.05, "anti": 0.80, "weight": 0.35},
        {"value": 1 - (si.get("docRiskScore") or 0), "ideal": 1.00, "anti": 0.30,
         "weight": 0.25},
    ]
    utility_ideal = 0.0
    for c in criteria:
        rng = c["ideal"] - c["anti"]
        norm = (c["value"] - c["anti"]) / rng if rng > 0 else 0.5
        utility_ideal += _clamp01(norm) * c["weight"]
    utility_anti = 1 - utility_ideal
    f_ideal = utility_ideal / (utility_ideal + utility_anti)
    f_anti = utility_anti / (utility_ideal + utility_anti)
    score = _jsdiv((f_ideal + f_anti),
                   1 + _jsdiv(1 - f_ideal, f_ideal) + _jsdiv(1 - f_anti, f_anti))
    score = _round3(score)
    color = ("Green" if score >= 0.65 else "Yellow" if score >= 0.50
             else "Amber" if score >= 0.35 else "Red")
    return {
        "method_class": "MARCOS",
        "status_color": color,
        "marcos_score": score,
        "utility_ideal": round2(utility_ideal),
        "evidence_metric": (
            f"MARCOS score: {_js_str(score)} "
            f"(utility vs ideal: {_js_str(round2(utility_ideal))})"
        ),
    }
```

---

## CRITIC-TOPSIS

Purpose: CRITIC-TOPSIS, category "Evidence Combination".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `CRITIC_TOPSIS`

```python
def run_critic_topsis(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "docRiskScore")):
        return insufficient("CRITIC_TOPSIS")
    criteria = [si["cpi"], si["spi"], 1 - (si.get("docRiskScore") or 0)]
    mean = sum(criteria) / len(criteria)
    stddev = math.sqrt(sum((v - mean) ** 2 for v in criteria) / len(criteria))
    weights = [abs(v - mean) / stddev if stddev > 0 else 1 / 3 for v in criteria]
    w_sum = sum(weights)
    weights = [w / w_sum for w in weights]
    ideal = [1.05, 1.05, 1.00]
    anti = [0.80, 0.80, 0.30]
    d_ideal = math.sqrt(sum(weights[i] * (criteria[i] - ideal[i]) ** 2
                            for i in range(len(criteria))))
    d_anti = math.sqrt(sum(weights[i] * (criteria[i] - anti[i]) ** 2
                           for i in range(len(criteria))))
    topsis = _round3(d_anti / (d_ideal + d_anti + 0.0001))
    color = ("Green" if topsis >= 0.65 else "Yellow" if topsis >= 0.50
             else "Amber" if topsis >= 0.35 else "Red")
    return {
        "method_class": "CRITIC_TOPSIS",
        "status_color": color,
        "topsis_score": topsis,
        "distance_ideal": _round3(d_ideal),
        "distance_anti": _round3(d_anti),
        "evidence_metric": (
            f"CRITIC-TOPSIS: {_js_str(topsis)} (d+ {_js_str(_round3(d_ideal))}, "
            f"d- {_js_str(_round3(d_anti))})"
        ),
    }
```

---

## Rough Sets

Purpose: Rough Sets, category "Evidence Combination".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. NEWLY WIRED: Newly wired and unvalidated: this module could not execute on the normal computation path before the flat-to-nested signal adapter, so its output has never been validated against real project evidence. Advisory, non-voting.

Method class: `Rough_Sets_Classification`

```python
def run_rough_sets(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    states = ["Green", "Amber", "Red"]
    classes: list[str] = []
    cpi, spi = _evm(si)
    if cpi and spi:
        evm_min = min(cpi, spi)
        classes.append("Green" if evm_min >= 0.95 else "Amber" if evm_min >= 0.90 else "Red")
    mc = si.get("mc")
    if mc is not None:
        p80 = mc.get("p80DeltaPct") or 0
        classes.append("Green" if p80 <= 5 else "Amber" if p80 <= 10 else "Red")
    cusum = si.get("cusum")
    if cusum is not None:
        classes.append("Red" if cusum.get("breached") else "Green")
    doc = si.get("doc")
    if doc is not None:
        score = doc.get("score") or 0
        classes.append("Green" if score < 0.30 else "Amber" if score < 0.70 else "Red")

    if not classes:
        # D1. The `or 1` that used to stand in for the denominator here made every ratio 0/1,
        # which put every state outside the lower approximation and produced "Indeterminate"
        # Amber from nothing. An empty evidence set has no classification.
        return insufficient("Rough_Sets_Classification")

    counts = {"Green": 0, "Amber": 0, "Red": 0}
    for c in classes:
        counts[c] += 1
    total = len(classes)

    lower = [s for s in states if counts[s] / total > 0.75]
    upper = [s for s in states if counts[s] > 0]
    boundary = [s for s in upper if s not in lower]

    if len(lower) == 1:
        classification = "Definite " + lower[0]
        status = lower[0]
    elif boundary:
        classification = "Borderline: " + " / ".join(boundary)
        status = "Red" if "Red" in boundary else "Amber"
    else:
        classification = "Indeterminate"
        status = "Amber"

    return {
        "method_class": "Rough_Sets_Classification",
        "status_color": status,
        "lower_approximation": lower,
        "upper_approximation": upper,
        "boundary_region": boundary,
        "classification": classification,
        "signal_votes": counts,
        "total_signals": total,
        "evidence_metric": (
            f"{classification} (Green {counts['Green']}, Amber {counts['Amber']}, "
            f"Red {counts['Red']} of {total} signals)"
        ),
    }
```

---

## Hypersoft Sets

Purpose: Hypersoft Sets, category "Evidence Combination".

Activation state: DISABLED. Concept-only: implements no defensible version of the analytical structure its name claims. Non-executable in production, non-voting, excluded from every fusion input and every rollup.

Method class: `Hypersoft_Sets`

```python
def run_hypersoft_sets(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "docRiskScore")):
        return insufficient("Hypersoft_Sets")
    doc = si.get("docRiskScore") or 0
    cost = "poor" if si["cpi"] < 0.90 else "fair" if si["cpi"] < 0.95 else "good"
    schedule = "poor" if si["spi"] < 0.90 else "fair" if si["spi"] < 0.95 else "good"
    risk = "high" if doc > 0.70 else "medium" if doc > 0.30 else "low"
    key = f"{cost}-{schedule}-{risk}"
    score = _HYPERSOFT.get(key, 0.35)
    color = ("Green" if score >= 0.70 else "Yellow" if score >= 0.50
             else "Amber" if score >= 0.30 else "Red")
    return {
        "method_class": "Hypersoft_Sets",
        "status_color": color,
        "attribute_combination": key,
        "score": score,
        "evidence_metric": f"Hypersoft [{key}]: score {_js_str(score)}",
    }
```

---

## Neutrosophic Logic

Purpose: Neutrosophic Logic, category "Evidence Combination".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. NEWLY WIRED: Newly wired and unvalidated: this module could not execute on the normal computation path before the flat-to-nested signal adapter, so its output has never been validated against real project evidence. Advisory, non-voting.

Method class: `Neutrosophic_Logic`

```python
def run_neutrosophic(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    components: list[dict] = []
    cpi, spi = _evm(si)
    if cpi and spi:
        evm_min = min(cpi, spi)
        if evm_min >= 0.95:
            components.append({"T": 0.85, "I": 0.10, "F": 0.05, "source": "EVM", "state": "Green"})
        elif evm_min >= 0.90:
            components.append({"T": 0.70, "I": 0.20, "F": 0.10, "source": "EVM", "state": "Amber"})
        else:
            components.append({"T": 0.75, "I": 0.15, "F": 0.10, "source": "EVM", "state": "Red"})
    mc = si.get("mc")
    if mc is not None:
        p80 = mc.get("p80DeltaPct") or 0
        if p80 <= 5:
            components.append({"T": 0.80, "I": 0.10, "F": 0.10,
                               "source": "Forecast", "state": "Green"})
        elif p80 <= 10:
            components.append({"T": 0.65, "I": 0.25, "F": 0.10,
                               "source": "Forecast", "state": "Amber"})
        else:
            components.append({"T": 0.75, "I": 0.15, "F": 0.10,
                               "source": "Forecast", "state": "Red"})
    cusum = si.get("cusum")
    if cusum is not None:
        if cusum.get("breached"):
            components.append({"T": 0.90, "I": 0.05, "F": 0.05,
                               "source": "CUSUM", "state": "Red"})
        else:
            components.append({"T": 0.80, "I": 0.10, "F": 0.10,
                               "source": "CUSUM", "state": "Green"})
    doc = si.get("doc")
    if doc is not None:
        s = doc.get("score") or 0
        if s < 0.30:
            components.append({"T": 0.85, "I": 0.10, "F": 0.05,
                               "source": "DocRisk", "state": "Green"})
        elif s < 0.70:
            components.append({"T": 0.65, "I": 0.25, "F": 0.10,
                               "source": "DocRisk", "state": "Amber"})
        else:
            components.append({"T": 0.75, "I": 0.15, "F": 0.10,
                               "source": "DocRisk", "state": "Red"})

    if not components:
        return insufficient("Neutrosophic_Logic")

    t = 0.0
    for c in components:
        t = 1 - (1 - t) * (1 - c["T"])
    i = 1.0
    for c in components:
        i = i * c["I"]
    f = 1.0
    for c in components:
        f = f * c["F"]
    total = (t + i + f) or 1
    t = round2(t / total)
    i = round2(i / total)
    f = round2(f / total)

    red_count = sum(1 for c in components if c["state"] == "Red")
    amber_count = sum(1 for c in components if c["state"] == "Amber")
    status = "Red" if red_count >= 2 else "Amber" if amber_count >= 2 else "Green"
    if i > 0.30:
        status = "Amber" if status == "Green" else status
    level = "High" if i > 0.30 else "Moderate" if i > 0.15 else "Low"

    return {
        "method_class": "Neutrosophic_Logic",
        "status_color": status,
        "T": t, "I": i, "F": f,
        "indeterminacy_level": level,
        "signal_components": components,
        "evidence_metric": (
            f"T={_num_str(t)} I={_num_str(i)} F={_num_str(f)}, Indeterminacy: {level}"
        ),
    }
```

---

## Interval Fuzzy Sets

Purpose: Interval Fuzzy Sets, category "Evidence Combination".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. NEWLY WIRED: Newly wired and unvalidated: this module could not execute on the normal computation path before the flat-to-nested signal adapter, so its output has never been validated against real project evidence. Advisory, non-voting.

Method class: `Interval_Fuzzy_Sets`

```python
def run_interval_fuzzy(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    ev_unc, ac_unc = 0.02, 0.01
    intervals = []
    cpi, spi = _evm(si)
    if cpi:
        lo, hi = cpi - ev_unc - ac_unc, cpi + ev_unc + ac_unc
        intervals.append({"green": _mem_interval(_mem_green, lo, hi),
                          "amber": _mem_interval(_mem_amber, lo, hi),
                          "red": _mem_interval(_mem_red, lo, hi)})
    if spi:
        lo, hi = spi - ev_unc, spi + ev_unc
        intervals.append({"green": _mem_interval(_mem_green, lo, hi),
                          "amber": _mem_interval(_mem_amber, lo, hi),
                          "red": _mem_interval(_mem_red, lo, hi)})

    if not intervals:
        return insufficient("Interval_Fuzzy_Sets")

    def agg(key, idx):
        out = 0
        for it in intervals:
            out = max(out, it[key][idx])
        return out

    agg_green = [agg("green", 0), agg("green", 1)]
    agg_amber = [agg("amber", 0), agg("amber", 1)]
    agg_red = [agg("red", 0), agg("red", 1)]

    green_mid = (agg_green[0] + agg_green[1]) / 2
    amber_mid = (agg_amber[0] + agg_amber[1]) / 2
    red_mid = (agg_red[0] + agg_red[1]) / 2
    status = ("Red" if red_mid >= amber_mid and red_mid >= green_mid
              else "Amber" if amber_mid >= green_mid else "Green")

    width = round2((agg_red[1] - agg_red[0]) + (agg_amber[1] - agg_amber[0]))

    def fmt(interval):
        return ", ".join(str(x) for x in
                         [_num_str(round2(interval[0])), _num_str(round2(interval[1]))])

    return {
        "method_class": "Interval_Fuzzy_Sets",
        "status_color": status,
        "green_interval": agg_green,
        "amber_interval": agg_amber,
        "red_interval": agg_red,
        "uncertainty_width": width,
        "uncertainty_level": ("High" if width > 0.3 else
                              "Moderate" if width > 0.15 else "Low"),
        "evidence_metric": (
            f"Green [{fmt(agg_green)}] Amber [{fmt(agg_amber)}] Red [{fmt(agg_red)}]"
        ),
    }
```

---

## Z-numbers

Purpose: Z-numbers, category "Evidence Combination".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. NEWLY WIRED: Newly wired and unvalidated: this module could not execute on the normal computation path before the flat-to-nested signal adapter, so its output has never been validated against real project evidence. Advisory, non-voting.

Method class: `Z_Numbers`

```python
def run_z_numbers(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    signals = []
    cpi, spi = _evm(si)
    if cpi and spi:
        evm_min = min(cpi, spi)
        restriction = "Green" if evm_min >= 0.95 else "Amber" if evm_min >= 0.90 else "Red"
        signals.append({"source": "EVM", "restriction": restriction, "reliability": 0.85})
    cusum = si.get("cusum")
    if cusum is not None:
        signals.append({"source": "CUSUM",
                        "restriction": "Red" if cusum.get("breached") else "Green",
                        "reliability": 0.90})
    doc = si.get("doc")
    if doc is not None:
        score = doc.get("score") or 0
        restriction = "Red" if score >= 0.70 else "Amber" if score >= 0.30 else "Green"
        signals.append({"source": "DocRisk", "restriction": restriction, "reliability": 0.65})
    mc = si.get("mc")
    if mc is not None:
        p80 = mc.get("p80DeltaPct") or 0
        restriction = "Red" if p80 > 10 else "Amber" if p80 > 5 else "Green"
        signals.append({"source": "MonteCarlo", "restriction": restriction, "reliability": 0.88})

    if not signals:
        return insufficient("Z_Numbers")

    total_red = sum(s["reliability"] for s in signals if s["restriction"] == "Red")
    total_amber = sum(s["reliability"] for s in signals if s["restriction"] == "Amber")
    total_green = sum(s["reliability"] for s in signals if s["restriction"] == "Green")
    avg_rel = sum(s["reliability"] for s in signals) / len(signals)

    status = ("Red" if total_red >= total_amber and total_red >= total_green
              else "Amber" if total_amber >= total_green else "Green")

    return {
        "method_class": "Z_Numbers",
        "status_color": status,
        "weighted_red": round2(total_red),
        "weighted_amber": round2(total_amber),
        "weighted_green": round2(total_green),
        "avg_reliability": round2(avg_rel),
        "signal_count": len(signals),
        "signals": signals,
        "evidence_metric": (
            f"Reliability-weighted: Red {_num_str(round2(total_red))} · "
            f"Amber {_num_str(round2(total_amber))} · "
            f"Green {_num_str(round2(total_green))} · "
            f"Avg reliability {int(js_round(avg_rel * 100))}%"
        ),
    }
```

---

## PLTS

Purpose: PLTS, category "Evidence Combination".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. NEWLY WIRED: Newly wired and unvalidated: this module could not execute on the normal computation path before the flat-to-nested signal adapter, so its output has never been validated against real project evidence. Advisory, non-voting.

Method class: `PLTS`

```python
def run_plts(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    plts = []
    cpi, spi = _evm(si)
    if cpi and spi:
        evm_min = min(cpi, spi)
        if evm_min >= 0.97:
            g, a, r = 0.90, 0.08, 0.02
        elif evm_min >= 0.95:
            g, a, r = 0.70, 0.25, 0.05
        elif evm_min >= 0.92:
            g, a, r = 0.15, 0.70, 0.15
        elif evm_min >= 0.90:
            g, a, r = 0.05, 0.65, 0.30
        elif evm_min >= 0.87:
            g, a, r = 0.02, 0.28, 0.70
        else:
            g, a, r = 0.02, 0.08, 0.90
        plts.append({"source": "EVM", "Green": g, "Amber": a, "Red": r})
    cusum = si.get("cusum")
    if cusum is not None:
        if cusum.get("breached"):
            plts.append({"source": "CUSUM", "Green": 0.02, "Amber": 0.13, "Red": 0.85})
        else:
            plts.append({"source": "CUSUM", "Green": 0.80, "Amber": 0.15, "Red": 0.05})
    doc = si.get("doc")
    if doc is not None:
        s = doc.get("score") or 0
        if s < 0.30:
            plts.append({"source": "DocRisk", "Green": 0.85, "Amber": 0.12, "Red": 0.03})
        elif s < 0.70:
            plts.append({"source": "DocRisk", "Green": 0.10, "Amber": 0.70, "Red": 0.20})
        else:
            plts.append({"source": "DocRisk", "Green": 0.03, "Amber": 0.17, "Red": 0.80})
    mc = si.get("mc")
    if mc is not None:
        p80 = mc.get("p80DeltaPct") or 0
        if p80 <= 5:
            plts.append({"source": "MC", "Green": 0.80, "Amber": 0.15, "Red": 0.05})
        elif p80 <= 10:
            plts.append({"source": "MC", "Green": 0.08, "Amber": 0.67, "Red": 0.25})
        else:
            plts.append({"source": "MC", "Green": 0.03, "Amber": 0.17, "Red": 0.80})

    if not plts:
        return insufficient("PLTS")

    n = len(plts)
    agg_g = sum(p["Green"] for p in plts) / n
    agg_a = sum(p["Amber"] for p in plts) / n
    agg_r = sum(p["Red"] for p in plts) / n
    status = ("Red" if agg_r >= agg_a and agg_r >= agg_g
              else "Amber" if agg_a >= agg_g else "Green")
    return {
        "method_class": "PLTS",
        "status_color": status,
        "p_green": int(js_round(agg_g * 100)),
        "p_amber": int(js_round(agg_a * 100)),
        "p_red": int(js_round(agg_r * 100)),
        "sources": plts,
        "evidence_metric": (
            f"P(Green)={int(js_round(agg_g * 100))}% · "
            f"P(Amber)={int(js_round(agg_a * 100))}% · "
            f"P(Red)={int(js_round(agg_r * 100))}%"
        ),
    }
```

---

## Plithogenic Sets

Purpose: Plithogenic Sets, category "Evidence Combination".

Activation state: DISABLED. Concept-only: implements no defensible version of the analytical structure its name claims. Non-executable in production, non-voting, excluded from every fusion input and every rollup. NEWLY WIRED: Newly wired and unvalidated: this module could not execute on the normal computation path before the flat-to-nested signal adapter, so its output has never been validated against real project evidence. Advisory, non-voting.

Method class: `Plithogenic_Sets`

```python
def run_plithogenic(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    attributes = []
    cpi, spi = _evm(si)
    if cpi and spi:
        evm_min = min(cpi, spi)
        state = "Green" if evm_min >= 0.95 else "Amber" if evm_min >= 0.90 else "Red"
        membership = 0.85 if evm_min >= 0.95 else 0.70 if evm_min >= 0.90 else 0.80
        contradiction = 0.0 if state == "Red" else 1.0 if state == "Green" else 0.5
        attributes.append({"name": "EVM", "state": state,
                           "membership": membership, "contradiction": contradiction})
    cusum = si.get("cusum")
    if cusum is not None:
        state = "Red" if cusum.get("breached") else "Green"
        attributes.append({"name": "CUSUM", "state": state, "membership": 0.88,
                           "contradiction": 0.0 if state == "Red" else 1.0})
    doc = si.get("doc")
    if doc is not None:
        s = doc.get("score") or 0
        state = "Red" if s >= 0.70 else "Amber" if s >= 0.30 else "Green"
        contradiction = 0.0 if state == "Red" else 1.0 if state == "Green" else 0.5
        attributes.append({"name": "DocRisk", "state": state, "membership": 0.75,
                           "contradiction": contradiction})
    mc = si.get("mc")
    if mc is not None:
        p80 = mc.get("p80DeltaPct") or 0
        state = "Red" if p80 > 10 else "Amber" if p80 > 5 else "Green"
        contradiction = 0.0 if state == "Red" else 1.0 if state == "Green" else 0.5
        attributes.append({"name": "MC", "state": state, "membership": 0.82,
                           "contradiction": contradiction})

    if not attributes:
        return insufficient("Plithogenic_Sets")

    red_s = amber_s = green_s = 0.0
    for a in attributes:
        w = a["membership"] * (1 - a["contradiction"] * 0.5)
        if a["state"] == "Red":
            red_s += w
        elif a["state"] == "Amber":
            amber_s += w
        else:
            green_s += w

    avg_c = sum(a["contradiction"] for a in attributes) / len(attributes)
    status = ("Red" if red_s >= amber_s and red_s >= green_s
              else "Amber" if amber_s >= green_s else "Green")
    return {
        "method_class": "Plithogenic_Sets",
        "status_color": status,
        "red_score": round2(red_s),
        "amber_score": round2(amber_s),
        "green_score": round2(green_s),
        "avg_contradiction": round2(avg_c),
        "contradiction_level": ("High" if avg_c > 0.6 else
                                "Moderate" if avg_c > 0.3 else "Low"),
        "attributes": attributes,
        "evidence_metric": (
            f"Plithogenic scores, Red: {_num_str(round2(red_s))} · "
            f"Amber: {_num_str(round2(amber_s))} · "
            f"Green: {_num_str(round2(green_s))} · "
            f"Contradiction: {int(js_round(avg_c * 100))}%"
        ),
    }
```

---

## Belief Rule Base

Purpose: Belief Rule Base, category "Evidence Combination".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. NEWLY WIRED: Newly wired and unvalidated: this module could not execute on the normal computation path before the flat-to-nested signal adapter, so its output has never been validated against real project evidence. Advisory, non-voting.

Method class: `Belief_Rule_Base`

```python
def run_brb(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    cpi, spi = _evm(si)
    cusum = si.get("cusum")
    breached = bool(cusum.get("breached")) if cusum is not None else False
    doc = si.get("doc")
    doc_score = (doc.get("score") or 0) if doc is not None else 0
    mc = si.get("mc")
    p80 = (mc.get("p80DeltaPct") or 0) if mc is not None else 0

    evm_state = (None if not cpi or not spi
                 else "Green" if min(cpi, spi) >= 0.95
                 else "Amber" if min(cpi, spi) >= 0.90 else "Red")
    doc_state = "Red" if doc_score >= 0.70 else "Amber" if doc_score >= 0.30 else "Green"
    mc_state = "Red" if p80 > 10 else "Amber" if p80 > 5 else "Green"

    rules = [
        {"id": "R1", "desc": "EVM Red + CUSUM breach",
         "condition": evm_state == "Red" and breached,
         "belief": {"Green": 0.02, "Amber": 0.08, "Red": 0.90}, "weight": 1.00},
        {"id": "R2", "desc": "EVM Red, no breach",
         "condition": evm_state == "Red" and not breached,
         "belief": {"Green": 0.05, "Amber": 0.25, "Red": 0.70}, "weight": 0.85},
        {"id": "R3", "desc": "EVM Amber + CUSUM breach",
         "condition": evm_state == "Amber" and breached,
         "belief": {"Green": 0.05, "Amber": 0.30, "Red": 0.65}, "weight": 0.90},
        {"id": "R4", "desc": "EVM Amber, doc Red",
         "condition": evm_state == "Amber" and not breached and doc_state == "Red",
         "belief": {"Green": 0.08, "Amber": 0.42, "Red": 0.50}, "weight": 0.80},
        {"id": "R5", "desc": "EVM Amber, doc not Red",
         "condition": evm_state == "Amber" and not breached and doc_state != "Red",
         "belief": {"Green": 0.10, "Amber": 0.70, "Red": 0.20}, "weight": 0.75},
        {"id": "R6", "desc": "EVM Green + CUSUM breach",
         "condition": evm_state == "Green" and breached,
         "belief": {"Green": 0.15, "Amber": 0.55, "Red": 0.30}, "weight": 0.85},
        {"id": "R7", "desc": "EVM Green, no breach, doc Green",
         "condition": evm_state == "Green" and not breached and doc_state == "Green",
         "belief": {"Green": 0.85, "Amber": 0.12, "Red": 0.03}, "weight": 0.90},
        {"id": "R8", "desc": "EVM Green, no breach, doc not Green",
         "condition": evm_state == "Green" and not breached and doc_state != "Green",
         "belief": {"Green": 0.50, "Amber": 0.40, "Red": 0.10}, "weight": 0.70},
    ]
    matched = [r for r in rules if r["condition"]]
    if not matched:
        # D1. Every rule above is conditioned on an EVM state, so no EVM means no rule fires.
        # The R0 fallback then supplied a near-uniform belief mass and a colour drawn from it.
        # A rule base with no activated rule has concluded nothing.
        return insufficient("Belief_Rule_Base")

    total_w = sum(r["weight"] for r in matched)
    agg_g = sum(r["belief"]["Green"] * r["weight"] for r in matched) / total_w
    agg_a = sum(r["belief"]["Amber"] * r["weight"] for r in matched) / total_w
    agg_r = sum(r["belief"]["Red"] * r["weight"] for r in matched) / total_w

    status = ("Red" if agg_r >= agg_a and agg_r >= agg_g
              else "Amber" if agg_a >= agg_g else "Green")
    return {
        "method_class": "Belief_Rule_Base",
        "status_color": status,
        "belief_green": int(js_round(agg_g * 100)),
        "belief_amber": int(js_round(agg_a * 100)),
        "belief_red": int(js_round(agg_r * 100)),
        "rules_matched": len(matched),
        "matched_rules": [{"id": m["id"], "desc": m["desc"], "weight": m["weight"]}
                          for m in matched],
        "mc_state": mc_state,
        "evidence_metric": (
            f"BRB belief: Green {int(js_round(agg_g * 100))}% · "
            f"Amber {int(js_round(agg_a * 100))}% · Red {int(js_round(agg_r * 100))}% · "
            f"{len(matched)} rule(s) activated"
        ),
    }
```

---

## Quantum Probability

Purpose: Quantum Probability, category "Evidence Combination".

Activation state: DISABLED. Concept-only: implements no defensible version of the analytical structure its name claims. Non-executable in production, non-voting, excluded from every fusion input and every rollup. NEWLY WIRED: Newly wired and unvalidated: this module could not execute on the normal computation path before the flat-to-nested signal adapter, so its output has never been validated against real project evidence. Advisory, non-voting.

Method class: `Quantum_Probability`

```python
def run_quantum_probability(si: dict, rand: Callable[[], float],
                            period_cutoff) -> dict[str, Any]:
    cpi, spi = _evm(si)
    cusum = si.get("cusum")
    doc = si.get("doc")
    if not (cpi and spi) and cusum is None and doc is None:
        # D1. The defaults below are not neutral: an absent EVM defaulted evm_min to 1.0, an
        # absent CUSUM to "no breach" and an absent doc risk to 0. All three read as good news,
        # so with no evidence at all the amplitudes resolved Green. Removed.
        return insufficient("Quantum_Probability")

    breached = bool(cusum.get("breached")) if cusum is not None else False
    doc_score = (doc.get("score") or 0) if doc is not None else 0

    evm_min = min(cpi, spi) if (cpi and spi) else 1.0
    p_green_evm = 0.80 if evm_min >= 0.95 else 0.10 if evm_min >= 0.90 else 0.05
    p_red_evm = 0.05 if evm_min >= 0.95 else 0.20 if evm_min >= 0.90 else 0.80
    p_green_cusum = 0.05 if breached else 0.80
    p_red_cusum = 0.85 if breached else 0.05
    p_green_doc = 0.85 if doc_score < 0.30 else 0.10 if doc_score < 0.70 else 0.03
    p_red_doc = 0.03 if doc_score < 0.30 else 0.20 if doc_score < 0.70 else 0.80

    alpha_green = math.sqrt((p_green_evm + p_green_cusum + p_green_doc) / 3)
    gamma_red = math.sqrt((p_red_evm + p_red_cusum + p_red_doc) / 3)

    red_count = sum(1 for p in (p_red_evm, p_red_cusum, p_red_doc) if p > 0.5)
    green_count = sum(1 for p in (p_green_evm, p_green_cusum, p_green_doc) if p > 0.5)
    theta = (abs(red_count - green_count) / 3) * math.pi
    interference = 2 * alpha_green * gamma_red * math.cos(theta)

    p_red_q = max(0, min(1, gamma_red * gamma_red + interference * 0.3))
    p_green_q = max(0, min(1, alpha_green * alpha_green - interference * 0.3))
    p_amber_q = max(0, 1 - p_red_q - p_green_q)

    itype = ("Constructive" if math.cos(theta) > 0.3
             else "Destructive" if math.cos(theta) < -0.3 else "Neutral")
    status = ("Red" if p_red_q >= p_amber_q and p_red_q >= p_green_q
              else "Amber" if p_amber_q >= p_green_q else "Green")
    deg = int(js_round(theta * 180 / math.pi))
    return {
        "method_class": "Quantum_Probability",
        "status_color": status,
        "p_green": int(js_round(p_green_q * 100)),
        "p_amber": int(js_round(p_amber_q * 100)),
        "p_red": int(js_round(p_red_q * 100)),
        "interference_type": itype,
        "interference_magnitude": round2(abs(interference)),
        "phase_angle_deg": deg,
        "alpha_green": round2(alpha_green),
        "gamma_red": round2(gamma_red),
        "evidence_metric": (
            f"Q-P(Green)={int(js_round(p_green_q * 100))}% · "
            f"Q-P(Amber)={int(js_round(p_amber_q * 100))}% · "
            f"Q-P(Red)={int(js_round(p_red_q * 100))}% · "
            f"{itype} interference · Phase {deg}°"
        ),
    }
```

---

## ABM Governance Layer

Purpose: ABM Governance Layer, category "Regulatory & Authority Thresholds".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. NEWLY WIRED: Newly wired and unvalidated: this module could not execute on the normal computation path before the flat-to-nested signal adapter, so its output has never been validated against real project evidence. Advisory, non-voting.

Method class: `ABM_Governance`

```python
def run_abm_governance(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not _guard(si):
        return insufficient("ABM_Governance")
    d = _derive_decision(si)
    return {
        "method_class": "ABM_Governance",
        "status_color": d["healthState"],
        "state": d["healthState"],
        "authority": d["authority"],
        "action": d["action"],
        "fairness_gate": d["fairnessGateRequired"],
        "evidence_metric": f"{d['healthState']}: {d['action']} ({d['authority']})",
    }
```

---

## FAR Threshold Monitor

Purpose: FAR Threshold Monitor, category "Regulatory & Authority Thresholds".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `FAR_Threshold`

```python
def run_far_threshold(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("bac", "cpi", "ev", "ac")):
        return insufficient("FAR_Threshold")
    if si["cpi"] == 0 or si["bac"] == 0:
        return insufficient("FAR_Threshold")  # JS Infinity/NaN fallthrough; refused
    eac = si["bac"] / si["cpi"]
    overrun = ((eac - si["bac"]) / si["bac"]) * 100
    threshold = 25
    headroom = threshold - overrun
    color = ("Green" if overrun <= 5 else "Yellow" if overrun <= 15
             else "Amber" if overrun <= 25 else "Red")
    return {
        "method_class": "FAR_Threshold",
        "status_color": color,
        "overrun_pct": round1(overrun),
        "far34_threshold_pct": threshold,
        "distance_to_threshold": round1(headroom),
        "far_reporting_required": overrun >= threshold,
        "evidence_metric": (
            f"FAR Part 34: {_js_str(round1(overrun))}% overrun, threshold {threshold}% ("
            + ("REPORTING REQUIRED" if overrun >= threshold
               else f"{_js_str(round1(headroom))}% headroom") + ")"
        ),
    }
```

---

## OMB A-11 Check

Purpose: OMB A-11 Check, category "Regulatory & Authority Thresholds".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `OMB_A11_Check`

```python
def run_omb_a11_check(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("bac", "cpi", "actualPctComplete")):
        return insufficient("OMB_A11_Check")
    if si["cpi"] == 0:
        return insufficient("OMB_A11_Check")  # JS Infinity; refused
    cpi_below = si["cpi"] < 0.90
    major = si["bac"] >= 10000000
    triggered = cpi_below and major
    eac = si["bac"] / si["cpi"]
    overrun = eac - si["bac"]
    color = ("Green" if not cpi_below else "Yellow" if si["cpi"] >= 0.92
             else "Amber" if si["cpi"] >= 0.88 else "Red")
    return {
        "method_class": "OMB_A11_Check",
        "status_color": color,
        "cpi_below_90": cpi_below,
        "major_program": major,
        "reporting_triggered": triggered,
        "projected_overrun": int(js_round(overrun)),
        "evidence_metric": (
            f"OMB A-11: CPI {_js_str(si['cpi'])}"
            + (": MANDATORY REPORTING TRIGGERED" if triggered
               else ": below threshold, monitor" if cpi_below else ": within threshold")
        ),
    }
```

---

## EVM Reporting Threshold

Purpose: EVM Reporting Threshold, category "Regulatory & Authority Thresholds".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `EVM_Reporting_Threshold`

```python
def run_evm_reporting_threshold(si: dict, rand: Callable[[], float],
                                period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("bac", "cpi", "spi")):
        return insufficient("EVM_Reporting_Threshold")
    if si["cpi"] == 0 or si["bac"] == 0:
        return insufficient("EVM_Reporting_Threshold")  # JS Infinity/NaN; refused
    cpi_b = si["cpi"] < 0.90
    spi_b = si["spi"] < 0.90
    both = cpi_b and spi_b
    eac = si["bac"] / si["cpi"]
    delta = ((eac - si["bac"]) / si["bac"]) * 100
    if not cpi_b and not spi_b:
        color = "Green"
    elif cpi_b != spi_b:
        color = "Yellow"
    elif both and delta <= 15:
        color = "Amber"
    else:
        color = "Red"
    return {
        "method_class": "EVM_Reporting_Threshold",
        "status_color": color,
        "cpi_breached": cpi_b,
        "spi_breached": spi_b,
        "both_breached": both,
        "eac_delta_pct": round1(delta),
        "evidence_metric": (
            f"EVM threshold: CPI {'BREACHED' if cpi_b else 'ok'}, "
            f"SPI {'BREACHED' if spi_b else 'ok'}, EAC +{_js_str(round1(delta))}%"
        ),
    }
```

---

## Contract Modification Frequency

Purpose: Contract Modification Frequency, category "Regulatory & Authority Thresholds".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: a raw modification count; not a frequency without a denominator

Method class: `Contract_Mod_Frequency`

```python
def run_contract_mod_frequency(si: dict, rand: Callable[[], float],
                               period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("changeOrderCount", "baselineContractSum", "revisedContractSum")):
        return insufficient("Contract_Mod_Frequency")
    growth = (((si["revisedContractSum"] - si["baselineContractSum"])
               / si["baselineContractSum"]) * 100 if si["baselineContractSum"] > 0 else 0)
    co = si["changeOrderCount"]
    if co >= 10 or growth >= 20:
        risk = "Red"
    elif co >= 6 or growth >= 10:
        risk = "Amber"
    elif co >= 3 or growth >= 5:
        risk = "Yellow"
    else:
        risk = "Green"
    is_derived = _derived(si, "changeOrderCount", "baselineContractSum")
    word = ("contracting officer review merits consideration" if risk == "Red"
            else "elevated modification frequency" if risk == "Amber"
            else "within normal range")
    return {
        "method_class": "Contract_Mod_Frequency",
        "status_color": risk,
        "co_count": co,
        "scope_growth_pct": round1(growth),
        "evidence_metric": (
            f"{_js_str(co)} contract modifications, {_js_str(round1(growth))}% scope growth, "
            + word
            + (" (estimated; upload Change Order log for precise figures)" if is_derived else "")
        ),
    }
```

---

## Multi-Objective Optimization

Purpose: Multi-Objective Optimization, category "Decision Optimization".

Activation state: DISABLED. Concept-only: implements no defensible version of the analytical structure its name claims. Non-executable in production, non-voting, excluded from every fusion input and every rollup.

Method class: `Multi_Objective_Optimization`

```python
def run_multi_objective(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "docRiskScore")):
        return insufficient("Multi_Objective_Optimization")
    norm_cpi = min(1, max(0, (si["cpi"] - 0.80) / 0.25))
    norm_spi = min(1, max(0, (si["spi"] - 0.80) / 0.25))
    norm_risk = 1 - (si.get("docRiskScore") or 0)
    pareto = round2((norm_cpi + norm_spi + norm_risk) / 3)
    objectives = sorted(
        [
            {"name": "Cost performance", "score": norm_cpi},
            {"name": "Schedule performance", "score": norm_spi},
            {"name": "Document risk", "score": norm_risk},
        ],
        key=lambda o: o["score"],
    )
    binding = objectives[0]
    color = ("Green" if pareto >= 0.75 else "Yellow" if pareto >= 0.55
             else "Amber" if pareto >= 0.35 else "Red")
    return {
        "method_class": "Multi_Objective_Optimization",
        "status_color": color,
        "pareto_score": pareto,
        "binding_constraint": binding["name"],
        "objectives": objectives,
        "evidence_metric": (
            f"Multi-objective score: {int(js_round(pareto * 100))}%, "
            f"binding constraint: {binding['name']} "
            f"(score {int(js_round(binding['score'] * 100))}%)"
        ),
    }
```

---

## Linear Programming

Purpose: Linear Programming, category "Decision Optimization".

Activation state: DISABLED. Concept-only: implements no defensible version of the analytical structure its name claims. Non-executable in production, non-voting, excluded from every fusion input and every rollup.

Method class: `Linear_Programming`

```python
def run_linear_programming(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("bac", "ev", "ac", "cpi")):
        return insufficient("Linear_Programming")
    remaining_work = si["bac"] - si["ev"]
    remaining_budget = si["bac"] - si["ac"]
    if remaining_budget <= 0:
        return {
            "method_class": "Linear_Programming",
            "status_color": "Red",
            "feasible": False,
            "evidence_metric": "No feasible solution: budget exhausted before project completion",
        }
    required = remaining_work / remaining_budget
    feasible = required <= 1.20
    optimal = required <= 1.00
    lp_score = min(1, _jsdiv(1.0, required)) if feasible else 0
    color = ("Green" if optimal else "Yellow" if required <= 1.05
             else "Amber" if required <= 1.15 else "Red")
    word = ("achievable at current performance" if optimal
            else "requires productivity improvement" if feasible
            else "budget infeasible, recovery plan needed")
    return {
        "method_class": "Linear_Programming",
        "status_color": color,
        "required_cpi_to_complete": _round3(required),
        "feasible": feasible,
        "optimal": optimal,
        "lp_score": round2(lp_score),
        "evidence_metric": (
            f"LP: requires CPI {_js_str(_round3(required))} to complete within budget, {word}"
        ),
    }
```

---

## Constraint Satisfaction Analysis

Purpose: Constraint Satisfaction Analysis, category "Decision Optimization".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: an explainable four-rule checklist, not a constraint-satisfaction solver

Method class: `Constraint_Satisfaction`

```python
def run_constraint_satisfaction(si: dict, rand: Callable[[], float],
                                period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "bac")):
        return insufficient("Constraint_Satisfaction")
    doc = si.get("docRiskScore") or 0
    constraints = [
        {"name": "Cost constraint (CPI ≥ 0.90)", "satisfied": si["cpi"] >= 0.90},
        {"name": "Schedule constraint (SPI ≥ 0.90)", "satisfied": si["spi"] >= 0.90},
        {"name": "Document risk (score < 0.70)", "satisfied": doc < 0.70},
        {"name": "FAR threshold (overrun < 25%)", "satisfied": si["cpi"] > 0.80},
    ]
    satisfied = sum(1 for c in constraints if c["satisfied"])
    violated = [c["name"] for c in constraints if not c["satisfied"]]
    rate = satisfied / len(constraints)
    color = ("Green" if rate >= 1.0 else "Yellow" if rate >= 0.75
             else "Amber" if rate >= 0.50 else "Red")
    return {
        "method_class": "Constraint_Satisfaction",
        "status_color": color,
        "satisfied": satisfied,
        "total": len(constraints),
        "violated_constraints": violated,
        "satisfaction_rate": int(js_round(rate * 100)),
        "evidence_metric": (
            f"{satisfied} of {len(constraints)} constraints satisfied"
            + (f"; violated: {', '.join(violated)}" if violated else "; all constraints met")
        ),
    }
```

---

## What-If Scenario Matrix

Purpose: What-If Scenario Matrix, category "Decision Optimization".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: four deterministic EAC variants; not an action-by-scenario matrix or optimiser

Method class: `WhatIf_Scenario_Matrix`

```python
def run_whatif_matrix(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    THE FIFTEEN DEFECTS, defect 13, applied to the second of the two computations it can name.

    The defect list identifies this one by code and by the name of its sibling, so both were
    read and both carried the same unguarded earned value domains: a guard at exactly zero, and
    nothing at all for a negative index, a negative budget, or earned value exceeding the budget
    at completion. The guards below are the same as the sibling's and refuse for the same
    reasons. Which of the two the audit meant does not change what either needed.
    """
    if not check_inputs(si, ("bac", "ev", "ac", "cpi", "spi")):
        return insufficient("WhatIf_Scenario_Matrix")
    if si["cpi"] <= 0 or si["spi"] <= 0:
        return insufficient(
            "WhatIf_Scenario_Matrix",
            "Cost or schedule performance is recorded as zero or below, which no remaining "
            "work can be divided by")
    if si["bac"] <= 0:
        return insufficient(
            "WhatIf_Scenario_Matrix",
            "No positive budget at completion is recorded to scale the scenarios against")
    if si["ev"] < 0 or si["ac"] < 0:
        return insufficient(
            "WhatIf_Scenario_Matrix",
            "Negative earned value or actual cost is not a measurable position to forecast from")
    if si["ev"] > si["bac"]:
        return insufficient(
            "WhatIf_Scenario_Matrix",
            "More value is recorded as earned than the budget at completion contains, so there "
            "is no remaining work to forecast")
    remaining = si["bac"] - si["ev"]
    scenarios = [
        {"name": "Optimistic (CPI recovers to 1.0)", "eac": si["ac"] + remaining * 1.00},
        {"name": "Base (current CPI continues)", "eac": si["bac"] / si["cpi"]},
        {"name": "Pessimistic (CPI degrades 5%)", "eac": si["bac"] / (si["cpi"] * 0.95)},
        {"name": "Recovery (CPI improves 5%)", "eac": si["bac"] / (si["cpi"] * 1.05)},
    ]
    base_eac = scenarios[1]["eac"]
    range_pct = int(js_round(((scenarios[2]["eac"] - scenarios[0]["eac"]) / si["bac"]) * 100))
    color = ("Green" if range_pct <= 5 else "Yellow" if range_pct <= 10
             else "Amber" if range_pct <= 20 else "Red")
    return {
        "method_class": "WhatIf_Scenario_Matrix",
        "status_color": color,
        "scenarios": [
            {"name": s["name"], "eac": int(js_round(s["eac"])),
             "delta_pct": round1(((s["eac"] - si["bac"]) / si["bac"]) * 100)}
            for s in scenarios
        ],
        "scenario_range_pct": range_pct,
        "base_eac": int(js_round(base_eac)),
        "evidence_metric": (
            f"Scenario range: {range_pct}% of BAC, "
            f"base EAC ${int(js_round(base_eac / 1000))}k, "
            f"worst ${int(js_round(scenarios[2]['eac'] / 1000))}k, "
            f"best ${int(js_round(scenarios[0]['eac'] / 1000))}k"
        ),
    }
```

---

## Decision Sensitivity Matrix

Purpose: Decision Sensitivity Matrix, category "Decision Optimization".

Activation state: DISABLED. Concept-only: implements no defensible version of the analytical structure its name claims. Non-executable in production, non-voting, excluded from every fusion input and every rollup.

Method class: `Decision_Sensitivity_Matrix`

```python
def run_decision_sensitivity(si: dict, rand: Callable[[], float],
                             period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "docRiskScore")):
        return insufficient("Decision_Sensitivity_Matrix")
    cpi_i = abs(1 - si["cpi"]) * 100
    spi_i = abs(1 - si["spi"]) * 100
    risk_i = (si.get("docRiskScore") or 0) * 50
    total = (cpi_i + spi_i + risk_i) or 1
    sensitivity = sorted(
        [
            {"driver": "Cost performance (CPI)", "impact": cpi_i,
             "pct": int(js_round(cpi_i / total * 100))},
            {"driver": "Schedule performance (SPI)", "impact": spi_i,
             "pct": int(js_round(spi_i / total * 100))},
            {"driver": "Document risk", "impact": risk_i,
             "pct": int(js_round(risk_i / total * 100))},
        ],
        key=lambda d: -d["impact"],
    )
    top = sensitivity[0]
    mx = top["impact"]
    color = ("Green" if mx <= 3 else "Yellow" if mx <= 7 else "Amber" if mx <= 12 else "Red")
    return {
        "method_class": "Decision_Sensitivity_Matrix",
        "status_color": color,
        "top_driver": top["driver"],
        "top_driver_pct": top["pct"],
        "sensitivity_matrix": sensitivity,
        "evidence_metric": (
            f"Decision most sensitive to: {top['driver']} ({top['pct']}% of decision weight); "
            f"a small change here most changes the governance recommendation"
        ),
    }
```

---

## Pareto Frontier Analysis

Purpose: Pareto Frontier Analysis, category "Decision Optimization".

Activation state: DISABLED. Concept-only: implements no defensible version of the analytical structure its name claims. Non-executable in production, non-voting, excluded from every fusion input and every rollup.

Method class: `Pareto_Frontier`

```python
def run_pareto_frontier(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "docRiskScore")):
        return insufficient("Pareto_Frontier")
    doc = si.get("docRiskScore") or 0
    cost_ok = si["cpi"] >= 0.95
    sched_ok = si["spi"] >= 0.95
    risk_ok = doc < 0.30
    dominated = not cost_ok and not sched_ok
    efficient = cost_ok and sched_ok and risk_ok
    tradeoff = (cost_ok != sched_ok) or (not risk_ok and (cost_ok or sched_ok))
    score = ((1 if cost_ok else si["cpi"] / 0.95)
             + (1 if sched_ok else si["spi"] / 0.95)
             + (1 if risk_ok else (1 - doc / 0.30))) / 3
    score = round2(min(1, score))
    color = ("Green" if efficient else "Yellow" if tradeoff
             else "Amber" if not dominated else "Red")
    evidence = ("Project is Pareto-efficient: all objectives met simultaneously" if efficient
                else "Project is Pareto-dominated: multiple objectives failing simultaneously"
                if dominated
                else "Trade-off required: improving one objective may affect another" if tradeoff
                else "Partial Pareto efficiency: some objectives met")
    return {
        "method_class": "Pareto_Frontier",
        "status_color": color,
        "pareto_efficient": efficient,
        "dominated": dominated,
        "tradeoff_required": tradeoff,
        "pareto_score": score,
        "evidence_metric": evidence,
    }
```

---

## Regret Minimization Index

Purpose: Regret Minimization Index, category "Decision Optimization".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `Regret_Minimization`

```python
def run_regret_minimization(si: dict, rand: Callable[[], float],
                            period_cutoff) -> dict[str, Any]:
    """
    RUN 7, AND THIS ONE ABSTAINS UNCONDITIONALLY.

    Minimax regret is defined by an action-by-scenario payoff matrix: what each course of action
    costs under each future state, for the decision actually in front of the reader. This
    platform holds no such matrix. The one below was nine literals and three literal state
    probabilities, so the three expected regrets were 11, 5 and 8 on every project and in every
    period, the minimum was always to investigate, and the two overrides could only move that to
    escalate. The known-answer run exhausted 3,721 cost and schedule index pairs from 0.70 to
    1.30 and found no pair that produced a healthy reading: a project twenty per cent ahead on
    both indices was still told to investigate, because the only branch that reads healthy was
    unreachable from any input.

    The corpus was searched for a governed payoff matrix before this was written, and there is
    none: no action-by-scenario structure exists anywhere in the repository outside these
    literals. Substituting different literals would repeat the fault at a different set of
    numbers, and building a real minimax-regret engine needs owner approval and a matrix that
    does not exist. So the module refuses and states which structure is missing.

    What this does NOT do is decide anything for a participant. The courses of action a
    participant chooses among were already outside this module's reach: a non-voting module is
    excluded from the recommendation text and the courses of action by the owner's settled
    decision, which this module has been subject to since Run 1, and it stays non-voting here.
    No new decision policy is introduced by this run.
    """
    return insufficient(
        "Regret_Minimization",
        "Insufficient data: no set of courses of action scored against defined future states is "
        "held for this project, so there is no worst case per course to compare and no course "
        "can be identified as carrying the smallest one. No ranking is offered in its place.",
        ABSTAIN_DECISION_STRUCTURE_ABSENT)
```

---
