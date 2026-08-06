# A project with 25 uploaded documents reads Awaiting analysis

**Date:** 2026-08-05
**Branch:** `claude/project-not-computed-s5s90m` (merged to `main`, PR #220, merge commit `80330d8`)
**Model:** Sonnet

**Verification:** server suite **41 suites, 2269/2269** (fresh SQLite DB per file; nothing under `server/app/simulation/` touched), `tests.html` **51/51**, `tests_render.html` **157/158** (new group 17, 4 checks, all green; the 1 red is the pre-existing auth-gated "production read path" check, red on `origin/main` too). Fault injected on the new check, confirmed detected, reverted.

---

## THE CAUSE, established by reproduction, not a guess

**Compute is a fully separate, manually-triggered server action, and across the entire client it is called from exactly one control.**

`a_projectupload` in `server/app/documents.py` (read in full) never calls compute. It extracts documents, files them, and logs a `signals_extracted` event per document. That is the whole of what upload does.

`projectcompute` is called from precisely one place in the client: the **"Run analysis for this period" button on the Workspace page's period-upload panel** (`assets/js/workspace.js:396`, wired in `index.html:675`). Confirmed independently: grepping every `assets/js/*.js` file and `index.html` for `projectcompute` returns exactly one call site.

**The project detail page's own upload panel (`signals.js`) and the Files tab (`files.js`) extract documents but have no compute control at all.** A project manager uploading through either of those paths — which is the natural place to upload documents to a specific project — gets successful extractions forever and no computed result. That is exactly the `WRAA-24-017-C` shape: 25 documents, 25 successful extractions, no compute ever invoked, because the path used to upload them has no button that would invoke it.

### Reproduced live

No `WRAA-24-017-C` fixture existed in this repository, so the shape was rebuilt from the real `a_projectupload` / `a_projectcompute` actions against a fresh SQLite database: a construction project, 25 documents uploaded and extracted (25 of 25 contributing). With compute never called, `projectuploadstatus` reports `computed: false` and `projectresults` refuses with "run projectcompute first." **Calling `projectcompute` explicitly on the same project and documents succeeds immediately with a real status.** This proves the cause is a missing manual step, not a guard, not sector-specific, and not a data problem.

### The three other candidates, ruled out with evidence

- **Compute failing silently:** ruled out. Compute was never invoked at all on this reproduction — there was no failure to observe, and calling it explicitly succeeded on the first attempt.
- **Compute refusing for an unsurfaced reason** (guard, missing field, out-of-contract value, underivable period): ruled out. The explicit call succeeded immediately with the same 25 documents that had already been extracted; nothing needed to change for it to work.
- **Something construction-specific**, since the two projects that computed were a design project and a training run: ruled out. The reproduction used a construction project through the identical code path and computed successfully once the action was actually called. Sector plays no role.
- **`window.confirm` gating the trigger** (this container's `window.confirm` returns false, and that has bitten this platform before — see the map/globe zoom investigation): **ruled out directly.** The compute button's click handler and its full call chain were read; there is no `confirm()` call anywhere in it. This is a real dead end this time, not the recurring one.

---

## THE FIX — the state is honest, the badge did not change to look better

`assets/js/app.js`'s `awaitingHtml()`, which feeds both the Signal Ledger and the Governance Decision card, now checks `hasUploadedDocuments(p)`:

```javascript
function hasUploadedDocuments(p) {
  const evs = /* the project's event log */;
  return evs.some((e) => e && (e.type || e.event || e.kind) === "signals_extracted");
}
```

It renders two distinct states:
- **Documents uploaded, computation not yet run** — when `signals_extracted` events exist but no computed result does.
- **Awaiting analysis** — unchanged, for a project with genuinely nothing uploaded.

**No project was made to appear computed when it is not.** Both states are non-computed states; the fix is that a reader can now tell which one they are looking at, which is what the task required.

---

## WHAT WAS LEFT FOR THE OWNER, DELIBERATELY NOT FIXED

- **The project detail page's upload panel and the Files tab still have no compute control.** This task made the resulting state honest rather than adding a trigger there, because adding a second compute entry point (and deciding what period it targets, whether it should auto-run, and how it interacts with the Workspace page's own trigger) is a product decision, not a display fix.
- **A stale docstring in `server/app/documents.py`** describes upload as running "on upload completion," which is no longer true. Left uncorrected as an internal comment — out of scope for a copy/naming task.

---

## VERIFICATION

Real headless Chromium drove the real application: uploaded documents to a project, observed that computation did not follow, read back the distinct new state, then triggered compute explicitly through the Workspace button and confirmed the project computes correctly.

`tests_render.html` group 17 (new, 4 checks) asserts the two states render distinctly and that a genuinely empty project still reads Awaiting analysis.

**Fault proven:** `hasUploadedDocuments` forced to return `false` unconditionally. FAIL count went from 1 to 4 (the new checks correctly detected the regression), reverted to green.

**The working path was confirmed not broken:** the two projects that do compute (a design project and a training run) were re-checked after the change and still compute and render correctly.

---

## FILES CHANGED

`assets/js/app.js`, `tests_render.html`, `T6_HANDOFF.md`, this report. No server file was modified. Nothing under `server/app/simulation/` was touched. No module id or number appears in the new text; no em dashes.
