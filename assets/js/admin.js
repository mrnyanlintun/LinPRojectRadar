/* ============================================================
   Opus Gubernatio — admin.js
   ------------------------------------------------------------
   T2 Part 4: the ResearchAdmin user-management interface.

   NOT the security boundary. This page is reachable only when
   auth.js reveals the Admin nav trigger for a ResearchAdmin — but
   that is a convenience, not the guard (Guarantee 5). Every call
   this file makes is refused server-side by _require_admin in
   research_identity.py/features.py regardless of who can see the
   button; a non-admin who forces this page open by editing the DOM
   gets a page full of refused-action errors, not data.

   Reuses the platform's existing chrome rather than inventing a
   parallel one: LinUI.openModal for the create-user / reset-
   password / feature-flag dialogs, LinUI.toast for outcomes,
   .about-table for the list, .ig-input for form fields.
   ============================================================ */
var LinAdmin = (function () {
  "use strict";

  var FEATURE_KEYS = ["chat", "knowledge_library", "health_dialog", "auditor"];
  var FEATURE_LABELS = {
    chat: "Assistant", knowledge_library: "Knowledge Library",
    health_dialog: "Health dialog", auditor: "Auditor"
  };

  var rootEl = null;
  var lastList = [];

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function token() { return window.LinAuth ? LinAuth.getToken() : null; }

  async function call(action, extra) {
    var body = Object.assign({ action: action, session_token: token() }, extra || {});
    if (!window.LinStore || !LinStore.postWithTimeout) return { ok: false, error: "Store not available." };
    try { return await LinStore.postWithTimeout(body); }
    catch (e) { return { ok: false, error: "Could not reach the server." }; }
  }

  /* ---------- copy-to-clipboard (no existing helper in the codebase; see T2 PR notes) ---------- */

  function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text).then(function () { return true; })
        .catch(function () { return false; });
    }
    return Promise.resolve(false);
  }

  function secretRevealHtml(secretValue) {
    return '<div class="admin-secret-reveal">' +
      '<input type="text" readonly class="ig-input admin-secret-input" value="' + esc(secretValue) + '">' +
      '<button type="button" class="btn small admin-copy-btn">Copy</button>' +
      '<p class="admin-secret-warning">Shown once. It is stored hashed and cannot be retrieved ' +
      'again — write it down or copy it now.</p>' +
    '</div>';
  }

  function wireCopyButtons(container) {
    container.querySelectorAll(".admin-copy-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var input = btn.previousElementSibling;
        var text = input ? input.value : "";
        copyToClipboard(text).then(function (ok) {
          if (window.LinUI && LinUI.toast) {
            LinUI.toast(ok ? "Copied" : "Copy failed — select the field and copy manually", ok);
          }
          if (input) { input.focus(); input.select(); }
        });
      });
    });
  }

  /* ---------- list ---------- */

  async function render() {
    rootEl = document.getElementById("admin-root");
    if (!rootEl) return;
    rootEl.innerHTML = '<p class="kn-sub">Loading users…</p>';
    var resp = await call("adminparticipantlist");
    if (!resp || resp.ok !== true) {
      // A non-admin who forces this page open lands here: the server refused
      // adminparticipantlist, and that refusal is all this page ever shows them.
      rootEl.innerHTML = '<p class="login-error" style="display:block">' +
        esc((resp && resp.error) || "Could not load users.") + '</p>';
      return;
    }
    lastList = resp.participants || [];
    paint();
  }

  function paint() {
    var rows = lastList.map(rowHtml).join("");
    rootEl.innerHTML =
      '<div class="admin-toolbar"><button type="button" class="btn primary" id="admin-create-btn">Create user</button></div>' +
      '<div class="about-table-wrap"><table class="about-table admin-table"><thead><tr>' +
      '<th>Username</th><th>Role</th><th>Type</th><th>Active</th><th>Consent</th>' +
      '<th>Features</th><th>Actions</th>' +
      '</tr></thead><tbody>' + rows + '</tbody></table></div>';

    var createBtn = document.getElementById("admin-create-btn");
    if (createBtn) createBtn.addEventListener("click", openCreateModal);

    lastList.forEach(function (p) {
      var resetBtn = document.getElementById("admin-reset-" + p.participant_id);
      if (resetBtn) resetBtn.addEventListener("click", function () { openResetModal(p); });
      var toggleBtn = document.getElementById("admin-toggle-" + p.participant_id);
      if (toggleBtn) toggleBtn.addEventListener("click", function () { toggleActive(p); });
      var flagsBtn = document.getElementById("admin-flags-" + p.participant_id);
      if (flagsBtn) flagsBtn.addEventListener("click", function () { openFlagsModal(p); });
      var linkBtn = document.getElementById("admin-link-" + p.participant_id);
      if (linkBtn) linkBtn.addEventListener("click", function () { openLinkGoogleModal(p); });
    });
  }

  function rowHtml(p) {
    var onCount = FEATURE_KEYS.filter(function (k) { return p.features && p.features[k]; }).length;
    return '<tr>' +
      '<td>' + esc(p.pseudonymous_code) +
        (p.display_name ? ' <span class="admin-dim">(' + esc(p.display_name) + ')</span>' : '') +
      '</td>' +
      '<td>' + esc(p.role) + '</td>' +
      '<td>' + esc(p.account_type) + '</td>' +
      '<td>' + (p.is_active
        ? '<span class="admin-pill admin-pill-on">Active</span>'
        : '<span class="admin-pill admin-pill-off">Inactive</span>') + '</td>' +
      '<td>' + esc((p.consent && p.consent.status) || 'none') + '</td>' +
      '<td>' + onCount + '/' + FEATURE_KEYS.length + ' on ' +
        '<button type="button" class="btn small" id="admin-flags-' + p.participant_id + '">Edit</button></td>' +
      '<td class="admin-actions">' +
        '<button type="button" class="btn small" id="admin-reset-' + p.participant_id + '">Reset password</button> ' +
        '<button type="button" class="btn small" id="admin-toggle-' + p.participant_id + '">' +
          (p.is_active ? 'Deactivate' : 'Activate') + '</button>' +
        (p.account_type === 'operational'
          ? ' <button type="button" class="btn small" id="admin-link-' + p.participant_id + '">' +
            (p.google_email ? 'Change Google link' : 'Link Google') + '</button>'
          : '') +
      '</td>' +
    '</tr>';
  }

  /* ---------- create user ---------- */

  function openCreateModal() {
    if (!window.LinUI || !LinUI.openModal) return;
    LinUI.openModal({
      title: "Create user",
      mount: function (body) {
        body.innerHTML =
          '<label class="login-field-label">Account type</label>' +
          '<select id="admin-new-account-type" class="ig-input">' +
            '<option value="research">Research</option>' +
            '<option value="operational">Operational</option>' +
          '</select>' +
          '<label class="login-field-label">Role</label>' +
          '<select id="admin-new-role" class="ig-input">' +
            '<option value="Participant">Participant</option>' +
            '<option value="ResearchAdmin">ResearchAdmin</option>' +
            '<option value="Expert">Expert</option>' +
            '<option value="Demo">Demo</option>' +
          '</select>' +
          '<label class="login-field-label">Username (optional — generated as PM-### if left blank)</label>' +
          '<input type="text" id="admin-new-code" class="ig-input" placeholder="PM-001">' +
          '<label class="login-field-label">Initial password (optional — generated if left blank)</label>' +
          '<input type="text" id="admin-new-password" class="ig-input" placeholder="Leave blank to generate">' +
          '<div id="admin-new-operational-fields" hidden>' +
            '<label class="login-field-label">Display name</label>' +
            '<input type="text" id="admin-new-display-name" class="ig-input">' +
            '<label class="login-field-label">Google account email (for SSO sign-in)</label>' +
            '<input type="email" id="admin-new-google-email" class="ig-input">' +
          '</div>' +
          '<p id="admin-create-error" class="login-error" role="alert" style="display:none;"></p>' +
          '<button type="button" class="btn primary" id="admin-create-submit">Create</button>' +
          '<div id="admin-create-result"></div>';

        var typeSel = body.querySelector("#admin-new-account-type");
        var opFields = body.querySelector("#admin-new-operational-fields");
        typeSel.addEventListener("change", function () {
          opFields.hidden = typeSel.value !== "operational";
        });

        body.querySelector("#admin-create-submit").addEventListener("click", async function () {
          var errEl = body.querySelector("#admin-create-error");
          errEl.style.display = "none";
          var payload = {
            account_type: typeSel.value,
            role: body.querySelector("#admin-new-role").value,
            pseudonymous_code: body.querySelector("#admin-new-code").value.trim() || undefined,
            password: body.querySelector("#admin-new-password").value.trim() || undefined,
          };
          if (typeSel.value === "operational") {
            payload.display_name = body.querySelector("#admin-new-display-name").value.trim() || undefined;
            payload.google_email = body.querySelector("#admin-new-google-email").value.trim() || undefined;
          }
          var resp = await call("adminparticipantcreate", payload);
          if (!resp || resp.ok !== true) {
            errEl.textContent = (resp && resp.error) || "Could not create user.";
            errEl.style.display = "block";
            return;
          }
          var resultEl = body.querySelector("#admin-create-result");
          resultEl.innerHTML = '<p><strong>' + esc(resp.pseudonymous_code) + '</strong> created.</p>' +
            secretRevealHtml(resp.password || resp.access_token);
          wireCopyButtons(resultEl);
          body.querySelector("#admin-create-submit").hidden = true;
          render(); // refresh the list behind the modal; the modal itself stays open on the secret
        });
      }
    });
  }

  /* ---------- reset password ---------- */

  function openResetModal(p) {
    if (!window.LinUI || !LinUI.openModal) return;
    LinUI.openModal({
      title: "Reset password — " + (p.display_name || p.pseudonymous_code),
      mount: function (body) {
        body.innerHTML =
          '<label class="login-field-label">New password (optional — generated if left blank)</label>' +
          '<input type="text" id="admin-reset-password-input" class="ig-input" placeholder="Leave blank to generate">' +
          '<button type="button" class="btn primary" id="admin-reset-submit">Reset</button>' +
          '<div id="admin-reset-result"></div>';
        body.querySelector("#admin-reset-submit").addEventListener("click", async function () {
          var pw = body.querySelector("#admin-reset-password-input").value.trim();
          var resp = await call("setpassword", {
            participant_id: p.participant_id, password: pw || undefined
          });
          if (!resp || resp.ok !== true) {
            if (window.LinUI && LinUI.toast) LinUI.toast((resp && resp.error) || "Reset failed", false);
            return;
          }
          var resultEl = body.querySelector("#admin-reset-result");
          resultEl.innerHTML = secretRevealHtml(resp.password);
          wireCopyButtons(resultEl);
          body.querySelector("#admin-reset-submit").hidden = true;
        });
      }
    });
  }

  /* ---------- activate / deactivate ---------- */

  async function toggleActive(p) {
    var resp = await call("setactive", { participant_id: p.participant_id, is_active: !p.is_active });
    if (!resp || resp.ok !== true) {
      // "cannot deactivate the last active administrator" surfaces here verbatim — a toast,
      // not a generic failure, so the admin sees WHY the click did nothing.
      if (window.LinUI && LinUI.toast) LinUI.toast((resp && resp.error) || "Could not change active state", false);
      return;
    }
    if (window.LinUI && LinUI.toast) LinUI.toast(resp.is_active ? "Activated" : "Deactivated", true);
    render();
  }

  /* ---------- link Google (operational SSO) ---------- */

  function openLinkGoogleModal(p) {
    if (!window.LinUI || !LinUI.openModal) return;
    LinUI.openModal({
      title: "Link Google account — " + (p.display_name || p.pseudonymous_code),
      mount: function (body) {
        body.innerHTML =
          '<label class="login-field-label">Google account email</label>' +
          '<input type="email" id="admin-link-email-input" class="ig-input" value="' +
            esc(p.google_email || "") + '">' +
          '<p class="kn-sub">Leave blank and save to remove the link.</p>' +
          '<button type="button" class="btn primary" id="admin-link-submit">Save</button>';
        body.querySelector("#admin-link-submit").addEventListener("click", async function () {
          var email = body.querySelector("#admin-link-email-input").value.trim();
          var resp = await call("adminlinkgoogle", {
            participant_id: p.participant_id, google_email: email
          });
          if (!resp || resp.ok !== true) {
            if (window.LinUI && LinUI.toast) LinUI.toast((resp && resp.error) || "Could not update link", false);
            return;
          }
          if (window.LinUI && LinUI.toast) LinUI.toast("Saved", true);
          render();
        });
      }
    });
  }

  /* ---------- feature flags ---------- */

  function openFlagsModal(p) {
    if (!window.LinUI || !LinUI.openModal) return;
    LinUI.openModal({
      title: "Feature flags — " + (p.display_name || p.pseudonymous_code),
      mount: function (body) { paintFlags(body, p); }
    });
  }

  async function paintFlags(body, p) {
    body.innerHTML = '<p class="kn-sub">Loading…</p>';
    var resp = await call("adminfeaturesget", { participant_id: p.participant_id });
    if (!resp || resp.ok !== true) {
      body.innerHTML = '<p class="login-error" style="display:block">' +
        esc((resp && resp.error) || "Could not load flags.") + '</p>';
      return;
    }
    var stored = resp.stored || {};
    var effective = resp.effective || {};
    var defaultsOn = resp.defaults_from_account_type;

    body.innerHTML = FEATURE_KEYS.map(function (k) {
      var isSet = Object.prototype.hasOwnProperty.call(stored, k);
      var eff = !!effective[k];
      return '<div class="admin-flag-row">' +
        '<span class="admin-flag-label">' + esc(FEATURE_LABELS[k]) + '</span>' +
        '<span class="admin-pill ' + (eff ? "admin-pill-on" : "admin-pill-off") + '">' +
          (eff ? "On" : "Off") + (isSet ? "" : " (default)") + '</span>' +
        '<button type="button" class="btn small" data-flag-key="' + k + '" data-flag-value="true">Turn on</button>' +
        '<button type="button" class="btn small" data-flag-key="' + k + '" data-flag-value="false">Turn off</button>' +
      '</div>';
    }).join("") +
      '<p class="kn-sub">An unset key resolves from account type: ' + (defaultsOn ? "on" : "off") +
      ' by default for a ' + esc(p.account_type) + ' account. There is currently no way to ' +
      'return an explicitly-set key to "default" other than setting it to match that value.</p>';

    body.querySelectorAll("[data-flag-key]").forEach(function (btn) {
      btn.addEventListener("click", async function () {
        var key = btn.getAttribute("data-flag-key");
        var val = btn.getAttribute("data-flag-value") === "true";
        var features = {}; features[key] = val;
        var r = await call("adminfeaturesset", { participant_id: p.participant_id, features: features });
        if (!r || r.ok !== true) {
          if (window.LinUI && LinUI.toast) LinUI.toast((r && r.error) || "Could not update flag", false);
          return;
        }
        if (window.LinUI && LinUI.toast) LinUI.toast("Updated", true);
        paintFlags(body, p); // repaint this same modal with the fresh state
        render();            // and refresh the summary column behind it
      });
    });
  }

  return { render: render };
})();
