# Run 40 — Fable adversarial functional acceptance, upload qualification, and security review

Date: 2026-08-19. Model: Fable. Reviewer and remediator: this run.

Final disposition: **FABLE_ACCEPTANCE_BLOCKED** (two owner decisions required; both are
integrity/version-boundary items, not participant-reachable holes left open).

## 1. Starting frozen identity (verified mechanically)
- HEAD == main == origin/main == `089b16eeb68093d197578bc6794e559488c38118`.
- Tree clean at start.
- `SIMULATION_VERSION = "sim-2026.08-v25"` (server/app/simulation/models.py:423).
- Participant `og-participant-2026.08-v13`, synthetic `OG-SYNTH-0.6`, analysis `og-analysis-2026.08-v1` (per brief).
- Freeze candidate `6142d877856ea651ef8d7e905f6d27604b3244f1`; freeze surfaces: `server/app`,
  `assets`, `index.html`, `research_fixtures/synthetic`, two methodology files.
- Main-study observations = 0; voting = 2.
Work on branch `run40-fable-wip`, merged to main at end.

## 2. Actual upload architecture
Not multipart. JSON facade: browser -> `POST /exec` (text/plain JSON, main.py:280) ->
`a_projectupload` (documents.py:1759, PM-only + membership) -> base64 decode, 20 MB bound
(`_decode`) -> **content-addressed raw bytes in DB keyed by sha256** (no filesystem write) ->
extraction (LLM prod / stub local) confined to per-type field allowlist -> `is_mapped` gating ->
compute -> ABSTAIN/`ComputedResult` -> `GET /documents/{id}/content` (main.py:411) with membership+
linkage recheck. Table: `code_audit/run40_upload_architecture.csv`.
Dominant facts: no uploaded byte hits the filesystem (path traversal NOT_REACHABLE for storage);
an LLM is genuinely in the evidence path, output filtered to declared fields (extraction_client.py:497).

## 3. Supported types
`code_audit/run40_supported_types.csv`: `.pdf` (primary), `.docx`, `.txt`; unknown -> UNMAPPED
stored WITHOUT extraction. **MIME not validated at upload** (client mimeType stored verbatim) = S1 root cause.

## 4-5. Extraction fidelity
Exercised through real `/exec` against the deterministic StubExtractor (no local API key; refuses
unknown hashes). Output confined to field allowlist -> volunteered keys cannot widen the stored
extraction. **Fabricated facts (stub path) = 0.** Real-model numeric-fabrication-under-injection =
NOT_VERIFIED_ENVIRONMENT_LIMITATION (no key); containment verified.

## 6. Lineage
`code_audit/run40_upload_lineage.csv`. checksum->fact->structure->module->category->qualification->
result all traceable; unknown stays unknown.

## 7-10,13-19. Adversarial / auth / malformed (real HTTP surface)
Cross-project upload refused; cross-user read 403; cross-project read 404; **cross-user r/w = 0**.
Unauthenticated upload refused. Zero-byte/empty/invalid base64/oversize refused with controlled
JSON errors (no crash, no traceback, no path disclosure — errors return `type(exc).__name__`).
Secrets: none tracked; `render.yaml` uses `sync:false`; the single DATABASE_URL role is unrestricted
(privilege behind S2).

## 8/11. Finding S1 — stored XSS / content-type spoofing (CONFIRMED, reproduced)
`/documents/{id}/content` echoed the unvalidated client `mime_type` as `Content-Type`,
`Content-Disposition: inline`, no `X-Content-Type-Options`. Reproduced end-to-end: PM uploads
`<html><script>…</script>` with `mimeType: text/html` -> serve returns `Content-Type: text/html`.
`assets/js/files.js:199` loads this in a **same-origin `<iframe>`** and `preview_kind` enables that
iframe on a `.pdf` filename regardless of bytes, so `evil.pdf`+`text/html` executes attacker script
in the app origin (token theft / act-as-victim). Reachable cross-member.
**Fix prepared & proven (11/11 green) in commit `a3fd8b6`**: serve-boundary inline-safe allowlist
(else octet-stream+attachment), `nosniff`, sanitized filename. **`server/app` is a frozen surface**;
the fix moves a frozen byte and reds 8 freeze/baseline gates. Per s.22/note(b) a security fix must
not silently invalidate the freeze, so the commit was **reverted** and S1 delivery held as an
owner-authorized freeze-successor item. Recover with `git show a3fd8b6`.

## 12. Prompt/document injection
LLM present but contained (output filtered to declared fields; no authority wiring). Live-model
numeric behavior NOT_VERIFIED (no key). Not NOT_APPLICABLE.

## 14. Auth/session
Unauth/malformed refused before dispatch (`gate_action`); errors leak only the exception class name.
Bearer token in sessionStorage; same-origin `/exec`; CORS the only middleware.

## 20. Preliminary lock (reconfirmed)
`trg_decisions_pre_lock_guard` reproduced: raw `UPDATE pre_action` on a locked row raises
`IntegrityError: pre-judgment is locked`. Storage-layer lock holds.

## 21. Finding S2 — final lock (CONFIRMED, reproduced)
Application layer intact: sole writer `a_researchdecision` guarded by `final_submitted_at is not
None`; exhaustive grep = no other writer, no raw SQL in server/app. **Application-path bypass = 0.**
Database layer absent: decisions trigger covers only pre-fields; **no final trigger, no updated_at,
no row-version** (verified on live migrated schema). Reproduced: raw `UPDATE decisions SET
final_action…final_confidence…rationale='TAMPERED'` on a final-locked row **succeeds silently, zero
audit delta**. No detection. Operator DATABASE_URL role can do exactly this. Asymmetry: the PRIMARY
outcome (final, RQ2) is less protected than the preliminary (RQ1) — indefensible vs this programme's
own 0003/0012 standard.

## 22. Final-lock remediation decision
Smallest control = symmetric DB trigger mirroring migration 0003 (final fields after
`final_submitted_at`). This is persisted-decision (executable) behavior: per s.22/note(b) it needs
v25 preserved, a simulation successor, and lock/state-machine/freeze/readiness requalification —
owner-authorized, not silent. **NEEDS_OWNER_DECISION.** No frozen byte moved this run.

## 23. AI recommendation binding
`code_audit/run40_ai_recommendation_binding.csv` (36 project-periods). Package binds via
`assignment.package_id`, revealed identically across all periods. Run 39 corroborated: **6 unique
exposures, not 36.**

## 24. Governed-design reconciliation (STOP evaluated, NOT a STOP)
Locked design: recommendation QUALITY rotated across PROJECTS by Latin square = per-project
treatment; decision-log: contrast "rests on one observation per participant [per project]".
Option A (per-project reuse) is the governed level and implementation matches it; per-period
distinct content is NOT explicitly governed (D). **Not a discrepancy** -> no STOP owner-blocker on
stimuli. Recorded (F1): within-project analytic dependence — a project's six periods are repeated
exposures to one recommendation, so period observations within a project are not independent w.r.t.
the recommendation treatment. Behavior preserved, not changed; surfaced for owner awareness.

## 25-26. Real browser
Full in-place click-through render = NOT_VERIFIED_ENVIRONMENT_LIMITATION (software render), as Run
39. All boundary claims proven through the real HTTP surface, not substituted; the in-browser render
itself is not claimed as passed.

## 27-28. Findings
`code_audit/run40_security_findings.csv`, `code_audit/run40_functional_findings.csv`. S1 (HIGH, fix
prepared, needs freeze successor), S2 (HIGH integrity, needs owner decision), S3 MIME-unvalidated
(DEFENSE_IN_DEPTH), S4 traversal (NOT_REACHABLE), S5/S7/S8/S9 (FALSE_POSITIVE), S6 injection
(CONFIRMED_NON_BLOCKING), S10 operator privilege (NEEDS_OWNER_DECISION, feeds S2).

## 29-30. Fixes / versions
No frozen byte moved; no executable behavior changed in the delivered tree. Retained: sim v25,
participant v13, synthetic 0.6, analysis v1, freeze candidate 6142d87. Both remediations cross the
freeze/version boundary and are held for owner authorization.

## 31. 18-case campaign
`code_audit/run40_regression_campaign.csv` — **18/18 accounted for**: 11 pass/refused/blocked, 2
contained (live-model NOT_VERIFIED noted for #17), 1 NOT_REACHABLE (#4), 1 reconciled (#15), 1
fix-prepared-held (#5=S1), 1 NEEDS_OWNER_DECISION (#13=S2). #5 baseline-RED reproduced pre-fix.

## 33. Owner package
`research/study_execution/OWNER_WEBSITE_ACCEPTANCE_CHECKLIST.md`.

## 34. Disposition
**FABLE_ACCEPTANCE_BLOCKED.** Two unresolved integrity/version-boundary owner decisions: S2
(final-lock DB tamper-evidence) and S1 delivery (proven XSS fix touches frozen server/app). Cross-
user access = 0, application-path final-lock bypass = 0, extraction fabrication (stub) = 0,
preliminary lock holds. Blocks are decisions, not open participant-reachable holes, but must be
resolved before real participants and not hidden under PASS.
