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

  /* ---------- in-memory hydration from a flat project list ---------- */
  function hydrate(projects) {
    LIN_PROJECTS.length = 0;
    LIN_ARCHIVED.length = 0;
    (projects || []).forEach((p) => (p.archived ? LIN_ARCHIVED : LIN_PROJECTS).push(p));
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
      banner("Project store not configured (LIN_API_URL). Showing " +
        (cached ? "last cached" : "an empty") + " portfolio — set the URL in config.js.", "warn");
      return LIN_PROJECTS.slice();
    }
    loading(true, "Loading projects");
    try {
      const j = await apiGet("?action=list");
      const projects = j.projects || [];
      hydrate(projects);
      writeCache(projects);
      banner("");
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

  /* ---------- the async seam (same names as Phase 1) ---------- */
  async function listProjects() { await load(); return LIN_PROJECTS.slice(); }

  async function getProject(id) {
    if (!configured()) return getCached(id);
    try {
      const j = await apiGet("?action=get&id=" + encodeURIComponent(id));
      return j.project || getCached(id);
    } catch (e) { lastError = e; return getCached(id); }
  }

  async function createProject({ name, sector }) {
    if (!configured()) throw new Error("Project store not configured (LIN_API_URL).");
    loading(true, "Creating project");
    try {
      const j = await apiPost({ action: "create", name, sector });
      const p = j.project;
      // backend owns id numbering; reflect into memory + cache
      LIN_PROJECTS.push(p);
      writeCache(LIN_PROJECTS.concat(LIN_ARCHIVED));
      banner("");
      return p;
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
      (saved.archived ? LIN_ARCHIVED : LIN_PROJECTS).push(saved);
      writeCache(LIN_PROJECTS.concat(LIN_ARCHIVED));
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
      banner("");
      return { archived: id };
    } finally { loading(false); }
  }

  /* ---------- Groq-backed endpoints (key lives in Apps Script, never here) ----------
     chat: explanatory assistant answer; analyze: document risk summary +
     optional spec-comparison verdict. Both return the backend payload; callers
     fall back gracefully on error. */
  async function chat(question, id) {
    const body = { action: "chat", question };
    if (id) body.id = id;
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
    archiveProject, chat, analyze,
    // sync mirror accessors used by render code
    cachedActive, cachedArchived, getCached, listActive: cachedActive, listArchived: cachedArchived,
    hasSignals, errored, configured, banner, loading
  };
  window.hasSignals = hasSignals;
})();
