# Group B — Recommendation and Governance

36 modules. Purpose: "what should be done and by whom." Source files:
`server/app/simulation/models_decision.py`, `models_gov.py`, `models_fuzzy.py`, `models_evc.py`.
Shared helpers documented once in `SHARED_MACHINERY.md`.

**Input-contract note (applies to the whole group, stated once here rather than per module):**
Unlike Group A, most Group B modules do **not** read flat `signalInputs` fields like `cpi`/`spi`
directly. Three different shapes share the registry's one `fn(si, rand, period_cutoff)` call
signature:
- B1.1, B1.2–B1.4 consume the **assembled project**: `si["signals"]` holding `{evm, mc, cusum,
  doc}` each with `.status` (and `cusum` additionally with `.breached`), and
  `si["simulationSignals"]["signal_array"]` holding per-module results with `.status_color`.
- B2.1 and B2.2–B2.9 consume the assembled signal keys directly from `si`: `si["evm"]`
  (`{cpi, spi}`), `si["mc"]` (`{p80DeltaPct}`), `si["cusum"]` (`{breached}`), `si["doc"]`
  (`{score}`), and for B1.1/B3.1, `si["decision"]` (`{state}`).
- B2.10–B2.20, B3.x, B4.x consume flat `signalInputs` (`cpi`/`spi`/`docRiskScore`/…), as Group A
  does.

This audit did not trace the assembly code that builds `si["signals"]`/`si["evm"]`/`si["mc"]`/
`si["cusum"]`/`si["doc"]` (it lives outside `server/app/simulation/`, in the caller that builds
`si` before `run_all`/`run_module` are invoked) — that assembly step is out of this audit's
registry-focused scope; each module's "Inputs" section below names the keys as read in the
simulation-layer code, not the upstream assembly.

---

## Conservative Dominance

Purpose: Conservative Dominance, category "Signal Synthesis".

Source (`models_decision.py`), including its private helpers (used only by this module and B3.1):

```python
def _signal_statuses(project: dict) -> dict:
    s = project.get("signals") or {}
    return {
        "evm": (s["evm"].get("status") if s.get("evm") is not None else None),
        "mc": (s["mc"].get("status") if s.get("mc") is not None else None),
        "cusum": (s["cusum"].get("status") if s.get("cusum") is not None else None),
        "doc": (s["doc"].get("status") if s.get("doc") is not None else None),
    }


def _count(statuses: dict, level: str) -> int:
    return sum(1 for v in statuses.values() if v == level)


def _classify_conflict(project: dict) -> str:
    s = _signal_statuses(project)
    reds = _count(s, "red")
    if reds >= 2:
        return "Multi-signal red-review"
    if project["signals"]["cusum"].get("breached") and s["doc"] == "green":
        return "Anomaly without narrative"
    if s["mc"] == "red" and s["evm"] != "red":
        return "Forecast ahead of status"
    if s["doc"] in ("amber", "red") and s["evm"] == "green":
        return "Leading document risk"
    if all(v == "green" for v in s.values()):
        return "Agreement: low risk"
    return "Mixed early warning"


def _derive_health_state(project: dict) -> str:
    s = _signal_statuses(project)
    reds = _count(s, "red")
    ambers = _count(s, "amber")
    signals = project.get("signals") or {}
    cusum = signals.get("cusum")
    cusum_breached = bool(cusum.get("breached")) if cusum is not None else False
    if reds == 0 and ambers == 0:
        return "Green"
    if reds >= 2 or (cusum_breached and s["mc"] == "red"):
        return "Red-review"
    return "Amber"


def _derive_decision(project: dict) -> dict:
    health = _derive_health_state(project)
    conflict = _classify_conflict(project)
    escalate = health in ("Red", "Red-review")

    if health == "Complete":
        action = "Project complete: proceed to close-out and any liability-period monitoring"
        authority = "Project manager / Controls lead"
        documentation = ("Close-out record; monitor through the defects-liability period "
                         "where applicable")
    elif health == "Green":
        action = "Routine monitoring"
        authority = "Project manager / Controls lead"
        documentation = "Monthly signal log entry"
    elif escalate:
        action = "Recovery-plan review and management escalation"
        authority = "Program director / PMO lead"
        documentation = ("Full signal package, assigned owner, rationale, response timeframe, "
                         "audit record")
    else:
        if conflict == "Forecast ahead of status":
            action = "Investigate forecast assumptions and mitigation options"
        elif conflict == "Anomaly without narrative":
            action = "Controls review: request explanation for unexplained trend drift"
        elif conflict == "Leading document risk":
            action = "Early-warning review; verify document evidence; update risk register"
        else:
            action = "Early-warning review; update risk register; set follow-up date"
        authority = "Project manager + Project controls lead"
        documentation = "Risk-register update, rationale, follow-up date"

    return {
        "healthState": health,
        "conflictType": conflict,
        "action": action,
        "authority": authority,
        "documentation": documentation,
        # THE FAIRNESS GATE IS REMOVED, NOT WIRED. It was `escalate and
        # si["fairnessSensitive"] is True`, and `fairnessSensitive` is not in
        # SIGNAL_INPUT_KEYS: no branch of extraction_merge writes it and documents.py never
        # supplies it, so on the server the condition has always been False and could not be
        # anything else... The KEY stays, always False, because assets/js/app.js reads
        # `d.fairnessGateRequired` to decide whether to render an acknowledgement checkbox and
        # whether to allow submit.
        "fairnessGateRequired": False,
    }


def _guard(project: dict) -> bool:
    signals = project.get("signals")
    return signals is not None and signals.get("cusum") is not None


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
        "evidence_metric": f"{d['healthState']} — {d['conflictType']}",
    }
```

**Inputs.** `si["signals"]["evm"|"mc"|"cusum"|"doc"]`, each with `.status` (and `cusum` with
`.breached`); `si["signals"]["cusum"]` must be present for the module to run at all
(`_guard`). None of these are flat `FIELD_KINDS` entries — they are the assembled per-source
signal package built upstream, not audited here.

**Availability.** Not determinable from `server/app/field_registry.py` alone since this consumes
an assembled structure, not raw extracted fields; whether `si["signals"]` is actually populated
on the server path depends on code outside `server/app/simulation/`.

**Literals:** none numeric — this module is pure conditional logic (string comparisons on status
labels "red"/"green"/"amber", lowercase, documented as deliberate: "classifyConflict and the
health-state fallback compare statuses in LOWERCASE... A capitalized 'Red' from a signal does not
count as red there. That is what the instrument executes; reproduced, not fixed.").

**Output / banding.** `state` (health state: "Green", "Amber", or "Red-review" — not the usual
Green/Amber/Red triad; note `status_color` is set to this same three/four-valued `healthState`
string directly, so "Red-review" would appear as a `status_color` value where other modules use
plain "Red"), `conflict` (one of six conflict-classification labels).

**Abstains** when `si["signals"]` is absent or has no `cusum` key (`_guard` fails) — documented as
the "refusing direction": the browser's `classifyConflict` dereferences
`project.signals.cusum.breached` unconditionally and **throws** in JavaScript on a missing
`cusum`; this port abstains instead.

---

## Weighted Voting

Purpose: Weighted Voting, category "Signal Synthesis".

Source (`models_gov.py`), with its private `_vote_bucket` helper (documented in
`SHARED_MACHINERY.md`, quoted again here as it is central to this module's logic):

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

**Inputs.** `si["signals"]["mc"|"cusum"|"doc"|"decision"]` (`.status`/`.state`) and
`si["simulationSignals"]["signal_array"]` (a list of already-computed module results, each with
`.status_color`) — this module votes over the *outputs of other modules*, not raw signalInputs.

**Availability.** Depends on upstream assembly of `signals`/`simulationSignals`, not on
`field_registry.py`.

**Literals:** category weights `cat1=1.5, cat4=1.0, cat7=0.6, cat9=1.5` — labelled by legacy
category names ("cat1"/"cat4"/"cat7"/"cat9", the retired numbering scheme per
`NAMING_AUTHORITY.md`), no comment explaining why these four weight values specifically.

**Output / banding.** `votes` (weighted tally per bucket), `dominant_pct`; `status_color` is
whichever bucket has the highest weighted vote, ties won by the later-iterated key ("JS reduce
with `>` keeps the LATER key on ties", documented and reproduced deliberately).

**Abstains** when total weighted votes across all sources is 0 (nothing to vote on).

---

## Majority Rules

Purpose: Majority Rules, category "Signal Synthesis".

Source (`models_gov.py`):

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

**Inputs.** Same signal package as Weighted Voting, minus the `decision` vote (this module does
not count `si["signals"]["decision"]`).

**Availability.** Same caveat as Weighted Voting.

**Literals:** none numeric beyond the vote-tie-break iteration order (documented, "JS reduce with
`>` keeps the LATER key on ties").

**Output / banding.** `counts` (unweighted tally), `majority_pct`, `total_votes`.

**Abstains** when total votes is 0.

---

## Worst-N-of-M

Purpose: Worst-N-of-M, category "Signal Synthesis".

Source (`models_gov.py`):

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
    if not all_statuses:
        return insufficient("Worst_N_of_M")
    red_count = sum(1 for st in all_statuses if st and "Red" in st)
    amber_count = sum(1 for st in all_statuses if st == "Amber")
    m_total = len(all_statuses)
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

**Inputs.** Same signal package, minus `decision`.

**Availability.** Same caveat.

**Literals:** trigger fractions `0.3` (Red threshold, ceiling) and `0.4` (Amber threshold,
ceiling) of total module count — no comment on why 30%/40%.

**Output / banding.** `red_count`, `amber_count`, `total_modules`; note this module can return
"Yellow" (any Red present but below the 30% threshold) as a *fourth* band distinct from
Green/Amber/Red.

**Abstains** when `all_statuses` is empty.

---

## Dempster-Shafer

Purpose: Dempster-Shafer, category "Evidence Combination".

Source (`models_gov.py`):

```python
def run_dst(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    ex = si
    sources: list[dict] = []

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

    max_state = "Green"
    for b in ("Amber", "Red"):
        max_state = max_state if result[max_state] > result[b] else b

    decision = ex.get("decision")
    conservative = decision.get("state") if decision is not None else None
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

**Inputs.** `si["evm"]` (`{cpi, spi}`), `si["mc"]` (`{p80DeltaPct}`), `si["cusum"]`
(`{breached}`), `si["doc"]` (`{score}`), `si["decision"]` (`{state}`, only used for the
`agrees_with_conservative` comparison, not for fusion itself).

**Availability.** These are the assembled-signal-package keys, not flat `field_registry.py`
entries; availability depends on upstream assembly outside this audit's scope.

**Literals, exhaustively — sixteen fixed belief-mass quadruples, one per signal per band, plus the
vacuous `{0.25×4}` fallback used when a signal is present-but-uninformative:**
- EVM arm: `{0.80,0.10,0.05,0.05}` (evm_min≥0.95), `{0.10,0.70,0.15,0.05}` (≥0.90),
  `{0.05,0.15,0.75,0.05}` (else) — no comment/citation for these specific probabilities.
- Forecast (mc) arm: `{0.75,0.15,0.05,0.05}` (p80≤5), `{0.10,0.65,0.20,0.05}` (≤10),
  `{0.05,0.10,0.80,0.05}` (else) — no comment.
- CUSUM arm: `{0.75,0.15,0.05,0.05}` (no breach), `{0.05,0.15,0.75,0.05}` (breach) — no comment.
- DocRisk arm: `{0.75,0.15,0.05,0.05}` (score<0.30), `{0.10,0.70,0.15,0.05}` (<0.70),
  `{0.05,0.15,0.75,0.05}` (else) — no comment.
- Vacuous fallback (each of the four arms, when the underlying signal is *present as an object*
  but insufficiently informative, e.g. `evm` present without both `cpi` and `spi`):
  `{0.25,0.25,0.25,0.25}` — a maximally uninformative mass, explicitly discussed in a code comment
  as the source of a documented past defect (D1): the four vacuous masses used to combine with a
  real Green mass from the doc arm's absent→0→Green branch and always resolved Green with no
  evidence at all; fixed by the whole-module early abstention added above it.
- `conflict_level` thresholds `>0.3` High, `>0.1` Moderate, else Low — no comment.

**Output / banding.** `belief_green/amber/red/unknown` (Dempster-combined masses),
`conflict_mass`/`conflict_level`, `agrees_with_conservative` (compares fused verdict to a prior
"conservative" decision state), `status_color` from whichever of Green/Amber/Red has the highest
combined mass (ties broken toward the later-checked band, i.e. Red beats Amber beats Green on a
tie, per the `for b in ("Amber","Red")` loop).

**Abstains** when none of the four evidence sources carry real information: `not (cpi and spi)`
and `mc`/`cusum`/`doc` all `None` — the fix documented in the D1 code comment above.

---

## Rough Sets

Purpose: Rough Sets, category "Evidence Combination".

Source (`models_evc.py`), with its private `_evm` helper:

```python
def _evm(si):
    evm = si.get("evm")
    cpi = evm.get("cpi") if evm is not None else None
    spi = evm.get("spi") if evm is not None else None
    return cpi, spi


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

**Inputs.** `si["evm"]`, `si["mc"]`, `si["cusum"]`, `si["doc"]` — same assembled-signal shape as
B2.1, minus `decision`.

**Availability.** Same upstream-assembly caveat.

**Literals:** EVM banding `>=0.95/>=0.90`; MC banding `<=5/<=10`; Doc banding `<0.30/<0.70` — same
cut points as B2.1's per-arm bands, reused here for hard classification instead of soft mass.
Lower-approximation threshold `> 0.75` (fraction of signals agreeing) — no comment.

**Output / banding.** Rough-set `lower_approximation`/`upper_approximation`/`boundary_region`
over {Green, Amber, Red}, textual `classification`.

**Abstains** when no signal (`evm`, `mc`, `cusum`, `doc`) is present at all — documented D1 fix
(previously an `or 1` denominator fallback produced a spurious "Indeterminate Amber" from zero
evidence).

---

## Neutrosophic Logic

Purpose: Neutrosophic Logic, category "Evidence Combination".

Source (`models_evc.py`):

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

**Inputs.** Same assembled-signal shape (`evm`, `mc`, `cusum`, `doc`).

**Availability.** Same upstream-assembly caveat.

**Literals:** twelve fixed `(T, I, F)` truth/indeterminacy/falsity triples, one per signal per
band (e.g. EVM-Green `0.85/0.10/0.05`, CUSUM-breach `0.90/0.05/0.05`, DocRisk-Green
`0.85/0.10/0.05`, etc.) — no comment/citation for any of the twelve. Status escalation:
`red_count >= 2` → Red, `amber_count >= 2` → Amber (a raw count threshold, not a fraction) — no
comment. Indeterminacy override: `i > 0.30` forces at least Amber. `indeterminacy_level`
thresholds `>0.30` High, `>0.15` Moderate, else Low — no comment.

**Output / banding.** `T`/`I`/`F` (normalized truth/indeterminacy/falsity, combined by a
probabilistic-sum rule for T and a product rule for I and F), `indeterminacy_level`,
`signal_components` (the raw per-source triples).

**Abstains** when no `components` (i.e. `evm`, `mc`, `cusum`, `doc` all absent/insufficient).

---

## Interval Fuzzy Sets

Purpose: Interval Fuzzy Sets, category "Evidence Combination".

Source (`models_evc.py`), with its private membership-function helpers:

```python
def _mem_amber(v):
    if v <= 0.85 or v >= 0.98:
        return 0
    if v <= 0.92:
        return (v - 0.85) / (0.92 - 0.85)
    return (0.98 - v) / (0.98 - 0.92)


def _mem_red(v):
    if v >= 0.92:
        return 0
    if v <= 0.85:
        return 1
    return (0.92 - v) / (0.92 - 0.85)


def _mem_green(v):
    if v <= 0.92:
        return 0
    if v >= 0.97:
        return 1
    return (v - 0.92) / (0.97 - 0.92)


def _mem_interval(fn, lo, hi):
    a, b = fn(lo), fn(hi)
    return [min(a, b), max(a, b)]


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

(`fmt` and `_num_str` are small local formatting helpers, omitted here for brevity as
non-computational.)

**Inputs.** `si["evm"]["cpi"]`/`["spi"]` only (this module does not read `mc`, `cusum`, or `doc`
at all, unlike its siblings).

**Availability.** Same upstream-assembly caveat.

**Literals:** membership-function breakpoints `0.85/0.92/0.97/0.98` (piecewise-linear triangular
membership for Amber/Red/Green bands over CPI/SPI value) — no comment on these specific
breakpoints. Uncertainty widths `ev_unc = 0.02`, `ac_unc = 0.01` (perturbation applied to CPI only,
not SPI — CPI's interval is `±(ev_unc+ac_unc)=±0.03`, SPI's is `±ev_unc=±0.02` only) — no comment
explaining the asymmetry or the specific magnitudes. `uncertainty_level` thresholds `>0.3` High,
`>0.15` Moderate — no comment.

**Output / banding.** `green_interval`/`amber_interval`/`red_interval` (aggregated membership
interval bounds), `uncertainty_width`, `uncertainty_level`; status from whichever band's interval
midpoint is highest.

**Abstains** when neither `cpi` nor `spi` is available.

---

## Z-numbers

Purpose: Z-numbers, category "Evidence Combination".

Source (`models_evc.py`):

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

**Inputs.** Same assembled-signal shape (`evm`, `cusum`, `doc`, `mc`).

**Availability.** Same upstream-assembly caveat.

**Literals — four fixed "reliability" (Z-number second component) values, one per source, with no
provenance:** EVM `0.85`, CUSUM `0.90`, DocRisk `0.65`, MonteCarlo `0.88` — no comment or citation
for any of these. Per-source banding cut points reuse the same values seen in B2.1/B2.2 (EVM
`0.95/0.90`, Doc `0.70/0.30`, MC `10/5`).

**Output / banding.** Reliability-weighted sums per band, `avg_reliability`, raw `signals` list.

**Abstains** when no source is present.

---

## PLTS

Purpose: PLTS, category "Evidence Combination". (Probabilistic Linguistic Term Sets.)

Source (`models_evc.py`):

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

**Inputs.** Same assembled-signal shape (`evm`, `cusum`, `doc`, `mc`).

**Availability.** Same upstream-assembly caveat.

**Literals — this module has the densest literal surface in the audit: six EVM bands (each a
Green/Amber/Red probability triple), plus two CUSUM, three DocRisk and three MC-band triples, 14
triples (42 numbers) in total, none commented or cited.** EVM bands alone: `0.97→(.90,.08,.02)`,
`0.95→(.70,.25,.05)`, `0.92→(.15,.70,.15)`, `0.90→(.05,.65,.30)`, `0.87→(.02,.28,.70)`,
else `(.02,.08,.90)`.

**Output / banding.** Averaged per-band probabilities across contributing sources
(`p_green/p_amber/p_red`), raw `sources` list.

**Abstains** when no source present.

---

## Plithogenic Sets

Purpose: Plithogenic Sets, category "Evidence Combination".

Source (`models_evc.py`):

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

**Inputs.** Same assembled-signal shape (`evm`, `cusum`, `doc`, `mc`).

**Availability.** Same upstream-assembly caveat.

**Literals:** per-source fixed "membership" degrees: EVM `0.85/0.70/0.80` (by band), CUSUM
`0.88` (constant regardless of band), DocRisk `0.75` (constant), MC `0.82` (constant) — no
comment; contradiction degrees are derived from the band (`1.0` Green, `0.5` Amber, `0.0` Red) by
a fixed rule, and the weight formula `membership * (1 - contradiction * 0.5)` uses an uncommented
`0.5` discount factor. `contradiction_level` thresholds `>0.6` High, `>0.3` Moderate — no comment.

**Output / banding.** `red_score`/`amber_score`/`green_score`, `avg_contradiction`,
`contradiction_level`, raw `attributes`.

**Abstains** when no source present.

---

## Belief Rule Base

Purpose: Belief Rule Base, category "Evidence Combination".

Source (`models_evc.py`):

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

**Inputs.** Same assembled-signal shape; note `mc_state` is computed but **the eight rules never
reference it** — Monte Carlo's P80 delta only ever appears in the output as an unused-by-rules
`mc_state` field, not as a rule condition.

**Availability.** Same upstream-assembly caveat.

**Literals:** eight fixed rules, each with a hardcoded belief triple and a hardcoded "weight"
(`1.00, 0.85, 0.90, 0.80, 0.75, 0.85, 0.90, 0.70`) — no comment or citation for any rule's belief
values or weight. Banding cut points reused from EVM/doc/MC (`0.95/0.90`, `0.70/0.30`, `10/5`).

**Output / banding.** Weighted-average belief (`belief_green/amber/red`, weighted by rule
`weight` among matched rules), `rules_matched`, `matched_rules`, `mc_state` (unused by the rule
logic itself).

**Abstains** when no rule's condition matches, which — since every rule requires a determinate
`evm_state` — happens whenever `cpi`/`spi` are unavailable (documented D1 fix: previously an "R0"
fallback rule fired instead).

---

## Quantum Probability

Purpose: Quantum Probability, category "Evidence Combination".

Source (`models_evc.py`):

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

**Inputs.** Same assembled-signal shape (`evm`, `cusum`, `doc`; `mc` is **not** read by this
module at all despite the shared signal package usually including it).

**Availability.** Same upstream-assembly caveat.

**Literals — the densest set of unexplained numeric constants in Group B, framed as a "quantum"
interference model over fixed classical probabilities:**
- Nine fixed per-band probabilities: `p_green_evm ∈ {0.80,0.10,0.05}`,
  `p_red_evm ∈ {0.05,0.20,0.80}`, `p_green_cusum ∈ {0.05,0.80}`, `p_red_cusum ∈ {0.85,0.05}`,
  `p_green_doc ∈ {0.85,0.10,0.03}`, `p_red_doc ∈ {0.03,0.20,0.80}` — no comment.
- `alpha_green`/`gamma_red` computed as `sqrt(mean of three probabilities)` — the "amplitude" of a
  quantum-probability model requires this square-root convention, but the choice to average three
  heterogeneous per-source probabilities before taking a square root is not justified by any
  comment or citation to an actual quantum-cognition model.
- Interference phase `theta = (|red_count - green_count| / 3) * pi` — the divisor `3` and
  radian-scaling-by-pi convention are uncommented.
- `interference * 0.3` — the 0.3 damping factor scaling how much interference perturbs
  `p_red_q`/`p_green_q` has no comment.
- `interference_type` thresholds `cos(theta) > 0.3` Constructive, `< -0.3` Destructive — no
  comment.

**Output / banding.** `p_green/p_amber/p_red` (quantum-probability-inspired composite),
`interference_type`, `interference_magnitude`, `phase_angle_deg`, `alpha_green`, `gamma_red`.

**Abstains** when `evm` (both cpi and spi), `cusum`, and `doc` are all absent — documented D1 fix
(previously all three defaulted to good-news values and resolved Green from zero evidence).

---

## Pythagorean Fuzzy Sets

Purpose: Pythagorean Fuzzy Sets, category "Evidence Combination".

Source (`models_fuzzy.py`):

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

**Inputs.** `cpi`, `spi`, `docRiskScore` — **flat signalInputs**, unlike B2.1–B2.9's assembled
signal package. All required.

**Availability.** All emittable per `FIELD_KINDS`.

**Literals:** membership breakpoints `0.85`/`0.95` and normalizing divisor `0.15` (used for both
mu and nu) — no comment. Doc-risk adjustment coefficient `0.3` (applied both to shrink mu and
grow nu) — no comment. Banding `>=0.3/0.0/-0.3` — no comment.

**Output / banding.** `membership`/`non_membership`/`hesitancy` (Pythagorean fuzzy triple, with
the Pythagorean constraint `mu²+nu²≤1` enforced by renormalization).

**Abstains** on missing `cpi`/`spi`/`docRiskScore`.

---

## Picture Fuzzy Sets

Purpose: Picture Fuzzy Sets, category "Evidence Combination".

Source (`models_fuzzy.py`):

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

**Inputs.** `cpi`, `spi`, `docRiskScore` (flat, required).

**Availability.** All emittable.

**Literals:** same `0.85/0.95/0.15` breakpoints as Pythagorean Fuzzy. Cap `0.95` on both positive
and negative membership. Doc-risk scale `0.5` (applied to negative only, asymmetric with
Pythagorean's symmetric `0.3`). Neutral formula `max(0, 0.6 - positive - negative) * 0.3` — both
`0.6` and `0.3` uncommented. Banding `>=0.30/0.00/-0.30` — same as Pythagorean.

**Output / banding.** `positive`/`neutral`/`negative`/`refusal` (the four picture-fuzzy-set
components).

**Abstains** on missing `cpi`/`spi`/`docRiskScore`.

---

## Hesitant Fuzzy Sets

Purpose: Hesitant Fuzzy Sets, category "Evidence Combination".

Source (`models_fuzzy.py`):

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

**Inputs.** `cpi`, `spi` (flat, required; no `docRiskScore` here unlike its two siblings above).

**Availability.** Both emittable.

**Literals:** same `0.85/0.15` breakpoint. Banding `>=0.7/0.5/0.3` — different scale than
Pythagorean/Picture (which band on a signed `-0.3..0.3` score), since this module's `score` is an
average of three `[0,1]` memberships, not a difference.

**Output / banding.** `memberships` (three-element hesitant fuzzy set: min, max, and midpoint
membership), `average_membership`, `hesitancy_degree`.

**Abstains** on missing `cpi`/`spi`.

---

## Type-2 Fuzzy Sets

Purpose: Type-2 Fuzzy Sets, category "Evidence Combination".

Source (`models_fuzzy.py`):

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

**Inputs.** `cpi`, `spi` (flat, required).

**Availability.** Both emittable.

**Literals:** `0.85/0.15` breakpoint again. `uncertainty = |cpi-spi| * 2` — the `2` scale factor
uncommented. `uncertainty * 0.5` spread around `primary` — no comment. Banding: `centroid>=0.7 and
footprint<=0.2` Green (a compound condition, unusual among these modules), `>=0.5` Yellow, `>=0.3`
Amber, else Red — no comment.

**Output / banding.** `lower_membership`/`upper_membership`/`centroid`/`footprint_of_uncertainty`
(type-2 fuzzy interval around the CPI/SPI-derived primary membership).

**Abstains** on missing `cpi`/`spi`.

---

## Maximum Entropy

Purpose: Maximum Entropy, category "Evidence Combination".

Source (`models_fuzzy.py`):

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

**Inputs.** `cpi`, `spi`, `docRiskScore` (flat, required).

**Availability.** All emittable.

**Literals — despite the name "Maximum Entropy," the four-way probability vector is a fixed
lookup table by EVM band, not fit by any entropy-maximization procedure:** Green-band raw vector
`(0.70,0.20,0.07,0.02)`, Amber-band `(0.20,0.50,0.25,0.05)`, Red-band `(0.05,0.20,0.60,0.15)`
(labels Green/Yellow/Amber/Red in that array order) — no comment or citation. Floor `0.01` on each
raw value before normalizing. Doc-risk nudges: `probs[2] += doc*0.2`, `probs[3] += doc*0.1`, capped
at `0.95` — no comment.

**Output / banding.** `probabilities` (normalized, doc-adjusted four-way distribution), `entropy`
(Shannon entropy normalized by `log2(4)`, i.e. the maximum possible entropy for 4 outcomes — this
is a genuine information-theoretic computation applied to the fixed lookup vector, not to any
fitted or measured distribution). `status_color` is whichever band has the highest probability.

**Abstains** on missing `cpi`/`spi`/`docRiskScore`.

---

## Possibility Theory

Purpose: Possibility Theory, category "Evidence Combination".

Source (`models_fuzzy.py`):

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
    for b in list(possibility)[1:]:
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

**Inputs.** `cpi`, `spi`, `docRiskScore` (flat, required).

**Availability.** All emittable.

**Literals:** three different breakpoints per band (`0.85/0.10` Green, `0.88/0.10` Amber,
`0.92/0.10` Red) — all uncommented, and the divisor `0.10` differs from most other B2 modules'
`0.15`. Doc-risk scale factors `0.5` (Green, subtractive), `0.3` (Amber, additive), `0.4` (Red,
additive) — three different uncommented coefficients. Necessity offset `-0.3` (flat subtraction
from possibility, floored at 0) — a textbook possibility/necessity duality shape but the specific
`0.3` gap is uncommented.

**Output / banding.** `possibility`/`necessity` per band; `status_color` is the band with highest
possibility, ties toward the later-checked key.

**Abstains** on missing `cpi`/`spi`/`docRiskScore`.

---

## Spherical Fuzzy Sets

Purpose: Spherical Fuzzy Sets, category "Evidence Combination".

Source (`models_fuzzy.py`):

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

**Inputs.** `cpi`, `spi`, `docRiskScore` (flat, required).

**Availability.** All emittable.

**Literals:** breakpoints `0.82/0.98/0.18` — different again from every sibling module (Pythagorean
used `0.85/0.95/0.15`, Possibility used three different sets). No comment for any of the choices
across the whole B2.10-B2.20 family, and no comment explaining why each fuzzy-set variant uses
slightly different breakpoints for what is nominally the same CPI/SPI evidence. Doc-risk scale
`0.5`. Banding `>=0.4/0.1/-0.2` — no comment.

**Output / banding.** `mu`/`nu`/`pi` (spherical fuzzy membership/non-membership/hesitancy,
constraint `mu²+nu²≤1` enforced by renormalization), `score` (mu − nu).

**Abstains** on missing `cpi`/`spi`/`docRiskScore`.

---

## Fermatean Fuzzy Sets

Purpose: Fermatean Fuzzy Sets, category "Evidence Combination".

Source (`models_fuzzy.py`):

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

**Inputs.** `cpi`, `spi` (flat, required — no `docRiskScore` here).

**Availability.** Both emittable.

**Literals:** breakpoints `0.80/1.00/0.20`. Renormalization decay `0.95` per loop iteration
(applied to both mu and nu until the Fermatean constraint `mu³+nu³≤1` holds) — no comment; the
`0.95` decay rate and loop-based (rather than closed-form) renormalization is noted in the file's
module docstring as "reproduced verbatim — IEEE doubles make the iteration count identical in
both languages," i.e. its *reproducibility* is documented, not its provenance. Banding
`>=0.35/0.05/-0.25` — no comment.

**Output / banding.** `mu`/`nu`/`pi` (Fermatean fuzzy triple, cubic constraint).

**Abstains** on missing `cpi`/`spi`.

---

## MARCOS Ranking

Purpose: MARCOS Ranking, category "Evidence Combination".

Source (`models_fuzzy.py`), calling the shared `_jsdiv` (documented in `SHARED_MACHINERY.md`):

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

**Inputs.** `cpi`, `spi`, `docRiskScore` (flat, required).

**Literals:** three criteria's ideal/anti-ideal reference points and weights: CPI
`ideal=1.05, anti=0.80, weight=0.40`; SPI `ideal=1.05, anti=0.80, weight=0.35`; DocRisk (inverted)
`ideal=1.00, anti=0.30, weight=0.25` (weights sum to 1.0) — no comment or citation for any of the
nine numbers. Banding `>=0.65/0.50/0.35` — no comment. **Division-by-zero handling is
documented as deliberate** (module docstring: "MARCOS's score formula divides by f_ideal and
f_anti; at the extremes JavaScript's Infinity arithmetic yields a finite 0, reproduced via
`_jsdiv` rather than refused" — so this module can never abstain from its own arithmetic, only
from missing inputs).

**Output / banding.** `marcos_score`, `utility_ideal`.

**Abstains** on missing `cpi`/`spi`/`docRiskScore`.

---

## CRITIC-TOPSIS

Purpose: CRITIC-TOPSIS, category "Evidence Combination".

Source (`models_fuzzy.py`):

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

**Inputs.** `cpi`, `spi`, `docRiskScore` (flat, required). **Weights are data-derived (CRITIC
method: weight ∝ deviation from the mean of the three criteria), not fixed literals** — the one
module in this family that computes its own weighting rather than hardcoding it.

**Literals:** ideal/anti-ideal reference points `ideal=[1.05,1.05,1.00]`, `anti=[0.80,0.80,0.30]`
— the same CPI/SPI `1.05/0.80` and DocRisk `1.00/0.30` reference points MARCOS uses, again
uncommented. `0.0001` epsilon in the denominator to avoid division by zero — no comment. Banding
`>=0.65/0.50/0.35` — identical cut points to MARCOS.

**Output / banding.** `topsis_score`, `distance_ideal`/`distance_anti` (Euclidean distances to
the ideal and anti-ideal reference points, CRITIC-weighted).

**Abstains** on missing `cpi`/`spi`/`docRiskScore`.

---

## Hypersoft Sets

Purpose: Hypersoft Sets, category "Evidence Combination".

Source (`models_fuzzy.py`), including its private lookup table (used only here):

```python
_HYPERSOFT = {
    "good-good-low": 0.90, "good-good-medium": 0.75, "good-good-high": 0.55,
    "good-fair-low": 0.70, "good-fair-medium": 0.55, "good-fair-high": 0.40,
    "fair-good-low": 0.70, "fair-good-medium": 0.55, "fair-good-high": 0.40,
    "fair-fair-low": 0.55, "fair-fair-medium": 0.40, "fair-fair-high": 0.30,
    "good-poor-low": 0.50, "poor-good-low": 0.50, "poor-poor-low": 0.30,
    "poor-fair-low": 0.35, "fair-poor-low": 0.35,
    "good-poor-medium": 0.35, "poor-good-medium": 0.35,
    "poor-poor-medium": 0.20, "poor-poor-high": 0.10,
    "fair-poor-high": 0.20, "poor-fair-high": 0.20,
    "good-poor-high": 0.25, "poor-good-high": 0.25,
}


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

**Inputs.** `cpi`, `spi`, `docRiskScore` (flat, required).

**Literals:** the discretization cut points `cpi/spi < 0.90`/`< 0.95` (poor/fair/good) and
`doc > 0.70`/`> 0.30` (high/medium/low) — uncommented; and a **24-entry lookup table of scores**
for the 3×3×3=27 possible combinations (three keys are absent from the table and fall back to a
literal default `0.35`) — none of the 24 scores carry any comment or citation. Banding
`>=0.70/0.50/0.30` — no comment.

**Output / banding.** `attribute_combination` (the three-way discretized key), `score` (direct
lookup, or `0.35` default for the three uncovered combinations).

**Abstains** on missing `cpi`/`spi`/`docRiskScore`.

---

## ABM Governance Layer

Purpose: ABM Governance Layer, category "Regulatory & Authority Thresholds".

Source (`models_decision.py`) — reuses the same `_guard`/`_derive_decision` machinery as
Conservative Dominance (B1.1), quoted in full there; only the wrapper differs:

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

**Inputs.** Identical to B1.1: `si["signals"]["evm"|"mc"|"cusum"|"doc"]`.

**Availability.** Same upstream-assembly caveat as B1.1.

**Literals:** none numeric — pure conditional routing (see B1.1's `_derive_decision` for the full
logic). The one literal-like value is `fairness_gate` which is **hardcoded `False` always** — see
the extensive code comment quoted under B1.1 explaining that the field is a dead switch kept only
for response-shape compatibility with a frontend field (`d.fairnessGateRequired`) that this task
does not touch.

**Output / banding.** `state` (same `healthState` triad as B1.1), `authority` (one of "Project
manager / Controls lead", "Program director / PMO lead", "Project manager + Project controls
lead" — text, not a numeric literal), `action` (free text per branch), `fairness_gate` (always
`False`).

**Abstains** when `si["signals"]["cusum"]` is absent, identical guard to B1.1.

---

## FAR Threshold Monitor

Purpose: FAR Threshold Monitor, category "Regulatory & Authority Thresholds".

Source (`models_gov.py`):

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

**Inputs.** `bac`, `cpi`, `ev`, `ac` (flat, required — `ev`/`ac` checked but unused in the
formula body, same pattern as elsewhere).

**Availability.** All emittable.

**Literals:** `threshold = 25` — presented as "FAR34 threshold" (a citation to Federal Acquisition
Regulation Part 34/Subpart 34.2 reporting triggers, named in the evidence text and field name, but
the value itself carries no comment tying it to an actual regulatory citation or paragraph
number). Banding `<=5/15/25` — no comment (25 doubles as both the "reporting required" trigger and
the Red color threshold, which the code makes coincide but does not state as deliberate).

**Output / banding.** `overrun_pct`, `far34_threshold_pct` (echoes the fixed `25`),
`distance_to_threshold`, `far_reporting_required` (boolean at the 25% mark).

**Abstains** on missing fields, `cpi == 0`, or `bac == 0`.

---

## OMB A-11 Check

Purpose: OMB A-11 Check, category "Regulatory & Authority Thresholds".

Source (`models_gov.py`):

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

**Inputs.** `bac`, `cpi`, `actualPctComplete` (required — `actualPctComplete` checked but unused
in the formula body).

**Availability.** All emittable.

**Literals:** `0.90` CPI trigger threshold (named "OMB A-11" — a citation to OMB Circular A-11,
value uncommented in code beyond the field/method name), `10000000` ($10M) "major program"
threshold (also uncommented — no citation to a specific A-11 dollar figure in code). Banding
reuses `0.92/0.88` from several A1 modules.

**Output / banding.** `cpi_below_90`, `major_program`, `reporting_triggered` (both booleans must
be true), `projected_overrun` (dollars).

**Abstains** on missing fields or `cpi == 0`.

---

## EVM Reporting Threshold

Purpose: EVM Reporting Threshold, category "Regulatory & Authority Thresholds".

Source (`models_gov.py`):

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

**Inputs.** `bac`, `cpi`, `spi` (required).

**Availability.** All emittable.

**Literals:** `0.90` breach threshold on both CPI and SPI (again uncommented, echoing OMB A-11's
0.90). `15` percent EAC-delta threshold distinguishing Amber from Red when both are breached — no
comment.

**Output / banding.** `cpi_breached`/`spi_breached`/`both_breached`, `eac_delta_pct`.

**Abstains** on missing fields, `cpi == 0`, or `bac == 0`.

---

## Contract Modification Frequency

Purpose: Contract Modification Frequency, category "Regulatory & Authority Thresholds".

Source (`models_gov.py`):

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

**Inputs.** `changeOrderCount` (EVENT kind per `field_registry.NEEDS`, filtered to "executed"
states, `servable: True`), `baselineContractSum` (PERMANENT), `revisedContractSum` (SNAPSHOT).
Note the identical field pair (`changeOrderCount`, `baselineContractSum`, and growth arithmetic)
appears in A4.6 Change Order Frequency, with different banding.

**Availability.** All three emittable/servable.

**Literals:** dual-track thresholds on both CO count and scope-growth percent: Red `co>=10 or
growth>=20`, Amber `co>=6 or growth>=10`, Yellow `co>=3 or growth>=5` — none commented. Note this
module has four tiers (adds "Yellow") where A4.6's near-identical formula (Green/Yellow/Amber/Red
with different cut points 5/3, 10/6, 20/10) uses a different threshold *shape* (AND rather than OR
combination in A4.6 — see A4.6 in the Group A file) for the same two underlying quantities.

**Output / banding.** `co_count`, `scope_growth_pct`, qualitative `word` per band.

**Abstains** on missing fields.

---

## Multi-Objective Optimization

Purpose: Multi-Objective Optimization, category "Decision Optimization".

Source (`models_gov.py`):

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

**Inputs.** `cpi`, `spi`, `docRiskScore` (flat, required).

**Availability.** All emittable.

**Literals:** normalization `(x - 0.80) / 0.25` for both CPI and SPI (mapping `[0.80,1.05]→[0,1]`)
— uncommented. Equal-weight average `(norm_cpi+norm_spi+norm_risk)/3` — no comment on the 1/3
weighting. Banding `>=0.75/0.55/0.35` — no comment.

**Output / banding.** `pareto_score`, `binding_constraint` (lowest-scoring objective),
`objectives` ranking.

**Abstains** on missing fields.

---

## Linear Programming

Purpose: Linear Programming, category "Decision Optimization".

Source (`models_gov.py`), using shared `_jsdiv`:

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

**Inputs.** `bac`, `ev`, `ac`, `cpi` — `cpi` is checked as required but never used in the formula
body (the "required CPI to complete" is derived purely from `bac`/`ev`/`ac`, not from the current
`cpi`).

**Availability.** All emittable.

**Literals:** feasibility cutoff `<=1.20`, optimal cutoff `<=1.00` — no comment. Banding
`<=1.00/1.05/1.15` — no comment. `_jsdiv` division-by-zero handling documented as deliberate (file
docstring: "Linear Programming can divide by zero in JavaScript yet still produce a FINITE score
via Infinity arithmetic").

**Output / banding.** `required_cpi_to_complete`, `feasible`/`optimal` booleans, `lp_score`.

**Abstains** on missing fields (`remaining_budget <= 0` returns a concrete Red result, not an
`insufficient()` abstention).

---

## Constraint Satisfaction Analysis

Purpose: Constraint Satisfaction Analysis, category "Decision Optimization".

Source (`models_gov.py`):

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

**Inputs.** `cpi`, `spi`, `bac` (required — `bac` checked but not used in the formula body),
`docRiskScore` (optional).

**Availability.** All emittable.

**Literals — four fixed constraints, none of which is actually derived from `bac` despite `bac`
being a required input:** `cpi >= 0.90`, `spi >= 0.90`, `doc < 0.70`, and a labeled "FAR threshold
(overrun < 25%)" constraint that is **actually implemented as `cpi > 0.80`**, not as an overrun
computation against a 25% threshold at all — the constraint's name and its implementation do not
match: no EAC, no overrun percentage, and no `25` literal appear anywhere in the actual check; only
`0.80` does. This is a naming/implementation mismatch worth flagging explicitly for the reviewer.
Banding on satisfaction rate `>=1.0/0.75/0.50` — no comment.

**Output / banding.** `satisfied`/`total`/`violated_constraints`/`satisfaction_rate`.

**Abstains** on missing `cpi`/`spi`/`bac`.

---

## What-If Scenario Matrix

Purpose: What-If Scenario Matrix, category "Decision Optimization".

Source (`models_gov.py`):

```python
def run_whatif_matrix(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("bac", "ev", "ac", "cpi", "spi")):
        return insufficient("WhatIf_Scenario_Matrix")
    if si["cpi"] == 0 or si["bac"] == 0:
        return insufficient("WhatIf_Scenario_Matrix")  # JS Infinity/NaN; refused
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

**Inputs.** `bac`, `ev`, `ac`, `cpi`, `spi` — `spi` checked as required but never used in the
formula body.

**Availability.** All emittable.

**Literals:** `1.00` optimistic multiplier, `0.95`/`1.05` (±5%) CPI degradation/recovery
scenarios — no comment on why exactly 5%. Banding on `range_pct` `<=5/10/20` — no comment.

**Output / banding.** Four named scenarios each with `eac`/`delta_pct`, `scenario_range_pct`,
`base_eac`.

**Abstains** on missing fields, `cpi == 0`, or `bac == 0`.

---

## Decision Sensitivity Matrix

Purpose: Decision Sensitivity Matrix, category "Decision Optimization".

Source (`models_gov.py`):

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

**Inputs.** `cpi`, `spi`, `docRiskScore` (required).

**Availability.** All emittable.

**Literals:** `risk_i = docRiskScore * 50` — the ×50 scale (converting a 0-1 score into a
percentage-point-equivalent impact comparable to `cpi_i`/`spi_i`, which run 0-100 as percent
deviations) has no comment. Banding `<=3/7/12` — no comment.

**Output / banding.** `top_driver`, `top_driver_pct`, full `sensitivity_matrix` ranking.

**Abstains** on missing fields.

---

## Pareto Frontier Analysis

Purpose: Pareto Frontier Analysis, category "Decision Optimization".

Source (`models_gov.py`):

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

**Inputs.** `cpi`, `spi`, `docRiskScore` (required).

**Availability.** All emittable.

**Literals:** efficiency cutoffs `cpi>=0.95`, `spi>=0.95`, `doc<0.30` — same `0.30` doc-risk
threshold seen repeatedly elsewhere, uncommented here too. Score normalization divisors `0.95` and
`0.30` reused inline.

**Output / banding.** `pareto_efficient`/`dominated`/`tradeoff_required` booleans,
`pareto_score`.

**Abstains** on missing fields.

---

## Regret Minimization Index

Purpose: Regret Minimization Index, category "Decision Optimization". **The third of the three
cases the task brief specifically flags — verified against the CURRENT code, not history.**

Source (`models_gov.py`):

```python
def run_regret_minimization(si: dict, rand: Callable[[], float],
                            period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "bac")):
        return insufficient("Regret_Minimization")
    future = {"improves": 0.3, "stable": 0.4, "worsens": 0.3}
    matrix = {
        "monitor": {"improves": 0, "stable": 5, "worsens": 30},
        "investigate": {"improves": 5, "stable": 0, "worsens": 10},
        "escalate": {"improves": 15, "stable": 8, "worsens": 0},
    }
    expected = {}
    for decision, regrets in matrix.items():  # insertion order; do not sort
        expected[decision] = int(js_round(
            regrets["improves"] * future["improves"]
            + regrets["stable"] * future["stable"]
            + regrets["worsens"] * future["worsens"]
        ))
    min_regret = min(expected.values())
    recommended = next(d for d in expected if expected[d] == min_regret)
    # Signal-state override: escalate on FAR breach, investigate below 0.95.
    if si["cpi"] < 0.88 or si["spi"] < 0.88:
        recommended = "escalate"
    elif si["cpi"] < 0.95 or si["spi"] < 0.95:
        recommended = "investigate"
    color = ("Green" if recommended == "monitor"
             else "Amber" if recommended == "investigate" else "Red")
    return {
        "method_class": "Regret_Minimization",
        "status_color": color,
        "recommended_action": recommended,
        "expected_regret": expected,
        "min_regret_score": min_regret,
        "evidence_metric": (
            f"Minimax regret recommends: {recommended} "
            f"(expected regret score {min_regret}/30); "
            f"this decision minimizes worst-case outcome under uncertain future states"
        ),
    }
```

**Inputs.** `cpi`, `spi`, `bac` (required — `bac` is checked for presence but never used
anywhere in the actual arithmetic; the module's entire decision is a function of `cpi`/`spi`
alone, and the minimax-regret table itself uses no project data whatsoever).

**Availability.** All emittable, though `bac`'s presence check is functionally irrelevant to the
output.

**Literals — the payoff matrix and future-state probabilities are still fixed literals with no
input dependence, confirmed against the CURRENT code (2026-08-10 session state, i.e. this audit's
own read, not a historical description):**
- Future-state probabilities `{"improves": 0.3, "stable": 0.4, "worsens": 0.3}` — no comment or
  citation; these never vary by project.
- Payoff/regret matrix, 9 fixed cells across 3 actions × 3 future states:
  `monitor: {0, 5, 30}`, `investigate: {5, 0, 10}`, `escalate: {15, 8, 0}` — no comment or
  citation for any of the nine values.
- Both structures are **module-level literals computed identically for every project**; the
  `expected_regret` values (`monitor: int(0*0.3+5*0.4+30*0.3)=11`, `investigate:
  int(5*0.3+0*0.4+10*0.3)=5`, `escalate: int(15*0.3+8*0.4+0*0.3)=8`) are **always exactly
  `{"monitor": 11, "investigate": 5, "escalate": 8}`** for every call, since neither `future` nor
  `matrix` depends on `si`. **This is exactly the `{11, 5, 8}` triple named in the task brief as
  the historical constants** — this audit confirms they are still present in the code as of now,
  computed from the same fixed `matrix`/`future` literals, and are still returned in the
  `expected_regret` dict on every call.
- Override thresholds `0.88` (escalate) and `0.95` (investigate) on `min(cpi, spi)` — no comment.

**What has changed, per the task brief's instruction to report current state rather than
history:** the code comment `# Signal-state override: escalate on FAR breach, investigate below
0.95.` documents that **the final `recommended_action` is NOT actually chosen by the minimax
regret calculation** in the vast majority of real cases — it is overridden by a simple two-tier
`cpi`/`spi` threshold check immediately afterward, which is what actually drives `status_color`
for any project with `cpi < 0.95` or `spi < 0.95`. Only when both `cpi >= 0.95` and `spi >= 0.95`
does the code fall through to whatever `min_regret` computed — which, since `expected_regret` is
always `{"monitor": 11, "investigate": 5, "escalate": 8}`, always selects `"investigate"`
(`min_regret = 5`) rather than `"monitor"`, because `investigate`'s fixed expected regret (5) is
always lower than `monitor`'s (11) under this literal matrix. **This audit's own read of the
current code confirms the task brief's framing: the `expected_regret` dict is still printed in
the module's output (it is a top-level key), it is still computed from the same fixed `{11,5,8}`
literals, and the minimax step it drives is redundant with — and always agrees with, at
`cpi/spi>=0.95`, in the direction of — "investigate," never "monitor," despite "monitor" being the
Green-mapped, most-favorable action.**

**Output / banding.** `recommended_action` (one of monitor/investigate/escalate, chosen mostly by
the `cpi`/`spi` override, occasionally — only when both signals are ≥0.95 — by the
always-identical minimax step), `expected_regret` (always `{11, 5, 8}` as shown above),
`min_regret_score` (always `5` in the fallthrough case). `status_color`: Green (monitor), Amber
(investigate), Red (escalate).

**Abstains** on missing `cpi`/`spi`/`bac`.
