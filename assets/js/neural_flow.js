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
    { id:1,  name:'Quantitative EVM',       group:'A', groupName:'Project Health',                  count:12 },
    { id:2,  name:'Schedule Simulation',    group:'A', groupName:'Project Health',                  count:11 },
    { id:3,  name:'Cost Simulation',        group:'A', groupName:'Project Health',                  count:10 },
    { id:4,  name:'Document & Risk',        group:'A', groupName:'Project Health',                  count:10 },
    { id:5,  name:'System Dynamics',        group:'A', groupName:'Project Health',                  count:8  },
    { id:6,  name:'Signal Synthesis',       group:'B', groupName:'Recommendation and Governance',   count:4  },
    { id:7,  name:'Evidence Combination',   group:'B', groupName:'Recommendation and Governance',   count:20 },
    { id:8,  name:'Governance & Compliance',group:'B', groupName:'Recommendation and Governance',   count:9  },
    { id:9,  name:'Data Integrity',         group:'C', groupName:'Data and Evidence Health',        count:6  },
    { id:10, name:'Decision Optimization',  group:'B', groupName:'Recommendation and Governance',   count:8  },
  ];

  // ─── Fallback module definitions: [catIdx, displayName, method_class] ───────
  var RAW_MODS = [
    // Cat 1 — Quantitative EVM (12)
    [0,'Monte Carlo EAC','Monte_Carlo_EAC'],  [0,'CUSUM Anomaly','CUSUM_Anomaly'],
    [0,'Doc Risk Score','Doc_Risk_Score'],    [0,'Bayesian EAC','Bayesian_EAC'],
    [0,'Kalman Filter','Kalman_Filter'],      [0,'ARIMA Forecast','ARIMA_Forecast'],
    [0,'Earned Schedule','Earned_Schedule'],  [0,'TCPI Monitor','TCPI_Monitor'],
    [0,'VAC Trend','VAC_Trend'],              [0,'Budget Exec Rate','Budget_Exec_Rate'],
    [0,'Regression to Mean','Regression_to_Mean'], [0,'ICE Ratio','ICE_Ratio'],
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
    [9,'Regret Minimiz.','Regret_Minimization'],[9,'Info Value','Info_Value'],
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
        return { id: ci + 1, name: c.name, group: c.group, groupName: c.groupName,
                 count: (c.modules || []).length };
      });
      var mods = [];
      var idxs = PLC.map(function() { return []; });
      var catIds = PLC.map(function(c) { return c.id; });
      PLC.forEach(function(c, ci) {
        (c.modules || []).forEach(function(m) {
          idxs[ci].push(mods.length);
          mods.push({ mc: m.method_class, name: m.name, num: m.num, catI: ci });
        });
      });
      return { CATS: cats, MODULES: mods, catModIdxs: idxs, catIds: catIds };
    }
    var fbIdxs = FB_CATS.map(function() { return []; });
    var fbMods = RAW_MODS.map(function(row, i) {
      var ci = row[0], modI = fbIdxs[ci].length;
      fbIdxs[ci].push(i);
      return { catI: ci, name: row[1], mc: row[2], num: (ci + 1) + '.' + (modI + 1) };
    });
    return { CATS: FB_CATS, MODULES: fbMods, catModIdxs: fbIdxs, catIds: null };
  }

  // ─── Doc → category indices (0-based, gapless 1-10; Portfolio Health is
  // portfolio-scale and not fed by individual document uploads) ────────────────
  var DOC_TO_CATS = [
    [0,2],      // Contract Value          → Cat1, Cat3
    [0,1],      // Schedule of Values      → Cat1, Cat2
    [0,2,7],    // Pay Application         → Cat1, Cat3, Cat8
    [0,1],      // Time-Phased Schedule    → Cat1, Cat2
    [1,4],      // Schedule Update         → Cat2, Cat5
    [0,1,2],    // Monthly Report          → Cat1, Cat2, Cat3
    [2,7],      // Change Order            → Cat3, Cat8
    [3],        // Submittal Register      → Cat4
    [3,7],      // OAC Minutes             → Cat4, Cat8
    [3,1],      // Field Report            → Cat4, Cat2
    [3],        // Inspection Report       → Cat4
    [3,7],      // NCR Log                 → Cat4, Cat8
    [3,7],      // Subcontractor Report    → Cat4, Cat8
    [3,2],      // Procurement Log         → Cat4, Cat3
    [1,4],      // Lookahead Schedule      → Cat2, Cat5
    [2,4],      // Resource Report         → Cat3, Cat5
    [2,0],      // Cost Report             → Cat3, Cat1
    [2],        // Past Performance Report → Cat3
    [7],        // Safety Report           → Cat8
    [7,3],      // Quality Audit Report    → Cat8, Cat4
    [7],        // Environmental Report    → Cat8
    [2],        // Historical Data         → Cat3
    [7,3],      // Commissioning Report    → Cat8, Cat4
    [3],        // Correspondence / Notice → Cat4
    [4,3],      // Risk Register           → Cat5, Cat4
    [3],        // RFI Log (register)      → Cat4  (v10.27)
    [3],        // RFA / Approval Log      → Cat4  (v10.27)
  ];

  // ─── Inter-category feeds (x-hubs between cat col and prj col) ───────────────
  var INTER_CAT = [
    { srcs:[0,1,2,3,4],             dst:5, xHub:860 },
    { srcs:[0,1,2,3,4,5],           dst:6, xHub:875 },
    { srcs:[0,1,2,3,4,5,6,7],       dst:8, xHub:905 },
    { srcs:[0,1,2,3,4,5,6,7],       dst:9, xHub:920 },
  ];

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
  function render(project, container) {
    if (!container) return;
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
    var mfb = se('marker', { id:'lnf-arr-fb', markerWidth:'5', markerHeight:'5', refX:'4', refY:'2.5', orient:'auto' }, defs);
    se('polygon', { points:'4,0 4,5 0,2.5', fill:COL.Red, opacity:'0.85' }, mfb);

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
      [CX.doc, DOC_KEYS.length + ' SUPPORTED DOCUMENT TYPES',
               uploadedDocCount + ' UPLOADED ON THIS PROJECT'],
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

    // Class B (rollup): cat → project — streaming dashes, arrowhead at the status node edge
    var catPrjEls = catStatuses.map(function(cs, ci) {
      var x1=CX.cat+9, y1=catCY[ci], x2=CX.prj-26, y2=PRJ_Y, mx=(x1+x2)/2;
      var p = se('path', { d:'M'+x1+','+y1+' C'+mx+','+y1+' '+mx+','+y2+' '+x2+','+y2,
        fill:'none', stroke:colFor(cs), 'stroke-width':'1.5', opacity:'0.35', 'stroke-linecap':'round',
        'marker-end':'url(#lnf-arr-'+cs+')' }, lineG);
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
        fill:'none', stroke:modInfos[mi].color, 'stroke-width':'0.8', opacity:MODCAT_OP, 'stroke-linecap':'round' }, lineG);
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
      DOC_TO_CATS[di].forEach(function(ci) {
        catModIdxs[ci].slice(0, 2).forEach(function(mi) {
          var x1=CX.doc+5, y1=docY(di), x2=CX.mod-4, y2=modY[mi], mx=(x1+x2)/2;
          var d = 'M'+x1+','+y1+' C'+mx+','+y1+' '+mx+','+y2+' '+x2+','+y2;
          var base = se('path', { d:d, class:'lnf-a-line', fill:'none',
            'stroke-width':w, opacity:baseOp, 'stroke-linecap':'round' }, lineG);
          var dash = se('path', { d:d, class:'lnf-a-line', fill:'none',
            'stroke-width':w, opacity:dashOp, 'stroke-linecap':'round' }, lineG);
          // An evidence path is live only when this project has actually uploaded that
          // document type. The unlit rows were already faint; now they are also still.
          flowAnim(dash, 'lnf-flow-a', up);
          docLineMap[di].push({ base:base, dash:dash, modI:mi });
        });
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
    var interCatEls = [];
    INTER_CAT.forEach(function(feed) {
      feed.srcs.forEach(function(srcI) {
        var cs = catStatuses[srcI];
        var x1=CX.cat+9, y1=catCY[srcI], x2=CX.cat+9, y2=catCY[feed.dst], xh=feed.xHub;
        var line = se('path', {
          d:'M'+x1+','+y1+' C'+xh+','+y1+' '+xh+','+y2+' '+x2+','+y2,
          fill:'none', stroke:colFor(cs), 'stroke-width':'1', opacity:'0.45',
          'stroke-dasharray':'6 4', 'marker-end':'url(#lnf-arr-'+cs+')'
        }, interG);
        if (!isEstimable(cs)) line.setAttribute('opacity', '0.16');
        flowAnim(line, 'lnf-flow-c', isEstimable(cs));
        interCatEls.push({ el:line, srcI:srcI, dstI:feed.dst });
      });
    });

    // Governance feedback arc: Project Status → Cat 8 (idx 7)
    var fbSX=CX.prj+26, fbSY=PRJ_Y, fbDX=CX.cat+9, fbDY=catCY[7];
    var fbEl = se('path', {
      d:'M'+fbSX+','+fbSY+' C'+(fbSX+65)+','+fbSY+' '+(fbSX+65)+','+fbDY+' '+fbDX+','+fbDY,
      fill:'none', stroke:COL.Red, 'stroke-width':'1.5', opacity:'0.30',
      'stroke-dasharray':'5 4', 'marker-end':'url(#lnf-arr-fb)'
    }, interG);
    // The governance loop is a configured relationship. It carries something only once the
    // governed rollup has a current estimable value to feed back.
    if (!prjEstimable) fbEl.setAttribute('opacity', '0.14');
    flowAnim(fbEl, 'lnf-flow-fb', prjEstimable);
    var fbLabelEl = se('text', {
      x:fbSX+70, y:(fbSY+fbDY)/2,
      fill:COL.Red, 'font-size':'10', 'font-family':'monospace',
      opacity:'0.70', 'writing-mode':'tb', 'text-anchor':'middle', class:'lnf-halo'
    }, interG);
    fbLabelEl.textContent = 'governance feedback';

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
      var glow = info.status !== 'None' ? 'url(#lnf-glow-'+info.status+')' : null;
      var g = se('g', { class:'lnf-nd' }, nodeG);

      var circleAttrs = {
        fill:info.color, opacity:info.status==='None'?'0.20':'0.85', stroke:'none' };
      if (glow) circleAttrs.filter = glow;
      var dotShape = window.linStatusShape ? linStatusShape(info.status) : 'circle';
      var circle = seShape(dotShape, CX.mod, modY[mi], 4, circleAttrs, g);
      if (info.status === 'Red') circle.classList.add('lnf-red-pulse');

      var lbl = se('text', {
        x:CX.mod+8, y:modY[mi],
        fill:info.status==='None'?'var(--faint, #1e2c44)':'var(--muted, #5a7898)',
        'font-size':'11.5', 'font-family':'monospace',
        'dominant-baseline':'middle', 'pointer-events':'none', class:'lnf-halo'
      }, g);
      if (info.status==='None') lbl.setAttribute('opacity','0.55');
      lbl.textContent = trunc(m.name, 26);

      circle.style.transformOrigin = CX.mod + 'px ' + modY[mi] + 'px';
      g.addEventListener('mouseenter', (function(m, mi, info, circle) {
        return function(evt) {
          circle.style.transform = 'scale(1.5)';
          var metStr = info.metric ? '<div class="sub">metric: '+escH(info.metric)+'</div>' : '';
          var statusLabel = info.na ? escH(sectorNAText) : info.status;
          showTT(evt,'<div class="m">'+escH(m.num)+'</div><div class="n">'+escH(m.name)+'</div><div class="sub" style="color:'+info.color+'">'+statusLabel+'</div>'+metStr+'<div class="sub">'+escH(CATS[m.catI].name)+'</div>');
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
      var glow = cs !== 'None' ? 'url(#lnf-glow-'+cs+')' : null;
      var x=CX.cat, y=catCY[ci];
      var g = se('g', { class:'lnf-nd' }, nodeG);
      var cAttrs = { fill:color, opacity:cs==='None'?'0.28':'0.88', stroke:'none' };
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
    var prjGlow = prjStatus !== 'None' ? 'url(#lnf-glow-'+prjStatus+')' : null;
    var prjG = se('g', { class:'lnf-nd', id:'lnf-prj' }, nodeG);
    var pcAttrs = { cx:CX.prj, cy:PRJ_Y, r:'22', fill:prjColor, opacity:'0.92', stroke:'none' };
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

    // Feedback arc events
    fbEl.style.cursor = 'default';
    fbEl.addEventListener('mouseenter', function(evt) {
      fbEl.setAttribute('opacity','0.80'); fbLabelEl.setAttribute('opacity','0.90');
      showTT(evt,'<div class="n">Governance Feedback</div>' +
        '<div class="sub">Governance decisions feed back into compliance monitoring</div>' +
        '<div class="sub">' + (prjEstimable ? 'Carrying a current result'
          : 'Configured relationship, nothing flowing now') + '</div>');
    });
    fbEl.addEventListener('mousemove', moveTT);
    fbEl.addEventListener('mouseleave', function() { hideTT(); fbEl.setAttribute('opacity', prjEstimable ? '0.30' : '0.14'); fbLabelEl.setAttribute('opacity','0.70'); });

    // Document nodes (rendered last = on top)
    DOC_KEYS.forEach(function(key, di) {
      var name = docLabel(key);
      var uploaded = isUploaded(key);
      // A doc row confirmed to never be produced for this corpus reads as the
      // platform's existing not-relevant state (blue, square) rather than as a
      // dark "no data" row implying a document is missing. Only applies while the
      // row is actually unlit — a document that WAS somehow uploaded still lights.
      var notApplicable = !uploaded && !!DOC_NOT_APPLICABLE[key];
      var color = uploaded ? COL.DocOn : (notApplicable ? COL.NotRelevant : COL.DocOff);
      var glow  = uploaded ? 'url(#lnf-glow-DocOn)' : null;
      var x=CX.doc, y=docY(di);
      var g = se('g', { class:'lnf-nd' }, nodeG);
      var dAttrs = { fill:color, opacity:uploaded?'0.88':(notApplicable?'0.75':'0.30'), stroke:'none' };
      if (glow) dAttrs.filter = glow;
      seShape(notApplicable ? 'square' : 'circle', x, y, 5, dAttrs, g);
      var t = se('text', { x:x-10, y:y,
        fill:uploaded?'var(--muted, #7a9ac0)':(notApplicable?COL.NotRelevant:'var(--faint, #253045)'),
        'font-size':'13', 'font-family':'monospace', 'text-anchor':'end', 'dominant-baseline':'middle', class:'lnf-halo' }, g);
      if (!uploaded && !notApplicable) t.setAttribute('opacity','0.55');
      t.textContent = name;

      g.addEventListener('mouseenter', (function(name, di, uploaded, notApplicable, color) {
        return function(evt) {
          var cats = DOC_TO_CATS[di].map(function(ci){return (CATS[ci] && CATS[ci].name) || '';}).join(', ');
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
    var archSentence = 'This diagram shows the platform\u2019s registered architecture: ' +
      DOC_KEYS.length + ' supported document types, ' + MODULES.length +
      ' registered project modules and ' + CATS.length + ' registered categories. ' +
      'It is what the platform can do, not what this project has done.';
    var actSentence;
    if (uploadedDocCount === 0 && modWithResult === 0 && catEstimable === 0) {
      actSentence = 'This project has no uploaded documents and no current results, so nothing ' +
        'on the diagram is active and the ' + (governedLabel || 'project status') +
        ' is not estimable.';
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
    [['Input (doc→model)', legLine('var(--flow-accent, #35d6e8)', false, false)],
     ['Rollup (model→category→status)', legLine(COL.Green, false, true)],
     ['Derived (category→category)', legLine(COL.Amber, true, true)],
     ['Governance feedback', legLine(COL.Red, true, true)],
     ['Configured relationship, not carrying current data', legLine('var(--faint, #4a5a7a)', true, false)]].forEach(function(t) {
      var s = document.createElement('span');
      s.innerHTML = t[1] + t[0];
      leg.appendChild(s);
    });
    container.appendChild(leg);
  }

  window.LinNeuralFlow = { render: render };
})();
