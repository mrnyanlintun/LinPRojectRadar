# Research fixtures

**Nothing in this directory is real project evidence.**

It holds generated research fixtures, staged so that they are visibly separate from production
data, participant data, operational project documents and research exports. Files here are read by
audit scripts and, later, by test-only importers. **No record in this directory may enter an
operational or participant database, and no surface may describe any of it as validation.**

## `synthetic/OG-SYNTH-0.1/`

The Opus Gubernatio synthetic programme, version `OG-SYNTH-0.1`, generated from seed `20260811`.
Every record carries `data_origin = SYNTHETIC_RESEARCH_FIXTURE` and
`not_for_empirical_validation = true`. Staged from three package archives; the combined archive the
handoff described was never supplied, and the validator and generator scripts it would have carried
are absent, so the programme's own validation claim is unverified.

What this material supports: implementation fidelity, known-answer testing, structural
verification, solver agreement, edge and abstention behaviour, and adapter development.

What it does not establish: real-world predictive accuracy, empirical calibration, universal
thresholds, field validity, or any causal benefit to practitioners.

Audit of record: `REPORT_2026-08-11_synthetic-package-ingest-and-reconciliation.md` at the
repository root, with machine-readable results under `code_audit/synthetic_package_*.csv`.
Independent checker: `tools/audit_synthetic_package.py`, which reads only.

A fixture existing here does not authorise a disabled module to run, does not make any module
voting, and does not convert a concept-only module into a canonical active module.
