/* ============================================================
   Opus Gubernatio — features.js
   ------------------------------------------------------------
   Client half of the per-user feature flags. It HIDES a disabled
   feature; it does not enforce it. Enforcement is server-side in
   server/app/features.py, which refuses the action itself — this
   file only stops a participant being shown an affordance that
   would be refused if they used it.

   Nothing here is a security boundary. Anyone can edit a class
   list in devtools; the point is that doing so gets them a
   refusal from the server, not the feature.

   SESSION-BACKED SINCE T2. auth.js signs a participant in and stores the token in
   sessionStorage under "og-session-token" (plus an in-memory mirror at
   window.OG_SESSION_TOKEN) — deliberately not localStorage; see auth.js. Before any sign-in,
   or for a sessionless/legacy caller, there is no token and this stays a no-op with every
   feature visible, same as before T2.
   ============================================================ */
(function () {
  "use strict";

  var KEYS = ["chat", "knowledge_library", "health_dialog", "auditor"];
  var TOKEN_KEY = "og-session-token";

  function sessionToken() {
    if (window.OG_SESSION_TOKEN) return window.OG_SESSION_TOKEN;
    try {
      return sessionStorage.getItem(TOKEN_KEY) || null;
    } catch (e) { return null; } // storage disabled
  }

  var state = null;

  function apply(features, accountType) {
    state = features;
    var body = document.body;
    if (!body) return;
    KEYS.forEach(function (k) {
      // og-no-<feature> is the hook radar.css hides against.
      body.classList.toggle("og-no-" + k.replace(/_/g, "-"), features[k] === false);
    });
    // Which upload/liability notice to show. Only an explicit "operational" from the server
    // switches away from the restrictive research notice: unknown, unresolved and research
    // all keep the restrictive text, which is the fail-safe direction for a liability notice.
    body.classList.toggle("og-account-operational", accountType === "operational");
    try {
      document.dispatchEvent(new CustomEvent("og:features", { detail: features }));
    } catch (e) { /* older browsers */ }
  }

  function enabled(key) {
    // Unknown until resolved → treated as available, because the server is the authority
    // and will refuse if it is not. Hiding on a failed lookup would break the operational
    // user for a network blip.
    return !state || state[key] !== false;
  }

  async function refresh() {
    var token = sessionToken();
    if (!token || !window.LinStore || !LinStore.postWithTimeout) return null;
    try {
      var r = await LinStore.postWithTimeout({
        action: "researchmyfeatures", session_token: token
      });
      if (r && r.ok && r.features) { apply(r.features, r.account_type); return r.features; }
    } catch (e) { /* non-fatal: the server still refuses what is disabled */ }
    return null;
  }

  window.OGFeatures = { refresh: refresh, enabled: enabled, keys: KEYS,
                        get state() { return state; } };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { refresh(); });
  } else {
    refresh();
  }
})();
