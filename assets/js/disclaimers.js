/* ============================================================
   disclaimers.js — the approved account-type notices, once.

   THE SOURCE OF THIS WORDING IS DISCLAIMERS_DRAFT.md. It is approved liability text. Do not
   edit it here, do not extend or strengthen it, and do not compose new wording for a surface
   that seems to need it: adopting liability language is the researcher's decision, not a
   session's. Edit the source first, then this, and keep the two identical.
   server/tools/test_disclaimers.py fails if they diverge by a character.

   WHY THIS FILE EXISTS. The sign-in notice and the footer carry this text as static HTML in
   index.html, so a liability notice never depends on JavaScript having loaded. The upload
   panels cannot do that: they are built as HTML strings by signals.js and auditor.js at render
   time, and there are four of them. Four copies of approved legal text in two files is the
   shape that drifts, and it had already drifted — before this file, the upload panels carried
   wording that matched neither each other nor the approved notice. They now share one constant.

   The class names are what the CSS account-type switch keys on: .notice-research is the default
   and shows before sign-in, because the restrictive text is the fail-safe direction, and
   body.og-account-operational reveals .notice-operational only after the server has resolved
   the caller as operational.
   ============================================================ */

(function () {
  "use strict";

  // Quoted verbatim from DISCLAIMERS_DRAFT.md, section 1.
  var RESEARCH = [
    "Notice: academic research instrument. Opus Gubernatio is a proof of concept developed solely for doctoral research and demonstration. It is not a commercial service and is provided as is, without warranty of any kind, express or implied.",
    "All project data is synthetic. No real project, agency, employer, contractor, or vendor is referenced. Do not upload confidential, proprietary, personally identifiable, or otherwise sensitive information, or any document relating to an actual project.",
    "Uploaded content is sent to third-party artificial intelligence services for extraction and is stored in research infrastructure. Analytical outputs are advisory. They are not a validated compliance determination, a contractual direction, or a diagnosis of a live project. The operator disclaims all liability arising from or relating to uploaded content to the fullest extent permitted by law."
  ];

  // Quoted verbatim from DISCLAIMERS_DRAFT.md, section 2.
  //
  // It deliberately does NOT say synthetic data only, does NOT say no real project is
  // referenced, and does NOT tell the user not to submit actual project documents. An
  // operational user uploading real project documents is the designed case, and each of those
  // statements would be false for them. That is the whole reason the two variants exist.
  var OPERATIONAL = [
    "Notice. Opus Gubernatio is provided as is, without warranty of any kind, express or implied.",
    "Analytical outputs are advisory. They are not a validated compliance determination, a contractual direction, or a diagnosis of a live project.",
    "Uploaded content is sent to third-party artificial intelligence services for extraction and is stored in the platform. You are responsible for confirming that you are authorized to upload each document, and for your organization's data handling, confidentiality, and records obligations. The operator disclaims all liability arising from or relating to uploaded content to the fullest extent permitted by law."
  ];

  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  // The leading "Notice." / "Notice: academic research instrument." is bolded to match how the
  // same paragraph is emphasised on the sign-in notice and the footer. Emphasis only; the
  // characters are unchanged, which is what the source-vs-live check compares.
  function paras(list) {
    return list.map(function (p, i) {
      if (i !== 0) return "<p>" + esc(p) + "</p>";
      var cut = p.indexOf(" ", p.indexOf("."));
      var lead = p.slice(0, cut);
      return "<p><strong>" + esc(lead) + "</strong>" + esc(p.slice(cut)) + "</p>";
    }).join("");
  }

  /* Both variants, as one block, for a surface that renders HTML strings. The CSS switch
     decides which of the two is visible; both are always present in the DOM, exactly as they
     are on the sign-in notice and the footer. */
  function uploadNoticeHtml() {
    return '<div class="upload-disclaimer notice-research">' + paras(RESEARCH) + "</div>" +
           '<div class="upload-disclaimer notice-operational">' + paras(OPERATIONAL) + "</div>";
  }

  window.LinDisclaimers = {
    research: RESEARCH.slice(),
    operational: OPERATIONAL.slice(),
    uploadNoticeHtml: uploadNoticeHtml
  };
})();
