/* global LinNeuralFlow — THE SIGNAL FLOW, REBUILT. Run 82, Part C. */

/* =================================================================================================
   WHAT THIS DRAWS, AND WHAT IT REFUSES TO DRAW.

   THE OWNER'S SPECIFICATION, in his words: "Only if the doc data are extracted, it will connect to
   the relevant modules. The modules will light the status of the result. Then connect to the
   corresponding category. They will also light the status. Then to the project health status."

   THE PREVIOUS VERSION drew every document into almost every module. Run 79 measured its census as
   63 module nodes with 2 lit, and its edges were drawn from `taxonomy.js`'s `required` declarations
   -- which Run 76 measured as WRONG for six of the ten A1 modules. Density carried no information
   because the density was invented. This file replaces it whole.

   -------------------------------------------------------------------------------------------
   THE ONE THING THAT DECIDED THE SHAPE OF THIS CHART, AND IT IS A NEGATIVE FINDING.

   The order's rule 1 is "a document draws a line only where a figure was extracted from it AND
   REACHED A MODULE". That needs two joins, and the platform stores only one of them:

     (a) DOCUMENT -> FIELD.  STORED, and exact. `signal_inputs.sources` maps each extracted field
         to {docType, value, documentId, documentVersion, asOf}. It reaches this client on
         `LinResults.rowFor(project).signal_inputs.sources`. Measured on the Run 82 reproduction:
         15 fields, each naming the document ULID and content hash it came from.

     (b) FIELD -> MODULE.  NOT STORED, ANYWHERE. `spec_projection.module_rows` emits module_id,
         band, value, display, evidence_metric, narrative and provenance -- and no list of the
         inputs the module consumed. `spec_apply.normalise_module` drops anything outside that
         fixed key set, so a specification could not report it even if it wanted to. The Python
         module layer does not record it either: every module is handed the WHOLE signal_inputs
         dict by `registry.run_module(mid, si, ...)` and returns no account of what it read. A
         grep for inputs_used / fields_used / input_fields across server/app finds nothing.

     The only per-module input list in the repository is `taxonomy.js`'s `required`, and Run 76
     MEASURED IT WRONG: A1.6 declares ev, pv, bac, actualPctComplete, plannedPctComplete and
     actually needs timePhasedBaseline + ev; A1.11 declares bac, cpi, ev, ac and actually needs
     independentEacPair. Run 77 left the scale of that beyond A1 unmeasured.

   SO NO EDGE IS DRAWN FROM A FIELD INTO A MODULE. Drawing one would be drawing a line that
   carried no figure, which the order fails the run for, and drawing it from `taxonomy.js` would
   be drawing a line the repository has already been shown to have wrong. The break is drawn
   EXPLICITLY, with the reason on the chart, rather than being papered over: the reader is told
   the platform does not record which module read which figure. That is a finding about the
   platform, and hiding it would be the same class of error Part A exists to correct.

   WHAT IS DRAWN, AND EVERY EDGE IS A STORED FACT:

     DOCUMENT -> FIELD      from `signal_inputs.sources`. One edge per field actually extracted.
                            A document that contributed nothing has no fields and draws nothing;
                            it is not on the chart at all, because `sources` never names it.
     [ THE BREAK ]          stated, not drawn.
     MODULE -> CATEGORY     ONLY where the module has a stored reading. A module with nothing to
                            report sits dark and unconnected: the line would carry no figure.
     CATEGORY -> PROJECT    ONLY where the category has a stored status AND
                            `contributes_to_project_status` is true on its own projection row.

   NOTHING HERE COMPUTES. Every colour, band, status and state is read off the row the server
   stored. `worst_band` is not re-implemented; the category's status is the one the server fused
   and the project's status is the one the server fused. There is no client fallback anywhere in
   this file: where the server stored nothing, the node renders as having nothing, which is true.

   -------------------------------------------------------------------------------------------
   THE FOUR STATES, AND THEY ARE NOT MERGED (order section 4, and section 10.3 fails the run for
   merging them). Rendered here as four different fills, four different strokes, four different
   glyphs and four different `data-state` attributes, so a check can tell them apart from the DOM
   and so can a person:

     HAS A READING     data-state="computed"     filled in the band's colour, solid stroke, and
                                                 the shared status GLYPH (circle/triangle/
                                                 diamond/square/ring) so the colour is not the
                                                 only cue. IT IS THE ONLY STATE THAT DRAWS AN
                                                 EDGE.
     NOTHING TO REPORT data-state="abstained"    dark fill, solid muted stroke. Present, silent.
                                                 The evidence is not there.
     NOT RELEVANT      data-state="not_relevant" NO FILL. Outline only, dashed, in the site's
                                                 own --status-notrelevant colour. Never called.
                                                 Read from `window.isModuleSectorNA` /
                                                 `window.isModuleDisabled`, which are TAXONOMY
                                                 declarations about the project's sector and
                                                 about permanently disabled modules -- a static
                                                 statement about the project TYPE, not a claim
                                                 about evidence, and not a stored reading being
                                                 invented. See the note on FAILED below.
     FAILED            data-state="failed"       drawn on the CATEGORY, filled red with a cross
                                                 through it, because that is where the platform
                                                 stored the failure and, in the owner's own
                                                 words, "it belongs on the category list where
                                                 it gets dealt with". It looks wrong on purpose.

   A FIFTH IS DRAWN AND IS NOT ONE OF THE FOUR: data-state="not_called". A module in a category
   nobody has processed yet has no reading of any kind. Merging it into "nothing to report" would
   assert that the evidence was looked for and found missing, which nobody has established. It is
   dotted and hollow-centred, distinct from all four above. Run 79 established this distinction on
   the panel and it holds here.

   WHAT THE SERVER CANNOT TELL THIS CHART, stated plainly for the record. There is no per-module
   FAILED state anywhere in the stored data: `spec_apply.normalise_module` accepts only 'computed'
   and 'abstained' from a specification, and a FAILED row is written at CATEGORY level with an
   empty module list. So a failed category's modules are drawn as not called -- which is what they
   are, since the category blew up before any of them reported -- and the failure itself is drawn,
   unmistakably, on the category. Nothing is invented to fill the gap.
   ============================================================================================== */

(function () {
  "use strict";

  var NS = "http://www.w3.org/2000/svg";

  /* ---------------------------------------------------------------- small DOM helpers ---- */
  function se(tag, attrs, parent) {
    var e = document.createElementNS(NS, tag);
    if (attrs) { Object.keys(attrs).forEach(function (k) { e.setAttribute(k, attrs[k]); }); }
    if (parent) parent.appendChild(e);
    return e;
  }
  function txt(s, x, y, attrs, parent) {
    var e = se("text", attrs || {}, parent);
    e.setAttribute("x", x); e.setAttribute("y", y);
    e.textContent = String(s == null ? "" : s);
    return e;
  }
  function trunc(s, n) { s = String(s == null ? "" : s); return s.length > n ? s.slice(0, n - 1) + "…" : s; }

  function colors() {
    var c = window.LIN_STATUS_COLORS || {};
    return {
      Green: c.Green || "#2ee66b", Yellow: c.Yellow || "#ffe066",
      Amber: c.Amber || "#ff8c1a", Red: c.Red || "#ff3b30",
      Complete: c.Complete || "#4ea0ff", None: c.None || "#26344f",
      NotRelevant: c.NotRelevant || "#5b3dd6"
    };
  }
  function bandColor(band) {
    var C = colors(), s = String(band || "").toLowerCase();
    if (s.indexOf("complete") >= 0 || s.indexOf("blue") >= 0) return C.Complete;
    if (s.indexOf("green") >= 0) return C.Green;
    if (s.indexOf("yellow") >= 0) return C.Yellow;
    if (s.indexOf("amber") >= 0 || s.indexOf("orange") >= 0) return C.Amber;
    if (s.indexOf("red") >= 0) return C.Red;
    return null;
  }

  /* ------------------------------------------------------------------ THE MODEL -----------
     Everything below is READ. Not one figure is derived. */

  function projectCategories() {
    var all = window.LIN_CATEGORIES || [];
    if (window.projectLevelCategories) {
      try { return window.projectLevelCategories() || []; } catch (e) { /* fall through */ }
    }
    return all.filter(function (c) { return !(c && (c.level === "portfolio" || c.portfolioLevel)); });
  }

  /* The stored row, or null. `LinResults.rowFor` is the single reader of the primed row and this
     file does not open a second route to it. */
  function storedRow(project) {
    try { return (window.LinResults && LinResults.rowFor(project)) || null; }
    catch (e) { return null; }
  }

  /* WHICH DOCUMENT SUPPLIED WHICH FIELD. Straight off `signal_inputs.sources`; the shape is
     {field: {docType, value, documentId, documentVersion, asOf}}. A field with no source entry
     is not drawn, because nothing recorded where it came from. */
  function documentEdges(row) {
    var si = (row && row.signal_inputs) || {};
    var sources = si.sources;
    var fields = [], docs = Object.create(null);
    if (!sources || typeof sources !== "object") return { fields: fields, docs: [] };
    Object.keys(sources).forEach(function (field) {
      var s = sources[field];
      if (!s || typeof s !== "object") return;
      var id = String(s.documentId || s.docType || "");
      if (!id) return;
      if (!docs[id]) {
        docs[id] = { id: id, docType: String(s.docType || "document"),
                     version: String(s.documentVersion || ""), asOf: s.asOf || null, fields: [] };
      }
      docs[id].fields.push(field);
      fields.push({ field: field, docId: id, docType: docs[id].docType,
                    value: s.value, asOf: s.asOf || null });
    });
    fields.sort(function (a, b) { return a.docId < b.docId ? -1 : a.docId > b.docId ? 1 : (a.field < b.field ? -1 : 1); });
    var list = Object.keys(docs).map(function (k) { return docs[k]; });
    list.sort(function (a, b) { return a.docType < b.docType ? -1 : a.docType > b.docType ? 1 : 0; });
    return { fields: fields, docs: list };
  }

  /* EVERY MODULE IN SERVICE, WITH THE STATE THE SERVER STORED FOR IT.

     The roster is `LIN_CATEGORIES`, which build_client_taxonomy.py generates from
     server/app/simulation/registry.py -- 63 modules, matching service_index() exactly. The state
     is read in this order, and the order matters:

       1. NOT RELEVANT first, from the taxonomy's sector tags and the disabled list. A module that
          does not apply to this project type was never called, so no reading can exist for it and
          nothing later can contradict this.
       2. HAS A READING, from `module_results` -- the specification-reading projection, which
          Run 79 made the source for every surface.
       3. NOTHING TO REPORT, from `abstained` -- the module spoke and declined, with its reason.
       4. NOT CALLED, the remainder: no reading of any kind exists for this module. */
  function moduleStates(project, row, cats) {
    var byId = Object.create(null);
    ((row && row.module_results) || []).forEach(function (m) {
      if (m && m.module_id) byId[m.module_id] = m;
    });
    var abst = Object.create(null);
    ((row && row.abstained) || []).forEach(function (a) {
      if (a && a.module_id) abst[a.module_id] = a;
    });
    var out = [];
    cats.forEach(function (cat) {
      (cat.modules || []).forEach(function (m) {
        var na = false;
        try {
          na = !!((window.isModuleDisabled && window.isModuleDisabled(m.method_class))
                  || (window.isModuleSectorNA && window.isModuleSectorNA(m.method_class, project)));
        } catch (e) { na = false; }
        var rec = { id: m.module_id, name: m.name, category: cat.key, methodClass: m.method_class,
                    state: "not_called", band: null, display: null, reason: null };
        if (na) { rec.state = "not_relevant"; }
        else if (byId[m.module_id]) {
          var r = byId[m.module_id];
          rec.state = "computed";
          rec.band = r.band || r.status_color || null;
          rec.display = (r.display != null ? r.display : r.value);
          rec.reason = r.evidence_metric || r.narrative || null;
        } else if (abst[m.module_id]) {
          rec.state = "abstained";
          rec.reason = abst[m.module_id].reason || null;
        }
        out.push(rec);
      });
    });
    return out;
  }

  /* THE CATEGORY ROW, AS THE SERVER PROJECTED IT. `category_statuses` has an entry ONLY for a
     category that was called, which Run 79 established is the whole point of it: a missing key is
     "not called", not "no status". */
  function categoryStates(row, cats) {
    var cs = (row && row.category_statuses) || {};
    return cats.map(function (cat) {
      var e = cs[cat.key];
      if (!e) {
        return { key: cat.key, name: cat.name, state: "not_called", status: null,
                 contributes: false, counts: {}, reason: null, moduleCount: 0 };
      }
      return { key: cat.key, name: cat.name,
               state: e.state || null, status: e.status || null,
               contributes: !!e.contributes_to_project_status,
               counts: e.counts || {}, reason: e.reason || null,
               moduleCount: Number(e.module_count || 0) };
    });
  }

  /* ------------------------------------------------------------------ THE DRAWING ---------- */

  var DOC_W = 150, FLD_W = 128, MOD_W = 62, CAT_W = 132;
  var COL_DOC = 16, COL_FLD = 210, COL_MOD = 452, COL_CAT = 706, COL_PRJ = 902;
  var ROW_H = 22, TOP = 74;

  function glyph(parent, cx, cy, r, status, fill, stroke, dash, attrs) {
    var shape = "circle";
    try { if (window.linStatusShape) shape = window.linStatusShape(status); } catch (e) {}
    var a = { fill: fill, stroke: stroke, "stroke-width": 1.4 };
    if (dash) a["stroke-dasharray"] = dash;
    Object.keys(attrs || {}).forEach(function (k) { a[k] = attrs[k]; });
    var e;
    if (shape === "square") {
      a.x = cx - r; a.y = cy - r; a.width = r * 2; a.height = r * 2; e = se("rect", a, parent);
    } else if (shape === "triangle") {
      a.points = (cx) + "," + (cy - r * 1.15) + " " + (cx + r * 1.05) + "," + (cy + r * 0.85)
               + " " + (cx - r * 1.05) + "," + (cy + r * 0.85);
      e = se("polygon", a, parent);
    } else if (shape === "diamond") {
      a.points = (cx) + "," + (cy - r * 1.2) + " " + (cx + r * 1.2) + "," + (cy)
               + " " + (cx) + "," + (cy + r * 1.2) + " " + (cx - r * 1.2) + "," + (cy);
      e = se("polygon", a, parent);
    } else {
      a.cx = cx; a.cy = cy; a.r = r; e = se("circle", a, parent);
    }
    return e;
  }

  /* THE FOUR STATES AND THE FIFTH, EACH GIVEN ITS OWN MARK. This is the ONE function that turns
     a state into an appearance; if two states ever looked alike, they would look alike here, and
     the browser check reads these very attributes back out of the DOM. */
  function paintModule(g, x, y, mod) {
    var C = colors(), cx = x + 7, cy = y + 7;
    var node;
    if (mod.state === "computed") {
      var col = bandColor(mod.band) || C.Complete;
      node = glyph(g, cx, cy, 6.2, mod.band, col, col, null, { "fill-opacity": "0.92" });
    } else if (mod.state === "abstained") {
      /* DARK AND SOLID: present, silent, evidence not there. */
      node = se("circle", { cx: cx, cy: cy, r: 5.4, fill: C.None, "fill-opacity": "0.95",
                            stroke: "var(--muted, #7c8aa5)", "stroke-width": 1.2 }, g);
    } else if (mod.state === "not_relevant") {
      /* OUTLINE ONLY, NO BODY. Never called; does not apply to this project type. */
      node = se("circle", { cx: cx, cy: cy, r: 5.6, fill: "none",
                            stroke: C.NotRelevant, "stroke-width": 1.5,
                            "stroke-dasharray": "2.4 2.2" }, g);
    } else {
      /* NOT CALLED: dotted ring with a hollow centre. Not one of the owner's four; kept
         separate because merging it into "nothing to report" would assert that the evidence
         was looked for. */
      node = se("circle", { cx: cx, cy: cy, r: 5.2, fill: "none",
                            stroke: "var(--line-strong, #3a4a66)", "stroke-width": 1.1,
                            "stroke-dasharray": "1 2.4" }, g);
    }
    node.setAttribute("class", "nf-mod-mark");
    return node;
  }

  function render(project, container) {
    if (!container) return;
    container.innerHTML = "";
    var C = colors();
    var cats = projectCategories();
    var row = storedRow(project);
    var de = documentEdges(row);
    var mods = moduleStates(project, row, cats);
    var catRows = categoryStates(row, cats);
    var projectStatus = (row && row.project_status) || null;

    /* THE CENSUS, computed once and written onto the root element so a check can read the
       numbers the drawing was made from rather than the numbers a harness passed in. */
    var lit = mods.filter(function (m) { return m.state === "computed"; });
    var litCats = catRows.filter(function (c) { return c.status; });
    var contributing = catRows.filter(function (c) { return c.status && c.contributes; });

    /* --- geometry. The module column is the tall one; everything else is measured off it. --- */
    var modRows = mods.length;
    var fldRows = de.fields.length;
    var maxRows = Math.max(modRows, fldRows, cats.length * 2, 12);
    var H = TOP + maxRows * ROW_H + 120;
    var W = COL_PRJ + 190;

    var svg = se("svg", {
      viewBox: "0 0 " + W + " " + H, width: "100%", height: String(H),
      preserveAspectRatio: "xMidYMin meet", class: "nf-svg", role: "img",
      "data-chart": "signal-flow",
      "aria-label": "Signal flow: documents to fields, modules to categories to project health"
    }, container);
    svg.setAttribute("data-modules", String(mods.length));
    svg.setAttribute("data-modules-lit", String(lit.length));
    svg.setAttribute("data-categories", String(cats.length));
    svg.setAttribute("data-categories-lit", String(litCats.length));
    svg.setAttribute("data-documents", String(de.docs.length));
    svg.setAttribute("data-fields", String(de.fields.length));
    svg.setAttribute("data-project-status", String(projectStatus || "none"));

    var edges = se("g", { class: "nf-edges", fill: "none" }, svg);
    var nodes = se("g", { class: "nf-nodes" }, svg);

    /* ------------------------------------------------------------------ column headings --- */
    function heading(x, label, sub) {
      txt(label, x, 22, { class: "nf-col", "font-size": "11.5", "font-weight": "700",
                          fill: "var(--heading, #dfe7f5)", "letter-spacing": ".06em" }, nodes);
      if (sub) {
        txt(sub, x, 38, { class: "nf-colsub", "font-size": "9.5",
                          fill: "var(--muted, #8fa0bd)" }, nodes);
      }
    }
    heading(COL_DOC, "DOCUMENTS", de.docs.length + " contributed a figure");
    heading(COL_FLD, "FIGURES EXTRACTED", de.fields.length + " with a recorded source");
    heading(COL_MOD, "MODULES", lit.length + " of " + mods.length + " have a reading");
    heading(COL_CAT, "CATEGORIES", litCats.length + " of " + cats.length + " carry a status");
    heading(COL_PRJ, "PROJECT HEALTH", null);

    /* ------------------------------------------------ documents, and the fields they gave --- */
    var fldY = Object.create(null), y = TOP;
    de.fields.forEach(function (f) {
      fldY[f.field] = y;
      var g = se("g", { class: "nf-field", "data-field": f.field, "data-doc": f.docId }, nodes);
      se("circle", { cx: COL_FLD + 6, cy: y + 6, r: 3.4, fill: C.Complete,
                     "fill-opacity": ".8" }, g);
      txt(trunc(f.field, 22), COL_FLD + 16, y + 9.5,
          { "font-size": "10", fill: "var(--text, #cdd8ea)" }, g);
      y += ROW_H;
    });
    var docY = Object.create(null), dy = TOP;
    de.docs.forEach(function (d) {
      var ys = d.fields.map(function (f) { return fldY[f]; }).filter(function (v) { return v != null; });
      var centre = ys.length ? (Math.min.apply(null, ys) + Math.max.apply(null, ys)) / 2 : dy;
      docY[d.id] = centre;
      var g = se("g", { class: "nf-doc", "data-doc": d.id, "data-doctype": d.docType,
                        "data-fields": String(d.fields.length) }, nodes);
      se("rect", { x: COL_DOC, y: centre - 12, width: DOC_W, height: 24, rx: 4,
                   fill: "var(--surface-soft, #131c2c)",
                   stroke: C.Complete, "stroke-width": 1.2, "stroke-opacity": ".7" }, g);
      txt(trunc(d.docType.replace(/_/g, " "), 20), COL_DOC + 8, centre - 1,
          { "font-size": "10", "font-weight": "600", fill: "var(--text, #cdd8ea)" }, g);
      txt(d.fields.length + (d.fields.length === 1 ? " figure" : " figures"), COL_DOC + 8, centre + 9,
          { "font-size": "8.5", fill: "var(--muted, #8fa0bd)" }, g);
      dy += 34;
    });
    /* ONE EDGE PER FIGURE ACTUALLY EXTRACTED. This is the only edge on the chart whose
       existence is asserted by the document layer, and every one of them is a row in
       `signal_inputs.sources`. */
    de.fields.forEach(function (f) {
      var y0 = docY[f.docId], y1 = fldY[f.field] + 6;
      if (y0 == null || y1 == null) return;
      var x0 = COL_DOC + DOC_W, x1 = COL_FLD;
      se("path", { d: "M" + x0 + "," + y0 + " C" + (x0 + 34) + "," + y0 + " "
                      + (x1 - 34) + "," + y1 + " " + x1 + "," + y1,
                   stroke: C.Complete, "stroke-width": 1, "stroke-opacity": ".45",
                   class: "nf-edge nf-edge-doc", "data-carries": f.field }, edges);
    });

    /* ---------------------------------------------------------------------- THE BREAK ------ */
    /* NOT AN ORNAMENT. This is the finding: the platform does not record which module read which
       figure, so the chain is broken here and the chart says so in words rather than guessing. */
    var bx = COL_FLD + FLD_W + 18, bw = COL_MOD - bx - 14;
    var brk = se("g", { class: "nf-break", "data-break": "field-to-module" }, nodes);
    se("rect", { x: bx, y: TOP - 6, width: bw, height: Math.max(60, maxRows * ROW_H * 0.55),
                 rx: 5, fill: "none", stroke: "var(--line-strong, #3a4a66)",
                 "stroke-width": 1, "stroke-dasharray": "3 4" }, brk);
    [ "NO LINE IS DRAWN",
      "ACROSS THIS GAP.",
      "",
      "The server records which",
      "document supplied which",
      "figure, and it does not",
      "record which module read",
      "which figure. Drawing an",
      "edge here would be drawing",
      "a line that carried no",
      "figure." ].forEach(function (line, i) {
      txt(line, bx + 9, TOP + 12 + i * 12.5,
          { "font-size": (i < 2 ? "9.5" : "9"), "font-weight": (i < 2 ? "700" : "400"),
            fill: (i < 2 ? "var(--radar-amber, #ff8c1a)" : "var(--muted, #8fa0bd)") }, brk);
    });

    /* ------------------------------------------------------------------------- modules ----- */
    var catY = Object.create(null);
    var catSpacing = Math.max(2 * ROW_H, (maxRows * ROW_H) / Math.max(1, cats.length));
    catRows.forEach(function (c, i) { catY[c.key] = TOP + 14 + i * catSpacing; });

    var my = TOP, modY = Object.create(null);
    mods.forEach(function (m) {
      modY[m.id] = my;
      var g = se("g", { class: "nf-module", "data-module": m.id, "data-state": m.state,
                        "data-category": m.category,
                        "data-band": String(m.band || "") }, nodes);
      paintModule(g, COL_MOD, my, m);
      txt(m.id, COL_MOD + 18, my + 10.5,
          { "font-size": "9.5",
            "font-family": "var(--font-mono, ui-monospace, monospace)",
            fill: (m.state === "computed" ? "var(--text, #cdd8ea)" : "var(--muted, #8fa0bd)"),
            "fill-opacity": (m.state === "computed" ? "1" : ".8") }, g);
      var tail = m.state === "computed" ? (m.display != null ? String(m.display) : "reading")
               : m.state === "abstained" ? "nothing to report"
               : m.state === "not_relevant" ? "not relevant" : "not called";
      txt(trunc(tail, 26), COL_MOD + 52, my + 10.5,
          { "font-size": "9", fill: "var(--muted, #8fa0bd)" }, g);
      /* A TITLE, so the reader can get the module's own words without a tooltip layer. */
      var t = se("title", {}, g);
      t.textContent = m.id + " " + (m.name || "") + " — " + tail
                    + (m.reason ? "\n" + m.reason : "");
      my += ROW_H;
    });

    /* MODULE -> CATEGORY, ONLY FOR A MODULE THAT HAS A READING. This is the rule that makes
       density mean something: a sparse fan is thin evidence, and it is the truth. */
    var drawnModuleEdges = 0;
    mods.forEach(function (m) {
      if (m.state !== "computed") return;
      var y0 = modY[m.id] + 7, y1 = catY[m.category];
      if (y1 == null) return;
      var x0 = COL_MOD + 150, x1 = COL_CAT;
      var col = bandColor(m.band) || C.Complete;
      se("path", { d: "M" + x0 + "," + y0 + " C" + (x0 + 36) + "," + y0 + " "
                      + (x1 - 36) + "," + y1 + " " + x1 + "," + y1,
                   stroke: col, "stroke-width": 1.3, "stroke-opacity": ".7",
                   class: "nf-edge nf-edge-mod",
                   "data-carries": m.id, "data-band": String(m.band || "") }, edges);
      drawnModuleEdges++;
    });

    /* ---------------------------------------------------------------------- categories ----- */
    var drawnCatEdges = 0;
    catRows.forEach(function (c) {
      var cy = catY[c.key];
      var col = bandColor(c.status);
      var g = se("g", { class: "nf-category", "data-category": c.key,
                        "data-state": c.state || "not_called",
                        "data-status": String(c.status || "none"),
                        "data-contributes": String(!!c.contributes) }, nodes);
      var failed = c.state === "failed";
      se("rect", { x: COL_CAT, y: cy - 13, width: CAT_W, height: 26, rx: 4,
                   fill: failed ? C.Red : (col || "var(--surface-soft, #131c2c)"),
                   "fill-opacity": failed ? ".9" : (col ? ".18" : "1"),
                   stroke: failed ? C.Red : (col || "var(--line-strong, #3a4a66)"),
                   "stroke-width": failed ? 2 : 1.2,
                   "stroke-dasharray": (c.state === "not_called" ? "3 3" : null) }, g);
      if (failed) {
        /* FAILED LOOKS WRONG ON PURPOSE. A cross through the body, in addition to the fill,
           so it is not a colour cue alone and cannot be read as a band. */
        se("path", { d: "M" + (COL_CAT + 4) + "," + (cy - 9) + " L" + (COL_CAT + CAT_W - 4) + "," + (cy + 9)
                        + " M" + (COL_CAT + CAT_W - 4) + "," + (cy - 9) + " L" + (COL_CAT + 4) + "," + (cy + 9),
                     stroke: "#fff", "stroke-width": 1.4, "stroke-opacity": ".85" }, g);
      }
      txt(c.key, COL_CAT + 8, cy - 1,
          { "font-size": "10.5", "font-weight": "700",
            fill: failed ? "#fff" : "var(--text, #cdd8ea)" }, g);
      var word = failed ? "FAILED"
               : c.state === "out_of_order" ? "out of order"
               : c.status ? String(c.status)
               : c.state === "abstained" ? "nothing to report"
               : "not called";
      txt(trunc(word + (c.moduleCount ? " · " + c.moduleCount + " lit" : ""), 22),
          COL_CAT + 8, cy + 9,
          { "font-size": "8.5", fill: failed ? "#fff" : "var(--muted, #8fa0bd)" }, g);
      var t = se("title", {}, g);
      t.textContent = c.key + " " + (c.name || "") + " — " + word
                    + (c.reason ? "\n" + c.reason : "");

      /* CATEGORY -> PROJECT, only where a status was stored AND the server's own projection says
         this category votes. `contributes_to_project_status` is read off the row; it is not
         re-decided here. */
      if (c.status && c.contributes) {
        var x0 = COL_CAT + CAT_W, x1 = COL_PRJ;
        var pcol = bandColor(c.status) || C.Complete;
        se("path", { d: "M" + x0 + "," + cy + " C" + (x0 + 30) + "," + cy + " "
                        + (x1 - 30) + "," + (TOP + 60) + " " + x1 + "," + (TOP + 60),
                     stroke: pcol, "stroke-width": 1.6, "stroke-opacity": ".75",
                     class: "nf-edge nf-edge-cat", "data-carries": c.key }, edges);
        drawnCatEdges++;
      }
    });

    /* ------------------------------------------------------------------- project health ---- */
    var pg = se("g", { class: "nf-project", "data-status": String(projectStatus || "none"),
                       "data-voters": String(contributing.length) }, nodes);
    var pcol2 = bandColor(projectStatus);
    se("rect", { x: COL_PRJ, y: TOP + 42, width: 168, height: 40, rx: 6,
                 fill: pcol2 || "var(--surface-soft, #131c2c)",
                 "fill-opacity": pcol2 ? ".22" : "1",
                 stroke: pcol2 || "var(--line-strong, #3a4a66)", "stroke-width": 1.6,
                 "stroke-dasharray": pcol2 ? null : "3 3" }, pg);
    txt(projectStatus || "no status", COL_PRJ + 12, TOP + 62,
        { "font-size": "13", "font-weight": "700",
          fill: pcol2 || "var(--muted, #8fa0bd)" }, pg);
    txt(contributing.length + " of " + cats.length + " categories voted", COL_PRJ + 12, TOP + 76,
        { "font-size": "8.5", fill: "var(--muted, #8fa0bd)" }, pg);

    svg.setAttribute("data-edges-doc", String(de.fields.length));
    svg.setAttribute("data-edges-module", String(drawnModuleEdges));
    svg.setAttribute("data-edges-category", String(drawnCatEdges));

    /* ---------------------------------------------------------------------------- legend --- */
    var ly = TOP + maxRows * ROW_H + 30;
    var legend = se("g", { class: "nf-legend" }, nodes);
    txt("THE FOUR STATES, AND THEY ARE NOT THE SAME THING", COL_DOC, ly,
        { "font-size": "10", "font-weight": "700", "letter-spacing": ".05em",
          fill: "var(--heading, #dfe7f5)" }, legend);
    var items = [
      { state: "computed", label: "has a reading — coloured by its band, and the only state that draws a line" },
      { state: "abstained", label: "nothing to report — the evidence is not there" },
      { state: "not_relevant", label: "not relevant — does not apply to this project type; never called" },
      { state: "not_called", label: "not called yet — no reading of any kind has been stored" },
      { state: "failed", label: "failed — drawn on the category, where the platform stored it" }
    ];
    items.forEach(function (it, i) {
      var yy = ly + 16 + i * 15;
      var g = se("g", { class: "nf-legend-item", "data-state": it.state }, legend);
      if (it.state === "failed") {
        se("rect", { x: COL_DOC + 1, y: yy - 6, width: 12, height: 12, rx: 2,
                     fill: C.Red, stroke: C.Red, "stroke-width": 1.4 }, g);
        se("path", { d: "M" + (COL_DOC + 3) + "," + (yy - 4) + " L" + (COL_DOC + 12) + "," + (yy + 4)
                        + " M" + (COL_DOC + 12) + "," + (yy - 4) + " L" + (COL_DOC + 3) + "," + (yy + 4),
                     stroke: "#fff", "stroke-width": 1.2 }, g);
      } else {
        paintModule(g, COL_DOC, yy - 7, { state: it.state, band: "Green" });
      }
      txt(it.label, COL_DOC + 22, yy + 3.5,
          { "font-size": "9.5", fill: "var(--muted, #8fa0bd)" }, g);
    });

    /* THE CENSUS IN WORDS, under the legend, because the owner reads this on a phone and a
       drawing he cannot zoom into must still state its own figures. */
    var cy2 = ly + 16 + items.length * 15 + 16;
    [ de.docs.length + " document(s) contributed " + de.fields.length
        + " figure(s) with a recorded source.",
      lit.length + " of " + mods.length + " modules have a reading, and only those "
        + drawnModuleEdges + " draw a line into their category.",
      litCats.length + " of " + cats.length + " categories carry a status; "
        + drawnCatEdges + " of them vote on project health."
    ].forEach(function (line, i) {
      txt(line, COL_DOC, cy2 + i * 13,
          { "font-size": "9.5", fill: "var(--text, #cdd8ea)", class: "nf-census" }, legend);
    });

    if (!row) {
      txt("This project has no stored result for this period, so nothing is drawn. "
          + "Nothing is assumed in its place.", COL_DOC, TOP + 4,
          { "font-size": "11", fill: "var(--radar-amber, #ff8c1a)", class: "nf-noresult" }, nodes);
    }
  }

  window.LinNeuralFlow = { render: render };
})();
