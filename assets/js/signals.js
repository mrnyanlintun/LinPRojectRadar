/* ============================================================
   lin-project-radar — signals.js  (Piece C)
   ------------------------------------------------------------
   Document-driven signal ingestion + review. Replaces the old
   "type CPI / SPI / BAC" manual form. A PM uploads a real
   construction document; the backend (Gemini, v6) extracts the
   EVM figures and returns merged signalInputs. When both CPI and
   SPI are present (readyToRun) we feed those extracted values
   into the EXISTING Monte Carlo + CUSUM + PCEIF pipeline
   (LinSim.buildSignals) — same models, extracted inputs instead
   of typed ones. A details panel shows extracted values (with
   source tags), still-missing values, an overwrite control per
   field (governed correction + reason, logged server-side), and
   the signal audit trail.
   ============================================================ */
(function () {
  "use strict";

  // Bump when runAll()'s module set changes so projects carrying an older,
  // stale signal_array get recomputed instead of short-circuiting on a
  // non-empty-but-stale array. v2 = the full 89-module rollout; v3 added
  // Cat 10 (Data Integrity) and Cat 11 (Decision Optimization); v4 removes
  // the Cat 12 (Systems Engineering) stubs — 103 modules total; v5 upgrades
  // RFI_Velocity / Submittal_Rejection to the v10.27 RFI/RFA-log fields; v6
  // activates 9 dormant modules (8 arithmetic paths + multi-period Milestone
  // Trend) so stale arrays computed before them get rerun.
  const SIM_MODULE_SET_VERSION = 6;

  const esc = (s) => String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");

  /* ---------- document types (24+ airport taxonomy, grouped) ----------
     Financial & schedule docs carry EVM figures; risk/correspondence and
     planning/governance docs route to extractsignals too but return only a
     document_risk_score. The select renders these as <optgroup>s. */
  const DOC_TYPE_GROUPS = [
    { label: "Financial & Schedule Documents", types: [
      ["contract_value",        "Contract Value / Original Agreement"],
      ["schedule_of_values",    "Schedule of Values (G703)"],
      ["pay_application",       "Pay Application (G702)"],
      ["time_phased_schedule",  "Time-phased Schedule / Baseline"],
      ["schedule_update",       "Schedule Update / Look-ahead"],
      ["change_order",          "Change Order / PCO"],
      ["monthly_report",        "Monthly Progress Report"]
    ]},
    { label: "Risk & Correspondence Documents", types: [
      ["rfi",                   "RFI / RFI Log"],
      ["rfi_log",               "RFI Log (register)"],
      ["rfa_log",               "RFA / Approval Log"],
      ["submittal",             "Submittal / Submittal Register"],
      ["oac_minutes",           "OAC Meeting Minutes"],
      ["correspondence_notice", "Correspondence / Notice"],
      ["risk_register",         "Risk Register"],
      ["inspection_report",     "Inspection Report / NCR"],
      ["field_report",          "Daily / Weekly Field Report"],
      ["commissioning_report",  "Test & Commissioning Report"]
    ]},
    { label: "Planning & Governance Documents", types: [
      ["airport_layout_plan",          "Airport Layout Plan (ALP)"],
      ["airport_master_plan",          "Airport Master Plan"],
      ["project_delivery_charter",     "Project Delivery System (PDS) Charter"],
      ["owners_project_requirements",  "Owner's Project Requirements (OPR)"],
      ["grant_assurances",             "Grant Assurances & Funding Compliance"],
      ["bim_execution_plan",           "BIM Execution Plan (BEP)"],
      ["front_end_project_manual",     "Front-End / Project Manual"],
      ["technical_specifications",     "Technical Specifications"],
      ["schematic_design",             "Schematic Design (SD) Sets"],
      ["design_development",           "Design Development (DD) Sets"],
      ["construction_documents",       "Construction Documents (CD Sets)"],
      ["basis_of_design",              "Basis of Design (BOD)"],
      ["construction_safety_phasing",  "Construction Safety & Phasing Plan (CSPP)"],
      ["project_execution_plan",       "Project Execution Plan (PEP)"],
      ["as_built_drawings",            "As-Built Drawings / Closeout Logs"]
    ]},
    { label: "Compliance & Performance Documents", types: [
      ["safety_report",            "Safety Report"],
      ["quality_audit_report",     "Quality Audit Report"],
      ["environmental_report",     "Environmental Compliance Report"],
      ["ncr_log",                  "NCR Log (Non-Conformance)"],
      ["subcontractor_report",     "Subcontractor Performance Report"],
      ["procurement_log",          "Procurement Log"],
      ["lookahead_schedule",       "Look-Ahead Schedule (6-week)"],
      ["resource_report",          "Resource Report"],
      ["cost_report",              "Cost Report"],
      ["past_performance_report",  "Past Performance Report"],
      ["historical_data",          "Historical Project Data"]
    ]}
  ];
  // flat list (back-compat) + value→label map
  const DOC_TYPES = DOC_TYPE_GROUPS.reduce((a, g) => a.concat(g.types), []);
  const DOC_TYPE_LABEL = DOC_TYPES.reduce((m, [k, v]) => (m[k] = v, m), {});

  /* signalInputs rows, in display order. editable = has an overwrite pencil. */
  const FIELD_ROWS = [
    { key: "bac",                label: "BAC",                     editable: true },
    { key: "ev",                 label: "EV (completed-to-date)",  editable: true },
    { key: "ac",                 label: "AC (paid-to-date)",       editable: true },
    { key: "pv",                 label: "PV (planned value)",      editable: true },
    { key: "actualPctComplete",  label: "Actual % complete",       editable: true },
    { key: "plannedPctComplete", label: "Planned % complete",      editable: true },
    { key: "docRiskScore",       label: "Document-risk score",     editable: true },
    { key: "cpi",                label: "CPI (computed)",           editable: false },
    { key: "spi",                label: "SPI (computed)",           editable: false }
  ];

  const ACCEPT = ".pdf,.doc,.docx,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg," +
    "application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document";

  /* ---------- per-project module cache (latest extraction result) ---------- */
  // cache[id] = { signalInputs, missing, readyToRun }
  const cache = {};
  // Drop a project's cached extraction so a post-reset UI doesn't re-show stale
  // signal inputs in the detail panel. Called by the "Reset signals" handler.
  function clearCache(id) { if (id != null) delete cache[id]; }

  /* ---------- PDF.js client-side text extraction ----------
     Apps Script's byte-level PDF parsing is unreliable for ReportLab-generated
     PDFs, so PDFs are converted to plain text in the browser and sent as `text`.
     The CDN script (index.html) exposes the global `pdfjsLib`. */
  let pdfWorkerSet = false;
  function ensurePdfWorker() {
    if (pdfWorkerSet || typeof pdfjsLib === "undefined") return;
    pdfjsLib.GlobalWorkerOptions.workerSrc =
      "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
    pdfWorkerSet = true;
  }
  async function extractPDFText(file) {
    ensurePdfWorker();
    const arrayBuffer = await file.arrayBuffer();
    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
    let text = "";
    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      const content = await page.getTextContent();
      text += content.items.map((item) => item.str).join(" ") + "\n";
    }
    return text.trim();
  }
  const isPdf = (file) =>
    file.type === "application/pdf" || /\.pdf$/i.test(file.name || "");

  /* ---------- helpers ---------- */
  function readFileAsBase64(file) {
    return new Promise((resolve, reject) => {
      const r = new FileReader();
      r.onerror = () => reject(new Error("Couldn't read file"));
      r.onload = () => {
        const result = String(r.result || "");
        const comma = result.indexOf(",");
        resolve(comma >= 0 ? result.slice(comma + 1) : result);
      };
      r.readAsDataURL(file);
    });
  }
  function fmtNum(v) {
    if (v == null || v === "") return null;
    const n = Number(v);
    if (!Number.isFinite(n)) return String(v);
    // keep small ratios at 2dp, whole-ish money at 0–2dp
    if (Math.abs(n) < 10) return (Math.round(n * 100) / 100).toString();
    return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
  }
  function fmtDate(s) {
    if (!s) return "";
    try { return window.LinTZ ? LinTZ.format(s) : String(s); } catch (e) { return String(s); }
  }
  function projectOptions(selectedId) {
    const list = (LinStore.cachedActive && LinStore.cachedActive()) || [];
    return `<option value="">Select project…</option>` +
      list.map((p) => `<option value="${esc(p.id)}"${p.id === selectedId ? " selected" : ""}>${esc(p.id)} — ${esc(p.name)}</option>`).join("");
  }
  function sourceLog(si, key) {
    const src = si && si.sources && si.sources[key];
    if (!src) return [];
    return Array.isArray(src) ? src : [src];
  }
  function latestSource(si, key) {
    const log = sourceLog(si, key);
    return log.length ? log[log.length - 1] : null;
  }
  function sourceDocType(si, key) {
    const src = latestSource(si, key);
    if (!src) return null;
    return src.docType || src.doc || src.type || null;
  }
  function appendSourceEntry(si, key, value, docTypeName, fileNameStr, reason, at) {
    if (!si || value == null || value === "") return;
    si.sources = si.sources || {};
    if (!Array.isArray(si.sources[key])) si.sources[key] = si.sources[key] ? [si.sources[key]] : [];
    si.sources[key].push({
      value,
      docType: docTypeName || "unknown",
      fileName: fileNameStr || null,
      at: at || new Date().toISOString(),
      reason: reason == null ? null : reason
    });
  }
  function appendExtractedSources(si, keys, docTypeName, fileNameStr) {
    const seen = {};
    (keys || []).forEach((key) => {
      if (!FIELD_ROWS.some((f) => f.key === key) || seen[key]) return;
      seen[key] = true;
      appendSourceEntry(si, key, si[key], docTypeName, fileNameStr, null);
    });
  }
  function fullSourceHistory(si) {
    si = si || {};
    const src = si.sources || {};
    return ["bac", "ev", "ac", "pv", "cpi", "spi"].reduce((out, key) => {
      const log = Array.isArray(src[key]) ? src[key] : (src[key] ? [src[key]] : []);
      out[key] = { current: si[key], log: log.slice() };
      return out;
    }, {});
  }

  const MODULE_METHOD_MAP = {
    PERT_Network_Criticality: "m04_pert",
    Line_of_Balance_Velocity: "m05_lob",
    CCPM_Buffer_Health: "m06_ccpm",
    Reference_Class_Forecasting: "m07_rcf",
    DSM_Rework_Propagation: "m08_dsm",
    Rough_Sets_Classification: "m11_rough_sets",
    Neutrosophic_Logic: "m12_neutrosophic",
    Interval_Fuzzy_Sets: "m13_interval_fuzzy",
    Z_Numbers: "m14_z_numbers",
    PLTS: "m15_plts",
    Plithogenic_Sets: "m16_plithogenic",
    Belief_Rule_Base: "m17_brb",
    Quantum_Probability: "m18_quantum",
    DST_Evidence_Combination: "m10_dst"
  };

  function decisionSnapshot(project) {
    if (!project || !project.signals) return null;
    if (project.signals.decision) return project.signals.decision;
    if (typeof deriveDecision !== "function") return null;
    const d = deriveDecision(project);
    return {
      state: d.healthState,
      conflict: d.conflictType,
      authority: d.authority,
      action: d.action,
      fairnessGate: d.fairnessGateRequired
    };
  }

  /* Ensure modules 04-08 and 10-18 have results when project.signals exists.
     These depend on existingSignals (the assembled signal package), so they
     must run AFTER MC/CUSUM/Doc. If a project was saved before this code
     shipped — or simulationSignals never got persisted — compute on-the-fly
     so the spider chart's 19 axes all carry a status. */
  /* Reconstruct the model inputs. Prefer the extracted signalInputs, but the
     backend echo omits client-only fields — a re-fetched/reloaded project can
     arrive with project.signals (CPI/SPI/BAC baked into signals.evm) yet no
     signalInputs. Falling back to signals.evm keeps the index-driven modules
     computing instead of collapsing the whole web to "No data". */
  function resolveSimInputs(project) {
    const si = Object.assign({}, project.signalInputs || {});
    const evm = (project.signals && project.signals.evm) || {};
    if (si.cpi == null && evm.cpi != null) si.cpi = evm.cpi;
    if (si.spi == null && evm.spi != null) si.spi = evm.spi;
    if (si.bac == null && evm.bac != null) si.bac = evm.bac;
    const doc = project.signals && project.signals.doc;
    if (si.docRiskScore == null && doc && doc.score != null) si.docRiskScore = doc.score;
    // Milestone Trend (Cat 2.7) reads dated snapshots the backend accumulates on
    // project.milestoneHistory. Bridge that project-level series into the module
    // inputs here, the same way the EVM histories reach the modules via si.
    if (si.milestoneHistory == null && Array.isArray(project.milestoneHistory)) {
      si.milestoneHistory = project.milestoneHistory;
    }
    return si;
  }

  function ensureSimulations(project, force) {
    if (!project || !project.signals || !window.LinSimulations) return;
    const arr = project.simulationSignals && project.simulationSignals.signal_array;
    const meta = project.simulationSignals && project.simulationSignals.signal_metadata;
    const si = deriveExtendedFields(resolveSimInputs(project));
    const fieldCount = Object.keys(si).filter(function(k) { return si[k] != null; }).length;
    const storedFieldCount = (meta && meta.signal_inputs_field_count) || 0;
    // Skip only when: not forced, array is non-empty, version is current, AND the field count
    // has not grown since the last run. More fields available → more modules can compute → rerun.
    const current = !force &&
      Array.isArray(arr) && arr.length &&
      meta && meta.module_set_version >= SIM_MODULE_SET_VERSION &&
      fieldCount <= storedFieldCount;
    if (current) return;
    // Diagnostic: confirm full field set reaches runAll.
    console.log("[runAll] inputs:", {
      cpi: si.cpi, spi: si.spi, bac: si.bac, ev: si.ev, ac: si.ac, pv: si.pv,
      docRiskScore: si.docRiskScore, fieldCount: fieldCount, fields: Object.keys(si)
    });
    try {
      const simResults = LinSimulations.runAll(si, project.signals, project);
      const dstResult = LinSimulations.runDST(si, project.signals);
      const all = simResults.concat([dstResult]);
      project.simulationSignals = {
        signal_metadata: {
          project_id: project.id,
          reporting_period: project.reportingPeriod || null,
          module_set_version: SIM_MODULE_SET_VERSION,
          signal_inputs_field_count: fieldCount,
          signal_inputs_snapshot: Object.assign({}, si),
          computed_inline: true
        },
        signal_array: all
      };
    } catch (e) { /* non-fatal — chart will fall back to greys */ }
  }

  function buildHistorySnapshot(project, at) {
    if (!project || !project.signals) return null;
    ensureSimulations(project);
    const now = at || new Date();
    const period = now.toISOString().substring(0, 7);
    const si = project.signalInputs || {};
    const s = project.signals || {};
    const d = decisionSnapshot(project) || {};
    const snapshot = {
      period,
      computed_at: now.toISOString(),
      signal_inputs: Object.assign({}, si),
      signal_inputs_with_history: fullSourceHistory(si),
      module_results: {
        m01_monte_carlo: s.mc ? {
          p50: s.mc.p50,
          p80: s.mc.p80,
          p80_delta_pct: s.mc.p80DeltaPct != null ? s.mc.p80DeltaPct : s.mc.p80eacOverrunPct,
          p_delay: s.mc.pDelay != null ? s.mc.pDelay : s.mc.pMilestoneDelay,
          status: s.mc.status
        } : null,
        m02_cusum: s.cusum ? {
          breached: s.cusum.breached,
          peak: s.cusum.peak != null ? s.cusum.peak : s.cusum.drift,
          decision_h: s.cusum.h != null ? s.cusum.h : s.cusum.threshold,
          breach_period: s.cusum.breachPeriod != null ? s.cusum.breachPeriod : s.cusum.breachIndex,
          status: s.cusum.status
        } : null,
        m03_doc_risk: {
          score: s.doc ? s.doc.score : null,
          status: s.doc ? s.doc.status : "Green"
        },
        m04_pert: null,
        m05_lob: null,
        m06_ccpm: null,
        m07_rcf: null,
        m08_dsm: null,
        m09_conservative: { state: d.state || null, conflict: d.conflict || null },
        m10_dst: null,
        m11_rough_sets: null,
        m12_neutrosophic: null,
        m13_interval_fuzzy: null,
        m14_z_numbers: null,
        m15_plts: null,
        m16_plithogenic: null,
        m17_brb: null,
        m18_quantum: null,
        m19_abm: {
          state: d.state || null,
          authority: d.authority || null,
          action: d.action || null,
          fairness_gate: d.fairnessGate || false
        }
      },
      governance: {
        state: d.state || null,
        conflict: d.conflict || null,
        authority: d.authority || null,
        action: d.action || null,
        fairness_gate: d.fairnessGate || false
      }
    };
    const sim = project.simulationSignals && project.simulationSignals.signal_array;
    if (Array.isArray(sim)) {
      sim.forEach((sig) => {
        const key = MODULE_METHOD_MAP[sig.method_class];
        if (key) snapshot.module_results[key] = sig;
      });
    }
    return snapshot;
  }

  function persistHistorySnapshot(project, at) {
    const snapshot = buildHistorySnapshot(project, at);
    if (!snapshot) return null;
    project.history = Array.isArray(project.history) ? project.history : [];
    project.history = project.history.filter((h) => h && h.period !== snapshot.period);
    project.history.push(snapshot);
    if (project.history.length > 24) project.history = project.history.slice(-24);
    return snapshot;
  }

  /* ---------- category snapshot ----------
     Rolls every signal up the 9-category structure (see categories.js)
     and stores the result on project.history. The spider web (9 axes),
     the signal ledger, the Signals page, and the executive brief all
     read this stored object — it is the audit-trail artefact, not a
     view derived on demand. */
  function buildCategorySnapshot(project) {
    if (!project || !window.LIN_CATEGORIES || typeof window.getCategoryStatus !== "function") return null;
    const s = project.signals || {};
    const sim = (project.simulationSignals && project.simulationSignals.signal_array) || [];
    const si = project.signalInputs || {};

    const period =
      (si.docDate && String(si.docDate).substring(0, 7)) ||
      (si.workPeriodTo && String(si.workPeriodTo).substring(0, 7)) ||
      new Date().toISOString().substring(0, 7);

    const categoryResults = {};
    LIN_CATEGORIES.forEach((cat) => {
      const moduleResults = cat.modules.map((m) => {
        const status = window.getModuleStatus(m.method_class, project);
        const simResult = sim.find((r) => r.method_class === m.method_class) || null;
        return {
          id: m.id, num: m.num, name: m.name, method_class: m.method_class,
          status: status || null,
          evidence_metric: simResult ? (simResult.evidence_metric || null) : null,
          raw: simResult
        };
      });
      categoryResults[cat.id] = {
        id: cat.id, num: cat.num, name: cat.name,
        status: window.getCategoryStatus(cat.id, project),
        parked: !!cat.parked,
        modules: moduleResults
      };
    });

    const allModules = [];
    Object.keys(categoryResults).forEach((cid) => {
      const c = categoryResults[cid];
      if (c.parked) return;
      // 'NA' = sector abstention — kept on the per-module snapshot rows for the
      // audit trail, but excluded from the status tally like any abstain.
      c.modules.forEach((m) => { if (m.status && m.status !== "NA") allModules.push(m); });
    });

    const byStatus = { Complete: 0, Green: 0, Yellow: 0, Amber: 0, Red: 0, Unknown: 0 };
    allModules.forEach((m) => {
      const v = String(m.status || "");
      const lc = v.toLowerCase();
      if (lc.indexOf("red") >= 0)      byStatus.Red++;
      else if (lc === "amber" || lc === "orange") byStatus.Amber++;
      else if (lc === "yellow" || lc === "light-amber") byStatus.Yellow++;
      else if (lc === "green")         byStatus.Green++;
      else if (lc === "complete" || lc === "blue") byStatus.Complete++;
      else                             byStatus.Unknown++;
    });

    const evidenceMethods = (categoryResults.cat7 && categoryResults.cat7.modules) || [];
    const govState = s.decision ? s.decision.state : null;
    const baseline = String(govState || "").toLowerCase().replace("-review", "");
    const agreeing = baseline
      ? evidenceMethods.filter((m) => m.status && String(m.status).toLowerCase().indexOf(baseline) >= 0).length
      : 0;
    const confidence = agreeing >= 7 ? "HIGH" : agreeing >= 4 ? "MODERATE" : "LOW";

    const byCategory = {};
    Object.keys(categoryResults).forEach((cid) => { byCategory[cid] = categoryResults[cid].status; });

    const snapshot = {
      period,
      computed_at: new Date().toISOString(),
      project_id: project.id,
      project_name: project.name,
      sector: project.sector,
      signal_inputs: {
        bac: si.bac, ev: si.ev, ac: si.ac, pv: si.pv,
        cpi: si.cpi, spi: si.spi,
        doc_risk_score: si.docRiskScore,
        baseline_start: si.baselineStart,
        baseline_end: si.baselineEnd
      },
      categories: categoryResults,
      summary: {
        total_modules: allModules.length,
        by_status: byStatus,
        by_category: byCategory,
        evidence_agreement: {
          methods_checked: evidenceMethods.length,
          methods_agreeing: agreeing,
          confidence
        }
      },
      governance: {
        state: s.decision ? s.decision.state : null,
        conflict: s.decision ? s.decision.conflict : null,
        authority: s.decision ? s.decision.authority : null,
        action: s.decision ? s.decision.action : null,
        documentation: s.decision ? s.decision.documentation : null,
        fairness_gate: s.decision ? !!s.decision.fairnessGate : false
      },
      executive_brief: null
    };

    project.history = Array.isArray(project.history) ? project.history : [];
    project.history = project.history.filter((h) => h && h.period !== period);
    project.history.push(snapshot);
    if (project.history.length > 24) project.history = project.history.slice(-24);

    return snapshot;
  }

  /* ---------- Cat 8 — portfolio-wide ML anomaly detection ----------
     Builds signal vectors from every loaded project (plus the current one) and
     POSTs them to the backend `portfolioanalyze` endpoint (Code.gs v10.17),
     which returns the 5 Cat 8 module results. Non-fatal and async — the core
     signal run is never blocked by it. Returns an array of Cat-8 sim results
     (real results, or insufficient-data stubs when there isn't enough data). */
  const CAT8_METHODS = ["Isolation_Forest", "Portfolio_Outlier", "Trajectory_Classifier",
                        "Cross_Project_Pattern", "Anomaly_Score"];
  function cat8Insufficient(message) {
    return CAT8_METHODS.map((mc) => ({
      method_class: mc, status_color: null, insufficient_data: true,
      evidence_metric: message || "Insufficient portfolio data"
    }));
  }
  function portfolioVector(p) {
    // Shape-tolerant. Full projects carry the EVM figures under signalInputs;
    // SLIM rows from ?action=listslim (the stale-while-revalidate portfolio list
    // that now fills LIN_PROJECTS) expose cpi/spi/docRisk(Score)/actualPctComplete
    // at the TOP level with no signalInputs. Reading only signalInputs dropped
    // every slim row → pool < 3 → Cat 8 permanently starved. Read either shape.
    const si = (p && p.signalInputs) ? p.signalInputs : (p && p.slim ? p : null);
    if (!si || si.cpi == null) return null;
    const docRisk = si.docRiskScore != null ? si.docRiskScore
                  : (si.docRisk != null ? si.docRisk : 0);
    return {
      id: p.id,
      cpi: si.cpi,
      spi: si.spi,
      docRiskScore: docRisk,
      actualPctComplete: si.actualPctComplete || 0
    };
  }
  async function runPortfolioAnalysis(project, allProjects) {
    const list = allProjects || window.LIN_PROJECTS || [];
    const portfolio = list.map(portfolioVector).filter(Boolean);
    // Ensure the current project is represented (it may not be in the mirror yet).
    const self = portfolioVector(project);
    if (self && !portfolio.some((v) => v.id === project.id)) portfolio.push(self);

    if (portfolio.length < 3) {
      return cat8Insufficient("Need 3+ projects with signal data for portfolio analysis");
    }
    if (!window.LinStore || !LinStore.post ||
        (LinStore.configured && !LinStore.configured())) {
      return cat8Insufficient("Portfolio analysis endpoint unavailable");
    }
    try {
      const resp = await LinStore.post({
        action: "portfolioanalyze",
        id: project.id,
        portfolio: portfolio,
        history: project.history || []
      });
      if (!resp || resp.ok === false || resp.insufficient_data) {
        return cat8Insufficient((resp && resp.message) || "Insufficient portfolio data");
      }
      const results = [];
      const rs = resp.results || {};
      Object.keys(rs).forEach((k) => { if (rs[k]) results.push(rs[k]); });
      return results.length ? results : cat8Insufficient("No portfolio results returned");
    } catch (err) {
      console.error("portfolioanalyze failed:", err && err.message);
      return cat8Insufficient("Portfolio analysis request failed");
    }
  }

  /* ---------- run the EXISTING models from extracted signalInputs ----------
     Same path the old manual form used (LinSim.buildSignals + saveProject),
     fed from extracted cpi/spi/bac/doc-risk. fairnessSensitive is left
     untouched so the red-review fairness gate behaves exactly as before. */
  /* Derive extended signalInputs from the figures we already extract (BAC, AC,
     CPI, SPI, doc-risk, RFI, %-complete). This lets ~15 modules compute from the
     existing document set using industry-standard ratios. Every derived value is
     tagged in si.sources with docType 'derived' so the UI can flag it [est.] and
     the modules can note "estimated". Checks use == null so an absent (undefined)
     OR null field is derived; preconditions use != null so we never derive from a
     missing input. Returns the same (mutated) si. */
  function deriveExtendedFields(si) {
    if (!si) return si;
    si.sources = si.sources || {};
    const now = () => new Date().toISOString();
    const mark = (key, value, note) => { si.sources[key] = { docType: 'derived', value: value, note: note, at: now() }; };

    if (si.materialCostBaseline == null && si.bac != null) {
      si.materialCostBaseline = Math.round(si.bac * 0.40);
      mark('materialCostBaseline', si.materialCostBaseline, 'Derived: 40% of BAC');
    }
    if (si.materialCostCurrent == null && si.ac != null) {
      si.materialCostCurrent = Math.round(si.ac * 0.40);
      mark('materialCostCurrent', si.materialCostCurrent, 'Derived: 40% of AC');
    }
    if (si.indirectCostPlan == null && si.bac != null) {
      si.indirectCostPlan = Math.round(si.bac * 0.12);
      mark('indirectCostPlan', si.indirectCostPlan, 'Derived: 12% overhead on BAC');
    }
    if (si.indirectCostActual == null && si.ac != null) {
      si.indirectCostActual = Math.round(si.ac * 0.12);
      mark('indirectCostActual', si.indirectCostActual, 'Derived: 12% overhead on AC');
    }
    if (si.baselineContractSum == null && si.bac != null) {
      si.baselineContractSum = si.bac;
      mark('baselineContractSum', si.bac, 'Derived: original BAC');
    }
    if (si.revisedContractSum == null && si.bac != null) {
      si.revisedContractSum = si.bac;
      mark('revisedContractSum', si.bac, 'Derived: current BAC');
    }
    if (si.changeOrderCount == null) {
      si.changeOrderCount = 0;
      mark('changeOrderCount', 0, 'Derived: no change orders uploaded');
    }
    if (si.originalContingency == null && si.bac != null) {
      si.originalContingency = Math.round(si.bac * 0.10);
      mark('originalContingency', si.originalContingency, 'Derived: 10% of BAC');
    }
    if (si.remainingContingency == null && si.originalContingency != null && si.cpi != null) {
      const burnFactor = Math.max(0, 1 - (1 - si.cpi) * 2);
      si.remainingContingency = Math.round(si.originalContingency * burnFactor);
      mark('remainingContingency', si.remainingContingency, 'Derived: estimated from CPI performance');
    }
    if (si.rfiCount == null && si.rfiNumber != null) {
      si.rfiCount = si.rfiNumber;
      mark('rfiCount', si.rfiNumber, 'Derived: from RFI sequential number');
    }
    if (si.rfiPeriodDays == null && si.rfiCount != null) {
      si.rfiPeriodDays = 30;
      mark('rfiPeriodDays', 30, 'Derived: assumed 30-day period');
    }
    if (si.submittalsTotal == null && si.docRiskScore != null) {
      si.submittalsTotal = 10;
      si.submittalsRejected = Math.round(si.docRiskScore * 3);
      mark('submittalsTotal', 10, 'Derived: estimated from doc risk');
    }
    if (si.activitiesPlanned == null && si.plannedPctComplete != null) {
      si.activitiesPlanned = 10;
      si.activitiesConstrained = Math.round(Math.max(0, (1 - (si.spi != null ? si.spi : 1)) * 4));
      si.lookaheadWeeks = 6;
      mark('activitiesPlanned', 10, 'Derived: estimated from SPI');
    }
    if (si.qualityDeficienciesNoted == null && si.docRiskScore != null) {
      si.qualityDeficienciesNoted = Math.round(si.docRiskScore * 5);
      si.itemsInspected = 20;
      si.itemsFailed = si.qualityDeficienciesNoted;
      mark('qualityDeficienciesNoted', si.qualityDeficienciesNoted, 'Derived: estimated from doc risk score');
    }
    if (si.safetyIncidentsDiscussed == null && si.docRiskScore != null) {
      si.safetyIncidentsDiscussed = Math.round(si.docRiskScore * 2);
      mark('safetyIncidentsDiscussed', si.safetyIncidentsDiscussed, 'Derived: estimated from doc risk score');
    }
    if (si.environmentalIssuesDiscussed == null && si.docRiskScore != null) {
      si.environmentalIssuesDiscussed = Math.round(si.docRiskScore * 1.5);
      mark('environmentalIssuesDiscussed', si.environmentalIssuesDiscussed, 'Derived: estimated from doc risk score');
    }
    if (si.weatherDaysLost == null && si.spi != null) {
      si.weatherDaysLost = Math.round(Math.max(0, (1 - si.spi) * 10));
      mark('weatherDaysLost', si.weatherDaysLost, 'Derived: estimated from SPI degradation');
    }
    if (si.floatRemaining == null && si.spi != null && si.bac != null) {
      si.floatRemaining = Math.round(Math.max(0, si.spi * 15));
      mark('floatRemaining', si.floatRemaining, 'Derived: estimated from SPI');
    }
    // Subcontractor compliance: OAC issues + NCR + doc risk + RFI velocity.
    if (si.subcontractorComplianceScore == null) {
      let subBase = 100;
      if (si.subcontractorIssuesDiscussed) subBase -= si.subcontractorIssuesDiscussed * 8;
      if (si.outstandingActionItems) subBase -= si.outstandingActionItems * 5;
      if (si.ncrOpen) subBase -= si.ncrOpen * 5;
      if (si.docRiskScore) subBase -= si.docRiskScore * 15;
      if (si.rfiCount != null && si.rfiPeriodDays != null) {
        const subRfiPerWeek = (si.rfiCount / si.rfiPeriodDays) * 7;
        if (subRfiPerWeek > 6) subBase -= 15;
        else if (subRfiPerWeek > 3) subBase -= 8;
      }
      si.subcontractorComplianceScore = Math.max(0, Math.min(100, Math.round(subBase))) / 100;
      mark('subcontractorComplianceScore', si.subcontractorComplianceScore,
        'Derived: OAC issues + NCR count + doc risk + RFI velocity');
    }
    return si;
  }

  async function runModels(project, si) {
    const cpiNum = Number(si.cpi), spiNum = Number(si.spi);
    const haveCpi = Number.isFinite(cpiNum) && cpiNum > 0;
    const haveSpi = Number.isFinite(spiNum) && spiNum > 0;
    // Run when EITHER index is present. A project with only SPI (or only CPI)
    // extracted should still compute — buildSignals uses a neutral 1.0 for the
    // missing index (the model logic itself is unchanged).
    if (!haveCpi && !haveSpi) return false;
    const bac = Number(si.bac);
    const docScore = Number(si.docRiskScore);
    // Keep the extracted inputs on the project (matches the signalInputs model
    // and is persisted with the project on save).
    project.signalInputs = si;
    project.signals = LinSim.buildSignals({
      cpi: haveCpi ? cpiNum : 1,
      spi: haveSpi ? spiNum : 1,
      bac: Number.isFinite(bac) && bac > 0 ? bac : undefined,
      metric: haveSpi ? "SPI" : "CPI",
      docScore: Number.isFinite(docScore) ? docScore : 0.1,
      docSource: "(extracted from project documents)",
      docExcerpt: "Signals extracted from uploaded documents via the document-ingestion flow.",
      seed: LinSim.hashSeed(project.id)
    });
    const decision = decisionSnapshot(project);
    if (decision) project.signals.decision = decision;
    // Derive extended fields (material/overhead/contingency/RFI/quality/safety/
    // environmental/subcontractor) from the figures already extracted, so the
    // derived-field modules can compute. Tagged in si.sources as 'derived'.
    si = deriveExtendedFields(si);
    project.signalInputs = si;
    // Client-side multi-model simulations (zero tokens, zero backend).
    // runAll() returns modules 04-08 + 11-18. DST (Module 10) runs separately
    // after the core signal package is assembled so it reads live signal data.
    let simPayload = null;
    if (window.LinSimulations) {
      try {
        const simResults = LinSimulations.runAll(si, project.signals, project);
        // Module 10: DST runs separately — needs the assembled project.signals
        // (EVM/MC/CUSUM/Doc) as existingSignals, not the raw signalInputs.
        const dstResult = LinSimulations.runDST(si, project.signals);
        const allResults = simResults.concat([dstResult]);
        const now = new Date();
        simPayload = {
          signal_metadata: {
            project_id: project.id,
            run_at: now.toISOString(),
            reporting_period: now.toISOString().substring(0, 7),
            data_date: now.toISOString().substring(0, 10),
            module_set_version: SIM_MODULE_SET_VERSION,
            signal_inputs_field_count: Object.keys(si).filter(function(k) { return si[k] != null; }).length,
            signal_inputs_snapshot: Object.assign({}, si)
          },
          signal_array: allResults
        };
        project.simulationSignals = simPayload;
        if (window.LinForceNet) LinForceNet.updateFromProject(project);
        // Append simulation run event to the project audit trail.
        project.events = project.events || [];
        const statusOrder = ["red", "amber", "green"];
        const statuses = allResults.map((s) => String(s.status_color || s.status || "").toLowerCase());
        const worstStatus = statusOrder.find((s) => statuses.includes(s)) || "unknown";
        project.events.push({
          event: "simulation_run",
          at: now.toISOString(),
          modules: allResults.map((s) => ({ method: s.method_class, status: s.status_color || s.status })),
          worst_status: worstStatus
        });
      } catch (e) { /* simulations are non-fatal — never block the core run */ }
    }
    // Cat 8 — portfolio-wide ML anomaly detection (POST portfolioanalyze). Runs
    // AFTER runAll() so the snapshot below is built with Cat 8 included. Async
    // and non-fatal: merged into the sim array when it returns, skipped on error.
    if (simPayload) {
      try {
        const cat8 = await runPortfolioAnalysis(project, window.LIN_PROJECTS);
        if (Array.isArray(cat8) && cat8.length) {
          simPayload.signal_array = simPayload.signal_array
            .filter((s) => CAT8_METHODS.indexOf(s.method_class) < 0)
            .concat(cat8);
        }
      } catch (e) { /* Cat 8 is non-fatal — never block the core run */ }
    }
    persistHistorySnapshot(project);
    try { buildCategorySnapshot(project); } catch (e) { /* non-fatal — keeps the legacy snapshot path working */ }
    const builtSignals = project.signals;
    await LinStore.saveProject(project);
    // saveProject reconciles the in-memory mirror with the backend's echoed
    // project, which omits client-only fields (the built signals package,
    // signalInputs, and simulationSignals). Re-assert them onto the canonical
    // cached object so the detail deep-dive and the ledger keep rendering
    // after the save.
    const cached = LinStore.getCached(project.id);
    if (cached) {
      if (!hasSignals(cached) && builtSignals) cached.signals = builtSignals;
      if (!cached.signalInputs) cached.signalInputs = si;
      if (!cached.simulationSignals && simPayload) cached.simulationSignals = simPayload;
      if (project.history) cached.history = project.history;
      if (project.milestoneHistory) cached.milestoneHistory = project.milestoneHistory;
    }
    return true;
  }

  /* refresh the in-memory project (events + persisted state) after a server
     mutation, so the audit trail reflects the new signals_* event. */
  async function refreshProject(id) {
    try {
      const fresh = await LinStore.getProject(id);
      if (fresh && window.LIN_PROJECTS) {
        const i = LIN_PROJECTS.findIndex((x) => x.id === id);
        if (i >= 0) {
          // Don't drop the signals/inputs we just computed/saved if the server's
          // copy hasn't caught up yet (eventual consistency / save↔get race).
          if (!hasSignals(fresh) && hasSignals(LIN_PROJECTS[i])) fresh.signals = LIN_PROJECTS[i].signals;
          if (!fresh.signalInputs && LIN_PROJECTS[i].signalInputs) fresh.signalInputs = LIN_PROJECTS[i].signalInputs;
          // Never replace a larger in-memory sim array with a smaller server copy — the backend
          // never writes simulationSignals, so a fresh GET always returns an absent or stale array.
          const memArr   = LIN_PROJECTS[i].simulationSignals && LIN_PROJECTS[i].simulationSignals.signal_array;
          const freshArr = fresh.simulationSignals && fresh.simulationSignals.signal_array;
          const memLen   = Array.isArray(memArr)   ? memArr.length   : 0;
          const freshLen = Array.isArray(freshArr) ? freshArr.length : 0;
          if (!fresh.simulationSignals || memLen > freshLen) {
            if (LIN_PROJECTS[i].simulationSignals) fresh.simulationSignals = LIN_PROJECTS[i].simulationSignals;
          }
          if (!fresh.history && LIN_PROJECTS[i].history) fresh.history = LIN_PROJECTS[i].history;
          if (!fresh.milestoneHistory && LIN_PROJECTS[i].milestoneHistory) fresh.milestoneHistory = LIN_PROJECTS[i].milestoneHistory;
          LIN_PROJECTS[i] = fresh;
        }
      }
      return fresh;
    } catch (e) { return LinStore.getCached(id); }
  }

  /* ===========================================================
     Change 1 — document-ingestion form
     =========================================================== */
  function ingestFormHtml(fixedId) {
    const projectField = fixedId
      ? `<input type="hidden" class="ds-project" value="${esc(fixedId)}" />`
      : `<label class="rationale-label">Project
           <select class="ds-project ig-input">${projectOptions(null)}</select></label>`;
    return `
      <div class="kn-grid ds-form">
        <div>
          ${projectField}
          <label class="rationale-label">Document type
            <select class="ds-doctype ig-input">
              ${DOC_TYPE_GROUPS.map((g) => `<optgroup label="${esc(g.label)}">${
                g.types.map(([v, l]) => `<option value="${v}">${esc(l)}</option>`).join("")
              }</optgroup>`).join("")}
            </select></label>
          <p class="kn-sub">Dates are pulled from the document. Nothing to fill in.</p>
        </div>
        <div>
          <label class="rationale-label">Document</label>
          <p class="upload-disclaimer">Notice: Do not upload confidential, proprietary, or personally identifiable information, or documents relating to actual projects. Content is processed by third-party AI services. Uploads are made at the user's sole risk.</p>
          <label class="aud-filebtn ds-filebtn">
            <input type="file" class="ds-file" accept="${ACCEPT}" />
            <span class="ds-filebtn-label aud-filebtn-label">Choose file</span>
          </label>
          <div class="dc-actions"><button class="btn primary ds-run">Upload</button></div>
          <p class="ds-status kn-sub" aria-live="polite"></p>
        </div>
      </div>`;
  }

  /* ---------- loading overlay (cycling messages, CSS-only spinner) ---------- */
  const LOADING_MSGS = [
    "Reading document…",
    "Extracting EVM figures…",
    "Computing CPI / SPI…",
    "Updating signal ledger…",
  ];
  function startLoadingOverlay(container) {
    if (!container) return function () {};
    container.classList.add("ds-loading-host");
    const ov = document.createElement("div");
    ov.className = "ds-overlay";
    ov.innerHTML =
      `<div class="ds-overlay-box">
         <div class="ds-spin" aria-hidden="true"></div>
         <p class="ds-overlay-title">Extracting signals…</p>
         <p class="ds-overlay-msg" aria-live="polite">${esc(LOADING_MSGS[0])}</p>
       </div>`;
    container.appendChild(ov);
    const msgEl = ov.querySelector(".ds-overlay-msg");
    let i = 0;
    const timer = setInterval(() => {
      i = (i + 1) % LOADING_MSGS.length;
      if (msgEl) msgEl.textContent = LOADING_MSGS[i];
    }, 2000);
    let stopped = false;
    return function stop() {
      if (stopped) return;
      stopped = true;
      clearInterval(timer);
      ov.remove();
      container.classList.remove("ds-loading-host");
    };
  }

  /* ---------- result modal (success / error, CSS draw animations) ---------- */
  const MODAL_FIELD_LABELS = {
    bac: "Budget at Completion (BAC)", ev: "Earned Value (EV)", ac: "Actual Cost (AC)",
    pv: "Planned Value (PV)", actualPctComplete: "Actual % complete",
    plannedPctComplete: "Planned % complete", docRiskScore: "Document-risk score",
    cpi: "Cost Performance Index (CPI)", spi: "Schedule Performance Index (SPI)",
  };
  const MONEY_FIELDS = { bac: 1, ev: 1, ac: 1, pv: 1 };
  function modalValue(key, v) {
    const n = fmtNum(v);
    if (n == null) return null;
    return MONEY_FIELDS[key] ? "$" + n : n;
  }
  function showResultModal(opts) {
    const prev = document.querySelector(".ds-modal-backdrop");
    if (prev) prev.remove();
    const back = document.createElement("div");
    back.className = "ds-modal-backdrop";
    let inner;

    if (opts.success) {
      const si = opts.si || {};
      const fieldRows = ["bac", "ev", "ac", "pv", "actualPctComplete", "plannedPctComplete", "docRiskScore"]
        .map((k) => {
          const val = modalValue(k, si[k]);
          if (val == null) return "";
          const src = sourceDocType(si, k);
          return `<li class="ds-modal-field"><span class="ds-mf-label">${esc(MODAL_FIELD_LABELS[k])}</span>` +
            `<span class="ds-mf-val">${esc(val)}</span>` +
            (src ? `<span class="ds-mf-src">from ${esc(DOC_TYPE_LABEL[src] || src)}</span>` : "") + `</li>`;
        }).join("");
      const compRows = ["cpi", "spi"].map((k) => {
        const val = fmtNum(si[k]);
        if (val == null) return "";
        return `<li class="ds-modal-field"><span class="ds-mf-label">${esc(MODAL_FIELD_LABELS[k])}</span>` +
          `<span class="ds-mf-val">${esc(val)}</span><span class="ds-mf-src">computed</span></li>`;
      }).join("");
      const d = opts.dates || {};
      const periods = [];
      if (d.baselineStart || d.baselineEnd) periods.push(`Baseline: ${esc(d.baselineStart || "?")} → ${esc(d.baselineEnd || "?")}`);
      if (d.workPeriodFrom || d.workPeriodTo) periods.push(`Work period: ${esc(d.workPeriodFrom || "?")} → ${esc(d.workPeriodTo || "?")}`);
      const missingNames = (opts.missing || [])
        .map((m) => (typeof m === "string" ? m : (m.field || m.label || ""))).filter(Boolean);
      const runLine = opts.ran
        ? `<p class="ds-modal-run ok">✓ All models complete — view results below.</p>`
        : (opts.readyToRun ? `<p class="ds-modal-run">Models could not run — check CPI / SPI.</p>` : "");
      inner = `<div class="ds-modal ds-modal-success" role="dialog" aria-label="Signals extracted">
        <button class="ds-modal-x" aria-label="Close">×</button>
        <svg class="ds-anim-check" viewBox="0 0 52 52" aria-hidden="true">
          <circle class="ds-anim-ring" cx="26" cy="26" r="24" fill="none"/>
          <path class="ds-anim-stroke" fill="none" d="M14 27l8 8 16-16"/></svg>
        <h3 class="ds-modal-title">Signals extracted</h3>
        ${(fieldRows || compRows)
          ? `<ul class="ds-modal-fields">${fieldRows}${compRows}</ul>`
          : `<p class="kn-sub">No EVM figures were found in this document.</p>`}
        ${periods.length ? `<div class="ds-modal-periods">${periods.map((p) => `<p>${p}</p>`).join("")}</div>` : ""}
        ${missingNames.length ? `<p class="ds-modal-missing">Still needed: ${esc(missingNames.join(", "))}</p>` : ""}
        ${runLine}
      </div>`;
    } else {
      inner = `<div class="ds-modal ds-modal-error" role="alertdialog" aria-label="Extraction failed">
        <button class="ds-modal-x" aria-label="Close">×</button>
        <svg class="ds-anim-x" viewBox="0 0 52 52" aria-hidden="true">
          <circle class="ds-anim-ring" cx="26" cy="26" r="24" fill="none"/>
          <path class="ds-anim-stroke" fill="none" d="M18 18l16 16"/>
          <path class="ds-anim-stroke ds-anim-stroke-2" fill="none" d="M34 18l-16 16"/></svg>
        <h3 class="ds-modal-title">Extraction failed</h3>
        <p class="ds-modal-err">${esc(opts.error || "Unknown error")}</p>
        <div class="dc-actions"><button class="btn primary ds-modal-retry">Try again</button></div>
      </div>`;
    }

    back.innerHTML = inner;
    document.body.appendChild(back);
    let timer = null;
    const close = () => { if (timer) clearTimeout(timer); back.remove(); };
    back.querySelector(".ds-modal-x").addEventListener("click", close);
    back.addEventListener("click", (e) => { if (e.target === back) close(); });
    const retry = back.querySelector(".ds-modal-retry");
    if (retry) retry.addEventListener("click", () => { close(); if (opts.onTryAgain) opts.onTryAgain(); });
    if (opts.success) timer = setTimeout(close, 8000); // auto-dismiss success after 8s
    return close;
  }

  function wireIngestForm(container, onResult) {
    const $c = (sel) => container.querySelector(sel);
    let picked = null;
    const fileInput = $c(".ds-file");
    if (fileInput) fileInput.addEventListener("change", (e) => {
      picked = (e.target.files && e.target.files[0]) || null;
      const lbl = $c(".ds-filebtn-label");
      if (lbl) lbl.textContent = picked ? picked.name : "Choose file";
    });

    $c(".ds-run").addEventListener("click", async () => {
      const id = $c(".ds-project").value;
      const status = $c(".ds-status");
      if (!id) { status.textContent = "Select a project first."; return; }
      if (!picked) { status.textContent = "Choose a document to upload."; return; }
      const docType = $c(".ds-doctype").value;

      const btn = $c(".ds-run");
      btn.disabled = true;
      btn.classList.add("ds-loading");
      status.textContent = "Scanning document with AI… this can take a few seconds.";
      const stopLoading = startLoadingOverlay(container);
      try {
        // Document upload diagnostics — the detailed logging + the hard size
        // cap run just below, immediately before the fetch. A "Failed to fetch"
        // with no HTTP status is usually a CORS preflight block, a network
        // timeout on a large payload, or mixed content (http vs https).
        // PDFs → extract text client-side (PDF.js) and send as `text`.
        // If PDF.js returns little/no text (scanned or image-only PDF), fall
        // back to base64 so the backend can OCR / multimodal-parse it.
        // Images / doc / docx → always send the raw file as `dataBase64`.
        const args = { id, docType, mimeType: picked.type || "application/octet-stream", fileName: picked.name };
        if (isPdf(picked) && typeof pdfjsLib !== "undefined") {
          status.textContent = "Reading PDF text in your browser…";
          const extractedText = await extractPDFText(picked);
          if (extractedText && extractedText.trim().length > 200) {
            args.text = extractedText;                       // born-digital PDF → text path
          } else {
            args.dataBase64 = await readFileAsBase64(picked); // scanned/image-only → server fallback
          }
          status.textContent = "Scanning document with AI… this can take a few seconds.";
        } else {
          args.dataBase64 = await readFileAsBase64(picked);
        }
        // Diagnostics immediately before the fetch — confirm exactly what is
        // sent to the extractsignals endpoint.
        const dataBase64 = args.dataBase64 || "";
        console.log("Upload URL:", window.LIN_API_URL);
        console.log("File size (bytes):", picked.size);
        console.log("Base64 length:", dataBase64.length);
        console.log("Doc type:", docType);
        console.log("Project id:", id);

        // Hard cap: base64 payloads over ~5M chars (~3.75 MB file) reliably
        // fail the Apps Script POST as "Failed to fetch". Block before the
        // fetch so the user gets a clear message instead of a network error.
        // Born-digital PDFs take the text path above (no dataBase64) and are
        // unaffected by this cap.
        if (dataBase64.length > 5000000) {
          status.textContent = "File too large — maximum 3MB. Please compress the PDF.";
          return; // finally{} re-enables the button + clears the overlay
        }
        const resp = await LinStore.extractSignals(args);
        // v7 returns computed CPI/SPI in `computed`; merge them into the
        // signalInputs view so the ledger + model run see them in one place.
        const si = mergeComputed(resp);
        const appliedKeys = (resp.applied && resp.applied.length)
          ? resp.applied.slice()
          : FIELD_ROWS.map((row) => row.key).filter((key) => si[key] != null && si[key] !== "");
        ["cpi", "spi"].forEach((key) => {
          if (si[key] != null && si[key] !== "" && !appliedKeys.includes(key)) appliedKeys.push(key);
        });
        appendExtractedSources(si, appliedKeys, docType, picked.name);
        const missing = resp.missing || [];
        const readyToRun = resp.readyToRun != null ? !!resp.readyToRun
          : (Number.isFinite(Number(si.cpi)) && Number.isFinite(Number(si.spi)));
        const dates = extractDates(resp, si);
        cache[id] = { signalInputs: si, missing, readyToRun, dates };

        // Run as soon as EITHER index is present (not only when both are).
        const canCompute = hasIndex(si.cpi) || hasIndex(si.spi);
        const project = LinStore.getCached(id);
        let ran = false;
        if (canCompute && project) {
          status.textContent = readyToRun
            ? "CPI and SPI ready — running models…"
            : "CPI or SPI ready — running models…";
          // Merge into accumulated inputs so successive single-file uploads on the same project
          // don't overwrite prior fields with null (each doc only carries its own field set).
          const accSi = Object.assign({}, project.signalInputs || {});
          Object.keys(si).forEach(function(k) { if (si[k] != null && si[k] !== "") accSi[k] = si[k]; });
          ran = await runModels(project, accSi);
        }
        await refreshProject(id);

        status.textContent = ran
          ? "Extracted — models ran on the extracted signals."
          : (canCompute
              ? "Extracted — but the models could not run (check CPI/SPI)."
              : "Extracted. Upload a document with CPI or SPI to run the models (see Details below).");
        if (window.LinApp) LinApp.refresh();
        if (onResult) onResult(id, { signalInputs: si, missing, readyToRun, ran });
        stopLoading();
        showResultModal({ success: true, si, missing, dates, readyToRun, ran });
      } catch (e) {
        console.error("Upload fetch error:", e && e.name, e && e.message);
        const msg = (e && e.message ? e.message : "store unreachable");
        status.textContent = "Extraction failed: " + msg + ". The form is still usable — retry.";
        stopLoading();
        showResultModal({ success: false, error: msg, onTryAgain: () => { const f = $c(".ds-file"); if (f) f.focus(); } });
      } finally {
        stopLoading();
        btn.disabled = false;
        btn.classList.remove("ds-loading");
      }
    });
  }

  /* ===========================================================
     Drag-and-drop multi-file ingest (Manage Projects page)
     -----------------------------------------------------------
     Drop any combination of documents. Each file is (1) identified
     via the identifyOnly endpoint, then (2) auto-extracted immediately
     with the identified docType — no confirmation or type-override
     step — and the models are run on the extracted signals. The file
     is read as base64 once and reused across both calls (storedFileId
     lets the backend skip re-uploading on extract).
     =========================================================== */

  // The 15 supported document types, shown as a non-interactive reference panel.
  const DROPZONE_REFERENCE = [
    "Pay Application", "Monthly Progress Report", "RFI Log", "OAC Meeting Minutes",
    "Schedule Update", "Change Order", "Field Report", "Inspection Report",
    "NCR Log", "Subcontractor Report", "Procurement Log", "Lookahead Schedule",
    "Resource Report", "Cost Report", "Past Performance Report"
  ];

  function dropzoneHtml(fixedId) {
    const projectField = fixedId
      ? `<input type="hidden" class="dz-project" value="${esc(fixedId)}" />`
      : `<label class="rationale-label">Project
           <select id="manage-project-select" class="dz-project ig-input">${projectOptions(null)}</select></label>`;
    return `
      <div class="doc-type-reference">
        <div class="dtr-title">Supported document types</div>
        <div class="dtr-grid">${DROPZONE_REFERENCE.map((t) => `<span class="dtr-pill">${esc(t)}</span>`).join("")}</div>
        <p class="dtr-note">Upload any combination — Lin identifies each document automatically.</p>
      </div>
      <div class="dz-project-row">${projectField}</div>
      <div class="dropzone">
        <div class="dz-icon" aria-hidden="true">↑</div>
        <div class="dz-title">Drop documents here</div>
        <div class="dz-sub">PDF · multiple files at once · Lin identifies type automatically</div>
        <p class="upload-disclaimer">Notice: Do not upload confidential, proprietary, or personally identifiable information, or documents relating to actual projects. Content is processed by third-party AI services. Uploads are made at the user's sole risk.</p>
        <button type="button" class="dz-browse">Browse files</button>
        <input type="file" class="dz-input" multiple accept="${ACCEPT}" hidden />
      </div>
      <div class="dz-queue" aria-live="polite"></div>`;
  }

  function wireDropzone(container, onResult, onBatch) {
    if (!container) return;
    const reportBatch = (ev) => { try { if (onBatch) onBatch(ev); } catch (e) {} };
    const dz = container.querySelector(".dropzone");
    const input = container.querySelector(".dz-input");
    const queue = container.querySelector(".dz-queue");
    const browse = container.querySelector(".dz-browse");
    if (!dz || !input || !queue) return;

    browse.addEventListener("click", () => input.click());
    input.addEventListener("change", (e) => { handleFiles(e.target.files); input.value = ""; });
    ["dragenter", "dragover"].forEach((ev) =>
      dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.add("dragover"); }));
    dz.addEventListener("dragleave", (e) => {
      e.preventDefault();
      if (dz.contains(e.relatedTarget)) return;
      dz.classList.remove("dragover");
    });
    dz.addEventListener("drop", (e) => {
      e.preventDefault();
      dz.classList.remove("dragover");
      handleFiles(e.dataTransfer && e.dataTransfer.files);
    });

    // CORS-safe POST with 45s timeout — text/plain bypasses preflight for Apps Script.
    function postJSON(payload) {
      var controller = new AbortController();
      var timedOut = false;
      var timer = setTimeout(function () { timedOut = true; controller.abort(); }, 45000);
      return fetch(window.LIN_API_URL || "", {
        method: "POST",
        headers: { "Content-Type": "text/plain" },
        body: JSON.stringify(payload),
        signal: controller.signal
      })
        .then(function (r) { return r.text(); })
        .then(function (t) {
          try { return JSON.parse(t); }
          catch (e) { throw new Error("Bad response: " + t.substring(0, 120)); }
        })
        .catch(function (e) {
          // Translate the browser's generic AbortError into a clear timeout message.
          if (timedOut || (e && e.name === "AbortError")) {
            throw new Error("Request timed out after 45s — try a smaller file or retry");
          }
          throw e;
        })
        .finally(function () { clearTimeout(timer); });
    }

    function fileToBase64(file) {
      return new Promise(function (resolve, reject) {
        var reader = new FileReader();
        reader.onload = function (e) {
          var raw = e.target.result;
          resolve(raw.indexOf(",") !== -1 ? raw.split(",")[1] : raw);
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });
    }

    function setError(item, file, msg, retryFn) {
      item.className = "dz-item dz-error";
      item.innerHTML = `<span class="dz-item-name">${esc(file.name)}</span>` +
        `<span class="dz-item-error">✗ ${esc(msg)}</span>`;
      if (retryFn) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "dz-item-retry btn small";
        btn.textContent = "Retry";
        btn.addEventListener("click", retryFn);
        item.appendChild(btn);
      }
    }

    // Detect an Anthropic rate-limit (HTTP 429 / rate_limit_error). The backend
    // reports it INSIDE the resolved response (e.g. "Auto extraction failed:
    // Error: Claude PDF 429: {...rate_limit_error...}"), so check the response
    // object/text as well as any thrown error.
    function isRateLimited(x) {
      if (x == null) return false;
      let s;
      if (typeof x === "string") s = x;
      else if (x instanceof Error) s = x.message || "";
      else { try { s = JSON.stringify(x); } catch (e) { s = String(x); } }
      return /\b429\b/.test(s) || /rate[_\s-]?limit/i.test(s);
    }

    // Wait out a rate-limit window with a live countdown in the item's status span.
    function rateLimitWait(item, ms) {
      const statusEl = item.querySelector(".dz-item-status");
      let remaining = Math.round(ms / 1000);
      return new Promise(function (resolve) {
        (function tick() {
          if (statusEl) statusEl.textContent = "⏳ Rate limited — retrying in " + remaining + "s…";
          if (remaining <= 0) return resolve();
          remaining -= 1;
          setTimeout(tick, 1000);
        })();
      });
    }

    // Extract with auto-retry on rate-limit errors. Up to 4 attempts; on a 429 it
    // waits 20s / 40s / 60s before the next try (each clears the 60s token window).
    // Returns the successful response. Throws on a non-rate-limit failure (→ the
    // existing setError path) or when all 4 attempts are exhausted.
    async function extractWithRetry(payload, item) {
      const BACKOFF = [20000, 40000, 60000]; // before attempts 2, 3, 4
      const MAX = 4;
      for (let attempt = 1; attempt <= MAX; attempt++) {
        let resp = null, threw = null;
        try {
          resp = await postJSON(payload);
          // Full response, logged before any success/failure decision.
          console.log("[upload] extractsignals response (attempt " + attempt + "):", resp);
        } catch (e) { threw = e; }

        if (!threw) {
          // SUCCESS whenever the backend returned ok:true, OR an `applied` list with
          // no error — a valid response with no CPI/SPI fields (Cost/Environmental
          // report) still succeeded. (Success logic unchanged.)
          const ok = resp && (resp.ok === true || (!resp.error && resp.applied !== undefined));
          if (ok) return resp;
        }
        const limited = threw ? isRateLimited(threw) : isRateLimited(resp);
        if (!limited) {                                   // non-rate-limit → fail as today
          if (threw) throw threw;
          throw new Error((resp && resp.error) || "extract failed");
        }
        if (attempt === MAX) throw new Error("Rate limited — wait a minute and Retry");
        await rateLimitWait(item, BACKOFF[attempt - 1]);  // wait, then retry
      }
    }

    async function processOne(id, file) {
      const item = document.createElement("div");
      item.className = "dz-item dz-identifying";
      item.innerHTML = `<span class="dz-item-name">${esc(file.name)}</span>` +
        `<span class="dz-item-status">⟳ Identifying…</span>`;
      queue.appendChild(item);
      reportBatch({ type: "file", name: file.name, state: "uploading" });

      if (file.size > 20 * 1024 * 1024) {
        setError(item, file, "File too large — max 20 MB");
        return { name: file.name, status: "failed", error: "File too large — max 20 MB" };
      }

      let base64;
      try { base64 = await fileToBase64(file); }
      catch (e) { setError(item, file, "Couldn't read file"); return { name: file.name, status: "failed", error: "Couldn't read file" }; }

      if (base64.length > 5000000) {
        setError(item, file, "File too large — maximum ~3 MB. Please compress the PDF.");
        return { name: file.name, status: "failed", error: "File too large — compress the PDF (~3 MB max)" };
      }

      // Single call: extract everything AND infer the document type at once
      // (docType:"auto"). No separate identifyOnly round-trip. The backend reads
      // the document, names the type, and extracts every field in one pass.
      reportBatch({ type: "file", name: file.name, state: "extracting" });
      item.className = "dz-item dz-identified";
      item.innerHTML = `<span class="dz-item-name">${esc(file.name)}</span>` +
        `<span class="dz-item-status">\u27f3 Extracting\u2026</span>`;

      let docType = "auto";
      try {
        const extractPayload = {
          action: "extractsignals",
          id,
          docType: "auto",
          dataBase64: base64,
          mimeType: file.type || "application/pdf",
          fileName: file.name
        };
        // Extract with auto-retry on Anthropic rate-limit (429) errors. Returns the
        // successful response; throws on a non-rate-limit failure or exhausted
        // retries (handled by the outer catch → setError). The success gate lives
        // inside extractWithRetry, unchanged.
        const resp = await extractWithRetry(extractPayload, item);

        // The backend echoes which type it inferred — use it for labels/sources.
        docType = resp.docType || docType;

        // resp.applied is authoritative for the field count; fall back to 0.
        const applied = Array.isArray(resp && resp.applied) ? resp.applied : [];
        let appliedCount = applied.length;

        // Secondary client-side work (merge into the cache, run models, refresh the
        // project view). NON-FATAL: a failure here must NOT turn a successful
        // extract into an error — the document was processed server-side regardless.
        let si = null;
        try {
          si = mergeComputed(resp);
          const appliedKeys = applied.length
            ? applied.slice()
            : FIELD_ROWS.map((r) => r.key).filter((k) => si[k] != null && si[k] !== "");
          ["cpi", "spi"].forEach((k) => {
            if (si[k] != null && si[k] !== "" && !appliedKeys.includes(k)) appliedKeys.push(k);
          });
          appliedCount = appliedKeys.length;
          appendExtractedSources(si, appliedKeys, docType, file.name);
          const missing = (resp && resp.missing) || [];
          const dates = extractDates(resp, si);
          cache[id] = { signalInputs: si, missing, readyToRun: resp && resp.readyToRun, dates };
          // Do NOT call runModels here — the batch runs module computation ONCE at the
          // end of handleFiles on the full accumulated field set (Fix 1b). Running per-doc
          // produces a small partial array that freezes at an early field count.
          await refreshProject(id);
        } catch (postErr) {
          console.warn("[upload] post-extract processing failed (extract itself succeeded):", postErr);
        }

        // Success — show what was applied. Zero fields is still a success.
        let resultText;
        if (appliedCount > 0) {
          const bits = [appliedCount + " field" + (appliedCount === 1 ? "" : "s")];
          if (si) {
            const cpi = fmtNum(si.cpi), spi = fmtNum(si.spi);
            if (cpi != null) bits.push("CPI " + cpi);
            if (spi != null) bits.push("SPI " + spi);
          }
          resultText = "✓ extracted " + bits.join(" · ");
        } else {
          resultText = "✓ processed (no signal fields in this document type)";
        }
        item.className = "dz-item dz-done";
        item.innerHTML = `<span class="dz-item-name">${esc(file.name)}</span>` +
          `<span class="dz-item-result">${esc(resultText)}</span>`;
        try { if (window.LinApp) LinApp.refresh(); } catch (e) { /* non-fatal */ }
        try { if (onResult) onResult(id); } catch (e) { /* non-fatal */ }
        return { name: file.name, status: "done", fields: appliedCount };
      } catch (e) {
        console.error("[dropzone] extract error:", e);
        setError(item, file, (e && e.message) || "Network error — check console",
          function () { item.remove(); processOne(id, file); });
        return { name: file.name, status: "failed", error: (e && e.message) || "Network error" };
      }
    }

    async function handleFiles(fileList) {
      const files = [].slice.call(fileList || []);
      if (!files.length) return;

      // Re-read the project select live at drop time (list may have loaded after render).
      const projectEl = container.querySelector(".dz-project");
      let id = projectEl ? projectEl.value : "";
      // Refresh options if select is empty (projects loaded after initial render).
      if (projectEl && projectEl.tagName === "SELECT" && projectEl.options.length <= 1) {
        projectEl.innerHTML = `<option value="">Select project…</option>` +
          ((LinStore.cachedActive && LinStore.cachedActive()) || [])
            .map(function (p) { return `<option value="${esc(p.id)}">${esc(p.id)} — ${esc(p.name)}</option>`; })
            .join("");
        id = projectEl.value;
      }
      if (!id) {
        const note = document.createElement("div");
        note.className = "dz-item dz-error";
        note.innerHTML = `<span class="dz-item-error">Select a project above before dropping documents.</span>`;
        queue.appendChild(note);
        return;
      }
      reportBatch({ type: "start", total: files.length, projectId: id });
      const summary = [];
      for (let i = 0; i < files.length; i++) {
        const res = await processOne(id, files[i]) || { name: files[i].name, status: "failed", error: "unknown" };
        summary.push(res);
        reportBatch({ type: "progress", done: i + 1, total: files.length, name: res.name, status: res.status });
        // 2.5s between files spreads a ~27-doc batch over ~70s so it stays under
        // the Anthropic 30k-input-tokens/min rate limit (a 429 trips otherwise).
        if (i < files.length - 1) await new Promise(function (r) { setTimeout(r, 2500); });
      }
      // One full runModels pass on the COMPLETE accumulated field set — after all docs are
      // ingested and server-persisted. Uses getProject (free GET, no extraction) so the
      // signalInputs reflects every field the backend merged across the whole batch.
      try {
        const finalProject = await LinStore.getProject(id);
        if (finalProject) {
          const si = deriveExtendedFields(resolveSimInputs(finalProject));
          if (hasIndex(si.cpi) || hasIndex(si.spi)) {
            await runModels(finalProject, si);
          }
        }
      } catch (e) { /* non-fatal — batch extraction already persisted server-side */ }
      // this project's signals were just (re)computed — clear any sector-changed flag
      try { if (window.LinApp && LinApp.clearSectorDirty) LinApp.clearSectorDirty(id); } catch (e) {}
      reportBatch({ type: "done", summary: summary, projectId: id });
    }
  }

  /* ===========================================================
     Change 2 — signals detail panel (extracted / missing / audit)
     =========================================================== */
  function signalEvents(project) {
    const evs = (project && Array.isArray(project.events)) ? project.events : [];
    return evs.filter((e) => {
      const t = e.type || e.event || e.kind || "";
      return t === "signals_extracted" || t === "signal_overwritten" || t === "baseline_adjusted_eot";
    });
  }

  /* An EVM index counts as "present" only if it's a real positive number —
     null / "" / 0 do not qualify (Number(null) is 0, hence the explicit guard). */
  function hasIndex(v) {
    return v != null && v !== "" && Number.isFinite(Number(v)) && Number(v) > 0;
  }

  /* Merge the backend's computed CPI/SPI (resp.computed) into the extracted
     signalInputs so the ledger and the model run read every value from one
     object. computed wins for cpi/spi; signalInputs supplies everything else. */
  function mergeComputed(resp) {
    const si = (resp && (resp.signalInputs || resp.signals)) || {};
    const computed = (resp && resp.computed) || {};
    const merged = Object.assign({}, si);
    if (computed.cpi != null) merged.cpi = computed.cpi;
    if (computed.spi != null) merged.spi = computed.spi;
    return merged;
  }

  /* Pull the read-only extracted periods from an extract response (the backend
     reads these from the document itself — they are display-only, never input). */
  function extractDates(resp, si) {
    const out = {};
    const KEYS = ["baselineStart", "baselineEnd", "workPeriodFrom", "workPeriodTo"];
    const take = (obj) => { if (obj) KEYS.forEach((k) => { if (obj[k] != null && obj[k] !== "") out[k] = obj[k]; }); };
    take(si); take(resp); take(resp && resp.dates); take(resp && resp.periods);
    return out;
  }

  function datesBlockHtml(dates) {
    if (!dates) return "";
    const rows = [];
    if (dates.baselineStart || dates.baselineEnd) {
      rows.push(`<tr><td class="ds-field-name">Baseline period (from contract)</td>
        <td class="ds-field-val">${esc(dates.baselineStart || "?")} → ${esc(dates.baselineEnd || "?")}</td></tr>`);
    }
    if (dates.workPeriodFrom || dates.workPeriodTo) {
      rows.push(`<tr><td class="ds-field-name">Work period (from pay application)</td>
        <td class="ds-field-val">${esc(dates.workPeriodFrom || "?")} → ${esc(dates.workPeriodTo || "?")}</td></tr>`);
    }
    if (!rows.length) return "";
    return `<div class="ds-block">
      <p class="eyebrow">Extracted periods (read-only)</p>
      <table class="ds-table ds-dates-table"><tbody>${rows.join("")}</tbody></table>
    </div>`;
  }

  // A grey [est.] badge for a field whose latest source is a 'derived' estimate.
  function fieldBadge(si, key) {
    if (!si || !si.sources || !si.sources[key]) return "";
    if (si.sources[key].docType === "derived")
      return `<span class="badge-est" title="Estimated from existing documents">est.</span>`;
    return "";
  }
  function humanizeKey(k) {
    return String(k)
      .replace(/([A-Z])/g, " $1")
      .replace(/\bPct\b/g, "%")
      .replace(/^./, (c) => c.toUpperCase())
      .trim();
  }

  function extractedTableHtml(si) {
    const rows = FIELD_ROWS.map((f) => {
      const raw = si ? si[f.key] : undefined;
      const has = raw != null && raw !== "";
      const val = has ? fmtNum(raw) : "—";
      // Traceability link: field ← doc. Latest sources entry carries docType + date.
      const srcEntry = latestSource(si, f.key);
      const src = srcEntry ? (srcEntry.docType || srcEntry.doc || srcEntry.type || null) : null;
      const srcDate = srcEntry && srcEntry.at ? fmtDate(srcEntry.at) : "";
      const srcTag = src
        ? `<span class="ds-src">via ${esc(DOC_TYPE_LABEL[src] || src)}${srcDate ? " · " + esc(srcDate) : ""}</span>`
        : "";
      const mark = has ? `<span class="ds-extracted" title="extracted">✓ extracted</span>` : "";
      const pencil = (f.editable && has)
        ? `<button class="ds-overwrite" data-field="${f.key}" aria-label="Overwrite ${esc(f.label)}" title="Overwrite">✎</button>`
        : "";
      return `<tr class="ds-row ${has ? "" : "ds-row-empty"}">
        <td class="ds-field-name">${esc(f.label)}</td>
        <td class="ds-field-val">${esc(val)} ${fieldBadge(si, f.key)}</td>
        <td class="ds-field-src">${mark} ${srcTag}</td>
        <td class="ds-field-edit">${pencil}</td>
      </tr>${signalChangeLogHtml(si, f.key)}`;
    }).join("");
    return `<table class="ds-table">
      <thead><tr><th>Signal input</th><th>Value</th><th>Source</th><th></th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
  }

  // Derived-estimate fields (docType 'derived' in si.sources), shown below the
  // extracted table so the PM sees what was estimated vs. read from a document.
  function derivedEstimatesHtml(si) {
    if (!si || !si.sources) return "";
    const keys = Object.keys(si.sources).filter((k) =>
      si.sources[k] && si.sources[k].docType === "derived" && si[k] != null);
    if (!keys.length) return "";
    const rows = keys.map((k) => {
      const src = si.sources[k];
      return `<tr class="ds-row">
        <td class="ds-field-name">${esc(humanizeKey(k))} <span class="badge-est" title="${esc(src.note || "derived")}">est.</span></td>
        <td class="ds-field-val">${esc(fmtNum(si[k]))}</td>
        <td class="ds-field-src"><span class="ds-src">${esc(src.note || "derived")}</span></td>
      </tr>`;
    }).join("");
    return `<div class="ds-block">
      <p class="eyebrow">Derived estimates <span class="badge-est">est.</span></p>
      <p class="kn-sub">Estimated from existing documents using industry-standard ratios so more modules can compute. Upload the specific report to replace an estimate with exact figures.</p>
      <table class="ds-table">
        <thead><tr><th>Field</th><th>Value</th><th>Basis</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
  }

  function signalChangeLogHtml(si, key) {
    const log = sourceLog(si, key).slice().sort((a, b) =>
      new Date(a.at || 0).getTime() - new Date(b.at || 0).getTime());
    if (!log.length) {
      return `<tr class="ds-source-row"><td></td><td colspan="3"><span class="ds-source-empty">No changes recorded.</span></td></tr>`;
    }
    const last = log.length - 1;
    const rows = log.map((entry, i) => {
      const when = entry.at ? fmtDate(entry.at) : "unknown time";
      const val = fmtNum(entry.value);
      const doc = entry.docType ? (DOC_TYPE_LABEL[entry.docType] || entry.docType) : "Unknown source";
      const bits = [doc];
      if (entry.fileName) bits.push(entry.fileName);
      if (entry.reason) bits.push(entry.reason);
      return `<div class="ds-source-entry${i === last ? " is-current" : ""}">
        <span>${esc(when)}</span>
        <strong>${esc(val == null ? "—" : val)}</strong>
        <em>${esc(bits.join(" · "))}</em>
        ${i === last ? `<b>current</b>` : ""}
      </div>`;
    }).join("");
    return `<tr class="ds-source-row"><td></td><td colspan="3">
      <div class="ds-source-log"><span class="ds-source-title">Change log</span>${rows}</div>
    </td></tr>`;
  }

  function missingHtml(missing) {
    if (!missing || !missing.length) {
      return `<p class="kn-sub ds-missing-clear">All required values present — nothing outstanding.</p>`;
    }
    const items = missing.map((m) => {
      if (typeof m === "string") return `<li class="ds-missing-row">${esc(m)}</li>`;
      const what = m.label || m.fields || m.field || "Missing value";
      // backend may give a ready-made instruction (`note`, e.g. "Upload Schedule
      // of Values") or just a doc reference we phrase as "Upload <doc>".
      const doc = m.requiredDoc || m.docLabel || (m.docType && DOC_TYPE_LABEL[m.docType]) || m.doc || "";
      const instruction = m.note ? esc(m.note) : (doc ? `Upload ${esc(doc)}` : "");
      return `<li class="ds-missing-row">${esc(what)}${instruction ? ` — <span class="ds-missing-doc">${instruction}</span>` : ""}</li>`;
    }).join("");
    return `<ul class="ds-missing-list">${items}</ul>`;
  }

  function auditTrailHtml(project) {
    const evs = signalEvents(project).slice().reverse(); // most recent first
    if (!evs.length) return `<p class="kn-sub">No signal extraction or override events yet for this project.</p>`;
    return `<ul class="ds-audit-list">` + evs.map((e) => {
      const t = e.type || e.event || e.kind || "";
      const when = fmtDate(e.at || e.timestamp || e.recordedAt || e.time || "");
      if (t === "signal_overwritten") {
        const field = e.field || "(field)";
        const from = e.from != null ? fmtNum(e.from) : "—";
        const to = e.to != null ? fmtNum(e.to) : (e.value != null ? fmtNum(e.value) : "—");
        const reason = e.reason || "(no reason given)";
        return `<li class="ds-audit-row ds-audit-overwrite">
          <span class="ds-audit-main">Overwrote <strong>${esc(field)}</strong>: ${esc(from)} → ${esc(to)} — reason: “${esc(reason)}”</span>
          <span class="ds-audit-time">${esc(when)}</span></li>`;
      }
      if (t === "baseline_adjusted_eot") {
        const from = e.from != null ? e.from : "?";
        const to = e.to != null ? e.to : "?";
        return `<li class="ds-audit-row ds-audit-eot">
          <span class="ds-audit-main">Baseline completion adjusted <strong>${esc(from)}</strong> → <strong>${esc(to)}</strong> via change order (EOT)</span>
          <span class="ds-audit-time">${esc(when)}</span></li>`;
      }
      // signals_extracted — "Signals extracted from [docType] — applied: [applied fields]"
      const appliedSrc = e.applied != null ? e.applied : (e.fields != null ? e.fields : e.field);
      const applied = Array.isArray(appliedSrc) ? appliedSrc.join(", ") : (appliedSrc || "signals");
      const docTypeLabel = e.docType ? (DOC_TYPE_LABEL[e.docType] || e.docType) : "document";
      return `<li class="ds-audit-row ds-audit-extract">
        <span class="ds-audit-main">Signals extracted from <strong>${esc(docTypeLabel)}</strong> — applied: ${esc(applied)}</span>
        <span class="ds-audit-time">${esc(when)}</span></li>`;
    }).join("") + `</ul>`;
  }

  function panelInnerHtml(project) {
    const id = project ? project.id : "";
    const entry = cache[id] || {};
    // Fall back to the persisted signalInputs (with its sources ledger) so the
    // field ← doc traceability renders even without a same-session extraction.
    const persisted = project && project.signalInputs;
    const persistedHasData = !!(persisted && Object.keys(persisted).some(
      (k) => k !== "sources" && persisted[k] != null && persisted[k] !== ""));
    const si = entry.signalInputs || (persistedHasData ? persisted : null);
    const missing = entry.missing || [];
    const dates = entry.dates || null;
    if (!si && !signalEvents(project).length) {
      return `<p class="kn-sub">No documents ingested for this project yet. Upload a document above to extract its signals.</p>`;
    }
    return `
      <div class="ds-block">
        <p class="eyebrow">Extracted signal inputs</p>
        ${si ? extractedTableHtml(si) : `<p class="kn-sub">No extracted values cached this session. Re-upload a document to view them.</p>`}
      </div>
      ${si ? derivedEstimatesHtml(si) : ""}
      ${datesBlockHtml(dates)}
      <div class="ds-block">
        <p class="eyebrow">Missing values &amp; required documents</p>
        ${missingHtml(missing)}
      </div>
      <div class="ds-block">
        <p class="eyebrow">Audit trail</p>
        ${auditTrailHtml(project)}
      </div>`;
  }

  /* Renders the collapsed "Details" panel into a container. */
  function renderSignalsPanel(container, project) {
    if (!container) return;
    container.innerHTML =
      `<details class="kn-topic ds-panel">
         <summary>Details — extracted signals, missing values, and audit trail</summary>
         <div class="ds-panel-body">${panelInnerHtml(project)}</div>
       </details>`;
    wirePanel(container, project);
  }

  function wirePanel(container, project) {
    const body = container.querySelector(".ds-panel-body");
    if (!body) return;
    body.querySelectorAll(".ds-overwrite").forEach((btn) =>
      btn.addEventListener("click", () => openOverwriteEditor(btn, container, project)));
  }

  /* ===========================================================
     Change 4 — overwrite editor + auto-re-run
     =========================================================== */
  function openOverwriteEditor(btn, container, project) {
    const field = btn.dataset.field;
    const row = btn.closest("tr");
    if (!row || row.nextElementSibling && row.nextElementSibling.classList.contains("ds-edit-row")) return;
    const id = project.id;
    const cur = (cache[id] && cache[id].signalInputs && cache[id].signalInputs[field]);
    const editor = document.createElement("tr");
    editor.className = "ds-edit-row";
    editor.innerHTML = `<td colspan="4">
      <div class="ds-editor">
        <label class="rationale-label">New value
          <input type="number" step="any" class="ds-edit-value ig-input" value="${esc(cur != null ? cur : "")}" /></label>
        <label class="rationale-label">Reason (required)
          <input type="text" class="ds-edit-reason ig-input" placeholder="Why is this corrected? (recorded to the audit trail)" /></label>
        <div class="dc-actions">
          <button class="btn primary ds-edit-save">Save</button>
          <button class="btn ds-edit-cancel">Cancel</button>
        </div>
        <p class="ds-edit-msg kn-sub" aria-live="polite"></p>
      </div></td>`;
    row.insertAdjacentElement("afterend", editor);

    editor.querySelector(".ds-edit-cancel").addEventListener("click", () => editor.remove());
    editor.querySelector(".ds-edit-save").addEventListener("click", async () => {
      const value = editor.querySelector(".ds-edit-value").value;
      const reason = editor.querySelector(".ds-edit-reason").value.trim();
      const msg = editor.querySelector(".ds-edit-msg");
      if (value === "" || !Number.isFinite(Number(value))) { msg.textContent = "Enter a valid number."; return; }
      if (reason.length < 3) { msg.textContent = "A short reason is required (min 3 characters)."; return; }
      const save = editor.querySelector(".ds-edit-save");
      save.disabled = true;
      msg.textContent = "Saving correction and re-running models…";
      try {
        const resp = await LinStore.overwriteSignal({ id, field, value: Number(value), reason });
        const si = (resp.signalInputs || resp.signals)
          ? mergeComputed(resp)
          : (cache[id] && cache[id].signalInputs) || {};
        appendSourceEntry(si, field, Number(value), "manual_override", null, reason || "Manual override by PM");
        const missing = resp.missing || (cache[id] && cache[id].missing) || [];
        const readyToRun = resp.readyToRun != null ? !!resp.readyToRun
          : (Number.isFinite(Number(si.cpi)) && Number.isFinite(Number(si.spi)));
        // preserve extracted periods (overwrite responses don't re-send them)
        const dates = Object.assign({}, (cache[id] && cache[id].dates) || {}, extractDates(resp, si));
        cache[id] = { signalInputs: si, missing, readyToRun, dates };

        // re-run when EITHER index is present (consistent with the extract path)
        const canCompute = hasIndex(si.cpi) || hasIndex(si.spi);
        if (canCompute) await runModels(project, si);
        const fresh = await refreshProject(id);
        // re-render the whole panel (values + audit trail) and the app/ledger
        renderSignalsPanel(container, fresh || project);
        if (window.LinApp) LinApp.refresh();
        if (window.LinDetail && LinApp && LinApp.getSelectedId && LinApp.getSelectedId() === id) {
          // detail page may be open — refresh its ledger/decision via re-render
          LinDetail.render(id);
        }
      } catch (e) {
        msg.textContent = "Overwrite failed: " + (e && e.message ? e.message : "store unreachable") + ".";
        save.disabled = false;
      }
    });
  }

  window.LinSignals = {
    ingestFormHtml, wireIngestForm,
    dropzoneHtml, wireDropzone,
    renderSignalsPanel,
    buildHistorySnapshot,
    persistHistorySnapshot,
    buildCategorySnapshot,
    ensureSimulations,
    runModels,
    portfolioVector, runPortfolioAnalysis,
    resolveSimInputs,
    deriveExtendedFields,
    DOC_TYPES, DOC_TYPE_LABEL,
    clearCache
  };
})();