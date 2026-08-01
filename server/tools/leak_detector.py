"""
The pre-lock leak detector, shared by every suite that has to prove a response is clean.

WHY THIS IS A MODULE AND NOT A COPY

T4 wrote this detector and proved it against planted leaks before trusting it. T6 needs exactly
the same detector for the expert reference lock. Copying it would have created two definitions of
what counts as a leak, and the moment they drifted, one suite would be proving something weaker
than it claimed while still reporting green. There is precedent for that failure in this
repository: B7b's leak survived eight phases because its grep had a clause that could never be
false.

So there is one definition, imported by both. Adding a marker or field name here strengthens every
suite at once, which is the intended behaviour.

WHY IT RETURNS FINDINGS AND NOT A BOOLEAN

A caller cannot accidentally write an assertion that passes vacuously against a list — the failure
detail names what leaked. `if scan_for_leak(x)` reads the same as `if not scan_for_leak(x)` to a
tired reviewer; `len(...) == 0` with the findings printed does not.

THIS DETECTOR MUST BE PROVEN ABLE TO FAIL. Every suite that imports it runs a self-test block
against deliberately planted leaks before trusting it against a real response.
"""

from __future__ import annotations

# Distinctive markers planted into the package fixture. If any appears in a pre-lock response, the
# treatment has reached the reader.
MARK_RECOMMENDATION = "ZQMARK-RECOMMENDED-ESCALATE-4417"
MARK_ALTERNATIVE = "ZQMARK-ALTERNATIVE-8823"
MARK_CONDITION = "ZQMARK-CONDITION-9911"
MARK_LIMITATION = "ZQMARK-LIMITATION-3355"
MARK_UNCERTAINTY = "ZQMARK-UNCERTAINTY-7702"
MARK_BOUNDARY = "ZQMARK-BOUNDARY-6644"

PACKAGE_MARKERS = (MARK_RECOMMENDATION, MARK_ALTERNATIVE, MARK_CONDITION,
                   MARK_LIMITATION, MARK_UNCERTAINTY, MARK_BOUNDARY)

# Every content-bearing field name on DecisionSupportPackage (from research_decision.HASHED_FIELDS
# plus the identity/integrity fields research_membership's docstring says must not appear either).
PACKAGE_FIELD_NAMES = (
    "recommended_action", "expected_regret", "detected_condition", "alternatives",
    "uncertainty", "limitations", "applicability_boundary", "expiration_trigger",
    "package_id", "package_hash", "approval_status",
)

# The analytical layer's own action vocabulary. These appear in PROSE (evidence_metric), which
# is exactly how the real leak T4 found was shaped — the key was stripped, the sentence was not.
# Scanned case-insensitively.
ACTION_PROSE_MARKERS = ("recommends:", "minimax regret recommends")


def scan_for_leak(blob: str) -> list[str]:
    """
    Return every reason this blob leaks. Empty list means clean.

    Deliberately returns a LIST OF FINDINGS rather than a bool, so a caller cannot accidentally
    write an assertion that passes vacuously — the failure detail names what leaked.
    """
    findings: list[str] = []
    lowered = blob.lower()
    for marker in PACKAGE_MARKERS:
        if marker.lower() in lowered:
            findings.append(f"package marker {marker!r}")
    for name in PACKAGE_FIELD_NAMES:
        if f'"{name}"' in blob:
            findings.append(f"package field name {name!r}")
    for phrase in ACTION_PROSE_MARKERS:
        if phrase in lowered:
            findings.append(f"recommendation prose {phrase!r}")
    return findings
