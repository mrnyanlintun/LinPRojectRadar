/* ============================================================
   lin-project-radar — simulations.js
   ------------------------------------------------------------
   Fourteen client-side simulation models that run in the browser
   from a project's extracted signalInputs — zero tokens, zero backend.

   Display module numbering (final / 2026 reorder):
     04  PERT — Stochastic Network Criticality Index
     05  LOB  — Line of Balance Production Velocity
     06  CCPM — Buffer Health (fever chart logic)
     07  RCF  — Reference Class Forecasting cost prior
     08  DSM  — Design Structure Matrix rework propagation
     10  DST  — Dempster-Shafer Evidence Combination
     11  Rough Sets — lower/upper approximation classification
     12  Neutrosophic — Truth / Indeterminacy / Falsity logic
     13  Interval Fuzzy — interval-valued fuzzy membership
     14  Z-numbers — reliability-weighted evidence (Zadeh 2011)
     15  PLTS — Probabilistic Linguistic Term Sets (Pang 2016)
     16  Plithogenic Sets — contradiction-degree weighting (Smarandache 2018)
     17  BRB  — Belief Rule Base, weighted IF-THEN rules (Yang 2006)
     18  Quantum Probability — amplitude interference (Busemeyer 2012)

   Module 09 (Conservative Dominance / Signal Synthesis) and Module 19 (ABM
   Governance) run in the main signal pipeline — not here — because they need
   the full assembled signal package, not raw signalInputs.

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
     Module 10 — Dempster-Shafer Evidence Combination
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
     Module 11 — Rough Set Theory
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
     Module 12 — Neutrosophic Logic
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
     Module 13 — Interval-valued Fuzzy Sets
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
     Module 14 — Z-numbers (Zadeh, 2011)
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
     Module 15 — Probabilistic Linguistic Term Sets (Pang, 2016)
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
     Module 16 — Plithogenic Sets (Smarandache, 2018)
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
     Module 17 — Belief Rule Base (Yang, 2006; extended 2018-2023)
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
     Module 18 — Quantum Probability (Busemeyer & Bruza, 2012)
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
     Stage-2 full-108 module calculations (108 = 89 baseline + Cat
     10/11/12 from the v3 module-set bump in signals.js).
     ------------------------------------------------------------
     These run from the project's signalInputs (si) directly —
     cpi / spi / docRiskScore plus any extracted document data.
     Every function checks its required inputs first and returns a
     standard insufficient-data stub when any are missing, so the
     ensemble / spider only ever count modules that truly computed.
     =========================================================== */

  function checkInputs(si, required) {
    for (var i = 0; i < required.length; i++) {
      if (si[required[i]] === null || si[required[i]] === undefined) return false;
    }
    return true;
  }

  function insufficientData(methodClass) {
    return {
      method_class: methodClass,
      status_color: null,
      insufficient_data: true,
      evidence_metric: 'Insufficient data — upload required documents'
    };
  }

  /* ---------- Cat 1 — EVM extensions ---------- */

  function runBayesianEAC(si) {
    if (!checkInputs(si, ['bac','ev','ac','cpi'])) return insufficientData('Bayesian_EAC');
    var priorMean = si.bac;
    var priorVariance = Math.pow(si.bac * 0.15, 2);
    var likelihoodMean = si.bac / si.cpi;
    var likelihoodVariance = Math.pow(si.bac * (1 - si.cpi) / si.cpi, 2);
    var posteriorMean = (priorMean / priorVariance + likelihoodMean / likelihoodVariance) /
                       (1 / priorVariance + 1 / likelihoodVariance);
    var deltaPct = ((posteriorMean - si.bac) / si.bac) * 100;
    var status = deltaPct <= 5 ? 'Green' : deltaPct <= 10 ? 'Yellow' : deltaPct <= 20 ? 'Amber' : 'Red';
    return {
      method_class: 'Bayesian_EAC', status_color: status,
      posterior_eac: Math.round(posteriorMean),
      delta_pct: Math.round(deltaPct * 10) / 10,
      evidence_metric: 'Bayesian EAC: $' + Math.round(posteriorMean).toLocaleString() +
        ' (' + (deltaPct > 0 ? '+' : '') + Math.round(deltaPct * 10) / 10 + '% BAC)'
    };
  }

  function runKalmanFilter(si) {
    var history = si.spiHistory || (si.spi ? [si.spi] : null);
    if (!history || history.length < 2) return insufficientData('Kalman_Filter');
    var Q = 0.01, R = 0.1;
    var x = history[0], P = 1.0;
    for (var i = 1; i < history.length; i++) {
      P = P + Q;
      var K = P / (P + R);
      x = x + K * (history[i] - x);
      P = (1 - K) * P;
    }
    var smoothedSPI = Math.round(x * 1000) / 1000;
    var trend = history.length >= 3 ?
      (history[history.length-1] - history[history.length-3]) / 2 : 0;
    var status = smoothedSPI >= 0.95 ? 'Green' :
                 smoothedSPI >= 0.92 ? 'Yellow' :
                 smoothedSPI >= 0.88 ? 'Amber' : 'Red';
    return {
      method_class: 'Kalman_Filter', status_color: status,
      smoothed_spi: smoothedSPI, trend: Math.round(trend * 1000) / 1000,
      evidence_metric: 'Kalman SPI: ' + smoothedSPI +
        ' (trend: ' + (trend >= 0 ? '+' : '') + Math.round(trend * 1000) / 1000 + '/period)'
    };
  }

  function runARIMAForecast(si) {
    var history = si.cpiHistory || (si.cpi ? [si.cpi] : null);
    if (!history || history.length < 3) return insufficientData('ARIMA_Forecast');
    var diffs = [];
    for (var i = 1; i < history.length; i++) diffs.push(history[i] - history[i-1]);
    var phi = 0;
    if (diffs.length >= 2) {
      var num = 0, den = 0;
      for (var j = 1; j < diffs.length; j++) {
        num += diffs[j] * diffs[j-1];
        den += diffs[j-1] * diffs[j-1];
      }
      phi = den !== 0 ? Math.max(-0.9, Math.min(0.9, num / den)) : 0;
    }
    var lastDiff = diffs[diffs.length - 1] || 0;
    var forecastDiff = phi * lastDiff;
    var forecastCPI = history[history.length - 1] + forecastDiff;
    forecastCPI = Math.round(forecastCPI * 1000) / 1000;
    var status = forecastCPI >= 0.95 ? 'Green' :
                 forecastCPI >= 0.92 ? 'Yellow' :
                 forecastCPI >= 0.88 ? 'Amber' : 'Red';
    return {
      method_class: 'ARIMA_Forecast', status_color: status,
      forecast_cpi: forecastCPI, phi: Math.round(phi * 100) / 100,
      evidence_metric: 'ARIMA CPI forecast: ' + forecastCPI +
        ' (' + (forecastDiff >= 0 ? 'recovering' : 'declining') + ')'
    };
  }

  function runEarnedSchedule(si) {
    if (!checkInputs(si, ['ev','pv','bac','actualPctComplete','plannedPctComplete']))
      return insufficientData('Earned_Schedule');
    var actualPct = si.actualPctComplete / 100;
    var plannedPct = si.plannedPctComplete / 100;
    var SPI_t = plannedPct > 0 ? actualPct / plannedPct : null;
    if (!SPI_t) return insufficientData('Earned_Schedule');
    var baselineDays = si.baselineStart && si.baselineEnd ?
      (new Date(si.baselineEnd) - new Date(si.baselineStart)) / 86400000 : null;
    var delayDays = baselineDays ? Math.round(baselineDays * (1 - SPI_t)) : null;
    var status = SPI_t >= 0.95 ? 'Green' :
                 SPI_t >= 0.92 ? 'Yellow' :
                 SPI_t >= 0.88 ? 'Amber' : 'Red';
    return {
      method_class: 'Earned_Schedule', status_color: status,
      spi_time: Math.round(SPI_t * 1000) / 1000,
      delay_days: delayDays,
      evidence_metric: 'ES SPI(t): ' + Math.round(SPI_t * 1000) / 1000 +
        (delayDays ? ' (' + delayDays + ' day delay implied)' : '')
    };
  }

  function runTCPI(si) {
    if (!checkInputs(si, ['bac','ev','ac'])) return insufficientData('TCPI');
    var remainingWork = si.bac - si.ev;
    var remainingBudget = si.bac - si.ac;
    if (remainingBudget <= 0) return {
      method_class: 'TCPI', status_color: 'Red',
      tcpi: null, evidence_metric: 'Budget exhausted — no remaining funds'
    };
    var tcpi = remainingWork / remainingBudget;
    tcpi = Math.round(tcpi * 1000) / 1000;
    var status = tcpi <= 1.05 ? 'Green' :
                 tcpi <= 1.10 ? 'Yellow' :
                 tcpi <= 1.20 ? 'Amber' : 'Red';
    return {
      method_class: 'TCPI', status_color: status, tcpi: tcpi,
      evidence_metric: 'TCPI: ' + tcpi +
        ' — ' + (tcpi <= 1.05 ? 'achievable' :
                 tcpi <= 1.10 ? 'challenging' :
                 tcpi <= 1.20 ? 'very difficult' : 'unrealistic') +
        ' to finish within budget'
    };
  }

  function runVAC(si) {
    if (!checkInputs(si, ['bac','cpi'])) return insufficientData('VAC');
    var eac = si.bac / si.cpi;
    var vac = si.bac - eac;
    var vacPct = (vac / si.bac) * 100;
    var status = vacPct >= -5 ? 'Green' :
                 vacPct >= -10 ? 'Yellow' :
                 vacPct >= -20 ? 'Amber' : 'Red';
    return {
      method_class: 'VAC', status_color: status,
      vac: Math.round(vac), vac_pct: Math.round(vacPct * 10) / 10,
      evidence_metric: 'VAC: $' + Math.round(Math.abs(vac)).toLocaleString() +
        ' ' + (vac < 0 ? 'over' : 'under') + ' budget (' +
        Math.round(Math.abs(vacPct) * 10) / 10 + '%)'
    };
  }

  function runBudgetExecutionRate(si) {
    if (!checkInputs(si, ['ac','bac','actualPctComplete'])) return insufficientData('Budget_Execution_Rate');
    var expectedSpend = si.bac * (si.actualPctComplete / 100);
    var executionRate = expectedSpend > 0 ? si.ac / expectedSpend : null;
    if (!executionRate) return insufficientData('Budget_Execution_Rate');
    executionRate = Math.round(executionRate * 1000) / 1000;
    var status = executionRate <= 1.05 ? 'Green' :
                 executionRate <= 1.10 ? 'Yellow' :
                 executionRate <= 1.20 ? 'Amber' : 'Red';
    return {
      method_class: 'Budget_Execution_Rate', status_color: status,
      execution_rate: executionRate,
      evidence_metric: 'Budget execution rate: ' + executionRate +
        ' (spending ' + (executionRate > 1 ? Math.round((executionRate-1)*100) + '% faster' : 'on plan') + ')'
    };
  }

  function runRegressionToMean(si) {
    var history = si.cpiHistory || (si.cpi ? [si.cpi] : null);
    if (!history || history.length < 2) return insufficientData('Regression_To_Mean');
    var mean = history.reduce(function(a,b){return a+b;},0) / history.length;
    var current = history[history.length - 1];
    var deviation = current - mean;
    var regressedCPI = mean + deviation * 0.5;
    regressedCPI = Math.round(regressedCPI * 1000) / 1000;
    var status = regressedCPI >= 0.95 ? 'Green' :
                 regressedCPI >= 0.92 ? 'Yellow' :
                 regressedCPI >= 0.88 ? 'Amber' : 'Red';
    return {
      method_class: 'Regression_To_Mean', status_color: status,
      regressed_cpi: regressedCPI, historical_mean: Math.round(mean * 1000) / 1000,
      evidence_metric: 'Regressed CPI: ' + regressedCPI +
        ' (mean: ' + Math.round(mean * 1000) / 1000 + ')'
    };
  }

  function runICERatio(si) {
    if (!checkInputs(si, ['bac','cpi','ev','ac'])) return insufficientData('ICE_Ratio');
    var eacCPI = si.bac / si.cpi;
    var eacParametric = si.ac + (si.bac - si.ev);
    var iceRatio = eacParametric > 0 ? eacCPI / eacParametric : null;
    if (!iceRatio) return insufficientData('ICE_Ratio');
    iceRatio = Math.round(iceRatio * 1000) / 1000;
    var status = Math.abs(iceRatio - 1) <= 0.05 ? 'Green' :
                 Math.abs(iceRatio - 1) <= 0.10 ? 'Yellow' :
                 Math.abs(iceRatio - 1) <= 0.20 ? 'Amber' : 'Red';
    return {
      method_class: 'ICE_Ratio', status_color: status, ice_ratio: iceRatio,
      eac_cpi: Math.round(eacCPI), eac_parametric: Math.round(eacParametric),
      evidence_metric: 'ICE ratio: ' + iceRatio +
        ' (CPI-EAC $' + Math.round(eacCPI).toLocaleString() +
        ' vs parametric $' + Math.round(eacParametric).toLocaleString() + ')'
    };
  }

  /* ---------- Cat 2 — Schedule extensions ---------- */

  function runScheduleCompression(si) {
    if (!checkInputs(si, ['baselineEnd','baselineStart','actualPctComplete']))
      return insufficientData('Schedule_Compression');
    var totalDays = (new Date(si.baselineEnd) - new Date(si.baselineStart)) / 86400000;
    if (totalDays <= 0) return insufficientData('Schedule_Compression');
    var remainingPct = (100 - si.actualPctComplete) / 100;
    var remainingDays = totalDays * remainingPct;
    var spi = si.spi || 1.0;
    var requiredDays = remainingDays;
    var availableDays = remainingDays * spi;
    var compressionRatio = requiredDays > 0 ? requiredDays / Math.max(availableDays, 1) : 1;
    compressionRatio = Math.round(compressionRatio * 100) / 100;
    var status = compressionRatio <= 1.05 ? 'Green' :
                 compressionRatio <= 1.15 ? 'Yellow' :
                 compressionRatio <= 1.30 ? 'Amber' : 'Red';
    return {
      method_class: 'Schedule_Compression', status_color: status,
      compression_ratio: compressionRatio, remaining_days: Math.round(remainingDays),
      evidence_metric: 'Schedule compression: ' + compressionRatio + 'x — ' +
        Math.round(remainingDays) + ' days of work remaining'
    };
  }

  function runFloatConsumption(si) {
    if (!checkInputs(si, ['totalFloat','consumedFloat'])) return insufficientData('Float_Consumption');
    var floatRemaining = si.totalFloat - si.consumedFloat;
    var consumptionRate = si.totalFloat > 0 ? si.consumedFloat / si.totalFloat : null;
    if (consumptionRate === null) return insufficientData('Float_Consumption');
    var pctComplete = si.actualPctComplete || 50;
    var expectedConsumption = pctComplete / 100;
    var floatStress = consumptionRate / Math.max(expectedConsumption, 0.01);
    floatStress = Math.round(floatStress * 100) / 100;
    var status = floatStress <= 1.0 ? 'Green' :
                 floatStress <= 1.3 ? 'Yellow' :
                 floatStress <= 1.6 ? 'Amber' : 'Red';
    return {
      method_class: 'Float_Consumption', status_color: status,
      float_remaining_days: Math.round(floatRemaining),
      consumption_rate: Math.round(consumptionRate * 100),
      float_stress: floatStress,
      evidence_metric: 'Float: ' + Math.round(floatRemaining) + ' days remaining — ' +
        Math.round(consumptionRate * 100) + '% consumed'
    };
  }

  function runSCurveDeviation(si) {
    if (!checkInputs(si, ['actualPctComplete','plannedPctComplete','ev','pv']))
      return insufficientData('SCurve_Deviation');
    var pctDeviation = si.actualPctComplete - si.plannedPctComplete;
    var valueDeviation = si.pv > 0 ? ((si.ev - si.pv) / si.pv) * 100 : null;
    if (valueDeviation === null) return insufficientData('SCurve_Deviation');
    var combinedDeviation = (pctDeviation + valueDeviation) / 2;
    var status = combinedDeviation >= -2 ? 'Green' :
                 combinedDeviation >= -5 ? 'Yellow' :
                 combinedDeviation >= -10 ? 'Amber' : 'Red';
    return {
      method_class: 'SCurve_Deviation', status_color: status,
      pct_deviation: Math.round(pctDeviation * 10) / 10,
      value_deviation: Math.round(valueDeviation * 10) / 10,
      evidence_metric: 'S-curve: ' + Math.round(pctDeviation * 10) / 10 +
        '% behind planned progress, ' + Math.round(valueDeviation * 10) / 10 +
        '% EV vs PV deviation'
    };
  }

  function runScheduleRiskAnalysis(si) {
    if (!checkInputs(si, ['spi','baselineEnd','baselineStart','actualPctComplete']))
      return insufficientData('Schedule_Risk_Analysis');
    var totalDays = (new Date(si.baselineEnd) - new Date(si.baselineStart)) / 86400000;
    if (totalDays <= 0) return insufficientData('Schedule_Risk_Analysis');
    var remainingPct = (100 - si.actualPctComplete) / 100;
    var remainingDays = totalDays * remainingPct;
    var p50Days = remainingDays / si.spi;
    var uncertainty = Math.max(0.05, 1 - si.spi) * 0.5;
    var p80Days = p50Days * (1 + uncertainty * 1.28);
    var delayDays = Math.round(p80Days - remainingDays);
    var status = delayDays <= 0 ? 'Green' :
                 delayDays <= 14 ? 'Yellow' :
                 delayDays <= 30 ? 'Amber' : 'Red';
    return {
      method_class: 'Schedule_Risk_Analysis', status_color: status,
      p50_delay_days: Math.round(p50Days - remainingDays),
      p80_delay_days: delayDays,
      evidence_metric: 'SRA P80 delay: ' + delayDays + ' days beyond baseline'
    };
  }

  function runCriticalPathIndex(si) {
    if (!checkInputs(si, ['spi','plannedPctComplete','actualPctComplete']))
      return insufficientData('Critical_Path_Index');
    var progressRatio = si.plannedPctComplete > 0 ?
      si.actualPctComplete / si.plannedPctComplete : si.spi;
    var cpi_schedule = si.spi;
    var criticalPathIndex = (progressRatio + cpi_schedule) / 2;
    criticalPathIndex = Math.round(criticalPathIndex * 1000) / 1000;
    var status = criticalPathIndex >= 0.95 ? 'Green' :
                 criticalPathIndex >= 0.92 ? 'Yellow' :
                 criticalPathIndex >= 0.88 ? 'Amber' : 'Red';
    return {
      method_class: 'Critical_Path_Index', status_color: status,
      critical_path_index: criticalPathIndex,
      evidence_metric: 'Critical Path Index: ' + criticalPathIndex
    };
  }

  /* ---------- Cat 3 — Cost extensions ---------- */

  function runContingencyBurnRate(si) {
    if (!checkInputs(si, ['originalContingency','remainingContingency','actualPctComplete']))
      return insufficientData('Contingency_Burn_Rate');
    var burned = si.originalContingency - si.remainingContingency;
    var burnRate = si.originalContingency > 0 ? burned / si.originalContingency : null;
    if (burnRate === null) return insufficientData('Contingency_Burn_Rate');
    var expectedBurn = si.actualPctComplete / 100;
    var burnStress = expectedBurn > 0 ? burnRate / expectedBurn : burnRate;
    burnStress = Math.round(burnStress * 100) / 100;
    var status = burnStress <= 1.0 ? 'Green' :
                 burnStress <= 1.3 ? 'Yellow' :
                 burnStress <= 1.6 ? 'Amber' : 'Red';
    var isDerived = si.sources && (
      (si.sources['originalContingency'] && si.sources['originalContingency'].docType === 'derived') ||
      (si.sources['remainingContingency'] && si.sources['remainingContingency'].docType === 'derived'));
    return {
      method_class: 'Contingency_Burn_Rate', status_color: status,
      burn_rate_pct: Math.round(burnRate * 100),
      remaining_pct: Math.round((1 - burnRate) * 100),
      burn_stress: burnStress,
      evidence_metric: 'Contingency: ' + Math.round(burnRate * 100) + '% burned at ' +
        Math.round(si.actualPctComplete) + '% complete' +
        (isDerived ? ' — estimated, upload Pay Application contingency detail for precise figures' : '')
    };
  }

  function runCostRiskAnalysis(si) {
    if (!checkInputs(si, ['bac','cpi','ac','ev'])) return insufficientData('Cost_Risk_Analysis');
    var eac = si.bac / si.cpi;
    var uncertainty = Math.max(0.03, Math.abs(1 - si.cpi)) * 0.5;
    var p80EAC = eac * (1 + uncertainty * 1.28);
    var p80DeltaPct = ((p80EAC - si.bac) / si.bac) * 100;
    var status = p80DeltaPct <= 5 ? 'Green' :
                 p80DeltaPct <= 10 ? 'Yellow' :
                 p80DeltaPct <= 20 ? 'Amber' : 'Red';
    return {
      method_class: 'Cost_Risk_Analysis', status_color: status,
      p80_eac: Math.round(p80EAC), p80_delta_pct: Math.round(p80DeltaPct * 10) / 10,
      evidence_metric: 'CRA P80 EAC: $' + Math.round(p80EAC).toLocaleString() +
        ' (+' + Math.round(p80DeltaPct * 10) / 10 + '% BAC)'
    };
  }

  function runParametricCost(si) {
    if (!checkInputs(si, ['bac','ev','ac','actualPctComplete'])) return insufficientData('Parametric_Cost');
    var eacCPI = si.bac / si.cpi;
    var eacParametric = si.ac + (si.bac - si.ev);
    var parametricIndex = eacParametric > 0 ? eacCPI / eacParametric : null;
    if (!parametricIndex) return insufficientData('Parametric_Cost');
    parametricIndex = Math.round(parametricIndex * 1000) / 1000;
    var status = Math.abs(parametricIndex - 1) <= 0.03 ? 'Green' :
                 Math.abs(parametricIndex - 1) <= 0.08 ? 'Yellow' :
                 Math.abs(parametricIndex - 1) <= 0.15 ? 'Amber' : 'Red';
    return {
      method_class: 'Parametric_Cost', status_color: status,
      parametric_index: parametricIndex,
      evidence_metric: 'Parametric index: ' + parametricIndex +
        ' (CPI-EAC vs BAC-EAC divergence)'
    };
  }

  /* ---------- Cat 4 — Doc / Risk extensions ---------- */

  function runRFIVelocity(si) {
    var count = si.rfiCount != null ? si.rfiCount : (si.rfiNumber != null ? si.rfiNumber : null);
    var days = si.rfiPeriodDays != null ? si.rfiPeriodDays : 30;
    if (count == null) return insufficientData('RFI_Velocity');
    var isDerived = si.sources && si.sources['rfiPeriodDays'] &&
                    si.sources['rfiPeriodDays'].docType === 'derived';
    var rfiPerWeek = days > 0 ? (count / days) * 7 : 0;
    rfiPerWeek = Math.round(rfiPerWeek * 10) / 10;
    var status = rfiPerWeek <= 2 ? 'Green' :
                 rfiPerWeek <= 4 ? 'Yellow' :
                 rfiPerWeek <= 8 ? 'Amber' : 'Red';
    var responseNote = '';
    if (si.rfiResponseTimeDays != null) {
      responseNote = ', avg response ' + si.rfiResponseTimeDays + ' days' +
        (si.rfiResponseTimeDays > 14 ? ' — slow response indicates dispute risk' : '');
    }
    return {
      method_class: 'RFI_Velocity', status_color: status,
      rfi_per_week: rfiPerWeek, total_rfis: count, period_days: days,
      response_time_days: si.rfiResponseTimeDays != null ? si.rfiResponseTimeDays : null,
      evidence_metric: count + ' RFIs over ' + days + ' days (' + rfiPerWeek + '/week)' +
        responseNote +
        (isDerived ? ' — assumed 30-day period, upload RFI log for precise velocity' : '')
    };
  }

  function runSubmittalRejection(si) {
    if (!checkInputs(si, ['submittalsTotal','submittalsRejected']))
      return insufficientData('Submittal_Rejection');
    var rejectionRate = si.submittalsTotal > 0 ?
      si.submittalsRejected / si.submittalsTotal : null;
    if (rejectionRate === null) return insufficientData('Submittal_Rejection');
    rejectionRate = Math.round(rejectionRate * 1000) / 1000;
    var status = rejectionRate <= 0.05 ? 'Green' :
                 rejectionRate <= 0.15 ? 'Yellow' :
                 rejectionRate <= 0.25 ? 'Amber' : 'Red';
    var isDerived = si.sources && si.sources['submittalsTotal'] &&
                    si.sources['submittalsTotal'].docType === 'derived';
    return {
      method_class: 'Submittal_Rejection', status_color: status,
      rejection_rate: rejectionRate,
      rejected: si.submittalsRejected, total: si.submittalsTotal,
      evidence_metric: si.submittalsRejected + ' of ' + si.submittalsTotal +
        ' submittals rejected (' + Math.round(rejectionRate * 100) + '%)' +
        (isDerived ? ' — estimated from doc risk, upload Submittal Register for precise figures' : '')
    };
  }

  function runCOFrequency(si) {
    if (!checkInputs(si, ['changeOrderCount','baselineContractSum','revisedContractSum']))
      return insufficientData('CO_Frequency');
    var scopeGrowth = si.baselineContractSum > 0 ?
      ((si.revisedContractSum - si.baselineContractSum) / si.baselineContractSum) * 100 : 0;
    var coRate = si.changeOrderCount;
    var status = (scopeGrowth <= 5 && coRate <= 3) ? 'Green' :
                 (scopeGrowth <= 10 && coRate <= 6) ? 'Yellow' :
                 (scopeGrowth <= 20 && coRate <= 10) ? 'Amber' : 'Red';
    var isDerived = si.sources && (
      (si.sources['changeOrderCount'] && si.sources['changeOrderCount'].docType === 'derived') ||
      (si.sources['baselineContractSum'] && si.sources['baselineContractSum'].docType === 'derived'));
    return {
      method_class: 'CO_Frequency', status_color: status,
      co_count: coRate, scope_growth_pct: Math.round(scopeGrowth * 10) / 10,
      evidence_metric: coRate + ' change orders — scope growth: +' +
        Math.round(scopeGrowth * 10) / 10 + '%' +
        (isDerived ? ' — estimated, upload Change Order log for precise figures' : '')
    };
  }

  function runDisputeEscalation(si) {
    if (!checkInputs(si, ['docRiskScore'])) return insufficientData('Dispute_Escalation');
    var rfiWeight = si.rfiCount ? Math.min(si.rfiCount / 20, 1) * 0.3 : 0;
    var coWeight = si.changeOrderCount ? Math.min(si.changeOrderCount / 10, 1) * 0.3 : 0;
    var docWeight = si.docRiskScore * 0.4;
    var escalationIndex = rfiWeight + coWeight + docWeight;
    escalationIndex = Math.round(escalationIndex * 100) / 100;
    var status = escalationIndex <= 0.20 ? 'Green' :
                 escalationIndex <= 0.40 ? 'Yellow' :
                 escalationIndex <= 0.65 ? 'Amber' : 'Red';
    return {
      method_class: 'Dispute_Escalation', status_color: status,
      escalation_index: escalationIndex,
      evidence_metric: 'Dispute escalation index: ' + escalationIndex +
        ' (doc risk + RFI velocity + CO frequency combined)'
    };
  }

  function runSpecConflictDensity(si) {
    if (!checkInputs(si, ['docRiskScore','rfiCount'])) return insufficientData('Spec_Conflict_Density');
    var conflictDensity = si.rfiCount > 0 ?
      (si.docRiskScore * si.rfiCount) / Math.sqrt(si.rfiCount) : si.docRiskScore;
    conflictDensity = Math.min(1, Math.round(conflictDensity * 100) / 100);
    var status = conflictDensity <= 0.15 ? 'Green' :
                 conflictDensity <= 0.35 ? 'Yellow' :
                 conflictDensity <= 0.60 ? 'Amber' : 'Red';
    return {
      method_class: 'Spec_Conflict_Density', status_color: status,
      conflict_density: conflictDensity,
      evidence_metric: 'Spec conflict density: ' + conflictDensity +
        ' (doc risk weighted by RFI volume)'
    };
  }

  /* ---------- Cat 5 — System dynamics extensions ---------- */

  function runSensitivityAnalysis(si) {
    if (!checkInputs(si, ['bac','ev','ac','pv','cpi','spi']))
      return insufficientData('Sensitivity_Analysis');
    var eacBase = si.bac / si.cpi;
    var deltaCPI = 0.05;
    var eacHighCPI = si.bac / (si.cpi + deltaCPI);
    var eacLowCPI = si.bac / (si.cpi - deltaCPI);
    var cpiSensitivity = Math.abs(eacLowCPI - eacHighCPI) / eacBase;
    var spiSensitivity = Math.abs(si.spi - 1.0) * 0.5;
    var docSensitivity = si.docRiskScore || 0;
    var drivers = [
      { name: 'CPI', sensitivity: cpiSensitivity },
      { name: 'SPI', sensitivity: spiSensitivity },
      { name: 'DocRisk', sensitivity: docSensitivity }
    ].sort(function(a,b) { return b.sensitivity - a.sensitivity; });
    var topDriver = drivers[0];
    var maxSensitivity = topDriver.sensitivity;
    var status = maxSensitivity <= 0.10 ? 'Green' :
                 maxSensitivity <= 0.20 ? 'Yellow' :
                 maxSensitivity <= 0.35 ? 'Amber' : 'Red';
    return {
      method_class: 'Sensitivity_Analysis', status_color: status,
      top_driver: topDriver.name,
      top_sensitivity: Math.round(maxSensitivity * 100),
      drivers: drivers,
      evidence_metric: 'Top risk driver: ' + topDriver.name +
        ' (sensitivity: ' + Math.round(maxSensitivity * 100) + '%)'
    };
  }

  function runTornadoDiagram(si) {
    if (!checkInputs(si, ['cpi','spi','docRiskScore','actualPctComplete','plannedPctComplete']))
      return insufficientData('Tornado_Diagram');
    var risks = [
      { name: 'Cost Performance', impact: Math.abs(1 - si.cpi) * 100 },
      { name: 'Schedule Performance', impact: Math.abs(1 - si.spi) * 100 },
      { name: 'Document Risk', impact: si.docRiskScore * 100 },
      { name: 'Progress Variance', impact: Math.abs(si.actualPctComplete - si.plannedPctComplete) }
    ].sort(function(a,b) { return b.impact - a.impact; });
    var topRisk = risks[0];
    var compositeScore = risks.reduce(function(sum, r) { return sum + r.impact; }, 0) / risks.length;
    var status = compositeScore <= 5 ? 'Green' :
                 compositeScore <= 10 ? 'Yellow' :
                 compositeScore <= 20 ? 'Amber' : 'Red';
    return {
      method_class: 'Tornado_Diagram', status_color: status,
      top_risk: topRisk.name,
      top_impact: Math.round(topRisk.impact * 10) / 10,
      composite_score: Math.round(compositeScore * 10) / 10,
      risks: risks,
      evidence_metric: 'Top risk: ' + topRisk.name +
        ' (' + Math.round(topRisk.impact * 10) / 10 + '% impact)'
    };
  }

  function runScenarioModeling(si) {
    if (!checkInputs(si, ['bac','ev','ac','cpi','spi'])) return insufficientData('Scenario_Modeling');
    var remainingWork = si.bac - si.ev;
    var optimisticEAC = si.ac + remainingWork * 1.00;
    var realisticEAC = si.ac + remainingWork / si.cpi;
    var pessimisticEAC = si.ac + remainingWork / Math.min(si.cpi, si.spi);
    var scenarioRange = (pessimisticEAC - optimisticEAC) / si.bac * 100;
    var status = pessimisticEAC <= si.bac * 1.05 ? 'Green' :
                 pessimisticEAC <= si.bac * 1.10 ? 'Yellow' :
                 pessimisticEAC <= si.bac * 1.20 ? 'Amber' : 'Red';
    return {
      method_class: 'Scenario_Modeling', status_color: status,
      optimistic_eac: Math.round(optimisticEAC),
      realistic_eac: Math.round(realisticEAC),
      pessimistic_eac: Math.round(pessimisticEAC),
      scenario_range_pct: Math.round(scenarioRange * 10) / 10,
      evidence_metric: 'Scenarios: best $' + Math.round(optimisticEAC/1000) + 'k / ' +
        'likely $' + Math.round(realisticEAC/1000) + 'k / ' +
        'worst $' + Math.round(pessimisticEAC/1000) + 'k'
    };
  }

  function runReworkFeedback(si) {
    if (!checkInputs(si, ['cpi'])) return insufficientData('Rework_Feedback');
    var rfiContrib = si.rfiCount ? Math.min(si.rfiCount / 30, 1) * 0.3 : 0;
    var coContrib = si.changeOrderCount ? Math.min(si.changeOrderCount / 15, 1) * 0.3 : 0;
    var cpiContrib = Math.max(0, (1 - si.cpi)) * 0.4;
    var reworkIndex = rfiContrib + coContrib + cpiContrib;
    reworkIndex = Math.round(reworkIndex * 100) / 100;
    var status = reworkIndex <= 0.10 ? 'Green' :
                 reworkIndex <= 0.25 ? 'Yellow' :
                 reworkIndex <= 0.45 ? 'Amber' : 'Red';
    return {
      method_class: 'Rework_Feedback', status_color: status,
      rework_index: reworkIndex,
      evidence_metric: 'Rework feedback index: ' + reworkIndex +
        ' (CPI degradation + RFI + CO combined)'
    };
  }

  function runDiscreteEventSim(si) {
    if (!checkInputs(si, ['spi','actualPctComplete','plannedPctComplete','cpi']))
      return insufficientData('Discrete_Event_Sim');
    var progressRatio = si.plannedPctComplete > 0 ?
      si.actualPctComplete / si.plannedPctComplete : 1;
    var interruptionRate = Math.max(0, 1 - progressRatio) +
                          Math.max(0, 1 - si.spi) * 0.5;
    var throughputIndex = 1 / (1 + interruptionRate);
    throughputIndex = Math.round(throughputIndex * 1000) / 1000;
    var status = throughputIndex >= 0.92 ? 'Green' :
                 throughputIndex >= 0.85 ? 'Yellow' :
                 throughputIndex >= 0.75 ? 'Amber' : 'Red';
    return {
      method_class: 'Discrete_Event_Sim', status_color: status,
      throughput_index: throughputIndex,
      interruption_rate: Math.round(interruptionRate * 100),
      evidence_metric: 'DES throughput: ' + throughputIndex +
        ' (' + Math.round(interruptionRate * 100) + '% interruption rate)'
    };
  }

  /* ---------- Cat 6 — Synthesis extensions (consume the project) ---------- */

  function voteBucket(status) {
    if (!status) return null;
    return status.indexOf('Red') >= 0 ? 'Red' :
           status === 'Amber' ? 'Amber' :
           status === 'Yellow' ? 'Yellow' : 'Green';
  }

  function runWeightedVoting(project) {
    project = project || {};
    var s = project.signals || {};
    var sim = (project.simulationSignals && project.simulationSignals.signal_array) || [];
    var votes = { Green: 0, Yellow: 0, Amber: 0, Red: 0 };
    var weights = { cat1: 1.5, cat2: 1.2, cat3: 1.2, cat4: 1.0,
                    cat5: 0.8, cat6: 1.0, cat7: 0.6, cat9: 1.5 };
    function addVote(status, catWeight) {
      var b = voteBucket(status);
      if (!b) return;
      votes[b] += catWeight;
    }
    if (s.mc) addVote(s.mc.status, weights.cat1);
    if (s.cusum) addVote(s.cusum.status, weights.cat1);
    if (s.doc) addVote(s.doc.status, weights.cat4);
    sim.forEach(function(m) { addVote(m.status_color, weights.cat7); });
    if (s.decision) addVote(s.decision.state, weights.cat9);
    var total = Object.keys(votes).reduce(function(a,k){return a+votes[k];},0);
    if (total === 0) return insufficientData('Weighted_Voting');
    var dominant = Object.keys(votes).reduce(function(a, b) {
      return votes[a] > votes[b] ? a : b;
    });
    var dominantPct = Math.round((votes[dominant] / total) * 100);
    return {
      method_class: 'Weighted_Voting', status_color: dominant,
      votes: votes, dominant_pct: dominantPct,
      evidence_metric: 'Weighted vote: ' + dominant + ' (' + dominantPct + '% of weighted signals)'
    };
  }

  function runMajorityRules(project) {
    project = project || {};
    var s = project.signals || {};
    var sim = (project.simulationSignals && project.simulationSignals.signal_array) || [];
    var counts = { Green: 0, Yellow: 0, Amber: 0, Red: 0 };
    function count(status) {
      var b = voteBucket(status);
      if (!b) return;
      counts[b]++;
    }
    if (s.mc) count(s.mc.status);
    if (s.cusum) count(s.cusum.status);
    if (s.doc) count(s.doc.status);
    sim.forEach(function(m) { count(m.status_color); });
    var total = Object.keys(counts).reduce(function(a,k){return a+counts[k];},0);
    if (total === 0) return insufficientData('Majority_Rules');
    var majority = Object.keys(counts).reduce(function(a, b) {
      return counts[a] > counts[b] ? a : b;
    });
    var majorityPct = Math.round((counts[majority] / total) * 100);
    return {
      method_class: 'Majority_Rules', status_color: majority,
      counts: counts, majority_pct: majorityPct, total_votes: total,
      evidence_metric: majority + ' by majority (' + counts[majority] +
        ' of ' + total + ' modules, ' + majorityPct + '%)'
    };
  }

  function runWorstNofM(project) {
    project = project || {};
    var s = project.signals || {};
    var sim = (project.simulationSignals && project.simulationSignals.signal_array) || [];
    var allStatuses = [];
    if (s.mc) allStatuses.push(s.mc.status);
    if (s.cusum) allStatuses.push(s.cusum.status);
    if (s.doc) allStatuses.push(s.doc.status);
    sim.forEach(function(m) { if (m.status_color) allStatuses.push(m.status_color); });
    if (!allStatuses.length) return insufficientData('Worst_N_of_M');
    var redCount = allStatuses.filter(function(st) { return st && st.indexOf('Red') >= 0; }).length;
    var amberCount = allStatuses.filter(function(st) { return st === 'Amber'; }).length;
    var M = allStatuses.length;
    var status = redCount >= Math.ceil(M * 0.3) ? 'Red' :
                 amberCount >= Math.ceil(M * 0.4) ? 'Amber' :
                 redCount >= 1 ? 'Yellow' : 'Green';
    return {
      method_class: 'Worst_N_of_M', status_color: status,
      red_count: redCount, amber_count: amberCount, total_modules: M,
      evidence_metric: redCount + ' Red + ' + amberCount + ' Amber of ' + M + ' total modules'
    };
  }

  /* ---------- Cat 7 — Evidence combination extensions ---------- */

  function runPythagoreanFuzzy(si) {
    if (!checkInputs(si, ['cpi','spi','docRiskScore'])) return insufficientData('Pythagorean_Fuzzy');
    var evmMin = Math.min(si.cpi, si.spi);
    var mu_g = Math.min(1, Math.max(0, (evmMin - 0.85) / 0.15));
    var nu_g = Math.min(1, Math.max(0, (0.95 - evmMin) / 0.15));
    if (mu_g * mu_g + nu_g * nu_g > 1) {
      var norm = Math.sqrt(mu_g * mu_g + nu_g * nu_g);
      mu_g /= norm; nu_g /= norm;
    }
    var pi_g = Math.sqrt(Math.max(0, 1 - mu_g * mu_g - nu_g * nu_g));
    var docRisk = si.docRiskScore || 0;
    var adjustedMu = mu_g * (1 - docRisk * 0.3);
    var adjustedNu = Math.min(1, nu_g + docRisk * 0.3);
    var score = adjustedMu - adjustedNu;
    var status = score >= 0.3 ? 'Green' :
                 score >= 0.0 ? 'Yellow' :
                 score >= -0.3 ? 'Amber' : 'Red';
    return {
      method_class: 'Pythagorean_Fuzzy', status_color: status,
      membership: Math.round(adjustedMu * 100) / 100,
      non_membership: Math.round(adjustedNu * 100) / 100,
      hesitancy: Math.round(pi_g * 100) / 100,
      evidence_metric: 'PFS: μ=' + Math.round(adjustedMu*100)/100 +
        ' ν=' + Math.round(adjustedNu*100)/100 +
        ' π=' + Math.round(pi_g*100)/100
    };
  }

  function runPictureFuzzy(si) {
    if (!checkInputs(si, ['cpi','spi','docRiskScore'])) return insufficientData('Picture_Fuzzy');
    var evmMin = Math.min(si.cpi, si.spi);
    var positive = Math.max(0, Math.min(0.95, (evmMin - 0.85) / 0.15));
    var negative = Math.max(0, Math.min(0.95, (0.95 - evmMin) / 0.15)) *
                   (1 + si.docRiskScore * 0.5);
    negative = Math.min(0.95, negative);
    var neutral = Math.max(0, 0.6 - positive - negative) * 0.3;
    var refusal = Math.max(0, 1 - positive - neutral - negative);
    var score = positive - negative;
    var status = score >= 0.30 ? 'Green' :
                 score >= 0.00 ? 'Yellow' :
                 score >= -0.30 ? 'Amber' : 'Red';
    return {
      method_class: 'Picture_Fuzzy', status_color: status,
      positive: Math.round(positive * 100) / 100,
      neutral: Math.round(neutral * 100) / 100,
      negative: Math.round(negative * 100) / 100,
      refusal: Math.round(refusal * 100) / 100,
      evidence_metric: 'PicFS: +' + Math.round(positive*100)/100 +
        ' 0' + Math.round(neutral*100)/100 +
        ' -' + Math.round(negative*100)/100 +
        ' r' + Math.round(refusal*100)/100
    };
  }

  function runHesitantFuzzy(si) {
    if (!checkInputs(si, ['cpi','spi'])) return insufficientData('Hesitant_Fuzzy');
    var evmMin = Math.min(si.cpi, si.spi);
    var evmMax = Math.max(si.cpi, si.spi);
    var memberships = [
      Math.max(0, Math.min(1, (evmMin - 0.85) / 0.15)),
      Math.max(0, Math.min(1, (evmMax - 0.85) / 0.15)),
      Math.max(0, Math.min(1, ((evmMin + evmMax) / 2 - 0.85) / 0.15))
    ];
    var score = memberships.reduce(function(a,b){return a+b;},0) / memberships.length;
    var hesitancy = Math.max.apply(null, memberships) - Math.min.apply(null, memberships);
    var status = score >= 0.7 ? 'Green' :
                 score >= 0.5 ? 'Yellow' :
                 score >= 0.3 ? 'Amber' : 'Red';
    return {
      method_class: 'Hesitant_Fuzzy', status_color: status,
      memberships: memberships.map(function(m){return Math.round(m*100)/100;}),
      average_membership: Math.round(score * 100) / 100,
      hesitancy_degree: Math.round(hesitancy * 100) / 100,
      evidence_metric: 'HFS: avg membership ' + Math.round(score*100)/100 +
        ', hesitancy ' + Math.round(hesitancy*100)/100
    };
  }

  function runType2Fuzzy(si) {
    if (!checkInputs(si, ['cpi','spi'])) return insufficientData('Type2_Fuzzy');
    var evmMin = Math.min(si.cpi, si.spi);
    var primaryMembership = Math.max(0, Math.min(1, (evmMin - 0.85) / 0.15));
    var uncertainty = Math.abs(si.cpi - si.spi) * 2;
    var lowerMembership = Math.max(0, primaryMembership - uncertainty * 0.5);
    var upperMembership = Math.min(1, primaryMembership + uncertainty * 0.5);
    var centroid = (lowerMembership + upperMembership) / 2;
    var footprint = upperMembership - lowerMembership;
    var status = centroid >= 0.7 && footprint <= 0.2 ? 'Green' :
                 centroid >= 0.5 ? 'Yellow' :
                 centroid >= 0.3 ? 'Amber' : 'Red';
    return {
      method_class: 'Type2_Fuzzy', status_color: status,
      lower_membership: Math.round(lowerMembership * 100) / 100,
      upper_membership: Math.round(upperMembership * 100) / 100,
      centroid: Math.round(centroid * 100) / 100,
      footprint_of_uncertainty: Math.round(footprint * 100) / 100,
      evidence_metric: 'T2FS: centroid ' + Math.round(centroid*100)/100 +
        ', FOU ' + Math.round(footprint*100)/100
    };
  }

  function runMaximumEntropy(si) {
    if (!checkInputs(si, ['cpi','spi','docRiskScore'])) return insufficientData('Maximum_Entropy');
    var evmMin = Math.min(si.cpi, si.spi);
    var rawProbs = [
      Math.max(0.01, evmMin >= 0.95 ? 0.70 : evmMin >= 0.90 ? 0.20 : 0.05),
      Math.max(0.01, evmMin >= 0.95 ? 0.20 : evmMin >= 0.90 ? 0.50 : 0.20),
      Math.max(0.01, evmMin >= 0.95 ? 0.07 : evmMin >= 0.90 ? 0.25 : 0.60),
      Math.max(0.01, evmMin >= 0.95 ? 0.02 : evmMin >= 0.90 ? 0.05 : 0.15)
    ];
    var sum = rawProbs.reduce(function(a,b){return a+b;},0);
    var probs = rawProbs.map(function(p){return p/sum;});
    var docAdjust = si.docRiskScore || 0;
    probs[2] = Math.min(0.95, probs[2] + docAdjust * 0.2);
    probs[3] = Math.min(0.95, probs[3] + docAdjust * 0.1);
    sum = probs.reduce(function(a,b){return a+b;},0);
    probs = probs.map(function(p){return p/sum;});
    var entropy = -probs.reduce(function(h,p){return h + (p > 0 ? p * Math.log2(p) : 0);}, 0);
    var maxEntropy = Math.log2(4);
    var normalizedEntropy = entropy / maxEntropy;
    var labels = ['Green','Yellow','Amber','Red'];
    var dominant = labels[probs.indexOf(Math.max.apply(null, probs))];
    return {
      method_class: 'Maximum_Entropy', status_color: dominant,
      probabilities: { Green: Math.round(probs[0]*100), Yellow: Math.round(probs[1]*100),
                       Amber: Math.round(probs[2]*100), Red: Math.round(probs[3]*100) },
      entropy: Math.round(normalizedEntropy * 100) / 100,
      evidence_metric: 'MaxEnt: ' + dominant + ' (entropy ' +
        Math.round(normalizedEntropy*100)/100 + ')'
    };
  }

  function runPossibilityTheory(si) {
    if (!checkInputs(si, ['cpi','spi','docRiskScore'])) return insufficientData('Possibility_Theory');
    var evmMin = Math.min(si.cpi, si.spi);
    var docRisk = si.docRiskScore || 0;
    var possibility = {
      Green: Math.min(1, Math.max(0, (evmMin - 0.85) / 0.10) * (1 - docRisk * 0.5)),
      Amber: Math.min(1, Math.max(0, 1 - (evmMin - 0.88) / 0.10) * (1 + docRisk * 0.3)),
      Red: Math.min(1, Math.max(0, (0.92 - evmMin) / 0.10) + docRisk * 0.4)
    };
    var necessity = {
      Green: Math.max(0, possibility.Green - 0.3),
      Amber: Math.max(0, possibility.Amber - 0.3),
      Red: Math.max(0, possibility.Red - 0.3)
    };
    var dominant = Object.keys(possibility).reduce(function(a, b) {
      return possibility[a] > possibility[b] ? a : b;
    });
    return {
      method_class: 'Possibility_Theory', status_color: dominant,
      possibility: { Green: Math.round(possibility.Green*100)/100,
                     Amber: Math.round(possibility.Amber*100)/100,
                     Red: Math.round(possibility.Red*100)/100 },
      necessity: { Green: Math.round(necessity.Green*100)/100,
                   Amber: Math.round(necessity.Amber*100)/100,
                   Red: Math.round(necessity.Red*100)/100 },
      evidence_metric: 'Possibility: ' + dominant +
        ' (Π=' + Math.round(possibility[dominant]*100)/100 +
        ', N=' + Math.round(necessity[dominant]*100)/100 + ')'
    };
  }

  function runSphericalFuzzy(si) {
    if (!checkInputs(si, ['cpi','spi','docRiskScore'])) return insufficientData('Spherical_Fuzzy');
    var evmMin = Math.min(si.cpi, si.spi);
    var mu = Math.max(0, Math.min(0.95, (evmMin - 0.82) / 0.18));
    var nu = Math.max(0, Math.min(0.95, (0.98 - evmMin) / 0.18)) *
             (1 + (si.docRiskScore || 0) * 0.5);
    nu = Math.min(0.95, nu);
    var constraint = mu * mu + nu * nu;
    if (constraint > 1) { var sc = Math.sqrt(constraint); mu /= sc; nu /= sc; }
    var pi = Math.sqrt(Math.max(0, 1 - mu * mu - nu * nu));
    var score = mu - nu;
    var status = score >= 0.4 ? 'Green' :
                 score >= 0.1 ? 'Yellow' :
                 score >= -0.2 ? 'Amber' : 'Red';
    return {
      method_class: 'Spherical_Fuzzy', status_color: status,
      mu: Math.round(mu*100)/100, nu: Math.round(nu*100)/100, pi: Math.round(pi*100)/100,
      score: Math.round(score*100)/100,
      evidence_metric: 'SFS: μ=' + Math.round(mu*100)/100 +
        ' ν=' + Math.round(nu*100)/100 +
        ' π=' + Math.round(pi*100)/100
    };
  }

  function runFermateanFuzzy(si) {
    if (!checkInputs(si, ['cpi','spi'])) return insufficientData('Fermatean_Fuzzy');
    var evmMin = Math.min(si.cpi, si.spi);
    var mu = Math.max(0, Math.min(0.99, (evmMin - 0.80) / 0.20));
    var nu = Math.max(0, Math.min(0.99, (1.00 - evmMin) / 0.20));
    while (mu*mu*mu + nu*nu*nu > 1) { mu *= 0.95; nu *= 0.95; }
    var pi = Math.pow(Math.max(0, 1 - Math.pow(mu,3) - Math.pow(nu,3)), 1/3);
    var score = mu - nu;
    var status = score >= 0.35 ? 'Green' :
                 score >= 0.05 ? 'Yellow' :
                 score >= -0.25 ? 'Amber' : 'Red';
    return {
      method_class: 'Fermatean_Fuzzy', status_color: status,
      mu: Math.round(mu*100)/100, nu: Math.round(nu*100)/100, pi: Math.round(pi*100)/100,
      evidence_metric: 'FFS: μ=' + Math.round(mu*100)/100 +
        ' ν=' + Math.round(nu*100)/100 +
        ' π=' + Math.round(pi*100)/100
    };
  }

  function runMARCOS(si) {
    if (!checkInputs(si, ['cpi','spi','docRiskScore'])) return insufficientData('MARCOS');
    var criteria = [
      { value: si.cpi, ideal: 1.05, anti: 0.80, weight: 0.40 },
      { value: si.spi, ideal: 1.05, anti: 0.80, weight: 0.35 },
      { value: 1 - (si.docRiskScore || 0), ideal: 1.00, anti: 0.30, weight: 0.25 }
    ];
    var utilityIdeal = criteria.reduce(function(sum, c) {
      var range = c.ideal - c.anti;
      var norm = range > 0 ? (c.value - c.anti) / range : 0.5;
      norm = Math.max(0, Math.min(1, norm));
      return sum + norm * c.weight;
    }, 0);
    var utilityAnti = 1 - utilityIdeal;
    var f_ideal = utilityIdeal / (utilityIdeal + utilityAnti);
    var f_anti = utilityAnti / (utilityIdeal + utilityAnti);
    var marcosScore = (f_ideal + f_anti) / (1 + (1 - f_ideal) / f_ideal + (1 - f_anti) / f_anti);
    marcosScore = Math.round(marcosScore * 1000) / 1000;
    var status = marcosScore >= 0.65 ? 'Green' :
                 marcosScore >= 0.50 ? 'Yellow' :
                 marcosScore >= 0.35 ? 'Amber' : 'Red';
    return {
      method_class: 'MARCOS', status_color: status,
      marcos_score: marcosScore,
      utility_ideal: Math.round(utilityIdeal * 100) / 100,
      evidence_metric: 'MARCOS score: ' + marcosScore +
        ' (utility vs ideal: ' + Math.round(utilityIdeal*100)/100 + ')'
    };
  }

  function runCRITIC_TOPSIS(si) {
    if (!checkInputs(si, ['cpi','spi','docRiskScore'])) return insufficientData('CRITIC_TOPSIS');
    var criteria = [si.cpi, si.spi, 1 - (si.docRiskScore || 0)];
    var mean = criteria.reduce(function(a,b){return a+b;},0) / criteria.length;
    var stddev = Math.sqrt(criteria.reduce(function(s,v){
      return s + Math.pow(v - mean, 2);
    }, 0) / criteria.length);
    var weights = criteria.map(function(v) {
      return stddev > 0 ? Math.abs(v - mean) / stddev : 1/3;
    });
    var wSum = weights.reduce(function(a,b){return a+b;},0);
    weights = weights.map(function(w){return w/wSum;});
    var ideal = [1.05, 1.05, 1.00];
    var antiIdeal = [0.80, 0.80, 0.30];
    var dIdeal = Math.sqrt(criteria.reduce(function(s,v,i){
      return s + weights[i] * Math.pow(v - ideal[i], 2);
    }, 0));
    var dAnti = Math.sqrt(criteria.reduce(function(s,v,i){
      return s + weights[i] * Math.pow(v - antiIdeal[i], 2);
    }, 0));
    var topsisScore = dAnti / (dIdeal + dAnti + 0.0001);
    topsisScore = Math.round(topsisScore * 1000) / 1000;
    var status = topsisScore >= 0.65 ? 'Green' :
                 topsisScore >= 0.50 ? 'Yellow' :
                 topsisScore >= 0.35 ? 'Amber' : 'Red';
    return {
      method_class: 'CRITIC_TOPSIS', status_color: status,
      topsis_score: topsisScore,
      distance_ideal: Math.round(dIdeal*1000)/1000,
      distance_anti: Math.round(dAnti*1000)/1000,
      evidence_metric: 'CRITIC-TOPSIS: ' + topsisScore +
        ' (d+ ' + Math.round(dIdeal*1000)/1000 +
        ', d- ' + Math.round(dAnti*1000)/1000 + ')'
    };
  }

  function runHypersoftSets(si) {
    if (!checkInputs(si, ['cpi','spi','docRiskScore'])) return insufficientData('Hypersoft_Sets');
    var attributes = {
      cost: si.cpi < 0.90 ? 'poor' : si.cpi < 0.95 ? 'fair' : 'good',
      schedule: si.spi < 0.90 ? 'poor' : si.spi < 0.95 ? 'fair' : 'good',
      risk: (si.docRiskScore||0) > 0.70 ? 'high' : (si.docRiskScore||0) > 0.30 ? 'medium' : 'low'
    };
    var combinations = {
      'good-good-low': 0.90, 'good-good-medium': 0.75, 'good-good-high': 0.55,
      'good-fair-low': 0.70, 'good-fair-medium': 0.55, 'good-fair-high': 0.40,
      'fair-good-low': 0.70, 'fair-good-medium': 0.55, 'fair-good-high': 0.40,
      'fair-fair-low': 0.55, 'fair-fair-medium': 0.40, 'fair-fair-high': 0.30,
      'good-poor-low': 0.50, 'poor-good-low': 0.50, 'poor-poor-low': 0.30,
      'poor-fair-low': 0.35, 'fair-poor-low': 0.35,
      'good-poor-medium': 0.35, 'poor-good-medium': 0.35,
      'poor-poor-medium': 0.20, 'poor-poor-high': 0.10,
      'fair-poor-high': 0.20, 'poor-fair-high': 0.20,
      'good-poor-high': 0.25, 'poor-good-high': 0.25
    };
    var key = attributes.cost + '-' + attributes.schedule + '-' + attributes.risk;
    var score = combinations[key] !== undefined ? combinations[key] : 0.35;
    var status = score >= 0.70 ? 'Green' :
                 score >= 0.50 ? 'Yellow' :
                 score >= 0.30 ? 'Amber' : 'Red';
    return {
      method_class: 'Hypersoft_Sets', status_color: status,
      attribute_combination: key, score: score,
      evidence_metric: 'Hypersoft [' + key + ']: score ' + score
    };
  }

  /* ---------- Cat 9 — Governance extensions ---------- */

  function runFARThreshold(si) {
    if (!checkInputs(si, ['bac','cpi','ev','ac'])) return insufficientData('FAR_Threshold');
    var eac = si.bac / si.cpi;
    var overrunPct = ((eac - si.bac) / si.bac) * 100;
    var far34Threshold = 25;
    var distanceToThreshold = far34Threshold - overrunPct;
    var status = overrunPct <= 5 ? 'Green' :
                 overrunPct <= 15 ? 'Yellow' :
                 overrunPct <= 25 ? 'Amber' : 'Red';
    return {
      method_class: 'FAR_Threshold', status_color: status,
      overrun_pct: Math.round(overrunPct * 10) / 10,
      far34_threshold_pct: far34Threshold,
      distance_to_threshold: Math.round(distanceToThreshold * 10) / 10,
      far_reporting_required: overrunPct >= far34Threshold,
      evidence_metric: 'FAR Part 34: ' + Math.round(overrunPct*10)/10 +
        '% overrun — threshold ' + far34Threshold + '% (' +
        (overrunPct >= far34Threshold ? 'REPORTING REQUIRED' :
         Math.round(distanceToThreshold*10)/10 + '% headroom') + ')'
    };
  }

  function runOMBA11Check(si) {
    if (!checkInputs(si, ['bac','cpi','actualPctComplete'])) return insufficientData('OMB_A11_Check');
    var cpiBelow90 = si.cpi < 0.90;
    var majorProgram = si.bac >= 10000000;
    var reportingTriggered = cpiBelow90 && majorProgram;
    var eac = si.bac / si.cpi;
    var projectedOverrun = eac - si.bac;
    var status = !cpiBelow90 ? 'Green' :
                 si.cpi >= 0.92 ? 'Yellow' :
                 si.cpi >= 0.88 ? 'Amber' : 'Red';
    return {
      method_class: 'OMB_A11_Check', status_color: status,
      cpi_below_90: cpiBelow90,
      major_program: majorProgram,
      reporting_triggered: reportingTriggered,
      projected_overrun: Math.round(projectedOverrun),
      evidence_metric: 'OMB A-11: CPI ' + si.cpi +
        (reportingTriggered ? ' — MANDATORY REPORTING TRIGGERED' :
         cpiBelow90 ? ' — below threshold, monitor' : ' — within threshold')
    };
  }

  function runEVMReportingThreshold(si) {
    if (!checkInputs(si, ['bac','cpi','spi'])) return insufficientData('EVM_Reporting_Threshold');
    var cpiBreached = si.cpi < 0.90;
    var spiBreached = si.spi < 0.90;
    var bothBreached = cpiBreached && spiBreached;
    var eac = si.bac / si.cpi;
    var eacDeltaPct = ((eac - si.bac) / si.bac) * 100;
    var status = (!cpiBreached && !spiBreached) ? 'Green' :
                 (cpiBreached !== spiBreached) ? 'Yellow' :
                 bothBreached && eacDeltaPct <= 15 ? 'Amber' : 'Red';
    return {
      method_class: 'EVM_Reporting_Threshold', status_color: status,
      cpi_breached: cpiBreached, spi_breached: spiBreached,
      both_breached: bothBreached,
      eac_delta_pct: Math.round(eacDeltaPct * 10) / 10,
      evidence_metric: 'EVM threshold: CPI ' + (cpiBreached ? 'BREACHED' : 'ok') +
        ', SPI ' + (spiBreached ? 'BREACHED' : 'ok') +
        ', EAC +' + Math.round(eacDeltaPct*10)/10 + '%'
    };
  }

  function runContractModFrequency(si) {
    if (!checkInputs(si, ['changeOrderCount','baselineContractSum','revisedContractSum']))
      return insufficientData('Contract_Mod_Frequency');
    var scopeGrowthPct = si.baselineContractSum > 0 ?
      ((si.revisedContractSum - si.baselineContractSum) / si.baselineContractSum) * 100 : 0;
    var riskLevel = si.changeOrderCount >= 10 || scopeGrowthPct >= 20 ? 'Red' :
                    si.changeOrderCount >= 6 || scopeGrowthPct >= 10 ? 'Amber' :
                    si.changeOrderCount >= 3 || scopeGrowthPct >= 5 ? 'Yellow' : 'Green';
    var isDerived = si.sources && (
      (si.sources['changeOrderCount'] && si.sources['changeOrderCount'].docType === 'derived') ||
      (si.sources['baselineContractSum'] && si.sources['baselineContractSum'].docType === 'derived'));
    return {
      method_class: 'Contract_Mod_Frequency', status_color: riskLevel,
      co_count: si.changeOrderCount,
      scope_growth_pct: Math.round(scopeGrowthPct * 10) / 10,
      evidence_metric: si.changeOrderCount + ' contract modifications — ' +
        Math.round(scopeGrowthPct*10)/10 + '% scope growth — ' +
        (riskLevel === 'Red' ? 'contracting officer review merits consideration' :
         riskLevel === 'Amber' ? 'elevated modification frequency' : 'within normal range') +
        (isDerived ? ' — estimated, upload Change Order log for precise figures' : '')
    };
  }

  /* ---------- modules fed by derived fields (Code.gs v10.18) ---------- */

  // Cat 2.8 — Look-Ahead Schedule Health
  function runLookaheadHealth(si) {
    if (!checkInputs(si, ['activitiesPlanned','activitiesConstrained']))
      return insufficientData('Lookahead_Health');
    var constraintRate = si.activitiesPlanned > 0 ?
      si.activitiesConstrained / si.activitiesPlanned : 0;
    var isDerived = si.sources && si.sources['activitiesPlanned'] &&
                    si.sources['activitiesPlanned'].docType === 'derived';
    var status = constraintRate <= 0.10 ? 'Green' :
                 constraintRate <= 0.25 ? 'Yellow' :
                 constraintRate <= 0.40 ? 'Amber' : 'Red';
    return {
      method_class: 'Lookahead_Health', status_color: status,
      constraint_rate: Math.round(constraintRate * 100),
      constrained: si.activitiesConstrained, planned: si.activitiesPlanned,
      evidence_metric: si.activitiesConstrained + ' of ' + si.activitiesPlanned +
        ' planned activities constrained (' + Math.round(constraintRate * 100) + '%)' +
        (isDerived ? ' — estimated, upload Look-Ahead Schedule for precise figures' : '')
    };
  }

  // Cat 4.5 — Weather Day Impact
  function runWeatherImpact(si) {
    if (!checkInputs(si, ['weatherDaysLost'])) return insufficientData('Weather_Impact');
    var isDerived = si.sources && si.sources['weatherDaysLost'] &&
                    si.sources['weatherDaysLost'].docType === 'derived';
    var float = si.floatRemaining != null ? si.floatRemaining :
                (si.totalFloat != null ? (si.totalFloat - (si.consumedFloat || 0)) : null);
    var weatherRatio = (float != null && float > 0) ? si.weatherDaysLost / float :
                       (si.weatherDaysLost > 0 ? 1.0 : 0);
    var status = si.weatherDaysLost === 0 ? 'Green' :
                 weatherRatio <= 0.20 ? 'Yellow' :
                 weatherRatio <= 0.50 ? 'Amber' : 'Red';
    return {
      method_class: 'Weather_Impact', status_color: status,
      weather_days_lost: si.weatherDaysLost, float_remaining: float,
      weather_ratio: Math.round(weatherRatio * 100),
      evidence_metric: si.weatherDaysLost + ' weather days lost' +
        (float != null ? ', ' + Math.round(weatherRatio * 100) + '% of available float consumed' : '') +
        (isDerived ? ' — estimated, upload Field Report for precise figures' : '')
    };
  }

  // Cat 9.6 — Quality Compliance Index
  function runQualityCompliance(si) {
    if (!checkInputs(si, ['qualityDeficienciesNoted']))
      return insufficientData('Quality_Compliance');
    var isDerived = si.sources && si.sources['qualityDeficienciesNoted'] &&
                    si.sources['qualityDeficienciesNoted'].docType === 'derived';
    var inspected = si.itemsInspected != null ? si.itemsInspected : 20;
    var failed = si.itemsFailed != null ? si.itemsFailed : si.qualityDeficienciesNoted;
    var passRate = inspected > 0 ? (inspected - failed) / inspected : 1;
    var auditScore = si.qualityAuditScore != null ? si.qualityAuditScore : (passRate * 100);
    var status = auditScore >= 85 ? 'Green' :
                 auditScore >= 70 ? 'Yellow' :
                 auditScore >= 55 ? 'Amber' : 'Red';
    return {
      method_class: 'Quality_Compliance', status_color: status,
      quality_score: Math.round(auditScore), pass_rate: Math.round(passRate * 100),
      deficiencies: si.qualityDeficienciesNoted,
      evidence_metric: 'Quality compliance: ' + Math.round(auditScore) + '/100 — ' +
        si.qualityDeficienciesNoted + ' deficiencies noted' +
        (isDerived ? ' — estimated from field observations, upload Quality Audit for precise score' : '')
    };
  }

  // Cat 9.7 — Safety Performance Index
  function runSafetyPerformance(si) {
    if (!checkInputs(si, ['safetyIncidentsDiscussed']))
      return insufficientData('Safety_Performance');
    var isDerived = si.sources && si.sources['safetyIncidentsDiscussed'] &&
                    si.sources['safetyIncidentsDiscussed'].docType === 'derived';
    var incidentRate = si.oshaIncidentRate != null ? si.oshaIncidentRate :
                       si.safetyIncidentsDiscussed * 10;
    var industryBenchmark = 3.0;
    var safetyIndex = incidentRate > 0 ? industryBenchmark / incidentRate : 1;
    safetyIndex = Math.min(2, Math.round(safetyIndex * 100) / 100);
    var status = incidentRate <= industryBenchmark ? 'Green' :
                 incidentRate <= industryBenchmark * 2 ? 'Yellow' :
                 incidentRate <= industryBenchmark * 5 ? 'Amber' : 'Red';
    return {
      method_class: 'Safety_Performance', status_color: status,
      incident_rate: Math.round(incidentRate * 10) / 10,
      industry_benchmark: industryBenchmark, safety_index: safetyIndex,
      incidents_discussed: si.safetyIncidentsDiscussed,
      evidence_metric: 'Safety: ' + si.safetyIncidentsDiscussed + ' incidents in OAC records' +
        (si.oshaIncidentRate != null ? ', OSHA rate ' + Math.round(si.oshaIncidentRate * 10) / 10 : '') +
        (isDerived ? ' — estimated from meeting records, upload Safety Report for OSHA rate' : '')
    };
  }

  // Cat 9.8 — Environmental Compliance Rate
  function runEnvironmentalCompliance(si) {
    if (!checkInputs(si, ['environmentalIssuesDiscussed']))
      return insufficientData('Environmental_Compliance');
    var isDerived = si.sources && si.sources['environmentalIssuesDiscussed'] &&
                    si.sources['environmentalIssuesDiscussed'].docType === 'derived';
    var complianceRate = si.environmentalComplianceRate != null ?
      si.environmentalComplianceRate :
      Math.max(50, 100 - (si.environmentalIssuesDiscussed * 5));
    complianceRate = Math.min(100, Math.round(complianceRate * 10) / 10);
    var status = complianceRate >= 95 ? 'Green' :
                 complianceRate >= 85 ? 'Yellow' :
                 complianceRate >= 70 ? 'Amber' : 'Red';
    return {
      method_class: 'Environmental_Compliance', status_color: status,
      compliance_rate: complianceRate, issues_discussed: si.environmentalIssuesDiscussed,
      violations: si.environmentalViolations || 0,
      evidence_metric: 'Environmental compliance: ' + complianceRate + '%' +
        (si.environmentalViolations ? ', ' + si.environmentalViolations + ' violations recorded' : '') +
        (isDerived ? ' — estimated from meeting records, upload Environmental Report for permit data' : '')
    };
  }

  // Cat 4.8 — Subcontractor Performance (derived from OAC + NCR + RFI + doc risk)
  function runSubcontractorPerformance(si) {
    if (si.subcontractorComplianceScore == null &&
        si.subcontractorIssuesDiscussed == null && si.docRiskScore == null)
      return insufficientData('Subcontractor_Performance');
    // Score is normally derived in signals.js before runAll; derive on demand
    // as a safety net when that path didn't run.
    if (si.subcontractorComplianceScore == null &&
        typeof window !== 'undefined' && window.LinSignals && window.LinSignals.deriveExtendedFields) {
      si = window.LinSignals.deriveExtendedFields(si);
    }
    var score = si.subcontractorComplianceScore;
    if (score == null) return insufficientData('Subcontractor_Performance');
    var isDerived = si.sources && si.sources['subcontractorComplianceScore'] &&
                    si.sources['subcontractorComplianceScore'].docType === 'derived';
    var scorePct = Math.round(score * 100);
    var status = scorePct >= 85 ? 'Green' :
                 scorePct >= 70 ? 'Yellow' :
                 scorePct >= 55 ? 'Amber' : 'Red';
    var signals = [];
    if (si.subcontractorIssuesDiscussed > 0)
      signals.push(si.subcontractorIssuesDiscussed + ' issues in OAC minutes');
    if (si.outstandingActionItems > 0)
      signals.push(si.outstandingActionItems + ' outstanding action items');
    if (si.ncrOpen > 0) signals.push(si.ncrOpen + ' open NCRs');
    if (si.docRiskScore > 0.30)
      signals.push('elevated document risk (' + Math.round(si.docRiskScore * 100) + '%)');
    return {
      method_class: 'Subcontractor_Performance', status_color: status,
      compliance_score: scorePct, signals_contributing: signals,
      evidence_metric: 'Subcontractor compliance: ' + scorePct + '%' +
        (signals.length ? ' — ' + signals.join(', ') : '') +
        (isDerived ? ' — derived from meeting records and correspondence' :
                     ' — from subcontractor performance report')
    };
  }

  // Cat 3.5 — Material Cost Variance (derived material baseline vs current)
  function runMaterialCostVariance(si) {
    if (!checkInputs(si, ['materialCostBaseline','materialCostCurrent']))
      return insufficientData('Material_Cost_Variance');
    var pct = si.actualPctComplete != null ? si.actualPctComplete / 100 : null;
    var expected = pct != null ? si.materialCostBaseline * pct : si.materialCostBaseline;
    var variance = expected > 0 ? (si.materialCostCurrent - expected) / expected : 0;
    variance = Math.round(variance * 1000) / 1000;
    var isDerived = si.sources && si.sources['materialCostBaseline'] &&
                    si.sources['materialCostBaseline'].docType === 'derived';
    var status = Math.abs(variance) <= 0.05 ? 'Green' :
                 Math.abs(variance) <= 0.12 ? 'Yellow' :
                 Math.abs(variance) <= 0.20 ? 'Amber' : 'Red';
    return {
      method_class: 'Material_Cost_Variance', status_color: status,
      variance_pct: Math.round(variance * 100),
      evidence_metric: 'Material cost variance: ' + (variance >= 0 ? '+' : '') +
        Math.round(variance * 100) + '% vs expected at current progress' +
        (isDerived ? ' — estimated (40% of BAC/AC), upload Cost Report for precise figures' : '')
    };
  }

  // Cat 3.6 — Overhead Absorption Rate (derived indirect plan vs actual)
  function runOverheadAbsorption(si) {
    if (!checkInputs(si, ['indirectCostPlan','indirectCostActual']))
      return insufficientData('Overhead_Absorption');
    var pct = si.actualPctComplete != null ? si.actualPctComplete / 100 : null;
    var planned = pct != null ? si.indirectCostPlan * pct : si.indirectCostPlan;
    var absorption = planned > 0 ? si.indirectCostActual / planned : 1;
    absorption = Math.round(absorption * 1000) / 1000;
    var isDerived = si.sources && si.sources['indirectCostPlan'] &&
                    si.sources['indirectCostPlan'].docType === 'derived';
    var status = absorption <= 1.05 ? 'Green' :
                 absorption <= 1.15 ? 'Yellow' :
                 absorption <= 1.30 ? 'Amber' : 'Red';
    return {
      method_class: 'Overhead_Absorption', status_color: status,
      absorption_ratio: absorption,
      evidence_metric: 'Overhead absorption: ' + Math.round(absorption * 100) +
        '% of planned indirect cost at current progress' +
        (isDerived ? ' — estimated (12% overhead), upload Cost Report for precise figures' : '')
    };
  }

  // Cat 3.10 — Inflation Adjustment Index (material escalation proxy)
  function runInflationAdjustment(si) {
    if (!checkInputs(si, ['materialCostBaseline','materialCostCurrent']))
      return insufficientData('Inflation_Adjustment');
    var pct = si.actualPctComplete != null ? si.actualPctComplete / 100 : null;
    var expected = pct != null ? si.materialCostBaseline * pct : si.materialCostBaseline;
    var escalation = expected > 0 ? Math.max(0, (si.materialCostCurrent - expected) / expected) : 0;
    escalation = Math.round(escalation * 1000) / 1000;
    var isDerived = si.sources && si.sources['materialCostBaseline'] &&
                    si.sources['materialCostBaseline'].docType === 'derived';
    var status = escalation <= 0.04 ? 'Green' :
                 escalation <= 0.08 ? 'Yellow' :
                 escalation <= 0.15 ? 'Amber' : 'Red';
    return {
      method_class: 'Inflation_Adjustment', status_color: status,
      escalation_pct: Math.round(escalation * 100),
      evidence_metric: 'Material escalation proxy: +' + Math.round(escalation * 100) +
        '% above progress-adjusted baseline' +
        (isDerived ? ' — estimated, upload Cost Report / price index for precise figures' : '')
    };
  }

  /* ===========================================================
     Cat 10 — Data Integrity & Information Quality
     ---------------------------------------------------------
     Quantifies the QUALITY of the inputs the other 100 modules
     consume. Every signal is only as good as its source data, so
     these modules surface the confidence the governance layer
     should place in the rest of the stack.
     =========================================================== */

  // Cat 10.1 — Missing Data Index
  function runMissingDataIndex(si) {
    var coreFields = ['bac','ev','ac','pv','cpi','spi','docRiskScore',
                      'actualPctComplete','plannedPctComplete',
                      'baselineStart','baselineEnd'];
    var present = coreFields.filter(function (f) {
      return si[f] !== null && si[f] !== undefined;
    }).length;
    var missingRatio = 1 - (present / coreFields.length);
    var missingCount = coreFields.length - present;
    var status = missingRatio <= 0.10 ? 'Green' :
                 missingRatio <= 0.25 ? 'Yellow' :
                 missingRatio <= 0.45 ? 'Amber' : 'Red';
    return {
      method_class: 'Missing_Data_Index', status_color: status,
      missing_count: missingCount, total_fields: coreFields.length,
      completeness_pct: Math.round((1 - missingRatio) * 100),
      evidence_metric: missingCount + ' of ' + coreFields.length +
        ' core fields missing (' + Math.round((1 - missingRatio) * 100) + '% complete)'
    };
  }

  // Cat 10.2 — Data Timeliness Score
  function runDataTimeliness(si) {
    if (!si.docDate) return insufficientData('Data_Timeliness_Score');
    var docDate = new Date(si.docDate);
    var now = new Date();
    var daysSinceDoc = Math.floor((now - docDate) / 86400000);
    var status = daysSinceDoc <= 30 ? 'Green' :
                 daysSinceDoc <= 60 ? 'Yellow' :
                 daysSinceDoc <= 90 ? 'Amber' : 'Red';
    return {
      method_class: 'Data_Timeliness_Score', status_color: status,
      days_since_last_doc: daysSinceDoc,
      last_doc_date: si.docDate,
      evidence_metric: 'Last document: ' + si.docDate +
        ' (' + daysSinceDoc + ' days ago' +
        (daysSinceDoc > 60 ? ' — data may be stale' : '') + ')'
    };
  }

  // Cat 10.3 — Source Reliability Weighting
  function runSourceReliability(si) {
    if (!si.sources || Object.keys(si.sources).length === 0)
      return insufficientData('Source_Reliability_Weighting');
    var sourceWeights = {
      'pay_application': 0.90, 'contract_value': 0.95,
      'schedule_of_values': 0.85, 'time_phased_schedule': 0.80,
      'monthly_report': 0.75, 'change_order': 0.90,
      'rfi': 0.65, 'submittal': 0.65, 'field_report': 0.60,
      'oac_minutes': 0.55, 'inspection_report': 0.70,
      'derived': 0.40
    };
    var weights = [];
    Object.keys(si.sources).forEach(function (key) {
      var src = si.sources[key];
      var docType = Array.isArray(src) ? src[src.length - 1].docType : src.docType;
      if (docType) weights.push(sourceWeights[docType] || 0.50);
    });
    if (!weights.length) return insufficientData('Source_Reliability_Weighting');
    var avgReliability = weights.reduce(function (a, b) { return a + b; }, 0) / weights.length;
    avgReliability = Math.round(avgReliability * 100) / 100;
    var derivedCount = Object.keys(si.sources).filter(function (k) {
      var src = si.sources[k];
      var dt = Array.isArray(src) ? src[src.length - 1].docType : src.docType;
      return dt === 'derived';
    }).length;
    var status = avgReliability >= 0.80 ? 'Green' :
                 avgReliability >= 0.65 ? 'Yellow' :
                 avgReliability >= 0.50 ? 'Amber' : 'Red';
    return {
      method_class: 'Source_Reliability_Weighting', status_color: status,
      avg_reliability: avgReliability,
      derived_fields: derivedCount,
      total_sources: weights.length,
      evidence_metric: 'Avg source reliability: ' + Math.round(avgReliability * 100) + '%' +
        (derivedCount > 0 ? ' (' + derivedCount + ' estimated fields)' : ' — all measured')
    };
  }

  // Cat 10.4 — Audit Trail Completeness
  function runAuditTrailCompleteness(si, project) {
    var events = (project && project.events) ? project.events : [];
    var requiredEvents = ['project_created', 'signals_extracted'];
    var presentEvents = requiredEvents.filter(function (e) {
      return events.some(function (ev) {
        // Recognise the live "simulation_run" event as evidence of extraction.
        if (e === 'signals_extracted' && ev.event === 'simulation_run') return true;
        return ev.event === e;
      });
    });
    var completeness = presentEvents.length / requiredEvents.length;
    var totalEvents = events.length;
    var hasDecisionRecord = events.some(function (e) { return e.event === 'decision_recorded'; });
    var status = completeness >= 1.0 && totalEvents >= 3 ? 'Green' :
                 completeness >= 0.75 ? 'Yellow' :
                 completeness >= 0.50 ? 'Amber' : 'Red';
    return {
      method_class: 'Audit_Trail_Completeness', status_color: status,
      completeness_pct: Math.round(completeness * 100),
      total_events: totalEvents,
      has_decision_record: hasDecisionRecord,
      evidence_metric: Math.round(completeness * 100) + '% audit trail completeness — ' +
        totalEvents + ' events recorded' +
        (hasDecisionRecord ? ', decision record present' : ', no decision record yet')
    };
  }

  // Cat 10.5 — Information Completeness Ratio
  function runInfoCompletenessRatio(si) {
    var allFields = ['bac','ev','ac','pv','cpi','spi','docRiskScore',
                     'actualPctComplete','plannedPctComplete',
                     'baselineStart','baselineEnd','workPeriodFrom','workPeriodTo',
                     'totalFloat','consumedFloat','originalContingency',
                     'rfiCount','changeOrderCount','subcontractorComplianceScore'];
    var measured = allFields.filter(function (f) {
      if (si[f] === null || si[f] === undefined) return false;
      var src = si.sources && si.sources[f];
      if (!src) return true;
      var dt = Array.isArray(src) ? src[src.length - 1].docType : src.docType;
      return dt !== 'derived';
    }).length;
    var estimated = allFields.filter(function (f) {
      if (si[f] === null || si[f] === undefined) return false;
      var src = si.sources && si.sources[f];
      if (!src) return false;
      var dt = Array.isArray(src) ? src[src.length - 1].docType : src.docType;
      return dt === 'derived';
    }).length;
    var missing = allFields.length - measured - estimated;
    var ratio = measured / allFields.length;
    var status = ratio >= 0.75 ? 'Green' :
                 ratio >= 0.55 ? 'Yellow' :
                 ratio >= 0.35 ? 'Amber' : 'Red';
    return {
      method_class: 'Information_Completeness_Ratio', status_color: status,
      measured: measured, estimated: estimated, missing: missing,
      total: allFields.length,
      completeness_ratio: Math.round(ratio * 100),
      evidence_metric: measured + ' measured + ' + estimated + ' estimated + ' +
        missing + ' missing of ' + allFields.length + ' fields (' +
        Math.round(ratio * 100) + '% from documents)'
    };
  }

  // Cat 10.6 — Cross-document Consistency Score
  function runCrossDocConsistency(si) {
    if (!checkInputs(si, ['ev','ac'])) return insufficientData('Cross_Doc_Consistency');
    var inconsistencies = 0;
    var checks = 0;
    // CPI derivation check
    if (si.cpi !== null && si.cpi !== undefined && si.ev !== null && si.ac !== null && si.ac !== 0) {
      var derivedCPI = Math.round((si.ev / si.ac) * 1000) / 1000;
      if (Math.abs(derivedCPI - si.cpi) > 0.005) inconsistencies++;
      checks++;
    }
    // SPI derivation check
    if (si.spi !== null && si.spi !== undefined && si.ev !== null && si.pv !== null && si.pv !== 0) {
      var derivedSPI = Math.round((si.ev / si.pv) * 1000) / 1000;
      if (Math.abs(derivedSPI - si.spi) > 0.005) inconsistencies++;
      checks++;
    }
    // % complete consistency
    if (si.actualPctComplete !== null && si.actualPctComplete !== undefined &&
        si.ev !== null && si.bac !== null && si.bac !== 0) {
      var derivedPct = Math.round((si.ev / si.bac) * 1000) / 10;
      if (Math.abs(derivedPct - si.actualPctComplete) > 5) inconsistencies++;
      checks++;
    }
    if (checks === 0) return insufficientData('Cross_Doc_Consistency');
    var consistencyScore = (checks - inconsistencies) / checks;
    var status = consistencyScore >= 1.0 ? 'Green' :
                 consistencyScore >= 0.67 ? 'Yellow' :
                 consistencyScore >= 0.33 ? 'Amber' : 'Red';
    return {
      method_class: 'Cross_Doc_Consistency', status_color: status,
      consistency_score: Math.round(consistencyScore * 100),
      inconsistencies: inconsistencies, checks_performed: checks,
      evidence_metric: (checks - inconsistencies) + ' of ' + checks +
        ' cross-document checks consistent (' +
        Math.round(consistencyScore * 100) + '%)' +
        (inconsistencies > 0 ? ' — verify figures across uploaded documents' : '')
    };
  }

  // Cat 10.7 — Reporting Frequency Index
  function runReportingFrequency(si, project) {
    var events = (project && project.events) ? project.events : [];
    // simulation_run is the canonical extraction-tracked event today; if
    // dedicated 'signals_extracted' events appear later they fold in cleanly.
    var extractEvents = events.filter(function (e) {
      return e.event === 'signals_extracted' || e.event === 'simulation_run';
    });
    if (extractEvents.length < 2) {
      return {
        method_class: 'Reporting_Frequency_Index', status_color: 'Yellow',
        uploads: extractEvents.length, expected_per_month: 4,
        evidence_metric: extractEvents.length + ' document upload(s) recorded — ' +
          (extractEvents.length === 0 ? 'no documents uploaded yet' : 'upload more documents for frequency analysis')
      };
    }
    var dates = extractEvents.map(function (e) { return new Date(e.at); }).sort(function (a, b) { return a - b; });
    var intervals = [];
    for (var i = 1; i < dates.length; i++) {
      intervals.push((dates[i] - dates[i - 1]) / 86400000);
    }
    var avgInterval = intervals.reduce(function (a, b) { return a + b; }, 0) / intervals.length;
    var status = avgInterval <= 14 ? 'Green' :
                 avgInterval <= 30 ? 'Yellow' :
                 avgInterval <= 60 ? 'Amber' : 'Red';
    return {
      method_class: 'Reporting_Frequency_Index', status_color: status,
      avg_interval_days: Math.round(avgInterval),
      uploads: extractEvents.length,
      evidence_metric: Math.round(avgInterval) + ' day avg interval between document uploads — ' +
        (avgInterval <= 14 ? 'high frequency reporting' :
         avgInterval <= 30 ? 'monthly reporting cycle' :
         avgInterval <= 60 ? 'infrequent updates' : 'reporting gap — data may be stale')
    };
  }

  /* ===========================================================
     Cat 11 — Decision Optimization
     ---------------------------------------------------------
     Cat 5 explains how the system behaves; Cat 11 selects the
     best action under constraints. Multi-objective, LP, regret-
     minimization etc — answer the PM's "what should I do?".
     =========================================================== */

  // Cat 11.1 — Multi-Objective Optimization
  function runMultiObjectiveOptimization(si) {
    if (!checkInputs(si, ['cpi','spi','docRiskScore']))
      return insufficientData('Multi_Objective_Optimization');
    var normCPI = Math.min(1, Math.max(0, (si.cpi - 0.80) / 0.25));
    var normSPI = Math.min(1, Math.max(0, (si.spi - 0.80) / 0.25));
    var normRisk = 1 - (si.docRiskScore || 0);
    var paretoScore = Math.round(((normCPI + normSPI + normRisk) / 3) * 100) / 100;
    var objectives = [
      { name: 'Cost performance', score: normCPI },
      { name: 'Schedule performance', score: normSPI },
      { name: 'Document risk', score: normRisk }
    ].sort(function (a, b) { return a.score - b.score; });
    var bindingConstraint = objectives[0];
    var status = paretoScore >= 0.75 ? 'Green' :
                 paretoScore >= 0.55 ? 'Yellow' :
                 paretoScore >= 0.35 ? 'Amber' : 'Red';
    return {
      method_class: 'Multi_Objective_Optimization', status_color: status,
      pareto_score: paretoScore,
      binding_constraint: bindingConstraint.name,
      objectives: objectives,
      evidence_metric: 'Multi-objective score: ' + Math.round(paretoScore * 100) + '% — ' +
        'binding constraint: ' + bindingConstraint.name +
        ' (score ' + Math.round(bindingConstraint.score * 100) + '%)'
    };
  }

  // Cat 11.2 — Linear Programming
  function runLinearProgramming(si) {
    if (!checkInputs(si, ['bac','ev','ac','cpi']))
      return insufficientData('Linear_Programming');
    var remainingWork = si.bac - si.ev;
    var remainingBudget = si.bac - si.ac;
    if (remainingBudget <= 0) return {
      method_class: 'Linear_Programming', status_color: 'Red',
      feasible: false,
      evidence_metric: 'No feasible solution — budget exhausted before project completion'
    };
    var requiredCPI = remainingWork / remainingBudget;
    var lpFeasible = requiredCPI <= 1.20;
    var lpOptimal = requiredCPI <= 1.00;
    var lpScore = lpFeasible ? Math.min(1, 1.0 / requiredCPI) : 0;
    var status = lpOptimal ? 'Green' :
                 requiredCPI <= 1.05 ? 'Yellow' :
                 requiredCPI <= 1.15 ? 'Amber' : 'Red';
    return {
      method_class: 'Linear_Programming', status_color: status,
      required_cpi_to_complete: Math.round(requiredCPI * 1000) / 1000,
      feasible: lpFeasible,
      optimal: lpOptimal,
      lp_score: Math.round(lpScore * 100) / 100,
      evidence_metric: 'LP: requires CPI ' + (Math.round(requiredCPI * 1000) / 1000) +
        ' to complete within budget — ' +
        (lpOptimal ? 'achievable at current performance' :
         lpFeasible ? 'requires productivity improvement' : 'budget infeasible — recovery plan needed')
    };
  }

  // Cat 11.3 — Constraint Satisfaction Analysis
  function runConstraintSatisfaction(si) {
    if (!checkInputs(si, ['cpi','spi','bac']))
      return insufficientData('Constraint_Satisfaction');
    var constraints = [
      { name: 'Cost constraint (CPI ≥ 0.90)', satisfied: si.cpi >= 0.90, value: si.cpi, threshold: 0.90 },
      { name: 'Schedule constraint (SPI ≥ 0.90)', satisfied: si.spi >= 0.90, value: si.spi, threshold: 0.90 },
      { name: 'Document risk (score < 0.70)', satisfied: (si.docRiskScore || 0) < 0.70, value: si.docRiskScore || 0, threshold: 0.70 },
      { name: 'FAR threshold (overrun < 25%)', satisfied: si.cpi > 0.80, value: si.cpi, threshold: 0.80 }
    ];
    var satisfied = constraints.filter(function (c) { return c.satisfied; }).length;
    var violated = constraints.filter(function (c) { return !c.satisfied; });
    var satisfactionRate = satisfied / constraints.length;
    var status = satisfactionRate >= 1.0 ? 'Green' :
                 satisfactionRate >= 0.75 ? 'Yellow' :
                 satisfactionRate >= 0.50 ? 'Amber' : 'Red';
    return {
      method_class: 'Constraint_Satisfaction', status_color: status,
      satisfied: satisfied, total: constraints.length,
      violated_constraints: violated.map(function (c) { return c.name; }),
      satisfaction_rate: Math.round(satisfactionRate * 100),
      evidence_metric: satisfied + ' of ' + constraints.length + ' constraints satisfied' +
        (violated.length > 0 ? ' — violated: ' + violated.map(function (c) { return c.name; }).join(', ') : ' — all constraints met')
    };
  }

  // Cat 11.4 — What-If Scenario Matrix
  function runWhatIfMatrix(si) {
    if (!checkInputs(si, ['bac','ev','ac','cpi','spi']))
      return insufficientData('WhatIf_Scenario_Matrix');
    var remaining = si.bac - si.ev;
    var scenarios = [
      { name: 'Optimistic (CPI recovers to 1.0)', eac: si.ac + remaining * 1.00, cpi: 1.00 },
      { name: 'Base (current CPI continues)', eac: si.bac / si.cpi, cpi: si.cpi },
      { name: 'Pessimistic (CPI degrades 5%)', eac: si.bac / (si.cpi * 0.95), cpi: si.cpi * 0.95 },
      { name: 'Recovery (CPI improves 5%)', eac: si.bac / (si.cpi * 1.05), cpi: si.cpi * 1.05 }
    ];
    var baseEAC = scenarios[1].eac;
    var range = scenarios[2].eac - scenarios[0].eac;
    var rangePct = Math.round((range / si.bac) * 100);
    var status = rangePct <= 5 ? 'Green' :
                 rangePct <= 10 ? 'Yellow' :
                 rangePct <= 20 ? 'Amber' : 'Red';
    return {
      method_class: 'WhatIf_Scenario_Matrix', status_color: status,
      scenarios: scenarios.map(function (s) {
        return {
          name: s.name, eac: Math.round(s.eac),
          delta_pct: Math.round(((s.eac - si.bac) / si.bac) * 100 * 10) / 10
        };
      }),
      scenario_range_pct: rangePct,
      base_eac: Math.round(baseEAC),
      evidence_metric: 'Scenario range: ' + rangePct + '% of BAC — ' +
        'base EAC $' + Math.round(baseEAC / 1000) + 'k, ' +
        'worst $' + Math.round(scenarios[2].eac / 1000) + 'k, ' +
        'best $' + Math.round(scenarios[0].eac / 1000) + 'k'
    };
  }

  // Cat 11.5 — Decision Sensitivity Matrix
  function runDecisionSensitivity(si) {
    if (!checkInputs(si, ['cpi','spi','docRiskScore']))
      return insufficientData('Decision_Sensitivity_Matrix');
    var cpiImpact = Math.abs(1 - si.cpi) * 100;
    var spiImpact = Math.abs(1 - si.spi) * 100;
    var riskImpact = (si.docRiskScore || 0) * 50;
    var total = cpiImpact + spiImpact + riskImpact || 1;
    var sensitivity = [
      { driver: 'Cost performance (CPI)', impact: cpiImpact, pct: Math.round(cpiImpact / total * 100) },
      { driver: 'Schedule performance (SPI)', impact: spiImpact, pct: Math.round(spiImpact / total * 100) },
      { driver: 'Document risk', impact: riskImpact, pct: Math.round(riskImpact / total * 100) }
    ].sort(function (a, b) { return b.impact - a.impact; });
    var topDriver = sensitivity[0];
    var maxImpact = topDriver.impact;
    var status = maxImpact <= 3 ? 'Green' :
                 maxImpact <= 7 ? 'Yellow' :
                 maxImpact <= 12 ? 'Amber' : 'Red';
    return {
      method_class: 'Decision_Sensitivity_Matrix', status_color: status,
      top_driver: topDriver.driver,
      top_driver_pct: topDriver.pct,
      sensitivity_matrix: sensitivity,
      evidence_metric: 'Decision most sensitive to: ' + topDriver.driver +
        ' (' + topDriver.pct + '% of decision weight) — ' +
        'a small change here most changes the governance recommendation'
    };
  }

  // Cat 11.6 — Pareto Frontier Analysis
  function runParetoFrontier(si) {
    if (!checkInputs(si, ['cpi','spi','docRiskScore']))
      return insufficientData('Pareto_Frontier');
    var costOk = si.cpi >= 0.95;
    var schedOk = si.spi >= 0.95;
    var riskOk = (si.docRiskScore || 0) < 0.30;
    var dominated = !costOk && !schedOk;
    var paretoEfficient = costOk && schedOk && riskOk;
    var tradeoffRequired = (costOk !== schedOk) || (!riskOk && (costOk || schedOk));
    var paretoScore = ((costOk ? 1 : si.cpi / 0.95) +
                       (schedOk ? 1 : si.spi / 0.95) +
                       (riskOk ? 1 : (1 - (si.docRiskScore || 0) / 0.30))) / 3;
    paretoScore = Math.round(Math.min(1, paretoScore) * 100) / 100;
    var status = paretoEfficient ? 'Green' :
                 tradeoffRequired ? 'Yellow' :
                 !dominated ? 'Amber' : 'Red';
    return {
      method_class: 'Pareto_Frontier', status_color: status,
      pareto_efficient: paretoEfficient,
      dominated: dominated,
      tradeoff_required: tradeoffRequired,
      pareto_score: paretoScore,
      evidence_metric: paretoEfficient ? 'Project is Pareto-efficient — all objectives met simultaneously' :
        dominated ? 'Project is Pareto-dominated — multiple objectives failing simultaneously' :
        tradeoffRequired ? 'Trade-off required — improving one objective may affect another' :
        'Partial Pareto efficiency — some objectives met'
    };
  }

  // Cat 11.7 — Regret Minimization Index
  function runRegretMinimization(si) {
    if (!checkInputs(si, ['cpi','spi','bac']))
      return insufficientData('Regret_Minimization');
    var futureStates = { improves: 0.3, stable: 0.4, worsens: 0.3 };
    var regretMatrix = {
      monitor:     { improves: 0,  stable: 5, worsens: 30 },
      investigate: { improves: 5,  stable: 0, worsens: 10 },
      escalate:    { improves: 15, stable: 8, worsens: 0 }
    };
    var expectedRegret = {};
    Object.keys(regretMatrix).forEach(function (decision) {
      var regrets = regretMatrix[decision];
      expectedRegret[decision] = Math.round(
        regrets.improves * futureStates.improves +
        regrets.stable * futureStates.stable +
        regrets.worsens * futureStates.worsens
      );
    });
    var minRegret = Math.min.apply(null, Object.keys(expectedRegret).map(function (k) { return expectedRegret[k]; }));
    var recommended = Object.keys(expectedRegret).filter(function (d) {
      return expectedRegret[d] === minRegret;
    })[0];
    // Signal-state override: the regret matrix says monitor by default, but the
    // governance layer must escalate when CPI/SPI breach the FAR thresholds.
    if (si.cpi < 0.88 || si.spi < 0.88) recommended = 'escalate';
    else if (si.cpi < 0.95 || si.spi < 0.95) recommended = 'investigate';
    var status = recommended === 'monitor' ? 'Green' :
                 recommended === 'investigate' ? 'Amber' : 'Red';
    return {
      method_class: 'Regret_Minimization', status_color: status,
      recommended_action: recommended,
      expected_regret: expectedRegret,
      min_regret_score: minRegret,
      evidence_metric: 'Minimax regret recommends: ' + recommended +
        ' (expected regret score ' + minRegret + '/30) — ' +
        'this decision minimizes worst-case outcome under uncertain future states'
    };
  }

  /* ===========================================================
     Cat 12 — Systems Engineering (conditional)
     ---------------------------------------------------------
     Activates when interface control / requirements / system
     architecture documents are uploaded. Until then the modules
     return a null-status conditional stub so the spider web
     renders them as a grey band and the ensemble panel excludes
     them from the active count.
     =========================================================== */

  function conditionalSE(methodClass, msg) {
    return {
      method_class: methodClass, status_color: null, conditional: true,
      evidence_metric: msg
    };
  }

  function runInterfaceDensity(si) {
    if (si.interfaceCount === null || si.interfaceCount === undefined)
      return conditionalSE('Interface_Density',
        'Requires interface control documents — upload ICD or system architecture docs to activate');
    var density = si.interfaceCount / Math.max(1, si.totalComponents || 10);
    var status = density <= 0.3 ? 'Green' :
                 density <= 0.6 ? 'Yellow' :
                 density <= 1.0 ? 'Amber' : 'Red';
    return {
      method_class: 'Interface_Density', status_color: status,
      density: Math.round(density * 100) / 100,
      evidence_metric: 'Interface density: ' + (Math.round(density * 100) / 100) + ' interfaces per component'
    };
  }

  function runDependencyMapping(si) {
    return conditionalSE('Dependency_Mapping',
      'Requires dependency mapping document — upload system architecture to activate');
  }

  function runRequirementsTraceability(si) {
    return conditionalSE('Requirements_Traceability',
      'Requires requirements specification — upload requirements document to activate');
  }

  function runConfigChangeImpact(si) {
    if (si.changeOrderCount !== null && si.changeOrderCount !== undefined && si.changeOrderCount > 0) {
      var impact = Math.min(1, si.changeOrderCount / 10);
      var status = impact <= 0.2 ? 'Green' :
                   impact <= 0.5 ? 'Yellow' :
                   impact <= 0.8 ? 'Amber' : 'Red';
      return {
        method_class: 'Config_Change_Impact', status_color: status,
        change_order_count: si.changeOrderCount,
        impact_score: Math.round(impact * 100) / 100,
        evidence_metric: si.changeOrderCount + ' change orders — configuration impact score ' +
          Math.round(impact * 100) + '%'
      };
    }
    return conditionalSE('Config_Change_Impact',
      'Requires configuration items document — partially derivable from change orders');
  }

  function runIntegrationComplexity(si) {
    return conditionalSE('Integration_Complexity',
      'Requires interface and dependency documents to activate');
  }

  /* ===========================================================
     runAll — runs the original 13 client-side models PLUS every
     new active Stage-2 module. DST (Module 10) still runs
     separately in signals.js after the core package is assembled.
     Conservative Dominance and ABM Governance live in the main
     signal pipeline / decision.js — they consume signals.

     Modules that lack their required inputs return an
     insufficient_data stub; those are filtered out here so the
     spider / ensemble only count modules that actually computed.
     Cat 12 conditional modules return status_color:null and are
     kept in the array (passed through the filter) so the spider
     web can render them as a greyed-out conditional band.
     =========================================================== */
  function runAll(input, existingSignals, project) {
    var si = (input && input.signalInputs) ? input.signalInputs : (input || {});
    var es = existingSignals || {};

    // Each model is a thunk so a single runner throwing on a malformed input
    // can't abort the whole batch (which previously left simulationSignals empty
    // and every non-core module reading "No data"). One failure is skipped; the
    // rest still compute.
    var runners = [
      // Original 13 client-side models (always present when signals exist).
      function () { return runPERT(si); },                  // Cat 2.1
      function () { return runLOB(si); },                   // Cat 2.2
      function () { return runCCPM(si); },                  // Cat 2.3
      function () { return runRCF(si); },                   // Cat 3.1
      function () { return runDSM(si); },                   // Cat 3.2 (+ aliased to Cat 5.1)
      function () { return runRoughSets(es); },             // Cat 7.2
      function () { return runNeutrosophic(es); },          // Cat 7.3
      function () { return runIntervalFuzzy(es); },         // Cat 7.4
      function () { return runZNumbers(es); },              // Cat 7.5
      function () { return runPLTS(es); },                  // Cat 7.6
      function () { return runPlithogenic(es); },           // Cat 7.7
      function () { return runBRB(es); },                   // Cat 7.8
      function () { return runQuantumProbability(es); },    // Cat 7.9

      // Cat 1 EVM extensions
      function () { return runBayesianEAC(si); }, function () { return runKalmanFilter(si); },
      function () { return runARIMAForecast(si); }, function () { return runEarnedSchedule(si); },
      function () { return runTCPI(si); }, function () { return runVAC(si); },
      function () { return runBudgetExecutionRate(si); }, function () { return runRegressionToMean(si); },
      function () { return runICERatio(si); },

      // Cat 2 schedule extensions
      function () { return runScheduleCompression(si); }, function () { return runFloatConsumption(si); },
      function () { return runSCurveDeviation(si); }, function () { return runScheduleRiskAnalysis(si); },
      function () { return runCriticalPathIndex(si); },

      // Cat 2 extension (derived)
      function () { return runLookaheadHealth(si); },

      // Cat 3 cost extensions
      function () { return runContingencyBurnRate(si); }, function () { return runCostRiskAnalysis(si); },
      function () { return runParametricCost(si); },
      function () { return runMaterialCostVariance(si); }, function () { return runOverheadAbsorption(si); },
      function () { return runInflationAdjustment(si); },

      // Cat 4 doc / risk extensions
      function () { return runRFIVelocity(si); }, function () { return runSubmittalRejection(si); },
      function () { return runCOFrequency(si); }, function () { return runDisputeEscalation(si); },
      function () { return runSpecConflictDensity(si); },
      function () { return runWeatherImpact(si); }, function () { return runSubcontractorPerformance(si); },

      // Cat 5 dynamics extensions
      function () { return runSensitivityAnalysis(si); }, function () { return runTornadoDiagram(si); },
      function () { return runScenarioModeling(si); }, function () { return runReworkFeedback(si); },
      function () { return runDiscreteEventSim(si); },

      // Cat 6 synthesis extensions (consume the assembled project)
      function () { return runWeightedVoting(project); }, function () { return runMajorityRules(project); },
      function () { return runWorstNofM(project); },

      // Cat 7 evidence extensions
      function () { return runPythagoreanFuzzy(si); }, function () { return runPictureFuzzy(si); },
      function () { return runHesitantFuzzy(si); }, function () { return runType2Fuzzy(si); },
      function () { return runMaximumEntropy(si); }, function () { return runPossibilityTheory(si); },
      function () { return runSphericalFuzzy(si); }, function () { return runFermateanFuzzy(si); },
      function () { return runMARCOS(si); }, function () { return runCRITIC_TOPSIS(si); },
      function () { return runHypersoftSets(si); },

      // Cat 9 governance extensions
      function () { return runFARThreshold(si); }, function () { return runOMBA11Check(si); },
      function () { return runEVMReportingThreshold(si); }, function () { return runContractModFrequency(si); },
      function () { return runQualityCompliance(si); }, function () { return runSafetyPerformance(si); },
      function () { return runEnvironmentalCompliance(si); },

      // Cat 10 — Data Integrity (project arg needed for audit-trail / frequency)
      function () { return runMissingDataIndex(si); },
      function () { return runDataTimeliness(si); },
      function () { return runSourceReliability(si); },
      function () { return runAuditTrailCompleteness(si, project); },
      function () { return runInfoCompletenessRatio(si); },
      function () { return runCrossDocConsistency(si); },
      function () { return runReportingFrequency(si, project); },

      // Cat 11 — Decision Optimization
      function () { return runMultiObjectiveOptimization(si); },
      function () { return runLinearProgramming(si); },
      function () { return runConstraintSatisfaction(si); },
      function () { return runWhatIfMatrix(si); },
      function () { return runDecisionSensitivity(si); },
      function () { return runParetoFrontier(si); },
      function () { return runRegretMinimization(si); },

      // Cat 12 — Systems Engineering (conditional). These return either a
      // computed status or a conditional stub (status_color === null with
      // conditional:true) that survives the filter below so the spider can
      // render a "needs more docs" band.
      function () { return runInterfaceDensity(si); },
      function () { return runDependencyMapping(si); },
      function () { return runRequirementsTraceability(si); },
      function () { return runConfigChangeImpact(si); },
      function () { return runIntegrationComplexity(si); }
    ];

    var results = [];
    for (var i = 0; i < runners.length; i++) {
      try {
        var r = runners[i]();
        if (r) results.push(r);
      } catch (e) { /* one model failing must not void the batch */ }
    }

    return results.filter(function (r) {
      if (!r) return false;
      if (r.insufficient_data) return false;
      // Cat 12 conditional stubs are kept (status_color === null + conditional)
      // so consumers can render them as a distinct grey band.
      if (r.status_color === null && !r.conditional) return false;
      return true;
    });
  }

  window.LinSimulations = {
    runAll,
    checkInputs, insufficientData,
    runPERT, runLOB, runCCPM, runRCF, runDSM,
    runDST, runRoughSets, runNeutrosophic, runIntervalFuzzy,
    runZNumbers, runPLTS, runPlithogenic, runBRB, runQuantumProbability,
    // Stage-2 modules (full 108-module rollout)
    runBayesianEAC, runKalmanFilter, runARIMAForecast, runEarnedSchedule,
    runTCPI, runVAC, runBudgetExecutionRate, runRegressionToMean, runICERatio,
    runScheduleCompression, runFloatConsumption, runSCurveDeviation,
    runScheduleRiskAnalysis, runCriticalPathIndex,
    runContingencyBurnRate, runCostRiskAnalysis, runParametricCost,
    runRFIVelocity, runSubmittalRejection, runCOFrequency,
    runDisputeEscalation, runSpecConflictDensity,
    runSensitivityAnalysis, runTornadoDiagram, runScenarioModeling,
    runReworkFeedback, runDiscreteEventSim,
    runWeightedVoting, runMajorityRules, runWorstNofM,
    runPythagoreanFuzzy, runPictureFuzzy, runHesitantFuzzy, runType2Fuzzy,
    runMaximumEntropy, runPossibilityTheory, runSphericalFuzzy,
    runFermateanFuzzy, runMARCOS, runCRITIC_TOPSIS, runHypersoftSets,
    runFARThreshold, runOMBA11Check, runEVMReportingThreshold, runContractModFrequency,
    // Derived-field modules (Code.gs v10.18)
    runLookaheadHealth, runWeatherImpact, runQualityCompliance, runSafetyPerformance,
    runEnvironmentalCompliance, runSubcontractorPerformance,
    runMaterialCostVariance, runOverheadAbsorption, runInflationAdjustment,
    // Cat 10 — Data Integrity & Information Quality
    runMissingDataIndex, runDataTimeliness, runSourceReliability,
    runAuditTrailCompleteness, runInfoCompletenessRatio,
    runCrossDocConsistency, runReportingFrequency,
    // Cat 11 — Decision Optimization
    runMultiObjectiveOptimization, runLinearProgramming, runConstraintSatisfaction,
    runWhatIfMatrix, runDecisionSensitivity, runParetoFrontier, runRegretMinimization,
    // Cat 12 — Systems Engineering (conditional)
    runInterfaceDensity, runDependencyMapping, runRequirementsTraceability,
    runConfigChangeImpact, runIntegrationComplexity,
    sampleTriangular
  };
})();
