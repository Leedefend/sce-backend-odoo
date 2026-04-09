# ITER-2026-04-09-1504 Report

## Batch
- Batch: `1/1`
- Mode: `implement`
- Stage: `Menu Target Interpreter - Batch 1 skeleton`

## Architecture declaration
- Layer Target: `Navigation interpretation layer`
- Module: `MenuTargetInterpreterService skeleton`
- Module Ownership: `addons/smart_core/delivery`
- Kernel or Scenario: `kernel`
- Reason: 建立统一解释入口，后续分批接入 scene/custom/native/url/unavailable 判定。

## Change summary
- 新增 `addons/smart_core/delivery/menu_target_interpreter_service.py`
  - 提供单一入口：`interpret(nav_fact, scene_map, policy)`。
  - 输出统一解释结构（`flat/tree`）与标准字段：
    - `target_type`
    - `delivery_mode`
    - `route`
    - `target`
    - `active_match`
    - `availability_status`
    - `reason_code`
  - 当前骨架策略：
    - 有 children 且无 action -> `directory + none + DIRECTORY_ONLY`
    - 其他默认 -> `unavailable + none + TARGET_MISSING`
  - 保持事实层不变，不回写 `menu_fact`。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-09-1504.yaml` ✅
- `rg -n "class MenuTargetInterpreterService|def interpret\(|target_type|delivery_mode|reason_code" addons/smart_core/delivery/menu_target_interpreter_service.py` ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：仅新增解释层骨架，不修改 facts-only 边界与前端逻辑。

## Rollback suggestion
- `git restore addons/smart_core/delivery/menu_target_interpreter_service.py`

## Next suggestion
- 进入 Batch 2：接入 scene 映射解析优先级。
