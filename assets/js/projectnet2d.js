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
    cat10: "Data Integrity", cat11: "Decision Opt", cat12: "Systems Eng"
  };

  // Fixed 2D layout (world coordinates). Left-to-right signal flow:
  // generators (Cat 1–5) → synthesis (Cat 6) → evidence (Cat 7) / ML (Cat 8)
  // → governance (Cat 9); Cat 10 (data integrity), Cat 11 (decision opt) and
  // Cat 12 (systems engineering) sit as supporting inputs near their targets.
  // Spacing is chosen so node labels never collide.
  var LAYOUT = {
    cat1:  { x: 110, y: 70  }, cat2: { x: 110, y: 160 }, cat3: { x: 110, y: 250 },
    cat4:  { x: 110, y: 340 }, cat5: { x: 110, y: 430 },
    cat6:  { x: 340, y: 150 }, cat10:{ x: 340, y: 330 }, cat12:{ x: 340, y: 480 },
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
    ["cat11", "cat9"],
    ["cat12", "cat5"]
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
          num: c.num,                                   // "Cat 1" … "Cat 12"
          name: SHORT_NAME[c.id] || c.name,
          pos: LAYOUT[c.id],
          status: st,
          fill: st ? (STATUS_FILL[st] || NO_DATA_FILL) : NO_DATA_FILL
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

    container.innerHTML =
      '<section class="panel projnet2d-panel" aria-label="Project signal network">' +
        '<div class="projnet2d-head">' +
          '<p class="eyebrow">PROJECT SIGNAL NETWORK — 108 modules · 12 categories</p>' +
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

    function cssSize() {
      var w = wrap.clientWidth || 720;
      return { w: w, h: 440 };
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

    var dragging = false, lastX = 0, lastY = 0;
    canvas.addEventListener("mousedown", function (e) {
      dragging = true; lastX = e.clientX; lastY = e.clientY;
      canvas.style.cursor = "grabbing";
    });
    window.addEventListener("mouseup", function () {
      dragging = false; canvas.style.cursor = "grab";
    });
    canvas.addEventListener("mousemove", function (e) {
      if (!dragging) return;
      view.x += e.clientX - lastX;
      view.y += e.clientY - lastY;
      lastX = e.clientX; lastY = e.clientY;
      draw();
    });
    canvas.style.cursor = "grab";

    window.addEventListener("resize", resize);
    resize();
  }

  window.LinProjectNet2D = { render: render };
})();
