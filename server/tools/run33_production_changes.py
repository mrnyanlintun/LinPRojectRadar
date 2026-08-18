"""
RUN 33. THE PRODUCTION FILES THIS RUN CREATED, DECLARED.

WHY THIS FILE EXISTS, and it is the Run-28/29/30/31/32 precedent unchanged. The Run-20 baseline
freeze compares production bytes against a pinned baseline, and a file that DID NOT EXIST when
that freeze was taken has no baseline row to differ from -- so without a declaration a new
production file could appear in the simulation package with nothing anywhere recording it. The
declared-production-changes guard reads this list alongside the earlier runs'.

IT IS DECLARED HERE AND NOT FOLDED INTO RUN 32's LIST, for the same reason Run 32 was not folded
into Run 31's: a run's manifest is the record of what THAT run did, and merging them would
falsify both.
"""

from __future__ import annotations

#: Production files Run 33 CREATED.
RUN33_NEW_PRODUCTION_FILES: dict[str, str] = {
    "server/app/simulation/canonical_v8.py":
        "THE CANONICAL PORTFOLIO HEALTH LAYER, v21. Four of the five measures were named for "
        "methods they were not carrying out, and the fifth -- a genuine isolation forest since "
        "Run 15 -- was fitted ONCE PER SCORED PROJECT, so the scores a portfolio card displayed "
        "side by side came from different forests trained on different populations and "
        "normalised by different constants. Portfolio Outlier Detection was a `less than or "
        "equal` rank over the cost and schedule indices alone, with four uncalibrated status "
        "bands and no shared rank for tied projects; the Signal Trajectory Classifier divided "
        "the endpoint difference of the last three cost-index values by the count minus one and "
        "read LIST POSITION as time, under four uncalibrated slope bands; the Cross-Project "
        "Pattern Detector declared a project similar inside a fixed unvalidated 0.15 euclidean "
        "radius over three RAW mixed-unit features and then banded the matched cluster's mean "
        "cost index, so a cluster of healthy peers produced a status; and the Anomaly Score was "
        "the mean of the RETIRED Mahalanobis proxy and one minus the outlier module's own "
        "percentile, with effective weights that changed silently from a half to a third when a "
        "history appeared. This file implements each method as the method, over ONE governed "
        "cohort with a declared population, period, feature schema and model version: one forest "
        "per cohort; a midrank adverse-tail empirical percentile in exact rational arithmetic "
        "with the governed orientation applied before ranking; an ordinary-least-squares slope on "
        "actual reporting times; and the continuous nearest-neighbour relationship on "
        "cohort-standardised features. NO PARAMETER IS INVENTED: there is no anomaly band, no "
        "percentile band, no slope magnitude band, no match radius and no composite weight "
        "anywhere in it, and the composite scalar is withheld under PARAMETER_PROVENANCE_BLOCKED "
        "because no governed normalisation, transformation, weight set, missingness policy or "
        "calibration objective exists for it.",
    "server/app/simulation/portfolio_health.py":
        "THE PRODUCTION DISPATCHER. A correct canonical library behind an unchanged route is a "
        "failed remediation -- Run 30 proved that at cost -- so this file is what makes the layer "
        "above operational. It assembles the governed cohort from the signal inputs the platform "
        "already stores per project, which is where `project_data.apply_to_signal_inputs` put "
        "the four governed portfolio structures, and hands it to the canonical layer; it performs "
        "NO arithmetic of its own. It also carries `assert_not_reachable`, which proves from the "
        "LIVE SOURCE of production's one portfolio call site that the superseded v20 "
        "implementation is not reachable -- that implementation is PRESERVED, because Runs 2, 6, "
        "13, 14, 15, 17 and 20 recorded findings about it and deleting it would delete the "
        "subject of those findings.",
}
