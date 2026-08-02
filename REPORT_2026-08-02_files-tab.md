# The Files tab: the Arora directory, automatic filing, and the two filed states

**Server 1571/1571 across 28 suites, `tests_render.html` 62/62 (was 49), `tests.html` 51/51,
green on merged `main`.** Eleven faults injected for the new server suite, every one detected,
every one reverted byte-identical with the baseline re-run after each; the new render group
separately proven able to fail. The tab was driven in a real browser and confirmed by DOM read.

---

# How the tree is handled per project

**No folder is ever created. There is no `folders` table, and that is the central decision.**

The source document is explicit that the tree is a template a project manager prunes. It says
to delete the disciplines outside Arora's scope, to delete either the CAD or the REVIT folder
depending on which the project uses, and that the PM creates the room-by-room photo folders by
hand. Materialising the template would mean writing roughly sixty folder rows for every
project and then asking someone to delete most of them, and every one of those rows would be a
folder nothing had ever put a document in.

So the template lives in code, as data, in `server/app/jdrive_tree.py`, and a project's real
tree is computed:

> **the template  +  the distinct `document_uploads.folder_path` values for that project**

Three consequences, all of which answer a specific instruction in the source document:

- **Disciplines outside Arora's scope are never created, so they are never deleted.** An empty
  discipline folder does not exist to prune. `occupied` is returned on every node (true for a
  folder holding documents and for every ancestor of one), so the tab shows the project's real
  tree by default and the full template on request. The browser check confirms both: four
  occupied branches for the seeded project, all eight template branches when the filter is
  switched off.
- **The CAD-versus-REVIT choice resolves itself.** Neither folder is created for any project;
  whichever one receives a file is the one that appears. A `.rvt` file files into the Revit
  folder and a `.dwg` into the CAD folder, from the extension, so the project's tree shows the
  one it actually uses and the PM deletes nothing.
- **The room-by-room photo folders come into being when something is filed into them.** The
  template carries `C. PHOTOS` with a `ROOM OR AREA` pattern beneath it; the platform cannot
  know the room, so it does not invent one. Photos file into the dated construction-photos
  folder and are flagged for review so the PM can move them into the room folders the source
  document says the PM creates.

**Placeholder segments are patterns, not folders, and the tab shows them as such.** Several
branches end in a pattern rather than a name (`YYYY-MM-DD`, `CLAIM #`, `YYYY-MM-DD SITE OBS #`,
`CREDIT NAME`). They render greyed and are not selectable, a move to one is refused, and
`resolve_destination` instantiates them into real folder names at filing time, so what is
stored is always a real path and never a pattern.

**The two identifier-bearing branches are built separately and are not flattened into one
type-then-date rule**, because they are genuinely different shapes:

| Branch | Shape | Result |
|---|---|---|
| Claims | identifier **above** the date, two levels | `5_CONST ADMIN/8_CLAIMS/CLAIM 014/2026-06-10` |
| Field visits | identifier **inside** the dated name, one level | `5_CONST ADMIN/7_FIELD-SITE VISITS/2026-06-12 SITE OBS 3` |

A check asserts the two produce different path depths, so a future change that collapsed them
into a shared date rule fails rather than passing quietly. Injecting exactly that collapse
turned it red.

**Folder names are verbatim, including the template's own inconsistencies.** `C. PHOTOS` uses a
period where every other lettered folder uses an underscore; `YYYY_MM_DD XX% INFO` uses
underscores in the date where every other dated folder uses hyphens; `1_ACTIVE CONSTR. SET`
carries an abbreviating period. These are reproduced, not tidied: a PM matching this tree
against the J drive has to see the same strings.

**A correction to the brief's description, worth recording.** The brief describes "numbered
top-level folders `1_RFP` through `6_RECEIVED`". In the source document `1_RFP` is a *sub*
folder of `0_PROJ-MGMNT`, not a top-level folder. The real top level is `0_PROJ-MGMNT`,
`1_PROJ INFO`, `2_DELIVERABLES`, `3_DESIGN`, `4_QC`, `5_CONST ADMIN`, `6_RECEIVED`, and the
unnumbered `NEWFORMA`. This is exactly why the brief said not to reconstruct the tree from it,
and the tree was transcribed from the PDF's own three-column table by position rather than from
the prose.

`NEWFORMA` is carried because it is in the source and a PM will look for it. The source says it
is a secured folder for the Newforma software that nobody needs to open, so nothing is ever
filed there and it is marked read-only.

---

# What else the schema needed (Constraints)

`doc_type` and `period` already existed. **Four columns were added and no new table**
(migration 0016):

| Column | On | Why there |
|---|---|---|
| `folder_path` | `document_uploads` | Where this upload was filed. On the upload and not on `documents` for the same reason `supersedes_document_id` is: `documents` is content-addressed and shared, so the same bytes can be a payment application in one project and reference material in another. Filing is a statement about a (project, period, document). |
| `filing_class` | `document_uploads` | `analysed` / `reference` / `filed`. Stored rather than recomputed from `doc_type`, so a document keeps the class it was filed under if the rules later change; recomputing would silently rewrite history. |
| `needs_filing_review` | `document_uploads` | The placement needs a human to confirm it. Mutable: moving the document resolves it. |
| `classification_confidence` | `documents` | Qualifies the classification, and the classification is of the bytes, so it belongs on the content-addressed row beside the `doc_type` it qualifies. |

---

# Automatic filing, and the confidence threshold

**The premise needed correcting, and the correction is the interesting part.** The brief says
"extraction already produces a document type and a confidence". Half true: the classifier
prompt has always asked the model for `{"docType", "confidence"}`, and `classify()` has always
parsed the answer and then **thrown the confidence away**. It returned a bare string. Nothing
on the platform had ever seen a confidence, and no column held one.

So the confidence is now kept, **without weakening the rule that was already there**.
`classify()`'s docstring records a deliberate decision: never inherit confidence from a
*rejected* classification, because the legacy did and a document whose type had just been
discarded still carried the model's certainty about the discarded answer. That rule is
preserved exactly. `classify_with_confidence` returns a confidence **only when the model's own
claim is what decided the type**; a filename-heuristic fallback or an `UNMAPPED` outcome
carries `None`, which is precisely the rejected-classification case the old docstring refuses
to inherit from.

**`None` is treated as reviewable, not as fine.** That is the same posture the numeric contract
takes: a value that cannot be read is never silently treated as a good one.

**The threshold is 0.70, and it is not calibrated.** It is the legacy Apps Script's own default
for a missing confidence (`parsed.confidence != null ? parsed.confidence : 0.7`), so it is the
one number the instrument being reproduced ever committed to. Extraction has never run against
a real project document, so nothing here has been measured; `CONFIDENCE_THRESHOLD` is a single
declared constant and is the only place to change when it has been.

**Where a low-confidence document lands, and why it is not an invented folder.** It goes to
`6_RECEIVED/<date>_INFO`, whose own description in the source is "All received documents are
saved into individual folders following Arora's naming convention" — the template's own answer
for a document arriving without a designated home. Inventing an `_UNFILED` folder would put a
directory in the tree that the Arora structure does not have.

**The folder is not what makes it reviewable; the flag is.** `needs_filing_review` is set, the
file list shows a "Check filing" mark on the row, and the tab carries a count badge. A document
needing review sits in its real folder, flagged, rather than in a holding pen of its own.
Confirmed in the browser: the badge reads "1 to review" and the row carries the mark.

**Filing is visible and correctable.** Every row shows the folder it landed in and its filing
class, and the PM can move it. Moving is audited (`document_refiled`, recording both folders),
resolves the review flag because a human has now decided, and is verified after commit. A
destination outside the Arora structure is refused by name, and so is a naming pattern.

**Moving does not touch the bytes, the extraction, or any observation.** A misfile is a filing
error, not new evidence; re-deriving anything from it would make correcting a folder silently
change a number.

**The template and the analytical vocabulary overlap only partly, and this is where it shows.**
The Arora tree was written for what a design and construction-administration project produces:
it has folders named for payment applications, claims, site observations, construction
schedules and closeout reports. It has **no** folder for an RFI log, a submittal register, a
safety report or an NCR log, because those arrive from the contractor rather than being
produced by the design team. Those types file to `6_RECEIVED`, with the reasoning recorded at
the rule table so it can be overridden with one line. Eleven types have a folder named for them
in the source document; fifteen do not.

**Two identifiers the template wants and the extraction vocabulary does not have.** The tree
wants a claim number and a site-observation number. Nothing in `extraction_fields.py` asks a
document for either, so there is no extracted field to read; the filename is the only evidence
available, and when it carries none the folder is created without the identifier rather than
with an invented one. `CO-014.pdf` yields `CLAIM 014`; a file with no number in its name yields
`CLAIM`, and the PM supplies the number by moving it.

---

# The two states, filed and analysed versus filed only

**Three classes, declared explicitly**, because the platform previously treated every upload as
something to extract from:

- **`analysed`** — a mapped analytical type. Its figures reach the analytical path.
- **`reference`** — specifications, codes of practice, client and user requirements.
- **`filed`** — stored and never analysed, and that is the **expected** outcome: discipline
  calculations, Revit files, LEED credits, survey photos.

**A plainly filed document no longer reads as a failed extraction.** Before this, anything that
was not a mapped type carried the note "document type not mapped to any signal input; stored,
but contributes nothing to the analysis", so a Revit model, a LEED credit and a specification
all read as something that had gone wrong. A `filed` document now says "filed and stored; this
document type is not one the analysis reads", and a `reference` document says it is reference
material deliberately kept out of the analytical path. Restoring the old wording turns a check
red.

**The `_corpus` separation is preserved without a `_corpus` folder.** The old Apps Script kept
specifications and codes in a separate folder so signal extraction could not read them. The
*separation* is what matters, not the folder name, and inventing a `_corpus` directory would
put a folder in the tree the Arora template does not have. The template already has the right
homes, named for exactly what these documents are:

| Corpus kind | Arora folder | The source's own description of it |
|---|---|---|
| Specifications | `4_QC/<dated>/D_SPECIFICATIONS` | "PDFs of Specs for review" |
| Codes, client standards, user requirements | `3_DESIGN/2_CODE & STANDARDS/B_CODE - CLIENT STANDARDS` | "Copies of referenced building codes, standards, client standards" |

The separation is then carried by the **class**, and it holds structurally in two independent
ways: a reference document is not a mapped type, so `is_mapped()` is false and
`assemble_signal_inputs` skips it (a check assembles a specification on its own and asserts the
result is byte-identical to the empty signal inputs); and it is classed `reference`, so it does
not read as an unmapped or failed extraction.

**Reference detection is deliberately separate from the analytical classifier.** Extending
`DOC_TYPES` with a "specification" type would put specifications inside the vocabulary the
analytical classifier chooses from, and the one thing this separation exists to guarantee is
that they are never chosen from it. Detection is on the filename, which is a stated limitation
rather than a hidden one: nothing reads the *content* of a reference document to decide it is
one, because the only content reader on the platform is the analytical extractor.

**The technical reviewer is gated on the server, by the existing mechanism.** `projectcorpus`
is registered in `features.GATED_ACTIONS` under the **existing `auditor` flag** — no third
scheme — so `gate_action` refuses it before dispatch. Verified: an operational account with the
reviewer on reads the corpus; an admin switches the flag off and the same call is refused with
the feature-flag message; an anonymous caller is refused too, which is the shape the earlier
`getportfoliohealth` finding was about. Removing the gate entry turns checks red.

**Filing is not conditional on the flag.** With the reviewer off, a specification is still
filed, still classed `reference`, and still kept out of the analytical path. Asserted directly:
the flag is switched off and a specification is uploaded, and both facts still hold. Turning the
reviewer off must not change how a document is stored, or turning it back on would find a
corpus with holes in it.

---

# Versions, preview, drag and drop

**Versions surface what already exists.** `supersedes_document_id` records "this replaces
that", as a chain of inserts, so version number is that chain's depth, counted at read time
rather than stored. A stored counter would be a second source of truth that could disagree with
the pointer. Version is a column in the file list, both versions appear, the superseded one is
marked rather than hidden, and each keeps its own upload row and its own folder. Nothing is
replaced on disk. A fault that filtered superseded rows out of the listing turns it red.

**Preview is browser-friendly formats only and no renderer is attempted otherwise.** The server
classifies each file `native` (PDF, images, text), `download` (Word, Excel, PowerPoint) or
`unsupported` (everything else, including CAD and Revit), and the tab renders an iframe only
for the first. The unsupported message is stated once, on the server, and shown verbatim.
Confirmed in the browser: selecting the Revit model shows "Format not supported for preview.
Download the file to open it in the application that reads it", **no iframe is created**, and a
download link is offered for `Tower.rvt`.

**Drag and drop shows the three things without waiting for extraction.** On drop each file gets
its own row reading "Accepted. Filing and analysing…" with a spinner, and when the upload
returns the row is replaced in place with the filing class and the destination, plus "marked
for review" where that applies. Per-file extraction failures are **not** given a second error
surface here: they already render verbatim in the upload panel's existing dialog, and the drop
row points at it.

---

# Verification

- Server suites: 1517 baseline → **1571/1571 across 28 suites**, fresh migrated sqlite per
  suite, `PYTHONIOENCODING=utf-8`. New suite `server/tools/test_files_tab.py`, 54 checks.
- **`tests_render.html` 62/62** (49 before; a new group 9 paints the Files tab from a fixture
  and asserts the render site), **`tests.html` 51/51**.
- **The tab driven in a real browser, confirmed by DOM read**: the tree renders and shows only
  occupied branches by default and the full Arora template when the filter is switched off;
  clicking a folder lists exactly its files with state, version and period; a review-flagged
  row carries its mark and the badge reads "1 to review"; a PDF previews in an iframe; the
  Revit model shows the unsupported message with **no iframe created** and a download offered.
- **Eleven faults, all confirmed applied, all detected, all reverted byte-identical, baseline
  re-run green after every single one:**

| Fault | Result |
|---|---|
| Claims flattened into a plain type-then-date rule | 52/54 |
| The site-observation identifier dropped from the dated name | 53/54 |
| Low confidence no longer routes to the reviewable destination | 50/54 |
| Reference documents stop being classed as reference | 49/54 |
| A filed document reads as a failed extraction again | 53/54 |
| The corpus read loses its feature gate | 52/54 |
| A superseding upload replaces the row instead of standing beside it | 28/32 |
| Move accepts any path, including one outside the structure | 52/54 |
| An unsupported format is reported as previewable | 53/54 |
| The tree materialises every folder as occupied | 52/54 |
| The classifier confidence is discarded again | 46/54 |

- The new render group was separately fault-proven: making a naming pattern clickable took
  `tests_render.html` from 62/62 to 60/62, and it returned to 62/62 after a byte-identical
  restore.
- **Two of my own faults were caught by the harness rather than by me.** One injection anchor
  did not match, and the harness refused to report a result rather than showing a false clean.
  And the first version of the render group **threw**, which stopped the results table from
  rendering at all and read as a clean run; the group is now wrapped so a throw is a red check,
  and the real cause was fixed in `files.js` (it called `LinAuth.getToken` without checking the
  method exists).

# Files changed

- `server/app/jdrive_tree.py` — new. The Arora template as data, the filing rules, the
  confidence threshold, path resolution and the tree view.
- `server/app/files.py` — new. `projectfiles`, `projectfilemove`, `projectcorpus`.
- `server/alembic/versions/0016_document_filing.py` — new. Four columns, no new table.
- `server/app/research_models.py` — the four columns.
- `server/app/extraction_client.py` — the classifier confidence is surfaced instead of
  discarded; `extract_many` carries it.
- `server/app/documents.py` — the filing decision at upload, and the corrected notes.
- `server/app/extraction_merge.py` — `document_as_of` made public so filing and observation
  emission cannot disagree about a document's date.
- `server/app/features.py` — `projectcorpus` under the existing `auditor` flag.
- `server/app/facade.py` — the three actions registered.
- `index.html`, `assets/js/files.js`, `assets/js/workspace.js`, `assets/css/radar.css` — the tab.
- `tests_render.html`, `server/tools/test_files_tab.py` — the checks.
- Nothing under `server/app/simulation/` was touched; no stored data altered; production not
  inspected.

# Still open, flagged rather than decided

- **The 0.70 threshold is uncalibrated.** It is the legacy's own default and nothing has been
  measured against real classifications, because extraction has never run against a real
  project document.
- **Fifteen analytical document types have no folder of their own in the Arora template** and
  file to `6_RECEIVED`. The mapping is one table with a comment per entry and is cheap to
  change once a real project shows where they actually go.
- **Claim and site-observation numbers are read from the filename or omitted.** Adding them to
  the extraction vocabulary would let the platform file them exactly; that is an
  `extraction_fields.py` change and was not made unasked.
- **Reference detection is by filename only**, for the structural reason above. A specification
  whose filename does not say so is filed as `filed` rather than `reference`, and the PM can
  move it.
- **Room-by-room photo folders are still the PM's to create**, by moving photos into them. The
  template says the PM creates them and the platform cannot know the room.
