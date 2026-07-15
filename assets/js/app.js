/* ============================================================
   Lin Project Radar — app.js
   Radar rendering, theme switching, signal ledger,
   PCEIF decision card, audit export.
   Depends on (load order): data.js, decision.js, app.js
   ============================================================ */

(function () {
  "use strict";

  /* ---------- HTML escape helper (XSS defence) ----------
     EVERY interpolation of dynamic data into innerHTML must pass through
     esc(). Quote escaping (" and ') is required so values land safely
     inside HTML attributes too, not just text content. Other files
     (deepdive.js, knowledge.js, signals.js, etc.) have their own local
     esc(); app.js previously had none, which the security scan flagged. */
  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  // Exact equal thirds (120° each). Angles are screen-polar:
  // 0° = right, positive = clockwise (y grows downward in polar()).
  // internal key stays "combined" (and SYN-CMB codes are unchanged);
  // only the human-facing sector label is "HYBRID".
  // Sectors define only the angular wedge a project plots in (by id prefix).
  // Sector identity is shown in the legend below the radar, not on the scope.
  const SECTORS = {
    design:       { label: "DESIGN",       start: -90, end: 30  },
    construction: { label: "CONSTRUCTION", start: 30,  end: 150 },
    hybrid:       { label: "HYBRID",       start: 150, end: 270 },
    // legacy alias so any "combined" records still plot in the hybrid arc
    combined:     { label: "HYBRID",       start: 150, end: 270 }
  };

  const STATUS_COLOR = {
    complete: "#4ea0ff",
    green: "var(--clear-green)",
    yellow: "var(--yellow)",
    amber: "var(--radar-amber)",
    red:   "var(--alarm-red)"
  };

  const SVG_NS = "http://www.w3.org/2000/svg";
  // Rectangular stage: the SVG spans the full panel width with a wide viewBox
  // (1200×460); the circular scope keeps its fixed geometry, centered, and the
  // side columns (status legend / ring thresholds) absorb the flexible width.
  // Below ~800px panel width buildRadar() switches to a narrow stacked viewBox.
  // The scope center is therefore mutable — set per build, read by polar().
  let CENTER_X = 600;          // wide stage scope center
  let CENTER_Y = 230;
  const R_MIN = 0.08 * 180;    // inner radius (health 100)
  const R_MAX = 0.92 * 180;    // outer radius (health 0)

  let selectedId = null;
  const decisionLog = [];

  /* ---------- small helpers ---------- */
  const $ = (sel, root = document) => root.querySelector(sel);
  const el = (tag, attrs = {}) => {
    const node = document.createElementNS(SVG_NS, tag);
    for (const k in attrs) node.setAttribute(k, attrs[k]);
    return node;
  };
  const reduceMotion = () =>
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Stable angle within a sector from a hashed id (no per-render jitter)
  function hashAngle(project) {
    // Unknown / missing sector must not throw and drop the project — fall back
    // to the hybrid arc so it still plots.
    const sec = SECTORS[project.sector] || SECTORS.hybrid;
    const id = String(project && project.id || "");
    let h = 0;
    for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) >>> 0;
    const span = sec.end - sec.start;
    const frac = (h % 1000) / 1000;
    // keep blips off the exact sector boundaries
    return sec.start + span * (0.14 + 0.72 * frac);
  }

  function healthToRadius(health) {
    const clamped = Math.max(0, Math.min(100, health));
    return R_MIN + (R_MAX - R_MIN) * (1 - clamped / 100);
  }

  /* ---------- empty-aware project state ----------
     A project with no signals is "awaiting ingest" — never a
     fabricated green/amber/red. Only populated projects get a
     derived state (and only those reach decision.js). */
  // Slim portfolio records (v10.28 listslim) carry a precomputed `status` string
  // and no `signals` object, so the radar/list read that field directly. Full
  // records (fetched on detail open) keep the deriveHealthState path unchanged.
  function statusKey(p) {
    if (p && p.slim) {
      const lab = (typeof slimStatusLabel === "function") ? slimStatusLabel(p) : null;
      return lab ? lab.toLowerCase().replace("-review", "") : "empty";
    }
    if (!hasSignals(p)) return "empty";
    return deriveHealthState(p).toLowerCase().replace("-review", "");
  }
  function stateLabel(p) {
    if (p && p.slim) {
      const lab = (typeof slimStatusLabel === "function") ? slimStatusLabel(p) : null;
      return lab || "Awaiting ingest";
    }
    return hasSignals(p) ? deriveHealthState(p) : "Awaiting ingest";
  }
  // health proxy → radius band, so distance still reads as drift:
  // green near center, amber mid, red outer. Empty sits at a neutral mid-ring.
  function proxyHealth(p) {
    switch (statusKey(p)) {
      case "complete": return 92;  // finished — near centre
      case "green":  return 85;  // inside green zone
      case "yellow": return 70;  // early-warning, between green and amber
      case "amber":  return 55;  // inside amber ring
      case "red":    return 25;  // inside red-review ring
      default:      return 50;   // empty → neutral radius (rendered hollow/grey)
    }
  }

  function polar(angleDeg, radius) {
    const a = (angleDeg * Math.PI) / 180;
    return { x: CENTER_X + radius * Math.cos(a), y: CENTER_Y + radius * Math.sin(a) };
  }

  /* ---------- rectangular-stage side columns ----------
     LEFT of the scope: a vertical status legend (dot + name + count per
     status). RIGHT: the ring-meaning labels ("On track / Watch / Escalate")
     moved off the scope face, with faint dashed leader ticks back to their
     rings. Both in mono 11px. In narrow (stacked) mode both columns render
     beneath the scope and the leaders are omitted. */
  function buildStageColumns(svg, narrow, VW, VH, thresholdRings) {
    const mono = { "font-family": "var(--font-mono, monospace)", "font-size": "11", fill: "var(--muted)" };

    // status counts from the live portfolio
    const counts = { complete: 0, green: 0, yellow: 0, amber: 0, red: 0, empty: 0 };
    LIN_PROJECTS.forEach((p) => {
      try { const k = statusKey(p); counts[k in counts ? k : "empty"]++; } catch (e) { counts.empty++; }
    });
    const LEGEND_ROWS = [
      ["Complete", STATUS_COLOR.complete, counts.complete],
      ["Green",    STATUS_COLOR.green,    counts.green],
      ["Yellow",   STATUS_COLOR.yellow,   counts.yellow],
      ["Amber",    STATUS_COLOR.amber,    counts.amber],
      ["Red",      STATUS_COLOR.red,      counts.red],
      ["Awaiting", "var(--muted)",        counts.empty],
    ];

    function textEl(x, y, str, attrs) {
      const t = el("text", Object.assign({ x, y, "dominant-baseline": "middle" }, mono, attrs || {}));
      t.textContent = str;
      return t;
    }

    // ── left column: STATUS legend ──
    const legX = narrow ? 46 : 46;
    let legY = narrow ? VH - 190 : 128;
    const leg = el("g", { class: "scope-col scope-col-status" });
    leg.appendChild(textEl(legX, legY, "STATUS", { fill: "var(--faint)", "letter-spacing": "0.2em", "font-size": "10" }));
    legY += 22;
    LEGEND_ROWS.forEach(([name, color, n]) => {
      leg.appendChild(el("circle", { cx: legX + 5, cy: legY, r: 4, fill: color, opacity: name === "Awaiting" ? "0.5" : "0.9" }));
      leg.appendChild(textEl(legX + 16, legY + 0.5, name));
      leg.appendChild(textEl(legX + 92, legY + 0.5, String(n), { fill: "var(--text)" }));
      legY += 24;
    });
    svg.appendChild(leg);

    // ── right column: ring thresholds ──
    const col = el("g", { class: "scope-col scope-col-rings" });
    if (narrow) {
      let ty = VH - 190;
      col.appendChild(textEl(250, ty, "RINGS", { fill: "var(--faint)", "letter-spacing": "0.2em", "font-size": "10" }));
      ty += 22;
      thresholdRings.forEach(({ stroke, label }, i) => {
        col.appendChild(el("line", { x1: 250, y1: ty, x2: 262, y2: ty, stroke, "stroke-width": "2" }));
        col.appendChild(textEl(268, ty + 0.5, label + (i === 0 ? " (inner)" : i === 1 ? " (middle)" : " (outer)")));
        ty += 24;
      });
    } else {
      const colX = 1000;
      col.appendChild(textEl(colX, 128, "RINGS", { fill: "var(--faint)", "letter-spacing": "0.2em", "font-size": "10" }));
      // one label row per ring, each with a faint dashed leader tick back to
      // the ring it names (staggered exit angles keep the leaders apart)
      const rows = [
        { i: 0, angle: -24, y: 168 },
        { i: 1, angle: -8,  y: 210 },
        { i: 2, angle: 8,   y: 252 },
      ];
      rows.forEach(({ i, angle, y }) => {
        const ring = thresholdRings[i];
        const pt = polar(angle, R_MAX * ring.frac);
        col.appendChild(el("path", {
          d: `M ${pt.x.toFixed(1)} ${pt.y.toFixed(1)} L ${colX - 32} ${y} L ${colX - 10} ${y}`,
          fill: "none", stroke: ring.stroke, "stroke-width": "1",
          "stroke-dasharray": "3 4", opacity: "0.35"
        }));
        col.appendChild(el("circle", { cx: colX + 1, cy: y, r: 3.5, fill: ring.stroke, opacity: "0.9" }));
        col.appendChild(textEl(colX + 12, y + 0.5, ring.label));
      });
    }
    svg.appendChild(col);
  }

  /* ---------- radar scope ---------- */
  function buildRadar() {
    const svg = $("#radar-svg");
    svg.innerHTML = "";

    // Visibility into exactly what reaches the radar. A project missing from
    // this list was dropped before render (hydrate / archived split) rather
    // than by buildRadar itself.
    console.log("Projects loaded:", LIN_PROJECTS.length, LIN_PROJECTS.map((p) => p.id));

    const R = R_MAX; // 165.6 — outer edge

    // ── rectangular stage geometry ────────────────────────────────────────
    // Wide stage: 1200×460, scope centered, status legend left / threshold
    // labels right. Narrow (<800px panel): 460×680, side columns stack below.
    const wrap = svg.parentElement;
    const panelW = (wrap && wrap.clientWidth) || window.innerWidth;
    const narrow = panelW < 800;
    const VW = narrow ? 460 : 1200;
    const VH = narrow ? 680 : 460;
    CENTER_X = narrow ? 230 : 600;
    CENTER_Y = 230;
    svg.setAttribute("viewBox", `0 0 ${VW} ${VH}`);
    svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
    if (wrap) wrap.style.aspectRatio = `${VW} / ${VH}`;

    // ── defs: sweep-trail gradient + the ONE shared blip marker ──────────
    const defs = el("defs");
    const trailGrad = el("radialGradient", {
      id: "sweep-trail-grad", gradientUnits: "userSpaceOnUse",
      cx: CENTER_X, cy: CENTER_Y, r: R
    });
    const tg1 = el("stop"); tg1.setAttribute("offset", "0%"); tg1.setAttribute("stop-color", "var(--phosphor)"); tg1.setAttribute("stop-opacity", "0");
    const tg2 = el("stop"); tg2.setAttribute("offset", "100%"); tg2.setAttribute("stop-color", "var(--phosphor)"); tg2.setAttribute("stop-opacity", "0.4");
    trailGrad.appendChild(tg1); trailGrad.appendChild(tg2);
    defs.appendChild(trailGrad);
    // Uniform building marker — a single minimal geometric glyph (pitched
    // roof + body) every blip references via <use>. Status is the only thing
    // that varies (fill color); sector is already encoded by the angular
    // wedge, so it needs no icon of its own.
    const buildingSym = el("symbol", { id: "blip-building", viewBox: "0 0 24 24" });
    buildingSym.appendChild(el("path", {
      d: "M12 3 L21 11 H18 V21 H6 V11 H3 Z",
      fill: "currentColor"
    }));
    defs.appendChild(buildingSym);
    svg.appendChild(defs);

    // ── full-stage panel background (one rectangular instrument screen) ───
    // page-bg underlay + surface wash (the surface var is translucent), same
    // treatment as the Signal Flow chart, so nothing bleeds through.
    svg.appendChild(el("rect", { x: 0, y: 0, width: VW, height: VH, fill: "var(--page-bg, #06080f)" }));
    svg.appendChild(el("rect", { x: 0, y: 0, width: VW, height: VH, fill: "var(--surface, #0b0e17)" }));

    // ── scope background (dark CRT surface, no colored zone bands) ───────
    svg.appendChild(el("circle", {
      cx: CENTER_X, cy: CENTER_Y, r: R,
      fill: "rgba(0,8,18,0.92)"
    }));

    // ── 4 faint concentric range rings ───────────────────────────────────
    for (let i = 1; i <= 4; i++) {
      svg.appendChild(el("circle", {
        cx: CENTER_X, cy: CENTER_Y, r: R * i / 4,
        fill: "none",
        stroke: "rgba(96,210,232,0.12)",
        "stroke-width": "0.5"
      }));
    }

    // ── outer solid ring ─────────────────────────────────────────────────
    svg.appendChild(el("circle", {
      cx: CENTER_X, cy: CENTER_Y, r: R,
      fill: "none",
      stroke: "rgba(96,210,232,0.35)",
      "stroke-width": "1.2"
    }));

    // ── threshold rings: Green / Amber / Red ─────────────────────────────
    // The ring-meaning labels live OFF the scope face, in the right-hand
    // threshold column (drawn below), keeping the scope itself clean.
    const THRESHOLD_RINGS = [
      { frac: 0.33, stroke: "#3fcaa6", label: "On track" },
      { frac: 0.66, stroke: "#e2b13c", label: "Watch"    },
      { frac: 0.90, stroke: "#e0556b", label: "Escalate" },
    ];
    THRESHOLD_RINGS.forEach(({ frac, stroke }) => {
      svg.appendChild(el("circle", {
        cx: CENTER_X, cy: CENTER_Y, r: R * frac,
        fill: "none",
        stroke,
        "stroke-opacity": "0.4",
        "stroke-width": "1"
      }));
    });

    // ── 12 radial lines every 30° ─────────────────────────────────────────
    for (let deg = 0; deg < 360; deg += 30) {
      const tip = polar(deg, R);
      svg.appendChild(el("line", {
        x1: CENTER_X, y1: CENTER_Y, x2: tip.x, y2: tip.y,
        stroke: "rgba(96,210,232,0.08)",
        "stroke-width": "0.5"
      }));
    }

    // ── side columns: status legend (left) + ring thresholds (right) ─────
    buildStageColumns(svg, narrow, VW, VH, THRESHOLD_RINGS);

    // ── degree markings just inside outer ring ───────────────────────────
    for (let deg = 0; deg < 360; deg += 30) {
      const pos = polar(deg, R - 13);
      const t = el("text", {
        x: pos.x, y: pos.y,
        "text-anchor": "middle", "dominant-baseline": "middle",
        class: "scope-deg-label"
      });
      t.textContent = String(deg);
      svg.appendChild(t);
    }

    // ── rotating sweep hand — SMIL animateTransform with explicit center ──
    // from="0 cx cy" to="360 cx cy" guarantees the pivot is at (cx,cy) in
    // SVG user coords, independent of CSS viewport sizing.
    if (!reduceMotion()) {
      const sweepG = el("g");

      // 60° trailing phosphor wedge: from –60° to 0° (both in SVG screen-polar)
      const tipA = polar(0, R);   // East
      const tipB = polar(-60, R); // NE
      sweepG.appendChild(el("path", {
        d: `M ${CENTER_X} ${CENTER_Y} L ${tipA.x.toFixed(1)} ${tipA.y.toFixed(1)} A ${R.toFixed(1)} ${R.toFixed(1)} 0 0 0 ${tipB.x.toFixed(1)} ${tipB.y.toFixed(1)} Z`,
        fill: "url(#sweep-trail-grad)"
      }));

      // sweep line: from center (cx,cy) to outer edge at 0° (East)
      sweepG.appendChild(el("line", {
        x1: CENTER_X, y1: CENTER_Y,
        x2: tipA.x.toFixed(1), y2: tipA.y.toFixed(1),
        stroke: "var(--phosphor)", "stroke-width": "1.5", opacity: "0.9"
      }));

      // SMIL rotation — pivot explicitly at (CENTER_X, CENTER_Y) in user coords
      const anim = document.createElementNS(SVG_NS, "animateTransform");
      anim.setAttribute("attributeName", "transform");
      anim.setAttribute("type", "rotate");
      anim.setAttribute("from", `0 ${CENTER_X} ${CENTER_Y}`);
      anim.setAttribute("to", `360 ${CENTER_X} ${CENTER_Y}`);
      anim.setAttribute("dur", "4s");
      anim.setAttribute("repeatCount", "indefinite");
      sweepG.appendChild(anim);

      svg.appendChild(sweepG);
    }

    // ── blips — two passes (collision de-overlap + label nudge) ──────────
    const plots = LIN_PROJECTS.map((p) => {
      try {
        const ang = hashAngle(p);
        return { p, ang, r: healthToRadius(proxyHealth(p)) };
      } catch (err) {
        // Never drop a project because its plot math threw — log it and place
        // it at a neutral default so it still appears on the radar.
        console.error("Radar plot failed for project", p && p.id, "—", err && err.message);
        return { p, ang: 0, r: healthToRadius(50) };
      }
    });

    // pass 1: collision de-overlap (deterministic by list order). Keep each
    // blip inside its true sector wedge (angle nudged at most ±8°, so the
    // sector reading stays correct) and push it outward in radius until it
    // clears every already-placed blip by MIN_SEP. The true radius is kept on
    // q.trueR so a faint tick can show the original drift when nudged far.
    const MIN_SEP = 34;               // ~2.4× the icon radius (ICON = 14)
    const RADIUS_CAP = R_MAX - 2;     // hard cap at outer ring edge
    const placedDots = [];
    plots.forEach((q) => {
      q.trueR = q.r;
      let r = q.r, ang = q.ang, pos = polar(ang, r), tries = 0;
      while (placedDots.some((d) => Math.hypot(d.x - pos.x, d.y - pos.y) < MIN_SEP) && tries < 12) {
        tries++;
        r = Math.min(RADIUS_CAP, q.trueR + tries * 7);                          // push outward
        const adeg = ((tries % 2) ? 1 : -1) * Math.min(8, Math.ceil(tries / 2) * 3); // small ± within ±8°
        ang = q.ang + adeg;
        pos = polar(ang, r);
      }
      // final-assignment clamp (fix/static-blips): no blip may sit outside the
      // ring, whatever the collision passes did to its radius.
      r = Math.min(r, R_MAX - 2);
      pos = polar(ang, r);
      q.x = pos.x; q.y = pos.y; q.r = r;
      placedDots.push({ x: pos.x, y: pos.y });
    });

    // pass 2: label collision avoidance — nudge the LABEL only (never the
    // blip), vertically in ±10px steps, from the uniform (+11, +4) offset.
    const LABEL_W = 44, LABEL_NUDGE = 10;
    plots.forEach((q) => { q.lx = q.x + 11; q.ly = q.y + 4; });
    const byY = plots.slice().sort((a, b) => a.ly - b.ly);
    byY.forEach((q, i) => {
      let moved = true, guard = 0;
      while (moved && guard < 20) {
        moved = false; guard++;
        for (let j = 0; j < i; j++) {
          const o = byY[j];
          if (Math.abs(o.lx - q.lx) < LABEL_W && Math.abs(o.ly - q.ly) < LABEL_NUDGE) {
            q.ly = o.ly + LABEL_NUDGE; moved = true;
          }
        }
      }
    });

    // ONE uniform marker for every blip — the shared #blip-building symbol
    // defined in <defs> above. No per-sector glyph branch exists anymore.
    const ICON = 14; // display size in SVG user units

    plots.forEach((q) => {
     try {
      const p = q.p;
      const status = statusKey(p);
      const empty = status === "empty";
      const g = el("g", {
        class: empty ? "blip blip-empty" : "blip",
        "aria-label": `${p.id} ${p.name}, ${stateLabel(p)}`,
        "data-id": p.id
      });

      const color =
        status === "complete" ? STATUS_COLOR.complete :
        status === "green" ? STATUS_COLOR.green :
        status === "yellow" ? STATUS_COLOR.yellow :
        status === "amber" ? STATUS_COLOR.amber :
        status === "red"   ? STATUS_COLOR.red : "var(--muted)";

      // SVG tooltip
      const titleEl = el("title");
      titleEl.textContent = `${p.id} — ${p.name}`;
      g.appendChild(titleEl);

      // faint tick back toward the true drift radius when the de-overlap pass
      // nudged this blip more than ~20px off its real radial position, so the
      // original drift stays legible.
      if (q.trueR != null && !empty) {
        const tp = polar(q.ang, q.trueR);
        if (Math.hypot(q.x - tp.x, q.y - tp.y) > 20) {
          g.appendChild(el("line", {
            x1: q.x, y1: q.y, x2: tp.x.toFixed(1), y2: tp.y.toFixed(1),
            stroke: "var(--muted)", "stroke-width": "1", opacity: "0.3",
            class: "blip-true-tick"
          }));
        }
      }

      // ping ring — synced to sweep: fires when sweep reaches blip's angle
      const normAng = ((q.ang % 360) + 360) % 360;
      const pingDelay = -(4 - (normAng / 360) * 4);
      if (!reduceMotion() && !empty) {
        const pingRing = el("circle", {
          cx: q.x, cy: q.y, r: "9",
          fill: "none", stroke: color,
          "stroke-width": "1",
          class: "blip-ping-ring"
        });
        pingRing.style.animationDelay = `${pingDelay.toFixed(2)}s`;
        g.appendChild(pingRing);
      }

      // selection ring highlight around the building icon (no shape change) —
      // visible only via CSS on .selected / .hot / :focus-visible.
      g.appendChild(el("circle", {
        cx: q.x, cy: q.y, r: ICON / 2 + 5,
        fill: "none", stroke: "var(--phosphor)", "stroke-width": "1.5",
        class: "blip-ring", opacity: "0"
      }));

      // the ONE uniform building marker, colored only by status
      const icon = el("use", {
        href: "#blip-building",
        x: (q.x - ICON / 2).toFixed(1),
        y: (q.y - ICON / 2).toFixed(1),
        width: ICON, height: ICON,
        class: "blip-icon",
        opacity: empty ? "0.55" : "1"
      });
      icon.style.color = color;                       // symbol path uses currentColor
      icon.style.filter = `drop-shadow(0 0 4px ${color})`;  // glow, matches status
      g.appendChild(icon);

      // leader line when the label was nudged away from its natural spot
      if (Math.abs(q.ly - (q.y + 4)) > 5) {
        g.appendChild(el("line", {
          x1: q.x + 8, y1: q.y, x2: q.lx - 2, y2: q.ly - 3,
          class: "blip-leader"
        }));
      }

      const label = el("text", { x: q.lx, y: q.ly, class: "blip-label" });
      label.textContent = p.id;
      g.appendChild(label);

      const choose = () => openDetail(p.id);
      g.addEventListener("click", choose);
      // hover: emphasize label and re-append so it paints on top
      const raise = () => { g.classList.add("hot"); svg.appendChild(g); };
      const lower = () => { g.classList.remove("hot"); };
      g.addEventListener("mouseenter", raise);
      g.addEventListener("mouseleave", lower);

      svg.appendChild(g);
     } catch (err) {
      // One project's blip failing must never blank the radar or silently drop
      // the others — log which project and keep going.
      console.error("Blip render failed for project", q && q.p && q.p.id, "—", err && err.message);
     }
    });

    highlightBlip();
  }

  function highlightBlip() {
    document.querySelectorAll(".blip").forEach((b) => {
      const on = b.getAttribute("data-id") === selectedId;
      b.classList.toggle("selected", on);
    });
    highlightPin();
  }

  /* ============================================================
     Stylized HUD world map — the portfolio's second view.
     Pure inline SVG: no map library, no tiles, no external
     requests. The landmass is a compact hand-simplified outline
     (lng/lat vertex rings, ~2KB) projected equirectangularly at
     build time with the SAME projection the pins use, so land and
     pins always agree:
       x = (lng + 180) / 360 * W,   y = (90 - lat) / 180 * H
     Rendered as a glowing hologram: landmass fill at low opacity,
     coastline stroke, and the same stroke blurred beneath for the
     glow halo (the blur layer is hidden on the light theme, where
     crisp lines read better).
     ============================================================ */
  const MAP_W = 1200, MAP_H = 600;
  const VIEW_KEY = "lin-portfolio-view";
  let mapBuilt = false;      // lazily built on first switch
  let mapHydrated = false;   // slim records swapped for full ones (coords live in full project.json)

  function mapProject(lng, lat) {
    return { x: (lng + 180) / 360 * MAP_W, y: (90 - lat) / 180 * MAP_H };
  }
  function hasCoords(p) {
    return !!p && p.lat != null && p.lng != null &&
      Number.isFinite(Number(p.lat)) && Number.isFinite(Number(p.lng));
  }

  // Hand-simplified world landmass — coarse on purpose (stylized silhouette,
  // not cartography). Each ring is a closed [lng, lat] vertex list.
  const WORLD_LANDMASS = [
    // North America (incl. Alaska + Central America)
    [[-168,66],[-161,70],[-140,70],[-125,72],[-110,73],[-95,72],[-85,70],[-82,67],[-88,64],[-90,58],[-85,55],[-82,58],[-78,62],[-70,60],[-60,55],[-65,50],[-70,47],[-65,44],[-70,42],[-74,39],[-76,35],[-80,32],[-81,26],[-83,29],[-90,29],[-96,27],[-97,22],[-95,18],[-90,16],[-88,16],[-86,12],[-83,9],[-80,8],[-85,10],[-92,15],[-105,20],[-110,23],[-114,28],[-117,33],[-122,37],[-124,43],[-124,48],[-132,55],[-140,60],[-152,60],[-158,56],[-165,55]],
    // South America
    [[-78,7],[-72,10],[-63,10],[-52,4],[-50,0],[-44,-3],[-35,-6],[-37,-12],[-39,-15],[-41,-22],[-48,-26],[-52,-32],[-57,-36],[-62,-40],[-65,-45],[-69,-50],[-69,-54],[-72,-52],[-74,-46],[-73,-40],[-71,-33],[-70,-25],[-70,-18],[-75,-15],[-79,-8],[-81,-4],[-80,1],[-77,4]],
    // Greenland
    [[-45,60],[-40,63],[-32,68],[-22,70],[-20,74],[-28,78],[-38,80],[-50,80],[-58,76],[-55,72],[-52,66],[-48,61]],
    // Africa
    [[-6,35],[10,33],[20,32],[30,31],[34,27],[37,21],[39,15],[43,12],[51,11],[48,5],[42,-2],[40,-10],[36,-18],[33,-26],[27,-34],[19,-35],[16,-29],[12,-18],[13,-11],[9,-2],[8,4],[0,6],[-8,5],[-13,9],[-17,15],[-17,21],[-10,30]],
    // Madagascar
    [[44,-12],[50,-16],[48,-25],[44,-24],[43,-17]],
    // Eurasia (Europe + Asia + Arabia + India + SE Asia, one coarse ring)
    [[-9,43],[-9,36],[3,40],[7,44],[13,44],[19,41],[23,38],[26,39],[27,41],[33,42],[41,41],[48,44],[44,47],[36,46],[30,46],[24,56],[18,60],[22,65],[28,71],[40,68],[45,68],[60,69],[75,73],[90,76],[110,77],[130,72],[150,70],[160,70],[170,66],[178,65],[178,62],[170,60],[162,60],[158,52],[155,51],[157,58],[150,60],[142,54],[135,44],[129,38],[126,35],[122,31],[117,24],[108,19],[105,10],[104,2],[100,6],[98,12],[97,17],[94,16],[90,22],[86,20],[80,15],[77,8],[73,18],[70,22],[66,25],[60,25],[57,25],[59,22],[57,17],[52,13],[45,12],[43,17],[39,21],[35,28],[34,30],[36,36],[30,36],[27,37],[26,39],[23,38],[19,41],[13,44],[7,44],[3,40],[-2,44],[0,49],[4,52],[8,54],[8,57],[12,56],[10,54],[5,53],[0,50],[-5,48],[-2,46]],
    // British Isles
    [[-5,50],[-3,53],[-2,56],[-4,58],[-6,56],[-5,53],[-6,50]],
    // Iceland
    [[-22,64],[-15,64],[-14,66],[-20,67],[-24,65]],
    // Japan
    [[130,31],[134,34],[140,36],[142,40],[145,44],[141,43],[137,37],[131,33]],
    // Borneo
    [[109,0],[113,5],[117,4],[118,-1],[114,-4],[110,-2]],
    // Sumatra + Java (coarse)
    [[95,5],[99,2],[103,-2],[106,-6],[110,-7],[114,-8],[112,-9],[105,-7],[101,-4],[96,1]],
    // New Guinea
    [[131,-1],[136,-2],[141,-3],[147,-6],[150,-9],[144,-8],[138,-7],[132,-4]],
    // Australia
    [[114,-22],[122,-18],[130,-13],[136,-12],[142,-11],[146,-15],[149,-20],[153,-26],[151,-33],[146,-39],[140,-38],[135,-35],[129,-32],[124,-33],[115,-34],[113,-26]],
    // New Zealand (coarse)
    [[173,-35],[176,-38],[178,-38],[175,-41],[172,-44],[167,-46],[170,-43],[172,-40],[173,-37]]
  ];

  function worldPathD() {
    return WORLD_LANDMASS.map((ring) =>
      ring.map(([lng, lat], i) => {
        const pt = mapProject(lng, lat);
        return (i ? "L" : "M") + pt.x.toFixed(1) + " " + pt.y.toFixed(1);
      }).join(" ") + " Z"
    ).join(" ");
  }

  /* ---------- map tooltip (HTML singleton, like the flow chart's) ---------- */
  function getMapTooltip() {
    let t = document.getElementById("map-tt");
    if (!t) { t = document.createElement("div"); t.id = "map-tt"; document.body.appendChild(t); }
    return t;
  }

  function renderMap(svg) {
    svg.innerHTML = "";
    const tt = getMapTooltip();
    const hideTT = () => { tt.style.display = "none"; };
    const moveTT = (e) => { tt.style.left = (e.clientX + 14) + "px"; tt.style.top = (e.clientY - 10) + "px"; };

    // ── defs: glow blur, vignette gradient, the shared building marker ──
    const defs = el("defs");
    const blur = el("filter", { id: "map-blur", x: "-20%", y: "-20%", width: "140%", height: "140%" });
    blur.appendChild(el("feGaussianBlur", { stdDeviation: "3" }));   // ≈6px halo
    defs.appendChild(blur);
    const vig = el("radialGradient", { id: "map-vignette-grad", cx: "0.5", cy: "0.5", r: "0.72" });
    const v1 = el("stop", { offset: "0.62" }); v1.setAttribute("stop-color", "#000"); v1.setAttribute("stop-opacity", "0");
    const v2 = el("stop", { offset: "1" });    v2.setAttribute("stop-color", "#000"); v2.setAttribute("stop-opacity", "0.38");
    vig.appendChild(v1); vig.appendChild(v2);
    defs.appendChild(vig);
    const sym = el("symbol", { id: "map-building", viewBox: "0 0 24 24" });
    sym.appendChild(el("path", { d: "M12 3 L21 11 H18 V21 H6 V11 H3 Z", fill: "currentColor" }));
    defs.appendChild(sym);
    svg.appendChild(defs);

    // ── stage background (same rectangular instrument treatment) ──
    svg.appendChild(el("rect", { x: 0, y: 0, width: MAP_W, height: MAP_H, fill: "var(--page-bg, #06080f)" }));
    svg.appendChild(el("rect", { x: 0, y: 0, width: MAP_W, height: MAP_H, fill: "var(--surface, #0b0e17)" }));

    // ── holographic landmass: glow halo → fill → crisp coastline ──
    const d = worldPathD();
    svg.appendChild(el("path", { d, class: "map-coast-glow", filter: "url(#map-blur)" }));
    svg.appendChild(el("path", { d, class: "map-land-fill" }));
    svg.appendChild(el("path", { d, class: "map-coast" }));

    // ── subtle vignette (darker edges; hidden on the light theme via CSS) ──
    svg.appendChild(el("rect", {
      x: 0, y: 0, width: MAP_W, height: MAP_H,
      fill: "url(#map-vignette-grad)", class: "map-vignette", "pointer-events": "none"
    }));

    // ── pins: ONLY projects whose stored data has coordinates ──
    const located = LIN_PROJECTS.filter(hasCoords);
    const unlocated = LIN_PROJECTS.filter((p) => !hasCoords(p));

    if (!located.length) {
      const hint = el("text", {
        x: MAP_W / 2, y: MAP_H / 2, "text-anchor": "middle",
        class: "map-empty-hint"
      });
      hint.textContent = "Set project locations via Manage Projects → Edit info.";
      svg.appendChild(hint);
    }

    // project all pins, then fan any that land within 18px of each other
    // (glyphs fan horizontally ±12px; a thin leader ties each back to its
    // TRUE projected point, which keeps its small dot)
    const pts = located.map((p) => {
      const pos = mapProject(Number(p.lng), Number(p.lat));
      return { p, tx: pos.x, ty: pos.y, dx: 0 };
    });
    const clusters = [];
    pts.forEach((pt) => {
      const c = clusters.find((cl) => cl.some((m) => Math.hypot(m.tx - pt.tx, m.ty - pt.ty) < 18));
      if (c) c.push(pt); else clusters.push([pt]);
    });
    clusters.forEach((cl) => {
      if (cl.length < 2) return;
      cl.sort((a, b) => a.tx - b.tx);
      cl.forEach((pt, k) => { pt.dx = (k - (cl.length - 1) / 2) * 24; });   // pairs = ±12
    });

    pts.forEach(({ p, tx, ty, dx }) => {
      const status = statusKey(p);
      const color =
        status === "complete" ? STATUS_COLOR.complete :
        status === "green" ? STATUS_COLOR.green :
        status === "yellow" ? STATUS_COLOR.yellow :
        status === "amber" ? STATUS_COLOR.amber :
        status === "red"   ? STATUS_COLOR.red : "var(--muted)";
      const gx = tx + dx, gy = ty - 15;   // glyph sits above the true point

      const g = el("g", { class: "map-pin", "data-id": p.id,
        "aria-label": `${p.id} ${p.name}, ${stateLabel(p)}` });

      // leader from the glyph down to the exact projected point
      g.appendChild(el("line", { x1: tx, y1: ty, x2: gx, y2: gy + 11,
        class: "map-pin-leader" + (dx === 0 ? " map-pin-leader-short" : "") }));
      g.appendChild(el("circle", { cx: tx, cy: ty, r: 2.5, fill: color, class: "map-pin-dot" }));

      // one-shot selection pulse ring (CSS-driven)
      g.appendChild(el("circle", { cx: gx, cy: gy, r: 15, fill: "none", stroke: "var(--phosphor)",
        "stroke-width": "1.5", class: "map-pin-ring", opacity: "0" }));

      // the SAME building glyph as the radar blips
      const icon = el("use", {
        href: "#map-building", x: (gx - 11).toFixed(1), y: (gy - 11).toFixed(1),
        width: 22, height: 22, class: "map-pin-icon",
        opacity: status === "empty" ? "0.55" : "1"
      });
      icon.style.color = color;
      icon.style.filter = `drop-shadow(0 0 5px ${color})`;
      g.appendChild(icon);

      const lbl = el("text", { x: gx + 13, y: gy + 4, class: "blip-label" });
      lbl.textContent = p.id;
      g.appendChild(lbl);

      // hover tooltip: number · name · sector · status · address
      g.addEventListener("mouseenter", (e) => {
        const sec = { design: "Design", construction: "Construction", hybrid: "Hybrid", combined: "Hybrid" }[String(p.sector || "").toLowerCase()] || p.sector || "—";
        const addr = p.formattedAddress || p.address;   // prefer the geocoded form
        tt.innerHTML =
          `<div class="mt-num">${esc(p.id)}</div>` +
          `<div class="mt-name">${esc(p.name)}</div>` +
          `<div class="mt-sub">${esc(sec)} · ${esc(stateLabel(p))}</div>` +
          (addr ? `<div class="mt-addr">${esc(addr)}</div>` : "") +
          `<div class="mt-hint">double-click to open detail →</div>`;
        tt.style.display = "block"; moveTT(e);
      });
      g.addEventListener("mousemove", moveTT);
      g.addEventListener("mouseleave", hideTT);
      // click = select (list-row sync); double-click = open detail
      g.addEventListener("click", () => selectProject(p.id));
      g.addEventListener("dblclick", () => { hideTT(); openDetail(p.id); });

      svg.appendChild(g);
    });

    // ── "No address set" side note (each id opens its Edit info panel) ──
    const note = document.getElementById("map-nolocation");
    if (note) {
      if (unlocated.length) {
        note.hidden = false;
        note.innerHTML = "No address set: " + unlocated.map((p) =>
          `<button type="button" class="map-noloc-id" data-editloc="${esc(p.id)}">${esc(p.id)}</button>`).join(", ");
        note.querySelectorAll("[data-editloc]").forEach((b) =>
          b.addEventListener("click", () => {
            showPage("manage");
            const editBtn = document.querySelector(`#manage-root [data-editinfo="${b.dataset.editloc}"]`);
            if (editBtn) { editBtn.click(); editBtn.scrollIntoView({ block: "center" }); }
          }));
      } else {
        note.hidden = true;
        note.innerHTML = "";
      }
    }

    highlightPin();
  }

  /* Lazy map build: on first use, swap slim portfolio records for full
     project JSON (the slim list carries no coordinates) — one GET per
     project, once per session, only when the map view is actually opened. */
  async function buildMap() {
    const svg = $("#map-svg");
    if (!svg) return;
    if (!mapHydrated && window.LinStore && LinStore.getProject && LinStore.configured && LinStore.configured()) {
      mapHydrated = true;
      const slims = LIN_PROJECTS.filter((p) => p && p.slim);
      if (slims.length) {
        try {
          const fulls = await Promise.all(slims.map((p) => LinStore.getProject(p.id).catch(() => null)));
          fulls.forEach((f) => {
            if (f && !f.slim) {
              const i = LIN_PROJECTS.findIndex((x) => x.id === f.id);
              if (i >= 0) LIN_PROJECTS[i] = f;
            }
          });
        } catch (e) { /* pins simply won't render for records we couldn't hydrate */ }
      }
    }
    renderMap(svg);
    mapBuilt = true;
  }

  function highlightPin() {
    document.querySelectorAll(".map-pin").forEach((g) => {
      const on = g.getAttribute("data-id") === selectedId;
      const was = g.classList.contains("selected");
      g.classList.toggle("selected", on);
      if (on && !was) {
        // restart the one-shot pulse so re-selection pulses again
        const ring = g.querySelector(".map-pin-ring");
        if (ring) { ring.style.animation = "none"; void ring.getBoundingClientRect(); ring.style.animation = ""; }
      }
    });
  }

  /* ---------- Radar | Map view toggle (persisted; radar default) ---------- */
  function setPortfolioView(view, persist) {
    const isMap = view === "map";
    const radarWrap = document.querySelector(".radar-wrap");
    const mapWrap = document.querySelector(".map-wrap");
    const note = document.querySelector(".radar-note");
    if (radarWrap) radarWrap.hidden = isMap;
    if (note) note.hidden = isMap;              // radar caption; the map has its own
    if (mapWrap) mapWrap.hidden = !isMap;
    document.querySelectorAll(".stage-btn").forEach((b) =>
      b.classList.toggle("active", b.dataset.view === view));
    if (isMap) buildMap();                       // lazy init on first switch
    if (persist !== false) { try { localStorage.setItem(VIEW_KEY, view); } catch (e) {} }
  }
  function wireViewToggle() {
    document.querySelectorAll(".stage-btn").forEach((b) =>
      b.addEventListener("click", () => setPortfolioView(b.dataset.view)));
  }

  /* ---------- accessible fallback list ---------- */
  function buildFallbackList() {
    const ul = $("#project-list");
    ul.innerHTML = "";
    LIN_PROJECTS.forEach((p) => {
      try {
        const li = document.createElement("li");
        const btn = document.createElement("button");
        btn.className = "list-item";
        btn.setAttribute("data-id", p.id);
        const state = stateLabel(p);
        // Colour the status word to the 5-status palette, reusing the canonical
        // map (no second copy). "Awaiting ingest" rows have no normalized status
        // → no inline colour → they stay muted via their class. Slim records
        // carry a precomputed status string; full records derive it — either
        // way normalizeStatusLabel maps the label to a palette key.
        const hasStatus = (p && p.slim)
          ? (typeof slimStatusLabel === "function" && !!slimStatusLabel(p))
          : hasSignals(p);
        const norm = (hasStatus && typeof normalizeStatusLabel === "function")
          ? normalizeStatusLabel(state) : null;
        const col = (norm && typeof PCEIF_STATUS_HEX !== "undefined") ? PCEIF_STATUS_HEX[norm] : null;
        const stateStyle = col ? ` style="color:${col}"` : "";
        const simChip = "";
        btn.innerHTML =
          `<span class="li-code">${esc(p.id)}</span>` +
          `<span class="li-name">${esc(p.name)}</span>` +
          simChip +
          `<span class="li-state state-${esc(statusKey(p))}"${stateStyle}>${esc(state)}</span>` +
          `<button class="btn small li-open" data-open="${esc(p.id)}" title="Open project detail">Open →</button>`;
        btn.addEventListener("click", () => { selectProject(p.id); });
        btn.querySelector(".li-open").addEventListener("click", (e) => {
          e.stopPropagation();
          openDetail(p.id);
        });
        li.appendChild(btn);
        ul.appendChild(li);
      } catch (err) {
        // Keep the list resilient — render a minimal fallback row and log,
        // rather than dropping the project (or breaking the whole list).
        console.error("List render failed for project", p && p.id, "—", err && err.message);
        const li = document.createElement("li");
        const btn = document.createElement("button");
        btn.className = "list-item";
        btn.setAttribute("data-id", p && p.id || "");
        btn.innerHTML =
          `<span class="li-code">${esc(p && p.id || "?")}</span>` +
          `<span class="li-name">${esc(p && p.name || "(unrenderable)")}</span>`;
        if (p && p.id) btn.addEventListener("click", () => openDetail(p.id));
        li.appendChild(btn);
        ul.appendChild(li);
      }
    });
  }

  /* ---------- first-load skeleton + refreshing indicator ----------
     Cold load with no cache shows three shimmer rows; a cached load paints
     instantly and shows a subtle mono "refreshing…" next to the list heading
     while the slim list revalidates in the background. */
  function renderSkeleton() {
    const ul = $("#project-list");
    if (!ul) return;
    ul.innerHTML = "";
    for (let i = 0; i < 3; i++) {
      const li = document.createElement("li");
      li.className = "list-item skeleton-row";
      li.setAttribute("aria-hidden", "true");
      li.innerHTML =
        `<span class="sk sk-code"></span><span class="sk sk-name"></span><span class="sk sk-state"></span>`;
      ul.appendChild(li);
    }
  }
  function setListRefreshing(on) {
    const heading = $("#list-heading");
    if (!heading) return;
    let tag = document.getElementById("list-refreshing");
    if (on) {
      if (!tag) {
        tag = document.createElement("span");
        tag.id = "list-refreshing";
        tag.className = "list-refreshing";
        tag.textContent = "refreshing…";
        heading.appendChild(tag);
      }
    } else if (tag) {
      tag.remove();
    }
  }

  function highlightListItem() {
    document.querySelectorAll(".list-item").forEach((b) => {
      b.classList.toggle("active", b.getAttribute("data-id") === selectedId);
    });
  }

  /* ---------- signal ledger ---------- */
  // Human sector name for NA labels ("Design", "Construction", "Hybrid").
  function sectorName(p) {
    const s = window.normalizeSector ? normalizeSector(p && p.sector) : String(p && p.sector || "hybrid");
    return s.charAt(0).toUpperCase() + s.slice(1);
  }
  function statusPill(status, naSector) {
    if (!status) return `<span class="pill pill-none">No data</span>`;
    if (status === "NA") {
      const full = `N/A — not applicable to ${naSector || "this sector's"} projects`;
      return `<span class="pill pill-na" title="${esc(full)}">N/A</span>`;
    }
    const key = String(status).toLowerCase().replace("-review", "");
    const label = { green: "Green", amber: "Amber", red: "Red", yellow: "Yellow", complete: "Complete" }[key] || status;
    return `<span class="pill pill-${esc(key)}">${esc(label)}</span>`;
  }

  /* Summarize the fourteen client-side simulation models (PERT/LOB/CCPM/RCF/DSM + DST/RoughSets/Neutrosophic/IFS + Z/PLTS/Plithogenic/BRB/Quantum)
     for the Portfolio views. Returns null when none have run (graceful
     fallback — nothing is shown). */
  // Total active modules across all categories — the consistent denominator for the sim pill.
  // Computed once; falls back to 94 (the known active count) if categories aren't loaded yet.
  function activeModuleTotal() {
    if (window.LIN_CATEGORIES) {
      return window.LIN_CATEGORIES.reduce(function(n, c) {
        return n + (c.modules || []).filter(function(m) { return m.active !== false; }).length;
      }, 0);
    }
    return 94;
  }

  function simSummary(p) {
    const arr = p && p.simulationSignals && Array.isArray(p.simulationSignals.signal_array)
      ? p.simulationSignals.signal_array : null;
    if (!arr || !arr.length) return null;
    let red = 0, amber = 0, green = 0;
    arr.forEach((s) => {
      const c = String(s.status_color || "").toLowerCase();
      if (c === "red") red++; else if (c === "amber") amber++; else green++;
    });
    const worst = red ? "red" : amber ? "amber" : "green";
    // Use the active-module total so every project shows /N out of the same denominator
    // (not arr.length, which varied by which partial run last persisted).
    return { red, amber, green, total: activeModuleTotal(), worst, flagged: red + amber };
  }

  function awaitingHtml(p, what) {
    return `<div class="ledger-head"><div>
        <p class="eyebrow">${esc(what)}</p>
        <h2>${esc(p.id)}</h2><p class="ledger-sub">${esc(p.name)}</p>
      </div></div>
      <div class="awaiting-state">
        <p><strong>Awaiting ingest.</strong> This project has no signals yet.</p>
        <p class="kn-sub">Populate signals on the <em>Manage Projects</em> page (or the “Ingest” panel on this project) to run the Monte Carlo forecast, CUSUM monitor, document-risk extraction, and the PCEIF decision. Nothing is fabricated until real inputs are ingested.</p>
      </div>`;
  }

  function renderLedger(p, root = $("#ledger")) {
    if (!root) return;   // portfolio no longer hosts the ledger; only the detail page does
    if (!hasSignals(p)) { root.innerHTML = awaitingHtml(p, "Signal ledger"); return; }
    const s = p.signals;
    const conflict = classifyConflict(p);

    const rows = [
      {
        name: "EVM cost / schedule", method: "Earned Value Management",
        status: s.evm.status,
        metric: `CPI ${s.evm.cpi.toFixed(2)} · SPI ${s.evm.spi.toFixed(2)}`,
        detail: `Data date ${esc(s.evm.dataDate)}`
      },
      {
        name: "Probabilistic forecast", method: `Monte Carlo · ${s.mc.iterations.toLocaleString()} iter`,
        status: s.mc.status,
        metric: `P80 EAC +${s.mc.p80eacOverrunPct.toFixed(1)}% · P(delay) ${s.mc.pMilestoneDelay.toFixed(2)}`,
        detail: "Percentile exposure on cost and milestone finish"
      },
      {
        name: "Anomaly / trend", method: "SPC / CUSUM",
        status: s.cusum.status,
        metric: `${esc(s.cusum.metric)} drift ${s.cusum.drift.toFixed(1)} / ${s.cusum.threshold.toFixed(1)}`,
        detail: s.cusum.breached ? "Threshold breached" : "Within control limits"
      },
      {
        name: "Document risk", method: "Keyword / rule extraction",
        status: s.doc.status,
        metric: `Risk score ${s.doc.score.toFixed(2)}`,
        // s.doc.source and s.doc.excerpt come from extracted-document content,
        // i.e. attacker-controllable input. Escape BEFORE wrapping in markup
        // so the template literal itself remains static structural HTML.
        detail: `<span class="src">${esc(s.doc.source)}</span><span class="excerpt">“${esc(s.doc.excerpt)}”</span>`
      }
    ];

    const conflictClass =
      conflict === "Agreement — low risk" ? "conflict-calm" : "conflict-alert";

    root.innerHTML =
      `<div class="ledger-head">
         <div>
           <p class="eyebrow">Signal ledger</p>
           <h2>${esc(p.id)}</h2>
           <p class="ledger-sub">${esc(p.name)}</p>
         </div>
       </div>
       <div class="conflict-banner ${esc(conflictClass)}">
         <span class="conflict-label">Signal conflict</span>
         <span class="conflict-value">${esc(conflict)}</span>
       </div>
       <div class="signal-rows">` +
      categoryLedgerHtml(p) +
      `</div>`;
    wireCategoryLedger(root);
  }

  /* 9-category signal ledger. Each row = one category; the row pill is the
     worst-status-wins category status. Click expands the per-module list.
     Cat 9 (Governance) is open by default; Cat 8 (ML & AI) is parked and
     shows the Stage 2 placeholder instead of an expand control. */
  function categoryLedgerHtml(p) {
    if (!window.LIN_CATEGORIES) return "";
    return LIN_CATEGORIES.map((cat) => {
      const status = window.getCategoryStatus ? getCategoryStatus(cat.id, p) : null;
      const open = cat.id === "cat9" ? " open" : "";
      const desc = esc(cat.description);
      const rowPill = cat.parked ? `<span class="pill pill-parked">Stage 2</span>` : statusPill(status);

      if (cat.parked) {
        return `<div class="cat-row cat-row-parked" data-cat="${esc(cat.id)}">
          <div class="cat-row-head">
            <span class="cat-row-num" style="color:${esc(cat.color)}">${esc(cat.num)}</span>
            <span class="cat-row-name">${esc(cat.name)}</span>
            ${rowPill}
          </div>
          <p class="cat-row-desc">${desc}</p>
          <p class="cat-row-parked-note">ML & AI — available in Stage 2. Modules listed for reference: ${esc(cat.modules.map((m) => m.name).join(", "))}.</p>
        </div>`;
      }

      const secName = sectorName(p);
      const modRows = cat.modules.map((m) => {
        const st = window.getModuleStatus ? getModuleStatus(m.method_class, p) : null;
        const na = st === "NA";
        return `<div class="cat-mod-row${na ? " cat-mod-na" : ""}"${na ? ` title="N/A — not applicable to ${esc(secName)}-sector projects"` : ""}>
          <span class="cat-mod-num">${esc(m.num)}</span>
          <span class="cat-mod-name">${esc(m.name)}</span>
          ${statusPill(st, secName + "-sector")}
        </div>`;
      }).join("");
      // Sector-abstention note — the category stays; only its construction-phase
      // modules abstain for this sector.
      const naCount = (window.categoryNAModules ? categoryNAModules(cat.id, p) : []).length;
      const naNote = naCount
        ? `<p class="cat-row-na-note">Some modules are construction-phase only and are excluded for ${esc(secName)}-sector projects.</p>`
        : "";

      return `<details class="cat-row" data-cat="${esc(cat.id)}"${open}>
        <summary class="cat-row-head">
          <span class="cat-row-num" style="color:${esc(cat.color)}">${esc(cat.num)}</span>
          <span class="cat-row-name">${esc(cat.name)}</span>
          ${rowPill}
        </summary>
        <p class="cat-row-desc">${desc}</p>
        ${naNote}
        <div class="cat-mod-list">${modRows}</div>
      </details>`;
    }).join("");
  }

  function wireCategoryLedger(/* root */) { /* details/summary handles toggling natively */ }

  /* 6th ledger row — only when the simulation models have run for this project. */
  function simLedgerRow(p) {
    const sum = simSummary(p);
    if (!sum) return "";
    return `
        <div class="signal-row">
          <div class="sig-top">
            <span class="sig-name">Simulation signals</span>
            ${statusPill(sum.worst)}
          </div>
          <div class="sig-metric">${sum.red} Red · ${sum.amber} Amber · ${sum.green} Green</div>
          <div class="sig-meta"><span class="sig-method">PERT · LOB · CCPM · RCF · DSM · DST · Rough Sets · Neutrosophic · Interval Fuzzy · Z-numbers · PLTS · Plithogenic · BRB · Quantum</span></div>
          <div class="sig-detail">Worst status across the fourteen simulation modules.</div>
        </div>`;
  }

  /* ---------- decision card ----------
     Renders into any container (portfolio side panel or Project Detail),
     so all controls are class-scoped to the container — no duplicate ids. */
  /* Signal-traced action plan table — every row is a deterministic PCEIF rule
     traced to the exact category/module that triggered it (decision.js). */
  function actionPlanHtml(p) {
    if (typeof deriveActionPlan !== "function") return "";
    let rows = [];
    try { rows = deriveActionPlan(p) || []; } catch (e) { return ""; }
    if (!rows.length) return "";
    const hex = (typeof PCEIF_STATUS_HEX !== "undefined" && PCEIF_STATUS_HEX) || {};
    const body = rows.map((r) => {
      const c = hex[r.severity] || "#c8d4e8";
      return `<tr>
        <td class="ap-trigger" style="color:${esc(c)}">${esc(r.trigger)}</td>
        <td>${esc(r.what)}</td>
        <td>${esc(r.who)}</td>
        <td>${esc(r.how)}</td>
        <td>${esc(r.when)}</td>
        <td>${esc(r.inform)}</td>
      </tr>`;
    }).join("");
    return `<div class="dc-action-plan">
        <h3 class="ap-title">Signal-Traced Action Plan</h3>
        <div style="overflow-x:auto">
        <table class="ap-table">
          <thead><tr><th>Trigger</th><th>What</th><th>Who</th><th>How</th><th>When</th><th>Inform</th></tr></thead>
          <tbody>${body}</tbody>
        </table>
        </div>
        <p class="dc-note">Actions are deterministic PCEIF rules traced to signal categories — recommendation only; a named human reviewer records the decision.</p>
      </div>`;
  }

  function renderDecisionCard(p, root = $("#decision-card")) {
    if (!root) return;   // portfolio no longer hosts the decision card; only the detail page does
    if (!hasSignals(p)) { root.innerHTML = awaitingHtml(p, "PCEIF governance decision"); return; }
    const d = deriveDecision(p);
    const stateClass = d.healthState.toLowerCase().replace("-review", "");

    const fairnessBlock = d.fairnessGateRequired
      ? `<label class="fairness-gate">
           <input type="checkbox" class="fairness-check" />
           <span>Contractor response opportunity will be provided before any formal action.
           Required before this decision can be recorded.</span>
         </label>`
      : "";

    root.innerHTML =
      `<div class="dc-head">
         <div>
           <p class="eyebrow">PCEIF governance decision</p>
           <h2>Recommended action</h2>
         </div>
         <span class="state-badge state-${esc(stateClass)}">${esc(d.healthState)}</span>
       </div>
       <div class="dc-grid">
         <div class="dc-field"><span class="dc-label">Conflict</span><span class="dc-value">${esc(d.conflictType)}</span></div>
         <div class="dc-field"><span class="dc-label">Authority</span><span class="dc-value">${esc(d.authority)}</span></div>
         <div class="dc-field dc-wide"><span class="dc-label">Recommended action</span><span class="dc-value">${esc(d.action)}</span></div>
         <div class="dc-field dc-wide"><span class="dc-label">Documentation required</span><span class="dc-value">${esc(d.documentation)}</span></div>
       </div>
       <p class="dc-caveat">Recommended actions require named human approval before they are recorded; fairness gates require contractor response opportunity before any formal action.</p>
       ${actionPlanHtml(p)}
       ${fairnessBlock}
       <label class="rationale-label">Reviewer rationale <span class="req">(required, min 20 characters)</span>
       <textarea class="rationale" placeholder="State why this action is taken, deferred, or overridden. Recorded to the audit log."></textarea></label>
       <div class="dc-actions">
         <button class="btn primary record-btn" disabled>Record decision</button>
         <button class="btn export-btn">Export audit JSON</button>
         <button class="btn export-xlsx-btn">Export Report (XLSX)</button>
       </div>
       <p class="dc-note">Recommendation only — a named human reviewer records the decision. The recommendation does not trigger any action on its own.</p>`;

    wireDecisionControls(p, d, root);
  }

  function wireDecisionControls(p, d, root) {
    const rationale = $(".rationale", root);
    const recordBtn = $(".record-btn", root);
    const fairnessCheck = $(".fairness-check", root); // may be null

    const evaluate = () => {
      const longEnough = rationale.value.trim().length >= 20;
      const fairnessOk = !d.fairnessGateRequired || (fairnessCheck && fairnessCheck.checked);
      recordBtn.disabled = !(longEnough && fairnessOk);
    };

    rationale.addEventListener("input", evaluate);
    if (fairnessCheck) fairnessCheck.addEventListener("change", evaluate);

    recordBtn.addEventListener("click", () => {
      const entry = {
        project: p.id,
        state: d.healthState,
        action: d.action,
        rationale: rationale.value.trim(),
        fairnessAcknowledged: d.fairnessGateRequired ? fairnessCheck.checked : null,
        recordedAt: new Date().toISOString()
      };
      decisionLog.unshift(entry);
      renderDecisionLog();
      rationale.value = "";
      if (fairnessCheck) fairnessCheck.checked = false;
      evaluate();
    });

    $(".export-btn", root).addEventListener("click", () => {
      const reviewerInput = {
        rationale: rationale.value.trim() || "(not recorded at export time)",
        fairnessAcknowledged: fairnessCheck ? fairnessCheck.checked : null,
        recordedAt: new Date().toISOString()
      };
      const record = buildAuditRecord(p, d, reviewerInput);
      // Display timestamps in the selected timezone; the record's
      // exported_at / recorded_at stay UTC ISO for integrity.
      record.exported_at_local = LinTZ.format(record.exported_at);
      record.timezone = LinTZ.get();
      const blob = new Blob([JSON.stringify(record, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `audit_${p.id}_${p.reportingPeriod}.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    });

    const xlsxBtn = $(".export-xlsx-btn", root);
    if (xlsxBtn) xlsxBtn.addEventListener("click", () => {
      try {
        if (window.LinExport && typeof LinExport.exportProjectReport === "function") {
          LinExport.exportProjectReport(p);
        } else {
          alert("XLSX export not available — the SheetJS library failed to load.");
        }
      } catch (e) {
        console.error("[xlsx] export failed:", e);
        alert("XLSX export failed: " + (e && e.message ? e.message : "unknown error"));
      }
    });
  }

  function renderDecisionLog() {
    const wrap = $("#decision-log");
    if (!wrap) return;   // decision log lives off the portfolio page now
    if (!decisionLog.length) {
      wrap.innerHTML = `<p class="log-empty">No decisions recorded this session.</p>`;
      return;
    }
    wrap.innerHTML =
      `<p class="eyebrow">Decision log (this session)</p>` +
      decisionLog.map((e) => `
        <div class="log-entry">
          <div class="log-top"><span class="log-proj">${esc(e.project)}</span><span class="log-state state-${esc(e.state.toLowerCase().replace("-review",""))}">${esc(e.state)}</span></div>
          <div class="log-action">${esc(e.action)}</div>
          <div class="log-rationale">“${esc(e.rationale)}”</div>
          <div class="log-time">${esc(LinTZ.format(e.recordedAt))}${e.fairnessAcknowledged ? " · fairness gate acknowledged" : ""}</div>
        </div>`).join("");
  }

  /* ---------- selection orchestration ---------- */
  function selectProject(id) {
    // Portfolio is radar + list only — selection just updates highlights now.
    // The signal ledger + PCEIF decision are rendered on the Project Detail page
    // (detail.js calls LinApp.renderLedger / renderDecisionCard into its panels).
    selectedId = id;
    const p = LIN_PROJECTS.find((x) => x.id === id);
    if (!p) return;
    highlightBlip();
    highlightListItem();
  }

  /* Drill-down: clicking a blip or list row opens Project Detail.
     Switch to the detail page FIRST (showPage renders the detail content from
     selectedId) so a render error downstream can never block navigation; the
     portfolio side-ledger update via selectProject is non-blocking.

     Under the slim-list model the cached record has no signals/simulation
     arrays, so the full project JSON is fetched here (once) and swapped into the
     in-memory mirror before re-rendering the detail page. The page shows its
     awaiting/loading state from the slim record first, then re-renders with the
     full data — no blocking spinner. */
  function openDetail(id) {
    selectedId = id;
    showPage("detail");
    try { selectProject(id); } catch (e) { /* side-ledger is non-critical to navigation */ }
    hydrateFullProject(id);
  }

  async function hydrateFullProject(id) {
    const cached = window.LinStore ? LinStore.getCached(id) : null;
    // Only fetch when the cached record is a slim stub (no signals + slim flag).
    if (!cached || !cached.slim) return;
    try {
      const full = await LinStore.getProject(id);
      if (!full || full.slim) return;                 // nothing better to show
      const i = LIN_PROJECTS.findIndex((x) => x.id === id);
      if (i >= 0) LIN_PROJECTS[i] = full;
      else {
        const ai = LIN_ARCHIVED.findIndex((x) => x.id === id);
        if (ai >= 0) LIN_ARCHIVED[ai] = full;
      }
      // Re-render the detail page (if still the open project) with full data.
      if (selectedId === id && window.LinDetail && typeof LinDetail.render === "function") {
        LinDetail.render(id);
      }
    } catch (e) { console.warn("[detail] full-project hydrate failed for", id, "—", e && e.message); }
  }

  /* ---------- theme switch ---------- */
  function applyTheme(theme) {
    document.body.dataset.theme = theme;
    document.querySelectorAll("[data-set-theme]").forEach((b) =>
      b.classList.toggle("active", b.dataset.setTheme === theme)
    );
    try {
      localStorage.setItem("lin-theme", theme);        // new primary key
      localStorage.setItem("lin-radar-theme", theme);  // legacy key (kept for back-compat)
    } catch (e) {}
  }

  /* ---------- clock (timezone-aware via tz.js) ---------- */
  function startClock() {
    const node = $("#tz-clock");
    const tick = () => { node.textContent = LinTZ.clock(); };
    tick();
    setInterval(tick, 1000);
    document.addEventListener("lin:tz-changed", () => { tick(); renderDecisionLog(); });
  }

  function wireTzSelect() {
    const sel = $("#tz-select");
    if (!sel) return;
    sel.innerHTML = LinTZ.zones.map((z) =>
      `<option value="${esc(z.id)}"${z.id === LinTZ.get() ? " selected" : ""}>${esc(z.label)}</option>`).join("");
    sel.addEventListener("change", () => LinTZ.set(sel.value));
  }

  /* ---------- page navigation ---------- */
  function showPage(page) {
    document.querySelectorAll(".page").forEach((s) =>
      s.toggleAttribute("hidden", s.dataset.page !== page));
    document.querySelectorAll("[data-nav]").forEach((b) =>
      b.classList.toggle("active", b.dataset.nav === page));
    // (re)render content pages so they reflect the latest portfolio state.
    // Guarded so a single page-render error can never leave navigation half-done.
    try {
      if (page === "modules" && window.LinModules) LinModules.renderModulesPage();
      if (page === "knowledge" && window.LinKnowledge) LinKnowledge.renderKnowledgePage();
      if (page === "manage" && window.LinIngest) LinIngest.renderManagePage();
      if (page === "auditor" && window.LinAuditor) LinAuditor.renderAuditorPage();
      if (page === "detail" && window.LinDetail && selectedId) LinDetail.render(selectedId);
    } catch (e) { /* page is already visible; a render hiccup must not block nav */ }
    window.scrollTo({ top: 0 });
  }

  function wireNav() {
    document.querySelectorAll("[data-nav]").forEach((b) =>
      b.addEventListener("click", () => {
        showPage(b.dataset.nav);
        // click-toggle nav: choosing an item always closes the rail
        setNavOpen(false);
      }));
  }

  /* ---------- click-toggle nav rail (no hover behavior, all viewports) ---------- */
  function setNavOpen(open) {
    document.body.classList.toggle("nav-open", open);
    const t = $("#nav-toggle");
    if (t) {
      t.setAttribute("aria-expanded", String(open));
      t.setAttribute("aria-label", open ? "Close navigation menu" : "Open navigation menu");
    }
    // keep the floating cluster's menu button in sync with the header one
    const f = $(".float-menu");
    if (f) f.setAttribute("aria-expanded", String(open));
  }

  /* ---------- floating nav cluster ----------
     Past ~120px of scroll the header (and its hamburger) is gone, so a fixed
     top-right cluster fades in: a 44px animated logo emblem (click = smooth
     scroll to top) + a hamburger that drives the SAME setNavOpen() menu as
     the header button. Fades back out at the top. The radar-sweep rotation
     is CSS-only and disabled under prefers-reduced-motion (glow stays). */
  function initFloatingNav() {
    if (document.getElementById("float-nav")) return;
    const el = document.createElement("div");
    el.id = "float-nav";
    el.className = "float-nav";
    el.innerHTML =
      '<button type="button" class="float-logo" title="Back to top" aria-label="Scroll back to top">' +
        '<img src="logo.png" alt="" />' +
        '<span class="float-logo-sweep" aria-hidden="true"></span>' +
      '</button>' +
      '<button type="button" class="float-menu" aria-label="Open navigation menu" aria-expanded="false">' +
        '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h18M3 12h18M3 18h18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>' +
      '</button>';
    document.body.appendChild(el);
    el.querySelector(".float-logo").addEventListener("click", () =>
      window.scrollTo({ top: 0, behavior: reduceMotion() ? "auto" : "smooth" }));
    el.querySelector(".float-menu").addEventListener("click", (e) => {
      e.stopPropagation(); // don't let the document outside-click handler re-close it
      setNavOpen(!document.body.classList.contains("nav-open"));
    });
    const onScroll = () => {
      // visibility (not display) so the fade transition runs and hidden
      // buttons drop out of the tab order / accessibility tree
      el.classList.toggle("visible", window.scrollY > 120);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  function wireNavReveal() {
    const rail = $("#nav-rail");
    const toggle = $("#nav-toggle");
    if (toggle) toggle.addEventListener("click", (e) => {
      e.stopPropagation();
      setNavOpen(!document.body.classList.contains("nav-open"));
    });
    // outside-click closes the rail (any click not inside the rail or on the toggle)
    document.addEventListener("click", (e) => {
      if (!document.body.classList.contains("nav-open")) return;
      if (rail && rail.contains(e.target)) return;
      if (toggle && toggle.contains(e.target)) return;
      setNavOpen(false);
    });
    // Escape closes the overlay
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") setNavOpen(false); });
  }

  /* ---------- "Recompute all signals" button ----------
     Runs the full 94-module set for every ingested project from stored
     signalInputs — no document re-upload, no extraction API calls.
     Network: only GET (?action=get) and save (?action=save). */
  (function wireRecomputeAll() {
    const btn    = document.getElementById("recompute-all-btn");
    const status = document.getElementById("recompute-all-status");
    if (!btn || !status) return;
    btn.addEventListener("click", async function () {
      if (!window.LinSignals || !window.LinStore) return;
      const projects = (LinStore.cachedActive ? LinStore.cachedActive() : []);
      if (!projects.length) { status.textContent = "No ingested projects found."; return; }
      btn.disabled = true;
      let done = 0;
      for (const p of projects) {
        status.textContent = "Recomputing " + (done + 1) + " / " + projects.length + "…";
        try {
          const full = await LinStore.getProject(p.id);
          if (!full || !full.signalInputs) { done++; continue; }
          const si = LinSignals.deriveExtendedFields(LinSignals.resolveSimInputs(full));
          const hasCpi = si.cpi != null && Number.isFinite(Number(si.cpi)) && Number(si.cpi) > 0;
          const hasSpi = si.spi != null && Number.isFinite(Number(si.spi)) && Number(si.spi) > 0;
          if (!hasCpi && !hasSpi) { done++; continue; }
          await LinSignals.runModels(full, si);
        } catch (e) {
          console.warn("[recompute-all] project " + p.id + ":", e && e.message);
        }
        done++;
      }
      status.textContent = "Done — recomputed " + done + " project" + (done === 1 ? "" : "s") + ".";
      btn.disabled = false;
      // Refresh the slim portfolio cache so the radar/list reflect the newly
      // computed statuses (and the cache isn't stale on the next cold load).
      if (window.LinApp) LinApp.refreshPortfolio();
    });
  })();

  /* ---------- public API (used by ingest.js) ---------- */
  window.LinApp = {
    refresh() {
      buildRadar(); buildFallbackList();
      if (mapBuilt) buildMap();   // keep the map view in sync once initialized
      // if the selected project was archived, fall back to the first active one
      if (selectedId && !LIN_PROJECTS.some((p) => p.id === selectedId) && LIN_PROJECTS.length) {
        selectProject(LIN_PROJECTS[0].id);
      }
    },
    // Re-fetch the slim portfolio list, refresh its cache, and re-render. Called
    // after mutations that change the portfolio (recompute-all, archive/restore,
    // create, rename) so the radar/list + cache reflect the new server state.
    async refreshPortfolio() {
      setListRefreshing(true);
      try {
        if (LinStore.loadSlim) await LinStore.loadSlim();
        else await LinStore.load();
      } catch (e) { /* store shows its own banner */ }
      setListRefreshing(false);
      this.refresh();
    },
    selectProject(id) { showPage("portfolio"); selectProject(id); },
    openDetail,
    showPage,
    getSelectedId() { return selectedId; },
    // Re-key the cached selection after a project-number change (setprojectnumber)
    // so the detail page / highlights keep pointing at the renamed project.
    renameSelection(oldId, newId) { if (selectedId === oldId) selectedId = newId; },
    // called by auth.js after a successful sign-in
    init,
    // shared renderers, reused by the Project Detail page (detail.js)
    renderLedger,
    renderDecisionCard
  };

  /* ---------- shared collapsible section (Project Detail + Signals page) ----------
     Open/closed state persists per section id in sessionStorage so toggles
     survive in-page navigation within a session; a fresh session returns to
     the declared defaults. Opening a section dispatches `lin:section-opened`
     so heavy visuals can lazy-render on first expand instead of page load. */
  var SECTION_STATE_PREFIX = "lin-sec-";
  function readSectionState(id) {
    try { return sessionStorage.getItem(SECTION_STATE_PREFIX + id); } catch (e) { return null; }
  }
  function writeSectionState(id, open) {
    try { sessionStorage.setItem(SECTION_STATE_PREFIX + id, open ? "1" : "0"); } catch (e) {}
  }
  window.toggleSection = function (id) {
    var body = document.getElementById("body-" + id);
    var arrow = document.getElementById("arrow-" + id);
    var section = document.getElementById("section-" + id);
    if (!body) return;
    if (body.style.display === "none") {
      body.style.display = "block";
      if (arrow) arrow.textContent = "▲";
      if (section) section.classList.add("open");
      writeSectionState(id, true);
      try { document.dispatchEvent(new CustomEvent("lin:section-opened", { detail: { id: id } })); } catch (e) {}
    } else {
      body.style.display = "none";
      if (arrow) arrow.textContent = "▼";
      if (section) section.classList.remove("open");
      writeSectionState(id, false);
    }
  };
  window.collapsibleSection = function (id, title, content, defaultOpen, badgeHtml) {
    var stored = readSectionState(id);
    if (stored != null) defaultOpen = stored === "1";
    var openCls = defaultOpen ? " open" : "";
    var toggle = "toggleSection('" + id + "')";
    return '<div class="collapse-section' + openCls + '" id="section-' + id + '">' +
      '<div class="collapse-header" role="button" tabindex="0" onclick="' + toggle + '" ' +
        'onkeydown="if(event.key===\'Enter\'||event.key===\' \'){event.preventDefault();' + toggle + ';}">' +
        '<span class="collapse-title">' + title + '</span>' +
        (badgeHtml ? '<span class="collapse-badge">' + badgeHtml + '</span>' : '') +
        '<span class="collapse-arrow" id="arrow-' + id + '">' + (defaultOpen ? '▲' : '▼') + '</span>' +
      '</div>' +
      '<div class="collapse-body" id="body-' + id + '" style="' + (defaultOpen ? '' : 'display:none') + '">' +
        content +
      '</div>' +
    '</div>';
  };

  /* ---------- Portfolio AI executive summary ---------- */
  const PORTFOLIO_SUMMARY_KEY = "lin-portfolio-summary";

  function summarisableProjects() {
    return (window.LIN_PROJECTS || []).filter((p) => p && p.id);
  }

  function renderPortfolioSummary(text, projectCount, when) {
    const el = document.getElementById("portfolio-summary-text");
    if (!el) return;
    const sections = String(text || "").split(/\n\n+/);
    const html = sections.map((section) => {
      const lines = section.trim().split("\n");
      const header = (lines[0] || "").replace(/\*\*/g, "").replace(/^#+\s*/, "").trim();
      const isHeader = /^(PROJECT STATUS AT A GLANCE|PORTFOLIO[- ]LEVEL RECOMMENDATIONS|OVERALL PORTFOLIO HEALTH)/i.test(header);
      if (isHeader) {
        const bodyLines = lines.slice(1).map((line) => {
          line = line.trim();
          if (!line) return "";
          if (/^[•\-*]/.test(line)) return "<li>" + esc(line.replace(/^[•\-*]\s*/, "")) + "</li>";
          return '<p class="brief-line">' + esc(line) + "</p>";
        });
        const hasLi = bodyLines.some((l) => l.indexOf("<li>") === 0);
        const bodyHtml = hasLi ? '<ul class="brief-list">' + bodyLines.join("") + "</ul>" : bodyLines.join("");
        return '<div class="brief-section"><div class="brief-section-header">' + esc(header) + "</div>" + bodyHtml + "</div>";
      }
      return '<p class="brief-line">' + esc(section.trim()) + "</p>";
    }).join("");
    el.innerHTML = html;
    const foot = document.getElementById("portfolio-summary-foot");
    if (foot) {
      let dateStr = "";
      try { dateStr = new Date(when || Date.now()).toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric" }); } catch (e) {}
      foot.textContent = "Generated from " + projectCount + " projects · " + dateStr + (when ? " · cached" : "");
    }
  }

  function generatePortfolioSummary() {
    const projects = summarisableProjects();
    const el = document.getElementById("portfolio-summary-text");
    if (!el) return;
    if (projects.length < 1) {
      el.innerHTML = '<div class="brief-loading">Add at least 1 project to generate a portfolio summary.</div>';
      return;
    }
    if (!window.LinStore || typeof LinStore.chat !== "function") {
      el.innerHTML = '<span style="color:var(--faint)">Summary unavailable — chat endpoint not configured.</span>';
      return;
    }
    const projectLines = projects.map((p) => {
      const s = p.signals || {};
      const state = (s.decision && s.decision.state) || p.status || "unknown";
      const si = p.signalInputs || {};
      const cpi = Number(si.cpi), spi = Number(si.spi);
      return p.id + " " + p.name + " (" + (p.sector || "unknown") + "): state=" + state +
        (Number.isFinite(cpi) ? ", cost performance " + (cpi >= 0.95 ? "on budget" : cpi >= 0.90 ? "slightly over" : "over budget") : "") +
        (Number.isFinite(spi) ? ", schedule " + (spi >= 0.95 ? "on track" : spi >= 0.90 ? "slightly behind" : "behind") : "");
    }).join("\n");
    const redCount = projects.filter((p) => p.signals && p.signals.decision && String(p.signals.decision.state || "").indexOf("Red") >= 0).length;
    const amberCount = projects.filter((p) => p.signals && p.signals.decision && p.signals.decision.state === "Amber").length;

    const prompt = "You are a senior program controls advisor writing a portfolio-level executive summary for a program director." +
      "\n\nPortfolio: " + projects.length + " active projects. " + redCount + " in red-review, " + amberCount + " amber, " +
      (projects.length - redCount - amberCount) + " green or better." +
      "\n\nProject signals:\n" + projectLines +
      "\n\nWrite a portfolio executive summary with exactly three sections:\n\n" +
      "PROJECT STATUS AT A GLANCE\n" +
      "One bullet per project. One sentence each. Plain English. No metric values. No module numbers. " +
      'Format: "Project [ID] — [Name]: [one sentence]"\n\n' +
      "PORTFOLIO-LEVEL RECOMMENDATIONS\n" +
      "3-5 bullet points. Advisory tone — suggest, recommend, consider. Portfolio-level observations only, not project-specific actions. Look for patterns across projects.\n\n" +
      "OVERALL PORTFOLIO HEALTH\n" +
      "One sentence. Diplomatic. Evidence-based.\n\n" +
      "Rules:\n- Never say 'you must' or issue commands.\n" +
      "- Use phrasing like 'the evidence suggests', 'it may be worth considering', 'the data indicates'.\n" +
      "- Match urgency to the actual signal state.\n" +
      "- One line per project only in the status section.\n" +
      "- Start each section with the exact header text shown above (no numbering, no markdown).";

    el.innerHTML = '<div class="brief-loading">Analysing ' + projects.length + " projects…</div>";
    LinStore.chat(prompt, undefined, { max_tokens: 1000 }).then((answer) => {
      const text = String(answer || "").trim();
      if (!text) throw new Error("empty summary");
      renderPortfolioSummary(text, projects.length, null);
      try {
        localStorage.setItem(PORTFOLIO_SUMMARY_KEY, JSON.stringify({
          text: text, generated_at: new Date().toISOString(), project_count: projects.length
        }));
      } catch (e) { /* non-fatal */ }
    }).catch((err) => {
      console.error("[portfolio-summary] chat failed:", err);
      el.innerHTML = '<span style="color:var(--faint)">Summary unavailable — check connection, then press Generate.</span>';
    });
  }

  function initPortfolioSummary() {
    const el = document.getElementById("portfolio-summary-text");
    if (!el) return;
    const btn = document.getElementById("portfolio-summary-generate");
    if (btn && !btn.dataset.wired) {
      btn.dataset.wired = "1";
      btn.addEventListener("click", generatePortfolioSummary);
    }
    let cached = null;
    try { cached = JSON.parse(localStorage.getItem(PORTFOLIO_SUMMARY_KEY) || "null"); } catch (e) {}
    if (cached && cached.text) {
      renderPortfolioSummary(cached.text, cached.project_count || summarisableProjects().length, cached.generated_at);
    } else if (summarisableProjects().length >= 2) {
      generatePortfolioSummary();
    } else {
      el.innerHTML = '<div class="brief-loading">Populate at least 2 projects with signals to generate a portfolio summary.</div>';
    }
  }

  /* ---------- init ---------- */
  async function init() {
    document.querySelectorAll("[data-set-theme]").forEach((b) =>
      b.addEventListener("click", () => applyTheme(b.dataset.setTheme))
    );
    // Three themes — Light / Dark / New York; Dark default. Read both the new
    // `lin-theme` key and the legacy `lin-radar-theme` key for backwards
    // compatibility; the old "clean" name maps to Light; the removed
    // "cyberpunk" theme falls back to Dark.
    let stored = "dark";
    try {
      stored = localStorage.getItem("lin-theme")
            || localStorage.getItem("lin-radar-theme")
            || "dark";
    } catch (e) {}
    if (stored === "clean") stored = "light";
    if (stored === "cyberpunk") stored = "dark";   // theme removed
    const VALID_THEMES = ["light", "dark", "newyork"];
    const saved = VALID_THEMES.includes(stored) ? stored : "dark";
    applyTheme(saved);

    wireNav();
    wireNavReveal();
    initFloatingNav();
    wireTzSelect();
    startClock();
    // Show the signed-in user's email in the top bar (auth.js / Stage 1).
    try {
      const emailEl = document.getElementById("auth-email-display");
      if (emailEl && window.LinAuth && LinAuth.getEmail) emailEl.textContent = LinAuth.getEmail() || "";
    } catch (e) { /* non-fatal */ }
    showPage("portfolio");
    renderDecisionLog();

    // Portfolio load — stale-while-revalidate against the slim list (v10.28).
    // (1) Paint instantly from the slim portfolio cache if present (else show a
    //     skeleton); (2) fetch listslim in the background, re-render, and update
    //     the cache. Full project JSON is fetched lazily only on detail open.
    let paintedFromCache = false;
    try {
      const cached = LinStore.readPortfolioCache && LinStore.readPortfolioCache();
      if (cached && cached.length) {
        LinStore.hydratePortfolio(cached);
        buildRadar();
        buildFallbackList();
        if (LIN_PROJECTS.length) selectProject(LIN_PROJECTS[0].id);
        setListRefreshing(true);
        paintedFromCache = true;
      } else {
        renderSkeleton();
      }
    } catch (e) { /* first paint is best-effort */ }

    // Background revalidate from the slim endpoint (falls back to full list on 404).
    try {
      if (LinStore.loadSlim) await LinStore.loadSlim();
      else await LinStore.load();
    } catch (e) { /* store shows its own banner */ }
    setListRefreshing(false);

    buildRadar();
    buildFallbackList();

    // Radar | Map toggle — radar default; a persisted "map" choice restores
    // (and lazily builds the map now that the portfolio is hydrated).
    wireViewToggle();
    let savedView = "radar";
    try { savedView = localStorage.getItem(VIEW_KEY) || "radar"; } catch (e) {}
    if (savedView === "map") setPortfolioView("map", false);

    // default selection: first project in the portfolio (may be empty →
    // shows the awaiting-ingest state, not a fabricated status).
    if (LIN_PROJECTS.length && (!selectedId || !LIN_PROJECTS.some((p) => p.id === selectedId))) {
      selectProject(LIN_PROJECTS[0].id);
    }

    // rebuild radar geometry on resize-driven motion-pref changes
    window.matchMedia("(prefers-reduced-motion: reduce)").addEventListener?.("change", buildRadar);
    // rebuild when the panel crosses the wide↔narrow stage breakpoint so the
    // side columns restack (debounced; cheap no-op when the mode is unchanged)
    let lastNarrow = null, resizeTimer = null;
    const checkStageMode = () => {
      const wrap = document.querySelector(".radar-wrap");
      const w = (wrap && wrap.clientWidth) || window.innerWidth;
      const narrow = w < 800;
      if (lastNarrow === null) { lastNarrow = narrow; return; }
      if (narrow !== lastNarrow) { lastNarrow = narrow; buildRadar(); }
    };
    checkStageMode();
    window.addEventListener("resize", () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(checkStageMode, 200);
    }, { passive: true });
  }

  // Auth gate (Stage 1): only initialise the app for an authenticated,
  // authorized user. LinAuth.init() shows the login screen and returns false
  // when sign-in is required; after a successful sign-in it calls LinApp.init().
  // When the auth layer is absent the app runs unguarded so it is never bricked.
  function boot() {
    if (window.LinAuth && typeof LinAuth.init === "function") {
      if (LinAuth.init()) init();
    } else {
      const appEl = document.getElementById("lin-app");
      if (appEl) appEl.style.display = "block";
      init();
    }
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
