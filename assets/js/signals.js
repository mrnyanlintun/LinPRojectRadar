/* ============================================================
   lin-project-radar — signals.js  (Piece C)
   ------------------------------------------------------------
   Document-driven signal ingestion + review. Replaces the old
   "type CPI / SPI / BAC" manual form. A PM uploads a real
   construction document; the backend (Gemini, v6) extracts the
   EVM figures and returns merged signalInputs. When both CPI and
   SPI are present (readyToRun) we feed those extracted values
   into the EXISTING Monte Carlo + CUSUM + PCEIF pipeline
   (LinSim.buildSignals) — same models, extracted inputs instead
   of typed ones. A details panel shows extracted values (with
   source tags), still-missing values, an overwrite control per
   field (governed correction + reason, logged server-side), and
   the signal audit trail.
   ============================================================ */
(function () {
  "use strict";

  const esc = (s) => String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  /* ---------- document types (value → label) ---------- */
  const DOC_TYPES = [
    ["contract_value",        "Contract Value / Original Agreement"],
    ["schedule_of_values",    "Schedule of Values (G703)"],
    ["pay_application",       "Pay Application (G702)"],
    ["time_phased_schedule",  "Time-phased Schedule / Baseline"],
    ["schedule_update",       "Schedule Update / Look-ahead"],
    ["change_order",          "Change Order / PCO"],
    ["monthly_report",        "Monthly Progress Report"],
    ["rfi",                   "RFI / RFI Log"],
    ["submittal",             "Submittal / Submittal Register"],
    ["oac_minutes",           "OAC Meeting Minutes"],
    ["correspondence_notice", "Correspondence / Notice"],
    ["risk_register",         "Risk Register"],
    ["inspection_report",     "Inspection Report / NCR"],
    ["field_report",          "Daily / Weekly Field Report"],
    ["commissioning_report",  "Test & Commissioning Report"]
  ];
  const DOC_TYPE_LABEL = DOC_TYPES.reduce((m, [k, v]) => (m[k] = v, m), {});

  /* signalInputs rows, in display order. editable = has an overwrite pencil. */
  const FIELD_ROWS = [
    { key: "bac",                label: "BAC",                     editable: true },
    { key: "ev",                 label: "EV (completed-to-date)",  editable: true },
    { key: "ac",                 label: "AC (paid-to-date)",       editable: true },
    { key: "pv",                 label: "PV (planned value)",      editable: true },
    { key: "actualPctComplete",  label: "Actual % complete",       editable: true },
    { key: "plannedPctComplete", label: "Planned % complete",      editable: true },
    { key: "docRiskScore",       label: "Document-risk score",     editable: true },
    { key: "cpi",                label: "CPI (computed)",           editable: false },
    { key: "spi",                label: "SPI (computed)",           editable: false }
  ];

  const ACCEPT = ".pdf,.doc,.docx,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg," +
    "application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document";

  /* ---------- per-project module cache (latest extraction result) ---------- */
  // cache[id] = { signalInputs, missing, readyToRun }
  const cache = {};

  /* ---------- PDF.js client-side text extraction ----------
     Apps Script's byte-level PDF parsing is unreliable for ReportLab-generated
     PDFs, so PDFs are converted to plain text in the browser and sent as `text`.
     The CDN script (index.html) exposes the global `pdfjsLib`. */
  let pdfWorkerSet = false;
  function ensurePdfWorker() {
    if (pdfWorkerSet || typeof pdfjsLib === "undefined") return;
    pdfjsLib.GlobalWorkerOptions.workerSrc =
      "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
    pdfWorkerSet = true;
  }
  async function extractPDFText(file) {
    ensurePdfWorker();
    const arrayBuffer = await file.arrayBuffer();
    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
    let text = "";
    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      const content = await page.getTextContent();
      text += content.items.map((item) => item.str).join(" ") + "\n";
    }
    return text.trim();
  }
  const isPdf = (file) =>
    file.type === "application/pdf" || /\.pdf$/i.test(file.name || "");

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
  function fmtNum(v) {
    if (v == null || v === "") return null;
    const n = Number(v);
    if (!Number.isFinite(n)) return String(v);
    // keep small ratios at 2dp, whole-ish money at 0–2dp
    if (Math.abs(n) < 10) return (Math.round(n * 100) / 100).toString();
    return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
  }
  function fmtDate(s) {
    if (!s) return "";
    try { return window.LinTZ ? LinTZ.format(s) : String(s); } catch (e) { return String(s); }
  }
  function projectOptions(selectedId) {
    const list = (LinStore.cachedActive && LinStore.cachedActive()) || [];
    return `<option value="">Select project…</option>` +
      list.map((p) => `<option value="${esc(p.id)}"${p.id === selectedId ? " selected" : ""}>${esc(p.id)} — ${esc(p.name)}</option>`).join("");
  }
  function sourceDocType(si, key) {
    const src = si && si.sources && si.sources[key];
    if (!src) return null;
    return src.docType || src.doc || src.type || null;
  }

  /* ---------- run the EXISTING models from extracted signalInputs ----------
     Same path the old manual form used (LinSim.buildSignals + saveProject),
     fed from extracted cpi/spi/bac/doc-risk. fairnessSensitive is left
     untouched so the red-review fairness gate behaves exactly as before. */
  async function runModels(project, si) {
    const cpiNum = Number(si.cpi), spiNum = Number(si.spi);
    const haveCpi = Number.isFinite(cpiNum) && cpiNum > 0;
    const haveSpi = Number.isFinite(spiNum) && spiNum > 0;
    // Run when EITHER index is present. A project with only SPI (or only CPI)
    // extracted should still compute — buildSignals uses a neutral 1.0 for the
    // missing index (the model logic itself is unchanged).
    if (!haveCpi && !haveSpi) return false;
    const bac = Number(si.bac);
    const docScore = Number(si.docRiskScore);
    // Keep the extracted inputs on the project (matches the signalInputs model
    // and is persisted with the project on save).
    project.signalInputs = si;
    project.signals = LinSim.buildSignals({
      cpi: haveCpi ? cpiNum : 1,
      spi: haveSpi ? spiNum : 1,
      bac: Number.isFinite(bac) && bac > 0 ? bac : undefined,
      metric: haveSpi ? "SPI" : "CPI",
      docScore: Number.isFinite(docScore) ? docScore : 0.1,
      docSource: "(extracted from project documents)",
      docExcerpt: "Signals extracted from uploaded documents via the document-ingestion flow.",
      seed: LinSim.hashSeed(project.id)
    });
    // Item 11: client-side multi-model simulations (zero tokens, zero backend).
    // Run the five additional models from the extracted inputs and store the
    // unified signal array on the project for display + governance synthesis.
    let simPayload = null;
    if (window.LinSimulations) {
      try {
        const simResults = LinSimulations.runAll(si);
        const now = new Date();
        simPayload = {
          signal_metadata: {
            project_id: project.id,
            reporting_period: now.toISOString().substring(0, 7),
            data_date: now.toISOString().substring(0, 10)
          },
          signal_array: simResults
        };
        project.simulationSignals = simPayload;
      } catch (e) { /* simulations are non-fatal — never block the core run */ }
    }
    const builtSignals = project.signals;
    await LinStore.saveProject(project);
    // saveProject reconciles the in-memory mirror with the backend's echoed
    // project, which omits client-only fields (the built signals package,
    // signalInputs, and simulationSignals). Re-assert them onto the canonical
    // cached object so the detail deep-dive (Five signals + the five extra
    // simulation cards) and the ledger keep rendering after the save.
    const cached = LinStore.getCached(project.id);
    if (cached) {
      if (!hasSignals(cached) && builtSignals) cached.signals = builtSignals;
      if (!cached.signalInputs) cached.signalInputs = si;
      if (!cached.simulationSignals && simPayload) cached.simulationSignals = simPayload;
    }
    return true;
  }

  /* refresh the in-memory project (events + persisted state) after a server
     mutation, so the audit trail reflects the new signals_* event. */
  async function refreshProject(id) {
    try {
      const fresh = await LinStore.getProject(id);
      if (fresh && window.LIN_PROJECTS) {
        const i = LIN_PROJECTS.findIndex((x) => x.id === id);
        if (i >= 0) {
          // Don't drop the signals/inputs we just computed/saved if the server's
          // copy hasn't caught up yet (eventual consistency / save↔get race).
          if (!hasSignals(fresh) && hasSignals(LIN_PROJECTS[i])) fresh.signals = LIN_PROJECTS[i].signals;
          if (!fresh.signalInputs && LIN_PROJECTS[i].signalInputs) fresh.signalInputs = LIN_PROJECTS[i].signalInputs;
          if (!fresh.simulationSignals && LIN_PROJECTS[i].simulationSignals) fresh.simulationSignals = LIN_PROJECTS[i].simulationSignals;
          LIN_PROJECTS[i] = fresh;
        }
      }
      return fresh;
    } catch (e) { return LinStore.getCached(id); }
  }

  /* ===========================================================
     Change 1 — document-ingestion form
     =========================================================== */
  function ingestFormHtml(fixedId) {
    const projectField = fixedId
      ? `<input type="hidden" class="ds-project" value="${esc(fixedId)}" />`
      : `<label class="rationale-label">Project
           <select class="ds-project ig-input">${projectOptions(null)}</select></label>`;
    return `
      <div class="kn-grid ds-form">
        <div>
          ${projectField}
          <label class="rationale-label">Document type
            <select class="ds-doctype ig-input">
              ${DOC_TYPES.map(([v, l]) => `<option value="${v}">${esc(l)}</option>`).join("")}
            </select></label>
          <p class="kn-sub">Periods (baseline / work period) are read from the document itself — no dates to enter.</p>
        </div>
        <div>
          <label class="rationale-label">Document (PDF or image — one at a time)</label>
          <label class="aud-filebtn ds-filebtn">
            <input type="file" class="ds-file" accept="${ACCEPT}" />
            <span class="ds-filebtn-label aud-filebtn-label">Choose document…</span>
          </label>
          <div class="dc-actions"><button class="btn primary ds-run">Upload &amp; extract</button></div>
          <p class="ds-status kn-sub" aria-live="polite"></p>
        </div>
      </div>`;
  }

  function wireIngestForm(container, onResult) {
    const $c = (sel) => container.querySelector(sel);
    let picked = null;
    const fileInput = $c(".ds-file");
    if (fileInput) fileInput.addEventListener("change", (e) => {
      picked = (e.target.files && e.target.files[0]) || null;
      const lbl = $c(".ds-filebtn-label");
      if (lbl) lbl.textContent = picked ? picked.name : "Choose document…";
    });

    $c(".ds-run").addEventListener("click", async () => {
      const id = $c(".ds-project").value;
      const status = $c(".ds-status");
      if (!id) { status.textContent = "Select a project first."; return; }
      if (!picked) { status.textContent = "Choose a document to upload."; return; }
      const docType = $c(".ds-doctype").value;

      const btn = $c(".ds-run");
      btn.disabled = true;
      status.textContent = "Scanning document with AI… this can take a few seconds.";
      try {
        // PDFs → extract text client-side (PDF.js) and send as `text`.
        // Images / doc / docx → send the raw file as `dataBase64`.
        const args = { id, docType, mimeType: picked.type || "application/octet-stream", fileName: picked.name };
        if (isPdf(picked) && typeof pdfjsLib !== "undefined") {
          status.textContent = "Reading PDF text in your browser…";
          args.text = await extractPDFText(picked);
          status.textContent = "Scanning document with AI… this can take a few seconds.";
        } else {
          args.dataBase64 = await readFileAsBase64(picked);
        }
        const resp = await LinStore.extractSignals(args);
        // v7 returns computed CPI/SPI in `computed`; merge them into the
        // signalInputs view so the ledger + model run see them in one place.
        const si = mergeComputed(resp);
        const missing = resp.missing || [];
        const readyToRun = resp.readyToRun != null ? !!resp.readyToRun
          : (Number.isFinite(Number(si.cpi)) && Number.isFinite(Number(si.spi)));
        const dates = extractDates(resp, si);
        cache[id] = { signalInputs: si, missing, readyToRun, dates };

        // Run as soon as EITHER index is present (not only when both are).
        const canCompute = hasIndex(si.cpi) || hasIndex(si.spi);
        const project = LinStore.getCached(id);
        let ran = false;
        if (canCompute && project) {
          status.textContent = readyToRun
            ? "CPI and SPI ready — running models…"
            : "CPI or SPI ready — running models…";
          ran = await runModels(project, si);
        }
        await refreshProject(id);

        status.textContent = ran
          ? "Extracted — models ran on the extracted signals."
          : (canCompute
              ? "Extracted — but the models could not run (check CPI/SPI)."
              : "Extracted. Upload a document with CPI or SPI to run the models (see Details below).");
        if (window.LinApp) LinApp.refresh();
        if (onResult) onResult(id, { signalInputs: si, missing, readyToRun, ran });
      } catch (e) {
        status.textContent = "Extraction failed: " + (e && e.message ? e.message : "store unreachable") + ". The form is still usable — retry.";
      } finally {
        btn.disabled = false;
      }
    });
  }

  /* ===========================================================
     Change 2 — signals detail panel (extracted / missing / audit)
     =========================================================== */
  function signalEvents(project) {
    const evs = (project && Array.isArray(project.events)) ? project.events : [];
    return evs.filter((e) => {
      const t = e.type || e.event || e.kind || "";
      return t === "signals_extracted" || t === "signal_overwritten" || t === "baseline_adjusted_eot";
    });
  }

  /* An EVM index counts as "present" only if it's a real positive number —
     null / "" / 0 do not qualify (Number(null) is 0, hence the explicit guard). */
  function hasIndex(v) {
    return v != null && v !== "" && Number.isFinite(Number(v)) && Number(v) > 0;
  }

  /* Merge the backend's computed CPI/SPI (resp.computed) into the extracted
     signalInputs so the ledger and the model run read every value from one
     object. computed wins for cpi/spi; signalInputs supplies everything else. */
  function mergeComputed(resp) {
    const si = (resp && (resp.signalInputs || resp.signals)) || {};
    const computed = (resp && resp.computed) || {};
    const merged = Object.assign({}, si);
    if (computed.cpi != null) merged.cpi = computed.cpi;
    if (computed.spi != null) merged.spi = computed.spi;
    return merged;
  }

  /* Pull the read-only extracted periods from an extract response (the backend
     reads these from the document itself — they are display-only, never input). */
  function extractDates(resp, si) {
    const out = {};
    const KEYS = ["baselineStart", "baselineEnd", "workPeriodFrom", "workPeriodTo"];
    const take = (obj) => { if (obj) KEYS.forEach((k) => { if (obj[k] != null && obj[k] !== "") out[k] = obj[k]; }); };
    take(si); take(resp); take(resp && resp.dates); take(resp && resp.periods);
    return out;
  }

  function datesBlockHtml(dates) {
    if (!dates) return "";
    const rows = [];
    if (dates.baselineStart || dates.baselineEnd) {
      rows.push(`<tr><td class="ds-field-name">Baseline period (from contract)</td>
        <td class="ds-field-val">${esc(dates.baselineStart || "?")} → ${esc(dates.baselineEnd || "?")}</td></tr>`);
    }
    if (dates.workPeriodFrom || dates.workPeriodTo) {
      rows.push(`<tr><td class="ds-field-name">Work period (from pay application)</td>
        <td class="ds-field-val">${esc(dates.workPeriodFrom || "?")} → ${esc(dates.workPeriodTo || "?")}</td></tr>`);
    }
    if (!rows.length) return "";
    return `<div class="ds-block">
      <p class="eyebrow">Extracted periods (read-only)</p>
      <table class="ds-table ds-dates-table"><tbody>${rows.join("")}</tbody></table>
    </div>`;
  }

  function extractedTableHtml(si) {
    const rows = FIELD_ROWS.map((f) => {
      const raw = si ? si[f.key] : undefined;
      const has = raw != null && raw !== "";
      const val = has ? fmtNum(raw) : "—";
      const src = sourceDocType(si, f.key);
      const srcTag = src ? `<span class="ds-src">from ${esc(DOC_TYPE_LABEL[src] || src)}</span>` : "";
      const mark = has ? `<span class="ds-extracted" title="extracted">✓ extracted</span>` : "";
      const pencil = (f.editable && has)
        ? `<button class="ds-overwrite" data-field="${f.key}" aria-label="Overwrite ${esc(f.label)}" title="Overwrite">✎</button>`
        : "";
      return `<tr class="ds-row ${has ? "" : "ds-row-empty"}">
        <td class="ds-field-name">${esc(f.label)}</td>
        <td class="ds-field-val">${esc(val)}</td>
        <td class="ds-field-src">${mark} ${srcTag}</td>
        <td class="ds-field-edit">${pencil}</td>
      </tr>`;
    }).join("");
    return `<table class="ds-table">
      <thead><tr><th>Signal input</th><th>Value</th><th>Source</th><th></th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
  }

  function missingHtml(missing) {
    if (!missing || !missing.length) {
      return `<p class="kn-sub ds-missing-clear">All required values present — nothing outstanding.</p>`;
    }
    const items = missing.map((m) => {
      if (typeof m === "string") return `<li class="ds-missing-row">${esc(m)}</li>`;
      const what = m.label || m.fields || m.field || "Missing value";
      // backend may give a ready-made instruction (`note`, e.g. "Upload Schedule
      // of Values") or just a doc reference we phrase as "Upload <doc>".
      const doc = m.requiredDoc || m.docLabel || (m.docType && DOC_TYPE_LABEL[m.docType]) || m.doc || "";
      const instruction = m.note ? esc(m.note) : (doc ? `Upload ${esc(doc)}` : "");
      return `<li class="ds-missing-row">${esc(what)}${instruction ? ` — <span class="ds-missing-doc">${instruction}</span>` : ""}</li>`;
    }).join("");
    return `<ul class="ds-missing-list">${items}</ul>`;
  }

  function auditTrailHtml(project) {
    const evs = signalEvents(project).slice().reverse(); // most recent first
    if (!evs.length) return `<p class="kn-sub">No signal extraction or override events yet for this project.</p>`;
    return `<ul class="ds-audit-list">` + evs.map((e) => {
      const t = e.type || e.event || e.kind || "";
      const when = fmtDate(e.at || e.timestamp || e.recordedAt || e.time || "");
      if (t === "signal_overwritten") {
        const field = e.field || "(field)";
        const from = e.from != null ? fmtNum(e.from) : "—";
        const to = e.to != null ? fmtNum(e.to) : (e.value != null ? fmtNum(e.value) : "—");
        const reason = e.reason || "(no reason given)";
        return `<li class="ds-audit-row ds-audit-overwrite">
          <span class="ds-audit-main">Overwrote <strong>${esc(field)}</strong>: ${esc(from)} → ${esc(to)} — reason: “${esc(reason)}”</span>
          <span class="ds-audit-time">${esc(when)}</span></li>`;
      }
      if (t === "baseline_adjusted_eot") {
        const from = e.from != null ? e.from : "?";
        const to = e.to != null ? e.to : "?";
        return `<li class="ds-audit-row ds-audit-eot">
          <span class="ds-audit-main">Baseline completion adjusted <strong>${esc(from)}</strong> → <strong>${esc(to)}</strong> via change order (EOT)</span>
          <span class="ds-audit-time">${esc(when)}</span></li>`;
      }
      // signals_extracted — "Signals extracted from [docType] — applied: [applied fields]"
      const appliedSrc = e.applied != null ? e.applied : (e.fields != null ? e.fields : e.field);
      const applied = Array.isArray(appliedSrc) ? appliedSrc.join(", ") : (appliedSrc || "signals");
      const docTypeLabel = e.docType ? (DOC_TYPE_LABEL[e.docType] || e.docType) : "document";
      return `<li class="ds-audit-row ds-audit-extract">
        <span class="ds-audit-main">Signals extracted from <strong>${esc(docTypeLabel)}</strong> — applied: ${esc(applied)}</span>
        <span class="ds-audit-time">${esc(when)}</span></li>`;
    }).join("") + `</ul>`;
  }

  function panelInnerHtml(project) {
    const id = project ? project.id : "";
    const entry = cache[id] || {};
    const si = entry.signalInputs || null;
    const missing = entry.missing || [];
    const dates = entry.dates || null;
    if (!si && !signalEvents(project).length) {
      return `<p class="kn-sub">No documents ingested for this project yet. Upload a document above to extract its signals.</p>`;
    }
    return `
      <div class="ds-block">
        <p class="eyebrow">Extracted signal inputs</p>
        ${si ? extractedTableHtml(si) : `<p class="kn-sub">No extracted values cached this session. Re-upload a document to view them.</p>`}
      </div>
      ${datesBlockHtml(dates)}
      <div class="ds-block">
        <p class="eyebrow">Missing values &amp; required documents</p>
        ${missingHtml(missing)}
      </div>
      <div class="ds-block">
        <p class="eyebrow">Audit trail</p>
        ${auditTrailHtml(project)}
      </div>`;
  }

  /* Renders the collapsed "Details" panel into a container. */
  function renderSignalsPanel(container, project) {
    if (!container) return;
    container.innerHTML =
      `<details class="kn-topic ds-panel">
         <summary>Details — extracted signals, missing values, and audit trail</summary>
         <div class="ds-panel-body">${panelInnerHtml(project)}</div>
       </details>`;
    wirePanel(container, project);
  }

  function wirePanel(container, project) {
    const body = container.querySelector(".ds-panel-body");
    if (!body) return;
    body.querySelectorAll(".ds-overwrite").forEach((btn) =>
      btn.addEventListener("click", () => openOverwriteEditor(btn, container, project)));
  }

  /* ===========================================================
     Change 4 — overwrite editor + auto-re-run
     =========================================================== */
  function openOverwriteEditor(btn, container, project) {
    const field = btn.dataset.field;
    const row = btn.closest("tr");
    if (!row || row.nextElementSibling && row.nextElementSibling.classList.contains("ds-edit-row")) return;
    const id = project.id;
    const cur = (cache[id] && cache[id].signalInputs && cache[id].signalInputs[field]);
    const editor = document.createElement("tr");
    editor.className = "ds-edit-row";
    editor.innerHTML = `<td colspan="4">
      <div class="ds-editor">
        <label class="rationale-label">New value
          <input type="number" step="any" class="ds-edit-value ig-input" value="${esc(cur != null ? cur : "")}" /></label>
        <label class="rationale-label">Reason (required)
          <input type="text" class="ds-edit-reason ig-input" placeholder="Why is this corrected? (recorded to the audit trail)" /></label>
        <div class="dc-actions">
          <button class="btn primary ds-edit-save">Save</button>
          <button class="btn ds-edit-cancel">Cancel</button>
        </div>
        <p class="ds-edit-msg kn-sub" aria-live="polite"></p>
      </div></td>`;
    row.insertAdjacentElement("afterend", editor);

    editor.querySelector(".ds-edit-cancel").addEventListener("click", () => editor.remove());
    editor.querySelector(".ds-edit-save").addEventListener("click", async () => {
      const value = editor.querySelector(".ds-edit-value").value;
      const reason = editor.querySelector(".ds-edit-reason").value.trim();
      const msg = editor.querySelector(".ds-edit-msg");
      if (value === "" || !Number.isFinite(Number(value))) { msg.textContent = "Enter a valid number."; return; }
      if (reason.length < 3) { msg.textContent = "A short reason is required (min 3 characters)."; return; }
      const save = editor.querySelector(".ds-edit-save");
      save.disabled = true;
      msg.textContent = "Saving correction and re-running models…";
      try {
        const resp = await LinStore.overwriteSignal({ id, field, value: Number(value), reason });
        const si = (resp.signalInputs || resp.signals)
          ? mergeComputed(resp)
          : (cache[id] && cache[id].signalInputs) || {};
        const missing = resp.missing || (cache[id] && cache[id].missing) || [];
        const readyToRun = resp.readyToRun != null ? !!resp.readyToRun
          : (Number.isFinite(Number(si.cpi)) && Number.isFinite(Number(si.spi)));
        // preserve extracted periods (overwrite responses don't re-send them)
        const dates = Object.assign({}, (cache[id] && cache[id].dates) || {}, extractDates(resp, si));
        cache[id] = { signalInputs: si, missing, readyToRun, dates };

        // re-run when EITHER index is present (consistent with the extract path)
        const canCompute = hasIndex(si.cpi) || hasIndex(si.spi);
        if (canCompute) await runModels(project, si);
        const fresh = await refreshProject(id);
        // re-render the whole panel (values + audit trail) and the app/ledger
        renderSignalsPanel(container, fresh || project);
        if (window.LinApp) LinApp.refresh();
        if (window.LinDetail && LinApp && LinApp.getSelectedId && LinApp.getSelectedId() === id) {
          // detail page may be open — refresh its ledger/decision via re-render
          LinDetail.render(id);
        }
      } catch (e) {
        msg.textContent = "Overwrite failed: " + (e && e.message ? e.message : "store unreachable") + ".";
        save.disabled = false;
      }
    });
  }

  window.LinSignals = {
    ingestFormHtml, wireIngestForm,
    renderSignalsPanel,
    runModels,
    DOC_TYPES, DOC_TYPE_LABEL
  };
})();
