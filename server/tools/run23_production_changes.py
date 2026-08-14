"""
POST-RUN-22 UI CORRECTION. THE DECLARED PRODUCTION CHANGES OF THIS CORRECTION.

WHY A THIRD MANIFEST. `run20_production_changes.py` records what Run 20 changed and
`run21_production_changes.py` what Run 21 changed, both checked against the immovable Run-20
freeze in `code_audit/run20_production_freeze.sha256`. Folding this correction's files into
either would falsify that run's own record. The guard's property is unchanged: the set of
production files whose bytes differ from the Run-20 freeze must equal EXACTLY the union of what
the manifests declare, so an undeclared production edit is still red and a declared file that
was never touched is still red.

`assets/js/neural_flow.js` is NOT repeated here. Run 21 already declares it, it already differs
from the Run-20 freeze, and declaring it twice would let one change be counted as two. This
correction changed it again; what that change was is recorded in the file itself, in
REPORT_2026-08-14_post-run22-signal-flow-ui-correction.md and in the superseding freeze record.

Each entry is (authority, path, why).
"""

from __future__ import annotations

RUN23_PRODUCTION_CHANGES: dict[str, tuple[str, str, str]] = {
    "NAV.1 detail": (
        "post-Run-22 UI correction, sections 5 and 6",
        "assets/js/detail.js",
        "SELECTED AND ACTIVE WERE THE SAME WORD. The left-hand numbered Signal rail marked its "
        "chosen entry with the class `active` -- the same vocabulary the Signal Flow uses for a "
        "category that carries current project evidence -- so a navigation state and an "
        "analytical state were indistinguishable in the code and nothing prevented a stylesheet "
        "from making them indistinguishable on screen. The rail now marks selection with "
        "`selected` plus `aria-current`, which assistive technology was not being given at all, "
        "and `data-active` is never set on a rail control. Second defect in the same handler: "
        "the selected entry was set ONLY by the scroll-spy observer, so clicking a control whose "
        "section was already in view selected nothing and the reader got no confirmation that "
        "the control had done anything. The click now sets the selection itself. No section, "
        "label, ordering or scroll behaviour changed."),
    "NAV.2 rail-styles": (
        "post-Run-22 UI correction, sections 5 and 7",
        "assets/css/radar.css",
        "THE RAIL WAS DIMMED AND, BELOW 700px, ABSENT. It rendered at opacity .7 until hovered, "
        "which reads as decoration rather than as usable navigation, and the mobile breakpoint "
        "was `display: none`, so on a phone viewport every numbered control was unreachable -- "
        "the navigation was removed rather than adapted. The rail is opaque now and lays out as "
        "a single horizontal row pinned to the bottom of the viewport below 700px, measured in a "
        "real browser at 390px with all controls present, displayed and hit-testable. The "
        "selected-state rules key on `selected` / `aria-current` only, never on `data-active`, "
        "so a navigation selection and an analytical activation cannot be styled by the same "
        "selector by accident. No collapse or hide control was introduced; none exists."),
}
