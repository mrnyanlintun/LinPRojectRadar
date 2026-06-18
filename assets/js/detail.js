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
    return 0; // no data — plot at centre so the 19-sided polygon stays closed
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
  function signalWebHtml(project) {
    if (!window.hasSignals || !hasSignals(project)) return "";
    const all = snapshots(project);
    const cur = currentSnapshot(project);
    if (!cur) return "";
    const currentPeriod = cur.period;
    const chosenPeriod = selectedHistoryPeriod[project.id] || currentPeriod;
    const selected = all.find((h) => h.period === chosenPeriod) || cur;
    const selectedIndex = all.findIndex((h) => h.period === selected.period);
    const previous = selectedIndex > 0 ? all[selectedIndex - 1] : null;
    const statuses = moduleStatuses(selected);
    const previousStatuses = previous ? moduleStatuses(previous) : null;
    const axis = MODULES.map((m, i) => {
      const p = pointFor(i, 1, 150);
      return `<line class="sw-axis" x1="210" y1="190" x2="${p.ax.toFixed(1)}" y2="${p.ay.toFixed(1)}"></line>`;
    }).join("");
    const dots = MODULES.map((m, i) => {
      const p = pointFor(i, 1, 150);
      const status = statuses[i];
      const dot = pointFor(i, statusToRadius(status), 150);
      const labelAnchor = Math.abs(p.tx - 210) < 12 ? "middle" : (p.tx > 210 ? "start" : "end");
      return `<text class="sw-label" x="${p.tx.toFixed(1)}" y="${p.ty.toFixed(1)}" text-anchor="${labelAnchor}">${m[0]}</text>
        <circle class="sw-dot sw-${statusClass(status)}" cx="${dot.x.toFixed(1)}" cy="${dot.y.toFixed(1)}" r="4">
          <title>${esc(m[0] + " — " + m[1] + "\nStatus: " + (normalizeStatus(status) || "No data") + "\n" + metricFor(selected, MODULE_KEYS[i]))}</title>
        </circle>`;
    }).join("");
    const overall = selected.governance && selected.governance.state;
    const pills = all.slice().reverse().map((h) => {
      const st = h.governance && h.governance.state;
      return `<button class="sw-history-pill ${h.period === selected.period ? "active" : ""}" data-history-period="${esc(h.period)}">
        <i class="sw-${statusClass(st)}"></i>${esc(periodLabel(h.period))}</button>`;
    }).join("");
    const history = all.length > 1
      ? `<div class="sw-history-row"><p class="eyebrow">Reporting history</p><div>${pills}</div></div>`
      : `<div class="sw-history-row"><p class="eyebrow">Reporting history</p><p class="kn-sub">First reporting period — no prior history.</p></div>`;
    return `<section class="panel signal-web-panel">
      <div class="sw-head">
        <div>
          <p class="eyebrow">Signal Web — ${esc(periodTitle(selected.period))}</p>
          ${previous ? `<p class="kn-sub sw-vs"><span class="sw-prev-key"></span> vs ${esc(periodLabel(previous.period))}</p>` : ""}
        </div>
        <div class="sw-legend" aria-label="Signal web legend">
          <span><i class="sw-complete"></i>Complete</span>
          <span><i class="sw-green"></i>Green</span>
          <span><i class="sw-yellow"></i>Yellow</span>
          <span><i class="sw-amber"></i>Amber</span>
          <span><i class="sw-red"></i>Red</span>
        </div>
      </div>
      <svg class="signal-web-svg" viewBox="0 0 420 380" role="img" aria-label="19 module signal web">
        <circle class="sw-ring sw-ring-green" cx="210" cy="190" r="37.5"></circle>
        <circle class="sw-ring sw-ring-yellow" cx="210" cy="190" r="67.5"></circle>
        <circle class="sw-ring sw-ring-amber" cx="210" cy="190" r="105"></circle>
        <circle class="sw-ring sw-ring-red" cx="210" cy="190" r="150"></circle>
        ${axis}
        ${previousStatuses ? `<polygon class="sw-web-prev" points="${polygonPoints(previousStatuses)}"></polygon>` : ""}
        <polygon class="sw-web-current" points="${polygonPoints(statuses)}"></polygon>
        ${dots}
        <circle class="sw-center sw-${statusClass(overall)}" cx="210" cy="190" r="5">
          <title>Overall governance state: ${esc(normalizeStatus(overall) || overall || "No data")}</title>
        </circle>
      </svg>
      ${history}
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
