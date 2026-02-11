# Phase 10.3 — Scene Health Dashboard + Auto-Degrade Policy

## Goals
- Expose a stable `scene.health` contract for Portal consumption.
- Provide Portal dashboard `/admin/scene-health` to inspect channel/rollback/version/drift/resolve_errors/debt.
- Add auto-degrade safety policy: critical diagnostics trigger fallback to stable and write governance audit log.

## Health Contract
Intent: `scene.health`

Required fields:
- `company_id`
- `scene_channel`
- `rollback_active`
- `scene_version`
- `schema_version`
- `contract_ref`
- `summary.critical_resolve_errors_count`
- `summary.critical_drift_warn_count`
- `summary.non_critical_debt_count`
- `details.resolve_errors[]`
- `details.drift[]`
- `details.debt[]`
- `auto_degrade.triggered`
- `auto_degrade.reason_codes[]`
- `auto_degrade.action_taken`
- `last_updated_at`
- `trace_id`

Rules:
- Frontend treats contract as display-only; no inference for critical counters.
- Summary critical counters must align with `system.init -> scene_diagnostics`.

## Auto-Degrade Policy
Config keys (`ir.config_parameter`):
- `sc.scene.auto_degrade.enabled` (default `true`)
- `sc.scene.auto_degrade.critical_threshold.resolve_errors` (default `1`)
- `sc.scene.auto_degrade.critical_threshold.drift_warn` (default `1`)
- `sc.scene.auto_degrade.action` (default `rollback_pinned`, optional `stable_latest`)

Behavior:
- Evaluate diagnostics for critical scenes (`projects.list`, `projects.ledger`).
- Trigger when critical counters reach threshold.
- Write governance log action `auto_degrade_triggered` with one-minute debounce per trace.
- Emit diagnostics field:
  - `scene_diagnostics.auto_degrade.triggered`
  - `scene_diagnostics.auto_degrade.reason_codes[]`
  - `scene_diagnostics.auto_degrade.action_taken`
  - `scene_diagnostics.auto_degrade.pre_counts`

## Verify Commands
- `make verify.portal.scene_health_contract_smoke.container`
- `make verify.portal.scene_observability_preflight_smoke.container`
- `make verify.portal.scene_auto_degrade_smoke.container`
- `make verify.portal.scene_observability_smoke.container`
- Strict evidence mode:
  - `make verify.portal.scene_observability_preflight.container`
  - `make verify.portal.scene_auto_degrade_strict.container`
  - `make verify.portal.scene_observability_strict.container`
- `make verify.portal.ui.v0_8.semantic.container`

## Artifacts
- Health contract smoke:
  - `artifacts/codex/portal-scene-health-v10_3/<timestamp>/scene_health.log`
  - `artifacts/codex/portal-scene-health-v10_3/<timestamp>/summary.md`
- Auto-degrade smoke:
  - `artifacts/codex/portal-scene-auto-degrade-v10_3/<timestamp>/scene_health_auto_degrade.log`
  - `artifacts/codex/portal-scene-auto-degrade-v10_3/<timestamp>/governance_log.log`
  - `artifacts/codex/portal-scene-auto-degrade-v10_3/<timestamp>/summary.md`

## Troubleshooting
- Strict observability failures: `docs/ops/verify/scene_observability_troubleshooting.md`
