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

  // Radar blips and map pins are GRAPHICS: they point at the --status-* fills
  // (not the darkened -text variants) and re-theme live via var(). The palette
  // itself lives in radar.css — never hardcode a status hex here.
  const STATUS_COLOR = {
    complete: "var(--status-complete)",
    green: "var(--status-green)",
    yellow: "var(--status-yellow)",
    amber: "var(--status-amber)",
    red:   "var(--status-red)"
  };

  const SVG_NS = "http://www.w3.org/2000/svg";
  // Rectangular stage: the SVG spans the full panel width with a wide viewBox
  // (1200×460); the circular scope is centered and the side columns (status
  // legend / ring thresholds) absorb the flexible width. Below ~800px panel
  // width buildRadar() switches to a narrow stacked viewBox (460×680).
  // The scope center is therefore mutable — set per build, read by polar().
  //
  // SCOPE_H is the vertical band the circle owns inside the stage. On the wide
  // stage that IS the viewBox height (460). On the narrow stage the viewBox is
  // 680 tall but the circle only owns the top 460 of it — the side columns
  // stack beneath at y = VH-190 — so the band, not VH, is what the radius must
  // derive from (44% of 680 would put the circle through the top edge and into
  // the stacked columns). Both bands are 460, so the scope is the same size in
  // either mode and only CENTER_X moves.
  const SCOPE_H = 460;
  // Outer radius = 44% of the band → ~6% breathing room above and below.
  // EVERYTHING radial derives from R_MAX; nothing below should hardcode a radius.
  const R_MAX = 0.44 * SCOPE_H;      // 202.4 — outer radius (health 0)
  const R_MIN = R_MAX * (8 / 92);    // 17.6  — inner radius (health 100), original ratio kept
  const ICON = 16;                   // blip glyph size in SVG user units (drives separation + rings)
  let CENTER_X = 600;                // wide stage scope center; 230 when narrow
  const CENTER_Y = SCOPE_H / 2;      // 230 — circle always centered in its band

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

  /* ---------- color-blind-safe status shape badge ----------
     The radar blip icon is deliberately ONE uniform glyph (see the
     #blip-building comment below) — status is colour-only on the icon
     itself, and at ICON=16 SVG units it's too small to hold a legible
     letter. So the redundant non-color cue here is a small distinct SHAPE
     badge (ring/circle/triangle/diamond/square, from linStatusShape()) drawn
     at the icon's top-right corner, filled with the same status colour. */
  function shapeBadge(shape, cx, cy, r, fill) {
    if (shape === "circle") return el("circle", { cx, cy, r, fill });
    if (shape === "square") return el("rect", { x: cx - r, y: cy - r, width: r * 2, height: r * 2, fill });
    if (shape === "triangle") {
      const p = `${cx},${cy - r} ${cx - r},${cy + r} ${cx + r},${cy + r}`;
      return el("polygon", { points: p, fill });
    }
    if (shape === "diamond") {
      const p = `${cx},${cy - r} ${cx + r},${cy} ${cx},${cy + r} ${cx - r},${cy}`;
      return el("polygon", { points: p, fill });
    }
    // ring — hollow circle, for Complete
    return el("circle", { cx, cy, r: r * 0.72, fill: "none", stroke: fill, "stroke-width": Math.max(1, r * 0.5) });
  }

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
  // deterministic per-project blink offset (0–1.68s) so map pins don't strobe
  // in unison — numeric ids use their value, others fall back to a char sum
  function mapPinBlinkDelay(id) {
    const s = String(id == null ? "" : id);
    const n = parseInt(s.replace(/\D/g, ""), 10);
    const h = Number.isFinite(n) ? n : s.split("").reduce((a, c) => a + c.charCodeAt(0), 0);
    return (h % 7) * 0.28;
  }

  /* T13. THE ROOT OF THE hasSignals FAMILY, and the one the T12 fix went around rather than
     through. It used to ask hasSignals(p) — the legacy client-side p.signals blob — and return
     "empty" when that was absent, which is wrong for every project the server has analysed.

     This drives EIGHT call sites, and they are not cosmetic: proxyHealth() places the project's
     radar blip by it (an analysed project sat on the neutral mid-ring rather than its real band),
     statusColorFor() colours markers by it, and the project list row takes its state- CSS class
     from it. The T12 legend fix added a separate storedStatusKey() helper beside this one instead
     of correcting it, so the legend read correctly while everything else kept reading "empty".
     That duplicate is gone; the legend calls this.

     Found by tests_render.html, which is the whole reason that harness exists: in a page without
     store.js the unqualified hasSignals reference threw a ReferenceError, the list row silently
     fell back to its minimal catch-block form, and the assertion went red. */
  function statusKey(p) {
    if (p && p.slim) {
      const lab = (typeof slimStatusLabel === "function") ? slimStatusLabel(p) : null;
      return lab ? lab.toLowerCase().replace("-review", "") : "empty";
    }
    if (!(window.LinResults && LinResults.hasResult(p))) return "empty";
    return String(deriveHealthState(p)).toLowerCase().replace("-review", "");
  }
  /* ---------- the shared status key ----------
     T12. Rendered for ALL THREE stages. It used to be drawn inside the radar's own SVG, so
     switching to Map or Globe lost the key while those views went on colouring markers by exactly
     the same statuses.

     IT COUNTS FROM THE STORED ROW, which is the fault that made it read zero. The old legend went
     through statusKey(), and statusKey() asks hasSignals() FIRST:

         if (!hasSignals(p)) return "empty";

     hasSignals() tests for the legacy client-side p.signals.evm/cusum/mc/doc blob. A project that
     has been analysed server-side and carries a stored computed_results row does not necessarily
     carry that blob, so every such project fell into "empty" and the five real bands all read 0.
     deriveHealthState() was already reading the stored row correctly through getProjectFusion; it
     simply never got asked. This reads getProjectFusion() directly, which is the same source
     atlas.js and globe.js colour their markers from, so the key and the markers cannot disagree.

     "AWAITING ANALYSIS" is the wording the rest of the platform uses for a project with no stored
     result, and it is what deriveHealthState() returns. The legend said "Awaiting", and stateLabel
     still said the retired "Awaiting ingest". Both now match what the views render. */

  const LEGEND_BANDS = [
    ["Complete", "complete", "--status-complete"],
    ["Green",    "green",    "--status-green"],
    ["Yellow",   "yellow",   "--status-yellow"],
    ["Amber",    "amber",    "--status-amber"],
    ["Red",      "red",      "--status-red"],
    ["Awaiting analysis", "empty", "--status-nodata"]
  ];

  function renderStatusLegend() {
    const host = document.getElementById("status-legend");
    if (!host) return;
    const counts = { complete: 0, green: 0, yellow: 0, amber: 0, red: 0, empty: 0 };
    (window.LIN_PROJECTS || []).forEach((p) => {
      try { counts[statusKey(p)]++; } catch (e) { counts.empty++; }
    });
    host.innerHTML = LEGEND_BANDS.map(([name, key, cssVar]) =>
      `<span class="legend-item" data-status="${key}">`
      + `<span class="legend-dot" style="background:var(${cssVar})" aria-hidden="true"></span>`
      + `<span class="legend-name">${esc(name)}</span>`
      + `<span class="legend-count">${counts[key]}</span>`
      + `</span>`).join("");
  }

  // T12. Same two corrections as the legend. It asked hasSignals() first, so a project with a
  // stored result but no legacy client-side signals blob was labelled as having nothing; and
  // "Awaiting ingest" is retired wording that no other surface uses. deriveHealthState() already
  // reads the stored row and already returns "Awaiting analysis" when there is none, so it can
  // simply be asked.
  function stateLabel(p) {
    if (p && p.slim) {
      const lab = (typeof slimStatusLabel === "function") ? slimStatusLabel(p) : null;
      return lab || "Awaiting analysis";
    }
    return deriveHealthState(p);
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

  /* ---------- rectangular-stage side column ----------
     A vertical status legend to the LEFT of the scope (dot + name + count per
     status), mono 11px. The former right-hand ring-meaning column ("On track /
     Watch / Escalate") was removed — the stage caption already explains that
     radial distance is drift from baseline, so the labels were redundant. The
     scope stays centered in the wide viewBox (x=600 of 1200). */
  function buildStageColumns(svg, narrow, VW, VH, thresholdRings) {
    const mono = { "font-family": "var(--font-mono, monospace)", "font-size": "11", fill: "var(--muted)" };

    // T12. THE STATUS LEGEND USED TO BE BUILT HERE, inside the radar's own SVG, which is why
    // switching to Map or Globe lost the key while those views kept colouring markers by exactly
    // the same statuses. It now lives in shared markup outside every stage and is rendered by
    // renderStatusLegend(). Nothing else was drawn in this column, so this function is left as
    // the seam rather than deleted: the right-hand ring-meaning column was removed in Release 2,
    // and if a per-stage annotation is ever wanted again this is where it goes.
    void svg; void narrow; void VW; void VH; void thresholdRings; void mono;
  }

  /* ---------- radar scope ---------- */
  function buildRadar() {
    const svg = $("#radar-svg");
    svg.innerHTML = "";

    // Visibility into exactly what reaches the radar. A project missing from
    // this list was dropped before render (hydrate / archived split) rather
    // than by buildRadar itself.
    console.log("Projects loaded:", LIN_PROJECTS.length, LIN_PROJECTS.map((p) => p.id));

    const R = R_MAX; // 202.4 — outer edge (derived from SCOPE_H)

    // ── rectangular stage geometry ────────────────────────────────────────
    // Wide stage: 1200×460, scope centered, status legend left / threshold
    // labels right. Narrow (<800px panel): 460×680, side columns stack below.
    const wrap = svg.parentElement;
    const panelW = (wrap && wrap.clientWidth) || window.innerWidth;
    const narrow = panelW < 800;
    const VW = narrow ? 460 : 1200;
    const VH = narrow ? 680 : 460;   // narrow: SCOPE_H band on top + stacked columns beneath
    CENTER_X = narrow ? VW / 2 : 600;
    // CENTER_Y is fixed at SCOPE_H/2 — the circle is centered in its band in
    // both modes, so it is a const now and needs no per-build assignment.
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
      { frac: 0.33, stroke: "var(--status-green)", label: "On track" },
      { frac: 0.66, stroke: "var(--status-amber)", label: "Watch"    },
      { frac: 0.90, stroke: "var(--status-red)",   label: "Escalate" },
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
    const DEG_INSET = R * 0.078;   // ≈13 at the old R — keeps the label just inside the ring
    for (let deg = 0; deg < 360; deg += 30) {
      const pos = polar(deg, R - DEG_INSET);
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
    const MIN_SEP = ICON * 2.43;      // ~2.4× the icon size — scales with the glyph
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
    // blip), vertically in ±10px steps, from the uniform (LABEL_DX, +4) offset.
    const LABEL_W = 44, LABEL_NUDGE = 10;
    const LABEL_DX = ICON / 2 + 4;    // clear of the glyph edge, whatever ICON is
    plots.forEach((q) => { q.lx = q.x + LABEL_DX; q.ly = q.y + 4; });
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
    // (ICON is module-scope: MIN_SEP above derives from it.)

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
      titleEl.textContent = `${p.id}: ${p.name}`;
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
          cx: q.x, cy: q.y, r: (ICON / 2 + 2).toFixed(1),
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

      // color-blind-safe cue: small shape badge at the icon's top-right
      // corner (too small at ICON=16 for a legible letter — see shapeBadge()).
      if (!empty && window.linStatusShape) {
        const shape = linStatusShape(status);
        const badgeFill = window.LIN_STATUS_COLORS ? LIN_STATUS_COLORS[
          status === "complete" ? "Complete" : status === "green" ? "Green" :
          status === "yellow" ? "Yellow" : status === "amber" ? "Amber" : "Red"
        ] : color;
        g.appendChild(shapeBadge(shape, q.x + ICON / 2 - 1, q.y - ICON / 2 + 1, 3.4, badgeFill));
      }

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
     Real street-level map — the portfolio's second view.
     MapLibre GL JS (vendored, assets/vendor/) + OpenFreeMap vector tiles: no API key,
     no account, no billing. Dark style for Gotham/NYC, positron for
     Miami; the style is swapped when the theme changes (markers are
     DOM overlays and survive the swap). One custom HTML building
     glyph per located project, colored by status and blinking like
     the radar blips; selecting one flies to street level with
     MapLibre's built-in arc. If the library or style can't load, a
     muted panel takes the stage and the Radar view stays fully
     functional — no console error storms.
     ============================================================ */
  const VIEW_KEY = "lin-portfolio-view";
  const GL_STYLE = {
    dark:  "https://tiles.openfreemap.org/styles/dark",      // Gotham + NYC
    light: "https://tiles.openfreemap.org/styles/positron"   // Miami
  };
  const GL_WORLD = { center: [20, 20], zoom: 1.6 };
  let mapBuilt = false;      // lazily built on first switch
  /* Which project ids have already had their full JSON fetched for a geographic view. A SET,
     NOT A BOOLEAN: the boolean this replaces latched on the first geographic open, so a view
     opened before the portfolio had loaded — or before a project was created — latched with
     nothing fetched and never tried again for the rest of the session. Keyed by id, the work
     is still done at most once per project per session, and a project that arrives later is
     not locked out of ever being placed. */
  const geoHydratedIds = new Set();
  let glMap = null;          // MapLibre instance (null until built / after failure)
  let glMarkers = {};        // id → { marker, el, p }
  let glPopup = null;        // the single open popup, if any
  let glLoadTimer = null;    // style-load watchdog → failure panel
  let glFailed = false;
  let mapBootRobot = null;   // 'loading' working-robot shown while tiles/style init
  let focusedPinId = null;   // the flown-to / selected marker
  // The portfolio globe's own handle. LinGlobe is no longer a singleton — the project detail
  // view keeps its own — so each caller holds and tears down the one it made.
  let portfolioGlobe = null;
  let globeMountToken = 0;

  // VENDORED, NOT CDN. These were cdnjs URLs, which meant the map failed on any corporate
  // network that blocks a public CDN — a realistic case for the directors this platform is for,
  // and one that looks like a broken product rather than a blocked request. Serving them from
  // /assets reduces the failure question to WebGL alone, which showMapFailure() already handles.
  //
  // Still loaded on demand rather than as static tags, unchanged: the map is one tab of one page
  // and has never been worth blocking the initial load for.
  const GL_CSS_URL = "assets/vendor/maplibre-gl.min.css";
  const GL_JS_URL  = "assets/vendor/maplibre-gl.min.js";
  let mapAssetsPromise = null;

  /* inject the MapLibre CSS/JS on demand (background warm-up or first Map
     toggle) instead of blocking the initial page load with static tags. */
  function loadMapAssets() {
    if (typeof maplibregl !== "undefined") return Promise.resolve();
    if (mapAssetsPromise) return mapAssetsPromise;
    mapAssetsPromise = new Promise((resolve, reject) => {
      if (!document.querySelector('link[data-maplibre-css]')) {
        const link = document.createElement("link");
        link.rel = "stylesheet";
        link.href = GL_CSS_URL;
        link.dataset.maplibreCss = "1";
        document.head.appendChild(link);
      }
      const script = document.createElement("script");
      script.src = GL_JS_URL;
      script.dataset.maplibreJs = "1";
      script.onload = () => resolve();
      script.onerror = () => reject(new Error("maplibre load failed"));
      document.head.appendChild(script);
    });
    return mapAssetsPromise;
  }

  /* respect constrained connections: no background warm-up on save-data or 2g */
  function shouldSkipMapWarmup() {
    try {
      const c = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
      if (!c) return false;
      if (c.saveData) return true;
      if (c.effectiveType && /2g/.test(c.effectiveType)) return true;
    } catch (e) {}
    return false;
  }

  /* background warm-up: after the portfolio list has painted and the browser
     is idle, preload the MapLibre assets and build the (hidden) map instance
     so style/fonts/sprites/tiles fetch while the user is still on the radar. */
  /* ORPHANED AS OF T11 — READ BEFORE REUSING.
     The MapLibre map is no longer reachable from any user path. It was two things: the second
     portfolio stage, and the fallback the globe degraded to. The flat atlas is now both, so
     nothing routes here any more — scheduleMapWarmup() has no callers, and buildMap() is only
     reachable from a flag that buildMap() itself is the only thing to set.

     It is left in place rather than deleted because removing it touches ~400 lines, two vendored
     files (837 KB), the CSP, and the map markup, and that is its own change with its own
     verification. It costs nothing where it stands: no path loads maplibre-gl, so the default
     path never pays for it. Deleting it is a clean follow-up, not a loose end that will bite —
     but do not "fix" it back into service by wiring a caller. */
  function scheduleMapWarmup() {
    if (shouldSkipMapWarmup()) return;
    const idle = window.requestIdleCallback || function (cb) { setTimeout(cb, 1200); };
    idle(() => {
      if (mapBuilt || glMap) return;   // already built (or being built) — nothing to warm
      loadMapAssets().then(() => { if (!mapBuilt && !glMap) createGlMap(false); }).catch(() => {});
    }, { timeout: 3000 });   // force a fire even under sustained load — never wait forever
  }

  function showBootStatus(msg) {
    const el = document.getElementById("map-boot-status");
    if (el) { el.textContent = msg; el.hidden = false; }
    // 'loading' working-robot (sm, indeterminate — no real progress signal for
    // tile/style init, so no invented bar). Mounted once; removed on the map's
    // first idle/load or on the failure path (hideBootStatus / showMapFailure).
    const host = document.getElementById("map-gl");
    if (host && host.parentNode && !mapBootRobot && window.LinWorkingRobot) {
      const holder = document.createElement("div");
      holder.className = "map-boot-robot";
      host.parentNode.insertBefore(holder, host.nextSibling);
      const handle = LinWorkingRobot.mount(holder, {
        variant: "loading", size: "sm", message: "Loading map…", progress: null
      });
      mapBootRobot = { handle, holder };
    }
  }
  function hideBootStatus() {
    const el = document.getElementById("map-boot-status");
    if (el) el.hidden = true;
    if (mapBootRobot) {
      try { mapBootRobot.handle.destroy(); } catch (e) {}
      if (mapBootRobot.holder && mapBootRobot.holder.parentNode) mapBootRobot.holder.parentNode.removeChild(mapBootRobot.holder);
      mapBootRobot = null;
    }
  }

  function hasCoords(p) {
    return !!p && p.lat != null && p.lng != null &&
      Number.isFinite(Number(p.lat)) && Number.isFinite(Number(p.lng));
  }
  // Whether a project has an ADDRESS (for the "no address set" note), tolerant
  // of BOTH shapes: full projects and v10.32 slim rows both surface
  // address / formattedAddress / lat / lng at the top level. A project counts as
  // located if it has coords OR a non-empty address string — so a project whose
  // address is set but not yet geocoded is no longer wrongly flagged.
  function hasAddress(p) {
    if (!p) return false;
    if (hasCoords(p)) return true;
    const a = p.formattedAddress || p.address;
    return !!(a && String(a).trim());
  }

  /* Sector-changed flag: changing a project's sector invalidates sector-gated
     module results, so the row is flagged "recompute" until its signals are
     recomputed (recompute-all or a per-project populate). Persisted so the flag
     survives a reload. */
  const SECTOR_DIRTY_KEY = "lpr-sector-dirty";
  function readSectorDirty() {
    try { const v = JSON.parse(localStorage.getItem(SECTOR_DIRTY_KEY) || "[]"); return Array.isArray(v) ? v : []; }
    catch (e) { return []; }
  }
  function writeSectorDirty(ids) { try { localStorage.setItem(SECTOR_DIRTY_KEY, JSON.stringify(ids)); } catch (e) {} }
  function isSectorDirty(id) { return readSectorDirty().indexOf(id) >= 0; }
  function markSectorDirty(id) { const s = readSectorDirty(); if (s.indexOf(id) < 0) { s.push(id); writeSectorDirty(s); } }
  function clearSectorDirty(id) { writeSectorDirty(readSectorDirty().filter((x) => x !== id)); }

  function glStyleForTheme() {
    return document.body.dataset.theme === "light" ? GL_STYLE.light : GL_STYLE.dark;
  }
  function sectorLabel(p) {
    return { design: "Design", construction: "Construction", hybrid: "Hybrid", combined: "Hybrid" }[String(p.sector || "").toLowerCase()] || p.sector || "N/A";
  }
  function statusColorFor(p) {
    const status = statusKey(p);
    return status === "complete" ? STATUS_COLOR.complete :
      status === "green"  ? STATUS_COLOR.green :
      status === "yellow" ? STATUS_COLOR.yellow :
      status === "amber"  ? STATUS_COLOR.amber :
      status === "red"    ? STATUS_COLOR.red : "var(--muted)";
  }

  /* muted failure panel inside the stage; the Radar view keeps working */
  function showMapFailure(msg) {
    glFailed = true;
    if (glLoadTimer) { clearTimeout(glLoadTimer); glLoadTimer = null; }
    if (glMap) { try { glMap.remove(); } catch (e) {} glMap = null; }
    glMarkers = {}; glPopup = null; focusedPinId = null;
    hideBootStatus();   // the fail panel below is the single source of truth for the error
    const host = document.getElementById("map-gl");
    if (host) host.innerHTML = `<div class="gl-fail">${esc(msg || "Map tiles unavailable: check connection")}</div>`;
    const rb = document.getElementById("map-reset-btn");
    if (rb) rb.hidden = true;
  }

  /* build the MapLibre map for the current theme (markers added on load).
     showStatus: false during background warm-up (stage isn't visible, no
     need to tell the user anything); true when built because the user is
     actually looking at the map stage and waiting on it. */
  function createGlMap(showStatus) {
    const host = document.getElementById("map-gl");
    if (!host) return;
    if (typeof maplibregl === "undefined") { if (showStatus) showMapFailure(); return; }   // CDN blocked / offline
    host.innerHTML = "";
    glFailed = false;
    if (showStatus) showBootStatus("ACQUIRING TILES…");
    try {
      glMap = new maplibregl.Map({
        container: host,
        style: glStyleForTheme(),
        center: GL_WORLD.center,
        zoom: GL_WORLD.zoom,
        attributionControl: true,      // "© OpenStreetMap contributors" stays visible (license)
        maxZoom: 18
      });
    } catch (e) { if (showStatus) showMapFailure(); return; }

    // watchdog: if the style never loads (offline / CDN down), show the panel
    glLoadTimer = setTimeout(() => {
      if (glMap && !glMap.isStyleLoaded()) showMapFailure();
    }, 9000);

    glMap.on("load", () => {
      if (glLoadTimer) { clearTimeout(glLoadTimer); glLoadTimer = null; }
      hideBootStatus();
      // T13. Add zoom controls. NavigationControl is vendored with MapLibre GL so no
      // new dependency is introduced. Position top-right to avoid the attribution badge.
      if (typeof maplibregl.NavigationControl === "function") {
        glMap.addControl(new maplibregl.NavigationControl(), "top-right");
      }
      addGlMarkers();
    });
    // swallow MapLibre's transient tile/sprite errors so they neither storm the
    // console nor nuke the map. A genuine style-load failure (offline / CDN down)
    // is caught by the watchdog above: 'load' never fires, panel shows.
    glMap.on("error", () => {});
  }

  /* ---------- the shared map-pin shape ----------
     Classic teardrop, defined ONCE in a hidden <defs> and referenced by every
     marker via <use>; only the status colour varies per instance (the body is
     fill:currentColor, and .gl-pin-inner sets color from --pin-color).

     Geometry matters here: the viewBox is 24×32 and the TIP sits at exactly
     (12, 32) — the bottom-centre of the box. Combined with MapLibre's
     anchor:"bottom" (which puts the element's bottom-centre on the coordinate)
     that lands the point, not the head, on the exact lat/lng. Anything that
     adds height below the svg would push the tip off the coordinate, which is
     why .gl-pin-num is taken out of flow in CSS.

     The radar keeps its own building glyph (#blip-building) — this is map-only. */
  const GL_PIN_DEFS_ID = "gl-pin-defs";
  function ensureGlPinDefs() {
    if (document.getElementById(GL_PIN_DEFS_ID)) return;
    const holder = document.createElementNS(SVG_NS, "svg");
    holder.id = GL_PIN_DEFS_ID;
    holder.setAttribute("aria-hidden", "true");
    holder.setAttribute("width", "0");
    holder.setAttribute("height", "0");
    holder.style.cssText = "position:absolute;width:0;height:0;overflow:hidden";
    holder.innerHTML =
      '<defs><g id="gl-pin-shape">' +
        // head: r9.5 circle centred (12,12); flanks sweep down to the tip at (12,32)
        '<path class="gl-pin-body" fill="currentColor" ' +
          'd="M12 32 C12 32 21.5 20.2 21.5 12 A9.5 9.5 0 1 0 2.5 12 C2.5 20.2 12 32 12 32 Z"/>' +
      '</g></defs>';
      // (The former decorative "hole" circle at (12,12) was replaced by the
      // color-blind-safe status LETTER drawn per-marker in pinMarkerEl() —
      // same visual anchor, now carries information instead of just contrast.)
    document.body.appendChild(holder);
  }

  /* one custom HTML marker per project — pin glyph, status color, blink.
     All visual state lives on .gl-pin-inner; MapLibre owns .gl-pin's transform
     for positioning, so we never set transform on the marker element itself. */
  function pinMarkerEl(p) {
    ensureGlPinDefs();
    const el = document.createElement("div");
    el.className = "gl-pin";
    el.dataset.status = statusKey(p);
    el.style.setProperty("--pin-color", statusColorFor(p));
    el.setAttribute("role", "button");
    el.setAttribute("tabindex", "0");
    el.setAttribute("aria-label", `${p.id} ${p.name}, ${stateLabel(p)}`);
    const inner = document.createElement("div");
    inner.className = "gl-pin-inner";
    inner.style.animationDelay = mapPinBlinkDelay(p.id).toFixed(2) + "s";   // stagger the fleet
    // 30px tall at the 24×32 aspect → 22.5 wide. The <use> pulls the shared
    // teardrop; currentColor resolves from --pin-color on .gl-pin-inner.
    // color-blind-safe cue: a status letter (C/G/Y/A/R) inside the pin head —
    // the head is a 19px circle, big enough for a legible letter (unlike the
    // 16-unit radar blip icon, which uses a shape badge instead — see
    // shapeBadge() above). Ink auto-contrasts per status via linStatusInk().
    const sKey = statusKey(p);
    const letter = window.linStatusLetter ? linStatusLetter(sKey) : "";
    const capName = sKey === "complete" ? "Complete" : sKey === "green" ? "Green" :
      sKey === "yellow" ? "Yellow" : sKey === "amber" ? "Amber" : sKey === "red" ? "Red" : null;
    const ink = (capName && window.LIN_STATUS_COLORS && window.linStatusInk)
      ? linStatusInk(LIN_STATUS_COLORS[capName]) : "#0b1220";
    const letterSvg = letter
      ? `<text class="gl-pin-letter" x="12" y="12" text-anchor="middle" dominant-baseline="central" ` +
        `font-family="var(--font-mono, monospace)" font-size="10" font-weight="700" fill="${ink}" ` +
        `aria-hidden="true">${esc(letter)}</text>`
      // no signals yet: keep the old decorative "hole" dot instead of a letter
      : '<circle class="gl-pin-hole" cx="12" cy="12" r="3.4" fill="rgba(0,8,18,.82)" stroke="none"/>';
    inner.innerHTML =
      '<svg class="gl-pin-glyph" viewBox="0 0 24 32" width="22.5" height="30" aria-hidden="true">' +
      '<use href="#gl-pin-shape"/>' + letterSvg + '</svg>' +
      `<span class="gl-pin-num">${esc(p.id)}</span>`;
    el.appendChild(inner);
    return el;
  }

  function addGlMarkers() {
    if (!glMap) return;
    Object.keys(glMarkers).forEach((id) => { try { glMarkers[id].marker.remove(); } catch (e) {} });
    glMarkers = {};
    LIN_PROJECTS.filter(hasCoords).forEach((p) => {
      // regression guard: |lat| > 90 means lat/lng got swapped upstream
      if (Math.abs(Number(p.lat)) > 90) {
        console.warn(`[map] project ${p.id}: latitude ${p.lat} out of range (±90). Check lat/lng order`);
      }
      const el = pinMarkerEl(p);
      const marker = new maplibregl.Marker({ element: el, anchor: "bottom" })
        .setLngLat([Number(p.lng), Number(p.lat)])   // MapLibre = [lng, lat]
        .addTo(glMap);
      el.dataset.id = p.id;
      el.setAttribute("aria-label", `${p.id} ${p.name}, ${stateLabel(p)}`);   // MapLibre resets it to "Map marker" on add
      const open = () => { selectProject(p.id); flyToProject(p.id); };
      el.addEventListener("click", (e) => { e.stopPropagation(); open(); });
      el.addEventListener("dblclick", (e) => { e.stopPropagation(); hideMapCard(); openDetail(p.id); });
      el.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(); }
      });
      glMarkers[p.id] = { marker, el, p };
    });
    updateNoLocationNote();
    if (focusedPinId && !glMarkers[focusedPinId]) focusedPinId = null;   // stale focus after refresh
    highlightPin();
    applyGlFocus();
  }

  /* "No address set" side note — each id opens that project's inline Manage
     accordion on the Portfolio list (address is edited there now). */
  function updateNoLocationNote() {
    const note = document.getElementById("map-nolocation");
    if (!note) return;
    const unlocated = LIN_PROJECTS.filter((p) => !hasAddress(p));
    if (unlocated.length) {
      note.hidden = false;
      note.innerHTML = "No address set: " + unlocated.map((p) =>
        `<button type="button" class="map-noloc-id" data-editloc="${esc(p.id)}">${esc(p.id)}</button>`).join(", ");
      note.querySelectorAll("[data-editloc]").forEach((b) =>
        b.addEventListener("click", () => {
          showPage("portfolio");
          if (window.LinIngest && LinIngest.openInlineManage) LinIngest.openInlineManage(b.dataset.editloc);
        }));
    } else {
      note.hidden = true;
      note.innerHTML = "";
    }
  }

  /* popup on click: number · name · sector · status pill · address · Open detail */
  function hideMapCard() { if (glPopup) { try { glPopup.remove(); } catch (e) {} glPopup = null; } }
  function openGlPopup(p) {
    if (!glMap) return;
    hideMapCard();
    const node = document.createElement("div");
    node.className = "gl-pop";
    const addr = p.formattedAddress || p.address;
    node.innerHTML =
      `<div class="mt-num">${esc(p.id)}</div>` +
      `<div class="mt-name">${esc(p.name)}</div>` +
      `<div class="mt-sub">${esc(sectorLabel(p))} · <span class="gl-pill" data-st="${esc(statusKey(p))}">${esc(stateLabel(p))}</span></div>` +
      (addr ? `<div class="mt-addr">${esc(addr)}</div>` : "") +
      `<button type="button" class="map-card-open">Open detail →</button>`;
    node.querySelector(".map-card-open").addEventListener("click", () => { hideMapCard(); openDetail(p.id); });
    glPopup = new maplibregl.Popup({ offset: 30, closeButton: true, closeOnClick: false, className: "gl-popup", maxWidth: "260px" })
      .setLngLat([Number(p.lng), Number(p.lat)])
      .setDOMContent(node)
      .addTo(glMap);
  }

  /* selection sync (list row ↔ marker): the selected marker scales + others dim */
  function highlightPin() {
    const host = document.getElementById("map-gl");
    Object.keys(glMarkers).forEach((id) => {
      const on = id === selectedId;
      const el = glMarkers[id].el;
      const was = el.classList.contains("gl-selected");
      el.classList.toggle("gl-selected", on);
      if (on && !was) { el.classList.remove("gl-ring"); void el.offsetWidth; el.classList.add("gl-ring"); }  // one-shot ring
      if (!on) el.classList.remove("gl-ring");
    });
    if (host) host.classList.toggle("gl-any-selected", !!(selectedId && glMarkers[selectedId]));
  }

  /* keep the reset control + focus dim in sync with the flown-to pin */
  function applyGlFocus() {
    const rb = document.getElementById("map-reset-btn");
    if (rb) rb.hidden = !focusedPinId;
  }

  /* ============================================================
     Cinematic entrance. Selecting a project (pin click, or list-row
     selection while the map view is active) flies to street level
     with MapLibre's built-in arc; the selected marker scales 1.4×
     with a one-shot ring pulse and the rest dim. Reduced motion →
     jumpTo (no arc). Reset returns to the world view.
     ============================================================ */
  function flyToProject(id) {
    const m = glMarkers[id];
    if (!glMap || !m) return;                 // no marker (no coordinates) → no flight
    focusedPinId = id;
    applyGlFocus();
    highlightPin();                            // ensure scale/dim reflect this pin
    const center = [Number(m.p.lng), Number(m.p.lat)];
    if (reduceMotion()) glMap.jumpTo({ center, zoom: 16 });
    else glMap.flyTo({ center, zoom: 16, speed: 1.2, curve: 1.6, essential: true });
    openGlPopup(m.p);
  }

  function resetMapView() {
    focusedPinId = null;
    hideMapCard();
    // clear the map's visual selection so the world view isn't left with one pin
    // scaled 1.4× and the rest dimmed (list-row selection is unaffected)
    const host = document.getElementById("map-gl");
    if (host) host.classList.remove("gl-any-selected");
    Object.keys(glMarkers).forEach((id) => glMarkers[id].el.classList.remove("gl-selected", "gl-ring"));
    applyGlFocus();
    if (!glMap) return;
    if (reduceMotion()) glMap.jumpTo(GL_WORLD);
    else glMap.flyTo({ center: GL_WORLD.center, zoom: GL_WORLD.zoom, speed: 1.2, curve: 1.6, essential: true });
  }

  /* theme switch → swap the OpenFreeMap style (markers persist across setStyle) */
  function onMapThemeChange() {
    if (!glMap || glFailed) return;
    try { glMap.setStyle(glStyleForTheme()); } catch (e) {}
  }

  /* Lazy map build: on first use, swap slim portfolio records for full
     project JSON (the slim list carries no coordinates) — one GET per
     project, once per session, only when the map view is actually opened. */
  /* Swap slim portfolio records for full project JSON. THE SLIM LIST CARRIES NO COORDINATES —
     facade.slim_row() returns status and metrics and nothing about location — so any view that
     places projects geographically has to do this first. Shared by the map and the globe so
     there is one copy: a second one would eventually be the one that forgot. One GET per
     project, once per session, only when a geographic view is actually opened. */
  async function hydrateProjectsForGeo() {
    if (!(window.LinStore && LinStore.getProject && LinStore.configured && LinStore.configured())) return;
    // Only rows that are still a projection AND have not been fetched already this session.
    // Marked before the await so two overlapping opens do not both fetch the same project.
    const slims = LIN_PROJECTS.filter((p) => p && p.slim && !geoHydratedIds.has(p.id));
    if (!slims.length) return;
    slims.forEach((p) => geoHydratedIds.add(p.id));
    try {
      const fulls = await Promise.all(slims.map((p) => LinStore.getProject(p.id).catch(() => null)));
      fulls.forEach((f) => {
        if (f && !f.slim) {
          const i = LIN_PROJECTS.findIndex((x) => x.id === f.id);
          if (i >= 0) LIN_PROJECTS[i] = f;
        }
      });
    } catch (e) {
      // Let a failed fetch be retried on the next open rather than being remembered as done.
      slims.forEach((p) => geoHydratedIds.delete(p.id));
    }
  }

  async function buildMap() {
    const host = document.getElementById("map-gl");
    if (!host) return;
    await hydrateProjectsForGeo();
    if (!glMap) {
      glFailed = false;
      try { await loadMapAssets(); } catch (e) { showMapFailure(); mapBuilt = true; return; }
      createGlMap(true);                          // markers added when the style loads
    } else {
      try { glMap.resize(); } catch (e) {}        // container was hidden until now
      if (glMap.isStyleLoaded()) addGlMarkers();
      else { showBootStatus("ACQUIRING TILES…"); glMap.once("load", () => { hideBootStatus(); addGlMarkers(); }); }
    }
    mapBuilt = true;
  }

  function mapViewActive() {
    const page = document.querySelector('.page[data-page="portfolio"]');
    const wrap = document.querySelector(".map-wrap");
    return !!(page && !page.hidden && wrap && !wrap.hidden);
  }
  // list-row selections fly only when the map view is actually showing
  // T11 orphaned the MapLibre stage (see the "ORPHANED AS OF T11" note above
  // scheduleMapWarmup): the "Map" button now shows the flat SVG atlas, not glMap. So the live
  // geographic surfaces a selection can fly to are the atlas — the Map view, and also what the
  // globe degrades to when it cannot draw — and the globe itself.
  function maybeFlyToSelection(id) {
    if (!id) return;   // selectProject already returned the viewer to the wide view
    if (atlasViewActive()) focusAtlasProject(id);
    else if (globeViewActive()) focusGlobeProject(id);
  }

  function atlasViewActive() {
    const page = document.querySelector('.page[data-page="portfolio"]');
    const wrap = document.querySelector(".atlas-wrap");
    return !!(page && !page.hidden && wrap && !wrap.hidden);
  }

  function globeViewActive() {
    const page = document.querySelector('.page[data-page="portfolio"]');
    const wrap = document.querySelector(".globe-wrap");
    return !!(page && !page.hidden && wrap && !wrap.hidden);
  }

  /* Atlas equivalent of flyToProject: zooms the SVG viewBox in on the project. A project with no
     usable coordinates leaves the viewBox exactly where it was — atlas.js's focus() already
     guards this, checked again here so a project not even in LIN_PROJECTS cannot reach it. */
  function focusAtlasProject(id) {
    if (!window.LinAtlas || typeof LinAtlas.focus !== "function") return;
    const host = document.getElementById("atlas-canvas");
    const p = LIN_PROJECTS.find((x) => x.id === id);
    if (!host || !p) return;
    try { LinAtlas.focus(host, p); } catch (e) {}
  }

  function resetAtlasView() {
    if (!window.LinAtlas || typeof LinAtlas.resetView !== "function") return;
    const host = document.getElementById("atlas-canvas");
    if (!host) return;
    try { LinAtlas.resetView(host); } catch (e) {}
  }

  /* Globe equivalent of flyToProject. A project with no usable coordinates leaves the camera
     exactly where it was — same contract as the map's flyToProject, which also does nothing
     when there is no marker to fly to. */
  function focusGlobeProject(id) {
    if (!portfolioGlobe || typeof portfolioGlobe.focus !== "function") return;
    const p = LIN_PROJECTS.find((x) => x.id === id);
    const lat = p && Number(p.lat), lng = p && Number(p.lng);
    if (!p || !isFinite(lat) || !isFinite(lng)) return;
    portfolioGlobe.focus(lat, lng);
  }

  function resetGlobeView() {
    if (portfolioGlobe && typeof portfolioGlobe.resetView === "function") portfolioGlobe.resetView();
  }

  // Ctrl/Cmd+0 + Escape → world view — the handler only acts (and only calls
  // preventDefault) while the map view is active AND a project is focused or
  // keyboard focus is inside the map stage, so the browser's page-zoom reset
  // keeps working everywhere else.
  document.addEventListener("keydown", (e) => {
    const zeroCombo = (e.ctrlKey || e.metaKey) && e.key === "0";
    if (!zeroCombo && e.key !== "Escape") return;
    if (!mapViewActive()) return;
    const wrap = document.querySelector(".map-wrap");
    const stageFocused = wrap && wrap.contains(document.activeElement);
    if (!focusedPinId && !stageFocused) return;
    if (zeroCombo) e.preventDefault();
    resetMapView();
  });


  /* ---------- Radar | Map | Globe view toggle (persisted; MAP is the default) ----------

     T11. Three buttons, four possible stages. The default is "map", the flat SVG atlas, because
     it is the only geographic view that cannot fail to draw: no WebGL, no 3D library, no
     animation loop, every mark a DOM node the moment it is built. The globe stayed in the
     codebase but stopped being the thing the portfolio depends on.

     "globe" now degrades to the ATLAS rather than to MapLibre. That is a shorter chain and a
     better one: the atlas needs no network at all beyond geometry already vendored, whereas
     MapLibre needed tiles from a host a corporate network may well block — the fallback was
     itself the most fragile link. */
  function setPortfolioView(view, persist) {
    // An unrecognised value is a corrupt or legacy preference; send it to the default rather than
    // to a particular view, so there is one answer to "what does a user with no valid preference
    // get". The globe still degrades to the map on its own if it cannot draw.
    if (view !== "map" && view !== "globe" && view !== "radar") view = "globe";
    const wantsGeo = view === "globe" || view === "map";
    if (!wantsGeo) hideMapCard();   // the pinned card is fixed-positioned — never leave it over the radar
    const radarWrap = document.querySelector(".radar-wrap");
    const mapWrap = document.querySelector(".map-wrap");
    const globeWrap = document.querySelector(".globe-wrap");
    const atlasWrap = document.querySelector(".atlas-wrap");
    const note = document.querySelector(".radar-note");
    if (radarWrap) radarWrap.hidden = wantsGeo;
    if (note) note.hidden = wantsGeo;           // radar caption; the geo views have their own
    document.querySelectorAll(".stage-btn").forEach((b) =>
      b.classList.toggle("active", b.dataset.view === view));

    // Whatever we are switching to, the globe's context goes if it is not the globe. A renderer
    // left running behind a hidden panel costs a small instance all afternoon.
    if (view !== "globe") {
      if (globeWrap) globeWrap.hidden = true;
      try { if (portfolioGlobe) { portfolioGlobe.destroy(); portfolioGlobe = null; } } catch (e) {}
      globeMountToken++;   // supersede any mount still resolving, so it releases itself
    }
    if (mapWrap) mapWrap.hidden = true;

    if (view === "radar") {
      if (atlasWrap) atlasWrap.hidden = true;
    } else if (view === "map") {
      if (atlasWrap) atlasWrap.hidden = false;
      buildAtlasStage();
    } else {
      if (atlasWrap) atlasWrap.hidden = true;
      buildGeoStage(globeWrap, mapWrap, atlasWrap);
    }
    // The key is shared markup outside every stage, so switching view does not remove it. This
    // re-render is here so it is correct on the first switch even if the portfolio hydrated after
    // the last refresh, which is the ordering that made it read zero.
    renderStatusLegend();
    if (persist !== false) { try { localStorage.setItem(VIEW_KEY, view); } catch (e) {} }
  }

  /* The default stage. Nothing here can fail in a way that leaves an empty panel: the frame and
     the markers are drawn synchronously, and the coastlines are a fetch of already-vendored
     geometry that resolves to nothing rather than rejecting. */
  async function buildAtlasStage() {
    const host = document.getElementById("atlas-canvas");
    const noteEl = document.getElementById("atlas-note");
    if (!host || !window.LinAtlas) return;
    if (noteEl) noteEl.textContent = "Locating projects…";
    await hydrateProjectsForGeo();
    const res = await LinAtlas.render(host, LIN_PROJECTS, {
      onSelect: (id) => openDetail(id)
    });
    if (noteEl && res) {
      // Say plainly that some projects are not shown, rather than letting a director count the
      // markers and wonder. They are still in the list below.
      noteEl.textContent = res.unplaced > 0
        ? res.placed + " project(s) placed. " + res.unplaced
          + " have no location yet and are listed below."
        : res.placed + " project(s) placed. Select one to open it.";
    }
  }

  /* The degradation chain, in one place so it cannot disagree with itself:
         globe  ->  the flat atlas  ->  the project list that is always in the DOM
     Each step is only reached because the one before it could not run. */
  async function buildGeoStage(globeWrap, mapWrap, atlasWrap) {
    if (!window.LinGlobe) { showAtlasInstead(globeWrap, atlasWrap); return; }
    // JS, NOT CSS, BECAUSE THIS DECIDES WHICH CODE RUNS, NOT HOW IT LOOKS. A media query can
    // hide the globe's canvas; it cannot stop LinGlobe.mount() below from opening a WebGL
    // context and starting globe.gl's animation loop before that hidden canvas is ever
    // painted. On a phone that is the one thing a static geographic view must not do: it is a
    // GPU context and a render loop spent on a panel the mobile scope treats as a picture.
    //
    // Same breakpoint the dock already uses for "this is a phone" (matchMedia, not innerWidth,
    // so it tracks the same live viewport CSS reasons about). Globe already had a degrade
    // path for "cannot draw" — this adds one more reason to take it, before any WebGL work
    // starts, rather than mounting and then discovering the viewport was never right for it.
    const isPhoneViewport = window.matchMedia && window.matchMedia("(max-width: 700px)").matches;
    if (isPhoneViewport) { showAtlasInstead(globeWrap, atlasWrap); return; }
    if (globeWrap) globeWrap.hidden = false;
    if (mapWrap) mapWrap.hidden = true;

    const host = document.getElementById("globe-canvas");
    const noteEl = document.getElementById("globe-note");
    if (noteEl) noteEl.textContent = "Locating projects…";
    await hydrateProjectsForGeo();
    // GUARD AGAINST A DOUBLE MOUNT. setPortfolioView can run twice in quick succession — the
    // persisted-view restore and a user click — and mount() is async, so a check on the handle
    // alone misses: the first mount has not resolved when the second starts, and both end up
    // live. Observed as liveCount() reporting 2 for one visible globe, which is a leaked WebGL
    // context. The token is taken synchronously, so only the most recent mount keeps its handle.
    if (portfolioGlobe) { try { portfolioGlobe.destroy(); } catch (e) {} portfolioGlobe = null; }
    const token = ++globeMountToken;

    /* T11a. A WATCHDOG THAT POLLS, because mount() resolving is not the same as the globe
       drawing. globe.gl builds its scene inside the animation loop, so on a machine where that
       loop never runs mount() still resolves ok and the panel stays black — the exact failure
       this whole change exists to stop a director from seeing.

       THE FIRST VERSION OF THIS ASKED ONCE AND BROKE THE WORKING CASE. mount() resolves in about
       40ms; the scene group does not exist until roughly a second later. Asking hasScene() a
       single time at resolve therefore always saw false, the watchdog never stood down, and four
       seconds later it destroyed a perfectly good globe and switched to the atlas by itself. The
       symptom was "selecting Globe switches back to Map on its own after a moment", and it fired
       precisely when the globe was working.

       So it polls to a deadline instead: the moment a scene appears it stands down, and only a
       deadline reached with no scene at all is treated as a failure. */
    let settled = false;
    const DEADLINE_MS = 6000, POLL_MS = 150;
    const startedAt = Date.now();
    let poll = setInterval(() => {
      if (settled || token !== globeMountToken) { clearInterval(poll); return; }
      const handle = portfolioGlobe;
      if (handle && typeof handle.hasScene === "function" && handle.hasScene()) {
        settled = true; clearInterval(poll);
        return;                                   // the globe drew; leave it alone
      }
      if (Date.now() - startedAt < DEADLINE_MS) return;
      settled = true; clearInterval(poll);
      try { if (portfolioGlobe) { portfolioGlobe.destroy(); portfolioGlobe = null; } } catch (e) {}
      showAtlasInstead(globeWrap, atlasWrap);
    }, POLL_MS);
    const giveUp = { stop: () => { settled = true; clearInterval(poll); } };

    LinGlobe.mount(host, LIN_PROJECTS, {
      // Selecting a point does exactly what double-clicking a map marker has always done.
      // Deliberately not a new navigation idea.
      onSelect: (id) => openDetail(id)
    }).then((res) => {
      if (token !== globeMountToken) {
        // A newer mount superseded this one while it was resolving. Release it rather than
        // leaving an orphan renderer holding a context nothing will ever tear down.
        try { if (res && res.handle) res.handle.destroy(); } catch (e) {}
        giveUp.stop();
        return;
      }
      if (!res || !res.ok) {
        // WebGL missing, or the library never arrived — a real failure, and known immediately.
        giveUp.stop();
        showAtlasInstead(globeWrap, atlasWrap);
        return;
      }
      // Hand the handle to the poller and let it decide. Deliberately NOT stood down here: at
      // this point the scene almost certainly does not exist yet, and treating "mounted" as
      // "drew" is what this file used to get wrong in the other direction.
      portfolioGlobe = res.handle;
      if (!(res.handle && typeof res.handle.hasScene === "function")) {
        giveUp.stop();   // an older build with no way to ask; trust the resolve rather than nag
      }
      if (noteEl) {
        // Say plainly that some projects are not shown, rather than letting a director count
        // the points and wonder. They are still in the list below.
        noteEl.textContent = res.unplaceable > 0
          ? res.points + " project(s) placed. " + res.unplaceable
            + " have no location yet and are listed below."
          : res.points + " project(s) placed. Select one to open it.";
      }
    });
  }

  /* The globe could not run. Show the flat map instead — never an empty panel, and no longer
     MapLibre, whose tiles are the one part of the old chain a blocked network could still take
     out. */
  function showAtlasInstead(globeWrap, atlasWrap) {
    if (globeWrap) globeWrap.hidden = true;
    if (atlasWrap) atlasWrap.hidden = false;
    buildAtlasStage();
  }
  function wireViewToggle() {
    document.querySelectorAll(".stage-btn").forEach((b) =>
      b.addEventListener("click", () => setPortfolioView(b.dataset.view)));
    const rb = document.getElementById("map-reset-btn");
    if (rb) rb.addEventListener("click", resetMapView);
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
        // map (no second copy). A row with no computed result has no normalized status
        // and no inline colour, so it stays muted via its class. Slim records
        // carry a precomputed status string; full records derive it — either
        // way normalizeStatusLabel maps the label to a palette key.
        //
        // T12b. The full-record branch used to be hasSignals(p) — the legacy blob — which left
        // every server-analysed project without that blob rendering as an uncoloured word, same
        // family as the legend and the state badge. It now asks about the stored row.
        const hasStatus = (p && p.slim)
          ? (typeof slimStatusLabel === "function" && !!slimStatusLabel(p))
          : (window.LinResults && LinResults.hasResult(p));
        const norm = (hasStatus && typeof normalizeStatusLabel === "function")
          ? normalizeStatusLabel(state) : null;
        const col = (norm && typeof PCEIF_STATUS_HEX !== "undefined") ? PCEIF_STATUS_HEX[norm] : null;
        const stateStyle = col ? ` style="color:${col}"` : "";
        const simChip = "";
        const secKey = String(p.sector || "hybrid").toLowerCase() === "combined" ? "hybrid" : String(p.sector || "hybrid").toLowerCase();
        // Membership columns — PM role, current period, computed state — merged in
        // from the former "Your projects" card. Keyed by project code, which is the
        // same identifier this list already uses (workspaceprojects returns it as
        // project_id === legacy_id === p.id). Absent for accounts that have not
        // loaded a membership list, so every span is conditional.
        const meta = (window.LIN_PM_META && window.LIN_PM_META[p.id]) || null;
        const addr = p.formattedAddress || p.address || "";
        const roleTxt = (meta && meta.role) ? esc(meta.role) : "";
        const periodTxt = (meta && meta.period != null) ? ("Period " + esc(meta.period)) : "";
        const computedSpan = meta
          ? `<span class="li-computed"><span class="li-computed-dot" style="background:var(${meta.computed ? "--status-green" : "--status-nodata"})" aria-hidden="true"></span>${meta.computed ? "Computed" : "Not yet computed"}</span>`
          : "";
        btn.innerHTML =
          `<span class="li-code">${esc(p.id)}</span>` +
          `<span class="li-name">${esc(p.name)}</span>` +
          (addr ? `<span class="li-address" title="${esc(addr)}">${esc(addr)}</span>` : "") +
          `<span class="sector-pill" data-sector="${esc(secKey)}">${esc(sectorLabel(p).toUpperCase())}</span>` +
          (isSectorDirty(p.id) ? `<span class="li-flag" title="Sector changed: recompute signals to update module applicability">recompute</span>` : "") +
          simChip +
          `<span class="li-state state-${esc(statusKey(p))}"${stateStyle}>${esc(state)}</span>` +
          (roleTxt ? `<span class="li-pm">${roleTxt}</span>` : "") +
          (periodTxt ? `<span class="li-period">${periodTxt}</span>` : "") +
          computedSpan +
          `<span class="li-actions">` +
            `<button class="btn small li-manage" data-manage="${esc(p.id)}" title="Edit info, upload, archive, reset (inline)">Manage</button>` +
            `<button class="btn small li-open" data-open="${esc(p.id)}" title="Open project detail">Open →</button>` +
          `</span>`;
        // Clicking an already-selected row deselects it (returns the map/globe to the
        // portfolio-wide view) rather than re-flying to the same place.
        btn.addEventListener("click", () => {
          const next = selectedId === p.id ? null : p.id;
          selectProject(next);
          maybeFlyToSelection(next);
        });
        // both row buttons stop propagation so they never trigger row-select
        btn.querySelectorAll(".li-manage, .li-open").forEach((b) =>
          b.addEventListener("click", (e) => e.stopPropagation()));
        // The row used to carry a "Signals" button beside this one. Both handlers were the same
        // call, openDetail(p.id), and openDetail takes only an id: no section, tab or scroll
        // target, so the two controls were indistinguishable to a user. Merged into this one.
        // "Open" names the action; "Signals" named an internal concept (NAMING_AUTHORITY.md).
        btn.querySelector(".li-open").addEventListener("click", () => openDetail(p.id));
        // Manage → the inline admin accordion directly under this row
        btn.querySelector(".li-manage").addEventListener("click", () => {
          if (window.LinIngest && LinIngest.openInlineManage) LinIngest.openInlineManage(p.id);
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
      const full = `N/A: not applicable to ${naSector || "this sector's"} projects`;
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
  // Computed once; falls back to 103 (the known active count) if categories aren't loaded yet.
  function activeModuleTotal() {
    if (window.LIN_CATEGORIES) {
      return window.LIN_CATEGORIES.reduce(function(n, c) {
        return n + (c.modules || []).filter(function(m) { return m.active !== false; }).length;
      }, 0);
    }
    return 103;
  }

  function awaitingHtml(p, what) {
    return `<div class="ledger-head"><div>
        <p class="eyebrow">${esc(what)}</p>
        <h2>${esc(p.id)}</h2><p class="ledger-sub">${esc(p.name)}</p>
      </div></div>
      <div class="awaiting-state">
        <p><strong>Awaiting analysis.</strong> This project has no computed result yet.</p>
        <p class="kn-sub">Upload this project's documents. The server reads them, extracts the signal values, runs the analysis, and stores the result with the version, seed, and period cutoff it used. Nothing is shown here until that has happened, and nothing is fabricated in the meantime.</p>
      </div>`;
  }

  // T12b. The gate used to be hasSignals(p), which tests the legacy client-side
  // p.signals.evm/cusum/mc/doc blob — the same fault as the status legend. Here it was hiding
  // something worse: the function built a "rows" array from p.signals.evm.cpi, .mc.iterations,
  // .cusum.drift and .doc.score, and then NEVER USED IT. The rendered HTML comes entirely from
  // categoryLedgerHtml(p), which already reads the stored row through getCategoryStatus and
  // getModuleStatus. The dead array was the only reason the gate existed at all: building it
  // threw a TypeError the moment p.signals was undefined, so a project analysed server-side
  // with no legacy blob crashed here instead of rendering its (perfectly available) ledger.
  // The dead code is removed rather than repaired, since nothing read its output.
  function renderLedger(p, root = $("#ledger")) {
    if (!root) return;   // portfolio no longer hosts the ledger; only the detail page does
    if (!(window.LinResults && LinResults.hasResult(p))) {
      root.innerHTML = awaitingHtml(p, "Signal ledger");
      return;
    }
    const conflict = classifyConflict(p);

    // "Signal breakdown not available" is an honest abstention, not a finding, and must not
    // read as an alert next to the four real conflict findings.
    const conflictClass =
      conflict === "Agreement: low risk" ? "conflict-calm"
      : conflict === "Signal breakdown not available" ? "conflict-unknown"
      : "conflict-alert";

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

  /* 10-category signal ledger (gapless 1-10). Each row = one project-level
     category; the row pill is the worst-status-wins category status. Click
     expands the per-module list. Cat 8 (Governance, ex-Cat 9) is open by
     default. Portfolio Health (ex-"Cat 8" ML & AI) is portfolio-scale, not a
     numbered project category, so it renders as ONE separated row at the end
     linking to the Health dialog instead of an expandable module list. */
  function categoryLedgerHtml(p) {
    if (!window.LIN_CATEGORIES) return "";
    const projectCats = window.projectLevelCategories ? projectLevelCategories() : LIN_CATEGORIES.filter((c) => !(c && c.level === "portfolio"));
    const healthCat = LIN_CATEGORIES.find((c) => c && c.level === "portfolio");
    const rows = projectCats.map((cat) => {
      const status = window.getCategoryStatus ? getCategoryStatus(cat.id, p) : null;
      const open = cat.id === "cat9" ? " open" : "";   // Governance (now Cat 8) open by default
      const desc = esc(cat.description);
      const rowPill = statusPill(status);

      const secName = sectorName(p);
      const modRows = cat.modules.map((m) => {
        const st = window.getModuleStatus ? getModuleStatus(m.method_class, p) : null;
        const na = st === "NA";
        // Per-module chart, drawn only when the stored result holds a labelled
        // breakdown for this module. An abstaining module returns "" (no chart).
        const chart = (!na && window.LinModuleCharts)
          ? LinModuleCharts.chartHtmlFor(m.method_class, p) : "";
        return `<div class="cat-mod-row${na ? " cat-mod-na" : ""}"${na ? ` title="N/A: not applicable to ${esc(secName)}-sector projects"` : ""}>
          <span class="cat-mod-num">${esc(m.num)}</span>
          <span class="cat-mod-name">${esc(m.name)}</span>
          ${statusPill(st, secName + "-sector")}
        </div>${chart}`;
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

    // Portfolio Health — separated row, not part of the numbered 1-10 sequence.
    let healthRow = "";
    if (healthCat) {
      healthRow = `<div class="cat-row cat-row-health" data-cat="${esc(healthCat.id)}">
        <div class="cat-row-head">
          <span class="cat-row-num" style="color:${esc(healthCat.color)}">${esc(healthCat.num)}</span>
          <span class="cat-row-name">${esc(healthCat.name)}</span>
        </div>
        <p class="cat-row-desc">${esc(healthCat.description)} Portfolio-scale: compares this project against the rest of the portfolio, not a numbered project category.</p>
      </div>`;
    }
    return rows + healthRow;
  }

  function wireCategoryLedger(root) {
    // details/summary handles the 1-10 rows' toggling natively; the separated
    // Portfolio Health row is read-only prose, so there is nothing to wire.
    if (!root) return;
  }

  /* 6th ledger row — only when the simulation models have run for this project. */
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
        <p class="dc-note">Actions are deterministic governance rules traced to signal categories: recommendation only; a named human reviewer records the decision.</p>
      </div>`;
  }

  // T12b. Same fault, same fix as renderLedger above: the gate asked hasSignals(p) for the
  // legacy blob, but deriveDecision -> deriveHealthState reads the stored row through
  // getProjectFusion, and deriveDecision -> classifyConflict is now defensive against a missing
  // p.signals (see decision.js). Nothing left in this path needs the legacy blob to render.
  function renderDecisionCard(p, root = $("#decision-card")) {
    if (!root) return;   // portfolio no longer hosts the decision card; only the detail page does
    if (!(window.LinResults && LinResults.hasResult(p))) {
      root.innerHTML = awaitingHtml(p, "governance decision");
      return;
    }
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
           <p class="eyebrow">Governance decision</p>
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
       <p class="dc-note">Recommendation only: a named human reviewer records the decision. The recommendation does not trigger any action on its own.</p>`;

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
          alert("XLSX export not available: the SheetJS library failed to load.");
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
    selectedId = id || null;
    const p = id ? LIN_PROJECTS.find((x) => x.id === id) : null;
    if (!p) {
      // Deselecting (id falsy) or selecting an id that no longer resolves to a project
      // (e.g. it was archived out from under the selection) both land here. Either way,
      // the map/globe must not be left stranded pointed at whatever was selected last —
      // return to the portfolio-wide view rather than leaving the camera where it was.
      highlightBlip();
      highlightListItem();
      if (atlasViewActive()) resetAtlasView();
      if (globeViewActive()) resetGlobeView();
      return;
    }
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
    // Miami, Maria and Plain are all LIGHT themes; the shared light-theme component
    // rules key off this class so all three get dark headings, status-marker
    // outlines, yellow-pill dark ink, light spider axes, etc.
    document.body.classList.toggle(
      "t-light", theme === "light" || theme === "maria" || theme === "plain");
    // NOTE: there is deliberately no [data-set-theme] sweep here. Nothing in the DOM has ever
    // carried that attribute — the theme switcher is the fly-out pills built in openThemeFlyout(),
    // which set their own active state on open and on click. The dead selector that used to sit
    // here cost a session: grepping for [data-set-theme] found nothing and the switcher was
    // reported as missing. If a declarative switcher is ever added, wire it here.
    try {
      localStorage.setItem("lin-theme", theme);        // new primary key
      localStorage.setItem("lin-radar-theme", theme);  // legacy key (kept for back-compat)
    } catch (e) {}
    // Canvas renderers can't read var(), so re-resolve the status palette from
    // the new theme's CSS vars; they pick it up on their next draw.
    try { if (window.LIN_STATUS_COLORS) LIN_STATUS_COLORS.refresh(); } catch (e) {}
    // T9 Task 4. Same reason, same moment: the globe's palette is CSS vars it read at mount, so
    // every live globe repaints in place. After LIN_STATUS_COLORS.refresh(), because the point
    // colours it re-resolves are status colours.
    try { if (window.LinGlobe && LinGlobe.retheme) LinGlobe.retheme(); } catch (e) {}
    // T11. The atlas has almost nothing to do here — its fills are var() references, so the
    // cascade has already repainted it. Only the status letters' ink is a resolved colour and
    // has to be recomputed.
    try { if (window.LinAtlas && LinAtlas.retheme) LinAtlas.retheme(); } catch (e) {}
    onMapThemeChange();   // swap the OpenFreeMap dark/positron style if the map is live
  }

  /* ---------- the server is the authority on which theme renders ----------
     THIS IS NOT THE ENFORCEMENT. `themeset` is refused for a research account in
     features.py's gate_action, before dispatch, and audited. This function is what makes the
     refusal coherent to look at: it takes the server's answer, applies it, and records whether
     the account may change it so the fly-out can leave the pills out rather than offering four
     controls that would be refused.

     themeFixed defaults to TRUE, so a call that fails or has not returned yet leaves the
     switcher out. The failure direction matters: showing the control to a participant whose
     status would then be refused is worse than an operational user briefly not seeing it. */
  let themeFixed = true;
  async function syncThemeFromServer() {
    try {
      if (!window.LinStore || !LinStore.postWithTimeout) return;
      const token = (window.LinAuth && LinAuth.getToken && LinAuth.getToken()) || null;
      if (!token) return;                       // signed out: localStorage stands
      const r = await LinStore.postWithTimeout({ action: "themeget", session_token: token });
      if (!r || r.ok !== true || !r.theme) return;
      themeFixed = r.fixed === true;
      if (r.theme !== document.body.dataset.theme) applyTheme(r.theme);
      // A research account must not leave a chosen theme behind in this browser: the next load
      // paints from localStorage before the round trip, and a stale value would flash the wrong
      // stimulus at them every time.
      if (themeFixed) {
        try {
          localStorage.setItem("lin-theme", r.theme);
          localStorage.setItem("lin-radar-theme", r.theme);
        } catch (e) {}
      }
    } catch (e) { /* non-fatal: the server still refuses what it refuses */ }
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
  // Consolidation redirects: the standalone Signals/Manage pages folded into
  // Portfolio, and Knowledge + About merged into the tabbed Handbook. Old
  // routes (and deep-links) resolve to their new home; knowledge → Handbook's
  // Methods tab, about → the About tab.
  const PAGE_REDIRECT = { modules: "portfolio", manage: "portfolio", knowledge: "handbook", about: "handbook" };

  function showPage(page) {
    // navigating closes any open dock fly-out
    try { if (window.LinUI && LinUI.flyout) LinUI.flyout.close(); } catch (e) {}
    if (PAGE_REDIRECT[page]) {
      if (page === "knowledge") pendingHandbookTab = "methods";
      if (page === "about") pendingHandbookTab = "about";
      page = PAGE_REDIRECT[page];
    }
    // T9. Leaving detail releases its globe's WebGL context. The portfolio globe is handled by
    // setPortfolioView; each view tears down the instance it made.
    if (page !== "detail") { try { if (window.LinDetail && LinDetail.teardown) LinDetail.teardown(); } catch (e) {} }
    document.querySelectorAll(".page").forEach((s) =>
      s.toggleAttribute("hidden", s.dataset.page !== page));
    document.querySelectorAll("[data-nav]").forEach((b) =>
      b.classList.toggle("active", b.dataset.nav === page));
    // the pinned map card is fixed-positioned — never leave it over another page
    if (page !== "portfolio") hideMapCard();
    // (re)render content pages so they reflect the latest portfolio state.
    // Guarded so a single page-render error can never leave navigation half-done.
    try {
      if (page === "portfolio" && window.LinIngest) LinIngest.renderPortfolioAdmin();
      if (page === "handbook") renderHandbook();
      if (page === "auditor" && window.LinAuditor) LinAuditor.renderAuditorPage();
      if (page === "training" && window.LinTraining) LinTraining.render();
      if (page === "detail" && window.LinDetail && selectedId) LinDetail.render(selectedId);
      if (page === "admin" && window.LinAdmin) LinAdmin.render();
      // T6. The folded surfaces render on arrival like every other page here.
      if (page === "admin" && window.LinAdminOps) LinAdminOps.boot();
    } catch (e) {
      // The page is already visible, so navigation has succeeded and must stay succeeded — but
      // a swallowed render error is how a fatal ReferenceError left the detail page blank for
      // two days with a clean console. Report through the two shapes the codebase already has:
      // console.error, the per-item render shape (buildRadar, buildFallbackList), and
      // LinStore.banner, the user-visible non-fatal shape ("Couldn't reach the project store").
      console.error("Page render failed for", page, "—", e && e.message, e);
      try {
        if (window.LinStore && LinStore.banner) {
          LinStore.banner("The " + page + " page failed to render: " +
            ((e && e.message) || "unknown error") + ". The rest of the application still works.",
            "warn");
        }
      } catch (e2) { /* the banner must never turn a render failure into a nav failure */ }
    }
    window.scrollTo({ top: 0 });
  }

  /* ---------- Handbook: tabbed About + Methods (Knowledge) ----------
     Two pill tabs mirror the Radar|Map control (distinct .hb-tab class so the
     stage handlers don't pick them up). Tab choice persists in sessionStorage;
     a pending tab (set by an old about/knowledge deep-link) wins once. The
     Methods tab hosts the whole Knowledge Library, rendered lazily. */
  const HB_TAB_KEY = "lin-handbook-tab";
  let pendingHandbookTab = null;
  let knowledgeRendered = false;
  function setHandbookTab(tab) {
    tab = tab === "methods" ? "methods" : "about";
    document.querySelectorAll(".hb-tab").forEach((b) => {
      const on = b.dataset.tab === tab;
      b.classList.toggle("active", on);
      b.setAttribute("aria-selected", String(on));
    });
    const ap = document.getElementById("hb-panel-about");
    const mp = document.getElementById("hb-panel-methods");
    if (ap) ap.toggleAttribute("hidden", tab !== "about");
    if (mp) mp.toggleAttribute("hidden", tab !== "methods");
    if (tab === "methods" && window.LinKnowledge) {
      // render once; renderKnowledgePage resets its own selected topic each call
      if (!knowledgeRendered) { LinKnowledge.renderKnowledgePage(); knowledgeRendered = true; }
    }
    try { sessionStorage.setItem(HB_TAB_KEY, tab); } catch (e) {}
  }
  function renderHandbook() {
    let tab = pendingHandbookTab;
    pendingHandbookTab = null;
    if (!tab) { try { tab = sessionStorage.getItem(HB_TAB_KEY); } catch (e) {} }
    setHandbookTab(tab || "about");
  }
  function wireHandbookTabs() {
    document.querySelectorAll(".hb-tab").forEach((b) =>
      b.addEventListener("click", () => setHandbookTab(b.dataset.tab)));
  }

  // Destinations shown on the icon dock (the sole navigation). Each glyph is a
  // 26px stroke SVG, accent-colored, with a mono label that flies out to the
  // left on hover. data-nav drives showPage() + the shared .active sync.
  // Each glyph carries class hooks so CSS/SMIL can animate it (no JS loops):
  //  · radar  — .radar-sweep wedge rotates around (13,13); .radar-blip pulse.
  //  · doc    — a document sheet being scanned: .doc-scan line sweeps top→bottom
  //             inside the sheet on hover, the three .doc-line rows brighten in
  //             turn, and the .doc-check tick draws in (pathLength=1 + dashoffset)
  //             when the sweep completes; active = slow looping scan, tick drawn.
  //  · book   — CLOSED by default (.book-closed: cover + binding + page block +
  //             ribbon); on hover / focus / row-open / active it cross-fades to
  //             the open two-page spread (.book-open) while the cover swings on
  //             its spine hinge.
  const DOCK_NAV = [
    { nav: "portfolio", label: "PORTFOLIO",
      svg: '<circle cx="13" cy="13" r="9" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
           '<g class="radar-sweep">' +
             '<path d="M13 13 L13 4 A9 9 0 0 1 21 10 Z" fill="currentColor" opacity="0.28"/>' +
             '<line x1="13" y1="13" x2="13" y2="4" stroke="currentColor" stroke-width="1.4"/>' +
           '</g>' +
           '<circle class="radar-blip radar-blip-1" cx="16.5" cy="9" r="1.5" fill="currentColor"/>' +
           '<circle class="radar-blip radar-blip-2" cx="9.5" cy="16" r="1.5" fill="currentColor"/>' },
    { nav: "auditor", label: "TECHNICAL AUDITOR",
      svg: '<g class="doc">' +
             // portrait sheet with a folded (dog-ear) top-right corner
             '<path class="doc-body" d="M8 3.6 H15.4 L19.6 7.8 V21 Q19.6 22.4 18.2 22.4 H9.4 Q8 22.4 8 21 V5 Q8 3.6 9.4 3.6 Z" fill="currentColor" fill-opacity="0.10" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>' +
             '<path class="doc-fold" d="M15.4 3.6 V7.8 H19.6" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>' +
             // three text rows
             '<line class="doc-line doc-line-1" x1="10.4" y1="11" x2="17" y2="11" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>' +
             '<line class="doc-line doc-line-2" x1="10.4" y1="14" x2="17" y2="14" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>' +
             '<line class="doc-line doc-line-3" x1="10.4" y1="17" x2="14.6" y2="17" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>' +
             // review tick (lower-right), drawn once when the sweep completes
             '<path class="doc-check" d="M14.6 18.4 L16.2 20 L19.4 15.7" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" pathLength="1"/>' +
             // scan line (glow underlay + crisp line) sweeping down inside the sheet
             '<g class="doc-scan">' +
               '<line x1="6.4" y1="8" x2="21.2" y2="8" stroke="currentColor" stroke-width="3" opacity="0.16"/>' +
               '<line x1="6.4" y1="8" x2="21.2" y2="8" stroke="currentColor" stroke-width="1.2"/>' +
             '</g>' +
           '</g>' },
    // Hidden by default: features.js toggles body.og-no-training when the resolved `training`
    // flag is false (unset, disabled, or a research account, which always resolves false — see
    // server/app/features.py default_for_account). radar.css hides [data-nav="training"] on
    // that class, the same hook health_dialog and auditor already use.
    { nav: "training", label: "TRAIN",
      svg: '<path d="M13 4 L21 8.5 L13 13 L5 8.5 Z" fill="currentColor" fill-opacity="0.14" ' +
             'stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>' +
           '<path d="M8.4 10.6 V15.4 C8.4 17 10.4 18.3 13 18.3 C15.6 18.3 17.6 17 17.6 15.4 V10.6" ' +
             'fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>' +
           '<line x1="21" y1="8.5" x2="21" y2="15.4" stroke="currentColor" stroke-width="1.3" ' +
             'stroke-linecap="round"/>' },
    { nav: "handbook", label: "HANDBOOK",
      svg: '<g class="book">' +
             '<g class="book-closed">' +
               '<rect x="7" y="4.6" width="12" height="16.8" rx="2" fill="currentColor" fill-opacity="0.12" stroke="currentColor" stroke-width="1.5"/>' +
               '<line x1="10.2" y1="5.7" x2="10.2" y2="20.3" stroke="currentColor" stroke-width="1.3"/>' +
               '<line x1="19" y1="9.2" x2="20.7" y2="9.2" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>' +
               '<line x1="19" y1="13" x2="20.7" y2="13" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>' +
               '<path class="book-ribbon" d="M14.6 4.6 V7.9 L15.6 6.9 L16.6 7.9 V4.6" fill="none" stroke="currentColor" stroke-width="1.1" stroke-linejoin="round"/>' +
             '</g>' +
             '<g class="book-open">' +
               '<path d="M13 8 C10.3 6.5 7.7 6.3 5 6.6 L5 18.9 C7.7 18.6 10.4 18.9 13 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>' +
               '<path d="M13 8 C15.7 6.5 18.3 6.3 21 6.6 L21 18.9 C18.3 18.6 15.6 18.9 13 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>' +
               '<line x1="13" y1="8" x2="13" y2="20" stroke="currentColor" stroke-width="1.5"/>' +
               '<path d="M9.7 9.5 C8.4 9.4 7 9.5 5.9 9.9" fill="none" stroke="currentColor" stroke-width="1" opacity="0.65"/>' +
               '<path d="M16.3 9.5 C17.6 9.4 19 9.5 20.1 9.9" fill="none" stroke="currentColor" stroke-width="1" opacity="0.65"/>' +
             '</g>' +
           '</g>' }
  ];

  // The emblem menu button's inline SVG IS the shipping design — three bars
  // whose middle bar is a radar sweep line ending in a blip dot.
  const MENU_EMBLEM_SVG =
    '<svg class="menu-emblem-svg" viewBox="0 0 24 24" aria-hidden="true">' +
      '<path d="M4 7h16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>' +
      '<path d="M4 12h10" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>' +
      '<circle cx="17.4" cy="12" r="1.8" fill="currentColor"/>' +
      '<path d="M4 17h16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>' +
    '</svg>';

  // Optional in-place upgrade: if a Gemini menu_emblem.png is added to assets/
  // later, swap it into every emblem button. Absent today → the SVG ships.
  function tryEmblemUpgrade() {
    const img = new Image();
    img.onload = () => {
      document.querySelectorAll(".menu-emblem").forEach((b) =>
        b.innerHTML = '<img src="assets/menu_emblem.png" alt="" class="menu-emblem-img" />');
    };
    img.src = "assets/menu_emblem.png";
  }

  /* ---------- themes offered in the switcher ----------
     Gotham ("dark") is archived: renders if forced, but not offered here and
     not the default. Default is NYC — the remaining dark theme. */
  const DEFAULT_THEME = "plain";
  const OFFERED_THEMES = ["plain", "light", "newyork", "maria"];
  const THEME_META = [
    // Fairbanks is first because it is the one meant for working in. The other three
    // each have a mood; this one deliberately has none, and its title says so
    // rather than describing a place. The internal key stays "plain" (see
    // server/app/theme.py THEMES and body[data-theme="plain"] in radar.css): that string is
    // what is written to the stored preference and would need a migration to change, so only
    // the label shown to a user changes here.
    { key: "plain",   label: "Fairbanks", title: "Fairbanks: white, high contrast, no decoration" },
    { key: "light",   label: "Miami", title: "Miami: always sunny" },
    { key: "newyork", label: "NYC",   title: "NYC: aged bronze and gilt" },
    { key: "maria",   label: "Maria", title: "Maria: baby pink and white" }
  ];

  /* ============================================================
     LinUI — shared overlay infrastructure.
       · openModal(): a centered <dialog>-style modal (reuses the .ds-modal
         chrome) with focus trap, Escape, backdrop-click, first-field autofocus.
         The single overlay pattern for ALL four pills — Create, Upload,
         Archived, Activity.
       · toast(): brief inline confirmation.
     ============================================================ */
  function focusableIn(el) {
    return Array.prototype.slice.call(el.querySelectorAll(
      'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    )).filter((n) => n.offsetParent !== null || n === document.activeElement);
  }
  function trapTab(e, container) {
    if (e.key !== "Tab") return;
    const f = focusableIn(container);
    if (!f.length) return;
    const first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  }

  // toast(text, ok, action?) — action is an optional { label, onClick } that
  // renders a button inside the toast (used for "failed to save — retry"). A
  // toast carrying an action stays up longer and is not auto-dismissed until
  // its window elapses, so the user has time to act.
  function toast(text, ok, action) {
    let t = document.getElementById("lin-toast");
    if (!t) { t = document.createElement("div"); t.id = "lin-toast"; t.className = "lin-toast"; t.setAttribute("role", "status"); document.body.appendChild(t); }
    t.classList.toggle("toast-error", ok === false);
    clearTimeout(t._timer);
    if (action && action.label && typeof action.onClick === "function") {
      t.textContent = "";
      const span = document.createElement("span");
      span.textContent = text;
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "lin-toast-action";
      btn.textContent = action.label;
      btn.addEventListener("click", () => { t.classList.remove("show"); action.onClick(); });
      t.appendChild(span);
      t.appendChild(btn);
      t.classList.add("show");
      t._timer = setTimeout(() => t.classList.remove("show"), 10000);
    } else {
      t.textContent = text;
      t.classList.add("show");
      t._timer = setTimeout(() => t.classList.remove("show"), 4000);
    }
  }

  function openModal(opts) {
    const back = document.createElement("div");
    back.className = "app-modal-backdrop";
    back.innerHTML =
      '<div class="app-modal" role="dialog" aria-modal="true" aria-label="' + esc(opts.title || "Dialog") + '">' +
        '<button type="button" class="app-modal-x" aria-label="Close">×</button>' +
        '<h2 class="app-modal-title">' + esc(opts.title || "") + '</h2>' +
        '<div class="app-modal-body"></div>' +
      '</div>';
    document.body.appendChild(back);
    const panel = back.querySelector(".app-modal");
    const body = back.querySelector(".app-modal-body");
    const lastFocus = document.activeElement;
    let closed = false;
    // Optional dismissal guard: opts.canClose() returning false blocks Escape /
    // backdrop / × (used by the non-dismissable upload progress dialog); when
    // blocked, opts.onBlockedClose() runs instead (e.g. a "leave anyway?" prompt).
    function attemptClose(source) {
      if (opts.canClose && !opts.canClose()) { if (opts.onBlockedClose) opts.onBlockedClose(close, source); return; }
      close();
    }
    function close() {
      if (closed) return; closed = true;
      document.removeEventListener("keydown", onKey, true);
      back.classList.remove("open");
      const done = () => back.remove();
      if (reduceMotion()) done(); else setTimeout(done, 160);
      if (lastFocus && lastFocus.focus) try { lastFocus.focus(); } catch (e) {}
      if (opts.onClose) opts.onClose();
    }
    function onKey(e) {
      if (e.key === "Escape") { e.preventDefault(); attemptClose("escape"); }
      else trapTab(e, panel);
    }
    document.addEventListener("keydown", onKey, true);
    back.addEventListener("mousedown", (e) => { if (e.target === back) attemptClose("backdrop"); });
    back.querySelector(".app-modal-x").addEventListener("click", () => attemptClose("x"));
    if (opts.mount) opts.mount(body, close);
    requestAnimationFrame(() => back.classList.add("open"));
    const first = panel.querySelector('input, select, textarea, button:not(.app-modal-x)');
    if (first) try { first.focus(); } catch (e) {}
    return close;
  }

  /* ============================================================
     Flyout — an UNBOXED pill row that extends LEFT from a dock button.
     Reused by the theme switcher (§3) and the Portfolio actions (§4):
     parameterized, not duplicated. No enclosing container — each pill
     carries its own chrome (surface fill, gold hairline, mono label).
     Pills stagger 30ms apart (outward from the button) as they extend, and
     retract with the stagger reversed. Escape / click-outside / toggle close
     it; focus order follows visual order (left→right). Only ONE flyout row is
     open at a time — opening another replaces it (theme and actions are
     mutually exclusive). Reduced-motion → appear without slide/stagger (CSS). */
  const Flyout = (function () {
    let el = null, curKey = null, anchorEl = null, lastFocus = null, onCloseCb = null;
    function ensure() {
      if (el) return;
      el = document.createElement("div");
      el.className = "dock-flyout";
      el.setAttribute("role", "group");
      document.body.appendChild(el);
      document.addEventListener("click", (e) => {
        if (!curKey) return;
        if (el.contains(e.target)) return;
        if (e.target.closest && e.target.closest(".dock-flyout-trigger")) return;
        close();
      });
      document.addEventListener("keydown", (e) => {
        if (curKey && e.key === "Escape") { e.preventDefault(); close(); }
        else if (curKey && e.key === "Tab") trapTab(e, el);
      });
      window.addEventListener("resize", reposition, { passive: true });
      window.addEventListener("scroll", reposition, { passive: true });
    }
    function reposition() {
      if (!curKey || !anchorEl) return;
      const r = anchorEl.getBoundingClientRect();
      const mobile = window.matchMedia && window.matchMedia("(max-width: 700px)").matches;
      if (mobile) {
        // mobile bottom bar: extend UPWARD from the icon, centered horizontally.
        // Bottom touches the icon (visual gap comes from padding) so hover intent
        // isn't broken by a dead gap between the icon and the row.
        el.classList.add("flyout-up");
        el.style.left = (r.left + r.width / 2) + "px";
        el.style.bottom = (window.innerHeight - r.top) + "px";
        el.style.top = ""; el.style.right = "";
      } else {
        // desktop right-edge dock: extend LEFT, centered on the button. Right edge
        // meets the button's left edge (padding supplies the visual gap) so the
        // hover area is continuous from icon to pills.
        el.classList.remove("flyout-up");
        el.style.top = (r.top + r.height / 2) + "px";
        el.style.right = (window.innerWidth - r.left) + "px";
        el.style.left = ""; el.style.bottom = "";
      }
    }
    function open(key, anchor, pills, onClose) {
      ensure();
      if (curKey === key) { close(); return; }            // toggle
      onCloseCb = null;                                   // suppress prior row's onClose
      curKey = key; anchorEl = anchor; lastFocus = document.activeElement;
      onCloseCb = onClose || null;
      el.setAttribute("aria-label", key === "theme" ? "Visual theme" : "Portfolio actions");
      el.dataset.flyoutKey = key;
      el.innerHTML = "";
      const n = pills.length;
      pills.forEach((p, i) => {
        const b = document.createElement("button");
        b.type = "button";
        b.className = "flyout-pill" + (p.primary ? " primary" : "") +
          (p.active ? " active" : "") + (p.sep ? " sep" : "");
        b.textContent = p.label;
        if (p.title) b.title = p.title;
        if (p.badgeId || p.badge != null) {
          const bd = document.createElement("span");
          bd.className = "tool-badge";
          if (p.badgeId) bd.id = p.badgeId;
          const cnt = p.badge != null ? p.badge : 0;
          if (cnt > 0) bd.textContent = String(cnt); else bd.hidden = true;
          b.appendChild(bd);
        }
        // stagger outward from the button: rightmost (nearest) extends first
        b.style.setProperty("--fly-delay", ((n - 1 - i) * 30) + "ms");
        b.addEventListener("click", () => { if (p.onClick) p.onClick(b); });
        el.appendChild(b);
      });
      reposition();
      requestAnimationFrame(() => el.classList.add("open"));
      syncTriggers();
      const first = el.querySelector(".flyout-pill");
      if (first) try { first.focus(); } catch (e) {}
    }
    function close() {
      if (!curKey) return;
      curKey = null; anchorEl = null;
      el.classList.remove("open");
      syncTriggers();
      // Fire onClose BEFORE returning focus, so a trigger (e.g. the Portfolio
      // icon) can suppress its own focus-reopen when we refocus it here.
      const cb = onCloseCb; onCloseCb = null;
      if (cb) try { cb(); } catch (e) {}
      if (lastFocus && lastFocus.focus) try { lastFocus.focus(); } catch (e) {}
    }
    function syncTriggers() {
      document.querySelectorAll(".dock-flyout-trigger").forEach((b) => {
        const on = !!curKey && b.dataset.flyout === curKey;
        b.classList.toggle("active", on);
        b.setAttribute("aria-expanded", String(on));
      });
      // The Portfolio and Handbook nav icons own their rows but are NOT triggers
      // (their .active class marks the current page); keep only their aria in sync.
      document.querySelectorAll('.dock-nav-btn[data-nav="portfolio"], .dock-nav-btn[data-nav="handbook"]')
        .forEach((b) => b.setAttribute("aria-expanded", String(curKey === b.dataset.nav)));
    }
    return { open: open, close: close, current: () => curKey };
  })();

  // Theme fly-out (§3): Miami · NYC · Maria pills + a gap-separated Sign out.
  function openThemeFlyout(anchor) {
    const cur = document.body.dataset.theme;
    // A research account gets no theme pills at all: its theme is fixed on the server and every
    // pill would post an action that is refused. Sign out remains, so the row is never empty.
    const pills = (themeFixed ? [] : THEME_META.map((t) => ({
      label: t.label, title: t.title, active: t.key === cur,
      onClick: (btn) => {
        applyTheme(t.key);
        // Persist per account. applyTheme has already written localStorage, which is what
        // paints on the next load before the round trip; this is what makes the choice follow
        // the account to another machine. A failure here is not surfaced: the theme still
        // applied, and the next load falls back to this browser's copy.
        try {
          const token = (window.LinAuth && LinAuth.getToken && LinAuth.getToken()) || null;
          if (token && window.LinStore && LinStore.postWithTimeout) {
            LinStore.postWithTimeout({ action: "themeset", session_token: token, theme: t.key });
          }
        } catch (e) {}
        // keep the row open so the new active state reads; refresh actives
        anchor.ownerDocument.querySelectorAll(".dock-flyout .flyout-pill:not(.sep)")
          .forEach((x) => x.classList.toggle("active", x === btn));
      }
    })));
    pills.push({ label: "Sign out", sep: true, onClick: () => {
      Flyout.close();
      if (window.LinAuth && LinAuth.logout) LinAuth.logout();
    } });
    Flyout.open("theme", anchor, pills);
  }

  // Portfolio fly-out: the row that extends from the Portfolio dock icon. Its
  // FIRST pill navigates to the page (so the row is self-sufficient — nothing
  // depends on the icon's own click), followed by the four actions, each opening
  // its dialog (New Project, Upload, Archived, Activity — one modal pattern).
  // Archived carries its live count badge (id kept so renderPortfolioAdmin
  // refreshes it while the row is open).
  // When a nav-icon row closes it returns focus to that icon, which would
  // retrigger the icon's focus-to-open handler and reopen the row. This flag
  // (set via Flyout's onClose, before the refocus) suppresses that reopen for a
  // short window. Shared by the Portfolio and Handbook icons (only one row is
  // open at a time, so a single flag is sufficient). Read by wireDockFlyoutIcon.
  let dockSuppressFocusOpen = false;
  function suppressDockRefocus() {
    dockSuppressFocusOpen = true;
    setTimeout(() => { dockSuppressFocusOpen = false; }, 400);
  }
  function openPortfolioFlyout(anchor) {
    const A = window.LinIngest;
    const archivedCount = (window.LinStore && LinStore.cachedArchived)
      ? LinStore.cachedArchived().length : 0;
    const pills = [
      { label: "Portfolio", title: "Go to Portfolio", onClick: () => { Flyout.close(); showPage("portfolio"); } },
      { label: "+ New Project", primary: true, onClick: () => { Flyout.close(); if (A) A.openCreateModal(); } },
      // Upload is now per-project (inline Manage accordion + detail page), not a
      // global pill — Release 2 item 1. Removed here.
      { label: "Archived", badgeId: "tool-archived-badge", badge: archivedCount, onClick: () => { Flyout.close(); if (A) A.openArchivedModal(); } },
      { label: "Activity", onClick: () => { Flyout.close(); if (A) A.openActivityModal(); } }
    ];
    Flyout.open("portfolio", anchor, pills, suppressDockRefocus);
  }

  // Handbook fly-out: both pills land on the Handbook page with a tab preselected
  // (reusing the existing pendingHandbookTab deep-link consumed by renderHandbook).
  // No separate "Handbook" pill — both pills navigate to the page.
  function openHandbookFlyout(anchor) {
    const go = (tab) => { Flyout.close(); pendingHandbookTab = tab; showPage("handbook"); };
    const pills = [
      { label: "About the Platform", title: "Handbook: About", onClick: () => go("about") },
      // "and", not "&": NAMING_AUTHORITY.md, user-facing text uses the word. This pill and the
      // tab button in index.html are the same label and were spelled two different ways.
      { label: "Methods and Framework", title: "Handbook: Methods", onClick: () => go("methods") }
    ];
    Flyout.open("handbook", anchor, pills, suppressDockRefocus);
  }

  window.LinUI = { openModal: openModal, flyout: Flyout, toast: toast };

  function wireNav() {
    // Dock buttons are wired in initIconDock; this covers any other [data-nav].
    document.querySelectorAll("[data-nav]").forEach((b) => {
      if (b.closest("#icon-dock")) return;
      b.addEventListener("click", () => { showPage(b.dataset.nav); });
    });
  }

  /* ---------- T6: tabs inside the folded sections ----------
     These are tabs WITHIN a page, not navigation. They deliberately do not use [data-nav]:
     a tab is not a destination, it must not appear in the nav's active-state sync, and a
     participant must never be able to reach the decision sequence or a questionnaire by
     navigating rather than by working through the period. */
  function wireFoldedTabs() {
    const tabs = document.querySelectorAll("#admin-tabs button");
    tabs.forEach((btn) => {
      btn.addEventListener("click", () => {
        const name = btn.dataset.admintab;
        tabs.forEach((b) => b.classList.toggle("active", b === btn));
        // Derived from the tab bar rather than a hardcoded list of panel names. The list here
        // used to be ["users","projects","members","monitoring","export"], and a list written
        // in a second place is a list that goes stale: renaming a tab in the markup would have
        // left this loop toggling panels that no longer exist while never revealing the one
        // that does, with no error anywhere. Consolidating five tabs into two on 2026-08-02 is
        // exactly that rename.
        tabs.forEach((b) => {
          const panel = document.getElementById("admintab-" + b.dataset.admintab);
          if (panel) panel.classList.toggle("active", b === btn);
        });
        // Each admin tab loads its own data on first reveal, so opening Admin does not fire
        // every query a ResearchAdmin may not have wanted.
        try { if (window.LinAdminOps) LinAdminOps.showTab(name); } catch (e) { /* non-fatal */ }
      });
    });
  }

  /* ---------- icon dock — the SOLE navigation ----------
     Fixed to the right edge, vertically centered, ALWAYS visible (subtle 70%
     at the top, full once scrolled). Top: the animated radar-sweep emblem
     (scroll-to-top, and its visibility stays scroll-gated). Middle: the three
     destination icons with left-flyout labels + active notch. Bottom: the
     emblem menu button, opening the theme fly-out (Miami · NYC · Maria + sign out).
     On ≤700px it becomes a horizontal bottom bar. */
  function initIconDock() {
    if (document.getElementById("icon-dock")) return;
    const el = document.createElement("div");
    el.id = "icon-dock";
    el.className = "icon-dock";
    el.innerHTML =
      '<button type="button" class="dock-emblem" title="Back to top" aria-label="Scroll back to top">' +
        '<img src="logo.png" alt="" />' +
        '<span class="logo-sweep" aria-hidden="true"></span>' +
      '</button>' +
      '<nav class="dock-nav" aria-label="Primary navigation">' +
        DOCK_NAV.map((d) =>
          `<button type="button" class="dock-nav-btn" data-nav="${d.nav}" aria-label="${d.label}">` +
            `<svg class="dock-icon" viewBox="0 0 26 26" aria-hidden="true">${d.svg}</svg>` +
            `<span class="dock-label">${d.label}</span>` +
          `</button>`).join("") +
      '</nav>' +
      '<button type="button" class="dock-menu menu-emblem dock-flyout-trigger" data-flyout="theme"' +
        ' aria-label="Theme and account menu" aria-expanded="false" aria-haspopup="true">' +
        MENU_EMBLEM_SVG +
      '</button>';
    document.body.appendChild(el);

    el.querySelector(".dock-emblem").addEventListener("click", () =>
      window.scrollTo({ top: 0, behavior: reduceMotion() ? "auto" : "smooth" }));
    // Destination icons navigate on click. Portfolio and Handbook are special
    // (see wireDockFlyoutIcon): they still navigate on mouse/keyboard, but each
    // also owns a fly-out row. Technical Auditor keeps a plain click-to-navigate
    // + its label flyout (no sub-destinations).
    el.querySelectorAll(".dock-nav-btn").forEach((b) => {
      if (b.dataset.nav === "portfolio" || b.dataset.nav === "handbook") return;
      b.addEventListener("click", () => { showPage(b.dataset.nav); });
    });
    el.querySelector(".dock-menu").addEventListener("click", (e) => {
      e.stopPropagation();
      openThemeFlyout(e.currentTarget);
    });
    wireDockFlyoutIcon(el.querySelector('.dock-nav-btn[data-nav="portfolio"]'),
      "portfolio", openPortfolioFlyout, () => showPage("portfolio"));
    wireDockFlyoutIcon(el.querySelector('.dock-nav-btn[data-nav="handbook"]'),
      "handbook", openHandbookFlyout, () => showPage("handbook"));

    // Always visible; the emblem (scroll-to-top) stays scroll-gated, and the
    // whole dock lifts to full opacity once past the header.
    const onScroll = () => el.classList.toggle("scrolled", window.scrollY > 120);
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    tryEmblemUpgrade();

    // Ambient dock loops run continuously (CSS-only). Pause them all when the
    // tab is backgrounded — perpetual loops on a hidden tab drain battery for
    // no benefit. One class toggle drives every ambient animation's play-state.
    const reflectDockPaused = () => document.body.classList.toggle("dock-idle-paused", document.hidden);
    document.addEventListener("visibilitychange", reflectDockPaused);
    reflectDockPaused();
  }

  /* ---------- dock nav icon that ALSO owns a fly-out row (Portfolio, Handbook) ----------
     ONE generic path (not per-icon): the icon keeps its primary job (click →
     navigate) while owning a row. Resolution of the two jobs:
       · Hover (pointer devices) → row flies out; leaving icon+row retracts it.
       · Focus (keyboard) → row appears; focus leaving icon+row retracts it;
         Escape retracts + returns focus to the icon (handled in Flyout).
       · Click on mouse/keyboard → navigate (the row was already open via
         hover/focus, and its pills also navigate — self-sufficient).
       · Touch (no hover) → tap toggles the row; a pill navigates.
     `key` is the Flyout key, `openFn(btn)` builds the row, `navFn()` is the
     icon's click navigation. */
  function wireDockFlyoutIcon(btn, key, openFn, navFn) {
    if (!btn) return;
    btn.setAttribute("aria-haspopup", "true");
    btn.setAttribute("aria-expanded", "false");
    const canHover = () => !window.matchMedia || window.matchMedia("(hover: hover)").matches;
    let lastPointer = "mouse", lastPointerAt = 0, closeTimer = null;
    const flyoutEl = () => document.querySelector(".dock-flyout");
    const isOpen = () => Flyout.current() === key;
    const openRow = () => { if (!isOpen()) openFn(btn); btn.setAttribute("aria-expanded", "true"); };
    const cancelClose = () => { if (closeTimer) { clearTimeout(closeTimer); closeTimer = null; } };
    const scheduleClose = () => {
      cancelClose();
      closeTimer = setTimeout(() => { if (isOpen()) Flyout.close(); btn.setAttribute("aria-expanded", "false"); }, 220);
    };

    btn.addEventListener("pointerdown", (e) => { lastPointer = e.pointerType || "mouse"; lastPointerAt = Date.now(); });

    // Hover opens (pointer devices only). Closing is handled by the document-level
    // mouseout below, which treats the icon + row as one hover group (via
    // relatedTarget) so crossing between them never triggers a spurious close.
    btn.addEventListener("mouseenter", () => { if (canHover()) { cancelClose(); openRow(); } });

    // KEYBOARD focus opens. The suppress flag skips the reopen when the row's own
    // close returned focus here. A pointer-driven focus (a tap or click just
    // moved focus here) is handled by the click/hover paths — only open on
    // keyboard focus, i.e. no recent pointerdown (focus-visible heuristic).
    btn.addEventListener("focus", () => {
      if (dockSuppressFocusOpen) return;
      const pointerDriven = (Date.now() - lastPointerAt) < 600;
      if (!pointerDriven) openRow();
    });
    btn.addEventListener("focusout", (e) => {
      if (!isOpen()) return;
      const to = e.relatedTarget;
      const row = flyoutEl();
      if (to && (btn.contains(to) || (row && row.contains(to)))) return;
      Flyout.close(); btn.setAttribute("aria-expanded", "false");
    });
    document.addEventListener("focusin", (e) => {
      if (!isOpen()) return;
      const row = flyoutEl();
      if (btn.contains(e.target) || (row && row.contains(e.target))) return;
      Flyout.close(); btn.setAttribute("aria-expanded", "false");
    });

    // Click: navigate on mouse/keyboard; toggle the row on touch
    btn.addEventListener("click", (e) => {
      if (lastPointer === "touch" || lastPointer === "pen") {
        e.preventDefault(); e.stopPropagation();
        if (isOpen()) { Flyout.close(); btn.setAttribute("aria-expanded", "false"); }
        else openRow();
        return;
      }
      navFn();   // mouse / keyboard keep the icon's primary job
    });

    // Keep the row hovered without it collapsing when the pointer crosses the gap
    document.addEventListener("mouseover", (e) => {
      if (!isOpen() || !canHover()) return;
      const row = flyoutEl();
      if (row && (row.contains(e.target) || btn.contains(e.target))) cancelClose();
    });
    document.addEventListener("mouseout", (e) => {
      if (!isOpen() || !canHover()) return;
      const row = flyoutEl();
      const to = e.relatedTarget;
      if (!row) return;
      const leaving = (row.contains(e.target) || btn.contains(e.target));
      const stayingInside = to && (row.contains(to) || btn.contains(to));
      if (leaving && !stayingInside) scheduleClose();
    });
  }

  /* The header hamburger and the stage toolbar's action buttons are gone: the
     Portfolio dock icon owns the actions row (New Project / Upload / Archived /
     Activity — all dialogs), the Handbook icon owns its tab row, and the menu
     button owns the theme fly-out — all wired in initIconDock. */

  /* The on-page "Portfolio Intelligence" section (Release 2 item 12) is retired.
     Portfolio Health now reads from each project's own stored result in the
     "Portfolio health" card on the portfolio page (renderPortfolio in
     workspace.js). The former live-recompute dialog was removed: it depended on
     deepdive.js, which the application does not load, so its control was a
     silent no-op. */

  /* Thin indeterminate top progress bar for the first cold load (no cache). */
  function showTopProgress() {
    let bar = document.getElementById("top-progress");
    if (!bar) {
      bar = document.createElement("div");
      bar.id = "top-progress";
      bar.className = "top-progress";
      bar.innerHTML = '<div class="top-progress-fill"></div>';
      document.body.appendChild(bar);
    }
    bar.hidden = false;
  }
  function hideTopProgress() {
    const bar = document.getElementById("top-progress");
    if (bar) bar.hidden = true;
  }

  /* Determinate progress overlay for Recompute-all — a small banner pinned to
     the radar stage ("Recomputing signals... project n of N" + a determinate
     bar). Non-blocking: it sits at the top of the stage and the rest of the
     page stays interactive. */
  function showRecomputeOverlay(total) {
    const stage = document.querySelector('.page[data-page="portfolio"] .radar-panel') || document.querySelector(".radar-panel");
    if (!stage) return null;
    // Reset any leftover overlay from a previous run so we never orphan a robot.
    const prev = document.getElementById("recompute-overlay");
    if (prev && prev.parentNode) prev.parentNode.removeChild(prev);
    const ov = document.createElement("div");
    ov.id = "recompute-overlay";
    ov.className = "recompute-overlay";
    if (getComputedStyle(stage).position === "static") stage.style.position = "relative";
    stage.appendChild(ov);
    // 'computing' robot, determinate from the real n-of-N loop counter.
    const robot = (window.LinWorkingRobot && LinWorkingRobot.mount)
      ? LinWorkingRobot.mount(ov, {
          variant: "computing", size: "md",
          message: "Recomputing signals, please wait.", progress: 0
        })
      : null;
    const removeOv = () => { if (ov.parentNode) ov.parentNode.removeChild(ov); };
    return {
      update(done, n, id) {
        const at = Math.min(done + 1, n);
        if (robot) robot.update({
          message: "Recomputing signals, project " + at + " of " + n + (id ? " (" + id + ")" : ""),
          progress: n ? done / n : null
        });
      },
      done() {
        if (robot) { robot.update({ message: "Recompute complete.", progress: 1 }); robot.tick(); }
        setTimeout(() => { if (robot) robot.destroy(); removeOv(); }, 1200);
      },
      // Error/abort path — always tear the robot down, never orphan it.
      destroy() { if (robot) robot.destroy(); removeOv(); }
    };
  }

  /* ---------- "Recompute all signals" button ----------
     Runs the full 101-computation set for every ingested project from stored
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
      const confirmed = window.confirm(
        "Rebuild signals (repair)\n\n" +
        "This re-runs local computation for all " + projects.length + " project" + (projects.length === 1 ? "" : "s") +
        " and refreshes Portfolio Health from the results already on file.\n\n" +
        "No AI calls, no document re-extraction: extraction results already on file are reused. " +
        "This is the only tool that recomputes everything at once; use it if signals look stale or out of sync.\n\n" +
        "Continue?"
      );
      if (!confirmed) return;
      btn.disabled = true;
      const overlay = showRecomputeOverlay(projects.length);   // determinate stage overlay (non-blocking)
      let done = 0;
      let completed = false;
      try {
      for (const p of projects) {
        if (overlay) overlay.update(done, projects.length, p.id);
        status.textContent = "Recomputing " + (done + 1) + " / " + projects.length + "…";
        try {
          const full = await LinStore.getProject(p.id);
          if (!full || !full.signalInputs) { done++; continue; }
          const si = LinSignals.deriveExtendedFields(LinSignals.resolveSimInputs(full));
          const hasCpi = si.cpi != null && Number.isFinite(Number(si.cpi)) && Number(si.cpi) > 0;
          const hasSpi = si.spi != null && Number.isFinite(Number(si.spi)) && Number(si.spi) > 0;
          if (!hasCpi && !hasSpi) { done++; continue; }
          await LinSignals.runModels(full, si);
          clearSectorDirty(full.id);                          // recompute clears the sector-changed flag
        } catch (e) {
          console.warn("[recompute-all] project " + p.id + ":", e && e.message);
        }
        done++;
        if (overlay) overlay.update(done, projects.length);
      }
      completed = true;
      if (overlay) overlay.done();                             // done() self-destroys the robot after a beat
      status.textContent = "Done: recomputed " + done + " project" + (done === 1 ? "" : "s") + ".";
      } finally {
        // Never orphan the robot: if the loop aborted before done(), tear it down.
        if (!completed && overlay) overlay.destroy();
        btn.disabled = false;
      }
      // Refresh the slim portfolio cache so the radar/list reflect the newly
      // computed statuses (and the cache isn't stale on the next cold load).
      if (window.LinApp) LinApp.refreshPortfolio();
    });
  })();

  /* ---------- public API (used by ingest.js) ---------- */
  window.LinApp = {
    // 2026-08-05. Exposed so auth.js can resolve the account's real theme (and, for a research
    // account, apply the New York pin) BEFORE the consent gate, not only after `init()` runs.
    // See the call site in auth.js's routeFromView for why: LinApp.init() — and with it
    // syncThemeFromServer, previously the only caller of applyTheme with the server's answer —
    // is skipped entirely while a research participant is on the consent screen, so that screen
    // used to render whatever the OPERATIONAL default happened to be. That was invisible while
    // DEFAULT_THEME and RESEARCH_THEME were both "newyork"; decoupling them on 2026-08-04 made it
    // a real, silent violation of "every participant sees identical stimulus" for the one screen
    // every research participant sees first. Idempotent and safe to call twice (once here, once
    // again inside init() once consent is granted): it only re-fetches and re-applies.
    syncTheme: syncThemeFromServer,
    refresh() {
      buildRadar(); buildFallbackList(); renderStatusLegend();
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
    // Exposed for tests_render.html / a Playwright harness so the Map/Globe flyTo behaviour
    // can be driven and read back without a real network. Not used by production UI code,
    // which reaches these through wireViewToggle()'s own listeners.
    setPortfolioView,
    wireViewToggle,
    getGlMap() { return glMap; },
    getPortfolioGlobe() { return portfolioGlobe; },
    // Re-key the cached selection after a project-number change (setprojectnumber)
    // so the detail page / highlights keep pointing at the renamed project.
    renameSelection(oldId, newId) { if (selectedId === oldId) selectedId = newId; },
    // called by auth.js after a successful sign-in
    init,
    // shared renderers, reused by the Project Detail page (detail.js)
    renderLedger,
    renderDecisionCard,
    // T13. Exposed for tests_render.html, the stored-result render regression net. These three
    // are exactly the paths the hasSignals() gates broke, and all three were unreachable from
    // outside this module, which is part of why nine such bugs passed 854 checks. They are
    // internal renderers with no side effects beyond the DOM node they are handed or look up,
    // so exporting them widens the surface without widening the behaviour.
    stateLabel,
    buildFallbackList,
    renderStatusLegend,
    // sector-changed flag hooks (Release 2 · editable project type)
    markSectorDirty, clearSectorDirty, isSectorDirty
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
      el.innerHTML = '<span style="color:var(--faint)">Summary unavailable: chat endpoint not configured.</span>';
      return;
    }
    // Shape-tolerant per-project state/metrics: full projects carry
    // signals.decision + signalInputs; SLIM rows (listslim) expose a precomputed
    // status label and top-level cpi/spi. Without the slim fallbacks the summary
    // reported every project as "unknown" with 0 red/amber and no CPI/SPI context.
    const projState = (p) => {
      const s = p.signals || {};
      if (s.decision && s.decision.state) return s.decision.state;
      if (p && p.slim && typeof slimStatusLabel === "function") {
        const lab = slimStatusLabel(p);
        if (lab) return lab;
      }
      return p.status || "unknown";
    };
    const projMetric = (p, k) => {
      const si = p.signalInputs || {};
      return Number(si[k] != null ? si[k] : p[k]);
    };
    const projectLines = projects.map((p) => {
      const state = projState(p);
      const cpi = projMetric(p, "cpi"), spi = projMetric(p, "spi");
      return p.id + " " + p.name + " (" + (p.sector || "unknown") + "): state=" + state +
        (Number.isFinite(cpi) ? ", cost performance " + (cpi >= 0.95 ? "on budget" : cpi >= 0.90 ? "slightly over" : "over budget") : "") +
        (Number.isFinite(spi) ? ", schedule " + (spi >= 0.95 ? "on track" : spi >= 0.90 ? "slightly behind" : "behind") : "");
    }).join("\n");
    const redCount = projects.filter((p) => String(projState(p)).indexOf("Red") >= 0).length;
    const amberCount = projects.filter((p) => projState(p) === "Amber").length;

    const prompt = "You are a senior program controls advisor writing a portfolio-level executive summary for a program director." +
      "\n\nPortfolio: " + projects.length + " active projects. " + redCount + " in red-review, " + amberCount + " amber, " +
      (projects.length - redCount - amberCount) + " green or better." +
      "\n\nProject signals:\n" + projectLines +
      "\n\nWrite a portfolio executive summary with exactly three sections:\n\n" +
      "PROJECT STATUS AT A GLANCE\n" +
      "One bullet per project. One sentence each. Plain English. No metric values. No module numbers. " +
      'Format: "Project [ID], [Name]: [one sentence]"\n\n' +
      "PORTFOLIO-LEVEL RECOMMENDATIONS\n" +
      "3-5 bullet points. Advisory tone: suggest, recommend, consider. Portfolio-level observations only, not project-specific actions. Look for patterns across projects.\n\n" +
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
      el.innerHTML = '<span style="color:var(--faint)">Summary unavailable: check connection, then press Generate.</span>';
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
    // Theme buttons are built inside the theme fly-out (wired there); nothing to
    // bind here at load. Offered themes: Fairbanks (plain) · Miami (light) · NYC
    // (newyork) · Maria. Gotham ("dark") is ARCHIVED — still renders if forced via
    // applyTheme, but no longer offered or used as a default. 2026-08-04: DEFAULT
    // changed newyork → plain (Fairbanks). A persisted "dark" falls through to the
    // default; "clean"→light and the removed "cyberpunk"→default as before.
    let stored = DEFAULT_THEME;
    try {
      stored = localStorage.getItem("lin-theme")
            || localStorage.getItem("lin-radar-theme")
            || DEFAULT_THEME;
    } catch (e) {}
    if (stored === "clean") stored = "light";
    if (stored === "cyberpunk") stored = DEFAULT_THEME;   // theme removed
    if (stored === "dark") stored = DEFAULT_THEME;         // Gotham archived → NYC
    const saved = OFFERED_THEMES.includes(stored) ? stored : DEFAULT_THEME;
    applyTheme(saved);
    // ...then ask the server, which is the authority. localStorage paints first so the page
    // does not flash a default before the round trip returns; the server's answer replaces it.
    // For a research account that answer is the FIXED theme regardless of what this browser has
    // stored, which is the whole point: a participant who had once chosen a theme, or who is
    // using a machine where somebody else did, still sees the study's stimulus.
    syncThemeFromServer();

    wireNav();
    initIconDock();
    wireHandbookTabs();
    wireTzSelect();
    startClock();
    // Show the signed-in user's email in the top bar (auth.js / Stage 1).
    try {
      const emailEl = document.getElementById("auth-email-display");
      if (emailEl && window.LinAuth && LinAuth.getEmail) emailEl.textContent = LinAuth.getEmail() || "";
    } catch (e) { /* non-fatal */ }
    showPage("portfolio");
    renderDecisionLog();

    // T6. The folded surfaces boot here, after auth has settled, rather than from their own
    // DOMContentLoaded handlers — those would have raced the login screen and rendered a
    // workspace behind it. Each is guarded independently so one failing cannot stop the others,
    // and none of them is required for the legacy dashboard to work.
    try { if (window.LinWorkspace) LinWorkspace.boot(); } catch (e) { /* non-fatal */ }
    // The participant profile: shown once, after consent, before the first decision. It decides
    // for itself whether it is needed by asking the server, so this call is idempotent and a
    // returning participant never sees it.
    try { if (window.LinProfile) LinProfile.maybePrompt(); } catch (e) { /* non-fatal */ }
    wireFoldedTabs();

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
        renderStatusLegend();
        if (LIN_PROJECTS.length) selectProject(LIN_PROJECTS[0].id);
        setListRefreshing(true);
        paintedFromCache = true;
      } else {
        renderSkeleton();
        showTopProgress();   // first-ever cold load (no cache): thin indeterminate top bar
      }
    } catch (e) { /* first paint is best-effort */ }

    // Background revalidate from the slim endpoint (falls back to full list on 404).
    try {
      if (LinStore.loadSlim) await LinStore.loadSlim();
      else await LinStore.load();
    } catch (e) { /* store shows its own banner */ }
    setListRefreshing(false);
    hideTopProgress();

    buildRadar();
    buildFallbackList();
    renderStatusLegend();

    // T11. Radar | Map | Globe — MAP is the default, and it is the flat SVG atlas. A persisted
    // "map" from before this change resolves to the atlas rather than to MapLibre, which is the
    // better of the two for anyone who chose it.
    //
    // THE MAPLIBRE WARM-UP IS GONE. It used to fetch maplibre-gl (773 KB + 64 KB of CSS) and
    // open a connection to tiles.openfreemap.org on idle, on the DEFAULT path, for a view the
    // user had not asked for. That was the largest single reason the default path touched an
    // off-origin host at all. Nothing warms anything now: the atlas needs only geometry that is
    // already vendored, and the globe's assets load when the globe is selected and not before.
    wireViewToggle();
    // T11b. GLOBE is the default for a user with no stored preference. It was Map while nobody
    // had ever seen the globe render and a black sphere in front of a director could not be ruled
    // out; the globe has since been confirmed by eye, so that argument no longer holds. Map stays
    // available as its own view and remains what the globe falls back to when WebGL is missing or
    // the scene never builds, so the safety property is unchanged — only the starting point.
    let savedView = "globe";
    try { savedView = localStorage.getItem(VIEW_KEY) || "globe"; } catch (e) {}
    setPortfolioView(savedView, false);

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
