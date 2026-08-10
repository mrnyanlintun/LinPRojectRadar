/* ============================================================
   Opus Gubernatio — atlas.js
   ------------------------------------------------------------
   The flat world map. SVG, no WebGL, no 3D library, no animation loop.

   WHY THIS EXISTS. The globe is written and may well be good, but two consecutive sessions could
   not verify it: the automated browser does not composite, requestAnimationFrame never fires, and
   globe.gl builds its scene inside that loop, so there was nothing to look at and nothing to
   measure. The risk that could not be ruled out is a director opening the portfolio and seeing a
   black sphere. So the default geographic view is now something that cannot fail that way, and
   the globe becomes a view you choose rather than the thing everything depends on.

   IT RENDERS WITHOUT A FRAME. Every mark is an SVG node in the DOM the moment render() returns.
   There is no draw loop, no requestAnimationFrame, no canvas context, and nothing that waits for
   a compositor. A page that never paints still has the full node tree, which is exactly the
   property that makes this checkable in an automated browser — and the property the globe lacks.

   IT COMPUTES NOTHING. Same rule as the globe and as every other surface since Part 3: status
   comes from the stored computed_results row through taxonomy.js's getProjectFusion(). A
   visualisation is where it would be tempting to derive one, and that is what produced the
   false-Red defect.

   THEME FOLLOWS THE CASCADE. Fills are declared as style="fill:var(--…)" rather than resolved
   colours, so a theme switch repaints this view with no JavaScript at all and no reload. The one
   thing that cannot be a var() is the letter ink, which depends on the resolved fill's luminance;
   retheme() recomputes it.

   PROJECTION: EQUIRECTANGULAR. Chosen over Natural Earth for one reason that matters more than
   how the coastlines read — it is linear, so a project's marker is at exactly
   (lon + 180) / 360 and (90 - lat) / 180 of the frame, and a wrong pin cannot be blamed on the
   projection. It is also the projection the source data is already in.
   ============================================================ */

(function () {
  "use strict";

  var COUNTRIES_URL = "assets/vendor/ne_110m_admin_0_countries.geojson";
  var SVG_NS = "http://www.w3.org/2000/svg";

  // The drawing frame. 2:1 is the equirectangular aspect ratio; the viewBox makes every size
  // below a fraction of the frame rather than a pixel count, so this is resolution-independent
  // and stays crisp at 3840 without redrawing anything.
  var W = 1000, H = 500;

  var countriesPromise = null;

  // Fetched once and shared. Resolves to [] rather than rejecting: a map with no coastlines is a
  // worse map, not a broken one, and the markers — the actual data — are unaffected.
  function loadCountries() {
    if (countriesPromise) return countriesPromise;
    countriesPromise = fetch(COUNTRIES_URL)
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) { return (j && j.features) || []; })
      .catch(function () { return []; });
    return countriesPromise;
  }

  /* ---------- projection ---------- */

  function projX(lon) { return (Number(lon) + 180) / 360 * W; }
  function projY(lat) { return (90 - Number(lat)) / 180 * H; }

  /* ---------- geometry -> path ----------
     Rings are emitted at 2 decimal places: at a 1000-unit frame that is a hundredth of a unit,
     far below anything visible, and it roughly halves the size of the path data in the DOM.

     THE ANTIMERIDIAN GUARD. Equirectangular maps longitude linearly, so a polygon that crosses
     ±180 (Fiji, Chukotka) would otherwise draw a horizontal smear straight across the map as the
     x coordinate jumps from one edge to the other. Any segment longer than half the frame is
     treated as a wrap and starts a new subpath instead. */

  function ringToPath(ring) {
    var d = "", pen = false, prevX = null;
    for (var i = 0; i < ring.length; i++) {
      var pt = ring[i];
      if (!pt || pt.length < 2) continue;
      var x = projX(pt[0]), y = projY(pt[1]);
      if (!isFinite(x) || !isFinite(y)) { pen = false; continue; }
      if (pen && prevX !== null && Math.abs(x - prevX) > W / 2) pen = false;   // wrapped
      d += (pen ? "L" : "M") + x.toFixed(2) + " " + y.toFixed(2);
      pen = true;
      prevX = x;
    }
    return d ? d + "Z" : "";
  }

  function featureToPath(geom) {
    if (!geom) return "";
    var d = "", i, j;
    if (geom.type === "Polygon") {
      for (i = 0; i < geom.coordinates.length; i++) d += ringToPath(geom.coordinates[i]);
    } else if (geom.type === "MultiPolygon") {
      for (i = 0; i < geom.coordinates.length; i++)
        for (j = 0; j < geom.coordinates[i].length; j++) d += ringToPath(geom.coordinates[i][j]);
    }
    return d;
  }

  /* ---------- data ---------- */

  function statusOf(p) {
    try {
      var fusion = window.getProjectFusion ? window.getProjectFusion(p) : null;
      return (fusion && fusion.status) || null;
    } catch (e) { return null; }
  }

  // Which CSS variable a status is drawn from. Returned as a variable name, not a colour, so the
  // fill can stay a var() and follow the theme without this file resolving anything.
  function statusVar(status) {
    var s = String(status || "").toLowerCase();
    if (s.indexOf("complete") >= 0 || s.indexOf("blue") >= 0) return "--status-complete";
    if (s.indexOf("green") >= 0) return "--status-green";
    if (s.indexOf("yellow") >= 0 || s.indexOf("light-amber") >= 0) return "--status-yellow";
    if (s.indexOf("amber") >= 0 || s.indexOf("orange") >= 0) return "--status-amber";
    if (s.indexOf("red") >= 0) return "--status-red";
    return "--status-nodata";
  }

  function resolveVar(name, fallback) {
    try {
      var v = getComputedStyle(document.body).getPropertyValue(name);
      v = (v || "").trim();
      return v || fallback;
    } catch (e) { return fallback; }
  }

  function placeable(p) {
    var lat = Number(p && p.lat), lng = Number(p && p.lng);
    return isFinite(lat) && isFinite(lng) && Math.abs(lat) <= 90 && Math.abs(lng) <= 180;
  }

  function el(name, attrs) {
    var n = document.createElementNS(SVG_NS, name);
    for (var k in attrs) if (Object.prototype.hasOwnProperty.call(attrs, k)) {
      n.setAttribute(k, attrs[k]);
    }
    return n;
  }

  /* ---------- render ---------- */

  /**
   * Draw the map into `host`.
   *
   * opts.onSelect — called with a project id. The portfolio passes openDetail, so selecting a
   *                 marker does exactly what selecting a map marker has always done.
   * opts.focusId  — a single project to emphasise, for project detail.
   *
   * Resolves { ok, placed, unplaced }. The coastlines arrive asynchronously; the markers and the
   * frame do not wait for them, so the view is never empty while the fetch is in flight.
   */
  function render(host, projects, opts) {
    opts = opts || {};
    if (!host) return Promise.resolve({ ok: false, reason: "no host" });

    var list = (projects || []).slice();
    var placed = list.filter(placeable);
    var unplaced = list.length - placed.length;

    host.innerHTML = "";

    var svg = el("svg", {
      viewBox: "0 0 " + W + " " + H,
      preserveAspectRatio: "xMidYMid meet",
      class: "atlas-svg",
      role: "img",
      "aria-label": "World map. One marker per project with a stored location; marker colour and "
        + "letter indicate the stored project status. Selecting a marker opens that project's "
        + "detail view. Projects without a location are not shown here and remain in the project "
        + "list below, which is an equivalent keyboard control path."
    });

    // Ocean. A rect rather than a background colour so it belongs to the drawing and scales with
    // the viewBox at any width.
    svg.appendChild(el("rect", {
      x: 0, y: 0, width: W, height: H, class: "atlas-ocean", style: "fill:var(--atlas-ocean)"
    }));

    var gGrat = el("g", { class: "atlas-graticule", "aria-hidden": "true" });
    for (var lon = -180; lon <= 180; lon += 30) {
      gGrat.appendChild(el("line", {
        x1: projX(lon).toFixed(2), y1: 0, x2: projX(lon).toFixed(2), y2: H,
        style: "stroke:var(--atlas-graticule)"
      }));
    }
    for (var lat = -60; lat <= 60; lat += 30) {
      gGrat.appendChild(el("line", {
        x1: 0, y1: projY(lat).toFixed(2), x2: W, y2: projY(lat).toFixed(2),
        style: "stroke:var(--atlas-graticule)"
      }));
    }
    svg.appendChild(gGrat);

    var gLand = el("g", { class: "atlas-land", "aria-hidden": "true" });
    svg.appendChild(gLand);

    var gMarks = el("g", { class: "atlas-markers" });
    svg.appendChild(gMarks);

    host.appendChild(svg);

    /* MARKER LEGIBILITY — the same treatment the globe uses, and for the same measured reason.
       A status colour on a map has no guaranteed contrast against what is behind it: land, ocean
       and the theme all differ, and the four status colours span a wide luminance range, so
       whatever the background is, one of them will be close to it. Dimming the background was
       measured on the globe's texture and does NOT fix it — it only changes which status fails.

       What works is local contrast. Every marker sits on a dark disc, so the status is read
       against near-black rather than against terrain. Against --atlas-marker-halo (#05080b) the
       measured ratios are Red 4.9, Amber 7.5, Green 10.5, Yellow 13.4 — all clearing the 3:1
       floor for a graphical object, and identical over land, ocean and every theme because they
       no longer depend on any of them.

       The letter is the platform's existing colour-blind-safe cue (config.js linStatusLetter),
       inked by luminance so it reads on any of the five fills. Status colours are untouched. */
    placed.forEach(function (p) {
      var id = p.id || p.project_id;
      var status = statusOf(p);
      var vName = statusVar(status);
      var fill = resolveVar(vName, "#6f7d70");
      var cx = projX(p.lng), cy = projY(p.lat);
      var focused = opts.focusId && id === opts.focusId;
      var r = focused ? 9 : 7;

      var g = el("g", {
        class: "atlas-marker" + (focused ? " atlas-marker-focus" : ""),
        "data-project-id": id == null ? "" : String(id),
        tabindex: opts.onSelect ? "0" : null,
        role: opts.onSelect ? "button" : null
      });
      if (!opts.onSelect) { g.removeAttribute("tabindex"); g.removeAttribute("role"); }

      var title = document.createElementNS(SVG_NS, "title");
      title.textContent = (p.name || "Untitled project") + " · " + (status || "Awaiting analysis")
        + (p.formattedAddress ? " · " + p.formattedAddress : "");
      g.appendChild(title);

      g.appendChild(el("circle", {
        cx: cx.toFixed(2), cy: cy.toFixed(2), r: r,
        class: "atlas-halo", style: "fill:var(--atlas-marker-halo)"
      }));
      g.appendChild(el("circle", {
        cx: cx.toFixed(2), cy: cy.toFixed(2), r: r - 2.4,
        class: "atlas-dot", style: "fill:var(" + vName + ")"
      }));

      var letter = window.linStatusLetter ? window.linStatusLetter(status) : "";
      if (letter) {
        var ink = window.linStatusInk ? window.linStatusInk(fill) : "#0b1220";
        var t = el("text", {
          x: cx.toFixed(2), y: cy.toFixed(2),
          class: "atlas-letter", "text-anchor": "middle", "dominant-baseline": "central",
          "font-size": (r - 2.2).toFixed(1), fill: ink, "aria-hidden": "true"
        });
        t.textContent = letter;
        g.appendChild(t);
      }

      if (opts.onSelect) {
        g.addEventListener("click", function () { opts.onSelect(id); });
        g.addEventListener("keydown", function (e) {
          if (e.key === "Enter" || e.key === " ") { e.preventDefault(); opts.onSelect(id); }
        });
      }
      gMarks.appendChild(g);
    });

    return loadCountries().then(function (feats) {
      // The host may have been re-rendered or the view left while the fetch was in flight.
      if (!svg.isConnected) return { ok: true, placed: placed.length, unplaced: unplaced };
      var frag = document.createDocumentFragment();
      feats.forEach(function (f) {
        var d = featureToPath(f && f.geometry);
        if (!d) return;
        frag.appendChild(el("path", {
          d: d, class: "atlas-country",
          style: "fill:var(--atlas-land);stroke:var(--atlas-land-stroke)"
        }));
      });
      gLand.appendChild(frag);
      return { ok: true, placed: placed.length, unplaced: unplaced, countries: feats.length };
    });
  }

  /* ---------- camera (viewBox pan/zoom) ----------
     The atlas has no camera in the MapLibre/globe.gl sense — it is one static SVG node tree, the
     whole world, drawn once. "Moving" it means animating the viewBox: shrinking it around a
     project's projected (x, y) reads as flying in, and returning it to "0 0 W H" reads as flying
     back out to the portfolio-wide view. No new dependency: requestAnimationFrame and the SVG
     viewBox attribute are both already in use elsewhere in this file. */

  function currentViewBox(svg) {
    var parts = (svg.getAttribute("viewBox") || ("0 0 " + W + " " + H)).trim().split(/\s+/).map(Number);
    return { x: parts[0] || 0, y: parts[1] || 0, w: parts[2] || W, h: parts[3] || H };
  }

  function setViewBoxAttr(svg, vb) {
    svg.setAttribute("viewBox",
      vb.x.toFixed(2) + " " + vb.y.toFixed(2) + " " + vb.w.toFixed(2) + " " + vb.h.toFixed(2));
  }

  function reduceMotion() {
    try { return !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches); }
    catch (e) { return false; }
  }

  // Each svg gets at most one in-flight tween; a second call (selecting a new project mid-flight)
  // must replace it rather than fight it, or the viewBox jitters between two competing rAF loops.
  var tweenToken = 0;

  function tweenViewBox(svg, target, ms) {
    if (!svg) return;
    var myToken = ++tweenToken;
    var start = currentViewBox(svg);
    if (!ms || ms <= 0) { setViewBoxAttr(svg, target); return; }
    var t0 = null;
    function step(ts) {
      if (myToken !== tweenToken) return;   // superseded by a newer focus()/resetView() call
      if (t0 === null) t0 = ts;
      var p = Math.min(1, (ts - t0) / ms);
      var e = p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;   // ease-in-out
      setViewBoxAttr(svg, {
        x: start.x + (target.x - start.x) * e,
        y: start.y + (target.y - start.y) * e,
        w: start.w + (target.w - start.w) * e,
        h: start.h + (target.h - start.h) * e
      });
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  /* Zoom to a project so it reads as a place, not a continent. A tenth of the world frame in
     each dimension — one tenth of 360° of longitude is 36°, close to the width of the
     continental United States, which is the smallest span that still reliably contains a city's
     immediate surroundings without the marker sitting on a seam. A project with no usable
     coordinates leaves the viewBox exactly where it was — same contract as the map's
     flyToProject, which also does nothing when there is no marker to fly to. */
  function focus(host, p) {
    if (!host) return;
    var svg = host.querySelector(".atlas-svg");
    if (!svg || !placeable(p)) return;
    var cx = projX(p.lng), cy = projY(p.lat);
    var zw = W / 10, zh = H / 10;
    tweenViewBox(svg, { x: cx - zw / 2, y: cy - zh / 2, w: zw, h: zh }, reduceMotion() ? 0 : 700);
  }

  /* Deselecting, or selecting a project the camera never moved for, returns to the
     portfolio-wide view rather than leaving the viewBox stranded on the last focus. */
  function resetView(host) {
    if (!host) return;
    var svg = host.querySelector(".atlas-svg");
    if (!svg) return;
    tweenViewBox(svg, { x: 0, y: 0, w: W, h: H }, reduceMotion() ? 0 : 700);
  }

  /* ---------- theme ----------
     Almost nothing to do: every fill is a var(), so the cascade has already repainted by the time
     this runs. The exception is the letter ink, which is computed from the resolved status colour
     rather than referenced, and so has to be recomputed. */

  function retheme(root) {
    var scope = root || document;
    var marks = scope.querySelectorAll(".atlas-marker");
    Array.prototype.forEach.call(marks, function (g) {
      var dot = g.querySelector(".atlas-dot");
      var txt = g.querySelector(".atlas-letter");
      if (!dot || !txt) return;
      var m = /var\((--[a-z-]+)\)/.exec(dot.getAttribute("style") || "");
      if (!m) return;
      var fill = resolveVar(m[1], "#6f7d70");
      if (window.linStatusInk) txt.setAttribute("fill", window.linStatusInk(fill));
    });
  }

  // Nothing to release: no context, no loop, no listeners outside the removed nodes.
  function teardown(host) {
    if (host) host.innerHTML = "";
  }

  window.LinAtlas = {
    render: render,
    retheme: retheme,
    teardown: teardown,
    focus: focus,
    resetView: resetView,
    // Exposed so a check can read the live camera state back, the same reason liveCount() and
    // stats() are exposed: the claim should be verifiable off the thing itself.
    viewBox: function (host) {
      var svg = host && host.querySelector(".atlas-svg");
      return svg ? currentViewBox(svg) : null;
    },
    // Exposed for the same reason LinGlobe.liveCount is: the claim is that this renders without a
    // frame, and that should be readable off the thing itself rather than taken on trust.
    stats: function (root) {
      var scope = root || document;
      var svg = scope.querySelector(".atlas-svg");
      if (!svg) return null;
      return {
        countries: svg.querySelectorAll(".atlas-country").length,
        markers: svg.querySelectorAll(".atlas-marker").length,
        halos: svg.querySelectorAll(".atlas-halo").length,
        letters: svg.querySelectorAll(".atlas-letter").length,
        nodes: svg.querySelectorAll("*").length
      };
    }
  };
})();
