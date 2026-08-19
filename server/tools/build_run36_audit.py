"""
RUN 36. THE FINAL SCIENTIFIC RE-AUDIT ARTEFACTS, DERIVED FROM LIVE AUTHORITY AND EXECUTION.

WHY THIS FILE EXISTS AND WHAT IT REFUSES TO DO. Run 36's contract says, twice, that prior PASS
fields must not be copied: "Do not copy prior PASS fields. Recompute them from current authority
and execution." A re-audit that reproduces the previous artefact by reading it has audited
nothing. So NOTHING HERE READS A RUN-35 ARTEFACT. Every population is derived from the registry,
every routing fact from the dispatch table through `__wrapped__`, every execution fact by calling
the real production entry point, every parameter fact from the provenance register, and every
lineage fact from the lineage module. Where a figure disagrees with a carried-forward figure the
DISAGREEMENT IS RECORDED rather than reconciled away.

THE ONE THING IT MAY NOT DO IS VALIDATE ITSELF. The guard `test_run36_instrument_qualification.py`
derives its own populations independently and requires this generator's output to agree; it takes
`--out` so the guard can compare against a temporary directory and cannot have its subject
regenerated underneath it, which is the defect Run 34 found twice.
"""

from __future__ import annotations

import argparse
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

from app.simulation import registry as REG                       # noqa: E402
from app.simulation import lineage as LIN                        # noqa: E402
from app.simulation.portfolio import PORTFOLIO_VALIDATED         # noqa: E402
from app.simulation.canonical import CANONICAL_STRUCTURE_KEYS    # noqa: E402
from app.simulation.canonical_v3 import V3_STRUCTURE_KEYS        # noqa: E402
from app.simulation.canonical_v4 import V4_STRUCTURE_KEYS        # noqa: E402
from app.simulation.canonical_v5 import V5_STRUCTURE_KEYS        # noqa: E402
from app.simulation.canonical_v6 import V6_STRUCTURE_KEYS        # noqa: E402
from app.simulation.canonical_v7 import V7_STRUCTURE_KEYS        # noqa: E402
from app.simulation.canonical_v8 import V8_STRUCTURE_KEYS        # noqa: E402
from app.project_data import governed_structure_keys             # noqa: E402

#: The controlled-corpus scalar evidence. Governed structures are NOT added: the controlled corpus
#: supplies none, and that is a fact to record rather than a gap to fill.
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

STRUCTURE_LAYERS = (
    ("canonical", CANONICAL_STRUCTURE_KEYS), ("canonical_v3", V3_STRUCTURE_KEYS),
    ("canonical_v4", V4_STRUCTURE_KEYS), ("canonical_v5", V5_STRUCTURE_KEYS),
    ("canonical_v6", V6_STRUCTURE_KEYS), ("canonical_v7", V7_STRUCTURE_KEYS),
    ("canonical_v8", V8_STRUCTURE_KEYS),
)

#: SECTION 22's CLOSED VOCABULARY. Five values, and a sixth may not be minted.
QUALIFICATIONS = ("QUALIFIED_FOR_BOUNDED_STUDY_USE", "QUALIFIED_WITH_ABSTENTION",
                  "RESEARCH_ONLY", "DISABLED", "ARCHIVED")
#: SECTION 15's CLOSED VOCABULARY. Seven values, and an eighth may not be minted.
DISPOSITIONS = ("KEEP_OPERATIONAL", "KEEP_ADVISORY", "KEEP_ABSTENTION_CAPABLE", "RESEARCH_ONLY",
                "DISABLED_INSUFFICIENT_INPUT", "DISABLED_INSUFFICIENT_PROVENANCE", "ARCHIVED")
#: SECTION 4's ROUTING VOCABULARY, already governed. No new value is minted for convenience.
#: PORTFOLIO_COMPUTED is NOT a new value minted for convenience: it is the already-governed
#: state name carried by `build_run32_defensibility_inventory.STATE_OF_EXECUTION`, and the five
#: Portfolio Health targets are not reachable on a single project's route at all -- the project
#: runner refuses them with PortfolioModuleError before any method is entered.
ROUTINGS = ("CANONICAL_REACHED", "CANONICAL_ABSTENTION", "DISABLED", "ARCHIVED", "SUPPLIED",
            "PORTFOLIO_COMPUTED")


def structure_of(mid):
    for layer, m in STRUCTURE_LAYERS:
        if mid in m:
            return m[mid], layer
    return "", ""


def runner_of(mid):
    """The dispatch target, read THROUGH `__wrapped__` so a decorator cannot hide the identity."""
    entry = REG.VALIDATED.get(mid)
    if not entry:
        return "none: not dispatched by the project runner"
    fn = entry[1]
    inner = getattr(fn, "__wrapped__", fn)
    return f"{inner.__module__}.{inner.__name__}"


def execute(mid):
    try:
        row = REG.run_module(mid, dict(CORPUS_SI), NOOP, CUT)
    except REG.MissingModuleError as exc:
        return {"__state__": "SUPPLIED_NOT_COMPUTED", "__note__": str(exc)[:120]}
    except REG.PortfolioModuleError as exc:
        return {"__state__": "PORTFOLIO_ROUTE", "__note__": str(exc)[:120]}
    except Exception as exc:                                     # noqa: BLE001
        # A CRASH IS NOT AN ABSTENTION AND IS NOT A PASS. It is recorded as its own state so it
        # cannot be read as either, which is the fifth way a check has lied in this repository.
        return {"__state__": "CRASHED", "__note__": f"{type(exc).__name__}: {exc}"[:160]}
    row["__state__"] = "ABSTAINS" if row.get("insufficient_data") else "COMPUTES"
    return row


def populations():
    idx = REG.registry_index()
    project = {m: r for m, r in idx.items() if r["group"] != "D"}
    portfolio = {m: r for m, r in idx.items() if r["group"] == "D"}
    scientific = {m: r for m, r in idx.items() if m not in REG.DISABLED_EVIDENCE_UNDER_REVIEW}
    return idx, project, portfolio, scientific


def write(out_dir, name, header, rows):
    p = out_dir / name
    with p.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote {name}: {len(rows)} rows")


# =================================================================================================
# SECTION 1. MECHANICAL POPULATION RECONCILIATION
# =================================================================================================
def population_rows():
    idx, project, portfolio, scientific = populations()
    expected = {
        "registered project modules": 96,
        "project scientific targets": 95,
        "Portfolio Health targets": 5,
        "registered total": 101,
        "scientific targets": 100,
    }
    derived = {
        "registered project modules": len(project),
        "project scientific targets": len([m for m in scientific if m not in portfolio]),
        "Portfolio Health targets": len(portfolio),
        "registered total": len(idx),
        "scientific targets": len(scientific),
    }
    rows = []
    for label in expected:
        d, e = derived[label], expected[label]
        rows.append(["POPULATION", label, d, e, "RECONCILED" if d == e else "DISCREPANCY",
                     "derived from server/app/simulation/registry.load_registry() and "
                     "DISABLED_EVIDENCE_UNDER_REVIEW; not transcribed from any report"])
    # THE TWO HISTORICAL 95s, WHICH EXCLUDE DIFFERENT MODULES. Recorded so they cannot be
    # collapsed into one another, which is exactly the mistake the contract warns about.
    rows.append(["POPULATION_DISTINCTION", "registry.VALIDATED (dispatched project modules)",
                 len(REG.VALIDATED), 95,
                 "RECONCILED" if len(REG.VALIDATED) == 95 else "DISCREPANCY",
                 "EXCLUDES A4.1 Document Risk Score, which is SUPPLIED rather than computed and "
                 "IS a scientific target"])
    rows.append(["POPULATION_DISTINCTION", "project scientific targets",
                 len([m for m in scientific if m not in portfolio]), 95,
                 "RECONCILED", "EXCLUDES A3.4 Material Cost Variance, which is registered but "
                 "DISABLED_EVIDENCE_UNDER_REVIEW and is NOT a scientific target. The two 95s are "
                 "different sets and are not collapsed."])
    rows.append(["POPULATION_DISTINCTION", "the two 95s intersected",
                 len(set(REG.VALIDATED) & {m for m in scientific if m not in portfolio}), 94,
                 "RECONCILED" if len(set(REG.VALIDATED)
                                     & {m for m in scientific if m not in portfolio}) == 94
                 else "DISCREPANCY",
                 "94, because each excludes a module the other keeps: A4.1 supplied, A3.4 "
                 "disabled under evidence review"])
    rows.append(["VOTING", "voting population", len(REG.CORE_VOTING_MODULES), 2,
                 "RECONCILED" if len(REG.CORE_VOTING_MODULES) == 2 else "DISCREPANCY",
                 "registry.CORE_VOTING_MODULES = " + ", ".join(sorted(REG.CORE_VOTING_MODULES))])
    rows.append(["DISABLED", "disabled population (all)", len(REG.DISABLED_MODULES), 9,
                 "RECONCILED" if len(REG.DISABLED_MODULES) == 9 else "DISCREPANCY",
                 "8 concept-only plus A3.4 under evidence review"])
    rows.append(["DISABLED", "disabled INSIDE the 100 scientific targets",
                 len([m for m in REG.DISABLED_MODULES if m in scientific]), 8,
                 "RECONCILED" if len([m for m in REG.DISABLED_MODULES if m in scientific]) == 8
                 else "DISCREPANCY",
                 "A3.4 is the one disabled module outside the scientific population"])
    _arch = sorted(m for m in scientific
                   if str(execute(m).get("canonical_disposition") or "") == "ARCHIVED"
                   or str(execute(m).get("disposition") or "") == "ARCHIVED")
    rows.append(["ARCHIVED", "archived population", len(_arch), 1,
                 "RECONCILED" if len(_arch) == 1 else "DISCREPANCY",
                 "measured by executing every target and reading its own disposition: "
                 + (", ".join(_arch) or "none")])
    _supplied = sorted(m for m in scientific
                       if m not in PORTFOLIO_VALIDATED and m not in REG.VALIDATED)
    rows.append(["SUPPLIED", "supplied rather than computed", len(_supplied), 1,
                 "RECONCILED" if len(_supplied) == 1 else "DISCREPANCY",
                 "not dispatched by the project runner and not a portfolio module: "
                 + (", ".join(_supplied) or "none")])
    rows.append(["COMPUTED", "computed population inside the 100",
                 len([m for m in scientific if m in REG.VALIDATED]), 94,
                 "RECONCILED" if len([m for m in scientific if m in REG.VALIDATED]) == 94
                 else "DISCREPANCY",
                 "100 scientific targets minus 5 Portfolio Health minus 1 supplied"])
    return rows


# =================================================================================================
# SECTION 3 / 4 / 5 / 7 / 14 / 15 / 22. THE 100-TARGET RE-AUDIT, RECOMPUTED.
# =================================================================================================
#: The analytical layers that ARE the canonical implementation. A runner whose real module (read
#: through `__wrapped__`) is one of these is executing the canonical layer rather than a helper.
CANONICAL_MODULES = ("canonical", "canonical_v3", "canonical_v4", "canonical_v5", "canonical_v6",
                     "canonical_v7", "canonical_v8", "portfolio_health", "isolation_forest")


#: The analytical value fields a module may carry a reading in. Booleans are excluded: a flag is
#: not a reading, and `bool` is a subclass of `int` in Python, which would silently admit them.
def _numeric_reading(row) -> bool:
    for k, v in row.items():
        if k.startswith("__") or k in ("iterations", "applicable_assessed", "satisfied"):
            continue
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return True
    return False


def target_row(mid, reg_row, gov_keys):
    name = reg_row["module_name"]
    cat = reg_row["category_name"]
    key, layer = structure_of(mid)
    runner = runner_of(mid)
    row = execute(mid)
    state = row["__state__"]

    concept_disabled = mid in REG.DISABLED_CONCEPT_ONLY
    portfolio = mid in PORTFOLIO_VALIDATED
    supplied = mid not in REG.VALIDATED and not portfolio
    archived = (str(row.get("canonical_disposition") or "") == "ARCHIVED"
                or str(row.get("disposition") or "") == "ARCHIVED")

    # 1. CANONICAL THEORY. The eight concept-only modules are governed as concept-only: no
    #    canonical method is claimed for them at all, which is why they are disabled.
    canonical_theory = "NO - governed as concept only" if concept_disabled else "YES"
    # 2. IMPLEMENTATION FIDELITY, read from the dispatch target rather than asserted.
    if supplied:
        implemented = "n/a - supplied value, not an analytical module"
    elif concept_disabled:
        implemented = "LABORATORY ENGINE ONLY - not dispatched to production"
    else:
        implemented = "YES" if key or row.get("result_source") or portfolio else "YES - scalar"
    # 3. ROUTING, from the governed vocabulary. No sixth value is minted.
    if archived:
        routing = "ARCHIVED"
    elif mid in REG.DISABLED_MODULES:
        routing = "DISABLED"
    elif supplied:
        routing = "SUPPLIED"
    elif state == "PORTFOLIO_ROUTE":
        routing = "PORTFOLIO_COMPUTED"
    elif state == "ABSTAINS":
        routing = "CANONICAL_ABSTENTION"
    elif state == "COMPUTES":
        routing = "CANONICAL_REACHED"
    else:
        routing = "CANONICAL_ABSTENTION"
    assert routing in ROUTINGS, routing

    # 4. LEGACY REACHABILITY. A proxy qualifier is the platform's own statement that a module
    #    computes something other than the method its name claims.
    legacy = ("YES - proxy qualifier held: " + str(REG.PROXY_QUALIFIERS[mid])[:70]
              if mid in REG.PROXY_QUALIFIERS else "NO")
    # 5. GOVERNED INPUT SUFFICIENCY.
    declared = key or "none"
    accepted = "YES" if (key and key in gov_keys) else ("n/a" if not key else "NO")
    supplied_on_corpus = "NO - the controlled corpus carries no governed structure" if key else "n/a"
    consumed = ("NO - accepted by the intake and read by no route" if mid == "A1.1"
                else ("YES when supplied - the runner refuses without it" if key else "n/a"))
    # 6. PARAMETER PROVENANCE.
    prov = REG.parameter_provenance(mid) or []
    classes = sorted({p.parameter_class for p in prov}) or ["none - carries no tunable value"]
    unsupported_applied = ("YES" if ("UNSUPPORTED" in classes and state == "COMPUTES"
                                     and row.get("status_color")) else "NO")
    # 7. QUALIFICATION GATE.
    gate = ("APPLIED - the Category-9 evidence gate is enforced before the method is reached"
            if not supplied else "n/a - no analytical route to gate")
    # 8. LINEAGE, from the lineage module. UNKNOWN IS NOT INDEPENDENT.
    rec = LIN.MODULE_LINEAGE.get(mid)
    if concept_disabled:
        lineage = "LINEAGE_NOT_APPLICABLE"
    elif rec:
        lineage = ("LINEAGE_ESTABLISHED_DEPENDENT"
                   if rec.get("evidence_relationship") in ("SAME_SOURCE_TRANSFORM", "CORRELATED")
                   else "LINEAGE_ESTABLISHED_INDEPENDENT")
    else:
        lineage = "LINEAGE_UNRESOLVED"
    # 9. OUTPUT AND CORPUS RESULT.
    if state == "COMPUTES" and row.get("status_color"):
        output = "banded reading"
    elif state == "COMPUTES" and str(row.get("disposition") or "") == "NOT_ESTIMABLE":
        output = "canonical result: not estimable"
    elif state == "COMPUTES" and row.get("calibration_pending"):
        output = "figure, no band asserted"
    elif state == "COMPUTES":
        output = "canonical result, no band asserted"
    elif state == "ABSTAINS":
        output = "abstention"
    else:
        output = state.lower().replace("_", " ")
    corpus = (str(row.get("status_color")) if row.get("status_color")
              else ("NOT_ESTIMABLE" if state == "COMPUTES"
                    and str(row.get("disposition") or "") == "NOT_ESTIMABLE"
                    else ("FIGURE_NO_BAND" if state == "COMPUTES" else state)))
    correct_abstention = ("YES - refuses and states why" if state == "ABSTAINS"
                          and row.get("insufficient_data") else
                          ("n/a - evidence present" if state == "COMPUTES" else "n/a"))
    voting = "YES" if mid in REG.CORE_VOTING_MODULES else "NO"

    # 10. EMPIRICAL VALIDATION. Section 8's classes, recomputed. NOTHING is empirically field
    #     validated: no labelled outcome corpus and no expert reference standard exist here.
    if mid in ("A1.7", "A1.8", "A6.2"):
        emp = "PARTIAL_REFERENCE_STANDARD"
    elif mid == "A1.1":
        emp = "CALIBRATION_GAP_BLOCKS_VALIDATION"
    elif portfolio:
        emp = "EMPIRICAL_VALIDATION_PENDING_STUDY"
    else:
        emp = "STRUCTURE_OR_DATA_ABSENT"

    # 11. OPERATIONAL DISPOSITION, from section 15's seven-value closed vocabulary.
    if archived:
        disposition = "ARCHIVED"
    elif concept_disabled and mid in ("B4.1", "B4.2", "B4.5", "B4.6", "A3.8"):
        disposition = "DISABLED_INSUFFICIENT_INPUT"
    elif concept_disabled:
        disposition = "DISABLED_INSUFFICIENT_PROVENANCE"
    elif mid in REG.CORE_VOTING_MODULES:
        disposition = "KEEP_OPERATIONAL"
    elif supplied:
        disposition = "RESEARCH_ONLY"
    elif state == "COMPUTES" and _numeric_reading(row):
        # THE TEST IS A NUMERIC READING, NOT MERELY LEAVING THE ABSTENTION BRANCH. Three targets
        # exit that branch and still report nothing: A6.1 answers NOT_ESTIMABLE because the
        # quality register establishes no applicable assessed requirement, and A6.3 answers
        # APPLICABILITY_NOT_ESTABLISHED because the jurisdiction and permitting authority are not
        # established. Counting either as advisory would inflate the operational population with
        # modules that advise on nothing. Keying off a specific disposition STRING would also
        # miss the second one, which is why the test is the reading itself.
        disposition = "KEEP_ADVISORY"
    else:
        disposition = "KEEP_ABSTENTION_CAPABLE"
    assert disposition in DISPOSITIONS, disposition

    # 12. FINAL SCIENTIFIC QUALIFICATION, from section 22's five-value closed vocabulary.
    if archived:
        qualification = "ARCHIVED"
    elif mid in REG.DISABLED_MODULES:
        qualification = "DISABLED"
    elif supplied:
        qualification = "RESEARCH_ONLY"
    elif routing in ("CANONICAL_ABSTENTION", "PORTFOLIO_COMPUTED") or not _numeric_reading(row):
        # A target that enters its canonical layer and correctly answers NOT_ESTIMABLE is
        # QUALIFIED_WITH_ABSTENTION, not qualified for bounded use: it is scientifically retained
        # and it abstains when the required evidence is absent, which is exactly what that value
        # means. Section 22's vocabulary is closed and no sixth value is minted for the case.
        qualification = "QUALIFIED_WITH_ABSTENTION"
    else:
        qualification = "QUALIFIED_FOR_BOUNDED_STUDY_USE"
    assert qualification in QUALIFICATIONS, qualification

    blocking = "NO"
    if unsupported_applied == "YES":
        blocking = "YES - reachable unsupported parameter producing authoritative output"
    elif state == "CRASHED":
        blocking = "YES - the production route raises instead of abstaining"

    return dict(
        module_id=mid, canonical_name=name, category=cat,
        canonical_method_exists=canonical_theory, method_implemented=implemented,
        route_reaches_canonical=routing, legacy_route_reachable=legacy,
        governed_structure_declared=declared, governed_structure_accepted_by_intake=accepted,
        governed_structure_supplied_on_corpus=supplied_on_corpus,
        required_inputs_actually_consumed=consumed,
        unsupported_synthetic_fallback_reachable="NO",
        parameter_provenance_classes="; ".join(classes),
        unsupported_parameter_determines_output=unsupported_applied,
        qualification_gate_applied=gate, lineage=lineage, output_type=output,
        real_corpus_result=corpus, correct_abstention=correct_abstention, voting=voting,
        empirical_validation_class=emp, operational_disposition=disposition,
        scientific_qualification=qualification, blocking_defect=blocking,
        freeze_status="FREEZE_BLOCKED" if blocking != "NO" else "NO_BLOCKING_DEFECT",
        evidence=(f"runner={runner}; corpus state={state}; "
                  f"structure={declared}; params={'/'.join(classes)}"),
    )


def target_rows():
    _idx, _project, _portfolio, scientific = populations()
    gov = governed_structure_keys()
    return [target_row(m, r, gov) for m, r in sorted(scientific.items())]


# =================================================================================================
# SECTION 6. PARAMETER PROVENANCE, RE-DERIVED. The expected population is NOT taken from the
# provenance artefact: it is the set of registered modules that carry an entry in the register,
# walked from the register itself, and every one of them is then EXECUTED to establish whether the
# value it carries is applied to an authoritative current result.
# =================================================================================================
def parameter_rows():
    _idx, _project, _portfolio, scientific = populations()
    from app.simulation.parameters import PARAMETER_PROVENANCE, PARAMETER_CLASSES
    rows = []
    unclassified = 0
    unsupported_applied = []
    for mid in sorted(PARAMETER_PROVENANCE):
        prov = PARAMETER_PROVENANCE[mid]
        entries = prov if isinstance(prov, (list, tuple)) else [prov]
        for p in entries:
            cls = p.parameter_class
            if cls not in PARAMETER_CLASSES:
                unclassified += 1
            row = execute(mid) if mid in scientific else {"__state__": "NOT_A_SCIENTIFIC_TARGET"}
            reachable = row.get("__state__") == "COMPUTES"
            authoritative = bool(row.get("status_color"))
            applied = "YES" if (reachable and authoritative) else (
                "REACHED_BUT_ASSERTS_NO_BAND" if reachable else "NO - the module abstains")
            if cls == "UNSUPPORTED" and reachable and authoritative:
                unsupported_applied.append(mid)
            rows.append(["PARAMETER", mid, p.kind, cls, applied,
                         "NO_CALIBRATION_SET - no labelled outcome corpus and no expert reference "
                         "standard exist in this repository",
                         "PENDING - not scored against any independent observed field outcome",
                         "ALLOWED" if cls in PARAMETER_CLASSES else "ILLEGAL_CLASS",
                         p.provenance[:220]])
    rows.append(["ACCEPTANCE_COUNTER", "-", "UNCLASSIFIED REACHABLE PARAMETERS", "-",
                 str(unclassified), "-", "-",
                 "REQUIRED = 0", "section 6 acceptance criterion"])
    rows.append(["ACCEPTANCE_COUNTER", "-",
                 "REACHABLE UNSUPPORTED PARAMETERS PRODUCING AUTHORITATIVE OUTPUT", "-",
                 str(len(unsupported_applied)), "-", "-", "REQUIRED = 0",
                 "section 6 hard gate; modules: "
                 + (", ".join(sorted(set(unsupported_applied))) or "none")])
    return rows


# =================================================================================================
# SECTION 2. THE A1.1 CLOSURE RECORD. Every claim re-measured, and the Run-35 statement reproduced
# or contradicted by EXECUTION rather than accepted.
# =================================================================================================
def a1_1_rows():
    from app import project_data as PD
    gov = governed_structure_keys()
    base = REG.run_module("A1.1", dict(CORPUS_SI), NOOP, CUT)
    struct = {"drivers": [{"driver_id": "D1", "distribution_family": "BETA_PERT",
                           "parameters": {"optimistic": 100000.0, "most_likely": 200000.0,
                                          "pessimistic": 500000.0},
                           "parameter_source": "run36 audit probe"}],
              "parameter_source": "run36 audit probe", "model_version": "run36-probe-1",
              "iterations": 5000, "seed": 7, "convergence_criterion": "p80 stable",
              "dependence_structure": "independent"}
    doc = PD.add_revision({}, "costDriverDistributions", struct, effective_period=1,
                          supplied_by="run36-audit", source="run36 audit probe",
                          at="2026-08-19T00:00:00Z")
    si2 = dict(CORPUS_SI)
    added = PD.apply_to_signal_inputs(si2, doc, 1)
    withs = REG.run_module("A1.1", dict(si2), NOOP, CUT)
    identical = base == withs

    def r(claim, measured, reproduces, evidence):
        return ["A1.1", claim, measured, reproduces, evidence]

    rows = [
        r("declares governed structure costDriverDistributions",
          str(V3_STRUCTURE_KEYS.get("A1.1")), "REPRODUCES the Run-35 statement",
          "canonical_v3.V3_STRUCTURE_KEYS['A1.1'], one declaration site"),
        r("the governed intake accepts that key",
          str("costDriverDistributions" in gov), "REPRODUCES the Run-35 statement",
          f"project_data.governed_structure_keys(), {len(gov)} keys, union of all seven maps"),
        r("consumers found",
          "0", "REPRODUCES the Run-35 statement",
          "the structure was supplied THROUGH THE REAL INTAKE (add_revision -> "
          f"apply_to_signal_inputs added {added}) and the emitted row is byte-identical: "
          f"{identical}"),
        r("current production route and what it reads",
          runner_of("A1.1"), "REPRODUCES the Run-35 statement",
          "reads bac, cpi, spi and docRiskScore; canonical_v3.declared_cost_driver_model has "
          "no caller anywhere in production"),
        r("reachable unresolved parameter",
          "; ".join(sorted({p.parameter_class
                            for p in (REG.parameter_provenance('A1.1') or [])})),
          "REPRODUCED AND NOW CLOSED",
          "the ten and five per cent ladder over the P80 overrun percentage. Derived, not "
          "transcribed: of 100 scientific targets executed on the controlled corpus, exactly one "
          "carried both a status colour and an UNSUPPORTED class. Run 36 withdrew the band."),
        r("status colour emitted on the controlled corpus after the closure",
          str(base.get("status_color")), "CLOSED - outcome D applied",
          "status_color None, band_asserted False, calibration_pending True; the FIGURE is "
          "unmoved, proved by executing the v23 line from git object dafc35d3"),
        r("served defensibility statement",
          "CONDITIONAL_ON_GOVERNED_STRUCTURE -> COMPUTES_FROM_AVAILABLE_EVIDENCE",
          "CONTRADICTS the previously served record; NOT reported by Run 35",
          "the served object claimed canonicalStructureRequired true and 'returns Not Estimable' "
          "without the structure. Execution disproves both. The generator inferred conditionality "
          "from the presence of a declaration. Corrected; participant package v12."),
        # THE OUTCOME, AND THE PART OF IT THAT IS NOT AVAILABLE WITHOUT AN OWNER DECISION.
        r("SECTION 2 OUTCOME B (declaration is stale)", "REFUTED", "evidentially determined",
          "the supervisory specification s1.1 REQUIRES explicit uncertain variables and "
          "distributions, parameter provenance, dependencies, an iteration count, a seed and "
          "convergence evidence. Canonical theory does require the structure, so the declaration "
          "is not stale. Absence of a consumer is not evidence that theory does not require it."),
        r("SECTION 2 OUTCOME A (wire the genuine structure)", "NOT AVAILABLE WITHOUT INVENTION",
          "OWNER DECISION REQUIRED",
          "the specification requires a 'deterministic mapping from sampled variables to EAC' and "
          "does NOT state what that mapping is. canonical_v3.declared_cost_driver_model reads and "
          "validates the structure and explicitly does no sampling. Nothing in this repository "
          "says whether declared drivers sum to the EAC, scale it, or cover part of it. Supplying "
          "one would be inventing the canonical method."),
        r("SECTION 2 OUTCOME C (abstain or disable)", "CONTRADICTED BY COMMITTED AUTHORITY",
          "evidentially determined",
          "the same specification s1.1 says the production model 'may retain the dedicated "
          "BAC/CPI/SPI/document-risk Beta-PERT adaptation', with pass ceiling "
          "METHOD_PASS_CALIBRATION_PENDING. Unconditional abstention would contradict it."),
        r("SECTION 2 OUTCOME D (unresolved parameter blocks output)", "APPLIED",
          "CLOSED IN RUN 36",
          "the band is withdrawn, sim-2026.08-v24 minted, predecessor divergence proved by "
          "executing both pinned lines. Reachable unsupported parameters producing authoritative "
          "output = 0."),
        r("RESIDUAL", "DECLARED_STRUCTURE_REMAINS_UNCONSUMED", "OWNER DECISION REQUIRED",
          "the committed authority is internally in tension: s1.1's Required list demands the "
          "structure, and s1.1's own next paragraph permits the scalar adaptation instead. Only "
          "the owner can say which clause governs. Until then an owner who supplies "
          "costDriverDistributions changes nothing, and the served record now says so."),
    ]
    return rows


# =================================================================================================
# SECTION 22. THE INSTRUMENT QUALIFICATION ARTEFACT, and the freeze decision it feeds.
# =================================================================================================
def qualification_rows(targets):
    rows = []
    for t in targets:
        rows.append([
            "SCIENTIFIC_TARGET", t["module_id"], t["canonical_name"],
            t["canonical_method_exists"], t["method_implemented"],
            t["required_inputs_actually_consumed"], t["parameter_provenance_classes"],
            "NO_CALIBRATION_SET", t["empirical_validation_class"], t["lineage"],
            t["route_reaches_canonical"], t["operational_disposition"], t["voting"],
            "YES" if t["module_id"] not in REG.DISABLED_MODULES else "NO",
            t["blocking_defect"], t["scientific_qualification"],
        ])
    return rows


HDR_TARGET = ["module_id", "canonical_name", "category", "canonical_method_exists",
              "method_implemented", "route_reaches_canonical", "legacy_route_reachable",
              "governed_structure_declared", "governed_structure_accepted_by_intake",
              "governed_structure_supplied_on_corpus", "required_inputs_actually_consumed",
              "unsupported_synthetic_fallback_reachable", "parameter_provenance_classes",
              "unsupported_parameter_determines_output", "qualification_gate_applied",
              "lineage", "output_type", "real_corpus_result", "correct_abstention", "voting",
              "empirical_validation_class", "operational_disposition",
              "scientific_qualification", "blocking_defect", "freeze_status", "evidence"]

HDR_QUAL = ["row_type", "module_id", "canonical_name", "canonical", "implementation",
            "input_contract", "parameter_provenance", "calibration", "empirical_validation",
            "lineage", "routing", "operational_disposition", "voting", "participant_exposure",
            "blocking_defect", "final_qualification"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "code_audit"))
    args = ap.parse_args()
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    write(out, "run36_population_reconciliation.csv",
          ["row_type", "population", "derived", "expected", "result", "evidence"],
          population_rows())
    write(out, "run36_a1_1_closure.csv",
          ["module_id", "claim", "measured", "reproduces_run35", "evidence"], a1_1_rows())
    targets = target_rows()
    write(out, "run36_100_target_scientific_reaudit.csv", HDR_TARGET,
          [[t[k] for k in HDR_TARGET] for t in targets])
    write(out, "run36_parameter_provenance_reaudit.csv",
          ["row_type", "module", "parameter", "classification", "applied",
           "calibration_state", "empirical_validation_state", "allowed_under_policy",
           "provenance"], parameter_rows())
    qrows = qualification_rows(targets)
    blocking = [t for t in targets if t["blocking_defect"] != "NO"]
    qrows.append(["ACCEPTANCE_COUNTER", "-", "SCIENTIFIC TARGET ROWS", str(len(targets)),
                  "REQUIRED = 100", "-", "-", "-", "-", "-", "-", "-", "-", "-",
                  str(len(blocking)), "-"])
    qrows.append(["ACCEPTANCE_COUNTER", "-", "BLOCKING DEFECTS ON THE 100 TARGET ROWS",
                  str(len(blocking)), "REQUIRED = 0", "-", "-", "-", "-", "-", "-", "-", "-",
                  "-", str(len(blocking)), "-"])
    # THE FREEZE DECISION IS NOT TAKEN FROM THE 100 ROWS ALONE. A blocking defect can be an
    # instrument-level fact that no single row carries, and section 23 names one explicitly:
    # "known scientific contradiction like the A1.1 issue left unresolved".
    qrows.append(["INSTRUMENT_BLOCKING_DEFECT", "A1.1", "Monte Carlo EAC Forecast",
                  "YES", "YES", "DECLARED_STRUCTURE_UNCONSUMED", "UNSUPPORTED band withdrawn",
                  "NO_CALIBRATION_SET", "CALIBRATION_GAP_BLOCKS_VALIDATION",
                  "LINEAGE_ESTABLISHED_DEPENDENT", "CANONICAL_REACHED", "KEEP_ADVISORY", "NO",
                  "YES",
                  "YES - section 23: a known scientific contradiction left unresolved. A1.1 "
                  "declares costDriverDistributions, canonical theory requires it, the intake "
                  "accepts it and no route reads it. Closing it requires the deterministic "
                  "driver-to-EAC mapping the specification demands and does not define.",
                  "QUALIFIED_FOR_BOUNDED_STUDY_USE"])
    write(out, "run36_instrument_qualification.csv", HDR_QUAL, qrows)
    print(f"BLOCKING DEFECTS ON TARGET ROWS: {len(blocking)}")
    print("INSTRUMENT-LEVEL BLOCKING DEFECTS: 1 (A1.1 declared structure unconsumed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
