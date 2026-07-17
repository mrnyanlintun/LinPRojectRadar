/* ============================================================
   lin-project-radar — store.js  (Phase 2: Drive-backed)
   ------------------------------------------------------------
   The single data-access seam. Phase 1 was localStorage; Phase 2
   talks to a Google Apps Script Web App (one endpoint, LIN_API_URL):
     GET  ?action=list            → { ok, projects:[...] }
     GET  ?action=get&id=01       → { ok, project:{...} }
     POST {action:"create",name,sector} → { ok, project:{...} }
     POST {action:"save",project} → { ok, project:{...} }

   CORS: Apps Script Web Apps can't set arbitrary CORS headers, so
   we only ever make "simple requests" to skip the preflight —
   GETs with no custom headers, and POSTs with
   Content-Type: text/plain;charset=UTF-8 (the body is still a JSON
   string; the backend JSON.parses e.postData.contents). We set NO
   custom headers (no X-*, no Authorization) anywhere.

   The UI keeps reading the in-memory mirrors window.LIN_PROJECTS /
   window.LIN_ARCHIVED (so render code stays synchronous). store
   hydrates them from the backend and mirrors the last good list to
   localStorage as a CACHE ONLY — Drive is the source of truth.
   Archive is a project flag (archived:true) persisted via save,
   since the backend exposes only list/get/create/save.
   ============================================================ */

(function () {
  "use strict";

  const CACHE_KEY = "lpr-cache-list-v2";
  // Slim portfolio cache (v10.28 listslim) — a small id/name/sector/status list
  // that paints the radar + list instantly on load before the network responds.
  const PORTFOLIO_CACHE_KEY = "lin-portfolio-cache";
  const url = () => (window.LIN_API_URL || "").trim();
  const configured = () => url() && !/PASTE_/.test(url());

  /* ---------- non-fatal status banner ---------- */
  let bannerEl = null;
  function banner(msg, kind) {
    if (!bannerEl) {
      bannerEl = document.createElement("div");
      bannerEl.id = "store-banner";
      bannerEl.setAttribute("role", "status");
      document.body.appendChild(bannerEl);
    }
    if (!msg) { bannerEl.hidden = true; return; }
    bannerEl.hidden = false;
    bannerEl.className = "store-banner " + (kind || "info");
    bannerEl.textContent = msg;
  }
  function loading(on, what) { if (on) banner((what || "Contacting the project store") + "…", "info"); else banner(""); }

  /* ---------- cache mirror (last good list) ---------- */
  function readCache() {
    try { return JSON.parse(localStorage.getItem(CACHE_KEY) || "null"); } catch (e) { return null; }
  }
  function writeCache(projects) {
    try { localStorage.setItem(CACHE_KEY, JSON.stringify(projects)); } catch (e) {}
  }

  /* ---------- slim portfolio cache (stale-while-revalidate) ----------
     Small enough to paint instantly. Read on load for the first paint,
     replaced after every successful slim fetch, cleared on sign-out. */
  function readPortfolioCache() {
    try {
      const v = JSON.parse(localStorage.getItem(PORTFOLIO_CACHE_KEY) || "null");
      return Array.isArray(v) ? v : null;
    } catch (e) { return null; }
  }
  function writePortfolioCache(projects) {
    try { localStorage.setItem(PORTFOLIO_CACHE_KEY, JSON.stringify(projects || [])); } catch (e) {}
  }
  function clearPortfolioCache() {
    try { localStorage.removeItem(PORTFOLIO_CACHE_KEY); } catch (e) {}
  }

  /* ---------- in-memory hydration from a flat project list ---------- */
  /* Interpret the archived flag robustly. The backend JSON has been seen with
     non-boolean shapes — notably the STRING "false", which is truthy in JS and
     would silently route an active project into the archive (and then vanish
     entirely once listArchived() overwrites LIN_ARCHIVED with the real archive
     list). Only genuine archived markers count; everything else stays visible. */
  function isArchived(p) {
    const a = p && p.archived;
    if (a === true || a === 1) return true;
    if (typeof a === "string") return /^(true|1|yes|archived)$/i.test(a.trim());
    return false;
  }
  function hydrate(projects) {
    LIN_PROJECTS.length = 0;
    LIN_ARCHIVED.length = 0;
    (projects || []).forEach((p) => (isArchived(p) ? LIN_ARCHIVED : LIN_PROJECTS).push(p));
  }

  /* ---------- CORS-safe fetch helpers (simple requests only) ---------- */
  async function apiGet(qs) {
    const r = await fetch(url() + qs);                       // no custom headers → no preflight
    if (!r.ok) throw new Error("HTTP " + r.status);
    const j = await r.json();
    if (!j || j.ok === false) throw new Error((j && j.error) || "backend error");
    return j;
  }
  async function apiPost(body) {
    const r = await fetch(url(), {
      method: "POST",
      headers: { "Content-Type": "text/plain;charset=UTF-8" }, // simple request → no preflight
      body: JSON.stringify(body)
    });
    if (!r.ok) throw new Error("HTTP " + r.status);
    const j = await r.json();
    if (!j || j.ok === false) throw new Error((j && j.error) || "backend error");
    return j;
  }

  let lastError = null;
  function errored() { return lastError; }

  /* ---------- load: hydrate the portfolio from the backend ---------- */
  async function load() {
    lastError = null;
    if (!configured()) {
      const cached = readCache();
      hydrate(cached || []);
      banner("Project data is not yet configured. Showing " +
        (cached ? "last cached" : "an empty") + " portfolio.", "warn");
      return LIN_PROJECTS.slice();
    }
    loading(true, "Loading projects");
    try {
      const j = await apiGet("?action=list");
      const projects = j.projects || [];
      hydrate(projects);
      writeCache(projects);
      banner("");
      // Diagnostic: what the API returned vs how it was split. A project that
      // appears in the API list but is absent from "Projects loaded" was routed
      // to the archive (inspect its archived flag) — never dropped silently.
      console.log("API ?action=list returned:", projects.length,
        projects.map((p) => p.id + (isArchived(p) ? " (archived)" : "")));
      console.log("Projects loaded:", LIN_PROJECTS.length, LIN_PROJECTS.map((p) => p.id));
      // A project can go "missing" from the portfolio because it was
      // accidentally archived. When the active list is empty — or there are
      // archived projects at all — surface a warning so they're discoverable.
      try {
        await listArchived();                 // ?action=listarchived → LIN_ARCHIVED
        const n = LIN_ARCHIVED.length;
        if (n > 0 || LIN_PROJECTS.length === 0) {
          console.log("[load] active:", LIN_PROJECTS.length, "· archived:", n,
            "·", LIN_ARCHIVED.map((p) => p.id).join(", "));
        }
        if (n > 0) {
          banner(n + (n === 1 ? " project is" : " projects are") +
            " archived — restore from the archive tab", "warn");
        }
      } catch (e2) { /* non-fatal — the archive check is advisory only */ }
      return LIN_PROJECTS.slice();
    } catch (e) {
      lastError = e;
      const cached = readCache();
      hydrate(cached || []);
      banner("Couldn't reach the project store" + (cached ? " — showing last cached projects. Retry." : ". Retry."), "warn");
      return LIN_PROJECTS.slice();
    } finally {
      loading(false);
    }
  }

  /* ---------- slim list (v10.28 ?action=listslim) ----------
     A lightweight portfolio list — id, name, sector, status, cpi/spi/docRisk,
     actualPctComplete, simModuleCount, docCount, slim:true — with no simulation
     arrays or event bodies. The radar, list, and status pills render from these
     fields; full project JSON is fetched lazily only when a project is opened.
     Falls back to the full ?action=list when the slim endpoint 404s (backend
     not yet on v10.28) — one console warning, no user-facing error. */
  async function listSlim() {
    if (!configured()) return readCache() || [];
    try {
      const j = await apiGet("?action=listslim");
      return j.projects || [];
    } catch (e) {
      if (/HTTP 404/.test(String(e && e.message))) {
        console.warn("[store] listslim unavailable (404) — falling back to full list");
        const j = await apiGet("?action=list");
        return j.projects || [];
      }
      throw e;
    }
  }

  /* Stale-while-revalidate loader. Fetches the slim list, hydrates the in-memory
     mirrors, and refreshes both the slim portfolio cache and the legacy cache.
     The archive check runs after (non-blocking to the caller's re-render). */
  async function loadSlim() {
    lastError = null;
    if (!configured()) {
      const cached = readPortfolioCache() || readCache();
      hydrate(cached || []);
      banner("Project data is not yet configured. Showing " +
        (cached ? "last cached" : "an empty") + " portfolio.", "warn");
      return LIN_PROJECTS.slice();
    }
    try {
      const projects = await listSlim();
      hydrate(projects);
      writePortfolioCache(projects);
      writeCache(projects);
      banner("");
      try {
        await listArchived();
        const n = LIN_ARCHIVED.length;
        if (n > 0) {
          banner(n + (n === 1 ? " project is" : " projects are") +
            " archived — restore from the archive tab", "warn");
        }
      } catch (e2) { /* non-fatal — archive check is advisory only */ }
      return LIN_PROJECTS.slice();
    } catch (e) {
      lastError = e;
      const cached = readPortfolioCache() || readCache();
      hydrate(cached || []);
      banner("Couldn't reach the project store" + (cached ? " — showing last cached projects. Retry." : ". Retry."), "warn");
      return LIN_PROJECTS.slice();
    }
  }

  /* ---------- the async seam (same names as Phase 1) ---------- */
  async function listProjects() { await load(); return LIN_PROJECTS.slice(); }

  async function getProject(id) {
    if (!configured()) return getCached(id);
    try {
      const j = await apiGet("?action=get&id=" + encodeURIComponent(id));
      return j.project || getCached(id);
    } catch (e) { lastError = e; return getCached(id); }
  }

  async function createProject({ id, name, sector }) {
    if (!configured()) throw new Error("Project store not configured (LIN_API_URL).");
    loading(true, "Creating project");
    try {
      // id is the user-assigned project number/code (v10.27); uniqueness is
      // validated client-side and re-enforced server-side.
      const j = await apiPost({ action: "create", id, name, sector });
      const p = j.project;
      LIN_PROJECTS.push(p);
      writeCache(LIN_PROJECTS.concat(LIN_ARCHIVED));
      writePortfolioCache(LIN_PROJECTS.slice());   // keep the slim cache in sync (active only)
      banner("");
      return p;
    } finally { loading(false); }
  }

  // Assign / revise a project's user-facing number (v10.27 setprojectnumber).
  // Uniqueness is enforced server-side; a clash comes back as {ok:false,error}
  // which apiPost surfaces as a thrown Error. On success the in-memory mirrors
  // and the cache are re-keyed to the new id.
  async function setProjectNumber(id, newId) {
    if (!configured()) throw new Error("Project store not configured (LIN_API_URL).");
    loading(true, "Updating project number");
    try {
      const j = await apiPost({ action: "setprojectnumber", id, newId });
      const updated = (j && j.project) || null;
      [LIN_PROJECTS, LIN_ARCHIVED].forEach((list) => {
        const i = list.findIndex((p) => p.id === id);
        if (i >= 0) {
          if (updated) list[i] = updated;
          else list[i].id = newId;
        }
      });
      writeCache(LIN_PROJECTS.concat(LIN_ARCHIVED));
      writePortfolioCache(LIN_PROJECTS.slice());   // keep the slim cache in sync (active only)
      banner("");
      return updated || { id: newId };
    } finally { loading(false); }
  }

  async function saveProject(project) {
    if (!configured()) throw new Error("Project store not configured (LIN_API_URL).");
    loading(true, "Saving");
    try {
      const j = await apiPost({ action: "save", project });
      const saved = j.project || project;
      // reconcile memory: replace wherever it lives, honour archived flag
      const fromActive = LIN_PROJECTS.findIndex((p) => p.id === saved.id);
      if (fromActive >= 0) LIN_PROJECTS.splice(fromActive, 1);
      const fromArch = LIN_ARCHIVED.findIndex((p) => p.id === saved.id);
      if (fromArch >= 0) LIN_ARCHIVED.splice(fromArch, 1);
      (isArchived(saved) ? LIN_ARCHIVED : LIN_PROJECTS).push(saved);
      writeCache(LIN_PROJECTS.concat(LIN_ARCHIVED));
      writePortfolioCache(LIN_PROJECTS.slice());   // keep the slim cache in sync (active only)
      banner("");
      return saved;
    } finally { loading(false); }
  }

  // Archive uses the backend endpoint (it moves the Drive folder to 00_Archive),
  // then we drop it from the in-memory active mirror + cache.
  async function archiveProject(id) {
    if (!configured()) throw new Error("Project store not configured (LIN_API_URL).");
    loading(true, "Archiving");
    try {
      await apiPost({ action: "archive", id });
      const i = LIN_PROJECTS.findIndex((p) => p.id === id);
      if (i >= 0) LIN_PROJECTS.splice(i, 1);
      writeCache(LIN_PROJECTS.concat(LIN_ARCHIVED));
      writePortfolioCache(LIN_PROJECTS.slice());   // keep the slim cache in sync (active only)
      banner("");
      return { archived: id };
    } finally { loading(false); }
  }

  // Restore brings an archived project back to the active portfolio.
  async function restoreProject(id) {
    if (!configured()) throw new Error("Project store not configured (LIN_API_URL).");
    loading(true, "Restoring");
    try {
      const j = await apiPost({ action: "restore", id });
      const p = (j && j.project) || null;
      const ai = LIN_ARCHIVED.findIndex((x) => x.id === id);
      if (ai >= 0) LIN_ARCHIVED.splice(ai, 1);
      if (p && !LIN_PROJECTS.some((x) => x.id === p.id)) LIN_PROJECTS.push(p);
      writeCache(LIN_PROJECTS.concat(LIN_ARCHIVED));
      writePortfolioCache(LIN_PROJECTS.slice());   // keep the slim cache in sync (active only)
      banner("");
      return { restored: id };
    } finally { loading(false); }
  }

  // Fetch the archived list from the backend into the LIN_ARCHIVED mirror.
  async function listArchived() {
    if (!configured()) return LIN_ARCHIVED.slice();
    try {
      const j = await apiGet("?action=listarchived");
      LIN_ARCHIVED.length = 0;
      (j.projects || []).forEach((p) => LIN_ARCHIVED.push(p));
      return LIN_ARCHIVED.slice();
    } catch (e) { lastError = e; return LIN_ARCHIVED.slice(); }
  }

  /* ---------- Groq-backed endpoints (key lives in Apps Script, never here) ----------
     chat: explanatory assistant answer; analyze: document risk summary +
     optional spec-comparison verdict. Both return the backend payload; callers
     fall back gracefully on error. */
  async function chat(question, id, opts) {
    const body = { action: "chat", question };
    if (id) body.id = id;
    // Optional generation controls (e.g. the executive brief asks for more
    // tokens to fit its 4-section format). Backend honours max_tokens.
    if (opts && opts.max_tokens) body.max_tokens = opts.max_tokens;
    const j = await apiPost(body);
    return j.answer;
  }
  async function analyze({ text, docType, spec, id }) {
    const body = { action: "analyze", text };
    if (docType) body.docType = docType;
    if (spec) body.spec = spec;
    if (id) body.id = id;
    const j = await apiPost(body);
    return j.analysis;
  }

  /* ---------- Technical Auditor: corpus + audit endpoints (Gemini-backed) ----------
     listcorpus / listauditresults are GETs; ingestcorpus / audit are POSTs.
     File payloads are base64-encoded by the caller (FileReader) so the wire
     stays a plain JSON string and the request remains a CORS-safe simple POST. */
  async function listCorpus(id) {
    if (!configured()) return [];
    try {
      const j = await apiGet("?action=listcorpus&id=" + encodeURIComponent(id));
      return j.corpus || j.files || [];
    } catch (e) { lastError = e; throw e; }
  }
  async function listAuditResults(id) {
    if (!configured()) return [];
    try {
      const j = await apiGet("?action=listauditresults&id=" + encodeURIComponent(id));
      return j.results || j.files || [];
    } catch (e) { lastError = e; throw e; }
  }
  async function ingestCorpus({ id, name, docType, mimeType, dataBase64, masterFormatSections }) {
    if (!configured()) throw new Error("Project store not configured (LIN_API_URL).");
    const body = { action: "ingestcorpus", id, name, docType, mimeType, dataBase64 };
    // MasterFormat sections detected client-side (PDF.js). The backend can
    // persist these into the corpus metadata / requirements_db.json — see
    // BACKEND_CHANGES_NEEDED.md. Harmless if the current backend ignores them.
    if (masterFormatSections && masterFormatSections.length) body.masterFormatSections = masterFormatSections;
    const j = await apiPost(body);
    return j.file || j.corpus || j;
  }
  async function runAudit({ id, reviewType, submissionName, submissionMime, submissionBase64, corpusIds }) {
    if (!configured()) throw new Error("Project store not configured (LIN_API_URL).");
    const j = await apiPost({
      action: "audit", id, reviewType, submissionName, submissionMime, submissionBase64, corpusIds
    });
    return j;
  }
  // Save a completed audit result to Drive (_audits/ folder in the project).
  // Non-fatal: a failure here must never block the UI showing the result.
  async function saveAuditResult(id, auditData) {
    if (!configured()) return null;
    try {
      const j = await apiPost({ action: "saveauditresult", id, auditData });
      return j;
    } catch (e) { lastError = e; return null; }
  }

  /* ---------- Piece C: document-driven signal extraction (Gemini-backed) ----------
     extractsignals reads figures (BAC/EV/AC/PV/% complete/doc-risk) from one
     uploaded document and returns the merged signalInputs (+ computed cpi/spi),
     a `missing` list of still-needed fields/documents, and readyToRun.
     overwritesignal applies a human correction to one field (with a reason,
     logged server-side) and returns the recomputed signalInputs. Both are
     CORS-safe simple POSTs (text/plain) to LIN_API_URL, same as every call. */
  async function extractSignals({ id, docType, dataBase64, text, mimeType, fileName }) {
    if (!configured()) throw new Error("Project store not configured (LIN_API_URL).");
    // The document IS the input. PDFs are parsed to plain text client-side
    // (PDF.js, more reliable than Apps Script byte parsing) and sent as `text`;
    // images / doc / docx are sent as `dataBase64`. Periods + figures are still
    // extracted by the backend from the document content — no dates are sent.
    const body = { action: "extractsignals", id, docType, mimeType, fileName };
    if (text != null) body.text = text; else body.dataBase64 = dataBase64;
    const j = await apiPost(body);
    return j;
  }
  // identifyOnly classifies one uploaded document WITHOUT extracting signals —
  // returns { docType, confidence, suggestedPeriod } so the drag-and-drop ingest
  // can auto-confirm high-confidence matches and let the PM override the rest.
  async function identifyDocument({ id, dataBase64, text, mimeType, fileName }) {
    if (!configured()) throw new Error("Project store not configured (LIN_API_URL).");
    const body = { action: "identifyOnly", id, mimeType, fileName };
    if (text != null) body.text = text; else body.dataBase64 = dataBase64;
    const j = await apiPost(body);
    return j;
  }
  async function overwriteSignal({ id, field, value, reason }) {
    if (!configured()) throw new Error("Project store not configured (LIN_API_URL).");
    const j = await apiPost({ action: "overwritesignal", id, field, value, reason });
    return j;
  }
  // Clear a project's signals server-side (back to "awaiting ingest").
  async function resetSignals(id) {
    if (!configured()) throw new Error("Project store not configured (LIN_API_URL).");
    const j = await apiPost({ action: "resetsignals", id });
    return j;
  }

  /* ---------- synchronous accessors for render (read the mirror) ---------- */
  function cachedActive() { return LIN_PROJECTS.slice(); }
  function cachedArchived() { return LIN_ARCHIVED.slice(); }
  function getCached(id) {
    return LIN_PROJECTS.find((p) => p.id === id) || LIN_ARCHIVED.find((p) => p.id === id) || null;
  }

  function hasSignals(p) {
    return !!(p && p.signals && p.signals.evm && p.signals.cusum && p.signals.mc && p.signals.doc);
  }

  window.LinStore = {
    load, listProjects, getProject, createProject, saveProject,
    setProjectNumber,
    archiveProject, restoreProject, listArchived, chat, analyze,
    listCorpus, listAuditResults, ingestCorpus, runAudit, saveAuditResult,
    extractSignals, identifyDocument, overwriteSignal, resetSignals,
    // slim portfolio list + stale-while-revalidate cache (v10.28)
    listSlim, loadSlim,
    readPortfolioCache, writePortfolioCache, clearPortfolioCache,
    hydratePortfolio: hydrate,
    // generic POST passthrough (used by the Portfolio Health portfolioanalyze call)
    post: apiPost,
    // sync mirror accessors used by render code
    cachedActive, cachedArchived, getCached, listActive: cachedActive,
    hasSignals, errored, configured, banner, loading
  };
  window.hasSignals = hasSignals;
})();
