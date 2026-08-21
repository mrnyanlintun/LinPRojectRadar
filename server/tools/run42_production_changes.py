"""
RUN 42. THE PRODUCTION FILES THIS RUN CHANGED, DECLARED.

WHY THIS FILE EXISTS, and it is the Run-28/29/30/31/32/33/36/41 precedent unchanged. The Run-20
baseline freeze compares production bytes against a pinned baseline, and the declared-changes
guard requires the differing set and the declared set to be EXACTLY equal -- so an undeclared
production edit is red and a declared file that was never touched is red too.

IT IS DECLARED HERE AND NOT FOLDED INTO AN EARLIER RUN'S LIST. A run's manifest is the record of
what THAT run did, and merging them would falsify both.

RUN 42 CREATED NO PRODUCTION FILE and changed five. Only ONE of them is declared here:
`server/app/simulation/qualification.py`. The other four -- `extraction_merge.py`, `compute.py`,
`documents.py` and `models.py` -- are already declared by earlier runs' manifests, and no path
may appear in two manifests, because one change may never be counted as two.

Each entry is (authority, path, why).
"""

from __future__ import annotations

_OWNER = ("owner instruction of 2026-08-21: fix the background data-processing and calculation "
          "mechanism, and specifically the missing document-to-fact-to-module lineage. The "
          "repair moves bytes inside a frozen surface, which is why Run 42 is a freeze successor "
          "(sim-2026.08-v27) rather than a repair inside v26")

#: Production files Run 42 CREATED.
RUN42_NEW_PRODUCTION_FILES: dict[str, str] = {}

#: Production files Run 42 CHANGED.
RUN42_PRODUCTION_CHANGES: dict[str, tuple[str, str, str]] = {
    "L1": (
        _OWNER,
        "server/app/simulation/qualification.py",
        "THE DIMENSION REASONS MUST DESCRIBE THE STATE ACTUALLY REACHED. Run 42's repair is in "
        "extraction_merge.py: the per-field source record now carries the document identity that "
        "every observation has always held, so `_provenance` -- which counts a field as traced "
        "only when it carries BOTH a documentId and a documentVersion -- can count more than "
        "zero for the first time, and `_timeliness` can see an asOf. Before the repair both "
        "dimensions were STRUCTURALLY pinned to PARTIAL: no input could ever have moved them, "
        "which is why the qualification record reported zero traced fields on every project ever "
        "computed. This file changes only because PROVENANCE_PARTIAL_REASON and "
        "TIMELINESS_PARTIAL_REASON are absolute sentences -- 'No document identity and no "
        "document version is recorded' -- and emitting either beside a PASS would put a false "
        "statement into the one object downstream readers are entitled to trust. Two PASS "
        "reasons are added and selected when the dimension passes; the stale comment claiming "
        "the repository has no per-field document identity is corrected. NO THRESHOLD, NO RULE "
        "AND NO STATE VOCABULARY IS CHANGED: the counting is identical, `_overall` is still the "
        "weakest of the dimensions, `revision_resolution_status` is still NOT_ESTIMABLE and the "
        "overall qualification state therefore still comes back NOT_ESTIMABLE. That the gate was "
        "not relaxed is proved by execution, not asserted: "
        "code_audit/run42_v26_v27_execution_proof.csv runs the whole registered population on "
        "both pinned lines and records that all 101 module rows are byte-identical and that "
        "revision_resolution_status and overall_qualification_state do not move.",
    ),
}
