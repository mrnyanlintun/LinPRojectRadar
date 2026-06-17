/* ============================================================
   Lin Project Radar — app.js
   Radar rendering, theme switching, signal ledger,
   PCEIF decision card, audit export.
   Depends on (load order): data.js, decision.js, app.js
   ============================================================ */

(function () {
  "use strict";

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
    green: "var(--clear-green)",
    amber: "var(--radar-amber)",
    red:   "var(--alarm-red)"
  };

  const SVG_NS = "http://www.w3.org/2000/svg";
  const CENTER = 200;          // viewBox is 400x400
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
    const sec = SECTORS[project.sector];
    let h = 0;
    for (let i = 0; i < project.id.length; i++) h = (h * 31 + project.id.charCodeAt(i)) >>> 0;
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
  function statusKey(p) {
    if (!hasSignals(p)) return "empty";
    return deriveHealthState(p).toLowerCase().replace("-review", "");
  }
  function stateLabel(p) {
    return hasSignals(p) ? deriveHealthState(p) : "Awaiting ingest";
  }
  // health proxy → radius band, so distance still reads as drift:
  // green near center, amber mid, red outer. Empty sits at a neutral mid-ring.
  function proxyHealth(p) {
    switch (statusKey(p)) {
      case "green": return 85;   // inside green zone
      case "amber": return 55;   // inside amber ring
      case "red":   return 25;   // inside red-review ring
      default:      return 50;   // empty → neutral radius (rendered hollow/grey)
    }
  }

  function polar(angleDeg, radius) {
    const a = (angleDeg * Math.PI) / 180;
    return { x: CENTER + radius * Math.cos(a), y: CENTER + radius * Math.sin(a) };
  }

  /* ---------- radar scope ---------- */
  function buildRadar() {
    const svg = $("#radar-svg");
    svg.innerHTML = "";

    const R = R_MAX; // 165.6 — outer edge

    // ── defs: sweep-trail gradient ───────────────────────────────────────
    const defs = el("defs");
    const trailGrad = el("radialGradient", {
      id: "sweep-trail-grad", gradientUnits: "userSpaceOnUse",
      cx: CENTER, cy: CENTER, r: R
    });
    const tg1 = el("stop"); tg1.setAttribute("offset", "0%"); tg1.setAttribute("stop-color", "var(--phosphor)"); tg1.setAttribute("stop-opacity", "0");
    const tg2 = el("stop"); tg2.setAttribute("offset", "100%"); tg2.setAttribute("stop-color", "var(--phosphor)"); tg2.setAttribute("stop-opacity", "0.4");
    trailGrad.appendChild(tg1); trailGrad.appendChild(tg2);
    defs.appendChild(trailGrad);
    svg.appendChild(defs);

    // ── scope background (dark CRT surface, no colored zone bands) ───────
    svg.appendChild(el("circle", {
      cx: CENTER, cy: CENTER, r: R,
      fill: "rgba(0,8,18,0.92)"
    }));

    // ── 4 faint concentric range rings ───────────────────────────────────
    for (let i = 1; i <= 4; i++) {
      svg.appendChild(el("circle", {
        cx: CENTER, cy: CENTER, r: R * i / 4,
        fill: "none",
        stroke: "rgba(96,210,232,0.12)",
        "stroke-width": "0.5"
      }));
    }

    // ── outer solid ring ─────────────────────────────────────────────────
    svg.appendChild(el("circle", {
      cx: CENTER, cy: CENTER, r: R,
      fill: "none",
      stroke: "rgba(96,210,232,0.35)",
      "stroke-width": "1.2"
    }));

    // ── threshold rings: Green / Amber / Red ─────────────────────────────
    const THRESHOLD_RINGS = [
      { frac: 0.33, stroke: "#3fcaa6", label: "On track" },
      { frac: 0.66, stroke: "#e2b13c", label: "Watch"    },
      { frac: 0.90, stroke: "#e0556b", label: "Escalate" },
    ];
    THRESHOLD_RINGS.forEach(({ frac, stroke, label }) => {
      const rr = R * frac;
      svg.appendChild(el("circle", {
        cx: CENTER, cy: CENTER, r: rr,
        fill: "none",
        stroke,
        "stroke-opacity": "0.4",
        "stroke-width": "1"
      }));
      const t = el("text", {
        x: CENTER + rr + 4, y: CENTER,
        "text-anchor": "start",
        "font-size": "8",
        fill: stroke,
        opacity: "0.65",
        "dominant-baseline": "middle",
        class: "scope-deg-label"
      });
      t.textContent = label;
      svg.appendChild(t);
    });

    // ── 12 radial lines every 30° ─────────────────────────────────────────
    for (let deg = 0; deg < 360; deg += 30) {
      const tip = polar(deg, R);
      svg.appendChild(el("line", {
        x1: CENTER, y1: CENTER, x2: tip.x, y2: tip.y,
        stroke: "rgba(96,210,232,0.08)",
        "stroke-width": "0.5"
      }));
    }

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
      const tipA = polar(0, R);   // East  (365.6, 200)
      const tipB = polar(-60, R); // NE    (282.8,  56.5)
      sweepG.appendChild(el("path", {
        d: `M ${CENTER} ${CENTER} L ${tipA.x.toFixed(1)} ${tipA.y.toFixed(1)} A ${R.toFixed(1)} ${R.toFixed(1)} 0 0 0 ${tipB.x.toFixed(1)} ${tipB.y.toFixed(1)} Z`,
        fill: "url(#sweep-trail-grad)"
      }));

      // sweep line: from center (cx,cy) to outer edge at 0° (East)
      sweepG.appendChild(el("line", {
        x1: CENTER, y1: CENTER,
        x2: tipA.x.toFixed(1), y2: tipA.y.toFixed(1),
        stroke: "var(--phosphor)", "stroke-width": "1.5", opacity: "0.9"
      }));

      // SMIL rotation — pivot explicitly at (CENTER, CENTER) in user coords
      const anim = document.createElementNS(SVG_NS, "animateTransform");
      anim.setAttribute("attributeName", "transform");
      anim.setAttribute("type", "rotate");
      anim.setAttribute("from", `0 ${CENTER} ${CENTER}`);
      anim.setAttribute("to", `360 ${CENTER} ${CENTER}`);
      anim.setAttribute("dur", "4s");
      anim.setAttribute("repeatCount", "indefinite");
      sweepG.appendChild(anim);

      svg.appendChild(sweepG);
    }

    // ── blips — two passes (collision jitter + label nudge) ──────────────
    const BAND_EDGES = [R_MIN - 6, 0.34 * 180, 0.62 * 180, R_MAX + 2];

    const plots = LIN_PROJECTS.map((p) => {
      const ang = hashAngle(p);
      return { p, ang, r: healthToRadius(proxyHealth(p)) };
    });

    // pass 1: dot collision jitter (deterministic by list order)
    const placedDots = [];
    plots.forEach((q) => {
      let pos = polar(q.ang, q.r);
      const lo = Math.max(...BAND_EDGES.filter((e) => e < q.r)) + 3;
      const hi = Math.min(...BAND_EDGES.filter((e) => e >= q.r)) - 3;
      let tries = 0;
      while (placedDots.some((d) => Math.hypot(d.x - pos.x, d.y - pos.y) < 12) && tries < 8) {
        tries++;
        const dir = tries % 2 ? 1 : -1;
        const r2 = Math.min(hi, Math.max(lo, q.r + dir * 6 * Math.ceil(tries / 2)));
        pos = polar(q.ang, r2);
      }
      q.x = pos.x; q.y = pos.y;
      placedDots.push(pos);
    });

    // pass 2: label collision avoidance (sorted vertical pass)
    const LABEL_W = 58, LABEL_H = 11;
    plots.forEach((q) => { q.lx = q.x + 14; q.ly = q.y + 5; });
    const byY = plots.slice().sort((a, b) => a.ly - b.ly);
    byY.forEach((q, i) => {
      let moved = true, guard = 0;
      while (moved && guard < 20) {
        moved = false; guard++;
        for (let j = 0; j < i; j++) {
          const o = byY[j];
          if (Math.abs(o.lx - q.lx) < LABEL_W && Math.abs(o.ly - q.ly) < LABEL_H) {
            q.ly = o.ly + LABEL_H; moved = true;
          }
        }
      }
    });

    // Sector-specific blip icons (stroke-based, 24-unit viewBox)
    // design = compass/dividers, construction = hammer, hybrid = hard hat
    const SECTOR_ICONS = {
      design: [
        // compass pivot circle
        "M12 4 m-1.2 0 a1.2 1.2 0 1 0 2.4 0 a1.2 1.2 0 1 0 -2.4 0",
        // left leg: pivot → lower-left foot
        "M11.1 5 L6 20",
        // right leg: pivot → lower-right foot
        "M12.9 5 L18 20",
        // crossbar connecting the two legs mid-way
        "M8 14 L16 14"
      ],
      construction: [
        // hammer head (horizontal rectangle)
        "M3 9 h8 v5 h-8 Z",
        // handle (vertical, below head center)
        "M8 14 L8 22"
      ],
      hybrid: [
        // hard-hat brim
        "M2 18a1 1 0 0 0 1 1h18a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1H3a1 1 0 0 0-1 1v2z",
        // crown ridge strap
        "M10 10V5a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v5",
        // dome arc
        "M4 15v-3a8 8 0 0 1 16 0v3"
      ],
      // legacy alias
      combined: [
        "M2 18a1 1 0 0 0 1 1h18a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1H3a1 1 0 0 0-1 1v2z",
        "M10 10V5a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v5",
        "M4 15v-3a8 8 0 0 1 16 0v3"
      ]
    };
    const ICON = 16; // display size in SVG user units

    plots.forEach((q) => {
      const p = q.p;
      const status = statusKey(p);
      const empty = status === "empty";
      const g = el("g", {
        class: empty ? "blip blip-empty" : "blip",
        tabindex: "0", role: "button",
        "aria-label": `${p.id} ${p.name}, ${stateLabel(p)}`,
        "data-id": p.id
      });

      const color =
        status === "green" ? STATUS_COLOR.green :
        status === "amber" ? STATUS_COLOR.amber :
        status === "red"   ? STATUS_COLOR.red : "var(--muted)";

      // SVG tooltip
      const titleEl = el("title");
      titleEl.textContent = `${p.id} — ${p.name}`;
      g.appendChild(titleEl);

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

      // keyboard focus ring
      const ring = el("circle", {
        cx: q.x, cy: q.y, r: 12, fill: "none",
        stroke: "var(--phosphor)", "stroke-width": "2",
        class: "blip-ring", opacity: "0"
      });
      g.appendChild(ring);

      // hard-hat icon: nested <svg> positions it unambiguously in the parent
      // SVG's coordinate system via x/y/width/height attributes.
      const iconSvg = el("svg", {
        x: (q.x - ICON / 2).toFixed(1),
        y: (q.y - ICON / 2).toFixed(1),
        width: ICON, height: ICON,
        viewBox: "0 0 24 24",
        overflow: "visible",
        class: "blip-icon"
      });
      const iconG = el("g", {
        fill: "none", stroke: color,
        "stroke-linecap": "round", "stroke-linejoin": "round",
        "stroke-width": "2",
        opacity: empty ? "0.45" : "1"
      });
      if (empty) iconG.setAttribute("stroke-dasharray", "2 2");
      const sector = (p.sector || "hybrid").toLowerCase();
      const iconPaths = SECTOR_ICONS[sector] || SECTOR_ICONS.hybrid;
      iconPaths.forEach((d) => iconG.appendChild(el("path", { d })));
      iconSvg.appendChild(iconG);
      g.appendChild(iconSvg);

      // leader line when the label was nudged away from its natural spot
      if (Math.abs(q.ly - (q.y + 5)) > 5) {
        g.appendChild(el("line", {
          x1: q.x + 9, y1: q.y, x2: q.lx - 2, y2: q.ly - 3,
          class: "blip-leader"
        }));
      }

      const label = el("text", { x: q.lx, y: q.ly, class: "blip-label" });
      label.textContent = p.id;
      g.appendChild(label);

      const choose = () => openDetail(p.id);
      g.addEventListener("click", choose);
      g.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); choose(); }
      });
      // hover/focus: emphasize label and re-append so it paints on top
      const raise = () => { g.classList.add("hot"); svg.appendChild(g); };
      const lower = () => { g.classList.remove("hot"); };
      g.addEventListener("mouseenter", raise);
      g.addEventListener("mouseleave", lower);
      g.addEventListener("focus", raise);
      g.addEventListener("blur", lower);

      svg.appendChild(g);
    });

    highlightBlip();
  }

  function highlightBlip() {
    document.querySelectorAll(".blip").forEach((b) => {
      const on = b.getAttribute("data-id") === selectedId;
      b.classList.toggle("selected", on);
      const ring = b.querySelector(".blip-ring");
      if (ring) ring.setAttribute("opacity", on ? "1" : "0");
    });
  }

  /* ---------- accessible fallback list ---------- */
  function buildFallbackList() {
    const ul = $("#project-list");
    ul.innerHTML = "";
    LIN_PROJECTS.forEach((p) => {
      const li = document.createElement("li");
      const btn = document.createElement("button");
      btn.className = "list-item";
      btn.setAttribute("data-id", p.id);
      const state = stateLabel(p);
      const sum = simSummary(p);
      const simChip = sum
        ? `<span class="li-sim state-${sum.worst}" title="Simulation models: ${sum.red} red, ${sum.amber} amber, ${sum.green} green">${sum.flagged}/${sum.total} sim</span>`
        : "";
      btn.innerHTML =
        `<span class="li-code">${p.id}</span>` +
        `<span class="li-name">${p.name}</span>` +
        simChip +
        `<span class="li-state state-${statusKey(p)}">${state}</span>`;
      btn.addEventListener("click", () => openDetail(p.id));
      li.appendChild(btn);
      ul.appendChild(li);
    });
  }

  function highlightListItem() {
    document.querySelectorAll(".list-item").forEach((b) => {
      b.classList.toggle("active", b.getAttribute("data-id") === selectedId);
    });
  }

  /* ---------- signal ledger ---------- */
  function statusPill(status) {
    const map = { green: "Green", amber: "Amber", red: "Red" };
    return `<span class="pill pill-${status}">${map[status] || status}</span>`;
  }

  /* Summarize the nine client-side simulation models (PERT/LOB/CCPM/RCF/DSM + DST/RoughSets/Neutrosophic/IFS)
     for the Portfolio views. Returns null when none have run (graceful
     fallback — nothing is shown). */
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
    return { red, amber, green, total: arr.length, worst, flagged: red + amber };
  }

  function awaitingHtml(p, what) {
    return `<div class="ledger-head"><div>
        <p class="eyebrow">${what}</p>
        <h2>${p.id}</h2><p class="ledger-sub">${p.name}</p>
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
        detail: `Data date ${s.evm.dataDate}`
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
        metric: `${s.cusum.metric} drift ${s.cusum.drift.toFixed(1)} / ${s.cusum.threshold.toFixed(1)}`,
        detail: s.cusum.breached ? "Threshold breached" : "Within control limits"
      },
      {
        name: "Document risk", method: "Keyword / rule extraction",
        status: s.doc.status,
        metric: `Risk score ${s.doc.score.toFixed(2)}`,
        detail: `<span class="src">${s.doc.source}</span><span class="excerpt">“${s.doc.excerpt}”</span>`
      }
    ];

    const conflictClass =
      conflict === "Agreement — low risk" ? "conflict-calm" : "conflict-alert";

    root.innerHTML =
      `<div class="ledger-head">
         <div>
           <p class="eyebrow">Signal ledger</p>
           <h2>${p.id}</h2>
           <p class="ledger-sub">${p.name}</p>
         </div>
       </div>
       <div class="conflict-banner ${conflictClass}">
         <span class="conflict-label">Signal conflict</span>
         <span class="conflict-value">${conflict}</span>
       </div>
       <div class="signal-rows">` +
      rows.map((r) => `
        <div class="signal-row">
          <div class="sig-top">
            <span class="sig-name">${r.name}</span>
            ${statusPill(r.status)}
          </div>
          <div class="sig-metric">${r.metric}</div>
          <div class="sig-meta"><span class="sig-method">${r.method}</span></div>
          <div class="sig-detail">${r.detail}</div>
        </div>`).join("") +
      simLedgerRow(p) +
      `</div>`;
  }

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
          <div class="sig-meta"><span class="sig-method">PERT · LOB · CCPM · RCF · DSM · DST · Rough Sets · Neutrosophic · Interval Fuzzy</span></div>
          <div class="sig-detail">Worst status across the nine simulation modules.</div>
        </div>`;
  }

  /* ---------- decision card ----------
     Renders into any container (portfolio side panel or Project Detail),
     so all controls are class-scoped to the container — no duplicate ids. */
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
         <span class="state-badge state-${stateClass}">${d.healthState}</span>
       </div>
       <div class="dc-grid">
         <div class="dc-field"><span class="dc-label">Conflict</span><span class="dc-value">${d.conflictType}</span></div>
         <div class="dc-field"><span class="dc-label">Authority</span><span class="dc-value">${d.authority}</span></div>
         <div class="dc-field dc-wide"><span class="dc-label">Recommended action</span><span class="dc-value">${d.action}</span></div>
         <div class="dc-field dc-wide"><span class="dc-label">Documentation required</span><span class="dc-value">${d.documentation}</span></div>
       </div>
       <p class="dc-caveat">Recommended actions require named human approval before they are recorded; fairness gates require contractor response opportunity before any formal action.</p>
       ${fairnessBlock}
       <label class="rationale-label">Reviewer rationale <span class="req">(required, min 20 characters)</span>
       <textarea class="rationale" placeholder="State why this action is taken, deferred, or overridden. Recorded to the audit log."></textarea></label>
       <div class="dc-actions">
         <button class="btn primary record-btn" disabled>Record decision</button>
         <button class="btn export-btn">Export audit JSON</button>
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
          <div class="log-top"><span class="log-proj">${e.project}</span><span class="log-state state-${e.state.toLowerCase().replace("-review","")}">${e.state}</span></div>
          <div class="log-action">${e.action}</div>
          <div class="log-rationale">“${e.rationale}”</div>
          <div class="log-time">${LinTZ.format(e.recordedAt)}${e.fairnessAcknowledged ? " · fairness gate acknowledged" : ""}</div>
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
     portfolio side-ledger update via selectProject is non-blocking. */
  function openDetail(id) {
    selectedId = id;
    showPage("detail");
    try { selectProject(id); } catch (e) { /* side-ledger is non-critical to navigation */ }
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
      `<option value="${z.id}"${z.id === LinTZ.get() ? " selected" : ""}>${z.label}</option>`).join("");
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

  /* ---------- public API (used by ingest.js) ---------- */
  window.LinApp = {
    refresh() {
      buildRadar(); buildFallbackList();
      // if the selected project was archived, fall back to the first active one
      if (selectedId && !LIN_PROJECTS.some((p) => p.id === selectedId) && LIN_PROJECTS.length) {
        selectProject(LIN_PROJECTS[0].id);
      }
    },
    selectProject(id) { showPage("portfolio"); selectProject(id); },
    openDetail,
    showPage,
    getSelectedId() { return selectedId; },
    // shared renderers, reused by the Project Detail page (detail.js)
    renderLedger,
    renderDecisionCard
  };

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
    wireTzSelect();
    startClock();
    showPage("portfolio");

    // Phase 2: hydrate the portfolio from the Drive-backed store (async).
    // Renders an empty/awaiting portfolio while loading; the store shows a
    // non-fatal banner on error and falls back to the last cached list.
    try { await LinStore.load(); } catch (e) { /* store shows its own banner */ }

    buildRadar();
    buildFallbackList();
    renderDecisionLog();

    // default selection: first project in the portfolio (may be empty →
    // shows the awaiting-ingest state, not a fabricated status).
    if (LIN_PROJECTS.length) selectProject(LIN_PROJECTS[0].id);

    // rebuild radar geometry on resize-driven motion-pref changes
    window.matchMedia("(prefers-reduced-motion: reduce)").addEventListener?.("change", buildRadar);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
