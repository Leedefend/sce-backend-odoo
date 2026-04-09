# ITER-2026-04-09-1507 Report

## Batch
- Batch: `1/1`
- Mode: `implement`
- Stage: `Menu Target Interpreter - Batch 4 native_bridge adjudicator`

## Architecture declaration
- Layer Target: `Navigation interpretation layer`
- Module: `MenuTargetInterpreterService native bridge adjudicator`
- Module Ownership: `addons/smart_core/delivery`
- Kernel or Scenario: `kernel`
- Reason: 对未落入 scene/custom_action 的 action 菜单输出显式 native_bridge，消除前端 fallback 决策。

## Change summary
- 更新 `addons/smart_core/delivery/menu_target_interpreter_service.py`
  - 新增 `NATIVE_BRIDGE_ACTION_TYPES`：`act_window/server/client`。
  - 新增 `_resolve_native_bridge_target`，要求：
    - action 类型在 native 集合
    - `action_id` 有效
    - `action_exists = true`
  - 在解释分支中新增 native 判定：
    - `target_type = native`
    - `delivery_mode = native_bridge`
    - `target = {action_id, action_type}`

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-09-1507.yaml` ✅
- `rg -n "native_bridge|target_type = \"native\"|def _resolve_native_bridge_target" addons/smart_core/delivery/menu_target_interpreter_service.py` ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：仅解释层新增 native 显式分支，不影响事实层与前端。

## Rollback suggestion
- `git restore addons/smart_core/delivery/menu_target_interpreter_service.py`

## Next suggestion
- 进入 Batch 5：`act_url` 与 `unavailable` 原因码解释补齐。
