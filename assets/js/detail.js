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

  function signalWebHtml(project) {
    if (!window.LIN_CATEGORIES) return "";
    if (!window.hasSignals || !hasSignals(project)) return "";

    // Build a category-shaped view from the live project (works without a
    // stored snapshot, so the spider renders the moment models complete).
    const cats = LIN_CATEGORIES.map((cat) => {
      const modules = cat.modules.map((m) => ({
        id: m.id, num: m.num, name: m.name, method_class: m.method_class,
        status: window.getModuleStatus ? getModuleStatus(m.method_class, project) : null
      }));
      return {
        id: cat.id, num: cat.num, name: cat.name, parked: !!cat.parked,
        status: window.getCategoryStatus ? getCategoryStatus(cat.id, project) : null,
        modules
      };
    });

    const statuses = cats.map((c) => c.parked ? null : c.status);
    const axisLines = cats.map((c, i) => {
      const p = catPointFor(i, 1, 135);
      const parked = c.parked ? " sw-axis-parked" : "";
      return `<line class="sw-axis${parked}" x1="210" y1="190" x2="${p.ax.toFixed(1)}" y2="${p.ay.toFixed(1)}"></line>`;
    }).join("");

    const dots = cats.map((c, i) => {
      const labelP = catPointFor(i, 1, 135);
      const dotP = catPointFor(i, catRadius(statuses[i]), 135);
      const labelAnchor = Math.abs(labelP.tx - 210) < 12 ? "middle" : (labelP.tx > 210 ? "start" : "end");
      const worst = pickWorstModule(c);
      const title = c.parked
        ? c.num + " " + c.name + "\nStatus: Stage 2 (parked)"
        : c.num + " " + c.name +
          "\nCategory status: " + (statuses[i] || "No data") +
          (worst ? "\nWorst module: " + worst.name + " — " + (worst.status || "no data") : "");
      const labelText = c.parked ? c.num + " ML*" : c.num + " " + c.name.split(" ")[0];
      const labelClass = c.parked ? "sw-label sw-label-parked" : "sw-label";
      const dotClass = c.parked ? "sw-dot sw-none" : ("sw-dot sw-" + statusClass(statuses[i]));
      return `<text class="${labelClass}" x="${labelP.tx.toFixed(1)}" y="${labelP.ty.toFixed(1)}" text-anchor="${labelAnchor}">${esc(labelText)}</text>
        <circle class="${dotClass}" cx="${dotP.x.toFixed(1)}" cy="${dotP.y.toFixed(1)}" r="4">
          <title>${esc(title)}</title>
        </circle>`;
    }).join("");

    const cur = currentSnapshot(project);
    const overall = cur && cur.governance && cur.governance.state;

    return `<section class="panel signal-web-panel">
      <div class="sw-head">
        <div>
          <p class="eyebrow">Signal Web — ${esc(periodTitle(cur && cur.period))}</p>
          <p class="kn-sub sw-vs">9-category view · Cat 8 ML* parked for Stage 2</p>
        </div>
        <div class="sw-legend" aria-label="Signal web legend">
          <span><i class="sw-complete"></i>Complete</span>
          <span><i class="sw-green"></i>Green</span>
          <span><i class="sw-yellow"></i>Yellow</span>
          <span><i class="sw-amber"></i>Amber</span>
          <span><i class="sw-red"></i>Red</span>
        </div>
      </div>
      <svg class="signal-web-svg" viewBox="0 0 420 380" role="img" aria-label="9 category signal web">
        <circle class="sw-ring sw-ring-red"   cx="210" cy="190" r="47"></circle>
        <circle class="sw-ring sw-ring-amber" cx="210" cy="190" r="81"></circle>
        <circle class="sw-ring sw-ring-green" cx="210" cy="190" r="121.5"></circle>
        <text class="sw-ring-label sw-ring-label-green" x="210" y="62"  text-anchor="middle">Healthy</text>
        <text class="sw-ring-label sw-ring-label-amber" x="210" y="105" text-anchor="middle">Watch</text>
        <text class="sw-ring-label sw-ring-label-red"   x="210" y="138" text-anchor="middle">Escalate</text>
        ${axisLines}
        <polygon class="sw-web-current" points="${catPolygonPoints(statuses)}"></polygon>
        ${dots}
        <circle class="sw-center sw-${statusClass(overall)}" cx="210" cy="190" r="5">
          <title>Overall governance state: ${esc(normalizeStatus(overall) || overall || "No data")}</title>
        </circle>
      </svg>
    </section>`;
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
        ${signalWebHtml(p)}
        ${executiveBriefHtml(p)}
        <div class="detail-grid">
         <section class="panel detail-ledger" aria-label="Signal ledger (project detail)"></section>
         <section class="panel detail-decision" aria-label="PCEIF governance decision (project detail)"></section>
       </div>
       <section class="panel detail-ingest" aria-label="Ingest to this project">
         <details class="kn-topic"${populated ? "" : " open"}>
           <summary>Ingest to this project (${esc(p.id)}) — populate signals / document-risk</summary>
           <p class="kn-sub" style="margin-top:8px">Pre-scoped to this project. Populate runs the real Monte Carlo + CUSUM; document-risk uses the transparent keyword rules with mandatory Approve/Reject.</p>
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
