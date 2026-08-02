# Run 2: legacy facade fixes, and user archive and delete

**Server 1469/1469 across 27 suites, `tests_render.html` 49/49, `tests.html` 51/51, green on
merged `main`.** Sixteen faults injected across two campaigns, every one detected with a
distinct signature, every one reverted byte-identical, baseline re-run after every single
fault. Archive and delete were also driven end to end in a real browser and confirmed by DOM
read, not only in a test.

---

# Part 3 leads: what delete reaches

Enumerated from the schema, not assumed, by reading every foreign key into `participants` and
every plain-text column that names one:

| Table | Column | Kind | What happens on delete |
|---|---|---|---|
| `participant_profiles` | `participant_id` | FK, `ON DELETE CASCADE` | **Removed explicitly.** Questionnaire responses. |
| `consents` | `participant_id` | FK, `ON DELETE CASCADE` | **Removed explicitly.** Consent grant/withdrawal history. |
| `assignments` | `participant_id` | FK, `ON DELETE CASCADE` | **Removed explicitly.** |
| `decisions` | `assignment_id` → assignments | FK, `ON DELETE CASCADE` (transitive) | **Removed explicitly.** The measurement record — see below. |
| `transitions` | `decision_id` → decisions | FK, `ON DELETE CASCADE` (transitive) | **Removed explicitly.** |
| `project_members` | `user_key` | FK, `ON DELETE CASCADE` | **Removed explicitly.** Every project this person was PM or Observer on. |
| `participants` | (itself) | — | **Removed.** |
| `audit_events` | `participant_id` | **not a FK, by design** | **Retained.** The docstring states it must survive the deletion of whatever it describes; this is what makes "the audit trail records the action even when the subject is gone" true. |
| `project_members` | `added_by` / `revoked_by` on OTHER people's rows | text, not a FK | **Retained**, as an unresolvable id. A membership row this person added or revoked for someone else is untouched; only the acting id stops resolving. |
| `documents` | `first_uploaded_by` | text, not a FK | **Retained.** Content-addressed, shared across projects; not this person's record to remove. |
| `document_uploads` | `uploaded_by` | text, NOT NULL, not a FK | **Retained.** |
| `research_exports` | `initiated_by` | text, not a FK | **Retained.** |

**Explicit deletion, not left to the database.** Postgres enforces `ON DELETE CASCADE`
regardless of how the `DELETE` is issued. SQLite — used for every local verification in this
run — does not enforce foreign keys or their cascade actions unless `PRAGMA foreign_keys=ON`
is set on the connection, which this application does not do. Relying on the declared cascade
alone would have made the fix appear correct in Postgres while silently leaving orphaned rows
in every SQLite-backed check. `a_admindeleteparticipant` clears each table itself, leaves
before roots, and reports exactly what it removed, so the response and every check are
verifying real deletions rather than trusting a database setting.

**This includes the participant's decision records, and that is not an oversight.** A research
participant's `assignments` row cascades to `decisions` and `transitions` — the measurement
record itself. Delete removes it, per instruction, with no condition attached. That
consequence is exactly why archive exists as a separate, independent control: archiving a
participant whose trial data must not be destroyed leaves it fully intact; deleting one does
not, and the choice between the two is the operator's, made at the point of clicking either
button, not something this task decided for them.

**No orphaned rows survive the six current-relational-state tables**, verified directly against
the database before and after a real delete, with every row present beforehand and every table
clear afterward. The five text-column references that remain are historical facts, not live
relationships — the same append-only-history posture the storage redesign and D2 work already
established for observations and documents, applied here to identity.

---

# Part 1. `w_saveportfoliohealth` appends

**What it is for, established before changing anything.** It stores the deployment-wide
portfolio-health snapshot the Health dialog reads (`getportfoliohealth`), one row per save. The
comment removed by this change said replacing "matches the live model, which keeps a single
`portfolio_health.json` file at the Drive root" — a reproduction of the legacy's storage
mechanism, not a requirement of anything that reads it.

**Nothing depends on there being exactly one row.** `a_getportfoliohealth` already selects the
latest by timestamp rather than reading the table's only row — that is a SELECTION, not a
consequence of singularity. Confirmed by reading the handler before touching it: it takes
`.order_by(...).first()` (now `max()` over the snapshot's own `savedAt`, see below), which
behaves identically whether the table holds one row or a hundred.

**The fix**: the `session.delete` loop — the only one in the application — is gone. Every save
inserts; nothing is removed. The read side is unchanged in behaviour: a caller who wants the
latest still gets exactly the latest, and only the latest.

**A real bug surfaced fixing this, not introduced by it.** The original verification and the
read path both ordered by the `saved_at` DB column. SQLite's `func.now()` default is
second-resolution; two saves in the same second — which the existing test suite's own two
calls sometimes are — tied, and `ORDER BY ... DESC` over a tie is not guaranteed to return the
newer row. With deletion removing the old row first, the tie never mattered before; appending
made it visible immediately (`test_writes_a1b.py`'s existing "replaced singleton" check went
red on the first run after the fix). Both the write-side verification and the read-side
selection now order by the snapshot's own `savedAt` string — stamped by `_server_now()` at
millisecond resolution — instead of the column, which is the ordering a timestamp comparison
was always meant to express.

---

# Part 2. `w_overwritesignal` validates the field name

**Restricted to `field_registry.ALL_SI_FIELDS`** — every field the merge can emit, the three
keys nothing emits any more but the computation layer still reads (`rfiNumber`,
`rfiResponseTimeDays`, `docDate`), and the two derived indices (`cpi`, `spi`) reachable through
this action. Verified to match `extraction_merge.SIGNAL_INPUT_KEYS` plus `cpi`/`spi` exactly,
by set equality, so the two vocabularies cannot drift: `field_registry.py` — named in the task
as the likely home — was already the source of truth for every other per-field declaration
this run's earlier work introduced, and this reuses it rather than adding a second list.

A name outside the set is refused before the project is even looked up, naming the field:

> Unknown signal field: 'totallyMadeUpField'. This platform has no field by that name; nothing
> was changed.

The numeric and range contract D2 added stays exactly where it was — this is a second,
independent gate (the field's NAME) ahead of the value contract already in place.

---

# Part 3. User archive and delete

**Archive was already built, and is used as-is: `setactive(is_active=false)`.** Re-read against
the definition given — "retention before permanent deletion, the account cannot sign in,
everything is retained" — and it matches exactly. `resolve_caller` is the single choke point
nearly every authenticated action passes through, and it refuses an inactive account outright;
`a_researchlogin` and `a_researchssologin` both check `is_active` before minting a session, so
sign-in itself is refused with a clear message. Nothing about the participant row, their
project membership, their consent records, or anything else is touched — archiving is a single
boolean flip, audited (`account_deactivated`/`account_activated`).

**No backend change was needed for Archive.** What changed is presentation: the toggle is
labelled "Archive"/"Restore" (was "Deactivate"/"Activate") and the pill reads "Active"/"Archived"
(was "Active"/"Inactive"), matching the vocabulary the platform already uses for the same
concept on projects. New strings, flagged as operational wording per the standing rule: the
button labels themselves, and the delete-confirmation copy below.

**Whether an archived account still appears where it should: confirmed, not assumed.**
`a_adminmemberlist` returns every membership row for a project unconditionally — it does not
filter on the member's `is_active`, and it never revokes membership on archive (archive and
revocation are different actions; only `adminmemberrevoke` sets `revoked_at`, and it is never
called by `setactive`). Verified directly: a participant archived mid-session still shows in
the project's member list with their role intact, exactly as their membership history should
read.

**Delete is new: `admindeleteparticipant`.** Admin-only, and — per instruction — carries no
other condition. `a_setactive` refuses to deactivate the last active ResearchAdmin because
deactivation is meant to be safely reversible into a working system; delete has no equivalent
guard, deliberately, because gatekeeping what the operator asked to remove is not this action's
place. The response reports exactly what was removed (`{"transitions": N, "decisions": N,
"assignments": N, "consents": N, "participant_profiles": N, "project_memberships": N}`), and an
audit row (`participant_deleted`) is written for the target's id, which by the next statement
no longer resolves to a row — the same non-FK design that lets `audit_events` survive the
deletion of whatever it describes.

**UI**: a "Delete…" button per row opens a confirmation requiring the admin to type the
account's exact username before the button enables, with explicit warning copy naming the
consequence (membership, and for a research participant, decision records) and pointing at
Archive as the reversible alternative. Flagged, new operational wording:

> This removes the account, its project membership, and, for a research participant, its
> decision records. It cannot be undone. If the account should be kept but locked out, use
> Archive instead.

---

# Verification

- **Server suites**: 1361 baseline → **1469/1469 across 27 suites**, fresh migrated sqlite per
  suite, `PYTHONIOENCODING=utf-8`. New suite `test_facade_and_user_lifecycle.py`, 26 checks.
  `test_writes_a1b.py` strengthened from 100 to 103 (asserts the prior portfolio-health
  snapshot is genuinely still in the store, not merely that the read side still answers
  correctly).
- **`tests_render.html` 49/49, `tests.html` 51/51**, real Chromium, DOM reads.
- **Both admin controls driven end to end in a real browser**, signed in through the actual
  login form, navigated via the real Admin nav button, clicked through the real DOM: Archive
  flips the pill and button live and the archived account's login attempt is refused; Delete's
  confirmation button stays disabled until the exact username is typed, and the row disappears
  from the DOM after submission. Compositing checked (`visibilityState: "visible"`) before any
  DOM read was trusted.
- **Sixteen faults, two campaigns, all confirmed applied, all detected, all reverted
  byte-identical, baseline re-run green after every single fault:**

| Fault (Part 1/2/3 suite, 26 checks) | Result |
|---|---|
| Portfolio health deletes prior snapshots again | 24/26 |
| overwritesignal field-name validation removed | 24/26 |
| Archive stops checking `is_active` at login | 25/26 |
| Delete stops removing decisions/transitions | 24/26 |
| Delete stops removing project memberships | 24/26 |
| Delete stops writing an audit event | 24/26 |
| Delete no longer restricted to admins | 25/26 |

- The suite is wrapped so a crash prints a failing RESULT line rather than silence, and every
  fault above was confirmed to have actually applied (anchor matched exactly once) before its
  result was read.

# Files changed

- `server/app/writes.py` — `w_saveportfoliohealth` appends; `w_overwritesignal` validates the
  field name against `field_registry.ALL_SI_FIELDS`.
- `server/app/facade.py` — `a_getportfoliohealth` selects the latest by the snapshot's own
  `savedAt`, not the DB column (the tie-resolution fix above).
- `server/app/field_registry.py` — `ALL_SI_FIELDS`, the declared vocabulary.
- `server/app/research_identity.py` — `a_admindeleteparticipant`.
- `assets/js/admin.js` — Archive/Restore labelling; the Delete button and its confirmation
  modal.
- `server/tools/test_facade_and_user_lifecycle.py` — new, 26 checks.
- `server/tools/test_writes_a1b.py` — strengthened portfolio-health retention checks.
- No migration: nothing here changed the schema. `server/app/simulation/` untouched; no stored
  data altered; production not inspected.

# Still open

- Whether `getportfoliohealth` should be membership-scoped remains the open item an earlier
  report raised; unrelated to this run's changes and not revisited.
- `document_uploads.uploaded_by`, `documents.first_uploaded_by`, `research_exports.initiated_by`
  and the `added_by`/`revoked_by` text columns on other people's membership rows are left as
  unresolvable historical references after a delete, by design; nothing further was done to
  them, consistent with how the rest of the platform treats history.
