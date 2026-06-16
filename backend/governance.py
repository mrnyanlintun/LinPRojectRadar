"""
lin-project-radar backend — governance.py  (Sprint 0 item 24)
PCEIFGovernanceRouter — expanded conflict typology (8 types) over a unified
signal array. Pure logic; no network.
"""


class PCEIFGovernanceRouter:
    AUTHORITY_MATRIX = {
        "Green": {"action": "Routine Monitoring", "role": "Project Manager / Controls Lead", "timeframe": "Monthly cycle"},
        "Amber": {"action": "Early Warning Review", "role": "PM + Project Controls Lead", "timeframe": "Weekly tracking loop"},
        "Red-Review": {"action": "Controlled Escalation", "role": "PM + Program Manager", "timeframe": "48 Business Hours"},
        "Critical": {"action": "Contracting Officer / Executive Board Escalation", "role": "Executive Authority / CO", "timeframe": "Immediate"},
    }

    FAIRNESS_SENSITIVE = ["Document_Risk_Extraction", "Line_of_Balance_Velocity", "CCPM_Buffer_Health"]

    def synthesize(self, signal_array: list, human_override: dict = None) -> dict:
        counts = {"Green": 0, "Amber": 0, "Red": 0, "Critical": 0}
        fairness_triggered = False
        evidence = []

        for sig in signal_array:
            color = sig.get("status_color", "Green")
            if color not in counts:
                counts[color] = 0
            counts[color] += 1
            evidence.append(f"[{sig.get('method_class', '?')}] {sig.get('evidence_metric', '')}")
            if color in ("Red", "Critical") and sig.get("method_class") in self.FAIRNESS_SENSITIVE:
                fairness_triggered = True

        # Conflict typology — expanded from the original 4 to 8 types
        if counts["Critical"] > 0:
            status = "Critical"
            conflict = "Severe Critical Override"
        elif counts["Red"] >= 2:
            status = "Red-Review"
            conflict = "Multi-signal Red-Review"
        elif counts["Red"] == 1 and counts["Amber"] >= 1:
            status = "Red-Review"
            conflict = "Mixed Red-Amber Divergence"
        elif counts["Red"] == 1:
            evm = next((s for s in signal_array if s.get("method_class") == "SPC_CUSUM_Anomaly"), None)
            doc = next((s for s in signal_array if s.get("method_class") == "Document_Risk_Extraction"), None)
            if evm and evm.get("status_color") == "Green" and doc and doc.get("status_color") == "Red":
                conflict = "Leading Document Risk (financials lag field)"
            else:
                conflict = "Anomaly Without Narrative"
            status = "Red-Review"
        elif counts["Amber"] >= 2:
            status = "Amber"
            conflict = "Early Warning Divergence"
        elif counts["Amber"] == 1:
            status = "Amber"
            conflict = "Single Signal Watch"
        else:
            status = "Green"
            conflict = "Agreement — All Channels Stable"

        if human_override:
            status = human_override.get("target_status", status)

        routing = self.AUTHORITY_MATRIX.get(status, self.AUTHORITY_MATRIX["Green"])
        return {
            "final_status": status,
            "conflict": conflict,
            "action": routing["action"],
            "role": routing["role"],
            "timeframe": routing["timeframe"],
            "fairness_gate": fairness_triggered,
            "evidence": evidence,
        }
