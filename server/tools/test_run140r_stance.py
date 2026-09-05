#!/usr/bin/env python3
"""
RUN 140 R -- THE STANCE CHANGE, RECORDED AND GUARDED.

Run (from server/):

    python tools/test_run140r_stance.py

THE STANCE CHANGED ON 2026-09-05 BY THE OWNER'S DECISION, WITH RUN 140 AS ITS ORIGIN. Until this
run the platform stated findings and asked a question and never suggested a response. It now also
suggests how to mitigate each non-Green reading, aimed one band up.

WHY THIS CHECK EXISTS AND WHY IT IS NOT DECORATIVE. A stance is carried in prose, and prose has
no test that fails when it goes stale. Ten sites across six files claimed, in the platform's own
voice, that it never suggests a response. Every one of them was found by survey, not by a tool,
which is exactly how the next one will be missed. This check pins the sweep: it asserts the
FALSE claims are gone, the TRUE reasons are still present in their narrowed form, and the change
is recorded as a dated stance change with this run named as its origin.

WHAT IT DELIBERATELY DOES NOT TOUCH. `server/app/simulation/models_cat10.py:156` says "it never
recommends and never approves". That is scoped to that one module, it is unaffected by this
change, and it is under `server/app/simulation/`, which this run must not modify. It is asserted
UNCHANGED here so the sweep is provably complete rather than merely claimed to be.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

PASSED = 0
TOTAL = 0
FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> bool:
    global PASSED, TOTAL
    TOTAL += 1
    if cond:
        PASSED += 1
        print("  [PASS] " + name)
        return True
    FAILS.append(name + (" -- " + detail if detail else ""))
    print("  [FAIL] " + name + (" -- " + detail if detail else ""))
    return False


def read(rel: str) -> str:
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


# Each site: (file, the claim that must be GONE as a live assertion, the narrowed truth that
# must be PRESENT). The "gone" strings are the exact sentences the survey found.
SITES = [
    ("server/app/decision_brief.py",
     "It does not produce an\naction recommendation.",
     "RECORDED, REPLAYABLE MODEL COMPOSITION"),
    ("server/app/decision_brief.py",
     "prescribes an action, assigns an authority",
     "A model COMPOSES CANDIDATE MITIGATIONS, and only those."),
    ("server/app/decision_brief.py",
     '"Resequence work now" is an instruction,\nand this module does not write one.',
     "The line is not imperative mood; it is\nWHO AND WHEN."),
    ("server/app/decision_brief.py",
     "It does not ask them to approve a remedy,\n    because no remedy is offered",
     "THE QUESTION ITSELF IS UNCHANGED BY RUN 140"),
    ("server/app/document_evidence.py",
     "never as advice: this module reports, it does not recommend.",
     "RUN 140 SCOPES THAT SENTENCE AND DOES NOT DELETE IT."),
    ("assets/js/decision-ui.js",
     "and it is not composed from any figure, so it cannot drift into a recommendation.\n\n     THE REASONS",
     "THE FINAL CLAUSE IS NOW FALSE AND IS WITHDRAWN."),
    ("assets/js/decision-ui.js",
     "It does NOT produce an\n     action recommendation:",
     "RECORDED, REPLAYABLE MODEL COMPOSITION"),
    ("assets/js/decision-ui.js",
     "a status, a driver, a threshold, an action, an authority, or whether evidence was adequate.",
     "THE ONE CARVE-OUT, RUN 140"),
    ("assets/js/export.js",
     "the\n      // platform states a finding and issues no action, no remedy and no authority, and an",
     "RUN 140 NARROWS THE GENERAL CLAUSE"),
    ("assets/js/decision.js",
     "The card's premise is that the platform states a finding\n   and never issues an action",
     "RUN 140 NARROWS THAT PREMISE"),
]

# The reasons that are STILL TRUE and load-bearing. If one of these disappears, the sweep
# deleted a constraint instead of narrowing a claim.
REASONS_KEPT = [
    ("server/app/decision_brief.py", "no deadline here, no approval authority"),
    ("server/app/decision_brief.py",
     "asserting an authority the instrument has never been given"),
    ("server/app/decision_brief.py", "No model decides a status, chooses a\ndriver"),
    ("server/app/decision_brief.py", "It names no authority, because the platform holds none"),
    ("assets/js/decision.js", "it assigns NO owner, sets NO deadline, names NO authority"),
    ("assets/js/export.js", "the platform\n      // holds NO authority, assigns NO owner, sets NO deadline"),
    ("assets/js/decision-ui.js", "never sets a deadline or a date; never invents a figure"),
    ("assets/js/app.js", "nothing here triggers any action on its own."),
]


def main() -> int:
    print("THE TEN WORDING SITES: the false claim gone, the narrowed truth present.")
    for rel, gone, present in SITES:
        src = read(rel)
        check(rel + ": the superseded claim is no longer asserted (" +
              gone.replace("\n", " ")[:52] + "...)", gone not in src)
        check(rel + ": the narrowed wording is present (" + present[:52] + "...)",
              present in src)

    print("\nTHE REASONS THAT ARE STILL TRUE WERE NARROWED, NOT DELETED.")
    for rel, kept in REASONS_KEPT:
        check(rel + ": still states \"" + kept.replace("\n", " ")[:56] + "...\"",
              kept in read(rel))

    print("\nTHE CHANGE IS RECORDED AS A DATED STANCE CHANGE NAMING THIS RUN AS ITS ORIGIN.")
    for rel in ("server/app/decision_brief.py", "assets/js/decision-ui.js"):
        src = read(rel)
        check(rel + ": names the date 2026-09-05", "2026-09-05" in src)
        check(rel + ": names Run 140", "RUN 140" in src or "Run 140" in src)
        check(rel + ": records it as the ORIGIN of the change",
              "origin of the change" in src.lower())
    check("decision_brief.py states the direction: one band up, Red->Amber->Yellow->Green",
          "Red toward Amber,\nAmber toward Yellow, Yellow toward Green" in
          read("server/app/decision_brief.py"))

    print("\nTHE FOOTER THE REVIEWER READS WAS UPDATED.")
    app = read("assets/js/app.js")
    check("the footer no longer claims the platform only states a finding and a question",
          '<p class="dc-note">The platform states a finding and a question. A named human'
          not in app)
    check("the footer states that candidate mitigations are offered",
          "offers candidate mitigations for each reading that is not Green" in app)
    check("the footer states a candidate is not an instruction and names nobody",
          "it names no owner, no authority and no date" in app)
    check("the footer keeps the sentence that is still true",
          "nothing here triggers any action on its own." in app)

    print("\nOUT OF SCOPE, ASSERTED UNCHANGED.")
    sim = read("server/app/simulation/models_cat10.py")
    check("simulation/models_cat10.py still reads \"it never recommends and never approves\" "
          "(scoped to that module; under simulation/, not to be touched)",
          "it never recommends and never approves" in sim)

    print("\nRESULT: " + str(PASSED) + "/" + str(TOTAL) + " checks passed")
    if FAILS:
        for f in FAILS:
            print("  FAILED: " + f)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
