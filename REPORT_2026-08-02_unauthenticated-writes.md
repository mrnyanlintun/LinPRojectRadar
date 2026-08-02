# Unauthenticated writes on the legacy facade: what was reachable, and what now is not

**1216 checks across 22 suites, 0 failures. `tests_render.html` 43/43, `tests.html` 51/51.**
Playwright driving the pre-installed Chromium; compositing proven before reading any DOM
(`visibilityState` "visible", **63 rAF frames per second**). No stored data was altered and
production was not inspected or queried.

---

## 1. What was reachable without authentication

Measured through `/exec` against a project owned by a signed-in PM **with membership rows** — the
strongest case the guard was supposed to protect. Every one of these was accepted with **no
session token at all**:

| Action | Accepted | What it did to another user's project |
|---|---|---|
| `save` | **yes** | replaced the whole project document; renamed it |
| `resetsignals` | **yes** | cleared `signals`, `signalInputs`, `simulationSignals` |
| `archive` | **yes** | archived it, removing it from every list |
| `restore` | **yes** | un-archived it |
| `setprojectnumber` | **yes** | **renamed the project id**; the old id stopped resolving |
| `overwritesignal` | **yes** | wrote `cpi = 0.01`, and an invented field name `totally_made_up` |
| `savehistory` | **yes** | inserted a fabricated period snapshot |
| `saveauditresult` | **yes** | inserted an audit-result row |
| `create` | **yes** | created projects at will |
| `saveportfoliohealth` | **yes** | replaced the portfolio-health snapshot for everyone |

`overwritesignal` needs `signalInputs` to be non-empty, which an anonymous caller can arrange with
an anonymous `save` first. That chain was measured: seed, then overwrite, then invent a field.

**Reads: every GET is unauthenticated and returns other users' data.** `list`, `listslim`,
`listarchived`, `get`, `gethistory`, `listcorpus`, `listauditresults`, `getportfoliohealth`,
`health`, `ping` — all `ok:true`, all returning full project documents including
`signalInputs`, the event log and stored figures. **This is unchanged and is reported, not fixed;
see section 5.**

**What was NOT reachable, and this is the boundary that held.** Every research, document,
workspace and admin action refuses without a token. Probed unauthenticated:
`projectcreate`, `projectupload`, `projectcompute`, `projectresults`, `adminrecompute`,
`workspaceprojects`, `researchwhoami`, `adminparticipantcreate`, `adminexportcreate`,
`researchprejudgment`, `adminmemberadd` — all eleven refused with "missing or malformed session
token". **The research record, the decision sequence, the export and the computed results were
never exposed by this.** What was exposed is the legacy facade's view of a project: its document,
its legacy signal blob and its event log.

---

## 2. Why the guard allowed it, and whether the reason has expired

The reason is on the record. `guard_project_write` was introduced by `486487c`, "B8: project
membership, observer role, and account separation" (2026-07-31), whose commit message says:

> Projects with no membership rows behave exactly as before, so nothing changes for pre-B8 flows.

and whose docstring said:

> Sessionless facade calls (the legacy frontend and the A1b contract tests) are unchanged — B8
> adds no authentication requirement to the facade, it adds authorisation for authenticated
> callers.

So B8 layered *authorisation* onto a facade that had never had *authentication*, and deliberately
left the sessionless path open so it would not break two things: the legacy frontend, and the A1b
contract harness.

**The frontend reason was real and has now expired.** `assets/js/store.js`'s `apiPost` and
`postWithTimeout` sent no token, so every write the application itself made was unauthenticated —
which is exactly why the hole could not simply be closed at the time. But the browser was already
holding a session: `LinAuth.getToken()` returns it, and `workspace.js` and `decision-ui.js` have
always attached it to their own calls. `store.js` was the one path that did not. **This is not a
dependency on unauthenticated writes; it is a client that failed to present a credential it
already had.** Fixed in this change.

**The A1b harness reason was never a product dependency**, only a test one. Those suites now sign
in; see section 6.

**Nothing else depends on unauthenticated writes.** I checked for other sessionless writers: the
only POST paths in the application are `store.js`'s two, and both now attach the session. The
GitHub Pages static mirror named in `config.js` resolves `/exec` against `github.io` and already
degrades to the "cannot reach the store" state, so it neither wrote before nor writes now.

---

## 3. The fix

**Fail closed, at the guard, for the whole POST surface.**

- **No token is a refusal**, not an allow. `if not payload.get("session_token"): return err(...)`.
- **`settings is None` is a refusal.** A build that cannot verify a session cannot authenticate
  anyone; the old code treated that as permission.
- **The guard now covers every POST action**, `PROJECT_WRITE_ACTIONS ∪ POST_ACTIONS`, rather than
  a hand-maintained subset. The two lists had drifted: `create` and `saveportfoliohealth` were in
  `POST_ACTIONS` and **not** in `PROJECT_WRITE_ACTIONS`, so they reached no guard at all. A write
  added to either list is now authenticated by default.
- **An action that genuinely needs to be public must say so at its own site.** `PUBLIC_WRITE_ACTIONS`
  is a named, deliberately empty allowlist. Nothing inherits permission from a guard waving
  through what it does not recognise.
- **`store.js` attaches the session it already holds** to every `/exec` POST, via one `withSession`
  helper used by both post paths. An explicit `session_token` in a payload still wins, so the
  research surfaces that build their own payloads are untouched.

### Two further fail-opens found inside the same guard, both fixed

**`resolve_caller` ran AFTER the membership check.** On a project with no membership rows the guard
returned allow before ever examining the token, so a **forged or expired session** was as good as a
valid one. Authentication now happens first, for every caller, whatever the project is.

**The PM rule had never applied to `save`.** Every action puts its project id at `payload["id"]`;
`save` puts it at `payload["project"]["id"]`. The guard read only the top level, so `save` resolved
no project, fell into the "no membership rows" arm and was allowed — on the single most powerful
write on the facade, the one that replaces the entire document. Measured before the fix: an
authenticated non-PM renamed a project whose PM was someone else. **The old test asserted this
outcome as correct** ("sessionless save still works on a membered project"), which is why nothing
caught it.

### Verified end to end against a running server

```
POST /exec  (no token, real HTTP, against a signed-in user's project)
  resetsignals         {"ok":false,"error":"not authorized: sign in to make this change"}
  archive              {"ok":false,"error":"not authorized: sign in to make this change"}
  setprojectnumber     {"ok":false,"error":"not authorized: sign in to make this change"}
  create               {"ok":false,"error":"not authorized: sign in to make this change"}
  saveportfoliohealth  {"ok":false,"error":"not authorized: sign in to make this change"}
  overwritesignal      {"ok":false,"error":"not authorized: sign in to make this change"}
```

And the real application still works: driven in a browser, signed in as an operational user,
`LinStore.saveProject` renamed a project successfully, the POST carried a session token, no error
banner, no page errors.

---

## 4. The same fail-open shape elsewhere

Swept every guard for "permits when the thing it checks is missing".

| Site | Shape | Verdict |
|---|---|---|
| `guard_project_write` — no token | allowed | **fixed** |
| `guard_project_write` — `settings is None` | allowed | **fixed** |
| `guard_project_write` — `resolve_caller` after the membership check | forged token allowed | **fixed** |
| `guard_project_write` — nested `save` id | never resolved a project | **fixed** |
| `guard_project_write` — project has no membership rows | allowed, now only for an **authenticated** caller | **remaining gap, reported** |
| `features.gate_action` — no token | returns None (no flags to apply) | **remaining gap, reported** |
| `refuse_unless_pm_for_assignment` — no membership rows | allowed | **remaining gap, reported**; token already required upstream |
| `research_consent.enforce_consent` — unresolvable participant | `has_active_consent(None)` returns **False**, so it raises | **fails closed, correct** |

**The three remaining gaps are authorisation, not authentication, and each needs its own decision:**

1. **A project with no membership rows is writable by any authenticated caller.** That is the
   pre-B8 legacy shape. Every project imported from the Apps Script era has no membership rows, so
   closing this locks them all out of the interface at once. It needs a membership backfill
   decision first.
2. **`gate_action` leaves sessionless callers alone.** It is a feature-flag gate and an anonymous
   caller has no flags, so this was harmless while writes were the concern. It is not harmless for
   **reads**: `getportfoliohealth` is a gated action, so an anonymous caller can read it while a
   signed-in user with the flag off cannot. Section 5.
3. **`refuse_unless_pm_for_assignment`** has the same no-membership-rows arm, on the research
   decision flow. Those actions already require a token upstream, so the exposure is an
   authenticated participant acting on an unmembered project, not an anonymous one.

---

## 5. Reads are still open, and I did not change them

Every GET on the facade returns any project's full document to anyone. I did not fix it, because
the fix is not the same shape as this one and would change three things at once:

- `store.js`'s reads are query-string GETs, so authenticating them means putting a session token in
  a URL — which lands in server logs and referrers. The application already does this for document
  content, so there is precedent, but it is a decision rather than a default.
- `list` / `listslim` / `get` are the legacy contract's captured GET fixtures. Requiring a session
  changes the contract those captures define.
- The GitHub Pages static mirror reads the same endpoints.

**What an anonymous reader can currently see:** project name, sector, status, `signalInputs`
(cpi, spi, bac, docRiskScore and the rest), the event log, stored period snapshots, audit-result
listings, and the portfolio-health snapshot. **Not** computed results, documents, decisions or
anything in the research schema — those are behind `projectresults` / `projectuploadstatus`, which
require a token.

This is the largest thing still open and it is yours to decide.

---

## 6. Reported, not fixed, as instructed

**`w_saveportfoliohealth` still deletes.** It removes every prior portfolio-health snapshot before
inserting the new one, and remains the only `session.delete` in the application. Verified again:
two saves leave one row. Its comment records the reason — the live model kept a single
`portfolio_health.json` at the Drive root. **It is no longer reachable unauthenticated**: it was
outside `PROJECT_WRITE_ACTIONS` entirely and is now covered by the widened guard. Unchanged
otherwise.

**`w_overwritesignal` still validates almost nothing.** It accepts an arbitrary `signalInputs`
field name and an arbitrary value. Measured: `cpi` set to `0.01`, and a field called
`totally_made_up` set to the string `"anything"`, both stored. The single exception is
`docRiskScore`, range-checked by T18's fourth entry point — and that guard fired correctly even
for the anonymous caller, refusing `85`. **It is no longer reachable unauthenticated**, and on a
membered project it is now PM-only. The validation gap is unchanged and still needs a per-field
contract decided before anything is written.

---

## 7. The decided item: `signals_extracted` on upload

Written, not backdated. One event per **contributing** document, stamped with the server clock at
the moment of upload, carrying `docType`, `fileName`, `period` and `wasCached`.

**C1.4 Audit Trail Completeness moves from Amber 50% to Yellow 100%**, which is the decided
outcome: it requires `project_created` and `signals_extracted`, and only the first existed. Green
needs a third entry and is left alone, since whether compute events should be written is a
separate decision.

**A qualification I established while building it, and it matters.** The event counts toward C1.4
only when the period's cutoff is on or after the upload date. Measured on a genuinely back-dated
document — a June report uploaded in August — the cutoff is 2026-06-30, `_events_as_of` truncates
everything stamped later, and **C1.4 reports Red, 0%, 0 events, both before and after this
change**: the new event is truncated exactly as `project_created` already was. So the improvement
lands on projects whose cutoff is the wall clock (the D3 fallback, when no document date parses)
and not on projects with real past document dates. Backdating the event would make it count and
would record an upload as having happened on a day it did not — falsifying the trail to improve
the score of the module that measures the trail. The understatement is the honest outcome and it
is left standing. The root cause is the cutoff rule, which is still your open judgement call
from D1.

**One test was strengthened as a side effect.** `test_d1_module_inputs` asserted event-log
truncation against a hardcoded date while its fixture had no parseable `document_date`, so the
cutoff was silently the wall clock and the assertion passed by coincidence. The fixture now
supplies real `document_date` values and the checks compare against each period's **own stored
cutoff**, so the suite exercises genuine truncation. 100/100.

**`test_documents_b7b` Guarantee 1 was re-scoped, not weakened.** It compared the whole
`signal_inputs` blob across two projects sharing one cached document. Since D1 that blob contains
`events`, `spiHistory` and `cpiHistory`, which belong to the project rather than the file — and the
two projects genuinely differ, because one upload was a cache hit and the extraction event records
which. The comparison now excludes those three keys **and additionally asserts that the difference
is confined to them**, so a divergence in any extracted field still fails. That is stronger than
what it replaced.

---

## 8. Verification

| Check | Result |
|---|---|
| Server suite, freshly migrated DB per suite | **1216 across 22 suites, 0 failures** (1190 → 1216) |
| `tests_render.html` | **43/43** |
| `tests.html` | **51/51** |
| Compositing proven before any DOM read | visible, 63 rAF/s |
| Unauthenticated writes refused, real HTTP | all ten actions |
| The signed-in application still writes | verified in a browser, token present on the POST |

**Fault injection.** `test_writes_a1b` is 87 checks, was 70.

| Fault restored | Result |
|---|---|
| The shipped fail-open (no token → allow) | **73/87**, 14 red |
| Guard reads only the top-level id (`save` loses its PM rule) | **85/87**, 2 red |
| `resolve_caller` moved back below the membership check | **86/87**, 1 red |
| Dispatch guards only `PROJECT_WRITE_ACTIONS` | **84/87**, 3 red |
| Upload writes no `signals_extracted` | `test_documents_b7b` **70/73**, 3 red |
| One event per request instead of per document | **73/74**, 1 red |
| Event backdated to the document's date | **72/73**, 1 red |
| A non-contributing document also logs an event | **70/73**, 3 red |

**Two of my own checks were vacuous and injection found both — the seventh session running.**

1. The anonymous-write checks **crashed instead of failing**: a successful anonymous
   `setprojectnumber` moved the target project out from under every later probe, and the read-back
   did `["project"]` on a missing key. The suite died and printed **no RESULT line**, which reads
   as clean — the exact failure mode recorded from last session. The rename now has its own
   throwaway target so it cannot disturb the others, and every read-back uses `.get(...) or {}` so
   a vanished project makes the check fail rather than raise.
2. The "one event per contributing document, not per request" check **could not distinguish the
   two**, because every upload in that fixture carried a single document. A fault that logged only
   the first document passed. The suite now performs one upload request carrying **two**
   contributing documents and asserts the count grows by two.

I also caught an injection-harness bug rather than a test bug: my first attempt at the
`resolve_caller` ordering fault silently failed to apply, so it reported a false clean. It is
listed above only after re-running with an anchor that matched.

---

## 9. Was the deployed site exposed the same way?

**I could not establish it directly, and I did not try: production was not inspected or queried.**

What I can say with confidence, and what I cannot:

- **The code that was deployed is the code I measured.** The guard, `store.js`, and the dispatch
  path are the same files on `main` that Render builds from, and `main` had not moved. There is no
  environment switch, feature flag or setting that changes the guard's behaviour between local and
  production — the only input it reads is `settings`, and a *missing* `settings` made it **more**
  permissive, not less.
- **The exposure needs no credential and no special network position.** Any client that can reach
  the deployment's `/exec` can issue these POSTs, so being deployed behind Render's public URL is
  sufficient.
- **What I cannot establish is whether anyone did it.** The legacy facade writes nothing to
  `audit_events`, so an anonymous write leaves no research-audit trace. The project's own event log
  does record `signals_reset`, `project_archived`, `project_restored`,
  `project_number_changed` and `signal_overwritten` entries with a server timestamp, so a write
  that happened is visible in the document even though the actor is not. **A query you could run on
  production:** look for those event types on projects whose owners did not perform them, and for
  `signalInputs` fields whose names are not in the extraction vocabulary. I have not run it and
  will not.
- **Whether any production data was altered is therefore unknown.** No stored data was touched by
  this session.

---

## What I could not establish

- **Whether the exposure was exercised in production.** Above.
- **Whether reads should be authenticated**, which is the largest remaining item and changes the
  legacy GET contract.
- **Whether unmembered legacy projects should stay writable by any authenticated caller.** It
  needs a membership backfill decision first.
- **Whether `w_overwritesignal`'s field vocabulary should be closed**, which needs a per-field
  contract, and `w_saveportfoliohealth`'s single-snapshot model, which is a research-record
  question. Both reported here, neither changed.
