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

  /* ---------- project number validation (shared by create + rename) ----------
     Rules: non-empty, none of / \ " ' (they break Drive paths + attribute
     contexts), and not already used by any loaded project (case-insensitive).
     Uniqueness is re-enforced server-side. Returns an error string or null. */
  const BAD_ID_CHARS = /[\/\\"']/;
  function validateProjectNumber(id, excludeId) {
    if (!id) return "Enter a project number / code.";
    if (BAD_ID_CHARS.test(id)) return "The project number can't contain / \\ \" or ' characters.";
    const all = LinStore.cachedActive().concat(LinStore.cachedArchived());
    const clash = all.some((p) =>
      p.id !== excludeId && String(p.id).toLowerCase() === id.toLowerCase());
    if (clash) return "Project number “" + id + "” is already in use.";
    return null;
  }

  /* ---------- geocode outcome (shared by edit + create) ----------
     Backend v10.29 geocodes server-side in saveProject_ whenever the saved
     address changed, echoing lat/lng/formattedAddress or a human-readable
     geocodeError on the returned project. PMs never type coordinates. */
  function geocodeOutcome(saved) {
    if (!saved) return null;
    if (saved.geocodeError) {
      // the backend message is already human-readable and usually carries its
      // own "refine and save again" instruction — don't repeat it
      const hint = /refine|save again/i.test(saved.geocodeError) ? "" : " — refine the address and save again.";
      return { ok: false, text: "Couldn't locate this address: " + saved.geocodeError + hint };
    }
    if (saved.formattedAddress || saved.lat != null) return { ok: true, text: "Located: " + (saved.formattedAddress || saved.address) };
    return null;
  }

  /* Unified inline "Edit info" panel — project number, name, and address in
     one place (merges the old Edit № affordance). Sector is shown read-only:
     it drives simulation rules and is not editable here. The address is the
     ONLY location field — the backend geocodes it server-side on save, and
     the outcome (formatted address or geocode error) surfaces inline. */
  function openEditInfo(btn) {
    const id = btn.dataset.editinfo;
    const row = btn.closest(".pr-row");
    if (!row) return;
    if (row.nextElementSibling && row.nextElementSibling.classList.contains("pr-editnum")) return;
    const cached = LinStore.getCached(id) || {};
    const box = document.createElement("div");
    box.className = "pr-editnum pr-editinfo";
    box.innerHTML =
      `<div class="pr-editinfo-grid">
         <label class="rationale-label">Project number / code
           <input type="text" class="pe-id ig-input" maxlength="40" placeholder="e.g. AP-2026-014" /></label>
         <label class="rationale-label">Project name
           <input type="text" class="pe-name ig-input" maxlength="80" /></label>
         <label class="rationale-label">Sector (read-only — drives simulation rules)
           <input type="text" class="pe-sector ig-input" disabled /></label>
         <label class="rationale-label pr-editinfo-addr">Address (optional — located automatically on save)
           <input type="text" class="pe-address ig-input" maxlength="160" placeholder="e.g. Terminal B, Austin-Bergstrom Intl Airport" /></label>
       </div>
       <div class="dc-actions">
         <button class="btn primary small pe-save">Save</button>
         <button class="btn small pe-cancel">Cancel</button>
       </div>
       <p class="pe-msg kn-sub" aria-live="polite"></p>`;
    row.insertAdjacentElement("afterend", box);
    // values via properties — legacy data may predate the charset rules
    box.querySelector(".pe-id").value = id;
    box.querySelector(".pe-name").value = cached.name || "";
    box.querySelector(".pe-sector").value = SECTOR_LABEL[cached.sector] || cached.sector || "";
    box.querySelector(".pe-address").value = cached.address || "";
    // show the current geocoded state so the PM knows where the pin sits now
    if (cached.formattedAddress && cached.lat != null) {
      box.querySelector(".pe-msg").textContent = "Located: " + cached.formattedAddress;
    }
    box.querySelector(".pe-id").focus();

    const close = () => box.remove();
    box.querySelector(".pe-cancel").addEventListener("click", close);
    box.addEventListener("keydown", (e) => { if (e.key === "Escape") close(); });
    box.querySelector(".pe-save").addEventListener("click", async () => {
      const msg = box.querySelector(".pe-msg");
      msg.classList.remove("pe-msg-error", "pe-msg-ok");
      const newId = box.querySelector(".pe-id").value.trim();
      const name = box.querySelector(".pe-name").value.trim();
      const address = box.querySelector(".pe-address").value.trim();
      if (newId !== id) {
        const idErr = validateProjectNumber(newId, id);
        if (idErr) { msg.textContent = idErr; return; }
      }
      if (name.length < 3) { msg.textContent = "Enter a project name (min 3 characters)."; return; }
      const save = box.querySelector(".pe-save");
      save.disabled = true;
      msg.textContent = address ? "Saving — locating address…" : "Saving project info…";
      try {
        // ALWAYS mutate the full project.json — never save a slim stub back
        // to Drive (that would drop signals/history from the stored file).
        const full = await LinStore.getProject(id);
        if (!full || full.slim) throw new Error("couldn't load the full project record");
        full.name = name;
        full.address = address || null;
        // the save response echoes the updated project, including the
        // server-side geocode result (lat/lng/formattedAddress/geocodeError)
        const saved = await LinStore.saveProject(full);
        // number change last — it re-keys the Drive folder + mirrors
        if (newId !== id) {
          await LinStore.setProjectNumber(id, newId);
          if (window.LinApp && LinApp.renameSelection) LinApp.renameSelection(id, newId);
          if (window.LinSignals && LinSignals.clearCache) LinSignals.clearCache(id);
        }
        logEvent(`EDITED project info for ${newId}${newId !== id ? ` (was ${id})` : ""}: name/address updated.`);
        await LinStore.load();
        if (window.LinApp) LinApp.refresh();
        renderManagePage();
        // Surface the geocode outcome inline: re-open the (re-rendered) panel
        // and show "Located: …" or the geocode error so the PM can refine.
        const outcome = address ? geocodeOutcome(saved) : null;
        if (outcome) {
          const finalId = newId !== id ? newId : id;
          const btn2 = document.querySelector(`#manage-root [data-editinfo="${finalId}"]`);
          if (btn2) {
            openEditInfo(btn2);
            const box2 = btn2.closest(".pr-row").nextElementSibling;
            const msg2 = box2 && box2.querySelector(".pe-msg");
            if (msg2) {
              msg2.textContent = outcome.text;
              msg2.classList.add(outcome.ok ? "pe-msg-ok" : "pe-msg-error");
              box2.scrollIntoView({ block: "center" });
            }
          }
        }
      } catch (e) {
        msg.textContent = "Couldn't save: " + ((e && e.message) || "store unreachable") + ".";
        msg.classList.add("pe-msg-error");
        save.disabled = false;
      }
    });
  }

  /* ---------- Manage Projects page ---------- */
  function renderManagePage() {
    const root = document.getElementById("manage-root");
    if (!root) return;

    const rowFor = (p) => {
      // Slim portfolio records carry EVM summary fields; slimStatusLabel resolves
      // a 5-state label from them (or the backend label). Full records derive it.
      const slimLabel = (p && p.slim && typeof slimStatusLabel === "function") ? slimStatusLabel(p) : null;
      const populated = slimLabel ? true : hasSignals(p);
      const state = slimLabel || (hasSignals(p) ? deriveHealthState(p) : "Awaiting ingest");
      const key = populated ? state.toLowerCase().replace("-review", "") : "empty";
      return `<div class="pr-row">
        <span class="pr-code">${esc(p.id)}</span>
        <span class="pr-name">${esc(p.name)} <span class="kn-sub">· ${esc(SECTOR_LABEL[p.sector] || p.sector)}</span></span>
        <span class="li-state state-${key}">${esc(state)}</span>
        <span class="pr-actions">
          <button class="btn small" data-detail="${esc(p.id)}">Detail</button>
          <button class="btn small" data-editinfo="${esc(p.id)}" title="Edit project number, name, address, and map coordinates">Edit info</button>
          <button class="btn small" data-populate="${esc(p.id)}">${populated ? "Re-upload" : "Populate"}</button>
          <button class="btn small" data-archive="${esc(p.id)}">Archive</button>
        </span>
      </div>`;
    };

    const active = LinStore.cachedActive();
    const archived = LinStore.cachedArchived();
    const cs = window.collapsibleSection || function (id, t, body) { return body; };

    /* CREATE NEW PROJECT — collapsed by default; expands when a PM needs it.
       The project number is assigned by the PM (no auto-numbering). */
    const createBody =
      `<p class="kn-sub">Assign your own project number, then a name and sector. Upload documents to get started.</p>
       <label class="rationale-label" for="np-id">Project number / code <span class="req">(required)</span></label>
       <input id="np-id" class="ig-input" maxlength="40" placeholder="e.g. AP-2026-014" />
       <label class="rationale-label" for="np-name">Project name</label>
       <input id="np-name" class="ig-input" maxlength="80" placeholder="e.g. Terminal B Expansion" />
       <label class="rationale-label" for="np-address">Address (optional — located automatically on save)</label>
       <input id="np-address" class="ig-input" maxlength="160" placeholder="e.g. Terminal B, Austin-Bergstrom Intl Airport" />
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

    /* UPLOAD DOCUMENTS — collapsed by default. Drag-and-drop multi-file ingest:
       drop any combination, Lin identifies each document type automatically. */
    const uploadBody =
      `<p class="kn-sub">Drop one or more documents below. Lin identifies each document type automatically and extracts the signals — no need to label them first.</p>
       ${LinSignals.dropzoneHtml(null)}
       <div id="signals-detail" class="ds-detail-wrap"></div>`;

    /* Everything starts collapsed except ACTIVE PROJECTS — the page's purpose;
       a fully blank Manage page is worse UX. This is the single deliberate
       exception to the collapsed-by-default rule. */
    root.innerHTML =
      cs("mg-create",   "CREATE NEW PROJECT",  createBody,   false) +
      cs("mg-active",   "ACTIVE PROJECTS",     activeBody,   true,  active.length + " project" + (active.length === 1 ? "" : "s")) +
      cs("mg-archived", "ARCHIVED PROJECTS",   archivedBody, false, archived.length + " project" + (archived.length === 1 ? "" : "s")) +
      `<div id="signals-panel">` +
        cs("mg-upload", "UPLOAD DOCUMENTS",    uploadBody,   false) +
      `</div>` +
      cs("mg-activity", "RECENT ACTIVITY", `<div id="ingest-log"></div>`, false,
         ingestLog.length ? ingestLog.length + " event" + (ingestLog.length === 1 ? "" : "s") : "");

    renderLog();
    // drag-and-drop multi-file ingest (identify → auto-confirm/override → extract);
    // on each result, render the signals detail panel (extracted / missing / audit).
    LinSignals.wireDropzone(root.querySelector("#signals-panel"), (id) => {
      const panel = root.querySelector("#signals-detail");
      if (panel) LinSignals.renderSignalsPanel(panel, LinStore.getCached(id));
    });

    document.getElementById("np-create").addEventListener("click", async () => {
      const id = document.getElementById("np-id").value.trim();
      const name = document.getElementById("np-name").value.trim();
      const sector = document.getElementById("np-sector").value;
      const address = document.getElementById("np-address").value.trim();
      const msg = document.getElementById("np-msg");
      const idErr = validateProjectNumber(id);
      if (idErr) { msg.textContent = idErr; return; }
      if (name.length < 3) { msg.textContent = "Enter a project name (min 3 characters)."; return; }
      msg.textContent = address ? "Creating project — locating address…" : "Creating project in the store…";
      try {
        const p = await LinStore.createProject({ id, name, sector });
        // the optional address persists via the normal save flow (the create
        // endpoint only takes id/name/sector); the backend geocodes on save
        let outcome = null;
        if (address) {
          p.address = address;
          const saved = await LinStore.saveProject(p);
          outcome = geocodeOutcome(saved);
        }
        logEvent(`Created EMPTY project ${p.id} — ${name} (${SECTOR_LABEL[sector] || sector}); awaiting ingest.`);
        if (window.LinApp) LinApp.refresh();
        renderManagePage();
        const msg2 = document.getElementById("np-msg");
        msg2.textContent = `Created ${p.id} (empty, saved to Drive).` +
          (outcome ? " " + outcome.text : " Populate its signals to run the models.");
        msg2.classList.toggle("pe-msg-error", !!(outcome && !outcome.ok));
      } catch (e) {
        msg.textContent = "Couldn't create the project: " + ((e && e.message) || "store unreachable") + ".";
      }
    });

    root.querySelectorAll("[data-archive]").forEach((b) =>
      b.addEventListener("click", async () => { try { await LinStore.archiveProject(b.dataset.archive); logEvent(`ARCHIVED ${b.dataset.archive}.`); if (window.LinApp) LinApp.refresh(); renderManagePage(); } catch (e) { LinStore.banner("Couldn't archive — store unreachable. Retry.", "warn"); } }));
    root.querySelectorAll("[data-detail]").forEach((b) =>
      b.addEventListener("click", () => LinApp.openDetail(b.dataset.detail)));
    root.querySelectorAll("[data-editinfo]").forEach((b) =>
      b.addEventListener("click", () => openEditInfo(b)));
    root.querySelectorAll("[data-populate]").forEach((b) =>
      b.addEventListener("click", () => {
        // Expand the UPLOAD DOCUMENTS section, pre-select this project in the
        // dropzone, and scroll it into view.
        const section = document.getElementById("section-mg-upload");
        if (window.toggleSection && section && !section.classList.contains("open")) toggleSection("mg-upload");
        const sel = root.querySelector(".dz-project");
        if (sel) sel.value = b.dataset.populate;
        const panel = root.querySelector("#signals-panel");
        if (panel) panel.scrollIntoView({ block: "start" });
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
