# Phase 9.9 - Resolve Errors Debt Ledger + Scene Target Completeness

Date: 2026-02-06

## Scope
- Add structured `resolve_errors`/`normalize_warnings` diagnostics (code/severity/scene_key/message).
- Introduce resolve-errors debt ledger baseline and guard (critical must be zero; non-critical must be whitelisted).
- Enforce scene target completeness (no empty targets).

## Diagnostics Contract
`data.scene_diagnostics.resolve_errors[]` entry shape:
- `scene_key`
- `kind` (`target` | `tile` | `filter` | `other`)
- `severity` (`critical` | `non_critical`)
- `code` (stable code like `MISSING_TARGET`, `XMLID_NOT_FOUND`)
- `ref` (optional: xmlid/route)
- `message` (short, stable)

`data.scene_diagnostics.normalize_warnings[]` entry shape:
- `code` (stable code like `LAYOUT_MISSING_OR_INVALID`)
- `severity` (usually `non_critical`)
- `scene_key`
- `message`

## Debt Ledger (Resolve Errors)
Baseline file:
- `docs/contract/snapshots/scenes/resolve_errors_debt.v0_9_9.json`

Rules:
- `severity=critical` resolve_errors must be **0**.
- `severity=non_critical` must be covered by the debt baseline (match by `scene_key + code + ref`).
- New debt requires an explicit baseline update in the PR.

## Verify

Debt guard:
```
DB_NAME=sc_demo E2E_LOGIN=svc_project_ro E2E_PASSWORD='ChangeMe_123!' \
make verify.portal.scene_resolve_errors_debt_guard.container
```

Target completeness (no empty targets):
```
DB_NAME=sc_demo E2E_LOGIN=svc_project_ro E2E_PASSWORD='ChangeMe_123!' \
make verify.portal.scene_target_smoke.container
```

## Gate
- `verify.portal.ui.v0_8.semantic.container` includes the debt guard.

## Artifacts
- `artifacts/codex/portal-shell-v0_9-9/<timestamp>/`

## Notes
- Debt baseline updates are manual and must be mentioned in the PR.
