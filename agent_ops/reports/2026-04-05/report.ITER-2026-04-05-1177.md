# ITER-2026-04-05-1177

- status: FAIL
- mode: execute
- layer_target: Governance Monitoring
- module: scene legacy docs guard
- risk: medium
- publishability: internal

## Summary of Change

- 在以下边界文档补齐 `/api/scenes/my` 迁移标记：`deprecated`、successor `/api/v1/intent`、`intent=app.init`、sunset `2026-04-30`：
  - `docs/audit/boundary/boundary_object_master_table.md`
  - `docs/audit/boundary/duplicate_controller_surface.md`
  - `docs/audit/boundary/frontend_runtime_dependency.md`
  - `docs/audit/boundary/http_route_classification.md`
  - `docs/audit/boundary/http_route_inventory.md`
  - `docs/audit/boundary/mainchain_boundary_table.md`
  - `docs/audit/boundary/platform_entry_occupation.md`
  - `docs/audit/boundary/runtime_priority_matrix.md`
  - `docs/audit/boundary/scenes_my_entry_layer_decision.md`
  - `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-05-1177.yaml`: PASS
- `make verify.scene.legacy_docs.guard`: PASS
- `make ci.preflight.contract`: FAIL
  - failure gate: `verify.scene.legacy_auth.smoke`
  - failure evidence: `HTTP request failed after retries: <urlopen error timed out>`

## Risk Analysis

- medium: 文档治理缺口已闭合，预检推进到 live smoke 阶段后被运行时 HTTP 超时阻断。
- repository stop rule triggered: required verify command failed.

## Rollback Suggestion

- `git restore docs/audit/boundary/boundary_object_master_table.md`
- `git restore docs/audit/boundary/duplicate_controller_surface.md`
- `git restore docs/audit/boundary/frontend_runtime_dependency.md`
- `git restore docs/audit/boundary/http_route_classification.md`
- `git restore docs/audit/boundary/http_route_inventory.md`
- `git restore docs/audit/boundary/mainchain_boundary_table.md`
- `git restore docs/audit/boundary/platform_entry_occupation.md`
- `git restore docs/audit/boundary/runtime_priority_matrix.md`
- `git restore docs/audit/boundary/scenes_my_entry_layer_decision.md`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- stop required by policy: yes
- unblock suggestion: open dedicated batch for `verify.scene.legacy_auth.smoke` timeout handling/runtime availability check, then rerun `make ci.preflight.contract`.

