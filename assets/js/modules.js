/* ============================================================
   Lin Project Radar — modules.js
   The five PCEIF simulation modules: plain-language explanation,
   key metrics, the rule that fired, and an ILLUSTRATIVE graph
   driven by the synthetic portfolio. Graphs are labeled
   illustrative — never live or validated model output.

   Module 05 (ABM governance layer) calls the existing pure
   functions in decision.js. The rules are NOT duplicated here.
   ============================================================ */

(function () {
  "use strict";

  const SVG_NS = "http://www.w3.org/2000/svg";
  const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  const statusVar = (s) =>
    s === "green" ? "var(--clear-green)" : s === "amber" ? "var(--radar-amber)" : "var(--alarm-red)";

  /* ---------- tiny SVG chart helpers (no external libs) ---------- */

  function svgOpen(w, h, label) {
    return `<svg viewBox="0 0 ${w} ${h}" class="mod-chart" role="img" aria-label="${esc(label)}">`;
  }

  /* Horizontal bar chart: rows = {label, value (0..max), color, note} */
  function barChart(rows, max, w, refLine) {
    const h = rows.length * 26 + 30;
    const left = 92, right = 64, barMax = w - left - right;
    let out = svgOpen(w, h, "Illustrative bar chart of synthetic data");
    rows.forEach((r, i) => {
      const y = 14 + i * 26;
      const bw = Math.max(2, Math.min(1, r.value / max) * barMax);
      out += `<text x="${left - 8}" y="${y + 11}" text-anchor="end" class="mod-axis">${esc(r.label)}</text>`;
      out += `<rect x="${left}" y="${y}" width="${bw}" height="15" rx="3" fill="${r.color}" opacity="0.85"></rect>`;
      out += `<text x="${left + bw + 6}" y="${y + 11}" class="mod-axis">${esc(r.note)}</text>`;
    });
    if (refLine) {
      const x = left + Math.min(1, refLine.value / max) * barMax;
      out += `<line x1="${x}" y1="6" x2="${x}" y2="${h - 18}" stroke="var(--alarm-red)" stroke-dasharray="4 3" stroke-width="1.5"></line>`;
      out += `<text x="${x + 4}" y="${h - 6}" class="mod-axis" fill="var(--alarm-red)">${esc(refLine.label)}</text>`;
    }
    return out + "</svg>";
  }

  /* Scatter: CPI (x) vs SPI (y), colored by EVM status */
  function cpiSpiScatter(projects, w) {
    const h = 230;
    const pad = 42;
    const minV = 0.75, maxV = 1.10;
    const sx = (v) => pad + ((v - minV) / (maxV - minV)) * (w - pad - 16);
    const sy = (v) => h - 30 - ((v - minV) / (maxV - minV)) * (h - 30 - 14);
    let out = svgOpen(w, h, "Illustrative CPI versus SPI scatter of synthetic projects");
    // axes + 1.0 reference lines
    out += `<line x1="${pad}" y1="${h - 30}" x2="${w - 12}" y2="${h - 30}" stroke="var(--ring-line)"></line>`;
    out += `<line x1="${pad}" y1="10" x2="${pad}" y2="${h - 30}" stroke="var(--ring-line)"></line>`;
    out += `<line x1="${sx(1)}" y1="10" x2="${sx(1)}" y2="${h - 30}" stroke="var(--ring-line)" stroke-dasharray="3 4"></line>`;
    out += `<line x1="${pad}" y1="${sy(1)}" x2="${w - 12}" y2="${sy(1)}" stroke="var(--ring-line)" stroke-dasharray="3 4"></line>`;
    out += `<text x="${w - 14}" y="${h - 14}" text-anchor="end" class="mod-axis">CPI →</text>`;
    out += `<text x="${pad - 30}" y="18" class="mod-axis">SPI ↑</text>`;
    out += `<text x="${sx(1) + 3}" y="${h - 34}" class="mod-axis">1.00</text>`;
    projects.forEach((p) => {
      const e = p.signals.evm;
      out += `<circle cx="${sx(e.cpi)}" cy="${sy(e.spi)}" r="6" fill="${statusVar(e.status)}" opacity="0.9"></circle>`;
      out += `<text x="${sx(e.cpi) + 8}" y="${sy(e.spi) + 4}" class="mod-axis">${esc(p.id)}</text>`;
    });
    return out + "</svg>";
  }

  /* ---------- Modules 06-10 helpers (simulation aggregation across portfolio) ---------- */

  // Build a signalInputs object for a project — prefer extracted inputs;
  // fall back to the canonical Monte Carlo input record (cpi/spi/bac/docScore)
  // with synthetic % complete so the CCPM module has something to read.
  function siFor(p) {
    if (p && p.signalInputs && Object.keys(p.signalInputs).length) return p.signalInputs;
    const e = p && p.signals && p.signals.evm;
    if (!e) return {};
    return {
      cpi: e.cpi, spi: e.spi, bac: e.bac,
      docRiskScore: p.signals.doc ? p.signals.doc.score : 0,
      // proxies so CCPM has chain-complete to read; the bar simply uses buffer-consumed
      actualPctComplete: 40, plannedPctComplete: 40,
    };
  }
  function simByMethod(arr, method) { return arr.find((s) => s.method_class === method); }
  // Run a single simulation model for every project, returning [{p, sig}].
  function runEachProject(projects, method, runner) {
    return projects.map((p) => {
      // prefer the persisted simulationSignals.signal_array when available
      const arr = p.simulationSignals && Array.isArray(p.simulationSignals.signal_array)
        ? p.simulationSignals.signal_array : null;
      const sig = (arr && simByMethod(arr, method)) || runner(siFor(p));
      return { p, sig };
    });
  }
  const simColor = (s) => statusVar(String(s || "green").toLowerCase());

  function module06(projects) {
    const results = runEachProject(projects, "PERT_Network_Criticality",
      window.LinSimulations ? LinSimulations.runPERT : () => ({ status_color: "Green", p80_duration_days: 0, path_criticality_index: 0 }));
    const rows = results.map(({ p, sig }) => ({
      label: p.id, value: Math.max(0.1, sig.p80_duration_days || 0),
      color: simColor(sig.status_color),
      note: `${(sig.p80_duration_days || 0).toFixed(1)}d · crit ${Math.round((sig.path_criticality_index || 0) * 100)}%`,
    }));
    const worst = results.slice().sort((a, b) => (b.sig.p80_duration_days || 0) - (a.sig.p80_duration_days || 0))[0];
    const max = Math.max(1, ...rows.map((r) => r.value)) * 1.15;
    return {
      num: "06",
      title: "Program Evaluation & Review Technique (PERT) — Network Criticality",
      method: "Stochastic 3-activity network · triangular distribution · 5,000 iterations · te = (a + 4m + b) / 6",
      explain: "PERT samples each activity's optimistic / most-likely / pessimistic durations from a triangular distribution and aggregates the dominant network path. The P80 duration is the conservative finish date; the path-criticality index is the share of simulated runs where the structural path was on the critical path. Lower project SPI widens the pessimistic bound, so the P80 tail grows when the schedule is already drifting.",
      rule: `Rule fired: P80 ≤ baseline → Green; P80 up to +20% → Amber; > +20% → Red. Worst current: ${worst ? worst.p.id : "—"}${worst ? ` (P80 ${(worst.sig.p80_duration_days || 0).toFixed(1)}d)` : ""}.`,
      charts:
        `<p class="mod-chart-label">Illustrative view — PERT P80 duration by project (days)</p>` +
        barChart(rows, max, 520),
    };
  }

  function module07(projects) {
    const results = runEachProject(projects, "Line_of_Balance_Velocity",
      window.LinSimulations ? LinSimulations.runLOB : () => ({ status_color: "Green", minimum_buffer_days: 5 }));
    // value = min crew buffer (days). Red threshold marker at 1.5d.
    const rows = results.map(({ p, sig }) => ({
      label: p.id, value: Math.max(0.05, sig.minimum_buffer_days || 0),
      color: simColor(sig.status_color),
      note: `${(sig.minimum_buffer_days || 0).toFixed(1)}d · crit unit ${sig.critical_unit_index ?? "—"}`,
    }));
    const worst = results.slice().sort((a, b) => (a.sig.minimum_buffer_days || 0) - (b.sig.minimum_buffer_days || 0))[0];
    const max = Math.max(6, ...rows.map((r) => r.value)) * 1.15;
    return {
      num: "07",
      title: "Line of Balance (LOB) — Production Velocity",
      method: "Leader (grading) vs follower (paving) crew velocity · minimum crew-to-crew buffer over linear units",
      explain: "LOB tracks production rate for sequential, repetitive work. Each crew has a units-per-day velocity; the buffer is the schedule gap between the leader and the follower as units roll. When the follower (paving) slows and that buffer compresses unit by unit, a crew collision is being telegraphed before EVM moves. The implementation slows the follower as project SPI degrades, making buffer collapse a leading schedule signal.",
      rule: `Rule fired: buffer > 3.0d → Green; 1.5–3.0d → Amber; ≤ 1.5d → Red. Worst current: ${worst ? worst.p.id : "—"}${worst ? ` (min buffer ${(worst.sig.minimum_buffer_days || 0).toFixed(1)}d)` : ""}.`,
      charts:
        `<p class="mod-chart-label">Illustrative view — minimum crew buffer by project (days; red ≤ 1.5d)</p>` +
        barChart(rows, max, 520, { value: 1.5, label: "red ≤ 1.5d" }),
    };
  }

  function module08(projects) {
    const results = runEachProject(projects, "CCPM_Buffer_Health",
      window.LinSimulations ? LinSimulations.runCCPM : () => ({ status_color: "Green", pct_buffer_consumed: 10, pct_chain_complete: 50 }));
    const rows = results.map(({ p, sig }) => ({
      label: p.id, value: Math.max(0.5, sig.pct_buffer_consumed || 0),
      color: simColor(sig.status_color),
      note: `${(sig.pct_buffer_consumed || 0).toFixed(1)}% buf @ ${(sig.pct_chain_complete || 0).toFixed(1)}% chain`,
    }));
    const worst = results.slice().sort((a, b) => (b.sig.pct_buffer_consumed || 0) - (a.sig.pct_buffer_consumed || 0))[0];
    return {
      num: "08",
      title: "Critical Chain Project Management (CCPM) — Buffer Health",
      method: "Fever-chart logic: buffer-consumed % vs chain-complete %",
      explain: "CCPM aggregates safety margin from each activity into a single project buffer, then plots its consumption against chain completion. The fever chart's amber threshold sits at the chain-complete percentage; the red threshold a third of the remaining range above that. Crossing into red means buffer is being burned faster than work is being completed — the buffer will be gone before the chain.",
      rule: "Rule fired: below the amber line → Green; buffer consumed ≥ % complete → Amber; ≥ % complete + (100 − % complete)/3 → Red." +
        (worst ? ` Worst current: ${worst.p.id} (${(worst.sig.pct_buffer_consumed || 0).toFixed(1)}% buffer).` : ""),
      charts:
        `<p class="mod-chart-label">Illustrative view — buffer consumed by project (%)</p>` +
        barChart(rows, 100, 520),
    };
  }

  function module09(projects) {
    const results = runEachProject(projects, "Reference_Class_Forecasting",
      window.LinSimulations ? LinSimulations.runRCF : () => ({ status_color: "Red", vs_bac_pct: 38, debiasing_factor: 1.38 }));
    const rows = results.map(({ p, sig }) => ({
      label: p.id, value: Math.max(0.5, sig.vs_bac_pct || 0),
      color: simColor(sig.status_color),
      note: `+${(sig.vs_bac_pct || 0).toFixed(1)}% · ×${(sig.debiasing_factor || 0).toFixed(2)}`,
    }));
    const max = Math.max(30, ...rows.map((r) => r.value)) * 1.15;
    return {
      num: "09",
      title: "Reference Class Forecasting (RCF) — Cost Prior",
      method: "Outside-view debiasing · airport-overrun multiplier reference class · P80 vs BAC",
      explain: "Flyvbjerg's reference-class forecasting replaces the inside-view estimate with an empirical prior drawn from comparable projects. This implementation uses an airport-infrastructure overrun multiplier set; the P80 multiplier is the conservative debiasing factor applied to BAC. It is the structural counter to optimism bias — what comparable projects actually cost, not what this one's bottom-up estimate predicts.",
      rule: `Rule fired: P80 prior ≤ +10% of BAC → Green; +10–25% → Amber; > +25% → Red.`,
      charts:
        `<p class="mod-chart-label">Illustrative view — RCF P80 prior vs BAC by project (%)</p>` +
        barChart(rows, max, 520, { value: 25, label: "red > +25%" }),
    };
  }

  function module10(projects) {
    const results = runEachProject(projects, "DSM_Rework_Propagation",
      window.LinSimulations ? LinSimulations.runDSM : () => ({ status_color: "Amber", rework_multiplier: 2.7 }));
    const rows = results.map(({ p, sig }) => ({
      label: p.id, value: Math.max(0.1, sig.rework_multiplier || 0),
      color: simColor(sig.status_color),
      note: `×${(sig.rework_multiplier || 0).toFixed(2)}`,
    }));
    const max = Math.max(4, ...rows.map((r) => r.value)) * 1.15;
    return {
      num: "10",
      title: "Design Structure Matrix (DSM) — Rework Propagation",
      method: "3×3 Arch / Structural / MEP dependency matrix · architectural change vector · 4 propagation passes",
      explain: "DSM captures information-flow dependencies between design disciplines as off-diagonal coupling weights. A single unit of architectural change is propagated through the matrix; after four passes the cumulative rework multiplier is the total downstream burden across Arch / Structural / MEP. Architectural changes cascade because both downstream disciplines depend on Arch decisions, so a multiplier above 2.5 signals high coordination risk.",
      rule: `Rule fired: total rework multiplier ≤ 2.5 → Green; > 2.5 → Amber.`,
      charts:
        `<p class="mod-chart-label">Illustrative view — DSM rework multiplier by project (×)</p>` +
        barChart(rows, max, 520, { value: 2.5, label: "amber > 2.5" }),
    };
  }

  /* ---------- module definitions ---------- */

  function module01(projects) {
    const worst = projects.slice().sort((a, b) => a.signals.evm.cpi - b.signals.evm.cpi)[0];
    const p80rows = projects.map((p) => ({
      label: p.id,
      value: Math.max(0.1, p.signals.mc.p80eacOverrunPct),
      color: statusVar(p.signals.mc.status),
      note: `+${p.signals.mc.p80eacOverrunPct.toFixed(1)}%`
    }));
    return {
      num: "01",
      title: "Hybrid Dynamic Simulation",
      method: "EVM (CPI / SPI) + Monte Carlo P80 EAC",
      explain: "The cost and schedule core. CPI = EV/AC and SPI = EV/PV measure performance against the approved baseline; the probabilistic forecast layers P80 EAC exposure on top, so emerging overrun risk is visible before it is fully realized in the variance.",
      rule: `Rule fired: CPI or SPI < 0.95 → amber; < 0.90 → red. Worst current: ${worst.id} (CPI ${worst.signals.evm.cpi.toFixed(2)}, SPI ${worst.signals.evm.spi.toFixed(2)}).`,
      charts:
        `<p class="mod-chart-label">Illustrative view — CPI vs SPI (synthetic portfolio)</p>` +
        cpiSpiScatter(projects, 520) +
        `<p class="mod-chart-label">Illustrative view — P80 EAC overrun exposure (%)</p>` +
        barChart(p80rows, 25, 520)
    };
  }

  function module02(projects) {
    const rows = projects.map((p) => ({
      label: p.id,
      value: p.signals.cusum.drift,
      color: p.signals.cusum.breached ? "var(--alarm-red)" : statusVar(p.signals.cusum.status),
      note: `${p.signals.cusum.drift.toFixed(1)}${p.signals.cusum.breached ? " ⚑ breach" : ""}`
    }));
    const breached = projects.filter((p) => p.signals.cusum.breached);
    return {
      num: "02",
      title: "SPC / CUSUM Anomaly Monitor",
      method: "Cumulative-sum drift vs control threshold 5.0",
      explain: "Statistical process control for slow slides. CUSUM accumulates small period deviations so a sustained drift is caught before any single period would trip a variance threshold. A breach hands the question to the governance layer — it never acts on its own.",
      rule: `Rule fired: cumulative drift ≥ 5.0 → breach. Currently breached: ${breached.length ? breached.map((p) => p.id).join(", ") : "none"}.`,
      charts:
        `<p class="mod-chart-label">Illustrative view — CUSUM drift by project (threshold 5.0)</p>` +
        barChart(rows, 8, 520, { value: 5.0, label: "threshold 5.0" })
    };
  }

  function module03(projects) {
    const rows = projects.map((p) => ({
      label: p.id,
      value: p.signals.doc.score,
      color: statusVar(p.signals.doc.status),
      note: p.signals.doc.score.toFixed(2)
    }));
    return {
      num: "03",
      title: "Document-Risk Extraction",
      method: "Visible keyword / rule extraction over project records",
      explain: "RFIs, submittals, QC comments, and procurement notes often deteriorate before CPI/SPI do. This module scores risk language with transparent keyword rules — the same rules the Manage Projects page runs — and carries the matched excerpt as evidence. No NLP model, no LLM: every match is inspectable.",
      rule: "Rule fired: score ≥ 0.30 → amber; ≥ 0.70 → red. Source file and matched excerpt are shown in the signal ledger.",
      charts:
        `<p class="mod-chart-label">Illustrative view — document-risk score by project</p>` +
        barChart(rows, 1.0, 520, { value: 0.70, label: "red ≥ 0.70" })
    };
  }

  function module04(projects) {
    const counts = {};
    projects.forEach((p) => {
      const c = classifyConflict(p);
      counts[c] = (counts[c] || 0) + 1;
    });
    const palette = {
      "Multi-signal red-review": "var(--alarm-red)",
      "Anomaly without narrative": "var(--alarm-red)",
      "Forecast ahead of status": "var(--radar-amber)",
      "Leading document risk": "var(--radar-amber)",
      "Mixed early warning": "var(--radar-amber)",
      "Agreement — low risk": "var(--clear-green)"
    };
    const rows = Object.entries(counts).map(([label, n]) => ({
      label: label.length > 14 ? label.slice(0, 13) + "…" : label,
      value: n,
      color: palette[label] || "var(--phosphor)",
      note: `${n} project${n > 1 ? "s" : ""}`
    }));
    return {
      num: "04",
      title: "Signal Synthesis",
      method: "Conflict classification (classifyConflict in decision.js)",
      explain: "PCEIF surfaces disagreement between signal classes instead of averaging it away. A green EVM with deteriorating documents, or a red forecast over an acceptable baseline, is itself the finding. The precedence order of the conflict labels is deliberate and documented in decision.js.",
      rule: "Rule fired: precedence — multi-red ▸ anomaly-without-narrative ▸ forecast-ahead ▸ leading-doc-risk ▸ agreement ▸ mixed early warning.",
      charts:
        `<p class="mod-chart-label">Illustrative view — conflict-type distribution (synthetic portfolio)</p>` +
        barChart(rows, Math.max(...Object.values(counts)) + 1, 520)
    };
  }

  function module05(projects) {
    // Calls the existing decision.js pure functions — no duplicated rules.
    const decisions = projects.map((p) => ({ p, d: deriveDecision(p) }));
    const byState = { "Green": [], "Amber": [], "Red-review": [] };
    decisions.forEach(({ p, d }) => (byState[d.healthState] || (byState[d.healthState] = [])).push({ p, d }));
    const gates = decisions.filter(({ d }) => d.fairnessGateRequired);

    const stateColor = { "Green": "var(--clear-green)", "Amber": "var(--radar-amber)", "Red-review": "var(--alarm-red)" };
    const rows = Object.entries(byState).map(([state, list]) => ({
      label: state, value: list.length, color: stateColor[state], note: `${list.length}`
    }));

    const table = decisions.map(({ p, d }) =>
      `<tr>
         <td><button class="mod-link mod-mono" data-open="${esc(p.id)}" title="Open ${esc(p.id)} project detail">${esc(p.id)}</button></td>
         <td><span class="pill pill-${d.healthState.toLowerCase().replace("-review", "")}">${esc(d.healthState)}</span></td>
         <td>${esc(d.authority)}</td>
         <td>${d.fairnessGateRequired ? "⚑ gate required" : "—"}</td>
       </tr>`).join("");

    return {
      num: "05",
      title: "ABM — Agent-Based Governance Layer",
      method: "deriveDecision / deriveHealthState / classifyConflict (decision.js — called live, not duplicated)",
      explain: "The governance layer is modeled as agents: each authority role (PM, controls lead, program director) holds explicit decision rules over the signal package. Those rules ARE the pure functions in decision.js — this module surfaces them. The mapping (health state × conflict × fairness sensitivity) → recommended action, authority, and documentation is the same logic that drives the decision card on the radar page.",
      rule: `Rule fired: red-review requires ≥2 red signals or CUSUM breach + red forecast; fairness-sensitive red-reviews additionally require the contractor fairness gate (currently: ${gates.length ? gates.map(({ p }) => p.id).join(", ") : "none"}).`,
      charts:
        `<p class="mod-chart-label">Illustrative view — derived state distribution (live call to decision.js)</p>` +
        barChart(rows, Math.max(1, ...rows.map((r) => r.value)) + 1, 520) +
        `<table class="mod-table">
           <thead><tr><th>Project</th><th>Derived state</th><th>Authority (from rules)</th><th>Fairness</th></tr></thead>
           <tbody>${table}</tbody>
         </table>`
    };
  }

  /* ---------- page rendering ---------- */

  function moduleCardsHtml(projects) {
    const mods = [
      module01(projects), module02(projects), module03(projects), module04(projects), module05(projects),
      module06(projects), module07(projects), module08(projects), module09(projects), module10(projects),
    ];
    return mods.map((m) => `
        <section class="panel mod-card" aria-label="Module ${m.num}: ${esc(m.title)}">
          <div class="mod-head">
            <span class="mod-num">MODULE ${m.num}</span>
            <h2>${esc(m.title)}</h2>
          </div>
          <p class="mod-method">${esc(m.method)}</p>
          <p class="mod-explain">${esc(m.explain)}</p>
          <p class="mod-rule">${esc(m.rule)}</p>
          ${m.charts}
        </section>`).join("");
  }

  const BANNER = `<p class="mod-banner">All graphs below are <strong>illustrative views of the synthetic demonstration data</strong> — they are not live or validated model output.</p>`;

  /* Whole-portfolio overview (Signals nav item; internal key stays "modules").
     Only POPULATED projects appear in the overview charts; empty projects are
     awaiting ingest and have nothing to chart yet. */
  function renderModulesPage() {
    const root = document.getElementById("modules-root");
    if (!root) return;
    const populated = LIN_PROJECTS.filter((p) => window.hasSignals && hasSignals(p));
    const emptyCount = LIN_PROJECTS.length - populated.length;
    const emptyNote = emptyCount
      ? `<p class="kn-sub">${emptyCount} project(s) awaiting ingest are not charted here — populate their signals on Manage Projects.</p>`
      : "";
    if (!populated.length) {
      root.innerHTML = BANNER +
        `<section class="panel awaiting-state"><p><strong>No populated projects yet.</strong></p>
         <p class="kn-sub">Create a project and populate its signals on Manage Projects to see the five signal modules across the portfolio. Empty projects are shown on the radar in an awaiting-ingest state, not charted here.</p></section>`;
      return;
    }
    root.innerHTML = BANNER + emptyNote + moduleCardsHtml(populated);
    root.querySelectorAll("[data-open]").forEach((b) =>
      b.addEventListener("click", () => LinApp.openDetail(b.dataset.open)));
  }

  /* All five modules computed for ONE project (Project Detail page).
     Same builders, single-project array — no duplicated rules anywhere;
     Module 05 still calls decision.js live. */
  function renderProjectModules(project, root) {
    if (!root) return;
    root.innerHTML = BANNER + moduleCardsHtml([project]);
  }

  window.LinModules = { renderModulesPage, renderProjectModules };
})();
