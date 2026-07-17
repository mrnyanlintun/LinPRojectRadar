/* ============================================================
   lin-project-radar — categories.js
   ------------------------------------------------------------
   The full 103-module definition across 10 PROJECT-LEVEL categories
   (display-numbered 1-10, gapless) plus the PORTFOLIO-LEVEL "Portfolio
   Health" suite (ML & AI Pattern Detection, 5 modules, numbered PH.1-PH.5,
   NOT part of the 1-10 sequence — it compares a project against the rest
   of the portfolio, not the project in isolation).

   Every entry's internal `id` (cat1..cat11, cat9_1, etc.) is STABLE and
   never renumbered — sessionStorage keys, deep-link anchors, and CSS hooks
   all key off `id`. The USER-VISIBLE number lives entirely in `num`
   ('Cat 1'..'Cat 10' for project categories, 'PH' for the portfolio suite;
   module nums 'N.M' or 'PH.M'). Anything that renders a category/module
   number MUST read `num`, never derive it from array position or the
   internal id. The Portfolio Health category also carries
   `level: 'portfolio'` so renderers can route it to the Health dialog
   instead of the numbered 1-10 sequence.

   Registry order (internal, for iteration) is unchanged from the original
   11-category rollout: cat1..cat7, cat8 (Portfolio Health), cat9..cat11.
   Display numbers:
     cat1..cat7   → Cat 1..Cat 7   (unchanged)
     cat8         → 'PH'            (Portfolio Health — was 'Cat 8')
     cat9         → 'Cat 8'         (Governance & Compliance — was 'Cat 9')
     cat10        → 'Cat 9'         (Data Integrity — was 'Cat 10')
     cat11        → 'Cat 10'        (Decision Optimization — was 'Cat 11')

   Every module carries: id, num, name, method_class, active
   (true/false) and required (input keys it needs to compute).

   Portfolio Health (ex-"Cat 8") is active — its 5 modules compute via the
   portfolioanalyze endpoint and render in the Health dialog, not on any
   single project's detail page. Many project-category modules now compute
   from fields derived from the existing document set (see signals.js
   deriveExtendedFields), tagged [est.] in the UI.

   Cat 9 (Data Integrity) and Cat 10 (Decision Optimization) are fully
   active — they derive from existing signalInputs and the project audit
   trail.

   Fusion/status math is UNCHANGED by this renumber: getProjectFusion still
   fuses all 11 registry entries (including Portfolio Health) via
   Dempster-Shafer — only the DISPLAY layer (num, grouping, dialogs) changed.

   Globals (no ES modules) so the site runs from file:// too.
   Loaded BEFORE the modules that consume it (categories.js
   then signals.js then detail.js etc — see index.html).
   ============================================================ */

window.LIN_CATEGORIES = [
  {
    id: 'cat1', num: 'Cat 1', name: 'Quantitative EVM',
    color: '#4ea0ff',
    description: 'Cost and schedule performance indices derived from verified pay applications and schedules.',
    modules: [
      { id: 'cat1_1', num: '1.1', name: 'Monte Carlo EAC Forecast', method_class: 'Monte_Carlo', active: true, required: ['bac','cpi','spi'] },
      { id: 'cat1_2', num: '1.2', name: 'CUSUM Anomaly Monitor', method_class: 'CUSUM', active: true, required: ['spi'] },
      { id: 'cat1_3', num: '1.3', name: 'Document Risk Extraction', method_class: 'Doc_Risk', active: true, required: ['docRiskScore'] },
      { id: 'cat1_4', num: '1.4', name: 'Bayesian EAC', method_class: 'Bayesian_EAC', active: true, required: ['bac','ev','ac','cpi'] },
      { id: 'cat1_5', num: '1.5', name: 'Kalman Filter SPI Smoother', method_class: 'Kalman_Filter', active: true, required: ['spi','spiHistory'] },
      { id: 'cat1_6', num: '1.6', name: 'ARIMA CPI Forecast', method_class: 'ARIMA_Forecast', active: true, required: ['cpiHistory'] },
      { id: 'cat1_7', num: '1.7', name: 'Earned Schedule', method_class: 'Earned_Schedule', active: true, required: ['ev','pv','bac','actualPctComplete','plannedPctComplete'] },
      { id: 'cat1_8', num: '1.8', name: 'TCPI', method_class: 'TCPI', active: true, required: ['bac','ev','ac'] },
      { id: 'cat1_9', num: '1.9', name: 'Variance at Completion', method_class: 'VAC', active: true, required: ['bac','cpi'] },
      { id: 'cat1_10', num: '1.10', name: 'Budget Execution Rate', method_class: 'Budget_Execution_Rate', active: true, required: ['ac','bac','actualPctComplete'] },
      { id: 'cat1_11', num: '1.11', name: 'Regression to Mean CPI', method_class: 'Regression_To_Mean', active: true, required: ['cpi','cpiHistory'] },
      { id: 'cat1_12', num: '1.12', name: 'ICE Ratio', method_class: 'ICE_Ratio', active: true, required: ['bac','cpi','ev','ac'] }
    ]
  },
  {
    id: 'cat2', num: 'Cat 2', name: 'Schedule Simulation',
    color: '#2dd4bf',
    description: 'Time-based leading indicators that surface schedule risk before it registers in SPI.',
    modules: [
      { id: 'cat2_1', num: '2.1', name: 'PERT Network Criticality', method_class: 'PERT_Network_Criticality', active: true, required: ['spi','bac'] },
      { id: 'cat2_2', num: '2.2', name: 'Line of Balance', method_class: 'Line_of_Balance_Velocity', active: true, required: ['spi','actualPctComplete','plannedPctComplete'] },
      { id: 'cat2_3', num: '2.3', name: 'CCPM Buffer Health', method_class: 'CCPM_Buffer_Health', active: true, required: ['actualPctComplete','plannedPctComplete'] },
      { id: 'cat2_4', num: '2.4', name: 'Schedule Compression Index', method_class: 'Schedule_Compression', active: true, required: ['baselineEnd','baselineStart','actualPctComplete'] },
      { id: 'cat2_5', num: '2.5', name: 'Float Consumption Rate', method_class: 'Float_Consumption', active: true, required: ['totalFloat','consumedFloat'] },
      { id: 'cat2_6', num: '2.6', name: 'S-Curve Deviation', method_class: 'SCurve_Deviation', active: true, required: ['actualPctComplete','plannedPctComplete','ev','pv'] },
      { id: 'cat2_7', num: '2.7', name: 'Milestone Trend Analysis', method_class: 'Milestone_Trend', active: true, required: ['milestoneHistory'] },
      { id: 'cat2_8', num: '2.8', name: 'Look-Ahead Schedule Health', method_class: 'Lookahead_Health', active: true, required: ['activitiesPlanned','activitiesConstrained'] },
      { id: 'cat2_9', num: '2.9', name: 'Resource Loading Index', method_class: 'Resource_Loading', active: true, required: ['plannedLaborHours','actualLaborHours'] },
      { id: 'cat2_10', num: '2.10', name: 'Schedule Risk Analysis P80', method_class: 'Schedule_Risk_Analysis', active: true, required: ['spi','baselineEnd','baselineStart','actualPctComplete'] },
      { id: 'cat2_11', num: '2.11', name: 'Critical Path Index', method_class: 'Critical_Path_Index', active: true, required: ['spi','plannedPctComplete','actualPctComplete'] }
    ]
  },
  {
    id: 'cat3', num: 'Cat 3', name: 'Cost Simulation',
    color: '#e9a23b',
    description: 'Budget-based leading indicators correcting for optimism bias in contractor estimates.',
    modules: [
      { id: 'cat3_1', num: '3.1', name: 'Reference Class Forecasting', method_class: 'Reference_Class_Forecasting', active: true, required: ['bac','cpi'] },
      { id: 'cat3_2', num: '3.2', name: 'DSM Rework Propagation', method_class: 'DSM_Rework_Propagation', active: true, required: ['cpi','spi'] },
      { id: 'cat3_3', num: '3.3', name: 'Contingency Burn Rate', method_class: 'Contingency_Burn_Rate', active: true, required: ['originalContingency','remainingContingency','actualPctComplete'] },
      { id: 'cat3_4', num: '3.4', name: 'Labor Productivity Index', method_class: 'Labor_Productivity', active: true, required: ['plannedLaborHours','actualLaborHours','actualPctComplete'] },
      { id: 'cat3_5', num: '3.5', name: 'Material Cost Variance', method_class: 'Material_Cost_Variance', active: true, required: ['materialCostBaseline','materialCostCurrent'] },
      { id: 'cat3_6', num: '3.6', name: 'Overhead Absorption Rate', method_class: 'Overhead_Absorption', active: true, required: ['indirectCostPlan','indirectCostActual'] },
      { id: 'cat3_7', num: '3.7', name: 'Cost Risk Analysis P80', method_class: 'Cost_Risk_Analysis', active: true, required: ['bac','cpi','ac','ev'] },
      { id: 'cat3_8', num: '3.8', name: 'Analogous Estimating Ratio', method_class: 'Analogous_Estimating', active: true, required: ['analogousOverrunPct','bac'] },
      { id: 'cat3_9', num: '3.9', name: 'Parametric Cost Index', method_class: 'Parametric_Cost', active: true, required: ['bac','ev','ac','actualPctComplete'] },
      { id: 'cat3_10', num: '3.10', name: 'Inflation Adjustment Index', method_class: 'Inflation_Adjustment', active: true, required: ['materialCostBaseline','materialCostCurrent'] }
    ]
  },
  {
    id: 'cat4', num: 'Cat 4', name: 'Document & Risk Signals',
    color: '#f59e0b',
    description: 'Qualitative signals from project records that lead EVM by weeks.',
    modules: [
      { id: 'cat4_1', num: '4.1', name: 'Document Risk Score', method_class: 'Doc_Risk_Cat4', active: true, required: ['docRiskScore'] },
      { id: 'cat4_2', num: '4.2', name: 'RFI Velocity', method_class: 'RFI_Velocity', active: true, required: ['rfiCount','rfiPeriodDays'] },
      { id: 'cat4_3', num: '4.3', name: 'Submittal Rejection Rate', method_class: 'Submittal_Rejection', active: true, required: ['submittalsTotal','submittalsRejected'] },
      { id: 'cat4_4', num: '4.4', name: 'NCR Rate', method_class: 'NCR_Rate', active: true, required: ['ncrIssued','ncrClosed','ncrOpen'], sectors: ['construction','hybrid'] },
      { id: 'cat4_5', num: '4.5', name: 'Weather Day Impact', method_class: 'Weather_Impact', active: true, required: ['weatherDaysLost'], sectors: ['construction','hybrid'] },
      { id: 'cat4_6', num: '4.6', name: 'Change Order Frequency', method_class: 'CO_Frequency', active: true, required: ['changeOrderCount','baselineContractSum','revisedContractSum'] },
      { id: 'cat4_7', num: '4.7', name: 'Dispute Escalation Index', method_class: 'Dispute_Escalation', active: true, required: ['docRiskScore','rfiCount','changeOrderCount'] },
      { id: 'cat4_8', num: '4.8', name: 'Subcontractor Performance', method_class: 'Subcontractor_Performance', active: true, required: ['subcontractorComplianceScore'], sectors: ['construction','hybrid'] },
      { id: 'cat4_9', num: '4.9', name: 'Procurement Lead Time Monitor', method_class: 'Procurement_Lead_Time', active: true, required: ['longLeadItemsTotal','longLeadAtRisk','longLeadDelayed'], sectors: ['construction','hybrid'] },
      { id: 'cat4_10', num: '4.10', name: 'Specification Conflict Density', method_class: 'Spec_Conflict_Density', active: true, required: ['docRiskScore','rfiCount'] }
    ]
  },
  {
    id: 'cat5', num: 'Cat 5', name: 'System Dynamics & Complexity',
    color: '#8b5cf6',
    description: 'How project components interact, amplify, and propagate risk through the system.',
    modules: [
      { id: 'cat5_1', num: '5.1', name: 'DSM Rework Propagation', method_class: 'DSM_Rework_Cat5', active: true, required: ['cpi','spi'] },
      { id: 'cat5_2', num: '5.2', name: 'Sensitivity Analysis', method_class: 'Sensitivity_Analysis', active: true, required: ['bac','ev','ac','pv','cpi','spi'] },
      { id: 'cat5_3', num: '5.3', name: 'Tornado Risk Ranking', method_class: 'Tornado_Diagram', active: true, required: ['cpi','spi','docRiskScore','actualPctComplete','plannedPctComplete'] },
      { id: 'cat5_4', num: '5.4', name: 'Scenario Modeling', method_class: 'Scenario_Modeling', active: true, required: ['bac','ev','ac','cpi','spi'] },
      { id: 'cat5_5', num: '5.5', name: 'Rework Feedback Loop', method_class: 'Rework_Feedback', active: true, required: ['cpi','rfiCount','changeOrderCount'] },
      { id: 'cat5_6', num: '5.6', name: 'Queueing Theory Bottleneck', method_class: 'Queueing_Bottleneck', active: true, required: ['activitiesPlanned','activitiesConstrained'] },
      { id: 'cat5_7', num: '5.7', name: 'Agent-Based Supply Chain', method_class: 'Agent_Supply_Chain', active: true, required: ['longLeadItemsTotal','longLeadAtRisk'] },
      { id: 'cat5_8', num: '5.8', name: 'Discrete Event Simulation', method_class: 'Discrete_Event_Sim', active: true, required: ['spi','actualPctComplete','plannedPctComplete','cpi'] }
    ]
  },
  {
    id: 'cat6', num: 'Cat 6', name: 'Signal Synthesis',
    color: '#e2b13c',
    description: 'Deterministic baseline classification — the worst signal wins.',
    modules: [
      { id: 'cat6_1', num: '6.1', name: 'Conservative Dominance', method_class: 'Conservative_Dominance', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'cat6_2', num: '6.2', name: 'Weighted Voting', method_class: 'Weighted_Voting', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'cat6_3', num: '6.3', name: 'Majority Rules', method_class: 'Majority_Rules', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'cat6_4', num: '6.4', name: 'Worst-N-of-M', method_class: 'Worst_N_of_M', active: true, required: ['cpi','spi','docRiskScore'] }
    ]
  },
  {
    id: 'cat7', num: 'Cat 7', name: 'Evidence Combination',
    color: '#9b6dff',
    description: 'Uncertainty reasoning — quantifies confidence in the classification across 20 mathematical frameworks.',
    modules: [
      { id: 'cat7_1', num: '7.1', name: 'Dempster-Shafer', method_class: 'DST_Evidence_Combination', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'cat7_2', num: '7.2', name: 'Rough Sets', method_class: 'Rough_Sets_Classification', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'cat7_3', num: '7.3', name: 'Neutrosophic Logic', method_class: 'Neutrosophic_Logic', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'cat7_4', num: '7.4', name: 'Interval Fuzzy Sets', method_class: 'Interval_Fuzzy_Sets', active: true, required: ['cpi','spi'] },
      { id: 'cat7_5', num: '7.5', name: 'Z-numbers', method_class: 'Z_Numbers', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'cat7_6', num: '7.6', name: 'PLTS', method_class: 'PLTS', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'cat7_7', num: '7.7', name: 'Plithogenic Sets', method_class: 'Plithogenic_Sets', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'cat7_8', num: '7.8', name: 'Belief Rule Base', method_class: 'Belief_Rule_Base', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'cat7_9', num: '7.9', name: 'Quantum Probability', method_class: 'Quantum_Probability', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'cat7_10', num: '7.10', name: 'Pythagorean Fuzzy Sets', method_class: 'Pythagorean_Fuzzy', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'cat7_11', num: '7.11', name: 'Picture Fuzzy Sets', method_class: 'Picture_Fuzzy', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'cat7_12', num: '7.12', name: 'Hesitant Fuzzy Sets', method_class: 'Hesitant_Fuzzy', active: true, required: ['cpi','spi'] },
      { id: 'cat7_13', num: '7.13', name: 'Type-2 Fuzzy Sets', method_class: 'Type2_Fuzzy', active: true, required: ['cpi','spi'] },
      { id: 'cat7_14', num: '7.14', name: 'Maximum Entropy', method_class: 'Maximum_Entropy', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'cat7_15', num: '7.15', name: 'Possibility Theory', method_class: 'Possibility_Theory', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'cat7_16', num: '7.16', name: 'Spherical Fuzzy Sets', method_class: 'Spherical_Fuzzy', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'cat7_17', num: '7.17', name: 'Fermatean Fuzzy Sets', method_class: 'Fermatean_Fuzzy', active: true, required: ['cpi','spi'] },
      { id: 'cat7_18', num: '7.18', name: 'MARCOS Ranking', method_class: 'MARCOS', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'cat7_19', num: '7.19', name: 'CRITIC-TOPSIS', method_class: 'CRITIC_TOPSIS', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'cat7_20', num: '7.20', name: 'Hypersoft Sets', method_class: 'Hypersoft_Sets', active: true, required: ['cpi','spi','docRiskScore'] }
    ]
  },
  {
    // Portfolio Health (ex-"Cat 8") is NOT a numbered project category — it
    // compares one project against the rest of the portfolio, not the project
    // in isolation. num:'PH' (module nums 'PH.1'-'PH.5'); level:'portfolio'
    // routes it to the Health dialog wherever project-category sequences render.
    id: 'cat8', num: 'PH', name: 'ML & AI Pattern Detection', level: 'portfolio',
    color: '#64748b',
    parked: false,  // ACTIVE — portfolioanalyze (Code.gs v10.17) computes these
    description: 'Machine learning anomaly detection using portfolio-wide signal comparison.',
    modules: [
      { id: 'cat8_1', num: 'PH.1', name: 'Isolation Forest', method_class: 'Isolation_Forest', active: true, required: ['portfolioVectors'] },
      { id: 'cat8_2', num: 'PH.2', name: 'Portfolio Outlier Detection', method_class: 'Portfolio_Outlier', active: true, required: ['portfolioVectors'] },
      { id: 'cat8_3', num: 'PH.3', name: 'Signal Trajectory Classifier', method_class: 'Trajectory_Classifier', active: true, required: ['signalHistory'] },
      { id: 'cat8_4', num: 'PH.4', name: 'Cross-project Pattern Detector', method_class: 'Cross_Project_Pattern', active: true, required: ['portfolioVectors'] },
      { id: 'cat8_5', num: 'PH.5', name: 'Anomaly Score', method_class: 'Anomaly_Score', active: true, required: ['portfolioVectors'] }
    ]
  },
  {
    id: 'cat9', num: 'Cat 8', name: 'Governance & Compliance',
    color: '#e0556b',
    description: 'Named authority, required action, regulatory compliance — always the last step.',
    modules: [
      { id: 'cat9_1', num: '8.1', name: 'ABM Governance Layer', method_class: 'ABM_Governance', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'cat9_2', num: '8.2', name: 'FAR Threshold Monitor', method_class: 'FAR_Threshold', active: true, required: ['bac','cpi','ev','ac'] },
      { id: 'cat9_3', num: '8.3', name: 'OMB A-11 Check', method_class: 'OMB_A11_Check', active: true, required: ['bac','cpi','actualPctComplete'] },
      { id: 'cat9_4', num: '8.4', name: 'EVM Reporting Threshold', method_class: 'EVM_Reporting_Threshold', active: true, required: ['bac','cpi','spi'] },
      { id: 'cat9_5', num: '8.5', name: 'Contract Modification Frequency', method_class: 'Contract_Mod_Frequency', active: true, required: ['changeOrderCount','baselineContractSum','revisedContractSum'] },
      { id: 'cat9_6', num: '8.6', name: 'Quality Compliance Index', method_class: 'Quality_Compliance', active: true, required: ['qualityDeficienciesNoted'] },
      { id: 'cat9_7', num: '8.7', name: 'Safety Performance Index', method_class: 'Safety_Performance', active: true, required: ['safetyIncidentsDiscussed'], sectors: ['construction','hybrid'] },
      { id: 'cat9_8', num: '8.8', name: 'Environmental Compliance Rate', method_class: 'Environmental_Compliance', active: true, required: ['environmentalIssuesDiscussed'], sectors: ['construction','hybrid'] },
      { id: 'cat9_9', num: '8.9', name: 'Contractor Performance Score', method_class: 'Contractor_Performance', active: true, required: ['overallRating','scheduleRating','costRating'] }
    ]
  },
  {
    id: 'cat10', num: 'Cat 9', name: 'Data Integrity & Information Quality',
    color: '#06b6d4',
    description: 'Measures the quality, completeness, timeliness and reliability of the data driving all other modules. Every analytical output is only as good as its inputs — Cat 9 quantifies that.',
    modules: [
      { id: 'cat10_1', num: '9.1', name: 'Missing Data Index', method_class: 'Missing_Data_Index', active: true, required: ['bac'] },
      { id: 'cat10_2', num: '9.2', name: 'Data Timeliness Score', method_class: 'Data_Timeliness_Score', active: true, required: ['docDate'] },
      { id: 'cat10_3', num: '9.3', name: 'Source Reliability Weighting', method_class: 'Source_Reliability_Weighting', active: true, required: ['bac'] },
      { id: 'cat10_4', num: '9.4', name: 'Audit Trail Completeness', method_class: 'Audit_Trail_Completeness', active: true, required: ['bac'] },
      { id: 'cat10_5', num: '9.5', name: 'Information Completeness Ratio', method_class: 'Information_Completeness_Ratio', active: true, required: ['bac'] },
      { id: 'cat10_6', num: '9.6', name: 'Cross-document Consistency Score', method_class: 'Cross_Doc_Consistency', active: true, required: ['ev','ac'] },
      { id: 'cat10_7', num: '9.7', name: 'Reporting Frequency Index', method_class: 'Reporting_Frequency_Index', active: true, required: ['docDate'] }
    ]
  },
  {
    id: 'cat11', num: 'Cat 10', name: 'Decision Optimization',
    color: '#10b981',
    description: 'Selects the best action under constraints — distinct from Cat 5 which explains system behavior. Cat 10 answers: given the current signal state, what is the optimal decision pathway?',
    modules: [
      { id: 'cat11_1', num: '10.1', name: 'Multi-Objective Optimization', method_class: 'Multi_Objective_Optimization', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'cat11_2', num: '10.2', name: 'Linear Programming', method_class: 'Linear_Programming', active: true, required: ['bac','ev','ac','cpi'] },
      { id: 'cat11_3', num: '10.3', name: 'Constraint Satisfaction Analysis', method_class: 'Constraint_Satisfaction', active: true, required: ['cpi','spi','bac'] },
      { id: 'cat11_4', num: '10.4', name: 'What-If Scenario Matrix', method_class: 'WhatIf_Scenario_Matrix', active: true, required: ['bac','ev','ac','cpi','spi'] },
      { id: 'cat11_5', num: '10.5', name: 'Decision Sensitivity Matrix', method_class: 'Decision_Sensitivity_Matrix', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'cat11_6', num: '10.6', name: 'Pareto Frontier Analysis', method_class: 'Pareto_Frontier', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'cat11_7', num: '10.7', name: 'Regret Minimization Index', method_class: 'Regret_Minimization', active: true, required: ['cpi','spi','bac'] }
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
/* True for the Portfolio Health suite (ex-"Cat 8") — portfolio-scale, not part
   of the numbered 1-10 project-category sequence. Renderers that walk
   LIN_CATEGORIES for a project's category rollup should route entries where
   this returns true to the Health dialog instead of the numbered list. */
window.isPortfolioLevelCategory = function (cat) {
  return !!(cat && cat.level === "portfolio");
};
/* The 10 project-level categories in display order (Portfolio Health excluded) —
   the canonical list for anything rendering a gapless 1-10 sequence. */
window.projectLevelCategories = function () {
  return LIN_CATEGORIES.filter(function (c) { return !window.isPortfolioLevelCategory(c); });
};

/* Per-module status lookup. Reads from live project shape:
     project.signals.{mc,cusum,doc,decision}.status / .state
     project.simulationSignals.signal_array[*].method_class / .status_color
   Returns null when the module hasn't been computed yet (or is inactive /
   returned insufficient-data and was filtered out of the signal array).
   Returns the string 'NA' when the module's `sectors` tag excludes this
   project's sector — a deliberate abstention, distinct from "no data yet". */
window.getModuleStatus = function (methodClass, project) {
  if (!project) return null;
  if (window.isModuleSectorNA(methodClass, project)) return "NA";
  const s = project.signals || {};
  const sim = (project.simulationSignals && project.simulationSignals.signal_array) || [];
  const findSim = (cls) => {
    const found = sim.find((m) => m.method_class === cls);
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
    case "DSM_Rework_Cat5":        return findSim("DSM_Rework_Propagation");
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
    case "Regret_Minimization":    return findSim(methodClass);
    default:                       return findSim(methodClass);
  }
};

/* Worst-status-wins per category. Returns null for parked categories or
   categories whose modules haven't been computed yet. */
window.getCategoryStatus = function (catId, project) {
  const cat = LIN_CATEGORIES.find((c) => c.id === catId);
  if (!cat || cat.parked) return null;
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
  const catStatuses = LIN_CATEGORIES
    .map((c) => getCategoryStatus(c.id, project))
    .filter(Boolean);

  let fused = null;
  if (window.LinSimulations && LinSimulations.dstFuse) fused = LinSimulations.dstFuse(catStatuses);

  // Every Red module + its category — for the executive brief flags list, so a
  // Green/Yellow project still surfaces its Red modules (nothing hidden by fusion).
  const redFlags = [];
  LIN_CATEGORIES.forEach((c) => {
    if (c.parked) return;
    (c.modules || []).forEach((m) => {
      const st = window.getModuleStatus ? getModuleStatus(m.method_class, project) : null;
      if (st && String(st).toLowerCase().indexOf("red") >= 0) {
        redFlags.push({ category: c.num, categoryName: c.name, module: m.name, num: m.num });
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
