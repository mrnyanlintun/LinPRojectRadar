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
window.LIN_TAXONOMY_COUNTS = { registered: 31, inService: 31, retired: 0, serverComputes: 31, supplied: 0 };
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
      { id: 'a2_9', module_id: 'A2.9', name: 'Resource Loading Index', method_class: 'Resource_Loading', active: true, required: ['plannedLaborHours','actualLaborHours'] },
      { id: 'a2_12', module_id: 'A2.12', name: 'Critical Path Analysis', method_class: 'Critical_Path_Analysis', active: true, required: ['scheduleNetwork'] }
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
      { id: 'b1_2', module_id: 'B1.2', name: 'Weighted Voting', method_class: 'Weighted_Voting', active: true, required: ['cpi','spi','docRiskScore'] }
    ]
  },
  {
    id: 'c1', key: 'C1', name: 'Data Integrity',
    group: 'C', groupName: 'Data and Evidence Health',
    color: '#94a3b8',
    description: 'Evidence quality of the underlying document set. Authoring-time only: these describe how trustworthy the evidence is, never the condition of the project.',
    modules: [
      { id: 'c1_5', module_id: 'C1.5', name: 'Information Completeness Ratio', method_class: 'Information_Completeness_Ratio', active: true, authoringOnly: true, excludeFromProjectStatus: true, required: ['bac'] }
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

/* ---------------------------------------------------------------------------
   RUN 90, AMENDED BY RUN 95. THE WEIGHTED PERFORMANCE CATEGORIES, AND THEY ARE
   THE ONLY THING THE TWO CHARTS DRAW. THERE ARE FIVE OF THEM SINCE RUN 95.

   The owner's ruling, Run 90 section 2: only Cost and EVM Performance, Schedule,
   Cost Risk, Document Signals and Delivery Quality render. Run 95 retired every
   module Systems and Dynamics held, so it holds none in service and is not a
   category of this platform any more -- it is absent from the generated roster
   above, from the weighted profile, and from both charts.
   Everything else -- Data Integrity, Signal Synthesis, Evidence Combination,
   Regulatory and Authority Thresholds, Decision Optimisation -- runs in the
   background, informs the recommendation, and does not appear.

   RESOLVED AGAINST THE TREE, NOT AGAINST THE ORDER'S NAMES. The order names them
   loosely. The tree's own resolution is
   `server/app/simulation/models_gov.py:WEIGHTED_VOTING_CATEGORY_WEIGHTS`, whose
   key set is exactly A1 A2 A3 A4 A6 since Run 95, with C1 held out by an
   executable assert in `WEIGHTED_VOTING_EXCLUDED_CATEGORIES`. Those five are
   exactly the GROUP A project-level categories in the generated block above, so
   this filter is derived from the roster rather than written out as a list that
   could drift.

   THE MODULE ROSTER IS THE REGISTRY'S. `modules` on each entry comes from the
   GENERATED block, which `server/tools/build_client_taxonomy.py` writes from
   `registry.service_index()` -- modules in service only. A module retired by the
   `RETIRED ` note on its registry row is therefore already absent here, and the
   charts cannot draw one. Nothing hand-maintained is consulted.
   --------------------------------------------------------------------------- */
window.performanceCategories = function () {
  var cats = window.projectLevelCategories().filter(function (c) {
    return c && c.group === 'A';
  });
  /* RUN 95. THE COUNT IS NO LONGER SIX AND NO NUMBER IS WRITTEN HERE.

     Run 90 wrote `!== 6` and Run 95 retired every module of A5 System Dynamics
     & Complexity, so the roster now yields FIVE. The literal was not changed
     from 6 to 5 and the guard was not deleted, because either would repeat the
     failure it was written against: a stated number that drifts from the
     computed one. What the guard actually needs to catch is a category being
     DRAWN WITH NOTHING IN IT -- the owner's ruling that "an empty category is
     not a category that failed to report, there is nothing in it to report".
     That is checkable without knowing how many there should be.

     `build_client_taxonomy.py` already declines to emit such a category, so
     this should never fire; it is the client-side half of the same rule, kept
     so a hand-edited or stale artifact cannot put an empty planet on a chart.
     Whatever passes it is returned; nothing is filtered silently. */
  var empty = cats.filter(function (c) {
    return !(c.modules && c.modules.length);
  });
  if (empty.length) {
    try {
      console.warn('performanceCategories: ' + empty.length
        + ' category(ies) carry no module in service and must not be drawn: '
        + empty.map(function (c) { return c.key; }).join(', '));
    } catch (e) {}
  }
  return cats.filter(function (c) { return c.modules && c.modules.length; });
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

  /* Stored rows, keyed by the project's display id AND THEN BY PERIOD. Deliberately a plain
     cache with no fetching of its own: a module that could fetch would eventually fetch during
     a render, and a render that can issue a request is a render that can audit an evidence view
     the participant did not ask for.

     RUN 61, THE OWNER'S RULING: THE CALLER STATES WHAT IT IS ASKING FOR, AND THE ANSWER MATCHES
     THE QUESTION OR REFUSES.

     This cache used to be one row per project. That single slot is what made the defect Run 60
     measured possible: the portfolio loader primed the project's PERIOD 1 row at page load,
     the detail page then held PERIOD 4, and `rowFor` handed the period-1 row to every reader
     asking for module statuses because it was the only complete row in the slot. The page named
     a Green module as the driver of the project status and did not mention the Red one. Nothing
     in the answer said which period it came from, so no caller could have noticed.

     One slot per (project, period) removes the collision at its source, and the three shapes
     below let a caller say which of them it is:

       rowForPeriod(project, n)  — SHAPE 1. That period's row, or null. Never a substitute.
       latest(project)           — SHAPE 2. {row, period} for the latest primed period, or null.
                                   The period is returned WITH the row, so a caller that asked
                                   for "the latest" is told which one it got.
       rowsForPeriods(project, ns) — SHAPE 3. The rows for exactly those periods, in the order
                                   asked, absent periods reported as null. The longitudinal
                                   readers (CUSUM history, Milestone Trend, Period Comparison)
                                   take many rows DELIBERATELY, and making shape 1 strict must
                                   not break them.

     `rowFor(project)` remains the default and is now shape 1 in disguise: the period it asks
     for is the one the PAGE holds, `project.storedResult.period`. */
  var ROWS = Object.create(null);

  // The bucket a row with no usable period number goes in. Rows constructed in JavaScript by a
  // test harness carry no `period`; they must still be readable, and they must not be mistaken
  // for a real period's row. Kept as a string key so it can never equal a period number.
  var NO_PERIOD = "_";

  function periodKey(value) {
    var n = Number(value);
    return (value === null || value === undefined || value === "" || !isFinite(n))
      ? NO_PERIOD : n;
  }

  function bucket(projectId) {
    return projectId ? (ROWS[projectId] || null) : null;
  }

  /* Which primed row answers a request for period `want`.

     `want === null` means the caller stated no period — it has no `storedResult` to state one
     from. There is nothing to contradict, so the unstated-period bucket answers first and the
     LATEST primed period answers after it. That is not a substitution: no period was asked for.

     `want` a number is strict. A row primed for a DIFFERENT period is not an answer to it and
     is not returned. That single line is the fix. */
  function primedFor(projectId, want) {
    var b = bucket(projectId);
    if (!b) return null;
    if (want !== null) return b[want] || null;
    if (b[NO_PERIOD]) return b[NO_PERIOD];
    var best = null, bestKey = null;
    Object.keys(b).forEach(function (k) {
      if (k === NO_PERIOD) return;
      var n = Number(k);
      if (bestKey === null || n > bestKey) { bestKey = n; best = b[k]; }
    });
    return best;
  }

  // method_class -> module number ("A1.1"), built once from the taxonomy above. The stored row
  // keys modules by that number; the call sites ask by method_class.
  var METHOD_TO_MODULE_ID = Object.create(null);
  (window.LIN_CATEGORIES || []).forEach(function (cat) {
    (cat.modules || []).forEach(function (m) {
      // RUN 52, RULING 3. The module identifier field is `module_id` on both sides of the
      // wire. This is THE dispatch path: method_class -> module identifier -> the stored
      // row, which keys its modules by that identifier.
      if (m && m.method_class && m.module_id) METHOD_TO_MODULE_ID[m.method_class] = m.module_id;
    });
  });

  /* HISTORICAL METHOD-CLASS ALIASES, FOR STORED ROWS ONLY.

     THIS FILE IS THE LIVE PARTICIPANT SURFACE. index.html loads taxonomy.js and NOT
     categories.js, so an alias map declared only in categories.js is never loaded by the page
     that participants read. That distinction cost this run a wrong first fix and is recorded
     here so it is not repeated.

     Runs 28, 31 and 32 renamed seven identities' method classes. A period result stored before
     one of those runs carries the SUPERSEDED identifier, and a caller holding that row and
     asking this file about it would otherwise be dropped: METHOD_TO_MODULE_ID is keyed on the current
     identifiers only. The current identifier is always primary -- nothing emits an alias, no
     taxonomy row carries one, and an alias is only ever matched against. */
  window.LIN_HISTORICAL_METHOD_CLASS = window.LIN_HISTORICAL_METHOD_CLASS || {
    CPI_Shrinkage_Forecast: ["Regression_To_Mean"],
    Independent_EAC_Reconciliation: ["ICE_Ratio"],
    EVMS_Applicability: ["FAR_Threshold"],
    A11_Conformance: ["OMB_A11_Check"],
    EVMS_Reporting_Compliance: ["EVM_Reporting_Threshold"],
    Modification_Governance: ["Contract_Mod_Frequency"],
    Minimax_Regret_Decision_Rule: ["Regret_Minimization"],
    DSM_Rework_Cat5: ["DSM_Rework_Propagation"]
  };
  /* The module number for a method class, resolving a superseded identifier through the map
     above. Returns undefined when the class is unknown, which callers treat as "no such
     module" -- distinct from "module present but abstaining". */
  function moduleIdForMethodClass(methodClass) {
    // RUN 32 FINAL CLOSURE. THIS LINE READ `numForMethodClass(methodClass)` AND CALLED ITSELF.
    // A blanket rewrite of the three call sites in the previous closure caught the resolver's own
    // body as a fourth, so every status and result lookup on a project with a stored row threw
    // RangeError: Maximum call stack size exceeded. Nothing anywhere went red, because every
    // guard on this file compared STRINGS and the one execution probe used the other client file.
    var moduleId = METHOD_TO_MODULE_ID[methodClass];
    if (moduleId) return moduleId;
    var hist = window.LIN_HISTORICAL_METHOD_CLASS || {};
    for (var cur in hist) {
      if (hist[cur].indexOf(methodClass) !== -1) return METHOD_TO_MODULE_ID[cur];
    }
    return undefined;
  }

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
    var stored = (project && project.storedResult) || null;
    /* RUN 61. THE PERIOD THIS CALLER IS ASKING FOR IS THE ONE THE PAGE HOLDS. `storedResult` is
       the a_get projection and it carries `period`; that number is the question. A primed row
       for any other period is not an answer to it, however complete it happens to be, and
       `primedFor` will not return one. Preferring completeness over the correct period is
       exactly how a Green module came to be named as the driver of a status a Red module set. */
    var want = stored ? periodKey(stored.period) : null;
    if (want === NO_PERIOD) want = null;
    var primed = primedFor(k, want);
    if (stored && primed && !stored.module_results && primed.module_results) return primed;
    if (stored) return stored;
    return primed;
  }

  /* SHAPE 1. The row for exactly this period, or null. Never another period's. */
  function rowForPeriod(project, period) {
    var want = periodKey(period);
    if (want === NO_PERIOD) return null;
    var stored = (project && project.storedResult) || null;
    if (stored && periodKey(stored.period) === want) {
      var primed1 = primedFor(keyOf(project), want);
      if (primed1 && !stored.module_results && primed1.module_results) return primed1;
      return stored;
    }
    return primedFor(keyOf(project), want);
  }

  /* SHAPE 2. The latest period this project has a primed row for, AND WHICH ONE IT IS.
     Returns null when nothing is primed. The caller is told the period because a caller that
     asked for "the latest" and is not told which one it got cannot check the answer. */
  function latest(project) {
    var b = bucket(keyOf(project));
    var stored = (project && project.storedResult) || null;
    var bestKey = null;
    if (b) {
      Object.keys(b).forEach(function (k) {
        if (k === NO_PERIOD) return;
        var n = Number(k);
        if (bestKey === null || n > bestKey) bestKey = n;
      });
    }
    var storedKey = stored ? periodKey(stored.period) : NO_PERIOD;
    if (storedKey !== NO_PERIOD && (bestKey === null || storedKey > bestKey)) bestKey = storedKey;
    if (bestKey === null) {
      var only = primedFor(keyOf(project), null) || stored;
      return only ? { row: only, period: null } : null;
    }
    var row = rowForPeriod(project, bestKey);
    return row ? { row: row, period: bestKey } : null;
  }

  /* SHAPE 3. The longitudinal read. The periods asked for, in the order asked, each answered
     with its own row or with null. Nothing is substituted and nothing is filled in. */
  function rowsForPeriods(project, periods) {
    if (!Array.isArray(periods)) return [];
    return periods.map(function (p) {
      return { period: Number(p), row: rowForPeriod(project, p) };
    });
  }

  window.LinResults = {
    /* Record the stored row for a project, IN ITS OWN PERIOD'S SLOT. Called by the loader that
       fetched it. A row that states no period goes in the unstated-period bucket rather than
       overwriting a real period's row. */
    prime: function (projectId, row) {
      if (!projectId || !row) return;
      var b = ROWS[projectId] || (ROWS[projectId] = Object.create(null));
      b[periodKey(row.period)] = row;
    },
    rowFor: rowFor,
    rowForPeriod: rowForPeriod,
    latest: latest,
    rowsForPeriods: rowsForPeriods,
    /* Which periods this project has a primed row for. Read-only; the longitudinal callers use
       it to state the range they want instead of discovering it by trial. */
    primedPeriods: function (project) {
      var b = bucket(keyOf(project));
      if (!b) return [];
      return Object.keys(b).filter(function (k) { return k !== NO_PERIOD; })
        .map(Number).sort(function (a, c) { return a - c; });
    },
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
    var moduleId = moduleIdForMethodClass(methodClass);
    if (!moduleId) return null;
    for (var i = 0; i < row.module_results.length; i++) {
      if (row.module_results[i] && row.module_results[i].module_id === moduleId) {
        return row.module_results[i].status_color || null;
      }
    }
    return "NODATA";
  };

  /* ==================================================================================
     RUN 143, PART 2. THE CARRIED MARKING, AND WHY IT NEEDED ITS OWN ACCESSOR.

     THE DEFECT THIS EXISTS TO PREVENT, stated plainly: `getModuleStatus` above returns
     `status_color` AND NOTHING ELSE, and every client surface that renders a module band
     goes through it. Append a carried reading to `module_results` and it renders as a
     current one on every surface, with no marker, no code change and no error. That is
     this codebase's DEFAULT behaviour, not a risk it runs -- and the owner's order names a
     carried reading that renders identically to a current one as the defect this run must
     not ship. So the marking cannot be a finishing touch; it is the work.

     `getModuleStatus` IS DELIBERATELY UNCHANGED. It answers "what band", and a carried
     reading's band is its band -- it votes with it, so a caller asking for the band must
     get it. Changing its return would have moved every one of its call sites, most of
     which are sorting, counting and colouring and are correct as they stand. What is added
     is a SECOND question, asked beside the first: "and was this taken from this period?"

     Both functions read the stored row and derive nothing. A row stored before
     sim-2026.09-v71 carries no `carried` key, so `getModuleCarried` returns null for it and
     every surface renders it exactly as it renders one today. There is no default of true
     anywhere: a reading is current unless the server said it was carried. */

  /* The carrying record for one module, or null when the reading is this period's own (or
     there is no reading). Never fabricated, never inferred from the sentence: the fields are
     the ones `carry_forward.py` writes and no others. */
  window.getModuleCarried = function (methodClass, project) {
    var r = window.getModuleResult ? getModuleResult(methodClass, project) : null;
    if (!r || r.carried !== true) return null;
    return {
      fromPeriod: (r.carried_from_period === null || r.carried_from_period === undefined)
        ? null : String(r.carried_from_period),
      age: (typeof r.carried_from_age === "number") ? r.carried_from_age : null,
      /* The source period's OWN evidence sentence, unaltered. This is the sentence the
         reader is entitled to see beside a carried band, and it is stored separately from
         `evidence_metric` precisely so that carrying cannot alter it. */
      evidence: r.carried_evidence || null,
      /* THIS period's own reason for producing nothing -- kept, because a reader shown a
         carried band must also be told why nothing current exists. */
      reason: r.carried_reason || null
    };
  };

  /* The short words that go on a collapsed row head, beside the band. Deliberately short --
     it must fit next to a pill without pushing the band off a narrow screen -- and it always
     NAMES THE PERIOD rather than saying "the previous period": a removed period is invisible
     to the look-back, so after a removal those two reliably differ. */
  window.moduleCarriedLabel = function (carried) {
    if (!carried) return "";
    return carried.fromPeriod ? ("Carried from " + carried.fromPeriod) : "Carried forward";
  };

  /* The full sentence for a title/tooltip, assembled from stored text only. */
  window.moduleCarriedTitle = function (carried) {
    if (!carried) return "";
    var out = "This reading was not taken from this period's evidence. It is carried forward"
      + (carried.fromPeriod ? " from " + carried.fromPeriod : "")
      + (carried.age ? " (" + carried.age + " stored period"
         + (carried.age === 1 ? "" : "s") + " back)" : "") + ".";
    if (carried.evidence) out += " That period said: " + carried.evidence;
    if (carried.reason) out += " This period: " + carried.reason;
    return out;
  };

  /* How many of a project's rendered module readings are carried, and out of how many
     banded. A COUNT OF STORED ROWS: it asserts nothing and fills no gap. Used by the card
     headline, which the owner requires to state -- visibly -- that a full status can now be
     published on a period where few or no documents were uploaded. */
  window.projectCarriedCount = function (project) {
    var row = (window.LinResults && LinResults.rowFor) ? LinResults.rowFor(project)
      : (window.rowFor ? rowFor(project) : null);
    var mods = (row && Array.isArray(row.module_results)) ? row.module_results : [];
    var carried = 0, banded = 0;
    for (var i = 0; i < mods.length; i++) {
      if (!mods[i]) continue;
      if (mods[i].status_color) banded += 1;
      if (mods[i].carried === true) carried += 1;
    }
    return { carried: carried, banded: banded };
  };

  /* The module's own abstention message, read verbatim from the stored row's `abstained` list
     (registry.py run_all(): {module_id, reason}, reason=None when the module gave none).
     Returns null when there is no stored row, the row predates the column (abstained is NULL),
     or this module gave no reason — never fabricated. This is the ONLY source for the reason
     text: it is not derived from status, not reworded, not synthesised. */
  window.getModuleAbstentionReason = function (methodClass, project) {
    var row = rowFor(project);
    if (!row || !Array.isArray(row.abstained)) return null;
    var moduleId = moduleIdForMethodClass(methodClass);
    if (!moduleId) return null;
    for (var i = 0; i < row.abstained.length; i++) {
      var a = row.abstained[i];
      if (a && a.module_id === moduleId) return a.reason || null;
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
    var moduleId = moduleIdForMethodClass(methodClass);
    if (!moduleId) return null;
    for (var i = 0; i < row.module_results.length; i++) {
      if (row.module_results[i] && row.module_results[i].module_id === moduleId) {
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
    var stored = row.category_statuses[cat.key];
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
    /* RUN 61. Same period rule as `rowFor`: the fuller copy consulted here is the one for the
       period the page holds, never another period's. */
    var wantFull = (project && project.storedResult) ? periodKey(project.storedResult.period) : NO_PERIOD;
    var full = primedFor(keyOf(project), wantFull === NO_PERIOD ? null : wantFull);
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
       contributes_to_project_status() excludes Group C (Data and Evidence Health). RUN 97:
       Group D (Portfolio Level) is not excluded any more because it no longer exists -- D1
       Portfolio Health and its five retired modules are removed from the taxonomy.
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
