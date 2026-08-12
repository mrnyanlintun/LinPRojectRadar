# Run 12 release and refreeze record

This record is ADDITIVE. No earlier freeze record is overwritten, and every historical
simulation version stamp remains in `server/app/simulation/models.py`.

## Versions frozen by this run

| Item | Value |
| --- | --- |
| Simulation version, previous | sim-2026.08-v6 |
| Simulation version, final | sim-2026.08-v7 |
| Synthetic package version | OG-SYNTH-0.3 (unchanged, not regenerated; 0.1 and 0.2 preserved) |
| Participant and study package version | og-participant-2026.08-v1 |
| Category nine qualification version | cat9-qual-v1 |
| Client algorithm stamp | as carried by assets/js/client_algorithm_version.js, deliberately not equal to the simulation version |

The participant and study package version is minted by this run and is the first of its kind in
this repository. It names exactly the served participant surface listed in
`run12_participant_package_checksums.sha256`: `index.html` and every file under `assets/`.

## Checksums

| Artefact | Digest |
| --- | --- |
| participant package manifest, aggregate sha256 | 502c03b8f789d1c9ced19ba993f2e88cf610eb0df3f313afd8ee35c749e2192b |
| per-file digests | `code_audit/run12_participant_package_checksums.sha256`, 70 files |
| synthetic v0.3 archive digest, carried forward unchanged | b478a2cb21d8acda89767abb6582913f39b64f3b20afd9ef2cdf0095cd5d93a6 |

## Runtime and dependencies

| Item | Value |
| --- | --- |
| Python | 3.11.15 |
| Platform | Linux 6.18.5, glibc 2.39 |
| fastapi | 0.115.6 |
| uvicorn | 0.34.0 |
| SQLAlchemy | 2.0.36 |
| alembic | 1.14.0 |
| pydantic | 2.13.4 |
| playwright | 1.48.0 |
| lxml | absent from the normal application and test interpreter, as required |

## Governed state at the freeze

| Item | Value |
| --- | --- |
| Voting set | exactly two, A1.7 and A1.8, both cost lineage |
| Disabled concept-only modules | eight |
| Bucket five | two of two disabled |
| Governed status label | Cost Recovery Status |
| Conflict semantics | NOT_ESTIMABLE_SINGLE_LINEAGE, published as no coefficient |
| Migrations applied in production | through 0019; 0020 to 0025 remain unapplied, and this run adds none |

## Frozen-file guard

The guard lives in `server/tools/test_run6_known_answer.py` and
`server/tools/test_run8_retest_classify_27.py`, and pins every file under `server/app/` and
`assets/` against commit 021d5e2 except the files each run is authorised to change. Run 12's
authorised list is three server files and one browser asset, and no more.
