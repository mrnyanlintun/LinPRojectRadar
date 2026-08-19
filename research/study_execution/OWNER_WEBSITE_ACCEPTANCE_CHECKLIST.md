# Owner website acceptance checklist (Run 40, Fable)

Practical manual test for the owner before any real participant. Everything below uses
NON-CONFIDENTIAL synthetic documents only. Do not use real project documents.

## Test environment
- Deploy the `server/` FastAPI service (Render blueprint `render.yaml`) against a THROWAWAY
  Postgres, or run locally: `cd server && DATABASE_URL=sqlite:///dev.db alembic upgrade head &&
  uvicorn app.main:app`. Never point acceptance at production Postgres.
- Set `ANTHROPIC_API_KEY` only if you want to exercise the REAL extractor; otherwise the stub
  serves recorded extractions and refuses unknown documents.

## Test credentials procedure
1. Create a ResearchAdmin participant (seed row) and log in via `researchlogin`.
2. `adminparticipantcreate` a Participant; copy its access token; `researchlogin` as that PM.
3. `adminmemberadd` the PM to a test project with role PM.

## Safe upload fixtures
- A small genuine `.pdf` (any non-confidential PDF).
- A `.txt` cost/schedule note.
- An `evil.pdf` whose BYTES are `<html><script>...</script></html>` (to test the XSS fix).

## Expected upload behavior
- PM uploads accepted; non-PM / non-member / unauthenticated refused with a JSON error.
- Empty, invalid-base64, or >20MB uploads refused with a controlled message (no crash).
- Period is server-derived for a research assignment; a client-supplied period is ignored there.

## Expected parsed facts / module / result
- Known-answer fixtures extract only the declared per-type fields; absent facts stay ABSENT
  (never 0). UNMAPPED documents contribute nothing to analysis.
- Results compute from extracted evidence; insufficient evidence yields ABSTENTION, not a number.

## Expected abstentions
- Any module lacking its canonical inputs abstains rather than emitting a fabricated value.

## Invalid upload tests (must be controlled rejection, never a crash/traceback)
- zero-byte, invalid base64, oversize, unsupported extension, duplicate content, Unicode/long
  filename. Path-traversal filenames are harmless: storage is content-addressed in the DB and the
  filename is a display label only.

## XSS fix verification (finding S1)
- Open the `evil.pdf` (HTML bytes) preview. It MUST download as an opaque file, NOT render, and
  the response MUST carry `X-Content-Type-Options: nosniff`. A genuine PDF still previews inline.

## Login / logout
- Log in, act, log out; a replayed request after logout is refused.

## Preliminary lock
- Submit a preliminary judgment; confirm it cannot be resubmitted or edited by any route
  (application refuses; DB trigger `trg_decisions_pre_lock_guard` blocks raw edits).

## AI reveal
- Reveal only unlocks after the preliminary judgment is locked. The SAME recommendation appears
  for every period of a given project (this is the governed per-project treatment; see below).

## Final lock
- Submit a final decision; confirm no application route can alter it afterward
  (`final_submitted_at` guard; only one writer).
- KNOWN GAP (S2, owner decision): a direct raw-SQL edit of `final_action`/`final_confidence`/
  `rationale` on a final-locked row currently succeeds and is undetectable (no trigger, no
  updated_at, no audit row). The preliminary judgment IS storage-protected; the final judgment is
  NOT. See the manifest for the recommended symmetric-trigger remedy and its version consequence.

## Reload / resume
- Reload mid-sequence: state resumes at the correct stage. (In-place browser render was NOT
  verified this run under software rendering.)

## What to inspect visually
- No console errors; no failed network requests; no stack traces or internal paths in any error.

## STOP conditions
- STOP if any final-locked decision can be altered through an HTTP/application route.
- STOP if any uploaded document renders active script in the app origin.
- STOP if any participant can read/write another participant's project or document.
- STOP if extraction emits a value for a fact absent from the source document.
- STOP before launch until the S2 final-lock owner decision is made and (if remediated) the
  simulation successor + refreeze/readiness requalification is complete.
