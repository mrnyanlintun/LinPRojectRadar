/* ============================================================
   lin-project-radar — config.js  (Phase 2)
   ------------------------------------------------------------
   Single backend endpoint for the whole app. Paste the Google
   Apps Script Web App /exec URL here. This is the ONLY network
   endpoint the front end is permitted to call in Phase 2.

   Leave as the placeholder to run in offline/cache mode (the UI
   degrades gracefully and shows a non-fatal "can't reach store"
   state instead of crashing).
   ============================================================ */

window.LIN_API_URL = "https://script.google.com/macros/s/AKfycbwhmg_1L_RjbxPTR0IF3xpmHgLLzHA67O3mH27uqrAFfv8bF9U359yBqwjqbZO3YNTO/exec";

/* ---------- Google OAuth — Stage 1 auth (PCEIF commercialization) ----------
   Only LIN_AUTHORIZED_EMAIL may access the app. The Client ID is bound to the
   GitHub Pages origin in the Google Cloud console (Authorized JavaScript
   origins / redirect URIs). Leave the client id unset to bypass auth locally. */
window.LIN_GOOGLE_CLIENT_ID = "604934233462-99079h2pcs0di52h4khj393cj0uu4rbt.apps.googleusercontent.com";
window.LIN_AUTHORIZED_EMAIL = "mrnyanlintun@gmail.com";

