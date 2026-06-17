/* ============================================================
   Lin Project Radar — deepdive.js
   Per-project deep-dive panels for the Project Detail page,
   matching the depth of the old HUD per-module views:
     chart + "why" metric grid + reasoning bullets + RULE line.

   Every chart is an ILLUSTRATIVE view derived deterministically
   from that project's synthetic data — never live or validated
   model output. Module 09 reads decision.js output directly;
   no governance rules are duplicated here.

   Module numbering:
     01  Monte Carlo EAC Forecast
     02  CUSUM Anomaly Monitor
     03  Document Risk Extraction
     04  PERT Network Criticality          (simulation)
     05  Line of Balance Production Velocity (simulation)
     06  CCPM Buffer Health                 (simulation)
     07  Reference Class Forecasting        (simulation)
     08  DSM Rework Propagation             (simulation)
     09  ABM Governance Layer
     10  Signal Synthesis (conservative dominance)
     11  Dempster-Shafer Evidence Combination (simulation)
     12  Rough Set Theory Classification   (simulation)
     13  Neutrosophic Logic                (simulation)
     14  Interval-valued Fuzzy Sets        (simulation)
   ============================================================ */

(function () {
  "use strict";

  const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const COLOR = {
    green: "var(--clear-green)",
    amber: "var(--radar-amber)",
    red:   "var(--alarm-red)"
  };
  const cls = (s) => String(s).toLowerCase().replace("-review", "");

  /* ---------- HUD-style building blocks ---------- */

  function verdict(label, status) {
    const c = cls(status);
    return `<span class="dd-verdict status-${c}"><i></i>${esc(label)}: ${esc(String(status).toUpperCase())}</span>`;
  }

  function metricBox(label, value, status) {
    const c = cls(status);
    return `<div class="dd-metric status-${c}"><span>${esc(label)}</span><strong>${esc(value)}</strong><em>${esc(String(status).toUpperCase())}</em></div>`;
  }

  function reasons(items, status) {
    return `<ul class="dd-reasons" style="--dd-color:${COLOR[cls(status)]}">${items.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>`;
  }

  function rule(text) {
    return `<div class="dd-rule"><strong>Rule:</strong> ${esc(text)}</div>`;
  }

  function note(text) {
    return `<p class="dd-chart-note">${esc(text)}</p>`;
  }

  function panel(num, title, status, inner) {
    const c = cls(status);
    return `<section class="panel dd-panel status-${c}" aria-label="Module ${num} deep dive">
      <div class="dd-head"><b>Why Module ${num} (${esc(title)}) is ${esc(String(status).toUpperCase())}</b>${verdict(title, status)}</div>
      ${inner}
    </section>`;
  }

  /* ---------- charts (pure SVG, theme tokens, deterministic) ---------- */

  const W = 540;

  function svgo(h, label) {
    return `<svg viewBox="0 0 ${W} ${h}" class="mod-chart" role="img" aria-label="${esc(label)}">`;
  }

  /* Module 01: REAL Monte Carlo. Re-runs LinSim.monteCarloEAC (5,000-iteration
     loop over a signal-derived Beta-PERT) live and draws the actual histogram
     of the simulated array, with P50/P80 markers at the computed percentiles
     and the baseline (demo BAC). Returns { svg, mc } so the caller can show N
     and the computed values. */
  function mcChartReal(p) {
    const h = 226, pad = 44, base = h - 50;
    const mc = LinSim.monteCarloEAC(p.signals.mc.inputs, { iterations: 5000 });
    const c = COLOR[p.signals.mc.status];
    const samples = mc.samples;                 // sorted ascending
    const lo = samples[0], hi = samples[samples.length - 1];
    const span = hi - lo || 1;
    const BINS = 40;
    const counts = new Array(BINS).fill(0);
    for (let i = 0; i < samples.length; i++) {
      let b = Math.floor(((samples[i] - lo) / span) * BINS);
      if (b >= BINS) b = BINS - 1; if (b < 0) b = 0;
      counts[b]++;
    }
    const maxCount = Math.max(...counts) || 1;
    const plotW = W - pad - 16;
    const sx = (v) => pad + ((v - lo) / span) * plotW;
    const bw = plotW / BINS;

    let bars = "";
    for (let b = 0; b < BINS; b++) {
      const bh = (counts[b] / maxCount) * (base - 22);
      const x = pad + b * bw;
      bars += `<rect x="${x.toFixed(1)}" y="${(base - bh).toFixed(1)}" width="${(bw - 0.6).toFixed(1)}" height="${bh.toFixed(1)}" fill="${c}" opacity="0.45"></rect>`;
    }
    const mark = (v, label, strong) =>
      `<line x1="${sx(v)}" y1="16" x2="${sx(v)}" y2="${base}" stroke="${strong ? c : "var(--ring-line)"}" stroke-width="${strong ? 1.8 : 1.2}" stroke-dasharray="${strong ? "none" : "4 3"}"></line>` +
      `<text x="${sx(v) + 4}" y="${strong ? 14 : 28}" class="mod-axis" fill="${strong ? c : "var(--muted)"}">${esc(label)}</text>`;

    const svg = svgo(h, "Real Monte Carlo EAC distribution (5,000 iterations) with P50 and P80 markers") +
      `<line x1="${pad}" y1="${base}" x2="${W - 12}" y2="${base}" stroke="var(--ring-line)"></line>` +
      bars +
      mark(mc.baseline, `BAC ${mc.baseline.toFixed(0)}`, false) +
      mark(mc.p50, `P50 ${mc.p50.toFixed(1)}`, false) +
      mark(mc.p80, `P80 ${mc.p80.toFixed(1)}`, true) +
      `<text x="${W / 2}" y="${h - 4}" text-anchor="middle" class="mod-axis-title">Estimate at Completion ($)</text>` +
      `<text transform="rotate(-90 10 ${h / 2})" x="10" y="${h / 2}" text-anchor="middle" class="mod-axis-title">Frequency</text>` +
      "</svg>";
    return { svg, mc };
  }

  /* Module 02: REAL CUSUM. Re-runs LinSim.cusumSeries (the two-sided tabular
     recursion) live over the project's metric series and draws the computed
     statistic per period against the decision interval H, flagging the breach
     point where the statistic actually crosses H. Returns { svg, cu }. */
  function cusumChartReal(p) {
    const cuStored = p.signals.cusum;
    const cu = LinSim.cusumSeries(cuStored.series, {
      target: cuStored.target, sigma: cuStored.sigma, hUnits: cuStored.hUnits
    });
    const h = 216, pad = 44, base = h - 46;
    const n = cu.stat.length;
    const yMax = Math.max(cu.H * 1.35, cu.maxStat * 1.15, 0.01);
    const sx = (i) => pad + (n > 1 ? (i / (n - 1)) : 0) * (W - pad - 20);
    const sy = (v) => base - (v / yMax) * (base - 18);
    const c = cu.breached ? COLOR.red : COLOR[LinSim.cusumStatus(cu)];

    const statPts = cu.stat.map((v, i) => `${sx(i).toFixed(1)},${sy(v).toFixed(1)}`).join(" ");

    let breachMark = "";
    if (cu.breached && cu.breachIndex >= 0) {
      const bx = sx(cu.breachIndex), by = sy(cu.stat[cu.breachIndex]);
      breachMark = `<circle cx="${bx}" cy="${by}" r="5" fill="${COLOR.red}"></circle>` +
        `<text x="${bx}" y="${by - 9}" text-anchor="middle" class="mod-axis" fill="${COLOR.red}">⚑ breach @ period ${cu.breachIndex + 1}</text>`;
    }

    return {
      svg: svgo(h, "Real two-sided CUSUM statistic vs decision interval H") +
        `<rect x="${pad}" y="${sy(cu.H)}" width="${W - pad - 20}" height="${base - sy(cu.H)}" fill="var(--zone-green)"></rect>` +
        `<line x1="${pad}" y1="${base}" x2="${W - 12}" y2="${base}" stroke="var(--ring-line)"></line>` +
        `<line x1="${pad}" y1="14" x2="${pad}" y2="${base}" stroke="var(--ring-line)"></line>` +
        `<line x1="${pad}" y1="${sy(cu.H)}" x2="${W - 20}" y2="${sy(cu.H)}" stroke="${COLOR.red}" stroke-width="1.4" stroke-dasharray="5 4"></line>` +
        `<text x="${W - 22}" y="${sy(cu.H) - 5}" text-anchor="end" class="mod-axis" fill="${COLOR.red}">decision interval H = ${cu.H.toFixed(2)} (${cu.hUnits}σ)</text>` +
        `<polyline points="${statPts}" fill="none" stroke="${c}" stroke-width="2"></polyline>` +
        breachMark +
        `<text x="${W / 2}" y="${h - 4}" text-anchor="middle" class="mod-axis-title">Reporting Period</text>` +
        `<text transform="rotate(-90 10 ${h / 2})" x="10" y="${h / 2}" text-anchor="middle" class="mod-axis-title">Cumulative Sum</text>` +
        "</svg>",
      cu
    };
  }

  /* Module 03: document-risk score gauge with amber/red thresholds. */
  function docChart(p) {
    const h = 96, pad = 40, barY = 34, barH = 18;
    const span = W - pad - 24;
    const score = p.signals.doc.score;
    const sx = (v) => pad + v * span;
    const c = COLOR[p.signals.doc.status];
    return svgo(h, "Illustrative document-risk score gauge") +
      `<rect x="${pad}" y="${barY}" width="${span}" height="${barH}" rx="4" fill="var(--surface-soft)" stroke="var(--ring-line)"></rect>` +
      `<rect x="${pad}" y="${barY}" width="${(sx(score) - pad).toFixed(1)}" height="${barH}" rx="4" fill="${c}" opacity="0.55"></rect>` +
      [[0.30, "amber >= 0.30", COLOR.amber], [0.70, "red >= 0.70", COLOR.red]].map(([v, lab, col]) =>
        `<line x1="${sx(v)}" y1="${barY - 8}" x2="${sx(v)}" y2="${barY + barH + 8}" stroke="${col}" stroke-width="1.3" stroke-dasharray="4 3"></line>` +
        `<text x="${sx(v) + 3}" y="${barY - 12}" class="mod-axis" fill="${col}">${lab}</text>`).join("") +
      `<circle cx="${sx(score)}" cy="${barY + barH / 2}" r="6" fill="${c}" stroke="var(--text)" stroke-width="1"></circle>` +
      `<text x="${sx(score)}" y="${barY + barH + 22}" text-anchor="middle" class="mod-axis" fill="${c}">score ${score.toFixed(2)}</text>` +
      "</svg>";
  }

  /* Module 10: signal agreement map — four signal nodes colored by status,
     like the HUD's conflict lens. */
  function synthChart(p) {
    const h = 150;
    const s = p.signals;
    const nodes = [
      ["EVM", s.evm.status], ["FORECAST", s.mc.status],
      ["CUSUM", s.cusum.status], ["DOC", s.doc.status]
    ];
    const cxs = [90, 215, 340, 465];
    return svgo(h, "Illustrative signal agreement map across the four signal classes") +
      nodes.map(([lab, st], i) =>
        (i < 3 ? `<line x1="${cxs[i] + 38}" y1="72" x2="${cxs[i + 1] - 38}" y2="72" stroke="var(--phosphor)" stroke-width="1.5" stroke-dasharray="6 5"></line>` : "") +
        `<circle cx="${cxs[i]}" cy="72" r="36" fill="none" stroke="${COLOR[st]}" stroke-width="2.5"></circle>` +
        `<text x="${cxs[i]}" y="69" text-anchor="middle" class="mod-axis" fill="var(--text)">${lab}</text>` +
        `<text x="${cxs[i]}" y="84" text-anchor="middle" class="mod-axis" fill="${COLOR[st]}">${st.toUpperCase()}</text>`
      ).join("") +
      "</svg>";
  }

  /* Module 09: governance decision path driven by decision.js output. */
  function abmChart(p, d) {
    const h = 132;
    const c = COLOR[cls(d.healthState)];
    const box = (x, w, l1, l2, col) =>
      `<rect x="${x}" y="34" width="${w}" height="58" rx="8" fill="none" stroke="${col}" stroke-width="2"></rect>` +
      `<text x="${x + w / 2}" y="58" text-anchor="middle" class="mod-axis" fill="var(--text)">${esc(l1)}</text>` +
      `<text x="${x + w / 2}" y="74" text-anchor="middle" class="mod-axis" fill="${col}">${esc(l2)}</text>`;
    const arrow = (x) => `<text x="${x}" y="68" text-anchor="middle" class="mod-axis" fill="var(--phosphor)">→</text>`;
    return svgo(h, "Illustrative governance decision path from decision.js output") +
      box(14, 130, "SIGNAL PACKAGE", "4 signal classes", "var(--phosphor)") + arrow(157) +
      box(172, 150, "CONFLICT", d.conflictType.length > 18 ? d.conflictType.slice(0, 17) + "…" : d.conflictType, c) + arrow(335) +
      box(350, 176, d.fairnessGateRequired ? "FAIRNESS GATE ⚑" : "RECOMMENDATION", d.healthState.toUpperCase(), c) +
      `<text x="${W / 2}" y="${h - 10}" text-anchor="middle" class="mod-axis">authority: ${esc(d.authority)}</text>` +
      "</svg>";
  }

  /* ---------- per-module status + reasoning ---------- */

  function m01(p) {
    const e = p.signals.evm, m = p.signals.mc;
    const st = (e.status === "red" || m.status === "red") ? "red"
      : (e.status === "amber" || m.status === "amber") ? "amber" : "green";
    const cpiS = e.cpi < 0.90 ? "red" : e.cpi < 0.95 ? "amber" : "green";
    const spiS = e.spi < 0.85 ? "red" : e.spi < 0.95 ? "amber" : "green";
    const p80S = m.p80eacOverrunPct >= 10 ? "red" : m.p80eacOverrunPct >= 5 ? "amber" : "green";
    const pdS  = m.pMilestoneDelay >= 0.60 ? "red" : m.pMilestoneDelay >= 0.30 ? "amber" : "green";
    const why = st === "red" ? [
      `CPI ${e.cpi.toFixed(2)} and SPI ${e.spi.toFixed(2)} are below control tolerance, so the earned-value trend is not only a forecast issue.`,
      `The P80 EAC sits ${m.p80eacOverrunPct >= 0 ? "+" : ""}${m.p80eacOverrunPct.toFixed(1)}% over baseline with a ${(m.pMilestoneDelay * 100).toFixed(0)}% probability of milestone delay — the conservative forecast is in recovery-review territory.`,
      `The distribution above shows the P50→P80 spread; the tail beyond P80 is the residual 20% risk the governance layer must own.`
    ] : st === "amber" ? [
      `At least one cost or schedule indicator is in the watch band: CPI ${e.cpi.toFixed(2)}, SPI ${e.spi.toFixed(2)}, P80 ${m.p80eacOverrunPct >= 0 ? "+" : ""}${m.p80eacOverrunPct.toFixed(1)}%.`,
      `The forecast remains manageable, but P(milestone delay) is ${(m.pMilestoneDelay * 100).toFixed(0)}%, which requires review before the next reporting cycle closes.`,
      `Amber means attention required — not immediate executive recovery action.`
    ] : [
      `CPI ${e.cpi.toFixed(2)} and SPI ${e.spi.toFixed(2)} remain inside normal monitoring tolerance for the current reporting cycle.`,
      `P80 EAC exposure is ${m.p80eacOverrunPct >= 0 ? "+" : ""}${m.p80eacOverrunPct.toFixed(1)}% with only a ${(m.pMilestoneDelay * 100).toFixed(0)}% delay probability, so the conservative outcome does not trigger recovery review.`,
      `Forecast and reported status agree — the distribution sits over the baseline.`
    ];
    const mcReal = mcChartReal(p);
    const mc = mcReal.mc;
    return panel("01", "Hybrid Dynamic Simulation", st,
      note("Probabilistic estimate at completion from 5,000 iterations of the project's cost and schedule performance indices. P50 and P80 bound the realistic cost exposure range. P80 is the planning-conservative figure used for contingency and escalation decisions.") +
      mcReal.svg +
      `<div class="dd-grid">${
        metricBox("Cost Performance Index (CPI)", e.cpi.toFixed(2), cpiS) +
        metricBox("Schedule Performance Index (SPI)", e.spi.toFixed(2), spiS) +
        metricBox("P50 EAC", mc.p50.toFixed(1), "green") +
        metricBox("P80 EAC", mc.p80.toFixed(1), p80S) +
        metricBox("P80 Delta vs BAC", `${mc.overrunPctP80 >= 0 ? "+" : ""}${mc.overrunPctP80.toFixed(1)}%`, p80S) +
        metricBox("P(delay)", m.pMilestoneDelay.toFixed(2), pdS)
      }</div>` +
      reasons(why, st) +
      rule("GREEN if CPI/SPI >= 0.95 and P80 EAC within +5%; AMBER if one forecast indicator enters the watch range (CPI/SPI < 0.95, P80 +5-10%, P(delay) >= 0.30); RED if CPI/SPI < 0.90, P80 >= +10%, or P(delay) >= 0.60."));
  }

  function m02(p) {
    const cu = p.signals.cusum;
    const st = cu.breached ? "red" : cu.status;
    const why = cu.breached ? [
      `CUSUM drift ${cu.drift.toFixed(1)} exceeds the control threshold ${cu.threshold.toFixed(1)}, so the pattern is cumulative — not a one-period fluctuation.`,
      `The chart shows sustained accumulation across reporting periods rather than noise around the baseline.`,
      `A breach hands the question to the governance layer; the monitor itself never acts.`
    ] : st === "amber" ? [
      `CUSUM drift ${cu.drift.toFixed(1)} is inside the watch band — weakening, but the ${cu.threshold.toFixed(1)} threshold is not broken.`,
      `Amber prevents the team from waiting until the next full EVM variance becomes visible.`
    ] : [
      `CUSUM drift ${cu.drift.toFixed(1)} on ${cu.metric} stays well below the ${cu.threshold.toFixed(1)} control threshold.`,
      `No control-limit breach is present in the trend; the anomaly monitor agrees with routine reporting cadence.`
    ];
    const cuReal = cusumChartReal(p);
    const r = cuReal.cu;
    return panel("02", "Statistical Process Control (SPC) / Cumulative Sum Control Chart (CUSUM) Anomaly Monitor", st,
      note("Cumulative Sum Control Chart monitoring the Schedule Performance Index across reporting periods. Detects sustained drift that single-period variance would mask. A breach means the pattern is systemic and requires explanation before the next reporting cycle closes.") +
      cuReal.svg +
      `<div class="dd-grid">${
        metricBox("Peak CUSUM", r.maxStat.toFixed(2), st) +
        metricBox("Decision H", r.H.toFixed(2), "green") +
        metricBox("Sigma estimate", r.sigma.toFixed(3), "green") +
        metricBox("Breached", r.breached ? "YES" : "NO", r.breached ? "red" : "green") +
        metricBox("Monitored", cu.metric, "green") +
        metricBox("Periods", String(r.x.length), "green")
      }</div>` +
      reasons(why, st) +
      rule("GREEN if cumulative drift is below watch level; AMBER if drift approaches the control limit; RED if CUSUM breaches the threshold (>= 5.0)."));
  }

  function m03(p) {
    const d = p.signals.doc;
    const st = d.status;
    const why = st === "red" ? [
      `Document risk score ${d.score.toFixed(2)} is at or above the 0.70 red threshold — the text evidence itself can justify escalation before the next cost report reflects it.`,
      `Source: ${d.source}. The extracted language points to cost/schedule/scope impact rather than routine correspondence.`,
      `Evidence excerpt: "${d.excerpt}"`
    ] : st === "amber" ? [
      `Document risk score ${d.score.toFixed(2)} sits in the 0.30–0.70 watch band; impact language is reviewable rather than conclusive.`,
      `Source: ${d.source}.`,
      `Evidence excerpt: "${d.excerpt}"`
    ] : [
      `Document risk score ${d.score.toFixed(2)} is below the 0.30 watch threshold — records are routine for this reporting cycle.`,
      `The document trail supports the quantitative forecast rather than contradicting it.`
    ];
    return panel("03", "Document-Risk Extraction", st,
      note("Risk signal extracted from project documents. Document language often leads the EVM signal by weeks — disputes and coordination failures appear in writing before they register in cost or schedule performance.") +
      docChart(p) +
      `<div class="dd-grid">${
        metricBox("Risk score", d.score.toFixed(2), st) +
        metricBox("Status", st.toUpperCase(), st) +
        metricBox("Source", d.source.length > 22 ? d.source.slice(0, 21) + "…" : d.source, "green")
      }</div>` +
      reasons(why, st) +
      rule("GREEN if score < 0.30 (routine language); AMBER if 0.30-0.70 (possible cost/schedule/scope impact); RED if >= 0.70 (high-impact language converging across records)."));
  }

  function m10(p) {
    const conflict = classifyConflict(p);
    const s = p.signals;
    const statuses = [s.evm.status, s.mc.status, s.cusum.status, s.doc.status];
    const redN = statuses.filter((x) => x === "red").length;
    const ambN = statuses.filter((x) => x === "amber").length;
    const st = redN >= 2 ? "red" : (redN || ambN) ? "amber" : "green";
    const why = conflict === "Agreement — low risk" ? [
      `All four signal classes are green and aligned — there is no disagreement to surface.`,
      `Agreement is itself recorded: the decision card still logs the evidence package for auditability.`
    ] : [
      `Conflict type "${conflict}": ${redN} red and ${ambN} amber signal class(es) against ${4 - redN - ambN} green.`,
      `PCEIF surfaces this disagreement instead of averaging it away — the gap between signal classes is the finding.`,
      `The classification feeds Module 09, which maps it to an action and an authority.`
    ];
    return panel("10", "Signal Synthesis", st,
      note("Agreement map across all signal classes. When signals diverge, the gap between classes is the finding. PCEIF surfaces disagreement instead of averaging it away. Conservative dominance: the worst single-signal status drives the overall classification.") +
      synthChart(p) +
      `<div class="dd-grid">${
        metricBox("Conflict", conflict.length > 20 ? conflict.slice(0, 19) + "…" : conflict, st) +
        metricBox("Red signals", String(redN), redN ? "red" : "green") +
        metricBox("Amber signals", String(ambN), ambN ? "amber" : "green") +
        metricBox("Aligned", redN + ambN === 0 ? "YES" : "NO", redN + ambN === 0 ? "green" : "amber")
      }</div>` +
      reasons(why, st) +
      rule("Precedence: multi-signal red-review > anomaly without narrative > forecast ahead of status > leading document risk > agreement > mixed early warning (classifyConflict in decision.js). Conservative dominance: worst signal wins."));
  }

  function m09(p) {
    // All values below come straight from decision.js — no duplicated rules.
    const d = deriveDecision(p);
    const st = cls(d.healthState);
    const why = [
      `decision.js derives state "${d.healthState}" with conflict "${d.conflictType}" for this project.`,
      `Recommended action: ${d.action}`,
      `Authority entitled to act: ${d.authority}. Documentation required: ${d.documentation}`,
      d.fairnessGateRequired
        ? "Fairness gate REQUIRED: contractor response opportunity must be acknowledged before any formal action — recording is blocked until then."
        : "No fairness gate is required for this state/sensitivity combination."
    ];
    return panel("09", "Agent-Based Model (ABM) Governance Layer", st,
      note("Governance decision derived from the full signal package using the PCEIF authority matrix. Maps the conflict classification to a specific action, a named authority, and required documentation.") +
      abmChart(p, d) +
      `<div class="dd-grid">${
        metricBox("Derived state", d.healthState, st) +
        metricBox("Fairness gate", d.fairnessGateRequired ? "REQUIRED" : "Not required", d.fairnessGateRequired ? "red" : "green") +
        metricBox("Conflict", d.conflictType.length > 20 ? d.conflictType.slice(0, 19) + "…" : d.conflictType, st) +
        metricBox("Sector", p.sector === "combined" ? "Hybrid" : p.sector, "green")
      }</div>` +
      reasons(why, st) +
      rule("GREEN → routine monitoring (PM/Controls); AMBER → early-warning review (PM + Controls lead); RED-REVIEW when >=2 red signals or CUSUM breach + red forecast (Program director/PMO); fairness-sensitive red-reviews additionally require the contractor fairness gate (deriveDecision in decision.js)."));
  }

  /* ---------- simulation modules (04–08, 11) ----------
     Renders project.simulationSignals (built by signals.js after the core run)
     as deep-dive modules — chart + metric grid + reasoning + rule —
     matching Modules 01–03. Each model object comes from LinSimulations. */
  const simCls = (s) => String(s || "green").toLowerCase();
  const simColor = (s) => COLOR[simCls(s)] || COLOR.green;
  const fByMethod = (arr, m) => arr.find((s) => s.method_class === m);

  /* Module 04 chart: horizontal bars Baseline / P50 / P80 (days). */
  function pertChart(s) {
    const h = 136, pad = 70, top = 22, rowH = 26;
    const span = W - pad - 90;
    const maxd = Math.max(s.baseline_days, s.p80_duration_days) * 1.18 || 1;
    const sx = (v) => (v / maxd) * span;
    const rows = [
      ["Baseline", s.baseline_days, "var(--ring-line)"],
      ["P50", s.p50_duration_days, COLOR.amber],
      ["P80", s.p80_duration_days, simColor(s.status_color)]
    ];
    return svgo(h, "PERT P50/P80 duration vs baseline") +
      rows.map((r, i) => {
        const y = top + i * rowH;
        return `<text x="8" y="${y + 13}" class="mod-axis" fill="var(--text)">${r[0]}</text>` +
          `<rect x="${pad}" y="${y + 3}" width="${span}" height="13" rx="3" fill="var(--surface-soft)" stroke="var(--ring-line)"></rect>` +
          `<rect x="${pad}" y="${y + 3}" width="${sx(r[1]).toFixed(1)}" height="13" rx="3" fill="${r[2]}" opacity="0.8"></rect>` +
          `<text x="${(pad + sx(r[1]) + 6).toFixed(1)}" y="${y + 13}" class="mod-axis" fill="${r[2]}">${r[1]}d</text>`;
      }).join("") +
      `<text x="${W / 2}" y="${h - 4}" text-anchor="middle" class="mod-axis-title">Duration (days)</text>` + "</svg>";
  }

  /* Module 05 chart: grading vs paving velocity lines, buffer zone, critical unit. */
  function lobChart(s) {
    const h = 136, pad = 40, base = h - 40, top = 14;
    const units = s.units || 20;
    const tMax = Math.max(units / s.grading_rate, s.initial_buffer_days + units / s.paving_rate) * 1.1 || 1;
    const sx = (u) => pad + (u / units) * (W - pad - 20);
    const sy = (t) => base - (t / tMax) * (base - top);
    let grade = "", pave = "";
    for (let u = 0; u <= units; u++) {
      grade += (u ? " " : "") + sx(u).toFixed(1) + "," + sy(u / s.grading_rate).toFixed(1);
      pave += (u ? " " : "") + sx(u).toFixed(1) + "," + sy(s.initial_buffer_days + u / s.paving_rate).toFixed(1);
    }
    const zone = grade + " " + pave.split(" ").reverse().join(" ");
    const cu = s.critical_unit_index;
    const critMark = cu < units
      ? `<line x1="${sx(cu)}" y1="${top}" x2="${sx(cu)}" y2="${base}" stroke="${COLOR.red}" stroke-width="1.3" stroke-dasharray="4 3"></line>` +
        `<text x="${sx(cu)}" y="${top + 8}" text-anchor="middle" class="mod-axis" fill="${COLOR.red}">crit unit ${cu}</text>`
      : "";
    return svgo(h, "LOB grading vs paving velocity") +
      `<line x1="${pad}" y1="${base}" x2="${W - 14}" y2="${base}" stroke="var(--ring-line)"></line>` +
      `<line x1="${pad}" y1="${top}" x2="${pad}" y2="${base}" stroke="var(--ring-line)"></line>` +
      `<polygon points="${zone}" fill="var(--zone-green)" opacity="0.5"></polygon>` +
      `<polyline points="${grade}" fill="none" stroke="${COLOR.green}" stroke-width="2"></polyline>` +
      `<polyline points="${pave}" fill="none" stroke="${simColor(s.status_color)}" stroke-width="2"></polyline>` +
      critMark +
      `<text x="${pad + 4}" y="${top + 8}" class="mod-axis" fill="${COLOR.green}">grading</text>` +
      `<text x="${W / 2}" y="${h - 4}" text-anchor="middle" class="mod-axis-title">Production Units</text>` +
      `<text transform="rotate(-90 10 ${h / 2})" x="10" y="${h / 2}" text-anchor="middle" class="mod-axis-title">Schedule Days</text>` + "</svg>";
  }

  /* Module 06 chart: fever bar Green/Amber/Red with the buffer-consumption dot. */
  function ccpmChart(s) {
    const h = 136, pad = 40, barY = 50, barH = 22, span = W - pad - 30;
    const sx = (v) => pad + (clamp01(v) / 100) * span;
    const a = s.amber_threshold, r = s.red_threshold, bc = s.pct_buffer_consumed;
    return svgo(h, "CCPM buffer-health fever chart") +
      `<text x="${W / 2}" y="22" text-anchor="middle" class="mod-axis">chain complete ${s.pct_chain_complete}% · amber >= ${a}% · red >= ${r}%</text>` +
      `<rect x="${pad}" y="${barY}" width="${(sx(a) - pad).toFixed(1)}" height="${barH}" fill="var(--zone-green)"></rect>` +
      `<rect x="${sx(a)}" y="${barY}" width="${(sx(r) - sx(a)).toFixed(1)}" height="${barH}" fill="var(--zone-amber)"></rect>` +
      `<rect x="${sx(r)}" y="${barY}" width="${(pad + span - sx(r)).toFixed(1)}" height="${barH}" fill="var(--zone-red)"></rect>` +
      `<rect x="${pad}" y="${barY}" width="${span}" height="${barH}" fill="none" stroke="var(--ring-line)"></rect>` +
      `<circle cx="${sx(bc)}" cy="${barY + barH / 2}" r="6" fill="${simColor(s.status_color)}" stroke="var(--text)" stroke-width="1"></circle>` +
      `<text x="${sx(bc)}" y="${barY - 8}" text-anchor="middle" class="mod-axis" fill="${simColor(s.status_color)}">${bc}% consumed</text>` +
      `<text x="${pad}" y="${barY + barH + 15}" class="mod-axis">0%</text>` +
      `<text x="${pad + span}" y="${barY + barH + 15}" text-anchor="end" class="mod-axis">100%</text>` +
      `<text x="${W / 2}" y="${h - 4}" text-anchor="middle" class="mod-axis-title">Buffer Consumed (%)</text>` + "</svg>";
  }

  /* Module 07 chart: multiplier histogram with P50/P80 markers. */
  function rcfChart(s) {
    const h = 136, pad = 30, base = h - 42, top = 20;
    const mult = s.multipliers && s.multipliers.length ? s.multipliers : [1.0];
    const lo = 1.0, hi = Math.max.apply(null, mult) * 1.04;
    const sx = (v) => pad + ((v - lo) / (hi - lo)) * (W - pad - 24);
    const barW = 11;
    const bars = mult.map((v) => `<rect x="${(sx(v) - barW / 2).toFixed(1)}" y="${top}" width="${barW}" height="${base - top}" rx="2" fill="var(--phosphor)" opacity="0.4"></rect>`).join("");
    const mk = (v, lab, col) => `<line x1="${sx(v)}" y1="${top - 5}" x2="${sx(v)}" y2="${base}" stroke="${col}" stroke-width="1.6" stroke-dasharray="5 3"></line>` +
      `<text x="${sx(v)}" y="${top - 7}" text-anchor="middle" class="mod-axis" fill="${col}">${lab}</text>`;
    return svgo(h, "RCF overrun-multiplier distribution") +
      `<line x1="${pad}" y1="${base}" x2="${W - 14}" y2="${base}" stroke="var(--ring-line)"></line>` +
      bars +
      mk(s.p50_multiplier, "P50 x" + s.p50_multiplier, COLOR.amber) +
      mk(s.p80_multiplier, "P80 x" + s.p80_multiplier, simColor(s.status_color)) +
      `<text x="${W / 2}" y="${h - 4}" text-anchor="middle" class="mod-axis-title">Cost Overrun Multiplier</text>` +
      `<text transform="rotate(-90 10 ${h / 2})" x="10" y="${h / 2}" text-anchor="middle" class="mod-axis-title">Historical Frequency</text>` + "</svg>";
  }

  /* Module 08 chart: 3x3 dependency-matrix heatmap (intensity = weight). */
  function dsmChart(s) {
    const h = 136, cell = 30, x0 = 150, y0 = 22;
    const M = s.matrix || [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
    const labels = ["Arch", "Struct", "MEP"];
    let cells = "";
    for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) {
      const w = M[i][j];
      const op = w > 0 ? (0.14 + 0.82 * w).toFixed(2) : "0.06";
      cells += `<rect x="${x0 + j * cell}" y="${y0 + i * cell}" width="${cell - 2}" height="${cell - 2}" rx="3" fill="var(--phosphor)" opacity="${op}"></rect>` +
        `<text x="${x0 + j * cell + (cell - 2) / 2}" y="${y0 + i * cell + (cell - 2) / 2 + 4}" text-anchor="middle" class="mod-axis" fill="var(--text)">${w > 0 ? w.toFixed(2) : "·"}</text>`;
    }
    const rowLabs = labels.map((l, i) => `<text x="${x0 - 6}" y="${y0 + i * cell + (cell - 2) / 2 + 4}" text-anchor="end" class="mod-axis">${l}</text>`).join("");
    const colLabs = labels.map((l, j) => `<text x="${x0 + j * cell + (cell - 2) / 2}" y="${y0 - 6}" text-anchor="middle" class="mod-axis">${l}</text>`).join("");
    return svgo(h, "DSM dependency-weight heatmap") +
      cells + rowLabs + colLabs +
      `<text x="${x0 + 3 * cell + 18}" y="${y0 + 16}" class="mod-axis">change in column</text>` +
      `<text x="${x0 + 3 * cell + 18}" y="${y0 + 32}" class="mod-axis">propagates to row</text>` +
      `<text x="14" y="${y0 + 3 * cell + 14}" class="mod-axis">rework x${s.rework_multiplier}</text>` +
      `<text x="${x0 + (3 * cell) / 2}" y="${h - 4}" text-anchor="middle" class="mod-axis-title">Dependency weight</text>` + "</svg>";
  }

  /* Module 11 chart: horizontal stacked belief-distribution bar. */
  function dstChart(s) {
    const h = 96, pad = 40, barY = 32, barH = 24;
    const span = W - pad - 24;
    const segments = [
      { key: "belief_green",   color: COLOR.green,         label: "Green" },
      { key: "belief_amber",   color: COLOR.amber,         label: "Amber" },
      { key: "belief_red",     color: COLOR.red,           label: "Red"   },
      { key: "belief_unknown", color: "var(--ring-line)",  label: "Unknown/Conflict" }
    ];
    let x = pad, bars = "", ticks = "";
    segments.forEach((seg) => {
      const pct = Number(s[seg.key]) || 0;
      const w = pct * span;
      if (w > 0) {
        bars += `<rect x="${x.toFixed(1)}" y="${barY}" width="${w.toFixed(1)}" height="${barH}" fill="${seg.color}" opacity="0.75"></rect>`;
        if (w > 28) {
          ticks += `<text x="${(x + w / 2).toFixed(1)}" y="${barY + barH / 2 + 4}" text-anchor="middle" class="mod-axis" fill="var(--bg)" font-weight="600">${Math.round(pct * 100)}%</text>`;
        }
      }
      x += w;
    });
    return svgo(h, "DST belief distribution — stacked horizontal bar showing Green/Amber/Red/Unknown masses") +
      `<rect x="${pad}" y="${barY}" width="${span}" height="${barH}" rx="4" fill="var(--surface-soft)" stroke="var(--ring-line)"></rect>` +
      bars +
      `<rect x="${pad}" y="${barY}" width="${span}" height="${barH}" rx="4" fill="none" stroke="var(--ring-line)"></rect>` +
      ticks +
      `<text x="${pad}" y="${barY + barH + 16}" class="mod-axis" fill="${COLOR.green}">Green</text>` +
      `<text x="${pad + span * 0.3}" y="${barY + barH + 16}" class="mod-axis" fill="${COLOR.amber}">Amber</text>` +
      `<text x="${pad + span * 0.6}" y="${barY + barH + 16}" class="mod-axis" fill="${COLOR.red}">Red</text>` +
      `<text x="${pad + span}" y="${barY + barH + 16}" text-anchor="end" class="mod-axis" fill="var(--muted)">Unknown</text>` +
      "</svg>";
  }

  const clamp01 = (v) => Math.max(0, Math.min(100, Number(v) || 0));
  const moneyShort = (v) => "$" + Math.round(Number(v) || 0).toLocaleString();

  function m04(s) {
    const st = simCls(s.status_color);
    return panel("04", "PERT — Network Criticality", st,
      note("Program Evaluation and Review Technique (PERT). Stochastic network analysis quantifying schedule risk across the critical path. The P80 duration is the planning-conservative milestone estimate. The Path Criticality Index identifies which path has the least float and highest probability of driving project completion.") +
      pertChart(s) +
      `<div class="dd-grid">${
        metricBox("P50 Duration", s.p50_duration_days + "d", "green") +
        metricBox("P80 Duration", s.p80_duration_days + "d", st) +
        metricBox("Path Criticality Index", s.path_criticality_index.toFixed(2), st) +
        metricBox("Baseline", s.baseline_days + "d", "green")
      }</div>` +
      reasons([
        `The P80 network duration is ${s.p80_duration_days} days against a ${s.baseline_days}-day deterministic baseline; the gap is the schedule risk the stochastic network exposes.`,
        `The dominant (structural) path is critical in ${Math.round(s.path_criticality_index * 100)}% of simulated runs — that is where float is thinnest.`
      ], st) +
      rule("GREEN if P80 <= +15% of baseline; AMBER if +15-30%; RED if > +30%. Lower SPI widens the pessimistic activity bound."));
  }

  function m05(s) {
    const st = simCls(s.status_color);
    return panel("05", "LOB — Production Velocity", st,
      note("Line of Balance (LOB). Production velocity analysis for sequential operations. Monitors the time buffer between lead and follow-on crews. Buffer erosion is a leading schedule indicator — it appears before the delay reaches the critical path and before it registers in the SPI.") +
      lobChart(s) +
      `<div class="dd-grid">${
        metricBox("Min Buffer (days)", s.minimum_buffer_days.toFixed(1), st) +
        metricBox("Critical Unit", String(s.critical_unit_index), st) +
        metricBox("Grading Rate", s.grading_rate + "/d", "green") +
        metricBox("Paving Rate", s.paving_rate + "/d", st)
      }</div>` +
      reasons([
        `The follower (paving ${s.paving_rate} units/day) trails the leader (grading ${s.grading_rate} units/day); the crew-to-crew schedule buffer falls to ${s.minimum_buffer_days.toFixed(1)} days.`,
        `Lower SPI slows the follower, eroding the buffer sooner — the marked critical unit is where collision risk peaks.`
      ], st) +
      rule("GREEN if minimum crew buffer > 3.0 days; AMBER if <= 3.0; RED if <= 1.5."));
  }

  function m06(s) {
    const st = simCls(s.status_color);
    return panel("06", "CCPM — Buffer Health", st,
      note("Critical Chain Project Management (CCPM). Tracks the rate at which the project buffer is being consumed against the rate of chain completion. A project burning buffer faster than it is completing work is on a trajectory toward delay, regardless of what the current SPI reports.") +
      ccpmChart(s) +
      `<div class="dd-grid">${
        metricBox("Chain Complete %", s.pct_chain_complete + "%", "green") +
        metricBox("Buffer Consumed %", s.pct_buffer_consumed + "%", st) +
        metricBox("Zone", String(s.zone).toUpperCase(), st) +
        metricBox("Status", st.toUpperCase(), st)
      }</div>` +
      reasons([
        `Buffer is ${s.pct_buffer_consumed}% consumed at ${s.pct_chain_complete}% chain completion — the fever-chart dot sits in the ${String(s.zone).toUpperCase()} zone.`,
        `Amber when buffer-burn >= chain completion; red when it crosses completion + (100 - completion)/3.`
      ], st) +
      rule("GREEN below the amber line; AMBER when buffer consumed >= chain complete %; RED beyond the upper fever band."));
  }

  function m07(s) {
    const st = simCls(s.status_color);
    return panel("07", "RCF — Cost Prior", st,
      note("Reference Class Forecasting (RCF). Outside-view cost estimate derived from the historical overrun distribution of comparable public infrastructure projects. Corrects for optimism bias in contractor estimates by anchoring the forecast to what projects of this type actually cost.") +
      rcfChart(s) +
      `<div class="dd-grid">${
        metricBox("P50 Adjusted", moneyShort(s.rcf_p50_adjusted), "green") +
        metricBox("P80 Adjusted", moneyShort(s.rcf_p80_adjusted), st) +
        metricBox("Debiasing Factor", "x" + s.debiasing_factor.toFixed(2), st) +
        metricBox("vs BAC %", (s.vs_bac_pct >= 0 ? "+" : "") + s.vs_bac_pct.toFixed(1) + "%", st)
      }</div>` +
      reasons([
        `The outside-view reference class puts the P80 cost prior at ${moneyShort(s.rcf_p80_adjusted)} — ${(s.vs_bac_pct >= 0 ? "+" : "") + s.vs_bac_pct.toFixed(1)}% over the Budget at Completion (BAC).`,
        `The debiasing factor x${s.debiasing_factor.toFixed(2)} is the empirical correction applied to the inside-view estimate.`
      ], st) +
      rule("GREEN if P80 prior <= +10% of BAC; AMBER if +10-25%; RED if > +25%."));
  }

  function m08(s) {
    const st = simCls(s.status_color);
    return panel("08", "DSM — Rework Propagation", st,
      note("Design Structure Matrix (DSM). Models how a scope change in one design discipline propagates through downstream disciplines. An architectural revision triggers structural re-coordination and MEP rerouting. The rework multiplier quantifies the total coordination burden a single change introduces across the design team.") +
      dsmChart(s) +
      `<div class="dd-grid">${
        metricBox("Rework Multiplier", "x" + s.rework_multiplier.toFixed(2), st) +
        metricBox("Arch Impact", s.arch_impact.toFixed(2), "green") +
        metricBox("Structural Impact", s.structural_impact.toFixed(2), st) +
        metricBox("MEP Impact", s.mep_impact.toFixed(2), st)
      }</div>` +
      reasons([
        `A unit architectural scope change propagates to x${s.rework_multiplier.toFixed(2)} cumulative rework across the three disciplines after four DSM passes.`,
        `Structural (${s.structural_impact.toFixed(2)}) and MEP (${s.mep_impact.toFixed(2)}) absorb the downstream burden the dependency matrix transmits.`
      ], st) +
      rule("GREEN if total rework multiplier <= 2.5; AMBER if > 2.5. Off-diagonal weights are the inter-discipline coupling strengths."));
  }

  function m11(s, project) {
    const st = simCls(s.status_color);
    // Derive conservative state on-the-fly if not stored on the signal
    let conservativeState = s.conservative_state;
    if (!conservativeState && project && window.deriveDecision) {
      try { conservativeState = deriveDecision(project).healthState; } catch (e) { /* non-fatal */ }
    }
    const agrees = conservativeState &&
      s.status_color.toLowerCase() === conservativeState.toLowerCase().replace("-review", "");

    const comparisonNote = conservativeState
      ? (agrees
        ? `DST confirms the conservative dominance result — both methods classify this project as ${conservativeState.toUpperCase()}.`
        : `DST diverges from conservative dominance. Conservative dominance classifies ${conservativeState.toUpperCase()}; DST assigns highest belief to ${s.status_color.toUpperCase()} with conflict mass ${Math.round((s.conflict_mass || 0) * 100)}% indicating significant inter-signal disagreement. The divergence itself is a governance signal.`)
      : `Conservative dominance state not yet available — run signals to compare.`;

    return panel("11", "DST — Evidence Combination", st,
      note("Dempster-Shafer Evidence Theory combines the four primary signal classes into a unified belief distribution. Unlike conservative dominance which takes the worst single signal, DST weights all evidence and produces explicit belief masses for each state plus a conflict mass measuring inter-signal disagreement.") +
      dstChart(s) +
      `<div class="dd-grid">${
        metricBox("Belief Green", Math.round((s.belief_green || 0) * 100) + "%", "green") +
        metricBox("Belief Amber", Math.round((s.belief_amber || 0) * 100) + "%", "amber") +
        metricBox("Belief Red", Math.round((s.belief_red || 0) * 100) + "%", s.belief_red > 0.3 ? "red" : "amber") +
        metricBox("Conflict Mass", Math.round((s.conflict_mass || 0) * 100) + "%", s.conflict_level === "High" ? "red" : s.conflict_level === "Moderate" ? "amber" : "green") +
        metricBox("Conflict Level", s.conflict_level || "Low", s.conflict_level === "High" ? "red" : s.conflict_level === "Moderate" ? "amber" : "green") +
        metricBox("Agrees with Module 10", agrees ? "Yes" : (conservativeState ? "No" : "N/A"), agrees ? "green" : (conservativeState ? "amber" : "green"))
      }</div>` +
      `<p class="dd-chart-note">${esc(comparisonNote)}</p>` +
      reasons([
        `DST assigns belief Green ${Math.round((s.belief_green || 0) * 100)}%, Amber ${Math.round((s.belief_amber || 0) * 100)}%, Red ${Math.round((s.belief_red || 0) * 100)}% — highest belief mass determines the output state.`,
        `Conflict mass ${Math.round((s.conflict_mass || 0) * 100)}% (${s.conflict_level || "Low"}) reflects disagreement between the four evidence sources. High conflict mass is itself a signal worth surfacing to the governance layer.`
      ], st) +
      rule("DST RULE: Belief masses assigned per signal class performance against thresholds. Dempster combination rule applied iteratively across four sources. Final state = highest belief mass. Conflict mass > 30% = high inter-signal disagreement."));
  }

  /* Module 12 chart: lower/upper/boundary zone horizontal stacked bar. */
  function roughSetsChart(s) {
    const h = 96, pad = 40, barY = 32, barH = 24, span = W - pad - 24;
    const lower = s.lower_approximation || [];
    const upper = s.upper_approximation || [];
    const boundary = s.boundary_region || [];
    const states = ["Green", "Amber", "Red"];
    const cols = { Green: COLOR.green, Amber: COLOR.amber, Red: COLOR.red };
    let x = pad, bars = "", ticks = "";
    const seg = span / 3;
    states.forEach(function (state, i) {
      const inLower = lower.indexOf(state) >= 0;
      const inUpper = upper.indexOf(state) >= 0;
      const inBoundary = boundary.indexOf(state) >= 0;
      const col = cols[state];
      const op = inLower ? "0.85" : inBoundary ? "0.45" : "0.12";
      bars += `<rect x="${(pad + i * seg).toFixed(1)}" y="${barY}" width="${(seg - 3).toFixed(1)}" height="${barH}" rx="3" fill="${col}" opacity="${op}"></rect>`;
      const zone = inLower ? "Definite" : inBoundary ? "Borderline" : "Outside";
      ticks += `<text x="${(pad + i * seg + seg / 2).toFixed(1)}" y="${barY + barH / 2 + 5}" text-anchor="middle" class="mod-axis" fill="var(--text)" font-size="9">${zone}</text>`;
    });
    return svgo(h, "Rough Sets lower/upper/boundary approximation") +
      bars + ticks +
      `<text x="${pad}" y="${barY + barH + 16}" class="mod-axis" fill="${COLOR.green}">Green</text>` +
      `<text x="${(pad + seg + seg / 2).toFixed(1)}" y="${barY + barH + 16}" text-anchor="middle" class="mod-axis" fill="${COLOR.amber}">Amber</text>` +
      `<text x="${(pad + 2 * seg + seg - 2).toFixed(1)}" y="${barY + barH + 16}" text-anchor="end" class="mod-axis" fill="${COLOR.red}">Red</text>` +
      "</svg>";
  }

  /* Module 13 chart: T/I/F triple horizontal bars. */
  function neutroChart(s) {
    const h = 116, pad = 70, barY = 20, barH = 18, rowGap = 26, span = W - pad - 40;
    const rows = [
      { label: "Truth (T)", val: s.T || 0, col: COLOR.green },
      { label: "Indeterminacy (I)", val: s.I || 0, col: COLOR.amber },
      { label: "Falsity (F)", val: s.F || 0, col: COLOR.red }
    ];
    return svgo(h, "Neutrosophic T/I/F membership bars") +
      rows.map(function (r, i) {
        const y = barY + i * rowGap;
        const w = (r.val * span).toFixed(1);
        return `<text x="4" y="${y + 13}" class="mod-axis" fill="var(--text)">${r.label}</text>` +
          `<rect x="${pad}" y="${y}" width="${span}" height="${barH}" rx="3" fill="var(--surface-soft)" stroke="var(--ring-line)"></rect>` +
          `<rect x="${pad}" y="${y}" width="${w}" height="${barH}" rx="3" fill="${r.col}" opacity="0.8"></rect>` +
          `<text x="${(pad + parseFloat(w) + 5).toFixed(1)}" y="${y + 13}" class="mod-axis" fill="${r.col}">${Math.round(r.val * 100)}%</text>`;
      }).join("") +
      "</svg>";
  }

  /* Module 14 chart: interval bars for Green/Amber/Red showing lower-upper spread. */
  function ifChart(s) {
    const h = 116, pad = 70, barY = 20, barH = 18, rowGap = 26, span = W - pad - 40;
    const rows = [
      { label: "Green interval", vals: s.green_interval || [0, 0], col: COLOR.green },
      { label: "Amber interval", vals: s.amber_interval || [0, 0], col: COLOR.amber },
      { label: "Red interval",   vals: s.red_interval   || [0, 0], col: COLOR.red   }
    ];
    return svgo(h, "Interval-valued Fuzzy membership ranges") +
      rows.map(function (r, i) {
        const y = barY + i * rowGap;
        const x0 = (pad + r.vals[0] * span).toFixed(1);
        const x1 = (pad + r.vals[1] * span).toFixed(1);
        const wRange = Math.max(0, r.vals[1] - r.vals[0]) * span;
        return `<text x="4" y="${y + 13}" class="mod-axis" fill="var(--text)">${r.label}</text>` +
          `<rect x="${pad}" y="${y}" width="${span}" height="${barH}" rx="3" fill="var(--surface-soft)" stroke="var(--ring-line)"></rect>` +
          `<rect x="${x0}" y="${y}" width="${wRange.toFixed(1)}" height="${barH}" rx="3" fill="${r.col}" opacity="0.7"></rect>` +
          `<line x1="${x0}" y1="${y - 3}" x2="${x0}" y2="${y + barH + 3}" stroke="${r.col}" stroke-width="1.5"></line>` +
          `<line x1="${x1}" y1="${y - 3}" x2="${x1}" y2="${y + barH + 3}" stroke="${r.col}" stroke-width="1.5"></line>` +
          `<text x="${(pad + r.vals[1] * span + 5).toFixed(1)}" y="${y + 13}" class="mod-axis" fill="${r.col}">[${Math.round(r.vals[0] * 100)}, ${Math.round(r.vals[1] * 100)}]%</text>`;
      }).join("") +
      "</svg>";
  }

  function m12(s) {
    const st = simCls(s.status_color);
    const votes = s.signal_votes || {};
    const total = s.total_signals || 1;
    return panel("12", "Rough Sets Classification", st,
      note("Rough Set Theory classifies the project using lower and upper approximations. The lower approximation contains states ALL signals definitively support (>75% agreement). The upper approximation contains states ANY signal supports. The boundary region — upper minus lower — is the indeterminate zone where evidence is insufficient to classify with certainty.") +
      roughSetsChart(s) +
      `<div class="dd-grid">${
        metricBox("Classification", (s.classification || "Unknown").length > 22 ? (s.classification || "").slice(0, 21) + "…" : (s.classification || "Unknown"), st) +
        metricBox("Lower approx.", (s.lower_approximation || []).join(", ") || "None", st) +
        metricBox("Boundary region", (s.boundary_region || []).join(", ") || "None", (s.boundary_region || []).length ? "amber" : "green") +
        metricBox("Green votes", String(votes.Green || 0) + "/" + total, votes.Green >= total * 0.75 ? "green" : "amber") +
        metricBox("Amber votes", String(votes.Amber || 0) + "/" + total, votes.Amber > 0 ? "amber" : "green") +
        metricBox("Red votes", String(votes.Red || 0) + "/" + total, votes.Red > 0 ? "red" : "green")
      }</div>` +
      reasons([
        `Rough Sets classifies this project as "${s.classification || "Unknown"}" based on ${total} signal votes (Green: ${votes.Green || 0}, Amber: ${votes.Amber || 0}, Red: ${votes.Red || 0}).`,
        `Lower approximation (definite states, > 75% agreement): ${(s.lower_approximation || []).join(", ") || "none"}. Boundary region (indeterminate): ${(s.boundary_region || []).join(", ") || "none"}.`
      ], st) +
      rule("GREEN definite if > 75% of signals are green; RED definite if > 75% red; otherwise boundary / borderline. Boundary region is the indeterminate zone requiring additional evidence."));
  }

  function m13(s) {
    const st = simCls(s.status_color);
    const T = Math.round((s.T || 0) * 100), I = Math.round((s.I || 0) * 100), F = Math.round((s.F || 0) * 100);
    return panel("13", "Neutrosophic Logic", st,
      note("Neutrosophic Logic extends fuzzy logic with three independent membership dimensions: Truth (T), Indeterminacy (I), and Falsity (F). Unlike classical logic where T + F = 1, neutrosophic values need not sum to 1 — genuine uncertainty is a separate dimension, not a residual of truth and falsity. High indeterminacy signals measurement ambiguity rather than a positive or negative finding.") +
      neutroChart(s) +
      `<div class="dd-grid">${
        metricBox("Truth (T)", T + "%", T >= 70 ? "green" : T >= 50 ? "amber" : "red") +
        metricBox("Indeterminacy (I)", I + "%", I > 30 ? "red" : I > 15 ? "amber" : "green") +
        metricBox("Falsity (F)", F + "%", F < 10 ? "green" : F < 20 ? "amber" : "red") +
        metricBox("Indeterminacy level", s.indeterminacy_level || "Low", s.indeterminacy_level === "High" ? "red" : s.indeterminacy_level === "Moderate" ? "amber" : "green")
      }</div>` +
      reasons([
        `Neutrosophic combines ${(s.signal_components || []).length} signal source(s) via disjunctive combination (T) and conjunctive combination (I, F).`,
        `T=${T}%, I=${I}%, F=${F}%. Indeterminacy level: ${s.indeterminacy_level || "Low"} — ${I > 30 ? "high uncertainty, governance attention warranted" : I > 15 ? "moderate uncertainty in evidence" : "evidence is sufficiently conclusive"}.`
      ], st) +
      rule("Status set by signal source majority (red if >= 2 red sources, amber if >= 2 amber, else green). Indeterminacy > 30% upgrades green to amber — the uncertainty itself is a governance signal."));
  }

  function m14(s) {
    const st = simCls(s.status_color);
    const gi = (s.green_interval || [0, 0]).map((v) => Math.round(v * 100));
    const ai = (s.amber_interval || [0, 0]).map((v) => Math.round(v * 100));
    const ri = (s.red_interval   || [0, 0]).map((v) => Math.round(v * 100));
    return panel("14", "Interval-valued Fuzzy Sets", st,
      note("Interval-valued Fuzzy Sets represent membership as a range [lower, upper] rather than a single value, reflecting measurement uncertainty in the input signals. The SoV document introduces approximately +/-2% earned-value uncertainty; pay applications introduce approximately +/-1% cost uncertainty. The width of the interval represents how much the classification can shift given realistic input variation.") +
      ifChart(s) +
      `<div class="dd-grid">${
        metricBox("Green interval", `[${gi[0]}, ${gi[1]}]%`, gi[1] > 50 ? "green" : "amber") +
        metricBox("Amber interval", `[${ai[0]}, ${ai[1]}]%`, ai[1] > 40 ? "amber" : "green") +
        metricBox("Red interval",   `[${ri[0]}, ${ri[1]}]%`, ri[1] > 40 ? "red" : ri[1] > 20 ? "amber" : "green") +
        metricBox("Uncertainty width", (s.uncertainty_width || 0).toFixed(2), s.uncertainty_level === "High" ? "red" : s.uncertainty_level === "Moderate" ? "amber" : "green") +
        metricBox("Uncertainty level", s.uncertainty_level || "Low", s.uncertainty_level === "High" ? "red" : s.uncertainty_level === "Moderate" ? "amber" : "green")
      }</div>` +
      reasons([
        `Interval-valued membership reflects +/-2% SoV and +/-1% pay-application input uncertainty. Green [${gi[0]}, ${gi[1]}]%, Amber [${ai[0]}, ${ai[1]}]%, Red [${ri[0]}, ${ri[1]}]%.`,
        `Uncertainty width ${(s.uncertainty_width || 0).toFixed(2)}: ${s.uncertainty_level || "Low"} — ${s.uncertainty_level === "High" ? "wide interval means input noise could shift the classification" : "interval width is within acceptable precision for this signal package"}.`
      ], st) +
      rule("Status = highest midpoint across Green/Amber/Red intervals. Uncertainty level HIGH if combined interval width > 0.30, MODERATE if > 0.15 — corresponds to input noise of roughly +/-3 percentage points on CPI."));
  }

  /* Synthesis comparison panel — Modules 10–14 agreement table. */
  function synthComparisonPanel(project, sims) {
    const arr = sims && sims.signal_array;
    if (!arr) return "";

    const s10 = (function () {
      const s = project.signals;
      if (!s) return null;
      const statuses = [s.evm.status, s.mc.status, s.cusum.status, s.doc.status];
      const redN = statuses.filter((x) => x === "red").length;
      const ambN = statuses.filter((x) => x === "amber").length;
      return redN >= 2 ? "Red" : (redN || ambN) ? "Amber" : "Green";
    })();

    const get = function (method) {
      const sig = fByMethod(arr, method);
      return sig ? (sig.status_color || sig.status || "—") : null;
    };
    const s11 = get("DST_Evidence_Combination");
    const s12 = get("Rough_Sets_Classification");
    const s13 = get("Neutrosophic_Logic");
    const s14 = get("Interval_Fuzzy_Sets");

    const entries = [
      { num: "10", label: "Conservative Dominance", val: s10 },
      { num: "11", label: "Dempster-Shafer",        val: s11 },
      { num: "12", label: "Rough Sets",             val: s12 },
      { num: "13", label: "Neutrosophic",           val: s13 },
      { num: "14", label: "Interval Fuzzy",         val: s14 }
    ].filter(function (e) { return e.val; });

    if (!entries.length || !s10) return "";

    // Compare every method against Module 10 (the governance baseline).
    const baseline = String(s10).toLowerCase();
    const vals = entries.map(function (e) { return String(e.val || "").toLowerCase(); });
    const allAgree   = vals.every(function (v) { return v === baseline; });
    const redCount   = vals.filter(function (v) { return v === "red"; }).length;
    const amberCount = vals.filter(function (v) { return v === "amber"; }).length;
    const greenCount = vals.length - redCount - amberCount;
    const overallSt  = redCount >= 2 ? "red" : amberCount >= 2 ? "amber" : "green";

    const header = `<tr class="dd-cmp-head"><th>Module · Method</th><th>Classification</th><th>Agrees with M10</th></tr>`;
    const rows = entries.map(function (e) {
      const c = cls(e.val);
      const isM10 = e.num === "10";
      const agreesM10 = isM10 ? "—" : (String(e.val).toLowerCase() === baseline ? "Yes" : "No");
      const agreeCls = isM10 ? "" : (agreesM10 === "Yes" ? "dd-cmp-yes" : "dd-cmp-no");
      return `<tr><td class="dd-cmp-mod">Module ${e.num} — ${esc(e.label)}</td>` +
        `<td><span class="dd-verdict status-${c}" style="display:inline-flex;gap:4px;align-items:center"><i></i>${esc(String(e.val).toUpperCase())}</span></td>` +
        `<td class="${agreeCls}">${agreesM10}</td></tr>`;
    }).join("");

    const summaryText = allAgree
      ? `All synthesis methods converge on ${String(s10).toUpperCase()} — high classification confidence.`
      : `Methods diverge — classification uncertainty is itself a governance signal. Spread across methods: ${redCount} Red, ${amberCount} Amber, ${greenCount} Green. Note the divergence in the decision record.`;

    return `<section class="panel dd-panel status-${overallSt}" aria-label="Synthesis comparison">
      <div class="dd-head"><b>Synthesis Methods Comparison — Modules 10–14</b></div>
      <p class="dd-chart-note">Agreement check across all synthesis and evidence methods. Conservative dominance (Module 10) is the governance baseline; Modules 11–14 provide independent cross-checks using different evidence frameworks.</p>
      <table class="dd-cmp-table">${header}${rows}</table>
      <p class="dd-chart-note">${esc(summaryText)}</p>
    </section>`;
  }

  function simModules(project) {
    const payload = project.simulationSignals;
    const baseArr = payload && Array.isArray(payload.signal_array) ? payload.signal_array : null;
    if (!baseArr || !baseArr.length) return { low: "", dst: "", rough: "", neutro: "", ifs: "", synth: "" };

    const pert = fByMethod(baseArr, "PERT_Network_Criticality");
    const lob  = fByMethod(baseArr, "Line_of_Balance_Velocity");
    const ccpm = fByMethod(baseArr, "CCPM_Buffer_Health");
    const rcf  = fByMethod(baseArr, "Reference_Class_Forecasting");
    const dsm  = fByMethod(baseArr, "DSM_Rework_Propagation");

    // Modules 11-14 read the assembled signal package (evm/mc/cusum/doc), not the
    // raw signalInputs. Older persisted signal_arrays (demo seeds and pre-update
    // ingests) only carry Modules 04-08, so compute the evidence-combination
    // models live from project.signals when they are absent — the same fallback
    // the portfolio Signals page uses, so both views always agree.
    const S = window.LinSimulations || {};
    const si = project.signalInputs || {};
    const es = project.signals || {};
    const resolve = (method, fn) => {
      let sig = fByMethod(baseArr, method);
      if (!sig && typeof fn === "function") { try { sig = fn(); } catch (e) { sig = null; } }
      return sig;
    };
    const dst    = resolve("DST_Evidence_Combination", S.runDST          && (() => S.runDST(si, es)));
    const rough  = resolve("Rough_Sets_Classification", S.runRoughSets     && (() => S.runRoughSets(es)));
    const neutro = resolve("Neutrosophic_Logic",        S.runNeutrosophic  && (() => S.runNeutrosophic(es)));
    const ifs    = resolve("Interval_Fuzzy_Sets",       S.runIntervalFuzzy && (() => S.runIntervalFuzzy(es)));

    const low = (pert ? m04(pert) : "") + (lob ? m05(lob) : "") + (ccpm ? m06(ccpm) : "") +
                (rcf ? m07(rcf) : "") + (dsm ? m08(dsm) : "");
    const dstHtml    = dst    ? m11(dst, project) : "";
    const roughHtml  = rough  ? m12(rough)        : "";
    const neutroHtml = neutro ? m13(neutro)       : "";
    const ifsHtml    = ifs    ? m14(ifs)          : "";

    // Feed the comparison panel the same resolved set the cards rendered: the
    // persisted array plus any live-computed evidence modules not already in it.
    const extra = [dst, rough, neutro, ifs]
      .filter(Boolean)
      .filter((s) => !fByMethod(baseArr, s.method_class));
    const synthHtml = synthComparisonPanel(project, { signal_array: baseArr.concat(extra) });

    return { low, dst: dstHtml, rough: roughHtml, neutro: neutroHtml, ifs: ifsHtml, synth: synthHtml };
  }

  /* ---------- entry point ---------- */

  function render(project, root) {
    if (!root) return;
    if (!window.hasSignals || !hasSignals(project)) {
      root.innerHTML =
        `<section class="panel awaiting-state">
           <p><strong>Awaiting ingest — no signals yet.</strong></p>
           <p class="kn-sub">The modules compute from this project's signals. Populate signals (Manage Projects, or the "Ingest" panel above) to run the real Monte Carlo (5,000 iterations) and CUSUM, the keyword document-risk extraction, and the PCEIF synthesis + governance decision. Nothing is computed or fabricated until inputs are ingested.</p>
         </section>`;
      return;
    }
    const sims = simModules(project);
    root.innerHTML =
      `<p class="mod-banner">Modules 01–03 are quantitative analyses of this project's extracted signal inputs. Modules 04–08 are schedule and cost simulation models. Modules 09–10 apply the PCEIF governance decision framework. Modules 11–14 are independent evidence synthesis methods cross-checking the Module 10 result.</p>` +
      m01(project) + m02(project) + m03(project) +
      sims.low +
      m09(project) + m10(project) +
      sims.dst +
      sims.rough + sims.neutro + sims.ifs +
      sims.synth;
  }

  window.LinDeepDive = { render };
})();
