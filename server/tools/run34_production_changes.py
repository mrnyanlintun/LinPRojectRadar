"""
RUN 34. THE PRODUCTION FILES THIS RUN CHANGED, DECLARED.

Run 34 CREATED no production file. It changed three, all of them already declared by earlier
runs' manifests, so no path appears in two manifests: the changes are declared here for the
record and the new-file list is deliberately empty.

WHAT CHANGED, AND WHY EACH IS A BEHAVIOUR CHANGE RATHER THAN AN EDIT:

  canonical_v8.py      the parameter registry with its seven provenance classes; the section-6B
                       cohort-size policy (n<3 NOT_ESTIMABLE, 3<=n<10 continuous with an explicit
                       small-cohort limitation and no authoritative flag); TWO_SIDED added to the
                       orientation vocabulary and ranked on distance from the cohort centre; the
                       PH.2 composite WITHHELD absent governed weights, with the per-feature
                       percentile profile returned in its place; PH.3's FLAT renamed STABLE and
                       NOT_ESTIMABLE below three observations, with equal spacing reported rather
                       than assumed; and the governed portfolioCalibrationRecord.
  portfolio_health.py  the calibration-record intake, carried on the cohort anchor rather than on
                       each member, so one project cannot change the weighting the whole cohort
                       is read under.
  models.py            the stamp advances to sim-2026.08-v22, because the three behaviour changes
                       above are observable on identical portfolio inputs.

NO PRODUCTION FILE WAS CREATED, and no parameter value was tuned into production: the tree count
remains the published default of 100.
"""

from __future__ import annotations

RUN34_NEW_PRODUCTION_FILES: dict[str, str] = {}

RUN34_CHANGED_PRODUCTION_FILES: tuple[str, ...] = (
    "server/app/simulation/canonical_v8.py",
    "server/app/simulation/portfolio_health.py",
    "server/app/simulation/models.py",
)
