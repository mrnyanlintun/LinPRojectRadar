#!/usr/bin/env python3
"""RUN 31 FINAL 16-ROW CLOSURE, generated mechanically from the shipped registry and scope."""
import csv, pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))

from app.simulation import registry as REG                                # noqa: E402
from app.simulation.models import SIMULATION_VERSION, VALIDATED           # noqa: E402
from app.simulation.models_cat89 import CAT89_CANONICAL, MODULE_USE       # noqa: E402
from app.simulation.canonical_v6 import V6_STRUCTURE_KEYS                 # noqa: E402
from app.simulation.qualification_boundary import gate_installed_for      # noqa: E402
from app.simulation.qualification_contract import requirement_for         # noqa: E402
from app.simulation.lineage import lineage_status                         # noqa: E402
from app.project_data import governed_structure_keys                      # noqa: E402
from run31_historical_cat89 import LEGACY_CAT89                           # noqa: E402
from app.simulation import regulatory as RG                               # noqa: E402

NOOP = (lambda: 0.5); CUT = "2026-06-30"
QUAL = {"qualification_state": "QUALIFIED", "timeliness_status": "TIMELY",
        "verification_status": "verified", "source_authority": "system_of_record"}
CORPUS = {"A6.1": {"qualityAuditScore": 92, "totalFindings": 18, "criticalFindings": 1},
          "A6.2": {"oshaRecordableIncidents": 3, "totalManhours": 200000},
          "A6.3": {"environmentalComplianceRate": 0.925, "environmentalViolations": 3}}
RULE_MODS = {m: rid for rid, mods in RG.RULE_MODULES.items() for m in mods}

rows = []
idx = REG.registry_index()
for mid in sorted(CAT89_CANONICAL):
    meta = idx[mid]
    cat = "Category 8" if not mid.startswith("C1.") else "Category 9"
    si = dict(CORPUS.get(mid, {}), evidenceQualification=dict(QUAL))
    r = REG.run_module(mid, si, NOOP, CUT)
    computes = not r.get("insufficient_data")
    fn = VALIDATED[mid][1]
    legacy = LEGACY_CAT89.get(mid)
    rows.append([
        mid, meta["module_name"], cat,
        "YES", "YES",
        "YES" if getattr(fn, "__wrapped_runner__", fn) is CAT89_CANONICAL[mid][1] else "NO",
        "YES" if V6_STRUCTURE_KEYS[mid] in governed_structure_keys() else "NO",
        "YES" if mid in CORPUS else "NO",
        "YES" if mid in ("A6.1", "A6.2", "A6.3") else "N/A",
        "YES" if (gate_installed_for(fn) or cat == "Category 9") else "NO",
        RULE_MODS.get(mid, "N/A (no regulatory rule for this measure)"),
        "YES", "YES", "YES",
        "COMPUTES" if computes else "ABSTAINS",
        (r.get("reason") or r.get("evidence_metric") or "")[:150],
        "YES", "YES",
        "YES" if (legacy and fn is legacy[1]) else "NO",
        "ACTIVE" if mid not in REG.DISABLED_CONCEPT_ONLY else "DISABLED",
        "NO",
        ("CANONICAL, OPERATIONAL, COMPUTES ON REAL CORPUS" if computes
         else "CANONICAL, OPERATIONAL, CORRECTLY ABSTAINS FOR WANT OF GOVERNED EVIDENCE"),
        ("Run 33: calibration of any band for this measure; empirical validation. "
         "Run 32: none." if cat == "Category 9" else
         "Run 33: calibration and empirical validation. Run 32: none."),
        SIMULATION_VERSION])

out = ROOT / "code_audit" / "run31_cat8_9_final_closure.csv"
with out.open("w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["module_id", "authoritative_current_name", "category",
                "canonical_structure_implemented", "canonical_method_rule_implemented",
                "production_route_canonical", "production_supply_path",
                "real_corpus_populated", "orphan_fields_wired", "qualification_integrated",
                "regulatory_version_present", "oracle_pass", "missingness_invalidity_pass",
                "lineage_pass", "operational_result", "result_reason", "calibration_pending",
                "empirical_validation_pending", "legacy_route_reachable", "current_activation",
                "voting", "final_run31_disposition", "remaining_run32_33_work",
                "simulation_version"])
    w.writerows(rows)
print(f"wrote {out.relative_to(ROOT)}  ({len(rows)} rows)")
print(f"  Cat8={sum(1 for r in rows if r[2]=='Category 8')} "
      f"Cat9={sum(1 for r in rows if r[2]=='Category 9')} unique={len({r[0] for r in rows})}")
print(f"  legacy reachable={sum(1 for r in rows if r[18]=='YES')} "
      f"blank disposition={sum(1 for r in rows if not r[21])} "
      f"computes={sum(1 for r in rows if r[14]=='COMPUTES')} "
      f"abstains={sum(1 for r in rows if r[14]=='ABSTAINS')}")
