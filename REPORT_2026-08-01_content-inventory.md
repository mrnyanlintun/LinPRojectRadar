# Content inventory, before any rewriting

Five read-only inventory agents, one per surface. This is the pre-rewrite report you asked for.
**No explanatory copy has been changed yet.** The globe default change (`5c099a9`) is separate and
already committed.

The headline is that the rewrite is roughly ten times the scope the brief assumed, and **three of
the brief's premises are wrong**. Those are worth settling before I write a word of replacement
prose.

---

## 1. Three premises that did not survive contact with the code

### 1.1 There is no chat assistant to rewrite

`assets/js/assistant.js` is a **scripted keyword matcher** over `knowledge.js`. There is no system
prompt, no API call, no model, no retrieval layer beyond a regex scorer at `assistant.js:119`. Its
own header says so: *"SCRIPTED: answers come only from the curated knowledge base... No LLM, no API
call, no backend, no key."*

There is **no `_lib` directory**. None of `pceif_definition`, `escalation_logic`,
`governance_framework`, `faq_simulated` or `signal_taxonomy` exist as files. The only real Anthropic
prompt in the repository is in `server/app/extraction_client.py`, and it is for document extraction.

So "rewrite the assistant's system prompt and its knowledge files" has no object. What exists is one
324 KB `knowledge.js` and one 401 KB `ds_defensibility_data.js`.

**But the platform claims otherwise, in both directions, and that is a real defect:**

| Where | Claim | Reality |
|---|---|---|
| `index.html:813` | "Signal extraction, **assistant chat**, document identification: `claude-sonnet-4-6`" | The chat is not LLM-backed at all |
| `knowledge.js:583` | "AI (Claude API, Anthropic) explains and summarizes" | Same |
| `knowledge.js:166` | "**There is no backend, no LLM call**, no analytics, no tracking" | There is a FastAPI backend and server-side Claude extraction |

A director reading the About tab concludes the chat is an LLM. A director reading the Knowledge
Library concludes there is no server. Both are false, in opposite directions, in the same app.

### 1.2 The framework and method sections are not empty

They are **fully populated and extensively wrong**, which is worse. `FRAMEWORK_TOPIC`
(`knowledge.js:2652`), `STATUS_RULES_TOPIC` (2690), `JUDGMENT_TOPIC` (2718), `LIMITATIONS_TOPIC`,
`REFERENCES_TOPIC`, all eleven `MODREF_TOPICS`, and every defensibility section render in full.

The only genuine placeholders are `index.html:874` (`<td id="about-date">—</td>`, script-filled), a
fallback string shown only if the data file fails to load, and ~25 empty `defenseQuestions` arrays
that render as a silently absent block.

### 1.3 PCEIF is not confined to prose, and ships with two different expansions

Two mutually exclusive expansions render **on the same tab**:

- "**Public Capital EVM Intelligence Framework**" — `knowledge.js:66, 76, 544, 2656`, `README.md:5`
- "**Probabilistic Capital-project Executive Intelligence Framework**" — `ds_defensibility_data.js:10`

At most one was ever right.

It is also in code: `decision.js:14` `PCEIF_VERSION`, `PCEIF_STATUS_LABELS`, `PCEIF_STATUS_HEX`,
`knowledge.js:328` `svgPceifFlow()`. Roughly **60+ user-visible occurrences**, including a chapter
titled "The PCEIF Governance Framework" (`ds_defensibility_data.js:3677`) and a rendered heading
"How PCEIF Is Accredited".

`index.html` contains **zero** occurrences — the acronym was already retired from the main UI and
survives in `knowledge.js`, `ds_defensibility_data.js` and `README.md`.

**"PDAF" does not appear anywhere in the repository.**

---

## 2. Your nine truth claims, verified against code

| # | Claim | Verdict |
|---|---|---|
| 1 | Computation server-side, browser computes nothing | **True for all statuses**, with two qualifications below |
| 2 | 101 computations, four groups | **101 declared, 100 implemented** — see below |
| 3 | Group C does not contribute to status | **True but incomplete** — C *and D* are both excluded |
| 4 | Group D portfolio level, needs >1 project | **True**, two independent guards |
| 5 | Extract once per unique file, cached by hash | **True**, SHA-256, `documents.py:454` |
| 6 | Stored with version, seed, period cutoff | **True, and stronger than claimed** |
| 7 | Decision sequence enforced server-side | **True for ordering**, one detail wrong |
| 8 | One PM decides, observers read | **True** |
| 9 | Geocoding server-side via Nominatim | **True** |

**Corrections I must make before writing any of this:**

- **Not "101 analytical computations".** The registry declares 101 live (103 rows, 2 retired):
  A Project Health 53, B Recommendation & Governance 36, C Data & Evidence Health 7, D Portfolio
  Level 5. But `A4.1 Document Risk Score` is **declared and unported**, so only **100 are
  implemented**. `registry.py:76` raises rather than silently omitting, and `compute_project`
  returns an explicit `unported` list. Safe phrasing: *"101 computations in the registry, of which
  100 are implemented and numerically validated."*
- **Group names in code use ampersands**: "Recommendation & Governance", "Data & Evidence Health".
- **Groups C *and* D are excluded from status** (`compute.py:17-28`, `group not in ("C", "D")`).
  Naming only C invites the obvious follow-up.
- **"Disposition with rationale" overstates it.** `disposition` is required and validated against a
  closed vocabulary; **`rationale` is an unvalidated optional passthrough accepting `None`**
  (`research_decision.py:550`). Write "with a rationale field captured".
- **"The browser computes nothing" is not literally true.** No project, category or module status is
  derived client-side, which is the claim that matters. But `detail.js:468` still runs
  `pcMilestoneMeanSlip()` in the browser on a participant route. Write the precise version.
- **`research/deepdive.html` is not access-controlled.** It loads the compute libraries and states
  *"NOT A SECURITY BOUNDARY, AND NOT PRETENDING TO BE. Anyone who knows the URL can open this
  page."* It is unlinked and obscure; the protection is that every action behind it is role-checked
  server-side. Do not describe it as researcher-restricted.

**Two claims are defensible in stronger terms than you wrote them**, and should be:

- `computed_results` is **append-only**: a recompute writes a new row and sets `superseded_by`, and
  once a submitted decision references a row, a database trigger (migration 0009) rejects any update
  except setting `superseded_by`. Nothing in the analytical layer reads the system clock;
  `period_cutoff` is the only notion of "now".
- Membership revocation is a **timestamped state change**, not a delete, carrying `added_by`,
  `added_at`, `revoked_by`, `revoked_at`.
- Worth adding, because a committee will probe it: the recommendation is hidden from **all** members
  including observers until the PM's pre-judgment locks, *because observers may be senior to the
  PM*. That closes an anchoring leak the study design depends on.

---

## 3. "Governance ruleset L2-v0.5-demo" is decoration. Recommend removal.

Repo-wide, `L2-v0` has exactly two hits: `decision.js:14` and `index.html:1076`. Server-side: zero.
The phrase "Governance ruleset" appears **nowhere in code**.

`PCEIF_VERSION` is a bare string stamped as a label into one exported audit record
(`decision.js:407`). It selects nothing, gates nothing, versions nothing. The footer string is
hardcoded separately, so the two can drift.

There *is* a genuinely versioned rule system — `research_transitions.py`, with `ActionFamily.version`
and `TransitionRule.version` and latest-version resolution — but its versions are arbitrary
operator-supplied strings from the database, and nothing seeds or validates `"L2-v0.5-demo"`.

**Verdict: the footer names a ruleset that does not exist. Remove the line.**

---

## 4. Disclaimers: the conditional covers four elements out of ~20 surfaces

Mechanism is sound. `body.og-account-operational` is toggled by two independent writers
(`features.js:46`, `auth.js:85`), CSS at `radar.css:3962-3968`, and the fail-safe direction is
correct: only an explicit `"operational"` from the server switches away from the restrictive text.

**Currently switched (4):** login notice pair (`index.html:315`/`337`), upload panels
(`signals.js:966/967`, `1262/1263`).

**Not switched — showing research-only text to operational users:**

| Location | Text that is wrong for an operational user |
|---|---|
| `auditor.js:307`, `auditor.js:438` | Upload disclaimers with **no variant class**. Same surface type as `signals.js`, simply unswitched. **Clearest bug.** |
| `index.html:1072` | "Synthetic demonstration data only. All project data is synthetic" |
| `index.html:1074` | "Do not submit confidential or actual project documents" |
| `index.html:888` | "All project data on this site is synthetic" |
| `index.html:548` | "Locations are illustrative: synthetic demonstration data" |
| `index.html:374` | "academic proof-of-concept" (access-denied) |
| `knowledge.js:166` | The whole "Demo boundaries" block |

**Both export paths are completely bare.** `export.js` (the XLSX workbook) and
`server/app/research_export.py` contain **zero** occurrences of "Notice", "advisory", "disclaim",
"synthetic", "Washington" or "©". The exported workbook is the artifact most likely to leave the
platform and be read by someone who never saw a footer. `research/deepdive.html` also carries none.

**Also flagged, independent of this rewrite:** the operational notice at `index.html:337-355` is
marked *"DRAFT. NOT YET REVIEWED"*, and its comment says it could never display because no account
resolved to operational in that build. **That gate has since moved** — `auth.js:85` now sets the
class straight from the login response. So unreviewed draft liability text is live for operational
accounts today.

---

## 5. The attribution line: no current form matches the required text

Required, exactly, on two lines:

> Doctor of Engineering
> The School of Engineering and Applied Science of The George Washington University

Current forms, all different, and the last two name the **department** rather than the School, so
these are substantive changes and not reformatting:

| Location | Current |
|---|---|
| `index.html:359` | "The George Washington University · Doctor of Engineering praxis research" |
| `index.html:375` | "GWU Doctor of Engineering Praxis, Nyan Lin Tun" |
| `index.html:886` | "...at The George Washington University, **Department of Engineering Management and Systems Engineering**" |
| `index.html:1076` | "(The George Washington University, **Engineering Management**)" |
| `calibration/verify.html:166`, `tests.html:284`, `tools/export_lib.html:210`, `assets/visualizations/pceif_neural_signal_flow.html:711` | The praxis sentence, verbatim, four times |

---

## 6. Other findings that change what may be written

- **`README.md` is substantially false.** "A static, client-side demonstration"; "Phase 1 is
  front-end only: **no backend, no AI, no Google Drive, no network calls**"; "Module 01 — real Monte
  Carlo". It is the repository's front door and contradicts the shipped `server/`.
- **`knowledge.js` accordion titles are literally category numbers** — "Cat 1.1: Hybrid Dynamic
  Simulation", "Cat 6.1: Conservative Dominance" — violating the repo's own rule in
  `COPY_GLOSSARY.md`: *"Module ids never appear in user-facing text."* `detail.js:1250` renders the
  number twice: `"Cat 1": "Cost Performance (Cat 1)"`.
- **`DSD_ID_REWRITES` (`knowledge.js:2462`)** is a render-time scrubber rewriting leaked module ids
  into prose. It is a cosmetic shim over stale source text, and anything not in its 12-entry list
  still reaches the user.
- **Three incompatible layer models ship at once**: two-layer (`knowledge.js:550`), four-layer
  (`knowledge.js:2669`), "Layers 1 and 2" (`index.html:873`).
- **Three incompatible category taxonomies**: `knowledge.js` "Cat 1 Quantitative EVM",
  `ds_defensibility_data.js` "Category 1 Cost / EVM Forecasting", and the current A/B/C/D groups.
- **Persistence contradiction inside one page**: `index.html:809` "Google Drive... **No SQL
  database**" vs `index.html:835` "Relational store, one record per project".
- **An overclaim a committee will find.** `ds_defensibility_data.js:18` lists fourteen
  **label-to-algorithm mismatches** that "should be renamed or reimplemented before a formal
  defense" — including Isolation Forest, Linear Programming, Pareto Frontier, ABM Governance. The
  About tab's Capabilities table (`index.html:850-860`) advertises those same items **with no
  caveat**, and `ds_defensibility_data.js:3717` asserts "**No capability claims a statistical
  property it does not have**", contradicted by its own line 18.
- **Leftover coursework voice in shipped prose**: "This is PCEIF's explicit handling of **the
  course's caveat**..." repeated at `ds_defensibility_data.js:3128, 3159, 3185, 3211, 3237, 3263,
  3290`.
- **Em dashes**: `knowledge.js` and `ds_defensibility_data.js` are already clean (zero). The sweep
  has not run on `index.html` (visible instances in footer, nav, login), `auditor.js` (23),
  `detail.js:391`, `assistant.js:152`, or `README.md` (16).

---

## 7. Two notice variants — DRAFT, REQUIRING YOUR REVIEW

**I am not adopting these. They are drafts for your approval, and I have not applied them.** You
asked me not to adopt liability language on my own judgement, and I have not. Both retain the GWU
attribution, the copyright and trademark notice, and that outputs are advisory. Neither contains an
em dash.

### 7.1 Research variant, and the pre-sign-in default

> **Notice: academic research instrument.** Opus Gubernatio is a proof of concept developed solely
> for doctoral research and demonstration. It is not a commercial service and is provided as is,
> without warranty of any kind, express or implied.
>
> All project data is synthetic. No real project, agency, employer, contractor, or vendor is
> referenced. Do not upload confidential, proprietary, personally identifiable, or otherwise
> sensitive information, or any document relating to an actual project.
>
> Uploaded content is sent to third-party artificial intelligence services for extraction and is
> stored in research infrastructure. Analytical outputs are advisory. They are not a validated
> compliance determination, a contractual direction, or a diagnosis of a live project. The operator
> disclaims all liability arising from or relating to uploaded content to the fullest extent
> permitted by law.

### 7.2 Operational variant

> **Notice.** Opus Gubernatio is provided as is, without warranty of any kind, express or implied.
>
> Analytical outputs are advisory. They are not a validated compliance determination, a contractual
> direction, or a diagnosis of a live project.
>
> Uploaded content is sent to third-party artificial intelligence services for extraction and is
> stored in the platform. You are responsible for confirming that you are authorized to upload each
> document, and for your organization's data handling, confidentiality, and records obligations. The
> operator disclaims all liability arising from or relating to uploaded content to the fullest
> extent permitted by law.

Per your instruction the operational variant does **not** say synthetic data only, does **not** say
no real project is referenced, and does **not** tell the user not to submit actual project
documents.

### 7.3 Attribution and copyright, retained in every state

> Doctor of Engineering
> The School of Engineering and Applied Science of The George Washington University

> © 2026 Nyan Lin Tun. All rights reserved. Opus Gubernatio™ and the associated framework, software,
> and documentation are the intellectual property of the author. Unauthorized reproduction,
> distribution, or use is prohibited.

**Consent text is untouched.** The placeholders at `index.html:387-400` are correctly marked "DRAFT.
NOT YET REVIEWED" and need IRB approval, not an editor.

---

## 8. What I need decided before the rewrite

Three questions where guessing would be worse than asking.

1. **What replaces the framework's name?** Removing PCEIF from ~60 user-visible places leaves the
   framework unnamed. `index.html:873` already uses "Decision-support framework, Layers 1 and 2".
   Options: adopt that everywhere, adopt a new name, or drop the framing and describe the platform
   directly without naming a framework. This decides the voice of every rewritten section.

2. **The fourteen label-to-algorithm mismatches.** The Capabilities table advertises capabilities
   the defensibility file says need renaming or reimplementation before defense. I can (a) remove
   the uncaveated table rows, (b) caveat them, or (c) leave them. Given the audience, I recommend
   (a) or (b), but removing advertised capability is your call, not mine.

3. **Scope of this pass.** Doing `knowledge.js` and `ds_defensibility_data.js` properly is a large
   piece of work on its own: ~60 PCEIF occurrences, three incompatible taxonomies, three layer
   models, the whole "Cat N" title scheme, and a chapter titled "The PCEIF Governance Framework".
   Recommended order, highest harm first:

   1. The false capability claims — assistant chat as Claude-backed, "there is no backend", and the
      accreditation contradiction. These mislead a director *today*.
   2. Disclaimers: extend the conditional to the footer, `auditor.js`, About, map caption; put a
      notice into both export paths; fix the attribution line; remove the governance ruleset string.
   3. The About tab: architecture, persistence contradiction, capabilities, and the corrected
      computation claims from section 2.
   4. `README.md`.
   5. `knowledge.js` and `ds_defensibility_data.js` — the largest, and the one that needs the naming
      decision from question 1.

---

## Regression

854 checks across 17 suites, unchanged. No source file has been modified by this inventory; the only
commits in this session are the globe default (`5c099a9`) and this report.
