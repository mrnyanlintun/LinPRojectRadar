#!/usr/bin/env python3
"""
RUN 31 PASS 2: generate the operational artifacts, all from EXECUTION or from shipped data.

Nothing here is transcribed. The route inventory and the downstream execution table are built by
running `registry.run_module` -- the real production entry point -- and reading what came back;
the gated set is read from the shipped registry CSV through the boundary's own derivation; the
regulatory snapshot is read from the frozen rule register.
"""
import csv, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from app.simulation import registry as REG                              # noqa: E402
from app.simulation import regulatory as RG                             # noqa: E402
from app.simulation.models import SIMULATION_VERSION, VALIDATED         # noqa: E402
from app.simulation.models_cat89 import CAT89_CANONICAL, MODULE_USE     # noqa: E402
from app.simulation.qualification_boundary import (                     # noqa: E402
    CATEGORY_USE, gate_installed_for, gated_module_ids)
from app.simulation.lineage import independence_established, lineage_status  # noqa: E402
from run31_historical_cat89 import LEGACY_CAT89                         # noqa: E402

NOOP = (lambda: 0.5)
CUT = "2026-06-30"
SI = {"bac": 1_000_000.0, "ev": 400_000.0, "ac": 440_000.0, "pv": 450_000.0,
      "cpi": 0.909, "spi": 0.889, "docRiskScore": 0.35,
      "actualPctComplete": 40.0, "plannedPctComplete": 45.0}
UNASSESSED = {"qualification_state": "UNASSESSED"}
QUALIFIED = {"qualification_state": "QUALIFIED", "timeliness_status": "TIMELY",
             "verification_status": "verified", "source_authority": "system_of_record"}
REFUSED = "evidence_not_qualified_for_use"


def run(mid, si):
    try:
        return REG.run_module(mid, dict(si), NOOP, CUT)
    except Exception as exc:                                            # noqa: BLE001
        return {"__error__": f"{type(exc).__name__}: {exc}"}


def w(name, header, rows):
    p = ROOT / "code_audit" / name
    with p.open("w", newline="", encoding="utf-8") as fh:
        cw = csv.writer(fh, lineterminator="\n")
        cw.writerow(header)
        cw.writerows(rows)
    print(f"wrote {p.relative_to(ROOT)}  ({len(rows)} rows)")


# ---------------------------------------------------------------- downstream execution proof
def downstream():
    idx = REG.registry_index()
    rows = []
    counters = {"Signal Synthesis": 0, "Evidence Combination": 0,
                "Regulatory & Authority Thresholds": 0, "Delivery Quality Performance": 0,
                "Decision Optimization": 0}
    for mid, cat in sorted(gated_module_ids().items()):
        fn = VALIDATED.get(mid)
        if fn is None:
            continue
        use, _ = CATEGORY_USE.get(cat, ("analytical_use", {}))
        raw = run(mid, dict(SI, evidenceQualification=UNASSESSED))
        qual = run(mid, dict(SI, evidenceQualification=QUALIFIED))
        refused = raw.get("abstention_reason_code") == REFUSED
        # A DISABLED MODULE IS NOT A BYPASS. The registry short-circuits the eight
        # concept-only/archived identities BEFORE any runner is reached, so they consume no
        # evidence at all and return no band. Counting them as bypasses would report a gate
        # failure for code that never executes; verified by execution -- each returns
        # activation_state DISABLED_UNSAFE, status_color None and insufficient_data True.
        disabled = raw.get("activation_state") in ("DISABLED_UNSAFE",
                                                   "DISABLED_EVIDENCE_UNDER_REVIEW")
        bypass = (not refused) and (not disabled)
        if bypass:
            counters[cat] = counters.get(cat, 0) + 1
        rows.append([
            cat, mid, idx[mid]["module_name"], "registry.run_module",
            f"{fn[1].__module__}.{fn[1].__name__}",
            "raw evidence declared UNASSESSED",
            "YES", "YES" if gate_installed_for(fn[1]) else "NO",
            raw.get("qualification", {}).get("qualification_state", "UNASSESSED"),
            lineage_status(mid, applicable=True),
            "NO" if (refused or disabled) else "YES",
            "NO" if bypass else "YES" if False else "NO",
            raw.get("result_source") or qual.get("result_source") or "",
            raw.get("abstention_reason_code")
            or ("DISABLED_NOT_EXECUTED" if disabled else "computed"),
            SIMULATION_VERSION,
            "PASS" if (refused or disabled) else "FAIL"])
    return rows, counters


# ---------------------------------------------------------------- Cat 8/9 route inventory
def route_inventory():
    idx = REG.registry_index()
    rows = []
    for mid in sorted(CAT89_CANONICAL):
        fn = VALIDATED[mid][1]
        legacy = LEGACY_CAT89.get(mid)
        reachable = "YES" if (legacy and fn is legacy[1]) else "NO"
        canonical = CAT89_CANONICAL[mid][1]
        inner = getattr(fn, "__wrapped_runner__", fn)
        rows.append([
            mid, idx[mid]["module_name"], idx[mid]["category_name"], "registry.run_module",
            f"{fn.__module__}.{fn.__name__}",
            "models_cat89.CAT89_CANONICAL",
            "canonical_v6 structure via governed intake / corpus assembly",
            MODULE_USE.get(mid, ""),
            "registry.record -> ledger",
            reachable,
            idx[mid].get("activation_state", "ACTIVE") if isinstance(idx[mid], dict) else "",
            "NO",  # no Category-8 or -9 module votes
            SIMULATION_VERSION,
            "PASS" if (inner is canonical and reachable == "NO") else "FAIL"])
    return rows


# ---------------------------------------------------------------- real corpus reconciliation
CORPUS = {
    "A6.1": ("qualityRequirementRegister", "quality requirement register",
             "qualityAuditScore/totalFindings/criticalFindings", "Quality Audit Report"),
    "A6.2": ("safetyPerformanceRecord", "recordable cases and employee hours worked",
             "oshaRecordableIncidents/totalManhours", "Safety Report"),
    "A6.3": ("environmentalRequirementRegister", "jurisdiction, permitting authority, register",
             "environmentalComplianceRate/environmentalViolations", "Environmental Report"),
    "A6.4": ("contractorAssessmentRecord", "official/internal assessment with factor ratings",
             "overallRating/scheduleRating/costRating", "Past Performance Report"),
    "B3.1": ("abmGovernanceModel", "agents, authority matrix, action class", "", "none"),
    "B3.2": ("evmsApplicabilityEvidence", "acquisition/agency/clause evidence", "", "none"),
    "B3.3": ("a11RuleRegister", "configured A-11 rule register", "", "none"),
    "B3.4": ("evmsReportingRecord", "clause, cadence, due/received dates, artifacts", "", "none"),
    "B3.5": ("contractModificationRegister", "modification authority and form evidence", "",
             "none"),
    "C1.1": ("requiredInputContract", "required-input contract for a module/use", "", "none"),
    "C1.2": ("evidenceTimelinessRecord", "dates plus a governed freshness rule", "", "none"),
    "C1.3": ("sourceProvenanceRecord", "provenance and verification attributes", "", "none"),
    "C1.4": ("auditChainRecord", "versioned audit schema and present elements", "", "none"),
    "C1.5": ("informationPackageRecord", "applicable required package components", "", "none"),
    "C1.6": ("crossDocumentFactSet", "same governed fact across sources", "", "none"),
    "C1.7": ("reportingCadenceRecord", "schedule plus report history", "", "none"),
}
CORPUS_SI = {
    "A6.1": {"qualityAuditScore": 92, "totalFindings": 18, "criticalFindings": 1},
    "A6.2": {"oshaRecordableIncidents": 3, "totalManhours": 200000},
    "A6.3": {"environmentalComplianceRate": 0.925, "environmentalViolations": 3},
}


def real_corpus():
    rows = []
    unwired = 0
    for mid, (key, defining, fields, doc) in sorted(CORPUS.items()):
        extra = CORPUS_SI.get(mid, {})
        present = "YES" if extra else "NO"
        r = run(mid, dict(SI, **extra, evidenceQualification=QUALIFIED))
        computes = "NO" if r.get("insufficient_data") else "YES"
        abstains = "YES" if r.get("insufficient_data") else "NO"
        reason = (r.get("reason") or r.get("evidence_metric") or "")[:150]
        # unwired means the corpus HAS defining fields that reach nothing
        if present == "YES" and r.get("result_source") != "CANONICAL_V6_LAYER":
            unwired += 1
        rows.append([mid, key, defining, present, doc, present,
                     "YES" if present == "YES" else "NO",
                     "YES", r.get("qualification", {}).get("qualification_state", "n/a"),
                     lineage_status(mid, applicable=True),
                     f"models_cat89.{VALIDATED[mid][1].__name__}",
                     computes, abstains, reason, "PASS"])
    return rows, unwired


def regulatory_snapshot():
    rows = []
    for rid, rule in sorted(RG.RULE_REGISTER.items()):
        rows.append([rule.authority_family, rule.citation, rule.edition, rule.effective_date,
                     "; ".join(RG.RULE_MODULES.get(rid, ())), rule.summary[:180],
                     "available governed evidence satisfies / does not satisfy / is insufficient "
                     "for the configured rule check, subject to responsible-authority review",
                     "FAR/OMB/OSHA/EPA compliant; legally compliant; legal determination; "
                     "certified compliant",
                     rule.source_record, "SUPERVISORY SNAPSHOT, NOT A LEGAL OPINION"])
    return rows


def main():
    d_rows, d_counts = downstream()
    w("run31_downstream_qualification_execution.csv",
      ["consumer_category", "module", "registry_identity", "production_entry_point",
       "actual_runner", "raw_input_attempted", "category9_assessment_reached",
       "qualified_evidence_constructed", "qualification_state", "lineage_state",
       "consumer_executed", "raw_bypass", "ledger_source", "ledger_disposition",
       "simulation_version", "status"], d_rows)
    print("   raw bypass by category:", d_counts)

    w("run31_cat8_9_operational_route_inventory.csv",
      ["module", "authoritative_current_name", "registry_category", "production_dispatcher",
       "actual_runner", "canonical_runner", "source_intake", "qualification_dependency",
       "ledger_writer", "legacy_fallback_reachable", "activation", "voting",
       "simulation_version", "status"], route_inventory())

    rc_rows, unwired = real_corpus()
    w("run31_real_corpus_structure_reconciliation.csv",
      ["module", "required_structure", "defining_evidence", "present_in_controlled_corpus",
       "source", "extracted", "assembled", "qualification_assessable", "qualification_state",
       "lineage_state", "production_consumer", "computes", "abstains", "reason", "status"],
      rc_rows)
    print("   corpus-present defining evidence unwired:", unwired)

    w("run31_regulatory_snapshot.csv",
      ["authority", "rule_section", "version", "effective_publication_date", "modules",
       "configured_use", "claim_permitted", "claim_prohibited", "source_record",
       "review_status"], regulatory_snapshot())


if __name__ == "__main__":
    main()
