# Administration consolidated, a PM assigned at creation, and the unmembered gap closed

2026-08-02. Local only. Production was not inspected, queried, or migrated, and nothing was
deleted anywhere.

---

## Lead: which projects become inaccessible

**Eight, all of them in the local development database, and all of them fixture debris.**
Production has no projects at all, so nothing there is affected.

| Project id | What it is | Membership rows | Should it get membership, or be deleted? |
|---|---|---|---|
| `PRJ-LEGACY-NOMEM` | Named "Imported, no members". Created by a membership suite specifically to be the unmembered case. Archived. | none | **Delete.** It exists only to represent the state this change removes. |
| `ST-OPEN` | Transition target state stub, seeded directly into the projects table by the export suite. | none | **Delete.** |
| `ST-RECOVERY` | Same, the recovery branch target. | none | **Delete.** |
| `ST-DRIFT` | Same, the drift branch target. | none | **Delete.** |
| `ST-B8-NEXT` | Same, seeded by the membership suite. | none | **Delete.** |
| `STATE-P1` | Same, seeded by the transitions suite. | none | **Delete.** |
| `STATE-RECOVERY` | Same. | none | **Delete.** |
| `STATE-DRIFT` | Same. | none | **Delete.** |

None of them is a real project and none holds any work. Seven of the eight are not projects in
any meaningful sense at all: they are next-state identifiers that transition rules point at, and
a row was inserted into `projects` so the foreign reference would resolve. They were never
created through the interface, have never had a document uploaded to them, and no account has
ever opened one.

**Nothing was deleted.** The recommendation above is a recommendation.

The other thirteen projects in the local database each already carry an active PM and are
unaffected. Every one of them was created by a suite through a real creation path, which is why
they have one.

**There is no project anywhere that a real person would lose access to.** That is the whole
reason this was safe to do now and would not have been before.

---

## Part 1. The PM is assigned when the project is created

### What was broken, established before anything was changed

The administration screen offered "Assign as PM (optional)" on project creation. It did not
work, and the way it failed was silent.

`createProject` in `assets/js/admin-ops.js` made **two** calls. First `projectcreate`, which
created the project. Then, if a PM had been chosen, `adminmemberadd` to install them. The second
call was refused every time, with:

> this project already has an active PM; revoke them first

because `projectcreate` had already made **the caller** the PM, and migration 0006 permits
exactly one active PM per project. So the project was created, the intended owner never got it,
and the admin was left holding a project they had meant to hand to someone else. The interface
did report the failure in its confirmation line, but by then the project existed.

### What it does now

`a_projectcreate` takes `pm_participant_id`. One call, one transaction.

- **The PM is resolved before anything is written.** A participant id that does not exist, or a
  non-admin trying to name somebody other than themselves, refuses the whole call. No project is
  created. That was the specific requirement and it is met literally: a refusal leaves neither
  row, because the refusal happens before either row is added.
- **The membership row is added to the same session as the project row and committed once.** A
  failure at the commit leaves neither. There was no obstacle in the current structure to doing
  this, so there is nothing to describe in place of it.
- **Naming another person as PM is admin-only**, and a non-admin attempting it is refused and
  audited as `admin_action_denied`. A participant creating their own project is unchanged.

The legacy `create` action on the compatibility facade had the same hole from the other side: it
produced projects with no membership at all. Since Part 3 makes such a project reachable by
nobody, including the person who just made it, `guard_project_write` now hands the resolved
caller down to the handler and `w_create` writes the creator's PM row in the same transaction as
the project. **Both creation paths now guarantee an owner.**

### In the interface

The picker is now labelled "PM for this project (required)" and opens on a disabled "Choose a
PM" option rather than the old "(nobody yet)", which was an invitation to create exactly the
project this work removes. Creating without a choice is refused in the browser before any
request is sent. The second call is gone.

---

## Part 2. Five tabs became two

| Was | Is |
|---|---|
| Users and access | **People and access** |
| Projects and assignment | " |
| Project membership | " |
| Monitoring | **Monitoring and export** |
| Export | " |

**Nothing was withdrawn.** All twenty-eight controls that stood on the five tabs are still
present and are checked by id in a browser, so a control quietly dropped during the move would
be caught rather than assumed absent.

### Keeping the two relationships apart

The first tab carries two relationships that take the same two nouns, a person and a project,
and mean entirely different things:

- **Who runs and who reads a project.** Operational. It decides who may open a project and act
  on it now.
- **What a participant works through for the study.** Research. It decides which scenario a
  person is taken through. It grants no access to any project.

Merging them onto one surface without separating them would invite an admin to make a study
change they meant as an access change. They sit under their own headings, in that order, each
with a sentence saying which of the two it is and that it is not the other, and with a rule
drawn between them. The browser check does not read the headings for wording; it resolves which
heading each control actually sits under in the document and requires the membership control and
the assignment control to resolve to **different** ones.

### Two defects found while doing this

**The Create export button did nothing at all.** `createExport` writes into `ao-export-error` on
its first line, before it calls anything. That element was never in the markup, so
`getElementById` returned null and the handler threw on the property assignment. No error was
shown, because showing the error was the statement that threw. This is the first recorded failure
mode in its purest form: the code that reports the problem was the code that broke. The element
is now in the markup, alongside every other card's error line.

**The tab switcher carried a hardcoded list of panel names**, `["users", "projects", "members",
"monitoring", "export"]`, in `app.js`, separate from the markup that defines them. Renaming the
tabs would have left it toggling panels that no longer exist while never revealing the one that
does, silently. It now derives the panel list from the tab bar's own buttons, so the markup is
the only place the tabs are named.

### The admin as PM

The instruction was to make the admin the PM "where that is the correct owner". **There is
nowhere that applies.** Every project in the local database that has an owner already has the
one its own fixture chose, and taking it would be wrong. The eight that have none are the
fixture debris listed at the top, which should be deleted rather than adopted. Production is
empty. Going forward the question does not arise: creation assigns a PM, so the admin is PM of
what the admin creates and of nothing else.

The stale sentence on the Administration page, "These were two pages a word apart in name", is
gone. The page now says what the two tabs hold.

---

## Part 3. The unmembered gap

### Closed

Three arms closed, all in `server/app/research_membership.py`. Each used to return "allow" when
the project had no membership rows:

- **`guard_project_write`** — an unmembered project was writable by any authenticated caller.
- **`guard_project_read`** — and readable by any authenticated caller.
- **`readable_project_ids`** — and listed in every authenticated caller's portfolio.

All three now authorise against membership unconditionally. No members means no active
membership, which means refused. **This was the last route from one authenticated user to
another user's project**, and it is gone.

It fails closed at the guard, in the same shape as the read guard's `PUBLIC_GET_ACTIONS`: a new
write action added to `PROJECT_WRITE_ACTIONS` inherits refusal, and permitting it is a visible
edit at its own site rather than something inherited from a guard that waves through what it does
not recognise.

Verified in a browser against a real server: an authenticated caller holding no membership row is
refused on `get`, refused on `archive`, the refused write does not land, and the project is
absent from their portfolio list. The owner reaches and writes their own project. The admin who
created a project **for somebody else** is refused on it, holding no row of their own, which is
the check that shows the refusal is not cosmetic.

### `refuse_unless_pm_for_assignment`: closed differently, and this needs your decision

**I did not close this the way the instruction described, because doing so literally would have
stopped the study from running. Here is exactly what happened and what I did instead.**

Closing the unmembered arm here was tried first, as asked. It made four suites red, all in the
same way: participants were refused on `researchprejudgment`, `researchreveal`,
`researchdecision` and `researchadvance` against their own assignments.

The cause is a collision between this change and Part 1:

1. A scenario names **one** evidence project.
2. Several participants are assigned the **same** scenario. That is what a counterbalanced
   design is.
3. Migration 0006 permits exactly **one active PM per project**, at the database level.
4. So requiring PM here means **one evidence project can serve exactly one participant.**

And this could not be dodged by leaving the arm as it was, because Part 1 removes the very
condition it tested. Both creation paths now write a PM row, so no project is unmembered, so
"does this project have any members" is true for every project from today, and the guard would
demand PM of everyone regardless.

**What the guard checks now is the caller's own membership row rather than whether the project
has any.** If the caller holds a row on the evidence project, it must be an active PM row: an
Observer is refused, exactly as before. If the caller holds no row, the action proceeds.

This is not a weakening, and the reason is that this guard was never what bound the action to a
person. Every caller reaching it has already passed `_resolve_target` or
`_resolve_advance_target`, which resolve **the caller's own current assignment** and refuse any
other `assignment_id` the request body names, with an audit row. There is no lateral route here
to close. The case this guard was written for, an Observer on an operational project attempting
to judge or decide, is precisely the case the caller's own row still catches, and the suite that
covers it is green.

**What is left for you.** If you want participants sharing an evidence project to each be its PM,
that is not possible while one active PM per project holds, and it would need either
per-participant evidence projects or a change to migration 0006's unique index. I have not made
either change: which one is right depends on the study design, not on the code.

---

## Verification

**The server suite: 1268 checks across 23 suites, all green.** Every suite printed a RESULT
line, which is checked rather than assumed, because the first recorded failure mode is a check
that crashes instead of failing and so prints nothing while looking clean.

**Browser: 29 checks, all green**, driven through real Chromium against a real server on a fresh
database, signing in through the actual form so the app's own gate opens rather than being forced
open. Compositing is proved first and before anything is read off the page, by counting distinct
pixel colours in a screenshot: a page that never painted is a uniform rectangle, and the DOM will
happily report element geometry for something that never reached the screen.

`tests.html` 51/51 and `tests_render.html` 43/43, both with no uncaught page error.

### Every check was proved able to fail

Ten faults, each one injected into the real source, each requiring its named check to go from
green to red. **All ten produce the expected red.**

**The harness guards both recorded failure modes explicitly.**

- Every fault asserts its anchor matched **exactly once** before the run, and prints
  `fault applied` only then. An anchor that does not match is reported as `ANCHOR FAILED` and the
  run is not treated as a result at all. This is the second failure mode: an injection that
  silently fails to apply reports a false clean.
- A run that produces **no RESULT line** is reported as `INCONCLUSIVE`, never as a pass and never
  as a red. This is the first failure mode: a check that crashes rather than failing prints
  nothing.

| Fault injected | Check that must go red | Result |
|---|---|---|
| `guard_project_read` waves an unmembered project through again | an authenticated caller is refused a READ of a project with no members | red, and the refusal starts carrying a project payload |
| `guard_project_write` waves an unmembered project through again | and refused a WRITE to it | red, and the write lands |
| the portfolio list stops filtering by membership | and it does not appear in the portfolio list either | red, and membered projects reappear in a non-member's list |
| project creation stops writing the PM row | creation wrote exactly one active PM row | red, and the PM can no longer reach the project |
| the PM becomes the caller again instead of the person chosen | and it is the person chosen in the picker, not the caller | red, and the admin stops being refused on a project it made for somebody else |
| the interface stops requiring a PM at creation | creating with no PM is refused in the interface | red |
| a third tab is added | Administration has two tabs, not five | red |
| study assignment is moved back under the operational heading | operational membership and study assignment sit under DIFFERENT headings | red |
| the export error line goes missing again | no capability lost: all 28 controls still present | red |
| an opaque overlay covers the viewport | compositing: the page painted | red, at 100.0% of the viewport in one flat colour |

**Three of these checks were rewritten because the injection showed they proved nothing.**

- **The two unmembered-arm checks were testing the wrong thing.** Reopening the arm left them
  green, because the project they ran against had members: they were non-member checks against a
  membered project, which is a different guard arm that passed before this change. The arm that
  was actually closed now has its own fixture in the server suite, a project inserted straight
  into the table with no membership rows at all, which is the only way to produce that state now
  that both creation paths write an owner. That is the shape of the eight orphans listed at the
  top of this report.
- **"the PM is the person chosen, not the caller" was vacuous.** The only account in the picker
  was the admin, who was also the caller, so hardcoding the server back to the caller left the
  check green. The browser suite now creates a second account before the picker is populated and
  names that one.
- **The compositing check counted distinct colours, which is too weak.** Flattening every element
  to black left thousands of shades from antialiasing and gradients, and the check passed. It now
  measures the share of the viewport held by the single most common colour: 62.6% normally,
  100.0% under the fault.

### A verification defect found and fixed in the checks themselves

Two of the browser checks first drove the refused write with `setprojectnumber` and the wrong
parameter name. The guard refused before the handler ever validated parameters, so the checks
went green while the write they were supposedly testing was malformed. The positive control is
what exposed it: the same call with the owner's session **also** failed, with
`id and newId are required`. Both now use `archive`, with valid parameters, and the owner
succeeding on the identical call is what makes the non-member's refusal mean something.

An earlier run of the browser suite was also invalid and was caught the same way. The reset
script removed the database file while the previous server still held an open handle on the
deleted inode; the new server could not bind the port and died, so the browser talked to the old
server with the old data and every check ran against stale state. The script now waits for the
port to actually free and waits for the new server to answer before the browser starts.

---

## What was not touched

`geocode.py` and `documents.py` are unmodified, for the parallel geocoding session.
`w_overwritesignal` and `w_saveportfoliohealth` are unchanged and remain as previously reported.
No stored data was altered or deleted anywhere, local or production.
