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

  function briefHtml(b) {
    if (!b) return "";
    var c = b.conditions || {};
    var e = b.standing_event || {};
    return '<div class="tr-brief" id="tr-brief"' + (briefOpen ? "" : " hidden") + ">" +
      "<h3>The brief</h3>" +
      "<p><strong>" + esc(b.contract_form_label) + ".</strong> " + esc(b.contract_note) + "</p>" +
      "<p><strong>Liquidated damages:</strong> " + money(b.liquidated_damages_per_day) +
      " per day. " + esc(b.liquidated_damages_rule) + "</p>" +
      "<p><strong>Conditions.</strong> Labour " + esc(c.labour) + ". Procurement " +
      esc(c.procurement) + ". Owner " + esc(c.owner) + ". Acceleration costs " +
      c.acceleration_cost_multiplier + " times base; restart productivity loss " +
      Math.round((c.restart_productivity_loss || 0) * 100) + " percent.</p>" +
      "<p><strong>The event.</strong> " + esc(e.description) + " Estimated cost " +
      money(e.estimated_cost) + ", estimated schedule content " + e.estimated_days +
      " days.</p>" +
      '<p class="kn-sub">' + esc(b.designed_figures_note) + "</p>" +
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
      "</div>";
  }

  function fig(label, value, id) {
    return '<div class="tr-fig"><span class="tr-fig-label">' + label +
      '</span><span class="tr-fig-value" id="' + id + '">' + value + "</span></div>";
  }

  function signalsHtml(result) {
    if (!result) return '<p class="kn-sub">No signals computed for this period.</p>';
    var cats = result.category_statuses || {};
    var rows = Object.keys(cats).sort().map(function (name) {
      var c = cats[name];
      return "<tr><td>" + esc(name) + "</td><td>" + esc(c.group || "") + "</td>" +
        '<td><span class="tr-status tr-status-' + String(c.status || "none").toLowerCase() +
        '">' + esc(c.status || "no status") + "</span></td></tr>";
    }).join("");
    var recs = (result.module_results || []).filter(function (m) {
      return m && (m.recommended_action || m.action);
    }).map(function (m) {
      return "<li>" + esc(m.recommended_action || m.action) +
        (m.authority ? " (" + esc(m.authority) + ")" : "") + "</li>";
    }).join("");
    return '<div class="tr-signals" id="tr-signals">' +
      "<h3>Signals, period " + view.period + "</h3>" +
      '<p>Project status: <span class="tr-status tr-status-' +
      String(result.project_status || "none").toLowerCase() + '" id="tr-project-status">' +
      esc(result.project_status || "no status") + "</span></p>" +
      '<div class="about-table-wrap"><table class="about-table"><thead>' +
      "<tr><th>Category</th><th>Group</th><th>Status</th></tr></thead><tbody>" +
      rows + "</tbody></table></div>" +
      (recs ? "<h3>Recommended actions</h3><ul id=\"tr-recommendations\">" + recs + "</ul>"
            : "") +
      "</div>";
  }

  function decisionsHtml(s) {
    if (view.status !== "active") {
      return '<p class="kn-sub" id="tr-complete">The run is complete. ' +
        "Start a new one to try a different response.</p>" +
        '<button type="button" class="btn primary" id="tr-restart-btn">Start a new run</button>';
    }
    var open = s.dispute.status === "open";
    return '<div class="tr-decide" id="tr-decide">' +
      "<h3>Decide, period " + view.period + "</h3>" +
      (open ? "" : '<p class="kn-sub">The dispute is settled; the remaining periods run out ' +
                   "the schedule. Deferring is the neutral close of a period.</p>") +
      '<button type="button" class="btn" data-decision="escalate">Escalate' +
      '<span class="tr-hint">protects entitlement, spends float</span></button>' +
      '<button type="button" class="btn" data-decision="absorb">Absorb' +
      '<span class="tr-hint">protects the relationship, spends contingency</span></button>' +
      '<button type="button" class="btn" data-decision="defer">Defer' +
      '<span class="tr-hint">protects both, and runs the notice clock down</span></button>' +
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
      figuresHtml(s, view.notice) +
      signalsHtml(view.result) +
      decisionsHtml(s) +
      logHtml(s);

    var briefBtn = document.getElementById("tr-brief-btn");
    if (briefBtn) briefBtn.addEventListener("click", function () {
      briefOpen = !briefOpen;
      paint();
    });
    var restart = document.getElementById("tr-restart-btn");
    if (restart) restart.addEventListener("click", paintStart);
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
