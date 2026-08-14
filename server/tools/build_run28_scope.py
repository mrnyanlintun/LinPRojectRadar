#!/usr/bin/env python3
"""
RUN 28. THE CATEGORY 1 TO 3 SCOPE, DERIVED FROM RUN 27 RATHER THAN WRITTEN FROM MEMORY.

The owner's Prompt A section 4 says in terms: do not create your own module list from memory;
select every remaining remediation row assigned to Categories 1, 2 and 3 from the Run-27 matrix
and reconcile them mechanically to the current registry. That is what this file does, and the
reconciliation is a comparison of two independently produced lists rather than a restatement of
one of them: the population comes from code_audit/run27_98_module_remediation_matrix.csv and the
identities and names come from the registry the server actually runs.

Writes code_audit/run28_cat1_3_scope.csv.
"""

from __future__ import annotations

import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "server"))

from app.simulation import registry as REG  # noqa: E402
from app.simulation import lineage as LIN  # noqa: E402
from app.simulation.canonical import CANONICAL_STRUCTURE_KEYS  # noqa: E402
from app.simulation.canonical_v3 import V3_STRUCTURE_KEYS  # noqa: E402

MATRIX = ROOT / "code_audit" / "run27_98_module_remediation_matrix.csv"
OUT = ROOT / "code_audit" / "run28_cat1_3_scope.csv"

#: The two renames the owner authorised for Categories 1 to 3 in this run, and no others.
APPROVED_RENAMES = {
    "A1.10": "CPI Shrinkage Forecast",
    "A1.11": "Independent EAC Reconciliation Index",
}

#: What each module's v3 disposition is, and what is left for a later run. Written against the
#: supplied supervisory contract, module by module.
DISPOSITION: dict[str, tuple[str, str, str]] = {
    # id: (post-Run-28 disposition, the v3 supply path, what remains and for which run)
    "A1.1": ("CANONICAL_RETAINED_CALIBRATION_PENDING",
             "the PCEIF stochastic model is retained; a declared cost-driver distribution set is "
             "now readable and its Beta-PERT moments are hand-checked against the contract's own "
             "lambda-4 oracle",
             "Run 33: band calibration and the elicitation record behind each distribution"),
    "A1.2": ("CANONICAL_FROZEN_DESIGN",
             "the two-sided tabular CUSUM is unchanged; the contract freezes k = 0.5 sigma and "
             "h = 5 sigma and forbids retuning them in this run, and a control chart design "
             "record is now readable for provenance",
             "Run 33: the in-control window, the sigma estimate and the average-run-length "
             "target behind the frozen design"),
    "A1.3": ("CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED",
             "a governed Bayesian model record: a prior with its source, an observation model "
             "with the basis its variance was estimated from",
             "Run 33: field calibration of the prior and observation variances. Run 31: the "
             "Category-9 qualification of the record's own provenance"),
    "A1.4": ("CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED",
             "a governed state-space record: the readings, the starting estimate and its "
             "uncertainty, and the process and measurement variances with the source of each",
             "Run 33: Q and R calibration. Run 27 established the measurement variance IS "
             "estimable from repeated readings of one period; assembling that estimate into the "
             "record from the corpus is corpus work this run did not do"),
    "A1.5": ("CANONICAL_IMPLEMENTED_HISTORY_REQUIRED",
             "the cost performance history already assembled by documents.py, now identified as "
             "an ARIMA(p,d,q) by AICc with residual diagnostics and a prediction interval",
             "Run 33: nothing calibratable remains in the identification itself; the minimum "
             "history of eight readings is a stated design choice a later run may revisit"),
    "A1.6": ("CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED",
             "a governed time-phased baseline: the cumulative planned value at the end of each "
             "period, with its baseline version and approval source",
             "corpus: the cumulative PV curve is not extracted from any document type today"),
    "A1.7": ("SCIENTIFIC_PASS_PROTECTED",
             "untouched: arithmetic, bands, citations and vote are byte-identical",
             "nothing"),
    "A1.8": ("SCIENTIFIC_PASS_PROTECTED",
             "untouched: arithmetic, bands, citations and vote are byte-identical",
             "nothing"),
    "A1.9": ("CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED",
             "an approved time-phased expenditure baseline, read at the governed status period",
             "corpus: no document type carries an approved expenditure profile today. The "
             "contract supplies no status bands for this indicator at all"),
    "A1.10": ("CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED",
              "a governed reference population with its membership basis, the weight estimation "
              "method and the data vintage; a weight declared fixed is refused",
              "Run 33: final empirical weight calibration"),
    "A1.11": ("CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED",
              "two provenance-distinct estimates whose independence is CHECKED at run time: the "
              "method and the responsible party must both differ",
              "Run 33: reconciliation bands. corpus: no independent estimate is collected today"),
    "A2.1": ("CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED",
             "a governed activity network with three-point durations; every trial redraws every "
             "duration and recomputes the forward and backward passes",
             "corpus: no activity network is extracted from any document type today"),
    "A2.2": ("CANONICAL_EXTENDED_CALIBRATION_PENDING",
             "the line of balance already required since Run 10B, now carrying the PLANNED "
             "production rate beside the actual one so deterioration is visible",
             "Run 33: no boundary for a production rate ratio is established"),
    "A2.3": ("CANONICAL_EXTENDED_CALIBRATION_PENDING",
             "the critical chain and sized buffer already required since Run 10B, now reporting "
             "the contract's buffer consumed and buffer consumption ratio",
             "Run 33: the fever-chart lines are reported as the policy lines they are and no "
             "colour is asserted from them"),
    "A2.4": ("CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED",
             "the schedule network's reconciled baseline and current remaining durations at one "
             "governed status basis",
             "Run 33: compression bands. corpus: no activity network today"),
    "A2.5": ("CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED",
             "float from the network's own forward and backward passes, against the baseline "
             "float the network states",
             "Run 33: float bands. corpus: no activity network today"),
    "A2.6": ("CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED",
             "the time-phased baseline and the matching actual series on one measurement basis; "
             "a single point is reported as a point and never as a trend",
             "Run 33: S-curve bands. corpus: no cumulative series today"),
    "A2.7": ("CANONICAL_IMPLEMENTED_AND_WIRED",
             "WIRED FROM THE CORPUS by this run: documents.py assembles a milestone forecast "
             "history from the baseline finish dates already extracted per activity and stored "
             "per period, so variance against the original commitment is measurable on real "
             "documents for the first time",
             "Run 33: slip bands"),
    "A2.8": ("CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED",
             "a governed look-ahead inventory: the window, the activity identities, each "
             "activity's constraint status and the category of each open constraint",
             "Run 33: readiness bands, which the contract names as policy. corpus: no "
             "constraint inventory today"),
    "A2.9": ("CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED",
             "a time-phased resource profile: demand against available capacity per period and "
             "per resource type",
             "Run 33: load bands. corpus: no capacity figure is collected today"),
    "A2.10": ("CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED",
              "Monte Carlo over the schedule network, recomputing the network every trial, with "
              "the empirical quantile convention frozen for the whole v3 line",
              "corpus: no activity network and no duration distributions today"),
    "A2.11": ("CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED",
              "the CPM forward and backward passes: project finish, critical activities and "
              "total float per activity",
              "corpus: no activity network today. The registered name is kept in Run 28 on the "
              "owner's instruction"),
    "A3.1": ("CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED",
             "a governed reference class with inclusion and exclusion criteria, an outcome "
             "definition, normalization, a data vintage and a governed percentile",
             "corpus: no population of completed comparable projects is held"),
    "A3.2": ("CANONICAL_RETAINED_BANDS_REMOVED",
             "the consumed fraction and the progress-normalised burn, both unchanged; the "
             "four-band ladder is removed because the contract supplies no universal bands",
             "Run 33: threshold calibration"),
    "A3.3": ("CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED",
             "a production record: the installed and planned quantities, the unit both are "
             "counted in, and the labour hours each took",
             "corpus: no installed quantity is extracted today"),
    "A3.4": ("REGISTERED_DISABLED_UNCHANGED",
             "not executed, not reactivated, not deleted; its registry entry and audit lineage "
             "are retained exactly as Run 16 left them",
             "owner: the evidence and context decision remains open"),
    "A3.5": ("CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED",
             "an explicit allocation base: the planned and actual overhead and the planned and "
             "actual amount of the driver it is absorbed over",
             "corpus: no allocation base is collected today"),
    "A3.6": ("CANONICAL_IMPLEMENTED_AND_WIRED",
             "WIRED FROM THE CORPUS by this run: documents.py assembles a cost risk model from "
             "the project's budget at completion and the risk register rows carrying BOTH a "
             "probability and a cost impact, closing the deferral this file has carried since "
             "the risk-register run",
             "Run 33: nothing calibratable remains in the simulation itself"),
    "A3.7": ("CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED",
             "an identified analog with its provenance, comparability criteria, normalization "
             "and adaptation factors",
             "corpus: no analog record is collected today"),
    "A3.8": ("DISABLED_LABORATORY_ONLY",
             "the canonical fitted linear model exists in canonical_v3 with its oracle; NO "
             "production path reaches it and the module remains disabled and non-voting",
             "owner: the activation decision. Run 33: coefficient fitting on a real dataset"),
    "A3.9": ("CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED",
             "a named external price index with its authority, geography, scope, base period, "
             "observation period and vintage; no index level is hard-coded anywhere",
             "corpus/external: no official index series is held. This is the one item on the "
             "list that needs data from outside the platform entirely"),
}


def main() -> int:
    matrix = list(csv.DictReader(MATRIX.open(encoding="utf-8-sig")))
    idx = REG.registry_index()
    scope = [r for r in matrix if r["category"] in ("A1", "A2", "A3")]

    problems = []
    for r in scope:
        mid = r["canonical_id"]
        if mid not in idx:
            problems.append(f"{mid} is in the Run-27 matrix and not in the registry")
    for mid in sorted(DISPOSITION):
        if mid not in idx:
            problems.append(f"{mid} has a disposition and is not in the registry")

    # A3.4 is registered, disabled and EXCLUDED from the scientific execution population, so it
    # is not a Run-27 remediation row. It is carried in this file anyway, marked as excluded, so
    # the scope document is a complete account of Categories 1 to 3 rather than of the
    # remediable part of them.
    ids = [r["canonical_id"] for r in scope]
    passes = ["A1.7", "A1.8"]

    rows = []
    for r in sorted(scope + [{"canonical_id": m, "category": m.split(".")[0],
                              "current_registered_name": idx[m]["module_name"],
                              "current_scientific_disposition": "SCIENTIFIC_PASS"
                              if m in passes else "EXCLUDED_DISABLED",
                              "primary_remediation_type": "", "secondary_remediation_types": "",
                              "exact_missing_evidence": "", "exact_missing_data_structure": "",
                              "calibration_needed": "", "empirical_validation_needed": "",
                              "lineage_or_qualification_requirement": "", "work_package": "",
                              "recommended_future_run": ""}
                             for m in ("A1.7", "A1.8", "A3.4")],
                       key=lambda r: (r["category"], int(r["canonical_id"].split(".")[1]))):
        mid = r["canonical_id"]
        disp, supply, remaining = DISPOSITION[mid]
        lin = LIN.lineage_for(mid)
        rows.append({
            "canonical_id": mid,
            "current_registered_name": idx[mid]["module_name"],
            "name_run27_recorded": r.get("current_registered_name") or idx[mid]["module_name"],
            "approved_v3_name": APPROVED_RENAMES.get(mid, ""),
            "run27_scientific_disposition": r.get("current_scientific_disposition") or "",
            "run27_primary_remediation": r.get("primary_remediation_type") or "",
            "run27_secondary_remediation": r.get("secondary_remediation_types") or "",
            "data_requirement": r.get("exact_missing_evidence") or "",
            "method_requirement": r.get("exact_missing_data_structure") or "",
            "cal_requirement": r.get("calibration_needed") or "",
            "validate_requirement": r.get("empirical_validation_needed") or "",
            "lineage_requirement": r.get("lineage_or_qualification_requirement") or "",
            "v3_structure_key": V3_STRUCTURE_KEYS.get(mid)
                                or CANONICAL_STRUCTURE_KEYS.get(mid) or "",
            "existing_evidence": supply,
            "run28_objective": disp,
            "post_run28_disposition": disp,
            "declared_lineage_bodies": "; ".join(lin["lineage_group_ids"]) if lin else "",
            "voting": "yes" if mid in REG.CORE_VOTING_MODULES else "no",
            "operationally_disabled": "yes" if mid in REG.DISABLED_MODULES else "no",
            "remaining_work_and_run": remaining,
        })

    with OUT.open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for row in rows:
            w.writerow(row)

    print(f"Run-27 matrix rows in Categories 1 to 3 (the remediation population): {len(scope)}")
    print(f"  Category 1: {sum(1 for r in scope if r['category'] == 'A1')}")
    print(f"  Category 2: {sum(1 for r in scope if r['category'] == 'A2')}")
    print(f"  Category 3: {sum(1 for r in scope if r['category'] == 'A3')}")
    print(f"scope rows written (the population plus the two passes and the disabled module): "
          f"{len(rows)}")
    print(f"wrote {OUT.relative_to(ROOT)}")
    if problems:
        print("RECONCILIATION PROBLEMS:")
        for p in problems:
            print("  -", p)
    print(f"RESULT: {len(rows) - len(problems)}/{len(rows)} checks passed")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
