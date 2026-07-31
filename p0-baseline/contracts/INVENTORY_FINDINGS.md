# Action Inventory Findings

Migration phase M0. Derived from three sources, one of which is unavailable.

## Sources

| Source | Status | Provenance |
|---|---|---|
| A. Dispatchers (`doGet`/`doPost`) | **UNAVAILABLE** | The deployed source is not in hand. `in_dispatcher` is `UNKNOWN` for every row, per M0 Amendment 3. |
| B1. Live ping self-report | **CAPTURED** | `p0-baseline/live/20260730T213156Z/ping.json`, field `postActionsRegistered`, 17 POST actions. |
| B2. Health self-report | **NOT CAPTURED** | No live `?action=health` request was issued in this PR. `in_health_selfreport` is `NOT_CAPTURED` for every row. |
| C. Frontend call sites | **COMPLETE** | Every `assets/js/*.js` module read; comment-only matches excluded by inspection. |

The live deployment reports `lin-project-radar-backend-v10.29-geocode`. The supplied v10.36 source is
editor HEAD, filed at `apps_script/reference/`, and is used below only as a labelled cross-check.
It is not the deployed contract.

## Counts

- 29 distinct actions recorded: 11 GET, 18 POST.
- 23 have at least one frontend call site.
- 6 have none.
- 17 POST actions confirmed registered by the live deployment.

## Actions in the backend but never called by the frontend

`gethistory`, `savehistory`, `tts`, `health`, `ping`, `version`.

`health`, `ping` and `version` are diagnostics and are expected to have no call site.
`gethistory` and `savehistory` are a matched read/write pair with no consumer in the current
frontend. `tts` is a paid AI action with no consumer. The Render facade should treat all five
non-diagnostic actions as candidates for exclusion at A1 unless a consumer is planned.

## Actions called by the frontend with no dispatcher match

None can be established, because Source A is unavailable. This determination must be repeated once
the deployed source is retrieved. The nearest available evidence is the live ping self-report, which
yields one gap, recorded below as accepted rather than as a defect.

## Known frontend/backend version gap (accepted)

Per M0 Amendment 4, the following is recorded and is **not** treated as a new bug.

- **`saveportfoliohealth`** is called at `store.js:535` but is absent from the live v10.29
  `postActionsRegistered` list. It is present in the v10.36 reference, which indicates it was
  added after v10.29.
- **`getportfoliohealth`** is called at `store.js:542` and is **confirmed absent from the live
  deployment**. The capture run returned:

  ```json
  {"ok":false,"error":"Unknown GET action: getportfoliohealth"}
  ```

  This upgrades the earlier "unverified" status to verified. Both halves of the portfolio health
  pair are therefore missing from the deployed backend while the frontend calls both.
  `deepdive.js:2330` consumes `LinStore.getPortfolioHealth()`, so the Health dialog is calling an
  endpoint that does not exist in production today.

The Render facade decides at A1 whether to implement these two actions.

## Capture run, 2026-07-30

Read-only GET actions only. All 18 POST actions remained `DEFERRED_TO_MANUAL`; no write or AI
action was issued. 11 of 11 GET actions captured, 0 failures, every one returning **HTTP 200**.

Two results are contract-relevant beyond the fixtures themselves:

1. **Errors are returned with HTTP 200 and `ok:false`.** `getportfoliohealth` is an unknown action
   yet still answers 200. Status code carries no success information in this API. The Render facade
   must reproduce this, and `compare.py`'s status check alone will not catch an action that
   regresses into an error shape; the key-set and type checks are what detect it.
2. **`ping` and `version` returned byte-identical payloads**, confirming they are aliases on the
   live deployment, not merely in the v10.36 reference.

`?action=health` confirmed live that it reports the version under `apiVersion`, while `?action=ping`
reports it under `version`. Both were captured, so the inconsistency is now evidenced rather than
inferred from source.

### Sample project id

`sample_project_id` is `PRJ-08421`, an active project verified from `?action=listslim`.

A first capture attempt used `01`, which produced `{"ok":false,"error":"Not found: 01"}` for `get`
and `Project not found: 01` for `listcorpus`, `listauditresults` and `gethistory`. `01` is an
**archived** project ("Phase23 Smoke Test"), visible in the `listarchived` fixture. Those four
fixtures were error shapes and were replaced by re-capturing with an active id. This is the exact
failure the config file warns about: an id that looks plausible can silently baseline an error
shape as the contract.

`gethistory` legitimately returns `{"ok":true,"history":[]}` for this project. The empty array
carries no element type information, so its derived schema records `items` as `unknown`.

## Actions present in dispatchers but absent from a self-report

Source A is unavailable, so this comparison is made against the v10.36 reference as a cross-check
only. Two discrepancies are visible within that reference file alone, which is why the self-reports
are treated as unreliable:

- `getportfoliohealth` is dispatched by the reference `doGet` but is missing from
  `okHealth_().endpoints`.
- `saveportfoliohealth` is dispatched by the reference `doPost` but is missing from
  `okHealth_().endpoints`, and is also missing from the live v10.29 ping self-report.

The live ping self-report lists 17 POST actions; the v10.36 reference dispatches 18. The single
difference is `saveportfoliohealth`, consistent with the version gap above.

## Every direct call site outside `store.js`

Exactly one exists.

| File | Line | Action | Detail |
|---|---|---|---|
| `assets/js/signals.js` | **1297** | `extractsignals` | `return fetch(window.LIN_API_URL \|\| "", {` inside `postJSON()` |

Call chain, verified by reading each step:

1. `signals.js:1436` builds `extractPayload` with `action: "extractsignals"`.
2. `signals.js:1447` calls `extractWithRetry(extractPayload, item)`.
3. `signals.js:1381` calls `postJSON(payload)`.
4. `signals.js:1297` issues `fetch(window.LIN_API_URL)` directly.

This site carries behaviour `store.js` does not replicate: a 45 second `AbortController` timeout and
a four attempt retry with 20s/40s/60s backoff on rate limit responses. Routing it through the shared
client before same origin cutover therefore requires porting that retry policy into `store.js`, not
merely swapping the transport.

Two nearby matches are **not** call sites and were excluded by inspection:

- `signals.js:1143` is `console.log("Upload URL:", window.LIN_API_URL)`.
- `signals.js:600` sends `portfolioanalyze` via `LinStore.post`, which is correctly routed.

Comment-only matches excluded: `store.js:6-9`, `app.js:2261`, `decision.js:74`, `signals.js:523`.

## Case normalisation, not a defect

`store.js:508` sends `action: "identifyOnly"` in camelCase. The live deployment registers
`identifyonly`. The v10.36 reference reads the action as
`String(p.action || 'health').toLowerCase()`, so the call dispatches correctly.

This is recorded because **the Render facade must preserve case insensitive action matching**. A
facade that compares the raw string would break document identification with no frontend change.

## Response key inconsistency

`?action=ping` returns the version under key **`version`**. `okHealth_()` returns it under key
**`apiVersion`**. Any code reading a version from this backend must handle both. M0 Amendment 1
records `reported_api_version` from `version`.
