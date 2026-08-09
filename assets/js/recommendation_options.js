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
  function exposure(mods, si) {
    var bac = si && si.bac;
    var cra = mods.Cost_Risk_Analysis;
    var mc = mods.Monte_Carlo;
    if (cra && isNum(cra.p80_eac) && isNum(cra.p80_delta_pct)) {
      return {
        text: "an eightieth percentile estimate at completion of " + money(cra.p80_eac)
          + " dollars, " + cra.p80_delta_pct + " per cent above budget",
        known: true
      };
    }
    if (mc && isNum(mc.p80_eac)) {
      return {
        text: "an eightieth percentile estimate at completion of " + money(mc.p80_eac)
          + " dollars" + (isNum(bac) ? " against a budget of " + money(bac) + " dollars" : ""),
        known: true
      };
    }
    return { text: null, known: false };
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

    var exp = exposure(mods, si);
    var gov = mods.ABM_Governance;
    var authority = (gov && gov.authority) ? String(gov.authority) : null;

    var keys = Object.keys(scores).filter(function (k) { return isNum(scores[k]); });
    var values = keys.map(function (k) { return Number(scores[k]); });
    var lowest = Math.min.apply(null, values);
    var highest = Math.max.apply(null, values);

    var unknowns = [];
    var options = keys.map(function (k) {
      var score = Number(scores[k]);
      var rank = score === lowest ? "the lowest of the set"
        : score === highest ? "the highest of the set" : "between the other two";

      var costs = ["The analysis scores the worst case of this course at " + score
        + " out of 30, " + rank + ", where a lower score means a smaller worst case."];
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
      } else {
        /* A course of action the analysis scored that this file has no stated consequence for.
           Say so; do not write one. */
        forecloses = unknown("the platform holds a score for this course of action and no "
          + "statement of what it closes off");
        protects = unknown("the platform holds a score for this course of action and no "
          + "statement of what it protects");
        unknowns.push(k);
      }

      return {
        key: k,
        title: ACTION_TITLE[k] || k,
        what: ACTION_WHAT[k] || unknown("the platform holds no description of this course of "
          + "action beyond its score"),
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
      var recScore = isNum(scores[recKey]) ? Number(scores[recKey]) : null;
      var others = keys.filter(function (k) { return k !== recKey; }).map(function (k) {
        return Number(scores[k]) + " for " + (ACTION_TITLE[k] || k).toLowerCase();
      });
      var reason;
      if (recScore === null) {
        reason = unknown("the stored result names a recommended course of action it holds no "
          + "score for");
      } else {
        reason = "It scores " + recScore + " out of 30"
          + (others.length ? ", against " + others.join(" and ") : "") + ". ";
        reason += (basis && basis.sentence)
          ? basis.sentence
          : ("The stored result records the recommendation and the scores. The rule that set "
             + "the recommendation against the score is not on this result, so the reason is "
             + "not established here.");
      }
      var evidence = [];
      if (isNum(si.cpi)) evidence.push("cost performance stands at " + si.cpi);
      if (isNum(si.spi)) evidence.push("schedule performance at " + si.spi);
      recommendation = {
        key: recKey,
        scoresAreFixed: !!(basis && basis.scores_are_fixed),
        title: ACTION_TITLE[recKey] || recKey,
        reason: reason,
        evidence: evidence.length ? evidence.join(" and ") + "." : null
      };
    }

    return {
      available: true,
      reason: null,
      options: options,
      recommendation: recommendation,
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
      // THE SCORES ARE A PROPERTY OF THE METHOD, NOT A FINDING ABOUT THIS PERIOD. The payoff
      // matrix and the future probabilities behind them are fixed, so every project and every
      // period scores 11, 5 and 8. Calling them "the courses the analysis scored for this
      // period" told a reader their own evidence produced those numbers. It did not, and the
      // recommendation is not taken from them either. Said once, here, rather than repeated.
      + (spec.recommendation && spec.recommendation.scoresAreFixed
          ? '<p class="ro-lede ro-lede-note">The scores below rank the courses by worst case '
            + "and are the same for every project: they come from the method, not from this "
            + "period's evidence. What decides the recommendation is stated with it.</p>"
          : "")
      + body + rec + "</div>";
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
