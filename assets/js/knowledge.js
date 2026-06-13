/* ============================================================
   Lin Project Radar — knowledge.js
   Curated static knowledge library: PCEIF method definitions,
   module explanations, and the term-definition lens.
   The assistant (assistant.js) draws on this curated library for its
   scripted fallback; the library's static definition + impact text is the
   dependable reference, with a live-AI 'Ask the AI' option per term.
   ============================================================ */

(function () {
  "use strict";

  /* ---------- term lens: click a term → definition ---------- */
  // Each term: definition (what it is), formula, and impact (why a
  // project-controls reviewer cares). Impact is curated static text — it
  // must read correctly even if the AI backend is down.
  const TERMS = [
    { term: "EVM", definition: "Earned Value Management compares planned value, earned value, and actual cost to show cost and schedule performance against the baseline.", formula: "PV, EV, AC",
      impact: "Gives reviewers an objective, normalized read on cost and schedule health instead of gut feel, so problems surface in the numbers before they show up in the field." },
    { term: "PV / Planned Value", definition: "Budgeted value of work planned to be complete by a given date.", formula: "PV = planned budgeted work to date",
      impact: "Sets the yardstick the other EVM measures are read against; if PV is wrong (bad baseline), every derived index is misleading." },
    { term: "EV / Earned Value", definition: "Budgeted value of work actually completed by a given date.", formula: "EV = budgeted value of completed work",
      impact: "Anchors performance to work actually done, not money spent or time elapsed — the core defense against 'we spent the budget so we must be on track.'" },
    { term: "AC / Actual Cost", definition: "Actual cost incurred for completed work by a given date.", formula: "AC = actual cost of performed work",
      impact: "When AC outruns EV the project is paying more than the work is worth; the gap is the early signal of cost inefficiency a reviewer must explain." },
    { term: "CPI", definition: "Cost Performance Index. A value below 1.00 indicates cost inefficiency.", formula: "CPI = EV / AC",
      impact: "A CPI under 1.0 means every dollar is buying less than a dollar of work; it drives the independent EAC (BAC/CPI) and is usually the first metric escalated." },
    { term: "SPI", definition: "Schedule Performance Index. A value below 1.00 indicates schedule underperformance.", formula: "SPI = EV / PV",
      impact: "Flags schedule slippage in cost terms; a sustained SPI below 1.0 is what the CUSUM monitor watches for accumulating drift toward a milestone miss." },
    { term: "BAC", definition: "Budget at Completion. The approved total baseline budget.", formula: "BAC = approved baseline budget",
      impact: "The reference point for overrun: the Monte Carlo P80 is compared against BAC (and its tolerance) to decide whether the forecast is in recovery territory." },
    { term: "EAC", definition: "Estimate at Completion. The forecasted total final project cost.", formula: "EAC ≈ BAC / CPI, or the documented EAC logic used by the module",
      impact: "Turns today's performance into a credible landing cost; a rising EAC is the basis for contingency draws and recovery planning." },
    { term: "P50", definition: "The median or likely simulation forecast.", formula: "P50 = 50th percentile of simulated outcomes",
      impact: "A realistic mid-point estimate; the distance from P50 to P80 shows how much tail risk the project carries, which informs how much contingency to hold." },
    { term: "P80", definition: "The conservative risk-informed forecast: an estimated 80% chance the final cost will be at or below this value.", formula: "P80 = 80th percentile of simulated forecast outcomes",
      impact: "Public programs budget to a conservative percentile; P80 exceeding the BAC tolerance is a direct trigger for escalation and a documented funding conversation." },
    { term: "Monte Carlo", definition: "Transparent uncertainty propagation through repeated simulation draws over uncertain inputs.", formula: "Sample uncertain inputs → outcome distribution",
      impact: "Replaces a single deterministic number with a range and a confidence level, so reviewers can talk about likelihood of overrun rather than a false-precision point estimate." },
    { term: "Bayesian Updating", definition: "A method for revising risk estimates when new evidence arrives.", formula: "Prior + evidence → posterior",
      impact: "Lets a project's risk rating move with new reporting-cycle evidence instead of staying anchored to a stale assumption — the basis for defensible, evolving judgments." },
    { term: "SPC", definition: "Statistical Process Control for monitoring process signals against control thresholds.", formula: "Observed signal vs. control threshold",
      impact: "Separates normal period-to-period noise from a real shift, so reviewers don't over-react to one bad month or miss a slow, steady decline." },
    { term: "CUSUM", definition: "Cumulative Sum logic that detects accumulating drift over time, before a single-period variance would trip a threshold.", formula: "CUSUM = cumulative deviation signal",
      impact: "Catches the slow slide that single-period variance reports hide; a breach hands an early, evidence-backed warning to governance before the trend becomes a crisis." },
    { term: "RFI", definition: "Request for Information. A formal project question or clarification record. Flagged RFIs contribute to document-risk evidence.", formula: "Document evidence input",
      impact: "Clusters of aging or scope-disputed RFIs often predict cost/schedule impact before EVM moves — leading document-risk evidence reviewers should act on early." },
    { term: "RFA", definition: "Request for Approval (or Authorization) — a formal request for a decision or sign-off, e.g. a substitution or deviation.", formula: "Document evidence input",
      impact: "A pending RFA can hold up procurement or work; when it proposes a deviation from spec, it is exactly the kind of document the AI analyze layer compares against the spec for a CONFLICT/GAP verdict." },
    { term: "Submittal", definition: "A contractor or supplier submission for review. Submittal status can affect schedule and procurement risk.", formula: "Document evidence input",
      impact: "Rejected or looping submittals on long-lead items are a procurement-risk early warning; repeated resubmittals quietly consume float a reviewer needs to protect." },
    { term: "Pay Application", definition: "A contractor request for payment documenting work completed in a period.", formula: "Document evidence input / progress claim",
      impact: "Pay-app percent-complete that outruns verified field progress is a classic over-billing / schedule-optimism signal reviewers reconcile against EV before certifying payment." },
    { term: "Document Risk", definition: "Risk extracted from project records such as RFIs, submittals, procurement notes, QC comments, claims, or meeting minutes.", formula: "Document evidence → rule classification → human review",
      impact: "Surfaces the qualitative warning signs that never reach a cost report; the transparent keyword score keeps that judgment inspectable and auditable rather than a black box." },
    { term: "Signal Synthesis", definition: "The combination of cost, schedule, anomaly, and document evidence into an explainable status. Disagreement is surfaced, not averaged away.", formula: "EVM + forecast + CUSUM + document evidence → conflict type",
      impact: "Stops a single green metric from masking trouble elsewhere; by naming the conflict (e.g. forecast ahead of status) it tells the reviewer what specifically to investigate." },
    { term: "ABM", definition: "Agent-Based Model governance layer: each authority role (PM, controls lead, program director) is an agent with explicit decision rules. In this demo, those rules ARE the readable functions in decision.js.", formula: "(health state × conflict × fairness sensitivity) → action + authority",
      impact: "Makes 'who acts and when' explicit and consistent, so escalation follows documented authority rules rather than whoever happens to notice the problem." },
    { term: "Fairness Gate", definition: "A mandatory workflow step on fairness-sensitive red-reviews: contractor response opportunity must be acknowledged before a decision can be recorded. It is a procedural gate, never a statistic.", formula: "Workflow step — blocks recording until acknowledged",
      impact: "Protects due process: it prevents a model signal from becoming a formal action against a contractor before they have had a documented chance to respond — defensible and auditable." },
    { term: "Red-review", definition: "The evidence package has crossed the threshold for accountable HUMAN review. It never means automatic action.", formula: "≥2 red signals, or CUSUM breach + red forecast",
      impact: "Defines the bright line where a project must get named, senior human attention with a full evidence package — never an automated penalty, always a review." },
    { term: "Governance Recommendation", definition: "The recommended action, responsible authority, and required documentation that the rules derive from a project's signal package.", formula: "Signal → Evidence → Threshold → Explanation → Consequence → Action",
      impact: "Converts analysis into an accountable next step with an owner and a paper trail; it is a recommendation a named human records — the tool never decides on its own." },
    { term: "PCEIF", definition: "Public Capital EVM Intelligence Framework: a signal-to-action governance framework for public AEC capital programs. Signals from four model classes feed explicit governance rules that recommend an action, an authority, and required documentation.", formula: "Signal → Evidence → Threshold → Explanation → Consequence → Action",
      impact: "Ties together the metrics, the anomaly and document evidence, and the decision rules so a public-program reviewer gets one explainable, auditable path from signal to governed action." }
  ];

  /* ---------- assistant topics: keywords → curated answer ---------- */
  const TOPICS = [
    {
      id: "pceif",
      keywords: ["pceif", "framework", "what is this", "purpose", "praxis", "research"],
      title: "What PCEIF is",
      body: "PCEIF (Public Capital EVM Intelligence Framework) is a signal-to-action governance framework for public AEC capital programs. Four signal classes — EVM, Monte Carlo forecast, SPC/CUSUM anomaly, and document risk — feed explicit governance rules that derive a health state, classify signal conflict, and recommend an action with a named authority and required documentation. This site is a synthetic demonstration of that workflow."
    },
    {
      id: "radar",
      keywords: ["radar", "portfolio", "blip", "scope", "circle", "ring", "sector", "distance", "center"],
      title: "Reading the portfolio scope",
      body: "Each blip is a synthetic project. Distance from center = drift from baseline (healthy projects sit near center). Angle = delivery sector: Design, Construction, or Hybrid. Blip color = derived health state. Click a blip — or use the equivalent list below the scope — to open that project's Detail page (ledger, decision card, and all five signals for that project)."
    },
    {
      id: "module01",
      keywords: ["module 01", "module 1", "hybrid", "dynamic simulation", "evm module", "cpi", "spi", "eac", "earned value"],
      title: "Module 01 — Hybrid Dynamic Simulation",
      body: "Module 01 covers the EVM core: CPI (cost performance, EV/AC) and SPI (schedule performance, EV/PV) against the baseline. On a project's Detail page the Monte Carlo is a REAL client-side computation: 5,000 iterations sampled from a signal-derived Beta-PERT distribution, with P50 and P80 read from the simulated array. It is a demonstration model, not a calibrated forecast."
    },
    {
      id: "module02",
      keywords: ["module 02", "module 2", "cusum", "spc", "anomaly", "drift", "trend", "control"],
      title: "Module 02 — SPC / CUSUM Anomaly Monitor",
      body: "Module 02 watches for accumulating drift. On a project's Detail page CUSUM is a REAL computation: the standard two-sided tabular recursion runs over the project's metric series and a breach is flagged only when the cumulative statistic crosses the decision interval H. It feeds the governance rules — including the 'Anomaly without narrative' conflict when the document record offers no explanation."
    },
    {
      id: "module03",
      keywords: ["module 03", "module 3", "document", "doc risk", "rfi", "submittal", "extraction", "keyword"],
      title: "Module 03 — Document-Risk Extraction",
      body: "Module 03 scores risk language in project records (RFIs, submittals, QC comments, procurement notes) using visible keyword rules — the same rules the Manage Projects page runs. The score and the matched excerpt feed the signal ledger. In this demo extraction is rule-based and transparent; there is no live NLP or LLM."
    },
    {
      id: "module04",
      keywords: ["module 04", "module 4", "synthesis", "conflict", "disagreement", "leading", "forecast ahead"],
      title: "Module 04 — Signal Synthesis",
      body: "Module 04 classifies disagreement between signal classes instead of averaging it away. Conflict types: Multi-signal red-review, Anomaly without narrative, Forecast ahead of status, Leading document risk, Agreement — low risk, and Mixed early warning. The precedence order is deliberate and documented in decision.js."
    },
    {
      id: "module05",
      keywords: ["module 05", "module 5", "abm", "agent", "governance layer", "decision rules", "authority"],
      title: "Module 05 — ABM governance layer",
      body: "Module 05 is the agent-based governance layer: each authority role (PM, controls lead, program director) is an agent with explicit decision rules. Those rules live in decision.js as pure, readable functions — deriveHealthState, classifyConflict, and deriveDecision — and the Signals page calls them directly. The decision card you see on the Portfolio and Project Detail pages IS this module's output."
    },
    {
      id: "fairness",
      keywords: ["fairness", "gate", "contractor", "response opportunity", "blocks", "checkbox"],
      title: "How the fairness gate works",
      body: "When a project is fairness-sensitive (its signals implicate delivery responsibility) AND its state is Red-review, the decision card shows a mandatory acknowledgement: contractor response opportunity will be provided before any formal action. 'Record decision' stays disabled until the reviewer checks it and enters a rationale. The gate is a procedural workflow step — it is never expressed as a score or percentage."
    },
    {
      id: "decision",
      keywords: ["decision card", "record", "rationale", "authority", "documentation", "audit", "export"],
      title: "Decision card and audit export",
      body: "The decision card shows the derived state, conflict type, recommended action, authority role, and documentation required. A named reviewer must type a rationale (min 20 characters) before recording. 'Export audit JSON' downloads the full signal package, derived decision, rationale, fairness acknowledgement, and timestamps — display times use your selected timezone, and the record always keeps a UTC ISO timestamp for integrity."
    },
    {
      id: "create",
      keywords: ["create project", "new project", "add project", "generate"],
      title: "Creating a project",
      body: "On the Manage Projects page, set a name and delivery type (Design / Construction / Hybrid). The app generates the next SYN code, seeds baseline synthetic signals, runs the project through the same decision.js rules, and plots it on the portfolio scope immediately. Created projects persist in your browser's localStorage and are synthetic like everything else here."
    },
    {
      id: "archive",
      keywords: ["archive", "archived", "restore", "unarchive", "remove project", "hide project"],
      title: "Archiving a project",
      body: "On the Manage Projects page, each active project has an Archive action. Archiving removes it from the portfolio scope and all active views without deleting it — it moves to the Archived list, persists in localStorage, and can be restored with one click. Every archive and restore is logged in the project event log."
    },
    {
      id: "ingest",
      keywords: ["ingest", "upload", "paste", "doc type", "approve", "reject", "delta"],
      title: "Ingesting a document",
      body: "Pick a project and document type, then paste or upload text (.txt / .csv / PDF-extracted text). The app runs the same visible keyword rules as Module 03, shows exactly which rule fired and the proposed signal delta, and nothing changes until a human clicks Approve. Reject discards the proposal. Every ingest event is logged."
    },
    {
      id: "themes",
      keywords: ["theme", "light", "dark", "appearance"],
      title: "Themes",
      body: "Two themes over the same structure — Dark (default) and Light — switchable in the menu. Your choice persists in localStorage."
    },
    {
      id: "timezone",
      keywords: ["timezone", "time zone", "clock", "est", "utc", "edt", "eastern"],
      title: "Timezone",
      body: "The clock and all displayed timestamps use the timezone selected in the top bar (default Eastern, EST/EDT). The audit JSON additionally always records a UTC ISO timestamp for record integrity. Your selection persists in localStorage."
    },
    {
      id: "boundaries",
      keywords: ["synthetic", "real data", "boundary", "production", "validated", "llm", "api", "backend"],
      title: "Demo boundaries",
      body: "Everything here is synthetic demonstration data — no real project, agency, employer, contractor, or vendor. There is no backend, no LLM call, no analytics, and no tracking; this assistant is scripted from the knowledge library. No predictive-accuracy validation has been performed, and every recommended action requires named human approval."
    }
  ];

  window.LIN_KNOWLEDGE = { terms: TERMS, topics: TOPICS };

  /* ---------- knowledge page rendering + term lens ---------- */
  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function renderKnowledgePage() {
    const root = document.getElementById("knowledge-root");
    if (!root) return;

    root.innerHTML =
      `<div class="kn-grid">
         <section class="panel kn-terms">
           <p class="eyebrow">Term lens</p>
           <h2 class="kn-h">Definitions</h2>
           <p class="kn-sub">Click a term to pin its definition. The guided assistant answers from this same content.</p>
           <div class="kn-chiprow">` +
      LIN_KNOWLEDGE.terms.map((t, i) =>
        `<button class="kn-chip" data-term="${i}">${esc(t.term)}</button>`).join("") +
      `  </div>
         <div class="kn-def" id="kn-def" aria-live="polite">
           <p class="kn-sub">Select a term above.</p>
         </div>
         </section>
         <section class="panel kn-topics">
           <p class="eyebrow">Method library</p>
           <h2 class="kn-h">PCEIF concepts &amp; how-to</h2>` +
      LIN_KNOWLEDGE.topics.map((t) =>
        `<details class="kn-topic"><summary>${esc(t.title)}</summary><p>${esc(t.body)}</p></details>`).join("") +
      `  </section>
       </div>`;

    root.querySelectorAll(".kn-chip").forEach((btn) => {
      btn.addEventListener("click", () => {
        const t = LIN_KNOWLEDGE.terms[Number(btn.dataset.term)];
        root.querySelectorAll(".kn-chip").forEach((b) => b.classList.toggle("active", b === btn));
        const def = document.getElementById("kn-def");
        def.innerHTML =
          `<h3 class="kn-defterm">${esc(t.term)}</h3>
           <p class="kn-defbody"><b>Definition.</b> ${esc(t.definition)}</p>
           ${t.impact ? `<p class="kn-impact"><b>Impact.</b> ${esc(t.impact)}</p>` : ""}
           <p class="kn-defformula">${esc(t.formula)}</p>
           <button class="kn-ask" type="button">Ask the AI about ${esc(t.term)}</button>`;
        const ask = def.querySelector(".kn-ask");
        if (ask) ask.addEventListener("click", () => {
          const q = `Explain ${t.term} and its impact on this portfolio in plain language for a project-controls reviewer.`;
          if (window.LinAssistant && LinAssistant.ask) LinAssistant.ask(q);
        });
      });
    });
  }

  window.LinKnowledge = { renderKnowledgePage };
})();
