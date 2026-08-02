# Which surfaces render the decision card, and for which account type

**Read-only session. No code, no test and no data was modified.**

---

## Which commit this was measured against, and what PR #201 supersedes

**The measurements below were taken at `a5c3da7`. PR #201 (the D1 implementation, T25) merged
while this branch was open and changes part of section 5.** Rather than restate stale numbers, I
re-ran the two findings that matter against the merged tree at `c05d028`. Both survive:

| Finding | At `a5c3da7` | Re-measured at `c05d028` |
|---|---|---|
| Detail page blank, `ReferenceError: populated is not defined` | yes | **unchanged**, `#detail-root` length 0, `.dc-field` 0, derived strings absent |
| D1.3 Green dot beside "No history available" | yes | **unchanged**: `status_color: "Green"`, `insufficient_data: True`, rendered `var(--status-green)` |
| Abstentions absent from `module_results` | 47 of 95 stored, 0 with the flag, 0 with a null colour | **36 of 95 stored, still 0 with the flag, still 0 with a null colour** |

**What #201 supersedes, and it is the good half of section 5's evidence.** The specific strings I
quote a research participant seeing — the five B2 "Insufficient signal data" Ambers, Audit Trail
Completeness Red at "0 events recorded", Reporting Frequency Yellow at "no documents uploaded yet"
— **are fixed and no longer appear**. Audit Trail Completeness now reads *"Amber | 50% audit trail
completeness, 1 events recorded"*. Read that subsection as the record of what the fabrications
looked like on a participant's screen, not as a live finding.

**What #201 does not touch is `portfolio.py`.** Group D still emits all five results
unconditionally, so D1.3 is unchanged and is now the only place in the platform where a colour and
an insufficiency flag are emitted together.

---

## The answer

**No. A research participant does not see the browser-derived recommendation. Neither does an
operational user. Nobody does, because the only surface that renders it has been throwing a
`ReferenceError` since 2026-08-01 and renders a blank page.**

**BROWSER-VERIFIED.** `LinDetail.render` references an identifier named `populated` that no
longer exists (`assets/js/detail.js:894`). It is inside the template literal that builds
`root.innerHTML`, so the function throws before assigning anything, `showPage`'s `try/catch`
swallows the throw, and the project detail page shows its header and footer with nothing between
them. Measured on both account types:

```
operational (OPS-1)  -> page 'detail' visible, #detail-root innerHTML length 0
                        LinDetail.render(id) -> ReferenceError: populated is not defined
research    (PM-R1)  -> page 'detail' visible, #detail-root innerHTML length 0
                        LinDetail.render(id) -> ReferenceError: populated is not defined
.dc-field elements present anywhere in the DOM, either account type: 0
```

The four strings the browser-derived recommendation would print — `Recovery-plan review and
management escalation`, `Routine monitoring`, `Program director / PMO`, `Full signal package,
assigned owner` — appear **nowhere in the rendered DOM of either account type**, on any route I
reached.

**So the urgency question the audit posed resolves to neither branch it anticipated.** The
browser-derived recommendation is not a live research-instrument problem and is not a live
operational defect. It is unreachable code sitting behind a page that has been blank for a day.
The live defect is the blank page.

**What a research participant actually sees as the disclosed recommendation is the frozen
`DecisionSupportPackage`, rendered verbatim from the server response.** Detail in section 4.

---

## Method, and which tooling was used

**Playwright driving the pre-installed Chromium** at
`/opt/pw-browsers/chromium-1194/chrome-linux/chrome`, against `server/tools/dev_serve.py` on
`127.0.0.1:8010`. **There is no `preview_start` / `preview_list` tooling in this container at
all**, so the `Demo` trap in the brief could not arise and no preview session was started. The
`Ignore DEng\Demo` directory does not exist in this checkout.

**Compositing was verified before anything was concluded from the DOM**, per the standing warning
in the handoff:

```
document.visibilityState : "visible"
requestAnimationFrame    : 62 frames in 1000 ms
```

Screenshots were taken and looked at, not merely captured.

**Data.** A fresh throwaway `server/dev.db` (gitignored, created by this session, seeded over the
HTTP API): one ResearchAdmin, one research participant `PM-R1` with consent, intake, a frozen
two-period scenario, a frozen decision support package whose every field carries a planted
`PKGMARK` marker, and a PM membership on an evidence project with a real extracted document and a
stored computed result; one operational user `OPS-1` with two of its own projects, both computed.
**No pre-existing data was altered and production was neither inspected nor queried.**

Every finding below is marked **BROWSER-VERIFIED** or **SOURCE-ONLY**.

---

## 1. The decision card has two mount points. Both are dead.

**SOURCE-ONLY, then BROWSER-VERIFIED.**

`renderDecisionCard(p, root = $("#decision-card"))` (`app.js:1615`) has exactly two ways to be
called:

| # | Caller | State |
|---|---|---|
| 1 | Its own default root, `#decision-card` | **No element with that id exists in `index.html`.** The default is `null` and the function returns at its first line (`if (!root) return;`). Verified in the browser: `document.getElementById('decision-card')` is `null` after sign-in on both account types. |
| 2 | `detail.js:988`, the `d-decision` lazy-init, into `.detail-decision` inside the project detail page | **Unreachable.** The page that contains that element never renders. |

There is no third caller. I grepped the whole of `assets/` for `renderDecisionCard`,
`decision-card`, `detail-decision` and `dc-field`.

**The one surface that would host it is reachable and blank.** From the portfolio list both
account types have working `Signals` and `Open →` controls that route to `openDetail(id)` →
`showPage("detail")`. Clicking either lands on the detail route with an empty `#detail-root`.
The screenshot shows the page: masthead, footer disclaimer, and nothing else.

**The portfolio page still advertises the card.** Its intro text, which both account types read,
says: *"Select a project to see its signal ledger, the signal-conflict classification, and the
governance decision, with explicit authority, documentation, and a contractor fairness gate where
required."* Selecting a project shows a blank page. BROWSER-VERIFIED.

### Where the ReferenceError came from

**SOURCE-ONLY, from git.** Commit `062731b`, *"T12b: the hasSignals sweep, and two false
statements in the assistant"* (2026-08-01), deleted `const populated = hasSignals(p);` and
rewrote its two uses on the lines below it, and left the third use at what is now line 894:

```javascript
${populated ? provenanceLineHtml(p) : ""}
```

`git show 062731b -- assets/js/detail.js` shows three `populated` lines removed and none added;
`git show 062731b^` shows four uses. The one at line 894 is the survivor. `detail.js` has not been
touched since.

### Why nothing caught it

Two independent reasons, both **SOURCE-ONLY**:

- **`app.js:1868-1876` swallows it.** `showPage` wraps every page render in `try { ... } catch (e)
  { /* page is already visible; a render hiccup must not block nav */ }`. That comment describes a
  hiccup; what it actually does is convert a fatal error into a blank page with no console output.
  This is why the browser reports **zero page errors** while the page is empty.
- **`tests_render.html` never calls `LinDetail.render`.** Its group 3 is headed *"The detail page
  State badge renders"* and calls `LinApp.stateLabel(p)`, a pure function. Its group 2 is headed
  *"decision card"* and calls `LinApp.renderDecisionCard(p, host)` directly into a synthetic host,
  bypassing the detail page entirely. Both assertions pass against a page that renders nothing.
  **This belongs in the vacuity sweep and was not in it**: the harness written specifically to
  catch "a fatal error hid a whole surface" does not exercise the surface it names.

---

## 2. Is the decision card rendered at all, per account type and route

**BROWSER-VERIFIED throughout.** Both account types share one shell and one route set.

| Route | Reached by | Operational | Research |
|---|---|---|---|
| Portfolio (`data-page="portfolio"`) | landing page after sign-in | radar, map, globe, project list — **no decision card** | identical — **no decision card** |
| Project detail (`data-page="detail"`) | `Signals` / `Open →` in the list, map card, radar select | **blank page.** Card would be here. | **blank page.** Card would be here. |
| Project workspace (`data-page="project"`) | `Open` on the workspace project card | four tabs: upload, documents, detail, decision — **no decision card**, no `.dc-field` | identical |
| Technical Auditor | dock nav | no decision card (`auditor.js` renders its own panels) | same |
| Handbook | dock nav | no decision card | same |
| Admin | admin-only, hidden here | not reached this session | not reached |

The nav set is identical for both accounts: `portfolio`, `auditor`, `handbook`. The one
account-type difference I saw is the workspace create-project card, hidden for a research account
(`workspace.js:186`), and the decision tab's content: an operational account opening it reads
*"No decision sequence is assigned to this account. Period decisions are recorded against a
scenario the researcher assigns."*

**Answer to question 2 (are the fields derived or stored):** the question does not arise on any
live surface, because no surface renders those fields. Where the code exists, it is derived —
`deriveDecision` computes action, authority, documentation and the fairness gate from the fused
status band with a four-branch `if`, exactly as the stages 7-8 audit reported. I confirmed in the
browser that calling `deriveDecision(p)` by hand on an operational project still returns
`{healthState: "Red", action: "Recovery-plan review and management escalation", authority:
"Program director / PMO lead", fairnessGateRequired: false}` — the function works; nothing calls
it on a rendered surface.

---

## 3. Does anything a research participant sees carry a browser-derived recommendation

**No. BROWSER-VERIFIED**, by driving the whole sequence: evidence → preliminary judgment →
commit → reveal.

Searched the participant's live DOM at every stage for the four derived strings. All absent at
every stage. `.dc-field` count: 0 at every stage.

---

## 4. What the disclosed recommendation actually is

**BROWSER-VERIFIED.** After the preliminary judgment is committed and locked, clicking *"Show the
decision support package"* calls `researchreveal` and `renderPackage` writes the server's response
into `#dc-package`. Captured verbatim from the live DOM:

```
Shown at 8/2/2026, 4:19:05 AM. Your preliminary judgment was recorded before this point and is
unchanged.
Recommended action        PKGMARK Escalate to the program director
Detected condition        PKGMARK cost variance exceeds threshold
Alternatives considered   { "a": "PKGMARK alternative: re-baseline" }
Uncertainty               { "u": "PKGMARK uncertainty text" }
Limitations               PKGMARK limitation text
Where this applies        PKGMARK boundary text
Model m1 · package version pkg-v1
```

Every value is a marker I planted in the frozen `DecisionSupportPackage` at seed time. **The
disclosed recommendation is the researcher-authored frozen package, read from the server and
printed field by field. Nothing about it is derived in the browser.**

**A nuance worth stating precisely, because it is easy to misread as reassurance.** The disclosed
recommendation is not the browser's — and it is also **not the 36 Group B computations'**. It is a
frozen artefact an admin authors through `adminpackagecreate`. The analytical layer reaches the
participant through a different panel: the *evidence* screen above the judgment form, which lists
the stored `module_results` including B4.4 Regret Minimization. So the instrument discloses a
researcher-written recommendation alongside server-computed evidence, and the browser derives
neither. **Whether the frozen package is meant to be the disclosed recommendation is a research
design question, not a finding, and I am not treating it as a defect.**

### One thing the redaction does not withhold

**BROWSER-VERIFIED.** Before the lock, the Regret Minimization Index row on the evidence screen
reads:

```
Regret Minimization Index | "This module's finding is withheld until the preliminary judgment
                            for this period is locked." | dot: var(--status-red)
```

The prose is withheld and **the status colour is not**. A participant who has not yet committed
can see that the action-bearing module is Red. After the lock the same row reads *"Minimax regret
recommends: escalate (expected regret score 5/30)…"*. Whether disclosing the colour pre-lock
matters is a measurement question for Lin; the mechanism is that `decision-ui.js:373` renders
`statusColor(m.status_color)` unconditionally and the server's redaction replaces
`evidence_metric` only. I did not check whether `test_decision_ui_t4`'s leak scan covers the
colour; its markers are prose strings, so on the face of it it would not.

---

## 5. Abstentions: which surfaces render a verdict without reading an insufficiency flag

**The concern in the brief is narrower than feared, and one case is real and visible.**

**BROWSER-VERIFIED, and this is the important one.** The operational user's workspace portfolio
panel, with two computed projects so the snapshot is real:

```
Isolation Forest             | Isolation Forest: anomaly score 0%   | var(--status-green)
Portfolio Outlier Detection  | Portfolio percentile: 100%           | var(--status-green)
Signal Trajectory Classifier | No history available                 | var(--status-green)   <--
Cross-project Pattern        | 1 project(s) show similar pattern    | var(--status-red)
Anomaly Score                | Composite anomaly score: 17%         | var(--status-green)
```

**A green dot beside "No history available", on screen, exactly as predicted.** Same on the second
project. This is `workspace.js:750` rendering `statusDotColor(m.status_color)` while
`insufficient_data: true` sits unread in the same object.

### Why the other surfaces are not affected, which changes the shape of the problem

**BROWSER-VERIFIED and confirmed against the stored row.** Abstaining project-level modules are
**not present in `module_results` at all**. On the seeded distressed project:

```
module_results length                   : 47   (of 95 project-level modules)
entries carrying insufficient_data      : 0
entries with status_color == null       : 0
```

The abstention contract (`models.py:35`, `insufficient()`) returns `status_color: None`, and those
results never reach the stored row. So on every project-level surface there is no verdict to
mis-colour: a module that abstains **disappears from the list** rather than rendering Green.
Counting the rendered dots on both the research evidence screen (57 rows) and the operational
workspace detail tab (50 rows), **zero carry the `var(--status-nodata)` colour**, which is what a
null status would produce.

**So the answer to "does a fix that makes modules abstain achieve nothing" is: it would work on
every project-level surface, and it would not work on the portfolio snapshot.** The distinction is
not "which surfaces read the flag" — *none* of them read it — but **which code paths emit a colour
and a flag at the same time**. Only one does: `portfolio.py`, which always emits all five D1
results, and D1.3 sets `status_color: "Green"` beside `insufficient_data: true`.

### Every surface that renders a module verdict, and what it reads

| Surface | Reads | Insufficiency flag | Account types | Verified |
|---|---|---|---|---|
| `workspace.js:750`, portfolio panel (D1 snapshot) | `status_color`, `evidence_metric` | **not read** — and this is where D1.3 lands | both | BROWSER |
| `workspace.js:700`, project detail tab (module_results) | `status_color`, `evidence_metric` | not read; no abstentions present to mis-render | both | BROWSER |
| `decision-ui.js:373`, evidence screen (module_results) | `status_color`, `evidence_metric` | not read; no abstentions present | research (operational sees "no sequence assigned") | BROWSER |
| `decision-ui.js:333`, evidence screen (category_statuses) | `c.status` | n/a | research | BROWSER |
| `detail.js` signal web, ensemble, signal stack | `status_color` | not read | — | **unreachable**, section 1 |
| `export.js` | `project.history` | n/a | — | not reached; empty on server-computed projects (prior report) |

**One surface reads an insufficiency signal correctly**, and it is worth recording: the workspace
portfolio panel checks the **outer** `snapshot.insufficient_data` and prints the server's message
verbatim rather than a colour. The research participant's single-project portfolio showed
*"Portfolio too small for anomaly detection — need at least 3 projects with signal data"*, with no
dots. BROWSER-VERIFIED. So the panel does read the outer flag and does not read the per-module one.

### What a research participant sees from the D1 fabrications

**BROWSER-VERIFIED.** These are on the evidence screen, above the judgment form, before the
participant commits anything:

```
Neutrosophic Logic       | "Insufficient signal data"                          | AMBER
Interval Fuzzy Sets      | "Insufficient signal data"                          | AMBER
Z-numbers                | "Insufficient signal data"                          | AMBER
PLTS                     | "Insufficient signal data"                          | AMBER
Plithogenic Sets         | "Insufficient signal data"                          | AMBER
Audit Trail Completeness | "0% audit trail completeness, 0 events recorded,    | RED
                           no decision record yet"
Reporting Frequency      | "0 document upload(s) recorded, no documents        | YELLOW
                           uploaded yet"
```

Five Amber verdicts whose own evidence text says there was no signal data, a Red for zero events
on a platform that recorded the upload, and a Yellow saying no documents were uploaded on a
project whose document is listed by filename **fourteen rows further down the same screen**. This
is the D1 report's finding, seen by the person whose judgment is the study's dependent variable.
The colours here are fabricated rather than abstained, so they are unaffected by the "abstentions
disappear" mechanism above.

---

## 6. Incidental, recorded because it was on screen

**BROWSER-VERIFIED.** The research participant's portfolio list showed **all three projects**,
including the two belonging to the operational user, and the `Signals` / `Open →` controls for
each. The workspace panel below it correctly showed only the one project they are a member of.
The portfolio list is fed by the legacy sessionless facade (`list` / `listslim`), which
`test_features.py:274` records as *"a sessionless facade call is unaffected (pre-existing
posture)"* — so this is the known posture rather than a new hole, and the project detail route it
leads to renders nothing anyway. **I am flagging it, not claiming it is new, and I did not test
whether any evidence content is reachable that way.**

---

## What I could not establish

- **Whether the detail page was ever seen working since `062731b`.** I established it throws today
  and that the commit that broke it is a day old. Whether anyone opened it in between is not
  something the repository records.
- **Whether the admin route renders a decision card.** The admin nav is hidden for both seeded
  accounts and I did not sign in as the ResearchAdmin to check. `admin.js` and `admin-ops.js`
  contain no `renderDecisionCard` reference (SOURCE-ONLY), so I expect not, but I did not look at
  it in a browser.
- **Whether `research/deepdive.html` renders a decision card.** Nothing links to it and it is the
  one surface that deliberately computes in the browser. Not reached.
- **Whether the pre-lock disclosure of the Regret Minimization colour is covered by
  `test_decision_ui_t4`'s leak scan.** Its planted markers are prose; a colour is not prose. I did
  not run the fault injection that would settle it.
- **How the blank detail page behaves on a project with no stored result.** The ReferenceError is
  before any conditional that depends on the result, so I expect the same blank page, but I only
  measured projects that have one.
- **Anything about production.** Not inspected, not queried.

---

## Summary

| Question | Answer | Verified |
|---|---|---|
| Does a research participant see the browser-derived recommendation? | **No** | BROWSER |
| Does an operational user? | **No** | BROWSER |
| Is the decision card rendered anywhere? | **No.** One mount point has no element; the other is on a page that throws | BROWSER |
| Why? | `detail.js:894` references `populated`, deleted in `062731b`; `showPage`'s catch hides it | BROWSER + git |
| What is the disclosed recommendation in the sequence? | The frozen researcher-authored `DecisionSupportPackage`, printed verbatim from the server | BROWSER |
| Does any surface render a verdict without reading its insufficiency flag? | **Yes, one that matters**: the portfolio snapshot panel, D1.3 Green on "No history available", both account types | BROWSER |
| Would making modules abstain fix the display? | On project-level surfaces yes — abstentions are absent from `module_results` entirely. Not for the portfolio snapshot, where the colour and the flag are emitted together | BROWSER + stored row |
