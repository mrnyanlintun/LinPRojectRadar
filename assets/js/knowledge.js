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
      body: "Traditional RAG collapses important distinctions. PCEIF uses five status levels for three reasons. (1) RAG hides the gap between 'slightly off' and 'stalled' — both show as Red. (2) Complete (blue) marks projects that have hit their milestone and transition to closeout governance — different authority, different documentation. (3) Yellow is an early-warning band between Green and Amber: minor variance, still recoverable, requiring a PM weekly check-in before it escalates. Each status maps to a distinct authority/timeframe in the Module 19 matrix."
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
      title: "Module 01: Hybrid Dynamic Simulation",
      body: "Module 01 covers the EVM core: CPI (cost performance, EV/AC) and SPI (schedule performance, EV/PV) against the baseline. On a project's Detail page the Monte Carlo runs 5,000 iterations sampled from a signal-derived Beta-PERT distribution, with P50 and P80 read from the simulated array. P80 is the planning-conservative figure used for contingency and escalation decisions."
    },
    {
      id: "module02",
      keywords: ["module 02", "module 2", "cusum", "spc", "anomaly", "drift", "trend", "control"],
      title: "Module 02: SPC / CUSUM Anomaly Monitor",
      body: "Module 02 watches for accumulating drift. On a project's Detail page CUSUM is a REAL computation: the standard two-sided tabular recursion runs over the project's metric series and a breach is flagged only when the cumulative statistic crosses the decision interval H. It feeds the governance rules, including the 'Anomaly without narrative' conflict when the document record offers no explanation."
    },
    {
      id: "module03",
      keywords: ["module 03", "module 3", "document", "doc risk", "rfi", "submittal", "extraction", "keyword"],
      title: "Module 03: Document-Risk Extraction",
      body: "Module 03 scores risk language in project records (RFIs, submittals, QC comments, procurement notes) using visible keyword rules, the same rules the Manage Projects page runs. The score and the matched excerpt feed the signal ledger. In this demo extraction is rule-based and transparent; there is no live NLP or LLM."
    },
    {
      id: "module10",
      keywords: ["module 10", "module 10", "synthesis", "conflict", "disagreement", "leading", "forecast ahead", "conservative dominance"],
      title: "Module 09: Conservative Dominance (Signal Synthesis)",
      body: "Module 09 classifies disagreement between signal classes instead of averaging it away. Conflict types: Multi-signal red-review, Anomaly without narrative, Forecast ahead of status, Leading document risk, Agreement, low risk, and Mixed early warning. The precedence order is deliberate and documented in decision.js. Conservative dominance: the worst single signal drives the overall state. M09 is the baseline that Modules 10–18 cross-check before Module 19 records the decision."
    },
    {
      id: "module19",
      keywords: ["module 19", "module 09", "abm", "agent", "governance layer", "decision rules", "authority"],
      title: "Module 19: ABM Governance Layer",
      body: "Module 19 is the agent-based governance layer: each authority role (PM, controls lead, program director) is an agent with explicit decision rules. Those rules live in decision.js as pure, readable functions (deriveHealthState, classifyConflict, and deriveDecision), and the Signals page calls them directly. The decision card you see on the Portfolio and Project Detail pages IS this module's output. Module 19 is the LAST module in the stack, the artefact that survives the reporting cycle."
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
      body: "Pick a project and document type, then paste or upload text (.txt / .csv / PDF-extracted text). The app runs the same visible keyword rules as Module 03, shows exactly which rule fired and the proposed signal delta, and nothing changes until a human clicks Approve. Reject discards the proposal. Every ingest event is logged."
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

  /* ---------- Modules 04-08, 11, Method Library accordion entries ---------- */
  TOPICS.push(
    {
      id: "module04",
      keywords: ["module 04", "module 4", "pert", "program evaluation", "network criticality", "triangular", "path criticality"],
      title: "Module 04: Program Evaluation & Review Technique (PERT)",
      body: "PERT is a stochastic network scheduling method. Each activity has three duration estimates, optimistic (a), most likely (m), and pessimistic (b), and is sampled from a triangular distribution. The classic deterministic three-point estimate is te = (a + 4m + b) / 6; the simulation aggregates the dominant path across 5,000 runs. P80 duration is the conservative finish (80% of runs at or under). The path-criticality index is the fraction of runs in which the structural path was on the critical path, the higher it is, the less float you have to absorb a slip. In this implementation a lower project SPI widens the pessimistic bound, so an already-drifting schedule grows a fatter P80 tail. Thresholds: Green P80 within baseline; Amber P80 up to +20%; Red P80 > +20%.",
    },
    {
      id: "module05",
      keywords: ["module 05", "module 5", "lob", "line of balance", "production velocity", "crew", "buffer"],
      title: "Module 05: Line of Balance (LOB)",
      body: "LOB tracks production velocity for sequential, repetitive work, grading runs ahead of paving, paving runs ahead of striping, and so on. Each crew has a rate in units/day; the buffer is the schedule gap between leader and follower at every unit. When the follower's rate slips, that buffer compresses unit by unit and a crew-on-crew collision is being telegraphed before EVM moves. Here, lower project SPI slows the follower (paving) so the minimum crew buffer shrinks. Buffer collapse is a leading schedule indicator: it shows up in the LOB chart before it shows up in CPI or SPI. Thresholds: Green buffer > 3 days; Amber 1.5–3 days; Red ≤ 1.5 days.",
    },
    {
      id: "module06",
      keywords: ["module 06", "module 6", "ccpm", "critical chain", "buffer", "fever chart"],
      title: "Module 06: Critical Chain Project Management (CCPM)",
      body: "CCPM (Goldratt) aggregates the safety margin embedded in individual activity estimates into a single project buffer at the end of the critical chain. The fever chart plots buffer-consumed % against chain-complete %. Two thresholds drive the zones: the amber line tracks chain completion (buffer consumed ≥ % complete), burning buffer at the same rate progress is being made; the red line sits a third of the remaining range above (buffer consumed ≥ % complete + (100 − % complete) / 3), burning buffer faster than the chain can complete. Crossing into red means the buffer will run out before the work does. Thresholds: Green below the amber line; Amber buffer consumed ≥ % complete; Red buffer consumed ≥ % complete + (100 − % complete) / 3.",
    },
    {
      id: "module07",
      keywords: ["module 07", "module 7", "rcf", "reference class", "forecasting", "flyvbjerg", "debias", "optimism bias"],
      title: "Module 07: Reference Class Forecasting (RCF)",
      body: "Reference Class Forecasting comes from Bent Flyvbjerg's research on optimism bias in large infrastructure projects: bottom-up estimates systematically underestimate cost because they reason from the inside view (this project's plan) rather than the outside view (how comparable projects have actually performed). RCF replaces the inside-view estimate with an empirical prior, the distribution of historical overrun multipliers from a comparable reference class. This implementation uses an airport-infrastructure multiplier set [1.00 to 1.52]; the P80 multiplier is the conservative debiasing factor applied to BAC. The debiasing factor is the multiplier itself: x1.38 means the outside view says comparable projects finished 38% over their baseline. The P80 RCF prior is the realistic planning budget to compare against the bottom-up EAC. Thresholds: Green P80 within +10% of BAC; Amber +10–25%; Red > +25%.",
    },
    {
      id: "module08",
      keywords: ["module 08", "module 8", "dsm", "design structure matrix", "rework", "propagation", "arch", "structural", "mep", "dependency"],
      title: "Module 08: Design Structure Matrix (DSM)",
      body: "A DSM captures information-flow dependencies between work elements as a square matrix: each off-diagonal entry A[i][j] is the strength of i's dependence on j. Here the elements are the three design disciplines, Architectural, Structural, MEP, and the off-diagonals encode how much a unit change in one cascades into the others. Architectural decisions flow downstream into both Structural and MEP, so an arch scope change ripples through the matrix; structural and MEP changes also feed back. The simulation propagates a unit architectural change vector through the matrix for four passes and accumulates the rework absorbed in each discipline. The total cumulative rework multiplier is the coordination cost: a multiplier above 2.5 indicates that one unit of arch change is generating more than 2.5 units of downstream rework, high coordination risk. Thresholds: Green rework multiplier ≤ 2.5; Amber > 2.5.",
    },
    {
      id: "module11",
      keywords: ["module 11", "module 11", "dst", "dempster", "shafer", "belief", "evidence combination", "conflict mass", "bpa"],
      title: "Module 11: Dempster-Shafer Evidence Combination (DST)",
      body: "Dempster-Shafer Theory (DST) is a mathematical framework for reasoning under uncertainty when evidence comes from multiple independent sources. Unlike conservative dominance (Module 09), which takes the worst single signal, DST combines all four signal classes into a belief distribution over {Green, Amber, Red, Unknown}. Each source assigns a basic probability assignment (BPA), a mass function over subsets of the frame of discernment. Dempster's combination rule then merges sources iteratively, redistributing conflict mass. The conflict mass K measures how much the sources disagree: K > 0.3 is flagged as high inter-signal disagreement, which is itself a governance signal. Academic context: Dempster (1967) and Shafer (1976). When DST agrees with Module 09, both methods corroborate each other. When they diverge, the disagreement is a finding: it tells the governance layer that the evidence picture is genuinely ambiguous rather than clear-cut, and that no single framing captures the full risk.",
    },
    {
      id: "module12",
      keywords: ["module 12", "rough sets", "rough set theory", "lower approximation", "upper approximation", "boundary region", "indeterminate", "pawlak"],
      title: "Module 12: Rough Set Theory Classification",
      body: "Rough Set Theory (Pawlak, 1982) provides a mathematical framework for classifying objects when available information is incomplete or imprecise. The core insight is that some concepts, like 'this project is Green', cannot be precisely defined with available attributes. Instead, rough sets define three regions: the lower approximation contains all objects (states) that definitely belong to the concept (over 75% of signals agree); the upper approximation contains all objects that possibly belong; and the boundary region, upper minus lower, is the indeterminate zone where evidence is insufficient to classify with certainty. A project falls in the definite Green region when the preponderance of evidence is unambiguous; it falls in the boundary when signals are mixed and classification is uncertain. A wide boundary region is itself a governance signal: it means the evidence does not yet support a confident classification. Unlike DST (Module 10), rough sets do not assign probability masses, they provide a set-theoretic answer: yes, possibly, or unknown. Thresholds: Definite requires > 75% signal agreement for a state; any support places a state in the upper approximation.",
    },
    {
      id: "module13",
      keywords: ["module 13", "neutrosophic", "neutrosophic logic", "truth", "indeterminacy", "falsity", "t i f", "smarandache"],
      title: "Module 13: Neutrosophic Logic",
      body: "Neutrosophic Logic (Smarandache, 1995) extends fuzzy logic by introducing three independent truth-value dimensions: Truth (T), Indeterminacy (I), and Falsity (F). Unlike classical logic (T + F = 1) and fuzzy logic (T + F = 1 as a constraint), neutrosophic values are independent, T + I + F need not equal 1, and can exceed 1 or be less than 1. This is a deliberate feature: it models genuine epistemic uncertainty as a separate dimension rather than forcing it to be the residual of known truths and falsehoods. In project risk terms: T represents the degree to which the evidence supports a given status; F represents evidence against it; I represents the portion of evidence that is genuinely undetermined or contradictory, measurement noise, missing data, or conflicting signals that cannot be resolved by collecting more of the same kind of data. High indeterminacy (I > 30%) is a governance signal: it means the evidence architecture itself needs strengthening before a confident classification is possible, not just that the project is 'in between' Green and Red. This module combines the four primary signal classes disjunctively for T (union of evidence) and conjunctively for I and F, producing a three-component characterization of the current signal package.",
    },
    {
      id: "module14",
      keywords: ["module 14", "interval fuzzy", "interval-valued fuzzy", "fuzzy interval", "membership interval", "uncertainty interval", "ifs"],
      title: "Module 14: Interval-valued Fuzzy Sets",
      body: "Interval-valued Fuzzy Sets (IVFS) extend classical fuzzy sets by representing membership as a range [lower, upper] rather than a single value. The interval reflects measurement uncertainty in the underlying data, the range of possible membership values given the precision of the inputs. For airport construction EVM, the primary sources of input uncertainty are: Schedule of Values (SoV) line-item accuracy of approximately +/-2% of contract value affecting Earned Value, and Pay Application rounding of approximately +/-1% affecting Actual Cost. These compound into a CPI/SPI uncertainty range of approximately +/-3 percentage points. IVFS propagates this uncertainty through the fuzzy membership functions for Green, Amber, and Red states, producing an interval rather than a point estimate. A wide interval signals that the current input precision is insufficient to reliably distinguish between adjacent states, e.g., a Green/Amber boundary crossing falls within the uncertainty band. The uncertainty width metric summarizes the total interval spread: High (> 0.30 width) means the classification is sensitive to input noise; Moderate (0.15-0.30) means some sensitivity; Low (< 0.15) means the signal package is sufficiently precise for reliable classification. References: Sambuc (1975); Zadeh (1975); Turksen (1986).",
    },
  );

  /* ---------- Knowledge Library, 11 narrative topics with formulas + SVG ---------- */
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

  // PCEIF signal-to-action flow (Topic 1), two rows so the diagram is large
  // and readable: 4 boxes across the top, 3 boxes centred underneath, with an
  // L-bend connector from box 4 down to box 5.
  function svgPceifFlow() {
    const row1 = [
      "Documents + Schedule + Cost",
      "Signal Generation: Modules 01-08",
      "Baseline Synthesis: Module 09",
      "Evidence Combination: Modules 10-18"
    ];
    const row2 = [
      "Governance Decision: Module 19",
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
    let out = `<svg viewBox="0 0 ${w} ${h}" width="100%" height="auto" class="kn-svg" role="img" aria-label="Signal stack of 19 modules feeding the governance decision">`;
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
    out += `<text x="620" y="142" text-anchor="middle" class="kn-svg-t" fill="var(--text)" font-weight="700">Module 09</text>`;
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

  // Module 10 agreement map (Topic 7)
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
        <p class="kn-lead">PCEIF, the <strong>Public Capital EVM Intelligence Framework</strong>, converts the multi-model signals that a public capital program already generates into a structured, accountable governance action with a named authority and a documented audit trail.</p>

        <h3>The problem it solves</h3>
        <p>Standard Earned Value Management produces excellent data. It does not produce a decision. A PM looking at CPI 0.88 in period 4 has no structured path to a defensible escalation: who must act, on what timeframe, with what documentation, under whose authority. The data exists; the governance link is missing.</p>
        <p>PCEIF closes that gap. Signals trigger an explicit rule set; the rule set returns a specific action, a specific authority, and the documentation required. The PM still records the decision, the framework simply makes the recommendation traceable.</p>

        <h3>Two-layer architecture</h3>
        <p>Nineteen signal modules feed two layers of governance. Modules 01 to 08 generate signals. Module 09 synthesizes them into a baseline state. Modules 10 to 18 quantify confidence by cross-checking the baseline through nine independent evidence-combination methods. Module 19 produces the governance decision card with a named authority and required documentation.</p>
        <ul class="kn-list">
          <li><strong>Layer 1, Agency Governance.</strong> Sets the policy framework: the authority matrix, escalation thresholds, fairness rules, audit requirements. Established by the program owner; not changed per project.</li>
          <li><strong>Layer 2, PM Decision Architecture.</strong> Takes that policy and the project's signal package and surfaces, for each reporting cycle, the specific action the PM should record (or override, with rationale).</li>
        </ul>

        <h3>Signal-to-action mechanism</h3>
        ${svgPceifFlow()}

        <h3>What's different from standard EVM</h3>
        <ul class="kn-list">
          <li><strong>Standard EVM:</strong> compute CPI / SPI → report to management.</li>
          <li><strong>PCEIF:</strong> compute 19 signal classes → detect conflict → classify the conflict → surface the action, authority, and documentation, <em>before</em> the next reporting cycle closes.</li>
        </ul>

        <h3>The role of AI</h3>
        <p>AI explains and summarizes. It does <strong>not</strong> make governance decisions. Every recommended action requires a named human approval before it is recorded; the AI's job is to make that approval well-informed, not to replace it. This is a design constraint, not a performance limitation.</p>
      `,
    },
    {
      id: "five-status",
      title: "2. Why Five Status Levels",
      eyebrow: "Governance model",
      build: () => `
        <p class="kn-lead">Traditional RAG (Red-Amber-Green) systems use three states. PCEIF uses five — Complete, Green, Yellow, Amber, Red — for three concrete reasons.</p>

        <h3>1. RAG collapses important distinctions</h3>
        <p>A project that is slightly behind schedule and a project that has completely stalled both show as Red under RAG. A PM responding to a slightly-behind project applies very different actions than one responding to a stalled project. Collapsing them to the same status loses the governance signal.</p>

        <h3>2. The Complete state enables closeout governance</h3>
        <p>Public capital programs have a distinct closeout phase — work is done, but sign-off, commissioning, and documentation must be completed. A Green state implies active monitoring is still required. A Complete state signals the project has met its targets and transitions to closeout governance — different authority, different documentation requirements.</p>

        <h3>3. Yellow provides an early warning band</h3>
        <p>The gap between Green (all good) and Amber (significant risk) is too wide. A project moving from Green to Amber has often already been in trouble for 2-3 reporting periods. Yellow captures the early warning zone — minor variance, still recoverable, but requiring PM attention before the next cycle. This is the band where early intervention prevents escalation.</p>

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
        <p>Six or more statuses create decision paralysis — the PM spends time debating whether a project is "Orange-Amber" vs "Deep-Amber" rather than acting. Five states map cleanly to five distinct governance responses with different authorities and timeframes.</p>
      `,
    },
    {
      id: "stack",
      title: "3. The Signal Stack: 19 Modules",
      eyebrow: "Architecture",
      build: () => `
        <p class="kn-lead">The signal stack splits into five tiers. The first two compute and govern; the next three extend coverage to specialised construction and design risks, then layer multiple evidence-combination and uncertainty-reasoning frameworks across the result.</p>
        ${svgSignalStack()}

        <h3>Modules 01–03, Quantitative EVM Analysis</h3>
        <ul class="kn-list">
          <li><strong>Module 01: Monte Carlo EAC Forecast.</strong> EVM core (CPI, SPI) plus the 5,000-iteration Beta-PERT P80 EAC forecast.</li>
          <li><strong>Module 02: CUSUM Anomaly Monitor.</strong> Two-sided tabular CUSUM over the SPI series; breach when cumulative drift exceeds the decision interval H = 5σ.</li>
          <li><strong>Module 03: Document Risk Extraction.</strong> Transparent keyword rules score risk language across RFIs, submittals, OAC minutes, and correspondence.</li>
        </ul>

        <h3>Modules 04–08, Extended Construction & Design Simulation</h3>
        <ul class="kn-list">
          <li><strong>Module 04: PERT</strong> network criticality (P80 duration, path criticality index).</li>
          <li><strong>Module 05: Line of Balance</strong> production velocity (crew-buffer collapse as a leading indicator).</li>
          <li><strong>Module 06: CCPM</strong> buffer-health fever chart (buffer consumed vs chain complete).</li>
          <li><strong>Module 07: Reference Class Forecasting</strong> cost prior (outside-view debiasing against an empirical reference class).</li>
          <li><strong>Module 08: Design Structure Matrix</strong> rework propagation (architectural change cascades to MEP).</li>
        </ul>

        <h3>Module 09, Baseline Synthesis</h3>
        <ul class="kn-list">
          <li><strong>Module 09: Conservative Dominance.</strong> Classifies the disagreement between signal classes (six conflict types) rather than averaging it away. Worst signal wins. This is the governance baseline that Modules 10–18 cross-check.</li>
        </ul>

        <h3>Modules 10–18, Evidence Combination &amp; Uncertainty Reasoning</h3>
        <ul class="kn-list">
          <li><strong>Module 10: Dempster-Shafer</strong> (1967/1976). Belief masses + conflict mass K.</li>
          <li><strong>Module 11: Rough Sets</strong> (1982). Lower / upper approximations and boundary region.</li>
          <li><strong>Module 12: Neutrosophic Logic</strong> (1995). Truth / Indeterminacy / Falsity as independent dimensions.</li>
          <li><strong>Module 13: Interval-valued Fuzzy Sets</strong> (1975/1986). Membership intervals propagating EVM measurement tolerances.</li>
          <li><strong>Module 14: Z-numbers</strong> (2011). Each signal as a (Restriction, Reliability) pair.</li>
          <li><strong>Module 15: PLTS</strong> (2016). Per-source probability distribution over linguistic states.</li>
          <li><strong>Module 16: Plithogenic Sets</strong> (2018). Contradiction-degree weighting against the dominant value.</li>
          <li><strong>Module 17: Belief Rule Base</strong> (2006/2023). Expert IF-THEN rules with belief-distribution consequents.</li>
          <li><strong>Module 18: Quantum Probability</strong> (2012). Amplitude state vector with phase-angle interference.</li>
        </ul>

        <h3>Module 19, Governance Decision Output</h3>
        <ul class="kn-list">
          <li><strong>Module 19: ABM Governance Layer.</strong> Consumes the M09 baseline plus the M10–18 cross-checks and maps (state × conflict × sector) to action, authority, and documentation. Implemented as pure functions in <code>decision.js</code>. This is the LAST module, the artefact that survives the reporting cycle.</li>
        </ul>

        <p class="kn-callout">Outputs from Modules 01–08 feed Module 09 (Conservative Dominance). M09 is the governance baseline; Modules 10–18 each provide an independent lens to compare against it. Module 19 consumes both and produces the recorded decision card. Divergence between Modules 10–18 and M09 is itself a governance-relevant finding that the PM must own explicitly.</p>
      `,
    },
    {
      id: "pm-advice",
      title: "3. How the 19 Modules Advise the PM",
      eyebrow: "PM decision protocol",
      build: () => `
        <p class="kn-lead">Nineteen modules is a lot. This section explains how the modules are layered, what the PM reads first, and what Lin will say in each confidence band. The point of the stack is not to overwhelm, it is to make the recommended action defensible.</p>

        <h3>The five tiers</h3>
        <ul class="kn-list">
          <li><strong>Tier 1: Modules 01–03: Quantitative EVM.</strong> Compute what IS happening on cost, schedule, and field documents. These are the inputs everything else stands on.</li>
          <li><strong>Tier 2: Modules 04–08: Extended simulation.</strong> Leading indicators that surface schedule and design risks BEFORE EVM shows the problem (network criticality, crew buffer, fever chart, outside-view priors, rework cascades).</li>
          <li><strong>Tier 3: Module 09: Baseline synthesis.</strong> Conservative dominance classification, the worst single signal wins. This is the governance baseline state.</li>
          <li><strong>Tier 4, Modules 10 to 18: Evidence combination.</strong> Nine independent uncertainty-reasoning frameworks (Dempster-Shafer, Rough Sets, Neutrosophic, Interval Fuzzy, Z-numbers, PLTS, Plithogenic, BRB, Quantum) confidence-check the M09 baseline.</li>
          <li><strong>Tier 5: Module 19: Governance decision.</strong> Named-authority action, required documentation, fairness gate, the artefact that survives the reporting cycle.</li>
        </ul>

        <h3>PM decision protocol</h3>
        <ol class="kn-list">
          <li><strong>Step 1.</strong> Read Module 19 (Governance recommendation). This is the action.</li>
          <li><strong>Step 2.</strong> Check Module 09 (Conservative dominance). This is the baseline state.</li>
          <li><strong>Step 3.</strong> Count how many of Modules 10–18 agree with Module 09:
            <ul class="kn-list">
              <li>8–9 agree: <strong>HIGH CONFIDENCE</strong>, act on the Module 19 recommendation.</li>
              <li>5–7 agree: <strong>MODERATE CONFIDENCE</strong>, act, but document the uncertainty.</li>
              <li>&lt; 5 agree: <strong>LOW CONFIDENCE</strong>, investigate before acting.</li>
            </ul>
          </li>
          <li><strong>Step 4.</strong> Read specific divergences:
            <ul class="kn-list">
              <li>M11 (Rough Sets) borderline → get more data.</li>
              <li>M13 (Interval Fuzzy) wide interval → verify EVM inputs.</li>
              <li>M14 (Z-numbers) low reliability → request verified data.</li>
              <li>M15 (PLTS) P(Red) &lt; 60% → document probability in rationale.</li>
              <li>M18 (Quantum) destructive interference → signals cancel, own the ambiguity.</li>
            </ul>
          </li>
          <li><strong>Step 5.</strong> Record the decision card with rationale and confidence level.</li>
        </ol>

        <h3>PM-facing language, what Lin should say</h3>
        ${ragTable(
          ["Scenario", "Recommended phrasing"],
          [
            [{ label: "High confidence Green", color: RAG.green }, "All signal methods agree this project is on track. Routine monitoring is appropriate."],
            [{ label: "High confidence Amber", color: RAG.amber }, "Multiple methods flag this project as needing attention. The signals are consistent, a weekly review with the controls lead is recommended before the next reporting cycle."],
            [{ label: "High confidence Red", color: RAG.red }, "The project requires escalation. All evidence methods confirm the classification. A recovery plan review with the program director is required within 48 hours."],
            ["Low confidence any state", "The classification is [state] but the signal methods disagree. [Specific reason]. Investigate the discrepancy before recording a formal governance action."],
            ["Destructive interference", "The signals are genuinely contradictory. The governance layer recommends [action] but the evidence base is divided, document the uncertainty explicitly."],
          ]
        )}

        <p class="kn-callout">The point of the stack is that the recommended action is defensible, not just to the PM, but to a future auditor reading the decision card. "Module 19 recommended Red-review; 8 of 9 evidence methods agreed with the M09 baseline; the contractor fairness gate was acknowledged on [date]" reads cleanly. "It looked Red so we escalated" does not.</p>
      `,
    },
    {
      id: "module01",
      title: "4. Module 01: Monte Carlo EAC Forecast",
      eyebrow: "Module 01",
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
      title: "5. Module 02: CUSUM Anomaly Monitor",
      eyebrow: "Module 02",
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
        <p>A CUSUM breach hands the question to Module 09 (Conservative Dominance) and ultimately Module 19 (ABM Governance Layer). The monitor never acts on its own; it produces evidence the governance layer routes. If the breach has no document narrative behind it, the conflict type is "Anomaly Without Narrative", itself a finding worth surfacing.</p>
      `,
    },
    {
      id: "module03",
      title: "6. Module 03: Document Risk Extraction",
      eyebrow: "Module 03",
      build: () => `
        <p class="kn-lead">EVM lags field conditions by weeks. An RFI log showing 20 open disputes in period 4 predicts a CPI collapse in period 6, but EVM will not show that collapse until it has already happened. Document risk is the leading signal.</p>

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
        <p>Keyword extraction is rule-based, not semantic. A sophisticated contractor writes around keyword rules. The score is a <em>leading indicator</em>, never a verdict. PCEIF treats Module 03 Red as a flag that requires Module 09 corroboration before it drives an action, never as a standalone trigger.</p>
      `,
    },
    {
      id: "module04",
      title: "7. Module 04: PERT Network Criticality",
      eyebrow: "Module 04",
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

        <h3>How it differs from Module 01</h3>
        <p>Module 01 (Monte Carlo EAC) randomises cost performance; Module 04 randomises activity durations along the schedule network. Module 01 answers "what will it cost?"; Module 04 answers "when will it finish?". Both contribute independent evidence to Module 09 synthesis.</p>
      `,
    },
    {
      id: "module05",
      title: "8. Module 05: Line of Balance Production Velocity",
      eyebrow: "Module 05",
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
      title: "9. Module 06: CCPM Buffer Health",
      eyebrow: "Module 06",
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
      title: "10. Module 07: Reference Class Forecasting",
      eyebrow: "Module 07",
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
      title: "11. Module 08: DSM Rework Propagation",
      eyebrow: "Module 08",
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
      title: "12. Module 09: Conservative Dominance (Signal Synthesis)",
      eyebrow: "Module 09 · baseline synthesis",
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

        <h3>How it differs from Modules 10–18</h3>
        <p>Module 09 is the governance baseline: conservative dominance with explicit conflict typing. Modules 10–18 each provide an independent evidence-combination lens (probabilistic, set-theoretic, fuzzy, quantum). When Module 09 and any of 10–18 disagree, the disagreement itself is what gets recorded, the governance layer owns the residual uncertainty rather than picking a method. Module 19 (ABM Governance) consumes both the M09 baseline and the M10–18 cross-checks to produce the actionable decision card.</p>
      `,
    },
    {
      id: "module10",
      title: "13. Module 10: Dempster-Shafer Evidence Combination",
      eyebrow: "Module 10 · evidence theory",
      build: () => `
        <p class="kn-lead">Dempster-Shafer Theory (DST) is a mathematical framework for reasoning under uncertainty with multiple independent sources. Each source assigns a basic probability assignment (BPA) over a frame of discernment, here {Green, Amber, Red, Unknown}. Dempster's rule combines sources and normalises out the conflict mass K.</p>

        <h3>What DST adds beyond conservative dominance</h3>
        <p>Module 09 takes the worst single signal. DST weights all four evidence sources and produces explicit belief masses for every state. When a project is Green by two signals, Amber by one, Red by one, conservative dominance outputs Red; DST may output Amber if the combined belief mass for Amber is highest, and the conflict mass K quantifies exactly how much the sources disagreed. That conflict mass is itself a governance-relevant finding.</p>

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
      title: "14. Module 11: Rough Sets Classification",
      eyebrow: "Module 11 · set theory",
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
      title: "15. Module 12: Neutrosophic Logic",
      eyebrow: "Module 12 · three-valued logic",
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
      title: "16. Module 13: Interval-valued Fuzzy Sets",
      eyebrow: "Module 13 · fuzzy logic",
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
      title: "17. Module 14: Z-numbers",
      eyebrow: "Module 14 · reliability-weighted evidence",
      build: () => `
        <p class="kn-lead">A Z-number is a pair (Restriction, Reliability). The restriction is the signal's classification; the reliability is how trustworthy the source data is. A CPI from a verified pay application is more trustworthy than one estimated from a schedule update, and the governance recommendation should reflect that, not just the headline state.</p>

        <h3>What Z-numbers add</h3>
        <p>Every other synthesis method treats all sources as equally reliable. Z-numbers make reliability a first-class input: a Red signal from a low-reliability source contributes less than a Red from a high-reliability source. This is the same epistemic structure auditors use informally; Module 14 makes it explicit in the audit record.</p>

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
      title: "18. Module 15: Probabilistic Linguistic Term Sets (PLTS)",
      eyebrow: "Module 15 · probabilistic linguistics",
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
      title: "19. Module 16: Plithogenic Sets",
      eyebrow: "Module 16 · contradiction-degree weighting",
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
      title: "20. Module 17: Belief Rule Base (BRB)",
      eyebrow: "Module 17 · expert IF-THEN rules",
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
      title: "21. Module 18: Quantum Probability",
      eyebrow: "Module 18 · amplitude interference",
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
      title: "22. Module 19: ABM Governance Layer",
      eyebrow: "Module 19 · decision output (LAST)",
      build: () => `
        <p class="kn-lead">"Agent-based" here means each authority role (PM, controls lead, program director) is modelled as an agent with explicit, executable decision rules. In <code>decision.js</code> those rules are pure functions, readable, testable, and auditable. Nothing is learned; everything is documented. Module 19 is the LAST module because it consumes the M09 baseline plus the M10–18 evidence checks and produces the recorded decision card.</p>

        <h3>Why the authority matrix exists</h3>
        <p>PCEIF operates under two layers. Layer 1 is the agency governance policy: the program owner sets the authority matrix before any project starts. Layer 2 is the PM decision architecture: it uses that matrix to route each signal package to the correct authority. The matrix is not hardcoded. A different agency can configure different thresholds and authorities. What PCEIF provides is the routing logic and the audit trail.</p>

        <h3>The authority matrix</h3>
        ${ragTable(
          ["State", "Authority", "Timeframe", "Basis"],
          [
            [{ label: "Complete", color: "#4ea0ff" },
             "Project Manager / Controls Lead",
             "Closeout documentation",
             "Milestone achieved and signed off — transition to closeout governance"],
            [{ label: "Green", color: RAG.green },
             "Project Manager / Controls Lead",
             "Monthly reporting cycle",
             "Routine performance within delegated PM authority"],
            [{ label: "Yellow", color: "#f0c040" },
             "Project Manager",
             "Weekly check-in",
             "Minor variance — early-warning band, investigate before next cycle"],
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

        <h3>Why Module 19 is the LAST module</h3>
        <p>The position is deliberate. The PM should read Module 19 first as the recommended action, then walk backward through the evidence chain to confirm. Modules 01–08 supply the inputs; Module 09 is the baseline classification; Modules 10–18 are the confidence check; Module 19 is what gets recorded. Placing the decision artefact at the end of the stack reflects the audit-trail order: the recommendation is the last thing the PM commits to, not the first thing they see.</p>
      `,
    },
    {
      id: "fairness",
      title: "23. The Fairness Gate",
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
      title: "24. The Decision Card and Audit Trail",
      eyebrow: "Accountable record",
      build: () => `
        <p class="kn-lead">The decision card is the single artefact that captures, for each governed decision, who decided, what they decided, on what evidence, under what authority, and on what date. It is the record that survives the project, the basis for independent audit, dispute resolution, and program-level reporting.</p>

        <h3>Decision card fields</h3>
        ${ragTable(
          ["Field", "Why it matters"],
          [
            ["Derived state", "The PCEIF rule output, Green / Amber / Red-review / Critical, that triggered this card."],
            ["Conflict type", "The named disagreement Module 09 surfaced; tells the reviewer what to investigate."],
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

  window.LIN_KNOWLEDGE = { terms: TERMS, glossary: GLOSSARY, topics: TOPICS, library: LIBRARY };

  /* ---------- knowledge page rendering, two-panel navigator + content ---------- */
  function renderKnowledgePage() {
    const root = document.getElementById("knowledge-root");
    if (!root) return;
    let selectedId = (LIBRARY[0] && LIBRARY[0].id) || "pceif";

    function isMobile() { return window.innerWidth <= 640; }

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
      const selectedTopic = LIBRARY.find((x) => x.id === selectedId) || LIBRARY[0];
      root.innerHTML =
        `<div class="kn-lib">
           <aside class="panel kn-nav">
             <button class="kn-nav-toggle" aria-expanded="false" aria-controls="kn-nav-list">
               <span>Topics: ${esc(selectedTopic.title)}</span>
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
