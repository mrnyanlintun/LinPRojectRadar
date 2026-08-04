/* ============================================================
   Opus Gubernatio — training.js
   ------------------------------------------------------------
   Training mode run 2: the loop's screen. A trainee opens a
   generated project, reads the position, decides, and the next
   period renders because of that decision.

   NOT the security boundary. Every action this file posts is
   gated server-side (features.gate_action refuses a disabled
   flag, a research account, and the handlers refuse again), so
   this page only ever shows what the server was willing to say.

   Everything rendered here comes from trainingstate /
   trainingdecision responses. Nothing is computed client-side:
   the effect table lives in server/app/training_engine.py and
   this file would mislead the trainee if it restated the rules
   from memory.
   ============================================================ */
var LinTraining = (function () {
  "use strict";

  var root = null;
  var view = null;       // the latest server view of the run
  var briefOpen = false; // the brief is reachable at any point, not only at the start

  function token() {
    return (window.LinAuth && typeof LinAuth.getToken === "function")
      ? LinAuth.getToken() : null;
  }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function money(v) {
    if (v == null || isNaN(v)) return "";
    return "$" + Number(v).toLocaleString("en-US", { maximumFractionDigits: 0 });
  }

  async function call(action, extra) {
    var body = Object.assign({ action: action, session_token: token() }, extra || {});
    if (!window.LinStore || !LinStore.postWithTimeout) {
      return { ok: false, error: "Store not available." };
    }
    try { return await LinStore.postWithTimeout(body); }
    catch (e) { return { ok: false, error: "Could not reach the server." }; }
  }

  /* ---------- entry ---------- */

  async function render() {
    root = document.getElementById("training-root");
    if (!root) return;
    root.innerHTML = '<p class="kn-sub">Loading training mode…</p>';
    var status = await call("trainingstatus");
    if (!status || status.ok !== true || status.enabled !== true) {
      root.innerHTML = '<p class="login-error" style="display:block">' +
        esc((status && status.error) || "Training mode is not available for this account.") +
        "</p>";
      return;
    }
    var state = await call("trainingstate");
    if (state && state.ok === true) {
      view = state;
      paint();
    } else {
      paintStart();
    }
  }

  /* ---------- the start form ---------- */

  function paintStart() {
    root.innerHTML =
      '<div class="tr-start">' +
      '<p class="kn-sub">A practice project. The contract form decides the notice periods; ' +
      'read the brief before period one.</p>' +
      '<label class="login-field-label">Contract form</label>' +
      '<select id="tr-form" class="ig-input">' +
      '<option value="A201-2017">AIA A201-2017</option>' +
      '<option value="ConsensusDocs 200">ConsensusDocs 200</option>' +
      '<option value="Federal FAR">Federal (FAR)</option>' +
      "</select>" +
      '<label class="login-field-label">Site and market conditions</label>' +
      '<select id="tr-conditions" class="ig-input">' +
      '<option value="exacting">Exacting: tight labour, long lead exposure, formal owner</option>' +
      '<option value="steady">Steady: available labour, stocked procurement, collaborative owner</option>' +
      "</select>" +
      '<label class="login-field-label">Facility</label>' +
      '<select id="tr-facility" class="ig-input">' +
      '<option value="critical">Critical occupancy (hospital grade)</option>' +
      '<option value="standard" selected>Standard commercial occupancy</option>' +
      '<option value="utilitarian">Utilitarian occupancy (warehouse grade)</option>' +
      "</select>" +
      '<label class="login-field-label">Contract value (dollars)</label>' +
      '<input id="tr-value" class="ig-input" type="number" value="12000000" min="1000000" max="500000000">' +
      '<p class="login-error" id="tr-start-error" style="display:none"></p>' +
      '<button type="button" class="btn primary" id="tr-start-btn">Start the run</button>' +
      "</div>";
    document.getElementById("tr-start-btn").addEventListener("click", async function () {
      var errEl = document.getElementById("tr-start-error");
      errEl.style.display = "none";
      var r = await call("trainingstart", {
        contract_form: document.getElementById("tr-form").value,
        conditions: document.getElementById("tr-conditions").value,
        facility: document.getElementById("tr-facility").value,
        contract_value: Number(document.getElementById("tr-value").value)
      });
      if (r && r.ok === true) { view = r; briefOpen = true; paint(); }
      else {
        errEl.textContent = (r && r.error) || "Could not start the run.";
        errEl.style.display = "block";
      }
    });
  }

  /* ---------- the run screen ---------- */

  function noticeHtml(n) {
    if (!n) return "";
    if (n.kind === "notice_bar") {
      var cls = n.expired ? "tr-notice-expired" : (n.days_remaining <= 7 ? "tr-notice-tight" : "");
      return '<div class="tr-notice ' + cls + '" id="tr-notice">' +
        (n.expired
          ? "Notice window closed: " + n.days_since_event + " days since the event against a " +
            n.window_days + " day window (" + esc(n.citation) + ")."
          : "Notice window: " + n.days_remaining + " days remaining of " + n.window_days +
            " (" + esc(n.citation) + "). " + n.days_since_event + " days since the event.") +
        "</div>";
    }
    return '<div class="tr-notice" id="tr-notice">' +
      "No fixed notice bar (" + esc(n.citation) + "). Recoverable fraction if noticed today: " +
      Math.round(n.recoverable_fraction * 100) + " percent, by the " + n.lookback_days +
      " day cost lookback.</div>";
  }

  function dscNoticeHtml(n) {
    if (!n) return "";
    var cls = n.expired ? "tr-notice-expired" : "tr-notice-tight";
    var body;
    if (n.kind === "dsc_notice_bar") {
      body = n.expired
        ? "Site condition: " + n.days_since_event + " days since first observance against a " +
          n.window_days + " day period (" + esc(n.citation) + "). " + esc(n.note)
        : "Site condition: " + n.days_remaining + " days remaining of " + n.window_days +
          " (" + esc(n.citation) + "). " + esc(n.note);
    } else {
      body = "Site condition (" + esc(n.citation) + "): " +
        (n.first_opportunity ? "notice is still timely if given now. "
                             : "the moment has passed. ") + esc(n.note);
    }
    return '<div class="tr-notice ' + cls + '" id="tr-dsc-notice">' + body + "</div>";
  }

  function qualityNoticeHtml(n) {
    if (!n) return "";
    var cls = n.status === "open" ? "tr-notice-tight" : "";
    var body;
    if (n.status === "open") {
      body = "Failed inspection: rework valued at " + money(n.defect_value) +
        (n.periods_deferred
          ? ", deferred " + n.periods_deferred + " time" + (n.periods_deferred === 1 ? "" : "s") +
            "; " + n.periods_until_forced + " more deferral" +
            (n.periods_until_forced === 1 ? "" : "s") + " forces the rework"
          : "; accept it, rework it now, or defer the rework");
    } else if (n.status === "accepted") {
      body = "Nonconforming work accepted: " + money(n.closeout_exposure) +
        " stands as exposure at closeout.";
    } else if (n.status === "forced_resolved") {
      body = "The deferred defect backlog forced rework, at a period not chosen: " +
        money(n.defect_value) + " spent.";
    } else {
      body = "Rework complete: " + money(n.defect_value) + " spent.";
    }
    return '<div class="tr-notice ' + cls + '" id="tr-quality-notice">' + body + "</div>";
  }

  function briefHtml(b) {
    if (!b) return "";
    var c = b.conditions || {};
    var e = b.standing_event || {};
    return '<div class="tr-brief" id="tr-brief"' + (briefOpen ? "" : " hidden") + ">" +
      "<h3>The brief</h3>" +
      "<p><strong>" + esc(b.contract_form_label) + ".</strong> " + esc(b.contract_note) + "</p>" +
      "<p><strong>Facility.</strong> " + esc(b.facility_label) + "</p>" +
      "<p><strong>Liquidated damages:</strong> " + money(b.liquidated_damages_per_day) +
      " per day. " + esc(b.liquidated_damages_rule) + "</p>" +
      (b.safety_note ? "<p><strong>Safety.</strong> " + esc(b.safety_note) + "</p>" : "") +
      "<p><strong>Conditions.</strong> Labour " + esc(c.labour) + ". Procurement " +
      esc(c.procurement) + ". Owner " + esc(c.owner) + ". Acceleration costs " +
      c.acceleration_cost_multiplier + " times base; restart productivity loss " +
      Math.round((c.restart_productivity_loss || 0) * 100) + " percent.</p>" +
      "<p><strong>The event.</strong> " + esc(e.description) + " Estimated cost " +
      money(e.estimated_cost) + ", estimated schedule content " + e.estimated_days +
      " days.</p>" +
      '<p class="kn-sub">' + esc(b.designed_figures_note) + "</p>" +
      (b.disclaimer ? '<p class="kn-sub" id="tr-disclaimer">' +
        esc(b.disclaimer.amendment_note) + " " + esc(b.disclaimer.sourced_figures) + " " +
        esc(b.disclaimer.designed_figures) + "</p>" : "") +
      "</div>";
  }

  function figuresHtml(s, n) {
    var floatLeft = s.float_total_days - s.float_consumed_days;
    return '<div class="tr-figures" id="tr-figures">' +
      fig("Cost performance", s.ac ? (s.ev / s.ac).toFixed(3) : "no data", "tr-cpi") +
      fig("Schedule performance", s.pv ? (s.ev / s.pv).toFixed(3) : "no data", "tr-spi") +
      fig("Float remaining", floatLeft + " of " + s.float_total_days + " days", "tr-float") +
      fig("Contingency", money(s.contingency_remaining) + " of " +
          money(s.contingency_original), "tr-contingency") +
      fig("Owner credibility", s.owner_credibility + " of 5", "tr-credibility") +
      fig("Liquidated damages exposure", money(s.liquidated_damages_exposure), "tr-ld") +
      fig("Dispute", esc(s.dispute.status) + ", entitlement " + esc(s.dispute.entitlement),
          "tr-dispute") +
      (s.quality ? fig("Quality", esc(s.quality.status) + ", backlog " +
          money(s.quality.defect_value), "tr-quality") : "") +
      "</div>";
  }

  function fig(label, value, id) {
    return '<div class="tr-fig"><span class="tr-fig-label">' + label +
      '</span><span class="tr-fig-value" id="' + id + '">' + value + "</span></div>";
  }

  // THE SIGNALS DISPLAY IS THE PLATFORM'S OWN LEDGER, not a training-only imitation:
  // LinWorkspace.buildProjectDetailHtml is the same builder the real project detail panel
  // uses, with the same category and computation NAME tables and the same row markup. The
  // trainee is learning the instrument they will actually use. Training passes
  // expandable:true so each category discloses the computations that fed it, plus the
  // abstentions the server reported for it.
  function signalsHtml(result) {
    if (!result) return '<p class="kn-sub">No signals computed for this period.</p>';
    if (!window.LinWorkspace || !LinWorkspace.buildProjectDetailHtml) {
      return '<p class="kn-sub">The signal ledger is unavailable on this page.</p>';
    }
    return '<div class="tr-signals" id="tr-signals">' +
      "<h3>Signals, period " + view.period + "</h3>" +
      LinWorkspace.buildProjectDetailHtml(result, {
        expandable: true,
        abstained: view.abstained_by_category || {}
      }) +
      "</div>";
  }

  // The recommendation, in full. Every figure, day count and clause reference here comes from
  // the server (engine-derived); this file formats and never computes. It is deliberately not
  // labelled as fallible on screen: a recommendation that announces its own unreliability is
  // no longer something the trainee has to weigh.
  function recommendationHtml(rec) {
    if (!rec) return "";
    function line(label, value, id) {
      if (!value) return "";
      return '<div class="tr-rec-line"><span class="tr-rec-label">' + label +
        '</span><span class="tr-rec-value"' + (id ? ' id="' + id + '"' : "") + ">" +
        esc(value) + "</span></div>";
    }
    return '<div class="tr-rec" id="tr-recommendation">' +
      '<h3>Recommendation</h3>' +
      '<p class="tr-rec-headline" id="tr-rec-headline">' + esc(rec.headline) + "</p>" +
      line("What", rec.what, "tr-rec-what") +
      line("Why", rec.why, "tr-rec-why") +
      line("Who acts", rec.who, "tr-rec-who") +
      line("To whom", rec.to_whom, "tr-rec-towhom") +
      line("By what means", rec.means, "tr-rec-means") +
      line("Next step", rec.next_step, "tr-rec-next") +
      line("By when", rec.deadline_date, "tr-rec-deadline") +
      "</div>";
  }

  function incidentHtml(inc) {
    if (!inc || inc.status === "none" || !inc.status) return "";
    if (inc.status === "stopped") {
      return '<div class="tr-notice tr-notice-expired" id="tr-incident">' +
        "Stop work order in effect since period " + inc.period_occurred +
        (inc.cause === "acceleration"
          ? ", following a near miss on the accelerated works." : ", following a near miss.") +
        " All work has stopped except safety work. Lifting requires a Certificate of " +
        "Correction plus whatever the cause demands. The response decides the duration." +
        "</div>";
    }
    if (inc.status === "restarting") {
      return '<div class="tr-notice tr-notice-tight" id="tr-incident">' +
        "The stop work order is lifted after " + inc.days_lost + " days. The site is " +
        "restarting; productivity has not yet recovered.</div>";
    }
    return "";
  }

  function changesHtml(pc) {
    if (!pc) return "";
    var items = [];
    if (pc.float_days_spent) items.push(pc.float_days_spent + " float days spent");
    if (pc.cost_added) items.push(money(pc.cost_added) + " added to actual cost");
    if (pc.contingency_spent) items.push(money(pc.contingency_spent) + " of contingency drawn");
    if (pc.credibility_change) {
      items.push("owner credibility " + (pc.credibility_change > 0 ? "up" : "down") + " " +
        Math.abs(pc.credibility_change));
    }
    var notes = (pc.notes || []).map(function (n) { return "<li>" + esc(n) + "</li>"; }).join("");
    return '<div class="tr-changes" id="tr-changes">' +
      "<h3>What the last period cost</h3>" +
      "<p>" + esc(pc.decision) + (items.length ? ": " + items.join(", ") + "."
                                              : ": no figures moved.") + "</p>" +
      (notes ? "<ul>" + notes + "</ul>" : "") +
      "</div>";
  }

  function narrativeHtml() {
    if (!view.narrative) return "";
    return '<div class="tr-narrative" id="tr-narrative"><h3>Site narrative</h3><p>' +
      esc(view.narrative) + "</p></div>";
  }

  var DECISION_META = {
    escalate: ["Escalate", "protects entitlement, spends float, and costs more the longer the position has been open"],
    absorb: ["Absorb", "protects the relationship, spends contingency"],
    defer: ["Defer", "protects both, runs the notice clock down, and drifts cost and float while the dispute stays open"],
    accelerate: ["Accelerate", "buys float back at a premium, and a compressed site carries a higher chance of an incident"],
    respond_strong: ["Respond with the full correction package", "costlier now, lifts the stop work order sooner, shorter restart shadow"],
    respond_minimal: ["Respond minimally", "cheaper now, stays stopped longer, longer restart shadow"],
    accept_nonconforming: ["Accept nonconforming", "no cost, no time, spends credibility now and stays as exposure at closeout"],
    rework_now: ["Rework now", "costs money and float immediately, clears it"],
    rework_later: ["Rework later", "cheaper now, the backlog grows, and it competes for the same float and contingency"]
  };

  function debriefHtml(d) {
    if (!d) return '<div id="tr-debrief"><p class="kn-sub">Loading the debrief.</p></div>';
    var sp = d.spent || {};
    var closedRows = (d.closed || []).map(function (m) {
      return "<li>" + esc(m.matter) + ": " + esc(m.status) + ", entitlement " +
        esc(m.entitlement) +
        (m.recovered_amount ? ", " + money(m.recovered_amount) + " recovered" : "") + "</li>";
    }).join("");
    if (d.quality) {
      closedRows += "<li id=\"tr-debrief-quality\">the failed inspection: " +
        esc(d.quality.status) +
        (d.quality.closeout_exposure
          ? ", " + money(d.quality.closeout_exposure) + " exposure at closeout"
          : "") + "</li>";
    }
    var incRows = (d.incidents || []).map(function (i) {
      return "<li>Period " + i.period + ", " +
        (i.response ? esc(String(i.response).replace("respond_", "")) + " response, " : "") +
        (i.days_lost || 0) + " days lost. " + esc(i.why) + "</li>";
    }).join("");
    var cf = d.counterfactual || {};
    var cfHtml;
    if (cf.available) {
      var cp = cf.position || {};
      cfHtml = "<p>" + esc(cf.description) + "</p><ul>" +
        "<li>Float spent: " + cp.float_spent_days + " of " + cp.float_total_days + " days</li>" +
        "<li>Contingency spent: " + money(cp.contingency_spent) + "</li>" +
        "<li>Recovered by change order: " + money(cp.recovered_by_change_order) + "</li>" +
        "<li>Liquidated damages exposure: " + money(cp.liquidated_damages_exposure) + "</li>" +
        (cf.claim ? "<li>The change: entitlement " + esc(cf.claim.entitlement) + "</li>" : "") +
        "</ul>";
    } else {
      cfHtml = '<p class="kn-sub" id="tr-cf-unavailable">Counterfactual not computed: ' +
        esc(cf.reason || "unavailable") + "</p>";
    }
    return '<div class="tr-debrief" id="tr-debrief">' +
      "<h3>Debrief</h3>" +
      '<p id="tr-debrief-spent">' + "Spent across " + d.periods_played + " periods: " +
      sp.float_spent_days + " of " + sp.float_total_days + " float days, " +
      money(sp.contingency_spent) + " of contingency, cost over earned " +
      money(sp.cost_over_earned) + ", owner credibility " + sp.owner_credibility +
      " of 5, liquidated damages exposure " + money(sp.liquidated_damages_exposure) + "." +
      "</p>" +
      (closedRows ? '<h3>What closed</h3><ul id="tr-debrief-closed">' + closedRows + "</ul>" : "") +
      (incRows ? '<h3>The incidents, and why</h3><ul id="tr-debrief-incidents">' + incRows + "</ul>" : "") +
      '<h3>The counterfactual</h3><div id="tr-debrief-cf">' + cfHtml + "</div>" +
      '<p class="kn-sub">' + esc((d.disclaimer || {}).amendment_note || "") + "</p>" +
      "</div>";
  }

  var debrief = null;

  async function loadDebrief() {
    var r = await call("trainingdebrief", { run_id: view.run_id });
    if (r && r.ok === true) { debrief = r.debrief; paint(); }
  }

  function decisionsHtml(s) {
    if (view.status !== "active") {
      return '<p class="kn-sub" id="tr-complete">The run is complete.</p>' +
        debriefHtml(debrief) +
        '<button type="button" class="btn primary" id="tr-restart-btn">Start a new run</button>';
    }
    var allowed = view.allowed_decisions || ["escalate", "absorb", "defer"];
    var open = s.dispute.status === "open";
    var buttons = allowed.map(function (d) {
      var meta = DECISION_META[d] || [d, ""];
      return '<button type="button" class="btn" data-decision="' + d + '">' + esc(meta[0]) +
        '<span class="tr-hint">' + esc(meta[1]) + "</span></button>";
    }).join("");
    return '<div class="tr-decide" id="tr-decide">' +
      "<h3>Decide, period " + view.period + "</h3>" +
      (open || allowed.indexOf("respond_strong") !== -1 ? "" :
        '<p class="kn-sub">The dispute is settled; the remaining periods run out ' +
        "the schedule. Deferring is the neutral close of a period.</p>") +
      buttons +
      '<p class="login-error" id="tr-decide-error" style="display:none"></p>' +
      "</div>";
  }

  function logHtml(s) {
    var items = (s.decisions || []).map(function (d) {
      return "<li>Period " + d.period + ": " + esc(d.decision) + "</li>";
    }).join("");
    return items ? '<div class="tr-log"><h3>Decisions so far</h3><ul id="tr-log-list">' +
      items + "</ul></div>" : "";
  }

  function paint() {
    var s = view.state;
    root.innerHTML =
      '<div class="tr-head">' +
      '<span class="tr-run-id">' + esc(view.project) + " · period " + view.period +
      " of " + view.periods_total + "</span>" +
      '<button type="button" class="btn small" id="tr-brief-btn">' +
      (briefOpen ? "Hide the brief" : "Read the brief") + "</button>" +
      "</div>" +
      briefHtml(view.brief) +
      noticeHtml(view.notice) +
      dscNoticeHtml(view.dsc_notice) +
      qualityNoticeHtml(view.quality_notice) +
      incidentHtml(s.incident) +
      recommendationHtml(view.recommendation) +
      changesHtml(s.period_changes) +
      narrativeHtml() +
      figuresHtml(s, view.notice) +
      signalsHtml(view.result) +
      decisionsHtml(s) +
      logHtml(s);

    var briefBtn = document.getElementById("tr-brief-btn");
    if (briefBtn) briefBtn.addEventListener("click", function () {
      briefOpen = !briefOpen;
      paint();
    });
    // The disclosure wiring is the workspace's own, for the same reason the markup is.
    if (window.LinWorkspace && LinWorkspace.wireCategoryRows) {
      LinWorkspace.wireCategoryRows(root);
    }
    var restart = document.getElementById("tr-restart-btn");
    if (restart) restart.addEventListener("click", function () {
      debrief = null;
      paintStart();
    });
    // The debrief is fetched once the run completes; a re-paint with it loaded renders it.
    if (view.status !== "active" && debrief === null) loadDebrief();
    root.querySelectorAll("[data-decision]").forEach(function (btn) {
      btn.addEventListener("click", function () { decide(btn.dataset.decision); });
    });
  }

  async function decide(decision) {
    var errEl = document.getElementById("tr-decide-error");
    if (errEl) errEl.style.display = "none";
    var r = await call("trainingdecision", { run_id: view.run_id, decision: decision });
    if (r && r.ok === true) { view = r; paint(); }
    else if (errEl) {
      errEl.textContent = (r && r.error) || "The decision could not be recorded.";
      errEl.style.display = "block";
    }
  }

  return { render: render, _paint: paint, get view() { return view; } };
})();
