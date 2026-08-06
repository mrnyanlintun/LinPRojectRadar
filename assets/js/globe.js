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
  var EARTH_TEXTURE_URL = "assets/vendor/earth-blue-marble-clouds.jpg";
  var COUNTRIES_URL = "assets/vendor/ne_110m_admin_0_countries.geojson";

  // Country outlines for the abstract treatment. Fetched once, shared by every instance, and
  // only when a theme that needs them is actually shown — the photographic themes never pay for
  // it. Resolves to [] on failure: a globe with no continents is a worse globe, not a broken one.
  var countriesPromise = null;

  function loadCountries() {
    if (countriesPromise) return countriesPromise;
    countriesPromise = fetch(COUNTRIES_URL)
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) { return (j && j.features) || []; })
      .catch(function () { return []; });
    return countriesPromise;
  }

  // Earth's axial tilt, in radians. 23.4 degrees.
  var AXIAL_TILT = 23.4 * Math.PI / 180;

  var loadPromise = null;
  var live = [];            // every mounted instance, so visibility can reach all of them
  var visibilityBound = false;

  /* ---------- capability ---------- */

  // Asked with a throwaway canvas rather than by trying to build a globe and catching the
  // failure: constructing one only to tear it down is slower and leaves a context behind on
  // some drivers.
  // A turning globe is motion, and someone who has asked the operating system for less of it
  // should not get a planet spinning under their cursor. Checked at mount rather than cached, so
  // a change to the setting is picked up on the next view.
  function reduceMotion() {
    try {
      return !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
    } catch (e) { return false; }
  }

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

  function themeNumber(name, fallback) {
    var v = parseFloat(themeColor(name, ""));
    return isFinite(v) ? v : fallback;
  }

  /* ---------- painting a globe from the theme ----------
     T9 Task 4. Every non-status colour the globe shows is resolved here, from the live computed
     style, so this is also what a theme switch re-runs. Nothing below touches point colours:
     those are statuses, and a status that changed shade with the theme would be a different
     claim about the project.

     The graticules have no globe.gl setter — showGraticules(true) builds a LineSegments with a
     hardcoded light grey at opacity 0.1, which disappears against a blue planet. Its material is
     reached through the scene, the same way the tilt is, and for the same reason. */

  // "photographic" or "abstract". The theme decides, not this file.
  function treatment() {
    return themeColor("--globe-treatment", "abstract") === "photographic"
      ? "photographic" : "abstract";
  }

  /* ---------- the two treatments ----------
     NYC gets the abstract data-network planet; Miami and Maria get the photographic Earth.
     Switching between them is a repaint, never a remount — dropping and reacquiring a WebGL
     context to change an appearance is the one thing this file is careful not to do.

     CONTINENTS AS DOTS, NOT AS A NIGHT-LIGHTS TEXTURE. globe.gl's hexPolygonsData with
     hexPolygonUseDots draws the country outlines as a dot field, and its colour comes from a
     theme variable. A night-lights image would have been another megabyte of texture whose
     colour is baked in and could not follow the theme at all, which is the whole point of this
     work. The resolution is deliberately coarse (3): it is the dominant cost of this treatment
     and the frame rate could not be measured in the session that built it, so it is set
     conservatively rather than optimistically.

     The "connecting lines across the surface" are the graticules the globe already draws. Arcs
     between project points were considered and rejected: an arc between two projects asserts a
     relationship between them that does not exist. */

  function applyTreatment(globe) {
    var mode = treatment();
    if (mode === "photographic") {
      try { globe.hexPolygonsData([]); } catch (e) {}
      try { globe.globeImageUrl(EARTH_TEXTURE_URL); } catch (e) {}
      return;
    }
    // abstract
    try { globe.globeImageUrl(null); } catch (e) {}
    var land = themeColor("--globe-land", "#63b6a2");
    var landOp = themeNumber("--globe-land-opacity", 0.85);
    try {
      globe.hexPolygonColor(function () { return land; })
           .hexPolygonResolution(3)
           .hexPolygonMargin(0.35)
           .hexPolygonUseDots(true)
           .hexPolygonAltitude(0.006);
      if (typeof globe.hexPolygonsData === "function") {
        loadCountries().then(function (feats) {
          try { globe.hexPolygonsData(feats); } catch (e) {}
        });
      }
    } catch (e) {}
    // landOp is carried in the colour when the theme wants it translucent; globe.gl has no
    // separate opacity for this layer, so it is folded in rather than silently ignored.
    if (landOp < 1) {
      try {
        globe.hexPolygonColor(function () { return rgbaFrom(land, landOp); });
      } catch (e) {}
    }
  }

  // globe.gl accepts CSS colour strings for hexPolygonColor (it is not Color.set), so an rgba()
  // here is safe and is the only way to get a translucent dot field.
  function rgbaFrom(col, alpha) {
    var m = /^#?([0-9a-f]{6})$/i.exec(col.trim());
    if (!m) return col;
    var n = parseInt(m[1], 16);
    return "rgba(" + ((n >> 16) & 255) + "," + ((n >> 8) & 255) + "," + (n & 255) + "," + alpha + ")";
  }

  function paintTheme(globe) {
    var sphere = themeColor("--globe-sphere", "#151c20");
    var atmos = themeColor("--globe-atmosphere", "#63b6a2");
    var grat = themeColor("--globe-graticule", "#4b7f74");
    var gratOp = themeNumber("--globe-graticule-opacity", 0.16);

    applyTreatment(globe);

    try { globe.atmosphereColor(atmos); } catch (e) {}

    try {
      var mat = globe.globeMaterial();
      if (mat && mat.color && typeof mat.color.set === "function") {
        mat.color.set(sphere);
        if ("shininess" in mat) mat.shininess = 4;
        mat.needsUpdate = true;
      }
    } catch (e) { /* the globe still renders without the tint */ }

    try {
      var scene = typeof globe.scene === "function" && globe.scene();
      var grp = scene && scene.children && scene.children.filter(function (c) {
        return c && c.type === "Group";
      })[0];
      var inner = grp && grp.children && grp.children[0];
      (inner && inner.children ? inner.children : []).forEach(function (c) {
        if (c && c.type === "LineSegments" && c.material && c.material.color) {
          c.material.color.set(grat);
          c.material.opacity = gratOp;
          c.material.transparent = true;
          c.material.needsUpdate = true;
        }
      });
    } catch (e) {}
  }

  /* ---------- marker legibility on the photographic themes ----------
     A status marker on real terrain has no guaranteed contrast: the four status colours span a
     wide luminance range, and whatever the terrain is, one of them will be close to it.

     MEASURED, NOT ASSUMED. Sampling the actual texture at six places and computing WCAG contrast
     for each status gave a worst case of 1.02:1 — Yellow over the Sahara. Dimming the texture,
     which is the obvious fix and was tried first, does NOT solve it: at 62% brightness and 72%
     saturation the worst case was still 1.01:1, because dimming only moves which status fails
     (Red, once the sand is dark). A global brightness change cannot serve four colours at
     different luminances at once. That is why the texture ships undimmed.

     WHAT WORKS IS LOCAL CONTRAST. Every marker gets a dark disc drawn underneath it, slightly
     larger and slightly lower, so the status colour is always read against near-black rather
     than against whatever is there. Contrast becomes a property of the marker's own surround and
     is therefore the same over ocean, desert, ice and cloud. Against #05080b every status clears
     3:1 with room: Red 4.9, Amber 7.5, Green 10.5, Yellow 13.4.

     The status colour itself is untouched, which is the constraint that ruled out the
     alternatives — desaturating the markers, or tinting them per theme.

     It is a labels layer with empty text rather than a second points layer, because globe.gl
     allows only one pointsData. Both are real 3D layers, so the disc is depth-tested and
     occluded by the globe exactly as the marker is; an HTML-overlay marker would have floated in
     front of the far side of the planet. */

  function haloData(pts) {
    return pts.map(function (p) { return { lat: p.lat, lng: p.lng }; });
  }

  function applyHalos(globe, pts) {
    var on = treatment() === "photographic";
    try {
      globe.labelsData(on ? haloData(pts) : [])
           .labelLat("lat").labelLng("lng")
           .labelText(function () { return ""; })
           .labelSize(0)
           .labelDotRadius(0.62)
           .labelIncludeDot(true)
           .labelAltitude(0.055)
           .labelColor(function () { return themeColor("--globe-marker-halo", "#05080b"); });
    } catch (e) {}
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
      if (grp && grp.rotation) {
        grp.rotation.z = AXIAL_TILT;
        // The graticules land in the same build step as the group, so this is where they can
        // first be recoloured. paintTheme is safe to run twice; mount has already set the
        // sphere and atmosphere, which exist earlier.
        paintTheme(globe);
        return;
      }
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

  function makeHandle(globe, host, defaultPOV) {
    var handle = {
      globe: globe,
      host: host,
      destroyed: false,

      // Selecting a project from the portfolio list flies the live camera to it, the same
      // move flyToProject makes on the map. altitude 1.4 matches opts.focus (the single-project
      // detail globe) so both routes to "look at this project" land at the same readable zoom.
      focus: function (lat, lng) {
        if (handle.destroyed || !isFinite(lat) || !isFinite(lng)) return;
        try {
          var controls = globe.controls();
          if (controls) controls.autoRotate = false;   // stop spinning under the selection
          globe.pointOfView({ lat: lat, lng: lng, altitude: 1.4 }, reduceMotion() ? 0 : 1000);
        } catch (e) {}
      },

      // Deselecting (or selecting a project the camera never moved for) returns to the
      // portfolio-wide view captured at mount, rather than leaving the camera stranded on
      // whatever was last selected.
      resetView: function () {
        if (handle.destroyed) return;
        try {
          var pov = defaultPOV || { lat: 0, lng: 0, altitude: 2.5 };
          globe.pointOfView(pov, reduceMotion() ? 0 : 1000);
          var controls = globe.controls();
          if (controls) controls.autoRotate = !reduceMotion();
        } catch (e) {}
      },

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
        try {
          var pts = pointsFrom(projects);
          globe.pointsData(pts);
          applyHalos(globe, pts);
        } catch (e) {}
      },

      isRunning: function () { return !handle.destroyed; },

      // T11. Whether globe.gl has actually BUILT its scene, which is not the same as mount()
      // having resolved. The scene is assembled inside the animation loop, so on a machine where
      // that loop never runs — a browser that is not compositing, and possibly a locked-down
      // driver — mount() resolves ok and the panel stays black. The caller's watchdog asks this
      // rather than trusting the resolve, because a black panel in front of a director is the
      // failure the flat atlas exists to prevent.
      hasScene: function () {
        try {
          var sc = globe.scene();
          return !!(sc && sc.children && sc.children.filter(function (c) {
            return c && c.type === "Group";
          })[0]);
        } catch (e) { return false; }
      }
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
        // Sphere and atmosphere are available now; the graticules are not, so applyTilt paints
        // them again once globe.gl has built the group.
        paintTheme(globe);
        applyHalos(globe, pts);

        applyTilt(globe);

        // Captured before any opts.focus is applied, so resetView() always returns to the
        // portfolio-wide framing this globe started at rather than to whatever the caller's
        // initial focus happened to be.
        var defaultPOV = null;
        try { defaultPOV = globe.pointOfView(); } catch (e) {}

        var handle = makeHandle(globe, container, defaultPOV);
        live.push(handle);
        handle.resize();

        if (opts.focus && isFinite(opts.focus.lat) && isFinite(opts.focus.lng)) {
          try {
            globe.pointOfView({ lat: opts.focus.lat, lng: opts.focus.lng, altitude: 1.4 }, 0);
          } catch (e) {}
        }
        /* T11a. THE GLOBE TURNS IN BOTH STATES — empty, as the platform's resting visual, and
           with projects placed. It used to turn only when it was empty or when it was the
           non-interactive detail globe, so the one case a director actually sees — the portfolio
           with projects on it — was the one case that never moved. That was a construction
           mistake, not a tuning one.

           SPEED, WITH THE ARITHMETIC, because the old value was not what it looked like.
           three.js turns at 6 degrees per second per unit of autoRotateSpeed, so the previous
           0.35 was 2.1 deg/s — about 171 seconds for one revolution, which reads as a still
           image. It had never actually been watched: earlier sessions confirmed "rotating at
           0.35" by reading the property, never by eye. 1.0 is 6 deg/s, one revolution a minute:
           unmistakably alive, and still slow enough that it does not compete with the points.

           OrbitControls suspends auto-rotation while the user is dragging and resumes after, so
           this does not fight anyone trying to inspect a point. */
        try {
          var controls = globe.controls();
          if (controls) {
            if (opts.interactive === false) controls.enableZoom = false;
            controls.autoRotate = !reduceMotion();
            controls.autoRotateSpeed = 1.0;
            // OrbitControls' default inertia (enableDamping) measurably fights focus()/resetView():
            // pointOfView() moves the camera directly during its own tween, damping reads that as
            // user input and keeps drifting the camera for several seconds after the tween finishes,
            // landing several degrees off the selected project. Verified in a real WebGL browser —
            // selecting a project reached the target then visibly kept sliding west. Programmatic
            // moves do not need inertia; disabling it removes the drift and costs nothing a director
            // would notice on manual drag, which now just stops the instant the pointer is released.
            controls.enableDamping = false;
          }
        } catch (e) {}
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

  /* ---------- theme switching ----------
     T9 Task 4. applyTheme() calls this after swapping body[data-theme], so every live globe
     repaints in place. No reload, and no remount: rebuilding a globe to change its colour would
     drop and reacquire a WebGL context, which is the one thing this file is careful not to do.

     Point colours are re-resolved rather than left alone. They are status colours and are the
     same in all three themes today, so in practice nothing about them changes — but re-reading
     them means a theme that ever did override a --status-* would be honoured, and a stale
     colour would not survive here unnoticed. */

  function retheme() {
    live.forEach(function (h) {
      if (!h || h.destroyed) return;
      try { paintTheme(h.globe); } catch (e) {}
      try {
        var pts = h.globe.pointsData() || [];
        pts.forEach(function (p) { p.color = statusColor(p.status); });
        h.globe.pointsData(pts);
        // The halo belongs to the photographic treatment, so a switch in either direction has to
        // add it or take it away, not just recolour it.
        applyHalos(h.globe, pts);
      } catch (e) {}
    });
  }

  window.LinGlobe = {
    mount: mount,
    retheme: retheme,
    webglAvailable: webglAvailable,
    // Exposed so a check can observe the loops rather than take them on trust.
    liveCount: function () { return live.length; },

    // Same reason as liveCount: the theme claim is "a live globe repaints without a reload",
    // and that is worth being able to read off a running globe rather than infer from a fresh
    // one. Returns what each live globe is actually painted with right now.
    palette: function () {
      return live.map(function (h) {
        var out = { sphere: null, graticule: null, gratOpacity: null, tiltDeg: null, points: [] };
        try { out.treatment = treatment(); } catch (e) {}
        try { out.textureUrl = h.globe.globeImageUrl() || null; } catch (e) {}
        try { out.hexPolygons = (h.globe.hexPolygonsData() || []).length; } catch (e) {}
        try { out.halos = (h.globe.labelsData() || []).length; } catch (e) {}
        try { out.sphere = "#" + h.globe.globeMaterial().color.getHexString(); } catch (e) {}
        try { out.atmosphere = h.globe.atmosphereColor(); } catch (e) {}
        try {
          var grp = h.globe.scene().children.filter(function (c) { return c.type === "Group"; })[0];
          out.tiltDeg = +(grp.rotation.z * 180 / Math.PI).toFixed(2);
          var line = grp.children[0].children.filter(function (c) {
            return c.type === "LineSegments";
          })[0];
          if (line) {
            out.graticule = "#" + line.material.color.getHexString();
            out.gratOpacity = +line.material.opacity.toFixed(3);
          }
        } catch (e) {}
        try {
          out.points = (h.globe.pointsData() || []).map(function (p) {
            return { status: p.status, color: p.color };
          });
        } catch (e) {}
        return out;
      });
    }
  };
})();
