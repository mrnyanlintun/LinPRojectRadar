"""
B1.1 Conservative Dominance and B3.1 ABM Governance Layer, ported from assets/js/decision.js
(classifyConflict / deriveHealthState / deriveDecision — PCEIF Layer-2 governance rules).

INPUT CONTRACT: the ASSEMBLED PROJECT, as for B1.2–B1.4 — si["signals"] holding {evm, mc,
cusum, doc} each with .status, {cusum} additionally with .breached, and si["fairnessSensitive"].
The two modules are projections of one derivation: Conservative Dominance records
{state, conflict} (the instrument's m09_conservative), ABM Governance records
{state, authority, action, fairness_gate} (m19_abm).

Quirks reproduced deliberately (validated against decision.js executed in the browser):

- classifyConflict and the health-state fallback compare statuses in LOWERCASE ("red",
  "green", "amber"). A capitalized "Red" from a signal does not count as red there. That is
  what the instrument executes; reproduced, not fixed, and covered by fixture cases in both
  casings.
- deriveHealthState prefers window.getProjectFusion when signals.js is loaded; the server (and
  the harness, which loads decision.js alone) uses the signal-class fallback rule. Same
  treatment as A4.8's deriveExtendedFields note.
- classifyConflict dereferences project.signals.cusum.breached unconditionally: a project
  with no cusum signal THROWS in JavaScript. The port abstains on a missing signals or cusum
  object instead — the refusing direction, recorded in VALIDATION.md.
"""

from __future__ import annotations

from typing import Any, Callable

from .models import insufficient


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
    # Signal-class rule (the decision.js fallback; getProjectFusion is browser-only).
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
    fairness_gate = escalate and project.get("fairnessSensitive") is True

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
        action = ("Request contractor explanation and recovery-plan review; fairness gate "
                  "required before any formal action" if fairness_gate
                  else "Recovery-plan review and management escalation")
        authority = ("Program director / PMO with contract-administration awareness"
                     if fairness_gate else "Program director / PMO lead")
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
        "fairnessGateRequired": fairness_gate,
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
    "B3.1": ("ABM_Governance", run_abm_governance),
}
