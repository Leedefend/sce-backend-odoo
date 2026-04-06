# ITER-2026-04-05-1176

- status: FAIL
- mode: execute
- layer_target: Governance Monitoring
- module: scene legacy contract guard
- risk: medium
- publishability: internal

## Summary of Change

- 对齐 `verify.scene.legacy_contract.guard` 目标文件归属：
  - `scripts/verify/scene_legacy_contract_guard.py` 中 `SCENE_CONTROLLER` 从
    `addons/smart_construction_core/controllers/scene_controller.py`
    调整为 `addons/smart_core/controllers/platform_scene_logic.py`。

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-05-1176.yaml`: PASS
- `make verify.scene.legacy_contract.guard`: PASS
- `make ci.preflight.contract`: FAIL
  - failure gate: `verify.scene.legacy_docs.guard`
  - failure evidence: multiple docs under `docs/audit/boundary/**` missing deprecation/successor/migration/sunset annotations for `/api/scenes/my`

## Risk Analysis

- medium: 本批守卫修复成功，预检继续前移到文档一致性守卫；当前阻断为文档治理缺口，不是运行时代码缺陷。
- repository stop rule triggered: required verify command failed.

## Rollback Suggestion

- `git restore scripts/verify/scene_legacy_contract_guard.py`
- `git restore agent_ops/tasks/ITER-2026-04-05-1176.yaml`
- `git restore agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1176.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-05-1176.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- stop required by policy: yes
- unblock suggestion: open dedicated docs-governance batch to satisfy `verify.scene.legacy_docs.guard` required markers for `/api/scenes/my` and rerun `make ci.preflight.contract`.

