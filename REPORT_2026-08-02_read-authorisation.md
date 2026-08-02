# Read authorisation on the legacy facade: what was readable, and what stays public

**1228 checks across 22 suites, 0 failures. `tests_render.html` 43/43, `tests.html` 51/51.**
Playwright driving the pre-installed Chromium; compositing proven before reading any DOM
(`visibilityState` "visible", **62–63 rAF frames per second**). No stored data was altered and
production was not inspected or queried.

**No overlap with the parallel geocoding session.** This change touches `main.py`, `facade.py`,
`research_membership.py`, `store.js` and four test files. `documents.py` and `geocode.py` are
untouched.

---

## 1. What was readable without a credential

Probed through `/exec` against a project owned by a signed-in PM **with membership rows**, on a
database carrying real extracted figures, stored snapshots and an audit row. Every one of these
answered `ok:true` with **no credential of any kind**:

| Action | Returned to an anonymous caller |
|---|---|
| `list` | **every project's full document** on the deployment — name, sector, status, `signals`, `signalInputs`, the complete event log |
| `listslim` | every project's `cpi`, `spi`, `docRiskScore`, `actualPctComplete`, status, `docCount` |
| `get` | one project's full document, including its event log |
| `gethistory` | that project's stored period snapshots |
| `listcorpus` | its corpus file listing |
| `listauditresults` | its audit-result rows |
| `listarchived` | every archived project's full document |
| `getportfoliohealth` | the portfolio-health snapshot for the whole deployment |

The leak was not theoretical: probing for marker strings, the anonymous `list` body carried the
victim project's name and event log, and `listslim` carried its `cpi`, `spi` and `docRiskScore`.

**Now:** all eight refuse with `{"ok":false,"error":"missing or malformed session token"}`,
verified over real HTTP against a running server, not only in a test.

---

## 2. What stays public, and why each one

**`health`, `ping`, `version` — and nothing else.**

Probed against a populated database: all three return build and capability information and **no
project data**. Version strings, whether an API key is present as a boolean, the advertised
endpoint list, a timestamp, the registered POST action names. Nothing derived from a project.

They stay public because a deployment has to be able to say it is alive before anyone signs in,
and `health` is the endpoint an operator and a monitor both reach for. `/healthz` and `/readyz` are
separate routes and are unaffected by any of this.

**They are named at their own site.** `PUBLIC_GET_ACTIONS` in `facade.py` is an explicit frozenset,
and `dispatch_get` authenticates anything not in it. A read added to `GET_ACTIONS` is therefore
**closed by default**, and opening it is a visible edit to that one line rather than an omission
somewhere else. That inversion is the point: the write side rotted precisely because a permissive
default let every new action inherit permission without anyone deciding it should.

### What I expected to find public and did not

**The sign-in page needs no project read.** I instrumented the browser and counted `/exec` GETs
before authentication: **zero**. `boot()` calls `LinAuth.init()`, which returns false without a
token and shows the login screen; `LinApp.init()` — which is what calls `loadSlim()` — runs only
after a session resolves. So closing these reads breaks nothing pre-session.

**The static mirror does not depend on them.** `config.js` records that the GitHub Pages copy
resolves `/exec` against `github.io` and degrades to the non-fatal "can't reach the store" state.
It could not read the facade before this change and cannot now; its behaviour is identical.

**The captured GET contract is not replayed against the server.** `p0-baseline/contracts/get/*.json`
are consumed by `seed_from_fixtures.py` and `import_from_drive.py`, which read the JSON **from
disk** to seed a database. No test issues an unauthenticated GET and compares it to a capture, so
no captured contract breaks. The response *shapes* are unchanged — only the requirement to
present a credential is new.

**Nothing broke silently.** The four suites that failed on the first run failed loudly, at their
own read helpers, and are updated in section 5.

---

## 3. The fix

**A read that can return project data requires a credential and membership, on the write guard's
terms.** `guard_project_read` in `research_membership.py` mirrors `guard_project_write`:

- **Authentication first, for every caller.** `settings is None` is a refusal, not a pass.
- **Then membership**, for the four reads that name one project (`get`, `gethistory`,
  `listcorpus`, `listauditresults`): the caller must be an **active member**.
- **Member, not PM.** An Observer exists in order to read; requiring PM here would break the role
  rather than protect anything. `require_member` has drawn that same line for the research read
  paths since B8.
- **A project that does not exist still returns its own "Not found"**, not an authorisation error.
  Replacing it would tell an attacker the difference between a project that is absent and one they
  simply cannot see.

**Collections are filtered, not refused.** `list`, `listslim` and `listarchived` return the rows
the caller may see and omit the rest. Refusing the whole call because one row belongs to someone
else would make a portfolio unusable for anyone who is a member of some projects and not others,
which is every real user.

Verified in the live application, both directions:

```
PM-R1  (PM of PRJ-EVID)      list -> ['PRJ-EVID']            get PRJ-EVID -> ok
OPS-1  (not a member)        list -> ['PRJ-0N4J…','PRJ-NMBH…']  get PRJ-EVID -> refused
```

Before this change the operational user's portfolio showed all three projects including the
research participant's. It now shows two. That cross-user leak is closed and visible in the real
application, not only in a test.

### The credential travels in a header

`Authorization: Bearer <token>`, with `X-Session-Token` accepted as an alternative. A token in a
URL is logged by every intermediary that logs URLs — the reverse proxy, the access log, the
browser's history, a `Referer` on any outbound link — so it is the wrong place for a credential
that grants read access to project data.

**The constraint that argued against a header has expired.** `store.js`'s `apiGet` carried the
comment "no custom headers → no preflight", which came from Apps Script: a custom header makes a
cross-origin request non-simple and triggers a preflight that backend could not answer. At T1 the
app moved to the **same origin** as `/exec` — `config.js` says so in its own header — and a
same-origin request issues no preflight whatever headers it carries.

**`session_token` in the query string is still accepted, and is confined to one caller.**
`/documents/{id}/content` is loaded as an iframe `src` by the document viewer
(`workspace.js:624`); a browser navigation carries no custom headers, so that route has always
taken the token as a parameter. Rejecting the parameter at `/exec` would not improve that route
and would break any caller mid-session. **It is a fallback, not the mechanism**, and the reasoning
including the logging hazard is written at `_session_token_from` so it is not re-adopted as a
general pattern by the next person who needs a token somewhere.

Verified in the browser: after sign-in, **every** `/exec` GET carried the `Authorization` header
and **no token appeared in any URL**.

### A gap closed as a side effect

`gate_action` deliberately leaves sessionless callers alone, because an anonymous caller has no
feature flags to apply. That meant an anonymous GET of `getportfoliohealth` **bypassed the feature
gate** that a signed-in user with the flag off is held to. The read guard sits one layer up, so
dropping the credential is no longer a way around the flag. The previous report named this as
authorisation gap 2; it is now closed.

---

## 4. The two gaps to report, not fix

### An unmembered project is readable and writable by any authenticated caller

**Current state, measured on the running server.** A project with no membership rows — every
project imported from the Apps Script era, and any created through the legacy `create` action —
is fully readable and fully writable by any signed-in user:

```
OPS-1 (unrelated) GET  PRJ-LEGACY-NOMEM  -> ok:true, full document
OPS-1 (unrelated) POST archive           -> ok:true, archived
```

This is the pre-B8 legacy shape, unchanged, and it is now the **only** way one authenticated user
reaches another's project. It is deliberately preserved on the read side for exactly the reason it
is preserved on the write side.

**What closing it would cost.** Every such project would become invisible and unwritable to
everyone at once, including its real owner, until membership rows exist. In the local dev store
that is 1 of 4 projects; **in production the number is unknown, because production was not
inspected**, and the imported Apps Script projects are exactly the population with no membership.
So closing it is a two-step change — backfill membership from whatever record establishes
ownership, then flip the guard — and the backfill needs a decision about what "owner" means for a
project imported from a Drive folder. It is yours.

### `refuse_unless_pm_for_assignment` has the same unmembered arm

**Current state.** The PM-only guard on the research decision flow (`prejudgment`, `reveal`,
`decision`, `advance`) returns allow when the assignment's project has no membership rows.
Unchanged by this session.

**What closing it would cost, and why it is smaller.** Those actions already require a valid
session upstream, so the exposure is an authenticated participant acting on an unmembered
project — not an anonymous one. Closing it has the same backfill dependency as the gap above and
should be decided with it, since both hinge on the same missing membership rows.

**Neither was changed.**

---

## 5. What changed in the suites, and why

Four suites read the facade unauthenticated for fixture setup and failed loudly:

- **`test_writes_a1b`, `test_workspace_t3t5`** — their `get()` helpers now send the session in an
  `Authorization` header, which also means the header path is exercised throughout rather than in
  one place. `test_writes_a1b` additionally gained five checks asserting the new read rules: a
  non-member is refused a read of a membered project, the refusal carries no project payload, the
  project's own PM still reads it, the membered project is filtered out of a non-member's list,
  and the caller's own projects stay in it.
- **`test_doc_risk_range`** — two direct `client.get` calls now send the header.
- **`test_features`** — one check asserted the defect (*"a sessionless facade call is unaffected
  (pre-existing posture)"*). It now asserts the refusal and that no snapshot payload comes with
  it, and gained five checks covering the credential carrier itself: Bearer works, `X-Session-Token`
  works, the query-string fallback works, a bad token in a Bearer header is refused rather than
  ignored, and a token sent **without** the `Bearer` scheme is not accepted by accident.

**One pre-existing check moved rather than weakened.** `test_writes_a1b` read a project's document
*after* adding a PM to it; that read is now correctly refused, so the document is captured before
the member is added. The behaviour it was there to test — a non-PM write being refused — is
unchanged and still asserted.

---

## 6. Verification

| Check | Result |
|---|---|
| Server suite, freshly migrated DB per suite | **1228 across 22 suites, 0 failures** (1216 → 1228) |
| `tests_render.html` | **43/43** |
| `tests.html` | **51/51** |
| Compositing proven before any DOM read | visible, 62–63 rAF/s |
| Anonymous GET refused, real HTTP | all eight project-data actions |
| `health` / `ping` / `version` still public, real HTTP | all three |
| Signed-in read works end to end in the application | both account types |
| Every GET carried the header; no token in any URL | verified by instrumenting the browser |

**Fault injection. Every fault was confirmed to have applied before its result was read** — the
harness prints `fault applied` only when the anchor matched, and prints a loud
`ANCHOR DID NOT MATCH` otherwise. That check exists because an injection that silently fails to
apply reported a false clean last session.

| Fault restored | Suite | Result |
|---|---|---|
| The read gate removed entirely (the shipped state) | `test_writes_a1b` | **89/92**, 3 red |
| Every GET treated as public | `test_features` | **41/43**, 2 red |
| Project-scoped reads skip the membership check | `test_writes_a1b` | **90/92**, 2 red |
| Collections not filtered | `test_writes_a1b` | **91/92**, 1 red |
| The `Authorization` header ignored | `test_features` | **48/49**, 1 red |
| The resolved token not handed to the guards | `test_features` | **47/49**, 2 red |
| The `Bearer` scheme not required | `test_features` | **48/49**, 1 red |

**The crash-instead-of-fail mode recurred and was corrected.** Faults 5 and 6 were first aimed at
`test_writes_a1b`, whose fixture setup reads the facade in dozens of places: with the header
broken every read failed, the suite died on an early `["project"]`, and it printed **no RESULT
line**. That is the failure mode recorded from the previous two sessions, and a runner reading
`RESULT: n/n` would have seen nothing. The carrier checks now live in `test_features`, whose reads
are not load-bearing for its fixtures and whose assertions use `.get(...)`, so a broken carrier
produces a clean red instead of a crash.

**A seed-script artifact nearly produced a false positive.** The research participant's browser
check first showed **0 projects**, which looked like the membership filter over-refusing. It was
not: my seeding script created that project through the sessionless `create` action, which the
*previous* session's write fix already refuses, so the project had never existed. The seed now
authenticates, and the corrected run shows the participant reading their own project and being
refused someone else's. Worth recording because "the legitimate user sees nothing" is exactly the
shape a real regression would take.

---

## 7. What I could not establish

- **Whether the exposure was exercised in production.** Production was not inspected. Reads leave
  no trace: the facade writes nothing to `audit_events`, and a GET modifies nothing, so an
  anonymous read is invisible after the fact — **less detectable than the write exposure**, where
  the project's own event log at least records that something happened.
- **How many production projects have no membership rows**, which is what the backfill in section 4
  would have to cover. Locally it is 1 of 4; production was not queried.
- **Whether any non-browser client reads the facade.** I found none in the repository, and the
  header is the only new requirement, so any such client would break loudly at its first read
  rather than silently.
- **Whether `getportfoliohealth` should be membership-scoped.** It is now authenticated, but it is
  a cross-project aggregate with no owning project, so there is nothing to scope it against. An
  authenticated user therefore sees an aggregate covering projects they are not a member of. The
  feature flag still gates it per account. Narrowing it further would mean recomputing the
  aggregate per caller, which is a design decision rather than a fix.
