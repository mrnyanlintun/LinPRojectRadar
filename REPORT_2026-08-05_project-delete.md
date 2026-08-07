# Permanent project deletion, admin only

**Date:** 2026-08-05
**Branch:** `claude/project-delete-s5s90m` (merged to `main`, PR #223, commit `2db65bd`)
**Model:** Sonnet

**Verification:** new suite `server/tools/test_project_delete.py` (19/19); full server suite **44 files, 2384 checks**; `tests.html` **51/51**; `tests_render.html` **169/170** (the one red is the pre-existing auth-gated "production read path" check, red on `main` too). Three faults injected, each confirmed applied, each detected, each reverted with the baseline re-run green.

**No migration was added by this task.** Production still has **0020 (`abstained_modules`)** and **0021 (`schedule_activities`)** unapplied, from the two preceding sessions.

---

## LEAD: what delete reaches, table by table

Built by reading `server/app/models.py` and `server/app/research_models.py` for every foreign key and text reference pointing at `projects`, rather than assuming the list.

### Cleared explicitly in code (eight tables)

| Table | Holds | On delete |
|---|---|---|
| `project_snapshots` | per-period project state | rows removed |
| `files` | uploaded file records | rows removed |
| `document_uploads` | the upload attempt log | rows removed |
| `computed_results` | every stored computation, all periods | rows removed |
| `observations` | the extracted-value store | rows removed |
| `schedule_activities` | the per-period schedule store added last session | rows removed |
| `project_members` | membership mapping | rows removed |
| `training_runs` | training runs bound to the project | rows removed |

All eight declare `ON DELETE CASCADE` toward `projects`. **The cascade is not trusted.** The finding from the user-account work was re-verified against this codebase and holds: SQLite does not enforce a declared cascade without a PRAGMA this application never sets, so relying on the declaration passes every local check while orphaning rows in Postgres. Every one of the eight is cleared by an explicit statement in the handler, and the response reports the per-table counts removed.

### Deliberately untouched

**`documents`** is content-addressed and shared across projects. Deleting a project removes its *filing* of a document, never the document itself. A second project that filed the same content is unaffected.

### Deliberately left to dangle (the research-record consequence)

Two references are not foreign keys, by design, so a historical record survives its subject:

- **`scenarios.evidence_package_id`** — a research scenario's pointer to the evidence package it was built on.
- **`decisions.result_id`** — the computed result a participant actually saw when they recorded a decision.

**After a deletion these point at nothing.** A decision recorded against that project's evidence still exists, still records what the participant judged and when, but the evidence it was judged against is gone and cannot be re-read. An export row referring to that result resolves to nothing.

**This is not prevented, because the owner decided it explicitly.** It is reported here so the consequence is a known choice rather than a discovery: deleting a project that a research scenario used destroys the ability to reconstruct what a participant was shown, while leaving the record that they decided.

**`audit_events` carries no `project_id` column at all** — a project is always referenced inside `event_metadata`. So nothing there can dangle, and the audit trail keeps its record that the project existed and was deleted.

---

## A mismatch found in archive and restore, and fixed

The rule states PM and observer can both archive and restore. Reading `guard_project_write` against that rule showed **observer was refused archive and restore server-side**: the guard was PM-only for every project write.

Fixed narrowly: `ARCHIVE_RESTORE_ACTIONS` in `server/app/research_membership.py` carves out exactly those two actions, requiring membership rather than the PM role. **Every other project write stays PM-only.** This was a real divergence from the stated rule, not a cosmetic change.

---

## The control

`a_admindeleteproject` in `server/app/research_identity.py`. Admin only, refused server-side for anyone else. **No further condition** — a project attached to a research scenario deletes exactly like any other, which the handler's own docstring records as an explicit product decision rather than something it enforces or questions.

The response reports what was removed, per table. An audited `project_deleted` event is written and survives the deletion.

**The user interface** is a typed-confirmation control under Project membership on the administration surface (`assets/js/admin-ops.js`, `index.html`), following the pattern the user-delete control already established: the operator types the project name and the control stays disabled until it matches. The confirmation text states that deletion removes the project for everyone, since membership is a mapping onto one project and a deletion is not the removal of one person's access.

**It is not gated on `window.confirm`** — verified: zero `confirm(` calls in `admin-ops.js`. That function returns false in this container and in any browser suppressing dialogs, and the platform has already lost an action to it once.

---

## Verification

- **An admin can delete, and the project is gone for every user** — checked from a second user's perspective, not merely that the row vanished.
- **A PM is refused server-side**, by calling the action directly rather than observing an absent button. Same for an **observer**.
- **Archive and restore still work for PM and observer** after the guard change.
- **No orphaned row in any enumerated table** — each of the eight queried directly after deletion.
- **The audit event survives.**
- Real headless-Chromium drive of the administration surface: login, create, the delete modal's disabled and enabled states, and DOM confirmation of removal.

**Faults proven** (each confirmed applied before the run, each reverted after):

| Fault | Result |
|---|---|
| a per-table clear removed | red |
| the admin check bypassed | red |
| the archive/restore role set emptied | red |

---

## Files changed

`server/app/research_identity.py`, `server/app/research_membership.py`, `assets/js/admin-ops.js`, `index.html`, `server/tools/test_project_delete.py` (new), `T6_HANDOFF.md`, this report. Nothing under `server/app/simulation/` was modified. No migration.
