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
    B: "Recommendation and Governance",
    C: "Data and Evidence Health",
    D: "Portfolio Level"
  };

  var CATEGORY_NAMES = {
    A1: "Cost and EVM Performance", A2: "Schedule Performance", A3: "Cost Risk",
    A4: "Document-Derived Condition Signals", A5: "System Dynamics and Complexity",
    A6: "Delivery Quality Performance",
    B1: "Signal Synthesis", B2: "Evidence Combination",
    B3: "Regulatory and Authority Thresholds", B4: "Decision Optimization",
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
    "A1.10": "CPI Shrinkage Forecast", "A1.11": "Independent EAC Reconciliation Index",
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
  function categoryName(id) { return CATEGORY_NAMES[id] || id || "Uncategorized"; }
  function groupName(id) { return GROUP_NAMES[id] || id || ""; }

  // The matched address, shown wherever a project's location is. Deliberately the geocoder's
  // display_name rather than the typed address: they differ, and the difference is the whole
  // point of showing it.

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

    // Each panel wires independently. One panel reaching for an element that another change
    // removed must not silently unwire the whole page, which is exactly what happened when the
    // create-project card was deleted: `wireProjectsPanel` threw and the three panels after it,
    // plus the project-list load, never ran. The failure is reported rather than swallowed --
    // a panel that did not wire is a defect, and a console error is how the next person finds
    // it -- but it is contained to its own panel.
    [["projects", wireProjectsPanel], ["upload", wireUploadPanel],
     ["documents", wireDocumentsPanel], ["detail", wireDetailPanel]].forEach(function (pair) {
      try {
        pair[1]();
      } catch (e) {
        if (window.console && console.error) {
          console.error("LinWorkspace: the " + pair[0] + " panel failed to wire", e);
        }
      }
    });

    await refreshProjects();
    renderPortfolio();
  }

  function switchPanel(name) {
    document.querySelectorAll("#ws-project-tabs button").forEach(function (b) {
      b.classList.toggle("active", b.dataset.wstab === name);
    });
    document.querySelectorAll("#wstab-upload, #wstab-files, #wstab-documents, #wstab-detail, "
                              + "#wstab-decision")
      .forEach(function (p) {
        p.classList.toggle("active", p.id === "wstab-" + name);
      });
    // The Files tab fetches the tree on reveal rather than on every project-page visit, the
    // same posture the decision sequence below takes.
    if (name === "files" && window.LinFiles && LinFiles.mount) {
      try { LinFiles.mount(); } catch (e) { /* a render fault must not trap the tab */ }
    }
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
    ["ws-upload-project", "ws-files-project", "ws-docs-project",
     "ws-detail-project"].forEach(function (id) {
      var sel = $(id);
      if (sel) sel.value = pid;
    });
    var p = (STATE.projects || []).filter(function (x) { return x.project_id === pid; })[0];
    if (p) {
      var t = $("ws-project-title"); if (t) t.textContent = p.name || "Project";
      var s = $("ws-project-sub");
      if (s) {
        var ln = window.linLocationNote ? linLocationNote(p) : null;
        s.textContent = (p.sector ? p.sector + " · " : "") + "Period " + (p.period || 1)
          + (ln && ln.kind === "matched" ? " · " + ln.text
             : ln && ln.kind === "stale" ? " · Map position is for the previous address"
             : p.geocodeError ? " · No map position" : "");
      }
    }
    if (window.LinApp && LinApp.showPage) LinApp.showPage("project");
    switchPanel("upload");
    onUploadProjectChange();
    onDocsProjectChange();
    onDetailProjectChange();
  }

  window.LinWorkspace = { boot: boot, openProject: openProject, switchPanel: switchPanel,
    // Shared with training mode (run 5): the same names, the same rows, the same ledger.
    buildProjectDetailHtml: buildProjectDetailHtml, wireCategoryRows: wireCategoryRows,
    moduleName: moduleName,
    categoryName: categoryName, groupName: groupName, statusDotColor: statusDotColor,
    // Exported so the render harness can drive them directly. Both draw from a server response
    // and both are surfaces that would fail silently: a failure list that renders nothing looks
    // exactly like a period in which nothing failed, and a schedule that draws every row looks
    // fine until the schedule has a thousand of them.
    renderFailedUploads: renderFailedUploads, renderScheduleDisplay: renderScheduleDisplay };

  /* ============================================================
     Part 1 — project list and creation
     ============================================================ */

  function wireProjectsPanel() {
    // THE CREATE-PROJECT CARD IS GONE FROM THIS PAGE and this wiring outlived it.
    // It was removed as a duplicate of the flyout's "+ New Project"; the handler below kept
    // reaching for `ws-create-btn`, so this function threw on every boot. `boot()` calls it
    // FIRST, so the throw took `wireUploadPanel`, `wireDocumentsPanel`, `wireDetailPanel`,
    // `refreshProjects` and `renderPortfolio` down with it: every project picker on this page
    // rendered zero options and the reporting-period controls beside them were never wired.
    // That is what "the period control does not work" was. Guarded rather than deleted, because
    // the card is still mounted on the operational build of this page in some deployments.
    if (!$("ws-create-btn")) return;
    $("ws-create-btn").addEventListener("click", async function () {
      var name = $("ws-new-name").value.trim();
      var sector = $("ws-new-sector").value.trim();
      var address = $("ws-new-address") ? $("ws-new-address").value.trim() : "";
      var errEl = $("ws-create-error");
      errEl.style.display = "none";
      if (!name) { errEl.textContent = "Name is required."; errEl.style.display = "block"; return; }
      $("ws-create-btn").disabled = true;
      var resp = await call("projectcreate", { name: name, sector: sector, address: address });
      $("ws-create-btn").disabled = false;
      if (!resp || resp.ok !== true) {
        errEl.className = "ws-error";
        errEl.textContent = (resp && resp.error) || "Could not create project.";
        errEl.style.display = "block";
        return;
      }
      // The project was created either way. If the address could not be resolved, say so here
      // rather than letting the PM discover later that their project is missing from the map.
      // This is shown in the error slot but is not a failure: the sentence says what happened.
      // The geocoder's top hit is not always the right one, and a wrong pin looks exactly like
      // a right one. Show what was MATCHED so the PM can see it now, while they still have the
      // address in mind, rather than discovering it on a map later.
      // Colour has to match meaning. This slot is the error slot, so anything put in it reads
      // as a failure unless the class is changed: a successful match shown in red says the
      // opposite of what it means, and "no map position" is amber because the project is fine
      // and only its position is missing.
      if (resp.geocodeError) {
        errEl.className = "ws-note ws-geo-warn";
        errEl.textContent = "Project created. " + resp.geocodeError;
        errEl.style.display = "block";
      } else if (resp.formattedAddress) {
        errEl.className = "ws-note";
        errEl.textContent = "Project created. Matched to: " + resp.formattedAddress;
        errEl.style.display = "block";
      }
      $("ws-new-name").value = "";
      $("ws-new-sector").value = "";
      if ($("ws-new-address")) $("ws-new-address").value = "";
      await refreshProjects();
    });
  }

  async function refreshProjects() {
    var resp = await call("workspaceprojects");
    if (!resp || resp.ok !== true) {
      // The single consolidated project list lives on the portfolio stage
      // (buildFallbackList in app.js). Nothing to render here on failure; the
      // stage list still shows whatever the portfolio snapshot loaded.
      window.LIN_PM_META = window.LIN_PM_META || {};
      return;
    }
    STATE.projects = resp.projects || [];
    // The former "Your projects" card duplicated the stage project list. It is
    // gone; the membership-only columns it carried (PM role, current period,
    // computed state) are now merged onto the single stage list. This map keys
    // those columns by project code (project_id === legacy_id === the stage
    // list's own id) so buildFallbackList can read them.
    var meta = {};
    STATE.projects.forEach(function (p) {
      meta[String(p.project_id)] = {
        role: p.project_role,
        period: p.period,
        computed: !!p.computed
      };
    });
    window.LIN_PM_META = meta;
    if (window.LinApp && LinApp.buildFallbackList) LinApp.buildFallbackList();
    populateProjectPickers();
    renderPortfolio();
  }

  function populateProjectPickers() {
    [["ws-upload-project", onUploadProjectChange],
     ["ws-files-project", onFilesProjectChange],
     ["ws-docs-project", onDocsProjectChange],
     ["ws-detail-project", onDetailProjectChange]].forEach(function (pair) {
      if (!$(pair[0])) return;
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

  // The Files tab owns its own rendering (assets/js/files.js); the workspace only tells it the
  // project changed, so the two do not both hold a copy of the tree.
  function onFilesProjectChange() {
    if (window.LinFiles && LinFiles.mount) {
      try { LinFiles.mount(); } catch (e) { /* a render fault must not trap the tab */ }
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
      var resp = await call("projectcompute", { id: pid, period: selectedPeriod().period });
      $("ws-compute-btn").disabled = false;
      var note = $("ws-compute-note");
      if (!resp || resp.ok !== true) {
        note.textContent = (resp && resp.error) || "Compute failed.";
        note.className = "ws-error";
      } else if (resp.recomputed) {
        note.textContent = "Recomputed. " + (resp.reason || "Documents changed") +
          ". Project status: " + (resp.project_status || "—");
        note.className = "ws-note";
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

    var resp = await call("projectuploadstatus", { id: pid, period: selectedPeriod().period });
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
    renderFailedUploads(resp.failed || []);
    renderScheduleDisplay(resp.schedule);
  }

  // The files that did not make it, read from the server's upload attempt record.
  //
  // THIS CANNOT BE DERIVED FROM WHAT IS STORED. Extraction refuses a whole document rather
  // than storing part of it, so a failed document has no row anywhere else and is simply
  // absent. The attempt is recorded when it is made, which is why this list survives the
  // dialog closing, the page reloading, and someone else opening the project tomorrow.
  //
  // RETRY IS PER DOCUMENT. Each row carries its own file input, so one document is retried on
  // its own rather than the batch being uploaded again. Nothing here is gated on
  // window.confirm: a browser that suppresses dialogs returns false from it, and an action
  // behind that is an action nobody can take.
  function renderFailedUploads(failed) {
    var target = $("ws-upload-failed");
    if (!target) return;
    if (!failed.length) { target.innerHTML = ""; return; }
    target.innerHTML =
      '<p class="ws-error" id="ws-upload-failed-head"><strong>' + failed.length +
      " document(s) did not make it. Each can be retried on its own.</strong></p>" +
      failed.map(function (f, i) {
        return '<div class="ws-file-row ws-upload-failed-row" data-failed-name="' +
          esc(f.filename) + '">' +
          "<span>" + esc(f.filename) + "</span>" +
          '<span class="ws-note ws-upload-failed-reason">' + esc(f.error || "no reason recorded") +
          "</span>" +
          '<label class="ws-note" style="text-decoration:underline; cursor:pointer;">' +
          "Retry this document" +
          '<input type="file" class="ws-retry-input" data-retry-index="' + i +
          '" style="display:none;"></label></div>';
      }).join("");
    Array.prototype.forEach.call(target.querySelectorAll(".ws-retry-input"), function (input) {
      input.addEventListener("change", function () {
        if (input.files && input.files.length) handleFiles([input.files[0]]);
      });
    });
  }

  // The period's schedule, drawn to the server's stated rule and never row by row.
  //
  // The row count is unbounded — a real construction schedule carries hundreds or thousands of
  // activities — so the server decides which rows earn a line and says how many it left in the
  // store. Drawing all of them would be the same unbounded failure as asking a model to retype
  // them.
  function renderScheduleDisplay(schedule) {
    var target = $("ws-schedule-display");
    if (!target) return;
    if (!schedule || !schedule.shown || !schedule.shown.length) {
      target.innerHTML = "";
      return;
    }
    var rows = schedule.shown.map(function (a) {
      var slip = a.slip_days ? a.slip_days + " day(s) later than last period" : "";
      return '<div class="ws-file-row ws-schedule-row"><span>' + esc(a.activity_key) + "</span>" +
        '<span class="ws-note">' + esc(a.description || "") + "</span>" +
        '<span class="ws-note">' + esc(a.current_finish || "not read") +
        (a.current_finish_kind === "actual" ? " (actual)" : "") + "</span>" +
        '<span class="ws-note">' + esc(slip || (a.shown_because || []).join("; ")) + "</span>" +
        "</div>";
    }).join("");
    target.innerHTML =
      '<p class="ws-note" id="ws-schedule-head"><strong>Schedule: ' + schedule.shown.length +
      " of " + schedule.total + " activities shown</strong>" +
      (schedule.not_shown ? ", " + schedule.not_shown +
        " stored and not drawn" : "") +
      (schedule.unusable ? ", " + schedule.unusable +
        " unusable because the source states no readable finish date" : "") + ".</p>" +
      '<p class="ws-note" id="ws-schedule-rule">' + esc(schedule.rule || "") + "</p>" + rows;
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

    // THE PERIOD IS THE ONE THE PERSON STATED, not a constant. This call sent `period: 1`
    // unconditionally, and the Files tab sent no period at all, so every document a project
    // ever uploaded landed in period one: a project holding several reporting periods computed
    // as a single period and every cross-period reader saw one point where there should have
    // been several.
    var stated = selectedPeriod();
    var resp = await call("projectupload", {
      id: pid, period: stated.period, period_end: stated.periodEnd, documents: documents
    });

    progress.style.display = "none";
    $("ws-upload-input").value = "";

    if (!resp || resp.ok !== true) {
      errEl.textContent = (resp && resp.error) || "Upload failed.";
      errEl.style.display = "block";
      return;
    }

    var s = resp.summary || {};
    // `recognized`, not `recognised`. The server has always spelled this key the American way
    // and this line read the British one, so every upload reported "undefined of 27 recognized
    // from cache" — a sentence that describes nothing that happened.
    label.textContent = s.recognized + " of " + s.total + " recognized from cache, " +
      s.extracted + " extracted fresh" +
      (s.failed ? ", " + s.failed + " failed" : "") +
      (s.unmapped ? ", " + s.unmapped + " unmapped" : "") +
      " (" + (resp.extraction_seconds != null ? resp.extraction_seconds.toFixed(1) : "?") + "s).";

    renderUploadFiles(resp.files || []);
    renderDateMismatches(resp.date_mismatches || []);
    await onUploadProjectChange();
  }

  /* The reporting period the person stated, read from the two controls on the panel.

     The number falls back to 1 only when the field has been emptied, which keeps a malformed
     entry from posting NaN; it is not a silent default for "unstated", because the field
     carries a value from the moment the panel renders and the person can see it. The ending
     date is optional: without it the platform has nothing to measure a document's own date
     against, and it says nothing rather than guessing at a period boundary. */
  function selectedPeriod() {
    var numEl = $("ws-upload-period");
    var endEl = $("ws-upload-period-end");
    var n = numEl ? parseInt(numEl.value, 10) : 1;
    if (!isFinite(n) || n < 1) n = 1;
    return { period: n, periodEnd: (endEl && endEl.value) ? endEl.value : null };
  }

  /* Documents whose own date disagrees with the period they were filed to. Every one of them
     WAS stored, in the period that was stated; this is the notice, not a refusal. */
  function renderDateMismatches(list) {
    var host = $("ws-upload-date-mismatch");
    if (!host) return;
    if (!list.length) { host.innerHTML = ""; host.style.display = "none"; return; }
    host.style.display = "";
    host.innerHTML =
      '<p class="ws-note" style="color:var(--status-amber);">'
      + list.length + " document(s) are dated outside the reporting period you filed them to. "
      + "They have been stored in that period. Check whether this is a filing mistake.</p>"
      + '<ul class="ws-note" style="margin:4px 0 0 18px;">'
      + list.map(function (m) {
          return "<li>" + esc(m.filename) + ": " + esc(m.reason) + "</li>";
        }).join("")
      + "</ul>";
  }

  function renderUploadFiles(files) {
    var html = files.map(function (f) {
      var tag, note;
      if (f.status === "failed") {
        tag = '<span class="ws-note" style="color:var(--status-red);">failed</span>';
        note = f.error || "extraction failed";
      } else if (f.status === "filed") {
        // A reference document: stored and placed, with no extraction attempted. It must not
        // read as "newly extracted", which would claim a model call that never happened.
        tag = '<span class="ws-note">filed, not analysed</span>';
        note = f.note || "filed as reference material";
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
    var resp = await call("projectuploadstatus", { id: pid, period: selectedPeriod().period });
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
    var resp = await call("projectresults", { id: pid, period: selectedPeriod().period });
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
    $("ws-detail-body").innerHTML = buildProjectDetailHtml(r);
  }

  // The one ledger-and-rollup builder, shared with training mode (run 5): the trainee reads
  // the SAME instrument a real project renders, not a training-only imitation. Returns html;
  // the caller owns where it lands.
  // Severity order, for naming the most severe contributor to a category. This is NOT how the
  // category status is decided: that is an evidence combination (Dempster-Shafer, Red weighted
  // 1.5x), and it is measurably NOT the worst contributor — on training data the two differ in
  // 47 of 80 categories, including a category with a Red contributor fusing to Green. So the
  // detail below names the most severe contributor as the most severe contributor, and says
  // plainly when the category status differs from it, rather than implying a maximum.
  var SEVERITY = { green: 0, yellow: 1, amber: 2, red: 3 };
  function severityOf(status) { return SEVERITY[String(status || "").toLowerCase()]; }

  function categoryDetailHtml(catId, entries, abstainedIds) {
    var withStatus = entries.filter(function (m) { return severityOf(m.status_color) != null; });
    var worst = null;
    withStatus.forEach(function (m) {
      if (!worst || severityOf(m.status_color) > severityOf(worst.status_color)) worst = m;
    });
    var rows = withStatus.slice().sort(function (a, b) {
      return severityOf(b.status_color) - severityOf(a.status_color);
    }).map(function (m) {
      var mark = (worst && m === worst)
        ? '<span class="ws-note ws-worst"> (most severe contributor)</span>' : "";
      return '<div class="ws-module"><span class="ws-dot" style="background:' +
        statusDotColor(m.status_color) + ';"></span><span class="ws-mname">' +
        esc(moduleName(m.module_id)) + "</span>" + mark +
        '<span class="ws-note">' + esc(m.evidence_metric || "") + "</span></div>";
    }).join("");
    // An abstention is a NAMED ABSENCE: no value, no colour, no dot.
    var abstained = (abstainedIds || []).map(function (id) {
      return '<div class="ws-module ws-abstained"><span class="ws-mname">' +
        esc(moduleName(id)) + '</span><span class="ws-note">abstained: no usable input this ' +
        "period</span></div>";
    }).join("");
    return '<div class="ws-cat-detail" data-cat-detail="' + esc(catId) + '" hidden>' +
      (rows || '<p class="ws-note">No computation in this category produced a status.</p>') +
      abstained + "</div>";
  }

  // opts.abstained: {categoryId: [moduleId, ...]} — which computations abstained this period.
  // opts.expandable: render each category as a disclosure carrying its contributors.
  function buildProjectDetailHtml(r, opts) {
    opts = opts || {};
    var abstainedMap = opts.abstained || {};
    var modsByCat = {};
    (Array.isArray(r.module_results) ? r.module_results : []).forEach(function (m) {
      var c = m.category || String(m.module_id || "").split(".")[0];
      (modsByCat[c] = modsByCat[c] || []).push(m);
    });
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
        if (!opts.expandable) {
          html += '<div class="ws-module"><span class="ws-dot" style="background:' +
            statusDotColor(e.c.status) + ';"></span>' +
            '<span class="ws-mname">' + esc(categoryName(e.catId)) + "</span>" + note + "</div>";
          return;
        }
        var contributors = modsByCat[e.catId] || [];
        var worst = null;
        contributors.forEach(function (m) {
          if (severityOf(m.status_color) == null) return;
          if (!worst || severityOf(m.status_color) > severityOf(worst.status_color)) worst = m;
        });
        // The teaching line: when the fused status differs from the most severe contributor,
        // say so. That difference is the instrument's actual behaviour and a trainee who
        // reads the category as a maximum is reading it wrong.
        var divergence = "";
        if (worst && String(worst.status_color).toLowerCase() !==
            String(e.c.status || "").toLowerCase()) {
          divergence = '<div class="ws-note ws-cat-divergence">Combined from ' +
            contributors.length + " computations by evidence combination, not by taking the " +
            "worst: " + esc(moduleName(worst.module_id)) + " reports " +
            esc(worst.status_color) + ".</div>";
        }
        html += '<div class="ws-module ws-cat-row" data-cat="' + esc(e.catId) + '" ' +
          'role="button" tabindex="0" aria-expanded="false">' +
          '<span class="ws-dot" style="background:' + statusDotColor(e.c.status) + ';"></span>' +
          '<span class="ws-mname">' + esc(categoryName(e.catId)) + "</span>" + note +
          '<span class="ws-note ws-cat-toggle">show the computations</span></div>' +
          divergence +
          categoryDetailHtml(e.catId, contributors, abstainedMap[e.catId]);
      });
      html += "</div>";
    });

    // Module results, grouped by group letter (from each module's own "group" field, not the
    // module id) — names only.
    var modules = opts.expandable ? null : r.module_results;
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

    return html;
  }

  // Disclosure wiring for the expandable category rows, shared with training mode.
  function wireCategoryRows(root) {
    if (!root) return;
    root.querySelectorAll("[data-cat]").forEach(function (row) {
      function toggle() {
        var detail = root.querySelector('[data-cat-detail="' + row.dataset.cat + '"]');
        if (!detail) return;
        var open = detail.hasAttribute("hidden");
        detail.toggleAttribute("hidden", !open);
        row.setAttribute("aria-expanded", String(open));
        var t = row.querySelector(".ws-cat-toggle");
        if (t) t.textContent = open ? "hide the computations" : "show the computations";
      }
      row.addEventListener("click", toggle);
      row.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(); }
      });
    });
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
    // Portfolio Health is a property of the whole portfolio, not of each project:
    // when the portfolio is too small (or the snapshot is otherwise unavailable),
    // every project returns the SAME insufficient-data reason. Say it once for the
    // portfolio rather than repeating it per project. Only projects that actually
    // carry a computed snapshot get their own card.
    var computed = [];
    var portfolioNote = null;
    rows.forEach(function (row) {
      var p = row.project, resp = row.resp;
      if (!resp || resp.ok !== true) {
        if (!portfolioNote) portfolioNote = "Portfolio Health has not been computed yet.";
        return;
      }
      var snap = resp.result.portfolio_snapshot;
      if (!snap || snap.insufficient_data) {
        if (!portfolioNote) {
          portfolioNote = (snap && snap.message) ? snap.message :
            "Portfolio Health has not been computed for this portfolio.";
        }
        return;
      }
      computed.push({ project: p, snap: snap });
    });

    var html = "";
    if (portfolioNote) {
      html += '<p class="ws-note">' + esc(portfolioNote) + "</p>";
    }
    html += computed.map(function (row) {
      var p = row.project, snap = row.snap;
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

    listEl.innerHTML = html || '<p class="ws-empty">You are not the PM of any project yet.</p>';
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
