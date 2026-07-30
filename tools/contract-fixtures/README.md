# Contract fixtures

Captures the Apps Script backend's response contract, and diffs a candidate implementation against
it. `compare.py` is the D2 gate tool.

Standard library only, no dependencies. Python 3.8+.

## Status at M0

**No capture run has been executed.** The harness is built and verified but not run, per M0
Amendment 7. `p0-baseline/contracts/` contains the inventory only; no fixture bodies exist yet.

## Before the first capture run

1. Populate `sample_project_id` in `config.json`. Four GET actions (`get`, `listcorpus`,
   `listauditresults`, `gethistory`) are skipped until it is set, because without an id they return
   an error shape that would be baselined as the contract.
2. Confirm the researcher authorises a live capture.

## Usage

```bash
python capture.py --config config.json            # dry run: prints the plan, issues nothing
python capture.py --config config.json --confirm  # issues the GET requests
```

```bash
python compare.py --baseline p0-baseline/contracts --candidate render-fixtures/contracts
python compare.py --baseline A --candidate B --json report.json
```

`compare.py` exits 0 when there are no differences, 1 on drift, 2 when it could not run.

## Safety

Three guards are enforced in code, not by convention:

- **No POST is ever issued.** All 18 POST actions are `DEFERRED_TO_MANUAL` in `config.json` because
  each mutates stored state or bills a paid API key. `send_post()` raises rather than sending.
  Capturing them needs a disposable project and explicit approval.
- **Capture is opt in.** Without `--confirm`, the script prints its plan and exits without issuing a
  request.
- **Timeout floor.** A `timeout_seconds` below 45 is rejected. Apps Script cold starts have been
  measured above 20 seconds, and a short timeout would record false failures as the contract.

## What is compared

`compare.py` reports four classes of drift: status, key sets at every depth, types, and null
handling. Array *contents* are not compared, only the merged element shape, so a portfolio of 12 and
a portfolio of 3 compare equal provided element shapes match.

Verified against synthetic fixtures: a candidate that changed status 200 to 500, dropped `ok`, added
`projects[].extra`, changed `projects[].cpi` from number to string, and changed `projects[].note`
from null to string was reported with all five differences and exit code 1.

## Notes carried from the inventory

- The endpoint answers with a `302` to `script.googleusercontent.com`. Clients must follow
  redirects or they record the redirect page instead of the payload.
- `?action=ping` reports the version under key `version`; `?action=health` reports it under
  `apiVersion`.
- The frontend sends `identifyOnly` in camelCase and the backend lowercases before dispatch. **The
  Render facade must match actions case insensitively.**
