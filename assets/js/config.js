/* ============================================================
   Opus Gubernatio — config.js
   ------------------------------------------------------------
   Single backend endpoint for the whole app.

   SAME-ORIGIN (T1). The app is served by the Render service that
   also serves /exec, so this is a relative path. Three things
   follow from that and none of them are incidental:

     - No CORS request is issued at all, so no preflight to avoid
       and no origin allowlist to keep in step with a deploy.
     - No Apps Script redirect hop, which is what
       script.googleusercontent.com in the CSP existed to allow.
     - Session cookies and tokens stay first-party.

   ROLLBACK. To point the frontend back at the Apps Script
   backend, comment the line below and uncomment the one after
   it. It is kept as a comment rather than a runtime fallback on
   purpose: a fallback that silently reaches a second backend
   would write research data to whichever one happened to answer.

   Note the GitHub Pages copy still loads this file, so it will
   resolve /exec against github.io and degrade to the non-fatal
   "can't reach store" state. That origin is now a static mirror,
   not a working deployment.
   ============================================================ */

window.LIN_API_URL = "/exec";
/* ROLLBACK ONLY — do not enable alongside the line above:
window.LIN_API_URL = "https://script.google.com/macros/s/AKfycbwhmg_1L_RjbxPTR0IF3xpmHgLLzHA67O3mH27uqrAFfv8bF9U359yBqwjqbZO3YNTO/exec";
*/

/* ---------- Google OAuth — Stage 1 auth ----------
   Only LIN_AUTHORIZED_EMAIL may access the app.

   ORIGINS, not redirect URIs. auth.js uses Google Identity Services
   (google.accounts.id.initialize + renderButton) with an in-page JavaScript
   callback. There is no ux_mode:'redirect', no login_uri and no redirect_uri
   anywhere in this codebase, so the Google Cloud console's "Authorized redirect
   URIs" list is not consulted and can stay empty. Only "Authorized JavaScript
   origins" is checked, and a missing entry there is what produces
   Error 400: origin_mismatch.

   Both origins need to be listed while the move off GitHub Pages completes:
     https://linprojectradar.onrender.com   (serves the app and /exec)
     https://mrnyanlintun.github.io         (static mirror; see the note above -
                                             sign-in works, but /exec resolves
                                             against github.io and finds nothing)

   Leave the client id unset to bypass auth locally. */
window.LIN_GOOGLE_CLIENT_ID = "604934233462-99079h2pcs0di52h4khj393cj0uu4rbt.apps.googleusercontent.com";
window.LIN_AUTHORIZED_EMAIL = "mrnyanlintun@gmail.com";

/* ============================================================
   STATUS COLOURS — the JS half of the single source of truth.
   ------------------------------------------------------------
   radar.css owns the palette (--status-*). Anything that renders through
   CSS/SVG/DOM should use var(--status-*) directly and re-theme for free.
   This map exists for <canvas> renderers (charts3d, forcenet, neural_flow,
   projectnet2d, deepdive) which cannot read var().

   Values are read back from the CSS vars at init, so the palette is defined
   in exactly one place; the literals below are only a fallback for when the
   stylesheet hasn't parsed or a var is missing. Keys match the canonical
   PCEIF labels in decision.js (Complete/Green/Yellow/Amber/Red + None).

   Theme switches change the vars, so app.js calls refresh() from applyTheme();
   canvases pick the new palette up on their next draw.
   ============================================================ */
(function () {
  var FALLBACK = {
    Complete: "#4ea0ff",
    Green:    "#2ee66b",
    Yellow:   "#ffe066",
    Amber:    "#ff8c1a",
    Red:      "#ff3b30",
    None:     "#26344f"
  };
  var CSS_VAR = {
    Complete: "--status-complete",
    Green:    "--status-green",
    Yellow:   "--status-yellow",
    Amber:    "--status-amber",
    Red:      "--status-red",
    None:     "--status-nodata"
  };

  var map = {};

  function refresh() {
    var cs = null;
    // Read off <body>, not <html>: the theme blocks are body[data-theme="…"],
    // so body resolves :root through inheritance AND sees any per-theme
    // override. Falls back to <html> if this ever runs before body exists.
    try { cs = window.getComputedStyle(document.body || document.documentElement); } catch (e) {}
    Object.keys(CSS_VAR).forEach(function (key) {
      var v = "";
      if (cs) { try { v = String(cs.getPropertyValue(CSS_VAR[key]) || "").trim(); } catch (e) {} }
      map[key] = v || FALLBACK[key];
    });
    return map;
  }

  // Non-enumerable so Object.keys(LIN_STATUS_COLORS) stays a clean status list.
  Object.defineProperty(map, "refresh", { value: refresh, enumerable: false });

  refresh();
  window.LIN_STATUS_COLORS = map;
})();

/* ============================================================
   STATUS LETTER / SHAPE — the shared non-color redundant cue.
   ------------------------------------------------------------
   Color-blind-safe accessibility: every status dot/pill/blip/pin/node also
   carries a letter (C/G/Y/A/R) and, where a marker is too small to hold a
   legible letter, a distinct SHAPE (ring/circle/triangle/diamond/square).
   Single source of truth so every renderer (app.js, deepdive.js, forcenet.js,
   projectnet2d.js, neural_flow.js) agrees on the same mapping. Status strings
   arrive in many casings/spellings across the app ("Complete", "green",
   "light-amber", "orange", "Red-review", "blue") — normalize by substring
   match the same way categories.js's getCategoryStatus keyword-fallback does.
   ============================================================ */
(function () {
  function norm(status) { return String(status || "").toLowerCase(); }

  window.linStatusLetter = function (status) {
    var s = norm(status);
    if (s.indexOf("complete") >= 0 || s.indexOf("blue") >= 0) return "C";
    if (s.indexOf("green") >= 0) return "G";
    if (s.indexOf("yellow") >= 0 || s.indexOf("light-amber") >= 0) return "Y";
    if (s.indexOf("amber") >= 0 || s.indexOf("orange") >= 0) return "A";
    if (s.indexOf("red") >= 0) return "R";
    return "";
  };

  // circle = Green, triangle = Yellow, diamond = Amber, square = Red,
  // ring (hollow circle) = Complete. Used where a marker is too small for
  // a legible letter (tiny flow-diagram dots, small radar blips at zoom-out).
  window.linStatusShape = function (status) {
    var s = norm(status);
    if (s.indexOf("complete") >= 0 || s.indexOf("blue") >= 0) return "ring";
    if (s.indexOf("green") >= 0) return "circle";
    if (s.indexOf("yellow") >= 0 || s.indexOf("light-amber") >= 0) return "triangle";
    if (s.indexOf("amber") >= 0 || s.indexOf("orange") >= 0) return "diamond";
    if (s.indexOf("red") >= 0) return "square";
    return "circle";
  };

  function parseColorToRGB(c) {
    c = String(c || "").trim();
    var m = c.match(/^#?([0-9a-f]{6})$/i);
    if (m) {
      var h = m[1];
      return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
    }
    m = c.match(/rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)/i);
    if (m) return [parseFloat(m[1]), parseFloat(m[2]), parseFloat(m[3])];
    return null;
  }
  // Perceptual (ITU BT.601) luminance-based ink color so the letter reads
  // on ANY of the 5 status fills (or a re-themed var(--status-*) override):
  // dark ink on the light fills (Complete/Green/Yellow/Amber), light ink on
  // the one genuinely dark-saturated fill (Red).
  window.linStatusInk = function (colorValue) {
    var rgb = parseColorToRGB(colorValue);
    if (!rgb) return "#0b1220";
    var luma = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255;
    return luma > 0.5 ? "#0b1220" : "#f5f8ff";
  };
})();


/* ============================================================
   linLocationNote(project) — ONE definition of how a project's
   location reads, because four surfaces render it (workspace's
   locationLine and project sub-line, detail's globe note, and
   ingest's geocodeOutcome) and they had already drifted apart
   once. Same reasoning as disclaimers.js: a sentence rendered in
   four places is a sentence that diverges in four places.

   THREE STATES, NOT TWO. The third is the one that did not exist
   before 2026-08-02, when a failed geocode erased the coordinates
   it could not replace:

     matched  — lat/lng belong to the address now stored.
     stale    — lat/lng were RETAINED from an earlier address
                because the new one could not be geocoded. The pin
                is real but it is not this address's pin, and
                saying so is the whole point of the state.
     none     — no coordinates at all.

   Returns { kind, text, warn }. `warn` is whether the surface
   should use its warning styling; a stale position warns, because
   an unlabelled old pin is exactly the failure being fixed.
   ============================================================ */
(function () {
  window.linLocationNote = function (p) {
    p = p || {};
    var has = p.lat != null && p.lng != null;
    var matched = p.formattedAddress || "";
    if (has && p.geocodeStale) {
      return {
        kind: "stale",
        warn: true,
        text: "Map position is for the previous address" +
          (matched ? " (" + matched + ")" : "") + ". " +
          (p.geocodeError || "The new address has not been matched yet.")
      };
    }
    if (p.geocodeError) {
      return { kind: "none", warn: true, text: "No map position. " + p.geocodeError };
    }
    if (has || matched) {
      return { kind: "matched", warn: false, text: matched ? "Matched to: " + matched : "Located." };
    }
    return { kind: "none", warn: true,
             text: "No map position. Add a site address to place this project." };
  };
})();
