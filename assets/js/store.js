/* ============================================================
   lin-project-radar — store.js  (Phase 1)
   ------------------------------------------------------------
   The SINGLE data-access seam. All project reads/writes/creates
   go through here. Phase 1 is backed by localStorage ONLY — no
   network calls. Phase 2 will swap this implementation for an
   Apps Script / Google Drive backend WITHOUT touching the UI:
   the UI only ever calls listProjects/getProject/createProject/
   saveProject/archive/restore below.

   It owns the live in-memory arrays window.LIN_PROJECTS and
   window.LIN_ARCHIVED so existing render modules keep reading
   them, and persists every mutation to localStorage.
   ============================================================ */

(function () {
  "use strict";

  const KEY_PROJECTS = "lpr-projects-v1";   // active + archived, full records
  const KEY_ARCHIVED = "lpr-archived-v1";   // array of archived ids

  /* ---------- low-level persistence ---------- */
  function readAll() {
    try { return JSON.parse(localStorage.getItem(KEY_PROJECTS) || "null"); }
    catch (e) { return null; }
  }
  function writeAll(records) {
    try { localStorage.setItem(KEY_PROJECTS, JSON.stringify(records)); } catch (e) {}
  }
  function readArchivedIds() {
    try { return JSON.parse(localStorage.getItem(KEY_ARCHIVED) || "[]"); }
    catch (e) { return []; }
  }
  function writeArchivedIds(ids) {
    try { localStorage.setItem(KEY_ARCHIVED, JSON.stringify(ids)); } catch (e) {}
  }

  /* Persist the current in-memory state (active + archived) as one record set. */
  function persist() {
    const records = LIN_PROJECTS.concat(LIN_ARCHIVED);
    writeAll(records);
    writeArchivedIds(LIN_ARCHIVED.map((p) => p.id));
  }

  /* ---------- a project has signals only after ingest populates them ---------- */
  function hasSignals(p) {
    return !!(p && p.signals && p.signals.evm && p.signals.cusum && p.signals.mc && p.signals.doc);
  }

  /* ---------- init: hydrate from localStorage, else seed empty shells ---------- */
  function init() {
    const stored = readAll();
    if (stored && Array.isArray(stored) && stored.length) {
      const archivedIds = new Set(readArchivedIds());
      LIN_PROJECTS.length = 0;
      LIN_ARCHIVED.length = 0;
      stored.forEach((p) => (archivedIds.has(p.id) ? LIN_ARCHIVED : LIN_PROJECTS).push(p));
    } else {
      // First run: seed clearly-empty example shells (no fabricated signals).
      LIN_PROJECTS.length = 0;
      LIN_ARCHIVED.length = 0;
      LIN_SEED_PROJECTS.forEach((s) => LIN_PROJECTS.push(JSON.parse(JSON.stringify(s))));
      persist();
    }
  }

  /* ---------- id assignment: numeric, zero-padded, next free ---------- */
  function nextId() {
    let max = 0;
    LIN_PROJECTS.concat(LIN_ARCHIVED).forEach((p) => {
      const n = parseInt(p.id, 10);
      if (Number.isFinite(n) && n > max) max = n;
    });
    return String(max + 1).padStart(2, "0");
  }

  /* ---------- public data-access API ---------- */

  function listProjects() { return LIN_PROJECTS.slice(); }
  function listArchived() { return LIN_ARCHIVED.slice(); }
  function getProject(id) {
    return LIN_PROJECTS.find((p) => p.id === id) ||
           LIN_ARCHIVED.find((p) => p.id === id) || null;
  }

  // createProject({name, sector}) → empty project (no signals), persisted.
  // Phase 2 will additionally create a Drive folder here; the UI contract
  // (returns the new project) does not change.
  function createProject({ name, sector }) {
    const project = {
      id: nextId(),
      name: String(name || "").trim(),
      sector: sector === "hybrid" ? "hybrid" : sector,  // design|construction|hybrid
      reportingPeriod: new Date().toISOString().slice(0, 7),
      signals: {},          // EMPTY until ingest populates
      fairnessSensitive: false,
      createdAt: new Date().toISOString()
    };
    LIN_PROJECTS.push(project);
    persist();
    return project;
  }

  function saveProject(project) {
    const i = LIN_PROJECTS.findIndex((p) => p.id === project.id);
    if (i >= 0) LIN_PROJECTS[i] = project;
    else if (!LIN_ARCHIVED.some((p) => p.id === project.id)) LIN_PROJECTS.push(project);
    persist();
    return project;
  }

  function archiveProject(id) {
    const i = LIN_PROJECTS.findIndex((p) => p.id === id);
    if (i < 0) return null;
    const p = LIN_PROJECTS.splice(i, 1)[0];
    LIN_ARCHIVED.push(p);
    persist();
    return p;
  }

  function restoreProject(id) {
    const i = LIN_ARCHIVED.findIndex((p) => p.id === id);
    if (i < 0) return null;
    const p = LIN_ARCHIVED.splice(i, 1)[0];
    LIN_PROJECTS.push(p);
    persist();
    return p;
  }

  window.LinStore = {
    init, listProjects, listArchived, getProject,
    createProject, saveProject, archiveProject, restoreProject,
    nextId, hasSignals
  };
  // convenience global guard used by render modules
  window.hasSignals = hasSignals;

  // Hydrate immediately (synchronous, before app.js init runs).
  init();
})();
