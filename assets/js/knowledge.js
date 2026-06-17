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
      body: "Module 01 covers the EVM core: CPI (cost performance, EV/AC) and SPI (schedule performance, EV/PV) against the baseline. On a project's Detail page the Monte Carlo runs 5,000 iterations sampled from a signal-derived Beta-PERT distribution, with P50 and P80 read from the simulated array. P80 is the planning-conservative figure used for contingency and escalation decisions."
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

  /* ---------- (legacy) static glossary — superseded by LIBRARY below ----------
     Kept around because removing it has no benefit; the page renders LIBRARY. */
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

  /* ---------- Knowledge Library — 11 narrative topics with formulas + SVG ---------- */
  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  // Small typography helpers shared by every topic body.
  const RAG = {
    green: "var(--clear-green)", amber: "var(--radar-amber)", red: "var(--alarm-red)",
  };
  function ragTable(headerRow, rows) {
    return `<table class="kn-rag">
      <thead><tr>${headerRow.map((h) => `<th>${esc(h)}</th>`).join("")}</tr></thead>
      <tbody>${rows.map((r) => `<tr>${r.map((c, i) => {
        if (typeof c === "object" && c.color) return `<td class="kn-rag-cell" style="--kn-th:${c.color}">${esc(c.label)}</td>`;
        return `<td${i === 0 ? ' class="kn-rag-metric"' : ""}>${esc(String(c))}</td>`;
      }).join("")}</tr>`).join("")}</tbody>
    </table>`;
  }
  function formulaBlock(lines) {
    return `<pre class="kn-formula"><code>${lines.map((l) =>
      Array.isArray(l) ? `<span class="kn-f-expr">${esc(l[0])}</span><span class="kn-f-label">${esc(l[1] || "")}</span>`
                       : esc(l)).join("\n")}</code></pre>`;
  }

  /* ---------- inline SVG illustrations (dark + light theme aware) ---------- */

  // PCEIF signal-to-action flow (Topic 1) — two rows so the diagram is large
  // and readable: 4 boxes across the top, 3 boxes centred underneath, with an
  // L-bend connector from box 4 down to box 5.
  function svgPceifFlow() {
    const row1 = ["Documents + Schedule + Cost", "10 Signal Modules", "Signal Synthesis", "Conflict Classification"];
    const row2 = ["Governance Decision Card", "Named Human Approval", "Audit Record"];
    const bw = 200, bh = 70, gap = 40, pad = 24;
    const rowGap = 80;             // vertical space between rows
    const captionGap = 36;
    const row1Width = row1.length * bw + (row1.length - 1) * gap;
    const row2Width = row2.length * bw + (row2.length - 1) * gap;
    const w = Math.max(row1Width, row2Width) + pad * 2;
    const row1Y = 28, row2Y = row1Y + bh + rowGap;
    const h = row2Y + bh + captionGap + 24;
    const row1X = pad + (w - pad * 2 - row1Width) / 2;
    const row2X = pad + (w - pad * 2 - row2Width) / 2;
    const arrowReserve = 12;

    let out = `<svg viewBox="0 0 ${w} ${h}" class="kn-svg kn-svg-flow" role="img" aria-label="PCEIF signal-to-action flow (two rows)">`;
    out += `<defs><marker id="kn-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="var(--phosphor)"/></marker></defs>`;

    // Helper: draw a labelled box with wrapped text + a right-pointing arrow to
    // the next box in the same row.
    function drawBox(label, x, y, isLastInRow) {
      let s = "";
      s += `<rect x="${x}" y="${y}" width="${bw}" height="${bh}" rx="10"
        fill="color-mix(in srgb, var(--phosphor) 10%, var(--surface-soft))"
        stroke="var(--phosphor)" stroke-width="2"></rect>`;
      // wrap at ~20 chars per line (14px text fits 200-px-wide box with padding)
      const words = label.split(" "); const lines = []; let cur = "";
      words.forEach((wd) => {
        if ((cur + " " + wd).trim().length > 20) { if (cur.trim()) lines.push(cur.trim()); cur = wd; }
        else cur += " " + wd;
      });
      if (cur.trim()) lines.push(cur.trim());
      const cy = y + bh / 2;
      const startY = cy - ((lines.length - 1) * 16) / 2 + 5;
      lines.forEach((ln, j) => {
        s += `<text x="${x + bw / 2}" y="${(startY + j * 16).toFixed(1)}" text-anchor="middle" class="kn-svg-flow-t" fill="var(--text)">${esc(ln)}</text>`;
      });
      if (!isLastInRow) {
        const ax1 = x + bw + 4;
        const ax2 = x + bw + gap - arrowReserve;
        s += `<line x1="${ax1}" y1="${cy}" x2="${ax2}" y2="${cy}" stroke="var(--phosphor)" stroke-width="2" marker-end="url(#kn-arrow)"></line>`;
      }
      return s;
    }

    // Row 1 (4 boxes)
    row1.forEach((l, i) => {
      out += drawBox(l, row1X + i * (bw + gap), row1Y, i === row1.length - 1);
    });
    // Row 2 (3 boxes, centred)
    row2.forEach((l, i) => {
      out += drawBox(l, row2X + i * (bw + gap), row2Y, i === row2.length - 1);
    });

    // L-bend connector from box 4 (end of row 1) down to box 5 (start of row 2).
    // Three-segment polyline with a single arrowhead at the end of the last leg
    // (which is vertical, so the arrowhead correctly points DOWN into box 5).
    const box4CenterX = row1X + 3 * (bw + gap) + bw / 2;       // bottom-centre of box 4
    const box4BottomY = row1Y + bh;
    const box5CenterX = row2X + bw / 2;                        // top-centre of box 5
    const box5TopY = row2Y;
    const midY = box4BottomY + (box5TopY - box4BottomY) / 2;
    const tailReserve = 10;                                    // leave room for arrowhead
    out += `<polyline points="${box4CenterX},${box4BottomY + 2} ${box4CenterX},${midY} ${box5CenterX},${midY} ${box5CenterX},${box5TopY - tailReserve}"
      stroke="var(--phosphor)" stroke-width="2" fill="none" marker-end="url(#kn-arrow)"></polyline>`;

    // Italic caption
    out += `<text x="${w / 2}" y="${row2Y + bh + captionGap}" text-anchor="middle" class="kn-svg-flow-cap" fill="var(--faint)">The system surfaces a recommendation. A named human records the decision.</text>`;
    return `<div class="kn-flow-wrap">${out}</svg></div>`;
  }

  // Signal stack grouping → Synthesis (Topic 2)
  function svgSignalStack() {
    const w = 720, h = 290;
    const groups = [
      { lab: "Quantitative EVM", mods: ["01 EVM", "02 CUSUM"], color: "var(--clear-green)", x: 30, y: 30 },
      { lab: "Governance Synthesis", mods: ["03 Doc Risk", "04 Synthesis", "05 ABM"], color: "var(--phosphor)", x: 30, y: 116 },
      { lab: "Extended Simulation", mods: ["06 PERT", "07 LOB", "08 CCPM", "09 RCF", "10 DSM"], color: "var(--radar-amber)", x: 30, y: 222 },
    ];
    let out = `<svg viewBox="0 0 ${w} ${h}" class="kn-svg" role="img" aria-label="Signal stack of 10 modules feeding Signal Synthesis">`;
    groups.forEach((g) => {
      const bx = g.x, by = g.y, bw = 360, bh = 64;
      out += `<rect x="${bx}" y="${by}" width="${bw}" height="${bh}" rx="9" fill="var(--surface-soft)" stroke="${g.color}" stroke-width="1.5"></rect>`;
      out += `<text x="${bx + 12}" y="${by + 18}" class="kn-svg-t" fill="${g.color}">${esc(g.lab)}</text>`;
      g.mods.forEach((m, i) => {
        const cx = bx + 14 + i * 68, cy = by + 30;
        out += `<rect x="${cx}" y="${cy}" width="60" height="22" rx="4" fill="var(--surface)" stroke="var(--line)"></rect>`;
        out += `<text x="${cx + 30}" y="${cy + 15}" text-anchor="middle" class="kn-svg-t" fill="var(--text)">${esc(m)}</text>`;
      });
      // connector to synthesis node
      out += `<path d="M${bx + bw + 4} ${by + bh / 2} L 590 145" stroke="var(--phosphor)" stroke-width="1.4" stroke-dasharray="3 3" fill="none"></path>`;
    });
    // synthesis target node
    out += `<rect x="540" y="115" width="160" height="60" rx="9" fill="var(--phosphor)" opacity="0.15" stroke="var(--phosphor)" stroke-width="1.8"></rect>`;
    out += `<text x="620" y="142" text-anchor="middle" class="kn-svg-t" fill="var(--text)" font-weight="700">Module 04</text>`;
    out += `<text x="620" y="160" text-anchor="middle" class="kn-svg-t" fill="var(--text)">Signal Synthesis</text>`;
    return out + "</svg>";
  }

  // EVM S-curve (Topic 3)
  function svgEvmSCurve() {
    const w = 720, h = 280, pad = 50, base = h - 40;
    const pts = (a, b, c) => {
      const arr = []; for (let i = 0; i <= 30; i++) { const t = i / 30; const v = 100 * (a * t + b * t * t + c * t * t * t); arr.push([pad + t * (w - pad - 60), base - v / 110 * (base - 30)]); } return arr;
    };
    const toPath = (a) => a.map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1)).join(" ");
    const pv = pts(0.30, 0.55, 0.15);   // planned (smooth s-curve, ends at 100)
    const ev = pts(0.20, 0.40, 0.20);   // earned (lags pv → SV gap)
    const ac = pts(0.25, 0.55, 0.30);   // actual (above ev at end → CV gap)
    // markers at month ~70%
    const k = 22, evP = ev[k], acP = ac[k], pvP = pv[k];
    let out = `<svg viewBox="0 0 ${w} ${h}" class="kn-svg" role="img" aria-label="EVM S-curve: PV vs EV vs AC with CV and SV gaps">`;
    out += `<line x1="${pad}" y1="${base}" x2="${w - 14}" y2="${base}" stroke="var(--ring-line)"></line>`;
    out += `<line x1="${pad}" y1="20" x2="${pad}" y2="${base}" stroke="var(--ring-line)"></line>`;
    out += `<text x="${w - 14}" y="${h - 14}" text-anchor="end" class="kn-svg-t" fill="var(--muted)">project time →</text>`;
    out += `<text x="${pad - 6}" y="22" text-anchor="end" class="kn-svg-t" fill="var(--muted)">$</text>`;
    out += `<path d="${toPath(pv)}" stroke="var(--phosphor)" fill="none" stroke-width="2"></path>`;
    out += `<path d="${toPath(ev)}" stroke="var(--clear-green)" fill="none" stroke-width="2"></path>`;
    out += `<path d="${toPath(ac)}" stroke="var(--alarm-red)" fill="none" stroke-width="2"></path>`;
    // CV gap (EV→AC) and SV gap (EV→PV) at month k
    out += `<line x1="${evP[0]}" y1="${evP[1]}" x2="${evP[0]}" y2="${acP[1]}" stroke="var(--alarm-red)" stroke-dasharray="3 3"></line>`;
    out += `<text x="${evP[0] + 8}" y="${(evP[1] + acP[1]) / 2}" class="kn-svg-t" fill="var(--alarm-red)">CV (cost variance)</text>`;
    out += `<line x1="${evP[0]}" y1="${evP[1]}" x2="${pvP[0]}" y2="${pvP[1]}" stroke="var(--radar-amber)" stroke-dasharray="3 3"></line>`;
    out += `<text x="${evP[0] - 6}" y="${pvP[1] - 8}" text-anchor="end" class="kn-svg-t" fill="var(--radar-amber)">SV (schedule variance)</text>`;
    // legend
    [["PV — planned value", "var(--phosphor)"], ["EV — earned value", "var(--clear-green)"], ["AC — actual cost", "var(--alarm-red)"]]
      .forEach(([l, c], i) => {
        const lx = 80 + i * 200, ly = 24;
        out += `<line x1="${lx}" y1="${ly}" x2="${lx + 18}" y2="${ly}" stroke="${c}" stroke-width="2"></line>`;
        out += `<text x="${lx + 24}" y="${ly + 4}" class="kn-svg-t" fill="var(--text)">${esc(l)}</text>`;
      });
    return out + "</svg>";
  }

  // Monte Carlo histogram with P50/P80 markers (Topic 4)
  function svgMcHist() {
    const w = 720, h = 240, pad = 50, base = h - 36;
    // synthetic bell-ish histogram (BAC=100, slight right skew)
    const bars = Array.from({ length: 24 }, (_, i) => {
      const x = i - 11; return Math.exp(-x * x / 18) * (1 - x * 0.04);
    });
    const max = Math.max(...bars);
    const bw = (w - pad - 60) / bars.length;
    let out = `<svg viewBox="0 0 ${w} ${h}" class="kn-svg" role="img" aria-label="Monte Carlo simulated EAC distribution with P50 and P80 markers">`;
    out += `<line x1="${pad}" y1="${base}" x2="${w - 14}" y2="${base}" stroke="var(--ring-line)"></line>`;
    bars.forEach((v, i) => {
      const bx = pad + i * bw, bh = (v / max) * (base - 28);
      out += `<rect x="${bx + 1}" y="${base - bh}" width="${bw - 2}" height="${bh}" fill="var(--phosphor)" opacity="0.45"></rect>`;
    });
    const p50x = pad + bw * 12, p80x = pad + bw * 17;
    out += `<line x1="${p50x}" y1="20" x2="${p50x}" y2="${base}" stroke="var(--radar-amber)" stroke-dasharray="5 4"></line>`;
    out += `<text x="${p50x + 4}" y="34" class="kn-svg-t" fill="var(--radar-amber)">P50</text>`;
    out += `<line x1="${p80x}" y1="20" x2="${p80x}" y2="${base}" stroke="var(--alarm-red)" stroke-dasharray="5 4"></line>`;
    out += `<text x="${p80x + 4}" y="34" class="kn-svg-t" fill="var(--alarm-red)">P80</text>`;
    out += `<text x="${w - 14}" y="${h - 12}" text-anchor="end" class="kn-svg-t" fill="var(--muted)">simulated EAC (5,000 iterations) →</text>`;
    return out + "</svg>";
  }

  // CUSUM line chart with H threshold (Topic 5)
  function svgCusum() {
    const w = 720, h = 240, pad = 50, base = h - 36;
    const periods = 12; const H = 5;
    const cusum = [0.4, 0.8, 1.2, 1.5, 2.1, 2.6, 3.4, 4.0, 4.7, 5.2, 5.8, 6.4];
    const sx = (i) => pad + (i / (periods - 1)) * (w - pad - 60);
    const sy = (v) => base - (v / 7.5) * (base - 28);
    let out = `<svg viewBox="0 0 ${w} ${h}" class="kn-svg" role="img" aria-label="CUSUM statistic vs decision interval H over 12 periods">`;
    out += `<line x1="${pad}" y1="${base}" x2="${w - 14}" y2="${base}" stroke="var(--ring-line)"></line>`;
    out += `<line x1="${pad}" y1="20" x2="${pad}" y2="${base}" stroke="var(--ring-line)"></line>`;
    // H line
    out += `<line x1="${pad}" y1="${sy(H)}" x2="${w - 24}" y2="${sy(H)}" stroke="var(--alarm-red)" stroke-dasharray="5 4"></line>`;
    out += `<text x="${w - 26}" y="${sy(H) - 6}" text-anchor="end" class="kn-svg-t" fill="var(--alarm-red)">H = 5σ (decision interval)</text>`;
    // statistic line + breach marker
    const pts = cusum.map((v, i) => sx(i) + "," + sy(v)).join(" ");
    out += `<polyline points="${pts}" fill="none" stroke="var(--phosphor)" stroke-width="2"></polyline>`;
    const breach = cusum.findIndex((v) => v > H);
    if (breach >= 0) {
      out += `<circle cx="${sx(breach)}" cy="${sy(cusum[breach])}" r="6" fill="var(--alarm-red)"></circle>`;
      out += `<text x="${sx(breach) + 8}" y="${sy(cusum[breach]) - 8}" class="kn-svg-t" fill="var(--alarm-red)">⚑ breach @ period ${breach + 1}</text>`;
    }
    out += `<text x="${w - 14}" y="${h - 12}" text-anchor="end" class="kn-svg-t" fill="var(--muted)">reporting periods →</text>`;
    return out + "</svg>";
  }

  // Module 04 agreement map (Topic 7)
  function svgAgreementMap() {
    const w = 720, h = 200;
    const nodes = [["EVM", "var(--clear-green)", 100], ["FORECAST", "var(--radar-amber)", 280], ["CUSUM", "var(--alarm-red)", 460], ["DOC", "var(--clear-green)", 620]];
    let out = `<svg viewBox="0 0 ${w} ${h}" class="kn-svg" role="img" aria-label="Signal class agreement map">`;
    nodes.forEach(([l, c, cx], i) => {
      out += `<circle cx="${cx}" cy="100" r="42" fill="none" stroke="${c}" stroke-width="2.5"></circle>`;
      out += `<text x="${cx}" y="98" text-anchor="middle" class="kn-svg-t" fill="var(--text)" font-weight="700">${esc(l)}</text>`;
      out += `<text x="${cx}" y="116" text-anchor="middle" class="kn-svg-t" fill="${c}">${l === "CUSUM" ? "RED" : (l === "FORECAST" ? "AMBER" : "GREEN")}</text>`;
      if (i < nodes.length - 1) {
        out += `<line x1="${nodes[i][2] + 44}" y1="100" x2="${nodes[i + 1][2] - 44}" y2="100" stroke="var(--phosphor)" stroke-dasharray="5 5" stroke-width="1.4"></line>`;
      }
    });
    out += `<text x="${w / 2}" y="180" text-anchor="middle" class="kn-svg-t" fill="var(--muted)">CUSUM Red + EVM Green → Anomaly Without Narrative (precedence rule 2)</text>`;
    return out + "</svg>";
  }

  /* ---------- 11 Library topics ---------- */
  const LIBRARY = [
    {
      id: "pceif",
      title: "1. What is PCEIF",
      eyebrow: "Framework foundation",
      build: () => `
        <p class="kn-lead">PCEIF — the <strong>Public Capital EVM Intelligence Framework</strong> — converts the multi-model signals that a public capital program already generates into a structured, accountable governance action with a named authority and a documented audit trail.</p>

        <h3>The problem it solves</h3>
        <p>Standard Earned Value Management produces excellent data. It does not produce a decision. A PM looking at CPI 0.88 in period 4 has no structured path to a defensible escalation: who must act, on what timeframe, with what documentation, under whose authority. The data exists; the governance link is missing.</p>
        <p>PCEIF closes that gap. Signals trigger an explicit rule set; the rule set returns a specific action, a specific authority, and the documentation required. The PM still records the decision — the framework simply makes the recommendation traceable.</p>

        <h3>Two-layer architecture</h3>
        <ul class="kn-list">
          <li><strong>Layer 1 — Agency Governance.</strong> Sets the policy framework: the authority matrix, escalation thresholds, fairness rules, audit requirements. Established by the program owner; not changed per project.</li>
          <li><strong>Layer 2 — PM Decision Architecture.</strong> Takes that policy and the project's signal package and surfaces, for each reporting cycle, the specific action the PM should record (or override, with rationale).</li>
        </ul>

        <h3>Signal-to-action mechanism</h3>
        ${svgPceifFlow()}

        <h3>What's different from standard EVM</h3>
        <ul class="kn-list">
          <li><strong>Standard EVM:</strong> compute CPI / SPI → report to management.</li>
          <li><strong>PCEIF:</strong> compute 10 signal classes → detect conflict → classify the conflict → surface the action, authority, and documentation — <em>before</em> the next reporting cycle closes.</li>
        </ul>

        <h3>The role of AI</h3>
        <p>AI explains and summarizes. It does <strong>not</strong> make governance decisions. Every recommended action requires a named human approval before it is recorded; the AI's job is to make that approval well-informed, not to replace it. This is a design constraint, not a performance limitation.</p>
      `,
    },
    {
      id: "stack",
      title: "2. The Signal Stack — 10 Modules",
      eyebrow: "Architecture",
      build: () => `
        <p class="kn-lead">The signal stack splits into three tiers. The first two compute and govern; the third extends quantitative coverage to specialised construction/design risks that EVM does not catch.</p>
        ${svgSignalStack()}

        <h3>Modules 01–02 — Quantitative EVM Analysis</h3>
        <ul class="kn-list">
          <li><strong>Module 01 — Hybrid Dynamic Simulation.</strong> EVM core (CPI, SPI) plus the 5,000-iteration Monte Carlo P80 EAC forecast.</li>
          <li><strong>Module 02 — SPC / CUSUM Anomaly Monitor.</strong> Two-sided tabular CUSUM over the SPI series; breach when cumulative drift exceeds the decision interval H = 5σ.</li>
        </ul>

        <h3>Modules 03–05 — Governance Synthesis (rule-based)</h3>
        <ul class="kn-list">
          <li><strong>Module 03 — Document Risk Extraction.</strong> Transparent keyword rules score risk language across RFIs, submittals, OAC minutes, and correspondence.</li>
          <li><strong>Module 04 — Signal Synthesis.</strong> Classifies the disagreement between signal classes (six conflict types) rather than averaging it away.</li>
          <li><strong>Module 05 — ABM Governance Layer.</strong> Maps (state × conflict × sector) to action, authority, and documentation. Implemented as pure functions in <code>decision.js</code>.</li>
        </ul>

        <h3>Modules 06–10 — Extended Simulation Stack</h3>
        <ul class="kn-list">
          <li><strong>Module 06 — PERT</strong> network criticality (P80 duration, path criticality index).</li>
          <li><strong>Module 07 — Line of Balance</strong> production velocity (crew-buffer collapse as a leading indicator).</li>
          <li><strong>Module 08 — CCPM</strong> buffer-health fever chart (buffer consumed vs chain complete).</li>
          <li><strong>Module 09 — Reference Class Forecasting</strong> cost prior (outside-view debiasing against an empirical reference class).</li>
          <li><strong>Module 10 — Design Structure Matrix</strong> rework propagation (architectural change cascades to MEP).</li>
        </ul>

        <p class="kn-callout">Outputs from all ten feed Module 04 (Signal Synthesis). The synthesis is what gates the governance card — not any individual signal.</p>
      `,
    },
    {
      id: "evm",
      title: "3. Module 01 — Earned Value Management (EVM)",
      eyebrow: "Module 01 (a)",
      build: () => `
        <p class="kn-lead">EVM integrates scope, schedule, and cost on a single measurement plane. On U.S. public capital programs it is required under OMB Circular A-11 and FAR Part 34 for major investments; under most agency policies a CPI shortfall sustained over multiple reporting periods is itself a reporting trigger.</p>

        <h3>The three curves</h3>
        <p><strong>PV</strong> (Planned Value), <strong>EV</strong> (Earned Value), and <strong>AC</strong> (Actual Cost) plotted against project time form the classic EVM S-curve. The gaps between them are the variances PCEIF acts on:</p>
        ${svgEvmSCurve()}

        <p>EV − AC is the <strong>cost variance</strong>: are we paying more or less than the work is worth? EV − PV is the <strong>schedule variance</strong> expressed in cost terms: are we ahead of or behind the planned burn? They measure different problems and demand different responses.</p>

        <h3>Formulas</h3>
        ${formulaBlock([
          ["CPI = EV / AC", "Cost Performance Index"],
          ["SPI = EV / PV", "Schedule Performance Index"],
          ["CV  = EV − AC", "Cost Variance ($)"],
          ["SV  = EV − PV", "Schedule Variance ($)"],
          "",
          ["EAC = BAC / CPI", "PCEIF default — assumes current efficiency continues"],
          ["EAC = AC + (BAC − EV)", "Optimistic — assumes future work on budget"],
          ["EAC = AC + (BAC − EV) / CPI", "Pessimistic — current CPI continues to completion"],
          ["VAC = BAC − EAC", "Variance at Completion"],
        ])}

        <h3>Why PCEIF defaults to BAC / CPI</h3>
        <p>On public capital programs cost overruns compound. A project 10% over budget at month 6 rarely recovers to baseline by closeout — the inefficiency rate is sticky. <code>BAC / CPI</code> assumes the current rate continues, which is the most defensible assumption for an escalation conversation. The optimistic formula is for the contractor; the pessimistic for risk reserves; the default is for the program controls record.</p>

        <h3>RAG thresholds</h3>
        ${ragTable(
          ["Metric", "Green", "Amber", "Red"],
          [
            ["CPI", { label: "≥ 0.95", color: RAG.green }, { label: "0.90–0.94", color: RAG.amber }, { label: "< 0.90", color: RAG.red }],
            ["SPI", { label: "≥ 0.95", color: RAG.green }, { label: "0.90–0.94", color: RAG.amber }, { label: "< 0.90", color: RAG.red }],
            ["P80 EAC vs BAC", { label: "within +5%", color: RAG.green }, { label: "+5% to +10%", color: RAG.amber }, { label: "> +10%", color: RAG.red }],
            ["P(milestone delay)", { label: "< 0.30", color: RAG.green }, { label: "0.30–0.60", color: RAG.amber }, { label: "≥ 0.60", color: RAG.red }],
          ]
        )}

        <h3>Governance implication</h3>
        <p>CPI &lt; 0.90 on a public capital program is the FAR-region threshold for potential corrective action reporting. A CPI of 0.88 sustained over three periods is not a "watch item" — under most agency program-controls policies it is a recovery-plan trigger, and the audit record should show the decision was made (or formally deferred) by named authority on a documented date.</p>
      `,
    },
    {
      id: "montecarlo",
      title: "4. Module 01 — Monte Carlo Forecast",
      eyebrow: "Module 01 (b)",
      build: () => `
        <p class="kn-lead">A single deterministic EAC gives false precision. A P50/P80 range is more honest and more useful: it lets program controls fund contingency to an explicit risk percentile rather than to a point estimate that pretends the future is known.</p>

        <h3>Why Beta-PERT</h3>
        <p>For construction cost modelling the Beta-PERT distribution is preferred over a normal or triangular distribution: it is continuous, naturally bounded by optimistic and pessimistic limits, and weighted toward the most-likely value. Across 5,000 iterations the simulated EAC distribution captures both central tendency and tail risk.</p>

        <h3>Formulas</h3>
        ${formulaBlock([
          "Beta-PERT parameters:",
          ["μ  = (a + 4m + b) / 6", "mean — most-likely weighted"],
          ["σ² = ((b − a) / 6)²", "variance"],
          ["α  = 6 × (μ − a) / (b − a)  ×  [ (μ − a)(b − μ) / σ²  − 1 ]", "shape α"],
          ["β  = α × (b − μ) / (μ − a)", "shape β"],
          "",
          "Per-iteration sample:",
          ["EAC_i = BAC / CPI_i,    CPI_i ~ Beta-PERT(a, m, b)", ""],
          "",
          "Aggregated outputs:",
          ["P50 EAC  = 50th percentile of [ EAC_1 … EAC_5000 ]", "median forecast"],
          ["P80 EAC  = 80th percentile", "conservative planning figure"],
          ["P(delay) = | { i : EAC_i > BAC × 1.10 } | / 5000", "milestone-delay probability"],
        ])}

        ${svgMcHist()}

        <p>The distance from P50 to P80 is the tail risk; widening that distance over reporting cycles is itself a finding — even if P50 holds steady, contingency needs are rising.</p>
      `,
    },
    {
      id: "cusum",
      title: "5. Module 02 — SPC / CUSUM Anomaly Monitor",
      eyebrow: "Module 02",
      build: () => `
        <p class="kn-lead">A single-period CPI/SPI reading is noisy. Real schedule drift accumulates slowly. Statistical Process Control separates signal from noise; CUSUM is the SPC method that catches sustained drift before any single period would trip a variance threshold.</p>

        <h3>Why tabular CUSUM, not Shewhart</h3>
        <p>A Shewhart chart flags points that breach 3σ control limits — good at detecting large single-period shifts, poor at detecting small sustained ones. Tabular CUSUM (Page, 1954) accumulates deviations from the target so a half-σ drift that persists over six periods triggers; on a project that is exactly the pattern that hides under Shewhart limits.</p>

        <h3>Two-sided tabular CUSUM</h3>
        ${formulaBlock([
          ["C⁺ᵢ = max( 0,  C⁺ᵢ₋₁ + (xᵢ − μ₀ − k) )", "upper (positive drift)"],
          ["C⁻ᵢ = max( 0,  C⁻ᵢ₋₁ − (xᵢ − μ₀ + k) )", "lower (negative drift)"],
          "",
          "Inputs:",
          ["xᵢ  = SPI at reporting period i", ""],
          ["μ₀  = 1.00", "target — on schedule"],
          ["k   = 0.5 σ", "allowance — half the series standard deviation"],
          ["H   = 5 σ", "decision interval"],
          "",
          ["Breach: C⁺ᵢ > H  or  C⁻ᵢ > H", "hand off to governance"],
        ])}

        <h3>Why H = 5σ (not 3σ)</h3>
        <p>Construction project SPI series have higher natural variability than manufacturing process measurements. A 3σ decision interval generates excessive false positives; 5σ ensures that only sustained, meaningful drift triggers governance action — at the cost of a slightly slower response. For a governance-grade signal that trade-off is correct.</p>

        ${svgCusum()}

        <h3>What a breach means</h3>
        <p>A CUSUM breach hands the question to Module 04 (Signal Synthesis) and Module 05 (ABM Governance Layer). The monitor never acts on its own; it produces evidence the governance layer routes. If the breach has no document narrative behind it, the conflict type is "Anomaly Without Narrative" — itself a finding worth surfacing.</p>
      `,
    },
    {
      id: "doc",
      title: "6. Module 03 — Document Risk Extraction",
      eyebrow: "Module 03",
      build: () => `
        <p class="kn-lead">EVM lags field conditions by weeks. An RFI log showing 20 open disputes in period 4 predicts a CPI collapse in period 6 — but EVM will not show that collapse until it has already happened. Document risk is the leading signal.</p>

        <h3>How extraction works</h3>
        <p>Module 03 applies transparent keyword and pattern rules over RFIs, submittal logs, OAC meeting minutes, and project correspondence. Each rule has a weight and an evidence excerpt; the document risk score is a weighted sum normalised to 0–1. Every score is inspectable: the matched rule, the source document, and the excerpt are carried into the ledger.</p>

        <h3>The score</h3>
        ${ragTable(
          ["Score", "Status", "Meaning"],
          [
            [{ label: "< 0.30", color: RAG.green }, "Green", "Routine language; no significant risk indicators."],
            [{ label: "0.30–0.70", color: RAG.amber }, "Amber", "Possible cost / schedule / scope impact language present."],
            [{ label: "≥ 0.70", color: RAG.red }, "Red", "High-impact language converging across multiple document types."],
          ]
        )}

        <h3>A real limitation</h3>
        <p>Keyword extraction is rule-based, not semantic. A sophisticated contractor writes around keyword rules. The score is a <em>leading indicator</em>, never a verdict. PCEIF treats Module 03 Red as a flag that requires Module 04 corroboration before it drives an action — never as a standalone trigger.</p>
      `,
    },
    {
      id: "synthesis",
      title: "7. Module 04 — Signal Synthesis",
      eyebrow: "Module 04",
      build: () => `
        <p class="kn-lead">A CPI of 1.02 and a CUSUM breach do <strong>not</strong> average to "slightly above baseline." The breach is the finding. PCEIF surfaces disagreement between signal classes instead of averaging it away — and names the disagreement so the reviewer knows what to investigate.</p>

        <h3>The six conflict types</h3>
        ${ragTable(
          ["Conflict Type", "Condition", "Meaning"],
          [
            ["Agreement — All Stable", "All Green", "No action required this cycle."],
            ["Mixed Early Warning", "Ambers only, no Red", "Monitor; no escalation yet."],
            ["Single Signal Watch", "One Amber", "Investigate the specific signal."],
            ["Anomaly Without Narrative", "CUSUM Red, EVM Amber/Green", "Schedule anomaly not yet explained by documents."],
            ["Leading Document Risk", "Doc Red, EVM Green", "Field conditions deteriorating before EVM shows it."],
            ["Multi-signal Red-review", "≥ 2 Red signals", "Escalation required — full signal package."],
          ]
        )}

        ${svgAgreementMap()}

        <h3>Why precedence matters</h3>
        <p>The classifier walks the table in order: it picks the <em>first</em> matching conflict, not the most common one. That preserves the leading-indicator property — a Document Red overshadowed by aggregate Greens still surfaces as "Leading Document Risk" if it would otherwise be missed.</p>
      `,
    },
    {
      id: "abm",
      title: "8. Module 05 — ABM Governance Layer",
      eyebrow: "Module 05",
      build: () => `
        <p class="kn-lead">"Agent-based" here means each authority role (PM, controls lead, program director) is modelled as an agent with explicit, executable decision rules. In <code>decision.js</code> those rules are pure functions — readable, testable, and auditable. Nothing is learned; everything is documented.</p>

        <h3>The three core functions</h3>
        ${formulaBlock([
          "deriveHealthState(signals):",
          "  Conservative dominance — the worst single signal class determines state.",
          "  Green only if ALL signal classes are Green.",
          "  Red-review if ≥2 signal classes are Red, OR CUSUM breach + Red forecast.",
          "",
          "classifyConflict(signals):  precedence order",
          "  1.  Multi-signal red-review  (≥2 Red)",
          "  2.  Anomaly without narrative  (CUSUM Red + EVM not Red)",
          "  3.  Forecast ahead of status  (Forecast Red + EVM Amber)",
          "  4.  Leading document risk  (Doc Red + EVM Green)",
          "  5.  Agreement  (all Green)",
          "  6.  Mixed early warning  (Ambers, no Red)",
          "",
          "deriveDecision(state, conflict, sector):",
          "  Maps state → action, authority, documentation, fairness gate requirement.",
          "",
          "Authority matrix — Layer 1 policy:",
          "  Green       → Project Manager / Controls Lead     — monthly cycle",
          "  Amber       → PM + Controls Lead                  — weekly loop",
          "  Red-review  → Program Director / PMO Lead         — 48 hours",
          "  Critical    → Contracting Officer / Executive     — immediate",
        ])}

        <h3>Why the rules are explicit, not learned</h3>
        <p>A governance system cannot rely on a black-box model. Every recommended action must be traceable to a specific rule that a reviewer can read aloud. During a dispute the PM must be able to say: "the system recommended escalation because two signal classes were Red and the conflict was classified as Multi-signal Red-review under the PCEIF authority matrix." That sentence requires explicit rules, not neural weights.</p>
        <p>This is also why <code>decision.js</code> is plain Javascript with no compilation step — anyone reading the code can verify the agency's authority matrix is implemented exactly as policy specifies.</p>
      `,
    },
    {
      id: "modules-06-10",
      title: "9. Modules 06–10 — Extended Simulation Stack",
      eyebrow: "Quantitative extensions",
      build: () => `
        <p class="kn-lead">Modules 06–10 cover construction and design risks that EVM does not catch. Each returns a status with an evidence metric that feeds Module 04.</p>

        <h3>Module 06 — Program Evaluation &amp; Review Technique (PERT)</h3>
        <p>Stochastic three-activity network with triangular activity sampling. The dominant path is aggregated across 5,000 iterations.</p>
        ${formulaBlock([
          ["te = (a + 4m + b) / 6", "deterministic three-point estimate"],
          ["dᵢ ~ Triangular(a, m, b)", "per-activity sample"],
          ["P80 duration = 80th percentile of simulated finishes", ""],
          ["criticality_index = | runs where path = critical | / 5000", ""],
        ])}
        ${ragTable(["Metric", "Green", "Amber", "Red"], [
          ["P80 vs baseline", { label: "≤ baseline", color: RAG.green }, { label: "+0 to +20%", color: RAG.amber }, { label: "> +20%", color: RAG.red }],
        ])}

        <h3>Module 07 — Line of Balance (LOB)</h3>
        <p>Leader (grading) versus follower (paving) crew velocity. SPI degradation slows the follower so the buffer compresses unit by unit.</p>
        ${formulaBlock([
          ["lag_per_unit = (1 / paving_rate) − (1 / grading_rate)", "schedule cost per linear unit"],
          ["buffer(u) = initial_buffer − u × lag_per_unit", "buffer at unit u"],
          ["min_buffer = minᵤ buffer(u)", "headline metric"],
        ])}
        ${ragTable(["Metric", "Green", "Amber", "Red"], [
          ["min crew buffer (days)", { label: "> 3.0", color: RAG.green }, { label: "1.5–3.0", color: RAG.amber }, { label: "≤ 1.5", color: RAG.red }],
        ])}

        <h3>Module 08 — Critical Chain Project Management (CCPM)</h3>
        <p>Buffer-consumption fever chart. The amber threshold tracks chain completion; the red threshold sits a third of the remaining range above.</p>
        ${formulaBlock([
          ["amber_line = % complete", ""],
          ["red_line   = % complete + (100 − % complete) / 3", ""],
        ])}
        ${ragTable(["Zone", "Condition"], [
          [{ label: "Green", color: RAG.green }, "buffer consumed < % complete (below the amber line)"],
          [{ label: "Amber", color: RAG.amber }, "buffer consumed ≥ % complete"],
          [{ label: "Red", color: RAG.red }, "buffer consumed ≥ % complete + (100 − % complete) / 3"],
        ])}

        <h3>Module 09 — Reference Class Forecasting (RCF)</h3>
        <p>Flyvbjerg's outside-view debiasing. Replaces the inside-view estimate with the empirical distribution from a comparable reference class.</p>
        ${formulaBlock([
          ["multipliers = [ 1.00, 1.04, 1.10, 1.14, 1.15, 1.26, 1.38, 1.45, 1.52 ]", "airport-infrastructure reference class"],
          ["P50 prior = BAC × multipliers[ P50 ]", ""],
          ["P80 prior = BAC × multipliers[ P80 ]", "conservative debiased budget"],
          ["debiasing_factor = multipliers[ P80 ]", "headline metric"],
        ])}
        ${ragTable(["Metric", "Green", "Amber", "Red"], [
          ["P80 prior vs BAC", { label: "≤ +10%", color: RAG.green }, { label: "+10% to +25%", color: RAG.amber }, { label: "> +25%", color: RAG.red }],
        ])}

        <h3>Module 10 — Design Structure Matrix (DSM)</h3>
        <p>3×3 Arch / Structural / MEP dependency matrix. A unit architectural change is propagated through four passes; the cumulative rework multiplier is the coordination cost.</p>
        ${formulaBlock([
          "A = [ [0.0, 0.3, 0.1],   Arch    ← Structural, MEP",
          "      [0.5, 0.0, 0.2],   Struct  ← Arch, MEP",
          "      [0.4, 0.4, 0.0] ]  MEP     ← Arch, Structural",
          "",
          ["v⁰ = [1, 0, 0],   vᵗ⁺¹ = A · vᵗ", "propagation step"],
          ["rework_multiplier = Σᵢ Σₜ₌₀⁴ vᵢᵗ", "cumulative across 4 passes"],
        ])}
        ${ragTable(["Metric", "Green", "Amber"], [
          ["rework multiplier", { label: "≤ 2.5", color: RAG.green }, { label: "> 2.5", color: RAG.amber }],
        ])}
      `,
    },
    {
      id: "fairness",
      title: "10. The Fairness Gate",
      eyebrow: "Procedural safeguard",
      build: () => `
        <p class="kn-lead">An automated signal must never directly drive a contractual consequence. The fairness gate is the procedural step that ensures the contractor has a documented opportunity to explain field conditions before a fairness-sensitive Red-review becomes a formal action.</p>

        <h3>When it triggers</h3>
        <p>The fairness gate engages when the project state is Red-review <em>and</em> at least one fairness-sensitive signal is Red:</p>
        <ul class="kn-list">
          <li><strong>Document Risk Red</strong> — risk language identified against the contractor's record.</li>
          <li><strong>LOB Red</strong> — projected crew collision implies a productivity allegation.</li>
          <li><strong>CCPM Red</strong> — buffer exhaustion implies the contractor's schedule discipline.</li>
        </ul>

        <h3>What it requires</h3>
        <ul class="kn-list">
          <li>A written request to the contractor stating the signal and the evidence.</li>
          <li>A reasonable response timeframe (commonly 5 business days; agency policy may set the floor).</li>
          <li>The reviewer's acknowledgement that the response was solicited and either received or formally non-responded.</li>
        </ul>

        <h3>What it produces</h3>
        <p>The contractor's response — or the documented non-response — is recorded alongside the decision card in the audit trail. The decision cannot be recorded until the gate is acknowledged; this is a hard procedural block, not a soft reminder.</p>

        <p class="kn-callout">The fairness gate is a workflow gate, not a statistic. It is never expressed as a score or a percentage; it is either acknowledged or it is not.</p>
      `,
    },
    {
      id: "decision",
      title: "11. The Decision Card & Audit Trail",
      eyebrow: "Accountable record",
      build: () => `
        <p class="kn-lead">The decision card is the single artefact that captures, for each governed decision, who decided, what they decided, on what evidence, under what authority, and on what date. It is the record that survives the project — the basis for independent audit, dispute resolution, and program-level reporting.</p>

        <h3>Decision card fields</h3>
        ${ragTable(
          ["Field", "Why it matters"],
          [
            ["Derived state", "The PCEIF rule output — Green / Amber / Red-review / Critical — that triggered this card."],
            ["Conflict type", "The named disagreement Module 04 surfaced; tells the reviewer what to investigate."],
            ["Recommended action", "The specific governance step the authority matrix returned; not a directive, a recommendation."],
            ["Authority", "The role entitled to record the decision. A different role recording it must document the override rationale."],
            ["Documentation required", "The artefacts (variance report, recovery plan, corrective-action notice) the agency policy requires for this state."],
            ["Fairness gate", "Whether the procedural contractor-response gate is required and, if so, acknowledged."],
            ["Reviewer rationale", "The reviewer's plain-language explanation. Required minimum length; recorded verbatim."],
            ["Recorded by / at", "Named human, role, and UTC timestamp at the moment of recording."],
          ]
        )}

        <h3>What "named human approval" means</h3>
        <p>A status change is not a decision. A decision has a name attached, a role attached, a rationale attached, and a timestamp. PCEIF will not let a Red-review be recorded as Approved without a rationale that meets the minimum length and a reviewer identifier. This is the same reason the fairness gate cannot be auto-acknowledged.</p>

        <h3>Audit export</h3>
        <p>The Export Audit JSON action writes the full signal package, derived decision, rationale, fairness acknowledgement, and timestamps to a structured file suitable for ingestion into a program-level audit register. UTC ISO timestamps are preserved alongside the local display time, so the record is unambiguous across time zones.</p>

        <h3>Why structured export matters</h3>
        <p>Program-level reporting and independent audit do not work on PDFs. They work on structured records that can be queried, aggregated, and reconciled. A decision card that exports cleanly is one that can be audited at scale — and one that protects the reviewer who recorded it.</p>
      `,
    },
  ];

  window.LIN_KNOWLEDGE = { terms: TERMS, glossary: GLOSSARY, topics: TOPICS, library: LIBRARY };

  /* ---------- knowledge page rendering — two-panel navigator + content ---------- */
  function renderKnowledgePage() {
    const root = document.getElementById("knowledge-root");
    if (!root) return;
    let selectedId = (LIBRARY[0] && LIBRARY[0].id) || "pceif";

    function navHtml() {
      return LIBRARY.map((t) =>
        `<li><button class="kn-nav-btn${t.id === selectedId ? " active" : ""}" data-topic="${esc(t.id)}">${esc(t.title)}</button></li>`
      ).join("");
    }
    function contentHtml() {
      const t = LIBRARY.find((x) => x.id === selectedId) || LIBRARY[0];
      return `<article class="kn-article">
        <p class="eyebrow">${esc(t.eyebrow || "Knowledge Library")}</p>
        <h2 class="kn-h kn-h-art">${esc(t.title)}</h2>
        ${t.build()}
      </article>`;
    }
    function paint() {
      root.innerHTML =
        `<div class="kn-lib">
           <aside class="panel kn-nav">
             <p class="eyebrow">Knowledge Library</p>
             <ol class="kn-nav-list">${navHtml()}</ol>
           </aside>
           <section class="panel kn-content">${contentHtml()}</section>
         </div>`;
      root.querySelectorAll(".kn-nav-btn").forEach((b) => b.addEventListener("click", () => {
        selectedId = b.dataset.topic;
        paint();
        const article = root.querySelector(".kn-article");
        if (article) article.scrollIntoView({ behavior: "smooth", block: "start" });
      }));
    }
    paint();
  }

  window.LinKnowledge = { renderKnowledgePage };
})();
