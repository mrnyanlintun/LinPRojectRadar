/* ============================================================
   Lin Project Radar — detail.js
   Project Detail drill-down: one project's identity, signal
   ledger, PCEIF decision card (fairness gate where applicable),
   and all five modules computed for that project.
   Reuses LinApp's ledger/decision-card renderers with no
   duplicated rules; the standalone Signals page was retired.
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
     103-axis module spider web. One axis per defined module across
     all 11 categories. Active modules plot at a status radius
     (healthy = near the rim); inactive / parked /
     no-data modules sit on a tiny grey ring just off-centre.
     Category clusters are separated by a small angular gap and
     backed by a faint arc in the category colour.
     ============================================================ */
  const MOD_CX = 250, MOD_CY = 250, MOD_OUTER = 200;
  const PARKED_GREY = "#64748b"; // Cat 8 (ML/AI) parked-status grey
  // Central palette (radar.css --status-* via config.js). Canvas/SVG dots.
  const SC = window.LIN_STATUS_COLORS;
  const DOT_COLOR = {
    Complete: SC.Complete, Green: SC.Green, Yellow: SC.Yellow,
    Amber: SC.Amber, Red: SC.Red, none: SC.None
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

  // Flatten the 103 modules into axis entries with angles, leaving a one-slot
  // gap between categories so the clusters read as distinct petals.
  function buildModuleAxes(project) {
    const cats = LIN_CATEGORIES;
    const moduleCount = cats.reduce((n, c) => n + c.modules.length, 0);
    // One padding gap before EVERY cluster — including the first, which seats a
    // gap at the top (12 o'clock). Without it the last category's label and
    // the first Cat 1 label collide where the ring wraps.
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
        // Parked categories never compute; inactive modules need document data.
        // Everything else (incl. active Cat 8 ML) resolves via getModuleStatus.
        const status = (cat.parked || m.active === false) ? null
          : (window.getModuleStatus ? getModuleStatus(m.method_class, project) : null);
        axes.push({ cat, module: m, angle, status });
        slot += 1;
      });
      const endSlot = slot - 1;
      bands.push({
        color: cat.color,
        parked: !!cat.parked,
        conditional: !!cat.conditional,
        ml: cat.id === "cat8", // ML category keeps a labelled grey arc band
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
    const cur = currentSnapshot(project);
    const simArr = (project.simulationSignals && project.simulationSignals.signal_array) || [];
    const totalModules = LIN_CATEGORIES.reduce((n, c) => n + c.modules.length, 0);
    const activeCount = simArr.filter((r) => r && r.status_color && normalizeStatus(r.status_color)).length;
    const counts = { Red: 0, Amber: 0, Yellow: 0, Green: 0, Complete: 0 };
    simArr.forEach((r) => {
      if (r && r.status_color) { const n = normalizeStatus(r.status_color); if (n && counts[n] != null) counts[n]++; }
    });
    return `<section class="panel signal-web-panel sphere3d-panel">
      <div class="sw-head">
        <div>
          <p class="eyebrow">Signal Sphere — ${esc(periodTitle(cur && cur.period))}</p>
          <p class="kn-sub sw-vs">${totalModules}-module sphere · ${activeCount} active · drag to rotate · scroll to zoom</p>
        </div>
        <div class="sw-legend" aria-label="Signal sphere legend">
          <span><i class="sw-complete"></i>Complete</span>
          <span><i class="sw-green"></i>Green</span>
          <span><i class="sw-yellow"></i>Yellow</span>
          <span><i class="sw-amber"></i>Amber</span>
          <span><i class="sw-red"></i>Red</span>
          <span><i class="sw-none"></i>No data</span>
        </div>
      </div>
      <div class="chart3d-controls">
        <button class="chart3d-btn active" data-sphere-view="free">Free rotate</button>
        <button class="chart3d-btn" data-sphere-view="top">Top</button>
        <button class="chart3d-btn" data-sphere-view="cost">Cost cluster</button>
        <button class="chart3d-btn" data-sphere-view="evidence">Evidence cluster</button>
        <button class="chart3d-btn" data-sphere-view="gov">Governance</button>
      </div>
      <div class="chart3d-wrap">
        <canvas class="sphere3d-canvas"></canvas>
        <div class="chart3d-tooltip" style="display:none;position:absolute;pointer-events:none;z-index:10;background:var(--surface-2,#131d33);border:1px solid var(--line,#26344f);border-radius:8px;padding:8px 12px;font-size:11px;white-space:nowrap"></div>
      </div>
      <p class="sw-footnote">${totalModules} modules · ${counts.Red} Red · ${counts.Amber} Amber · ${counts.Green} Green</p>
    </section>`;
  }

  /* ============================================================
     Ensemble analysis panel — three views of the 103-module output:
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
    const { counts } = ensembleTally(project);
    const activeTotal = ["Complete","Green","Yellow","Amber","Red"].reduce((n, k) => n + counts[k], 0);
    if (!activeTotal) return "";
    const totalModules = LIN_CATEGORIES.reduce((n, c) => n + c.modules.length, 0);
    return `<section class="panel ens-panel scatter3d-panel" aria-label="Ensemble analysis">
      <div class="sw-head">
        <div>
          <p class="eyebrow">Ensemble Scatter — ${activeTotal} active modules (${totalModules} total)</p>
          <p class="kn-sub sw-vs">${totalModules} modules in 3D · X = category · Y = status severity · drag to rotate</p>
        </div>
      </div>
      <div class="chart3d-controls">
        <button class="chart3d-btn" data-scatter-view="free">Free rotate</button>
        <button class="chart3d-btn active" data-scatter-view="front">Front</button>
        <button class="chart3d-btn" data-scatter-view="side">Side</button>
        <button class="chart3d-btn" data-scatter-view="top">Top</button>
      </div>
      <div class="chart3d-wrap">
        <canvas class="scatter3d-canvas"></canvas>
        <div class="scatter3d-tooltip" style="display:none;position:absolute;pointer-events:none;z-index:10;background:var(--surface-2,#131d33);border:1px solid var(--line,#26344f);border-radius:8px;padding:8px 12px;font-size:11px;white-space:nowrap"></div>
      </div>
      <div class="scatter-legend"></div>
    </section>`;
  }

  /* ============================================================
     Uploaded Documents — one row per `signals_extracted` event on
     the project. Reuses LinSignals.DOC_TYPE_LABEL for friendly type
     names and the selected LinTZ zone for the upload timestamp.
     ============================================================ */
  function uploadedDocEvents(project) {
    const evs = (project && Array.isArray(project.events)) ? project.events : [];
    const fromEvents = evs.filter((e) => {
      const t = (e && (e.type || e.event || e.kind)) || "";
      return t === "signals_extracted";
    });
    // Union with signalInputs.sources: add doc types that have no surviving event
    // (events may have been partially cleared by an earlier reset).
    const out = fromEvents.slice();
    if (project && project.signalInputs && project.signalInputs.sources) {
      const seen = {};
      fromEvents.forEach((e) => { if (e.docType) seen[String(e.docType).toLowerCase()] = true; });
      Object.values(project.signalInputs.sources).forEach(function (src) {
        if (!src || !src.docType) return;
        const key = String(src.docType).toLowerCase();
        if (seen[key]) return;
        seen[key] = true;
        out.push({
          event: 'signals_extracted',
          docType: src.docType,
          at: src.at || null,
          appliedFields: [],
          synthetic: true
        });
      });
    }
    return out;
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
    // Backend extractSignals_ stores the array as `appliedFields` — read it first.
    const src = e.appliedFields != null ? e.appliedFields
              : e.applied != null ? e.applied
              : (e.fields != null ? e.fields : e.field);
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
        <p class="eyebrow">Documents — ${evs.length} ${evs.length === 1 ? "document" : "documents"}</p>
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

    // ---- collapsible-section badges ----
    const cs = (window.collapsibleSection) || function (id, t, c) { return c; };
    const pillBadge = (st) => {
      const norm = normalizeStatus(st);
      if (!norm) return `<span class="pill pill-none">No data</span>`;
      const map = { Green: "green", Complete: "green", Yellow: "amber", Amber: "amber", Red: "red" };
      return `<span class="pill pill-${map[norm] || "none"}">${esc(norm)}</span>`;
    };
    let overallState = null;
    try { const c = currentSnapshot(p); overallState = (c && c.governance && c.governance.state) || resolveBriefState(p); }
    catch (e) { try { overallState = resolveBriefState(p); } catch (e2) {} }
    const simArr = (p.simulationSignals && p.simulationSignals.signal_array) || [];
    const ensActive = simArr.filter((r) => r && r.status_color && normalizeStatus(r.status_color)).length;
    const ensEst = simArr.filter((r) => r && /\b(estimated|derived|assumed)\b/i.test(String(r.evidence_metric || ""))).length;
    const uploadCount = (typeof uploadedDocEvents === "function") ? uploadedDocEvents(p).length : 0;
    const inputFieldCount = Object.keys(p.signalInputs || {})
      .filter((k) => k !== "sources" && p.signalInputs[k] != null && p.signalInputs[k] !== "").length;
    const totalCats = LIN_CATEGORIES.length;
    const totalModulesForBadge = LIN_CATEGORIES.reduce((n, c) => n + c.modules.length, 0);

    root.innerHTML =
      `<div class="detail-head">
         <button class="btn detail-back" data-back>← Back to Portfolio</button>
         <div class="detail-id">
           <p class="eyebrow">Project detail</p>
           <h1><span class="mod-mono">${esc(p.id)}</span> ${esc(p.name)} <span class="sector-pill" data-sector="${esc(String(p.sector || "hybrid").toLowerCase() === "combined" ? "hybrid" : String(p.sector || "hybrid").toLowerCase())}">${esc(String(SECTOR_LABEL[p.sector] || p.sector || "Hybrid").toUpperCase())}</span></h1>
           ${(p.formattedAddress || p.address) ? `<p class="detail-meta detail-address">${esc(p.formattedAddress || p.address)}</p>` : ""}
           <p class="detail-meta">
             Reporting period: <span class="mod-mono">${esc(p.reportingPeriod)}</span> ·
             State: <span class="li-state state-${stateKey}">${esc(state)}</span>
           </p>
         </div>
         <div class="detail-head-actions">
           <button class="btn small primary detail-upload" data-upload="${esc(p.id)}">Upload documents</button>
           <button class="btn small detail-reset" data-reset="${esc(p.id)}">Reset signals</button>
           <span class="detail-reset-msg kn-sub" aria-live="polite"></span>
         </div>
       </div>
        ${/* Release 2 · Phase 2 item 9 — section order: Project Signal Network →
             Signal Flow → Executive Brief → Governance Decision → Signal Web →
             Signal Inputs → Ensemble Analysis → Signal Stack. Documents &
             Extracted Signals (not in the named order) is kept adjacent to Signal
             Inputs. sessionStorage keys (the section ids) are unchanged, so saved
             open/closed states survive. */""}
        ${cs("d-projnet", "Project Signal Network", `<div class="detail-projnet2d"></div>`, false, totalCats + " categories")}
        ${cs("d-neural", "Signal Flow", `<div class="detail-neural-flow" data-project-id="${esc(p.id)}"></div>`, false, `${totalModulesForBadge} modules`)}
        ${cs("d-brief", "Executive Brief", executiveBriefHtml(p), false, "")}
        ${cs("d-decision", "Governance Decision", `<section class="panel detail-decision" aria-label="PCEIF governance decision (project detail)"></section>`, false, pillBadge(overallState))}
        ${cs("d-web", "Signal Web", signalWebHtml(p), false, totalModulesForBadge + " modules")}
        ${cs("d-ledger", "Signal Inputs", `<section class="panel detail-ledger" aria-label="Signal ledger (project detail)"></section>`, false, pillBadge(overallState))}
        ${cs("d-docsignals", "Documents & Extracted Signals",
             uploadedDocsPanelHtml(p) +
             `<section class="panel detail-signals" aria-label="Extracted signals detail"></section>`,
             false, `${uploadCount} doc${uploadCount === 1 ? "" : "s"} · ${inputFieldCount} field${inputFieldCount === 1 ? "" : "s"}`)}
        ${cs("d-ensemble", "Ensemble Analysis", ensembleHtml(p), false, `${ensActive} active · ${ensEst} est.`)}
       ${cs("d-stack", "Signal Stack — " + totalCats + " Categories", `<div class="detail-modules"></div>`, false, "")}`;

    // Every section starts collapsed (sessionStorage may restore an open one);
    // the badges above still summarise what's inside. Heavy visuals render on
    // FIRST expand via the lin:section-opened event from toggleSection, not at
    // page load. The canvases (sphere / scatter) additionally need visible
    // dimensions — eager rendering into a display:none body sizes them 0×0.
    lazyInits = {
      // 2D per-project signal network — flat node-link of the 11 categories.
      "d-projnet": () => { if (window.LinProjectNet2D) LinProjectNet2D.render(root.querySelector(".detail-projnet2d"), p); },
      "d-neural": () => { if (typeof LinNeuralFlow !== "undefined") LinNeuralFlow.render(p, root.querySelector(".detail-neural-flow")); },
      // Brief renders (and possibly calls the chat endpoint) only when opened.
      "d-brief": () => { wireBrief(root, p); refreshBrief(root, p); },
      "d-web": () => { wireSignalWeb(root, id); wireSignalSphere(root, p); },
      "d-ensemble": () => { wireEnsembleScatter(root, p); },
      // Uploaded-docs table is already in the section HTML; the extracted-
      // signals panel below it renders on expand.
      "d-docsignals": () => { if (window.LinSignals) LinSignals.renderSignalsPanel(root.querySelector(".detail-signals"), p); },
      "d-ledger": () => { LinApp.renderLedger(p, root.querySelector(".detail-ledger")); },
      "d-decision": () => { LinApp.renderDecisionCard(p, root.querySelector(".detail-decision")); },
      // HUD-depth per-project deep dive (chart + why-grid + reasoning + rule)
      "d-stack": () => { LinDeepDive.render(p, root.querySelector(".detail-modules")); }
    };
    Object.keys(lazyDone).forEach((k) => { delete lazyDone[k]; });

    wireBack(root);
    wireReset(root);
    // Initialise any section the session restored as open.
    Object.keys(lazyInits).forEach((secId) => {
      const body = document.getElementById("body-" + secId);
      if (body && body.style.display !== "none") runLazyInit(secId);
    });
  }

  /* ---------- lazy section initialisation (render-on-first-expand) ---------- */
  let lazyInits = null;
  const lazyDone = {};
  function runLazyInit(secId) {
    if (!lazyInits || typeof lazyInits[secId] !== "function" || lazyDone[secId]) return;
    lazyDone[secId] = true;
    try { lazyInits[secId](); }
    catch (e) { console.warn("[detail] lazy init failed for section", secId, e); }
  }
  document.addEventListener("lin:section-opened", (e) => {
    const secId = e && e.detail && e.detail.id;
    if (secId) runLazyInit(secId);
  });

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

  // Group every category by its computed status (Red / Amber / Green /
  // Conditional-or-no-data) so the brief can describe a SIGNAL PATTERN rather
  // than list each category individually.
  function briefCategoryGroups(project) {
    const groups = { Red: [], Amber: [], Green: [], Conditional: [] };
    const snap = briefSnapshot(project);
    if (snap && snap.categories) {
      Object.keys(snap.categories).forEach((k) => {
        const c = snap.categories[k];
        const num = c && c.num;
        if (!num) return;
        if (c.parked || !c.status) { groups.Conditional.push(num); return; }
        const s = String(c.status).toLowerCase();
        if (s.indexOf("red") >= 0) groups.Red.push(num);
        else if (s.indexOf("amber") >= 0 || s.indexOf("yellow") >= 0) groups.Amber.push(num);
        else if (s.indexOf("green") >= 0 || s.indexOf("complete") >= 0) groups.Green.push(num);
        else groups.Conditional.push(num);
      });
    }
    return groups;
  }

  // The 3-6 specific computed values that most explain the overall status —
  // actual numbers, never generic text. Each is { label, value, status }.
  function briefKeySignals(project) {
    const s = (project && project.signals) || {};
    const si = (project && project.signalInputs) || {};
    const evm = s.evm || {}, mc = s.mc || {};
    const out = [];
    const bac = Number(evm.bac != null ? evm.bac : si.bac);
    if (Number.isFinite(bac) && bac > 0 && Number.isFinite(Number(mc.p80))) {
      const pct = Math.round((Number(mc.p80) / bac - 1) * 100);
      out.push({ label: "P80 EAC vs BAC", value: (pct >= 0 ? "+" : "") + pct + "%", status: pct > 10 ? "Red" : pct > 5 ? "Amber" : "Green" });
    }
    if (Number.isFinite(Number(evm.cpi))) out.push({ label: "CPI", value: Number(evm.cpi).toFixed(3), status: evm.cpi < 0.90 ? "Red" : evm.cpi < 0.95 ? "Amber" : "Green" });
    if (Number.isFinite(Number(evm.spi))) out.push({ label: "SPI", value: Number(evm.spi).toFixed(3), status: evm.spi < 0.90 ? "Red" : evm.spi < 0.95 ? "Amber" : "Green" });
    if (s.cusum) out.push({ label: "Schedule drift (CUSUM)", value: s.cusum.breached ? "breach detected" : "in control", status: s.cusum.breached ? "Red" : "Green" });
    const ctot = Number(si.contingencyTotal), cburn = Number(si.contingencyBurned);
    const comp = Number(si.actualPctComplete != null ? si.actualPctComplete : si.pctComplete);
    if (Number.isFinite(ctot) && ctot > 0 && Number.isFinite(cburn)) {
      const bp = Math.round(cburn / ctot * 100);
      out.push({ label: "Contingency burned", value: bp + "%" + (Number.isFinite(comp) ? " at " + Math.round(comp) + "% complete" : ""), status: bp > 75 ? "Red" : bp > 50 ? "Amber" : "Green" });
    }
    if (s.doc && Number.isFinite(Number(s.doc.score))) {
      const ds = Number(s.doc.score);
      out.push({ label: "Document risk", value: ds.toFixed(2), status: ds >= 0.70 ? "Red" : ds >= 0.40 ? "Amber" : "Green" });
    }
    return out.slice(0, 6);
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

    const stateName = gov.state || resolveBriefState(project) || "unknown";

    // PCEIF is a prediction + advisory platform: it presents evidence and
    // surfaces recommendations — it does not issue commands. The PM is the
    // decision-maker; the platform is the advisor. The persona below sets that
    // diplomatic, advisory tone for the whole brief.
    const advisor =
      "You are a senior project controls advisor writing an evidence-based briefing for a program director. " +
      "Your role is to present findings from computational analysis and offer considered recommendations — not to command action. " +
      "PCEIF is a prediction and advisory platform: it presents evidence and surfaces recommendations; it does not issue commands or directives. " +
      "The program director is the decision-maker; you are the advisor.\n\n" +
      "Tone:\n" +
      "- DIPLOMATIC: present findings as evidence, not verdicts.\n" +
      "- ADVISORY: suggest, recommend, consider — never command or direct.\n" +
      "- RESPECTFUL: the program director is the decision-maker — acknowledge their judgment.\n" +
      "- MEASURED: match urgency to the evidence — never amplify beyond what the data supports.\n" +
      "- PRECISE: be specific about what the models found, and deferential about what must happen — that is the PM's call.\n\n" +
      "USE phrasing such as: 'The computational analysis suggests…', 'The evidence indicates…', " +
      "'The models collectively point to…', 'It may be worth considering…', 'The data supports a closer look at…', " +
      "'The program director may wish to review…', 'The signals are consistent with…', 'One area that warrants attention is…'.\n" +
      "AVOID: 'You must…' / 'The PM must…', 'Immediate action required', 'Recovery plan required', " +
      "'Escalate immediately', 'Critical failure', and any commanding or alarming language. " +
      "Stay diplomatic even for a Red state — for example: 'The evidence across multiple analytical methods consistently points to " +
      "significant cost and schedule pressure. The program director may wish to consider bringing the controls lead into a focused review " +
      "before the next reporting cycle closes.' — and NOT 'This project is in critical failure. Recovery plan required within 48 hours.'\n\n" +
      "This is advice from a trusted analytical system to a senior professional. Treat the reader accordingly.\n\n";

    const groups = briefCategoryGroups(project);
    const keySignals = briefKeySignals(project);
    const groupLine = (label, arr) => label + " (" + arr.length + " categor" + (arr.length === 1 ? "y" : "ies") + "): " + (arr.length ? arr.join(", ") : "none");
    const groupsText = [
      groupLine("RED", groups.Red),
      groupLine("AMBER", groups.Amber),
      groupLine("GREEN", groups.Green),
      groupLine("CONDITIONAL / NO DATA", groups.Conditional)
    ].join("\n");
    const signalsText = keySignals.length
      ? keySignals.map((k) => "- " + k.label + ": " + k.value + " (" + k.status + ")").join("\n")
      : "- (no computed key signals available yet)";

    return advisor +
      "Briefing subject: " + (snapshot.project_name || project.name) + " (Project " + snapshot.project_id + ", " + (snapshot.sector || "unknown") + " sector). " +
      "The platform computed " + totalModules + " signal modules across " + LIN_CATEGORIES.length + " analytical categories from a stored log dated " + computedDay + ".\n\n" +
      "Category statuses grouped by colour (internal context — use these groupings, do NOT re-list each category individually):\n" + groupsText +
      "\n\nComputed key signal values (internal context — quote these ACTUAL numbers in Key Drivers):\n" + signalsText +
      "\n\nPer-category worst module (internal context — do NOT quote raw module names or metrics):\n" + catSummary +
      "\n\nOverall governance state: " + (gov.state || "unknown") +
      "\nNamed authority: " + (gov.authority || "unknown") +
      "\nRecommended action on file: " + (gov.action || "unknown") +
      "\nEvidence agreement: " + confText +
      "\n\nWrite the briefing with EXACTLY these four sections, each introduced by its '### ' header line verbatim. " +
      "LEAD WITH THE RECOMMENDATION — the first thing the reader sees is what to do, not a data summary. " +
      "Do NOT mention category numbers except when grouping them in Signal Pattern; a program director does not think in Cat 1-12.\n\n" +
      "### Recommendation\n" +
      "Begin with the overall status in CAPS followed by ' · ' and a single short action clause (e.g. 'RED-REVIEW · bring the controls lead into a focused review this cycle'). " +
      "Then ONE sentence beginning 'The evidence suggests…' that frames the overall picture. Diplomatic and advisory — never a command.\n\n" +
      "### Signal Pattern\n" +
      "Group the categories by status. For each non-empty group, output a line starting with '● ' then the status word in CAPS and the count in parentheses, " +
      "then on the SAME line ' — ' followed by a 2-3 sentence synthesis of what those categories have in common and what they indicate. " +
      "List the grouped Cat numbers inside the synthesis once. Order groups RED, then AMBER, then GREEN, then CONDITIONAL / NO DATA. Skip empty groups. " +
      "Do NOT write one line per category — synthesise the group.\n\n" +
      "### Key Drivers\n" +
      "3-4 bullet points, each line starting with '- ', each naming a SPECIFIC computed signal value from the list above (e.g. '- CPI 0.929 indicates…', " +
      "'- P80 EAC is +10% above BAC…'). Use the actual numbers. These are the signals that most explain the overall status.\n\n" +
      "### Required Actions\n" +
      "2-4 bullet points, each line starting with '- ', each a specific advisory action that NAMES a plausible authority (e.g. controls lead, program director) " +
      "and a sensible horizon (e.g. 'before the next reporting cycle closes'). Use diplomatic advisory language throughout — 'the evidence suggests', " +
      "'the program director may wish to' — never an imperative command, never an ultimatum, and never 48-hour or recovery-plan language, not even for a Red state.\n\n" +
      "Output ONLY the four sections with the exact '### ' headers above — no preamble and no closing remarks.";
  }

  // Friendly category labels used by the structured brief (Section 2).
  const BRIEF_CAT_LABEL = {
    "Cat 1": "Cost Performance (Cat 1)", "Cat 2": "Schedule Simulation (Cat 2)",
    "Cat 3": "Cost Simulation (Cat 3)", "Cat 4": "Document & Risk (Cat 4)",
    "Cat 5": "System Dynamics (Cat 5)", "Cat 6": "Signal Synthesis (Cat 6)",
    "Cat 7": "Evidence Combination (Cat 7)", "Cat 8": "Portfolio Analysis (Cat 8)",
    "Cat 9": "Governance & Compliance (Cat 9)"
  };

  /* Parse the structured 4-section brief into its parts. Returns null when the
     text has no recognisable '### ' / bold / bare section headers, so the caller
     can fall back to rendering the brief as a single plain paragraph. */
  function parseBrief(text) {
    if (!text) return null;
    const lines = String(text).replace(/\r/g, "").split("\n");
    const out = { recommendation: [], pattern: [], drivers: [], actions: [] };
    function headerKey(line) {
      const isHash = /^#{1,6}\s/.test(line);
      let h = line.replace(/^#{1,6}\s*/, "").replace(/\*\*/g, "").trim().replace(/:\s*$/, "").toLowerCase();
      // New headers + legacy headers (so old cached briefs still render).
      const known = (h === "recommendation" || h === "signal pattern" || h === "key drivers" ||
                     h === "required actions" || h === "overall status" || h === "category analysis" ||
                     h === "conclusion" || h === "recommendations");
      if (!isHash && !known) return null;
      if (h === "recommendation" || h.indexOf("overall") >= 0) return "recommendation";
      if (h.indexOf("signal pattern") >= 0 || h.indexOf("category") >= 0) return "pattern";
      if (h.indexOf("key driver") >= 0 || h.indexOf("conclusion") >= 0) return "drivers";
      if (h.indexOf("required action") >= 0 || h.indexOf("recommendation") >= 0) return "actions";
      return null;
    }
    let cur = null, seen = false;
    lines.forEach((raw) => {
      const line = raw.trim();
      const key = headerKey(line);
      if (key) { cur = key; seen = true; return; }
      if (!cur || !line) return;
      out[cur].push(line);
    });
    if (!seen) return null;
    const stripBullet = (s) => s.replace(/^[-*•▸]\s*/, "").replace(/^\d+[.)]\s*/, "").trim();
    return {
      recommendation: out.recommendation.join(" ").trim(),
      pattern: out.pattern.slice(),                                   // keep raw lines (● group rows + synthesis)
      drivers: out.drivers.map(stripBullet).filter(Boolean),
      actions: out.actions.map(stripBullet).filter(Boolean)
    };
  }

  // Map a leading status word to a normalized status key for colour-coding.
  function statusKeyFromText(s) {
    const t = String(s || "").toLowerCase();
    if (t.indexOf("red") >= 0) return "red";
    if (t.indexOf("amber") >= 0 || t.indexOf("yellow") >= 0) return "amber";
    if (t.indexOf("green") >= 0 || t.indexOf("complete") >= 0) return "green";
    if (t.indexOf("conditional") >= 0 || t.indexOf("no data") >= 0) return "none";
    return "none";
  }

  function briefSectionsHtml(parsed) {
    const section = (head, inner) => inner
      ? `<div class="eb-section"><p class="eb-sec-head">${esc(head)}</p>${inner}</div>` : "";

    // Recommendation — lead block. First " · "-delimited token is the status.
    let recHtml = "";
    if (parsed.recommendation) {
      const rec = parsed.recommendation;
      const dot = rec.indexOf("·");
      if (dot > 0) {
        const statusPart = rec.slice(0, dot).trim();
        const rest = rec.slice(dot + 1).trim();
        const k = statusKeyFromText(statusPart);
        recHtml = `<p class="eb-rec"><span class="eb-rec-status status-${esc(k)}">${esc(statusPart)}</span> ${esc(rest)}</p>`;
      } else {
        recHtml = `<p class="eb-rec">${esc(rec)}</p>`;
      }
    }

    // Signal Pattern — group rows (● STATUS (n) — synthesis) with coloured dots.
    const patItems = parsed.pattern.map((raw) => {
      const line = raw.replace(/^[●○•*-]\s*/, "").trim();
      const dash = line.indexOf("—") >= 0 ? line.indexOf("—") : line.indexOf(" - ");
      const head = dash > 0 ? line.slice(0, dash).trim() : line;
      const body = dash > 0 ? line.slice(dash + 1).replace(/^[—-]\s*/, "").trim() : "";
      const k = statusKeyFromText(head);
      if (/^[●○•*-]/.test(raw) || /\((\d+)\s*categor/i.test(head)) {
        return `<li class="eb-group"><span class="eb-group-dot status-${esc(k)}"></span>` +
          `<span class="eb-group-head">${esc(head)}</span>${body ? ` <span class="eb-group-body">${esc(body)}</span>` : ""}</li>`;
      }
      return `<li class="eb-group eb-group-cont">${esc(line)}</li>`;
    }).join("");

    const driverItems = parsed.drivers.map((d) => `<li>${esc(d)}</li>`).join("");
    const actionItems = parsed.actions.map((a) => `<li>${esc(a)}</li>`).join("");

    return `<div class="eb-body eb-structured">` +
      section("Recommendation", recHtml) +
      section("Signal Pattern", patItems ? `<ul class="eb-pattern">${patItems}</ul>` : "") +
      section("Key Drivers", driverItems ? `<ul class="eb-drivers">${driverItems}</ul>` : "") +
      section("Required Actions", actionItems ? `<ul class="eb-actions">${actionItems}</ul>` : "") +
      `</div>`;
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

    const stKey = String(state).toLowerCase().replace("-review", "");

    // Group categories by status and pull the actual computed key signals.
    const groups = briefCategoryGroups(project);
    const keySignals = briefKeySignals(project);

    // ── Recommendation (lead): status + one action clause + an evidence line.
    const actionClause = stKey === "red" ? "bring the controls lead into a focused review this cycle"
      : stKey === "amber" ? "review the cost and schedule trend with the controls lead this cycle"
      : stKey === "yellow" ? "keep a light watch on the early-warning variance"
      : stKey === "complete" ? "begin closeout reconciliation when convenient"
      : "maintain routine monitoring";
    const evidenceLine = stKey === "red"
        ? "The evidence suggests significant cost and schedule pressure that warrants a focused look before the next reporting cycle closes."
      : stKey === "amber"
        ? "The evidence suggests meaningful risk that may warrant a closer look this cycle."
      : stKey === "yellow"
        ? "The evidence suggests early-warning variance worth monitoring."
      : stKey === "complete"
        ? "The evidence suggests the tracked measures are reading as complete."
        : "The evidence suggests the project is tracking within expected ranges.";
    const recommendation = String(state).toUpperCase() + " · " + actionClause + "\n" + evidenceLine;

    // ── Signal Pattern: one ● line per non-empty status group.
    const phraseFor = {
      Red: "the evidence points to significant pressure concentrated in these areas",
      Amber: "the analysis indicates meaningful risk worth a closer look",
      Green: "the signals are consistent with these areas tracking well",
      Conditional: "these areas are awaiting data or are conditional on further inputs"
    };
    const patternLines = [];
    [["Red", "RED"], ["Amber", "AMBER"], ["Green", "GREEN"], ["Conditional", "CONDITIONAL / NO DATA"]].forEach((g) => {
      const arr = groups[g[0]];
      if (!arr.length) return;
      patternLines.push("● " + g[1] + " (" + arr.length + " categor" + (arr.length === 1 ? "y" : "ies") + ") — " +
        arr.join(", ") + ": " + phraseFor[g[0]] + ".");
    });
    const patternBlock = patternLines.length ? patternLines.join("\n") : "No category has computed data yet.";

    // ── Key Drivers: the actual computed signal values.
    const driverLines = keySignals.length
      ? keySignals.map((k) => "- " + k.label + ": " + k.value + " (" + k.status + ")")
      : ["- No computed key signals are available yet."];

    // ── Required Actions: advisory, named authority + horizon, never a command.
    let actions;
    if (stKey === "red") {
      actions = [
        "The program director may wish to bring the controls lead into a focused review before the next reporting cycle closes",
        "It may be helpful to validate the cost and schedule baseline against the latest pay application",
        "The data supports a closer look at the most pressured areas together with the project team"
      ];
    } else if (stKey === "amber") {
      actions = [
        "Consider reviewing the cost and schedule trend with the controls lead before the next reporting cycle closes",
        "It may be worth verifying the earned-value figures against the latest pay application"
      ];
    } else if (stKey === "yellow") {
      actions = [
        "Consider a brief check-in to monitor the early-warning variance over the coming cycle",
        "It may be helpful to confirm the latest earned-value inputs are current"
      ];
    } else if (stKey === "complete") {
      actions = [
        "Consider initiating closeout documentation when convenient",
        "It may be helpful to reconcile the final cost and schedule figures"
      ];
    } else {
      actions = [
        "The signals are within expected ranges; routine monitoring appears sufficient this cycle",
        "No escalation appears warranted based on the current evidence"
      ];
    }

    return [
      "### Recommendation", recommendation,
      "### Signal Pattern", patternBlock,
      "### Key Drivers", driverLines.join("\n"),
      "### Required Actions", actions.map((a) => "- " + a).join("\n")
    ].join("\n");
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
        <span class="eb-status">Analysing signals across ${LIN_CATEGORIES.length} categories…</span>
      </div>`;
    }
    if (state === "skipped") {
      return `<div class="eb-body eb-skipped">Upload project documents to generate the stored log. The executive brief is generated from that log — not from recomputed signals.</div>`;
    }
    if (state === "error") {
      return `<div class="eb-body eb-error" role="alert">Brief unavailable: ${esc(errMsg || "unknown error")}</div>`;
    }
    // Ready: render the structured 4 sections when the brief follows the format,
    // otherwise fall back to the brief text as a single paragraph.
    const text = (brief && brief.text) ? brief.text : "";
    const parsed = parseBrief(text);
    if (parsed && (parsed.recommendation || parsed.pattern.length || parsed.drivers.length || parsed.actions.length)) {
      return briefSectionsHtml(parsed);
    }
    return `<div class="eb-body">${esc(text)}</div>`;
  }

  // Deterministic flags block — rendered regardless of the LLM brief so a
  // Green/Yellow project still surfaces EVERY Red module (with its category),
  // the Red-review high-conflict advisory (project DST conflict K >= 0.55), and
  // any active liability period. Reads the DST project fusion directly so the
  // rollup can never hide a Red.
  function briefFlagsHtml(project) {
    let f = null;
    try { f = window.getProjectFusion ? window.getProjectFusion(project) : null; } catch (e) { f = null; }
    if (!f) return "";
    const parts = [];
    if (f.complete && f.liabilityUntil) {
      const today = new Date().toISOString().slice(0, 10);
      if (f.liabilityUntil >= today) {
        parts.push('<p class="eb-flag eb-flag-info">In liability period (ends ' + esc(f.liabilityUntil) + ')</p>');
      }
    }
    if (f.redReview) {
      parts.push('<p class="eb-flag eb-flag-review">⚑ Red-review: high disagreement among categories (conflict ' +
        Math.round((f.conflict || 0) * 100) + '%) — recommend named human review. This advisory does not change the fused status band.</p>');
    }
    const reds = f.redFlags || [];
    if (reds.length) {
      const items = reds.map((r) =>
        '<li><span class="eb-flag-cat">' + esc(r.category) + '</span> ' + esc(r.module) + '</li>').join("");
      parts.push('<div class="eb-flags-red"><p class="eb-flag eb-flag-red">⚑ Red modules (' + reds.length +
        ') — flagged regardless of overall status:</p><ul class="eb-flag-list">' + items + '</ul></div>');
    }
    if (!parts.length) return "";
    return '<div class="eb-flags" aria-label="Brief flags">' + parts.join("") + '</div>';
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
    let flags = "";
    try { flags = briefFlagsHtml(project); } catch (e) {}
    const state = cached ? "ready" : "loading";
    return `<section class="panel eb-panel eb-accent-${esc(accent)}" aria-label="Executive brief" data-eb-id="${esc(projectId)}">
      <div class="eb-head">
        <div>
          <p class="eyebrow eb-eyebrow">Executive brief${project && project.name ? " — " + esc(project.name) : ""}</p>
          <p class="kn-sub eb-sub">${period ? "Reporting period: " + esc(period) + " · " : ""}grouped analysis across ${LIN_CATEGORIES.length} signal categories</p>
        </div>
        <button type="button" class="btn small eb-regen" data-eb-regen="${esc(projectId)}" aria-label="Regenerate brief">Regenerate ↺</button>
      </div>
      ${flags}
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
      // 1200 tokens to fit the longer 4-section structured brief.
      const chatP = LinStore.chat(prompt, project.id, { max_tokens: 1200 });
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
    // Per-project upload (Release 2): opens the upload dialog pre-locked to this
    // project (no selector).
    root.querySelectorAll("[data-upload]").forEach((b) =>
      b.addEventListener("click", () => {
        if (window.LinIngest && LinIngest.openUploadModal) LinIngest.openUploadModal(b.dataset.upload);
      }));
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
        // Drop the dropzone's per-project extraction cache so the signals panel
        // doesn't re-show stale inputs after the reset.
        if (window.LinSignals && LinSignals.clearCache) LinSignals.clearCache(id);
        // Re-fetch the (now-cleared) server copy; fall back to the cached copy.
        try {
          const fresh = await LinStore.getProject(id);
          if (fresh && window.LIN_PROJECTS) {
            const i = LIN_PROJECTS.findIndex((x) => x.id === id);
            if (i >= 0) LIN_PROJECTS[i] = fresh;
          }
        } catch (e) { /* keep the cached copy on fetch failure */ }
        // Force the in-memory copy to a true "Awaiting ingest" state, so the UI is
        // correct even if the backend reset is an older build that didn't clear
        // history/events/documents (history feeds CUSUM; events backs the
        // Uploaded Documents table). The server is the source of truth once its
        // resetSignals_ is redeployed — this just keeps the screen honest meanwhile.
        const p = LinStore.getCached(id);
        if (p) {
          p.signals = null; p.signalInputs = null; p.simulationSignals = null;
          p.history = []; p.events = [];
          ["documents", "uploadedDocuments", "docs"].forEach((k) => {
            if (Array.isArray(p[k])) p[k] = [];
          });
          p.status = null; p.reportingPeriod = null; p.derivedState = null;
        }
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

  function wireSignalSphere(root, project) {
  const SC = window.LIN_STATUS_COLORS;   // central palette (radar.css --status-*)
    const canvas = root.querySelector(".sphere3d-canvas");
    if (!canvas || !window.LIN_CATEGORIES) return;
    const wrap = canvas.parentElement;
    const dpr = window.devicePixelRatio || 1;
    function resize() {
      const w = wrap.clientWidth || 800;
      canvas.width = w * dpr;
      canvas.height = 480 * dpr;
      canvas.style.width = w + "px";
      canvas.style.height = "480px";
    }
    resize();
    const ctx = canvas.getContext("2d");
    const DOT = { Complete: SC.Complete, Green: SC.Green, Yellow: SC.Yellow, Amber: SC.Amber, Red: SC.Red, none: SC.None };
    const SR = { Complete: 1.0, Green: 0.85, Yellow: 0.65, Amber: 0.40, Red: 0.15 };
    const R = 160;
    const goldenAngle = Math.PI * (3 - Math.sqrt(5));

    const sectorNA = "N/A — not applicable to " +
      ((window.normalizeSector ? normalizeSector(project.sector) : (project.sector || "hybrid"))
        .replace(/^./, (c) => c.toUpperCase())) + "-sector projects";
    const moduleList = [];
    LIN_CATEGORIES.forEach((cat) => {
      cat.modules.forEach((m) => {
        const active = !(cat.parked || cat.conditional || m.active === false);
        const status = active && window.getModuleStatus ? getModuleStatus(m.method_class, project) : null;
        const na = status === "NA"; // sector abstention — dim dot, explanatory tooltip
        const norm = active && !na ? normalizeStatus(status) : null;
        const evidence = active && !na ? moduleEvidence(m, project) : null;
        moduleList.push({ cat, module: m, status: norm, na, evidence, catColor: cat.color });
      });
    });

    const pts = moduleList.map((ml, i) => {
      const yUnit = 1 - (i / (moduleList.length - 1)) * 2;
      const r = Math.sqrt(Math.max(0, 1 - yUnit * yUnit));
      const theta = goldenAngle * i;
      const rad = ml.status ? (SR[ml.status] || 0.05) : 0.05;
      return { bx: r * Math.cos(theta) * rad, by: yUnit * rad, bz: r * Math.sin(theta) * rad,
               sx: r * Math.cos(theta), sy: yUnit, sz: r * Math.sin(theta), ml, i };
    });

    const catLabels = LIN_CATEGORIES.map((cat) => {
      let sx = 0, sy = 0, sz = 0, n = 0;
      pts.forEach((pt) => { if (pt.ml.cat.id === cat.id) { sx += pt.sx; sy += pt.sy; sz += pt.sz; n++; } });
      if (!n) return null;
      const len = Math.sqrt((sx/n)*(sx/n) + (sy/n)*(sy/n) + (sz/n)*(sz/n)) || 1;
      return { label: cat.num + " " + cat.name.split(" ").slice(0, 2).join(" "), color: cat.color,
               bx: sx/n/len*1.22, by: sy/n/len*1.22, bz: sz/n/len*1.22 };
    }).filter(Boolean);

    var rotX = 0.3, rotY = 0, zoom = 1;
    var autoRotate = true, dragging = false, lastX = 0, lastY = 0;
    var hoverIdx = -1, projectedPts = [];

    function rxf(p, a) { return { x: p.x, y: p.y*Math.cos(a)-p.z*Math.sin(a), z: p.y*Math.sin(a)+p.z*Math.cos(a) }; }
    function ryf(p, a) { return { x: p.x*Math.cos(a)+p.z*Math.sin(a), y: p.y, z: -p.x*Math.sin(a)+p.z*Math.cos(a) }; }
    function proj(p) {
      const CW = canvas.width/dpr, CH = canvas.height/dpr;
      const fov = 400*zoom, z = p.z+fov, scale = fov/Math.max(z,1);
      return { x: CW/2+p.x*scale, y: CH/2+p.y*scale, scale };
    }

    function draw() {
      const W = canvas.width, H = canvas.height;
      ctx.clearRect(0,0,W,H);
      ctx.save(); ctx.scale(dpr,dpr);
      const CW = W/dpr, CH = H/dpr;
      const grad = ctx.createRadialGradient(CW/2,CH/2,0,CW/2,CH/2,R*1.5);
      grad.addColorStop(0,"rgba(15,23,42,0.3)"); grad.addColorStop(1,"transparent");
      ctx.fillStyle=grad; ctx.fillRect(0,0,CW,CH);

      for (let ring=1;ring<=5;ring++) {
        const a=(ring/6)*Math.PI, ringR=Math.sin(a)*R, ringY=-Math.cos(a)*R;
        ctx.beginPath();
        for (let s=0;s<=60;s++) {
          const ang=(s/60)*Math.PI*2;
          const pr=rxf(ryf({x:ringR*Math.cos(ang),y:ringY,z:ringR*Math.sin(ang)},rotY),rotX);
          const pp=proj(pr); s===0?ctx.moveTo(pp.x,pp.y):ctx.lineTo(pp.x,pp.y);
        }
        ctx.strokeStyle="rgba(38,52,79,0.4)"; ctx.lineWidth=0.5; ctx.stroke();
      }

      projectedPts = pts.map((pt) => {
        const pr=rxf(ryf({x:pt.bx*R,y:pt.by*R,z:pt.bz*R},rotY),rotX);
        const pp=proj(pr); return {pt,pp,pz:pr.z};
      }).sort((a,b)=>a.pz-b.pz);

      projectedPts.forEach((s) => {
        if (!s.pt.ml.status) return;
        const col=DOT[s.pt.ml.status]||DOT.none;
        ctx.beginPath(); ctx.moveTo(CW/2,CH/2); ctx.lineTo(s.pp.x,s.pp.y);
        ctx.strokeStyle=col+"20"; ctx.lineWidth=0.7; ctx.stroke();
      });

      projectedPts.forEach((s) => {
        const ml=s.pt.ml, col=ml.status?(DOT[ml.status]||DOT.none):DOT.none;
        const dotR=ml.status?Math.max(2,4*s.pp.scale):Math.max(1,2*s.pp.scale);
        const isHover=s.pt.i===hoverIdx;
        ctx.beginPath(); ctx.arc(s.pp.x,s.pp.y,isHover?dotR*1.6:dotR,0,Math.PI*2);
        ctx.fillStyle=col; ctx.globalAlpha=ml.status?0.9:0.28; ctx.fill();
        if (isHover) { ctx.strokeStyle=col; ctx.lineWidth=1.5; ctx.globalAlpha=0.5; ctx.stroke(); }
        ctx.globalAlpha=1;
      });

      catLabels.forEach((l) => {
        const pr=rxf(ryf({x:l.bx*R,y:l.by*R,z:l.bz*R},rotY),rotX);
        if (pr.z<-40) return;
        const pp=proj(pr);
        ctx.font="9px SFMono-Regular,ui-monospace,monospace";
        ctx.fillStyle=l.color; ctx.globalAlpha=0.75; ctx.fillText(l.label,pp.x,pp.y); ctx.globalAlpha=1;
      });

      ctx.beginPath(); ctx.arc(CW/2,CH/2,4,0,Math.PI*2);
      ctx.fillStyle="#e9a23b"; ctx.globalAlpha=0.85; ctx.fill(); ctx.globalAlpha=1;
      ctx.restore();
    }

    function animate() { if(autoRotate&&!dragging) rotY+=0.003; draw(); requestAnimationFrame(animate); }

    canvas.addEventListener("mousedown",(e)=>{dragging=true;lastX=e.clientX;lastY=e.clientY;});
    window.addEventListener("mouseup",()=>{if(dragging){dragging=false;autoRotate=true;}});
    canvas.addEventListener("mousemove",(e)=>{
      if(dragging){rotY+=(e.clientX-lastX)*0.006;rotX+=(e.clientY-lastY)*0.006;lastX=e.clientX;lastY=e.clientY;return;}
      const rect=canvas.getBoundingClientRect(), mx=e.clientX-rect.left, my=e.clientY-rect.top;
      let hit=-1;
      for(let k=projectedPts.length-1;k>=0;k--){
        const s=projectedPts[k], dotR=s.pt.ml.status?Math.max(2,4*s.pp.scale):Math.max(1,2*s.pp.scale);
        const dx=s.pp.x-mx, dy=s.pp.y-my;
        if(dx*dx+dy*dy<(dotR*1.6+4)*(dotR*1.6+4)){hit=s.pt.i;break;}
      }
      hoverIdx=hit;
      const tt=root.querySelector(".chart3d-tooltip");
      if(tt){
        if(hit>=0){
          const ml=pts[hit].ml, col=DOT[ml.status]||DOT.none;
          tt.style.display="block"; tt.style.left=(e.clientX-rect.left+14)+"px"; tt.style.top=(e.clientY-rect.top-10)+"px";
          tt.innerHTML=`<div style="font-family:var(--font-mono,monospace);font-size:10px;color:#e9a23b;margin-bottom:3px">${esc(ml.module.num)} ${esc(ml.module.name)}</div><div style="font-size:12px;font-weight:600;color:${esc(col)}">${esc(ml.status||(ml.na?sectorNA:"No data"))}</div>${ml.evidence?`<div style="font-size:11px;color:#9fb0cc;margin-top:2px">${esc(ml.evidence)}</div>`:""}`;
        } else { tt.style.display="none"; }
      }
    });
    canvas.addEventListener("mouseleave",()=>{hoverIdx=-1;const tt=root.querySelector(".chart3d-tooltip");if(tt)tt.style.display="none";});
    canvas.addEventListener("wheel",(e)=>{e.preventDefault();zoom=Math.max(0.5,Math.min(3,zoom-e.deltaY*0.001));},{passive:false});

    root.querySelectorAll("[data-sphere-view]").forEach((btn)=>{
      btn.addEventListener("click",()=>{
        root.querySelectorAll("[data-sphere-view]").forEach((b)=>b.classList.remove("active"));
        btn.classList.add("active");
        const v=btn.dataset.sphereView;
        if(v==="free"){autoRotate=true;}
        else if(v==="top"){autoRotate=false;rotX=Math.PI/2;rotY=0;}
        else if(v==="cost"){autoRotate=false;rotX=0.3;rotY=0.5;}
        else if(v==="evidence"){autoRotate=false;rotX=0.3;rotY=-1.2;}
        else if(v==="gov"){autoRotate=false;rotX=0.3;rotY=2.0;}
      });
    });
    animate();
  }

  function wireEnsembleScatter(root, project) {
  const SC = window.LIN_STATUS_COLORS;   // central palette (radar.css --status-*)
    const canvas = root.querySelector(".scatter3d-canvas");
    if (!canvas || !window.LIN_CATEGORIES) return;
    if (!window.hasSignals || !hasSignals(project)) return;
    const wrap = canvas.parentElement;
    const dpr = window.devicePixelRatio || 1;
    function resize() {
      const w = wrap.clientWidth || 800;
      canvas.width = w * dpr;
      canvas.height = 420 * dpr;
      canvas.style.width = w + "px";
      canvas.style.height = "420px";
    }
    resize();
    const ctx = canvas.getContext("2d");
    const DOT = { Complete: SC.Complete, Green: SC.Green, Yellow: SC.Yellow, Amber: SC.Amber, Red: SC.Red, none: SC.None };
    const SY = { Complete: -120, Green: -80, Yellow: -30, Amber: 40, Red: 100, none: 0 };
    const GRID_Y = 120;

    const scatterData = [];
    // Centre the category columns on the X axis whatever the category count.
    const CAT_MID = (LIN_CATEGORIES.length - 1) / 2;
    let idx = 0;
    LIN_CATEGORIES.forEach((cat, catIdx) => {
      cat.modules.forEach((m) => {
        idx++;
        const active = !(cat.parked || m.active === false);
        const status = active && window.getModuleStatus ? getModuleStatus(m.method_class, project) : null;
        const norm = active ? normalizeStatus(status) : null;
        const bucket = norm || "none";
        const evidence = active ? moduleEvidence(m, project) : null;
        const statusKey = bucket === "none" ? "none" : bucket;
        const zSpread = ((idx*13+7)%60) - 30;
        const xJitter = ((idx*7+3)%40) - 20;
        scatterData.push({
          x: (catIdx-CAT_MID)*55 + xJitter,
          y: SY[statusKey] + (((idx*11)%20) - 10),
          z: zSpread,
          num: m.num, name: m.name, bucket, evidence, color: cat.color, catId: cat.id, catIdx
        });
      });
    });

    const counts = { Red:0, Amber:0, Yellow:0, Green:0, Complete:0 };
    scatterData.forEach((d)=>{ if(d.bucket!=="none"&&counts[d.bucket]!=null) counts[d.bucket]++; });
    const activeTotal = Object.values(counts).reduce((n,v)=>n+v,0);
    if (!activeTotal) return;

    var rotX=0.05, rotY=0.0, autoRotate=false, dragging=false, lastX=0, lastY=0;
    var hoverIdx=-1, projectedPts=[];
    const filteredCats=new Set();

    function rxf(p,a){return{x:p.x,y:p.y*Math.cos(a)-p.z*Math.sin(a),z:p.y*Math.sin(a)+p.z*Math.cos(a)};}
    function ryf(p,a){return{x:p.x*Math.cos(a)+p.z*Math.sin(a),y:p.y,z:-p.x*Math.sin(a)+p.z*Math.cos(a)};}
    function proj(p){
      const CW=canvas.width/dpr, CH=canvas.height/dpr, cx=CW/2, cy=CH/2+30, fov=500;
      const z=p.z+fov, scale=fov/Math.max(z,1);
      return{x:cx+p.x*scale,y:cy+p.y*scale,scale};
    }

    function draw() {
      const W=canvas.width, H=canvas.height;
      ctx.clearRect(0,0,W,H); ctx.save(); ctx.scale(dpr,dpr);
      const CW=W/dpr, CH=H/dpr;

      for(let gx=-6;gx<=6;gx++){
        const p1=rxf(ryf({x:gx*55,y:GRID_Y,z:-180},rotY),rotX);
        const p2=rxf(ryf({x:gx*55,y:GRID_Y,z:180},rotY),rotX);
        const pp1=proj(p1),pp2=proj(p2);
        ctx.beginPath();ctx.moveTo(pp1.x,pp1.y);ctx.lineTo(pp2.x,pp2.y);
        ctx.strokeStyle="rgba(38,52,79,0.5)";ctx.lineWidth=0.5;ctx.stroke();
      }
      for(let gz=-3;gz<=3;gz++){
        const p3=rxf(ryf({x:-330,y:GRID_Y,z:gz*60},rotY),rotX);
        const p4=rxf(ryf({x:330,y:GRID_Y,z:gz*60},rotY),rotX);
        const pp3=proj(p3),pp4=proj(p4);
        ctx.beginPath();ctx.moveTo(pp3.x,pp3.y);ctx.lineTo(pp4.x,pp4.y);
        ctx.strokeStyle="rgba(38,52,79,0.5)";ctx.lineWidth=0.5;ctx.stroke();
      }

      // Fix 6: X axis labels — 10px, "Cat N", category color, centered
      LIN_CATEGORIES.forEach((cat,i)=>{
        const p=rxf(ryf({x:(i-CAT_MID)*55,y:GRID_Y+14,z:0},rotY),rotX), pp=proj(p);
        ctx.font="10px SFMono-Regular,ui-monospace,monospace";
        ctx.fillStyle=cat.color||"#64748b";
        ctx.globalAlpha=filteredCats.size===0||filteredCats.has(cat.id)?0.9:0.25;
        ctx.textAlign="center";
        ctx.fillText("Cat "+(i+1),pp.x,pp.y);
        ctx.textAlign="left";ctx.globalAlpha=1;
      });

      projectedPts=scatterData.map((d,i)=>{
        const pr=rxf(ryf(d,rotY),rotX), pp=proj(pr); return{d,pp,pz:pr.z,i};
      }).sort((a,b)=>a.pz-b.pz);

      projectedPts.forEach((s)=>{
        const d=s.d;
        const catFocused=filteredCats.size===0||filteredCats.has(d.catId);
        // Fix 5: dot = status color, stem = category color
        const dotCol=DOT[d.bucket]||DOT.none;
        const stemCol=d.color||"#4ea0ff";
        const dotR=Math.max(2.5,5*s.pp.scale), isHover=s.i===hoverIdx;
        const shadow=rxf(ryf({x:d.x,y:GRID_Y,z:d.z},rotY),rotX), sp=proj(shadow);
        ctx.beginPath();ctx.arc(sp.x,sp.y,dotR*0.6,0,Math.PI*2);
        ctx.fillStyle="rgba(0,0,0,0.25)";ctx.globalAlpha=catFocused?1:0.1;ctx.fill();
        ctx.beginPath();ctx.moveTo(s.pp.x,s.pp.y);ctx.lineTo(sp.x,sp.y);
        ctx.strokeStyle=stemCol+"55";ctx.lineWidth=0.7;ctx.globalAlpha=catFocused?0.9:0.08;ctx.stroke();
        const r=isHover?dotR*1.4:dotR;
        ctx.beginPath();ctx.arc(s.pp.x,s.pp.y,r,0,Math.PI*2);
        if(d.bucket!=="none"){
          const g=ctx.createRadialGradient(s.pp.x-r*0.3,s.pp.y-r*0.3,0,s.pp.x,s.pp.y,r);
          g.addColorStop(0,dotCol);g.addColorStop(1,dotCol+"80");ctx.fillStyle=g;ctx.globalAlpha=catFocused?0.9:0.08;
        } else {ctx.fillStyle=DOT.none;ctx.globalAlpha=catFocused?0.2:0.04;}
        ctx.fill();ctx.globalAlpha=1;
      });

      ctx.font="10px SFMono-Regular,ui-monospace,monospace";ctx.fillStyle="#64748b";
      ctx.fillText(scatterData.length+"-MODULE ENSEMBLE SCATTER",14,22);
      ctx.font="12px -apple-system,sans-serif";ctx.fillStyle="#9fb0cc";
      ctx.fillText(activeTotal+" active · "+counts.Red+" Red · "+counts.Amber+" Amber · "+counts.Green+" Green",14,40);

      // Fix 2: Y axis status labels as screen-space overlay — drawn last, anchored to left
      [{label:"Complete",y:SY.Complete,color:SC.Complete},{label:"Green",y:SY.Green,color:SC.Green},
       {label:"Yellow",y:SY.Yellow,color:SC.Yellow},{label:"Amber",y:SY.Amber,color:SC.Amber},
       {label:"Red",y:SY.Red,color:SC.Red}
      ].forEach((lb)=>{
        const pp=proj(rxf(ryf({x:-320,y:lb.y,z:0},rotY),rotX));
        ctx.font="10px SFMono-Regular,ui-monospace,monospace";
        ctx.fillStyle=lb.color;ctx.globalAlpha=0.85;
        ctx.textAlign="right";
        ctx.fillText(lb.label,pp.x-6,pp.y+4);
        ctx.beginPath();ctx.moveTo(pp.x,pp.y);ctx.lineTo(pp.x+20,pp.y);
        ctx.strokeStyle=lb.color+"33";ctx.lineWidth=0.5;ctx.stroke();
        ctx.textAlign="left";ctx.globalAlpha=1;
      });
      ctx.restore();
    }

    function animate(){if(autoRotate&&!dragging) rotY+=0.002;draw();requestAnimationFrame(animate);}

    canvas.addEventListener("mousedown",(e)=>{dragging=true;autoRotate=false;lastX=e.clientX;lastY=e.clientY;});
    window.addEventListener("mouseup",()=>{if(dragging) dragging=false;});
    canvas.addEventListener("mousemove",(e)=>{
      if(dragging){rotY+=(e.clientX-lastX)*0.005;rotX+=(e.clientY-lastY)*0.005;lastX=e.clientX;lastY=e.clientY;return;}
      const rect=canvas.getBoundingClientRect(), mx=e.clientX-rect.left, my=e.clientY-rect.top;
      let hit=-1;
      for(let k=projectedPts.length-1;k>=0;k--){
        const s=projectedPts[k], dotR=Math.max(2.5,5*s.pp.scale);
        const dx=s.pp.x-mx, dy=s.pp.y-my;
        if(dx*dx+dy*dy<(dotR*1.4+5)*(dotR*1.4+5)){hit=s.i;break;}
      }
      hoverIdx=hit;
      const tt=root.querySelector(".scatter3d-tooltip");
      if(tt){
        if(hit>=0){
          const d=scatterData[hit], col=DOT[d.bucket]||DOT.none;
          tt.style.display="block";tt.style.left=(e.clientX-rect.left+14)+"px";tt.style.top=(e.clientY-rect.top-10)+"px";
          tt.innerHTML=`<div style="font-family:var(--font-mono,monospace);font-size:10px;color:#e9a23b;margin-bottom:3px">${esc(d.num)} ${esc(d.name)}</div><div style="font-size:12px;font-weight:600;color:${esc(col)}">${esc(d.bucket==="none"?"No data":d.bucket)}</div>${d.evidence?`<div style="font-size:11px;color:#9fb0cc;margin-top:2px">${esc(d.evidence)}</div>`:""}`;
        } else {tt.style.display="none";}
      }
    });
    canvas.addEventListener("mouseleave",()=>{hoverIdx=-1;const tt=root.querySelector(".scatter3d-tooltip");if(tt)tt.style.display="none";});

    root.querySelectorAll("[data-scatter-view]").forEach((btn)=>{
      btn.addEventListener("click",()=>{
        root.querySelectorAll("[data-scatter-view]").forEach((b)=>b.classList.remove("active"));
        btn.classList.add("active");
        const v=btn.dataset.scatterView;
        if(v==="free"){autoRotate=true;}
        else if(v==="front"){autoRotate=false;rotY=0.0;rotX=0.05;}
        else if(v==="side"){autoRotate=false;rotY=Math.PI/2;rotX=0.1;}
        else if(v==="top"){autoRotate=false;rotX=Math.PI/2;rotY=0;}
      });
    });
    // Fix 3: category legend pills
    const legendEl=root.querySelector(".scatter-legend");
    if(legendEl){
      LIN_CATEGORIES.forEach((cat,ci)=>{
        const pill=document.createElement("span");
        pill.className="scatter-legend-pill";
        pill.dataset.cat=cat.id;
        pill.style.borderColor=(cat.color||"#4ea0ff")+"55";
        pill.innerHTML=`<span class="slp-dot" style="background:${esc(cat.color||'#4ea0ff')}"></span><span class="slp-label">Cat ${ci+1}</span>`;
        pill.title=cat.name||"";
        pill.addEventListener("click",()=>{
          if(filteredCats.has(cat.id)){filteredCats.delete(cat.id);pill.classList.remove("active");}
          else{filteredCats.add(cat.id);pill.classList.add("active");}
          legendEl.querySelectorAll(".scatter-legend-pill").forEach((p)=>{
            p.classList.toggle("dimmed",filteredCats.size>0&&!filteredCats.has(p.dataset.cat));
          });
        });
        legendEl.appendChild(pill);
      });
    }
    animate();
  }

  window.LinDetail = { render };
})();
