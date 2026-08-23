"""
RUN 51. THE PRODUCTION FILES THIS RUN CHANGED, DECLARED.

WHY THIS FILE EXISTS, and it is the Run-28/29/30/31/32/33/36/41/42/43/44 precedent unchanged.
The Run-20 baseline freeze compares production bytes against a pinned baseline, and the
declared-changes guard requires the differing set and the declared set to be EXACTLY equal -- so
an undeclared production edit is red, and a declared file that was never touched is red too.

IT IS DECLARED HERE AND NOT FOLDED INTO AN EARLIER RUN'S LIST. A run's manifest is the record of
what THAT run did, and merging them would falsify both.

RUN 51 IS THE DELIVERY OF THE SIX RULINGS RUN 50 STOPPED ON. It declares only the production
paths no earlier manifest already names. `assets/js/detail.js`, `assets/js/deepdive.js`,
`assets/js/knowledge.js`, `assets/js/signals.js`, `assets/js/taxonomy.js`,
`assets/js/categories.js`, `assets/js/charts3d.js`, `assets/js/neural_flow.js`,
`assets/js/decision-ui.js`, `assets/js/ds_defensibility_data.js`, `assets/js/workspace.js`,
`index.html` and `server/app/simulation/models.py` are NOT declared here, because earlier
manifests already declare each of them and no path may appear in two -- one change may never be
counted as two.

WHAT THIS RUN CHANGED IN THOSE ALREADY-DECLARED FILES, recorded here so the reader of this
manifest is not left to infer it from a checksum:

  * `assets/js/deepdive.js` -- SEQUENCE-BEARING. The Portfolio Health flyout is DELETED with its
    six symbols and the three buttons inside them; the eight-module compliance panel is SPLIT
    into two panels, one per current category; the panel label map and the panel bucket map are
    replaced by ONE table of category keys from which both are derived through the loaded
    taxonomy, correcting seven mis-filings; and the grouping loop's bound is derived from the
    taxonomy rather than a literal ten.
  * `assets/js/detail.js` -- the key/label separation, and the executive brief lists category
    NAMES where it listed category identifiers.
  * `assets/js/knowledge.js` -- every count of modules or categories derives; the Signal Stack
    SVG's ten module identifiers and its accessible name are corrected.
  * `assets/js/signals.js` -- the key/label separation and the document group labels.
  * `assets/js/taxonomy.js`, `assets/js/categories.js` -- GENERATED, regenerated from the
    authority after `num` became `key` and after the generator began emitting the derived counts.
  * `assets/js/charts3d.js`, `assets/js/neural_flow.js`, `assets/js/decision-ui.js`,
    `assets/js/ds_defensibility_data.js`, `assets/js/workspace.js` -- the dash and ampersand
    sweep, and, in neural_flow.js, the word beside three derived counts.
  * `index.html` -- three typed counts become spans filled from the taxonomy.
  * `server/app/simulation/models.py` -- the stamp and its boundary note.

Each entry is (authority, path, why).
"""

from __future__ import annotations

_OWNER = ("owner's order of 2026-08-22, Run 51 section 3, rulings 1 to 6: delete the Portfolio "
          "Health flyout; separate the taxonomy's key from the label it was being rendered as; "
          "split the compliance panel by category; sweep every en dash and em dash from "
          "user-facing text; correct the category mis-filings; and derive the deep-dive grouping "
          "bound from the taxonomy")

#: Production files Run 51 CREATED.
RUN51_NEW_PRODUCTION_FILES: dict[str, str] = {}

#: Production files Run 51 CHANGED.
RUN51_PRODUCTION_CHANGES: dict[str, tuple[str, str, str]] = {
    "R1": (_OWNER, "assets/js/app.js",
           "RULING 2 AND SECTION 6.1. The Signal Ledger rendered the module's and the category's "
           "primary key as visible text: 63 module chips and 11 category chips, counted in the "
           "rendered DOM. Both spans are gone and the category's colour is carried by a swatch "
           "that reads no identifier. The About page's three typed counts are filled from "
           "window.LIN_TAXONOMY_COUNTS, which the taxonomy generator writes from "
           "registry_index() and service_index(). No control was added, moved or removed."),
    "R2": (_OWNER, "assets/js/decision.js",
           "SEQUENCE-BEARING. RULING 2. The action plan's trigger lines concatenated a category "
           "identifier and a module identifier into rendered text. They now name the category "
           "and the module. The field read for dispatch is renamed to `key`, which is what it "
           "is. No rule, no severity, no threshold and no ordering moved."),
    "R3": (_OWNER, "assets/js/export.js",
           "RULING 2. The exported workbook carried an identifier column beside each name "
           "column, filled from the taxonomy's primary key. An exported workbook is user-facing "
           "text, so the two identifier columns are removed rather than blanked."),
    "R4": (_OWNER, "assets/js/projectnet2d.js",
           "RULING 2. The click callout carried the module's key; the sort now reads `key` and "
           "the callout carries the name."),
    "R5": (_OWNER, "assets/js/admin-ops.js",
           "RULING 4. Six rendered placeholders that were a bare em dash now say what they mean."),
    "R6": (_OWNER, "assets/js/auditor.js",
           "RULING 4. Rendered placeholders and one model prompt lose their em dashes."),
    "R7": (_OWNER, "assets/js/ingest.js",
           "RULING 4. One rendered placeholder loses its em dash."),
    "R8": (_OWNER, "assets/js/store.js",
           "RULING 4. One console separator loses its em dash."),
    "R9": (_OWNER, "assets/questionnaires/intake.json",
           "SEQUENCE-BEARING. RULING 4. Em dashes inside existing participant-facing labels and "
           "notes are replaced by words. NO ITEM, NO RESPONSE OPTION, NO SCALE AND NO ORDER "
           "CHANGED, asserted structurally rather than by byte-identity."),
    "R10": (_OWNER, "assets/questionnaires/debrief.json",
            "SEQUENCE-BEARING. RULING 4. One em dash in the placeholder notice. No item, no "
            "response option, no scale and no order changed."),
    "R11": (_OWNER, "assets/visualizations/pceif_neural_signal_flow.html",
            "RULING 4. The page title and its heading lose an em dash each."),
}
