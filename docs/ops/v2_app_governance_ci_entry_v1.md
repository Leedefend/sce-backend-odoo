# v2 App Governance CI Light Entry v1

## Goal

Use a lightweight, deterministic governance gate entry in CI and local smoke chains.

## Recommended commands

- CI-light make target:
  - `make verify.v2.app.ci.light`
- Full local governance chain:
  - `make verify.v2.app.all`
- Script alias:
  - `python3 scripts/verify/v2_app_verify_all.py --json`

## Why this entry

- Keeps iteration cost low for governance checks.
- Preserves deterministic output via summary + failure reasons.
- Avoids running heavy runtime pipelines for schema-only governance changes.

## Schema guard linkage

- `verify.v2.app.ci.light` additionally runs:
  - `python3 scripts/verify/v2_app_governance_output_schema_audit.py --json`

## Audit output semantics

- `gate_version`: audit output version marker
- `gate_profile`: fixed as `ci_light` for this audit
