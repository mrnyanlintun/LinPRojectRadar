# Delete beside Restore in the Archived Projects modal

**Date:** 2026-08-05
**Branch:** `claude/archived-delete-control-s5s90m` (merged to `main`, commit `8048d1f`)
**Model:** Sonnet

**Verification:** server suite **45 suites, 2478/2478** (+7 new checks in `test_workspace_t3t5.py`; fresh SQLite per test file), `tests.html` **51/51**, `tests_render.html` **184/185** (the one red is the pre-existing auth-gated "production read path" check). Two faults injected, each confirmed applied, each detected, each reverted with the baseline re-run green.

---

## LEAD: where the control is now, and where it was

**Delete was built admin-only on the administration surface** (`assets/js/admin-ops.js`, under Project membership), calling `a_admindeleteproject`. **It is still there, unmodified** — verified directly in the merged code (`admindeleteproject` call at `admin-ops.js:294`, with a comment noting the real refusal is server-side regardless of the control's placement).

**It now also appears on every row of the Archived Projects modal** (`assets/js/ingest.js`), reached from the menu bar, which is where the owner actually looked for it. Both controls call the identical, unmodified `a_admindeleteproject` action — nothing about the delete behaviour changed, only where it can be triggered from.

- **Admin** sees Restore and Delete on every archived row.
- **Everyone else** sees Restore only. The client-side conditional rendering is explicitly documented in the code as "a rendering convenience," not the actual security boundary.
- **The refusal is server-side.** `_require_admin` inside `a_admindeleteproject` refuses first, before any table is touched. This was confirmed by reading the existing action rather than rebuilding it, and was independently verified by calling the action directly from a non-admin session: refused with `not authorized: ResearchAdmin role required`.

**Whether the original administration-surface control should stay:** yes, and it does. It was not removed and this report does not treat it as redundant — an admin working from the administration surface for other project-management tasks (the same page as project membership) still has it there, and removing a working control without being asked to was exactly what this task's brief was pushing back on with the *original* placement decision. Both locations reach the same server action, so there is no behavioural inconsistency between them.

---

## Part 2 — surfaces enumerated for the archive-exclusion rule

Every place that lists or offers a project was grepped across `assets/js/*.js` and every list-returning action in `server/app/*.py`.

| Surface | Source | Archived before this task? |
|---|---|---|
| Portfolio list, atlas, globe, project detail selector | `list`/`listslim` → `LIN_PROJECTS` | Already excluded (`archived=False` filter already in `facade.py`) |
| Admin membership picker | `a_adminprojectlist` | Already excluded |
| Upload / extraction pickers | `cachedActive()`-built `projectOptions()` | Already excluded |
| Compute path | Acts on one already-selected project id | Not applicable — not a list |
| **Workspace project list** | `a_workspaceprojects`, which walked `ProjectMember` rows directly, bypassing the filter every other surface already had | **Not excluded — a real, previously unnoticed gap. Fixed.** |
| Archived Projects modal | `a_listarchived` | Correctly **unfiltered** — showing archived projects is the entire purpose of this surface, named explicitly rather than silently left alone |
| `a_researchmyprojects` | Server action exists but has no client caller (confirmed by grep — nothing in `assets/js/*.js` calls it) | Not wired to any UI currently; left as is, noted rather than guessed at |

**The one real gap found:** the Workspace page's own project list walked `ProjectMember` rows directly rather than going through the same `archived=False` filter every other working surface already had. An archived project — East Basin, North Concourse, the ones named in the task — was reachable for work from the Workspace page specifically, even though it had already dropped out of the portfolio list, the admin picker, and the upload pickers. Fixed with a single `continue` guard in `server/app/workspace.py`, leaving the underlying `ProjectMember` row itself untouched.

## The two things that do not change, confirmed rather than assumed

- **Existing membership rows survive archiving.** An existing `ProjectMember` row on an archived project was queried directly against the database and still existed and was still readable throughout the test, confirming archiving withholds a project from *new* work offers without touching the historical record of who was on it — the same behaviour as revocation.
- **Restore returns a project to every surface**, tested per surface rather than assumed symmetric. Because each surface filters independently, this was not inferred from "it's the same flag" — the fixed Workspace list was specifically re-checked after restore and confirmed to offer the project again, alongside the surfaces that were already correctly filtered.

---

## What was built

- `server/app/workspace.py` — `a_workspaceprojects` now skips a project whose `archived` flag is set, with a comment explaining the rule and pointing at restore as the way back.
- `assets/js/ingest.js` — the Archived Projects modal renders a Delete button beside Restore on each row, gated client-side on admin status; wired to the confirmation flow.
- `assets/js/store.js`, `assets/css/radar.css` — supporting wiring and styling for the new control.
- The **typed confirmation** the existing delete control already used is preserved on the modal's control: the button stays disabled until the project's identifier is typed exactly, and it is **not gated on `window.confirm`**.

---

## Verification

Real headless Chromium drove the Archived Projects modal as both an admin and a non-admin session against a local throwaway SQLite instance (never production):

- **Admin** sees both controls, with the Delete button correctly disabled until the exact project identifier is typed, then enabled.
- **Non-admin** sees Restore only, and a **direct call to the delete action** (not merely the absent button) is refused server-side.
- **Delete from the modal removes the project for every user**, not only the admin who triggered it.
- **Restore works for the non-admin** and was confirmed against the database afterward, not just the UI response.
- An existing `ProjectMember` row on an archived project was queried directly and still existed at every point in the sequence.

**Faults proven:**

| Fault | Result |
|---|---|
| the workspace `archived` guard removed | red, 76/77 in the new suite |
| `isAdmin()` hardcoded to `true` in `ingest.js`, so a non-admin's browser rendered the Delete button | The button appeared in the real browser, **but the direct server call was still refused** — proving the server-side gate does not depend on client rendering, which is the property that matters. Reverted, diff confirmed byte-identical. |

The second fault is the more important one: it demonstrates that even a compromised or bugged client cannot delete a project without admin authorization, because the enforcement never lived in the button.

---

## Files changed

`assets/js/ingest.js`, `assets/js/store.js`, `assets/css/radar.css`, `server/app/workspace.py`, `server/tools/test_workspace_t3t5.py`, `T6_HANDOFF.md`, this report. `admin-ops.js` and `index.html` (the original control) were read and confirmed but not modified. No file under `server/app/simulation/` was touched. No migration.
