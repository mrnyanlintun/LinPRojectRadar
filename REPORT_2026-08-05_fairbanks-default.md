# 2026-08-05 — Fairbanks becomes the default theme

A same-day session (`4e719ea`, already on `main` when this one started) had done most of this:
the default flip, the research-pin decoupling, and the admin pill's contrast fix. This session
found two things it missed — one a real leak, one a real bug affecting every research
participant's first screen — fixed both, corrected the unmeasured-token inventory, and wrote the
report that session's own note says was never filed.

**Server 39 suites, 2196/2196. `tests_render.html` 86/86. `tests.html` 51/51.** Nine faults
injected (one against `test_extraction_prompt.py`'s neighbourhood not required here — see the
fault table below for the eight specific to this task), all detected, all reverted
byte-identical, baseline re-measured after each. No migration. `server/app/simulation/`
untouched.

---

## 1. LEAD: contrast ratios measured, and every text token still unmeasured

### 1.1 The admin pill, measured live in a browser, transitions suppressed

Computed style, not the stylesheet, read from a real signed-in operational admin account on the
Administration page:

| Pill | Background | Ink | Ratio (computed) | Ratio (independent Python recompute) |
|---|---|---|---|---|
| Active (`.admin-pill-on`) | `rgb(215, 240, 224)` = `#d7f0e0` | `rgb(10, 64, 32)` = `#0a4020` | — | **9.86** |
| Archived (`.admin-pill-off`) | `rgb(251, 220, 219)` = `#fbdcdb` | `rgb(138, 14, 22)` = `#8a0e16` | — | **7.59** |

Both at 11px, both against `body[data-theme="plain"]`. Both figures match the `4e719ea` commit
message's claim exactly; this session's contribution is having actually read them from the DOM
(the archived pill required creating a real archived participant first — none existed) rather
than trusting the CSS-regex suite alone. Both clear AA (4.5) with room to spare; the failure this
replaces was **3.71**, below AA, on 11px text — confirmed by fault injection (T5, section 5) that
reverting to the old translucent-fill rule turns the check red.

### 1.2 Every text token the automated check does not measure — corrected, not just re-quoted

The prior session's list (`--eyebrow`, `--gold-text`, `--scope-label`, `--brand-bronze`,
`--brand-verdigris`, `--sector-design`, `--sector-construction`, `--sector-hybrid`, `--ink-dim`)
was checked against every `color: var(--x)` usage in `radar.css`, not re-quoted. Two findings:

**It missed one.** `--accent` colours real text in at least twelve places (headings, dropzone
labels, flow-diagram node labels) and was not in the list.

**Four of its nine are not live text colours at all.** `--sector-design`, `--sector-construction`,
`--sector-hybrid` and `--scope-label` are declared in the plain block and **have zero `color:`
consumers anywhere in `radar.css` or the frontend JS** — confirmed by exhaustive search, not
assumed from the name. They render nothing today. `--status-ink-complete/green/yellow/amber/red`
are the same situation and were not in the prior list at all.

The corrected inventory, split by whether a token actually paints text on the page today:

**Live** (unmeasured, but real — ratios shown for completeness, all clear AA today):

| Token | Value | Surface | Page | Consumers in `radar.css` |
|---|---|---|---|---|
| `--eyebrow` | `#545b66` | 6.85 | 6.34 | 8 |
| `--gold-text` | `#545b66` | 6.85 | 6.34 | 2 |
| `--brand-bronze` | `#1a1d23` | 16.88 | 15.61 | 1 |
| `--brand-verdigris` | `#0b6bcb` | 5.28 | 4.88 | 1 |
| `--ink-dim` | `#545b66` | 6.85 | 6.34 | 12 |
| `--accent` | `#0b6bcb` | 5.28 | 4.88 | **12 — missed by the prior pass** |

**Declared, never consumed** (not a live contrast risk today; flagged so a future rule that
starts using one does not silently skip this check):

| Token | Value | Consumers |
|---|---|---|
| `--sector-design` | `#0b6bcb` | 0 |
| `--sector-construction` | `#545b66` | 0 |
| `--sector-hybrid` | `#6f5200` | 0 |
| `--scope-label` | `#545b66` | 0 |
| `--status-ink-complete/green/yellow/amber` | `#ffffff` | 0 |
| `--status-ink-red` | `#ffffff` | 0 |

`test_theme_plain.py` now asserts BOTH halves of this classification — that every "live" token
really has at least one consumer, and every "declared, never consumed" token really has zero —
so a future edit that starts using one of the dead tokens, or stops using a live one, is caught
by the classification going wrong, not just missed silently.

---

## 2. What surfaces were verified, and how

**By computed style, in a real browser, transitions suppressed, for every read.** A
`* { transition: none !important; animation: none !important; }` rule was injected before every
read — the same trap the brief warned about from the 2026-08-02 session bit nothing this time
only because it was suppressed first, every time, deliberately.

| Surface | Account state | Result |
|---|---|---|
| Sign-in screen | unauthenticated | `data-theme="plain"`, bg `rgb(245,246,248)`, text `rgb(26,29,35)` — Fairbanks |
| A fresh operational account, no stored preference | new | `data-theme="plain"` |
| An operational account with a stored choice (`maria`) | chosen | `data-theme="maria"` — kept, not overridden |
| Research account, consent screen | pending consent | `data-theme="newyork"` **after the fix in section 3**; was `"plain"` before it |
| Research account, intake questionnaire overlay | consent granted | `data-theme="newyork"`, bg `rgb(10,14,18)` (dark, correct) |
| Research account with `maria` written directly into its column (bypassing `themeset`) | forced stored value | `data-theme="newyork"` regardless — the pin holds even against a value the API itself refuses to write |
| Administration "Active"/"Archived" pills | operational admin | see 1.1 |

**Not observed**: anything requiring actual pixel rendering (this container does not composite,
per the standing constraint) — no screenshot, no claim about how anything *looks*. Every number
above is `getComputedStyle`, arithmetic, or text content, never a visual judgement.

---

## 3. A real defect found while verifying: the consent screen never got the research pin

**Not hypothetical, not a test artifact — confirmed live, then fixed, then re-confirmed.**

### 3.1 What was wrong

`LinApp.init()` — before this session, the ONLY caller of the theme sync that applies a research
account's fixed theme — is skipped entirely while a research participant is on the consent
screen. `auth.js`'s `routeFromView`:

```js
function routeFromView(view) {
  currentView = view;
  if (needsConsent(view)) { showConsentScreen(); return; }   // <-- returns HERE
  showApp(view);
  ...
  if (window.LinApp && typeof window.LinApp.init === "function") window.LinApp.init();
}
```

So the consent screen — which every research participant sees first, before anything else —
rendered whatever the **operational** default happened to be, never the research pin. This was
invisible for as long as `DEFAULT_THEME` and `RESEARCH_THEME` were both `"newyork"` (identical by
coincidence). Decoupling them on 2026-08-04 turned it into a real, silent violation of "every
participant sees identical stimulus" for the one screen every research participant is guaranteed
to see.

**Found by testing, not by inspection first.** A research account with `maria` forced directly
into its `theme` column was loaded fresh; the consent screen rendered `data-theme="plain"` even
after a real network round trip to `/exec` had already returned `{"theme":"newyork","fixed":true}`
— confirmed by calling the exact fetch `syncThemeFromServer` makes, by hand, and getting the
correct answer while the DOM still showed Fairbanks. Calling `LinApp.init()` a second time fixed
it, which localised the cause to the consent gate, not the network or the server.

### 3.2 The fix

`app.js` exposes the theme sync directly:

```js
window.LinApp = {
  syncTheme: syncThemeFromServer,
  ...
```

`auth.js`'s `routeFromView` calls it BEFORE the consent branch, not only after:

```js
function routeFromView(view) {
  currentView = view;
  try { if (window.LinApp && typeof window.LinApp.syncTheme === "function") LinApp.syncTheme(); }
  catch (e) {}
  if (needsConsent(view)) { showConsentScreen(); return; }
  showApp(view);
  ...
```

Idempotent — `init()` still calls the same sync again once consent is granted, which is a no-op
if nothing changed. Confirmed live, before and after: consent screen `data-theme` went from
`"plain"` to `"newyork"` for the same account, same stored value, only the code changed.

### 3.3 Why there is no offline DOM harness for this, and what stands in for one

`tests_render.html` stubs `LinAuth.init()` to return `false` specifically so `app.js` never boots
the real application (its own header comment states this), and it does not load `auth.js` at
all — the defect lives entirely in the bootstrap sequence that harness exists to avoid running.
A live check needs a real browser driving `index.html` through an actual sign-in, which is how
this was found.

What runs offline instead, in `test_theme_plain.py` (**GUARANTEE 7**): a structural assertion
that `LinApp.syncTheme` is exported, that `routeFromView` calls it, and that the call is
positioned before `needsConsent(view)` in the function source — the exact line-order the fix
depends on. It cannot see behaviour behind a passing consent check; it does verify a regression
that deletes the call, or reorders it back, is caught. Fault-injected twice (section 5, T7a/T7b)
and both go red.

---

## 4. The three changes from the brief, and where each stands

**1. Fairbanks is the default everywhere.** `DEFAULT_THEME` is `"plain"` in both `theme.py` and
`app.js`, `index.html`'s initial `<body data-theme="plain">` matches. Verified live: sign-in
screen, a fresh operational account, and (after section 3's fix) the consent screen and intake
questionnaire for an account not yet resolved to research — though for an actual research
account both of those resolve to New York per point 2, correctly, which is not a contradiction:
the operational default is what an unresolved/operational visitor sees; the research pin
overrides it the moment the account is known to be research, and now does so as early as
`routeFromView`, not only after `init()`.

**2. Research participants are pinned to New York, explicitly.** `RESEARCH_THEME: str = "newyork"`
is a literal, not derived from `DEFAULT_THEME` — confirmed by reading the source, not by trusting
the docstring. Verified the pin holds against a value written directly into the database column
(bypassing the API refusal entirely), on the consent screen, and on the intake questionnaire.
The server-side refusal (`themeset` gated in `gate_action`, refused again in the handler, ignored
again in `resolve_theme`) is unchanged from the 2026-08-02 work and re-verified green.

**3. Operational accounts keep the switch; a stored choice survives the new default.** Verified
live: an account that chose `maria` before this session's changes (simulated by calling
`themeset` after the new default was in place) still renders `maria`, not `plain`, on the next
load — `resolve_theme` only falls through to `DEFAULT_THEME` on a NULL column, never overwrites
a real one.

---

## 5. The label/key divergence — the leak, and the fix

`a_themeset`'s unknown-theme refusal built its message from `', '.join(THEMES)` — the RAW
internal keys, `"plain, light, newyork, maria"`. Confirmed by direct call:

```
unknown theme: chartreuse; recognized themes are plain, light, newyork, maria
```

**The prior session's own "no surface says plain" test (Guarantee 6) did not catch this**,
because it only exercised the RESEARCH account's fixed-theme refusal (`"not available: the
interface theme is fixed..."`), which structurally can never mention a theme name at all — a
different refusal message from the one that actually leaked. The leaking path is an
**operational** account sending an unrecognised theme string, never exercised by that check.

Fixed with a server-side `THEME_LABELS` map (mirroring `app.js`'s `THEME_META` labels) and the
refusal now reads:

```
unknown theme: chartreuse; recognized themes are Fairbanks, Miami, NYC, Maria
```

Two checks added, right where the leak actually happens (not only in the general sweep): the
refusal from an operational account's unknown-theme request never contains `"plain"`, and does
contain `"Fairbanks"`. A third check cross-reads `THEME_LABELS` against `app.js`'s `THEME_META`
text so the two literals — genuinely independent, no shared source — cannot drift apart silently.

**No migration.** The stored column value and `THEMES`'s vocabulary are unchanged; only the
label a human reads changed, exactly as instructed.

---

## 6. Verification

### 6.1 `test_theme_plain.py`: 63 → 74 (prior session) → **98** (this session)

Guarantee 5 (pill contrast, re-verified live per section 1.1), Guarantee 6 (extended: the actual
leaking refusal path, plus the `THEME_LABELS`/`THEME_META` cross-check), and the new Guarantee 7
(section 3.3) account for the growth.

### 6.2 Fault injection — every check proven able to fail, baseline re-measured after each

| Fault | Detected | Baseline after restore |
|---|---|---|
| T1 `THEME_LABELS` reverted to the raw `', '.join(THEMES)` leak | 96/98 | restored |
| T2 `THEME_LABELS` diverges from `app.js` (one label changed) | 96/98 | restored |
| T3 `DEFAULT_THEME` reverted to `newyork` | 96/98 | restored |
| T4 `RESEARCH_THEME` re-coupled to `DEFAULT_THEME` | 95/98 | restored |
| T5 admin pill reverted to the old translucent fill | 96/97 | restored |
| T6 `LinApp.syncTheme` export removed | 97/98 | restored |
| T7a the sync call removed from `routeFromView` entirely | 96/97 | restored |
| T7b the sync call moved to AFTER the consent branch (**the original defect, reproduced exactly**) | 97/98 | restored |

**A trap repeated from this project's own history, caught in the act.** A first attempt at T7b
*renamed* `needsConsent` to `FAULT_T7b_needsConsent` rather than reordering anything, and the
check stayed green — not because the check was weak, but because Python's `str.find` matched
`"needsConsent(view)"` as a **substring** inside the renamed identifier, so the fault never
actually removed what the check was looking for. Caught by watching it stay green and asking
why, not by trusting the result. Replaced with a genuine two-line reorder that reproduces the
original defect's exact shape; it goes red.

### 6.3 Full suite and both harnesses, current code

**Server: 39 suites, 2196/2196.** `tests_render.html`: **86/86** (a session token from a real
signed-in operational PM with a computed project — the same live-state proof the 2026-08-04 and
2026-08-05 extraction reports established: the count moves with server state, which is the
evidence these checks reach the server rather than a primed fixture). `tests.html`: **51/51**.

Repo state was clean before this session started (`git status` empty, `main` even with
`origin/main`) — the concurrent-editing collision from the prior task's session did not recur
here.

---

## 7. Files changed this session

- `server/app/theme.py` — `THEME_LABELS`, and the refusal message built from it.
- `server/tools/test_theme_plain.py` — 63 → 98 checks (see 6.1).
- `assets/js/app.js` — `LinApp.syncTheme` exported; the corrected unmeasured-token comment (in
  the test file, not here — `app.js` itself only gained the one export line).
- `assets/js/auth.js` — `routeFromView` calls the theme sync before the consent branch.

Nothing under `server/app/simulation/` touched. No migration; `participants.theme` (0017) is
unchanged.

---

## 8. Open

- The four "declared, never consumed" sector/scope tokens and the five `status-ink-*` tokens
  (section 1.2) are dead CSS. Not fixed here — reported so a future session does not have to
  rediscover their status by hand, and so a future rule that starts consuming one is prompted to
  reconsider whether it then needs a contrast floor.
- Whether `--accent` and the other "live unmeasured" tokens should get an automated AA floor
  (not just be reported) is Lin's call, same posture the prior report and this one both take.
