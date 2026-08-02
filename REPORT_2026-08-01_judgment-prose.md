# Step 5, the judgment prose

873 checks across 18 suites pass. `tests_render.html` passes 22/22 in a real browser against the
dev server. The app loads with zero page errors after every change below.

Four surfaces were written, in order, each finished before the next: the About tab, the
assistant and its knowledge entries, `README.md`, and `DISCLAIMERS_DRAFT.md`. The Methods and
Framework tab was not in scope and was not rewritten; what that leaves inconsistent is stated
plainly in section 5.

---

## 1. A defect found on the way: knowledge.js has not parsed since the module renumbering

This is the most important finding of the session and it is not prose.

Commit `e34fa50` ("Module renumbering: 101 distinct computations") removed two module entries
from `knowledge.js` by deleting **only each object's opening line**, leaving the remaining seven
properties orphaned. That is a JavaScript syntax error, and it is fatal to the whole file: the
IIFE never runs, so **`LIN_KNOWLEDGE` was never defined, the Methods and Framework tab rendered
nothing, and the assistant had no knowledge library at all** in every build since that commit.
The two orphans were the old Document Risk Extraction entry (excluded from the count by
`GROUP_ASSIGNMENT.md`) and a Design Structure Matrix entry that duplicates the one still present
under Group A. Both orphan bodies are now removed, with comments at each site recording why.
`node --check` passes and the browser smoke test confirms `LIN_KNOWLEDGE` loads with 25 topics.

No test caught this because nothing exercises `knowledge.js` in a browser. A one-line check in
`tests_render.html` asserting `window.LIN_KNOWLEDGE` exists would have caught it; I did not add
one because the task said not to start new surfaces, but it is a cheap next-session item.

## 2. What was written

### 2.1 The About tab (`index.html`, with one CSS addition in `radar.css`)

- **What it is**: the long-form standing description from `NAMING_AUTHORITY.md`, quoted verbatim
  in a styled blockquote (`.about-standing`, new CSS), followed by one paragraph on the two
  audiences. An HTML comment marks the quote as verbatim-from-authority so future edits go
  through the authority first.
- **The framework** (new section): says there is deliberately no named framework and why, then
  gives the capability as the short-form standing description, also quoted verbatim.
- **Method** (new section): the five-step sequence the platform actually enforces (evidence,
  analysis, locked preliminary judgment, disclosure, recorded disposition). It opens by saying
  it describes what the platform does and makes no claim about what any study will find. The
  wording "a rationale field captured" is deliberate: `rationale` is an optional passthrough,
  not a validated requirement.
- **The analytical layer** (new section): 100 computations, the four groups by name and purpose
  only, the document-risk-score footnote, the Data and Evidence Health exclusion from status,
  the Portfolio Level more-than-one-project constraint, and Dempster-Shafer combination
  (verified: `server/app/simulation/fusion.py` is a real Dempster-Shafer port used by
  `compute.py`).
- **Architecture**: kept, with the AI layer corrected to name the deferred capabilities
  (conversational AI, automated audit, speech) as refused by name, and "reads the reported
  figures" replacing extraction phrasing.
- **Removed outright**: the Tech stack table (claimed `claude-sonnet-4-6` chat, `claude-opus-4-8`
  auditor, OpenAI `tts-1` speech; none exist, all three actions are in `DEFERRED_AI_ACTIONS`),
  the Capabilities table (advertised Isolation Forest, LP optimization and the rest of the
  fourteen label-to-algorithm mismatches with no caveat), and the "What it does" pipeline
  (claimed automatic extraction and an auditor that "audits submittals and drawings", when the
  `audit` action is refused by the server).
- **Version table**: trimmed to Last updated, Institution, Program, Author. "v1.0-praxis-demo",
  "Backend v10.28+" and "Framework: Decision-support framework, Layers 1 and 2" were removed;
  nothing in the code implements or reports any of the three.
- **Research context**: rewritten to describe the instrument role only. The DSR-methodology and
  practitioner-validation sentences were removed because they describe the study design, which
  the method section explicitly promises not to do.

### 2.2 The assistant (`assistant.js`) and its knowledge files (`knowledge.js` TERMS and TOPICS)

The assistant has no system prompt in the LLM sense; it is a scripted keyword matcher, which is
the design. Its "prompt" surfaces are the intro message, the out-of-scope answer, the
suggestions, and the input placeholder.

- Intro message now says: scripted by design, not a live AI, answers from a written library and
  live lookups, and says so rather than inventing where it has no answer. The out-of-scope
  answer already said this from a previous session and is untouched.
- Placeholder "Ask about the demo" became "Ask a question" (operational users are not using a
  demo), and "in the current synthetic portfolio" lost "synthetic" for the same reason.
- Knowledge entries the assistant answers from: the PCEIF term and topic are gone, replaced by
  an Opus Gubernatio term and a "What Opus Gubernatio is" topic whose first sentence is the
  short-form standing description verbatim and which states the no-named-framework position.
  Every "Cat N.N" topic title is retitled by method name; module ids no longer appear in any
  answer the assistant can give. Topics describing retired behaviour (Manage Projects page, SYN
  codes, localStorage persistence, two themes, client-side keyword extraction, "no live NLP or
  LLM") were rewritten against the current server reality, verified in code: project creation
  and its research-account gate (`features.py`), upload and extract-once-per-hash
  (`documents.py`), three themes (`THEME_META`), archiving without deletion.
- Method topics (PERT, LOB, CCPM, RCF, DSM, Dempster-Shafer, rough sets, neutrosophic logic,
  interval fuzzy sets) keep their educational content but lost their specific thresholds and
  implementation parameters, which were written against the retired client-side simulation and
  which I could not verify against the server registry one by one.
- Two false live-AI claims inside the Methods tab library were also fixed, though that tab was
  otherwise out of scope, because they directly contradict "the assistant must not imply a live
  AI exists": "AI (Claude API, Anthropic) explains and summarizes using keyword-matched
  retrieval" and the matching callout.

### 2.3 README.md

Rewritten from scratch. The old README described a static, client-side Phase 1 with "no backend,
no AI, no network calls", a Drive `_lib` export flow for files that do not exist, and PCEIF. The
new one describes the shipped system: FastAPI behind one `/exec` facade, Postgres/SQLite with
Alembic, one server-side AI call cached by content hash, the scripted assistant, the 100-count
taxonomy with its footnote, the decision sequence, the two audiences, how to run the dev server
and the suites, and a summary of the content rules pointing at `NAMING_AUTHORITY.md`. The
standing description is quoted verbatim at the top. The retired names are mentioned once, as
retired, so a developer greeting the codebase's 60 remaining `PCEIF` occurrences knows what they
are; that is the only use.

### 2.4 DISCLAIMERS_DRAFT.md

The research and operational variants, drafted and marked as requiring review, with the
attribution and copyright constants. No live surface was changed; the live operational notice in
`index.html` is untouched. The draft also flags for review: (a) the live operational notice is
itself still comment-marked "DRAFT. NOT YET REVIEWED" yet can now display, because `auth.js`
sets the account class from the login response; (b) both export paths carry no notice at all;
(c) the copyright line still says "the associated framework".

## 3. Verification

| What | Result |
|---|---|
| Server suites, each on a freshly migrated SQLite | **873/873 across 18 suites**, all exit 0 |
| `tests_render.html` via dev server, headless Chromium | **22/22** |
| App load smoke test | 0 page errors; `LIN_KNOWLEDGE` loads, 25 topics |
| About panel, measured in the DOM | verbatim description present; PCEIF 0; em dashes 0; module ids 0 |
| `node --check` on `knowledge.js`, `assistant.js` | pass |
| Em dashes in `README.md`, `DISCLAIMERS_DRAFT.md` | 0 and 0 |

The 873 reconciles with the 854 baseline: `test_group_assignment` (17, added T13b) and
`test_simulation` 27 to 29 (the two replaced checks from T13b).

## 4. Claims I could not verify against the code, and what I did about each

- **Five status levels including Complete.** The five-state vocabulary is real in the frontend
  (legend, portfolio counts). I did not trace where the server emits Complete. The five-status
  knowledge topic survives with softened wording; if Complete turns out to be frontend-only
  vocabulary, that topic needs another look.
- **Method thresholds** (PERT +20% bands, LOB buffer days, RCF multiplier set, and so on) could
  not be confirmed against the server registry per module. Removed from the assistant's answers
  rather than asserted. They still exist inside the Methods tab library, which I did not
  rewrite.
- **The fairness gate** as described in the fairness topic and the decision-card topic comes
  from the legacy `decision.js` path, which still renders the decision card from stored results.
  I left both topics standing on the strength of the T12b verification that the card renders; I
  did not re-verify the gate's blocking behaviour this session.
- **"Complete" audit export claims** in the decision-card topic (timezone handling, UTC ISO
  timestamp) are asserted from `decision.js`'s export code as read, not from a live export run.

## 5. Not done, and why

- **The Methods and Framework tab** (`knowledge.js` LIBRARY, module reference, "PCEIF Framework
  Overview" topic, and all of `ds_defensibility_data.js`): 37 PCEIF occurrences remain in
  `knowledge.js` and 49 in `ds_defensibility_data.js`, plus the Cat N title scheme and the
  incompatible taxonomies the inventory documented. This is the large rewrite every session has
  deferred, it was not one of this task's named surfaces, and starting it with the context left
  would have violated the finish-one-surface rule. **The consequence to know about: the About
  tab now says there is deliberately no named framework while the Methods tab, one click away,
  still has a topic named "PCEIF Framework Overview".** That contradiction existed in
  substance before (index.html had already dropped PCEIF); it is now sharper because the About
  tab states the position explicitly. Note that until this session the Methods tab rendered
  nothing at all (section 1), so no user has actually seen those PCEIF topics since the
  renumbering; deploying this branch makes them visible again. If that is unacceptable, hold
  the deploy until the Methods tab pass is done.
- **Export paths** still carry no notice; deliberately left for the disclaimer review, since
  adding a notice there is adopting liability wording.
- **The em dash sweep** on remaining files (`auditor.js` and the legacy researcher surfaces) is
  untouched, per the standing rule that a partial sweep is worse than none. The files written
  this session carry none.
- `tests.html` (the signal-math harness) was not run; the task named `tests_render.html` and
  the server suite, and no signal math changed.

## 6. Handoff

`T6_HANDOFF.md` updated with a new top section covering this session and correcting what is now
stale.

---

## 7. Judgment calls to review, in one list

1. **"Empty framework and method sections" read as sections to add.** The About tab had no
   framework or method section; I created both. If instead you meant existing sections
   somewhere I did not find, say so and I will move the prose.
2. **The framework section narrates the no-name decision** ("A name was considered more than
   once and set aside, because the contribution is empirical evidence about how professionals
   respond to AI decision support, not a new governance framework"). This states your research
   positioning on a user-facing page, which participants will read. You may prefer a quieter
   version that simply describes the capability without explaining the naming history.
3. **The standing description is quoted twice on the About tab**: long form in "What it is",
   short form in "The framework". Both verbatim, but twice on one page is a style call.
4. **The Tech stack and Capabilities tables were removed, not caveated** (the inventory's
   option (a)). Removing advertised capability was flagged as your call; I made it because
   every AI row was false and the capability rows were the fourteen known mismatches.
5. **Version table stripped** of "v1.0-praxis-demo", "Backend v10.28+", and the "Layers 1 and
   2" framework row. If a version string matters for the defense narrative, it needs a real
   source in the code first.
6. **The DSR and practitioner-validation sentences were removed from Research context.** They
   describe study methodology. If you want the About page to carry the praxis methodology, it
   should come back in your words.
7. **Method topics lost their numeric thresholds** in the assistant's answers rather than having
   each verified against the server. Coverage traded for correctness.
8. **The two orphaned knowledge.js objects were deleted, not restored.** I read the renumbering
   commit's intent as removal (both entries are excluded or duplicated in the settled taxonomy).
   If Document Risk Extraction was meant to stay as a described method, it needs rewriting
   against A4.1's excluded status, not restoring as it was.
9. **The Methods tab's two live-AI claims were fixed although that tab was out of scope**,
   because leaving "AI (Claude API) explains and summarizes" contradicted the assistant task
   directly.
10. **README names PCEIF once** to explain the residue in the code to developers. The naming
    authority says do not use the name in anything written; I judged a repo-internal "these
    names are retired" pointer to be the lesser risk against developers reasoning from the ~90
    occurrences they will still find. Delete the sentence if you disagree.
11. **The disclaimer draft flags the live operational notice as unreviewed-but-live** rather
    than pulling it. Pulling live liability text felt like adopting liability posture on my own
    judgement; the flag puts the decision with you.
12. **The About architecture section still says "reads the reported figures... using
    claude-opus-4-6"** with the model id visible to users. The model id is in the code
    (`extraction_client.py`) and was already on the page before this session; keep or remove is
    a disclosure-style call.
