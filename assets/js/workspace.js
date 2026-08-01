/* ============================================================
   Opus Gubernatio — workspace.js (T3/T5)
   ------------------------------------------------------------
   Project workspace and portfolio view. T6 folded workspace.html into
   index.html, so this now renders the Portfolio project list and the
   Project page rather than a page of its own.

   It still calls nothing from sim.js / simulations.js / categories.js /
   knowledge.js, and that is now a rule this file keeps rather than one
   the page kept for it. While workspace.html existed, calling LinSim
   here was impossible — the function was not in the document. It is in
   the document now, so the discipline has to live here: this file has
   zero references to any of those four bundles, and a change that adds
   one is a change that puts a browser-computed number in front of a
   participant. Every number rendered here comes from a stored
   `computed_results` row, fetched
   through LinStore.postWithTimeout({action:...}) — nothing is computed
   in this file. The only "logic" below is presentation: grouping,
   labelling, and rendering what /exec already returns.

   Module/category names are a small static table (MODULE_NAMES /
   CATEGORY_NAMES / GROUP_NAMES below), sourced from
   p0-baseline/module_renumbering_map.csv — the same file
   server/app/simulation/registry.py reads at runtime — copied in
   rather than loading categories.js, which pulls in the rest of the
   client-side simulation bundle this page must not load. This is the
   ONLY thing here that duplicates data from elsewhere in the repo, and
   it is names only: no thresholds, no formulas, no computation.
   ============================================================ */

(function () {
  "use strict";

  /* ---------- module / category / group name lookup (names only) ---------- */

  var GROUP_NAMES = {
    A: "Project Health",
    B: "Recommendation & Governance",
    C: "Data & Evidence Health",
    D: "Portfolio Level"
  };

  var CATEGORY_NAMES = {
    A1: "Cost & EVM Performance", A2: "Schedule Performance", A3: "Cost Risk",
    A4: "Document-Derived Condition Signals", A5: "System Dynamics & Complexity",
    A6: "Delivery Quality Performance",
    B1: "Signal Synthesis", B2: "Evidence Combination",
    B3: "Regulatory & Authority Thresholds", B4: "Decision Optimization",
    C1: "Data Integrity",
    D1: "Portfolio Health"
  };

  // Group C computes but must never contribute to project status (server-enforced already,
  // via contributes_to_project_status — this is display-only, so the UI can label it, not so
  // it can decide inclusion).
  var GROUP_ORDER = ["A", "B", "C", "D"];

  var MODULE_NAMES = {
    "A1.1": "Monte Carlo EAC", "A1.2": "CUSUM Anomaly Monitor", "A1.3": "Bayesian EAC",
    "A1.4": "Kalman Filter SPI Smoother", "A1.5": "ARIMA CPI Forecast", "A1.6": "Earned Schedule",
    "A1.7": "TCPI", "A1.8": "Variance at Completion", "A1.9": "Budget Execution Rate",
    "A1.10": "Regression to Mean CPI", "A1.11": "ICE Ratio",
    "A2.1": "PERT Network Criticality", "A2.2": "Line of Balance", "A2.3": "CCPM Buffer Health",
    "A2.4": "Schedule Compression Index", "A2.5": "Float Consumption Rate",
    "A2.6": "S-Curve Deviation", "A2.7": "Milestone Trend Analysis",
    "A2.8": "Look-Ahead Schedule Health", "A2.9": "Resource Loading Index",
    "A2.10": "Schedule Risk Analysis P80", "A2.11": "Critical Path Index",
    "A3.1": "Reference Class Forecasting", "A3.2": "Contingency Burn Rate",
    "A3.3": "Labor Productivity Index", "A3.4": "Material Cost Variance",
    "A3.5": "Overhead Absorption Rate", "A3.6": "Cost Risk Analysis P80",
    "A3.7": "Analogous Estimating Ratio", "A3.8": "Parametric Cost Index",
    "A3.9": "Inflation Adjustment Index",
    "A4.1": "Document Risk Score", "A4.2": "RFI Velocity", "A4.3": "Submittal Rejection Rate",
    "A4.4": "NCR Rate", "A4.5": "Weather Day Impact", "A4.6": "Change Order Frequency",
    "A4.7": "Dispute Escalation Index", "A4.8": "Subcontractor Performance",
    "A4.9": "Procurement Lead Time Monitor", "A4.10": "Specification Conflict Density",
    "A5.1": "DSM Rework Propagation", "A5.2": "Sensitivity Analysis",
    "A5.3": "Tornado Risk Ranking", "A5.4": "Scenario Modeling",
    "A5.5": "Rework Feedback Loop", "A5.6": "Queueing Theory Bottleneck",
    "A5.7": "Agent-Based Supply Chain", "A5.8": "Discrete Event Simulation",
    "A6.1": "Quality Compliance Index", "A6.2": "Safety Performance Index",
    "A6.3": "Environmental Compliance Rate", "A6.4": "Contractor Performance Score",
    "B1.1": "Conservative Dominance", "B1.2": "Weighted Voting", "B1.3": "Majority Rules",
    "B1.4": "Worst-N-of-M",
    "B2.1": "Dempster-Shafer", "B2.2": "Rough Sets", "B2.3": "Neutrosophic Logic",
    "B2.4": "Interval Fuzzy Sets", "B2.5": "Z-numbers", "B2.6": "PLTS",
    "B2.7": "Plithogenic Sets", "B2.8": "Belief Rule Base", "B2.9": "Quantum Probability",
    "B2.10": "Pythagorean Fuzzy Sets", "B2.11": "Picture Fuzzy Sets",
    "B2.12": "Hesitant Fuzzy Sets", "B2.13": "Type-2 Fuzzy Sets", "B2.14": "Maximum Entropy",
    "B2.15": "Possibility Theory", "B2.16": "Spherical Fuzzy Sets",
    "B2.17": "Fermatean Fuzzy Sets", "B2.18": "MARCOS Ranking", "B2.19": "CRITIC-TOPSIS",
    "B2.20": "Hypersoft Sets",
    "B3.1": "ABM Governance Layer", "B3.2": "FAR Threshold Monitor",
    "B3.3": "OMB A-11 Check", "B3.4": "EVM Reporting Threshold",
    "B3.5": "Contract Modification Frequency",
    "B4.1": "Multi-Objective Optimization", "B4.2": "Linear Programming",
    "B4.3": "Constraint Satisfaction Analysis", "B4.4": "What-If Scenario Matrix",
    "B4.5": "Decision Sensitivity Matrix", "B4.6": "Pareto Frontier Analysis",
    "B4.7": "Regret Minimization Index",
    "C1.1": "Missing Data Index", "C1.2": "Data Timeliness Score",
    "C1.3": "Source Reliability Weighting", "C1.4": "Audit Trail Completeness",
    "C1.5": "Information Completeness Ratio", "C1.6": "Cross-document Consistency Score",
    "C1.7": "Reporting Frequency Index",
    "D1.1": "Isolation Forest", "D1.2": "Portfolio Outlier Detection",
    "D1.3": "Signal Trajectory Classifier", "D1.4": "Cross-project Pattern Detector",
    "D1.5": "Anomaly Score"
  };

  function moduleName(id) { return MODULE_NAMES[id] || "Unrecognized analytical module"; }
  function categoryName(id) { return CATEGORY_NAMES[id] || id || "Uncategorised"; }
  function groupName(id) { return GROUP_NAMES[id] || id || ""; }

  function statusDotColor(status) {
    var s = String(status || "").toLowerCase();
    if (s.indexOf("green") >= 0) return "var(--status-green)";
    if (s.indexOf("yellow") >= 0) return "var(--status-yellow)";
    if (s.indexOf("amber") >= 0) return "var(--status-amber)";
    if (s.indexOf("red") >= 0) return "var(--status-red)";
    if (s.indexOf("complete") >= 0) return "var(--status-complete)";
    return "var(--status-nodata)";
  }

  /* ---------- tiny DOM helpers ---------- */

  function $(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function fmtDate(iso) {
    if (!iso) return "—";
    try { return new Date(iso).toLocaleString(); } catch (e) { return iso; }
  }

  /* ---------- wire helper ---------- */

  function token() { return window.LinAuth ? LinAuth.getToken() : null; }

  function call(action, extra) {
    var payload = Object.assign({ action: action, session_token: token() }, extra || {});
    return LinStore.postWithTimeout(payload, 60000);
  }

  /* ---------- state ---------- */

  var STATE = { projects: [] };

  /* ---------- boot ---------- */

  // T6. This was its own page with its own sign-in gate. It is now two sections of the main
  // application, so the gate is gone: index.html's auth flow decides whether anyone is signed in
  // at all, and app.js calls boot() once that has been settled. Booting from DOMContentLoaded
  // here would have raced that decision and rendered a workspace behind the login screen.
  //
  // There is deliberately no sign-out handler any more. The old one did
  // `window.location.href = "index.html"`, which inside the shell would reload the whole
  // application; the topbar's existing LinAuth.logout() control is the one path now.
  var booted = false;

  async function boot() {
    if (booted) return;
    var who = await call("researchwhoami");
    if (!who || who.ok !== true) return;
    booted = true;

    // A research participant does not create projects — the researcher creates the project and
    // its assignment together. Hiding the card is a courtesy, not the guard: gate_action refuses
    // projectcreate (and the legacy `create`) for any research account before dispatch, so this
    // could be deleted and nothing would change about what the server accepts.
    //
    // Operational accounts keep it. A director running a real project is who it is for.
    if (who.account_type === "research") {
      var createCard = document.getElementById("ws-create-card");
      if (createCard) createCard.hidden = true;
    }

    document.querySelectorAll("#ws-project-tabs button").forEach(function (btn) {
      btn.addEventListener("click", function () { switchPanel(btn.dataset.wstab); });
    });

    wireProjectsPanel();
    wireUploadPanel();
    wireDocumentsPanel();
    wireDetailPanel();

    await refreshProjects();
    renderPortfolio();
  }

  function switchPanel(name) {
    document.querySelectorAll("#ws-project-tabs button").forEach(function (b) {
      b.classList.toggle("active", b.dataset.wstab === name);
    });
    document.querySelectorAll("#wstab-upload, #wstab-documents, #wstab-detail, #wstab-decision")
      .forEach(function (p) {
        p.classList.toggle("active", p.id === "wstab-" + name);
      });
    // The decision sequence renders lazily: it is the last step of the period and asking the
    // server for its state on every project-page visit would audit an evidence view that the
    // participant did not make.
    if (name === "decision" && window.LinDecisionUI && LinDecisionUI.mount) {
      try { LinDecisionUI.mount(); } catch (e) { /* a render fault must not trap the tab */ }
    }
  }

  // Opening a project from the portfolio list routes here and selects it in every picker, so
  // the three tabs agree about which project is being looked at.
  function openProject(pid) {
    ["ws-upload-project", "ws-docs-project", "ws-detail-project"].forEach(function (id) {
      var sel = $(id);
      if (sel) sel.value = pid;
    });
    var p = (STATE.projects || []).filter(function (x) { return x.project_id === pid; })[0];
    if (p) {
      var t = $("ws-project-title"); if (t) t.textContent = p.name || "Project";
      var s = $("ws-project-sub");
      if (s) s.textContent = (p.sector ? p.sector + " · " : "") + "Period " + (p.period || 1);
    }
    if (window.LinApp && LinApp.showPage) LinApp.showPage("project");
    switchPanel("upload");
    onUploadProjectChange();
    onDocsProjectChange();
    onDetailProjectChange();
  }

  window.LinWorkspace = { boot: boot, openProject: openProject, switchPanel: switchPanel };

  /* ============================================================
     Part 1 — project list and creation
     ============================================================ */

  function wireProjectsPanel() {
    $("ws-create-btn").addEventListener("click", async function () {
      var name = $("ws-new-name").value.trim();
      var sector = $("ws-new-sector").value.trim();
      var errEl = $("ws-create-error");
      errEl.style.display = "none";
      if (!name) { errEl.textContent = "Name is required."; errEl.style.display = "block"; return; }
      $("ws-create-btn").disabled = true;
      var resp = await call("projectcreate", { name: name, sector: sector });
      $("ws-create-btn").disabled = false;
      if (!resp || resp.ok !== true) {
        errEl.textContent = (resp && resp.error) || "Could not create project.";
        errEl.style.display = "block";
        return;
      }
      $("ws-new-name").value = "";
      $("ws-new-sector").value = "";
      await refreshProjects();
    });
  }

  async function refreshProjects() {
    var resp = await call("workspaceprojects");
    var listEl = $("ws-project-list");
    if (!resp || resp.ok !== true) {
      listEl.innerHTML = '<p class="ws-error">' + esc((resp && resp.error) ||
        "Could not load projects.") + "</p>";
      return;
    }
    STATE.projects = resp.projects || [];
    if (STATE.projects.length === 0) {
      listEl.innerHTML = '<p class="ws-empty">No projects yet. Create one above.</p>';
    } else {
      listEl.innerHTML = STATE.projects.map(function (p) {
        var badgeClass = p.project_role === "PM" ? "ws-badge-pm" : "ws-badge-observer";
        // T6 Part E. The identifier was the subtitle of every row and the title of any row
        // whose name was empty, which made an internal key the name of the thing. The name is
        // the name; where there is none, say so in words. The id survives only as truncated
        // metadata, because an operator reconciling against a log still needs to find it.
        var shortId = String(p.project_id || "");
        if (shortId.length > 10) shortId = shortId.slice(0, 8) + "…";
        return '<div class="ws-row">' +
          '<div><strong>' + esc(p.name || "Untitled project") + '</strong>' +
          '<div class="ws-note">' + (p.sector ? esc(p.sector) + " · " : "") +
          '<span class="ws-id" title="' + esc(p.project_id) + '">' + esc(shortId) + '</span>' +
          '</div></div>' +
          '<div style="display:flex; align-items:center; gap:10px;">' +
          '<button class="ws-btn ws-btn-secondary" data-open-project="' + esc(p.project_id) +
            '">Open</button>' +
          '<span class="ws-badge ' + badgeClass + '">' + esc(p.project_role) + '</span>' +
          '<span class="ws-note">Period ' + esc(p.period) + '</span>' +
          '<span class="ws-note">' + (p.computed ?
            '<span class="ws-dot" style="background:var(--status-green);"></span>Computed' :
            '<span class="ws-dot" style="background:var(--status-nodata);"></span>Not yet computed') +
          '</span></div></div>';
      }).join("");
      listEl.querySelectorAll("[data-open-project]").forEach(function (b) {
        b.addEventListener("click", function () { openProject(b.dataset.openProject); });
      });
    }
    populateProjectPickers();
    renderPortfolio();
  }

  function populateProjectPickers() {
    [["ws-upload-project", onUploadProjectChange],
     ["ws-docs-project", onDocsProjectChange],
     ["ws-detail-project", onDetailProjectChange]].forEach(function (pair) {
      var sel = $(pair[0]);
      var current = sel.value;
      sel.innerHTML = STATE.projects.map(function (p) {
        return '<option value="' + esc(p.project_id) + '">' + esc(p.name || "Untitled project") +
          " (" + esc(p.project_role) + ")</option>";
      }).join("");
      if (current && STATE.projects.some(function (p) { return p.project_id === current; })) {
        sel.value = current;
      }
      if (!sel.dataset.wired) {
        sel.dataset.wired = "1";
        var handler = pair[1];
        sel.addEventListener("change", function () {
          // Only a real project switch clears the last batch's per-file outcome — the same
          // handler also runs programmatically after a successful upload TO THE SAME project
          // (see handleFiles), which must not wipe out what it just rendered.
          if (sel === $("ws-upload-project")) {
            $("ws-upload-results").innerHTML = "";
            $("ws-compute-note").textContent = "";
          }
          handler();
        });
      }
    });
    if (STATE.projects.length) {
      if ($("ws-upload-project").value) onUploadProjectChange();
      if ($("ws-docs-project").value) onDocsProjectChange();
      if ($("ws-detail-project").value) onDetailProjectChange();
    }
  }

  function projectRole(id) {
    var p = STATE.projects.filter(function (x) { return x.project_id === id; })[0];
    return p ? p.project_role : null;
  }

  /* ============================================================
     Part 2 — period upload
     ============================================================ */

  function wireUploadPanel() {
    var input = $("ws-upload-input");
    var drop = $("ws-upload-drop");
    input.addEventListener("change", function () { handleFiles(input.files); });
    ["dragover", "dragenter"].forEach(function (ev) {
      drop.addEventListener(ev, function (e) { e.preventDefault(); });
    });
    drop.addEventListener("drop", function (e) {
      e.preventDefault();
      if (drop.classList.contains("disabled")) return;
      if (e.dataTransfer && e.dataTransfer.files) handleFiles(e.dataTransfer.files);
    });
    $("ws-compute-btn").addEventListener("click", async function () {
      var pid = $("ws-upload-project").value;
      if (!pid) return;
      $("ws-compute-btn").disabled = true;
      var resp = await call("projectcompute", { id: pid, period: 1 });
      $("ws-compute-btn").disabled = false;
      var note = $("ws-compute-note");
      if (!resp || resp.ok !== true) {
        note.textContent = (resp && resp.error) || "Compute failed.";
        note.className = "ws-error";
      } else if (resp.note) {
        note.textContent = resp.note;
        note.className = "ws-note";
      } else {
        note.textContent = "Computed. Project status: " + (resp.project_status || "—") +
          (resp.abstained && resp.abstained.length ?
            " (" + resp.abstained.length + " module(s) abstained on missing data)" : "");
        note.className = "ws-note";
      }
      await refreshProjects();
      await onUploadProjectChange();
    });
  }

  async function onUploadProjectChange() {
    var pid = $("ws-upload-project").value;
    var drop = $("ws-upload-drop");
    var input = $("ws-upload-input");
    var isPM = projectRole(pid) === "PM";
    drop.classList.toggle("disabled", !isPM);
    input.disabled = !isPM;
    $("ws-upload-error").style.display = "none";

    if (!isPM) {
      $("ws-upload-status").innerHTML =
        '<span class="ws-error">Only this project\'s PM may upload documents. ' +
        "You are an Observer on this project. The server refuses uploads regardless of what " +
        "this page shows.</span>";
    }

    var resp = await call("projectuploadstatus", { id: pid, period: 1 });
    if (!resp || resp.ok !== true) {
      if (isPM) $("ws-upload-status").textContent = (resp && resp.error) || "";
      $("ws-upload-results").innerHTML = "";
      return;
    }
    renderUploadStatus(resp, isPM);
  }

  // Two distinct pieces of state, deliberately never sharing a container:
  //   - ws-upload-results: the outcome of the batch just uploaded (renderUploadFiles), which
  //     is the only place a FAILED extraction is ever shown — a failed document never gets a
  //     `documents` row, so projectuploadstatus can never reproduce that information later.
  //   - ws-upload-period-docs: the period's cumulative document set (this call), useful across
  //     multiple upload batches. Overwriting ws-upload-results with this on every status
  //     refresh was the bug that made a just-reported failure disappear a moment later.
  function renderUploadStatus(resp, isPM) {
    if (isPM) {
      var bits = [];
      bits.push(resp.documents.length + " document(s) present for period " + resp.period + ".");
      if (resp.expected_missing && resp.expected_missing.length) {
        bits.push("Still expected: " + resp.expected_missing.join(", ") + " (advisory only. " +
          "compute never refuses on a missing document type).");
      }
      bits.push(resp.computed ?
        "This period has been computed." : "This period has not been computed yet.");
      $("ws-upload-status").innerHTML = esc(bits.join(" "));
    }
    renderContributionList(resp.documents, "ws-upload-period-docs");
  }

  function renderContributionList(documents, targetId) {
    if (!documents || !documents.length) {
      $(targetId).innerHTML = "";
      return;
    }
    var contributing = documents.filter(function (d) { return d.contributes; });
    var nonContributing = documents.filter(function (d) { return !d.contributes; });
    var html = "";
    if (nonContributing.length) {
      html += '<p class="ws-note" style="margin-top:12px;"><strong>' + nonContributing.length +
        " document(s) did not contribute to the analysis:</strong></p>";
      html += nonContributing.map(function (d) {
        return '<div class="ws-file-row"><span>' + esc(d.filename) + "</span>" +
          '<span class="ws-note">document type "' + esc(d.doc_type) +
          '" is not mapped to any signal input. It is stored, but contributes nothing</span></div>';
      }).join("");
    }
    if (contributing.length) {
      html += '<p class="ws-note" style="margin-top:12px;">' + contributing.length +
        " document(s) contributing to the analysis:</p>";
      html += contributing.map(function (d) {
        return '<div class="ws-file-row"><span>' + esc(d.filename) + "</span>" +
          '<span class="ws-note">' + esc(d.doc_type) + "</span></div>";
      }).join("");
    }
    $(targetId).innerHTML = html;
  }

  function fileToBase64(file) {
    return new Promise(function (resolve, reject) {
      var reader = new FileReader();
      reader.onload = function () {
        var result = reader.result || "";
        var comma = result.indexOf(",");
        resolve(comma >= 0 ? result.slice(comma + 1) : result);
      };
      reader.onerror = function () { reject(reader.error); };
      reader.readAsDataURL(file);
    });
  }

  async function handleFiles(fileList) {
    var pid = $("ws-upload-project").value;
    if (!pid || projectRole(pid) !== "PM") return;
    var files = Array.prototype.slice.call(fileList || []);
    if (!files.length) return;

    var errEl = $("ws-upload-error");
    errEl.style.display = "none";

    var progress = $("ws-upload-progress");
    var label = $("ws-upload-progress-label");
    var fill = $("ws-upload-progress-fill");
    progress.style.display = "block";
    label.textContent = "Reading " + files.length + " file(s)…";
    fill.style.width = "10%";

    var documents;
    try {
      documents = await Promise.all(files.map(async function (f) {
        return {
          filename: f.name,
          mimeType: f.type || "application/pdf",
          dataBase64: await fileToBase64(f)
        };
      }));
    } catch (e) {
      progress.style.display = "none";
      errEl.textContent = "Could not read one or more files.";
      errEl.style.display = "block";
      return;
    }

    label.textContent = "Uploading and extracting " + files.length + " file(s). This can " +
      "take a while for documents never seen before…";
    fill.style.width = "45%";

    var resp = await call("projectupload", { id: pid, period: 1, documents: documents });

    progress.style.display = "none";
    $("ws-upload-input").value = "";

    if (!resp || resp.ok !== true) {
      errEl.textContent = (resp && resp.error) || "Upload failed.";
      errEl.style.display = "block";
      return;
    }

    var s = resp.summary || {};
    label.textContent = s.recognised + " of " + s.total + " recognized from cache, " +
      s.extracted + " extracted fresh" +
      (s.failed ? ", " + s.failed + " failed" : "") +
      (s.unmapped ? ", " + s.unmapped + " unmapped" : "") +
      " (" + (resp.extraction_seconds != null ? resp.extraction_seconds.toFixed(1) : "?") + "s).";

    renderUploadFiles(resp.files || []);
    await onUploadProjectChange();
  }

  function renderUploadFiles(files) {
    var html = files.map(function (f) {
      var tag, note;
      if (f.status === "failed") {
        tag = '<span class="ws-note" style="color:var(--status-red);">failed</span>';
        note = f.error || "extraction failed";
      } else {
        tag = f.was_cached ?
          '<span class="ws-note">recognized (cached, no model call)</span>' :
          '<span class="ws-note">newly extracted</span>';
        note = f.contributes ? esc(f.doc_type) : (f.note || "did not contribute");
      }
      return '<div class="ws-file-row"><span>' + esc(f.filename) + "</span>" + tag +
        '<span class="ws-note">' + esc(note) + "</span></div>";
    }).join("");
    $("ws-upload-results").innerHTML = html;
  }

  /* ============================================================
     Part 3 — document viewer
     ============================================================ */

  function wireDocumentsPanel() {
    $("ws-doc-reader-close").addEventListener("click", function () {
      $("ws-doc-reader-card").style.display = "none";
      $("ws-doc-reader-frame").src = "about:blank";
    });
  }

  async function onDocsProjectChange() {
    var pid = $("ws-docs-project").value;
    var resp = await call("projectuploadstatus", { id: pid, period: 1 });
    var listEl = $("ws-docs-list");
    if (!resp || resp.ok !== true) {
      listEl.innerHTML = '<p class="ws-error">' + esc((resp && resp.error) || "") + "</p>";
      return;
    }
    var docs = resp.documents || [];
    if (!docs.length) {
      listEl.innerHTML = '<p class="ws-empty">No documents uploaded for this period yet.</p>';
      return;
    }
    listEl.innerHTML = docs.map(function (d) {
      var openable = !!d.document_id;
      return '<div class="ws-file-row">' +
        '<span style="flex:1;">' + esc(d.filename) + "</span>" +
        '<span class="ws-note">' + esc(d.doc_type) + "</span>" +
        '<span class="ws-note">' + (d.was_cached ? "cached" : "newly extracted") + "</span>" +
        '<span class="ws-note">' + esc(fmtDate(d.uploaded_at)) + "</span>" +
        (openable ?
          '<button class="ws-btn-secondary ws-btn" data-open-doc="' + esc(d.document_id) +
          '" data-open-name="' + esc(d.filename) + '">Open</button>' : "") +
        "</div>";
    }).join("");
    listEl.querySelectorAll("[data-open-doc]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        openDocument(pid, btn.dataset.openDoc, btn.dataset.openName);
      });
    });
  }

  function openDocument(projectId, documentId, filename) {
    var url = "/documents/" + encodeURIComponent(documentId) + "/content" +
      "?project_id=" + encodeURIComponent(projectId) +
      "&session_token=" + encodeURIComponent(token());
    $("ws-doc-reader-title").textContent = filename || "Document";
    $("ws-doc-reader-frame").src = url;
    $("ws-doc-reader-card").style.display = "block";
  }

  /* ============================================================
     Part 4 — project detail (reads stored computed_results only)
     ============================================================ */

  function wireDetailPanel() {}

  async function onDetailProjectChange() {
    var pid = $("ws-detail-project").value;
    var body = $("ws-detail-body");
    body.innerHTML = '<p class="ws-note">Loading…</p>';
    var resp = await call("projectresults", { id: pid, period: 1 });
    // Share the stored row with the rest of the application. taxonomy.js reads statuses from
    // here, so the radar, the project list and this panel all show the same number without any
    // of them recomputing it — and without a second request for a row already in hand.
    if (resp && resp.ok === true && window.LinResults) LinResults.prime(pid, resp.result);
    if (!resp || resp.ok !== true) {
      body.innerHTML = '<p class="ws-empty">' + esc((resp && resp.error) ||
        "No computed result yet for this period. Upload documents and run analysis " +
        "from the Period upload tab.") + "</p>";
      return;
    }
    renderProjectDetail(resp.result);
  }

  function renderProjectDetail(r) {
    var html = "";
    html += '<div class="ws-row"><div><strong>Project status</strong></div>' +
      '<div><span class="ws-dot" style="background:' + statusDotColor(r.project_status) +
      ';"></span>' + esc(r.project_status || "—") + "</div></div>";

    // Category statuses, by group, using names only — never a category id or module id.
    var cats = r.category_statuses || {};
    var byGroup = {};
    Object.keys(cats).forEach(function (catId) {
      var c = cats[catId];
      var g = c.group || catId.charAt(0);
      (byGroup[g] = byGroup[g] || []).push({ catId: catId, c: c });
    });
    GROUP_ORDER.forEach(function (g) {
      var entries = byGroup[g];
      if (!entries || !entries.length) return;
      html += '<div class="ws-group"><h3>' + esc(groupName(g)) + "</h3>";
      entries.forEach(function (e) {
        var note = (e.c.contributes_to_project_status === false) ?
          '<span class="ws-note"> (informational, does not contribute to project status)</span>' : "";
        html += '<div class="ws-module"><span class="ws-dot" style="background:' +
          statusDotColor(e.c.status) + ';"></span>' +
          '<span class="ws-mname">' + esc(categoryName(e.catId)) + "</span>" + note + "</div>";
      });
      html += "</div>";
    });

    // Module results, grouped by group letter (from each module's own "group" field, not the
    // module id) — names only.
    var modules = r.module_results;
    if (Array.isArray(modules) && modules.length) {
      var byModGroup = {};
      modules.forEach(function (m) {
        var g = m.group || (m.module_id || "").charAt(0);
        (byModGroup[g] = byModGroup[g] || []).push(m);
      });
      html += '<div class="ws-group"><h3>Module results</h3>';
      GROUP_ORDER.forEach(function (g) {
        var list = byModGroup[g];
        if (!list || !list.length) return;
        html += '<div style="margin-bottom:8px;"><div class="ws-note" style="margin-bottom:2px;">' +
          esc(groupName(g)) + "</div>";
        list.forEach(function (m) {
          var name = moduleName(m.module_id);
          var evidence = m.evidence_metric ? esc(m.evidence_metric) : "";
          html += '<div class="ws-module"><span class="ws-dot" style="background:' +
            statusDotColor(m.status_color) + ';"></span>' +
            '<span class="ws-mname">' + esc(name) + "</span>" +
            '<span class="ws-note">' + evidence + "</span></div>";
        });
        html += "</div>";
      });
      html += "</div>";
    }

    // The recommendation is intentionally never rendered here. When visible, r.recommendation
    // is a non-null object; T4 owns showing it. This screen shows nothing about it either way —
    // not even a "recommendation available" placeholder — so there is nothing here for the
    // pre-lock redaction to leak around.

    html += '<div class="ws-provenance">Stored result, not a live computation. ' +
      "Computed at " + esc(fmtDate(r.computed_at)) +
      " · simulation " + esc(r.simulation_version || "—") +
      " · seed " + esc(r.seed || "—") +
      " · period cutoff " + esc(r.period_cutoff || "—") +
      (r.superseded_by ? " · superseded by a later recompute" : "") + "</div>";

    $("ws-detail-body").innerHTML = html;
  }

  /* ============================================================
     Part 5 — portfolio view
     ============================================================ */

  async function renderPortfolio() {
    var listEl = $("ws-portfolio-list");
    var mine = STATE.projects.filter(function (p) { return p.project_role === "PM"; });
    if (!mine.length) {
      listEl.innerHTML = '<p class="ws-empty">You are not the PM of any project yet.</p>';
      return;
    }
    listEl.innerHTML = '<p class="ws-note">Loading…</p>';
    var rows = await Promise.all(mine.map(async function (p) {
      var resp = await call("projectresults", { id: p.project_id, period: p.period || 1 });
      // Same reason as the detail panel: this is the loader that already has the row, so it is
      // the one that shares it. The portfolio radar reads statuses through taxonomy.js and
      // never fetches anything of its own.
      if (resp && resp.ok === true && window.LinResults) LinResults.prime(p.project_id, resp.result);
      return { project: p, resp: resp };
    }));
    listEl.innerHTML = rows.map(function (row) {
      var p = row.project, resp = row.resp;
      if (!resp || resp.ok !== true) {
        return '<div class="ws-card"><strong>' + esc(p.name || "Untitled project") + "</strong>" +
          '<p class="ws-note">No computed result yet.</p></div>';
      }
      var snap = resp.result.portfolio_snapshot;
      if (!snap || snap.insufficient_data) {
        var msg = snap && snap.message ? snap.message :
          "Portfolio Health has not been computed for this project.";
        return '<div class="ws-card"><strong>' + esc(p.name || "Untitled project") + "</strong>" +
          '<p class="ws-note">' + esc(msg) + "</p></div>";
      }
      var results = snap.results || {};
      var rowsHtml = Object.keys(results).map(function (key) {
        var m = results[key];
        return '<div class="ws-module"><span class="ws-dot" style="background:' +
          statusDotColor(m.status_color) + ';"></span>' +
          '<span class="ws-mname">' + esc(moduleNameForPortfolioKey(key)) + "</span>" +
          '<span class="ws-note">' + esc(m.evidence_metric || "") + "</span></div>";
      }).join("");
      return '<div class="ws-card"><strong>' + esc(p.name || "Untitled project") + "</strong>" +
        '<div class="ws-note">portfolio size ' + esc(snap.portfolio_size) + "</div>" +
        rowsHtml + "</div>";
    }).join("");
  }

  // The stored portfolio_snapshot keys results by an internal cat8_N_* name, not a module id
  // in MODULE_NAMES (D1.1..D1.5 map differently) — translate the handful of keys directly.
  var PORTFOLIO_KEY_NAMES = {
    cat8_1_isolation_forest: "Isolation Forest",
    cat8_2_portfolio_outlier: "Portfolio Outlier Detection",
    cat8_3_trajectory_classifier: "Signal Trajectory Classifier",
    cat8_4_cross_project_pattern: "Cross-project Pattern Detector",
    cat8_5_anomaly_score: "Anomaly Score"
  };
  function moduleNameForPortfolioKey(key) { return PORTFOLIO_KEY_NAMES[key] || key; }
})();
