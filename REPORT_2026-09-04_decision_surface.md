# Run 134 — Period Analysis Summary and Suggested Decision

Presentation and information architecture only. No module, threshold, weight, category rule,
project rule or computation was changed. No Python was touched.

- **Starting commit:** `6b5a543` (= `origin/main`, tree clean)
- **Branch:** `main`
- **`SIMULATION_VERSION`:** `sim-2026.09-v68` — **unchanged**, not read and not written by this run
- **Migration head:** `0033_recognition_matches.py` — **unchanged**, no migration
- **Nothing under `server/`** was modified. `git diff --stat -- server/` is empty.

---

## 1. The four establish-items

### Item 1 — which files render these two panels

**The briefing's guess was wrong, and the Run 131 trap was live.** Traced by registration, not by
name.

`detail.js:1082` registers the brief with its content built **inline** by `executiveBriefHtml`,
which lives in `detail.js`. That one is where its name suggests.

`detail.js:1083` registers the decision card as an **empty** `<section class="detail-decision">`.
The briefing named `assets/js/decision-ui.js` as "the strong candidate". **It is not the
populator.** The populator is `detail.js:1221`, which calls **`LinApp.renderDecisionCard`**,
defined at **`assets/js/app.js:1492`**. `decision-ui.js` says so itself, in a comment at line
1010 written by Run 97:

> "The operational Governance Decision card on the project detail page is
> `LinApp.renderDecisionCard`, a different function in a different file, which never saw any of
> this."

`decision-ui.js` is nonetheless load-bearing: `app.js` delegates the card's body to
`LinDecisionUI.renderBrief` (= `renderDecisionBrief`), and the content is composed **server-side**
by `server/app/decision_brief.py` and served as `row.decision_brief`. So the Suggested Decision
panel is **three** files, not one: `app.js` (shell, dispositions, audit wiring), `decision-ui.js`
(body layout), `decision_brief.py` (composition — not touched).

### Item 2 — can the three-condition limit be met without a new ranking rule? **Yes.**

`server/app/decision_brief.py:241` already sorts every adverse reading before serving it:

```python
rows.sort(key=lambda r: (by_severity.get(_band(r["band"]), 9),
                         str(r.get("category") or ""), str(r.get("module_id") or "")))
```

with `by_severity = {"red": 0, "amber": 1, "yellow": 2}`. A total, deterministic order over
`(severity, category, module id)` already exists in production and is already used. **Taking the
first three is a truncation of an existing order, not a new ranking rule**, and the order's stated
constraint — that a Red must never sit below Amber and Yellow observations — is exactly what this
sort already guarantees. No ranking was written. The full list stays in the drawer, and where rows
are hidden the count of hidden rows is printed.

### Item 3 — the disposition vocabulary. **I STOPPED. Nothing was changed.**

The briefing's account is **correct in every particular**, verified at
`server/app/research_decision.py:473-501`. The card's five dispositions are server-supplied
(`PROJECT_DECISION_DISPOSITIONS`), asserted to be a subset of the nine in `DISPOSITIONS`, served
via `documents.py:4133`, and rendered whole by `app.js`.

The order's four reviewer options **cannot** be mapped onto them without narrowing the audit
record: they would drop `no_action_within_current_authority` entirely and collapse the
`modify` / `reject` distinction, and "Request additional analysis or evidence" wants
`request_evidence`, which exists in `DISPOSITIONS` but is deliberately not among the card's five.

The code has already refused to settle this, in writing, and asks for a ruling:

> "Whether the card should offer them separately too is **NOT decided here**." … "`reject` is the
> closest existing value and it is **NOT identical** … It is reported for a ruling."

**What I did:** nothing to the vocabulary. The five arrive and the five are offered, with every
stored `code` and every served `label` untouched and unreordered. The only change is that the
select, the rationale and the record button are now grouped under a **Reviewer response** heading,
and the rationale is marked "required". Verified in the browser after the change:

```
'accept::Accept finding', 'modify::Modify finding', 'defer::Defer pending evidence',
'reject::Override finding',
'no_action_within_current_authority::Record no action within current authority'
```

**This is the order's own stop condition on item 3, and I stopped at it.**

### Item 4 — the Run 128 test: is any relocated text the only statement of something?

Applied to every element. Two **failed** the test and were therefore **not** moved:

- **`briefFlagsHtml`** is the only statement anywhere on this surface of the **Red-review
  high-disagreement advisory** and of the **liability period**. Neither is restated in the
  decision card or in any drawer.
- **`briefConsistencyHtml`** is the only statement of a **document that disagrees with itself**.
  It appears on no other surface.

Both stay above the fold, exactly where they stood. Everything else that moved is restated
elsewhere or is reachable in one click, and nothing was deleted.

---

## 2. What changed, file by file

### `assets/js/detail.js` — Period Analysis Summary
**Changed:** panel renamed `Executive Brief` → `Period Analysis Summary` (section registration,
panel eyebrow, `aria-label`). Added `periodAnalysisSummaryHtml` and four helpers, which **read and
print only**: posture from `decision_brief.posture` / `project_status`, confidence from
`information_completeness`, up to three conditions from the already-sorted
`decision_brief.adverse_readings.rows`, and one limitation from the server's own caveat or first
limitation. Added the `ebDrawer` helper. The four narrative blocks moved into an **All findings**
drawer; the rejection body's blocks moved into **How official posture was formed**, **All adverse
findings**, **Data coverage** and **Internal diagnostic**. The route text now names the renamed
destination and says "system finding" rather than "recommendation".

The reader-facing sentence *"The generated recommendation was rejected before it rendered, because
it did not meet the checks below"* — software behaviour, not the project — became: *"No generated
narrative is shown for this period. What the analysis holds is printed below instead of a summary
of it."* The validator's full reasoning, every failure row verbatim, moved into **Internal
diagnostic**. Nothing was deleted.

**Left alone:** every computation, `briefGate` and its three Run 70 checks, `briefEvidence`,
`briefKeySignals`, `scriptedBrief`, `parseBrief`, the flags block and the consistency block.

**A defect this run introduced and then caught before shipping:** the summary first printed
`project_status_label` after "Official posture:". On a real stored row that field reads
**"Cost Recovery Status"** — the *name of the kind* of status, served beside
`project_status_scope`. It is not a posture. The posture on that same row is `"Awaiting analysis"`.
Corrected to prefer `decision_brief.posture.status`, the identical field the decision card prints,
so the two surfaces cannot state different postures for one period.

### `assets/js/decision-ui.js` — the card body
**Changed:** `renderPosture` split so the weighted-vote band and its arithmetic move into a
`renderPostureFormation` helper; the posture itself and Run 106's withheld-posture sentence stay
above the fold. Added `dcDrawer` and `renderSuggestedDecision`. `renderDecisionBrief` now leads
with posture → suggested decision → decision question, then eight drawers.

**Left alone:** `renderForecast`, `renderDrivers`, `renderAdverse`, `renderEvidence`,
`renderLimitations`, `renderVoting`, `renderReviewer`, `renderAudit` — all called with the same
arguments, rendering the same fields. Only their position changed.

### `assets/js/app.js` — the card shell
**Changed:** eyebrow and heading → "Suggested decision"; disposition select, rationale and record
button grouped under a `Reviewer response` heading; rationale labelled "(required, min 20
characters)".

**Left alone:** `dispositionBlock` and its served list, `wireDecisionControls`, the
`projectdecisionrecord` write, the `projectdecisions` read-back, `buildAuditRecord`, both exports.

### `assets/css/radar.css`
**Changed:** one appended block. Every colour resolves through an existing token; no literal colour
was introduced. `.pas-band` and `.dc-band` are **neutral chips that print the band's word in the
ordinary text colour** — an unbanded reading prints whatever word the server sent and never
acquires a Green, Yellow, Amber or Red.

---

## 3. Proof by observation

Rendered in Chromium (headless shell 1194) through the **production route** — `LinDetail.render`
and `LinApp.renderDecisionCard` — against a **real stored row** pulled from `server/dev.db` and put
through the **real** `documents._result_view`. Nothing about the data was hand-written. Screenshots
before and after, both panels, dark and light.

**Every moved element is reachable.** With all 8 drawers opened by click, 17 of 17 markers present,
including the weighted-vote arithmetic, the renormalisation sentence, the fourth adverse reading,
the forecast figures, the full limitations list, `AUDIT RECORD`, both exports and the record button.

**The check was proven able to fail.** With the drawers left closed, 9 of the 17 markers flip to
MISS. The 8 that stay are precisely the ones deliberately kept above the fold.

**Two contrast defects were found by measurement and one was real.**
- `.pas-ident` rendered at **1.14:1** in dark — dark navy on near-black, invisible, and visible as
  such in the screenshot. Cause: `var(--heading)` is declared for the light palette and not
  redeclared in dark, so the fallback never fired. Fixed to `--text`; now 17.58:1 and legible in
  the re-shot screenshot.
- `.dc-suggested-text` measured 1.72:1 in light. **That figure was a measurement artifact**: the
  decision panel paints a gradient, so my background walk skipped it and found a dark ancestor.
  **Observation overrules it** — the light card is fully legible in the screenshot. This is the
  exact failure mode the order warned about, in reverse: a stylesheet-derived number was wrong
  and the rendered page was right.
- The remaining light-theme sub-4.5:1 figures are **pre-existing and site-wide**: `.eb-sec-head`
  3.96, `.dc-note` 3.46, `.eyebrow` 3.96, `.eb-route-note` 2.75. My drawer heads sit at 2.75,
  identical to `.eb-route-note`, i.e. the established house level for secondary headings. Not
  introduced here and not fixed here.

**No computed value moved.** Confirmed three ways: no file under `server/` is modified
(`git diff -- server/` empty); the served view JSON regenerated from the same database **after**
the changes is **byte-identical** to the one generated before; and every new browser function
reads served fields and prints them — none ranks, thresholds, bands, sums or rounds.

**The audit record still carries every field.** `buildAuditRecord`, the `projectdecisionrecord`
write, the `projectdecisions` read-back and both export buttons are untouched; the read-back line
still reports disposition, period, posture and timestamp. Run 107's disposition route was not
narrowed — the five dispositions are unchanged.

---

## 4. Things the order got wrong, and one it got right

**The Contingency Burn contradiction is not what the order describes.** The order states the card
renders Contingency Burn **Red at a burn of 1.5** while the boundary text says at or below 1.5 is
Amber. At `server/app/simulation/models_ext.py:871`:

```python
elif burn <= 1.5: color = "Amber"
else:             color = "Red"
```

and the boundary text served alongside it reads *"above 1.2 and at or below 1.5 is Amber; above 1.5
is Red."* **At exactly 1.5 the module emits Amber and the text says Amber. They agree.** There is no
self-contradiction at that value.

Two real things sit nearby and are **reported, not touched**:

1. **A display/band mismatch that would look exactly like the order's description.** The band is
   computed from the **unrounded** burn, while the message and `normalized_burn` print
   `round2(burn)`. A burn of 1.502 therefore **displays as "1.5" and bands Red**, against boundary
   text saying 1.5 is Amber. This is a genuine rounding-vs-banding seam and is very likely what was
   seen. It is the A1/A3 audit's subject, not this run's.
2. The **exhaustion arm** bands Red irrespective of the burn value; the boundary text does state
   that arm.

Also: the module's own docstring still says *"v3 reports both figures and asserts NO colour"*,
which **Run 101 superseded** when it re-added the ladder. The prose above the code is stale; the
code bands. Reported, not edited.

**Is the contradiction more or less visible now?** **Neither — it is not visible at all on this
surface, and its visibility is unchanged.** No A3.2 reading appears in the fixture, and nothing in
this run touches how a band or a boundary is rendered. If a project did carry an A3.2 Red, the
redesign would make it **slightly more prominent**: a Red sorts first, so it would appear among the
top three conditions on the first screen rather than partway down a long list. Its boundary text
remains in the same drawer as the rest of the evidence. I am flagging that as required, rather than
suppressing it.

**The order got the dispositions exactly right**, and the briefing's establish-item 3 was accurate
in full.

**`T6_HANDOFF.md` was read (top block only) and NOT updated.** Its newest entry is Run 89
(2026-08-30); HEAD is Run 133 (2026-09-04). It is stale by **44 runs**, and Runs 90 through 133 each
declined to append. Appending Run 134 alone would misrepresent a 44-run gap as a maintained file.
The file's own header says it carries no authority and that the code is true where they disagree.
**Reported for a ruling rather than resolved unilaterally.**

---

## 5. No check was committed

Following Runs 128 and 131. The verification here is a **rendered-page** measurement, and committing
it would drag a Playwright harness, a Chromium path and a database-derived fixture into the
repository. A source-reading substitute is the thing Run 121 warned against and Run 128 measured
failing. The harness was built in the scratchpad, used, proven able to fail, and deleted.
