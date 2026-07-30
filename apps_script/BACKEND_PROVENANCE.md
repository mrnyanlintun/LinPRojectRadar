# Backend Provenance

Migration phase M0. This document records what is known, what is unknown, and how the Render
compatibility contract will be derived from it.

> The endpoint response and the production frontend configuration are controlling. Source comments
> and separately supplied source files are not evidence of what is deployed.

## Which URL the frontend calls

`assets/js/config.js:13` sets:

```js
window.LIN_API_URL = "https://script.google.com/macros/s/AKfycbwhmg_1L_.../exec";
```

Deployment id `AKfycbwhmg_1L_RjbxPTR0IF3xpmHgLLzHA67O3mH27uqrAFfv8bF9U359yBqwjqbZO3YNTO`.
This is the single endpoint for the entire application; there is no second base URL.

## Which Apps Script project owns it

**TO_BE_RECORDED.** `script_id` and `project_name` are visible only in the Apps Script console and
cannot be derived from the endpoint or the repository.

## Which version is deployed

**TO_BE_RECORDED** as a version number. `active_version_number` comes from
Apps Script, Deploy, Manage deployments. It must not be inferred from any source file.

What the live endpoint reported on capture:

| Field | Value |
|---|---|
| `version` | `lin-project-radar-backend-v10.29-geocode` |
| server `timestamp` | `2026-07-30T21:31:40.548Z` |
| client capture stamp | `20260730T213156Z` |

The two timestamps are kept separate in `deployment-manifest.json` as `server_reported_timestamp`
and `captured_at_utc`. They differ by roughly 16 seconds.

## What the live endpoint reported

Evidence: `p0-baseline/live/20260730T213156Z/`, containing `ping.json`, `ping.headers.txt` and
`ping.sha256.txt`.

- Final status `200 OK`, `application/json`, after a `302` redirect to
  `script.googleusercontent.com`. The redirect is normal Apps Script behaviour; a capture client
  must follow redirects or it will record the 302 body instead of the payload.
- SHA-256 of `ping.json`: `D7CA7342297B41645728E93180459E021AEF7E4F05A85D4CB97AC052A48DCE82`.
- `postActionsRegistered` lists 17 POST actions.
- `anthropicKeyPresent` and `openaiKeyPresent` are booleans, not key values. No credential is
  present in the captured evidence.
- The response reports the version under key `version`. The `health` action reports it under key
  `apiVersion`. Both spellings exist in this backend.

## Where the source snapshot came from

No deployed source snapshot is in hand. `apps_script/deployed/` is empty.

A v10.36 source was supplied separately as a `.docx` and is filed at
`apps_script/reference/Code_v10.36_editor_head.gs`. It is **editor HEAD, not the deployed version**,
and the live endpoint reports v10.29. It is used only as a labelled cross-check when parsing
dispatchers, never as the deployed contract.

That file declares three different versions of itself: the header comment says `v10.26-drop-cat12`,
the deploy instruction says `?action=ping` returns `v10.31-milestones`, and `API_VERSION` is
`v10.36-roster-json`. Eight distinct version strings appear in total. This is the precise failure the
controlling statement above anticipates.

## Its checksum

**Not recorded, deliberately.** The `.docx` extraction is not verifiable as byte identical to the
console original: paragraph breaks were reconstructed from Word XML markers, and a Word round trip
does not preserve line endings, trailing whitespace or tab structure faithfully. A SHA-256 over it
would certify a transcription, not the source.

Character content did survive intact (19 em dashes U+2014, one U+00B7, zero U+FFFD replacement
characters). An earlier note in this migration claimed the round trip had corrupted non-ASCII
characters; that was a console rendering artifact and is withdrawn. The objection to checksumming
this file is structural fidelity plus the fact that it is the wrong version, not character damage.

A checksum is recorded only when a plain text export is taken directly from the Apps Script console,
and only for a file placed under `apps_script/deployed/version-NNN/`.

## How the Render compatibility contract will be derived

1. Retrieve the deployed source for `active_version_number` from the console as plain text, place it
   at `apps_script/deployed/version-NNN/Code.gs`, and record its SHA-256.
2. Re-run the inventory with Source A available, replacing every `UNKNOWN` in
   `p0-baseline/contracts/action-inventory.csv`.
3. Authorise a capture run of `tools/contract-fixtures/capture.py` against the live endpoint for
   read-only actions, producing fixtures and derived response schemas.
4. Capture write and AI actions manually against a disposable project, with approval.
5. Build the Render facade against those fixtures.
6. Gate at D2 with `tools/contract-fixtures/compare.py`, diffing Render responses against the Apps
   Script fixtures on status, key sets, types and null handling.

Two behaviours the facade must preserve, both established during M0:

- **Case insensitive action matching.** The frontend sends `identifyOnly` at `store.js:508` while
  the backend registers `identifyonly`; the dispatcher lowercases the action before comparing.
- **Redirect following.** Clients must follow the `302` or they will not see the payload.

## Credentials

No credentials, OAuth tokens, API keys or account identifiers are recorded in this directory or in
`p0-baseline/`. The captured ping exposes only boolean key presence flags.
