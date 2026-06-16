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

  const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  const SECTOR_LABEL = { design: "Design", construction: "Construction", hybrid: "Hybrid", combined: "Hybrid" };

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
    const state = populated ? deriveHealthState(p) : "Awaiting ingest";
    const stateKey = populated ? state.toLowerCase().replace("-review", "") : "empty";

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

  window.LinDetail = { render };
})();
