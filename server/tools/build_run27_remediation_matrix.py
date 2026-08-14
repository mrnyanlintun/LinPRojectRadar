"""
RUN 27. Build the remediation matrix and the work packages from live sources.

NOTHING IN THE OUTPUT IS TYPED TWICE. The mechanical columns are read at build time from:

  p0-baseline/module_renumbering_map.csv          registered name, group, category
  code_audit/run20_cycle12_100_reaudit.csv        the population and every audit disposition
  server/app/simulation/method_labels.py          the shipped computation and the absent structure
  server/app/simulation/registry.py               proxy qualifiers, activation, voting, disabled sets
  server/app/simulation/parameters.py             parameter and calibration provenance
  code_audit/signal_flow_authoritative_edges.csv  the document fields that actually reach a module

and the authored evidence contract comes from server/tools/run27_curation.py. A rename in the
registry, a disposition change in the re-audit or a new edge therefore moves the matrix without
anyone editing it, which is the property Run 26 had to establish for the counts.

THE POPULATION IS DERIVED, NOT ASSUMED. The run was commissioned expecting ninety-eight
non-SCIENTIFIC_PASS targets. The re-audit yields three passes and therefore ninety-seven, and this
script prints and writes what it finds. Forcing ninety-eight would have been the failure the
prompt's own section 1 warns against.
"""

from __future__ import annotations

import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

from app.simulation.method_labels import (  # noqa: E402
    STRUCTURAL_CLAIM_LIMITS, TRUTHFUL_METHOD_LABELS,
)
from app.simulation.parameters import PARAMETER_PROVENANCE_BY_MODULE  # noqa: E402
from app.simulation.registry import (  # noqa: E402
    CORE_VOTING_MODULES, DISABLED_CONCEPT_ONLY, DISABLED_EVIDENCE_UNDER_REVIEW, DISABLED_MODULES,
    PROXY_QUALIFIERS, activation_state, load_registry,
)

sys.path.insert(0, str(ROOT / "server" / "tools"))
from run27_curation import (  # noqa: E402
    CORPUS_STATES, CURATED, FUTURE_RUNS, PARSIMONY_CLASSES, PRIORITIES, REMEDIATION_TYPES,
    SUPPLY_MECHANISMS,
)

REAUDIT = ROOT / "code_audit" / "run20_cycle12_100_reaudit.csv"
EDGES = ROOT / "code_audit" / "signal_flow_authoritative_edges.csv"
MATRIX_OUT = ROOT / "code_audit" / "run27_98_module_remediation_matrix.csv"
PACKAGES_OUT = ROOT / "code_audit" / "run27_remediation_work_packages.csv"

#: The taxonomy display names that differ from the registry name, so the edge list can be joined
#: on identity rather than on a string that two authorities disagree about. This is the A1.1
#: disagreement Run 26 recorded and this run does NOT resolve: resolving it is a production change
#: and section 13 allows one only where the inconsistency prevents the matrix being accurate. It
#: does not: the join is made explicit here instead.
EDGE_NAME_ALIASES = {"Monte Carlo EAC": "Monte Carlo EAC Forecast"}

COLUMNS = [
    "canonical_id", "current_registered_name", "category", "category_name", "group", "scope",
    "current_operational_status", "voting_status", "current_scientific_disposition",
    "actual_computation_currently_implemented", "canonical_method_required",
    "primary_remediation_type", "secondary_remediation_types",
    "exact_missing_evidence", "exact_missing_data_structure",
    "existing_source_document_availability", "existing_structured_fields_available",
    "new_document_or_form_needed", "new_structured_form_needed",
    "new_database_or_data_contract_structure_needed", "historical_series_needed",
    "external_or_reference_dataset_needed", "regulatory_authority_needed", "calibration_needed",
    "empirical_validation_needed", "lineage_or_qualification_requirement",
    "canonical_implementation_work", "truthful_rename_candidate", "redundancy_candidate",
    "research_only_candidate", "owner_decision_required", "proposed_operational_destination",
    "supply_mechanism", "proposed_artifact", "corpus_status", "parsimony_class", "work_package",
    "priority", "recommended_future_run", "secondary_future_runs", "authority_source", "notes",
]

_NEW_STRUCTURE_MECHANISMS = {
    "NEW_DOCUMENT_TYPE", "NEW_STRUCTURED_FORM", "NEW_PROJECT_DATA_OBJECT",
}
_DATASET_MECHANISMS = {
    "HISTORICAL_DATASET", "PORTFOLIO_REFERENCE_DATASET", "EXTERNAL_OFFICIAL_DATA",
}


def _reaudit_rows() -> list[dict[str, str]]:
    with REAUDIT.open(encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def _edge_fields() -> dict[str, set[str]]:
    """Module display name -> the document-emitted fields the edge list records reaching it."""
    import re
    out: dict[str, set[str]] = {}
    with EDGES.open(encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if row["edge_type"] != "DOCUMENT -> MODULE":
                continue
            found = re.findall(r"emits ([a-zA-Z0-9_, ]+?), which", row["notes"])
            fields = out.setdefault(row["downstream_name"], set())
            if found:
                for part in found[0].replace(" and ", ",").split(","):
                    part = part.strip()
                    if part:
                        fields.add(part)
    return out


def _edge_docs() -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    with EDGES.open(encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if row["edge_type"] == "DOCUMENT -> MODULE":
                out.setdefault(row["downstream_name"], set()).add(row["upstream_name"])
    return out


def _shipped_computation(code_id: str) -> str:
    label = TRUTHFUL_METHOD_LABELS.get(code_id)
    if label is not None:
        d = label.as_dict()
        return f"{d['truthful_method_name']}: {d['performs']}"
    qualifier = PROXY_QUALIFIERS.get(code_id)
    if qualifier is not None:
        return f"Published proxy qualifier: {qualifier}"
    return "As registered; no proxy qualifier and no truthful-method relabel is carried."


def _absent_structure(code_id: str) -> str:
    label = TRUTHFUL_METHOD_LABELS.get(code_id)
    if label is None:
        return ""
    return label.as_dict()["absent_canonical_structure"]


def _calibration_statement(code_id: str, audit: dict[str, str]) -> str:
    entries = PARAMETER_PROVENANCE_BY_MODULE.get(code_id, [])
    if entries:
        parts = []
        for e in entries:
            d = e.as_dict()
            parts.append(f"{d['parameter_kind']} [{d['parameter_class']}]")
        head = "; ".join(parts)
    elif audit["parameter_provenance"] == "NO_TUNABLE_VALUE":
        head = "no tunable value: the module carries no threshold, weight or boundary of its own"
    else:
        head = f"parameter provenance {audit['parameter_provenance']}"
    if audit["calibration"] == "NO_CALIBRATION_SET_EXISTS":
        return (head + ". No calibration set exists in this repository: no labelled corpus of "
                "project outcomes and no expert reference standard, so no boundary can be fitted "
                "or tested.")
    return head + f". Calibration status: {audit['calibration']}."


def _lineage_statement(audit: dict[str, str]) -> str:
    bits = []
    if audit["category9_qualification"] == "FAIL":
        bits.append("Category-9 qualification FAIL recorded by the re-audit")
    if audit["lineage_declared"] == "no":
        bits.append("no lineage declaration is carried")
    else:
        bits.append(f"lineage declared as {audit['lineage_relationship']}")
    bits.append(
        "the platform-wide Category-9 qualification gate is unimplemented and production "
        "discloses it: signal_package.py records SIGNAL_QUALIFICATION = 'unqualified' and "
        "CATEGORY_9_DEVIATION"
    )
    return "; ".join(bits) + "."


def build_rows() -> list[dict[str, str]]:
    registry = {r["new_id"]: r for r in load_registry()}
    audits = _reaudit_rows()
    fields_by_name = _edge_fields()
    docs_by_name = _edge_docs()

    rows = []
    for audit in audits:
        if audit["scientific_disposition"] == "SCIENTIFIC_PASS":
            continue
        code_id = audit["code_id"]
        reg = registry[code_id]
        cur = CURATED[code_id]

        display = EDGE_NAME_ALIASES.get(reg["module_name"], reg["module_name"])
        fields = sorted(fields_by_name.get(display, set()))
        docs = sorted(docs_by_name.get(display, set()))

        primary, secondary = _remediation_types(code_id, audit, cur)
        # RUN ASSIGNMENT. A row whose remaining work is calibration and empirical validation
        # ONLY -- no missing evidence, no re-implementation -- belongs to Run 33 by the owner's
        # own programme description, and its category run is recorded beside it rather than
        # discarded. Every other row terminates in Run 33 too, because Run 33 carries the
        # complete hundred-target re-audit, so Run 33 is its secondary. No row is an orphan and
        # no row is assigned to Run 33 by default.
        if cur["pkg"] == "PKG-CAL-BANDS":
            primary_run, secondary_runs = "Run 33", cur["run"]
        else:
            primary_run, secondary_runs = cur["run"], "Run 33"

        supply = cur["supply"]
        rows.append({
            "canonical_id": code_id,
            "current_registered_name": reg["module_name"],
            "category": reg["category"],
            "category_name": reg["category_name"],
            "group": reg["group"],
            "scope": audit["level"],
            "current_operational_status": activation_state(code_id),
            "voting_status": "voting" if code_id in CORE_VOTING_MODULES else "non-voting",
            "current_scientific_disposition": audit["scientific_disposition"],
            "actual_computation_currently_implemented": _shipped_computation(code_id),
            "canonical_method_required": cur["canon"],
            "primary_remediation_type": primary,
            "secondary_remediation_types": " ".join(secondary),
            "exact_missing_evidence": cur["missing"],
            "exact_missing_data_structure": cur["struct"] or _absent_structure(code_id),
            "existing_source_document_availability": (
                f"{len(docs)} supported document type(s) currently reach this module: "
                + (", ".join(docs) if docs else "none")
            ),
            "existing_structured_fields_available": (
                ", ".join(fields) if fields else "none on the authoritative edge list"
            ),
            "new_document_or_form_needed": (
                cur["artifact"] if supply in _NEW_STRUCTURE_MECHANISMS else ""
            ),
            "new_structured_form_needed": (
                cur["artifact"] if supply == "NEW_STRUCTURED_FORM" else ""
            ),
            "new_database_or_data_contract_structure_needed": (
                cur["struct"] if supply in (_NEW_STRUCTURE_MECHANISMS
                                            | {"DERIVED_FROM_EXISTING_QUALIFIED_DATA",
                                               "EXISTING_DOCUMENT_EXTRACTION"}) else ""
            ),
            "historical_series_needed": (
                cur["artifact"] if supply in {"HISTORICAL_DATASET", "PORTFOLIO_REFERENCE_DATASET"}
                else ""
            ),
            "external_or_reference_dataset_needed": (
                cur["artifact"] if supply in _DATASET_MECHANISMS else ""
            ),
            "regulatory_authority_needed": (
                "yes: " + cur["artifact"] if "REG" in (primary, *secondary) else "no"
            ),
            "calibration_needed": _calibration_statement(code_id, audit),
            "empirical_validation_needed": (
                audit["empirical_validation"] + ". "
                + (STRUCTURAL_CLAIM_LIMITS[code_id][1] if code_id in STRUCTURAL_CLAIM_LIMITS
                   else "No labelled holdout corpus and no expert reference standard exist for "
                        "this platform, so how often this module's banding is right is unknown.")
            ),
            "lineage_or_qualification_requirement": _lineage_statement(audit),
            "canonical_implementation_work": _implementation_work(code_id, cur, audit),
            "truthful_rename_candidate": cur["rename"],
            "redundancy_candidate": (
                "yes" if cur["pars"] in {"CONSOLIDATE_CANDIDATE", "REMOVE_CANDIDATE"} else "no"
            ),
            "research_only_candidate": (
                "yes" if cur["pars"] == "KEEP_RESEARCH_ONLY"
                or audit["scientific_disposition"] == "FUTURE_RESEARCH_ONLY" else "no"
            ),
            "owner_decision_required": _owner_decision(code_id, cur, audit),
            "proposed_operational_destination": _destination(code_id, cur, audit),
            "supply_mechanism": supply,
            "proposed_artifact": cur["artifact"],
            "corpus_status": cur["corpus"],
            "parsimony_class": cur["pars"],
            "work_package": cur["pkg"],
            "priority": cur["pri"],
            "recommended_future_run": primary_run,
            "secondary_future_runs": secondary_runs,
            "authority_source": (
                "p0-baseline/module_renumbering_map.csv; "
                "code_audit/run20_cycle12_100_reaudit.csv; "
                "server/app/simulation/method_labels.py; "
                "server/app/simulation/parameters.py; "
                "server/app/simulation/registry.py; "
                "code_audit/signal_flow_authoritative_edges.csv; "
                "research/methodology/PCEIF_100_MODULE_SUPERVISORY_METHOD_SPECIFICATION_v1.md"
            ),
            "notes": cur["note"],
        })
    return rows


def _remediation_types(code_id, audit, cur) -> tuple[str, list[str]]:
    types: list[str] = []
    if cur["missing"]:
        types.append("DATA")
    if (code_id in TRUTHFUL_METHOD_LABELS
            or audit["scientific_disposition"] in {"CORRECT_PROXY_ONLY", "FUTURE_RESEARCH_ONLY"}
            or audit["canonical_structure_required"] == "yes"):
        types.append("METHOD")
    if (audit["calibration"] == "NO_CALIBRATION_SET_EXISTS"
            or audit["parameter_provenance"] in {"UNSOURCED", "MIXED_PUBLISHED_AND_UNSOURCED"}
            or audit["threshold_provenance"] == "UNSOURCED"):
        types.append("CAL")
    if (audit["category9_qualification"] == "FAIL"
            or audit["lineage_declared"] == "no"
            or audit["lineage_relationship"] in {"CORRELATED", "SAME_SOURCE_TRANSFORM",
                                                 "SYNTHESIZED"}):
        types.append("LINEAGE")
    if (audit["regulatory_status"] != "NOT_A_REGULATORY_DETERMINATION"
            or cur["supply"] == "EXTERNAL_OFFICIAL_DATA"
            or "Regulatory" in cur["artifact"]):
        types.append("REG")
    if code_id not in DISABLED_MODULES and audit["execution_outcome"] == "RAN":
        types.append("VALIDATE")
    if (audit["scientific_disposition"] == "FUTURE_RESEARCH_ONLY"
            or cur["pars"] == "KEEP_RESEARCH_ONLY"):
        types.append("RESEARCH")
    if (cur["pars"] in {"RENAME", "CONSOLIDATE_CANDIDATE", "REMOVE_CANDIDATE",
                        "OWNER_DECISION_REQUIRED"}
            or cur["rename"]):
        types.append("PARSIMONY")
    # Order is fixed so the primary type is deterministic: the most blocking class first.
    order = ["DATA", "METHOD", "LINEAGE", "REG", "CAL", "VALIDATE", "RESEARCH", "PARSIMONY"]
    types = [t for t in order if t in types]
    assert types, code_id
    return types[0], types[1:]


def _implementation_work(code_id, cur, audit) -> str:
    if code_id in DISABLED_CONCEPT_ONLY:
        return ("Build from nothing: the formula function is never called and the module is "
                "DISABLED_UNSAFE. A real implementation is a new build, not a rename. "
                "NOT AUTHORISED IN RUN 27 and no activation is proposed.")
    if code_id in DISABLED_EVIDENCE_UNDER_REVIEW:
        return ("Execution withdrawn pending an evidence-design decision; registry entry and "
                "audit lineage retained.")
    absent = _absent_structure(code_id)
    if absent:
        return ("Implement the canonical structure once the evidence exists: " + absent
                + ". Until then the truthful method label is what the interface, export and "
                  "methods documentation publish.")
    if cur["missing"]:
        return ("The shipped arithmetic performs what its name says; the work is the evidence "
                "supply above plus the band calibration, not a re-implementation.")
    return ("No re-implementation required. The remaining work is calibration and empirical "
            "validation of the band boundaries.")


def _owner_decision(code_id, cur, audit) -> str:
    if cur["pars"] == "OWNER_DECISION_REQUIRED":
        return "yes: " + (cur["note"] or "recorded by the re-audit as OWNER_DECISION_REQUIRED")
    if cur["pars"] in {"CONSOLIDATE_CANDIDATE", "REMOVE_CANDIDATE"}:
        return ("yes: consolidation or removal is a RECOMMENDATION only. Run 27 removes nothing "
                "and consolidates nothing.")
    if cur["pars"] == "RENAME":
        return ("yes: the served participant surface is frozen and checksummed and the study is "
                "mid-sequence, so a rename on the participant surface is an instrument decision "
                "for the owner, not a remediation.")
    if cur["pars"] == "KEEP_CONDITIONAL":
        return "yes: applicability to this platform's projects is a scoping decision."
    if cur["rename"]:
        return ("yes: whether the truthful name replaces the registered name on the participant "
                "surface is an instrument decision.")
    if cur["supply"] == "NOT_REASONABLY_SUPPLIABLE":
        return "yes: the evidence cannot reasonably be supplied; retention is a parsimony decision."
    return "no"


def _destination(code_id, cur, audit) -> str:
    if code_id in DISABLED_MODULES:
        return "remains disabled; no activation is proposed by this run"
    if cur["pars"] == "KEEP_RESEARCH_ONLY":
        return "research surface only; not an operational signal"
    if code_id in CORE_VOTING_MODULES:
        return "voting"
    return "advisory, non-voting, on the signal ledger with its published claim limit"


# --------------------------------------------------------------------------------------------
# Work packages. Modules served are DERIVED from the matrix rows, so a package cannot claim a
# module the matrix does not assign to it.
# --------------------------------------------------------------------------------------------

PACKAGE_META = {
    "PKG-SCHEDNET": dict(
        name="Schedule network package",
        structure="Schedule Network Data: activities, relationships, calendars, float, status "
                  "date; with activity duration distributions and a risk-event mapping for the "
                  "sampling variants",
        newdoc="Schedule Network Export (new document type) plus Activity Duration Distribution "
               "Set and Crash Cost Table (new structured forms)",
        code="a network parser and store; a critical path engine; a sampling engine over activity "
             "durations with a correlation structure; a repetitive-work production model for line "
             "of balance and a buffer model for CCPM",
        cal="percentile reporting needs no band until an output band is claimed; buffer and "
            "compression bands need calibration once real networks exist",
        order="1. network store; 2. critical path engine; 3. duration distributions and sampling; "
              "4. the variants (LoB, CCPM, crashing)",
        run="Run 28"),
    "PKG-TIMEPHASED": dict(
        name="Time-phased baseline curve package",
        structure="Time-Phased Baseline Curve: per-period planned value, cumulative planned value, "
                  "baseline id and approval date",
        newdoc="the time_phased_schedule document type is ALREADY declared in extraction_fields.py "
               "and emits nothing these modules read; the work is an extraction contract, not a "
               "new document class",
        code="a baseline curve store; earned schedule computed against the curve; S-curve "
             "deviation computed curve against curve",
        cal="none until the curve exists; the current bands are on a different quantity",
        order="1. extraction contract for time_phased_schedule; 2. curve store; 3. A1.6; 4. A2.6",
        run="Run 28"),
    "PKG-HISTORY": dict(
        name="Reporting history and time-series package",
        structure="Reporting History Series per project, and Milestone Forecast History with "
                  "stable milestone ids",
        newdoc="none: derived from data the platform already stores period by period",
        code="a governed history accessor with a declared minimum series length; noise estimation "
             "for the filter; order identification and residual diagnostics for the projection; "
             "stable milestone identity across snapshots",
        cal="control chart k and H against an average-run-length target; prior and likelihood "
            "variances estimated rather than designed",
        order="1. history accessor and minimum length rule; 2. milestone identity; 3. per-module "
              "estimation",
        run="Run 28"),
    "PKG-REFCLASS": dict(
        name="Reference-class package",
        structure="Reference-Class Dataset: completed projects with inclusion criteria, type, "
                  "baseline, outcome, normalisation variables and vintage",
        newdoc="Reference-Class Dataset (historical dataset, sourced outside the project corpus)",
        code="a cohort selection engine with declared inclusion and exclusion; normalisation and "
             "adaptation; an empirical outcome distribution and its quantiles",
        cal="the distribution replaces chosen bands; no separate calibration once the class exists",
        order="1. dataset acquisition and governance; 2. cohort selection; 3. A3.1; 4. A3.7",
        run="Run 28"),
    "PKG-CONTRACT": dict(
        name="Contract, procurement and quantity baseline package",
        structure="Contract Baseline Data: schedule of values, approved rates and quantities, "
                  "material baseline, contingency allocations and drawdowns, independent estimates",
        newdoc="Contract Material Baseline and Current Procurement Report (new document types); "
               "Quantity Installed and Unit Rate Table and Contingency Drawdown Ledger (new "
               "structured forms); Independent Cost Estimate (new document type)",
        code="a quantity and rate store; earned-output productivity; contingency drawdown against "
             "risk retirement; an independent-estimate comparison that is genuinely independent",
        cal="material variance control limits, which registry.py records as unsourced today",
        order="1. schedule of values and rates; 2. quantities; 3. contingency ledger; 4. "
              "independent estimate",
        run="Run 28",
        note="This package is also the evidence design A3.4 Material Cost Variance was disabled "
             "pending. A3.4 is NOT one of the ninety-seven, because the scientific-audit "
             "population excludes it, but the package serves it and the owner's deferred "
             "retain-or-remove decision on it depends on this package."),
    "PKG-RISKQUANT": dict(
        name="Quantified risk register package",
        structure="Quantified Risk Register: per risk, probability, cost and schedule impact "
                  "distributions, correlation, realisation status, cost-account mapping",
        newdoc="the risk_register document type is ALREADY declared and emits no probability or "
               "impact; the work is an extraction and form contract",
        code="a sampling engine over the register; percentile reporting; the risk-to-activity "
             "mapping shared with the schedule network package",
        cal="none once sampling is real: a percentile is a percentile",
        order="1. register contract; 2. sampling engine; 3. A3.6; 4. joins to A2.10",
        run="Run 28"),
    "PKG-DENOM": dict(
        name="Document event denominator package",
        structure="Document Event Denominator: for every counted document event, the exposure "
                  "window or exposure quantity it is counted against",
        newdoc="none: report_period, work_period_from, work_period_to and items_inspected are "
               "already extracted fields; they are not joined to the counts",
        code="a join from counted events to their exposure; rate computation replacing raw counts",
        cal="rate thresholds, which are unsourced today for every module in the package",
        order="1. exposure join; 2. rate replacement; 3. thresholds",
        run="Run 29"),
    "PKG-DOCEVENT": dict(
        name="Document event evidence package",
        structure="Claim and Notice Register, Specification Conflict Register with evidence "
                  "locations, Subcontractor Assessment Record",
        newdoc="Claim and Notice Register (new document type, correspondence_notice is the natural "
               "carrier); Specification Conflict Register (new structured form)",
        code="claim-state ladder; conflict identification with retained evidence locations; "
             "assessment component storage",
        cal="escalation ladder rungs and conflict density bands",
        order="1. claim register; 2. conflict register; 3. assessment components",
        run="Run 29"),
    "PKG-DOCLABEL": dict(
        name="Document risk label and validation package",
        structure="Labelled Document Corpus with a frozen train, calibration and holdout split",
        newdoc="Labelled Document Corpus (new project data object; requires qualified reviewers)",
        code="a score construction record; precision and recall measurement against the holdout",
        cal="this package IS the calibration and validation basis for the whole platform: the "
            "absence of a labelled corpus is the stated reason no module can be calibrated",
        order="1. reviewer protocol; 2. labelling; 3. split; 4. measurement",
        run="Run 29",
        note="A4.1 Document Risk Score reaches at least twenty-eight registered modules on the "
             "authoritative edge list, so this package's fan-out is the largest in the "
             "programme."),
    "PKG-DSM": dict(
        name="DSM and system model package",
        structure="DSM Dependency Matrix and Rework Stock and Flow Series",
        newdoc="DSM Dependency Matrix (new structured form)",
        code="propagation over the matrix; stock and flow integration with observed rates",
        cal="rework probabilities and impacts per edge",
        order="1. element set; 2. dependency matrix; 3. propagation; 4. stocks and flows",
        run="Run 29"),
    "PKG-SCENARIO": dict(
        name="Scenario and input-range package",
        structure="Scenario Assumption Set and Input Range Declaration",
        newdoc="Scenario Assumption Set (new structured form)",
        code="a scenario evaluator; a response re-evaluated at each input's low and high; ranking "
             "of the resulting swings",
        cal="the ranges themselves need a basis, which is the calibration in this package",
        order="1. input range declaration; 2. scenario set; 3. sensitivity; 4. tornado",
        run="Run 29"),
    "PKG-QUEUE": dict(
        name="Queue, agent and discrete-event package",
        structure="Queue Observation Log, Agent and Resource Definition Set, DES Event Definition "
                  "Set",
        newdoc="Queue Observation Log, Agent / Resource Definition, DES Event Definition (new "
               "structured forms)",
        code="a queueing model; an agent scheduler; an event list and simulation clock",
        cal="service and arrival process fitting; replication and warm-up policy",
        order="1. observation log; 2. queueing; 3. DES; 4. ABM",
        run="Run 29",
        note="The heaviest evidence burden in the programme for the smallest number of modules. "
             "Whether it is worth it is an explicit owner parsimony question."),
    "PKG-ORPHANFIELDS": dict(
        name="Orphan extracted-field wiring package",
        structure="no new structure at all: join already-extracted safety, quality and "
                  "environmental fields to the modules named for them",
        newdoc="none. Safety Report, Quality Audit Report and Environmental Report are ALREADY "
               "supported document types and their fields are ALREADY extracted",
        code="input-contract changes so A6.1, A6.2 and A6.3 read the real evidence instead of "
             "meeting-minute proxies",
        cal="the standard safety rate convention replaces a chosen band; quality and environmental "
            "bands still need sourcing",
        order="1. input contracts; 2. abstention behaviour when the real field is absent; 3. bands",
        run="Run 31",
        note="THE CHEAPEST PACKAGE IN THE PROGRAMME AND THE ONLY ONE THAT NEEDS NO NEW EVIDENCE. "
             "environmentalComplianceRate, qualityAuditScore, totalFindings, criticalFindings, "
             "oshaIncidentRate and totalManhours are extracted and consumed by no registered "
             "module, while the three modules named for them read meeting-minute proxies."),
    "PKG-CAT9": dict(
        name="Category-9 qualification and lineage package",
        structure="Qualified Signal State per signal, a declared dependence structure over "
                  "signals, Field Provenance Record, Audit Object Graph, Reporting Cadence and "
                  "Freshness Declaration, Source Reliability Record",
        newdoc="Reporting Cadence and Freshness Declaration (new project data object); the rest is "
               "derived from data the platform already holds",
        code="the qualification gate itself, which CANNOT BE BUILT UNDER THE CURRENT FREEZE: "
             "server/app/simulation/ is frozen at sim-2026.08-v2 under a byte-identical guard, "
             "and signal_package.py is where SIGNAL_QUALIFICATION and CATEGORY_9_DEVIATION live",
        cal="none: qualification is a gate, not a threshold",
        order="1. field provenance; 2. qualification verdict object; 3. dependence declaration; "
              "4. synthesis modules read qualified state",
        run="Run 31",
        note="THIS PACKAGE IS BLOCKED BY THE PLATFORM FREEZE AND RUN 27 RECORDS THAT RATHER THAN "
             "WORKING AROUND IT. Production's own disclosure is the finding: 205 of the 397 "
             "document-to-module edges land inside the four downstream categories that the gate "
             "would qualify."),
    "PKG-REG": dict(
        name="Regulatory evidence package",
        structure="Regulatory Applicability Record: authority, instrument, clause, version, "
                  "effective date, jurisdiction, applicability predicate, the level the "
                  "instrument itself states, and the evidence object proving the condition",
        newdoc="Regulatory Applicability Record (new project data object)",
        code="an applicability engine; determination records that cite the instrument version they "
             "were made under",
        cal="none: a regulatory level is stated by the instrument or it is not a regulatory level",
        order="1. authority register; 2. applicability predicate; 3. per-module determinations",
        run="Run 31",
        note="Run 20 Cycle 2 already removed one false attribution of a FAR part to an internally "
             "chosen number. The package exists so that cannot recur."),
    "PKG-ELICIT": dict(
        name="Elicitation and evidence-parameter package",
        structure="Elicited Assessment Set: expert id, object assessed, linguistic or interval "
                  "assessment, protocol, date, agreed aggregation rule, agreement statistic",
        newdoc="Expert Elicitation Form (new structured form)",
        code="membership construction from elicited assessments rather than from hard-coded maps; "
             "an independence or dependence treatment for the combination rules",
        cal="this package IS the calibration for the whole of Category 7",
        order="1. elicitation protocol; 2. assessment store; 3. membership construction; 4. "
              "per-method combination",
        run="Run 30",
        note="Serves the largest number of modules of any package. It is also where the "
             "consolidation question is sharpest: the variants differ in their band boundaries, "
             "not in their evidence."),
    "PKG-ALTERNATIVES": dict(
        name="Alternatives, objectives and constraints package",
        structure="Decision Alternatives Table and Objective and Constraint Set: actions, decision "
                  "variables with bounds and units, objective coefficients and sense, constraint "
                  "matrix and right-hand sides",
        newdoc="Decision Alternatives Table and Objective and Constraint Set (new structured "
               "forms)",
        code="an optimisation layer; a dominance relation; a payoff matrix over states of nature; "
             "a genuine multi-alternative ranking",
        cal="none intrinsic: an optimum is defined by the model, not by a band",
        order="1. alternatives table; 2. objectives and constraints; 3. ranking and dominance; "
              "4. optimisation",
        run="Run 32",
        note="ONE STRUCTURE UNBLOCKS THE WHOLE OF CATEGORY 10 PLUS TWO CATEGORY 7 MODULES. It is "
             "the highest module-per-structure ratio in the programme after the orphan-field "
             "package. The platform already collects courses of action from participants, which "
             "is the nearest existing thing to an alternatives table and should be examined "
             "before a new form is designed."),
    "PKG-PORTFOLIO-HISTORY": dict(
        name="Portfolio cohort and history package",
        structure="Portfolio Cohort Definition and Portfolio Reporting History: inclusion "
                  "criteria, minimum cohort size, per-project per-period readings, vintage",
        newdoc="Portfolio Cohort Definition (new project data object); the history is derived",
        code="a cohort accessor; variance components for shrinkage; a declared composition for the "
             "composite anomaly score that does not double-count its siblings",
        cal="anomaly score thresholds; percentile small-n behaviour; trend class boundaries",
        order="1. cohort definition; 2. pooled history; 3. per-module estimation; 4. D1.5 "
              "recomposition",
        run="Run 32"),
    "PKG-EXTERNAL": dict(
        name="External official data package",
        structure="External Price Index Record and Past Performance Information Record",
        newdoc="external official sources, not project documents",
        code="index lookup with vintage pinning; a past-performance accessor that cannot be "
             "confused with project-document ratings",
        cal="none: an index value is published, not chosen",
        order="1. source selection and licensing; 2. vintage pinning; 3. per-module use",
        run="Run 28",
        note="A6.4 in this package is scheduled with Run 31 because its category sits there; the "
             "shared external-data work is Run 28's."),
    "PKG-CAL-BANDS": dict(
        name="Band calibration and empirical validation package",
        structure="no new evidence structure: these modules already receive every input their "
                  "canonical method needs",
        newdoc="none; but calibration itself requires the Labelled Document Corpus and an outcome "
               "corpus, which are PKG-DOCLABEL and PKG-REFCLASS",
        code="none: the arithmetic performs what the name says",
        cal="THE WHOLE PACKAGE. Band boundaries with an objective, a metric, an error target, a "
            "frozen selection, a holdout evaluation and a sensitivity analysis",
        order="after PKG-DOCLABEL and PKG-REFCLASS exist; nothing here can be calibrated before "
              "a calibration set does",
        run="Run 33",
        note="These are the modules where the honest answer is 'the method is right and the "
             "threshold is invented'. They need no new evidence about the project; they need a "
             "corpus to fit against."),
}


def build_packages(rows) -> list[dict[str, str]]:
    served: dict[str, list[str]] = {}
    for r in rows:
        served.setdefault(r["work_package"], []).append(
            f"{r['canonical_id']} {r['current_registered_name']}")
    out = []
    for pkg, mods in sorted(served.items()):
        meta = PACKAGE_META[pkg]
        out.append({
            "package_id": pkg,
            "package_name": meta["name"],
            "modules_served_count": str(len(mods)),
            "modules_served": "; ".join(mods),
            "shared_data_structure": meta["structure"],
            "new_document_or_form_required": meta["newdoc"],
            "code_work_later_required": meta["code"],
            "calibration_work_later_required": meta["cal"],
            "dependency_order": meta["order"],
            "recommended_run": meta["run"],
            "notes": meta.get("note", ""),
        })
    return out


def _write(path, columns, rows):
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main() -> int:
    audits = _reaudit_rows()
    passes = [a for a in audits if a["scientific_disposition"] == "SCIENTIFIC_PASS"]
    rows = build_rows()
    packages = build_packages(rows)

    # Vocabulary enforcement happens here as well as in the guard, so a bad build cannot be
    # committed even if the guard is not run first.
    for r in rows:
        assert r["supply_mechanism"] in SUPPLY_MECHANISMS or r["supply_mechanism"] == "", r
        assert r["corpus_status"] in CORPUS_STATES, r
        assert r["parsimony_class"] in PARSIMONY_CLASSES, r
        assert r["priority"] in PRIORITIES, r
        assert r["recommended_future_run"] in FUTURE_RUNS, r
        assert r["primary_remediation_type"] in REMEDIATION_TYPES, r

    _write(MATRIX_OUT, COLUMNS, rows)
    _write(PACKAGES_OUT, list(packages[0].keys()), packages)

    print(f"scientific targets                : {len(audits)}")
    print(f"unique target identities          : {len({a['code_id'] for a in audits})}")
    print(f"SCIENTIFIC_PASS                   : {len(passes)} "
          f"({', '.join(p['code_id'] + ' ' + p['module_name'] for p in passes)})")
    print(f"non-SCIENTIFIC_PASS               : {len(audits) - len(passes)}")
    print(f"matrix rows written               : {len(rows)}")
    print(f"work packages written             : {len(packages)}")
    print(f"matrix   -> {MATRIX_OUT.relative_to(ROOT)}")
    print(f"packages -> {PACKAGES_OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
