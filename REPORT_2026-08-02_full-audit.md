# Full platform audit

Read-only audit before study preparation. No code, test, or data changed; findings only.
Method per finding is marked **executed** (ran code or API against a live server),
**probed** (driven in a real browser), or **source-read**, and should be trusted in that order.

Environment: a fresh throwaway SQLite database migrated to head `0017_participant_theme`,
served by `server/tools/dev_serve.py` (stub extractor, no Anthropic key), driven in the
container's browser. Production was not touched. The database was created for this audit and
holds only audit fixtures.

## Section 1: end to end as a user

The whole loop was driven once, in order, as a real user where the interface allowed it and by
the same server actions the interface calls where it did not: admin sign-in, project creation
(both the portfolio form and the admin form), document upload, stub extraction, automatic
filing, period analysis, signals render, participant sign-in, consent, intake questionnaire,
scenario assignment, the four-stage decision sequence to a recorded final decision, both export
kinds built and fetched, and both workbooks opened with openpyxl and read back. **The machinery
completes.** What follows is what it took to get there, which is the finding.

### 1.1 The study cannot be prepared through the interface. (HIGH, executed + probed)

Four server-side prerequisites stand between a fresh deployment and one participant recording
one decision, and none of them can be created from the UI:

1. **A scenario.** `adminscenariocreate` exists and works, but its UI was deliberately
   withdrawn (`admin-ops.js:307`, "The UI is withdrawn. B3's BACKEND IS DELIBERATELY
   UNTOUCHED"). The assignment UI that DEPENDS on scenarios was kept.
2. **A frozen condition sequence.** `adminassign` refuses with "no frozen condition sequence
   for order_group 'G1' and scenario_set 'S1'". `adminsequencecreate` has no UI. The
   `condition_sequences` table is empty on a fresh database (verified by query); nothing seeds
   it.
3. **A frozen configuration.** The sequence's config codes must exist as frozen
   `Configuration` rows ("no configuration exists for code C1"). `adminconfigurationcreate`
   has no UI.
4. **A frozen decision support package, attached per assignment.** Even with evidence attached,
   `researchreveal` refuses: "no decision support package is attached to this assignment".
   `adminpackagecreate` and `adminpackageattach` have no UI.

Each was verified by hitting the refusal in the browser first, then satisfying it with a direct
authenticated call to the documented action, then proceeding. The decision sequence completed
only after all four were hand-assembled. The handoff's stated rationale for withdrawing the
scenario UI ("there are no conditions left to counterbalance, so assigning a participant to a
pre-authored scenario set no longer describes anything the platform does") is contradicted by
the assignment path, which still enforces scenario, sequence, configuration, and package. Either
the enforcement is stale or the withdrawal was premature; they cannot both be right.

### 1.2 A participant can be walked into a dead end that consumes their judgment. (HIGH, probed)

A scenario created without an evidence package id and without a decision support package is
accepted by `adminscenariocreate` and by `adminassign`. The assigned participant then:

- sees "No evidence project is attached to this period" on the Evidence panel, with the
  preliminary-judgment controls fully live;
- can commit a preliminary judgment against that empty panel (probed: it locked);
- is then refused at reveal ("no decision support package is attached to this assignment") with
  no path forward and no path back, because the preliminary judgment is by design irreversible.

The stuck instance then appears in the `participant_inputs` export as a Decisions row (executed:
the export built during this audit contains it). Nothing warns the admin at assignment time that
the scenario carries no evidence and no package, and nothing warns the participant before the
one irreversible step of the whole sequence.

### 1.3 Admin dropdowns are populated once and go stale. (MEDIUM, probed)

Creating a user does not refresh the "PM for this project", membership, or assignment
participant pickers; the new account is absent until a full page reload. Probed directly: a
project was created with the wrong PM because the intended participant was not in the list
moments after being created in the same view. Same class of defect, worse trigger: the scenario
dropdown is populated only by `LinAdminOps.showTab("access")`, which fires on tab CLICK — and
"People and access" is the default, already-active tab, so on first open of Administration the
scenario list is always empty even when scenarios exist (probed: clicking away to "Monitoring
and export" and back filled it). An admin who never leaves the first tab can never assign.

### 1.4 What worked, verified

- Sign-in (username/password) for both account types; wrong-credential and deactivated paths
  not distinguished to the prober (source-read at `a_researchlogin`, consistent behaviour
  observed).
- Portfolio project creation, upload of the `healthy` dev fixture, stub extraction ("newly
  extracted · monthly_report"), period analysis, and a Green project status rendering from the
  stored result.
- Automatic filing into `6_RECEIVED/2026-06-30_INFO` with the "Check filing" review flag
  (expected here: the local stub provides no model classification, so confidence is None, which
  is the documented reviewable state).
- Consent gate (participant sees consent before anything else; operational accounts are
  structurally refused a consent row), intake questionnaire required before judgment (executed:
  `researchprejudgment` refused until `intakesave`).
- The four-stage sequence: evidence → locked preliminary judgment → reveal (idempotent,
  `reveal_at` recorded once) → final decision with disposition vocabulary enforced (executed:
  a missing `disposition` was refused with the full vocabulary in the message).
- Exports: `participant_inputs` (2 decision rows — including the stuck 1.2 instance, which is
  correct Part 5 behaviour) with sheets Notice, Decisions (44 columns), Stimulus, Module
  results, analysis_long (2 rows per instance); `project_health` with Notice and Module results
  only. Both checksums verified server-side on fetch; both workbooks opened and read back with
  openpyxl.

### 1.5 Smaller observations recorded for later sections

- The consent screen is entirely bracketed placeholders, correctly labelled "DRAFT. NOT YET
  REVIEWED." (known deliberate deferral; section 7).
- The Signals tab renders group headings "Recommendation & Governance", "Data & Evidence
  Health", "Cost & EVM Performance", "System Dynamics & Complexity" — ampersands in user-facing
  text (section 6).
- The admin Create-user modal and the intake questionnaire's certifications item use em dashes
  in user-facing text (section 6).
- The portfolio headline "From multi-model signals to a governed decision" makes a
  "multi-model" claim to check against what the platform does (one extraction model; section 6).
- The status legend read "Awaiting analysis 0" while an uncomputed, unplaced project existed
  (whether the legend counts only placed markers is checked in section 4).

## Section 2: cross-feature seams

### 2.1 Reference documents are routed through the analytical extractor, and a failed extraction discards them. (HIGH, probed + source-read)

`jdrive_tree.reference_kind()`'s own docstring: "nothing reads the CONTENT of a reference
document to decide it is one, because the only content reader on the platform is the analytical
extractor and routing a specification through it is precisely what must not happen." The upload
pipeline does exactly that. In `a_projectupload` (documents.py), every hash not already held is
queued for extraction unconditionally; `_decide_filing` — the only place `reference_kind` is
consulted — runs after extraction returns. Probed: uploading `SPECIFICATION_09_2900_Gypsum.txt`
returned `status: "failed"` from the stub extractor's refusal, and the file list afterwards
confirms the document was never stored or filed at all.

Two consequences. Against the real model, every specification, code, standard, Revit model,
photo and other never-analysed document has its content sent to the extraction model first,
spending an AI call and contradicting the stated design. And whenever extraction fails on such
a file — the likely outcome for binary formats — the document is silently dropped rather than
filed, which defeats the Files tab's central claim that "most of the Arora tree is documents
stored and never analysed; that is the expected outcome." The existing suite passes because its
reference fixtures are extractable text; the failing path was never exercised (see section 5).

### 2.2 Seams that held, verified

- **Theme × mobile** (probed): at 390px with transitions suppressed, the upload/decision
  desktop-only gates hold under all four themes — notice text generated, real controls
  `display: none`, zero horizontal overflow, notice colour resolving per theme's `--muted`.
- **Files tab × document versioning** (executed): supersession is explicit-only; uploading a
  revised monthly report with `supersedes` produced v2, marked v1 superseded, and both render
  in the Files list with correct state. A same-type upload without the claim would create a
  sibling, not a version, exactly as documented.
- **Membership × archive × the decision sequence** (executed): archiving the project a
  scenario's `evidence_package_id` names does NOT break a mid-sequence participant — evidence
  still resolves (before/after verified with a fresh participant). `w_archive` gives the admin
  no warning that a scenario references the project, which is worth knowing but not a defect
  while evidence survives it.
- **Delete × export** (executed): `admindeleteparticipant` cleared exactly the six documented
  tables, reported counts per table, and the already-created export was untouched. The
  documented tension stands: consent withdrawal preserves the record, account deletion destroys
  it, and the code says this is deliberate.
- **Observations × export** (executed): the stored `computed_results.module_results` (36
  entries for the audit project) matches the export's Module results sheet row for row. The
  `observations` table (12 rows here) is stored and unexported — a recorded open item, not a
  drift.
- **Geocode retention × markers** (source-read only): retained coordinates come from the stored
  doc, never the client copy; clearing the address clears the coordinates; geocoder failure
  stores `geocodeError` without failing the save. Not probed live — geocoding needs network
  this audit did not exercise.
- **Abstention × display surfaces** is examined with the stored-versus-shown contract in
  section 4.

## Section 3: authorisation, probed

**Nothing was found open.** This is the one section of the audit that came back clean, and the
detector was proved able to report otherwise before that was believed.

Method (executed, all against the live server): the 81 registered POST actions were enumerated
from the dispatch tables themselves (`POST_ACTIONS`, `DOCUMENT_ACTIONS`, `FILE_ACTIONS`,
`WORKSPACE_ACTIONS`, `QUESTIONNAIRE_ACTIONS`, `ASSIGNMENT_ACTIONS`, `DECISION_ACTIONS`,
`EXPERT_ACTIONS`, `EXPORT_ACTIONS`, `MEMBERSHIP_ACTIONS`, `TRANSITION_ACTIONS`,
`IDENTITY_ACTIONS`, `FEATURE_ACTIONS`, `THEME_ACTIONS`) rather than from a hand-written list,
so an action added since the last review is included automatically. Each was called under four
postures: no credential, a research participant, an operational non-admin, and a valid admin.

| Probe | Result |
|---|---|
| All 8 non-public GET actions without a credential | Refused: "missing or malformed session token". No project data returned |
| All 81 POST actions without a credential | Every one refused. Zero succeeded, and no refusal was off-shape |
| All `admin*` actions as a research participant | Zero succeeded |
| All `admin*` actions as an operational non-admin | Zero succeeded |
| Non-member on another project (`projectfiles`, `projectuploadstatus`, `projectupload`, `projectcompute`) | "not authorized: not a member of this project" |
| Non-member write (`archive`, `save`) | "not authorized: only the project's PM may perform this action" |
| Tampered session token | "invalid session token" |

**`w_overwritesignal` field validation** (executed): an unknown field name is refused by name
("Unknown signal field: 'nonsense_field'. This platform has no field by that name"), including
`__proto__`. A known field on a project with no extracted signals is refused with the distinct
"No extracted signals to overwrite", so the two failure modes do not collapse into one message.

**The research and operational gates** (executed): `themeset` refused for a research account
with the fixed-stimulus reason; `adminexportcreate` refused for a participant with
"ResearchAdmin role required"; `projectcorpus` refused without the auditor flag; `projectcreate`
refused for a research account; `consentgrant` refused structurally for an operational account.

**Proof the probe can fail** (executed): the identical detector run with a valid admin token
reports 11 `admin*` actions succeeding. A detector that returns "NONE" under every posture
including the authorised one would be measuring nothing; this one distinguishes them.

Two probes returned "Unknown POST action" rather than a refusal — `expertreferenceget` and
`expertreferencesave`. These names are inferred, not registered; the expert surface's real
action names were not probed and are recorded as **unaudited** rather than as passing.
