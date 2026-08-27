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
    // T6 Part 3. THE LEGACY BROWSER INGEST IS RETIRED ON THIS APPLICATION.
    //
    // This derived a project's signals in the browser, and it is where the false Red came from:
    // buildSignals was called without a time series, so it synthesised one from a single metric
    // value and a seed, and that fabricated series tripped the CUSUM detector on healthy work.
    //
    // The server owns this path now. projectupload extracts the documents, projectcompute runs
    // the analytical layer and stores the result, and projectresults reads it back. sim.js is
    // not loaded here, so this cannot run even by accident — the check below turns what would
    // be a ReferenceError into a sentence someone can act on.
    if (!window.LinSim) {
      throw new Error("Signals are computed by the server. Upload the period documents on the "
                      + "project page and run the analysis there.");
    }
    const e = project.signals.evm;
    const cu = project.signals.cusum;
    project.signals = LinSim.buildSignals({
      cpi: e.cpi, spi: e.spi, bac: e.bac, metric: cu.metric, series: cu.series,
      docScore, docSource, docExcerpt, seed: LinSim.hashSeed(project.id)
    });
    await LinStore.saveProject(project);
  }

  async function populateSignals(project, inputs) {
    // T6 Part 3. THE LEGACY BROWSER INGEST IS RETIRED ON THIS APPLICATION.
    //
    // This derived a project's signals in the browser, and it is where the false Red came from:
    // buildSignals was called without a time series, so it synthesised one from a single metric
    // value and a seed, and that fabricated series tripped the CUSUM detector on healthy work.
    //
    // The server owns this path now. projectupload extracts the documents, projectcompute runs
    // the analytical layer and stores the result, and projectresults reads it back. sim.js is
    // not loaded here, so this cannot run even by accident — the check below turns what would
    // be a ReferenceError into a sentence someone can act on.
    if (!window.LinSim) {
      throw new Error("Signals are computed by the server. Upload the period documents on the "
                      + "project page and run the analysis there.");
    }
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
    return LinStore.cachedActive().map((p) => `<option value="${esc(p.id)}">${esc(p.id)}: ${esc(p.name)}</option>`).join("");
  }
  function renderLog() {
    const elLog = document.getElementById("ingest-log");
    if (!elLog) return;
    elLog.innerHTML = ingestLog.length
      ? ingestLog.slice(0, 25).map((e) =>
          `<div class="ig-log-entry"><span class="mod-mono">${esc(window.LinTZ ? LinTZ.format(e.at) : e.at)}</span> ${esc(e.msg)}</div>`).join("")
      : `<p class="pr-empty">No recent activity.</p>`;
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
    // A failed geocode now retains the previous coordinates. Saying "Couldn't locate this
    // address" and nothing else would leave the PM believing the pin they can still see is the
    // one they just typed.
    if (saved.geocodeStale && saved.lat != null && window.linLocationNote) {
      return { ok: false, text: linLocationNote(saved).text };
    }
    if (saved.geocodeError) {
      // the backend message is already human-readable and usually carries its
      // own "refine and save again" instruction — don't repeat it
      const hint = /refine|save again/i.test(saved.geocodeError) ? "" : " Refine the address and save again.";
      return { ok: false, text: "Couldn't locate this address: " + saved.geocodeError + hint };
    }
    if (saved.formattedAddress || saved.lat != null) return { ok: true, text: "Located: " + (saved.formattedAddress || saved.address) };
    return null;
  }

  /* ---------- inline per-row admin accordion (Portfolio list) ----------
     The old standalone Manage page's per-project controls now live inline on
     the Portfolio list rows: clicking a row's "Manage" button opens this
     accordion directly beneath it. One panel open at a time. It carries the
     unified Edit-info fields (number / name / address; sector read-only) PLUS
     the row's admin actions — Populate/Re-upload, Archive, Reset signals.
     The address is the ONLY location field — the backend geocodes it on save
     and the outcome surfaces inline. */
  function findPortfolioRow(id) {
    let row = null;
    document.querySelectorAll("#project-list .list-item").forEach((r) => {
      if (r.getAttribute("data-id") === id) row = r;
    });
    return row;
  }
  function closeInlineManage(exceptLi) {
    document.querySelectorAll("#project-list .pr-admin").forEach((el) => {
      if (el.parentElement !== exceptLi) {
        const b = el.parentElement && el.parentElement.querySelector(".list-item");
        if (b) b.classList.remove("mng-open");
        el.remove();
      }
    });
  }

  // Toggle the inline admin accordion for a project id. Reused by the map's
  // "No address set" deep-link (was: open the Manage page's Edit-info panel).
  //
  // RUN 55, PHASE A. THE PANEL IS NOW MOUNTABLE ON THE PROJECT DETAIL PAGE.
  // Run 54 phase C re-bound Manage to openDetail() and removed Open, which left this panel --
  // and with it Save info, Upload documents, Recompute this project, Reset signals, Archive and
  // Close -- with no entry point at all. The owner's ruling at section 6 of the Run 55 order is
  // that all six move onto the detail page of the project being viewed.
  //
  // THIS IS A MOVE, NOT A REWRITE (section 11.1). The panel is built by THIS function, from the
  // same markup, and every one of the six click handlers below is the same code it was on the
  // portfolio row. The only thing that changes is the PARENT ELEMENT: pass `hostEl` and the box
  // is appended there instead of to the row's <li>. When `hostEl` is absent the behaviour is
  // exactly what it was -- find the row, toggle, one-open-at-a-time -- so the row path is byte
  // -for-byte the same journey it always was.
  //
  // "Close" keeps its meaning: it removes the panel. On the row it was reopened by clicking
  // Manage; on the detail page it is reopened by clicking Manage again from the portfolio, which
  // re-renders the detail page. The SAME control undoes it, so no new control is introduced.
  /* ---------- RUN 56, PHASE B. THE CONFIRMATION BEFORE A DESTRUCTIVE ADMIN CONTROL ----------
     THE PATTERN IS REUSED, NOT INVENTED. The application already confirms in two shapes:

       1. `window.confirm(...)`  -- app.js:2485 ("Recompute every project") and
          decision-ui.js:488 ("Commit your preliminary judgment?").
       2. `LinUI.openModal(...)` -- admin-ops.js `openDeleteProjectModal` and this file's own
          `openDeleteArchivedModal`, both for destructive PROJECT-SCOPED actions.

     SHAPE 2 IS THE ONE REUSED HERE, and the reason is written down in the repository in four
     places already: `window.confirm` RETURNS FALSE in this container and in any dialog
     suppressing browser (ingest.js openDeleteArchivedModal, admin-ops.js openDeleteProjectModal,
     workspace.js renderFailedUploads, detail.js's "Generate signals for every period"), and, in
     workspace.js's words, "an action behind that is an action nobody can take". Gating Archive
     on `window.confirm` would therefore make Archive IMPOSSIBLE TO PERFORM here, which would
     change what the confirmed action does. It is not used.

     NO CONTROL IS ADDED. The dialog carries ONE button, the confirm, exactly as
     `openDeleteArchivedModal` does; cancelling is the modal's own x, Escape or backdrop, which
     `LinUI.openModal` already provides to every dialog in the application. Nothing is added to
     the page: the dialog exists only while it is open.

     CANCELLING DOES NOTHING AT ALL. `onConfirm` is called from the confirm button's listener and
     from nowhere else. There is no `onClose` handler, no navigation and no state change on any
     dismissal path, so dismissing the dialog cannot reach the action.

     NO TYPED CONFIRMATION. That heavier shape is the application's answer to PERMANENT DELETE.
     Neither of these two actions deletes anything: Archive is reversible from the Archived
     dialog's Restore, and Reset signals keeps the documents. Reusing the typed shape here would
     overstate what the action does. */
  function confirmDestructive(opts) {
    if (!(window.LinUI && LinUI.openModal)) return;
    LinUI.openModal({
      title: opts.title,
      mount: (body, close) => {
        body.innerHTML =
          `<p class="login-error" style="display:block">${esc(opts.detail)}</p>` +
          `<button type="button" class="btn small danger" data-confirm-go>` +
            `${esc(opts.confirmLabel)}</button>`;
        body.querySelector("[data-confirm-go]").addEventListener("click", () => {
          close();
          opts.onConfirm();
        });
      }
    });
  }

  function openInlineManage(id, hostEl) {
    const rowBtn = hostEl ? null : findPortfolioRow(id);
    const li = hostEl || (rowBtn && rowBtn.closest("li"));
    if (!li) return;
    // toggle: second click (or Manage again) collapses it
    const open = li.querySelector(".pr-admin");
    if (open) { open.remove(); if (rowBtn) rowBtn.classList.remove("mng-open"); return; }
    if (!hostEl) closeInlineManage(li);    // accordion: one open at a time
    if (rowBtn) rowBtn.classList.add("mng-open");

    const cached = LinStore.getCached(id) || {};
    const populated = hasSignals(cached);
    const box = document.createElement("div");
    box.className = "pr-admin pr-editinfo";
    box.innerHTML =
      `<div class="pr-editinfo-grid">
         <label class="rationale-label">Project number / code
           <input type="text" class="pe-id ig-input" maxlength="40" placeholder="e.g. AP-2026-014" /></label>
         <label class="rationale-label">Project name
           <input type="text" class="pe-name ig-input" maxlength="80" /></label>
         <label class="rationale-label">Project type / sector (drives which modules apply)
           <select class="pe-sector ig-input">
             <option value="design">Design</option>
             <option value="construction">Construction</option>
             <option value="hybrid">Hybrid</option>
           </select></label>
         <label class="rationale-label pr-editinfo-addr">Address (optional, located automatically on save)
           <input type="text" class="pe-address ig-input" maxlength="160" placeholder="e.g. Terminal B, Austin-Bergstrom Intl Airport" /></label>
       </div>
       <div class="dc-actions">
         <button class="btn primary small pe-save">Save info</button>
         ${/* RUN 56, PHASE A. NOT RENDERED ON THE DETAIL PAGE. The detail page already carries
              .detail-upload, labelled "Upload documents", which calls the SAME function with the
              SAME project id (detail.js data-upload -> LinIngest.openUploadModal). Run 55 phase A
              moved this panel onto that page and so put a SECOND control with the same label and
              the same action beside it. The owner's Run 56 ruling is that .detail-upload survives
              and this one is removed FROM THE DETAIL PAGE ONLY. hostEl is supplied only by the
              hosted (detail-page) path, so the row path -- if any caller ever supplies no host
              again -- still builds the button exactly as it always did. NOTHING ELSE CHANGES:
              the listener below is guarded, not deleted. */""}
         ${hostEl ? "" : `<button class="btn small pe-populate">Upload documents</button>`}
         <button class="btn small pe-recompute"${populated ? "" : " disabled title=\"No signals to recompute: upload documents first\""}>Recompute this project</button>
         <button class="btn small pe-reset">Reset signals</button>
         <button class="btn small pe-archive">Archive</button>
         <button class="btn small pe-cancel">Close</button>
       </div>
       <p class="pe-msg kn-sub" aria-live="polite"></p>`;
    li.appendChild(box);
    box.querySelector(".pe-id").value = id;
    box.querySelector(".pe-name").value = cached.name || "";
    const origSector = (window.normalizeSector ? window.normalizeSector(cached.sector) : String(cached.sector || "hybrid").toLowerCase());
    box.querySelector(".pe-sector").value = origSector;
    box.querySelector(".pe-address").value = cached.address || "";
    // Changing sector invalidates sector-gated module results — warn inline.
    box.querySelector(".pe-sector").addEventListener("change", (e) => {
      if (e.target.value !== origSector) {
        msg.classList.remove("pe-msg-ok"); msg.classList.add("pe-msg-error");
        msg.textContent = "Sector changed: save, then recompute signals to update module applicability.";
      }
    });
    if (cached.formattedAddress && cached.lat != null) {
      box.querySelector(".pe-msg").textContent = "Located: " + cached.formattedAddress;
    }
    const msg = box.querySelector(".pe-msg");

    const close = () => { box.remove(); if (rowBtn) rowBtn.classList.remove("mng-open"); };
    box.querySelector(".pe-cancel").addEventListener("click", close);
    box.addEventListener("keydown", (e) => { if (e.key === "Escape") { e.stopPropagation(); close(); } });

    // Populate / Re-upload → open the Upload modal with this project preselected.
    const populateBtn = box.querySelector(".pe-populate");
    if (populateBtn) populateBtn.addEventListener("click", () => {
      openUploadModal(id);
    });

    // Recompute this project — surgical repair: local re-run for THIS project
    // plus one Portfolio Health refresh. No AI calls, no re-extraction.
    const recomputeBtn = box.querySelector(".pe-recompute");
    if (recomputeBtn) recomputeBtn.addEventListener("click", async () => {
      if (!window.LinSignals || !window.LinStore) return;
      recomputeBtn.disabled = true;
      msg.classList.remove("pe-msg-error", "pe-msg-ok");
      msg.textContent = "Recomputing " + id + "…";
      try {
        const full = await LinStore.getProject(id);
        if (!full || !full.signalInputs) throw new Error("no stored signal inputs to recompute from");
        const si = LinSignals.deriveExtendedFields(LinSignals.resolveSimInputs(full));
        const hasCpi = si.cpi != null && Number.isFinite(Number(si.cpi)) && Number(si.cpi) > 0;
        const hasSpi = si.spi != null && Number.isFinite(Number(si.spi)) && Number(si.spi) > 0;
        if (!hasCpi && !hasSpi) throw new Error("no CPI/SPI on file, upload a document first");
        await LinSignals.runModels(full, si);   // also refreshes Portfolio Health once
        if (window.LinApp && LinApp.clearSectorDirty) LinApp.clearSectorDirty(id);
        logEvent(`RECOMPUTED signals for ${id}.`);
        if (window.LinApp) LinApp.refresh();
        msg.textContent = "Recomputed " + id + " and refreshed Portfolio Health.";
        msg.classList.add("pe-msg-ok");
      } catch (e) {
        msg.textContent = "Couldn't recompute: " + ((e && e.message) || "store unreachable") + ".";
        msg.classList.add("pe-msg-error");
      } finally {
        recomputeBtn.disabled = false;
      }
    });

    // Archive
    // RUN 56, PHASE B. The confirmation is a GATE IN FRONT of the action. The action itself is
    // the SAME BODY it has always had, moved into doArchive() and called with nothing added,
    // nothing removed and nothing reordered, so confirming does exactly what the control did
    // before. The project is NAMED in both the title and the button.
    const doArchive = async () => {
      try {
        await LinStore.archiveProject(id);
        logEvent(`ARCHIVED ${id}.`);
        if (window.LinApp) LinApp.refresh();
        renderPortfolioAdmin();
      } catch (e) { LinStore.banner("Couldn't archive: store unreachable. Retry.", "warn"); }
    };
    box.querySelector(".pe-archive").addEventListener("click", () => {
      confirmDestructive({
        title: "Archive " + id,
        detail: "This moves " + id + " out of the active portfolio. Its documents and its "
              + "computed results are kept, and it can be brought back from the Archived "
              + "dialog. Nothing is deleted and no other project is touched.",
        confirmLabel: "Archive " + id,
        onConfirm: doArchive
      });
    });

    // Reset signals → clears extraction back to "Awaiting ingest".
    // RUN 56, PHASE B. Same shape as Archive above: the confirmation is a gate, doReset() is the
    // handler body unchanged, and the project is NAMED in the title and on the button. The
    // wording of the detail is the application's OWN wording for this action, taken verbatim
    // from the title attribute detail.js CARRIED on `.detail-reset` before Run 57 phase A removed
    // that control, so the surviving control describes itself in the application's own words.
    // RUN 57, PHASE A. THE MERGED RESET HANDLER -- THE UNION OF THE TWO CONTROLS THAT CLEARED
    // STORED SIGNALS. Both handler bodies were measured again at the explicit commit 50dfb40 and
    // NEITHER was a superset of the other, exactly as Run 56 measured at e13b4f1. The owner's
    // Run 57 ruling is that the two bodies MERGE INTO ONE control doing the union, and the other
    // control is removed. This body is that union; `.detail-reset` and its markup, its handler
    // and its dead CSS rule are gone.
    //
    // WHY `.pe-reset` IS THE SURVIVOR. Every behaviour unique to `.detail-reset` is reachable
    // from this file through interfaces that are ALREADY public -- window.LinResults,
    // window.LIN_PROJECTS, LinStore.getProject/getCached, and detail.js's exported
    // LinDetail.render -- whereas two behaviours unique to THIS handler, logEvent() and
    // confirmDestructive(), are module-private to ingest.js and would have had to be newly
    // EXPORTED to build the same union inside detail.js. Merging here adds nothing to any
    // module's public surface. It also leaves Run 56's confirmation exactly where Run 56 put it.
    //
    // THE ORDER IS BY DEPENDENCY, NOT BY CONCATENATION:
    //   1. the server is reset FIRST; everything after it reconciles clients to that truth;
    //   2. caches are dropped BEFORE any re-fetch or re-render, or the re-render repopulates
    //      from the stale copies. LinResults.clear() is the line whose absence left a cleared
    //      project still drawing 41 modules with a current result and an Amber project rollup in
    //      the same session, from a row the server had already retired;
    //   3. re-fetch: LinStore.load() rebuilds the store's list FIRST, then getProject(id) takes
    //      the authoritative single record into LIN_PROJECTS -- the other order would let load()
    //      overwrite the record just fetched;
    //   4. the in-memory record is forced to awaiting-ingest AFTER the re-fetch, or the fetch
    //      would restore the very fields that mutation nulls;
    //   5. logEvent() ONCE, after the state change succeeded and before the re-renders, so the
    //      activity log renders with the entry already in it;
    //   6. re-render broadest to narrowest: LinApp.refresh(), renderPortfolioAdmin(), and
    //      LinDetail.render(id) LAST, because it rebuilds the host that contains this button.
    const doReset = async () => {
      const btn = box.querySelector(".pe-reset");
      btn.disabled = true;
      msg.classList.remove("pe-msg-error", "pe-msg-ok");
      msg.textContent = "Resetting signals…";
      try {
        await LinStore.resetSignals(id);
        if (window.LinSignals && LinSignals.clearCache) LinSignals.clearCache(id);
        // FROM `.detail-reset`: drop the derived-results cache. NOTHING is recomputed here; this
        // discards a copy, it does not derive a replacement.
        if (window.LinResults && LinResults.clear) LinResults.clear();
        await LinStore.load();
        // FROM `.detail-reset`: re-fetch the (now-cleared) server copy into LIN_PROJECTS; fall
        // back to the cached copy on failure, exactly as the removed handler did.
        try {
          const fresh = await LinStore.getProject(id);
          if (fresh && window.LIN_PROJECTS) {
            const i = LIN_PROJECTS.findIndex((x) => x.id === id);
            if (i >= 0) LIN_PROJECTS[i] = fresh;
          }
        } catch (e) { /* keep the cached copy on fetch failure */ }
        // FROM `.detail-reset`: force the in-memory copy to a true "Awaiting ingest" state, so
        // the screen is correct even against an older backend build. `p.events` is deliberately
        // NOT blanked -- Run 22 proved that mask made the live page less truthful than the
        // reloaded one -- but history IS cleared, because it feeds CUSUM.
        const p = LinStore.getCached(id);
        if (p) {
          p.signals = null; p.signalInputs = null; p.simulationSignals = null;
          p.history = [];
          ["documents", "uploadedDocuments", "docs"].forEach((k) => {
            if (Array.isArray(p[k])) p[k] = [];
          });
          p.status = null; p.reportingPeriod = null; p.derivedState = null;
        }
        logEvent(`RESET signals for ${id}.`);
        if (window.LinApp) LinApp.refresh();
        renderPortfolioAdmin();
        // FROM `.detail-reset`: re-render the detail page, which then reads "awaiting ingest".
        // GUARDED ON hostEl, which is supplied only by the hosted (detail-page) path: on a
        // portfolio row there is no detail page to re-render and `.detail-reset` never existed
        // there, so this is the union on the surface each original actually lived on.
        if (hostEl && window.LinDetail && LinDetail.render) LinDetail.render(id);
      } catch (e) {
        // The union of both failure paths: re-enable the control and report the failure in the
        // aria-live region. The survivor's own wording is kept.
        msg.textContent = "Couldn't reset: " + ((e && e.message) || "store unreachable") + ".";
        msg.classList.add("pe-msg-error");
        btn.disabled = false;
      }
    };
    box.querySelector(".pe-reset").addEventListener("click", () => {
      confirmDestructive({
        title: "Reset signals for " + id,
        detail: "This clears " + id + "'s stored signal values so its documents can be read "
              + "again. It does not delete documents and it does not touch other projects.",
        confirmLabel: "Reset signals for " + id,
        onConfirm: doReset
      });
    });

    // Save info (number / name / address) with inline geocode feedback.
    box.querySelector(".pe-save").addEventListener("click", async () => {
      msg.classList.remove("pe-msg-error", "pe-msg-ok");
      const newId = box.querySelector(".pe-id").value.trim();
      const name = box.querySelector(".pe-name").value.trim();
      const address = box.querySelector(".pe-address").value.trim();
      const sector = box.querySelector(".pe-sector").value;
      const sectorChanged = sector !== origSector;
      if (newId !== id) {
        const idErr = validateProjectNumber(newId, id);
        if (idErr) { msg.textContent = idErr; return; }
      }
      if (name.length < 3) { msg.textContent = "Enter a project name (min 3 characters)."; return; }
      const save = box.querySelector(".pe-save");
      save.disabled = true;
      msg.textContent = address ? "Saving, locating address…" : "Saving project info…";
      try {
        const full = await LinStore.getProject(id);
        if (!full || full.slim) throw new Error("couldn't load the full project record");
        full.name = name;
        full.address = address || null;
        full.sector = sector;
        const saved = await LinStore.saveProject(full);
        // Sector change invalidates sector-gated modules — flag the row until recomputed.
        if (sectorChanged && window.LinApp && LinApp.markSectorDirty) LinApp.markSectorDirty(newId !== id ? newId : id);
        if (newId !== id) {
          await LinStore.setProjectNumber(id, newId);
          if (window.LinApp && LinApp.renameSelection) LinApp.renameSelection(id, newId);
          if (window.LinSignals && LinSignals.clearCache) LinSignals.clearCache(id);
        }
        logEvent(`EDITED project info for ${newId}${newId !== id ? ` (was ${id})` : ""}: name/address updated.`);
        await LinStore.load();
        if (window.LinApp) LinApp.refresh();
        renderPortfolioAdmin();
        // re-open the (rebuilt) row's panel to surface the geocode outcome
        const outcome = address ? geocodeOutcome(saved) : null;
        const finalId = newId !== id ? newId : id;
        openInlineManage(finalId, hostEl);
        if (outcome) {
          const li2 = hostEl || findPortfolioRow(finalId);
          const box2 = hostEl ? hostEl.querySelector(".pr-admin")
                              : (li2 && li2.closest("li").querySelector(".pr-admin"));
          const msg2 = box2 && box2.querySelector(".pe-msg");
          if (msg2) {
            msg2.textContent = outcome.text;
            msg2.classList.add(outcome.ok ? "pe-msg-ok" : "pe-msg-error");
            box2.scrollIntoView({ block: "center" });
          }
        }
      } catch (e) {
        msg.textContent = "Couldn't save: " + ((e && e.message) || "store unreachable") + ".";
        msg.classList.add("pe-msg-error");
        save.disabled = false;
      }
    });
    // RUN 55, PHASE A -- THE ONE DEVIATION, AND IT IS REPORTED AS ONE. On the portfolio row the
    // panel opened in response to a CLICK, so taking focus and scrolling the row into view was
    // the right answer. On the detail page the panel is mounted by render(), which runs on every
    // navigation to the page; taking focus and scrolling there would drag the reader past the
    // project heading every time they opened a project. The two lines are therefore kept for the
    // row path and skipped for the hosted path. NO HANDLER AND NO ACTION CHANGES.
    if (!hostEl) {
      box.querySelector(".pe-id").focus();
      box.scrollIntoView({ block: "nearest" });
    }
    return box;
  }

  /* ---------- Portfolio admin (Create / Upload / Archived / Activity) ----------
     All four are centered DIALOGS (LinUI.openModal), launched from the dock
     actions fly-out. Per-project admin lives inline on each Portfolio list row
     (openInlineManage). */
  /* renderPortfolioAdmin — the admin surfaces are now dialogs (Create, Upload,
     Archived, Activity) launched from the dock actions fly-out. Nothing renders
     into #portfolio-admin anymore; this only refreshes the fly-out's Archived
     badge count. Kept as the name app.js + the internal flows call. */
  function renderPortfolioAdmin() {
    const badge = document.getElementById("tool-archived-badge");
    if (!badge) return;
    const n = LinStore.cachedArchived().length;
    if (n > 0) { badge.textContent = String(n); badge.hidden = false; }
    else { badge.textContent = ""; badge.hidden = true; }
  }

  /* ---------- CREATE — modal dialog (LinUI.openModal) ---------- */
  function openCreateModal() {
    if (!window.LinUI) return;
    LinUI.openModal({
      title: "New Project",
      mount: (body, close) => {
        body.innerHTML =
          `<p class="kn-sub">Assign your own project number, then a name and sector. Upload documents to get started.</p>
           <label class="rationale-label" for="np-id">Project number / code <span class="req">(required)</span></label>
           <input id="np-id" class="ig-input" maxlength="40" placeholder="e.g. AP-2026-014" />
           <label class="rationale-label" for="np-name">Project name</label>
           <input id="np-name" class="ig-input" maxlength="80" placeholder="e.g. Terminal B Expansion" />
           <label class="rationale-label" for="np-address">Address (optional, located automatically on save)</label>
           <input id="np-address" class="ig-input" maxlength="160" placeholder="e.g. Terminal B, Austin-Bergstrom Intl Airport" />
           <label class="rationale-label" for="np-sector">Sector</label>
           <select id="np-sector" class="ig-input">
             <option value="design">Design</option>
             <option value="construction">Construction</option>
             <option value="hybrid">Hybrid</option>
           </select>
           <div class="dc-actions"><button id="np-create" class="btn primary">Create project</button></div>
           <p id="np-msg" class="kn-sub" aria-live="polite"></p>`;
        body.querySelector("#np-create").addEventListener("click", async () => {
          const id = body.querySelector("#np-id").value.trim();
          const name = body.querySelector("#np-name").value.trim();
          const sector = body.querySelector("#np-sector").value;
          const address = body.querySelector("#np-address").value.trim();
          const msg = body.querySelector("#np-msg");
          msg.classList.remove("pe-msg-error");
          const idErr = validateProjectNumber(id);
          if (idErr) { msg.textContent = idErr; return; }
          if (name.length < 3) { msg.textContent = "Enter a project name (min 3 characters)."; return; }
          const btn = body.querySelector("#np-create"); btn.disabled = true;
          msg.textContent = address ? "Creating project, locating address…" : "Creating project in the store…";
          try {
            const p = await LinStore.createProject({ id, name, sector });
            let outcome = null;
            if (address) { p.address = address; const saved = await LinStore.saveProject(p); outcome = geocodeOutcome(saved); }
            logEvent(`Created EMPTY project ${p.id}: ${name} (${SECTOR_LABEL[sector] || sector}); awaiting analysis.`);
            if (window.LinApp) LinApp.refresh();
            renderPortfolioAdmin();
            close();
            if (window.LinUI) LinUI.toast(`Created ${p.id}. ` + (outcome ? outcome.text : "Populate its signals to run the models."), !(outcome && !outcome.ok));
          } catch (e) {
            btn.disabled = false;
            msg.textContent = "Couldn't create the project: " + ((e && e.message) || "store unreachable") + ".";
            msg.classList.add("pe-msg-error");
          }
        });
      }
    });
  }

  /* ---------- UPLOAD — modal dialog (bulk dropzone + selector) ----------
     preselectId (optional) pre-selects that project in the dropzone selector —
     used by the inline-row Populate/Re-upload button. The academic-use
     disclaimer rides along inside LinSignals.dropzoneHtml(). */
  function openUploadModal(preselectId) {
    if (!window.LinUI) return;
    let busy = false;
    const locked = !!preselectId;
    const projName = preselectId ? ((LinStore.getCached(preselectId) || {}).name || "") : "";
    LinUI.openModal({
      title: locked ? "Upload Documents" : "Upload Documents",
      // Wide: the document-type reference and the per-file results list are both cramped in
      // the default 480px modal — the types wrap across many rows and each result truncates to
      // a narrow strip. See .app-modal-wide in radar.css; it still collapses to full width on a
      // phone viewport exactly like every other modal.
      wide: true,
      // Non-dismissable while a batch runs: the backdrop is inert, Escape / ×
      // prompt "leave anyway?". Once the summary shows (busy=false) closing is free.
      canClose: () => !busy,
      onBlockedClose: (doClose, source) => {
        if (source === "backdrop") return;                 // backdrop never closes mid-upload
        if (window.confirm("Uploads in progress, leave anyway?")) doClose();
      },
      mount: (body, close) => {
        body.innerHTML =
          `<p class="kn-sub">${locked ? `Uploading to <strong>${esc(preselectId)}${projName && projName !== preselectId ? " · " + esc(projName) : ""}</strong>. ` : ""}Drop one or more documents below. The platform identifies each document type automatically and extracts the signals, no need to label them first.</p>
           <div class="up-progress" hidden>
             <div class="up-robot"></div>
           </div>
           <div id="signals-panel">
             ${LinSignals.dropzoneHtml(preselectId || null)}
             <div id="signals-detail" class="ds-detail-wrap"></div>
           </div>
           <div class="up-summary" hidden></div>`;
        const panelWrap = body.querySelector("#signals-panel");
        const prog = body.querySelector(".up-progress");
        const robotHost = body.querySelector(".up-robot");
        const summaryEl = body.querySelector(".up-summary");
        // 'extracting' working-robot at md size, driven by the REAL n-of-N batch
        // events (never a faked bar). Torn down on 'done' (before the summary
        // shows) so it is never orphaned.
        let robot = null;
        const destroyRobot = () => { if (robot) { try { robot.destroy(); } catch (e) {} robot = null; } };
        LinSignals.wireDropzone(panelWrap, (id) => {
          const panel = body.querySelector("#signals-detail");
          if (panel) LinSignals.renderSignalsPanel(panel, LinStore.getCached(id));
        }, (ev) => {
          if (ev.type === "start") {
            busy = true; prog.hidden = false;
            destroyRobot();
            robot = window.LinWorkingRobot
              ? LinWorkingRobot.mount(robotHost, {
                  variant: "extracting", size: "md",
                  message: "Reading " + ev.total + " document" + (ev.total === 1 ? "" : "s") + "…",
                  progress: 0
                })
              : null;
          } else if (ev.type === "file") {
            // 'uploading' → reading the file; 'extracting' → pulling figures out.
            const msg = ev.state === "extracting" ? "Extracting figures from " + ev.name : "Reading " + ev.name + "…";
            if (robot) robot.update({ message: msg });
          } else if (ev.type === "progress") {
            if (robot) {
              robot.update({
                message: ev.done + " of " + ev.total + " document" + (ev.total === 1 ? "" : "s") + " complete",
                progress: ev.total ? ev.done / ev.total : null
              });
              robot.tick();                     // a check pops as each file lands
            }
          } else if (ev.type === "done") {
            busy = false;
            if (robot) { robot.update({ message: "Extraction complete", progress: 1 }); robot.tick(); }
            // Keep the robot visible long enough for the completion tick to play,
            // then remove it and its container together (no orphan, no dangling box).
            setTimeout(() => { destroyRobot(); prog.hidden = true; }, 700);
            panelWrap.hidden = true;
            const ok = ev.summary.filter((s) => s.status === "done");
            const bad = ev.summary.filter((s) => s.status !== "done");
            summaryEl.hidden = false;
            summaryEl.innerHTML =
              `<h3 class="up-summary-title">Upload complete</h3>` +
              `<p class="kn-sub">${ok.length} file${ok.length === 1 ? "" : "s"} uploaded${bad.length ? `, ${bad.length} failed` : ""}.</p>` +
              `<ul class="up-summary-list">` +
                ev.summary.map((s) => `<li class="${s.status === "done" ? "up-ok" : "up-fail"}"><span class="up-file">${esc(s.name)}</span> ` +
                  (s.status === "done"
                    ? `<span class="up-detail">${s.fields || 0} field${(s.fields || 0) === 1 ? "" : "s"} extracted</span>`
                    : `<span class="up-detail">${esc(s.error || "failed")}</span>`) + `</li>`).join("") +
              `</ul>` +
              `<div class="dc-actions"><button class="btn primary small up-close">Close</button></div>`;
            summaryEl.querySelector(".up-close").addEventListener("click", () => close());
            try { if (window.LinApp) LinApp.refresh(); } catch (e) {}
          }
        });
      }
    });
  }

  /* ---------- ARCHIVED — centered dialog (Restore per row) ----------
     Same modal component as New Project / Upload (LinUI.openModal). Restoring
     UPDATES THE LIST IN PLACE (a visitor may restore several in a row) rather
     than closing on the first — each restore refreshes the portfolio list + map
     and shows an inline toast; the dialog closes on ×, Escape, or backdrop. */
  function openArchivedModal() {
    if (!window.LinUI) return;
    LinUI.openModal({
      title: "Archived Projects",
      mount: (body, close) => {
        body.innerHTML = `<div class="app-modal-scroll"><div id="archived-list"><p class="pr-empty">Loading archived projects…</p></div></div>`;
        loadArchivedList(body);
      }
    });
  }

  // Delete is admin-only. The button only appears for an admin (a rendering convenience); the
  // real refusal is server-side in a_admindeleteproject (_require_admin) — a non-admin calling
  // the action directly is refused regardless of what this file renders. See
  // REPORT_2026-08-05_archived-delete-control.md.
  function isAdmin() {
    const view = window.LinAuth && LinAuth.currentView ? LinAuth.currentView() : null;
    return !!view && view.role === "ResearchAdmin";
  }

  async function loadArchivedList(scope) {
    const box = scope.querySelector("#archived-list");
    if (!box) return;
    let archived = [];
    try { archived = await LinStore.listArchived(); }
    catch (e) { box.innerHTML = `<p class="pr-empty">Couldn't load archived projects. Retry.</p>`; return; }
    const dateOf = (p) => {
      const d = p.archivedAt || p.archivedDate || p.updatedAt || p.modified || p.date || null;
      return d ? (window.LinTZ ? LinTZ.format(d) : String(d)) : "not recorded";
    };
    const admin = isAdmin();
    box.innerHTML = archived.length
      ? archived.map((p) =>
          `<div class="pr-row"><span class="pr-code">${esc(p.id)}</span>` +
          `<span class="pr-name">${esc(p.name)} <span class="kn-sub">· ${esc(SECTOR_LABEL[p.sector] || p.sector)} · archived ${esc(dateOf(p))}</span></span>` +
          `<button class="btn small" data-restore="${esc(p.id)}">Restore</button>` +
          (admin ? `<button class="btn small danger" data-delete="${esc(p.id)}" data-name="${esc(p.name)}">Delete</button>` : "<span></span>") +
          `</div>`).join("")
      : `<p class="pr-empty">No archived projects.</p>`;
    box.querySelectorAll("[data-restore]").forEach((b) =>
      b.addEventListener("click", async () => {
        const id = b.dataset.restore;
        b.disabled = true;
        try {
          await LinStore.restoreProject(id);
          logEvent(`RESTORED ${id}.`);
          if (window.LinApp) LinApp.refresh();     // refresh portfolio list + map
          renderPortfolioAdmin();                  // refresh the Archived count badge
          loadArchivedList(scope);                 // update the dialog list in place
          if (window.LinUI) LinUI.toast(`Restored ${id} to the active portfolio.`);
        } catch (e) {
          b.disabled = false;
          LinStore.banner("Couldn't restore: store unreachable. Retry.", "warn");
        }
      }));
    box.querySelectorAll("[data-delete]").forEach((b) =>
      b.addEventListener("click", () => openDeleteArchivedModal(b.dataset.delete, b.dataset.name, scope)));
  }

  // Typed confirmation, same shape as admin-ops.js's project-delete control — the operator types
  // the project id and the control stays disabled until it matches. Deliberately not gated on
  // window.confirm, which returns false in this container and in any dialog-suppressing browser.
  function openDeleteArchivedModal(id, name, listScope) {
    if (!window.LinUI || !LinUI.openModal) return;
    LinUI.openModal({
      title: `Delete ${name || id} permanently`,
      mount: (body, close) => {
        body.innerHTML =
          `<p class="login-error" style="display:block">This removes the project for every PM ` +
            `and Observer on it, not just one person's access. Its documents, computed results, ` +
            `observations, membership and uploads are removed with it. It cannot be undone.</p>` +
          `<label class="login-field-label">Type <strong>${esc(id)}</strong> to confirm</label>` +
          `<input type="text" id="archived-delete-confirm-input" class="ig-input">` +
          `<p id="archived-delete-error" class="login-error" role="alert" style="display:none;"></p>` +
          `<button type="button" class="btn small danger" id="archived-delete-submit" disabled>` +
            `Delete permanently</button>`;
        const input = body.querySelector("#archived-delete-confirm-input");
        const submitBtn = body.querySelector("#archived-delete-submit");
        input.addEventListener("input", () => { submitBtn.disabled = input.value.trim() !== id; });
        submitBtn.addEventListener("click", async () => {
          const innerErr = body.querySelector("#archived-delete-error");
          innerErr.style.display = "none";
          submitBtn.disabled = true;
          try {
            const resp = await LinStore.deleteProject(id);
            if (!resp || resp.ok !== true) {
              innerErr.textContent = (resp && resp.error) || "Could not delete this project.";
              innerErr.style.display = "block";
              submitBtn.disabled = false;
              return;
            }
            logEvent(`DELETED ${id}.`);
            if (window.LinUI) LinUI.toast("Deleted", true);
            close();
            if (window.LinApp) LinApp.refresh();
            renderPortfolioAdmin();
            loadArchivedList(listScope);
          } catch (e) {
            innerErr.textContent = "Could not delete this project.";
            innerErr.style.display = "block";
            submitBtn.disabled = false;
          }
        });
      }
    });
  }

  /* ---------- ACTIVITY — centered dialog (Recent Activity log) ---------- */
  function openActivityModal() {
    if (!window.LinUI) return;
    LinUI.openModal({
      title: "Recent Activity",
      mount: (body) => { body.innerHTML = `<div class="app-modal-scroll"><div id="ingest-log"></div></div>`; renderLog(); }
    });
  }

  /* ---------- RUN 71. DOCUMENT CONTROL — withdraw documents from a period ----------

     WHY IT LIVES IN ingest.js AND NOT IN detail.js. It needs `confirmDestructive()`, which is
     module-private here, and it is a document-lifecycle action beside the upload modal it
     undoes. Run 57 settled the same question the same way: build where the private helpers
     already are rather than newly export them. detail.js carries the BUTTON and calls
     `LinIngest.openDocumentControl(id)` — exactly the shape `.detail-upload` already uses to
     reach `LinIngest.openUploadModal(id)`.

     NO SECOND RECOMPUTE CONTROL. §2 item 5 asks for a recalculate button that recomputes the
     project on demand. The detail page already carries one — "Generate signals for every
     period" (`.detail-compute-all` -> `projectcomputeall` -> `projectcompute` per period),
     which recomputes SERVER-SIDE from the period's live document set and reports what moved.
     That is what item 5 describes, so this dialog does NOT add a recompute button. It NAMES
     that control in its own words and leaves the press to the owner, which is also ruling 3:
     archiving stages the withdrawal, recalculating applies it.

     WHAT IT SHOWS. A period dropdown listing only the periods that HOLD DOCUMENTS, the chosen
     period's live documents each with a checkbox and the fields it is currently supplying, the
     documents already archived for that period, and the archive record read back out of the
     audit trail. All four come from ONE read (`projectdocumentcontrol`), which writes nothing.

     THE CONFIRMATION IS `confirmDestructive`, the application's existing primitive, for the
     reason Run 56 wrote down: `window.confirm` returns false in this container, so an action
     behind it is an action nobody can take. The sentence it shows names the COUNT and the
     PERIOD, and the SAME STRING is sent to the server and recorded in the audit row, so the
     record can answer "what did the confirmation say" with the text the person actually read.
     Cancelling is the modal's own x, Escape or backdrop; there is no onClose path to the
     action, so dismissing cannot archive anything. */
  function openDocumentControl(id) {
    if (!(window.LinUI && LinUI.openModal && window.LinStore && LinStore.postWithTimeout)) return;
    LinUI.openModal({
      title: "Document control — " + id,
      wide: true,
      mount: (body) => {
        body.innerHTML =
          '<div class="app-modal-scroll dc-doccontrol">' +
            '<p class="kn-sub dc-dc-intro">Withdraw documents from a reporting period. ' +
            'Archiving keeps the document and its bytes and removes its extracted fields from ' +
            "this project's live document set. The stored figures do not change until you " +
            'press <strong>Generate signals for every period</strong> on this page.</p>' +
            '<label class="rationale-label">Reporting period' +
              '<select class="ig-input dc-dc-period"><option value="">Loading…</option></select>' +
            '</label>' +
            '<div class="dc-dc-list"></div>' +
            '<div class="dc-actions">' +
              '<button type="button" class="btn small danger dc-dc-archive" disabled>' +
                'Archive selected documents</button>' +
            '</div>' +
            '<p class="dc-dc-msg kn-sub" aria-live="polite"></p>' +
            '<div class="dc-dc-record"></div>' +
          '</div>';
        const sel = body.querySelector(".dc-dc-period");
        const list = body.querySelector(".dc-dc-list");
        const go = body.querySelector(".dc-dc-archive");
        const msg = body.querySelector(".dc-dc-msg");
        const rec = body.querySelector(".dc-dc-record");
        let state = { periods: [], record: [] };

        function ticked() {
          return Array.from(list.querySelectorAll(".dc-dc-tick:checked"))
                      .map((c) => c.dataset.docId);
        }
        function syncButton() {
          const n = ticked().length;
          go.disabled = n === 0;
          go.textContent = n === 0 ? "Archive selected documents"
                                   : "Archive " + n + " document" + (n === 1 ? "" : "s");
        }
        function current() {
          const p = Number(sel.value);
          return state.periods.filter((x) => Number(x.period) === p)[0] || null;
        }
        function paintList() {
          const per = current();
          if (!per) { list.innerHTML = '<p class="kn-sub">No period selected.</p>'; syncButton(); return; }
          const live = per.documents || [];
          const arch = per.archived || [];
          list.innerHTML =
            '<p class="kn-sub dc-dc-count">' + live.length + ' live document' +
              (live.length === 1 ? "" : "s") + " in period " + per.period + ".</p>" +
            (live.length
              ? '<ul class="dc-dc-docs">' + live.map((d) =>
                  '<li><label><input type="checkbox" class="dc-dc-tick" data-doc-id="' +
                  esc(d.document_id) + '" /> <span class="mod-mono">' + esc(d.filename) +
                  '</span> <span class="kn-sub">' + esc(d.doc_type) + '</span></label>' +
                  '<span class="kn-sub dc-dc-fields">' +
                  (d.fields && d.fields.length
                    ? "supplies: " + d.fields.map(esc).join(", ")
                    : "supplies no extracted field") + "</span></li>").join("") + "</ul>"
              : "") +
            (arch.length
              ? '<p class="kn-sub dc-dc-archived-head">Already archived in period ' + per.period +
                " (kept, and readable):</p><ul class=\"dc-dc-archived\">" + arch.map((d) =>
                  '<li><span class="mod-mono">' + esc(d.filename) + "</span> " +
                  '<span class="kn-sub">archived ' + esc(d.archived_at || "") + " by " +
                  esc(d.archived_by || "") + "</span></li>").join("") + "</ul>"
              : "");
          list.querySelectorAll(".dc-dc-tick").forEach((c) =>
            c.addEventListener("change", syncButton));
          syncButton();
        }
        function paintRecord() {
          const entries = state.record || [];
          rec.innerHTML =
            '<p class="kn-sub dc-dc-record-head">Archive record — ' + entries.length +
              " entr" + (entries.length === 1 ? "y" : "ies") + " for " + esc(id) + ".</p>" +
            (entries.length
              ? '<ul class="dc-dc-record-list">' + entries.map((e) =>
                  "<li><span class=\"kn-sub\">" + esc(e.server_ts || e.archived_at || "") +
                  " · period " + esc(String(e.period)) + " · " + esc(String(e.document_count)) +
                  " document(s) · by " + esc(e.archived_by || "") + "</span><br />" +
                  "<span class=\"kn-sub\">fields withdrawn: " +
                  ((e.fields_withdrawn && e.fields_withdrawn.length)
                    ? e.fields_withdrawn.map(esc).join(", ") : "none") + "</span><br />" +
                  "<span class=\"kn-sub\">confirmation: " + esc(e.confirmation || "") +
                  "</span></li>").join("") + "</ul>"
              : "");
        }
        async function load(keepPeriod) {
          let resp;
          try {
            resp = await LinStore.postWithTimeout({ action: "projectdocumentcontrol", id: id });
          } catch (e) {
            msg.textContent = "Could not read this project's documents: " +
                              ((e && e.message) || "the server is not reachable") + ".";
            return;
          }
          if (!resp || resp.ok !== true) {
            msg.textContent = (resp && resp.error) || "Could not read this project's documents.";
            return;
          }
          state = { periods: resp.periods || [], record: resp.record || [] };
          const want = keepPeriod != null ? String(keepPeriod)
                                          : (state.periods.length
                                             ? String(state.periods[state.periods.length - 1].period)
                                             : "");
          sel.innerHTML = state.periods.length
            ? state.periods.map((p) =>
                '<option value="' + esc(String(p.period)) + '">Period ' + esc(String(p.period)) +
                " — " + (p.documents || []).length + " live, " +
                (p.archived || []).length + " archived</option>").join("")
            : '<option value="">This project holds no documents</option>';
          if (want) sel.value = want;
          paintList();
          paintRecord();
        }

        sel.addEventListener("change", () => { msg.textContent = ""; paintList(); });
        go.addEventListener("click", () => {
          const per = current();
          const ids = ticked();
          if (!per || !ids.length) return;
          // THE SENTENCE THE PERSON READS IS THE SENTENCE THAT IS RECORDED. Built once, shown
          // in the confirmation, and sent verbatim as `confirmation`.
          const sentence = "Archive " + ids.length + " document" + (ids.length === 1 ? "" : "s") +
            " from reporting period " + per.period + " of " + id +
            ". The document" + (ids.length === 1 ? "" : "s") + " and " +
            (ids.length === 1 ? "its" : "their") + " bytes are kept and stay readable. " +
            "The extracted fields are withdrawn from this project's live document set. " +
            "The stored figures do not change until you generate signals for every period. " +
            "No other document is touched.";
          confirmDestructive({
            title: "Archive " + ids.length + " document" + (ids.length === 1 ? "" : "s") +
                   " from period " + per.period,
            detail: sentence,
            confirmLabel: "Archive " + ids.length + " document" + (ids.length === 1 ? "" : "s"),
            onConfirm: async () => {
              go.disabled = true;
              msg.textContent = "Archiving…";
              let resp;
              try {
                resp = await LinStore.postWithTimeout({
                  action: "projectdocumentarchive", id: id, period: per.period,
                  document_ids: ids, confirmation: sentence });
              } catch (e) {
                resp = { ok: false, error: (e && e.message) || "the request did not complete" };
              }
              if (!resp || resp.ok !== true) {
                msg.textContent = (resp && resp.error) || "Could not archive.";
                syncButton();
                return;
              }
              logEvent("ARCHIVED " + resp.archived.length + " document(s) from period " +
                       per.period + " of " + id + ".");
              const fields = [];
              (resp.archived || []).forEach((a) =>
                (a.fields_withdrawn || []).forEach((f) => {
                  if (fields.indexOf(f) === -1) fields.push(f);
                }));
              msg.textContent = "Archived " + resp.archived.length + " document(s) from period " +
                per.period + ". Fields withdrawn: " +
                (fields.length ? fields.join(", ") : "none") +
                ". The stored figures have not moved yet — press “Generate signals for " +
                "every period” on this page to recalculate.";
              await load(per.period);
            }
          });
        });
        load(null);
      }
    });
  }

  // Phase 2 seam kept for API compatibility; store.js already hydrates.
  function mergeUserProjects() {}

  window.LinIngest = { mergeUserProjects, renderPortfolioAdmin, openInlineManage, openCreateModal, openUploadModal, openDocumentControl, openArchivedModal, openActivityModal, renderScopedIngest, populateSignals, INGEST_RULES };
})();
