/* global LinNeuralFlow — dynamic neural signal flow for project detail page */
(function () {
  'use strict';

  // ─── Document types (27 backend keys, ordered to match DOC_TO_CATS) ─────────
  // The individual `rfi` type is retired (registers/logs only — see
  // extraction_fields.py DOC_TYPES); its row is gone rather than repointed, since
  // `rfi_log` below is already the structurally-correct row for that traffic.
  // `submittal` is keyed on its current canonical name, `submittal_register`
  // (extraction_fields.py LEGACY_TYPE_ALIASES) — the classified/event docType this
  // diagram compares against is always the canonical name, never the retired alias.
  var DOC_KEYS = [
    'contract_value','schedule_of_values','pay_application','time_phased_schedule',
    'schedule_update','monthly_report','change_order','submittal_register',
    'oac_minutes','field_report','inspection_report','ncr_log',
    'subcontractor_report','procurement_log','lookahead_schedule','resource_report',
    'cost_report','past_performance_report','safety_report','quality_audit_report',
    'environmental_report','historical_data','commissioning_report',
    'correspondence_notice','risk_register','rfi_log','rfa_log',
  ];
  function docLabel(key) {
    var lbl = window.LinSignals && LinSignals.DOC_TYPE_LABEL && LinSignals.DOC_TYPE_LABEL[key];
    if (lbl) return lbl;
    return key.split('_').map(function(w) { return w.charAt(0).toUpperCase() + w.slice(1); }).join(' ');
  }

  // These three types are confirmed by the document set's creator to be deliberately
  // absent from this corpus (not gaps). The platform has no per-document-type
  // applicability signal to derive this from — unlike modules, which carry a
  // `sectors` list on their taxonomy entry (see taxonomy.js LIN_MODULE_SECTORS) that
  // getModuleStatus() reads to decide NA — so this is a hardcoded editorial list, not
  // a computed one. See REPORT_2026-08-09_document-rows.md Part 4 for why no
  // data-driven distinction was available.
  var DOC_NOT_APPLICABLE = {
    'past_performance_report': true,
    'historical_data': true,
    'commissioning_report': true,
  };

  // ─── Fallback category definitions (10 project-level; Portfolio Health is
  // portfolio-scale and not part of this diagram) — used only if
  // LIN_CATEGORIES is absent (script-order failure); canonical source is
  // categories.js ───────────────────────────────────────────────────────────
  // group/groupName follow NAMING_AUTHORITY's current taxonomy (Groups A-D),
  // mapped onto this fallback's legacy category order on a best-effort basis;
  // this path only runs when LIN_CATEGORIES failed to load (script-order
  // failure) — the canonical source (taxonomy.js) always carries the
  // authoritative group assignment.
  var FB_CATS = [
    { id:1,  taxId:'a1', name:'Quantitative EVM',       group:'A', groupName:'Project Health',                  count:12 },
    { id:2,  taxId:'a2', name:'Schedule Simulation',    group:'A', groupName:'Project Health',                  count:11 },
    { id:3,  taxId:'a3', name:'Cost Simulation',        group:'A', groupName:'Project Health',                  count:10 },
    { id:4,  taxId:'a4', name:'Document and Risk',        group:'A', groupName:'Project Health',                  count:10 },
    { id:5,  taxId:'a5', name:'System Dynamics',        group:'A', groupName:'Project Health',                  count:8  },
    { id:6,  taxId:'b1', name:'Signal Synthesis',       group:'B', groupName:'Recommendation and Governance',   count:4  },
    { id:7,  taxId:'b2', name:'Evidence Combination',   group:'B', groupName:'Recommendation and Governance',   count:20 },
    { id:8,  taxId:'b3', name:'Governance and Compliance',group:'B', groupName:'Recommendation and Governance',   count:9  },
    { id:9,  taxId:'c1', name:'Data Integrity',         group:'C', groupName:'Data and Evidence Health',        count:6  },
    { id:10, taxId:'b4', name:'Decision Optimization',  group:'B', groupName:'Recommendation and Governance',   count:8  },
  ];


  // ─── Fallback module definitions: [catIdx, displayName, method_class] ───────
  var RAW_MODS = [
    // Cat 1 — Quantitative EVM (12)
    [0,'Monte Carlo EAC Forecast','Monte_Carlo_EAC'],  [0,'CUSUM Anomaly','CUSUM_Anomaly'],
    [0,'Doc Risk Score','Doc_Risk_Score'],    [0,'Bayesian EAC','Bayesian_EAC'],
    [0,'Kalman Filter','Kalman_Filter'],      [0,'ARIMA Forecast','ARIMA_Forecast'],
    [0,'Earned Schedule','Earned_Schedule'],  [0,'TCPI Monitor','TCPI_Monitor'],
    [0,'VAC Trend','VAC_Trend'],              [0,'Budget Exec Rate','Budget_Exec_Rate'],
    [0,'CPI Shrinkage Forecast','Regression_to_Mean'], [0,'Independent EAC Reconciliation Index','ICE_Ratio'],
    // Cat 2 — Schedule Simulation (11)
    [1,'PERT Network','PERT_Network'],        [1,'Line of Balance','Line_of_Balance'],
    [1,'CCPM Buffer','CCPM_Buffer'],          [1,'Schedule Compress.','Schedule_Compression'],
    [1,'Float Consumption','Float_Consumption'],[1,'S-Curve Deviation','SCurve_Deviation'],
    [1,'MTA Velocity','MTA_Velocity'],        [1,'Look-Ahead','Look_Ahead'],
    [1,'Resource Loading','Resource_Loading'],[1,'Schedule Risk P80','Schedule_Risk_P80'],
    [1,'Critical Path Idx','Critical_Path_Index'],
    // Cat 3 — Cost Simulation (10)
    [2,'RCF Prior','RCF_Prior'],              [2,'DSM Rework','DSM_Rework'],
    [2,'Contingency Burn','Contingency_Burn'],[2,'Labor Productivity','Labor_Productivity'],
    [2,'Material Cost Var','Material_Cost_Var'],[2,'Overhead Rate','Overhead_Rate'],
    [2,'Cost Risk P80','Cost_Risk_P80'],      [2,'Analogous Est','Analogous_Est'],
    [2,'Parametric Est','Parametric_Est'],    [2,'Inflation Adj','Inflation_Adj'],
    // Cat 4 — Document & Risk (10)
    [3,'Doc Risk Score','Doc_Risk_Score'],    [3,'RFI Velocity','RFI_Velocity'],
    [3,'Submittal Rejection','Submittal_Rejection'],[3,'NCR Rate','NCR_Rate'],
    [3,'Weather Impact','Weather_Impact'],    [3,'CO Frequency','CO_Frequency'],
    [3,'Dispute Escalation','Dispute_Escalation'],[3,'Subcontractor Risk','Subcontractor_Risk'],
    [3,'Procurement Risk','Procurement_Risk'],[3,'Spec Conflict','Spec_Conflict'],
    // Cat 5 — System Dynamics (8)
    [4,'DSM Propagation','DSM_Propagation'],  [4,'Sensitivity Analysis','Sensitivity_Analysis'],
    [4,'Tornado Chart','Tornado_Chart'],      [4,'Scenario Planning','Scenario_Planning'],
    [4,'Rework Feedback','Rework_Feedback'],  [4,'Queueing Model','Queueing_Model'],
    [4,'Agent-Based Supply','Agent_Based_Supply'],[4,'Discrete Event','Discrete_Event'],
    // Cat 6 — Signal Synthesis (4)
    [5,'Conservative Dom.','Conservative_Dominance'],[5,'Weighted Voting','Weighted_Voting'],
    [5,'Majority Rules','Majority_Rules'],    [5,'Worst-N-of-M','Worst_N_of_M'],
    // Cat 7 — Evidence Combination (20)
    [6,'Dempster-Shafer','Dempster_Shafer'],  [6,'Rough Sets','Rough_Sets'],
    [6,'Neutrosophic','Neutrosophic'],        [6,'Interval Fuzzy','Interval_Fuzzy'],
    [6,'Z-Numbers','Z_Numbers'],              [6,'PLTS','PLTS'],
    [6,'Plithogenic','Plithogenic'],          [6,'BRB','BRB'],
    [6,'Quantum','Quantum'],                  [6,'Pythagorean Fuzzy','Pythagorean_Fuzzy'],
    [6,'Picture Fuzzy','Picture_Fuzzy'],      [6,'Hesitant Fuzzy','Hesitant_Fuzzy'],
    [6,'Type-2 Fuzzy','Type2_Fuzzy'],         [6,'Max Entropy','Max_Entropy'],
    [6,'Possibility Theory','Possibility_Theory'],[6,'Spherical Fuzzy','Spherical_Fuzzy'],
    [6,'Fermatean Fuzzy','Fermatean_Fuzzy'],  [6,'MARCOS','MARCOS'],
    [6,'CRITIC-TOPSIS','CRITIC_TOPSIS'],      [6,'Hypersoft Sets','Hypersoft_Sets'],
    // Cat 8 — Governance & Compliance (9)
    [7,'ABM Governance','ABM_Governance'],    [7,'FAR Monitor','FAR_Monitor'],
    [7,'OMB A-11','OMB_A11'],                 [7,'EVM Threshold','EVM_Threshold'],
    [7,'CO Frequency Gov','CO_Frequency_Gov'],[7,'Quality Gate','Quality_Gate'],
    [7,'Safety Gate','Safety_Gate'],          [7,'Environmental Gate','Environmental_Gate'],
    [7,'Contractor Score','Contractor_Score'],
    // Cat 9 — Data Integrity (6)
    [8,'Missing Field Det.','Missing_Field_Detector'],[8,'Outlier Screener','Outlier_Screener'],
    [8,'Temporal Consist.','Temporal_Consistency'],[8,'Cross-Doc Conflict','Cross_Doc_Conflict'],
    [8,'Completeness Score','Completeness_Score'],[8,'Source Audit Trail','Source_Audit_Trail'],
    // Cat 10 — Decision Optimization (8)
    [9,'Pareto Front','Pareto_Front'],        [9,'MAUT','MAUT'],
    [9,'AHP Weighting','AHP_Weighting'],      [9,'TOPSIS Rank','TOPSIS_Rank'],
    [9,'Minimax Regret','Minimax_Regret_Decision_Rule'],[9,'Info Value','Info_Value'],
    [9,'Sensitivity Rank','Sensitivity_Rank'],[9,'Robust Decision','Robust_Decision'],
  ];
  // Portfolio Health (ex-Cat 8 ML/AI) is portfolio-scale — not part of this
  // project-level diagram; see the Health dialog (ingest.js/deepdive.js).

  // Canonical categories + modules from taxonomy.js (real method_class names,
  // so byClass/getModuleStatus lookups actually hit). Portfolio Health is
  // portfolio-scale and excluded from this project-level diagram. Falls back
  // to the hardcoded arrays above only if LIN_CATEGORIES failed to load.
  function buildModel() {
    var LC = window.LIN_CATEGORIES;
    if (LC && LC.length) {
      var PLC = window.projectLevelCategories ? window.projectLevelCategories()
        : LC.filter(function(c) { return !(c && c.level === 'portfolio'); });
      var cats = PLC.map(function(c, ci) {
        return { id: ci + 1, taxId: c.id, name: c.name, group: c.group,
                 groupName: c.groupName, count: (c.modules || []).length };
      });
      var mods = [];
      var idxs = PLC.map(function() { return []; });
      var catIds = PLC.map(function(c) { return c.id; });
      PLC.forEach(function(c, ci) {
        (c.modules || []).forEach(function(m) {
          idxs[ci].push(mods.length);
          // `required` is the module's own declaration of the signal keys it consumes. It is
          // what makes a DOCUMENT -> MODULE edge derivable instead of positional.
          mods.push({ mc: m.method_class, name: m.name, module_id: m.module_id, catI: ci,
                      required: (m.required || []).slice() });
        });
      });
      return { CATS: cats, MODULES: mods, catModIdxs: idxs, catIds: catIds };
    }
    var fbIdxs = FB_CATS.map(function() { return []; });
    var fbMods = RAW_MODS.map(function(row, i) {
      var ci = row[0], modI = fbIdxs[ci].length;
      fbIdxs[ci].push(i);
      return { catI: ci, name: row[1], mc: row[2], module_id: (ci + 1) + '.' + (modI + 1) };
    });
    return { CATS: FB_CATS, MODULES: fbMods, catModIdxs: fbIdxs, catIds: null };
  }

  /* ─── RUN 26. THE WIRING IS DERIVED FROM THE ARCHITECTURE, NOT FROM POSITION ──
     WHAT WAS HERE, AND WHY IT WAS WRONG. Two hand-written arrays of category
     INDICES, `DOC_TO_CATS` and `INTER_CAT`, written against the retired gapless
     Cat 1-10 scheme. `CATS` has been built from `LIN_CATEGORIES` since the
     taxonomy replaced categories.js, and that list is ELEVEN project categories
     in a different order: A1, A2, A3, A4, A5, A6, B1, B2, B3, B4, C1. Index 7
     used to mean Cat 8 Governance and now means Evidence Combination; index 5
     used to mean Signal Synthesis and now means Delivery Quality Performance;
     index 8 used to mean Data Integrity and now means Regulatory and Authority
     Thresholds. Every document row the old array sent to "Cat 8" was rendered
     landing on Evidence Combination, and every inter-category feed pointed at
     the wrong node. Measured in a real browser at the Run-26 baseline.

     Correcting the indices would only have restored a wiring that was itself
     never derived from an authority: the document lines were drawn to
     `catModIdxs[ci].slice(0, 2)`, the first two modules of a category by
     REGISTRY ORDER, which is one of the inferences Addition A forbids by name.

     WHAT REPLACES IT. Every edge is derived from a committed authority:

       DOCUMENT -> MODULE   the document contract crossed with the module's own
                            declared required inputs. A document feeds a module
                            when it emits a signal key that module requires, and
                            not otherwise.
       MODULE -> CATEGORY   registry category membership.
       CATEGORY -> CATEGORY only what the architecture master states in words:
                            "Project Evidence -> Category 9 assessment ->
                            Qualified Evidence -> analytical/governance use"
                            (section 18) and "downstream Cats 6/7/8/10 consume
                            qualified governed objects" (section 22). That is
                            Data Integrity into each of the four downstream
                            categories, and nothing else. The master states NO
                            ordering among those four, so none is drawn.
       CATEGORY -> STATUS   every project-level Group A and Group B category.
                            Group C is excluded: GROUP_ASSIGNMENT.md states that
                            Data and Evidence Health does not contribute to
                            project status, so the rollup edge must not exist.

     The full inventory, with the authority for every row and every place the
     architecture is SILENT, is code_audit/signal_flow_authoritative_edges.csv.
     The diagram is the object under test; that file is the oracle. ──────────── */

  // ---BEGIN GENERATED DOCUMENT EMISSIONS---
  // GENERATED by server/tools/build_run26_authoritative_edges.py from
  // server/app/extraction_merge.py. Do not edit by hand: the suite regenerates
  // this block and fails if the bytes differ.
  var DOC_EMISSIONS = {
    'change_order': ['bac','baselineContractSum','changeOrderCount'],
    'commissioning_report': ['docRiskScore'],
    'contract_value': ['bac','baselineContractSum','baselineEnd','baselineStart'],
    'correspondence_notice': ['docRiskScore'],
    'cost_report': ['indirectCostActual','indirectCostPlan','materialCostBaseline','materialCostCurrent'],
    'environmental_report': ['environmentalComplianceRate','environmentalViolations'],
    'field_report': ['docRiskScore','floatRemaining','qualityDeficienciesNoted','weatherDaysLost'],
    'historical_data': ['analogousBac','analogousFinalCost','analogousOverrunPct'],
    'inspection_report': ['criticalDeficiencyCount','docRiskScore','itemsFailed','itemsInspected','qualityDeficienciesNoted'],
    'lookahead_schedule': ['activitiesConstrained','activitiesPlanned','lookaheadWeeks'],
    'monthly_report': ['ac','actualPctComplete','bac','ev','plannedPctComplete','pv'],
    'ncr_log': ['ncrClosed','ncrIssued','ncrOpen'],
    'oac_minutes': ['docRiskScore','environmentalIssuesDiscussed','outstandingActionItems','qualityIssuesDiscussed','safetyActionsOpen','safetyIncidentsDiscussed','subcontractorDisputes','subcontractorIssuesDiscussed','weatherDaysDiscussed'],
    'past_performance_report': ['costRating','overallRating','qualityRating','scheduleRating'],
    'pay_application': ['ac','actualPctComplete','bac','ev','originalContingency','remainingContingency','workPeriodFrom','workPeriodTo'],
    'procurement_log': ['longLeadAtRisk','longLeadDelayed','longLeadItemsTotal'],
    'quality_audit_report': ['criticalFindings','qualityAuditScore','totalFindings'],
    'resource_report': ['actualLaborHours','plannedLaborHours'],
    'rfa_log': ['rfaApproved','rfaAvgReviewDays','rfaOpen','rfaRejected','rfaResubmit','rfaTotal','submittalsRejected','submittalsTotal'],
    'rfi_log': ['rfiAvgResponseDays','rfiCount','rfiOldestOpenDays','rfiOpen','rfiOverdue','rfiPeriodDays'],
    'risk_register': ['docRiskScore'],
    'safety_report': ['oshaIncidentRate','totalManhours'],
    'schedule_of_values': ['bac','ev'],
    'schedule_update': ['activitiesConstrained','activitiesPlanned','consumedFloat','lookaheadWeeks','plannedPctComplete','pv','totalFloat'],
    'subcontractor_report': ['subcontractorComplianceScore'],
    'submittal_register': ['docRiskScore','submittalsRejected','submittalsTotal'],
    'time_phased_schedule': ['consumedFloat','plannedPctComplete','pv','totalFloat'],
  };
  // ---END GENERATED DOCUMENT EMISSIONS---

  // The categories the architecture master names as consuming qualified governed
  // objects rather than raw evidence, by taxonomy id. Verified against the master
  // sections 15, 18 and 22, not taken from a brief.
  var QUALIFIER_CAT = 'c1';
  var DERIVED_CATS = ['b1', 'b2', 'b3', 'b4'];
  // Group C measures evidence quality and does not roll up into project status.
  var NO_STATUS_ROLLUP = ['c1'];

  // ─── Colors ──────────────────────────────────────────────────────────────────
  var SC = window.LIN_STATUS_COLORS;
  var COL = {
    Green:SC.Green, Yellow:SC.Yellow, Amber:SC.Amber,
    Red:SC.Red,     None:SC.None,     Complete:SC.Complete,
    // Not a verdict, not a severity: a module not relevant to this project's sector
    // (construction-phase on Design, or the reverse). Its own blue, distinct from Complete.
    NotRelevant:SC.NotRelevant,
    DocOn:'#a0bcd8', DocOff:'#1e2a3c',
  };
  // Complete ranks alongside Green (blue is a display colour, not a severity). NotRelevant sits
  // beside None (neither votes -- see contributesToProjectStatus / compute.py's rollup, which
  // never sees either), listed separately only so worstStatus never folds one into the other.
  var STATUS_RANK = { Red:0, Amber:1, Yellow:2, Green:3, Complete:3, None:4, NotRelevant:4 };

  function statusFromSig(r) {
    if (!r) return 'None';
    // NOTE: the hexes below are INPUT normalisation, not palette definitions —
    // stored status_color is normally a name ("Green"), but older records may
    // carry a raw hex from the pre-centralisation palette. They stay pinned to
    // those historical values on purpose; do not "update" them to the current
    // palette or legacy records stop resolving. Output colour comes from COL.
    var sc = String(r.status_color || r.status || '').toLowerCase();
    if (sc === 'green'  || sc === '#3fcaa6') return 'Green';
    if (sc === 'yellow' || sc === '#f0c040') return 'Yellow';
    if (sc === 'amber'  || sc === '#e2b13c') return 'Amber';
    if (sc === 'red'    || sc === '#e0556b') return 'Red';
    if (sc === 'light-amber') return 'Yellow';   // categories.js ranks light-amber with yellow
    if (sc === 'complete' || sc === 'blue' || sc === '#4ea0ff') return 'Complete';
    return 'None';
  }
  function colFor(s) { return COL[s] || COL.None; }
  function worstStatus(arr) {
    var r = 4;
    arr.forEach(function(s) { if (STATUS_RANK[s] !== undefined && STATUS_RANK[s] < r) r = STATUS_RANK[s]; });
    return ['Red','Amber','Yellow','Green','None'][r];
  }
  function normKey(s) { return String(s).toLowerCase().replace(/[^a-z0-9]/g, ''); }
  function trunc(s, n) { s = String(s); return s.length > n ? s.slice(0, n-1) + '…' : s; }
  function escH(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  // ─── SVG helper ──────────────────────────────────────────────────────────────
  var NS = 'http://www.w3.org/2000/svg';
  function se(tag, attrs, parent) {
    var e = document.createElementNS(NS, tag);
    if (attrs) for (var k in attrs) if (Object.prototype.hasOwnProperty.call(attrs,k)) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  // Color-blind-safe cue: these are the tiny (r=4) flow-diagram module dots —
  // too small for a legible letter, so status is ALSO encoded as a distinct
  // shape (circle/triangle/diamond/square/ring — matches linStatusShape() in
  // config.js). Draws a circle/rect/polygon in place of a plain circle;
  // `attrs` still carries fill/opacity/filter/stroke as before.
  function seShape(shape, cx, cy, r, attrs, parent) {
    var a = Object.assign({}, attrs || {});
    if (shape === 'square') {
      a.x = cx - r; a.y = cy - r; a.width = r * 2; a.height = r * 2;
      return se('rect', a, parent);
    }
    if (shape === 'triangle') {
      a.points = cx + ',' + (cy - r) + ' ' + (cx - r) + ',' + (cy + r) + ' ' + (cx + r) + ',' + (cy + r);
      return se('polygon', a, parent);
    }
    if (shape === 'diamond') {
      a.points = cx + ',' + (cy - r) + ' ' + (cx + r) + ',' + cy + ' ' + cx + ',' + (cy + r) + ' ' + (cx - r) + ',' + cy;
      return se('polygon', a, parent);
    }
    if (shape === 'ring') {
      a.cx = cx; a.cy = cy; a.r = r * 0.7;
      a.stroke = a.fill; a['stroke-width'] = Math.max(1, r * 0.5); a.fill = 'none';
      return se('circle', a, parent);
    }
    a.cx = cx; a.cy = cy; a.r = r;
    return se('circle', a, parent);
  }

  // ─── Inject shared styles once ───────────────────────────────────────────────
  function ensureStyles() {
    if (document.getElementById('lnf-styles')) return;
    var s = document.createElement('style');
    s.id = 'lnf-styles';
    s.textContent = [
      '@keyframes lnf-red-pulse{0%,100%{opacity:1}50%{opacity:0.5}}',
      '.lnf-red-pulse{animation:lnf-red-pulse 2s ease-in-out infinite}',
      // Directional flow: each connection class gets a dash pattern and a
      // keyframe advancing stroke-dashoffset by exactly one dash period
      // (dash+gap), so the loop is seamless. A negative offset moves the
      // dashes TOWARD the path end — i.e. in the drawn flow direction.
      '@keyframes lnf-flow-16{to{stroke-dashoffset:-16}}',
      '@keyframes lnf-flow-12{to{stroke-dashoffset:-12}}',
      '@keyframes lnf-flow-10{to{stroke-dashoffset:-10}}',
      '@keyframes lnf-flow-9{to{stroke-dashoffset:-9}}',
      '.lnf-flow-a{stroke-dasharray:10 6;animation:lnf-flow-16 6s linear infinite}',   // Class A input — high-contrast dash
      '.lnf-flow-b{stroke-dasharray:7 5;animation:lnf-flow-12 4s linear infinite}',    // Class B rollup
      '.lnf-flow-c{animation:lnf-flow-10 3s linear infinite}',                          // Class C derived (keeps its 6 4 dash attr)
      '.lnf-flow-fb{animation:lnf-flow-9 3s linear infinite}',                          // governance feedback (5 4 dash attr; path runs status→Cat9, so the stream reads as reverse flow)
      // Class A doc→module lines take the theme accent (phosphor/verdigris/
      // slate-blue) so they carry a visible hue against the surface instead of
      // grey-on-grey. Each connection is two stacked paths sharing this colour:
      // a static base + a brighter moving dash overlay (opacity set per element).
      '.lnf-a-line{stroke:var(--flow-accent,#35d6e8)}',
      '@media (prefers-reduced-motion: reduce){.lnf-flow-a,.lnf-flow-b,.lnf-flow-c,.lnf-flow-fb{animation:none!important}}',
      // Text halo: paint-order strokes a 3px surface-coloured outline UNDER the
      // glyph fill, so labels stay legible where connection lines pass beneath
      // them. Applied to every label class (module, category, doc, headers).
      '.lnf-halo{paint-order:stroke;stroke:var(--surface,#0b0e17);stroke-width:3px;stroke-linejoin:round;stroke-linecap:round}',
      // RUN 16. A configured-but-idle edge. It carries no animation class at all; this rule
      // exists so the state is nameable in the DOM and cannot be reintroduced by a stray class
      // landing on one of the animated selectors above.
      '.lnf-static{animation:none!important}',
      '.lnf-nd{cursor:pointer}',
      '#lnf-tt{position:fixed;background:#0c1422;border:1px solid #2a3a5c;border-radius:4px;',
      '  padding:6px 10px;font-size:11px;color:#c8d4e8;pointer-events:none;z-index:9999;',
      '  max-width:230px;line-height:1.55;display:none;font-family:var(--mono,monospace);}',
      '#lnf-tt .n{font-weight:600;color:#e8f0ff}',
      '#lnf-tt .m{font-size:9px;color:#3a4a6a;margin-bottom:1px}',
      '#lnf-tt .sub{font-size:9px;color:#4a5a7a;margin-top:2px}',
    ].join('');
    document.head.appendChild(s);
  }

  // ─── Shared tooltip singleton ────────────────────────────────────────────────
  function getTooltip() {
    var t = document.getElementById('lnf-tt');
    if (!t) { t = document.createElement('div'); t.id = 'lnf-tt'; document.body.appendChild(t); }
    return t;
  }

  // ─── Main render function ─────────────────────────────────────────────────────
  // RUN 24. `drawDiagram` is the WHOLE previous `render`, unchanged in what it draws. It now
  // RETURNS the emptiness decision it already computed for its own summary sentence, so the
  // empty-state gate below keys on the SAME predicate rather than on a second copy of it.
  // See `render` at the bottom of this file for the gate.
  function drawDiagram(project, container) {
    if (!container) return null;
    container.innerHTML = '';

    ensureStyles();
    var tt = getTooltip();
    function showTT(evt, html) { tt.innerHTML = html; tt.style.display = 'block'; moveTT(evt); }
    function moveTT(evt) { tt.style.left = (evt.clientX + 14) + 'px'; tt.style.top = (evt.clientY - 10) + 'px'; }
    function hideTT() { tt.style.display = 'none'; }

    // RUN 18, GATE 2. THE EVENT LOG IS AN APPEND-ONLY AUDIT RECORD, SO IT MUST BE READ FROM THE
    // LAST RESET, NOT FROM THE BEGINNING.
    //
    // THE DEFECT THIS FIXES, found by driving a FRESH DOCUMENT at the cleared project rather
    // than only the session that performed the clear-all. Run 16 deliberately stopped the reset
    // from deleting the event log, for good reasons recorded in writes.py: deleting it destroyed
    // audit history and took Audit Trail Completeness from 100% to 0% on a project whose trail
    // was intact. The reset instead APPENDS a `signals_reset` entry. Nothing here was taught to
    // notice it. So a cleared project still carried every `signals_extracted` entry it had ever
    // recorded, and this diagram read them as current: a project with its evidence cleared drew
    // "24 UPLOADED ON THIS PROJECT" and lit twenty-four document-to-module evidence paths, while
    // correctly reporting zero modules with a result and a status of not estimable.
    //
    // It was invisible in the session that performed the clear-all only because detail.js
    // forcibly zeroes `p.events` on the in-memory copy afterwards. That is a browser-side mask
    // over a record the server still serves, which is the thing the owner's clear-all
    // requirement specifically prohibits. The mask is left in place because it is harmless once
    // this reads correctly; the truthfulness no longer depends on it.
    //
    // The boundary is the index of the LAST `signals_reset` entry. Events are appended in order
    // by _append_event, so everything after that index is evidence supplied since the reset and
    // everything before it is history. No event is hidden or deleted: the audit panel and the
    // Uploaded Documents table still read the whole log.
    var evAll = (project && Array.isArray(project.events)) ? project.events : [];
    var sinceReset = evAll;
    for (var ri = evAll.length - 1; ri >= 0; ri--) {
      var rev = evAll[ri] && (evAll[ri].event || evAll[ri].type || evAll[ri].kind);
      if (rev === 'signals_reset') { sinceReset = evAll.slice(ri + 1); break; }
    }

    // ── 1. Determine uploaded doc types from project events ───────────────────
    var uploadedNorm = {};
    sinceReset.forEach(function(e) {
      if (e.event === 'signals_extracted' && e.docType) uploadedNorm[normKey(e.docType)] = true;
    });
    // Union with signalInputs.sources (events may be partially cleared by resets)
    if (project.signalInputs && project.signalInputs.sources) {
      Object.values(project.signalInputs.sources).forEach(function(src) {
        if (src && src.docType) uploadedNorm[normKey(src.docType)] = true;
      });
    }
    function isUploaded(name) { return !!uploadedNorm[normKey(name)]; }

    // RUN 16, WORKSTREAM A4. HOW MANY DOCUMENTS THIS PROJECT HAS ACTUALLY UPLOADED.
    // Counted from the project's own extraction events, the same record the Documents panel
    // counts, unioned with the surviving `signalInputs.sources` so a partially cleared event
    // log does not undercount. It is NOT the number of document types the platform supports,
    // which is what the old column header was reporting.
    var uploadedDocCount = 0;
    (function () {
      // RUN 18, GATE 2. Counted from the last reset onward, for the reason recorded above.
      var evs = sinceReset;
      var seen = {};
      evs.forEach(function (e) {
        var ty = (e && (e.type || e.event || e.kind)) || '';
        if (ty !== 'signals_extracted') return;
        uploadedDocCount++;
        if (e.docType) seen[normKey(e.docType)] = true;
      });
      if (project && project.signalInputs && project.signalInputs.sources) {
        Object.values(project.signalInputs.sources).forEach(function (src) {
          if (!src || !src.docType) return;
          var k = normKey(src.docType);
          if (seen[k]) return;
          seen[k] = true;
          uploadedDocCount++;
        });
      }
    })();
    var uploadedTypeCount = Object.keys(uploadedNorm).length;

    // RUN 21. HOW MANY DOCUMENTS THE PROJECT STILL HOLDS FROM BEFORE THE RESET.
    //
    // THE DEFECT THIS FIXES, measured in a real browser on a RELOADED document so it is not a
    // cache artefact. Run 18 correctly made the count above a count SINCE THE LAST RESET, so a
    // cleared project stops claiming its old evidence is current. But the words beside it were
    // left saying "UPLOADED ON THIS PROJECT", and the summary strip said "This project has no
    // uploaded documents". Both are FALSE after a reset. The reset deliberately does not delete
    // documents -- its own control says so, "Clears this project's stored signal values so its
    // documents can be read again. Does not delete documents" -- and the server still holds
    // every one of them. MEASURED: a project reset after twenty-four uploads served twenty-five
    // events, reported "0 UPLOADED ON THIS PROJECT" and "no uploaded documents" after a real
    // reload, and then computed FORTY-ONE modules from those retained documents the moment
    // signals were regenerated. A reader was being told the evidence was gone while it was
    // being kept and was about to be used.
    //
    // This is the same class of defect Run 16 fixed for "96 modules": the NUMBER was right for
    // what it counted and the WORDS asserted something else. NO COUNT CHANGES HERE. The
    // since-reset figure is untouched, no document is re-admitted to the current window, and
    // nothing on the diagram becomes active. Only the retained documents are disclosed, and
    // only when there are some.
    var retainedBeforeReset = 0;
    if (sinceReset !== evAll) {
      evAll.slice(0, evAll.length - sinceReset.length).forEach(function (e) {
        var ty = (e && (e.event || e.type || e.kind)) || '';
        if (ty === 'signals_extracted') retainedBeforeReset++;
      });
    }

    // ── 2. Canonical categories/modules + status resolution ──────────────────
    var model = buildModel();
    var CATS = model.CATS, MODULES = model.MODULES, catModIdxs = model.catModIdxs, catIds = model.catIds;

    var simArr = (project.simulationSignals && project.simulationSignals.signal_array) || [];
    var byClass = {};
    simArr.forEach(function(r) { if (r && r.method_class) byClass[r.method_class] = r; });
    // Sector-abstention label for NA modules (construction-phase modules on a
    // Design project). Shown in the tooltip in place of a status word.
    var secName = (window.normalizeSector ? window.normalizeSector(project.sector)
      : String(project.sector || 'hybrid')).replace(/^./, function(c) { return c.toUpperCase(); });
    var sectorNAText = 'N/A: not applicable to ' + secName + '-sector projects';
    function modInfo(m) {
      var r = byClass[m.mc];
      var metric = r && r.evidence_metric ? String(r.evidence_metric) : null;
      // Prefer the app's shared resolver (handles computed/derived modules too)
      var st = null;
      try { if (window.getModuleStatus) st = window.getModuleStatus(m.mc, project); } catch (e) {}
      // RUN 16. `NA` covers two different absences and the counts below have to tell them
      // apart: a module excluded by this project's sector, and a module disabled platform-wide.
      // isModuleDisabled reads the taxonomy's own `disabled` flag; it is not guessed here.
      var isDis = false;
      try { isDis = !!(window.isModuleDisabled && window.isModuleDisabled(m.mc)); } catch (e) {}
      if (st === 'NA') {
        return { status: 'NotRelevant', na: true, disabled: isDis,
                 color: COL.NotRelevant, metric: null };
      }
      if (st) {
        var s = statusFromSig({ status_color: st });
        return { status: s, color: colFor(s), metric: metric };
      }
      var s2 = statusFromSig(r);
      return { status: s2, color: colFor(s2), metric: metric };
    }

    // RUN 16, WORKSTREAM A3. AN EDGE ANIMATES ONLY WHEN DATA CURRENTLY TRAVELS IT.
    //
    // Every connection used to stream its dashes unconditionally, so a project with no
    // documents, no signals and no stored result rendered the same moving topology as a fully
    // computed one. A configured dependency is not a flow. `active` is decided by the caller
    // from the CURRENT stored state and nothing else (see isEstimable below); an inactive edge
    // keeps its geometry, loses its motion, and is marked `.lnf-static` so it reads as
    // configured architecture rather than as traffic.
    //
    // Staggered start offsets so the streaming dashes don't march in lockstep. Negative delays
    // start every line mid-cycle.
    var flowIdx = 0;
    function flowAnim(el, cls, active) {
      if (!active) { el.classList.add('lnf-static'); return; }
      el.classList.add('lnf-active');
      el.classList.add(cls);
      el.style.animationDelay = (-((flowIdx++ % 16) * 0.37)).toFixed(2) + 's';
    }
    // The five verdicts a module, a category or the project rollup can carry. Anything else --
    // 'None' (no current result) and 'NotRelevant' (sector exclusion or a disabled module) --
    // is an absence of a result, not a result, and must not light a path.
    var ESTIMABLE = { Green:1, Yellow:1, Amber:1, Red:1, Complete:1 };
    function isEstimable(s) { return !!ESTIMABLE[s]; }

    // ── 3. Pre-compute all statuses ───────────────────────────────────────────
    var modInfos = MODULES.map(function(m) { return modInfo(m); });
    // Category statuses — use the app's DST fusion (categories.js), keyed by
    // the STABLE internal id (catIds[ci]) rather than array position, since
    // Portfolio Health is filtered out of this project-level CATS list.
    // Worst-of is only a fallback.
    var catStatuses = CATS.map(function(cat, ci) {
      try {
        if (window.getCategoryStatus && catIds && catIds[ci]) {
          var s = window.getCategoryStatus(catIds[ci], project);
          if (s) return s; // 'Green' | 'Yellow' | 'Amber' | 'Red' | 'Complete'
        }
      } catch (e) {}
      return worstStatus(catModIdxs[ci].map(function(mi) { return modInfos[mi].status; }));
    });

    // Project status — the app's DST project fusion (Red weighted 1.5x)
    var prjStatus = null;
    try {
      if (window.getProjectFusion) {
        var f = window.getProjectFusion(project);
        if (f && f.status) prjStatus = f.status;
      }
    } catch (e) {}
    if (!prjStatus) prjStatus = worstStatus(catStatuses);
    var prjColor = colFor(prjStatus);
    // RUN 16, GATE 5. NOTHING IS COMPUTED HERE. Every figure below is a tally over statuses the
    // SERVER produced and the browser read (getModuleStatus / getCategoryStatus /
    // getProjectFusion all read the stored row). No arithmetic, no inference, no defaults.
    var modWithResult = 0, modDisabled = 0, modNotRelevant = 0;
    modInfos.forEach(function (i) {
      if (i.disabled) { modDisabled++; return; }
      if (i.na) { modNotRelevant++; return; }
      if (isEstimable(i.status)) modWithResult++;
    });
    var modSilent = MODULES.length - modWithResult - modDisabled - modNotRelevant;
    var catEstimable = catStatuses.filter(isEstimable).length;
    var prjEstimable = isEstimable(prjStatus);

    /* ─── RUN 26. THE ONE EMPTINESS PREDICATE, HOISTED ────────────────────────
       Run 24 introduced this condition to decide whether the diagram is drawn
       unasked; it now also decides whether ANY analytical colour may appear.
       It is computed once, here, so the colour decision and the drawn/not-drawn
       decision cannot disagree -- the same reason Run 24 gave for having one
       predicate rather than two. */
    var projectIsEmpty = (uploadedDocCount === 0 && modWithResult === 0 && catEstimable === 0);

    /* ─── RUN 26. GREY, AND ONLY GREY, ON AN EMPTY PROJECT ────────────────────
       THE OWNER'S RULE, AND THE CONTRACT IT REVERSES. Until this run, a module
       or document row that is registered but NOT RELEVANT to this project drew
       in its own purple, `--status-notrelevant-text` #5b3dd6, at opacity 0.34.
       A previous owner instruction endorsed that as the correct not-relevant
       state and Runs 23 and 24 guarded it. Measured in a real browser at the
       Run-26 baseline, an empty project rendered TWELVE purple nodes -- nine
       disabled modules and three not-applicable document rows -- plus nine
       purple module-to-category strokes and one red governance arc.

       THE 2026-08-14 INSTRUCTION REVERSES THAT CONTRACT for the empty case, in
       these words: no purple document squares, no blue Not Relevant markers, no
       other analytical colour anywhere on the diagram. REGISTERED is not ACTIVE
       and NOT RELEVANT is not current evidence, so on a project with no evidence
       neither may be drawn in a colour the legend explains as a verdict or as a
       relevance judgement about THIS project. It applies to the revealed
       architecture too: revealing it is an act of the reader, not evidence.

       On a project that HAS evidence nothing here applies and the not-relevant
       marker is drawn exactly as before: the distinction is still real there,
       because there is a project state for it to be a distinction FROM.

       The reversal is recorded in code_audit/run20_anti_fossilization_register.csv
       as an owner-directed contract change, and the guards that asserted the old
       contract were turned red against this build before being rewritten. */
    function neutralOnEmpty(color, status) {
      if (!projectIsEmpty) return color;
      // An empty project has one vocabulary: no current result.
      return COL.None;
    }
    //: The stroke an EDGE gets. Same rule, and it is the reason nine purple and one red
    //: stroke left the empty diagram along with the nodes that fed them.
    function edgeStroke(status, explicitColor) {
      if (projectIsEmpty) return COL.None;
      return explicitColor || colFor(status);
    }
    //: Category lookup by the taxonomy's own stable id, never by array position. Position is
    //: what silently repointed every document line and every inter-category feed when the
    //: eleven-category taxonomy replaced the gapless Cat 1-10 order.
    function catIndexOf(taxId) {
      for (var i = 0; i < CATS.length; i++) {
        if (CATS[i] && CATS[i].taxId === taxId) return i;
      }
      return -1;
    }
    function rollsUpToStatus(ci) {
      var id = CATS[ci] && CATS[ci].taxId;
      return !id || NO_STATUS_ROLLUP.indexOf(id) < 0;
    }
    /* DOCUMENT -> MODULE, DERIVED. A document feeds a module when the document type emits a
       signal key that module declares as a required input. Both halves are authorities: the
       emissions are generated from server/app/extraction_merge.py into the block at the top of
       this file, and `required` is the module's own taxonomy declaration. Nothing here reads
       category membership, registry order or position. */
    var docToMods = DOC_KEYS.map(function(key) {
      var emits = DOC_EMISSIONS[key] || [];
      if (!emits.length) return [];
      var hits = [];
      MODULES.forEach(function(m, mi) {
        var req = m.required || [];
        for (var i = 0; i < req.length; i++) {
          if (emits.indexOf(req[i]) >= 0) { hits.push(mi); return; }
        }
      });
      return hits;
    });
    //: The document types this document row's evidence actually reaches, by category, for the
    //: hover tooltip. Derived from docToMods so the words and the lines cannot disagree.
    var docToCatNames = docToMods.map(function(mis) {
      var seen = {}, names = [];
      mis.forEach(function(mi) {
        var ci = MODULES[mi].catI;
        if (!seen[ci]) { seen[ci] = 1; names.push(CATS[ci].name); }
      });
      return names;
    });
    // The governed project-level label, read from the stored row when the server supplied one.
    // Never invented: a project with no stored result keeps the generic column heading.
    var governedLabel = null;
    try {
      if (window.getProjectFusion) {
        var gf = window.getProjectFusion(project);
        if (gf && gf.statusLabel) governedLabel = String(gf.statusLabel);
      }
    } catch (e) {}

    // ── 4. Layout geometry ────────────────────────────────────────────────────
    // Row pitch sized to the 11.5px module labels (13px pitch avoids collisions);
    // the SVG height grows with the pitch. The doc column sits further right so
    // its enlarged end-anchored labels never clip the left viewBox edge.
    var W = 1280, PAD_TOP = 45;
    var MOD_SPACE = 13, MOD_GAP = 15;
    var totalModH = MODULES.length * MOD_SPACE + (CATS.length - 1) * MOD_GAP;
    var H = Math.max(totalModH + PAD_TOP * 2, 920);

    var CX = { doc:268, mod:460, cat:760, prj:1090 };

    var DOC_SPACING = (H - PAD_TOP * 2) / (DOC_KEYS.length - 1);
    function docY(i) { return PAD_TOP + i * DOC_SPACING; }

    var modY = [];      // indexed by module flat index
    var catStartYArr = [];
    var y0 = (H - totalModH) / 2;
    var yCur = y0;
    CATS.forEach(function(cat, ci) {
      catStartYArr.push(yCur);
      catModIdxs[ci].forEach(function(mi, j) { modY[mi] = yCur + j * MOD_SPACE; });
      yCur += cat.count * MOD_SPACE + MOD_GAP;
    });

    var catCY = CATS.map(function(_, ci) {
      var mods = catModIdxs[ci];
      return (modY[mods[0]] + modY[mods[mods.length-1]]) / 2;
    });
    var PRJ_Y = H / 2;

    // ── 5. Build SVG ─────────────────────────────────────────────────────────
    var svg = se('svg', { viewBox:'0 0 '+W+' '+H, width:'100%', height:H, xmlns:NS, style:'display:block' }, container);

    // Solid panel background — page-bg underlay + surface wash — so the NYC
    // skyline art and page gradients never bleed through the diagram. On the
    // Miami (light) theme the vars resolve to the light surface automatically.
    se('rect', { x:0, y:0, width:W, height:H, fill:'var(--page-bg, #0b0e17)' }, svg);
    se('rect', { x:0, y:0, width:W, height:H, fill:'var(--surface, #0b0e17)' }, svg);

    // defs
    var defs = se('defs', {}, svg);
    var glowTargets = { Green:COL.Green, Yellow:COL.Yellow, Amber:COL.Amber, Red:COL.Red, Complete:COL.Complete, DocOn:COL.DocOn };
    Object.keys(glowTargets).forEach(function(k) {
      var f = se('filter', { id:'lnf-glow-'+k, x:'-60%', y:'-60%', width:'220%', height:'220%' }, defs);
      se('feDropShadow', { dx:'0', dy:'0', stdDeviation:'2.5', 'flood-color':glowTargets[k], 'flood-opacity':'0.85' }, f);
    });
    // arrowhead markers for inter-cat and feedback
    ['Green','Yellow','Amber','Red','Complete','None'].forEach(function(s) {
      var m = se('marker', { id:'lnf-arr-'+s, markerWidth:'5', markerHeight:'5', refX:'4', refY:'2.5', orient:'auto' }, defs);
      se('polygon', { points:'4,0 4,5 0,2.5', fill:colFor(s), opacity:'0.75' }, m);
    });
    // RUN 26. The feedback arrowhead is gone with the arc it belonged to. It was a red marker
    // polygon inside <defs>, and a red one, on every project including an empty one.

    // ── Column headers ────────────────────────────────────────────────────────
    // RUN 16, WORKSTREAMS A2, A4 AND A5. ARCHITECTURE ON THE TOP LINE, CURRENT ACTIVITY ON THE
    // SECOND, NEVER THE ONE STANDING IN FOR THE OTHER.
    //
    // These headers used to read "27 DOCUMENTS", "96 MODULES" and "11 CATEGORIES". Every one of
    // those numbers is a property of the platform's registry, not of the project on screen: 27
    // is the number of document types the extraction layer recognises, 96 the number of
    // project-level modules the registry declares, and 11 the number of registered categories.
    // A project with nothing uploaded and nothing computed therefore announced twenty-seven
    // documents and ninety-six modules. The counts are unchanged and still derived from the
    // registry rather than typed in; what changed is that they are now labelled as what they
    // are, and the project's own figures sit beneath them.
    var HEADERS = [
      // RUN 21. The words now match what the number counts. Before a reset the window IS the
      // project, so the original wording is kept exactly. After one, the figure is a
      // since-the-reset count and says so, and the retained documents are named beside it
      // instead of being silently reported as absent.
      [CX.doc, DOC_KEYS.length + ' SUPPORTED DOCUMENT TYPES',
               retainedBeforeReset > 0
                 ? (uploadedDocCount + ' UPLOADED SINCE THE RESET, ' + retainedBeforeReset +
                    ' RETAINED')
                 : (uploadedDocCount + ' UPLOADED ON THIS PROJECT')],
      [CX.mod, MODULES.length + ' REGISTERED PROJECT MODULES',
               modWithResult + ' WITH A CURRENT RESULT'],
      [CX.cat, CATS.length + ' REGISTERED CATEGORIES',
               catEstimable + ' ESTIMABLE NOW'],
      [CX.prj, (governedLabel || 'PROJECT STATUS').toUpperCase(),
               prjEstimable ? 'CURRENT' : 'NOT ESTIMABLE'],
    ];
    HEADERS.forEach(function(row) {
      var t1 = se('text', { x:row[0], y:16, 'text-anchor':'middle', fill:'var(--faint, #4a5a7a)',
        'font-size':'11', 'font-weight':'700', 'letter-spacing':'0.08em',
        'font-family':'monospace', class:'lnf-halo lnf-hdr-arch' }, svg);
      t1.textContent = row[1];
      var t2 = se('text', { x:row[0], y:30, 'text-anchor':'middle', fill:'var(--muted, #5a7898)',
        'font-size':'11', 'font-weight':'700', 'letter-spacing':'0.08em',
        'font-family':'monospace', class:'lnf-halo lnf-hdr-activity' }, svg);
      t2.textContent = row[2];
    });

    // ── 6. Connection layers ──────────────────────────────────────────────────
    var lineG  = se('g', { id:'lnf-lines'  }, svg);
    var interG = se('g', { id:'lnf-intercat' }, svg);

    // Class B (rollup): cat → project — streaming dashes, arrowhead at the status node edge.
    // RUN 26. NOT DRAWN FOR A CATEGORY THE AUTHORITY EXCLUDES FROM THE ROLLUP.
    // GROUP_ASSIGNMENT.md states that Data and Evidence Health does not contribute to project
    // status, and compute.py's rollup never sees it. The edge was being drawn anyway, which
    // asserted a dependency the authority positively denies.
    var catPrjEls = catStatuses.map(function(cs, ci) {
      if (!rollsUpToStatus(ci)) return null;
      var x1=CX.cat+9, y1=catCY[ci], x2=CX.prj-26, y2=PRJ_Y, mx=(x1+x2)/2;
      var p = se('path', { d:'M'+x1+','+y1+' C'+mx+','+y1+' '+mx+','+y2+' '+x2+','+y2,
        fill:'none', stroke:edgeStroke(cs), 'stroke-width':'1.5', opacity:'0.35',
        'stroke-linecap':'round', 'marker-end':'url(#lnf-arr-'+cs+')',
        'data-edge-type':'CATEGORY -> PROJECT STATUS', 'data-edge-src':CATS[ci].name,
        'data-edge-dst':'Project status' }, lineG);
      // A category rollup path carries traffic only when the category has a current estimable
      // result. Otherwise the relationship is configured and idle.
      if (!isEstimable(cs)) p.setAttribute('opacity', '0.14');
      flowAnim(p, 'lnf-flow-b', isEstimable(cs));
      return p;
    });

    // Class B (rollup): mod → cat — streaming dashes, no arrowhead (volume too
    // high). Base opacity nudged 0.25 → 0.35 so it isn't overpowered by the now
    // brighter Class A doc→module lines (keeps the rollup readable).
    var MODCAT_OP = '0.35';
    var modCatEls = MODULES.map(function(m, mi) {
      var ci=m.catI, x1=CX.mod+4, y1=modY[mi], x2=CX.cat-9, y2=catCY[ci], mx=(x1+x2)/2;
      var p = se('path', { d:'M'+x1+','+y1+' C'+mx+','+y1+' '+mx+','+y2+' '+x2+','+y2,
        fill:'none', stroke:edgeStroke(modInfos[mi].status, modInfos[mi].color),
        'stroke-width':'0.8', opacity:MODCAT_OP, 'stroke-linecap':'round',
        'data-edge-type':'MODULE -> CATEGORY', 'data-edge-src':m.name,
        'data-edge-dst':CATS[ci].name }, lineG);
      // Same rule one level down: a module path is live only when that module has a current
      // result. A disabled, abstaining, sector-excluded or never-computed module contributes
      // nothing, and its line must not move as though it did.
      var modLive = isEstimable(modInfos[mi].status);
      if (!modLive) p.setAttribute('opacity', '0.14');
      flowAnim(p, 'lnf-flow-b', modLive);
      return p;
    });

    // Class A (input): doc → module. Drawn as TWO stacked paths sharing the
    // theme accent (var --flow-accent via .lnf-a-line): a STATIC base plus a
    // brighter animated dash overlay, so the motion reads without relying on a
    // single faint stroke. UPLOADED docs render bright (base .45 / dash .75,
    // 1.6px); not-uploaded stay faint (.12) — the contrast is the signal.
    // Store per-doc arrays of {base, dash, modI} for hover interaction.
    var A_BASE = { on: '0.45', off: '0.12' };
    var A_DASH = { on: '0.75', off: '0.12' };
    var A_W    = { on: '1.6',  off: '0.7'  };
    var docLineMap = DOC_KEYS.map(function() { return []; });
    DOC_KEYS.forEach(function(key, di) {
      var up = isUploaded(key);
      var baseOp = up ? A_BASE.on : A_BASE.off, dashOp = up ? A_DASH.on : A_DASH.off, w = up ? A_W.on : A_W.off;
      // RUN 26. The modules this document actually feeds, by field consumption, not the first
      // two modules of a category by registry order. `docToMods` is derived at build time from
      // the generated document-emission map and each module's own declared required inputs.
      docToMods[di].forEach(function(mi) {
        var x1=CX.doc+5, y1=docY(di), x2=CX.mod-4, y2=modY[mi], mx=(x1+x2)/2;
        var d = 'M'+x1+','+y1+' C'+mx+','+y1+' '+mx+','+y2+' '+x2+','+y2;
        var edgeAttrs = { 'data-edge-type':'DOCUMENT -> MODULE', 'data-edge-src':key,
                          'data-edge-dst':MODULES[mi].name };
        var base = se('path', { d:d, class:'lnf-a-line', fill:'none',
          'stroke-width':w, opacity:baseOp, 'stroke-linecap':'round',
          'data-edge-type':edgeAttrs['data-edge-type'], 'data-edge-src':key,
          'data-edge-dst':MODULES[mi].name }, lineG);
        // The animated overlay is the SAME edge drawn a second time, so it carries the same
        // identity. An edge that does not name itself cannot be reconciled against the
        // inventory, and a silently unnamed path is exactly where a fabricated one would hide.
        var dash = se('path', { d:d, class:'lnf-a-line lnf-a-dash', fill:'none',
          'stroke-width':w, opacity:dashOp, 'stroke-linecap':'round',
          'data-edge-type':edgeAttrs['data-edge-type'], 'data-edge-src':key,
          'data-edge-dst':MODULES[mi].name }, lineG);
        // An evidence path is live only when this project has actually uploaded that
        // document type. The unlit rows were already faint; now they are also still.
        flowAnim(dash, 'lnf-flow-a', up);
        docLineMap[di].push({ base:base, dash:dash, modI:mi });
      });
    });

    // ── Class A hover helpers ─────────────────────────────────────────────────
    // A hover dims every doc→module line to 0.2 so the highlighted path pops,
    // then raises the connected lines to 0.85 / 2.2px; leaving restores each
    // line to its per-upload default.
    function classAReset() {
      docLineMap.forEach(function(arr, di) {
        var up = isUploaded(DOC_KEYS[di]);
        arr.forEach(function(e) {
          e.base.setAttribute('opacity', up ? A_BASE.on : A_BASE.off);
          e.dash.setAttribute('opacity', up ? A_DASH.on : A_DASH.off);
          e.base.setAttribute('stroke-width', up ? A_W.on : A_W.off);
          e.dash.setAttribute('stroke-width', up ? A_W.on : A_W.off);
        });
      });
    }
    function classAFocus(match) {
      docLineMap.forEach(function(arr, di) {
        arr.forEach(function(e) {
          if (match(e, di)) {
            e.base.setAttribute('opacity', '0.85'); e.dash.setAttribute('opacity', '0.85');
            e.base.setAttribute('stroke-width', '2.2'); e.dash.setAttribute('stroke-width', '2.2');
          } else {
            e.base.setAttribute('opacity', '0.2'); e.dash.setAttribute('opacity', '0.2');
          }
        });
      });
    }

    // inter-category dashed lines
    // RUN 26. ONLY THE CATEGORY-TO-CATEGORY DEPENDENCIES THE ARCHITECTURE MASTER STATES.
    // Section 18 states the target architecture "Project Evidence -> Category 9 assessment ->
    // Qualified Evidence -> analytical/governance use", and section 22 that the downstream
    // categories consume qualified governed objects. That gives Data Integrity into each of
    // the four downstream categories. The master states NOTHING about which analytical
    // categories supply the signal states those categories synthesize, and NOTHING about any
    // ordering among the four; the previous twenty-seven feeds asserted both. Where the
    // architecture is silent no edge is drawn, and the silence is reported instead.
    var interCatEls = [];
    var qualI = catIndexOf(QUALIFIER_CAT);
    if (qualI >= 0) {
      DERIVED_CATS.forEach(function(taxId, k) {
        var dst = catIndexOf(taxId);
        if (dst < 0) return;
        var cs = catStatuses[qualI];
        var x1=CX.cat+9, y1=catCY[qualI], x2=CX.cat+9, y2=catCY[dst], xh=860 + k * 20;
        var line = se('path', {
          d:'M'+x1+','+y1+' C'+xh+','+y1+' '+xh+','+y2+' '+x2+','+y2,
          fill:'none', stroke:edgeStroke(cs), 'stroke-width':'1', opacity:'0.45',
          'stroke-dasharray':'6 4', 'marker-end':'url(#lnf-arr-'+cs+')',
          'data-edge-type':'CATEGORY -> CATEGORY', 'data-edge-src':CATS[qualI].name,
          'data-edge-dst':CATS[dst].name
        }, interG);
        if (!isEstimable(cs)) line.setAttribute('opacity', '0.16');
        flowAnim(line, 'lnf-flow-c', isEstimable(cs));
        interCatEls.push({ el:line, srcI:qualI, dstI:dst });
      });
    }

    // RUN 26. THE GOVERNANCE FEEDBACK ARC IS REMOVED.
    // It drew PROJECT STATUS -> CATEGORY, which is not one of the architecture's edge kinds at
    // all, and it targeted `catCY[7]` -- an index written for the retired Cat 1-10 scheme, so
    // on the current eleven-category taxonomy it pointed at Evidence Combination rather than at
    // any governance category. No committed authority states that project status feeds back
    // into a category, and the master's governance flow (section 17) ends at a human decision
    // rather than looping. It was also the only red stroke on an empty project. Drawn from
    // nothing, it is not drawn.
    var fbEl = null, fbLabelEl = null;

    // ── 7. Node layer ─────────────────────────────────────────────────────────
    var nodeG = se('g', { id:'lnf-nodes' }, svg);

    // Category group micro-labels (dim, above each module group)
    CATS.forEach(function(cat, ci) {
      var firstMI = catModIdxs[ci][0];
      var t = se('text', {
        x:CX.mod-6, y:modY[firstMI]-9,
        fill:'var(--faint, #1e2c44)', 'font-size':'9', 'font-family':'monospace',
        'text-anchor':'end', 'font-weight':'700', class:'lnf-halo'
      }, nodeG);
      t.textContent = cat.group || '';
    });

    // Module dots + right-side labels (11.5px, truncated 26 chars — full
    // names stay available in the hover tooltip)
    var modNodeEls = MODULES.map(function(m, mi) {
      var info = modInfos[mi];
      // POST-RUN-22 UI CORRECTION. ACTIVE MEANS A CURRENT RESULT, NOT A REGISTRY FACT.
      //
      // THE DEFECT THIS FIXES, reproduced in a real browser on a brand-new EMPTY project
      // (code_audit/run16_final_flow_run23_signal_flow_ui.csv, state A-empty, before the fix):
      // nine module dots rendered at the ACTIVE opacity tier (0.85) in the not-relevant
      // colour AND carried a glow filter, and three document rows rendered as lit squares at
      // 0.75, on a project with zero documents and zero results. The illumination was keyed on
      // `status !== 'None'`, and 'NotRelevant' — a module disabled platform-wide or excluded by
      // this project's sector — is not 'None'. That is a property of the REGISTRY, not of this
      // project's current evidence, so the diagram was lighting capability as activity. (The
      // glow filter it asked for, `lnf-glow-NotRelevant`, is not even defined in defs, which is
      // its own proof that this branch was never meant to light.)
      //
      // The rule is now the same one the edges already used: only an ESTIMABLE status — a
      // current stored verdict — reaches the active tier. Everything else keeps its geometry,
      // its shape and its colour hint, and stays visually neutral. `data-active` records the
      // decision in the DOM so it is nameable rather than inferred from an opacity.
      var live = isEstimable(info.status);
      var glow = live ? 'url(#lnf-glow-'+info.status+')' : null;
      var g = se('g', { class:'lnf-nd', 'data-kind':'module', 'data-active':live ? 'true' : 'false' }, nodeG);

      // RUN 26. On an EMPTY project a not-relevant or disabled module is drawn in the
      // no-data colour like every other silent module. Nine purple dots were measured here on
      // a project with no evidence; a platform-wide disablement and a sector exclusion are
      // registry facts, and REGISTERED is not ACTIVE.
      var circleAttrs = {
        fill:neutralOnEmpty(info.color, info.status),
        opacity:live ? '0.85' : (projectIsEmpty || info.status === 'None' ? '0.20' : '0.34'),
        stroke:'none', 'data-active':live ? 'true' : 'false',
        'data-status':projectIsEmpty ? 'None' : info.status };
      if (glow) circleAttrs.filter = glow;
      var dotShape = window.linStatusShape ? linStatusShape(info.status) : 'circle';
      var circle = seShape(dotShape, CX.mod, modY[mi], 4, circleAttrs, g);
      if (info.status === 'Red') circle.classList.add('lnf-red-pulse');

      var lbl = se('text', {
        x:CX.mod+8, y:modY[mi],
        fill:live ? 'var(--muted, #5a7898)' : 'var(--faint, #1e2c44)',
        'font-size':'11.5', 'font-family':'monospace',
        'dominant-baseline':'middle', 'pointer-events':'none', class:'lnf-halo'
      }, g);
      if (!live) lbl.setAttribute('opacity','0.55');
      lbl.textContent = trunc(m.name, 26);

      circle.style.transformOrigin = CX.mod + 'px ' + modY[mi] + 'px';
      g.addEventListener('mouseenter', (function(m, mi, info, circle) {
        return function(evt) {
          circle.style.transform = 'scale(1.5)';
          var metStr = info.metric ? '<div class="sub">metric: '+escH(info.metric)+'</div>' : '';
          var statusLabel = info.na ? escH(sectorNAText) : info.status;
          showTT(evt,'<div class="n">'+escH(m.name)+'</div><div class="sub" style="color:'+info.color+'">'+statusLabel+'</div>'+metStr+'<div class="sub">'+escH(CATS[m.catI].name)+'</div>');
          modCatEls[mi].setAttribute('opacity','0.70');
          modCatEls[mi].setAttribute('stroke-width','1.4');
          classAFocus(function(e){ return e.modI===mi; });
        };
      })(m, mi, info, circle));
      g.addEventListener('mousemove', moveTT);
      g.addEventListener('mouseleave', (function(mi, info, circle) {
        return function() {
          hideTT();
          circle.style.transform = '';
          modCatEls[mi].setAttribute('opacity', MODCAT_OP);
          modCatEls[mi].setAttribute('stroke-width','0.8');
          classAReset();
        };
      })(mi, info, circle));
      return g;
    });

    // Category nodes
    // Gapless 1-10 project-level roles, keyed by cat id (Cat 2-3 share a role;
    // Cat 6-7 share a role). Portfolio Health's "how this project compares to
    // the portfolio" caption now lives in the Health dialog, not here.
    var CAT_ROLE = {
      1: 'what is happening',
      2: 'what will happen', 3: 'what will happen',
      4: 'what is being said',
      5: 'how components interact',
      6: 'what the evidence collectively means', 7: 'what the evidence collectively means',
      8: 'what action is required',
      9: 'how much to trust the signals',
      10: 'what the best decision is'
    };
    var catNodeEls = CATS.map(function(cat, ci) {
      var cs=catStatuses[ci], color=colFor(cs);
      // Same rule as the module dots: a REGISTERED category is not an ACTIVE one. A category
      // reaches the active tier only when the app's own fusion returns a current estimable
      // verdict for it; a registered-but-silent category stays neutral.
      var catLive = isEstimable(cs);
      var glow = catLive ? 'url(#lnf-glow-'+cs+')' : null;
      var x=CX.cat, y=catCY[ci];
      var g = se('g', { class:'lnf-nd', 'data-kind':'category', 'data-active':catLive ? 'true' : 'false' }, nodeG);
      var cAttrs = { fill:neutralOnEmpty(color, cs), opacity:catLive ? '0.88' : '0.28',
                     stroke:'none', 'data-active':catLive ? 'true' : 'false',
                     'data-status':projectIsEmpty ? 'None' : cs };
      if (glow) cAttrs.filter = glow;
      var catShape = window.linStatusShape ? linStatusShape(cs) : 'circle';
      var circle = seShape(catShape, x, y, 9, cAttrs, g);
      circle.style.transformOrigin = x + 'px ' + y + 'px';
      if (cs==='Red') circle.classList.add('lnf-red-pulse');
      // group letter + name label, nudged up so the role caption sits directly beneath
      var t = se('text', { x:x+14, y:y-4, fill:'var(--muted, #6a8aaa)', 'font-size':'13', 'font-family':'monospace', 'dominant-baseline':'middle', class:'lnf-halo' }, g);
      t.textContent = (cat.group ? cat.group+' · ' : '') + cat.name;
      var role = CAT_ROLE[cat.id];
      if (role) {
        var rt = se('text', { x:x+14, y:y+9, fill:'var(--faint, #6f7d90)', 'font-size':'9', 'font-style':'italic', 'font-family':'monospace', 'dominant-baseline':'middle', class:'lnf-halo lnf-cat-role' }, g);
        rt.textContent = role;
        var rtitle = se('title', {}, rt);
        rtitle.textContent = cat.name + ' · ' + role;
      }

      g.addEventListener('mouseenter', (function(cat, ci, cs, color, circle) {
        return function(evt) {
          circle.style.transform = 'scale(1.22)';
          var icIn  = interCatEls.filter(function(l){return l.dstI===ci;}).map(function(l){return CATS[l.srcI].name;});
          var icOut = interCatEls.filter(function(l){return l.srcI===ci;}).map(function(l){return CATS[l.dstI].name;});
          var sub = cat.count+' modules';
          if (icIn.length)  sub += ' · from: '+[...new Set(icIn)].join(', ');
          if (icOut.length) sub += ' · to: '+[...new Set(icOut)].join(', ');
          showTT(evt,'<div class="n">'+escH(cat.name)+'</div><div class="sub" style="color:'+color+'">'+cs+'</div><div class="sub">'+sub+'</div>');
        };
      })(cat, ci, cs, color, circle));
      g.addEventListener('mousemove', moveTT);
      g.addEventListener('mouseleave', (function(circle) {
        return function() { hideTT(); circle.style.transform = ''; };
      })(circle));
      return g;
    });

    // Project Status node
    // The governed decision node is derived: it must not read as illuminated while the rollup
    // it displays is not estimable. Before this correction it rendered at 0.92 on every
    // project, empty ones included.
    var prjGlow = prjEstimable ? 'url(#lnf-glow-'+prjStatus+')' : null;
    var prjG = se('g', { class:'lnf-nd', 'data-kind':'project', id:'lnf-prj', 'data-active':prjEstimable ? 'true' : 'false' }, nodeG);
    var pcAttrs = { cx:CX.prj, cy:PRJ_Y, r:'22', fill:prjColor,
                    opacity:prjEstimable ? '0.92' : '0.26', stroke:'none',
                    'data-active':prjEstimable ? 'true' : 'false' };
    if (prjGlow) pcAttrs.filter = prjGlow;
    var prjCircle = se('circle', pcAttrs, prjG);
    if (prjStatus==='Red') prjCircle.classList.add('lnf-red-pulse');
    [['Project',-6],['Status',7]].forEach(function(pair) {
      var t = se('text', { x:CX.prj, y:PRJ_Y+pair[1], fill:'#e8f0ff', 'font-size':'10', 'font-weight':'700',
        'text-anchor':'middle', 'dominant-baseline':'middle', 'font-family':'monospace' }, prjG);
      t.textContent = pair[0];
    });
    var prjStatusText = se('text', { x:CX.prj, y:PRJ_Y+38, fill:prjColor, 'font-size':'12', 'font-weight':'700',
      'text-anchor':'middle', 'font-family':'monospace', class:'lnf-halo' }, prjG);
    // RUN 16, WORKSTREAM A8. The node used to print the internal word "None" at a project with
    // no stored result, which reads as a verdict rather than as an absence of one. The governed
    // vocabulary is unchanged and no new status is invented: this renders the existing
    // no-data state in words a reader can act on.
    prjStatusText.textContent = prjEstimable ? prjStatus : 'Not estimable';
    var prjNodeLabel = governedLabel || 'Project Status';
    prjG.addEventListener('mouseenter', function(evt) {
      var line = prjEstimable
        ? '<div class="sub" style="color:'+prjColor+'">'+escH(prjStatus)+'</div>' +
          '<div class="sub">Fused from the categories that carry a current result</div>'
        : '<div class="sub" style="color:'+prjColor+'">Not estimable</div>' +
          '<div class="sub">No current stored result for this project</div>';
      showTT(evt,'<div class="n">'+escH(prjNodeLabel)+'</div>'+line);
    });
    prjG.addEventListener('mousemove', moveTT);
    prjG.addEventListener('mouseleave', hideTT);

    // (The governance feedback arc and its hover behaviour were removed: see above.)

    // Document nodes (rendered last = on top)
    DOC_KEYS.forEach(function(key, di) {
      var name = docLabel(key);
      var uploaded = isUploaded(key);
      // A doc row confirmed to never be produced for this corpus reads as the
      // platform's existing not-relevant state (blue, square) rather than as a
      // dark "no data" row implying a document is missing. Only applies while the
      // row is actually unlit — a document that WAS somehow uploaded still lights.
      // RUN 26. On an EMPTY project the not-applicable distinction is suppressed entirely:
      // the owner's 2026-08-14 rule forbids a purple square there, and a project with no
      // evidence has no state for "not applicable to it" to be a distinction from. The row
      // reads exactly like every other unlit row, and `data-state` says so rather than
      // leaving it to be inferred from a shade.
      var notApplicable = !uploaded && !projectIsEmpty && !!DOC_NOT_APPLICABLE[key];
      var color = uploaded ? COL.DocOn : (notApplicable ? COL.NotRelevant : COL.DocOff);
      var glow  = uploaded ? 'url(#lnf-glow-DocOn)' : null;
      var x=CX.doc, y=docY(di);
      var g = se('g', { class:'lnf-nd', 'data-kind':'document', 'data-active':uploaded ? 'true' : 'false' }, nodeG);
      // A document row is ACTIVE only when this project has actually uploaded that type since
      // the reset boundary. "Not applicable to this corpus" is an editorial registry fact and
      // was being drawn at 0.75 — brighter than every other unlit row and read by the owner as
      // a lit document on an empty project. It keeps its own colour and square shape so the
      // distinction from a plain "not uploaded" row survives, at the inactive opacity tier.
      var dAttrs = { fill:color, opacity:uploaded?'0.88':(notApplicable?'0.34':'0.30'),
                     stroke:'none', 'data-active':uploaded ? 'true' : 'false',
                     // RUN 24. The three states this column can be in, named in the DOM so a
                     // check reads the shipped decision instead of inferring it from a shade.
                     'data-state':uploaded ? 'uploaded'
                                  : (notApplicable ? 'registered-not-active' : 'not-uploaded') };
      if (glow) dAttrs.filter = glow;
      seShape(notApplicable ? 'square' : 'circle', x, y, 5, dAttrs, g);
      var t = se('text', { x:x-10, y:y,
        fill:uploaded?'var(--muted, #7a9ac0)':(notApplicable?COL.NotRelevant:'var(--faint, #253045)'),
        'font-size':'13', 'font-family':'monospace', 'text-anchor':'end', 'dominant-baseline':'middle', class:'lnf-halo' }, g);
      if (!uploaded) t.setAttribute('opacity','0.55');
      t.textContent = name;

      g.addEventListener('mouseenter', (function(name, di, uploaded, notApplicable, color) {
        return function(evt) {
          var cats = docToCatNames[di].join(', ') || 'no registered module consumes this document type';
          var label = uploaded ? 'Uploaded' : (notApplicable ? 'Not applicable to this corpus' : 'Not uploaded');
          showTT(evt,'<div class="n">'+escH(name)+'</div><div class="sub" style="color:'+color+'">'+label+'</div><div class="sub">Feeds: '+cats+'</div>');
          // trace this document's feeds regardless of upload state
          classAFocus(function(e, d){ return d===di; });
        };
      })(name, di, uploaded, notApplicable, color));
      g.addEventListener('mousemove', moveTT);
      g.addEventListener('mouseleave', (function(di, uploaded) {
        return function() { hideTT(); classAReset(); };
      })(di, uploaded));
    });

    // ── 8. Architecture-versus-activity summary ───────────────────────────────
    // RUN 16, WORKSTREAM A2. The diagram draws the platform's whole registered architecture on
    // every project, which is what makes it useful and also what made it misleading. This strip
    // says in words which of the shapes on screen are capability and which are this project's
    // current activity, so the distinction does not depend on a reader noticing that a line has
    // stopped moving. Every figure is read from the stored result; none is computed here.
    var sum = document.createElement('div');
    sum.className = 'lnf-summary';
    sum.style.cssText = 'padding:8px 12px 2px;font-size:11px;line-height:1.6;' +
      'color:var(--muted, #4a5a7a);font-family:monospace;background:var(--surface, #0b0e17);';
    // RUN 51, SECTION 6.1. The three numbers were always derived from the model this file
    // builds, which is the population IN SERVICE. The word beside them said "registered",
    // which names a different and larger population, so the sentence read as though the
    // diagram drew the whole registry. Only the word moved; no count changed.
    var archSentence = 'This diagram shows the analytical architecture in service: ' +
      DOC_KEYS.length + ' supported document types, ' + MODULES.length +
      ' project modules in service and ' + CATS.length + ' categories in service. ' +
      'It is what the platform can do, not what this project has done.';
    var actSentence;
    // RUN 24. THE ONE PREDICATE. This is the condition that already decided the empty-project
    // sentence; it is now also what decides whether the architecture is drawn unasked. Both
    // readings therefore cannot disagree, which is how "0 uploaded, 0 with a current result"
    // came to sit above a full picture in the first place.
    // (RUN 26: `projectIsEmpty` is computed once, near the statuses, and used both here and by
    // the colour rule. The second definition that stood here has gone: two copies of one
    // predicate is how the caption and the picture came to disagree in the first place.)
    if (projectIsEmpty) {
      // RUN 21. The empty-project sentence is UNCHANGED and is still the one a project with
      // nothing uploaded reads. What changed is that a project whose signals were CLEARED no
      // longer reads it, because for that project it is false: the documents were deliberately
      // not deleted, the server still serves them, and regenerating signals reads them again.
      actSentence = retainedBeforeReset > 0
        ? ('This project has no documents uploaded since its stored signals were cleared and no '
           + 'current results, so nothing on the diagram is active and the '
           + (governedLabel || 'project status') + ' is not estimable. '
           + retainedBeforeReset + ' document' + (retainedBeforeReset === 1 ? '' : 's')
           + ' uploaded before the reset ' + (retainedBeforeReset === 1 ? 'is' : 'are')
           + ' retained and will be read again when signals are regenerated.')
        : ('This project has no uploaded documents and no current results, so nothing '
           + 'on the diagram is active and the ' + (governedLabel || 'project status')
           + ' is not estimable.');
    } else {
      actSentence = 'This project currently has ' + uploadedDocCount + ' uploaded document' +
        (uploadedDocCount === 1 ? '' : 's') + ' across ' + uploadedTypeCount + ' type' +
        (uploadedTypeCount === 1 ? '' : 's') + ', ' + modWithResult +
        ' module' + (modWithResult === 1 ? '' : 's') + ' with a current result, ' +
        modSilent + ' with no current result, ' + modNotRelevant +
        ' not applicable to this project and ' + modDisabled +
        ' disabled, and ' + catEstimable + ' estimable categor' +
        (catEstimable === 1 ? 'y' : 'ies') + '.';
    }
    sum.textContent = archSentence + ' ' + actSentence;
    container.appendChild(sum);

    // ── 9. Legend strip ───────────────────────────────────────────────────────
    var leg = document.createElement('div');
    leg.className = 'lnf-legend';
    leg.style.cssText = 'display:flex;align-items:center;gap:12px;flex-wrap:wrap;padding:8px 12px 6px;' +
      'font-size:10.5px;color:var(--muted, #4a5a7a);font-family:monospace;' +
      'background:var(--surface, #0b0e17);border-top:1px solid var(--line, #1a2440);margin-top:0;';

    function legDot(color, glow) {
      var sh = glow ? '0 0 5px '+color : 'none';
      return '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:'+color+';box-shadow:'+sh+';vertical-align:middle;margin-right:3px"></span>';
    }
    // Square marker (not the five verdicts' round dot) for "Not relevant" -- a sector
    // exclusion, not a severity, so its shape as well as its colour says so.
    function legSquare(color) {
      return '<span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:'+color+';vertical-align:middle;margin-right:3px"></span>';
    }
    [['Green',COL.Green,true],['Yellow',COL.Yellow,true],['Amber',COL.Amber,true],
     ['Red',COL.Red,true],['No data',COL.None,false]].forEach(function(t) {
      var s = document.createElement('span');
      s.innerHTML = legDot(t[1],t[2]) + t[0];
      leg.appendChild(s);
    });
    (function() {
      var s = document.createElement('span');
      s.innerHTML = legSquare(COL.NotRelevant) + 'Not relevant';
      leg.appendChild(s);
    })();
    // POST-RUN-22. The distinction the diagram now draws, said in words as well as in
    // brightness: a dim node is registered architecture, a lit one is current activity.
    (function() {
      var s = document.createElement('span');
      s.innerHTML = '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;' +
        'background:' + COL.None + ';opacity:0.3;vertical-align:middle;margin-right:3px"></span>' +
        'Registered, not active on this project';
      leg.appendChild(s);
    })();
    var sep = document.createElement('span');
    sep.style.cssText = 'border-left:1px solid #1a2440;height:10px;';
    leg.appendChild(sep);
    [['Uploaded',COL.DocOn,true],['Not uploaded',COL.DocOff,false]].forEach(function(t) {
      var s = document.createElement('span');
      s.innerHTML = legDot(t[1],t[2]) + t[0];
      leg.appendChild(s);
    });

    // Flow-class key: line-style samples for the four connection classes
    function legLine(color, dashed, arrow) {
      var border = (dashed ? 'dashed' : 'solid');
      return '<span style="display:inline-block;width:16px;border-top:2px '+border+' '+color+
        ';vertical-align:middle;margin-right:3px"></span>' + (arrow ? '<span style="color:'+color+';margin-right:3px">&#9656;</span>' : '');
    }
    var sep2 = document.createElement('span');
    sep2.style.cssText = 'border-left:1px solid #1a2440;height:10px;';
    leg.appendChild(sep2);
    // RUN 26. THE FLOW-CLASS KEY NO LONGER BORROWS VERDICT COLOURS.
    // It drew its three connection classes in Green, Amber and Red -- colours the same legend
    // strip explains, four entries earlier, as project verdicts. A rollup edge is never green
    // because it is a rollup: it takes the colour of the category's own status. So the legend
    // said one thing and the diagram rendered another, which is the defect the owner's rule 5
    // names. The classes are distinguished by LINE STYLE, which is what actually distinguishes
    // them on the diagram, and drawn in the neutral line colour. "Governance feedback" is gone
    // with the arc it described.
    [['Input (doc→model)', legLine('var(--flow-accent, #35d6e8)', false, false)],
     ['Rollup (model→category→status)', legLine('var(--muted, #5a7898)', false, true)],
     ['Derived (category→category)', legLine('var(--muted, #5a7898)', true, true)],
     ['Configured relationship, not carrying current data', legLine('var(--faint, #4a5a7a)', true, false)]].forEach(function(t) {
      var s = document.createElement('span');
      s.innerHTML = t[1] + t[0];
      leg.appendChild(s);
    });
    container.appendChild(leg);
    return { empty: projectIsEmpty, retainedBeforeReset: retainedBeforeReset,
             governedLabel: governedLabel };
  }

  // ─── RUN 24. AN EMPTY PROJECT MUST LOOK EMPTY ────────────────────────────────
  //
  // THE DEFECT, reproduced in a real browser on a brand-new project before a line was changed
  // (code_audit/run24_empty_project_diagram_baseline.csv, state A-empty-as-shown): the diagram
  // drew 144 node shapes and 323 link paths, every one of the supported document types, every
  // registered module row, every registered category and every configured link, and said
  // "0 UPLOADED ON THIS PROJECT / 0 WITH A CURRENT RESULT" in a caption above it. Nothing was
  // lit: the post-Run-22 correction had already made that true, and this run re-measured it as
  // true (0 nodes at the active tier, 0 animated edges, 0 `.lnf-active`). The remaining defect
  // is not false light. It is MASS. A reader's dominant impression of ~96 module rows, ~11
  // category nodes and 229 drawn links is a working diagram, whatever the caption says.
  //
  // THE THREE OPTIONS THE OWNER ASKED TO BE WEIGHED, and why this is the third.
  //   * Do not draw the links at all until something is uploaded. Rejected: measured here, the
  //     links are 323 of 467 drawn elements, so removing them leaves ~144 shapes including
  //     every module row. It reduces the mass without changing the impression, and it also
  //     destroys the architecture view for the case where a reader legitimately wants it.
  //   * Draw everything at a weight that plainly reads as inactive. Already shipped, and
  //     already verified here: the inactive tiers are 0.20 (no data), 0.28 to 0.34 and 0.14 to
  //     0.16 on links. The owner is looking at that build and still reads it as dense, which is
  //     the evidence that weight alone does not carry the distinction.
  //   * Replace the diagram with a short statement of what it will show once documents arrive,
  //     with the full architecture behind an explicit control. Chosen. It is the only one of
  //     the three where the absence, and not the architecture, is what the page leads with,
  //     and it is the only one that separates "what the platform can do" from "what this
  //     project has done" by an act of the reader rather than by a shade of grey.
  //
  // THE DIAGRAM IS NOT REMOVED. It is built exactly as before, by exactly the same code, and
  // is one click away on an empty project. On a project with any current evidence nothing here
  // applies and the diagram is shown directly, as it always was.
  var revealSeq = 0;

  function render(project, container) {
    if (!container) return;
    container.innerHTML = '';
    var host = document.createElement('div');
    host.className = 'lnf-diagram';
    host.id = 'lnf-diagram-' + (++revealSeq);
    container.appendChild(host);

    var info = drawDiagram(project, host);
    if (!info || !info.empty) return;

    // The project has nothing current. Lead with that.
    host.style.display = 'none';
    host.setAttribute('aria-hidden', 'true');

    var panel = document.createElement('div');
    panel.className = 'lnf-empty';
    panel.style.cssText = 'padding:26px 22px 22px;font-family:monospace;' +
      'background:var(--surface, #0b0e17);color:var(--muted, #4a5a7a);';

    var h = document.createElement('div');
    h.style.cssText = 'font-size:13px;font-weight:700;letter-spacing:0.08em;' +
      'color:var(--muted, #5a7898);margin-bottom:10px;';
    h.textContent = 'NOTHING TO SHOW ON THIS PROJECT YET';
    panel.appendChild(h);

    var p1 = document.createElement('p');
    p1.style.cssText = 'font-size:12px;line-height:1.7;margin:0 0 8px;max-width:74ch;';
    p1.textContent = info.retainedBeforeReset > 0
      ? ('No documents have been uploaded since this project’s stored signals were cleared '
         + 'and there are no current results, so the ' + (info.governedLabel || 'project status')
         + ' is not estimable. ' + info.retainedBeforeReset + ' document'
         + (info.retainedBeforeReset === 1 ? '' : 's') + ' uploaded before the reset '
         // WORDED DELIBERATELY DIFFERENTLY from the summary strip's retained-document
         // sentence. Repeating that sentence verbatim here would give the Run-21 reset
         // disclosure guard a second copy to find, so reverting the real one in the summary
         // strip would no longer turn that guard red. Measured: it did exactly that.
         + (info.retainedBeforeReset === 1 ? 'is' : 'are')
         + ' still held and will be read the next time signals are generated.')
      : ('This project has no uploaded documents and no current results, so the '
         + (info.governedLabel || 'project status') + ' is not estimable.');
    panel.appendChild(p1);

    var p2 = document.createElement('p');
    p2.style.cssText = 'font-size:12px;line-height:1.7;margin:0 0 16px;max-width:74ch;';
    p2.textContent = 'Once documents are uploaded and signals are generated, this view will '
      + 'show which document types arrived, which analytical groups they reached, and which '
      + 'of those produced a current status.';
    panel.appendChild(p2);

    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'lnf-reveal';
    btn.setAttribute('aria-expanded', 'false');
    btn.setAttribute('aria-controls', host.id);
    btn.style.cssText = 'font-family:monospace;font-size:11.5px;letter-spacing:0.06em;' +
      'padding:8px 14px;border:1px solid var(--line, #1a2440);border-radius:4px;' +
      'background:transparent;color:var(--muted, #5a7898);cursor:pointer;';
    btn.textContent = 'Show the architecture in service';
    panel.appendChild(btn);

    var note = document.createElement('div');
    note.style.cssText = 'font-size:11px;line-height:1.6;margin-top:10px;max-width:74ch;' +
      'color:var(--faint, #4a5a7a);';
    note.textContent = 'The architecture view is what the platform can do, not what this '
      + 'project has done. Nothing on it will be active until this project has evidence.';
    panel.appendChild(note);

    btn.addEventListener('click', function () {
      var open = btn.getAttribute('aria-expanded') === 'true';
      if (open) {
        host.style.display = 'none';
        host.setAttribute('aria-hidden', 'true');
        btn.setAttribute('aria-expanded', 'false');
        btn.textContent = 'Show the architecture in service';
      } else {
        host.style.display = '';
        host.removeAttribute('aria-hidden');
        btn.setAttribute('aria-expanded', 'true');
        btn.textContent = 'Hide the architecture in service';
      }
    });

    container.insertBefore(panel, host);
  }

  window.LinNeuralFlow = { render: render };
})();
