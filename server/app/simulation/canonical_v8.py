"""
THE CANONICAL PORTFOLIO HEALTH LAYER, v21 (Run 33). PH.1 to PH.5 = D1.1 to D1.5.

WHAT THIS REPLACES, and every one of these was real production behaviour at v20 in
`portfolio.py`:

  PH.1  Isolation Forest            a GENUINE pure-Python isolation forest (Run 15) -- but fitted
                                    ONCE PER SCORED PROJECT, on the other projects, so the four
                                    scores a three-project portfolio produced came from three
                                    DIFFERENT forests and were displayed side by side as one
                                    scale. Section 6's operational rule forbids exactly that.
                                    Bands Green/Yellow/Amber/Red were hung off the frozen
                                    synthetic threshold as though it were a project-status band.
  PH.2  Portfolio Outlier           `sum(v <= x)/n` on cpi and spi only: a "less than or equal"
                                    rank, NOT a midrank, so ties were not shared; four status
                                    colours on uncalibrated percentile cut points 0.15/0.30/0.45.
  PH.3  Trajectory Classifier       endpoint difference over (count - 1) on the LAST THREE cpi
                                    values, using LIST POSITION as time; four status bands on
                                    uncalibrated slope magnitudes 0.01/-0.01/-0.03.
  PH.4  Cross-Project Pattern       a fixed 0.15 euclidean radius over the first three RAW
                                    features (unstandardised, mixed units), then a status ladder
                                    on the matched cluster's mean cost index.
  PH.5  Anomaly Score               mean of `relative_distance` (the RETIRED Mahalanobis proxy,
                                    kept alive solely to feed this) and `1 - composite_rank`
                                    (PH.2's own output re-used as an independent term), plus a
                                    trend term when history existed -- so the effective weights
                                    changed silently from 1/2 to 1/3 when a history appeared, and
                                    PH.1 and PH.2 were counted as independent corroboration when
                                    the first term was not PH.1 at all.

THE GOVERNING FLOW (section 4 of the Run-33 contract):

    QUALIFIED PROJECT EVIDENCE -> GOVERNED PORTFOLIO COHORT -> GOVERNED FEATURE SCHEMA
    -> PER-PROJECT FEATURE RECORDS / SIGNAL HISTORIES -> ONE FITTED MODEL PER COHORT
    -> CONTINUOUS PORTFOLIO READINGS -> HUMAN REVIEW.

ONE SHARED STRUCTURE, NOT FIVE. All five modules read the SAME governed cohort and the SAME
feature schema. Section 4 forbids five incompatible inputs, and the reason is not tidiness: a
score produced under one feature schema and a score produced under another are not on one scale,
and the v20 portfolio view put five such readings in one card.

PORTFOLIO HEALTH CREATES NO PROJECT EVIDENCE. It is programme-context, exploratory, inform-only
and non-voting. Nothing here returns a `status_color`; nothing here enters fusion, Project
Status, TCPI, VAC or the vote; `NON_VOTING` and `CREATES_PROJECT_EVIDENCE` are named constants so
a guard asserts against a contract rather than against a repetition of a sentence.

NO PARAMETER IS INVENTED (section 14). There is no PH.1 anomaly band, no PH.2 percentile band, no
PH.3 slope magnitude band, no PH.4 match radius and no PH.5 weight anywhere in this file. Where
the canonical method requires a number that no owner has supplied, the module reports the
continuous quantity and stops, or abstains and says owner policy is required. PH.5 in particular
returns `score = None` under `PARAMETER_PROVENANCE_BLOCKED`: a composite with no governed
normalisation, transformation, weights or missingness policy is not a measurement.

THE 1e-12 IN PH.3 IS NUMERICAL ZERO HANDLING, NOT AN OPERATIONAL THRESHOLD. It separates a slope
that is exactly zero in exact arithmetic from one that is zero only to floating point. No
magnitude of adverse slope is treated as more or less serious than another anywhere here.
"""

from __future__ import annotations

import datetime as _dt
import math
from fractions import Fraction
from typing import Any, Mapping, Sequence

from .canonical import StructureAbsent
from .qualified_evidence import ELIGIBLE_STATES, UNASSESSED

# ---------------------------------------------------------------------------------------------
# GOVERNED VOCABULARY
# ---------------------------------------------------------------------------------------------

#: The governed structure key each Portfolio Health module reads first. The supplementary keys
#: below complete the cohort; they are listed separately because `V8_STRUCTURE_KEYS` is a
#: module -> primary-structure map like every other canonical layer's, not the intake vocabulary.
V8_STRUCTURE_KEYS: dict[str, str] = {
    "D1.1": "portfolioCohort",
    "D1.2": "portfolioCohort",
    "D1.3": "portfolioSignalHistory",
    "D1.4": "portfolioCohort",
    "D1.5": "portfolioCohort",
}

#: The rest of the shared portfolio structure. `portfolioFeatureSchema` is the cohort's feature
#: definition; `portfolioFeatureRecord` is ONE project's row in that schema; the history is one
#: project's governed signal series.
V8_SUPPLEMENTARY_KEYS: tuple[str, ...] = (
    "portfolioFeatureSchema",
    "portfolioFeatureRecord",
    "portfolioSignalHistory",
)

V8_STRUCTURE_WORDS: dict[str, str] = {
    "D1.1": "a governed portfolio cohort: the projects being compared, the period they are "
            "compared in, the feature schema they are measured on and the model version the "
            "comparison is made under",
    "D1.2": "a governed portfolio cohort and the feature values of every project in it",
    "D1.3": "a governed signal history: a stable signal identity with at least three qualified "
            "observations at three distinct reporting dates",
    "D1.4": "a governed portfolio cohort and the feature values of every project in it",
    "D1.5": "the governed Portfolio Health constituents this profile is assembled from",
}

#: Feature orientations (section 4). NEUTRAL is not "no orientation known": it is a declared
#: statement that the feature is not risk-oriented, and PH.2 excludes it from the adverse-tail
#: ranking rather than guessing a direction.
HIGHER_IS_MORE_ADVERSE = "HIGHER_IS_MORE_ADVERSE"
LOWER_IS_MORE_ADVERSE = "LOWER_IS_MORE_ADVERSE"
NEUTRAL = "NEUTRAL"
ORIENTATIONS = (HIGHER_IS_MORE_ADVERSE, LOWER_IS_MORE_ADVERSE, NEUTRAL)

#: Governance constants. A guard asserts against these, not against prose.
NON_VOTING = True
CREATES_PROJECT_EVIDENCE = False
INFORM_ONLY = "INFORM_ONLY"
PROGRAMME_CONTEXT_EVIDENCE = "PROGRAMME_CONTEXT_EVIDENCE"
AUTHORITY_NOTE = (
    "Portfolio Health is programme-context, exploratory comparison. It is inform-only and "
    "non-voting: it does not alter TCPI, VAC, Project Status, Category-6 synthesis, Category-7 "
    "evidence fusion or any participant decision, and it is never a sole contractual or "
    "escalation trigger.")

#: Dispositions.
PARAMETER_PROVENANCE_BLOCKED = "PARAMETER_PROVENANCE_BLOCKED"
INSUFFICIENT_COHORT = "INSUFFICIENT_COHORT"
OWNER_POLICY = "OWNER_POLICY"

#: Section 7: n < 3 is an explicit insufficient-cohort state; n < 10 carries a small-sample
#: warning. Both are STRUCTURAL MINIMA supplied by the Run-33 contract, not calibrated cut points
#: on any measured quantity, and they are named here so the difference is legible.
MIN_COHORT_FOR_RANKING = 3
SMALL_SAMPLE_BELOW = 10
SMALL_SAMPLE_NOTE = (
    "Small-sample limitation: this cohort holds fewer than ten projects. Every reading below is "
    "exploratory programme context. No predictive validity is claimed and no reading may be used "
    "as a sole trigger.")


class CohortInconsistent(StructureAbsent):
    """A cohort whose members do not share one period, one schema or one model version."""


class PortfolioAbstention(StructureAbsent):
    """A Portfolio Health module that cannot compute and will not substitute anything."""


# ---------------------------------------------------------------------------------------------
# THE GOVERNED COHORT
# ---------------------------------------------------------------------------------------------

_COHORT_FIELDS = ("cohort_id", "portfolio_id", "project_ids", "period", "inclusion_rule",
                  "exclusion_rule", "feature_schema_version", "qualification_policy",
                  "model_version")

_FEATURE_FIELDS = ("feature_id", "label", "units", "orientation", "scaling_rule",
                   "missingness_rule", "source_module", "qualification_requirement")

_RECORD_FIELDS = ("project_id", "cohort_id", "period", "values", "qualification_state",
                  "feature_schema_version", "source_lineage", "source_provenance")


def _require_mapping(obj: Any, words: str) -> Mapping[str, Any]:
    if obj is None:
        raise PortfolioAbstention(
            f"Awaiting {words}. This measure is named for a method that cannot be carried out "
            f"without it, so no reading is reported and no other figure is used in its place.")
    if not isinstance(obj, Mapping):
        raise PortfolioAbstention(
            f"The information provided in place of {words} is not in a form this measure can "
            f"read, so no reading is taken from it.")
    return obj


class PortfolioFeature:
    """One governed feature: identity, units, orientation, scaling, missingness, provenance."""

    __slots__ = ("feature_id", "label", "units", "orientation", "scaling_rule",
                 "missingness_rule", "source_module", "qualification_requirement",
                 "required", "version")

    def __init__(self, raw: Mapping[str, Any], schema_version: str):
        for f in _FEATURE_FIELDS:
            if raw.get(f) in (None, ""):
                raise PortfolioAbstention(
                    f"A governed portfolio feature must declare {f}; the supplied feature "
                    f"{raw.get('feature_id')!r} does not, so nothing is ranked on it.")
        orientation = str(raw["orientation"])
        if orientation not in ORIENTATIONS:
            raise PortfolioAbstention(
                f"{orientation!r} is not a declared feature orientation. The orientation of a "
                f"portfolio feature is never inferred from its name or its sign.")
        self.feature_id = str(raw["feature_id"])
        self.label = str(raw["label"])
        self.units = str(raw["units"])
        self.orientation = orientation
        self.scaling_rule = str(raw["scaling_rule"])
        self.missingness_rule = str(raw["missingness_rule"])
        self.source_module = str(raw["source_module"])
        self.qualification_requirement = str(raw["qualification_requirement"])
        #: A feature the cohort declares REQUIRED must be present and eligible for every project
        #: or the ranking modules abstain. Absent flag means required: a feature nobody marked
        #: optional is not quietly optional.
        self.required = bool(raw.get("required", True))
        self.version = str(raw.get("version") or schema_version)

    def as_dict(self) -> dict[str, Any]:
        return {"feature_id": self.feature_id, "label": self.label, "units": self.units,
                "orientation": self.orientation, "scaling_rule": self.scaling_rule,
                "missingness_rule": self.missingness_rule, "source_module": self.source_module,
                "qualification_requirement": self.qualification_requirement,
                "required": self.required, "version": self.version}


class PortfolioCohort:
    """
    The one governed comparison population. Every Portfolio Health reading reported together
    comes from an instance of this class and carries its `cohort_id`, `feature_schema_version`
    and `model_version`, so two readings can be compared only when those three agree.
    """

    def __init__(self, cohort: Mapping[str, Any], schema: Mapping[str, Any],
                 records: Sequence[Mapping[str, Any]]):
        cohort = _require_mapping(cohort, V8_STRUCTURE_WORDS["D1.1"])
        for f in _COHORT_FIELDS:
            if cohort.get(f) in (None, "", [], {}):
                raise PortfolioAbstention(
                    f"A governed portfolio cohort must declare {f}; nothing is compared without "
                    f"it.")
        self.cohort_id = str(cohort["cohort_id"])
        self.portfolio_id = str(cohort["portfolio_id"])
        self.period = str(cohort["period"])
        self.inclusion_rule = str(cohort["inclusion_rule"])
        self.exclusion_rule = str(cohort["exclusion_rule"])
        self.feature_schema_version = str(cohort["feature_schema_version"])
        self.qualification_policy = str(cohort["qualification_policy"])
        self.model_version = str(cohort["model_version"])
        declared = cohort["project_ids"]
        if not isinstance(declared, (list, tuple)) or not declared:
            raise PortfolioAbstention(
                "A governed portfolio cohort must name the projects it compares.")
        self.declared_project_ids = tuple(str(p) for p in declared)
        if len(set(self.declared_project_ids)) != len(self.declared_project_ids):
            raise CohortInconsistent(
                "The cohort names the same project more than once. A project duplicated in its "
                "own comparison population partly sets its own normal.")

        schema = _require_mapping(schema, "a governed portfolio feature schema")
        schema_version = str(schema.get("version") or "")
        if not schema_version:
            raise PortfolioAbstention("A governed portfolio feature schema must declare its "
                                      "version.")
        if schema_version != self.feature_schema_version:
            raise CohortInconsistent(
                f"The cohort is declared on feature schema {self.feature_schema_version!r} and "
                f"the supplied schema is {schema_version!r}. Scores produced under different "
                f"feature schemas are not on one scale and are not compared here.")
        raw_features = schema.get("features")
        if not isinstance(raw_features, (list, tuple)) or not raw_features:
            raise PortfolioAbstention("A governed portfolio feature schema must define at least "
                                      "one feature.")
        self.schema_version = schema_version
        self.features = tuple(PortfolioFeature(f, schema_version) for f in raw_features)
        ids = [f.feature_id for f in self.features]
        if len(set(ids)) != len(ids):
            raise CohortInconsistent("The feature schema declares the same feature twice.")
        self.feature_ids = tuple(ids)

        # -- the members ------------------------------------------------------------------------
        self.members: list[dict[str, Any]] = []
        self.excluded: list[dict[str, Any]] = []
        seen: set[str] = set()
        for raw in records:
            raw = _require_mapping(raw, "a governed portfolio feature record")
            for f in _RECORD_FIELDS:
                if f not in raw or raw.get(f) in (None, ""):
                    raise PortfolioAbstention(
                        f"A governed portfolio feature record must declare {f}; the record for "
                        f"{raw.get('project_id')!r} does not.")
            pid = str(raw["project_id"])
            if pid in seen:
                raise CohortInconsistent(
                    f"Project {pid!r} appears twice in the cohort. Section 13 forbids a target "
                    f"duplicated in its own comparison population.")
            seen.add(pid)
            if pid not in self.declared_project_ids:
                raise CohortInconsistent(
                    f"Project {pid!r} supplied a feature record but is not a declared member of "
                    f"cohort {self.cohort_id!r}.")
            if str(raw["cohort_id"]) != self.cohort_id:
                raise CohortInconsistent(
                    f"Project {pid!r} carries cohort {raw['cohort_id']!r}, not {self.cohort_id!r}.")
            if str(raw["period"]) != self.period:
                raise CohortInconsistent(
                    f"Project {pid!r} reports period {raw['period']!r} and the cohort period is "
                    f"{self.period!r}. Mixed reporting periods are rejected: a comparison across "
                    f"periods is not a comparison of a portfolio at a moment.")
            if str(raw["feature_schema_version"]) != self.schema_version:
                raise CohortInconsistent(
                    f"Project {pid!r} reports feature schema {raw['feature_schema_version']!r} "
                    f"and the cohort schema is {self.schema_version!r}. Mixed feature schemas "
                    f"are rejected.")
            state = str(raw["qualification_state"])
            member = {
                "project_id": pid,
                "qualification_state": state,
                "values": dict(raw.get("values") or {}),
                "missing_fields": tuple(str(x) for x in (raw.get("missing_fields") or ())),
                "invalid_fields": tuple(str(x) for x in (raw.get("invalid_fields") or ())),
                "source_lineage": raw["source_lineage"],
                "source_provenance": raw["source_provenance"],
            }
            if state not in ELIGIBLE_STATES:
                member["ineligible_reason"] = (
                    "Category-9 qualification state "
                    f"{state!r} does not permit analytical use."
                    + (" Unassessed evidence is not eligible and is never converted to "
                       "qualified." if state == UNASSESSED else ""))
                self.excluded.append(member)
                continue
            self.members.append(member)
        self.members.sort(key=lambda m: m["project_id"])
        self.excluded.sort(key=lambda m: m["project_id"])
        self.project_ids = tuple(m["project_id"] for m in self.members)
        self.missing_members = tuple(sorted(set(self.declared_project_ids)
                                            - set(self.project_ids)
                                            - {m["project_id"] for m in self.excluded}))

    # -- feature access -------------------------------------------------------------------------

    def value(self, member: Mapping[str, Any], feature: PortfolioFeature) -> float | None:
        """
        The project's value for one feature, or None. A MISSING VALUE IS NEVER ZERO: absence is
        returned as absence and every consumer decides explicitly what to do with it.
        """
        if feature.feature_id in member["missing_fields"]:
            return None
        if feature.feature_id in member["invalid_fields"]:
            return None
        v = member["values"].get(feature.feature_id)
        if v is None or isinstance(v, bool):
            return None
        try:
            f = float(v)
        except (TypeError, ValueError):
            return None
        if math.isnan(f) or math.isinf(f):
            return None
        return f

    def required_features(self) -> tuple[PortfolioFeature, ...]:
        return tuple(f for f in self.features if f.required)

    def missing_required(self) -> list[str]:
        """Every (project, feature) pair a required feature is absent or ineligible for."""
        out = []
        for m in self.members:
            for f in self.required_features():
                if self.value(m, f) is None:
                    out.append(f"{m['project_id']}:{f.feature_id}")
        return sorted(out)

    def identity(self) -> dict[str, Any]:
        return {
            "cohort_id": self.cohort_id,
            "portfolio_id": self.portfolio_id,
            "period": self.period,
            "feature_schema_version": self.schema_version,
            "model_version": self.model_version,
            "qualification_policy": self.qualification_policy,
            "inclusion_rule": self.inclusion_rule,
            "exclusion_rule": self.exclusion_rule,
            "declared_project_ids": list(self.declared_project_ids),
            "eligible_project_ids": list(self.project_ids),
            "excluded_project_ids": [m["project_id"] for m in self.excluded],
            "excluded_reasons": {m["project_id"]: m["ineligible_reason"] for m in self.excluded},
            "missing_member_records": list(self.missing_members),
            "cohort_size": len(self.project_ids),
            "features": [f.as_dict() for f in self.features],
        }

    def limitation(self) -> dict[str, Any]:
        n = len(self.project_ids)
        return {
            "cohort_size": n,
            "small_sample": n < SMALL_SAMPLE_BELOW,
            "small_sample_note": SMALL_SAMPLE_NOTE if n < SMALL_SAMPLE_BELOW else None,
            "predictive_validity_claimed": False,
        }


def _envelope(module_id: str, method: str, cohort: PortfolioCohort) -> dict[str, Any]:
    """The fields EVERY Portfolio Health reading carries, whether it computes or abstains."""
    return {
        "module_id": module_id,
        "method_class": method,
        "evidence_class": PROGRAMME_CONTEXT_EVIDENCE,
        "use": INFORM_ONLY,
        "voting": False,
        "creates_project_evidence": False,
        "authority_note": AUTHORITY_NOTE,
        "cohort": cohort.identity(),
        "limitation": cohort.limitation(),
        "calibration_pending": True,
        "empirical_validation_pending": True,
    }


def abstain(module_id: str, method: str, cohort: PortfolioCohort | None, reason: str,
            disposition: str = "STRUCTURE_ABSENT") -> dict[str, Any]:
    body = (_envelope(module_id, method, cohort) if cohort is not None else {
        "module_id": module_id, "method_class": method,
        "evidence_class": PROGRAMME_CONTEXT_EVIDENCE, "use": INFORM_ONLY,
        "voting": False, "creates_project_evidence": False,
        "authority_note": AUTHORITY_NOTE,
        "calibration_pending": True, "empirical_validation_pending": True})
    body.update({"abstained": True, "disposition": disposition, "abstention_reason": reason,
                 "projects": {}})
    return body


# ---------------------------------------------------------------------------------------------
# PH.1  ISOLATION FOREST  (D1.1)
# ---------------------------------------------------------------------------------------------
#
# CANONICAL SOURCE. Liu, Ting and Zhou, "Isolation Forest", ICDM 2008, doi:10.1109/ICDM.2008.17.
# The algorithm itself is unchanged from Run 15 and lives in `isolation_forest.py`: random
# attribute, random split between the observed minimum and maximum, height limit ceil(log2 psi),
# external node retains its sample size, path length = depth + c(size), c(n) = 2H(n-1) - 2(n-1)/n,
# s(x, psi) = 2 ** (-E(h(x)) / c(psi)). Run 33 VERIFIED that construction by execution rather
# than by reading the Run-15 report, and it holds.
#
# WHAT RUN 33 CHANGES IS THE OPERATIONAL RULE, WHICH IS SECTION 6'S OWN. v20 fitted a NEW forest
# for every project, on the OTHER projects. That was adopted in Run 15 for a good reason -- a
# project must not set its own normal -- but its consequence is that the scores shown together in
# one portfolio card came from different forests, trained on different populations, normalised by
# different c(psi). Section 6: "Fit one governed forest per portfolio cohort/model version. Do
# not fit a different forest for every project and compare those scores. Every project score
# reported together must come from the same fitted forest." So ONE forest is fitted on the whole
# eligible cohort and every member is scored by it. The self-inclusion the Run-15 note worried
# about is a property the published algorithm already has -- iForest scores its own training set
# and that is the standard use -- and it is now recorded in the model metadata as
# `fitted_project_population` rather than avoided by producing incomparable scores.

IF_TREES = 100
IF_SUBSAMPLE = 256
IF_SEED = 20250815

#: The Run-15 frozen synthetic threshold, VERIFIED not retuned. It is carried here as an
#: ARTEFACT REFERENCE, never as a band: section 6 requires that if it is exposed operationally it
#: is labelled a synthetic/laboratory threshold, an exploratory flag, not a project-status band
#: and not a sole trigger. It was selected on a seeded synthetic population under the four-feature
#: Run-15 vector and it does not travel to another feature schema, so `exploratory_flag` is
#: reported as None under any other schema rather than computed on a scale it was not fitted to.
RUN15_FROZEN_THRESHOLD = 0.576
RUN15_FROZEN_SCHEMA = "run15-synthetic-4feature-v1"
RUN15_THRESHOLD_LABELS = {
    "threshold_basis": "SYNTHETIC_LABORATORY",
    "is_project_status_band": False,
    "is_sole_trigger": False,
    "field_validated": False,
    "artifact": "code_audit/run15_isolation_forest_validation.csv",
    "note": "Synthetic/laboratory threshold, frozen at Run 15 on seeded synthetic populations "
            "and evaluated once on a synthetic holdout. It is an exploratory flag only. It is "
            "not a project-status band, it is not a sole trigger, and no field validation is "
            "claimed for it.",
}


def isolation_forest(cohort: PortfolioCohort, *, n_trees: int = IF_TREES,
                     subsample: int = IF_SUBSAMPLE, seed: int = IF_SEED) -> dict[str, Any]:
    from .isolation_forest import IsolationForest

    out = _envelope("D1.1", "Isolation_Forest", cohort)
    feats = [f for f in cohort.features if f.required]
    if not feats:
        return abstain("D1.1", "Isolation_Forest", cohort,
                       "The feature schema declares no required feature to isolate on.")
    missing = cohort.missing_required()
    if missing:
        return abstain("D1.1", "Isolation_Forest", cohort,
                       "A required governed feature is absent or ineligible for "
                       f"{len(missing)} project-feature pair(s) ({', '.join(missing)}). A "
                       "missing feature is not replaced by zero, by a cohort mean or by any "
                       "other stand-in, so no forest is grown.")
    if len(cohort.project_ids) < 2:
        return abstain("D1.1", "Isolation_Forest", cohort,
                       "An isolation forest needs at least two observations to grow a tree on. "
                       "A cohort of fewer than two eligible projects produces no authoritative "
                       "anomaly reading of any kind.", INSUFFICIENT_COHORT)

    order = [f.feature_id for f in feats]
    vectors = [[cohort.value(m, f) for f in feats] for m in cohort.members]
    forest = IsolationForest(vectors, n_trees=n_trees,
                             subsample=min(subsample, len(vectors)), seed=seed)
    projects: dict[str, Any] = {}
    for m, v in zip(cohort.members, vectors):
        score = forest.anomaly_score(v)
        projects[m["project_id"]] = {
            "anomaly_score": score,
            "mean_path_length": forest.mean_path_length(v),
            "source_lineage": m["source_lineage"],
            "source_provenance": m["source_provenance"],
            "qualification_state": m["qualification_state"],
            # The frozen threshold travels only with the schema it was fitted on.
            "exploratory_flag": (
                bool(score >= RUN15_FROZEN_THRESHOLD)
                if cohort.schema_version == RUN15_FROZEN_SCHEMA else None),
            "exploratory_flag_reason": (
                None if cohort.schema_version == RUN15_FROZEN_SCHEMA else
                "The frozen synthetic threshold was fitted on feature schema "
                f"{RUN15_FROZEN_SCHEMA!r}; this cohort is on {cohort.schema_version!r}, so no "
                "flag is derived from it."),
        }
    out.update({
        "abstained": False,
        "disposition": "COMPUTED",
        "projects": projects,
        "model": {
            "cohort_id": cohort.cohort_id,
            "feature_schema_version": cohort.schema_version,
            "feature_order": order,
            "subsample_psi": forest.subsample,
            "n_trees": forest.n_trees,
            "height_limit": forest.height_limit,
            "seed": forest.seed,
            "normaliser_c_psi": forest.normaliser,
            "preprocessing_version": cohort.schema_version,
            "model_version": cohort.model_version,
            "fitted_project_population": list(cohort.project_ids),
            "one_forest_per_cohort": True,
            "harmonic_number_form": "PAPER_ESTIMATE_LN_PLUS_EULER_GAMMA",
        },
        "frozen_synthetic_threshold": RUN15_FROZEN_THRESHOLD,
        "frozen_synthetic_threshold_labels": dict(RUN15_THRESHOLD_LABELS),
        "higher_score_is_more_anomalous": True,
    })
    return out


# ---------------------------------------------------------------------------------------------
# PH.2  PORTFOLIO OUTLIER DETECTION  (D1.2)
# ---------------------------------------------------------------------------------------------
#
# NOT A LEARNED MODEL (section 7). A transparent adverse-tail empirical percentile, computed in
# EXACT RATIONAL ARITHMETIC and converted to float only at the boundary, so the oracle midranks
# on [1, 2, 3, 10] are exactly 1/8, 3/8, 5/8, 7/8 rather than nearly so.
#
#     r_ij = (#{cohort values strictly LESS ADVERSE than x_ij} + 0.5 * #{equal}) / n
#
# after the governed orientation is applied. That is a MIDRANK percentile: tied projects receive
# the same value, which the v20 `<=` rank did not give them.
#
# THE COMPOSITE IS AN OWNER-POLICY DESIGN, NOT A CALIBRATED CONSTANT. The mean over the complete
# governed required risk-oriented feature set weights every feature equally. That is a transparent
# v21 design decision recorded as OWNER_POLICY and handed to Run 34/35; it is not an empirically
# calibrated scientific constant and this file does not pretend otherwise.

METHOD_CLASS_NOTE_D12 = (
    "Descriptive empirical percentile over the governed cohort. This is not a learned machine "
    "learning model: nothing is trained, nothing is fitted and no parameter is estimated from "
    "data. It is not a probability of failure.")


def _midrank(values: Sequence[Fraction], x: Fraction) -> Fraction:
    less = sum(1 for v in values if v < x)
    equal = sum(1 for v in values if v == x)
    return (Fraction(less) + Fraction(equal, 2)) / Fraction(len(values))


def portfolio_outlier(cohort: PortfolioCohort) -> dict[str, Any]:
    out = _envelope("D1.2", "Portfolio_Outlier", cohort)
    feats = [f for f in cohort.required_features() if f.orientation != NEUTRAL]
    if not feats:
        return abstain("D1.2", "Portfolio_Outlier", cohort,
                       "The feature schema declares no required risk-oriented feature. A "
                       "neutral feature has no adverse tail and none is invented for it.")
    n = len(cohort.project_ids)
    if n < MIN_COHORT_FOR_RANKING:
        return abstain("D1.2", "Portfolio_Outlier", cohort,
                       f"A cohort of {n} eligible project(s) is below the governed minimum of "
                       f"{MIN_COHORT_FOR_RANKING} for a portfolio percentile. No rank is "
                       "reported.", INSUFFICIENT_COHORT)
    missing = [f"{m['project_id']}:{f.feature_id}" for m in cohort.members for f in feats
               if cohort.value(m, f) is None]
    if missing:
        return abstain("D1.2", "Portfolio_Outlier", cohort,
                       "A required governed feature is absent or ineligible for "
                       f"{len(missing)} project-feature pair(s) ({', '.join(missing)}). The "
                       "feature is NOT dropped and the remaining features are NOT renormalised: "
                       "this measure abstains.")

    per_feature: dict[str, dict[str, Fraction]] = {}
    for f in feats:
        # THE ORIENTATION IS APPLIED BEFORE RANKING, never after and never by reversing the
        # finished rank. A lower-is-more-adverse feature is negated so that "greater" means
        # "more adverse" for every feature alike; the percentile is then the adverse tail
        # position on one consistent convention.
        sign = -1 if f.orientation == LOWER_IS_MORE_ADVERSE else 1
        vals = {m["project_id"]: sign * Fraction(str(cohort.value(m, f)))
                for m in cohort.members}
        pool = list(vals.values())
        per_feature[f.feature_id] = {pid: _midrank(pool, x) for pid, x in vals.items()}

    projects: dict[str, Any] = {}
    for m in cohort.members:
        pid = m["project_id"]
        ranks = {fid: per_feature[fid][pid] for fid in per_feature}
        composite = sum(ranks.values(), Fraction(0)) / Fraction(len(ranks))
        projects[pid] = {
            "feature_percentiles": {k: float(v) for k, v in sorted(ranks.items())},
            "feature_percentiles_exact": {k: f"{v.numerator}/{v.denominator}"
                                          for k, v in sorted(ranks.items())},
            "portfolio_outlier_percentile": float(composite),
            "portfolio_outlier_percentile_exact": f"{composite.numerator}/{composite.denominator}",
            "source_lineage": m["source_lineage"],
            "source_provenance": m["source_provenance"],
            "qualification_state": m["qualification_state"],
        }
    ordered = sorted(projects, key=lambda p: (-projects[p]["portfolio_outlier_percentile"], p))
    out.update({
        "abstained": False, "disposition": "COMPUTED", "projects": projects,
        "method_note": METHOD_CLASS_NOTE_D12,
        "is_learned_model": False,
        "is_probability_of_failure": False,
        "ranking_rule": "MIDRANK_ADVERSE_TAIL_EMPIRICAL_PERCENTILE",
        "composite_rule": "MEAN_OVER_COMPLETE_GOVERNED_REQUIRED_RISK_ORIENTED_FEATURE_SET",
        "composite_weighting_provenance": OWNER_POLICY,
        "composite_weighting_note": (
            "Equal weighting over the complete governed required risk-oriented feature set is a "
            "transparent v21 owner-policy design, not an empirically calibrated scientific "
            "constant. Final calibration and value assessment are Run-34/35 work."),
        "features_ranked": [f.feature_id for f in feats],
        "most_adverse_project_ids": ordered[:1],
        "adverse_order": ordered,
    })
    return out


# ---------------------------------------------------------------------------------------------
# PH.3  SIGNAL TRAJECTORY CLASSIFIER  (D1.3)
# ---------------------------------------------------------------------------------------------
#
# NOT A TRAINED CLASSIFIER (section 8). A deterministic ordinary-least-squares time trend, in
# exact rational arithmetic:
#
#     b = SUM (t_i - mean t)(x_i - mean x) / SUM (t_i - mean t)^2
#
# ACTUAL REPORTING TIME, NOT LIST POSITION. v20 divided the endpoint difference of the last three
# cost-index values by (count - 1) and called it a slope per period, which is the correct answer
# only when the observations are equally spaced and only for a two-point fit. Irregular reporting
# intervals now enter the fit as they actually are.
#
# ORIENTATION MULTIPLIER q: +1 when higher is more adverse, -1 when lower is more adverse.
# AdverseSlope a = q * b. a > 0 DETERIORATING, a < 0 IMPROVING, |a| <= 1e-12 FLAT.
#
# THE 1e-12 IS NUMERICAL ZERO HANDLING. There is no magnitude band anywhere here: a slope is not
# graded, and no Green/Yellow/Amber/Red ladder exists on it.

DETERIORATING = "DETERIORATING"
IMPROVING = "IMPROVING"
FLAT = "FLAT"
NUMERICAL_ZERO = Fraction(1, 10 ** 12)

MIN_TRAJECTORY_OBSERVATIONS = 3


def _as_days(value: Any) -> Fraction:
    """A reporting time as a number of days. An ISO date, an ISO datetime or a number."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return Fraction(str(value))
    s = str(value).strip()
    for parse in (lambda t: _dt.date.fromisoformat(t),
                  lambda t: _dt.datetime.fromisoformat(t).date()):
        try:
            d = parse(s)
        except ValueError:
            continue
        return Fraction((d - _dt.date(1970, 1, 1)).days)
    try:
        return Fraction(s)
    except (ValueError, ZeroDivisionError):
        raise PortfolioAbstention(
            f"{value!r} is not a reporting time this measure can read. List position is never "
            f"used as time when actual reporting dates are required.") from None


def ols_slope(times: Sequence[Fraction], values: Sequence[Fraction]) -> Fraction:
    n = Fraction(len(times))
    tbar = sum(times, Fraction(0)) / n
    xbar = sum(values, Fraction(0)) / n
    num = sum(((t - tbar) * (x - xbar) for t, x in zip(times, values)), Fraction(0))
    den = sum(((t - tbar) ** 2 for t in times), Fraction(0))
    if den == 0:
        raise PortfolioAbstention(
            "Every observation carries the same reporting time, so no slope in time is defined.")
    return num / den


def _one_history(entry: Mapping[str, Any], cohort: PortfolioCohort | None) -> dict[str, Any]:
    """One project/signal trajectory. Returns a result body without the shared envelope."""
    required = ("project_id", "signal_id", "units", "orientation", "source",
                "history_version", "observations")
    for f in required:
        if entry.get(f) in (None, "", [], {}):
            raise PortfolioAbstention(
                f"A governed signal history must declare {f}; nothing is classified without it.")
    orientation = str(entry["orientation"])
    if orientation not in ORIENTATIONS:
        raise PortfolioAbstention(
            f"{orientation!r} is not a declared feature orientation. A trajectory is never "
            "classified adverse or favourable on an orientation nobody declared.")
    if orientation == NEUTRAL:
        raise PortfolioAbstention(
            "A neutral, non-risk-oriented signal has no adverse direction, so its slope is "
            "reported without a classification rather than being given one.")
    signal_id = str(entry["signal_id"])
    obs = entry["observations"]
    if not isinstance(obs, (list, tuple)):
        raise PortfolioAbstention("A governed signal history must carry a list of observations.")

    times: list[Fraction] = []
    values: list[Fraction] = []
    for o in obs:
        if not isinstance(o, Mapping):
            raise PortfolioAbstention("Every observation must be a governed record.")
        if str(o.get("signal_id", signal_id)) != signal_id:
            raise PortfolioAbstention(
                f"An observation carries signal identity {o.get('signal_id')!r} inside the "
                f"history of {signal_id!r}. Two different signals are never fitted as one "
                "trajectory.")
        state = str(o.get("qualification_state", UNASSESSED))
        if state not in ELIGIBLE_STATES:
            raise PortfolioAbstention(
                f"An observation of {signal_id!r} carries qualification state {state!r}, which "
                "does not permit analytical use. The observation is not dropped and the "
                "remaining points are not fitted as though the series were complete.")
        if o.get("reporting_time") in (None, ""):
            raise PortfolioAbstention(
                f"An observation of {signal_id!r} carries no reporting time. List position is "
                "never used as time.")
        v = o.get("value")
        if v is None or isinstance(v, bool):
            raise PortfolioAbstention(
                f"An observation of {signal_id!r} carries no value. A missing observation is "
                "never read as zero.")
        times.append(_as_days(o["reporting_time"]))
        values.append(Fraction(str(v)))

    if len(times) < MIN_TRAJECTORY_OBSERVATIONS:
        raise PortfolioAbstention(
            f"{len(times)} observation(s) of {signal_id!r}; at least "
            f"{MIN_TRAJECTORY_OBSERVATIONS} are required before a trend is fitted.")
    if len(set(times)) < MIN_TRAJECTORY_OBSERVATIONS:
        raise PortfolioAbstention(
            f"The history of {signal_id!r} holds {len(set(times))} distinct reporting time(s); "
            f"at least {MIN_TRAJECTORY_OBSERVATIONS} are required. Duplicate timestamps are not "
            "silently spread across the interval.")

    # Input order is irrelevant to an OLS fit; sorting is for the reported series only.
    pairs = sorted(zip(times, values))
    b = ols_slope([t for t, _ in pairs], [x for _, x in pairs])
    q = 1 if orientation == HIGHER_IS_MORE_ADVERSE else -1
    a = q * b
    if abs(a) <= NUMERICAL_ZERO:
        classification = FLAT
    elif a > 0:
        classification = DETERIORATING
    else:
        classification = IMPROVING
    return {
        "project_id": str(entry["project_id"]),
        "signal_id": signal_id,
        "units": str(entry["units"]),
        "orientation": orientation,
        "orientation_multiplier_q": q,
        "source": str(entry["source"]),
        "history_version": str(entry["history_version"]),
        "observations_used": len(times),
        "distinct_reporting_times": len(set(times)),
        "time_units": "days",
        "ols_slope_per_day": float(b),
        "ols_slope_exact": f"{b.numerator}/{b.denominator}",
        "adverse_slope_per_day": float(a),
        "adverse_slope_exact": f"{a.numerator}/{a.denominator}",
        "classification": classification,
        "magnitude_band": None,
        "numerical_zero_handling": "1e-12; this is floating-point zero handling and is not an "
                                   "operational threshold.",
        "is_trained_classifier": False,
    }


def trajectory_classifier(histories: Sequence[Mapping[str, Any]],
                          cohort: PortfolioCohort) -> dict[str, Any]:
    out = _envelope("D1.3", "Trajectory_Classifier", cohort)
    if not histories:
        return abstain("D1.3", "Trajectory_Classifier", cohort,
                       "No governed signal history was supplied for any project in this cohort, "
                       "so no trajectory is fitted.")
    trajectories: dict[str, list[dict[str, Any]]] = {}
    abstentions: dict[str, list[dict[str, str]]] = {}
    for entry in histories:
        pid = str((entry or {}).get("project_id", "?"))
        try:
            body = _one_history(entry, cohort)
        except PortfolioAbstention as exc:
            abstentions.setdefault(pid, []).append(
                {"signal_id": str((entry or {}).get("signal_id", "?")), "reason": str(exc)})
            continue
        trajectories.setdefault(body["project_id"], []).append(body)
    for v in trajectories.values():
        v.sort(key=lambda b: b["signal_id"])
    if not trajectories:
        body = abstain("D1.3", "Trajectory_Classifier", cohort,
                       "Every supplied signal history was refused; no trajectory is fitted.")
        body["signal_abstentions"] = abstentions
        return body
    out.update({"abstained": False, "disposition": "COMPUTED", "projects": trajectories,
                "signal_abstentions": abstentions,
                "method": "ORDINARY_LEAST_SQUARES_TIME_TREND",
                "is_trained_classifier": False,
                "status_bands": None})
    return out


# ---------------------------------------------------------------------------------------------
# PH.4  CROSS-PROJECT PATTERN DETECTOR  (D1.4)
# ---------------------------------------------------------------------------------------------
#
# NOT A TRAINED CLUSTERING MODEL (section 9). A nearest-neighbour relationship over the governed
# cohort, standardised on the cohort's own moments:
#
#     z_ij = (x_ij - mean_j) / sd_j        zero-variance features EXCLUDED and RECORDED
#     d(i,k) = sqrt( SUM_j (z_ij - z_kj)^2 / p )     p = usable features
#     sim(i,k) = 1 / (1 + d(i,k))
#
# THE 0.15 MATCH RADIUS IS GONE AND NOTHING REPLACES IT. v20 declared a project "similar" inside
# a fixed euclidean radius of 0.15 over three RAW features of mixed units, then read a status
# ladder off the matched cluster's mean cost index -- so a cluster of healthy peers produced a
# status. Section 9 forbids both: the radius was never validated, no new threshold may be
# invented, and matching a healthy peer must not imply adverse status. Run 33 reports the
# CONTINUOUS relationship; Run 34 owns any threshold that is still wanted.
#
# TIE RULE, DECLARED: all tied nearest neighbours are returned, in ascending project-id order.

TIE_RULE = "ALL_TIED_NEIGHBOURS_IN_ASCENDING_PROJECT_ID_ORDER"


def _population_sd(values: Sequence[float]) -> float:
    n = len(values)
    mean = sum(values) / n
    return math.sqrt(sum((v - mean) ** 2 for v in values) / n)


def cross_project_pattern(cohort: PortfolioCohort) -> dict[str, Any]:
    out = _envelope("D1.4", "Cross_Project_Pattern", cohort)
    feats = list(cohort.required_features())
    if not feats:
        return abstain("D1.4", "Cross_Project_Pattern", cohort,
                       "The feature schema declares no required feature to compare projects on.")
    missing = cohort.missing_required()
    if missing:
        return abstain("D1.4", "Cross_Project_Pattern", cohort,
                       "A required governed feature is absent or ineligible for "
                       f"{len(missing)} project-feature pair(s) ({', '.join(missing)}). No "
                       "stand-in value is substituted, so no distance is computed.")
    n = len(cohort.project_ids)
    if n < 2:
        return abstain("D1.4", "Cross_Project_Pattern", cohort,
                       f"A cohort of {n} eligible project(s) has no peer to compare against.",
                       INSUFFICIENT_COHORT)

    usable: list[PortfolioFeature] = []
    excluded: list[dict[str, str]] = []
    columns: dict[str, list[float]] = {}
    for f in feats:
        col = [cohort.value(m, f) for m in cohort.members]
        sd = _population_sd(col)
        if sd == 0.0:
            excluded.append({"feature_id": f.feature_id,
                             "reason": "ZERO_VARIANCE_NON_INFORMATIVE"})
            continue
        usable.append(f)
        mean = sum(col) / len(col)
        columns[f.feature_id] = [(v - mean) / sd for v in col]
    if not usable:
        body = abstain("D1.4", "Cross_Project_Pattern", cohort,
                       "Every governed feature is zero-variance across this cohort and therefore "
                       "non-informative; no pattern is reported.")
        body["excluded_features"] = excluded
        return body

    p = len(usable)
    ids = list(cohort.project_ids)
    z = {pid: [columns[f.feature_id][i] for f in usable] for i, pid in enumerate(ids)}

    def dist(a: str, b: str) -> float:
        return math.sqrt(sum((z[a][j] - z[b][j]) ** 2 for j in range(p)) / p)

    projects: dict[str, Any] = {}
    for pid in ids:
        peers = sorted(q for q in ids if q != pid)      # SELF-MATCH EXCLUDED
        dists = {q: dist(pid, q) for q in peers}
        best = min(dists.values())
        nearest = sorted(q for q in peers if dists[q] == best)
        duplicates = sorted(q for q in peers if dists[q] == 0.0)
        member = next(m for m in cohort.members if m["project_id"] == pid)
        projects[pid] = {
            "nearest_neighbour_project_ids": nearest,
            "distance": best,
            "similarity": 1.0 / (1.0 + best),
            "all_distances": {q: dists[q] for q in peers},
            "duplicate_of": duplicates,
            "usable_features": [f.feature_id for f in usable],
            "excluded_features": list(excluded),
            "usable_feature_count": p,
            "peer_condition": {
                q: {f.feature_id: cohort.value(
                        next(m for m in cohort.members if m["project_id"] == q), f)
                    for f in usable}
                for q in nearest},
            "source_lineage": member["source_lineage"],
            "source_provenance": member["source_provenance"],
            "qualification_state": member["qualification_state"],
        }
    out.update({
        "abstained": False, "disposition": "COMPUTED", "projects": projects,
        "excluded_features": excluded,
        "usable_features": [f.feature_id for f in usable],
        "tie_rule": TIE_RULE,
        "match_threshold": None,
        "match_threshold_note": (
            "No match threshold is applied. The unvalidated 0.15 radius is retired and no "
            "replacement is invented here; Run 34 owns any threshold calibration that is still "
            "required."),
        "similarity_is_not_failure": True,
        "peer_condition_reported_separately": True,
        "is_trained_clustering_model": False,
        "self_match_excluded": True,
    })
    return out


# ---------------------------------------------------------------------------------------------
# PH.5  ANOMALY SCORE  (D1.5) -- THE PORTFOLIO ANOMALY PROFILE
# ---------------------------------------------------------------------------------------------
#
# PH.5 IS NOT NEW INDEPENDENT EVIDENCE (section 10). It is a composite of the other four, and it
# must keep their lineage rather than laundering it into one number.
#
# THE SUPERVISORY DECISION FOR RUN 33: NO SCALAR. A scalar composite needs a governed
# normalisation, governed transformations, governed weights, a governed missingness policy and a
# calibration objective. None of those exists. So `score` is None and the disposition is
# PARAMETER_PROVENANCE_BLOCKED, which is the CORRECT outcome for this run and not a failure to
# finish it. Run 34 owns the composite.
#
# WHAT IS FORBIDDEN HERE, each of which was real v20 behaviour or a real failure mode:
#   - a constant placeholder in the mean (v20 carried a literal 0.5 until Run 3);
#   - the retired Mahalanobis/distance proxy standing in for PH.1 (v20 did exactly this);
#   - `1 - composite_rank`, i.e. PH.2's own output, entering as an independent constituent;
#   - weights that change silently when a constituent is absent (v20's mean went 1/2 -> 1/3);
#   - renormalising the remaining weights after a constituent disappears;
#   - counting PH.1 and PH.2 as independent corroboration -- they read the SAME feature records;
#   - converting a missing constituent into a neutral or favourable value.

PH5_CONSTITUENTS = ("D1.1", "D1.2", "D1.3", "D1.4")
PH5_CONSTITUENT_ROLES = {
    "D1.1": "isolation_forest_anomaly_score",
    "D1.2": "descriptive_outlier_percentile",
    "D1.3": "trajectory_slope_and_classification",
    "D1.4": "nearest_neighbour_pattern_result",
}

#: PH.1 and PH.2 are computed from the SAME governed feature records under the SAME schema. They
#: are not independent observations of the project and this file says so in a field, so a reader
#: cannot take two agreeing constituents as corroboration.
PH5_INDEPENDENCE = {
    "D1.1": {"independent": False, "shares_evidence_with": ["D1.2", "D1.4"],
             "relationship": "SAME_SOURCE_TRANSFORM"},
    "D1.2": {"independent": False, "shares_evidence_with": ["D1.1", "D1.4"],
             "relationship": "SAME_SOURCE_TRANSFORM"},
    "D1.4": {"independent": False, "shares_evidence_with": ["D1.1", "D1.2"],
             "relationship": "SAME_SOURCE_TRANSFORM"},
    "D1.3": {"independent": False, "shares_evidence_with": [],
             "relationship": "SAME_SOURCE",
             "note": "The signal history is the same reporting stream the feature records are "
                     "assembled from."},
}


def anomaly_profile(cohort: PortfolioCohort, constituents: Mapping[str, Mapping[str, Any]]
                    ) -> dict[str, Any]:
    out = _envelope("D1.5", "Anomaly_Score", cohort)
    profiles: dict[str, Any] = {}
    for pid in cohort.project_ids:
        present: dict[str, Any] = {}
        missing: list[str] = []
        for mid in PH5_CONSTITUENTS:
            res = constituents.get(mid) or {}
            body = (res.get("projects") or {}).get(pid)
            if res.get("abstained") or body is None:
                missing.append(mid)
                continue
            present[mid] = {
                "role": PH5_CONSTITUENT_ROLES[mid],
                "module_id": mid,
                "model_version": (res.get("model") or {}).get("model_version",
                                                              cohort.model_version),
                "feature_schema_version": cohort.schema_version,
                "cohort_id": cohort.cohort_id,
                "period": cohort.period,
                "value": body,
                "independence": PH5_INDEPENDENCE[mid],
            }
        # DUPLICATE LINEAGE CANNOT REINFORCE. The constituents are keyed by module id, so the
        # same result offered twice occupies one slot; and `distinct_evidence_bodies` counts the
        # underlying evidence, not the number of constituents, so two transforms of one feature
        # record can never read as two supporting observations.
        bodies = sorted({(c["cohort_id"], c["feature_schema_version"], c["period"])
                         for c in present.values()})
        profiles[pid] = {
            "project_id": pid,
            "cohort_id": cohort.cohort_id,
            "period": cohort.period,
            "feature_schema_version": cohort.schema_version,
            "constituents": present,
            "constituent_ids": sorted(present),
            "missing_constituents": missing,
            "missing_constituents_are_not_neutral": True,
            "distinct_evidence_bodies": len(bodies),
            "corroboration_established": False,
            "corroboration_note": (
                "The constituents are transforms of the same governed feature records under one "
                "schema. Agreement between them is not corroboration and does not increase "
                "confidence."),
            "confidence": None,
            "score": None,
            "disposition": PARAMETER_PROVENANCE_BLOCKED,
            "score_blocked_reason": (
                "No governed normalisation, transformation, weight set, missingness policy or "
                "calibration objective exists for a Portfolio Health composite. A scalar "
                "produced without them would be a number with no provenance, so none is "
                "produced. Run 34 owns the composite."),
            "weights": None,
            "effective_weights": None,
        }
    out.update({
        "abstained": False,
        "disposition": PARAMETER_PROVENANCE_BLOCKED,
        "result_type": "PortfolioAnomalyProfile",
        "score": None,
        "weights": None,
        "projects": profiles,
        "constituent_modules": list(PH5_CONSTITUENTS),
        "constituent_roles": dict(PH5_CONSTITUENT_ROLES),
        "is_independent_evidence": False,
        "run34_owns": ["normalization", "transformations", "weights", "missingness_policy",
                       "calibration_objective"],
    })
    return out


# ---------------------------------------------------------------------------------------------
# THE ONE CANONICAL ENTRY POINT
# ---------------------------------------------------------------------------------------------

RESULT_KEYS = {
    "D1.1": "cat8_1_isolation_forest",
    "D1.2": "cat8_2_portfolio_outlier",
    "D1.3": "cat8_3_trajectory_classifier",
    "D1.4": "cat8_4_cross_project_pattern",
    "D1.5": "cat8_5_anomaly_score",
}
METHOD_CLASSES = {
    "D1.1": "Isolation_Forest", "D1.2": "Portfolio_Outlier", "D1.3": "Trajectory_Classifier",
    "D1.4": "Cross_Project_Pattern", "D1.5": "Anomaly_Score",
}


def compute_portfolio_health(cohort_structure: Mapping[str, Any] | None,
                             schema: Mapping[str, Any] | None,
                             records: Sequence[Mapping[str, Any]],
                             histories: Sequence[Mapping[str, Any]] = ()) -> dict[str, Any]:
    """
    All five Portfolio Health readings for one governed cohort, from one fitted model set.

    Returns `{"ok", "cohort", "results", "structure_absent"}`. Where the governed structure is
    absent or inconsistent every module abstains WITH THE SAME REASON, because the abstention is
    a property of the cohort and not of five separate opinions about it.
    """
    try:
        cohort = PortfolioCohort(cohort_structure, schema, records)
    except StructureAbsent as exc:
        reason = str(exc)
        return {
            "ok": True,
            "structure_absent": True,
            "cohort": None,
            "results": {RESULT_KEYS[m]: abstain(m, METHOD_CLASSES[m], None, reason)
                        for m in RESULT_KEYS},
        }
    results = {
        "cat8_1_isolation_forest": isolation_forest(cohort),
        "cat8_2_portfolio_outlier": portfolio_outlier(cohort),
        "cat8_3_trajectory_classifier": trajectory_classifier(list(histories), cohort),
        "cat8_4_cross_project_pattern": cross_project_pattern(cohort),
    }
    results["cat8_5_anomaly_score"] = anomaly_profile(cohort, {
        "D1.1": results["cat8_1_isolation_forest"],
        "D1.2": results["cat8_2_portfolio_outlier"],
        "D1.3": results["cat8_3_trajectory_classifier"],
        "D1.4": results["cat8_4_cross_project_pattern"],
    })
    return {"ok": True, "structure_absent": False, "cohort": cohort.identity(),
            "results": {k: results[k] for k in sorted(results)}}
