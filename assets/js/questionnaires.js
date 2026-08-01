/* ============================================================
   Opus Gubernatio — questionnaires.js (T7/T8)
   ------------------------------------------------------------
   Renders EITHER the intake or the debrief questionnaire from its JSON
   definition (assets/questionnaires/intake.json / debrief.json), fetched
   fresh on every load — editing the JSON and reloading changes the form
   with no code edit, which is the whole point of building it this way
   (the instruments are not finalised; see each JSON's `note` field).

   Which one to show is decided by SERVER STATE, not a URL flag the
   participant could set themselves:
     - consent not granted            -> gate, link back to sign-in/consent
     - intake not yet completed       -> intake.json
     - intake done, debrief eligible  -> debrief.json
     - debrief done                   -> "already complete" message
     - intake done, debrief not yet   -> "nothing to do right now" message
   `?type=` is read ONLY as a hint for direct testing/deep-linking; the
   eligibility checks above always win, so it cannot be used to skip ahead.

   No computation happens here. Rendering an item's UI control and
   collecting its answer is the only logic in this file.
   ============================================================ */

(function () {
  "use strict";

  function $(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function token() { return window.LinAuth ? LinAuth.getToken() : null; }
  function call(action, extra) {
    return LinStore.postWithTimeout(Object.assign({ action: action, session_token: token() },
                                                   extra || {}), 30000);
  }

  // The gate/shell/done screens belonged to questionnaires.html, which had to handle being
  // opened directly by someone not signed in. An overlay inside the application cannot be
  // opened directly, so the only outcome left is "saved, now get on with it".

  // T6 Part A/A.1. questionnaires.html is gone, and with it the idea that this is somewhere a
  // participant goes. The profile is captured ONCE — after consent, before the first decision —
  // in an overlay that has no route and no navigation item.
  //
  // Whether it is needed is decided by the SERVER, from profilestatus, not by a flag this file
  // keeps. That matters: a participant who reloads, signs in on another machine, or comes back
  // a week later must not be asked twice, and the only place that knows is the row.
  //
  // The debrief is no longer reachable from here at all. It was its own page, and a separate
  // page a participant could visit at any moment is exactly the wrong shape for items that only
  // mean anything at the end of the final decision — T6 moves them into that flow.

  async function maybePrompt() {
    if (!token()) return;

    var status = await call("profilestatus");
    if (!status || status.ok !== true) return;
    // Consent first, always. auth.js owns that gate; if it has not been granted the application
    // is not showing yet and this returns without touching the DOM.
    if (!status.consent_granted) return;
    // Already captured — the overlay never appears again.
    if (status.intake_completed) return;

    var def;
    try {
      var resp = await fetch("assets/questionnaires/intake.json", { cache: "no-store" });
      def = await resp.json();
    } catch (e) {
      // Silent: a participant who cannot load the definition is better off in the application
      // than behind an overlay they cannot dismiss. The server still refuses a preliminary
      // judgment until intake exists, so nothing downstream is compromised by this returning.
      return;
    }

    var overlay = $("profile-overlay");
    if (!overlay) return;
    renderForm(def, "intake");
    overlay.hidden = false;
  }

  function dismiss() {
    var overlay = $("profile-overlay");
    if (overlay) overlay.hidden = true;
  }

  window.LinProfile = { maybePrompt: maybePrompt };

  /* ---------- rendering ---------- */

  function renderForm(def, kind) {
    var root = $("q-form-root");
    var html = '<h2 class="q-title">' + esc(def.title) + "</h2>";
    if (def.note) html += '<div class="q-note">' + esc(def.note) + "</div>";
    (def.sections || []).forEach(function (section) {
      html += '<div class="q-section" data-section="' + esc(section.id) + '">';
      html += "<h3>" + esc(section.title) + "</h3>";
      if (section.note) html += '<p class="q-section-note">' + esc(section.note) + "</p>";
      (section.items || []).forEach(function (item) { html += renderItem(item); });
      html += "</div>";
    });
    root.innerHTML = html;

    $("q-submit-btn").onclick = function () { submitForm(def, kind); };
  }

  function renderItem(item) {
    var required = item.required ?
      '<span class="q-required" title="required">*</span>' : "";
    var label = '<label class="q-label" for="item-' + esc(item.id) + '">' +
      esc(item.label) + required + "</label>";

    switch (item.type) {
      case "single-select":
        return '<div class="q-item" data-item="' + esc(item.id) + '" data-type="single-select">' +
          label + '<div class="q-options">' +
          (item.options || []).map(function (o) {
            return '<label class="q-option-row"><input type="radio" name="item-' + esc(item.id) +
              '" value="' + esc(o.value) + '"> ' + esc(o.label) + "</label>";
          }).join("") + "</div></div>";

      case "multi-select":
        return '<div class="q-item" data-item="' + esc(item.id) + '" data-type="multi-select">' +
          label + '<div class="q-options">' +
          (item.options || []).map(function (o) {
            return '<label class="q-option-row"><input type="checkbox" data-group="item-' +
              esc(item.id) + '" value="' + esc(o.value) + '"> ' + esc(o.label) + "</label>";
          }).join("") + "</div></div>";

      case "text":
        return '<div class="q-item" data-item="' + esc(item.id) + '" data-type="text">' + label +
          (item.multiline ?
            '<textarea class="q-textarea" id="item-' + esc(item.id) + '"></textarea>' :
            '<input class="q-input" type="text" id="item-' + esc(item.id) + '">') + "</div>";

      case "numeric":
        return '<div class="q-item" data-item="' + esc(item.id) + '" data-type="numeric">' + label +
          '<input class="q-input" type="number" id="item-' + esc(item.id) +
          '" min="' + esc(item.min != null ? item.min : "") +
          '" max="' + esc(item.max != null ? item.max : "") +
          '" step="' + esc(item.step || 1) + '"></div>';

      case "likert": {
        var min = item.scaleMin != null ? item.scaleMin : 1;
        var max = item.scaleMax != null ? item.scaleMax : 5;
        var opts = [];
        for (var v = min; v <= max; v++) opts.push(v);
        return '<div class="q-item" data-item="' + esc(item.id) + '" data-type="likert">' + label +
          '<div class="q-likert">' +
          (item.scaleMinLabel ? '<span class="q-likert-endlabel">' + esc(item.scaleMinLabel) + "</span>" : "") +
          '<div class="q-likert-scale">' +
          opts.map(function (v) {
            return '<label><input type="radio" name="item-' + esc(item.id) + '" value="' + v +
              '">' + v + "</label>";
          }).join("") + "</div>" +
          (item.scaleMaxLabel ? '<span class="q-likert-endlabel">' + esc(item.scaleMaxLabel) + "</span>" : "") +
          "</div></div>";
      }

      default:
        return '<div class="q-item"><p class="q-error">Unknown item type: ' +
          esc(item.type) + "</p></div>";
    }
  }

  function collectAnswer(item) {
    var el = document.querySelector('[data-item="' + item.id + '"]');
    if (!el) return undefined;
    switch (item.type) {
      case "single-select":
      case "likert": {
        var checked = el.querySelector('input[type="radio"]:checked');
        return checked ? checked.value : null;
      }
      case "multi-select":
        return Array.prototype.slice.call(el.querySelectorAll('input[type="checkbox"]:checked'))
          .map(function (c) { return c.value; });
      case "text":
        return $("item-" + item.id).value.trim() || null;
      case "numeric": {
        var raw = $("item-" + item.id).value;
        return raw === "" ? null : Number(raw);
      }
      default:
        return null;
    }
  }

  function allItems(def) {
    var out = [];
    (def.sections || []).forEach(function (s) { (s.items || []).forEach(function (i) { out.push(i); }); });
    return out;
  }

  async function submitForm(def, kind) {
    var errEl = $("q-error");
    errEl.style.display = "none";
    var items = allItems(def);
    var responses = {};
    var missing = [];
    items.forEach(function (item) {
      var answer = collectAnswer(item);
      responses[item.id] = answer;
      var empty = answer === null || answer === undefined ||
        (Array.isArray(answer) && answer.length === 0);
      if (item.required && empty) missing.push(item.label);
    });
    if (missing.length) {
      errEl.textContent = "Please answer: " + missing.join("; ");
      errEl.style.display = "block";
      return;
    }

    $("q-submit-btn").disabled = true;
    var resp = await call(kind === "intake" ? "intakesave" : "debriefsave",
                          { responses: responses });
    $("q-submit-btn").disabled = false;

    if (!resp || resp.ok !== true) {
      errEl.textContent = (resp && resp.error) || "Could not save your responses.";
      errEl.style.display = "block";
      return;
    }
    // Saved. The overlay closes and the participant is in the application — there is no
    // confirmation screen to acknowledge, because this is a step in getting started rather
    // than an errand that was completed.
    dismiss();
  }
})();
