/* ============================================================
   lin-project-radar — sim.js  (Phase 1)
   ------------------------------------------------------------
   REAL client-side computations (pure, no DOM, no network):
     • monteCarloEAC()  — genuine Monte Carlo over a Beta-PERT
       distribution derived from a project's EVM + risk signals.
       N iterations is a real loop; P50/P80 are read from the
       sorted simulated array.
     • cusumSeries()    — the standard two-sided tabular CUSUM
       recursion over a metric series, with a real decision
       interval H; a breach is the statistic crossing H, never a
       hardcoded boolean.
     • buildSignals()   — assembles a project's signal package
       from ingest inputs, running both computations so the
       stored statuses reflect real arithmetic.

   These are DEMONSTRATION models: the signal→spread mapping is a
   designed heuristic, not a calibrated/validated forecast.
   ============================================================ */

(function () {
  "use strict";

  const DEMO_BAC = 100; // demo Budget At Completion (units) when none supplied
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

  /* ---------- seeded RNG (mulberry32) ----------
     Seeding per project keeps the distribution reproducible across
     re-renders (documented choice); it is still a real sampled draw,
     not a drawn curve. Change the seed and the draw changes. */
  function mulberry32(seed) {
    let a = seed >>> 0;
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function hashSeed(str) {
    let h = 2166136261 >>> 0;
    for (let i = 0; i < String(str).length; i++) {
      h ^= String(str).charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return h >>> 0;
  }

  /* Standard normal via Box–Muller using the provided uniform rng. */
  function normal(rng) {
    let u = 0, v = 0;
    while (u === 0) u = rng();
    while (v === 0) v = rng();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  }

  /* Gamma(k,1) via Marsaglia–Tsang (valid for k ≥ 1; our PERT α,β ≥ 1). */
  function gamma(k, rng) {
    const d = k - 1 / 3;
    const c = 1 / Math.sqrt(9 * d);
    for (;;) {
      let x, v;
      do { x = normal(rng); v = 1 + c * x; } while (v <= 0);
      v = v * v * v;
      const u = rng();
      if (u < 1 - 0.0331 * x * x * x * x) return d * v;
      if (Math.log(u) < 0.5 * x * x + d * (1 - v + Math.log(v))) return d * v;
    }
  }
  /* Beta(α,β) = G1 / (G1 + G2). */
  function beta(alpha, betaParam, rng) {
    const g1 = gamma(alpha, rng);
    const g2 = gamma(betaParam, rng);
    return g1 / (g1 + g2);
  }

  function percentile(sortedAsc, q) {
    if (!sortedAsc.length) return NaN;
    const idx = clamp(Math.floor(q * (sortedAsc.length - 1)), 0, sortedAsc.length - 1);
    return sortedAsc[idx];
  }

  /* ---------- 5,000-iteration Monte Carlo on a signal-derived PERT ----------
     inputs: { cpi, spi, bac?, docScore, cusumBreached, cusumDrift,
               cusumThreshold, seed? } */
  function monteCarloEAC(inputs, opts) {
    const iterations = (opts && opts.iterations) || 5000;
    const cpi = Number(inputs.cpi) || 1;
    const spi = Number(inputs.spi) || 1;
    const bac = Number(inputs.bac) || DEMO_BAC;
    const docScore = clamp(Number(inputs.docScore) || 0, 0, 1);

    // Most-likely EAC = standard EVM independent estimate BAC / CPI.
    const mEAC = bac / cpi;

    // Spread driver s ∈ [0,1] — blend of risk signals. Calm → tight,
    // deteriorating → wide & pessimistically skewed. (Designed heuristic.)
    const cusumPenalty = inputs.cusumBreached
      ? 0.15
      : 0.15 * clamp((Number(inputs.cusumDrift) || 0) / (Number(inputs.cusumThreshold) || 1), 0, 1);
    const s = clamp(0.5 * (1 - cpi) + 0.3 * (1 - spi) + 0.2 * docScore + cusumPenalty, 0, 1);

    // Three-point estimate (asymmetric: cost downside dominates).
    const o = mEAC * (1 - 0.10 * s);
    const m = mEAC;
    const p = mEAC * (1 + 0.40 * s);

    const rng = mulberry32(inputs.seed != null ? (inputs.seed >>> 0) : hashSeed(`${cpi}|${spi}|${bac}|${docScore}`));
    const samples = new Array(iterations);

    if (p - o < 1e-9) {
      // Zero spread (perfectly calm) → degenerate distribution at mEAC.
      for (let i = 0; i < iterations; i++) samples[i] = mEAC;
    } else {
      // Beta-PERT shape parameters.
      const alpha = 1 + 4 * (m - o) / (p - o);
      const betaP = 1 + 4 * (p - m) / (p - o);
      for (let i = 0; i < iterations; i++) {
        samples[i] = o + beta(alpha, betaP, rng) * (p - o);
      }
    }

    const sorted = samples.slice().sort((a, b) => a - b);
    const p50 = percentile(sorted, 0.50);
    const p80 = percentile(sorted, 0.80);
    return {
      iterations, samples: sorted, p50, p80, o, m, p, s, mEAC, baseline: bac,
      overrunPctP50: (p50 / bac - 1) * 100,
      overrunPctP80: (p80 / bac - 1) * 100
    };
  }

  /* ---------- standard two-sided tabular CUSUM ----------
     series: array of metric values (e.g. periodic SPI or CPI).
     opts: { target=1.0, sigma?, hUnits=5 }  (k = 0.5σ slack, H = hUnits·σ) */
  function cusumSeries(series, opts) {
    opts = opts || {};
    const x = (series || []).map(Number).filter((v) => Number.isFinite(v));
    const target = opts.target != null ? opts.target : 1.0;
    // σ estimate from the series, with a sensible floor for short/flat series.
    let sigma = opts.sigma;
    if (sigma == null) {
      if (x.length > 1) {
        const mean = x.reduce((a, b) => a + b, 0) / x.length;
        const varr = x.reduce((a, b) => a + (b - mean) ** 2, 0) / (x.length - 1);
        sigma = Math.sqrt(varr);
      } else sigma = 0;
    }
    if (!(sigma > 0)) sigma = 0.05; // documented floor so k/H are meaningful
    const hUnits = opts.hUnits != null ? opts.hUnits : 5;
    const k = 0.5 * sigma;
    const H = hUnits * sigma;

    const sHi = [], sLo = [], stat = [];
    let hi = 0, lo = 0, breached = false, breachIndex = -1;
    for (let t = 0; t < x.length; t++) {
      hi = Math.max(0, hi + (x[t] - target) - k);
      lo = Math.max(0, lo + (target - x[t]) - k);
      sHi.push(hi); sLo.push(lo); stat.push(Math.max(hi, lo));
      if (!breached && (hi > H || lo > H)) { breached = true; breachIndex = t; }
    }
    const maxStat = stat.length ? Math.max(...stat) : 0;
    return { x, target, sigma, k, H, hUnits, sHi, sLo, stat, maxStat, breached, breachIndex };
  }

  /* ---------- status thresholds (shared, deterministic) ---------- */
  function evmStatus(cpi, spi) {
    if (cpi < 0.90 || spi < 0.85) return "red";
    if (cpi < 0.95 || spi < 0.95) return "amber";
    return "green";
  }
  function mcStatus(overrunPctP80) {
    if (overrunPctP80 >= 10) return "red";
    if (overrunPctP80 >= 5) return "amber";
    return "green";
  }
  function cusumStatus(cu) {
    if (cu.breached) return "red";
    if (cu.maxStat >= 0.6 * cu.H) return "amber";
    return "green";
  }
  function docStatus(score) {
    if (score >= 0.70) return "red";
    if (score >= 0.30) return "amber";
    return "green";
  }

  /* If no explicit metric series is supplied, derive a short deterministic
     one from the current metric value so CUSUM has real numbers to run on.
     (Documented synthesis — the CUSUM arithmetic over it is genuine.) */
  function deriveSeries(metricValue, seed) {
    const rng = mulberry32(hashSeed("series-" + seed));
    const n = 12, out = [];
    // start near target 1.0, drift linearly toward the reported metric value
    for (let t = 0; t < n; t++) {
      const frac = t / (n - 1);
      const base = 1.0 + (metricValue - 1.0) * frac;
      out.push(Math.round((base + (rng() - 0.5) * 0.02) * 1000) / 1000);
    }
    return out;
  }

  /* ---------- assemble a full signal package from ingest inputs ----------
     inputs: { cpi, spi, bac?, metric?("SPI"|"CPI"), series?,
               docScore, docSource?, docExcerpt?, seed } */
  function buildSignals(inputs) {
    const cpi = Number(inputs.cpi);
    const spi = Number(inputs.spi);
    const bac = Number(inputs.bac) || DEMO_BAC;
    const metric = inputs.metric === "CPI" ? "CPI" : "SPI";
    const metricValue = metric === "CPI" ? cpi : spi;
    const docScore = clamp(Number(inputs.docScore) || 0, 0, 1);
    const seed = inputs.seed != null ? inputs.seed : hashSeed(`${cpi}|${spi}|${bac}`);

    const series = (Array.isArray(inputs.series) && inputs.series.length >= 3)
      ? inputs.series.map(Number)
      : deriveSeries(metricValue, seed);

    const cu = cusumSeries(series, { target: 1.0, hUnits: 5 });
    const mc = monteCarloEAC({
      cpi, spi, bac, docScore,
      cusumBreached: cu.breached, cusumDrift: cu.maxStat, cusumThreshold: cu.H, seed
    }, { iterations: 5000 });

    // P(milestone delay) — heuristic from SPI + spread (demonstration only).
    const pMilestoneDelay = clamp(0.5 * (1 - spi) + 0.3 * mc.s, 0, 0.95);

    return {
      evm: {
        cpi, spi, bac, dataDate: new Date().toISOString().slice(0, 10),
        status: evmStatus(cpi, spi)
      },
      mc: {
        iterations: mc.iterations,
        p50: mc.p50, p80: mc.p80,
        p80eacOverrunPct: mc.overrunPctP80,
        p50eacOverrunPct: mc.overrunPctP50,
        pMilestoneDelay,
        status: mcStatus(mc.overrunPctP80),
        // inputs needed to re-run the real simulation live on Project Detail
        inputs: { cpi, spi, bac, docScore, cusumBreached: cu.breached, cusumDrift: cu.maxStat, cusumThreshold: cu.H, seed }
      },
      cusum: {
        metric, series, target: cu.target, sigma: cu.sigma, hUnits: cu.hUnits,
        threshold: cu.H,            // absolute decision interval (σ units × hUnits)
        drift: cu.maxStat,          // peak CUSUM statistic
        breached: cu.breached,
        breachIndex: cu.breachIndex,
        status: cusumStatus(cu)
      },
      doc: {
        score: docScore,
        status: docStatus(docScore),
        source: inputs.docSource || "(manual signal entry)",
        excerpt: inputs.docExcerpt || "No document text ingested; document-risk score entered/derived directly."
      }
    };
  }

  window.LinSim = {
    monteCarloEAC, cusumSeries, buildSignals, deriveSeries,
    evmStatus, mcStatus, cusumStatus, docStatus, hashSeed, DEMO_BAC
  };
})();
