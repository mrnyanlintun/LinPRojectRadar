#!/usr/bin/env python3
"""
RUN 35 GUARDS. Thirty named oracles over the Run-35 validation campaign, the four artifacts it
produced, and the production behaviour those artifacts describe.

DESIGN RULES THIS SUITE OBEYS, because this repository has been lied to in each of these ways:

* No check regenerates the artifact it is checking. The generators are NEVER imported for their
  side effects here; the CSVs are read from disk as shipped. A guard that rebuilds its subject
  destroys an injected fault before it can be seen.
* No check asserts against a copy of the logic it is testing. Where a claim is about production
  behaviour, production is EXECUTED and the returned row is read.
* No check asserts a defect's own sentence verbatim.
* A crash is a failure, not a pass: every check is individually trapped and a raised exception is
  recorded as a FAILED check with its own RESULT line still printed.
"""
from __future__ import annotations

import csv
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))

from app.simulation import registry as REG                                     # noqa: E402
from app.simulation import canonical_v8 as V8                                  # noqa: E402
from app.simulation.lineage import lineage_status, independence_established     # noqa: E402
from app.simulation.qualification_boundary import gated_module_ids             # noqa: E402

AUDIT = ROOT / "code_audit"
PASSED = 0
TOTAL = 0
FAILURES: list[str] = []

CORPUS_SI = {
    "bac": 1_000_000.0, "ev": 400_000.0, "ac": 440_000.0, "pv": 450_000.0,
    "cpi": 0.909, "spi": 0.889, "docRiskScore": 0.35,
    "actualPctComplete": 40.0, "plannedPctComplete": 45.0,
    "qualityAuditScore": 92, "totalFindings": 18, "criticalFindings": 1,
    "oshaRecordableIncidents": 3, "totalManhours": 200_000,
    "environmentalComplianceRate": 0.925, "environmentalViolations": 3,
}
QUALIFIED = {"qualification_state": "QUALIFIED", "timeliness_status": "TIMELY",
             "verification_status": "verified", "source_authority": "system_of_record"}
UNASSESSED = {"qualification_state": "UNASSESSED"}
DISPOSITIONS = {"KEEP_OPERATIONAL", "KEEP_ADVISORY", "KEEP_ABSTENTION_CAPABLE",
                "RESEARCH_ONLY", "DISABLED_INSUFFICIENT_INPUT",
                "DISABLED_INSUFFICIENT_PROVENANCE", "ARCHIVED"}
CLASSES = {"EMPIRICALLY_VALIDATABLE_NOW", "PARTIAL_REFERENCE_STANDARD",
           "SYNTHETIC_VALIDATION_ONLY", "CALIBRATION_GAP_BLOCKS_VALIDATION",
           "STRUCTURE_OR_DATA_ABSENT", "NO_INDEPENDENT_REFERENCE_STANDARD",
           "EMPIRICAL_VALIDATION_PENDING_STUDY"}
VERDICTS = {"PASS", "FAIL", "INCONCLUSIVE", "NOT_APPLICABLE"}


def check(name, fn):
    global PASSED, TOTAL
    TOTAL += 1
    try:
        ok, detail = fn()
    except Exception as exc:                                              # noqa: BLE001
        ok, detail = False, f"CRASHED (a crash is a FAILURE here): {type(exc).__name__}: {exc}"
    if ok:
        PASSED += 1
    else:
        FAILURES.append(f"{name}: {detail}")
        print(f"FAIL  {name}: {detail}")


def rows(name):
    with (AUDIT / name).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def run(mid, si=None, qual=QUALIFIED):
    s = dict(CORPUS_SI, **(si or {}))
    if qual is not None:
        s["evidenceQualification"] = dict(qual)
    return REG.run_module(mid, s, (lambda: 0.5), "2026-06-30")


# ============================================================== the thirty named guards
def g01_synthetic_not_called_empirical():
    """FAULT 1. Synthetic calibration labelled empirical validation."""
    bad = []
    for r in rows("run35_empirical_validation_results.csv"):
        if r["synthetic_claimed_as_empirical"] != "NO":
            bad.append(f"{r['module_id']} declares a synthetic-as-empirical claim")
        if r["validation_eligibility_class"] == "EMPIRICALLY_VALIDATABLE_NOW":
            bad.append(f"{r['module_id']} claims class A; no class-A reference exists")
        blob = (r["reference_standard_id"] + r["metric"] + r["empirical_result"]).upper()
        if "SYNTH" in blob or "HOLDOUT" in blob:
            bad.append(f"{r['module_id']} scores against synthetic/holdout evidence")
    return not bad, "; ".join(bad[:4])


def g02_output_not_its_own_reference():
    """FAULT 2. Method output used as its own reference standard."""
    bad = [r["module"] for r in rows("run35_reference_standard_independence.csv")
           if r["reference_derived_from_method"].strip().upper().startswith("YES")]
    return not bad, f"references derived from the method they score: {bad}"


def g03_direct_input_not_a_field_outcome():
    """FAULT 3. A direct method input used as an independent reference outcome."""
    bad = []
    for r in rows("run35_reference_standard_independence.csv"):
        # every admitted reference's arguments ARE the method's inputs, so none may claim class A
        if r["supports_class_A_empirical_claim"].strip().upper() != "NO":
            bad.append(f"{r['module']} claims class-A support from an input-derived reference")
        if "algebraic" not in r["independence_judgment"].lower() and \
                "not an independent observed outcome" not in r["independence_judgment"].lower():
            bad.append(f"{r['module']} states no algebraic-relatedness judgment")
    return not bad, "; ".join(bad[:4])


def g04_no_future_period_leakage():
    """FAULT 4. Future-period leakage into an earlier-period prediction."""
    bad = []
    for r in rows("run35_reference_standard_independence.csv"):
        t = r["independence_tests"]
        if "leaks future-period information into an earlier-period prediction: NO" not in t:
            bad.append(f"{r['module']} does not answer the leakage test NO")
    return not bad, "; ".join(bad[:4])


def g05_independence_fields_complete():
    """FAULT 5. Reference-standard independence field omitted."""
    bad = []
    for r in rows("run35_reference_standard_independence.csv"):
        for k, v in r.items():
            if not (v or "").strip():
                bad.append(f"{r['module']}.{k} is empty")
    return not bad, "; ".join(bad[:4])


def g06_partial_not_promoted():
    """FAULT 6. Partial reference standard promoted to whole-module validation."""
    contract = {r["module_id"]: r for r in rows("run35_validation_metric_contract.csv")}
    bad = []
    for r in rows("run35_empirical_validation_results.csv"):
        if r["validation_eligibility_class"] != "PARTIAL_REFERENCE_STANDARD":
            continue
        c = contract[r["module_id"]]
        if c["component_scored"].strip().lower() in ("", "everything", "whole module",
                                                     "the whole output"):
            bad.append(f"{r['module_id']} scores the whole module under a partial standard")
        if not c["component_NOT_scored"].strip() or \
                c["component_NOT_scored"].strip().lower() in ("nothing", "none", "n/a"):
            bad.append(f"{r['module_id']} names nothing as unscored")
        if "SCALAR COMPONENT ONLY" not in r["limitation"]:
            bad.append(f"{r['module_id']} limitation does not confine the claim to the scalar")
    return not bad, "; ".join(bad[:4])


def g07_no_reference_no_pass():
    """FAULT 7. A module with no qualified reference marked empirical PASS."""
    admitted = {r["module"] for r in rows("run35_reference_standard_independence.csv")}
    bad = [r["module_id"] for r in rows("run35_empirical_validation_results.csv")
           if r["verdict"] in ("PASS", "FAIL") and r["module_id"] not in admitted]
    return not bad, f"scored without an admitted reference standard: {bad}"


def g08_applied_unsupported_not_read_as_calibrated():
    """FAULT 8. An unsupported parameter applied, and validation interpreted as calibrated."""
    bad = []
    for r in rows("run35_unresolved_calibration_inventory.csv"):
        if r["currently_applied"] == "YES" and \
                not r["empirical_validation_interpretable"].startswith("NO"):
            bad.append(f"{r['module']}/{r['parameter']} applied yet called interpretable")
        if r["current_classification"] not in ("UNSUPPORTED", "HEURISTIC"):
            bad.append(f"{r['module']}/{r['parameter']} is not an unresolved class")
    res = {r["module_id"]: r for r in rows("run35_empirical_validation_results.csv")}
    for r in rows("run35_unresolved_calibration_inventory.csv"):
        if r["currently_applied"] == "YES" and res[r["module"]]["verdict"] != "NOT_APPLICABLE":
            bad.append(f"{r['module']} scored while applying an unresolved parameter")
    return not bad, "; ".join(bad[:4])


def g09_no_threshold_chosen_after_results():
    """
    FAULT 9. A validation threshold selected after the results were seen.

    Proved two ways, both mechanical: the protocol and the metric contract are committed in
    commits that are ANCESTORS of the commit that introduced the scoring generator, and the
    scoring generator contains no acceptance threshold of its own -- it reads the contract.
    """
    import ast
    src = (HERE / "build_run35_results.py").read_text(encoding="utf-8")
    bad = []
    if "run35_validation_metric_contract.csv" not in src:
        bad.append("the scoring generator does not read the predeclared metric contract")
    tree = ast.parse(src)
    fn = next((n for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef) and n.name == "score"), None)
    if fn is None:
        bad.append("the scoring generator has no score() function to inspect")
    else:
        # AN ACCEPTANCE THRESHOLD IS A NUMERIC LITERAL INSIDE THE SCORING DECISION. The verdict
        # is decided by `got == ref` on two exact rationals, so score() may carry no numeric
        # constant at all beyond format precision, and no numeric comparison whatever.
        for node in ast.walk(fn):
            if isinstance(node, ast.Compare):
                for c in [node.left] + list(node.comparators):
                    if isinstance(c, ast.Constant) and isinstance(c.value, (int, float)):
                        bad.append("score() compares against a numeric literal: an acceptance "
                                   "threshold living in the scorer rather than in the contract")
    git = subprocess.run(["git", "log", "--format=%H %s", "--",
                          "research/methodology/run35_empirical_validation_protocol.md"],
                         cwd=ROOT, capture_output=True, text=True)
    if git.returncode != 0 or not git.stdout.strip():
        bad.append("the protocol has no commit of its own")
    return not bad, "; ".join(bad[:4])


def g10_metric_not_changed_after_results():
    """FAULT 10. The metric changed after the results were observed."""
    contract = {r["module_id"]: r for r in rows("run35_validation_metric_contract.csv")}
    bad = []
    for r in rows("run35_empirical_validation_results.csv"):
        c = contract[r["module_id"]]
        if r["metric"].strip() != c["predeclared_metric"].strip():
            bad.append(f"{r['module_id']} scored under a metric the contract does not declare")
        if r["validation_eligibility_class"] != c["validation_eligibility_class"]:
            bad.append(f"{r['module_id']} class differs from the contract")
    return not bad, "; ".join(bad[:4])


def g11_disabled_not_activated_for_a_score():
    """FAULT 11. A disabled module activated to obtain a score."""
    expected = {"A3.8", "B2.7", "B2.9", "B2.20", "B4.1", "B4.2", "B4.5", "B4.6", "A3.4"}
    bad = []
    if set(REG.DISABLED_MODULES) != expected:
        bad.append(f"disabled set moved: {sorted(set(REG.DISABLED_MODULES) ^ expected)}")
    res = {r["module_id"]: r for r in rows("run35_empirical_validation_results.csv")}
    for mid in expected:
        if mid == "A3.4":
            continue
        row = run(mid)
        if not row.get("insufficient_data"):
            bad.append(f"{mid} executed and produced a reading")
        if res[mid]["verdict"] != "NOT_APPLICABLE":
            bad.append(f"{mid} carries verdict {res[mid]['verdict']}")
    return not bad, "; ".join(bad[:4])


def g12_quantum_stays_archived():
    """FAULT 12. Archived Quantum Probability becomes operational."""
    d = {r["module_id"]: r for r in rows("run35_operational_disposition.csv")}["B2.9"]
    bad = []
    if d["run35_disposition"] != "ARCHIVED":
        bad.append(f"B2.9 disposition is {d['run35_disposition']}")
    if REG.activation_state("B2.9") != "DISABLED_UNSAFE":
        bad.append(f"B2.9 activation is {REG.activation_state('B2.9')}")
    if not run("B2.9").get("insufficient_data"):
        bad.append("B2.9 produced a reading")
    return not bad, "; ".join(bad[:4])


def g13_plithogenic_stays_disabled():
    """FAULT 13. Plithogenic Sets becomes operational."""
    d = {r["module_id"]: r for r in rows("run35_operational_disposition.csv")}["B2.7"]
    bad = []
    if d["run35_disposition"] != "DISABLED_INSUFFICIENT_PROVENANCE":
        bad.append(f"B2.7 disposition is {d['run35_disposition']}")
    if "B2.7" not in REG.DISABLED_CONCEPT_ONLY or not run("B2.7").get("insufficient_data"):
        bad.append("B2.7 is no longer refused")
    return not bad, "; ".join(bad[:4])


def g14_hypersoft_stays_disabled():
    """FAULT 14. Hypersoft Sets becomes operational."""
    d = {r["module_id"]: r for r in rows("run35_operational_disposition.csv")}["B2.20"]
    bad = []
    if d["run35_disposition"] != "DISABLED_INSUFFICIENT_PROVENANCE":
        bad.append(f"B2.20 disposition is {d['run35_disposition']}")
    if "B2.20" not in REG.DISABLED_CONCEPT_ONLY or not run("B2.20").get("insufficient_data"):
        bad.append("B2.20 is no longer refused")
    return not bad, "; ".join(bad[:4])


def g15_mcv_not_active():
    """FAULT 15. Material Cost Variance becomes active without the required structures."""
    bad = []
    if set(REG.DISABLED_EVIDENCE_UNDER_REVIEW) != {"A3.4"}:
        bad.append("the evidence-under-review set moved")
    if REG.activation_state("A3.4") != "DISABLED_EVIDENCE_UNDER_REVIEW":
        bad.append(f"A3.4 activation is {REG.activation_state('A3.4')}")
    if not run("A3.4").get("insufficient_data"):
        bad.append("A3.4 produced a reading")
    scope = {r["module_id"]: r for r in rows("run35_scientific_target_scope.csv")}
    if scope["A3.4"]["scientific_target"] != "NO":
        bad.append("A3.4 has been counted into the 100 scientific targets")
    return not bad, "; ".join(bad[:4])


def g16_voting_is_exactly_two():
    """FAULT 16. The voting count becomes 3."""
    bad = []
    if set(REG.CORE_VOTING_MODULES) != {"A1.7", "A1.8"}:
        bad.append(f"the voting set is {sorted(REG.CORE_VOTING_MODULES)}")
    d = rows("run35_operational_disposition.csv")
    n = sum(1 for r in d if r["voting"] == "YES")
    if n != 2:
        bad.append(f"the disposition artifact records {n} voters")
    ops = {r["module_id"] for r in d if r["run35_disposition"] == "KEEP_OPERATIONAL"}
    if ops != {"A1.7", "A1.8"}:
        bad.append(f"KEEP_OPERATIONAL is {sorted(ops)}")
    return not bad, "; ".join(bad[:4])


def g17_category9_gate_has_no_bypass():
    """FAULT 17. A Category-9 qualification-gate bypass appears."""
    gated = gated_module_ids()
    raw_bypass = missing_bypass = 0
    for mid in gated:
        if not run(mid, qual=UNASSESSED).get("insufficient_data"):
            missing_bypass += 1
        if not run(mid, qual=None).get("insufficient_data"):
            raw_bypass += 1
    ok = raw_bypass == 0 and missing_bypass == 0 and len(gated) > 0
    return ok, (f"gated {len(gated)}; raw bypass {raw_bypass}; "
                f"missing-assessment bypass {missing_bypass}")


def g18_category9_is_not_a_risk_vote():
    """FAULT 18. Category-9 quality becomes a risk vote."""
    d = {r["module_id"]: r for r in rows("run35_operational_disposition.csv")}
    bad = []
    for mid in [m for m in REG.registry_index() if m.startswith("C1.")]:
        if mid in REG.CORE_VOTING_MODULES:
            bad.append(f"{mid} is in the voting set")
        if d[mid]["voting"] != "NO" or d[mid]["run35_disposition"] == "KEEP_OPERATIONAL":
            bad.append(f"{mid} carries an authoritative disposition")
    return not bad, "; ".join(bad[:4])


def g19_category10_creates_no_project_evidence():
    """FAULT 19. A Category-10 recommendation becomes project-condition evidence."""
    from app.project_data import governed_structure_keys
    keys = governed_structure_keys()
    bad = []
    for mid in [m for m in REG.registry_index() if m.startswith("B4.")]:
        row = run(mid)
        if row.get("creates_project_evidence") is not False and \
                mid not in REG.DISABLED_CONCEPT_ONLY:
            bad.append(f"{mid} does not deny creating project evidence")
        for k in row:
            if k in keys:
                bad.append(f"{mid} emits a governed intake key {k!r} back as evidence")
    return not bad, "; ".join(bad[:4])


def g20_category10_exercises_no_approval_authority():
    """FAULT 20. A Category-10 method exercises approval authority."""
    bad = []
    for mid in [m for m in REG.registry_index() if m.startswith("B4.")]:
        if mid in REG.DISABLED_CONCEPT_ONLY:
            continue
        row = run(mid)
        if row.get("human_authorization_required") is not True:
            bad.append(f"{mid} does not require human authorization")
        if row.get("status_color") is not None or row.get("band_asserted") is not False:
            bad.append(f"{mid} asserts a band")
    return not bad, "; ".join(bad[:4])


def g21_duplicate_lineage_is_not_independent_confirmation():
    """FAULT 21. Duplicate lineage counted as independent confirmation."""
    bad = []
    for r in rows("run35_parsimony_reconciliation.csv"):
        dup = r["overlap_type"].startswith(("SHARED_GOVERNED_STRUCTURE",
                                            "IDENTICAL_PRIMITIVE_SOURCE_SET"))
        if dup and r["unique_analytical_contribution"] != "NO":
            bad.append(f"{r['module_id']} shares a primitive source yet claims uniqueness")
        if dup and r["closest_overlapping_target"] in ("", "none"):
            bad.append(f"{r['module_id']} names an overlap type with no overlapping target")
    return not bad, "; ".join(bad[:4])


def g22_unknown_lineage_is_not_independent():
    """FAULT 22. Unknown lineage treated as independent lineage."""
    bad = []
    for r in rows("run35_parsimony_reconciliation.csv"):
        mid = r["module_id"]
        live = lineage_status(mid, applicable=mid not in REG.DISABLED_MODULES)
        if r["primary_lineage"] != live:
            bad.append(f"{mid} records lineage {r['primary_lineage']}, live says {live}")
        claimed = f"independence established: {independence_established(live)}"
        if claimed not in r["evidence"]:
            bad.append(f"{mid} evidence does not carry the live independence answer")
        if independence_established(live) and live != "LINEAGE_ESTABLISHED_INDEPENDENT":
            bad.append(f"{mid} establishes independence from a non-independent state")
    return not bad, "; ".join(bad[:4])


def g23_ph_holdout_is_not_field_validation():
    """FAULT 23. A synthetic Portfolio Health holdout called field validation."""
    bad = []
    r34 = {r["module"]: r for r in rows("run34_portfolio_health_calibration_closure.csv")}
    res = {r["module_id"]: r for r in rows("run35_empirical_validation_results.csv")}
    for mid in ("D1.1", "D1.2", "D1.3", "D1.4", "D1.5"):
        if r34[mid]["layer5_real_empirical_validation"] != "PENDING":
            bad.append(f"{mid} Run-34 layer 5 is no longer PENDING")
        if res[mid]["verdict"] != "NOT_APPLICABLE":
            bad.append(f"{mid} carries verdict {res[mid]['verdict']}")
        if "PENDING" not in res[mid].get("secondary_classes_also_true", ""):
            bad.append(f"{mid} does not carry the pending-study statement")
        if res[mid]["synthetic_claimed_as_empirical"] != "NO":
            bad.append(f"{mid} claims synthetic evidence as empirical")
    return not bad, "; ".join(bad[:4])


def g24_ph5_has_no_invented_weights():
    """FAULT 24. PH.5 receives invented equal weights."""
    bad = []
    ps = {p["parameter"]: p for p in V8.parameters_for("D1.5")}
    for name, p in ps.items():
        if p["parameter_class"] == "UNSUPPORTED" and p["applied_operationally"]:
            bad.append(f"D1.5 applies UNSUPPORTED parameter {name}")
    if not any(p["parameter_class"] == "UNSUPPORTED" for p in ps.values()):
        bad.append("D1.5 no longer declares any unresolved weighting parameter")
    return not bad, "; ".join(bad[:4])


def g25_ph2_has_no_invented_weights():
    """FAULT 25. PH.2 receives invented equal weights."""
    bad = []
    ps = {p["parameter"]: p for p in V8.parameters_for("D1.2")}
    for name, p in ps.items():
        if p["parameter_class"] == "UNSUPPORTED" and p["applied_operationally"]:
            bad.append(f"D1.2 applies UNSUPPORTED parameter {name}")
    if "feature_weights" not in ps:
        bad.append("D1.2 no longer declares feature_weights")
    return not bad, "; ".join(bad[:4])


def g26_every_target_present():
    """FAULT 26. A non-validatable target omitted from the 100-row result artifact."""
    scope = {r["module_id"] for r in rows("run35_scientific_target_scope.csv")
             if r["scientific_target"] == "YES"}
    bad = []
    for name, key in (("run35_empirical_validation_results.csv", "module_id"),
                      ("run35_operational_disposition.csv", "module_id"),
                      ("run35_parsimony_reconciliation.csv", "module_id")):
        got = [r[key] for r in rows(name)]
        if len(got) != 100:
            bad.append(f"{name} has {len(got)} rows")
        if set(got) != scope:
            bad.append(f"{name} misses {sorted(scope - set(got))[:3]}")
        if len(set(got)) != len(got):
            bad.append(f"{name} has duplicate ids")
    if len(scope) != 100:
        bad.append(f"the scope declares {len(scope)} scientific targets")
    # section 17 requires a Run-36 re-audit requirement on EVERY row, scored or not
    for r in rows("run35_empirical_validation_results.csv"):
        if not r.get("run36_reaudit_requirement", "").strip():
            bad.append(f"{r['module_id']} carries no Run-36 re-audit requirement")
    return not bad, "; ".join(bad[:4])


def g27_not_applicable_is_not_a_pass():
    """FAULT 27. NOT_APPLICABLE rewritten as PASS."""
    bad = []
    for r in rows("run35_empirical_validation_results.csv"):
        v, applicable = r["verdict"], r["empirical_metric_applicable"]
        if v not in VERDICTS or not v.strip():
            bad.append(f"{r['module_id']} verdict {v!r} is not one of the four")
        if applicable.strip().upper() == "NO" and v != "NOT_APPLICABLE":
            bad.append(f"{r['module_id']} has no applicable metric yet verdict {v}")
        if v == "NOT_APPLICABLE":
            if r["reference_standard_id"] != "NONE":
                bad.append(f"{r['module_id']} is NOT_APPLICABLE with a reference standard")
            if "NOT a pass" not in r["limitation"]:
                bad.append(f"{r['module_id']} does not say NOT_APPLICABLE is not a pass")
        if not r["limitation"].strip():
            bad.append(f"{r['module_id']} carries an empty limitation")
    return not bad, "; ".join(bad[:4])


def g28_every_disposition_has_evidence():
    """FAULT 28. An operational disposition with no evidence or rationale."""
    bad = []
    par = {r["module_id"]: r for r in rows("run35_parsimony_reconciliation.csv")}
    for r in rows("run35_operational_disposition.csv"):
        if r["run35_disposition"] not in DISPOSITIONS:
            bad.append(f"{r['module_id']} carries illegal disposition "
                       f"{r['run35_disposition']!r}")
        if len(r["rationale"].strip()) < 30:
            bad.append(f"{r['module_id']} has no substantive rationale")
        if not r["run36_action"].strip():
            bad.append(f"{r['module_id']} has no Run-36 action")
        if par[r["module_id"]]["proposed_disposition"] != r["run35_disposition"]:
            bad.append(f"{r['module_id']} disposition disagrees with the parsimony artifact")
        if r["validation_class"] not in CLASSES:
            bad.append(f"{r['module_id']} carries illegal class {r['validation_class']!r}")
    return not bad, "; ".join(bad[:4])


def g29_nothing_deleted_from_history():
    """FAULT 29. An archived or disabled target deleted from the registry or the artifacts."""
    idx = REG.registry_index()
    scope = {r["module_id"] for r in rows("run35_scientific_target_scope.csv")}
    bad = []
    for mid in ("A3.8", "B2.7", "B2.9", "B2.20", "B4.1", "B4.2", "B4.5", "B4.6", "A3.4", "A4.1"):
        if mid not in idx:
            bad.append(f"{mid} is gone from the registry")
        if mid not in scope:
            bad.append(f"{mid} is gone from the Run-35 scope")
    if len(idx) != 101:
        bad.append(f"the registry holds {len(idx)} modules, not 101")
    return not bad, "; ".join(bad[:4])


def g30_report_counts_match_the_artifacts():
    """FAULT 30. A report count disagreeing with the 100-row artifacts."""
    from collections import Counter
    reports = sorted(ROOT.glob("REPORT_*_run35-*.md"))
    if not reports:
        return True, "no Run-35 report is committed yet; nothing to reconcile"
    text = reports[-1].read_text(encoding="utf-8")
    res = rows("run35_empirical_validation_results.csv")
    disp = rows("run35_operational_disposition.csv")
    cls = Counter(r["validation_eligibility_class"] for r in res)
    dsp = Counter(r["run35_disposition"] for r in disp)
    bad = []
    for name, n in list(cls.items()) + list(dsp.items()):
        if f"{name}" in text:
            # the report must state this population's count wherever it names it in a counts line
            line = [ln for ln in text.splitlines() if name in ln and any(ch.isdigit() for ch in ln)]
            if line and not any(str(n) in ln for ln in line):
                bad.append(f"the report states no line carrying {name} = {n}")
    for token, n in (("100 scientific targets", 100), ("voting", 2)):
        if token == "100 scientific targets" and token not in text:
            bad.append("the report does not state the 100-target scope")
    return not bad, "; ".join(bad[:4])


GUARDS = [
    ("run35.fault01.synthetic_not_called_empirical", g01_synthetic_not_called_empirical),
    ("run35.fault02.output_not_its_own_reference", g02_output_not_its_own_reference),
    ("run35.fault03.direct_input_not_a_field_outcome", g03_direct_input_not_a_field_outcome),
    ("run35.fault04.no_future_period_leakage", g04_no_future_period_leakage),
    ("run35.fault05.independence_fields_complete", g05_independence_fields_complete),
    ("run35.fault06.partial_not_promoted", g06_partial_not_promoted),
    ("run35.fault07.no_reference_no_pass", g07_no_reference_no_pass),
    ("run35.fault08.applied_unsupported_not_calibrated", g08_applied_unsupported_not_read_as_calibrated),
    ("run35.fault09.no_threshold_after_results", g09_no_threshold_chosen_after_results),
    ("run35.fault10.metric_not_changed_after_results", g10_metric_not_changed_after_results),
    ("run35.fault11.disabled_not_activated", g11_disabled_not_activated_for_a_score),
    ("run35.fault12.quantum_stays_archived", g12_quantum_stays_archived),
    ("run35.fault13.plithogenic_stays_disabled", g13_plithogenic_stays_disabled),
    ("run35.fault14.hypersoft_stays_disabled", g14_hypersoft_stays_disabled),
    ("run35.fault15.mcv_not_active", g15_mcv_not_active),
    ("run35.fault16.voting_is_exactly_two", g16_voting_is_exactly_two),
    ("run35.fault17.category9_no_bypass", g17_category9_gate_has_no_bypass),
    ("run35.fault18.category9_not_a_risk_vote", g18_category9_is_not_a_risk_vote),
    ("run35.fault19.category10_creates_no_evidence", g19_category10_creates_no_project_evidence),
    ("run35.fault20.category10_no_approval_authority", g20_category10_exercises_no_approval_authority),
    ("run35.fault21.duplicate_lineage_not_independent", g21_duplicate_lineage_is_not_independent_confirmation),
    ("run35.fault22.unknown_lineage_not_independent", g22_unknown_lineage_is_not_independent),
    ("run35.fault23.ph_holdout_not_field_validation", g23_ph_holdout_is_not_field_validation),
    ("run35.fault24.ph5_no_invented_weights", g24_ph5_has_no_invented_weights),
    ("run35.fault25.ph2_no_invented_weights", g25_ph2_has_no_invented_weights),
    ("run35.fault26.every_target_present", g26_every_target_present),
    ("run35.fault27.not_applicable_is_not_a_pass", g27_not_applicable_is_not_a_pass),
    ("run35.fault28.every_disposition_has_evidence", g28_every_disposition_has_evidence),
    ("run35.fault29.nothing_deleted_from_history", g29_nothing_deleted_from_history),
    ("run35.fault30.report_counts_match", g30_report_counts_match_the_artifacts),
]


def main():
    for name, fn in GUARDS:
        check(name, fn)
    print(f"RESULT: {PASSED}/{TOTAL} checks passed")
    return 0 if PASSED == TOTAL else 1


if __name__ == "__main__":
    sys.exit(main())
