"""
RUN 28 CLOSURE. THE PARTICIPANT PACKAGE CHAIN, DECLARED ONCE.

WHY A DECLARATION FILE. The chain has three links now and each is a different KIND of evidence:
v1 exists only inside a git object, v2 exists only inside a git object, and v3 is the tree you are
standing in. A guard that had to work that out from filenames would eventually get it wrong, and
the failure mode is the one this programme has already met twice -- a record that describes the
CURRENT tree while carrying a PREDECESSOR's name.

THE RULE THIS ENCODES. Exactly one record in the chain describes the live tree, and it is the one
marked current. Every other record must be reconstructible from the commit named beside it and
must NOT match the live tree, because if it did, either nothing changed or a predecessor has been
rewritten to agree with the present.
"""

from __future__ import annotations

from typing import NamedTuple


class Package(NamedTuple):
    identifier: str
    #: The checksum record, relative to the repository root.
    record: str
    #: The commit whose blobs the record describes. `None` means the live working tree.
    source_commit: str | None
    #: Why this link exists at all.
    why: str


#: Oldest first. Append; never edit a row, because each row is the evidence for the results
#: collected under that package.
PARTICIPANT_PACKAGES: tuple[Package, ...] = (
    Package(
        "og-participant-2026.08-v1",
        "code_audit/run12_participant_package_checksums.sha256",
        "c44e3ced94a22a9def35fa5a2be3a2268fbed6bb",
        "Run 12 Gates 11-12 froze the participant package for the study. Fourteen of its seventy "
        "files have legitimately moved on since, through Runs 21 to 26 and the Run-28 closure, so "
        "the LIVE TREE IS NOT EVIDENCE FOR IT and it is reconstructed from this commit.",
    ),
    Package(
        "og-participant-2026.08-v2",
        "code_audit/run28_closure_participant_package_checksums.sha256",
        "0293dc5dff40c66a61bc0f57330611de96c4f7b0",
        "The Run-28 closure's FIRST pass propagated the two approved Category-1 renames -- "
        "Regression to Mean CPI and ICE Ratio -- into assets/js/taxonomy.js, the participant "
        "ledger's own name source, which changed the package checksum and required a successor.",
    ),
    Package(
        "og-participant-2026.08-v3",
        "code_audit/run28_closure_v3_participant_package_checksums.sha256",
        None,
        "The Run-28 closure's SECOND pass applied the owner's A1.1 decision -- Monte Carlo EAC "
        "becomes Monte Carlo EAC Forecast -- to the naming authority and re-propagated it. Eleven "
        "package files carry that name and their bytes moved after the v2 record was taken. The "
        "second pass REGENERATED THE v2 RECORD IN PLACE instead of creating this successor, which "
        "made a record describe the tree rather than the package it names; the v2 record has been "
        "restored to its frozen bytes and this is the successor that should have been created.",
    ),
)

#: The one link that describes the working tree.
CURRENT = PARTICIPANT_PACKAGES[-1]

#: The files whose bytes moved between v2 and v3, and the ONLY change permitted in them: the
#: owner's A1.1 rename. Every one is a display surface. The normalisation below maps a current
#: file back to its v2-era text; byte identity after it is the proof that nothing else moved.
V2_TO_V3_CHANGED = (
    "assets/js/categories.js",
    "assets/js/charts3d.js",
    "assets/js/decision-ui.js",
    "assets/js/deepdive.js",
    "assets/js/ds_defensibility_data.js",
    "assets/js/ds_defensibility_evidence.js",
    "assets/js/knowledge.js",
    "assets/js/neural_flow.js",
    "assets/js/recommendation_options.js",
    "assets/js/taxonomy.js",
    "assets/js/workspace.js",
)

#: The inverse of the rename, applied longest-first. The last three entries undo de-duplications
#: the rename itself required: the v2-era prose said "Monte Carlo EAC Monte Carlo outputs" and
#: "Monte Carlo EAC forecast", and renaming without collapsing those would have produced
#: "Monte Carlo EAC Forecast Monte Carlo outputs" and "Monte Carlo EAC Forecast forecast".
_INVERSE_RENAME = (
    ("Monte Carlo EAC Forecast outputs", "Monte Carlo EAC Monte Carlo outputs"),
    ("the schedule analogue of the Monte Carlo EAC Forecast.",
     "the schedule analogue of the Monte Carlo EAC Monte Carlo cost forecast."),
    ("the full Monte Carlo EAC Forecast run", "the full Monte Carlo EAC Monte Carlo run"),
    ("<h3>Monte Carlo EAC Forecast, why a range",
     "<h3>Monte Carlo EAC forecast, why a range"),
    ('["green","Monte Carlo EAC Forecast"', '["green","Monte Carlo EAC forecast"'),
    ("Monte Carlo EAC Forecast", "Monte Carlo EAC"),
)


def to_v2_era(text: str) -> str:
    """Map a current package file back through the A1.1 rename to its v2-era text."""
    for new, old in _INVERSE_RENAME:
        text = text.replace(new, old)
    return text


#: The participant PROTOCOL surface inside the package: every file that carries a step of the
#: decision sequence, the reveal gate, the lock, the randomization, the server contract or the
#: append-only record. NONE of these may differ between v2 and v3 by a single byte. Derived from
#: what each file does, not from what it is named: `decision.js` and `decision-ui.js` are not the
#: same thing -- the first runs the sequence, the second holds a module-id-to-display-name table --
#: and only the second is in the changed list above.
PROTOCOL_SURFACE = (
    "assets/js/decision.js",
    "assets/js/store.js",
    "assets/js/app.js",
    "assets/js/auth.js",
    "assets/js/data.js",
    "assets/js/signals.js",
    "assets/js/detail.js",
    "assets/js/questionnaires.js",
    "assets/js/disclaimers.js",
    "assets/js/features.js",
    "assets/js/config.js",
    "assets/js/export.js",
    "assets/js/training.js",
    "assets/questionnaires/intake.json",
    "assets/questionnaires/debrief.json",
    "index.html",
)
