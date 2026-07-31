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

   DORMANT UNTIL THE RESEARCH SESSION EXISTS. The SPA does not
   sign a participant in yet — that is T4 — so with no session
   token this is a no-op and every feature stays visible, which
   is exactly today's behaviour for the researcher and for
   operational use. Once T4 stores a token, the flags resolve on
   load and the body classes below drive the CSS.
   ============================================================ */
(function () {
  "use strict";

  var KEYS = ["chat", "knowledge_library", "health_dialog", "auditor"];
  var SESSION_KEYS = ["og-session-token", "lin-research-session"];

  function sessionToken() {
    if (window.OG_SESSION_TOKEN) return window.OG_SESSION_TOKEN;
    for (var i = 0; i < SESSION_KEYS.length; i++) {
      try {
        var v = localStorage.getItem(SESSION_KEYS[i]);
        if (v) return v;
      } catch (e) { /* storage disabled */ }
    }
    return null;
  }

  var state = null;

  function apply(features) {
    state = features;
    var body = document.body;
    if (!body) return;
    KEYS.forEach(function (k) {
      // og-no-<feature> is the hook radar.css hides against.
      body.classList.toggle("og-no-" + k.replace(/_/g, "-"), features[k] === false);
    });
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
      if (r && r.ok && r.features) { apply(r.features); return r.features; }
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
