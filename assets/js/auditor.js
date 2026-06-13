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

    /* Section B */
    reviewType: "material_submittal",
    submission: null,         // {name, mime, size, base64}
    auditing: false,
    auditError: "",
    auditResult: null         // {items[], summary{}, csvContent, csvName}
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
            return `<li class="aud-corpus-row">
              <span class="aud-corpus-name">${esc(name)}</span>
              <span class="aud-corpus-date kn-sub">${esc(fmtDate(when))}</span>
            </li>`;
          }).join("")}</ul>`
        : `<p class="kn-sub aud-corpus-empty">None uploaded yet.</p>`;
      return `<div class="aud-corpus-group">
        <p class="eyebrow">${esc(dt.label)}</p>
        ${rows}
      </div>`;
    }).join("");
  }

  function sectionAHtml() {
    const canUpload = !!(state.projectId && state.pickFile && !state.uploadBusy);
    const msg = state.uploadMsg;
    return `<section class="panel aud-panel ${state.projectId ? "" : "is-muted"}">
      <p class="eyebrow">Section A · Corpus</p>
      <h2 class="kn-h">User Requirements</h2>
      <p class="kn-sub">Upload the reference documents this project will be audited against. Stored in the project folder and reused automatically in every future audit.</p>

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
      </div>
    </section>`;
  }

  function resultsHtml() {
    if (state.auditError) return `<p class="aud-msg warn" aria-live="polite">${esc(state.auditError)}</p>`;
    if (state.auditing) return `<div class="aud-loading" aria-live="polite">
        <span class="aud-spinner" aria-hidden="true"></span>
        <span>Auditing with Gemini… this may take 10–20 seconds.</span>
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
    const csvName = r.csvName || r.filename || ("audit_" + state.reviewType + "_" + Date.now() + ".csv");

    const rows = items.map((it, i) => {
      const sk = statusKey(it.status);
      const statusLabel = it.status || "—";
      return `<tr>
        <td class="aud-num">${i + 1}</td>
        <td>${esc(it.item || it.itemSubmitted || it.submittedItem || "—")}</td>
        <td>${esc(it.remark || it.comment || it.note || "—")}</td>
        <td class="aud-cite">${esc(it.citation || it.reference || "—")}</td>
        <td><span class="aud-status aud-status-${sk}">${esc(statusLabel)}</span></td>
      </tr>`;
    }).join("");

    return `<div class="aud-result">
      <div class="aud-summary">
        <strong>${total}</strong> items reviewed —
        <span class="aud-status aud-status-approved">${ap} Approved</span>,
        <span class="aud-status aud-status-approved-as-noted">${apN} Approved as Noted</span>,
        <span class="aud-status aud-status-rejected">${rj} Rejected</span>,
        <span class="aud-status aud-status-remark">${rm} Remarks</span>
      </div>

      ${items.length
        ? `<div class="aud-table-wrap"><table class="aud-table">
            <thead><tr><th>#</th><th>Item Submitted</th><th>Remark</th><th>Citation</th><th>Status</th></tr></thead>
            <tbody>${rows}</tbody>
          </table></div>`
        : `<p class="kn-sub">The audit returned no line items.</p>`}

      <div class="aud-download-row">
        <button class="btn primary aud-download" id="aud-download-csv">Download Remark</button>
        <p class="kn-sub aud-saved-note">Results also saved to project folder: <span class="mod-mono">${esc(csvName)}</span></p>
      </div>
    </div>`;
  }

  function sectionBHtml() {
    const hasProject = !!state.projectId;
    const hasCorpus = state.corpus.length > 0;
    const canRun = !!(hasProject && hasCorpus && state.submission && !state.auditing);
    const emptyCorpusMsg = hasProject && !state.corpusLoading && !hasCorpus
      ? `<p class="aud-msg warn">No reference documents found for this project. Upload specifications, codes, or user requirements in User Requirements above before running an audit.</p>`
      : "";
    return `<section class="panel aud-panel ${hasProject ? "" : "is-muted"}">
      <p class="eyebrow">Section B · Audit</p>
      <h2 class="kn-h">Technical Audit</h2>
      <p class="kn-sub">Upload a submission to audit it against all reference documents in this project's corpus. Results are saved to the project folder.</p>
      <p class="aud-illus" role="note">Audit findings are AI-generated (Gemini) and illustrative only. All verdicts require named human review and sign-off before any formal action is taken.</p>

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
        ${resultsHtml()}
      </div>
    </section>`;
  }

  function historyHtml() {
    if (!state.projectId) return `<p class="kn-sub">Select a project to view its audit history.</p>`;
    if (state.pastLoading) return `<p class="kn-sub">Loading audit history…</p>`;
    if (state.pastError) return `<p class="aud-msg warn">${esc(state.pastError)}</p>`;
    if (!state.pastAudits.length) return `<p class="kn-sub">No audit history yet for this project.</p>`;
    const rows = state.pastAudits.map((f) => {
      const name = f.name || f.filename || "(unnamed)";
      const when = f.createdAt || f.date || f.modifiedAt || "";
      return `<tr>
        <td class="aud-past-date">${esc(fmtDate(when))}</td>
        <td>${esc(reviewTypeFromName(name))}</td>
        <td class="aud-past-name mod-mono">${esc(name)}</td>
      </tr>`;
    }).join("");
    return `<div class="aud-table-wrap"><table class="aud-table">
        <thead><tr><th>Date</th><th>Review Type</th><th>Filename</th></tr></thead>
        <tbody>${rows}</tbody>
      </table></div>
      <p class="kn-sub" style="margin-top:8px">To re-download a past result, open the project folder in Google Drive.</p>`;
  }

  function historySectionHtml() {
    return `<section class="panel aud-panel ${state.projectId ? "" : "is-muted"}">
      <p class="eyebrow">Audit history</p>
      <h2 class="kn-h">Audit History</h2>
      ${historyHtml()}
    </section>`;
  }

  function renderAuditorPage() {
    const root = document.getElementById("auditor-root");
    if (!root) return;
    root.innerHTML =
      topPickerHtml() +
      `<div class="aud-stack">` +
        sectionAHtml() +
        sectionBHtml() +
        historySectionHtml() +
      `</div>`;
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
        await LinStore.ingestCorpus({
          id: state.projectId,
          name: f.name,
          docType: state.pickDocType,
          mimeType: f.type || "application/octet-stream",
          dataBase64: b64
        });
        state.uploadMsg = "✓ Uploaded — " + f.name;
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
      state.auditing = true; state.auditError = ""; state.auditResult = null;
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
        loadPastAudits().then(renderAuditorPage);
      } catch (err) {
        state.auditError = "Audit failed: " + (err && err.message ? err.message : "store unreachable");
      } finally {
        state.auditing = false;
        renderAuditorPage();
      }
    });

    const dl = $("#aud-download-csv");
    if (dl) dl.addEventListener("click", () => {
      const r = state.auditResult;
      if (!r) return;
      const csv = r.csvContent || r.csv || "";
      if (!csv) { alert("No CSV content was returned for this audit."); return; }
      const name = r.csvName || r.filename || ("audit_" + state.reviewType + "_" + Date.now() + ".csv");
      const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = name;
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
    });
  }

  window.LinAuditor = { renderAuditorPage };
})();
