# ITER-2026-04-05-1174

- status: FAIL
- mode: execute
- layer_target: Scenario Orchestration Runtime
- module: system_init scene runtime surface
- risk: medium
- publishability: internal

## Summary of Change

- 在 `addons/smart_core/handlers/system_init.py` 新增 `_bind_scene_assets` 包装函数，并将场景运行时上下文中的 `bind_scene_assets_fn` 显式指向该包装，恢复 `system_init` 边界上的 `bind_scene_assets(` 调用可见性。

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-05-1174.yaml`: PASS
- `make verify.scene.orchestrator.base_fact_binding.guard`: PASS
- `make ci.preflight.contract`: FAIL
  - failure gate: `verify.scene.action_surface_strategy.wiring.guard`
  - failure evidence: `system.init missing action strategy pass-through to scene_ready builder`

## Risk Analysis

- medium: 本批目标守卫已通过，但全链预检进入下一阻断点，说明 scene orchestrator wiring 仍有未闭环项。
- repository stop rule triggered: required verify command failed.

## Rollback Suggestion

- `git restore addons/smart_core/handlers/system_init.py`
- `git restore agent_ops/tasks/ITER-2026-04-05-1174.yaml`
- `git restore agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1174.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-05-1174.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- stop required by policy: yes
- unblock suggestion: open dedicated low-risk batch for `verify.scene.action_surface_strategy.wiring.guard`, restore explicit action strategy pass-through in `system_init`, then rerun `make ci.preflight.contract`.

