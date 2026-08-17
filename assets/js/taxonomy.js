/* ============================================================
   Opus Gubernatio — taxonomy.js
   ------------------------------------------------------------
   The module and category taxonomy, and the status accessors the
   interface reads.

   THIS FILE REPLACES categories.js ON THE PARTICIPANT-FACING
   APPLICATION. The taxonomy below is unchanged from that file:
   the same categories, the same modules, the same method_class
   tags, the same sector eligibility rules. It is DATA, and it
   computes nothing.

   What is not here is the part that computed a status in the
   browser. categories.js derived module, category and project
   statuses from project.signals, fusing them with
   simulations.js. That derivation produced false Red statuses on
   healthy projects — see the block above getModuleStatus below
   for the measurements. Those four functions now read the stored
   computed_results row instead, so every screen shows the number
   the server computed and stored, and no screen can disagree
   with another.

   categories.js still exists and is still loaded on the
   researcher-side deep-dive route, which deliberately re-runs
   models live to show its working. Nothing here is loaded there
   and nothing there is loaded here.
   ============================================================ */


window.LIN_CATEGORIES = [
  {
    id: 'a1', num: 'A1', name: 'Cost and EVM Performance',
    group: 'A', groupName: 'Project Health',
    color: '#4ea0ff',
    description: 'Cost and schedule performance indices derived from verified pay applications and schedules.',
    modules: [
      { id: 'a1_1', num: 'A1.1', name: 'Monte Carlo EAC Forecast', method_class: 'Monte_Carlo', active: true, required: ['bac','cpi','spi'] },
      { id: 'a1_2', num: 'A1.2', name: 'CUSUM Anomaly Monitor', method_class: 'CUSUM', active: true, required: ['spi'] },
      { id: 'a1_3', num: 'A1.3', name: 'Bayesian EAC', method_class: 'Bayesian_EAC', active: true, required: ['bac','ev','ac','cpi'] },
      { id: 'a1_4', num: 'A1.4', name: 'Kalman Filter SPI Smoother', method_class: 'Kalman_Filter', active: true, required: ['spi','spiHistory'] },
      { id: 'a1_5', num: 'A1.5', name: 'ARIMA CPI Forecast', method_class: 'ARIMA_Forecast', active: true, required: ['cpiHistory'] },
      { id: 'a1_6', num: 'A1.6', name: 'Earned Schedule', method_class: 'Earned_Schedule', active: true, required: ['ev','pv','bac','actualPctComplete','plannedPctComplete'] },
      { id: 'a1_7', num: 'A1.7', name: 'TCPI', method_class: 'TCPI', active: true, required: ['bac','ev','ac'] },
      { id: 'a1_8', num: 'A1.8', name: 'Variance at Completion', method_class: 'VAC', active: true, required: ['bac','cpi'] },
      { id: 'a1_9', num: 'A1.9', name: 'Budget Execution Rate', method_class: 'Budget_Execution_Rate', active: true, required: ['ac','bac','actualPctComplete'] },
      { id: 'a1_10', num: 'A1.10', name: 'CPI Shrinkage Forecast', method_class: 'Regression_To_Mean', active: true, required: ['cpi','cpiHistory'] },
      { id: 'a1_11', num: 'A1.11', name: 'Independent EAC Reconciliation Index', method_class: 'ICE_Ratio', active: true, required: ['bac','cpi','ev','ac'] }
    ]
  },
  {
    id: 'a2', num: 'A2', name: 'Schedule Performance',
    group: 'A', groupName: 'Project Health',
    color: '#7c5cff',
    description: 'Schedule simulation and critical-path behavior.',
    modules: [
      { id: 'a2_1', num: 'A2.1', name: 'PERT Network Criticality', method_class: 'PERT_Network_Criticality', active: true, required: ['spi','bac'] },
      { id: 'a2_2', num: 'A2.2', name: 'Line of Balance', method_class: 'Line_of_Balance_Velocity', active: true, required: ['spi','actualPctComplete','plannedPctComplete'] },
      { id: 'a2_3', num: 'A2.3', name: 'CCPM Buffer Health', method_class: 'CCPM_Buffer_Health', active: true, required: ['actualPctComplete','plannedPctComplete'] },
      { id: 'a2_4', num: 'A2.4', name: 'Schedule Compression Index', method_class: 'Schedule_Compression', active: true, required: ['baselineEnd','baselineStart','actualPctComplete'] },
      { id: 'a2_5', num: 'A2.5', name: 'Float Consumption Rate', method_class: 'Float_Consumption', active: true, required: ['totalFloat','consumedFloat'] },
      { id: 'a2_6', num: 'A2.6', name: 'S-Curve Deviation', method_class: 'SCurve_Deviation', active: true, required: ['actualPctComplete','plannedPctComplete','ev','pv'] },
      { id: 'a2_7', num: 'A2.7', name: 'Milestone Trend Analysis', method_class: 'Milestone_Trend', active: true, required: ['milestoneHistory'] },
      { id: 'a2_8', num: 'A2.8', name: 'Look-Ahead Schedule Health', method_class: 'Lookahead_Health', active: true, required: ['activitiesPlanned','activitiesConstrained'] },
      { id: 'a2_9', num: 'A2.9', name: 'Resource Loading Index', method_class: 'Resource_Loading', active: true, required: ['plannedLaborHours','actualLaborHours'] },
      { id: 'a2_10', num: 'A2.10', name: 'Schedule Risk Analysis P80', method_class: 'Schedule_Risk_Analysis', active: true, required: ['spi','baselineEnd','baselineStart','actualPctComplete'] },
      { id: 'a2_11', num: 'A2.11', name: 'Critical Path Index', method_class: 'Critical_Path_Index', active: true, required: ['spi','plannedPctComplete','actualPctComplete'] }
    ]
  },
  {
    id: 'a3', num: 'A3', name: 'Cost Risk',
    group: 'A', groupName: 'Project Health',
    color: '#22c1a4',
    description: 'Cost risk, contingency and parametric cost behavior.',
    modules: [
      { id: 'a3_1', num: 'A3.1', name: 'Reference Class Forecasting', method_class: 'Reference_Class_Forecasting', active: true, required: ['bac','cpi'] },
      { id: 'a3_2', num: 'A3.2', name: 'Contingency Burn Rate', method_class: 'Contingency_Burn_Rate', active: true, required: ['originalContingency','remainingContingency','actualPctComplete'] },
      { id: 'a3_3', num: 'A3.3', name: 'Labor Productivity Index', method_class: 'Labor_Productivity', active: true, required: ['plannedLaborHours','actualLaborHours','actualPctComplete'] },
      /* RUN 16. Disabled from operational execution pending an evidence and context
         requirement decision, NOT because its arithmetic is in question. The server
         refuses it (registry.DISABLED_EVIDENCE_UNDER_REVIEW) and this flag is what keeps
         the browser from presenting it as available; the row stays, reading as not
         available for production use, exactly as the eight concept-only rows do. */
      { id: 'a3_4', num: 'A3.4', name: 'Material Cost Variance', method_class: 'Material_Cost_Variance', active: true, disabled: true, required: ['materialCostBaseline','materialCostCurrent'] },
      { id: 'a3_5', num: 'A3.5', name: 'Overhead Absorption Rate', method_class: 'Overhead_Absorption', active: true, required: ['indirectCostPlan','indirectCostActual'] },
      { id: 'a3_6', num: 'A3.6', name: 'Cost Risk Analysis P80', method_class: 'Cost_Risk_Analysis', active: true, required: ['bac','cpi','ac','ev'] },
      { id: 'a3_7', num: 'A3.7', name: 'Analogous Estimating Ratio', method_class: 'Analogous_Estimating', active: true, required: ['analogousOverrunPct','bac'] },
      { id: 'a3_8', num: 'A3.8', name: 'Parametric Cost Index', method_class: 'Parametric_Cost', active: true, disabled: true, required: ['bac','ev','ac','actualPctComplete'] },
      { id: 'a3_9', num: 'A3.9', name: 'Inflation Adjustment Index', method_class: 'Inflation_Adjustment', active: true, required: ['materialCostBaseline','materialCostCurrent'] }
    ]
  },
  {
    id: 'a4', num: 'A4', name: 'Document-Derived Condition Signals',
    group: 'A', groupName: 'Project Health',
    color: '#f0a020',
    description: 'Condition signals derived from project documents: RFIs, submittals, change orders and disputes.',
    modules: [
      { id: 'a4_1', num: 'A4.1', name: 'Document Risk Score', method_class: 'Doc_Risk_Cat4', active: true, required: ['docRiskScore'] },
      { id: 'a4_2', num: 'A4.2', name: 'RFI Velocity', method_class: 'RFI_Velocity', active: true, required: ['rfiCount','rfiPeriodDays'] },
      { id: 'a4_3', num: 'A4.3', name: 'Submittal Rejection Rate', method_class: 'Submittal_Rejection', active: true, required: ['submittalsTotal','submittalsRejected'] },
      { id: 'a4_4', num: 'A4.4', name: 'NCR Rate', method_class: 'NCR_Rate', active: true, required: ['ncrIssued','ncrClosed','ncrOpen'], sectors: ['construction','hybrid'] },
      { id: 'a4_5', num: 'A4.5', name: 'Weather Day Impact', method_class: 'Weather_Impact', active: true, required: ['weatherDaysLost'], sectors: ['construction','hybrid'] },
      { id: 'a4_6', num: 'A4.6', name: 'Change Order Frequency', method_class: 'CO_Frequency', active: true, required: ['changeOrderCount','baselineContractSum','revisedContractSum'] },
      { id: 'a4_7', num: 'A4.7', name: 'Dispute Escalation Index', method_class: 'Dispute_Escalation', active: true, required: ['docRiskScore','rfiCount','changeOrderCount'] },
      { id: 'a4_8', num: 'A4.8', name: 'Subcontractor Performance', method_class: 'Subcontractor_Performance', active: true, required: ['subcontractorComplianceScore'], sectors: ['construction','hybrid'] },
      { id: 'a4_9', num: 'A4.9', name: 'Procurement Lead Time Monitor', method_class: 'Procurement_Lead_Time', active: true, required: ['longLeadItemsTotal','longLeadAtRisk','longLeadDelayed'], sectors: ['construction','hybrid'] },
      { id: 'a4_10', num: 'A4.10', name: 'Specification Conflict Density', method_class: 'Spec_Conflict_Density', active: true, required: ['docRiskScore','rfiCount'] }
    ]
  },
  {
    id: 'a5', num: 'A5', name: 'System Dynamics and Complexity',
    group: 'A', groupName: 'Project Health',
    color: '#ff7ac6',
    description: 'System dynamics, feedback and complexity behavior.',
    modules: [
      { id: 'a5_1', num: 'A5.1', name: 'DSM Rework Propagation', method_class: 'DSM_Rework_Cat5', active: true, required: ['cpi','spi'] },
      { id: 'a5_2', num: 'A5.2', name: 'Sensitivity Analysis', method_class: 'Sensitivity_Analysis', active: true, required: ['bac','ev','ac','pv','cpi','spi'] },
      { id: 'a5_3', num: 'A5.3', name: 'Tornado Risk Ranking', method_class: 'Tornado_Diagram', active: true, required: ['cpi','spi','docRiskScore','actualPctComplete','plannedPctComplete'] },
      { id: 'a5_4', num: 'A5.4', name: 'Scenario Modeling', method_class: 'Scenario_Modeling', active: true, required: ['bac','ev','ac','cpi','spi'] },
      { id: 'a5_5', num: 'A5.5', name: 'Rework Feedback Loop', method_class: 'Rework_Feedback', active: true, required: ['cpi','rfiCount','changeOrderCount'] },
      { id: 'a5_6', num: 'A5.6', name: 'Queueing Theory Bottleneck', method_class: 'Queueing_Bottleneck', active: true, required: ['activitiesPlanned','activitiesConstrained'] },
      { id: 'a5_7', num: 'A5.7', name: 'Agent-Based Supply Chain', method_class: 'Agent_Supply_Chain', active: true, required: ['longLeadItemsTotal','longLeadAtRisk'] },
      { id: 'a5_8', num: 'A5.8', name: 'Discrete Event Simulation', method_class: 'Discrete_Event_Sim', active: true, required: ['spi','actualPctComplete','plannedPctComplete','cpi'] }
    ]
  },
  {
    id: 'a6', num: 'A6', name: 'Delivery Quality Performance',
    group: 'A', groupName: 'Project Health',
    color: '#8fb69a',
    description: 'Delivery quality, safety, environmental and contractor performance. These describe how the work is being delivered, not who must authorize a response.',
    modules: [
      { id: 'a6_1', num: 'A6.1', name: 'Quality Compliance Index', method_class: 'Quality_Compliance', active: true, required: ['qualityDeficienciesNoted'] },
      { id: 'a6_2', num: 'A6.2', name: 'Safety Performance Index', method_class: 'Safety_Performance', active: true, required: ['safetyIncidentsDiscussed'], sectors: ['construction','hybrid'] },
      { id: 'a6_3', num: 'A6.3', name: 'Environmental Compliance Rate', method_class: 'Environmental_Compliance', active: true, required: ['environmentalIssuesDiscussed'], sectors: ['construction','hybrid'] },
      { id: 'a6_4', num: 'A6.4', name: 'Contractor Performance Assessment Signal', method_class: 'Contractor_Performance', active: true, required: ['overallRating','scheduleRating','costRating'] }
    ]
  },
  {
    id: 'b1', num: 'B1', name: 'Signal Synthesis',
    group: 'B', groupName: 'Recommendation and Governance',
    color: '#ffd05a',
    description: 'Synthesis of the assembled signal set into a single recommended posture.',
    modules: [
      { id: 'b1_1', num: 'B1.1', name: 'Conservative Dominance', method_class: 'Conservative_Dominance', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'b1_2', num: 'B1.2', name: 'Weighted Voting', method_class: 'Weighted_Voting', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'b1_3', num: 'B1.3', name: 'Majority Rules', method_class: 'Majority_Rules', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'b1_4', num: 'B1.4', name: 'Worst-N-of-M', method_class: 'Worst_N_of_M', active: true, required: ['cpi','spi','docRiskScore'] }
    ]
  },
  {
    id: 'b2', num: 'B2', name: 'Evidence Combination',
    group: 'B', groupName: 'Recommendation and Governance',
    color: '#5ed7ff',
    description: 'Evidence combination under uncertainty: fuzzy, rough, neutrosophic and belief-function methods.',
    modules: [
      { id: 'b2_1', num: 'B2.1', name: 'Dempster-Shafer', method_class: 'DST_Evidence_Combination', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'b2_2', num: 'B2.2', name: 'Rough Sets', method_class: 'Rough_Sets_Classification', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'b2_3', num: 'B2.3', name: 'Neutrosophic Logic', method_class: 'Neutrosophic_Logic', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'b2_4', num: 'B2.4', name: 'Interval Fuzzy Sets', method_class: 'Interval_Fuzzy_Sets', active: true, required: ['cpi','spi'] },
      { id: 'b2_5', num: 'B2.5', name: 'Z-numbers', method_class: 'Z_Numbers', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'b2_6', num: 'B2.6', name: 'PLTS', method_class: 'PLTS', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'b2_7', num: 'B2.7', name: 'Plithogenic Sets', method_class: 'Plithogenic_Sets', active: true, disabled: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'b2_8', num: 'B2.8', name: 'Belief Rule Base', method_class: 'Belief_Rule_Base', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'b2_9', num: 'B2.9', name: 'Quantum Probability', method_class: 'Quantum_Probability', active: true, disabled: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'b2_10', num: 'B2.10', name: 'Pythagorean Fuzzy Sets', method_class: 'Pythagorean_Fuzzy', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'b2_11', num: 'B2.11', name: 'Picture Fuzzy Sets', method_class: 'Picture_Fuzzy', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'b2_12', num: 'B2.12', name: 'Hesitant Fuzzy Sets', method_class: 'Hesitant_Fuzzy', active: true, required: ['cpi','spi'] },
      { id: 'b2_13', num: 'B2.13', name: 'Type-2 Fuzzy Sets', method_class: 'Type2_Fuzzy', active: true, required: ['cpi','spi'] },
      { id: 'b2_14', num: 'B2.14', name: 'Maximum Entropy', method_class: 'Maximum_Entropy', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'b2_15', num: 'B2.15', name: 'Possibility Theory', method_class: 'Possibility_Theory', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'b2_16', num: 'B2.16', name: 'Spherical Fuzzy Sets', method_class: 'Spherical_Fuzzy', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'b2_17', num: 'B2.17', name: 'Fermatean Fuzzy Sets', method_class: 'Fermatean_Fuzzy', active: true, required: ['cpi','spi'] },
      { id: 'b2_18', num: 'B2.18', name: 'MARCOS Ranking', method_class: 'MARCOS', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'b2_19', num: 'B2.19', name: 'CRITIC-TOPSIS', method_class: 'CRITIC_TOPSIS', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'b2_20', num: 'B2.20', name: 'Hypersoft Sets', method_class: 'Hypersoft_Sets', active: true, disabled: true, required: ['cpi','spi','docRiskScore'] }
    ]
  },
  {
    id: 'b3', num: 'B3', name: 'Regulatory and Authority Thresholds',
    group: 'B', groupName: 'Recommendation and Governance',
    color: '#e0556b',
    description: 'Regulatory and authority thresholds that determine who must act and at what level.',
    modules: [
      { id: 'b3_1', num: 'B3.1', name: 'Agent-Based Governance Model', method_class: 'ABM_Governance', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'b3_2', num: 'B3.2', name: 'FAR/Agency EVMS Applicability Monitor', method_class: 'FAR_Threshold', active: true, required: ['bac','cpi','ev','ac'] },
      { id: 'b3_3', num: 'B3.3', name: 'Versioned A-11 Capital Programming Conformance Check', method_class: 'OMB_A11_Check', active: true, required: ['bac','cpi','actualPctComplete'] },
      { id: 'b3_4', num: 'B3.4', name: 'EVMS Reporting Compliance Monitor', method_class: 'EVM_Reporting_Threshold', active: true, required: ['bac','cpi','spi'] },
      { id: 'b3_5', num: 'B3.5', name: 'Contract Modification Governance Check', method_class: 'Contract_Mod_Frequency', active: true, required: ['changeOrderCount','baselineContractSum','revisedContractSum'] }
    ]
  },
  {
    id: 'b4', num: 'B4', name: 'Decision Optimization',
    group: 'B', groupName: 'Recommendation and Governance',
    color: '#a78bfa',
    description: 'Decision optimisation and trade-off analysis over the available courses of action.',
    modules: [
      { id: 'b4_1', num: 'B4.1', name: 'Multi-Objective Optimization', method_class: 'Multi_Objective_Optimization', active: true, disabled: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'b4_2', num: 'B4.2', name: 'Linear Programming', method_class: 'Linear_Programming', active: true, disabled: true, required: ['bac','ev','ac','cpi'] },
      { id: 'b4_3', num: 'B4.3', name: 'Constraint Satisfaction Analysis', method_class: 'Constraint_Satisfaction', active: true, required: ['cpi','spi','bac'] },
      { id: 'b4_4', num: 'B4.4', name: 'What-If Scenario Matrix', method_class: 'WhatIf_Scenario_Matrix', active: true, required: ['bac','ev','ac','cpi','spi'] },
      { id: 'b4_5', num: 'B4.5', name: 'Decision Sensitivity Matrix', method_class: 'Decision_Sensitivity_Matrix', active: true, disabled: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'b4_6', num: 'B4.6', name: 'Pareto Frontier Analysis', method_class: 'Pareto_Frontier', active: true, disabled: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'b4_7', num: 'B4.7', name: 'Regret Minimization Index', method_class: 'Regret_Minimization', active: true, required: ['cpi','spi','bac'] }
    ]
  },
  {
    id: 'c1', num: 'C1', name: 'Data Integrity',
    group: 'C', groupName: 'Data and Evidence Health',
    color: '#94a3b8',
    authoringOnly: true, excludeFromProjectStatus: true,
    description: 'Evidence quality of the underlying document set. Authoring-time only: these describe how trustworthy the evidence is, never the condition of the project.',
    modules: [
      { id: 'c1_1', num: 'C1.1', name: 'Missing Data Index', method_class: 'Missing_Data_Index', active: true, required: ['bac'], authoringOnly: true, excludeFromProjectStatus: true },
      { id: 'c1_2', num: 'C1.2', name: 'Data Timeliness Score', method_class: 'Data_Timeliness_Score', active: true, required: ['docDate'], authoringOnly: true, excludeFromProjectStatus: true },
      { id: 'c1_3', num: 'C1.3', name: 'Source Reliability Weighting', method_class: 'Source_Reliability_Weighting', active: true, required: ['bac'], authoringOnly: true, excludeFromProjectStatus: true },
      { id: 'c1_4', num: 'C1.4', name: 'Audit Trail Completeness', method_class: 'Audit_Trail_Completeness', active: true, required: ['bac'], authoringOnly: true, excludeFromProjectStatus: true },
      { id: 'c1_5', num: 'C1.5', name: 'Information Completeness Ratio', method_class: 'Information_Completeness_Ratio', active: true, required: ['bac'], authoringOnly: true, excludeFromProjectStatus: true },
      { id: 'c1_6', num: 'C1.6', name: 'Cross-document Consistency Score', method_class: 'Cross_Doc_Consistency', active: true, required: ['ev','ac'], authoringOnly: true, excludeFromProjectStatus: true },
      { id: 'c1_7', num: 'C1.7', name: 'Reporting Frequency Index', method_class: 'Reporting_Frequency_Index', active: true, required: ['docDate'], authoringOnly: true, excludeFromProjectStatus: true }
    ]
  },
  {
    id: 'd1', num: 'D1', name: 'Portfolio Health',
    group: 'D', groupName: 'Portfolio Level',
    color: '#64748b',
    level: 'portfolio', portfolioLevel: true, parked: false,
    description: 'Portfolio-wide pattern detection. Requires three or more projects and is parked on the portfolio page.',
    modules: [
      { id: 'd1_1', num: 'D1.1', name: 'Isolation Forest', method_class: 'Isolation_Forest', active: true, required: ['portfolioVectors'], portfolioLevel: true },
      { id: 'd1_2', num: 'D1.2', name: 'Portfolio Outlier Detection', method_class: 'Portfolio_Outlier', active: true, required: ['portfolioVectors'], portfolioLevel: true },
      { id: 'd1_3', num: 'D1.3', name: 'Signal Trajectory Classifier', method_class: 'Trajectory_Classifier', active: true, required: ['signalHistory'], portfolioLevel: true },
      { id: 'd1_4', num: 'D1.4', name: 'Cross-project Pattern Detector', method_class: 'Cross_Project_Pattern', active: true, required: ['portfolioVectors'], portfolioLevel: true },
      { id: 'd1_5', num: 'D1.5', name: 'Anomaly Score', method_class: 'Anomaly_Score', active: true, required: ['portfolioVectors'], portfolioLevel: true }
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

/* ------------------------------------------------------------
   Remediation Run 1 (remediation_programme.md, remediation_decisions_answered.md 1.3). The
   eight concept-only modules the external arithmetic audit found undefensible: none implements
   the analytical structure its name claims. Non-executable in production, non-voting, excluded
   from every fusion input. Marked `disabled: true` on their taxonomy entries above.

   Run 16 adds a ninth entry carrying the same flag for a different reason: Material Cost
   Variance is disabled pending an evidence and context requirement decision. Nothing here says
   its arithmetic is wrong. The flag is deliberately shared, because what the browser has to do
   about it is identical in both cases and a second flag would be a second thing to forget.

   Reuses the EXISTING not-relevant state (blue, distinct from grey no-data) rather than
   inventing a sixth verdict -- the same state a sector-excluded module already carries. The row
   stays: it reads as not available for production use, it does not disappear. See
   getModuleStatus below, which checks this before falling back to the stored row exactly the
   way it already does for isModuleSectorNA. */
var LIN_DISABLED_MODULES = null; // method_class → true (lazy, built once)
function disabledModuleMap() {
  if (LIN_DISABLED_MODULES) return LIN_DISABLED_MODULES;
  LIN_DISABLED_MODULES = {};
  (window.LIN_CATEGORIES || []).forEach(function (c) {
    (c.modules || []).forEach(function (m) {
      if (m.disabled) LIN_DISABLED_MODULES[m.method_class] = true;
    });
  });
  return LIN_DISABLED_MODULES;
}
/* True for any module the platform has disabled, unconditionally -- not a sector question, so
   it does not depend on the project. Two disjoint reasons put a module here and the taxonomy
   flag is the same for both: the eight concept-only modules (Run 1) and Material Cost Variance,
   whose evidence and context requirement is under review (Run 16). The server refuses both. */
window.isModuleDisabled = function (methodClass) {
  return !!disabledModuleMap()[methodClass];
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
  return LIN_CATEGORIES.filter(function (c) { return !window.isPortfolioLevelCategory(c); });
};

/* ============================================================================
   STATUS COMES FROM THE STORED ROW. NOTHING BELOW COMPUTES ONE.

   These four functions kept their names and their signatures, because roughly
   eighty call sites across app.js, detail.js, signals.js, decision.js,
   forcenet.js, neural_flow.js and projectnet2d.js read them. What changed is
   where the answer comes from: they used to derive a status in the browser
   from project.signals, and they now look one up in the computed_results row
   the server stored.

   WHY THIS HAD TO CHANGE — a measured defect, not a preference.

   The browser derivation produced FALSE RED STATUSES on healthy projects. On
   identical earned-value inputs the server and the browser disagreed:

       cpi 1.05, spi 1.05   server: Green    browser: Red   (40 of 40 seeds)
       cpi 1.00, spi 1.00   server: Green    browser: Green 38 / Amber 2
       cpi 0.83, spi 0.80   server: Red      browser: Red

   The mechanism was a fabricated input. LinSim.buildSignals expects a time
   series; the ingest path never passed one, so it synthesised one from a
   single metric value and a seed, and that invented series tripped the CUSUM
   anomaly detector. The seed derived from the project id, so two identical
   projects could show different statuses.

   A project five per cent under budget and five per cent ahead of schedule was
   deterministically Red. This platform is used on real projects by practising
   directors, so that is not a cosmetic defect.

   The server computes once, from real documents, and stores the result with
   its simulation version, seed and period cutoff. Reading that row is the only
   way a screen can agree with every other screen.

   HOW A ROW REACHES A PROJECT

   LinResults.prime(projectId, row) is called by whatever fetched it — the
   portfolio loader, the project page, the decision sequence. Anything asking
   for a status before a row has arrived gets null, which every call site
   already handles: null has always meant "not computed yet", and a project
   whose analysis has not been run is exactly that.
   ============================================================================ */

(function () {
  "use strict";

  // Stored rows, keyed by the project's display id. Deliberately a plain cache with no
  // fetching of its own: a module that could fetch would eventually fetch during a render,
  // and a render that can issue a request is a render that can audit an evidence view the
  // participant did not ask for.
  var ROWS = Object.create(null);

  // method_class -> module number ("A1.1"), built once from the taxonomy above. The stored row
  // keys modules by that number; the call sites ask by method_class.
  var METHOD_TO_NUM = Object.create(null);
  (window.LIN_CATEGORIES || []).forEach(function (cat) {
    (cat.modules || []).forEach(function (m) {
      if (m && m.method_class && m.num) METHOD_TO_NUM[m.method_class] = m.num;
    });
  });

  function keyOf(project) {
    if (!project) return null;
    return project.project_id || project.id || null;
  }

  /* The stored row for a project, preferring whichever copy is COMPLETE.

     Two copies can exist and they are not the same shape. `project.storedResult` is attached
     by the list/get projection and carries four status fields only: result_id, period,
     project_status, category_statuses. ROWS[id] is primed from projectresults and carries the
     whole row, module_results and signal_inputs included.

     Preferring storedResult unconditionally meant that, for as long as the page held the
     projection, every reader asking this function for module_results was told there were
     none. A reader cannot tell that apart from a project whose modules did not compute, and
     at least one surface said exactly that out loud: the Governance Decision card reported
     that the analysis scoring the courses of action "did not compute" for a project whose
     ledger was rendering that same module's status two panels down. The graft in
     detail.js repairs the projection after projectresults returns, so the false state is a
     race, but a race that resolves to a false statement on screen is still a false statement.

     So: take the projection when it is all there is, and take the primed row when the
     projection cannot answer what is being asked. Where both carry module results the
     projection wins, because the graft has already put the complete data there and a caller
     may have attached more to it. */
  function rowFor(project) {
    var k = keyOf(project);
    var primed = k ? (ROWS[k] || null) : null;
    var stored = (project && project.storedResult) || null;
    if (stored && primed && !stored.module_results && primed.module_results) return primed;
    if (stored) return stored;
    return primed;
  }

  window.LinResults = {
    /* Record the stored row for a project. Called by the loader that fetched it. */
    prime: function (projectId, row) {
      if (projectId && row) ROWS[projectId] = row;
    },
    rowFor: rowFor,
    /* True when this project has a stored result to read. Screens use it to tell
       "computed and healthy" apart from "not computed yet". */
    hasResult: function (project) { return !!rowFor(project); },
    clear: function () { ROWS = Object.create(null); }
  };

  /* Per-module status, read from the stored row.

     Two states are reasons a row is empty, not a sixth or seventh verdict, and neither
     contributes to a category or project status (see contributesToProjectStatus and
     compute.py's rollup, which never reads either):

       'NA'     — the module's sector tag excludes this project (a construction-phase module
                  on a Design project, or the reverse), OR the module is one of the eight
                  disabled concept-only modules (remediation Run 1) -- not available for
                  production use on any project, any sector. Read from the taxonomy, not
                  guessed.
       'NODATA' — the row exists (this project HAS been computed for this period) but this
                  module has no entry in it: it ran and abstained, because a figure or series
                  the module needed was not in the documents.

     Returns null only when there is no stored row at all — a project that has not been
     computed for this period, which is a different situation from either of the above and is
     handled entirely elsewhere (the "Awaiting analysis" ledger state). */
  window.getModuleStatus = function (methodClass, project) {
    if (!project) return null;
    if (window.isModuleDisabled && window.isModuleDisabled(methodClass)) return "NA";
    if (window.isModuleSectorNA && window.isModuleSectorNA(methodClass, project)) return "NA";
    var row = rowFor(project);
    if (!row || !Array.isArray(row.module_results)) return null;
    var num = METHOD_TO_NUM[methodClass];
    if (!num) return null;
    for (var i = 0; i < row.module_results.length; i++) {
      if (row.module_results[i] && row.module_results[i].module_id === num) {
        return row.module_results[i].status_color || null;
      }
    }
    return "NODATA";
  };

  /* The module's own abstention message, read verbatim from the stored row's `abstained` list
     (registry.py run_all(): {module_id, reason}, reason=None when the module gave none).
     Returns null when there is no stored row, the row predates the column (abstained is NULL),
     or this module gave no reason — never fabricated. This is the ONLY source for the reason
     text: it is not derived from status, not reworded, not synthesised. */
  window.getModuleAbstentionReason = function (methodClass, project) {
    var row = rowFor(project);
    if (!row || !Array.isArray(row.abstained)) return null;
    var num = METHOD_TO_NUM[methodClass];
    if (!num) return null;
    for (var i = 0; i < row.abstained.length; i++) {
      var a = row.abstained[i];
      if (a && a.module_id === num) return a.reason || null;
    }
    return null;
  };

  /* Full stored result dict for one module, read from the stored row.

     Returns the exact object the server stored for this module (status_color plus whatever
     structured fields that module computed), or null when there is no stored row or the row
     carries no entry for this module (an abstaining or insufficient-data module). This is the
     only honest source for a per-module chart: it reads what was stored and derives nothing. */
  window.getModuleResult = function (methodClass, project) {
    if (!project) return null;
    var row = rowFor(project);
    if (!row || !Array.isArray(row.module_results)) return null;
    var num = METHOD_TO_NUM[methodClass];
    if (!num) return null;
    for (var i = 0; i < row.module_results.length; i++) {
      if (row.module_results[i] && row.module_results[i].module_id === num) {
        return row.module_results[i];
      }
    }
    return null;
  };

  /* Per-category status, read from the stored row.

     The server already fused the modules in this category and stored the answer, so there is
     no fusion here. The previous implementation ran Dempster-Shafer in the browser over
     browser-derived module statuses; both halves of that are now the server's. */
  window.getCategoryStatus = function (catId, project) {
    var cats = window.LIN_CATEGORIES || [];
    var cat = null;
    for (var i = 0; i < cats.length; i++) {
      if (cats[i].id === catId) { cat = cats[i]; break; }
    }
    if (!cat || cat.parked) return null;
    var row = rowFor(project);
    if (!row || !row.category_statuses) return null;
    var stored = row.category_statuses[cat.num];
    return (stored && stored.status) || null;
  };

  /* Project rollup, read from the stored row.

     Consumers read .status and .redReview and nothing else. redReview is reported only when
     the server said so; the browser no longer infers disagreement it cannot see. */
  window.getProjectFusion = function (project) {
    var row = rowFor(project);
    if (!row) return null;
    /* RUN 11, GATES 5 AND 6, AND THE REASON IT IS SPELT OUT.
       rowFor prefers the list projection, which is the slim row the portfolio list can afford
       to carry. That projection has never carried the governed status label or the conflict
       state, so asking it for them returned nothing and the ledger fell back to the legacy
       signal-class classification: the browser drive found the banner still reading "Mixed
       early warning" on a project whose server result says the conflict is not estimable.
       Same shape as the module_results case documented above: take the projection when it can
       answer, and the primed row when it cannot. Neither is recomputed here. */
    var full = (project && keyOf(project) && ROWS[keyOf(project)]) || null;
    function pick(field) {
      if (row[field] != null) return row[field];
      return full && full[field] != null ? full[field] : null;
    }
    return {
      status: row.project_status || null,
      redReview: !!row.red_review,
      /* RUN 11, GATES 5 AND 6. Both are read from the stored row, never derived here. The
         server decides what the governed rollup may be called and whether its conflict
         coefficient can be estimated at all; this file does the reading and nothing else.
         A row computed before Run 11 carries neither field, so both come back null and the
         callers fall back to what they showed before rather than inventing a label. */
      statusLabel: pick("project_status_label"),
      statusScope: pick("project_status_scope"),
      conflict: pick("project_conflict"),
      conflictState: pick("project_conflict_state"),
      conflictSentence: pick("project_conflict_sentence"),
      /* Kept so a caller can tell a stored answer from a missing one without reaching for
         LinResults directly. */
      stored: true
    };
  };
})();

/* ------------------------------------------------------------
   Completion date and the Complete promotion. That is ALL this block does.

   THE HEADER THAT USED TO SIT HERE DESCRIBED A ROLLUP THIS FILE NO LONGER PERFORMS, and three of
   its claims were false against the shipped server. It said the project status is produced by
   fusing "all 11 registry category statuses (10 project categories + Portfolio Health)", that
   "Portfolio Health still votes here", and that a conflict coefficient raises a Red-review
   advisory at 0.55. Corrected, because the same three claims were removed from the Methods tab
   for being untrue and a comment repeating them is how they get reintroduced:

     · The fusion is server-side (server/app/simulation/compute.py) and the browser reads its
       stored result. getProjectFusion above does the reading; nothing here fuses anything.
     · Only the categories that describe the CONDITION of the project vote.
       contributes_to_project_status() excludes Group C (Data and Evidence Health) and Group D
       (Portfolio Level), so Portfolio Health does NOT vote in a project's status. Group D needs
       more than one project and the registry refuses it on a single-project path.
     · Nothing writes red_review. getProjectFusion reads row.red_review because that is the
       honest way to surface a server-set flag, but the server has never set one, so redReview
       is always false today. Do not reintroduce a browser-side inference to fill the gap.

   What remains below is the one place the Complete promotion and the liability rule live:
   a project at full percent-complete is promoted to Complete, and Construction/Hybrid sectors
   carry a defects-liability tail from the completion date. ------------------------------ */
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
