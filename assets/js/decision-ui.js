/* ============================================================
   Opus Gubernatio — decision-ui.js (T4)
   ------------------------------------------------------------
   The decision sequence:

     evidence -> preliminary judgment -> LOCK -> reveal -> decision -> advance

   THE THREE PROPERTIES THIS FILE IS RESPONSIBLE FOR
   -------------------------------------------------

   1. THE PACKAGE DOES NOT REACH THE CLIENT BEFORE THE LOCK.
      There is exactly one call in this file that can return package content —
      `revealPackage()`, wired to a button the participant presses themselves
      after locking. Nothing calls it on load, nothing prefetches it, and there
      is no markup for it in index.html: the package DOM is constructed from
      the response and appended only then. A refused request would itself be a
      disclosure ("something exists to be refused"), so this file does not make
      one speculatively either.

   2. THE CLIENT COMPUTES NO STAGE.
      `render()` switches on `state.current_stage`, which comes from
      researchsequencestate and is derived server-side from the decisions row.
      This file never infers a stage from what it just did, never caches one,
      and after every mutation it re-reads the server rather than assuming the
      transition succeeded. A participant who reloads, signs out and in, or
      returns in a week lands wherever the rows say they are.

   3. THE LOCK IS A ONE-WAY DOOR IN THE INTERFACE TOO.
      On lock, the preliminary-judgment card is REMOVED from the DOM
      (`el.remove()`), not hidden. There is no edit control, no draft, no back
      navigation, and the server never returns the locked pre_action or
      pre_confidence, so there is nothing for a form to repopulate even if one
      were reintroduced by mistake.

   NO SESSION TIMEOUT, AND NO WARNING THAT IMPLIES ONE.
   A session that expires mid-decision destroys a data point. There is
   deliberately no idle timer, no countdown, and no "you will be signed out"
   message anywhere in this file.

   NO CLIENT-SIDE COMPUTATION. Every number rendered comes from a stored
   computed_results row via projectresults. sim.js / simulations.js /
   categories.js are not loaded on this route.
   ============================================================ */

(function () {
  "use strict";

  /* ---------- module and category NAMES (never ids) ----------
     Same table T3/T5 established, and for the same reason: the analytical
     layer's ids (A1.1, B4.4) must never appear in participant-facing text, and
     loading categories.js to get the names would pull in the client-side
     simulation bundle this route must not have. Names only — no thresholds, no
     formulas, no computation. */

  var GROUP_NAMES = {
    A: "Project Health",
    B: "Recommendation and Governance",
    C: "Data and Evidence Health",
    D: "Portfolio Level"
  };
  var GROUP_ORDER = ["A", "B", "C", "D"];
  var CATEGORY_NAMES = {
    A1: "Cost and EVM Performance", A2: "Schedule Performance", A3: "Cost Risk",
    A4: "Document-Derived Condition Signals", A5: "System Dynamics and Complexity",
    A6: "Delivery Quality Performance",
    B1: "Signal Synthesis", B2: "Evidence Combination",
    B3: "Regulatory and Authority Thresholds", B4: "Decision Optimization",
    C1: "Data Integrity", D1: "Portfolio Health"
  };
  var MODULE_NAMES = {
    "A1.1": "Monte Carlo EAC", "A1.2": "CUSUM Anomaly Monitor", "A1.3": "Bayesian EAC",
    "A1.4": "Kalman Filter SPI Smoother", "A1.5": "ARIMA CPI Forecast",
    "A1.6": "Earned Schedule", "A1.7": "TCPI", "A1.8": "Variance at Completion",
    "A1.9": "Budget Execution Rate", "A1.10": "Regression to Mean CPI", "A1.11": "ICE Ratio",
    "A2.1": "PERT Network Criticality", "A2.2": "Line of Balance",
    "A2.3": "CCPM Buffer Health", "A2.4": "Schedule Compression Index",
    "A2.5": "Float Consumption Rate", "A2.6": "S-Curve Deviation",
    "A2.7": "Milestone Trend Analysis", "A2.8": "Look-Ahead Schedule Health",
    "A2.9": "Resource Loading Index", "A2.10": "Schedule Risk Analysis P80",
    "A2.11": "Critical Path Index",
    "A3.1": "Reference Class Forecasting", "A3.2": "Contingency Burn Rate",
    "A3.3": "Labor Productivity Index", "A3.4": "Material Cost Variance",
    "A3.5": "Overhead Absorption Rate", "A3.6": "Cost Risk Analysis P80",
    "A3.7": "Analogous Estimating Ratio", "A3.8": "Parametric Cost Index",
    "A3.9": "Inflation Adjustment Index",
    "A4.1": "Document Risk Score", "A4.2": "RFI Velocity",
    "A4.3": "Submittal Rejection Rate", "A4.4": "NCR Rate", "A4.5": "Weather Day Impact",
    "A4.6": "Change Order Frequency", "A4.7": "Dispute Escalation Index",
    "A4.8": "Subcontractor Performance", "A4.9": "Procurement Lead Time Monitor",
    "A4.10": "Specification Conflict Density",
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
    "B2.12": "Hesitant Fuzzy Sets", "B2.13": "Type-2 Fuzzy Sets",
    "B2.14": "Maximum Entropy", "B2.15": "Possibility Theory",
    "B2.16": "Spherical Fuzzy Sets", "B2.17": "Fermatean Fuzzy Sets",
    "B2.18": "MARCOS Ranking", "B2.19": "CRITIC-TOPSIS", "B2.20": "Hypersoft Sets",
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

  function moduleName(id) { return MODULE_NAMES[id] || "Analytical module"; }
  function categoryName(id) { return CATEGORY_NAMES[id] || "Uncategorised"; }
  function groupName(id) { return GROUP_NAMES[id] || ""; }

  function statusColor(status) {
    var s = String(status || "").toLowerCase();
    if (s.indexOf("green") >= 0) return "var(--status-green)";
    if (s.indexOf("yellow") >= 0) return "var(--status-yellow)";
    if (s.indexOf("amber") >= 0) return "var(--status-amber)";
    if (s.indexOf("red") >= 0) return "var(--status-red)";
    if (s.indexOf("complete") >= 0) return "var(--status-complete)";
    return "var(--status-nodata)";
  }

  /* ---------- helpers ---------- */

  function $(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function humanise(token) {
    return String(token || "").replace(/[_-]/g, " ")
      .replace(/\b\w/g, function (m) { return m.toUpperCase(); });
  }
  function token() { return window.LinAuth ? LinAuth.getToken() : null; }
  function call(action, extra) {
    return LinStore.postWithTimeout(
      Object.assign({ action: action, session_token: token() }, extra || {}), 60000);
  }

  /* ---------- state ----------
     `STATE.server` is the last researchsequencestate response and is the ONLY
     source of stage. `STATE.evidenceLabels` is what the evidence screen actually
     displayed, so the decision form can offer exactly those items and nothing
     the participant never saw. */
  var STATE = { server: null, evidenceLabels: [] };

  // T6. decision.html is gone. This renders into the Period decision tab of the Project page,
  // so the sequence is a step in the period rather than a place a participant navigates to —
  // which is the point: T4 put a page load between forming a judgment and recording it.
  //
  // Every former gate used to be a message plus a link to another page. There are no other
  // pages now, so a gate states the position and stops. The two that pointed at
  // questionnaires.html are gone entirely: the profile is captured before any of this can be
  // reached, and the server refuses a preliminary judgment without it regardless.
  var wired = false;

  // Hides the sequence and states why, WITHOUT rewriting #dc-root — the stage cards are markup
  // in index.html now, and blowing them away would mean they could never come back when the
  // reason for the gate cleared.
  function gate(message) {
    ["dc-evidence", "dc-prejudgment", "dc-reveal", "dc-decide", "dc-advance"].forEach(
      function (id) { var el = $(id); if (el) el.style.display = "none"; });
    var rail = document.querySelector("#dc-root .dc-rail");
    if (rail) rail.style.display = "none";
    var note = $("dc-position");
    if (note) note.textContent = message;
  }

  // NAMED `mount`, NOT `render`. This file already has an internal `render()` at the foot of the
  // stage machinery, and a second `function render()` in the same scope silently replaces it —
  // function declarations hoist, so the LAST one wins and the export below would have captured
  // the internal stage renderer instead of this entry point. That fails at the first call with
  // "cannot read current_stage of null", because the stage renderer assumes STATE.server is
  // already populated and only refresh() populates it.
  async function mount() {
    if (!token()) { gate("You need to be signed in to work on a decision."); return; }
    if (!wired) { wire(); wired = true; }
    await refresh();
  }

  window.LinDecisionUI = { mount: mount };

  /* Re-read the server and re-render. Called on load and after EVERY mutation —
     never assume a transition succeeded, ask. */
  async function refresh() {
    var state = await call("researchsequencestate");
    if (!state || state.ok !== true) {
      gate((state && state.error) || "Could not read your current position.");
      return;
    }
    STATE.server = state;

    // ORDER MATTERS HERE, and it was wrong.
    //
    // The intake check used to come first, so anyone without an assignment was told to record a
    // background profile before their first decision. For an OPERATIONAL user that is a dead
    // end: they never complete intake, because the profile is only ever offered to a consented
    // research account and an operational account can never obtain a consents row. A director
    // opening a project they created was told to do something they cannot do, about a decision
    // they were never going to make.
    //
    // Whether an assignment exists is now asked first, because it is the question that decides
    // whether the sequence applies at all. Only once we know it applies is it worth saying what
    // is missing before it can start.
    if (!state.assignment) {
      // Covers both "never assigned" and "nothing assigned any more". The sequence is recorded
      // against a scenario, not against a project, so this is the honest sentence for an
      // operational user with their own project AND for a participant awaiting assignment.
      // The old wording claimed every period was complete, which for someone who was never
      // assigned anything was simply untrue.
      gate(state.all_assignments_complete && state.current_sequence_number !== null
        ? "You have completed every period assigned to you."
        : "No decision sequence is assigned to this account. Period decisions are recorded "
          + "against a scenario the researcher assigns.");
      return;
    }
    if (!state.intake_completed) {
      // Now meaningful: there IS an assignment, so intake genuinely is the thing standing in
      // the way. The overlay normally captures it before the application is usable; this branch
      // only fires if that was somehow bypassed.
      gate("Your background profile has to be recorded before your first decision.");
      return;
    }

    $("dc-position").textContent =
      "Project " + state.current_sequence_number + " · period "
      + String(state.period || "").replace(/^P/, "")
      + (state.period_count ? " of " + state.period_count : "");

    await render();
  }

  function setRail(stage) {
    var order = ["evidence", "prejudgment", "reveal", "decide"];
    var current = { evidence: "evidence", awaiting_reveal: "reveal",
                    deciding: "decide", complete: "decide" }[stage] || "evidence";
    var idx = order.indexOf(current);
    document.querySelectorAll(".dc-rail-step").forEach(function (el) {
      var i = order.indexOf(el.dataset.step);
      el.classList.toggle("done", i < idx || stage === "complete");
      el.classList.toggle("active", i === idx && stage !== "complete");
    });
  }

  /* THE RENDER SWITCH. Reads server stage only. */
  async function render() {
    var state = STATE.server;
    var stage = state.current_stage;
    setRail(stage);

    await renderEvidence();

    show("dc-prejudgment", stage === "evidence");
    show("dc-reveal", stage === "awaiting_reveal" || stage === "deciding"
                      || stage === "complete");
    show("dc-decide", stage === "deciding");
    show("dc-advance", stage === "complete");

    if (stage === "evidence") {
      renderPreForm();
    } else {
      // Past the lock: remove the form from the document entirely. Hiding it would
      // leave a submittable form in the DOM.
      var pre = $("dc-prejudgment");
      if (pre && pre.parentNode) pre.parentNode.removeChild(pre);
    }

    if (stage === "awaiting_reveal") {
      $("dc-reveal-sub").textContent =
        "Your preliminary judgment is locked. The decision support package for this period "
        + "is available when you are ready to see it.";
      $("dc-reveal-btn").style.display = "";
      $("dc-package").innerHTML = "";
    } else if (stage === "deciding" || stage === "complete") {
      // Already revealed in a previous visit — re-fetch is safe and does not move
      // reveal_at (the server returns already_revealed and leaves the timestamp).
      $("dc-reveal-btn").style.display = "none";
      if (!$("dc-package").innerHTML) await revealPackage(true);
    }

    if (stage === "deciding") renderDecideForm();
    if (stage === "complete") renderAdvance();
  }

  function show(id, on) {
    var el = $(id);
    if (el) el.style.display = on ? "" : "none";
  }

  /* ============================================================
     Part 1 — evidence
     ============================================================ */

  async function renderEvidence() {
    var state = STATE.server;
    var pid = state.evidence_project_id;
    $("dc-evidence-sub").textContent =
      "The stored analysis for this period. Nothing on this page is recalculated in your "
      + "browser.";

    if (!pid) {
      $("dc-evidence-body").innerHTML =
        '<p class="dc-empty">No evidence project is attached to this period.</p>';
      return;
    }

    var res = await call("projectresults", { id: pid, period: 1 });
    var docs = await call("projectuploadstatus", { id: pid, period: 1 });

    var html = "";
    var labels = [];

    if (res && res.ok === true) {
      var r = res.result;
      html += '<div class="dc-row"><strong style="flex:1;">Overall project status</strong>' +
        '<span class="dc-dot" style="background:' + statusColor(r.project_status) +
        ';"></span> ' + esc(r.project_status || "—") + "</div>";

      var cats = r.category_statuses || {};
      var byGroup = {};
      Object.keys(cats).forEach(function (catId) {
        var c = cats[catId];
        var g = c.group || catId.charAt(0);
        (byGroup[g] = byGroup[g] || []).push({ id: catId, c: c });
      });
      GROUP_ORDER.forEach(function (g) {
        var entries = byGroup[g];
        if (!entries || !entries.length) return;
        html += '<div class="dc-group"><h3>' + esc(groupName(g)) + "</h3>";
        entries.forEach(function (e) {
          var name = categoryName(e.id);
          labels.push(name);
          var informational = e.c.contributes_to_project_status === false
            ? '<span class="dc-note"> (informational, does not affect project status)</span>'
            : "";
          html += '<div class="dc-row"><span class="dc-dot" style="background:' +
            statusColor(e.c.status) + ';"></span><span class="dc-row-name">' + esc(name) +
            "</span>" + informational + "</div>";
        });
        html += "</div>";
      });

      var mods = r.module_results;
      if (Array.isArray(mods) && mods.length) {
        var modsByGroup = {};
        mods.forEach(function (m) {
          var g = m.group || String(m.module_id || "").charAt(0);
          (modsByGroup[g] = modsByGroup[g] || []).push(m);
        });
        html += '<div class="dc-group"><h3>Analytical findings</h3>';
        GROUP_ORDER.forEach(function (g) {
          var list = modsByGroup[g];
          if (!list || !list.length) return;
          html += '<div class="dc-note" style="margin:10px 0 2px;">' + esc(groupName(g)) +
            "</div>";
          list.forEach(function (m) {
            html += '<div class="dc-row"><span class="dc-dot" style="background:' +
              statusColor(m.status_color) + ';"></span><span class="dc-row-name">' +
              esc(moduleName(m.module_id)) + "</span>" +
              '<span class="dc-note">' + esc(m.evidence_metric || "") + "</span></div>";
          });
        });
        html += "</div>";
      }

      html += '<p class="dc-note" style="margin-top:14px;">Stored result, computed ' +
        esc(r.computed_at ? new Date(r.computed_at).toLocaleString() : "—") + ".</p>";
    } else {
      html += '<p class="dc-empty">No stored analysis for this period yet.</p>';
    }

    if (docs && docs.ok === true && (docs.documents || []).length) {
      html += '<div class="dc-group dc-doclist"><h3>Source documents</h3>';
      docs.documents.forEach(function (d) {
        labels.push(d.filename);
        var url = "/documents/" + encodeURIComponent(d.document_id) + "/content"
          + "?project_id=" + encodeURIComponent(pid)
          + "&session_token=" + encodeURIComponent(token());
        html += '<div class="dc-row"><span class="dc-row-name">' +
          (d.document_id ? '<a href="' + url + '" target="_blank" rel="noopener">' +
            esc(d.filename) + "</a>" : esc(d.filename)) + "</span>" +
          '<span class="dc-note">' + esc(d.doc_type) + "</span></div>";
      });
      html += "</div>";
    }

    STATE.evidenceLabels = labels;
    $("dc-evidence-body").innerHTML = html;
  }

  /* ============================================================
     Part 2 — preliminary judgment
     ============================================================ */

  function actionOptions() {
    var v = (STATE.server.vocabularies || {}).actions || [];
    return v.map(function (a) {
      return '<option value="' + esc(a) + '">' + esc(humanise(a)) + "</option>";
    }).join("");
  }

  function renderPreForm() {
    $("dc-pre-form").innerHTML =
      '<label class="dc-label" for="dc-pre-action">Proposed action' +
      '<span class="dc-required">*</span></label>' +
      '<select id="dc-pre-action" class="dc-select">' +
      '<option value="">Select an action…</option>' + actionOptions() + "</select>" +

      '<label class="dc-label" for="dc-pre-confidence">Confidence' +
      '<span class="dc-required">*</span></label>' +
      '<div class="dc-scale"><input id="dc-pre-confidence" type="range" min="0" max="100" ' +
      'step="1" value="50"><span class="dc-scale-value" id="dc-pre-confidence-value">50' +
      "</span></div>" +

      '<label class="dc-label" for="dc-pre-assessment">Brief assessment</label>' +
      '<textarea id="dc-pre-assessment" class="dc-textarea" ' +
      'placeholder="One or two sentences on how you read this period."></textarea>';

    $("dc-pre-confidence").addEventListener("input", function () {
      $("dc-pre-confidence-value").textContent = this.value;
    });

    // Said once, plainly. The previous wording said the same thing three times — "cannot be
    // changed", then "permanently", then "no way to edit or withdraw it afterwards" — and
    // stacked emphasis reads as anxiety rather than as a clear consequence. One statement of
    // what happens, one of what follows.
    $("dc-commit-warning").innerHTML =
      "<strong>You cannot change this afterwards.</strong> Committing locks your preliminary "
      + "judgment for this period. The decision support package is shown only once it is "
      + "locked.";
  }

  async function commitPreJudgment() {
    var errEl = $("dc-pre-error");
    errEl.style.display = "none";
    var action = $("dc-pre-action").value;
    if (!action) {
      errEl.textContent = "Choose a proposed action before committing.";
      errEl.style.display = "block";
      return;
    }
    var assessment = $("dc-pre-assessment").value.trim();

    if (!window.confirm(
        "Commit your preliminary judgment?\n\n"
        + "You cannot change it afterwards. "
        + "The decision support package is shown only after this step.")) {
      return;
    }

    $("dc-commit-btn").disabled = true;
    var resp = await call("researchprejudgment", {
      pre_action: action,
      pre_confidence: Number($("dc-pre-confidence").value),
      pre_assessment: assessment
    });
    $("dc-commit-btn").disabled = false;

    if (!resp || resp.ok !== true) {
      errEl.textContent = (resp && resp.error) || "Could not commit your judgment.";
      errEl.style.display = "block";
      return;
    }
    // Do not trust the response's stage — re-read.
    await refresh();
  }

  /* ============================================================
     Part 3 — reveal
     ============================================================ */

  async function revealPackage(silent) {
    var errEl = $("dc-reveal-error");
    errEl.style.display = "none";
    var resp = await call("researchreveal");
    if (!resp || resp.ok !== true) {
      errEl.textContent = (resp && resp.error) || "Could not reveal the package.";
      errEl.style.display = "block";
      return;
    }
    renderPackage(resp.package, resp.reveal_at);
    await renderRevealedOptions();
    if (!silent) await refresh();
  }

  /* ------------------------------------------------------------
     The courses of action, generated at DISPLAY TIME from the stored result.

     The package above is the researcher-authored, frozen stimulus and is rendered exactly as
     it was frozen. This block is a different thing and is labelled as one: the courses of
     action the analytical layer scored, read back off the same stored result the evidence
     screen showed, with the consequence of each. It is generated here, on every view, by the
     same generator the operational Governance Decision card calls, so the same evidence
     produces the same words on both surfaces.

     It can only run AFTER the reveal. Before the preliminary judgment is locked the stored
     result comes back with the action-bearing module fields redacted (documents.py
     `_ACTION_KEYS`), which is what makes the pre-lock evidence screen safe; the generator then
     finds no scored courses of action and says so rather than inventing a set.
     ------------------------------------------------------------ */
  async function renderRevealedOptions() {
    var host = $("dc-options");
    if (!host) return;
    var pid = STATE.server && STATE.server.evidence_project_id;
    if (!pid) { host.innerHTML = ""; return; }
    if (!window.LinRecOptions) { host.innerHTML = ""; return; }
    var res = await call("projectresults", { id: pid, period: 1 });
    if (!res || res.ok !== true || !res.result) {
      host.innerHTML = '<p class="dc-empty" id="dc-options-empty">No stored analysis is '
        + "available for this period, so no courses of action can be laid out.</p>";
      return;
    }
    host.innerHTML = window.LinRecOptions.html(window.LinRecOptions.build(res.result));
  }

  function field(title, value) {
    if (value === null || value === undefined || value === "") return "";
    var body = (typeof value === "object")
      ? '<pre class="dc-note" style="white-space:pre-wrap; margin:4px 0 0;">' +
        esc(JSON.stringify(value, null, 2)) + "</pre>"
      : "<p style=\"margin:4px 0 0; font-size:13px;\">" + esc(value) + "</p>";
    return '<div class="dc-group"><h3>' + esc(title) + "</h3>" + body + "</div>";
  }

  function renderPackage(pkg, revealAt) {
    if (!pkg) {
      $("dc-package").innerHTML =
        '<p class="dc-empty">No package is attached to this period.</p>';
      return;
    }
    var html = '<div class="dc-locked-banner">Shown at ' +
      esc(revealAt ? new Date(revealAt).toLocaleString() : "—") +
      ". Your preliminary judgment was recorded before this point and is unchanged.</div>";
    html += field("Recommended action", pkg.recommended_action);
    html += field("Detected condition", pkg.detected_condition);
    html += field("Alternatives considered", pkg.alternatives);
    html += field("Uncertainty", pkg.uncertainty);
    html += field("Limitations", pkg.limitations);
    html += field("Where this applies", pkg.applicability_boundary);
    html += field("When this expires", pkg.expiration_trigger);
    html += field("Supporting evidence and provenance", pkg.provenance);
    html += '<p class="dc-note" style="margin-top:12px;">Model ' +
      esc(pkg.model_version || "—") + " · package version " + esc(pkg.version || "—") + "</p>";
    $("dc-package").innerHTML = html;
  }

  /* ============================================================
     Part 4 — final decision
     ============================================================ */

  function renderDecideForm() {
    var vocab = STATE.server.vocabularies || {};
    var dispositions = (vocab.dispositions || []).map(function (d) {
      return '<option value="' + esc(d) + '">' + esc(humanise(d)) + "</option>";
    }).join("");
    var reasons = (vocab.reason_codes || []).map(function (rc) {
      return '<option value="' + esc(rc) + '">' + esc(humanise(rc)) + "</option>";
    }).join("");
    var evidence = STATE.evidenceLabels.map(function (label, i) {
      return '<label class="dc-check-row"><input type="checkbox" data-evidence="1" value="' +
        esc(label) + '" id="dc-ev-' + i + '"> ' + esc(label) + "</label>";
    }).join("");

    $("dc-decide-form").innerHTML =
      '<label class="dc-label" for="dc-final-action">Final action' +
      '<span class="dc-required">*</span></label>' +
      '<select id="dc-final-action" class="dc-select">' +
      '<option value="">Select an action…</option>' + actionOptions() + "</select>" +

      '<label class="dc-label" for="dc-disposition">How did you treat the recommendation?' +
      '<span class="dc-required">*</span></label>' +
      '<select id="dc-disposition" class="dc-select">' +
      '<option value="">Select…</option>' + dispositions + "</select>" +

      '<label class="dc-label" for="dc-reason">Primary reason</label>' +
      '<select id="dc-reason" class="dc-select">' +
      '<option value="">Select…</option>' + reasons + "</select>" +

      '<label class="dc-label">Evidence you relied on</label>' +
      '<div class="dc-checks">' +
      (evidence || '<span class="dc-note">No evidence items were displayed.</span>') +
      "</div>" +

      '<label class="dc-label" for="dc-rationale">Rationale' +
      '<span class="dc-required">*</span></label>' +
      '<textarea id="dc-rationale" class="dc-textarea" ' +
      'placeholder="One or two sentences."></textarea>' +

      '<label class="dc-label" for="dc-final-confidence">Final confidence' +
      '<span class="dc-required">*</span></label>' +
      '<div class="dc-scale"><input id="dc-final-confidence" type="range" min="0" max="100" ' +
      'step="1" value="50"><span class="dc-scale-value" id="dc-final-confidence-value">50' +
      "</span></div>" +

      '<h3>If this action requires it</h3>' +
      '<label class="dc-label" for="dc-owner">Owner</label>' +
      '<input id="dc-owner" class="dc-input" placeholder="Who carries this out">' +
      '<label class="dc-label" for="dc-authority">Deciding authority</label>' +
      '<input id="dc-authority" class="dc-input" placeholder="Who authorises it">' +
      '<label class="dc-label" for="dc-deadline">By when</label>' +
      '<input id="dc-deadline" class="dc-input" placeholder="e.g. next reporting cycle">' +
      '<label class="dc-label" for="dc-residual">Residual risk</label>' +
      '<textarea id="dc-residual" class="dc-textarea" ' +
      'placeholder="What remains after this action."></textarea>';

    $("dc-final-confidence").addEventListener("input", function () {
      $("dc-final-confidence-value").textContent = this.value;
    });
  }

  async function submitDecision() {
    var errEl = $("dc-decide-error");
    errEl.style.display = "none";
    var action = $("dc-final-action").value;
    var disposition = $("dc-disposition").value;
    var rationale = $("dc-rationale").value.trim();
    var missing = [];
    if (!action) missing.push("final action");
    if (!disposition) missing.push("how you treated the recommendation");
    if (!rationale) missing.push("rationale");
    if (missing.length) {
      errEl.textContent = "Please provide: " + missing.join(", ") + ".";
      errEl.style.display = "block";
      return;
    }

    var evidence = Array.prototype.slice.call(
      document.querySelectorAll('[data-evidence]:checked')).map(function (c) {
        return c.value;
      });

    $("dc-decide-btn").disabled = true;
    var resp = await call("researchdecision", {
      final_action: action,
      disposition: disposition,
      reason_code: $("dc-reason").value || undefined,
      evidence_items: evidence,
      rationale: rationale,
      final_confidence: Number($("dc-final-confidence").value),
      owner_role: $("dc-owner").value.trim() || undefined,
      authority_role: $("dc-authority").value.trim() || undefined,
      deadline: $("dc-deadline").value.trim() || undefined,
      residual_risk: $("dc-residual").value.trim() || undefined
    });
    $("dc-decide-btn").disabled = false;

    if (!resp || resp.ok !== true) {
      errEl.textContent = (resp && resp.error) || "Could not record your decision.";
      errEl.style.display = "block";
      return;
    }
    await refresh();
  }

  /* ============================================================
     Part 5 — advance
     ============================================================ */

  function renderAdvance() {
    var state = STATE.server;
    var periodNum = parseInt(String(state.period || "P1").replace(/\D/g, ""), 10) || 1;
    var last = state.period_count && periodNum >= state.period_count;
    $("dc-advance-title").textContent = last ? "Project complete" : "Period complete";
    $("dc-advance-sub").textContent = last
      ? "This was the final period for this project."
      : "Your decision for this period is recorded and locked.";
    $("dc-advance-btn").textContent = last ? "Continue" : "Continue to the next period";
  }

  async function advance() {
    var errEl = $("dc-advance-error");
    errEl.style.display = "none";
    var state = STATE.server;
    var periodNum = parseInt(String(state.period || "P1").replace(/\D/g, ""), 10) || 1;
    var last = state.period_count && periodNum >= state.period_count;

    if (!last) {
      var resp = await call("researchadvance");
      if (!resp || resp.ok !== true) {
        errEl.textContent = (resp && resp.error) || "Could not advance.";
        errEl.style.display = "block";
        return;
      }
    }
    // On the final period there is nothing to advance to; refresh() reads the server,
    // which reports all_assignments_complete and routes to the debrief.
    await refresh();
  }

  /* ---------- wiring ---------- */

  function wire() {
    $("dc-commit-btn").addEventListener("click", commitPreJudgment);
    $("dc-reveal-btn").addEventListener("click", function () { revealPackage(false); });
    $("dc-decide-btn").addEventListener("click", submitDecision);
    $("dc-advance-btn").addEventListener("click", advance);
  }
})();
