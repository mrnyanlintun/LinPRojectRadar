/* global LinNeuralFlow — dynamic neural signal flow for project detail page */
(function () {
  'use strict';

  // ─── Document types (27, ordered to match DOC_TO_CATS) ──────────────────────
  var DOCS = [
    'Contract Value','Schedule of Values','Pay Application','Time-Phased Schedule',
    'Schedule Update','Monthly Report','Change Order','RFI','Submittal',
    'OAC Minutes','Field Report','Inspection Report','NCR Log',
    'Subcontractor Report','Procurement Log','Lookahead Schedule','Resource Report',
    'Cost Report','Past Performance Report','Safety Report','Quality Audit Report',
    'Environmental Report','Historical Data','Commissioning Report',
    'Correspondence / Notice','Risk Register','Schedule of Values (Baseline)',
  ];

  // ─── Category definitions (12) ───────────────────────────────────────────────
  var CATS = [
    { id:1,  name:'Quantitative EVM',       short:'EVM',       count:12 },
    { id:2,  name:'Schedule Simulation',    short:'Schedule',  count:11 },
    { id:3,  name:'Cost Simulation',        short:'Cost',      count:10 },
    { id:4,  name:'Document & Risk',        short:'Doc&Risk',  count:10 },
    { id:5,  name:'System Dynamics',        short:'Sys.Dyn.',  count:8  },
    { id:6,  name:'Signal Synthesis',       short:'Synthesis', count:4  },
    { id:7,  name:'Evidence Combination',   short:'Evidence',  count:20 },
    { id:8,  name:'ML & AI',                short:'ML & AI',   count:5  },
    { id:9,  name:'Governance & Compliance',short:'Gov.',      count:9  },
    { id:10, name:'Data Integrity',         short:'Integrity', count:6  },
    { id:11, name:'Decision Optimization',  short:'Decision',  count:8  },
    { id:12, name:'Systems Engineering',    short:'Sys.Eng.',  count:5  },
  ];

  // ─── Module definitions: [catIdx, displayName, method_class] (108 total) ────
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
    // Cat 8 — ML & AI (5)
    [7,'Isolation Forest','Isolation_Forest'],[7,'Portfolio Outlier','Portfolio_Outlier'],
    [7,'Trajectory Class.','Trajectory_Classifier'],[7,'Cross-Project Pat.','Cross_Project_Pattern'],
    [7,'Anomaly Score','Anomaly_Score'],
    // Cat 9 — Governance & Compliance (9)
    [8,'ABM Governance','ABM_Governance'],    [8,'FAR Monitor','FAR_Monitor'],
    [8,'OMB A-11','OMB_A11'],                 [8,'EVM Threshold','EVM_Threshold'],
    [8,'CO Frequency Gov','CO_Frequency_Gov'],[8,'Quality Gate','Quality_Gate'],
    [8,'Safety Gate','Safety_Gate'],          [8,'Environmental Gate','Environmental_Gate'],
    [8,'Contractor Score','Contractor_Score'],
    // Cat 10 — Data Integrity (6)
    [9,'Missing Field Det.','Missing_Field_Detector'],[9,'Outlier Screener','Outlier_Screener'],
    [9,'Temporal Consist.','Temporal_Consistency'],[9,'Cross-Doc Conflict','Cross_Doc_Conflict'],
    [9,'Completeness Score','Completeness_Score'],[9,'Source Audit Trail','Source_Audit_Trail'],
    // Cat 11 — Decision Optimization (8)
    [10,'Pareto Front','Pareto_Front'],        [10,'MAUT','MAUT'],
    [10,'AHP Weighting','AHP_Weighting'],      [10,'TOPSIS Rank','TOPSIS_Rank'],
    [10,'Regret Minimiz.','Regret_Minimization'],[10,'Info Value','Info_Value'],
    [10,'Sensitivity Rank','Sensitivity_Rank'],[10,'Robust Decision','Robust_Decision'],
    // Cat 12 — Systems Engineering (5)
    [11,'Requirements Trace','Requirements_Trace'],[11,'Interface Risk','Interface_Risk'],
    [11,'V-Model Gate','V_Model_Gate'],        [11,'SysML Signal','SysML_Signal'],
    [11,'Digital Twin Sync','Digital_Twin_Sync'],
  ];

  // Build indexed module list and per-category index maps
  var catModIdxs = CATS.map(function() { return []; });
  var MODULES = RAW_MODS.map(function(row, i) {
    var ci = row[0], name = row[1], mc = row[2];
    var modI = catModIdxs[ci].length;
    catModIdxs[ci].push(i);
    return { i:i, catI:ci, modI:modI, name:name, mc:mc, num:(ci+1)+'.'+(modI+1) };
  });

  // ─── Doc → category indices (0-based), corrected per spec ───────────────────
  var DOC_TO_CATS = [
    [0,2],      // Contract Value          → Cat1, Cat3
    [0,1],      // Schedule of Values      → Cat1, Cat2
    [0,2,8],    // Pay Application         → Cat1, Cat3, Cat9
    [0,1],      // Time-Phased Schedule    → Cat1, Cat2
    [1,4],      // Schedule Update         → Cat2, Cat5
    [0,1,2],    // Monthly Report          → Cat1, Cat2, Cat3
    [2,8],      // Change Order            → Cat3, Cat9
    [3],        // RFI                     → Cat4
    [3],        // Submittal               → Cat4
    [3,8],      // OAC Minutes             → Cat4, Cat9
    [3,1],      // Field Report            → Cat4, Cat2
    [3],        // Inspection Report       → Cat4
    [3,8],      // NCR Log                 → Cat4, Cat9
    [3,8],      // Subcontractor Report    → Cat4, Cat9
    [3,2],      // Procurement Log         → Cat4, Cat3
    [1,4],      // Lookahead Schedule      → Cat2, Cat5
    [2,4],      // Resource Report         → Cat3, Cat5
    [2,0],      // Cost Report             → Cat3, Cat1
    [2],        // Past Performance Report → Cat3
    [8],        // Safety Report           → Cat9
    [8,3],      // Quality Audit Report    → Cat9, Cat4
    [8],        // Environmental Report    → Cat9
    [2],        // Historical Data         → Cat3
    [8,3],      // Commissioning Report    → Cat9, Cat4
    [3],        // Correspondence / Notice → Cat4
    [4,3],      // Risk Register           → Cat5, Cat4
    [0,1],      // Schedule of Values (Baseline) → Cat1, Cat2
  ];

  // ─── Inter-category feeds (x-hubs between cat col and prj col) ───────────────
  var INTER_CAT = [
    { srcs:[0,1,2,3,4],             dst:5,  xHub:860 },
    { srcs:[0,1,2,3,4,5],           dst:6,  xHub:875 },
    { srcs:[0,1,2],                 dst:7,  xHub:890 },
    { srcs:[0,1,2,3,4,5,6,7,8],    dst:9,  xHub:905 },
    { srcs:[0,1,2,3,4,5,6,7,8],    dst:10, xHub:920 },
    { srcs:[0,1,2,3],               dst:11, xHub:935 },
  ];

  // ─── Colors ──────────────────────────────────────────────────────────────────
  var COL = {
    Green:'#3fcaa6', Yellow:'#f0c040', Amber:'#e2b13c',
    Red:'#e0556b',   None:'#2a3346',  Complete:'#4ea0ff',
    DocOn:'#a0bcd8', DocOff:'#1e2a3c',
  };
  // Complete ranks alongside Green (blue is a display colour, not a severity)
  var STATUS_RANK = { Red:0, Amber:1, Yellow:2, Green:3, Complete:3, None:4 };

  function statusFromSig(r) {
    if (!r) return 'None';
    var sc = String(r.status_color || r.status || '').toLowerCase();
    if (sc === 'green'  || sc === '#3fcaa6') return 'Green';
    if (sc === 'yellow' || sc === '#f0c040') return 'Yellow';
    if (sc === 'amber'  || sc === '#e2b13c') return 'Amber';
    if (sc === 'red'    || sc === '#e0556b') return 'Red';
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

  // ─── Inject shared styles once ───────────────────────────────────────────────
  function ensureStyles() {
    if (document.getElementById('lnf-styles')) return;
    var s = document.createElement('style');
    s.id = 'lnf-styles';
    s.textContent = [
      '@keyframes lnf-red-pulse{0%,100%{opacity:1}50%{opacity:0.5}}',
      '.lnf-red-pulse{animation:lnf-red-pulse 2s ease-in-out infinite}',
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

    // ── 1. Determine uploaded doc types from project events ───────────────────
    var uploadedNorm = {};
    (project.events || []).forEach(function(e) {
      if (e.event === 'signals_extracted' && e.docType) uploadedNorm[normKey(e.docType)] = true;
    });
    // Union with signalInputs.sources (events may be partially cleared by resets)
    if (project.signalInputs && project.signalInputs.sources) {
      Object.values(project.signalInputs.sources).forEach(function(src) {
        if (src && src.docType) uploadedNorm[normKey(src.docType)] = true;
      });
    }
    function isUploaded(name) { return !!uploadedNorm[normKey(name)]; }

    // ── 2. Module status from simulationSignals.signal_array ─────────────────
    var simArr = (project.simulationSignals && project.simulationSignals.signal_array) || [];
    var byClass = {};
    simArr.forEach(function(r) { if (r && r.method_class) byClass[r.method_class] = r; });
    function modInfo(mc) {
      var r = byClass[mc];
      var s = statusFromSig(r);
      return { status:s, color:colFor(s), metric: r && r.evidence_metric ? String(r.evidence_metric) : null };
    }

    // ── 3. Pre-compute all statuses ───────────────────────────────────────────
    var modInfos = MODULES.map(function(m) { return modInfo(m.mc); });
    // Category statuses — use the app's DST fusion (categories.js); LIN_CATEGORIES
    // is ordered cat1..cat12, matching the CATS index. Worst-of is only a fallback.
    var catStatuses = CATS.map(function(cat, ci) {
      try {
        if (window.getCategoryStatus && window.LIN_CATEGORIES && window.LIN_CATEGORIES[ci]) {
          var s = window.getCategoryStatus(window.LIN_CATEGORIES[ci].id, project);
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

    // ── 4. Layout geometry ────────────────────────────────────────────────────
    var W = 1280, PAD_TOP = 45;
    var MOD_SPACE = 8, MOD_GAP = 12;
    var totalModH = MODULES.length * MOD_SPACE + (CATS.length - 1) * MOD_GAP;
    var H = Math.max(totalModH + PAD_TOP * 2, 920);

    var CX = { doc:115, mod:420, cat:730, prj:1090 };

    var DOC_SPACING = (H - PAD_TOP * 2) / (DOCS.length - 1);
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

    // Column headers
    [['DOCUMENTS',CX.doc],['108 MODULES',CX.mod],['12 CATEGORIES',CX.cat],['PROJECT STATUS',CX.prj]].forEach(function(pair) {
      var t = se('text', { x:pair[0], y:18, 'text-anchor':'middle', fill:'#253045',
        'font-size':'8', 'font-weight':'700', 'letter-spacing':'0.10em', 'font-family':'monospace' }, svg);
      t.textContent = pair[1];
    });

    // ── 6. Connection layers ──────────────────────────────────────────────────
    var lineG  = se('g', { id:'lnf-lines'  }, svg);
    var interG = se('g', { id:'lnf-intercat' }, svg);

    // cat → project lines
    var catPrjEls = catStatuses.map(function(cs, ci) {
      var x1=CX.cat+9, y1=catCY[ci], x2=CX.prj-26, y2=PRJ_Y, mx=(x1+x2)/2;
      return se('path', { d:'M'+x1+','+y1+' C'+mx+','+y1+' '+mx+','+y2+' '+x2+','+y2,
        fill:'none', stroke:colFor(cs), 'stroke-width':'1.5', opacity:'0.22', 'stroke-linecap':'round' }, lineG);
    });

    // mod → cat lines
    var modCatEls = MODULES.map(function(m, mi) {
      var ci=m.catI, x1=CX.mod+4, y1=modY[mi], x2=CX.cat-9, y2=catCY[ci], mx=(x1+x2)/2;
      return se('path', { d:'M'+x1+','+y1+' C'+mx+','+y1+' '+mx+','+y2+' '+x2+','+y2,
        fill:'none', stroke:modInfos[mi].color, 'stroke-width':'0.8', opacity:'0.15', 'stroke-linecap':'round' }, lineG);
    });

    // doc → module lines (first 2 modules of each target category)
    // Store per-doc arrays for hover interaction
    var docLineMap = DOCS.map(function() { return []; }); // docIdx → [{el, modI}]
    DOCS.forEach(function(name, di) {
      var uploaded = isUploaded(name);
      var stroke = uploaded ? COL.DocOn : COL.DocOff;
      var opacity = uploaded ? '0.20' : '0.05';
      DOC_TO_CATS[di].forEach(function(ci) {
        catModIdxs[ci].slice(0, 2).forEach(function(mi) {
          var x1=CX.doc+5, y1=docY(di), x2=CX.mod-4, y2=modY[mi], mx=(x1+x2)/2;
          var line = se('path', { d:'M'+x1+','+y1+' C'+mx+','+y1+' '+mx+','+y2+' '+x2+','+y2,
            fill:'none', stroke:stroke, 'stroke-width':'0.7', opacity:opacity, 'stroke-linecap':'round' }, lineG);
          docLineMap[di].push({ el:line, modI:mi });
        });
      });
    });

    // inter-category dashed lines
    var interCatEls = [];
    INTER_CAT.forEach(function(feed) {
      feed.srcs.forEach(function(srcI) {
        var cs = catStatuses[srcI];
        var x1=CX.cat+9, y1=catCY[srcI], x2=CX.cat+9, y2=catCY[feed.dst], xh=feed.xHub;
        var line = se('path', {
          d:'M'+x1+','+y1+' C'+xh+','+y1+' '+xh+','+y2+' '+x2+','+y2,
          fill:'none', stroke:colFor(cs), 'stroke-width':'1', opacity:'0.20',
          'stroke-dasharray':'4 3', 'marker-end':'url(#lnf-arr-'+cs+')'
        }, interG);
        interCatEls.push({ el:line, srcI:srcI, dstI:feed.dst });
      });
    });

    // Governance feedback arc: Project Status → Cat 9 (idx 8)
    var fbSX=CX.prj+26, fbSY=PRJ_Y, fbDX=CX.cat+9, fbDY=catCY[8];
    var fbEl = se('path', {
      d:'M'+fbSX+','+fbSY+' C'+(fbSX+65)+','+fbSY+' '+(fbSX+65)+','+fbDY+' '+fbDX+','+fbDY,
      fill:'none', stroke:COL.Red, 'stroke-width':'1.5', opacity:'0.30',
      'stroke-dasharray':'5 4', 'marker-end':'url(#lnf-arr-fb)'
    }, interG);
    var fbLabelEl = se('text', {
      x:fbSX+70, y:(fbSY+fbDY)/2,
      fill:COL.Red, 'font-size':'7', 'font-family':'monospace',
      opacity:'0.50', 'writing-mode':'tb', 'text-anchor':'middle'
    }, interG);
    fbLabelEl.textContent = 'governance feedback';

    // ── 7. Node layer ─────────────────────────────────────────────────────────
    var nodeG = se('g', { id:'lnf-nodes' }, svg);

    // Category group micro-labels (dim, above each module group)
    CATS.forEach(function(cat, ci) {
      var firstMI = catModIdxs[ci][0];
      var t = se('text', {
        x:CX.mod-6, y:modY[firstMI]-8,
        fill:'#1e2c44', 'font-size':'7', 'font-family':'monospace',
        'text-anchor':'end', 'font-weight':'700'
      }, nodeG);
      t.textContent = 'C'+cat.id;
    });

    // Module dots + small right-side labels
    var modNodeEls = MODULES.map(function(m, mi) {
      var info = modInfos[mi];
      var glow = info.status !== 'None' ? 'url(#lnf-glow-'+info.status+')' : null;
      var g = se('g', { class:'lnf-nd' }, nodeG);

      var circleAttrs = { cx:CX.mod, cy:modY[mi], r:'4',
        fill:info.color, opacity:info.status==='None'?'0.20':'0.85', stroke:'none' };
      if (glow) circleAttrs.filter = glow;
      var circle = se('circle', circleAttrs, g);
      if (info.status === 'Red') circle.classList.add('lnf-red-pulse');

      // Small label to the right (7px, truncated 20 chars)
      var lbl = se('text', {
        x:CX.mod+7, y:modY[mi],
        fill:info.status==='None'?'#1e2c44':'#5a7898',
        'font-size':'7', 'font-family':'monospace',
        'dominant-baseline':'middle', 'pointer-events':'none'
      }, g);
      lbl.textContent = trunc(m.name, 20);

      g.addEventListener('mouseenter', (function(m, mi, info, circle) {
        return function(evt) {
          circle.setAttribute('r','6');
          var metStr = info.metric ? '<div class="sub">metric: '+escH(info.metric)+'</div>' : '';
          showTT(evt,'<div class="m">'+escH(m.num)+'</div><div class="n">'+escH(m.name)+'</div><div class="sub" style="color:'+info.color+'">'+info.status+'</div>'+metStr+'<div class="sub">'+escH(CATS[m.catI].name)+'</div>');
          modCatEls[mi].setAttribute('opacity','0.70');
          modCatEls[mi].setAttribute('stroke-width','1.4');
          docLineMap.forEach(function(arr, di) {
            arr.forEach(function(e) { if (e.modI===mi) { e.el.setAttribute('opacity','0.65'); e.el.setAttribute('stroke-width','1.3'); } });
          });
        };
      })(m, mi, info, circle));
      g.addEventListener('mousemove', moveTT);
      g.addEventListener('mouseleave', (function(mi, info, circle) {
        return function() {
          hideTT();
          circle.setAttribute('r','4');
          modCatEls[mi].setAttribute('opacity','0.15');
          modCatEls[mi].setAttribute('stroke-width','0.8');
          docLineMap.forEach(function(arr, di) {
            arr.forEach(function(e) {
              if (e.modI===mi) {
                e.el.setAttribute('opacity', isUploaded(DOCS[di])?'0.20':'0.05');
                e.el.setAttribute('stroke-width','0.7');
              }
            });
          });
        };
      })(mi, info, circle));
      return g;
    });

    // Category nodes
    var catNodeEls = CATS.map(function(cat, ci) {
      var cs=catStatuses[ci], color=colFor(cs);
      var glow = cs !== 'None' ? 'url(#lnf-glow-'+cs+')' : null;
      var x=CX.cat, y=catCY[ci];
      var g = se('g', { class:'lnf-nd' }, nodeG);
      var cAttrs = { cx:x, cy:y, r:'9', fill:color, opacity:cs==='None'?'0.28':'0.88', stroke:'none' };
      if (glow) cAttrs.filter = glow;
      var circle = se('circle', cAttrs, g);
      if (cs==='Red') circle.classList.add('lnf-red-pulse');
      var t = se('text', { x:x+13, y:y, fill:'#6a8aaa', 'font-size':'9', 'font-family':'monospace', 'dominant-baseline':'middle' }, g);
      t.textContent = 'C'+cat.id+' '+cat.short;

      g.addEventListener('mouseenter', (function(cat, ci, cs, color, circle) {
        return function(evt) {
          circle.setAttribute('r','11');
          var icIn  = interCatEls.filter(function(l){return l.dstI===ci;}).map(function(l){return 'C'+(l.srcI+1);});
          var icOut = interCatEls.filter(function(l){return l.srcI===ci;}).map(function(l){return 'C'+(l.dstI+1);});
          var sub = cat.count+' modules';
          if (icIn.length)  sub += ' · from: '+[...new Set(icIn)].join(', ');
          if (icOut.length) sub += ' · to: '+[...new Set(icOut)].join(', ');
          showTT(evt,'<div class="n">C'+(ci+1)+': '+escH(cat.name)+'</div><div class="sub" style="color:'+color+'">'+cs+'</div><div class="sub">'+sub+'</div>');
        };
      })(cat, ci, cs, color, circle));
      g.addEventListener('mousemove', moveTT);
      g.addEventListener('mouseleave', (function(circle) {
        return function() { hideTT(); circle.setAttribute('r','9'); };
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
    [['Project',-5],['Status',7]].forEach(function(pair) {
      var t = se('text', { x:CX.prj, y:PRJ_Y+pair[1], fill:'#e8f0ff', 'font-size':'9', 'font-weight':'700',
        'text-anchor':'middle', 'dominant-baseline':'middle', 'font-family':'monospace' }, prjG);
      t.textContent = pair[0];
    });
    var prjStatusText = se('text', { x:CX.prj, y:PRJ_Y+34, fill:prjColor, 'font-size':'10', 'font-weight':'700',
      'text-anchor':'middle', 'font-family':'monospace' }, prjG);
    prjStatusText.textContent = prjStatus;
    prjG.addEventListener('mouseenter', function(evt) {
      showTT(evt,'<div class="n">Project Status</div><div class="sub" style="color:'+prjColor+'">'+prjStatus+'</div><div class="sub">DST fusion of 12 categories</div>');
    });
    prjG.addEventListener('mousemove', moveTT);
    prjG.addEventListener('mouseleave', hideTT);

    // Feedback arc events
    fbEl.style.cursor = 'default';
    fbEl.addEventListener('mouseenter', function(evt) {
      fbEl.setAttribute('opacity','0.80'); fbLabelEl.setAttribute('opacity','0.90');
      showTT(evt,'<div class="n">Governance Feedback</div><div class="sub" style="color:'+COL.Red+'">Cat 9 loop</div><div class="sub">Governance decisions feed back into Cat 9 compliance monitoring</div>');
    });
    fbEl.addEventListener('mousemove', moveTT);
    fbEl.addEventListener('mouseleave', function() { hideTT(); fbEl.setAttribute('opacity','0.30'); fbLabelEl.setAttribute('opacity','0.50'); });

    // Document nodes (rendered last = on top)
    DOCS.forEach(function(name, di) {
      var uploaded = isUploaded(name);
      var color = uploaded ? COL.DocOn : COL.DocOff;
      var glow  = uploaded ? 'url(#lnf-glow-DocOn)' : null;
      var x=CX.doc, y=docY(di);
      var g = se('g', { class:'lnf-nd' }, nodeG);
      var dAttrs = { cx:x, cy:y, r:'5', fill:color, opacity:uploaded?'0.88':'0.30', stroke:'none' };
      if (glow) dAttrs.filter = glow;
      se('circle', dAttrs, g);
      var t = se('text', { x:x-9, y:y, fill:uploaded?'#7a9ac0':'#253045',
        'font-size':'8.5', 'font-family':'monospace', 'text-anchor':'end', 'dominant-baseline':'middle' }, g);
      t.textContent = name;

      g.addEventListener('mouseenter', (function(name, di, uploaded, color) {
        return function(evt) {
          var cats = DOC_TO_CATS[di].map(function(ci){return 'C'+(ci+1);}).join(', ');
          showTT(evt,'<div class="n">'+escH(name)+'</div><div class="sub" style="color:'+color+'">'+(uploaded?'Uploaded':'Not uploaded')+'</div><div class="sub">Feeds: '+cats+'</div>');
          if (uploaded) {
            docLineMap[di].forEach(function(e) { e.el.setAttribute('opacity','0.65'); e.el.setAttribute('stroke-width','1.4'); });
          }
        };
      })(name, di, uploaded, color));
      g.addEventListener('mousemove', moveTT);
      g.addEventListener('mouseleave', (function(di, uploaded) {
        return function() {
          hideTT();
          if (uploaded) docLineMap[di].forEach(function(e) { e.el.setAttribute('opacity','0.20'); e.el.setAttribute('stroke-width','0.7'); });
        };
      })(di, uploaded));
    });

    // ── 8. Legend strip ───────────────────────────────────────────────────────
    var leg = document.createElement('div');
    leg.style.cssText = 'display:flex;align-items:center;gap:12px;flex-wrap:wrap;padding:7px 10px 4px;' +
      'font-size:9px;color:#4a5a7a;font-family:monospace;border-top:1px solid #1a2440;margin-top:2px;';

    function legDot(color, glow) {
      var sh = glow ? '0 0 5px '+color : 'none';
      return '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:'+color+';box-shadow:'+sh+';vertical-align:middle;margin-right:3px"></span>';
    }
    [['Green',COL.Green,true],['Yellow',COL.Yellow,true],['Amber',COL.Amber,true],
     ['Red',COL.Red,true],['No data',COL.None,false]].forEach(function(t) {
      var s = document.createElement('span');
      s.innerHTML = legDot(t[1],t[2]) + t[0];
      leg.appendChild(s);
    });
    var sep = document.createElement('span');
    sep.style.cssText = 'border-left:1px solid #1a2440;height:10px;';
    leg.appendChild(sep);
    [['Uploaded',COL.DocOn,true],['Not uploaded',COL.DocOff,false]].forEach(function(t) {
      var s = document.createElement('span');
      s.innerHTML = legDot(t[1],t[2]) + t[0];
      leg.appendChild(s);
    });
    container.appendChild(leg);
  }

  window.LinNeuralFlow = { render: render };
})();
