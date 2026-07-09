/* ============================================================
   lin-project-radar — export.js
   ------------------------------------------------------------
   On-demand XLSX project report. Reads from the LATEST stored
   category snapshot on project.history. Generates a 2- or
   3-sheet workbook via SheetJS (already loaded in index.html):

     1. Executive Summary — project identity, governance decision,
        signal inputs, evidence agreement, executive brief text.
     2. Category Results — each of the 9 categories with its
        worst-status-wins rollup + every module underneath.
     3. Signal History — present only when project.history has
        more than one period; one row per period with the
        per-category status across time.

   Globals (no ES modules), exported as window.LinExport.
   ============================================================ */

(function () {
  "use strict";

  function exportProjectReport(project) {
    if (!project) {
      alert("No project provided to the report exporter.");
      return;
    }
    if (typeof XLSX === "undefined") {
      alert("XLSX library not loaded — cannot export the report.");
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

    // ----- Sheet 1: Executive Summary -----
    const gov = snapshot.governance || {};
    const si = snapshot.signal_inputs || {};
    const ea = (snapshot.summary && snapshot.summary.evidence_agreement) || {};
    const brief = snapshot.executive_brief || project.executiveBrief || null;

    const summaryRows = [
      ["LIN OPUS GUBERNATIO — PROJECT REPORT"],
      [""],
      ["Project:",       snapshot.project_name || ""],
      ["Project ID:",    snapshot.project_id || ""],
      ["Sector:",        snapshot.sector || ""],
      ["Report Period:", snapshot.period || ""],
      ["Generated:",     snapshot.computed_at || ""],
      [""],
      ["GOVERNANCE DECISION"],
      ["State:",                  gov.state || ""],
      ["Authority:",              gov.authority || ""],
      ["Recommended Action:",     gov.action || ""],
      ["Documentation Required:", gov.documentation || ""],
      ["Fairness Gate:",          gov.fairness_gate ? "Required" : "Not required"],
      [""]
    ];

    // Signal-traced action plan (deterministic rules, decision.js)
    if (typeof deriveActionPlan === "function") {
      try {
        const plan = deriveActionPlan(project) || [];
        if (plan.length) {
          summaryRows.push(["SIGNAL-TRACED ACTION PLAN"]);
          summaryRows.push(["Trigger", "What", "Who", "How", "When", "Inform"]);
          plan.forEach((r) => {
            summaryRows.push([r.trigger, r.what, r.who, r.how, r.when, r.inform]);
          });
          summaryRows.push([""]);
        }
      } catch (e) { /* plan derivation must never block the export */ }
    }

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

    // ----- Sheet 2: Category Results -----
    const catRows = [[
      "Category", "Category Name", "Overall Status",
      "Module", "Module Name", "Status", "Evidence Metric"
    ]];
    const cats = snapshot.categories || {};
    Object.keys(cats).forEach((key) => {
      const cat = cats[key];
      if (!cat) return;
      if (cat.parked) {
        catRows.push([cat.num, cat.name, "Stage 2 — not yet active", "", "", "", ""]);
        catRows.push(["", "", "", "", "", "", ""]);
        return;
      }
      (cat.modules || []).forEach((m, idx) => {
        catRows.push([
          idx === 0 ? cat.num : "",
          idx === 0 ? cat.name : "",
          idx === 0 ? (cat.status || "No data") : "",
          m.num,
          m.name,
          m.status || "No data",
          m.evidence_metric || ""
        ]);
      });
      catRows.push(["", "", "", "", "", "", ""]);
    });
    const wsCat = XLSX.utils.aoa_to_sheet(catRows);
    wsCat["!cols"] = [
      { wch: 8 }, { wch: 28 }, { wch: 18 },
      { wch: 10 }, { wch: 35 }, { wch: 12 }, { wch: 50 }
    ];
    XLSX.utils.book_append_sheet(wb, wsCat, "Category Results");

    // ----- Sheet 3: Signal History (only if >1 period) -----
    if (project.history && project.history.length > 1) {
      const histRows = [[
        "Period", "Cat 1 EVM", "Cat 2 Schedule", "Cat 3 Cost",
        "Cat 4 Doc/Risk", "Cat 5 Dynamics", "Cat 6 Synthesis",
        "Cat 7 Evidence", "Cat 9 Governance", "Overall"
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

    const filename = "LinPR_Project" + (snapshot.project_id || project.id) +
      "_" + (snapshot.period || "current") + "_Report.xlsx";
    XLSX.writeFile(wb, filename);
  }

  window.LinExport = { exportProjectReport };
})();
