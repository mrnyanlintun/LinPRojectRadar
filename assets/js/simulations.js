/* ============================================================
   lin-project-radar — simulations.js  (Sprint 0 items 6–10)
   ------------------------------------------------------------
   Five additional client-side simulation models that run in the
   browser from a project's extracted signalInputs — zero tokens,
   zero backend calls. Each returns a signal object that feeds the
   unified signal array (item 11) shown in the Five Signals panel.

     6  PERT — Stochastic Network Criticality Index
     7  LOB  — Line of Balance Production Velocity
     8  CCPM — Buffer Health (fever chart logic)
     9  RCF  — Reference Class Forecasting cost prior
    10  DSM  — Design Structure Matrix rework propagation

   These are DEMONSTRATION models (designed heuristics over the
   project's synthetic inputs), not calibrated/validated forecasts.
   ============================================================ */
(function () {
  "use strict";

  /* ---------- small numeric helpers ---------- */
  function num(v, dflt) { var n = Number(v); return Number.isFinite(n) ? n : dflt; }
  function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
  function round1(v) { return Math.round(v * 10) / 10; }
  function round2(v) { return Math.round(v * 100) / 100; }
  function pctile(sortedAsc, q) {
    if (!sortedAsc.length) return NaN;
    var i = clamp(Math.floor(q * (sortedAsc.length - 1)), 0, sortedAsc.length - 1);
    return sortedAsc[i];
  }
  function money(v) {
    return "$" + Math.round(v).toLocaleString();
  }
  // percent in 0–100 from a value that may be a fraction (0–1) or a percent
  function asPercent(v, dflt) {
    var n = num(v, null);
    if (n == null) return dflt;
    return n <= 1 ? n * 100 : n;
  }

  /* exact triangular distribution sampler (item 6 reference) */
  function sampleTriangular(a, m, b) {
    var F = (m - a) / (b - a);
    var U = Math.random();
    if (U < F) return a + Math.sqrt(U * (b - a) * (m - a));
    return b - Math.sqrt((1 - U) * (b - a) * (b - m));
  }

  /* ===========================================================
     Item 6 — PERT Stochastic Network Criticality Index
     3-activity network: A then (B ∥ C); finish = A + max(B, C).
     SPI widens the pessimistic bound of the work activities.
     =========================================================== */
  function runPERT(signalInputs) {
    var spi = num(signalInputs.spi, 1.0);
    var pess = 1 + Math.max(0, 1 - spi) * 0.8;   // lower SPI → fatter pessimistic tail
    var A = [8, 10, 14];
    var B = [12, 15, 22 * pess];
    var C = [10, 13, 18 * pess];
    var N = 2000, totals = new Array(N), bCritical = 0;
    for (var i = 0; i < N; i++) {
      var a = sampleTriangular(A[0], A[1], A[2]);
      var b = sampleTriangular(B[0], B[1], B[2]);
      var c = sampleTriangular(C[0], C[1], C[2]);
      totals[i] = a + Math.max(b, c);
      if (b >= c) bCritical++;
    }
    totals.sort(function (x, y) { return x - y; });
    var p80 = pctile(totals, 0.80);
    var crit = bCritical / N;
    var baseline = A[1] + Math.max(B[1], C[1]);
    var ratio = p80 / baseline;
    var color = ratio > 1.30 ? "Red" : ratio > 1.15 ? "Amber" : "Green";
    return {
      method_class: "PERT_Network_Criticality",
      status_color: color,
      p80_duration_days: round1(p80),
      path_criticality_index: round2(crit),
      evidence_metric: "P80 path " + round1(p80) + "d vs baseline " + round1(baseline) +
        "d; structural path critical " + Math.round(crit * 100) + "% of runs"
    };
  }

  /* ===========================================================
     Item 7 — Line of Balance production velocity
     Leader (grading) vs follower (paving). SPI slows paving, so the
     crew-to-crew schedule buffer erodes unit by unit.
     =========================================================== */
  function runLOB(signalInputs) {
    var spi = num(signalInputs.spi, 1.0);
    var units = 20;
    var gradingRate = 2.0;                          // units/day (leader)
    var pavingRate = 1.8 * clamp(spi, 0.3, 1.2);    // follower slows with SPI
    var initialBufferDays = 5.0;
    var lagPerUnit = Math.max(0, (1 / pavingRate) - (1 / gradingRate));
    var minBuffer = initialBufferDays, critUnit = units, flagged = false;
    for (var u = 1; u <= units; u++) {
      var buffer = initialBufferDays - u * lagPerUnit;
      if (buffer < minBuffer) minBuffer = buffer;
      if (!flagged && buffer <= 1.5) { critUnit = u; flagged = true; }
    }
    var color = minBuffer <= 1.5 ? "Red" : minBuffer <= 3.0 ? "Amber" : "Green";
    return {
      method_class: "Line_of_Balance_Velocity",
      status_color: color,
      minimum_buffer_days: round1(minBuffer),
      critical_unit_index: critUnit,
      evidence_metric: "Min crew buffer " + round1(minBuffer) + "d (paving " + round2(pavingRate) +
        " vs grading " + gradingRate + " units/day)"
    };
  }

  /* ===========================================================
     Item 8 — CCPM buffer-health fever chart logic
     Buffer consumption vs chain completion.
     =========================================================== */
  function runCCPM(signalInputs) {
    var pctChainComplete = asPercent(
      signalInputs.actualPctComplete != null ? signalInputs.actualPctComplete : signalInputs.plannedPctComplete,
      0
    );
    var spi = num(signalInputs.spi, 1.0);
    var pctBufferConsumed = clamp((1 - spi) * 100 * 1.5, 0, 100); // SPI degradation burns buffer
    var amber = pctChainComplete;
    var red = pctChainComplete + (100 - pctChainComplete) / 3;
    var color = pctBufferConsumed >= red ? "Red" : pctBufferConsumed >= amber ? "Amber" : "Green";
    return {
      method_class: "CCPM_Buffer_Health",
      status_color: color,
      pct_chain_complete: round1(pctChainComplete),
      pct_buffer_consumed: round1(pctBufferConsumed),
      evidence_metric: "Buffer " + round1(pctBufferConsumed) + "% consumed at " +
        round1(pctChainComplete) + "% chain complete"
    };
  }

  /* ===========================================================
     Item 9 — Reference Class Forecasting cost prior
     Empirical airport-infrastructure overrun multipliers.
     =========================================================== */
  function runRCF(signalInputs) {
    var bac = num(signalInputs.bac, 0);
    var mult = [1.00, 1.04, 1.10, 1.14, 1.15, 1.26, 1.38, 1.45, 1.52];
    var sorted = mult.slice().sort(function (a, b) { return a - b; });
    var p50 = pctile(sorted, 0.50);
    var p80 = pctile(sorted, 0.80);
    var p50adj = bac * p50, p80adj = bac * p80;
    var overP80 = (p80 - 1) * 100;
    var color = overP80 <= 10 ? "Green" : overP80 <= 25 ? "Amber" : "Red";
    return {
      method_class: "Reference_Class_Forecasting",
      status_color: color,
      rcf_p50_adjusted: Math.round(p50adj),
      rcf_p80_adjusted: Math.round(p80adj),
      debiasing_factor: round2(p80),
      evidence_metric: bac > 0
        ? "P80 cost prior " + money(p80adj) + " (+" + round1(overP80) + "% vs BAC); debias ×" + round2(p80)
        : "Debias ×" + round2(p80) + " (+" + round1(overP80) + "% P80 prior; BAC not yet extracted)"
    };
  }

  /* ===========================================================
     Item 10 — DSM rework propagation
     3×3 [Arch, Structural, MEP]; architectural change vector,
     4 propagation iterations, cumulative rework burden.
     =========================================================== */
  function runDSM(signalInputs) {
    // A[i][j] = fraction of a change in discipline j that propagates rework to i
    var A = [
      [0.0, 0.30, 0.10],   // Arch       ← Structural, MEP
      [0.50, 0.0, 0.20],   // Structural ← Arch, MEP
      [0.40, 0.30, 0.0]    // MEP        ← Arch, Structural
    ];
    var wave = [1.0, 0.0, 0.0];          // initial architectural scope change
    var cumulative = wave.slice();
    for (var it = 0; it < 4; it++) {
      var next = [0, 0, 0];
      for (var i = 0; i < 3; i++) for (var j = 0; j < 3; j++) next[i] += A[i][j] * wave[j];
      for (var k = 0; k < 3; k++) cumulative[k] += next[k];
      wave = next;
    }
    var total = cumulative[0] + cumulative[1] + cumulative[2];
    var color = total > 2.5 ? "Amber" : "Green";
    return {
      method_class: "DSM_Rework_Propagation",
      status_color: color,
      rework_multiplier: round2(total),
      evidence_metric: "Architectural change → ×" + round2(total) +
        " cumulative rework across Arch/Struct/MEP (4 propagation passes)"
    };
  }

  /* ===========================================================
     runAll — accepts a project OR a signalInputs object and
     returns the array of the five simulation signal objects.
     =========================================================== */
  function runAll(input) {
    var si = (input && input.signalInputs) ? input.signalInputs : (input || {});
    return [runPERT(si), runLOB(si), runCCPM(si), runRCF(si), runDSM(si)];
  }

  window.LinSimulations = {
    runAll,
    runPERT, runLOB, runCCPM, runRCF, runDSM,
    sampleTriangular
  };
})();
