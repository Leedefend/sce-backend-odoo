# ITER-2026-04-05-1173

- status: FAIL
- mode: execute
- layer_target: Scenario Orchestration Runtime
- module: system_init scene runtime surface
- risk: medium
- publishability: internal

## Summary of Change

- 在 `addons/smart_core/handlers/system_init.py` 增加显式 `data["scene_ready_contract_v1"]` 赋值路径，满足输出 schema 守卫对关键字段写入路径的门禁要求。

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-05-1173.yaml`: PASS
- `make verify.scene.orchestrator.output.schema.guard`: PASS
- `make ci.preflight.contract`: FAIL
  - failure gate: `verify.scene.orchestrator.base_fact_binding.guard`
  - failure evidence: `system_init missing bind_scene_assets call`

## Risk Analysis

- medium: 本批目标守卫已通过，但全链预检暴露新的编排基事实绑定守卫阻断，必须按停机规则切换到新专属批次修复。
- repository stop rule triggered: required verify command failed.

## Rollback Suggestion

- `git restore addons/smart_core/handlers/system_init.py`
- `git restore agent_ops/tasks/ITER-2026-04-05-1173.yaml`
- `git restore agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1173.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-05-1173.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- stop required by policy: yes
- unblock suggestion: open dedicated low-risk batch for `verify.scene.orchestrator.base_fact_binding.guard`, restore explicit `bind_scene_assets` call site visibility in `system_init`, then rerun `make ci.preflight.contract`.

