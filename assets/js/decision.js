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
const PCEIF_STATUS_HEX = {
  Complete: "#4ea0ff",
  Green: "#3fcaa6",
  Yellow: "#f0c040",
  Amber: "#e2b13c",
  Red: "#e0556b"
};
const DATA_BOUNDARY =
  "Synthetic demonstration data only; not a validated production system.";

/* ------------------------------------------------------------
   1. Signal status extraction
   ------------------------------------------------------------ */
function signalStatuses(project) {
  const s = (project && project.signals) || {};
  return {
    evm:   s.evm   ? s.evm.status   : null,
    mc:    s.mc    ? s.mc.status    : null,
    cusum: s.cusum ? s.cusum.status : null,
    doc:   s.doc   ? s.doc.status   : null
  };
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
  const reds = countStatus(s, "red");

  if (reds >= 2) return "Multi-signal red-review";
  if (project.signals.cusum.breached && s.doc === "green")
    return "Anomaly without narrative";
  if (s.mc === "red" && s.evm !== "red") return "Forecast ahead of status";
  if ((s.doc === "amber" || s.doc === "red") && s.evm === "green")
    return "Leading document risk";
  if (Object.values(s).every((v) => v === "green")) return "Agreement — low risk";
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
  // Primary path: Dempster-Shafer category->project fusion (5 states:
  // Complete/Green/Yellow/Amber/Red). High disagreement surfaces as a separate
  // "Red-review" advisory flag (getProjectFusion().redReview), NOT as the status
  // band — no single Red hard-overrides. Falls back to the signal-class rule for
  // sparse projects (signals present but few/no computed category modules).
  try {
    if (typeof window !== "undefined" && window.getProjectFusion) {
      const f = window.getProjectFusion(project);
      if (f && f.status) return f.status;
    }
  } catch (e) { /* fall through to the signal-class rule */ }

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
    action = "Project complete — proceed to close-out and any liability-period monitoring";
    authority = "Project manager / Controls lead";
    documentation = "Close-out record; monitor through the defects-liability period where applicable";
  } else if (healthState === "Green") {
    action = "Routine monitoring";
    authority = "Project manager / Controls lead";
    documentation = "Monthly signal log entry";
  } else if (escalate) {
    action = fairnessGateRequired
      ? "Request contractor explanation and recovery-plan review — fairness gate required before any formal action"
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
      action = "Controls review — request explanation for unexplained trend drift";
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
    when: { Yellow: "Next reporting cycle", Amber: "Within 5 business days", Red: "Immediate — regulatory clock may be running" },
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
  },
  cat12: {
    what: "Verify requirements and interface risks",
    who: "Systems Engineer",
    how: "Trace flagged requirements to affected interfaces; confirm V-model gate criteria before proceeding",
    when: { any: "Before next stage gate" },
    inform: "Design Manager"
  }
};

function deriveActionPlan(project) {
  const rows = [];
  const cats = (typeof window !== "undefined" && window.LIN_CATEGORIES) || [];
  const triggeredCatNums = {};

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
    triggeredCatNums[c.num] = true;
    rows.push({
      trigger: c.num + " " + c.name + " — " + sev,
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
    if (triggeredCatNums[f.category]) return;
    const cat = cats.find((c) => c.num === f.category);
    const a = cat ? CATEGORY_ACTIONS[cat.id] : null;
    rows.push({
      trigger: "Module " + f.num + " " + f.module + " — Red",
      severity: "Red",
      what: "Investigate red module signal",
      who: a ? a.who : "Project Controls Lead",
      how: "Open the module evidence metric; verify inputs; explain or escalate",
      when: "Within 5 business days",
      inform: a ? a.inform : "Project Manager"
    });
  });

  // 3. All Green, no red flags — single routine-monitoring row
  if (!rows.length) {
    rows.push({
      trigger: "All categories Green",
      severity: "Green",
      what: "Routine monitoring",
      who: "Project Manager / Controls Lead",
      how: "Continue monthly signal log; no corrective action indicated",
      when: "Next monthly cycle",
      inform: "—"
    });
  }
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
