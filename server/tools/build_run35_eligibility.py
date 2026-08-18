#!/usr/bin/env python3
"""
RUN 35 STAGE 1: the scientific-target scope, the unresolved-calibration inventory, the
reference-standard independence register and the target-to-metric contract.

NOTHING HERE SCORES ANYTHING. This generator establishes *availability* only: which targets
exist, what they can and cannot execute on the governed corpus, which parameters are unresolved
and actually applied, which proposed reference standards survive the independence rules, and
what metric each target's output type would admit. It is committed BEFORE the scoring generator
runs, so the metric contract cannot have been chosen after a result was seen.

Every population is derived by execution or from a live authority. Nothing is transcribed from
prose.

Writes:
  code_audit/run35_scientific_target_scope.csv
  code_audit/run35_unresolved_calibration_inventory.csv
  code_audit/run35_reference_standard_independence.csv
  code_audit/run35_validation_metric_contract.csv
"""
from __future__ import annotations

import csv
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))

from app.simulation import registry as REG                                    # noqa: E402
from app.simulation.lineage import lineage_status                             # noqa: E402
from app.simulation.models import SIMULATION_VERSION                          # noqa: E402
from app.simulation.parameters import PARAMETER_PROVENANCE_BY_MODULE as PROV   # noqa: E402
from app.simulation.portfolio import PORTFOLIO_VALIDATED                       # noqa: E402
from app.simulation.canonical_v8 import parameters_for as PH_PARAMS            # noqa: E402

AUDIT = ROOT / "code_audit"
OUT_DIR = AUDIT          # a guard may redirect this; see Run 34's note on self-rewriting guards

# ------------------------------------------------------------------ the controlled corpus
#: The controlled-corpus scalar evidence, identical to the set Runs 29-32 executed against, plus
#: the Category-8 corpus scalars Run 31 established. Governed structures are NOT added: the
#: controlled corpus supplies none, which is the fact this run has to record rather than repair.
CORPUS_SI = {
    "bac": 1_000_000.0, "ev": 400_000.0, "ac": 440_000.0, "pv": 450_000.0,
    "cpi": 0.909, "spi": 0.889, "docRiskScore": 0.35,
    "actualPctComplete": 40.0, "plannedPctComplete": 45.0,
    "qualityAuditScore": 92, "totalFindings": 18, "criticalFindings": 1,
    "oshaRecordableIncidents": 3, "totalManhours": 200_000,
    "environmentalComplianceRate": 0.925, "environmentalViolations": 3,
    "evidenceQualification": {"qualification_state": "QUALIFIED",
                              "timeliness_status": "TIMELY",
                              "verification_status": "verified",
                              "source_authority": "system_of_record"},
}
CUT = "2026-06-30"
NOOP = (lambda: 0.5)

CLASSES = ("EMPIRICALLY_VALIDATABLE_NOW", "PARTIAL_REFERENCE_STANDARD",
           "SYNTHETIC_VALIDATION_ONLY", "CALIBRATION_GAP_BLOCKS_VALIDATION",
           "STRUCTURE_OR_DATA_ABSENT", "NO_INDEPENDENT_REFERENCE_STANDARD",
           "EMPIRICAL_VALIDATION_PENDING_STUDY")

#: The only reference standards Run 35 proposes. Each is a PUBLISHED IDENTITY authored outside
#: this repository. They are proposed here and then put through the protocol's independence rules
#: below; nothing is admitted by being listed.
PROPOSED_REFERENCES = {
    "A1.7": dict(
        ref_id="REF-PMI-TCPI",
        source=("Project Management Institute, A Guide to the PMBOK, 6th ed. 2017, s.7.4.2.2; "
                "PMI Practice Standard for Earned Value Management, 2nd ed. 2011"),
        period="publication is period-invariant; applied to corpus reporting period 2026-06",
        variable="to-complete performance index = (BAC - EV) / (BAC - AC)",
        method_inputs="bac, ev, ac",
        available_to_method="YES - the identity is the method's own declared definition",
        derived_from_method="NO - authored outside this repository and before it existed",
        lineage="published standards body; no lineage shared with this platform's evidence",
    ),
    "A1.8": dict(
        ref_id="REF-PMI-VAC",
        source=("Project Management Institute, A Guide to the PMBOK, 6th ed. 2017, s.7.4.2.2; "
                "PMI Practice Standard for Earned Value Management, 2nd ed. 2011"),
        period="publication is period-invariant; applied to corpus reporting period 2026-06",
        variable="variance at completion = BAC - EAC, with the index-based EAC = BAC / CPI",
        method_inputs="bac, cpi",
        available_to_method="YES - the identity is the method's own declared definition",
        derived_from_method="NO - authored outside this repository and before it existed",
        lineage="published standards body; no lineage shared with this platform's evidence",
    ),
    "A6.2": dict(
        ref_id="REF-OSHA-INCIDENCE",
        source=("OSHA recordable incidence rate identity, recordkeeping/incidence guidance; "
                "carried live in server/app/simulation/regulatory.py as OSHA-INCIDENCE-RATE"),
        period="regulatory identity, period-invariant; corpus reporting period 2026-06",
        variable="incidence rate = recordable cases * 200000 / employee hours worked",
        method_inputs="oshaRecordableIncidents, totalManhours",
        available_to_method="YES - the identity is the method's own declared definition",
        derived_from_method="NO - a regulatory authority's identity, not this platform's",
        lineage="federal regulatory authority; no lineage shared with this platform's evidence",
    ),
}


def write(name, header, rows):
    p = OUT_DIR / name
    with p.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote {name}: {len(rows)} rows")
    return rows


# ---------------------------------------------------------------- populations, derived
def populations():
    idx = REG.registry_index()
    project = {m: r for m, r in idx.items() if r["group"] != "D"}
    portfolio = {m: r for m, r in idx.items() if r["group"] == "D"}
    # the scientific project population EXCLUDES the disabled-evidence-under-review module and
    # nothing else; the supplied Document Risk Score stays in.
    scientific_project = {m: r for m, r in project.items()
                          if m not in REG.DISABLED_EVIDENCE_UNDER_REVIEW}
    return idx, project, portfolio, scientific_project


def execute(mid):
    """Run the real production entry point on the controlled corpus."""
    try:
        r = REG.run_module(mid, dict(CORPUS_SI), NOOP, CUT)
    except REG.MissingModuleError as exc:
        return {"__state__": "NOT_COMPUTED_SUPPLIED_FIELD", "__note__": str(exc)[:120]}
    except REG.PortfolioModuleError as exc:
        return {"__state__": "PORTFOLIO_ROUTE", "__note__": str(exc)[:120]}
    r["__state__"] = "ABSTAINS" if r.get("insufficient_data") else "COMPUTES"
    return r


def numeric_reading(row):
    """True when the executed row actually carries a numeric quantity that could be scored."""
    for k in ("value", "raw_value", "reading", "metric_value"):
        if isinstance(row.get(k), (int, float)):
            return True
    m = row.get("evidence_metric")
    return bool(m and re.search(r"\d", str(m)) and not row.get("insufficient_data"))


def suite_coverage():
    """Which module ids any executable suite asserts about. Laboratory/canonical evidence."""
    cov = {}
    for f in sorted((HERE).glob("test_*.py")):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for mid in re.findall(r"\b([ABCD][1-6]\.\d{1,2})\b", text):
            cov.setdefault(mid, set()).add(f.name)
    return cov


def structure_key_map():
    from app.simulation.canonical import CANONICAL_STRUCTURE_KEYS
    from app.simulation.canonical_v3 import V3_STRUCTURE_KEYS
    from app.simulation.canonical_v4 import V4_STRUCTURE_KEYS
    from app.simulation.canonical_v5 import V5_STRUCTURE_KEYS
    from app.simulation.canonical_v6 import V6_STRUCTURE_KEYS
    from app.simulation.canonical_v7 import V7_STRUCTURE_KEYS
    from app.simulation.canonical_v8 import V8_STRUCTURE_KEYS
    out = {}
    for layer, m in (("canonical", CANONICAL_STRUCTURE_KEYS), ("v3", V3_STRUCTURE_KEYS),
                     ("v4", V4_STRUCTURE_KEYS), ("v5", V5_STRUCTURE_KEYS),
                     ("v6", V6_STRUCTURE_KEYS), ("v7", V7_STRUCTURE_KEYS),
                     ("v8", V8_STRUCTURE_KEYS)):
        for mid, key in m.items():
            out.setdefault(mid, (key, layer))
    return out


# ---------------------------------------------------------------- eligibility, mechanical
def classify(mid, row, applied_unsupported, has_numeric, struct_key):
    """
    The protocol's precedence, applied mechanically:
        E -> D -> A -> B -> G -> C -> F
    """
    state = row.get("__state__")
    if mid in REG.DISABLED_MODULES:
        return ("STRUCTURE_OR_DATA_ABSENT",
                "disabled; the structure or evidence its method requires does not exist in the "
                "governed corpus, so there is no output to validate")
    if state == "NOT_COMPUTED_SUPPLIED_FIELD":
        return ("STRUCTURE_OR_DATA_ABSENT",
                "supplied field, not a computed method; the governed document risk evidence "
                "record required to validate a score is absent and no labelled document corpus "
                "exists")
    if state == "ABSTAINS":
        return ("STRUCTURE_OR_DATA_ABSENT",
                f"abstains on the governed corpus: required structure "
                f"{struct_key or 'declared by its canonical layer'} is not supplied")
    if state == "COMPUTES" and not has_numeric:
        return ("STRUCTURE_OR_DATA_ABSENT",
                "executes and emits a governed row, but the corpus establishes no measurable "
                "quantity, so no output exists to score")
    if applied_unsupported:
        return ("CALIBRATION_GAP_BLOCKS_VALIDATION",
                "computes and APPLIES an unresolved parameter to its emitted output, so any "
                "measured performance would be attributable to the uncalibrated value")
    # class A requires a reference not derivable from the method's own inputs. No such reference
    # exists anywhere in this repository; see the independence register.
    if mid in PROPOSED_REFERENCES:
        return ("PARTIAL_REFERENCE_STANDARD",
                "a published definitional/regulatory identity fixes the numeric quantity; "
                "nothing independent fixes the band, status or decision attached to it")
    return ("NO_INDEPENDENT_REFERENCE_STANDARD",
            "computes with no applied unresolved parameter, but no defensible independent "
            "outcome exists against which to score it")


def main():
    idx, project, portfolio, sci_project = populations()
    cov = suite_coverage()
    skeys = structure_key_map()

    # -------- report the derived counts before anything else
    print(f"registry rows (live CSV, RETIRED removed): {len(idx)}")
    print(f"  registered project modules (groups A/B/C): {len(project)}")
    print(f"  portfolio health targets (group D):        {len(portfolio)}")
    print(f"  project SCIENTIFIC targets (project - A3.4 disabled-evidence-under-review): "
          f"{len(sci_project)}")
    print(f"  registry VALIDATED (computed project modules, excludes supplied A4.1): "
          f"{len(REG.VALIDATED)}")
    print(f"  TOTAL SCIENTIFIC TARGETS: {len(sci_project) + len(portfolio)}")

    scientific = dict(sci_project)
    scientific.update(portfolio)
    # A3.4 IS REGISTERED AND IS NOT A SCIENTIFIC TARGET. It gets a scope row anyway -- section 8
    # of the Run-35 contract keeps an eligibility row for a disabled target -- and the row says
    # scientific_target = NO, so the two populations cannot be collapsed by reading this file.
    non_scientific = {m: idx[m] for m in REG.DISABLED_EVIDENCE_UNDER_REVIEW}

    scope_rows, cal_rows, contract_rows = [], [], []
    eligibility = {}
    for mid in sorted(scientific, key=lambda m: (m[0], int(m[1]), float(m.split('.')[1]))):
        r = idx[mid]
        row = execute(mid) if r["group"] != "D" else {
            "__state__": "ABSTAINS",
            "__note__": "portfolio route; the controlled portfolio supplies no governed cohort"}
        state = row["__state__"]
        struct_key = skeys.get(mid, ("", ""))[0]
        layer = skeys.get(mid, ("", ""))[1]
        provs = PROV.get(mid, ())
        unresolved = [p for p in provs if p.parameter_class in ("UNSUPPORTED", "HEURISTIC")]
        # APPLIED is measured, not assumed: an unresolved band ladder is applied only when the
        # executed row actually carries the value it produces.
        applied = bool(unresolved) and row.get("status_color") not in (None, "")
        has_num = numeric_reading(row) if state == "COMPUTES" else False
        cls, why = classify(mid, row, applied, has_num, struct_key)
        eligibility[mid] = cls
        voting = "YES" if mid in REG.CORE_VOTING_MODULES else "NO"
        op_state = ("PORTFOLIO_ADVISORY" if r["group"] == "D"
                    else REG.activation_state(mid))
        scope_rows.append([
            mid, r["module_name"], r["category_name"], "YES",
            "YES", "SUPPLIED" if mid in REG.unported_modules() else "COMPUTED",
            op_state,
            "YES" if (struct_key or r["group"] == "D") else "NO_DECLARED_STRUCTURE_KEY",
            "NO" if state in ("ABSTAINS", "NOT_COMPUTED_SUPPLIED_FIELD") else "YES",
            "NO_CALIBRATION_SET" if unresolved else (
                "PUBLISHED_METHOD_PARAMETER" if provs else "NO_TUNABLE_VALUE"),
            ";".join(sorted({p.parameter_class for p in provs})) or "NO_PARAMETER_ROW",
            state, voting,
            "NO_PRODUCTION_ROUTE" if mid in REG.DISABLED_MODULES else "N/A",
            cls,
        ])
        # ---- unresolved calibration inventory: one row per unresolved parameter.
        # PORTFOLIO HEALTH USES THE FINER LIVE REGISTRY. `parameters.py` carries ONE coarse row
        # per D1.x module; `canonical_v8.PH_PARAMETERS` is the live per-parameter register Run 34
        # established, with its own measured `applied` flag. Using the coarse row as well would
        # double-count the same values under two names, so the coarse row is replaced, not added.
        if r["group"] == "D":
            for pp in PH_PARAMS(mid):
                if pp["parameter_class"] not in ("UNSUPPORTED", "HEURISTIC"):
                    continue
                ap = bool(pp.get("applied_operationally"))
                cal_rows.append([
                    mid, pp["parameter"], pp["parameter_class"], "YES" if ap else "NO",
                    "YES" if ap else "NO",
                    "NO - a measured error would be attributable to the uncalibrated value"
                    if ap else
                    "NOT_REACHED - canonical_v8 refuses to apply an UNSUPPORTED parameter",
                    (pp.get("note") or "")[:200] or "no operational consequence: not applied",
                    "NO OPPORTUNISTIC TUNING IN RUN 35; classification carried to Run 36"])
            unresolved = []
        for p in unresolved:
            cal_rows.append([
                mid, p.kind, p.parameter_class, "YES" if applied else "NO",
                "YES" if applied else "NO",
                "NO - a measured error would be attributable to the uncalibrated value"
                if applied else
                "NOT_REACHED - the value is carried but the governed corpus never reaches it",
                "band/status colour emitted on the governed corpus" if applied else
                "none on the governed corpus; the module abstains or emits no status",
                "NO OPPORTUNISTIC TUNING IN RUN 35; classification carried to Run 36"
            ])
        # ---- metric contract, by output type. Predeclared, before any scoring.
        if state == "COMPUTES" and has_num:
            otype = ("Forecast (stochastic distribution summary)" if mid == "A1.1"
                     else "Deterministic scalar + categorical status")
        elif mid in REG.DISABLED_MODULES:
            otype = "NOT_EXECUTED_DISABLED"
        elif state == "NOT_COMPUTED_SUPPLIED_FIELD":
            otype = "SUPPLIED_SCALAR_NOT_COMPUTED"
        else:
            otype = "NOT_EMITTED_ON_GOVERNED_CORPUS"
        if cls == "PARTIAL_REFERENCE_STANDARD":
            metric = ("exact equality in exact rational arithmetic (fractions.Fraction) between "
                      "the production scalar and an independent implementation of the published "
                      "identity; tolerance 0, justified because both sides are exact rationals")
            scored = "scalar component ONLY"
            unscored = ("the band boundary / status colour and any field-outcome relationship: "
                        "no independent label population exists, so no confusion matrix, "
                        "sensitivity or specificity is admissible")
            rule = ("PREDECLARED ACCEPTANCE RULE: PASS if and only if the production scalar "
                    "equals the independent published-identity value exactly as a rational; "
                    "any inequality is FAIL. Declared before execution of the scoring generator.")
        else:
            metric = "NONE - no qualified independent reference standard exists"
            scored = "nothing"
            unscored = "the whole output"
            rule = ("NONE. No predeclared acceptance rule; no threshold may be created after a "
                    "result is observed.")
        contract_rows.append([mid, r["module_name"], cls, otype, metric, scored, unscored, rule,
                              "YES" if mid in cov else "NO", layer or "n/a", SIMULATION_VERSION])

    for mid, r in sorted(non_scientific.items()):
        row = execute(mid)
        struct_key = skeys.get(mid, ("", ""))[0]
        provs = PROV.get(mid, ())
        scope_rows.append([
            mid, r["module_name"], r["category_name"], "YES", "NO", "COMPUTED",
            REG.activation_state(mid),
            "YES" if struct_key else "NO_DECLARED_STRUCTURE_KEY", "NO",
            "NO_CALIBRATION_SET", ";".join(sorted({p.parameter_class for p in provs})),
            row["__state__"], "NO", "NO_PRODUCTION_ROUTE",
            "STRUCTURE_OR_DATA_ABSENT (recorded for completeness; NOT one of the 100 "
            "scientific targets)"])

    write("run35_scientific_target_scope.csv",
          ["module_id", "module_name", "category", "registered", "scientific_target",
           "supplied_or_computed", "current_operational_state", "canonical_method_established",
           "governed_structure_available_on_corpus", "calibration_state",
           "parameter_provenance_state", "real_corpus_execution_state", "voting",
           "legacy_route_reachable", "run35_validation_eligibility"], scope_rows)

    write("run35_unresolved_calibration_inventory.csv",
          ["module", "parameter", "current_classification", "currently_applied",
           "output_affected", "empirical_validation_interpretable", "operational_consequence",
           "disposition"], cal_rows)

    # ---- reference-standard independence register
    ref_rows = []
    for mid, d in sorted(PROPOSED_REFERENCES.items()):
        tests = [
            ("is a direct method input", "NO - the identity is a specification, not a datum"),
            ("is calculated by the same method",
             "NO - computed by an independent implementation written for this register"),
            ("is a transformation of the method output",
             "NO - it is computed from the inputs, never from the output"),
            ("was selected after seeing method performance",
             "NO - declared and committed before the scoring generator was written or run"),
            ("comes from the synthetic detector used to create the prediction",
             "NO - no synthetic detector is involved"),
            ("leaks future-period information into an earlier-period prediction",
             "NO - the identity is period-invariant and no later period is read"),
        ]
        # THE DECIDING TEST. The reference's arguments are the method's own inputs, so under the
        # protocol's algebraic-relatedness rule this cannot be a class-A field reference.
        judgment = ("INDEPENDENTLY AUTHORED, NOT AN INDEPENDENT FIELD OUTCOME. The identity is "
                    "external, published and pre-existing, so it qualifies as a reference "
                    "standard for the ARITHMETIC. Its arguments are the method's own inputs, so "
                    "under the algebraic-relatedness rule it is NOT an independent observed "
                    "outcome and cannot support a class-A empirical claim. Admitted for "
                    "PARTIAL_REFERENCE_STANDARD scoring of the scalar component only.")
        ref_rows.append([
            d["ref_id"], mid, d["source"], d["period"], d["variable"], d["method_inputs"],
            d["available_to_method"], d["derived_from_method"], d["lineage"],
            " | ".join(f"{t}: {a}" for t, a in tests), judgment,
            "QUALIFIED_FOR_PARTIAL_SCORING", "NO",
        ])
    write("run35_reference_standard_independence.csv",
          ["reference_standard_id", "module", "source_document_or_data", "timestamp_or_period",
           "reference_variable", "method_inputs", "reference_available_to_method",
           "reference_derived_from_method", "lineage", "independence_tests",
           "independence_judgment", "admission", "supports_class_A_empirical_claim"], ref_rows)

    write("run35_validation_metric_contract.csv",
          ["module_id", "module_name", "validation_eligibility_class", "output_type",
           "predeclared_metric", "component_scored", "component_NOT_scored",
           "predeclared_acceptance_rule", "laboratory_suite_evidence_exists",
           "canonical_layer", "simulation_version"], contract_rows)

    from collections import Counter
    dist = Counter(eligibility.values())
    print("\neligibility distribution (primary class, protocol precedence):")
    for c in CLASSES:
        print(f"  {c}: {dist.get(c, 0)}")
    sci_rows = [r for r in scope_rows if r[4] == "YES"]
    assert len(sci_rows) == 100, f"scientific rows = {len(sci_rows)}, expected 100"
    assert len(set(r[0] for r in sci_rows)) == 100, "duplicate scientific ids"
    assert len(set(r[0] for r in scope_rows)) == len(scope_rows), "duplicate scope ids"
    assert sum(1 for r in scope_rows if r[12] == "YES") == 2, "voting must be exactly 2"
    print(f"scope rows total {len(scope_rows)}; scientific {len(sci_rows)}; "
          f"registered-not-scientific {len(scope_rows) - len(sci_rows)}")
    (OUT_DIR / "run35_eligibility.json").write_text(
        json.dumps(eligibility, indent=0, sort_keys=True), encoding="utf-8")
    print("OK")


if __name__ == "__main__":
    main()
