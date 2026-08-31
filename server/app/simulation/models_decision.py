"""
B1.1 Conservative Dominance and B3.1 ABM Governance Layer, ported from assets/js/decision.js
(classifyConflict / deriveHealthState / deriveDecision — PCEIF Layer-2 governance rules).

INPUT CONTRACT: the ASSEMBLED PROJECT, as for B1.2–B1.4 — si["signals"] holding {evm, mc,
cusum, doc} each with .status, {cusum} additionally with .breached. The fairness gate that once read
si["fairnessSensitive"] is removed: nothing writes that key, so it could never fire.
The two modules are projections of one derivation: Conservative Dominance records
{state, conflict} (the instrument's m09_conservative), ABM Governance records
{state, authority, action, fairness_gate} (m19_abm).

THE FIFTEEN DEFECTS, defect 1, fixed here. classifyConflict and the health-state fallback used
to compare statuses in LOWERCASE ("red", "green", "amber"), so a capitalised "Red" from a signal
did not count as red: on the audit's own input (cost performance Red, forecast Red, control chart
Green, document risk Green) this counted zero reds and returned Green where the correct answer is
a red review. Every comparison here now runs through the one shared vocabulary in fusion.py,
which is case-insensitive and returns None for a value it does not recognise.

The same fix closes the second half of the defect, the bucket. The old Green arm was "no reds and
no ambers", so a Yellow signal, a light-amber signal, an unrecognised string and a missing signal
all produced agreement at low risk. The Green arm now requires all four signals to be present and
all four to be Green; anything else is at best an early warning. That is the conservative
direction, which is what this computation is named for.

Quirks reproduced deliberately (validated against decision.js executed in the browser):

- deriveHealthState prefers window.getProjectFusion when signals.js is loaded; the server (and
  the harness, which loads decision.js alone) uses the signal-class fallback rule. Same
  treatment as A4.8's deriveExtendedFields note.
- classifyConflict dereferences project.signals.cusum.breached unconditionally: a project
  with no cusum signal THROWS in JavaScript. The port abstains on a missing signals or cusum
  object instead — the refusing direction, recorded in VALIDATION.md.
"""

from __future__ import annotations

from typing import Any, Callable

from .fusion import normalise_status
from .models import insufficient

SIGNAL_NAMES = ("evm", "mc", "cusum", "doc")


def _signal_statuses(project: dict) -> dict:
    """
    The four assembled signal statuses, each normalised onto one band or None.

    None means "this signal did not contribute": either it is absent, or it carried a value
    outside the platform's status vocabulary. Both are treated the same way downstream, and
    neither is allowed to read as Green. See fusion.normalise_status.
    """
    s = project.get("signals") or {}
    return {
        name: (normalise_status(s[name].get("status")) if s.get(name) is not None else None)
        for name in SIGNAL_NAMES
    }


def _count(statuses: dict, level: str) -> int:
    return sum(1 for v in statuses.values() if v == level)


def _all_green(statuses: dict) -> bool:
    """Agreement at low risk needs every signal present AND every one of them Green."""
    return all(statuses.get(name) == "Green" for name in SIGNAL_NAMES)


def _classify_conflict(project: dict) -> str:
    s = _signal_statuses(project)
    reds = _count(s, "Red")
    if reds >= 2:
        return "Multi-signal red-review"
    if project["signals"]["cusum"].get("breached") and s["doc"] == "Green":
        return "Anomaly without narrative"
    if s["mc"] == "Red" and s["evm"] != "Red":
        return "Forecast ahead of status"
    if s["doc"] in ("Amber", "Red") and s["evm"] == "Green":
        return "Leading document risk"
    if _all_green(s):
        return "Agreement: low risk"
    return "Mixed early warning"


def _derive_health_state(project: dict) -> str:
    # Signal-class rule (the decision.js fallback; getProjectFusion is browser-only).
    s = _signal_statuses(project)
    reds = _count(s, "Red")
    signals = project.get("signals") or {}
    cusum = signals.get("cusum")
    cusum_breached = bool(cusum.get("breached")) if cusum is not None else False
    # The red review is tested FIRST, before the low-risk arm, so that no ordering accident can
    # let a project with two red signals reach a Green answer again.
    if reds >= 2 or (cusum_breached and s["mc"] == "Red"):
        return "Red-review"
    if _all_green(s):
        return "Green"
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
        # anything else. It selected a different action sentence and a different escalation
        # authority, so a reader of this module would reasonably believe two escalation paths
        # exist here. One does.
        #
        # The KEY stays, always False, because assets/js/app.js reads `d.fairnessGateRequired`
        # to decide whether to render an acknowledgement checkbox and whether to allow submit.
        # Dropping the key would change the response shape for a frontend this task may not
        # touch. Removing the dead condition is the change; removing the contract is not.
        #
        # The browser's own decision.js:228 still computes a live gate from
        # project.fairnessSensitive, which ingest.js does write. That is the legacy client
        # path and a separate decision; nothing here affects it.
        "fairnessGateRequired": False,
    }


def _guard(project: dict) -> bool:
    signals = project.get("signals")
    return signals is not None and signals.get("cusum") is not None


#: Severity order over the four bands, worst last. Imported rather than restated so this module
#: and the combination rule cannot disagree about which band is worse.
from .fusion import BAND_SEVERITY  # noqa: E402


def _dominant_band(statuses: dict) -> str | None:
    """The most adverse band any present signal reads, which is what dominance means."""
    present = [b for b in statuses.values() if b in BAND_SEVERITY]
    return max(present, key=lambda b: BAND_SEVERITY[b]) if present else None


def run_conservative_dominance(si: dict, rand: Callable[[], float],
                               period_cutoff) -> dict[str, Any]:
    if not _guard(si):
        return insufficient("Conservative_Dominance")
    d = _derive_decision(si)
    # ------------------------------------------------------------- RUN 20 CYCLE 9, THE P1 DEFECT
    #
    # THE MODULE NAMED CONSERVATIVE DOMINANCE DID NOT APPLY A DOMINANCE RULE. It returned the
    # shared decision-layer health state, which is a COUNTING rule: two or more Red signals, or a
    # cumulative-sum breach together with a Red forecast, reach "Red-review"; everything else
    # that is not uniformly Green reaches Amber. So a project whose worst signal was RED, alone,
    # reported AMBER and selected routine early-warning review rather than escalation. Adverse
    # evidence was outvoted by the count of the signals that had nothing adverse to say.
    #
    # Conservative dominance is not a count. It is the rule that the most adverse reading
    # DOMINATES: the decision is taken against the worst state the evidence supports, and a
    # single adverse signal is enough because that is precisely what "conservative" means. The
    # rule is also IDEMPOTENT, which matters here for a second reason established this same
    # cycle: three of the four signals this module reads are readings of ONE earned-value
    # measurement, so a counting rule over them was counting one measurement up to three times
    # while a dominance rule cannot.
    #
    # NO THRESHOLD, WEIGHT OR CONSTANT IS INTRODUCED. The rule has no parameter: it is a maximum
    # over the bands already assigned by the signals themselves.
    #
    # THE GOVERNANCE PROJECTION IS DELIBERATELY LEFT ALONE. B3.1 reads the same decision layer to
    # decide WHICH ACTION AND WHOSE AUTHORITY, which is a different question from what the
    # evidence most adversely supports, and it is not this module's finding to change. The two
    # states are therefore reported side by side here rather than silently reconciled, so a
    # reader can see the dominance state and the decision-layer state and is never shown one
    # while believing it is the other.
    # THE CONSERVATIVE TREATMENT OF ABSENT EVIDENCE IS PART OF THE RULE, NOT AN EXCEPTION TO IT.
    # A dominance rule over the signals PRESENT would let an absent or unrecognised signal read
    # as agreement: three Greens and one missing would dominate to Green, which is the strongest
    # claim available and the one the missing signal never made. The pre-existing rule already
    # required every one of the four signals to be present and Green before it would say Green,
    # and that requirement is kept exactly: the calmest band is reachable only on complete
    # evidence, and incomplete evidence cannot be calmer than Amber. Nothing is invented; the
    # existing `_all_green` predicate is the one applied.
    _bands = _signal_statuses(si)
    _dominant = _dominant_band(_bands)
    _complete = _all_green(_bands) or all(_bands.get(n) is not None for n in SIGNAL_NAMES)
    if _dominant is None:
        state = d["healthState"]
    elif _dominant == "Green" and not _all_green(_bands):
        state = "Amber"
    else:
        state = _dominant
    return {
        "method_class": "Conservative_Dominance",
        "status_color": state,
        "state": state,
        "dominant_signal_band": _dominant,
        "signal_bands": _bands,
        "decision_layer_state": d["healthState"],
        "evidence_complete": _complete,
        "conflict": d["conflictType"],
        # NO EM DASH. This string is what the Signal Ledger renders as this module's finding,
        # and until the flat-to-nested adapter landed it reached no screen, because the module
        # could not execute on the normal path at all. The moment it became reachable it became
        # user-facing text, which NAMING_AUTHORITY.md's standing rule covers. The separator is
        # the only change: no arithmetic, no state name, no classification is touched.
        "evidence_metric": f"{state}: {d['conflictType']}",
    }


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


DECISION_EXTENSIONS: dict[str, tuple[str, Callable]] = {
    "B1.1": ("Conservative_Dominance", run_conservative_dominance),
}
