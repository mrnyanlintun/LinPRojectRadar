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
      fairness_gate_required: decision.fairnessGateRequired
    },
    human_review: {
      rationale: reviewerInput.rationale,
      fairness_gate_acknowledged: reviewerInput.fairnessAcknowledged === true,
      recorded_at: reviewerInput.recordedAt
    }
  };
}
