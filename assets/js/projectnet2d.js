/* ============================================================
   lin-project-radar — projectnet2d.js
   ------------------------------------------------------------
   A flat 2D node-link diagram of the 12 signal categories for a
   SINGLE project, rendered on the Project Detail page. Each node
   is one category, coloured by that category's computed status
   FOR THIS PROJECT (reusing window.getCategoryStatus — the exact
   same source that colours the per-category module cards). Edges
   show signal flow: generators → synthesis → evidence → ML →
   governance, with Cat 10–12 as supporting inputs.

   Pure 2D: scroll to zoom, drag to pan. No 3D projection, no
   rotation. Replaces the 3D force network (forcenet.js), which is
   no longer mounted anywhere.

   Exposes window.LinProjectNet2D.render(container, project).
   ============================================================ */
(function () {
  "use strict";

  // Status → fill colour (matches the radar/forcenet legend and the spec).
  var STATUS_FILL = {
    Complete: "#4ea0ff",
    Green:    "#3fcaa6",
    Yellow:   "#f0c040",
    Amber:    "#e2b13c",
    Red:      "#e0556b"
  };
  var NO_DATA_FILL = "#26344f";

  // Compact display names so labels never overflow / overlap.
  var SHORT_NAME = {
    cat1:  "Quant EVM",     cat2:  "Schedule Sim", cat3:  "Cost Sim",
    cat4:  "Doc & Risk",    cat5:  "Sys Dynamics", cat6:  "Synthesis",
    cat7:  "Evidence",      cat8:  "ML & AI",      cat9:  "Governance",
    cat10: "Data Integrity", cat11: "Decision Opt"
  };

  // Fixed 2D layout (world coordinates). Left-to-right signal flow:
  // generators (Cat 1–5) → synthesis (Cat 6) → evidence (Cat 7) / ML (Cat 8)
  // → governance (Cat 9); Cat 10 (data integrity) and Cat 11 (decision opt)
  // sit as supporting inputs near their targets.
  // Spacing is chosen so node labels never collide.
  var LAYOUT = {
    cat1:  { x: 110, y: 70  }, cat2: { x: 110, y: 160 }, cat3: { x: 110, y: 250 },
    cat4:  { x: 110, y: 340 }, cat5: { x: 110, y: 430 },
    cat6:  { x: 340, y: 150 }, cat10:{ x: 340, y: 330 },
    cat7:  { x: 560, y: 150 }, cat8: { x: 560, y: 330 },
    cat9:  { x: 790, y: 150 }, cat11:{ x: 790, y: 330 }
  };
  var WORLD_W = 920, WORLD_H = 560, NODE_R = 27;

  // Directed signal-flow edges (same logical flow as the old force network).
  var EDGES = [
    ["cat1", "cat6"], ["cat2", "cat6"], ["cat3", "cat6"], ["cat4", "cat6"], ["cat5", "cat6"],
    ["cat6", "cat7"], ["cat6", "cat9"],
    ["cat7", "cat9"],
    ["cat8", "cat7"], ["cat8", "cat9"],
    ["cat10", "cat6"], ["cat10", "cat7"],
    ["cat11", "cat9"]
  ];

  var esc = function (s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  };

  function categoryStatus(catId, project) {
    try {
      if (window.getCategoryStatus) return window.getCategoryStatus(catId, project) || null;
    } catch (e) { /* fall through to no-data */ }
    return null;
  }

  // Map a raw per-module status string (from getModuleStatus) to a fill colour.
  // Mirrors the worst-status-wins keyword logic getCategoryStatus uses, so a
  // module dot's colour matches how the module cards read the same status.
  function moduleFill(raw) {
    if (!raw) return NO_DATA_FILL;
    var s = String(raw).toLowerCase();
    if (s.indexOf("red") >= 0) return STATUS_FILL.Red;
    if (s.indexOf("amber") >= 0 || s.indexOf("orange") >= 0) return STATUS_FILL.Amber;
    if (s.indexOf("yellow") >= 0 || s.indexOf("light-amber") >= 0) return STATUS_FILL.Yellow;
    if (s.indexOf("green") >= 0) return STATUS_FILL.Green;
    if (s.indexOf("complete") >= 0 || s.indexOf("blue") >= 0) return STATUS_FILL.Complete;
    return NO_DATA_FILL;
  }

  // G/Y/A/R bucket for a raw module status (null/insufficient -> null, i.e. the
  // module abstains and is excluded from the vote tally). Complete groups with
  // Green, matching the footer/category aggregation.
  function statusBucket(raw) {
    if (!raw) return null;
    var s = String(raw).toLowerCase();
    if (s.indexOf("red") >= 0) return "R";
    if (s.indexOf("amber") >= 0 || s.indexOf("orange") >= 0) return "A";
    if (s.indexOf("yellow") >= 0 || s.indexOf("light-amber") >= 0) return "Y";
    if (s.indexOf("green") >= 0) return "G";
    if (s.indexOf("complete") >= 0 || s.indexOf("blue") >= 0) return "G";
    return null;
  }
  var BUCKET_FILL = { G: STATUS_FILL.Green, Y: STATUS_FILL.Yellow, A: STATUS_FILL.Amber, R: STATUS_FILL.Red };
  var BUCKET_WORD = { G: "Green", Y: "Yellow", A: "Amber", R: "Red" };

  // Lay this category's modules out as small dots in an arc around the node,
  // avoiding the bottom wedge where the category label sits. One ring up to
  // 12 modules; two concentric rings above that (Cat 7 = 20) so they stay
  // legible. Dot count always equals the real module count (no-data included).
  function buildDots(catObj, pos, project) {
    var mods = (catObj && catObj.modules) || [];
    var n = mods.length;
    if (!n) return [];
    var ARC_START = 153 * Math.PI / 180;   // lower-left, just below horizontal
    var ARC_SWEEP = 234 * Math.PI / 180;   // sweep up and over to lower-right
    var statusOf = function (m) {
      try { return window.getModuleStatus ? window.getModuleStatus(m.method_class, project) : null; }
      catch (e) { return null; }
    };
    var dots = [];
    // phase shifts each dot within its angular step (0 = centred); the outer
    // ring uses 0.5 so its dots interleave with the inner ring rather than
    // stacking on the same radial spokes.
    var place = function (count, radius, startIdx, phase) {
      for (var j = 0; j < count; j++) {
        var a = ARC_START + ((j + 0.5 + (phase || 0)) / count) * ARC_SWEEP;
        var m = mods[startIdx + j];
        var raw = statusOf(m);
        dots.push({
          x: pos.x + radius * Math.cos(a),
          y: pos.y + radius * Math.sin(a),
          fill: moduleFill(raw),
          num: m && m.num, name: m && m.name, status: raw   // identity for the click callout
        });
      }
    };
    if (n > 12) {
      var inner = Math.ceil(n / 2);
      place(inner, NODE_R + 12, 0, 0);
      place(n - inner, NODE_R + 24, inner, 0.5);
    } else {
      place(n, NODE_R + 13, 0);
    }
    return dots;
  }

  function render(container, project) {
    if (!container) return;
    var cats = window.LIN_CATEGORIES || [];
    if (!cats.length) {
      container.innerHTML = '<p class="kn-sub">Category metadata unavailable.</p>';
      return;
    }

    // Compute each category's status once.
    var nodes = cats
      .filter(function (c) { return LAYOUT[c.id]; })
      .map(function (c) {
        var st = categoryStatus(c.id, project);
        return {
          id: c.id,
          num: c.num,                                   // "Cat 1" … "Cat 11"
          name: SHORT_NAME[c.id] || c.name,
          pos: LAYOUT[c.id],
          status: st,
          fill: st ? (STATUS_FILL[st] || NO_DATA_FILL) : NO_DATA_FILL,
          dots: buildDots(c, LAYOUT[c.id], project)     // per-module dots, coloured by module status
        };
      });
    var nodeById = {};
    nodes.forEach(function (n) { nodeById[n.id] = n; });

    // Footer counts.
    var counts = { Red: 0, Amber: 0, Yellow: 0, Green: 0, NoData: 0 };
    nodes.forEach(function (n) {
      if (n.status === "Red") counts.Red++;
      else if (n.status === "Amber") counts.Amber++;
      else if (n.status === "Yellow") counts.Yellow++;
      else if (n.status === "Green") counts.Green++;
      else if (n.status === "Complete") counts.Green++; // Complete groups with healthy in the tally
      else counts.NoData++;
    });
    var anyData = nodes.some(function (n) { return n.status != null; });

    // Derive the header counts from the canonical category data so they can
    // never drift from categories.js.
    var totalModules = cats.reduce(function (n, c) { return n + (c.modules || []).length; }, 0);

    container.innerHTML =
      '<section class="panel projnet2d-panel" aria-label="Project signal network">' +
        '<div class="projnet2d-head">' +
          '<p class="eyebrow">PROJECT SIGNAL NETWORK — ' + totalModules + ' modules · ' + cats.length + ' categories</p>' +
          '<p class="kn-sub">Derived from this project’s extracted signals</p>' +
          (anyData ? "" : '<p class="projnet2d-awaiting">Awaiting signal extraction — all categories shown as no-data.</p>') +
        '</div>' +
        '<div class="projnet2d-legend" aria-hidden="true">' +
          '<span><i style="background:#4ea0ff"></i>Complete</span>' +
          '<span><i style="background:#3fcaa6"></i>Green</span>' +
          '<span><i style="background:#f0c040"></i>Yellow</span>' +
          '<span><i style="background:#e2b13c"></i>Amber</span>' +
          '<span><i style="background:#e0556b"></i>Red</span>' +
          '<span><i style="background:#26344f"></i>No data</span>' +
        '</div>' +
        '<div class="projnet2d-wrap"><canvas class="projnet2d-canvas"></canvas></div>' +
        '<p class="projnet2d-foot kn-sub">' +
          counts.Red + " Red · " + counts.Amber + " Amber · " + counts.Yellow +
          " Yellow · " + counts.Green + " Green · " + counts.NoData + " No-data" +
        '</p>' +
      '</section>';

    var canvas = container.querySelector(".projnet2d-canvas");
    var wrap = container.querySelector(".projnet2d-wrap");
    if (!canvas || !wrap) return;
    var ctx = canvas.getContext("2d");

    // Label / edge colour follows the themed panel text colour.
    var inkColor = "#c9d4e3";
    try { var cc = getComputedStyle(canvas).color; if (cc) inkColor = cc; } catch (e) {}

    var view = { scale: 1, x: 0, y: 0 };
    var fitted = false;

    // Floating one-line callout (NOT a modal/panel) — a div positioned over the
    // canvas, anchored to the clicked bubble/dot. `active` tracks what's shown.
    var callout = document.createElement("div");
    callout.className = "projnet2d-callout";
    callout.style.display = "none";
    wrap.appendChild(callout);
    var active = null; // { key, wx, wy } in world coords, or null when hidden

    function cssSize() {
      var w = wrap.clientWidth || 720;
      return { w: w, h: 520 };   // taller to give the 103 module dots room at default zoom
    }

    function resize() {
      var dpr = window.devicePixelRatio || 1;
      var s = cssSize();
      canvas.width = Math.round(s.w * dpr);
      canvas.height = Math.round(s.h * dpr);
      canvas.style.width = s.w + "px";
      canvas.style.height = s.h + "px";
      if (!fitted) { fit(s); fitted = true; }
      draw();
    }

    // Fit the world box into the canvas with padding, centred.
    function fit(s) {
      var pad = 28;
      var sx = (s.w - pad * 2) / WORLD_W;
      var sy = (s.h - pad * 2) / WORLD_H;
      view.scale = Math.max(0.2, Math.min(sx, sy));
      view.x = (s.w - WORLD_W * view.scale) / 2;
      view.y = (s.h - WORLD_H * view.scale) / 2;
    }

    function worldArrow(from, to) {
      var a = from.pos, b = to.pos;
      var dx = b.x - a.x, dy = b.y - a.y;
      var len = Math.sqrt(dx * dx + dy * dy) || 1;
      var ux = dx / len, uy = dy / len;
      return {
        x1: a.x + ux * NODE_R, y1: a.y + uy * NODE_R,
        x2: b.x - ux * (NODE_R + 3), y2: b.y - uy * (NODE_R + 3),
        ux: ux, uy: uy
      };
    }

    function hexToRgba(hex, alpha) {
      // inkColor may be rgb()/rgba() (from getComputedStyle) or a hex literal.
      if (/^rgb/i.test(hex)) {
        return hex.replace(/rgba?\(([^)]+)\)/i, function (_, inner) {
          var parts = inner.split(",").map(function (v) { return v.trim(); });
          return "rgba(" + parts[0] + "," + parts[1] + "," + parts[2] + "," + alpha + ")";
        });
      }
      var m = /^#?([0-9a-f]{6})$/i.exec(hex);
      if (!m) return "rgba(150,170,200," + alpha + ")";
      var n = parseInt(m[1], 16);
      return "rgba(" + ((n >> 16) & 255) + "," + ((n >> 8) & 255) + "," + (n & 255) + "," + alpha + ")";
    }

    function draw() {
      var dpr = window.devicePixelRatio || 1;
      var s = cssSize();
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, s.w, s.h);
      ctx.translate(view.x, view.y);
      ctx.scale(view.scale, view.scale);

      // Edges (under nodes).
      ctx.lineWidth = 1.4;
      ctx.strokeStyle = hexToRgba(inkColor, 0.45);
      ctx.fillStyle = hexToRgba(inkColor, 0.55);
      EDGES.forEach(function (e) {
        var from = nodeById[e[0]], to = nodeById[e[1]];
        if (!from || !to) return;
        var ar = worldArrow(from, to);
        ctx.beginPath();
        ctx.moveTo(ar.x1, ar.y1);
        ctx.lineTo(ar.x2, ar.y2);
        ctx.stroke();
        // Arrowhead.
        var ah = 7, aw = 4;
        var px = -ar.uy, py = ar.ux; // perpendicular
        ctx.beginPath();
        ctx.moveTo(ar.x2, ar.y2);
        ctx.lineTo(ar.x2 - ar.ux * ah + px * aw, ar.y2 - ar.uy * ah + py * aw);
        ctx.lineTo(ar.x2 - ar.ux * ah - px * aw, ar.y2 - ar.uy * ah - py * aw);
        ctx.closePath();
        ctx.fill();
      });

      // Module dots: thin connector spokes first (under the dots and nodes),
      // then the dots themselves coloured by each module's own status.
      nodes.forEach(function (n) {
        if (!n.dots || !n.dots.length) return;
        ctx.lineWidth = 0.6;
        ctx.strokeStyle = hexToRgba(inkColor, 0.28);
        n.dots.forEach(function (d) {
          var dx = d.x - n.pos.x, dy = d.y - n.pos.y;
          var len = Math.sqrt(dx * dx + dy * dy) || 1;
          ctx.beginPath();
          ctx.moveTo(n.pos.x + (dx / len) * NODE_R, n.pos.y + (dy / len) * NODE_R);
          ctx.lineTo(d.x, d.y);
          ctx.stroke();
        });
        n.dots.forEach(function (d) {
          ctx.beginPath();
          ctx.arc(d.x, d.y, 3.3, 0, Math.PI * 2);
          ctx.fillStyle = d.fill;
          ctx.fill();
          ctx.lineWidth = 0.6;
          ctx.strokeStyle = hexToRgba(inkColor, 0.5);
          ctx.stroke();
        });
      });

      // Nodes.
      nodes.forEach(function (n) {
        ctx.beginPath();
        ctx.arc(n.pos.x, n.pos.y, NODE_R, 0, Math.PI * 2);
        ctx.fillStyle = n.fill;
        ctx.fill();
        ctx.lineWidth = 1.5;
        ctx.strokeStyle = hexToRgba(inkColor, 0.6);
        ctx.stroke();

        // "Cat N" centred in the node; light text except on the pale Yellow fill.
        ctx.fillStyle = (n.status === "Yellow") ? "#1c2330" : "#ffffff";
        ctx.font = "700 12px 'IBM Plex Mono', ui-monospace, monospace";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(n.num, n.pos.x, n.pos.y);

        // Category short-name below the node.
        ctx.fillStyle = inkColor;
        ctx.font = "600 11px 'Inter', system-ui, sans-serif";
        ctx.textBaseline = "top";
        ctx.fillText(n.name, n.pos.x, n.pos.y + NODE_R + 5);
      });

      // Keep the callout pinned to its world anchor through zoom/pan.
      positionCallout();
    }

    // ── Click callout (one floating line; no panel/modal) ──
    function worldToScreen(wx, wy) { return { x: view.x + wx * view.scale, y: view.y + wy * view.scale }; }
    function colorSpan(text, color) { return '<span style="color:' + color + '">' + esc(text) + '</span>'; }

    // Vertical callout for a category bubble — one row per bucket, then fused status.
    function catCalloutHtml(n) {
      var c = { G: 0, Y: 0, A: 0, R: 0, none: 0 };
      (n.dots || []).forEach(function (d) { var b = statusBucket(d.status); if (b) c[b]++; else c.none++; });
      var fusedColor = n.status ? (STATUS_FILL[n.status] || inkColor) : inkColor;
      var rows = '<div class="pn2d-co-row pn2d-co-cat">' + esc(n.num) + '</div>' +
        '<div class="pn2d-co-row">' + colorSpan(c.G + "  G", BUCKET_FILL.G) + '</div>' +
        '<div class="pn2d-co-row">' + colorSpan(c.Y + "  Y", BUCKET_FILL.Y) + '</div>' +
        '<div class="pn2d-co-row">' + colorSpan(c.A + "  A", BUCKET_FILL.A) + '</div>' +
        '<div class="pn2d-co-row">' + colorSpan(c.R + "  R", BUCKET_FILL.R) + '</div>' +
        (c.none ? '<div class="pn2d-co-row pn2d-co-dim">' + c.none + '  no-data</div>' : '') +
        '<div class="pn2d-co-row pn2d-co-divider"></div>' +
        '<div class="pn2d-co-row">' + colorSpan("→ " + (n.status || "No data"), fusedColor) + '</div>';
      return '<div class="pn2d-co-stack">' + rows + '</div>';
    }

    // "1.2 CUSUM — Green" (or "— No data").
    function modCalloutHtml(d) {
      var label = (d.num ? d.num + " " : "") + (d.name || "Module");
      var b = statusBucket(d.status);
      var word = d.status ? (b ? BUCKET_WORD[b] : String(d.status)) : "No data";
      var color = b ? BUCKET_FILL[b] : inkColor;
      return '<span class="pn2d-co-cat">' + esc(label) + '</span> — ' + colorSpan(word, color);
    }

    function showCallout(key, wx, wy, html) {
      active = { key: key, wx: wx, wy: wy };
      callout.innerHTML = html;
      callout.style.display = "block";
      positionCallout();
    }
    function hideCallout() { active = null; callout.style.display = "none"; }
    function positionCallout() {
      if (!active) return;
      var p = worldToScreen(active.wx, active.wy);
      var s = cssSize();
      var cw = callout.offsetWidth || 160, ch = callout.offsetHeight || 22;
      var left = p.x + 12, top = p.y - ch - 8;          // upper-right of the anchor
      if (left + cw > s.w - 4) left = p.x - cw - 12;     // flip left near the right edge
      if (left < 4) left = 4;
      if (top < 4) top = p.y + 14;                       // flip below if off the top
      if (top + ch > s.h - 4) top = s.h - ch - 4;
      callout.style.left = Math.round(left) + "px";
      callout.style.top = Math.round(top) + "px";
    }

    // A click (mousedown+mouseup with no drag) toggles a callout for the bubble
    // or dot under the cursor; clicking empty space or the same node hides it.
    function handleClick(clientX, clientY) {
      var rect = canvas.getBoundingClientRect();
      var sx = clientX - rect.left, sy = clientY - rect.top;
      // Dots first (small, sit around the bubble), then bubbles.
      for (var ni = 0; ni < nodes.length; ni++) {
        var n = nodes[ni], dots = n.dots || [];
        for (var di = 0; di < dots.length; di++) {
          var d = dots[di], ps = worldToScreen(d.x, d.y), rr = Math.max(7, 3.3 * view.scale);
          if ((sx - ps.x) * (sx - ps.x) + (sy - ps.y) * (sy - ps.y) <= rr * rr) {
            var mkey = "mod:" + n.id + ":" + di;
            if (active && active.key === mkey) { hideCallout(); return; }
            showCallout(mkey, d.x, d.y, modCalloutHtml(d));
            return;
          }
        }
      }
      for (var k = 0; k < nodes.length; k++) {
        var nn = nodes[k], nps = worldToScreen(nn.pos.x, nn.pos.y), nr = NODE_R * view.scale;
        if ((sx - nps.x) * (sx - nps.x) + (sy - nps.y) * (sy - nps.y) <= nr * nr) {
          var ckey = "cat:" + nn.id;
          if (active && active.key === ckey) { hideCallout(); return; }
          showCallout(ckey, nn.pos.x, nn.pos.y, catCalloutHtml(nn));
          return;
        }
      }
      hideCallout();   // empty space
    }

    // Tear down listeners from any previous render into this same container
    // (detail.js re-renders on every project open / inline overwrite) so window
    // listeners can't accumulate and fire against detached canvases.
    if (typeof container.__projnet2dCleanup === "function") {
      try { container.__projnet2dCleanup(); } catch (e) { /* non-fatal */ }
    }

    // ── Interaction: scroll to zoom, drag to pan (no rotate) ──
    canvas.addEventListener("wheel", function (e) {
      e.preventDefault();
      var rect = canvas.getBoundingClientRect();
      var sx = e.clientX - rect.left, sy = e.clientY - rect.top;
      var factor = e.deltaY > 0 ? 0.9 : 1.1;
      var next = Math.max(0.3, Math.min(4, view.scale * factor));
      // Keep the point under the cursor fixed while zooming.
      view.x = sx - (sx - view.x) * (next / view.scale);
      view.y = sy - (sy - view.y) * (next / view.scale);
      view.scale = next;
      draw();
    }, { passive: false });

    var dragging = false, lastX = 0, lastY = 0, pressX = 0, pressY = 0, movedDuringPress = false;
    canvas.addEventListener("mousedown", function (e) {
      dragging = true; lastX = e.clientX; lastY = e.clientY;
      pressX = e.clientX; pressY = e.clientY; movedDuringPress = false;
      canvas.style.cursor = "grabbing";
    });
    canvas.style.cursor = "grab";

    // mousemove/mouseup live on window so a drag keeps tracking (and ends)
    // even when the cursor leaves the canvas.
    function onMouseMove(e) {
      if (!dragging) return;
      if (!movedDuringPress && Math.abs(e.clientX - pressX) + Math.abs(e.clientY - pressY) > 4) {
        movedDuringPress = true;
      }
      view.x += e.clientX - lastX;
      view.y += e.clientY - lastY;
      lastX = e.clientX; lastY = e.clientY;
      draw();
    }
    function onMouseUp() {
      if (!dragging) return;
      dragging = false; canvas.style.cursor = "grab";
      // A press with no real movement is a click → toggle the callout.
      if (!movedDuringPress) handleClick(pressX, pressY);
    }
    // A detached canvas means the detail page was re-rendered — self-clean and stop.
    function onResize() {
      if (!document.body.contains(canvas)) { cleanup(); return; }
      resize();
    }
    function cleanup() {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
      window.removeEventListener("resize", onResize);
      if (container.__projnet2dCleanup === cleanup) container.__projnet2dCleanup = null;
    }
    container.__projnet2dCleanup = cleanup;

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    window.addEventListener("resize", onResize);
    resize();
  }

  window.LinProjectNet2D = { render: render };
})();
