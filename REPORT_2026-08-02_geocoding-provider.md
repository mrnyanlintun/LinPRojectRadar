# 2026-08-02 — Geocoding provider: Google primary, US Census fallback

Nominatim is removed. Google Geocoding is the primary provider and the United States Census
Geocoder is the fallback. No other provider was added.

---

## 1. WHAT YOU NEED TO PROVISION. Nothing geocodes worldwide until this is done.

| | |
|---|---|
| **Environment variable** | `GOOGLE_GEOCODING_API_KEY` |
| **Where to set it** | Render, on the web service, under Environment. Locally, export it. |
| **API to enable** | **Geocoding API**, in the same Google Cloud project you already use for OAuth sign-in. Google Cloud console, APIs and Services, Library, search "Geocoding API", Enable. |
| **Billing** | The Geocoding API requires billing enabled on the project even inside the free monthly credit. If billing is not enabled the key returns `REQUEST_DENIED` and the service will report a credentials problem. |
| **Key restriction to set** | **API restriction: restrict the key to the Geocoding API only.** For application restriction choose **IP addresses**, not HTTP referrers. |

### Why IP restriction and not referrer restriction

This key is used server side, from `server/app/geocode.py`, in an outbound request from the Render
container. It is never sent to a browser and never appears in any page. An HTTP referrer
restriction only works for keys called from a browser and would reject every request this service
makes. Restrict by IP if you can pin Render's outbound addresses, and leave the application
restriction as None if you cannot; the API restriction to Geocoding alone is the one that matters
most, because it caps what a leaked key can be spent on.

Do not reuse the OAuth client credentials. This is a separate API key in the same project.

### What happens before you provision it

The code is inert and fails safely. With no key set, `_google()` returns `NOT_CONFIGURED`
**without making any HTTP request at all**, so an unconfigured deployment costs nothing and leaks
nothing. The Census fallback still runs, so United States street addresses still geocode. The
user is told plainly that the primary provider is not configured rather than being told their
address is wrong.

That distinction is asserted by a check, not assumed. See section 4.

---

## 2. The seam

`server/app/geocode.py`:

```python
# THE SEAM. Order is precedence. Append to add a provider.
_PROVIDERS = (_google, _census)
```

Each provider is a function taking an address and returning an `_Attempt`: what happened, and the
coordinates if it found any. `geocode()` walks the tuple in order and stops at the first provider
that returns a position. Adding a third provider is appending a function. It is not a plugin
system, a registry, or a base class, because two providers do not justify one and a third would
not either.

`_get_json(url)` is the single HTTP seam in the module. It is the one thing the test suite
replaces, which is why the suite is fully offline and deterministic.

The public contract is unchanged: `geocode(address) -> Result` and
`apply_to_doc(doc, address, previous=None) -> Result`. Both callers
(`server/app/workspace.py:87`, `server/app/writes.py:213`) are untouched.

`Result` gained two fields: `provider` (which provider supplied the position) and `ambiguous`.

---

## 3. The Google response cases are handled by name, not as "non-200 means failure"

| Google status | Outcome | What the user reads |
|---|---|---|
| `OK`, one exact result | `FOUND` | the matched address, shown back |
| `OK`, several results, or `partial_match` | `AMBIGUOUS` | the matched address, and the position is used, flagged uncertain |
| `ZERO_RESULTS` | `NOT_FOUND` | falls through to Census; if that also finds nothing, "That address could not be found." |
| `OVER_QUERY_LIMIT`, `OVER_DAILY_LIMIT` | `QUOTA` | "The address service has reached its usage limit for now." |
| `REQUEST_DENIED` | `REJECTED` | "The address service rejected this deployment's credentials." |
| `INVALID_REQUEST`, `UNKNOWN_ERROR`, anything new | `UNAVAILABLE` | a reachability sentence |
| key absent | `NOT_CONFIGURED` | "The address service is not configured on this deployment." |
| transport failure or timeout | `UNAVAILABLE` | a reachability sentence |

Two decisions inside that table are worth stating:

**Google's `error_message` is logged and never shown.** It is the useful half of a
`REQUEST_DENIED` for whoever is debugging, and it can name the key restriction that refused the
request, which is not something to put on a user's screen. A check asserts it does not leak.

**A "not found" is never claimed on the strength of Census alone.** Census covers United States
addresses only, so it returning nothing for a London address is not evidence the address does not
exist. When Google is rejected or unconfigured and Census finds nothing, the message says the
primary is not available and that a United States service was tried instead. It does not say the
address could not be found. A check asserts this.

### Caching rule

Cache answers about the **address**. Never cache answers about the **service**.

A position, or every provider agreeing the address is not findable, is cached by normalized
address. A quota, a rejected key, an absent key and a timeout are **not** cached, because caching
one would make a single misconfigured minute permanent and the retry the message promises the user
would silently never happen.

---

## 4. Verification

### The key is not available in this environment

There is no `GOOGLE_GEOCODING_API_KEY` here, so **the Google path is verified against stubbed
responses only, and I am not claiming the live Google path works.** What I verified live is the
Census fallback and the unconfigured-key behaviour, end to end, through the real module against
the real service.

```
GOOGLE key present: False

ADDRESS : 1600 Pennsylvania Avenue NW, Washington, DC 20500
  ok    : True | provider: census | ambiguous: False
  latlng: 38.89869893252 -77.03518753691
  shown : 1600 PENNSYLVANIA AVE NW, WASHINGTON, DC, 20500
  error : None

ADDRESS : Philadelphia International Airport, Philadelphia, PA
  ok    : False | provider: None | ambiguous: False
  error : The address service is not configured on this deployment. A United States address
          service was tried instead and did not match this address. Saving the address again
          will retry it.

ADDRESS : 8000 Essington Ave, Philadelphia, PA 19153
  ok    : False | provider: None | ambiguous: False
  error : The address service is not configured on this deployment. A United States address
          service was tried instead and did not match this address. Saving the address again
          will retry it.
```

**What is shown back to the user** on success is the provider's own matched address, third line
above: `1600 PENNSYLVANIA AVE NW, WASHINGTON, DC, 20500`. That is how a user checks the pin is on
the right building, and it is why it has always been surfaced.

**Read the second and third cases as a limit, not a success.** Census could not match a facility
name, which is expected, but it also could not match a plain numbered street address in
Philadelphia. Census matches against its own address-range reference set and its coverage is
patchier than it looks. Until the Google key is in place, expect a meaningful share of real
addresses to fail. The message correctly does not blame the address for it.

### The provider suite: 31 checks, and every one proven able to fail

`server/tools/test_geocode_providers.py`. Fully offline: `_get_json` is stubbed by a router that
answers by URL prefix and records which providers were called.

Seven guarantees: Google answers and the fallback is not consulted; the fallback runs when Google
finds nothing or cannot be reached; the failure conditions are told apart; an uncertain match is
flagged but still used; service answers are never cached and address answers are; the retained
coordinates behaviour survives the provider change; the retired provider is gone.

**Fault injection.** 18 faults were injected into `geocode.py` one at a time, each reverted after.
Every check went red under at least one fault, and **every run printed a `RESULT:` line**, so none
of them crashed rather than failed.

| Fault | Checks red |
|---|---|
| always consult the fallback, even after a success | 11 |
| collapse every failure to one undifferentiated sentence | 4 |
| never flag ambiguity / always flag ambiguity | 2 / 1 |
| cache everything / cache nothing | 1 / 3 |
| restore the old erase-coordinates-on-failure behaviour | 3 |
| re-add the retired provider's URL constant | 2 |
| reverse provider precedence | 2 |
| show Google's raw `error_message` to the user | 1 |
| call Google even when the key is absent | 2 |
| report an unreachable service as "address not found" | 1 |
| let any single NOT_FOUND decide the message | 4 |
| treat an unreachable provider as a match | 7 |
| normalize the address written back to the document | 3 |
| retain coordinates even when there were none to retain | 3 |

Coverage: **31/31 checks proven able to fail.**

**Two of my own injections were themselves faulty, and that matters.** The patcher replaced the
first matching occurrence of a string; after one injection there were two matches, so reverting it
swapped the "could not be found" and "could not be reached" sentences instead of restoring them.
A later re-anchoring edit did not match but printed success anyway. The restore-and-recheck step
after every single fault caught both. Without it, six of the fourteen results above would have
been measured against a silently corrupted module and would have been worthless. The lesson is the
one this repository keeps relearning: verify the revert, not just the injection.

### Full suites, on merged `main`

Run after fast-forwarding to `origin/main` at `ead2357`, because that merge touched eight test
files and `assets/js/store.js`.

- **Server: 23 suites, 1247 checks, 0 failures.** Including `test_workspace_t3t5.py` 70/70, which
  is the suite that covers `apply_to_doc`, and `test_writes_a1b.py` 87/87.
- **`tests_render.html`: 43/43.** In a real browser, no console errors.
- **`tests.html`: 51/51 assertions.** In a real browser.

One environment note. Most server suites need a migrated database and `SESSION_SECRET`; run
against a stale `server/dev.db` they abort with `KeyError` and print no `RESULT:` line at all,
which reads exactly like a clean run if you only skim. They were run against a throwaway sqlite
built by `alembic upgrade head`, never against production.

---

## 5. Behaviour preserved from the previous geocode fix

All three, asserted against the **new** provider path, because a provider swap is exactly the kind
of change that quietly regresses them:

1. **A failed geocode does not erase coordinates it cannot replace.** `apply_to_doc` reads
   `previous`, the STORED document, so a client payload that omits coordinates cannot delete them.
2. **The matched address is shown back to the user**, carried as `formattedAddress`.
3. **A retained position is labelled as such.** `geocodeStale` is set, and `formattedAddress` keeps
   naming the address those coordinates actually matched, so a reader can see it is not the address
   now stored. `linLocationNote()` in `config.js` still returns its three states.

Nothing was retained when there was nothing to retain, also checked.

**The map and the globe were not touched.** No mapping library was swapped, no Google Maps was
embedded, and no globe code was modified.

---

## 6. Backfill: how many projects need it

**Do not run this. It is yours to approve.**

I can only count what I am permitted to inspect. In the local development database
(`server/dev.db`, the only project data I looked at, and production was not queried):

| | |
|---|---|
| Projects total | 2 |
| With an address | 2 |
| With coordinates already | 2 |
| **With an address and no coordinates** | **0** |
| Flagged `geocodeStale` | 0 |

So **zero projects in the local database need a backfill to gain coordinates.**

I cannot give you the production number. To get it, run this read-only query against the
production database yourself:

```sql
SELECT count(*) FROM projects
WHERE coalesce(trim(doc->>'address'), '') <> ''
  AND (doc->>'lat' IS NULL OR doc->>'lng' IS NULL);
```

### There is a second, larger question you should decide separately

Both local projects already have coordinates, **and both were placed by the retired provider.**
One of them is visibly wrong:

| Project | Address entered | Retained match |
|---|---|---|
| Globe Verify PHL | Philadelphia International Airport, Philadelphia, PA | Hampton Inn Philadelphia-International Airport, 8600 Bartram Avenue |
| Globe Points BNA | Nashville International Airport, Nashville, TN | Nashville International Airport, 1 Terminal Drive |

The first pin is on a hotel near the airport, not the airport. These coordinates will never be
revisited on their own, because the geocoder only runs when an address changes.

So there are two possible backfills and they are different sizes:

- **Fill the gaps.** Geocode only projects with an address and no coordinates. Zero locally,
  unknown in production. Purely additive, nothing existing is overwritten.
- **Re-place everything the retired provider placed.** Every project currently holding
  coordinates. This overwrites existing data and would need a record of the old values first.

Either would be a script that reads each project, calls `geocode()`, and writes through
`apply_to_doc`, rate-limited and run once with the key present. Neither was written and neither
was run.

---

## 7. Repository state

`main` had moved: local was at `8b151a4` and `origin/main` at `ead2357`, one commit ahead. I
fast-forwarded and re-ran everything on the merged tree before committing. There is no push in
this report's scope beyond this commit; a push triggers a Render deploy.

Separately, and unresolved from an earlier session: the branch **`t15-local-unpushed`** (`9dc137d`)
holds five commits that were never pushed. The only substantive code of mine in them is the
`unported_modules()` correction at `server/app/simulation/registry.py:49`; `origin` still carries
the old `sorted(set(registry_index()) - set(VALIDATED))`, which over-reports the five Group D
modules as unported. That branch is preserved and nothing was lost. It needs a decision from you,
and touching it means editing `server/app/simulation/`, which I do not have standing permission for.

## Files changed

- `server/app/geocode.py` — rewritten. Nominatim removed, Google and Census behind `_PROVIDERS`.
- `server/tools/test_geocode_providers.py` — new, 31 checks.
- `REPORT_2026-08-02_geocoding-provider.md` — this file.
- `T6_HANDOFF.md` — new section at the top.

Three surfaces still told users the platform geocodes through Nominatim, which is now false. A
retired provider that is still named in user-facing copy has not really been removed:

- `index.html:849` — the About panel. Rewritten, and it now also states the retained-position
  behaviour. Verified rendered in a real browser: no occurrence of the retired provider's name
  remains anywhere in the DOM, and the new paragraph contains no em dashes. The Browser pane was
  not compositing frames, so there is no screenshot; the evidence is a DOM read, not an image.
- `NAMING_AUTHORITY.md:104` — the standing description that user-facing surfaces quote. Corrected
  to name the provider and the fallback. Nothing else in that document was touched.
- `README.md:26` and `server/README.md` — corrected, and `GOOGLE_GEOCODING_API_KEY` was added to
  the environment variable table with the restriction guidance.

`server/tools/test_workspace_t3t5.py` — two stale comments corrected, and a note added recording
that its stub replaces `geocode()` wholesale and therefore exercises no provider, which is why the
new suite exists separately. Comments only; no check was changed.

## Flagged for your review, not approved by me

The user-facing failure sentences in `_compose_error()` are operational wording I composed. They
are not liability or consent statements, but they are what a user reads when a location does not
resolve, and they were written here rather than approved. They are marked as such in the source.
