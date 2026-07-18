/* ============================================================
   Lin Project Radar, knowledge.js
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
  // project-controls reviewer cares). Impact is curated static text, it
  // must read correctly even if the AI backend is down.
  const TERMS = [
    { term: "EVM", definition: "Earned Value Management compares planned value, earned value, and actual cost to show cost and schedule performance against the baseline.", formula: "PV, EV, AC",
      impact: "Gives reviewers an objective, normalized read on cost and schedule health instead of gut feel, so problems surface in the numbers before they show up in the field." },
    { term: "PV / Planned Value", definition: "Budgeted value of work planned to be complete by a given date.", formula: "PV = planned budgeted work to date",
      impact: "Sets the yardstick the other EVM measures are read against; if PV is wrong (bad baseline), every derived index is misleading." },
    { term: "EV / Earned Value", definition: "Budgeted value of work actually completed by a given date.", formula: "EV = budgeted value of completed work",
      impact: "Anchors performance to work actually done, not money spent or time elapsed, the core defense against 'we spent the budget so we must be on track.'" },
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
      impact: "Lets a project's risk rating move with new reporting-cycle evidence instead of staying anchored to a stale assumption, the basis for defensible, evolving judgments." },
    { term: "SPC", definition: "Statistical Process Control for monitoring process signals against control thresholds.", formula: "Observed signal vs. control threshold",
      impact: "Separates normal period-to-period noise from a real shift, so reviewers don't over-react to one bad month or miss a slow, steady decline." },
    { term: "CUSUM", definition: "Cumulative Sum logic that detects accumulating drift over time, before a single-period variance would trip a threshold.", formula: "CUSUM = cumulative deviation signal",
      impact: "Catches the slow slide that single-period variance reports hide; a breach hands an early, evidence-backed warning to governance before the trend becomes a crisis." },
    { term: "RFI", definition: "Request for Information. A formal project question or clarification record. Flagged RFIs contribute to document-risk evidence.", formula: "Document evidence input",
      impact: "Clusters of aging or scope-disputed RFIs often predict cost/schedule impact before EVM moves, leading document-risk evidence reviewers should act on early." },
    { term: "RFA", definition: "Request for Approval (or Authorization), a formal request for a decision or sign-off, e.g. a substitution or deviation.", formula: "Document evidence input",
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
    { term: "Fairness Gate", definition: "A mandatory workflow step on fairness-sensitive red-reviews: contractor response opportunity must be acknowledged before a decision can be recorded. It is a procedural gate, never a statistic.", formula: "Workflow step, blocks recording until acknowledged",
      impact: "Protects due process: it prevents a model signal from becoming a formal action against a contractor before they have had a documented chance to respond, defensible and auditable." },
    { term: "Red-review", definition: "The evidence package has crossed the threshold for accountable HUMAN review. It never means automatic action.", formula: "≥2 red signals, or CUSUM breach + red forecast",
      impact: "Defines the bright line where a project must get named, senior human attention with a full evidence package, never an automated penalty, always a review." },
    { term: "Governance Recommendation", definition: "The recommended action, responsible authority, and required documentation that the rules derive from a project's signal package.", formula: "Signal → Evidence → Threshold → Explanation → Consequence → Action",
      impact: "Converts analysis into an accountable next step with an owner and a paper trail; it is a recommendation a named human records, the tool never decides on its own." },
    { term: "PCEIF", definition: "Public Capital EVM Intelligence Framework: a signal-to-action governance framework for public AEC capital programs. Signals from four model classes feed explicit governance rules that recommend an action, an authority, and required documentation.", formula: "Signal → Evidence → Threshold → Explanation → Consequence → Action",
      impact: "Ties together the metrics, the anomaly and document evidence, and the decision rules so a public-program reviewer gets one explainable, auditable path from signal to governed action." }
  ];

  /* ---------- assistant topics: keywords → curated answer ---------- */
  const TOPICS = [
    {
      id: "pceif",
      keywords: ["pceif", "framework", "what is this", "purpose", "praxis", "research"],
      title: "What PCEIF is",
      body: "PCEIF (Public Capital EVM Intelligence Framework) is a signal-to-action governance framework for public AEC capital programs. Four signal classes (EVM, Monte Carlo forecast, SPC/CUSUM anomaly, and document risk) feed explicit governance rules that derive a health state, classify signal conflict, and recommend an action with a named authority and required documentation. This site is a synthetic demonstration of that workflow."
    },
    {
      id: "five-status",
      keywords: ["status", "five status", "5 status", "complete", "yellow", "blue", "rag", "red amber green", "why five", "authority matrix", "closeout"],
      title: "Why five status levels (Complete / Green / Yellow / Amber / Red)",
      body: "Traditional RAG collapses important distinctions. PCEIF uses five status levels for three reasons. (1) RAG hides the gap between 'slightly off' and 'stalled', both show as Red. (2) Complete (blue) marks projects that have hit their milestone and transition to closeout governance, different authority, different documentation. (3) Yellow is an early-warning band between Green and Amber: minor variance, still recoverable, requiring a PM weekly check-in before it escalates. Each status maps to a distinct authority/timeframe in the Cat 8.1 matrix."
    },
    {
      id: "radar",
      keywords: ["radar", "portfolio", "blip", "scope", "circle", "ring", "sector", "distance", "center"],
      title: "Reading the portfolio scope",
      body: "Each blip is a synthetic project. Distance from center = drift from baseline (healthy projects sit near center). Angle = delivery sector: Design, Construction, or Hybrid. Blip color = derived health state. Click a blip, or use the equivalent list below the scope, to open that project's Detail page (ledger, decision card, and all five signals for that project)."
    },
    {
      id: "module01",
      keywords: ["module 01", "module 1", "hybrid", "dynamic simulation", "evm module", "cpi", "spi", "eac", "earned value"],
      title: "Cat 1.1: Hybrid Dynamic Simulation",
      body: "Cat 1.1 covers the EVM core: CPI (cost performance, EV/AC) and SPI (schedule performance, EV/PV) against the baseline. On a project's Detail page the Monte Carlo runs 5,000 iterations sampled from a signal-derived Beta-PERT distribution, with P50 and P80 read from the simulated array. P80 is the planning-conservative figure used for contingency and escalation decisions."
    },
    {
      id: "module02",
      keywords: ["module 02", "module 2", "cusum", "spc", "anomaly", "drift", "trend", "control"],
      title: "Cat 1.2: SPC / CUSUM Anomaly Monitor",
      body: "Cat 1.2 watches for accumulating drift. On a project's Detail page CUSUM is a REAL computation: the standard two-sided tabular recursion runs over the project's metric series and a breach is flagged only when the cumulative statistic crosses the decision interval H. It feeds the governance rules, including the 'Anomaly without narrative' conflict when the document record offers no explanation."
    },
    {
      id: "module03",
      keywords: ["module 03", "module 3", "document", "doc risk", "rfi", "submittal", "extraction", "keyword"],
      title: "Cat 1.3: Document-Risk Extraction",
      body: "Cat 1.3 scores risk language in project records (RFIs, submittals, QC comments, procurement notes) using visible keyword rules, the same rules the Manage Projects page runs. The score and the matched excerpt feed the signal ledger. In this demo extraction is rule-based and transparent; there is no live NLP or LLM."
    },
    {
      id: "module10",
      keywords: ["module 10", "module 10", "synthesis", "conflict", "disagreement", "leading", "forecast ahead", "conservative dominance"],
      title: "Cat 6.1: Conservative Dominance (Signal Synthesis)",
      body: "Cat 6.1 classifies disagreement between signal classes instead of averaging it away. Conflict types: Multi-signal red-review, Anomaly without narrative, Forecast ahead of status, Leading document risk, Agreement, low risk, and Mixed early warning. The precedence order is deliberate and documented in decision.js. Conservative dominance: the worst single signal drives the overall state. Cat 6.1 is the baseline that Cat 7.1–Cat 7.9 cross-check before Cat 8.1 records the decision."
    },
    {
      id: "module19",
      keywords: ["module 19", "module 09", "abm", "agent", "governance layer", "decision rules", "authority"],
      title: "Cat 8.1: ABM Governance Layer",
      body: "Cat 8.1 is the agent-based governance layer: each authority role (PM, controls lead, program director) is an agent with explicit decision rules. Those rules live in decision.js as pure, readable functions (deriveHealthState, classifyConflict, and deriveDecision), and the Signals page calls them directly. The decision card you see on the Portfolio and Project Detail pages IS this module's output. Cat 8.1 is the LAST module in the stack, the artefact that survives the reporting cycle."
    },
    {
      id: "fairness",
      keywords: ["fairness", "gate", "contractor", "response opportunity", "blocks", "checkbox"],
      title: "How the fairness gate works",
      body: "When a project is fairness-sensitive (its signals implicate delivery responsibility) AND its state is Red-review, the decision card shows a mandatory acknowledgement: contractor response opportunity will be provided before any formal action. 'Record decision' stays disabled until the reviewer checks it and enters a rationale. The gate is a procedural workflow step, it is never expressed as a score or percentage."
    },
    {
      id: "decision",
      keywords: ["decision card", "record", "rationale", "authority", "documentation", "audit", "export"],
      title: "Decision card and audit export",
      body: "The decision card shows the derived state, conflict type, recommended action, authority role, and documentation required. A named reviewer must type a rationale (min 20 characters) before recording. 'Export audit JSON' downloads the full signal package, derived decision, rationale, fairness acknowledgement, and timestamps, display times use your selected timezone, and the record always keeps a UTC ISO timestamp for integrity."
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
      body: "On the Manage Projects page, each active project has an Archive action. Archiving removes it from the portfolio scope and all active views without deleting it, it moves to the Archived list, persists in localStorage, and can be restored with one click. Every archive and restore is logged in the project event log."
    },
    {
      id: "ingest",
      keywords: ["ingest", "upload", "paste", "doc type", "approve", "reject", "delta"],
      title: "Ingesting a document",
      body: "Pick a project and document type, then paste or upload text (.txt / .csv / PDF-extracted text). The app runs the same visible keyword rules as Cat 1.3, shows exactly which rule fired and the proposed signal delta, and nothing changes until a human clicks Approve. Reject discards the proposal. Every ingest event is logged."
    },
    {
      id: "themes",
      keywords: ["theme", "light", "dark", "appearance"],
      title: "Themes",
      body: "Two themes over the same structure, Dark (default) and Light, switchable in the menu. Your choice persists in localStorage."
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
      body: "Everything here is synthetic demonstration data, no real project, agency, employer, contractor, or vendor. There is no backend, no LLM call, no analytics, and no tracking; this assistant is scripted from the knowledge library. No predictive-accuracy validation has been performed, and every recommended action requires named human approval."
    }
  ];

  /* ---------- (legacy) static glossary, superseded by LIBRARY below ----------
     Kept around because removing it has no benefit; the page renders LIBRARY. */
  const T = {
    green: "var(--clear-green)", amber: "var(--radar-amber)", red: "var(--alarm-red)",
  };
  const GLOSSARY = [
    { term: "EVM, Earned Value Management",
      definition: "A project controls methodology that integrates scope, schedule, and cost to objectively measure project performance. Compares planned work against actual work completed and actual cost incurred." },
    { term: "CPI, Cost Performance Index",
      definition: "CPI = EV / AC. Measures cost efficiency. CPI = 1.00 means on budget; > 1.00 means under budget; < 1.00 means over budget.",
      thresholds: [
        { label: "Green: CPI ≥ 0.95", color: T.green },
        { label: "Amber: CPI 0.90–0.94", color: T.amber },
        { label: "Red: CPI < 0.90", color: T.red },
      ] },
    { term: "SPI, Schedule Performance Index",
      definition: "SPI = EV / PV. Measures schedule efficiency. SPI = 1.00 means on schedule; > 1.00 means ahead of schedule; < 1.00 means behind schedule.",
      thresholds: [
        { label: "Green: SPI ≥ 0.95", color: T.green },
        { label: "Amber: SPI 0.90–0.94", color: T.amber },
        { label: "Red: SPI < 0.90", color: T.red },
      ] },
    { term: "BAC, Budget at Completion",
      definition: "The total authorized budget for the project. The baseline against which earned value is measured. Established at contract award; changes only through approved change orders." },
    { term: "EV, Earned Value",
      definition: "The budgeted cost of work performed. EV = BAC × % complete (verified). Represents the monetary value of work actually accomplished." },
    { term: "AC, Actual Cost",
      definition: "The actual money spent to accomplish the work measured by EV. Comes from the pay application (amount paid to date)." },
    { term: "PV, Planned Value",
      definition: "The budgeted cost of work scheduled. Derived from the time-phased baseline schedule. Represents what was planned to be spent by a given date." },
    { term: "EAC, Estimate at Completion",
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
    { term: "CUSUM, Cumulative Sum Control Chart",
      definition: "Statistical process control method that detects sustained drift in a time series. Applied to SPI across 12 reporting periods. Breach = cumulative drift exceeds the decision interval H (5σ). A breach means the pattern is systemic, not noise.",
      thresholds: [
        { label: "Green: drift below watch level", color: T.green },
        { label: "Amber: drift approaching control limit", color: T.amber },
        { label: "Red: CUSUM breaches threshold", color: T.red },
      ] },
    { term: "SPC, Statistical Process Control",
      definition: "The use of statistical methods to monitor and control a process. CUSUM is the SPC method used in PCEIF to detect schedule drift." },
    { term: "PERT, Program Evaluation & Review Technique",
      definition: "Stochastic network scheduling method. Each activity has optimistic (a), most likely (m), and pessimistic (b) durations sampled from a triangular distribution. P80 project duration and path criticality index are computed from 5,000 iterations. Formula: te = (a + 4m + b) / 6" },
    { term: "LOB, Line of Balance",
      definition: "Production scheduling method for repetitive work. Plots crew velocity (units/day) for sequential operations. Flags when the buffer between operations collapses, a leading indicator of schedule collision before it shows in EVM." },
    { term: "CCPM, Critical Chain Project Management",
      definition: "Aggregates safety margins from individual activities into a single project buffer. Fever chart maps buffer consumption against chain completion. Entering the red zone means the buffer is being consumed faster than progress is being made." },
    { term: "RCF, Reference Class Forecasting",
      definition: "Flyvbjerg's debiasing method. Uses historical cost overrun data from similar projects to establish a prior probability distribution, bypassing optimism bias in contractor estimates. P80 RCF prior is the statistically-adjusted realistic budget." },
    { term: "DSM, Design Structure Matrix",
      definition: "Models information dependencies between design disciplines (Arch, Structural, MEP). Simulates how a scope change propagates through design iterations. Rework multiplier > 2.5 indicates high coordination risk." },
    { term: "ABM, Agent-Based Model",
      definition: "The governance decision layer in PCEIF. Takes the signal package from all modules and derives a conflict classification, recommended action, named authority, and fairness gate requirement. Does not make decisions, surfaces the structured recommendation for human approval." },
    { term: "Fairness Gate",
      definition: "A mandatory step requiring contractor explanation before formal action is recorded. Triggered when a fairness-sensitive signal (document risk, LOB, CCPM) reaches Red. Prevents automated model outputs from driving contractual consequences without human review." },
    { term: "Red-review",
      definition: "PCEIF governance state requiring Program Director / PMO lead review. Triggered when ≥2 signal classes are Red, or CUSUM breach + Red forecast. Requires full signal package, assigned owner, rationale, response timeframe, and audit record." },
  ];

  /* ---------- Cat 2.1–Cat 3.2, 11, Method Library accordion entries ---------- */
  TOPICS.push(
    {
      id: "module04",
      keywords: ["module 04", "module 4", "pert", "program evaluation", "network criticality", "triangular", "path criticality"],
      title: "Cat 2.1: Program Evaluation & Review Technique (PERT)",
      body: "PERT is a stochastic network scheduling method. Each activity has three duration estimates, optimistic (a), most likely (m), and pessimistic (b), and is sampled from a triangular distribution. The classic deterministic three-point estimate is te = (a + 4m + b) / 6; the simulation aggregates the dominant path across 5,000 runs. P80 duration is the conservative finish (80% of runs at or under). The path-criticality index is the fraction of runs in which the structural path was on the critical path, the higher it is, the less float you have to absorb a slip. In this implementation a lower project SPI widens the pessimistic bound, so an already-drifting schedule grows a fatter P80 tail. Thresholds: Green P80 within baseline; Amber P80 up to +20%; Red P80 > +20%.",
    },
    {
      id: "module05",
      keywords: ["module 05", "module 5", "lob", "line of balance", "production velocity", "crew", "buffer"],
      title: "Cat 2.2: Line of Balance (LOB)",
      body: "LOB tracks production velocity for sequential, repetitive work, grading runs ahead of paving, paving runs ahead of striping, and so on. Each crew has a rate in units/day; the buffer is the schedule gap between leader and follower at every unit. When the follower's rate slips, that buffer compresses unit by unit and a crew-on-crew collision is being telegraphed before EVM moves. Here, lower project SPI slows the follower (paving) so the minimum crew buffer shrinks. Buffer collapse is a leading schedule indicator: it shows up in the LOB chart before it shows up in CPI or SPI. Thresholds: Green buffer > 3 days; Amber 1.5–3 days; Red ≤ 1.5 days.",
    },
    {
      id: "module06",
      keywords: ["module 06", "module 6", "ccpm", "critical chain", "buffer", "fever chart"],
      title: "Cat 2.3: Critical Chain Project Management (CCPM)",
      body: "CCPM (Goldratt) aggregates the safety margin embedded in individual activity estimates into a single project buffer at the end of the critical chain. The fever chart plots buffer-consumed % against chain-complete %. Two thresholds drive the zones: the amber line tracks chain completion (buffer consumed ≥ % complete), burning buffer at the same rate progress is being made; the red line sits a third of the remaining range above (buffer consumed ≥ % complete + (100 − % complete) / 3), burning buffer faster than the chain can complete. Crossing into red means the buffer will run out before the work does. Thresholds: Green below the amber line; Amber buffer consumed ≥ % complete; Red buffer consumed ≥ % complete + (100 − % complete) / 3.",
    },
    {
      id: "module07",
      keywords: ["module 07", "module 7", "rcf", "reference class", "forecasting", "flyvbjerg", "debias", "optimism bias"],
      title: "Cat 3.1: Reference Class Forecasting (RCF)",
      body: "Reference Class Forecasting comes from Bent Flyvbjerg's research on optimism bias in large infrastructure projects: bottom-up estimates systematically underestimate cost because they reason from the inside view (this project's plan) rather than the outside view (how comparable projects have actually performed). RCF replaces the inside-view estimate with an empirical prior, the distribution of historical overrun multipliers from a comparable reference class. This implementation uses an airport-infrastructure multiplier set [1.00 to 1.52]; the P80 multiplier is the conservative debiasing factor applied to BAC. The debiasing factor is the multiplier itself: x1.38 means the outside view says comparable projects finished 38% over their baseline. The P80 RCF prior is the realistic planning budget to compare against the bottom-up EAC. Thresholds: Green P80 within +10% of BAC; Amber +10–25%; Red > +25%.",
    },
    {
      id: "module08",
      keywords: ["module 08", "module 8", "dsm", "design structure matrix", "rework", "propagation", "arch", "structural", "mep", "dependency"],
      title: "Cat 3.2: Design Structure Matrix (DSM)",
      body: "A DSM captures information-flow dependencies between work elements as a square matrix: each off-diagonal entry A[i][j] is the strength of i's dependence on j. Here the elements are the three design disciplines, Architectural, Structural, MEP, and the off-diagonals encode how much a unit change in one cascades into the others. Architectural decisions flow downstream into both Structural and MEP, so an arch scope change ripples through the matrix; structural and MEP changes also feed back. The simulation propagates a unit architectural change vector through the matrix for four passes and accumulates the rework absorbed in each discipline. The total cumulative rework multiplier is the coordination cost: a multiplier above 2.5 indicates that one unit of arch change is generating more than 2.5 units of downstream rework, high coordination risk. Thresholds: Green rework multiplier ≤ 2.5; Amber > 2.5.",
    },
    {
      id: "module11",
      keywords: ["module 11", "module 11", "dst", "dempster", "shafer", "belief", "evidence combination", "conflict mass", "bpa"],
      title: "Cat 7.1: Dempster-Shafer Evidence Combination (DST)",
      body: "Dempster-Shafer Theory (DST) is a mathematical framework for reasoning under uncertainty when evidence comes from multiple independent sources. Unlike conservative dominance (Cat 6.1), which takes the worst single signal, DST combines all four signal classes into a belief distribution over {Green, Amber, Red, Unknown}. Each source assigns a basic probability assignment (BPA), a mass function over subsets of the frame of discernment. Dempster's combination rule then merges sources iteratively, redistributing conflict mass. The conflict mass K measures how much the sources disagree: K > 0.3 is flagged as high inter-signal disagreement, which is itself a governance signal. Academic context: Dempster (1967) and Shafer (1976). When DST agrees with Cat 6.1, both methods corroborate each other. When they diverge, the disagreement is a finding: it tells the governance layer that the evidence picture is genuinely ambiguous rather than clear-cut, and that no single framing captures the full risk.",
    },
    {
      id: "module12",
      keywords: ["module 12", "rough sets", "rough set theory", "lower approximation", "upper approximation", "boundary region", "indeterminate", "pawlak"],
      title: "Cat 7.2: Rough Set Theory Classification",
      body: "Rough Set Theory (Pawlak, 1982) provides a mathematical framework for classifying objects when available information is incomplete or imprecise. The core insight is that some concepts, like 'this project is Green', cannot be precisely defined with available attributes. Instead, rough sets define three regions: the lower approximation contains all objects (states) that definitely belong to the concept (over 75% of signals agree); the upper approximation contains all objects that possibly belong; and the boundary region, upper minus lower, is the indeterminate zone where evidence is insufficient to classify with certainty. A project falls in the definite Green region when the preponderance of evidence is unambiguous; it falls in the boundary when signals are mixed and classification is uncertain. A wide boundary region is itself a governance signal: it means the evidence does not yet support a confident classification. Unlike DST (Cat 7.1), rough sets do not assign probability masses, they provide a set-theoretic answer: yes, possibly, or unknown. Thresholds: Definite requires > 75% signal agreement for a state; any support places a state in the upper approximation.",
    },
    {
      id: "module13",
      keywords: ["module 13", "neutrosophic", "neutrosophic logic", "truth", "indeterminacy", "falsity", "t i f", "smarandache"],
      title: "Cat 7.3: Neutrosophic Logic",
      body: "Neutrosophic Logic (Smarandache, 1995) extends fuzzy logic by introducing three independent truth-value dimensions: Truth (T), Indeterminacy (I), and Falsity (F). Unlike classical logic (T + F = 1) and fuzzy logic (T + F = 1 as a constraint), neutrosophic values are independent, T + I + F need not equal 1, and can exceed 1 or be less than 1. This is a deliberate feature: it models genuine epistemic uncertainty as a separate dimension rather than forcing it to be the residual of known truths and falsehoods. In project risk terms: T represents the degree to which the evidence supports a given status; F represents evidence against it; I represents the portion of evidence that is genuinely undetermined or contradictory, measurement noise, missing data, or conflicting signals that cannot be resolved by collecting more of the same kind of data. High indeterminacy (I > 30%) is a governance signal: it means the evidence architecture itself needs strengthening before a confident classification is possible, not just that the project is 'in between' Green and Red. This module combines the four primary signal classes disjunctively for T (union of evidence) and conjunctively for I and F, producing a three-component characterization of the current signal package.",
    },
    {
      id: "module14",
      keywords: ["module 14", "interval fuzzy", "interval-valued fuzzy", "fuzzy interval", "membership interval", "uncertainty interval", "ifs"],
      title: "Cat 7.4: Interval-valued Fuzzy Sets",
      body: "Interval-valued Fuzzy Sets (IVFS) extend classical fuzzy sets by representing membership as a range [lower, upper] rather than a single value. The interval reflects measurement uncertainty in the underlying data, the range of possible membership values given the precision of the inputs. For airport construction EVM, the primary sources of input uncertainty are: Schedule of Values (SoV) line-item accuracy of approximately +/-2% of contract value affecting Earned Value, and Pay Application rounding of approximately +/-1% affecting Actual Cost. These compound into a CPI/SPI uncertainty range of approximately +/-3 percentage points. IVFS propagates this uncertainty through the fuzzy membership functions for Green, Amber, and Red states, producing an interval rather than a point estimate. A wide interval signals that the current input precision is insufficient to reliably distinguish between adjacent states, e.g., a Green/Amber boundary crossing falls within the uncertainty band. The uncertainty width metric summarizes the total interval spread: High (> 0.30 width) means the classification is sensitive to input noise; Moderate (0.15-0.30) means some sensitivity; Low (< 0.15) means the signal package is sufficiently precise for reliable classification. References: Sambuc (1975); Zadeh (1975); Turksen (1986).",
    },
  );

  /* ---------- Knowledge Library, 11 narrative topics with formulas + SVG ---------- */
  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  // Small typography helpers shared by every topic body.
  // Reference tables render the palette as label ink → -text variants, which
  // are the darkened set on Miami and the plain fills on the dark themes.
  const RAG = {
    green: "var(--status-green-text)", amber: "var(--status-amber-text)", red: "var(--status-red-text)",
    yellow: "var(--status-yellow-text)", complete: "var(--status-complete-text)",
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

  // PCEIF signal-to-action flow (Topic 1), two rows so the diagram is large
  // and readable: 4 boxes across the top, 3 boxes centred underneath, with an
  // L-bend connector from box 4 down to box 5.
  function svgPceifFlow() {
    const row1 = [
      "Documents + Schedule + Cost",
      "Signal Generation: Cat 1.1–Cat 3.2",
      "Baseline Synthesis: Cat 6.1",
      "Evidence Combination: Cat 7.1–Cat 7.9"
    ];
    const row2 = [
      "Governance Decision: Cat 8.1",
      "Named Human Approval",
      "Audit Record"
    ];
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

    let out = `<svg viewBox="0 0 ${w} ${h}" width="100%" height="auto" preserveAspectRatio="xMidYMid meet" class="kn-svg kn-svg-flow" role="img" aria-label="PCEIF signal-to-action flow (two rows)">`;
    out += `<defs><marker id="kn-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="var(--phosphor)"/></marker></defs>`;

    // Helper: draw a labelled box with wrapped text + a right-pointing arrow to
    // the next box in the same row.
    function drawBox(label, x, y, isLastInRow) {
      let s = "";
      s += `<rect x="${x}" y="${y}" width="${bw}" height="${bh}" rx="10"
        fill="color-mix(in srgb, var(--phosphor) 10%, var(--surface-soft))"
        stroke="var(--phosphor)" stroke-width="2"></rect>`;
      // wrap at ~22 chars per line (14px text fits 200-px-wide box with padding)
      const words = label.split(" "); const lines = []; let cur = "";
      words.forEach((wd) => {
        if ((cur + " " + wd).trim().length > 22) { if (cur.trim()) lines.push(cur.trim()); cur = wd; }
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
    let out = `<svg viewBox="0 0 ${w} ${h}" width="100%" height="auto" class="kn-svg" role="img" aria-label="Signal stack of 10 categories and Portfolio Health feeding the governance decision">`;
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
    out += `<text x="620" y="142" text-anchor="middle" class="kn-svg-t" fill="var(--text)" font-weight="700">Cat 6.1</text>`;
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
    let out = `<svg viewBox="0 0 ${w} ${h}" width="100%" height="auto" class="kn-svg" role="img" aria-label="EVM S-curve: PV vs EV vs AC with CV and SV gaps">`;
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
    [["PV, planned value", "var(--phosphor)"], ["EV, earned value", "var(--clear-green)"], ["AC, actual cost", "var(--alarm-red)"]]
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
    let out = `<svg viewBox="0 0 ${w} ${h}" width="100%" height="auto" class="kn-svg" role="img" aria-label="Monte Carlo simulated EAC distribution with P50 and P80 markers">`;
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
    let out = `<svg viewBox="0 0 ${w} ${h}" width="100%" height="auto" class="kn-svg" role="img" aria-label="CUSUM statistic vs decision interval H over 12 periods">`;
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

  // Cat 7.1 agreement map (Topic 7)
  function svgAgreementMap() {
    const w = 720, h = 200;
    const nodes = [["EVM", "var(--clear-green)", 100], ["FORECAST", "var(--radar-amber)", 280], ["CUSUM", "var(--alarm-red)", 460], ["DOC", "var(--clear-green)", 620]];
    let out = `<svg viewBox="0 0 ${w} ${h}" width="100%" height="auto" class="kn-svg" role="img" aria-label="Signal class agreement map">`;
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
        <p class="kn-lead">PCEIF, the <strong>Public Capital EVM Intelligence Framework</strong>, converts the signals that a public capital program already generates into a structured, accountable governance action with a named authority and a documented audit trail, using 103 analytical modules across 10 project-level categories and the portfolio-level Health suite. Lin Opus Gubernatio is the platform that implements the framework.</p>

        <h3>The problem it solves</h3>
        <p>Standard Earned Value Management produces excellent data. It does not produce a decision. A PM looking at CPI 0.88 in period 4 has no structured path to a defensible escalation: who must act, on what timeframe, with what documentation, under whose authority. The data exists; the governance link is missing.</p>
        <p>PCEIF closes that gap. Signals trigger an explicit rule set; the rule set returns a specific action, a specific authority, and the documentation required. The PM still records the decision, the framework simply makes the recommendation traceable.</p>

        <h3>Two-layer architecture</h3>
        <p>103 analytical modules across 10 project-level categories and the portfolio-level Health suite feed two layers of governance. Cat 1–5 generate signals. Cat 6 synthesizes them into a baseline state. Cat 7 quantifies confidence through twenty independent evidence-combination methods. Cat 8 produces the governance decision card. Cat 9 assesses data integrity. Cat 10 identifies the optimal decision pathway. Portfolio Health (PH) sits outside the numbered stack, comparing each project against the rest of the program.</p>
        <ul class="kn-list">
          <li><strong>Layer 1, Agency Governance.</strong> Sets the policy framework: the authority matrix, escalation thresholds, fairness rules, audit requirements. Established by the program owner; not changed per project.</li>
          <li><strong>Layer 2, PM Decision Architecture.</strong> Takes that policy and the project's signal package and surfaces, for each reporting cycle, the specific action the PM should record (or override, with rationale).</li>
        </ul>

        <h3>Signal-to-action mechanism</h3>
        <pre class="kn-flow">Documents + Schedule + Cost Data
        ↓
Cat 1–5: Signal Generation (57 modules)
        ↓
Cat 6: Signal Synthesis (4 modules), Conservative Dominance baseline
        ↓
Cat 7: Evidence Combination (20 modules), Confidence quantification
        ↓
PH: Portfolio Health (5 modules), Portfolio anomaly detection
        ↓
Cat 9: Data Integrity (7 modules), Input quality assessment
        ↓
Cat 10: Decision Optimization (7 modules), Optimal action selection
        ↓
Cat 8: Governance & Compliance (9 modules), Named authority + audit trail
        ↓
Named Human Approval → Audit Record</pre>

        <h3>What's different from standard EVM</h3>
        <ul class="kn-list">
          <li><strong>Standard EVM:</strong> compute CPI / SPI → report to management.</li>
          <li><strong>PCEIF:</strong> run 103 analytical modules → detect conflict → classify state → surface the action, authority, and documentation, <em>before</em> the next reporting cycle closes.</li>
        </ul>

        <h3>The role of AI</h3>
        <p>AI (Claude API, Anthropic) explains and summarizes using keyword-matched retrieval from the knowledge library. It does <strong>not</strong> make governance decisions. Every recommended action requires a named human approval before it is recorded; the AI's job is to make that approval well-informed, not to replace it. This is a design constraint, not a performance limitation.</p>
      `,
    },
    {
      id: "why-108-modules",
      title: "Why 103 modules across 10 categories and Portfolio Health",
      eyebrow: "Framework depth",
      build: () => `
        <p class="kn-lead">Public capital projects are complex adaptive systems. A single EVM index (CPI or SPI) captures cost and schedule performance but misses the systemic, probabilistic, and qualitative dimensions that determine whether a project will succeed. PCEIF addresses this through four principles.</p>

        <h3>1. No human can compute 103 analyses simultaneously</h3>
        <p>A senior PM reviewing a monthly report might check CPI, SPI, and open RFIs. PCEIF runs 103 analytical methods in milliseconds, probabilistic forecasts, anomaly detection, uncertainty reasoning, optimization, data integrity checks, and governance compliance, all before the PM opens their laptop. The platform does not replace human judgment; it gives the PM a complete evidence package to exercise that judgment.</p>

        <h3>2. Convergence equals confidence</h3>
        <p>When 90 of 103 methods agree on a Red classification, the PM can act with high confidence. When methods diverge, some showing Amber, others Red, the divergence itself is the finding: the project is in an ambiguous state that requires investigation before action. No single method can surface that ambiguity.</p>

        <h3>3. Each category adds a distinct lens</h3>
        <p>The 10 project-level categories, plus the portfolio-level Health suite, are not redundant:</p>
        <ul class="kn-list">
          <li><strong>Cat 1 (EVM)</strong>, shows what <em>is</em> happening.</li>
          <li><strong>Cat 2–3 (Simulation)</strong>, shows what <em>will</em> happen.</li>
          <li><strong>Cat 4 (Documents)</strong>, shows what <em>is being said</em>.</li>
          <li><strong>Cat 5 (Dynamics)</strong>, shows how components <em>interact</em>.</li>
          <li><strong>Cat 6–7 (Synthesis)</strong>, shows what the evidence <em>collectively means</em>.</li>
          <li><strong>Cat 8 (Governance)</strong>, shows what <em>action is required</em>.</li>
          <li><strong>Cat 9 (Data Integrity)</strong>, shows how much to <em>trust the signals</em>.</li>
          <li><strong>Cat 10 (Optimization)</strong>, shows what the <em>best decision</em> is.</li>
          <li><strong>Portfolio Health (PH)</strong>, shows how this project <em>compares to the portfolio</em>.</li>
        </ul>

        <h3>4. What the 103-module count includes</h3>
        <p>All 103 modules are executable from standard project documents available in any public capital program. Every status derives from extracted data; a module whose required inputs are absent abstains and reports "Insufficient data" with the specific missing fields. No status is fabricated.</p>
      `,
    },
    {
      id: "five-status",
      title: "Why five status levels",
      eyebrow: "Governance model",
      build: () => `
        <p class="kn-lead">Traditional RAG (Red-Amber-Green) systems use three states. PCEIF uses five, Complete, Green, Yellow, Amber, Red, for three concrete reasons.</p>

        <h3>1. RAG collapses important distinctions</h3>
        <p>A project that is slightly behind schedule and a project that has completely stalled both show as Red under RAG. A PM responding to a slightly-behind project applies very different actions than one responding to a stalled project. Collapsing them to the same status loses the governance signal.</p>

        <h3>2. The Complete state enables closeout governance</h3>
        <p>Public capital programs have a distinct closeout phase, work is done, but sign-off, commissioning, and documentation must be completed. A Green state implies active monitoring is still required. A Complete state signals the project has met its targets and transitions to closeout governance, different authority, different documentation requirements.</p>

        <h3>3. Yellow provides an early warning band</h3>
        <p>The gap between Green (on track) and Amber (significant risk) is too wide: a project moving from Green to Amber has often already been in trouble for two or three reporting periods. Yellow captures the zone in between, minor variance, still recoverable, requiring PM attention before the next cycle. With 103 modules producing outputs, Yellow consensus across multiple categories marks the inflection point where a project is leaving the Green zone, and it is where early intervention prevents escalation.</p>

        <h3>The five-status authority matrix</h3>
        <table class="kn-table">
          <thead><tr><th>Status</th><th>Meaning</th><th>PM action</th></tr></thead>
          <tbody>
            <tr><td><span class="pill pill-complete">Complete</span></td><td>Milestone achieved, signed off</td><td>Closeout documentation</td></tr>
            <tr><td><span class="pill pill-green">Green</span></td><td>Fully on track</td><td>Routine monthly monitoring</td></tr>
            <tr><td><span class="pill pill-yellow">Yellow</span></td><td>Minor variance, early warning</td><td>PM weekly check-in</td></tr>
            <tr><td><span class="pill pill-amber">Amber</span></td><td>Significant risk, major bottleneck</td><td>PM + Controls Lead weekly review</td></tr>
            <tr><td><span class="pill pill-red">Red</span></td><td>Critical failure, escalation required</td><td>Program Director within 48 hours</td></tr>
          </tbody>
        </table>

        <h3>Why not more than five?</h3>
        <p>Six or more statuses create decision paralysis, the PM spends time debating whether a project is "Orange-Amber" vs "Deep-Amber" rather than acting. Five states map cleanly to five distinct governance responses with different authorities and timeframes.</p>
      `,
    },
    /* The former "stack" and "pm-advice" topics (19-module era) were removed:
       unreachable from the category nav and describing a superseded module
       count. Their architecture content lives on in "How the categories
       advise the PM" and the per-category articles. */
    {
      id: "module01",
      title: "4. Cat 1.1: Monte Carlo EAC Forecast",
      eyebrow: "Cat 1.1",
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
          ["EAC = BAC / CPI", "PCEIF default, assumes current efficiency continues"],
          ["EAC = AC + (BAC − EV)", "Optimistic, assumes future work on budget"],
          ["EAC = AC + (BAC − EV) / CPI", "Pessimistic, current CPI continues to completion"],
          ["VAC = BAC − EAC", "Variance at Completion"],
        ])}

        <h3>Reading CPI</h3>
        <p>CPI measures how many cents of completed work the project is getting for every dollar spent. A CPI of exactly 1.00 means the project is spending exactly what was budgeted for the work done, on budget. A CPI above 1.00 means the project is delivering more work than expected per dollar spent, under budget and efficient. A CPI below 1.00 means the project is spending more than the work is worth, over budget.</p>
        <p>Worked example: if EV is $900,000 and AC is $1,000,000, then <code>CPI = 900,000 / 1,000,000 = 0.90</code>. The project is spending $1.10 for every $1.00 of work completed. At that rate the independent EAC is <code>BAC / 0.90</code>, a 11% overrun projected to completion. Three sustained periods at CPI 0.90 is a recovery-plan trigger under most agency program-controls policies, not a watch item.</p>

        <h3>Reading SPI</h3>
        <p>SPI measures how much progress the project is making per dollar of planned progress. An SPI of 1.00 means the project is completing work exactly on the baseline schedule. An SPI above 1.00 means work is completing ahead of schedule. An SPI below 1.00 means the project is behind, less work has been completed than was planned by this date.</p>
        <p>Worked example: if EV is $720,000 and PV is $900,000, then <code>SPI = 720,000 / 900,000 = 0.80</code>. Only 80 cents of every planned dollar of progress has been earned, the project is 20% behind schedule as measured in cost terms. Note that SPI naturally converges toward 1.00 as the project nears closeout (all work must eventually be earned); it is most informative in the early and middle periods. CUSUM is used to detect the sustained SPI drift that single-period readings obscure.</p>
        <p>Both CPI and SPI should be read together. A CPI of 0.92 with an SPI of 0.88 tells a different story from a CPI of 0.92 with an SPI of 1.05, the first is over budget and behind schedule; the second is over budget but ahead of schedule, which may justify a different governance response.</p>

        <h3>Why PCEIF defaults to BAC / CPI</h3>
        <p>On public capital programs cost overruns compound. A project 10% over budget at month 6 rarely recovers to baseline by closeout, the inefficiency rate is sticky. <code>BAC / CPI</code> assumes the current rate continues, which is the most defensible assumption for an escalation conversation. The optimistic formula is for the contractor; the pessimistic for risk reserves; the default is for the program controls record.</p>

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
        <p>CPI &lt; 0.90 on a public capital program is the FAR-region threshold for potential corrective action reporting. A CPI of 0.88 sustained over three periods is not a "watch item", under most agency program-controls policies it is a recovery-plan trigger, and the audit record should show the decision was made (or formally deferred) by named authority on a documented date.</p>

        <h3>Monte Carlo EAC forecast, why a range, not a point</h3>
        <p>A single deterministic EAC gives false precision. A P50/P80 range is more honest and more useful: it lets program controls fund contingency to an explicit risk percentile rather than to a point estimate that pretends the future is known.</p>

        <h3>Why Beta-PERT</h3>
        <p>For construction cost modelling the Beta-PERT distribution is preferred over a normal or triangular distribution: it is continuous, naturally bounded by optimistic and pessimistic limits, and weighted toward the most-likely value. Across 5,000 iterations the simulated EAC distribution captures both central tendency and tail risk.</p>

        <h3>Monte Carlo formulas</h3>
        ${formulaBlock([
          "Beta-PERT parameters:",
          ["μ  = (a + 4m + b) / 6", "mean, most-likely weighted"],
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

        <p>The distance from P50 to P80 is the tail risk; widening that distance over reporting cycles is itself a finding, even if P50 holds steady, contingency needs are rising.</p>
      `,
    },
    {
      id: "module02",
      title: "5. Cat 1.2: CUSUM Anomaly Monitor",
      eyebrow: "Cat 1.2",
      build: () => `
        <p class="kn-lead">A single-period CPI/SPI reading is noisy. Real schedule drift accumulates slowly. Statistical Process Control separates signal from noise; CUSUM is the SPC method that catches sustained drift before any single period would trip a variance threshold.</p>

        <h3>Why tabular CUSUM, not Shewhart</h3>
        <p>A Shewhart chart flags points that breach 3σ control limits, good at detecting large single-period shifts, poor at detecting small sustained ones. Tabular CUSUM (Page, 1954) accumulates deviations from the target so a half-σ drift that persists over six periods triggers; on a project that is exactly the pattern that hides under Shewhart limits.</p>

        <h3>Two-sided tabular CUSUM</h3>
        ${formulaBlock([
          ["C⁺ᵢ = max( 0,  C⁺ᵢ₋₁ + (xᵢ − μ₀ − k) )", "upper (positive drift)"],
          ["C⁻ᵢ = max( 0,  C⁻ᵢ₋₁ − (xᵢ − μ₀ + k) )", "lower (negative drift)"],
          "",
          "Inputs:",
          ["xᵢ  = SPI at reporting period i", ""],
          ["μ₀  = 1.00", "target, on schedule"],
          ["k   = 0.5 σ", "allowance, half the series standard deviation"],
          ["H   = 5 σ", "decision interval"],
          "",
          ["Breach: C⁺ᵢ > H  or  C⁻ᵢ > H", "hand off to governance"],
        ])}

        <h3>Why H = 5σ (not 3σ)</h3>
        <p>Construction project SPI series have higher natural variability than manufacturing process measurements. A 3σ decision interval generates excessive false positives; 5σ ensures that only sustained, meaningful drift triggers governance action, at the cost of a slightly slower response. For a governance-grade signal that trade-off is correct.</p>

        ${svgCusum()}

        <h3>What a breach means</h3>
        <p>A CUSUM breach hands the question to Cat 6.1 (Conservative Dominance) and ultimately Cat 8.1 (ABM Governance Layer). The monitor never acts on its own; it produces evidence the governance layer routes. If the breach has no document narrative behind it, the conflict type is "Anomaly Without Narrative", itself a finding worth surfacing.</p>
      `,
    },
    {
      id: "module03",
      title: "6. Cat 1.3: Document Risk Extraction",
      eyebrow: "Cat 1.3",
      build: () => `
        <p class="kn-lead">EVM lags field conditions by weeks. An RFI log showing 20 open disputes in period 4 predicts a CPI collapse in period 6, but EVM will not show that collapse until it has already happened. Document risk is the leading signal.</p>

        <h3>How extraction works</h3>
        <p>Cat 1.3 applies transparent keyword and pattern rules over RFIs, submittal logs, OAC meeting minutes, and project correspondence. Each rule has a weight and an evidence excerpt; the document risk score is a weighted sum normalised to 0–1. Every score is inspectable: the matched rule, the source document, and the excerpt are carried into the ledger.</p>

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
        <p>Keyword extraction is rule-based, not semantic. A sophisticated contractor writes around keyword rules. The score is a <em>leading indicator</em>, never a verdict. PCEIF treats Cat 1.3 Red as a flag that requires Cat 6.1 corroboration before it drives an action, never as a standalone trigger.</p>
      `,
    },
    {
      id: "module04",
      title: "7. Cat 2.1: PERT Network Criticality",
      eyebrow: "Cat 2.1",
      build: () => `
        <p class="kn-lead">A deterministic critical-path estimate is fragile; PERT samples each activity's plausible duration range and reports the probabilistic finish date. The P80 duration is the conservative milestone estimate program controls should plan to.</p>

        <h3>Why a stochastic network</h3>
        <p>The Program Evaluation &amp; Review Technique (PERT) treats each activity duration as a random variable rather than a single point. Across 5,000 iterations the dominant network path emerges, and the path-criticality index reports the share of runs in which the structural path was on the critical path, high criticality means thin float concentrated on one chain.</p>

        ${formulaBlock([
          ["te = (a + 4m + b) / 6", "deterministic three-point estimate"],
          ["di ~ Triangular(a, m, b)", "per-activity sample"],
          ["P80 duration = 80th percentile of simulated finishes", ""],
          ["criticality_index = | runs where path = critical | / 5000", ""],
        ])}
        ${ragTable(["Metric", "Green", "Amber", "Red"], [
          ["P80 vs baseline", { label: "within baseline", color: RAG.green }, { label: "+0 to +20%", color: RAG.amber }, { label: "> +20%", color: RAG.red }],
        ])}

        <h3>How it differs from Cat 1.1</h3>
        <p>Cat 1.1 (Monte Carlo EAC) randomises cost performance; Cat 2.1 randomises activity durations along the schedule network. Cat 1.1 answers "what will it cost?"; Cat 2.1 answers "when will it finish?". Both contribute independent evidence to Cat 6.1 synthesis.</p>
      `,
    },
    {
      id: "module05",
      title: "8. Cat 2.2: Line of Balance Production Velocity",
      eyebrow: "Cat 2.2",
      build: () => `
        <p class="kn-lead">For repetitive linear work, paving, MEP installation, finishes, the schedule risk lives in the gap between leading and following crews, not in EVM aggregates. Line of Balance tracks crew velocity so that buffer collapse appears as a leading schedule signal.</p>

        <h3>Buffer collapse as a leading indicator</h3>
        <p>The leader crew (grading) sets the pace; the follower (paving) trails by an initial buffer. When the follower slows, typically because SPI is degrading project-wide, the buffer compresses unit by unit, and the unit at which the buffer would hit zero is the crew-collision point. EVM aggregates do not see this; LOB does.</p>

        ${formulaBlock([
          ["lag_per_unit = (1 / paving_rate) - (1 / grading_rate)", "schedule cost per linear unit"],
          ["buffer(u) = initial_buffer - u x lag_per_unit", "buffer at unit u"],
          ["min_buffer = min_u buffer(u)", "headline metric"],
        ])}
        ${ragTable(["Metric", "Green", "Amber", "Red"], [
          ["min crew buffer (days)", { label: "> 3.0", color: RAG.green }, { label: "1.5–3.0", color: RAG.amber }, { label: "≤ 1.5", color: RAG.red }],
        ])}

        <h3>Reference</h3>
        <p>Origin: U.S. Navy Bureau of Yards and Docks (1942) for shipbuilding. Adapted to repetitive construction work in the 1960s; remains the canonical scheduling method for linear infrastructure where the same activities repeat across units.</p>
      `,
    },
    {
      id: "module06",
      title: "9. Cat 2.3: CCPM Buffer Health",
      eyebrow: "Cat 2.3",
      build: () => `
        <p class="kn-lead">Critical Chain Project Management aggregates safety margin into a single project buffer rather than scattering it across activities. The fever chart plots buffer consumption against chain completion, a project burning buffer faster than it completes work is on a trajectory to delay, regardless of what current SPI shows.</p>

        <h3>The fever chart</h3>
        <p>The amber line tracks chain completion (consuming buffer 1:1 with progress is the warning floor); the red line sits a third of the remaining range above. Crossing into red means buffer is being burned faster than work is being earned, the buffer will be gone before the chain.</p>

        ${formulaBlock([
          ["amber_line = % complete", ""],
          ["red_line   = % complete + (100 - % complete) / 3", ""],
        ])}
        ${ragTable(["Zone", "Condition"], [
          [{ label: "Green", color: RAG.green }, "buffer consumed < % complete (below the amber line)"],
          [{ label: "Amber", color: RAG.amber }, "buffer consumed >= % complete"],
          [{ label: "Red", color: RAG.red }, "buffer consumed >= % complete + (100 - % complete) / 3"],
        ])}

        <h3>Reference</h3>
        <p>Goldratt, E.M. (1997). <em>Critical Chain</em>. North River Press. CCPM treats schedule contingency as a programme-level resource rather than per-activity padding, making the actual consumption rate visible.</p>
      `,
    },
    {
      id: "module07",
      title: "10. Cat 3.1: Reference Class Forecasting",
      eyebrow: "Cat 3.1",
      build: () => `
        <p class="kn-lead">Inside-view estimates, bottom-up cost roll-ups from the project's own scope, systematically underestimate cost on public infrastructure. Reference Class Forecasting replaces the inside view with the empirical distribution of overruns from comparable projects.</p>

        <h3>Outside-view debiasing</h3>
        <p>Flyvbjerg's analysis of public infrastructure shows a consistent pattern: optimism bias in inside-view estimates compounds with strategic mis-representation. The empirical reference-class distribution captures both the bias and the variance; the P80 multiplier is the conservative debiasing factor applied to BAC.</p>

        ${formulaBlock([
          ["multipliers = [ 1.00, 1.04, 1.10, 1.14, 1.15, 1.26, 1.38, 1.45, 1.52 ]", "airport-infrastructure reference class"],
          ["P50 prior = BAC x multipliers[ P50 ]", ""],
          ["P80 prior = BAC x multipliers[ P80 ]", "conservative debiased budget"],
          ["debiasing_factor = multipliers[ P80 ]", "headline metric"],
        ])}
        ${ragTable(["Metric", "Green", "Amber", "Red"], [
          ["P80 prior vs BAC", { label: "within +10%", color: RAG.green }, { label: "+10% to +25%", color: RAG.amber }, { label: "> +25%", color: RAG.red }],
        ])}

        <h3>Reference</h3>
        <p>Flyvbjerg, B. (2008). Curbing optimism bias and strategic misrepresentation in planning. <em>European Planning Studies</em>, 16(1), 3–21. The reference-class method is now embedded in the UK Treasury Green Book guidance.</p>
      `,
    },
    {
      id: "module08",
      title: "11. Cat 3.2: DSM Rework Propagation",
      eyebrow: "Cat 3.2",
      build: () => `
        <p class="kn-lead">Design changes do not stay where they start. The Design Structure Matrix captures the inter-discipline dependency network so a single architectural change can be propagated through Structural and MEP to estimate the cumulative rework burden.</p>

        <h3>The 3x3 design dependency matrix</h3>
        <p>The off-diagonal entries are the coupling strengths between Arch, Structural, and MEP. A unit architectural change vector is propagated through four passes; the cumulative rework multiplier across all three disciplines is the coordination cost of that single change.</p>

        ${formulaBlock([
          "A = [ [0.0, 0.3, 0.1],   Arch    <- Structural, MEP",
          "      [0.5, 0.0, 0.2],   Struct  <- Arch, MEP",
          "      [0.4, 0.4, 0.0] ]  MEP     <- Arch, Structural",
          "",
          ["v0 = [1, 0, 0],   v(t+1) = A · v(t)", "propagation step"],
          ["rework_multiplier = sum_i sum_t=0..4 v_i(t)", "cumulative across 4 passes"],
        ])}
        ${ragTable(["Metric", "Green", "Amber"], [
          ["rework multiplier", { label: "≤ 2.5", color: RAG.green }, { label: "> 2.5", color: RAG.amber }],
        ])}

        <h3>Reference</h3>
        <p>Steward, D.V. (1981). The Design Structure System: A Method for Managing the Design of Complex Systems. <em>IEEE Transactions on Engineering Management</em>, 28(3), 71–74. Modern DSM analysis underpins building-information-modelling clash detection and integrated-project-delivery coordination practice.</p>
      `,
    },
    {
      id: "module09",
      title: "12. Cat 6.1: Conservative Dominance (Signal Synthesis)",
      eyebrow: "Cat 6.1 · baseline synthesis",
      build: () => `
        <p class="kn-lead">A CPI of 1.02 and a CUSUM breach do <strong>not</strong> average to "slightly above baseline." The breach is the finding. PCEIF surfaces disagreement between signal classes instead of averaging it away, and names the disagreement so the reviewer knows what to investigate.</p>

        <h3>The six conflict types</h3>
        ${ragTable(
          ["Conflict Type", "Condition", "Meaning"],
          [
            ["Agreement, All Stable", "All Green", "No action required this cycle."],
            ["Mixed Early Warning", "Ambers only, no Red", "Monitor; no escalation yet."],
            ["Single Signal Watch", "One Amber", "Investigate the specific signal."],
            ["Anomaly Without Narrative", "CUSUM Red, EVM Amber/Green", "Schedule anomaly not yet explained by documents."],
            ["Leading Document Risk", "Doc Red, EVM Green", "Field conditions deteriorating before EVM shows it."],
            ["Multi-signal Red-review", "≥ 2 Red signals", "Escalation required, full signal package."],
          ]
        )}

        ${svgAgreementMap()}

        <h3>Why precedence matters</h3>
        <p>The classifier walks the table in order: it picks the <em>first</em> matching conflict, not the most common one. That preserves the leading-indicator property, a Document Red overshadowed by aggregate Greens still surfaces as "Leading Document Risk" if it would otherwise be missed.</p>

        <h3>How it differs from Cat 7.1–Cat 7.9</h3>
        <p>Cat 6.1 is the governance baseline: conservative dominance with explicit conflict typing. Cat 7.1–Cat 7.9 each provide an independent evidence-combination lens (probabilistic, set-theoretic, fuzzy, quantum). When Cat 6.1 and any of 10–18 disagree, the disagreement itself is what gets recorded, the governance layer owns the residual uncertainty rather than picking a method. Cat 8.1 (ABM Governance) consumes both the Cat 6.1 baseline and the M10–18 cross-checks to produce the actionable decision card.</p>
      `,
    },
    {
      id: "module10",
      title: "13. Cat 7.1: Dempster-Shafer Evidence Combination",
      eyebrow: "Cat 7.1 · evidence theory",
      build: () => `
        <p class="kn-lead">Dempster-Shafer Theory (DST) is a mathematical framework for reasoning under uncertainty with multiple independent sources. Each source assigns a basic probability assignment (BPA) over a frame of discernment, here {Green, Amber, Red, Unknown}. Dempster's rule combines sources and normalises out the conflict mass K.</p>

        <h3>What DST adds beyond conservative dominance</h3>
        <p>Cat 6.1 takes the worst single signal. DST weights all four evidence sources and produces explicit belief masses for every state. When a project is Green by two signals, Amber by one, Red by one, conservative dominance outputs Red; DST may output Amber if the combined belief mass for Amber is highest, and the conflict mass K quantifies exactly how much the sources disagreed. That conflict mass is itself a governance-relevant finding.</p>

        ${formulaBlock([
          "Frame of discernment: Theta = {Green, Amber, Red, Unknown}",
          "Each source i assigns mass m_i(A) for each subset A of Theta,",
          "where sum_A m_i(A) = 1.",
          "",
          "Dempster combination of two sources m1, m2:",
          ["m(A) = (1 / (1 - K)) * sum_{B∩C=A} m1(B) * m2(C)", "combined mass"],
          ["K = sum_{B∩C=empty} m1(B) * m2(C)", "conflict mass, inter-source disagreement"],
          "",
          "If K → 1 (total conflict), the combination is undefined;",
          "this implementation returns uniform mass as a safe fallback.",
          "",
          "Final state = argmax_{Green,Amber,Red} m(state)",
          "Conflict level: Low if K < 0.10, Moderate if K 0.10-0.30, High if K > 0.30",
        ])}

        ${ragTable(["Conflict Mass K", "Interpretation"], [
          [{ label: "< 0.10 (Low)", color: RAG.green }, "Sources broadly agree, DST result is reliable."],
          [{ label: "0.10–0.30 (Moderate)", color: RAG.amber }, "Some inter-signal tension, review which sources diverge."],
          [{ label: "> 0.30 (High)", color: RAG.red }, "Strong disagreement, divergence itself is a governance signal worth surfacing."],
        ])}

        <h3>Reference</h3>
        <p>Dempster, A.P. (1967). Upper and lower probabilities induced by a multivalued mapping. <em>Annals of Mathematical Statistics</em>, 38(2), 325–339. Shafer, G. (1976). <em>A Mathematical Theory of Evidence</em>. Princeton University Press.</p>
      `,
    },
    {
      id: "module11",
      title: "14. Cat 7.2: Rough Sets Classification",
      eyebrow: "Cat 7.2 · set theory",
      build: () => `
        <p class="kn-lead">Rough Set Theory classifies a project by computing lower and upper approximations of each state class. The lower approximation holds states that all available signals definitively support (over 75% agreement); the upper approximation holds states that any signal supports; the boundary region is the indeterminate zone.</p>

        <h3>What rough sets add</h3>
        <p>Unlike fuzzy logic, rough sets do not assign membership grades, they answer set-theoretic questions: Definite? Possible? Indeterminate? A non-empty boundary region is itself a finding: the evidence framework cannot yet support a single classification, so the governance layer must record the indeterminacy rather than force a verdict.</p>

        ${formulaBlock([
          "Lower approximation: states with signal agreement > 75%",
          "Upper approximation: states with any supporting signal",
          "Boundary region: upper - lower (indeterminate zone)",
          "",
          "Definite classification: lower approximation contains exactly one state",
          "Borderline: boundary region is non-empty",
          "Indeterminate: upper approximation spans multiple states",
        ])}

        ${ragTable(["Region", "Interpretation"], [
          ["Lower approximation", "Definite membership, all signals agree on this state."],
          ["Upper approximation", "Possible membership, at least one signal supports this state."],
          [{ label: "Boundary region", color: RAG.amber }, "Indeterminate, evidence is present but insufficient for certain classification."],
        ])}

        <h3>Reference</h3>
        <p>Pawlak, Z. (1982). Rough sets. <em>International Journal of Computer and Information Sciences</em>, 11(5), 341–356. Rough set theory remains a foundational framework for decision-making under incomplete information.</p>
      `,
    },
    {
      id: "module12",
      title: "15. Cat 7.3: Neutrosophic Logic",
      eyebrow: "Cat 7.3 · three-valued logic",
      build: () => `
        <p class="kn-lead">Neutrosophic Logic adds a third dimension to truth value: Indeterminacy (I), alongside Truth (T) and Falsity (F). Unlike classical and fuzzy logic, T + I + F is unconstrained, indeterminacy lives as its own dimension rather than being inferred from the residual of truth and falsity.</p>

        <h3>What neutrosophic adds</h3>
        <p>High I means the evidence is genuinely undetermined, not a soft positive or a soft negative, but an unresolvable uncertainty that no additional signal of the same type can remove. The governance recommendation can then be explicit: "the data we have cannot yet decide" is a valid output, distinct from "we have data and it says Amber."</p>

        ${formulaBlock([
          "Combination rule:",
          ["T_combined = 1 - prod_i(1 - T_i)", "disjunctive (T grows as evidence accumulates)"],
          ["I_combined = prod_i(I_i)", "conjunctive (I shrinks as certainty increases)"],
          ["F_combined = prod_i(F_i)", "conjunctive (F shrinks as evidence resolves)"],
          "",
          "Normalise: T, I, F each divided by (T + I + F)",
          "",
          "Status: Red if >= 2 sources Red; Amber if >= 2 Amber; else Green.",
          "If I_normalised > 0.30, upgrade Green to Amber (uncertainty warning).",
        ])}

        ${ragTable(["Indeterminacy (I)", "Interpretation"], [
          [{ label: "< 15% (Low)", color: RAG.green }, "Evidence is sufficiently conclusive for classification."],
          [{ label: "15–30% (Moderate)", color: RAG.amber }, "Moderate uncertainty, some sources are ambiguous."],
          [{ label: "> 30% (High)", color: RAG.red }, "Evidence architecture needs strengthening before confident classification."],
        ])}

        <h3>Reference</h3>
        <p>Smarandache, F. (1995). <em>A Unifying Field in Logics: Neutrosophic Logic</em>. American Research Press. Neutrosophic theory generalises classical, fuzzy, and intuitionistic logics by treating indeterminacy as an independent axis.</p>
      `,
    },
    {
      id: "module13",
      title: "16. Cat 7.4: Interval-valued Fuzzy Sets",
      eyebrow: "Cat 7.4 · fuzzy logic",
      build: () => `
        <p class="kn-lead">Interval-valued Fuzzy Sets represent membership as a range [lower, upper] rather than a single value, explicitly propagating input measurement uncertainty through the fuzzy classification. The width of the resulting interval shows how much realistic input noise could shift the verdict.</p>

        <h3>Measurement tolerances</h3>
        <p>For airport construction EVM the principal noise sources are Schedule-of-Values line-item accuracy (~±2% EV) and pay-application rounding (~±1% AC), compounding to ~±3 percentage points on CPI/SPI. A narrow interval means the classification is robust to that noise; a wide interval means a Green/Amber boundary crossing is within reach of normal measurement uncertainty.</p>

        ${formulaBlock([
          "CPI uncertainty range: [CPI - 0.03, CPI + 0.03]",
          "Membership functions per state (Green / Amber / Red):",
          "  Green:  mu_G(v) = 0 if v <= 0.92, 1 if v >= 0.97, linear between",
          "  Amber:  bell centred at 0.92, zero outside [0.85, 0.98]",
          "  Red:    mu_R(v) = 1 if v <= 0.85, 0 if v >= 0.92, linear between",
          "",
          "State interval: [min(mu(low), mu(high)), max(mu(low), mu(high))]",
          "Aggregation across sources: element-wise max of lower, max of upper.",
          "",
          "Status = state with highest interval midpoint.",
          "Uncertainty width = sum of (red + amber) interval spreads.",
        ])}

        ${ragTable(["Uncertainty width", "Interpretation"], [
          [{ label: "< 0.15 (Low)", color: RAG.green }, "Input precision is sufficient for reliable classification."],
          [{ label: "0.15–0.30 (Moderate)", color: RAG.amber }, "Boundary classification may shift with better input data."],
          [{ label: "> 0.30 (High)", color: RAG.red }, "Input noise could change the classification, request more precise documents."],
        ])}

        <h3>Reference</h3>
        <p>Sambuc, R. (1975). <em>Fonctions phi-floues</em>. PhD thesis, University of Marseille. Zadeh, L.A. (1975). The concept of a linguistic variable and its application to approximate reasoning. <em>Information Sciences</em>, 8(3), 199–249. Turksen, I.B. (1986). Interval valued fuzzy sets based on normal forms. <em>Fuzzy Sets and Systems</em>, 20(2), 191–210.</p>
      `,
    },
    {
      id: "module14",
      title: "17. Cat 7.5: Z-numbers",
      eyebrow: "Cat 7.5 · reliability-weighted evidence",
      build: () => `
        <p class="kn-lead">A Z-number is a pair (Restriction, Reliability). The restriction is the signal's classification; the reliability is how trustworthy the source data is. A CPI from a verified pay application is more trustworthy than one estimated from a schedule update, and the governance recommendation should reflect that, not just the headline state.</p>

        <h3>What Z-numbers add</h3>
        <p>Every other synthesis method treats all sources as equally reliable. Z-numbers make reliability a first-class input: a Red signal from a low-reliability source contributes less than a Red from a high-reliability source. This is the same epistemic structure auditors use informally; Cat 7.5 makes it explicit in the audit record.</p>

        ${formulaBlock([
          "For each signal i with state s_i and reliability r_i in [0, 1]:",
          ["weighted_Red   = sum_{i: s_i=Red}   r_i", "reliability-weighted total"],
          ["weighted_Amber = sum_{i: s_i=Amber} r_i", ""],
          ["weighted_Green = sum_{i: s_i=Green} r_i", ""],
          "",
          "Status = state with highest weighted total.",
          "",
          "Reliability defaults (this implementation):",
          "  EVM (pay app):     0.85    Monte Carlo:  0.88",
          "  CUSUM:             0.90    Doc keyword:  0.65",
        ])}

        ${ragTable(["Avg reliability", "Interpretation"], [
          [{ label: "≥ 80%", color: RAG.green }, "High-confidence aggregate, sources are well-instrumented."],
          [{ label: "60–80%", color: RAG.amber }, "Moderate, at least one source is rule-based or estimated."],
          [{ label: "< 60%", color: RAG.red }, "Aggregate is dominated by low-reliability sources; improve instrumentation before acting."],
        ])}

        <h3>Reference</h3>
        <p>Zadeh, L.A. (2011). A note on Z-numbers. <em>Information Sciences</em>, 181(14), 2923–2932. Z-numbers extend the linguistic-variable framework to model the reliability of the data behind a fuzzy assessment, distinct from the assessment itself.</p>
      `,
    },
    {
      id: "module15",
      title: "18. Cat 7.6: Probabilistic Linguistic Term Sets (PLTS)",
      eyebrow: "Cat 7.6 · probabilistic linguistics",
      build: () => `
        <p class="kn-lead">PLTS expresses each signal as a probability distribution across linguistic states {Green, Amber, Red} rather than forcing a crisp label. A CUSUM that just barely missed breach is not the same Green as a deeply stable monitor, PLTS preserves that distinction explicitly.</p>

        <h3>What PLTS adds</h3>
        <p>Conservative dominance and Z-numbers both pre-classify each signal as a single state before combining. PLTS skips that crispening step: each source contributes its native probability triple, and the aggregate is the average across all sources. The result is closer to how expert reviewers actually assess projects, with confidence degrees attached to every classification.</p>

        ${formulaBlock([
          "For each signal i, an expert-mapped probability triple:",
          ["p_i = (p_Green, p_Amber, p_Red),  sum = 1.0", "per-source linguistic distribution"],
          "",
          "Aggregate across N sources:",
          ["P(s) = (1/N) * sum_i p_i(s)   for s in {Green, Amber, Red}", "averaged probability"],
          "",
          "Status = state s with highest aggregate P(s).",
        ])}

        ${ragTable(["P(Red)", "Interpretation"], [
          [{ label: "< 25%", color: RAG.green }, "Aggregate probability of Red is low across sources."],
          [{ label: "25–50%", color: RAG.amber }, "Non-trivial Red probability; review which sources contribute."],
          [{ label: "≥ 50%", color: RAG.red }, "Majority probability mass sits on Red, escalation indicated."],
        ])}

        <h3>Reference</h3>
        <p>Pang, Q., Wang, H., &amp; Xu, Z. (2016). Probabilistic linguistic term sets in multi-attribute group decision making. <em>Information Sciences</em>, 369, 128–143. PLTS now underpins multi-attribute decision frameworks where each criterion's assessment naturally carries a confidence distribution.</p>
      `,
    },
    {
      id: "module16",
      title: "19. Cat 7.7: Plithogenic Sets",
      eyebrow: "Cat 7.7 · contradiction-degree weighting",
      build: () => `
        <p class="kn-lead">Plithogenic Sets assign each signal a contradiction degree against the dominant value. A Green signal in a project where every other signal is Red has high contradiction, it is not cancelled, but it is weighted down to reflect that it is the outlier. High average contradiction means the signals are genuinely opposed, not merely mixed.</p>

        <h3>What plithogenic adds</h3>
        <p>Most aggregation methods average opposing signals into a middle state. Plithogenic aggregation distinguishes "opposed" from "intermediate" by tracking how far each signal sits from the dominant value: a contradiction degree of 1.0 means the signal is at the opposite pole; 0.5 means it is mid-spectrum. The average contradiction across sources becomes a governance signal in its own right.</p>

        ${formulaBlock([
          "For each attribute (signal) a:",
          "  membership(a) in [0, 1]",
          "  contradiction(a, dominant) in [0, 1]   (0 = same, 1 = opposite)",
          "",
          "Aggregation weight per attribute:",
          ["w(a) = membership(a) * (1 - contradiction(a) * 0.5)", "discounts opposing signals"],
          "",
          "State scores:",
          ["score(s) = sum_{a: state(a) = s} w(a)", "per-state weighted total"],
          "",
          "Status = state s with highest score(s).",
        ])}

        ${ragTable(["Average contradiction", "Interpretation"], [
          [{ label: "< 30% (Low)", color: RAG.green }, "Signals are broadly consistent."],
          [{ label: "30–60% (Moderate)", color: RAG.amber }, "Some opposition; review which signals oppose the dominant view."],
          [{ label: "> 60% (High)", color: RAG.red }, "Signals are genuinely polarised, the disagreement is the finding."],
        ])}

        <h3>Reference</h3>
        <p>Smarandache, F. (2018). <em>Plithogeny, Plithogenic Set, Logic, Probability and Statistics</em>. Pons Editions, Brussels. Plithogenic theory generalises crisp / fuzzy / neutrosophic sets by adding the contradiction-degree dimension between attribute values.</p>
      `,
    },
    {
      id: "module17",
      title: "20. Cat 7.8: Belief Rule Base (BRB)",
      eyebrow: "Cat 7.8 · expert IF-THEN rules",
      build: () => `
        <p class="kn-lead">A Belief Rule Base encodes expert knowledge as IF-THEN rules whose consequent is a belief distribution rather than a crisp state. "If EVM is Red and CUSUM has breached, belief is 90% Red, 8% Amber, 2% Green." Multiple matching rules are combined by rule weight to produce the aggregate belief.</p>

        <h3>What BRB adds</h3>
        <p>BRB bridges the explicit governance rules of PCEIF and probabilistic expert judgement. The rule conditions are crisp (matching the PCEIF authority matrix structure), but the consequents are graded probability distributions (matching how experts actually express confidence). Each rule carries a weight that captures how strongly it should drive the aggregate when it fires.</p>

        ${formulaBlock([
          "Rule R_k: IF antecedent_k THEN belief = (b_G, b_A, b_R) with weight w_k",
          "",
          "Matched rules: M = { R_k : antecedent_k holds for this signal package }",
          "",
          "Aggregate belief, weighted average across M:",
          ["B(s) = sum_{R_k in M} b_k(s) * w_k  /  sum_{R_k in M} w_k", ""],
          "",
          "Status = state s with highest B(s).",
        ])}

        ${ragTable(["B(Red) aggregate", "Interpretation"], [
          [{ label: "< 25%", color: RAG.green }, "Matched rules collectively assign low Red belief."],
          [{ label: "25–50%", color: RAG.amber }, "Non-trivial Red belief from at least one high-weight rule."],
          [{ label: "≥ 50%", color: RAG.red }, "Aggregate belief mass on Red, escalation indicated."],
        ])}

        <h3>Reference</h3>
        <p>Yang, J.-B., Liu, J., Wang, J., Sii, H.-S., &amp; Wang, H.-W. (2006). Belief rule-base inference methodology using the evidential reasoning approach, RIMER. <em>IEEE Transactions on Systems, Man, and Cybernetics, Part A</em>, 36(2), 266–285. Extended through 2018–2023 with hierarchical and self-adaptive BRB variants.</p>
      `,
    },
    {
      id: "module18",
      title: "21. Cat 7.9: Quantum Probability",
      eyebrow: "Cat 7.9 · amplitude interference",
      build: () => `
        <p class="kn-lead">Quantum Probability models signals as wave amplitudes rather than classical probabilities. When signals align they interfere constructively, amplifying the dominant classification; when signals oppose they interfere destructively, reflecting genuine ambiguity. The phase angle measures signal coherence.</p>

        <h3>What quantum probability adds</h3>
        <p>Classical aggregation is additive: opposing signals partially cancel by simple subtraction. Quantum probability is amplitude-based: the cross term 2·α·γ·cos(θ) captures order effects and interference that classical probability cannot represent. In governance terms, destructive interference means the signals are genuinely contradictory in a way no further averaging can resolve, the residual uncertainty belongs to the governance layer.</p>

        ${formulaBlock([
          "Amplitudes from classical probabilities:",
          ["α = sqrt( avg P(Green) across sources )", "Green amplitude"],
          ["γ = sqrt( avg P(Red)   across sources )", "Red amplitude"],
          "",
          "Phase angle from signal coherence:",
          ["θ = |red_count - green_count| / N * pi", "small θ → constructive, large θ → destructive"],
          "",
          "Interference cross-term:",
          ["I = 2 * α * γ * cos(θ)", ""],
          "",
          "Quantum probabilities (clipped to [0, 1]):",
          ["P_q(Red)   = γ² + 0.3 * I", ""],
          ["P_q(Green) = α² − 0.3 * I", ""],
          ["P_q(Amber) = 1 − P_q(Red) − P_q(Green)", ""],
          "",
          "Status = state with highest P_q.",
        ])}

        ${ragTable(["Interference type", "Interpretation"], [
          [{ label: "Constructive (cos θ > 0.3)", color: RAG.green }, "Signals reinforce, high classification confidence."],
          [{ label: "Neutral", color: RAG.amber }, "Mixed reinforcement and cancellation."],
          [{ label: "Destructive (cos θ < -0.3)", color: RAG.amber }, "Signals partially cancel, residual uncertainty is genuine."],
        ])}

        <h3>Reference</h3>
        <p>Busemeyer, J.R., &amp; Bruza, P.D. (2012). <em>Quantum Models of Cognition and Decision</em>. Cambridge University Press. Quantum probability gives a principled formal framework for order effects and contextual contradictions that classical Bayesian models cannot easily express.</p>
      `,
    },
    {
      id: "module19",
      title: "22. Cat 8.1: ABM Governance Layer",
      eyebrow: "Cat 8.1 · decision output (LAST)",
      build: () => `
        <p class="kn-lead">"Agent-based" here means each authority role (PM, controls lead, program director) is modelled as an agent with explicit, executable decision rules. In <code>decision.js</code> those rules are pure functions, readable, testable, and auditable. Nothing is learned; everything is documented. Cat 8.1 is the LAST module because it consumes the Cat 6.1 baseline plus the M10–18 evidence checks and produces the recorded decision card.</p>

        <h3>Why the authority matrix exists</h3>
        <p>PCEIF operates under two layers. Layer 1 is the agency governance policy: the program owner sets the authority matrix before any project starts. Layer 2 is the PM decision architecture: it uses that matrix to route each signal package to the correct authority. The matrix is not hardcoded. A different agency can configure different thresholds and authorities. What PCEIF provides is the routing logic and the audit trail.</p>

        <h3>The authority matrix</h3>
        ${ragTable(
          ["State", "Authority", "Timeframe", "Basis"],
          [
            [{ label: "Complete", color: RAG.complete },
             "Project Manager / Controls Lead",
             "Closeout documentation",
             "Milestone achieved and signed off, transition to closeout governance"],
            [{ label: "Green", color: RAG.green },
             "Project Manager / Controls Lead",
             "Monthly reporting cycle",
             "Routine performance within delegated PM authority"],
            [{ label: "Yellow", color: RAG.yellow },
             "Project Manager",
             "Weekly check-in",
             "Minor variance, early-warning band, investigate before next cycle"],
            [{ label: "Amber", color: RAG.amber },
             "PM + Project Controls Lead",
             "Weekly review loop",
             "Significant risk requiring controls oversight but within PM authority"],
            [{ label: "Red-review", color: RAG.red },
             "Program Director / PMO Lead",
             "48 business hours",
             "Cost or schedule signal exceeds PM delegated authority threshold. FAR Part 34 and OMB Circular A-11 require named senior approver on record for programs showing sustained underperformance"],
            [{ label: "Critical", color: RAG.red },
             "Contracting Officer / Executive Board",
             "Immediate",
             "Potential contract default, major scope change, or regulatory reporting threshold breached"],
          ]
        )}

        <h3>Why Program Director for Red-review (not PM)</h3>
        <p>Three reasons:</p>
        <ol class="kn-list">
          <li><strong>Authority limit.</strong> PMs have delegated authority up to a defined threshold. A sustained CPI below 0.90 or multiple Red signals typically exceeds that threshold. The PM cannot unilaterally authorize a recovery plan without program-level approval.</li>
          <li><strong>Regulatory basis.</strong> OMB Circular A-11 (capital programming) and FAR Part 34 (major system acquisitions) require that cost overruns above defined thresholds be reported to a named senior official with documented rationale and a corrective action plan. The Program Director is that official.</li>
          <li><strong>Accountability chain.</strong> Public capital programs are publicly accountable. A governance action recorded only at the PM level is insufficient for audit purposes when the project is in distress. The Program Director's name on the record creates the accountability chain the oversight framework requires.</li>
        </ol>

        <h3>Why 48 hours</h3>
        <p>The 48-hour timeframe is derived from standard agency program controls policy. The next reporting cycle cannot close with an unresolved Red-review: the decision must be on record before the period closes. 48 business hours gives the Program Director time to review the full signal package, consult with the PM, and record a decision or deferral with rationale.</p>

        <h3>The fairness gate</h3>
        <p>For Red-review on fairness-sensitive signals (document risk, LOB crew buffer, CCPM buffer), the contractor must have a response opportunity before the Program Director records a formal action. This prevents automated model outputs from directly triggering contractual consequences without the contractor's voice. The fairness gate is a PCEIF Layer 1 policy requirement, not optional.</p>

        <h3>Layer 1 vs Layer 2</h3>
        <p><strong>Layer 1 (Agency Governance):</strong> sets the matrix. Which thresholds trigger which authority, what documentation is required, whether a fairness gate applies. Established by the program owner before any project starts. Not changed per project.</p>
        <p><strong>Layer 2 (PM Decision Architecture):</strong> uses the matrix. Takes the signal package from all 19 modules, applies the matrix, and surfaces the specific recommendation for this reporting cycle. The PM sees the recommendation, records a decision (approve, defer, or override with rationale), and the audit trail captures everything.</p>
        <p class="kn-callout">AI explains and summarizes. It does not make governance decisions. Every recommended action requires named human approval before it is recorded.</p>

        <h3>The three core functions</h3>
        ${formulaBlock([
          "deriveHealthState(signals):",
          "  Conservative dominance, the worst single signal class determines state.",
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
          "Authority matrix, Layer 1 policy:",
          "  Complete    → Project Manager / Controls Lead    , closeout documentation",
          "  Green       → Project Manager / Controls Lead    , monthly cycle",
          "  Yellow      → Project Manager                    , weekly check-in",
          "  Amber       → PM + Controls Lead                 , weekly loop",
          "  Red-review  → Program Director / PMO Lead        , 48 hours",
          "  Critical    → Contracting Officer / Executive    , immediate",
        ])}

        <h3>Why the rules are explicit, not learned</h3>
        <p>A governance system cannot rely on a black-box model. Every recommended action must be traceable to a specific rule that a reviewer can read aloud. During a dispute the PM must be able to say: "the system recommended escalation because two signal classes were Red and the conflict was classified as Multi-signal Red-review under the PCEIF authority matrix." That sentence requires explicit rules, not neural weights.</p>
        <p>This is also why <code>decision.js</code> is plain JavaScript with no compilation step, anyone reading the code can verify the agency's authority matrix is implemented exactly as policy specifies.</p>

        <h3>Why Cat 8.1 is the LAST module</h3>
        <p>The position is deliberate. The PM should read Cat 8.1 first as the recommended action, then walk backward through the evidence chain to confirm. Cat 1.1–Cat 3.2 supply the inputs; Cat 6.1 is the baseline classification; Cat 7.1–Cat 7.9 are the confidence check; Cat 8.1 is what gets recorded. Placing the decision artefact at the end of the stack reflects the audit-trail order: the recommendation is the last thing the PM commits to, not the first thing they see.</p>
      `,
    },
    {
      id: "fairness",
      title: "The fairness gate",
      eyebrow: "Procedural safeguard",
      build: () => `
        <p class="kn-lead">An automated signal must never directly drive a contractual consequence. The fairness gate is the procedural step that ensures the contractor has a documented opportunity to explain field conditions before a fairness-sensitive Red-review becomes a formal action.</p>

        <h3>When it triggers</h3>
        <p>The fairness gate engages when the project state is Red-review <em>and</em> at least one fairness-sensitive signal is Red:</p>
        <ul class="kn-list">
          <li><strong>Document Risk Red</strong>, risk language identified against the contractor's record.</li>
          <li><strong>LOB Red</strong>, projected crew collision implies a productivity allegation.</li>
          <li><strong>CCPM Red</strong>, buffer exhaustion implies the contractor's schedule discipline.</li>
        </ul>

        <h3>What it requires</h3>
        <ul class="kn-list">
          <li>A written request to the contractor stating the signal and the evidence.</li>
          <li>A reasonable response timeframe (commonly 5 business days; agency policy may set the floor).</li>
          <li>The reviewer's acknowledgement that the response was solicited and either received or formally non-responded.</li>
        </ul>

        <h3>What it produces</h3>
        <p>The contractor's response, or the documented non-response, is recorded alongside the decision card in the audit trail. The decision cannot be recorded until the gate is acknowledged; this is a hard procedural block, not a soft reminder.</p>

        <p class="kn-callout">The fairness gate is a workflow gate, not a statistic. It is never expressed as a score or a percentage; it is either acknowledged or it is not.</p>
      `,
    },
    {
      id: "decision",
      title: "The decision card and audit trail",
      eyebrow: "Accountable record",
      build: () => `
        <p class="kn-lead">The decision card is the single artefact that captures, for each governed decision, who decided, what they decided, on what evidence, under what authority, and on what date. It is the record that survives the project, the basis for independent audit, dispute resolution, and program-level reporting.</p>

        <h3>Decision card fields</h3>
        ${ragTable(
          ["Field", "Why it matters"],
          [
            ["Derived state", "The PCEIF rule output, Green / Amber / Red-review / Critical, that triggered this card."],
            ["Conflict type", "The named disagreement Cat 6.1 surfaced; tells the reviewer what to investigate."],
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
        <p>Program-level reporting and independent audit do not work on PDFs. They work on structured records that can be queried, aggregated, and reconciled. A decision card that exports cleanly is one that can be audited at scale, and one that protects the reviewer who recorded it.</p>
      `,
    },
  ];

/* ============================================================
   Module Reference, per-module documentation for all 103 project-
   level modules (Cat 1-10) plus the 5 Portfolio Health modules.
   Data is read directly from assets/js/simulations.js (formulas,
   thresholds, abstention conditions) and assets/js/categories.js
   (module registry). Rendered as collapsed <details>-equivalent
   panels via the existing window.collapsibleSection() primitive,
   reused verbatim from app.js rather than inventing a new pattern.
   ============================================================ */

  function modBands(rows) {
    return `<table class="kn-rag"><thead><tr><th>Band</th><th>Condition</th></tr></thead><tbody>` +
      rows.map((r) => `<tr><td class="kn-rag-cell" style="--kn-th:${RAG[r[0]] || ""}">${esc(r[1])}</td><td>${esc(r[2])}</td></tr>`).join("") +
      `</tbody></table>`;
  }
  // Governance role, rendered from the TDS §11 template parameterised by the
  // module's name, method class, and input gate. Per-module override via m.gov.
  // This is the concise "one contribution to an evidence package, not an
  // autonomous decision" framing required by PCEIF, not the full boilerplate.
  function modGov(m) {
    if (m.gov) return m.gov;
    return `Within PCEIF this module contributes one signal to an evidence package; it is evidence, not an instruction, and it never authorises action on its own. Its output must trace to the source record, data date, method (<code>${esc(m.mc)}</code>), threshold or trigger reason, and code version, and it abstains rather than fabricating a status when a required input is absent. Any conflict with the other signals in its category stays visible and routes to human review, where a named authority may accept, override, defer, or escalate the recommendation with a recorded rationale.`;
  }
  // Human-judgment note: the anchoring/over- or under-reaction risk this class
  // of signal invites, and the discipline that counters it. Override via m.hj.
  function modHj(m) {
    if (m.hj) return m.hj;
    return "Read as evidence, not verdict: corroborate against the other signals in its category before acting, and record a rationale if you set it aside. No silent override, the reasoning enters the audit trail.";
  }
  function modDoc(m) {
    const html = `
      <p><strong>Purpose.</strong> ${m.purpose}</p>
      <p><strong>Computation.</strong> ${m.formula}</p>
      ${m.bands ? modBands(m.bands) : ""}
      ${m.abstain ? `<p><strong>Abstains (Insufficient data) when:</strong> ${m.abstain}</p>` : ""}
      <p><strong>Data sources.</strong> ${m.sources}</p>
      <p><strong>Interpretation for the PM.</strong> ${m.interp}</p>
      <p><strong>Methodological grounding.</strong> ${m.ground}</p>
      <p><strong>Governance role.</strong> ${modGov(m)}</p>
      <p><strong>Human-judgment note.</strong> ${modHj(m)}</p>
    `;
    return window.collapsibleSection("modref-" + m.mc, `<strong>${esc(m.n)}</strong> ${esc(m.name)}`, html, false);
  }
  function modSectionBody(lead, mods) {
    return `<p class="kn-lead">${lead}</p>` + mods.map(modDoc).join("");
  }

  /* ---------- Per-category governance framing (Praxis Ch. 5 pattern) ----------
     Each category is introduced with the Praxis Ch.5 structure: Why it matters,
     Governance role, Human-judgment risks. Rendered as plain <p> (not <h3>) so
     the shared wrapArticleSections() splitter leaves the module register intact.
     The module register itself is the collapsible per-module list below. */
  const CAT_PRAXIS = {
    cat1: {
      why: "Category 1 addresses baseline cost and schedule performance, the CPI/SPI core of earned value. It matters because public project-control action must come early enough to prevent avoidable deterioration, yet not so early that it produces unsupported or unfair escalation. It gives the PM and controls team a structured family of evidence that would otherwise stay fragmented across spreadsheets, schedules, logs, and narratives.",
      risks: "PMs may anchor on familiar CPI/SPI values, assume last period's Green still controls this review, or over-react to a single forecast without checking its assumptions. The framework counters this with status rollup, dominant-signal display, evidence sufficiency, mandatory rationale, no silent overrides, and audit-aware decision records."
    },
    cat2: {
      why: "Category 2 addresses delivery timing, milestone exposure, float, resource feasibility, and near-term schedule health, the time-based leading indicators that move before SPI does. It surfaces schedule risk early enough to act while there is still room to recover.",
      risks: "PMs may normalise incremental drift, accept aggressive recovery plans without feasibility evidence, or under-react to float consumption. The framework counters this with status rollup, dominant-signal display, evidence sufficiency, mandatory rationale, and audit-aware records."
    },
    cat3: {
      why: "Category 3 addresses future budget exposure: productivity, contingency, rework, material cost, and escalation pressure, correcting for the optimism bias built into bottom-up contractor estimates.",
      risks: "PMs may treat remaining contingency as comfort even when the burn rate is unsustainable, or dispute a model's assumptions without documenting why. The framework counters this with evidence sufficiency, mandatory rationale, and audit-aware records."
    },
    cat4: {
      why: "Category 4 addresses evidence embedded in RFIs, submittals, NCRs, procurement notes, weather records, change logs, specifications, and field narratives, the qualitative early warning that leads EVM by weeks.",
      risks: "PMs may over-read one strong phrase, ignore repeated weak warnings, or treat a document-risk flag as fault rather than review evidence. The framework counters this by requiring corroboration, mandatory rationale, and the fairness gate before any contractor-affecting action."
    },
    cat5: {
      why: "Category 5 addresses interdependence, feedback loops, bottlenecks, rework propagation, supply coordination, and scenario behaviour, how project components amplify one another rather than fail in isolation.",
      risks: "PMs may treat connected problems as isolated issues, underestimate rework loops, or miss queue effects because they look purely operational. The framework counters this with status rollup, evidence sufficiency, and audit-aware records."
    },
    cat6: {
      why: "Category 6 combines heterogeneous module outputs into a transparent project-health interpretation. Its baseline rule, conservative dominance, keeps a severe credible signal from being averaged away by a crowd of green ones.",
      risks: "PMs may cherry-pick the most favourable signal, ignore conflict, or average away a serious Red. The framework counters this by making the dominant signal and the conflict explicit, and requiring rationale to depart from them."
    },
    cat7: {
      why: "Category 7 addresses uncertainty, incompleteness, vagueness, conflicting evidence, and multi-criteria ranking. Twenty independent uncertainty-reasoning frameworks cross-check the Category 6 baseline and quantify how much confidence the classification actually carries.",
      risks: "PMs may treat vague evidence as certain, treat uncertain evidence as useless, or confuse weak evidence with conflicting evidence. The framework counters this by reporting agreement and conflict, not just a colour."
    },
    cat8: {
      why: "Category 8 addresses public-owner authority, procurement constraints, audit obligations, and procedural fairness. It is always the last step: the named authority, the required action, the compliance check, and the audit trail.",
      risks: "PMs may act outside authority, bypass approval, treat an internal warning as formal direction, or fail to record rationale. The framework counters this with the authority matrix, the human-approval gate, the fairness gate, and mandatory rationale."
    },
    cat9: {
      why: "Category 9 addresses record completeness, freshness, provenance, and suitability for signal generation. Every analytical output is only as good as its inputs; this category quantifies that and refuses to hide it.",
      risks: "PMs may trust a complete-looking dashboard built on missing data, or treat extracted facts as verified facts. The framework counters this by surfacing missing, stale, and low-reliability inputs before the fused status is trusted."
    },
    cat10: {
      why: "Category 10 addresses candidate management responses, action ranking, recovery options, and proportional response selection. Where Category 5 explains system behaviour, Category 10 takes the current state as given and asks which action is optimal under constraints.",
      risks: "PMs may choose the easiest action, escalate too quickly, or delay because the options are unclear. The framework counters this by ranking proportional responses and tying each to its constraint and authority."
    },
    ph: {
      why: "Portfolio Health matters because public owners manage programs, not only isolated projects. A project can look normal in isolation yet be an outlier against its peers. It supports executive review and program learning.",
      risks: "It provides program-level context only: it does not automatically trigger project-level formal action without project-level evidence review, and its outputs are noisier for small portfolios (fewer than roughly three to five active projects)."
    }
  };
  const CAT_PRAXIS_GOV = "PCEIF treats this category's output as evidence, not instruction. The governance role is to convert each module result into a reviewable signal package carrying source record, data date, method, threshold or trigger reason, confidence or uncertainty, input completeness, action implication, and reviewer role. If required inputs are missing, the module abstains rather than fabricating a status.";
  function praxisIntro(key) {
    const p = CAT_PRAXIS[key];
    if (!p) return "";
    return `<p><strong>Why it matters.</strong> ${p.why}</p>` +
           `<p><strong>Governance role.</strong> ${CAT_PRAXIS_GOV}</p>` +
           `<p><strong>Human-judgment risks.</strong> ${p.risks}</p>`;
  }
  function catModSection(key, lead, mods) {
    return praxisIntro(key) + `<p class="kn-lead">${lead}</p>` + mods.map(modDoc).join("");
  }

  /* ---------- Cat 1, Quantitative EVM (1.1-1.12) ---------- */
  const CAT1_MODULES = [
    { n: "1.1", name: "Monte Carlo EAC Forecast", mc: "Monte_Carlo",
      purpose: "Replaces a single-point EAC with a probabilistic range so contingency and escalation decisions are made against an explicit confidence level rather than false precision.",
      formula: "5,000-iteration simulation: CPI is sampled per-iteration from a Beta-PERT(a, m, b) distribution derived from the project's current CPI/SPI; EAC_i = BAC / CPI_i. P50 and P80 are read from the sorted simulated array; P(delay) = share of iterations where EAC_i &gt; BAC × 1.10.",
      bands: [["green","Green","P80 EAC within +5% of BAC"], ["amber","Amber","P80 EAC +5% to +10% of BAC"], ["red","Red","P80 EAC &gt; +10% of BAC"]],
      sources: "Pay Application (G702), Schedule of Values (G703), Cost Report, supplies BAC/EV/AC/CPI/SPI that seed the distribution.",
      interp: "Green means the conservative planning figure is within tolerance of budget; Red means even the 80th-percentile outcome breaches the +10% overrun line, a funding conversation, not a watch item.",
      ground: "Monte Carlo simulation with a Beta-PERT input distribution is standard practice in quantitative cost-risk analysis for capital programs (Project Management Institute, 2019); Beta-PERT is preferred over triangular or normal because it is bounded and weighted toward the most-likely estimate." },
    { n: "1.2", name: "CUSUM Anomaly Monitor", mc: "CUSUM",
      purpose: "Detects sustained schedule drift that accumulates slowly across periods, before any single-period SPI reading would trip a simple variance threshold.",
      formula: "Two-sided tabular CUSUM over the SPI series: C⁺ᵢ = max(0, C⁺ᵢ₋₁ + (xᵢ − μ₀ − k)); C⁻ᵢ = max(0, C⁻ᵢ₋₁ − (xᵢ − μ₀ + k)); μ₀ = 1.00 (on schedule), k = 0.5σ, decision interval H = 5σ. A breach is C⁺ᵢ &gt; H or C⁻ᵢ &gt; H.",
      bands: [["green","Green","drift statistic below the watch level"], ["amber","Amber","drift approaching the control limit"], ["red","Red","C⁺ or C⁻ breaches H (5σ)"]],
      sources: "Schedule Update / Look-ahead, Monthly Progress Report, supplies the SPI time series the recursion runs over.",
      interp: "A breach hands the finding to Cat 6.1/Cat 8.1 governance; on its own it is evidence of a systemic pattern, not noise, and if no document explains it the conflict type is 'Anomaly Without Narrative'.",
      ground: "Tabular CUSUM (Page, 1954) is a sequential change-detection method from statistical process control, chosen over a Shewhart 3σ chart because it is sensitive to small sustained shifts rather than only large single-period ones; construction SPI series carry higher natural variance than manufacturing measurements, so H is widened to 5σ to bound false positives." },
    { n: "1.3", name: "Document Risk Extraction", mc: "Doc_Risk",
      purpose: "Surfaces qualitative risk language in project records as a leading indicator, since EVM lags field conditions by weeks.",
      formula: "Weighted sum of matched keyword/pattern rules across RFIs, submittals, OAC minutes, and correspondence, normalised to a 0-1 score. Each match carries a weight and an evidence excerpt; the ledger stores the matched rule and source document.",
      bands: [["green","Green","score &lt; 0.30, routine language"], ["amber","Amber","0.30-0.70, possible cost/schedule/scope impact language"], ["red","Red","score ≥ 0.70, high-impact language converging across document types"]],
      sources: "RFI / RFI Log, Submittal / Submittal Register, OAC Meeting Minutes, Correspondence / Notice, Risk Register, Inspection Report / NCR.",
      interp: "Red is a flag requiring Cat 6.1 corroboration, never a standalone trigger, keyword extraction is rule-based, not semantic, and a sophisticated contractor can write around it.",
      ground: "Rule-based text scoring for early warning is consistent with document-risk literature in project controls; it trades recall for full auditability, every matched rule and excerpt is inspectable, unlike a black-box NLP classifier." },
    { n: "1.4", name: "Bayesian EAC", mc: "Bayesian_EAC",
      purpose: "Blends a prior expectation (finish on budget) with the likelihood implied by current CPI, producing a posterior EAC that is more conservative than a naive CPI-only projection when current performance is thin on data.",
      formula: "priorMean = BAC, priorVariance = (BAC × 0.15)²; likelihoodMean = BAC/CPI, likelihoodVariance = (BAC × (1−CPI)/CPI)²; posteriorMean = (priorMean/priorVariance + likelihoodMean/likelihoodVariance) / (1/priorVariance + 1/likelihoodVariance); deltaPct = (posteriorMean − BAC)/BAC × 100.",
      bands: [["green","Green","delta ≤ 5%"], ["yellow","Yellow","5% &lt; delta ≤ 10%"], ["amber","Amber","10% &lt; delta ≤ 20%"], ["red","Red","delta &gt; 20%"]],
      abstain: "any of bac, ev, ac, cpi is null/undefined.",
      sources: "Pay Application, Schedule of Values, Cost Report, the same BAC/EV/AC/CPI inputs as Cat 1.1.",
      interp: "A posterior far from BAC means the current-period evidence is overwhelming the prior; the PM should treat the posterior, not the raw BAC/CPI figure, as the credible forecast.",
      ground: "Bayesian updating (prior + evidence → posterior) is the standard mechanism for revising an estimate as new reporting-period evidence arrives, letting a forecast move with the data instead of staying anchored to the original budget." },
    { n: "1.5", name: "Kalman Filter SPI Smoother", mc: "Kalman_Filter",
      purpose: "Smooths a noisy SPI history into a stable trend estimate, filtering period-to-period measurement noise out of the schedule signal.",
      formula: "Scalar Kalman recursion over spiHistory with process noise Q = 0.01 and measurement noise R = 0.1: P = P + Q; K = P/(P+R); x = x + K(xᵢ − x); P = (1−K)P. trend = (last − third-from-last)/2 when history.length ≥ 3.",
      bands: [["green","Green","smoothed SPI ≥ 0.95"], ["yellow","Yellow","0.92-0.94"], ["amber","Amber","0.88-0.91"], ["red","Red","&lt; 0.88"]],
      abstain: "spiHistory (or a single spi reading) has fewer than 2 periods.",
      sources: "Schedule Update / Look-ahead, Monthly Progress Report, the SPI series across reporting periods.",
      interp: "The smoothed value and trend separate a real schedule shift from a single noisy period; a negative trend with an already-low smoothed SPI is a compounding-risk signal, not a one-off dip.",
      ground: "The Kalman filter (Kalman, 1960) is the standard recursive estimator for extracting a latent state (true schedule performance) from a noisy observed series, balancing prior estimate against new measurement via the Kalman gain K." },
    { n: "1.6", name: "ARIMA CPI Forecast", mc: "ARIMA_Forecast",
      purpose: "Forecasts next-period CPI from the autocorrelation structure of the recent CPI series, rather than assuming performance is static.",
      formula: "First-differences the cpiHistory series; phi = lag-1 autocorrelation of the differences, clamped to [-0.9, 0.9]; forecastDiff = phi × lastDiff; forecastCPI = lastCPI + forecastDiff.",
      bands: [["green","Green","forecast CPI ≥ 0.95"], ["yellow","Yellow","0.92-0.94"], ["amber","Amber","0.88-0.91"], ["red","Red","&lt; 0.88"]],
      abstain: "cpiHistory (or a single cpi reading) has fewer than 3 periods.",
      sources: "Pay Application, Cost Report, the CPI series across reporting periods.",
      interp: "'Recovering' vs 'declining' in the evidence string tells the PM whether the autocorrelation structure of recent periods points toward or away from budget; treat as a trend confirmation for Cat 1.1/1.4, not an independent verdict.",
      ground: "Box-Jenkins ARIMA methodology (Box &amp; Jenkins, 1970) models a series from its own autocorrelation structure; this implementation is a simplified AR(1)-on-differences approximation, a lightweight proxy for the full Box-Jenkins identification/estimation/diagnostic cycle." },
    { n: "1.7", name: "Earned Schedule", mc: "Earned_Schedule",
      purpose: "Converts the cost-based SPI (which converges to 1.0 near closeout and becomes uninformative) into a time-based schedule performance index that stays meaningful through the whole project.",
      formula: "SPI(t) = actualPctComplete / plannedPctComplete. delayDays = round(baselineDurationDays × (1 − SPI(t))) when baselineStart/baselineEnd are present.",
      bands: [["green","Green","SPI(t) ≥ 0.95"], ["yellow","Yellow","0.92-0.94"], ["amber","Amber","0.88-0.91"], ["red","Red","&lt; 0.88"]],
      abstain: "ev, pv, bac, actualPctComplete or plannedPctComplete missing, or plannedPctComplete is 0.",
      sources: "Schedule Update / Look-ahead, Time-phased Schedule / Baseline, Pay Application.",
      interp: "The implied delay in days is more actionable to a PM than a dimensionless SPI, especially late in the project when cost-based SPI has converged to ~1.0 regardless of actual schedule health.",
      ground: "Earned Schedule (Lipke, 2003) extends classic EVM by re-expressing schedule performance in time units rather than cost units, correcting the well-documented failure of SPI to signal schedule problems near project completion." },
    { n: "1.8", name: "TCPI", mc: "TCPI",
      purpose: "Answers 'what cost-efficiency must the remaining work achieve to finish on budget', the forward-looking complement to CPI's backward-looking read.",
      formula: "TCPI = (BAC − EV) / (BAC − AC). If remaining budget (BAC − AC) ≤ 0, the module reports Red directly ('Budget exhausted: no remaining funds') without computing a ratio.",
      bands: [["green","Green","TCPI ≤ 1.05, achievable"], ["yellow","Yellow","1.05-1.10, challenging"], ["amber","Amber","1.10-1.20, very difficult"], ["red","Red","&gt; 1.20, unrealistic, or budget exhausted"]],
      abstain: "bac, ev or ac missing.",
      sources: "Pay Application, Schedule of Values, Cost Report.",
      interp: "A TCPI well above the project's demonstrated CPI-to-date is a credibility check: if the project has never sustained that efficiency level, budget completion is unrealistic without a scope, schedule, or funding change.",
      ground: "TCPI is a standard PMI EVM-standard index (Project Management Institute, 2019) used specifically to test the achievability of the current EAC/BAC assumption against required future performance." },
    { n: "1.9", name: "Variance at Completion", mc: "VAC",
      purpose: "States the projected dollar (and percentage) gap between the approved budget and the forecast final cost, in a form finance can put directly into a funding request.",
      formula: "EAC = BAC / CPI; VAC = BAC − EAC; VAC% = (VAC / BAC) × 100.",
      bands: [["green","Green","VAC% ≥ −5%"], ["yellow","Yellow","−10% to −5%"], ["amber","Amber","−20% to −10%"], ["red","Red","&lt; −20%"]],
      abstain: "bac or cpi missing.",
      sources: "Pay Application, Schedule of Values, Cost Report.",
      interp: "A negative VAC means projected overrun; its magnitude in dollars, not just percent, is what a program controls office takes into a contingency-draw conversation.",
      ground: "Variance at Completion is a standard PMI EVM output (Project Management Institute, 2019), the completion-date analogue of the point-in-time cost variance (CV)." },
    { n: "1.10", name: "Budget Execution Rate", mc: "Budget_Execution_Rate",
      purpose: "Checks whether spend is tracking ahead of, at, or behind the pace implied by percent complete, a different lens from CPI because it compares AC to expected spend, not to EV.",
      formula: "expectedSpend = BAC × (actualPctComplete / 100); executionRate = AC / expectedSpend.",
      bands: [["green","Green","≤ 1.05"], ["yellow","Yellow","1.05-1.10"], ["amber","Amber","1.10-1.20"], ["red","Red","&gt; 1.20"]],
      abstain: "ac, bac or actualPctComplete missing, or expectedSpend is 0.",
      sources: "Pay Application, Cost Report.",
      interp: "A rate above 1.0 means the project is spending faster than its stated percent complete would imply, either front-loaded billing or unreported progress lag, both worth reconciling before certifying the next pay app.",
      ground: "Spend-pacing checks against the S-curve baseline are a standard cost-control practice; comparing AC against percent-complete-implied spend (rather than EV) isolates billing-pace anomalies independent of earned-value definitions." },
    { n: "1.11", name: "Regression to Mean CPI", mc: "Regression_To_Mean",
      purpose: "Tempers a single extreme CPI reading by partially reverting it toward the project's own historical average, guarding against over-reacting to one noisy period.",
      formula: "mean = average(cpiHistory); deviation = current − mean; regressedCPI = mean + deviation × 0.5 (50% reversion toward the mean).",
      bands: [["green","Green","regressed CPI ≥ 0.95"], ["yellow","Yellow","0.92-0.94"], ["amber","Amber","0.88-0.91"], ["red","Red","&lt; 0.88"]],
      abstain: "cpiHistory (or a single cpi reading) has fewer than 2 periods.",
      sources: "Pay Application, Cost Report, CPI history.",
      interp: "When the regressed CPI and the raw current CPI disagree sharply, the raw reading may be an outlier period (e.g., a one-time billing timing effect) rather than a real shift in performance, worth a document check before escalating on the raw number alone.",
      ground: "Regression to the mean is a well-established statistical phenomenon (Galton, 1886) applied here as a simple 50%-reversion smoother, a deliberately conservative counterweight to single-period Monte Carlo/ARIMA readings that could otherwise be dominated by one noisy observation." },
    { n: "1.12", name: "ICE Ratio", mc: "ICE_Ratio",
      purpose: "Cross-checks the CPI-based EAC against an independent parametric EAC (AC-to-date plus remaining work at budget rate); large divergence between the two means the forecasting method choice itself matters.",
      formula: "eacCPI = BAC/CPI; eacParametric = AC + (BAC − EV); iceRatio = eacCPI / eacParametric.",
      bands: [["green","Green","|ratio−1| ≤ 0.05"], ["yellow","Yellow","0.05-0.10"], ["amber","Amber","0.10-0.20"], ["red","Red","&gt; 0.20"]],
      abstain: "bac, cpi, ev or ac missing, or eacParametric is 0.",
      sources: "Pay Application, Schedule of Values, Cost Report.",
      interp: "Two independent EAC formulas that agree (ratio near 1.0) increase confidence in either; wide divergence means the choice of EAC formula materially changes the governance conversation, and both should be presented, not just one.",
      ground: "Independent-Cost-Estimate (ICE) cross-checking, comparing multiple EAC formulas, is a standard defense against a single forecasting assumption driving a funding decision, echoing the PMI EVM standard's guidance to compare multiple EAC formulas (Project Management Institute, 2019)." }
  ];

  /* ---------- Cat 2, Schedule Simulation (2.1-2.11) ---------- */
  const CAT2_MODULES = [
    { n: "2.1", name: "PERT Network Criticality", mc: "PERT_Network_Criticality",
      purpose: "Simulates a small representative network of dependent activities to produce a probabilistic finish date instead of a single deterministic estimate.",
      formula: "3-activity network (A then max(B,C)); each duration sampled from a Triangular(a,m,b) distribution across 2,000 iterations, with the pessimistic bounds of B and C widened by a factor of 1 + max(0, 1 − SPI) × 0.8 (a degrading SPI fattens the tail). ratio = P80 total duration ÷ deterministic baseline duration.",
      bands: [["green","Green","ratio ≤ 1.15 (within baseline)"], ["amber","Amber","1.15 &lt; ratio ≤ 1.30"], ["red","Red","ratio &gt; 1.30"]],
      sources: "Schedule Update / Look-ahead, Time-phased Schedule / Baseline, supplies the SPI that widens the pessimistic bound.",
      interp: "Because a degrading SPI directly fattens the simulated tail, this module amplifies existing schedule concerns into a probabilistic finish-date warning before the project's own critical path tool would flag it.",
      ground: "PERT (Malcolm, Roseboom, Clark &amp; Fazar, 1959) treats activity duration as a random variable rather than a point estimate; sampling from a triangular distribution across many iterations is the standard simplification of full network simulation." },
    { n: "2.2", name: "Line of Balance", mc: "Line_of_Balance_Velocity",
      purpose: "Tracks the schedule buffer between a leading and a following crew on repetitive linear work, so buffer collapse is visible before a crew-collision shows up in aggregate EVM.",
      formula: "gradingRate = 2.0 units/day (leader); pavingRate = 1.8 × clamp(SPI, 0.3, 1.2) units/day (follower); lagPerUnit = max(0, 1/pavingRate − 1/gradingRate); over 20 units, buffer(u) = 5.0 days − u × lagPerUnit; minBuffer is the headline metric.",
      bands: [["green","Green","min buffer &gt; 3.0 days"], ["amber","Amber","1.5-3.0 days"], ["red","Red","≤ 1.5 days"]],
      sources: "Schedule Update / Look-ahead, supplies the SPI that sets the follower crew's simulated velocity.",
      interp: "A shrinking buffer, even while EVM aggregates still look fine, means the two crews are converging toward a physical collision on site and the sequencing needs attention now, not after CPI/SPI move.",
      ground: "Line of Balance originates in repetitive-unit production scheduling (U.S. Navy Bureau of Yards and Docks, 1942; later formalised for construction), tracking velocity and buffer between sequential trades rather than a single critical path." },
    { n: "2.3", name: "CCPM Buffer Health", mc: "CCPM_Buffer_Health",
      purpose: "Aggregates schedule safety margin into one project buffer and tracks its consumption rate against chain completion, so a buffer being burned faster than work is being earned is visible on a fever chart.",
      formula: "pctBufferConsumed = clamp((1 − SPI) × 100 × 1.5, 0, 100); amberLine = % chain complete; redLine = % chain complete + (100 − % chain complete) / 3. Status compares consumed against these two dynamic (completion-dependent) lines.",
      bands: [["green","Green","consumed below the amber line"], ["amber","Amber","consumed ≥ amber line"], ["red","Red","consumed ≥ red line"]],
      sources: "Schedule Update / Look-ahead, SPI and percent complete.",
      interp: "Crossing into the red zone means the buffer will be exhausted before the chain finishes; this is a rate-of-burn signal, distinct from CPI/SPI's point-in-time reading.",
      ground: "Critical Chain Project Management (Goldratt, 1997) consolidates individual-activity padding into a single chain-level buffer and manages that buffer's consumption rate as the primary schedule-health signal, rather than tracking dozens of individual float values." },
    { n: "2.4", name: "Schedule Compression Index", mc: "Schedule_Compression",
      purpose: "Measures how much the remaining schedule must compress, i.e. how much faster the remaining work must proceed relative to the current pace, to still hit the baseline finish date.",
      formula: "totalDays = baselineEnd − baselineStart; remainingDays = totalDays × (100 − actualPctComplete)/100; availableDays = remainingDays × SPI; compressionRatio = remainingDays / max(availableDays, 1).",
      bands: [["green","Green","≤ 1.05"], ["yellow","Yellow","1.05-1.15"], ["amber","Amber","1.15-1.30"], ["red","Red","&gt; 1.30"]],
      abstain: "baselineEnd, baselineStart or actualPctComplete missing, or baseline duration ≤ 0.",
      sources: "Time-phased Schedule / Baseline, Schedule Update / Look-ahead.",
      interp: "A ratio above 1.0 quantifies exactly how much faster the remaining work must proceed at current SPI to hit the baseline finish; ratios above 1.3 mean recovery through acceleration alone is unrealistic and a re-baseline conversation is due.",
      ground: "Schedule compression analysis follows standard CPM crashing logic: the ratio of required pace to demonstrated pace is the same test a scheduler runs before recommending crashing, fast-tracking, or a formal baseline change." },
    { n: "2.5", name: "Float Consumption Rate", mc: "Float_Consumption",
      purpose: "Checks whether total float is being consumed faster than the project is progressing, an early float-erosion signal independent of the critical path's current location.",
      formula: "consumptionRate = consumedFloat / totalFloat; expectedConsumption = actualPctComplete/100 (default 50%); floatStress = consumptionRate / max(expectedConsumption, 0.01).",
      bands: [["green","Green","floatStress ≤ 1.0"], ["yellow","Yellow","1.0-1.3"], ["amber","Amber","1.3-1.6"], ["red","Red","&gt; 1.6"]],
      abstain: "totalFloat or consumedFloat missing, or totalFloat ≤ 0.",
      sources: "Schedule Update / Look-ahead, Time-phased Schedule / Baseline.",
      interp: "Float stress above 1.0 means float is being consumed faster than physical progress is being made; sustained stress above 1.6 means the schedule's safety margin will be gone well before the work is.",
      ground: "Float/slack consumption tracking is a core CPM discipline; comparing the consumption rate to the progress rate (rather than reading float in isolation) is the standard technique for catching erosion before the critical path itself shifts." },
    { n: "2.6", name: "S-Curve Deviation", mc: "SCurve_Deviation",
      purpose: "Combines the percent-complete gap and the EV/PV value gap into one composite deviation reading of how far the project sits from its planned S-curve.",
      formula: "pctDeviation = actualPctComplete − plannedPctComplete; valueDeviation = ((EV − PV)/PV) × 100; combinedDeviation = (pctDeviation + valueDeviation) / 2.",
      bands: [["green","Green","≥ −2"], ["yellow","Yellow","−5 to −2"], ["amber","Amber","−10 to −5"], ["red","Red","&lt; −10"]],
      abstain: "actualPctComplete, plannedPctComplete, ev or pv missing, or pv is 0.",
      sources: "Schedule Update / Look-ahead, Pay Application, Schedule of Values.",
      interp: "This blends a physical-progress read with a cost-based read into a single deviation number; when the two gaps disagree sharply the combined figure understates either problem, so the PM should also check the two components separately.",
      ground: "S-curve deviation analysis is the classic visual/quantitative EVM technique of comparing planned, earned, and actual cumulative curves; averaging the percent-based and value-based deviations is a pragmatic single-number summary of that comparison." },
    { n: "2.7", name: "Milestone Trend Analysis", mc: "Milestone_Trend",
      purpose: "Compares forecast dates for the same named milestones across two consecutive schedule updates to detect creeping slip before it accumulates into a missed date.",
      formula: "For each milestone matched by name between the latest and previous snapshot: slip = (latest forecast date − previous forecast date) in days. meanSlip = average slip across matched milestones; worstSlip = the single largest slip.",
      bands: [["green","Green","mean slip ≤ 0"], ["yellow","Yellow","0-7 days"], ["amber","Amber","7-14 days, or any single milestone slipping &gt; 21 days"], ["red","Red","mean slip &gt; 14 days"]],
      abstain: "fewer than 2 milestone-history snapshots are available, or no milestone names match across the two snapshots.",
      sources: "Schedule Update / Look-ahead, requires at least two dated schedule snapshots.",
      interp: "A single badly-slipping milestone is force-escalated to at least Amber even if the average across all milestones looks fine, so one critical date cannot hide inside an otherwise healthy mean.",
      ground: "Milestone trend charts (tracking successive forecast dates for the same milestone over time) are a standard program-controls technique for detecting slow slip that a single-period schedule variance would miss." },
    { n: "2.8", name: "Look-Ahead Schedule Health", mc: "Lookahead_Health",
      purpose: "Measures what share of near-term planned activities are constrained (blocked by a predecessor, permit, or resource) in the 6-week look-ahead, a leading indicator of near-term schedule disruption.",
      formula: "constraintRate = activitiesConstrained / activitiesPlanned.",
      bands: [["green","Green","≤ 10%"], ["yellow","Yellow","10-25%"], ["amber","Amber","25-40%"], ["red","Red","&gt; 40%"]],
      abstain: "activitiesPlanned or activitiesConstrained missing.",
      sources: "Look-Ahead Schedule (6-week).",
      interp: "A high constraint rate flags near-term activities that cannot start as planned; because this is the 6-week window, it gives the PM roughly a month and a half of lead time to clear constraints before they hit the critical path.",
      ground: "Six-week look-ahead constraint tracking is a core Last Planner System practice (Ballard, 2000) for surfacing near-term make-ready problems before they consume schedule float." },
    { n: "2.9", name: "Resource Loading Index", mc: "Resource_Loading",
      purpose: "Checks whether actual labor hours are tracking within a reasonable band of planned hours, flagging both under- and over-staffing relative to plan.",
      formula: "ratio = actualLaborHours / plannedLaborHours.",
      bands: [["green","Green","0.90-1.10"], ["yellow","Yellow","0.80-0.90 or 1.10-1.20"], ["amber","Amber","0.70-0.80 or 1.20-1.35"], ["red","Red","&lt; 0.70 or &gt; 1.35"]],
      abstain: "plannedLaborHours or actualLaborHours missing, or planned hours ≤ 0.",
      sources: "Resource Report.",
      interp: "This is a two-sided band: both under-loading (risk of schedule slip) and over-loading (risk of cost overrun or crew crowding) trigger the same escalating status, so the PM should check which direction the ratio is off before choosing an action.",
      ground: "Resource-loading histograms comparing actual to planned labor hours are a standard construction resource-management technique for detecting staffing mismatches against the baseline plan." },
    { n: "2.10", name: "Schedule Risk Analysis P80", mc: "Schedule_Risk_Analysis",
      purpose: "Produces a conservative P80 estimate of schedule delay beyond the baseline finish date, the schedule analogue of the Cat 1.1 Monte Carlo cost forecast.",
      formula: "remainingDays = total baseline days × (100 − actualPctComplete)/100; p50Days = remainingDays / SPI; uncertainty = max(0.05, 1 − SPI) × 0.5; p80Days = p50Days × (1 + uncertainty × 1.28); delayDays = round(p80Days − remainingDays).",
      bands: [["green","Green","delayDays ≤ 0"], ["yellow","Yellow","0-14 days"], ["amber","Amber","14-30 days"], ["red","Red","&gt; 30 days"]],
      abstain: "spi, baselineEnd, baselineStart or actualPctComplete missing, or baseline duration ≤ 0.",
      sources: "Schedule Update / Look-ahead, Time-phased Schedule / Baseline.",
      interp: "delayDays is the conservative (P80) projected slip beyond the baseline finish; a positive value even a few days above zero is worth tracking, since P80 is meant to be the number contingency schedule is planned against.",
      ground: "P80 schedule-risk analysis mirrors P80 cost-risk analysis (Cat 1.1/3.7): a single deterministic finish date is replaced with a conservative percentile estimate, applying an analytic uncertainty scaling (1.28 ≈ the z-score for the 80th percentile of a normal approximation) rather than a full simulation." },
    { n: "2.11", name: "Critical Path Index", mc: "Critical_Path_Index",
      purpose: "Blends the physical-progress ratio and SPI into a single composite index of schedule health along the critical path.",
      formula: "progressRatio = actualPctComplete / plannedPctComplete (falls back to SPI if plannedPctComplete is 0); criticalPathIndex = (progressRatio + SPI) / 2.",
      bands: [["green","Green","≥ 0.95"], ["yellow","Yellow","0.92-0.94"], ["amber","Amber","0.88-0.91"], ["red","Red","&lt; 0.88"]],
      abstain: "spi, plannedPctComplete or actualPctComplete missing.",
      sources: "Schedule Update / Look-ahead.",
      interp: "Because it averages two schedule reads, a low Critical Path Index confirmed by both a low progress ratio and a low SPI is stronger evidence than either alone; if the two components diverge sharply, check them individually.",
      ground: "Combining a physical-progress ratio with the cost-based SPI is a pragmatic cross-check technique, similar in spirit to how Cat 1.7 (Earned Schedule) and Cat 2.6 (S-Curve Deviation) each triangulate schedule health from more than one read." }
  ];

  /* ---------- Cat 3, Cost Simulation (3.1-3.10) ---------- */
  const CAT3_MODULES = [
    { n: "3.1", name: "Reference Class Forecasting", mc: "Reference_Class_Forecasting",
      purpose: "Replaces the project's own bottom-up cost estimate with the empirical distribution of overruns from comparable projects, correcting for optimism bias baked into inside-view estimates.",
      formula: "Fixed airport-infrastructure reference-class multiplier set [1.00, 1.04, 1.10, 1.14, 1.15, 1.26, 1.38, 1.45, 1.52]; P50/P80 read from this sorted array; P80 prior = BAC × multiplier[P80]; overP80 = (multiplier[P80] − 1) × 100.",
      bands: [["green","Green","P80 overrun ≤ 10% of BAC"], ["amber","Amber","10-25%"], ["red","Red","&gt; 25%"]],
      sources: "Historical Project Data, Past Performance Report, the reference class itself is a fixed synthetic distribution, not per-project extracted data; only BAC is read from the project.",
      interp: "The debiasing multiplier is the outside-view answer to 'what do comparable projects actually cost'; when it diverges sharply from the project's own bottom-up EAC (Cat 1.1/1.4), the gap is itself the finding worth escalating.",
      ground: "Reference Class Forecasting (Flyvbjerg, 2008) replaces inside-view estimation with the empirical outside-view distribution of a comparable reference class, the method now embedded in UK Treasury Green Book guidance for major infrastructure business cases." },
    { n: "3.2", name: "DSM Rework Propagation", mc: "DSM_Rework_Propagation",
      purpose: "Estimates the cumulative downstream rework triggered by a single architectural change, by propagating it through a fixed inter-discipline dependency matrix.",
      formula: "3×3 dependency matrix over {Arch, Structural, MEP}; unit change vector v0 = [1,0,0] is propagated for 4 passes (v(t+1) = A·v(t)); rework multiplier = sum of all accumulated values across the 4 passes and 3 disciplines. This module uses a fixed synthetic matrix, it does not read the project's live signal inputs.",
      bands: [["green","Green","rework multiplier ≤ 2.5"], ["amber","Amber","&gt; 2.5"]],
      sources: "BIM Execution Plan (BEP), Design Development (DD) Sets, conceptually informs the coupling strengths; the matrix itself is fixed/synthetic in this demo, not derived per-project.",
      interp: "A multiplier above 2.5 means a single unit of architectural change is estimated to generate more than 2.5 units of downstream coordination rework, a high-coordination-risk design phase where even small scope changes should go through a formal impact review before approval.",
      ground: "The Design Structure Matrix (Steward, 1981) captures dependency and feedback loops between design elements; propagating a unit change through the matrix to estimate cumulative rework underpins modern BIM clash-detection and integrated-project-delivery coordination practice." },
    { n: "3.3", name: "Contingency Burn Rate", mc: "Contingency_Burn_Rate",
      purpose: "Compares how much of the contingency reserve has been spent against how much of the physical work has been completed, flagging contingency being drawn down faster than the project is progressing.",
      formula: "burnRate = (originalContingency − remainingContingency) / originalContingency; expectedBurn = actualPctComplete/100; burnStress = burnRate / expectedBurn.",
      bands: [["green","Green","burnStress ≤ 1.0"], ["yellow","Yellow","1.0-1.3"], ["amber","Amber","1.3-1.6"], ["red","Red","&gt; 1.6"]],
      abstain: "originalContingency, remainingContingency or actualPctComplete missing, or originalContingency ≤ 0.",
      sources: "Pay Application (contingency line item), Cost Report.",
      interp: "A burn stress above 1.0 means contingency is being consumed faster than the work is being earned; sustained stress above 1.6 means the reserve will be exhausted well before completion at the current draw rate.",
      ground: "Contingency drawdown-versus-progress tracking is a standard program-controls discipline for public capital budgets, where contingency is a finite, board-approved reserve rather than an open-ended buffer." },
    { n: "3.4", name: "Labor Productivity Index", mc: "Labor_Productivity",
      purpose: "Measures earned labor-hour efficiency: how much of the planned labor budget was actually needed to produce the work completed to date.",
      formula: "earnedHoursRate = ((actualPctComplete/100) × plannedLaborHours) / actualLaborHours.",
      bands: [["green","Green","≥ 0.95"], ["yellow","Yellow","0.85-0.94"], ["amber","Amber","0.75-0.84"], ["red","Red","&lt; 0.75"]],
      abstain: "plannedLaborHours, actualLaborHours or actualPctComplete missing, or actualLaborHours ≤ 0.",
      sources: "Resource Report, Cost Report.",
      interp: "A rate below 1.0 means more hours were consumed than the earned percent-complete would justify, a direct labor-productivity shortfall worth reconciling against crew size, rework, or scope-growth explanations in the field reports.",
      ground: "Earned-hours productivity tracking (earned hours ÷ actual hours) is the standard construction labor-productivity metric, distinct from CPI because it isolates the labor component from material/subcontract cost variance." },
    { n: "3.5", name: "Material Cost Variance", mc: "Material_Cost_Variance",
      purpose: "Compares actual material cost against the baseline expectation at current progress, isolating material-price risk from labor or overhead variance.",
      formula: "expected = materialCostBaseline × (actualPctComplete/100); variance = (materialCostCurrent − expected) / expected.",
      bands: [["green","Green","|variance| ≤ 5%"], ["yellow","Yellow","5-12%"], ["amber","Amber","12-20%"], ["red","Red","&gt; 20%"]],
      abstain: "materialCostBaseline or materialCostCurrent missing.",
      sources: "Cost Report; when absent, the value is estimated as ~40% of BAC/AC and flagged '[est.]', a Cat 9 (Source Reliability) input.",
      interp: "This module isolates material cost specifically; a material variance that is much worse than the overall CPI points to a commodity price or procurement issue rather than a general execution problem.",
      ground: "Cost-variance-by-cost-category decomposition (material, labor, overhead) is standard practice for pinpointing which cost driver is responsible for an overall CPI shortfall, rather than treating cost variance as a single undifferentiated number." },
    { n: "3.6", name: "Overhead Absorption Rate", mc: "Overhead_Absorption",
      purpose: "Checks whether indirect (overhead) cost is being absorbed at a rate consistent with physical progress, distinct from direct-cost CPI.",
      formula: "planned = indirectCostPlan × (actualPctComplete/100); absorption = indirectCostActual / planned.",
      bands: [["green","Green","≤ 1.05"], ["yellow","Yellow","1.05-1.15"], ["amber","Amber","1.15-1.30"], ["red","Red","&gt; 1.30"]],
      abstain: "indirectCostPlan or indirectCostActual missing.",
      sources: "Cost Report; when absent, estimated at a 12% overhead-rate proxy and flagged '[est.]'.",
      interp: "An absorption rate above 1.0 means overhead is running ahead of progress, a fixed-cost/duration risk that compounds if the schedule slips further, since overhead accrues by time, not by units of work completed.",
      ground: "Overhead absorption analysis, comparing actual indirect cost to the rate implied by progress, is a standard cost-accounting check that isolates fixed/time-based cost risk from the direct-cost performance already captured by CPI." },
    { n: "3.7", name: "Cost Risk Analysis P80", mc: "Cost_Risk_Analysis",
      purpose: "Produces an analytic (non-simulated) P80 conservative cost estimate as a fast cross-check against the full Cat 1.1 Monte Carlo run.",
      formula: "eac = BAC/CPI; uncertainty = max(0.03, |1 − CPI|) × 0.5; p80EAC = eac × (1 + uncertainty × 1.28); p80DeltaPct = ((p80EAC − BAC)/BAC) × 100.",
      bands: [["green","Green","p80DeltaPct ≤ 5%"], ["yellow","Yellow","5-10%"], ["amber","Amber","10-20%"], ["red","Red","&gt; 20%"]],
      abstain: "bac, cpi, ac or ev missing.",
      sources: "Pay Application, Schedule of Values, Cost Report.",
      interp: "This is an analytic shortcut, not a full simulation; when it disagrees with Cat 1.1's simulated P80, the simulated figure should be treated as the more defensible one for a formal funding conversation, but disagreement itself is worth investigating.",
      ground: "The 1.28 scaling factor approximates the 80th-percentile z-score of a normal distribution, a standard analytic proxy for percentile-based risk estimation when a full Monte Carlo run is not warranted." },
    { n: "3.8", name: "Analogous Estimating Ratio", mc: "Analogous_Estimating",
      purpose: "Applies a documented overrun percentage from an analogous prior project directly to this project's BAC, a lightweight top-down cross-check independent of Cat 3.1's fixed reference class.",
      formula: "exposure = BAC × analogousOverrunPct / 100.",
      bands: [["green","Green","overrun &lt; 3%"], ["yellow","Yellow","3-7%"], ["amber","Amber","7-12%"], ["red","Red","≥ 12%"]],
      abstain: "analogousOverrunPct or bac missing.",
      sources: "Historical Project Data, Past Performance Report, the analogous overrun figure is a documented, project-specific analog rather than a fixed distribution.",
      interp: "The dollar exposure figure is what makes this module actionable: it converts an abstract percentage into the specific contingency amount a reviewer should expect to hold in reserve, based on how a genuinely comparable project actually performed.",
      ground: "Analogous estimating, using an actual prior project's documented result as the basis for a percentage adjustment, is one of PMI's three standard estimating techniques (Project Management Institute, 2019), alongside parametric and bottom-up estimating." },
    { n: "3.9", name: "Parametric Cost Index", mc: "Parametric_Cost",
      purpose: "Cross-checks the CPI-based EAC against an independent parametric EAC formula, similar to Cat 1.12's ICE Ratio but with tighter bands appropriate to cost-category-level review.",
      formula: "eacCPI = BAC/CPI; eacParametric = AC + (BAC − EV); parametricIndex = eacCPI / eacParametric.",
      bands: [["green","Green","|index−1| ≤ 3%"], ["yellow","Yellow","3-8%"], ["amber","Amber","8-15%"], ["red","Red","&gt; 15%"]],
      abstain: "bac, ev, ac or actualPctComplete missing, or eacParametric ≤ 0.",
      sources: "Pay Application, Schedule of Values, Cost Report.",
      interp: "Because this module uses tighter tolerance bands than the closely related Cat 1.12 ICE Ratio, it can flag divergence between forecasting methods earlier, treat a Cat 3.9 Amber/Red alongside a still-Green Cat 1.12 as an early warning to reconcile forecasting assumptions before it becomes a larger gap.",
      ground: "Parametric estimating (deriving cost from a statistical relationship between historical data and project parameters) is a standard PMI estimating technique (Project Management Institute, 2019); comparing it against the CPI-based EAC applies the same independent-cross-check logic as Cat 1.12." },
    { n: "3.10", name: "Inflation Adjustment Index", mc: "Inflation_Adjustment",
      purpose: "Isolates the portion of material cost overrun attributable to price escalation above the expected baseline rate, distinct from quantity or scope-driven cost variance.",
      formula: "expected = materialCostBaseline × (actualPctComplete/100); escalation = max(0, (materialCostCurrent − expected) / expected).",
      bands: [["green","Green","≤ 4%"], ["yellow","Yellow","4-8%"], ["amber","Amber","8-15%"], ["red","Red","&gt; 15%"]],
      abstain: "materialCostBaseline or materialCostCurrent missing.",
      sources: "Cost Report; when absent, estimated the same way as Cat 3.5 and flagged '[est.]'.",
      interp: "Unlike Cat 3.5 (which reports variance in either direction), this module only counts positive escalation, so it should be read as a market/commodity risk exposure figure, not a full material cost-variance read.",
      ground: "Escalation tracking against a baseline material cost index is standard practice on multi-year public capital programs, where material price volatility (structural steel, copper, concrete) is a well-documented, non-performance-driven source of overrun." }
  ];

  /* ---------- Cat 4, Document & Risk Signals (4.1-4.10) ---------- */
  const CAT4_MODULES = [
    { n: "4.1", name: "Document Risk Score", mc: "Doc_Risk_Cat4",
      purpose: "The Cat 4 view of the same document-risk score computed in Cat 1.3, surfaced here alongside the other qualitative Cat 4 signals for category-level rollup.",
      formula: "Identical computation to Cat 1.3 (Document Risk Extraction): a weighted sum of matched keyword/pattern rules across project records, normalised to 0-1.",
      bands: [["green","Green","score &lt; 0.30"], ["amber","Amber","0.30-0.70"], ["red","Red","≥ 0.70"]],
      sources: "RFI / RFI Log, Submittal / Submittal Register, OAC Meeting Minutes, Correspondence / Notice, Risk Register, Inspection Report / NCR.",
      interp: "Read this the same way as Cat 1.3, it is the same score; its presence in Cat 4 lets the document-risk category roll up alongside RFI velocity, submittal rejection, and the other qualitative Cat 4 signals rather than only living under EVM.",
      ground: "Same grounding as Cat 1.3: transparent, auditable rule-based scoring rather than a black-box classifier." },
    { n: "4.2", name: "RFI Velocity", mc: "RFI_Velocity",
      purpose: "Tracks the rate of new RFIs per week and the share overdue, a classic leading indicator of scope ambiguity, design conflicts, or coordination problems.",
      formula: "rfiPerWeek = (rfiCount / rfiPeriodDays) × 7; overdueRatio = rfiOverdue / rfiCount (when overdue data is available). Status is the worse of the velocity band and the overdue band.",
      bands: [["green","Green","≤ 2 RFIs/week, and overdue ratio &lt; 10%"], ["yellow","Yellow","2-4/week, or overdue ratio 10-20%"], ["amber","Amber","4-8/week, or overdue ratio 20-35%"], ["red","Red","&gt; 8/week, or overdue ratio ≥ 35%"]],
      abstain: "rfiCount (or the legacy rfiNumber fallback) is null.",
      sources: "RFI / RFI Log, with period-days, overdue count, average response days, and oldest-open days used when available; falls back to an estimated 30-day period (flagged '[est.]') if the RFI log lacks explicit dates.",
      interp: "A high overdue ratio combined with a slow average response time (&gt;14 days) points to dispute risk on top of raw volume, worth flagging even if the raw per-week velocity still reads Green.",
      ground: "RFI velocity and aging are standard leading indicators in construction claims and delay-analysis practice; a spike in RFI volume with slow turnaround is a well-documented precursor to schedule and cost impact well before it registers in EVM." },
    { n: "4.3", name: "Submittal Rejection Rate", mc: "Submittal_Rejection",
      purpose: "Tracks the share of submittals (or RFAs) rejected or requiring revise-and-resubmit, a leading indicator of design/spec quality and contractor coordination problems.",
      formula: "rejectionRate = rejected / total, preferring the RFA log (rfaTotal/rfaRejected) when present, falling back to the submittal register (submittalsTotal/submittalsRejected).",
      bands: [["green","Green","≤ 5%"], ["yellow","Yellow","5-15%"], ["amber","Amber","15-25%"], ["red","Red","&gt; 25%"]],
      abstain: "both total and rejected counts (RFA or submittal) are missing.",
      sources: "RFA / Approval Log (preferred), Submittal / Submittal Register (fallback); estimated from document risk when neither is available and flagged '[est.]'.",
      interp: "A high rejection rate concentrated in one discipline usually points to a specification or coordination issue at the design level, not contractor performance, worth checking against Cat 4.10 (Spec Conflict Density) before attributing it to the sub.",
      ground: "Submittal cycle-time and rejection-rate tracking is a standard construction quality-management metric; repeated rejections consume float invisibly, a well-known driver of schedule slip that predates any EVM impact." },
    { n: "4.4", name: "NCR Rate", mc: "NCR_Rate",
      purpose: "Tracks the share of issued non-conformance reports that remain open, a direct quality-control signal (construction/hybrid sectors only).",
      formula: "openRatio = ncrOpen / max(ncrIssued, 1). If no NCRs were issued this period, the module reports Green directly.",
      bands: [["green","Green","open ratio &lt; 15%, or zero NCRs issued"], ["yellow","Yellow","15-30%"], ["amber","Amber","30-50%"], ["red","Red","≥ 50%"]],
      abstain: "ncrIssued, ncrClosed or ncrOpen missing.",
      sources: "NCR Log (Non-Conformance), Inspection Report / NCR.",
      interp: "A high open ratio (not just a high issued count) is the signal to watch: it means non-conformances are accumulating faster than they are being closed out, a backlog that grows quality and re-inspection risk the longer it persists.",
      ground: "Open-versus-closed NCR tracking is a standard construction-quality KPI; sector-gated to construction/hybrid because non-conformance reports as defined here are a field-inspection artifact specific to physical construction work." },
    { n: "4.5", name: "Weather Day Impact", mc: "Weather_Impact",
      purpose: "Measures how much of the project's remaining float has been consumed by documented weather delays (construction/hybrid sectors only).",
      formula: "weatherRatio = weatherDaysLost / floatRemaining (float from floatRemaining, or totalFloat − consumedFloat).",
      bands: [["green","Green","zero weather days lost"], ["yellow","Yellow","weatherRatio ≤ 20% of float"], ["amber","Amber","20-50%"], ["red","Red","&gt; 50%"]],
      abstain: "weatherDaysLost missing.",
      sources: "Daily / Weekly Field Report; estimated when float data is unavailable and flagged '[est.]'.",
      interp: "This module reads weather loss relative to remaining float, not in absolute days, so the same 10 lost weather days is Yellow on a project with ample float and Red on one that has already burned most of its schedule cushion.",
      ground: "Weather-day tracking against remaining float, rather than in isolation, is standard delay-analysis practice for excusable, non-compensable delay claims on public construction contracts." },
    { n: "4.6", name: "Change Order Frequency", mc: "CO_Frequency",
      purpose: "Tracks both the count of change orders and the resulting scope growth as a percentage of the original contract sum, a joint indicator of scope stability.",
      formula: "scopeGrowth = ((revisedContractSum − baselineContractSum)/baselineContractSum) × 100. Status requires BOTH the CO count and the scope-growth percentage to clear a band together.",
      bands: [["green","Green","scope growth ≤ 5% AND ≤ 3 change orders"], ["yellow","Yellow","≤ 10% AND ≤ 6"], ["amber","Amber","≤ 20% AND ≤ 10"], ["red","Red","exceeds either bound"]],
      abstain: "changeOrderCount, baselineContractSum or revisedContractSum missing.",
      sources: "Change Order / PCO; estimated from document risk when the log is unavailable and flagged '[est.]'.",
      interp: "Because status requires both the count and the percentage band, a project can trip Red on either driver alone, e.g. many small change orders (count-driven) or one large scope addition (percentage-driven) present very differently and call for different governance conversations.",
      ground: "Change-order frequency and cumulative scope growth are the two standard metrics for scope-creep monitoring on fixed-price public contracts, where both frequent modification and large cumulative growth are separately actionable under most agency change-management policies." },
    { n: "4.7", name: "Dispute Escalation Index", mc: "Dispute_Escalation",
      purpose: "Combines RFI volume, change-order volume, and document risk into a single composite index estimating the trajectory toward formal dispute.",
      formula: "index = min(rfiCount/20,1)×0.3 + min(changeOrderCount/10,1)×0.3 + docRiskScore×0.4.",
      bands: [["green","Green","≤ 0.20"], ["yellow","Yellow","0.20-0.40"], ["amber","Amber","0.40-0.65"], ["red","Red","&gt; 0.65"]],
      abstain: "docRiskScore missing.",
      sources: "RFI / RFI Log, Change Order / PCO, and the same document set feeding Cat 1.3/4.1 document risk.",
      interp: "This is a composite trailing/leading blend, not a single documented dispute; a rising index over consecutive periods, even while still Amber, is the pattern worth a proactive OAC conversation before it becomes a formal claim.",
      ground: "Combining correspondence volume with document-risk language into a single escalation index reflects standard claims-avoidance practice: disputes rarely appear from nowhere, they accumulate through RFI/CO volume and increasingly adversarial correspondence language." },
    { n: "4.8", name: "Subcontractor Performance", mc: "Subcontractor_Performance",
      purpose: "Rolls up OAC-minutes issue mentions, outstanding action items, open NCRs, and document risk into a single subcontractor compliance score (construction/hybrid sectors only).",
      formula: "scorePct = round(subcontractorComplianceScore × 100), where the underlying compliance score is derived (in signals.js) from the contributing signals listed above when not directly supplied.",
      bands: [["green","Green","≥ 85%"], ["yellow","Yellow","70-84%"], ["amber","Amber","55-69%"], ["red","Red","&lt; 55%"]],
      abstain: "subcontractorComplianceScore, subcontractorIssuesDiscussed and docRiskScore are all null.",
      sources: "OAC Meeting Minutes, NCR Log, Subcontractor Performance Report, Correspondence / Notice.",
      interp: "The evidence string lists exactly which contributing signals drove the score down (OAC issues, outstanding action items, open NCRs, elevated doc risk), giving the PM a specific starting point for the subcontractor conversation rather than a bare number.",
      ground: "Deriving a subcontractor scorecard from meeting-minutes issue tracking and NCR history, rather than a single formal survey, reflects standard practice for continuously updating subcontractor performance records between formal review cycles." },
    { n: "4.9", name: "Procurement Lead Time Monitor", mc: "Procurement_Lead_Time",
      purpose: "Weighs at-risk and already-delayed long-lead procurement items into a single disruption ratio, with delayed items counted twice as heavily as merely at-risk ones (construction/hybrid sectors only).",
      formula: "riskRatio = (longLeadAtRisk + 2 × longLeadDelayed) / longLeadItemsTotal.",
      bands: [["green","Green","&lt; 15%"], ["yellow","Yellow","15-30%"], ["amber","Amber","30-50%"], ["red","Red","≥ 50%"]],
      abstain: "longLeadItemsTotal, longLeadAtRisk or longLeadDelayed missing.",
      sources: "Procurement Log.",
      interp: "The 2x weighting on already-delayed items means this module reacts faster to confirmed delays than to merely at-risk items, appropriate since a delayed long-lead item is a near-certain schedule impact while an at-risk one may still resolve.",
      ground: "Long-lead-item tracking, weighted by delay severity, is a standard procurement-risk-management technique on capital programs where equipment lead times (switchgear, elevators, specialty glazing) routinely exceed the construction schedule float available to absorb them." },
    { n: "4.10", name: "Specification Conflict Density", mc: "Spec_Conflict_Density",
      purpose: "Weights the raw document-risk score by RFI volume (via a square-root dampening) to estimate how concentrated specification conflicts are, distinguishing a genuinely conflict-dense document set from one that simply has a lot of routine RFIs.",
      formula: "conflictDensity = (docRiskScore × rfiCount) / sqrt(rfiCount), clamped to [0,1]; falls back to docRiskScore alone if rfiCount is 0.",
      bands: [["green","Green","≤ 0.15"], ["yellow","Yellow","0.15-0.35"], ["amber","Amber","0.35-0.60"], ["red","Red","&gt; 0.60"]],
      abstain: "docRiskScore or rfiCount missing.",
      sources: "Technical Specifications, RFI / RFI Log, Construction Documents (CD Sets).",
      interp: "The square-root dampening means this metric grows sub-linearly with RFI volume, a project with many RFIs but low per-RFI risk language scores lower here than one with fewer RFIs but consistently high-risk language, isolating conflict density from raw volume (already covered by Cat 4.2).",
      ground: "Weighting a risk score by document volume with a sub-linear (square-root) dampening is a standard technique for avoiding double-counting when two correlated signals (document risk and RFI count) are combined into one index." }
  ];

  /* ---------- Cat 5, System Dynamics & Complexity (5.1-5.8) ---------- */
  const CAT5_MODULES = [
    { n: "5.1", name: "DSM Rework Propagation", mc: "DSM_Rework_Cat5",
      purpose: "The Cat 5 (systems view) presentation of the same DSM rework-propagation result computed once in Cat 3.2, read here as a demonstration of how a design change amplifies through the interacting system rather than as a cost estimate.",
      formula: "Identical computation and result to Cat 3.2, this module is a status alias (module.method_class 'DSM_Rework_Cat5' resolves via getModuleStatus() to the Cat 3.2 'DSM_Rework_Propagation' result), not a second calculation.",
      bands: [["green","Green","rework multiplier ≤ 2.5"], ["amber","Amber","&gt; 2.5"]],
      sources: "Same as Cat 3.2: BIM Execution Plan (BEP), Design Development (DD) Sets.",
      interp: "Read this alongside the rest of Cat 5 as the system-dynamics illustration of amplification and feedback, and alongside Cat 3.2 as the cost-impact reading of the same underlying propagation.",
      ground: "Same grounding as Cat 3.2 (Steward, 1981); presenting one computed result under two category lenses reflects that DSM is simultaneously a cost-estimating tool and a systems-dynamics amplification model." },
    { n: "5.2", name: "Sensitivity Analysis", mc: "Sensitivity_Analysis",
      purpose: "Identifies which single input variable (cost performance, schedule performance, or document risk) currently has the largest effect on the project's forecast, so review effort is focused on the variable that matters most this cycle.",
      formula: "cpiSensitivity = |EAC(CPI−0.05) − EAC(CPI+0.05)| / EAC(CPI); spiSensitivity = |SPI − 1.0| × 0.5; docSensitivity = docRiskScore. The three are ranked; the top driver and its sensitivity value are reported.",
      bands: [["green","Green","top sensitivity ≤ 10%"], ["yellow","Yellow","10-20%"], ["amber","Amber","20-35%"], ["red","Red","&gt; 35%"]],
      abstain: "bac, ev, ac, pv, cpi or spi missing.",
      sources: "Pay Application, Schedule of Values, Cost Report, RFI / RFI Log (for document risk).",
      interp: "The top driver named in the evidence string tells the PM where a small data-quality improvement or a small performance change would most change the governance recommendation, directing limited verification effort to the highest-leverage input.",
      ground: "One-at-a-time sensitivity analysis (perturbing a single input while holding others fixed) is the standard first-pass technique in quantitative risk analysis before committing to a full multivariate simulation." },
    { n: "5.3", name: "Tornado Risk Ranking", mc: "Tornado_Diagram",
      purpose: "Ranks four risk drivers (cost performance, schedule performance, document risk, progress variance) by impact magnitude, the classic tornado-diagram presentation of relative risk contribution.",
      formula: "Four impacts: |1−CPI|×100, |1−SPI|×100, docRiskScore×100, |actualPctComplete − plannedPctComplete|; ranked descending; compositeScore = mean of the four.",
      bands: [["green","Green","composite ≤ 5"], ["yellow","Yellow","5-10"], ["amber","Amber","10-20"], ["red","Red","&gt; 20"]],
      abstain: "cpi, spi, docRiskScore, actualPctComplete or plannedPctComplete missing.",
      sources: "Pay Application, Schedule of Values, Cost Report, RFI / RFI Log, Schedule Update / Look-ahead.",
      interp: "The top-ranked risk in the evidence string is the single largest contributor to the composite score this period; unlike Cat 5.2 (which reports sensitivity to a hypothetical change), this reports current impact magnitude as observed.",
      ground: "Tornado diagrams (ranking risk variables by impact magnitude, widest bar on top) are a standard qualitative risk-analysis visualization technique in project risk management practice." },
    { n: "5.4", name: "Scenario Modeling", mc: "Scenario_Modeling",
      purpose: "Projects three explicit EAC scenarios (optimistic, realistic, pessimistic) and reports the spread between them as a decision-uncertainty metric.",
      formula: "remainingWork = BAC − EV; optimisticEAC = AC + remainingWork × 1.00; realisticEAC = AC + remainingWork/CPI; pessimisticEAC = AC + remainingWork/min(CPI,SPI); scenarioRange = (pessimisticEAC − optimisticEAC)/BAC × 100.",
      bands: [["green","Green","pessimistic EAC ≤ BAC × 1.05"], ["yellow","Yellow","≤ 1.10"], ["amber","Amber","≤ 1.20"], ["red","Red","&gt; 1.20"]],
      abstain: "bac, ev, ac, cpi or spi missing.",
      sources: "Pay Application, Schedule of Values, Cost Report.",
      interp: "Unlike Cat 1.1's simulated distribution, this is three fixed deterministic points; a wide gap between the three scenarios (large scenarioRange) even with a Green status on the pessimistic band alone is itself informative about how uncertain the current forecast really is.",
      ground: "Three-point (optimistic/most-likely/pessimistic) scenario forecasting is the deterministic ancestor of full Monte Carlo simulation, still standard practice for a quick range estimate when a full stochastic run is not required." },
    { n: "5.5", name: "Rework Feedback Loop", mc: "Rework_Feedback",
      purpose: "Combines RFI volume, change-order volume, and CPI degradation into a single index estimating how much of current cost inefficiency is being driven by a rework feedback loop rather than original scope.",
      formula: "index = min(rfiCount/30,1)×0.3 + min(changeOrderCount/15,1)×0.3 + max(0, 1−CPI)×0.4.",
      bands: [["green","Green","≤ 0.10"], ["yellow","Yellow","0.10-0.25"], ["amber","Amber","0.25-0.45"], ["red","Red","&gt; 0.45"]],
      abstain: "cpi missing.",
      sources: "Pay Application (CPI), RFI / RFI Log, Change Order / PCO.",
      interp: "A high index concentrated in the RFI/CO terms (rather than the CPI term) suggests the cost drag is coordination-driven and may respond to a design-clarification push; a high index driven mainly by the CPI term suggests a broader execution problem.",
      ground: "System-dynamics rework feedback loops (undiscovered rework generating further rework, compounding cost) are a well-documented mechanism in construction project system-dynamics modelling literature (e.g., Cooper's Rework Cycle models used in program-level system dynamics studies)." },
    { n: "5.6", name: "Queueing Theory Bottleneck", mc: "Queueing_Bottleneck",
      purpose: "Reads the same near-term constraint data as Cat 2.8 through a queueing-theory lens: a high share of constrained activities means work is queuing up behind a bottleneck resource or predecessor.",
      formula: "constraintRatio = activitiesConstrained / activitiesPlanned. (Same underlying fields as Cat 2.8, with tighter thresholds appropriate to a bottleneck-severity read.)",
      bands: [["green","Green","&lt; 15%"], ["yellow","Yellow","15-25%"], ["amber","Amber","25-40%"], ["red","Red","≥ 40%"]],
      abstain: "activitiesPlanned or activitiesConstrained missing.",
      sources: "Look-Ahead Schedule (6-week), same source as Cat 2.8.",
      interp: "Where Cat 2.8 asks 'is the near-term schedule healthy', this module asks 'is there a systemic bottleneck resource'; a persistently high constraint ratio across several periods, not just one, is the pattern that indicates a structural bottleneck rather than a transient blockage.",
      ground: "Queueing theory (work arriving faster than a constrained resource can process it, Little's Law: L = λW) is the formal framework behind Theory of Constraints bottleneck management, applied here as a simplified constrained-activity-share proxy." },
    { n: "5.7", name: "Agent-Based Supply Chain", mc: "Agent_Supply_Chain",
      purpose: "Reads the raw at-risk share of long-lead procurement items, a different lens on the Cat 4.9 procurement data that does not weight already-delayed items more heavily.",
      formula: "atRiskRatio = longLeadAtRisk / longLeadItemsTotal. (Compare to Cat 4.9's weighted riskRatio = (atRisk + 2×delayed)/total, this module reports the unweighted at-risk share alone.)",
      bands: [["green","Green","&lt; 10%"], ["yellow","Yellow","10-20%"], ["amber","Amber","20-35%"], ["red","Red","≥ 35%"]],
      abstain: "longLeadItemsTotal or longLeadAtRisk missing.",
      sources: "Procurement Log, same source as Cat 4.9.",
      interp: "Because this is the unweighted at-risk share, Cat 5.7 can read Green while Cat 4.9 (which double-weights delayed items) reads worse, or vice versa; reading both together separates 'many items are merely at risk' from 'a smaller number are already confirmed delayed'.",
      ground: "Agent-based supply-chain modelling (Bonabeau, 2002) treats procurement as a network of interacting agents (suppliers, fabricators, the project) whose individual delay risk aggregates into program-level exposure; this implementation is a simplified aggregate proxy for that fuller agent-based simulation." },
    { n: "5.8", name: "Discrete Event Simulation", mc: "Discrete_Event_Sim",
      purpose: "Estimates a throughput index representing how much schedule interruption (from progress lag and SPI shortfall combined) the project is absorbing, the closest Cat 5 module to a true process-simulation read.",
      formula: "progressRatio = actualPctComplete / plannedPctComplete; interruptionRate = max(0, 1 − progressRatio) + max(0, 1 − SPI) × 0.5; throughputIndex = 1 / (1 + interruptionRate).",
      bands: [["green","Green","≥ 0.92"], ["yellow","Yellow","0.85-0.91"], ["amber","Amber","0.75-0.84"], ["red","Red","&lt; 0.75"]],
      abstain: "spi, actualPctComplete, plannedPctComplete or cpi missing.",
      sources: "Schedule Update / Look-ahead, Pay Application.",
      interp: "throughputIndex compresses two separate interruption sources (progress lag and SPI shortfall) into one number; a low index confirmed by both underlying terms is stronger evidence of systemic disruption than a low index driven by only one.",
      ground: "Discrete event simulation (Law &amp; Kelton, 2000) models a system as a sequence of state-changing events with interruptions and queues; this implementation is a lightweight closed-form throughput proxy rather than a full event-by-event simulation." }
  ];

  /* ---------- Cat 6, Signal Synthesis (6.1-6.4) ---------- */
  const CAT6_MODULES = [
    { n: "6.1", name: "Conservative Dominance", mc: "Conservative_Dominance",
      purpose: "The governance baseline: the worst single signal class drives the overall classification, and the specific TYPE of disagreement between signal classes is named rather than averaged away.",
      formula: "Six precedence-ordered conflict types are evaluated in order (first match wins): Multi-signal Red-review (≥2 Red), Anomaly Without Narrative (CUSUM Red, EVM Amber/Green), Leading Document Risk (Doc Red, EVM Green), Single Signal Watch (one Amber), Mixed Early Warning (Ambers only), Agreement/All Stable (all Green). Runs in the main signal pipeline (decision.js), not simulations.js.",
      sources: "Consumes the already-computed outputs of Cat 1 (EVM, CUSUM, Doc Risk) and Cat 1.1 (Monte Carlo forecast), no independent document extraction of its own.",
      interp: "Conservative Dominance never averages a Red into a 'slightly Amber' reading; the worst signal wins by design, so a project with one severe problem and several healthy metrics still surfaces as needing review, the deliberate opposite of a weighted average.",
      ground: "Conservative dominance (worst-signal-wins classification with named conflict typing) is a deliberate governance design choice favoring transparency and precaution over statistical optimality, it is the interpretable baseline that the 20 Cat 7 evidence-combination methods then cross-check." },
    { n: "6.2", name: "Weighted Voting", mc: "Weighted_Voting",
      purpose: "Aggregates every currently-computed module's status into a single weighted vote, giving core EVM/Doc-Risk signals more influence than the 20 Cat 7 evidence-combination methods, which each individually carry low weight.",
      formula: "Per-category weights: Cat 1 (EVM/CUSUM) 1.5, Cat 2 1.2, Cat 3 1.2, Cat 4 1.0, Cat 5 0.8, Cat 6 1.0, Cat 7 0.6, decision-state 1.5. Votes accumulate into Green/Yellow/Amber/Red buckets; the status is the bucket with the most accumulated weight; dominantPct reports its share of the total weighted vote.",
      abstain: "no module has produced a status yet (total weighted vote is 0).",
      sources: "Consumes every other module's already-computed status; no independent document extraction.",
      interp: "The dominantPct is the confidence read: a status that carries 80%+ of the weighted vote is far more decisive than one that barely edges out a close second place, worth checking dominantPct even when the headline status looks fine.",
      ground: "Weighted voting is a standard ensemble-classification technique; weighting core EVM/document signals above the 20 lower-weighted evidence-combination methods reflects that Cat 7's methods are individually exploratory cross-checks, not independent primary evidence sources." },
    { n: "6.3", name: "Majority Rules", mc: "Majority_Rules",
      purpose: "The unweighted counterpart to Cat 6.2, simple plurality vote across every currently-computed module's status, with no category weighting.",
      formula: "Counts each module's status into Green/Yellow/Amber/Red buckets (one vote per module, no weighting); status is the bucket with the most votes; majorityPct = winning count / total votes.",
      abstain: "no module has produced a status yet.",
      sources: "Consumes every other module's already-computed status; no independent document extraction.",
      interp: "Comparing Cat 6.2 (weighted) and Cat 6.3 (unweighted) side by side shows whether the 'core signals' or the 'raw module count' are driving the outcome; a sharp disagreement between the two means a large bloc of lower-weighted Cat 7 methods is outvoting a smaller number of high-weight core signals.",
      ground: "Simple majority voting is the baseline ensemble method against which weighted voting (Cat 6.2) is normally benchmarked in classifier-ensemble literature." },
    { n: "6.4", name: "Worst-N-of-M", mc: "Worst_N_of_M",
      purpose: "A threshold-count rule: escalates based on how many of the total M computed modules are Red or Amber, rather than on any single worst signal (Cat 6.1) or a weighted vote (Cat 6.2/6.3).",
      formula: "redCount and amberCount tallied across all computed modules (M total). Red if redCount ≥ ceil(M × 0.30); Amber if amberCount ≥ ceil(M × 0.40); Yellow if redCount ≥ 1; else Green.",
      abstain: "no module has produced a status yet.",
      sources: "Consumes every other module's already-computed status; no independent document extraction.",
      interp: "This module escalates on breadth of concern (how many modules are Red/Amber) rather than depth (how bad any one signal is), a useful counterweight to Cat 6.1's worst-single-signal logic when several modules are moderately concerning but none individually severe.",
      ground: "N-of-M threshold voting is a standard fault-tolerant-systems technique (a system is considered failed once N of M independent checks fail); applying it to a governance signal package treats module agreement as a redundancy/consensus check." }
  ];

  /* ---------- Cat 7, Evidence Combination (7.1-7.20) ---------- */
  const CAT7_MODULES = [
    { n: "7.1", name: "Dempster-Shafer", mc: "DST_Evidence_Combination",
      purpose: "Combines four independent evidence sources (EVM, Monte Carlo forecast, CUSUM, document risk) into explicit belief masses over {Green, Amber, Red, Unknown}, rather than taking the single worst signal.",
      formula: "Each source assigns a basic probability assignment (mass function); Dempster's combination rule merges sources pairwise, normalising out the conflict mass K = Σ mass pairs whose intersection is empty. Final state = argmax belief mass.",
      bands: [["green","Low (K &lt; 0.10)","sources broadly agree, result is reliable"], ["amber","Moderate (0.10-0.30)","some inter-signal tension"], ["red","High (K &gt; 0.30)","strong disagreement, itself a governance finding"]],
      sources: "Consumes existing Cat 1 EVM/CUSUM/Doc Risk and Cat 1.1 Monte Carlo outputs.",
      interp: "When DST and Cat 6.1 agree, both corroborate each other; when they diverge, the divergence is recorded rather than resolved in favor of one method, telling the reviewer the evidence picture is genuinely ambiguous.",
      ground: "Dempster-Shafer Theory (Dempster, 1967; Shafer, 1976) is a mathematical framework for combining evidence from multiple independent sources under uncertainty, explicitly modelling and quantifying inter-source conflict rather than assuming sources always agree." },
    { n: "7.2", name: "Rough Sets", mc: "Rough_Sets_Classification",
      purpose: "Classifies the project's state via lower/upper set approximations rather than a single point estimate, explicitly naming the indeterminate boundary region when evidence is insufficient for a definite classification.",
      formula: "Each of the four evidence sources is bucketed into Green/Amber/Red; lower approximation = states with &gt;75% signal agreement; upper approximation = states with any support; boundary = upper − lower.",
      bands: [["green","Definite","lower approximation contains exactly one state"], ["amber","Borderline","boundary region is non-empty (Red if it contains Red, else Amber)"], ["amber","Indeterminate","upper approximation spans multiple states with no clear majority"]],
      sources: "Consumes existing Cat 1 EVM/CUSUM/Doc Risk and Cat 1.1 Monte Carlo outputs.",
      interp: "A non-empty boundary region is itself the finding: it means the current evidence set cannot yet support a confident single classification, and the governance response should be to gather more evidence, not to force a verdict.",
      ground: "Rough Set Theory (Pawlak, 1982) provides a set-theoretic framework for classification under incomplete or imprecise information, distinguishing what is definitely, possibly, and indeterminately true given the available attributes." },
    { n: "7.3", name: "Neutrosophic Logic", mc: "Neutrosophic_Logic",
      purpose: "Adds indeterminacy (I) as an independent third dimension alongside truth (T) and falsity (F), so genuine unresolvable uncertainty is modelled explicitly rather than folded into a soft Amber reading.",
      formula: "T_combined = 1 − ∏(1−Tᵢ) (disjunctive); I_combined = ∏Iᵢ; F_combined = ∏Fᵢ (both conjunctive); normalised so T+I+F sums consistently. Status: Red if ≥2 sources Red, Amber if ≥2 Amber, else Green; escalates Green→Amber if I &gt; 0.30.",
      abstain: "no evidence-source components are available (returns an Amber 'Insufficient signal data' stub rather than the standard insufficient-data flag).",
      sources: "Consumes existing Cat 1 EVM/CUSUM/Doc Risk and Cat 1.1 Monte Carlo outputs.",
      interp: "High indeterminacy (&gt;30%) triggers an automatic upgrade from Green to Amber, the module treats 'we genuinely don't know' as a governance-relevant state in its own right, distinct from 'we know it's fine' or 'we know it's a problem'.",
      ground: "Neutrosophic Logic (Smarandache, 1995) generalises fuzzy and intuitionistic logic by treating indeterminacy as an independent axis, T+I+F need not sum to 1, capturing epistemic uncertainty that classical and fuzzy frameworks force into the residual of truth and falsity." },
    { n: "7.4", name: "Interval Fuzzy Sets", mc: "Interval_Fuzzy_Sets",
      purpose: "Propagates realistic input-measurement uncertainty (±2% on EV from Schedule-of-Values accuracy, ±1% on AC from pay-app rounding) through the fuzzy classification, producing an interval rather than a point membership.",
      formula: "CPI/SPI uncertainty range ±3 percentage points; piecewise Green/Amber/Red membership functions evaluated at both interval endpoints; state intervals aggregated by element-wise max across sources; status = state with the highest interval midpoint.",
      bands: [["green","Low (&lt; 0.15)","input precision sufficient for reliable classification"], ["amber","Moderate (0.15-0.30)","boundary classification may shift with better data"], ["red","High (&gt; 0.30)","input noise could change the classification"]],
      abstain: "no CPI/SPI intervals are available (returns an Amber 'Insufficient signal data' stub).",
      sources: "Pay Application (AC rounding), Schedule of Values (EV line-item accuracy).",
      interp: "A wide uncertainty width means a Green/Amber boundary crossing is within reach of ordinary measurement noise; the practical response is to request more precise source documents (a verified pay app rather than an estimate), not to escalate on the classification alone.",
      ground: "Interval-valued fuzzy sets (Sambuc, 1975; Zadeh, 1975; Turksen, 1986) represent membership as a range rather than a point, explicitly modelling measurement uncertainty rather than assuming perfectly precise inputs." },
    { n: "7.5", name: "Z-numbers", mc: "Z_Numbers",
      purpose: "Pairs each evidence source's classification (the restriction) with a fixed reliability weight for that source type (the reliability), so a verified pay-application-derived signal carries more weight than a less-reliable proxy source.",
      formula: "Fixed source reliabilities: EVM 0.85, CUSUM 0.90, Document Risk 0.65, Monte Carlo forecast 0.88. Reliability-weighted totals accumulate per bucket; status = the bucket with the highest total reliability-weighted mass.",
      abstain: "no signals are available (returns an Amber 'Insufficient signal data' stub).",
      sources: "Consumes existing Cat 1 EVM/CUSUM/Doc Risk and Cat 1.1 Monte Carlo outputs.",
      interp: "Because document risk carries the lowest fixed reliability (0.65) of the four sources, a Red from Cat 1.3 alone is weighted less heavily here than an equivalent Red from CUSUM (0.90); this is a deliberate check against over-weighting the least-verified signal class.",
      ground: "The Z-number (Zadeh, 2011) is a pair (restriction, reliability) explicitly separating what a signal says from how much to trust it, letting the governance layer discount lower-reliability sources rather than treating every signal as equally trustworthy." },
    { n: "7.6", name: "PLTS", mc: "PLTS",
      purpose: "Represents each evidence source as a full probability distribution over {Green, Amber, Red} rather than a single crisp label, then averages those distributions across sources.",
      formula: "Each source is mapped through a 6-band lookup table into a {Green, Amber, Red} probability triple; the four sources' triples are simple-averaged; status = argmax of the averaged triple.",
      abstain: "no source distributions are available (returns an Amber stub with p_green:33, p_amber:34, p_red:33).",
      sources: "Consumes existing Cat 1 EVM/CUSUM/Doc Risk and Cat 1.1 Monte Carlo outputs.",
      interp: "The reported probability triple (not just the winning label) shows how close a call was, e.g. 40/35/25 Green/Amber/Red is a genuinely different situation from 90/8/2 even though both round to the same 'Green' headline status.",
      ground: "Probabilistic Linguistic Term Sets (Pang, Wang &amp; Xu, 2016) let an evaluator express a judgment as a distribution over linguistic terms rather than committing to one, appropriate for evidence that is not cleanly binary." },
    { n: "7.7", name: "Plithogenic Sets", mc: "Plithogenic_Sets",
      purpose: "Weights each evidence attribute by both its membership degree and an explicit contradiction degree, so attributes that contradict the dominant classification are down-weighted rather than simply averaged in.",
      formula: "Each attribute's weight = membership × (1 − contradiction × 0.5); weighted scores accumulate per bucket; status = argmax bucket; avgContradiction is reported as its own metric.",
      bands: [["green","Low (&lt; 0.30)","attributes are broadly consistent"], ["amber","Moderate (0.30-0.60)","some attributes pull against the classification"], ["red","High (&gt; 0.60)","the evidence set is internally contradictory"]],
      abstain: "no evidence attributes are available (returns an Amber 'Insufficient signal data' stub).",
      sources: "Consumes existing Cat 1 EVM/CUSUM/Doc Risk and Cat 1.1 Monte Carlo outputs.",
      interp: "A high contradiction level is a distinct finding from a high Red mass: it means the sources are not just disagreeing on the verdict but structurally pulling in opposite directions, worth investigating why before acting on the majority classification alone.",
      ground: "Plithogenic Sets (Smarandache, 2018) generalise crisp, fuzzy, intuitionistic, and neutrosophic sets by attaching an explicit contradiction degree to each attribute relative to a dominant attribute value." },
    { n: "7.8", name: "Belief Rule Base", mc: "Belief_Rule_Base",
      purpose: "Applies eight fixed, explicit IF-THEN governance rules matched against the current EVM state, CUSUM breach status, and document-risk state, then combines the belief distributions of every matching rule.",
      formula: "8 rules (R1-R8), each a fixed belief distribution over {Green,Amber,Red} with an associated weight, matched by condition; matched rules combine via weighted average: aggregate = Σ(belief × weight) / Σweight; status = argmax of the aggregate.",
      sources: "Consumes existing Cat 1 EVM/CUSUM/Doc Risk and Cat 1.1 Monte Carlo outputs.",
      interp: "Because the rules are fixed and enumerable (not learned from data), every classification this module produces traces back to a specific, readable IF-THEN rule, the same auditability principle that governs decision.js's escalation logic elsewhere in PCEIF.",
      ground: "The Belief Rule Base methodology (Yang, Liu, Wang, Sii &amp; Wang, 2006) combines expert-authored IF-THEN rules with Dempster-Shafer-style belief distributions, an interpretable alternative to a learned (black-box) classifier for the same evidence-combination task." },
    { n: "7.9", name: "Quantum Probability", mc: "Quantum_Probability",
      purpose: "Models the possibility that evidence sources interfere constructively or destructively with each other (rather than combining additively), capturing a form of correlation that classical probability combination misses.",
      formula: "alpha_green = sqrt(mean(pGreen across sources)); gamma_red = sqrt(mean(pRed across sources)); theta = (|redCount − greenCount|/3) × π; interference = 2 × alpha_green × gamma_red × cos(theta); P_red_q and P_green_q adjusted by ±0.3×interference and clamped.",
      sources: "Consumes existing Cat 1 EVM/CUSUM/Doc Risk outputs.",
      interp: "'Constructive interference' (cos θ &gt; 0.3) means aligned signals reinforce each other more than a simple average would predict; 'destructive interference' (cos θ &lt; −0.3) means opposing signals cancel more than expected, worth noting when the classical Cat 6.1/7.1 read looks marginal.",
      ground: "Quantum probability theory applied to cognition and decision-making (Busemeyer &amp; Bruza, 2012) allows for interference effects between correlated judgments that violate classical probability's additivity assumption, an exploratory cross-check rather than a primary governance signal." },
    { n: "7.10", name: "Pythagorean Fuzzy Sets", mc: "Pythagorean_Fuzzy",
      purpose: "Represents the evidence as a (membership, non-membership) pair constrained by μ² + ν² ≤ 1 (rather than fuzzy logic's simpler μ + ν ≤ 1), giving more room to express both positive and negative evidence simultaneously, then discounts membership by document risk.",
      formula: "μ_g = clamp((min(CPI,SPI) − 0.85)/0.15, 0, 1); ν_g = clamp((0.95 − min(CPI,SPI))/0.15, 0, 1), renormalised if μ²+ν²&gt;1; adjustedμ = μ_g×(1 − docRisk×0.3); adjustedν = min(1, ν_g + docRisk×0.3); score = adjustedμ − adjustedν.",
      bands: [["green","Green","score ≥ 0.3"], ["yellow","Yellow","0.0-0.3"], ["amber","Amber","−0.3 to 0.0"], ["red","Red","&lt; −0.3"]],
      abstain: "cpi, spi or docRiskScore missing.",
      sources: "Pay Application, Schedule of Values, RFI / RFI Log (for document risk).",
      interp: "The hesitancy term (π, the leftover 'unassigned' mass) reported alongside membership/non-membership quantifies how much of the judgment remains genuinely uncommitted, distinct from Cat 7.4's measurement-uncertainty interval.",
      ground: "Pythagorean Fuzzy Sets (Yager, 2013) relax the intuitionistic-fuzzy constraint from μ+ν≤1 to μ²+ν²≤1, allowing a wider, more expressive combination of simultaneous positive and negative evidence." },
    { n: "7.11", name: "Picture Fuzzy Sets", mc: "Picture_Fuzzy",
      purpose: "Extends fuzzy evaluation to four components, positive, neutral, negative, and refusal, modelling abstention (a source declining to commit) as its own explicit category rather than as residual uncertainty.",
      formula: "positive = clamp((evmMin−0.85)/0.15, 0, 0.95); negative = clamp((0.95−evmMin)/0.15, 0, 0.95) × (1 + docRisk×0.5), clamped 0.95; neutral = max(0, 0.6−positive−negative)×0.3; refusal = max(0, 1−positive−neutral−negative); score = positive − negative.",
      bands: [["green","Green","score ≥ 0.30"], ["yellow","Yellow","0.00-0.30"], ["amber","Amber","−0.30 to 0.00"], ["red","Red","&lt; −0.30"]],
      abstain: "cpi, spi or docRiskScore missing.",
      sources: "Pay Application, Schedule of Values, RFI / RFI Log.",
      interp: "A high refusal component means the evidence genuinely does not commit to a clear read in any direction, distinct from a high neutral component (evidence that is actively lukewarm); the evidence string reports all four components so the reviewer can tell which case applies.",
      ground: "Picture Fuzzy Sets (Cuong, 2014) add a 'neutral' and a 'refusal' degree to the standard positive/negative fuzzy pair, useful for modelling voting-style or committee-style evaluations where abstention is a distinct outcome from a lukewarm rating." },
    { n: "7.12", name: "Hesitant Fuzzy Sets", mc: "Hesitant_Fuzzy",
      purpose: "Instead of forcing a single membership value, evaluates three plausible membership readings (from the min, max, and average of CPI/SPI) and reports both their average and the spread between them as an explicit hesitancy measure.",
      formula: "memberships = [f(min(CPI,SPI)), f(max(CPI,SPI)), f(avg(CPI,SPI))] where f(x) = clamp((x−0.85)/0.15, 0, 1); score = mean(memberships); hesitancy = max(memberships) − min(memberships).",
      bands: [["green","Green","score ≥ 0.7"], ["yellow","Yellow","0.5-0.7"], ["amber","Amber","0.3-0.5"], ["red","Red","&lt; 0.3"]],
      abstain: "cpi or spi missing.",
      sources: "Pay Application, Schedule of Values.",
      interp: "High hesitancy means CPI and SPI point in noticeably different directions, so the single composite score is masking a real cost/schedule split; check CPI and SPI individually rather than reading the composite alone when hesitancy is elevated.",
      ground: "Hesitant Fuzzy Sets (Torra, 2010) allow an evaluator to consider several plausible membership values simultaneously rather than committing to one, modelling genuine hesitation between multiple reasonable readings of the same evidence." },
    { n: "7.13", name: "Type-2 Fuzzy Sets", mc: "Type2_Fuzzy",
      purpose: "Fuzzy-membership itself carries uncertainty here: a lower and an upper membership bound (a footprint of uncertainty) are computed, driven by how far CPI and SPI diverge from each other.",
      formula: "primaryMembership = clamp((min(CPI,SPI)−0.85)/0.15, 0, 1); uncertainty = |CPI−SPI| × 2; lower = max(0, primary−uncertainty×0.5); upper = min(1, primary+uncertainty×0.5); centroid = (lower+upper)/2; footprint = upper−lower.",
      bands: [["green","Green","centroid ≥ 0.7 AND footprint ≤ 0.2"], ["yellow","Yellow","centroid ≥ 0.5"], ["amber","Amber","centroid ≥ 0.3"], ["red","Red","centroid &lt; 0.3"]],
      abstain: "cpi or spi missing.",
      sources: "Pay Application, Schedule of Values.",
      interp: "Green requires BOTH a high centroid AND a narrow footprint (uncertainty band); a project with a high centroid but a wide footprint (because CPI and SPI disagree sharply) will not read Green here even though a simpler single-value fuzzy read might.",
      ground: "Type-2 Fuzzy Sets (Mendel &amp; John, 2002) model uncertainty about the membership function itself (a 'fuzzy fuzzy set'), useful when the inputs feeding the membership calculation (here, CPI vs SPI) disagree with each other." },
    { n: "7.14", name: "Maximum Entropy", mc: "Maximum_Entropy",
      purpose: "Reports a full probability distribution over all four states (Green/Yellow/Amber/Red) alongside a normalised entropy score measuring how spread-out (uncertain) that distribution is.",
      formula: "Raw probabilities looked up from a fixed table keyed on min(CPI,SPI) band, adjusted upward on Amber/Red by document risk, renormalised; entropy = −Σp×log2(p); normalizedEntropy = entropy / log2(4); status = the state with the highest probability.",
      abstain: "cpi, spi or docRiskScore missing.",
      sources: "Pay Application, Schedule of Values, RFI / RFI Log.",
      interp: "A high normalised entropy (probability mass spread relatively evenly across states) means the classification is genuinely uncertain even if one state narrowly wins the plurality; a low entropy means the dominant state is a confident read.",
      ground: "The Maximum Entropy principle (Jaynes, 1957) selects the probability distribution consistent with known constraints that is otherwise maximally non-committal, i.e. the distribution that assumes the least beyond what the evidence actually supports, and reports its own uncertainty explicitly via the entropy measure." },
    { n: "7.15", name: "Possibility Theory", mc: "Possibility_Theory",
      purpose: "Reports both a possibility (how plausible is this state, an upper bound) and a necessity (how certain is this state, a lower bound) for each of Green/Amber/Red, distinguishing 'this could be true' from 'this must be true'.",
      formula: "possibility.Green/Amber/Red each computed from evmMin and docRisk via fixed piecewise formulas; necessity.X = max(0, possibility.X − 0.3); status = the state with the highest possibility.",
      abstain: "cpi, spi or docRiskScore missing.",
      sources: "Pay Application, Schedule of Values, RFI / RFI Log.",
      interp: "A state can have high possibility but low (or zero) necessity, meaning the evidence does not rule it out but also does not confirm it; only a state with both high possibility and non-trivial necessity is a genuinely confident read.",
      ground: "Possibility Theory (Dubois &amp; Prade, 1988) is a non-additive alternative to probability theory that separately tracks an upper bound (possibility) and a lower bound (necessity) on how well evidence supports a proposition, well-suited to evidence that is incomplete rather than merely random." },
    { n: "7.16", name: "Spherical Fuzzy Sets", mc: "Spherical_Fuzzy",
      purpose: "A three-dimensional generalisation of Pythagorean fuzzy sets (μ² + ν² + π² ≤ 1), giving even more room to express membership, non-membership, and hesitancy independently before any constraint binds.",
      formula: "μ = clamp((evmMin−0.82)/0.18, 0, 0.95); ν = clamp((0.98−evmMin)/0.18, 0, 0.95) × (1+docRisk×0.5), clamped 0.95; renormalised if μ²+ν²&gt;1; π = sqrt(max(0, 1−μ²−ν²)); score = μ−ν.",
      bands: [["green","Green","score ≥ 0.4"], ["yellow","Yellow","0.1-0.4"], ["amber","Amber","−0.2 to 0.1"], ["red","Red","&lt; −0.2"]],
      abstain: "cpi, spi or docRiskScore missing.",
      sources: "Pay Application, Schedule of Values, RFI / RFI Log.",
      interp: "The wider bands here relative to Cat 7.10 (Pythagorean) reflect the extra degree of freedom in the spherical constraint; treat this and Cat 7.10 as two related but not identical cross-checks rather than duplicates.",
      ground: "Spherical Fuzzy Sets (Kutlu Gündoğdu &amp; Kahraman, 2019) extend Pythagorean fuzzy sets to a three-term constraint (membership, non-membership, hesitancy), developed specifically for multi-criteria decision-making applications like TOPSIS-style ranking." },
    { n: "7.17", name: "Fermatean Fuzzy Sets", mc: "Fermatean_Fuzzy",
      purpose: "A further generalisation using a cubic constraint (μ³ + ν³ ≤ 1), giving the most room of the three fuzzy-set generalisations in this stack (Pythagorean, Spherical, Fermatean) to express strong simultaneous membership and non-membership.",
      formula: "μ = clamp((evmMin−0.80)/0.20, 0, 0.99); ν = clamp((1.00−evmMin)/0.20, 0, 0.99); if μ³+ν³&gt;1, both scaled down by 0.95 iteratively; score = μ − ν.",
      bands: [["green","Green","score ≥ 0.35"], ["yellow","Yellow","0.05-0.35"], ["amber","Amber","−0.25 to 0.05"], ["red","Red","&lt; −0.25"]],
      abstain: "cpi or spi missing.",
      sources: "Pay Application, Schedule of Values.",
      interp: "This is the least document-risk-sensitive of the three related generalisations (it does not factor docRiskScore into ν at all, unlike Cat 7.10/7.16), so read it as a pure EVM-based cross-check rather than a document-risk-adjusted one.",
      ground: "Fermatean Fuzzy Sets (Senapati &amp; Yager, 2020) extend the Pythagorean/Spherical family with a cubic constraint, allowing an even wider simultaneous expression of positive and negative evidence before the constraint binds." },
    { n: "7.18", name: "MARCOS Ranking", mc: "MARCOS",
      purpose: "A multi-criteria decision-making (MCDM) method that ranks the project's evidence state by its utility relative to both an ideal (best-case) and an anti-ideal (worst-case) reference point simultaneously.",
      formula: "Three weighted criteria (CPI w=0.40, SPI w=0.35, 1−docRiskScore w=0.25) each normalised against ideal/anti-ideal reference values; utilityIdeal = Σ(normalised value × weight); f_ideal and f_anti derived from utilityIdeal/Anti; marcosScore combines both via the MARCOS utility-function formula.",
      bands: [["green","Green","score ≥ 0.65"], ["yellow","Yellow","0.50-0.65"], ["amber","Amber","0.35-0.50"], ["red","Red","&lt; 0.35"]],
      abstain: "cpi, spi or docRiskScore missing.",
      sources: "Pay Application, Schedule of Values, RFI / RFI Log.",
      interp: "MARCOS explicitly compares distance from both the best-case and worst-case anchor, so a mid-range MARCOS score means the project is genuinely between the two references, not simply an average of unrelated criteria.",
      ground: "MARCOS (Measurement Alternatives and Ranking according to Compromise Solution; Stević, Pamučar, Puška &amp; Chatterjee, 2020) is a recent multi-criteria ranking method that anchors alternatives against both ideal and anti-ideal reference solutions simultaneously." },
    { n: "7.19", name: "CRITIC-TOPSIS", mc: "CRITIC_TOPSIS",
      purpose: "Combines CRITIC (objective, data-driven criteria weighting) with TOPSIS (ranking by distance from ideal and anti-ideal solutions), so criteria weights are derived from the data itself rather than fixed a priori.",
      formula: "CRITIC weights derived from each criterion's deviation from the mean, normalised to sum to 1; Euclidean distances to a fixed ideal [1.05, 1.05, 1.00] and anti-ideal [0.80, 0.80, 0.30] vector computed with those weights; topsisScore = distance-to-anti-ideal / (distance-to-ideal + distance-to-anti-ideal).",
      bands: [["green","Green","score ≥ 0.65"], ["yellow","Yellow","0.50-0.65"], ["amber","Amber","0.35-0.50"], ["red","Red","&lt; 0.35"]],
      abstain: "cpi, spi or docRiskScore missing.",
      sources: "Pay Application, Schedule of Values, RFI / RFI Log.",
      interp: "Unlike Cat 7.18's fixed weights, this module's CRITIC weighting means the criterion currently varying most from its typical value gets the most influence on the score this period, worth noting when interpreting which input is driving the result.",
      ground: "CRITIC weighting (Diakoulaki, Mavrotas &amp; Papayannakis, 1995) derives objective criteria weights from the data's own variability; TOPSIS (Hwang &amp; Yoon, 1981) ranks alternatives by their relative closeness to an ideal solution, combining the two removes the need for a priori fixed weights." },
    { n: "7.20", name: "Hypersoft Sets", mc: "Hypersoft_Sets",
      purpose: "Classifies the project by matching a categorical combination of attributes (cost quality, schedule quality, risk level) against a fixed lookup table of pre-scored combinations, a fundamentally discrete, rule-table approach distinct from the continuous fuzzy methods elsewhere in Cat 7.",
      formula: "Three categorical attributes derived from thresholds (cost/schedule: poor/fair/good from CPI/SPI bands; risk: low/medium/high from docRiskScore bands); the combined key looks up a score in a fixed 24-entry combination table (default 0.35 if the exact combination is not tabulated).",
      bands: [["green","Green","score ≥ 0.70"], ["yellow","Yellow","0.50-0.70"], ["amber","Amber","0.30-0.50"], ["red","Red","&lt; 0.30"]],
      abstain: "cpi, spi or docRiskScore missing.",
      sources: "Pay Application, Schedule of Values, RFI / RFI Log.",
      interp: "Because this method is table-driven rather than continuous, it is the most directly auditable of the 20 Cat 7 methods, every possible combination and its score can be read straight from the lookup table, no formula to unwind.",
      ground: "Hypersoft Sets (Smarandache, 2018) generalise Soft Set theory by allowing multiple independent attribute dimensions (rather than a single parameter set), matched here against an explicit, enumerable scoring table rather than a continuous function." }
  ];

  /* ---------- Cat 8, Governance & Compliance (8.1-8.9) ---------- */
  const CAT8_MODULES = [
    { n: "8.1", name: "ABM Governance Layer", mc: "ABM_Governance",
      purpose: "Converts the fused signal state into the named authority, recommended action, and required documentation, the last step in the stack, the artefact that survives the reporting cycle.",
      formula: "Each authority role (PM, controls lead, program director) is modelled as an agent with explicit decision rules implemented as pure functions (deriveHealthState, classifyConflict, deriveDecision) in decision.js, consuming the Cat 6.1 baseline and Cat 7 evidence-combination cross-checks. Runs in decision.js, not simulations.js.",
      sources: "Consumes every already-computed module's output; no independent document extraction of its own.",
      interp: "This module's output IS the decision card the PM sees; a status change here is not itself a decision, a decision requires a named human, a role, a rationale, and a timestamp before it is recorded.",
      ground: "Agent-based governance modelling (Bonabeau, 2002) assigns explicit decision rules to distinct authority roles; here those rules are deliberately implemented as readable functions rather than a learned model, so every recommendation is traceable to an inspectable rule." },
    { n: "8.2", name: "FAR Threshold Monitor", mc: "FAR_Threshold",
      purpose: "Tracks projected cost overrun against the FAR Part 34 25% reporting threshold used on federal capital programs, converting a percentage into a specific reporting obligation.",
      formula: "eac = BAC/CPI; overrunPct = ((eac−BAC)/BAC) × 100; far34Threshold = 25%; distanceToThreshold = 25 − overrunPct.",
      bands: [["green","Green","overrun ≤ 5%"], ["yellow","Yellow","5-15%"], ["amber","Amber","15-25%"], ["red","Red","≥ 25% (FAR reporting required)"]],
      abstain: "bac, cpi, ev or ac missing.",
      sources: "Pay Application, Schedule of Values, Cost Report.",
      interp: "distanceToThreshold in the evidence string tells the PM exactly how much headroom remains before mandatory FAR reporting is triggered, a specific number for a specific regulatory conversation, not just a status color.",
      ground: "FAR Part 34 (Federal Acquisition Regulation, Major System Acquisition) sets a 25% cost-growth threshold that triggers formal reporting obligations on federal capital programs; this module encodes that specific regulatory threshold directly." },
    { n: "8.3", name: "OMB A-11 Check", mc: "OMB_A11_Check",
      purpose: "Flags whether a major program (BAC ≥ $10M) with CPI below 0.90 has crossed the mandatory-reporting condition under OMB Circular A-11 guidance for federal capital investments.",
      formula: "cpiBelow90 = CPI &lt; 0.90; majorProgram = BAC ≥ $10,000,000; reportingTriggered = both true simultaneously.",
      bands: [["green","Green","CPI ≥ 0.90"], ["yellow","Yellow","0.92 ≤ CPI &lt; ... (see amber)"], ["amber","Amber","0.88 ≤ CPI &lt; 0.92"], ["red","Red","CPI &lt; 0.88, or reporting triggered"]],
      abstain: "bac, cpi or actualPctComplete missing.",
      sources: "Pay Application, Schedule of Values, Cost Report.",
      interp: "'MANDATORY REPORTING TRIGGERED' in the evidence string means both conditions (major-program size AND CPI breach) are simultaneously true; a smaller program with the same CPI shortfall does not carry the same OMB reporting obligation.",
      ground: "OMB Circular A-11 establishes reporting and review requirements for major federal capital investments; this module encodes the size and cost-performance conditions that jointly trigger that reporting obligation." },
    { n: "8.4", name: "EVM Reporting Threshold", mc: "EVM_Reporting_Threshold",
      purpose: "Checks whether CPI and/or SPI have individually breached the standard 0.90 reporting threshold, distinguishing a single-metric breach from a joint cost-and-schedule breach.",
      formula: "cpiBreached = CPI &lt; 0.90; spiBreached = SPI &lt; 0.90; bothBreached = both; eacDeltaPct computed from BAC/CPI.",
      bands: [["green","Green","neither breached"], ["yellow","Yellow","exactly one of CPI/SPI breached"], ["amber","Amber","both breached AND EAC delta ≤ 15%"], ["red","Red","both breached AND EAC delta &gt; 15%"]],
      abstain: "bac, cpi or spi missing.",
      sources: "Pay Application, Schedule of Values.",
      interp: "A joint cost-and-schedule breach (both true) reads more severely than either alone even at the same individual CPI/SPI value, because a single-dimension shortfall is more often recoverable than a compounding cost-and-schedule problem.",
      ground: "The 0.90 CPI/SPI threshold is a widely used industry rule-of-thumb reporting trigger in EVM practice (consistent with the PMI EVM standard's guidance on significant-variance reporting); joint-breach escalation reflects that simultaneous cost and schedule shortfalls compound risk." },
    { n: "8.5", name: "Contract Modification Frequency", mc: "Contract_Mod_Frequency",
      purpose: "The Cat 8 governance-compliance reading of change-order activity, distinct from Cat 4.6's document-risk framing: here the question is whether modification frequency merits contracting-officer review.",
      formula: "scopeGrowthPct computed identically to Cat 4.6; riskLevel = Red if changeOrderCount ≥10 OR scopeGrowth ≥20%; Amber if ≥6 OR ≥10%; Yellow if ≥3 OR ≥5%; else Green.",
      abstain: "changeOrderCount, baselineContractSum or revisedContractSum missing.",
      sources: "Change Order / PCO; estimated when the log is unavailable, flagged '[est.]'.",
      interp: "Red here specifically means 'contracting officer review merits consideration' per the evidence string, a specific compliance/authority action distinct from Cat 4.6's scope-stability framing of the same underlying data.",
      ground: "Contract modification frequency thresholds reflect standard federal/public contracting-officer review triggers for cumulative modification activity on a fixed-price or unit-price public works contract." },
    { n: "8.6", name: "Quality Compliance Index", mc: "Quality_Compliance",
      purpose: "Converts quality-audit inspection results (or, absent an audit, a proxy from noted deficiencies) into a single compliance score comparable across projects.",
      formula: "passRate = (itemsInspected − itemsFailed)/itemsInspected; auditScore = qualityAuditScore if supplied, else passRate × 100.",
      bands: [["green","Green","≥ 85/100"], ["yellow","Yellow","70-84"], ["amber","Amber","55-69"], ["red","Red","&lt; 55"]],
      abstain: "qualityDeficienciesNoted missing.",
      sources: "Quality Audit Report; estimated from field observations when unavailable, flagged '[est.]'.",
      interp: "When qualityAuditScore is directly supplied it should be treated as more reliable than the passRate proxy; check the evidence string for '[est.]' to know which case applies before treating the score as a formal audit result.",
      ground: "Pass-rate-based quality scoring against a fixed inspection sample is standard construction-quality-management practice, converting raw deficiency counts into a comparable percentage metric across projects of different sizes." },
    { n: "8.7", name: "Safety Performance Index", mc: "Safety_Performance",
      purpose: "Benchmarks the project's incident rate (from OSHA data when available, otherwise a proxy from OAC-minutes safety mentions) against a fixed industry benchmark (construction/hybrid sectors only).",
      formula: "incidentRate = oshaIncidentRate if supplied, else safetyIncidentsDiscussed × 10 (proxy); industryBenchmark = 3.0; safetyIndex = min(2, benchmark/incidentRate).",
      bands: [["green","Green","incidentRate ≤ 3.0 (benchmark)"], ["yellow","Yellow","≤ 6.0 (2x benchmark)"], ["amber","Amber","≤ 15.0 (5x benchmark)"], ["red","Red","&gt; 15.0"]],
      abstain: "safetyIncidentsDiscussed missing.",
      sources: "Safety Report (OSHA incident rate preferred); OAC Meeting Minutes proxy when unavailable, flagged '[est.]'.",
      interp: "The proxy (10x the OAC-mentions count) is a much coarser signal than a real OSHA rate; treat a proxy-derived Red as a prompt to obtain the actual Safety Report before escalating on the estimated figure alone.",
      ground: "OSHA recordable incident rate benchmarking against an industry-standard reference rate is the standard safety-performance metric in U.S. construction safety management." },
    { n: "8.8", name: "Environmental Compliance Rate", mc: "Environmental_Compliance",
      purpose: "Tracks permit and environmental-compliance performance, from a directly reported compliance rate when available, otherwise a proxy from OAC-minutes issue mentions (construction/hybrid sectors only).",
      formula: "complianceRate = environmentalComplianceRate if supplied, else max(50, 100 − environmentalIssuesDiscussed × 5), clamped to 100.",
      bands: [["green","Green","≥ 95%"], ["yellow","Yellow","85-94%"], ["amber","Amber","70-84%"], ["red","Red","&lt; 70%"]],
      abstain: "environmentalIssuesDiscussed missing.",
      sources: "Environmental Compliance Report (preferred); OAC Meeting Minutes proxy when unavailable, flagged '[est.]'.",
      interp: "Any recorded environmentalViolations count is surfaced directly in the evidence string alongside the rate, a formal violation should be treated as materially more significant than a compliance-rate dip alone, regardless of the numeric band.",
      ground: "Environmental permit compliance-rate tracking is standard practice for public capital programs subject to NEPA and related environmental review requirements, where violations carry direct regulatory and funding consequences." },
    { n: "8.9", name: "Contractor Performance Score", mc: "Contractor_Performance",
      purpose: "Takes the worst of three separately rated dimensions (overall, schedule, cost), rather than an average, so one weak dimension cannot be masked by two strong ones.",
      formula: "minRating = min(overallRating, scheduleRating, costRating), each on a 1-5 scale.",
      bands: [["green","Green","≥ 4.0"], ["yellow","Yellow","3.5-3.9"], ["amber","Amber","3.0-3.4"], ["red","Red","&lt; 3.0"]],
      abstain: "overallRating, scheduleRating or costRating missing.",
      sources: "Past Performance Report, Subcontractor Performance Report.",
      interp: "Because this is a worst-of-three, not an average, a contractor with excellent cost and overall ratings but a weak schedule rating will still read Amber/Red here, ensuring a single weak dimension is not diluted away by the other two.",
      ground: "Contractor Performance Assessment Reporting System (CPARS)-style multi-dimension rating, taking the minimum across dimensions rather than an average, reflects standard federal past-performance evaluation practice where any single failing dimension is independently disqualifying." }
  ];

  /* ---------- Cat 9, Data Integrity & Information Quality (9.1-9.7) ---------- */
  const CAT9_MODULES = [
    { n: "9.1", name: "Missing Data Index", mc: "Missing_Data_Index",
      purpose: "Counts how many of the 11 core signal fields (bac, ev, ac, pv, cpi, spi, docRiskScore, actualPctComplete, plannedPctComplete, baselineStart, baselineEnd) are populated at all.",
      formula: "missingRatio = 1 − (present fields / 11).",
      bands: [["green","Green","missing ratio ≤ 10%"], ["yellow","Yellow","10-25%"], ["amber","Amber","25-45%"], ["red","Red","&gt; 45%"]],
      sources: "Every core document type the other 9 categories depend on; this module never abstains, it always computes against whatever is present.",
      interp: "A Red here means the entire downstream analytical stack, all 103 modules, is resting on a badly incomplete input set; every other module's status should be read with correspondingly lower confidence until this improves.",
      ground: "Field-completeness auditing against a fixed core-schema checklist is standard data-quality practice, applied here to make an otherwise invisible input-quality problem an explicit, first-class governance signal." },
    { n: "9.2", name: "Data Timeliness Score", mc: "Data_Timeliness_Score",
      purpose: "Measures how stale the most recently uploaded document is, since signals computed from month-old data may no longer reflect current project conditions.",
      formula: "daysSinceDoc = today − most recent docDate.",
      bands: [["green","Green","≤ 30 days"], ["yellow","Yellow","30-60 days"], ["amber","Amber","60-90 days"], ["red","Red","&gt; 90 days"]],
      abstain: "no docDate is available at all.",
      sources: "Any uploaded document, this module reads the most recent document date across all types.",
      interp: "A Red or Amber here is a caution flag on every other module's currency, not just this one; a governance recommendation built on 90-day-old data should be treated as provisional until fresher documents are uploaded.",
      ground: "Data-timeliness / data-freshness scoring is a standard data-quality dimension (alongside completeness, accuracy, and consistency) in information-quality frameworks applied to decision-support systems." },
    { n: "9.3", name: "Source Reliability Weighting", mc: "Source_Reliability_Weighting",
      purpose: "Averages a fixed reliability weight per document type across every field the project's signals draw on, so the overall input quality reflects the mix of verified vs. estimated sources.",
      formula: "Fixed reliability weights (e.g. contract_value 0.95, pay_application 0.90, change_order 0.90, schedule_of_values 0.85, time_phased_schedule 0.80, monthly_report 0.75, inspection_report 0.70, rfi/submittal 0.65, field_report 0.60, oac_minutes 0.55, derived/estimated 0.40); avgReliability = mean across all populated fields' source weights.",
      bands: [["green","Green","≥ 0.80"], ["yellow","Yellow","0.65-0.79"], ["amber","Amber","0.50-0.64"], ["red","Red","&lt; 0.50"]],
      abstain: "no source metadata is recorded at all.",
      sources: "Every document type; this module reads the recorded provenance (docType) of each populated signal field, not the field values themselves.",
      interp: "The derivedCount reported alongside the average tells the PM specifically how many fields are estimated proxies rather than measured, uploading the specific missing document types would directly raise this score.",
      ground: "Source-reliability weighting by provenance is a standard data-fusion technique, treating a verified pay application and a derived estimate as different-quality inputs rather than interchangeable data points." },
    { n: "9.4", name: "Audit Trail Completeness", mc: "Audit_Trail_Completeness",
      purpose: "Checks whether the project's event log contains the required governance milestones (creation, signal extraction, and ideally a recorded decision), a structural completeness check independent of the signal values themselves.",
      formula: "completeness = presentRequiredEvents / 2 (project_created, signals_extracted/simulation_run); hasDecisionRecord checked separately.",
      bands: [["green","Green","completeness = 100% AND total events ≥ 3"], ["yellow","Yellow","completeness ≥ 75%"], ["amber","Amber","completeness ≥ 50%"], ["red","Red","completeness &lt; 50%"]],
      sources: "The project's own internal event log (project creation, document ingests, simulation runs, decision records), not an external document type.",
      interp: "A project with healthy signal statuses but no recorded decision event is flagged here even though the other 102 modules may look fine; a status change without a name, role, rationale, and timestamp attached is exactly what this module is designed to catch.",
      ground: "Audit-trail completeness checking against a required-event checklist is standard governance-record practice on public programs where every material status determination must be independently reconstructable from the record." },
    { n: "9.5", name: "Information Completeness Ratio", mc: "Information_Completeness_Ratio",
      purpose: "Distinguishes measured fields (from real documents) from estimated fields (derived proxies) across an 18-field checklist, a finer-grained companion to Cat 9.1's simple presence count.",
      formula: "For each of 18 fields: measured if populated and its source is not flagged 'derived'; estimated if populated but flagged 'derived'; missing otherwise. ratio = measured / 18.",
      bands: [["green","Green","≥ 75%"], ["yellow","Yellow","55-74%"], ["amber","Amber","35-54%"], ["red","Red","&lt; 35%"]],
      sources: "Every core and extended signal field's recorded provenance.",
      interp: "A project can look complete under Cat 9.1 (all fields present) yet score poorly here if most of those fields are estimated proxies rather than measured, this module is the sharper test of whether the completeness is real or derived.",
      ground: "Measured-versus-estimated field distinction follows the same information-quality principle as Cat 9.3, applied at field-count granularity rather than as a reliability average." },
    { n: "9.6", name: "Cross-document Consistency Score", mc: "Cross_Doc_Consistency",
      purpose: "Runs three internal-consistency checks (does the recorded CPI match EV/AC, does the recorded SPI match EV/PV, does percent-complete match EV/BAC) to catch figures across documents that do not reconcile with each other.",
      formula: "Three checks with tight tolerances (CPI/SPI derivation within 0.005, percent-complete within 5 points); consistencyScore = (checks passed) / (checks performed).",
      bands: [["green","Green","100% consistent"], ["yellow","Yellow","≥ 67%"], ["amber","Amber","≥ 33%"], ["red","Red","&lt; 33%"]],
      abstain: "ev or ac missing, or none of the three checks can be performed.",
      sources: "Pay Application, Schedule of Values, cross-checks whether the recorded CPI/SPI/percent-complete are internally consistent with the underlying EV/AC/PV/BAC figures.",
      interp: "Any inconsistency flagged here means the numbers feeding every other module do not reconcile internally, worth verifying the source figures across documents before trusting the derived CPI/SPI/percent-complete elsewhere in the stack.",
      ground: "Cross-document reconciliation checking (do the summary figures match the underlying source data) is a standard internal-controls technique for detecting transcription or reporting errors before they propagate into downstream analysis." },
    { n: "9.7", name: "Reporting Frequency Index", mc: "Reporting_Frequency_Index",
      purpose: "Measures the average interval between document-upload events, since infrequent updates mean the portfolio is making decisions on progressively staler data.",
      formula: "avgInterval = mean day-gap between consecutive document-extraction events in the project's event log.",
      bands: [["green","Green","≤ 14 days"], ["yellow","Yellow","≤ 30 days, or fewer than 2 uploads recorded"], ["amber","Amber","≤ 60 days"], ["red","Red","&gt; 60 days"]],
      sources: "The project's own internal event log; not an external document type.",
      interp: "This is the cadence read, distinct from Cat 9.2's single-point-in-time staleness read; a project can pass Cat 9.2 (recent upload) but still score poorly here if that recent upload was preceded by a long gap, an irregular reporting pattern rather than a chronically stale one.",
      ground: "Reporting-cadence tracking against an expected monthly (or more frequent) update cycle is standard program-controls discipline; PCEIF makes the interval itself an explicit, auditable signal rather than an assumed constant." }
  ];

  /* ---------- Cat 10, Decision Optimization (10.1-10.7) ---------- */
  const CAT10_MODULES = [
    { n: "10.1", name: "Multi-Objective Optimization", mc: "Multi_Objective_Optimization",
      purpose: "Normalises cost performance, schedule performance, and document risk onto a common 0-1 scale and identifies which objective is currently the binding constraint on the project's overall standing.",
      formula: "normCPI = clamp((CPI−0.80)/0.25, 0, 1); normSPI = clamp((SPI−0.80)/0.25, 0, 1); normRisk = 1 − docRiskScore; paretoScore = mean of the three; the lowest-scoring objective is reported as the binding constraint.",
      bands: [["green","Green","paretoScore ≥ 0.75"], ["yellow","Yellow","0.55-0.74"], ["amber","Amber","0.35-0.54"], ["red","Red","&lt; 0.35"]],
      abstain: "cpi, spi or docRiskScore missing.",
      sources: "Pay Application, Schedule of Values, RFI / RFI Log.",
      interp: "The named binding constraint tells the PM which objective to improve first for the largest overall gain, e.g. if document risk is the binding constraint, cost/schedule interventions will not move the composite score as much as addressing the document risk directly.",
      ground: "Multi-objective (Pareto) optimization formalises the trade-off between competing objectives, cost, schedule, and risk cannot all be independently maximised; naming the binding constraint operationalises the Pareto-frontier concept for a single-project read." },
    { n: "10.2", name: "Linear Programming", mc: "Linear_Programming",
      purpose: "Answers the direct feasibility question: given remaining work and remaining budget, is finishing within budget achievable, and at what required future CPI?",
      formula: "remainingWork = BAC − EV; remainingBudget = BAC − AC; requiredCPI = remainingWork / remainingBudget. If remainingBudget ≤ 0, the module reports Red directly, no feasible solution.",
      bands: [["green","Green","requiredCPI ≤ 1.00 (achievable at current performance)"], ["yellow","Yellow","≤ 1.05"], ["amber","Amber","≤ 1.15"], ["red","Red","&gt; 1.15, or budget exhausted"]],
      abstain: "bac, ev, ac or cpi missing.",
      sources: "Pay Application, Schedule of Values, Cost Report.",
      interp: "requiredCPI is the credibility test: if the project has never sustained that efficiency level in its own history (compare against Cat 1.6 ARIMA or Cat 1.11 Regression to Mean), budget completion is not a realistic assumption without a scope, schedule, or funding change.",
      ground: "Linear programming (Dantzig, 1963) is the standard framework for feasibility analysis under linear constraints; this module applies its core feasibility-test logic (is a solution within the given budget constraint even possible) in closed form rather than a full LP solve." },
    { n: "10.3", name: "Constraint Satisfaction Analysis", mc: "Constraint_Satisfaction",
      purpose: "Checks the project against four fixed governance constraints (cost, schedule, document risk, FAR-adjacent overrun threshold) simultaneously and reports which specific ones are violated.",
      formula: "Four constraints: CPI ≥ 0.90; SPI ≥ 0.90; docRiskScore &lt; 0.70; CPI &gt; 0.80 (FAR-threshold proxy). satisfactionRate = satisfied / 4.",
      bands: [["green","Green","4 of 4 satisfied"], ["yellow","Yellow","3 of 4"], ["amber","Amber","2 of 4"], ["red","Red","≤ 1 of 4"]],
      abstain: "cpi, spi or bac missing.",
      sources: "Pay Application, Schedule of Values, RFI / RFI Log.",
      interp: "The evidence string names the specific violated constraints by name, giving the PM a direct checklist of exactly which governance conditions require a response, rather than a single aggregate score to unpack.",
      ground: "Constraint Satisfaction Problem (CSP) framing, checking multiple discrete conditions simultaneously and reporting exactly which fail, is standard practice for compliance-style governance checks where partial credit does not substitute for meeting a specific regulatory or policy threshold." },
    { n: "10.4", name: "What-If Scenario Matrix", mc: "WhatIf_Scenario_Matrix",
      purpose: "Projects four explicit named futures (Optimistic, Base, Pessimistic, Recovery) and reports the dollar range across them as a decision-uncertainty metric, similar in spirit to Cat 5.4 but framed around decision options rather than raw forecasts.",
      formula: "Optimistic: CPI recovers to 1.00; Base: current CPI continues; Pessimistic: CPI degrades 5%; Recovery: CPI improves 5%. Each scenario's EAC computed; scenarioRange = (Pessimistic EAC − Optimistic EAC)/BAC × 100.",
      bands: [["green","Green","range ≤ 5% of BAC"], ["yellow","Yellow","≤ 10%"], ["amber","Amber","≤ 20%"], ["red","Red","&gt; 20%"]],
      abstain: "bac, ev, ac, cpi or spi missing.",
      sources: "Pay Application, Schedule of Values, Cost Report.",
      interp: "A wide scenario range means the decision the PM faces this cycle is genuinely uncertain even before considering probability weights, useful context for how much confidence to attach to whichever single-point forecast (Cat 1.1, 1.4, 3.7) is being used for the funding conversation.",
      ground: "Named-scenario decision matrices are a standard decision-analysis technique for presenting a bounded range of plausible futures to a non-technical decision-maker without requiring them to interpret a full probability distribution." },
    { n: "10.5", name: "Decision Sensitivity Matrix", mc: "Decision_Sensitivity_Matrix",
      purpose: "Identifies which single input (cost, schedule, or document risk) would most change the governance recommendation if it shifted, directing verification effort to the highest-leverage variable, the Cat 10 counterpart to Cat 5.2's broader sensitivity analysis.",
      formula: "cpiImpact = |1−CPI| × 100; spiImpact = |1−SPI| × 100; riskImpact = docRiskScore × 50; ranked; topDriverPct = share of total impact.",
      bands: [["green","Green","top driver impact ≤ 3"], ["yellow","Yellow","3-7"], ["amber","Amber","7-12"], ["red","Red","&gt; 12"]],
      abstain: "cpi, spi or docRiskScore missing.",
      sources: "Pay Application, Schedule of Values, RFI / RFI Log.",
      interp: "If cost performance accounts for 70% of decision sensitivity, a small CPI change would materially change the governance recommendation, the PM should verify that input first, before spending equivalent effort double-checking the lower-weight drivers.",
      ground: "Decision sensitivity analysis (ranking which input variable most changes a downstream decision, not just a downstream forecast) directly operationalises Cat 5.2's sensitivity-analysis output for the specific purpose of prioritising verification effort ahead of a governance decision." },
    { n: "10.6", name: "Pareto Frontier Analysis", mc: "Pareto_Frontier",
      purpose: "Classifies the project's position relative to the cost/schedule/risk Pareto frontier: efficient (all objectives met), dominated (multiple objectives simultaneously failing), or requiring an explicit trade-off.",
      formula: "costOk = CPI ≥ 0.95; schedOk = SPI ≥ 0.95; riskOk = docRiskScore &lt; 0.30; dominated = !costOk AND !schedOk; paretoEfficient = all three OK; tradeoffRequired = costOk ≠ schedOk, or riskOk fails while either cost or schedule is OK.",
      bands: [["green","Green","Pareto-efficient (all three objectives met)"], ["yellow","Yellow","trade-off required (objectives partially conflict)"], ["amber","Amber","partial efficiency, not dominated"], ["red","Red","Pareto-dominated (cost AND schedule both failing)"]],
      abstain: "cpi, spi or docRiskScore missing.",
      sources: "Pay Application, Schedule of Values, RFI / RFI Log.",
      interp: "'Pareto-dominated' (Red) is a specific, stronger finding than a generic Red elsewhere in the stack: it means multiple objectives are simultaneously failing, a pattern consistent with systemic rather than isolated problems, and worth investigating for a common root cause.",
      ground: "Pareto efficiency (Pareto, 1906) is the standard multi-objective optimisation concept for a solution where no objective can be improved without worsening another; classifying a project as efficient, dominated, or in a trade-off zone directly applies that concept to the cost/schedule/risk objective set." },
    { n: "10.7", name: "Regret Minimization Index", mc: "Regret_Minimization",
      purpose: "Applies minimax-regret decision theory to choose between monitor/investigate/escalate under three weighted future states (improves/stable/worsens), then overrides the regret-minimising choice with a hard signal-state floor so a severe CPI/SPI reading cannot be smoothed away by the probability weighting.",
      formula: "Fixed regret matrix per decision × future-state combination; expectedRegret[decision] = Σ(regret × future-state probability); recommended = argmin(expectedRegret). Override: if CPI &lt; 0.88 or SPI &lt; 0.88 → forced to 'escalate'; else if CPI &lt; 0.95 or SPI &lt; 0.95 → forced to 'investigate'.",
      bands: [["green","Green","recommended = monitor"], ["amber","Amber","recommended = investigate"], ["red","Red","recommended = escalate"]],
      abstain: "cpi, spi or bac missing.",
      sources: "Pay Application, Schedule of Values.",
      interp: "The override logic means this module never lets the probability-weighted regret calculation alone recommend 'monitor' when CPI/SPI have breached hard thresholds, the decision-theoretic optimum is a floor, not a ceiling, on the escalation the governance layer will accept.",
      ground: "Minimax regret theory (Savage, 1951) chooses the action minimising the worst-case regret across possible future states, a decision rule specifically suited to genuine Knightian uncertainty about the future rather than a single point forecast; the hard override reflects that decision theory informs, but does not override, governance policy floors." }
  ];

  /* ---------- Portfolio Health (PH.1-PH.5), computed server-side via the
     portfolioanalyze endpoint (Code.gs, not present in this client-side repo);
     documentation here reflects the existing, already-accurate CAT8_TOPICS
     descriptions used elsewhere in this file, restructured into the same
     six-part format as the project-level modules for consistency. ---------- */
  const PH_MODULES = [
    { n: "PH.1", name: "Isolation Forest", mc: "Isolation_Forest",
      purpose: "Detects a project whose overall combination of signals is unusual relative to the rest of the portfolio, even when no individual module has crossed its own Red threshold.",
      formula: "Server-side (portfolioanalyze): computes the Mahalanobis distance from a project's signal vector (CPI, SPI, document risk, and related derived fields) to the portfolio centroid; high distance indicates an unusual combination of signals relative to the whole program.",
      abstain: "the portfolio has fewer than 3 projects (insufficient population for a meaningful centroid/covariance estimate).",
      sources: "Aggregates the already-computed signal vectors of every active project in the portfolio; not driven by a single project's documents.",
      interp: "A project can show moderate CPI and moderate SPI individually (nothing Red on its own project page) yet still register high here if that particular combination, together with elevated document risk, is unlike any other project in the program, worth a second look even on an otherwise Green project.",
      ground: "Isolation Forest (Liu, Ting &amp; Zhou, 2008) is an anomaly-detection method that isolates outliers by how few random partitions are needed to separate them from the rest of the data; Mahalanobis distance to the portfolio centroid is used here as the isolation-forest-style distance proxy." },
    { n: "PH.2", name: "Portfolio Outlier Detection", mc: "Portfolio_Outlier",
      purpose: "Ranks the project's CPI and SPI by percentile within the current portfolio, a relative rather than an absolute read of standing.",
      formula: "Server-side (portfolioanalyze): computes the project's percentile rank on CPI and on SPI against every other active project in the portfolio.",
      abstain: "the portfolio has fewer than 3 projects.",
      sources: "Aggregates every active project's CPI/SPI.",
      interp: "A project in the bottom 15th percentile on both CPI and SPI is a portfolio-level outlier regardless of whether its own individual thresholds are breached, this is a peer-comparison read, distinct from the absolute bands used everywhere else in the stack.",
      ground: "Percentile-rank outlier detection is a standard relative-standing technique in portfolio management, appropriate when 'healthy' is contextual to the portfolio's own performance distribution rather than a fixed absolute standard." },
    { n: "PH.3", name: "Signal Trajectory Classifier", mc: "Trajectory_Classifier",
      purpose: "Classifies the direction and character of the project's CPI trend across its own reporting-period history (improving, stable, declining, deteriorating).",
      formula: "Server-side (portfolioanalyze): analyses the CPI trend across the project's own stored snapshot history.",
      abstain: "fewer than 2 reporting periods of CPI history are stored.",
      sources: "The project's own signal snapshot history across reporting cycles; not a portfolio-comparison signal despite sitting in the Portfolio Health suite.",
      interp: "This is the only Portfolio Health module that reads a single project's own trajectory rather than comparing it to peers; a 'deteriorating' classification alongside a still-Green current-period status is an early trend warning worth flagging before the current period itself turns Amber or Red.",
      ground: "Trend-direction classification from a time-ordered signal history is a standard technique for surfacing directional change before a threshold-based single-period status reflects it." },
    { n: "PH.4", name: "Cross-project Pattern Detector", mc: "Cross_Project_Pattern",
      purpose: "Identifies other projects in the portfolio showing a similar distress pattern to this one, distinguishing an isolated project problem from a possible systemic, program-level issue.",
      formula: "Server-side (portfolioanalyze): compares this project's signal-vector combination against every other project's, surfacing others with a similar combination.",
      abstain: "the portfolio has fewer than 3 projects.",
      sources: "Aggregates every active project's signal vectors.",
      interp: "When several projects show the same distress pattern simultaneously, e.g. the same subcontractor, the same material category, the same region, the governance response should shift from project-level to program-level (a common-cause investigation), which is exactly what this module is designed to surface.",
      ground: "Cross-entity pattern matching for common-cause detection is standard portfolio-risk-management practice, distinguishing idiosyncratic (single-project) risk from systematic (program-wide) risk that a project-by-project review would miss." },
    { n: "PH.5", name: "Anomaly Score", mc: "Anomaly_Score",
      purpose: "Combines the other four Portfolio Health methods (Isolation Forest, Outlier percentile, Trajectory, Cross-project Pattern) into a single composite anomaly index from 0-100%, the single most important Portfolio Health output for the executive brief.",
      formula: "Server-side (portfolioanalyze): a weighted combination of PH.1-PH.4's outputs into one composite index.",
      bands: [["green","Below 70%","not highly anomalous"], ["red","≥ 70%","highly anomalous, immediate attention required"]],
      abstain: "the portfolio has fewer than 3 projects, or the four contributing Portfolio Health methods have insufficient data.",
      sources: "Aggregates PH.1-PH.4's already-computed outputs; not an independent document extraction.",
      interp: "Because this is the single composite figure across all four other Portfolio Health lenses, it is the number to check first in the Health dialog before drilling into which specific PH module is driving the anomaly.",
      ground: "Composite anomaly indices combining multiple detection methods into one score are standard practice in anomaly-detection ensembles, reducing the chance that any single method's blind spot goes unnoticed." }
  ];

  /* ---------- Module Reference topic registration (one per category) ---------- */
  const MODREF_TOPICS = {
    "cat1-modules": { id: "cat1-modules", title: "Cat 1 Module Reference", eyebrow: "Cat 1 · Methods & Framework",
      build: () => catModSection("cat1", "Full documentation for all 12 Cat 1 (Quantitative EVM) modules: purpose, exact computation as implemented in simulations.js, real status-band thresholds, data sources, PM interpretation, methodological grounding, governance role, and a human-judgment note. Collapsed by default, expand a module to read it.", CAT1_MODULES) },
    "cat2-modules": { id: "cat2-modules", title: "Cat 2 Module Reference", eyebrow: "Cat 2 · Methods & Framework",
      build: () => catModSection("cat2", "Full documentation for all 11 Cat 2 (Schedule Simulation) modules.", CAT2_MODULES) },
    "cat3-modules": { id: "cat3-modules", title: "Cat 3 Module Reference", eyebrow: "Cat 3 · Methods & Framework",
      build: () => catModSection("cat3", "Full documentation for all 10 Cat 3 (Cost Simulation) modules.", CAT3_MODULES) },
    "cat4-modules": { id: "cat4-modules", title: "Cat 4 Module Reference", eyebrow: "Cat 4 · Methods & Framework",
      build: () => catModSection("cat4", "Full documentation for all 10 Cat 4 (Document & Risk Signals) modules.", CAT4_MODULES) },
    "cat5-modules": { id: "cat5-modules", title: "Cat 5 Module Reference", eyebrow: "Cat 5 · Methods & Framework",
      build: () => catModSection("cat5", "Full documentation for all 8 Cat 5 (System Dynamics & Complexity) modules.", CAT5_MODULES) },
    "cat6-modules": { id: "cat6-modules", title: "Cat 6 Module Reference", eyebrow: "Cat 6 · Methods & Framework",
      build: () => catModSection("cat6", "Full documentation for all 4 Cat 6 (Signal Synthesis) modules.", CAT6_MODULES) },
    "cat7-modules": { id: "cat7-modules", title: "Cat 7 Module Reference", eyebrow: "Cat 7 · Methods & Framework",
      build: () => catModSection("cat7", "Full documentation for all 20 Cat 7 (Evidence Combination) modules.", CAT7_MODULES) },
    "cat9-modules": { id: "cat9-modules", title: "Cat 8 Module Reference", eyebrow: "Cat 8 · Methods & Framework",
      build: () => catModSection("cat8", "Full documentation for all 9 Cat 8 (Governance & Compliance) modules.", CAT8_MODULES) },
    "cat10-modules": { id: "cat10-modules", title: "Cat 9 Module Reference", eyebrow: "Cat 9 · Methods & Framework",
      build: () => catModSection("cat9", "Full documentation for all 7 Cat 9 (Data Integrity & Information Quality) modules.", CAT9_MODULES) },
    "cat11-modules": { id: "cat11-modules", title: "Cat 10 Module Reference", eyebrow: "Cat 10 · Methods & Framework",
      build: () => catModSection("cat10", "Full documentation for all 7 Cat 10 (Decision Optimization) modules.", CAT10_MODULES) },
    "ph-modules": { id: "ph-modules", title: "Portfolio Health Module Reference", eyebrow: "PH · Methods & Framework",
      build: () => catModSection("ph", "Full documentation for all 5 Portfolio Health modules. These compute server-side (the portfolioanalyze endpoint) rather than in this repository's client-side simulations.js; the computation summaries below reflect the same descriptions used elsewhere in this Knowledge Library.", PH_MODULES) }
  };

  /* ---------- References (APA 7th) ---------- */
  const REFERENCES_TOPIC = {
    id: "references", title: "References",
    eyebrow: "Methods & Framework · citations",
    build: () => {
      const refs = [
        "Ballard, G. (2000). <em>The last planner system of production control</em> [Doctoral dissertation, University of Birmingham].",
        "Bonabeau, E. (2002). Agent-based modeling: Methods and techniques for simulating human systems. <em>Proceedings of the National Academy of Sciences</em>, 99(Suppl 3), 7280-7287.",
        "Box, G. E. P., &amp; Jenkins, G. M. (1970). <em>Time series analysis: Forecasting and control</em>. Holden-Day.",
        "Busemeyer, J. R., &amp; Bruza, P. D. (2012). <em>Quantum models of cognition and decision</em>. Cambridge University Press.",
        "Cuong, B. C. (2014). Picture fuzzy sets. <em>Journal of Computer Science and Cybernetics</em>, 30(4), 409-420.",
        "Dantzig, G. B. (1963). <em>Linear programming and extensions</em>. Princeton University Press.",
        "Dempster, A. P. (1967). Upper and lower probabilities induced by a multivalued mapping. <em>Annals of Mathematical Statistics</em>, 38(2), 325-339.",
        "Diakoulaki, D., Mavrotas, G., &amp; Papayannakis, L. (1995). Determining objective weights in multiple criteria problems: The CRITIC method. <em>Computers &amp; Operations Research</em>, 22(7), 763-770.",
        "Dubois, D., &amp; Prade, H. (1988). <em>Possibility theory: An approach to computerized processing of uncertainty</em>. Plenum Press.",
        "Flyvbjerg, B. (2008). Curbing optimism bias and strategic misrepresentation in planning: Reference class forecasting in practice. <em>European Planning Studies</em>, 16(1), 3-21.",
        "Goldratt, E. M. (1997). <em>Critical chain</em>. North River Press.",
        "Hwang, C. L., &amp; Yoon, K. (1981). <em>Multiple attribute decision making: Methods and applications</em>. Springer-Verlag.",
        "Jaynes, E. T. (1957). Information theory and statistical mechanics. <em>Physical Review</em>, 106(4), 620-630.",
        "Kalman, R. E. (1960). A new approach to linear filtering and prediction problems. <em>Journal of Basic Engineering</em>, 82(1), 35-45.",
        "Law, A. M., &amp; Kelton, W. D. (2000). <em>Simulation modeling and analysis</em> (3rd ed.). McGraw-Hill.",
        "Lipke, W. (2003). Schedule is different. <em>The Measurable News</em>, Summer 2003, 31-34.",
        "Liu, F. T., Ting, K. M., &amp; Zhou, Z.-H. (2008). Isolation forest. <em>Proceedings of the 8th IEEE International Conference on Data Mining</em>, 413-422.",
        "Malcolm, D. G., Roseboom, J. H., Clark, C. E., &amp; Fazar, W. (1959). Application of a technique for research and development program evaluation. <em>Operations Research</em>, 7(5), 646-669.",
        "Mendel, J. M., &amp; John, R. I. B. (2002). Type-2 fuzzy sets made simple. <em>IEEE Transactions on Fuzzy Systems</em>, 10(2), 117-127.",
        "Page, E. S. (1954). Continuous inspection schemes. <em>Biometrika</em>, 41(1/2), 100-115.",
        "Pang, J., Wang, J., &amp; Xu, Z. (2016). Probabilistic linguistic term sets in multi-attribute group decision making. <em>Information Sciences</em>, 369, 128-143.",
        "Pareto, V. (1906). <em>Manuale di economia politica</em>. Società Editrice Libraria.",
        "Pawlak, Z. (1982). Rough sets. <em>International Journal of Computer and Information Sciences</em>, 11(5), 341-356.",
        "Project Management Institute. (2019). <em>The standard for earned value management</em>. PMI.",
        "Kutlu Gündoğdu, F., &amp; Kahraman, C. (2019). Spherical fuzzy sets and spherical fuzzy TOPSIS method. <em>Journal of Intelligent &amp; Fuzzy Systems</em>, 36(1), 337-352.",
        "Savage, L. J. (1951). The theory of statistical decision. <em>Journal of the American Statistical Association</em>, 46(253), 55-67.",
        "Senapati, T., &amp; Yager, R. R. (2020). Fermatean fuzzy sets. <em>Journal of Ambient Intelligence and Humanized Computing</em>, 11(2), 663-674.",
        "Shafer, G. (1976). <em>A mathematical theory of evidence</em>. Princeton University Press.",
        "Smarandache, F. (1995). <em>A unifying field in logics: Neutrosophic logic</em>. American Research Press.",
        "Smarandache, F. (2018). Extension of soft set to hypersoft set, and then to plithogenic hypersoft set. <em>Neutrosophic Sets and Systems</em>, 22, 168-170.",
        "Steward, D. V. (1981). The design structure system: A method for managing the design of complex systems. <em>IEEE Transactions on Engineering Management</em>, 28(3), 71-74.",
        "Stević, Ž., Pamučar, D., Puška, A., &amp; Chatterjee, P. (2020). Sustainable supplier selection in healthcare industries using a new MCDM method: Measurement of alternatives and ranking according to compromise solution (MARCOS). <em>Computers &amp; Industrial Engineering</em>, 140, 106231.",
        "Torra, V. (2010). Hesitant fuzzy sets. <em>International Journal of Intelligent Systems</em>, 25(6), 529-539.",
        "Turksen, I. B. (1986). Interval valued fuzzy sets based on normal forms. <em>Fuzzy Sets and Systems</em>, 20(2), 191-210.",
        "Yager, R. R. (2013). Pythagorean membership grades in multicriteria decision making. <em>IEEE Transactions on Fuzzy Systems</em>, 22(4), 958-965.",
        "Yang, J. B., Liu, J., Wang, J., Sii, H. S., &amp; Wang, H. W. (2006). Belief rule-base inference methodology using the evidential reasoning approach. <em>IEEE Transactions on Systems, Man, and Cybernetics, Part A</em>, 36(2), 266-285.",
        "Zadeh, L. A. (1975). The concept of a linguistic variable and its application to approximate reasoning, I. <em>Information Sciences</em>, 8(3), 199-249.",
        "Zadeh, L. A. (2011). A note on Z-numbers. <em>Information Sciences</em>, 181(14), 2923-2932."
      ];
      return `<p class="kn-lead">APA 7th-edition references for every method actually implemented in PCEIF's 103 project-level modules and 5 Portfolio Health modules, cited in-text throughout the Cat 1-10 and Portfolio Health Module Reference sections above. Only works that genuinely underlie an implemented computation are listed here.</p>
        <ul class="kn-list kn-refs">${refs.sort().map((r) => `<li>${r}</li>`).join("")}</ul>`;
    }
  };

  /* ---------- Limitations and Threats to Validity ---------- */
  const LIMITATIONS_TOPIC = {
    id: "limitations", title: "Limitations and Threats to Validity",
    eyebrow: "Methods & Framework · honest boundaries",
    build: () => `
      <p class="kn-lead">This section states plainly what this demonstration does and does not establish, so a reviewer can calibrate exactly how much weight to place on any module output.</p>

      <h3>Synthetic demonstration data</h3>
      <p>Every project on this site is synthetic: authored and calibrated to exercise the framework's status bands and conflict-classification logic, not sourced from a real program, agency, employer, or contractor. Numbers were chosen to populate the full Green-through-Red range across the module set, not sampled from field measurements. Nothing here should be read as a claim about how any real capital program has performed.</p>

      <h3>LLM extraction variance</h3>
      <p>Where document text is summarised or classified by an LLM (the scripted-fallback assistant and the AI-assisted document review path), the same source document can extract marginally differently between runs, language models are not perfectly deterministic even at low temperature. This is mitigated two ways: source documents are kept to raw, primary figures rather than requiring the model to infer or estimate, and every downstream calculation, once a figure is extracted, is fully deterministic arithmetic in simulations.js with no further model involvement. The extraction step is the only place variance can enter; the 103-module computation stack that follows it is exact and reproducible given the same inputs.</p>

      <h3>Single-source document risk scoring</h3>
      <p>Cat 1.3 / Cat 4.1 document risk (Doc_Risk / Doc_Risk_Cat4) is a transparent keyword-and-pattern score, not a semantic understanding of the text. It is deliberately treated throughout PCEIF as a leading indicator requiring Cat 6.1 corroboration, never as a standalone trigger, precisely because a rule-based score over a single document type is a narrow, gameable signal on its own. A sophisticated author can write around keyword rules; the score's value is in its transparency and auditability (every match and excerpt is inspectable), not in claimed semantic accuracy.</p>

      <h3>What module abstention does and does not mean</h3>
      <p>When a module reports "Insufficient data" (the insufficientData() stub in simulations.js), that means specifically that one or more required input fields were null or undefined for that computation, nothing more. It does NOT mean the project is healthy, it does not mean the underlying condition is absent, and it is not itself a status band, an abstaining module is excluded from category fusion (Cat 6-8) rather than defaulting to Green. A project with many abstaining modules should be read through Cat 9 (Data Integrity), specifically Cat 9.1 Missing Data Index and Cat 9.5 Information Completeness Ratio, before its fused status is treated as a confident read.</p>

      <h3>Portfolio-scale methods and small populations</h3>
      <p>The five Portfolio Health modules (PH.1-PH.5) compare a project against the rest of the portfolio and require at least 3 active projects to produce a meaningful centroid, covariance estimate, or percentile rank; with fewer than 3 projects these modules abstain. Even above that floor, anomaly-detection methods like Isolation Forest (Liu, Ting &amp; Zhou, 2008, cited in the References above) are known to be sensitive to small sample sizes, a portfolio of 4-5 projects will produce noisier outlier and cross-project-pattern reads than one of 40-50, and a PH.5 Anomaly Score computed against a very small portfolio should be weighted accordingly.</p>

      <h3>Behavioral and simulation modules as synthetic stress tests</h3>
      <p>The agent-based, game-theoretic, and discrete-event style modules are synthetic stress-test illustrations, not calibrated behavioral models. They demonstrate how the framework governs a signal under bounded conditions; they do not prove real-world behavioral outcomes, and they are not calibrated against observed project-control meetings or decision events. Future work would need to calibrate these parameters against coded practitioner decision patterns or controlled expert elicitation before they could support empirical claims.</p>

      <h3>Practitioner-validation scope and pilot dependency</h3>
      <p>The intended evaluation path is design-science practitioner consultation (relevance, feasibility, auditability, fairness, usability, and implementation burden), not field measurement. Practitioner feedback can support the claim that the framework is credible and worth refinement; it cannot substitute for a field pilot. PCEIF should be treated as a governance artifact pending pilot testing, not as an operational standard for agency adoption. The technology landscape it reasons about is also bounded by the literature cutoff and will continue to evolve, which the model-agnostic signal classes and version governance are designed to accommodate.</p>

      <h3>No claim of predictive validity</h3>
      <p>No predictive-accuracy validation has been performed on this demonstration, there is no held-out real-world outcome data against which any module's forecast, threshold, or classification has been back-tested. This is a deliberate scope boundary, not an oversight: the research contribution of this project is the governance framework and decision logic itself, the signal-to-action pipeline, the explicit conflict typing in Cat 6.1, the named-authority escalation rules in Cat 8.1/decision.js, the fairness gate, the audit-export structure, validated qualitatively against public-sector program-controls and administrative-law practice, not the numerical accuracy of the synthetic module outputs. A reviewer evaluating this work should evaluate the governance architecture on its own terms, and treat every module's numeric output as an illustration of that architecture rather than as a validated forecast.</p>
    `
  };

  /* ---------- PCEIF Framework Overview (TDS §1-4) ---------- */
  const FRAMEWORK_TOPIC = {
    id: "pceif-framework", title: "PCEIF Framework Overview",
    eyebrow: "Methods & Framework · the governance spine",
    build: () => `
      <p class="kn-lead">PCEIF, the Public Capital EVM Intelligence Framework, is a model-agnostic governance architecture for converting project-control signals into accountable action. It treats every analytical output as evidence, and defines the minimum conditions under which that evidence can support monitoring, clarification, investigation, escalation, recovery planning, executive review, or formal authority review, and what must be recorded when a PM accepts, rejects, overrides, defers, or requests more evidence. Lin Opus Gubernatio is the current reference implementation, but PCEIF can be instantiated above commercial platforms, spreadsheets, simulations, or future digital-twin environments.</p>

      <h3>Architectural principles</h3>
      <ul class="kn-list">
        <li><strong>Technology agnosticism.</strong> Governance attaches to the signal package, not to the vendor or algorithm.</li>
        <li><strong>Evidence traceability.</strong> Every signal identifies its data date, source record, method or rule, input completeness, uncertainty, and trigger reason.</li>
        <li><strong>Human accountability.</strong> High-impact actions require a named reviewer and a recorded judgment.</li>
        <li><strong>Procedural fairness.</strong> Contractor-affecting action requires evidence review and a response opportunity, unless urgent safety, compliance, or public-interest conditions apply.</li>
        <li><strong>Abstention honesty.</strong> Modules with missing required inputs return no status and are excluded from fusion rather than fabricating evidence.</li>
        <li><strong>Single-source state.</strong> Project status is computed once, persisted, and read by all surfaces.</li>
        <li><strong>Learning governance.</strong> Repeated override, deferral, and data-doubt patterns become framework-revision inputs.</li>
      </ul>

      <h3>The four-layer governance architecture</h3>
      <ul class="kn-list">
        <li><strong>Layer 1, Evidence and Record Governance.</strong> Controls source records, version, date, provenance, completeness, and access boundary.</li>
        <li><strong>Layer 2, Signal Assurance Governance.</strong> Controls method transparency, thresholds, uncertainty, abstention, and conflict.</li>
        <li><strong>Layer 3, Decision Authority Governance.</strong> Controls action category, authority, timeframe, fairness, approval, and override.</li>
        <li><strong>Layer 4, Audit, Learning, and Version Governance.</strong> Controls reconstruction, review, post-action learning, and framework change.</li>
      </ul>

      <h3>Governance objects</h3>
      <p>The object model deliberately separates evidence extraction, analytical computation, and management authority so they cannot be conflated: project record, source document, extracted fact, signal input, signal output, signal package, category state, conflict state, project-health state, Portfolio Health state, governance decision card, PM judgment record, responsible-party response record, audit event, and framework version. A source document can produce extracted facts; facts can support signals; signals can support a recommendation; only a human authority can approve or modify an action.</p>

      <h3>From document to decision</h3>
      ${svgPceifFlow()}
      <p>Records (documents, schedule, cost) become signals (Cat 1 to Cat 5), which are synthesised into a baseline health state (Cat 6), cross-checked for confidence (Cat 7), checked for data quality and optimal response (Cat 9, Cat 10), governed into a decision card with a named authority (Cat 8), approved by a named human, and preserved as an exportable audit record. Portfolio Health (PH) runs alongside as program-level context, not a project-level trigger.</p>

      <h3>Conformance</h3>
      <p>An implementation conforms to PCEIF only when it preserves the evidence-to-action separation, exposes method and source metadata, supports abstention, records human judgment, enforces authority and fairness controls, and produces an exportable audit record. Visual similarity to Lin is not a conformance requirement.</p>
    `
  };

  /* ---------- Status & Evidence Rules (TDS §6, verified vs code) ---------- */
  const STATUS_RULES_TOPIC = {
    id: "status-evidence-rules", title: "Status & Evidence Rules",
    eyebrow: "Methods & Framework · how status is decided",
    build: () => `
      <p class="kn-lead">PCEIF status is not a single averaged colour. Module states roll up into category states, category states fuse into a project state, and disagreement is surfaced at every step. The rules below are stated as implemented in <code>sim.js</code> and <code>simulations.js</code>, which are the ground truth for every threshold.</p>

      <h3>The five states plus Abstain</h3>
      <p>A module or category reports one of five states, Complete, Green, Yellow, Amber, or Red, or it Abstains. Abstain is a governance state, not an error: it communicates that the evidence a module requires is absent or insufficient. An abstaining module (the <code>insufficientData()</code> path in simulations.js, triggered when a required input is null or undefined) contributes no mass to fusion and is excluded from the vote; it does not default to Green. Complete (blue) is a project-end flag set when actual percent complete reaches 100, independent of the fused band; a completed source contributes best-case (Green) evidence to any fusion it enters.</p>

      <h3>Evidence sufficiency and the minimum viable signal package</h3>
      <p>Before a status is trusted, the signal package should carry, for each contributing signal, its source record, data date, method or rule identity, input completeness, uncertainty or confidence, and trigger reason. A project running many abstaining modules should be read through Cat 9 (Data Integrity), specifically the Missing Data Index and the Information Completeness Ratio, before its fused status is treated as a confident read.</p>

      <h3>Category status: Dempster-Shafer evidence combination</h3>
      <p>Category status is produced by evidence combination, not worst-wins. The shared <code>dstFuse()</code> in simulations.js maps each module status to a belief mass over {Green, Yellow, Amber, Red, Unknown} (for example a Red source carries mass 0.76 to Red, 0.14 to Amber), combines sources by Dempster's rule, and reports the maximum-belief state. A Red-dominant source is applied at 1.5x weight (full once plus a half-strength Shafer-discounted re-combination) so a single Red cannot silently sink a category of greens, while genuine Red evidence still dominates. The combination also yields a conflict coefficient K measuring how much the sources disagree.</p>

      <h3>Project status: conservative dominance and the conflict advisory</h3>
      <p>Project status follows conservative dominance in spirit, a severe, credible category is not averaged away, and is implemented by fusing all eleven registry category statuses (the ten project categories plus Portfolio Health) through the same Dempster-Shafer fuser with Red weighted 1.5x. The last-step conflict K feeds an advisory <code>redReview</code> flag when K is at least 0.55; this flags the package for accountable human review but never overrides the fused band. (Within an individual Cat 7 evidence module, the conflict level is labelled High above 0.30 and Moderate above 0.10.) Portfolio Health provides program-level review context but does not directly authorise project-level formal action.</p>

      <h3>Cat 1 core thresholds (sim.js)</h3>
      ${modBands([
        ["green","Monte Carlo (mcStatus)","Green P80 EAC within +5% of BAC; Amber +5% to +10%; Red beyond +10%"],
        ["amber","CUSUM (cusumStatus)","two-sided tabular CUSUM, μ0 = 1.00, k = 0.5σ, decision interval H = 5σ; Red on a C+ or C- breach of H"],
        ["red","Document risk (docStatus)","Green below 0.30; Amber 0.30 to 0.70; Red at or above 0.70"]
      ])}
    `
  };

  /* ---------- Human Judgment Record (TDS §8) ---------- */
  const JUDGMENT_TOPIC = {
    id: "human-judgment-record", title: "Human Judgment Record",
    eyebrow: "Methods & Framework · accountable judgment",
    build: () => `
      <p class="kn-lead">PCEIF never lets a model output become an action on its own. Whenever a recommendation is approved, modified, overridden, deferred, escalated, or converted into an evidence request, the PM judgment record is mandatory. No silent override is permitted: the reasoning is always written down and always enters the audit trail.</p>

      <h3>Mandatory rationale, no silent override</h3>
      <p>The decision card exposes the derived state, the dominant signal, the recommended action, the required authority, the fairness requirement, and the documentation required. A named reviewer must record a rationale before the decision is committed. Accepting the recommendation is a judgment; departing from it is a judgment; both are recorded. This is what separates a governed decision from an automated one.</p>

      <h3>The override taxonomy</h3>
      <p>When a reviewer departs from the recommendation, the judgment record classifies why, using a fixed taxonomy so patterns can be learned across cycles:</p>
      <ul class="kn-list">
        <li><strong>data_doubt.</strong> The reviewer questions the accuracy or completeness of the underlying data.</li>
        <li><strong>context_knowledge.</strong> The reviewer holds project context the model does not, that changes the reading.</li>
        <li><strong>timing.</strong> The action is right but the timing is not; the reviewer defers or accelerates.</li>
        <li><strong>authority_directed.</strong> A higher authority has directed a different course.</li>
        <li><strong>evidence_escalation.</strong> The reviewer judges the evidence stronger than the signal implies and escalates.</li>
        <li><strong>evidence_reduction.</strong> The reviewer judges the evidence weaker than the signal implies and de-escalates.</li>
        <li><strong>fairness_gate.</strong> The reviewer intervenes to protect a responsible party's response opportunity before formal action.</li>
        <li><strong>emergency.</strong> Urgent safety, compliance, or public-interest conditions require immediate action.</li>
      </ul>

      <h3>The judgment ledger</h3>
      <p>The judgment ledger joins the decision card, the approval record, the override or deferral record, the responsible-party response record, and the audit identifier into one reconstructable chain. The audit record must permit reconstruction of what evidence existed, what method was used, which signal state was produced, who reviewed it, what judgment was made, why it was made, and what follow-up was assigned.</p>

      <h3>Fairness gate</h3>
      <p>Where an action would affect a contractor or other responsible party and the state has reached red-review, the fairness gate is a mandatory procedural step: evidence review and a documented response opportunity must be acknowledged before a formal decision is recorded, unless urgent safety, compliance, or public-interest conditions apply. It is a workflow step, never a score or percentage.</p>

      <h3>Learning governance</h3>
      <p>Repeated overrides, deferrals, and evidence-gap patterns are not noise; they are inputs to framework revision. Learning governance analyses them to identify thresholds, modules, data pipelines, or workflow steps that require change, so the framework improves from how it is actually used.</p>
    `
  };

  window.LIN_KNOWLEDGE = { terms: TERMS, glossary: GLOSSARY, topics: TOPICS, library: LIBRARY };

  /* ---------- knowledge page rendering, two-panel navigator + content ---------- */
  /* ---------- category nav structure (10 numbered categories + Portfolio Health) ----------
     Top-level entries are either flat topics (rendered as a single button) or
     a `category` group with a list of child topic ids. Portfolio Health (the
     former ML & AI category) is now a portfolio-level suite displayed as
     "PH", not a numbered project-level category, its topic ids are
     'stage2:*' (kept for back-compat) and resolve to the real per-method
     articles in CAT8_TOPICS. */
  const CATEGORY_NAV = [
    { id: "pceif" },
    { id: "pceif-framework" },
    { id: "why-108-modules" },
    { id: "five-status" },
    { id: "status-evidence-rules" },
    { id: "human-judgment-record" },
    { id: "how-categories-advise-pm" },
    { category: "cat1", num: "Cat 1", name: "Quantitative EVM",
      children: ["module01", "module02", "module03", "cat1-modules"] },
    { category: "cat2", num: "Cat 2", name: "Schedule Simulation",
      children: ["module04", "module05", "module06", "cat2-modules"] },
    { category: "cat3", num: "Cat 3", name: "Cost Simulation",
      children: ["module07", "module08", "cat3-modules"] },
    { category: "cat4", num: "Cat 4", name: "Document & Risk Signals",
      children: ["module03", "cat4-modules"] },
    { category: "cat5", num: "Cat 5", name: "System Dynamics",
      children: ["module08", "cat5-modules"] },
    { category: "cat6", num: "Cat 6", name: "Signal Synthesis",
      children: ["module09", "cat6-modules"] },
    { category: "cat7", num: "Cat 7", name: "Evidence Combination",
      children: ["module10", "module11", "module12", "module13", "module14",
                 "module15", "module16", "module17", "module18", "cat7-modules"] },
    { category: "cat9", num: "Cat 8", name: "Governance & Compliance",
      children: ["module19", "cat9-modules"] },
    { category: "cat10", num: "Cat 9", name: "Data Integrity & Information Quality",
      children: ["cat10-overview", "cat10-modules"] },
    { category: "cat11", num: "Cat 10", name: "Decision Optimization",
      children: ["cat11-overview", "cat11-modules"] },
    { category: "cat8", num: "PH", name: "Portfolio Health",
      children: ["stage2:isolation", "stage2:portfolio", "stage2:trajectory",
                 "stage2:cross-project", "stage2:anomaly-score", "ph-modules"] },
    { id: "limitations" },
    { id: "references" },
    { id: "fairness" },
    { id: "decision" }
  ];

  // Sequential display numbers for top-level flat topics, derived from nav
  // order at render time so inserting a topic never breaks the numbering.
  // Category groups are skipped, "Cat N" is domain terminology, not an
  // ordinal. Topic ids/anchors are untouched; only the display label changes.
  const TOPIC_DISPLAY_NUM = {};
  CATEGORY_NAV.filter((g) => !g.category).forEach((g, i) => { TOPIC_DISPLAY_NUM[g.id] = i + 1; });
  function displayTitle(t) {
    const bare = String(t.title || "").replace(/^\d+[a-z]?\.\s*/, "");
    const n = TOPIC_DISPLAY_NUM[t.id];
    return n ? n + ". " + bare : bare;
  }

  // Cat X.Y label per topic id, used in the nav and the article header.
  const CAT_LABEL_BY_ID = {
    module01: "Cat 1.1", module02: "Cat 1.2", module03: "Cat 1.3 / Cat 4.1",
    module04: "Cat 2.1", module05: "Cat 2.2", module06: "Cat 2.3",
    module07: "Cat 3.1", module08: "Cat 3.2 / Cat 5.1",
    module09: "Cat 6.1",
    module10: "Cat 7.1", module11: "Cat 7.2", module12: "Cat 7.3",
    module13: "Cat 7.4", module14: "Cat 7.5", module15: "Cat 7.6",
    module16: "Cat 7.7", module17: "Cat 7.8", module18: "Cat 7.9",
    module19: "Cat 8.1"
  };

  // Portfolio Health (formerly "Cat 8, ML & AI Pattern Detection"). Active
  // (portfolioanalyze, Code.gs v10.17). This is a portfolio-level suite, not
  // a numbered project-level category, its modules are labelled PH.1–PH.5.
  // The shared overview is prepended to every Portfolio Health article so the
  // context (portfolio-wide comparison) is always visible.
  const CAT8_OVERVIEW = "Portfolio Health uses portfolio-wide signal comparison to detect anomalies that individual module analysis cannot surface. Rather than evaluating a project in isolation, these methods ask: how does this project compare to every other project in the portfolio? A project with normal-looking EVM can still be anomalous if its combination of cost performance, schedule performance, and document risk is unlike any other project in the program.";

  const CAT8_TOPICS = {
    "stage2:isolation": { id: "stage2:isolation", title: "PH.1 Isolation Forest",
      body: "Measures how far a project's signal combination sits from the portfolio centroid using Mahalanobis distance. High distance = unusual combination of signals. A project with moderate CPI and moderate SPI but very high document risk may appear amber on individual modules but anomalous when compared against the full portfolio." },
    "stage2:portfolio": { id: "stage2:portfolio", title: "PH.2 Portfolio Outlier Detection",
      body: "Ranks the project by CPI and SPI percentile within the portfolio. A project in the bottom 15th percentile on both dimensions is a portfolio-level outlier, regardless of whether individual thresholds are breached." },
    "stage2:trajectory": { id: "stage2:trajectory", title: "PH.3 Signal Trajectory Classifier",
      body: "Analyzes CPI trend across reporting periods from the stored snapshot history. Distinguishes improving, stable, declining, and deteriorating trajectories. Requires at least 2 reporting periods." },
    "stage2:cross-project": { id: "stage2:cross-project", title: "PH.4 Cross-project Pattern Detector",
      body: "Identifies other projects in the portfolio with similar signal combinations. When multiple projects show the same distress pattern, it may indicate a systemic program-level issue rather than an isolated project problem." },
    "stage2:anomaly-score": { id: "stage2:anomaly-score", title: "PH.5 Composite Anomaly Score",
      body: "Weighted combination of all Portfolio Health methods into a single anomaly index from 0 to 100%. Above 70% = highly anomalous, immediate attention required. This is the single most important Portfolio Health output for the executive brief." }
  };
  function cat8TopicBody(t) {
    return `<p class="kn-sub">${CAT8_OVERVIEW}</p><p class="kn-lead">${t.body}</p>`;
  }

  // Cat 9 / 10, category-level articles. Individual modules are not
  // (yet) carved into per-method articles; the overview surfaces the entire
  // category's purpose, module list, and PM reading instructions.
  const CAT_OVERVIEW_TOPICS = {
    "cat10-overview": {
      id: "cat10-overview",
      title: "Cat 9, Data Integrity & Information Quality",
      eyebrow: "Cat 9 · data quality of the inputs",
      body: "Every analytical output in PCEIF is only as good as its inputs. A CPI derived from an unverified pay application is less reliable than one from an audited schedule of values. A document risk score estimated from proxy signals is less precise than one extracted directly from RFI logs. Cat 9 makes this uncertainty explicit, it does not hide it.",
      modules: [
        ["9.1 Missing Data Index", "Counts how many of the 11 core signal fields are populated. A project with 6 of 11 fields missing may still generate a governance recommendation, but Cat 9.1 flags that the recommendation rests on incomplete information."],
        ["9.2 Data Timeliness Score", "Measures days since the most recent document upload. Data older than 60 days warrants a Yellow flag, the signals may not reflect current project conditions. Data older than 90 days warrants Amber."],
        ["9.3 Source Reliability Weighting", "Each document type carries a reliability weight based on its verification status. Verified pay applications (0.90) outweigh estimated fields derived from proxy calculations (0.40). The weighted average across all populated fields gives the overall source reliability score."],
        ["9.4 Audit Trail Completeness", "Checks whether the required governance events are recorded, project creation, document uploads, signal extractions, and decision records. A project with signals but no decision record has an incomplete audit trail."],
        ["9.5 Information Completeness Ratio", "Distinguishes between measured fields (from actual documents) and estimated fields (derived from proxy calculations). A project with 80% measured fields has higher information quality than one with 40% measured."],
        ["9.6 Cross-document Consistency Score", "Checks whether figures across uploaded documents are internally consistent. If the CPI stored in signalInputs does not match EV/AC, or if the percentage complete in the pay application conflicts with the schedule, this module flags the inconsistency."],
        ["9.7 Reporting Frequency Index", "Measures the average interval between document uploads. Projects with infrequent updates accumulate stale data, a 90-day gap between pay applications means the portfolio is making decisions on two-month-old cost performance data."]
      ],
      pmReading: "High Cat 9 status means the evidence base is current, measured, complete and internally consistent, act on the Cat 8 recommendation with confidence. Low Cat 9 status means the evidence base has gaps, seek additional documents before recording a formal governance action."
    },
    "cat11-overview": {
      id: "cat11-overview",
      title: "Cat 10, Decision Optimization",
      eyebrow: "Cat 10 · choosing under constraints",
      body: "Cat 5 (System Dynamics) explains how project components interact and how disturbances propagate. Cat 10 takes the current signal state as given and asks: what is the optimal decision? These are fundamentally different questions. Cat 5 is diagnostic; Cat 10 is prescriptive.",
      modules: [
        ["10.1 Multi-Objective Optimization", "Public capital projects have three competing objectives: minimize cost overrun, minimize schedule delay, minimize risk. These objectives often trade off, accelerating schedule increases cost; reducing scope reduces risk but may miss requirements. Cat 10.1 finds the Pareto-efficient position given the current signal state."],
        ["10.2 Linear Programming", "Given remaining work, remaining budget, and current cost performance, linear programming determines whether completing the project within budget is feasible and what CPI is required. It answers: is recovery possible?"],
        ["10.3 Constraint Satisfaction Analysis", "Checks whether the project satisfies four governance constraints: cost (CPI ≥ 0.90), schedule (SPI ≥ 0.90), document risk (score < 0.70), and FAR reporting threshold (overrun < 25%). Violated constraints require specific governance responses under federal acquisition regulations."],
        ["10.4 What-If Scenario Matrix", "Projects four futures: optimistic (CPI recovers to 1.0), base (current CPI continues), pessimistic (CPI degrades 5%), and recovery (CPI improves 5%). The range across scenarios quantifies decision uncertainty."],
        ["10.5 Decision Sensitivity Matrix", "Identifies which input variable most affects the governance recommendation. If cost performance accounts for 70% of decision sensitivity, a small CPI change changes the recommendation significantly, the PM should focus verification efforts there first."],
        ["10.6 Pareto Frontier Analysis", "Determines whether the project is Pareto-efficient (all objectives met), Pareto-dominated (multiple objectives failing simultaneously, suggesting systemic problems), or in a trade-off zone (improving one objective requires accepting degradation in another)."],
        ["10.7 Regret Minimization Index", "Applies minimax regret theory to the PM's decision under uncertainty. Given three possible futures (improvement, stability, deterioration) and three possible decisions (monitor, investigate, escalate), which decision minimizes the worst-case regret? This is the most theoretically grounded decision-theoretic module in PCEIF."]
      ],
      pmReading: "Cat 10 is read AFTER Cat 6 and Cat 7, it does not replace the conservative-dominance classification or the evidence-combination cross-check, it operationalises them. The PM reads Cat 6/7 to understand the state, then reads Cat 10 to choose the action."
    }
  };
  function catOverviewBody(t) {
    var modList = (t.modules || []).map(function (m) {
      return '<li><strong>' + esc(m[0]) + '</strong>, ' + esc(m[1]) + '</li>';
    }).join("");
    return '<p class="kn-lead">' + esc(t.body) + '</p>' +
           '<h3>Modules in this category</h3>' +
           '<ul class="kn-list">' + modList + '</ul>' +
           '<h3>How the PM reads this category</h3>' +
           '<p>' + esc(t.pmReading) + '</p>';
  }

  const CATEGORIES_ADVISE_PM_TOPIC = {
    id: "how-categories-advise-pm",
    title: "How the categories advise the PM",
    eyebrow: "Reading the categories",
    build: () => `
      <p class="kn-lead">The ten project-level categories, plus the portfolio-level Health suite, each answer a different governance question. Reading them together tells the PM where to spend attention this reporting cycle.</p>
      <ul class="kn-list">
        <li><strong>Cat 1 Quantitative EVM</strong>, what is happening NOW (cost / schedule indices).</li>
        <li><strong>Cat 2 Schedule Simulation</strong>, WHEN will problems appear (time-based leading indicators).</li>
        <li><strong>Cat 3 Cost Simulation</strong>, HOW MUCH will it cost (budget-based leading indicators).</li>
        <li><strong>Cat 4 Document & Risk Signals</strong>, qualitative early warning from project records, BEFORE EVM shows the slip.</li>
        <li><strong>Cat 5 System Dynamics</strong>, how the components AMPLIFY each other (rework propagation).</li>
        <li><strong>Cat 6 Signal Synthesis</strong>, the BASELINE classification (conservative dominance), the worst single signal wins.</li>
        <li><strong>Cat 7 Evidence Combination</strong>, HOW CONFIDENT is the classification (twenty independent uncertainty-reasoning methods cross-check the baseline).</li>
        <li><strong>Cat 8 Governance & Compliance</strong>, the named authority, required action, and audit trail.</li>
        <li><strong>Cat 9 Data Integrity</strong>, how trustworthy ARE the inputs. Missing data, stale data, low-reliability sources, Cat 9 surfaces the quality of the signal package the other categories consumed.</li>
        <li><strong>Cat 10 Decision Optimization</strong>, given everything the models found, what is the BEST action under constraints (multi-objective, LP, regret minimization).</li>
        <li><strong>Portfolio Health (PH)</strong>, portfolio-wide anomaly detection: how unusual is this project versus the whole program (Isolation Forest, outlier ranking, trajectory, cross-project patterns, composite score).</li>
      </ul>
      <h3>Five-step PM decision protocol</h3>
      <ol class="kn-list kn-list-num">
        <li><strong>Read Cat 8 (Governance)</strong>, this is the recommended action.</li>
        <li><strong>Check Cat 6 (Conservative Dominance)</strong>, this is the baseline state.</li>
        <li><strong>Check Cat 9 (Data Integrity)</strong>, how much to trust the signals.</li>
        <li><strong>Count how many of Cat 7 (20 evidence methods) agree with Cat 6:</strong>
          <ul class="kn-list" style="margin-top:6px">
            <li>16–20 agree: HIGH CONFIDENCE, act on Cat 8 recommendation.</li>
            <li>10–15 agree: MODERATE CONFIDENCE, act but document uncertainty.</li>
            <li>&lt;10 agree: LOW CONFIDENCE, investigate before acting.</li>
          </ul>
        </li>
        <li><strong>Read Cat 10 (Optimization)</strong> for the recommended decision pathway.</li>
        <li><strong>Record decision</strong> with rationale, authority, and confidence level.</li>
      </ol>
      <p>The PM reads the categories top-down to GENERATE the picture (with Cat 9 verifying that what was generated stands on solid inputs), then bottom-up (start at Cat 8 / Cat 10) to ACT on it. The decision is whatever Cat 8 records, the rest of the 103-module stack is the evidence supporting that decision.</p>
    `
  };

  function renderKnowledgePage() {
    const root = document.getElementById("knowledge-root");
    if (!root) return;
    let selectedId = (LIBRARY[0] && LIBRARY[0].id) || "pceif";

    function isMobile() { return window.innerWidth <= 640; }

    // Topic lookup that includes Stage 2 stubs and the new how-the-categories
    // topic alongside the existing LIBRARY entries.
    function lookupTopic(id) {
      if (MODREF_TOPICS[id]) return MODREF_TOPICS[id];
      if (id === "pceif-framework") return FRAMEWORK_TOPIC;
      if (id === "status-evidence-rules") return STATUS_RULES_TOPIC;
      if (id === "human-judgment-record") return JUDGMENT_TOPIC;
      if (id === "limitations") return LIMITATIONS_TOPIC;
      if (id === "references") return REFERENCES_TOPIC;
      if (CAT8_TOPICS[id]) {
        const t = CAT8_TOPICS[id];
        return Object.assign({}, t, {
          eyebrow: "Portfolio Health (PH)",
          build: () => cat8TopicBody(t)
        });
      }
      if (CAT_OVERVIEW_TOPICS[id]) {
        const t = CAT_OVERVIEW_TOPICS[id];
        return Object.assign({}, t, { build: () => catOverviewBody(t) });
      }
      if (id === "how-categories-advise-pm") return CATEGORIES_ADVISE_PM_TOPIC;
      return LIBRARY.find((x) => x.id === id) || null;
    }

    function flatNavBtn(id) {
      const t = lookupTopic(id);
      if (!t) return "";
      return `<li><button class="kn-nav-btn${t.id === selectedId ? " active" : ""}" data-topic="${esc(t.id)}">${esc(displayTitle(t))}</button></li>`;
    }

    function modNavBtn(id) {
      const t = lookupTopic(id);
      if (!t) return "";
      // Titles are now "N. Cat X.Y: Name" (or legacy "N. Module NN: Name").
      // Strip the leading ordinal and the Cat/Module prefix, then re-prefix
      // with the canonical Cat X.Y label so the nav never double-prints it.
      const bare = t.title
        .replace(/^\d+\.\s*/, "")
        .replace(/^(Cat\s[\d.]+|Module\s\d+):\s*/, "");
      const label = CAT_LABEL_BY_ID[id] ? CAT_LABEL_BY_ID[id] + " " + bare : t.title;
      return `<li class="kn-nav-mod"><button class="kn-nav-btn${t.id === selectedId ? " active" : ""}" data-topic="${esc(t.id)}">${esc(label)}</button></li>`;
    }

    function categoryGroup(g) {
      // Portfolio Health stage-2 topics and Cat 9/10 category overviews render as
      // simple flat buttons (no Cat X.Y CAT_LABEL_BY_ID rewriting).
      const childButtons = (g.children || []).map((cid) =>
        (CAT8_TOPICS[cid] || CAT_OVERVIEW_TOPICS[cid]) ? flatNavBtn(cid) : modNavBtn(cid)
      ).join("");
      const open = g.children && g.children.some((c) => c === selectedId);
      const parkedTag = g.parked ? `<span class="kn-nav-cat-parked">Stage 2</span>` : "";
      return `<li class="kn-nav-cat">
        <details${open ? " open" : ""}>
          <summary class="kn-nav-cat-head">
            <span class="kn-nav-cat-num">${esc(g.num)}</span>
            <span class="kn-nav-cat-name">${esc(g.name)}</span>
            ${parkedTag}
          </summary>
          <ol class="kn-nav-cat-list">${childButtons}</ol>
        </details>
      </li>`;
    }

    function navHtml() {
      return CATEGORY_NAV.map((g) => g.category ? categoryGroup(g) : flatNavBtn(g.id)).join("");
    }
    /* Split the article body on <h3>…</h3> headings and wrap each section
       in the shared collapsibleSection() pattern. The lead intro that sits
       before the first <h3> becomes an "Overview" panel open by default; all
       <h3> sections collapse closed. Topics with no <h3> are returned as-is. */
    function wrapArticleSections(html, topicId) {
      if (!window.collapsibleSection) return html;
      const parts = String(html || "").split(/(<h3[^>]*>[\s\S]*?<\/h3>)/i);
      if (parts.length < 3) return html;
      const overview = parts[0] || "";
      let out = "";
      const safeOverview = overview.trim();
      if (safeOverview) {
        out += window.collapsibleSection(
          "kn-" + topicId + "-overview", "Overview", overview, true);
      }
      for (let i = 1; i < parts.length; i += 2) {
        const headingMatch = parts[i].match(/<h3[^>]*>([\s\S]*?)<\/h3>/i);
        const titleHtml = headingMatch ? headingMatch[1] : ("Section " + ((i + 1) / 2));
        const titleText = titleHtml.replace(/<[^>]+>/g, "").trim() || ("Section " + ((i + 1) / 2));
        const body = parts[i + 1] || "";
        const sectionId = "kn-" + topicId + "-sec" + ((i + 1) / 2);
        // Leading ordinal ("1.") renders gold, echoing the brand-init treatment.
        const numMatch = titleText.match(/^(\d+[a-z]?\.)\s*(.*)$/);
        const titleMarkup = numMatch
          ? `<span class="kn-sec-num">${esc(numMatch[1])}</span> ${esc(numMatch[2])}`
          : esc(titleText);
        out += window.collapsibleSection(sectionId, titleMarkup, body, false);
      }
      return out;
    }

    function contentHtml() {
      const t = lookupTopic(selectedId) || LIBRARY[0];
      const built = t.build ? t.build() : "";
      const body = wrapArticleSections(built, t.id || "topic");
      // Gold leading number + cream title, echoes the header brand-init treatment.
      const bare = String(t.title || "").replace(/^\d+[a-z]?\.\s*/, "");
      const n = TOPIC_DISPLAY_NUM[t.id];
      const heading = (n ? `<span class="kn-num">${n}.</span> ` : "") + esc(bare);
      return `<article class="kn-article">
        <p class="eyebrow">${esc(t.eyebrow || "Knowledge Library")}</p>
        <h2 class="kn-h kn-h-art">${heading}</h2>
        ${body}
      </article>`;
    }
    function paint() {
      const selectedTopic = lookupTopic(selectedId) || LIBRARY[0];
      root.innerHTML =
        `<div class="kn-lib">
           <aside class="panel kn-nav">
             <button class="kn-nav-toggle" aria-expanded="false" aria-controls="kn-nav-list">
               <span>Topics: ${esc(displayTitle(selectedTopic))}</span>
               <span class="kn-nav-toggle-arrow">▾</span>
             </button>
             <ol class="kn-nav-list" id="kn-nav-list">${navHtml()}</ol>
           </aside>
           <section class="panel kn-content">${contentHtml()}</section>
         </div>`;

      const toggle = root.querySelector(".kn-nav-toggle");
      const list = root.querySelector(".kn-nav-list");

      toggle.addEventListener("click", () => {
        const open = list.classList.toggle("kn-nav-open");
        toggle.setAttribute("aria-expanded", String(open));
      });

      root.querySelectorAll(".kn-nav-btn").forEach((b) => b.addEventListener("click", () => {
        selectedId = b.dataset.topic;
        // On mobile, collapse the nav after selection
        if (isMobile()) {
          list.classList.remove("kn-nav-open");
          toggle.setAttribute("aria-expanded", "false");
        }
        paint();
        const article = root.querySelector(".kn-article");
        if (article) article.scrollIntoView({ behavior: "smooth", block: "start" });
      }));
    }
    paint();
  }

  window.LinKnowledge = { renderKnowledgePage };
})();
