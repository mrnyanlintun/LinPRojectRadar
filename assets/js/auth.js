/* ============================================================
   Opus Gubernatio — auth.js
   ------------------------------------------------------------
   T2: two sign-in paths, resolving to real backend Participant
   accounts — username + password for research participants,
   Google Sign-In for operational users — the research consent
   gate, and session resume.

   SESSION STORAGE, DELIBERATELY NOT localStorage. The token lives
   in sessionStorage plus an in-memory mirror (window.OG_SESSION_
   TOKEN, which features.js also reads). sessionStorage is cleared
   when the tab/browser closes; localStorage is not. A closed
   browser requiring a fresh sign-in is the point, not an
   oversight — this is a research instrument recording decisions
   under a specific participant identity, and a token that outlives
   the browser session is a token that can authenticate the next
   person to open the laptop.

   NO IDLE TIMEOUT. There is no timer anywhere in this file that
   signs a user out for inactivity. A session ends only when its
   server-assigned TTL elapses (mint_session in research_identity.py)
   or the user calls logout(). A participant who leaves mid-decision
   and returns hours later, within the TTL, resumes exactly where
   the server says they are — the stage is read from researchwhoami
   on every resume, never cached or computed here.

   ROUTING is entirely server-driven. The three gate states —
   login, consent, app — are chosen from account_type, role and
   consent.status as returned by the server on login/resume; this
   file never decides who needs to consent by any rule of its own,
   and current_stage is rendered wherever the app shows it, never
   recomputed here.
   ============================================================ */
var LinAuth = (function () {
  "use strict";

  var TOKEN_KEY = "og-session-token";
  var memoryToken = null;
  var currentView = null; // last known participant view: role, account_type, consent, current_stage, ...

  function el(id) { return document.getElementById(id); }
  function show(id, mode) { var e = el(id); if (e) e.style.display = mode; }

  function hideAllScreens() {
    show("lin-login", "none");
    show("lin-access-denied", "none");
    show("lin-consent", "none");
    show("lin-app", "none");
  }

  /* ---------- token storage ---------- */

  function getToken() {
    if (memoryToken) return memoryToken;
    try { return sessionStorage.getItem(TOKEN_KEY) || null; } catch (e) { return null; }
  }
  function setToken(t) {
    memoryToken = t || null;
    try {
      if (t) sessionStorage.setItem(TOKEN_KEY, t);
      else sessionStorage.removeItem(TOKEN_KEY);
    } catch (e) { /* storage disabled — the in-memory mirror still works for this tab */ }
    window.OG_SESSION_TOKEN = t || undefined; // features.js's fast path
  }
  function clearToken() { setToken(null); }

  /* ---------- routing rules, all derived from the server's own view ---------- */

  // A "research participant" for the purposes of the consent gate: an account_type of
  // research that is not the platform's own administrator. ResearchAdmin accounts reach the
  // app (and the admin interface) regardless of account_type, because gating the only admin
  // behind a consent they may never grant would lock the platform.
  function isResearchParticipant(view) {
    return !!view && view.account_type === "research" && view.role !== "ResearchAdmin";
  }
  function needsConsent(view) {
    return isResearchParticipant(view) && (!view.consent || view.consent.status !== "granted");
  }

  function applyAccountClass(view) {
    // The account-type-conditional notices (T1a) key off this class; setting it here means an
    // in-app notice is correct immediately after login rather than waiting on features.js's own
    // (independent) researchmyfeatures round trip.
    try {
      document.body.classList.toggle("og-account-operational", !!view && view.account_type === "operational");
    } catch (e) {}
  }

  function setAdminNavVisible(isAdmin) {
    document.querySelectorAll("[data-nav-admin-only]").forEach(function (n) {
      n.hidden = !isAdmin;
    });
  }

  function updateIdentityChrome(view) {
    var emailEl = el("auth-email-display");
    if (emailEl) emailEl.textContent = view ? (view.display_name || view.pseudonymous_code || "") : "";
  }

  /* ---------- screen transitions ---------- */

  function showLoginScreen() {
    hideAllScreens();
    clearLoginError();
    show("lin-login", "flex");
    renderGoogleButton(0);
  }

  function showAccessDenied(message) {
    hideAllScreens();
    var m = el("access-denied-message");
    if (m) m.textContent = message || "Access is restricted.";
    show("lin-access-denied", "flex");
  }

  function showConsentScreen() {
    hideAllScreens();
    show("lin-consent", "flex");
    var err = el("consent-error");
    if (err) { err.textContent = ""; err.style.display = "none"; }
  }

  function showApp(view) {
    hideAllScreens();
    show("lin-app", "block");
    applyAccountClass(view);
    updateIdentityChrome(view);
    setAdminNavVisible(view && view.role === "ResearchAdmin");
  }

  function routeFromView(view) {
    currentView = view;
    // 2026-08-05. Resolved for EVERY route, before the consent branch, not only once the app
    // shows: LinApp.init() below (the only other caller of the theme sync) never runs while a
    // research participant is on the consent screen, so without this call that screen rendered
    // whatever the operational default was rather than the research pin. Invisible while the
    // two happened to be the same value; a real violation of "identical stimulus" once they
    // diverged. Idempotent — init() re-runs the same sync once consent is granted.
    try { if (window.LinApp && typeof window.LinApp.syncTheme === "function") LinApp.syncTheme(); }
    catch (e) {}
    if (needsConsent(view)) { showConsentScreen(); return; }
    showApp(view);
    // features.js resolved once at page load, before any token existed. Now that a session is
    // known, ask it to re-resolve so the account's real flags — not the "no token yet" no-op —
    // drive the og-no-* hiding classes for the rest of this session.
    try { if (window.OGFeatures && OGFeatures.refresh) OGFeatures.refresh(); } catch (e) {}
    if (window.LinApp && typeof window.LinApp.init === "function") window.LinApp.init();
  }

  /* ---------- login errors ---------- */

  function clearLoginError() {
    var e = el("login-error");
    if (e) { e.textContent = ""; e.style.display = "none"; }
  }
  function setLoginError(msg) {
    var e = el("login-error");
    if (e) { e.textContent = msg; e.style.display = "block"; }
  }

  /* ---------- username + password ---------- */

  async function submitPasswordLogin(username, password) {
    clearLoginError();
    if (!window.LinStore || !LinStore.postWithTimeout) {
      setLoginError("The project store is not available. Try again in a moment.");
      return;
    }
    var resp;
    try {
      resp = await LinStore.postWithTimeout({ action: "researchlogin", username: username, password: password });
    } catch (e) {
      setLoginError("Could not reach the server. Check your connection and try again.");
      return;
    }
    if (!resp || resp.ok !== true) {
      // Whatever the server says — "username or password not recognised" for any mismatch,
      // by design (research_identity.a_researchlogin), never a distinguishing message.
      setLoginError((resp && resp.error) || "Sign-in failed.");
      return;
    }
    setToken(resp.session_token);
    routeFromView(resp);
  }

  /* ---------- Google SSO (operational users) ---------- */

  async function ssoLogin(credential) {
    if (!window.LinStore || !LinStore.postWithTimeout) {
      showAccessDenied("The project store is not available. Try again in a moment.");
      return;
    }
    var resp;
    try {
      resp = await LinStore.postWithTimeout({ action: "researchssologin", credential: credential });
    } catch (e) {
      showAccessDenied("Could not reach the server. Try again.");
      return;
    }
    if (!resp || resp.ok !== true) {
      // Guarantee 3 lands here: a research account attempting SSO gets the server's own clear
      // explanation ("...sign in with the username and password supplied by the researcher..."),
      // not a generic denial.
      showAccessDenied((resp && resp.error) || "Google sign-in was not accepted.");
      return;
    }
    setToken(resp.session_token);
    routeFromView(resp);
  }

  function renderGoogleButton(tries) {
    tries = tries || 0;
    if (!window.LIN_GOOGLE_CLIENT_ID) return;
    if (!(window.google && google.accounts && google.accounts.id)) {
      if (tries < 60) setTimeout(function () { renderGoogleButton(tries + 1); }, 150);
      return;
    }
    google.accounts.id.initialize({
      client_id: window.LIN_GOOGLE_CLIENT_ID,
      callback: handleCredentialResponse,
      auto_select: false,
      cancel_on_tap_outside: false
    });
    var btn = el("google-signin-btn");
    if (btn) {
      btn.innerHTML = "";
      google.accounts.id.renderButton(btn, {
        theme: "filled_black", size: "large", text: "signin_with", shape: "pill", width: 280
      });
    }
  }

  function handleCredentialResponse(response) {
    if (!response || !response.credential) return;
    ssoLogin(response.credential);
  }

  /* ---------- consent ---------- */

  async function grantConsent(version) {
    if (!window.LinStore || !LinStore.postWithTimeout) return { ok: false, error: "Store not available." };
    var resp = await LinStore.postWithTimeout({
      action: "consentgrant", session_token: getToken(), consent_version: version
    });
    if (resp && resp.ok) {
      // Re-derived from the server, not patched onto the cached view locally: the gate's own
      // truth is whatever researchwhoami reports next, the same predicate used everywhere else.
      var who = await LinStore.postWithTimeout({ action: "researchwhoami", session_token: getToken() });
      if (who && who.ok) routeFromView(who);
    } else {
      var err = el("consent-error");
      if (err) { err.textContent = (resp && resp.error) || "Could not record consent."; err.style.display = "block"; }
    }
    return resp;
  }

  async function withdrawConsent() {
    if (!window.LinStore || !LinStore.postWithTimeout) return { ok: false };
    var resp = await LinStore.postWithTimeout({ action: "consentwithdraw", session_token: getToken() });
    if (resp && resp.ok) {
      var who = await LinStore.postWithTimeout({ action: "researchwhoami", session_token: getToken() });
      // Withdrawal closes the gate again: routeFromView sends a research participant straight
      // back to the consent screen, because consent.status is no longer "granted".
      if (who && who.ok) routeFromView(who);
    }
    return resp;
  }

  /* ---------- resume + sign out ---------- */

  async function resumeSession(token) {
    var resp;
    try {
      resp = await LinStore.postWithTimeout({ action: "researchwhoami", session_token: token });
    } catch (e) {
      resp = null;
    }
    if (!resp || resp.ok !== true) {
      // Expired, revoked, or deactivated — the token no longer resolves to a usable session.
      // Fresh sign-in required; no retry loop, no silent fallback to a stale identity.
      clearToken();
      showLoginScreen();
      return;
    }
    setToken(token);
    routeFromView(resp);
  }

  function logout() {
    clearToken();
    currentView = null;
    try { if (window.LinStore && LinStore.clearPortfolioCache) LinStore.clearPortfolioCache(); } catch (e) {}
    if (window.google && window.google.accounts) {
      try { google.accounts.id.disableAutoSelect(); } catch (e) {}
    }
    showLoginScreen();
  }

  function getEmail() {
    // Back-compat name for the existing app.js call site (topbar identity display). Returns
    // whatever label is appropriate for the signed-in account — never a real identity for a
    // research participant, whose only identifier anywhere in the system is the pseudonymous
    // code.
    return currentView ? (currentView.display_name || currentView.pseudonymous_code || "") : "";
  }

  /* ---------- boot ---------- */

  function init() {
    var token = getToken();
    if (!token) { showLoginScreen(); return false; }
    // Always resolved asynchronously against the server, even for a token that looks
    // well-formed: the current_stage and consent state a resumed session routes on are never
    // assumed from the token alone. app.js's boot() already tolerates init() returning false
    // and the real initialization happening later via a callback — routeFromView calls
    // LinApp.init() once the resume resolves, the same pattern the SSO callback already used.
    resumeSession(token);
    return false;
  }

  return {
    init: init,
    logout: logout,
    getEmail: getEmail,
    isAuthenticated: function () { return !!getToken(); },
    handleCredentialResponse: handleCredentialResponse,
    submitPasswordLogin: submitPasswordLogin,
    grantConsent: grantConsent,
    withdrawConsent: withdrawConsent,
    currentView: function () { return currentView; },
    getToken: getToken
  };
})();

// Global callback Google Identity Services invokes by name.
function handleCredentialResponse(response) {
  LinAuth.handleCredentialResponse(response);
}

// Static form/button wiring — not re-run on screen transitions, since these elements are
// permanent parts of index.html rather than content auth.js renders itself.
document.addEventListener("DOMContentLoaded", function () {
  var form = document.getElementById("password-login-form");
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var u = document.getElementById("login-username");
      var p = document.getElementById("login-password");
      LinAuth.submitPasswordLogin(u ? u.value : "", p ? p.value : "");
    });
  }
  var consentBtn = document.getElementById("consent-grant-btn");
  if (consentBtn) {
    consentBtn.addEventListener("click", function () {
      // The consent screen carries no version selector — a placeholder document has only one
      // version. Bump this string when the reviewed text replaces the placeholder.
      LinAuth.grantConsent("placeholder-v0");
    });
  }
});
