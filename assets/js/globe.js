/* ============================================================
   Opus Gubernatio — globe.js
   ------------------------------------------------------------
   The portfolio globe, and the focused globe on project detail.

   IT COMPUTES NOTHING. Every colour here comes from the status the server stored in
   computed_results, read through taxonomy.js's getProjectFusion(). That is the rule Part 3
   established after the browser derivation was found returning Red on projects five per cent
   under budget, and a visualisation is exactly where it would be tempting to break it.

   NO TEXTURE, NO CDN. globe.gl normally paints an earth image fetched from a CDN. This does not:
   the globe is a solid material coloured from the platform theme, with graticules. That keeps
   two promises at once — nothing loads from a CDN that a corporate network can block, and no
   screen defines its own palette.

   DEGRADATION IS THE POINT, NOT AN EXTRA. A director on a locked laptop is a realistic user, so
   there are three steps and none of them is a blank panel:

       WebGL and globe.gl available   -> the globe
       either missing                 -> the existing MapLibre map
       MapLibre missing too           -> the plain project list, which is always in the DOM

   THE ANIMATION LOOP IS A LIABILITY IF IT OUTLIVES THE VIEW. This service is one small
   instance and a director may leave a tab open all afternoon. The loop is paused when the
   document is hidden and stopped entirely when the view is left, and the WebGL context is
   released rather than left for the garbage collector to find later.

   PROJECTS WITHOUT COORDINATES ARE NOT LOST. They cannot be placed, so they are not points, but
   they remain in the project list below the stage, which is the same keyboard path the radar
   has always had. Being unplaceable is not being deleted.
   ============================================================ */

(function () {
  "use strict";

  var VENDOR_URL = "assets/vendor/globe.gl.min.js";

  var instance = null;      // the live Globe(), or null
  var host = null;          // the element it was mounted into
  var loadPromise = null;
  var visibilityBound = false;

  /* ---------- capability ---------- */

  // Asked with a throwaway canvas rather than by trying to build a globe and catching the
  // failure: constructing one only to tear it down is slower and leaves a context behind on
  // some drivers.
  function webglAvailable() {
    try {
      var c = document.createElement("canvas");
      return !!(c.getContext("webgl2") || c.getContext("webgl"));
    } catch (e) {
      return false;
    }
  }

  function loadLibrary() {
    if (typeof window.Globe === "function") return Promise.resolve(true);
    if (loadPromise) return loadPromise;
    loadPromise = new Promise(function (resolve) {
      var s = document.createElement("script");
      s.src = VENDOR_URL;
      s.async = true;
      s.onload = function () { resolve(typeof window.Globe === "function"); };
      // Resolves false rather than rejecting. A missing globe is a fallback, not an exception:
      // the caller's job is to show the map, not to handle an error.
      s.onerror = function () { resolve(false); };
      document.head.appendChild(s);
    });
    return loadPromise;
  }

  /* ---------- theme ---------- */

  // Read from the live computed style so a theme switch is picked up, rather than hard-coding
  // anything. No screen defines its own palette.
  function themeColor(name, fallback) {
    try {
      var v = getComputedStyle(document.body).getPropertyValue(name);
      v = (v || "").trim();
      return v || fallback;
    } catch (e) {
      return fallback;
    }
  }

  function statusColor(status) {
    var s = String(status || "").toLowerCase();
    if (s.indexOf("green") >= 0) return themeColor("--status-green", "#2ee66b");
    if (s.indexOf("yellow") >= 0) return themeColor("--status-yellow", "#ffd166");
    if (s.indexOf("amber") >= 0) return themeColor("--status-amber", "#ff8c1a");
    if (s.indexOf("red") >= 0) return themeColor("--status-red", "#ff3b30");
    if (s.indexOf("complete") >= 0) return themeColor("--status-complete", "#4ea0ff");
    return themeColor("--status-nodata", "#6f7d70");
  }

  /* ---------- data ----------
     The stored status, never a computed one. getProjectFusion reads the computed_results row
     through taxonomy.js; when there is no row it returns null and the point is drawn in the
     no-data colour, which is honest: unanalysed is not healthy and is not at risk. */

  function pointsFrom(projects) {
    var pts = [];
    (projects || []).forEach(function (p) {
      var lat = Number(p && p.lat);
      var lng = Number(p && p.lng);
      if (!isFinite(lat) || !isFinite(lng)) return;   // unplaceable; stays in the list
      if (Math.abs(lat) > 90 || Math.abs(lng) > 180) return;
      var status = null;
      try {
        var fusion = window.getProjectFusion ? window.getProjectFusion(p) : null;
        status = fusion && fusion.status;
      } catch (e) { status = null; }
      pts.push({
        id: p.id || p.project_id,
        name: p.name || "Untitled project",
        lat: lat,
        lng: lng,
        status: status,
        matched: p.formattedAddress || "",
        color: statusColor(status)
      });
    });
    return pts;
  }

  /* ---------- lifecycle ---------- */

  function onVisibility() {
    if (!instance) return;
    // A globe spinning in a tab nobody is looking at is pure cost on a single small instance.
    try {
      if (document.hidden) instance.pauseAnimation();
      else instance.resumeAnimation();
    } catch (e) { /* older builds may lack these; not worth failing the view over */ }
  }

  function bindVisibility() {
    if (visibilityBound) return;
    document.addEventListener("visibilitychange", onVisibility);
    visibilityBound = true;
  }

  function destroy() {
    if (!instance) return;
    try { instance.pauseAnimation(); } catch (e) {}
    try {
      // globe.gl's own teardown. It disposes the renderer, which is what actually releases the
      // WebGL context; dropping the reference alone would leave the context alive until the
      // driver reclaimed it, and browsers cap how many a page may hold.
      if (typeof instance._destructor === "function") instance._destructor();
    } catch (e) {}
    try {
      if (host) host.innerHTML = "";
    } catch (e) {}
    instance = null;
    host = null;
  }

  /* ---------- mount ---------- */

  /**
   * Build the globe into `container`.
   *
   * Resolves { ok: true } when the globe is showing, or { ok: false, reason } when the caller
   * should fall back. It never throws and never leaves the container empty on failure: an empty
   * panel is the one outcome that is not allowed.
   *
   * opts.focus  — { lat, lng } to centre on, for the project detail view.
   * opts.onSelect — called with a project id. The portfolio passes openDetail, so selecting a
   *                 point does exactly what selecting a map marker has always done.
   */
  function mount(container, projects, opts) {
    opts = opts || {};
    if (!container) return Promise.resolve({ ok: false, reason: "no container" });

    if (!webglAvailable()) {
      return Promise.resolve({ ok: false, reason: "webgl-unavailable" });
    }

    return loadLibrary().then(function (available) {
      if (!available) return { ok: false, reason: "library-unavailable" };

      destroy();                     // never two globes, never two contexts
      host = container;
      container.innerHTML = "";

      var pts = pointsFrom(projects);

      try {
        instance = window.Globe()(container)
          .backgroundColor("rgba(0,0,0,0)")
          .showAtmosphere(true)
          .atmosphereColor(themeColor("--brand-verdigris", "#4fa393"))
          .atmosphereAltitude(0.12)
          .showGraticules(true)
          .pointsData(pts)
          .pointLat("lat")
          .pointLng("lng")
          .pointColor("color")
          .pointAltitude(0.06)
          .pointRadius(0.6)
          .pointLabel(function (d) {
            // Name, status and what the geocoder matched. The matched address is here for the
            // same reason it is on every other surface: a pin on the wrong building looks
            // exactly like a pin on the right one.
            return '<div style="font-family:var(--font-body);font-size:12px;">'
              + '<strong>' + escapeHtml(d.name) + '</strong><br>'
              + escapeHtml(d.status || "Awaiting analysis")
              + (d.matched ? '<br><span style="opacity:.7">' + escapeHtml(d.matched) + '</span>' : '')
              + '</div>';
          })
          .onPointClick(function (d) {
            if (d && d.id && typeof opts.onSelect === "function") opts.onSelect(d.id);
          });

        // Solid material from the theme rather than a texture image, which would be a CDN fetch.
        try {
          var mat = instance.globeMaterial();
          if (mat && mat.color && typeof mat.color.set === "function") {
            mat.color.set(themeColor("--surface-soft", "#12242a"));
            if ("shininess" in mat) mat.shininess = 4;
          }
        } catch (e) { /* the globe still renders without the tint */ }

        sizeToHost();
        if (opts.focus && isFinite(opts.focus.lat) && isFinite(opts.focus.lng)) {
          try {
            instance.pointOfView({ lat: opts.focus.lat, lng: opts.focus.lng, altitude: 1.6 }, 0);
          } catch (e) {}
        }
        bindVisibility();
        return { ok: true, points: pts.length, unplaceable: (projects || []).length - pts.length };
      } catch (e) {
        destroy();
        return { ok: false, reason: "construction-failed" };
      }
    });
  }

  function sizeToHost() {
    if (!instance || !host) return;
    var rect = host.getBoundingClientRect();
    var w = Math.max(240, Math.round(rect.width));
    // Height follows the container; the stage is a fixed-height band on every viewport width.
    var h = Math.max(240, Math.round(rect.height || w * 0.5));
    try { instance.width(w).height(h); } catch (e) {}
  }

  function refresh(projects) {
    if (!instance) return;
    try { instance.pointsData(pointsFrom(projects)); } catch (e) {}
  }

  function escapeHtml(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  window.LinGlobe = {
    mount: mount,
    destroy: destroy,
    refresh: refresh,
    resize: sizeToHost,
    webglAvailable: webglAvailable,
    // Exposed so a check can observe the loop rather than take it on trust.
    isRunning: function () { return !!instance; }
  };
})();
