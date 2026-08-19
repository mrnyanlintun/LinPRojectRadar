"""
RUN 41. THE PRODUCTION FILES THIS RUN CHANGED, DECLARED.

WHY THIS FILE EXISTS, and it is the Run-28/29/30/31/32/33/36 precedent unchanged. The Run-20
baseline freeze compares production bytes against a pinned baseline, and the declared-changes
guard requires the differing set and the declared set to be EXACTLY equal -- so an undeclared
production edit is red and a declared file that was never touched is red too.

IT IS DECLARED HERE AND NOT FOLDED INTO AN EARLIER RUN'S LIST. A run's manifest is the record of
what THAT run did, and merging them would falsify both.

RUN 41 CREATED ONE PRODUCTION FILE and CHANGED ONE. The created file is the alembic migration
carrying finding S2; the changed file is main.py, carrying finding S1. `models.py` is NOT declared
here, because Run 28 already declares it and no path may appear in two manifests -- one change may
never be counted as two.

Each entry is (authority, path, why).
"""

from __future__ import annotations

_OWNER = ("owner ruling of 2026-08-19 on the two HIGH defects confirmed by Run 40: FIX BOTH "
          "BEFORE PARTICIPANT USE. Neither risk is accepted for the study period, and neither "
          "fix may be applied silently, because both move a byte inside a frozen surface -- "
          "which is why Run 41 is a freeze successor rather than a repair inside v25")

#: Production files Run 41 CREATED.
RUN41_NEW_PRODUCTION_FILES: dict[str, str] = {
    "server/alembic/versions/0026_final_lock_guard.py":
        "FINDING S2, THE FINAL-LOCK DATABASE GUARD. Migration 0003 put the PRELIMINARY judgment "
        "beyond the reach of raw SQL, because that judgment is the measurement the study rests "
        "on. The FINAL response never got the same treatment, and Run 41 reproduced the "
        "consequence on the v25 schema with the decision driven to final lock entirely through "
        "the real application routes: with final_submitted_at set, 13 of 13 direct UPDATE "
        "statements succeeded, rewriting every substantive component of the participant's final "
        "judgment and clearing final_submitted_at itself. The final response is primary outcome "
        "data; an instrument in which it can be edited after the fact, without trace, cannot "
        "support a claim about what participants decided. This migration adds "
        "trg_decisions_final_lock_guard, mirroring the preliminary-lock guard onto the final "
        "side on both Postgres and SQLite. The protected column list was DERIVED, not chosen: "
        "run41_derive_final_fields.py reads the AST of a_researchdecision, the only route that "
        "records a final response, and cross-checks every assignment it makes against "
        "EXPORT_COLUMNS. Both authorities agree on thirteen names -- twelve substantive fields "
        "plus the lock timestamp, the last protected because a guard keyed off a predicate it "
        "permits to be cleared is bypassable in two statements. Before the lock, nothing "
        "changes; the governed flow writes all thirteen columns in the same statement that "
        "first sets final_submitted_at, and that statement is permitted precisely because "
        "OLD.final_submitted_at is still NULL.",
}

#: Production files Run 41 CHANGED.
RUN41_PRODUCTION_CHANGES: dict[str, tuple[str, str, str]] = {
    "S1": (
        _OWNER,
        "server/app/main.py",
        "FINDING S1, STORED XSS AND CONTENT-TYPE SPOOFING AT THE DOCUMENT-SERVING BOUNDARY. The "
        "mime_type stored at upload is CLIENT-SUPPLIED and never validated, and "
        "GET /documents/{id}/content echoed it as the response Content-Type with "
        "Content-Disposition: inline and no nosniff. Because assets/js/files.js loads that route "
        "inside a same-origin iframe to preview a document, an authenticated uploader could "
        "serve active content -- text/html or image/svg+xml carrying script -- that executed in "
        "this application's origin as soon as any project member previewed it. This was "
        "reproduced in a real browser BEFORE it was fixed rather than argued from the source: 4 "
        "of 4 attacker payloads reached the boundary at HTTP 200 and executed. The remediation "
        "draws Content-Type from a server-controlled allowlist of formats browsers render "
        "WITHOUT script, serves everything else as application/octet-stream with an attachment "
        "disposition, sends X-Content-Type-Options: nosniff on every response, and sanitises the "
        "Content-Disposition filename so a quote or control character cannot break the "
        "quoted-string or split the response. After the fix 0 of 4 execute, and all 4 STILL "
        "reach the boundary at HTTP 200 -- so the refusal belongs to this boundary and not to an "
        "unrelated authentication or routing gate. Stored bytes, authorization, extraction and "
        "evidence meaning are untouched; a genuine PDF still previews inline. One intended "
        "consequence: image/svg+xml is script-capable and is now downloaded rather than rendered "
        "in place. Retrieval still works; only in-place SVG rendering changes.",
    ),
}
