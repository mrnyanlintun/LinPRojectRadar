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
        # Abstention row. Reached when the router cannot read a signal's status, or when an
        # override names a status this matrix does not define. It is deliberately NOT a band:
        # it routes the reader back to the missing input rather than publishing a colour.
        "Indeterminate": {"action": "Abstain — resolve signal status before routing", "role": "Project Controls Lead", "timeframe": "Before routing can proceed"},
    }

    # The only status values a signal may carry. Case-sensitive on purpose: "red" is not "Red",
    # and silently folding it was the defect (a lowercase red counted into counts["red"], which
    # the ladder never read, so a red signal published Green).
    CANONICAL_SIGNAL_STATUS = ("Green", "Amber", "Red", "Critical")

    ABSTAIN_STATUS = "Indeterminate"

    FAIRNESS_SENSITIVE = ["Document_Risk_Extraction", "Line_of_Balance_Velocity", "CCPM_Buffer_Health"]

    def _abstain(self, needs: list, evidence: list) -> dict:
        routing = self.AUTHORITY_MATRIX[self.ABSTAIN_STATUS]
        return {
            "final_status": self.ABSTAIN_STATUS,
            "conflict": "Abstained — signal status not readable",
            "action": routing["action"], "role": routing["role"], "timeframe": routing["timeframe"],
            "fairness_gate": False,
            "evidence": evidence,
            "needs": needs,
        }

    def synthesize(self, signal_array: list, human_override: dict = None) -> dict:
        counts = {"Green": 0, "Amber": 0, "Red": 0, "Critical": 0}
        fairness_triggered = False
        evidence = []
        needs = []

        for idx, sig in enumerate(signal_array):
            evidence.append(f"[{sig.get('method_class', '?')}] {sig.get('evidence_metric', '')}")
            # No default. A signal that does not state a canonical status is not a Green signal;
            # it is a signal the router cannot read, and the whole synthesis abstains.
            if "status_color" not in sig:
                needs.append(f"signal {idx} ({sig.get('method_class', '?')}): status_color absent")
                continue
            color = sig["status_color"]
            if color not in self.CANONICAL_SIGNAL_STATUS:
                needs.append(
                    f"signal {idx} ({sig.get('method_class', '?')}): status_color {color!r} is not one of "
                    + "/".join(self.CANONICAL_SIGNAL_STATUS)
                )
                continue
            counts[color] += 1
            if color in ("Red", "Critical") and sig.get("method_class") in self.FAIRNESS_SENSITIVE:
                fairness_triggered = True

        if needs:
            return self._abstain(needs, evidence)

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
            if status not in self.AUTHORITY_MATRIX:
                return self._abstain(
                    [f"human_override.target_status {status!r} is not one of "
                     + "/".join(k for k in self.AUTHORITY_MATRIX if k != self.ABSTAIN_STATUS)],
                    evidence,
                )

        # No favourable fallback: every reachable status has a row above.
        routing = self.AUTHORITY_MATRIX[status]
        return {
            "final_status": status,
            "conflict": conflict,
            "action": routing["action"],
            "role": routing["role"],
            "timeframe": routing["timeframe"],
            "fairness_gate": fairness_triggered,
            "evidence": evidence,
        }
