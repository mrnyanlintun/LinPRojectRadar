/* ============================================================
   lin-project-radar — export.js
   ------------------------------------------------------------
   On-demand XLSX project report. Reads from the LATEST stored
   category snapshot on project.history. Generates a 3- or
   4-sheet workbook via SheetJS (already loaded in index.html):

     1. Notice — the approved advisory text for the signed-in
        account type, plus attribution and copyright. First,
        because the file leaves the platform and is read by
        people who never saw the site.
     2. Executive Summary — project identity, governance decision,
        signal inputs, evidence agreement, executive brief text.
     3. Category Results — each of the 9 categories with its
        worst-status-wins rollup + every module underneath.
     4. Signal History — present only when project.history has
        more than one period; one row per period with the
        per-category status across time.
     5. Mitigations — RUN 140, present only when the card the
        reviewer saw carried mitigations. One row per non-Green
        reading with its band, reading, next-band boundary, gap
        and each candidate, plus the composition date, model and
        provider.

   RUN 140: WHY A FIFTH SHEET AND NOT WIDER SUMMARY ROWS. The
   Executive Summary is a two-column label/value list; a
   mitigation is five fields and a variable number of candidate
   bullets, and forcing it into that shape would either truncate
   the candidates or restructure a sheet three other blocks read.
   A new sheet adds nothing to what the existing four carry, so
   nothing that reads them can be broken by it.

   Globals (no ES modules), exported as window.LinExport.
   ============================================================ */

(function () {
  "use strict";

  /* RUN 140. `decisionBrief` is the SERVED decision brief (NOT `brief`, which is
     the executive brief a few lines down; measured -- the first attempt collided with it), optional and defaulting to null.
     The workbook is otherwise built entirely from the latest stored snapshot on
     `project.history`, which has never carried a mitigation and still does not. Mitigations are
     reveal-gated, so a card rendered without them exports a four-sheet workbook exactly as it
     did before this run -- the fifth sheet is not appended empty. */
  function exportProjectReport(project, decisionBrief) {
    if (!project) {
      alert("No project provided to the report exporter.");
      return;
    }
    if (typeof XLSX === "undefined") {
      alert("XLSX library not loaded: cannot export the report.");
      return;
    }
    const snapshot = (project.history && project.history.length)
      ? project.history[project.history.length - 1]
      : null;
    if (!snapshot) {
      alert("No snapshot available. Run signal extraction first.");
      return;
    }

    const wb = XLSX.utils.book_new();

    // ----- Sheet 1: Notice -----
    //
    // AN EXPORT IS THE ARTIFACT MOST LIKELY TO BE READ WITHOUT ANY SURROUNDING CONTEXT. It leaves
    // the platform as a file and circulates to people who never saw the sign-in notice or the
    // footer, and until now it carried no notice, no attribution and no copyright at all. It is
    // the FIRST sheet, not an appendix, because a sheet nobody scrolls to is not a notice.
    //
    // The text is not written here. It comes from LinDisclaimers, which holds the approved
    // wording quoted verbatim from DISCLAIMERS_DRAFT.md, and server/tools/test_disclaimers.py
    // fails if the two diverge by a character. No shortened form is composed for the narrower
    // space of a spreadsheet cell: a surface carries the approved text whole or does not carry
    // it. It switches on account type exactly as every other surface does.
    const D = window.LinDisclaimers;
    if (D && typeof D.currentNotice === "function") {
      const noticeRows = [["OPUS GUBERNATIO: NOTICE"], [""]];
      D.currentNotice().forEach((p) => { noticeRows.push([p], [""]); });
      noticeRows.push([D.attribution], [""], [D.copyright]);
      const wsNotice = XLSX.utils.aoa_to_sheet(noticeRows);
      wsNotice["!cols"] = [{ wch: 118 }];
      XLSX.utils.book_append_sheet(wb, wsNotice, "Notice");
    }

    // ----- Sheet 2: Executive Summary -----
    const gov = snapshot.governance || {};
    const si = snapshot.signal_inputs || {};
    const ea = (snapshot.summary && snapshot.summary.evidence_agreement) || {};
    const brief = snapshot.executive_brief || project.executiveBrief || null;

    const summaryRows = [
      ["OPUS GUBERNATIO: PROJECT REPORT"],
      [""],
      ["Project:",       snapshot.project_name || ""],
      ["Project ID:",    snapshot.project_id || ""],
      ["Sector:",        snapshot.sector || ""],
      ["Report Period:", snapshot.period || ""],
      ["Generated:",     snapshot.computed_at || ""],
      [""],
      // RUN 98. Authority / Recommended Action / Documentation Required are removed from the
      // exported report. That history stands: they came from `deriveDecision`, which no longer
      // composes them, and an export that carried them made the claim the card had already
      // stopped making.
      //
      // RUN 140 NARROWS THE GENERAL CLAUSE THAT USED TO SIT HERE. It read "the platform states
      // a finding and issues no action, no remedy and no authority". The first two thirds of
      // that are no longer true: from 2026-09-05 the card suggests candidate mitigations for
      // every non-Green reading, and the "Mitigations" sheet of this workbook now carries the
      // ones the reviewer was shown, verbatim and with their composition date. What remains
      // exactly true, and is why these three rows stay removed, is the last third: the platform
      // holds NO authority, assigns NO owner, sets NO deadline and requires NO document.
      ["GOVERNANCE DECISION"],
      ["State:",                  gov.state || ""],
      ["Fairness Gate:",          gov.fairness_gate ? "Required" : "Not required"],
      [""]
    ];

    // RUN 98. The SIGNAL-TRACED ACTION PLAN block is removed from the export. It printed the
    // Trigger / What / Who / How / When / Inform rows -- an assigned actor, a prescribed
    // method and a deadline -- into the workbook. `deriveActionPlan` no longer exists.

    summaryRows.push(
      ["SIGNAL INPUTS"],
      ["Budget at Completion (BAC):",      si.bac != null ? si.bac : ""],
      ["Earned Value (EV):",               si.ev  != null ? si.ev  : ""],
      ["Actual Cost (AC):",                si.ac  != null ? si.ac  : ""],
      ["Planned Value (PV):",              si.pv  != null ? si.pv  : ""],
      ["Cost Performance Index (CPI):",    si.cpi != null ? si.cpi : ""],
      ["Schedule Performance Index (SPI):",si.spi != null ? si.spi : ""],
      [""],
      ["EVIDENCE AGREEMENT"],
      ["Methods Checked:",  ea.methods_checked  != null ? ea.methods_checked  : ""],
      ["Methods Agreeing:", ea.methods_agreeing != null ? ea.methods_agreeing : ""],
      ["Confidence:",       ea.confidence || ""],
      [""],
      ["EXECUTIVE BRIEF"],
      [brief && brief.text ? brief.text : "Not generated"]
    );
    if (brief && brief.text) {
      summaryRows.push([""], ["Brief generated:", brief.generated_at || ""]);
    }
    const wsSummary = XLSX.utils.aoa_to_sheet(summaryRows);
    wsSummary["!cols"] = [{ wch: 35 }, { wch: 60 }];
    XLSX.utils.book_append_sheet(wb, wsSummary, "Executive Summary");

    // ----- Sheet 3: Category Results -----
    // RUN 51, RULING 2. The sheet carried an IDENTIFIER column beside each NAME column, filled
    // from the taxonomy's primary key. The key dispatches; it is not a label, and an exported
    // workbook is user-facing text. The two identifier columns are gone rather than blanked,
    // because an empty column is a worse artefact than a missing one.
    const catRows = [[
      "Category Name", "Overall Status", "Module Name", "Status", "Evidence Metric"
    ]];
    const cats = snapshot.categories || {};
    Object.keys(cats).forEach((key) => {
      const cat = cats[key];
      if (!cat) return;
      if (cat.parked) {
        catRows.push([cat.name, "Stage 2: not yet active", "", "", ""]);
        catRows.push(["", "", "", "", ""]);
        return;
      }
      (cat.modules || []).forEach((m, idx) => {
        catRows.push([
          idx === 0 ? cat.name : "",
          idx === 0 ? (cat.status || "No data") : "",
          m.name,
          m.status || "No data",
          m.evidence_metric || ""
        ]);
      });
      catRows.push(["", "", "", "", ""]);
    });
    const wsCat = XLSX.utils.aoa_to_sheet(catRows);
    wsCat["!cols"] = [
      { wch: 8 }, { wch: 28 }, { wch: 18 },
      { wch: 10 }, { wch: 35 }, { wch: 12 }, { wch: 50 }
    ];
    XLSX.utils.book_append_sheet(wb, wsCat, "Category Results");

    // ----- Sheet 4: Signal History (only if >1 period) -----
    if (project.history && project.history.length > 1) {
      // Column header text is the display label; the stored per-period summary
      // keys (c.cat9 etc.) are the STABLE internal category ids and are read
      // as-is — only the header string changed. No category id or number in
      // the header text (see NAMING_AUTHORITY.md).
      const histRows = [[
        "Period", "Cost and EVM Performance", "Schedule Performance", "Cost Risk",
        "Document-Derived Condition Signals", "System Dynamics and Complexity", "Signal Synthesis",
        "Evidence Combination", "Regulatory and Authority Thresholds", "Overall"
      ]];
      project.history.forEach((h) => {
        const c = (h.summary && h.summary.by_category) || {};
        histRows.push([
          h.period,
          c.cat1 || "", c.cat2 || "", c.cat3 || "",
          c.cat4 || "", c.cat5 || "", c.cat6 || "",
          c.cat7 || "", c.cat9 || "",
          h.governance ? (h.governance.state || "") : ""
        ]);
      });
      const wsHist = XLSX.utils.aoa_to_sheet(histRows);
      wsHist["!cols"] = new Array(10).fill({ wch: 16 });
      XLSX.utils.book_append_sheet(wb, wsHist, "Signal History");
    }

    // ----- Sheet 5: Mitigations (RUN 140; only when the card carried them) -----
    //
    // THE RECORD PRESERVES WHAT THE REVIEWER SAW. Every cell below is a stored string copied
    // through unchanged. Nothing is recomputed, rounded or re-ordered: the rows are in the
    // server's severity order, and the figures are the ones the constant that decided the band
    // produced. A workbook that improved on the card would document a card that never existed.
    //
    // THE PROVENANCE TRAVELS WITH THE TEXT. A spreadsheet leaves the platform and is read
    // without any surrounding context, so a composed sentence in it that did not carry its
    // composition date, model and provider would be an assertion of unknown origin.
    const mits = (decisionBrief && Array.isArray(decisionBrief.mitigations))
      ? decisionBrief.mitigations : [];
    if (mits.length) {
      const mitRows = [[
        "Module", "Band", "Reading", "Next Band", "Gap", "Candidate Mitigation",
        "Composed", "Model", "Provider"
      ]];
      mits.forEach((m) => {
        const cands = Array.isArray(m.candidates) ? m.candidates : [];
        // NO CANDIDATE, NO BLANK ROW. The absence line is the server's fixed text and is
        // written where a candidate would be, so the sheet states the absence rather than
        // leaving a reader to infer it from an empty cell.
        const cells = cands.length ? cands
          : [m.absent_reason || "no mitigation composed for this reading"];
        cells.forEach((c, idx) => {
          mitRows.push([
            idx === 0 ? (m.module_id || "") : "",
            idx === 0 ? (m.band || "") : "",
            idx === 0 ? (m.reading || "") : "",
            idx === 0 ? (m.next_band || "") : "",
            idx === 0 ? (m.gap || "") : "",
            c,
            idx === 0 ? (m.composed_at || "") : "",
            idx === 0 ? (m.model || "") : "",
            idx === 0 ? (m.provider || "") : ""
          ]);
        });
        mitRows.push(["", "", "", "", "", "", "", "", ""]);
      });
      const wsMit = XLSX.utils.aoa_to_sheet(mitRows);
      wsMit["!cols"] = [
        { wch: 10 }, { wch: 10 }, { wch: 52 }, { wch: 52 }, { wch: 52 },
        { wch: 60 }, { wch: 12 }, { wch: 18 }, { wch: 12 }
      ];
      XLSX.utils.book_append_sheet(wb, wsMit, "Mitigations");
    }

    const filename = "OpusGubernatio_Project" + (snapshot.project_id || project.id) +
      "_" + (snapshot.period || "current") + "_Report.xlsx";
    XLSX.writeFile(wb, filename);
  }

  window.LinExport = { exportProjectReport };
})();
