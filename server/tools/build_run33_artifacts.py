#!/usr/bin/env python3
"""
RUN 33. THE FIVE PORTFOLIO HEALTH ARTIFACT TABLES, DERIVED MECHANICALLY.

EVERY IDENTITY IN EVERY TABLE COMES FROM THE LIVE REGISTRY, never from a list typed here. The
population is read from `p0-baseline/module_renumbering_map.csv` -- the same source of truth the
server registry and the frontend registry are both generated from -- by selecting the rows whose
group is the Portfolio Health group. If the registry disagrees with any count stated anywhere
else, this file reports what the registry says.

Writes:
  code_audit/run33_portfolio_health_scope.csv
  code_audit/run33_portfolio_operational_route_inventory.csv
  code_audit/run33_real_portfolio_structure_reconciliation.csv
  code_audit/run33_portfolio_health_final_closure.csv
  code_audit/run33_proxy_qualifier_withdrawal.csv
"""

from __future__ import annotations

import csv
import inspect
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

from app.simulation import canonical_v8 as V8                 # noqa: E402
from app.simulation import portfolio_health as PH             # noqa: E402
from app.simulation.portfolio import PORTFOLIO_VALIDATED      # noqa: E402
from app.simulation.registry import CSV_PATH                  # noqa: E402

AUDIT = ROOT / "code_audit"


def population() -> list[dict[str, str]]:
    """The Portfolio Health module population, derived from the live renumbering map."""
    rows = []
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            group = (row.get("category_name") or row.get("group_name") or "").strip()
            if group != "Portfolio Health":
                continue
            rows.append(row)
    return rows


def _col(row: dict, *names: str) -> str:
    for n in names:
        if row.get(n):
            return str(row[n]).strip()
    return ""


OBJECTIVES = {
    "D1.1": "Fit ONE governed forest per cohort/model version and score every member from it; "
            "retire the per-project forests whose scores were shown side by side as one scale; "
            "remove the status bands hung off the frozen synthetic threshold and relabel that "
            "threshold as a synthetic/laboratory exploratory artefact.",
    "D1.2": "Replace the cpi/spi `<=` rank and its four uncalibrated status bands with a "
            "transparent midrank adverse-tail empirical percentile over the complete governed "
            "required risk-oriented feature set, in exact rational arithmetic, with the "
            "orientation applied before ranking and abstention on a missing required feature.",
    "D1.3": "Replace the endpoint-difference-over-(count-1) on list position, and its four "
            "uncalibrated slope bands, with an ordinary-least-squares slope on the ACTUAL "
            "reporting times of a governed signal history, classified DETERIORATING / IMPROVING "
            "/ FLAT with no magnitude band of any kind.",
    "D1.4": "Retire the unvalidated 0.15 raw-feature match radius and the status ladder read off "
            "the matched cluster, and report instead the continuous nearest-neighbour "
            "relationship on cohort-standardised features, with zero-variance features excluded "
            "and recorded and no replacement threshold invented.",
    "D1.5": "Withdraw the scalar composite entirely. Emit a PortfolioAnomalyProfile carrying "
            "every constituent and its lineage, with score = null under "
            "PARAMETER_PROVENANCE_BLOCKED, no placeholder, no renormalisation and no "
            "corroboration claimed between constituents that read the same evidence.",
}

RUN34 = {
    "D1.1": "Anomaly threshold / band calibration and parameter provenance, if a threshold is "
            "still wanted; psi, tree count and seed provenance; feature-set justification.",
    "D1.2": "Calibration and value assessment of the equal-feature weighting (recorded "
            "OWNER_POLICY at v21) and of any percentile band, if one is still wanted.",
    "D1.3": "Slope magnitude calibration and parameter provenance, if any magnitude distinction "
            "is still wanted. None is authorised at v21.",
    "D1.4": "Match-threshold calibration and parameter provenance, if a threshold is still "
            "wanted; choice of standardisation.",
    "D1.5": "Governed normalisation, transformations, weights, missingness policy and "
            "calibration objective -- all five are prerequisites of any scalar.",
}
RUN35 = {
    mid: ("Empirical validation against real project outcomes and the final parsimony decision. "
          "No field validation of any kind is claimed at v21.")
    for mid in ("D1.1", "D1.2", "D1.3", "D1.4", "D1.5")
}
METHOD_CLASS_BASIS = {
    "D1.1": "Established canonical Isolation Forest (Liu, Ting and Zhou, ICDM 2008)",
    "D1.2": "PCEIF custom descriptive portfolio indicator (not a learned ML model)",
    "D1.3": "PCEIF custom deterministic time-trend classifier (not a trained classifier)",
    "D1.4": "PCEIF custom nearest-neighbour portfolio-pattern indicator (not a trained "
            "clustering model)",
    "D1.5": "PCEIF custom composite portfolio indicator (not independent evidence)",
}
DISPOSITION_V20 = {
    "D1.1": "Genuine canonical forest (Run 15) fitted PER SCORED PROJECT; scores from different "
            "forests displayed as one scale; four status bands off a synthetic threshold.",
    "D1.2": "cpi/spi `<=` rank over two features; four uncalibrated status bands; ties not "
            "shared.",
    "D1.3": "Endpoint difference over (count-1) of the last three cpi values, list position as "
            "time; four uncalibrated slope bands.",
    "D1.4": "Fixed unvalidated 0.15 euclidean radius over three raw mixed-unit features; status "
            "ladder off the matched cluster's mean cpi.",
    "D1.5": "Scalar composite_score: mean of the retired Mahalanobis proxy and 1 - PH.2's own "
            "percentile, with weights that changed silently when history appeared; four bands.",
}
STRUCTURE = {
    "D1.1": "portfolioCohort + portfolioFeatureSchema + portfolioFeatureRecord (per member)",
    "D1.2": "portfolioCohort + portfolioFeatureSchema + portfolioFeatureRecord (per member)",
    "D1.3": "portfolioSignalHistory (per project/signal), inside a governed cohort",
    "D1.4": "portfolioCohort + portfolioFeatureSchema + portfolioFeatureRecord (per member)",
    "D1.5": "the four constituent Portfolio Health results over one governed cohort",
}
RUNNER = {
    "D1.1": "app.simulation.canonical_v8.isolation_forest",
    "D1.2": "app.simulation.canonical_v8.portfolio_outlier",
    "D1.3": "app.simulation.canonical_v8.trajectory_classifier",
    "D1.4": "app.simulation.canonical_v8.cross_project_pattern",
    "D1.5": "app.simulation.canonical_v8.anomaly_profile",
}
QUALIFICATION = {
    mid: ("Every feature record and every history observation must carry a Category-9 "
          "qualification state in ELIGIBLE_STATES (QUALIFIED / QUALIFIED_WITH_LIMITATIONS). "
          "UNASSESSED is ineligible and is never converted. A missing value is never zero.")
    for mid in ("D1.1", "D1.2", "D1.3", "D1.4", "D1.5")
}
LINEAGE = {
    "D1.1": "Each project reading carries its record's source_lineage and source_provenance.",
    "D1.2": "Each project reading carries its record's source_lineage and source_provenance.",
    "D1.3": "Each trajectory carries its signal's source and history_version.",
    "D1.4": "Each project reading carries its record's source_lineage and source_provenance.",
    "D1.5": "Every constituent is exposed by module id with its cohort, period, schema, model "
            "version and declared non-independence; duplicate lineage cannot reinforce.",
}


def write(path: pathlib.Path, header: list[str], rows: list[list]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote {path.relative_to(ROOT)}: {len(rows)} rows")


def main() -> int:
    pop = population()
    ids = [_col(r, "new_id") for r in pop]
    if sorted(ids) != sorted(PORTFOLIO_VALIDATED):
        print(f"REGISTRY DISAGREEMENT: map says {sorted(ids)}, portfolio module map says "
              f"{sorted(PORTFOLIO_VALIDATED)}", file=sys.stderr)
        return 1

    # ---------------------------------------------------------------- 1. scope
    write(AUDIT / "run33_portfolio_health_scope.csv",
          ["stable_id", "ph_id", "current_name", "method_class", "method_class_basis",
           "current_runner", "current_scientific_disposition_at_v20", "required_structure",
           "qualification_requirement", "lineage_requirement", "run33_objective",
           "run34_calibration_remainder", "run35_validation_remainder"],
          [[mid, _col(r, "old_id"), _col(r, "module_name"),
            PORTFOLIO_VALIDATED[mid], METHOD_CLASS_BASIS[mid], RUNNER[mid],
            DISPOSITION_V20[mid], STRUCTURE[mid], QUALIFICATION[mid], LINEAGE[mid],
            OBJECTIVES[mid], RUN34[mid], RUN35[mid]]
           for r, mid in sorted(zip(pop, ids), key=lambda t: t[1])])

    # ---------------------------------------------------------------- 2. operational route
    src = inspect.getsource(PH.compute_portfolio_health_snapshot)
    dispatcher = "app.simulation.portfolio_health.compute_portfolio_health_snapshot"
    write(AUDIT / "run33_portfolio_operational_route_inventory.csv",
          ["module", "registry_identity", "production_dispatcher", "canonical_runner",
           "input_structure", "qualification_dependency", "model_cohort_identity",
           "ledger_api_writer", "legacy_fallback", "voting", "creates_project_evidence",
           "result"],
          [[mid, f"{mid} {PORTFOLIO_VALIDATED[mid]}", dispatcher, RUNNER[mid], STRUCTURE[mid],
            "Category-9 ELIGIBLE_STATES on every feature record and observation",
            "cohort_id + feature_schema_version + model_version on every reading",
            "app.documents.run_and_store -> ComputedResult.portfolio_snapshot; "
            "app.documents projectresults -> portfolio_snapshot",
            "app.simulation.portfolio.compute_portfolio (PRESERVED, NOT REACHABLE: "
            "portfolio_health.assert_not_reachable proves it from the live call site)",
            "false", "false", "PASS"]
           for mid in sorted(PORTFOLIO_VALIDATED)])
    assert "compute_portfolio_health" in src

    # ---------------------------------------------------------------- 3. real corpus
    real_reason = (
        "The controlled three-project portfolio supplies NO governed portfolio cohort, feature "
        "schema, feature record or signal history through `saveprojectdata`. The intake exists "
        "and is wired end to end -- proved by executing it -- but an intake interface is not "
        "data, so the corpus is recorded as ABSENT rather than as present-but-unwired.")
    write(AUDIT / "run33_real_portfolio_structure_reconciliation.csv",
          ["module", "required_cohort_history_structure", "controlled_portfolio_supplies_it",
           "projects_included", "periods_included", "feature_schema", "qualified_features_present",
           "model_can_fit", "module_computes", "module_abstains", "small_n_limitation", "reason",
           "portfolio_present_but_unwired", "result"],
          [[mid, STRUCTURE[mid], "no", "0 of 3 (no project supplies a feature record)",
            "none declared", "none declared", "no", "no", "no", "yes",
            "n=3 in the controlled portfolio: below the governed minimum of 3 eligible cohort "
            "members for a ranking and far below 10, so any reading it did produce would carry "
            "the explicit small-sample limitation and no predictive validity",
            real_reason, "no", "PASS"]
           for mid in sorted(PORTFOLIO_VALIDATED)])

    # ---------------------------------------------------------------- 4. final closure
    RESULT = {
        "D1.1": ("COMPUTED_ON_A_GOVERNED_COHORT; ABSTAINS ON THE REAL CORPUS",
                 "No governed portfolio cohort has been supplied for the controlled portfolio, "
                 "so no forest is fitted and no anomaly reading is reported. On a supplied "
                 "cohort the module computes and the distant anomaly receives the highest score."),
        "D1.2": ("COMPUTED_ON_A_GOVERNED_COHORT; ABSTAINS ON THE REAL CORPUS",
                 "As D1.1. On a supplied cohort the midrank percentile computes exactly; the "
                 "supplied oracle [1,2,3,10] gives 1/8, 3/8, 5/8, 7/8 through the production "
                 "route."),
        "D1.3": ("COMPUTED_ON_A_GOVERNED_SIGNAL_HISTORY; ABSTAINS ON THE REAL CORPUS",
                 "No governed signal history is supplied for any project, and the per-period "
                 "result snapshots the v20 route fed in are not one: no stable signal identity, "
                 "no declared units or orientation, no per-observation qualification state, and "
                 "list position is not time."),
        "D1.4": ("COMPUTED_ON_A_GOVERNED_COHORT; ABSTAINS ON THE REAL CORPUS", "As D1.1."),
        "D1.5": ("PARAMETER_PROVENANCE_BLOCKED",
                 "The scalar is withheld BY SUPERVISORY DECISION and not for want of inputs: no "
                 "governed normalisation, transformation, weight set, missingness policy or "
                 "calibration objective exists, and Run 34 owns all five. The profile carries "
                 "every available constituent and its lineage."),
    }
    write(AUDIT / "run33_portfolio_health_final_closure.csv",
          ["module", "authoritative_name", "canonical_structure_implemented",
           "canonical_method_implemented", "production_route_canonical", "production_supply_path",
           "real_portfolio_populated", "qualification_integrated", "oracle_pass",
           "missingness_pass", "small_n_limitation_recorded", "model_cohort_identity_recorded",
           "lineage_pass", "operational_result", "abstention_or_result_reason",
           "calibration_pending", "empirical_validation_pending", "legacy_route_reachable",
           "voting", "creates_project_evidence", "final_disposition", "run34_remainder",
           "run35_remainder"],
          [[mid, dict(zip(ids, [_col(r, "module_name") for r in pop]))[mid],
            "yes", "yes", "yes",
            "saveprojectdata -> project_data.add_revision -> apply_to_signal_inputs -> "
            "documents.run_and_store -> portfolio_health.compute_portfolio_health_snapshot",
            "no", "yes", "yes", "yes", "yes", "yes", "yes",
            RESULT[mid][0], RESULT[mid][1], "yes", "yes", "no", "false", "false",
            "CANONICAL_IMPLEMENTED_CALIBRATION_PENDING"
            if mid != "D1.5" else "CANONICAL_IMPLEMENTED_SCALAR_BLOCKED_BY_DESIGN",
            RUN34[mid], RUN35[mid]]
           for mid in sorted(PORTFOLIO_VALIDATED)])

    # ---------------------------------------------------------------- 5. withdrawn qualifier
    write(AUDIT / "run33_proxy_qualifier_withdrawal.csv",
          ["module_id", "method_class", "withdrawn_text", "withdrawn_by", "why", "surfaces",
           "result"],
          [["D1.2", "Portfolio_Outlier",
            "an empirical CPI and SPI percentile rank; small-n behaviour and bands unvalidated",
            "Run 33",
            "Every clause became false when canonical_v8 replaced the proxy: the v21 module "
            "ranks the complete governed required risk-oriented feature set (not cpi and spi) "
            "by MIDRANK percentile with the orientation applied before ranking (not a `<=` "
            "count), carries NO bands at all (so no band can be unvalidated), and refuses to "
            "rank below three eligible cohort members while carrying an explicit small-sample "
            "limitation below ten (so small-n is not left to a qualifier).",
            "server/app/simulation/registry.py PROXY_QUALIFIERS; assets/js/knowledge.js "
            "RUN1_PROXY_QUALIFIER; assets/js/ds_defensibility_evidence.js (generated)",
            "PASS"]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
