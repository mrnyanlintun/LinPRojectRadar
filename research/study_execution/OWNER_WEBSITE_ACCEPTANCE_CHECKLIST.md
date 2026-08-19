# Owner website acceptance checklist (Run 41 successor, sim-2026.08-v26)

> **What changed since the Run-40 checklist.** Run 40 confirmed two HIGH defects and left them
> open for your decision. You ruled that both be fixed before participant use. They are now
> fixed, and this checklist is the manual confirmation of that:
>
> 1. **S1 - stored XSS / content-type spoofing.** An uploaded document could execute script in
>    the application's own origin when previewed. Now closed. **CONFIRMED_FIXED.**
> 2. **S2 - final-lock database integrity.** A direct database edit could silently rewrite a
>    participant's final answer after it was locked. Now closed. **CONFIRMED_FIXED.**
>
> **You do not need database access for any test below.** Everything is verifiable through the
> website. The S2 test is written as something you can see rather than something you must query.

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

## Documents - what to test by hand (finding S1, now CONFIRMED_FIXED)

**1. Ordinary document preview - must still work.**
- Upload the small genuine `.pdf`. Open its preview.
- EXPECTED: it renders inline, in place, exactly as before. The fix must not have cost you
  ordinary document viewing.
- Upload the `.txt` note and open it. EXPECTED: it displays as text.

**2. Spoofed content - must NOT render.**
- Upload `evil.pdf`, the file whose NAME ends in `.pdf` but whose BYTES are
  `<html><script>...</script></html>`. Open its preview.
- EXPECTED: the browser offers it as a DOWNLOAD, or shows nothing. It must NOT render as a web
  page, and no script in it may run. If you see the page render, or see any pop-up or alert from
  the file, STOP.
- The same applies to a `.svg` containing a `<script>` tag: SVG can carry script, so it now
  downloads instead of displaying. That is intended, not a fault.

**3. Malformed upload - must be refused or handled cleanly, never crash.**
- Upload a truncated/corrupt PDF, a zero-byte file, and a file over 20 MB.
- EXPECTED: a plain readable message each time. No stack trace, no internal file path, no blank
  error page.

**4. Download still works.**
- Use the download control on each uploaded document.
- EXPECTED: the file downloads and opens correctly in its normal application. The bytes are
  unchanged by the fix - only how the browser is told to treat them changed.

## Login / logout
- Log in, act, log out; a replayed request after logout is refused.

## Preliminary lock
- Submit a preliminary judgment; confirm it cannot be resubmitted or edited by any route
  (application refuses; DB trigger `trg_decisions_pre_lock_guard` blocks raw edits).

## AI reveal
- Reveal only unlocks after the preliminary judgment is locked. The SAME recommendation appears
  for every period of a given project (this is the governed per-project treatment; see below).

## Final lock - what to test by hand (finding S2, now CONFIRMED_FIXED)

**1. Complete a decision.**
- Work one project-period through: evidence, preliminary response, preliminary lock, AI reveal,
  final response.
- EXPECTED: each step is offered in that order, and the AI recommendation appears only AFTER the
  preliminary judgment is locked - never before.

**2. Final lock.**
- Submit the final decision.
- EXPECTED: it is accepted, and the screen moves to the completed state.

**3. Try to change it.**
- Attempt to submit a final decision again for the same period, by any route the site offers.
- EXPECTED: refused, with a message saying a final decision has already been recorded. Your
  original answer must still be the one shown.

**4. Reload.**
- Reload the page. Then log out, log back in, and return to the same project-period.
- EXPECTED: the final response is still there, word for word, with the same action, the same
  confidence and the same rationale you entered. Nothing is blank, nothing has reverted, and
  nothing has silently changed.

**5. Come back later.**
- Return the next day and look at the same completed decision.
- EXPECTED: identical again.

> **What changed underneath, in one sentence:** the database itself now refuses to alter a
> final-locked response, so a mistaken or malicious edit made outside the website cannot rewrite
> what a participant decided. The preliminary judgment already had this protection; the final
> judgment now has the same protection, covering every substantive part of the final answer -
> the action, the confidence, the rationale, the disposition toward the recommendation, the
> evidence cited, the reason code, the roles, the deadline and the residual risk.

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
- STOP if a final-locked decision reads differently after a reload, a re-login, or a day later.
- STOP if a spoofed-content upload renders as a page instead of downloading.

## Closed since Run 40
- S1 stored XSS / content-type spoofing: **CONFIRMED_FIXED** (sim-2026.08-v26).
- S2 final-lock database integrity: **CONFIRMED_FIXED** (migration 0026, sim-2026.08-v26).
- Unresolved HIGH security blockers: **0**. The Run-40 condition that held launch - the S2 owner
  decision, and the successor/refreeze requalification it implied - is discharged.
