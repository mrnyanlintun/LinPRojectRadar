/* ============================================================
   Lin — 3D Force Network Visualization
   108 modules · 12 categories · signal flow connections
   Exposes window.LinForceNet
   ============================================================ */
(function () {
  "use strict";

  // ── CATEGORY DATA ──────────────────────────────────────────────
  // Built from window.LIN_CATEGORIES when available; hard-coded as fallback.
  var CATS_FALLBACK = [
    {id:"cat1",  name:"Quantitative EVM",       short:"Cat 1",  color:"#4ea0ff", count:12},
    {id:"cat2",  name:"Schedule Simulation",    short:"Cat 2",  color:"#2dd4bf", count:11},
    {id:"cat3",  name:"Cost Simulation",        short:"Cat 3",  color:"#e9a23b", count:10},
    {id:"cat4",  name:"Doc & Risk Signals",     short:"Cat 4",  color:"#f59e0b", count:10},
    {id:"cat5",  name:"System Dynamics",        short:"Cat 5",  color:"#8b5cf6", count:8},
    {id:"cat6",  name:"Signal Synthesis",       short:"Cat 6",  color:"#e2b13c", count:4},
    {id:"cat7",  name:"Evidence Combination",   short:"Cat 7",  color:"#9b6dff", count:20},
    {id:"cat8",  name:"ML & AI Detection",      short:"Cat 8",  color:"#64748b", count:5},
    {id:"cat9",  name:"Governance",             short:"Cat 9",  color:"#e0556b", count:9},
    {id:"cat10", name:"Data Integrity",         short:"Cat 10", color:"#06b6d4", count:7},
    {id:"cat11", name:"Decision Optimization",  short:"Cat 11", color:"#10b981", count:7},
    {id:"cat12", name:"Systems Engineering",    short:"Cat 12", color:"#8b5cf6", count:5}
  ];

  var NAMES_FALLBACK = {
    cat1: ["Monte Carlo EAC","CUSUM Monitor","Document Risk","Bayesian EAC","Kalman SPI","ARIMA CPI",
           "Earned Schedule","TCPI","VAC","Budget Exec Rate","Regression CPI","ICE Ratio"],
    cat2: ["PERT Criticality","Line of Balance","CCPM Buffer","Sched Compression","Float Consumption",
           "S-Curve Deviation","Milestone Trend","Look-Ahead Health","Resource Loading","Sched Risk P80","Critical Path Index"],
    cat3: ["Reference Class","DSM Rework","Contingency Burn","Labor Productivity","Material Cost Var",
           "Overhead Absorption","Cost Risk P80","Analogous Est","Parametric Cost","Inflation Adjustment"],
    cat4: ["Document Risk Score","RFI Velocity","Submittal Rejection","NCR Rate","Weather Day Impact",
           "Change Order Freq","Dispute Escalation","Subcontractor Perf","Procurement Lead","Spec Conflict"],
    cat5: ["DSM Propagation","Sensitivity Analysis","Tornado Ranking","Scenario Modeling",
           "Rework Feedback","Queueing Bottleneck","Agent-Based Supply","Discrete Event Sim"],
    cat6: ["Conservative Dominance","Weighted Voting","Majority Rules","Worst-N-of-M"],
    cat7: ["Dempster-Shafer","Rough Sets","Neutrosophic","Interval Fuzzy","Z-numbers","PLTS",
           "Plithogenic","Belief Rule Base","Quantum Probability","Pythagorean Fuzzy","Picture Fuzzy",
           "Hesitant Fuzzy","Type-2 Fuzzy","Maximum Entropy","Possibility Theory","Spherical Fuzzy",
           "Fermatean Fuzzy","MARCOS","CRITIC-TOPSIS","Hypersoft Sets"],
    cat8: ["Isolation Forest","Portfolio Outlier","Trajectory Classifier","Cross-project Pattern","Anomaly Score"],
    cat9: ["ABM Governance","FAR Threshold","OMB A-11","EVM Reporting","Contract Mod Freq",
           "Quality Compliance","Safety Performance","Environmental Comp","Contractor Score"],
    cat10:["Missing Data Index","Data Timeliness","Source Reliability","Audit Trail",
           "Info Completeness","Cross-doc Consistency","Reporting Frequency"],
    cat11:["Multi-Objective Opt","Linear Programming","Constraint Satisfaction","What-If Scenario",
           "Decision Sensitivity","Pareto Frontier","Regret Minimization"],
    cat12:["Interface Density","Dependency Mapping","Requirements Trace","Config Change Impact","Integration Complexity"]
  };

  // Signal flow connections (inner → outer; cat6 = synthesis hub)
  var CONNS = [
    {from:"cat1",to:"cat6"},{from:"cat2",to:"cat6"},{from:"cat3",to:"cat6"},
    {from:"cat4",to:"cat6"},{from:"cat5",to:"cat6"},
    {from:"cat6",to:"cat7"},{from:"cat6",to:"cat9"},
    {from:"cat7",to:"cat9"},{from:"cat8",to:"cat7"},{from:"cat8",to:"cat9"},
    {from:"cat10",to:"cat6"},{from:"cat10",to:"cat7"},
    {from:"cat11",to:"cat9"},{from:"cat12",to:"cat5"}
  ];

  var SC = {Complete:"#4ea0ff",Green:"#3fcaa6",Yellow:"#f0c040",Amber:"#e2b13c",Red:"#e0556b","null":"#26344f"};

  // ── MODULE REGISTRY ────────────────────────────────────────────
  var CATS_DATA = [];
  var MODS = [];         // {idx, cat, catName, catShort, catColor, num, name, status, metric}
  var STATUS_MAP = {};   // catId → array of status strings (mutable, updated by live data)

  function buildModules() {
    CATS_DATA = [];
    MODS = [];
    STATUS_MAP = {};

    var cats = (window.LIN_CATEGORIES && window.LIN_CATEGORIES.length) ? window.LIN_CATEGORIES : null;
    if (cats) {
      cats.forEach(function (cat) {
        var short = cat.num; // cat.num is already "Cat 1", "Cat 10", etc.
        var fallbackNames = NAMES_FALLBACK[cat.id] || [];
        var d = {id: cat.id, name: cat.name, short: short, color: cat.color, count: cat.modules.length};
        CATS_DATA.push(d);
        STATUS_MAP[cat.id] = cat.modules.map(function () { return null; });
        cat.modules.forEach(function (m, i) {
          MODS.push({
            idx: MODS.length, cat: cat.id, catName: cat.name, catShort: short,
            catColor: cat.color, num: short + "." + (i + 1),
            name: m.name || fallbackNames[i] || ("Module " + (i + 1)),
            methodClass: m.method_class || "",
            status: null, metric: ""
          });
        });
      });
    } else {
      CATS_FALLBACK.forEach(function (cat) {
        CATS_DATA.push(cat);
        STATUS_MAP[cat.id] = [];
        var names = NAMES_FALLBACK[cat.id] || [];
        for (var i = 0; i < cat.count; i++) {
          STATUS_MAP[cat.id].push(null);
          MODS.push({
            idx: MODS.length, cat: cat.id, catName: cat.name, catShort: cat.short,
            catColor: cat.color, num: cat.short + "." + (i + 1),
            name: names[i] || ("Module " + (i + 1)), methodClass: "", status: null, metric: ""
          });
        }
      });
    }

    // Sync MODS statuses from STATUS_MAP
    syncStatuses();
  }

  function syncStatuses() {
    MODS.forEach(function (m) {
      var arr = STATUS_MAP[m.cat];
      if (!arr) return;
      var catMods = MODS.filter(function (mm) { return mm.cat === m.cat; });
      var i = catMods.indexOf(m);
      m.status = (arr[i] != null && arr[i] !== "null") ? arr[i] : null;
    });
  }

  // ── 3D LAYOUT ──────────────────────────────────────────────────
  var CAT_POS = {};
  var MOD_POS = [];

  function buildLayout() {
    CAT_POS = {};
    var inner = ["cat1","cat2","cat3","cat4","cat5","cat6"];
    var outer = ["cat7","cat8","cat9","cat10","cat11","cat12"];
    var IR = 150, OR = 290;

    inner.forEach(function (id, i) {
      var a = (i / inner.length) * Math.PI * 2 - Math.PI / 2;
      CAT_POS[id] = {x: IR * Math.cos(a), y: IR * Math.sin(a) * 0.5, z: IR * Math.sin(a)};
    });
    outer.forEach(function (id, i) {
      var a = (i / outer.length) * Math.PI * 2 - Math.PI / 6;
      CAT_POS[id] = {x: OR * Math.cos(a), y: OR * Math.sin(a) * 0.4, z: OR * Math.sin(a)};
    });

    MOD_POS = [];
    MODS.forEach(function (m) {
      var cp = CAT_POS[m.cat];
      if (!cp) return;
      var mods = MODS.filter(function (mm) { return mm.cat === m.cat; });
      var mi = mods.indexOf(m), n = mods.length;
      var ring = mi < 5 ? 0 : 1;
      var rIdx = ring === 0 ? mi : mi - 5;
      var rCount = ring === 0 ? Math.min(5, n) : n - 5;
      var rR = ring === 0 ? 45 : 75;
      var a = (rIdx / Math.max(rCount, 1)) * Math.PI * 2 + ring * 0.5;
      var tilt = 0.5;
      MOD_POS.push({
        m: m,
        x: cp.x + rR * Math.cos(a),
        y: cp.y + rR * Math.sin(a) * Math.sin(tilt),
        z: cp.z + rR * Math.sin(a) * Math.cos(tilt),
        cx: cp.x, cy: cp.y, cz: cp.z
      });
    });
  }

  // ── 3D ENGINE ──────────────────────────────────────────────────
  function rotX(p, a) { return {x:p.x, y:p.y*Math.cos(a)-p.z*Math.sin(a), z:p.y*Math.sin(a)+p.z*Math.cos(a)}; }
  function rotY(p, a) { return {x:p.x*Math.cos(a)+p.z*Math.sin(a), y:p.y, z:-p.x*Math.sin(a)+p.z*Math.cos(a)}; }

  var cv = null, ctx = null;
  var RX = 0.28, RY = 0.42, ZOOM = 1.0;
  var DEFAULT_RX = 0.28, DEFAULT_RY = 0.42, DEFAULT_ZOOM = 1.0;
  var autoR = false, dragging = false, lastX, lastY;
  var focusCat = null, hovered = null, hoveredCat = null;
  var rafRunning = false;

  function getCanvasW() { return cv ? cv.clientWidth : 800; }
  function getCanvasH() { return cv ? 500 : 500; }

  function project3d(p) {
    var W = cv.width, H = cv.height;
    var cx = W / 2, cy = H / 2;
    var FOV = Math.min(W, H) * 0.9;
    var px = p.x * ZOOM, py = p.y * ZOOM, pz = p.z * ZOOM;
    var z = pz + FOV;
    if (z < 1) z = 1;
    var s = FOV / z;
    return {x: cx + px * s, y: cy + py * s, s: s};
  }

  function transform(p) {
    return project3d(rotX(rotY(p, RY), RX));
  }

  // ── DRAW ───────────────────────────────────────────────────────
  function draw() {
    if (!cv || !ctx) return;
    var W = cv.width, H = cv.height;
    ctx.clearRect(0, 0, W, H);

    // 1. Inter-category connection lines with flow arrows
    CONNS.forEach(function (conn) {
      var fp = CAT_POS[conn.from], tp = CAT_POS[conn.to];
      if (!fp || !tp) return;
      var pf = transform(fp), pt2 = transform(tp);
      if (!isFinite(pf.x) || !isFinite(pt2.x)) return;

      var active = !focusCat || conn.from === focusCat || conn.to === focusCat;
      var fc = CATS_DATA.find(function (c) { return c.id === conn.from; });
      var tc = CATS_DATA.find(function (c) { return c.id === conn.to; });
      if (!fc || !tc) return;

      var g = ctx.createLinearGradient(pf.x, pf.y, pt2.x, pt2.y);
      g.addColorStop(0, fc.color + (active ? "66" : "18"));
      g.addColorStop(1, tc.color + (active ? "99" : "18"));
      ctx.beginPath(); ctx.moveTo(pf.x, pf.y); ctx.lineTo(pt2.x, pt2.y);
      ctx.strokeStyle = g;
      ctx.lineWidth = active ? 1.5 : 0.5;
      ctx.stroke();

      if (active) {
        var ax = pf.x + (pt2.x - pf.x) * 0.65;
        var ay = pf.y + (pt2.y - pf.y) * 0.65;
        var ang = Math.atan2(pt2.y - pf.y, pt2.x - pf.x);
        ctx.save(); ctx.translate(ax, ay); ctx.rotate(ang);
        ctx.beginPath(); ctx.moveTo(-5, -3); ctx.lineTo(5, 0); ctx.lineTo(-5, 3);
        ctx.fillStyle = tc.color + "bb"; ctx.fill();
        ctx.restore();
      }
    });

    // 2. Module→category spokes (depth-sorted)
    var sortedMods = MOD_POS.map(function (mp) {
      var p = rotX(rotY(mp, RY), RX);
      return {mp: mp, pz: p.z, pp: transform(mp), cpp: transform({x:mp.cx,y:mp.cy,z:mp.cz})};
    }).sort(function (a, b) { return a.pz - b.pz; });

    sortedMods.forEach(function (s) {
      var focused = !focusCat || s.mp.m.cat === focusCat;
      if (!isFinite(s.pp.x) || !isFinite(s.cpp.x)) return;
      ctx.beginPath(); ctx.moveTo(s.pp.x, s.pp.y); ctx.lineTo(s.cpp.x, s.cpp.y);
      ctx.strokeStyle = s.mp.m.catColor + (focused ? "55" : "10");
      ctx.lineWidth = focused ? 0.9 : 0.3;
      ctx.stroke();
    });

    // 3. Category nodes
    var sortedCats = Object.keys(CAT_POS).map(function (id) {
      var cp = CAT_POS[id];
      var p = rotX(rotY(cp, RY), RX);
      return {id: id, pz: p.z, pp: transform(cp)};
    }).sort(function (a, b) { return a.pz - b.pz; });

    sortedCats.forEach(function (sc) {
      var cat = CATS_DATA.find(function (c) { return c.id === sc.id; });
      if (!cat || !isFinite(sc.pp.x)) return;
      var focused = !focusCat || sc.id === focusCat;
      var r = Math.max(10, 15 * sc.pp.s);
      if (focusCat && sc.id === focusCat) r *= 1.3;

      ctx.globalAlpha = focused ? 1 : 0.1;
      var isHovCat = hoveredCat === sc.id;

      if (isHovCat) {
        ctx.beginPath(); ctx.arc(sc.pp.x, sc.pp.y, r + 6, 0, Math.PI * 2);
        ctx.strokeStyle = cat.color + "44"; ctx.lineWidth = 3; ctx.stroke();
      }
      ctx.beginPath(); ctx.arc(sc.pp.x, sc.pp.y, r, 0, Math.PI * 2);
      ctx.strokeStyle = cat.color + (isHovCat ? "ff" : "cc");
      ctx.lineWidth = isHovCat ? 3 : 2; ctx.stroke();
      ctx.fillStyle = cat.color + (isHovCat ? "33" : "18"); ctx.fill();

      ctx.font = "bold 9px SFMono-Regular,monospace";
      ctx.fillStyle = cat.color;
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(cat.short.replace("Cat ", ""), sc.pp.x, sc.pp.y);
      ctx.textBaseline = "alphabetic";

      var tagText = cat.short + " — " + cat.name;
      ctx.font = "bold 10px SFMono-Regular,monospace";
      var tw = ctx.measureText(tagText).width;
      var tx = sc.pp.x - tw / 2 - 8, ty = sc.pp.y + r + 8;
      ctx.beginPath();
      if (ctx.roundRect) ctx.roundRect(tx, ty, tw + 16, 18, 4);
      else ctx.rect(tx, ty, tw + 16, 18);
      ctx.fillStyle = cat.color + "22"; ctx.fill();
      ctx.strokeStyle = cat.color + "66"; ctx.lineWidth = 1; ctx.stroke();
      ctx.fillStyle = cat.color; ctx.textAlign = "center";
      ctx.fillText(tagText, sc.pp.x, ty + 13);
      ctx.textAlign = "left";
      ctx.globalAlpha = 1;
    });

    // 4. Module dots
    sortedMods.forEach(function (s) {
      var m = s.mp.m;
      var col = SC[m.status || "null"] || SC["null"];
      var focused = !focusCat || m.cat === focusCat;
      var isH = hovered && hovered.m.idx === m.idx;
      if (!isFinite(s.pp.x)) return;

      var r = m.status ? Math.max(3, 4 * s.pp.s) : Math.max(1.5, 2 * s.pp.s);
      if (focusCat && m.cat === focusCat) r *= 1.4;
      if (isH) r *= 1.8;

      ctx.beginPath(); ctx.arc(s.pp.x, s.pp.y, r, 0, Math.PI * 2);
      ctx.fillStyle = col;
      ctx.globalAlpha = focused ? (m.status ? (isH ? 1 : 0.85) : 0.2) : 0.05;
      ctx.fill();

      if (m.status && focused) {
        ctx.beginPath(); ctx.arc(s.pp.x, s.pp.y, r + 1, 0, Math.PI * 2);
        ctx.strokeStyle = m.catColor + "66"; ctx.lineWidth = 0.8;
        ctx.globalAlpha = 0.6; ctx.stroke();
      }
      if (focused && focusCat && m.status) {
        ctx.font = "7px SFMono-Regular,monospace";
        ctx.fillStyle = col; ctx.globalAlpha = 0.7;
        ctx.textAlign = "center";
        ctx.fillText(m.num, s.pp.x, s.pp.y - r - 2);
        ctx.textAlign = "left";
      }
      if (isH) {
        ctx.beginPath(); ctx.arc(s.pp.x, s.pp.y, r + 3, 0, Math.PI * 2);
        ctx.strokeStyle = "#ffffff44"; ctx.lineWidth = 1.5;
        ctx.globalAlpha = 1; ctx.stroke();
      }
      ctx.globalAlpha = 1;
    });

    // 5. Overlay: legend text + focus info
    ctx.font = "10px SFMono-Regular,monospace"; ctx.fillStyle = "#64748b";
    ctx.fillText("FORCE NETWORK — 108 MODULES · 12 CATEGORIES", 16, 26);
    ctx.font = "9px SFMono-Regular,monospace"; ctx.fillStyle = "#64748b";
    ctx.fillText("→ arrows show signal flow · inner ring = generators · outer ring = synthesis/evidence/governance", 16, 42);

    if (focusCat) {
      var fc2 = CATS_DATA.find(function (c) { return c.id === focusCat; });
      var fm = MODS.filter(function (m) { return m.cat === focusCat; });
      var fR = fm.filter(function (m) { return m.status === "Red"; }).length;
      var fA = fm.filter(function (m) { return m.status === "Amber"; }).length;
      var fG = fm.filter(function (m) { return m.status === "Green"; }).length;
      var fAct = fm.filter(function (m) { return m.status; }).length;
      ctx.font = "bold 11px SFMono-Regular,monospace";
      ctx.fillStyle = fc2 ? fc2.color : "#e9a23b"; ctx.globalAlpha = 0.9;
      ctx.fillText("FOCUS: " + (fc2 ? fc2.short + " — " + fc2.name : focusCat), 16, H - 14);
      ctx.font = "10px -apple-system,sans-serif"; ctx.fillStyle = "#9fb0cc"; ctx.globalAlpha = 0.8;
      ctx.fillText(fAct + " active · " + fR + " Red · " + fA + " Amber · " + fG + " Green · click again to clear", 16, H - 2);
      ctx.globalAlpha = 1;
    }
  }

  // ── STATS BAR UPDATE ───────────────────────────────────────────
  function updateStats() {
    var el = document.getElementById("fn-stat");
    if (!el) return;
    var sc2 = {Red:0, Amber:0, Yellow:0, Green:0};
    MODS.forEach(function (m) { if (m.status && sc2[m.status] !== undefined) sc2[m.status]++; });
    var act = MODS.filter(function (m) { return m.status; }).length;
    el.textContent = act + " active · " + sc2.Red + " Red · " + sc2.Amber + " Amber · " + sc2.Yellow + " Yellow · " + sc2.Green + " Green";
  }

  // ── CATEGORY BUTTONS ───────────────────────────────────────────
  function buildCatButtons() {
    var container = document.getElementById("fn-cat-btns");
    if (!container) return;
    container.innerHTML = "";
    CATS_DATA.forEach(function (cat) {
      var b = document.createElement("button");
      b.className = "fn-cbtn";
      b.dataset.cat = cat.id;
      b.textContent = cat.short;
      b.title = cat.name + " · click to focus";
      b.style.color = cat.color;
      b.style.borderColor = cat.color + "66";
      b.addEventListener("click", function () {
        setFocus(focusCat === cat.id ? null : cat.id);
        if (focusCat) focusCatWithCenter(focusCat);
      });
      container.appendChild(b);
    });
  }

  function setFocus(catId) {
    focusCat = catId;
    var allBtn = document.getElementById("fn-btn-all");
    if (allBtn) allBtn.classList.toggle("active", !catId);
    document.querySelectorAll(".fn-cbtn").forEach(function (b) {
      b.classList.toggle("active", b.dataset.cat === catId);
      b.style.opacity = (!catId || b.dataset.cat === catId) ? "1" : "0.35";
    });
  }

  function resetView() {
    RX = DEFAULT_RX; RY = DEFAULT_RY; ZOOM = DEFAULT_ZOOM;
    autoR = false;
    setFocus(null);
  }

  function focusCatWithCenter(catId) {
    var cp = CAT_POS[catId];
    if (!cp) return;
    var targetRY = -Math.atan2(cp.x, cp.z);
    var dist = Math.sqrt(cp.x * cp.x + cp.z * cp.z);
    var targetRX = Math.atan2(cp.y, dist) * 0.6;
    var startRX = RX, startRY = RY, startZoom = ZOOM, targetZoom = 2.2;
    while (targetRY - startRY > Math.PI) targetRY -= Math.PI * 2;
    while (targetRY - startRY < -Math.PI) targetRY += Math.PI * 2;
    var t = 0, dur = 45;
    function animStep() {
      t++;
      var p = t / dur;
      var ease = p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
      RX = startRX + (targetRX - startRX) * ease;
      RY = startRY + (targetRY - startRY) * ease;
      ZOOM = startZoom + (targetZoom - startZoom) * ease;
      if (t < dur) requestAnimationFrame(animStep);
    }
    requestAnimationFrame(animStep);
  }

  // ── TOOLTIP ────────────────────────────────────────────────────
  function showTooltip(e, m) {
    var tt = document.getElementById("fn-tooltip");
    if (!tt) return;
    var col = SC[m.status || "null"] || SC["null"];
    tt.querySelector(".fn-tt-cat").textContent = m.catName;
    tt.querySelector(".fn-tt-cat").style.color = m.catColor;
    tt.querySelector(".fn-tt-num").textContent = m.num;
    tt.querySelector(".fn-tt-name").textContent = m.name;
    var el = tt.querySelector(".fn-tt-status");
    el.textContent = m.status || (m.cat === "cat12" ? "Conditional" : "No data");
    el.style.background = col + "18"; el.style.color = col; el.style.border = "1px solid " + col + "44";
    tt.querySelector(".fn-tt-metric").textContent = m.metric || "";
    var rect = cv.getBoundingClientRect();
    tt.style.display = "block";
    var tx = e.clientX - rect.left + 14;
    var ty = e.clientY - rect.top - 8;
    if (tx + 250 > rect.width) tx = e.clientX - rect.left - 254;
    if (ty + 160 > rect.height) ty = e.clientY - rect.top - 164;
    tt.style.left = tx + "px"; tt.style.top = ty + "px";
  }

  function hideTooltip() {
    var tt = document.getElementById("fn-tooltip");
    if (tt) tt.style.display = "none";
  }

  // ── CANVAS RESIZE ─────────────────────────────────────────────
  function resizeCanvas() {
    if (!cv) return;
    var w = cv.parentElement ? cv.parentElement.clientWidth : 800;
    cv.width = w;
    cv.height = 500;
  }

  // ── ANIMATION LOOP ─────────────────────────────────────────────
  function loop() {
    if (autoR && !dragging) RY += 0.0018;
    draw();
    requestAnimationFrame(loop);
  }

  // ── PUBLIC INIT ────────────────────────────────────────────────
  function init() {
    cv = document.getElementById("fn-canvas");
    if (!cv) return;
    ctx = cv.getContext("2d");

    buildModules();
    buildLayout();
    resizeCanvas();
    buildCatButtons();
    updateStats();

    // Mouse events
    cv.addEventListener("mousedown", function (e) {
      dragging = true; lastX = e.clientX; lastY = e.clientY; autoR = false;
    });
    window.addEventListener("mouseup", function () { dragging = false; });

    cv.addEventListener("mousemove", function (e) {
      if (dragging) {
        RY += (e.clientX - lastX) * 0.005;
        RX += (e.clientY - lastY) * 0.005;
        lastX = e.clientX; lastY = e.clientY;
        return;
      }
      var rect = cv.getBoundingClientRect();
      var mx = e.clientX - rect.left, my = e.clientY - rect.top;

      // Category hover
      var bestCat = null, bestCatD = 30;
      Object.keys(CAT_POS).forEach(function (id) {
        var pp = transform(CAT_POS[id]);
        if (!isFinite(pp.x)) return;
        var r = Math.max(10, 15 * pp.s) * 1.3;
        var d = Math.sqrt((mx - pp.x) * (mx - pp.x) + (my - pp.y) * (my - pp.y));
        if (d < r && d < bestCatD) { bestCatD = d; bestCat = id; }
      });
      hoveredCat = bestCat;

      // Module hover
      var best = null, bestD = 26;
      MOD_POS.forEach(function (mp) {
        var pp = transform(mp);
        if (!isFinite(pp.x)) return;
        var d = Math.sqrt((mx - pp.x) * (mx - pp.x) + (my - pp.y) * (my - pp.y));
        if (d < bestD) { bestD = d; best = mp; }
      });
      hovered = best;

      if (hoveredCat) {
        hideTooltip();
        cv.style.cursor = "pointer";
      } else if (best) {
        showTooltip(e, best.m);
        cv.style.cursor = "crosshair";
      } else {
        hideTooltip();
        cv.style.cursor = dragging ? "grabbing" : "grab";
      }
    });

    cv.addEventListener("mouseleave", function () {
      hideTooltip();
      hovered = null; hoveredCat = null;
    });

    cv.addEventListener("click", function () {
      if (hoveredCat) {
        if (focusCat === hoveredCat) { setFocus(null); return; }
        setFocus(hoveredCat);
        focusCatWithCenter(hoveredCat);
      }
    });

    cv.addEventListener("wheel", function (e) {
      e.preventDefault();
      var delta = e.deltaY > 0 ? 0.93 : 1.07;
      ZOOM = Math.max(0.3, Math.min(4.0, ZOOM * delta));
    }, {passive: false});

    window.addEventListener("resize", function () { resizeCanvas(); });

    // Wire header buttons
    var allBtn = document.getElementById("fn-btn-all");
    if (allBtn) allBtn.addEventListener("click", function () { setFocus(null); });
    var resetBtn = document.getElementById("fn-btn-reset");
    if (resetBtn) resetBtn.addEventListener("click", resetView);

    if (!rafRunning) { rafRunning = true; loop(); }
  }

  // ── PUBLIC API ─────────────────────────────────────────────────
  window.LinForceNet = {
    init: init,
    redraw: function () { draw(); updateStats(); },

    updateFromProject: function (project) {
      if (!project) return;
      var signals = (project.simulationSignals && project.simulationSignals.signal_array) || [];
      var cats = window.LIN_CATEGORIES || [];

      signals.forEach(function (sig) {
        if (!sig || !sig.method_class || !sig.status_color) return;
        var norm = sig.status_color;
        // Find module by method_class in LIN_CATEGORIES
        var found = null, foundCat = null;
        cats.forEach(function (cat) {
          (cat.modules || []).forEach(function (m, mi) {
            var mc = m.method_class === "DSM_Rework_Cat5" ? "DSM_Rework_Propagation" : m.method_class;
            if (mc === sig.method_class) { found = mi; foundCat = cat.id; }
          });
        });
        if (found === null || !foundCat) {
          // Also try matching by method_class in MODS
          MODS.forEach(function (m) {
            if (m.methodClass === sig.method_class) {
              var catMods = MODS.filter(function (mm) { return mm.cat === m.cat; });
              var i = catMods.indexOf(m);
              if (STATUS_MAP[m.cat]) STATUS_MAP[m.cat][i] = norm;
            }
          });
        } else {
          if (STATUS_MAP[foundCat]) STATUS_MAP[foundCat][found] = norm;
        }
      });
      syncStatuses();
      updateStats();
    },

    setModuleStatus: function (catId, modIdx, status) {
      if (STATUS_MAP[catId]) STATUS_MAP[catId][modIdx] = status;
      syncStatuses();
    }
  };
})();
