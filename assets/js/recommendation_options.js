/* ============================================================
   Opus Gubernatio — recommendation_options.js
   ------------------------------------------------------------
   THE COURSES OF ACTION OPEN TO THE PROJECT MANAGER, AND WHAT
   FOLLOWS FROM EACH, BUILT FROM THE STORED RESULT ONLY.

   One generator, two surfaces: the Governance Decision card on
   the project detail page (operational) and the decision support
   the research participant responds to after the reveal. Both
   call it at DISPLAY TIME, both read the same stored row, so the
   same evidence produces the same words on both.

   THE RULE THIS FILE EXISTS TO KEEP. Every consequence stated
   here is either (a) a figure read back from the stored result,
   (b) a statement about where the decision moves, taken from a
   figure the stored result holds, or (c) an explicit statement
   that the platform does not hold what would be needed to say.
   There is no fourth kind of sentence. A consequence that reads
   well and cannot be traced is the failure this file avoids.

   NOTHING RECOMPUTES. This file calls no model. It reads
   `module_results` and `signal_inputs` off the primed stored row
   and formats them.

   Plain global, no module system, like every other file here.
   ============================================================ */
(function (global) {
  "use strict";

  /* ---------------------------------------------------------- formatting */

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  /* Money to the nearest dollar with thousands separators. The stored value is not altered;
     only its presentation is. A non-finite value never reaches here. */
  function money(v) {
    var n = Math.round(Number(v));
    return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }

  function isNum(v) {
    return v !== null && v !== undefined && v !== "" && Number.isFinite(Number(v));
  }

  /* The one phrase for "the platform does not hold this". Used verbatim everywhere so a
     reader learns to recognise it, and so a check can count it. */
  function unknown(what) {
    return "Not established: " + what + ".";
  }

  /* ---------------------------------------------------------- reading the stored row */

  function modulesOf(result) {
    var out = {};
    var mods = result && result.module_results;
    if (!Array.isArray(mods)) return out;
    mods.forEach(function (m) {
      if (m && m.method_class) out[m.method_class] = m;
    });
    return out;
  }

  /* Descriptive titles. NAMING_AUTHORITY: no module id, no number, purpose only. */
  var ACTION_TITLE = {
    monitor: "Keep the project under routine monitoring",
    investigate: "Investigate before taking a formal step",
    escalate: "Escalate to management review"
  };
  var ACTION_WHAT = {
    monitor: "Carry the position into the next reporting period unchanged and record the "
      + "signals as they stand.",
    investigate: "Open the variance inside the project: test the figures behind the forecast "
      + "and establish what is driving them before any formal step is taken.",
    escalate: "Put the position formally in front of management as a matter for review, "
      + "rather than settling it inside the project."
  };

  /* ---------------------------------------------------------- the exposure sentence
     The one figure every option is weighed against: what the analytical layer says this
     project finishes at. Cost Risk Analysis stores an integer estimate and a percentage;
     Monte Carlo EAC stores the same quantity from its own simulation. Either is quoted
     verbatim. When neither computed, the exposure is stated as not established rather than
     replaced with an adjective. */
  function exposure(mods, si, docEv) {
    /* NO FORECAST FIGURE APPEARS WITHOUT AN INPUT BEHIND IT.

       This used to print `Cost_Risk_Analysis.p80_eac` as "an eightieth percentile estimate at
       completion", falling back to `Monte_Carlo.p80_eac`. Neither has a distribution behind it.
       The first computes its whole spread as `max(0.03, abs(1 - cpi)) * 0.5`, multiplied by a
       literal 1.28; the second from literal weights and a literal Beta-PERT spread. The
       document sets supply no distribution and no percentile of any kind, so those figures are
       not measurements of the project they are printed beside. On a design project whose
       authored estimate at completion was 4,835,600 dollars this produced 10,555,811.

       So the percentile is not printed. What IS printed is the exposure the RISK REGISTER
       supports: the sum of probability times cost impact over the risks that stated both
       numbers, which is arithmetic the register itself implies and which names the risks it
       came from. Where the register supports none, the exposure is not established and the
       card says so, which is the state this card was already built to express.

       The modules are not changed by any of this: changing their arithmetic was out of scope,
       and what a module stores is still stored. This decides only what a reader is shown as a
       finding about their project. */
    var reg = docEv && docEv.register;
    var exp = reg && reg.exposure;
    if (exp && isNum(exp.expected_value) && exp.usable_count > 0) {
      return {
        text: "a risk exposure of " + money(exp.expected_value) + " dollars, being the sum of "
          + "probability times cost impact across the " + exp.usable_count + " risk"
          + (exp.usable_count === 1 ? "" : "s") + " in the register that state both",
        known: true
      };
    }
    return { text: null, known: false, refusedForecast: true };
  }

  /* ---------------------------------------------------------- build */

  /**
   * Build the option set for one stored result.
   * Returns { available, reason, options[], recommendation, unknowns[] }.
   * `available:false` means the platform does not hold a set of courses of action for this
   * project, and the caller must say so rather than draw an empty frame.
   */
  function build(result) {
    var mods = modulesOf(result);
    var si = (result && result.signal_inputs) || {};
    var regret = mods.Regret_Minimization;
    var scores = regret && regret.expected_regret;

    // Run 1 remediation (remediation_decisions_answered.md 1.1, 1.2; the run-1 prompt Part 3).
    // The seven CORE modules vote on project status on an interim basis; every other module,
    // including the one that scores these courses of action, does not -- and non-voting means
    // excluded from generated recommendation text and courses of action, not only from the
    // status fusion. `votes` is a new field on the stored module result (server/app/simulation/
    // registry.py run_all()); a module computed before this run has no such field and reads as
    // undefined, never as false, so this only fires once a period has actually been recomputed
    // under the new scope.
    if (regret && regret.votes === false) {
      return {
        available: false,
        // The word "validated" was removed here by Run 4 (the freeze point). It claimed a
        // standard nothing on this platform meets: band boundaries are sourced to published
        // literature, and false-positive and false-negative performance has never been measured
        // on labelled cases. The sentence now says what is true, which is which measures
        // contribute to project status. The substance a participant reads is unchanged.
        reason: "The analysis that scores the courses of action against each other is not one "
          + "of the measures that contribute to project status, so its scoring is not carried "
          + "into a recommended course of action here. Its own finding still appears on the "
          + "signal ledger.",
        nonVoting: true,
        options: [],
        recommendation: null,
        unknowns: []
      };
    }

    if (!scores || typeof scores !== "object" || Object.keys(scores).length < 2) {
      // THREE DIFFERENT FACTS REACH HERE AND THEY MUST NOT SHARE A SENTENCE.
      //
      // 1. The row this surface was given carries no module results at all. That happens
      //    while the page still holds the four-field status projection and the complete row
      //    has not been read back yet. NOTHING is known about any module from such a row,
      //    so claiming the scoring analysis did not compute is asserting a fact not in
      //    evidence, and it was doing so on projects whose ledger showed that very module
      //    with a status. Say the analysis has not been read back yet.
      // 2. The module is present but its action-bearing fields were withheld by the reveal
      //    gate. This is now reachable on the RESEARCH path only: an operational project is
      //    no longer gated (server/app/documents.py, `project_under_research_protocol`), so
      //    a project manager reading their own project can never see this sentence. It stays
      //    because the research instrument depends on it.
      // 3. The row carries module results and the scoring module is not among them: it
      //    abstained. That, and only that, is "did not compute".
      var hasModuleResults = Array.isArray(result && result.module_results);
      var withheld = regret && regret.recommendation_withheld;
      var reason;
      if (!hasModuleResults) {
        reason = "The analysis for this period has not been read back yet, so the courses of "
          + "action are not available on this screen. Nothing here says whether the analysis "
          + "that scores them ran.";
      } else if (withheld) {
        reason = "The analysis that scores the courses of action against each other computed "
          + "for this project, but its finding is withheld until this period's preliminary "
          + "judgment is recorded and locked. Once it is, the courses of action appear here.";
      } else {
        reason = "The analysis that scores the courses of action against each other, the one "
          + "that asks which course carries the smallest worst case, did not compute for this "
          + "project. Without it the platform holds no set of courses of action to lay out, "
          + "and it will not invent one.";
      }
      return {
        available: false,
        reason: reason,
        pending: !hasModuleResults,
        withheld: !!withheld,
        options: [],
        recommendation: null,
        unknowns: []
      };
    }

    // Declared before `exposure` reads it: with `var` hoisting a later
    // declaration would leave it undefined here and the gate would never fire.
    var docEv = (result && result.document_evidence) || null;
    var exp = exposure(mods, si, docEv);
    var gov = mods.ABM_Governance;
    var authority = (gov && gov.authority) ? String(gov.authority) : null;

    var keys = Object.keys(scores).filter(function (k) { return isNum(scores[k]); });

    var unknowns = [];
    var options = keys.map(function (k) {
      /* NO SCORE IS QUOTED PER OPTION EITHER.
         This read "The analysis scores the worst case of this course at 11 out of 30, the
         highest of the set". The score and its rank within the set are both properties of a
         payoff matrix that reads no project input, so they were the same three numbers in the
         same order on every project this platform has ever shown. Quoting them under the
         heading "What it costs" said this course costs 11 on THIS project, which was never
         true of any project. The heading now carries only costs the platform can actually
         attribute to this period, and says so when it holds none. */
      var costs = [];
      var forecloses, protects;

      if (k === "escalate") {
        if (authority) {
          costs.push("It moves the decision to " + authority + ".");
          forecloses = "It closes off settling this inside the project: once it is a matter for "
            + "review, " + authority + " holds it, not you.";
        } else {
          costs.push(unknown("the platform holds no record of which authority an escalation "
            + "moves this decision to"));
          forecloses = "It closes off settling this inside the project. "
            + unknown("who it moves the decision to is not recorded for this project");
        }
        protects = exp.known
          ? "It protects the position from being carried further on the project's own judgment: "
            + "the figure that goes up is " + exp.text + "."
          : "It protects the position from being carried further on the project's own judgment. "
            + unknown("the completion figure it would put in front of management did not "
              + "compute for this project");
      } else if (k === "investigate") {
        forecloses = exp.known
          ? "It closes off nothing formally, and it spends a reporting period. The forecast the "
            + "period would close on is unchanged by investigating it: " + exp.text + "."
          : "It closes off nothing formally, and it spends a reporting period. "
            + unknown("the forecast that period would close on did not compute for this project");
        protects = "It protects the decision from leaving the project before the figures behind "
          + "it have been tested, and it keeps the formal step available afterwards.";
        costs.push(unknown("how long an investigation takes, and what it costs, is not a figure "
          + "the platform holds"));
      } else if (k === "monitor") {
        forecloses = exp.known
          ? "It closes off nothing, and it spends a reporting period during which the position "
            + "is unchanged: " + exp.text + "."
          : "It closes off nothing, and it spends a reporting period during which the position "
            + "is unchanged. "
            + unknown("the completion forecast for that period did not compute for this project");
        protects = "It protects the working relationship and the project's own authority over "
          + "the matter, and it adds no cost of its own.";
        costs.push(unknown("what carrying the position unchanged costs is not a figure the "
          + "platform holds"));
      } else {
        /* A course of action the analysis named that this file has no stated consequence for.
           Say so; do not write one. */
        forecloses = unknown("the platform holds this course of action and no statement of "
          + "what it closes off");
        protects = unknown("the platform holds this course of action and no statement of "
          + "what it protects");
        costs.push(unknown("the platform holds no statement of what this course costs"));
        unknowns.push(k);
      }

      return {
        key: k,
        title: ACTION_TITLE[k] || k,
        what: ACTION_WHAT[k] || unknown("the platform holds no description of this course of "
          + "action"),
        costs: costs,
        forecloses: forecloses,
        protects: protects
      };
    });

    /* The recommendation is the one the stored result holds. It is read back, never
       re-derived here, and the reason it differs from the ranking is the SERVED basis
       (`recommendation_basis`), which is derived server-side from this same row and pinned
       against the analysis's own rule by a check. This file states it; it does not decide it.

       The card used to say the difference was "not established". It was always establishable:
       the rule is a threshold on the period's own cost and schedule performance, and it is
       what chooses. Saying so is the difference between a recommendation a project manager can
       argue with and one they cannot. */
    var recKey = regret.recommended_action || null;
    var basis = (result && result.recommendation_basis) || null;
    var recommendation = null;
    if (recKey) {
      /* NO SCORE IS QUOTED, BECAUSE NO SCORE IS ABOUT THIS PROJECT.
         This used to read "It scores 8 out of 30, against 11 for ... and 5 for ...". Those
         three numbers are literals in the analysis's payoff matrix and its future
         probabilities; neither reads any project input, so every project and every period
         scores the same three. Printing them beside a project's name told a reader their own
         evidence produced them, and a reader who then argued with the ranking would have been
         arguing with a constant. The ranking is refused, with its reason, and the rule that
         actually chooses is stated in its place. */
      /* THE REFUSAL DOES NOT DEPEND ON THE SERVER ATTACHING ANYTHING. The scores are constants
         because the matrix behind them reads no project input; that is true of every read,
         including one where `document_evidence` was never served. An earlier draft of this
         gated the refusal on the served block, so a read without it printed neither the scores
         nor the reason they were withheld, which tells the reader less than either. The served
         reason is preferred because it is the authoritative wording; the fallback says the
         same thing so a reader is never left with an unexplained absence. */
      var reason = (docEv && docEv.ranking && docEv.ranking.possible === false
                    && docEv.ranking.reason)
        ? docEv.ranking.reason + " "
        : ("The courses are not ranked here: the scores the analysis holds are the same for "
           + "every project and every reporting period, so they say nothing about this one. ");
      reason += (basis && basis.sentence)
        ? basis.sentence
        : ("The stored result records the recommendation. The rule that set it is not on this "
           + "result, so the reason is not established here.");
      var evidence = [];
      if (isNum(si.cpi)) evidence.push("cost performance stands at " + si.cpi);
      if (isNum(si.spi)) evidence.push("schedule performance at " + si.spi);
      recommendation = {
        key: recKey,
        // True whenever the analysis holds scored courses at all: it holds them, and they rank
        // nothing. Not conditional on the served block, for the reason stated above.
        rankingRefused: keys.length > 0,
        title: ACTION_TITLE[recKey] || recKey,
        reason: reason,
        evidence: evidence.length ? evidence.join(" and ") + "." : null
      };
    }

    /* WHAT THE DOCUMENTS ESTABLISH, each statement carrying the document behind it.
       Read at display time from the period's live documents by `document_evidence.py`; this
       file formats and never derives. A finding with no filename is dropped rather than
       printed unattributed: the whole point of this block is that a reader can go and check
       it, and a sentence they cannot trace to a document is the kind this card refuses. */
    var documents = null;
    if (docEv) {
      var findings = (docEv.findings || []).filter(function (f) {
        return f && f.sentence && f.filename;
      });
      var unread = (docEv.not_established || []).filter(function (f) {
        return f && f.sentence && f.filename;
      });
      var reg = docEv.register || {};
      documents = {
        register: {
          openCount: reg.open_count || 0,
          unnamed: reg.unnamed || 0,
          named: (reg.named || []).filter(function (f) { return f && f.sentence; })
        },
        notices: (docEv.notices || []).filter(function (n) { return n && n.sentence; }),
        readCount: (docEv.documents_read || []).length,
        findings: findings.map(function (f) {
          return { sentence: f.sentence, filename: f.filename, bearing: f.bearing };
        }),
        notEstablished: unread.map(function (f) {
          return { sentence: f.sentence, filename: f.filename };
        })
      };
    }

    return {
      available: true,
      reason: null,
      options: options,
      recommendation: recommendation,
      documents: documents,
      exposureKnown: exp.known,
      authority: authority,
      unknowns: unknowns
    };
  }

  function buildForProject(project) {
    var row = (global.LinResults && global.LinResults.rowFor)
      ? global.LinResults.rowFor(project) : null;
    return build(row);
  }

  /* ---------------------------------------------------------- render */

  function html(spec) {
    if (!spec || spec.available !== true) {
      return '<div class="ro-block" id="ro-block"><h3 class="ro-title">Courses of action</h3>'
        + '<p class="ro-unavailable" id="ro-unavailable">'
        + esc((spec && spec.reason) || "No courses of action are available for this project.")
        + "</p></div>";
    }
    var body = spec.options.map(function (o) {
      return '<div class="ro-option" data-option="' + esc(o.key) + '">'
        + '<h4 class="ro-option-title">' + esc(o.title) + "</h4>"
        + '<p class="ro-what">' + esc(o.what) + "</p>"
        + '<p class="ro-costs">What it costs. ' + o.costs.map(esc).join(" ") + "</p>"
        + '<p class="ro-forecloses">What it forecloses. ' + esc(o.forecloses) + "</p>"
        + '<p class="ro-protects">What it protects. ' + esc(o.protects) + "</p>"
        + "</div>";
    }).join("");

    // WHAT THE DOCUMENTS SAY, WITH THE DOCUMENT NAMED. Rendered above the recommendation
    // because it is the evidence the recommendation is read against, and a reader who wants to
    // check a statement needs the filename beside it rather than in a panel somewhere else.
    var docs = "";
    if (spec.documents) {
      var d = spec.documents;
      if (d.findings.length || d.notEstablished.length
          || (d.register && d.register.named.length) || (d.notices && d.notices.length)) {
        docs = '<div class="ro-documents" id="ro-documents">'
          + '<h4 class="ro-option-title">What this period\'s documents say</h4>'
          + '<p class="ro-what">These are read from the documents uploaded for this period, not '
          + "from the computed figures. Each statement names the document it came from.</p>"
          + (d.findings.length
              ? '<ul class="ro-doc-findings">' + d.findings.map(function (f) {
                  return '<li class="ro-doc-finding">' + esc(f.sentence)
                    + ' <span class="ro-doc-source">Read from ' + esc(f.filename) + ".</span>"
                    + "</li>";
                }).join("") + "</ul>"
              : '<p class="ro-doc-none">No document in this period records an open item of a '
                + "kind this platform reads back.</p>")
          + (d.register && d.register.named.length
              ? '<h4 class="ro-option-title ro-sub">What the risk register records</h4>'
                + '<p class="ro-what">' + esc(String(d.register.openCount)) + " open risk"
                + (d.register.openCount === 1 ? "" : "s") + " in the register for this period"
                + (d.register.unnamed
                    ? ", of which the " + esc(String(d.register.named.length))
                      + " carrying the most weight the register itself assigned are named here"
                    : "") + ". Bands are quoted as the register wrote them and are never turned "
                + "into numbers.</p>"
                + '<ul class="ro-doc-findings">' + d.register.named.map(function (f) {
                    return '<li class="ro-doc-finding">' + esc(f.sentence) + "</li>";
                  }).join("") + "</ul>"
              : "")
          + (d.notices && d.notices.length
              ? '<h4 class="ro-option-title ro-sub">Notices served this period</h4>'
                + '<ul class="ro-doc-findings">' + d.notices.map(function (n) {
                    return '<li class="ro-doc-finding">' + esc(n.sentence)
                      + " " + esc(n.clock)
                      + (n.second_step ? " " + esc(n.second_step) : "")
                      + (n.filename
                          ? ' <span class="ro-doc-source">Read from ' + esc(n.filename)
                            + ".</span>"
                          : "")
                      + "</li>";
                  }).join("") + "</ul>"
              : "")
          + (d.notEstablished.length
              ? '<ul class="ro-doc-unread">' + d.notEstablished.map(function (f) {
                  return '<li class="ro-doc-finding">' + esc(f.sentence)
                    + ' <span class="ro-doc-source">' + esc(f.filename) + ".</span></li>";
                }).join("") + "</ul>"
              : "")
          + "</div>";
      }
    }

    var rec = "";
    if (spec.recommendation) {
      rec = '<div class="ro-recommendation" id="ro-recommendation">'
        + '<h4 class="ro-option-title">Recommended: ' + esc(spec.recommendation.title) + "</h4>"
        + '<p class="ro-reason">' + esc(spec.recommendation.reason)
        + (spec.recommendation.evidence
            ? " Against this period's evidence, " + esc(spec.recommendation.evidence) : "")
        + "</p></div>";
    }

    return '<div class="ro-block" id="ro-block">'
      + '<h3 class="ro-title">Courses of action</h3>'
      + '<p class="ro-lede">These are the courses of action open to you, each with what it '
      + "costs, what it closes off, and what it protects. Where the platform does not hold what "
      + "would be needed to state a consequence, it says so instead of asserting one. The "
      + "recommendation follows the options, so the choice stays yours.</p>"
      // THE COURSES ARE NOT RANKED HERE, AND THE CARD SAYS SO. The scores the analysis stores
      // come from a fixed payoff matrix over fixed probabilities, neither of which reads a
      // project input, so they are identical on every project and every period. They used to
      // be printed with a caveat; a number a reader cannot argue with is worse than no number,
      // so they are no longer printed at all. What decides is stated with the recommendation.
      + (spec.recommendation && spec.recommendation.rankingRefused
          ? '<p class="ro-lede ro-lede-note">The courses below are not ranked. The scores the '
            + "analysis holds are the same for every project and every reporting period, so "
            + "they say nothing about this one. What decides the recommendation is stated with "
            + "it, and what this period's documents say is set out below.</p>"
          : "")
      + body + docs + rec + "</div>";
  }

  function htmlForProject(project) {
    return html(buildForProject(project));
  }

  global.LinRecOptions = {
    build: build,
    buildForProject: buildForProject,
    html: html,
    htmlForProject: htmlForProject,
    unknownPhrase: "Not established:"
  };
})(typeof window !== "undefined" ? window : this);
