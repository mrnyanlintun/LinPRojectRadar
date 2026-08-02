# The event log stops being deleted, and what the upload events would cost

**1190 checks across 22 suites, 0 failures. `tests_render.html` 43/43, `tests.html` 51/51.**
Playwright driving the pre-installed Chromium; compositing proven first (`visibilityState`
"visible", **63 rAF frames per second**). No stored data was altered and production was not
inspected or queried.

---

## Part 3 first, because it is the decision waiting on you

**The docCount answer is: nothing a user can see changes, because no user-facing surface reads
docCount at all.** But **C1.4 does change, and that is user-visible**, so I established it and
stopped rather than shipping, per your instruction.

### docCount

`docCount` is produced by `facade.slim_row` and returned in `listslim`. I grepped every `.js`,
`.html` and `.py` in the repository outside the captured baseline and the Apps Script reference:

```
server/app/facade.py    produces it
server/app/models.py    comment about it
server/app/writes.py    comment about it
assets/js/store.js:367  names it in a comment listing the slim fields
tests_render.html:373   sets it to 0 in a fixture
calibration/verify.html mentions it in a comment
```

**No render path reads it. No test asserts a value for it.** So writing `signals_extracted` on
upload would move `docCount` from `0` to the number of documents uploaded, in an API response
nobody displays. Measured end to end: `0 → 1` after one upload.

### C1.4 Audit Trail Completeness, which is the real cost

C1.4 requires `project_created` **and** `signals_extracted`, and needs `total_events >= 3` for
Green. Measured by running `run_audit_trail` directly against each candidate event set:

| Event log | C1.4 today / after |
|---|---|
| `project_created` only — **every server-created project today** | **Amber, 50%, "1 events recorded"** |
| `+ signals_extracted` | **Yellow, 100%, "2 events recorded"** |
| `+ signals_extracted + an analysis-computed event` | **Green, 100%, "3 events recorded"** |
| two documents, plus a compute event | Green, 100%, "4 events recorded" |

**So writing the upload events moves C1.4 from Amber to Yellow, and adding a compute event moves
it to Green.** Category C1 Data and Evidence Health moves with it. C1 does not vote in project
status (Group C is excluded by `contributes_to_project_status`), so **the project colour does not
move** — but the evidence-health reading a participant sees on the evidence screen does, on every
project.

**That is a change to what a user sees, so I stopped and shipped nothing for Part 3.**

### What should be written, when you decide

For the trail to be complete on C1.4's own terms, an upload needs `signals_extracted` per stored
document, and reaching Green needs a third entry, for which the natural candidate is the compute
itself. Two things you should know before choosing:

1. **`_append_event` stamps the server clock, and `_events_as_of` truncates at the period cutoff.**
   A June report uploaded in August produces an event dated August, which is *after* that period's
   cutoff and therefore excluded from that period's C1.4. Measured: appending `signals_extracted`
   to a project whose cutoff was 2026-06-30 left C1.4 at 50%. **On back-dated documents the events
   are written and still do not count.** Backdating them to the document's date would make them
   count and would be recording an event as having happened when it did not, which I will not do
   on my own judgement. This is the same cutoff judgement call the D1 report flagged for you, now
   with a second consequence attached.
2. **The event name is load-bearing in two directions.** `signals_extracted` is what
   `detail.js`'s Uploaded Documents table renders and what `docCount` counts, so writing one per
   document also populates a table that is currently empty for server-uploaded documents.

---

## Part 1. The reset no longer deletes, and it records what it did

### A correction to the premise, because it changes what the defect is

**`w_resetsignals` does not touch `audit_events`.** There are two event stores and the brief
conflates them:

- **`audit_events`** — the research audit trail, 84 `audit(...)` call sites, 66 event types.
  **Verified genuinely append-only:** there is no `UPDATE` or `DELETE` against it anywhere in
  `server/app/`, and the only `session.delete` in the entire application is
  `w_saveportfoliohealth`'s. Measured across a reset: 0 rows before, 0 rows after, untouched.
- **`doc["events"]`** — the legacy per-project JSON list inside the project document, written by
  `writes._append_event`. **This is what the reset truncated.**

The distinction matters twice over. It narrows the blast radius (the research audit trail was
never at risk), and it widens it in a different direction: **the legacy facade writes nothing to
`audit_events` at all**, so a reset through that surface leaves no research-audit record that it
happened, even now. That is reported below, not fixed.

### What the action is for, and who can call it

`resetsignals` clears `signals`, `signalInputs` and `simulationSignals` so a project reads as
un-analysed. It is in `PROJECT_WRITE_ACTIONS`, so `guard_project_write` restricts it to the
project's PM — **but only when the caller presents a session token and the project has membership
rows**. `guard_project_write` returns `None` (allow) when `not payload.get("session_token")`.

**Measured: a completely unauthenticated POST of `{"action":"resetsignals","id":...}` is
accepted.** That is the documented B8 posture — the facade adds authorisation for authenticated
callers, not authentication — but it means the action that destroyed the log needed no credential.
Reported, not changed: altering the facade's authentication posture is not this task.

### The deletion was not load-bearing

Measured before deciding. The old code kept only `signals_extracted` and dropped everything else:

```
before reset : ['project_created', 'signal_overwritten', 'project_archived', 'project_restored']
after  reset : ['signals_reset']
```

Nothing needs the others gone:

- **`detail.js`'s Uploaded Documents table** filters for `signals_extracted` itself.
- **`signals.js`'s audit panel** filters for `signals_extracted`, `signal_overwritten`,
  `baseline_adjusted_eot` itself — so the deletion was, incidentally, erasing the record of manual
  signal overwrites from a panel whose purpose is to show them.
- **`docCount`** counts `signals_extracted` specifically.

**What the deletion did change, since D1 wired `events` into `signalInputs`, is C1.4.** Dropping
`project_created` takes C1.4 from **Green, 100%, 3 events** to **Red, 0%, 1 event** on a project
whose trail was intact. The reset was making the platform report a worse audit trail than the
project actually had — a wrong number caused by destroying the record, which is the compounding
this task exists to stop.

### The fix, and why this shape

The event log is left alone, and the reset is recorded with `_append_event` — **the shape this
module already uses for every other mutation** (`project_archived`, `project_restored`,
`project_number_changed`, `signal_overwritten` all use it). No new table, no new pattern, no
migration. Superseding and tombstones were considered and rejected: both are row-level shapes for
row-level stores (`computed_results.superseded_by`, `document_uploads.supersedes_document_id`),
and this is a JSON list inside a document, where "append and never remove" is already the idiom.

The `signals_reset` entry now carries **what was cleared, by shape and not by value**: how many
`signalInputs` fields, which ones by name, which signal blocks, how many simulation modules, and
the caller's `reason` if supplied. Not the values themselves — removing those values is the point
of the action, and writing them into an event that `get` returns would defeat it.

Measured after the fix:

```
after reset : ['project_created', 'signal_overwritten', 'project_archived',
               'project_restored', 'signals_reset']
```

---

## Part 2. The rest of the legacy facade

Surveyed all ten POST actions by reading each handler's write path and then exercising it, rather
than by grepping for `.pop` — the limitation the geocode sweep had. **One further violation found,
and it is larger than the one I was sent to fix.**

### `w_save` wiped the event log, and needed no credential to do it

`w_save` replaces the stored document wholesale with the client's copy, so `events` was whatever
the client sent. Measured:

```
stored before                                   : ['project_created','project_archived','project_restored']
save with NO events key, no concurrency token   : accepted -> stored events now []
save with a fabricated one-entry list           : accepted -> stored events now ['only_this_one']
```

Both accepted. `_check_not_stale` returns without complaint when the client presents neither
`record_version` nor `updatedAt`, and the legacy frontend sends neither. **This is the write path
the frontend actually uses** (`store.js` posts `{action:"save", project}`), and a project whose
in-memory copy came from the slim projection never carried `events` at all — so an ordinary
address edit through `ingest.js` on a slim-loaded project destroyed the log.

**Fixed, because leaving it would make the Part 1 fix cosmetic.** The rule is: *the event log may
be extended, never shortened or substituted.* A save whose `events` starts with the stored list is
taken as a genuine append; anything else leaves the stored log standing. The client is a
legitimate appender — `signals.js` pushes a `simulation_run` entry and then saves — so the server
cannot simply own the list, and a check asserts that a genuine append is still accepted, because a
fix that broke it would be a silent regression.

### Every other action

| Action | Write shape | Verdict |
|---|---|---|
| `create` | INSERT, refuses if the id exists | append-only |
| `save` | replaced the stored doc wholesale | **was the second violation, now fixed** |
| `archive` / `restore` | `_append_event` on the **stored** doc | append-only |
| `setprojectnumber` | reads the stored doc, appends an event | append-only |
| `resetsignals` | truncated the log | **fixed, Part 1** |
| `overwritesignal` | reads the stored doc, sets one field, appends an event | structurally append-only; see below |
| `savehistory` | INSERT `ProjectSnapshot` | append-only. Two saves for the same period leave **two rows** — verified — so it accumulates rather than replacing |
| `saveauditresult` | INSERT `File` | append-only |
| `saveportfoliohealth` | **DELETEs all prior portfolio-health snapshots**, then inserts | **deletes, deliberately** — see below |

**`w_saveportfoliohealth` is the one remaining deletion**, and it is the only `session.delete` in
the application. Verified: two saves leave one row, the first is gone. Its comment says this
"matches the live model, which keeps a single portfolio_health.json at the Drive root" — a
deliberate reproduction of the Apps Script. It destroys the history of portfolio-health snapshots,
which is a research-record question rather than a bug, and it is atomic (delete and insert in one
transaction, so a failed insert rolls the delete back). **Reported, not changed**: it is a
different store from the event log and reversing it is a decision about what the portfolio-health
record is for.

**`w_overwritesignal`, current state, reported not fixed as instructed.** It still accepts an
arbitrary `signalInputs` field name and an arbitrary value, PM-gated but otherwise unvalidated,
with exactly one exception: `docRiskScore` is range-checked (T18's fourth entry point). A caller
can still write nonsense into `cpi`, `bac`, `actualPctComplete`, or a field name that does not
exist. It does append a `signal_overwritten` event recording the field and the reason — though not
the from/to values, which it returns to the caller and does not store. Its structural shape is
sound; its validation is the open item, and it needs a per-field contract decided before anything
is written.

### GET actions

None write. `gethistory` reads `project_snapshots`, never `doc["history"]`; the rest are
projections.

---

## Consequences

### Has event data already been deleted, and is it detectable?

**Nothing reachable locally has lost anything, and one of the two paths is undetectable after the
fact.**

I inspected every project store reachable in the repository read-only: **3 project rows, 0
carrying a `signals_reset` event, so 0 truncated by that path.** Production was not inspected.

Detectability differs sharply between the two violations:

- **The reset path leaves a signature.** A project whose log contains `signals_reset` but not
  `project_created` was truncated, because `project_created` is written at creation by both
  `w_create` and `a_projectcreate` and nothing else removes it. That query is available to you on
  production and I have not run it.
- **The `w_save` path leaves no trace at all.** It replaced the list with whatever arrived; a
  wiped log is indistinguishable from a project that never had events. There is no signature, no
  count to compare against, and no second copy. **If this has happened in production, it is not
  recoverable and not detectable.**

### Does the research export or any decision trace depend on these events?

**No, and this is the one piece of good news.** The export reads `AuditEvent` — the append-only
table — and only for `evidence_viewed`, which supplies `deliberation_seconds` and
`pre_assessment_seconds`. It never reads `doc["events"]`. `EXPORT_COLUMNS` is 39 columns and
contains nothing named for an event, a result or an audit; the stages 7-8 finding that it carries
no `result_id` is unchanged.

So a decision's trace to its evidence runs through `Decision.result_id` →
`ComputedResult.source_documents`, none of which passes through the deleted log. **The research
record was not damaged by either violation.** What was damaged is the operational project's own
history, and — since D1 — the C1.4 verdict computed from it.

---

## Verification

| Check | Result |
|---|---|
| Server suite, freshly migrated DB per suite | **1190 across 22 suites, 0 failures** (1177 → 1190) |
| `tests_render.html` | **43/43** |
| `tests.html` | **51/51** |
| Compositing proven before reading any DOM | visible, 63 rAF/s |
| New checks proven able to fail | 4 faults, distinct signatures |

`test_writes_a1b` is 70 checks, was 57. Fault injection:

| Fault restored | Result |
|---|---|
| The original `signals_extracted`-only truncation | **67/70**, 3 red |
| The reset stops recording what it cleared | **68/70**, 2 red |
| `w_save` takes the client's events verbatim | **66/70**, 4 red |
| `w_save` server-owns the log, refusing legitimate appends | **68/70**, 2 red |

**One of my checks was vacuous and injection caught it, which is the sixth session running.**
The `w_save` checks read `resp["project"]["events"]` directly, so with the fix removed the suite
died on a `KeyError` before the assertion evaluated — it printed no `RESULT` line at all, and my
first injection pass showed nothing and looked like a pass. They now go through a helper that
returns `None` for a missing or non-list key, so the handler dropping it makes the check **fail**
rather than raise past it. **I did not add an unconditional check**; the two `precondition:` lines
I added both assert a measured property of the fixture and both go red under fault A.

---

## What I could not establish

- **Whether production has lost event data.** Not inspected. The reset signature is queryable; the
  `w_save` wipe is not.
- **Whether the legacy `simulation_run` append path still runs in a shipped build.** `signals.js`
  is loaded, but the block that pushes the event is inside a guard on the client-side simulation
  libraries, which `index.html` does not load. I preserved the append capability rather than
  assuming it is dead.
- **Whether `w_saveportfoliohealth`'s single-snapshot model should change.** A decision about the
  portfolio-health record, not a defect.
- **The facade's authentication posture.** A sessionless caller can still reset any project's
  signals. Documented as deliberate in `guard_project_write`; I did not change it.
