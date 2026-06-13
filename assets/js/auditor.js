/* ============================================================
   lin-project-radar — auditor.js  (Technical Auditor page)
   ------------------------------------------------------------
   Section A — User Requirements: per-project corpus ingest
     (Specification / Code of Practice / User Requirement).
   Section B — Technical Audit: pick corpus refs, upload a
     submission (PDF/image), run a Gemini-backed audit via the
     backend, render the verdict table, download CSV, list past.
   All file payloads are read client-side with FileReader and
   sent as base64; all network goes through LinStore (LIN_API_URL).
   ============================================================ */
(function () {
  "use strict";

  const esc = (s) => String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  const DOC_TYPES = [
    { key: "specification",    label: "Specification",
      blurb: "Project specifications, technical requirements, and material standards." },
    { key: "code_of_practice", label: "Code of Practice",
      blurb: "Applicable building codes, standards, and regulations (e.g. IBC, ACI, NFPA)." },
    { key: "user_requirement", label: "User Requirement",
      blurb: "Owner/client base drawings, design intent documents, or consultant requirements." }
  ];
  const DOC_TYPE_LABEL = { specification: "Specification", code_of_practice: "Code of Practice", user_requirement: "User Requirement" };

  const REVIEW_TYPES = [
    { key: "material_submittal", label: "Material Submittal" },
    { key: "drawing",            label: "Drawing" }
  ];

  const ACCEPT = ".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg";

  /* ---------- in-memory page state ---------- */
  let state = {
    projectId: "",
    corpus: [],
    corpusLoading: false,
    corpusError: "",
    pastAudits: [],
    pastError: "",
    /* per-docType chosen file (for Section A) */
    pickA: { specification: null, code_of_practice: null, user_requirement: null },
    uploadMsg: { specification: "", code_of_practice: "", user_requirement: "" },
    uploadBusy: { specification: false, code_of_practice: false, user_requirement: false },
    /* Section B */
    reviewType: "material_submittal",
    selectedCorpusIds: new Set(),
    submission: null,                 // {name, mime, size, base64}
    auditing: false,
    auditError: "",
    auditResult: null                 // { items[], summary{}, csvContent, csvName }
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
    return `<option value="">Select project…</option>` +
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

  /* ---------- corpus + past-audits loading ---------- */
  async function loadCorpus() {
    if (!state.projectId) { state.corpus = []; return; }
    state.corpusLoading = true; state.corpusError = "";
    try {
      const list = await LinStore.listCorpus(state.projectId);
      state.corpus = Array.isArray(list) ? list : [];
    } catch (e) {
      state.corpusError = "Couldn't load corpus — store unreachable.";
      state.corpus = [];
    } finally {
      state.corpusLoading = false;
    }
  }
  async function loadPastAudits() {
    if (!state.projectId) { state.pastAudits = []; return; }
    state.pastError = "";
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
      state.pastError = "Couldn't load past audit results.";
      state.pastAudits = [];
    }
  }

  /* ---------- rendering ---------- */
  function corpusByType(type) {
    return state.corpus.filter((f) => (f.docType || "").toLowerCase() === type);
  }
  function corpusEntryHtml(f) {
    const fileId = f.fileId || f.id || f.driveId || "";
    const name = f.name || f.filename || "(unnamed)";
    const when = f.createdAt || f.date || f.modifiedAt || "";
    return `<li class="aud-corpus-row">
      <span class="aud-corpus-name">${esc(name)}</span>
      <span class="aud-corpus-date kn-sub">${esc(fmtDate(when))}</span>
      <span class="mod-mono kn-sub" title="File ID">${esc(String(fileId).slice(0, 10))}${fileId.length > 10 ? "…" : ""}</span>
    </li>`;
  }
  function corpusCheckHtml(f) {
    const fileId = f.fileId || f.id || f.driveId || "";
    const name = f.name || f.filename || "(unnamed)";
    const when = f.createdAt || f.date || f.modifiedAt || "";
    const t = (f.docType || "").toLowerCase();
    const checked = state.selectedCorpusIds.has(fileId);
    return `<label class="aud-check">
      <input type="checkbox" class="aud-corpus-pick" data-fileid="${esc(fileId)}" ${checked ? "checked" : ""} />
      <span class="aud-check-main">${esc(name)}</span>
      <span class="aud-check-meta kn-sub">${esc(DOC_TYPE_LABEL[t] || t || "Reference")} · ${esc(fmtDate(when))}</span>
    </label>`;
  }

  function sectionAHtml() {
    const subs = DOC_TYPES.map((dt) => {
      const list = corpusByType(dt.key);
      const pick = state.pickA[dt.key];
      const busy = state.uploadBusy[dt.key];
      const msg = state.uploadMsg[dt.key];
      const disabled = !state.projectId || !pick || busy;
      return `<div class="aud-doctype" data-doctype="${dt.key}">
        <div class="aud-doctype-head">
          <p class="eyebrow">${esc(dt.label)}</p>
          <p class="kn-sub">${esc(dt.blurb)}</p>
        </div>
        <div class="aud-uploader">
          <label class="aud-filebtn ${state.projectId ? "" : "is-disabled"}">
            <input type="file" class="aud-a-file" accept="${ACCEPT}" data-doctype="${dt.key}" ${state.projectId ? "" : "disabled"} />
            <span class="aud-filebtn-label">${pick ? esc(pick.name) : "Choose file (PDF or image)…"}</span>
            ${pick ? `<span class="kn-sub">· ${esc(fmtSize(pick.size))}</span>` : ""}
          </label>
          <button class="btn primary aud-a-upload" data-doctype="${dt.key}" ${disabled ? "disabled" : ""}>${busy ? "Uploading…" : "Upload"}</button>
        </div>
        ${msg ? `<p class="aud-msg ${msg.startsWith("✓") ? "ok" : "warn"}" aria-live="polite">${esc(msg)}</p>` : ""}
        <p class="eyebrow" style="margin-top:10px">Already uploaded</p>
        ${list.length
          ? `<ul class="aud-corpus-list">${list.map(corpusEntryHtml).join("")}</ul>`
          : `<p class="kn-sub aud-corpus-empty">${state.projectId ? "None uploaded yet." : "Select a project to view its corpus."}</p>`}
      </div>`;
    }).join("");

    return `<section class="panel aud-panel aud-panel-a">
      <p class="eyebrow">Section A · Corpus</p>
      <h2 class="kn-h">User Requirements</h2>
      <p class="kn-sub">Upload the reference documents this project will be audited against. These are stored in the project folder and available for all future audits.</p>

      <label class="rationale-label">Project
        <select id="aud-project" class="ig-input">${projectOptions()}</select></label>

      <div class="aud-doctype-grid">${subs}</div>
    </section>`;
  }

  function corpusChecklistHtml() {
    if (state.corpusLoading) return `<p class="kn-sub">Loading corpus…</p>`;
    if (state.corpusError)   return `<p class="aud-msg warn">${esc(state.corpusError)}</p>`;
    if (!state.projectId)    return `<p class="kn-sub">Select a project to load its reference corpus.</p>`;
    if (!state.corpus.length) return `<p class="kn-sub">No reference documents uploaded yet. Upload in User Requirements above.</p>`;
    const groups = DOC_TYPES.map((dt) => {
      const list = corpusByType(dt.key);
      if (!list.length) return "";
      return `<div class="aud-check-group">
        <p class="eyebrow">${esc(dt.label)}</p>
        ${list.map(corpusCheckHtml).join("")}
      </div>`;
    }).join("");
    return `<div class="aud-corpus-toolbar">
        <button type="button" class="aud-link" id="aud-select-all">Select all</button>
        <span class="kn-sub">·</span>
        <button type="button" class="aud-link" id="aud-deselect-all">Deselect all</button>
        <span class="kn-sub">· ${state.selectedCorpusIds.size} selected</span>
      </div>
      ${groups}`;
  }

  function resultsHtml() {
    if (state.auditError) return `<p class="aud-msg warn" aria-live="polite">${esc(state.auditError)}</p>`;
    if (state.auditing) return `<div class="aud-loading" aria-live="polite">
        <span class="aud-spinner" aria-hidden="true"></span>
        <span>Auditing with Gemini… this may take 10–20 seconds for large documents.</span>
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
      <div class="aud-result-head">
        <div class="aud-summary">
          <strong>${total}</strong> items reviewed —
          <span class="aud-status aud-status-approved">${ap} Approved</span>,
          <span class="aud-status aud-status-approved-as-noted">${apN} Approved as Noted</span>,
          <span class="aud-status aud-status-rejected">${rj} Rejected</span>,
          <span class="aud-status aud-status-remark">${rm} Remarks</span>
        </div>
        <button class="btn primary" id="aud-download-csv">Download CSV</button>
      </div>
      ${r.csvName || r.filename ? `<p class="kn-sub">Results saved to project folder: <span class="mod-mono">${esc(csvName)}</span></p>` : ""}
      ${items.length
        ? `<div class="aud-table-wrap"><table class="aud-table">
            <thead><tr><th>#</th><th>Item Submitted</th><th>Remark</th><th>Citation</th><th>Status</th></tr></thead>
            <tbody>${rows}</tbody>
          </table></div>`
        : `<p class="kn-sub">The audit returned no line items.</p>`}
    </div>`;
  }

  function pastAuditsHtml() {
    if (!state.projectId) return `<p class="kn-sub">Select a project to view its past audits.</p>`;
    if (state.pastError)  return `<p class="aud-msg warn">${esc(state.pastError)}</p>`;
    if (!state.pastAudits.length) return `<p class="kn-sub">No audit results yet for this project.</p>`;
    return `<ul class="aud-past-list">
      ${state.pastAudits.map((f) => {
        const name = f.name || f.filename || "(unnamed)";
        const when = f.createdAt || f.date || f.modifiedAt || "";
        return `<li class="aud-past-row">
          <span class="aud-past-name">${esc(name)}</span>
          <span class="aud-past-date kn-sub">${esc(fmtDate(when))}</span>
        </li>`;
      }).join("")}
    </ul>`;
  }

  function sectionBHtml() {
    const corpusReady = state.projectId && state.selectedCorpusIds.size > 0;
    const canRun = !!(state.projectId && corpusReady && state.submission && !state.auditing);
    return `<section class="panel aud-panel aud-panel-b">
      <p class="eyebrow">Section B · Audit</p>
      <h2 class="kn-h">Technical Audit</h2>
      <p class="kn-sub">Select a project, choose reference documents from the corpus, upload a submission, and run the audit. Results are saved to the project folder and available to download.</p>
      <p class="aud-illus" role="note">Audit findings are AI-generated (Gemini) and illustrative only. All verdicts require named human review and sign-off before any formal action is taken.</p>

      <div class="aud-step">
        <p class="eyebrow">Step 1 · Project</p>
        <label class="rationale-label">Project
          <select id="aud-project-b" class="ig-input">${projectOptions()}</select></label>
      </div>

      <div class="aud-step">
        <p class="eyebrow">Step 2 · Review type</p>
        <label class="rationale-label">Review type
          <select id="aud-review-type" class="ig-input">
            ${REVIEW_TYPES.map((rt) => `<option value="${rt.key}"${rt.key === state.reviewType ? " selected" : ""}>${esc(rt.label)}</option>`).join("")}
          </select></label>
      </div>

      <div class="aud-step">
        <p class="eyebrow">Step 3 · Reference corpus</p>
        ${corpusChecklistHtml()}
      </div>

      <div class="aud-step">
        <p class="eyebrow">Step 4 · Submission</p>
        <label class="aud-filebtn ${state.projectId ? "" : "is-disabled"}">
          <input type="file" id="aud-submission" accept="${ACCEPT}" ${state.projectId ? "" : "disabled"} />
          <span class="aud-filebtn-label">${state.submission ? esc(state.submission.name) : "Submission (PDF or image)…"}</span>
          ${state.submission ? `<span class="kn-sub">· ${esc(fmtSize(state.submission.size))}</span>` : ""}
        </label>
      </div>

      <div class="aud-step">
        <p class="eyebrow">Step 5 · Run</p>
        <div class="dc-actions">
          <button class="btn primary" id="aud-run" ${canRun ? "" : "disabled"}>${state.auditing ? "Running…" : "Run Audit"}</button>
        </div>
        ${resultsHtml()}
      </div>

      <div class="aud-step aud-past">
        <p class="eyebrow">Past Audits</p>
        ${pastAuditsHtml()}
      </div>
    </section>`;
  }

  function renderAuditorPage() {
    const root = document.getElementById("auditor-root");
    if (!root) return;
    root.innerHTML = sectionAHtml() + sectionBHtml();
    wire(root);
  }

  /* ---------- wiring ---------- */
  function wire(root) {
    const $ = (sel) => root.querySelector(sel);
    const $$ = (sel) => root.querySelectorAll(sel);

    /* keep the two project selectors in sync */
    const selA = $("#aud-project");
    const selB = $("#aud-project-b");
    function onProjectChange(id) {
      if (state.projectId === id) return;
      state.projectId = id;
      state.selectedCorpusIds.clear();
      state.submission = null;
      state.auditResult = null;
      state.auditError = "";
      state.pickA = { specification: null, code_of_practice: null, user_requirement: null };
      state.uploadMsg = { specification: "", code_of_practice: "", user_requirement: "" };
      Promise.all([loadCorpus(), loadPastAudits()]).then(renderAuditorPage);
      renderAuditorPage(); // immediate redraw to flip enabled states + show "loading"
    }
    if (selA) selA.addEventListener("change", (e) => onProjectChange(e.target.value));
    if (selB) selB.addEventListener("change", (e) => onProjectChange(e.target.value));

    /* Section A: file pick + upload */
    $$(".aud-a-file").forEach((inp) => inp.addEventListener("change", (e) => {
      const dt = e.target.dataset.doctype;
      const f = e.target.files && e.target.files[0];
      if (!f) return;
      state.pickA[dt] = f;
      state.uploadMsg[dt] = "";
      renderAuditorPage();
    }));
    $$(".aud-a-upload").forEach((btn) => btn.addEventListener("click", async () => {
      const dt = btn.dataset.doctype;
      const f = state.pickA[dt];
      if (!state.projectId || !f) return;
      state.uploadBusy[dt] = true;
      state.uploadMsg[dt] = "";
      renderAuditorPage();
      try {
        const b64 = await readFileAsBase64(f);
        await LinStore.ingestCorpus({
          id: state.projectId,
          name: f.name,
          docType: dt,
          mimeType: f.type || "application/octet-stream",
          dataBase64: b64
        });
        state.uploadMsg[dt] = "✓ Uploaded — " + f.name;
        state.pickA[dt] = null;
        await loadCorpus();
      } catch (e) {
        state.uploadMsg[dt] = "Upload failed: " + (e && e.message ? e.message : "store unreachable");
      } finally {
        state.uploadBusy[dt] = false;
        renderAuditorPage();
      }
    }));

    /* Section B: review type */
    const rt = $("#aud-review-type");
    if (rt) rt.addEventListener("change", (e) => { state.reviewType = e.target.value; });

    /* Section B: corpus checks */
    $$(".aud-corpus-pick").forEach((cb) => cb.addEventListener("change", (e) => {
      const id = e.target.dataset.fileid;
      if (e.target.checked) state.selectedCorpusIds.add(id);
      else state.selectedCorpusIds.delete(id);
      renderAuditorPage();
    }));
    const selAll = $("#aud-select-all");
    if (selAll) selAll.addEventListener("click", () => {
      state.corpus.forEach((f) => state.selectedCorpusIds.add(f.fileId || f.id || f.driveId || ""));
      renderAuditorPage();
    });
    const deselAll = $("#aud-deselect-all");
    if (deselAll) deselAll.addEventListener("click", () => {
      state.selectedCorpusIds.clear();
      renderAuditorPage();
    });

    /* Section B: submission file */
    const sub = $("#aud-submission");
    if (sub) sub.addEventListener("change", async (e) => {
      const f = e.target.files && e.target.files[0];
      if (!f) return;
      try {
        const b64 = await readFileAsBase64(f);
        state.submission = { name: f.name, mime: f.type || "application/octet-stream", size: f.size, base64: b64 };
      } catch (err) {
        state.submission = null;
        state.auditError = "Couldn't read submission file.";
      }
      renderAuditorPage();
    });

    /* Section B: Run Audit */
    const runBtn = $("#aud-run");
    if (runBtn) runBtn.addEventListener("click", async () => {
      if (!state.projectId || !state.submission || state.selectedCorpusIds.size === 0) return;
      state.auditing = true; state.auditError = ""; state.auditResult = null;
      renderAuditorPage();
      try {
        const resp = await LinStore.runAudit({
          id: state.projectId,
          reviewType: state.reviewType,
          submissionName: state.submission.name,
          submissionMime: state.submission.mime,
          submissionBase64: state.submission.base64,
          corpusIds: Array.from(state.selectedCorpusIds)
        });
        const payload = resp.audit || resp.result || resp;
        state.auditResult = payload || { items: [], summary: {} };
        loadPastAudits().then(renderAuditorPage);
      } catch (e) {
        state.auditError = "Audit failed: " + (e && e.message ? e.message : "store unreachable");
      } finally {
        state.auditing = false;
        renderAuditorPage();
      }
    });

    /* Section B: download CSV */
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
