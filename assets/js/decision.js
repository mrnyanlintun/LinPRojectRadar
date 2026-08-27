/* ============================================================
   Lin Project Radar — decision.js
   PCEIF Layer-2 governance rules (pure functions, no DOM)
   ------------------------------------------------------------
   This file is intentionally readable: it is the demonstration
   that PCEIF decision logic is explicit, auditable rules — not
   model output and not informal judgment. Every function here
   is deterministic and side-effect free.

   Plain globals (not ES modules) so the site also runs from
   file:// where module imports are blocked by CORS.
   ============================================================ */

const PCEIF_VERSION = "L2-v0.5-demo";

/* 5-status palette (Complete / Green / Yellow / Amber / Red). Kept on the
   global so renderers can read both the canonical label set and the hex
   palette without duplicating it. */
const PCEIF_STATUS_LABELS = ["Complete", "Green", "Yellow", "Amber", "Red"];
const PCEIF_STATUS_HEX = (function () {
  /* Resolved from the ONE palette: radar.css --status-* → config.js
     LIN_STATUS_COLORS. The literals here are a last-ditch fallback for
     running this file without config.js (e.g. a bare unit harness). */
  var c = (typeof window !== "undefined" && window.LIN_STATUS_COLORS) || {};
  return {
    Complete: c.Complete || "#4ea0ff",
    Green:    c.Green    || "#2ee66b",
    Yellow:   c.Yellow   || "#ffe066",
    Amber:    c.Amber    || "#ff8c1a",
    Red:      c.Red      || "#ff3b30"
  };
})();
const DATA_BOUNDARY =
  "Synthetic demonstration data only; not a validated production system.";

/* ------------------------------------------------------------
   1. Signal status extraction
   ------------------------------------------------------------ */
function signalStatuses(project) {
  const s = (project && project.signals) || {};
  const out = {
    evm:   s.evm   ? s.evm.status   : null,
    mc:    s.mc    ? s.mc.status    : null,
    cusum: s.cusum ? s.cusum.status : null,
    doc:   s.doc   ? s.doc.status   : null
  };
  // Server-computed projects carry no legacy p.signals blob, so the four per-signal-class
  // statuses above are all null and classifyConflict falls to "Signal breakdown not available".
  // The same breakdown is recoverable from the STORED row: earned-value bands from
  // signal_inputs (CPI/SPI, document risk) and the Monte Carlo / CUSUM module statuses from
  // module_results, read through the shared resolver. This reads the stored answer; it does not
  // recompute one. Only fill the classes still missing, so a real p.signals blob always wins.
  const stored = storedSignalStatuses(project);
  if (stored) {
    ["evm", "mc", "cusum", "doc"].forEach((k) => { if (out[k] == null && stored[k] != null) out[k] = stored[k]; });
  }
  return out;
}

/* The four signal-class statuses derived from the stored computed row, or null when the project
   has no stored result. Returned as lowercase band words ("red"/"amber"/"yellow"/"green") to
   match the comparisons classifyConflict / countStatus make. A class with no stored basis stays
   null — an abstaining signal class, never a fabricated "green". */
function storedSignalStatuses(project) {
  /* RUN 69, SECTION 7.2. THE FOUR SIGNAL-CLASS BANDS ARE READ, NOT DERIVED.

     WHAT THIS FUNCTION USED TO DO: `evm` was `deriveStatusFromMetrics(si.cpi, si.spi, null)`
     and `doc` was `deriveStatusFromMetrics(null, null, si.docRiskScore)` -- RAG thresholds
     applied IN THE BROWSER to raw stored indices, producing a band no module computed and no
     row stores. On this platform's own fixture a stored CPI of 0.952 came out GREEN here while
     A1.7 TCPI and A1.8 VAC, the two modules that actually vote on cost, both stored AMBER, and
     the conflict classification below then compared an invented band against real ones.

     `mc` and `cusum` were already read off stored module rows through `getModuleStatus`. All
     four now are. A class with no stored band stays null -- an abstaining class, never a
     fabricated one -- which is what `classifyConflict` and `countStatus` already expect. */
  const row = (typeof window !== "undefined" && window.LinResults && window.LinResults.rowFor)
    ? window.LinResults.rowFor(project) : null;
  if (!row) return null;
  const modBand = (methodClass) => {
    const st = (typeof window !== "undefined" && window.getModuleStatus)
      ? window.getModuleStatus(methodClass, project) : null;
    const norm = normalizeStatusLabel(st);
    return norm ? norm.toLowerCase() : null;
  };
  /* THE COST-AND-SCHEDULE CLASS IS THE STORED BAND OF THE MODULES THAT VOTE ON IT. Where the
     two disagree the more adverse STORED band stands for the class; that is a choice between
     two values the server computed, not a band manufactured from an index. Where neither
     stored one, the class is null. */
  const RANK = { green: 0, yellow: 1, amber: 2, "red-review": 3, red: 4, complete: -1 };
  const worstOfStored = (classes) => {
    let best = null;
    classes.forEach((c) => {
      const b = modBand(c);
      if (!b) return;
      if (best === null || (RANK[b] != null && RANK[best] != null && RANK[b] > RANK[best])) best = b;
    });
    return best;
  };
  const evm = worstOfStored(["TCPI", "VAC"]);
  const doc = modBand("Doc_Risk");
  const mc = modBand("Monte_Carlo");
  const cusum = modBand("CUSUM");
  if (evm == null && doc == null && mc == null && cusum == null) return null;
  return { evm, mc, cusum, doc };
}

function countStatus(statuses, level) {
  return Object.values(statuses).filter((v) => v === level).length;
}

/* ------------------------------------------------------------
   1b. Status normalization (5-status system)
   ------------------------------------------------------------
   PCEIF uses five status levels — Complete (blue), Green, Yellow,
   Amber, Red. Sources upstream may still emit "Red-review" or
   "Critical"; these normalize to "Red". "Light-amber" normalizes
   to "Yellow". Anything else falls back to its lowercased label.
   ------------------------------------------------------------ */
function normalizeStatusLabel(status) {
  const s = String(status || "").toLowerCase();
  if (s === "complete" || s === "blue") return "Complete";
  if (s === "green") return "Green";
  if (s === "yellow" || s === "light-amber" || s === "lightamber") return "Yellow";
  if (s === "amber" || s === "orange") return "Amber";
  if (s === "red" || s === "red-review" || s === "redreview" || s === "critical") return "Red";
  return null;
}

/* ------------------------------------------------------------
   1c. Slim-list status (portfolio glance, no full signals object)
   ------------------------------------------------------------
   The slim portfolio list (v10.28 ?action=listslim) carries EVM
   summary fields but no signals object. When the backend supplies a
   real 5-status label, use it; otherwise derive a conservative
   worst-of band from CPI / SPI using the same RAG thresholds the
   modules use (≥0.95 Green, ≥0.90 Amber, else Red). Doc-risk is only
   folded in when it is a valid normalized score in [0, 1] (the slim
   docRiskScore field carries inconsistent scales — raw counts as well
   as 0–1 scores — so out-of-range values are ignored). Returns null
   when there are no EVM metrics — i.e. genuinely awaiting ingest.
   ------------------------------------------------------------ */
/* RUN 69. RETIRED, NOT DELETED. Nothing on a served page calls this any more: both call sites
   (`storedSignalStatuses` and `slimStatusLabel`) now read the band the server stored. It stays
   here, unreferenced, because tests.html pins its arithmetic and because deleting a check is
   forbidden; retiring one means it stops running and the reason is recorded, which is this
   comment. DO NOT WIRE IT BACK INTO A RENDER PATH: a band it returns is one no module computed. */
function deriveStatusFromMetrics(cpi, spi, docRisk) {
  let worst = -1;                 // 0 Green, 1 Amber, 2 Red
  const bump = (n) => { if (n > worst) worst = n; };
  [cpi, spi].forEach((v) => {
    const n = Number(v);
    if (Number.isFinite(n) && n > 0) bump(n >= 0.95 ? 0 : n >= 0.90 ? 1 : 2);
  });
  if (docRisk != null) {   // guard: Number(null) is 0, which would falsely read as Green
    const d = Number(docRisk);
    if (Number.isFinite(d) && d >= 0 && d <= 1) bump(d < 0.30 ? 0 : d < 0.70 ? 1 : 2);
  }
  return worst < 0 ? null : ["Green", "Amber", "Red"][worst];
}
function slimStatusLabel(p) {
  /* RUN 69, SECTION 7.2. THE SLIM LIST'S BAND IS READ, NOT DERIVED.

     The second arm used to be `deriveStatusFromMetrics(p.cpi, p.spi, docRisk)` -- RAG
     thresholds applied in the browser to whatever indices the slim projection happened to
     carry, producing a portfolio-list colour for a project whose stored result says something
     else, or has no status at all. The slim projection DOES carry the server's answer: the
     list/get projection attaches `storedResult` with `project_status` on it, and `p.status` is
     the persisted label. Both are read; neither is computed.

     A project the server has given no status is now "not yet analysed" on the list, which is
     what it is. A colour is never supplied in place of an absent one. */
  if (!p) return null;
  const norm = normalizeStatusLabel(p.status);   // the persisted 5-state label, where there is one
  if (norm) return norm;
  const stored = p.storedResult || null;
  return stored ? normalizeStatusLabel(stored.project_status) : null;
}

/* ------------------------------------------------------------
   2. Signal-conflict classification
   ------------------------------------------------------------
   PCEIF surfaces disagreement between signal classes instead of
   averaging it away. Precedence order matters and is deliberate:

   (1) Multi-signal red-review   — two or more red signals: the
       severity question dominates any single-conflict label.
   (2) Anomaly without narrative — trend rules (CUSUM) breached
       while the document record offers no explanation. The gap
       between the numbers and the narrative IS the finding.
   (3) Forecast ahead of status  — probabilistic forecast is red
       while current EVM is not: foresight precedes variance.
   (4) Leading document risk     — text evidence (RFIs, QC,
       submittals, procurement) deteriorates before CPI/SPI.
   (5) Agreement — low risk      — every signal class is green.
   (6) Mixed early warning       — residual amber combinations.
   ------------------------------------------------------------ */
function classifyConflict(project) {
  const s = signalStatuses(project);
  // T12b. signalStatuses() already guards a missing project.signals down to nulls, but this
  // function used to read project.signals.cusum.breached directly, unguarded, one line below.
  // That was safe only because every caller was gated on hasSignals(project) first. Once that
  // gate is corrected to ask about the STORED row instead of this legacy blob, a project that
  // has been analysed server-side and carries no p.signals reaches this function and the direct
  // read throws. Guarded here the same way deriveHealthState's client-side fallback arm already
  // guards the identical field.
  const cusumBreached = !!(project && project.signals && project.signals.cusum
    && project.signals.cusum.breached);

  // No legacy per-signal breakdown at all: every value in s is null, and none of the branches
  // below can honestly distinguish "Agreement: low risk" from "Mixed early warning" without it.
  // Falling through to "Mixed early warning" would report a specific finding the platform has no
  // basis for. This is the classification a project with a stored server result and no such
  // breakdown gets: honest about not being available, rather than a guess dressed as an answer.
  if (Object.values(s).every((v) => v === null)) return "Signal breakdown not available";

  const reds = countStatus(s, "red");
  if (reds >= 2) return "Multi-signal red-review";
  if (cusumBreached && s.doc === "green") return "Anomaly without narrative";
  if (s.mc === "red" && s.evm !== "red") return "Forecast ahead of status";
  if ((s.doc === "amber" || s.doc === "red") && s.evm === "green")
    return "Leading document risk";
  if (Object.values(s).every((v) => v === "green")) return "Agreement: low risk";
  return "Mixed early warning";
}

/* ------------------------------------------------------------
   3. Health-state synthesis
   ------------------------------------------------------------
   Green       — all signal classes green.
   Red-review  — two or more red signals, OR a breached trend
                 rule combined with a red probabilistic forecast.
                 "Red-review" deliberately means: the evidence
                 package has crossed the threshold for accountable
                 HUMAN review. It never means automatic action.
   Amber       — every other early-warning combination.
   ------------------------------------------------------------ */
function deriveHealthState(project) {
  // The status is the one the server computed and stored. getProjectFusion reads that row.
  try {
    if (typeof window !== "undefined" && window.getProjectFusion) {
      const f = window.getProjectFusion(project);
      if (f && f.status) return f.status;
      // A stored row exists and carries no status: say so, do not invent one.
      if (f && f.stored) return "Awaiting analysis";
    }
  } catch (e) { /* fall through */ }

  // NO STORED ROW, AND DELIBERATELY NO FALLBACK DERIVATION.
  //
  // This used to fall through to the signal-class rule below, deriving a status in the browser
  // from project.signals. That derivation is what produced Red on projects five per cent under
  // budget, in 40 of 40 seeds, because the signals it read had been built from a synthesised
  // time series. Falling back to it would mean a project whose analysis has not been run gets a
  // confident colour anyway, and a wrong one.
  //
  // "Awaiting analysis" is the honest answer for a project with no computed result: it has not
  // been analysed, which is a different thing from being healthy and a different thing again
  // from being at risk.
  if (typeof window !== "undefined" && window.LinResults) return "Awaiting analysis";

  // Retained for the researcher-side deep-dive route, which loads categories.js and simulations.js
  // deliberately and re-runs the models live to show its working. LinResults is absent there, so
  // this arm is reachable only from that surface.
  const s = signalStatuses(project);
  const reds = countStatus(s, "red");
  const ambers = countStatus(s, "amber");
  const cusumBreached = !!(project && project.signals && project.signals.cusum && project.signals.cusum.breached);

  if (reds === 0 && ambers === 0) return "Green";
  if (reds >= 2 || (cusumBreached && s.mc === "red")) return "Red-review";
  return "Amber";
}

/* Display-label helper. Returns deriveHealthState as-is — kept as a stable
   hook for the UI so renderers can adopt new labels later without breaking
   the core 3-state engine. */
function deriveHealthStateLabel(project) {
  return deriveHealthState(project);
}

/* ------------------------------------------------------------
   4. Decision derivation — the PCEIF escalation matrix
   ------------------------------------------------------------
   Maps (health state x conflict type x fairness sensitivity) to
   a RECOMMENDED action, the authority role entitled to act, the
   documentation required, and whether the contractor fairness
   gate must be satisfied before any formal step.

   The output is a recommendation. A named human reviewer must
   record a rationale before the decision enters the audit log,
   and the fairness gate — where required — blocks recording
   until contractor response opportunity is acknowledged.
   ------------------------------------------------------------ */
function deriveDecision(project) {
  const healthState = deriveHealthState(project);
  const conflictType = classifyConflict(project);
  // The fused "Red" band IS the escalation tier — it replaced the old
  // "Red-review" STATUS (which the DST rollup no longer emits; high category
  // disagreement is now a separate advisory flag). The signal-class fallback
  // can still emit "Red-review" for sparse projects, so route both here.
  const escalate = healthState === "Red" || healthState === "Red-review";
  const fairnessGateRequired = escalate && project.fairnessSensitive === true;

  let action, authority, documentation;

  if (healthState === "Complete") {
    action = "Project complete: proceed to close-out and any liability-period monitoring";
    authority = "Project manager / Controls lead";
    documentation = "Close-out record; monitor through the defects-liability period where applicable";
  } else if (healthState === "Green") {
    action = "Routine monitoring";
    authority = "Project manager / Controls lead";
    documentation = "Monthly signal log entry";
  } else if (escalate) {
    action = fairnessGateRequired
      ? "Request contractor explanation and recovery-plan review; fairness gate required before any formal action"
      : "Recovery-plan review and management escalation";
    authority = fairnessGateRequired
      ? "Program director / PMO with contract-administration awareness"
      : "Program director / PMO lead";
    documentation =
      "Full signal package, assigned owner, rationale, response timeframe, audit record";
  } else {
    // Yellow / Amber early-warning sub-cases keyed to the conflict type
    if (conflictType === "Forecast ahead of status") {
      action = "Investigate forecast assumptions and mitigation options";
    } else if (conflictType === "Anomaly without narrative") {
      action = "Controls review: request explanation for unexplained trend drift";
    } else if (conflictType === "Leading document risk") {
      action = "Early-warning review; verify document evidence; update risk register";
    } else {
      action = "Early-warning review; update risk register; set follow-up date";
    }
    authority = "Project manager + Project controls lead";
    documentation = "Risk-register update, rationale, follow-up date";
  }

  return { healthState, conflictType, action, authority, documentation, fairnessGateRequired };
}

/* ------------------------------------------------------------
   4b. Signal-traced action plan
   ------------------------------------------------------------
   Deterministic what/who/how/when/inform rules per category.
   Every row is traced to the exact category (or module) that
   triggered it — never free text, never model output. A reviewer
   can read: "this row exists because Cat 3 Cost is Amber."
   ------------------------------------------------------------ */
const CATEGORY_ACTIONS = {
  cat1: {
    what: "Investigate cost/schedule variance drivers",
    who: "Project Controls Lead",
    how: "Reconcile EV/AC/PV against pay applications and schedule updates; verify data date alignment; identify top 3 variance work packages",
    when: { Yellow: "Next monthly cycle", Amber: "Within 10 business days", Red: "Within 48 business hours" },
    inform: "Project Manager; Program Manager if Red"
  },
  cat2: {
    what: "Adjust schedule and recover float",
    who: "Scheduler + Project Manager",
    how: "Re-sequence near-critical activities; verify look-ahead constraints are being cleared; evaluate compression options (crash/fast-track) with cost trade-off",
    when: { Yellow: "Next schedule update", Amber: "Within 2 weekly cycles", Red: "Immediate recovery-schedule workshop" },
    inform: "Owner's representative; affected trade contractors"
  },
  cat3: {
    what: "Control budget and contingency burn",
    who: "Cost Engineer + Project Controls Lead",
    how: "Freeze non-essential commitments; review contingency drawdown vs % complete; re-forecast EAC using current productivity; validate pending change orders",
    when: { Yellow: "Next cost report", Amber: "Within 10 business days", Red: "Within 48 business hours" },
    inform: "Project Manager; Finance/PMO if Red"
  },
  cat4: {
    what: "Resolve open RFIs, submittals, and technical issues",
    who: "Design Manager + Document Controller",
    how: "Prioritize overdue RFIs by schedule impact; expedite rejected submittal resubmissions; escalate unresolved technical conflicts to the design team; update risk register",
    when: { Yellow: "Within 2 weeks", Amber: "Within 1 week", Red: "Daily standup until cleared" },
    inform: "Architect/Engineer of record; affected subcontractors"
  },
  cat5: {
    what: "Break rework and cascade loops",
    who: "Project Manager + Design Manager",
    how: "Identify the propagation source (design change, rework feedback); contain scope of affected work packages; sequence corrective work to avoid re-triggering",
    when: { Yellow: "Next coordination meeting", Amber: "Within 1 week", Red: "Immediate containment review" },
    inform: "All affected discipline leads"
  },
  cat6: {
    what: "Reconcile disagreeing signal classes",
    who: "Project Controls Lead",
    how: "Review which synthesis rules disagree (conservative vs weighted); verify underlying data quality before acting on the composite",
    when: { any: "Before next governance decision" },
    inform: "Project Manager"
  },
  cat7: {
    what: "Investigate evidence conflict before acting",
    who: "Project Controls Lead + Reviewer",
    how: "Check the conflict coefficient K; identify which evidence methods dissent and why; do not record a decision until conflict is explained",
    when: { any: "Before next governance decision" },
    inform: "Named decision reviewer"
  },
  cat8: {
    what: "Review portfolio anomaly signals",
    who: "PMO Analyst",
    how: "Compare this project's trajectory against portfolio peers; verify anomaly is real (not data artifact); document explanation or corrective plan",
    when: { Yellow: "Next portfolio review", Amber: "Within 2 weeks", Red: "Within 1 week" },
    inform: "Program Manager"
  },
  cat9: {
    what: "Address compliance threshold breaches",
    who: "Project Manager + Contract Administrator",
    how: "Identify which gate breached (EVM threshold, safety, quality, environmental); execute the prescribed regulatory response; document corrective action",
    when: { Yellow: "Next reporting cycle", Amber: "Within 5 business days", Red: "Immediate; regulatory clock may be running" },
    inform: "Contracting Officer / Executive as required by the gate"
  },
  cat10: {
    what: "Fix data quality before trusting signals",
    who: "Document Controller + Project Controls Lead",
    how: "Locate missing/stale fields flagged by the integrity modules; re-upload or correct source documents; re-run signals after correction",
    when: { any: "Before acting on any other signal" },
    inform: "Project Manager"
  },
  cat11: {
    what: "Re-evaluate decision trade-offs",
    who: "Project Manager",
    how: "Review the optimization ranking against current constraints; confirm the recommended option still dominates under updated signals",
    when: { any: "Next decision point" },
    inform: "PMO"
  }
};

function deriveActionPlan(project) {
  const rows = [];
  const cats = (typeof window !== "undefined" && window.LIN_CATEGORIES) || [];
  const triggeredCatKeys = {};

  // 1. One row per Yellow/Amber/Red category (DST-fused status)
  cats.forEach((c) => {
    let st = null;
    try {
      if (window.getCategoryStatus) st = window.getCategoryStatus(c.id, project);
    } catch (e) {}
    const sev = normalizeStatusLabel(st);
    if (sev !== "Yellow" && sev !== "Amber" && sev !== "Red") return;
    const a = CATEGORY_ACTIONS[c.id];
    if (!a) return;
    triggeredCatKeys[c.key] = true;
    rows.push({
      trigger: c.name + ": " + sev,
      severity: sev,
      what: a.what,
      who: a.who,
      how: a.how,
      when: a.when[sev] || a.when.any || "Next reporting cycle",
      inform: a.inform
    });
  });

  // 2. Module-level watch rows: Red modules whose category didn't emit a row
  let fusion = null;
  try {
    if (typeof window !== "undefined" && window.getProjectFusion) fusion = window.getProjectFusion(project);
  } catch (e) {}
  ((fusion && fusion.redFlags) || []).forEach((f) => {
    if (triggeredCatKeys[f.category]) return;
    const cat = cats.find((c) => c.key === f.category);
    const a = cat ? CATEGORY_ACTIONS[cat.id] : null;
    rows.push({
      trigger: f.module + ": Red",
      severity: "Red",
      what: "Investigate red module signal",
      who: a ? a.who : "Project Controls Lead",
      how: "Open the module evidence metric; verify inputs; explain or escalate",
      when: "Within 5 business days",
      inform: a ? a.inform : "Project Manager"
    });
  });

  // 3. NO ALL-CLEAR FALLBACK. An empty plan means nothing was established, not that everything
  //    is fine, and those must not render the same.
  //
  //    There used to be a "All categories Green / Routine monitoring" row here for the empty
  //    case. Both branches above are unreachable today — CATEGORY_ACTIONS is keyed cat1..cat11
  //    while LIN_CATEGORIES ids are a1..d1, so its lookup never matches, and getProjectFusion
  //    has not returned redFlags since taxonomy.js replaced categories.js — so that row was the
  //    ONLY output this function ever produced. It printed "All categories Green" beside a Red
  //    badge on the same card, from a different source than the badge reads.
  //
  //    Returning nothing makes actionPlanHtml render nothing, which is the same abstain-by-
  //    absence contract the project-level modules keep: a module with no evidence is absent from
  //    module_results rather than present with a reassuring value. Restoring an all-clear here
  //    would restore the contradiction.
  return rows;
}

/* ------------------------------------------------------------
   5. Audit-record assembly
   ------------------------------------------------------------ */
function buildAuditRecord(project, decision, reviewerInput) {
  return {
    pceif_version: PCEIF_VERSION,
    data_boundary: DATA_BOUNDARY,
    exported_at: new Date().toISOString(),
    project_id: project.id,
    project_name: project.name,
    reporting_period: project.reportingPeriod,
    signal_package: project.signals,
    derived_decision: {
      health_state: decision.healthState,
      conflict_type: decision.conflictType,
      recommended_action: decision.action,
      authority: decision.authority,
      documentation_required: decision.documentation,
      fairness_gate_required: decision.fairnessGateRequired,
      action_plan: deriveActionPlan(project)
    },
    human_review: {
      rationale: reviewerInput.rationale,
      fairness_gate_acknowledged: reviewerInput.fairnessAcknowledged === true,
      recorded_at: reviewerInput.recordedAt
    }
  };
}
