# Phase 9.8 - Scene Observability + Snapshot Guard

Date: 2026-02-06

## Scope
- Add `scene_diagnostics` to `system.init` output (schema/version/loaded_from/resolve_errors/normalize_warnings/timings).
- Add scene snapshot guard to detect unintended scene config drift.
- Add export/update targets for canonical scene snapshots.

## Scene Diagnostics (system.init)
Fields added under `data.scene_diagnostics`:
- `schema_version`
- `scene_version`
- `loaded_from`
- `normalize_warnings[]`
- `resolve_errors[]`
- `timings` (load_ms/normalize_ms/resolve_ms)

## Snapshot Guard
- Canonical snapshot stored under `docs/contract/snapshots/scenes/`.
- Canonicalization rules:
  - Stable key ordering.
  - Stable array ordering for known arrays.
  - Remove runtime noise (timings/trace_id/etc.).

## Verify (system-bound)
Run with svc account:

```
DB_NAME=sc_demo E2E_LOGIN=svc_project_ro E2E_PASSWORD='ChangeMe_123!' \
make verify.portal.scene_diagnostics_smoke.container

DB_NAME=sc_demo E2E_LOGIN=svc_project_ro E2E_PASSWORD='ChangeMe_123!' \
make verify.portal.scene_snapshot_guard.container
```

## Snapshot Update (manual only)

```
DB_NAME=sc_demo E2E_LOGIN=svc_project_ro E2E_PASSWORD='ChangeMe_123!' \
make scene.snapshot.update
```

## Evidence
- Diagnostics artifacts: `artifacts/codex/portal-shell-v0_9-8/<timestamp>/`
- Snapshot guard artifacts: `artifacts/codex/portal-shell-v0_9-8/<timestamp>/`

## Notes
- `verify.portal.ui.v0_8.semantic.container` includes diagnostics + snapshot guard.
- Snapshot update is **manual** and should be referenced in PR body.
