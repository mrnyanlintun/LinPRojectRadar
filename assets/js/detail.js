/* ============================================================
   Lin Project Radar — detail.js
   Project Detail drill-down: one project's identity, signal
   ledger, PCEIF decision card (fairness gate where applicable),
   and all five modules computed for that project.
   Reuses LinApp's ledger/decision-card renderers and
   LinModules.renderProjectModules — no duplicated rules.
   ============================================================ */

(function () {
  "use strict";

  const esc = (s) => String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");

  const SECTOR_LABEL = { design: "Design", construction: "Construction", hybrid: "Hybrid", combined: "Hybrid" };
  const selectedHistoryPeriod = {};
  const MODULES = [
    ["M01", "Monte Carlo"], ["M02", "CUSUM"], ["M03", "Doc Risk"],
    ["M04", "PERT"], ["M05", "LOB"], ["M06", "CCPM"], ["M07", "RCF"], ["M08", "DSM"],
    ["M09", "Conservative"], ["M10", "DST"], ["M11", "Rough Sets"], ["M12", "Neutrosophic"],
    ["M13", "Interval Fuzzy"], ["M14", "Z-numbers"], ["M15", "PLTS"], ["M16", "Plithogenic"],
    ["M17", "BRB"], ["M18", "Quantum"], ["M19", "ABM"]
  ];
  const MODULE_KEYS = [
    "m01_monte_carlo", "m02_cusum", "m03_doc_risk", "m04_pert", "m05_lob", "m06_ccpm",
    "m07_rcf", "m08_dsm", "m09_conservative", "m10_dst", "m11_rough_sets", "m12_neutrosophic",
    "m13_interval_fuzzy", "m14_z_numbers", "m15_plts", "m16_plithogenic", "m17_brb",
    "m18_quantum", "m19_abm"
  ];

  function normalizeStatus(status) {
    const s = String(status || "").toLowerCase();
    if (s === "red" || s === "red-review" || s === "critical") return "Red";
    if (s === "amber" || s === "orange") return "Amber";
    if (s === "yellow" || s === "light-amber" || s === "lightamber") return "Yellow";
    if (s === "green") return "Green";
    if (s === "complete" || s === "blue") return "Complete";
    return null;
  }
  function statusToRadius(status) {
    const s = normalizeStatus(status);
    if (s === "Red") return 1.00;
    if (s === "Amber") return 0.70;
    if (s === "Yellow") return 0.45;
    if (s === "Green") return 0.25;
    if (s === "Complete") return 0.10;
    // No-data axes sit on a tiny ring just off-centre instead of exactly 0 so
    // the 19-sided polygon closes cleanly (no collapse-to-centre starburst).
    return 0.05;
  }
  function statusClass(status) {
    const s = normalizeStatus(status);
    return s ? s.toLowerCase() : "none";
  }
  function periodLabel(period) {
    if (!period) return "Current period";
    const d = new Date(period + "-01T00:00:00Z");
    try { return d.toLocaleDateString(undefined, { month: "short", year: "numeric", timeZone: "UTC" }); }
    catch (e) { return period; }
  }
  function periodTitle(period) {
    if (!period) return "Signal Web";
    const d = new Date(period + "-01T00:00:00Z");
    try { return d.toLocaleDateString(undefined, { month: "long", year: "numeric", timeZone: "UTC" }); }
    catch (e) { return period; }
  }
  function currentSnapshot(project) {
    return window.LinSignals && LinSignals.buildHistorySnapshot
      ? LinSignals.buildHistorySnapshot(project)
      : null;
  }
  function sortedHistory(project) {
    return (Array.isArray(project.history) ? project.history.slice() : [])
      .filter((h) => h && h.period)
      .sort((a, b) => String(a.period).localeCompare(String(b.period)));
  }
  function snapshots(project) {
    const hist = sortedHistory(project);
    const cur = currentSnapshot(project);
    if (cur && !hist.some((h) => h.period === cur.period)) hist.push(cur);
    return hist.sort((a, b) => String(a.period).localeCompare(String(b.period)));
  }
  function statusFromResult(result) {
    if (!result) return null;
    return result.status || result.status_color || result.state || result.health_state || null;
  }
  function moduleStatuses(snapshot) {
    const results = (snapshot && snapshot.module_results) || {};
    return MODULE_KEYS.map((key) => statusFromResult(results[key]));
  }

  /* Backfill the M10-M18 evidence-combination methods on the fly when the
     persisted simulationSignals is missing them. Spider-web renders read
     module_results — if DST / Rough Sets / Neutrosophic etc never ran (or
     the persisted copy lost them on reload) those axes show as "no data"
     even when project.signals has the EVM / Monte Carlo / CUSUM / Doc inputs
     they depend on. Compute them client-side from window.LinSimulations and
     graft the results onto the snapshot we're about to render. */
  function ensureEvidenceModules(project, snapshot) {
    if (!project || !snapshot || !snapshot.module_results) return;
    const s = project.signals;
    if (!s) return;
    // Evidence methods need EVM-derived signals — at least one of these must
    // exist or every run() will return a "no data" stub.
    if (!s.evm && !s.mc && !s.cusum && !s.doc) return;
    if (!window.LinSimulations) return;
    const results = snapshot.module_results;
    const runners = [
      { key: "m10_dst",            fn: "runDST",                cls: "DST_Evidence_Combination",   needsInputs: true },
      { key: "m11_rough_sets",     fn: "runRoughSets",          cls: "Rough_Sets_Classification" },
      { key: "m12_neutrosophic",   fn: "runNeutrosophic",       cls: "Neutrosophic_Logic" },
      { key: "m13_interval_fuzzy", fn: "runIntervalFuzzy",      cls: "Interval_Fuzzy_Sets" },
      { key: "m14_z_numbers",      fn: "runZNumbers",           cls: "Z_Numbers" },
      { key: "m15_plts",           fn: "runPLTS",               cls: "PLTS" },
      { key: "m16_plithogenic",    fn: "runPlithogenic",        cls: "Plithogenic_Sets" },
      { key: "m17_brb",            fn: "runBRB",                cls: "Belief_Rule_Base" },
      { key: "m18_quantum",        fn: "runQuantumProbability", cls: "Quantum_Probability" }
    ];
    const si = project.signalInputs || {};
    runners.forEach((r) => {
      if (statusFromResult(results[r.key])) return; // already populated
      const fn = LinSimulations[r.fn];
      if (typeof fn !== "function") return;
      try {
        const out = r.needsInputs ? fn(si, s) : fn(s);
        if (out) results[r.key] = out;
      } catch (e) { /* non-fatal — axis stays at the no-data ring */ }
    });
  }
  function metricFor(snapshot, key) {
    const r = snapshot && snapshot.module_results && snapshot.module_results[key];
    if (!r) return "No data";
    if (key === "m01_monte_carlo") return r.p80_delta_pct != null ? "P80 +" + Number(r.p80_delta_pct).toFixed(1) + "%" : "P80 unavailable";
    if (key === "m02_cusum") return r.breached ? "Breached period " + (r.breach_period != null ? r.breach_period : "?") : "No breach";
    if (key === "m03_doc_risk") return r.score != null ? "Score " + Number(r.score).toFixed(2) : "Score unavailable";
    if (key === "m09_conservative") return r.conflict || r.state || "No decision";
    if (key === "m19_abm") return r.action || r.authority || r.state || "No decision";
    return r.evidence_metric || r.metric || r.status_color || "Computed";
  }
  function pointFor(i, radiusFactor, outerRadius) {
    const cx = 210, cy = 190;
    const angle = -Math.PI / 2 + (Math.PI * 2 * i / MODULES.length);
    const r = outerRadius * radiusFactor;
    return {
      x: cx + Math.cos(angle) * r,
      y: cy + Math.sin(angle) * r,
      tx: cx + Math.cos(angle) * (outerRadius + 20),
      ty: cy + Math.sin(angle) * (outerRadius + 20),
      ax: cx + Math.cos(angle) * outerRadius,
      ay: cy + Math.sin(angle) * outerRadius
    };
  }
  function polygonPoints(statuses) {
    return statuses.map((status, i) => {
      const p = pointFor(i, statusToRadius(status), 150);
      return p.x.toFixed(1) + "," + p.y.toFixed(1);
    }).join(" ");
  }
  // Inverted radius: full polygon at the rim = healthy. See PR #74 spec.
  function catRadius(status) {
    const s = normalizeStatus(status);
    if (s === "Complete") return 1.00;
    if (s === "Green") return 0.80;
    if (s === "Yellow") return 0.60;
    if (s === "Amber") return 0.35;
    if (s === "Red") return 0.10;
    return 0.05; // parked or no data
  }

  // Category-axis helpers — 9 axes evenly spaced (40deg apart), CSS centred
  // on (210, 190) like the previous module web.
  function catPointFor(i, radiusFactor, outerRadius) {
    const cx = 210, cy = 190, n = LIN_CATEGORIES.length;
    const angle = -Math.PI / 2 + (Math.PI * 2 * i / n);
    const r = outerRadius * radiusFactor;
    return {
      x: cx + Math.cos(angle) * r,
      y: cy + Math.sin(angle) * r,
      tx: cx + Math.cos(angle) * (outerRadius + 22),
      ty: cy + Math.sin(angle) * (outerRadius + 22),
      ax: cx + Math.cos(angle) * outerRadius,
      ay: cy + Math.sin(angle) * outerRadius
    };
  }

  function catPolygonPoints(statuses) {
    return statuses.map((status, i) => {
      const p = catPointFor(i, catRadius(status), 135);
      return p.x.toFixed(1) + "," + p.y.toFixed(1);
    }).join(" ");
  }

  function pickWorstModule(cat) {
    const order = { Red: 0, "Red-review": 1, Amber: 2, Yellow: 3, Green: 4, Complete: 5 };
    return (cat.modules || []).filter((m) => m.status).slice()
      .sort((a, b) => (order[a.status] != null ? order[a.status] : 3) - (order[b.status] != null ? order[b.status] : 3))[0] || null;
  }

  /* ============================================================
     89-axis module spider web. One axis per defined module across
     all 9 categories. Active modules plot at a status radius
     (healthy = near the rim); inactive / parked / no-data modules
     sit on a tiny grey ring just off-centre. Category clusters are
     separated by a small angular gap and backed by a faint arc in
     the category colour.
     ============================================================ */
  const MOD_CX = 250, MOD_CY = 250, MOD_OUTER = 200;
  const PARKED_GREY = "#64748b"; // Cat 8 (ML/AI) parked-status grey
  const DOT_COLOR = {
    Complete: "#4ea0ff", Green: "#3fcaa6", Yellow: "#f0c040",
    Amber: "#e2b13c", Red: "#e0556b", none: "#26344f"
  };

  function moduleStatusToRadius(status) {
    const s = normalizeStatus(status);
    if (s === "Complete") return 1.00;
    if (s === "Green") return 0.85;
    if (s === "Yellow") return 0.65;
    if (s === "Amber") return 0.40;
    if (s === "Red") return 0.15;
    return 0.05; // no data — grey near-centre
  }
  function moduleToRadius(module, status) {
    if (module.active === false || module.parked) return 0.05;
    if (!status) return 0.05;
    return moduleStatusToRadius(status);
  }
  function modPoint(angle, radiusFactor) {
    const r = MOD_OUTER * radiusFactor;
    return { x: MOD_CX + Math.cos(angle) * r, y: MOD_CY + Math.sin(angle) * r };
  }

  // Resolve a module's live evidence_metric for the hover tooltip.
  function moduleEvidence(m, project) {
    const sim = (project.simulationSignals && project.simulationSignals.signal_array) || [];
    const cls = m.method_class === "DSM_Rework_Cat5" ? "DSM_Rework_Propagation" : m.method_class;
    const found = sim.find((x) => x.method_class === cls);
    if (found && found.evidence_metric) return found.evidence_metric;
    const s = project.signals || {};
    if ((m.method_class === "Monte_Carlo") && s.mc)
      return s.mc.p80eacOverrunPct != null ? "P80 EAC +" + Number(s.mc.p80eacOverrunPct).toFixed(1) + "%" : null;
    if ((m.method_class === "CUSUM") && s.cusum)
      return s.cusum.breached ? "CUSUM breach detected" : "Within control limits";
    if ((m.method_class === "Doc_Risk" || m.method_class === "Doc_Risk_Cat4") && s.doc)
      return s.doc.score != null ? "Doc-risk score " + Number(s.doc.score).toFixed(2) : null;
    if ((m.method_class === "Conservative_Dominance" || m.method_class === "ABM_Governance") && s.decision)
      return s.decision.action || s.decision.state || null;
    return null;
  }

  // Flatten the 89 modules into axis entries with angles, leaving a one-slot
  // gap between categories so the clusters read as distinct petals.
  function buildModuleAxes(project) {
    const cats = LIN_CATEGORIES;
    const moduleCount = cats.reduce((n, c) => n + c.modules.length, 0);
    // One padding gap before EVERY cluster — including the first, which seats a
    // gap at the top (12 o'clock). Without it the last Cat 9 label and the first
    // Cat 1 label collide where the ring wraps. (Fixes top-of-chart overlap.)
    const gaps = cats.length;
    const totalSlots = moduleCount + gaps;
    const axes = [];
    const bands = [];
    let slot = 0;
    cats.forEach((cat) => {
      slot += 1; // cluster-separating gap (the first one lands at the top)
      const startSlot = slot;
      cat.modules.forEach((m) => {
        const angle = -Math.PI / 2 + (Math.PI * 2 * slot) / totalSlots;
        // Parked categories (Cat 8 ML) never compute — axes still render, but
        // they carry no status (grey dot at the near-centre ring).
        const status = (cat.parked || m.active === false) ? null
          : (window.getModuleStatus ? getModuleStatus(m.method_class, project) : null);
        axes.push({ cat, module: m, angle, status });
        slot += 1;
      });
      const endSlot = slot - 1;
      bands.push({
        color: cat.color,
        parked: !!cat.parked,
        num: cat.num,
        a0: -Math.PI / 2 + (Math.PI * 2 * (startSlot - 0.45)) / totalSlots,
        a1: -Math.PI / 2 + (Math.PI * 2 * (endSlot + 0.45)) / totalSlots,
        amid: -Math.PI / 2 + (Math.PI * 2 * ((startSlot + endSlot) / 2)) / totalSlots
      });
    });
    return { axes, bands };
  }

  function bandArcPath(band, radiusFactor) {
    const r = MOD_OUTER * radiusFactor;
    const p0 = { x: MOD_CX + Math.cos(band.a0) * r, y: MOD_CY + Math.sin(band.a0) * r };
    const p1 = { x: MOD_CX + Math.cos(band.a1) * r, y: MOD_CY + Math.sin(band.a1) * r };
    const large = (band.a1 - band.a0) > Math.PI ? 1 : 0;
    return `M ${p0.x.toFixed(1)} ${p0.y.toFixed(1)} A ${r.toFixed(1)} ${r.toFixed(1)} 0 ${large} 1 ${p1.x.toFixed(1)} ${p1.y.toFixed(1)}`;
  }

  function signalWebHtml(project) {
    if (!window.LIN_CATEGORIES) return "";
    if (!window.hasSignals || !hasSignals(project)) return "";

    // Compute the snapshot FIRST. currentSnapshot → buildHistorySnapshot →
    // ensureSimulations runs runAll()/runDST() and populates
    // project.simulationSignals.signal_array. getModuleStatus (called below via
    // buildModuleAxes) reads that array for every non-core module, so it must
    // exist before we build the axes — otherwise only the handful of core EVM /
    // decision signals resolve and the rest fall back to "no data".
    const cur = currentSnapshot(project);
    const overall = cur && cur.governance && cur.governance.state;

    const { axes, bands } = buildModuleAxes(project);

    // Category colour bands behind each cluster (subtle grouping). Parked
    // categories (Cat 8 ML) render a clearly grey band to signal "no compute".
    const bandPaths = bands.map((b) => {
      const cls = b.parked ? "sw-mod-band sw-mod-band-parked" : "sw-mod-band";
      return `<path class="${cls}" d="${bandArcPath(b, 1.04)}" stroke="${esc(b.color)}"></path>`;
    }).join("");

    // Parked-category arc labels (Cat 8 ML*) — the asterisk ties to the footnote.
    const bandLabels = bands.filter((b) => b.parked).map((b) => {
      const lp = modPoint(b.amid, 1.22);
      const anchor = Math.abs(lp.x - MOD_CX) < 10 ? "middle" : (lp.x > MOD_CX ? "start" : "end");
      return `<text class="sw-mod-band-label" x="${lp.x.toFixed(1)}" y="${lp.y.toFixed(1)}" text-anchor="${anchor}">${esc(b.num)} ML*</text>`;
    }).join("");

    // Axis spokes.
    const axisLines = axes.map((a) => {
      const tip = modPoint(a.angle, 1.0);
      const parked = (a.cat.parked || a.module.active === false) ? " sw-axis-parked" : "";
      return `<line class="sw-axis${parked}" x1="${MOD_CX}" y1="${MOD_CY}" x2="${tip.x.toFixed(1)}" y2="${tip.y.toFixed(1)}"></line>`;
    }).join("");

    // Web polygon connecting every module's plotted point.
    const polyPoints = axes.map((a) => {
      const p = modPoint(a.angle, moduleToRadius(a.module, a.status));
      return p.x.toFixed(1) + "," + p.y.toFixed(1);
    }).join(" ");

    // Dots + labels.
    const nodes = axes.map((a) => {
      const parked = a.cat.parked === true;
      const active = !(parked || a.module.active === false);
      const norm = active ? normalizeStatus(a.status) : null;
      const rf = moduleToRadius(a.module, a.status);
      const dp = modPoint(a.angle, rf);
      // Parked (Cat 8) plots a clearly grey dot; active-no-data uses the dim
      // navy ring; computed modules take their status colour.
      const color = parked ? PARKED_GREY : (active ? (DOT_COLOR[norm] || DOT_COLOR.none) : DOT_COLOR.none);
      const dotR = active && norm ? 3.2 : 1.6;
      const lp = modPoint(a.angle, 1.09);
      const anchor = Math.abs(lp.x - MOD_CX) < 10 ? "middle" : (lp.x > MOD_CX ? "start" : "end");
      const ev = active ? moduleEvidence(a.module, project) : null;
      const statusLabel = parked ? "Stage 2 (parked)"
        : a.module.active === false ? "Inactive — needs document data"
        : (norm || "No data");
      const title = a.module.num + " " + a.module.name + " — " + statusLabel +
        (ev ? " — " + ev : "");
      const labelCls = parked ? "sw-mod-label sw-mod-label-parked" : "sw-mod-label";
      return `<line class="sw-mod-spoke" x1="${MOD_CX}" y1="${MOD_CY}" x2="${dp.x.toFixed(1)}" y2="${dp.y.toFixed(1)}" stroke="${esc(color)}"></line>
        <circle class="sw-dot" cx="${dp.x.toFixed(1)}" cy="${dp.y.toFixed(1)}" r="${dotR}" fill="${esc(color)}">
          <title>${esc(title)}</title>
        </circle>
        <text class="${labelCls}" x="${lp.x.toFixed(1)}" y="${lp.y.toFixed(1)}" text-anchor="${anchor}">${esc(a.module.num)}</text>`;
    }).join("");

    const activeCount = axes.filter((a) => a.status && normalizeStatus(a.status)).length;

    return `<section class="panel signal-web-panel">
      <div class="sw-head">
        <div>
          <p class="eyebrow">Signal Web — ${esc(periodTitle(cur && cur.period))}</p>
          <p class="kn-sub sw-vs">89-module view · ${activeCount} computed · Cat 8 ML parked for Stage 2</p>
        </div>
        <div class="sw-legend" aria-label="Signal web legend">
          <span><i class="sw-complete"></i>Complete</span>
          <span><i class="sw-green"></i>Green</span>
          <span><i class="sw-yellow"></i>Yellow</span>
          <span><i class="sw-amber"></i>Amber</span>
          <span><i class="sw-red"></i>Red</span>
          <span><i class="sw-none"></i>No data</span>
        </div>
      </div>
      <svg class="signal-web-svg sw-mod-svg" viewBox="0 0 500 500" role="img" aria-label="89 module signal web">
        <circle class="sw-ring sw-ring-red"   cx="${MOD_CX}" cy="${MOD_CY}" r="${(MOD_OUTER*0.40).toFixed(1)}"></circle>
        <circle class="sw-ring sw-ring-amber" cx="${MOD_CX}" cy="${MOD_CY}" r="${(MOD_OUTER*0.65).toFixed(1)}"></circle>
        <circle class="sw-ring sw-ring-green" cx="${MOD_CX}" cy="${MOD_CY}" r="${(MOD_OUTER*0.85).toFixed(1)}"></circle>
        <circle class="sw-ring sw-ring-outer" cx="${MOD_CX}" cy="${MOD_CY}" r="${MOD_OUTER}"></circle>
        ${bandPaths}
        ${axisLines}
        <polygon class="sw-web-current" points="${polyPoints}"></polygon>
        ${nodes}
        ${bandLabels}
        <circle class="sw-center sw-${statusClass(overall)}" cx="${MOD_CX}" cy="${MOD_CY}" r="5">
          <title>Overall governance state: ${esc(normalizeStatus(overall) || overall || "No data")}</title>
        </circle>
      </svg>
      <p class="sw-footnote">* Cat 8 ML/AI — available in Stage 2</p>
    </section>`;
  }

  /* ============================================================
     Ensemble analysis panel — three views of the 89-module output:
       1) per-module scatter across status columns
       2) ensemble distribution bar (count per status + trend line)
       3) consensus stacked bar (single proportional bar)
     ============================================================ */
  const ENSEMBLE_STATES = ["Complete", "Green", "Yellow", "Amber", "Red"];

  function ensembleTally(project) {
    const counts = { Complete: 0, Green: 0, Yellow: 0, Amber: 0, Red: 0, none: 0 };
    const rows = [];
    let idx = 0;
    LIN_CATEGORIES.forEach((cat) => {
      cat.modules.forEach((m) => {
        idx += 1;
        const active = !(cat.parked || m.active === false);
        const status = active && window.getModuleStatus ? getModuleStatus(m.method_class, project) : null;
        const norm = active ? normalizeStatus(status) : null;
        const bucket = norm && counts[norm] != null ? norm : "none";
        counts[bucket] += 1;
        rows.push({ index: idx, num: m.num, name: m.name, color: cat.color, bucket });
      });
    });
    return { counts, rows };
  }

  function ensembleHtml(project) {
    if (!window.LIN_CATEGORIES) return "";
    if (!window.hasSignals || !hasSignals(project)) return "";
    const { counts, rows } = ensembleTally(project);
    const activeTotal = ENSEMBLE_STATES.reduce((n, k) => n + counts[k], 0);
    if (!activeTotal) return ""; // nothing computed yet

    // All charts draw in numeric user-units inside a 0..100 wide viewBox with
    // preserveAspectRatio="none", so x can stretch to the panel width.

    // SVG charts use uniform scaling so dots stay circular and text is not
    // stretched. The consensus bar is plain HTML (text never distorts).

    // ---- Chart 1: scatter (6 columns incl. No data, 89 rows) ----
    const cols = ENSEMBLE_STATES.concat(["none"]);
    const colLabel = { Complete: "Complete", Green: "Green", Yellow: "Yellow", Amber: "Amber", Red: "Red", none: "No data" };
    const SW = 120, SH = 150;
    const colW = SW / cols.length;
    const scatterDots = rows.map((r) => {
      const ci = cols.indexOf(r.bucket);
      const cx = (ci + 0.5) * colW;
      const cy = 16 + (r.index / 89) * (SH - 22);
      const fill = r.bucket === "none" ? DOT_COLOR.none : DOT_COLOR[r.bucket];
      const rad = r.bucket === "none" ? 1.3 : 2.1;
      return `<circle cx="${cx.toFixed(2)}" cy="${cy.toFixed(2)}" r="${rad}" fill="${esc(fill)}"><title>${esc(r.num + " " + r.name + " — " + colLabel[r.bucket])}</title></circle>`;
    }).join("");
    const scatterGrid = cols.map((c, i) =>
      (i ? `<line class="ens-col-line" x1="${(i * colW).toFixed(2)}" y1="14" x2="${(i * colW).toFixed(2)}" y2="${SH}"></line>` : "") +
      `<text x="${((i + 0.5) * colW).toFixed(2)}" y="9" text-anchor="middle" class="ens-col-label">${esc(colLabel[c])}</text>`
    ).join("");

    // ---- Chart 2: distribution bar ----
    const maxCount = Math.max(1, ...ENSEMBLE_STATES.map((k) => counts[k]));
    const BW = 120, BH = 150, barTop = 22, barBottom = 122;
    const bW = BW / ENSEMBLE_STATES.length;
    const barBody = ENSEMBLE_STATES.map((k, i) => {
      const h = (counts[k] / maxCount) * (barBottom - barTop);
      const x = i * bW, y = barBottom - h;
      const pct = activeTotal ? Math.round((counts[k] / activeTotal) * 100) : 0;
      return `<rect x="${(x + bW * 0.18).toFixed(2)}" y="${y.toFixed(1)}" width="${(bW * 0.64).toFixed(2)}" height="${h.toFixed(1)}" fill="${esc(DOT_COLOR[k])}" rx="1.5"></rect>
        <text x="${(x + bW * 0.5).toFixed(2)}" y="${(y - 4).toFixed(1)}" text-anchor="middle" class="ens-bar-count">${counts[k]} · ${pct}%</text>
        <text x="${(x + bW * 0.5).toFixed(2)}" y="${barBottom + 14}" text-anchor="middle" class="ens-col-label">${esc(k)}</text>`;
    }).join("");
    const trendPts = ENSEMBLE_STATES.map((k, i) => {
      const h = (counts[k] / maxCount) * (barBottom - barTop);
      return `${(i * bW + bW * 0.5).toFixed(2)},${(barBottom - h).toFixed(1)}`;
    });
    const trendLine = `<polyline class="ens-trend" points="${trendPts.join(" ")}"></polyline>`;

    // ---- Chart 3: consensus stacked bar (HTML) ----
    const segs = ENSEMBLE_STATES.map((k) => {
      const w = (counts[k] / activeTotal) * 100;
      if (w <= 0) return "";
      const pct = Math.round(w);
      return `<div class="ens-seg" style="width:${w.toFixed(2)}%;background:${esc(DOT_COLOR[k])}" title="${esc(k)}: ${counts[k]} (${pct}%)">${w >= 8 ? pct + "%" : ""}</div>`;
    }).join("");
    const legend = ENSEMBLE_STATES.map((k) =>
      `<span class="ens-leg"><i style="background:${esc(DOT_COLOR[k])}"></i>${esc(k)}: ${counts[k]} (${Math.round((counts[k] / activeTotal) * 100)}%)</span>`
    ).join("");

    return `<section class="panel ens-panel" aria-label="Ensemble analysis">
      <div class="sw-head">
        <div>
          <p class="eyebrow">Ensemble analysis — ${activeTotal} active models</p>
          <p class="kn-sub sw-vs">Individual model outputs · distribution · consensus</p>
        </div>
      </div>

      <div class="ens-grid">
        <div class="ens-chart">
          <p class="ens-chart-title">Individual model outputs</p>
          <svg class="ens-scatter" viewBox="0 0 ${SW} ${SH}" role="img" aria-label="Per-module status scatter">
            ${scatterGrid}
            ${scatterDots}
          </svg>
        </div>

        <div class="ens-chart">
          <p class="ens-chart-title">Ensemble distribution</p>
          <svg class="ens-bars" viewBox="0 0 ${BW} ${BH}" role="img" aria-label="Ensemble distribution bars">
            ${barBody}
            ${trendLine}
          </svg>
        </div>
      </div>

      <div class="ens-consensus">
        <p class="ens-chart-title">Consensus</p>
        <div class="ens-stack">${segs}</div>
        <div class="ens-legend">${legend}</div>
      </div>
    </section>`;
  }

  /* ============================================================
     Uploaded Documents — one row per `signals_extracted` event on
     the project. Reuses LinSignals.DOC_TYPE_LABEL for friendly type
     names and the selected LinTZ zone for the upload timestamp.
     ============================================================ */
  function uploadedDocEvents(project) {
    const evs = (project && Array.isArray(project.events)) ? project.events : [];
    return evs.filter((e) => {
      const t = (e && (e.type || e.event || e.kind)) || "";
      return t === "signals_extracted";
    });
  }
  function fmtDocType(dt) {
    if (!dt) return "Document";
    const map = (window.LinSignals && LinSignals.DOC_TYPE_LABEL) || {};
    if (map[dt]) return map[dt];
    // generic snake_case → Title Case fallback for unmapped types
    return String(dt).replace(/[_-]+/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  }
  // "Jun 16, 2026 14:32 EDT" in the user's selected timezone.
  function fmtUploadTime(iso) {
    const d = iso instanceof Date ? iso : new Date(iso);
    if (!iso || isNaN(d)) return "—";
    const zone = (window.LinTZ && LinTZ.get && LinTZ.get()) || "America/New_York";
    try {
      const parts = new Intl.DateTimeFormat("en-US", {
        timeZone: zone, hour12: false,
        month: "short", day: "numeric", year: "numeric",
        hour: "2-digit", minute: "2-digit", timeZoneName: "short"
      }).formatToParts(d);
      const g = (t) => { const x = parts.find((pp) => pp.type === t); return x ? x.value : ""; };
      return `${g("month")} ${g("day")}, ${g("year")} ${g("hour")}:${g("minute")} ${g("timeZoneName")}`;
    } catch (e) { return window.LinTZ ? LinTZ.format(d) : d.toISOString(); }
  }
  function uploadedDocFields(e) {
    const src = e.applied != null ? e.applied : (e.fields != null ? e.fields : e.field);
    if (Array.isArray(src)) return src.filter(Boolean);
    if (src == null || src === "") return [];
    return [src];
  }
  // Partial when the extraction recorded missing fields (or applied none).
  function uploadedDocIsPartial(e, fields) {
    const missing = e.missing != null ? e.missing : e.missingFields;
    if (Array.isArray(missing) && missing.length) return true;
    if (e.partial === true || e.readyToRun === false) return true;
    return (fields || []).length === 0;
  }
  function uploadedDocsPanelHtml(project) {
    const evs = uploadedDocEvents(project).slice().reverse(); // newest first
    const rows = evs.map((e) => {
      const fields = uploadedDocFields(e);
      const partial = uploadedDocIsPartial(e, fields);
      const fileName = e.fileName || e.file || e.name || "—";
      const at = e.at || e.timestamp || e.recordedAt || e.time || "";
      const fieldList = fields.length ? fields.join(", ") : "—";
      const pill = partial
        ? `<span class="pill pill-amber up-pill" title="Some expected fields were missing">partial</span>`
        : `<span class="pill pill-green up-pill" title="All expected fields extracted">✓</span>`;
      return `<tr class="up-row">
          <td class="up-type">${esc(fmtDocType(e.docType))}</td>
          <td class="up-file">${esc(fileName)}</td>
          <td class="up-time">${esc(fmtUploadTime(at))}</td>
          <td class="up-fields">${esc(fieldList)}</td>
          <td class="up-status">${pill}</td>
        </tr>`;
    }).join("");
    const body = evs.length
      ? `<table class="up-table"><thead><tr>
           <th>Type</th><th>File</th><th>Uploaded</th><th>Fields extracted</th><th aria-label="Status"></th>
         </tr></thead><tbody>${rows}</tbody></table>`
      : `<p class="kn-sub up-empty">No documents uploaded. Use the Upload panel to add project documents.</p>`;
    return `<section class="panel detail-uploads" aria-label="Uploaded documents">
        <p class="eyebrow">Uploaded Documents — ${evs.length} ${evs.length === 1 ? "document" : "documents"}</p>
        ${body}
      </section>`;
  }
  // Compact "what's already on file" note for the ingest panel, so the PM can
  // see existing documents before uploading again.
  function ingestUploadedNoteHtml(project) {
    const evs = uploadedDocEvents(project);
    if (!evs.length) return "";
    const seen = {};
    const items = [];
    evs.slice().reverse().forEach((e) => {
      const fn = e.fileName || e.file || e.name || "";
      const key = (e.docType || "") + "|" + fn;
      if (seen[key]) return;
      seen[key] = true;
      items.push(esc(fmtDocType(e.docType)) + (fn ? ` <span class="up-note-file">(${esc(fn)})</span>` : ""));
    });
    return `<p class="kn-sub up-note"><strong>Already uploaded (${items.length}):</strong> ${items.join(" · ")}</p>`;
  }

  function render(id) {
    const root = document.getElementById("detail-root");
    if (!root) return;
    const p = (window.LinStore ? LinStore.getCached(id) : null) ||
              LIN_PROJECTS.find((x) => x.id === id);
    if (!p) {
      root.innerHTML = `<p class="pr-empty">Project not found (it may have been archived). <button class="btn small" data-back>Back to Portfolio</button></p>`;
      wireBack(root);
      return;
    }

    const populated = hasSignals(p);
    const state = populated
      ? (typeof deriveHealthStateLabel === "function" ? deriveHealthStateLabel(p) : deriveHealthState(p))
      : "Awaiting ingest";
    const stateKey = populated ? String(state).toLowerCase().replace("-review", "") : "empty";

    root.innerHTML =
      `<div class="detail-head">
         <button class="btn detail-back" data-back>← Back to Portfolio</button>
         <div class="detail-id">
           <p class="eyebrow">Project detail</p>
           <h1><span class="mod-mono">${esc(p.id)}</span> ${esc(p.name)}</h1>
           <p class="detail-meta">
             Sector: <strong>${esc(SECTOR_LABEL[p.sector] || p.sector)}</strong> ·
             Reporting period: <span class="mod-mono">${esc(p.reportingPeriod)}</span> ·
             State: <span class="li-state state-${stateKey}">${esc(state)}</span>
           </p>
         </div>
         <div class="detail-head-actions">
           <button class="btn small detail-reset" data-reset="${esc(p.id)}">Reset signals</button>
           <span class="detail-reset-msg kn-sub" aria-live="polite"></span>
         </div>
       </div>
        ${executiveBriefHtml(p)}
        ${signalWebHtml(p)}
        ${ensembleHtml(p)}
        ${uploadedDocsPanelHtml(p)}
        <div class="detail-grid">
         <section class="panel detail-ledger" aria-label="Signal ledger (project detail)"></section>
         <section class="panel detail-decision" aria-label="PCEIF governance decision (project detail)"></section>
       </div>
       <section class="panel detail-ingest" aria-label="Ingest to this project">
         <details class="kn-topic"${populated ? "" : " open"}>
           <summary>Ingest to this project (${esc(p.id)}) — populate signals / document-risk</summary>
           <p class="kn-sub" style="margin-top:8px">Pre-scoped to this project. Populate runs the real Monte Carlo + CUSUM; document-risk uses the transparent keyword rules with mandatory Approve/Reject.</p>
           ${ingestUploadedNoteHtml(p)}
           <div class="detail-ingest-form"></div>
         </details>
       </section>
       <h2 class="detail-mods-h">Signal stack — 10 models — computed for ${esc(p.id)}</h2>
       <div class="detail-modules"></div>
       <section class="panel detail-signals" aria-label="Extracted signals detail"></section>`;

    // Reuse the shared renderers, scoped to this page's containers.
    LinApp.renderLedger(p, root.querySelector(".detail-ledger"));
    LinApp.renderDecisionCard(p, root.querySelector(".detail-decision"));
    // Pre-scoped ingest — same shared logic and event log as Manage Projects.
    LinIngest.renderScopedIngest(p.id, root.querySelector(".detail-ingest-form"),
      (id) => render(id)); // on approve: re-render detail so ledger/deep dive reflect the delta
    // HUD-depth per-project deep dive (chart + why-grid + reasoning + rule)
    LinDeepDive.render(p, root.querySelector(".detail-modules"));
    // Signals detail panel (extracted values, missing docs, audit trail) — sits
    // under the simulated charts; collapsed by default behind a "Details" toggle.
    if (window.LinSignals) LinSignals.renderSignalsPanel(root.querySelector(".detail-signals"), p);

    wireBack(root);
    wireReset(root);
    wireSignalWeb(root, id);
    wireBrief(root, p);
    // Kick off the brief AFTER the spider chart + evidence backfill have run,
    // so the prompt sees a fully-populated simulationSignals array. Cached
    // briefs for the current reporting period render without a chat call.
    refreshBrief(root, p);
  }

  /* ============================================================
     Executive brief — Lin-generated 4-6 sentence summary of the
     full 19-module signal package, written for a PM / program
     director. Cached per reporting period on project.executiveBrief
     and persisted via LinStore.saveProject so a reload renders the
     same brief without re-calling the chat endpoint.
     ============================================================ */

  function briefCurrentPeriod(project) {
    let snap = null;
    try { snap = currentSnapshot(project); } catch (e) { /* snapshot may throw on partial signals */ }
    return (snap && snap.period) || (project && project.reportingPeriod) || null;
  }

  function briefForPeriod(project, period) {
    const b = project && project.executiveBrief;
    if (!b || !b.text) return null;
    if (period && b.period && b.period !== period) return null;
    return b;
  }

  // Resolve the governance state from every shape we've seen on the wire:
  // decision.state (PCEIF), decision.healthState (raw deriveDecision output),
  // decision.derivedState (legacy backend field), project.status (top-level
  // override). Falls back to deriveHealthState(project) if decision.js is
  // available and signals are populated. Returns null if no state can be
  // resolved — callers should never assume a default.
  function resolveBriefState(project) {
    const s = (project && project.signals) || {};
    const d = s.decision || {};
    const raw = d.state || d.healthState || d.derivedState || (project && project.status) || null;
    if (raw) return String(raw);
    try {
      if (typeof deriveHealthState === "function" && s.evm && s.mc && s.cusum && s.doc) {
        return deriveHealthState(project);
      }
    } catch (e) { /* defensive */ }
    return null;
  }

  function briefSignalsDigest(project) {
    const s = (project && project.signals) || {};
    const bits = [];
    if (s.evm) {
      const cpi = Number(s.evm.cpi);
      const spi = Number(s.evm.spi);
      if (Number.isFinite(cpi)) bits.push("cost " + (cpi >= 0.95 ? "on budget" : cpi >= 0.90 ? "slightly over" : "over budget"));
      if (Number.isFinite(spi)) bits.push("schedule " + (spi >= 0.95 ? "on plan" : spi >= 0.90 ? "slightly behind" : "behind"));
    }
    if (s.cusum) bits.push(s.cusum.breached ? "sustained schedule drift" : "no drift");
    if (s.doc) {
      const score = Number(s.doc.score);
      if (Number.isFinite(score)) bits.push("documents " + (score < 0.20 ? "clean" : score < 0.40 ? "minor risk" : score < 0.70 ? "elevated risk" : "high risk"));
    }
    const state = resolveBriefState(project);
    if (state) bits.push("overall state " + state);
    return bits.join(", ");
  }

  /* Pick the snapshot the brief reads from. Builds a category snapshot on
     the fly when LinSignals is available and the project has signals — the
     stored history may not include the new category fields yet on legacy
     projects. Returns null when there is nothing to brief on. */
  function briefSnapshot(project) {
    if (!project) return null;
    const history = Array.isArray(project.history) ? project.history : [];
    let snap = history.length ? history[history.length - 1] : null;
    if (snap && snap.categories) return snap;
    if (window.LinSignals && typeof LinSignals.buildCategorySnapshot === "function") {
      try {
        const fresh = LinSignals.buildCategorySnapshot(project);
        if (fresh && fresh.categories) return fresh;
      } catch (e) { /* defensive */ }
    }
    return null;
  }

  function buildBriefPrompt(project) {
    const snapshot = briefSnapshot(project);
    if (!snapshot || !snapshot.categories) {
      console.log("[brief] no stored category snapshot for " + (project && project.id) + " — skipping chat");
      return null;
    }

    const cats = Object.keys(snapshot.categories).map((k) => snapshot.categories[k]);
    const catSummary = cats
      .filter((c) => !c.parked && c.status)
      .map((c) => {
        const order = { Red: 0, "Red-review": 1, Amber: 2, Yellow: 3, Green: 4, Complete: 5 };
        const worst = (c.modules || [])
          .filter((m) => m.status)
          .slice()
          .sort((a, b) => (order[a.status] != null ? order[a.status] : 3) - (order[b.status] != null ? order[b.status] : 3))[0];
        const worstDesc = worst ? " (worst: " + worst.name + (worst.evidence_metric ? " — " + worst.evidence_metric : "") + ")" : "";
        return c.num + " " + c.name + ": " + c.status + worstDesc;
      }).join("\n");

    const conf = snapshot.summary && snapshot.summary.evidence_agreement;
    const confText = conf
      ? conf.confidence + " confidence (" + conf.methods_agreeing + " of " + conf.methods_checked + " evidence methods agree)"
      : "agreement not computed";
    const gov = snapshot.governance || {};
    const computedDay = (snapshot.computed_at || "").substring(0, 10) || "unknown date";
    const totalModules = (snapshot.summary && snapshot.summary.total_modules) || 0;

    console.log("[brief] using stored category snapshot for " + project.id + " (period " + snapshot.period + ", " + totalModules + " modules across " + cats.filter((c) => !c.parked).length + " categories)");

    return "You are briefing a senior program director before a governance meeting. " +
      "Write a 4-6 sentence executive brief about " +
      (snapshot.project_name || project.name) + " (Project " + snapshot.project_id + ", " + (snapshot.sector || "unknown") + " sector).\n\n" +
      "This brief is based on a stored computational log from " + computedDay + ". " +
      "The platform computed " + totalModules + " signal modules across 9 analytical categories. " +
      "No human reviewer could complete this analysis in real time.\n\n" +
      "Category results:\n" + catSummary +
      "\n\nOverall governance: " + (gov.state || "unknown") +
      "\nAuthority: " + (gov.authority || "unknown") +
      "\nRecommended action: " + (gov.action || "unknown") +
      "\nEvidence agreement: " + confText +
      "\n\nBrief requirements:\n" +
      "1. First sentence: overall project health in plain English\n" +
      "2. Second/third sentence: the one or two most critical category concerns\n" +
      "3. Fourth sentence: recommended action and who takes it\n" +
      "4. Fifth sentence: confidence level — do the evidence methods agree?\n" +
      "5. No module numbers, no metric values, no jargon\n" +
      "6. Use: on track / early warning / significant risk / critical failure\n" +
      "7. Speak directly to the program director\n" +
      "Start immediately with the project status.";
  }

  // Scripted fallback when the chat endpoint fails. Same pattern as Ask Lin's
  // catch block in assistant.js — show something useful instead of an error.
  // Only mentions signals that are actually present and accurate; the action
  // is keyed to the concerns themselves so it can never contradict them
  // (the previous version produced "Routine monitoring is appropriate" next
  // to "sustained drift detected").
  function scriptedBrief(project) {
    const s = (project && project.signals) || {};
    const d = s.decision || {};
    const conflict = d.conflict || "";
    const authority = d.authority || "the project manager";

    const concerns = [];
    if (s.evm) {
      const cpi = Number(s.evm.cpi);
      if (Number.isFinite(cpi)) {
        if (cpi < 0.90) concerns.push("cost is over budget");
        else if (cpi < 0.95) concerns.push("cost is slightly over budget");
      }
      const spi = Number(s.evm.spi);
      if (Number.isFinite(spi)) {
        if (spi < 0.90) concerns.push("the schedule is behind");
        else if (spi < 0.95) concerns.push("the schedule is slipping");
      }
    }
    if (s.cusum && s.cusum.breached) concerns.push("the trend monitor has detected sustained drift");
    if (s.doc) {
      const ds = Number(s.doc.score);
      if (Number.isFinite(ds) && ds >= 0.70) concerns.push("document risk is high");
      else if (Number.isFinite(ds) && ds >= 0.40) concerns.push("document risk is elevated");
    }

    // Resolve state. If decision.js doesn't tell us, infer from the concerns
    // so the lead line never reads "in an unknown state" when there are real
    // concerns on the package.
    let state = resolveBriefState(project);
    if (!state) {
      if (concerns.length >= 2) state = "Red-review";
      else if (concerns.length === 1) state = "Amber";
      else state = "Green";
    }

    const stateWord = state === "Red-review" || state === "Red" ? "in the red zone — critical failure"
                    : state === "Amber"   ? "in the amber zone — significant risk"
                    : state === "Yellow"  ? "showing early warning signs"
                    : state === "Complete" ? "showing the milestone as achieved"
                    : state === "Green"   ? "on track"
                    : "in an unsettled state";
    const lead = "Project " + project.id + " is " + stateWord + ".";

    const concernLine = concerns.length
      ? "The most pressing concerns are that " + concerns.slice(0, 2).join(" and ") + "."
      : "No single concern dominates the signal package.";

    // Action picks its branch from the CONCERNS as well as the state, so it
    // can never read "Routine monitoring" while concerns are listed.
    let action;
    const hasCritical = concerns.some((c) => c.indexOf("over budget") >= 0 || c.indexOf("schedule is behind") >= 0 || c.indexOf("sustained drift") >= 0 || c.indexOf("high") >= 0);
    if (state === "Red-review" || state === "Red" || (hasCritical && concerns.length >= 2)) {
      action = "The recommendation is for " + authority + " to convene a recovery review within 48 hours.";
    } else if (state === "Amber" || hasCritical) {
      action = "The recommendation is for " + authority + " to open a weekly review loop and tighten the recovery plan.";
    } else if (state === "Yellow" || concerns.length === 1) {
      action = "The recommendation is for the project manager to schedule a weekly check-in and investigate the early-warning variance before the next cycle.";
    } else if (state === "Complete") {
      action = "The recommendation is to begin closeout documentation.";
    } else {
      action = "Routine monthly monitoring is appropriate this cycle.";
    }

    const conflictLine = conflict
      ? "The evidence methods classify this as " + conflict.toLowerCase() + "."
      : "The evidence methods broadly agree on the assessment.";

    return [lead, concernLine, action, conflictLine].join(" ");
  }

  function briefAccentClass(project) {
    let snap = null;
    try { snap = currentSnapshot(project); } catch (e) {}
    const overall = snap && snap.governance && snap.governance.state;
    const cls = String(overall || "").toLowerCase().replace("-review", "");
    return cls || "none";
  }

  function briefFooter(brief) {
    if (!brief) return "";
    const snap = brief.snapshot || null;
    const computedAt = (snap && snap.computed_at) || brief.generated_at || null;
    if (!computedAt) return "";
    let when = computedAt.substring(0, 10);
    try {
      const d = new Date(computedAt);
      when = d.toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric" });
    } catch (e) {}
    const total = (snap && snap.summary && snap.summary.total_modules) || null;
    const conf = snap && snap.summary && snap.summary.evidence_agreement && snap.summary.evidence_agreement.confidence;
    const parts = ["Generated from stored log", when];
    if (total) parts.push(total + " modules");
    if (conf) parts.push(conf + " confidence");
    return `<div class="eb-foot">${esc(parts.join(" · "))}</div>`;
  }

  function briefBodyHtml(state, brief, errMsg) {
    if (state === "loading") {
      return `<div class="eb-body eb-loading" aria-live="polite">
        <span class="eb-shimmer"></span>
        <span class="eb-status">Analysing 19 signal modules…</span>
      </div>`;
    }
    if (state === "skipped") {
      return `<div class="eb-body eb-skipped">Upload project documents to generate the stored log. The executive brief is generated from that log — not from recomputed signals.</div>`;
    }
    if (state === "error") {
      return `<div class="eb-body eb-error" role="alert">Brief unavailable: ${esc(errMsg || "unknown error")}</div>`;
    }
    return `<div class="eb-body">${esc(brief && brief.text ? brief.text : "")}</div>`;
  }

  function executiveBriefHtml(project) {
    // Every helper is wrapped — the card must ALWAYS render so the user
    // sees the loading shimmer (or the cached brief) regardless of whether
    // the signal snapshot is computable yet. A throw here would otherwise
    // take down the whole detail-page template-literal assembly.
    let period = null, cached = null, accent = "none", projectId = "";
    try { period = briefCurrentPeriod(project); } catch (e) {}
    try { cached = briefForPeriod(project, period); } catch (e) {}
    try { accent = briefAccentClass(project); } catch (e) {}
    try { projectId = (project && project.id) || ""; } catch (e) {}
    const state = cached ? "ready" : "loading";
    return `<section class="panel eb-panel eb-accent-${esc(accent)}" aria-label="Executive brief" data-eb-id="${esc(projectId)}">
      <div class="eb-head">
        <div>
          <p class="eyebrow eb-eyebrow">Executive brief</p>
          <p class="kn-sub eb-sub">Generated from 19-module signal analysis</p>
        </div>
        <button type="button" class="btn small eb-regen" data-eb-regen="${esc(projectId)}" aria-label="Regenerate brief">Regenerate ↺</button>
      </div>
      ${briefBodyHtml(state, cached)}
      ${cached ? briefFooter(cached) : ""}
    </section>`;
  }

  function setBriefState(root, state, project, brief, errMsg) {
    const panel = root.querySelector(".eb-panel");
    if (!panel) return;
    const old = panel.querySelector(".eb-body");
    if (old) old.remove();
    const oldFoot = panel.querySelector(".eb-foot");
    if (oldFoot) oldFoot.remove();
    panel.insertAdjacentHTML("beforeend", briefBodyHtml(state, brief, errMsg));
    if (state === "ready" && brief) panel.insertAdjacentHTML("beforeend", briefFooter(brief));
    if (project) {
      const accent = briefAccentClass(project);
      panel.className = panel.className.replace(/\beb-accent-\S+/g, "").trim() + " eb-accent-" + accent;
    }
  }

  async function refreshBrief(root, project, opts) {
    if (!project || !window.LinStore || typeof LinStore.chat !== "function") {
      console.error("[brief] LinStore.chat unavailable");
      setBriefState(root, "error", project, null, "chat endpoint unavailable");
      return;
    }
    const force = !!(opts && opts.force);
    const period = briefCurrentPeriod(project);
    const cached = briefForPeriod(project, period);
    if (cached && !force) {
      setBriefState(root, "ready", project, cached);
      return;
    }
    // Guard: a project with no signals at all has nothing meaningful to brief
    // on. Show the explicit "no signals" state instead of burning a chat call
    // (the backend prompt would be all-empty signal lines).
    const prompt = buildBriefPrompt(project);
    if (prompt == null) {
      console.log("[brief] skipped " + project.id + " — no signals to brief on");
      setBriefState(root, "skipped", project, null);
      return;
    }
    setBriefState(root, "loading", project, null);
    console.log("[brief] calling chat for project", project.id);
    console.log("[brief] prompt =", prompt);
    try {
      // 15s timeout — if the chat hangs the user gets an actionable error +
      // a working Regenerate button instead of a spinning shimmer forever.
      const TIMEOUT_MS = 15000;
      const chatP = LinStore.chat(prompt, project.id);
      const timeoutP = new Promise((_, reject) =>
        setTimeout(() => reject(new Error("chat timed out after 15s")), TIMEOUT_MS));
      const answer = await Promise.race([chatP, timeoutP]);
      console.log("[brief] chat response for " + project.id + ":", answer);
      const text = String(answer || "").trim();
      if (!text) throw new Error("empty brief returned");
      const snap = briefSnapshot(project);
      const brief = { text, generated_at: new Date().toISOString(), period, snapshot: snap };
      project.executiveBrief = brief;
      setBriefState(root, "ready", project, brief);
      // Persist — non-blocking. Save failure leaves the brief in memory so
      // the user still sees it this session; next reload will refetch.
      if (LinStore.saveProject) {
        LinStore.saveProject(project).catch((err) => {
          console.error("[brief] saveProject failed (non-fatal):", err);
        });
      }
    } catch (err) {
      console.error("[brief] chat error for " + project.id + ":", err);
      // Match Ask Lin's pattern: if the live AI endpoint fails, fall back to
      // a scripted brief built from the same project data we already have in
      // memory. The user gets useful text instead of an error string, and the
      // Regenerate button still lets them retry the live call.
      try {
        const text = scriptedBrief(project);
        const snap = briefSnapshot(project);
        const brief = { text, generated_at: new Date().toISOString(), period, source: "scripted", snapshot: snap };
        project.executiveBrief = brief;
        setBriefState(root, "ready", project, brief);
      } catch (e2) {
        const msg = (err && err.message) ? err.message : "unknown error";
        setBriefState(root, "error", project, null, msg);
      }
    }
  }

  function wireBrief(root, project) {
    root.querySelectorAll("[data-eb-regen]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const period = briefCurrentPeriod(project);
        // Force regeneration: drop the cached entry for this period.
        if (project.executiveBrief && (!project.executiveBrief.period || project.executiveBrief.period === period)) {
          project.executiveBrief = null;
        }
        refreshBrief(root, project, { force: true });
      });
    });
  }

  function wireBack(root) {
    root.querySelectorAll("[data-back]").forEach((b) =>
      b.addEventListener("click", () => LinApp.showPage("portfolio")));
  }

  // Reset signals: POST resetsignals, clear local signal state, re-render the
  // detail page (which then shows "awaiting ingest"). No confirmation dialog.
  function wireReset(root) {
    const btn = root.querySelector(".detail-reset");
    if (!btn) return;
    const msg = root.querySelector(".detail-reset-msg");
    btn.addEventListener("click", async () => {
      const id = btn.dataset.reset;
      btn.disabled = true;
      if (msg) msg.textContent = "Resetting…";
      try {
        await LinStore.resetSignals(id);
        // clear local model state so the page reflects the cleared project
        const cached = LinStore.getCached(id);
        if (cached) { delete cached.signals; delete cached.signalInputs; delete cached.simulationSignals; }
        try {
          const fresh = await LinStore.getProject(id);
          if (fresh && window.LIN_PROJECTS) {
            const i = LIN_PROJECTS.findIndex((x) => x.id === id);
            if (i >= 0) LIN_PROJECTS[i] = fresh;
          }
        } catch (e) { /* keep the cleared cached copy on fetch failure */ }
        if (window.LinApp) LinApp.refresh();
        render(id); // re-render → awaiting ingest
      } catch (e) {
        btn.disabled = false;
        if (msg) msg.textContent = "Reset failed — store unreachable. Retry.";
      }
    });
  }

  function wireSignalWeb(root, projectId) {
    root.querySelectorAll("[data-history-period]").forEach((btn) =>
      btn.addEventListener("click", () => {
        selectedHistoryPeriod[projectId] = btn.dataset.historyPeriod;
        render(projectId);
      }));
  }

  window.LinDetail = { render };
})();
