/* ============================================================
   lin-project-radar — simulations.js
   ------------------------------------------------------------
   Six client-side simulation models that run in the browser from
   a project's extracted signalInputs — zero tokens, zero backend.

     04  PERT — Stochastic Network Criticality Index
     05  LOB  — Line of Balance Production Velocity
     06  CCPM — Buffer Health (fever chart logic)
     07  RCF  — Reference Class Forecasting cost prior
     08  DSM  — Design Structure Matrix rework propagation
     11  DST  — Dempster-Shafer Evidence Combination

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
    var p50 = pctile(totals, 0.50);
    var p80 = pctile(totals, 0.80);
    var crit = bCritical / N;
    var baseline = A[1] + Math.max(B[1], C[1]);
    var ratio = p80 / baseline;
    var color = ratio > 1.30 ? "Red" : ratio > 1.15 ? "Amber" : "Green";
    return {
      method_class: "PERT_Network_Criticality",
      status_color: color,
      p50_duration_days: round1(p50),
      p80_duration_days: round1(p80),
      baseline_days: round1(baseline),
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
      grading_rate: gradingRate,
      paving_rate: round2(pavingRate),
      initial_buffer_days: initialBufferDays,
      units: units,
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
      zone: color,
      amber_threshold: round1(amber),
      red_threshold: round1(red),
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
      vs_bac_pct: round1(overP80),
      p50_multiplier: round2(p50),
      p80_multiplier: round2(p80),
      multipliers: sorted.slice(),
      bac: bac,
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
      matrix: A,
      arch_impact: round2(cumulative[0]),
      structural_impact: round2(cumulative[1]),
      mep_impact: round2(cumulative[2]),
      evidence_metric: "Architectural change → ×" + round2(total) +
        " cumulative rework across Arch/Struct/MEP (4 propagation passes)"
    };
  }

  /* ===========================================================
     Module 11 — Dempster-Shafer Evidence Combination
     Combines signal evidence from the four primary classes into a
     unified belief distribution over {Green, Amber, Red, Unknown}.
     =========================================================== */
  function runDST(signalInputs, existingSignals) {
    var sources = [];

    var cpi = existingSignals.evm ? existingSignals.evm.cpi : null;
    var spi = existingSignals.evm ? existingSignals.evm.spi : null;
    if (cpi && spi) {
      var evmMin = Math.min(cpi, spi);
      if (evmMin >= 0.95) sources.push({ Green: 0.80, Amber: 0.10, Red: 0.05, Unknown: 0.05 });
      else if (evmMin >= 0.90) sources.push({ Green: 0.10, Amber: 0.70, Red: 0.15, Unknown: 0.05 });
      else sources.push({ Green: 0.05, Amber: 0.15, Red: 0.75, Unknown: 0.05 });
    } else {
      sources.push({ Green: 0.25, Amber: 0.25, Red: 0.25, Unknown: 0.25 });
    }

    var mc = existingSignals.mc;
    if (mc) {
      var p80delta = mc.p80DeltaPct || 0;
      if (p80delta <= 5) sources.push({ Green: 0.75, Amber: 0.15, Red: 0.05, Unknown: 0.05 });
      else if (p80delta <= 10) sources.push({ Green: 0.10, Amber: 0.65, Red: 0.20, Unknown: 0.05 });
      else sources.push({ Green: 0.05, Amber: 0.10, Red: 0.80, Unknown: 0.05 });
    } else {
      sources.push({ Green: 0.25, Amber: 0.25, Red: 0.25, Unknown: 0.25 });
    }

    var cusum = existingSignals.cusum;
    if (cusum) {
      if (!cusum.breached) sources.push({ Green: 0.75, Amber: 0.15, Red: 0.05, Unknown: 0.05 });
      else sources.push({ Green: 0.05, Amber: 0.15, Red: 0.75, Unknown: 0.05 });
    } else {
      sources.push({ Green: 0.25, Amber: 0.25, Red: 0.25, Unknown: 0.25 });
    }

    var docScore = existingSignals.doc ? existingSignals.doc.score : 0;
    if (docScore < 0.30) sources.push({ Green: 0.75, Amber: 0.15, Red: 0.05, Unknown: 0.05 });
    else if (docScore < 0.70) sources.push({ Green: 0.10, Amber: 0.70, Red: 0.15, Unknown: 0.05 });
    else sources.push({ Green: 0.05, Amber: 0.15, Red: 0.75, Unknown: 0.05 });

    function combine(m1, m2) {
      var states = ["Green", "Amber", "Red", "Unknown"];
      var combined = { Green: 0, Amber: 0, Red: 0, Unknown: 0 };
      var K = 0;
      states.forEach(function (s1) {
        states.forEach(function (s2) {
          var mass = m1[s1] * m2[s2];
          if (s1 === s2) combined[s1] += mass;
          else K += mass;
        });
      });
      var norm = 1 - K;
      if (norm <= 0) return { Green: 0.25, Amber: 0.25, Red: 0.25, Unknown: 0.25, conflict: 1 };
      states.forEach(function (s) { combined[s] = combined[s] / norm; });
      combined.conflict = K;
      return combined;
    }

    var result = sources[0];
    for (var i = 1; i < sources.length; i++) {
      result = combine(result, sources[i]);
    }

    var decisionStates = ["Green", "Amber", "Red"];
    var maxState = decisionStates.reduce(function (a, b) {
      return result[a] > result[b] ? a : b;
    });

    var conservativeState = existingSignals.decision ? existingSignals.decision.state : null;
    var agrees = conservativeState && maxState.toLowerCase() === conservativeState.toLowerCase();
    var conflictLevel = result.conflict > 0.3 ? "High" : result.conflict > 0.1 ? "Moderate" : "Low";
    var statusColor = maxState === "Red" ? "Red" : maxState === "Amber" ? "Amber" : "Green";

    return {
      method_class: "DST_Evidence_Combination",
      status_color: statusColor,
      belief_green: Math.round(result.Green * 100) / 100,
      belief_amber: Math.round(result.Amber * 100) / 100,
      belief_red: Math.round(result.Red * 100) / 100,
      belief_unknown: Math.round(result.Unknown * 100) / 100,
      conflict_mass: Math.round(result.conflict * 100) / 100,
      conflict_level: conflictLevel,
      agrees_with_conservative: agrees,
      conservative_state: conservativeState,
      evidence_metric: "Belief: Green " + Math.round(result.Green * 100) + "% · Amber " +
        Math.round(result.Amber * 100) + "% · Red " + Math.round(result.Red * 100) +
        "% · Conflict mass " + Math.round(result.conflict * 100) + "%"
    };
  }

  /* ===========================================================
     Module 12 — Rough Set Theory
     Classifies the project into definite, borderline, or
     indeterminate zones based on signal voting across states.
     Lower approximation: states all signals definitively support.
     Upper approximation: states any signal supports.
     Boundary = upper - lower = indeterminate zone.
     =========================================================== */
  function runRoughSets(existingSignals) {
    var states = ["Green", "Amber", "Red"];
    var signalClasses = [];

    var cpi = existingSignals.evm ? existingSignals.evm.cpi : null;
    var spi = existingSignals.evm ? existingSignals.evm.spi : null;
    if (cpi && spi) {
      var evmMin = Math.min(cpi, spi);
      if (evmMin >= 0.95) signalClasses.push("Green");
      else if (evmMin >= 0.90) signalClasses.push("Amber");
      else signalClasses.push("Red");
    }

    var mc = existingSignals.mc;
    if (mc) {
      var p80 = mc.p80DeltaPct || 0;
      if (p80 <= 5) signalClasses.push("Green");
      else if (p80 <= 10) signalClasses.push("Amber");
      else signalClasses.push("Red");
    }

    var cusum = existingSignals.cusum;
    if (cusum) {
      signalClasses.push(cusum.breached ? "Red" : "Green");
    }

    var doc = existingSignals.doc;
    if (doc) {
      var docScore = doc.score || 0;
      if (docScore < 0.30) signalClasses.push("Green");
      else if (docScore < 0.70) signalClasses.push("Amber");
      else signalClasses.push("Red");
    }

    var counts = { Green: 0, Amber: 0, Red: 0 };
    signalClasses.forEach(function (s) { counts[s]++; });
    var total = signalClasses.length || 1;

    var lower = [], upper = [];
    states.forEach(function (s) {
      if (counts[s] / total > 0.75) lower.push(s);
      if (counts[s] > 0) upper.push(s);
    });
    var boundary = upper.filter(function (s) { return lower.indexOf(s) === -1; });

    var classification, statusColor;
    if (lower.length === 1) {
      classification = "Definite " + lower[0];
      statusColor = lower[0];
    } else if (boundary.length > 0) {
      classification = "Borderline: " + boundary.join(" / ");
      statusColor = boundary.indexOf("Red") >= 0 ? "Red" : "Amber";
    } else {
      classification = "Indeterminate";
      statusColor = "Amber";
    }

    return {
      method_class: "Rough_Sets_Classification",
      status_color: statusColor,
      lower_approximation: lower,
      upper_approximation: upper,
      boundary_region: boundary,
      classification: classification,
      signal_votes: counts,
      total_signals: total,
      evidence_metric: classification + " (Green " + counts.Green + ", Amber " + counts.Amber +
        ", Red " + counts.Red + " of " + total + " signals)"
    };
  }

  /* ===========================================================
     Module 13 — Neutrosophic Logic
     Truth (T), Indeterminacy (I), Falsity (F) per signal source.
     T + I + F need not sum to 1 — genuine uncertainty is a
     separate dimension, not residual of T and F.
     =========================================================== */
  function runNeutrosophic(existingSignals) {
    var components = [];

    var cpi = existingSignals.evm ? existingSignals.evm.cpi : null;
    var spi = existingSignals.evm ? existingSignals.evm.spi : null;
    if (cpi && spi) {
      var evmMin = Math.min(cpi, spi);
      if (evmMin >= 0.95) components.push({ T: 0.85, I: 0.10, F: 0.05, source: "EVM", state: "Green" });
      else if (evmMin >= 0.90) components.push({ T: 0.70, I: 0.20, F: 0.10, source: "EVM", state: "Amber" });
      else components.push({ T: 0.75, I: 0.15, F: 0.10, source: "EVM", state: "Red" });
    }

    var mc = existingSignals.mc;
    if (mc) {
      var p80 = mc.p80DeltaPct || 0;
      if (p80 <= 5) components.push({ T: 0.80, I: 0.10, F: 0.10, source: "Forecast", state: "Green" });
      else if (p80 <= 10) components.push({ T: 0.65, I: 0.25, F: 0.10, source: "Forecast", state: "Amber" });
      else components.push({ T: 0.75, I: 0.15, F: 0.10, source: "Forecast", state: "Red" });
    }

    var cusum = existingSignals.cusum;
    if (cusum) {
      if (cusum.breached) components.push({ T: 0.90, I: 0.05, F: 0.05, source: "CUSUM", state: "Red" });
      else components.push({ T: 0.80, I: 0.10, F: 0.10, source: "CUSUM", state: "Green" });
    }

    var doc = existingSignals.doc;
    if (doc) {
      var score = doc.score || 0;
      if (score < 0.30) components.push({ T: 0.85, I: 0.10, F: 0.05, source: "DocRisk", state: "Green" });
      else if (score < 0.70) components.push({ T: 0.65, I: 0.25, F: 0.10, source: "DocRisk", state: "Amber" });
      else components.push({ T: 0.75, I: 0.15, F: 0.10, source: "DocRisk", state: "Red" });
    }

    if (!components.length) {
      return {
        method_class: "Neutrosophic_Logic", status_color: "Amber",
        T: 0, I: 1, F: 0, indeterminacy_level: "High",
        signal_components: [],
        evidence_metric: "Insufficient signal data"
      };
    }

    var T = components.reduce(function (a, b) { return 1 - (1 - a) * (1 - b.T); }, 0);
    var I = components.reduce(function (a, b) { return a * b.I; }, 1);
    var F = components.reduce(function (a, b) { return a * b.F; }, 1);
    var sum = T + I + F || 1;
    T = Math.round(T / sum * 100) / 100;
    I = Math.round(I / sum * 100) / 100;
    F = Math.round(F / sum * 100) / 100;

    var redCount   = components.filter(function (c) { return c.state === "Red";   }).length;
    var amberCount = components.filter(function (c) { return c.state === "Amber"; }).length;
    var statusColor = redCount >= 2 ? "Red" : amberCount >= 2 ? "Amber" : "Green";
    if (I > 0.30) statusColor = statusColor === "Green" ? "Amber" : statusColor;

    return {
      method_class: "Neutrosophic_Logic",
      status_color: statusColor,
      T: T, I: I, F: F,
      indeterminacy_level: I > 0.30 ? "High" : I > 0.15 ? "Moderate" : "Low",
      signal_components: components,
      evidence_metric: "T=" + T + " I=" + I + " F=" + F +
        " — Indeterminacy: " + (I > 0.30 ? "High" : I > 0.15 ? "Moderate" : "Low")
    };
  }

  /* ===========================================================
     Module 14 — Interval-valued Fuzzy Sets
     Membership is a range [lower, upper] reflecting measurement
     uncertainty in EVM inputs (SoV accuracy ±2%, pay-app ±1%).
     =========================================================== */
  function runIntervalFuzzy(existingSignals) {
    var EV_UNCERTAINTY  = 0.02;
    var AC_UNCERTAINTY  = 0.01;

    function membershipAmber(val) {
      if (val <= 0.85 || val >= 0.98) return 0;
      if (val <= 0.92) return (val - 0.85) / (0.92 - 0.85);
      return (0.98 - val) / (0.98 - 0.92);
    }
    function membershipRed(val) {
      if (val >= 0.92) return 0;
      if (val <= 0.85) return 1;
      return (0.92 - val) / (0.92 - 0.85);
    }
    function membershipGreen(val) {
      if (val <= 0.92) return 0;
      if (val >= 0.97) return 1;
      return (val - 0.92) / (0.97 - 0.92);
    }

    var intervals = [];
    var cpi = existingSignals.evm ? existingSignals.evm.cpi : null;
    if (cpi) {
      var cpiLow = cpi - EV_UNCERTAINTY - AC_UNCERTAINTY;
      var cpiHigh = cpi + EV_UNCERTAINTY + AC_UNCERTAINTY;
      intervals.push({
        source: "CPI", value: cpi, range: [cpiLow, cpiHigh],
        green: [membershipGreen(cpiLow), membershipGreen(cpiHigh)],
        amber: [membershipAmber(cpiLow), membershipAmber(cpiHigh)],
        red:   [membershipRed(cpiLow),   membershipRed(cpiHigh)]
      });
    }

    var spi = existingSignals.evm ? existingSignals.evm.spi : null;
    if (spi) {
      var spiLow = spi - EV_UNCERTAINTY;
      var spiHigh = spi + EV_UNCERTAINTY;
      intervals.push({
        source: "SPI", value: spi, range: [spiLow, spiHigh],
        green: [membershipGreen(spiLow), membershipGreen(spiHigh)],
        amber: [membershipAmber(spiLow), membershipAmber(spiHigh)],
        red:   [membershipRed(spiLow),   membershipRed(spiHigh)]
      });
    }

    if (!intervals.length) {
      return {
        method_class: "Interval_Fuzzy_Sets", status_color: "Amber",
        green_interval: [0, 0], amber_interval: [0, 0], red_interval: [0, 0],
        uncertainty_width: 0, uncertainty_level: "Low",
        evidence_metric: "Insufficient signal data"
      };
    }

    var aggGreen = [
      intervals.reduce(function (a, b) { return Math.max(a, b.green[0]); }, 0),
      intervals.reduce(function (a, b) { return Math.max(a, b.green[1]); }, 0)
    ];
    var aggAmber = [
      intervals.reduce(function (a, b) { return Math.max(a, b.amber[0]); }, 0),
      intervals.reduce(function (a, b) { return Math.max(a, b.amber[1]); }, 0)
    ];
    var aggRed = [
      intervals.reduce(function (a, b) { return Math.max(a, b.red[0]); }, 0),
      intervals.reduce(function (a, b) { return Math.max(a, b.red[1]); }, 0)
    ];

    var greenMid = (aggGreen[0] + aggGreen[1]) / 2;
    var amberMid = (aggAmber[0] + aggAmber[1]) / 2;
    var redMid   = (aggRed[0]   + aggRed[1])   / 2;
    var statusColor = redMid >= amberMid && redMid >= greenMid ? "Red"
                    : amberMid >= greenMid ? "Amber" : "Green";

    var uncertaintyWidth = Math.round(
      ((aggRed[1] - aggRed[0]) + (aggAmber[1] - aggAmber[0])) * 100) / 100;

    return {
      method_class: "Interval_Fuzzy_Sets",
      status_color: statusColor,
      green_interval: aggGreen,
      amber_interval: aggAmber,
      red_interval:   aggRed,
      uncertainty_width: uncertaintyWidth,
      uncertainty_level: uncertaintyWidth > 0.3 ? "High" : uncertaintyWidth > 0.15 ? "Moderate" : "Low",
      evidence_metric: "Green [" + aggGreen.map(function (v) { return Math.round(v * 100) / 100; }).join(", ") +
        "] Amber [" + aggAmber.map(function (v) { return Math.round(v * 100) / 100; }).join(", ") +
        "] Red [" + aggRed.map(function (v) { return Math.round(v * 100) / 100; }).join(", ") + "]"
    };
  }

  /* ===========================================================
     runAll — Modules 04-08 (signalInputs-based) + 12-14
     (existingSignals-based). DST (Module 11) runs separately in
     signals.js after the core signal package is assembled, so it
     can access project.signals directly and its result is appended
     to the signal_array outside this function.
     =========================================================== */
  function runAll(input, existingSignals) {
    var si = (input && input.signalInputs) ? input.signalInputs : (input || {});
    var es = existingSignals || {};
    return [
      runPERT(si),             // Module 04
      runLOB(si),              // Module 05
      runCCPM(si),             // Module 06
      runRCF(si),              // Module 07
      runDSM(si),              // Module 08
      runRoughSets(es),        // Module 12
      runNeutrosophic(es),     // Module 13
      runIntervalFuzzy(es)     // Module 14
    ];
  }

  window.LinSimulations = {
    runAll,
    runPERT, runLOB, runCCPM, runRCF, runDSM,
    runDST, runRoughSets, runNeutrosophic, runIntervalFuzzy,
    sampleTriangular
  };
})();
