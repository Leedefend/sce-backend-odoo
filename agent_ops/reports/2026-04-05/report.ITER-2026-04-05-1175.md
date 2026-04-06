# ITER-2026-04-05-1175

- status: FAIL
- mode: execute
- layer_target: Scenario Orchestration Runtime
- module: system_init scene runtime surface
- risk: medium
- publishability: internal

## Summary of Change

- 在 `addons/smart_core/handlers/system_init.py` 补充显式 action strategy pass-through 表达式：
  - 将 `data["scene_action_surface_strategy"]` 通过 `_normalize_scene_action_surface_strategy` 与
    `dict(action_surface_strategy=data.get("scene_action_surface_strategy"))` 显式透传归一化，满足 wiring 守卫文本与语义要求。

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-05-1175.yaml`: PASS
- `make verify.scene.action_surface_strategy.wiring.guard`: PASS
- `make ci.preflight.contract`: FAIL
  - failure gate: `verify.scene.legacy_contract.guard`
  - failure evidence: `missing file: addons/smart_construction_core/controllers/scene_controller.py`

## Risk Analysis

- medium: 本批目标守卫已通过，`ci.preflight.contract` 前移到 legacy contract 守卫；当前阻断是守卫基线与现状文件面的不一致。
- repository stop rule triggered: required verify command failed.

## Rollback Suggestion

- `git restore addons/smart_core/handlers/system_init.py`
- `git restore agent_ops/tasks/ITER-2026-04-05-1175.yaml`
- `git restore agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1175.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-05-1175.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- stop required by policy: yes
- unblock suggestion: open dedicated batch to reconcile `verify.scene.legacy_contract.guard` with current controller ownership/baseline, then rerun `make ci.preflight.contract`.

