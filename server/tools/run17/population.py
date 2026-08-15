"""
Run 17 population derivation.

Derives the 100 Run-17 scientific targets from p0-baseline/module_renumbering_map.csv, the same
source of truth server/app/simulation/registry.py reads.

FINDING RECORDED IN CODE (Run 17, Gate 0). The CSV has an `old_id` column that superficially
looks like the v0.5 registry Module_ID_Text_Key. IT IS NOT. It is a legacy pre-renumbering id
whose sequence contains two retired rows (old 1.3, alias of 4.1; and old 3.2, alias of 5.1), so
every row after each gap is displaced by one. Reading `old_id` as the registry key silently
renames eleven modules: old_id 3.4 is Labor Productivity Index while the v0.5 key 3.4 is
Material Cost Variance. A Run-17 exclusion driven off `old_id` would therefore have excluded the
wrong module and executed the one the owner disabled.

The v0.5 Module_ID_Text_Key is carried by the `new_id` column with its group letter replaced by
the owner-specification category number. That mapping is asserted below by MODULE NAME against
the owner specification, not assumed, so a future registry edit that breaks it fails loudly.

IDENTIFIERS ARE STRINGS. The keys include 1.10, 2.10, 3.10 is absent but 4.10, 7.10 and 7.20 are
present. Parsing any as a float collides 1.10 with 1.1. Every function here keeps text, and
_float_collision() records exactly which pairs would have merged.
"""

from __future__ import annotations

import csv
import pathlib

CSV_PATH = (pathlib.Path(__file__).resolve().parents[3]
            / "p0-baseline" / "module_renumbering_map.csv")

#: The one module excluded from Run-17 scientific execution, by v0.5 key. Owner spec 3 and 12.
EXCLUDED_TEXT_KEY = "3.4"
EXCLUDED_CODE_ID = "A3.4"

#: Registry code-id group -> owner-specification category. Verified by module name in
#: verify_mapping() below. A6 and B3 both feed category 8: B3 supplies 8.1 to 8.5 and A6
#: supplies 8.6 to 8.9, which is why the category number alone is not enough and the per-module
#: offset is carried here.
GROUP_TO_CATEGORY: dict[str, tuple[str, int]] = {
    # code group: (owner category, number offset added to the code's own index)
    "A1": ("1", 0),
    "A2": ("2", 0),
    "A3": ("3", 0),
    "A4": ("4", 0),
    "A5": ("5", 0),
    "B1": ("6", 0),
    "B2": ("7", 0),
    "B3": ("8", 0),
    "A6": ("8", 5),   # A6.1 Quality Compliance Index is owner-spec 8.6
    "C1": ("9", 0),
    "B4": ("10", 0),
    "D1": ("PH", 0),
}

#: The owner specification's own module names, keyed by v0.5 Module_ID_Text_Key. This is the
#: supervisory specification's list, transcribed from sections 10 to 20 of the Run-17 prompt.
#: It exists so the group mapping above is PROVED rather than believed: if the registry and the
#: specification ever disagree about which module an identifier names, verify_mapping() raises.
SPEC_NAMES: dict[str, str] = {
    # RUN 28 CLOSURE. The owner decided A1.1's canonical identity is `Monte Carlo EAC Forecast`,
    # final, and directed that the CURRENT naming authority be updated; it was. The Run-17
    # transcription follows the decision for exactly the reason the two Run-28 renames below do:
    # this table exists so the mapping proof compares the registry against the SPECIFICATION AS
    # IT NOW STANDS rather than against a stale transcription of an earlier one. The previous
    # name is recorded beside it so the identity stays followable, and the specification document
    # itself is untouched -- it is the immutable controlling authority and this is a
    # transcription of the owner's later decision, not an edit of it.
    "1.1": "Monte Carlo EAC Forecast",  # Run 17 and earlier: Monte Carlo EAC
    "1.2": "CUSUM Anomaly Monitor", "1.3": "Bayesian EAC",
    "1.4": "Kalman Filter SPI Smoother", "1.5": "ARIMA CPI Forecast", "1.6": "Earned Schedule",
    "1.7": "TCPI", "1.8": "Variance at Completion", "1.9": "Budget Execution Rate",
    # RUN 28. The owner's Run-28 supervisory contract renames both of these, under its own
    # authority, and the registry map now carries the new names. The Run-17 transcription is
    # updated here so the mapping proof continues to compare the registry against the
    # SPECIFICATION rather than against a stale transcription of an earlier one; the previous
    # names are recorded beside them so the identity is still followable.
    "1.10": "CPI Shrinkage Forecast",              # Run 17 and earlier: Regression to Mean CPI
    "1.11": "Independent EAC Reconciliation Index",  # Run 17 and earlier: ICE Ratio
    "2.1": "PERT Network Criticality", "2.2": "Line of Balance", "2.3": "CCPM Buffer Health",
    "2.4": "Schedule Compression Index", "2.5": "Float Consumption Rate",
    "2.6": "S-Curve Deviation", "2.7": "Milestone Trend Analysis",
    "2.8": "Look-Ahead Schedule Health", "2.9": "Resource Loading Index",
    "2.10": "Schedule Risk Analysis P80", "2.11": "Critical Path Index",
    "3.1": "Reference Class Forecasting", "3.2": "Contingency Burn Rate",
    "3.3": "Labor Productivity Index", "3.4": "Material Cost Variance",
    "3.5": "Overhead Absorption Rate", "3.6": "Cost Risk Analysis P80",
    "3.7": "Analogous Estimating Ratio", "3.8": "Parametric Cost Index",
    "3.9": "Inflation Adjustment Index",
    "4.1": "Document Risk Score", "4.2": "RFI Velocity", "4.3": "Submittal Rejection Rate",
    "4.4": "NCR Rate", "4.5": "Weather Day Impact", "4.6": "Change Order Frequency",
    "4.7": "Dispute Escalation Index", "4.8": "Subcontractor Performance",
    "4.9": "Procurement Lead Time Monitor", "4.10": "Specification Conflict Density",
    "5.1": "DSM Rework Propagation", "5.2": "Sensitivity Analysis",
    "5.3": "Tornado Risk Ranking", "5.4": "Scenario Modeling", "5.5": "Rework Feedback Loop",
    "5.6": "Queueing Theory Bottleneck", "5.7": "Agent-Based Supply Chain",
    "5.8": "Discrete Event Simulation",
    "6.1": "Conservative Dominance", "6.2": "Weighted Voting", "6.3": "Majority Rules",
    "6.4": "Worst-N-of-M",
    "7.1": "Dempster-Shafer", "7.2": "Rough Sets", "7.3": "Neutrosophic Logic",
    "7.4": "Interval Fuzzy Sets", "7.5": "Z-Numbers", "7.6": "PLTS",
    "7.7": "Plithogenic Sets", "7.8": "Belief Rule Base", "7.9": "Quantum Probability",
    "7.10": "Pythagorean Fuzzy Sets", "7.11": "Picture Fuzzy Sets",
    "7.12": "Hesitant Fuzzy Sets", "7.13": "Type-2 Fuzzy Sets", "7.14": "Maximum Entropy",
    "7.15": "Possibility Theory", "7.16": "Spherical Fuzzy Sets",
    "7.17": "Fermatean Fuzzy Sets", "7.18": "MARCOS Ranking", "7.19": "CRITIC-TOPSIS",
    "7.20": "Hypersoft Sets",
    "8.1": "ABM Governance Layer", "8.2": "FAR Threshold Monitor", "8.3": "OMB A-11 Check",
    "8.4": "EVM Reporting Threshold", "8.5": "Contract Modification Frequency",
    "8.6": "Quality Compliance Index", "8.7": "Safety Performance Index",
    "8.8": "Environmental Compliance Rate", "8.9": "Contractor Performance Score",
    "9.1": "Missing Data Index", "9.2": "Data Timeliness Score",
    "9.3": "Source Reliability Weighting", "9.4": "Audit Trail Completeness",
    "9.5": "Information Completeness Ratio", "9.6": "Cross-document Consistency Score",
    "9.7": "Reporting Frequency Index",
    "10.1": "Multi-Objective Optimization", "10.2": "Linear Programming",
    "10.3": "Constraint Satisfaction Analysis", "10.4": "What-If Scenario Matrix",
    "10.5": "Decision Sensitivity Matrix", "10.6": "Pareto Frontier Analysis",
    "10.7": "Regret Minimization Index",
    "PH.1": "Isolation Forest", "PH.2": "Portfolio Outlier Detection",
    "PH.3": "Signal Trajectory Classifier", "PH.4": "Cross-project Pattern Detector",
    "PH.5": "Anomaly Score",
}

#: Owner-spec section 3: the eight concept-only modules included in the 100 scientific targets
#: but which MUST remain operationally disabled and non-voting.
CONCEPT_ONLY_KEYS = ("3.8", "7.7", "7.9", "7.20", "10.1", "10.2", "10.5", "10.6")

#: Name differences that are spelling only, not identity. Each is recorded rather than silently
#: normalised, so no module identity is asserted on a fuzzy match.
NAME_ALIASES: dict[str, str] = {
    "PH.4": "Cross-project Pattern Detector",   # registry lowercase p; spec capitalises Project
}


def load_rows() -> list[dict[str, str]]:
    """Every live registry row, in file order. RETIRED aliases are not modules."""
    with CSV_PATH.open(encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    return [r for r in rows if r["new_id"].strip().upper() != "RETIRED"]


def text_key(code_id: str) -> str:
    """
    The v0.5 Module_ID_Text_Key for a registry code id. String arithmetic only on the index;
    the returned key is always text.
    """
    group, index = code_id.strip().split(".", 1)
    category, offset = GROUP_TO_CATEGORY[group]
    return f"{category}.{int(index) + offset}"


def verify_mapping() -> list[str]:
    """
    Prove the group mapping by module name against the owner specification. Returns the list of
    disagreements; an empty list is the proof. Never silently corrects.
    """
    problems = []
    for row in load_rows():
        code = row["new_id"].strip()
        key = text_key(code)
        registry_name = row["module_name"].strip()
        spec_name = SPEC_NAMES.get(key)
        if spec_name is None:
            problems.append(f"{code} -> {key}: no owner-specification module at that key")
            continue
        if registry_name.lower() != spec_name.lower():
            problems.append(
                f"{code} -> {key}: registry {registry_name!r} vs specification {spec_name!r}")
    missing = set(SPEC_NAMES) - {text_key(r["new_id"].strip()) for r in load_rows()}
    for key in sorted(missing):
        problems.append(f"{key} ({SPEC_NAMES[key]}): in specification, absent from registry")
    return problems


def population() -> list[dict[str, str]]:
    """The 100 Run-17 scientific targets: every live registry row except the excluded module."""
    out = []
    for row in load_rows():
        code = row["new_id"].strip()
        key = text_key(code)
        if key == EXCLUDED_TEXT_KEY:
            continue
        out.append({
            "module_id": key,
            "code_id": code,
            "module_name": row["module_name"].strip(),
            "category": key.split(".", 1)[0],
            "group": row["group"].strip(),
            "level": "portfolio" if row["group"].strip() == "D" else "project",
            "concept_only": "yes" if key in CONCEPT_ONLY_KEYS else "no",
        })
    return out


def reconciliation() -> dict[str, object]:
    """The count proof the owner specification requires before any testing begins."""
    rows = load_rows()
    project = [r for r in rows if r["group"].strip() in ("A", "B", "C")]
    portfolio = [r for r in rows if r["group"].strip() == "D"]
    pop = population()
    keys = [p["module_id"] for p in pop]
    return {
        "registry_live_rows": len(rows),
        "project_level": len(project),
        "portfolio_level": len(portfolio),
        "excluded_key": EXCLUDED_TEXT_KEY,
        "excluded_code_id": EXCLUDED_CODE_ID,
        "excluded_name": SPEC_NAMES[EXCLUDED_TEXT_KEY],
        "project_targets": len(project) - 1,
        "portfolio_targets": len(portfolio),
        "total_targets": len(pop),
        "unique_module_ids": len(set(keys)),
        "mapping_problems": verify_mapping(),
        "float_coercion_would_collide": _float_collision(keys),
        "concept_only_in_population": sorted(
            k for k in CONCEPT_ONLY_KEYS if k in set(keys)),
    }


def _float_collision(keys: list[str]) -> list[str]:
    """Which keys collide if parsed as floats. The trap avoided, recorded rather than assumed."""
    seen: dict[float, str] = {}
    collided = []
    for k in keys:
        try:
            f = float(k)
        except ValueError:
            continue
        if f in seen and seen[f] != k:
            collided.append(f"{seen[f]} vs {k}")
        seen[f] = k
    return collided


if __name__ == "__main__":
    rec = reconciliation()
    for k, v in rec.items():
        print(f"{k}: {v}")
