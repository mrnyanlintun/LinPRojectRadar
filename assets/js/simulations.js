/* ============================================================
   lin-project-radar — simulations.js
   ------------------------------------------------------------
   Fourteen client-side simulation models that run in the browser
   from a project's extracted signalInputs — zero tokens, zero backend.

     04  PERT — Stochastic Network Criticality Index
     05  LOB  — Line of Balance Production Velocity
     06  CCPM — Buffer Health (fever chart logic)
     07  RCF  — Reference Class Forecasting cost prior
     08  DSM  — Design Structure Matrix rework propagation
     11  DST  — Dempster-Shafer Evidence Combination
     12  Rough Sets — lower/upper approximation classification
     13  Neutrosophic — Truth / Indeterminacy / Falsity logic
     14  Interval Fuzzy — interval-valued fuzzy membership
     15  Z-numbers — reliability-weighted evidence (Zadeh 2011)
     16  PLTS — Probabilistic Linguistic Term Sets (Pang 2016)
     17  Plithogenic Sets — contradiction-degree weighting (Smarandache 2018)
     18  BRB  — Belief Rule Base, weighted IF-THEN rules (Yang 2006)
     19  Quantum Probability — amplitude interference (Busemeyer 2012)

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

    // An interval-valued membership is the [min, max] of the membership
    // function across the input interval. Some membership functions decrease
    // in CPI (Red) and some are non-monotonic (Amber), so evaluating the two
    // endpoints and ordering them keeps every interval ascending.
    function membershipInterval(fn, lo, hi) {
      var a = fn(lo), b = fn(hi);
      return [Math.min(a, b), Math.max(a, b)];
    }

    var intervals = [];
    var cpi = existingSignals.evm ? existingSignals.evm.cpi : null;
    if (cpi) {
      var cpiLow = cpi - EV_UNCERTAINTY - AC_UNCERTAINTY;
      var cpiHigh = cpi + EV_UNCERTAINTY + AC_UNCERTAINTY;
      intervals.push({
        source: "CPI", value: cpi, range: [cpiLow, cpiHigh],
        green: membershipInterval(membershipGreen, cpiLow, cpiHigh),
        amber: membershipInterval(membershipAmber, cpiLow, cpiHigh),
        red:   membershipInterval(membershipRed,   cpiLow, cpiHigh)
      });
    }

    var spi = existingSignals.evm ? existingSignals.evm.spi : null;
    if (spi) {
      var spiLow = spi - EV_UNCERTAINTY;
      var spiHigh = spi + EV_UNCERTAINTY;
      intervals.push({
        source: "SPI", value: spi, range: [spiLow, spiHigh],
        green: membershipInterval(membershipGreen, spiLow, spiHigh),
        amber: membershipInterval(membershipAmber, spiLow, spiHigh),
        red:   membershipInterval(membershipRed,   spiLow, spiHigh)
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
     Module 15 — Z-numbers (Zadeh, 2011)
     Each signal is a Z-number (Restriction, Reliability): a
     restriction (the classified state) paired with a reliability
     measure for the source. Higher-reliability sources carry
     proportionally more weight in the aggregate.
     =========================================================== */
  function runZNumbers(existingSignals) {
    var signals = [];

    var cpi = existingSignals.evm ? existingSignals.evm.cpi : null;
    var spi = existingSignals.evm ? existingSignals.evm.spi : null;
    if (cpi && spi) {
      var evmMin = Math.min(cpi, spi);
      var restriction = evmMin >= 0.95 ? "Green" : evmMin >= 0.90 ? "Amber" : "Red";
      var reliability = 0.85; // pay application = high reliability
      signals.push({ source: "EVM", restriction: restriction, reliability: reliability });
    }

    var cusum = existingSignals.cusum;
    if (cusum) {
      var restriction2 = cusum.breached ? "Red" : "Green";
      signals.push({ source: "CUSUM", restriction: restriction2, reliability: 0.90 });
    }

    var doc = existingSignals.doc;
    if (doc) {
      var score = doc.score || 0;
      var restriction3 = score >= 0.70 ? "Red" : score >= 0.30 ? "Amber" : "Green";
      signals.push({ source: "DocRisk", restriction: restriction3, reliability: 0.65 });
    }

    var mc = existingSignals.mc;
    if (mc) {
      var p80 = mc.p80DeltaPct || 0;
      var restriction4 = p80 > 10 ? "Red" : p80 > 5 ? "Amber" : "Green";
      signals.push({ source: "MonteCarlo", restriction: restriction4, reliability: 0.88 });
    }

    if (!signals.length) {
      return { method_class: "Z_Numbers", status_color: "Amber",
        weighted_red: 0, weighted_amber: 0, weighted_green: 0, avg_reliability: 0,
        signal_count: 0, evidence_metric: "Insufficient signal data" };
    }

    var totalRed   = signals.reduce(function (a, b) { return a + (b.restriction === "Red"   ? b.reliability : 0); }, 0);
    var totalAmber = signals.reduce(function (a, b) { return a + (b.restriction === "Amber" ? b.reliability : 0); }, 0);
    var totalGreen = signals.reduce(function (a, b) { return a + (b.restriction === "Green" ? b.reliability : 0); }, 0);
    var avgReliability = signals.reduce(function (a, b) { return a + b.reliability; }, 0) / signals.length;

    var statusColor = totalRed >= totalAmber && totalRed >= totalGreen ? "Red"
                    : totalAmber >= totalGreen ? "Amber" : "Green";

    return {
      method_class: "Z_Numbers",
      status_color: statusColor,
      weighted_red:   Math.round(totalRed   * 100) / 100,
      weighted_amber: Math.round(totalAmber * 100) / 100,
      weighted_green: Math.round(totalGreen * 100) / 100,
      avg_reliability: Math.round(avgReliability * 100) / 100,
      signal_count: signals.length,
      signals: signals,
      evidence_metric: "Reliability-weighted: Red " + (Math.round(totalRed * 100) / 100) +
        " · Amber " + (Math.round(totalAmber * 100) / 100) +
        " · Green " + (Math.round(totalGreen * 100) / 100) +
        " · Avg reliability " + Math.round(avgReliability * 100) + "%"
    };
  }

  /* ===========================================================
     Module 16 — Probabilistic Linguistic Term Sets (Pang, 2016)
     Each signal is expressed as a probability distribution over
     linguistic states {Green, Amber, Red} rather than a crisp label.
     Captures partial confidence within each source.
     =========================================================== */
  function runPLTS(existingSignals) {
    var plts = [];

    var cpi = existingSignals.evm ? existingSignals.evm.cpi : null;
    var spi = existingSignals.evm ? existingSignals.evm.spi : null;
    if (cpi && spi) {
      var evmMin = Math.min(cpi, spi);
      var pRed, pAmber, pGreen;
      if      (evmMin >= 0.97) { pGreen = 0.90; pAmber = 0.08; pRed = 0.02; }
      else if (evmMin >= 0.95) { pGreen = 0.70; pAmber = 0.25; pRed = 0.05; }
      else if (evmMin >= 0.92) { pGreen = 0.15; pAmber = 0.70; pRed = 0.15; }
      else if (evmMin >= 0.90) { pGreen = 0.05; pAmber = 0.65; pRed = 0.30; }
      else if (evmMin >= 0.87) { pGreen = 0.02; pAmber = 0.28; pRed = 0.70; }
      else                     { pGreen = 0.02; pAmber = 0.08; pRed = 0.90; }
      plts.push({ source: "EVM", Green: pGreen, Amber: pAmber, Red: pRed });
    }

    var cusum = existingSignals.cusum;
    if (cusum) {
      if (cusum.breached) plts.push({ source: "CUSUM", Green: 0.02, Amber: 0.13, Red: 0.85 });
      else                plts.push({ source: "CUSUM", Green: 0.80, Amber: 0.15, Red: 0.05 });
    }

    var doc = existingSignals.doc;
    if (doc) {
      var s = doc.score || 0;
      if      (s < 0.30) plts.push({ source: "DocRisk", Green: 0.85, Amber: 0.12, Red: 0.03 });
      else if (s < 0.70) plts.push({ source: "DocRisk", Green: 0.10, Amber: 0.70, Red: 0.20 });
      else               plts.push({ source: "DocRisk", Green: 0.03, Amber: 0.17, Red: 0.80 });
    }

    var mc = existingSignals.mc;
    if (mc) {
      var p80m = mc.p80DeltaPct || 0;
      if      (p80m <= 5)  plts.push({ source: "MC", Green: 0.80, Amber: 0.15, Red: 0.05 });
      else if (p80m <= 10) plts.push({ source: "MC", Green: 0.08, Amber: 0.67, Red: 0.25 });
      else                 plts.push({ source: "MC", Green: 0.03, Amber: 0.17, Red: 0.80 });
    }

    if (!plts.length) {
      return { method_class: "PLTS", status_color: "Amber",
        p_green: 33, p_amber: 34, p_red: 33, sources: [],
        evidence_metric: "Insufficient signal data" };
    }

    var n = plts.length;
    var aggGreen = plts.reduce(function (a, b) { return a + b.Green; }, 0) / n;
    var aggAmber = plts.reduce(function (a, b) { return a + b.Amber; }, 0) / n;
    var aggRed   = plts.reduce(function (a, b) { return a + b.Red;   }, 0) / n;

    var statusColor = aggRed >= aggAmber && aggRed >= aggGreen ? "Red"
                    : aggAmber >= aggGreen ? "Amber" : "Green";

    return {
      method_class: "PLTS",
      status_color: statusColor,
      p_green: Math.round(aggGreen * 100),
      p_amber: Math.round(aggAmber * 100),
      p_red:   Math.round(aggRed   * 100),
      sources: plts,
      evidence_metric: "P(Green)=" + Math.round(aggGreen * 100) + "% · " +
        "P(Amber)=" + Math.round(aggAmber * 100) + "% · " +
        "P(Red)="   + Math.round(aggRed   * 100) + "%"
    };
  }

  /* ===========================================================
     Module 17 — Plithogenic Sets (Smarandache, 2018)
     Each attribute value carries a contradiction degree against
     the dominant value. High average contradiction means the
     signals are genuinely opposed, not merely mixed.
     =========================================================== */
  function runPlithogenic(existingSignals) {
    var attributes = [];

    var cpi = existingSignals.evm ? existingSignals.evm.cpi : null;
    var spi = existingSignals.evm ? existingSignals.evm.spi : null;
    if (cpi && spi) {
      var evmMin = Math.min(cpi, spi);
      var state = evmMin >= 0.95 ? "Green" : evmMin >= 0.90 ? "Amber" : "Red";
      var membership = evmMin >= 0.95 ? 0.85 : evmMin >= 0.90 ? 0.70 : 0.80;
      var contradiction = state === "Red" ? 0.0 : state === "Green" ? 1.0 : 0.5;
      attributes.push({ name: "EVM", state: state, membership: membership, contradiction: contradiction });
    }

    var cusum = existingSignals.cusum;
    if (cusum) {
      var state2 = cusum.breached ? "Red" : "Green";
      var contradiction2 = state2 === "Red" ? 0.0 : 1.0;
      attributes.push({ name: "CUSUM", state: state2, membership: 0.88, contradiction: contradiction2 });
    }

    var doc = existingSignals.doc;
    if (doc) {
      var s = doc.score || 0;
      var state3 = s >= 0.70 ? "Red" : s >= 0.30 ? "Amber" : "Green";
      var contradiction3 = state3 === "Red" ? 0.0 : state3 === "Green" ? 1.0 : 0.5;
      attributes.push({ name: "DocRisk", state: state3, membership: 0.75, contradiction: contradiction3 });
    }

    var mc = existingSignals.mc;
    if (mc) {
      var p80p = mc.p80DeltaPct || 0;
      var state4 = p80p > 10 ? "Red" : p80p > 5 ? "Amber" : "Green";
      var contradiction4 = state4 === "Red" ? 0.0 : state4 === "Green" ? 1.0 : 0.5;
      attributes.push({ name: "MC", state: state4, membership: 0.82, contradiction: contradiction4 });
    }

    if (!attributes.length) {
      return { method_class: "Plithogenic_Sets", status_color: "Amber",
        red_score: 0, amber_score: 0, green_score: 0,
        avg_contradiction: 0, contradiction_level: "Low",
        attributes: [], evidence_metric: "Insufficient signal data" };
    }

    var redScore = 0, amberScore = 0, greenScore = 0;
    attributes.forEach(function (a) {
      var w = a.membership * (1 - a.contradiction * 0.5);
      if      (a.state === "Red")   redScore   += w;
      else if (a.state === "Amber") amberScore += w;
      else                          greenScore += w;
    });

    var avgContradiction = attributes.reduce(function (a, b) { return a + b.contradiction; }, 0) / attributes.length;
    var statusColor = redScore >= amberScore && redScore >= greenScore ? "Red"
                    : amberScore >= greenScore ? "Amber" : "Green";

    return {
      method_class: "Plithogenic_Sets",
      status_color: statusColor,
      red_score:   Math.round(redScore   * 100) / 100,
      amber_score: Math.round(amberScore * 100) / 100,
      green_score: Math.round(greenScore * 100) / 100,
      avg_contradiction: Math.round(avgContradiction * 100) / 100,
      contradiction_level: avgContradiction > 0.6 ? "High" : avgContradiction > 0.3 ? "Moderate" : "Low",
      attributes: attributes,
      evidence_metric: "Plithogenic scores — Red: " + (Math.round(redScore * 100) / 100) +
        " · Amber: " + (Math.round(amberScore * 100) / 100) +
        " · Green: " + (Math.round(greenScore * 100) / 100) +
        " · Contradiction: " + Math.round(avgContradiction * 100) + "%"
    };
  }

  /* ===========================================================
     Module 18 — Belief Rule Base (Yang, 2006; extended 2018-2023)
     Expert IF-THEN rules with belief-distribution consequents
     and rule weights. Multiple matching rules are combined by
     weight to produce the aggregate belief over states.
     =========================================================== */
  function runBRB(existingSignals) {
    var cpi = existingSignals.evm ? existingSignals.evm.cpi : null;
    var spi = existingSignals.evm ? existingSignals.evm.spi : null;
    var cusumBreached = existingSignals.cusum ? existingSignals.cusum.breached : false;
    var docScore = existingSignals.doc ? (existingSignals.doc.score || 0) : 0;
    var p80Delta = existingSignals.mc  ? (existingSignals.mc.p80DeltaPct || 0) : 0;

    var evmState = (!cpi || !spi) ? null
      : Math.min(cpi, spi) >= 0.95 ? "Green"
      : Math.min(cpi, spi) >= 0.90 ? "Amber" : "Red";
    var docState = docScore >= 0.70 ? "Red" : docScore >= 0.30 ? "Amber" : "Green";
    var mcState  = p80Delta > 10 ? "Red" : p80Delta > 5 ? "Amber" : "Green";

    var rules = [
      { id: "R1", desc: "EVM Red + CUSUM breach",                 condition: evmState === "Red"   && cusumBreached,
        belief: { Green: 0.02, Amber: 0.08, Red: 0.90 }, weight: 1.00 },
      { id: "R2", desc: "EVM Red, no breach",                     condition: evmState === "Red"   && !cusumBreached,
        belief: { Green: 0.05, Amber: 0.25, Red: 0.70 }, weight: 0.85 },
      { id: "R3", desc: "EVM Amber + CUSUM breach",               condition: evmState === "Amber" && cusumBreached,
        belief: { Green: 0.05, Amber: 0.30, Red: 0.65 }, weight: 0.90 },
      { id: "R4", desc: "EVM Amber, doc Red",                     condition: evmState === "Amber" && !cusumBreached && docState === "Red",
        belief: { Green: 0.08, Amber: 0.42, Red: 0.50 }, weight: 0.80 },
      { id: "R5", desc: "EVM Amber, doc not Red",                 condition: evmState === "Amber" && !cusumBreached && docState !== "Red",
        belief: { Green: 0.10, Amber: 0.70, Red: 0.20 }, weight: 0.75 },
      { id: "R6", desc: "EVM Green + CUSUM breach",               condition: evmState === "Green" && cusumBreached,
        belief: { Green: 0.15, Amber: 0.55, Red: 0.30 }, weight: 0.85 },
      { id: "R7", desc: "EVM Green, no breach, doc Green",        condition: evmState === "Green" && !cusumBreached && docState === "Green",
        belief: { Green: 0.85, Amber: 0.12, Red: 0.03 }, weight: 0.90 },
      { id: "R8", desc: "EVM Green, no breach, doc not Green",    condition: evmState === "Green" && !cusumBreached && docState !== "Green",
        belief: { Green: 0.50, Amber: 0.40, Red: 0.10 }, weight: 0.70 }
    ];

    var matched = rules.filter(function (r) { return r.condition; });
    if (!matched.length) matched = [{ id: "R0", desc: "fallback", belief: { Green: 0.33, Amber: 0.34, Red: 0.33 }, weight: 0.50 }];

    var totalWeight = matched.reduce(function (a, b) { return a + b.weight; }, 0);
    var aggGreen = matched.reduce(function (a, b) { return a + b.belief.Green * b.weight; }, 0) / totalWeight;
    var aggAmber = matched.reduce(function (a, b) { return a + b.belief.Amber * b.weight; }, 0) / totalWeight;
    var aggRed   = matched.reduce(function (a, b) { return a + b.belief.Red   * b.weight; }, 0) / totalWeight;

    var statusColor = aggRed >= aggAmber && aggRed >= aggGreen ? "Red"
                    : aggAmber >= aggGreen ? "Amber" : "Green";

    return {
      method_class: "Belief_Rule_Base",
      status_color: statusColor,
      belief_green: Math.round(aggGreen * 100),
      belief_amber: Math.round(aggAmber * 100),
      belief_red:   Math.round(aggRed   * 100),
      rules_matched: matched.length,
      matched_rules: matched.map(function (m) { return { id: m.id, desc: m.desc, weight: m.weight }; }),
      mc_state: mcState,
      evidence_metric: "BRB belief: Green " + Math.round(aggGreen * 100) + "% · " +
        "Amber " + Math.round(aggAmber * 100) + "% · Red " + Math.round(aggRed * 100) + "% · " +
        matched.length + " rule(s) activated"
    };
  }

  /* ===========================================================
     Module 19 — Quantum Probability (Busemeyer & Bruza, 2012)
     Signals modelled as amplitudes in a state vector. The
     interference term captures coherence (aligned signals) vs
     destructive cancellation (opposed signals).
     =========================================================== */
  function runQuantumProbability(existingSignals) {
    var cpi = existingSignals.evm ? existingSignals.evm.cpi : null;
    var spi = existingSignals.evm ? existingSignals.evm.spi : null;
    var cusumBreached = existingSignals.cusum ? existingSignals.cusum.breached : false;
    var docScore = existingSignals.doc ? (existingSignals.doc.score || 0) : 0;

    var evmMin = (cpi && spi) ? Math.min(cpi, spi) : 1.0;
    var pGreen_evm   = evmMin >= 0.95 ? 0.80 : evmMin >= 0.90 ? 0.10 : 0.05;
    var pRed_evm     = evmMin >= 0.95 ? 0.05 : evmMin >= 0.90 ? 0.20 : 0.80;
    var pGreen_cusum = cusumBreached ? 0.05 : 0.80;
    var pRed_cusum   = cusumBreached ? 0.85 : 0.05;
    var pGreen_doc   = docScore < 0.30 ? 0.85 : docScore < 0.70 ? 0.10 : 0.03;
    var pRed_doc     = docScore < 0.30 ? 0.03 : docScore < 0.70 ? 0.20 : 0.80;

    var alpha_green = Math.sqrt((pGreen_evm + pGreen_cusum + pGreen_doc) / 3);
    var gamma_red   = Math.sqrt((pRed_evm   + pRed_cusum   + pRed_doc)   / 3);

    // Phase angle from signal coherence — aligned reds give small theta
    // (constructive); opposed signals give theta near pi (destructive).
    var redCount   = [pRed_evm   > 0.5, pRed_cusum   > 0.5, pRed_doc   > 0.5].filter(Boolean).length;
    var greenCount = [pGreen_evm > 0.5, pGreen_cusum > 0.5, pGreen_doc > 0.5].filter(Boolean).length;
    var theta = (Math.abs(redCount - greenCount) / 3) * Math.PI;
    var interference = 2 * alpha_green * gamma_red * Math.cos(theta);

    var P_red_q   = Math.max(0, Math.min(1, gamma_red * gamma_red   + interference * 0.3));
    var P_green_q = Math.max(0, Math.min(1, alpha_green * alpha_green - interference * 0.3));
    var P_amber_q = Math.max(0, 1 - P_red_q - P_green_q);

    var interferenceType = Math.cos(theta) > 0.3 ? "Constructive"
      : Math.cos(theta) < -0.3 ? "Destructive" : "Neutral";

    var statusColor = P_red_q >= P_amber_q && P_red_q >= P_green_q ? "Red"
                    : P_amber_q >= P_green_q ? "Amber" : "Green";

    return {
      method_class: "Quantum_Probability",
      status_color: statusColor,
      p_green: Math.round(P_green_q * 100),
      p_amber: Math.round(P_amber_q * 100),
      p_red:   Math.round(P_red_q   * 100),
      interference_type: interferenceType,
      interference_magnitude: Math.round(Math.abs(interference) * 100) / 100,
      phase_angle_deg: Math.round(theta * 180 / Math.PI),
      alpha_green: Math.round(alpha_green * 100) / 100,
      gamma_red:   Math.round(gamma_red   * 100) / 100,
      evidence_metric: "Q-P(Green)=" + Math.round(P_green_q * 100) + "% · " +
        "Q-P(Amber)=" + Math.round(P_amber_q * 100) + "% · " +
        "Q-P(Red)="   + Math.round(P_red_q   * 100) + "% · " +
        interferenceType + " interference · Phase " + Math.round(theta * 180 / Math.PI) + "°"
    };
  }

  /* ===========================================================
     runAll — Modules 04-08 (signalInputs-based) + 12-19
     (existingSignals-based). DST (Module 11) runs separately in
     signals.js after the core signal package is assembled so it
     can access the assembled project.signals directly.
     =========================================================== */
  function runAll(input, existingSignals) {
    var si = (input && input.signalInputs) ? input.signalInputs : (input || {});
    var es = existingSignals || {};
    return [
      runPERT(si),                  // Module 04
      runLOB(si),                   // Module 05
      runCCPM(si),                  // Module 06
      runRCF(si),                   // Module 07
      runDSM(si),                   // Module 08
      runRoughSets(es),             // Module 12
      runNeutrosophic(es),          // Module 13
      runIntervalFuzzy(es),         // Module 14
      runZNumbers(es),              // Module 15
      runPLTS(es),                  // Module 16
      runPlithogenic(es),           // Module 17
      runBRB(es),                   // Module 18
      runQuantumProbability(es)     // Module 19
    ];
  }

  window.LinSimulations = {
    runAll,
    runPERT, runLOB, runCCPM, runRCF, runDSM,
    runDST, runRoughSets, runNeutrosophic, runIntervalFuzzy,
    runZNumbers, runPLTS, runPlithogenic, runBRB, runQuantumProbability,
    sampleTriangular
  };
})();
