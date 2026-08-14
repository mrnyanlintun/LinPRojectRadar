"""
RUN 27. The curated evidence contract, one entry per non-SCIENTIFIC_PASS target.

THIS FILE IS THE HAND-AUTHORED HALF OF THE MATRIX AND NOTHING ELSE. Every mechanical column --
registered name, group, category, activation state, voting status, scientific disposition, the
shipped computation's own description, the absent canonical structure, the parameter provenance
sentence, and the document fields that actually reach the module -- is read at build time from the
registry, the Cycle-12 re-audit, method_labels.py, parameters.py and the authoritative edge list.
Nothing in those columns is retyped here, so this file cannot drift from them.

What IS authored here is the part no artifact in the repository already answers: for a method whose
canonical structure is absent, WHAT EXACTLY THE PLATFORM WOULD HAVE TO ACQUIRE, item by item, and
through which supply mechanism. Section 4 of the Run 27 prompt forbids "more data required", so an
entry whose missing_evidence is a single vague phrase is a defect in this file.

SUPPLY MECHANISM VOCABULARY is fixed by section 5 of the prompt and validated by the guard.
CORPUS STATUS VOCABULARY is fixed by section 6.
PARSIMONY CLASS VOCABULARY is fixed by section 7.
"""

from __future__ import annotations

# --------------------------------------------------------------------------------------------
# Vocabularies. The guard imports these, so a typo in an entry below fails the suite rather than
# reaching the matrix.
# --------------------------------------------------------------------------------------------

SUPPLY_MECHANISMS = {
    "EXISTING_DOCUMENT_EXTRACTION",
    "NEW_DOCUMENT_TYPE",
    "NEW_STRUCTURED_FORM",
    "NEW_PROJECT_DATA_OBJECT",
    "HISTORICAL_DATASET",
    "PORTFOLIO_REFERENCE_DATASET",
    "EXTERNAL_OFFICIAL_DATA",
    "CONTRACT_BASELINE_DATA",
    "DERIVED_FROM_EXISTING_QUALIFIED_DATA",
    "NOT_REASONABLY_SUPPLIABLE",
}

CORPUS_STATES = {
    "PRESENT",
    "PRESENT_NOT_EXTRACTED",
    "PARTIALLY_PRESENT",
    "ABSENT",
    "CANNOT_BE_INFERRED_SAFELY",
}

PARSIMONY_CLASSES = {
    "KEEP_AND_SUPPLY",
    "KEEP_AND_IMPLEMENT",
    "KEEP_AS_TRUTHFUL_PROXY",
    "KEEP_CONDITIONAL",
    "KEEP_RESEARCH_ONLY",
    "RENAME",
    "CONSOLIDATE_CANDIDATE",
    "REMOVE_CANDIDATE",
    "OWNER_DECISION_REQUIRED",
}

REMEDIATION_TYPES = {"DATA", "METHOD", "CAL", "LINEAGE", "REG", "VALIDATE", "RESEARCH", "PARSIMONY"}

PRIORITIES = {"P0", "P1", "P2", "P3"}

FUTURE_RUNS = {"Run 28", "Run 29", "Run 30", "Run 31", "Run 32", "Run 33"}

# --------------------------------------------------------------------------------------------
# Shared evidence structures. Several modules are blocked by ONE missing structure, and stating
# that structure once is the point of section 10's work packages: supply it and several modules
# become runnable together. The package id is carried on every row it serves.
# --------------------------------------------------------------------------------------------

SCHEDULE_NETWORK = (
    "activity id; activity name; deterministic duration; predecessor and successor relationships "
    "with relationship type and lag; calendar id and working-day definition; data date / status "
    "date; baseline start and finish per activity; actual start and finish per activity; "
    "remaining duration; total float and free float per activity; constraint type and date where "
    "one is imposed; WBS parent"
)

SCHEDULE_NETWORK_STOCH = (
    SCHEDULE_NETWORK
    + "; plus, for a sampling run: a duration distribution family and its parameters per activity "
    "(or three-point optimistic / most likely / pessimistic), the correlation or dependence "
    "structure between activity durations, and the risk-event-to-activity mapping with "
    "probability and impact"
)

TIME_PHASED_PV = (
    "period start and end; the planned value planned to be earned in that period; the cumulative "
    "planned value at each period end; the budget at completion the curve integrates to; the "
    "baseline id and baseline approval date the curve belongs to; the units and currency"
)

REPORTING_HISTORY = (
    "a per-project time series with, for each reporting period: period id, period start, period "
    "end, data date, budget at completion, earned value, actual cost, planned value, actual and "
    "planned percent complete, and the document version each figure was read from"
)

REFERENCE_CLASS = (
    "a population of completed projects with, per project: project id; project type / asset class; "
    "delivery method; region; currency and price base year; approved baseline cost and baseline "
    "duration at the decision point the class is anchored to; realised final cost and realised "
    "final duration; scope-change indicator; inclusion and exclusion criteria applied; the "
    "normalisation and adaptation variables (size, complexity, escalation base) used to make the "
    "class comparable; and the data vintage of each record"
)

CONTRACT_BASELINE = (
    "the schedule of values or approved contract rates; the contractual material baseline with "
    "planned quantity, unit of measure, unit rate and currency per line; approved substitutions; "
    "escalation provisions and their index reference; the contract sum breakdown and its "
    "revisions with effective dates"
)

DSM_STRUCTURE = (
    "an explicit element set (components, work packages or design tasks) with stable ids; a "
    "directed dependency matrix over those elements; a rework probability and a rework impact per "
    "dependency edge; a work-transformation or learning coefficient per element; and the iteration "
    "or period step over which propagation is evaluated"
)

QUEUE_OBSERVATION = (
    "arrival timestamps (or a fitted arrival process with its parameters); service start and "
    "service end timestamps, or observed service-time durations; the number of servers or "
    "resource units available per period; the queue discipline; the routing between stations; "
    "and the observation window with its start and end"
)

DES_STRUCTURE = (
    "entity types and their generation process; resource definitions with capacity and calendar; "
    "an event definition set (event type, trigger condition, state change, duration "
    "distribution); queue definitions and disciplines; a run length, warm-up period and "
    "replication count; and the random seed policy"
)

ABM_STRUCTURE = (
    "agent types with attributes; a decision rule per agent type; an interaction or network "
    "structure between agents; an environment state the agents read and write; a time-step "
    "definition; and initialisation and replication policy"
)

ALTERNATIVES_SET = (
    "a set of candidate actions with stable ids and a description of each; the decision variables "
    "each action moves, with type, unit and bounds; the objective functions with coefficients and "
    "sense (minimise or maximise); the constraint set with coefficient matrix, relation and "
    "right-hand side; and the units of every quantity so the model is dimensionally coherent"
)

REG_AUTHORITY = (
    "the issuing authority; the instrument identifier and its clause or section; the version and "
    "its effective date; the jurisdiction; an applicability predicate stating which projects the "
    "rule binds; the numeric level the instrument itself states (rather than one chosen here); "
    "and an evidence object recording which document proved the condition and where in it"
)

ELICITATION_SET = (
    "an elicited assessment set: expert id; the object assessed; the linguistic or interval "
    "assessment given; the elicitation protocol and date; the aggregation rule agreed in advance; "
    "and the consistency or agreement statistic across experts"
)

LABELLED_CORPUS = (
    "a labelled reference corpus: document id; document type; the ground-truth condition assigned "
    "by a qualified reviewer; the reviewer id; the adjudication rule for disagreements; and a "
    "frozen train / calibration / holdout split"
)

# --------------------------------------------------------------------------------------------
# The curated table. Keys are code ids. Every non-SCIENTIFIC_PASS target must appear exactly once;
# the guard fails if one is missing or if an id here is not a non-pass target.
#
# Field meanings:
#   canon      canonical method the registered name commits the platform to
#   missing    the exact evidence items that are absent, itemised. Empty string means the method
#              is not blocked on evidence.
#   struct     the named data structure that must exist to hold them
#   supply     supply mechanism from SUPPLY_MECHANISMS
#   artifact   the proposed artifact that would carry it
#   corpus     corpus status from CORPUS_STATES
#   pars       parsimony class from PARSIMONY_CLASSES
#   rename     truthful rename candidate, or ""
#   pkg        work package id (section 10)
#   pri        priority (section 12)
#   run        future run (section 11)
#   note       anything that must be said in the row's own words
# --------------------------------------------------------------------------------------------


def _e(canon, missing, struct, supply, artifact, corpus, pars, rename, pkg, pri, run, note=""):
    return dict(canon=canon, missing=missing, struct=struct, supply=supply, artifact=artifact,
                corpus=corpus, pars=pars, rename=rename, pkg=pkg, pri=pri, run=run, note=note)


_NO_CAL_SET = (
    "no labelled corpus of project outcomes and no expert reference standard exists in this "
    "repository, so no calibration set exists to fit or test a boundary against"
)

CURATED: dict[str, dict] = {}

# ---------------------------------------------------------------- Category 1, A1 Cost and EVM
CURATED["A1.1"] = _e(
    "Monte Carlo simulation of cost at completion over declared input distributions, reporting a "
    "distribution and stated percentiles of it",
    "cost-driver input distributions with a declared family and parameters (the module samples "
    "designed distributions rather than elicited or fitted ones); the elicitation or fitting "
    "record behind each distribution; the dependence structure between drivers; and a convergence "
    "criterion tied to the reported percentile",
    "Cost Driver Distribution Set (driver id, distribution family, parameters, source of the "
    "parameters, correlation matrix between drivers)",
    "NEW_STRUCTURED_FORM", "Cost Driver Distribution Set", "ABSENT",
    "KEEP_AND_SUPPLY", "", "PKG-CAL-BANDS", "P2", "Run 28",
    "The simulation itself is real and is performed as named. What is unsourced is the band "
    "ladder over its output and the provenance of the sampled spread.")

CURATED["A1.2"] = _e(
    "two-sided cumulative sum control chart with a reference value k and a decision interval H "
    "derived from the in-control process standard deviation and a stated shift to detect",
    "an in-control reference period declared as such; an estimate of the process standard "
    "deviation from that period rather than a floored constant; the shift size the chart is "
    "designed to detect; and the average-run-length target the pair (k, H) is chosen to meet",
    "Control Chart Design Record (series id, in-control window, sigma estimate and its n, target "
    "shift, k, H, resulting in-control and out-of-control ARL)",
    "DERIVED_FROM_EXISTING_QUALIFIED_DATA", "Control Chart Design Record", "PARTIALLY_PRESENT",
    "KEEP_AND_SUPPLY", "", "PKG-HISTORY", "P1", "Run 28",
    "The cumulative sums run on real reported cost-index history, so the series exists; the "
    "design constants around it do not.")

CURATED["A1.3"] = _e(
    "Bayesian updating of a completion-cost posterior from a stated prior and a stated likelihood, "
    "reporting a posterior with a credible interval",
    "a prior distribution with its source (currently a designed constant variance); a likelihood "
    "whose variance is estimated from observed reporting error rather than designed; and the "
    "observation series the update runs over",
    "Bayesian Model Record (prior family and parameters with source, likelihood variance and the "
    "residual series it was estimated from, posterior summary and credible interval)",
    "DERIVED_FROM_EXISTING_QUALIFIED_DATA", "Bayesian Model Record", "PARTIALLY_PRESENT",
    "KEEP_AND_SUPPLY", "", "PKG-HISTORY", "P1", "Run 28",
    "Normal-normal updating with designed constant variances is a governed model once the two "
    "variances have an estimation basis; the reporting history is the basis available.")

CURATED["A1.4"] = _e(
    "Kalman filtering of the schedule performance index with process noise Q and measurement "
    "noise R estimated from data, reporting a filtered state and its variance",
    "an estimate of measurement noise R from repeated readings of the same period (the "
    "disagreement between documents reporting one period); an estimate of process noise Q from "
    "the period-to-period movement of the index; and a history long enough for both",
    "Filter Noise Estimation Record (series id, R estimate with the repeated-reading pairs it "
    "came from, Q estimate with the differenced series, filtered state and variance)",
    "DERIVED_FROM_EXISTING_QUALIFIED_DATA", "Filter Noise Estimation Record", "PARTIALLY_PRESENT",
    "KEEP_AND_SUPPLY", "", "PKG-HISTORY", "P1", "Run 28",
    "Repeated readings of one period do occur in this corpus when two document types report the "
    "same period, which is exactly what an R estimate needs.")

CURATED["A1.5"] = _e(
    "an identified ARIMA model: order selection, stationarity testing, residual diagnostics and a "
    "prediction interval on the forecast",
    "a reported cost-index series long enough to identify an order (the platform currently fits "
    "one autoregressive coefficient at a fixed lag with no order search); the stationarity test "
    "result; residual autocorrelation diagnostics; and the residual variance the prediction "
    "interval is built from",
    "Reporting History Series (per period: period id, data date, cpi, spi, ev, ac, pv, bac, "
    "percent complete, source document version)",
    "DERIVED_FROM_EXISTING_QUALIFIED_DATA", "Reporting History Series", "PARTIALLY_PRESENT",
    "KEEP_AND_SUPPLY", "Fixed-order one-step cost index projection", "PKG-HISTORY", "P1", "Run 28",
    "History exists but its length per project is not governed; an order search needs a stated "
    "minimum series length, which is itself a decision to record.")

CURATED["A1.6"] = _e(
    "earned schedule: the time at which the earned value now reported would have been planned, "
    "read off a time-phased planned value curve",
    "a time-phased planned value curve: " + TIME_PHASED_PV,
    "Time-Phased Baseline Curve", "NEW_DOCUMENT_TYPE",
    "Time-Phased Schedule / Baseline S-Curve (a document type is already declared for this and "
    "emits nothing the module reads)", "PARTIALLY_PRESENT",
    "KEEP_AND_SUPPLY", "Reported against planned progress ratio", "PKG-TIMEPHASED", "P1", "Run 28",
    "time_phased_schedule is already a declared document type in extraction_fields.py, so the "
    "supply path is an extraction contract rather than a new document class.")

CURATED["A1.9"] = _e(
    "a standardised statistical test of expenditure against progress, with a stated null and a "
    "reference distribution",
    "the reference distribution the ratio would be tested against, which requires a population of "
    "expenditure-versus-progress observations across projects and periods",
    "Portfolio Reporting History (the Reporting History Series pooled across projects)",
    "PORTFOLIO_REFERENCE_DATASET", "Portfolio Reporting History", "ABSENT",
    "KEEP_AS_TRUTHFUL_PROXY", "Expenditure against progress control ratio",
    "PKG-PORTFOLIO-HISTORY", "P2", "Run 28",
    "As a transparent ratio it is defensible now; only the word 'test' would require the "
    "reference distribution.")

CURATED["A1.10"] = _e(
    "regression to the mean: shrinkage of a project reading toward a REFERENCE POPULATION mean "
    "with a shrinkage weight estimated from the variance components",
    "a governed reference population of projects with their cost indices; the within-project and "
    "between-project variance components estimated from it; and the resulting shrinkage weight "
    "(the platform uses a fixed one half toward the project's own history)",
    "Portfolio Reference Cohort (project id, cohort membership criteria, per-period cost index, "
    "cohort mean and variance components, vintage)",
    "PORTFOLIO_REFERENCE_DATASET", "Portfolio Reference Cohort", "ABSENT",
    "KEEP_AND_SUPPLY", "Fixed shrinkage toward the project's own history",
    "PKG-PORTFOLIO-HISTORY", "P1", "Run 28",
    "Shrinking toward a project's own history is a different estimator from the one the name "
    "names, and no amount of calibration converts one into the other without the population.")

CURATED["A1.11"] = _e(
    "an independent cost estimate: an estimate prepared separately, by a different party or a "
    "different method, against the same scope, compared with the current forecast",
    "an independently prepared estimate carrying: estimator identity and independence attestation; "
    "estimate date; the scope baseline version estimated; the estimating method used; the "
    "estimate value with its confidence basis; and the WBS level of detail",
    "Independent Cost Estimate Record",
    "NEW_DOCUMENT_TYPE", "Independent Cost Estimate", "ABSENT",
    "KEEP_AND_SUPPLY", "Internal completion forecast divergence index", "PKG-CONTRACT", "P1",
    "Run 28",
    "Both forecasts compared today are this platform's own arithmetic on one set of numbers, so "
    "the comparison cannot be independent by construction, not by calibration.")

# ---------------------------------------------------------------- Category 2, A2 Schedule
CURATED["A2.1"] = _e(
    "PERT: a network with three-point activity duration estimates, from which path criticality is "
    "computed",
    SCHEDULE_NETWORK_STOCH,
    "Schedule Network Data", "NEW_DOCUMENT_TYPE",
    "Schedule Network Export (activity table plus relationship table, from the scheduling tool)",
    "ABSENT",
    "KEEP_AND_SUPPLY", "", "PKG-SCHEDNET", "P1", "Run 28",
    "The module currently abstains, which is the correct behaviour in the absence of the network; "
    "abstention is not the defect, the missing structure is.")

CURATED["A2.2"] = _e(
    "line of balance: planned and actual production rates per repetitive activity across units, "
    "with the buffer between them",
    "repetitive unit ids and their sequence; per activity and per unit, planned start and finish "
    "and actual start and finish; the planned production rate per activity; the target buffer "
    "between successive activities; and the status date",
    "Repetitive Work Production Table", "NEW_STRUCTURED_FORM",
    "Line of Balance Production Schedule", "ABSENT",
    "KEEP_CONDITIONAL", "", "PKG-SCHEDNET", "P1", "Run 28",
    "Line of balance is only meaningful on repetitive work. Whether this platform's projects are "
    "repetitive is an owner scoping decision, not a data question.")

CURATED["A2.3"] = _e(
    "critical chain buffer health: buffer consumption against chain completion, on a "
    "buffered network",
    "the identified critical chain; the project buffer size and its origin; feeding buffers with "
    "their sizes and the chains they protect; buffer consumed to date; and the percentage of the "
    "protected chain complete",
    "Critical Chain Buffer Register", "NEW_STRUCTURED_FORM", "CCPM Buffer Register", "ABSENT",
    "KEEP_CONDITIONAL", "", "PKG-SCHEDNET", "P1", "Run 28",
    "A buffered schedule is a scheduling-method choice the project must have made; if it has not, "
    "the module is not applicable rather than under-supplied.")

CURATED["A2.4"] = _e(
    "schedule compression / crashing: a network-based model of which activities can be shortened, "
    "at what cost slope, and the resulting duration-cost trade-off",
    SCHEDULE_NETWORK + "; plus a crash duration and a cost slope per crashable activity",
    "Schedule Network Data with Crash Cost Table", "NEW_DOCUMENT_TYPE",
    "Schedule Network Export plus Crash Cost Table", "ABSENT",
    "KEEP_AS_TRUTHFUL_PROXY", "Reported duration compression ratio", "PKG-SCHEDNET", "P1",
    "Run 28",
    "The ratio it computes today is interpretable on its own terms; it is the crashing model the "
    "name implies that is absent.")

CURATED["A2.5"] = _e(
    "float consumption rate: total float consumed per unit of elapsed time on identified activities",
    "", "", "", "", "PRESENT",
    "KEEP_AND_SUPPLY", "", "PKG-CAL-BANDS", "P2", "Run 28",
    "consumedFloat and totalFloat are extracted and the arithmetic is what the name says. What is "
    "missing is a calibrated band, not evidence.")

CURATED["A2.6"] = _e(
    "S-curve deviation: the divergence between the planned and actual cumulative progress CURVES "
    "over time",
    "a time-phased planned curve and the matching actual series: " + TIME_PHASED_PV
    + "; plus the actual cumulative earned value at each of the same period ends",
    "Time-Phased Baseline Curve plus Reporting History Series", "NEW_DOCUMENT_TYPE",
    "Time-Phased Schedule / Baseline S-Curve", "PARTIALLY_PRESENT",
    "KEEP_AND_SUPPLY", "Planned versus actual progress snapshot", "PKG-TIMEPHASED", "P1", "Run 28",
    "One snapshot is a point, not a curve; the module compares two points and is named for a "
    "comparison of two curves.")

CURATED["A2.7"] = _e(
    "milestone trend analysis: forecast milestone dates plotted against successive reporting "
    "dates, read as a trend against the BASELINE milestone date",
    "the baseline date for each milestone, and at least three dated snapshots of the forecast "
    "date for the same milestone with a stable milestone identifier rather than a name match",
    "Milestone Forecast History (milestone id, milestone name, baseline date, per snapshot: "
    "report date and forecast date, status)",
    "DERIVED_FROM_EXISTING_QUALIFIED_DATA", "Milestone Forecast History", "PARTIALLY_PRESENT",
    "KEEP_AND_SUPPLY", "Period-on-period milestone forecast drift", "PKG-HISTORY", "P1", "Run 28",
    "Snapshots exist and are matched by NAME, which breaks silently on a renamed milestone; a "
    "stable id is part of the missing structure, not a refinement of it.")

CURATED["A2.8"] = _e(
    "look-ahead schedule health: constraint and commitment reliability over a rolling look-ahead "
    "window",
    "", "", "", "", "PRESENT",
    "KEEP_AND_SUPPLY", "", "PKG-CAL-BANDS", "P2", "Run 28",
    "activitiesPlanned and activitiesConstrained are extracted. registry.py records that no source "
    "specifies a constraint-rate threshold, which is a calibration gap, not an evidence gap.")

CURATED["A2.9"] = _e(
    "resource loading: planned against actual resource units by period against resource "
    "availability",
    "", "", "", "", "PRESENT",
    "KEEP_AND_SUPPLY", "", "PKG-CAL-BANDS", "P2", "Run 28",
    "planned and actual labour hours are extracted; the band ladder over their ratio is unsourced.")

CURATED["A2.10"] = _e(
    "schedule risk analysis: a sampling run over a schedule network with activity duration "
    "distributions, reporting the eightieth percentile of the completion date distribution",
    SCHEDULE_NETWORK_STOCH,
    "Schedule Network Data with duration distributions", "NEW_DOCUMENT_TYPE",
    "Schedule Network Export plus Activity Duration Distribution Set", "ABSENT",
    "KEEP_AND_SUPPLY", "Deterministic schedule uplift on the remaining duration", "PKG-SCHEDNET",
    "P0", "Run 28",
    "Nothing is sampled and the reported figure is not a percentile of anything, so the registered "
    "name asserts a quantity that does not exist. P0 because the output is presented as a "
    "percentile.")

CURATED["A2.11"] = _e(
    "critical path index: the share of simulation runs in which an activity lies on the critical "
    "path",
    SCHEDULE_NETWORK_STOCH,
    "Schedule Network Data with duration distributions", "NEW_DOCUMENT_TYPE",
    "Schedule Network Export plus Activity Duration Distribution Set", "ABSENT",
    "KEEP_AND_SUPPLY", "Mean of the progress ratio and the schedule index", "PKG-SCHEDNET", "P0",
    "Run 28",
    "Neither a network nor a simulation run exists, so no activity is identified as critical at "
    "all. P0 for the same reason as A2.10.")

# ---------------------------------------------------------------- Category 3, A3 Cost risk
CURATED["A3.1"] = _e(
    "reference class forecasting: an outside-view forecast from an empirical distribution of "
    "outcomes in a comparable class of completed projects",
    REFERENCE_CLASS,
    "Reference-Class Dataset", "HISTORICAL_DATASET", "Reference-Class Dataset", "ABSENT",
    "KEEP_AND_SUPPLY", "", "PKG-REFCLASS", "P1", "Run 28",
    "The module abstains today, correctly. similar_project_bac and similar_project_final_cost are "
    "extracted from a historical_data document type, which is two fields, not a reference class: "
    "no inclusion criteria, no project type, no normalisation, no vintage.")

CURATED["A3.2"] = _e(
    "contingency burn rate: contingency drawdown against risk retirement",
    "the risk register with, per risk: risk id, the contingency allocated to it, its status "
    "(open, realised, retired) and the date of the status change; so that drawdown can be read "
    "against risk retirement rather than against percent complete",
    "Contingency Drawdown Ledger (risk id, allocation, drawdown transactions with date and "
    "amount, risk status history)",
    "NEW_STRUCTURED_FORM", "Contingency Drawdown Ledger", "PARTIALLY_PRESENT",
    "KEEP_AND_SUPPLY", "", "PKG-CONTRACT", "P1", "Run 28",
    "registry.py records that the proportional-drawdown premise the band rests on is not what the "
    "contingency literature describes, so this is a method gap as well as an evidence gap. A "
    "risk_register document type is declared but supplies no allocation or drawdown fields.")

CURATED["A3.3"] = _e(
    "labour productivity: earned output per labour hour against a productivity baseline",
    "an output measure to earn against: quantity installed per work item with its unit of "
    "measure, and the budgeted hours per unit of that quantity. Labour hours alone give a ratio "
    "of hours to percent complete, not productivity",
    "Quantity and Unit Rate Table (work item id, unit of measure, budgeted quantity, quantity "
    "installed to date, budgeted hours per unit, actual hours charged)",
    "NEW_STRUCTURED_FORM", "Quantity Installed and Unit Rate Table", "ABSENT",
    "KEEP_AS_TRUTHFUL_PROXY", "Labour hours against reported progress ratio", "PKG-CONTRACT", "P1",
    "Run 28",
    "The registered name asserts productivity; the computation reads hours against a self-reported "
    "percentage.")

CURATED["A3.5"] = _e(
    "overhead absorption: indirect cost absorbed against an absorption base",
    "the definition of the indirect plan figure: whether indirect_cost_plan is a total-at-"
    "completion or a period-to-date figure, and the absorption base (direct labour hours, direct "
    "cost or machine hours) the rate is struck on",
    "Indirect Cost Basis Declaration (plan basis flag, absorption base, base period, rate)",
    "EXISTING_DOCUMENT_EXTRACTION", "Indirect Cost Basis Declaration on the cost report", "PRESENT_NOT_EXTRACTED",
    "KEEP_AS_TRUTHFUL_PROXY", "", "PKG-CONTRACT", "P1", "Run 28",
    "The two figures are already extracted. Their MEANING is not carried, and registry.py records "
    "that the ratio's validity depends entirely on which of the two the plan figure is. One "
    "boolean field settles it.")

CURATED["A3.6"] = _e(
    "cost risk analysis: a sampling run over a risk register with cost impact distributions, "
    "reporting the eightieth percentile of the cost outcome distribution",
    "per risk: risk id; probability of occurrence; cost impact distribution family and parameters "
    "(or three-point low / likely / high); the correlation between risks; whether the risk is "
    "already realised; and the mapping of each risk to the cost account it hits",
    "Quantified Risk Register", "NEW_STRUCTURED_FORM", "Quantified Risk Register", "ABSENT",
    "KEEP_AND_SUPPLY", "Deterministic cost uplift on the index-based forecast", "PKG-RISKQUANT",
    "P0", "Run 28",
    "A risk_register document type is declared but emits no probability and no impact "
    "distribution, so a list of risks is not a quantified register. P0 because a percentile is "
    "reported where nothing is sampled.")

CURATED["A3.7"] = _e(
    "analogous estimating: a governed selection of analogous completed projects with a documented "
    "normalisation and adaptation to the subject project",
    "the analogue selection rule; per analogue: project id, scope description, final cost, "
    "completion year, size and complexity descriptors, region and price base; and the "
    "normalisation and adaptation factors applied with their justification",
    "Analogue Project Set (a governed subset of the Reference-Class Dataset)",
    "HISTORICAL_DATASET", "Reference-Class Dataset", "PARTIALLY_PRESENT",
    "KEEP_AND_SUPPLY", "", "PKG-REFCLASS", "P1", "Run 28",
    "analogous_overrun_pct is extracted as a single number with no record of which project it came "
    "from or how it was adapted, which is the whole of the method.")

CURATED["A3.9"] = _e(
    "inflation adjustment against a published price index",
    "a governed external price index: publisher; index name and series id; geography; commodity or "
    "trade coverage; base period; the index value at the baseline date and at the current date; "
    "and the vintage or revision of the series used",
    "External Price Index Record", "EXTERNAL_OFFICIAL_DATA",
    "Price Index Reference (for example a published construction cost or producer price series)",
    "ABSENT",
    "KEEP_AND_SUPPLY", "Material cost ratio without an external price index", "PKG-EXTERNAL", "P1",
    "Run 28",
    "The module compares a project's own reported material cost against its own baseline and calls "
    "the ratio an inflation adjustment. No index is read.")

# ---------------------------------------------------------------- Category 4, A4 Document signals
CURATED["A4.1"] = _e(
    "a document risk score with measured precision and recall against a reference standard",
    "a labelled reference corpus: " + LABELLED_CORPUS
    + "; plus the score's own construction: which document features enter it, with what weights "
    "and from what source",
    "Labelled Document Corpus plus Score Construction Record",
    "NEW_PROJECT_DATA_OBJECT", "Labelled Document Corpus", "ABSENT",
    "KEEP_CONDITIONAL", "", "PKG-DOCLABEL", "P0", "Run 29",
    "Supplied by the extraction model rather than computed by the analytical server, and it is the "
    "single most widely consumed input in the system: it reaches at least twenty-eight registered "
    "modules on the authoritative edge list. An unvalidated score with that fan-out is a P0.")

CURATED["A4.2"] = _e(
    "requests for information per unit of exposure time, with an overdue share",
    "", "", "", "", "PRESENT",
    "KEEP_AND_SUPPLY", "", "PKG-CAL-BANDS", "P2", "Run 29",
    "rfiCount and rfiPeriodDays are both extracted, so the rate is a real rate. registry.py "
    "records that no source specifies a per-week rate or overdue-share threshold.")

CURATED["A4.3"] = _e(
    "submittal rejection share against total submittals reviewed",
    "", "", "", "", "PRESENT",
    "KEEP_AND_SUPPLY", "", "PKG-CAL-BANDS", "P2", "Run 29",
    "Both numerator and denominator are extracted; only the threshold is unsourced.")

CURATED["A4.4"] = _e(
    "nonconformance rate: nonconformances per unit of exposure",
    "an exposure denominator: inspections performed, work quantity placed, or labour hours in the "
    "period, so that a count becomes a rate. Only counts (ncr_issued, ncr_open, ncr_closed) are "
    "extracted",
    "Document Event Denominator (period id, event type, count, exposure unit, exposure quantity)",
    "EXISTING_DOCUMENT_EXTRACTION", "Document Event Denominator Set", "PARTIALLY_PRESENT",
    "KEEP_AND_SUPPLY", "", "PKG-DENOM", "P1", "Run 29",
    "items_inspected is already an extracted field on the inspection report and is a candidate "
    "denominator; nothing currently connects it to the nonconformance counts.")

CURATED["A4.5"] = _e(
    "weather impact: lost days against the float available to absorb them",
    "", "", "", "", "PRESENT",
    "KEEP_AS_TRUTHFUL_PROXY", "Lost days against available float", "PKG-CAL-BANDS", "P2", "Run 29",
    "Requires verified lost days and a positive float figure and refuses without either. The band "
    "ladder is ungoverned.")

CURATED["A4.6"] = _e(
    "change order frequency: change orders per unit of exposure time or exposure value",
    "an exposure window: the period over which the counted change orders arose, or the contract "
    "value at risk they are counted against. A count with no denominator is not a frequency",
    "Document Event Denominator (period start, period end, count in window, contract value "
    "exposed)",
    "EXISTING_DOCUMENT_EXTRACTION", "Document Event Denominator Set", "PRESENT_NOT_EXTRACTED",
    "KEEP_AND_SUPPLY", "Change order count with contract growth", "PKG-DENOM", "P1", "Run 29",
    "report_period and work_period_from / work_period_to are already extracted fields on other "
    "document types, so the window exists in the corpus and is simply not joined to the count.")

CURATED["A4.7"] = _e(
    "dispute escalation: the state of claims and disputes on a governed escalation ladder",
    "per claim or notice: identifier; date raised; the contractual clause invoked; the amount "
    "claimed; the current rung of the escalation ladder (notice, claim, negotiation, mediation, "
    "arbitration, litigation); the date of the last state change; and the outcome where resolved",
    "Claim and Dispute Register", "NEW_DOCUMENT_TYPE", "Claim and Notice Register", "ABSENT",
    "KEEP_AS_TRUTHFUL_PROXY", "Weighted project stress composite", "PKG-DOCEVENT", "P1", "Run 29",
    "A correspondence_notice document type is declared, which is the natural carrier, but no "
    "claim-state field is emitted. Also carries a LINEAGE defect: the composite sums a request "
    "count, a change order count and the document risk score, and the document risk score is "
    "itself partly built from document events.")

CURATED["A4.8"] = _e(
    "subcontractor performance assessment against declared criteria",
    "the construction of the compliance score: which criteria it aggregates, with what weights, "
    "assessed by whom, on what date, and against which subcontract scope. The platform reads a "
    "precomputed number with no construction record",
    "Subcontractor Assessment Record (subcontract id, criterion, score, weight, assessor, "
    "assessment date, period covered)",
    "EXISTING_DOCUMENT_EXTRACTION", "Subcontractor Assessment Record", "PARTIALLY_PRESENT",
    "KEEP_AND_SUPPLY", "", "PKG-DOCEVENT", "P1", "Run 29",
    "The subcontractor_report document type exists and supplies the aggregate; the components it "
    "aggregates are what is missing.")

CURATED["A4.9"] = _e(
    "procurement lead time monitoring: required-on-site dates against forecast delivery dates for "
    "long-lead items",
    "", "", "", "", "PRESENT",
    "KEEP_AND_SUPPLY", "", "PKG-CAL-BANDS", "P2", "Run 29",
    "long_lead_items_total, at_risk and delayed are extracted from the procurement log. Dates per "
    "item would strengthen it, but the module as named runs on what it has; the bands are "
    "unsourced.")

CURATED["A4.10"] = _e(
    "specification conflict density: identified conflicts between specification sections per unit "
    "of specification exposure",
    "identified conflicts: conflict id; the two specification references in conflict, each with "
    "document id, section and page or clause; who identified it and when; and the exposure unit "
    "(specification sections issued, or drawings issued) the density is measured over",
    "Specification Conflict Register with evidence locations",
    "NEW_STRUCTURED_FORM", "Specification Conflict Register", "ABSENT",
    "CONSOLIDATE_CANDIDATE", "Document risk weighted by request volume", "PKG-DOCEVENT", "P1",
    "Run 29",
    "No conflict is located in any document, so nothing is counted as a conflict. The computation "
    "is a strict function of the document risk score and the request count, both of which are "
    "already registered inputs elsewhere, so it adds no evidence of its own.")

# ---------------------------------------------------------------- Category 5, A5 System dynamics
CURATED["A5.1"] = _e(
    "design structure matrix rework propagation: rework probability and impact propagated over a "
    "dependency matrix",
    DSM_STRUCTURE,
    "DSM Dependency Matrix", "NEW_STRUCTURED_FORM", "DSM Dependency Matrix", "ABSENT",
    "KEEP_AND_SUPPLY", "", "PKG-DSM", "P1", "Run 29",
    "A list of risks is not a dependency matrix. The module abstains today, correctly.")

CURATED["A5.2"] = _e(
    "sensitivity analysis: a response re-evaluated as each input is moved across a declared range",
    "declared input ranges: for each input, the low and high value with the basis for each, and "
    "the response function the ranges are propagated through",
    "Input Range Declaration (input id, low, high, basis, distribution if used)",
    "NEW_STRUCTURED_FORM", "Scenario Assumption Set", "ABSENT",
    "KEEP_AS_TRUTHFUL_PROXY", "Local cost index perturbation with present-state deviations",
    "PKG-SCENARIO", "P1", "Run 29",
    "The module perturbs one index by a designed amount and reports present-state deviations "
    "beside it; no input range is declared anywhere.")

CURATED["A5.3"] = _e(
    "tornado analysis: the swing in an output when each input is moved across its declared range, "
    "ranked by swing",
    "declared input ranges as for A5.2, plus the output the swing is measured on and its "
    "re-evaluation at each low and high",
    "Input Range Declaration plus a named response output",
    "NEW_STRUCTURED_FORM", "Scenario Assumption Set", "ABSENT",
    "CONSOLIDATE_CANDIDATE", "Ranked present-state deviations", "PKG-SCENARIO", "P1", "Run 29",
    "Ranks four present-state deviations by magnitude. Once input ranges exist, A5.2 and A5.3 are "
    "two presentations of one computation and consolidation should be considered.")

CURATED["A5.4"] = _e(
    "scenario modelling: named scenarios with declared assumption sets, evaluated through the "
    "same model",
    "per scenario: scenario id and name; the assumption set (each assumption with the input it "
    "sets and the value it sets it to); the probability or weight assigned to the scenario if "
    "any; and the author and date of the assumption set",
    "Scenario Assumption Set", "NEW_STRUCTURED_FORM", "Scenario Assumption Set", "ABSENT",
    "KEEP_AND_SUPPLY", "", "PKG-SCENARIO", "P1", "Run 29",
    "Abstains today. The scenario structure is the whole method.")

CURATED["A5.5"] = _e(
    "a system dynamics rework feedback loop: stocks of work done, work discovered defective and "
    "work returned, with the rates between them over time",
    "stock and flow definitions: work in each stock at each period; the discovery rate; the "
    "rework rate; the delay between execution and discovery; and the loop gain, each estimated "
    "from observed period data rather than assumed",
    "Rework Stock and Flow Series", "NEW_STRUCTURED_FORM", "Rework Stock and Flow Series", "ABSENT",
    "KEEP_AS_TRUTHFUL_PROXY", "Weighted rework pressure composite", "PKG-DSM", "P1", "Run 29",
    "Nothing accumulates and nothing feeds back; the computation is a fixed weighted sum of three "
    "present-state figures.")

CURATED["A5.6"] = _e(
    "queueing analysis: arrival and service processes, server count and discipline, from which "
    "utilisation, queue length and waiting time follow",
    QUEUE_OBSERVATION,
    "Queue Observation Log", "NEW_STRUCTURED_FORM", "Queue Observation Log", "ABSENT",
    "KEEP_AND_SUPPLY", "", "PKG-QUEUE", "P1", "Run 29",
    "Counts of constrained and planned activities are not arrival and service observations. The "
    "module abstains today, correctly.")

CURATED["A5.7"] = _e(
    "agent-based supply chain simulation: agents with decision rules interacting over time",
    ABM_STRUCTURE + "; plus, for a supply chain: supplier agents with lead-time distributions, "
    "order policies, and the disruption events they respond to",
    "Agent / Resource Definition", "NEW_STRUCTURED_FORM", "Agent and Resource Definition Set",
    "ABSENT",
    "KEEP_RESEARCH_ONLY", "", "PKG-QUEUE", "P3", "Run 29",
    "Two extracted long-lead fields are the whole of its evidence today. Whether an agent-based "
    "supply chain model earns its evidence burden for this platform is an open owner question.")

CURATED["A5.8"] = _e(
    "discrete event simulation: entities, resources, queues, an event list and a simulation clock",
    DES_STRUCTURE,
    "DES Event Definition", "NEW_STRUCTURED_FORM", "DES Event Definition Set", "ABSENT",
    "KEEP_RESEARCH_ONLY", "Throughput index from the schedule index and progress ratio",
    "PKG-QUEUE", "P1", "Run 29",
    "No event is scheduled and no clock advances. P1 rather than P3 because the registered name "
    "asserts a simulation that does not exist, which is a truthfulness problem now.")

# ---------------------------------------------------------------- Category 8 part 1, A6 Quality
CURATED["A6.1"] = _e(
    "quality compliance: conformance against declared quality criteria",
    "the quality audit findings themselves: audit_score, total_findings, critical_findings and "
    "items_inspected / items_failed are ALL extracted from the quality_audit_report and "
    "inspection_report document types and NONE of them reaches this module, which reads the "
    "meeting-minute proxy qualityDeficienciesNoted instead",
    "Quality Evidence Wiring (join the quality_audit_report and inspection_report fields to the "
    "module's input contract)",
    "EXISTING_DOCUMENT_EXTRACTION", "Quality Audit Report (already a supported document type)",
    "PRESENT_NOT_EXTRACTED",
    "KEEP_AND_SUPPLY", "", "PKG-ORPHANFIELDS", "P0", "Run 31",
    "This is the orphan-field finding: the evidence exists in the corpus, is extracted, and is not "
    "consumed. P0 because the module reads a weaker proxy while the real evidence sits unused.")

CURATED["A6.2"] = _e(
    "safety performance: recordable incidents against exposure hours on the standard basis",
    "osha_recordable_incidents, incident_rate and total_manhours are ALL extracted from the "
    "safety_report document type and NONE reaches this module, which reads the meeting-minute "
    "proxy safetyIncidentsDiscussed instead. The standard rate requires recordable incident count "
    "and total manhours together with the two-hundred-thousand-hour convention",
    "Safety Evidence Wiring (join the safety_report fields to the module's input contract)",
    "EXISTING_DOCUMENT_EXTRACTION", "Safety Report (already a supported document type)",
    "PRESENT_NOT_EXTRACTED",
    "KEEP_AND_SUPPLY", "", "PKG-ORPHANFIELDS", "P0", "Run 31",
    "Same orphan-field finding as A6.1. A safety rate computed from a count of mentions in "
    "minutes, while the recordable count and manhours sit extracted and unread, is the clearest "
    "case in the population.")

CURATED["A6.3"] = _e(
    "environmental compliance against a named authority's conditions, at a stated version",
    "environmentalComplianceRate and violations are extracted from the environmental_report and "
    "do not reach this module, which reads environmentalIssuesDiscussed from meeting minutes. "
    "Separately the regulatory object is absent: " + REG_AUTHORITY,
    "Regulatory Applicability Record plus Environmental Evidence Wiring",
    "EXISTING_DOCUMENT_EXTRACTION",
    "Environmental Report (already supported) plus Regulatory Applicability Record",
    "PRESENT_NOT_EXTRACTED",
    "KEEP_AND_SUPPLY", "", "PKG-ORPHANFIELDS", "P0", "Run 31",
    "Carries BOTH open findings at once: an orphan extracted field and a REGULATORY_VERSION_BLOCKED "
    "disposition. The permit authority, jurisdiction and version of the conditions assessed are "
    "not carried.")

CURATED["A6.4"] = _e(
    "contractor past performance assessment drawn from official past performance information",
    "a past performance record with: the source system identifier; the assessing agency; the "
    "assessment period; the contract it relates to; the rating on each declared factor; the record "
    "status; and its review state",
    "Past Performance Information Record", "EXTERNAL_OFFICIAL_DATA",
    "Official Past Performance Information", "ABSENT",
    "KEEP_AS_TRUTHFUL_PROXY", "Project-document contractor estimate", "PKG-EXTERNAL", "P1",
    "Run 31",
    "A past_performance_report document type is declared and supplies overall, cost and schedule "
    "ratings from this project's own documents. Nothing here is past performance information and "
    "must not be read as such.")

# ---------------------------------------------------------------- Category 6, B1 Signal synthesis
CURATED["B1.2"] = _e(
    "weighted voting over qualified signal states with sourced weights",
    "the qualified-evidence boundary: a signal qualification state per input, which the "
    "Category-9 gate would supply and which production itself records as unimplemented "
    "(SIGNAL_QUALIFICATION = 'unqualified', CATEGORY_9_DEVIATION)",
    "Qualified Signal State (per signal: qualification verdict, the dimensions assessed, the "
    "reason where unqualified)",
    "DERIVED_FROM_EXISTING_QUALIFIED_DATA", "Category-9 Qualification Verdict", "ABSENT",
    "KEEP_AND_SUPPLY", "Fixed-weight signal band tally", "PKG-CAT9", "P0", "Run 30",
    "Four design-constant weights with no source, applied to signals that are not qualified. P0: "
    "it is a synthesis feeding presentation.")

CURATED["B1.3"] = _e(
    "majority rule over qualified signal states",
    "the same qualified-evidence boundary as B1.2, plus dependence control: the signals tallied "
    "are not independent, and several are readings of one earned-value measurement",
    "Qualified Signal State plus a declared dependence structure over signals",
    "DERIVED_FROM_EXISTING_QUALIFIED_DATA", "Category-9 Qualification Verdict", "ABSENT",
    "KEEP_AND_SUPPLY", "", "PKG-CAT9", "P0", "Run 30",
    "A counting rule over correlated readings counts one measurement more than once. Run 20 "
    "Cycle 9 established exactly this for B1.1 and fixed B1.1 only.")

CURATED["B1.4"] = _e(
    "worst-N-of-M: escalate when N of M signals are adverse, with N and M chosen against a stated "
    "error target",
    "the basis for the two proportional thresholds (three tenths of the banded signals for Red, "
    "four tenths for Amber), which are design constants; and the qualified-evidence boundary as "
    "for B1.2",
    "Threshold Design Record (rule, threshold, the error target it meets, the evidence it was "
    "chosen against) plus Qualified Signal State",
    "DERIVED_FROM_EXISTING_QUALIFIED_DATA", "Category-9 Qualification Verdict", "ABSENT",
    "KEEP_AND_SUPPLY", "", "PKG-CAT9", "P0", "Run 30",
    "Its denominator is the whole simulation signal array, so the fraction of adverse signals "
    "shrinks as more modules are registered. That is a structural defect of a proportional rule "
    "over a growing module set and is independent of calibration.")

# ---------------------------------------------------------------- Category 7, B2 Evidence
_B2_SHARED_MISSING = (
    "elicited or observed assessments to build the memberships from: " + ELICITATION_SET
    + "; plus the qualified-evidence boundary, because the memberships currently consume raw "
    "unqualified cost and schedule indices and the document risk score directly"
)

for _id, _canon, _rename, _pars, _note in [
    ("B2.1", "Dempster-Shafer combination over independently derived bodies of evidence, with a "
             "declared frame of discernment and a stated conflict treatment", "",
     "KEEP_AND_SUPPLY",
     "The combination rule is implemented. What is absent is the independence its arithmetic "
     "assumes: the bodies combined are readings of the same underlying figures."),
    ("B2.2", "rough set approximation over an information table of objects described by attributes",
     "Supermajority band classification over bodies of evidence", "KEEP_AS_TRUTHFUL_PROXY",
     "There are no objects here, only this project's own signals, so no indiscernibility class "
     "and no lower or upper approximation can be formed."),
    ("B2.3", "neutrosophic logic over independently assessed truth, indeterminacy and falsity "
             "degrees", "", "CONSOLIDATE_CANDIDATE",
     "Reads the same two indices and the document risk score as the rest of the B2 family."),
    ("B2.4", "interval-valued fuzzy sets whose interval widths come from assessment uncertainty",
     "", "CONSOLIDATE_CANDIDATE",
     "Interval widths are design constants, so the interval measures the design, not the "
     "uncertainty."),
    ("B2.5", "Z-numbers: a restriction paired with a reliability measure of that restriction", "",
     "CONSOLIDATE_CANDIDATE",
     "The reliability component needs an assessed reliability; none is elicited."),
    ("B2.6", "probabilistic linguistic term sets over elicited linguistic assessments with their "
             "probabilities", "", "CONSOLIDATE_CANDIDATE",
     "Requires linguistic assessments from people; none are collected."),
    ("B2.8", "belief rule base inference with rule weights and attribute weights learned or "
             "elicited", "", "KEEP_AND_SUPPLY",
     "The rule base is designed rather than learned or elicited."),
    ("B2.10", "Pythagorean fuzzy sets over assessed membership and non-membership", "",
     "CONSOLIDATE_CANDIDATE",
     "Hard-coded transformations of raw cost index, schedule index and document risk."),
    ("B2.11", "picture fuzzy sets over assessed positive, neutral, negative and refusal degrees",
     "", "CONSOLIDATE_CANDIDATE", "Hard-coded memberships consuming raw metrics."),
    ("B2.12", "hesitant fuzzy sets over MULTIPLE assessments of the same object by different "
              "assessors", "", "CONSOLIDATE_CANDIDATE",
     "Designed perturbations stand in for hesitant assessments; hesitancy that is manufactured "
     "measures the manufacturing rule."),
    ("B2.13", "type-2 fuzzy sets whose footprint of uncertainty comes from disagreement between "
              "assessors", "", "CONSOLIDATE_CANDIDATE",
     "Membership intervals are designed constants."),
    ("B2.14", "maximum entropy: the distribution of greatest entropy subject to stated moment "
              "constraints", "Entropy of a designed band lookup", "KEEP_AS_TRUTHFUL_PROXY",
     "Nothing is maximised. The distribution is looked up from a fixed table, so the entropy "
     "measures the lookup table."),
    ("B2.15", "possibility theory with a governed possibility distribution", "",
     "CONSOLIDATE_CANDIDATE", "Fixed mappings from raw metrics; no governed distribution."),
    ("B2.16", "spherical fuzzy sets over assessed membership, non-membership and hesitancy", "",
     "CONSOLIDATE_CANDIDATE", "Algebraically bounded but fixed memberships on raw unqualified "
     "inputs."),
    ("B2.17", "Fermatean fuzzy sets over assessed membership and non-membership", "",
     "CONSOLIDATE_CANDIDATE",
     "Property testing over a 5,166-point grid shows its band is a function of min(cpi, spi) "
     "ALONE, so it carries strictly less information than its three-input siblings."),
]:
    CURATED[_id] = _e(
        _canon, _B2_SHARED_MISSING,
        "Elicited Assessment Set plus Qualified Signal State",
        "NEW_STRUCTURED_FORM", "Expert Elicitation Form plus Category-9 Qualification Verdict",
        "ABSENT", _pars, _rename, "PKG-ELICIT", "P1", "Run 30", _note)

CURATED["B2.7"] = _e(
    "plithogenic set operations over attributes with degrees of appurtenance and a contradiction "
    "degree between attribute values",
    "the attribute set with, per attribute: its value range; the dominant value; the degree of "
    "appurtenance of each object to each value; and the contradiction degree between each value "
    "and the dominant one",
    "Plithogenic Attribute Set", "NEW_STRUCTURED_FORM", "Expert Elicitation Form", "ABSENT",
    "KEEP_RESEARCH_ONLY", "Disabled: no plithogenic structure is implemented", "PKG-ELICIT", "P3",
    "Run 30",
    "DISABLED_UNSAFE today and its formula function is never called. Assessed as requested: the "
    "structure is suppliable in principle through elicitation, but no operational question in "
    "this platform is currently expressed in plithogenic terms, and no scientific or operational "
    "value has been demonstrated. Recommendation: leave disabled, research-only.")

CURATED["B2.9"] = _e(
    "quantum probability: a state vector in a Hilbert space with projective measurement operators, "
    "from which order and interference effects follow",
    "the declared Hilbert space and its basis; the projection operators corresponding to each "
    "assessment; the state preparation; and an empirical reason to believe the judgments being "
    "modelled violate classical additivity, which is the only thing that motivates the formalism",
    "Quantum Judgment Model Specification", "NOT_REASONABLY_SUPPLIABLE",
    "none proposed: the motivating empirical phenomenon would itself have to be demonstrated first",
    "ABSENT",
    "KEEP_RESEARCH_ONLY", "Disabled: no quantum probability model is implemented", "PKG-ELICIT",
    "P3", "Run 30",
    "DISABLED_UNSAFE today. Assessed as requested: unlike the fuzzy family this one is NOT simply "
    "an elicitation gap. Quantum probability is warranted only where classical probability fails "
    "on the data, and no such failure has been observed here. Recommendation: leave disabled; "
    "strongest REMOVE_CANDIDATE in the population on parsimony grounds, subject to the owner.")

CURATED["B2.18"] = _e(
    "MARCOS: ranking of a SET of alternatives against ideal and anti-ideal reference points "
    "derived from that set",
    "a real alternative set to rank: " + ALTERNATIVES_SET
    + ". The reference points must be derived from the alternative set, which is what makes them "
    "ideal and anti-ideal",
    "Decision Alternatives Table", "NEW_STRUCTURED_FORM", "Decision Alternatives Table", "ABSENT",
    "OWNER_DECISION_REQUIRED", "Single-project criterion scoring against designed reference points",
    "PKG-ALTERNATIVES", "P1", "Run 30",
    "A ranking method over one alternative returns that alternative. Either a real alternative set "
    "is supplied or the module is not a ranking method; the owner decides which.")

CURATED["B2.19"] = _e(
    "CRITIC weighting followed by TOPSIS ranking over a decision matrix of alternatives by criteria",
    "a decision matrix: " + ALTERNATIVES_SET
    + ". CRITIC weights are derived from the contrast and conflict WITHIN the alternative set, so "
    "a single alternative supplies no weights at all",
    "Decision Alternatives Table", "NEW_STRUCTURED_FORM", "Decision Alternatives Table", "ABSENT",
    "KEEP_AND_SUPPLY", "", "PKG-ALTERNATIVES", "P1", "Run 30",
    "Abstains today, correctly.")

CURATED["B2.20"] = _e(
    "hypersoft sets: a soft set over a Cartesian product of attribute-value sets, with a mapping "
    "from each attribute tuple to a subset of the universe",
    "the universe of objects; the attribute set with the value set of each attribute; and the "
    "mapping from each tuple of attribute values to its subset of the universe",
    "Hypersoft Attribute Mapping", "NEW_STRUCTURED_FORM", "Expert Elicitation Form", "ABSENT",
    "KEEP_RESEARCH_ONLY", "Disabled: no hypersoft structure is implemented", "PKG-ELICIT", "P3",
    "Run 30",
    "DISABLED_UNSAFE today. Assessed as requested: a hypersoft set needs a universe of objects, "
    "and a single project is not a universe. Suppliable only if the platform ever ranks a real "
    "alternative or project set. Recommendation: leave disabled, research-only.")

# ---------------------------------------------------------------- Category 8 part 2, B3
CURATED["B3.1"] = _e(
    "agent-based modelling: agents with decision rules, an interaction structure and time steps",
    ABM_STRUCTURE,
    "Agent / Resource Definition", "NEW_STRUCTURED_FORM", "Agent and Resource Definition Set",
    "ABSENT",
    "RENAME", "Action boundary and authority matrix", "PKG-CAT9", "P0", "Run 31",
    "The mapping from decision-layer state to action and authority is sound and is what the "
    "platform actually needs; nothing about it is agent based. It ALSO declares raw cpi, spi and "
    "docRiskScore as required inputs, which specification section 18 forbids in those words, and "
    "that is the P0 rather than the naming.")

CURATED["B3.2"] = _e(
    "a Federal Acquisition Regulation threshold determination at a stated part, version and "
    "applicability",
    REG_AUTHORITY,
    "Regulatory Applicability Record", "NEW_PROJECT_DATA_OBJECT", "Regulatory Applicability Record",
    "ABSENT",
    "KEEP_AND_SUPPLY", "", "PKG-REG", "P1", "Run 31",
    "Run 20 Cycle 2 already removed one false attribution of a FAR part to an internally chosen "
    "level in B4.3. The same exposure exists wherever a regulation is named beside a number the "
    "regulation does not state.")

CURATED["B3.3"] = _e(
    "an OMB Circular A-11 reporting determination at a stated version and applicability",
    REG_AUTHORITY,
    "Regulatory Applicability Record", "NEW_PROJECT_DATA_OBJECT", "Regulatory Applicability Record",
    "ABSENT",
    "KEEP_AND_SUPPLY", "", "PKG-REG", "P1", "Run 31",
    "A-11 binds federal agencies; whether it binds a given project in this platform is exactly "
    "the applicability predicate that is missing.")

CURATED["B3.4"] = _e(
    "an earned value management reporting-threshold determination at a stated authority and version",
    REG_AUTHORITY,
    "Regulatory Applicability Record", "NEW_PROJECT_DATA_OBJECT", "Regulatory Applicability Record",
    "ABSENT",
    "KEEP_AND_SUPPLY", "", "PKG-REG", "P1", "Run 31", "")

CURATED["B3.5"] = _e(
    "contract modification frequency: modifications per unit of exposure time or contract value",
    "an exposure window or exposure value, as for A4.6: the period the counted modifications arose "
    "in, or the contract value they are counted against",
    "Document Event Denominator", "EXISTING_DOCUMENT_EXTRACTION", "Document Event Denominator Set",
    "PRESENT_NOT_EXTRACTED",
    "CONSOLIDATE_CANDIDATE", "Contract modification count", "PKG-DENOM", "P1", "Run 31",
    "Reads exactly the same two extracted fields as A4.6 Change Order Frequency "
    "(baselineContractSum, changeOrderCount) per the authoritative edge list. Two registered "
    "modules over one pair of inputs.")

# ---------------------------------------------------------------- Category 10, B4
CURATED["B4.1"] = _e(
    "multi-objective optimization over declared objectives, decision variables and a feasible set",
    ALTERNATIVES_SET,
    "Objective and Constraint Set", "NEW_STRUCTURED_FORM",
    "Decision Alternatives Table plus Objective and Constraint Set", "ABSENT",
    "KEEP_RESEARCH_ONLY", "Disabled: no objectives, decision variables or feasible set are "
    "implemented", "PKG-ALTERNATIVES", "P3", "Run 32",
    "DISABLED_UNSAFE. A real implementation is a new build and not a rename.")

CURATED["B4.2"] = _e(
    "linear programming: decision variables, a linear objective, a constraint matrix with "
    "right-hand sides and bounds",
    ALTERNATIVES_SET,
    "Objective and Constraint Set", "NEW_STRUCTURED_FORM", "Objective and Constraint Set", "ABSENT",
    "KEEP_RESEARCH_ONLY", "Disabled: no decision variables, objective or constraints are "
    "implemented", "PKG-ALTERNATIVES", "P3", "Run 32",
    "DISABLED_UNSAFE. Nothing in the corpus is a decision variable.")

CURATED["B4.3"] = _e(
    "constraint satisfaction: a constraint network over declared variables and domains, solved for "
    "a satisfying assignment",
    "declared decision variables with domains, and constraints over them that are not simply "
    "threshold tests on already-computed indices",
    "Objective and Constraint Set", "NEW_STRUCTURED_FORM", "Objective and Constraint Set", "ABSENT",
    "RENAME", "Four-rule project condition check", "PKG-ALTERNATIVES", "P1", "Run 32",
    "Answered explicitly for section 8: the truthful checklist reading is the right one, and the "
    "rename is the remediation. It also carries a provable arithmetic defect. Of its four rules, "
    "'CPI >= 0.90' logically IMPLIES 'CPI > 0.80', so two of the four items are one cost test, "
    "and the satisfaction rate gives cost half the weight while schedule and document risk get a "
    "quarter each. That weighting is a consequence of the redundancy rather than a decision.")

CURATED["B4.4"] = _e(
    "a what-if matrix: candidate actions as rows, scenarios as columns, an outcome in each cell",
    "candidate actions with identity (none is carried) and scenario definitions: "
    + ALTERNATIVES_SET,
    "Decision Alternatives Table plus Scenario Assumption Set", "NEW_STRUCTURED_FORM",
    "Decision Alternatives Table", "ABSENT",
    "KEEP_AS_TRUTHFUL_PROXY", "Earned value completion forecast range", "PKG-ALTERNATIVES", "P1",
    "Run 32",
    "There is one dimension here, not a matrix, and no action is carried.")

CURATED["B4.5"] = _e(
    "a decision sensitivity matrix: a decision set with declared input ranges and a response "
    "evaluated over them",
    "a decision set and declared input ranges: " + ALTERNATIVES_SET,
    "Decision Alternatives Table plus Input Range Declaration", "NEW_STRUCTURED_FORM",
    "Decision Alternatives Table plus Scenario Assumption Set", "ABSENT",
    "KEEP_RESEARCH_ONLY", "Disabled: no decisions and no sensitivities are implemented",
    "PKG-ALTERNATIVES", "P3", "Run 32", "DISABLED_UNSAFE.")

CURATED["B4.6"] = _e(
    "Pareto frontier: a set of alternatives evaluated on two or more objectives, over which "
    "dominance is assessed",
    "a set of at least two alternatives with their objective values: " + ALTERNATIVES_SET,
    "Decision Alternatives Table", "NEW_STRUCTURED_FORM", "Decision Alternatives Table", "ABSENT",
    "KEEP_RESEARCH_ONLY", "Disabled: no alternative set and no dominance relation are implemented",
    "PKG-ALTERNATIVES", "P3", "Run 32",
    "DISABLED_UNSAFE. A frontier over a single project is not defined.")

CURATED["B4.7"] = _e(
    "regret minimization: maximum regret across states of nature for each candidate action, "
    "minimised",
    "candidate actions and states of nature with a payoff for each action-state pair: "
    + ALTERNATIVES_SET + "; plus the state set with its definition",
    "Decision Alternatives Table plus Scenario Assumption Set", "NEW_STRUCTURED_FORM",
    "Decision Alternatives Table", "ABSENT",
    "KEEP_AND_SUPPLY", "", "PKG-ALTERNATIVES", "P1", "Run 32",
    "Abstains today, correctly. Regret is defined over a payoff matrix; there is no action set.")

# ---------------------------------------------------------------- Category 9, C1 Data integrity
CURATED["C1.1"] = _e(
    "missing data index: the share of required inputs absent, against a declared required set",
    "", "", "", "", "PRESENT",
    "KEEP_AND_SUPPLY", "", "PKG-CAL-BANDS", "P2", "Run 31",
    "Measures completeness and therefore has no abstention of its own, correctly. The band ladder "
    "is unsourced.")

CURATED["C1.2"] = _e(
    "data timeliness: the age of each reported figure against a declared freshness requirement",
    "a declared freshness requirement per field: the maximum acceptable age of each figure and the "
    "authority for it, so that lateness is measured against a standard rather than a chosen number",
    "Freshness Requirement Declaration (field, maximum age, unit, authority)",
    "NEW_PROJECT_DATA_OBJECT", "Reporting Cadence and Freshness Declaration", "ABSENT",
    "KEEP_AND_SUPPLY", "", "PKG-CAT9", "P1", "Run 31",
    "Document dates are extracted, so age is computable; the standard to compare it against is not.")

CURATED["C1.3"] = _e(
    "source reliability weighting: weights on sources derived from their observed reliability",
    "an observed reliability record per source type: how often figures from that source were later "
    "corrected, by how much, over how many observations",
    "Source Reliability Record (source type, observations, correction rate, mean correction "
    "magnitude, window)",
    "DERIVED_FROM_EXISTING_QUALIFIED_DATA", "Source Reliability Record", "PARTIALLY_PRESENT",
    "KEEP_AND_SUPPLY", "", "PKG-CAT9", "P1", "Run 31",
    "Document versioning already exists in this platform, so revisions of the same figure are "
    "observable; nothing currently accumulates them into a reliability estimate.")

CURATED["C1.4"] = _e(
    "audit trail completeness: assessment of the real signal, judgment and audit objects, their "
    "event chronology and the linkage between them, with noncompensatory treatment of critical "
    "fields",
    "the audit object graph itself: signal record ids, judgment record ids, audit event ids, their "
    "timestamps, and the declared linkage between them; plus the designation of which fields are "
    "critical and therefore may not be compensated for by others",
    "Audit Object Graph plus Critical Field Designation",
    "DERIVED_FROM_EXISTING_QUALIFIED_DATA", "Audit Object Graph", "PRESENT_NOT_EXTRACTED",
    "OWNER_DECISION_REQUIRED", "Declared audit field presence check", "PKG-CAT9", "P1", "Run 31",
    "The objects exist in this platform's own database; the module counts declared field presence "
    "instead of assessing them. This is the rare row where the missing structure is already "
    "inside the application rather than outside it.")

CURATED["C1.5"] = _e(
    "information completeness: the share of the declared information set that is present",
    "", "", "", "", "PRESENT",
    "CONSOLIDATE_CANDIDATE", "", "PKG-CAL-BANDS", "P2", "Run 31",
    "Measures completeness against a declared set, as C1.1 does. Whether two registered modules "
    "are needed for completeness is a parsimony question for the owner.")

CURATED["C1.6"] = _e(
    "cross-document consistency: the same fact compared across two or more identified documents",
    "per-field source records: for each extracted figure, the document id, document version, page "
    "or location, and extraction timestamp it came from, so that two documents reporting one fact "
    "can be compared and the disagreeing document named",
    "Field Provenance Record (field, value, document id, document version, location, extracted at)",
    "EXISTING_DOCUMENT_EXTRACTION", "Field-Level Provenance", "PRESENT_NOT_EXTRACTED",
    "KEEP_AND_SUPPLY", "Reported index self-consistency check", "PKG-CAT9", "P0", "Run 31",
    "Every figure compared today comes from the same assembled set, so no fact is compared across "
    "two documents and no document is identified as the source of any disagreement. The merge "
    "layer knows which document won each field; that knowledge is discarded before the module "
    "sees it. P0 because the module's name asserts a cross-document check that never happens.")

CURATED["C1.7"] = _e(
    "reporting frequency: reports received against a declared reporting cadence",
    "the declared reporting cadence: required reporting interval, the document types required each "
    "interval, and the contractual or policy basis for the requirement",
    "Reporting Cadence Declaration", "NEW_PROJECT_DATA_OBJECT",
    "Reporting Cadence and Freshness Declaration", "ABSENT",
    "KEEP_AND_SUPPLY", "", "PKG-CAT9", "P1", "Run 31",
    "Abstains today. Without a required cadence, a count of reports is not a frequency against "
    "anything.")

# ---------------------------------------------------------------- Portfolio Health, D1
CURATED["D1.1"] = _e(
    "isolation forest anomaly detection with an anomaly-score threshold chosen against a stated "
    "error target",
    "a portfolio large enough for the ensemble to mean anything, with a declared cohort definition: "
    "which projects are comparable and why",
    "Portfolio Cohort Definition plus Portfolio Reporting History",
    "PORTFOLIO_REFERENCE_DATASET", "Portfolio Cohort Definition", "PARTIALLY_PRESENT",
    "KEEP_AND_SUPPLY", "", "PKG-PORTFOLIO-HISTORY", "P2", "Run 32",
    "Run 15 made this a real isolation forest per Liu, Ting and Zhou. Its published defaults are "
    "sourced; the band ladder over its score is not, and the cohort it runs on is whatever "
    "projects happen to be in the portfolio.")

CURATED["D1.2"] = _e(
    "portfolio outlier detection: a percentile rank of this project within a defined cohort",
    "a declared cohort: inclusion criteria, minimum cohort size for a percentile to be meaningful, "
    "and the vintage of the cohort's readings",
    "Portfolio Cohort Definition", "PORTFOLIO_REFERENCE_DATASET", "Portfolio Cohort Definition",
    "PARTIALLY_PRESENT",
    "KEEP_AND_SUPPLY", "", "PKG-PORTFOLIO-HISTORY", "P1", "Run 32",
    "An empirical percentile over an undeclared and possibly tiny cohort. registry.py records that "
    "small-n behaviour is unvalidated.")

CURATED["D1.3"] = _e(
    "trajectory classification: a classified trend over a project's history against defined classes",
    "a governed minimum history length and a class definition with boundaries derived from "
    "observed trend distributions rather than chosen",
    "Portfolio Reporting History plus Trend Class Definition",
    "PORTFOLIO_REFERENCE_DATASET", "Portfolio Reporting History", "PARTIALLY_PRESENT",
    "KEEP_AND_SUPPLY", "", "PKG-PORTFOLIO-HISTORY", "P2", "Run 32",
    "Runs on as few as two readings, which is one interval; abstains correctly below that.")

CURATED["D1.4"] = _e(
    "cross-project pattern detection: recurring signal patterns identified across a portfolio",
    "a declared similarity metric with its threshold justified, and a cohort large enough for a "
    "pattern to be distinguishable from coincidence",
    "Portfolio Cohort Definition plus Similarity Metric Declaration",
    "PORTFOLIO_REFERENCE_DATASET", "Portfolio Cohort Definition", "PARTIALLY_PRESENT",
    "KEEP_AND_SUPPLY", "", "PKG-PORTFOLIO-HISTORY", "P2", "Run 32",
    "The similarity radius of 0.15 in a four-dimensional standardised space is a chosen constant.")

CURATED["D1.5"] = _e(
    "a composite anomaly score over independent anomaly evidence",
    "independent anomaly evidence to compose. Read from portfolio.py, this score is the mean of "
    "(a) a standardised Mahalanobis distance, (b) one minus D1.2's own composite percentile rank, "
    "and (c) a term in D1.3's own trend. Two of its at most three terms are other registered "
    "modules' outputs",
    "Declared composition with a dependence structure, or removal of the duplicated terms",
    "DERIVED_FROM_EXISTING_QUALIFIED_DATA", "Portfolio Cohort Definition", "PARTIALLY_PRESENT",
    "CONSOLIDATE_CANDIDATE", "", "PKG-PORTFOLIO-HISTORY", "P0", "Run 32",
    "This is the portfolio double-counting finding, provable from the source rather than asserted: "
    "D1.5 is a strict function of D1.2's and D1.3's internals plus a distance quantity that "
    "portfolio.py itself records as the one formerly mislabelled the isolation forest score. It "
    "does not read D1.1. P0 on lineage grounds.")

CURATED["A3.8"] = _e(
    "parametric cost estimating: an estimating relationship fitted to measurable cost drivers, "
    "with calibrated coefficients and their standard errors",
    "measurable cost drivers for the asset class (quantities, capacities, areas, complexity "
    "descriptors); a population of completed projects carrying those drivers and their realised "
    "costs; the fitted relationship with its functional form; the estimated coefficients with "
    "standard errors; and the fit and validation statistics",
    "Parametric Estimating Relationship (driver set, project population, functional form, "
    "coefficients, standard errors, fit statistics, applicability range)",
    "HISTORICAL_DATASET", "Reference-Class Dataset extended with cost drivers", "ABSENT",
    "KEEP_RESEARCH_ONLY", "Disabled: no parametric estimating relationship is implemented",
    "PKG-REFCLASS", "P3", "Run 28",
    "DISABLED_UNSAFE today and its formula function is never called. A parametric estimate IS the "
    "relationship; without it there is no method to name. It shares the Reference-Class Dataset "
    "with A3.1 and A3.7, so the package that unblocks those is the one that would unblock this.")
