/* ============================================================================
   Per-module charts, rendered inline in the Signal Ledger from the STORED row.

   Before computation moved server-side, each module drew its own chart of its
   working in the browser. That computation is now the server's, and the browser
   renders only what was stored. A module qualifies for a chart here ONLY when
   the stored result already holds a labelled, multi-value breakdown that the
   module itself produced (an array of {label, value} pairs, or a small
   distribution over named outcomes). Nothing is derived, interpolated or
   synthesised: every bar is a value the server wrote to module_results, read
   back verbatim through getModuleResult().

   A module whose stored result is a single scalar or a verdict is NOT charted
   here. A one-bar bar chart would manufacture the appearance of a distribution
   the stored result does not hold, which is exactly the defect the analytical
   layer removed. Such a module simply shows its status and one-line finding.

   NAMING: no module id or number appears in any title, label or tooltip. Bars
   are labelled by the descriptive name the module stored (driver names, outcome
   classes, scenario names). No em dashes.
   ============================================================================ */

(function () {
  "use strict";

  function num(v) { return (typeof v === "number" && isFinite(v)) ? v : null; }

  /* Build a chart spec from a stored module result, or null when this module is
     not one of the charted kinds (or its stored fields are absent). Each spec:
       { title, note, unit, bars: [{ label, value }] }
     Values are read verbatim from the stored dict. Bars with a non-finite value
     are dropped rather than drawn as zero, so an absent figure never reads as a
     measured one. */
  function specFor(methodClass, r) {
    if (!r) return null;

    // Which inputs most move the forecast. Stored: drivers[].name / .sensitivity.
    if (methodClass === "Sensitivity_Analysis" && Array.isArray(r.drivers)) {
      var sb = r.drivers
        .map(function (d) { return { label: String(d.name), value: num(d.sensitivity) }; })
        .filter(function (b) { return b.value !== null; });
      if (sb.length < 2) return null;
      return { title: "Input sensitivity", note: "How much each input moves the forecast.",
               unit: "index", bars: sb };
    }

    // Ranked risk drivers. Stored: risks[].name / .impact.
    if (methodClass === "Tornado_Diagram" && Array.isArray(r.risks)) {
      var tb = r.risks
        .map(function (d) { return { label: String(d.name), value: num(d.impact) }; })
        .filter(function (b) { return b.value !== null; });
      if (tb.length < 2) return null;
      return { title: "Risk driver impact", note: "Each driver's contribution to the risk score.",
               unit: "", bars: tb };
    }

    // Competing objectives and how each scores. Stored: objectives[].name / .score.
    if (methodClass === "Multi_Objective_Optimization" && Array.isArray(r.objectives)) {
      var ob = r.objectives
        .map(function (d) { return { label: String(d.name), value: num(d.score) }; })
        .filter(function (b) { return b.value !== null; });
      if (ob.length < 2) return null;
      return { title: "Objective scores", note: "How each competing objective scores now.",
               unit: "", bars: ob };
    }

    // Forecast cost under each scenario. Stored: scenarios[].name / .delta_pct.
    if (methodClass === "WhatIf_Scenario_Matrix" && Array.isArray(r.scenarios)) {
      var wb = r.scenarios
        .map(function (d) { return { label: String(d.name), value: num(d.delta_pct) }; })
        .filter(function (b) { return b.value !== null; });
      if (wb.length < 2) return null;
      return { title: "Scenario cost outlook", note: "Forecast overrun under each scenario.",
               unit: "%", bars: wb };
    }

    // Which decision drivers weigh most. Stored: sensitivity_matrix[].driver / .pct.
    if (methodClass === "Decision_Sensitivity_Matrix" && Array.isArray(r.sensitivity_matrix)) {
      var db = r.sensitivity_matrix
        .map(function (d) { return { label: String(d.driver), value: num(d.pct) }; })
        .filter(function (b) { return b.value !== null; });
      if (db.length < 2) return null;
      return { title: "Decision driver weight", note: "Share of the decision each driver carries.",
               unit: "%", bars: db };
    }

    // Expected regret of each candidate action. Stored: expected_regret{action: value}.
    // RUN 32 FINAL CLOSURE: match the current method class, and the historical one for rows
    // stored before the section-3 rename. Matching only the old identifier meant this chart
    // silently stopped being drawn rather than failing.
    if ((methodClass === "Minimax_Regret_Decision_Rule" || methodClass === "Regret_Minimization") && r.expected_regret && typeof r.expected_regret === "object") {
      var rb = Object.keys(r.expected_regret)
        .map(function (k) { return { label: k.charAt(0).toUpperCase() + k.slice(1), value: num(r.expected_regret[k]) }; })
        .filter(function (b) { return b.value !== null; });
      if (rb.length < 2) return null;
      return { title: "Expected regret by action", note: "Lower is the less regrettable action.",
               unit: "", bars: rb };
    }

    // Probability mass across outcome bands. Stored: probabilities{band: value}.
    if (methodClass === "Maximum_Entropy" && r.probabilities && typeof r.probabilities === "object") {
      var mb = Object.keys(r.probabilities)
        .map(function (k) { return { label: k, value: num(r.probabilities[k]) }; })
        .filter(function (b) { return b.value !== null; });
      if (mb.length < 2) return null;
      return { title: "Outcome likelihood", note: "How the evidence spreads across outcome bands.",
               unit: "%", bars: mb };
    }

    return null;
  }

  function escAttr(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  /* Horizontal bar chart as inline SVG. No dependency: the platform already
     draws every other chart with hand-built inline SVG. Bars scale to the
     largest absolute value in the set; negative values draw left of a baseline
     so a favourable (negative) cost delta is not shown as a tall bar. */
  function barChartSvg(spec) {
    var bars = spec.bars;
    var n = bars.length;
    var maxAbs = 0;
    bars.forEach(function (b) { maxAbs = Math.max(maxAbs, Math.abs(b.value)); });
    if (maxAbs === 0) maxAbs = 1;

    var hasNeg = bars.some(function (b) { return b.value < 0; });
    var rowH = 26, gap = 8, padTop = 6, padBottom = 6;
    var labelW = 148, trackW = 150, valW = 62;
    var W = labelW + trackW + valW + 8;
    var H = padTop + padBottom + n * rowH + (n - 1) * gap;
    var zeroX = labelW + (hasNeg ? trackW / 2 : 0);
    var halfW = hasNeg ? trackW / 2 : trackW;

    var rows = bars.map(function (b, i) {
      var y = padTop + i * (rowH + gap);
      var len = (Math.abs(b.value) / maxAbs) * halfW;
      var x = b.value < 0 ? (zeroX - len) : zeroX;
      var barY = y + 4, barH = rowH - 8;
      var val = b.value;
      var valTxt = (Math.round(val * 100) / 100).toString() + (spec.unit === "%" ? "%" : "");
      return (
        '<text x="' + (labelW - 8) + '" y="' + (y + rowH / 2 + 4) + '" text-anchor="end" ' +
          'class="mchart-label">' + escAttr(b.label) + '</text>' +
        '<rect x="' + labelW + '" y="' + barY + '" width="' + trackW + '" height="' + barH + '" ' +
          'rx="3" class="mchart-track"></rect>' +
        '<rect x="' + x + '" y="' + barY + '" width="' + Math.max(1, len) + '" height="' + barH + '" ' +
          'rx="3" class="mchart-bar' + (b.value < 0 ? ' mchart-bar-neg' : '') + '"></rect>' +
        '<text x="' + (labelW + trackW + 6) + '" y="' + (y + rowH / 2 + 4) + '" ' +
          'class="mchart-value">' + escAttr(valTxt) + '</text>'
      );
    }).join("");

    var zeroLine = hasNeg
      ? '<line x1="' + zeroX + '" y1="' + padTop + '" x2="' + zeroX + '" y2="' + (H - padBottom) +
        '" class="mchart-zero"></line>'
      : "";

    return (
      '<svg class="mchart-svg" viewBox="0 0 ' + W + ' ' + H + '" width="100%" ' +
      'preserveAspectRatio="xMinYMin meet" role="img" ' +
      'aria-label="' + escAttr(spec.title) + '">' + zeroLine + rows + '</svg>'
    );
  }

  /* HTML block for one module's chart, or "" when the module has no chartable
     stored result. Callers append this beneath the module's ledger row. */
  function chartHtmlFor(methodClass, project) {
    if (!window.getModuleResult) return "";
    var r = window.getModuleResult(methodClass, project);
    if (!r) return "";
    var spec = specFor(methodClass, r);
    if (!spec) return "";
    return (
      '<div class="mchart" data-mchart="' + escAttr(methodClass) + '">' +
      '<p class="mchart-title">' + escAttr(spec.title) + '</p>' +
      barChartSvg(spec) +
      '<p class="mchart-note">' + escAttr(spec.note) + '</p>' +
      '</div>'
    );
  }

  window.LinModuleCharts = {
    specFor: specFor,
    barChartSvg: barChartSvg,
    chartHtmlFor: chartHtmlFor,
    // The method_class set this module can chart. Callers may pre-filter with it.
    charted: {
      Sensitivity_Analysis: true, Tornado_Diagram: true, Multi_Objective_Optimization: true,
      WhatIf_Scenario_Matrix: true, Decision_Sensitivity_Matrix: true,
      Minimax_Regret_Decision_Rule: true, Regret_Minimization: true,
      Maximum_Entropy: true
    }
  };
})();
