/* =================== LIN AUTH — Google Sign-In ===================
   Stage 1 of the PCEIF commercialization roadmap. Gates the app behind
   Google OAuth; only window.LIN_AUTHORIZED_EMAIL may enter. The Google JWT
   is decoded client-side for the email claim and a short session is kept in
   localStorage (8h). When the client ID / authorized email are not configured,
   auth is bypassed so local / offline use is never bricked. */
var LinAuth = (function () {
  var AUTH_KEY = 'lin-auth-token';
  var AUTH_EMAIL_KEY = 'lin-auth-email';
  var AUTH_EXPIRY_KEY = 'lin-auth-expiry';
  var SESSION_HOURS = 8;

  function configured() {
    var cid = window.LIN_GOOGLE_CLIENT_ID;
    return !!(cid && window.LIN_AUTHORIZED_EMAIL && String(cid).indexOf('YOUR_') !== 0);
  }
  function el(id) { return document.getElementById(id); }
  function show(id, mode) { var e = el(id); if (e) e.style.display = mode; }

  function isAuthenticated() {
    var token = localStorage.getItem(AUTH_KEY);
    var expiry = localStorage.getItem(AUTH_EXPIRY_KEY);
    var email = localStorage.getItem(AUTH_EMAIL_KEY);
    if (!token || !expiry || !email) return false;
    if (Date.now() > parseInt(expiry, 10)) { logout(); return false; }
    if (email !== window.LIN_AUTHORIZED_EMAIL) { logout(); return false; }
    return true;
  }

  function getEmail() { return localStorage.getItem(AUTH_EMAIL_KEY); }

  function login(credential) {
    // Decode the email claim from the Google ID-token JWT (payload is the
    // middle base64url segment). This is for UX gating only — the production
    // (Stage 2) backend must verify the token signature server-side.
    try {
      var part = credential.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
      var payload = JSON.parse(atob(part));
      var email = payload.email;
      if (email !== window.LIN_AUTHORIZED_EMAIL) { showAccessDenied(email); return false; }
      var expiry = Date.now() + (SESSION_HOURS * 60 * 60 * 1000);
      localStorage.setItem(AUTH_KEY, credential);
      localStorage.setItem(AUTH_EMAIL_KEY, email);
      localStorage.setItem(AUTH_EXPIRY_KEY, String(expiry));
      return true;
    } catch (e) { console.error('Auth error:', e); return false; }
  }

  function logout() {
    localStorage.removeItem(AUTH_KEY);
    localStorage.removeItem(AUTH_EMAIL_KEY);
    localStorage.removeItem(AUTH_EXPIRY_KEY);
    if (window.google && window.google.accounts) {
      try { google.accounts.id.disableAutoSelect(); } catch (e) {}
    }
    showLoginScreen();
  }

  function showApp() {
    show('lin-login', 'none');
    show('lin-access-denied', 'none');
    show('lin-app', 'block');
  }

  function showAccessDenied(email) {
    show('lin-app', 'none');
    show('lin-login', 'none');
    var d = el('denied-email'); if (d) d.textContent = email;
    show('lin-access-denied', 'flex');
  }

  // The GSI client script is async/defer, so window.google may not exist yet
  // when we first try to render the button — retry until it loads.
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
    var btn = el('google-signin-btn');
    if (btn) {
      btn.innerHTML = '';
      google.accounts.id.renderButton(btn, {
        theme: 'filled_black', size: 'large', text: 'signin_with', shape: 'pill', width: 280
      });
    }
  }

  function showLoginScreen() {
    show('lin-app', 'none');
    show('lin-access-denied', 'none');
    show('lin-login', 'flex');
    renderGoogleButton(0);
  }

  function handleCredentialResponse(response) {
    if (!response || !response.credential) return;
    if (login(response.credential)) {
      showApp();
      if (window.LinApp && typeof window.LinApp.init === 'function') {
        window.LinApp.init();
      } else {
        window.location.reload();
      }
    }
  }

  function init() {
    // Not configured → don't gate; let the app run (local / offline dev).
    if (!configured()) { showApp(); return true; }
    if (isAuthenticated()) { showApp(); return true; }
    showLoginScreen();
    return false;
  }

  return {
    init: init,
    login: login,
    logout: logout,
    isAuthenticated: isAuthenticated,
    getEmail: getEmail,
    handleCredentialResponse: handleCredentialResponse
  };
})();

// Global callback Google Identity Services invokes by name.
function handleCredentialResponse(response) {
  LinAuth.handleCredentialResponse(response);
}
