# Document versioning

**1013 checks across 21 suites pass. `tests_render.html` 26/26.** Migration 0013 is written and
applied against a throwaway SQLite. **Production has NOT been migrated.**

---

## 1. The current behaviour, established from the code and measured

Your description was that a revised document "arrives as an unrelated document while the
extraction cache has frozen the original's figures". **The first half is right and the second is
not, and the real behaviour is worse than either.**

The cache freezes nothing at the project level. The revision is different bytes, so it gets its
own `documents` row and its own extraction. What actually happens:

**It stores both, and both reach computation.** `_period_documents` selected on
`(project_id, period)` and de-duplicated on `sha256` only. There is no filter by `doc_type` and no
notion of recency, so two versions of one pay application were simply two members of the period's
document set. No collision: `uq_document_uploads_once_per_period` is unique on
`(project_id, period, document_id)`, and a revision has a different `document_id`, so nothing
conflicts and nothing is refused.

**Which version's figures survived was then decided by the SHA256.** `_ordered_docs` sorts by
`(rank, doc_type, sha256)`. Two versions of one document share a rank and a doc_type, so the
tiebreak is the content hash. Measured:

| Field class | Example | Behaviour with two versions present |
|---|---|---|
| First-wins | `monthly_report` ev/ac/pv/bac | the **lower** hash wins |
| Last-wins | `pay_application` ac, actualPctComplete | the **higher** hash wins |
| Additive | `rfiCount` | **both counted**: 10 revised to 12 assembled to **22** |
| keep_max | `rfiNumber` | a downward correction **silently discarded** |

Measured output, same two documents, only the hash ordering differing:

```
monthly_report ev, original 4.0M vs revision 5.0M
  original hash LOW,  revision HIGH -> ev=4,000,000  cpi=1.0     ORIGINAL (superseded) wins
  original hash HIGH, revision LOW  -> ev=5,000,000  cpi=1.25    revision wins

pay_application ac, original 4.0M vs revision 4.8M
  original hash LOW,  revision HIGH -> ac=4,800,000  cpi=0.938   revision wins
  original hash HIGH, revision LOW  -> ac=4,000,000  cpi=1.125   ORIGINAL (superseded) wins
```

**Three consequences worth stating plainly:**

1. A revision won roughly half the time, by luck of the hash. Not "the original's figures are
   frozen" but "an arbitrary one of the two wins".
2. First-wins and last-wins fields resolve in **opposite directions**, so a single revision could
   produce a `signalInputs` that mixes both versions. The stored result was internally incoherent
   in a way nothing surfaced.
3. It was **deterministic**, which is worse than random. The same inputs reproduced the same wrong
   answer, so a recompute confirmed it and it looked stable.

**And a result could not say which version produced it.** `computed_results` carried
`signal_inputs` but no document identity; `signal_inputs.sources` records a docType per field and
never a document. Once a period's document set moved on, "which version produced this Amber" was
unanswerable.

## 2. What was built

### `document_uploads.supersedes_document_id`, and why that shape

**Not on `documents`.** That table is content-addressed: one row per unique file for the lifetime
of the platform, shared by every project that uploads those bytes. Supersession is not a property
of the bytes. The same file can be current evidence in one project and superseded in another, so
marking the shared row would leak one project's revision into every other project holding the same
document, and would break the property `documents` exists to provide (two PMs uploading the
identical file read the same extraction row).

`document_uploads` is scoped to `(project, period)`, which is exactly the scope in which "this
supersedes that" is a true or false statement, and it already carries `uploaded_by` and
`uploaded_at`, so the claim comes with who asserted it and when.

**The pointer runs new to old, not `superseded_by` old to new.** Three reasons:

- **Append-only.** The superseding upload is INSERTED carrying the pointer; the superseded row is
  never updated. Nothing rewrites a row a stored decision may reference. `computed_results` uses
  `superseded_by` in the other direction, and the difference is deliberate: there the superseding
  row is written by the same transaction that supersedes, and there is exactly one live row.
- **A revision can itself be revised.** C supersedes B supersedes A is a chain of inserts. With
  `superseded_by` on the old row, superseding B means rewriting a pointer already written, and
  "current" starts depending on update ordering.
- **The claim belongs to the act**, not to the document being replaced.

Cost: "is this superseded" is a reverse lookup rather than a column read. One indexed query;
`ix_document_uploads_supersedes` covers it.

**No foreign key**, deliberately. The referenced id comes from the request, and a bad one must
refuse by name rather than surface as a driver integrity error. The application checks the
document exists **and is already in this project and period**, which is stronger than a foreign
key could express.

### Explicit, never inferred

A `supersedes` field on the uploaded document entry. **Nothing is inferred from upload order**, and
that is a correctness decision rather than caution: two documents of the same type in one period
are not necessarily versions of each other. Two RFI logs from different weeks are both current
evidence, and inferring supersession from arrival order would silently discard one.

### The superseded document stays readable

`_period_documents` excludes it from computation. `a_projectuploadstatus` lists it separately under
a new `superseded` key, marked `contributes: false` and naming `superseded_by_document_id`. The
row, its bytes, and its extraction are all retained; the suite asserts all three, because deleting
them would make a decision recorded against that version unreproducible, which is a property the
About tab states.

### `computed_results.source_documents`

Each result records the documents actually assembled: `document_id`, `sha256`, `doc_type`,
`filename`. A result computed before a revision keeps naming the version it used.

## 3. Results computed against a now-superseded document: FOR YOUR DECISION

**I have not changed any existing result, and this is flagged rather than settled.**

The situation: a result computed from version 1 stays live after version 2 supersedes it, until
someone recomputes. Three options.

**Option A, recompute automatically on supersession.** The live result always matches the live
document set. Against it, and I think decisively: a recompute **rewrites what a participant was
shown**. If a PM has already recorded a preliminary judgment or a decision against that result,
the research record now contains a decision whose stated evidence no longer matches what the
decision was actually made against. The platform's whole append-only discipline exists to prevent
that. `adminrecompute` already requires an explicit reason for exactly this reason.

**Option B, mark the result stale.** Add a flag when a source document is superseded, so a reader
sees "this was computed from a version that has since been replaced". Honest and non-destructive.
Costs: a new column, a new user-facing state, and a decision about whether a stale result may
still be decided against. It also needs wording, which is yours.

**Option C, leave it, and let the existing recompute path handle it.** The result stays exactly as
computed and stays reproducible, `source_documents` now says which version produced it, and
`adminrecompute` writes a new row with a stated reason when you want the revision reflected.

**I chose C for this session** because it is the only one of the three that changes nothing about
already-collected data, and because `source_documents` closes the actual information gap: the
question "was this computed from a superseded version" is now answerable by comparing the result's
`source_documents` against the period's live set. **I recommend B as the follow-up** if you want
that comparison surfaced rather than derivable, and it is a small addition on top of what exists.
What I would avoid is A.

**Nothing in this session recomputes, backfills, or marks anything.**

## 4. Migration

`0013_document_versioning`, revises `0012_expert_reference_lock`. Adds
`document_uploads.supersedes_document_id`, the index, and `computed_results.source_documents`.
Both columns nullable and **not backfilled**: NULL means "superseded nothing" and "predates
provenance recording", which are both true statements about existing rows. Backfilling
`source_documents` by re-reading today's period set would attribute to an old result a document
set that may already have changed, which is the confusion the column exists to end.

Applied against a throwaway SQLite in the scratchpad; `alembic current` reports
`0013_document_versioning (head)` and both columns and the index verified present.

**PRODUCTION HAS NOT BEEN MIGRATED.** Migrations are applied manually by you. Production was not
inspected or queried in this session.

## 5. Tests, and proof they can fail

New suite `server/tools/test_document_versioning.py`, **28 checks**.

**The vacuous-check trap, addressed directly.** The specific way a supersede test passes for the
wrong reason: the superseding document happens to win the sha256 tiebreak anyway, so computation
uses the revision whether or not supersession works. The fixture is therefore built so the
**original wins without supersession**, and the suite asserts that precondition explicitly against
the pure merge before testing anything. Section 1 of the suite also reproduces the original defect,
so the file carries the evidence for why the mechanism exists.

Six faults injected, each restored byte-identical:

| Fault | Result |
|---|---|
| Computation stops excluding superseded documents | 22/28, exit 1 |
| `source_documents` no longer recorded | 25/28, exit 1 |
| `supersedes` claim no longer validated | 25/28, exit 1 |
| `superseded` list dropped from the status surface | 24/28, exit 1 |
| **Fixture flipped so the revision wins the tiebreak anyway** | **26/28, exit 1, the PRECONDITION check fails** |
| Supersession accepted but not persisted at upload | 18/28, exit 1 |

The fifth is the one that matters most: **if this suite's own fixture ever degrades into proving
nothing, the suite fails rather than going quietly green.**

## 6. Verification

| Check | Result |
|---|---|
| Server suite | **1013 checks across 21 suites, 0 failures** |
| `tests_render.html` | **26/26** |
| Migration 0013 on throwaway SQLite | applied, head confirmed, columns and index verified |
| New suite proven able to fail | 6 independent faults, distinct signatures |
| `test_documents_b7b` (the determinism guarantees) | 66/66 unchanged |

Suite arithmetic: 985 + 28 (`test_document_versioning`) = 1013 across 21 suites.

`test_documents_b7b` passing unchanged is the evidence that the exclusion did not disturb the
existing extract-once and reproducibility guarantees.

## 7. Remaining gap, reported not fixed

**An undeclared duplicate is unchanged.** If a PM uploads a revision **without** the `supersedes`
field, behaviour is exactly as section 1 describes: both documents assemble, and the sha256 decides.
The mechanism only helps when the claim is made.

I did not add an inferred fallback, for the reason in section 2: same type and period does not
imply versioning. What I would suggest instead, and did not build because it needs your wording, is
**detecting the ambiguity and reporting it** on upload: "this period now holds two documents of
type X; if one replaces the other, say so". That is a warning rather than a behaviour change, and
it would turn a silent arbitrary outcome into a visible question.

---

## Judgement calls to review

1. **Option C on stale results**, detailed in section 3. The one I would most like you to look at.
2. **No inferred supersession.** A revision uploaded without the claim still merges arbitrarily.
   Defensible, but it means the defect is reachable by a PM who does not know the field exists,
   which is every PM until the interface offers it.
3. **The frontend does not yet offer a supersedes control.** This session added the server
   mechanism and the API; `signals.js` has no UI for marking a replacement, so today the field is
   reachable only by an API caller. Building that UI needs wording and layout decisions I did not
   want to make unilaterally on an upload surface that already carries approved notices.
4. **`supersedes` accepts a `document_id`, not a filename or a doc_type.** Precise and unambiguous,
   but it means a caller must first read `projectuploadstatus` to learn the id. A friendlier
   "supersede whatever the current pay application is" would be guessing at intent.
5. **Cross-period supersession is refused.** A document in period 2 cannot be superseded from
   period 3. I judged that a claim spanning periods would silently drop evidence from a period the
   uploader is not looking at, but if revisions legitimately arrive in a later period, this is the
   rule to revisit.
6. **`source_documents` stores a denormalised copy** (id, sha, type, filename) rather than ids
   alone. It survives independently of whether the referenced rows are later reachable, which suits
   a reproducibility record, at the cost of duplicating the filename.
