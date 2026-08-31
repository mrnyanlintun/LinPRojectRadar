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

  // T9. The detail view's own globe handle. LinGlobe is not a singleton, so this one is
  // independent of the portfolio's and each is torn down by whoever made it.
  let detailGlobe = null;

  /* THE CATEGORIES A SINGLE PROJECT HAS, AND WHY EVERY COUNT ON THIS PAGE USES THEM.

     `LIN_CATEGORIES` is the taxonomy IN SERVICE, across twelve categories. The REGISTRY holds
     101 modules -- Group A 53, Group B 36, Group C 7, Group D 5 -- and Run 43 retired 38 of
     them from service on the owner's ruling of 2026-08-21, leaving 63. (This comment read 52
     for Group A until Run 43; the registry has always held 53 and 101, and only the comment was
     wrong.) Retirement is a statement about the taxonomy, not about arithmetic: every retired
     module keeps its registry entry and its audit lineage, and none of them reaches this page.

     Group D is PORTFOLIO LEVEL. Its one category, Portfolio Health, detects patterns ACROSS
     projects and requires more than one by definition; its five modules all declare
     `required: ['portfolioVectors']`. They cannot compute for a single project and they do not
     belong on a single project's page. All five are now retired from service as well, so the
     category renders with no module rows at all.

     Counting the whole taxonomy on this page is how the detail view came to advertise 101
     modules across 12 categories while the Signal Flow diagram in the same page, which already
     filtered correctly, read 96 across 11. Every count, every axis and every iteration below
     goes through these two functions so the page cannot disagree with itself again.

     Portfolio Health is unaffected on the portfolio, where it belongs: the "Portfolio
     health" card (index.html, filled by `renderPortfolio` in workspace.js) reads it from each
     project's own stored result. */
  function projectCats() {
    const all = window.LIN_CATEGORIES || [];
    if (window.projectLevelCategories) {
      try { return window.projectLevelCategories() || []; } catch (e) { /* fall through */ }
    }
    return all.filter((c) => !(c && (c.level === "portfolio" || c.portfolioLevel)));
  }

  function projectModuleCount() {
    return projectCats().reduce((n, c) => n + ((c && c.modules) || []).length, 0);
  }

  // A project is placeable when it has finite coordinates in range. Same test the portfolio
  // globe and the map use; kept here rather than imported so detail.js stays free of app.js.
  function hasCoordsFor(p) {
    const lat = Number(p && p.lat), lng = Number(p && p.lng);
    return isFinite(lat) && isFinite(lng) && Math.abs(lat) <= 90 && Math.abs(lng) <= 180;
  }

  /* ---------- Google Maps, keyed from the deployment's environment ----------

     The Location section shows streets when the deployment has a browser map key, and a note that
     the map is unavailable when it does not. The plumbing — the /mapconfig fetch, the on-demand
     API loader, the status colours — is SHARED with the portfolio Map view in assets/js/gmap.js
     (window.LinGMap), so the two surfaces cannot drift into two behaviours or two keys. The key
     never lives in a committed file; see server/app/map_config.py.

     NO KEY, NO REQUEST TO GOOGLE. Without a key LinGMap.ensure is never called, so the API script
     is never injected and this page makes no call to any Google host. The only request the no-key
     path makes is the same-origin /mapconfig fetch that tells it there is no key.

     __resetMapForTest is kept on LinDetail for the render harness, which reset the detail map's
     caches between the keyed and no-key branches; it now delegates to the shared module. */
  function __resetMapForTest() { if (window.LinGMap && LinGMap.__resetForTest) LinGMap.__resetForTest(); }
  function getMapConfig() { return LinGMap.config(); }
  function ensureGoogleMaps(apiKey) { return LinGMap.ensure(apiKey); }

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
  /* ------------------------------------------------------------
     Severity rank. THE ONE PLACE THIS PAGE ORDERS STATUSES.
     ------------------------------------------------------------
     RUN 44, SECTION 4.1. Two `order` maps on this page were keyed on the
     capitalised spellings only, and the platform does not emit one casing:
     A1.2 CUSUM Anomaly Monitor stores 'green' where every other module stores
     'Green'. A key miss fell through to the unknown default, which is more
     adverse than Green, so a module whose only irregularity was its
     capitalisation was selected as its category's "worst" ahead of two
     properly-cased Green ones. CASE IS NOT SEVERITY. Matching is therefore
     case-insensitive here, the same rule fusion.normalise_status already
     applies on the server, and an unrecognised value keeps the historical
     unknown rank rather than being silently read as good.
     Lower number = more adverse. ------------------------------------------ */
  const STATUS_RANK = { red: 0, "red-review": 1, amber: 2, yellow: 3, green: 4, complete: 5 };
  const STATUS_RANK_UNKNOWN = 3;
  function statusRank(status) {
    const raw = String(status == null ? "" : status).trim().toLowerCase();
    if (STATUS_RANK[raw] != null) return STATUS_RANK[raw];
    // Vocabulary aliases (orange, light-amber, critical, blue) resolve through the
    // page's existing normaliser rather than being restated here.
    const norm = normalizeStatus(status);
    if (norm && STATUS_RANK[norm.toLowerCase()] != null) return STATUS_RANK[norm.toLowerCase()];
    return STATUS_RANK_UNKNOWN;
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
    // RUN 11, GATE 1. This backfill computed nine evidence-combination modules in the browser
    // and grafted them onto the snapshot the spider web renders, which is a second arithmetic
    // source for rows the server also computes and stores. It is refused on the application
    // route. An axis with no stored result stays on the no-data ring, which is the truthful
    // rendering of a module that did not compute.
    if (!window.LIN_ALLOW_CLIENT_ANALYTICS) return;
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
    const cx = 210, cy = 190, n = projectCats().length;
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
    return (cat.modules || []).filter((m) => m.status).slice()
      .sort((a, b) => statusRank(a.status) - statusRank(b.status))[0] || null;
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
  const PARKED_GREY = "#64748b"; // Portfolio Health (ex-Cat 8 ML/AI) parked-status grey
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

  // Flatten the 101 computations into axis entries with angles, leaving a one-slot
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
        // Everything else (incl. active Portfolio Health ML) resolves via getModuleStatus.
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
        key: cat.key,
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

  // RUN 74. THE SIGNAL SPHERE IS REMOVED, by owner ruling for this run.
  //
  // `signalWebHtml` built the whole of the "Signal Web" section -- the eyebrow, the
  // module tally, the five view buttons, the rotating canvas and the footnote -- so the
  // section WAS the sphere and removing the sphere removes the section. Nothing else on
  // the page is touched: the nine remaining sections keep their ids, their order and their
  // sessionStorage open/closed state, and d-ledger now follows d-decision directly.
  //
  // The dead `.sw-*` and `.sphere3d-*` CSS is deliberately LEFT IN PLACE. `.sw-legend` and
  // `.sw-legend i` are shared with `.sw-history-pill`, and editing that block would be a
  // restyle of something other than the sphere.

  /* ============================================================
     Ensemble analysis panel — three views of the 101-computation output:
       1) per-module scatter across status columns
       2) ensemble distribution bar (count per status + trend line)
       3) consensus stacked bar (single proportional bar)
     ============================================================ */
  /* RUN 79, PART C, ITEM 2, AN OWNER RULING. ENSEMBLE ANALYSIS IS REMOVED.
     `ensembleHtml()`, `ensembleTally()` and `ENSEMBLE_STATES` stood here and are gone with the
     section. Nothing else called them: the tally fed the panel and the panel's collapse badge,
     and both are removed. `wireEnsembleScatter()` and `ensembleEstimatedCount()` are removed
     at their own sites below for the same reason.

     THE CSS IS DELIBERATELY LEFT IN PLACE, on Run 74's precedent when the Signal Web sphere
     came out: `.chart3d-btn`, `.chart3d-wrap` and the panel rules are not provably unique to
     this section, and removing a shared rule to tidy up is how a removal restyles something the
     owner did not ask to change. Dead CSS renders nothing.

     NOTHING ELSE MOVES. Every other section keeps its id, its order and its sessionStorage
     open/closed key, so a saved open state survives this removal. */

  /* ============================================================
     Period Comparison — read-only longitudinal view over the
     project's already-stored history snapshots (project.history)
     and milestone-trend snapshots (project.milestoneHistory). Never
     recomputes anything; only reads what's already on the loaded
     project object. Delta table for the last two periods + small
     inline-SVG sparklines (CPI/SPI/docRisk) across every stored
     period, matching the house inline-SVG style used in deepdive.js
     (svgo()-style viewBox + <polyline>).
     ============================================================ */
  // Sorted, read-only view of project.history — deliberately does NOT call
  // LinSignals.buildHistorySnapshot() (that recomputes/mutates); this section
  // is read-only by contract.
  function storedHistory(project) {
    return (Array.isArray(project && project.history) ? project.history.slice() : [])
      .filter((h) => h && h.period)
      .sort((a, b) => String(a.period).localeCompare(String(b.period)));
  }
  function pcArrow(delta) {
    if (delta == null || !Number.isFinite(delta) || Math.abs(delta) < 1e-9) return "no change";
    return delta > 0 ? "▲" : "▼";
  }
  function pcNum(v) {
    if (v == null || v === "") return null;
    const n = Number(v);
    return Number.isFinite(n) ? n : null;
  }
  function pcFmt(v, digits) {
    if (v == null) return "not recorded";
    return v.toFixed(digits == null ? 2 : digits);
  }
  // Red-module count from a history snapshot. buildHistorySnapshot() (the
  // legacy shape) stores a fixed module_results map keyed by module id, not
  // every module — count Red across whatever module_results the snapshot
  // actually carries. buildCategorySnapshot()'s richer shape stores a
  // summary.by_status.Red tally directly — prefer that when present since
  // it's computed from the full per-category module list.
  function pcRedCount(snapshot) {
    if (!snapshot) return null;
    if (snapshot.summary && snapshot.summary.by_status && Number.isFinite(snapshot.summary.by_status.Red)) {
      return snapshot.summary.by_status.Red;
    }
    const mr = snapshot.module_results;
    if (!mr || typeof mr !== "object") return null;
    let n = 0;
    Object.keys(mr).forEach((k) => {
      const r = mr[k];
      const st = r && (r.status || r.status_color || r.state);
      if (normalizeStatus(st) === "Red") n++;
    });
    return n;
  }
  function pcStatus(snapshot) {
    if (!snapshot) return null;
    return (snapshot.governance && snapshot.governance.state) || null;
  }
  // Same date-diff / mean-slip logic as LinSimulations.runMilestoneTrend
  // (simulations.js), applied to the last two project.milestoneHistory
  // snapshots — kept identical on purpose so the two surfaces never disagree.
  function pcMilestoneMeanSlip(milestoneHistory) {
    const mh = Array.isArray(milestoneHistory) ? milestoneHistory : [];
    if (mh.length < 2) return null;
    const latest = mh[mh.length - 1], prev = mh[mh.length - 2];
    const validDate = (v) => { const d = new Date(v); return isNaN(d.getTime()) ? null : d; };
    const prevByName = {};
    ((prev && prev.milestones) || []).forEach((m) => {
      if (m && m.name && validDate(m.forecast)) prevByName[m.name] = validDate(m.forecast);
    });
    let matched = 0, sumSlip = 0;
    ((latest && latest.milestones) || []).forEach((m) => {
      if (!m || !m.name) return;
      const lf = validDate(m.forecast), pf = prevByName[m.name];
      if (!lf || !pf) return;
      matched++;
      sumSlip += Math.round((lf.getTime() - pf.getTime()) / 86400000);
    });
    if (!matched) return null;
    return sumSlip / matched;
  }
  function pcDeltaRow(label, prevVal, curVal, digits, suffix) {
    const p = pcNum(prevVal), c = pcNum(curVal);
    const delta = (p != null && c != null) ? c - p : null;
    return `<tr>
        <td class="pc-metric">${esc(label)}</td>
        <td class="pc-val">${p == null ? "not recorded" : pcFmt(p, digits) + (suffix || "")}</td>
        <td class="pc-val">${c == null ? "not recorded" : pcFmt(c, digits) + (suffix || "")}</td>
        <td class="pc-arrow">${pcArrow(delta)}</td>
        <td class="pc-delta">${delta == null ? "not recorded" : (delta > 0 ? "+" : "") + pcFmt(delta, digits) + (suffix || "")}</td>
      </tr>`;
  }
  function pcDeltaRowText(label, prevVal, curVal) {
    const changed = prevVal !== curVal;
    const arrow = !changed ? "same" : "▲"; // status is categorical — ▲ just flags "changed"
    return `<tr>
        <td class="pc-metric">${esc(label)}</td>
        <td class="pc-val">${esc(prevVal == null ? "not recorded" : String(prevVal))}</td>
        <td class="pc-val">${esc(curVal == null ? "not recorded" : String(curVal))}</td>
        <td class="pc-arrow">${arrow}</td>
        <td class="pc-delta">${changed ? esc((prevVal == null ? "not recorded" : prevVal) + " → " + (curVal == null ? "not recorded" : curVal)) : "no change"}</td>
      </tr>`;
  }
  // Small hand-rolled inline-SVG sparkline (house style — see deepdive.js
  // svgo()/<polyline> pattern). No chart libraries.
  function pcSparkline(values, color, label) {
    const pts = values.map((v, i) => ({ i, v })).filter((p) => p.v != null);
    const W = 160, H = 36, PAD = 3;
    if (pts.length < 2) {
      return `<svg viewBox="0 0 ${W} ${H}" class="pc-spark" role="img" aria-label="${esc(label)}, insufficient points">` +
        `<text x="${W / 2}" y="${H / 2 + 4}" text-anchor="middle" class="pc-spark-empty">n/a</text></svg>`;
    }
    const vals = pts.map((p) => p.v);
    const lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals);
    const span = hi - lo || 1;
    const n = values.length;
    const x = (i) => PAD + (i * (W - 2 * PAD)) / Math.max(1, n - 1);
    const y = (v) => H - PAD - ((v - lo) / span) * (H - 2 * PAD);
    const points = pts.map((p) => `${x(p.i).toFixed(1)},${y(p.v).toFixed(1)}`).join(" ");
    return `<svg viewBox="0 0 ${W} ${H}" class="pc-spark" role="img" aria-label="${esc(label)} sparkline across ${pts.length} periods">` +
      `<polyline points="${points}" fill="none" stroke="${color}" stroke-width="2"></polyline>` +
      `</svg>`;
  }
  function periodComparisonHtml(project) {
    const hist = storedHistory(project);
    if (hist.length < 2) {
      return `<section class="panel detail-periods" aria-label="Period comparison">
        <p class="kn-sub">Longitudinal view unlocks after two reporting periods.</p>
      </section>`;
    }
    const prev = hist[hist.length - 2];
    const cur = hist[hist.length - 1];
    const prevSi = prev.signal_inputs || {};
    const curSi = cur.signal_inputs || {};
    const prevRed = pcRedCount(prev);
    const curRed = pcRedCount(cur);
    const mh = Array.isArray(project.milestoneHistory) ? project.milestoneHistory : [];
    const prevMh = mh.slice(0, Math.max(0, mh.length - 1));
    const curSlip = pcMilestoneMeanSlip(mh);
    const prevSlip = pcMilestoneMeanSlip(prevMh);
    const rows =
      pcDeltaRow("CPI", prevSi.cpi, curSi.cpi, 2, "") +
      pcDeltaRow("SPI", prevSi.spi, curSi.spi, 2, "") +
      pcDeltaRow("Doc-risk score", prevSi.docRiskScore, curSi.docRiskScore, 2, "") +
      pcDeltaRowText("Status", pcStatus(prev), pcStatus(cur)) +
      pcDeltaRow("Red modules", prevRed, curRed, 0, "") +
      pcDeltaRow("Milestone mean slip", prevSlip, curSlip, 1, "d");
    const cpiSeries = hist.map((h) => pcNum(h.signal_inputs && h.signal_inputs.cpi));
    const spiSeries = hist.map((h) => pcNum(h.signal_inputs && h.signal_inputs.spi));
    const docSeries = hist.map((h) => pcNum(h.signal_inputs && h.signal_inputs.docRiskScore));
    const redModuleNote = (prevRed == null || curRed == null)
      ? `<p class="kn-sub pc-note">Red-module count: this project's stored snapshots don't carry a full per-module status array for one or both periods, so the count above may be a partial approximation of what was actually stored (not a fabricated figure).</p>`
      : "";
    return `<section class="panel detail-periods" aria-label="Period comparison">
      <p class="eyebrow">Last two reporting periods: <span class="mod-mono">${esc(prev.period)}</span> → <span class="mod-mono">${esc(cur.period)}</span></p>
      <table class="pc-table">
        <thead><tr><th>Metric</th><th>${esc(prev.period)}</th><th>${esc(cur.period)}</th><th></th><th>Δ</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
      ${redModuleNote}
      <p class="eyebrow pc-spark-head">Trend across ${hist.length} stored periods</p>
      <div class="pc-spark-grid">
        <div class="pc-spark-cell"><span class="pc-spark-label">CPI</span>${pcSparkline(cpiSeries, "var(--clear-green)", "CPI")}</div>
        <div class="pc-spark-cell"><span class="pc-spark-label">SPI</span>${pcSparkline(spiSeries, "var(--radar-amber)", "SPI")}</div>
        <div class="pc-spark-cell"><span class="pc-spark-label">Doc risk</span>${pcSparkline(docSeries, "var(--alarm-red)", "Doc risk")}</div>
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
    if (!iso || isNaN(d)) return "not recorded";
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
  // Fields extracted for one document. The server's `signals_extracted` event records only
  // docType/fileName/period (see documents.py: it never carried an applied-fields array), so a
  // server-computed project has no per-event field list. Reconstruct it from the STORED
  // signal_inputs.sources ledger, which maps each extracted field to the document TYPE it came
  // from — the honest per-document attribution available. Prefer an explicit per-event array on
  // the rare legacy record that still carries one.
  function uploadedDocFields(e, srcByDocType) {
    const src = e.appliedFields != null ? e.appliedFields
              : e.applied != null ? e.applied
              : (e.fields != null ? e.fields : e.field);
    // RUN 74. AN EVENT THAT CARRIES A documentId IS AUTHORITATIVE FOR ITS OWN DOCUMENT.
    // The server writes `appliedFields` from the observation store at upload, per document, so
    // for such an event the array IS the answer — including when it is empty, which means this
    // document stored no figure. Falling through to the doc-TYPE ledger below would then paint
    // a sibling document's fields onto a row that stored nothing, which is the reverse of the
    // defect this run was sent to fix. Events written before this run carry no documentId and
    // keep the old fallback.
    if (e.documentId && Array.isArray(src)) return src.filter(Boolean);
    if (Array.isArray(src) && src.length) return src.filter(Boolean);
    if (src != null && src !== "" && !Array.isArray(src)) return [src];
    const key = String(e.docType || "").toLowerCase();
    return (srcByDocType && srcByDocType[key]) ? srcByDocType[key].slice() : [];
  }
  // Partial ONLY when the extraction record itself says so — an explicit missing/partial flag.
  // The absence of a per-event field array is a recording gap in the event log, NOT evidence
  // that extraction returned a subset, so it must never on its own brand a document "partial"
  // (that was the defect: every server document read "partial" because the event carried no
  // fields). A document with fields attributed from the stored ledger reads as recorded.
  function uploadedDocIsPartial(e, fields, hasStoredInputs) {
    const missing = e.missing != null ? e.missing : e.missingFields;
    if (Array.isArray(missing) && missing.length) return true;
    if (e.partial === true || e.readyToRun === false) return true;
    // No fields for this document AND nothing extracted for the project at all → genuinely
    // awaiting/empty. If the project HAS stored inputs, absence here is only the event-log gap.
    return (fields || []).length === 0 && !hasStoredInputs;
  }
  // {docTypeLower: [field, …]} from the stored signal_inputs.sources ledger. "sources" maps
  // field → {docType, value}; invert it to a per-docType field list, preserving order.
  function sourcesByDocType(project) {
    const row = (window.LinResults && LinResults.rowFor(project)) || null;
    const si = (row && row.signal_inputs) || (project && project.signalInputs) || null;
    const sources = si && si.sources && typeof si.sources === "object" ? si.sources : null;
    const out = {};
    if (!sources) return out;
    Object.keys(sources).forEach((field) => {
      const s = sources[field];
      const dt = s && s.docType ? String(s.docType).toLowerCase() : null;
      if (!dt) return;
      (out[dt] || (out[dt] = [])).push(field);
    });
    return out;
  }
  function uploadedDocsPanelHtml(project) {
    const evs = uploadedDocEvents(project).slice().reverse(); // newest first
    const srcByDocType = sourcesByDocType(project);
    const hasStoredInputs = storedInputFieldCount(project) > 0;
    const rows = evs.map((e) => {
      const fields = uploadedDocFields(e, srcByDocType);
      const partial = uploadedDocIsPartial(e, fields, hasStoredInputs);
      const fileName = e.fileName || e.file || e.name || "not recorded";
      const at = e.at || e.timestamp || e.recordedAt || e.time || "";
      const fieldList = fields.length ? fields.join(", ") : "not recorded";
      const pill = partial
        ? `<span class="pill pill-amber up-pill" title="Some expected fields were missing">partial</span>`
        : `<span class="pill pill-green up-pill" title="Fields extracted and on file">✓</span>`;
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
        <p class="eyebrow">Documents: ${evs.length} ${evs.length === 1 ? "document" : "documents"}</p>
        ${body}
      </section>`;
  }
  // Compact "what's already on file" note for the ingest panel, so the PM can
  // see existing documents before uploading again.
  /* ============================================================
     Status provenance trace ("why this status") — quality pack.
     Pure read of already-stored data (project.status, category/module
     statuses derived from the stored simulationSignals/signals, and
     signalInputs.sources[field].docType/.at) — never recomputes.
     Walks: project status → worst category (getCategoryStatus) →
     worst module in it (getModuleStatus) → its evidence_metric →
     the source document that fed the module's required input(s).
     ============================================================ */
  const PROV_RANK = { Red: 0, Amber: 1, Yellow: 2, Green: 3, Complete: 4 };
  function provRank(s) { const n = PROV_RANK[normalizeStatus(s)]; return n == null ? 9 : n; }

  // Best-effort extraction of the one number worth surfacing inline from an
  // evidence_metric sentence (e.g. "...doc risk 0.46)" → "0.46"). Falls back
  // to null (the one-liner omits the parenthetical) rather than guessing.
  function firstMetricNumber(evidenceMetric) {
    if (!evidenceMetric) return null;
    const m = String(evidenceMetric).match(/(-?\d+(?:\.\d+)?)/);
    return m ? m[1] : null;
  }

  function sourceForModule(project, module) {
    const si = project.signalInputs || {};
    const required = module.required || [];
    for (let i = 0; i < required.length; i++) {
      const raw = si.sources && si.sources[required[i]];
      const entry = Array.isArray(raw) ? raw[raw.length - 1] : raw;
      if (entry && entry.docType && entry.docType !== "derived") {
        return { field: required[i], docType: entry.docType, at: entry.at || null, fileName: entry.fileName || null };
      }
    }
    // No non-derived source found — fall back to ANY source (including a
    // derived estimate) so the trace still points somewhere, flagged as such.
    for (let i = 0; i < required.length; i++) {
      const raw = si.sources && si.sources[required[i]];
      const entry = Array.isArray(raw) ? raw[raw.length - 1] : raw;
      if (entry) return { field: required[i], docType: entry.docType || "unknown", at: entry.at || null, derived: entry.docType === "derived" };
    }
    return null;
  }

  function buildProvenanceTrace(project) {
    if (!project || !window.LIN_CATEGORIES || typeof window.getCategoryStatus !== "function") return null;
    const projStatus = project.status ||
      (window.getProjectFusion ? ((window.getProjectFusion(project) || {}).status) : null);
    if (!projStatus) return null;

    // Was `LIN_CATEGORIES.filter((c) => !c.parked)` on the fallback arm, which leaks Portfolio
    // Health: it is portfolio-level but it is NOT parked, so `!parked` keeps it. `projectCats`
    // filters on what actually matters, which is the level.
    const cats = projectCats();
    let worstCat = null, worstCatStatus = null, worstCatRank = 99, catTieCount = 0;
    cats.forEach((c) => {
      const st = window.getCategoryStatus(c.id, project);
      if (!st) return;
      const r = provRank(st);
      if (r < worstCatRank) { worstCatRank = r; worstCat = c; worstCatStatus = st; catTieCount = 1; }
      else if (r === worstCatRank) { catTieCount++; }
    });
    if (!worstCat) return null;

    /* ------------------------------------------------------------------------------------
       RUN 69, SECTION 7.1. THE DRIVING MODULE IS READ, NOT RANKED.

       WHAT THIS BLOCK USED TO DO: it walked every module in the category, ranked their status
       strings in the browser, and named the most adverse one as the driver of the category's
       status. That is the client deciding something the server had already decided. The server
       fuses each category from its VOTING modules and stores the answer AND ITS AUTHORS:
       `category_statuses[key].status_set_by` is the list of module ids that actually set the
       status. Run 44 patched the symptom here -- `modDrives` refuses to name a module better
       than the severity it is offered as the driver of -- because the ranking could name a
       module that had no part in setting the status at all. The ranking is now gone and the
       stored list is read instead, so there is nothing left for that patch to catch.

       WHERE THE STORED ROW CARRIES NO `status_set_by` (a row computed before it was written),
       NO MODULE IS NAMED. The trace keeps its project and category hops and its document hop,
       and the module hop is simply absent. A hop omitted is a true account; a hop filled by a
       browser-side ranking is not. ------------------------------------------------------ */
    const provRow = (window.LinResults && LinResults.rowFor(project)) || null;
    const provCat = (provRow && provRow.category_statuses
                     && provRow.category_statuses[worstCat.key]) || null;
    const setBy = (provCat && Array.isArray(provCat.status_set_by)) ? provCat.status_set_by : [];
    let worstMod = null, worstModStatus = null, modTieCount = setBy.length;
    if (setBy.length) {
      const driverId = setBy[0];
      (worstCat.modules || []).forEach((m) => {
        if (worstMod) return;
        // The taxonomy row carries its own module id; `METHOD_TO_MODULE_ID` in taxonomy.js is
        // built from exactly this field, so reading it here is the same lookup without a new
        // export.
        if (m.module_id === driverId) {
          worstMod = m;
          worstModStatus = window.getModuleStatus
            ? window.getModuleStatus(m.method_class, project) : null;
        }
      });
    }
    // THE MODULE HOP IS OPTIONAL NOW. The category and document hops stand on their own, so a
    // project whose stored row names no author still gets its trace.
    const simResult = worstMod && window.getModuleResult
      ? window.getModuleResult(worstMod.method_class, project) : null;
    // THE SENTENCE IS THE ONE THE SERVER STORED. It was read off
    // `project.simulationSignals.signal_array`, which a server-computed project does not carry
    // at all, so this line was silently null on every stored-row project.
    const evidenceMetric = simResult ? (simResult.evidence_metric || null) : null;
    const source = worstMod ? sourceForModule(project, worstMod) : null;

    // Every OTHER Red/Amber module across the whole project (not just the
    // worst category), for the "also elevated: …" list.
    const otherFlags = [];
    projectCats().forEach((c) => {
      if (c.parked) return;
      (c.modules || []).forEach((m) => {
        if (worstMod && m.method_class === worstMod.method_class) return;
        const st = window.getModuleStatus ? window.getModuleStatus(m.method_class, project) : null;
        if (!st || st === "NA") return;
        const n = normalizeStatus(st);
        if (n === "Red" || n === "Amber") otherFlags.push({ cat: c, module: m, status: n });
      });
    });
    otherFlags.sort((a, b) => provRank(a.status) - provRank(b.status));

    // RUN 69. `modDrives` is now simply WHETHER THE SERVER NAMED A MODULE. Run 44's severity
    // comparison guarded against a ranking that could offer a Green module as the driver of an
    // Amber category; there is no ranking left to guard.
    const modDrives = !!worstMod;

    return {
      projStatus, worstCat, worstCatStatus, catTieCount,
      worstMod, worstModStatus, modTieCount, modDrives,
      evidenceMetric, source, otherFlags
    };
  }

  function provenanceLineHtml(project) {
    const t = buildProvenanceTrace(project);
    if (!t) return "";
    const metricNum = firstMetricNumber(t.evidenceMetric);
    const docLabel = t.source
      ? ((window.LinSignals && LinSignals.DOC_TYPE_LABEL && LinSignals.DOC_TYPE_LABEL[t.source.docType]) || t.source.docType)
      : null;
    const docDate = t.source && t.source.at ? (window.LinTZ ? LinTZ.format(t.source.at) : String(t.source.at).slice(0, 10)) : null;
    const tieNote = t.catTieCount > 1 ? " and " + (t.catTieCount - 1) + " other" + (t.catTieCount - 1 === 1 ? "" : "s") : "";
    const parts = [
      esc(t.projStatus) + ", driven by " + esc(t.worstCat.name) + tieNote
    ];
    if (t.modDrives) {
      parts.push(esc(t.worstMod.name) + (metricNum ? " (" + esc(metricNum) + ")" : ""));
    }
    if (docLabel) {
      parts.push(esc(docLabel) + (docDate ? " " + esc(docDate) : "") + (t.source.derived ? " [est.]" : ""));
    }
    const oneLine = parts.join(" → ");
    const hasDetail = !!(t.evidenceMetric || t.otherFlags.length);
    return `<p class="det-prov" data-detail-provenance>
      <span class="det-prov-line">${oneLine}</span>
      ${hasDetail ? `<button type="button" class="dd-link det-prov-toggle" aria-expanded="false">why?</button>` : ""}
      <span class="det-prov-panel" hidden>${provenancePanelHtml(t)}</span>
    </p>`;
  }

  function provenancePanelHtml(t) {
    const rows = [];
    rows.push(`<div class="det-prov-hop"><b>Project</b>: ${esc(t.projStatus)}</div>`);
    rows.push(`<div class="det-prov-hop"><b>${esc(t.worstCat.name)}</b>: ${esc(normalizeStatus(t.worstCatStatus) || t.worstCatStatus)}${t.catTieCount > 1 ? ` (tied with ${t.catTieCount - 1} other ${t.catTieCount - 1 === 1 ? "category" : "categories"} at this severity, shown first)` : ""}</div>`);
    if (!t.modDrives) {
      // RUN 69. The server's stored row names no module as having set this category's status,
      // so none is named. The browser does not pick one by ranking.
      rows.push(`<div class="det-prov-hop"><b>Modules</b>: the stored result does not record which module set this category's status, so none is named as driving it.</div>`);
    } else {
      rows.push(`<div class="det-prov-hop"><b>${esc(t.worstMod.name)}</b>: ${esc(normalizeStatus(t.worstModStatus) || t.worstModStatus)}${t.modTieCount > 1 ? ` (with ${t.modTieCount - 1} other module${t.modTieCount - 1 === 1 ? "" : "s"} recorded as setting this status, shown first)` : ""}${t.evidenceMetric ? `<div class="kn-sub">${esc(t.evidenceMetric)}</div>` : ""}</div>`);
    }
    if (t.source) {
      const docLabel = (window.LinSignals && LinSignals.DOC_TYPE_LABEL && LinSignals.DOC_TYPE_LABEL[t.source.docType]) || t.source.docType;
      const docDate = t.source.at ? (window.LinTZ ? LinTZ.format(t.source.at) : String(t.source.at).slice(0, 10)) : "date unknown";
      rows.push(`<div class="det-prov-hop"><b>Source</b>: ${esc(docLabel)}${t.source.fileName ? " (" + esc(t.source.fileName) + ")" : ""}, ${esc(docDate)}${t.source.derived ? " (estimated field, not a direct extraction)" : ""}</div>`);
    } else {
      rows.push(`<div class="det-prov-hop"><b>Source</b>: no traceable document for this module's inputs.</div>`);
    }
    if (t.otherFlags.length) {
      const shown = t.otherFlags.slice(0, 6);
      const extra = t.otherFlags.length - shown.length;
      rows.push(`<div class="det-prov-also"><b>Also elevated:</b> ` +
        shown.map((f) => esc(f.module.name) + " (" + esc(f.status) + ")").join(", ") +
        (extra > 0 ? ", and " + extra + " more" : "") + `</div>`);
    }
    return rows.join("");
  }

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
    // Stamp the project this render is for, so an in-flight primeAndRefresh for a previously
    // opened project cannot apply its result to this one (see currentRenderId).
    currentRenderId = id;
    // render() replaces the whole subtree, so any globe from a previous project would lose its
    // container while keeping its WebGL context. Release it before the DOM goes.
    if (detailGlobe) { try { detailGlobe.destroy(); } catch (e) {} detailGlobe = null; }
    const p = (window.LinStore ? LinStore.getCached(id) : null) ||
              LIN_PROJECTS.find((x) => x.id === id);
    if (!p) {
      root.innerHTML = `<p class="pr-empty">Project not found (it may have been archived). <button class="btn small" data-back>Back to Portfolio</button></p>`;
      wireBack(root);
      return;
    }

    // T12b. The top-line "State:" badge, the most visible status text on this page. It used to
    // gate on hasSignals(p) — the legacy blob — and say the retired "Awaiting ingest" when that
    // blob was absent, even for a project the server had already analysed. deriveHealthState()
    // already reads the stored row and already returns "Awaiting analysis" honestly when there
    // is none, so it needs no gate at all; asking it directly is both simpler and correct.
    const state = (typeof deriveHealthStateLabel === "function") ? deriveHealthStateLabel(p) : deriveHealthState(p);
    // `populated` used to be hasSignals(p), the legacy blob. Its meaning now is "this project
    // has a stored computed result" — the same gate stateKey and the provenance line need,
    // because buildProvenanceTrace reads the stored row through getProjectFusion.
    const populated = !!(window.LinResults && LinResults.hasResult(p));
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
    // RUN 79, PART C. `simArr`, `ensActive` and `ensEst` computed the Ensemble Analysis
    // collapse badge and are removed with the section. They had no other reader.
    const uploadCount = (typeof uploadedDocEvents === "function") ? uploadedDocEvents(p).length : 0;
    const inputFieldCount = Object.keys(p.signalInputs || {})
      .filter((k) => k !== "sources" && p.signalInputs[k] != null && p.signalInputs[k] !== "").length;
    // RUN 16, WORKSTREAM A5 AND A2. These two are REGISTRY counts, not this project's activity:
    // how many categories and project modules the platform declares. They used to be badged as
    // "11 categories" and "96 modules" beside a project that had computed nothing, which reads
    // as a tally of what ran. The figures are unchanged and still derived from the taxonomy
    // rather than typed in; the word beside them now says which kind of number they are.
    /* RUN 90. THE TWO CHART BADGES COUNT WHAT THOSE TWO CHARTS ACTUALLY DRAW.
       Both charts now render the six weighted performance categories only (owner's ruling,
       Run 90 section 2), so a badge reading "11 in service" over a chart showing six, and
       "60 in service" over a chart showing 42, states a population the reader cannot find.
       Derived from the same accessor the charts use -- never a typed number. */
    const chartCats = (typeof window.performanceCategories === "function")
      ? window.performanceCategories()
      : projectCats().filter((c) => c && c.group === "A");
    const chartCatCount = chartCats.length;
    const chartModuleCount = chartCats.reduce((n, c) => n + ((c && c.modules) || []).length, 0);

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
           ${/* RUN 61, SECTION 4.4. NAMED HOST so the line can be rebuilt when the row arrives. */""}
           <div data-provenance-host>${populated ? provenanceLineHtml(p) : ""}</div>
         </div>
         <div class="detail-head-actions">
           <button class="btn small primary detail-upload" data-upload="${esc(p.id)}">Upload documents</button>
           ${/* Part 5. Computation is a separate, manual action, and until now the only control
                that started it was the Workspace panel's per-period button. This page could
                upload and extract every document a project had and still read "Awaiting
                analysis", because nothing here could ask for the analysis. This asks for every
                period the project holds documents for, oldest first.

                NOT GATED ON window.confirm. A browser that suppresses dialogs returns false
                from it, and the platform has already lost one action that way. The button
                reports what it did instead of asking permission first. */""}
           <button class="btn small detail-compute-all" data-compute-all="${esc(p.id)}">Generate signals for every period</button>
           ${/* RUN 71. DOCUMENT CONTROL. The owner's specified placement: a document control
                button on the project detail page. It sits THIRD in this panel, after "Upload
                documents" and "Generate signals for every period", which puts the three in
                lifecycle order — put documents in, compute from them, withdraw one and compute
                again.

                NO SECOND RECOMPUTE CONTROL IS ADDED. §2 item 5's "recalculate button" is
                `.detail-compute-all`, immediately above: it calls `projectcomputeall`, which
                runs `projectcompute` per period against the period's CURRENT live document set
                and reports which periods recomputed and why. Archiving removes a document from
                that set, so `_period_is_stale` finds the period stale and it recomputes rather
                than skipping. Adding a second server-side recompute here would be the third
                duplicate-control pair this platform has had to resolve.

                The dialog is built by LinIngest.openDocumentControl(id) — the same shape
                `.detail-upload` uses to reach LinIngest.openUploadModal(id) — because it needs
                ingest.js's module-private confirmDestructive(). See wireDocumentControl(). */""}
           <button class="btn small detail-doc-control" data-doc-control="${esc(p.id)}">Document control</button>
           ${/* RUN 57, PHASE A. `.detail-reset` ("Clear stored signals for this project") AND ITS
                aria-live SPAN ARE REMOVED. It and `.pe-reset` in the admin panel below were two
                controls on this one page that both cleared stored signals, and Run 56 measured
                that NEITHER was a superset of the other, so neither could be removed on its own
                without losing behaviour. The owner's Run 57 ruling merges the two handler bodies
                into ONE control doing the UNION and removes the other. The union lives on
                `.pe-reset` in ingest.js, which now also calls LinResults.clear(), re-fetches
                through LinStore.getProject into LIN_PROJECTS, forces the in-memory record to
                awaiting-ingest and calls LinDetail.render(id) -- everything this handler did --
                and asks before acting, which this one never did. */""}
           <span class="detail-compute-all-msg kn-sub" aria-live="polite"></span>
         </div>
         ${/* RUN 55, PHASE A. THE SIX ADMIN CONTROLS LIVE HERE NOW.
              Run 54 phase C re-bound Manage to openDetail() and removed Open, which left the
              inline admin accordion on the portfolio row with no entry point and took six
              operational controls with it: Save info, Upload documents, Recompute this project,
              Reset signals, Archive and Close. The owner's ruling at section 6 of the Run 55
              order is that all six belong on the detail page of the project being viewed.

              THE PANEL IS MOVED, NOT REBUILT. This host is empty markup; the panel inside it is
              built by LinIngest.openInlineManage(id, host) -- the same function, the same
              markup, the same six handlers -- with this element as the parent instead of the
              row's <li>. Every handler is closed over THIS page's project id, taken from
              render()'s own `p.id`, so each control acts on the project being viewed and no
              other. See wireDetailAdmin() below. */""}
         <div class="detail-admin-host" data-admin-for="${esc(p.id)}"></div>
       </div>
        ${/* Release 2 · Phase 2 item 9 — section order: Project Signal Network →
             Signal Flow → Executive Brief → Governance Decision → Signal Web →
             Signal Inputs → Ensemble Analysis → Period Comparison. Documents &
             Extracted Signals (not in the named order) is kept adjacent to Signal
             Inputs. sessionStorage keys (the section ids) are unchanged, so saved
             open/closed states survive. */""}
        ${/* T9. The focused globe. A NEW section rather than a replacement: project detail
             never had a map view. First in the order because where a project is is context for
             everything below it, and it collapses like every other section. */""}
        ${/* RUN 76, section 6. THE CATEGORY SPECIFICATION PANEL, immediately above Location,
             which is the owner's ruling and makes it the first section on the page. */""}
        ${cs("d-catspecs", "Category Specifications", categoryPanelHtml(p), false,
             projectCats().length + " categories")}
        ${cs("d-globe", "Location",
             `<div class="detail-globe" data-project-id="${esc(p.id)}"></div>
              <p class="detail-globe-note ws-note"></p>`,
             false, hasCoordsFor(p) ? "located" : "no location")}
        ${cs("d-projnet", "Project Signal Network", `<div class="detail-projnet2d"></div>`, false, chartCatCount + " categories drawn")}
        ${cs("d-neural", "Signal Flow", `<div class="detail-neural-flow" data-project-id="${esc(p.id)}"></div>`, false, `${chartModuleCount} modules drawn`)}
        ${cs("d-brief", "Executive Brief", executiveBriefHtml(p), false, "")}
        ${cs("d-decision", "Governance Decision", `<section class="panel detail-decision" aria-label="Governance decision (project detail)"></section>`, false, pillBadge(overallState))}
        ${cs("d-ledger", "Signal Inputs", `<section class="panel detail-ledger" aria-label="Signal ledger (project detail)"></section>`, false, pillBadge(overallState))}
        ${cs("d-docsignals", "Documents and Extracted Signals",
             uploadedDocsPanelHtml(p) +
             `<section class="panel detail-signals" aria-label="Extracted signals detail"></section>`,
             false, `${uploadCount} doc${uploadCount === 1 ? "" : "s"} · ${inputFieldCount} field${inputFieldCount === 1 ? "" : "s"}`)}
        ${/* RUN 79, PART C, ITEM 2. The `d-ensemble` Ensemble Analysis section stood here,
             between `d-docsignals` and `d-periods`, and is removed on the owner's ruling.
             The two sections either side keep their ids and their adjacency. */""}
        ${cs("d-periods", "Period Comparison", periodComparisonHtml(p), false,
             storedHistory(p).length >= 2 ? `${storedHistory(p).length} periods` : "")}`;

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
      // RUN 79, PART C. The `d-ensemble` lazy initialiser is removed with its section.
      // Period Comparison is fully static HTML (table + inline SVG sparklines)
      // already rendered above — no post-expand work, but kept in lazyInits
      // to follow the same render-on-first-expand idiom as every other section.
      "d-periods": () => {},
      // T9. One instance per mount point: this globe is the detail view's own and does not
      // disturb the portfolio's. Same rules as the portfolio globe — status from the stored
      // row, nothing computed, and never a blank panel.
      "d-globe": () => {
        const host = root.querySelector(".detail-globe");
        const note = root.querySelector(".detail-globe-note");
        if (!host) return;
        if (!hasCoordsFor(p)) {
          // A project with no coordinates gets the no-position state, not an empty sphere
          // spinning over nothing.
          host.innerHTML = "";
          if (note) {
            note.className = "detail-globe-note ws-note ws-geo-warn";
            note.textContent = window.linLocationNote
              ? linLocationNote(p).text
              : "No map position. Add a site address to place this project.";
          }
          return;
        }
        // STREETS ON GOOGLE MAPS WHERE A KEY IS SET, A NOTE WHERE IT IS NOT.
        //
        // The point of this section is to place the project at street level, which needs street
        // data. Google Maps is drawn in the browser from a key the deployment sets in its
        // environment, which the page fetches at /mapconfig rather than reading from any committed
        // file. This is the SAME plumbing (window.LinGMap) the portfolio Map view uses.
        //
        // With no key: no request to Google, and the section says the map is unavailable under the
        // matched-address line — the SAME no-key answer the portfolio gives, so the site does not
        // carry two different no-key behaviours. With a key that fails to load: the note says the
        // street map could not be reached, rather than a broken Google frame. The flat atlas that
        // used to be the no-key fallback here is gone.
        //
        // Releases any map this view previously built, so a detail page rendered before this
        // change does not leave a WebGL/map context behind when it re-renders.
        if (detailGlobe) { try { detailGlobe.destroy(); } catch (e) {} detailGlobe = null; }

        function setLocationNote(extra) {
          if (!note) return;
          // A RETAINED position is drawn and labelled as belonging to the previous address.
          // Drawing it under "Matched to:" would present an old pin as the current one, which
          // is the failure the retention change exists to make visible rather than to hide.
          const ln = window.linLocationNote ? linLocationNote(p) : null;
          const base = ln ? ln.text
            : (p.formattedAddress ? "Matched to: " + p.formattedAddress : "Located.");
          note.className = "detail-globe-note ws-note" + (ln && ln.warn ? " ws-geo-warn" : "");
          note.textContent = extra ? extra + " " + base : base;
        }

        // No key, or the API could not be reached: no map, a note that says so, and the matched
        // address stays beneath. No Google request is made on this path.
        function setMapUnavailable(reason) {
          if (detailGlobe) { try { detailGlobe.destroy(); } catch (e) {} detailGlobe = null; }
          host.classList.remove("detail-globe--gmap");
          host.classList.add("detail-globe--unavailable");
          host.innerHTML = '<div class="detail-globe-unavail">Map unavailable</div>';
          setLocationNote(reason);
        }

        function renderGoogleMap(gmaps) {
          host.classList.remove("detail-globe--unavailable");
          host.classList.add("detail-globe--gmap");
          host.innerHTML = "";
          const inner = document.createElement("div");
          inner.className = "gmap-inner";
          host.appendChild(inner);
          const lat = Number(p.lat), lng = Number(p.lng);
          // Street level. Seventeen shows the block and the surrounding roads, which is the
          // whole reason for the change from the world atlas.
          const map = new gmaps.Map(inner, {
            center: { lat: lat, lng: lng },
            zoom: 17,
            mapTypeControl: false,
            streetViewControl: false,
            fullscreenControl: false,
          });
          try { new gmaps.Marker({ position: { lat: lat, lng: lng }, map: map }); } catch (e) {}
          // Torn down like the globe was, so re-rendering the page does not leak a map.
          detailGlobe = { destroy: function () {
            try { host.classList.remove("detail-globe--gmap"); host.innerHTML = ""; } catch (e) {}
          } };
          setLocationNote();
        }

        getMapConfig().then((cfg) => {
          if (!cfg || !cfg.present || !cfg.apiKey) {
            // No key: no request to Google, and the section says the map is unavailable with the
            // matched address kept beneath — the same no-key answer the portfolio Map view gives.
            setMapUnavailable("The map is unavailable.");
            return;
          }
          ensureGoogleMaps(cfg.apiKey)
            .then((gmaps) => renderGoogleMap(gmaps))
            .catch(() => setMapUnavailable("The map could not be reached."));
        }).catch(() => setMapUnavailable("The map is unavailable."));
      },
      // Uploaded-docs table is already in the section HTML; the extracted-
      // signals panel below it renders on expand.
      // Documents & Extracted Signals. The uploaded-docs table's "Fields extracted" column and
      // its per-document status pill are reconstructed from the stored signal_inputs.sources
      // ledger, which a_get does not deliver — rebuild the whole body here so that once
      // primeAndRefresh grafts the row, re-running this section fills the field lists in and
      // clears the false "partial" pills, and the extracted-inputs panel below reads the stored
      // values rather than "No extracted values cached this session".
      "d-docsignals": () => {
        const body = document.getElementById("body-d-docsignals");
        if (body) body.innerHTML = uploadedDocsPanelHtml(p) +
          `<section class="panel detail-signals" aria-label="Extracted signals detail"></section>`;
        if (window.LinSignals) LinSignals.renderSignalsPanel(root.querySelector(".detail-signals"), p);
      },
      "d-ledger": () => { LinApp.renderLedger(p, root.querySelector(".detail-ledger")); },
      "d-decision": () => { LinApp.renderDecisionCard(p, root.querySelector(".detail-decision")); }
    };
    Object.keys(lazyDone).forEach((k) => { delete lazyDone[k]; });

    wireBack(root);
    wireDetailAdmin(root, p.id);
    wireCategoryPanel(root, p);
    wireProvenanceTrace(root);
    // Initialise any section the session restored as open.
    Object.keys(lazyInits).forEach((secId) => {
      const body = document.getElementById("body-" + secId);
      if (body && body.style.display !== "none") runLazyInit(secId);
    });


    // T13. Fetch the full stored result (module_results + signal_inputs) and graft it onto
    // the project so every surface on this page reads from the same computed row.
    // a_get (called by hydrateFullProject) returns only category_statuses, not module_results,
    // so Signal Ledger and Project Signal Network always showed "No data" for individual modules
    // even when the project had a fully computed result. This call is non-blocking: the page
    // renders immediately with whatever is available, and sections re-draw once the row arrives.
    primeAndRefresh(id, p);
  }

  /* ---------- lazy section initialisation (render-on-first-expand) ---------- */
  let lazyInits = null;
  // The id of the project the detail page is currently rendered for. primeAndRefresh is async, so
  // if the user opens project X and then quickly opens project Y before X's fetch resolves, X's
  // resolution must NOT graft X's row or write X's badges into Y's DOM (the section element ids
  // are shared, so it otherwise would). Every render() stamps this; primeAndRefresh checks it
  // after the await and abandons a resolution the page has moved on from.
  let currentRenderId = null;
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

  // RUN 25, OWNER-DIRECTED, 2026-08-14. The section navigator rail builder and its
  // scroll-spy observer were removed entirely with the rail they built. Sections are
  // reached by their own headers; nothing else consumed the rail.

  /* ---------- fetch full stored result and refresh open sections ----------
     Called at the end of render(). Fetches projectresults (which includes
     module_results and signal_inputs — fields that a_get deliberately omits)
     and grafts them onto project.storedResult so every rowFor() call on this
     page returns a complete row. Re-runs any sections that were already open
     when the fetch completes so they re-read the now-complete row.

     Why graft rather than replace: rowFor(project) prefers project.storedResult
     over ROWS[id]. Replacing storedResult wholesale or nulling it would race with
     any background a_get refresh that re-sets it. Grafting the two missing fields
     is idempotent and safe.
  */
  /* RUN 48, RULING 1. THE PERIOD THIS PAGE OPENS ON IS THE LATEST ONE THAT HAS BEEN COMPUTED.

     It used to be the literal 1. Every panel on this page holds whatever row this one call
     returns -- the key drivers, the abstention reasons, `recommendation_basis` and the
     disagreement findings -- so on a project whose current period is not 1 the whole page
     showed period 1 and said nothing about it.

     THE DETERMINATION IS DERIVED AND IT IS THE SERVER'S. `projectperiods` reads the result
     table and returns `latest_computed_period`: the maximum period holding a LIVE computed
     result. Nothing here assumes the highest period number has results (a period may hold
     documents and never have been computed, and that period is not selected), nothing assumes
     periods are contiguous (1 and 4 with 2 and 3 absent selects 4), and nothing assumes a
     maximum count (a project may run to sixty periods). A project with no computed result in
     any period returns null: this function then returns without a results call and the page
     keeps the empty state render() already produced. No new empty state is invented and no
     error is raised.

     NO CONTROL IS ADDED. This page has no period selector and this run does not give it one;
     what changes is only which row the page opens on. */
  async function currentPeriod(id, tok) {
    let resp;
    try {
      resp = await LinStore.postWithTimeout(
        { action: "projectperiods", id: id, session_token: tok }, 30000
      );
    } catch (e) {
      console.warn("[detail] period determination failed for", id, e && e.message);
      return null;
    }
    if (!resp || resp.ok !== true) return null;
    const latest = resp.latest_computed_period;
    return (latest === null || latest === undefined) ? null : Number(latest);
  }

  async function primeAndRefresh(id, p) {
    if (!window.LinStore || typeof LinStore.postWithTimeout !== "function") return;
    const tok = window.LinAuth ? LinAuth.getToken() : null;
    const period = await currentPeriod(id, tok);
    // No computed result in any period. The page keeps its existing empty state.
    if (period === null) return;
    // The page may have moved to another project while the period call was in flight.
    if (currentRenderId !== id) return;
    let resp;
    try {
      resp = await LinStore.postWithTimeout(
        { action: "projectresults", id: id, period: period, session_token: tok }, 30000
      );
    } catch (e) {
      console.warn("[detail] primeAndRefresh fetch failed for", id, e && e.message);
      return;
    }
    if (!resp || resp.ok !== true || !resp.result) return;
    // The page may have moved to another project while this fetch was in flight. Priming the ROWS
    // cache for this id is still correct and harmless, but grafting onto p, rewriting badges and
    // re-running sections would write this project's data into whatever project is now on screen.
    if (currentRenderId !== id) {
      if (window.LinResults) LinResults.prime(id, resp.result);
      return;
    }

    // Share with taxonomy.js so getModuleStatus / getCategoryStatus work everywhere.
    if (window.LinResults) LinResults.prime(id, resp.result);

    /* Graft missing fields onto storedResult so rowFor(p) returns the complete row.
       storedResult may not exist (project has no computed result yet) — guard each field.

       RUN 69, SECTION 7.3. THE GRAFT NOW REFUSES A DIFFERENT PERIOD'S ROW.

       `resp.result` is the row for `period` -- the LATEST COMPUTED period, chosen by
       `currentPeriod` above -- and `p.storedResult` is the list/get projection, which carries
       its own `period` and need not be the same one. Nothing here compared them, so the served
       row's module_results, signal_inputs, abstentions and source documents were copied onto a
       projection stating a DIFFERENT period, and every `rowFor(p)` afterwards returned one row
       claiming one period and carrying another's modules. That is exactly what Run 61 removed
       from `rowFor` -- a caller asks for a period and receives that period or nothing, never a
       substitute because another was more complete -- reappearing one layer up, at the graft.

       The ROWS cache is primed above with the served row IN ITS OWN PERIOD'S SLOT either way,
       so a page that wants the latest period can still ask for it by number through
       `rowForPeriod`. What is refused here is the SILENT MIXING of two periods in one object. */
    const graftPeriod = (resp.result && resp.result.period != null) ? Number(resp.result.period) : null;
    const projectionPeriod = (p.storedResult && p.storedResult.period != null)
      ? Number(p.storedResult.period) : null;
    const periodsAgree = (graftPeriod === null || projectionPeriod === null)
      ? true : graftPeriod === projectionPeriod;
    if (p.storedResult && !periodsAgree) {
      console.warn("[detail] served row is period " + graftPeriod + " and the projection states period "
        + projectionPeriod + "; not grafting one period's result onto another's row");
    }
    if (p.storedResult && periodsAgree) {
      if (resp.result.module_results && !p.storedResult.module_results) {
        p.storedResult.module_results = resp.result.module_results;
      }
      if (resp.result.signal_inputs && !p.storedResult.signal_inputs) {
        p.storedResult.signal_inputs = resp.result.signal_inputs;
      }
      // RUN 63. `source_documents` — which document versions produced this row — is on the
      // served result (documents.py `_result_view`) and was NOT on the list projection, so
      // `LinResults.rowFor(p).source_documents` came back undefined on every detail page.
      // MEASURED, not read: the Run 63 driver captured `row_source_documents: null` in the
      // browser against a stored row holding seventeen of them. Grafted here for the same
      // reason module_results and signal_inputs are, and by the same guarded shape.
      if (resp.result.source_documents && !p.storedResult.source_documents) {
        p.storedResult.source_documents = resp.result.source_documents;
      }
      // The served basis for the recommendation travels with the row for the same reason the
      // other two fields do: `rowFor` prefers `storedResult`, and the Governance Decision card
      // reads the basis off whatever `rowFor` returns. Without this graft the card fell back to
      // saying the reason was not established on a row whose basis the server had supplied.
      if (resp.result.recommendation_basis && !p.storedResult.recommendation_basis) {
        p.storedResult.recommendation_basis = resp.result.recommendation_basis;
      }
      // THE FOURTH FIELD, AND IT WAS THE ONE THAT MADE THREE RUNS' WORK INVISIBLE. The ledger
      // has code to print a module's own abstention reason under its row, and that code has
      // never run on this page: it reads `row.abstained`, the projection does not carry it,
      // `rowFor` prefers the projection, and so every module that abstained showed a bare
      // "No data" pill and nothing else. Two earlier runs wrote careful sentences saying what
      // each silent module was waiting for, asserted them on the stored row, and recorded that
      // the ledger renders them. The row had them; the page never saw them. Same graft, same
      // reason, as the three fields above.
      if (resp.result.abstained && !p.storedResult.abstained) {
        p.storedResult.abstained = resp.result.abstained;
      }
      // THE FIFTH FIELD, grafted for exactly the reason the four above are: the executive
      // brief and the courses-of-action card both read the served consistency findings off
      // whatever `rowFor` returns, and `rowFor` prefers `storedResult`. Without this graft a
      // disagreement the server had already established would never reach either surface.
      if (resp.result.consistency_findings && !p.storedResult.consistency_findings) {
        p.storedResult.consistency_findings = resp.result.consistency_findings;
      }
      // THE SIXTH FIELD, RUN 91, AND IT MADE RUN 89'S ENTIRE INDETERMINATE BRIEF DEAD CODE.
      // `project_status_basis` -- the required-core verdict, carrying `required_missing` and
      // `required_missing_detail` -- is on the served result (documents.py `_result_view`) and
      // is NOT on the list projection. `rowFor` prefers `storedResult`, so `ev.statusBasis` was
      // null on every detail page, the `basis.official === false` branch in `scriptedBrief`
      // never ran, and the GENERIC branch rendered instead: that is why the brief said "The
      // posture is Indeterminate, set by A1.7 ..." -- naming the three modules that DID report --
      // and never mentioned Cost Risk or Delivery Quality, the categories whose absence caused
      // the status. MEASURED in a real browser at 1280px and 1024px before this graft:
      // `row.project_status_basis` null on the client while the server served the full object.
      // Same graft, same guarded shape, same reason as the five fields above.
      if (resp.result.project_status_basis && !p.storedResult.project_status_basis) {
        p.storedResult.project_status_basis = resp.result.project_status_basis;
      }
    } else if (!p.storedResult) {
      // a_get delivered no storedResult (a race, or the list projection had not attached it
      // yet) but the row exists. Attach it so every rowFor(p) on this page reads the complete
      // row directly, not only through the ROWS cache prime above.
      p.storedResult = resp.result;
    }

    // The collapsed-section badges above each panel were computed at render() from the
    // truncated row (and, for Ensemble, from the retired simulationSignals field the server
    // never writes) so they read "0 active · 0 est." and "N docs · 0 fields". Recompute them
    // from the now-complete row so the summary agrees with the panel it summarises.
    refreshSectionBadges(p);

    // RUN 47. The executive brief panel is assembled during render(), BEFORE this fetch
    // returns, so the disagreement block it carries was built from a row that did not yet hold
    // the served findings. Rebuild that block, and only that block, from the now-complete row.
    // Same reason the badges above are recomputed, and the same scope: it replaces text inside
    // a panel that already exists and touches no control.
    refreshBriefConsistency(p);

    // RUN 61, SECTION 4.4. THE PROVENANCE LINE GETS THE SAME SECOND PASS EVERY OTHER PANEL HAS.
    //
    // It is built inside render()'s innerHTML at detail.js:1047, from whatever row was in hand
    // at that moment, and until now it was the ONE surface on this page that never re-read the
    // row when the correct one arrived. Run 60 measured the consequence directly: the same
    // project rendered twice in one page gave two different drivers, and only the second was
    // right. The first is the one a user gets.
    //
    // With the period rule in taxonomy.js this pass should have nothing to correct -- the first
    // render either has the right row or honestly has none. It is here so that the moment the
    // right row lands, the line is rebuilt from it rather than leaving whatever the first pass
    // produced. Necessary, and on its own not sufficient; that is why both changes exist.
    refreshProvenanceLine(p);

    // A scripted Executive Brief generated before the row arrived would have cached its
    // "No computed key signals are available yet" fallback. Drop that stale scripted brief so the
    // re-run below regenerates it from the now-complete row. A live (chat) brief the user
    // generated is left untouched.
    if (p.executiveBrief && p.executiveBrief.source === "scripted") p.executiveBrief = null;

    // Re-run any sections already open — they rendered before module_results arrived. d-brief and
    // d-decision are included because their key-signal and signal-breakdown sections also read
    // the stored row (they were reading the absent legacy blob before).
    // RUN 79, PART C. "d-ensemble" was in this list and is removed with its section. The other
    // five are untouched and still re-run when they are open.
    const REFRESH_SECTIONS = ["d-ledger", "d-projnet", "d-docsignals",
                              "d-brief", "d-decision"];
    REFRESH_SECTIONS.forEach((secId) => {
      if (!lazyInits || typeof lazyInits[secId] !== "function") return;
      const body = document.getElementById("body-" + secId);
      if (!body || body.style.display === "none") return;
      // Clear the done flag so runLazyInit re-fires.
      delete lazyDone[secId];
      runLazyInit(secId);
    });
  }

  /* Recompute the two collapsed-section badges that summarise stored-row data — the
     Ensemble Analysis "N active · M est." and the Documents "K docs · F fields". Both are
     read straight from the stored computed row (module_results and signal_inputs), so once
     primeAndRefresh has grafted it they can agree with the panels they head. Modules with no
     stored status are abstaining and are counted in neither the active nor the estimated
     tally, matching the abstention rule the panels themselves follow. */
  function refreshBriefConsistency(project) {
    const panel = document.querySelector(".eb-panel");
    if (!panel) return;
    const old = panel.querySelector(".eb-consistency");
    let html = "";
    try { html = briefConsistencyHtml(project); } catch (e) { html = ""; }
    if (old) old.remove();
    if (!html) return;
    // Immediately after the flags block when there is one, otherwise directly under the head,
    // which is where the panel's own template puts it. No control is inserted or moved.
    const anchor = panel.querySelector(".eb-flags") || panel.querySelector(".eb-head");
    if (anchor) anchor.insertAdjacentHTML("afterend", html);
    else panel.insertAdjacentHTML("afterbegin", html);
  }

  // RUN 61, SECTION 4.4. Rebuild the status provenance line from the now-complete row.
  //
  // REPLACES TEXT INSIDE AN ELEMENT THAT ALREADY EXISTS AND MOVES NO CONTROL. The "why?"
  // disclosure is part of the line's own markup, so it is re-emitted in the same place, in the
  // same order, by the same builder, and re-wired by the same `wireProvenanceTrace` render()
  // uses. Its expanded/collapsed state is deliberately NOT carried across: the panel's content
  // is the trace being replaced, and re-showing an old trace inside a rebuilt line would be the
  // same class of error this run exists to remove.
  //
  // Where the rebuilt trace is empty (no module in the driving category has a status on the row
  // the page holds) the line is removed rather than left saying something the row cannot
  // support. An absent claim is honest; a wrong one is not.
  function refreshProvenanceLine(project) {
    const host = document.querySelector("[data-provenance-host]");
    if (!host) return;
    let html = "";
    try { html = provenanceLineHtml(project); } catch (e) { html = ""; }
    host.innerHTML = html;
    if (html) wireProvenanceTrace(host);
  }

  function refreshSectionBadges(project) {
    const setBadge = (secId, html) => {
      const sec = document.getElementById("section-" + secId);
      const badge = sec && sec.querySelector(".collapse-badge");
      if (badge) badge.innerHTML = html;
    };
    // RUN 79, PART C. The `d-ensemble` badge refresh is removed with its section.
    try {
      const uploadCount = (typeof uploadedDocEvents === "function") ? uploadedDocEvents(project).length : 0;
      const fieldCount = storedInputFieldCount(project);
      setBadge("d-docsignals",
        `${uploadCount} doc${uploadCount === 1 ? "" : "s"} · ${fieldCount} field${fieldCount === 1 ? "" : "s"}`);
    } catch (e) { /* non-fatal */ }
  }

  /* The number of extracted signal-input fields on file for this project, read from the
     STORED row's signal_inputs (the value the analytical layer actually consumed), with the
     legacy client-side signalInputs as a fallback for projects that still carry it. "sources"
     is the field ← document provenance ledger, not a signal, so it is never counted. */
  function storedInputFields(project) {
    const row = (window.LinResults && LinResults.rowFor(project)) || null;
    const stored = row && row.signal_inputs && typeof row.signal_inputs === "object" ? row.signal_inputs : null;
    const legacy = project && project.signalInputs && typeof project.signalInputs === "object" ? project.signalInputs : null;
    const src = stored || legacy || {};
    return Object.keys(src).filter((k) => k !== "sources" && src[k] != null && src[k] !== "");
  }
  function storedInputFieldCount(project) {
    return storedInputFields(project).length;
  }
  /* RUN 79, PART C. `ensembleEstimatedCount()` counted for the Ensemble Analysis badge only
     and is removed with it. */

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
      // RUN 44, SECTION 4.2. Number(null) is 0 and finite, so a doc block carrying a null score
      // read as "documents clean". An absent score says nothing about the documents.
      const score = (s.doc.score == null || s.doc.score === "") ? NaN : Number(s.doc.score);
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
        // The KEY dispatches; what goes into the brief is the category's LABEL, which
        // carries no identifier. Before Run 51 this pushed c.num and the brief read
        // "RED (2 categories): A1, A3".
        const label = c && c.name;
        if (!label) return;
        if (c.parked || !c.status) { groups.Conditional.push(label); return; }
        const s = String(c.status).toLowerCase();
        if (s.indexOf("red") >= 0) groups.Red.push(label);
        else if (s.indexOf("amber") >= 0 || s.indexOf("yellow") >= 0) groups.Amber.push(label);
        else if (s.indexOf("green") >= 0 || s.indexOf("complete") >= 0) groups.Green.push(label);
        else groups.Conditional.push(label);
      });
    }
    return groups;
  }

  /* ============================================================
     RUN 69, SECTION 6 AND SECTION 7.2. KEY DRIVERS, READ AND NOT DERIVED.
     ============================================================
     WHAT THIS FUNCTION USED TO DO, AND IT WAS THE DEFECT THE ORDER DESCRIBES: it took raw
     figures out of the stored `signal_inputs` and MADE UP BOTH THE NUMBER AND THE COLOUR.

       · "Contingency burned" was `(originalContingency - remainingContingency) / originalContingency`
         computed here, and its status was `bp > 75 ? Red : bp > 50 ? Amber : Green` — bands
         invented in the browser. The server computes that exact quantity in A3.2 Contingency
         Burn Rate, stores `burn_rate_pct: 55` beside `normalized_burn: 1.1`, and stores
         `status_color: null` WITH ITS REASON: "no source specifies a burn-against-progress
         threshold". So on this platform's own fixture the browser printed an AMBER contingency
         driver for a quantity the server had explicitly refused to band. That is precisely the
         thirty-one bandless ladders being overridden by the client.
       · "P80 EAC vs BAC" was `Math.round((mc.p80 / bac - 1) * 100)`, a percentage no module
         computed and no row stores.
       · CPI, SPI, CUSUM and document risk each carried a band invented from client-side
         thresholds. On the same fixture the stored CPI of 0.952 rendered GREEN here while the
         two modules that actually vote on cost, A1.7 TCPI and A1.8 VAC, both stored AMBER.

     WHAT IT DOES NOW. Every row is a STORED module result: the figure comes from a field the
     module stored, and the colour is that module's stored `status_color` — which is `null`
     wherever the module asserted no band, and a null colour is rendered as no colour rather
     than as Green. A quantity no module stored does not appear.

     The four raw EVM scalars are still shown, because a stored figure read verbatim is exactly
     what section 6 permits, but they now carry NO STATUS AT ALL: no module on this platform
     bands CPI or SPI directly, so this file has none to read and invents none. ---------- */

  //: label -> the module whose stored result supplies the figure and the colour, the field on
  //: that result carrying the figure, and how to print it. Nothing here computes.
  const BRIEF_DRIVERS = [
    { label: "Contingency burned", method: "Contingency_Burn_Rate", field: "burn_rate_pct",
      format: (v) => Math.round(v) + "%" },
    { label: "Contingency against progress", method: "Contingency_Burn_Rate",
      field: "normalized_burn", format: (v) => Number(v).toFixed(2) },
    { label: "TCPI", method: "TCPI", field: "tcpi", format: (v) => Number(v).toFixed(3) },
    { label: "Variance at completion", method: "VAC", field: "vac",
      format: (v) => (v < 0 ? "-$" : "$") + Math.abs(Math.round(v)).toLocaleString("en-US") },
    { label: "P80 EAC", method: "Monte_Carlo", field: "p80_eac",
      format: (v) => "$" + Math.round(v).toLocaleString("en-US") },
  ];

  //: The raw stored scalars. Read verbatim off the row's own `signal_inputs`, printed with no
  //: status, because this platform stores no band for any of them. A raw value that is null or
  //: blank is ABSENT and is omitted -- `Number(null)` is 0 and finite, which is how an absent
  //: document risk once rendered as "0.00 (Green)".
  const BRIEF_SCALARS = [
    { label: "CPI", key: "cpi", digits: 3 },
    { label: "SPI", key: "spi", digits: 3 },
    { label: "Document risk", key: "docRiskScore", digits: 2 },
  ];

  function briefKeySignals(project) {
    const storedRow = (window.LinResults && LinResults.rowFor(project)) || null;
    if (!storedRow) return [];
    const si = (storedRow.signal_inputs && typeof storedRow.signal_inputs === "object")
      ? storedRow.signal_inputs : {};
    const out = [];

    BRIEF_DRIVERS.forEach((d) => {
      const res = window.getModuleResult ? window.getModuleResult(d.method, project) : null;
      if (!res) return;
      const raw = res[d.field];
      if (raw == null || raw === "") return;
      const n = Number(raw);
      if (!Number.isFinite(n)) return;
      out.push({
        label: d.label,
        value: d.format(n),
        // THE MODULE'S OWN STORED BAND, AND NOTHING ELSE. `null` where the module asserted
        // none, which the renderers below print as "no band stated" rather than as a colour.
        status: res.status_color || null,
      });
    });

    BRIEF_SCALARS.forEach((f) => {
      const raw = si[f.key];
      if (raw == null || raw === "") return;
      const n = Number(raw);
      if (!Number.isFinite(n)) return;
      out.push({ label: f.label, value: n.toFixed(f.digits), status: null });
    });

    return out.slice(0, 6);
  }

  //: How a driver reads when the server stored no band for it. A colour is never supplied in
  //: its place, and the absence is stated in words rather than left to look like an omission.
  function briefStatusWords(status) {
    return status ? String(status) : "no band stated";
  }

  function buildBriefPrompt(project) {
    const snapshot = briefSnapshot(project);
    if (!snapshot || !snapshot.categories) {
      console.log("[brief] no stored category snapshot for " + (project && project.id) + ". Skipping chat");
      return null;
    }

    const cats = Object.keys(snapshot.categories).map((k) => snapshot.categories[k]);
    const catSummary = cats
      .filter((c) => !c.parked && c.status)
      .map((c) => {
        const worst = (c.modules || [])
          .filter((m) => m.status)
          .slice()
          .sort((a, b) => statusRank(a.status) - statusRank(b.status))[0];
        // RUN 44, SECTION 4.1 REQUIREMENT 3. The category status is the server's fusion of the
        // two voting modules; this list is every module in service in the category. Nothing
        // required the two to agree, so an Amber category could be offered a Green module as
        // the driver of its Amber. A module that is BETTER than the severity it would be
        // offered as the driver of is not a driver, and is not named.
        const worstDesc = (worst && statusRank(worst.status) <= statusRank(c.status))
          ? " (worst: " + worst.name + (worst.evidence_metric ? ", " + worst.evidence_metric : "") + ")"
          : "";
        // RUN 48, RULING 2. The category identifier is gone from the text sent to the brief's
        // model. NAMING_AUTHORITY.md:96: no module id and no number in user-facing text, and
        // the brief the model writes from this is read by a program director.
        return c.name + ": " + c.status + worstDesc;
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
      "Your role is to present findings from computational analysis and offer considered recommendations, not to command action. " +
      "Opus Gubernatio is a prediction and advisory platform: it presents evidence and surfaces recommendations; it does not issue commands or directives. " +
      "The program director is the decision-maker; you are the advisor.\n\n" +
      "Tone:\n" +
      "- DIPLOMATIC: present findings as evidence, not verdicts.\n" +
      "- ADVISORY: suggest, recommend, consider. Never command or direct.\n" +
      "- RESPECTFUL: the program director is the decision-maker, so acknowledge their judgment.\n" +
      "- MEASURED: match urgency to the evidence. Never amplify beyond what the data supports.\n" +
      "- PRECISE: be specific about what the models found, and deferential about what must happen, because that is the PM's call.\n\n" +
      "USE phrasing such as: 'The computational analysis suggests…', 'The evidence indicates…', " +
      "'The models collectively point to…', 'It may be worth considering…', 'The data supports a closer look at…', " +
      "'The program director may wish to review…', 'The signals are consistent with…', 'One area that warrants attention is…'.\n" +
      "AVOID: 'You must…' / 'The PM must…', 'Immediate action required', 'Recovery plan required', " +
      "'Escalate immediately', 'Critical failure', and any commanding or alarming language. " +
      "Stay diplomatic even for a Red state. For example: 'The evidence across multiple analytical methods consistently points to " +
      "significant cost and schedule pressure. The program director may wish to consider bringing the controls lead into a focused review " +
      "before the next reporting cycle closes.', and NOT 'This project is in critical failure. Recovery plan required within 48 hours.'\n\n" +
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
      ? keySignals.map((k) => "- " + k.label + ": " + k.value + " (" + briefStatusWords(k.status) + ")").join("\n")
      : "- (no computed key signals available yet)";

    return advisor +
      "Briefing subject: " + (snapshot.project_name || project.name) + " (Project " + snapshot.project_id + ", " + (snapshot.sector || "unknown") + " sector). " +
      "The platform computed " + totalModules + " signal modules across " + projectCats().length + " analytical categories from a stored log dated " + computedDay + ".\n\n" +
      "Category statuses grouped by color (internal context, use these groupings, do NOT re-list each category individually):\n" + groupsText +
      "\n\nComputed key signal values (internal context, quote these ACTUAL numbers in Key Drivers):\n" + signalsText +
      "\n\nPer-category worst module (internal context, do NOT quote raw module names or metrics):\n" + catSummary +
      "\n\nOverall governance state: " + (gov.state || "unknown") +
      "\nNamed authority: " + (gov.authority || "unknown") +
      "\nRecommended action on file: " + (gov.action || "unknown") +
      "\nEvidence agreement: " + confText +
      "\n\nWrite the briefing with EXACTLY these four sections, each introduced by its '### ' header line verbatim. " +
      "LEAD WITH THE RECOMMENDATION. The first thing the reader sees is what to do, not a data summary. " +
      "Do NOT print any module identifier or category number anywhere in the briefing: name what a category DOES, in words. A program director thinks in purposes, not in identifiers.\n\n" +
      "### Recommendation\n" +
      "Begin with the overall status in CAPS followed by ' · ' and a single short action clause (e.g. 'RED-REVIEW · bring the controls lead into a focused review this cycle'). " +
      "Then ONE sentence beginning 'The evidence suggests…' that frames the overall picture. Diplomatic and advisory, never a command.\n\n" +
      "### Signal Pattern\n" +
      "Group the categories by status. For each non-empty group, output a line starting with '● ' then the status word in CAPS and the count in parentheses, " +
      "then on the SAME line ': ' followed by a 2-3 sentence synthesis of what those categories have in common and what they indicate. " +
      "List the grouped Cat numbers inside the synthesis once. Order groups RED, then AMBER, then GREEN, then CONDITIONAL / NO DATA. Skip empty groups. " +
      "Do NOT write one line per category. Synthesize the group.\n\n" +
      "### Key Drivers\n" +
      "3-4 bullet points, each line starting with '- ', each naming a SPECIFIC computed signal value from the list above (e.g. '- CPI 0.929 indicates…', " +
      "'- P80 EAC is +10% above BAC…'). Use the actual numbers. These are the signals that most explain the overall status.\n\n" +
      "### Required Actions\n" +
      "2-4 bullet points, each line starting with '- ', each a specific advisory action that NAMES a plausible authority (e.g. controls lead, program director) " +
      "and a sensible horizon (e.g. 'before the next reporting cycle closes'). Use diplomatic advisory language throughout: 'the evidence suggests', " +
      "'the program director may wish to'. Never an imperative command, never an ultimatum, and never 48-hour or recovery-plan language, not even for a Red state.\n\n" +
      "Output ONLY the four sections with the exact '### ' headers above. No preamble and no closing remarks.";
  }

  /* RUN 48, RULING 3. THE BRIEF'S FRIENDLY CATEGORY LABEL MAP IS DELETED. It was a constant
     that no code ever read: Run 47 corrected its retired labels and recorded, in the same
     report, that a repository-wide grep for its name found the definition and no reader
     anywhere. Four runs rediscovered it. It is removed rather than kept corrected, so a fifth
     run does not find it again. The name it was declared under is in the Run 48 report. */

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
      // RUN 51, RULING 4, STOP CONDITION 9.3. This em dash is NOT prose and is NOT ours: it is a
    // PARSER over text the model produced, splitting a Signal Pattern line at whatever
    // separator the model wrote. Replacing it with words would stop the parse. The dash is
    // syntactically significant here, so this instance is STOPPED and reported rather than
    // swept, and the sweep's blanket pass over this file is reverted at this line.
    const dash = line.indexOf("\u2014") >= 0 ? line.indexOf("\u2014") : line.indexOf(" - ");
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
      briefDecisionRouteHtml() +
      `</div>`;
  }

  /* RUN 91, SECTION 3.5. THE ROUTE FROM THE END OF THE BRIEF TO THE DECISION CARD.

     MEASURED BEFORE THIS: the brief's rendered text never used the word decision, and its only
     controls were its own collapse header and Regenerate. The Governance Decision section sits
     on the same page and a participant who read to the end of the brief had nothing to follow.

     WHAT THIS IS AND WHAT IT IS NOT. It is a route to a section that exists on this page --
     `#section-d-decision`, whose heading reads GOVERNANCE DECISION. IT PROMISES NOTHING ABOUT
     WHAT IS INSIDE IT. That restraint is deliberate: `recommendation_options.js` returns
     `available: false` on every current row, and on the fixture row this run measured the card
     renders its heading and a "No data" badge and exposes no controls at all. A sentence here
     claiming the participant can record a judgement would be a claim about a control that is
     not there. So the wording names the destination and stops, and the report says plainly
     where the route lands. */
  function briefDecisionRouteHtml() {
    return '<div class="eb-section eb-decision-route">'
      + '<p class="eb-sec-head">Recording your judgement</p>'
      + '<p class="eb-route-note">Your judgement on this recommendation is recorded on the '
      + 'Governance Decision card, further down this page.</p>'
      + '<button type="button" class="btn small eb-to-decision" data-brief-to-decision="1">'
      + 'Go to the Governance Decision card \u2193</button></div>';
  }

  /* RUN 70, FIX 4. THE SCRIPTED BRIEF IS REBUILT ON THE STORED FIGURES.

     WHAT IT WAS. It read `project.signals`, a legacy blob that is EMPTY on every project this
     server computes, so its `concerns` list was always empty and its prose was chosen from a
     status alone: "The evidence suggests meaningful risk that may warrant a closer look this
     cycle." That sentence asserted a condition about the project and named no figure, which is
     the defect fix 4 exists to close.

     WHAT IT IS NOW. Every sentence it asserts is built FROM a stored figure and prints that
     figure, so it passes the same gate that would reject it. It states, in order: the posture
     and the category and module that set it; the cost position AND the schedule position,
     whichever of them set the posture; the band each figure crossed; the document type each
     figure came from; and what the platform could not compute this period. If nothing computed
     it says so rather than producing a posture from an empty tree.

     NOTHING HERE INVENTS A VALUE. Every number printed is read off the stored row, and where
     the row holds nothing the sentence says the platform did not compute it. */
  function scriptedBrief(project) {
    const ev = briefEvidence(project);

    // NOTHING COMPUTED: say so, and produce no posture from an empty tree.
    if (!ev.row || !ev.modules.length) {
      return [
        "### Recommendation",
        "NO DATA \u00b7 no course is recommended this period.",
        "No module produced a figure for this period, so this platform states no posture and no "
          + "cost or schedule position.",
        "### Signal Pattern",
        "No category has computed data yet.",
        "### Key Drivers",
        "- No computed key signals are available yet.",
        "### Required Actions",
        "- Upload the period's documents so the analysis has something to read"
      ].join("\n");
    }

    /* =====================================================================================
       RUN 89, GOAL THREE. THE INDETERMINATE BRIEF.

       INDETERMINATE IS NOT A BLANK SCREEN AND NOT A FAILURE STATE. When a required category
       carries no posture the server issues Indeterminate, and this branch renders the full
       brief the owner specified: the status and what it means, the reason and what is missing,
       EVERY assessed category and its posture INCLUDING any that are Red, every supporting
       category assessed or not, and a recommendation about EVIDENCE ACQUISITION, verification
       and escalation -- never a fabricated health recommendation.

       IT ESCALATES AN ASSESSED ADVERSE CONDITION RATHER THAN WAITING FOR THE STATUS. Any
       category the row bands Red or Amber is named in the Recommendation, with the module that
       set it and that module's own stated figure, so the reader is not asked to wait for an
       official posture before acting on evidence the platform already holds.

       THE THREE RUN 70 CHECKS ARE NOT WEAKENED AND ARE NOT ROUTED AROUND. This text goes
       through `briefGate` exactly as every other brief does. It is written to PASS them: every
       sentence that asserts a condition names a figure the stored row holds (the setter's own
       `evidence_metric`), and the sentences about missing evidence assert no condition at all
       because "could not be assessed" is a statement about the platform, not about the project.
       ===================================================================================== */
    const basis = ev.statusBasis;
    if (basis && basis.official === false) {
      const missing = basis.required_missing || [];
      const detail = basis.required_missing_detail || [];
      const catByKey = {};
      ev.categories.forEach((c) => { catByKey[c.key] = c; });
      /* The category's name, read from the taxonomy the whole page already reads. Falls back
         to the key rather than to an invented label. */
      const catName = (k) => {
        const c = (window.LIN_CATEGORIES || []).filter((x) => x.key === k)[0];
        return (c && c.name) || k;
      };

      // 1. THE STATUS.
      const iRec = ["INDETERMINATE \u00b7 there is insufficient evidence for an official project "
        + "posture this period, so none is issued."];

      // 2. THE REASON, naming which required category could not be assessed and what is missing.
      detail.forEach((d) => {
        iRec.push(catName(d.category) + " (" + d.category + ") could not be assessed: "
                  + (d.missing || "no reading was produced") + ".");
      });
      if (!detail.length && missing.length) {
        iRec.push("These required categories could not be assessed: " + missing.join(", ") + ".");
      }

      // 5. ESCALATION OF ANY ASSESSED ADVERSE CONDITION, with the setter's own figure so the
      //    sentence names the figure behind it and Check 1 is satisfied by evidence, not by
      //    softening the words.
      /* RUN 91, SECTION 3.4. AN ADVERSE READING IS STATED WITH ITS FIGURE, ITS REACH AND WHAT
         FOLLOWS -- and its reach is stated in BOTH directions.

         WHAT WAS WRONG. On the measured row this branch never ran at all (see the
         `project_status_basis` graft in `primeAndRefresh`), so the GENERIC branch rendered and
         closed with "Routine monitoring appears sufficient this cycle" beside a category the
         row bands Red. The owner's ruling is that a recommendation must state its reason: an
         adverse category is not automatically a project-level threat, and the brief must say
         what the adverse reading is, what it does and does not reach, and what follows.

         THE FIGURE. `evidence_metric` is the setter's own sentence and is frequently null on a
         stored specification reading; where it is, the module's own stored `display` and then
         its stored `value` are used. All three are figures the row holds, so check 1 is
         satisfied by evidence rather than by softening the words. Where the module stored no
         figure at all that is said, and no number is invented for it. */
      const adverse = ev.categories.filter((c) => c.status
        && statusKeyFromText(c.status) !== "green");
      const reqKeys = basis.required_categories || [];
      const supKeys = basis.supporting_categories || [];
      adverse.forEach((c) => {
        const bits = (c.setBy || []).map((mid) => {
          const m = ev.modules.filter((x) => x.module_id === mid)[0];
          if (!m) return mid;
          const fig = (m.evidence_metric != null && m.evidence_metric !== "") ? m.evidence_metric
            : (m.display != null && m.display !== "") ? m.display
            : (m.value != null ? String(m.value) : null);
          return mid + (fig ? " reading " + fig : " which stored no figure");
        });
        const isRequired = reqKeys.indexOf(c.key) >= 0;
        const isSupporting = supKeys.indexOf(c.key) >= 0;
        // RUN 92. THE REASON PRECEDES THE IMPERATIVE. This sentence led with "Escalate
        // now, without waiting for an official posture:" and stated its grounds after it.
        // The owner ruled at Run 92 that a recommendation states its reason before it
        // issues its instruction, so the READING is stated here and the ESCALATION moved
        // to the "What follows" sentence below, after what the reading does and does not
        // reach. The instruction itself is UNCHANGED in force and its literal wording is
        // preserved; only its position moved.
        iRec.push(c.key + " " 
          + catName(c.key) + " reads " + c.status
          + (bits.length ? ", set by " + bits.join("; ") : "") + ".");
        // WHAT IT REACHES, AND WHAT IT DOES NOT. Stated from the basis the server published,
        // not from a judgement made here.
        if (isSupporting) {
          iRec.push("What that reaches: " + c.key + " is a SUPPORTING category, so this reading "
            + "does not set the project status and could not have set it even had the required "
            + "categories all reported. What it does not reach: the required core, which is "
            + (basis.required_assessed || []).join(", ")
            + " assessed and " + missing.join(", ") + " unassessed, so no project-level "
            + "conclusion follows from it either way.");
        } else if (isRequired) {
          iRec.push("What that reaches: " + c.key + " is a REQUIRED category, so this reading "
            + "would contribute to the project status once every required category reports. "
            + "What it does not reach: a project status now, because " + missing.join(", ")
            + " are still unassessed.");
        }
        iRec.push("What follows: Escalate now, without waiting for an official posture. "
          + "Treat this as a category-level finding on " + c.key
          + " and act on it at that level; it is not evidence of a project-level condition, and "
          + "the absence of a project status is not evidence that there is none.");
      });
      if (basis.fused_band) {
        iRec.push("Worst-wins over the categories that did report would have produced "
          + basis.fused_band + "; that band is recorded and is not issued as the official "
          + "status, because the required categories are not all assessed.");
      }

      // 3 AND 4. EVERY ASSESSED CATEGORY AND ITS POSTURE; EVERY SUPPORTING CATEGORY.
      const assessedLines = ev.categories.filter((c) => c.status)
        .map((c) => "\u25cf " + c.key + " " + catName(c.key) + ": " + c.status + ".");
      const notAssessedLines = ev.categories.filter((c) => !c.status)
        .map((c) => "\u25cb " + c.key + " " + catName(c.key) + ": not assessed.");
      (basis.required_categories || []).concat(basis.supporting_categories || [])
        .forEach((k) => {
          if (catByKey[k]) return;
          notAssessedLines.push("\u25cb " + k + " " + catName(k) + ": never called this period.");
        });
      const supLines = (basis.supporting_categories || []).map((k) => {
        const c = catByKey[k];
        return "- " + k + " " + catName(k) + " (supporting): "
          + (c && c.status ? c.status
             : "not assessed. A supporting category that was not assessed never produces a Green.");
      });
      const reqLines = (basis.required_categories || []).map((k) => {
        const c = catByKey[k];
        return "- " + k + " " + catName(k) + " (required): "
          + (c && c.status ? c.status : "not assessed.");
      });

      // 5. THE RECOMMENDATION: evidence acquisition, verification, escalation. Advisory, and
      //    it asserts no project condition, so it needs no figure.
      const iActions = [];
      detail.forEach((d) => {
        iActions.push("Acquire the evidence " + catName(d.category) + " (" + d.category
          + ") needs, and re-run the period once it is on file");
      });
      iActions.push("Verify the figures already on file for the categories that did report, "
        + "so the partial picture is at least trustworthy");
      if (adverse.length) {
        iActions.push("Escalate " + adverse.map((c) => c.key).join(", ")
          + " to the controls lead now rather than waiting for an official posture");
      }
      /* THE CONCRETE COURSE THE PARTICIPANT ACTS ON. Named exactly as the decision card
         presents it -- "How did you treat the recommendation?", whose vocabulary is
         `research_decision.DISPOSITIONS` -- so this sentence names a control that exists.
         `request_evidence` is called out because it is the disposition an Indeterminate
         status is actually about. Nothing in decision-ui.js is changed by this run. */
      iActions.push("Record how you treated this recommendation on the decision card - accept, "
        + "accept with conditions, modify, reject, defer, request evidence, escalate or "
        + "transfer authority - and request evidence is the disposition this status is about");

      return [
        "### Recommendation", iRec.join("\n"),
        "### Signal Pattern",
        (assessedLines.concat(notAssessedLines).join("\n")
         || "No category has computed data yet."),
        "### Key Drivers", reqLines.concat(supLines).join("\n"),
        "### Required Actions", iActions.map((a) => "- " + a).join("\n")
      ].join("\n");
    }

    const posture = ev.posture ? String(ev.posture) : "NO POSTURE";
    const stKey = ev.postureKey;
    const actionClause = stKey === "red"
        ? "bring the controls lead into a focused review this cycle."
      : stKey === "amber"
        ? "review the cost and schedule trend with the controls lead this cycle."
      : stKey === "green"
        ? "maintain routine monitoring this cycle."
        : "no course follows from the bands this period.";

    // 1. THE POSTURE, AND THE CATEGORY AND MODULE THAT SET IT, with each setter's own figure.
    const setters = ev.categories.filter((c) => c.status && (c.setBy || []).length);
    const setterBits = [];
    setters.forEach((c) => {
      (c.setBy || []).forEach((mid) => {
        const m = ev.modules.filter((x) => x.module_id === mid)[0];
        if (!m) return;
        setterBits.push(mid + " in " + c.key + ", reading " + (m.evidence_metric || "no figure stated")
                        + ", band " + (m.status_color || "none stated"));
      });
    });
    const postureSentence = setterBits.length
      ? "The posture is " + posture + ", set by " + setterBits.join("; ") + "."
      : "The posture is " + posture + ", and the stored result records no module as having set it.";

    // 2. THE COST AND THE SCHEDULE POSITION, WHETHER OR NOT EITHER SET THE POSTURE. A
    //    recommendation that omits cost because schedule was worse is the failure this fix
    //    exists to prevent, so both lines are always printed.
    const positionSentence = (label, key) => {
      const v = ev.signalInputs[key];
      if (v == null || v === "") return label + " was not computed this period.";
      return label + " is " + v + ", read from the " + briefFigureSource(ev, key) + ".";
    };
    const costLine = positionSentence("The cost performance index", "cpi");
    const schedLine = positionSentence("The schedule performance index", "spi");

    // 5. WHAT THE PLATFORM COULD NOT COMPUTE THIS PERIOD.
    const darkCats = ev.categories.filter((c) => !c.status).map((c) => c.key);
    const censusBits = [ev.modules.length + " modules produced a figure this period"];
    if (ev.abstainedCount != null) censusBits.push(ev.abstainedCount + " produced none");
    if (darkCats.length) censusBits.push(darkCats.length + " categories carry no status ("
                                        + darkCats.join(", ") + ")");
    const censusLine = censusBits.join(", ") + ".";

    const recommendation = posture.toUpperCase() + " \u00b7 " + actionClause + "\n"
      + postureSentence + "\n" + costLine + "\n" + schedLine + "\n" + censusLine;

    // THE SIGNAL PATTERN CARRIES A COUNT AND THE CATEGORY KEYS AND NOTHING ELSE. The editorial
    // phrase that used to close each line ("the analysis indicates meaningful risk worth a
    // closer look") asserted a condition and named no figure; it is gone rather than reworded.
    const byBand = { RED: [], AMBER: [], GREEN: [], "NO BAND": [] };
    ev.categories.forEach((c) => {
      const k = c.status ? statusKeyFromText(c.status) : "none";
      const bucket = k === "red" ? "RED" : k === "amber" ? "AMBER" : k === "green" ? "GREEN" : "NO BAND";
      byBand[bucket].push(c.key);
    });
    const patternLines = [];
    Object.keys(byBand).forEach((b) => {
      const arr = byBand[b];
      if (!arr.length) return;
      patternLines.push("\u25cf " + b + " (" + arr.length + " categor"
        + (arr.length === 1 ? "y" : "ies") + "): " + arr.join(", ") + ".");
    });
    const patternBlock = patternLines.length ? patternLines.join("\n")
                                             : "No category has computed data yet.";

    // 3 AND 4. THE BAND EACH FIGURE CROSSED, AND THE DOCUMENT IT CAME FROM.
    const keySignals = briefKeySignals(project);
    const driverLines = keySignals.length
      ? keySignals.map((k) => "- " + k.label + ": " + k.value + " (" + briefStatusWords(k.status) + ")")
      : ["- No computed key signals are available yet."];
    BRIEF_SCALARS.forEach((f) => {
      if (ev.signalInputs[f.key] == null) return;
      driverLines.push("- " + f.label + " came from the " + briefFigureSource(ev, f.key) + ".");
    });

    // ADVISORY, NAMED AUTHORITY AND HORIZON, NEVER A COMMAND, AND NEVER A CONDITION CLAIM: an
    // action says what someone might do, so it asserts nothing that would need a figure.
    const actions = stKey === "red" || stKey === "amber"
      ? ["The program director may wish to bring the controls lead into a review before the next "
         + "reporting cycle closes",
         "It may be helpful to reconcile the earned-value figures against the latest pay application"]
      : ["Routine monitoring appears sufficient this cycle",
         "It may be helpful to confirm the latest earned-value inputs are current"];

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

  /* RUN 91, SECTION 3.3. THE TWO COUNTS THE BRIEF PRINTS ARE DERIVED AT RENDER FROM THIS ROW.

     WHAT WAS WRONG, MEASURED IN A BROWSER. The header read "grouped analysis across 11 signal
     categories" -- `projectCats().length`, the size of the whole taxonomy, not of anything on
     the page -- and the footer read "51 modules", the stored `summary.total_modules` count. The
     brief itself said, on the same row, that 9 modules produced a figure and 12 produced none:
     twenty-one, not fifty-one. Neither printed number matched anything a reader could see.

     WHAT THEY NOW COUNT, said out loud so the number is not ambiguous:
       * categories -- every category this brief accounts for: the ones the row carries a
         category status for, plus every required and supporting category the server's
         `project_status_basis` names, whether or not it was ever called. That is the set the
         Signal Pattern and Key Drivers sections between them list.
       * modules -- every module this row holds: those that produced a figure plus those that
         abstained.

     NO STORED OR HARD-CODED COUNT IS CARRIED. Where there is no row there is no number, and the
     clause is omitted rather than filled with one. */
  function briefScope(project) {
    let ev = null;
    try { ev = briefEvidence(project); } catch (e) { return null; }
    if (!ev || !ev.row) return null;
    const b = ev.statusBasis || {};
    const keys = Object.create(null);
    (ev.categories || []).forEach((c) => { if (c && c.key) keys[c.key] = 1; });
    (b.required_categories || []).forEach((k) => { keys[k] = 1; });
    (b.supporting_categories || []).forEach((k) => { keys[k] = 1; });
    const reported = (ev.modules || []).length;
    const silent = (ev.abstainedCount != null) ? ev.abstainedCount : 0;
    return { categories: Object.keys(keys).length, modules: reported + silent,
             reported: reported, silent: silent };
  }

  function briefFooter(brief, project) {
    if (!brief) return "";
    const snap = brief.snapshot || null;
    const computedAt = (snap && snap.computed_at) || brief.generated_at || null;
    if (!computedAt) return "";
    let when = computedAt.substring(0, 10);
    try {
      const d = new Date(computedAt);
      when = d.toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric" });
    } catch (e) {}
    // RUN 91. `snap.summary.total_modules` is NOT read here any more -- see `briefScope`.
    const scope = project ? briefScope(project) : null;
    const conf = snap && snap.summary && snap.summary.evidence_agreement && snap.summary.evidence_agreement.confidence;
    const parts = ["Generated from stored log", when];
    if (scope) parts.push(scope.modules + " modules on this row (" + scope.reported
                          + " produced a figure, " + scope.silent + " produced none)");
    if (conf) parts.push(conf + " confidence");
    return `<div class="eb-foot">${esc(parts.join(" · "))}</div>`;
  }


  /* =========================================================================================
     RUN 70, FIX 4. THREE CHECKS, IN CODE, RUN BEFORE ANYTHING RENDERS.

     THE DEFECT. The Executive Brief printed "The evidence suggests meaningful risk that may
     warrant a closer look this cycle." beside three key drivers that all read green, and named
     no figure supporting the concern. Two paths produce that text -- the chat endpoint, and
     `scriptedBrief` when it fails -- and NOTHING obliged either of them to use the evidence it
     was given. The prompt asked politely; a prompt is not a check.

     WHERE THE GATE SITS, AND WHY HERE. `briefBodyHtml`'s "ready" branch is the single point at
     which any brief text, from either path, becomes HTML. Gating here gates both, once, and a
     third path added later cannot route around it without going through this function.

     WHAT HAPPENS ON FAILURE. The recommendation is REJECTED, the failure is recorded on the
     project and in the console, and the reader is shown the reasoning's structured fields
     instead: the posture and what set it, the cost and the schedule position whichever set it,
     the band each figure crossed, the document type each figure came from, and what the
     platform could not compute this period. That is a worse experience than a fluent paragraph
     and an honest one. No substitute sentence is synthesised to keep the panel looking full.
     ========================================================================================= */

  //: A sentence containing one of these ASSERTS A CONDITION about the project, and must
  //: therefore name the figure behind it. Words that merely describe an action ("review",
  //: "verify", "confirm") are deliberately absent: an advisory step asserts nothing.
  const BRIEF_CONDITION_WORDS = [
    "meaningful risk", "significant risk", "elevated risk", "high risk", "risk is", "at risk",
    "pressure", "drift", "over budget", "overrun", "is behind", "behind schedule", "slipping",
    "slippage", "variance", "adverse", "deteriorat", "worsen", "improv", "tracking within",
    "tracking well", "tracking as", "on plan", "on budget", "healthy", "concern",
    "underperform", "favourable", "favorable", "unfavourable", "unfavorable",
    "suggests", "indicates", "warrants", "points to"
  ];

  //: Words that make a sentence a claim ABOUT THE SCHEDULE, and about the cost. Check 3 refuses
  //: either kind of claim when no module and no stored scalar produced a figure of that kind.
  const BRIEF_SCHEDULE_WORDS = ["schedule", "spi", "milestone", "float", "slip", "behind",
                                "late", "duration", "critical path", "earned schedule"];
  const BRIEF_COST_WORDS = ["cost", "cpi", "budget", "eac", "tcpi", "vac", "contingency",
                            "spend", "overrun", "dollar", "$"];

  //: The category prefixes whose modules produce a schedule figure and a cost figure. Read from
  //: the stored row's own module ids, so a module that abstained cannot supply one.
  const BRIEF_SCHEDULE_CATS = ["A2"];
  const BRIEF_COST_CATS = ["A1", "A3"];

  //: A figure as it is compared: digits only, sign kept, separators and units dropped.
  function briefNormFigure(t) {
    const m = String(t == null ? "" : t).replace(/[,$\s\u00a0]/g, "").match(/-?\d+(?:\.\d+)?/);
    return m ? String(Number(m[0])) : null;
  }

  //: Every figure a sentence names.
  function briefFiguresIn(text) {
    const out = [];
    (String(text || "").match(/-?\$?\d[\d,]*(?:\.\d+)?/g) || []).forEach((raw) => {
      const n = briefNormFigure(raw);
      if (n !== null) out.push(n);
    });
    return out;
  }

  /* Everything the three checks judge against, read from the STORED ROW and nowhere else.
     Nothing here is derived, defaulted or inferred: a quantity the row does not hold is absent,
     and absence is what Check 3 tests for. */
  function briefEvidence(project) {
    const row = (window.LinResults && LinResults.rowFor(project)) || null;
    const si = (row && row.signal_inputs && typeof row.signal_inputs === "object")
      ? row.signal_inputs : {};
    const sources = (si.sources && typeof si.sources === "object") ? si.sources : {};
    const mods = (row && Array.isArray(row.module_results)) ? row.module_results : [];
    const cats = (row && row.category_statuses && typeof row.category_statuses === "object")
      ? row.category_statuses : {};

    const drivers = briefKeySignals(project);

    // THE FIGURES THE PLATFORM ACTUALLY HOLDS. A claim may name one of these and nothing else.
    const allowed = Object.create(null);
    const add = (v, why) => {
      const n = briefNormFigure(v);
      if (n !== null && !(n in allowed)) allowed[n] = why;
    };
    drivers.forEach((d) => add(d.value, d.label));
    BRIEF_SCALARS.forEach((f) => { if (si[f.key] != null) add(si[f.key], f.label); });
    mods.forEach((m) => {
      Object.keys(m).forEach((k) => {
        const v = m[k];
        if (typeof v === "number" && Number.isFinite(v)) {
          add(v, m.module_id + " " + k);
          add(Math.round(v), m.module_id + " " + k);
          add(Number(v).toFixed(2), m.module_id + " " + k);
          add(Number(v).toFixed(3), m.module_id + " " + k);
          add(Math.abs(v), m.module_id + " " + k + " (magnitude)");
          add(Math.abs(Math.round(v)), m.module_id + " " + k + " (magnitude)");
        }
      });
    });
    Object.keys(si).forEach((k) => {
      const v = si[k];
      if (typeof v === "number" && Number.isFinite(v)) add(v, k);
    });
    // The Signal Pattern prints a COUNT of categories per band. That count is a stored fact
    // about this row, so it is admissible, and it is added from the row rather than assumed.
    const bandCount = { red: 0, amber: 0, green: 0, none: 0 };
    const catList = [];
    Object.keys(cats).forEach((k) => {
      const c = cats[k] || {};
      const st = c.status ? String(c.status) : null;
      catList.push({ key: k, status: st, setBy: c.status_set_by || [] });
      const b = st ? statusKeyFromText(st) : "none";
      if (bandCount[b] != null) bandCount[b] += 1; else bandCount.none += 1;
    });
    Object.keys(bandCount).forEach((b) => add(bandCount[b], b + " category count"));
    // THE CENSUS IS A STORED FACT ABOUT THIS ROW: how many modules produced a figure, how many
    // did not, and how many categories carry a status. A recommendation may cite these because
    // the row holds them; it may not cite a count of anything the row does not hold.
    add(mods.length, "modules holding a result");
    add(catList.length, "categories on the row");
    add(catList.filter(function (c) { return !c.status; }).length, "categories with no status");
    if (row && Array.isArray(row.abstained)) add(row.abstained.length, "modules that abstained");

    const has = (prefixes, keys) =>
      mods.some((m) => prefixes.some((p) => String(m.module_id || "").indexOf(p + ".") === 0)) ||
      keys.some((k) => si[k] != null);

    return {
      row: row,
      signalInputs: si,
      sources: sources,
      modules: mods,
      categories: catList,
      drivers: drivers,
      allowedFigures: allowed,
      // THE STORED ROW'S OWN PROJECT STATUS IS THE FALLBACK, not a default: `resolveBriefState`
      // reads `project.signals`, a legacy blob that is empty on every server-computed project.
      posture: resolveBriefState(project) || (row ? (row.project_status || null) : null),
      postureKey: statusKeyFromText(
        resolveBriefState(project) || (row ? (row.project_status || "") : "")),
      costComputed: has(BRIEF_COST_CATS, ["cpi", "ev", "ac", "bac"]),
      scheduleComputed: has(BRIEF_SCHEDULE_CATS, ["spi"]),
      abstainedCount: (row && Array.isArray(row.abstained)) ? row.abstained.length : null,
      /* RUN 89, GOAL THREE. The server's required-core verdict, read from the stored row and
         NEVER re-derived here. Absent on a row computed before Run 89, and absence means the
         gate did not run rather than that the status is official. */
      statusBasis: (row && row.project_status_basis
                    && typeof row.project_status_basis === "object")
                    ? row.project_status_basis : null
    };
  }

  //: The brief split into the sentences a check can be applied to, each carrying the section it
  //: came from so a rejection can say where.
  function briefClaimSentences(parsed) {
    const out = [];
    const push = (section, block) => {
      String(block || "").split(/(?<=[.!?])\s+|\n+/).forEach((raw) => {
        const t = raw.trim();
        if (t) out.push({ section: section, text: t });
      });
    };
    push("Recommendation", parsed.recommendation);
    (parsed.pattern || []).forEach((l) => push("Signal Pattern", l));
    (parsed.drivers || []).forEach((l) => push("Key Drivers", l));
    (parsed.actions || []).forEach((l) => push("Required Actions", l));
    return out;
  }

  function briefHasAny(text, words) {
    const t = String(text || "").toLowerCase();
    return words.some((w) => t.indexOf(w) >= 0);
  }

  /* THE GATE. Returns {ok: true} or {ok: false, failures: [{check, section, sentence, reason}]}.
     A recommendation failing ANY of the three is rejected. */
  function briefGate(parsed, ev) {
    const failures = [];
    const sentences = briefClaimSentences(parsed);

    // ---------------------------------------------------------------- CHECK 1
    // EVERY CLAIM NAMES THE FIGURE BEHIND IT. A sentence asserting a condition with no figure
    // attached does not render; nor does one naming a figure the stored result does not hold.
    sentences.forEach((s) => {
      if (!briefHasAny(s.text, BRIEF_CONDITION_WORDS)) return;
      const figs = briefFiguresIn(s.text);
      if (!figs.length) {
        failures.push({
          check: "1. Every claim names the figure behind it",
          section: s.section, sentence: s.text,
          reason: "asserts a condition about this project and names no figure"
        });
        return;
      }
      const grounded = figs.filter((f) => f in ev.allowedFigures);
      if (!grounded.length) {
        failures.push({
          check: "1. Every claim names the figure behind it",
          section: s.section, sentence: s.text,
          reason: "names " + figs.join(", ") + ", and the stored result for this period holds "
                  + "no such figure"
        });
      }
    });

    // ---------------------------------------------------------------- CHECK 2
    // THE POSTURE AGREES WITH ITS DRIVERS. If every stated driver reads green and the posture
    // is adverse, the recommendation must name what made it adverse.
    if (ev.postureKey === "red" || ev.postureKey === "amber") {
      // THE DRIVERS THE RECOMMENDATION STATES, read out of its own Key Drivers lines, not off
      // the stored row. The order's words are "if every STATED driver reads green": a brief
      // that shows the reader three green drivers beside an adverse posture is the defect,
      // whatever the row happens to hold elsewhere.
      const statedBands = [];
      (parsed.drivers || []).forEach((line) => {
        const m = String(line).match(/\(([^)]+)\)\s*$/);
        if (!m) return;
        const k = statusKeyFromText(m[1]);
        if (k === "red" || k === "amber" || k === "green") statedBands.push(k);
      });
      const allGreen = statedBands.length > 0 && statedBands.every((k) => k === "green");
      if (allGreen) {
        // WHAT WOULD MAKE THE POSTURE HONEST: a figure from a driver the row bands non-green,
        // or the key of a category the row bands non-green. Named in the recommendation, or
        // the posture is asserted with nothing behind it.
        const adverseFigs = [];
        ev.drivers.forEach((d) => {
          if (d.status && statusKeyFromText(d.status) !== "green") {
            const n = briefNormFigure(d.value);
            if (n !== null) adverseFigs.push(n);
          }
        });
        const adverseCats = ev.categories
          .filter((c) => c.status && statusKeyFromText(c.status) !== "green")
          .map((c) => c.key);
        const text = String(parsed.recommendation || "");
        const namesFigure = briefFiguresIn(text).some((f) => adverseFigs.indexOf(f) >= 0);
        const namesCategory = adverseCats.some((k) => text.indexOf(k) >= 0);
        if (!namesFigure && !namesCategory) {
          failures.push({
            check: "2. The posture agrees with its drivers",
            section: "Recommendation", sentence: text,
            reason: "the posture is " + (ev.posture || "adverse") + " and every driver it states "
                    + "reads green, and it names nothing that made the posture adverse"
          });
        }
      }
    }

    // ---------------------------------------------------------------- CHECK 3
    // NOTHING IS ASSERTED THAT NO MODULE COMPUTED.
    sentences.forEach((s) => {
      if (!briefHasAny(s.text, BRIEF_CONDITION_WORDS)) return;
      if (briefHasAny(s.text, BRIEF_SCHEDULE_WORDS) && !ev.scheduleComputed) {
        failures.push({
          check: "3. Nothing is asserted that no module computed",
          section: s.section, sentence: s.text,
          reason: "makes a claim about the schedule, and no schedule module produced a value "
                  + "this period"
        });
      }
      if (briefHasAny(s.text, BRIEF_COST_WORDS) && !ev.costComputed) {
        failures.push({
          check: "3. Nothing is asserted that no module computed",
          section: s.section, sentence: s.text,
          reason: "makes a claim about cost, and no cost module produced a value this period"
        });
      }
    });

    return failures.length ? { ok: false, failures: failures } : { ok: true, failures: [] };
  }

  //: The rejection is RECORDED, not only rendered. It rides the project object so the console,
  //: the regenerate path and anything reading the page afterwards can see what was refused.
  function recordBriefRejection(project, gate, brief) {
    const rec = {
      at: new Date().toISOString(),
      source: (brief && brief.source) || "chat",
      failures: gate.failures
    };
    try { project.executiveBriefRejection = rec; } catch (e) { /* frozen object */ }
    try {
      console.warn("[brief] REJECTED for " + (project && project.id) + ":", gate.failures);
    } catch (e) { /* no console */ }
    return rec;
  }

  //: THE FIGURE'S DOCUMENT, from the row's own `signal_inputs.sources` map. Never guessed: a
  //: field with no source entry is reported as having none.
  const BRIEF_DERIVED_FROM = { cpi: ["ev", "ac"], spi: ["ev", "pv"] };

  function briefFigureSource(ev, key) {
    const label = (t) => (window.DOC_TYPE_LABEL && DOC_TYPE_LABEL[t]) || String(t);
    const direct = ev.sources[key];
    if (direct && direct.docType) return label(direct.docType);
    // A DERIVED INDEX HAS NO SOURCE ENTRY OF ITS OWN, because no document states it: it is
    // formed from figures that do. Name those documents rather than report none.
    const parts = BRIEF_DERIVED_FROM[key] || [];
    const types = [];
    parts.forEach((f) => {
      const src = ev.sources[f];
      if (src && src.docType && types.indexOf(label(src.docType)) < 0) types.push(label(src.docType));
    });
    if (types.length) return types.join(" and ");
    return "no document type recorded";
  }

  /* What a reader sees INSTEAD of a rejected recommendation: the reasoning's structured fields.
     Section 9 of the order in five blocks -- the posture and what set it; the cost and the
     schedule position whether or not either set it; the band each figure crossed; the document
     each figure came from; and what the platform could not compute this period. */
  function briefRejectionHtml(ev, failures) {
    const li = (x) => `<li>${x}</li>`;
    const setters = ev.categories.filter((c) => c.status && (c.setBy || []).length);
    const postureLine = ev.posture
      ? `<p class="eb-rec"><span class="eb-rec-status status-${esc(ev.postureKey)}">${esc(String(ev.posture))}</span> `
        + (setters.length
            ? esc("set by " + setters.map((c) => c.key + " (" + c.setBy.join(", ") + ")").join("; "))
            : esc("no category recorded which modules set it"))
        + `</p>`
      : `<p class="eb-rec">No posture was computed for this period.</p>`;

    const positionRow = (label, key) => {
      const v = ev.signalInputs[key];
      if (v == null || v === "") {
        return li(esc(label + ": not computed this period"));
      }
      return li(esc(label + ": " + v + " (from " + briefFigureSource(ev, key) + ")"));
    };
    // BOTH POSITIONS, ALWAYS. A recommendation that omits cost because schedule was worse is
    // the failure this gate exists to prevent, so both are printed whichever set the posture.
    const positions = positionRow("Cost position (cost performance index)", "cpi")
                    + positionRow("Schedule position (schedule performance index)", "spi");

    const bandRows = ev.modules.length
      ? ev.modules.map((m) => li(
          esc(String(m.module_id) + ": " + (m.evidence_metric || "no figure stated") + " — "
              + (m.status_color ? "band " + m.status_color : "no band stated"))
        )).join("")
      : li(esc("No module produced a figure this period."));

    const notComputed = [];
    if (ev.abstainedCount != null) {
      notComputed.push(li(esc(ev.abstainedCount + " modules produced no figure this period.")));
    }
    const dark = ev.categories.filter((c) => !c.status).map((c) => c.key);
    if (dark.length) {
      notComputed.push(li(esc("Categories carrying no status: " + dark.join(", ") + ".")));
    }
    if (!notComputed.length) notComputed.push(li(esc("Nothing was recorded as uncomputed.")));

    const failRows = failures.map((f) => li(
      `<strong>${esc(f.check)}</strong> — ${esc(f.section)}: ${esc(f.reason)}.`
      + (f.sentence ? ` <em>${esc("“" + f.sentence + "”")}</em>` : "")
    )).join("");

    const sec = (head, inner) =>
      `<div class="eb-section"><p class="eb-sec-head">${esc(head)}</p>${inner}</div>`;

    return `<div class="eb-body eb-structured eb-rejected">`
      + `<p class="eb-flag eb-flag-review">The generated recommendation was rejected before it `
      + `rendered, because it did not meet the checks below. What the analysis actually holds is `
      + `printed in its place.</p>`
      + sec("Why it was rejected", `<ul class="eb-actions">${failRows}</ul>`)
      + sec("Posture", postureLine)
      + sec("Cost and schedule position", `<ul class="eb-drivers">${positions}</ul>`)
      + sec("Every figure and the band it crossed", `<ul class="eb-drivers">${bandRows}</ul>`)
      + sec("What could not be computed this period", `<ul class="eb-actions">${notComputed.join("")}</ul>`)
      + `</div>`;
  }

  function briefBodyHtml(state, brief, errMsg, project) {
    if (state === "loading") {
      return `<div class="eb-body eb-loading" aria-live="polite">
        <span class="eb-shimmer"></span>
        <span class="eb-status">Analysing signals across ${projectCats().length} categories…</span>
      </div>`;
    }
    if (state === "skipped") {
      return `<div class="eb-body eb-skipped">Upload project documents to generate the stored log. The executive brief is generated from that log, not from recomputed signals.</div>`;
    }
    if (state === "error") {
      return `<div class="eb-body eb-error" role="alert">Brief unavailable: ${esc(errMsg || "unknown error")}</div>`;
    }
    // Ready: render the structured 4 sections when the brief follows the format,
    // otherwise fall back to the brief text as a single paragraph.
    const text = (brief && brief.text) ? brief.text : "";
    const parsed = parseBrief(text);
    if (parsed && (parsed.recommendation || parsed.pattern.length || parsed.drivers.length || parsed.actions.length)) {
      // RUN 70, FIX 4. THE GATE. Both brief paths -- the chat endpoint and the scripted
      // fallback -- arrive here, and neither renders until the three checks pass. A failure is
      // recorded and the reasoning's structured fields are shown in place of the prose.
      if (project) {
        let ev = null;
        try { ev = briefEvidence(project); } catch (e) { ev = null; }
        if (ev) {
          const gate = briefGate(parsed, ev);
          if (!gate.ok) {
            recordBriefRejection(project, gate, brief);
            return briefRejectionHtml(ev, gate.failures);
          }
        }
      }
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
        Math.round((f.conflict || 0) * 100) + '%). Recommend named human review. This advisory does not change the fused status band.</p>');
    }
    const reds = f.redFlags || [];
    if (reds.length) {
      const items = reds.map((r) =>
        '<li><span class="eb-flag-cat">' + esc(r.category) + '</span> ' + esc(r.module) + '</li>').join("");
      parts.push('<div class="eb-flags-red"><p class="eb-flag eb-flag-red">⚑ Red modules (' + reds.length +
        '), flagged regardless of overall status:</p><ul class="eb-flag-list">' + items + '</ul></div>');
    }
    if (!parts.length) return "";
    return '<div class="eb-flags" aria-label="Brief flags">' + parts.join("") + '</div>';
  }

  /* WHERE A DOCUMENT DISAGREES WITH ITSELF. Deterministic, like the flags block above and for
     the same reason: it is read from the stored row the server already served, not from the
     generated brief, so it cannot be lost to a cached brief, a model refusal or a regenerate.

     It states what disagrees and by how much, names the document that stated both figures, and
     stops. It does not say which figure is wrong, because the platform does not know, and it
     does not tell the reader what to do about it. It carries no band, no colour and no
     severity: the class below is the same neutral informational class the liability-period
     line uses, and no status anywhere on this page reads it. */
  function briefConsistencyHtml(project) {
    var row = null;
    try { row = (window.LinResults && LinResults.rowFor(project)) || null; } catch (e) { row = null; }
    var findings = (row && row.consistency_findings) || [];
    if (!findings.length) return "";
    var items = findings.map(function (f) {
      return '<p class="eb-flag eb-flag-info eb-consistency-item">' + esc(f && f.sentence ? f.sentence : "") + "</p>";
    }).join("");
    return '<div class="eb-consistency" aria-label="Figures that disagree">'
      + '<p class="eb-flag eb-flag-info eb-consistency-head">Figures stated in one document that do not agree with each other:</p>'
      + items + "</div>";
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
    let consistency = "";
    try { consistency = briefConsistencyHtml(project); } catch (e) {}
    // RUN 91, SECTION 3.3. The header's category count is this row's, derived here, or absent.
    let scope = null;
    try { scope = briefScope(project); } catch (e) {}
    const scopeClause = scope
      ? esc("grouped analysis across the " + scope.categories + " signal categories this brief "
            + "accounts for")
      : esc("grouped analysis of this period's stored result");
    const state = cached ? "ready" : "loading";
    return `<section class="panel eb-panel eb-accent-${esc(accent)}" aria-label="Executive brief" data-eb-id="${esc(projectId)}">
      <div class="eb-head">
        <div>
          <p class="eyebrow eb-eyebrow">Executive brief${project && project.name ? ": " + esc(project.name) : ""}</p>
          <p class="kn-sub eb-sub">${period ? "Reporting period: " + esc(period) + " · " : ""}${scopeClause}</p>
        </div>
        <button type="button" class="btn small eb-regen" data-eb-regen="${esc(projectId)}" aria-label="Regenerate brief">Regenerate ↺</button>
      </div>
      ${flags}
      ${consistency}
      ${briefBodyHtml(state, cached, null, project)}
      ${cached ? briefFooter(cached, project) : ""}
    </section>`;
  }

  function setBriefState(root, state, project, brief, errMsg) {
    const panel = root.querySelector(".eb-panel");
    if (!panel) return;
    const old = panel.querySelector(".eb-body");
    if (old) old.remove();
    const oldFoot = panel.querySelector(".eb-foot");
    if (oldFoot) oldFoot.remove();
    panel.insertAdjacentHTML("beforeend", briefBodyHtml(state, brief, errMsg, project));
    if (state === "ready" && brief) panel.insertAdjacentHTML("beforeend", briefFooter(brief, project));
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
      console.log("[brief] skipped " + project.id + ". No signals to brief on");
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
    /* RUN 91, SECTION 3.5. The route, wired. `toggleSection` is app.js's own collapse control,
       the same one the section headers call, so this opens the section exactly as a click on
       its header would; the body is then scrolled into view and focused for a keyboard reader.
       Delegated from the panel root because the button is re-created by `setBriefState` on every
       regenerate, and a listener bound to the old node would be lost with it. */
    root.addEventListener("click", (e) => {
      const btn = e.target && e.target.closest
        ? e.target.closest("[data-brief-to-decision]") : null;
      if (!btn) return;
      const body = document.getElementById("body-d-decision");
      const closed = !body || body.style.display === "none";
      if (closed && typeof window.toggleSection === "function") {
        try { window.toggleSection("d-decision"); } catch (err) {}
      }
      const sec = document.getElementById("section-d-decision");
      if (sec && sec.scrollIntoView) sec.scrollIntoView({ behavior: "smooth", block: "start" });
      const head = sec ? sec.querySelector(".collapse-header") : null;
      if (head && head.focus) { try { head.focus(); } catch (err) {} }
    });
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
    wireComputeAll(root);
    wireDocumentControl(root);
  }

  /* Generate signals for every period the project holds documents for.
     ------------------------------------------------------------------
     The periods are computed SERVER-SIDE, in order, oldest first, and each sees only itself
     and earlier periods. Nothing about the computation happens in the browser: this control
     asks, reads the answer and reports it.

     The server refuses this for a research account whether or not this button is drawn, so
     hiding it is a courtesy and not the enforcement. */
  function wireComputeAll(root) {
    root.querySelectorAll("[data-compute-all]").forEach((b) =>
      b.addEventListener("click", async () => {
        const msg = root.querySelector(".detail-compute-all-msg");
        if (!window.LinStore || !LinStore.postWithTimeout) {
          if (msg) msg.textContent = "The server is not reachable from this page.";
          return;
        }
        b.disabled = true;
        if (msg) msg.textContent = "Generating signals for every period…";
        let resp;
        try {
          resp = await LinStore.postWithTimeout({ action: "projectcomputeall", id: b.dataset.computeAll });
        } catch (e) {
          resp = { ok: false, error: (e && e.message) || "the request did not complete" };
        }
        b.disabled = false;
        if (!resp || resp.ok !== true) {
          if (msg) msg.textContent = (resp && resp.error) || "Could not generate signals.";
          return;
        }
        const order = (resp.periods || []).join(", ");
        if (msg) {
          var parts = [];
          var results = resp.results || [];
          var fresh = results.filter(function(r) { return r.computed && !r.recomputed; });
          var recomputed = results.filter(function(r) { return r.recomputed; });
          var skipped = results.filter(function(r) { return r.skipped; });
          if (fresh.length)
            parts.push(fresh.length + " period(s) computed for the first time");
          if (recomputed.length) {
            var reasons = recomputed.map(function(r) {
              return "period " + r.period + " (" + (r.reason || "documents changed") + ")";
            });
            parts.push(recomputed.length + " period(s) recomputed: " + reasons.join("; "));
          }
          if (skipped.length)
            parts.push(skipped.length + " period(s) unchanged, left untouched");
          if (!parts.length) parts.push("nothing to compute");
          msg.textContent = parts.join(". ") +
            (order ? " (periods in order: " + order + ")" : "") + ".";
        }
        if (window.LinApp && LinApp.refresh) LinApp.refresh();
      }));
  }

  // Status provenance trace toggle — pure UI expand/collapse, no data fetch
  // (the panel HTML is already rendered; this just reveals it).
  function wireProvenanceTrace(root) {
    const toggle = root.querySelector(".det-prov-toggle");
    if (!toggle) return;
    const panel = root.querySelector(".det-prov-panel");
    if (!panel) return;
    toggle.addEventListener("click", () => {
      const open = panel.hasAttribute("hidden");
      if (open) panel.removeAttribute("hidden"); else panel.setAttribute("hidden", "");
      toggle.setAttribute("aria-expanded", String(open));
      toggle.textContent = open ? "hide" : "why?";
    });
  }

  /* RUN 55, PHASE A. Mount the six admin controls on THIS project's detail page.
     ------------------------------------------------------------------------------
     `id` is render()'s own `p.id` -- the project this page was rendered for -- and it is
     passed straight into the panel builder, which closes every one of the six handlers over
     it. That is what makes "each control acts on that project and no other" true by
     construction rather than by inspection: there is no selector, no lookup and no shared
     mutable id anywhere in the path.

     LinIngest may not be loaded on a surface that renders detail without ingest.js (the
     render-only test harness is one), so this degrades to leaving the host empty rather than
     throwing and taking the rest of the page's wiring down with it. */
  /* RUN 71. The document control button opens ingest.js's dialog for THIS project.
     ------------------------------------------------------------------------------
     Same shape as `.detail-upload`: the project id is render()'s own `p.id`, carried on the
     button and read back here, so the dialog acts on the project being viewed and no other.
     Degrades to doing nothing where ingest.js is not loaded (the render-only harness), rather
     than throwing and taking the rest of this page's wiring down with it. */
  function wireDocumentControl(root) {
    root.querySelectorAll("[data-doc-control]").forEach((b) =>
      b.addEventListener("click", () => {
        if (!(window.LinIngest && typeof LinIngest.openDocumentControl === "function")) return;
        try { LinIngest.openDocumentControl(b.dataset.docControl); }
        catch (e) { console.warn("[detail] document control failed to open:", e && e.message); }
      }));
  }


  /* =====================================================================================
     RUN 76. THE CATEGORY SPECIFICATION PANEL.

     PLACEMENT IS THE OWNER'S RULING, section 6 of the Run 76 order: "a new panel on the project
     detail page, immediately above Location. That is decided; do not place it elsewhere."
     Location is `d-globe` and is currently the FIRST section, so this panel becomes the first.

     WHAT IT SHOWS. The same eleven-category tree the signal ledger renders -- projectCats(),
     which is LIN_CATEGORIES minus the portfolio-level entry. A "Call all" button above the list
     and a "Call" button on each row.

     FOUR STATES, AND THEY ARE NOT BLURRED (section 12.4 fails the run if they are):

       computed     a value and its band
       abstained    the evidence is not there; the module says which input it wants. NOT a
                    failure -- it is the correct answer to a missing figure.
       out_of_order the specification could have applied but the upstream categories have not
                    run. Names them. A WARNING on the row, not a failure.
       failed       the call errored or the answer was unusable. THE PLATFORM'S fault.

     Each state carries its own `data-state` value, its own class and its own visible word, so a
     reader -- and a browser assertion -- can tell them apart from the DOM alone.

     THIS PANEL COMPUTES NOTHING. Section 7.5: the client renders and computes nothing. Every
     figure, band, count and status below is read from the server's stored reading.
     ===================================================================================== */

  /* RUN 81. THE STATE VOCABULARY, ON THE OWNER'S RULING OF THIS RUN.
     "A module reports what its evidence supports. It is not deciding anything, so it cannot
     abstain. It says what it has. If it is not relevant, it was never called."

     THIS IS A RENAME AND NOTHING ELSE. Every state the server stores keeps its own row, its
     own `data-state` marker and its own CSS class; not one is merged into another and not one
     word here is derived from anything the client worked out for itself. The server's
     vocabulary (`spec_readings.reading_payload`) is untouched -- only what the person reads is.

       computed     -> "Has a reading"     the module reported a value, and its band is shown
       abstained    -> "Nothing to report" the evidence is not there. NOT "abstained": the
                                           explanation under the row already says what is
                                           being waited for, and the label must not claim the
                                           module declined to answer.
       out_of_order -> "Out of order"      unchanged. This is a real fifth distinction (the
                                           category's inputs have not run yet) and merging it
                                           into either neighbour would lose it.
       failed       -> "Failed"            unchanged. The platform owes an answer here.
       (no reading) -> "Not called yet"    the fifth on-screen distinction Run 79 established.

     THE OWNER'S THIRD STATE, "Not relevant -- does not apply to this project type", HAS NO
     SERVER COUNTERPART AND IS DELIBERATELY NOT MANUFACTURED HERE. No specification reading
     carries a sector-applicability mark, so a "Not relevant" label rendered from this client
     would be a claim the server never stored. The order forbids implying a value the server
     did not store, so the state is reported to the owner as unavailable rather than invented. */
  const SPEC_STATE_WORDS = {
    computed: "Has a reading",
    abstained: "Nothing to report",
    out_of_order: "Out of order",
    failed: "Failed",
    /* The two no-reading rows, which Run 79 established are genuinely different from each
       other and from an empty reading: one category has a written specification and has not
       been processed yet, the other has no written specification at all. */
    not_run: "Not called yet",
    unspecified: "No specification"
  };

  /* What the status cell says when the server stored NO band. An em dash is a typographic
     shrug; each of these is a fact about the stored row and none of them implies a reading. */
  const SPEC_NO_STATUS_WORDS = {
    computed: "No band",
    abstained: "No band \u2014 nothing to report",
    out_of_order: "No band \u2014 out of order",
    failed: "No band \u2014 failed",
    not_run: "No band",
    unspecified: "No band"
  };

  function specStateChip(state, extra) {
    const key = String(state || "");
    const word = SPEC_STATE_WORDS[key] || "Not called yet";
    return `<span class="dcat-state dcat-state-${esc(key || "notrun")}" `
      + `data-state="${esc(key || "not_run")}">${esc(word)}</span>`
      + (extra ? `<span class="dcat-extra">${esc(extra)}</span>` : "");
  }

  /* RUN 82, PART A1. HOW MANY MODULES IN THIS CATEGORY PRODUCED A STATUS, OUT OF HOW MANY
     SHOULD HAVE.

     WHERE THE DENOMINATOR COMES FROM, and it is not invented and not hardcoded here. It is the
     length of the category's module list in `LIN_CATEGORIES`, which `build_client_taxonomy.py`
     GENERATES from `server/app/simulation/registry.py`. Measured this run: the per-category
     roster is A1 10, A2 6, A3 7, A4 10, A5 7, A6 4, B1 4, B2 1, B3 5, B4 2, C1 7 -- 63 -- which
     is `service_index()` exactly. The client is therefore reading a server authority, not
     counting something it decided for itself.

     WHERE THE NUMERATOR COMES FROM. `counts.computed` on the STORED reading. Nothing here
     derives a state, a band or a value; a category that has not been called has no reading and
     produces zero, which is the truth about it.

     WHY IT IS INSIDE THE COUNTS CELL AND NOT A NEW COLUMN. The row is a five-track grid and
     Run 81's column layout is correct under the standing ruling; a sixth track would restyle
     it. The figure is the FIRST item of the counts cell, so it reads before the breakdown
     exactly as the order requires, and the grid is untouched. */
  function specProducedHtml(produced, total) {
    const n = Number(produced || 0), N = Number(total || 0);
    return `<span class="dcat-produced" data-produced="${n}" data-of="${N}">`
      + `${n} of ${N} produced a status</span>`;
  }

  /* RUN 82, PART A2. THE COUNT LINE NOW SAYS WHAT THE STATE LABELS SAY.

     Run 81 corrected the state chips -- `abstained` renders as "Nothing to report" -- and left
     this line reading "7 abstained". A module does not abstain; it has nothing to report. Only
     the VISIBLE WORDS change.

     `data-count="abstained"` IS DELIBERATELY UNCHANGED. It is the server's state name and the
     machine-readable key: `radar.css:4730` selects on `[data-count="failed"]`, and the browser
     checks read the attribute rather than the words. Changing the key would rename the server's
     vocabulary from the client, which is a different and much larger change than the one the
     owner asked for. The words are what he objected to; the words are what moved. */
  /* RUN 83, SECTION 4. THE HEADLINE COUNT STAYS IN THE ROW; THE BREAKDOWN MOVES BEHIND THE
     EXPANSION.

     WHAT WAS WRONG. Run 82 added the produced-out-of figure as the FIRST item of this cell and
     did not remove the four-part breakdown it was meant to lead. Five figures rendered on one
     collapsed row -- "0 of 7 produced a status · 0 with a reading · 7 nothing to report · 0 out
     of order · 0 failed" -- the cell overflowed its grid track, the row wrapped, and the Process
     button was pushed off the end of its own row.

     WHAT CHANGED, AND ONLY THIS. `specCountsHtml` no longer emits the produced-out-of figure
     (the collapsed row now calls `specProducedHtml` directly), and the row no longer calls
     `specCountsHtml` at all: the breakdown is emitted into `.dcat-body`, where the per-module
     detail already lives and where the person has already asked for more. Every `data-count`
     key, every word and every number is unchanged -- the SAME markup, at a different place in
     the document. No control was added, moved or removed; the Process button is untouched. */
  function specCountsHtml(counts) {
    const c = counts || {};
    return `<span class="dcat-counts">`
      + `<span class="dcat-n" data-count="computed">${Number(c.computed || 0)} with a reading</span> · `
      + `<span class="dcat-n" data-count="abstained">${Number(c.abstained || 0)} nothing to report</span> · `
      + `<span class="dcat-n" data-count="out_of_order">${Number(c.out_of_order || 0)} out of order</span> · `
      + `<span class="dcat-n" data-count="failed">${Number(c.failed || 0)} failed</span>`
      + `</span>`;
  }

  function specModuleRowHtml(m) {
    const st = String((m && m.state) || "");
    if (st === "computed") {
      const band = m.band ? `<span class="dcat-band" data-band="${esc(m.band)}">${esc(m.band)}</span>`
                          : `<span class="dcat-band dcat-noband" data-band="none">no band</span>`;
      return `<li class="dcat-mod" data-module="${esc(m.module_id)}" data-state="computed">`
        + `<span class="dcat-mid">${esc(m.module_id)}</span>`
        + `<span class="dcat-val">${esc(m.display != null ? m.display : String(m.value))}</span>`
        + band + `</li>`;
    }
    return `<li class="dcat-mod" data-module="${esc(m && m.module_id)}" data-state="${esc(st)}">`
      + `<span class="dcat-mid">${esc(m && m.module_id)}</span>`
      + specStateChip(st)
      + `<span class="dcat-reason">${esc((m && m.reason) || "")}</span></li>`;
  }

  function specCategoryRowHtml(cat, reading, specified) {
    const key = cat.key;
    const has = specified.indexOf(key) >= 0;
    const state = reading ? reading.state : "";
    const status = (reading && reading.status) || "";
    const rowState = state || (has ? "not_run" : "unspecified");
    const noStatusWord = SPEC_NO_STATUS_WORDS[rowState] || "No band";
    let detail = "";
    /* A STORED READING ALWAYS RENDERS. The "no specification" note is what a category with
       nothing stored and no specification shows -- it must never hide a reading that exists. */
    if (!reading && !has) {
      detail = `<p class="dcat-note">No written specification yet. This category is still `
        + `served by the Python module layer.</p>`;
    } else if (!reading) {
      detail = `<p class="dcat-note">Not called yet for this period.</p>`;
    } else if (state === "out_of_order") {
      detail = `<p class="dcat-note dcat-warn" data-state="out_of_order">${esc(reading.reason || "")}</p>`;
    } else if (state === "failed") {
      detail = `<p class="dcat-note dcat-fail" data-state="failed">${esc(reading.reason || "")}</p>`;
    } else {
      detail = `<ul class="dcat-mods">`
        + (reading.modules || []).map(specModuleRowHtml).join("") + `</ul>`
        + `<p class="dcat-served">Served by <strong>${esc(reading.servedBy || "unknown")}</strong>`
        + (reading.modelId ? ` (${esc(reading.modelId)})` : "") + `</p>`;
    }
    return `<li class="dcat-row" data-category="${esc(key)}" `
      + `data-state="${esc(rowState)}">`
      + `<div class="dcat-head">`
      + `<button type="button" class="dcat-toggle" data-cat="${esc(key)}" aria-expanded="false">`
      + `<span class="dcat-name">${esc(key)} · ${esc(cat.name)}</span></button>`
      /* RUN 81, FAULT 2. The status cell said "—" wherever the server stored no band, which
         is the same mark a missing value gets everywhere else on the site and told the person
         nothing. It now says WHICH of the states left it without a band, which is a fact off
         the stored row. `data-status` is unchanged, so nothing reading the marker moves. */
      + `<span class="dcat-status" data-status="${esc(status || "none")}">`
      + esc(status || noStatusWord) + `</span>`
      + specStateChip(rowState)
      /* RUN 82, PART A1. The produced-out-of figure renders on EVERY row, including the ones
         with no reading at all: "0 of 7 produced a status" is precisely the fact the owner is
         asking the panel to admit, and hiding it on the untouched rows would hide it where it
         matters most. */
      + specProducedHtml((reading && reading.counts && reading.counts.computed) || 0,
                         ((cat && cat.modules) || []).length)
      /* RUN 81, FAULT 5. RELABELLED, NOT REPLACED. Same button, same class, same data-cat,
         same handler, same disabled rule: only the word changes. "Call" is what the code does;
         "Process" is what the person is asking for. */
      + `<button type="button" class="dcat-call btn-small" data-cat="${esc(key)}"`
      + (has ? "" : " disabled") + `>Process</button>`
      + `</div>`
      + `<div class="dcat-body" style="display:none">`
      + `<p class="dcat-breakdown">` + specCountsHtml(reading && reading.counts) + `</p>`
      + `${detail}</div></li>`;
  }

  /* RUN 82, PART A1. THE HEADLINE, AND WHY IT LEADS.

     THE OWNER'S RULING, and it is the whole of Part A: a panel reporting "0 failed" on every
     row while fifty-seven of sixty-three modules produce nothing is the platform grading itself
     on its own terms. The platform's distinction between a module that lacks evidence and a
     module the platform broke is real and it is kept -- the four states are still four states,
     still four different markers, still four different colours. It is simply not what the page
     leads with any more.

     The figure is a COUNT OF STORED ROWS: how many modules the server recorded a reading for,
     over how many modules are in service. It asserts nothing about any module and fills no gap.
     A project with nothing called reads "0 of 63 produced a status", which is true. */
  function specHeadlineHtml(produced, total, called, cats) {
    const n = Number(produced || 0), N = Number(total || 0);
    const silent = Math.max(0, N - n);
    return `<p class="dcat-headline" data-produced="${n}" data-of="${N}" data-called="${Number(called || 0)}">`
      + `<span class="dcat-headline-figure">${n} of ${N}</span> `
      + `<span class="dcat-headline-words">modules produced a status for this period.</span> `
      + `<span class="dcat-headline-rest">${silent} did not. `
      + `${Number(called || 0)} of ${Number(cats || 0)} categories have been processed.</span></p>`;
  }

  function categoryPanelHtml(p) {
    const cats = projectCats();
    const total = projectModuleCount();
    return `<section class="panel detail-catspecs" aria-label="Category specifications"
              data-project-id="${esc(p.id)}">
        ${specHeadlineHtml(0, total, 0, cats.length)}
        <div class="dcat-actions">
          <button type="button" class="dcat-call-all btn-small">Process all</button>
          <span class="dcat-hint">Applies each category's written specification to this
            period's stored figures. Per category is for building and diagnosis; the
            generate-for-every-period control is unchanged.</span>
        </div>
        <!-- RUN 82, PART A3. THE PROGRESS LINE MOVED HERE, from below the eleven rows.
             It is the SAME element: same tag, same class, same role=status live region,
             same and only writer, specCall(). Nothing was added and nothing removed; it now
             sits where the person who just pressed Process all is looking. -->
        <p class="dcat-status-line" role="status"></p>
        <ul class="dcat-list">${cats.map((c) => specCategoryRowHtml(c, null, [])).join("")}</ul>
      </section>`;
  }

  async function specCall(root, p, category) {
    const line = root.querySelector(".dcat-status-line");
    const tok = window.LinAuth ? LinAuth.getToken() : null;
    /* RUN 82, PART A4. Run 81 relabelled the buttons to Process and Process all and left this
       line saying "Calling". Two words for one action is what the owner is reading. */
    /* RUN 85, §3.2. THE LINE IS UNMISSABLE WHILE THE CALL IS IN FLIGHT. A call takes time and
       costs money; the person paying for it should not have to hunt for whether it is running.
       `is-processing` makes the SAME element bold, coloured and pulsing (CSS owns the pulse and
       stands down under prefers-reduced-motion); it is removed on every completion path, so a
       finished or failed call reverts to the quiet line. No element added, none removed. */
    if (line) {
      line.textContent = category ? ("Processing " + category + "…") : "Processing all…";
      line.classList.add("is-processing");
    }
    const body = { action: "projectcategoryapply", id: p.id, session_token: tok };
    if (category) body.category = category;
    let resp;
    try {
      resp = await LinStore.postWithTimeout(body, 300000);
    } catch (e) {
      if (line) {
        line.classList.remove("is-processing");
        line.textContent = "The call did not complete: " + (e && e.message);
      }
      return;
    }
    if (line) line.classList.remove("is-processing");
    if (!resp || resp.ok !== true) {
      if (line) line.textContent = (resp && resp.error) || "The call did not complete.";
      return;
    }
    if (line) {
      line.textContent = "Served by " + (resp.servedBy || "unknown")
        + ". " + (resp.readings || []).length + " category call(s) stored.";
    }
    await specRefresh(root, p);
  }

  async function specRefresh(root, p) {
    const tok = window.LinAuth ? LinAuth.getToken() : null;
    let resp;
    try {
      resp = await LinStore.postWithTimeout(
        { action: "projectcategoryreadings", id: p.id, session_token: tok }, 30000);
    } catch (e) { return; }
    if (!resp || resp.ok !== true) return;
    specPaint(root, resp.readings || {}, resp.specified || []);
  }

  /* Painted from the SERVER'S stored readings only. Nothing here derives a status, a band or a
     count; each is read from the row the server wrote. */
  function specPaint(root, readings, specified) {
    const list = root.querySelector(".dcat-list");
    if (!list) return;
    const cats = projectCats();
    list.innerHTML = cats.map((c) =>
      specCategoryRowHtml(c, readings[c.key] || null, specified)).join("");
    /* RUN 82, PART A1. The headline is repainted from the same stored readings that painted the
       rows, in the same pass, so the two can never disagree. Summed, not derived. */
    const head = root.querySelector(".dcat-headline");
    if (head) {
      let produced = 0, called = 0;
      cats.forEach((c) => {
        const r = readings[c.key];
        if (!r) return;
        called += 1;
        produced += Number((r.counts && r.counts.computed) || 0);
      });
      head.outerHTML = specHeadlineHtml(produced, projectModuleCount(), called, cats.length);
    }
  }

  function wireCategoryPanel(root, p) {
    const host = root.querySelector(".detail-catspecs");
    if (!host) return;
    host.addEventListener("click", function (ev) {
      const toggle = ev.target.closest(".dcat-toggle");
      if (toggle) {
        const row = toggle.closest(".dcat-row");
        const bodyEl = row && row.querySelector(".dcat-body");
        if (bodyEl) {
          const open = bodyEl.style.display !== "none";
          bodyEl.style.display = open ? "none" : "";
          toggle.setAttribute("aria-expanded", open ? "false" : "true");
        }
        return;
      }
      const call = ev.target.closest(".dcat-call");
      if (call && !call.disabled) { specCall(root, p, call.getAttribute("data-cat")); return; }
      if (ev.target.closest(".dcat-call-all")) { specCall(root, p, null); }
    });
    specRefresh(root, p);
  }

  function wireDetailAdmin(root, id) {
    const host = root.querySelector(".detail-admin-host");
    if (!host) return;
    if (!(window.LinIngest && typeof LinIngest.openInlineManage === "function")) return;
    try { LinIngest.openInlineManage(id, host); }
    catch (e) { console.warn("[detail] admin panel failed to mount for", id, "reason:", e && e.message); }
  }

  // RUN 57, PHASE A. wireReset() IS REMOVED WITH ITS CONTROL. Its whole body is now inside
  // ingest.js's doReset(), the merged union handler on `.pe-reset`, which this page mounts
  // through wireDetailAdmin() -> LinIngest.openInlineManage(id, host).

  function wireSignalWeb(root, projectId) {
    root.querySelectorAll("[data-history-period]").forEach((btn) =>
      btn.addEventListener("click", () => {
        selectedHistoryPeriod[projectId] = btn.dataset.historyPeriod;
        render(projectId);
      }));
  }

  // RUN 74. `wireSignalSphere` is removed with the panel it drew: the canvas, the drag and
  // wheel handlers and the five `[data-sphere-view]` buttons no longer exist in the DOM.
  // `wireSignalWeb` just above is NOT removed -- it wires `[data-history-period]`, which is
  // not the sphere, and which this page has not rendered for some time. Removing it would
  // be removing something other than the sphere.

  /* RUN 79, PART C. `wireEnsembleScatter()` drew and drove the Ensemble Analysis 3D scatter
     -- its canvas, its four view buttons, its tooltip and its category legend -- and is
     removed whole with the section. It had exactly one caller, the `d-ensemble` lazy
     initialiser, which is removed above. */

  // teardown is exported so app.js can release the context when the detail page is left,
  // rather than waiting for the next render that may never come.
  function teardown() {
    if (detailGlobe) { try { detailGlobe.destroy(); } catch (e) {} detailGlobe = null; }
  }

  // RUN 63, ORDER SECTION 5.3.2. THE DOCUMENTS PANEL AND THE SIGNAL FLOW READ ONE SOURCE.
  //
  // The owner's render showed "0 uploaded documents across 0 types" on a page listing 100
  // documents. Both surfaces walk the project's own extraction record, but they walked it
  // through two different implementations under two different windows: this one over the whole
  // log, and neural_flow.js's over the slice since the last `signals_reset`. Two accounts of
  // one quantity is a defect whatever each says alone, so there is now ONE implementation and
  // the diagram calls it rather than keeping a copy.
  /* RUN 89. The brief pipeline is exported FOR MEASUREMENT ONLY, by the same `__...ForTest`
     convention `__resetMapForTest` already established. Nothing in production calls it, and it
     exports the REAL functions rather than copies, so a harness cannot measure a second
     implementation of the three Run 70 checks. */
  window.LinDetail = { render, teardown, __resetMapForTest, uploadedDocEvents,
                       __briefForTest: { scriptedBrief, briefGate, briefEvidence, parseBrief } };
})();
