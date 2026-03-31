# ITER-2026-03-30-356 Report

## Summary

- Audited the remaining scene-oriented payload fields inside `smart_construction_core` after the direct scene-seed cleanup, runtime hook migration, and workspace-row cleanup.
- Reduced the remaining scene pollution to a concrete tail list instead of a broad suspicion set.
- Confirmed that the major remaining items are now concentrated in handlers and service-layer payload builders rather than in the previously cleaned fact seed and extension-hook owners.

## Changed Files

- `agent_ops/tasks/ITER-2026-03-30-356.yaml`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`
- `agent_ops/reports/2026-03-30/report.ITER-2026-03-30-356.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-356.yaml` -> PASS

## Residual Tail List

- Usage / analytics handlers
  - [usage_track.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/handlers/usage_track.py)
  - [usage_report.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/handlers/usage_report.py)
  - note: these use `scene_key` as telemetry dimensions rather than navigation payload; they are scene-aware but not the same class of fact-layer contamination as menu/action payloads

- Enter / redirect handlers still embedding scene routes
  - [project_quick_create_wizard.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/wizard/project_quick_create_wizard.py)
  - [settlement_slice_enter.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/handlers/settlement_slice_enter.py)
  - [cost_tracking_enter.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/handlers/cost_tracking_enter.py)
  - [payment_slice_enter.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/handlers/payment_slice_enter.py)
  - [project_plan_bootstrap_enter.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/handlers/project_plan_bootstrap_enter.py)
  - [project_dashboard_enter.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/handlers/project_dashboard_enter.py)
  - [project_execution_enter.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/handlers/project_execution_enter.py)
  - note: these are the next highest-value cleanup candidates because they still emit direct `/s/...` route semantics from the industry module

- My-work and aggregate payload builders
  - [my_work_summary.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/handlers/my_work_summary.py)
  - [my_work_aggregate_service.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/services/my_work_aggregate_service.py)
  - note: they still normalize records into `scene_key` payloads and section-level scene targets

- Capability / projection services
  - [capability_registry.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/services/capability_registry.py)
  - [project_execution_item_projection_service.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/services/project_execution_item_projection_service.py)
  - [project_risk_alert_service.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/services/project_risk_alert_service.py)
  - note: these are semantically heavier because they bake `scene_key` into business capability or projection payloads

## Residual Classification

- `P1`
  - direct route/scene emission in enter handlers
- `P2`
  - `scene_key` embedded in business-facing my-work aggregation payloads
- `P3`
  - capability/projection services with scene-oriented targets
- `P4`
  - telemetry-only scene dimensions used for reporting and counters

## Risk Analysis

- Risk level remains low because this batch is audit-only.
- The cleanup line is now materially safer because the remaining work is no longer mixed between seed data, extension hooks, workspace rows, and runtime payloads.
- The next risky area is not breadth but ordering: enter-handler route cleanup should happen before capability/projection cleanup so user entry paths stay coherent.

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-30-356.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-356.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-30-356.json`

## Next Suggestion

- Start the next cleanup batch on the `P1` tail only:
  - move direct `/s/...` route and scene-target emission out of the enter handlers listed above
- Leave telemetry-only `scene_key` usage for a later governance decision unless it starts polluting user-facing payload contracts.
