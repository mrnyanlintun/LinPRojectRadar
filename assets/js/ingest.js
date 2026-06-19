/* ============================================================
   lin-project-radar — ingest.js  (Phase 1)
   ------------------------------------------------------------
   Create projects (empty), populate a project's signals from
   ingest inputs (which runs the REAL Monte Carlo + CUSUM via
   sim.js), run the transparent keyword document-risk extraction,
   and the active/archived lifecycle.

   ALL project reads/writes go through store.js (the data seam).
   Phase 1 is localStorage-backed; no network calls. The event
   log is kept separately (UI state, not project data).
   ============================================================ */

(function () {
  "use strict";

  const STORE_LOG = "lpr-ingest-log";
  const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const SECTOR_LABEL = { design: "Design", construction: "Construction", hybrid: "Hybrid", combined: "Hybrid" };

  /* ---------- visible document-risk keyword rules (Module 03, transparent) ---------- */
  const INGEST_RULES = [
    { id: "R1-unresolved", pattern: /unresolved|no committed date|outstanding/i, label: "Unresolved item language", scoreDelta: +0.15 },
    { id: "R2-dispute",    pattern: /dispute|claim|contested|disagreement/i,     label: "Dispute / claim language",   scoreDelta: +0.25 },
    { id: "R3-delay",      pattern: /delay|resequenc|slip|behind schedule|late/i, label: "Schedule-impact language",   scoreDelta: +0.20 },
    { id: "R4-rejected",   pattern: /rejected|resubmit|nonconform|deficien/i,     label: "Rejection / rework language", scoreDelta: +0.20 },
    { id: "R5-cost",       pattern: /overrun|cost growth|change order|escalation/i, label: "Cost-pressure language",   scoreDelta: +0.20 },
    { id: "R6-positive",   pattern: /\bresolved\b|\bclosed\b|on schedule|within budget|approved as submitted/i, label: "Favorable resolution language", scoreDelta: -0.15 }
  ];
  const DOC_TYPES = ["RFI log", "Submittal notes", "QC comments", "Procurement notes", "Meeting minutes"];

  let pendingProposal = null;
  let ingestLog = [];
  try { ingestLog = JSON.parse(localStorage.getItem(STORE_LOG) || "[]"); } catch (e) { ingestLog = []; }
  function saveLog() { try { localStorage.setItem(STORE_LOG, JSON.stringify(ingestLog.slice(0, 80))); } catch (e) {} }
  function logEvent(msg) { ingestLog.unshift({ at: new Date().toISOString(), msg }); saveLog(); renderLog(); }

  /* ---------- keyword extraction (transparent, per praxis) ---------- */
  function analyzeText(text) {
    const fired = [];
    let scoreDelta = 0;
    INGEST_RULES.forEach((r) => {
      const m = text.match(r.pattern);
      if (m) { fired.push({ rule: r, match: m[0] }); scoreDelta += r.scoreDelta; }
    });
    let excerpt = "";
    if (fired.length) {
      const sentences = text.split(/(?<=[.!?])\s+/);
      excerpt = (sentences.find((s) => fired.some((f) => f.rule.pattern.test(s))) || sentences[0] || "").trim().slice(0, 220);
    }
    return { fired, scoreDelta, excerpt };
  }

  /* ---------- populate / rebuild a project's signals (runs sim.js) ---------- */
  async function rebuildWithDocScore(project, docScore, docSource, docExcerpt) {
    const e = project.signals.evm;
    const cu = project.signals.cusum;
    project.signals = LinSim.buildSignals({
      cpi: e.cpi, spi: e.spi, bac: e.bac, metric: cu.metric, series: cu.series,
      docScore, docSource, docExcerpt, seed: LinSim.hashSeed(project.id)
    });
    await LinStore.saveProject(project);
  }

  async function populateSignals(project, inputs) {
    const doc = inputs.docText ? analyzeText(inputs.docText) : { fired: [], scoreDelta: 0, excerpt: "" };
    const docScore = inputs.docText ? Math.max(0, Math.min(1, 0.1 + doc.scoreDelta)) : (Number(inputs.docScore) || 0.1);
    const series = (inputs.seriesText || "").trim()
      ? inputs.seriesText.split(/[,\s]+/).map(Number).filter(Number.isFinite)
      : undefined;
    project.signals = LinSim.buildSignals({
      cpi: Number(inputs.cpi), spi: Number(inputs.spi), bac: Number(inputs.bac) || undefined,
      metric: inputs.metric || "SPI", series, docScore,
      docSource: inputs.docText ? "(ingested document)" : "(manual signal entry)",
      docExcerpt: doc.excerpt || undefined, seed: LinSim.hashSeed(project.id)
    });
    project.fairnessSensitive = !!inputs.fairnessSensitive;
    await LinStore.saveProject(project);
    logEvent(`POPULATED signals for ${project.id}: CPI ${Number(inputs.cpi).toFixed(2)}, SPI ${Number(inputs.spi).toFixed(2)} → MC ran 5,000 iters (P80 ${project.signals.mc.p80.toFixed(1)}), CUSUM ${project.signals.cusum.breached ? "BREACH" : "in-control"}, doc ${docScore.toFixed(2)}.`);
  }

  /* ---------- page rendering ---------- */
  function projectOptions() {
    return LinStore.cachedActive().map((p) => `<option value="${esc(p.id)}">${esc(p.id)} — ${esc(p.name)}</option>`).join("");
  }
  function renderLog() {
    const elLog = document.getElementById("ingest-log");
    if (!elLog) return;
    elLog.innerHTML = ingestLog.length
      ? ingestLog.slice(0, 25).map((e) =>
          `<div class="ig-log-entry"><span class="mod-mono">${esc(window.LinTZ ? LinTZ.format(e.at) : e.at)}</span> ${esc(e.msg)}</div>`).join("")
      : `<p class="kn-sub">Nothing yet. Upload a document to get started.</p>`;
  }

  /* The keyword document-risk ingest panel was removed — document ingestion now
     goes through the single LinSignals "Ingest Document" panel (file upload →
     extractsignals). The keyword rules + analyzeText remain only as a helper. */

  /* The manual "type CPI / SPI / BAC" populate form was removed in Piece C —
     signals now come from document extraction (LinSignals). populateSignals()
     is kept (still exported) as the shared model-run helper. */

  function renderScopedIngest(projectId, container, onApplied) {
    if (!container) return;
    const project = LinStore.getCached(projectId);
    const populated = hasSignals(project);
    container.innerHTML =
      `<h4 class="kn-h" style="font-size:14px">Upload a Document</h4>` +
      `<p class="kn-sub">Upload a contract, pay application, schedule, or RFI. The system reads the figures and updates the project signals automatically.</p>` +
      LinSignals.ingestFormHtml(projectId);
    // doc-driven extraction → re-render the detail page so charts + signals panel update
    LinSignals.wireIngestForm(container, onApplied);
  }

  /* ---------- Manage Projects page ---------- */
  function renderManagePage() {
    const root = document.getElementById("manage-root");
    if (!root) return;

    const rowFor = (p) => {
      const populated = hasSignals(p);
      const state = populated ? deriveHealthState(p) : "Awaiting ingest";
      const key = populated ? state.toLowerCase().replace("-review", "") : "empty";
      return `<div class="pr-row">
        <span class="pr-code">${esc(p.id)}</span>
        <span class="pr-name">${esc(p.name)} <span class="kn-sub">· ${esc(SECTOR_LABEL[p.sector] || p.sector)}</span></span>
        <span class="li-state state-${key}">${esc(state)}</span>
        <span class="pr-actions">
          <button class="btn small" data-detail="${esc(p.id)}">Detail</button>
          <button class="btn small" data-populate="${esc(p.id)}">${populated ? "Re-upload" : "Populate"}</button>
          <button class="btn small" data-archive="${esc(p.id)}">Archive</button>
        </span>
      </div>`;
    };

    const active = LinStore.cachedActive();
    const archived = LinStore.cachedArchived();
    const cs = window.collapsibleSection || function (id, t, body) { return body; };

    /* CREATE NEW PROJECT — collapsed by default; expands when a PM needs it. */
    const createBody =
      `<p class="kn-sub">Give your project a name and sector. Upload documents to get started.</p>
       <label class="rationale-label" for="np-name">Project name</label>
       <input id="np-name" class="ig-input" maxlength="80" placeholder="e.g. Terminal B Expansion" />
       <label class="rationale-label" for="np-sector">Sector</label>
       <select id="np-sector" class="ig-input">
         <option value="design">Design</option>
         <option value="construction">Construction</option>
         <option value="hybrid">Hybrid</option>
       </select>
       <div class="dc-actions"><button id="np-create" class="btn primary">Create project</button></div>
       <p id="np-msg" class="kn-sub" aria-live="polite"></p>`;

    /* ACTIVE PROJECTS — open by default; the primary view of this page. */
    const activeBody = active.map(rowFor).join("") || `<p class="pr-empty">No active projects.</p>`;

    /* ARCHIVED PROJECTS — collapsed by default. The empty-state copy lives
       inside the body so it shows when the user expands the section. */
    const archivedBody = `<div id="archived-list"><p class="pr-empty">Loading archived projects…</p></div>`;

    /* UPLOAD DOCUMENTS — collapsed by default. Same ingest form as before. */
    const uploadBody =
      `<p class="kn-sub">Upload a contract, pay application, schedule, or RFI. The system reads the figures and updates the project signals automatically.</p>
       ${LinSignals.ingestFormHtml(null)}
       <div id="signals-detail" class="ds-detail-wrap"></div>`;

    root.innerHTML =
      cs("mg-create",   "CREATE NEW PROJECT",  createBody,   false) +
      cs("mg-active",   "ACTIVE PROJECTS",     activeBody,   true,  active.length + " project" + (active.length === 1 ? "" : "s")) +
      cs("mg-archived", "ARCHIVED PROJECTS",   archivedBody, false, archived.length + " project" + (archived.length === 1 ? "" : "s")) +
      `<div id="signals-panel">` +
        cs("mg-upload", "UPLOAD DOCUMENTS",    uploadBody,   false) +
      `</div>` +
      `<section class="panel" style="margin-top:18px">
        <p class="eyebrow">Recent Activity</p>
        <div id="ingest-log"></div>
      </section>`;

    renderLog();
    // document-driven signal extraction (replaces the manual CPI/SPI/BAC form);
    // on result, render the signals detail panel (extracted / missing / audit).
    LinSignals.wireIngestForm(root.querySelector("#signals-panel"), (id) => {
      const panel = root.querySelector("#signals-detail");
      if (panel) LinSignals.renderSignalsPanel(panel, LinStore.getCached(id));
    });

    document.getElementById("np-create").addEventListener("click", async () => {
      const name = document.getElementById("np-name").value.trim();
      const sector = document.getElementById("np-sector").value;
      const msg = document.getElementById("np-msg");
      if (name.length < 3) { msg.textContent = "Enter a project name (min 3 characters)."; return; }
      msg.textContent = "Creating project in the store…";
      try {
        const p = await LinStore.createProject({ name, sector });
        logEvent(`Created EMPTY project ${p.id} — ${name} (${SECTOR_LABEL[sector] || sector}); awaiting ingest.`);
        if (window.LinApp) LinApp.refresh();
        renderManagePage();
        document.getElementById("np-msg").textContent = `Created ${p.id} (empty, saved to Drive). Populate its signals to run the models.`;
      } catch (e) {
        msg.textContent = "Couldn't reach the project store to create the project. Retry.";
      }
    });

    root.querySelectorAll("[data-archive]").forEach((b) =>
      b.addEventListener("click", async () => { try { await LinStore.archiveProject(b.dataset.archive); logEvent(`ARCHIVED ${b.dataset.archive}.`); if (window.LinApp) LinApp.refresh(); renderManagePage(); } catch (e) { LinStore.banner("Couldn't archive — store unreachable. Retry.", "warn"); } }));
    root.querySelectorAll("[data-detail]").forEach((b) =>
      b.addEventListener("click", () => LinApp.openDetail(b.dataset.detail)));
    root.querySelectorAll("[data-populate]").forEach((b) =>
      b.addEventListener("click", () => {
        root.querySelector("#populate-panel .ps-project").value = b.dataset.populate;
        root.querySelector("#populate-panel").scrollIntoView({ block: "start" });
      }));

    // async: load the archived list from the backend and wire Restore
    loadArchivedList(root);
  }

  async function loadArchivedList(root) {
    const box = root.querySelector("#archived-list");
    if (!box) return;
    let archived = [];
    try { archived = await LinStore.listArchived(); }
    catch (e) { box.innerHTML = `<p class="pr-empty">Couldn't load archived projects. Retry.</p>`; return; }
    box.innerHTML = archived.length
      ? archived.map((p) =>
          `<div class="pr-row"><span class="pr-code">${esc(p.id)}</span>` +
          `<span class="pr-name">${esc(p.name)} <span class="kn-sub">· ${esc(SECTOR_LABEL[p.sector] || p.sector)}</span></span>` +
          `<span class="pr-code">Archived</span>` +
          `<button class="btn small" data-restore="${esc(p.id)}">Restore</button></div>`).join("")
      : `<p class="pr-empty">Nothing archived. Archiving moves a project's folder to <span class="mod-mono">00_Archive</span> in Drive.</p>`;
    box.querySelectorAll("[data-restore]").forEach((b) =>
      b.addEventListener("click", async () => {
        try {
          await LinStore.restoreProject(b.dataset.restore);
          logEvent(`RESTORED ${b.dataset.restore}.`);
          if (window.LinApp) LinApp.refresh();
          renderManagePage();
        } catch (e) { LinStore.banner("Couldn't restore — store unreachable. Retry.", "warn"); }
      }));
  }

  // Phase 2 seam kept for API compatibility; store.js already hydrates.
  function mergeUserProjects() {}

  window.LinIngest = { mergeUserProjects, renderManagePage, renderScopedIngest, populateSignals, INGEST_RULES };
})();
