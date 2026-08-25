# Run-59 successor freeze report

**Disposition: FINAL_FREEZE_ACCEPTED** for `sim-2026.08-v39`.

## Why there is a successor at all

**No behaviour moved.** Six of the 242 governed production-tree members moved and every one of
the six edits is a comment or a document heading. The stamp advances because the MANIFEST
advances, which is the version-boundary rule working as intended, and because one of the six is
`assets/js/decision-ui.js`, a **sequence-bearing** participant file. What a participant reads and
clicks is part of the frozen candidate, so v38 is **superseded, not amended** -- even though what
a participant reads and clicks is, in this release, byte for byte what it was.

    v25 accepted freeze -> ... -> v37 -> the two reset controls merged into one -> v38
    -> no markdown document carries authority -> v39 successor

## The ruling, and what it became

| ruling | what was built |
|---|---|
| No markdown document carries authority | Eight documents corrected against production, not five: an uncapped sweep added `COPY_GLOSSARY.md`, `README.md` and `BACKEND_CHANGES_NEEDED.md` to Run 58's inventory of five. |
| The five code citations of the superseded rule | **Dropped in all five**, the reason stated directly. `research_export.py` cited it by number as "rule 6"; `portfolio_health.py` cited "NAMING_AUTHORITY section 4", which is the section that RECORDED THE REVERSAL. Established by execution that no test reads any of those comment strings. |
| The registered count | `MODULE_RETIREMENT_DECISIONS.md` said the REGISTERED count fell 101 to 63. It is the IN-SERVICE count that fell. Corrected. |
| The count floats | `GROUP_ASSIGNMENT.md` and `p0-baseline/MODULE_TAXONOMY.md` now mark their figures as the figure at a date. **No new number was invented.** |
| The specification floats | Its CONTROLLING designation is withdrawn from `production_tree.py` and the read-first order from `WORKER_BRIEF.md`. It is NOT deleted, NOT renamed and NOT removed from the authority tree, whose manifest sha256 is unmoved for a fifth run. |
| No check may assert a markdown document's content | Four guards **re-pointed** at production oracles, each proved still able to fail BY BREAKING PRODUCTION. Fifteen checks **retired the way modules were retired**: they stop running, their bodies are not deleted, the reason is recorded. Two **stopped**, because re-pointing them would have meant inventing an oracle. **No check was deleted.** |

## What a participant reads and clicks, before and after

**Identical.** One file a participant loads moved, `assets/js/decision-ui.js`, and it is
sequence-bearing, so this link carries a **named exception of record** in
`V23_TO_V24_SEQUENCE_EXCEPTION` rather than a discovery by checksum. What moved inside it is
proved to be a comment and nothing else: the file is byte-identical to v23 once block comments
are stripped, and `GROUP_NAMES` and `MODULE_NAMES` are byte-identical across the link. The other
four members of `SEQUENCE_BEARING_FILES_FROM_V21` are present and byte-identical, measured.

NO STORED FIGURE MOVED. No formula, band, threshold, calibration, abstention rule or population
moved: voting is still exactly A1.7 and A1.8, 63 modules in service of 101 registered, and the
behaviour digest is RE-DERIVED and unchanged.

## Gate

15 blocker classes evaluated, 0 blocked. Artifact:
`research/freeze/run59_successor_freeze_gate.csv`.

The v25 to v38 release records are preserved unchanged and still record their own stamps.
