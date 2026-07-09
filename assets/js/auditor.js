/* ============================================================
   lin-project-radar — auditor.js  (Technical Auditor page, v2)
   ------------------------------------------------------------
   ONE project picker at the top scopes the whole page.
   Section A — User Requirements: a single upload card
     (doctype dropdown + file + Upload). Corpus list below,
     grouped by doctype.
   Section B — Technical Audit: review type + submission +
     Run Audit. Corpus is auto-attached in full (no checkboxes).
     Results table + DOWNLOAD REMARK button appear only after a
     successful audit.
   Audit History at the bottom shows past CSV filenames + dates
     (Drive-stored; no in-app re-download from the list).
   All file payloads are base64 via FileReader; all network
   goes through LinStore (LIN_API_URL).
   ============================================================ */
(function () {
  "use strict";

  const esc = (s) => String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  const DOC_TYPES = [
    { key: "specification",    label: "Specification" },
    { key: "code_of_practice", label: "Code of Practice" },
    { key: "user_requirement", label: "User Requirement" }
  ];
  const DOC_TYPE_LABEL = {
    specification: "Specification",
    code_of_practice: "Code of Practice",
    user_requirement: "User Requirement"
  };

  const REVIEW_TYPES = [
    { key: "material_submittal", label: "Material Submittal" },
    { key: "drawing",            label: "Drawing" }
  ];
  const REVIEW_TYPE_LABEL = { material_submittal: "Material Submittal", drawing: "Drawing" };

  const ACCEPT = ".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg";

  /* ---------- MasterFormat section detection (Item 15) ----------
     Parse "SECTION 03 30 00 - CONCRETE" style headings out of corpus text. */
  function detectMasterFormatSections(text) {
    if (!text) return [];
    const pattern = /SECTION\s+\d{2}\s+\d{2}\s+\d{2}[\s\w\-]*/gi;
    const raw = text.match(pattern) || [];
    // normalize whitespace + dedupe, keep the leading "SECTION NN NN NN [title]"
    const seen = {}, out = [];
    raw.forEach((m) => {
      const s = m.replace(/\s+/g, " ").trim().slice(0, 60);
      const key = (s.match(/SECTION\s+\d{2}\s+\d{2}\s+\d{2}/i) || [s])[0].toUpperCase();
      if (!seen[key]) { seen[key] = 1; out.push(s); }
    });
    return out;
  }
  const isPdf = (file) => file.type === "application/pdf" || /\.pdf$/i.test(file.name || "");
  async function extractPdfText(file) {
    if (typeof pdfjsLib === "undefined") return "";
    try {
      pdfjsLib.GlobalWorkerOptions.workerSrc =
        "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
      const buf = await file.arrayBuffer();
      const pdf = await pdfjsLib.getDocument({ data: buf }).promise;
      let text = "";
      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const content = await page.getTextContent();
        text += content.items.map((it) => it.str).join(" ") + "\n";
      }
      return text.trim();
    } catch (e) { return ""; }
  }

  /* ---------- page state ---------- */
  let state = {
    projectId: "",

    corpus: [],
    corpusLoading: false,
    corpusError: "",

    pastAudits: [],
    pastLoading: false,
    pastError: "",

    /* Section A (upload card) */
    pickDocType: "specification",
    pickFile: null,           // File object
    uploadBusy: false,
    uploadMsg: "",            // "" | "✓ ..." | "Upload failed: ..."

    /* MasterFormat sections detected client-side, keyed by file name (Item 15)
       — used so tags show immediately even before the backend persists them. */
    sectionsByName: {},

    /* Section B */
    reviewType: "material_submittal",
    submission: null,         // {name, mime, size, base64}
    auditing: false,
    auditError: "",
    auditResult: null,        // {items[], summary{}, csvContent, csvName}
    drafts: {},               // Item 17: contractor-response drafts keyed by row index
    pastAuditCache: {},       // keyed by audit_id → full audit payload (survives page reload via localStorage)
    expandedAudit: null,      // audit_id of the row expanded in Past Audits

    /* Auto-expand AUDIT RESULTS the first time a fresh result arrives */
    resultsOpen: false
  };

  /* ---------- helpers ---------- */
  function readFileAsBase64(file) {
    return new Promise((resolve, reject) => {
      const r = new FileReader();
      r.onerror = () => reject(new Error("Couldn't read file"));
      r.onload = () => {
        const result = String(r.result || "");
        const comma = result.indexOf(",");
        resolve(comma >= 0 ? result.slice(comma + 1) : result);
      };
      r.readAsDataURL(file);
    });
  }
  function fmtSize(bytes) {
    if (!Number.isFinite(bytes)) return "";
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / 1024 / 1024).toFixed(2) + " MB";
  }
  function fmtDate(s) {
    if (!s) return "";
    try { return window.LinTZ ? LinTZ.format(s) : String(s); } catch (e) { return String(s); }
  }
  function projectOptions() {
    const list = (LinStore.cachedActive && LinStore.cachedActive()) || [];
    return `<option value="">Select a project…</option>` +
      list.map((p) => `<option value="${esc(p.id)}"${p.id === state.projectId ? " selected" : ""}>${esc(p.id)} — ${esc(p.name)}</option>`).join("");
  }
  function statusKey(s) {
    const v = String(s || "").toLowerCase().trim();
    if (v === "approved")           return "approved";
    if (v === "approved as noted")  return "approved-as-noted";
    if (v === "rejected")           return "rejected";
    if (v === "remark")             return "remark";
    return "other";
  }
  function fileIdOf(f) { return f.fileId || f.id || f.driveId || ""; }
  function reviewTypeFromName(name) {
    const n = String(name || "").toLowerCase();
    if (n.includes("material")) return "Material Submittal";
    if (n.includes("drawing"))  return "Drawing";
    return "—";
  }

  /* ---------- loaders ---------- */
  async function loadCorpus() {
    if (!state.projectId) { state.corpus = []; return; }
    state.corpusLoading = true; state.corpusError = "";
    try {
      const list = await LinStore.listCorpus(state.projectId);
      state.corpus = Array.isArray(list) ? list : [];
    } catch (e) {
      state.corpus = [];
      state.corpusError = "Couldn't load corpus — store unreachable.";
    } finally {
      state.corpusLoading = false;
    }
  }
  async function loadPastAudits() {
    if (!state.projectId) { state.pastAudits = []; return; }
    state.pastLoading = true; state.pastError = "";
    try {
      const list = await LinStore.listAuditResults(state.projectId);
      const arr = Array.isArray(list) ? list.slice() : [];
      arr.sort((a, b) => {
        const da = new Date(a.createdAt || a.date || a.modifiedAt || 0).getTime();
        const db = new Date(b.createdAt || b.date || b.modifiedAt || 0).getTime();
        return db - da;
      });
      state.pastAudits = arr;
    } catch (e) {
      state.pastAudits = [];
      state.pastError = "Couldn't load audit history.";
    } finally {
      state.pastLoading = false;
    }
  }

  /* ---------- local audit cache (localStorage) ---------- */
  const AUDIT_CACHE_KEY = "lpr-audit-cache-v1";
  function readAuditCache() {
    try { return JSON.parse(localStorage.getItem(AUDIT_CACHE_KEY) || "{}"); } catch (e) { return {}; }
  }
  function writeAuditCache(cache) {
    try { localStorage.setItem(AUDIT_CACHE_KEY, JSON.stringify(cache)); } catch (e) {}
  }
  function cacheAuditResult(auditId, payload) {
    const cache = readAuditCache();
    cache[auditId] = payload;
    writeAuditCache(cache);
    state.pastAuditCache[auditId] = payload;
  }
  function loadAuditCache() {
    const cache = readAuditCache();
    Object.assign(state.pastAuditCache, cache);
  }

  /* ---------- XLSX export ---------- */
  function exportAuditXLSX(auditData, projectId) {
    const XL = window.XLSX;
    if (!XL) { alert("SheetJS not loaded — cannot export XLSX."); return; }
    const r = auditData;
    const items = Array.isArray(r.items) ? r.items : (Array.isArray(r.results) ? r.results : []);
    const rows = [
      ["#", "Item Submitted", "Spec Section", "Remark", "Citation", "Status"]
    ];
    items.forEach((it, i) => {
      rows.push([
        i + 1,
        it.item || it.itemSubmitted || it.submittedItem || "",
        it.specSection || it.spec_section || "",
        it.remark || it.comment || it.note || "",
        it.citation || it.reference || "",
        it.status || ""
      ]);
    });
    rows.push([]);
    const sum = r.summary || {};
    const project = LinStore.getCached ? LinStore.getCached(projectId) : null;
    const projectName = project ? project.name : (projectId || "");
    rows.push(["Project:", projectName, "Date:", r.run_at ? r.run_at.substring(0, 10) : new Date().toISOString().substring(0, 10),
               "Overall:", r.overall_verdict || ""]);
    const ws = XL.utils.aoa_to_sheet(rows);
    ws["!cols"] = [{ wch: 4 }, { wch: 36 }, { wch: 20 }, { wch: 42 }, { wch: 26 }, { wch: 16 }];
    const wb = XL.utils.book_new();
    XL.utils.book_append_sheet(wb, ws, "Audit Results");
    const filename = "audit_" + (projectId || "proj") + "_" + new Date().toISOString().substring(0, 10) + ".xlsx";
    XL.writeFile(wb, filename);
  }

  /* ---------- rendering ---------- */
  function corpusByType(type) {
    return state.corpus.filter((f) => (f.docType || "").toLowerCase() === type);
  }

  function topPickerHtml() {
    return `<section class="panel aud-topbar">
      <label class="rationale-label" for="aud-project">Project
        <select id="aud-project" class="ig-input">${projectOptions()}</select></label>
      <p class="kn-sub">Every section below is scoped to this project. Selecting a project loads its reference corpus and audit history.</p>
    </section>`;
  }

  function corpusListHtml() {
    if (!state.projectId) return `<p class="kn-sub">Select a project to view its corpus.</p>`;
    if (state.corpusLoading) return `<p class="kn-sub">Loading corpus…</p>`;
    if (state.corpusError) return `<p class="aud-msg warn">${esc(state.corpusError)}</p>`;
    return DOC_TYPES.map((dt) => {
      const items = corpusByType(dt.key);
      const rows = items.length
        ? `<ul class="aud-corpus-list">${items.map((f) => {
            const name = f.name || f.filename || "(unnamed)";
            const when = f.createdAt || f.date || f.modifiedAt || "";
            // sections from the backend metadata, or the local detection cache
            const sections = (Array.isArray(f.masterFormatSections) && f.masterFormatSections)
              || (Array.isArray(f.sections) && f.sections)
              || state.sectionsByName[name] || [];
            const tags = sections.length
              ? `<div class="aud-mf-tags"><span class="aud-mf-count kn-sub">${sections.length} MasterFormat section${sections.length > 1 ? "s" : ""} detected</span>${
                  sections.slice(0, 8).map((s) => `<span class="aud-mf-tag">${esc(s)}</span>`).join("")
                }</div>`
              : "";
            return `<li class="aud-corpus-row">
              <span class="aud-corpus-name">${esc(name)}</span>
              <span class="aud-corpus-date kn-sub">${esc(fmtDate(when))}</span>
              ${tags}
            </li>`;
          }).join("")}</ul>`
        : `<p class="kn-sub aud-corpus-empty">None uploaded yet.</p>`;
      return `<div class="aud-corpus-group">
        <p class="eyebrow">${esc(dt.label)}</p>
        ${rows}
      </div>`;
    }).join("");
  }

  /* CORPUS DOCUMENTS body: upload card + corpus list. Wrapped in a single
     collapsible by renderAuditorPage; the section <h2>/intro paragraph live
     inside the body so the collapse header stays terse. */
  function corpusBodyHtml() {
    const canUpload = !!(state.projectId && state.pickFile && !state.uploadBusy);
    const msg = state.uploadMsg;
    return `<p class="kn-sub">Reference documents this project is audited against. Stored in the project folder and reused automatically in every future audit.</p>

      <div class="aud-card">
        <div class="aud-upload-row">
          <label class="rationale-label">Document type
            <select id="aud-a-doctype" class="ig-input" ${state.projectId ? "" : "disabled"}>
              ${DOC_TYPES.map((dt) => `<option value="${dt.key}"${dt.key === state.pickDocType ? " selected" : ""}>${esc(dt.label)}</option>`).join("")}
            </select></label>
          <label class="aud-filebtn ${state.projectId ? "" : "is-disabled"}">
            <input type="file" id="aud-a-file" accept="${ACCEPT}" ${state.projectId ? "" : "disabled"} />
            <span class="aud-filebtn-label">${state.pickFile ? esc(state.pickFile.name) : "Choose file (PDF or image)…"}</span>
            ${state.pickFile ? `<span class="kn-sub">· ${esc(fmtSize(state.pickFile.size))}</span>` : ""}
          </label>
          <button class="btn primary" id="aud-a-upload" ${canUpload ? "" : "disabled"}>${state.uploadBusy ? "Uploading…" : "Upload"}</button>
        </div>
        ${msg ? `<p class="aud-msg ${msg.startsWith("✓") ? "ok" : "warn"}" aria-live="polite">${esc(msg)}</p>` : ""}
      </div>

      <div class="aud-corpus-block">
        <p class="eyebrow" style="margin-top:18px">Uploaded references</p>
        ${corpusListHtml()}
      </div>`;
  }

  function corpusCountBadge() {
    if (!state.projectId) return "no project selected";
    if (state.corpusLoading) return "loading…";
    const n = state.corpus.length;
    return n + " reference file" + (n === 1 ? "" : "s");
  }

  /* Render a single item row, indexed by its absolute position in items[] so the
     draft-row buttons and state.drafts mapping keep working unchanged. */
  function itemRowHtml(it, i) {
    const sk = statusKey(it.status);
    const statusLabel = it.status || "—";
    const needsDraft = sk === "rejected" || sk === "remark";
    const draft = state.drafts[i];
    const draftBtn = needsDraft
      ? `<button class="aud-draft-btn" data-row="${i}">${draft && draft.loading ? "Drafting…" : "Draft contractor response"}</button>`
      : "";
    const draftRow = (needsDraft && draft && (draft.text || draft.loading || draft.error))
      ? `<tr class="aud-draft-row"><td colspan="5">
          <div class="aud-draft">
            <p class="aud-draft-label kn-sub">Draft response request (for contractor fairness gate) — requires human review before sending</p>
            ${draft.loading ? `<p class="kn-sub">Drafting with AI…</p>`
              : draft.error ? `<p class="aud-msg warn">${esc(draft.error)}</p>`
              : `<textarea class="aud-draft-text" rows="5" readonly>${esc(draft.text)}</textarea>`}
          </div></td></tr>`
      : "";
    return `<tr>
      <td class="aud-num">${i + 1}</td>
      <td>${esc(it.item || it.itemSubmitted || it.submittedItem || "—")}</td>
      <td>${esc(it.remark || it.comment || it.note || "—")}</td>
      <td class="aud-cite">${esc(it.citation || it.reference || "—")}</td>
      <td><span class="aud-status aud-status-${sk}">${esc(statusLabel)}</span>${draftBtn ? `<div class="aud-draft-actions">${draftBtn}</div>` : ""}</td>
    </tr>${draftRow}`;
  }

  /* Group items by verdict, build one nested collapsible per non-empty bucket. */
  function resultsByVerdictHtml(items) {
    if (!items.length) return `<p class="kn-sub">The audit returned no line items.</p>`;
    const buckets = [
      { key: "approved",          label: "Approved" },
      { key: "approved-as-noted", label: "Approved as Noted" },
      { key: "rejected",          label: "Rejected" },
      { key: "remark",            label: "Remark" }
    ];
    const cs = window.collapsibleSection || function (id, title, body) { return body; };
    return buckets.map((b, bi) => {
      const rows = items.map((it, i) => statusKey(it.status) === b.key ? itemRowHtml(it, i) : "").filter(Boolean).join("");
      const count = rows ? items.filter((it) => statusKey(it.status) === b.key).length : 0;
      const body = count
        ? `<div class="aud-table-wrap"><table class="aud-table">
            <thead><tr><th>#</th><th>Item Submitted</th><th>Remark</th><th>Citation</th><th>Status</th></tr></thead>
            <tbody>${rows}</tbody></table></div>`
        : `<p class="kn-sub">No items in this bucket.</p>`;
      const badge = `<span class="aud-status aud-status-${b.key}">${count}</span>`;
      return cs("aud-bucket-" + b.key, b.label, body, false, badge);
    }).join("");
  }

  function resultsHtml() {
    if (state.auditError) return `<p class="aud-msg warn" aria-live="polite">${esc(state.auditError)}</p>`;
    if (state.auditing) return `<div class="aud-loading" aria-live="polite">
        <span class="aud-spinner" aria-hidden="true"></span>
        <span>Auditing… this may take 10–20 seconds.</span>
      </div>`;
    if (!state.auditResult) return "";
    const r = state.auditResult;
    const items = Array.isArray(r.items) ? r.items
                 : (Array.isArray(r.results) ? r.results : []);
    const sum = r.summary || {};
    const total = sum.total ?? items.length;
    const ap   = sum.approved        ?? items.filter((i) => statusKey(i.status) === "approved").length;
    const apN  = sum.approvedAsNoted ?? items.filter((i) => statusKey(i.status) === "approved-as-noted").length;
    const rj   = sum.rejected        ?? items.filter((i) => statusKey(i.status) === "rejected").length;
    const rm   = sum.remarks         ?? items.filter((i) => statusKey(i.status) === "remark").length;

    return `<div class="aud-result">
      <div class="aud-summary">
        <strong>${total}</strong> items reviewed —
        <span class="aud-status aud-status-approved">${ap} Approved</span>,
        <span class="aud-status aud-status-approved-as-noted">${apN} Approved as Noted</span>,
        <span class="aud-status aud-status-rejected">${rj} Rejected</span>,
        <span class="aud-status aud-status-remark">${rm} Remarks</span>
      </div>

      ${resultsByVerdictHtml(items)}

      <div class="aud-download-row">
        <button class="btn primary aud-download" id="aud-export-xlsx">Export XLSX</button>
        <p class="kn-sub aud-saved-note">Results saved to project folder and audit history.</p>
      </div>
    </div>`;
  }

  /* UPLOAD SUBMISSION body — review type + submission upload + run audit. The
     results block lives in its own collapsible (audit-results) so that one can
     auto-expand after a run without forcing this panel open as well. */
  function submissionBodyHtml() {
    const hasProject = !!state.projectId;
    const hasCorpus = state.corpus.length > 0;
    const canRun = !!(hasProject && hasCorpus && state.submission && !state.auditing);
    const emptyCorpusMsg = hasProject && !state.corpusLoading && !hasCorpus
      ? `<p class="aud-msg warn">No reference documents found for this project. Upload specifications, codes, or user requirements in CORPUS DOCUMENTS above before running an audit.</p>`
      : "";
    return `<p class="kn-sub">Upload a submission to audit it against all reference documents in this project's corpus. Results are saved to the project folder.</p>
      <p class="aud-illus" role="note">Audit findings are AI-assisted and require named human review and sign-off before any formal action is taken.</p>

      <div class="aud-step">
        <p class="eyebrow">Step 1 · Review type</p>
        <label class="rationale-label" for="aud-review-type">Review type
          <select id="aud-review-type" class="ig-input" ${hasProject ? "" : "disabled"}>
            ${REVIEW_TYPES.map((rt) => `<option value="${rt.key}"${rt.key === state.reviewType ? " selected" : ""}>${esc(rt.label)}</option>`).join("")}
          </select></label>
      </div>

      <div class="aud-step">
        <p class="eyebrow">Step 2 · Submission</p>
        <label class="aud-filebtn ${hasProject ? "" : "is-disabled"}">
          <input type="file" id="aud-submission" accept="${ACCEPT}" ${hasProject ? "" : "disabled"} />
          <span class="aud-filebtn-label">${state.submission ? esc(state.submission.name) : "Submission (PDF or image)…"}</span>
          ${state.submission ? `<span class="kn-sub">· ${esc(fmtSize(state.submission.size))}</span>` : ""}
        </label>
      </div>

      <div class="aud-step">
        <p class="eyebrow">Step 3 · Run audit</p>
        <div class="dc-actions">
          <button class="btn primary" id="aud-run" ${canRun ? "" : "disabled"}>${state.auditing ? "Running…" : "Run Audit"}</button>
        </div>
        ${emptyCorpusMsg}
      </div>`;
  }

  function resultsCountBadge() {
    if (state.auditing) return "running…";
    if (!state.auditResult) return "not run yet";
    const items = Array.isArray(state.auditResult.items) ? state.auditResult.items
                : (Array.isArray(state.auditResult.results) ? state.auditResult.results : []);
    return items.length + " item" + (items.length === 1 ? "" : "s");
  }

  function historyCountBadge() {
    if (!state.projectId) return "no project selected";
    if (state.pastLoading) return "loading…";
    const n = state.pastAudits.length;
    return n + " previous audit" + (n === 1 ? "" : "s");
  }

  function historyHtml() {
    if (!state.projectId) return `<p class="kn-sub">Select a project to view its audit history.</p>`;
    if (state.pastLoading) return `<p class="kn-sub">Loading audit history…</p>`;
    if (state.pastError) return `<p class="aud-msg warn">${esc(state.pastError)}</p>`;
    if (!state.pastAudits.length) return `<p class="kn-sub">No audit history yet for this project.</p>`;
    const rows = state.pastAudits.map((f) => {
      const auditId = f.audit_id || f.id || f.name || "";
      const name = f.name || f.filename || auditId || "(unnamed)";
      const when = f.run_at || f.createdAt || f.date || f.modifiedAt || "";
      const verdict = f.overall_verdict || "";
      const cached = state.pastAuditCache[auditId];
      const isExpanded = state.expandedAudit === auditId;
      const canExport = !!cached;
      const canView = !!cached;
      const expandedTable = (isExpanded && cached) ? (() => {
        const items = Array.isArray(cached.items) ? cached.items : (Array.isArray(cached.results) ? cached.results : []);
        if (!items.length) return `<tr class="aud-history-detail"><td colspan="5"><p class="kn-sub">No line items in this record.</p></td></tr>`;
        const itemRows = items.map((it, i) => {
          const sk = statusKey(it.status);
          return `<tr>
            <td class="aud-num">${i + 1}</td>
            <td>${esc(it.item || it.itemSubmitted || it.submittedItem || "—")}</td>
            <td>${esc(it.remark || it.comment || it.note || "—")}</td>
            <td class="aud-cite">${esc(it.citation || it.reference || "—")}</td>
            <td><span class="aud-status aud-status-${sk}">${esc(it.status || "—")}</span></td>
          </tr>`;
        }).join("");
        return `<tr class="aud-history-detail"><td colspan="5">
          <div class="aud-table-wrap" style="margin:8px 0">
            <table class="aud-table">
              <thead><tr><th>#</th><th>Item Submitted</th><th>Remark</th><th>Citation</th><th>Status</th></tr></thead>
              <tbody>${itemRows}</tbody>
            </table>
          </div></td></tr>`;
      })() : "";
      return `<tr>
        <td class="aud-past-date">${esc(fmtDate(when))}</td>
        <td>${esc(reviewTypeFromName(name))}</td>
        <td class="aud-past-name mod-mono">${esc(name)}</td>
        <td>${verdict ? `<span class="aud-status aud-status-${statusKey(verdict)}">${esc(verdict)}</span>` : ""}</td>
        <td class="aud-past-actions">
          ${canView ? `<button class="aud-history-view" data-audit-id="${esc(auditId)}">${isExpanded ? "Hide" : "View"}</button>` : ""}
          ${canExport ? `<button class="aud-history-xlsx" data-audit-id="${esc(auditId)}">Export XLSX</button>` : ""}
        </td>
      </tr>${expandedTable}`;
    }).join("");
    return `<div class="aud-table-wrap"><table class="aud-table">
        <thead><tr><th>Date</th><th>Review Type</th><th>Filename</th><th>Verdict</th><th></th></tr></thead>
        <tbody>${rows}</tbody>
      </table></div>`;
  }

  function renderAuditorPage() {
    const root = document.getElementById("auditor-root");
    if (!root) return;
    loadAuditCache(); // merge localStorage cache into state.pastAuditCache
    const cs = window.collapsibleSection || function (id, title, body) { return body; };
    const corpus = cs("aud-corpus", "CORPUS DOCUMENTS", corpusBodyHtml(), true, corpusCountBadge());
    const submission = cs("aud-submission-sec", "UPLOAD SUBMISSION", submissionBodyHtml(), false);
    /* Results — auto-expands the first time a fresh result lands (see run handler). */
    const results = cs("aud-results", "AUDIT RESULTS", resultsHtml() || "<p class=\"kn-sub\">No audit run yet.</p>",
                       !!state.resultsOpen, resultsCountBadge());
    const history = cs("aud-history", "AUDIT HISTORY", historyHtml(), false, historyCountBadge());
    root.innerHTML =
      topPickerHtml() +
      `<p class="upload-disclaimer">Academic use only — do not upload sensitive or real project documents.</p>` +
      `<div class="aud-stack">${corpus}${submission}${results}${history}</div>`;
    wire(root);
  }

  /* ---------- wiring ---------- */
  function wire(root) {
    const $ = (sel) => root.querySelector(sel);

    /* Top picker — scopes the whole page */
    const sel = $("#aud-project");
    if (sel) sel.addEventListener("change", (e) => {
      const id = e.target.value;
      if (id === state.projectId) return;
      state.projectId = id;
      /* reset per-project state */
      state.pickFile = null;
      state.uploadMsg = "";
      state.submission = null;
      state.auditResult = null;
      state.auditError = "";
      renderAuditorPage();
      Promise.all([loadCorpus(), loadPastAudits()]).then(renderAuditorPage);
    });

    /* Section A */
    const dt = $("#aud-a-doctype");
    if (dt) dt.addEventListener("change", (e) => { state.pickDocType = e.target.value; });

    const aFile = $("#aud-a-file");
    if (aFile) aFile.addEventListener("change", (e) => {
      const f = e.target.files && e.target.files[0];
      state.pickFile = f || null;
      state.uploadMsg = "";
      renderAuditorPage();
    });

    const aUp = $("#aud-a-upload");
    if (aUp) aUp.addEventListener("click", async () => {
      if (!state.projectId || !state.pickFile) return;
      state.uploadBusy = true; state.uploadMsg = "";
      renderAuditorPage();
      const f = state.pickFile;
      try {
        const b64 = await readFileAsBase64(f);
        // Detect MasterFormat sections client-side from PDF text (Item 15).
        let sections = [];
        if (isPdf(f)) {
          const text = await extractPdfText(f);
          sections = detectMasterFormatSections(text);
        }
        if (sections.length) state.sectionsByName[f.name] = sections;
        await LinStore.ingestCorpus({
          id: state.projectId,
          name: f.name,
          docType: state.pickDocType,
          mimeType: f.type || "application/octet-stream",
          dataBase64: b64,
          masterFormatSections: sections
        });
        state.uploadMsg = "✓ Uploaded — " + f.name +
          (sections.length ? " · " + sections.length + " MasterFormat section" + (sections.length > 1 ? "s" : "") + " detected" : "");
        state.pickFile = null;
        await loadCorpus();
      } catch (err) {
        state.uploadMsg = "Upload failed: " + (err && err.message ? err.message : "store unreachable");
      } finally {
        state.uploadBusy = false;
        renderAuditorPage();
      }
    });

    /* Section B */
    const rt = $("#aud-review-type");
    if (rt) rt.addEventListener("change", (e) => { state.reviewType = e.target.value; });

    const sub = $("#aud-submission");
    if (sub) sub.addEventListener("change", async (e) => {
      const f = e.target.files && e.target.files[0];
      if (!f) return;
      try {
        const b64 = await readFileAsBase64(f);
        state.submission = { name: f.name, mime: f.type || "application/octet-stream", size: f.size, base64: b64 };
        state.auditError = "";
      } catch (err) {
        state.submission = null;
        state.auditError = "Couldn't read submission file.";
      }
      renderAuditorPage();
    });

    const run = $("#aud-run");
    if (run) run.addEventListener("click", async () => {
      if (!state.projectId || !state.submission || state.corpus.length === 0) return;
      state.auditing = true; state.auditError = ""; state.auditResult = null; state.drafts = {};
      renderAuditorPage();
      try {
        const corpusIds = state.corpus.map(fileIdOf).filter(Boolean);
        const resp = await LinStore.runAudit({
          id: state.projectId,
          reviewType: state.reviewType,
          submissionName: state.submission.name,
          submissionMime: state.submission.mime,
          submissionBase64: state.submission.base64,
          corpusIds
        });
        const payload = resp.audit || resp.result || resp;
        state.auditResult = payload || { items: [], summary: {} };
        state.resultsOpen = true;     // auto-expand AUDIT RESULTS after a fresh run
        // Persist to Drive (non-fatal) and cache locally for View/Export XLSX.
        const auditId = "audit_" + Date.now();
        const auditPayload = Object.assign({ audit_id: auditId, run_at: new Date().toISOString(),
          submittal_file: state.submission ? state.submission.name : "",
          overall_verdict: (payload && payload.overall_verdict) || "" }, payload);
        cacheAuditResult(auditId, auditPayload);
        LinStore.saveAuditResult(state.projectId, auditPayload); // fire-and-forget
        loadPastAudits().then(renderAuditorPage);
      } catch (err) {
        state.auditError = "Audit failed: " + (err && err.message ? err.message : "store unreachable");
      } finally {
        state.auditing = false;
        renderAuditorPage();
      }
    });

    /* Item 17: per-row "Draft contractor response" via the chat endpoint. */
    root.querySelectorAll(".aud-draft-btn").forEach((btn) => btn.addEventListener("click", async () => {
      const i = Number(btn.dataset.row);
      const r = state.auditResult;
      const items = r && (Array.isArray(r.items) ? r.items : (Array.isArray(r.results) ? r.results : []));
      const it = items && items[i];
      if (!it) return;
      const item = it.item || it.itemSubmitted || it.submittedItem || "(item)";
      const remark = it.remark || it.comment || it.note || "(remark)";
      state.drafts[i] = { loading: true };
      renderAuditorPage();
      try {
        const question = `Draft a polite contractor response request for: ${item} — ${remark}. ` +
          `Keep it professional, neutral, and under 100 words.`;
        const answer = await LinStore.chat(question, state.projectId);
        state.drafts[i] = { text: String(answer || "").trim() || "(no draft returned)" };
      } catch (e) {
        state.drafts[i] = { error: "Draft failed: " + (e && e.message ? e.message : "store unreachable") };
      }
      renderAuditorPage();
    }));

    const xlsxBtn = $("#aud-export-xlsx");
    if (xlsxBtn) xlsxBtn.addEventListener("click", () => {
      if (state.auditResult) exportAuditXLSX(state.auditResult, state.projectId);
    });

    // Past Audits: View toggle and Export XLSX per row
    root.querySelectorAll(".aud-history-view").forEach((btn) => btn.addEventListener("click", () => {
      const id = btn.dataset.auditId;
      state.expandedAudit = state.expandedAudit === id ? null : id;
      renderAuditorPage();
    }));
    root.querySelectorAll(".aud-history-xlsx").forEach((btn) => btn.addEventListener("click", () => {
      const id = btn.dataset.auditId;
      const cached = state.pastAuditCache[id];
      if (cached) exportAuditXLSX(cached, state.projectId);
    }));
  }

  window.LinAuditor = { renderAuditorPage };
})();
