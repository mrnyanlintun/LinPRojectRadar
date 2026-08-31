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
    None:     "#26344f",
    // Not a verdict: a module not relevant to this project's sector. Deliberately its OWN
    // blue, distinct from Complete (a real verdict) — see radar.css's --status-notrelevant-text.
    NotRelevant: "#5b3dd6"
  };
  var CSS_VAR = {
    Complete: "--status-complete",
    Green:    "--status-green",
    Yellow:   "--status-yellow",
    Amber:    "--status-amber",
    Red:      "--status-red",
    None:     "--status-nodata",
    NotRelevant: "--status-notrelevant-text"
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

/* ============================================================
   RUN 94b. IDENTITY COLOURS, GENERATED FROM THE ROSTER AT RUNTIME.
   ------------------------------------------------------------
   The owner's ruling (Run 94b order, section 4): EVERY MODULE GETS ITS OWN
   COLOUR, documents get their own colour set and categories theirs, and every
   line takes the colour of the node it leaves so a stream can be traced by eye
   from a module to its category and on to the status.

   NOTHING HERE IS HAND-WRITTEN PER MODULE. The palette is a pure function of
   the list of keys handed in, so a module entering or leaving service needs no
   colour added or removed by hand -- which is section 4.4 of the order.

   HOW ADJACENT COLOURS ARE KEPT APART. Hue advances by the GOLDEN ANGLE
   (137.50776 deg) per position, so two colours drawn in adjacent rows are
   always about 137 degrees apart in hue -- the maximum any equidistributed
   sequence can guarantee -- and lightness and saturation cycle on periods of 3
   and 4 underneath it, so hue is never the only thing separating a pair.

   BAND COLOURS ARE NOT NEGOTIABLE (section 4.3). The status band colours keep
   their existing meaning and their existing values from the site theme; they
   are read at call time from window.LIN_STATUS_COLORS, which config.js derives
   from the --status-* vars and refreshes on a theme change. Any generated
   identity colour that lands within BAND_MIN_DE of a band colour is ROTATED
   until it does not; the band colour never moves.

   THE COLOUR DIFFERENCE MEASURE IS CIE76 (dE*ab): the plain Euclidean distance
   in CIE L*a*b* under D65. It is stated rather than implied, and it is the same
   function the charts and the drivers measure with, so a reported number and a
   shipped decision cannot come from two different formulas.
   ============================================================ */
(function () {
  var GOLDEN = 137.50776405003785;
  var BAND_MIN_DE = 25;      /* see below */
  var SET_MIN_DE = 18;       /* two colours in one set are never nearer than this if it can be helped */      /* an identity colour nearer than this to a band colour is moved */

  function hex2rgb(h) {
    h = String(h || "").trim();
    if (h.charAt(0) === "#") h = h.slice(1);
    if (h.length === 3) h = h.charAt(0)+h.charAt(0)+h.charAt(1)+h.charAt(1)+h.charAt(2)+h.charAt(2);
    if (!/^[0-9a-fA-F]{6}$/.test(h)) return null;
    return [parseInt(h.slice(0,2),16), parseInt(h.slice(2,4),16), parseInt(h.slice(4,6),16)];
  }
  function rgb2hex(r, g, b) {
    function c(v) { v = Math.max(0, Math.min(255, Math.round(v))); return (v<16?"0":"")+v.toString(16); }
    return "#" + c(r) + c(g) + c(b);
  }
  function hsl2rgb(h, s, l) {
    h = ((h % 360) + 360) % 360 / 360; s = s / 100; l = l / 100;
    function f(p, q, t) {
      if (t < 0) t += 1; if (t > 1) t -= 1;
      if (t < 1/6) return p + (q - p) * 6 * t;
      if (t < 1/2) return q;
      if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
      return p;
    }
    if (s === 0) return [l*255, l*255, l*255];
    var q = l < 0.5 ? l * (1 + s) : l + s - l * s, p = 2 * l - q;
    return [f(p,q,h+1/3)*255, f(p,q,h)*255, f(p,q,h-1/3)*255];
  }
  function rgb2lab(rgb) {
    var v = rgb.map(function (u) {
      u = u / 255;
      return u > 0.04045 ? Math.pow((u + 0.055) / 1.055, 2.4) : u / 12.92;
    });
    var X = (v[0]*0.4124564 + v[1]*0.3575761 + v[2]*0.1804375) / 0.95047;
    var Y = (v[0]*0.2126729 + v[1]*0.7151522 + v[2]*0.0721750) / 1.00000;
    var Z = (v[0]*0.0193339 + v[1]*0.1191920 + v[2]*0.9503041) / 1.08883;
    function f(t) { return t > 0.008856 ? Math.pow(t, 1/3) : (7.787 * t) + 16/116; }
    var fx = f(X), fy = f(Y), fz = f(Z);
    return [116*fy - 16, 500*(fx - fy), 200*(fy - fz)];
  }

  /* CIE76 dE*ab. Named in the code so a report cannot claim a formula the
     shipped palette did not use. */
  window.LIN_LAB = function (hex) {
    var rgb = hex2rgb(hex);
    return rgb ? rgb2lab(rgb) : null;
  };
  window.LIN_COLOR_DELTA_E = function (a, b) {
    var la = window.LIN_LAB(a), lb = window.LIN_LAB(b);
    if (!la || !lb) return null;
    var d0 = la[0]-lb[0], d1 = la[1]-lb[1], d2 = la[2]-lb[2];
    return Math.sqrt(d0*d0 + d1*d1 + d2*d2);
  };

  /* The three colour SETS. Each is a different lightness/saturation regime, so a
     document colour, a module colour and a category colour are told apart by more
     than their hue: documents sit light and soft, modules mid and strong,
     categories deep and strong. `off` starts each set at a different point on the
     hue circle so the three sets do not simply repeat one another. */
  var SETS = {
    module:   { off:  0, L: [46, 60, 53, 67], S: [78, 62, 90] },
    document: { off: 47, L: [70, 76, 64],     S: [42, 55, 34]  },
    category: { off: 91, L: [38, 46, 32],     S: [72, 88, 60]  }
  };

  function bandColors() {
    var m = window.LIN_STATUS_COLORS || {};
    var out = [];
    Object.keys(m).forEach(function (k) {
      var rgbOk = hex2rgb(m[k]);
      if (rgbOk) out.push({ name: k, hex: m[k] });
    });
    return out;
  }

  /* keys: an ARRAY OF IDENTIFIERS, in the order they will be drawn. The palette is
     positional, so "adjacent in this array" is "adjacent on screen", which is the
     thing section 4.2 asks to be measured. Returns { byKey, list, bands, minAdjacentDeltaE,
     minBandDeltaE, formula }. */
  window.LIN_IDENTITY_PALETTE = function (keys, setName) {
    var set = SETS[setName] || SETS.module;
    var bands = bandColors();
    var list = [], byKey = {};
    /* GREEDY, WITH TWO CONSTRAINTS, and it is deterministic: the same roster in the
       same order always yields the same palette.
         1. no identity colour within BAND_MIN_DE of a band colour  (section 4.3);
         2. no identity colour within SET_MIN_DE of one already assigned, so "its own
            colour" means its own across the whole set and not merely against its
            neighbour  (section 4, first sentence).
       The golden-angle hue is the FIRST candidate at every position, so when both
       constraints are already satisfied -- the usual case -- the sequence is exactly
       the equidistributed one and adjacency stays maximally separated. When they are
       not, the position walks its hue and lightness and keeps the candidate with the
       LARGEST minimum distance it found, which is the honest fallback: it never
       silently ships a duplicate, and the achieved minimum is reported below. */
    (keys || []).forEach(function (key, i) {
      var L0 = set.L[i % set.L.length];
      var S0 = set.S[i % set.S.length];
      var best = null, bestScore = -1;
      for (var attempt = 0; attempt < 64 && bestScore < SET_MIN_DE; attempt++) {
        var h = set.off + i * GOLDEN + attempt * 23.7;
        var L = L0 + ((attempt % 3) - 1) * 7;
        var S = Math.max(28, Math.min(96, S0 + ((attempt % 5) - 2) * 6));
        var rgb = hsl2rgb(h, S, L);
        var cand = rgb2hex(rgb[0], rgb[1], rgb[2]);
        var bandOk = true, nearestBand = Infinity;
        for (var b = 0; b < bands.length; b++) {
          var db = window.LIN_COLOR_DELTA_E(cand, bands[b].hex);
          if (db < nearestBand) nearestBand = db;
        }
        if (nearestBand < BAND_MIN_DE) bandOk = false;
        var nearestOwn = Infinity;
        for (var q = 0; q < list.length; q++) {
          var dq = window.LIN_COLOR_DELTA_E(cand, list[q].hex);
          if (dq < nearestOwn) nearestOwn = dq;
        }
        /* A band collision is disqualifying, not merely costly: section 4.3 is absolute.
           It is expressed as a large negative score so a band-colliding candidate can
           only ever win when NO candidate cleared the bands, which is itself reported. */
        var score = (bandOk ? 0 : -1000) + Math.min(nearestOwn, 1000);
        if (score > bestScore) { bestScore = score; best = cand; }
      }
      byKey[key] = best;
      list.push({ key: key, hex: best });
    });
    /* The two measurements the order requires, computed by the palette itself so the
       number a report prints is the number the chart shipped. */
    var minAdj = null, minAdjPair = null;
    for (var i2 = 1; i2 < list.length; i2++) {
      var d = window.LIN_COLOR_DELTA_E(list[i2-1].hex, list[i2].hex);
      if (d !== null && (minAdj === null || d < minAdj)) { minAdj = d; minAdjPair = [list[i2-1].key, list[i2].key]; }
    }
    var minBand = null, minBandPair = null;
    list.forEach(function (o) {
      bands.forEach(function (b) {
        var d = window.LIN_COLOR_DELTA_E(o.hex, b.hex);
        if (d !== null && (minBand === null || d < minBand)) { minBand = d; minBandPair = [o.key, b.name]; }
      });
    });
    var minAny = null, minAnyPair = null;
    for (var a1 = 0; a1 < list.length; a1++) for (var a2 = a1+1; a2 < list.length; a2++) {
      var dd = window.LIN_COLOR_DELTA_E(list[a1].hex, list[a2].hex);
      if (dd !== null && (minAny === null || dd < minAny)) { minAny = dd; minAnyPair = [list[a1].key, list[a2].key]; }
    }
    return { byKey: byKey, list: list, bands: bands, formula: "CIE76 dE*ab (CIE L*a*b*, D65)",
             minAnyDeltaE: minAny, minAnyPair: minAnyPair, setMinRequired: SET_MIN_DE,
             minAdjacentDeltaE: minAdj, minAdjacentPair: minAdjPair,
             minBandDeltaE: minBand, minBandPair: minBandPair, bandMinRequired: BAND_MIN_DE };
  };
})();
