/* ============================================================
   Opus Gubernatio — globe.js
   ------------------------------------------------------------
   The portfolio globe, and the focused globe on project detail.

   ONE INSTANCE PER MOUNT POINT. This was a singleton, which meant a second mount destroyed
   the first and the two views could not coexist. They now each own a renderer, a context and
   a destructor. Two WebGL contexts is not a problem — browsers allow well beyond two — and the
   alternative was tearing the portfolio globe down and rebuilding it every time a project was
   opened and closed, which is slower and has more ways to go wrong than simply letting each
   view keep its own.

   The portfolio view is hidden while detail is open, so its loop is already stopped by the same
   visibility and teardown mechanism the portfolio globe uses; an idle second context costs
   nothing while it is not animating.

   IT COMPUTES NOTHING. Every colour comes from the status the server stored in
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
       either missing                 -> whatever the caller falls back to (the map, or a
                                         plain no-position message on project detail)
       nothing available              -> the project list, which is always in the DOM

   PROJECTS WITHOUT COORDINATES ARE NOT LOST. They cannot be placed, so they are not points, but
   they remain in the project list below the stage, which is the same keyboard path the radar
   has always had. Being unplaceable is not being deleted.
   ============================================================ */

(function () {
  "use strict";

  var VENDOR_URL = "assets/vendor/globe.gl.min.js";

  // Earth's axial tilt, in radians. 23.4 degrees.
  var AXIAL_TILT = 23.4 * Math.PI / 180;

  var loadPromise = null;
  var live = [];            // every mounted instance, so visibility can reach all of them
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
      // the caller's job is to show something else, not to handle an error.
      s.onerror = function () { resolve(false); };
      document.head.appendChild(s);
    });
    return loadPromise;
  }

  /* ---------- theme ---------- */

  // Read from the live computed style so a theme switch is picked up, rather than hard-coding
  // anything. No screen defines its own palette.
  // three.js Color.set() parses hex and rgb(), but NOT rgba(). Several theme surfaces are
  // declared with alpha (newyork's --surface-soft is rgba(21,28,32,.86)), so passing the raw
  // value through made Color.set throw and the globe silently kept its default material. The
  // alpha is dropped rather than approximated: the globe is opaque, and compositing a
  // translucent surface colour against an unknown backdrop is not something this can know.
  function stripAlpha(v) {
    var m = /^rgba\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)/i.exec(v);
    if (!m) return v;
    return "rgb(" + Math.round(+m[1]) + "," + Math.round(+m[2]) + "," + Math.round(+m[3]) + ")";
  }

  function themeColor(name, fallback) {
    try {
      var v = getComputedStyle(document.body).getPropertyValue(name);
      v = stripAlpha((v || "").trim());
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

  function escapeHtml(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  /* ---------- shared visibility ----------
     One listener for every instance. A globe spinning in a tab nobody is looking at is pure
     cost on a single small instance, and that is as true of two globes as of one. */

  function onVisibility() {
    live.forEach(function (g) {
      try {
        if (document.hidden) g.globe.pauseAnimation();
        else g.globe.resumeAnimation();
      } catch (e) { /* older builds may lack these; not worth failing a view over */ }
    });
  }

  function bindVisibility() {
    if (visibilityBound) return;
    document.addEventListener("visibilitychange", onVisibility);
    visibilityBound = true;
  }

  /* ---------- axial tilt ----------
     T9 Task 3. Earth's tilt, so the globe reads as a planet rather than a sphere.

     Applied to globe.gl's own group — the one holding the sphere, the graticules and the
     points — rather than to the camera. Tilting the camera would look the same on the first
     frame, but pointOfView() and the focus option both reason in camera space, so the focused
     detail globe would then be fighting it. Tilting the group instead means the points stay
     attached to their coordinates on a tilted planet, which is what a tilt actually means.

     The group does not exist yet when mount() returns: globe.gl builds it over the following
     frames, and setting rotation on the scene at construction time silently did nothing. So
     this retries across a bounded number of frames and stops as soon as it lands. */

  function applyTilt(globe, tries) {
    tries = tries || 0;
    try {
      var scene = typeof globe.scene === "function" && globe.scene();
      var grp = scene && scene.children && scene.children.filter(function (c) {
        return c && c.type === "Group";
      })[0];
      if (grp && grp.rotation) { grp.rotation.z = AXIAL_TILT; return; }
    } catch (e) {
      // Deliberately falls through to the retry rather than giving up. Reading .scene() before
      // globe.gl has built it can throw, and returning here was why the first version of this
      // silently left every globe upright: the one early throw killed the retry for good.
    }
    // A timer, not requestAnimationFrame. rAF does not fire while the page is not compositing
    // — a background tab, or an automated browser whose pane is not displayed — and globe.gl
    // builds its group from its own timers regardless. On rAF the globe finished building and
    // then stayed upright forever, because the retry that was meant to catch it never ran.
    // Bounded at ~1s so a build that never produces a group cannot retry forever.
    if (tries < 60) setTimeout(function () { applyTilt(globe, tries + 1); }, 16);
  }

  /* ---------- an instance ---------- */

  function makeHandle(globe, host) {
    var handle = {
      globe: globe,
      host: host,
      destroyed: false,

      destroy: function () {
        if (handle.destroyed) return;
        handle.destroyed = true;
        try { globe.pauseAnimation(); } catch (e) {}
        try {
          // globe.gl's own teardown. It disposes the renderer, which is what actually releases
          // the WebGL context; dropping the reference alone would leave the context alive until
          // the driver reclaimed it, and browsers cap how many a page may hold.
          if (typeof globe._destructor === "function") globe._destructor();
        } catch (e) {}
        try { if (host) host.innerHTML = ""; } catch (e) {}
        var i = live.indexOf(handle);
        if (i >= 0) live.splice(i, 1);
      },

      resize: function () {
        if (handle.destroyed || !host) return;
        var rect = host.getBoundingClientRect();
        var w = Math.max(240, Math.round(rect.width));
        var h = Math.max(240, Math.round(rect.height || w * 0.5));
        try { globe.width(w).height(h); } catch (e) {}
      },

      refresh: function (projects) {
        if (handle.destroyed) return;
        try { globe.pointsData(pointsFrom(projects)); } catch (e) {}
      },

      isRunning: function () { return !handle.destroyed; }
    };
    return handle;
  }

  /**
   * Build a globe into `container`.
   *
   * Resolves { ok: true, handle } when the globe is showing, or { ok: false, reason } when the
   * caller should fall back. It never throws and never leaves the container empty on failure:
   * an empty panel is the one outcome that is not allowed.
   *
   * opts.focus    — { lat, lng } to centre on, for the project detail view.
   * opts.onSelect — called with a project id. The portfolio passes openDetail, so selecting a
   *                 point does exactly what selecting a map marker has always done.
   * opts.interactive — false to disable rotate/zoom, for a focused single-project view.
   */
  function mount(container, projects, opts) {
    opts = opts || {};
    if (!container) return Promise.resolve({ ok: false, reason: "no container" });
    if (!webglAvailable()) return Promise.resolve({ ok: false, reason: "webgl-unavailable" });

    return loadLibrary().then(function (available) {
      if (!available) return { ok: false, reason: "library-unavailable" };

      container.innerHTML = "";
      var pts = pointsFrom(projects);

      try {
        var globe = window.Globe()(container)
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
          .pointRadius(opts.focus ? 1.0 : 0.6)
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
          var mat = globe.globeMaterial();
          if (mat && mat.color && typeof mat.color.set === "function") {
            mat.color.set(themeColor("--surface-soft", "#12242a"));
            if ("shininess" in mat) mat.shininess = 4;
          }
        } catch (e) { /* the globe still renders without the tint */ }

        applyTilt(globe);

        var handle = makeHandle(globe, container);
        live.push(handle);
        handle.resize();

        if (opts.focus && isFinite(opts.focus.lat) && isFinite(opts.focus.lng)) {
          try {
            globe.pointOfView({ lat: opts.focus.lat, lng: opts.focus.lng, altitude: 1.4 }, 0);
          } catch (e) {}
        }
        // T9 Task 3. The empty state is the platform's resting visual, not an error. A portfolio
        // with nothing placeable still gets a globe, turning slowly, rather than a blank stage or
        // a message. It stays interactive — the user can still spin it — the rotation only gives
        // it life while nothing is on it, and any later refresh() with points leaves it as it is.
        var idle = pts.length === 0;
        if (opts.interactive === false || idle) {
          try {
            var controls = globe.controls();
            if (controls) {
              if (opts.interactive === false) controls.enableZoom = false;
              controls.autoRotate = true;
              controls.autoRotateSpeed = 0.35;
            }
          } catch (e) {}
        }
        bindVisibility();
        return {
          ok: true,
          handle: handle,
          points: pts.length,
          unplaceable: (projects || []).length - pts.length
        };
      } catch (e) {
        return { ok: false, reason: "construction-failed" };
      }
    });
  }

  window.LinGlobe = {
    mount: mount,
    webglAvailable: webglAvailable,
    // Exposed so a check can observe the loops rather than take them on trust.
    liveCount: function () { return live.length; }
  };
})();
