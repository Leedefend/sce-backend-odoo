# ITER-2026-04-05-1148

- status: PASS
- mode: execute
- layer_target: Platform Layer
- module: app_config_engine.capability.native
- risk: medium
- publishability: internal

## Summary of Change

- added phase-1 native capability ingestion layer:
  - `addons/smart_core/app_config_engine/capability/native/menu_adapter.py`
  - `addons/smart_core/app_config_engine/capability/native/action_adapter.py`
  - `addons/smart_core/app_config_engine/capability/native/native_projection_service.py`
  - `addons/smart_core/app_config_engine/capability/native/__init__.py`
- integrated native projected rows into capability registry loader:
  - `addons/smart_core/app_config_engine/capability/core/contribution_loader.py`
- extended capability type schema for native/platform typed capability families:
  - `addons/smart_core/app_config_engine/capability/schema/capability_schema.py`

## Native Ingestion Scope (Phase-1)

- menu projection source: `ir.ui.menu` (active + action-bound entries)
- window action projection source: `ir.actions.act_window`
- output shape: standard capability row (identity/ownership/ui/binding/policy/runtime/audit)
- ownership model: platform owner (`smart_core`) with `native_projection` source kind

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-05-1148.yaml`: PASS
- `python3 -m py_compile ...native/*.py ...contribution_loader.py ...capability_schema.py`: PASS
- `make verify.architecture.platformization_boundary_closure_bundle`: PASS
- `make verify.controller.boundary.guard`: PASS

## Risk Analysis

- medium: projection introduces additional capability rows from native objects; merge/ownership path remains platform-controlled.
- no change to domain business facts or permission mutation semantics.

## Rollback Suggestion

- `git restore addons/smart_core/app_config_engine/capability/native`
- `git restore addons/smart_core/app_config_engine/capability/core/contribution_loader.py`
- `git restore addons/smart_core/app_config_engine/capability/schema/capability_schema.py`
- `git restore agent_ops/tasks/ITER-2026-04-05-1148.yaml`
- `git restore agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1148.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-05-1148.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- PASS
- next step suggestion: phase-2 add model access projection + menu/action/model linkage matrix and native ingestion lint guards.
