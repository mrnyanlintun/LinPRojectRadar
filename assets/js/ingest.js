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

  /* ---------- keyword doc-ingest proposal (updates the doc signal) ---------- */
  function proposeIngest(projectId, docType, text) {
    const project = LinStore.getCached(projectId);
    if (!project || !text.trim()) return null;
    if (!hasSignals(project)) return { needsPopulate: true, projectId };
    const a = analyzeText(text);
    const fromScore = project.signals.doc.score;
    const newScore = Math.max(0, Math.min(1, fromScore + a.scoreDelta));
    return {
      projectId, docType, fired: a.fired, excerpt: a.excerpt,
      from: { score: fromScore, status: project.signals.doc.status },
      to: { score: newScore, status: LinSim.docStatus(newScore) }
    };
  }
  async function applyProposal(prop) {
    const project = LinStore.getCached(prop.projectId);
    if (!project || !hasSignals(project)) return;
    // Rebuild the package so the new doc score flows through MC spread + statuses.
    await rebuildWithDocScore(project, prop.to.score, `(ingested) ${prop.docType}`, prop.excerpt || project.signals.doc.excerpt);
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
      : `<p class="kn-sub">No ingest events this browser yet.</p>`;
  }

  /* ---------- shared keyword-ingest form (Manage panel + Project Detail) ---------- */
  function ingestFormHtml(fixedId) {
    const projectField = fixedId
      ? `<input type="hidden" class="ig-project" value="${esc(fixedId)}" />`
      : `<label class="rationale-label">Project
           <select class="ig-project ig-input">${projectOptions()}</select></label>`;
    return `
      <div class="kn-grid">
        <div>
          ${projectField}
          <label class="rationale-label">Document type
            <select class="ig-doctype ig-input">${DOC_TYPES.map((d) => `<option>${d}</option>`).join("")}</select></label>
          <details class="kn-topic"><summary>The keyword rules that will run (visible by design)</summary>
            <ul class="ig-fired">${INGEST_RULES.map((r) =>
              `<li><span class="mod-mono">${esc(r.id)}</span> ${esc(r.label)} — /${esc(r.pattern.source)}/i → doc ${r.scoreDelta >= 0 ? "+" : ""}${r.scoreDelta.toFixed(2)}</li>`).join("")}
            </ul>
          </details>
        </div>
        <div>
          <label class="rationale-label">Document text (RFI / RFA / meeting minutes)
            <textarea class="ig-text ig-textarea" placeholder="Paste document text here, or load a file below…"></textarea></label>
          <input type="file" class="ig-file" accept=".txt,.csv,.md,.text" aria-label="Load text file" />
          <label class="rationale-label">Spec / code excerpt to compare against (optional, .md or pasted)
            <textarea class="ig-spec ig-textarea" placeholder="Optional: paste the relevant spec/code clause to check the document against (enables a CONFLICT / GAP / CONSISTENT verdict)."></textarea></label>
          <div class="dc-actions"><button class="btn primary ig-run">Run extraction</button></div>
        </div>
      </div>
      <div class="ig-result" aria-live="polite"></div>
      <div class="ig-analysis" aria-live="polite"></div>`;
  }

  function renderProposal(prop, box, onApplied) {
    if (!prop) {
      box.innerHTML = `<p class="kn-sub">No risk rules matched this text. No change proposed — nothing to approve.</p>`;
      return;
    }
    if (prop.needsPopulate) {
      box.innerHTML = `<p class="kn-sub">This project has no signals yet — populate its signals first (Monte Carlo / CUSUM inputs), then document-risk ingest can update the doc signal.</p>`;
      return;
    }
    const firedHtml = prop.fired.length
      ? prop.fired.map((f) =>
          `<li><strong>${esc(f.rule.label)}</strong> <span class="mod-mono">(${esc(f.rule.id)})</span> — matched “${esc(f.match)}” → doc ${f.rule.scoreDelta >= 0 ? "+" : ""}${f.rule.scoreDelta.toFixed(2)}</li>`).join("")
      : "<li>No rules fired.</li>";
    box.innerHTML =
      `<h3 class="kn-defterm">Proposed document-risk delta — human approval required</h3>
       <ul class="ig-fired">${firedHtml}</ul>
       <div class="ig-delta mod-mono">doc score ${prop.from.score.toFixed(2)} → <strong>${prop.to.score.toFixed(2)}</strong> (${esc(prop.from.status)} → <strong>${esc(prop.to.status)}</strong>)</div>
       ${prop.excerpt ? `<p class="ig-excerpt">Evidence excerpt: “${esc(prop.excerpt)}”</p>` : ""}
       <div class="dc-actions">
         <button class="btn primary ig-approve">Approve — apply to project</button>
         <button class="btn ig-reject">Reject — discard</button>
       </div>
       <p class="dc-note">Nothing changes until Approve is clicked. The whole signal package is re-derived so the new document score flows through the Monte Carlo spread and the decision.</p>`;
    box.querySelector(".ig-approve").addEventListener("click", async () => {
      box.innerHTML = `<p class="kn-sub">Saving to the project store…</p>`;
      try {
        await applyProposal(prop);
        logEvent(`APPROVED doc ingest (${prop.docType}) on ${prop.projectId}: doc ${prop.from.score.toFixed(2)}→${prop.to.score.toFixed(2)}. Rules: ${prop.fired.map((f) => f.rule.id).join(", ") || "none"}.`);
        box.innerHTML = `<p class="kn-sub">Applied and re-derived. Saved to Drive; re-plotted and re-run through the decision rules.</p>`;
        pendingProposal = null;
        if (window.LinApp) LinApp.refresh();
        if (onApplied) onApplied(prop.projectId);
      } catch (e) {
        box.innerHTML = `<p class="kn-sub">Couldn't save to the project store — change not applied. Retry.</p>`;
      }
    });
    box.querySelector(".ig-reject").addEventListener("click", () => {
      logEvent(`REJECTED doc ingest (${prop.docType}) on ${prop.projectId}. No state change.`);
      box.innerHTML = `<p class="kn-sub">Proposal discarded. No project state was changed.</p>`;
      pendingProposal = null;
    });
  }

  function wireIngestForm(container, onApplied) {
    const $c = (sel) => container.querySelector(sel);
    $c(".ig-file").addEventListener("change", (e) => {
      const f = e.target.files && e.target.files[0];
      if (!f) return;
      const reader = new FileReader();
      reader.onload = () => { $c(".ig-text").value = String(reader.result || "").slice(0, 20000); };
      reader.readAsText(f);
    });
    $c(".ig-run").addEventListener("click", () => {
      const projectId = $c(".ig-project").value;
      const docType = $c(".ig-doctype").value;
      const text = $c(".ig-text").value;
      const spec = ($c(".ig-spec") && $c(".ig-spec").value || "").trim();
      const box = $c(".ig-result");
      if (!text.trim()) { box.innerHTML = `<p class="kn-sub">Paste or load some document text first.</p>`; return; }

      // 1) transparent keyword layer — produces the actual signal delta + evidence,
      //    gated by Approve/Reject (unchanged, praxis-required base).
      pendingProposal = proposeIngest(projectId, docType, text);
      const fired = pendingProposal && pendingProposal.fired ? pendingProposal.fired.length : 0;
      logEvent(`Ran doc extraction (${docType}) on ${projectId}: ${pendingProposal && pendingProposal.needsPopulate ? "project not populated yet" : fired + " rule(s) fired — awaiting human review"}.`);
      renderProposal(pendingProposal && (pendingProposal.needsPopulate || pendingProposal.fired.length) ? pendingProposal : null, box, onApplied);

      // 2) AI explanatory layer — supporting analysis only (enhancement, not a
      //    dependency; keyword ingest above stands alone if this fails).
      runAnalyze($c(".ig-analysis"), { text, docType, spec, id: projectId });
    });
  }

  /* AI document analysis (Groq via backend). Clearly labeled illustrative;
     never gates the keyword signal. Non-fatal on failure. */
  async function runAnalyze(box, { text, docType, spec, id }) {
    if (!box) return;
    if (!(window.LinStore && LinStore.configured && LinStore.configured())) {
      box.innerHTML = `<p class="kn-sub">AI analysis unavailable (backend not configured). Keyword extraction above is unaffected.</p>`;
      return;
    }
    box.innerHTML = `<p class="kn-sub"><em>Running AI document analysis${spec ? " with spec comparison" : ""}…</em></p>`;
    try {
      const analysis = await LinStore.analyze({ text, docType, spec: spec || undefined, id });
      if (!analysis || !String(analysis).trim()) {
        box.innerHTML = `<p class="kn-sub">AI analysis returned nothing; keyword extraction above is unaffected.</p>`;
        return;
      }
      const verdict = (String(analysis).match(/\b(CONFLICT|GAP|CONSISTENT)\b/i) || [])[0];
      box.innerHTML =
        `<h3 class="kn-defterm">AI document analysis ${verdict ? `· <span class="ig-verdict v-${verdict.toLowerCase()}">${esc(verdict.toUpperCase())}</span>` : ""}</h3>
         <p class="ig-analysis-text">${esc(String(analysis))}</p>
         <p class="dc-note">Illustrative AI analysis, supporting explanation only (<strong>not a validated compliance determination</strong>). The signal delta is set by the transparent keyword rules above and gated by Approve/Reject.</p>`;
    } catch (e) {
      box.innerHTML = `<p class="kn-sub">AI analysis unreachable — keyword extraction above still works. (Retry later.)</p>`;
    }
  }

  /* The manual "type CPI / SPI / BAC" populate form was removed in Piece C —
     signals now come from document extraction (LinSignals). populateSignals()
     is kept (still exported) as the shared model-run helper. */

  function renderScopedIngest(projectId, container, onApplied) {
    if (!container) return;
    const project = LinStore.getCached(projectId);
    const populated = hasSignals(project);
    container.innerHTML =
      `<h4 class="kn-h" style="font-size:14px">${populated ? "Re-populate signals — upload a document (re-runs Monte Carlo + CUSUM)" : "Populate signals — upload a document (runs Monte Carlo + CUSUM)"}</h4>` +
      `<p class="kn-sub">Upload a real document (pay application, schedule of values, time-phased schedule, …); the backend extracts the EVM figures and, once CPI and SPI are present, runs the models on the extracted values.</p>` +
      LinSignals.ingestFormHtml(projectId) +
      `<h4 class="kn-h" style="font-size:14px;margin-top:14px">Document-risk ingest (keyword extraction)</h4>` +
      ingestFormHtml(projectId);
    // doc-driven extraction → re-render the detail page so charts + signals panel update
    LinSignals.wireIngestForm(container, onApplied);
    wireIngestForm(container, onApplied);
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
          <button class="btn small" data-populate="${esc(p.id)}">${populated ? "Re-populate" : "Populate"}</button>
          <button class="btn small" data-archive="${esc(p.id)}">Archive</button>
        </span>
      </div>`;
    };

    const active = LinStore.cachedActive();
    const archived = LinStore.cachedArchived();

    root.innerHTML =
      `<div class="kn-grid">
        <section class="panel">
          <p class="eyebrow">Create project</p>
          <h2 class="kn-h">New project</h2>
          <p class="kn-sub">A new project is assigned a project number automatically and starts empty. Ingest documents to populate its quantitative project-management analysis.</p>
          <label class="rationale-label" for="np-name">Project name</label>
          <input id="np-name" class="ig-input" maxlength="80" placeholder="e.g. Concourse Wayfinding Refresh" />
          <label class="rationale-label" for="np-sector">Delivery type</label>
          <select id="np-sector" class="ig-input">
            <option value="design">Design</option>
            <option value="construction">Construction</option>
            <option value="hybrid">Hybrid</option>
          </select>
          <div class="dc-actions"><button id="np-create" class="btn primary">Create project</button></div>
          <p id="np-msg" class="kn-sub" aria-live="polite"></p>
        </section>
        <section class="panel">
          <p class="eyebrow">Active (${active.length})</p>
          ${active.map(rowFor).join("") || `<p class="pr-empty">No active projects.</p>`}
          <p class="eyebrow" style="margin-top:16px">Archived</p>
          <div id="archived-list"><p class="pr-empty">Loading archived projects…</p></div>
        </section>
      </div>

      <section class="panel" style="margin-top:18px" id="signals-panel">
        <p class="eyebrow">Populate signals — from documents</p>
        <h2 class="kn-h">Upload a document; the system extracts the EVM figures</h2>
        <p class="kn-sub">A PM doesn't type CPI / SPI / BAC — upload a real document (pay application, schedule of values, time-phased schedule, …) and the backend (Gemini) extracts the figures. When both CPI and SPI are present the app runs the same 5,000-iteration Monte Carlo, two-sided CUSUM, and PCEIF decision on the extracted values. Demonstration models — not calibrated forecasts.</p>
        ${LinSignals.ingestFormHtml(null)}
        <div id="signals-detail" class="ds-detail-wrap"></div>
      </section>

      <section class="panel" style="margin-top:18px" id="ingest-panel">
        <p class="eyebrow">Ingest document</p>
        <h2 class="kn-h">Keyword document-risk extraction (selected project)</h2>
        <p class="kn-sub">Transparent keyword rules update the document-risk signal; a human must Approve before anything changes. (Populate a project's signals first.)</p>
        ${ingestFormHtml(null)}
      </section>

      <section class="panel" style="margin-top:18px">
        <p class="eyebrow">Project event log</p>
        <div id="ingest-log"></div>
      </section>`;

    renderLog();
    // document-driven signal extraction (replaces the manual CPI/SPI/BAC form);
    // on result, render the signals detail panel (extracted / missing / audit).
    LinSignals.wireIngestForm(root.querySelector("#signals-panel"), (id) => {
      const panel = root.querySelector("#signals-detail");
      if (panel) LinSignals.renderSignalsPanel(panel, LinStore.getCached(id));
    });
    wireIngestForm(root.querySelector("#ingest-panel"), (id) => { if (window.LinApp) LinApp.selectProject(id); });

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
          `<span class="pr-code">archived</span>` +
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
