"""
RUN 44. THE PRODUCTION FILES THIS RUN CHANGED, DECLARED.

WHY THIS FILE EXISTS, and it is the Run-28/29/30/31/32/33/36/41/42/43 precedent unchanged. The
Run-20 baseline freeze compares production bytes against a pinned baseline, and the
declared-changes guard requires the differing set and the declared set to be EXACTLY equal -- so
an undeclared production edit is red, and a declared file that was never touched is red too.

IT IS DECLARED HERE AND NOT FOLDED INTO AN EARLIER RUN'S LIST. A run's manifest is the record of
what THAT run did, and merging them would falsify both.

RUN 44 IS THE REPAIR OF THE PARTICIPANT-FACING RENDER DEFECTS Run 43J diagnosed. It declares only
the production paths no earlier manifest already names. `assets/js/detail.js`,
`assets/js/deepdive.js`, `assets/css/radar.css`, `server/app/simulation/registry.py` and
`server/app/simulation/models.py` are NOT declared here, because earlier manifests already
declare each of them and no path may appear in two -- one change may never be counted as two.

WHAT THIS RUN CHANGED IN THOSE ALREADY-DECLARED FILES, recorded here so the reader of this
manifest is not left to infer it from a checksum:

  * `assets/js/detail.js` -- the two severity `order` maps became ONE case-insensitive rank,
    because the platform emits both casings and a module storing lowercase 'green' was ranking
    as more adverse than 'Green'; no site names a module as the driver of a severity better than
    its own; and an absent document-risk score renders as absent rather than as "0.00" Green,
    while a genuine stored zero still renders as zero.
  * `assets/js/deepdive.js` -- the Portfolio Health flyout's reason sentence, on the owner's
    order at Run 44 section 4.4. This is the one sequence-bearing file the run was authorised to
    move, and it is declared as such in participant_packages.V14_TO_V15_SEQUENCE_EXCEPTION.
  * `assets/css/radar.css` -- one added rule, `.ds-computed`.
  * `server/app/simulation/registry.py` -- a DOCSTRING only. `available_modules()` described the
    retirement-reason refusal Phase F withdrew; the function's body is untouched, and the
    v28 -> v29 execution proof shows every one of the 101 rows is byte-identical.
  * `server/app/simulation/models.py` -- the stamp and its boundary note.

Each entry is (authority, path, why).
"""

from __future__ import annotations

_OWNER = ("owner's order of 2026-08-22, Run 44 sections 4.1 to 4.5: the participant-facing "
          "render defects Run 43J classified F are repaired at the render, where they are. "
          "Storage was correct in every one of them and is untouched: the document-risk score is "
          "stored present-and-null by design, CPI and SPI are derived values in a derived-values "
          "slot with no source record, and the category status is the server's own fusion. No "
          "server computation changed, and that is proved by executing both lines rather than "
          "read off a diff")

#: Production files Run 44 CREATED.
RUN44_NEW_PRODUCTION_FILES: dict[str, str] = {}

#: Production files Run 44 CHANGED.
RUN44_PRODUCTION_CHANGES: dict[str, tuple[str, str, str]] = {
    "R1": (
        _OWNER,
        "assets/js/signals.js",
        "THE EXTRACTED MARK, AND THE PANEL HEADING ABOVE IT. `extractedTableHtml` stamped every "
        "row that carried a value with the extracted mark, with no test of whether the field was "
        "read from a document or derived from two that were. CPI and SPI are computed by "
        "`select_signal_inputs` and carry no entry in `signal_inputs.sources`, so they were shown "
        "as extracted with no source to show. The two rows now declare themselves computed and "
        "the mark reads them; the heading says Signal inputs rather than asserting that every row "
        "beneath it was extracted; and the upload result line, which begins with the word "
        "extracted, says which of the figures it names were computed. Nothing about what is read, "
        "stored or displayed as a VALUE changed, and no control was added, moved or removed.",
    ),
}
