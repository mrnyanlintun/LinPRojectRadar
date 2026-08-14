"""
RUN 25. THE DECLARED PRODUCTION CHANGES OF THE RAIL REMOVAL.

WHY A FOURTH MANIFEST. `run20_production_changes.py`, `run21_production_changes.py` and
`run23_production_changes.py` each record what their own run changed against the immovable
Run-20 freeze in `code_audit/run20_production_freeze.sha256`. Folding this run's files into
any of them would falsify that run's record. The guard's property is unchanged: the set of
production files whose bytes differ from the Run-20 freeze must equal EXACTLY the union of
what the manifests declare.

`assets/js/detail.js` and `assets/css/radar.css` are NOT repeated here. Run 23 already
declares both, they already differ from the Run-20 freeze, and declaring either twice would
let one change be counted as two. Run 25 changed them again -- it removed the section
navigator rail from both -- and what that change was is recorded in the files themselves, in
REPORT_2026-08-14_rail-and-empty-diagram.md and in the superseding freeze record
research/freeze/RUN25_RAIL_REMOVAL_FREEZE_2026-08-14.json.

Each entry is (authority, path, why).
"""

from __future__ import annotations

RUN25_PRODUCTION_CHANGES: dict[str, tuple[str, str, str]] = {
    "RAIL.1 index": (
        "owner instruction of 2026-08-14: remove the left rail entirely",
        "index.html",
        "THE LEFT RAIL IS GONE, ON THE OWNER'S EXPLICIT ORDER. The served page carried a "
        "fixed left-hand section navigator (nav#detail-secnav): a column of numbered controls "
        "listing the detail page's collapsible sections. Earlier instructions said it stays "
        "and Runs 16, 23 and 24 guarded its presence; the owner's 2026-08-14 instruction "
        "reverses that and orders the whole rail removed, numbered list and any paging "
        "control beneath it. The element is removed from the page; its builder leaves "
        "assets/js/detail.js and its styles leave assets/css/radar.css, both of which Run 23 "
        "already declares. Sections remain reachable by their own headers. Display only: no "
        "count, no threshold, no status rule and nothing under server/app/simulation/ "
        "changed. The reversal is recorded in code_audit/run20_anti_fossilization_register.csv "
        "as an owner-directed contract change."),
}
