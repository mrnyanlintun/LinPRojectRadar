/* ============================================================
   lin-project-radar — categories.js
   ------------------------------------------------------------
   The 9-category structure that groups the M01..M19 signal
   modules for the spider web, the signal ledger, the Signals
   page, and the stored snapshot the executive brief reads from.

   Cat 8 (ML & AI) is parked — Stage 2. Its modules are listed
   so the structure is forward-compatible, but anything that
   summarises the portfolio skips them.

   Globals (no ES modules) so the site runs from file:// too.
   Loaded BEFORE the modules that consume it (categories.js
   then signals.js then detail.js etc — see index.html).
   ============================================================ */

window.LIN_CATEGORIES = [
  {
    id: "cat1", num: "Cat 1", name: "Quantitative EVM",
    description: "Cost and schedule performance indices — what is happening now",
    color: "#4ea0ff",
    modules: [
      { id: "cat1_1", num: "Cat 1.1", name: "Monte Carlo EAC Forecast", method_class: "monte_carlo" },
      { id: "cat1_2", num: "Cat 1.2", name: "CUSUM Anomaly Monitor",   method_class: "cusum" },
      { id: "cat1_3", num: "Cat 1.3", name: "Document Risk Extraction", method_class: "doc_risk" }
    ]
  },
  {
    id: "cat2", num: "Cat 2", name: "Schedule Simulation",
    description: "Time-based leading indicators — when will problems appear",
    color: "#2dd4bf",
    modules: [
      { id: "cat2_1", num: "Cat 2.1", name: "PERT Network Criticality", method_class: "PERT_Network_Criticality" },
      { id: "cat2_2", num: "Cat 2.2", name: "Line of Balance",          method_class: "Line_of_Balance_Velocity" },
      { id: "cat2_3", num: "Cat 2.3", name: "CCPM Buffer Health",       method_class: "CCPM_Buffer_Health" }
    ]
  },
  {
    id: "cat3", num: "Cat 3", name: "Cost Simulation",
    description: "Budget-based leading indicators — how much will it cost",
    color: "#e9a23b",
    modules: [
      { id: "cat3_1", num: "Cat 3.1", name: "Reference Class Forecasting", method_class: "Reference_Class_Forecasting" },
      { id: "cat3_2", num: "Cat 3.2", name: "DSM Rework Propagation",      method_class: "DSM_Rework_Propagation" }
    ]
  },
  {
    id: "cat4", num: "Cat 4", name: "Document & Risk Signals",
    description: "Qualitative signals from project records — early warning before EVM shows it",
    color: "#f59e0b",
    modules: [
      { id: "cat4_1", num: "Cat 4.1", name: "Document Risk Extraction", method_class: "doc_risk" }
    ]
  },
  {
    id: "cat5", num: "Cat 5", name: "System Dynamics",
    description: "How project components interact and amplify each other",
    color: "#8b5cf6",
    modules: [
      { id: "cat5_1", num: "Cat 5.1", name: "DSM Rework Propagation", method_class: "DSM_Rework_Propagation" }
    ]
  },
  {
    id: "cat6", num: "Cat 6", name: "Signal Synthesis",
    description: "Conservative dominance — baseline classification from all signals",
    color: "#e2b13c",
    modules: [
      { id: "cat6_1", num: "Cat 6.1", name: "Conservative Dominance", method_class: "conservative_dominance" }
    ]
  },
  {
    id: "cat7", num: "Cat 7", name: "Evidence Combination",
    description: "Uncertainty reasoning — how confident is the classification",
    color: "#9b6dff",
    modules: [
      { id: "cat7_1", num: "Cat 7.1", name: "Dempster-Shafer",       method_class: "DST_Evidence_Combination" },
      { id: "cat7_2", num: "Cat 7.2", name: "Rough Sets",            method_class: "Rough_Sets_Classification" },
      { id: "cat7_3", num: "Cat 7.3", name: "Neutrosophic Logic",    method_class: "Neutrosophic_Logic" },
      { id: "cat7_4", num: "Cat 7.4", name: "Interval Fuzzy Sets",   method_class: "Interval_Fuzzy_Sets" },
      { id: "cat7_5", num: "Cat 7.5", name: "Z-numbers",             method_class: "Z_Numbers" },
      { id: "cat7_6", num: "Cat 7.6", name: "PLTS",                  method_class: "PLTS" },
      { id: "cat7_7", num: "Cat 7.7", name: "Plithogenic Sets",      method_class: "Plithogenic_Sets" },
      { id: "cat7_8", num: "Cat 7.8", name: "Belief Rule Base",      method_class: "Belief_Rule_Base" },
      { id: "cat7_9", num: "Cat 7.9", name: "Quantum Probability",   method_class: "Quantum_Probability" }
    ]
  },
  {
    id: "cat8", num: "Cat 8", name: "ML & AI Pattern Detection",
    description: "Machine learning anomaly detection — Stage 2 (parked)",
    color: "#64748b", parked: true,
    modules: [
      { id: "cat8_1", num: "Cat 8.1", name: "Isolation Forest",                method_class: "Isolation_Forest" },
      { id: "cat8_2", num: "Cat 8.2", name: "Portfolio Outlier Detection",     method_class: "Portfolio_Outlier" },
      { id: "cat8_3", num: "Cat 8.3", name: "Signal Trajectory Classifier",    method_class: "Trajectory_Classifier" },
      { id: "cat8_4", num: "Cat 8.4", name: "Cross-project Pattern Detector",  method_class: "Cross_Project_Pattern" },
      { id: "cat8_5", num: "Cat 8.5", name: "Anomaly Score",                   method_class: "Anomaly_Score" }
    ]
  },
  {
    id: "cat9", num: "Cat 9", name: "Governance & Compliance",
    description: "Named authority, required action, audit trail — ALWAYS LAST",
    color: "#e0556b",
    modules: [
      { id: "cat9_1", num: "Cat 9.1", name: "ABM Governance Layer", method_class: "abm_governance" }
    ]
  }
];

/* Per-module status lookup. Reads from live project shape:
     project.signals.{mc,cusum,doc,decision}.status / .state
     project.simulationSignals.signal_array[*].method_class / .status_color
   Returns null when the module hasn't been computed yet. */
window.getModuleStatus = function (methodClass, project) {
  if (!project) return null;
  const s = project.signals || {};
  const sim = (project.simulationSignals && project.simulationSignals.signal_array) || [];
  switch (methodClass) {
    case "monte_carlo":            return s.mc ? s.mc.status : null;
    case "cusum":                  return s.cusum ? s.cusum.status : null;
    case "doc_risk":               return s.doc ? s.doc.status : null;
    case "conservative_dominance": return s.decision ? s.decision.state : null;
    case "abm_governance":         return s.decision ? s.decision.state : null;
    default: {
      const found = sim.find((m) => m.method_class === methodClass);
      return found ? (found.status_color || found.status || null) : null;
    }
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
