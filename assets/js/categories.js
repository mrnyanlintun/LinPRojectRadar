/* ============================================================
   lin-project-radar — categories.js
   ------------------------------------------------------------
   101 DISTINCT COMPUTATIONS, grouped by what a module's output is FOR
   rather than by legacy category order.

     Group A  Project Health                 53   what condition is the project in
     Group B  Recommendation and Governance    36   what should be done, by whom, under what authority
     Group C  Data and Evidence Health          7   how trustworthy is the evidence base

   The earlier figure of 103 counted two aliases twice. Old 1.3 was an alias of
   old 4.1, and old 3.2 an alias of old 5.1; each pair is now a single entry
   (A4.1 and A5.1). See p0-baseline/MODULE_TAXONOMY.md.

   Numbering and grouping are generated from p0-baseline/module_renumbering_map.csv,
   which is the single source of truth. Each module's method_class, active,
   required and sectors are carried over unchanged: this is a display renumber,
   NOT a rename of the compute contract.

   Group C carries authoringOnly + excludeFromProjectStatus. Those modules still
   COMPUTE, and their results still render in the authoring views, but they do not
   vote in getCategoryStatus or getProjectFusion. Evidence quality is a gate on
   scenario construction, not a description of project condition: a project with
   healthy EVM and a thin document trail is a healthy project recorded on thin
   evidence, and reporting it as Amber conflates the two.


   Globals (no ES modules) so the site runs from file:// too. Loaded BEFORE the
   modules that consume it (categories.js then signals.js then detail.js etc).
   ============================================================ */

/* GENERATED BLOCK. Do not edit by hand.

   Written by server/tools/build_client_taxonomy.py from TWO authorities, and neither
   this file nor its sibling is hand-maintained. Editing the array below cannot change
   what ships: the guard regenerates from the authorities and compares, so a hand edit
   is reverted or caught. Change an authority and regenerate.

     name, method_class, disabled   server/app/simulation/registry.py (and the
                                    dispatch table) -- the identifiers the
                                    production runners actually emit
     everything else                server/tools/taxonomy_authority.json -- category
                                    identity, colour, description, and each module's
                                    id, module_id, required inputs, sectors and level flags

   WHY. categories.js and taxonomy.js each carried a hand-maintained copy of the same
   101-module taxonomy. index.html loads taxonomy.js and not categories.js, so a fix
   made in the wrong copy passed every source check while the live page stayed broken;
   and the two had already drifted apart on their own, with nine modules carrying
   `disabled: true` in one and not the other. */
window.LIN_TAXONOMY_COUNTS = { registered: 45, inService: 45, retired: 0, serverComputes: 45, supplied: 0 };
window.LIN_CATEGORIES = [
  {
    id: 'a1', key: 'A1', name: 'Cost and EVM Performance',
    group: 'A', groupName: 'Project Health',
    color: '#4ea0ff',
    description: 'Cost and schedule performance indices derived from verified pay applications and schedules.',
    modules: [
      { id: 'a1_2', module_id: 'A1.2', name: 'CUSUM Anomaly Monitor', method_class: 'CUSUM', active: true, required: ['spi'] },
      { id: 'a1_5', module_id: 'A1.5', name: 'ARIMA CPI Forecast', method_class: 'ARIMA_Forecast', active: true, required: ['cpiHistory'] },
      { id: 'a1_6', module_id: 'A1.6', name: 'Earned Schedule', method_class: 'Earned_Schedule', active: true, required: ['ev','pv','bac','actualPctComplete','plannedPctComplete'] },
      { id: 'a1_7', module_id: 'A1.7', name: 'TCPI', method_class: 'TCPI', active: true, required: ['bac','ev','ac'] },
      { id: 'a1_8', module_id: 'A1.8', name: 'Variance at Completion', method_class: 'VAC', active: true, required: ['bac','cpi'] },
      { id: 'a1_9', module_id: 'A1.9', name: 'Budget Execution Rate', method_class: 'Budget_Execution_Rate', active: true, required: ['ac','bac','actualPctComplete'] },
      { id: 'a1_11', module_id: 'A1.11', name: 'Independent EAC Reconciliation Index', method_class: 'Independent_EAC_Reconciliation', active: true, required: ['bac','cpi','ev','ac'] }
    ]
  },
  {
    id: 'a2', key: 'A2', name: 'Schedule Performance',
    group: 'A', groupName: 'Project Health',
    color: '#7c5cff',
    description: 'Schedule simulation and critical-path behavior.',
    modules: [
      { id: 'a2_1', module_id: 'A2.1', name: 'PERT Network Criticality', method_class: 'PERT_Network_Criticality', active: true, required: ['spi','bac'] },
      { id: 'a2_7', module_id: 'A2.7', name: 'Milestone Trend Analysis', method_class: 'Milestone_Trend', active: true, required: ['milestoneHistory'] },
      { id: 'a2_8', module_id: 'A2.8', name: 'Look-Ahead Schedule Health', method_class: 'Lookahead_Health', active: true, required: ['activitiesPlanned','activitiesConstrained'] },
      { id: 'a2_9', module_id: 'A2.9', name: 'Resource Loading Index', method_class: 'Resource_Loading', active: true, required: ['plannedLaborHours','actualLaborHours'] }
    ]
  },
  {
    id: 'a3', key: 'A3', name: 'Cost Risk',
    group: 'A', groupName: 'Project Health',
    color: '#22c1a4',
    description: 'Cost risk, contingency and parametric cost behavior.',
    modules: [
      { id: 'a3_2', module_id: 'A3.2', name: 'Contingency Burn Rate', method_class: 'Contingency_Burn_Rate', active: true, required: ['originalContingency','remainingContingency','actualPctComplete'] },
      { id: 'a3_3', module_id: 'A3.3', name: 'Labor Productivity Index', method_class: 'Labor_Productivity', active: true, required: ['plannedLaborHours','actualLaborHours','actualPctComplete'] },
      { id: 'a3_5', module_id: 'A3.5', name: 'Overhead Absorption Rate', method_class: 'Overhead_Absorption', active: true, required: ['indirectCostPlan','indirectCostActual'] },
      { id: 'a3_6', module_id: 'A3.6', name: 'Cost Risk Analysis P80', method_class: 'Cost_Risk_Analysis', active: true, required: ['bac','cpi','ac','ev'] }
    ]
  },
  {
    id: 'a4', key: 'A4', name: 'Document-Derived Condition Signals',
    group: 'A', groupName: 'Project Health',
    color: '#f0a020',
    description: 'Condition signals derived from project documents: RFIs, submittals, change orders and disputes.',
    modules: [
      { id: 'a4_2', module_id: 'A4.2', name: 'RFI Velocity', method_class: 'RFI_Velocity', active: true, required: ['rfiCount','rfiPeriodDays'] },
      { id: 'a4_3', module_id: 'A4.3', name: 'Submittal Rejection Rate', method_class: 'Submittal_Rejection', active: true, required: ['submittalsTotal','submittalsRejected'] },
      { id: 'a4_4', module_id: 'A4.4', name: 'NCR Rate', method_class: 'NCR_Rate', active: true, required: ['ncrIssued','ncrClosed','ncrOpen'], sectors: ['construction','hybrid'] },
      { id: 'a4_5', module_id: 'A4.5', name: 'Weather Day Impact', method_class: 'Weather_Impact', active: true, required: ['weatherDaysLost'], sectors: ['construction','hybrid'] },
      { id: 'a4_6', module_id: 'A4.6', name: 'Change Order Frequency', method_class: 'CO_Frequency', active: true, required: ['changeOrderCount','baselineContractSum','revisedContractSum'] },
      { id: 'a4_7', module_id: 'A4.7', name: 'Dispute Escalation Index', method_class: 'Dispute_Escalation', active: true, required: ['docRiskScore','rfiCount','changeOrderCount'] },
      { id: 'a4_8', module_id: 'A4.8', name: 'Subcontractor Performance', method_class: 'Subcontractor_Performance', active: true, required: ['subcontractorComplianceScore'], sectors: ['construction','hybrid'] },
      { id: 'a4_9', module_id: 'A4.9', name: 'Procurement Lead Time Monitor', method_class: 'Procurement_Lead_Time', active: true, required: ['longLeadItemsTotal','longLeadAtRisk','longLeadDelayed'], sectors: ['construction','hybrid'] }
    ]
  },
  {
    id: 'a6', key: 'A6', name: 'Delivery Quality Performance',
    group: 'A', groupName: 'Project Health',
    color: '#8fb69a',
    description: 'Delivery quality, safety, environmental and contractor performance. These describe how the work is being delivered, not who must authorize a response.',
    modules: [
      { id: 'a6_1', module_id: 'A6.1', name: 'Quality Compliance Index', method_class: 'Quality_Compliance', active: true, required: ['qualityDeficienciesNoted'] },
      { id: 'a6_2', module_id: 'A6.2', name: 'Safety Performance Index', method_class: 'Safety_Performance', active: true, required: ['safetyIncidentsDiscussed'], sectors: ['construction','hybrid'] },
      { id: 'a6_3', module_id: 'A6.3', name: 'Environmental Compliance Rate', method_class: 'Environmental_Compliance', active: true, required: ['environmentalIssuesDiscussed'], sectors: ['construction','hybrid'] },
      { id: 'a6_4', module_id: 'A6.4', name: 'Contractor Performance Assessment Signal', method_class: 'Contractor_Performance', active: true, required: ['overallRating','scheduleRating','costRating'] }
    ]
  },
  {
    id: 'b1', key: 'B1', name: 'Signal Synthesis',
    group: 'B', groupName: 'Recommendation and Governance',
    color: '#ffd05a',
    description: 'Synthesis of the assembled signal set into a single recommended posture.',
    modules: [
      { id: 'b1_1', module_id: 'B1.1', name: 'Conservative Dominance', method_class: 'Conservative_Dominance', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'b1_2', module_id: 'B1.2', name: 'Weighted Voting', method_class: 'Weighted_Voting', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'b1_3', module_id: 'B1.3', name: 'Majority Rules', method_class: 'Majority_Rules', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'b1_4', module_id: 'B1.4', name: 'Worst-N-of-M', method_class: 'Worst_N_of_M', active: true, required: ['cpi','spi','docRiskScore'] }
    ]
  },
  {
    id: 'b2', key: 'B2', name: 'Evidence Combination',
    group: 'B', groupName: 'Recommendation and Governance',
    color: '#5ed7ff',
    description: 'Evidence combination under uncertainty: fuzzy, rough, neutrosophic and belief-function methods.',
    modules: [
      { id: 'b2_18', module_id: 'B2.18', name: 'MARCOS Ranking', method_class: 'MARCOS', active: true, required: ['cpi','spi','docRiskScore'] }
    ]
  },
  {
    id: 'b3', key: 'B3', name: 'Regulatory and Authority Thresholds',
    group: 'B', groupName: 'Recommendation and Governance',
    color: '#e0556b',
    description: 'Regulatory and authority thresholds that determine who must act and at what level.',
    modules: [
      { id: 'b3_1', module_id: 'B3.1', name: 'Agent-Based Governance Model', method_class: 'ABM_Governance', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'b3_2', module_id: 'B3.2', name: 'FAR/Agency EVMS Applicability Monitor', method_class: 'EVMS_Applicability', active: true, required: ['bac','cpi','ev','ac'] },
      { id: 'b3_3', module_id: 'B3.3', name: 'Versioned A-11 Capital Programming Conformance Check', method_class: 'A11_Conformance', active: true, required: ['bac','cpi','actualPctComplete'] },
      { id: 'b3_4', module_id: 'B3.4', name: 'EVMS Reporting Compliance Monitor', method_class: 'EVMS_Reporting_Compliance', active: true, required: ['bac','cpi','spi'] },
      { id: 'b3_5', module_id: 'B3.5', name: 'Contract Modification Governance Check', method_class: 'Modification_Governance', active: true, required: ['changeOrderCount','baselineContractSum','revisedContractSum'] }
    ]
  },
  {
    id: 'b4', key: 'B4', name: 'Decision Optimization',
    group: 'B', groupName: 'Recommendation and Governance',
    color: '#a78bfa',
    description: 'Decision optimisation and trade-off analysis over the available courses of action.',
    modules: [
      { id: 'b4_3', module_id: 'B4.3', name: 'Constraint Satisfaction Analysis', method_class: 'Constraint_Satisfaction', active: true, required: ['cpi','spi','bac'] }
    ]
  },
  {
    id: 'c1', key: 'C1', name: 'Data Integrity',
    group: 'C', groupName: 'Data and Evidence Health',
    color: '#94a3b8',
    description: 'Evidence quality of the underlying document set. Authoring-time only: these describe how trustworthy the evidence is, never the condition of the project.',
    modules: [
      { id: 'c1_1', module_id: 'C1.1', name: 'Missing Data Index', method_class: 'Missing_Data_Index', active: true, authoringOnly: true, excludeFromProjectStatus: true, required: ['bac'] },
      { id: 'c1_2', module_id: 'C1.2', name: 'Data Timeliness Score', method_class: 'Data_Timeliness_Score', active: true, authoringOnly: true, excludeFromProjectStatus: true, required: ['docDate'] },
      { id: 'c1_3', module_id: 'C1.3', name: 'Source Reliability Weighting', method_class: 'Source_Reliability_Weighting', active: true, authoringOnly: true, excludeFromProjectStatus: true, required: ['bac'] },
      { id: 'c1_4', module_id: 'C1.4', name: 'Audit Trail Completeness', method_class: 'Audit_Trail_Completeness', active: true, authoringOnly: true, excludeFromProjectStatus: true, required: ['bac'] },
      { id: 'c1_5', module_id: 'C1.5', name: 'Information Completeness Ratio', method_class: 'Information_Completeness_Ratio', active: true, authoringOnly: true, excludeFromProjectStatus: true, required: ['bac'] },
      { id: 'c1_6', module_id: 'C1.6', name: 'Cross-document Consistency Score', method_class: 'Cross_Doc_Consistency', active: true, authoringOnly: true, excludeFromProjectStatus: true, required: ['ev','ac'] },
      { id: 'c1_7', module_id: 'C1.7', name: 'Reporting Frequency Index', method_class: 'Reporting_Frequency_Index', active: true, authoringOnly: true, excludeFromProjectStatus: true, required: ['docDate'] }
    ]
  }
];


/* ------------------------------------------------------------
   Sector relevance. Construction-phase modules carry an optional
   `sectors` tag; for a project whose sector is outside that list
   the module abstains with the distinct 'NA' status (excluded
   from category fusion, rendered dim with an explanation).
   ------------------------------------------------------------ */
var LIN_MODULE_SECTORS = null; // method_class → sectors[] (lazy, built once)
function moduleSectorMap() {
  if (LIN_MODULE_SECTORS) return LIN_MODULE_SECTORS;
  LIN_MODULE_SECTORS = {};
  window.LIN_CATEGORIES.forEach(function (c) {
    (c.modules || []).forEach(function (m) {
      if (m.sectors && m.sectors.length) LIN_MODULE_SECTORS[m.method_class] = m.sectors;
    });
  });
  return LIN_MODULE_SECTORS;
}
// Normalise the project sector the same way app.js plots it: the legacy
// "combined" alias and a missing sector both read as hybrid.
window.normalizeSector = function (sector) {
  var s = String(sector || "hybrid").toLowerCase();
  return s === "combined" ? "hybrid" : s;
};
/* True when this module carries sector tags that exclude the project's sector. */
window.isModuleSectorNA = function (methodClass, project) {
  var sectors = moduleSectorMap()[methodClass];
  if (!sectors) return false;
  return sectors.indexOf(window.normalizeSector(project && project.sector)) < 0;
};
/* The modules of one category that are N/A for this project's sector —
   drives the one-line explanatory note under the category header. */
window.categoryNAModules = function (catId, project) {
  var cat = LIN_CATEGORIES.find(function (c) { return c.id === catId; });
  if (!cat) return [];
  return cat.modules.filter(function (m) {
    return window.isModuleSectorNA(m.method_class, project);
  });
};
/* RUN 97, GOAL ONE. THE PORTFOLIO-LEVEL DISTINCTION IS GONE, BECAUSE THERE IS NO
   PORTFOLIO-LEVEL CATEGORY LEFT TO DISTINGUISH.

   `isPortfolioLevelCategory` and `projectLevelCategories` existed to hold ONE category out of
   the roster: D1 Portfolio Health, whose five modules were retired at Run 43 and which Run 97
   removes from the taxonomy authority entirely. With D1 gone, a filter separating project-level
   from portfolio-level categories separated the roster from nothing -- it returned every
   category it was given -- while reading on the page as though a real exclusion were happening.
   Six callers carried that filter; all six now read the roster directly.

   Nothing about which categories the charts draw has changed: that is
   `window.performanceCategories()` below, which is a DIFFERENT and still-live rule -- the five
   weighted performance categories A1 A2 A3 A4 A6. */
/* The 10 project-level categories in display order (Portfolio Health excluded) —
   the canonical list for anything rendering a gapless 1-10 sequence. */
/* ------------------------------------------------------------
   Does this category describe the CONDITION of the project?

   Group C (Data and Evidence Health) does not. Its modules measure how trustworthy the evidence
   base is, which is a quality gate on scenario construction, not a property of the project. A
   project with healthy EVM recorded on a thin document trail is a healthy project recorded on
   thin evidence; folding the thinness into the status conflates the two and would have made
   every early-period scenario look worse than it is.

   Group C modules still COMPUTE and still render in the authoring views. They are excluded here
   and nowhere else, so nothing about their computation changes.
   ------------------------------------------------------------ */
window.contributesToProjectStatus = function (cat) {
  if (!cat) return false;
  if (cat.parked) return false;
  return !cat.excludeFromProjectStatus;
};

window.projectLevelCategories = function () {
  return LIN_CATEGORIES.slice();
};

/* Per-module status lookup. Reads from live project shape:
     project.signals.{mc,cusum,doc,decision}.status / .state
     project.simulationSignals.signal_array[*].method_class / .status_color
   Returns null when the module hasn't been computed yet (or is inactive /
   returned insufficient-data and was filtered out of the signal array).
   Returns the string 'NA' when the module's `sectors` tag excludes this
   project's sector — a deliberate abstention, distinct from "no data yet". */
/* HISTORICAL METHOD-CLASS ALIASES, FOR STORED ROWS ONLY.

   A stored period result carries the method class the runner emitted WHEN IT WAS COMPUTED. Runs
   28, 31 and 32 renamed six identities' method classes, so a row written before those runs
   carries the superseded identifier and a lookup on the current one would miss it.

   THE CURRENT IDENTIFIER IS ALWAYS THE PRIMARY. These are only ever matched against; nothing
   emits them, no taxonomy row carries them, and an alias must never become the key a surface
   displays or a generator writes.

   The consequence of NOT having had this is on record: the client taxonomy carried the
   superseded identifiers for these six modules, `findSim` matched none of them against the
   server's signal array, and the lookup returned null rather than failing -- a status that
   silently never rendered. */
window.LIN_HISTORICAL_METHOD_CLASS = {
  CPI_Shrinkage_Forecast: ["Regression_To_Mean"],
  Independent_EAC_Reconciliation: ["ICE_Ratio"],
  EVMS_Applicability: ["FAR_Threshold"],
  A11_Conformance: ["OMB_A11_Check"],
  EVMS_Reporting_Compliance: ["EVM_Reporting_Threshold"],
  Modification_Governance: ["Contract_Mod_Frequency"],
  Minimax_Regret_Decision_Rule: ["Regret_Minimization"],
  DSM_Rework_Cat5: ["DSM_Rework_Propagation"]
};
window.linMethodClassMatches = function (candidate, wanted) {
  if (candidate === wanted) return true;
  var alt = window.LIN_HISTORICAL_METHOD_CLASS[wanted];
  return !!alt && alt.indexOf(candidate) !== -1;
};

window.getModuleStatus = function (methodClass, project) {
  if (!project) return null;
  if (window.isModuleSectorNA(methodClass, project)) return "NA";
  const s = project.signals || {};
  const sim = (project.simulationSignals && project.simulationSignals.signal_array) || [];
  const findSim = (cls) => {
    // Matches the CURRENT identifier, and a superseded one only for rows stored before the
    // rename. Comparing on equality alone is what made six modules' status silently absent.
    const found = sim.find((m) => window.linMethodClassMatches(m.method_class, cls));
    return found ? (found.status_color || found.status || null) : null;
  };
  switch (methodClass) {
    // Cat 1 core EVM signals live on project.signals, not the sim array.
    case "Monte_Carlo":
    case "monte_carlo":            return s.mc ? s.mc.status : null;
    case "CUSUM":
    case "cusum":                  return s.cusum ? s.cusum.status : null;
    case "Doc_Risk":
    case "Doc_Risk_Cat4":
    case "doc_risk":               return s.doc ? s.doc.status : null;
    // Synthesis + governance dominance read the PCEIF decision state.
    case "Conservative_Dominance":
    case "conservative_dominance":
    case "ABM_Governance":
    case "abm_governance":         return s.decision ? s.decision.state : null;
    // Cat 5.1 reuses the Cat 3 DSM result under a distinct method_class.
    // RUN 32 FINAL CLOSURE. This TRANSLATED the current identifier into `DSM_Rework_Propagation`,
    // which no runner emits: the server stamps `DSM_Rework_Cat5`. The remap therefore turned a
    // working lookup into a guaranteed miss, and a miss returns null rather than failing, so
    // A5.1's status silently never rendered. The current identifier is passed through and the
    // superseded one is carried in the historical alias map for rows stored under it.
    case "DSM_Rework_Cat5":        return findSim(methodClass);
    // Portfolio Health (ex-"Cat 8" ML/AI) — results come from the
    // portfolioanalyze POST and are merged into the simulation signal_array
    // like the other sim modules.
    case "Isolation_Forest":
    case "Portfolio_Outlier":
    case "Trajectory_Classifier":
    case "Cross_Project_Pattern":
    case "Anomaly_Score":          return findSim(methodClass);
    // Cat 9 — Data Integrity & Information Quality (compute from existing
    // signalInputs + the project audit trail).
    case "Missing_Data_Index":
    case "Data_Timeliness_Score":
    case "Source_Reliability_Weighting":
    case "Audit_Trail_Completeness":
    case "Information_Completeness_Ratio":
    case "Cross_Doc_Consistency":
    case "Reporting_Frequency_Index":
    // Cat 10 — Decision Optimization (compute from existing signalInputs).
    case "Multi_Objective_Optimization":
    case "Linear_Programming":
    case "Constraint_Satisfaction":
    case "WhatIf_Scenario_Matrix":
    case "Decision_Sensitivity_Matrix":
    case "Pareto_Frontier":
    // RUN 32 FINAL CLOSURE: the current method class. The old identifier is kept beside it
    // so a STORED row written before the section-3 rename still routes; nothing emits it.
    case "Minimax_Regret_Decision_Rule":
    case "Regret_Minimization":    return findSim(methodClass);
    default:                       return findSim(methodClass);
  }
};

/* Worst-status-wins per category. Returns null for parked categories or
   categories whose modules haven't been computed yet. */
window.getCategoryStatus = function (catId, project) {
  const cat = LIN_CATEGORIES.find((c) => c.id === catId);
  if (!cat || cat.parked) return null;
  // Deliberately still computed for Group C: the authoring views show it. It is the PROJECT
  // rollup in getProjectFusion that ignores it, not this function.
  const statuses = cat.modules
    .map((m) => getModuleStatus(m.method_class, project))
    .filter(Boolean)
    // NA = sector abstention — excluded from the fusion vote like any abstain
    .filter((s) => s !== "NA")
    .map((s) => String(s));
  if (!statuses.length) return null;
  // Dempster-Shafer evidence fusion (Red weighted 1.5x) instead of
  // worst-status-wins, so a single Red module can't sink a category full of
  // greens. Uses the shared fuser in simulations.js. Falls back to keyword
  // worst-wins only if that module hasn't loaded.
  if (window.LinSimulations && LinSimulations.dstFuse) {
    const fused = LinSimulations.dstFuse(statuses);
    if (fused && fused.status) return fused.status;
  }
  const has = (label) => statuses.some((s) => s.toLowerCase().indexOf(label) >= 0);
  if (has("red")) return "Red";
  if (has("amber") || has("orange")) return "Amber";
  if (has("yellow") || has("light-amber")) return "Yellow";
  if (has("green")) return "Green";
  if (has("complete") || has("blue")) return "Complete";
  return null;
};

/* ------------------------------------------------------------
   Project-level rollup — fuse all 11 registry category statuses (10 project
   categories + Portfolio Health; again via Dempster-Shafer, Red weighted
   1.5x) into the project status. UNCHANGED by the display renumber —
   Portfolio Health still votes here, it just isn't shown as "Cat 8" anymore.
   Also surfaces: the conflict K (Red-review advisory when >= 0.55),
   every currently-Red module + its category (so the brief can flag
   them even on a Green project), and Complete + liability handling.
   ------------------------------------------------------------ */
function projectCompletionDate_(project) {
  const si = (project && project.signalInputs) || {};
  if (si.baselineEnd) return si.baselineEnd;
  if (project && project.signals && project.signals.evm && project.signals.evm.dataDate) {
    return project.signals.evm.dataDate;
  }
  if (project && project.reportingPeriod) return project.reportingPeriod + "-01";
  return null;
}
window.projectCompletionDate = projectCompletionDate_;
/* ------------------------------------------------------------
   Canonical status-decision helper — the ONE place the Complete
   promotion + liability rule is implemented. Called by getProjectFusion
   (live, full-object render paths) AND by the signal-run finalization
   in signals.js (so the PERSISTED project.status — the only field the
   slim/listslim portfolio-list path can read — carries the same
   promotion the map/radar/detail already compute live). Pure function:
   fusedStatus is the raw DST-fused band (Green/Yellow/Amber/Red/null);
   signalInputs supplies actualPctComplete + the completion-date fields;
   sector drives the 2-year Construction/Hybrid liability tail. ------ */
window.deriveProjectStatus = function (fusedStatus, signalInputs, sector, completionDate) {
  const si = signalInputs || {};
  const v = si.actualPctComplete != null ? si.actualPctComplete : si.pctComplete;
  const pct = Number(v);
  const out = { status: fusedStatus || null, complete: false, completionDate: null, liabilityUntil: null };
  if (!Number.isFinite(pct) || pct < 100) return out;

  out.status = "Complete";
  out.complete = true;
  const cDate = completionDate ||
    si.baselineEnd ||
    null;
  out.completionDate = cDate;
  const sec = String(sector || "").toLowerCase();
  if ((sec === "construction" || sec === "hybrid" || sec === "combined") && cDate) {
    const d = new Date(cDate);
    if (!isNaN(d.getTime())) {
      d.setFullYear(d.getFullYear() + 2);
      out.liabilityUntil = d.toISOString().slice(0, 10);
    }
  }
  return out;
};

window.getProjectFusion = function (project) {
  if (!project) return null;
  // Group C is excluded here: evidence quality is not project condition. Everything else,
  // including Portfolio Health, still votes exactly as before.
  const catStatuses = LIN_CATEGORIES
    .filter((c) => window.contributesToProjectStatus(c))
    .map((c) => getCategoryStatus(c.id, project))
    .filter(Boolean);

  let fused = null;
  if (window.LinSimulations && LinSimulations.dstFuse) fused = LinSimulations.dstFuse(catStatuses);

  // Every Red module + its category — for the executive brief flags list, so a
  // Green/Yellow project still surfaces its Red modules (nothing hidden by fusion).
  const redFlags = [];
  LIN_CATEGORIES.forEach((c) => {
    // Same exclusion as the fusion vote. A Red on an evidence-quality module belongs in the
    // authoring report, not in a participant-facing brief about the project.
    if (!window.contributesToProjectStatus(c)) return;
    (c.modules || []).forEach((m) => {
      const st = window.getModuleStatus ? getModuleStatus(m.method_class, project) : null;
      if (st && String(st).toLowerCase().indexOf("red") >= 0) {
        redFlags.push({ category: c.key, categoryName: c.name, module: m.name, module_id: m.module_id });
      }
    });
  });

  const conflict = fused ? fused.conflict : 0;
  const out = {
    status: fused ? fused.status : null,   // Green / Yellow / Amber / Red (or null = awaiting)
    mass: fused ? fused.mass : null,
    conflict: conflict,
    redReview: conflict >= 0.55,           // advisory flag only — does NOT override the band
    redFlags: redFlags,
    categoryStatuses: catStatuses
  };

  // Complete (blue) is a project-end flag set by actual % complete == 100,
  // independent of DST. Construction/Hybrid then carry a 2-year liability tail.
  // Delegates to the canonical deriveProjectStatus so this live path and the
  // persisted-at-finalization path (signals.js) can never disagree.
  const completionDate = projectCompletionDate_(project);
  const decided = window.deriveProjectStatus(out.status, project.signalInputs, project.sector, completionDate);
  out.status = decided.status;
  if (decided.complete) {
    out.complete = true;
    out.completionDate = decided.completionDate;
    if (decided.liabilityUntil) out.liabilityUntil = decided.liabilityUntil;
  }
  return out;
};
