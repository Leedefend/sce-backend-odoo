# ITER-2026-04-09-1509 Report

## Batch
- Batch: `1/1`
- Mode: `implement`
- Stage: `Menu Target Interpreter - Batch 6 route generation`

## Architecture declaration
- Layer Target: `Navigation interpretation layer`
- Module: `MenuTargetInterpreterService route generator`
- Module Ownership: `addons/smart_core/delivery`
- Kernel or Scenario: `kernel`
- Reason: 后端单点输出 route，消除前端拼接逻辑分叉。

## Change summary
- 更新 `addons/smart_core/delivery/menu_target_interpreter_service.py`
  - 新增 `_build_route(target_type, target, menu_id)` 统一规则：
    - `scene` -> `/s/:scene_key?menu_id=:id`
    - `action` -> `/a/:action_id?menu_id=:id`
    - `native` -> `/native/action/:action_id?menu_id=:id`
    - `url` -> `target.url`
    - 其他 -> `null`
  - 在解释流程统一调用 `route = self._build_route(...)`。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-09-1509.yaml` ✅
- `rg -n "def _build_route|/s/|/a/|/native/action/|route = self._build_route" addons/smart_core/delivery/menu_target_interpreter_service.py` ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：仅解释层 route 字段生成逻辑，事实层与前端未变。

## Rollback suggestion
- `git restore addons/smart_core/delivery/menu_target_interpreter_service.py`

## Next suggestion
- 进入 Batch 7：`active_match` 细化输出。
