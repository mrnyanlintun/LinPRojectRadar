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

  /* ---------- static glossary (Knowledge page left panel) ----------
     Plain, scannable definitions + colour thresholds. The TERMS array above is
     kept for the scripted assistant fallback; this GLOSSARY drives the page. */
  const T = {
    green: "var(--clear-green)", amber: "var(--radar-amber)", red: "var(--alarm-red)",
  };
  const GLOSSARY = [
    { term: "EVM — Earned Value Management",
      definition: "A project controls methodology that integrates scope, schedule, and cost to objectively measure project performance. Compares planned work against actual work completed and actual cost incurred." },
    { term: "CPI — Cost Performance Index",
      definition: "CPI = EV / AC. Measures cost efficiency. CPI = 1.00 means on budget; > 1.00 means under budget; < 1.00 means over budget.",
      thresholds: [
        { label: "Green: CPI ≥ 0.95", color: T.green },
        { label: "Amber: CPI 0.90–0.94", color: T.amber },
        { label: "Red: CPI < 0.90", color: T.red },
      ] },
    { term: "SPI — Schedule Performance Index",
      definition: "SPI = EV / PV. Measures schedule efficiency. SPI = 1.00 means on schedule; > 1.00 means ahead of schedule; < 1.00 means behind schedule.",
      thresholds: [
        { label: "Green: SPI ≥ 0.95", color: T.green },
        { label: "Amber: SPI 0.90–0.94", color: T.amber },
        { label: "Red: SPI < 0.90", color: T.red },
      ] },
    { term: "BAC — Budget at Completion",
      definition: "The total authorized budget for the project. The baseline against which earned value is measured. Established at contract award; changes only through approved change orders." },
    { term: "EV — Earned Value",
      definition: "The budgeted cost of work performed. EV = BAC × % complete (verified). Represents the monetary value of work actually accomplished." },
    { term: "AC — Actual Cost",
      definition: "The actual money spent to accomplish the work measured by EV. Comes from the pay application (amount paid to date)." },
    { term: "PV — Planned Value",
      definition: "The budgeted cost of work scheduled. Derived from the time-phased baseline schedule. Represents what was planned to be spent by a given date." },
    { term: "EAC — Estimate at Completion",
      definition: "Forecast of total project cost. EAC = BAC / CPI (most common formula). P50 EAC = median of Monte Carlo simulation. P80 EAC = 80th percentile (conservative).",
      thresholds: [
        { label: "Green: P80 EAC within +5% of BAC", color: T.green },
        { label: "Amber: P80 EAC +5% to +10% of BAC", color: T.amber },
        { label: "Red: P80 EAC > +10% of BAC", color: T.red },
      ] },
    { term: "P50 / P80",
      definition: "Percentile outputs from the Monte Carlo simulation. P50 = 50% probability cost will be at or below this value. P80 = 80% probability. P80 is the conservative planning figure." },
    { term: "Monte Carlo",
      definition: "5,000-iteration probabilistic simulation sampling EAC from a Beta-PERT distribution derived from CPI and SPI. Produces P50/P80 EAC and P(milestone delay)." },
    { term: "CUSUM — Cumulative Sum Control Chart",
      definition: "Statistical process control method that detects sustained drift in a time series. Applied to SPI across 12 reporting periods. Breach = cumulative drift exceeds the decision interval H (5σ). A breach means the pattern is systemic, not noise.",
      thresholds: [
        { label: "Green: drift below watch level", color: T.green },
        { label: "Amber: drift approaching control limit", color: T.amber },
        { label: "Red: CUSUM breaches threshold", color: T.red },
      ] },
    { term: "SPC — Statistical Process Control",
      definition: "The use of statistical methods to monitor and control a process. CUSUM is the SPC method used in PCEIF to detect schedule drift." },
    { term: "PERT — Program Evaluation & Review Technique",
      definition: "Stochastic network scheduling method. Each activity has optimistic (a), most likely (m), and pessimistic (b) durations sampled from a triangular distribution. P80 project duration and path criticality index are computed from 5,000 iterations. Formula: te = (a + 4m + b) / 6" },
    { term: "LOB — Line of Balance",
      definition: "Production scheduling method for repetitive work. Plots crew velocity (units/day) for sequential operations. Flags when the buffer between operations collapses — a leading indicator of schedule collision before it shows in EVM." },
    { term: "CCPM — Critical Chain Project Management",
      definition: "Aggregates safety margins from individual activities into a single project buffer. Fever chart maps buffer consumption against chain completion. Entering the red zone means the buffer is being consumed faster than progress is being made." },
    { term: "RCF — Reference Class Forecasting",
      definition: "Flyvbjerg's debiasing method. Uses historical cost overrun data from similar projects to establish a prior probability distribution — bypassing optimism bias in contractor estimates. P80 RCF prior is the statistically-adjusted realistic budget." },
    { term: "DSM — Design Structure Matrix",
      definition: "Models information dependencies between design disciplines (Arch, Structural, MEP). Simulates how a scope change propagates through design iterations. Rework multiplier > 2.5 indicates high coordination risk." },
    { term: "ABM — Agent-Based Model",
      definition: "The governance decision layer in PCEIF. Takes the signal package from all modules and derives a conflict classification, recommended action, named authority, and fairness gate requirement. Does not make decisions — surfaces the structured recommendation for human approval." },
    { term: "Fairness Gate",
      definition: "A mandatory step requiring contractor explanation before formal action is recorded. Triggered when a fairness-sensitive signal (document risk, LOB, CCPM) reaches Red. Prevents automated model outputs from driving contractual consequences without human review." },
    { term: "Red-review",
      definition: "PCEIF governance state requiring Program Director / PMO lead review. Triggered when ≥2 signal classes are Red, or CUSUM breach + Red forecast. Requires full signal package, assigned owner, rationale, response timeframe, and audit record." },
  ];

  /* ---------- Modules 06-10 — Method Library accordion entries (Fix 3) ---------- */
  TOPICS.push(
    {
      id: "module06",
      keywords: ["module 06", "module 6", "pert", "program evaluation", "network criticality", "triangular", "path criticality"],
      title: "Module 06 — Program Evaluation & Review Technique (PERT)",
      body: "PERT is a stochastic network scheduling method. Each activity has three duration estimates — optimistic (a), most likely (m), and pessimistic (b) — and is sampled from a triangular distribution. The classic deterministic three-point estimate is te = (a + 4m + b) / 6; the simulation aggregates the dominant path across 5,000 runs. P80 duration is the conservative finish (80% of runs at or under). The path-criticality index is the fraction of runs in which the structural path was on the critical path — the higher it is, the less float you have to absorb a slip. In this implementation a lower project SPI widens the pessimistic bound, so an already-drifting schedule grows a fatter P80 tail. Thresholds: Green P80 ≤ baseline; Amber P80 up to +20%; Red P80 > +20%.",
    },
    {
      id: "module07",
      keywords: ["module 07", "module 7", "lob", "line of balance", "production velocity", "crew", "buffer"],
      title: "Module 07 — Line of Balance (LOB)",
      body: "LOB tracks production velocity for sequential, repetitive work — grading runs ahead of paving, paving runs ahead of striping, and so on. Each crew has a rate in units/day; the buffer is the schedule gap between leader and follower at every unit. When the follower's rate slips, that buffer compresses unit by unit and a crew-on-crew collision is being telegraphed before EVM moves. Here, lower project SPI slows the follower (paving) so the minimum crew buffer shrinks. Buffer collapse is a leading schedule indicator: it shows up in the LOB chart before it shows up in CPI or SPI. Thresholds: Green buffer > 3 days; Amber 1.5–3 days; Red ≤ 1.5 days.",
    },
    {
      id: "module08",
      keywords: ["module 08", "module 8", "ccpm", "critical chain", "buffer", "fever chart"],
      title: "Module 08 — Critical Chain Project Management (CCPM)",
      body: "CCPM (Goldratt) aggregates the safety margin embedded in individual activity estimates into a single project buffer at the end of the critical chain. The fever chart plots buffer-consumed % against chain-complete %. Two thresholds drive the zones: the amber line tracks chain completion (buffer consumed ≥ % complete) — burning buffer at the same rate progress is being made; the red line sits a third of the remaining range above (buffer consumed ≥ % complete + (100 − % complete) / 3) — burning buffer faster than the chain can complete. Crossing into red means the buffer will run out before the work does. Thresholds: Green below the amber line; Amber buffer consumed ≥ % complete; Red buffer consumed ≥ % complete + (100 − % complete) / 3.",
    },
    {
      id: "module09",
      keywords: ["module 09", "module 9", "rcf", "reference class", "forecasting", "flyvbjerg", "debias", "optimism bias"],
      title: "Module 09 — Reference Class Forecasting (RCF)",
      body: "Reference Class Forecasting comes from Bent Flyvbjerg's research on optimism bias in large infrastructure projects: bottom-up estimates systematically underestimate cost because they reason from the inside view (this project's plan) rather than the outside view (how comparable projects have actually performed). RCF replaces the inside-view estimate with an empirical prior — the distribution of historical overrun multipliers from a comparable reference class. This implementation uses an airport-infrastructure multiplier set [1.00 … 1.52]; the P80 multiplier is the conservative debiasing factor applied to BAC. The debiasing factor is the multiplier itself: ×1.38 means the outside view says comparable projects finished 38% over their baseline. The P80 RCF prior is the realistic planning budget to compare against the bottom-up EAC. Thresholds: Green P80 within +10% of BAC; Amber +10–25%; Red > +25%.",
    },
    {
      id: "module10",
      keywords: ["module 10", "dsm", "design structure matrix", "rework", "propagation", "arch", "structural", "mep", "dependency"],
      title: "Module 10 — Design Structure Matrix (DSM)",
      body: "A DSM captures information-flow dependencies between work elements as a square matrix: each off-diagonal entry A[i][j] is the strength of i's dependence on j. Here the elements are the three design disciplines — Architectural, Structural, MEP — and the off-diagonals encode how much a unit change in one cascades into the others. Architectural decisions flow downstream into both Structural and MEP, so an arch scope change ripples through the matrix; structural and MEP changes also feed back. The simulation propagates a unit architectural change vector through the matrix for four passes and accumulates the rework absorbed in each discipline. The total cumulative rework multiplier is the coordination cost: a multiplier above 2.5 indicates that one unit of arch change is generating more than 2.5 units of downstream rework — high coordination risk. Thresholds: Green rework multiplier ≤ 2.5; Amber > 2.5.",
    },
  );

  window.LIN_KNOWLEDGE = { terms: TERMS, glossary: GLOSSARY, topics: TOPICS };

  /* ---------- knowledge page rendering + term lens ---------- */
  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function renderKnowledgePage() {
    const root = document.getElementById("knowledge-root");
    if (!root) return;

    const glossary = (LIN_KNOWLEDGE.glossary || []).map((g) => {
      const thresholds = (g.thresholds || []).map((t) =>
        `<li class="kn-gl-threshold" style="--kn-th:${t.color}">${esc(t.label)}</li>`).join("");
      return `<div class="kn-gl-item">
        <p class="kn-gl-term"><strong>${esc(g.term)}</strong></p>
        <p class="kn-gl-def">${esc(g.definition)}</p>
        ${thresholds ? `<ul class="kn-gl-thresholds">${thresholds}</ul>` : ""}
      </div>`;
    }).join("");

    root.innerHTML =
      `<div class="kn-grid">
         <section class="panel kn-terms">
           <p class="eyebrow">Glossary</p>
           <h2 class="kn-h">Definitions</h2>
           <p class="kn-sub">Plain-language definitions of the PCEIF terms and the color thresholds where they apply.</p>
           <div class="kn-glossary">${glossary}</div>
         </section>
         <section class="panel kn-topics">
           <p class="eyebrow">Method library</p>
           <h2 class="kn-h">PCEIF concepts &amp; how-to</h2>` +
      LIN_KNOWLEDGE.topics.map((t) =>
        `<details class="kn-topic"><summary>${esc(t.title)}</summary><p>${esc(t.body)}</p></details>`).join("") +
      `  </section>
       </div>`;
  }

  window.LinKnowledge = { renderKnowledgePage };
})();
