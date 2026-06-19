/* ============================================================
   lin-project-radar — categories.js
   ------------------------------------------------------------
   The full 108-module definition across 12 analytical categories.
   Drives the spider web (108 axes), the ensemble panel, the
   signal ledger, the Signals page, and the stored snapshot the
   executive brief reads from.

   Every module carries: id, num, name, method_class, active
   (true/false) and required (input keys it needs to compute).

   Cat 8 (ML & AI) is active — its 5 modules compute via the
   portfolioanalyze endpoint. Many Cat 2-9 modules now compute
   from fields derived from the existing document set (see
   signals.js deriveExtendedFields), tagged [est.] in the UI.

   Cat 10 (Data Integrity) and Cat 11 (Decision Optimization)
   are fully active — they derive from existing signalInputs
   and the project audit trail. Cat 12 (Systems Engineering) is
   defined but conditional: it activates only when interface
   control / requirements / system architecture docs are
   uploaded (see the `conditional` flag).

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
      { id: 'cat2_7', num: '2.7', name: 'Milestone Trend Analysis', method_class: 'Milestone_Trend', active: false, required: ['milestoneHistory'] },
      { id: 'cat2_8', num: '2.8', name: 'Look-Ahead Schedule Health', method_class: 'Lookahead_Health', active: true, required: ['activitiesPlanned','activitiesConstrained'] },
      { id: 'cat2_9', num: '2.9', name: 'Resource Loading Index', method_class: 'Resource_Loading', active: false, required: ['plannedLaborHours','actualLaborHours'] },
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
      { id: 'cat3_4', num: '3.4', name: 'Labor Productivity Index', method_class: 'Labor_Productivity', active: false, required: ['plannedLaborHours','actualLaborHours','actualPctComplete'] },
      { id: 'cat3_5', num: '3.5', name: 'Material Cost Variance', method_class: 'Material_Cost_Variance', active: true, required: ['materialCostBaseline','materialCostCurrent'] },
      { id: 'cat3_6', num: '3.6', name: 'Overhead Absorption Rate', method_class: 'Overhead_Absorption', active: true, required: ['indirectCostPlan','indirectCostActual'] },
      { id: 'cat3_7', num: '3.7', name: 'Cost Risk Analysis P80', method_class: 'Cost_Risk_Analysis', active: true, required: ['bac','cpi','ac','ev'] },
      { id: 'cat3_8', num: '3.8', name: 'Analogous Estimating Ratio', method_class: 'Analogous_Estimating', active: false, required: ['analogousOverrunPct','bac'] },
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
      { id: 'cat4_4', num: '4.4', name: 'NCR Rate', method_class: 'NCR_Rate', active: false, required: ['ncrIssued','ncrClosed','ncrOpen'] },
      { id: 'cat4_5', num: '4.5', name: 'Weather Day Impact', method_class: 'Weather_Impact', active: true, required: ['weatherDaysLost'] },
      { id: 'cat4_6', num: '4.6', name: 'Change Order Frequency', method_class: 'CO_Frequency', active: true, required: ['changeOrderCount','baselineContractSum','revisedContractSum'] },
      { id: 'cat4_7', num: '4.7', name: 'Dispute Escalation Index', method_class: 'Dispute_Escalation', active: true, required: ['docRiskScore','rfiCount','changeOrderCount'] },
      { id: 'cat4_8', num: '4.8', name: 'Subcontractor Performance', method_class: 'Subcontractor_Performance', active: true, required: ['subcontractorComplianceScore'] },
      { id: 'cat4_9', num: '4.9', name: 'Procurement Lead Time Monitor', method_class: 'Procurement_Lead_Time', active: false, required: ['longLeadItemsTotal','longLeadAtRisk','longLeadDelayed'] },
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
      { id: 'cat5_6', num: '5.6', name: 'Queueing Theory Bottleneck', method_class: 'Queueing_Bottleneck', active: false, required: ['activitiesPlanned','activitiesConstrained'] },
      { id: 'cat5_7', num: '5.7', name: 'Agent-Based Supply Chain', method_class: 'Agent_Supply_Chain', active: false, required: ['longLeadItemsTotal','longLeadAtRisk'] },
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
    id: 'cat8', num: 'Cat 8', name: 'ML & AI Pattern Detection',
    color: '#64748b',
    parked: false,  // NOW ACTIVE — portfolioanalyze (Code.gs v10.17) computes these
    description: 'Machine learning anomaly detection using portfolio-wide signal comparison.',
    modules: [
      { id: 'cat8_1', num: '8.1', name: 'Isolation Forest', method_class: 'Isolation_Forest', active: true, required: ['portfolioVectors'] },
      { id: 'cat8_2', num: '8.2', name: 'Portfolio Outlier Detection', method_class: 'Portfolio_Outlier', active: true, required: ['portfolioVectors'] },
      { id: 'cat8_3', num: '8.3', name: 'Signal Trajectory Classifier', method_class: 'Trajectory_Classifier', active: true, required: ['signalHistory'] },
      { id: 'cat8_4', num: '8.4', name: 'Cross-project Pattern Detector', method_class: 'Cross_Project_Pattern', active: true, required: ['portfolioVectors'] },
      { id: 'cat8_5', num: '8.5', name: 'Anomaly Score', method_class: 'Anomaly_Score', active: true, required: ['portfolioVectors'] }
    ]
  },
  {
    id: 'cat9', num: 'Cat 9', name: 'Governance & Compliance',
    color: '#e0556b',
    description: 'Named authority, required action, regulatory compliance — always the last step.',
    modules: [
      { id: 'cat9_1', num: '9.1', name: 'ABM Governance Layer', method_class: 'ABM_Governance', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'cat9_2', num: '9.2', name: 'FAR Threshold Monitor', method_class: 'FAR_Threshold', active: true, required: ['bac','cpi','ev','ac'] },
      { id: 'cat9_3', num: '9.3', name: 'OMB A-11 Check', method_class: 'OMB_A11_Check', active: true, required: ['bac','cpi','actualPctComplete'] },
      { id: 'cat9_4', num: '9.4', name: 'EVM Reporting Threshold', method_class: 'EVM_Reporting_Threshold', active: true, required: ['bac','cpi','spi'] },
      { id: 'cat9_5', num: '9.5', name: 'Contract Modification Frequency', method_class: 'Contract_Mod_Frequency', active: true, required: ['changeOrderCount','baselineContractSum','revisedContractSum'] },
      { id: 'cat9_6', num: '9.6', name: 'Quality Compliance Index', method_class: 'Quality_Compliance', active: true, required: ['qualityDeficienciesNoted'] },
      { id: 'cat9_7', num: '9.7', name: 'Safety Performance Index', method_class: 'Safety_Performance', active: true, required: ['safetyIncidentsDiscussed'] },
      { id: 'cat9_8', num: '9.8', name: 'Environmental Compliance Rate', method_class: 'Environmental_Compliance', active: true, required: ['environmentalIssuesDiscussed'] },
      { id: 'cat9_9', num: '9.9', name: 'Contractor Performance Score', method_class: 'Contractor_Performance', active: false, required: ['overallRating','scheduleRating','costRating'] }
    ]
  },
  {
    id: 'cat10', num: 'Cat 10', name: 'Data Integrity & Information Quality',
    color: '#06b6d4',
    description: 'Measures the quality, completeness, timeliness and reliability of the data driving all other modules. Every analytical output is only as good as its inputs — Cat 10 quantifies that.',
    modules: [
      { id: 'cat10_1', num: '10.1', name: 'Missing Data Index', method_class: 'Missing_Data_Index', active: true, required: ['bac'] },
      { id: 'cat10_2', num: '10.2', name: 'Data Timeliness Score', method_class: 'Data_Timeliness_Score', active: true, required: ['docDate'] },
      { id: 'cat10_3', num: '10.3', name: 'Source Reliability Weighting', method_class: 'Source_Reliability_Weighting', active: true, required: ['bac'] },
      { id: 'cat10_4', num: '10.4', name: 'Audit Trail Completeness', method_class: 'Audit_Trail_Completeness', active: true, required: ['bac'] },
      { id: 'cat10_5', num: '10.5', name: 'Information Completeness Ratio', method_class: 'Information_Completeness_Ratio', active: true, required: ['bac'] },
      { id: 'cat10_6', num: '10.6', name: 'Cross-document Consistency Score', method_class: 'Cross_Doc_Consistency', active: true, required: ['ev','ac'] },
      { id: 'cat10_7', num: '10.7', name: 'Reporting Frequency Index', method_class: 'Reporting_Frequency_Index', active: true, required: ['docDate'] }
    ]
  },
  {
    id: 'cat11', num: 'Cat 11', name: 'Decision Optimization',
    color: '#10b981',
    description: 'Selects the best action under constraints — distinct from Cat 5 which explains system behavior. Cat 11 answers: given the current signal state, what is the optimal decision pathway?',
    modules: [
      { id: 'cat11_1', num: '11.1', name: 'Multi-Objective Optimization', method_class: 'Multi_Objective_Optimization', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'cat11_2', num: '11.2', name: 'Linear Programming', method_class: 'Linear_Programming', active: true, required: ['bac','ev','ac','cpi'] },
      { id: 'cat11_3', num: '11.3', name: 'Constraint Satisfaction Analysis', method_class: 'Constraint_Satisfaction', active: true, required: ['cpi','spi','bac'] },
      { id: 'cat11_4', num: '11.4', name: 'What-If Scenario Matrix', method_class: 'WhatIf_Scenario_Matrix', active: true, required: ['bac','ev','ac','cpi','spi'] },
      { id: 'cat11_5', num: '11.5', name: 'Decision Sensitivity Matrix', method_class: 'Decision_Sensitivity_Matrix', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'cat11_6', num: '11.6', name: 'Pareto Frontier Analysis', method_class: 'Pareto_Frontier', active: true, required: ['cpi','spi','docRiskScore'] },
      { id: 'cat11_7', num: '11.7', name: 'Regret Minimization Index', method_class: 'Regret_Minimization', active: true, required: ['cpi','spi','bac'] }
    ]
  },
  {
    id: 'cat12', num: 'Cat 12', name: 'Systems Engineering',
    color: '#a855f7',
    description: 'Interface complexity, dependency mapping, and requirements traceability. Activates when interface control documents and requirements specifications are uploaded. Most novel category — very few EVM platforms address systems engineering complexity.',
    conditional: true,
    modules: [
      { id: 'cat12_1', num: '12.1', name: 'Interface Density Index', method_class: 'Interface_Density', active: false, required: ['interfaceCount','totalComponents'] },
      { id: 'cat12_2', num: '12.2', name: 'Dependency Mapping Score', method_class: 'Dependency_Mapping', active: false, required: ['dependencyCount','criticalDependencies'] },
      { id: 'cat12_3', num: '12.3', name: 'Requirements Traceability Coverage', method_class: 'Requirements_Traceability', active: false, required: ['requirementsTotal','requirementsVerified'] },
      { id: 'cat12_4', num: '12.4', name: 'Configuration Change Impact', method_class: 'Config_Change_Impact', active: false, required: ['changeOrderCount','configurationItems'] },
      { id: 'cat12_5', num: '12.5', name: 'Integration Complexity Index', method_class: 'Integration_Complexity', active: false, required: ['interfaceCount','dependencyCount'] }
    ]
  }
];

/* Per-module status lookup. Reads from live project shape:
     project.signals.{mc,cusum,doc,decision}.status / .state
     project.simulationSignals.signal_array[*].method_class / .status_color
   Returns null when the module hasn't been computed yet (or is inactive /
   returned insufficient-data and was filtered out of the signal array). */
window.getModuleStatus = function (methodClass, project) {
  if (!project) return null;
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
    // Cat 8 ML/AI — results come from the portfolioanalyze POST and are merged
    // into the simulation signal_array like the other sim modules.
    case "Isolation_Forest":
    case "Portfolio_Outlier":
    case "Trajectory_Classifier":
    case "Cross_Project_Pattern":
    case "Anomaly_Score":          return findSim(methodClass);
    // Cat 10 — Data Integrity & Information Quality (compute from existing
    // signalInputs + the project audit trail).
    case "Missing_Data_Index":
    case "Data_Timeliness_Score":
    case "Source_Reliability_Weighting":
    case "Audit_Trail_Completeness":
    case "Information_Completeness_Ratio":
    case "Cross_Doc_Consistency":
    case "Reporting_Frequency_Index":
    // Cat 11 — Decision Optimization (compute from existing signalInputs).
    case "Multi_Objective_Optimization":
    case "Linear_Programming":
    case "Constraint_Satisfaction":
    case "WhatIf_Scenario_Matrix":
    case "Decision_Sensitivity_Matrix":
    case "Pareto_Frontier":
    case "Regret_Minimization":
    // Cat 12 — Systems Engineering (conditional; mostly returns null until
    // interface / requirements / system architecture docs are uploaded).
    case "Interface_Density":
    case "Dependency_Mapping":
    case "Requirements_Traceability":
    case "Config_Change_Impact":
    case "Integration_Complexity": return findSim(methodClass);
    default:                       return findSim(methodClass);
  }
};

/* Worst-status-wins per category. Returns null for parked categories or
   categories whose modules haven't been computed yet. Conditional categories
   (Cat 12) only surface when at least one of their modules has data — until
   then they render as a grey/inactive band on the spider web. */
window.getCategoryStatus = function (catId, project) {
  const cat = LIN_CATEGORIES.find((c) => c.id === catId);
  if (!cat || cat.parked) return null;
  if (cat.conditional) {
    const hasAnyData = cat.modules.some((m) => getModuleStatus(m.method_class, project) != null);
    if (!hasAnyData) return null;
  }
  const statuses = cat.modules
    .map((m) => getModuleStatus(m.method_class, project))
    .filter(Boolean)
    .map((s) => String(s));
  if (!statuses.length) return null;
  const has = (label) => statuses.some((s) => s.toLowerCase().indexOf(label) >= 0);
  if (has("red")) return "Red";
  if (has("amber") || has("orange")) return "Amber";
  if (has("yellow") || has("light-amber")) return "Yellow";
  if (has("green")) return "Green";
  if (has("complete") || has("blue")) return "Complete";
  return null;
};
