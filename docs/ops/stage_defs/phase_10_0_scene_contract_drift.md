# Phase 10.0 - Scene Contract Export + Drift Control

Date: 2026-02-06

## Scope
- Export a canonical scene contract package for release.
- Surface DB-to-registry drift in diagnostics.
- Add drift guard + contract export smoke to v0.8 semantic gate.
- Produce artifacts for contract export + drift report + contract diff.

## Scene Contract Export
Command:
```
DB_NAME=sc_demo E2E_LOGIN=svc_project_ro E2E_PASSWORD='ChangeMe_123!' \
make scene.contract.export
```

Output:
- `docs/contract/exports/scenes/scene_contract.v10_0.json`
- `docs/contract/exports/scenes/LATEST.json`

Contract fields:
- `schema_version`
- `scene_version`
- `profiles_version`
- `scenes` (canonical)

Notes:
- `generated_at` is optional and excluded from canonical diff checks.

## Drift Diagnostics
`data.scene_diagnostics.drift[]` entry shape:
- `scene_key`
- `kind` (`db_missing_field_filled` | `fallback_override` | `schema_migration_injected`)
- `fields`
- `severity` (`info` | `warn`)
- `source` (`db->registry`)

## Drift Guard
Command:
```
DB_NAME=sc_demo E2E_LOGIN=svc_project_ro E2E_PASSWORD='ChangeMe_123!' \
make verify.portal.scene_drift_guard.container
```

Rules:
- Critical scenes (`projects.list`, `projects.ledger`) cannot emit `warn` drift.
- `fallback_override` drift for non-critical scenes must appear in drift debt baseline.

Drift baseline:
- `docs/contract/snapshots/scenes/scene_drift_debt.v10_0.json`

## Contract Export Smoke
Command:
```
DB_NAME=sc_demo E2E_LOGIN=svc_project_ro E2E_PASSWORD='ChangeMe_123!' \
make verify.portal.scene_contract_export_smoke.container
```

## Artifacts
- `/mnt/artifacts/scenes/scene_contract.latest.json`
- `/mnt/artifacts/scenes/scene_drift_report.latest.json`
- `/mnt/artifacts/scenes/scene_contract.diff.txt`

## Gate
- `verify.portal.ui.v0_8.semantic.container` includes:
  - `verify.portal.scene_contract_export_smoke.container`
  - `verify.portal.scene_drift_guard.container`
